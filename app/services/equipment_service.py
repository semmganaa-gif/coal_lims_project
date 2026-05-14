# app/services/equipment_service.py
# -*- coding: utf-8 -*-
"""Equipment business logic — extracted from routes/equipment/api.py."""

import logging
from datetime import datetime, timedelta

from sqlalchemy import func
from flask_babel import lazy_gettext as _l
from sqlalchemy.exc import SQLAlchemyError

from app import db
from app.models import (
    Equipment, MaintenanceLog, UsageLog,
    SparePart, SparePartUsage, SparePartLog,
)
from app.utils.datetime import now_local
from app.utils.shifts import get_shift_date
from app.utils.audit import log_audit
from app.utils.transaction import transactional

logger = logging.getLogger(__name__)


def _filter_equipment_by_category(query, category):
    """Equipment query-г category-р шүүнэ."""
    if category and category != "all":
        return query.filter(Equipment.category == category)
    return query


# -------------------------------------------------
# CALIBRATION DESCRIPTION BUILDER
# -------------------------------------------------

def build_calibration_description(calibration):
    """
    Calibration dict-ээс тайлбар болон үр дүн үүсгэнэ.

    Args:
        calibration: dict with 'type' key and type-specific fields.

    Returns:
        tuple[list[str], str]: (desc_parts, result) where result is "Pass" or "Fail".
    """
    calib_type = calibration.get("type", "")
    desc_parts = []
    result = "Pass"

    if calib_type == "temperature":
        set_temp = calibration.get("set_temp")
        actual_temp = calibration.get("actual_temp")
        if set_temp is not None and actual_temp is not None:
            diff = actual_temp - set_temp
            desc_parts.append(f"Тохируулсан: {set_temp}\u00b0C")
            desc_parts.append(f"Хэмжсэн: {actual_temp}\u00b0C")
            desc_parts.append(f"Зөрүү: {'+' if diff >= 0 else ''}{diff:.1f}\u00b0C")
            if abs(diff) > 5:
                result = "Fail"

    elif calib_type == "weight":
        weights = calibration.get("weights", [])
        for i, w in enumerate(weights, 1):
            std = w.get("standard")
            meas = w.get("measured")
            if std is not None and meas is not None:
                diff = abs(meas - std)
                tolerance = 0.0002 if std < 1 else 0.001
                status = "OK" if diff <= tolerance else "FAIL"
                desc_parts.append(f"Жин {i}: Стд={std}g, Хэмжсэн={meas}g ({status})")
                if diff > tolerance:
                    result = "Fail"

        # Этанол туухайн шалгалт
        ethanol = calibration.get("ethanol")
        if ethanol:
            eth_temp = ethanol.get("temperature")
            eth_density = ethanol.get("density")
            eth_volume = ethanol.get("volume")
            eth_expected = ethanol.get("expected")
            eth_measured = ethanol.get("measured")
            desc_parts.append(_l("Этанол туухай шалгалт:"))
            if eth_temp is not None:
                desc_parts.append(f"  Температур: {eth_temp}\u00b0C")
            if eth_density is not None:
                desc_parts.append(f"  Нягт: {eth_density} g/mL")
            if eth_volume is not None:
                desc_parts.append(f"  Эзэлхүүн: {eth_volume} mL")
            if eth_expected is not None and eth_measured is not None:
                diff = abs(eth_measured - eth_expected)
                eth_status = "OK" if diff <= 0.001 else "FAIL"
                desc_parts.append(
                    f"  Тооцоолсон: {eth_expected:.4f}g, Хэмжсэн: {eth_measured:.4f}g ({eth_status})"
                )
                if diff > 0.001:
                    result = "Fail"

    elif calib_type in ("sulfur", "xrf_calib"):
        # Хүхэр / Фосфор / Фтор / Хлор багаж калибровка
        curve_type = calibration.get("curve_type", "linear")
        rms_error = calibration.get("rms_error")
        standards = calibration.get("standards", [])
        verifications = calibration.get("verifications", [])

        calib_label = _l("XRF калибровка") if calib_type == "xrf_calib" else _l("Хүхэр багаж калибровка")
        desc_parts.append(f"{calib_label} ({curve_type.capitalize()}):")
        if rms_error is not None:
            desc_parts.append(f"  RMS Error: {rms_error:.4f}")

        for i, std in enumerate(standards, 1):
            name = std.get("name", f"Стд {i}")
            weight = std.get("weight")
            moisture = std.get("moisture")
            cert = std.get("certified")
            meas = std.get("measured")
            parts = [f"{i}. {name}"]
            if weight:
                parts.append(f"Wt={weight}g")
            if moisture:
                parts.append(f"M={moisture}%")
            if cert is not None and meas is not None:
                diff_pct = abs((meas - cert) / cert * 100) if cert else 0
                status = "OK" if diff_pct <= 5 else "FAIL"
                parts.append(f"St,d={meas}%")
                parts.append(f"Cert={cert}%")
                parts.append(f"({status})")
                if diff_pct > 5:
                    result = "Fail"
            desc_parts.append("  " + " | ".join(parts))

        if verifications:
            desc_parts.append(_l("Шалгалт:"))
            for i, v in enumerate(verifications, 1):
                name = v.get("name", f"Шалг {i}")
                cert = v.get("certified")
                meas = v.get("measured")
                if cert is not None and meas is not None:
                    diff_pct = abs((meas - cert) / cert * 100) if cert else 0
                    status = "OK" if diff_pct <= 5 else "FAIL"
                    desc_parts.append(f"  {i}. {name}: St,d={meas}%, Cert={cert}% ({status})")
                    if diff_pct > 5:
                        result = "Fail"

    elif calib_type == "calorimeter":
        # Илчлэг багаж - 5 хэмжилт
        std_name = calibration.get("standard_name", _l("Бензой хүчил"))
        cert_val = calibration.get("certified_value", 26454)
        prev_cap = calibration.get("prev_heat_capacity")
        bomb_cap = calibration.get("bomb_heat_capacity")
        measurements = calibration.get("measurements", [])
        if measurements:
            avg = sum(measurements) / len(measurements)
            if len(measurements) >= 2:
                std_dev = (sum((x - avg) ** 2 for x in measurements) / (len(measurements) - 1)) ** 0.5
                rsd = (std_dev / avg) * 100 if avg else 0
            else:
                rsd = 0
            avg_diff = abs(avg - cert_val)
            desc_parts.append(f"Илчлэг багаж ({std_name}):")
            desc_parts.append(f"  Баталгаат: {cert_val} J/g")
            desc_parts.append(f"  Хэмжилтүүд: {', '.join(str(int(m)) for m in measurements)}")
            desc_parts.append(f"  Дундаж: {avg:.0f}, RSD: {rsd:.3f}%")
            if prev_cap:
                desc_parts.append(f"  Өмнөх C: {prev_cap} J/\u00b0C")
            if bomb_cap:
                desc_parts.append(f"  C: {bomb_cap} J/\u00b0C")
            if rsd > 0.1 or avg_diff > 60:
                result = "Fail"
                desc_parts.append(f"  Шалтгаан: {'RSD > 0.1%' if rsd > 0.1 else _l('Зөрүү > 60 J/g')}")

    elif calib_type == "analysis":
        std_name = calibration.get("standard_name", "")
        cert_val = calibration.get("certified_value")
        meas_val = calibration.get("measured_value")
        if cert_val is not None and meas_val is not None:
            diff_pct = (meas_val - cert_val) / cert_val * 100 if cert_val else 0
            desc_parts.append(f"Стандарт: {std_name}")
            desc_parts.append(f"Баталгаат: {cert_val}")
            desc_parts.append(f"Хэмжсэн: {meas_val}")
            desc_parts.append(f"Зөрүү: {'+' if diff_pct >= 0 else ''}{diff_pct:.2f}%")
            if abs(diff_pct) > 2:
                result = "Fail"

    elif calib_type == "csn_crucible":
        # Хоосон тигелийн туршилт (CSN)
        start_temp = calibration.get("start_temp")
        max_current = calibration.get("max_current_sec")
        tests = calibration.get("tests", [])
        adjustments = calibration.get("adjustments", [])
        final_pass = calibration.get("final_pass", False)

        desc_parts.append(_l("Хоосон тигелийн туршилт (CSN):"))
        if start_temp:
            desc_parts.append(f"  Эхлэх темп: {start_temp}\u00b0C")
        if max_current:
            desc_parts.append(f"  Max гүйдэл: {max_current} сек")

        for i, t in enumerate(tests, 1):
            t1 = t.get("temp_1min", "")
            t130 = t.get("temp_1m30", "")
            t230 = t.get("temp_2m30", "")
            passed = "OK" if t.get("pass") else "FAIL"
            desc_parts.append(
                f"  T{i}: 1мин={t1}\u00b0C, "
                f"1:30={t130}\u00b0C, "
                f"2:30={t230}\u00b0C \u2192 {passed}"
            )

        for i, a in enumerate(adjustments, 1):
            adj_temp = a.get("start_temp", "")
            adj_current = a.get("max_current_sec", "")
            desc_parts.append(f"  Тохируулга {i}: темп={adj_temp}\u00b0C, гүйдэл={adj_current}сек")

        result = "Pass" if final_pass else "Fail"

    elif calib_type == "drum":
        # Барабан калибровка
        meas_1min = calibration.get("meas_1min")
        meas_5min = calibration.get("meas_5min")

        if meas_1min is not None or meas_5min is not None:
            # Gi барабан
            initial_rpm = calibration.get("initial_rpm")
            target_1 = calibration.get("target_1min", 50)
            target_5 = calibration.get("target_5min", 250)
            drum_pass = calibration.get("pass", False)

            desc_parts.append(_l("Барабан калибровка (Gi):"))
            if initial_rpm is not None:
                desc_parts.append(f"  Эхний эргэлт: {initial_rpm}")
            if meas_1min is not None:
                ok1 = "OK" if meas_1min == target_1 else "FAIL"
                desc_parts.append(f"  1 мин: {meas_1min} (зорилт={target_1}) \u2192 {ok1}")
            if meas_5min is not None:
                ok5 = "OK" if meas_5min == target_5 else "FAIL"
                desc_parts.append(f"  5 мин: {meas_5min} (зорилт={target_5}) \u2192 {ok5}")
            result = "Pass" if drum_pass else "Fail"
        else:
            # Prep drum — before/after format
            before_rpm = calibration.get("before")
            after_rpm = calibration.get("after")
            duration = calibration.get("duration", "")
            desc_parts.append(_l("Тээрэм калибровка:"))
            if duration:
                desc_parts.append(f"  Хугацаа: {duration} мин")
            if before_rpm is not None and after_rpm is not None:
                diff = abs(after_rpm - before_rpm)
                desc_parts.append(f"  Өмнө: {before_rpm} RPM, Дараа: {after_rpm} RPM, Зөрүү: {diff}")
                result = "Pass" if diff <= 2 else "Fail"

    return desc_parts, result


