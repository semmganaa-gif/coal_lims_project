# app/routes/equipment/api.py
# -*- coding: utf-8 -*-
"""Тоног төхөөрөмжийн API endpoints."""

from flask import request, jsonify, current_app
from flask_login import login_required, current_user
from app import db
from app.models import Equipment, MaintenanceLog, UsageLog
from datetime import datetime, timedelta
from app.utils.datetime import now_local
from app.utils.shifts import get_shift_date
from sqlalchemy import func

from app.routes.equipment import equipment_bp


def _filter_equipment_by_category(query, category):
    """Бүх API-д ашиглах шүүлтүүр."""
    if category and category != "all":
        return query.filter(Equipment.category == category)
    return query


# -------------------------------------------------
# BULK USAGE LOG
# -------------------------------------------------

@equipment_bp.route("/api/log_usage_bulk", methods=["POST"])
@login_required
def log_usage_bulk():
    """
    Frontend-ээс ирсэн олон төхөөрөмжийн бүртгэлийг хүлээж авч хадгална.
    JSON бүтэц: { "items": [ { "eq_id": 1, "minutes": 60, "note": "...", "is_checked": true }, ... ] }
    """
    try:
        data = request.get_json() or {}
        items = data.get("items", [])

        if not items:
            return jsonify({"status": "error", "message": "No data provided"}), 400

        count = 0
        today_date = now_local()

        for item in items:
            eq_id = item.get("eq_id")
            try:
                eq_id = int(eq_id)
            except (TypeError, ValueError):
                continue

            minutes_val = item.get("minutes")
            minutes = float(minutes_val) if minutes_val else 0

            note = item.get("note", "")
            is_checked = item.get("is_checked", False)

            # Засвар бүртгэл
            is_repair = item.get("repair", False)
            if is_repair:
                repair_date_str = item.get("repair_date", "")
                spare_parts = item.get("spare_parts", [])

                desc_parts = []
                if note:
                    desc_parts.append(note)
                for sp in spare_parts:
                    sp_id = sp.get("spare_id")
                    try:
                        sp_id = int(sp_id)
                    except (TypeError, ValueError):
                        continue
                    sp_eq = db.session.get(Equipment, sp_id)
                    sp_name = f"{sp_eq.lab_code or ''} {sp_eq.name}".strip() if sp_eq else f"ID:{sp.get('spare_id')}"
                    desc_parts.append(f"Сэлбэг: {sp_name} x{sp.get('qty', 1)} ({sp.get('used_by', '')})")

                repair_date = None
                if repair_date_str:
                    try:
                        repair_date = datetime.strptime(repair_date_str, "%Y-%m-%d")
                    except ValueError:
                        repair_date = today_date

                mlog = MaintenanceLog(
                    equipment_id=eq_id,
                    action_date=repair_date or today_date,
                    action_type="Repair",
                    description="\n".join(desc_parts) if desc_parts else "Засвар хийгдсэн",
                    performed_by=current_user.username,
                    result="Pass",
                )
                db.session.add(mlog)

            if minutes > 0 or note or is_checked:
                end_time = today_date + timedelta(minutes=minutes)

                purpose_text = note
                if not purpose_text and is_checked:
                    purpose_text = "Daily Check / Routine"

                new_usage = UsageLog(
                    equipment_id=eq_id,
                    start_time=today_date,
                    end_time=end_time,
                    duration_minutes=minutes,
                    used_by=current_user.username,
                    purpose=purpose_text
                )
                db.session.add(new_usage)
                count += 1
            elif is_repair:
                count += 1

        db.session.commit()
        return jsonify({"status": "success", "count": count})

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Bulk Usage Log Error: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


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

    if start_str:
        start_dt = datetime.strptime(start_str, "%Y-%m-%d")
    else:
        start_dt = datetime.combine(today - timedelta(days=30), datetime.min.time())
    if end_str:
        end_dt = datetime.strptime(end_str, "%Y-%m-%d")
    else:
        end_dt = datetime.combine(today, datetime.min.time())
    end_dt = end_dt.replace(hour=23, minute=59, second=59)

    eq_query = _filter_equipment_by_category(Equipment.query, category)
    equipments = eq_query.order_by(Equipment.name.asc()).all()
    eq_ids = [e.id for e in equipments]

    if not eq_ids:
        return jsonify({"rows": []})

    usage_stats = db.session.query(
        UsageLog.equipment_id, func.sum(UsageLog.duration_minutes), func.max(UsageLog.start_time)
    ).filter(
        UsageLog.start_time >= start_dt, UsageLog.start_time <= end_dt, UsageLog.equipment_id.in_(eq_ids)
    ).group_by(UsageLog.equipment_id).all()
    usage_map = {r[0]: {"total": r[1], "last": r[2]} for r in usage_stats}

    maint_stats = db.session.query(
        MaintenanceLog.equipment_id, func.count(MaintenanceLog.id), func.max(MaintenanceLog.action_date)
    ).filter(
        MaintenanceLog.action_date >= start_dt, MaintenanceLog.action_date <= end_dt,
        MaintenanceLog.equipment_id.in_(eq_ids)
    ).group_by(MaintenanceLog.equipment_id).all()
    maint_map = {r[0]: {"cnt": r[1], "last": r[2]} for r in maint_stats}

    rows = []
    for eq in equipments:
        u = usage_map.get(eq.id, {})
        m = maint_map.get(eq.id, {})
        total_mins = int(u.get("total") or 0)
        is_expired = (eq.next_calibration_date and eq.next_calibration_date < today)

        rows.append({
            "equipment_id": eq.id, "lab_code": eq.lab_code, "name": eq.name,
            "location": eq.location, "room": eq.room_number, "status": eq.status or "normal",
            "total_usage_hours": round(total_mins/60.0, 2), "maintenance_count": m.get("cnt", 0),
            "last_usage_end": u.get("last", None), "last_maintenance": m.get("last", None),
            "next_calibration_date": (
                eq.next_calibration_date.strftime("%Y-%m-%d")
                if eq.next_calibration_date else None
            ),
            "is_calibration_expired": is_expired
        })
    return jsonify({"rows": rows, "start_date": start_dt.strftime("%Y-%m-%d"), "end_date": end_dt.strftime("%Y-%m-%d")})


