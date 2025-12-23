# tests/unit/test_routes_helpers.py
# -*- coding: utf-8 -*-
"""
Routes helper functions tests
"""
import pytest
from unittest.mock import Mock, patch
from datetime import datetime
from app.routes.main.helpers import get_12h_shift_code, get_quarter_code


class TestGet12hShiftCode:
    """get_12h_shift_code() функцийн тестүүд"""

    def test_returns_string(self):
        """Should return a string"""
        dt = datetime(2025, 1, 15, 12, 0)
        result = get_12h_shift_code(dt)
        assert isinstance(result, str)

    def test_day_shift_morning(self):
        """7 AM should be day shift"""
        dt = datetime(2025, 1, 15, 7, 0)
        result = get_12h_shift_code(dt)
        assert result == "_D"

    def test_day_shift_afternoon(self):
        """3 PM should be day shift"""
        dt = datetime(2025, 1, 15, 15, 0)
        result = get_12h_shift_code(dt)
        assert result == "_D"

    def test_night_shift_evening(self):
        """7 PM should be night shift"""
        dt = datetime(2025, 1, 15, 19, 0)
        result = get_12h_shift_code(dt)
        assert result == "_N"

    def test_night_shift_midnight(self):
        """Midnight should be night shift"""
        dt = datetime(2025, 1, 15, 0, 0)
        result = get_12h_shift_code(dt)
        assert result == "_N"

    def test_night_shift_early_morning(self):
        """6 AM should be night shift"""
        dt = datetime(2025, 1, 15, 6, 0)
        result = get_12h_shift_code(dt)
        assert result == "_N"


class TestGetQuarterCode:
    """get_quarter_code() функцийн тестүүд"""

    def test_q1_january(self):
        """January should be Q1"""
        from datetime import date
        result = get_quarter_code(date(2025, 1, 15))
        assert "Q1" in result or "1" in result

    def test_q2_april(self):
        """April should be Q2"""
        from datetime import date
        result = get_quarter_code(date(2025, 4, 15))
        assert "Q2" in result or "2" in result

    def test_q3_july(self):
        """July should be Q3"""
        from datetime import date
        result = get_quarter_code(date(2025, 7, 15))
        assert "Q3" in result or "3" in result

    def test_q4_october(self):
        """October should be Q4"""
        from datetime import date
        result = get_quarter_code(date(2025, 10, 15))
        assert "Q4" in result or "4" in result
