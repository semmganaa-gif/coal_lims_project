# app/utils/shifts.py
# -*- coding: utf-8 -*-

"""
Ээлжийн (shift) тооцооллын util.

Гол зорилго:
  - Ямар нэг datetime (локал цагтай) → аль ээлж (A/B/C) + өдөр / шөнийн ээлж вэ?
  - KPI, тайлан, шүүлт хийхэд: "энэ үйлдэл ямар ээлжийн хариуцлага вэ?" гэдгийг тогтоох.

⚙ Цагийн зааг:
  - ӨДӨР: 07:01–19:00
  - ШӨНӨ: 19:01–07:00 (дараагийн өглөө хүртэл)

⚙ Цикл (21 хоног):
  - А баг: 7 хоног ӨДӨР -> 7 хоног ШӨНӨ -> 7 хоног АМРАЛТ
  - Эхлэх цэг: 2025-11-22 (А баг Өдөр эхэлсэн)
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, time, timedelta
from typing import Optional
from app.utils.datetime import now_local


# 🧭 Циклийн эхлэх өдөр (калибровк)
# 2025-11-22-оос эхлэн A баг ӨДӨР ээлжинд гарч байна гэж тохируулав.
CYCLE_START_DATE = date(2025, 11, 22)

DAY_START = time(7, 1)   # 07:01
DAY_END   = time(19, 0)  # 19:00
# Night shift нь үүнээс бусад бүх цаг (19:01–07:00)


@dataclass
class ShiftInfo:
    """Ээлжийн тухай нэгдсэн мэдээлэл."""
    team: str            # "A" / "B" / "C"
    shift_type: str      # "day" / "night"
    anchor_date: date    # аль "хоног"-т тооцогдоод байгаа вэ (өдрийн index-аар)
    cycle_day_index: int # 0..20 (CYCLE_START_DATE-ээс хойшхи 21-ээс модулярласан)
    segment_index: int   # 0,1,2 (0..6, 7..13, 14..20 гэсэн 7 хоногийн блокууд)
    shift_start: datetime
    shift_end: datetime

    @property
    def label(self) -> str:
        """Жишээ: 'A-Өдөр', 'B-Шөнө'."""
        mn = "Өдөр" if self.shift_type == "day" else "Шөнө"
        return f"{self.team}-{mn}"


def _get_shift_type_and_anchor_date(dt: datetime) -> tuple[str, date]:
    """
    Огноо/цаг → (shift_type, anchor_date)

      - Хэрэв 07:01–19:00 хооронд → 'day', anchor_date = тухайн өдөр
      - Үгүй бол → 'night'
           * 19:01–23:59 → anchor_date = тухайн өдөр
           * 00:00–07:00 → anchor_date = өмнөх өдөр
    """
    if dt.tzinfo is not None:
        # Локал гэж үзэж байгаа тул tz-aware байвал шууд local цагийг нь авна.
        local_time = dt.timetz().replace(tzinfo=None)
    else:
        local_time = dt.time()

    if DAY_START <= local_time <= DAY_END:
        # Өдрийн ээлж
        return "day", dt.date()

    # Шөнийн ээлж
    if local_time >= time(19, 1):
        # 19:01–23:59 → тухайн өдрийн night shift
        anchor = dt.date()
    else:
        # 00:00–07:00 → өмнөх өдрийн night shift
        anchor = (dt - timedelta(days=1)).date()

    return "night", anchor


def _get_cycle_day_index(anchor_date: date) -> int:
    """CYCLE_START_DATE-ээс эхлэн хэд дэх өдөр вэ (0..∞), түүний 21 доторх үлдэгдэл."""
    delta = anchor_date - CYCLE_START_DATE
    return delta.days % 21


def _get_team_for_segment(segment_index: int, shift_type: str) -> str:
    """
    segment_index = 0,1,2 (0..6, 7..13, 14..20)
    
    Хуваарилалт (2025-11-22-оос эхлэн A баг өдрөөр эхэлсэн):

      Segment 0 (0..6):
        - Day   : A  (Таны баг)
        - Night : B  (B шөнөөр)
        - Off   : C

      Segment 1 (7..13):
        - Day   : C  (C амарч дуусаад өдөр гарна)
        - Night : A  (Таны баг шөнө рүү шилжинэ)
        - Off   : B

      Segment 2 (14..20):
        - Day   : B  (B амарч дуусаад өдөр гарна)
        - Night : C
        - Off   : A  (Таны баг амарна)
    """

    if segment_index == 0:
        day_team, night_team = "A", "B"
    elif segment_index == 1:
        day_team, night_team = "C", "A"
    else:
        day_team, night_team = "B", "C"

    return day_team if shift_type == "day" else night_team


def _compute_shift_start_end(anchor_date: date, shift_type: str) -> tuple[datetime, datetime]:
    """
    anchor_date, shift_type → тухайн ээлжийн яг эхлэх/дуусах datetime.
      - Өдөр: 07:01–19:00, anchor_date дээр
      - Шөнө: 19:01–07:00, anchor_date оройноос дараагийн өглөө хүртэл
    """
    if shift_type == "day":
        start = datetime.combine(anchor_date, DAY_START)
        end   = datetime.combine(anchor_date, DAY_END)
    else:
        start = datetime.combine(anchor_date, time(19, 1))
        end   = datetime.combine(anchor_date + timedelta(days=1), time(7, 0))
    return start, end


def get_shift_info(dt: datetime) -> ShiftInfo:
    """
    ГАДНААС ХАМГИЙН ИХ АШИГЛАХ ФУНКЦ.

    Жишээ:
      info = get_shift_info(some_datetime)
      info.team       → "A" / "B" / "C"
      info.shift_type → "day" / "night"
      info.anchor_date→ энэ ээлж аль өдөрт хамаарч бүртгэгдэж байгаа вэ
      info.label      → "A-Өдөр", "C-Шөнө" гэх мэт

    Дараа нь KPI тайлан дээр:
      - info.team, info.shift_type-аар group-by хийх
      - info.anchor_date-аар огнооны бүлэг гаргах г.м.
    """
    shift_type, anchor_date = _get_shift_type_and_anchor_date(dt)
    cycle_day_index = _get_cycle_day_index(anchor_date)
    segment_index = cycle_day_index // 7  # 0,1,2
    team = _get_team_for_segment(segment_index, shift_type)
    shift_start, shift_end = _compute_shift_start_end(anchor_date, shift_type)

    return ShiftInfo(
        team=team,
        shift_type=shift_type,
        anchor_date=anchor_date,
        cycle_day_index=cycle_day_index,
        segment_index=segment_index,
        shift_start=shift_start,
        shift_end=shift_end,
    )


# =====================================================================
# LEGACY ФУНКЦҮҮД (Backward Compatibility)
# Өмнө app/routes/main/helpers.py болон app/utils/shift_helper.py-д байсан
# =====================================================================

def get_12h_shift_code(dt):
    """
    12 цагийн ээлжийн код буцаах (_D эсвэл _N).

    Args:
        dt: datetime объект

    Returns:
        str: "_D" (өдрийн ээлж 7:00-19:00) эсвэл "_N" (шөнийн ээлж)

    Examples:
        >>> from datetime import datetime
        >>> get_12h_shift_code(datetime(2025, 1, 1, 8, 0))
        '_D'
        >>> get_12h_shift_code(datetime(2025, 1, 1, 20, 0))
        '_N'
    """
    hour = dt.hour
    return "_D" if 7 <= hour < 19 else "_N"


def get_quarter_code(dt):
    """
    Улирлын код буцаах (_Q1, _Q2, _Q3, _Q4).

    Args:
        dt: datetime объект

    Returns:
        str: "_Q1" (1-3 сар), "_Q2" (4-6), "_Q3" (7-9), "_Q4" (10-12)

    Examples:
        >>> from datetime import datetime
        >>> get_quarter_code(datetime(2025, 1, 15))
        '_Q1'
        >>> get_quarter_code(datetime(2025, 7, 1))
        '_Q3'
    """
    month = dt.month
    if month <= 3:
        return "_Q1"
    elif month <= 6:
        return "_Q2"
    elif month <= 9:
        return "_Q3"
    else:
        return "_Q4"


def get_shift_date(dt: Optional[datetime] = None) -> date:
    """
    Ээлжийн огноо авах.

    Шөнийн ээлж (00:00-07:00) бол өмнөх өдрийн огноо буцаана.
    Өдрийн ээлж (07:01-24:00) бол тухайн өдрийн огноо буцаана.

    Args:
        dt: datetime объект (default: now)

    Returns:
        date: Ээлжийн огноо

    Examples:
        >>> from datetime import datetime
        >>> get_shift_date(datetime(2025, 12, 3, 2, 0))  # 02:00
        date(2025, 12, 2)  # Өчигдөр
        >>> get_shift_date(datetime(2025, 12, 3, 8, 0))  # 08:00
        date(2025, 12, 3)  # Өнөөдөр
    """
    if dt is None:
        dt = now_local()
    _, anchor_date = _get_shift_type_and_anchor_date(dt)
    return anchor_date


def get_current_shift_start(current_dt: datetime) -> datetime:
    """
    Одоогийн цагт харгалзах ээлжийн ЭХЛЭХ цагийг буцаана.

    Дүрэм:
    - Ээлж өглөө 08:00 цагт эхэлнэ.
    - Хэрэв одоо 08:00-аас хойш бол (ж: 14:00) -> Өнөөдрийн 08:00
    - Хэрэв одоо 08:00-аас өмнө бол (ж: 02:00) -> Өчигдрийн 08:00

    Args:
        current_dt: Одоогийн datetime

    Returns:
        datetime: Ээлжийн эхлэх цаг

    Examples:
        >>> from datetime import datetime
        >>> # 14:00 цагт - өнөөдрийн 08:00 буцаана
        >>> get_current_shift_start(datetime(2025, 1, 15, 14, 0))
        datetime.datetime(2025, 1, 15, 8, 0)
        >>> # 02:00 цагт - өчигдрийн 08:00 буцаана
        >>> get_current_shift_start(datetime(2025, 1, 15, 2, 0))
        datetime.datetime(2025, 1, 14, 8, 0)
    """
    SHIFT_START_HOUR = 8

    # Хэрэв одоогийн цаг 08:00-аас бага бол (шөнийн 00:00 - 07:59)
    # Ээлж нь "Өчигдөр" эхэлсэн гэж үзнэ.
    if current_dt.hour < SHIFT_START_HOUR:
        shift_date = current_dt.date() - timedelta(days=1)
    else:
        # 08:00-аас хойш бол "Өнөөдөр" эхэлсэн гэж үзнэ.
        shift_date = current_dt.date()

    # Тухайн өдрийн өглөөний 08:00:00 цагийг үүсгэнэ
    return datetime.combine(shift_date, time(SHIFT_START_HOUR, 0, 0))
