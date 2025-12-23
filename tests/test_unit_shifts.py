# tests/unit/test_shifts.py
# -*- coding: utf-8 -*-
"""
Shifts module тест

Tests for shift calculation utilities.
"""

import pytest
from datetime import datetime, date, time, timedelta

from app.utils.shifts import (
    ShiftInfo,
    CYCLE_START_DATE,
    DAY_START,
    DAY_END,
    get_shift_info,
    get_12h_shift_code,
    get_quarter_code,
    get_shift_date,
    get_current_shift_start,
    _get_shift_type_and_anchor_date,
    _get_cycle_day_index,
    _get_team_for_segment,
    _compute_shift_start_end,
)


class TestShiftInfo:
    """ShiftInfo dataclass тест"""

    def test_shift_info_creation(self):
        """ShiftInfo объект үүсгэх"""
        info = ShiftInfo(
            team="A",
            shift_type="day",
            anchor_date=date(2025, 12, 11),
            cycle_day_index=5,
            segment_index=0,
            shift_start=datetime(2025, 12, 11, 7, 1),
            shift_end=datetime(2025, 12, 11, 19, 0)
        )
        assert info.team == "A"
        assert info.shift_type == "day"
        assert info.anchor_date == date(2025, 12, 11)

    def test_label_day_shift(self):
        """Label - өдрийн ээлж"""
        info = ShiftInfo(
            team="A",
            shift_type="day",
            anchor_date=date(2025, 12, 11),
            cycle_day_index=0,
            segment_index=0,
            shift_start=datetime(2025, 12, 11, 7, 1),
            shift_end=datetime(2025, 12, 11, 19, 0)
        )
        assert info.label == "A-Өдөр"

    def test_label_night_shift(self):
        """Label - шөнийн ээлж"""
        info = ShiftInfo(
            team="B",
            shift_type="night",
            anchor_date=date(2025, 12, 11),
            cycle_day_index=0,
            segment_index=0,
            shift_start=datetime(2025, 12, 11, 19, 1),
            shift_end=datetime(2025, 12, 12, 7, 0)
        )
        assert info.label == "B-Шөнө"


class TestGetShiftTypeAndAnchorDate:
    """_get_shift_type_and_anchor_date() функцийн тест"""

    def test_day_shift_morning(self):
        """Өглөөний цаг - өдрийн ээлж"""
        dt = datetime(2025, 12, 11, 8, 0)
        shift_type, anchor = _get_shift_type_and_anchor_date(dt)
        assert shift_type == "day"
        assert anchor == date(2025, 12, 11)

    def test_day_shift_afternoon(self):
        """Үдээс хойш - өдрийн ээлж"""
        dt = datetime(2025, 12, 11, 15, 0)
        shift_type, anchor = _get_shift_type_and_anchor_date(dt)
        assert shift_type == "day"
        assert anchor == date(2025, 12, 11)

    def test_day_shift_boundary_start(self):
        """Өдрийн ээлж эхлэх цаг - 07:01"""
        dt = datetime(2025, 12, 11, 7, 1)
        shift_type, anchor = _get_shift_type_and_anchor_date(dt)
        assert shift_type == "day"

    def test_day_shift_boundary_end(self):
        """Өдрийн ээлж дуусах цаг - 19:00"""
        dt = datetime(2025, 12, 11, 19, 0)
        shift_type, anchor = _get_shift_type_and_anchor_date(dt)
        assert shift_type == "day"

    def test_night_shift_evening(self):
        """Оройн цаг - шөнийн ээлж"""
        dt = datetime(2025, 12, 11, 20, 0)
        shift_type, anchor = _get_shift_type_and_anchor_date(dt)
        assert shift_type == "night"
        assert anchor == date(2025, 12, 11)

    def test_night_shift_midnight(self):
        """Шөнө дунд - өмнөх өдрийн ээлж"""
        dt = datetime(2025, 12, 12, 2, 0)
        shift_type, anchor = _get_shift_type_and_anchor_date(dt)
        assert shift_type == "night"
        assert anchor == date(2025, 12, 11)  # Өмнөх өдөр

    def test_night_shift_early_morning(self):
        """Өглөө эрт - өмнөх өдрийн ээлж"""
        dt = datetime(2025, 12, 12, 5, 0)
        shift_type, anchor = _get_shift_type_and_anchor_date(dt)
        assert shift_type == "night"
        assert anchor == date(2025, 12, 11)

    def test_before_day_start(self):
        """07:00 - өдрийн ээлж эхлээгүй"""
        dt = datetime(2025, 12, 11, 7, 0)
        shift_type, anchor = _get_shift_type_and_anchor_date(dt)
        assert shift_type == "night"  # Still night shift from previous day


