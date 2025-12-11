# app/routes/analysis/senior.py
# -*- coding: utf-8 -*-
"""
Ахлах шинжилгээчийн хяналтын самбартай холбоотой routes:
  - /ahlah_dashboard - Ахлахын хяналтын самбар
  - /api/ahlah_data - Dashboard-ын өгөгдөл
  - /update_result_status/<int:result_id>/<new_status> - Үр дүнг батлах/буцаах
"""

from flask import request, render_template, jsonify
from flask_login import login_required, current_user
from sqlalchemy import or_
from datetime import datetime, date
from app.utils.shifts import get_shift_date
import json

from app import db
from app.models import AnalysisResult, AnalysisResultLog, Sample, User, AnalysisType
from app.utils.datetime import now_local
from app.utils.security import escape_like_pattern
from app.utils.settings import get_error_reason_labels  # ✅ DB-ээс унших
from app.utils.normalize import normalize_raw_data
from app.config.analysis_schema import get_analysis_schema
from app.utils.audit import log_audit
from app.utils.decorators import analysis_role_required
from app.utils.notifications import notify_sample_status_change


def register_routes(bp):
    """Route-уудыг өгөгдсөн blueprint дээр бүртгэх"""

    # =====================================================================
    # 1. АХЛАХЫН ХЯНАЛТЫН САМБАР
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
            title="Ахлахын хяналт",
            error_labels=get_error_reason_labels(),  # ✅ DB-ээс унших
            analysis_schemas=schema_map,
            use_aggrid=True,  # ✅ Enable AG Grid loading
        )

    # =====================================================================
    # 2. АХЛАХЫН САМБАРЫН ӨГӨГДӨЛ (API)
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

        results_to_review = q.order_by(AnalysisResult.updated_at.desc()).all()

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
    # 3. ҮР ДҮНГ БАТЛАХ/БУЦААХ
    # =====================================================================
    @bp.route("/update_result_status/<int:result_id>/<new_status>", methods=["POST"])
    @login_required
    def update_result_status(result_id, new_status):
        if getattr(current_user, "role", None) not in ("senior", "admin"):
            return jsonify({"message": "Эрх хүрэхгүй"}), 403

        res = AnalysisResult.query.get_or_404(result_id)
        if new_status not in {"approved", "rejected", "pending_review"}:
            return jsonify({"message": "Буруу статус"}), 400

        data = request.get_json(silent=True) or request.form.to_dict() or {}
        rejection_comment = data.get("rejection_comment")
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
        reason_text = rejection_comment or ("Approved" if new_status == "approved" else "Review")

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
        )
        db.session.add(audit)
        db.session.commit()

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
    # 3.5 ОЛОН ҮР ДҮНГ НЭГ ДОРД БАТЛАХ/БУЦААХ (Bulk Operations)
    # =====================================================================
    @bp.route("/bulk_update_status", methods=["POST"])
    @login_required
    def bulk_update_status():
        """Олон үр дүнг нэг дор approve/reject хийх"""
        if getattr(current_user, "role", None) not in ("senior", "admin"):
            return jsonify({"message": "Эрх хүрэхгүй"}), 403

        data = request.get_json(silent=True) or {}
        result_ids = data.get("result_ids", [])
        new_status = data.get("status")
        rejection_comment = data.get("rejection_comment")
        rejection_category = data.get("rejection_category")

        if not result_ids:
            return jsonify({"message": "Үр дүн сонгоогүй байна"}), 400

        if new_status not in {"approved", "rejected"}:
            return jsonify({"message": "Буруу статус"}), 400

        if new_status == "rejected" and not rejection_category:
            return jsonify({"message": "Буцаах шалтгаан сонгоно уу"}), 400

        success_count = 0
        failed_ids = []

        for rid in result_ids:
            try:
                res = AnalysisResult.query.get(int(rid))
                if not res:
                    failed_ids.append(rid)
                    continue

                # Зөвхөн pending_review эсвэл rejected статустай бол засах
                if res.status not in ("pending_review", "rejected"):
                    failed_ids.append(rid)
                    continue

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

                # Audit log
                audit = AnalysisResultLog(
                    timestamp=now_local(),
                    user_id=current_user.id,
                    sample_id=res.sample_id,
                    analysis_result_id=res.id,
                    analysis_code=res.analysis_code,
                    action=f"BULK_{new_status.upper()}",
                    raw_data_snapshot=res.raw_data,
                    final_result_snapshot=res.final_result,
                    rejection_category=rejection_category if new_status == "rejected" else None,
                    error_reason=rejection_category if new_status == "rejected" else None,
                    reason=rejection_comment or ("Bulk Approved" if new_status == "approved" else "Bulk Rejected"),
                )
                db.session.add(audit)
                success_count += 1

            except (ValueError, Exception):
                failed_ids.append(rid)
                continue

        if success_count > 0:
            try:
                db.session.commit()
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

                # Email notification (async-style, don't block)
                try:
                    notify_sample_status_change(
                        sample_code=f"Bulk ({success_count} results)",
                        new_status=new_status,
                        changed_by=current_user.username,
                        reason=rejection_comment if new_status == "rejected" else None
                    )
                except Exception:
                    pass  # Email алдаа гарсан ч үндсэн үйлдлийг зогсоохгүй

            except Exception as e:
                db.session.rollback()
                return jsonify({"message": f"DB алдаа: {str(e)[:100]}"}), 500

        return jsonify({
            "message": f"{success_count} үр дүн амжилттай {new_status} болгогдлоо.",
            "success_count": success_count,
            "failed_count": len(failed_ids),
            "failed_ids": failed_ids
        })

    # =====================================================================
    # 4. АХЛАХЫН САМБАРЫН СТАТИСТИК (Химич, Дээж бүртгэл тоо)
    # =====================================================================
    @bp.route("/api/ahlah_stats")
    @login_required
    @analysis_role_required(["senior", "admin"])
    def api_ahlah_stats():
        """
        Ахлахын самбарт харуулах статистик:
        - Химич бүрийн өнөөдрийн шинжилгээний тоо
        - Өнөөдөр бүртгэгдсэн дээжийн тоо
        - Баталгаажсан/Буцаагдсан тоо
        """
        from sqlalchemy import func, case
        from datetime import timedelta

        today = get_shift_date()
        today_start = datetime.combine(today, datetime.min.time())
        today_end = datetime.combine(today, datetime.max.time())

        # 1. Химич бүрийн өнөөдрийн шинжилгээний тоо
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
            .filter(User.role.in_(["chemist", "senior"]))
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

        # 2. Өнөөдөр бүртгэгдсэн дээжийн тоо
        today_samples = (
            db.session.query(func.count(Sample.id))
            .filter(Sample.received_date >= today_start)
            .filter(Sample.received_date <= today_end)
            .scalar() or 0
        )

        # 2a. Дээж бүртгэл - Нэгжээр (client_name)
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

        # 2b. Дээж бүртгэл - Төрлөөр (sample_type)
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

        # 3. Шинжилгээний төрөл бүрийн тоо (өнөөдөр)
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

        # 4. Нийт тоо (өнөөдөр)
        total_today = (
            db.session.query(func.count(AnalysisResult.id))
            .filter(AnalysisResult.updated_at >= today_start)
            .filter(AnalysisResult.updated_at <= today_end)
            .scalar() or 0
        )

        approved_today = (
            db.session.query(func.count(AnalysisResult.id))
            .filter(AnalysisResult.updated_at >= today_start)
            .filter(AnalysisResult.updated_at <= today_end)
            .filter(AnalysisResult.status == "approved")
            .scalar() or 0
        )

        pending_today = (
            db.session.query(func.count(AnalysisResult.id))
            .filter(AnalysisResult.updated_at >= today_start)
            .filter(AnalysisResult.updated_at <= today_end)
            .filter(AnalysisResult.status == "pending_review")
            .scalar() or 0
        )

        rejected_today = (
            db.session.query(func.count(AnalysisResult.id))
            .filter(AnalysisResult.updated_at >= today_start)
            .filter(AnalysisResult.updated_at <= today_end)
            .filter(AnalysisResult.status == "rejected")
            .scalar() or 0
        )

        return jsonify({
            "chemists": chemist_list,
            "analysis_types": analysis_list,
            "samples_today": today_samples,
            "samples_by_unit": unit_list,
            "samples_by_type": type_list,
            "summary": {
                "total": total_today,
                "approved": approved_today,
                "pending": pending_today,
                "rejected": rejected_today,
            }
        })
