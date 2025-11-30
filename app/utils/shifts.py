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