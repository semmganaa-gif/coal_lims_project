# app/routes/chemicals/api.py
# -*- coding: utf-8 -*-
"""Химийн бодисын API endpoints."""

from flask import request, jsonify, current_app
from flask_login import login_required, current_user
from sqlalchemy import select

from app import db, limiter
from app.repositories import ChemicalRepository
from app.routes.chemicals import chemicals_bp
from app.routes.api.helpers import api_success, api_error
from app.services.chemical_service import (
    get_chemical_api_list,
    get_low_stock_chemicals,
    get_expiring_chemicals,
    consume_chemical_stock,
    consume_bulk,
    search_chemicals,
    get_chemical_stats,
    get_usage_history,
)
from app.utils.database import safe_commit


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

    data = get_chemical_api_list(
        lab=lab, category=category, status=status,
        include_disposed=include_disposed
    )
    return jsonify(data)


# -------------------------------------------------
# 2. Бага нөөцтэй (Low Stock Alert)
# -------------------------------------------------

@chemicals_bp.route("/api/low_stock")
@login_required
def api_low_stock():
    """Бага нөөцтэй химийн бодисууд."""
    lab = request.args.get("lab", "all")
    return jsonify(get_low_stock_chemicals(lab=lab))


# -------------------------------------------------
# 3. Хугацаа дуусах (Expiring Soon)
# -------------------------------------------------

@chemicals_bp.route("/api/expiring")
@login_required
def api_expiring():
    """Хугацаа дуусах химийн бодисууд."""
    lab = request.args.get("lab", "all")
    try:
        days = int(request.args.get("days", 30))
    except (ValueError, TypeError):
        days = 30

    return jsonify(get_expiring_chemicals(lab=lab, days=days))


# -------------------------------------------------
# 3b. Notification summary (navbar bell)
# -------------------------------------------------

@chemicals_bp.route("/api/notifications")
@login_required
def api_notifications():
    """Navbar notification bell-д зориулсан нэгдсэн alert.

    Returns expiring-soon + expired chemicals (нийт тоо + жагсаалт).
    """
    from app.models import Chemical

    chemicals = list(db.session.execute(
        select(Chemical).where(
            Chemical.status.in_(['active', 'low_stock', 'expired']),
        )
    ).scalars().all())

    expired = []
    expiring = []
    for c in chemicals:
        days = c.days_until_expiry()
        if days is None:
            continue
        entry = {
            'id': c.id,
            'name': c.name,
            'lot_number': c.lot_number or '',
            'lab_type': c.lab_type,
            'days': days,
            'expiry_date': c.expiry_date.strftime('%Y-%m-%d') if c.expiry_date else None,
            'opened_expiry_date': c.opened_expiry_date.strftime('%Y-%m-%d') if c.opened_expiry_date else None,
            'ghs_signal_word': c.ghs_signal_word or '',
        }
        if days < 0:
            expired.append(entry)
        elif c.is_expiring_soon():
            expiring.append(entry)

    # Sort by urgency
    expired.sort(key=lambda x: x['days'])
    expiring.sort(key=lambda x: x['days'])

    return jsonify({
        'total': len(expired) + len(expiring),
        'expired_count': len(expired),
        'expiring_count': len(expiring),
        'expired': expired[:10],
        'expiring': expiring[:10],
    })


# -------------------------------------------------
# 4. Хэрэглээ бүртгэх API
# -------------------------------------------------