class TestGetCycleDayIndex:
    """_get_cycle_day_index() функцийн тест"""

    def test_cycle_start_date(self):
        """Циклийн эхлэх өдөр"""
        index = _get_cycle_day_index(CYCLE_START_DATE)
        assert index == 0

    def test_cycle_day_1(self):
        """Циклийн 2 дахь өдөр"""
        index = _get_cycle_day_index(CYCLE_START_DATE + timedelta(days=1))
        assert index == 1

    def test_cycle_day_20(self):
        """Циклийн сүүлийн өдөр (21 дэх)"""
        index = _get_cycle_day_index(CYCLE_START_DATE + timedelta(days=20))
        assert index == 20

    def test_cycle_wraps_around(self):
        """Цикл 21 хоногоор давтагдана"""
        index = _get_cycle_day_index(CYCLE_START_DATE + timedelta(days=21))
        assert index == 0

    def test_cycle_multiple_wraps(self):
        """Олон цикл"""
        index = _get_cycle_day_index(CYCLE_START_DATE + timedelta(days=42))
        assert index == 0

        index = _get_cycle_day_index(CYCLE_START_DATE + timedelta(days=43))
        assert index == 1


class TestGetTeamForSegment:
    """_get_team_for_segment() функцийн тест"""

    def test_segment_0_day(self):
        """Segment 0 - Өдөр: A баг"""
        team = _get_team_for_segment(0, "day")
        assert team == "A"

    def test_segment_0_night(self):
        """Segment 0 - Шөнө: B баг"""
        team = _get_team_for_segment(0, "night")
        assert team == "B"

    def test_segment_1_day(self):
        """Segment 1 - Өдөр: C баг"""
        team = _get_team_for_segment(1, "day")
        assert team == "C"

    def test_segment_1_night(self):
        """Segment 1 - Шөнө: A баг"""
        team = _get_team_for_segment(1, "night")
        assert team == "A"

    def test_segment_2_day(self):
        """Segment 2 - Өдөр: B баг"""
        team = _get_team_for_segment(2, "day")
        assert team == "B"

    def test_segment_2_night(self):
        """Segment 2 - Шөнө: C баг"""
        team = _get_team_for_segment(2, "night")
        assert team == "C"


class TestComputeShiftStartEnd:
    """_compute_shift_start_end() функцийн тест"""

    def test_day_shift_times(self):
        """Өдрийн ээлжийн эхлэх/дуусах цаг"""
        start, end = _compute_shift_start_end(date(2025, 12, 11), "day")
        assert start == datetime(2025, 12, 11, 7, 1)
        assert end == datetime(2025, 12, 11, 19, 0)

    def test_night_shift_times(self):
        """Шөнийн ээлжийн эхлэх/дуусах цаг"""
        start, end = _compute_shift_start_end(date(2025, 12, 11), "night")
        assert start == datetime(2025, 12, 11, 19, 1)
        assert end == datetime(2025, 12, 12, 7, 0)  # Дараагийн өглөө


class TestGetShiftInfo:
    """get_shift_info() функцийн тест (гол функц)"""

    def test_day_shift_info(self):
        """Өдрийн ээлжийн мэдээлэл"""
        dt = datetime(2025, 11, 22, 10, 0)  # CYCLE_START_DATE, өдөр
        info = get_shift_info(dt)

        assert info.shift_type == "day"
        assert info.anchor_date == date(2025, 11, 22)
        assert info.cycle_day_index == 0
        assert info.segment_index == 0
        assert info.team == "A"

    def test_night_shift_info(self):
        """Шөнийн ээлжийн мэдээлэл"""
        dt = datetime(2025, 11, 22, 22, 0)  # CYCLE_START_DATE, шөнө
        info = get_shift_info(dt)

        assert info.shift_type == "night"
        assert info.anchor_date == date(2025, 11, 22)
        assert info.team == "B"  # Шөнийн ээлж - B баг

    def test_shift_info_has_start_end(self):
        """ShiftInfo start/end цагуудтай"""
        dt = datetime(2025, 11, 22, 10, 0)
        info = get_shift_info(dt)

        assert info.shift_start is not None
        assert info.shift_end is not None
        assert info.shift_start < info.shift_end


