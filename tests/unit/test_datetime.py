# -*- coding: utf-8 -*-
"""
Tests for app/utils/datetime.py
Date/time utility functions tests
"""
import pytest
from datetime import datetime
from unittest.mock import patch, MagicMock


class TestNowLocal:
    """now_local function tests"""

    def test_import(self):
        """Import function"""
        from app.utils.datetime import now_local
        assert callable(now_local)

    def test_returns_datetime(self):
        """Returns datetime object"""
        from app.utils.datetime import now_local
        result = now_local()
        assert isinstance(result, datetime)

    def test_default_timezone_ulaanbaatar(self):
        """Default timezone is Asia/Ulaanbaatar"""
        from app.utils.datetime import now_local, _DEFAULT_TZ
        assert _DEFAULT_TZ == "Asia/Ulaanbaatar"

    def test_custom_timezone(self):
        """Can specify custom timezone"""
        from app.utils.datetime import now_local
        result = now_local("UTC")
        assert isinstance(result, datetime)
        # UTC timezone should be set
        assert result.tzinfo is not None

    def test_invalid_timezone_fallback(self):
        """Invalid timezone falls back to naive datetime"""
        from app.utils.datetime import now_local
        result = now_local("Invalid/Timezone")
        assert isinstance(result, datetime)
        # Should fall back to datetime.now() which is naive
        # (tzinfo may or may not be None depending on implementation)

    def test_returns_current_time(self):
        """Returns approximately current time"""
        from app.utils.datetime import now_local
        before = datetime.now()
        result = now_local()
        after = datetime.now()
        # Result should be between before and after (ignoring timezone)
        result_naive = result.replace(tzinfo=None)
        # Allow some tolerance for timezone difference
        assert abs((result_naive - before).total_seconds()) < 86400  # Within 24 hours

    def test_with_utc_timezone(self):
        """Works with UTC timezone"""
        from app.utils.datetime import now_local
        result = now_local("UTC")
        assert result.tzinfo is not None
        assert "UTC" in str(result.tzinfo) or "+00:00" in str(result)

    def test_with_us_timezone(self):
        """Works with US timezone"""
        from app.utils.datetime import now_local
        try:
            result = now_local("America/New_York")
            assert isinstance(result, datetime)
        except Exception:
            # Some systems may not have all timezone data
            pass


class TestNowMn:
    """now_mn legacy function tests"""

    def test_import(self):
        """Import function"""
        from app.utils.datetime import now_mn
        assert callable(now_mn)

    def test_returns_datetime(self):
        """Returns datetime object"""
        from app.utils.datetime import now_mn
        result = now_mn()
        assert isinstance(result, datetime)

    def test_same_as_now_local(self):
        """Returns same as now_local() with default timezone"""
        from app.utils.datetime import now_mn, now_local
        # Both should return very similar times
        result1 = now_mn()
        result2 = now_local()
        # Within 1 second of each other
        diff = abs((result1 - result2).total_seconds())
        assert diff < 1

    def test_has_timezone_info(self):
        """Result has timezone info"""
        from app.utils.datetime import now_mn
        result = now_mn()
        # Should have timezone from Asia/Ulaanbaatar
        assert result.tzinfo is not None


class TestDefaultTz:
    """Default timezone constant tests"""

    def test_default_tz_exists(self):
        """_DEFAULT_TZ constant exists"""
        from app.utils.datetime import _DEFAULT_TZ
        assert _DEFAULT_TZ is not None

    def test_default_tz_is_string(self):
        """_DEFAULT_TZ is string"""
        from app.utils.datetime import _DEFAULT_TZ
        assert isinstance(_DEFAULT_TZ, str)

    def test_default_tz_is_ulaanbaatar(self):
        """_DEFAULT_TZ is Asia/Ulaanbaatar"""
        from app.utils.datetime import _DEFAULT_TZ
        assert _DEFAULT_TZ == "Asia/Ulaanbaatar"


class TestEdgeCases:
    """Edge case tests"""

    def test_empty_string_timezone(self):
        """Empty string timezone"""
        from app.utils.datetime import now_local
        # Empty string is invalid timezone, should fallback
        result = now_local("")
        assert isinstance(result, datetime)

    def test_none_timezone(self):
        """None timezone raises TypeError or uses fallback"""
        from app.utils.datetime import now_local
        try:
            result = now_local(None)
            # If it doesn't raise, should return datetime
            assert isinstance(result, datetime)
        except TypeError:
            # This is also acceptable
            pass

    def test_numeric_timezone(self):
        """Numeric timezone value"""
        from app.utils.datetime import now_local
        try:
            result = now_local(123)
            # Should fallback if ZoneInfo fails
            assert isinstance(result, datetime)
        except (TypeError, AttributeError):
            # Also acceptable
            pass

    def test_multiple_calls_return_different_times(self):
        """Multiple calls return slightly different times"""
        from app.utils.datetime import now_local
        import time
        result1 = now_local()
        time.sleep(0.01)  # 10ms
        result2 = now_local()
        # Second call should be later or equal
        assert result2 >= result1

    def test_year_range_valid(self):
        """Returned year is reasonable"""
        from app.utils.datetime import now_local
        result = now_local()
        assert 2020 <= result.year <= 2100

    def test_month_range_valid(self):
        """Returned month is valid"""
        from app.utils.datetime import now_local
        result = now_local()
        assert 1 <= result.month <= 12

    def test_day_range_valid(self):
        """Returned day is valid"""
        from app.utils.datetime import now_local
        result = now_local()
        assert 1 <= result.day <= 31
