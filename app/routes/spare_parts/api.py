# app/routes/spare_parts/api.py
"""Сэлбэг хэрэгслийн API routes."""

import logging

from flask import jsonify, request
from flask_login import login_required, current_user
from sqlalchemy.exc import SQLAlchemyError

from app import db, limiter
from app.routes.spare_parts import spare_parts_bp
from app.utils.database import safe_commit
from app.services.spare_parts_service import (
    get_spare_parts_list_simple,
    get_low_stock_parts,
    get_full_stats,
    consume_stock,
    consume_stock_bulk,
    search_spare_parts,
    get_usage_history,
)

logger = logging.getLogger(__name__)


@spare_parts_bp.route('/api/list')
@login_required
def api_spare_part_list():
    """Сэлбэг хэрэгслийн жагсаалт API."""
    return jsonify(get_spare_parts_list_simple())


@spare_parts_bp.route('/api/low_stock')
@login_required
def api_low_stock():
    """Нөөц бага сэлбэгүүд."""
    return jsonify(get_low_stock_parts())


@spare_parts_bp.route('/api/stats')
@login_required
def api_stats():
    """Статистик API."""
    return jsonify(get_full_stats())


@spare_parts_bp.route('/api/consume', methods=['POST'])
@login_required
@limiter.limit("30 per minute")
def api_consume():
    """Сэлбэг зарцуулах API - тоног төхөөрөмжийн засварт ашиглах."""
    data = request.get_json()

    spare_part_id = data.get('spare_part_id')
    try:
        quantity = float(data.get('quantity', 0))
    except (ValueError, TypeError):
        return jsonify({'success': False, 'message': 'Invalid quantity'}), 400

    if not spare_part_id or quantity <= 0:
        return jsonify({'success': False, 'message': 'spare_part_id and quantity are required'}), 400

    try:
        result, error = consume_stock(
            spare_part_id=spare_part_id,
            quantity=quantity,
            user_id=current_user.id,
            equipment_id=data.get('equipment_id'),
            maintenance_log_id=data.get('maintenance_log_id'),
            purpose=data.get('purpose', 'Засвар'),
        )

        if error == 'not_found':
            return jsonify({'success': False, 'message': 'Spare part not found'}), 404
        if error:
            return jsonify({'success': False, 'message': error}), 400

        if not safe_commit(error_msg="Spare part consume commit error", notify=False):
            return jsonify({'success': False, 'message': 'Сэлбэг зарцуулахад алдаа гарлаа'}), 500

        return jsonify({
            'success': True,
            'message': f"{result['consumed']} {result['unit']} consumed",
            'remaining': result['remaining'],
            'status': result['status'],
        })

    except (ValueError, TypeError, SQLAlchemyError) as e:
        db.session.rollback()
        logger.error("Spare part consume error: %s", e, exc_info=True)
        return jsonify({'success': False, 'message': 'Сэлбэг зарцуулахад алдаа гарлаа'}), 500


@spare_parts_bp.route('/api/consume_bulk', methods=['POST'])
@login_required
@limiter.limit("10 per minute")
def api_consume_bulk():
    """Олон сэлбэг нэг дор зарцуулах API."""
    data = request.get_json()
    items = data.get('items', [])

    if not items:
        return jsonify({'success': False, 'message': 'items are required'}), 400

    # A-H4: Bulk array size cap
    if len(items) > 100:
        return jsonify({'success': False, 'message': 'Нэг удаад 100-аас ихийг зарцуулах боломжгүй'}), 400

    try:
        results, errors = consume_stock_bulk(
            items=items,
            user_id=current_user.id,
            equipment_id=data.get('equipment_id'),
            maintenance_log_id=data.get('maintenance_log_id'),
            purpose=data.get('purpose', 'Засвар'),
        )

        if not safe_commit(error_msg="Spare part bulk consume commit error", notify=False):
            return jsonify({'success': False, 'message': 'Олноор зарцуулахад алдаа гарлаа'}), 500

        return jsonify({
            'success': True,
            'results': results,
            'errors': errors,
        })

    except (ValueError, TypeError, SQLAlchemyError) as e:
        db.session.rollback()
        logger.error("Spare part bulk consume error: %s", e, exc_info=True)
        return jsonify({'success': False, 'message': 'Олноор зарцуулахад алдаа гарлаа'}), 500


@spare_parts_bp.route('/api/search')
@login_required
def api_search():
    """Сэлбэг хайх (autocomplete)."""
    q = request.args.get('q', '').strip()
    return jsonify(search_spare_parts(q))


@spare_parts_bp.route('/api/usage_history/<int:id>')
@login_required
def api_usage_history(id):
    """Зарцуулалтын түүх API."""
    return jsonify(get_usage_history(id))
