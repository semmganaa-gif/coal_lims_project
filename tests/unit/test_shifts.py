# -*- coding: utf-8 -*-
"""
Tests for app/utils/shifts.py
Shift calculation utilities comprehensive tests
"""
import pytest
from unittest.mock import patch, MagicMock
from datetime import date, datetime, time, timedelta


class TestShiftInfoDataclass:
    """ShiftInfo dataclass tests"""

    def test_import(self):
        """Import ShiftInfo"""
        from app.utils.shifts import ShiftInfo
        assert ShiftInfo is not None

    def test_create_day_shift_info(self):
        """Create day shift info"""
        from app.utils.shifts import ShiftInfo
        info = ShiftInfo(
            team="A",
            shift_type="day",
            anchor_date=date(2025, 11, 22),
            cycle_day_index=0,
            segment_index=0,
            shift_start=datetime(2025, 11, 22, 7, 1),
            shift_end=datetime(2025, 11, 22, 19, 0)
        )
        assert info.team == "A"
        assert info.shift_type == "day"

    def test_create_night_shift_info(self):
        """Create night shift info"""
        from app.utils.shifts import ShiftInfo
        info = ShiftInfo(
            team="B",
            shift_type="night",
            anchor_date=date(2025, 11, 22),
            cycle_day_index=0,
            segment_index=0,
            shift_start=datetime(2025, 11, 22, 19, 1),
            shift_end=datetime(2025, 11, 23, 7, 0)
        )
        assert info.team == "B"
        assert info.shift_type == "night"

    def test_label_day_shift(self):
        """Label for day shift shows correct Mongolian"""
        from app.utils.shifts import ShiftInfo
        info = ShiftInfo(
            team="A",
            shift_type="day",
            anchor_date=date(2025, 11, 22),
            cycle_day_index=0,
            segment_index=0,
            shift_start=datetime(2025, 11, 22, 7, 1),
            shift_end=datetime(2025, 11, 22, 19, 0)
        )
        assert info.label == "A-Өдөр"

    def test_label_night_shift(self):
        """Label for night shift shows correct Mongolian"""
        from app.utils.shifts import ShiftInfo
        info = ShiftInfo(
            team="B",
            shift_type="night",
            anchor_date=date(2025, 11, 22),
            cycle_day_index=0,
            segment_index=0,
            shift_start=datetime(2025, 11, 22, 19, 1),
            shift_end=datetime(2025, 11, 23, 7, 0)
        )
        assert info.label == "B-Шөнө"

    def test_label_team_c(self):
        """Label for team C"""
        from app.utils.shifts import ShiftInfo
        info = ShiftInfo(
            team="C",
            shift_type="day",
            anchor_date=date(2025, 11, 29),
            cycle_day_index=7,
            segment_index=1,
            shift_start=datetime(2025, 11, 29, 7, 1),
            shift_end=datetime(2025, 11, 29, 19, 0)
        )
        assert info.label == "C-Өдөр"


class TestConstants:
    """Constants tests"""

    def test_cycle_start_date(self):
        """CYCLE_START_DATE is correct"""
        from app.utils.shifts import CYCLE_START_DATE
        assert CYCLE_START_DATE == date(2025, 11, 22)

    def test_day_start_time(self):
        """DAY_START is 07:01"""
        from app.utils.shifts import DAY_START
        assert DAY_START == time(7, 1)

    def test_day_end_time(self):
        """DAY_END is 19:00"""
        from app.utils.shifts import DAY_END
        assert DAY_END == time(19, 0)


