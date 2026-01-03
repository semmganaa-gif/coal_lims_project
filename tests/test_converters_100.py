# -*- coding: utf-8 -*-
"""
converters.py модулийн 100% coverage тестүүд
"""
import pytest


class TestConvertersImport:
    """Модуль импорт тест"""

    def test_import_module(self):
        from app.utils import converters
        assert converters is not None

    def test_import_to_float(self):
        from app.utils.converters import to_float
        assert to_float is not None
        assert callable(to_float)


class TestToFloatNone:
    """to_float - None утгуудын тест"""

    def test_none_input(self):
        from app.utils.converters import to_float
        assert to_float(None) is None

    def test_empty_string(self):
        from app.utils.converters import to_float
        assert to_float("") is None

    def test_whitespace_only(self):
        from app.utils.converters import to_float
        assert to_float("   ") is None

    def test_null_string(self):
        from app.utils.converters import to_float
        assert to_float("null") is None

    def test_none_string(self):
        from app.utils.converters import to_float
        assert to_float("none") is None

    def test_na_string(self):
        from app.utils.converters import to_float
        assert to_float("na") is None

    def test_na_slash_string(self):
        from app.utils.converters import to_float
        assert to_float("n/a") is None

    def test_dash_string(self):
        from app.utils.converters import to_float
        assert to_float("-") is None

    def test_null_uppercase(self):
        from app.utils.converters import to_float
        assert to_float("NULL") is None

    def test_none_uppercase(self):
        from app.utils.converters import to_float
        assert to_float("NONE") is None

    def test_na_uppercase(self):
        from app.utils.converters import to_float
        assert to_float("NA") is None

    def test_na_slash_uppercase(self):
        from app.utils.converters import to_float
        assert to_float("N/A") is None


class TestToFloatNumbers:
    """to_float - Тоон утгуудын тест"""

    def test_int_input(self):
        from app.utils.converters import to_float
        assert to_float(42) == 42.0

    def test_float_input(self):
        from app.utils.converters import to_float
        assert to_float(3.14) == 3.14

    def test_negative_int(self):
        from app.utils.converters import to_float
        assert to_float(-5) == -5.0

    def test_negative_float(self):
        from app.utils.converters import to_float
        assert to_float(-2.5) == -2.5

    def test_zero_int(self):
        from app.utils.converters import to_float
        assert to_float(0) == 0.0

    def test_zero_float(self):
        from app.utils.converters import to_float
        assert to_float(0.0) == 0.0


class TestToFloatStrings:
    """to_float - String тоон утгуудын тест"""

    def test_simple_string_int(self):
        from app.utils.converters import to_float
        assert to_float("42") == 42.0

    def test_simple_string_float(self):
        from app.utils.converters import to_float
        assert to_float("3.14") == 3.14

    def test_string_with_spaces(self):
        from app.utils.converters import to_float
        assert to_float("  42  ") == 42.0

    def test_string_with_inner_spaces(self):
        from app.utils.converters import to_float
        # Spaces in number should be removed
        assert to_float("1 000") == 1000.0

    def test_comma_decimal(self):
        from app.utils.converters import to_float
        assert to_float("3,14") == 3.14

    def test_negative_string(self):
        from app.utils.converters import to_float
        assert to_float("-5.5") == -5.5

    def test_non_breaking_space(self):
        from app.utils.converters import to_float
        # \u00A0 is non-breaking space
        assert to_float("1\u00A0000") == 1000.0

    def test_scientific_notation(self):
        from app.utils.converters import to_float
        assert to_float("1e3") == 1000.0

    def test_scientific_negative(self):
        from app.utils.converters import to_float
        assert to_float("1e-3") == 0.001


class TestToFloatInvalid:
    """to_float - Буруу утгуудын тест"""

    def test_invalid_string(self):
        from app.utils.converters import to_float
        assert to_float("abc") is None

    def test_mixed_invalid(self):
        from app.utils.converters import to_float
        assert to_float("12abc") is None

    def test_special_chars(self):
        from app.utils.converters import to_float
        assert to_float("@#$") is None

    def test_list_input(self):
        from app.utils.converters import to_float
        assert to_float([1, 2, 3]) is None

    def test_dict_input(self):
        from app.utils.converters import to_float
        assert to_float({"value": 1}) is None

    def test_object_input(self):
        from app.utils.converters import to_float
        assert to_float(object()) is None

    def test_bool_input(self):
        from app.utils.converters import to_float
        # Bool is subclass of int, so True = 1.0, False = 0.0
        assert to_float(True) == 1.0
        assert to_float(False) == 0.0


class TestToFloatEdgeCases:
    """to_float - Edge cases"""

    def test_very_large_number(self):
        from app.utils.converters import to_float
        result = to_float("999999999999")
        assert result == 999999999999.0

    def test_very_small_decimal(self):
        from app.utils.converters import to_float
        result = to_float("0.000001")
        assert result == 0.000001

    def test_leading_zeros(self):
        from app.utils.converters import to_float
        assert to_float("007") == 7.0

    def test_trailing_zeros(self):
        from app.utils.converters import to_float
        assert to_float("7.00") == 7.0

    def test_only_decimal_point(self):
        from app.utils.converters import to_float
        # Just "." is not a valid number
        assert to_float(".") is None

    def test_decimal_without_leading_zero(self):
        from app.utils.converters import to_float
        assert to_float(".5") == 0.5

    def test_decimal_without_trailing(self):
        from app.utils.converters import to_float
        assert to_float("5.") == 5.0
