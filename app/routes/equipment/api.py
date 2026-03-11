# app/routes/equipment/api.py
# -*- coding: utf-8 -*-
"""Тоног төхөөрөмжийн API endpoints — thin wrappers over equipment_service."""

from datetime import datetime, timedelta

from flask import request, jsonify, current_app
from flask_login import login_required, current_user
from sqlalchemy.exc import SQLAlchemyError

from app import db, limiter
from app.models import Equipment
from app.routes.equipment import equipment_bp
from app.routes.api.helpers import api_success, api_error
from app.utils.datetime import now_local
from app.utils.shifts import get_shift_date
from app.services.equipment_service import (
    process_bulk_usage_items,
    get_usage_summary,
    get_journal_detailed,
    get_monthly_stats,
)


# -------------------------------------------------
# BULK USAGE LOG
# -------------------------------------------------

@equipment_bp.route("/api/log_usage_bulk", methods=["POST"])
@login_required
@limiter.limit("10 per minute")
def log_usage_bulk():
    """
    Frontend-ээс ирсэн олон төхөөрөмжийн бүртгэлийг хүлээж авч хадгална.
    JSON бүтэц: {
        "items": [{
            "eq_id": 1,
            "minutes": 60,
            "note": "...",
            "is_checked": true,
            "calibration": {
                "type": "temperature|weight|analysis",
                "set_temp": 815, "actual_temp": 814.5,  // furnace
                "weights": [{"standard": 200, "measured": 200.0001}],  // balance
                "standard_name": "...", "certified_value": 5.2, "measured_value": 5.18  // analysis
            }
        }, ...]
    }
    """
    try:
        data = request.get_json() or {}
        items = data.get("items", [])

        if not items:
            return api_error("No data provided")

        # A-H4: Bulk array size cap
        if len(items) > 100:
            return api_error("Нэг удаад 100-аас их бүртгэл оруулах боломжгүй")

        success, count, error_msg = process_bulk_usage_items(
            items, current_user.id, current_user.username
        )

        if not success:
            return api_error(error_msg, status_code=500)

        return api_success({"count": count}, f"{count} records saved")

    except (SQLAlchemyError, ValueError, TypeError, KeyError) as e:
        db.session.rollback()
        current_app.logger.error(f"Bulk Usage Log Error: {e}")
        return api_error("Бүртгэл хадгалахад алдаа гарлаа", status_code=500)


# -------------------------------------------------
# SUMMARY & STATS
# -------------------------------------------------

@equipment_bp.route("/api/equipment/usage_summary")
@login_required
def api_equipment_usage_summary():
    """Ашиглалтын нэгдсэн тойм API."""
    today = get_shift_date()
    start_str = request.args.get("start_date")
    end_str = request.args.get("end_date")
    category = request.args.get("category", "all")

    try:
        start_dt = datetime.strptime(start_str, "%Y-%m-%d") if start_str else None
    except ValueError:
        start_dt = None
    if not start_dt:
        start_dt = datetime.combine(today - timedelta(days=30), datetime.min.time())

    try:
        end_dt = datetime.strptime(end_str, "%Y-%m-%d") if end_str else None
    except ValueError:
        end_dt = None
    if not end_dt:
        end_dt = datetime.combine(today, datetime.min.time())
    end_dt = end_dt.replace(hour=23, minute=59, second=59)

    rows = get_usage_summary(start_dt, end_dt, category)
    return jsonify({
        "rows": rows,
        "start_date": start_dt.strftime("%Y-%m-%d"),
        "end_date": end_dt.strftime("%Y-%m-%d"),
    })


@equipment_bp.route("/api/equipment/journal_detailed")
@login_required
def api_equipment_journal_detailed():
    """Дэлгэрэнгүй журнал API."""
    start_str = request.args.get("start_date")
    end_str = request.args.get("end_date")
    category = request.args.get("category", "all")
    equipment_id = request.args.get("equipment_id", type=int)

    try:
        start_dt = datetime.strptime(start_str, "%Y-%m-%d") if start_str else None
    except ValueError:
        start_dt = None
    if not start_dt:
        start_dt = now_local() - timedelta(days=30)

    try:
        end_dt = datetime.strptime(end_str, "%Y-%m-%d") if end_str else None
    except ValueError:
        end_dt = None
    if not end_dt:
        end_dt = now_local()
    end_dt = end_dt.replace(hour=23, minute=59, second=59)

    rows = get_journal_detailed(start_dt, end_dt, category, equipment_id)
    return jsonify({"rows": rows})


@equipment_bp.route("/api/equipment/monthly_stats")
@login_required
def api_equipment_monthly_stats():
    """Сарын статистик API."""
    try:
        year = int(request.args.get("year", now_local().year))
    except (ValueError, TypeError):
        year = now_local().year
    category = request.args.get("category", "all")

    rows = get_monthly_stats(year, category)
    return jsonify({"rows": rows, "year": year})


@equipment_bp.route("/api/equipment_list_json")
@login_required
def api_equipment_list_json():
    """Төхөөрөмжийн жагсаалт JSON API (AG Grid-д)."""
    include_retired = request.args.get("include_retired", "false").lower() == "true"
    query = Equipment.query
    if not include_retired:
        query = query.filter(Equipment.status != "retired")
    equipments = query.order_by(Equipment.name.asc()).limit(1000).all()

    data = []
    today = now_local().date()

    for eq in equipments:
        is_expired = False
        if eq.next_calibration_date and eq.next_calibration_date < today:
            is_expired = True

        data.append({
            "id": eq.id,
            "name": eq.name,
            "manufacturer": eq.manufacturer or "",
            "model": eq.model or "",
            "serial_number": eq.serial_number or "",
            "lab_code": eq.lab_code or "",
            "quantity": eq.quantity,
            "location": eq.location or "",
            "calibration_date": eq.calibration_date.strftime('%Y-%m-%d') if eq.calibration_date else "",
            "next_calibration_date": eq.next_calibration_date.strftime('%Y-%m-%d') if eq.next_calibration_date else "",
            "status": eq.status,
            "category": eq.category,
            "is_expired": is_expired
        })

    return jsonify(data)
