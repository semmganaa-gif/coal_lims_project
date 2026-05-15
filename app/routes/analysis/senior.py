# app/routes/analysis/senior.py
# -*- coding: utf-8 -*-
"""
Senior analyst review dashboard routes:
  - /ahlah_dashboard - Senior review dashboard
  - /api/ahlah_data - Dashboard data
  - /update_result_status/<int:result_id>/<new_status> - Approve/reject results
"""

from flask import request, render_template, jsonify
from flask_login import login_required, current_user

from app import cache
from app.services.analysis_workflow import (
    build_dashboard_stats,
    build_pending_results,
    bulk_update_result_status,
    load_analysis_schemas,
    select_repeat_result,
    update_result_status,
)
from app.utils.decorators import analysis_role_required
from app.utils.settings import get_error_reason_labels


def register_routes(bp):
    """Register routes on the given blueprint"""

    # =====================================================================
    # 1. SENIOR REVIEW DASHBOARD
    # =====================================================================
    @bp.route("/ahlah_dashboard", endpoint="ahlah_dashboard")
    @login_required
    @analysis_role_required(["senior", "admin"])
    def ahlah_dashboard():
        schema_map = load_analysis_schemas()

        return render_template(
            "ahlah_dashboard.html",
            title="Ахлах хяналт",
            error_labels=get_error_reason_labels(),
            analysis_schemas=schema_map,
            use_aggrid=True,
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

        results = build_pending_results(
            start_date=start_date,
            end_date=end_date,
            sample_name=sample_name,
        )
        return jsonify(results)

    # =====================================================================
    # 3. APPROVE/REJECT RESULTS
    # =====================================================================
    @bp.route("/update_result_status/<int:result_id>/<new_status>", methods=["POST"])
    @login_required
    def update_result_status_route(result_id, new_status):
        if getattr(current_user, "role", None) not in ("senior", "admin"):
            return jsonify({"message": "Эрх хүрэлцэхгүй байна"}), 403

        data = request.get_json(silent=True) or request.form.to_dict() or {}
        rejection_comment = data.get("rejection_comment")
        rejection_category = data.get("rejection_category")

        result, error, status_code = update_result_status(
            result_id=result_id,
            new_status=new_status,
            rejection_comment=rejection_comment,
            rejection_category=rejection_category,
        )

        if error:
            return jsonify({"message": error}), status_code
        return jsonify(result)

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
        rejection_comment = data.get("rejection_comment")
        rejection_category = data.get("rejection_category")

        result, error, status_code = bulk_update_result_status(
            result_ids=result_ids,
            new_status=new_status,
            rejection_comment=rejection_comment,
            rejection_category=rejection_category,
            username=current_user.username,
        )

        if error:
            return jsonify({"message": error}), status_code
        return jsonify(result)

    # =====================================================================
    # 4. SENIOR DASHBOARD STATISTICS
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
        stats = build_dashboard_stats()
        return jsonify(stats)

    # =====================================================================
    # 5. ДАВТАН ШИНЖИЛГЭЭНИЙ ҮР ДҮН СОНГОХ
    # =====================================================================
    @bp.route("/api/select_repeat_result/<int:result_id>", methods=["POST"])
    @login_required
    @analysis_role_required(["senior", "admin"])
    def select_repeat_result_route(result_id):
        """
        Давтан шинжилгээтэй үр дүнд аль утгыг ашиглахаа сонгоно.
        Body: {"use_original": true/false}
        """
        data = request.get_json(silent=True) or {}
        use_original = data.get("use_original", False)

        result, error, status_code = select_repeat_result(
            result_id=result_id,
            use_original=use_original,
        )

        if error:
            return jsonify({"message": error}), status_code
        return jsonify(result)
