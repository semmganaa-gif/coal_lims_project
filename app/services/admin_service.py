# app/services/admin_service.py
# -*- coding: utf-8 -*-
"""
Admin Service - Админ удирдлагын бизнес логик.

Routes-аас салгасан бизнес логикийг агуулна:
- Шинжилгээний төрөл sync
- Профайл auto-populate
- Хэрэглэгч CRUD
- Шинжилгээний тохиргоо хадгалах
- Control Standard / GBW Standard CRUD
"""

from __future__ import annotations

import json
import logging
from typing import Optional

import sqlalchemy as sa
from flask_babel import lazy_gettext as _l
from sqlalchemy.exc import SQLAlchemyError

from app import db
from app.constants import (
    SAMPLE_TYPE_CHOICES_MAP, CHPP_CONFIG_GROUPS,
    MASTER_ANALYSIS_TYPES_LIST, UserRole,
)
from app.models import (
    User, AnalysisType, AnalysisProfile,
    ControlStandard, GbwStandard,
)
from app.repositories import (
    AnalysisTypeRepository, GbwStandardRepository,
    ControlStandardRepository, SystemSettingRepository,
)
from app.schemas import UserSchema
from app.utils.audit import log_audit
from app.utils.transaction import transactional

logger = logging.getLogger(__name__)


def _admin_db_error(operation: str, exc: Exception,
                    template: str = "Алдаа: {msg}") -> tuple[bool, str]:
    """SQLAlchemyError-ыг tuple[bool, str] болгож log хийх."""
    logger.error("%s error: %s", operation, exc, exc_info=True)
    return False, template.format(msg=str(exc)[:100])


# ==============================================================================
# ШИНЖИЛГЭЭНИЙ ТӨРӨЛ / ПРОФАЙЛ
# ==============================================================================

@transactional()
def _seed_analysis_types_atomic() -> bool:
    """seed_analysis_types-ийн atomic core. True if changes made."""
    existing_analysis_types = {at.code: at for at in AnalysisTypeRepository.get_all()}
    changed_any = False

    for req in MASTER_ANALYSIS_TYPES_LIST:
        if req['code'] not in existing_analysis_types:
            new_at = AnalysisType(
                code=req['code'],
                name=req['name'],
                order_num=req['order'],
                required_role=req['role']
            )
            db.session.add(new_at)
            changed_any = True
        else:
            existing = existing_analysis_types[req['code']]
            changed = (
                existing.name != req['name']
                or existing.order_num != req['order']
                or existing.required_role != req['role']
            )
            if changed:
                existing.name = req['name']
                existing.order_num = req['order']
                existing.required_role = req['role']
                db.session.add(existing)
                changed_any = True

    return changed_any


def seed_analysis_types() -> bool:
    """
    Шинжилгээний төрлүүдийг автоматаар үүсгэх/шинэчлэх.

    Returns:
        True if changes were committed.
    """
    try:
        return _seed_analysis_types_atomic()
    except SQLAlchemyError as e:
        logger.error("Analysis type save error: %s", e, exc_info=True)
        return False


@transactional()
def _auto_populate_profiles_atomic() -> bool:
    """auto_populate_profiles-ийн atomic core. True if new profiles added."""
    added_new = False

    # Simple Profiles (CHPP-ээс бусад)
    for client, types in SAMPLE_TYPE_CHOICES_MAP.items():
        if client == 'CHPP':
            continue
        for s_type in types:
            exists = AnalysisProfile.query.filter(
                (AnalysisProfile.pattern.is_(None)) | (AnalysisProfile.pattern == ''),
                AnalysisProfile.client_name == client,
                AnalysisProfile.sample_type == s_type
            ).first()
            if not exists:
                db.session.add(AnalysisProfile(
                    client_name=client,
                    sample_type=s_type,
                    pattern=None,
                    analyses_json="[]"
                ))
                added_new = True

    # CHPP Pattern Profiles
    for hourly_type, config in CHPP_CONFIG_GROUPS.items():
        for sample in config['samples']:
            sample_name = sample['name']
            exists = AnalysisProfile.query.filter(
                AnalysisProfile.pattern == sample_name,
                AnalysisProfile.client_name == 'CHPP',
                AnalysisProfile.sample_type == hourly_type
            ).first()
            if not exists:
                db.session.add(AnalysisProfile(
                    client_name='CHPP',
                    sample_type=hourly_type,
                    pattern=sample_name,
                    analyses_json="[]",
                    priority=10
                ))
                added_new = True

    return added_new


