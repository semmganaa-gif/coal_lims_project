# app/routes/reports/monthly_plan.py
# -*- coding: utf-8 -*-
"""
Monthly Plan — сарын төлөвлөгөө, API, weekly performance, chemist report.
Routes are thin wrappers; business logic lives in app.services.report_service.
"""

from flask import render_template, request, jsonify, current_app
from flask_login import login_required, current_user

from app.utils.datetime import now_local
from app.routes.reports.routes import reports_bp, _year_arg
from app.services.report_service import (
    get_weeks_in_month,
    calculate_weekly_performance,
    build_monthly_plan_context,
    save_monthly_plans,
    save_staff_settings,
    get_plan_statistics,
    build_chemist_report_data,
)


# ======================================================================
#  Monthly Plan page
# ======================================================================

@reports_bp.route("/monthly_plan", methods=["GET"])
@login_required
def monthly_plan():
    """
    MONTHLY PLAN - Сарын төлөвлөгөө
    Долоо хоног бүрийн төлөвлөгөө ба гүйцэтгэлийг харьцуулах.
    """
    now = now_local()
    current_year = now.year
    current_month = now.month

    year = request.args.get("year", type=int) or current_year
    month = request.args.get("month", type=int) or current_month

    if year < current_year - 20 or year > current_year + 1:
        year = current_year
    if month < 1 or month > 12:
        month = current_month

    ctx = build_monthly_plan_context(year, month)

    return render_template(
        "reports/monthly_plan.html",
        title="Monthly Plan",
        year=year,
        month=month,
        **ctx,
    )


# =====================================================================
# MONTHLY PLAN API (Planned тоог хадгалах/унших)
# =====================================================================

@reports_bp.route("/api/monthly_plan", methods=["GET"])
@login_required
def api_get_monthly_plan():
    """
    Сарын төлөвлөгөө авах.
    Query params: year, month
    """
    from app.repositories import MonthlyPlanRepository

    year = request.args.get("year", type=int)
    month = request.args.get("month", type=int)

    if not year or not month:
        return jsonify({"error": "year болон month шаардлагатай"}), 400

    plans = MonthlyPlanRepository.get_by_month(year, month)

    result = {}
    for p in plans:
        key = f"{p.client_name}|{p.sample_type}|{p.week}"
        result[key] = p.planned_count

    return jsonify({"year": year, "month": month, "plans": result})


@reports_bp.route("/api/monthly_plan", methods=["POST"])
@login_required
def api_save_monthly_plan():
    """
    Сарын төлөвлөгөө хадгалах.
    JSON body: { year, month, plans: { "CHPP|2 hourly|1": 10, ... } }
    """
    if current_user.role not in ["senior", "admin"]:
        return jsonify({"error": "Зөвхөн ахлах эрхтэй"}), 403

    data = request.get_json()
    year = data.get("year")
    month = data.get("month")
    plans = data.get("plans", {})

    if not year or not month:
        return jsonify({"error": "year болон month шаардлагатай"}), 400

    success, saved_count, error_msg = save_monthly_plans(
        plans, year, month, current_user.id
    )

    if not success:
        current_app.logger.error(error_msg)
        return jsonify({"success": False, "error": "Төлөвлөгөө хадгалахад алдаа гарлаа."}), 500

    return jsonify({"success": True, "saved": saved_count})


@reports_bp.route("/api/staff_settings", methods=["POST"])
@login_required
def api_save_staff_settings():
    """
    Ажилтны тоог хадгалах.
    JSON body: { year, month, staff_preparers, staff_chemists }
    """
    if current_user.role not in ["senior", "admin"]:
        return jsonify({"error": "Зөвхөн ахлах эрхтэй"}), 403

    data = request.get_json()
    year = data.get("year")
    month = data.get("month")
    preparers = data.get("staff_preparers", 6)
    chemists = data.get("staff_chemists", 10)

    if not year or not month:
        return jsonify({"error": "year болон month шаардлагатай"}), 400

    success, error_msg = save_staff_settings(year, month, preparers, chemists)

    if not success:
        current_app.logger.error(error_msg)
        return jsonify({"success": False, "error": "Ажилтны тохиргоо хадгалахад алдаа гарлаа."}), 500

    return jsonify({"success": True})


@reports_bp.route("/api/plan_statistics", methods=["GET"])
@login_required
def api_plan_statistics():
    """
    Статистик мэдээлэл - жилээр, сараар, долоо хоногоор.
    Query params: from_year, from_month, to_year, to_month
    """
    now = now_local()
    current_year = now.year

    from_year = request.args.get("from_year", type=int) or (current_year - 1)
    from_month = request.args.get("from_month", type=int) or 1
    to_year = request.args.get("to_year", type=int) or current_year
    to_month = request.args.get("to_month", type=int) or now.month

    result = get_plan_statistics(from_year, from_month, to_year, to_month)
    return jsonify(result)


@reports_bp.route("/api/weekly_performance", methods=["GET"])
@login_required
def api_weekly_performance():
    """
    Долоо хоногийн гүйцэтгэл (дээжийн тоо) авах.
    Query params: year, month
    """
    year = request.args.get("year", type=int)
    month = request.args.get("month", type=int)

    if not year or not month:
        return jsonify({"error": "year болон month шаардлагатай"}), 400

    performance, weeks = calculate_weekly_performance(year, month)

    weeks_info = [
        {"week": w[0], "start": w[1].strftime("%Y-%m-%d"), "end": w[2].strftime("%Y-%m-%d")}
        for w in weeks
    ]

    return jsonify({
        "year": year,
        "month": month,
        "weeks": weeks_info,
        "performance": performance,
    })


# ======================================================================
#  III. ХИМИЧИЙН ТАЙЛАН - Chemist Performance Report
# ======================================================================

@reports_bp.route("/chemist_report")
@login_required
def chemist_report():
    """
    Химич нарын гүйцэтгэлийн тайлан:
    1. Сараар шинжилгээний тоо
    2. Шинжилгээний төрөл бүрээр тоо
    3. Error reason (8 төрөл) - алдааны тоо
    """
    year = _year_arg()

    date_from_str = request.args.get("date_from", "")
    date_to_str = request.args.get("date_to", "")

    ctx = build_chemist_report_data(year, date_from_str, date_to_str)

    return render_template(
        "reports/chemist_report.html",
        title=f"Химичийн тайлан — {ctx['year']}",
        **ctx,
    )