class TestGetShiftTypeAndAnchorDate:
    """_get_shift_type_and_anchor_date function tests"""

    def test_import(self):
        """Import function"""
        from app.utils.shifts import _get_shift_type_and_anchor_date
        assert callable(_get_shift_type_and_anchor_date)

    def test_morning_is_day_shift(self):
        """Morning time (08:00) is day shift"""
        from app.utils.shifts import _get_shift_type_and_anchor_date
        dt = datetime(2025, 11, 22, 8, 0)
        shift_type, anchor = _get_shift_type_and_anchor_date(dt)
        assert shift_type == "day"
        assert anchor == date(2025, 11, 22)

    def test_afternoon_is_day_shift(self):
        """Afternoon time (15:00) is day shift"""
        from app.utils.shifts import _get_shift_type_and_anchor_date
        dt = datetime(2025, 11, 22, 15, 0)
        shift_type, anchor = _get_shift_type_and_anchor_date(dt)
        assert shift_type == "day"
        assert anchor == date(2025, 11, 22)

    def test_day_start_boundary(self):
        """07:01 is day shift start"""
        from app.utils.shifts import _get_shift_type_and_anchor_date
        dt = datetime(2025, 11, 22, 7, 1)
        shift_type, anchor = _get_shift_type_and_anchor_date(dt)
        assert shift_type == "day"

    def test_day_end_boundary(self):
        """19:00 is still day shift"""
        from app.utils.shifts import _get_shift_type_and_anchor_date
        dt = datetime(2025, 11, 22, 19, 0)
        shift_type, anchor = _get_shift_type_and_anchor_date(dt)
        assert shift_type == "day"

    def test_evening_is_night_shift(self):
        """Evening time (20:00) is night shift"""
        from app.utils.shifts import _get_shift_type_and_anchor_date
        dt = datetime(2025, 11, 22, 20, 0)
        shift_type, anchor = _get_shift_type_and_anchor_date(dt)
        assert shift_type == "night"
        assert anchor == date(2025, 11, 22)

    def test_night_shift_start_boundary(self):
        """19:01 is night shift start"""
        from app.utils.shifts import _get_shift_type_and_anchor_date
        dt = datetime(2025, 11, 22, 19, 1)
        shift_type, anchor = _get_shift_type_and_anchor_date(dt)
        assert shift_type == "night"
        assert anchor == date(2025, 11, 22)

    def test_midnight_is_night_shift(self):
        """Midnight (00:00) is night shift"""
        from app.utils.shifts import _get_shift_type_and_anchor_date
        dt = datetime(2025, 11, 23, 0, 0)
        shift_type, anchor = _get_shift_type_and_anchor_date(dt)
        assert shift_type == "night"
        # Anchor is previous day
        assert anchor == date(2025, 11, 22)

    def test_early_morning_is_night_shift(self):
        """Early morning (02:00) is night shift with previous day anchor"""
        from app.utils.shifts import _get_shift_type_and_anchor_date
        dt = datetime(2025, 11, 23, 2, 0)
        shift_type, anchor = _get_shift_type_and_anchor_date(dt)
        assert shift_type == "night"
        assert anchor == date(2025, 11, 22)

    def test_before_day_start_is_night_shift(self):
        """07:00 is still night shift"""
        from app.utils.shifts import _get_shift_type_and_anchor_date
        dt = datetime(2025, 11, 23, 7, 0)
        shift_type, anchor = _get_shift_type_and_anchor_date(dt)
        assert shift_type == "night"
        assert anchor == date(2025, 11, 22)

    def test_late_night_before_midnight(self):
        """23:59 is night shift with same day anchor"""
        from app.utils.shifts import _get_shift_type_and_anchor_date
        dt = datetime(2025, 11, 22, 23, 59)
        shift_type, anchor = _get_shift_type_and_anchor_date(dt)
        assert shift_type == "night"
        assert anchor == date(2025, 11, 22)

    def test_timezone_aware_datetime(self):
        """Works with timezone-aware datetime"""
        from app.utils.shifts import _get_shift_type_and_anchor_date
        import pytz
        tz = pytz.timezone('Asia/Ulaanbaatar')
        dt = tz.localize(datetime(2025, 11, 22, 12, 0))
        shift_type, anchor = _get_shift_type_and_anchor_date(dt)
        assert shift_type == "day"


