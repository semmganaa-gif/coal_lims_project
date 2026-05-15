# app/repositories/system_setting_repository.py
# -*- coding: utf-8 -*-
"""SystemSetting Repository — системийн тохиргооны database operations.

SQLAlchemy 2.0 native API (`select()` builder) ашиглана.
"""

from __future__ import annotations
from typing import Optional, Any
import json

from sqlalchemy import select

from app import db
from app.models import SystemSetting


def _get_one(category: str, key: str) -> Optional[SystemSetting]:
    """Category + key-ийн тохиргоог авах helper."""
    stmt = select(SystemSetting).where(
        SystemSetting.category == category,
        SystemSetting.key == key,
    )
    return db.session.execute(stmt).scalar_one_or_none()


class SystemSettingRepository:
    """SystemSetting model-ийн database operations."""

    @staticmethod
    def get(category: str, key: str) -> Optional[SystemSetting]:
        """Category + key-ээр тохиргоо авах."""
        return _get_one(category, key)

    @staticmethod
    def get_value(category: str, key: str, default: Any = None) -> Any:
        """Category + key-ээр value шууд авах."""
        setting = _get_one(category, key)
        if setting is None:
            return default
        return setting.value

    @staticmethod
    def get_json(category: str, key: str, default: Any = None) -> Any:
        """Category + key-ээр JSON value parse хийж авах."""
        setting = _get_one(category, key)
        if setting is None or not setting.value:
            return default
        try:
            return json.loads(setting.value)
        except (json.JSONDecodeError, TypeError):
            return default

    @staticmethod
    def set_value(category: str, key: str, value: str, commit: bool = False) -> SystemSetting:
        """Category + key-ээр value хадгалах (upsert)."""
        setting = _get_one(category, key)
        if setting:
            setting.value = value
        else:
            setting = SystemSetting(category=category, key=key, value=value)
            db.session.add(setting)
        if commit:
            db.session.commit()
        return setting

    @staticmethod
    def get_all_by_category(category: str) -> list[SystemSetting]:
        stmt = select(SystemSetting).where(SystemSetting.category == category)
        return list(db.session.execute(stmt).scalars().all())

    @staticmethod
    def get_email_recipients() -> tuple[str, str]:
        """Имэйл хүлээн авагчдыг авах (to, cc)."""
        to_setting = _get_one('email', 'report_recipients_to')
        cc_setting = _get_one('email', 'report_recipients_cc')
        return (
            to_setting.value if to_setting else '',
            cc_setting.value if cc_setting else '',
        )

    @staticmethod
    def get_gi_shift_config() -> Optional[SystemSetting]:
        return _get_one('gi_shift', 'config')

    @staticmethod
    def get_repeatability_limits() -> Optional[SystemSetting]:
        return _get_one('repeatability', 'limits')

    @staticmethod
    def delete(setting: SystemSetting, commit: bool = False) -> bool:
        db.session.delete(setting)
        if commit:
            db.session.commit()
        return True
