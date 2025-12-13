# app/utils/quality_helpers.py
# -*- coding: utf-8 -*-
"""
Чанарын модуль туслагчид - Давхардсан кодыг нэгтгэсэн
ISO 17025 Чанарын удирдлагын систем
"""

from functools import wraps
from datetime import datetime
from app.utils.datetime import now_local
from flask import flash, redirect, url_for
from flask_login import current_user
import logging

logger = logging.getLogger(__name__)


def can_edit_quality():
    """
    Senior, Manager, Admin эрхтэй эсэхийг шалгах.

    Returns:
        bool: Засах эрхтэй эсэх
    """
    return current_user.is_authenticated and current_user.role in ['senior', 'manager', 'admin']


def require_quality_edit(redirect_endpoint='quality.index'):
    """
    Quality засварлах эрх шаардах decorator.

    Args:
        redirect_endpoint: Эрх байхгүй үед redirect хийх endpoint

    Usage:
        @require_quality_edit('quality.capa_list')
        def capa_new():
            ...
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not can_edit_quality():
                flash("Энэ үйлдэл зөвхөн ахлах/админ эрхтэй.", "danger")
                return redirect(url_for(redirect_endpoint))
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def calculate_status_stats(items, status_field='status', status_values=None):
    """
    Жагсаалтаас статус тоолол гаргах.

    Args:
        items: Model objects жагсаалт
        status_field: Status талбарын нэр (default: 'status')
        status_values: Тоолох status утгуудын жагсаалт (default: None - бүгдийг тоолно)

    Returns:
        dict: {'total': N, 'status1': N, 'status2': N, ...}

    Usage:
        stats = calculate_status_stats(capas, status_values=['open', 'in_progress', 'closed'])
        stats = calculate_status_stats(complaints, status_values=['received', 'investigating', 'resolved', 'closed'])
    """
    stats = {'total': len(items)}

    if status_values:
        for status in status_values:
            stats[status] = len([item for item in items if getattr(item, status_field, None) == status])
    else:
        # Өвөрмөц статусуудыг автоматаар олох
        unique_statuses = set(getattr(item, status_field, None) for item in items)
        for status in unique_statuses:
            if status:
                stats[status] = len([item for item in items if getattr(item, status_field, None) == status])

    return stats


def generate_sequential_code(model, code_field, prefix, year=None, padding=4):
    """
    Дараалсан код үүсгэх (CA-2025-0001, COMP-2025-0001 гэх мэт).

    Args:
        model: SQLAlchemy model class
        code_field: Код хадгалах column (string нэр)
        prefix: Кодын угтвар (CA, COMP, PT гэх мэт)
        year: Он (default: одоогийн он)
        padding: Дугаарын урт (default: 4 -> 0001)

    Returns:
        str: Шинэ код (CA-2025-0001)

    Usage:
        ca_number = generate_sequential_code(CorrectiveAction, 'ca_number', 'CA')
        complaint_no = generate_sequential_code(CustomerComplaint, 'complaint_no', 'COMP')
    """
    year = year or now_local().year

    # Баганы объект авах
    column = getattr(model, code_field)

    # Тухайн оны сүүлийн кодыг олох
    last_record = model.query.filter(
        column.like(f'{prefix}-{year}-%')
    ).order_by(column.desc()).first()

    if last_record:
        last_code = getattr(last_record, code_field)
        try:
            last_num = int(last_code.split('-')[-1])
            new_num = last_num + 1
        except (ValueError, IndexError):
            new_num = 1
    else:
        new_num = 1

    return f"{prefix}-{year}-{new_num:0{padding}d}"


def parse_date(date_str, default=None):
    """
    Date string-ийг date object болгох (алдаа гарвал default буцаана).

    Args:
        date_str: Огноо string (YYYY-MM-DD format)
        default: Алдаа гарсан үед буцаах утга

    Returns:
        date | None: Parsed date эсвэл default
    """
    if not date_str:
        return default
    try:
        return datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError:
        logger.warning(f"Invalid date format: {date_str}")
        return default


def parse_datetime(datetime_str, default=None):
    """
    Datetime string-ийг datetime object болгох.

    Args:
        datetime_str: Огноо цаг string (YYYY-MM-DD HH:MM:SS format)
        default: Алдаа гарсан үед буцаах утга

    Returns:
        datetime | None: Parsed datetime эсвэл default
    """
    if not datetime_str:
        return default

    formats = [
        '%Y-%m-%d %H:%M:%S',
        '%Y-%m-%d %H:%M',
        '%Y-%m-%dT%H:%M:%S',
        '%Y-%m-%dT%H:%M',
        '%Y-%m-%d'
    ]

    for fmt in formats:
        try:
            return datetime.strptime(datetime_str, fmt)
        except ValueError:
            continue

    logger.warning(f"Invalid datetime format: {datetime_str}")
    return default
