# app/utils/datetime.py
"""
Огноо цагийн туслах функцууд.

Монголын цагийн бүстэй (Asia/Ulaanbaatar) ажиллана.
"""
from __future__ import annotations
from datetime import datetime
from zoneinfo import ZoneInfo

_DEFAULT_TZ = "Asia/Ulaanbaatar"


def now_local(tz_name: str = _DEFAULT_TZ) -> datetime:
    """Монголын цагаар одоогийн цагийг буцаах."""
    try:
        return datetime.now(ZoneInfo(tz_name))
    except (KeyError, ValueError):
        return datetime.now()

# --- add alias for legacy imports ---


def now_mn() -> datetime:
    """Legacy нэршил — models.py зэрэг хуучин код this-г дуудаж байсан."""
    return now_local()
