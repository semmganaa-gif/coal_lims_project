# app/services/spare_parts_service.py
# -*- coding: utf-8 -*-
"""Spare parts business logic — extracted from routes/spare_parts/crud.py and api.py."""

import logging
import os
import uuid
from datetime import date

from sqlalchemy import func, case
from flask_babel import lazy_gettext as _l

from app import db
from app.models import SparePart, SparePartUsage, SparePartLog, SparePartCategory
from app.repositories import (
    SparePartRepository,
    SparePartCategoryRepository,
    SparePartUsageRepository,
    SparePartLogRepository,
)
from app.utils.converters import to_float

logger = logging.getLogger(__name__)

# Зураг upload тохиргоо
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
UPLOAD_FOLDER = 'spare_parts'


# =====================================================
# IMAGE HELPERS
# =====================================================

def allowed_file(filename):
    """Файлын өргөтгөл зөвшөөрөгдсөн эсэх."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def save_image_to_disk(file_storage, app_root_path):
    """Save uploaded image, return relative path or None.

    Args:
        file_storage: werkzeug FileStorage object (already validated by caller).
        app_root_path: absolute path to app root (e.g. current_app.root_path).

    Returns:
        str | None: relative path like 'uploads/spare_parts/abc.jpg' or None.
    """
    if not file_storage or not file_storage.filename:
        return None
    if not allowed_file(file_storage.filename):
        return None

    ext = file_storage.filename.rsplit('.', 1)[1].lower()
    filename = f"{uuid.uuid4().hex}.{ext}"

    upload_path = os.path.join(app_root_path, 'static', 'uploads', UPLOAD_FOLDER)
    os.makedirs(upload_path, exist_ok=True)

    file_path = os.path.join(upload_path, filename)
    file_storage.save(file_path)

    return f"uploads/{UPLOAD_FOLDER}/{filename}"


def delete_image_from_disk(image_path, app_root_path):
    """Delete image file from disk.

    Args:
        image_path: relative path like 'uploads/spare_parts/abc.jpg'.
        app_root_path: absolute path to app root.
    """
    if image_path:
        full_path = os.path.join(app_root_path, 'static', image_path)
        if os.path.exists(full_path):
            os.remove(full_path)


# =====================================================
# AUDIT LOGGING
# =====================================================

def log_spare_part_action(spare_part, action, user_id,
                          quantity_change=None, quantity_before=None,
                          quantity_after=None, details=None):
    """Create an audit log entry with hash (ISO 17025).

    Args:
        spare_part: SparePart model instance.
        action: str action name ('created', 'updated', 'received', etc.).
        user_id: int user ID performing the action.
        quantity_change: optional float.
        quantity_before: optional float.
        quantity_after: optional float.
        details: optional str description.
    """
    log = SparePartLog(
        spare_part_id=spare_part.id,
        user_id=user_id,
        action=action,
        quantity_change=quantity_change,
        quantity_before=quantity_before,
        quantity_after=quantity_after,
        details=details,
    )
    log.data_hash = log.compute_hash()
    db.session.add(log)


# =====================================================
# CATEGORY QUERIES
# =====================================================

def get_categories():
    """Return active categories as list of (code, name) tuples."""
    cats = SparePartCategoryRepository.get_active(ordered=True)
    return [(c.code, c.name) for c in cats]


def get_categories_dict():
    """Return active categories as {code: name} dict."""
    cats = SparePartCategoryRepository.get_active(ordered=False)
    return {c.code: c.name for c in cats}


def get_all_categories_ordered():
    """Return all categories ordered (for admin list)."""
    return SparePartCategoryRepository.get_all_ordered()


# =====================================================
# CATEGORY CRUD
# =====================================================

def create_category(code, name, name_en=None, description=None,
                    sort_order=0, is_active=True, equipment_id=None):
    """Create a new spare part category.

    Returns:
        (SparePartCategory, None) on success, (None, error_message) on failure.
    """
    if not code or not name:
        return None, _l('Код болон нэр шаардлагатай.')

    if SparePartCategoryRepository.get_by_code(code):
        return None, f"'{code}' код аль хэдийн бүртгэгдсэн байна."

    cat = SparePartCategory(
        code=code,
        name=name,
        name_en=name_en or None,
        description=description or None,
        sort_order=sort_order,
        is_active=is_active,
        equipment_id=equipment_id,
    )
    db.session.add(cat)
    return cat, None


def update_category(category_id, name, name_en=None, description=None,
                    sort_order=0, is_active=True, equipment_id=None):
    """Update an existing category.

    Returns:
        (SparePartCategory, None) on success, (None, error_message) on failure.
    """
    cat = SparePartCategoryRepository.get_by_id(category_id)
    if not cat:
        return None, 'not_found'

    cat.name = name
    cat.name_en = name_en or None
    cat.description = description or None
    cat.sort_order = sort_order
    cat.is_active = is_active
    cat.equipment_id = equipment_id
    return cat, None


def delete_category(category_id):
    """Delete a category if no spare parts reference it.

    Returns:
        (name, None) on success, (None, error_message) on failure.
    """
    cat = SparePartCategoryRepository.get_by_id(category_id)
    if not cat:
        return None, 'not_found'

    count = SparePartRepository.count_by_category(cat.code)
    if count > 0:
        return None, f"'{cat.name}' ангилалд {count} сэлбэг бүртгэлтэй байна. Эхлээд тэдгээрийг шилжүүлнэ үү."

    name = cat.name
    db.session.delete(cat)
    return name, None


# =====================================================
# SPARE PART LIST / FILTER / SEARCH
# =====================================================

def get_spare_parts_filtered(category=None, status=None, view='all'):
    """Query spare parts with optional filters.

    Returns:
        list of dicts ready for JSON/template rendering.
    """
    spare_parts_rows = SparePartRepository.get_filtered(category, status, view)

    return [{
        'id': sp.id,
        'name': sp.name,
        'name_en': sp.name_en,
        'part_number': sp.part_number,
        'manufacturer': sp.manufacturer,
        'supplier': sp.supplier,
        'quantity': sp.quantity,
        'unit': sp.unit,
        'reorder_level': sp.reorder_level,
        'unit_price': sp.unit_price,
        'storage_location': sp.storage_location,
        'compatible_equipment': sp.compatible_equipment,
        'usage_life_months': sp.usage_life_months,
        'category': sp.category,
        'status': sp.status,
        'equipment_name': sp.equipment.name if sp.equipment else None,
    } for sp in spare_parts_rows]


def get_spare_parts_list_simple():
    """Return all spare parts as simple dicts (for API list endpoint)."""
    spare_parts = SparePartRepository.get_all_ordered()
    return [{
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


def get_low_stock_parts():
    """Return spare parts with low/out_of_stock status."""
    spare_parts = SparePartRepository.get_low_stock()

    return [{
        'id': sp.id,
        'name': sp.name,
        'quantity': sp.quantity,
        'unit': sp.unit,
        'reorder_level': sp.reorder_level,
        'status': sp.status,
    } for sp in spare_parts]


def search_spare_parts(query_str):
    """Search spare parts by name/name_en/part_number (autocomplete).

    Args:
        query_str: search string (minimum 2 chars).

    Returns:
        list of dicts.
    """
    spare_parts = SparePartRepository.search(query_str)

    return [{
        'id': sp.id,
        'name': sp.name,
        'name_en': sp.name_en,
        'part_number': sp.part_number,
        'quantity': sp.quantity,
        'unit': sp.unit,
        'status': sp.status,
    } for sp in spare_parts]


# =====================================================
# STATISTICS
# =====================================================

def get_list_stats():
    """Get spare part stats for list page (total, low_stock, out_of_stock)."""
    return SparePartRepository.get_list_stats()


def get_full_stats():
    """Get full statistics including total_value (for API stats endpoint)."""
    row = db.session.query(
        func.count(SparePart.id).label('total'),
        func.count(case((SparePart.status == 'active', SparePart.id))).label('active'),
        func.count(case((SparePart.status == 'low_stock', SparePart.id))).label('low_stock'),
        func.count(case((SparePart.status == 'out_of_stock', SparePart.id))).label('out_of_stock'),
        func.coalesce(func.sum(SparePart.quantity * SparePart.unit_price), 0).label('total_value'),
    ).one()

    return {
        'total': row.total,
        'active': row.active,
        'low_stock': row.low_stock,
        'out_of_stock': row.out_of_stock,
        'total_value': float(row.total_value),
    }


# =====================================================
# SPARE PART CREATE / UPDATE
# =====================================================

def _parse_int_safe(val):
    """Parse int from string, return None if empty/invalid."""
    if val and isinstance(val, str) and val.strip():
        return int(val)
    if isinstance(val, int):
        return val
    return None


def create_spare_part(data, user_id):
    """Create a new spare part.

    Args:
        data: dict with spare part fields (name, name_en, part_number, etc.).
        user_id: int creator user ID.

    Returns:
        (SparePart, None) on success, (None, error_message) on failure.
    """
    try:
        spare_part = SparePart(
            name=data.get('name'),
            name_en=data.get('name_en'),
            part_number=data.get('part_number'),
            description=data.get('description'),
            manufacturer=data.get('manufacturer'),
            supplier=data.get('supplier'),
            quantity=to_float(data.get('quantity')) or 0,
            unit=data.get('unit', 'pcs'),
            reorder_level=to_float(data.get('reorder_level')) or 1,
            unit_price=to_float(data.get('unit_price')),
            storage_location=data.get('storage_location'),
            compatible_equipment=data.get('compatible_equipment'),
            usage_life_months=_parse_int_safe(data.get('usage_life_months')),
            category=data.get('category', 'general'),
            created_by_id=user_id,
        )

        equipment_id = data.get('equipment_id')
        if equipment_id:
            spare_part.equipment_id = int(equipment_id)

        # image_path can be pre-set by caller after save_image_to_disk
        if data.get('image_path'):
            spare_part.image_path = data['image_path']

        spare_part.update_status()
        db.session.add(spare_part)
        db.session.flush()

        log_spare_part_action(
            spare_part, 'created',
            user_id=user_id,
            quantity_change=spare_part.quantity,
            quantity_before=0,
            quantity_after=spare_part.quantity,
            details=f"Шинээр үүсгэв: {spare_part.name}",
        )

        return spare_part, None

    except (ValueError, TypeError) as e:
        db.session.rollback()
        logger.error("Error creating spare part: %s", e)
        return None, str(e)[:100]


def update_spare_part(spare_part_id, data, user_id):
    """Update an existing spare part.

    Args:
        spare_part_id: int.
        data: dict with fields to update.
        user_id: int user ID performing the update.

    Returns:
        (SparePart, None) on success, (None, error_message) on failure.
    """
    spare_part = SparePartRepository.get_by_id(spare_part_id)
    if not spare_part:
        return None, 'not_found'

    try:
        old_quantity = spare_part.quantity

        spare_part.name = data.get('name')
        spare_part.name_en = data.get('name_en')
        spare_part.part_number = data.get('part_number')
        spare_part.description = data.get('description')
        spare_part.manufacturer = data.get('manufacturer')
        spare_part.supplier = data.get('supplier')
        spare_part.quantity = to_float(data.get('quantity')) or 0
        spare_part.unit = data.get('unit', 'pcs')
        spare_part.reorder_level = to_float(data.get('reorder_level')) or 1
        spare_part.unit_price = to_float(data.get('unit_price'))
        spare_part.storage_location = data.get('storage_location')
        spare_part.compatible_equipment = data.get('compatible_equipment')
        spare_part.usage_life_months = _parse_int_safe(data.get('usage_life_months'))
        spare_part.category = data.get('category', 'general')

        equipment_id = data.get('equipment_id')
        spare_part.equipment_id = int(equipment_id) if equipment_id else None

        # image_path managed by caller (save/delete handled in route)
        if 'image_path' in data:
            spare_part.image_path = data['image_path']

        spare_part.update_status()

        # Log quantity change if any
        if old_quantity != spare_part.quantity:
            log_spare_part_action(
                spare_part, 'adjusted',
                user_id=user_id,
                quantity_change=spare_part.quantity - old_quantity,
                quantity_before=old_quantity,
                quantity_after=spare_part.quantity,
                details=str(_l("Гараар тохируулав")),
            )

        # General update log
        log_spare_part_action(
            spare_part, 'updated',
            user_id=user_id,
            details=str(_l("Мэдээлэл шинэчлэв")),
        )

        return spare_part, None

    except (ValueError, TypeError) as e:
        db.session.rollback()
        logger.error("Error updating spare part: %s", e)
        return None, str(e)[:100]


# =====================================================
# STOCK MOVEMENTS
# =====================================================

def receive_stock(spare_part_id, quantity, user_id, notes=None):
    """Receive stock (increase quantity).

    Returns:
        (dict with result info, None) on success, (None, error_message) on failure.
    """
    spare_part = SparePartRepository.get_by_id(spare_part_id)
    if not spare_part:
        return None, 'not_found'

    if quantity <= 0:
        return None, _l('Тоо хэмжээ 0-ээс их байх ёстой.')

    old_quantity = spare_part.quantity
    spare_part.quantity += quantity
    spare_part.update_status()
    spare_part.received_date = date.today()

    log_spare_part_action(
        spare_part, 'received',
        user_id=user_id,
        quantity_change=quantity,
        quantity_before=old_quantity,
        quantity_after=spare_part.quantity,
        details=notes or _l('Шинээр ирсэн'),
    )

    return {
        'name': spare_part.name,
        'quantity_added': quantity,
        'unit': spare_part.unit,
        'new_total': spare_part.quantity,
    }, None


def consume_stock(spare_part_id, quantity, user_id,
                  equipment_id=None, maintenance_log_id=None,
                  purpose='', notes=None):
    """Consume stock (decrease quantity) and create usage record.

    Returns:
        (dict with result info, None) on success, (None, error_message) on failure.
    """
    spare_part = SparePartRepository.get_by_id(spare_part_id)
    if not spare_part:
        return None, 'not_found'

    if quantity <= 0:
        return None, _l('Тоо хэмжээ 0-ээс их байх ёстой.')

    if quantity > spare_part.quantity:
        return None, f'Нөөц хүрэлцэхгүй байна! Боломжит: {spare_part.quantity} {spare_part.unit}'

    old_quantity = spare_part.quantity
    spare_part.quantity -= quantity
    spare_part.update_status()
    spare_part.last_used_date = date.today()

    # Usage record
    usage = SparePartUsage(
        spare_part_id=spare_part.id,
        equipment_id=int(equipment_id) if equipment_id else None,
        maintenance_log_id=maintenance_log_id,
        quantity_used=quantity,
        unit=spare_part.unit,
        purpose=purpose,
        used_by_id=user_id,
        quantity_before=old_quantity,
        quantity_after=spare_part.quantity,
        notes=notes,
    )
    db.session.add(usage)

    log_spare_part_action(
        spare_part, 'consumed',
        user_id=user_id,
        quantity_change=-quantity,
        quantity_before=old_quantity,
        quantity_after=spare_part.quantity,
        details=f"Зарцуулав: {purpose or '-'}",
    )

    return {
        'spare_part_id': spare_part.id,
        'name': spare_part.name,
        'consumed': quantity,
        'unit': spare_part.unit,
        'remaining': spare_part.quantity,
        'status': spare_part.status,
    }, None


def consume_stock_bulk(items, user_id, equipment_id=None,
                       maintenance_log_id=None, purpose=_l('Засвар')):
    """Consume multiple spare parts in one transaction.

    Args:
        items: list of dicts with 'spare_part_id' and 'quantity'.
        user_id: int.
        equipment_id: optional int.
        maintenance_log_id: optional int.
        purpose: str.

    Returns:
        (results_list, errors_list) tuple.
    """
    results = []
    errors = []

    for item in items:
        spare_part_id = item.get('spare_part_id')
        quantity = float(item.get('quantity', 0))

        spare_part = SparePartRepository.get_by_id(spare_part_id)
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
            used_by_id=user_id,
            quantity_before=old_quantity,
            quantity_after=spare_part.quantity,
        )
        db.session.add(usage)

        log_spare_part_action(
            spare_part, 'consumed',
            user_id=user_id,
            quantity_change=-quantity,
            quantity_before=old_quantity,
            quantity_after=spare_part.quantity,
            details=f"Bulk: {purpose}",
        )

        results.append({
            'spare_part_id': spare_part.id,
            'name': spare_part.name,
            'consumed': quantity,
            'remaining': spare_part.quantity,
        })

    return results, errors


def dispose_spare_part(spare_part_id, user_id, reason=_l('Устгав')):
    """Mark spare part as disposed.

    Returns:
        (name, None) on success, (None, error_message) on failure.
    """
    spare_part = SparePartRepository.get_by_id(spare_part_id)
    if not spare_part:
        return None, 'not_found'

    old_quantity = spare_part.quantity
    spare_part.status = 'disposed'
    spare_part.quantity = 0

    log_spare_part_action(
        spare_part, 'disposed',
        user_id=user_id,
        quantity_change=-old_quantity,
        quantity_before=old_quantity,
        quantity_after=0,
        details=f"Устгав: {reason}",
    )

    return spare_part.name, None


def delete_spare_part_permanently(spare_part_id):
    """Permanently delete a spare part (admin only, caller checks permission).

    Returns:
        (name, None) on success, (None, error_message) on failure.
    """
    spare_part = SparePartRepository.get_by_id(spare_part_id)
    if not spare_part:
        return None, 'not_found'

    name = spare_part.name
    db.session.delete(spare_part)
    return name, None


# =====================================================
# USAGE / AUDIT HISTORY
# =====================================================

def get_detail_data(spare_part_id):
    """Get spare part detail with usage and audit history.

    Returns:
        (spare_part, usages, logs) or (None, None, None) if not found.
    """
    spare_part = SparePartRepository.get_by_id(spare_part_id)
    if not spare_part:
        return None, None, None

    usages = SparePartUsageRepository.get_for_spare(spare_part_id, limit=50)
    logs = SparePartLogRepository.get_for_spare(spare_part_id, limit=50)

    return spare_part, usages, logs


def get_usage_history(spare_part_id, limit=100):
    """Get usage history for a spare part as list of dicts.

    Returns:
        list of dicts.
    """
    usages = SparePartUsageRepository.get_for_spare(spare_part_id, limit=limit)

    return [{
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
