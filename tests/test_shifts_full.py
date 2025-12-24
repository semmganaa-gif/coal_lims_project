# tests/test_shifts_full.py
# -*- coding: utf-8 -*-
"""
Complete tests for app/utils/shifts.py - targeting 100% coverage.
"""

import pytest
from datetime import datetime, date, time, timedelta


class TestShiftInfo:
    """Tests for ShiftInfo dataclass."""

    def test_create_shift_info(self, app):
        """Test creating ShiftInfo object."""
        with app.app_context():
            from app.utils.shifts import ShiftInfo
            info = ShiftInfo(
                team='A',
                shift_type='day',
                anchor_date=date(2025, 12, 25),
                cycle_day_index=0,
                segment_index=0,
                shift_start=datetime(2025, 12, 25, 7, 1),
                shift_end=datetime(2025, 12, 25, 19, 0)
            )
            assert info.team == 'A'
            assert info.shift_type == 'day'

    def test_label_day(self, app):
        """Test label property for day shift."""
        with app.app_context():
            from app.utils.shifts import ShiftInfo
            info = ShiftInfo(
                team='A',
                shift_type='day',
                anchor_date=date(2025, 12, 25),
                cycle_day_index=0,
                segment_index=0,
                shift_start=datetime(2025, 12, 25, 7, 1),
                shift_end=datetime(2025, 12, 25, 19, 0)
            )
            assert info.label == 'A-Өдөр'

    def test_label_night(self, app):
        """Test label property for night shift."""
        with app.app_context():
            from app.utils.shifts import ShiftInfo
            info = ShiftInfo(
                team='B',
                shift_type='night',
                anchor_date=date(2025, 12, 25),
                cycle_day_index=0,
                segment_index=0,
                shift_start=datetime(2025, 12, 25, 19, 1),
                shift_end=datetime(2025, 12, 26, 7, 0)
            )
            assert info.label == 'B-Шөнө'


class TestGetShiftTypeAndAnchorDate:
    """Tests for _get_shift_type_and_anchor_date function."""

    def test_day_shift_morning(self, app):
        """Test morning time returns day shift."""
        with app.app_context():
            from app.utils.shifts import _get_shift_type_and_anchor_date
            dt = datetime(2025, 12, 25, 8, 0)
            shift_type, anchor = _get_shift_type_and_anchor_date(dt)
            assert shift_type == 'day'
            assert anchor == date(2025, 12, 25)

    def test_day_shift_afternoon(self, app):
        """Test afternoon time returns day shift."""
        with app.app_context():
            from app.utils.shifts import _get_shift_type_and_anchor_date
            dt = datetime(2025, 12, 25, 15, 30)
            shift_type, anchor = _get_shift_type_and_anchor_date(dt)
            assert shift_type == 'day'
            assert anchor == date(2025, 12, 25)

    def test_day_shift_boundary_start(self, app):
        """Test exactly at day shift start (07:01)."""
        with app.app_context():
            from app.utils.shifts import _get_shift_type_and_anchor_date
            dt = datetime(2025, 12, 25, 7, 1)
            shift_type, anchor = _get_shift_type_and_anchor_date(dt)
            assert shift_type == 'day'

    def test_day_shift_boundary_end(self, app):
        """Test exactly at day shift end (19:00)."""
        with app.app_context():
            from app.utils.shifts import _get_shift_type_and_anchor_date
            dt = datetime(2025, 12, 25, 19, 0)
            shift_type, anchor = _get_shift_type_and_anchor_date(dt)
            assert shift_type == 'day'

    def test_night_shift_evening(self, app):
        """Test evening time returns night shift."""
        with app.app_context():
            from app.utils.shifts import _get_shift_type_and_anchor_date
            dt = datetime(2025, 12, 25, 21, 0)
            shift_type, anchor = _get_shift_type_and_anchor_date(dt)
            assert shift_type == 'night'
            assert anchor == date(2025, 12, 25)

    def test_night_shift_early_morning(self, app):
        """Test early morning (before 07:01) returns night shift."""
        with app.app_context():
            from app.utils.shifts import _get_shift_type_and_anchor_date
            dt = datetime(2025, 12, 25, 3, 0)
            shift_type, anchor = _get_shift_type_and_anchor_date(dt)
            assert shift_type == 'night'
            assert anchor == date(2025, 12, 24)  # Previous day

    def test_night_shift_midnight(self, app):
        """Test midnight returns night shift."""
        with app.app_context():
            from app.utils.shifts import _get_shift_type_and_anchor_date
            dt = datetime(2025, 12, 25, 0, 0)
            shift_type, anchor = _get_shift_type_and_anchor_date(dt)
            assert shift_type == 'night'
            assert anchor == date(2025, 12, 24)

    def test_with_timezone_aware_datetime(self, app):
        """Test with timezone-aware datetime."""
        with app.app_context():
            from app.utils.shifts import _get_shift_type_and_anchor_date
            import pytz
            tz = pytz.timezone('Asia/Ulaanbaatar')
            dt = tz.localize(datetime(2025, 12, 25, 10, 0))
            shift_type, anchor = _get_shift_type_and_anchor_date(dt)
            assert shift_type == 'day'


