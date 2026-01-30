# -*- coding: utf-8 -*-
"""
Shifts модулийн coverage тестүүд
"""
import pytest
from unittest.mock import patch
from datetime import datetime, date, time, timedelta


class TestShiftInfo:
    """ShiftInfo dataclass тестүүд"""

    def test_import_class(self):
        """Class import"""
        from app.utils.shifts import ShiftInfo
        assert ShiftInfo is not None

    def test_create_shift_info(self):
        """Create ShiftInfo instance"""
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

    def test_label_day(self):
        """Label for day shift"""
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
        assert "Өдөр" in info.label
        assert "A" in info.label

    def test_label_night(self):
        """Label for night shift"""
        from app.utils.shifts import ShiftInfo
        info = ShiftInfo(
            team="B",
            shift_type="night",
            anchor_date=date(2025, 1, 15),
            cycle_day_index=0,
            segment_index=0,
            shift_start=datetime(2025, 1, 15, 19, 1),
            shift_end=datetime(2025, 1, 16, 7, 0)
        )
        assert "Шөнө" in info.label
        assert "B" in info.label


class TestGetShiftTypeAndAnchorDate:
    """_get_shift_type_and_anchor_date тестүүд"""

    def test_import_function(self):
        """Function import"""
        from app.utils.shifts import _get_shift_type_and_anchor_date
        assert _get_shift_type_and_anchor_date is not None

    def test_day_shift_morning(self):
        """Day shift in morning"""
        from app.utils.shifts import _get_shift_type_and_anchor_date
        dt = datetime(2025, 1, 15, 8, 0)
        shift_type, anchor = _get_shift_type_and_anchor_date(dt)
        assert shift_type == "day"
        assert anchor == date(2025, 1, 15)

    def test_day_shift_afternoon(self):
        """Day shift in afternoon"""
        from app.utils.shifts import _get_shift_type_and_anchor_date
        dt = datetime(2025, 1, 15, 15, 0)
        shift_type, anchor = _get_shift_type_and_anchor_date(dt)
        assert shift_type == "day"
        assert anchor == date(2025, 1, 15)

    def test_day_shift_boundary_start(self):
        """Day shift at 07:01"""
        from app.utils.shifts import _get_shift_type_and_anchor_date
        dt = datetime(2025, 1, 15, 7, 1)
        shift_type, anchor = _get_shift_type_and_anchor_date(dt)
        assert shift_type == "day"

    def test_day_shift_boundary_end(self):
        """Day shift at 19:00"""
        from app.utils.shifts import _get_shift_type_and_anchor_date
        dt = datetime(2025, 1, 15, 19, 0)
        shift_type, anchor = _get_shift_type_and_anchor_date(dt)
        assert shift_type == "day"

    def test_night_shift_evening(self):
        """Night shift in evening (19:01-23:59)"""
        from app.utils.shifts import _get_shift_type_and_anchor_date
        dt = datetime(2025, 1, 15, 21, 0)
        shift_type, anchor = _get_shift_type_and_anchor_date(dt)
        assert shift_type == "night"
        assert anchor == date(2025, 1, 15)

    def test_night_shift_early_morning(self):
        """Night shift in early morning (00:00-07:00)"""
        from app.utils.shifts import _get_shift_type_and_anchor_date
        dt = datetime(2025, 1, 15, 3, 0)
        shift_type, anchor = _get_shift_type_and_anchor_date(dt)
        assert shift_type == "night"
        assert anchor == date(2025, 1, 14)  # Previous day

    def test_tz_aware_datetime(self):
        """TZ-aware datetime"""
        from app.utils.shifts import _get_shift_type_and_anchor_date
        from zoneinfo import ZoneInfo
        dt = datetime(2025, 1, 15, 10, 0, tzinfo=ZoneInfo("Asia/Ulaanbaatar"))
        shift_type, anchor = _get_shift_type_and_anchor_date(dt)
        assert shift_type == "day"


