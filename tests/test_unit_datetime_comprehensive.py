# tests/unit/test_datetime_comprehensive.py
# -*- coding: utf-8 -*-
"""
Datetime utility comprehensive tests
"""
import pytest
from datetime import datetime
from app.utils.datetime import now_local


class TestNowLocal:
    """now_local() функцийн тестүүд"""

    def test_returns_datetime(self):
        """Should return a datetime object"""
        result = now_local()
        assert isinstance(result, datetime)

    def test_returns_current_year(self):
        """Should return current year"""
        result = now_local()
        assert result.year == datetime.now().year

    def test_returns_current_month(self):
        """Should return current month"""
        result = now_local()
        assert result.month == datetime.now().month

    def test_returns_current_day(self):
        """Should return current day"""
        result = now_local()
        assert result.day == datetime.now().day

    def test_successive_calls_increase(self):
        """Successive calls should return increasing times"""
        import time
        t1 = now_local()
        time.sleep(0.01)
        t2 = now_local()
        assert t2 >= t1
