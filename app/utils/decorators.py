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
from flask import flash, redirect, request, url_for, jsonify
from flask_babel import gettext as _
from flask_login import current_user

from app.constants import LabKey, UserRole


def _role_denied_response():
    """Эрхгүй хэрэглэгчид буцаах хариу — UI/API context-ийг ялгана.

    Энэ helper нь `role_required` family decorator-ууд хооронд consistent
    зан төлөвийг хангана (өмнө `role_required`/`admin_required` нь `abort(403)`
    шууд хийдэг, `lab_required` нь flash + redirect хийдэг гэх мэт ялгаатай
    байсныг арилгана):

    - **API route** (path `/api/` эхэлсэн эсвэл `Accept: application/json`)
      → JSON 403 буцаана.
    - **UI route** → flash шиднэ + `request.referrer` эсвэл `main.index`-руу
      redirect.

    Returns Response (caller redirect эсвэл jsonify бэлэн утгыг буцаана).
    """
    is_api = request.path.startswith('/api/') or request.is_json or \
        request.accept_mimetypes.best == 'application/json'
    if is_api:
        return jsonify({"error": "Permission denied", "status": 403}), 403

    flash(_("You do not have permission for this action."), "danger")
    # Referrer-ийг тэргүүн сонголтоор ашиглах; үгүй бол safe `main.index` руу.
    # `main.index` бүртгэгдээгүй (жишээ нь нэг blueprint-ийн isolated test app)
    # үед `/`-руу зайлсхийнэ.
    if request.referrer:
        return redirect(request.referrer)
    try:
        return redirect(url_for('main.index'))
    except Exception:
        return redirect('/')


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

    Permission байхгүй үед `_role_denied_response()`-аар UI flash+redirect
    эсвэл API JSON 403 буцаана (`lab_required` pattern-тай consistent).

    Example:
        >>> @bp.route('/equipment/edit/<int:eq_id>')
        >>> @login_required
        >>> @role_required('admin', 'senior')
        >>> def edit_equipment(eq_id):
        >>>     ...
    """
    def _check(*args: Any, **kwargs: Any) -> Any:
        if getattr(current_user, "role", None) not in allowed_roles:
            return _role_denied_response()
        return None
    return _dual_wrap(_check)


def admin_required(f: Callable) -> Callable:
    """Зөвхөн админ эрхтэй хэрэглэгчид зориулсан decorator (sync + async)."""
    def _check(*args: Any, **kwargs: Any) -> Any:
        if getattr(current_user, "role", None) != UserRole.ADMIN.value:
            return _role_denied_response()
        return None
    return _dual_wrap(_check)(f)


def senior_or_admin_required(f: Callable) -> Callable:
    """Senior эсвэл admin эрхтэй хэрэглэгчид (sync + async)."""
    def _check(*args: Any, **kwargs: Any) -> Any:
        if getattr(current_user, "role", None) not in (UserRole.SENIOR.value, UserRole.ADMIN.value):
            return _role_denied_response()
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
        return _role_denied_response()
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

    Default: бүх authenticated role-ууд (UserRole enum-аас).
    """
    if allowed_roles is None:
        allowed_roles = UserRole.values()

    def decorator(f: Callable) -> Callable:
        def _check(*args: Any, **kwargs: Any) -> Any:
            if not current_user.is_authenticated:
                return redirect(url_for("main.login", next=url_for(f.__name__)))
            if current_user.role not in allowed_roles:
                return _role_denied_response()
            return None
        return _dual_wrap(_check)(f)
    return decorator
