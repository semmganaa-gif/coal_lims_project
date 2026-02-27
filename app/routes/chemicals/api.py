# app/routes/chemicals/api.py
# -*- coding: utf-8 -*-
"""Химийн бодисын API endpoints."""

from datetime import datetime, date, timedelta

from flask import request, jsonify, current_app
from flask_login import login_required, current_user
from sqlalchemy import func

from app import db
from app.models import Chemical, ChemicalUsage, ChemicalLog
from app.routes.chemicals import chemicals_bp
from app.routes.api.helpers import api_success, api_error
from app.utils.security import escape_like_pattern


# -------------------------------------------------
# 1. Жагсаалт API (AG Grid-д)
# -------------------------------------------------

@chemicals_bp.route("/api/list")
@login_required
def api_chemical_list():
    """Химийн бодисын жагсаалт JSON API."""
    lab = request.args.get("lab", "all")
    category = request.args.get("category", "all")
    status = request.args.get("status", "all")
    include_disposed = request.args.get("include_disposed", "false") == "true"

    query = Chemical.query

    # Шүүлтүүр
    if lab and lab != "all":
        query = query.filter(
            (Chemical.lab_type == lab) | (Chemical.lab_type == 'all')
        )

    if category and category != "all":
        query = query.filter(Chemical.category == category)

    if status and status != "all":
        query = query.filter(Chemical.status == status)

    if not include_disposed:
        query = query.filter(Chemical.status != 'disposed')

    # ✅ Limit нэмсэн
    chemicals = query.order_by(Chemical.name.asc()).limit(2000).all()
    today = date.today()
    warning_date = today + timedelta(days=30)

    data = []
    for c in chemicals:
        is_expiring = c.expiry_date and c.expiry_date <= warning_date and c.expiry_date > today
        is_expired = c.expiry_date and c.expiry_date <= today

        data.append({
            "id": c.id,
            "name": c.name,
            "formula": c.formula or "",
            "cas_number": c.cas_number or "",
            "manufacturer": c.manufacturer or "",
            "lot_number": c.lot_number or "",
            "grade": c.grade or "",
            "quantity": c.quantity,
            "unit": c.unit,
            "reorder_level": c.reorder_level,
            "expiry_date": c.expiry_date.strftime("%Y-%m-%d") if c.expiry_date else "",
            "storage_location": c.storage_location or "",
            "lab_type": c.lab_type,
            "category": c.category,
            "status": c.status,
            "is_low_stock": c.status == 'low_stock',
            "is_expiring": is_expiring,
            "is_expired": is_expired,
        })

    return jsonify(data)


# -------------------------------------------------
# 2. Бага нөөцтэй (Low Stock Alert)
# -------------------------------------------------

@chemicals_bp.route("/api/low_stock")
@login_required
def api_low_stock():
    """Бага нөөцтэй химийн бодисууд."""
    lab = request.args.get("lab", "all")

    query = Chemical.query.filter(Chemical.status == 'low_stock')

    if lab and lab != "all":
        query = query.filter(
            (Chemical.lab_type == lab) | (Chemical.lab_type == 'all')
        )

    chemicals = query.order_by(Chemical.name.asc()).all()

    data = [{
        "id": c.id,
        "name": c.name,
        "quantity": c.quantity,
        "unit": c.unit,
        "reorder_level": c.reorder_level,
        "lab_type": c.lab_type,
    } for c in chemicals]

    return jsonify({
        "count": len(data),
        "items": data
    })


# -------------------------------------------------
# 3. Хугацаа дуусах (Expiring Soon)
# -------------------------------------------------

@chemicals_bp.route("/api/expiring")
@login_required
def api_expiring():
    """Хугацаа дуусах химийн бодисууд."""
    lab = request.args.get("lab", "all")
    days = int(request.args.get("days", 30))

    today = date.today()
    warning_date = today + timedelta(days=days)

    query = Chemical.query.filter(
        Chemical.expiry_date <= warning_date,
        Chemical.expiry_date >= today,
        Chemical.status != 'disposed'
    )

    if lab and lab != "all":
        query = query.filter(
            (Chemical.lab_type == lab) | (Chemical.lab_type == 'all')
        )

    chemicals = query.order_by(Chemical.expiry_date.asc()).all()

    data = [{
        "id": c.id,
        "name": c.name,
        "expiry_date": c.expiry_date.strftime("%Y-%m-%d"),
        "days_left": (c.expiry_date - today).days,
        "quantity": c.quantity,
        "unit": c.unit,
        "lab_type": c.lab_type,
    } for c in chemicals]

    return jsonify({
        "count": len(data),
        "items": data
    })