@chemicals_bp.route("/api/consume", methods=["POST"])
@login_required
@limiter.limit("30 per minute")
def api_consume():
    """Химийн бодисын хэрэглээ бүртгэх API."""
    try:
        data = request.get_json() or {}

        chemical_id = data.get("chemical_id")
        try:
            quantity_used = float(data.get("quantity_used", 0))
        except (ValueError, TypeError):
            return api_error("Invalid quantity")

        if not chemical_id or quantity_used <= 0:
            return api_error("Invalid data")

        chemical = ChemicalRepository.get_by_id(chemical_id)
        if not chemical:
            return api_error("Chemical not found", status_code=404)

        # Parse sample_id safely
        sample_id = None
        raw_sample_id = data.get("sample_id")
        if raw_sample_id is not None:
            try:
                sample_id = int(raw_sample_id)
            except (ValueError, TypeError):
                pass

        result = consume_chemical_stock(
            chemical=chemical,
            quantity_used=quantity_used,
            user_id=current_user.id,
            purpose=data.get("purpose", ""),
            analysis_code=data.get("analysis_code"),
            sample_id=sample_id,
        )

        if not result.success:
            return api_error(result.error)

        if not safe_commit(error_msg="API consume commit error", notify=False):
            return api_error("Хэрэглээ хадгалахад алдаа гарлаа", status_code=500)

        return api_success({
            "new_quantity": result.new_quantity,
            "chemical_status": result.chemical_status
        }, f"Consumed {quantity_used} {chemical.unit}")

    except (ValueError, TypeError) as e:
        db.session.rollback()
        current_app.logger.error(f"API consume error: {e}")
        return api_error("Chemical consumption failed", status_code=500)


# -------------------------------------------------
# 5. Хайлт / Autocomplete
# -------------------------------------------------

@chemicals_bp.route("/api/search")
@login_required
def api_search():
    """Химийн бодис хайх (autocomplete)."""
    q = request.args.get("q", "").strip()
    lab = request.args.get("lab", "all")
    try:
        limit = int(request.args.get("limit", 20))
    except (ValueError, TypeError):
        limit = 20

    return jsonify(search_chemicals(q=q, lab=lab, limit=limit))


# -------------------------------------------------
# 6. Статистик (Dashboard)
# -------------------------------------------------

@chemicals_bp.route("/api/stats")
@login_required
def api_stats():
    """Химийн бодисын статистик."""
    lab = request.args.get("lab", "all")
    return jsonify(get_chemical_stats(lab=lab))


# -------------------------------------------------
# 7. Хэрэглээний түүх API
# -------------------------------------------------

@chemicals_bp.route("/api/usage_history")
@login_required
def api_usage_history():
    """Химийн бодисын хэрэглээний түүх."""
    raw_chemical_id = request.args.get("chemical_id")
    lab = request.args.get("lab", "all")
    start_date = request.args.get("start_date")
    end_date = request.args.get("end_date")
    try:
        limit = int(request.args.get("limit", 100))
    except (ValueError, TypeError):
        limit = 100

    chemical_id = None
    if raw_chemical_id:
        try:
            chemical_id = int(raw_chemical_id)
        except (ValueError, TypeError):
            return jsonify({"items": [], "count": 0})

    try:
        data = get_usage_history(
            chemical_id=chemical_id, lab=lab,
            start_date=start_date, end_date=end_date, limit=limit
        )
    except ValueError:
        return api_error("Буруу огнооны формат. YYYY-MM-DD байх ёстой", status_code=400)

    return jsonify(data)


# -------------------------------------------------
# 8. Bulk Consume (Олон бодис нэг дор хэрэглэх)
# -------------------------------------------------

@chemicals_bp.route("/api/consume_bulk", methods=["POST"])
@login_required
@limiter.limit("10 per minute")
def api_consume_bulk():
    """Олон химийн бодис нэг дор хэрэглээ бүртгэх."""
    try:
        data = request.get_json() or {}
        items = data.get("items", [])
        purpose = data.get("purpose", "")
        analysis_code = data.get("analysis_code")

        # Parse sample_id safely
        sample_id = None
        raw_sample_id = data.get("sample_id")
        if raw_sample_id is not None:
            try:
                sample_id = int(raw_sample_id)
            except (ValueError, TypeError):
                pass

        result = consume_bulk(
            items=items,
            user_id=current_user.id,
            purpose=purpose,
            analysis_code=analysis_code,
            sample_id=sample_id,
        )

        if not result.success and result.error:
            return api_error(result.error)

        if not safe_commit(error_msg="Bulk consume commit error", notify=False):
            return api_error("Багц хэрэглээ хадгалахад алдаа гарлаа", status_code=500)

        return api_success({
            "count": result.count,
            "errors": result.errors
        }, f"{result.count} chemicals consumed.")

    except (ValueError, TypeError) as e:
        db.session.rollback()
        current_app.logger.error(f"Bulk consume error: {e}")
        return api_error("Bulk consumption failed", status_code=500)