def auto_populate_profiles() -> bool:
    """
    Simple болон CHPP профайлуудыг автоматаар үүсгэх.

    Returns:
        True if new profiles were added and committed.
    """
    try:
        return _auto_populate_profiles_atomic()
    except SQLAlchemyError as e:
        logger.error("Profile auto-populate error: %s", e, exc_info=True)
        return False


@transactional()
def _delete_pattern_profile_atomic(profile_id: int) -> tuple[bool, str]:
    """delete_pattern_profile-ийн atomic core."""
    profile = db.session.get(AnalysisProfile, profile_id)
    if profile is None:
        return False, 'not_found'
    if not profile.pattern:
        return False, _l('Анхдагч тохиргоог устгах боломжгүй.')
    db.session.delete(profile)
    return True, _l('Дүрэм устгагдлаа.')


def delete_pattern_profile(profile_id: int) -> tuple[bool, str]:
    """Pattern профайл устгах."""
    try:
        return _delete_pattern_profile_atomic(profile_id)
    except SQLAlchemyError as e:
        return _admin_db_error("delete_pattern_profile", e, "Устгах алдаа: {msg}")


def load_gi_shift_config() -> dict:
    """Gi ээлжийн тохиргоо DB-с унших, default утгатай."""
    gi_shift_config = {}
    gi_setting = SystemSettingRepository.get_gi_shift_config()
    if gi_setting and gi_setting.value:
        try:
            gi_shift_config = json.loads(gi_setting.value)
        except (json.JSONDecodeError, TypeError):
            pass

    if not gi_shift_config:
        gi_shift_config = {
            'PF211': ['D1', 'D3', 'D5', 'N1', 'N3', 'N5'],
            'PF221': ['D2', 'D4', 'D6', 'N2', 'N4', 'N6'],
            'PF231': ['D1', 'D3', 'D5', 'N1', 'N3', 'N5'],
        }

    return gi_shift_config


# ==============================================================================
# ХЭРЭГЛЭГЧИЙН УДИРДЛАГА
# ==============================================================================

def validate_and_create_user(
    username: str,
    password: str,
    role: str,
    full_name: Optional[str],
    email: Optional[str],
    phone: Optional[str],
    position: Optional[str],
    allowed_labs: Optional[list],
) -> tuple[bool, str, Optional[int]]:
    """
    Хэрэглэгч үүсгэх бизнес логик.

    Returns:
        (success, message, user_id or None)
    """
    # Schema validation
    _user_schema = UserSchema()
    schema_data = {
        'username': username,
        'password': password,
        'role': role,
        'full_name': full_name,
        'email': email,
        'phone': phone,
        'position': position,
        'allowed_labs': allowed_labs or ['coal'],
    }
    schema_errors = _user_schema.validate(schema_data)
    if schema_errors:
        error_messages = []
        for field_name, messages in schema_errors.items():
            for msg in (messages if isinstance(messages, list) else [messages]):
                error_messages.append(msg)
        return False, '\n'.join(error_messages), None

    # Check duplicate
    existing_user = db.session.scalar(
        sa.select(User).where(User.username == username)
    )
    if existing_user:
        return False, f'"{username}" хэрэглэгч аль хэдийн бүртгэгдсэн байна.', None

    # Admin constraint
    if role == UserRole.ADMIN.value:
        return False, _l('Шинэ админ хэрэглэгч үүсгэх боломжгүй.'), None

    # Create user
    user = User(username=username, role=role)
    user.allowed_labs = allowed_labs or ['coal']
    user.full_name = full_name
    user.email = email
    user.phone = phone
    user.position = position

    try:
        user.set_password(password)
    except ValueError:
        return False, _l('Нууц үг шаардлагыг хангахгүй байна (10+ тэмдэгт, том/жижиг үсэг, тоо).'), None

    @transactional()
    def _persist():
        db.session.add(user)

    try:
        _persist()
    except SQLAlchemyError as e:
        logger.error("validate_and_create_user error: %s", e, exc_info=True)
        return False, f'Хэрэглэгч үүсгэх алдаа: {str(e)[:100]}', None

    log_audit(
        action='create_user',
        resource_type='User',
        resource_id=user.id,
        details={
            'username': user.username,
            'role': user.role,
            'allowed_labs': user.allowed_labs
        }
    )
    return True, f'"{user.username}" хэрэглэгч амжилттай нэмэгдлээ.', user.id