class TestGetCycleDayIndex:
    """Tests for _get_cycle_day_index function."""

    def test_cycle_start_date(self, app):
        """Test index at cycle start date."""
        with app.app_context():
            from app.utils.shifts import _get_cycle_day_index, CYCLE_START_DATE
            result = _get_cycle_day_index(CYCLE_START_DATE)
            assert result == 0

    def test_day_after_start(self, app):
        """Test index day after start."""
        with app.app_context():
            from app.utils.shifts import _get_cycle_day_index, CYCLE_START_DATE
            result = _get_cycle_day_index(CYCLE_START_DATE + timedelta(days=1))
            assert result == 1

    def test_cycle_wraps_at_21(self, app):
        """Test cycle wraps at 21 days."""
        with app.app_context():
            from app.utils.shifts import _get_cycle_day_index, CYCLE_START_DATE
            result = _get_cycle_day_index(CYCLE_START_DATE + timedelta(days=21))
            assert result == 0

    def test_cycle_wraps_at_42(self, app):
        """Test cycle wraps at 42 days."""
        with app.app_context():
            from app.utils.shifts import _get_cycle_day_index, CYCLE_START_DATE
            result = _get_cycle_day_index(CYCLE_START_DATE + timedelta(days=42))
            assert result == 0

    def test_all_indices_in_cycle(self, app):
        """Test all indices 0-20 in cycle."""
        with app.app_context():
            from app.utils.shifts import _get_cycle_day_index, CYCLE_START_DATE
            for i in range(21):
                result = _get_cycle_day_index(CYCLE_START_DATE + timedelta(days=i))
                assert result == i


class TestGetTeamForSegment:
    """Tests for _get_team_for_segment function."""

    def test_segment_0_day(self, app):
        """Test segment 0 day shift returns A."""
        with app.app_context():
            from app.utils.shifts import _get_team_for_segment
            result = _get_team_for_segment(0, 'day')
            assert result == 'A'

    def test_segment_0_night(self, app):
        """Test segment 0 night shift returns B."""
        with app.app_context():
            from app.utils.shifts import _get_team_for_segment
            result = _get_team_for_segment(0, 'night')
            assert result == 'B'

    def test_segment_1_day(self, app):
        """Test segment 1 day shift returns C."""
        with app.app_context():
            from app.utils.shifts import _get_team_for_segment
            result = _get_team_for_segment(1, 'day')
            assert result == 'C'

    def test_segment_1_night(self, app):
        """Test segment 1 night shift returns A."""
        with app.app_context():
            from app.utils.shifts import _get_team_for_segment
            result = _get_team_for_segment(1, 'night')
            assert result == 'A'

    def test_segment_2_day(self, app):
        """Test segment 2 day shift returns B."""
        with app.app_context():
            from app.utils.shifts import _get_team_for_segment
            result = _get_team_for_segment(2, 'day')
            assert result == 'B'

    def test_segment_2_night(self, app):
        """Test segment 2 night shift returns C."""
        with app.app_context():
            from app.utils.shifts import _get_team_for_segment
            result = _get_team_for_segment(2, 'night')
            assert result == 'C'


