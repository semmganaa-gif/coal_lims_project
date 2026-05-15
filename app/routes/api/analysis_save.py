# app/routes/api/analysis_save.py
# -*- coding: utf-8 -*-
"""
Analysis save & status update endpoints:
  - /save_results (chemist saves analysis results)
  - /update_result_status (senior approves/rejects)
"""

from flask import request, jsonify, current_app, url_for, redirect
from flask_babel import gettext as _
from flask_login import login_required, current_user

from app import limiter
from app.schemas import AnalysisResultSchema
from app.services.analysis_workflow import (
    BATCH_SAVE_CONFLICT,
    BATCH_SAVE_DB_ERROR,
    BATCH_SAVE_OK,
    save_results_batch,
    update_result_status_api,
)
from app.utils.validators import validate_save_results_batch
from .helpers import _coalesce_diff, _effective_limit
from app.monitoring import track_analysis

# Нэг удаагийн batch хүсэлтийн дээд хэмжээ (DoS хамгаалалт)
MAX_BATCH_SIZE = 500


def register_save_routes(bp):
    """Save/update route-уудыг blueprint дээр бүртгэх"""

    # -----------------------------------------------------------
    # 1) Химич хадгалсан үр дүн → /api/save_results
    # -----------------------------------------------------------
    @bp.route("/save_results", methods=["POST"])
    @login_required
    @limiter.limit("100 per minute")
    def save_results():
        # Role check
        if getattr(current_user, "role", None) not in ("chemist", "senior", "admin"):
            return jsonify({"success": False, "message": _("Шинжилгээний үр дүн хадгалах эрхгүй")}), 403

        data = request.get_json(silent=True)

        if data is None:
            return jsonify({"message": _("JSON өгөгдөл хүлээн аваагүй.")}), 400

        if isinstance(data, dict):
            data = [data]

        if not isinstance(data, list) or len(data) == 0:
            return jsonify({"message": _("JSON массив байх ёстой")}), 400

        if len(data) > MAX_BATCH_SIZE:
            return jsonify({
                "message": f"Нэг удаад {MAX_BATCH_SIZE}-аас их мөр хадгалах боломжгүй. "
                           f"Хүлээн авсан: {len(data)}"
            }), 400

        # Schema validation (structural check)
        _schema = AnalysisResultSchema(many=True)
        schema_errors = _schema.validate(data)
        if schema_errors:
            current_app.logger.warning("Schema validation errors: %s", schema_errors)

        # Input validation (business logic: range, CSN, etc.)
        is_valid, _validated_items, validation_errors = validate_save_results_batch(data)
        if not is_valid:
            current_app.logger.warning("Validation warnings: %s", validation_errors)

        # Service: atomic batch save + StaleDataError/SQLAlchemyError translation
        result = save_results_batch(
            items=data,
            user_id=current_user.id,
            coalesce_diff_fn=_coalesce_diff,
            effective_limit_fn=_effective_limit,
        )

        if result["status"] == BATCH_SAVE_CONFLICT:
            return jsonify({"message": _(result["message"])}), 409
        if result["status"] == BATCH_SAVE_DB_ERROR:
            return jsonify({"message": _(result["message"])}), 500

        # BATCH_SAVE_OK — partial success боломжтой (errors list-ээр илэрхийлэгдэнэ)
        saved_count = len(result["saved"])
        failed_count = len(result["errors"])

        for res in result["saved"]:
            if res.get("success"):
                track_analysis(
                    analysis_type=res.get("analysis_code", "unknown"),
                    status=res.get("status", "completed"),
                )

        response_data = {
            "message": f"{saved_count} мөр амжилттай хадгалагдлаа, {failed_count} алдаа.",
            "results": result["saved"],
            "errors": result["errors"],
        }
        status_code = 200 if failed_count == 0 else 207
        return jsonify(response_data), status_code

    # -----------------------------------------------------------
    # 2) Ахлахын буцаах/батлах
    # -----------------------------------------------------------
    @bp.route("/update_result_status/<int:result_id>/<new_status>", methods=["POST"])
    @login_required
    def update_result_status(result_id, new_status):
        if getattr(current_user, "role", None) not in ("senior", "admin"):
            return jsonify({"message": _("Хандах эрхгүй")}), 403

        if request.is_json:
            data = request.get_json(silent=True) or {}
        else:
            data = request.form.to_dict()

        result, error, status_code = update_result_status_api(
            result_id=result_id,
            new_status=new_status,
            action_type=data.get("action_type"),
            rejection_category=data.get("rejection_category"),
            rejection_subcategory=data.get("rejection_subcategory"),
            rejection_comment=data.get("rejection_comment"),
            error_reason=data.get("error_reason"),
        )

        if error:
            return jsonify({"message": error}), status_code

        if request.headers.get("X-Requested-With") == "XMLHttpRequest" or request.is_json:
            return jsonify(result)

        if "analysis" in current_app.blueprints:
            return redirect(url_for("analysis.ahlah_dashboard"))
        return redirect(url_for("main.index"))