class TestGetCycleDayIndex:
    """_get_cycle_day_index function tests"""

    def test_import(self):
        """Import function"""
        from app.utils.shifts import _get_cycle_day_index
        assert callable(_get_cycle_day_index)

    def test_cycle_start_date_is_day_0(self):
        """CYCLE_START_DATE (2025-11-22) is day 0"""
        from app.utils.shifts import _get_cycle_day_index, CYCLE_START_DATE
        result = _get_cycle_day_index(CYCLE_START_DATE)
        assert result == 0

    def test_day_1(self):
        """Day after start is day 1"""
        from app.utils.shifts import _get_cycle_day_index
        result = _get_cycle_day_index(date(2025, 11, 23))
        assert result == 1

    def test_day_6_end_of_segment_0(self):
        """Day 6 is end of segment 0"""
        from app.utils.shifts import _get_cycle_day_index
        result = _get_cycle_day_index(date(2025, 11, 28))
        assert result == 6

    def test_day_7_start_of_segment_1(self):
        """Day 7 is start of segment 1"""
        from app.utils.shifts import _get_cycle_day_index
        result = _get_cycle_day_index(date(2025, 11, 29))
        assert result == 7

    def test_day_20_end_of_cycle(self):
        """Day 20 is end of 21-day cycle"""
        from app.utils.shifts import _get_cycle_day_index
        result = _get_cycle_day_index(date(2025, 12, 12))
        assert result == 20

    def test_day_21_wraps_to_0(self):
        """Day 21 wraps to day 0"""
        from app.utils.shifts import _get_cycle_day_index
        result = _get_cycle_day_index(date(2025, 12, 13))
        assert result == 0

    def test_negative_days_before_start(self):
        """Days before start date wrap correctly"""
        from app.utils.shifts import _get_cycle_day_index
        result = _get_cycle_day_index(date(2025, 11, 21))
        # -1 mod 21 = 20
        assert result == 20

    def test_multiple_cycles(self):
        """Multiple full cycles later"""
        from app.utils.shifts import _get_cycle_day_index
        # 42 days later (2 full cycles)
        result = _get_cycle_day_index(date(2026, 1, 3))
        assert result == 0


class TestGetTeamForSegment:
    """_get_team_for_segment function tests"""

    def test_import(self):
        """Import function"""
        from app.utils.shifts import _get_team_for_segment
        assert callable(_get_team_for_segment)

    # Segment 0 tests
    def test_segment_0_day_is_team_a(self):
        """Segment 0 day shift is Team A"""
        from app.utils.shifts import _get_team_for_segment
        assert _get_team_for_segment(0, "day") == "A"

    def test_segment_0_night_is_team_b(self):
        """Segment 0 night shift is Team B"""
        from app.utils.shifts import _get_team_for_segment
        assert _get_team_for_segment(0, "night") == "B"

    # Segment 1 tests
    def test_segment_1_day_is_team_c(self):
        """Segment 1 day shift is Team C"""
        from app.utils.shifts import _get_team_for_segment
        assert _get_team_for_segment(1, "day") == "C"

    def test_segment_1_night_is_team_a(self):
        """Segment 1 night shift is Team A"""
        from app.utils.shifts import _get_team_for_segment
        assert _get_team_for_segment(1, "night") == "A"

    # Segment 2 tests
    def test_segment_2_day_is_team_b(self):
        """Segment 2 day shift is Team B"""
        from app.utils.shifts import _get_team_for_segment
        assert _get_team_for_segment(2, "day") == "B"

    def test_segment_2_night_is_team_c(self):
        """Segment 2 night shift is Team C"""
        from app.utils.shifts import _get_team_for_segment
        assert _get_team_for_segment(2, "night") == "C"

    def test_all_segments_cover_all_teams(self):
        """All segments and shifts cover all teams"""
        from app.utils.shifts import _get_team_for_segment
        day_teams = {_get_team_for_segment(i, "day") for i in range(3)}
        night_teams = {_get_team_for_segment(i, "night") for i in range(3)}
        assert day_teams == {"A", "B", "C"}
        assert night_teams == {"A", "B", "C"}


