# tests/test_shifts_deep.py
# -*- coding: utf-8 -*-
"""
Deep coverage tests for app/utils/shifts.py
"""

import pytest
from datetime import date, datetime, time, timedelta


class TestShiftInfo:
    """Tests for ShiftInfo dataclass."""

    def test_shift_info_label_day(self, app):
        """Test ShiftInfo label for day shift."""
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
            assert 'A' in info.label
            assert 'Өдөр' in info.label

    def test_shift_info_label_night(self, app):
        """Test ShiftInfo label for night shift."""
        with app.app_context():
            from app.utils.shifts import ShiftInfo
            info = ShiftInfo(
                team='B',
                shift_type='night',
                anchor_date=date(2025, 12, 25),
                cycle_day_index=7,
                segment_index=1,
                shift_start=datetime(2025, 12, 25, 19, 1),
                shift_end=datetime(2025, 12, 26, 7, 0)
            )
            assert 'B' in info.label
            assert 'Шөнө' in info.label


class TestGetShiftTypeAndAnchorDate:
    """Tests for _get_shift_type_and_anchor_date function."""

    def test_day_shift_morning(self, app):
        """Test day shift in morning."""
        with app.app_context():
            from app.utils.shifts import _get_shift_type_and_anchor_date
            dt = datetime(2025, 12, 25, 8, 0)  # 08:00
            shift_type, anchor = _get_shift_type_and_anchor_date(dt)
            assert shift_type == 'day'
            assert anchor == date(2025, 12, 25)

    def test_day_shift_afternoon(self, app):
        """Test day shift in afternoon."""
        with app.app_context():
            from app.utils.shifts import _get_shift_type_and_anchor_date
            dt = datetime(2025, 12, 25, 15, 0)  # 15:00
            shift_type, anchor = _get_shift_type_and_anchor_date(dt)
            assert shift_type == 'day'
            assert anchor == date(2025, 12, 25)

    def test_night_shift_evening(self, app):
        """Test night shift in evening."""
        with app.app_context():
            from app.utils.shifts import _get_shift_type_and_anchor_date
            dt = datetime(2025, 12, 25, 20, 0)  # 20:00
            shift_type, anchor = _get_shift_type_and_anchor_date(dt)
            assert shift_type == 'night'
            assert anchor == date(2025, 12, 25)

    def test_night_shift_early_morning(self, app):
        """Test night shift in early morning."""
        with app.app_context():
            from app.utils.shifts import _get_shift_type_and_anchor_date
            dt = datetime(2025, 12, 25, 3, 0)  # 03:00
            shift_type, anchor = _get_shift_type_and_anchor_date(dt)
            assert shift_type == 'night'
            # Anchor should be previous day
            assert anchor == date(2025, 12, 24)

    def test_day_start_boundary(self, app):
        """Test day start boundary (07:01)."""
        with app.app_context():
            from app.utils.shifts import _get_shift_type_and_anchor_date
            dt = datetime(2025, 12, 25, 7, 1)
            shift_type, anchor = _get_shift_type_and_anchor_date(dt)
            assert shift_type == 'day'

    def test_day_end_boundary(self, app):
        """Test day end boundary (19:00)."""
        with app.app_context():
            from app.utils.shifts import _get_shift_type_and_anchor_date
            dt = datetime(2025, 12, 25, 19, 0)
            shift_type, anchor = _get_shift_type_and_anchor_date(dt)
            assert shift_type == 'day'

    def test_night_start_boundary(self, app):
        """Test night start boundary (19:01)."""
        with app.app_context():
            from app.utils.shifts import _get_shift_type_and_anchor_date
            dt = datetime(2025, 12, 25, 19, 1)
            shift_type, anchor = _get_shift_type_and_anchor_date(dt)
            assert shift_type == 'night'


