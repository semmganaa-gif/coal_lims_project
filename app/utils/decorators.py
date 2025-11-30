# app/utils/decorators.py
# -*- coding: utf-8 -*-
"""
Эрх шалгах декораторууд (Authorization decorators).

Давхардсан эрх шалгах кодыг арилгах зорилготой.
"""
from functools import wraps
from typing import List, Callable, Any
from flask import flash, redirect, url_for, abort
from flask_login import current_user


def role_required(*allowed_roles: str) -> Callable:
    """
    Эрх шалгах decorator. Тухайн route-д зөвхөн зөвшөөрөгдсөн эрхтэй
    хэрэглэгч нэвтрэх боломжтой.

    Args:
        *allowed_roles: Зөвшөөрөгдсөн эрхүүд (ж: 'admin', 'ahlah', 'himich')

    Returns:
        Decorated function

    Example:
        >>> @bp.route('/equipment/edit/<int:eq_id>')
        >>> @login_required
        >>> @role_required('admin', 'ahlah')
        >>> def edit_equipment(eq_id):
        >>>     ...

    Raises:
        403 Forbidden: Хэрэглэгчийн эрх хүрэлцэхгүй бол

    Notes:
        - Flask-Login @login_required дээр нэмж ашиглана
        - current_user.role шалгана
        - Эрх хүрэлцэхгүй бол 403 error буцаана
    """
    def decorator(f: Callable) -> Callable:
        @wraps(f)
        def decorated_function(*args: Any, **kwargs: Any) -> Any:
            if not current_user.is_authenticated:
                flash('Эхлээд нэвтэрнэ үү.', 'warning')
                return redirect(url_for('auth.login'))

            if current_user.role not in allowed_roles:
                flash(f'Танд энэ хуудсанд нэвтрэх эрх байхгүй. Шаардлагатай эрх: {", ".join(allowed_roles)}', 'danger')
                abort(403)

            return f(*args, **kwargs)
        return decorated_function
    return decorator


def admin_required(f: Callable) -> Callable:
    """
    Зөвхөн админ эрхтэй хэрэглэгчид зориулсан decorator.

    Args:
        f: Decorated function

    Returns:
        Decorated function

    Example:
        >>> @bp.route('/admin/users')
        >>> @login_required
        >>> @admin_required
        >>> def list_users():
        >>>     ...
    """
    @wraps(f)
    def decorated_function(*args: Any, **kwargs: Any) -> Any:
        if not current_user.is_authenticated:
            flash('Эхлээд нэвтэрнэ үү.', 'warning')
            return redirect(url_for('auth.login'))

        if current_user.role != 'admin':
            flash('Зөвхөн админ хандах боломжтой.', 'danger')
            abort(403)

        return f(*args, **kwargs)
    return decorated_function


def role_or_owner_required(*allowed_roles: str, owner_check: Callable[[Any], bool] = None) -> Callable:
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
        >>> @role_or_owner_required('admin', 'ahlah',
        ...     owner_check=lambda sample_id: Sample.query.get(sample_id).user_id == current_user.id)
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
                flash('Эхлээд нэвтэрнэ үү.', 'warning')
                return redirect(url_for('auth.login'))

            # Эрх шалгах
            if current_user.role in allowed_roles:
                return f(*args, **kwargs)

            # Эзэмшигч эсэхийг шалгах
            if owner_check and owner_check(*args, **kwargs):
                return f(*args, **kwargs)

            flash('Танд энэ үйлдэл хийх эрх байхгүй.', 'danger')
            abort(403)

        return decorated_function
    return decorator


def analysis_role_required(allowed_roles=None):
    """
    Шинжилгээний модульд хандах эрх шалгах декоратор.

    Analysis модулийн routes-уудад ашиглана. Default эрхүүд: himich, ahlah, admin, beltgegch

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
        >>> @analysis_role_required(['admin', 'ahlah'])
        >>> def analysis_admin():
        >>>     ...

    Notes:
        - app/routes/analysis/helpers.py-аас зөөгдсөн
        - Flask-Login нэвтрэх шалгалт бас хийнэ
    """
    if allowed_roles is None:
        allowed_roles = ["himich", "ahlah", "admin", "beltgegch"]

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
