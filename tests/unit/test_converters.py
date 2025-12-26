# -*- coding: utf-8 -*-
"""
Tests for app/utils/converters.py
Type conversion utility tests
"""
import pytest


class TestToFloat:
    """to_float function tests"""

    def test_import(self):
        """Import function"""
        from app.utils.converters import to_float
        assert callable(to_float)

    def test_none_returns_none(self):
        """None input returns None"""
        from app.utils.converters import to_float
        assert to_float(None) is None

    def test_int_to_float(self):
        """Int converted to float"""
        from app.utils.converters import to_float
        assert to_float(10) == 10.0

    def test_float_returns_float(self):
        """Float returns float"""
        from app.utils.converters import to_float
        assert to_float(10.5) == 10.5

    def test_string_number(self):
        """String number converted"""
        from app.utils.converters import to_float
        assert to_float("10.5") == 10.5

    def test_string_int(self):
        """String int converted"""
        from app.utils.converters import to_float
        assert to_float("10") == 10.0

    def test_comma_to_dot(self):
        """Comma converted to dot"""
        from app.utils.converters import to_float
        assert to_float("10,5") == 10.5

    def test_whitespace_stripped(self):
        """Whitespace stripped"""
        from app.utils.converters import to_float
        assert to_float("  10.5  ") == 10.5

    def test_internal_spaces_removed(self):
        """Internal spaces removed"""
        from app.utils.converters import to_float
        assert to_float("10 000.5") == 10000.5

    def test_nbsp_removed(self):
        """Non-breaking space removed"""
        from app.utils.converters import to_float
        # \u00A0 is non-breaking space
        assert to_float("10\u00A05") == 105.0

    def test_empty_string_returns_none(self):
        """Empty string returns None"""
        from app.utils.converters import to_float
        assert to_float("") is None

    def test_whitespace_only_returns_none(self):
        """Whitespace only returns None"""
        from app.utils.converters import to_float
        assert to_float("   ") is None

    def test_null_string_returns_none(self):
        """'null' string returns None"""
        from app.utils.converters import to_float
        assert to_float("null") is None

    def test_null_uppercase_returns_none(self):
        """'NULL' string returns None"""
        from app.utils.converters import to_float
        assert to_float("NULL") is None

    def test_none_string_returns_none(self):
        """'none' string returns None"""
        from app.utils.converters import to_float
        assert to_float("none") is None

    def test_na_string_returns_none(self):
        """'na' string returns None"""
        from app.utils.converters import to_float
        assert to_float("na") is None

    def test_n_a_string_returns_none(self):
        """'n/a' string returns None"""
        from app.utils.converters import to_float
        assert to_float("n/a") is None

    def test_dash_returns_none(self):
        """'-' string returns None"""
        from app.utils.converters import to_float
        assert to_float("-") is None

    def test_invalid_string_returns_none(self):
        """Invalid string returns None"""
        from app.utils.converters import to_float
        assert to_float("abc") is None

    def test_mixed_invalid_returns_none(self):
        """Mixed invalid string returns None"""
        from app.utils.converters import to_float
        assert to_float("10abc") is None

    def test_negative_number(self):
        """Negative number works"""
        from app.utils.converters import to_float
        assert to_float("-10.5") == -10.5

    def test_negative_int(self):
        """Negative int works"""
        from app.utils.converters import to_float
        assert to_float(-10) == -10.0

    def test_zero(self):
        """Zero works"""
        from app.utils.converters import to_float
        assert to_float(0) == 0.0
        assert to_float("0") == 0.0

    def test_scientific_notation(self):
        """Scientific notation works"""
        from app.utils.converters import to_float
        assert to_float("1e10") == 1e10

    def test_float_zero(self):
        """Float zero works"""
        from app.utils.converters import to_float
        assert to_float(0.0) == 0.0

    def test_very_large_number(self):
        """Very large number works"""
        from app.utils.converters import to_float
        assert to_float("9999999999.99") == 9999999999.99

    def test_very_small_number(self):
        """Very small number works"""
        from app.utils.converters import to_float
        assert to_float("0.0000001") == 0.0000001

    def test_leading_zeros(self):
        """Leading zeros work"""
        from app.utils.converters import to_float
        assert to_float("007.5") == 7.5

    def test_trailing_zeros(self):
        """Trailing zeros work"""
        from app.utils.converters import to_float
        assert to_float("10.500") == 10.5

    def test_list_returns_none(self):
        """List returns None"""
        from app.utils.converters import to_float
        assert to_float([1, 2, 3]) is None

    def test_dict_returns_none(self):
        """Dict returns None"""
        from app.utils.converters import to_float
        assert to_float({"a": 1}) is None

    def test_bool_true(self):
        """Bool True converts to 1.0"""
        from app.utils.converters import to_float
        # bool is subclass of int in Python
        assert to_float(True) == 1.0

    def test_bool_false(self):
        """Bool False converts to 0.0"""
        from app.utils.converters import to_float
        assert to_float(False) == 0.0

    def test_european_format_comma(self):
        """European format with comma decimal"""
        from app.utils.converters import to_float
        assert to_float("123,45") == 123.45

    def test_plus_sign(self):
        """Plus sign works"""
        from app.utils.converters import to_float
        assert to_float("+10.5") == 10.5

    def test_multiple_dots_returns_none(self):
        """Multiple dots returns None"""
        from app.utils.converters import to_float
        assert to_float("10.5.5") is None

    def test_na_uppercase(self):
        """'NA' uppercase returns None"""
        from app.utils.converters import to_float
        assert to_float("NA") is None

    def test_n_a_uppercase(self):
        """'N/A' uppercase returns None"""
        from app.utils.converters import to_float
        assert to_float("N/A") is None
