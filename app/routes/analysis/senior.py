# app/routes/analysis/senior.py
# -*- coding: utf-8 -*-
"""
Senior analyst review dashboard routes:
  - /ahlah_dashboard - Senior review dashboard
  - /api/ahlah_data - Dashboard data
  - /update_result_status/<int:result_id>/<new_status> - Approve/reject results
"""

import json
from datetime import datetime

from flask import request, render_template, jsonify, current_app
from flask_login import login_required, current_user
from markupsafe import escape
from sqlalchemy import or_
from sqlalchemy.orm.exc import StaleDataError

from app import db, cache
from app.config.analysis_schema import get_analysis_schema
from app.models import AnalysisResult, AnalysisResultLog, Sample, User, AnalysisType
from app.utils.audit import log_audit
from app.utils.datetime import now_local
from app.utils.decorators import analysis_role_required
from app.utils.normalize import normalize_raw_data
from app.utils.notifications import notify_sample_status_change
from app.utils.security import escape_like_pattern
from app.utils.settings import get_error_reason_labels
from app.utils.shifts import get_shift_info


def register_routes(bp):
    """Register routes on the given blueprint"""

    # =====================================================================
    # 1. SENIOR REVIEW DASHBOARD
    # =====================================================================
    @bp.route("/ahlah_dashboard", endpoint="ahlah_dashboard")
    @login_required
    @analysis_role_required(["senior", "admin"])
    def ahlah_dashboard():
        schema_map = {"_default": get_analysis_schema(None)}
        try:
            codes = AnalysisType.query.with_entities(AnalysisType.code).all()
            for (code,) in codes:
                schema_map[code] = get_analysis_schema(code)
        except Exception:
            pass

        return render_template(
            "ahlah_dashboard.html",
            title="Ахлах хяналт",
            error_labels=get_error_reason_labels(),
            analysis_schemas=schema_map,
            use_aggrid=True,  # Enable AG Grid loading
        )

    # =====================================================================
    # 2. SENIOR DASHBOARD DATA (API)
    # =====================================================================
    @bp.route("/api/ahlah_data")
    @login_required
    @analysis_role_required(["senior", "admin"])
    def api_ahlah_data():
        start_date = request.args.get("start_date")
        end_date = request.args.get("end_date")
        sample_name = request.args.get("sample_name")

        q = (
            db.session.query(AnalysisResult, Sample, User, AnalysisType)
            .join(Sample, AnalysisResult.sample_id == Sample.id)
            .join(User, AnalysisResult.user_id == User.id)
            .join(AnalysisType, AnalysisResult.analysis_code == AnalysisType.code)
            .filter(
                or_(
                    AnalysisResult.status == "pending_review",
                    AnalysisResult.status == "rejected",
                )
            )
        )

        if start_date:
            try:
                sd = datetime.strptime(start_date, "%Y-%m-%d")
                q = q.filter(AnalysisResult.updated_at >= sd)
            except ValueError:
                pass

        if end_date:
            try:
                ed = datetime.strptime(end_date, "%Y-%m-%d")
                ed = datetime.combine(ed, datetime.max.time())
                q = q.filter(AnalysisResult.updated_at <= ed)
            except ValueError:
                pass

        if sample_name:
            safe_name = escape_like_pattern(sample_name)
            q = q.filter(Sample.sample_code.ilike(f"%{safe_name}%"))

        results_to_review = q.order_by(AnalysisResult.updated_at.desc()).limit(500).all()

        processed_results = []
        for result, sample, user, analysis_type in results_to_review:
            data_dict = {}
            raw_data = result.raw_data
            if isinstance(raw_data, str):
                try:
                    data_dict = json.loads(raw_data)
                except json.JSONDecodeError:
                    data_dict = {}
            elif isinstance(raw_data, dict):
                data_dict = dict(raw_data)
            else:
                data_dict = {}

            normalized = normalize_raw_data(data_dict, analysis_type.code)
            if normalized:
                data_dict.update(normalized)

            is_csn = analysis_type.code == "CSN"
            diff = data_dict.get("diff")
            avg = data_dict.get("avg")
            t_val = data_dict.get("t") if is_csn else diff
            avg_val = data_dict.get("avg") if is_csn else avg
            final_display = avg_val if not is_csn else result.final_result

            processed_results.append({
                "result_id": result.id,
                "sample_code": sample.sample_code,
                "analysis_name": analysis_type.name,
                "analysis_code": analysis_type.code,
                "status": result.status,
                "error_reason": result.error_reason,
                "raw_data": data_dict,
                "t_value": t_val,
                "final_value": final_display if final_display is not None else result.final_result,
                "user_name": user.username,
                "updated_at": result.updated_at.strftime("%Y-%m-%d %H:%M") if result.updated_at else None,
            })

        return jsonify(processed_results)

    # =====================================================================
    # 3. APPROVE/REJECT RESULTS
    # =====================================================================
    @bp.route("/update_result_status/<int:result_id>/<new_status>", methods=["POST"])
    @login_required
    def update_result_status(result_id, new_status):
        if getattr(current_user, "role", None) not in ("senior", "admin"):
            return jsonify({"message": "Эрх хүрэлцэхгүй байна"}), 403

        if new_status not in {"approved", "rejected", "pending_review"}:
            return jsonify({"message": "Төлөв буруу байна"}), 400

        # Row lock to prevent lost update
        res = AnalysisResult.query.filter_by(id=result_id).with_for_update().first()
        if not res:
            return jsonify({"message": "Үр дүн олдсонгүй"}), 404

        data = request.get_json(silent=True) or request.form.to_dict() or {}
        # XSS protection
        rejection_comment_raw = data.get("rejection_comment")
        rejection_comment = str(escape(rejection_comment_raw)) if rejection_comment_raw else None
        rejection_category = data.get("rejection_category")

        res.status = new_status
        res.updated_at = now_local()

        if new_status == "rejected":
            if hasattr(res, "rejection_category"):
                res.rejection_category = rejection_category
            if hasattr(res, "rejection_comment"):
                res.rejection_comment = rejection_comment or "Ахлах буцаасан"
            if hasattr(res, "error_reason"):
                res.error_reason = rejection_category
        else:
            if hasattr(res, "rejection_category"):
                res.rejection_category = None
            if hasattr(res, "rejection_comment"):
                res.rejection_comment = None
            if hasattr(res, "error_reason"):
                res.error_reason = None

        db.session.flush()

        action_text = new_status.upper()
        reason_text = rejection_comment or ("Зөвшөөрөгдсөн" if new_status == "approved" else "Хянагдаж буй")

        sample = db.session.get(Sample, res.sample_id) if res.sample_id else None
        audit = AnalysisResultLog(
            timestamp=now_local(),
            user_id=current_user.id,
            sample_id=res.sample_id,
            analysis_result_id=res.id,
            analysis_code=res.analysis_code,
            action=action_text,
            raw_data_snapshot=res.raw_data,
            final_result_snapshot=res.final_result,
            rejection_category=rejection_category,
            error_reason=rejection_category,
            reason=reason_text,
            sample_code_snapshot=sample.sample_code if sample else None,
        )
        # CRITICAL FIX: Compute hash (ISO 17025 audit integrity)
        audit.data_hash = audit.compute_hash()
        db.session.add(audit)

        try:
            db.session.commit()
        except StaleDataError:
            db.session.rollback()
            return jsonify({"message": "Өөр хэрэглэгч энэ үр дүнг өөрчилсөн байна. Refresh хийнэ үү."}), 409

        # Invalidate cached stats after status change
        cache.delete('kpi_summary_ahlah')
        cache.delete('ahlah_stats')

        # ISO 17025 compliance audit log
        log_audit(
            action=f'result_{new_status}',
            resource_type='AnalysisResult',
            resource_id=res.id,
            details={
                'sample_id': res.sample_id,
                'analysis_code': res.analysis_code,
                'final_result': res.final_result,
                'rejection_comment': rejection_comment
            }
        )

        return jsonify({"message": "OK", "status": new_status})

    # =====================================================================
    # 3.5 BULK APPROVE/REJECT RESULTS
    # =====================================================================
    @bp.route("/bulk_update_status", methods=["POST"])
    @login_required
    def bulk_update_status():
        """Bulk approve/reject multiple results"""
        if getattr(current_user, "role", None) not in ("senior", "admin"):
            return jsonify({"message": "Эрх хүрэлцэхгүй байна"}), 403

        data = request.get_json(silent=True) or {}
        result_ids = data.get("result_ids", [])
        new_status = data.get("status")
        # XSS protection
        rejection_comment_raw = data.get("rejection_comment")
        rejection_comment = str(escape(rejection_comment_raw)) if rejection_comment_raw else None
        rejection_category = data.get("rejection_category")

        if not result_ids:
            return jsonify({"message": "Үр дүн сонгогдоогүй байна"}), 400

        # A-H4: Bulk array size cap
        if len(result_ids) > 200:
            return jsonify({"message": "Нэг удаад 200-аас их үр дүн шинэчлэх боломжгүй"}), 400

        if new_status not in {"approved", "rejected"}:
            return jsonify({"message": "Төлөв буруу байна"}), 400

        if new_status == "rejected" and not rejection_category:
            return jsonify({"message": "Буцаах шалтгаанаа сонгоно уу"}), 400

        success_count = 0
        failed_ids = []

        # P-C1 fix: Batch-load бүх AnalysisResult нэг query-гээр (N+1 устгах)
        try:
            int_ids = [int(rid) for rid in result_ids]
        except (ValueError, TypeError):
            return jsonify({"message": "ID буруу байна"}), 400

        results_map = {
            r.id: r for r in
            AnalysisResult.query.filter(
                AnalysisResult.id.in_(int_ids)
            ).with_for_update().all()
        }

        # Batch-load холбогдох Sample-ууд (N+1 устгах)
        sample_ids = {r.sample_id for r in results_map.values()}
        samples_map = {
            s.id: s for s in
            Sample.query.filter(Sample.id.in_(sample_ids)).all()
        } if sample_ids else {}

        now_ts = now_local()

        for rid in int_ids:
            try:
                res = results_map.get(rid)
                if not res:
                    failed_ids.append(rid)
                    continue

                # Only modify pending_review or rejected status
                if res.status not in ("pending_review", "rejected"):
                    failed_ids.append(rid)
                    continue

                res.status = new_status
                res.updated_at = now_ts

                if new_status == "rejected":
                    if hasattr(res, "rejection_category"):
                        res.rejection_category = rejection_category
                    if hasattr(res, "rejection_comment"):
                        res.rejection_comment = rejection_comment or "Ахлах буцаасан"
                    if hasattr(res, "error_reason"):
                        res.error_reason = rejection_category
                else:
                    if hasattr(res, "rejection_category"):
                        res.rejection_category = None
                    if hasattr(res, "rejection_comment"):
                        res.rejection_comment = None
                    if hasattr(res, "error_reason"):
                        res.error_reason = None

                # Audit log (sample from pre-loaded map)
                sample = samples_map.get(res.sample_id)
                audit = AnalysisResultLog(
                    timestamp=now_ts,
                    user_id=current_user.id,
                    sample_id=res.sample_id,
                    analysis_result_id=res.id,
                    analysis_code=res.analysis_code,
                    action=f"BULK_{new_status.upper()}",
                    raw_data_snapshot=res.raw_data,
                    final_result_snapshot=res.final_result,
                    rejection_category=rejection_category if new_status == "rejected" else None,
                    error_reason=rejection_category if new_status == "rejected" else None,
                    reason=rejection_comment or ("Бөөнөөр зөвшөөрөгдсөн" if new_status == "approved" else "Бөөнөөр буцаагдсан"),
                    sample_code_snapshot=sample.sample_code if sample else None,
                )
                # CRITICAL FIX: Compute hash (ISO 17025 audit integrity)
                audit.data_hash = audit.compute_hash()
                db.session.add(audit)
                success_count += 1

            except Exception as e:
                current_app.logger.warning(f"bulk_update_status: result_id={rid} error: {e}")
                failed_ids.append(rid)
                continue

        if success_count > 0:
            try:
                db.session.commit()
            except StaleDataError:
                db.session.rollback()
                return jsonify({"message": "Зарим үр дүнг өөр хэрэглэгч өөрчилсөн байна. Refresh хийнэ үү."}), 409
            except Exception as e:
                db.session.rollback()
                return jsonify({"message": "Мэдээллийн сангийн алдаа"}), 500

            log_audit(
                action=f'bulk_result_{new_status}',
                resource_type='AnalysisResult',
                resource_id=None,
                details={
                    'count': success_count,
                    'status': new_status,
                    'rejection_category': rejection_category
                }
            )

            # Email notification (don't block)
            try:
                notify_sample_status_change(
                    sample_code=f"Бөөнөөр ({success_count} үр дүн)",
                    new_status=new_status,
                    changed_by=current_user.username,
                    reason=rejection_comment if new_status == "rejected" else None
                )
            except Exception:
                pass  # Don't block main operation if email fails

        return jsonify({
            "message": f"{success_count} үр дүн амжилттай {new_status} төлөвт шилжлээ.",
            "success_count": success_count,
            "failed_count": len(failed_ids),
            "failed_ids": failed_ids
        })

    # =====================================================================
    # 4. SENIOR DASHBOARD STATISTICS (Chemist, Sample registration counts)
    # =====================================================================
    @bp.route("/api/ahlah_stats")
    @login_required
    @analysis_role_required(["senior", "admin"])
    @cache.cached(timeout=30, key_prefix='ahlah_stats')
    def api_ahlah_stats():
        """
        Statistics for senior dashboard:
        - Analysis count per chemist today
        - Sample registration count today
        - Approved/Rejected counts
        """
        from sqlalchemy import func, case

        # Get shift start/end times (handles night shift correctly)
        shift_info = get_shift_info(now_local())
        today_start = shift_info.shift_start
        today_end = shift_info.shift_end

        # 1. Analysis count per chemist today
        chemist_stats = (
            db.session.query(
                User.username,
                User.id.label("user_id"),
                func.count(AnalysisResult.id).label("total"),
                func.sum(case((AnalysisResult.status == "approved", 1), else_=0)).label("approved"),
                func.sum(case((AnalysisResult.status == "pending_review", 1), else_=0)).label("pending"),
                func.sum(case((AnalysisResult.status == "rejected", 1), else_=0)).label("rejected"),
            )
            .join(AnalysisResult, AnalysisResult.user_id == User.id)
            .filter(User.role.in_(["chemist", "senior", "preparer"]))
            .filter(AnalysisResult.updated_at >= today_start)
            .filter(AnalysisResult.updated_at <= today_end)
            .group_by(User.id, User.username)
            .order_by(func.count(AnalysisResult.id).desc())
            .all()
        )

        chemist_list = []
        for row in chemist_stats:
            chemist_list.append({
                "username": row.username,
                "user_id": row.user_id,
                "total": row.total,
                "approved": row.approved or 0,
                "pending": row.pending or 0,
                "rejected": row.rejected or 0,
            })

        # 2. Sample registration count today
        today_samples = (
            db.session.query(func.count(Sample.id))
            .filter(Sample.received_date >= today_start)
            .filter(Sample.received_date <= today_end)
            .scalar() or 0
        )

        # 2a. Samples by unit (client_name)
        samples_by_unit = (
            db.session.query(
                Sample.client_name,
                func.count(Sample.id).label("count"),
            )
            .filter(Sample.received_date >= today_start)
            .filter(Sample.received_date <= today_end)
            .group_by(Sample.client_name)
            .order_by(func.count(Sample.id).desc())
            .all()
        )

        unit_list = []
        for row in samples_by_unit:
            unit_list.append({
                "name": row.client_name or "Тодорхойгүй",
                "count": row.count,
            })

        # 2b. Samples by type (sample_type)
        samples_by_type = (
            db.session.query(
                Sample.sample_type,
                func.count(Sample.id).label("count"),
            )
            .filter(Sample.received_date >= today_start)
            .filter(Sample.received_date <= today_end)
            .group_by(Sample.sample_type)
            .order_by(func.count(Sample.id).desc())
            .all()
        )

        type_list = []
        for row in samples_by_type:
            type_list.append({
                "name": row.sample_type or "Тодорхойгүй",
                "count": row.count,
            })

        # 3. Analysis count by type (today)
        analysis_type_stats = (
            db.session.query(
                AnalysisType.code,
                AnalysisType.name,
                func.count(AnalysisResult.id).label("total"),
                func.sum(case((AnalysisResult.status == "approved", 1), else_=0)).label("approved"),
                func.sum(case((AnalysisResult.status == "pending_review", 1), else_=0)).label("pending"),
                func.sum(case((AnalysisResult.status == "rejected", 1), else_=0)).label("rejected"),
            )
            .join(AnalysisResult, AnalysisResult.analysis_code == AnalysisType.code)
            .filter(AnalysisResult.updated_at >= today_start)
            .filter(AnalysisResult.updated_at <= today_end)
            .group_by(AnalysisType.code, AnalysisType.name)
            .order_by(func.count(AnalysisResult.id).desc())
            .all()
        )

        analysis_list = []
        for row in analysis_type_stats:
            analysis_list.append({
                "code": row.code,
                "name": row.name,
                "total": row.total,
                "approved": row.approved or 0,
                "pending": row.pending or 0,
                "rejected": row.rejected or 0,
            })

        # 4. Total counts (today) — нэг query-д нэгтгэсэн
        summary_row = (
            db.session.query(
                func.count(AnalysisResult.id).label("total"),
                func.sum(case((AnalysisResult.status == "approved", 1), else_=0)).label("approved"),
                func.sum(case((AnalysisResult.status == "pending_review", 1), else_=0)).label("pending"),
                func.sum(case((AnalysisResult.status == "rejected", 1), else_=0)).label("rejected"),
            )
            .filter(AnalysisResult.updated_at >= today_start)
            .filter(AnalysisResult.updated_at <= today_end)
            .one()
        )

        return jsonify({
            "chemists": chemist_list,
            "analysis_types": analysis_list,
            "samples_today": today_samples,
            "samples_by_unit": unit_list,
            "samples_by_type": type_list,
            "summary": {
                "total": summary_row.total or 0,
                "approved": summary_row.approved or 0,
                "pending": summary_row.pending or 0,
                "rejected": summary_row.rejected or 0,
            }
        })

    # =====================================================================
    # 5. ДАВТАН ШИНЖИЛГЭЭНИЙ ҮР ДҮН СОНГОХ (Аудит хуудаснаас)
    # =====================================================================
    @bp.route("/api/select_repeat_result/<int:result_id>", methods=["POST"])
    @login_required
    @analysis_role_required(["senior", "admin"])
    def select_repeat_result(result_id):
        """
        Давтан шинжилгээтэй үр дүнд аль утгыг ашиглахаа сонгоно.
        Body: {"use_original": true/false}
        - use_original=true  → final_result = анхны утга
        - use_original=false → final_result = давтан утга (default)
        """
        res = AnalysisResult.query.filter_by(id=result_id).with_for_update().first()
        if not res:
            return jsonify({"message": "Үр дүн олдсонгүй"}), 404

        data = request.get_json(silent=True) or {}
        use_original = data.get("use_original", False)

        # raw_data-аас _repeat мэдээлэл авах
        raw = res.get_raw_data()
        repeat_info = raw.get("_repeat")
        if not repeat_info:
            return jsonify({"message": "Давтан шинжилгээний мэдээлэл олдсонгүй"}), 400

        original_val = repeat_info.get("original_final_result")
        repeat_val = repeat_info.get("repeat_final_result")

        if original_val is None or repeat_val is None:
            return jsonify({"message": "Анхны/давтан утга олдсонгүй"}), 400

        old_final = res.final_result

        if use_original:
            res.final_result = original_val
        else:
            res.final_result = repeat_val

        # _repeat.use_original flag шинэчлэх
        repeat_info["use_original"] = use_original
        raw["_repeat"] = repeat_info
        res.set_raw_data(raw)
        res.updated_at = now_local()

        db.session.flush()

        # Audit log
        sample = db.session.get(Sample, res.sample_id)
        choice = "ORIGINAL" if use_original else "REPEAT"
        audit = AnalysisResultLog(
            timestamp=now_local(),
            user_id=current_user.id,
            sample_id=res.sample_id,
            analysis_result_id=res.id,
            analysis_code=res.analysis_code,
            action=f"SELECT_{choice}",
            raw_data_snapshot=res.raw_data,
            final_result_snapshot=res.final_result,
            reason=f"Ахлах {choice.lower()} үр дүнг сонгосон: {old_final} → {res.final_result}",
            sample_code_snapshot=sample.sample_code if sample else None,
        )
        audit.data_hash = audit.compute_hash()
        db.session.add(audit)

        try:
            db.session.commit()
        except StaleDataError:
            db.session.rollback()
            return jsonify({"message": "Өөр хэрэглэгч энэ үр дүнг өөрчилсөн байна. Refresh хийнэ үү."}), 409

        log_audit(
            action=f"select_{choice.lower()}_result",
            resource_type="AnalysisResult",
            resource_id=res.id,
            details={
                "sample_id": res.sample_id,
                "analysis_code": res.analysis_code,
                "old_final": old_final,
                "new_final": res.final_result,
                "use_original": use_original,
            },
        )

        return jsonify({
            "message": f"{'Анхны' if use_original else 'Давтан'} үр дүн сонгогдлоо",
            "final_result": res.final_result,
            "use_original": use_original,
        })
