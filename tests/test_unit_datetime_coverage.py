# tests/unit/test_datetime_coverage.py
"""Datetime utility coverage tests"""
import pytest
from datetime import datetime


class TestNowLocal:
    """now_local function tests"""

    def test_now_local_default(self):
        """Default timezone"""
        from app.utils.datetime import now_local
        result = now_local()
        assert isinstance(result, datetime)

    def test_now_local_custom_tz(self):
        """Custom timezone"""
        from app.utils.datetime import now_local
        result = now_local("Asia/Ulaanbaatar")
        assert isinstance(result, datetime)

    def test_now_local_invalid_tz(self):
        """Invalid timezone - should fallback"""
        from app.utils.datetime import now_local
        result = now_local("Invalid/Timezone")
        assert isinstance(result, datetime)

    def test_now_local_utc(self):
        """UTC timezone"""
        from app.utils.datetime import now_local
        result = now_local("UTC")
        assert isinstance(result, datetime)


class TestNowMn:
    """now_mn legacy function tests"""

    def test_now_mn(self):
        """Legacy now_mn function"""
        from app.utils.datetime import now_mn
        result = now_mn()
        assert isinstance(result, datetime)

    def test_now_mn_type(self):
        """Check return type"""
        from app.utils.datetime import now_mn
        result = now_mn()
        assert hasattr(result, 'year')
        assert hasattr(result, 'month')
        assert hasattr(result, 'day')


class TestDatetimeConstants:
    """Datetime constants tests"""

    def test_default_tz_exists(self):
        """Default timezone constant exists"""
        from app.utils.datetime import _DEFAULT_TZ
        assert _DEFAULT_TZ == "Asia/Ulaanbaatar"
