# app/routes/spare_parts/api.py
"""Сэлбэг хэрэгслийн API routes."""

import logging
from datetime import date

logger = logging.getLogger(__name__)

from flask import jsonify, request
from flask_login import login_required, current_user
from sqlalchemy import func

from app import db
from app.models import SparePart, SparePartUsage, SparePartLog, Equipment
from app.routes.spare_parts import spare_parts_bp
from app.utils.security import escape_like_pattern


@spare_parts_bp.route('/api/list')
@login_required
def api_spare_part_list():
    """Сэлбэг хэрэгслийн жагсаалт API."""
    spare_parts = SparePart.query.order_by(SparePart.name).all()

    data = [{
        'id': sp.id,
        'name': sp.name,
        'name_en': sp.name_en,
        'part_number': sp.part_number,
        'quantity': sp.quantity,
        'unit': sp.unit,
        'reorder_level': sp.reorder_level,
        'status': sp.status,
        'category': sp.category,
        'storage_location': sp.storage_location,
        'equipment_name': sp.equipment.name if sp.equipment else None,
    } for sp in spare_parts]

    return jsonify(data)


@spare_parts_bp.route('/api/low_stock')
@login_required
def api_low_stock():
    """Нөөц бага сэлбэгүүд."""
    spare_parts = SparePart.query.filter(
        SparePart.status.in_(['low_stock', 'out_of_stock'])
    ).order_by(SparePart.quantity.asc()).all()

    data = [{
        'id': sp.id,
        'name': sp.name,
        'quantity': sp.quantity,
        'unit': sp.unit,
        'reorder_level': sp.reorder_level,
        'status': sp.status,
    } for sp in spare_parts]

    return jsonify(data)


@spare_parts_bp.route('/api/stats')
@login_required
def api_stats():
    """Статистик API."""
    stats = {
        'total': SparePart.query.count(),
        'active': SparePart.query.filter_by(status='active').count(),
        'low_stock': SparePart.query.filter_by(status='low_stock').count(),
        'out_of_stock': SparePart.query.filter_by(status='out_of_stock').count(),
        'total_value': db.session.query(
            func.sum(SparePart.quantity * SparePart.unit_price)
        ).scalar() or 0,
    }

    return jsonify(stats)


@spare_parts_bp.route('/api/consume', methods=['POST'])
@login_required
def api_consume():
    """Сэлбэг зарцуулах API - тоног төхөөрөмжийн засварт ашиглах."""
    data = request.get_json()

    spare_part_id = data.get('spare_part_id')
    quantity = float(data.get('quantity', 0))
    equipment_id = data.get('equipment_id')
    maintenance_log_id = data.get('maintenance_log_id')
    purpose = data.get('purpose', 'Засвар')

    if not spare_part_id or quantity <= 0:
        return jsonify({'success': False, 'message': 'spare_part_id and quantity are required'}), 400

    spare_part = SparePart.query.get(spare_part_id)
    if not spare_part:
        return jsonify({'success': False, 'message': 'Spare part not found'}), 404

    if quantity > spare_part.quantity:
        return jsonify({
            'success': False,
            'message': f'Insufficient stock! Available: {spare_part.quantity} {spare_part.unit}'
        }), 400

    try:
        old_quantity = spare_part.quantity
        spare_part.quantity -= quantity
        spare_part.update_status()
        spare_part.last_used_date = date.today()

        # Usage бүртгэл
        usage = SparePartUsage(
            spare_part_id=spare_part.id,
            equipment_id=equipment_id,
            maintenance_log_id=maintenance_log_id,
            quantity_used=quantity,
            unit=spare_part.unit,
            purpose=purpose,
            used_by_id=current_user.id,
            quantity_before=old_quantity,
            quantity_after=spare_part.quantity,
        )
        db.session.add(usage)

        # Аудит лог (with hash - ISO 17025)
        log = SparePartLog(
            spare_part_id=spare_part.id,
            action='consumed',
            quantity_change=-quantity,
            quantity_before=old_quantity,
            quantity_after=spare_part.quantity,
            user_id=current_user.id,
            details=f"API: {purpose}"
        )
        log.data_hash = log.compute_hash()
        db.session.add(log)
        db.session.commit()

        return jsonify({
            'success': True,
            'message': f'{quantity} {spare_part.unit} consumed',
            'remaining': spare_part.quantity,
            'status': spare_part.status,
        })

    except Exception as e:
        db.session.rollback()
        logger.error(f"Spare part consume error: {e}", exc_info=True)
        return jsonify({'success': False, 'message': 'Сэлбэг зарцуулахад алдаа гарлаа'}), 500


