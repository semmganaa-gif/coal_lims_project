# app/utils/settings.py
# -*- coding: utf-8 -*-
"""
Системийн тохиргоог DB-ээс унших helper функцүүд
"""

from app import db
from app.models import SystemSetting
from sqlalchemy import select
import json


def get_error_reason_labels():
    """
    ERROR_REASON_LABELS-ийг DB-ээс унших

    Returns:
        dict: {key: value} жишээ: {'sample_prep': '1. Дээж бэлтгэлийн алдаа', ...}
    """
    settings = db.session.execute(
        select(SystemSetting).filter_by(category='error_reason', is_active=True)
        .order_by(SystemSetting.sort_order)
    ).scalars().all()

    return {s.key: s.value for s in settings}


def get_setting_by_category(category):
    """
    Тодорхой category-ийн бүх тохиргоог унших

    Args:
        category (str): Категори нэр (error_reason, sample_type, гэх мэт)

    Returns:
        dict: {key: value}
    """
    settings = db.session.execute(
        select(SystemSetting).filter_by(category=category, is_active=True)
        .order_by(SystemSetting.sort_order)
    ).scalars().all()

    return {s.key: s.value for s in settings}


def get_setting_value(category, key, default=None):
    """
    Нэг тохиргооны утгыг унших

    Args:
        category (str): Категори
        key (str): Түлхүүр
        default: Default утга (олдохгүй бол)

    Returns:
        str: Тохиргооны утга эсвэл default
    """
    setting = db.session.execute(
        select(SystemSetting).filter_by(category=category, key=key, is_active=True)
    ).scalars().first()

    return setting.value if setting and setting.value is not None else default


def update_setting(category, key, value, updated_by_id=None):
    """
    Тохиргоог шинэчлэх эсвэл үүсгэх

    Args:
        category (str): Категори
        key (str): Түлхүүр
        value (str): Шинэ утга
        updated_by_id (int, optional): Засварласан хэрэглэгчийн ID

    Returns:
        SystemSetting: Шинэчлэгдсэн эсвэл шинээр үүссэн setting
    """
    setting = db.session.execute(
        select(SystemSetting).filter_by(category=category, key=key)
    ).scalars().first()

    if setting:
        setting.value = value
        setting.updated_by_id = updated_by_id
    else:
        setting = SystemSetting(
            category=category,
            key=key,
            value=value,
            updated_by_id=updated_by_id
        )
        db.session.add(setting)

    db.session.commit()
    return setting


def get_sample_type_choices_map():
    """
    SAMPLE_TYPE_CHOICES_MAP-ийг DB-ээс унших.
    DB хоосон бол constants.py-ээс fallback авна.
    """
    settings = db.session.execute(
        select(SystemSetting).filter_by(category='sample_type', is_active=True)
    ).scalars().all()
    if settings:
        return {s.key: json.loads(s.value) for s in settings}
    # Fallback: constants.py
    from app.constants import SAMPLE_TYPE_CHOICES_MAP
    return SAMPLE_TYPE_CHOICES_MAP


def get_unit_abbreviations():
    """
    UNIT_ABBREVIATIONS-ийг DB-ээс унших.
    DB хоосон бол constants.py-ээс fallback авна.
    """
    settings = db.session.execute(
        select(SystemSetting).filter_by(category='unit_abbr', is_active=True)
    ).scalars().all()
    if settings:
        return {s.key: s.value for s in settings}
    # Fallback: constants.py
    from app.constants import UNIT_ABBREVIATIONS
    return UNIT_ABBREVIATIONS