class TestComputeShiftStartEnd:
    """_compute_shift_start_end function tests"""

    def test_import(self):
        """Import function"""
        from app.utils.shifts import _compute_shift_start_end
        assert callable(_compute_shift_start_end)

    def test_day_shift_start(self):
        """Day shift starts at 07:01"""
        from app.utils.shifts import _compute_shift_start_end
        start, end = _compute_shift_start_end(date(2025, 11, 22), "day")
        assert start == datetime(2025, 11, 22, 7, 1)

    def test_day_shift_end(self):
        """Day shift ends at 19:00"""
        from app.utils.shifts import _compute_shift_start_end
        start, end = _compute_shift_start_end(date(2025, 11, 22), "day")
        assert end == datetime(2025, 11, 22, 19, 0)

    def test_day_shift_same_day(self):
        """Day shift start and end are same day"""
        from app.utils.shifts import _compute_shift_start_end
        start, end = _compute_shift_start_end(date(2025, 11, 22), "day")
        assert start.date() == end.date()

    def test_night_shift_start(self):
        """Night shift starts at 19:01"""
        from app.utils.shifts import _compute_shift_start_end
        start, end = _compute_shift_start_end(date(2025, 11, 22), "night")
        assert start == datetime(2025, 11, 22, 19, 1)

    def test_night_shift_end(self):
        """Night shift ends at 07:00 next day"""
        from app.utils.shifts import _compute_shift_start_end
        start, end = _compute_shift_start_end(date(2025, 11, 22), "night")
        assert end == datetime(2025, 11, 23, 7, 0)

    def test_night_shift_crosses_midnight(self):
        """Night shift end is next day"""
        from app.utils.shifts import _compute_shift_start_end
        start, end = _compute_shift_start_end(date(2025, 11, 22), "night")
        assert end.date() == date(2025, 11, 23)

    def test_night_shift_duration(self):
        """Night shift is about 12 hours"""
        from app.utils.shifts import _compute_shift_start_end
        start, end = _compute_shift_start_end(date(2025, 11, 22), "night")
        duration = end - start
        # 19:01 to 07:00 = 11h 59m
        assert duration == timedelta(hours=11, minutes=59)


class TestGetShiftInfo:
    """get_shift_info main function tests"""

    def test_import(self):
        """Import function"""
        from app.utils.shifts import get_shift_info
        assert callable(get_shift_info)

    def test_returns_shift_info(self):
        """Returns ShiftInfo instance"""
        from app.utils.shifts import get_shift_info, ShiftInfo
        result = get_shift_info(datetime(2025, 11, 22, 12, 0))
        assert isinstance(result, ShiftInfo)

    def test_cycle_start_day_shift(self):
        """First day at noon - Team A day shift"""
        from app.utils.shifts import get_shift_info
        result = get_shift_info(datetime(2025, 11, 22, 12, 0))
        assert result.team == "A"
        assert result.shift_type == "day"
        assert result.anchor_date == date(2025, 11, 22)
        assert result.cycle_day_index == 0
        assert result.segment_index == 0

    def test_cycle_start_night_shift(self):
        """First day at night - Team B night shift"""
        from app.utils.shifts import get_shift_info
        result = get_shift_info(datetime(2025, 11, 22, 22, 0))
        assert result.team == "B"
        assert result.shift_type == "night"
        assert result.anchor_date == date(2025, 11, 22)

    def test_segment_1_day_shift(self):
        """Day 7 day shift - Team C"""
        from app.utils.shifts import get_shift_info
        result = get_shift_info(datetime(2025, 11, 29, 12, 0))
        assert result.team == "C"
        assert result.shift_type == "day"
        assert result.segment_index == 1

    def test_segment_1_night_shift(self):
        """Day 7 night shift - Team A"""
        from app.utils.shifts import get_shift_info
        result = get_shift_info(datetime(2025, 11, 29, 22, 0))
        assert result.team == "A"
        assert result.shift_type == "night"
        assert result.segment_index == 1

    def test_segment_2_day_shift(self):
        """Day 14 day shift - Team B"""
        from app.utils.shifts import get_shift_info
        result = get_shift_info(datetime(2025, 12, 6, 12, 0))
        assert result.team == "B"
        assert result.shift_type == "day"
        assert result.segment_index == 2

    def test_segment_2_night_shift(self):
        """Day 14 night shift - Team C"""
        from app.utils.shifts import get_shift_info
        result = get_shift_info(datetime(2025, 12, 6, 22, 0))
        assert result.team == "C"
        assert result.shift_type == "night"
        assert result.segment_index == 2

    def test_shift_start_end_populated(self):
        """Shift start and end are correctly populated"""
        from app.utils.shifts import get_shift_info
        result = get_shift_info(datetime(2025, 11, 22, 12, 0))
        assert result.shift_start == datetime(2025, 11, 22, 7, 1)
        assert result.shift_end == datetime(2025, 11, 22, 19, 0)

    def test_label_property(self):
        """Label property works"""
        from app.utils.shifts import get_shift_info
        result = get_shift_info(datetime(2025, 11, 22, 12, 0))
        assert result.label == "A-Өдөр"

    def test_early_morning_belongs_to_previous_day_shift(self):
        """02:00 on Nov 23 belongs to Nov 22 night shift"""
        from app.utils.shifts import get_shift_info
        result = get_shift_info(datetime(2025, 11, 23, 2, 0))
        assert result.shift_type == "night"
        assert result.anchor_date == date(2025, 11, 22)
        assert result.team == "B"  # Nov 22 night is Team B


