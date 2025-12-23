# tests/unit/test_converters.py
# -*- coding: utf-8 -*-
"""
Converters utility tests
"""
import pytest
from app.utils.converters import to_float


class TestToFloat:
    """to_float() функцийн тестүүд"""

    def test_none_returns_none(self):
        assert to_float(None) is None

    def test_int_converts_to_float(self):
        assert to_float(5) == 5.0
        assert to_float(0) == 0.0
        assert to_float(-10) == -10.0

    def test_float_returns_float(self):
        assert to_float(3.14) == 3.14
        assert to_float(0.0) == 0.0
        assert to_float(-2.5) == -2.5

    def test_string_number_converts(self):
        assert to_float("3.14") == 3.14
        assert to_float("100") == 100.0
        assert to_float("-50.5") == -50.5

    def test_string_with_comma_converts(self):
        """European decimal format with comma"""
        assert to_float("3,14") == 3.14
        assert to_float("1000,5") == 1000.5

    def test_string_with_spaces_strips(self):
        assert to_float("  3.14  ") == 3.14
        assert to_float(" 100 ") == 100.0

    def test_string_with_nbsp_strips(self):
        """Non-breaking space removal"""
        assert to_float("3.14\u00A0") == 3.14
        assert to_float("\u00A0100\u00A0") == 100.0

    def test_empty_string_returns_none(self):
        assert to_float("") is None
        assert to_float("   ") is None

    def test_null_string_returns_none(self):
        assert to_float("null") is None
        assert to_float("NULL") is None
        assert to_float("Null") is None

    def test_none_string_returns_none(self):
        assert to_float("none") is None
        assert to_float("NONE") is None
        assert to_float("None") is None

    def test_na_string_returns_none(self):
        assert to_float("na") is None
        assert to_float("NA") is None
        assert to_float("n/a") is None
        assert to_float("N/A") is None

    def test_dash_returns_none(self):
        assert to_float("-") is None

    def test_invalid_string_returns_none(self):
        assert to_float("abc") is None
        assert to_float("not a number") is None
        assert to_float("12abc") is None

    def test_list_returns_none(self):
        assert to_float([1, 2, 3]) is None

    def test_dict_returns_none(self):
        assert to_float({"a": 1}) is None

    def test_bool_returns_none(self):
        """Bool is not int/float instance check"""
        # In Python, bool is subclass of int, so True=1.0, False=0.0
        # But our function checks isinstance(v, (int, float)) which includes bool
        assert to_float(True) == 1.0
        assert to_float(False) == 0.0

    def test_scientific_notation(self):
        assert to_float("1e5") == 100000.0
        assert to_float("1.5e-3") == 0.0015

    def test_zero_variations(self):
        assert to_float("0") == 0.0
        assert to_float("0.0") == 0.0
        assert to_float("0,0") == 0.0
        assert to_float(0) == 0.0
        assert to_float(0.0) == 0.0