class TestGetCycleDayIndex:
    """_get_cycle_day_index тестүүд"""

    def test_import_function(self):
        """Function import"""
        from app.utils.shifts import _get_cycle_day_index
        assert _get_cycle_day_index is not None

    def test_cycle_start_date(self):
        """Day 0 at cycle start"""
        from app.utils.shifts import _get_cycle_day_index, CYCLE_START_DATE
        result = _get_cycle_day_index(CYCLE_START_DATE)
        assert result == 0

    def test_cycle_day_7(self):
        """Day 7 (one week later)"""
        from app.utils.shifts import _get_cycle_day_index, CYCLE_START_DATE
        d = CYCLE_START_DATE + timedelta(days=7)
        result = _get_cycle_day_index(d)
        assert result == 7

    def test_cycle_day_21_wraps(self):
        """Day 21 wraps to 0"""
        from app.utils.shifts import _get_cycle_day_index, CYCLE_START_DATE
        d = CYCLE_START_DATE + timedelta(days=21)
        result = _get_cycle_day_index(d)
        assert result == 0

    def test_cycle_day_25(self):
        """Day 25 wraps to 4"""
        from app.utils.shifts import _get_cycle_day_index, CYCLE_START_DATE
        d = CYCLE_START_DATE + timedelta(days=25)
        result = _get_cycle_day_index(d)
        assert result == 4


class TestGetTeamForSegment:
    """_get_team_for_segment тестүүд"""

    def test_import_function(self):
        """Function import"""
        from app.utils.shifts import _get_team_for_segment
        assert _get_team_for_segment is not None

    def test_segment_0_day(self):
        """Segment 0 day -> A"""
        from app.utils.shifts import _get_team_for_segment
        assert _get_team_for_segment(0, "day") == "A"

    def test_segment_0_night(self):
        """Segment 0 night -> B"""
        from app.utils.shifts import _get_team_for_segment
        assert _get_team_for_segment(0, "night") == "B"

    def test_segment_1_day(self):
        """Segment 1 day -> C"""
        from app.utils.shifts import _get_team_for_segment
        assert _get_team_for_segment(1, "day") == "C"

    def test_segment_1_night(self):
        """Segment 1 night -> A"""
        from app.utils.shifts import _get_team_for_segment
        assert _get_team_for_segment(1, "night") == "A"

    def test_segment_2_day(self):
        """Segment 2 day -> B"""
        from app.utils.shifts import _get_team_for_segment
        assert _get_team_for_segment(2, "day") == "B"

    def test_segment_2_night(self):
        """Segment 2 night -> C"""
        from app.utils.shifts import _get_team_for_segment
        assert _get_team_for_segment(2, "night") == "C"


class TestComputeShiftStartEnd:
    """_compute_shift_start_end тестүүд"""

    def test_import_function(self):
        """Function import"""
        from app.utils.shifts import _compute_shift_start_end
        assert _compute_shift_start_end is not None

    def test_day_shift(self):
        """Day shift start/end"""
        from app.utils.shifts import _compute_shift_start_end
        start, end = _compute_shift_start_end(date(2025, 1, 15), "day")
        assert start.hour == 7
        assert start.minute == 1
        assert end.hour == 19
        assert end.minute == 0
        assert start.date() == date(2025, 1, 15)
        assert end.date() == date(2025, 1, 15)

    def test_night_shift(self):
        """Night shift start/end"""
        from app.utils.shifts import _compute_shift_start_end
        start, end = _compute_shift_start_end(date(2025, 1, 15), "night")
        assert start.hour == 19
        assert start.minute == 1
        assert end.hour == 7
        assert end.minute == 0
        assert start.date() == date(2025, 1, 15)
        assert end.date() == date(2025, 1, 16)  # Next day