class TestComputeShiftStartEnd:
    """Tests for _compute_shift_start_end function."""

    def test_day_shift(self, app):
        """Test day shift start and end times."""
        with app.app_context():
            from app.utils.shifts import _compute_shift_start_end
            anchor = date(2025, 12, 25)
            start, end = _compute_shift_start_end(anchor, 'day')
            assert start == datetime(2025, 12, 25, 7, 1)
            assert end == datetime(2025, 12, 25, 19, 0)

    def test_night_shift(self, app):
        """Test night shift start and end times."""
        with app.app_context():
            from app.utils.shifts import _compute_shift_start_end
            anchor = date(2025, 12, 25)
            start, end = _compute_shift_start_end(anchor, 'night')
            assert start == datetime(2025, 12, 25, 19, 1)
            assert end == datetime(2025, 12, 26, 7, 0)


class TestGetShiftInfo:
    """Tests for get_shift_info function."""

    def test_day_shift(self, app):
        """Test get_shift_info for day shift."""
        with app.app_context():
            from app.utils.shifts import get_shift_info
            dt = datetime(2025, 12, 25, 10, 0)
            info = get_shift_info(dt)
            assert info.shift_type == 'day'
            assert info.team in ['A', 'B', 'C']

    def test_night_shift(self, app):
        """Test get_shift_info for night shift."""
        with app.app_context():
            from app.utils.shifts import get_shift_info
            dt = datetime(2025, 12, 25, 22, 0)
            info = get_shift_info(dt)
            assert info.shift_type == 'night'

    def test_all_properties_set(self, app):
        """Test all properties are set."""
        with app.app_context():
            from app.utils.shifts import get_shift_info
            dt = datetime(2025, 12, 25, 10, 0)
            info = get_shift_info(dt)
            assert info.team is not None
            assert info.shift_type is not None
            assert info.anchor_date is not None
            assert info.cycle_day_index is not None
            assert info.segment_index is not None
            assert info.shift_start is not None
            assert info.shift_end is not None


class TestGet12hShiftCode:
    """Tests for get_12h_shift_code function."""

    def test_morning_day(self, app):
        """Test morning (08:00) returns day."""
        with app.app_context():
            from app.utils.shifts import get_12h_shift_code
            dt = datetime(2025, 12, 25, 8, 0)
            assert get_12h_shift_code(dt) == '_D'

    def test_afternoon_day(self, app):
        """Test afternoon (15:00) returns day."""
        with app.app_context():
            from app.utils.shifts import get_12h_shift_code
            dt = datetime(2025, 12, 25, 15, 0)
            assert get_12h_shift_code(dt) == '_D'

    def test_evening_night(self, app):
        """Test evening (20:00) returns night."""
        with app.app_context():
            from app.utils.shifts import get_12h_shift_code
            dt = datetime(2025, 12, 25, 20, 0)
            assert get_12h_shift_code(dt) == '_N'

    def test_midnight_night(self, app):
        """Test midnight returns night."""
        with app.app_context():
            from app.utils.shifts import get_12h_shift_code
            dt = datetime(2025, 12, 25, 0, 0)
            assert get_12h_shift_code(dt) == '_N'

    def test_boundary_7am_day(self, app):
        """Test exactly 7am returns day."""
        with app.app_context():
            from app.utils.shifts import get_12h_shift_code
            dt = datetime(2025, 12, 25, 7, 0)
            assert get_12h_shift_code(dt) == '_D'

    def test_boundary_19pm_night(self, app):
        """Test exactly 19:00 returns night."""
        with app.app_context():
            from app.utils.shifts import get_12h_shift_code
            dt = datetime(2025, 12, 25, 19, 0)
            assert get_12h_shift_code(dt) == '_N'


