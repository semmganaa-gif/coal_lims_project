"""
Repeatability (T) хязгаарын дүрмийг ачаалах модуль.

DB эсвэл файлаас repeatability дүрмийг уншина.
"""
from __future__ import annotations

import json
import logging
from functools import lru_cache

from sqlalchemy.exc import SQLAlchemyError

from app.config.repeatability import LIMIT_RULES as FILE_LIMIT_RULES

logger = logging.getLogger(__name__)


@lru_cache(maxsize=1)
def load_limit_rules() -> dict:
    """
    Repeatability (T) дүрмийг DB-с уншина; олдохгүй бол файл дахь LIMIT_RULES-г буцаана.
    """
    try:
        from app.models import SystemSetting
        from app import db
        from sqlalchemy import select

        setting = db.session.execute(
            select(SystemSetting).filter_by(category="repeatability", key="limits")
        ).scalars().first()
        if setting and setting.value:
            return json.loads(setting.value)
    except (json.JSONDecodeError, TypeError, OSError, SQLAlchemyError) as e:
        logger.debug(f"Repeatability rules DB fallback: {e}")
    return FILE_LIMIT_RULES


def clear_cache():
    """Кэшлэсэн repeatability дүрмийг цэвэрлэх."""
    load_limit_rules.cache_clear()
