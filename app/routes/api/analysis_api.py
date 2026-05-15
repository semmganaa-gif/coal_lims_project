# app/routes/api/analysis_api.py
# -*- coding: utf-8 -*-
"""
Analysis-related API endpoints (query operations):
  - /eligible_samples/<analysis_code>
  - /unassign_sample
  - /request_analysis
  - /check_ready_samples

Save/update operations are in analysis_save.py.
"""

import asyncio
import json

from flask import request, jsonify, current_app
from flask_login import login_required, current_user
from flask_babel import gettext as _
from sqlalchemy import or_, not_, select
from sqlalchemy.exc import SQLAlchemyError

from app import db, limiter
from app.constants import UserRole
from app.models import Sample, AnalysisResult
from app.services.analysis_audit import log_analysis_action
from app.utils.datetime import now_local
from app.utils.codes import norm_code, BASE_TO_ALIASES
from app.utils.audit import log_audit
from app.utils.database import safe_commit
from .helpers import _requires_mass_gate, _has_m_task_sql
from .analysis_save import register_save_routes
from datetime import timedelta


def register_routes(bp):
    """Route-уудыг өгөгдсөн blueprint дээр бүртгэх"""

    # Save/update routes-ийг тусдаа модулиас бүртгэх
    register_save_routes(bp)

    # -----------------------------------------------------------
    # 1) Ажлын талбарын "дээжүүд"
    # -----------------------------------------------------------
    @bp.route("/eligible_samples/<analysis_code>", methods=["GET"])
    @login_required
    @limiter.limit("100 per minute")
    async def eligible_samples(analysis_code):
        base_code = norm_code(analysis_code).strip()
        if not base_code:
            return jsonify({"samples": []})

        # WTL_MG: search for MG-only codes (MT/TRD are shared)
        mg_only_codes = ['MG', 'MG_SIZE']
        is_mg = base_code == 'WTL_MG' or base_code in mg_only_codes

        def _query_eligible():
            if is_mg:
                existing_ids_subq = (
                    db.session.query(AnalysisResult.sample_id)
                    .filter(AnalysisResult.analysis_code.in_(mg_only_codes))
                    .distinct()
                )
            else:
                existing_ids_subq = (
                    db.session.query(AnalysisResult.sample_id)
                    .filter(AnalysisResult.analysis_code == base_code)
                    .distinct()
                )

            from sqlalchemy import func
            text_lc = func.lower(Sample.analyses_to_perform)

            if is_mg:
                terms = [c.lower() for c in mg_only_codes] + ['wtl_mg']
            else:
                terms = [base_code.lower()]
                for alias_lc in (BASE_TO_ALIASES.get(base_code, []) or []):
                    terms.append(alias_lc)

            like_clauses = [text_lc.like(f'%"{t}"%') for t in terms]

            stmt = select(Sample).where(
                Sample.lab_type == 'coal',
                Sample.status.in_(["new", "New"]),
                or_(*like_clauses),
                ~Sample.id.in_(existing_ids_subq),
            )

            if _requires_mass_gate(base_code):
                stmt = stmt.where(or_(not_(_has_m_task_sql()), Sample.mass_ready.is_(True)))

            from app.constants import MAX_ANALYSIS_RESULTS
            stmt = stmt.order_by(Sample.received_date.desc(), Sample.id.desc()).limit(MAX_ANALYSIS_RESULTS)
            return list(db.session.execute(stmt).scalars().all())

        rows = await asyncio.to_thread(_query_eligible)
        from app.constants import CHPP_2H_SAMPLES_ORDER

        # CHPP дээжүүдийг зөв дарааллаар эрэмбэлэх
        def get_chpp_order(sample):
            """CHPP дээжийн дараалал олох"""
            sample_name = getattr(sample, "sample_name", None) or getattr(sample, "name", None) or ""
            date_key = sample.received_date.strftime("%Y%m%d") if sample.received_date else "00000000"
            for idx, chpp_name in enumerate(CHPP_2H_SAMPLES_ORDER):
                if chpp_name in sample_name:
                    return (date_key, idx)
            return (date_key, 1000 + sample.id)

        rows_sorted = sorted(rows, key=lambda s: (
            -(int(get_chpp_order(s)[0])),
            get_chpp_order(s)[1]
        ))

        samples = []
        for s in rows_sorted:
            samples.append({
                "id": s.id,
                "sample_code": s.sample_code or "",
                "name": getattr(s, "sample_name", None) or getattr(s, "name", None) or "",
                "client_name": s.client_name or "",
                "sample_type": s.sample_type or "",
                "received_date": s.received_date.strftime("%Y-%m-%d %H:%M") if s.received_date else "",
            })

        # Rejected дээжүүд - давтах шаардлагатай
        def _query_rejected():
            rejected_query = (
                db.session.query(AnalysisResult, Sample)
                .join(Sample, AnalysisResult.sample_id == Sample.id)
                .filter(
                    AnalysisResult.analysis_code == base_code,
                    AnalysisResult.status == "rejected"
                )
            )

            if current_user.role == UserRole.CHEMIST.value:
                rejected_query = rejected_query.filter(AnalysisResult.user_id == current_user.id)

            return rejected_query.order_by(AnalysisResult.updated_at.desc()).all()

        rejected_rows = await asyncio.to_thread(_query_rejected)

        rejected_samples = []
        for result, sample in rejected_rows:
            rejected_samples.append({
                "id": sample.id,
                "result_id": result.id,
                "sample_code": sample.sample_code or "",
                "client_name": sample.client_name or "",
                "sample_type": sample.sample_type or "",
                "error_reason": result.error_reason or "",
                "updated_at": result.updated_at.strftime("%Y-%m-%d %H:%M") if result.updated_at else "",
            })

        return jsonify({
            "samples": samples,
            "rejected": rejected_samples,
            "rejected_count": len(rejected_samples)
        })

    # -----------------------------------------------------------
    # 2) Дээжийг шинжилгээнээс хасах (senior/admin only)
    # -----------------------------------------------------------
    @bp.route("/unassign_sample", methods=["POST"])
    @login_required
    @limiter.limit("100 per minute")
    async def unassign_sample():
        """Дээжийг тухайн шинжилгээнээс хасах."""
        if current_user.role not in (UserRole.SENIOR.value, UserRole.ADMIN.value):
            return jsonify({"success": False, "message": _("Ахлах эсвэл админ эрх шаардлагатай")}), 403

        data = request.get_json(silent=True)
        if not data:
            return jsonify({"success": False, "message": _("JSON өгөгдөл хүлээн аваагүй")}), 400

        sample_id = data.get("sample_id")
        analysis_code = data.get("analysis_code")

        if not sample_id or not analysis_code:
            return jsonify({"success": False, "message": _("sample_id болон analysis_code шаардлагатай")}), 400

        sample = db.session.get(Sample, sample_id)
        if not sample:
            return jsonify({"success": False, "message": _("Дээж олдсонгүй")}), 404

        try:
            analyses = json.loads(sample.analyses_to_perform or "[]")
        except (json.JSONDecodeError, TypeError, ValueError):
            analyses = []

        base_code = norm_code(analysis_code).strip()
        codes_to_remove = [base_code.lower()] + [a.lower() for a in (BASE_TO_ALIASES.get(base_code, []) or [])]

        original_count = len(analyses)
        analyses = [a for a in analyses if a.lower() not in codes_to_remove]

        if len(analyses) == original_count:
            return jsonify({"success": False, "message": _("%(code)s шинжилгээ оноогдоогүй байна") % {"code": analysis_code}}), 400

        sample.analyses_to_perform = json.dumps(analyses)

        log_audit(
            action="unassign_analysis",
            resource_type="Sample",
            resource_id=sample.id,
            details={
                "sample_code": sample.sample_code,
                "analysis_code": analysis_code,
            }
        )

        if not safe_commit(error_msg="Unassign analysis commit error", notify=False):
            return jsonify({"success": False, "message": _("Хадгалахад алдаа гарлаа")}), 500

        return jsonify({
            "success": True,
            "message": f"{sample.sample_code} дээжээс {analysis_code} шинжилгээг хаслаа",
            "remaining_analyses": analyses
        })

    # -----------------------------------------------------------
    # 3) Шинжилгээ захиалах (Нэгтгэлээс)
    # -----------------------------------------------------------
    @bp.route("/request_analysis", methods=["POST"])
    @login_required
    async def request_analysis():
        """Нэгтгэлээс хоосон нүдэн дээр дарж шинжилгээ захиалах."""
        if getattr(current_user, "role", None) not in ("senior", "admin"):
            return jsonify({"message": _("Зөвхөн ахлах болон админ захиалга өгөх боломжтой")}), 403

        data = request.get_json(silent=True) or {}
        sample_id = data.get("sample_id")
        analysis_code = data.get("analysis_code")

        if not sample_id or not analysis_code:
            return jsonify({"message": _("sample_id болон analysis_code шаардлагатай")}), 400

        try:
            sample = db.session.get(Sample, sample_id)
            if not sample:
                return jsonify({"message": _("#%(id)s дээж олдсонгүй") % {"id": sample_id}}), 404

            current_analyses = sample.analyses_to_perform or []
            if isinstance(current_analyses, str):
                try:
                    current_analyses = json.loads(current_analyses)
                except (json.JSONDecodeError, TypeError, ValueError):
                    current_analyses = []

            base_code = norm_code(analysis_code)
            if not base_code:
                base_code = analysis_code

            existing_codes = [norm_code(c) for c in current_analyses]
            if base_code in existing_codes:
                return jsonify({"message": _("'%(code)s' шинжилгээ аль хэдийн захиалагдсан") % {"code": base_code}}), 400

            current_analyses.append(base_code)
            sample.analyses_to_perform = json.dumps(current_analyses)
            sample.updated_at = now_local()

            log_analysis_action(
                result_id=None,
                sample_id=sample_id,
                analysis_code=base_code,
                action="ANALYSIS_REQUESTED",
                reason=f"Нэгтгэлээс '{base_code}' шинжилгээ захиалсан",
                sample_code_snapshot=sample.sample_code,
            )
            if not safe_commit(error_msg="Request analysis error", notify=False):
                return jsonify({"message": _("Мэдээллийн сангийн алдаа гарлаа")}), 500

            return jsonify({
                "message": f"'{base_code}' шинжилгээ амжилттай захиалагдлаа",
                "sample_id": sample_id,
                "analysis_code": base_code
            })

        except SQLAlchemyError as e:
            current_app.logger.error(f"Request analysis error: {e}", exc_info=True)
            return jsonify({"message": _("Мэдээллийн сангийн алдаа гарлаа")}), 500

    # -----------------------------------------------------------
    # 4) Notification Check
    # -----------------------------------------------------------
    @bp.route("/check_ready_samples", methods=["GET"])
    @login_required
    async def check_ready_samples():
        try:
            cutoff_time = now_local() - timedelta(hours=12)
            pending_samples = list(db.session.execute(
                select(Sample).where(
                    Sample.received_date >= cutoff_time,
                    Sample.client_name == 'CHPP',
                    Sample.sample_type.in_(['2 hourly', '4 hourly', '2 Hourly', '4 Hourly']),
                    ~Sample.status.in_(['completed', 'reported', 'archived']),
                )
            ).scalars().all())

            ready_count = 0
            ready_samples_list = []

            for s in pending_samples:
                calc = s.get_calculations()
                p_name = (s.product or "").upper()
                is_ready = False

                if "PF" in p_name:
                    if (calc.mt is not None) and (calc.aad is not None):
                        is_ready = True
                else:
                    if (
                        (calc.mt is not None) and (calc.mad is not None) and
                        (calc.aad is not None) and (calc.vad is not None) and
                        (calc.gi is not None)
                    ):
                        is_ready = True

                if is_ready:
                    ready_count += 1
                    ready_samples_list.append({
                        "sample_code": s.sample_code,
                        "time": s.received_date.strftime("%H:%M"),
                        "product": s.product
                    })

            return jsonify({
                "ready_count": ready_count,
                "samples": ready_samples_list,
                "timestamp": now_local().strftime("%H:%M:%S")
            })

        except (SQLAlchemyError, AttributeError) as e:
            current_app.logger.error(f"Notification Check Error: {e}", exc_info=True)
            return jsonify({"ready_count": 0, "error": _("Шалгахад алдаа гарлаа")}), 500
