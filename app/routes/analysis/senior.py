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
from datetime import datetime
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


def register_routes(bp):
    """Route-уудыг өгөгдсөн blueprint дээр бүртгэх"""

    # =====================================================================
    # 1. АХЛАХЫН ХЯНАЛТЫН САМБАР
    # =====================================================================
    @bp.route("/ahlah_dashboard", endpoint="ahlah_dashboard")
    @login_required
    @analysis_role_required(["ahlah", "admin"])
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
        )

    # =====================================================================
    # 2. АХЛАХЫН САМБАРЫН ӨГӨГДӨЛ (API)
    # =====================================================================
    @bp.route("/api/ahlah_data")
    @login_required
    @analysis_role_required(["ahlah", "admin"])
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
        if getattr(current_user, "role", None) not in ("ahlah", "admin"):
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