class TestGetShiftInfo:
    """get_shift_info тестүүд"""

    def test_import_function(self):
        """Function import"""
        from app.utils.shifts import get_shift_info
        assert get_shift_info is not None

    def test_day_shift(self):
        """Day shift info"""
        from app.utils.shifts import get_shift_info
        dt = datetime(2025, 11, 22, 10, 0)  # Cycle start date
        info = get_shift_info(dt)
        assert info.shift_type == "day"
        assert info.team == "A"  # First day of cycle

    def test_night_shift(self):
        """Night shift info"""
        from app.utils.shifts import get_shift_info
        dt = datetime(2025, 11, 22, 21, 0)  # Night shift on cycle start
        info = get_shift_info(dt)
        assert info.shift_type == "night"
        assert info.team == "B"

    def test_has_all_fields(self):
        """Info has all required fields"""
        from app.utils.shifts import get_shift_info
        dt = datetime(2025, 1, 15, 10, 0)
        info = get_shift_info(dt)
        assert hasattr(info, 'team')
        assert hasattr(info, 'shift_type')
        assert hasattr(info, 'anchor_date')
        assert hasattr(info, 'cycle_day_index')
        assert hasattr(info, 'segment_index')
        assert hasattr(info, 'shift_start')
        assert hasattr(info, 'shift_end')


class TestGet12hShiftCode:
    """get_12h_shift_code тестүүд"""

    def test_import_function(self):
        """Function import"""
        from app.utils.shifts import get_12h_shift_code
        assert get_12h_shift_code is not None

    def test_day_shift_7am(self):
        """Day shift at 7:00"""
        from app.utils.shifts import get_12h_shift_code
        dt = datetime(2025, 1, 15, 7, 0)
        assert get_12h_shift_code(dt) == "_D"

    def test_day_shift_noon(self):
        """Day shift at noon"""
        from app.utils.shifts import get_12h_shift_code
        dt = datetime(2025, 1, 15, 12, 0)
        assert get_12h_shift_code(dt) == "_D"

    def test_day_shift_6pm(self):
        """Day shift at 18:00"""
        from app.utils.shifts import get_12h_shift_code
        dt = datetime(2025, 1, 15, 18, 0)
        assert get_12h_shift_code(dt) == "_D"

    def test_night_shift_7pm(self):
        """Night shift at 19:00"""
        from app.utils.shifts import get_12h_shift_code
        dt = datetime(2025, 1, 15, 19, 0)
        assert get_12h_shift_code(dt) == "_N"

    def test_night_shift_midnight(self):
        """Night shift at midnight"""
        from app.utils.shifts import get_12h_shift_code
        dt = datetime(2025, 1, 15, 0, 0)
        assert get_12h_shift_code(dt) == "_N"

    def test_night_shift_early_morning(self):
        """Night shift at 3:00"""
        from app.utils.shifts import get_12h_shift_code
        dt = datetime(2025, 1, 15, 3, 0)
        assert get_12h_shift_code(dt) == "_N"


class TestGetQuarterCode:
    """get_quarter_code тестүүд"""

    def test_import_function(self):
        """Function import"""
        from app.utils.shifts import get_quarter_code
        assert get_quarter_code is not None

    def test_q1_january(self):
        """Q1 in January"""
        from app.utils.shifts import get_quarter_code
        dt = datetime(2025, 1, 15)
        assert get_quarter_code(dt) == "_Q1"

    def test_q1_march(self):
        """Q1 in March"""
        from app.utils.shifts import get_quarter_code
        dt = datetime(2025, 3, 31)
        assert get_quarter_code(dt) == "_Q1"

    def test_q2_april(self):
        """Q2 in April"""
        from app.utils.shifts import get_quarter_code
        dt = datetime(2025, 4, 1)
        assert get_quarter_code(dt) == "_Q2"

    def test_q2_june(self):
        """Q2 in June"""
        from app.utils.shifts import get_quarter_code
        dt = datetime(2025, 6, 30)
        assert get_quarter_code(dt) == "_Q2"

    def test_q3_july(self):
        """Q3 in July"""
        from app.utils.shifts import get_quarter_code
        dt = datetime(2025, 7, 1)
        assert get_quarter_code(dt) == "_Q3"

    def test_q3_september(self):
        """Q3 in September"""
        from app.utils.shifts import get_quarter_code
        dt = datetime(2025, 9, 30)
        assert get_quarter_code(dt) == "_Q3"

    def test_q4_october(self):
        """Q4 in October"""
        from app.utils.shifts import get_quarter_code
        dt = datetime(2025, 10, 1)
        assert get_quarter_code(dt) == "_Q4"

    def test_q4_december(self):
        """Q4 in December"""
        from app.utils.shifts import get_quarter_code
        dt = datetime(2025, 12, 31)
        assert get_quarter_code(dt) == "_Q4"


