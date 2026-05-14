# app/utils/decorators.py
# -*- coding: utf-8 -*-
"""
Эрх шалгах декораторууд (Authorization decorators).

Давхардсан эрх шалгах кодыг арилгах зорилготой.
"""
from functools import wraps
from typing import Callable, Any, Optional
from flask import flash, redirect, url_for, abort
from flask_login import current_user

from app.constants import LabKey, UserRole


def role_required(*allowed_roles: str) -> Callable:
    """
    Эрх шалгах decorator. Зөвхөн зөвшөөрөгдсөн role-той хэрэглэгчийг хүлээн авна.

    Args:
        *allowed_roles: Зөвшөөрөгдсөн эрхүүд (ж: 'admin', 'senior', 'chemist').

    Example:
        >>> @bp.route('/equipment/edit/<int:eq_id>')
        >>> @login_required
        >>> @role_required('admin', 'senior')
        >>> def edit_equipment(eq_id):
        >>>     ...

    Raises:
        403 Forbidden: role хангахгүй бол.

    Notes:
        - `@login_required`-тэй хамт ашиглах (нэвтрэх шалгалт энд хийгдэхгүй).
        - HTML + JSON API хоёуланд тогтвортой 403 буцаана (errors/403.html
          template HTML route-д render-дэнэ).
    """
    def decorator(f: Callable) -> Callable:
        @wraps(f)
        def decorated_function(*args: Any, **kwargs: Any) -> Any:
            if getattr(current_user, "role", None) not in allowed_roles:
                abort(403)
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def admin_required(f: Callable) -> Callable:
    """
    Зөвхөн админ эрхтэй хэрэглэгчид зориулсан decorator.

    Example:
        >>> @bp.route('/admin/users')
        >>> @login_required
        >>> @admin_required
        >>> def list_users():
        >>>     ...

    Notes:
        - `@login_required`-тэй хамт ашиглах.
        - Async route-уудтай хамт ажиллана (sync decorator + async fn pattern,
          Flask-Login `@login_required`-тэй ижил).
    """
    @wraps(f)
    def decorated_function(*args: Any, **kwargs: Any) -> Any:
        if getattr(current_user, "role", None) != UserRole.ADMIN.value:
            abort(403)
        return f(*args, **kwargs)
    return decorated_function


def senior_or_admin_required(f: Callable) -> Callable:
    """Senior эсвэл admin эрхтэй хэрэглэгчид зориулсан decorator."""
    @wraps(f)
    def decorated_function(*args: Any, **kwargs: Any) -> Any:
        if getattr(current_user, "role", None) not in (UserRole.SENIOR.value, UserRole.ADMIN.value):
            abort(403)
        return f(*args, **kwargs)
    return decorated_function


def role_or_owner_required(*allowed_roles: str, owner_check: Optional[Callable[[Any], bool]] = None) -> Callable:
    """
    Тусгай эрх ЭСВЭЛ өөрийнхөө өгөгдөл засах боломжтой болгох decorator.

    Args:
        *allowed_roles: Зөвшөөрөгдсөн эрхүүд
        owner_check: Хэрэглэгч өөрийнхөө өгөгдөл эсэхийг шалгах функц

    Returns:
        Decorated function

    Example:
        >>> @bp.route('/sample/edit/<int:sample_id>')
        >>> @login_required
        >>> @role_or_owner_required('admin', 'senior',
        ...     owner_check=lambda sample_id: db.session.get(Sample, sample_id).user_id == current_user.id)
        >>> def edit_sample(sample_id):
        >>>     ...

    Notes:
        - Эрхтэй хэрэглэгч ЭСВЭЛ өөрийнх нь бол OK
        - Аль нь ч биш бол 403
    """
    def decorator(f: Callable) -> Callable:
        @wraps(f)
        def decorated_function(*args: Any, **kwargs: Any) -> Any:
            if not current_user.is_authenticated:
                flash('Please log in first.', 'warning')
                return redirect(url_for('auth.login'))

            # Эрх шалгах
            if current_user.role in allowed_roles:
                return f(*args, **kwargs)

            # Эзэмшигч эсэхийг шалгах
            if owner_check and owner_check(*args, **kwargs):
                return f(*args, **kwargs)

            flash('You do not have permission for this action.', 'danger')
            abort(403)

        return decorated_function
    return decorator


def lab_required(lab_key: str) -> Callable:
    """
    Лабын эрх шалгах decorator.
    Хэрэглэгчийн allowed_labs жагсаалтад тухайн лаб байгаа эсэхийг шалгана.
    Admin бүх лабд нэвтрэх боломжтой.

    Args:
        lab_key: Лабын түлхүүр ('coal', 'petrography', 'water', 'microbiology')
    """
    def decorator(f: Callable) -> Callable:
        @wraps(f)
        def decorated_function(*args: Any, **kwargs: Any) -> Any:
            if not current_user.is_authenticated:
                flash('Please log in first.', 'warning')
                return redirect(url_for('auth.login'))

            # Admin бүх лабд нэвтрэх боломжтой
            if current_user.role == UserRole.ADMIN.value:
                return f(*args, **kwargs)

            user_labs = current_user.allowed_labs or [LabKey.COAL.value]
            if lab_key not in user_labs:
                flash(f'You do not have access to this laboratory.', 'danger')
                return redirect(url_for('main.lab_selector'))

            return f(*args, **kwargs)
        return decorated_function
    return decorator


def analysis_role_required(allowed_roles=None):
    """
    Шинжилгээний модульд хандах эрх шалгах декоратор.

    Analysis модулийн routes-уудад ашиглана. Default эрхүүд: chemist, senior, admin, prep

    Args:
        allowed_roles: Зөвшөөрөгдсөн эрхүүдын жагсаалт (опциональ)

    Returns:
        Decorated function

    Example:
        >>> @bp.route('/analysis/workspace')
        >>> @analysis_role_required()
        >>> def analysis_workspace():
        >>>     ...
        >>>
        >>> @bp.route('/analysis/admin')
        >>> @analysis_role_required(['admin', 'senior'])
        >>> def analysis_admin():
        >>>     ...

    Notes:
        - app/routes/analysis/helpers.py-аас зөөгдсөн
        - Flask-Login нэвтрэх шалгалт бас хийнэ
    """
    if allowed_roles is None:
        allowed_roles = ["chemist", "senior", "manager", "admin", "prep"]

    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                return redirect(url_for("main.login", next=url_for(f.__name__)))
            if current_user.role not in allowed_roles:
                abort(403)
            return f(*args, **kwargs)
        return decorated_function
    return decorator
