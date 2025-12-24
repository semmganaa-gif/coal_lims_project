# tests/test_converters_full.py
# -*- coding: utf-8 -*-
"""
Complete tests for app/utils/converters.py
"""

import pytest


class TestToFloat:
    """Tests for to_float function."""

    def test_none_returns_none(self, app):
        """Test None returns None."""
        with app.app_context():
            from app.utils.converters import to_float
            result = to_float(None)
            assert result is None

    def test_int_returns_float(self, app):
        """Test int returns float."""
        with app.app_context():
            from app.utils.converters import to_float
            result = to_float(123)
            assert result == 123.0
            assert isinstance(result, float)

    def test_float_returns_float(self, app):
        """Test float returns float."""
        with app.app_context():
            from app.utils.converters import to_float
            result = to_float(123.45)
            assert result == 123.45

    def test_string_number(self, app):
        """Test string number returns float."""
        with app.app_context():
            from app.utils.converters import to_float
            result = to_float("123.45")
            assert result == 123.45

    def test_string_with_spaces(self, app):
        """Test string with spaces."""
        with app.app_context():
            from app.utils.converters import to_float
            result = to_float("  123.45  ")
            assert result == 123.45

    def test_string_with_comma(self, app):
        """Test string with comma (European format)."""
        with app.app_context():
            from app.utils.converters import to_float
            result = to_float("123,45")
            assert result == 123.45

    def test_empty_string_returns_none(self, app):
        """Test empty string returns None."""
        with app.app_context():
            from app.utils.converters import to_float
            result = to_float("")
            assert result is None

    def test_null_string_returns_none(self, app):
        """Test 'null' string returns None."""
        with app.app_context():
            from app.utils.converters import to_float
            result = to_float("null")
            assert result is None

    def test_none_string_returns_none(self, app):
        """Test 'none' string returns None."""
        with app.app_context():
            from app.utils.converters import to_float
            result = to_float("none")
            assert result is None

    def test_na_string_returns_none(self, app):
        """Test 'na' string returns None."""
        with app.app_context():
            from app.utils.converters import to_float
            result = to_float("na")
            assert result is None

    def test_n_a_string_returns_none(self, app):
        """Test 'n/a' string returns None."""
        with app.app_context():
            from app.utils.converters import to_float
            result = to_float("n/a")
            assert result is None

    def test_dash_returns_none(self, app):
        """Test '-' returns None."""
        with app.app_context():
            from app.utils.converters import to_float
            result = to_float("-")
            assert result is None

    def test_invalid_string_returns_none(self, app):
        """Test invalid string returns None."""
        with app.app_context():
            from app.utils.converters import to_float
            result = to_float("not a number")
            assert result is None

    def test_non_breaking_space(self, app):
        """Test non-breaking space is stripped."""
        with app.app_context():
            from app.utils.converters import to_float
            result = to_float("123\u00A045")  # non-breaking space
            assert result == 12345.0

    def test_negative_number(self, app):
        """Test negative number."""
        with app.app_context():
            from app.utils.converters import to_float
            result = to_float("-123.45")
            assert result == -123.45

    def test_scientific_notation(self, app):
        """Test scientific notation."""
        with app.app_context():
            from app.utils.converters import to_float
            result = to_float("1.5e3")
            assert result == 1500.0

    def test_uppercase_null(self, app):
        """Test uppercase 'NULL' returns None."""
        with app.app_context():
            from app.utils.converters import to_float
            result = to_float("NULL")
            assert result is None

    def test_mixed_case_none(self, app):
        """Test mixed case 'None' returns None."""
        with app.app_context():
            from app.utils.converters import to_float
            result = to_float("None")
            assert result is None

    def test_list_returns_none(self, app):
        """Test list returns None."""
        with app.app_context():
            from app.utils.converters import to_float
            result = to_float([1, 2, 3])
            assert result is None

    def test_dict_returns_none(self, app):
        """Test dict returns None."""
        with app.app_context():
            from app.utils.converters import to_float
            result = to_float({'value': 123})
            assert result is None

    def test_zero(self, app):
        """Test zero returns 0.0."""
        with app.app_context():
            from app.utils.converters import to_float
            result = to_float(0)
            assert result == 0.0

    def test_string_zero(self, app):
        """Test string zero returns 0.0."""
        with app.app_context():
            from app.utils.converters import to_float
            result = to_float("0")
            assert result == 0.0
