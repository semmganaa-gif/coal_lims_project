# app/utils/audit.py
# -*- coding: utf-8 -*-
"""
Аудитын логын утилити функцууд

Бүх чухал үйлдлүүдийг бүртгэнэ - ISO 17025 compliance
"""

from typing import Optional, Dict, Any
import json

from app.constants import DEFAULT_AUDIT_LOG_LIMIT


def log_audit(
    action: str,
    resource_type: Optional[str] = None,
    resource_id: Optional[int] = None,
    details: Optional[Dict[str, Any]] = None
) -> None:
    """
    Аудитын лог бичих.

    Args:
        action: Үйлдлийн төрөл (login, logout, delete_sample, update_settings, гэх мэт)
        resource_type: Нөөцийн төрөл (Sample, User, Equipment, AnalysisResult, гэх мэт)
        resource_id: Нөөцийн ID
        details: Нэмэлт дэлгэрэнгүй мэдээлэл (JSON хэлбэрээр хадгална)

    Examples:
        >>> log_audit('login')
        >>> log_audit('delete_sample', resource_type='Sample', resource_id=123)
        >>> log_audit('approve_result', resource_type='AnalysisResult',
        ...           resource_id=456, details={'old_status': 'pending', 'new_status': 'approved'})

    Notes:
        - Request context шаардлагатай (Flask request объект)
        - User authenticated байх шаардлагагүй (анонимч үйлдэл ч бүртгэх боломжтой)
        - Database commit автоматаар хийгдэнэ
    """
    from app import db
    from app.models import AuditLog
    from flask import request
    from flask_login import current_user

    # Хэрэглэгчийн ID авах (нэвтрээгүй бол None)
    user_id = None
    if hasattr(current_user, 'id') and current_user.is_authenticated:
        user_id = current_user.id

    # Request-ийн мэдээлэл авах
    ip_address = request.remote_addr if request else None
    user_agent = None
    if request and request.headers:
        user_agent = request.headers.get('User-Agent', '')[:200]  # 200 тэмдэгтээр хязгаарлах

    # Details-г JSON string болгох
    details_str = None
    if details:
        try:
            details_str = json.dumps(details, ensure_ascii=False)
        except Exception:
            details_str = str(details)

    # AuditLog бичлэг үүсгэх
    entry = AuditLog(
        user_id=user_id,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        details=details_str,
        ip_address=ip_address,
        user_agent=user_agent
    )

    # ISO 17025: Audit log integrity hash
    entry.data_hash = entry.compute_hash()

    db.session.add(entry)

    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        # Audit log бичихэд алдаа гарсан ч үндсэн үйлдэл үргэлжлэх ёстой
        # Алдааг зөвхөн log-д бичнэ
        import logging
        logger = logging.getLogger('security')
        logger.error(f"Failed to write audit log: {e}")


def get_recent_audit_logs(limit: int = DEFAULT_AUDIT_LOG_LIMIT, action: Optional[str] = None) -> list:
    """
    Сүүлийн аудитын логуудыг авах.

    Args:
        limit: Хамгийн ихдээ хэдэн лог авах (default: 100)
        action: Тодорхой үйлдлийн логуудыг шүүх (бүгдийг авах бол None)

    Returns:
        list: AuditLog объектуудын жагсаалт (сүүлийн нь эхэнд)

    Examples:
        >>> logs = get_recent_audit_logs(limit=50)
        >>> login_logs = get_recent_audit_logs(action='login')
    """
    from app.models import AuditLog

    query = AuditLog.query

    if action:
        query = query.filter_by(action=action)

    return query.order_by(AuditLog.timestamp.desc()).limit(limit).all()


def get_user_audit_logs(user_id: int, limit: int = DEFAULT_AUDIT_LOG_LIMIT) -> list:
    """
    Тодорхой хэрэглэгчийн аудитын логуудыг авах.

    Args:
        user_id: Хэрэглэгчийн ID
        limit: Хамгийн ихдээ хэдэн лог авах (default: 100)

    Returns:
        list: AuditLog объектуудын жагсаалт (сүүлийн нь эхэнд)

    Examples:
        >>> user_logs = get_user_audit_logs(user_id=5, limit=20)
    """
    from app.models import AuditLog

    return AuditLog.query.filter_by(user_id=user_id)\
        .order_by(AuditLog.timestamp.desc())\
        .limit(limit)\
        .all()


def get_resource_audit_logs(
    resource_type: str,
    resource_id: int,
    limit: int = DEFAULT_AUDIT_LOG_LIMIT
) -> list:
    """
    Тодорхой нөөцийн (Sample, User, Equipment гэх мэт) аудитын логуудыг авах.

    Args:
        resource_type: Нөөцийн төрөл (Sample, User, Equipment, AnalysisResult)
        resource_id: Нөөцийн ID
        limit: Хамгийн ихдээ хэдэн лог авах (default: 100)

    Returns:
        list: AuditLog объектуудын жагсаалт (сүүлийн нь эхэнд)

    Examples:
        >>> sample_logs = get_resource_audit_logs('Sample', 123)
        >>> result_logs = get_resource_audit_logs('AnalysisResult', 456, limit=50)
    """
    from app.models import AuditLog

    return AuditLog.query.filter_by(
        resource_type=resource_type,
        resource_id=resource_id
    )\
        .order_by(AuditLog.timestamp.desc())\
        .limit(limit)\
        .all()