@spare_parts_bp.route('/api/consume_bulk', methods=['POST'])
@login_required
def api_consume_bulk():
    """Олон сэлбэг нэг дор зарцуулах API."""
    data = request.get_json()
    items = data.get('items', [])
    equipment_id = data.get('equipment_id')
    maintenance_log_id = data.get('maintenance_log_id')
    purpose = data.get('purpose', 'Засвар')

    if not items:
        return jsonify({'success': False, 'message': 'items are required'}), 400

    results = []
    errors = []

    try:
        for item in items:
            spare_part_id = item.get('spare_part_id')
            quantity = float(item.get('quantity', 0))

            spare_part = SparePart.query.get(spare_part_id)
            if not spare_part:
                errors.append(f'ID {spare_part_id} олдсонгүй')
                continue

            if quantity > spare_part.quantity:
                errors.append(f'{spare_part.name}: нөөц хүрэлцэхгүй ({spare_part.quantity})')
                continue

            old_quantity = spare_part.quantity
            spare_part.quantity -= quantity
            spare_part.update_status()
            spare_part.last_used_date = date.today()

            usage = SparePartUsage(
                spare_part_id=spare_part.id,
                equipment_id=equipment_id,
                maintenance_log_id=maintenance_log_id,
                quantity_used=quantity,
                unit=spare_part.unit,
                purpose=purpose,
                used_by_id=current_user.id,
                quantity_before=old_quantity,
                quantity_after=spare_part.quantity,
            )
            db.session.add(usage)

            log = SparePartLog(
                spare_part_id=spare_part.id,
                action='consumed',
                quantity_change=-quantity,
                quantity_before=old_quantity,
                quantity_after=spare_part.quantity,
                user_id=current_user.id,
                details=f"Bulk API: {purpose}"
            )
            log.data_hash = log.compute_hash()
            db.session.add(log)

            results.append({
                'spare_part_id': spare_part.id,
                'name': spare_part.name,
                'consumed': quantity,
                'remaining': spare_part.quantity,
            })

        db.session.commit()

        return jsonify({
            'success': True,
            'results': results,
            'errors': errors,
        })

    except Exception as e:
        db.session.rollback()
        logger.error(f"Spare part bulk consume error: {e}", exc_info=True)
        return jsonify({'success': False, 'message': 'Олноор зарцуулахад алдаа гарлаа'}), 500


@spare_parts_bp.route('/api/search')
@login_required
def api_search():
    """Сэлбэг хайх (autocomplete)."""
    q = request.args.get('q', '').strip()
    if len(q) < 2:
        return jsonify([])

    # ✅ SQL Injection хамгаалалт
    safe_q = escape_like_pattern(q)
    spare_parts = SparePart.query.filter(
        (SparePart.name.ilike(f'%{safe_q}%')) |
        (SparePart.name_en.ilike(f'%{safe_q}%')) |
        (SparePart.part_number.ilike(f'%{safe_q}%'))
    ).limit(20).all()

    data = [{
        'id': sp.id,
        'name': sp.name,
        'name_en': sp.name_en,
        'part_number': sp.part_number,
        'quantity': sp.quantity,
        'unit': sp.unit,
        'status': sp.status,
    } for sp in spare_parts]

    return jsonify(data)


@spare_parts_bp.route('/api/usage_history/<int:id>')
@login_required
def api_usage_history(id):
    """Зарцуулалтын түүх API."""
    usages = SparePartUsage.query.filter_by(spare_part_id=id)\
        .order_by(SparePartUsage.used_at.desc()).limit(100).all()

    data = [{
        'id': u.id,
        'quantity_used': u.quantity_used,
        'unit': u.unit,
        'purpose': u.purpose,
        'used_by': u.used_by.username if u.used_by else None,
        'used_at': u.used_at.strftime('%Y-%m-%d %H:%M') if u.used_at else None,
        'equipment_name': u.equipment.name if u.equipment else None,
        'quantity_before': u.quantity_before,
        'quantity_after': u.quantity_after,
    } for u in usages]

    return jsonify(data)