class TestGet12HShiftCode:
    """get_12h_shift_code function tests (legacy)"""

    def test_import(self):
        """Import function"""
        from app.utils.shifts import get_12h_shift_code
        assert callable(get_12h_shift_code)

    def test_morning_7am_is_day(self):
        """07:00 is day shift"""
        from app.utils.shifts import get_12h_shift_code
        dt = datetime(2025, 1, 1, 7, 0)
        assert get_12h_shift_code(dt) == "_D"

    def test_afternoon_is_day(self):
        """15:00 is day shift"""
        from app.utils.shifts import get_12h_shift_code
        dt = datetime(2025, 1, 1, 15, 0)
        assert get_12h_shift_code(dt) == "_D"

    def test_evening_18_59_is_day(self):
        """18:59 is day shift"""
        from app.utils.shifts import get_12h_shift_code
        dt = datetime(2025, 1, 1, 18, 59)
        assert get_12h_shift_code(dt) == "_D"

    def test_evening_19_00_is_night(self):
        """19:00 is night shift"""
        from app.utils.shifts import get_12h_shift_code
        dt = datetime(2025, 1, 1, 19, 0)
        assert get_12h_shift_code(dt) == "_N"

    def test_night_22_00_is_night(self):
        """22:00 is night shift"""
        from app.utils.shifts import get_12h_shift_code
        dt = datetime(2025, 1, 1, 22, 0)
        assert get_12h_shift_code(dt) == "_N"

    def test_midnight_is_night(self):
        """00:00 is night shift"""
        from app.utils.shifts import get_12h_shift_code
        dt = datetime(2025, 1, 1, 0, 0)
        assert get_12h_shift_code(dt) == "_N"

    def test_early_morning_is_night(self):
        """06:00 is night shift"""
        from app.utils.shifts import get_12h_shift_code
        dt = datetime(2025, 1, 1, 6, 0)
        assert get_12h_shift_code(dt) == "_N"

    def test_boundary_6_59_is_night(self):
        """06:59 is night shift"""
        from app.utils.shifts import get_12h_shift_code
        dt = datetime(2025, 1, 1, 6, 59)
        assert get_12h_shift_code(dt) == "_N"