@equipment_bp.route("/api/equipment/journal_detailed")
@login_required
def api_equipment_journal_detailed():
    """Дэлгэрэнгүй журнал API."""
    start_str = request.args.get("start_date")
    end_str = request.args.get("end_date")
    category = request.args.get("category", "all")

    start_dt = datetime.strptime(start_str, "%Y-%m-%d") if start_str else now_local() - timedelta(days=30)
    end_dt = datetime.strptime(end_str, "%Y-%m-%d") if end_str else now_local()
    end_dt = end_dt.replace(hour=23, minute=59, second=59)

    m_logs = db.session.query(MaintenanceLog, Equipment).join(Equipment).filter(
        MaintenanceLog.action_date >= start_dt, MaintenanceLog.action_date <= end_dt
    )
    m_logs = _filter_equipment_by_category(m_logs, category).all()

    u_logs = db.session.query(UsageLog, Equipment).join(Equipment).filter(
        UsageLog.start_time >= start_dt, UsageLog.start_time <= end_dt
    )
    u_logs = _filter_equipment_by_category(u_logs, category).all()

    combined = []
    for log, eq in m_logs:
        combined.append({
            "date": log.action_date.strftime("%Y-%m-%d %H:%M"), "timestamp": log.action_date.timestamp(),
            "lab_code": eq.lab_code, "equipment": eq.name, "category": "Maintenance", "type": log.action_type,
            "user": log.performed_by, "description": log.description, "result": log.result or ""
        })
    for log, eq in u_logs:
        combined.append({
            "date": log.start_time.strftime("%Y-%m-%d %H:%M"), "timestamp": log.start_time.timestamp(),
            "lab_code": eq.lab_code, "equipment": eq.name, "category": "Usage", "type": "Ашиглалт",
            "user": "-", "description": f"{log.duration_minutes} мин", "result": "Normal"
        })

    combined.sort(key=lambda x: x["timestamp"], reverse=True)
    return jsonify({"rows": combined})


@equipment_bp.route("/api/equipment/monthly_stats")
@login_required
def api_equipment_monthly_stats():
    """Сарын статистик API."""
    year = int(request.args.get("year", now_local().year))
    category = request.args.get("category", "all")

    start_dt = datetime(year, 1, 1)
    end_dt = datetime(year, 12, 31, 23, 59, 59)

    eq_query = _filter_equipment_by_category(Equipment.query, category)
    equips = eq_query.all()
    eq_ids = [e.id for e in equips]

    if not eq_ids:
        return jsonify({"rows": [], "year": year})

    data_map = {
        e.id: {"lab_code": e.lab_code, "name": e.name, "months": {m: {"usage": 0, "maint": 0} for m in range(1, 13)}}
        for e in equips
    }

    usage_rows = db.session.query(
        UsageLog.equipment_id, func.extract('month', UsageLog.start_time), func.sum(UsageLog.duration_minutes)
    ).filter(
        UsageLog.start_time.between(start_dt, end_dt), UsageLog.equipment_id.in_(eq_ids)
    ).group_by(UsageLog.equipment_id, func.extract('month', UsageLog.start_time)).all()
    for eid, mon, val in usage_rows:
        if eid in data_map:
            data_map[eid]["months"][int(mon)]["usage"] = int(val or 0)

    maint_rows = db.session.query(
        MaintenanceLog.equipment_id, func.extract('month', MaintenanceLog.action_date), func.count(MaintenanceLog.id)
    ).filter(
        MaintenanceLog.action_date.between(start_dt, end_dt), MaintenanceLog.equipment_id.in_(eq_ids)
    ).group_by(MaintenanceLog.equipment_id, func.extract('month', MaintenanceLog.action_date)).all()
    for eid, mon, val in maint_rows:
        if eid in data_map:
            data_map[eid]["months"][int(mon)]["maint"] = int(val or 0)

    rows = []
    for eid, info in data_map.items():
        row = {"lab_code": info["lab_code"], "name": info["name"]}
        for m in range(1, 13):
            row[f"usage_{m}"] = info["months"][m]["usage"]
            row[f"maint_{m}"] = info["months"][m]["maint"]
        rows.append(row)

    return jsonify({"rows": rows, "year": year})


@equipment_bp.route("/api/equipment_list_json")
@login_required
def api_equipment_list_json():
    """Төхөөрөмжийн жагсаалт JSON API (AG Grid-д)."""
    equipments = Equipment.query.order_by(Equipment.name.asc()).all()

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