# -------------------------------------------------
# BULK USAGE PROCESSING
# -------------------------------------------------

def process_bulk_usage_items(items, user_id, username):
    """
    Олон төхөөрөмжийн бүртгэлийг боловсруулж DB-д хадгална.

    Args:
        items: list[dict] — бүртгэлийн жагсаалт.
        user_id: int — current user id.
        username: str — current user username.

    Returns:
        tuple[bool, int, str|None]: (success, count, error_message).
    """
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

        # Калибровка/шалгалт бүртгэл
        calibration = item.get("calibration")
        if calibration:
            desc_parts, result = build_calibration_description(calibration)

            if desc_parts:
                freq = calibration.get("frequency", "daily")
                freq_map = {
                    "daily": _l("Өдөр тутам"),
                    "monthly": _l("Сар болгон"),
                    "adjustment": _l("Тохируулга"),
                }
                freq_label = freq_map.get(freq, freq)
                desc_parts.insert(0, f"[{freq_label}]")

                action_type_map = {
                    "temperature": "Temperature Check",
                    "sulfur": "Sulfur Calibration",
                    "calorimeter": "Calorimeter Calibration",
                    "weight": "Balance Check",
                    "analysis": "Calibration Check",
                    "csn_crucible": "CSN Crucible Test",
                    "drum": "Drum Calibration",
                    "xrf_calib": "XRF Calibration",
                }
                calib_type = calibration.get("type", "")
                mlog = MaintenanceLog(
                    equipment_id=eq_id,
                    action_date=today_date,
                    action_type=action_type_map.get(calib_type, "Check"),
                    description="\n".join(desc_parts),
                    performed_by=username,
                    performed_by_id=user_id,
                    result=result,
                )
                db.session.add(mlog)
                count += 1

        # Засвар бүртгэл
        is_repair = item.get("repair", False)
        if is_repair:
            repair_date_str = item.get("repair_date", "")
            spare_parts = item.get("spare_parts", [])

            repair_desc_parts = []
            if note:
                repair_desc_parts.append(note)

            # SparePart модел ашиглаж exceeds stock хасах
            for sp in spare_parts:
                sp_id = sp.get("spare_id")
                try:
                    sp_id = int(sp_id)
                except (TypeError, ValueError):
                    continue

                sp_item = db.session.get(SparePart, sp_id)
                if not sp_item:
                    continue

                qty_used = int(sp.get('qty', 1))
                used_by = sp.get('used_by', username)
                sp_name = sp_item.name

                # Нөөцөөс хасах
                old_qty = sp_item.quantity
                if qty_used <= sp_item.quantity:
                    sp_item.quantity -= qty_used
                    sp_item.update_status()

                    # SparePartUsage бүртгэл
                    usage = SparePartUsage(
                        spare_part_id=sp_id,
                        equipment_id=eq_id,
                        quantity_used=qty_used,
                        unit=sp_item.unit,
                        purpose=f"Засвар: {note}" if note else str(_l("Засвар")),
                        used_by_id=user_id,
                        quantity_before=old_qty,
                        quantity_after=sp_item.quantity,
                    )
                    db.session.add(usage)

                    # SparePartLog аудит (with hash - ISO 17025)
                    sp_log = SparePartLog(
                        spare_part_id=sp_id,
                        action='consumed',
                        quantity_change=-qty_used,
                        quantity_before=old_qty,
                        quantity_after=sp_item.quantity,
                        user_id=user_id,
                        details=f"Засвар: Equipment ID {eq_id}"
                    )
                    sp_log.data_hash = sp_log.compute_hash()
                    db.session.add(sp_log)

                repair_desc_parts.append(f"Сэлбэг: {sp_name} x{qty_used} ({used_by})")

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
                description="\n".join(repair_desc_parts) if repair_desc_parts else str(_l("Засвар хийгдсэн")),
                performed_by=username,
                performed_by_id=user_id,
                result="Pass",
            )
            db.session.add(mlog)

        if minutes > 0 or note:
            end_time = today_date + timedelta(minutes=minutes)

            purpose_text = note
            if not purpose_text:
                purpose_text = "Daily Check / Routine"

            new_usage = UsageLog(
                equipment_id=eq_id,
                start_time=today_date,
                end_time=end_time,
                duration_minutes=minutes,
                used_by=username,
                used_by_id=user_id,
                purpose=purpose_text,
            )
            db.session.add(new_usage)
            count += 1
        elif is_repair:
            count += 1

    @transactional()
    def _persist():
        pass  # objects added to session — commit нь @transactional-аар

    try:
        _persist()
    except SQLAlchemyError as e:
        logger.error("Bulk usage log commit error: %s", e)
        return False, 0, _l("Хадгалахад алдаа гарлаа")

    # Audit log
    if count > 0:
        log_audit(
            action='bulk_usage_log',
            resource_type='Equipment',
            resource_id=None,
            details={'count': count, 'items_count': len(items)}
        )

    return True, count, None


