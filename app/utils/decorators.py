# app/utils/decorators.py
# -*- coding: utf-8 -*-
"""
Эрх шалгах декораторууд (Authorization decorators).

Давхардсан эрх шалгах кодыг арилгах зорилготой.

Sync + async route хосыг хоёуланг дэмжих:
  Энэ файл доторх декораторууд route function-ыг wrap хийнэ. View функц нь
  `async def` (Flask 2+ + asgiref support) эсвэл sync `def` байж болно.
  `_dual_wrap(check_fn)` helper нь `asyncio.iscoroutinefunction`-аар f-г
  үзэж зөв wrapper-ыг буцаана. Энэ pattern байхгүй бол sync decorator нь
  `return f(...)` гэж coroutine object буцаагаад Flask `TypeError: ... view
  function returned a coroutine` шиднэ.
"""
import asyncio
from functools import wraps
from typing import Callable, Any, Optional
from flask import flash, redirect, url_for, abort
from flask_login import current_user

from app.constants import LabKey, UserRole


def _dual_wrap(check_fn: Callable[..., Any]) -> Callable[[Callable], Callable]:
    """Sync + async route function-ыг хоёуланг дэмжих декораторын factory.

    Args:
        check_fn(*args, **kwargs): нөхцөл шалгана. Хэрэв `None` буцаавал f
            ажиллана; өөр утга буцаавал (redirect/abort/response) шууд буцаана.
    """
    def decorate(f: Callable) -> Callable:
        if asyncio.iscoroutinefunction(f):
            @wraps(f)
            async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
                early = check_fn(*args, **kwargs)
                if early is not None:
                    return early
                return await f(*args, **kwargs)
            return async_wrapper

        @wraps(f)
        def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
            early = check_fn(*args, **kwargs)
            if early is not None:
                return early
            return f(*args, **kwargs)
        return sync_wrapper
    return decorate


def role_required(*allowed_roles: str) -> Callable:
    """Эрх шалгах decorator (sync + async route хоёуланг дэмжинэ).

    Example:
        >>> @bp.route('/equipment/edit/<int:eq_id>')
        >>> @login_required
        >>> @role_required('admin', 'senior')
        >>> def edit_equipment(eq_id):
        >>>     ...
    """
    def _check(*args: Any, **kwargs: Any) -> Any:
        if getattr(current_user, "role", None) not in allowed_roles:
            abort(403)
        return None
    return _dual_wrap(_check)


def admin_required(f: Callable) -> Callable:
    """Зөвхөн админ эрхтэй хэрэглэгчид зориулсан decorator (sync + async)."""
    def _check(*args: Any, **kwargs: Any) -> Any:
        if getattr(current_user, "role", None) != UserRole.ADMIN.value:
            abort(403)
        return None
    return _dual_wrap(_check)(f)


def senior_or_admin_required(f: Callable) -> Callable:
    """Senior эсвэл admin эрхтэй хэрэглэгчид (sync + async)."""
    def _check(*args: Any, **kwargs: Any) -> Any:
        if getattr(current_user, "role", None) not in (UserRole.SENIOR.value, UserRole.ADMIN.value):
            abort(403)
        return None
    return _dual_wrap(_check)(f)


def role_or_owner_required(*allowed_roles: str, owner_check: Optional[Callable[[Any], bool]] = None) -> Callable:
    """Эрх ЭСВЭЛ өөрийнх нь өгөгдөл засах эрх (sync + async).

    Args:
        *allowed_roles: Зөвшөөрөгдсөн эрхүүд
        owner_check: Хэрэглэгч өөрийнхөө өгөгдөл эсэхийг шалгах функц
    """
    def _check(*args: Any, **kwargs: Any) -> Any:
        if not current_user.is_authenticated:
            flash('Please log in first.', 'warning')
            return redirect(url_for('auth.login'))
        if current_user.role in allowed_roles:
            return None
        if owner_check and owner_check(*args, **kwargs):
            return None
        flash('You do not have permission for this action.', 'danger')
        abort(403)
    return _dual_wrap(_check)


def lab_required(lab_key: str) -> Callable:
    """Лабын эрх шалгах decorator (sync + async).

    Admin бүх лабд нэвтрэх боломжтой.

    Args:
        lab_key: Лабын түлхүүр ('coal', 'petrography', 'water', 'microbiology')
    """
    def _check(*args: Any, **kwargs: Any) -> Any:
        if not current_user.is_authenticated:
            flash('Please log in first.', 'warning')
            return redirect(url_for('auth.login'))
        if current_user.role == UserRole.ADMIN.value:
            return None
        user_labs = current_user.allowed_labs or [LabKey.COAL.value]
        if lab_key not in user_labs:
            flash('You do not have access to this laboratory.', 'danger')
            return redirect(url_for('main.lab_selector'))
        return None
    return _dual_wrap(_check)


def analysis_role_required(allowed_roles=None):
    """Шинжилгээний модульд хандах эрх шалгах decorator (sync + async).

    Default эрхүүд: chemist, senior, manager, admin, prep
    """
    if allowed_roles is None:
        allowed_roles = ["chemist", "senior", "manager", "admin", "prep"]

    def decorator(f: Callable) -> Callable:
        def _check(*args: Any, **kwargs: Any) -> Any:
            if not current_user.is_authenticated:
                return redirect(url_for("main.login", next=url_for(f.__name__)))
            if current_user.role not in allowed_roles:
                abort(403)
            return None
        return _dual_wrap(_check)(f)
    return decorator
