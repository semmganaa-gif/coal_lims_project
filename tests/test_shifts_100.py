# -*- coding: utf-8 -*-
"""
shifts.py модулийн 100% coverage тестүүд
"""
import pytest
from datetime import datetime, date, time, timedelta
from unittest.mock import patch


class TestShiftsImport:
    """Модуль импорт тест"""

    def test_import_module(self):
        from app.utils import shifts
        assert shifts is not None

    def test_import_shift_info(self):
        from app.utils.shifts import ShiftInfo
        assert ShiftInfo is not None

    def test_import_functions(self):
        from app.utils.shifts import (
            get_shift_info, get_12h_shift_code, get_quarter_code,
            get_shift_date, get_current_shift_start
        )
        assert all(callable(f) for f in [
            get_shift_info, get_12h_shift_code, get_quarter_code,
            get_shift_date, get_current_shift_start
        ])

    def test_import_constants(self):
        from app.utils.shifts import CYCLE_START_DATE, DAY_START, DAY_END
        assert CYCLE_START_DATE is not None
        assert DAY_START is not None
        assert DAY_END is not None


class TestShiftInfo:
    """ShiftInfo dataclass тест"""

    def test_create_shift_info(self):
        from app.utils.shifts import ShiftInfo
        info = ShiftInfo(
            team="A",
            shift_type="day",
            anchor_date=date(2025, 1, 15),
            cycle_day_index=0,
            segment_index=0,
            shift_start=datetime(2025, 1, 15, 7, 1),
            shift_end=datetime(2025, 1, 15, 19, 0)
        )
        assert info.team == "A"
        assert info.shift_type == "day"

    def test_shift_info_label_day(self):
        from app.utils.shifts import ShiftInfo
        info = ShiftInfo(
            team="A", shift_type="day",
            anchor_date=date(2025, 1, 15),
            cycle_day_index=0, segment_index=0,
            shift_start=datetime(2025, 1, 15, 7, 1),
            shift_end=datetime(2025, 1, 15, 19, 0)
        )
        assert info.label == "A-Өдөр"

    def test_shift_info_label_night(self):
        from app.utils.shifts import ShiftInfo
        info = ShiftInfo(
            team="B", shift_type="night",
            anchor_date=date(2025, 1, 15),
            cycle_day_index=0, segment_index=0,
            shift_start=datetime(2025, 1, 15, 19, 1),
            shift_end=datetime(2025, 1, 16, 7, 0)
        )
        assert info.label == "B-Шөнө"


class TestGetShiftInfo:
    """get_shift_info функцийн тест"""

    def test_day_shift_morning(self):
        from app.utils.shifts import get_shift_info
        dt = datetime(2025, 11, 22, 8, 0)  # Cycle start date, 8:00 AM
        info = get_shift_info(dt)
        assert info.shift_type == "day"
        assert info.team == "A"  # First team on cycle start

    def test_day_shift_afternoon(self):
        from app.utils.shifts import get_shift_info
        dt = datetime(2025, 11, 22, 15, 0)  # 3:00 PM
        info = get_shift_info(dt)
        assert info.shift_type == "day"

    def test_night_shift_evening(self):
        from app.utils.shifts import get_shift_info
        dt = datetime(2025, 11, 22, 20, 0)  # 8:00 PM
        info = get_shift_info(dt)
        assert info.shift_type == "night"

    def test_night_shift_early_morning(self):
        from app.utils.shifts import get_shift_info
        dt = datetime(2025, 11, 23, 3, 0)  # 3:00 AM
        info = get_shift_info(dt)
        assert info.shift_type == "night"
        # anchor_date should be previous day
        assert info.anchor_date == date(2025, 11, 22)

    def test_shift_at_day_start(self):
        from app.utils.shifts import get_shift_info
        dt = datetime(2025, 11, 22, 7, 1)  # 7:01 AM - day starts
        info = get_shift_info(dt)
        assert info.shift_type == "day"

    def test_shift_at_day_end(self):
        from app.utils.shifts import get_shift_info
        dt = datetime(2025, 11, 22, 19, 0)  # 7:00 PM - day ends
        info = get_shift_info(dt)
        assert info.shift_type == "day"

    def test_shift_at_night_start(self):
        from app.utils.shifts import get_shift_info
        dt = datetime(2025, 11, 22, 19, 1)  # 7:01 PM - night starts
        info = get_shift_info(dt)
        assert info.shift_type == "night"