class TestGetQuarterCode:
    """Tests for get_quarter_code function."""

    def test_q1_january(self, app):
        """Test January returns Q1."""
        with app.app_context():
            from app.utils.shifts import get_quarter_code
            dt = datetime(2025, 1, 15)
            assert get_quarter_code(dt) == '_Q1'

    def test_q1_march(self, app):
        """Test March returns Q1."""
        with app.app_context():
            from app.utils.shifts import get_quarter_code
            dt = datetime(2025, 3, 31)
            assert get_quarter_code(dt) == '_Q1'

    def test_q2_april(self, app):
        """Test April returns Q2."""
        with app.app_context():
            from app.utils.shifts import get_quarter_code
            dt = datetime(2025, 4, 1)
            assert get_quarter_code(dt) == '_Q2'

    def test_q2_june(self, app):
        """Test June returns Q2."""
        with app.app_context():
            from app.utils.shifts import get_quarter_code
            dt = datetime(2025, 6, 30)
            assert get_quarter_code(dt) == '_Q2'

    def test_q3_july(self, app):
        """Test July returns Q3."""
        with app.app_context():
            from app.utils.shifts import get_quarter_code
            dt = datetime(2025, 7, 1)
            assert get_quarter_code(dt) == '_Q3'

    def test_q3_september(self, app):
        """Test September returns Q3."""
        with app.app_context():
            from app.utils.shifts import get_quarter_code
            dt = datetime(2025, 9, 30)
            assert get_quarter_code(dt) == '_Q3'

    def test_q4_october(self, app):
        """Test October returns Q4."""
        with app.app_context():
            from app.utils.shifts import get_quarter_code
            dt = datetime(2025, 10, 1)
            assert get_quarter_code(dt) == '_Q4'

    def test_q4_december(self, app):
        """Test December returns Q4."""
        with app.app_context():
            from app.utils.shifts import get_quarter_code
            dt = datetime(2025, 12, 31)
            assert get_quarter_code(dt) == '_Q4'


class TestGetShiftDate:
    """Tests for get_shift_date function."""

    def test_day_shift(self, app):
        """Test day shift returns same date."""
        with app.app_context():
            from app.utils.shifts import get_shift_date
            dt = datetime(2025, 12, 25, 10, 0)
            result = get_shift_date(dt)
            assert result == date(2025, 12, 25)

    def test_night_shift_evening(self, app):
        """Test night shift evening returns same date."""
        with app.app_context():
            from app.utils.shifts import get_shift_date
            dt = datetime(2025, 12, 25, 21, 0)
            result = get_shift_date(dt)
            assert result == date(2025, 12, 25)

    def test_night_shift_early_morning(self, app):
        """Test night shift early morning returns previous date."""
        with app.app_context():
            from app.utils.shifts import get_shift_date
            dt = datetime(2025, 12, 25, 3, 0)
            result = get_shift_date(dt)
            assert result == date(2025, 12, 24)

    def test_default_now(self, app):
        """Test default uses current time."""
        with app.app_context():
            from app.utils.shifts import get_shift_date
            result = get_shift_date()  # No argument
            assert isinstance(result, date)


class TestGetCurrentShiftStart:
    """Tests for get_current_shift_start function."""

    def test_afternoon(self, app):
        """Test afternoon returns same day 08:00."""
        with app.app_context():
            from app.utils.shifts import get_current_shift_start
            dt = datetime(2025, 12, 25, 14, 0)
            result = get_current_shift_start(dt)
            assert result == datetime(2025, 12, 25, 8, 0)

    def test_early_morning(self, app):
        """Test early morning returns previous day 08:00."""
        with app.app_context():
            from app.utils.shifts import get_current_shift_start
            dt = datetime(2025, 12, 25, 2, 0)
            result = get_current_shift_start(dt)
            assert result == datetime(2025, 12, 24, 8, 0)

    def test_exactly_8am(self, app):
        """Test exactly 08:00 returns same day 08:00."""
        with app.app_context():
            from app.utils.shifts import get_current_shift_start
            dt = datetime(2025, 12, 25, 8, 0)
            result = get_current_shift_start(dt)
            assert result == datetime(2025, 12, 25, 8, 0)

    def test_just_before_8am(self, app):
        """Test 07:59 returns previous day 08:00."""
        with app.app_context():
            from app.utils.shifts import get_current_shift_start
            dt = datetime(2025, 12, 25, 7, 59)
            result = get_current_shift_start(dt)
            assert result == datetime(2025, 12, 24, 8, 0)


class TestConstants:
    """Tests for module constants."""

    def test_cycle_start_date(self, app):
        """Test CYCLE_START_DATE is a date."""
        with app.app_context():
            from app.utils.shifts import CYCLE_START_DATE
            assert isinstance(CYCLE_START_DATE, date)

    def test_day_start(self, app):
        """Test DAY_START is 07:01."""
        with app.app_context():
            from app.utils.shifts import DAY_START
            assert DAY_START == time(7, 1)

    def test_day_end(self, app):
        """Test DAY_END is 19:00."""
        with app.app_context():
            from app.utils.shifts import DAY_END
            assert DAY_END == time(19, 0)