class TestGetQuarterCode:
    """get_quarter_code function tests (legacy)"""

    def test_import(self):
        """Import function"""
        from app.utils.shifts import get_quarter_code
        assert callable(get_quarter_code)

    def test_january_is_q1(self):
        """January is Q1"""
        from app.utils.shifts import get_quarter_code
        assert get_quarter_code(datetime(2025, 1, 15)) == "_Q1"

    def test_february_is_q1(self):
        """February is Q1"""
        from app.utils.shifts import get_quarter_code
        assert get_quarter_code(datetime(2025, 2, 15)) == "_Q1"

    def test_march_is_q1(self):
        """March is Q1"""
        from app.utils.shifts import get_quarter_code
        assert get_quarter_code(datetime(2025, 3, 15)) == "_Q1"

    def test_april_is_q2(self):
        """April is Q2"""
        from app.utils.shifts import get_quarter_code
        assert get_quarter_code(datetime(2025, 4, 15)) == "_Q2"

    def test_may_is_q2(self):
        """May is Q2"""
        from app.utils.shifts import get_quarter_code
        assert get_quarter_code(datetime(2025, 5, 15)) == "_Q2"

    def test_june_is_q2(self):
        """June is Q2"""
        from app.utils.shifts import get_quarter_code
        assert get_quarter_code(datetime(2025, 6, 15)) == "_Q2"

    def test_july_is_q3(self):
        """July is Q3"""
        from app.utils.shifts import get_quarter_code
        assert get_quarter_code(datetime(2025, 7, 1)) == "_Q3"

    def test_august_is_q3(self):
        """August is Q3"""
        from app.utils.shifts import get_quarter_code
        assert get_quarter_code(datetime(2025, 8, 15)) == "_Q3"

    def test_september_is_q3(self):
        """September is Q3"""
        from app.utils.shifts import get_quarter_code
        assert get_quarter_code(datetime(2025, 9, 15)) == "_Q3"

    def test_october_is_q4(self):
        """October is Q4"""
        from app.utils.shifts import get_quarter_code
        assert get_quarter_code(datetime(2025, 10, 15)) == "_Q4"

    def test_november_is_q4(self):
        """November is Q4"""
        from app.utils.shifts import get_quarter_code
        assert get_quarter_code(datetime(2025, 11, 15)) == "_Q4"

    def test_december_is_q4(self):
        """December is Q4"""
        from app.utils.shifts import get_quarter_code
        assert get_quarter_code(datetime(2025, 12, 15)) == "_Q4"

    def test_all_months_covered(self):
        """All 12 months have quarter codes"""
        from app.utils.shifts import get_quarter_code
        quarters = []
        for month in range(1, 13):
            dt = datetime(2025, month, 15)
            quarters.append(get_quarter_code(dt))
        assert quarters.count("_Q1") == 3
        assert quarters.count("_Q2") == 3
        assert quarters.count("_Q3") == 3
        assert quarters.count("_Q4") == 3


class TestGetShiftDate:
    """get_shift_date function tests (legacy)"""

    def test_import(self):
        """Import function"""
        from app.utils.shifts import get_shift_date
        assert callable(get_shift_date)

    def test_afternoon_returns_same_day(self):
        """08:00 returns same day"""
        from app.utils.shifts import get_shift_date
        result = get_shift_date(datetime(2025, 12, 3, 8, 0))
        assert result == date(2025, 12, 3)

    def test_early_morning_returns_previous_day(self):
        """02:00 returns previous day"""
        from app.utils.shifts import get_shift_date
        result = get_shift_date(datetime(2025, 12, 3, 2, 0))
        assert result == date(2025, 12, 2)

    def test_midnight_returns_previous_day(self):
        """00:00 returns previous day"""
        from app.utils.shifts import get_shift_date
        result = get_shift_date(datetime(2025, 12, 3, 0, 0))
        assert result == date(2025, 12, 2)

    def test_7am_returns_previous_day(self):
        """07:00 returns previous day (before 07:01)"""
        from app.utils.shifts import get_shift_date
        result = get_shift_date(datetime(2025, 12, 3, 7, 0))
        assert result == date(2025, 12, 2)

    def test_7_01_returns_same_day(self):
        """07:01 returns same day"""
        from app.utils.shifts import get_shift_date
        result = get_shift_date(datetime(2025, 12, 3, 7, 1))
        assert result == date(2025, 12, 3)

    def test_none_uses_current_time(self):
        """None input uses current time"""
        from app.utils.shifts import get_shift_date
        with patch('app.utils.shifts.now_local') as mock_now:
            mock_now.return_value = datetime(2025, 12, 3, 12, 0)
            result = get_shift_date(None)
            assert result == date(2025, 12, 3)

    def test_evening_returns_same_day(self):
        """22:00 returns same day (night shift starts)"""
        from app.utils.shifts import get_shift_date
        result = get_shift_date(datetime(2025, 12, 3, 22, 0))
        assert result == date(2025, 12, 3)