class TestCycleAndTeams:
    """Cycle болон team тооцооллын тест"""

    def test_segment_0_day_team(self):
        from app.utils.shifts import get_shift_info
        # Day 0-6 of cycle -> segment 0
        dt = datetime(2025, 11, 22, 10, 0)  # Day 0
        info = get_shift_info(dt)
        assert info.segment_index == 0
        assert info.team == "A"  # Day team for segment 0

    def test_segment_0_night_team(self):
        from app.utils.shifts import get_shift_info
        dt = datetime(2025, 11, 22, 21, 0)  # Night of day 0
        info = get_shift_info(dt)
        assert info.team == "B"  # Night team for segment 0

    def test_segment_1_day_team(self):
        from app.utils.shifts import get_shift_info
        # Day 7-13 -> segment 1
        dt = datetime(2025, 11, 29, 10, 0)  # Day 7
        info = get_shift_info(dt)
        assert info.segment_index == 1
        assert info.team == "C"  # Day team for segment 1

    def test_segment_1_night_team(self):
        from app.utils.shifts import get_shift_info
        dt = datetime(2025, 11, 29, 21, 0)  # Night of day 7
        info = get_shift_info(dt)
        assert info.team == "A"  # Night team for segment 1

    def test_segment_2_day_team(self):
        from app.utils.shifts import get_shift_info
        # Day 14-20 -> segment 2
        dt = datetime(2025, 12, 6, 10, 0)  # Day 14
        info = get_shift_info(dt)
        assert info.segment_index == 2
        assert info.team == "B"  # Day team for segment 2

    def test_segment_2_night_team(self):
        from app.utils.shifts import get_shift_info
        dt = datetime(2025, 12, 6, 21, 0)  # Night of day 14
        info = get_shift_info(dt)
        assert info.team == "C"  # Night team for segment 2

    def test_cycle_wraps_around(self):
        from app.utils.shifts import get_shift_info
        # Day 21 -> back to segment 0
        dt = datetime(2025, 12, 13, 10, 0)  # Day 21 = Day 0 of new cycle
        info = get_shift_info(dt)
        assert info.cycle_day_index == 0
        assert info.segment_index == 0


class TestGet12hShiftCode:
    """get_12h_shift_code функцийн тест"""

    def test_day_shift_7am(self):
        from app.utils.shifts import get_12h_shift_code
        dt = datetime(2025, 1, 15, 7, 0)
        assert get_12h_shift_code(dt) == "_D"

    def test_day_shift_noon(self):
        from app.utils.shifts import get_12h_shift_code
        dt = datetime(2025, 1, 15, 12, 0)
        assert get_12h_shift_code(dt) == "_D"

    def test_day_shift_6pm(self):
        from app.utils.shifts import get_12h_shift_code
        dt = datetime(2025, 1, 15, 18, 0)
        assert get_12h_shift_code(dt) == "_D"

    def test_night_shift_7pm(self):
        from app.utils.shifts import get_12h_shift_code
        dt = datetime(2025, 1, 15, 19, 0)
        assert get_12h_shift_code(dt) == "_N"

    def test_night_shift_midnight(self):
        from app.utils.shifts import get_12h_shift_code
        dt = datetime(2025, 1, 15, 0, 0)
        assert get_12h_shift_code(dt) == "_N"

    def test_night_shift_6am(self):
        from app.utils.shifts import get_12h_shift_code
        dt = datetime(2025, 1, 15, 6, 0)
        assert get_12h_shift_code(dt) == "_N"


class TestGetQuarterCode:
    """get_quarter_code функцийн тест"""

    def test_q1_january(self):
        from app.utils.shifts import get_quarter_code
        dt = datetime(2025, 1, 15)
        assert get_quarter_code(dt) == "_Q1"

    def test_q1_march(self):
        from app.utils.shifts import get_quarter_code
        dt = datetime(2025, 3, 31)
        assert get_quarter_code(dt) == "_Q1"

    def test_q2_april(self):
        from app.utils.shifts import get_quarter_code
        dt = datetime(2025, 4, 1)
        assert get_quarter_code(dt) == "_Q2"

    def test_q2_june(self):
        from app.utils.shifts import get_quarter_code
        dt = datetime(2025, 6, 30)
        assert get_quarter_code(dt) == "_Q2"

    def test_q3_july(self):
        from app.utils.shifts import get_quarter_code
        dt = datetime(2025, 7, 1)
        assert get_quarter_code(dt) == "_Q3"

    def test_q3_september(self):
        from app.utils.shifts import get_quarter_code
        dt = datetime(2025, 9, 30)
        assert get_quarter_code(dt) == "_Q3"

    def test_q4_october(self):
        from app.utils.shifts import get_quarter_code
        dt = datetime(2025, 10, 1)
        assert get_quarter_code(dt) == "_Q4"

    def test_q4_december(self):
        from app.utils.shifts import get_quarter_code
        dt = datetime(2025, 12, 31)
        assert get_quarter_code(dt) == "_Q4"