# -------------------------------------------------
# 4. Хэрэглээ бүртгэх API
# -------------------------------------------------

@chemicals_bp.route("/api/consume", methods=["POST"])
@login_required
def api_consume():
    """Химийн бодисын хэрэглээ бүртгэх API."""
    try:
        data = request.get_json() or {}

        chemical_id = data.get("chemical_id")
        quantity_used = float(data.get("quantity_used", 0))
        purpose = data.get("purpose", "")
        analysis_code = data.get("analysis_code")
        sample_id = data.get("sample_id")

        if not chemical_id or quantity_used <= 0:
            return api_error("Invalid data")

        chemical = Chemical.query.get(chemical_id)
        if not chemical:
            return api_error("Chemical not found", status_code=404)

        if quantity_used > chemical.quantity:
            return api_error(f"Insufficient stock. Available: {chemical.quantity} {chemical.unit}")

        old_quantity = chemical.quantity
        chemical.quantity -= quantity_used
        new_quantity = chemical.quantity

        # Хэрэглээний бүртгэл
        usage = ChemicalUsage(
            chemical_id=chemical.id,
            quantity_used=quantity_used,
            unit=chemical.unit,
            purpose=purpose,
            analysis_code=analysis_code,
            used_by_id=current_user.id,
            quantity_before=old_quantity,
            quantity_after=new_quantity,
        )

        if sample_id:
            try:
                usage.sample_id = int(sample_id)
            except ValueError:
                pass

        db.session.add(usage)

        if not chemical.opened_date:
            chemical.opened_date = date.today()

        chemical.update_status()

        # Аудит лог (with hash - ISO 17025)
        log = ChemicalLog(
            chemical_id=chemical.id,
            user_id=current_user.id,
            action='consumed',
            quantity_change=-quantity_used,
            quantity_before=old_quantity,
            quantity_after=new_quantity,
            details=purpose
        )
        log.data_hash = log.compute_hash()
        db.session.add(log)

        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"API consume commit error: {e}")
            return api_error("Хэрэглээ хадгалахад алдаа гарлаа", status_code=500)

        return api_success({
            "new_quantity": new_quantity,
            "chemical_status": chemical.status
        }, f"Consumed {quantity_used} {chemical.unit}")

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"API consume error: {e}")
        return api_error(str(e), status_code=500)


# -------------------------------------------------
# 5. Хайлт / Autocomplete
# -------------------------------------------------

@chemicals_bp.route("/api/search")
@login_required
def api_search():
    """Химийн бодис хайх (autocomplete)."""
    q = request.args.get("q", "").strip()
    lab = request.args.get("lab", "all")
    limit = int(request.args.get("limit", 20))

    if len(q) < 2:
        return jsonify([])

    # ✅ SQL Injection хамгаалалт
    safe_q = escape_like_pattern(q)
    query = Chemical.query.filter(
        Chemical.status != 'disposed',
        (Chemical.name.ilike(f"%{safe_q}%") |
         Chemical.formula.ilike(f"%{safe_q}%") |
         Chemical.cas_number.ilike(f"%{safe_q}%"))
    )

    if lab and lab != "all":
        query = query.filter(
            (Chemical.lab_type == lab) | (Chemical.lab_type == 'all')
        )

    chemicals = query.order_by(Chemical.name.asc()).limit(limit).all()

    data = [{
        "id": c.id,
        "name": c.name,
        "formula": c.formula or "",
        "quantity": c.quantity,
        "unit": c.unit,
        "status": c.status,
        "label": f"{c.name} ({c.formula})" if c.formula else c.name
    } for c in chemicals]

    return jsonify(data)


# -------------------------------------------------
# 6. Статистик (Dashboard)
# -------------------------------------------------

@chemicals_bp.route("/api/stats")
@login_required
def api_stats():
    """Химийн бодисын статистик."""
    lab = request.args.get("lab", "all")
    today = date.today()
    warning_date = today + timedelta(days=30)

    base_query = Chemical.query.filter(Chemical.status != 'disposed')

    if lab and lab != "all":
        base_query = base_query.filter(
            (Chemical.lab_type == lab) | (Chemical.lab_type == 'all')
        )

    total = base_query.count()
    low_stock = base_query.filter(Chemical.status == 'low_stock').count()
    expired = base_query.filter(Chemical.status == 'expired').count()
    expiring = base_query.filter(
        Chemical.expiry_date <= warning_date,
        Chemical.expiry_date > today
    ).count()

    # Категориор
    by_category = db.session.query(
        Chemical.category,
        func.count(Chemical.id)
    ).filter(
        Chemical.status != 'disposed'
    )

    if lab and lab != "all":
        by_category = by_category.filter(
            (Chemical.lab_type == lab) | (Chemical.lab_type == 'all')
        )

    by_category = by_category.group_by(Chemical.category).all()

    return jsonify({
        "total": total,
        "low_stock": low_stock,
        "expired": expired,
        "expiring": expiring,
        "by_category": {cat: cnt for cat, cnt in by_category}
    })