def update_user(
    user_id: int,
    username: str,
    password: Optional[str],
    role: str,
    full_name: Optional[str],
    email: Optional[str],
    phone: Optional[str],
    position: Optional[str],
    allowed_labs: Optional[list],
) -> tuple[bool, str]:
    """
    Хэрэглэгчийн мэдээлэл шинэчлэх бизнес логик.

    Returns:
        (success, message)
    """
    user_to_edit = db.session.get(User, user_id)
    if user_to_edit is None:
        return False, 'not_found'

    original_username = user_to_edit.username

    # Capture old values for audit before/after
    _old_audit = {
        'username': user_to_edit.username,
        'role': user_to_edit.role,
        'allowed_labs': user_to_edit.allowed_labs,
        'full_name': user_to_edit.full_name,
        'email': user_to_edit.email,
    }

    # Duplicate check
    if original_username != username:
        existing_user = db.session.scalar(
            sa.select(User).where(User.username == username)
        )
        if existing_user:
            return False, f'"{username}" хэрэглэгч аль хэдийн бүртгэгдсэн байна.'

    user_to_edit.username = username

    # Admin role protection
    admin_role_warning = None
    if user_to_edit.role != UserRole.ADMIN.value:
        user_to_edit.role = role
    elif role != UserRole.ADMIN.value:
        admin_role_warning = _l('Админ хэрэглэгчийн эрхийн түвшинг өөрчлөх боломжгүй.')

    # Update fields
    user_to_edit.allowed_labs = allowed_labs or ['coal']
    user_to_edit.full_name = full_name
    user_to_edit.email = email
    user_to_edit.phone = phone
    user_to_edit.position = position

    # Password change
    if password:
        try:
            user_to_edit.set_password(password)
        except ValueError:
            return False, _l('Нууц үг шаардлагыг хангахгүй байна (10+ тэмдэгт, том/жижиг үсэг, тоо).')

    @transactional()
    def _persist():
        pass  # user_to_edit аль хэдийн session-д бэлэн — commit нь @transactional-аар явна

    try:
        _persist()
    except SQLAlchemyError as e:
        logger.error("update_user error: %s", e, exc_info=True)
        return False, f'Хэрэглэгч шинэчлэх алдаа: {str(e)[:100]}'

    log_audit(
        action='edit_user',
        resource_type='User',
        resource_id=user_to_edit.id,
        details={
            'username': user_to_edit.username,
            'role': user_to_edit.role,
            'allowed_labs': user_to_edit.allowed_labs,
            'password_changed': bool(password)
        },
        old_value=_old_audit,
        new_value={
            'username': user_to_edit.username,
            'role': user_to_edit.role,
            'allowed_labs': user_to_edit.allowed_labs,
            'full_name': user_to_edit.full_name,
            'email': user_to_edit.email,
        },
    )
    msg = f'"{user_to_edit.username}" хэрэглэгчийн мэдээлэл амжилттай шинэчлэгдлээ.'
    if admin_role_warning:
        msg = admin_role_warning + ' ' + msg
    return True, msg


def delete_user(user_id: int, current_user_id: int) -> tuple[bool, str]:
    """
    Хэрэглэгч устгах бизнес логик.

    Returns:
        (success, message)
    """
    if current_user_id == user_id:
        return False, _l("Админ хэрэглэгч өөрийгөө устгах боломжгүй.")

    user_to_delete = db.session.get(User, user_id)
    if user_to_delete is None:
        return False, 'not_found'

    if user_to_delete.role == UserRole.ADMIN.value:
        return False, _l("Админ хэрэглэгчийг устгах боломжгүй.")

    username = user_to_delete.username
    user_role = user_to_delete.role

    @transactional()
    def _persist():
        db.session.delete(user_to_delete)

    try:
        _persist()
    except SQLAlchemyError as e:
        logger.error("delete_user error: %s", e, exc_info=True)
        return False, f'Хэрэглэгч устгах алдаа: {str(e)[:100]}'

    log_audit(
        action='delete_user',
        resource_type='User',
        resource_id=user_id,
        details={'username': username, 'role': user_role}
    )
    return True, f'"{username}" хэрэглэгч амжилттай устгагдлаа.'


# ==============================================================================
# ШИНЖИЛГЭЭНИЙ ТОХИРГОО ХАДГАЛАХ
# ==============================================================================

