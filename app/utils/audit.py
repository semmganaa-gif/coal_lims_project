# app/utils/audit.py
# -*- coding: utf-8 -*-
"""
Аудитын логын утилити функцууд

Бүх чухал үйлдлүүдийг бүртгэнэ - ISO 17025 compliance
"""

from typing import Optional, Dict, Any
import json
import logging

from sqlalchemy.exc import SQLAlchemyError

from app.constants import DEFAULT_AUDIT_LOG_LIMIT


# File-based loggers (logging_config.py-аас instance/logs/audit.log болон
# security.log руу бичигдэнэ). Эдгээр нь зэрэгцээ DB AuditLog-той ажиллана.
_audit_file_logger = logging.getLogger('audit')
_security_file_logger = logging.getLogger('security')


# Security-relevant action keywords: эдгээр action-уудыг security.log-д бичнэ.
_SECURITY_ACTIONS = frozenset({
    'login_success', 'login_failed', 'logout',
    'tamper_blocked', 'tamper_detected', 'hardware_mismatch',
    'permission_denied', 'rate_limit_exceeded',
    'license_activated', 'license_expired', 'license_check_failed',
    'password_changed', 'password_reset',
    'admin_action', 'create_user', 'delete_user', 'edit_user',
})


def log_audit(
    action: str,
    resource_type: Optional[str] = None,
    resource_id: Optional[int] = None,
    details: Optional[Dict[str, Any]] = None,
    old_value: Optional[Dict[str, Any]] = None,
    new_value: Optional[Dict[str, Any]] = None,
    commit: bool = True,
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
        except (TypeError, ValueError):
            details_str = str(details)

    # Before/after values → JSON string
    old_value_str = None
    new_value_str = None
    if old_value:
        try:
            old_value_str = json.dumps(old_value, ensure_ascii=False)
        except (TypeError, ValueError):
            old_value_str = str(old_value)
    if new_value:
        try:
            new_value_str = json.dumps(new_value, ensure_ascii=False)
        except (TypeError, ValueError):
            new_value_str = str(new_value)

    # AuditLog бичлэг үүсгэх
    # timestamp-г гараар тохируулна — hash тооцоолоход шаардлагатай
    from app.utils.datetime import now_local as _now
    entry = AuditLog(
        timestamp=_now(),
        user_id=user_id,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        details=details_str,
        ip_address=ip_address,
        user_agent=user_agent,
        old_value=old_value_str,
        new_value=new_value_str,
    )

    # ISO 17025: Audit log integrity hash
    entry.data_hash = entry.compute_hash()

    db.session.add(entry)

    if commit:
        try:
            db.session.commit()
        except SQLAlchemyError as e:
            db.session.rollback()
            # ISO 17025: Audit failure нь silent байх ёсгүй. CRITICAL log + raise.
            _security_file_logger.critical(
                f"Failed to write audit log (action={action}, "
                f"resource={resource_type}#{resource_id}): {e}"
            )
            raise
    # commit=False: дуудагч тал commit хийнэ (transaction consistency)

    # File-based logger (parallel to DB AuditLog):
    # - Бүх action `audit.log`-д бичигдэнэ
    # - Security-relevant action `security.log`-д ч бас бичигдэнэ
    _write_file_log(action, resource_type, resource_id, user_id, ip_address, details_str)


def _write_file_log(action: str, resource_type: Optional[str],
                    resource_id: Optional[int], user_id: Optional[int],
                    ip_address: Optional[str], details_str: Optional[str]) -> None:
    """File-based audit/security loggers-д бичих (silent — алдаа throw хийхгүй).

    ISO 17025 retention хадгалалт + production grep-friendly text format.
    """
    try:
        # Single-line message format (grep + log-aggregation tool-д тохиромжтой)
        parts = [f"action={action}"]
        if user_id is not None:
            parts.append(f"user_id={user_id}")
        if resource_type:
            parts.append(f"resource={resource_type}#{resource_id}")
        if ip_address:
            parts.append(f"ip={ip_address}")
        if details_str:
            parts.append(f"details={details_str}")
        message = " ".join(parts)

        _audit_file_logger.info(message)
        if action in _SECURITY_ACTIONS:
            _security_file_logger.info(message)
    except Exception:
        # File logger failure нь main flow-ыг blocking хийхгүй
        pass


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
    from app import db
    from sqlalchemy import select

    stmt = select(AuditLog)
    if action:
        stmt = stmt.filter_by(action=action)
    stmt = stmt.order_by(AuditLog.timestamp.desc()).limit(limit)

    return db.session.execute(stmt).scalars().all()


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
    from app import db
    from sqlalchemy import select

    stmt = select(AuditLog).filter_by(user_id=user_id)\
        .order_by(AuditLog.timestamp.desc()).limit(limit)
    return db.session.execute(stmt).scalars().all()


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
    from app import db
    from sqlalchemy import select

    stmt = select(AuditLog).filter_by(
        resource_type=resource_type,
        resource_id=resource_id
    ).order_by(AuditLog.timestamp.desc()).limit(limit)
    return db.session.execute(stmt).scalars().all()