class TestGetShiftDate:
    """get_shift_date функцийн тест"""

    @patch('app.utils.shifts.now_local')
    def test_default_now(self, mock_now):
        from app.utils.shifts import get_shift_date
        mock_now.return_value = datetime(2025, 1, 15, 10, 0)
        result = get_shift_date()
        assert result == date(2025, 1, 15)

    def test_day_shift(self):
        from app.utils.shifts import get_shift_date
        dt = datetime(2025, 1, 15, 10, 0)  # 10 AM
        result = get_shift_date(dt)
        assert result == date(2025, 1, 15)

    def test_night_shift_evening(self):
        from app.utils.shifts import get_shift_date
        dt = datetime(2025, 1, 15, 21, 0)  # 9 PM
        result = get_shift_date(dt)
        assert result == date(2025, 1, 15)

    def test_night_shift_early_morning(self):
        from app.utils.shifts import get_shift_date
        dt = datetime(2025, 1, 15, 3, 0)  # 3 AM
        result = get_shift_date(dt)
        # Should return previous day
        assert result == date(2025, 1, 14)


class TestGetCurrentShiftStart:
    """get_current_shift_start функцийн тест"""

    def test_after_8am(self):
        from app.utils.shifts import get_current_shift_start
        dt = datetime(2025, 1, 15, 14, 0)  # 2 PM
        result = get_current_shift_start(dt)
        assert result == datetime(2025, 1, 15, 8, 0)

    def test_at_8am(self):
        from app.utils.shifts import get_current_shift_start
        dt = datetime(2025, 1, 15, 8, 0)  # Exactly 8 AM
        result = get_current_shift_start(dt)
        assert result == datetime(2025, 1, 15, 8, 0)

    def test_before_8am(self):
        from app.utils.shifts import get_current_shift_start
        dt = datetime(2025, 1, 15, 2, 0)  # 2 AM
        result = get_current_shift_start(dt)
        # Should return previous day's 8 AM
        assert result == datetime(2025, 1, 14, 8, 0)

    def test_at_midnight(self):
        from app.utils.shifts import get_current_shift_start
        dt = datetime(2025, 1, 15, 0, 0)  # Midnight
        result = get_current_shift_start(dt)
        assert result == datetime(2025, 1, 14, 8, 0)


class TestPrivateFunctions:
    """Private функцүүдийн тест"""

    def test_get_shift_type_and_anchor_date_day(self):
        from app.utils.shifts import _get_shift_type_and_anchor_date
        dt = datetime(2025, 1, 15, 10, 0)
        shift_type, anchor = _get_shift_type_and_anchor_date(dt)
        assert shift_type == "day"
        assert anchor == date(2025, 1, 15)

    def test_get_shift_type_and_anchor_date_night_late(self):
        from app.utils.shifts import _get_shift_type_and_anchor_date
        dt = datetime(2025, 1, 15, 21, 0)  # 9 PM
        shift_type, anchor = _get_shift_type_and_anchor_date(dt)
        assert shift_type == "night"
        assert anchor == date(2025, 1, 15)

    def test_get_shift_type_and_anchor_date_night_early(self):
        from app.utils.shifts import _get_shift_type_and_anchor_date
        dt = datetime(2025, 1, 15, 3, 0)  # 3 AM
        shift_type, anchor = _get_shift_type_and_anchor_date(dt)
        assert shift_type == "night"
        assert anchor == date(2025, 1, 14)  # Previous day

    def test_get_cycle_day_index(self):
        from app.utils.shifts import _get_cycle_day_index, CYCLE_START_DATE
        # Day 0
        assert _get_cycle_day_index(CYCLE_START_DATE) == 0
        # Day 7
        assert _get_cycle_day_index(CYCLE_START_DATE + timedelta(days=7)) == 7
        # Day 21 = Day 0 (cycle wraps)
        assert _get_cycle_day_index(CYCLE_START_DATE + timedelta(days=21)) == 0

    def test_get_team_for_segment_day(self):
        from app.utils.shifts import _get_team_for_segment
        assert _get_team_for_segment(0, "day") == "A"
        assert _get_team_for_segment(1, "day") == "C"
        assert _get_team_for_segment(2, "day") == "B"

    def test_get_team_for_segment_night(self):
        from app.utils.shifts import _get_team_for_segment
        assert _get_team_for_segment(0, "night") == "B"
        assert _get_team_for_segment(1, "night") == "A"
        assert _get_team_for_segment(2, "night") == "C"

    def test_compute_shift_start_end_day(self):
        from app.utils.shifts import _compute_shift_start_end
        anchor = date(2025, 1, 15)
        start, end = _compute_shift_start_end(anchor, "day")
        assert start == datetime(2025, 1, 15, 7, 1)
        assert end == datetime(2025, 1, 15, 19, 0)

    def test_compute_shift_start_end_night(self):
        from app.utils.shifts import _compute_shift_start_end
        anchor = date(2025, 1, 15)
        start, end = _compute_shift_start_end(anchor, "night")
        assert start == datetime(2025, 1, 15, 19, 1)
        assert end == datetime(2025, 1, 16, 7, 0)


class TestTimezoneAware:
    """Timezone-aware datetime тест"""

    def test_tz_aware_datetime(self):
        from app.utils.shifts import get_shift_info
        import pytz

        tz = pytz.timezone('Asia/Ulaanbaatar')
        dt = tz.localize(datetime(2025, 1, 15, 10, 0))
        info = get_shift_info(dt)
        assert info.shift_type == "day"
