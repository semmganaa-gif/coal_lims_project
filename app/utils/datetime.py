# app/utils/datetime.py
"""
Огноо цагийн туслах функцууд.

Монголын цагийн бүстэй (Asia/Ulaanbaatar = UTC+8 year-round, no DST) ажиллана.
"""
from __future__ import annotations
import logging
from datetime import datetime, timezone, timedelta
from zoneinfo import ZoneInfo

_DEFAULT_TZ = "Asia/Ulaanbaatar"

# UTC+8 fallback — Монгол улс DST хэрэглэдэггүй (2017 онд цуцалсан) тул жилийн
# турш UTC+8 тогтмол. tzdata байхгүй container/system-д энэ нь ZoneInfo-той ижил
# үр дүн өгнө.
_UTC8 = timezone(timedelta(hours=8))

_logger = logging.getLogger(__name__)
_tz_warned = False


def now_local(tz_name: str = _DEFAULT_TZ) -> datetime:
    """Монголын цагаар одоогийн цагийг буцаах.

    ZoneInfo (tzdata) байхгүй үед UTC+8 fallback (Mongolia DST хэрэглэдэггүй).
    Өмнөх version `datetime.now()` буцаадаг байсныг засаж — server TZ-аас
    хамаарал арилгасан (Theme G).
    """
    global _tz_warned
    try:
        return datetime.now(ZoneInfo(tz_name))
    except (KeyError, ValueError) as e:
        if not _tz_warned:
            _logger.critical(
                "ZoneInfo(%r) unavailable: %s. Using UTC+8 fallback. "
                "Install tzdata (pip install tzdata) on this system.",
                tz_name, e,
            )
            _tz_warned = True
        return datetime.now(_UTC8)


def now_mn() -> datetime:
    """Legacy нэршил — models.py зэрэг хуучин код this-г дуудаж байсан."""
    return now_local()