class TestGetCurrentShiftStart:
    """get_current_shift_start function tests (legacy)"""

    def test_import(self):
        """Import function"""
        from app.utils.shifts import get_current_shift_start
        assert callable(get_current_shift_start)

    def test_afternoon_returns_today_8am(self):
        """14:00 returns today's 08:00"""
        from app.utils.shifts import get_current_shift_start
        result = get_current_shift_start(datetime(2025, 1, 15, 14, 0))
        assert result == datetime(2025, 1, 15, 8, 0)

    def test_early_morning_returns_yesterday_8am(self):
        """02:00 returns yesterday's 08:00"""
        from app.utils.shifts import get_current_shift_start
        result = get_current_shift_start(datetime(2025, 1, 15, 2, 0))
        assert result == datetime(2025, 1, 14, 8, 0)

    def test_exactly_8am_returns_today(self):
        """08:00 exactly returns today's 08:00"""
        from app.utils.shifts import get_current_shift_start
        result = get_current_shift_start(datetime(2025, 1, 15, 8, 0))
        assert result == datetime(2025, 1, 15, 8, 0)

    def test_7_59_returns_yesterday(self):
        """07:59 returns yesterday's 08:00"""
        from app.utils.shifts import get_current_shift_start
        result = get_current_shift_start(datetime(2025, 1, 15, 7, 59))
        assert result == datetime(2025, 1, 14, 8, 0)

    def test_midnight_returns_yesterday(self):
        """00:00 returns yesterday's 08:00"""
        from app.utils.shifts import get_current_shift_start
        result = get_current_shift_start(datetime(2025, 1, 15, 0, 0))
        assert result == datetime(2025, 1, 14, 8, 0)

    def test_late_night_returns_same_day(self):
        """23:00 returns same day's 08:00"""
        from app.utils.shifts import get_current_shift_start
        result = get_current_shift_start(datetime(2025, 1, 15, 23, 0))
        assert result == datetime(2025, 1, 15, 8, 0)


