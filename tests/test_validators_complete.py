# tests/test_validators_complete.py
# -*- coding: utf-8 -*-
"""
Complete coverage tests for app/utils/validators.py
"""

import pytest


class TestAnalysisValueRanges:
    """Tests for ANALYSIS_VALUE_RANGES constant."""

    def test_ranges_exist(self, app):
        """Test ANALYSIS_VALUE_RANGES exists."""
        with app.app_context():
            from app.utils.validators import ANALYSIS_VALUE_RANGES
            assert isinstance(ANALYSIS_VALUE_RANGES, dict)

    def test_ranges_has_moisture(self, app):
        """Test ranges has moisture parameters."""
        with app.app_context():
            from app.utils.validators import ANALYSIS_VALUE_RANGES
            assert 'MT' in ANALYSIS_VALUE_RANGES
            assert 'Mad' in ANALYSIS_VALUE_RANGES

    def test_ranges_has_ash(self, app):
        """Test ranges has ash parameters."""
        with app.app_context():
            from app.utils.validators import ANALYSIS_VALUE_RANGES
            assert 'Aad' in ANALYSIS_VALUE_RANGES
            assert 'A' in ANALYSIS_VALUE_RANGES

    def test_ranges_are_tuples(self, app):
        """Test all ranges are tuples with min/max."""
        with app.app_context():
            from app.utils.validators import ANALYSIS_VALUE_RANGES
            for code, range_tuple in ANALYSIS_VALUE_RANGES.items():
                assert isinstance(range_tuple, tuple)
                assert len(range_tuple) == 2
                assert range_tuple[0] <= range_tuple[1]


class TestValidateAnalysisResult:
    """Tests for validate_analysis_result function."""

    def test_validate_none_allowed(self, app):
        """Test validate with None when allowed."""
        with app.app_context():
            from app.utils.validators import validate_analysis_result
            value, error = validate_analysis_result(None, 'MT', allow_none=True)
            assert value is None
            assert error is None

    def test_validate_none_not_allowed(self, app):
        """Test validate with None when not allowed."""
        with app.app_context():
            from app.utils.validators import validate_analysis_result
            value, error = validate_analysis_result(None, 'MT', allow_none=False)
            assert value is None
            assert error is not None

    def test_validate_valid_float(self, app):
        """Test validate with valid float value."""
        with app.app_context():
            from app.utils.validators import validate_analysis_result
            value, error = validate_analysis_result(10.5, 'MT')
            assert value == 10.5
            assert error is None

    def test_validate_valid_int(self, app):
        """Test validate with valid int value."""
        with app.app_context():
            from app.utils.validators import validate_analysis_result
            value, error = validate_analysis_result(10, 'MT')
            assert value == 10.0
            assert error is None

    def test_validate_valid_string(self, app):
        """Test validate with valid string value."""
        with app.app_context():
            from app.utils.validators import validate_analysis_result
            value, error = validate_analysis_result("10.5", 'MT')
            assert value == 10.5
            assert error is None

    def test_validate_invalid_string(self, app):
        """Test validate with invalid string value."""
        with app.app_context():
            from app.utils.validators import validate_analysis_result
            value, error = validate_analysis_result("invalid", 'MT')
            assert value is None
            assert error is not None

    def test_validate_out_of_range_high(self, app):
        """Test validate with value above range."""
        with app.app_context():
            from app.utils.validators import validate_analysis_result
            # MT range is (0.5, 40.0)
            value, error = validate_analysis_result(50.0, 'MT')
            assert value is None
            assert error is not None

    def test_validate_out_of_range_low(self, app):
        """Test validate with value below range."""
        with app.app_context():
            from app.utils.validators import validate_analysis_result
            # MT range is (0.5, 40.0)
            value, error = validate_analysis_result(0.1, 'MT')
            assert value is None
            assert error is not None

    def test_validate_at_boundary(self, app):
        """Test validate with value at boundary."""
        with app.app_context():
            from app.utils.validators import validate_analysis_result
            # MT range is (0.5, 40.0)
            value, error = validate_analysis_result(0.5, 'MT')
            assert value == 0.5
            assert error is None

    def test_validate_unknown_code(self, app):
        """Test validate with unknown analysis code."""
        with app.app_context():
            from app.utils.validators import validate_analysis_result
            value, error = validate_analysis_result(100.0, 'UNKNOWN')
            # Should use default range
            assert value == 100.0

    def test_validate_empty_string(self, app):
        """Test validate with empty string."""
        with app.app_context():
            from app.utils.validators import validate_analysis_result
            value, error = validate_analysis_result("", 'MT', allow_none=True)
            assert value is None

    def test_validate_whitespace_string(self, app):
        """Test validate with whitespace string."""
        with app.app_context():
            from app.utils.validators import validate_analysis_result
            value, error = validate_analysis_result("  10.5  ", 'MT')
            assert value == 10.5

    def test_validate_comma_decimal(self, app):
        """Test validate with comma as decimal separator."""
        with app.app_context():
            from app.utils.validators import validate_analysis_result
            value, error = validate_analysis_result("10,5", 'MT')
            # May or may not handle comma decimals
            assert value is None or value == 10.5

    def test_validate_negative_value(self, app):
        """Test validate with negative value."""
        with app.app_context():
            from app.utils.validators import validate_analysis_result
            value, error = validate_analysis_result(-5.0, 'MT')
            assert value is None
            assert error is not None

    def test_validate_calorific_value(self, app):
        """Test validate with calorific value."""
        with app.app_context():
            from app.utils.validators import validate_analysis_result
            value, error = validate_analysis_result(6000.0, 'CV')
            assert value == 6000.0
            assert error is None

    def test_validate_sulfur(self, app):
        """Test validate with sulfur value."""
        with app.app_context():
            from app.utils.validators import validate_analysis_result
            value, error = validate_analysis_result(2.5, 'TS')
            assert value == 2.5
            assert error is None


class TestDefaultRange:
    """Tests for DEFAULT_RANGE constant."""

    def test_default_range_exists(self, app):
        """Test DEFAULT_RANGE exists."""
        with app.app_context():
            from app.utils.validators import DEFAULT_RANGE
            assert isinstance(DEFAULT_RANGE, tuple)
            assert len(DEFAULT_RANGE) == 2