# -------------------------------------------------
# SUMMARY & STATS
# -------------------------------------------------

def get_usage_summary(start_dt, end_dt, category):
    """
    Ашиглалтын нэгдсэн тойм.

    Args:
        start_dt: datetime — эхлэх огноо.
        end_dt: datetime — дуусах огноо (23:59:59 байх ёстой).
        category: str — "all" эсвэл equipment category.

    Returns:
        list[dict]: rows list.
    """
    today = get_shift_date()

    eq_query = _filter_equipment_by_category(Equipment.query, category)
    equipments = eq_query.order_by(Equipment.name.asc()).all()
    eq_ids = [e.id for e in equipments]

    if not eq_ids:
        return []

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
            "total_usage_hours": round(total_mins / 60.0, 2), "maintenance_count": m.get("cnt", 0),
            "last_usage_end": u.get("last", None), "last_maintenance": m.get("last", None),
            "next_calibration_date": (
                eq.next_calibration_date.strftime("%Y-%m-%d")
                if eq.next_calibration_date else None
            ),
            "is_calibration_expired": is_expired,
        })
    return rows


def get_journal_detailed(start_dt, end_dt, category, equipment_id=None):
    """
    Дэлгэрэнгүй журнал.

    Args:
        start_dt: datetime — эхлэх огноо.
        end_dt: datetime — дуусах огноо (23:59:59 байх ёстой).
        category: str — "all" эсвэл equipment category.
        equipment_id: int|None — тодорхой equipment-р шүүх.

    Returns:
        list[dict]: combined sorted rows (newest first).
    """
    m_logs = db.session.query(MaintenanceLog, Equipment).join(Equipment).filter(
        MaintenanceLog.action_date >= start_dt, MaintenanceLog.action_date <= end_dt
    )
    u_logs = db.session.query(UsageLog, Equipment).join(Equipment).filter(
        UsageLog.start_time >= start_dt, UsageLog.start_time <= end_dt
    )

    if equipment_id:
        m_logs = m_logs.filter(MaintenanceLog.equipment_id == equipment_id)
        u_logs = u_logs.filter(UsageLog.equipment_id == equipment_id)
    else:
        m_logs = _filter_equipment_by_category(m_logs, category)
        u_logs = _filter_equipment_by_category(u_logs, category)

    m_logs = m_logs.all()
    u_logs = u_logs.all()

    combined = []
    for log, eq in m_logs:
        combined.append({
            "date": log.action_date.strftime("%Y-%m-%d %H:%M"), "timestamp": log.action_date.timestamp(),
            "equipment_id": eq.id, "lab_code": eq.lab_code, "equipment": eq.name,
            "category": "Maintenance", "type": log.action_type,
            "duration": "", "user": log.performed_by, "user_id": log.performed_by_id,
            "description": log.description, "result": log.result or "",
            "log_id": log.id,
            "has_file": bool(log.file_path),
            "certificate_no": log.certificate_no or "",
        })
    for log, eq in u_logs:
        combined.append({
            "date": log.start_time.strftime("%Y-%m-%d %H:%M"), "timestamp": log.start_time.timestamp(),
            "equipment_id": eq.id, "lab_code": eq.lab_code, "equipment": eq.name,
            "category": "Usage", "type": _l("Ашиглалт"),
            "duration": f"{log.duration_minutes} мин" if log.duration_minutes else "",
            "user": log.used_by or "-", "user_id": log.used_by_id,
            "description": log.purpose or "", "result": "",
            "log_id": None, "has_file": False, "certificate_no": "",
        })

    combined.sort(key=lambda x: x["timestamp"], reverse=True)
    return combined


def get_monthly_stats(year, category):
    """
    Сарын статистик.

    Args:
        year: int — жил.
        category: str — "all" эсвэл equipment category.

    Returns:
        list[dict]: rows list.
    """
    start_dt = datetime(year, 1, 1)
    end_dt = datetime(year, 12, 31, 23, 59, 59)

    eq_query = _filter_equipment_by_category(Equipment.query, category)
    equips = eq_query.all()
    eq_ids = [e.id for e in equips]

    if not eq_ids:
        return []

    data_map = {
        e.id: {
            "lab_code": e.lab_code, "name": e.name,
            "months": {m: {"usage": 0, "maint": 0} for m in range(1, 13)},
        }
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
        row = {"equipment_id": eid, "lab_code": info["lab_code"], "name": info["name"]}
        for m in range(1, 13):
            row[f"usage_{m}"] = info["months"][m]["usage"]
            row[f"maint_{m}"] = info["months"][m]["maint"]
        rows.append(row)

    return rows