class TestGet12hShiftCode:
    """get_12h_shift_code() функцийн тест"""

    def test_day_shift_morning(self):
        """7:00 - Өдрийн ээлж"""
        assert get_12h_shift_code(datetime(2025, 1, 1, 7, 0)) == "_D"

    def test_day_shift_afternoon(self):
        """15:00 - Өдрийн ээлж"""
        assert get_12h_shift_code(datetime(2025, 1, 1, 15, 0)) == "_D"

    def test_day_shift_boundary(self):
        """18:59 - Өдрийн ээлж"""
        assert get_12h_shift_code(datetime(2025, 1, 1, 18, 59)) == "_D"

    def test_night_shift_evening(self):
        """19:00 - Шөнийн ээлж"""
        assert get_12h_shift_code(datetime(2025, 1, 1, 19, 0)) == "_N"

    def test_night_shift_midnight(self):
        """00:00 - Шөнийн ээлж"""
        assert get_12h_shift_code(datetime(2025, 1, 1, 0, 0)) == "_N"

    def test_night_shift_early_morning(self):
        """06:59 - Шөнийн ээлж"""
        assert get_12h_shift_code(datetime(2025, 1, 1, 6, 59)) == "_N"


class TestGetQuarterCode:
    """get_quarter_code() функцийн тест"""

    def test_q1_january(self):
        """1 сар - Q1"""
        assert get_quarter_code(datetime(2025, 1, 15)) == "_Q1"

    def test_q1_march(self):
        """3 сар - Q1"""
        assert get_quarter_code(datetime(2025, 3, 31)) == "_Q1"

    def test_q2_april(self):
        """4 сар - Q2"""
        assert get_quarter_code(datetime(2025, 4, 1)) == "_Q2"

    def test_q2_june(self):
        """6 сар - Q2"""
        assert get_quarter_code(datetime(2025, 6, 30)) == "_Q2"

    def test_q3_july(self):
        """7 сар - Q3"""
        assert get_quarter_code(datetime(2025, 7, 1)) == "_Q3"

    def test_q3_september(self):
        """9 сар - Q3"""
        assert get_quarter_code(datetime(2025, 9, 30)) == "_Q3"

    def test_q4_october(self):
        """10 сар - Q4"""
        assert get_quarter_code(datetime(2025, 10, 1)) == "_Q4"

    def test_q4_december(self):
        """12 сар - Q4"""
        assert get_quarter_code(datetime(2025, 12, 31)) == "_Q4"


class TestGetShiftDate:
    """get_shift_date() функцийн тест"""

    def test_day_shift_returns_same_date(self):
        """Өдрийн ээлж - тухайн өдөр"""
        dt = datetime(2025, 12, 11, 10, 0)
        assert get_shift_date(dt) == date(2025, 12, 11)

    def test_night_shift_evening_returns_same_date(self):
        """Шөнийн ээлж (орой) - тухайн өдөр"""
        dt = datetime(2025, 12, 11, 22, 0)
        assert get_shift_date(dt) == date(2025, 12, 11)

    def test_night_shift_early_morning_returns_previous_date(self):
        """Шөнийн ээлж (өглөө эрт) - өмнөх өдөр"""
        dt = datetime(2025, 12, 12, 2, 0)
        assert get_shift_date(dt) == date(2025, 12, 11)

    def test_none_uses_current_time(self):
        """None үед одоогийн цагийг ашиглана"""
        result = get_shift_date(None)
        assert isinstance(result, date)


class TestGetCurrentShiftStart:
    """get_current_shift_start() функцийн тест"""

    def test_after_8am_returns_today_8am(self):
        """08:00-аас хойш - өнөөдрийн 08:00"""
        dt = datetime(2025, 12, 11, 14, 0)
        result = get_current_shift_start(dt)
        assert result == datetime(2025, 12, 11, 8, 0)

    def test_at_8am_returns_today_8am(self):
        """08:00 - өнөөдрийн 08:00"""
        dt = datetime(2025, 12, 11, 8, 0)
        result = get_current_shift_start(dt)
        assert result == datetime(2025, 12, 11, 8, 0)

    def test_before_8am_returns_yesterday_8am(self):
        """08:00-аас өмнө - өчигдрийн 08:00"""
        dt = datetime(2025, 12, 11, 2, 0)
        result = get_current_shift_start(dt)
        assert result == datetime(2025, 12, 10, 8, 0)

    def test_at_7_59_returns_yesterday_8am(self):
        """07:59 - өчигдрийн 08:00"""
        dt = datetime(2025, 12, 11, 7, 59)
        result = get_current_shift_start(dt)
        assert result == datetime(2025, 12, 10, 8, 0)