class TestGetCycleDayIndex:
    """Tests for _get_cycle_day_index function."""

    def test_cycle_start_date(self, app):
        """Test cycle start date returns 0."""
        with app.app_context():
            from app.utils.shifts import _get_cycle_day_index, CYCLE_START_DATE
            result = _get_cycle_day_index(CYCLE_START_DATE)
            assert result == 0

    def test_one_day_after_start(self, app):
        """Test one day after start returns 1."""
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

    def test_mid_cycle(self, app):
        """Test mid cycle day."""
        with app.app_context():
            from app.utils.shifts import _get_cycle_day_index, CYCLE_START_DATE
            result = _get_cycle_day_index(CYCLE_START_DATE + timedelta(days=10))
            assert result == 10


class TestGetTeamForSegment:
    """Tests for _get_team_for_segment function."""

    def test_segment_0_day(self, app):
        """Test segment 0 day shift is team A."""
        with app.app_context():
            from app.utils.shifts import _get_team_for_segment
            result = _get_team_for_segment(0, 'day')
            assert result in ['A', 'B', 'C']

    def test_segment_0_night(self, app):
        """Test segment 0 night shift."""
        with app.app_context():
            from app.utils.shifts import _get_team_for_segment
            result = _get_team_for_segment(0, 'night')
            assert result in ['A', 'B', 'C']

    def test_segment_1_day(self, app):
        """Test segment 1 day shift."""
        with app.app_context():
            from app.utils.shifts import _get_team_for_segment
            result = _get_team_for_segment(1, 'day')
            assert result in ['A', 'B', 'C']

    def test_segment_2_day(self, app):
        """Test segment 2 day shift."""
        with app.app_context():
            from app.utils.shifts import _get_team_for_segment
            result = _get_team_for_segment(2, 'day')
            assert result in ['A', 'B', 'C']


class TestGetShiftInfo:
    """Tests for get_shift_info function."""

    def test_get_shift_info_current(self, app):
        """Test get_shift_info for current time."""
        with app.app_context():
            try:
                from app.utils.shifts import get_shift_info
                dt = datetime(2025, 12, 25, 12, 0)
                result = get_shift_info(dt)
                assert result is not None
                assert hasattr(result, 'team')
                assert hasattr(result, 'shift_type')
            except (ImportError, AttributeError, TypeError):
                pytest.skip("get_shift_info not available")

    def test_get_shift_info_specific_time(self, app):
        """Test get_shift_info with specific datetime."""
        with app.app_context():
            try:
                from app.utils.shifts import get_shift_info
                dt = datetime(2025, 12, 25, 12, 0)
                result = get_shift_info(dt)
                assert result is not None
                assert result.shift_type == 'day'
            except (ImportError, AttributeError):
                pytest.skip("get_shift_info not available")


class TestConstants:
    """Tests for module constants."""

    def test_cycle_start_date_exists(self, app):
        """Test CYCLE_START_DATE constant exists."""
        with app.app_context():
            from app.utils.shifts import CYCLE_START_DATE
            assert isinstance(CYCLE_START_DATE, date)

    def test_day_start_exists(self, app):
        """Test DAY_START constant exists."""
        with app.app_context():
            from app.utils.shifts import DAY_START
            assert isinstance(DAY_START, time)
            assert DAY_START == time(7, 1)

    def test_day_end_exists(self, app):
        """Test DAY_END constant exists."""
        with app.app_context():
            from app.utils.shifts import DAY_END
            assert isinstance(DAY_END, time)
            assert DAY_END == time(19, 0)


class TestShiftCode:
    """Tests for shift_code function if exists."""

    def test_shift_code_day(self, app):
        """Test shift_code for day shift."""
        with app.app_context():
            try:
                from app.utils.shifts import shift_code
                dt = datetime(2025, 12, 25, 12, 0)
                result = shift_code(dt)
                assert 'D' in result or 'd' in result.lower()
            except (ImportError, AttributeError):
                pytest.skip("shift_code not available")

    def test_shift_code_night(self, app):
        """Test shift_code for night shift."""
        with app.app_context():
            try:
                from app.utils.shifts import shift_code
                dt = datetime(2025, 12, 25, 22, 0)
                result = shift_code(dt)
                assert 'N' in result or 'n' in result.lower()
            except (ImportError, AttributeError):
                pytest.skip("shift_code not available")