class TestGetShiftDate:
    """get_shift_date тестүүд"""

    def test_import_function(self):
        """Function import"""
        from app.utils.shifts import get_shift_date
        assert get_shift_date is not None

    def test_day_shift(self):
        """Day shift returns today"""
        from app.utils.shifts import get_shift_date
        dt = datetime(2025, 1, 15, 10, 0)
        assert get_shift_date(dt) == date(2025, 1, 15)

    def test_night_shift_early_morning(self):
        """Night shift early morning returns previous day"""
        from app.utils.shifts import get_shift_date
        dt = datetime(2025, 1, 15, 2, 0)
        assert get_shift_date(dt) == date(2025, 1, 14)

    def test_night_shift_evening(self):
        """Night shift evening returns today"""
        from app.utils.shifts import get_shift_date
        dt = datetime(2025, 1, 15, 21, 0)
        assert get_shift_date(dt) == date(2025, 1, 15)

    @patch('app.utils.shifts.now_local')
    def test_no_dt_uses_now(self, mock_now):
        """No dt argument uses now_local"""
        from app.utils.shifts import get_shift_date
        mock_now.return_value = datetime(2025, 1, 15, 10, 0)
        result = get_shift_date()
        assert result == date(2025, 1, 15)


class TestGetCurrentShiftStart:
    """get_current_shift_start тестүүд"""

    def test_import_function(self):
        """Function import"""
        from app.utils.shifts import get_current_shift_start
        assert get_current_shift_start is not None

    def test_afternoon(self):
        """Afternoon returns today 08:00"""
        from app.utils.shifts import get_current_shift_start
        dt = datetime(2025, 1, 15, 14, 0)
        result = get_current_shift_start(dt)
        assert result == datetime(2025, 1, 15, 8, 0)

    def test_early_morning(self):
        """Early morning returns yesterday 08:00"""
        from app.utils.shifts import get_current_shift_start
        dt = datetime(2025, 1, 15, 2, 0)
        result = get_current_shift_start(dt)
        assert result == datetime(2025, 1, 14, 8, 0)

    def test_at_8am(self):
        """At 08:00 returns today 08:00"""
        from app.utils.shifts import get_current_shift_start
        dt = datetime(2025, 1, 15, 8, 0)
        result = get_current_shift_start(dt)
        assert result == datetime(2025, 1, 15, 8, 0)

    def test_at_7_59am(self):
        """At 07:59 returns yesterday 08:00"""
        from app.utils.shifts import get_current_shift_start
        dt = datetime(2025, 1, 15, 7, 59)
        result = get_current_shift_start(dt)
        assert result == datetime(2025, 1, 14, 8, 0)


class TestConstants:
    """Constants тестүүд"""

    def test_cycle_start_date(self):
        """CYCLE_START_DATE exists"""
        from app.utils.shifts import CYCLE_START_DATE
        assert isinstance(CYCLE_START_DATE, date)

    def test_day_start(self):
        """DAY_START exists"""
        from app.utils.shifts import DAY_START
        assert isinstance(DAY_START, time)
        assert DAY_START.hour == 7
        assert DAY_START.minute == 1

    def test_day_end(self):
        """DAY_END exists"""
        from app.utils.shifts import DAY_END
        assert isinstance(DAY_END, time)
        assert DAY_END.hour == 19
        assert DAY_END.minute == 0
