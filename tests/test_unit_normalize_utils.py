# -*- coding: utf-8 -*-
"""
Normalize utility тестүүд
"""
import pytest
from app.utils.normalize import (
    normalize_raw_data,
    COMMON_VALUE_ALIASES,
    RESULT_ALIASES
)


class TestNormalizeRawData:
    """normalize_raw_data функц тестүүд"""

    def test_empty_data(self):
        """Хоосон data"""
        result = normalize_raw_data({})
        assert isinstance(result, dict)

    def test_basic_data(self):
        """Энгийн data"""
        data = {'m1': 1.5, 'm2': 1.6}
        result = normalize_raw_data(data)
        assert isinstance(result, dict)

    def test_with_aliases(self):
        """Alias-тай data"""
        data = {'trial_1': 1.5, 'trial_2': 1.6}
        result = normalize_raw_data(data)
        assert isinstance(result, dict)

    def test_none_input(self):
        """None оролт"""
        try:
            result = normalize_raw_data(None)
            assert result is None or isinstance(result, dict)
        except (TypeError, AttributeError):
            pass


class TestAliasConstants:
    """Alias constants тестүүд"""

    def test_common_value_aliases_exists(self):
        """COMMON_VALUE_ALIASES байгаа эсэх"""
        assert COMMON_VALUE_ALIASES is not None
        assert isinstance(COMMON_VALUE_ALIASES, dict)

    def test_result_aliases_exists(self):
        """RESULT_ALIASES байгаа эсэх"""
        assert RESULT_ALIASES is not None
        assert isinstance(RESULT_ALIASES, (list, tuple))