# -------------------------------------------------
# 7. Хэрэглээний түүх API
# -------------------------------------------------

@chemicals_bp.route("/api/usage_history")
@login_required
def api_usage_history():
    """Химийн бодисын хэрэглээний түүх."""
    chemical_id = request.args.get("chemical_id")
    lab = request.args.get("lab", "all")
    start_date = request.args.get("start_date")
    end_date = request.args.get("end_date")
    limit = int(request.args.get("limit", 100))

    query = db.session.query(ChemicalUsage, Chemical).join(Chemical)

    if chemical_id:
        query = query.filter(ChemicalUsage.chemical_id == int(chemical_id))

    if lab and lab != "all":
        query = query.filter(
            (Chemical.lab_type == lab) | (Chemical.lab_type == 'all')
        )

    if start_date:
        start_dt = datetime.strptime(start_date, "%Y-%m-%d")
        query = query.filter(ChemicalUsage.used_at >= start_dt)

    if end_date:
        end_dt = datetime.strptime(end_date, "%Y-%m-%d")
        end_dt = end_dt.replace(hour=23, minute=59, second=59)
        query = query.filter(ChemicalUsage.used_at <= end_dt)

    usages = query.order_by(ChemicalUsage.used_at.desc()).limit(limit).all()

    data = [{
        "id": u.id,
        "chemical_id": u.chemical_id,
        "chemical_name": c.name,
        "quantity_used": u.quantity_used,
        "unit": u.unit or c.unit,
        "purpose": u.purpose or "",
        "analysis_code": u.analysis_code or "",
        "used_at": u.used_at.strftime("%Y-%m-%d %H:%M") if u.used_at else "",
        "used_by": u.used_by.username if u.used_by else "",
    } for u, c in usages]

    return jsonify({"items": data, "count": len(data)})


# -------------------------------------------------
# 8. Bulk Consume (Олон бодис нэг дор хэрэглэх)
# -------------------------------------------------

@chemicals_bp.route("/api/consume_bulk", methods=["POST"])
@login_required
def api_consume_bulk():
    """Олон химийн бодис нэг дор хэрэглээ бүртгэх."""
    try:
        data = request.get_json() or {}
        items = data.get("items", [])
        purpose = data.get("purpose", "")
        analysis_code = data.get("analysis_code")
        sample_id = data.get("sample_id")

        if not items:
            return api_error("No items provided")

        count = 0
        errors = []

        for item in items:
            chemical_id = item.get("chemical_id")
            quantity_used = float(item.get("quantity_used", 0))

            if not chemical_id or quantity_used <= 0:
                continue

            chemical = Chemical.query.get(chemical_id)
            if not chemical:
                errors.append(f"Chemical {chemical_id} not found")
                continue

            if quantity_used > chemical.quantity:
                errors.append(f"{chemical.name}: insufficient stock")
                continue

            old_quantity = chemical.quantity
            chemical.quantity -= quantity_used
            new_quantity = chemical.quantity

            usage = ChemicalUsage(
                chemical_id=chemical.id,
                quantity_used=quantity_used,
                unit=chemical.unit,
                purpose=purpose,
                analysis_code=analysis_code,
                used_by_id=current_user.id,
                quantity_before=old_quantity,
                quantity_after=new_quantity,
            )

            if sample_id:
                try:
                    usage.sample_id = int(sample_id)
                except ValueError:
                    pass

            db.session.add(usage)

            if not chemical.opened_date:
                chemical.opened_date = date.today()

            chemical.update_status()

            log = ChemicalLog(
                chemical_id=chemical.id,
                user_id=current_user.id,
                action='consumed',
                quantity_change=-quantity_used,
                quantity_before=old_quantity,
                quantity_after=new_quantity,
                details=purpose
            )
            log.data_hash = log.compute_hash()
            db.session.add(log)
            count += 1

        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Bulk consume commit error: {e}")
            return api_error("Багц хэрэглээ хадгалахад алдаа гарлаа", status_code=500)

        return api_success({
            "count": count,
            "errors": errors
        }, f"{count} chemicals consumed.")

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Bulk consume error: {e}")
        return api_error(str(e), status_code=500)