def save_analysis_config(form_data: dict) -> tuple[bool, str]:
    """
    Шинжилгээний тохиргоо хадгалах (simple + CHPP profiles + Gi shift).

    Args:
        form_data: dict with keys matching request.form interface
                   (getlist method required for multi-value fields).

    Returns:
        (success, message)
    """
    # Simple profiles
    simple_profiles = AnalysisProfile.query.filter(
        (AnalysisProfile.pattern.is_(None)) | (AnalysisProfile.pattern == ''),
        AnalysisProfile.client_name != 'CHPP'
    ).all()

    # CHPP profiles
    chpp_profiles = AnalysisProfile.query.filter(
        AnalysisProfile.client_name == 'CHPP',
        AnalysisProfile.pattern.isnot(None),
        AnalysisProfile.pattern != ''
    ).all()

    updated_count = 0

    # Save simple profiles
    for profile in simple_profiles:
        input_name = f"simple-{profile.id}-analyses"
        selected_codes = form_data.getlist(input_name)
        profile.analyses_json = json.dumps(selected_codes)
        updated_count += 1

    # Save CHPP profiles
    for profile in chpp_profiles:
        input_name = f"chpp-{profile.id}-analyses"
        selected_codes = form_data.getlist(input_name)
        profile.analyses_json = json.dumps(selected_codes)
        updated_count += 1

    # Save Gi shift config
    gi_config = {}
    for pf_code in ['PF211', 'PF221', 'PF231']:
        shifts = form_data.getlist(f'gi_shifts_{pf_code}')
        if shifts:
            gi_config[pf_code] = shifts

    if gi_config:
        SystemSettingRepository.set_value('gi_shift', 'config', json.dumps(gi_config), commit=False)

    # Save SLA hours config
    from app.services.sla_service import SLA_CONFIG_CATEGORY
    from app.models import SystemSetting
    sla_count = 0
    for field_key in form_data:
        if field_key.startswith('sla_hours[') and field_key.endswith(']'):
            sla_key = field_key[10:-1]  # extract "CHPP:2 hourly" from "sla_hours[CHPP:2 hourly]"
            val = (form_data.get(field_key) or '').strip()
            existing = SystemSetting.query.filter_by(
                category=SLA_CONFIG_CATEGORY, key=sla_key
            ).first()
            if val:
                try:
                    hours = int(val)
                    if 1 <= hours <= 8760:
                        if existing:
                            existing.value = str(hours)
                        else:
                            db.session.add(SystemSetting(
                                category=SLA_CONFIG_CATEGORY, key=sla_key,
                                value=str(hours), is_active=True,
                            ))
                        sla_count += 1
                except (ValueError, TypeError):
                    pass
            elif existing:
                # Empty value = remove custom config (revert to default)
                db.session.delete(existing)
                sla_count += 1

    @transactional()
    def _persist():
        pass  # objects already in session

    try:
        _persist()
        return True, f'{updated_count} тохиргоо амжилттай хадгалагдлаа.'
    except SQLAlchemyError as e:
        logger.error("save_analysis_config error: %s", e, exc_info=True)
        return False, f'Тохиргоо хадгалах алдаа: {str(e)[:100]}'


# ==============================================================================
# CONTROL STANDARD CRUD
# ==============================================================================

@transactional()
def _create_standard_atomic(name: str, targets: dict) -> tuple[bool, str]:
    new_std = ControlStandard(name=name, targets=targets, is_active=False)
    db.session.add(new_std)
    return True, _l("Амжилттай үүсгэгдлээ")


def create_standard(name: str, targets: dict) -> tuple[bool, str]:
    """Шинэ хяналтын стандарт үүсгэх."""
    if not name or not targets:
        return False, _l("Нэр болон утгууд шаардлагатай")
    try:
        return _create_standard_atomic(name, targets)
    except SQLAlchemyError as e:
        return _admin_db_error("create_standard", e)


@transactional()
def _update_standard_atomic(std_id: int, name: str, targets: dict) -> tuple[bool, str]:
    std = ControlStandardRepository.get_by_id(std_id)
    if std is None:
        return False, 'not_found'
    std.name = name
    std.targets = targets
    return True, _l("Амжилттай шинэчлэгдлээ")


def update_standard(std_id: int, name: str, targets: dict) -> tuple[bool, str]:
    """Хяналтын стандарт засах."""
    if not name or not targets:
        return False, _l("Бүрэн бус өгөгдөл")
    try:
        return _update_standard_atomic(std_id, name, targets)
    except SQLAlchemyError as e:
        return _admin_db_error("update_standard", e)


