from __future__ import annotations

import json
from functools import lru_cache
from app.models import SystemSetting
from app.config.repeatability import LIMIT_RULES as FILE_LIMIT_RULES


@lru_cache(maxsize=1)
def load_limit_rules() -> dict:
    """
    Repeatability (T) дүрмийг DB-с уншина; олдохгүй бол файл дахь LIMIT_RULES-г буцаана.
    """
    try:
        setting = SystemSetting.query.filter_by(category="repeatability", key="limits").first()
        if setting and setting.value:
            return json.loads(setting.value)
    except Exception:
        # DB connection/context байхгүй бол шууд fallback
        pass
    return FILE_LIMIT_RULES


def clear_cache():
    load_limit_rules.cache_clear()