class TestShiftCycleIntegration:
    """Integration tests for shift cycle"""

    def test_full_cycle_team_a_rotation(self):
        """Team A rotates: Day -> Night -> Off"""
        from app.utils.shifts import get_shift_info

        # Day 0: A is Day
        info = get_shift_info(datetime(2025, 11, 22, 12, 0))
        assert info.team == "A"
        assert info.shift_type == "day"

        # Day 7: A is Night
        info = get_shift_info(datetime(2025, 11, 29, 22, 0))
        assert info.team == "A"
        assert info.shift_type == "night"

        # Day 14: A is Off (not A in Day or Night)
        info_day = get_shift_info(datetime(2025, 12, 6, 12, 0))
        info_night = get_shift_info(datetime(2025, 12, 6, 22, 0))
        assert info_day.team != "A"  # B is Day
        assert info_night.team != "A"  # C is Night

    def test_all_teams_work_each_segment(self):
        """Each segment has all teams working"""
        from app.utils.shifts import get_shift_info

        # Segment 0
        day0_day = get_shift_info(datetime(2025, 11, 22, 12, 0))
        day0_night = get_shift_info(datetime(2025, 11, 22, 22, 0))
        assert {day0_day.team, day0_night.team} == {"A", "B"}

        # Segment 1
        day7_day = get_shift_info(datetime(2025, 11, 29, 12, 0))
        day7_night = get_shift_info(datetime(2025, 11, 29, 22, 0))
        assert {day7_day.team, day7_night.team} == {"C", "A"}

        # Segment 2
        day14_day = get_shift_info(datetime(2025, 12, 6, 12, 0))
        day14_night = get_shift_info(datetime(2025, 12, 6, 22, 0))
        assert {day14_day.team, day14_night.team} == {"B", "C"}

    def test_cycle_repeats_after_21_days(self):
        """Cycle repeats after 21 days"""
        from app.utils.shifts import get_shift_info

        # Day 0
        info_day0 = get_shift_info(datetime(2025, 11, 22, 12, 0))

        # Day 21 (one full cycle later)
        info_day21 = get_shift_info(datetime(2025, 12, 13, 12, 0))

        assert info_day0.team == info_day21.team
        assert info_day0.shift_type == info_day21.shift_type

    def test_year_boundary_works(self):
        """Shift calculation works across year boundary"""
        from app.utils.shifts import get_shift_info

        # Late December 2025
        info_dec = get_shift_info(datetime(2025, 12, 31, 12, 0))
        assert info_dec.team in ["A", "B", "C"]

        # Early January 2026
        info_jan = get_shift_info(datetime(2026, 1, 1, 12, 0))
        assert info_jan.team in ["A", "B", "C"]


class TestEdgeCases:
    """Edge case tests"""

    def test_exactly_midnight_boundary(self):
        """Midnight exactly belongs to previous day's night shift"""
        from app.utils.shifts import _get_shift_type_and_anchor_date
        shift_type, anchor = _get_shift_type_and_anchor_date(datetime(2025, 11, 23, 0, 0, 0))
        assert shift_type == "night"
        assert anchor == date(2025, 11, 22)

    def test_shift_info_is_dataclass(self):
        """ShiftInfo is a proper dataclass"""
        from app.utils.shifts import ShiftInfo
        from dataclasses import is_dataclass
        assert is_dataclass(ShiftInfo)

    def test_very_old_date(self):
        """Very old date still calculates"""
        from app.utils.shifts import get_shift_info
        result = get_shift_info(datetime(2020, 1, 1, 12, 0))
        assert result.team in ["A", "B", "C"]

    def test_future_date(self):
        """Future date calculates correctly"""
        from app.utils.shifts import get_shift_info
        result = get_shift_info(datetime(2030, 6, 15, 12, 0))
        assert result.team in ["A", "B", "C"]

    def test_leap_year_handling(self):
        """Leap year dates work correctly"""
        from app.utils.shifts import get_shift_info
        # Feb 29, 2028 is a leap year
        result = get_shift_info(datetime(2028, 2, 29, 12, 0))
        assert result.team in ["A", "B", "C"]

    def test_12h_shift_code_with_seconds(self):
        """12h shift code ignores seconds"""
        from app.utils.shifts import get_12h_shift_code
        dt = datetime(2025, 1, 1, 7, 0, 59)
        assert get_12h_shift_code(dt) == "_D"

    def test_quarter_code_first_day_of_month(self):
        """Quarter code for first day of month"""
        from app.utils.shifts import get_quarter_code
        assert get_quarter_code(datetime(2025, 1, 1)) == "_Q1"
        assert get_quarter_code(datetime(2025, 4, 1)) == "_Q2"
        assert get_quarter_code(datetime(2025, 7, 1)) == "_Q3"
        assert get_quarter_code(datetime(2025, 10, 1)) == "_Q4"

    def test_quarter_code_last_day_of_quarter(self):
        """Quarter code for last day of quarter"""
        from app.utils.shifts import get_quarter_code
        assert get_quarter_code(datetime(2025, 3, 31)) == "_Q1"
        assert get_quarter_code(datetime(2025, 6, 30)) == "_Q2"
        assert get_quarter_code(datetime(2025, 9, 30)) == "_Q3"
        assert get_quarter_code(datetime(2025, 12, 31)) == "_Q4"