@transactional()
def _delete_standard_atomic(std_id: int) -> tuple[bool, str]:
    std = ControlStandardRepository.get_by_id(std_id)
    if std is None:
        return False, 'not_found'
    if std.is_active:
        return False, _l("Идэвхтэй стандартыг устгах боломжгүй!")
    db.session.delete(std)
    return True, _l("Устгагдлаа")


def delete_standard(std_id: int) -> tuple[bool, str]:
    """Хяналтын стандарт устгах."""
    try:
        return _delete_standard_atomic(std_id)
    except SQLAlchemyError as e:
        return _admin_db_error("delete_standard", e)


@transactional()
def _activate_standard_atomic(std_id: int) -> tuple[bool, str]:
    std = ControlStandardRepository.get_by_id(std_id)
    if std is None:
        return False, 'not_found'
    ControlStandardRepository.deactivate_all(commit=False)
    std.is_active = True
    return True, _l("Идэвхжүүлэгдлээ")


def activate_standard(std_id: int) -> tuple[bool, str]:
    """Хяналтын стандарт идэвхжүүлэх."""
    try:
        return _activate_standard_atomic(std_id)
    except SQLAlchemyError as e:
        return _admin_db_error("activate_standard", e)


# ==============================================================================
# GBW STANDARD CRUD
# ==============================================================================

@transactional()
def _create_gbw_atomic(name: str, targets: dict) -> tuple[bool, str]:
    new_gbw = GbwStandard(name=name, targets=targets, is_active=False)
    db.session.add(new_gbw)
    return True, _l("GBW амжилттай бүртгэгдлээ")


def create_gbw(name: str, targets: dict) -> tuple[bool, str]:
    """Шинэ GBW стандарт үүсгэх."""
    if not name or not targets:
        return False, _l("GBW дугаар болон утгууд шаардлагатай")
    try:
        return _create_gbw_atomic(name, targets)
    except SQLAlchemyError as e:
        return _admin_db_error("create_gbw", e)


@transactional()
def _update_gbw_atomic(gbw_id: int, name: str, targets: dict) -> tuple[bool, str]:
    gbw = GbwStandardRepository.get_by_id(gbw_id)
    if gbw is None:
        return False, 'not_found'
    gbw.name = name
    gbw.targets = targets
    return True, _l("GBW мэдээлэл шинэчлэгдлээ")


def update_gbw(gbw_id: int, name: str, targets: dict) -> tuple[bool, str]:
    """GBW стандарт засах."""
    if not name or not targets:
        return False, _l("Бүрэн бус өгөгдөл")
    try:
        return _update_gbw_atomic(gbw_id, name, targets)
    except SQLAlchemyError as e:
        return _admin_db_error("update_gbw", e)


@transactional()
def _delete_gbw_atomic(gbw_id: int) -> tuple[bool, str]:
    gbw = GbwStandardRepository.get_by_id(gbw_id)
    if gbw is None:
        return False, 'not_found'
    if gbw.is_active:
        return False, _l("Ашиглагдаж буй GBW-ийг устгах боломжгүй!")
    db.session.delete(gbw)
    return True, _l("GBW устгагдлаа")


def delete_gbw(gbw_id: int) -> tuple[bool, str]:
    """GBW стандарт устгах."""
    try:
        return _delete_gbw_atomic(gbw_id)
    except SQLAlchemyError as e:
        return _admin_db_error("delete_gbw", e)


@transactional()
def _activate_gbw_atomic(gbw_id: int) -> tuple[bool, str]:
    gbw = GbwStandardRepository.get_by_id(gbw_id)
    if gbw is None:
        return False, 'not_found'
    GbwStandardRepository.deactivate_all(commit=False)
    gbw.is_active = True
    return True, _l("GBW идэвхжүүлэгдлээ")


def activate_gbw(gbw_id: int) -> tuple[bool, str]:
    """GBW стандарт идэвхжүүлэх."""
    try:
        return _activate_gbw_atomic(gbw_id)
    except SQLAlchemyError as e:
        return _admin_db_error("activate_gbw", e)


@transactional()
def _deactivate_gbw_atomic(gbw_id: int) -> tuple[bool, str]:
    gbw = GbwStandardRepository.get_by_id(gbw_id)
    if gbw is None:
        return False, 'not_found'
    gbw.is_active = False
    return True, _l("Амжилттай идэвхгүй болгогдлоо")


def deactivate_gbw(gbw_id: int) -> tuple[bool, str]:
    """GBW стандарт идэвхгүй болгох."""
    try:
        return _deactivate_gbw_atomic(gbw_id)
    except SQLAlchemyError as e:
        return _admin_db_error("deactivate_gbw", e)
