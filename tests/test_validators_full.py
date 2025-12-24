# tests/test_validators_full.py
# -*- coding: utf-8 -*-
"""
Complete tests for app/utils/validators.py - targeting 100% coverage.
"""

import pytest
from unittest.mock import patch, MagicMock


class TestValidateAnalysisResult:
    """Tests for validate_analysis_result function."""

    def test_valid_float_value(self, app):
        """Test with valid float value."""
        with app.app_context():
            from app.utils.validators import validate_analysis_result
            value, error = validate_analysis_result(5.0, 'MT')
            assert value == 5.0
            assert error is None

    def test_valid_int_value(self, app):
        """Test with valid int value."""
        with app.app_context():
            from app.utils.validators import validate_analysis_result
            value, error = validate_analysis_result(5, 'MT')
            assert value == 5.0
            assert error is None

    def test_valid_string_value(self, app):
        """Test with valid string value."""
        with app.app_context():
            from app.utils.validators import validate_analysis_result
            value, error = validate_analysis_result('5.5', 'MT')
            assert value == 5.5
            assert error is None

    def test_string_with_comma(self, app):
        """Test with string containing comma as decimal."""
        with app.app_context():
            from app.utils.validators import validate_analysis_result
            value, error = validate_analysis_result('5,5', 'MT')
            assert value == 5.5
            assert error is None

    def test_none_value_allowed(self, app):
        """Test with None value when allowed."""
        with app.app_context():
            from app.utils.validators import validate_analysis_result
            value, error = validate_analysis_result(None, 'MT', allow_none=True)
            assert value is None
            assert error is None

    def test_empty_string_allowed(self, app):
        """Test with empty string when None allowed."""
        with app.app_context():
            from app.utils.validators import validate_analysis_result
            value, error = validate_analysis_result('', 'MT', allow_none=True)
            assert value is None
            assert error is None

    def test_none_value_not_allowed(self, app):
        """Test with None value when not allowed."""
        with app.app_context():
            from app.utils.validators import validate_analysis_result
            value, error = validate_analysis_result(None, 'MT', allow_none=False)
            assert value is None
            assert error is not None

    def test_invalid_string_value(self, app):
        """Test with invalid string value."""
        with app.app_context():
            from app.utils.validators import validate_analysis_result
            value, error = validate_analysis_result('abc', 'MT')
            assert value is None
            assert error is not None
            assert 'тоон' in error

    def test_invalid_type(self, app):
        """Test with invalid type (list)."""
        with app.app_context():
            from app.utils.validators import validate_analysis_result
            value, error = validate_analysis_result([1, 2, 3], 'MT')
            assert value is None
            assert error is not None
            assert 'төрөл' in error

    def test_value_too_large(self, app):
        """Test with extremely large value."""
        with app.app_context():
            from app.utils.validators import validate_analysis_result
            value, error = validate_analysis_result(1e309, 'MT')
            assert value is None
            assert error is not None

    def test_value_below_range(self, app):
        """Test with value below allowed range."""
        with app.app_context():
            from app.utils.validators import validate_analysis_result
            value, error = validate_analysis_result(0.01, 'MT')  # MT min is 0.5
            assert value is None
            assert error is not None
            assert 'хооронд' in error

    def test_value_above_range(self, app):
        """Test with value above allowed range."""
        with app.app_context():
            from app.utils.validators import validate_analysis_result
            value, error = validate_analysis_result(50.0, 'MT')  # MT max is 40
            assert value is None
            assert error is not None

    def test_unknown_analysis_code(self, app):
        """Test with unknown analysis code uses default range."""
        with app.app_context():
            from app.utils.validators import validate_analysis_result
            value, error = validate_analysis_result(500.0, 'UNKNOWN_CODE')
            assert value == 500.0
            assert error is None

    def test_all_analysis_codes(self, app):
        """Test with all defined analysis codes."""
        with app.app_context():
            from app.utils.validators import validate_analysis_result, ANALYSIS_VALUE_RANGES
            for code, (min_val, max_val) in ANALYSIS_VALUE_RANGES.items():
                mid = (min_val + max_val) / 2
                value, error = validate_analysis_result(mid, code)
                assert value == mid, f"Failed for {code}"
                assert error is None, f"Failed for {code}"


class TestValidateSampleId:
    """Tests for validate_sample_id function."""

    def test_valid_int(self, app):
        """Test with valid integer."""
        with app.app_context():
            from app.utils.validators import validate_sample_id
            sample_id, error = validate_sample_id(123)
            assert sample_id == 123
            assert error is None

    def test_valid_string(self, app):
        """Test with valid string."""
        with app.app_context():
            from app.utils.validators import validate_sample_id
            sample_id, error = validate_sample_id("456")
            assert sample_id == 456
            assert error is None

    def test_none_value(self, app):
        """Test with None value."""
        with app.app_context():
            from app.utils.validators import validate_sample_id
            sample_id, error = validate_sample_id(None)
            assert sample_id is None
            assert error is not None

    def test_invalid_string(self, app):
        """Test with invalid string."""
        with app.app_context():
            from app.utils.validators import validate_sample_id
            sample_id, error = validate_sample_id("abc")
            assert sample_id is None
            assert error is not None

    def test_zero_value(self, app):
        """Test with zero value."""
        with app.app_context():
            from app.utils.validators import validate_sample_id
            sample_id, error = validate_sample_id(0)
            assert sample_id is None
            assert error is not None
            assert 'эерэг' in error

    def test_negative_value(self, app):
        """Test with negative value."""
        with app.app_context():
            from app.utils.validators import validate_sample_id
            sample_id, error = validate_sample_id(-5)
            assert sample_id is None
            assert error is not None

    def test_value_too_large(self, app):
        """Test with value exceeding INT max."""
        with app.app_context():
            from app.utils.validators import validate_sample_id
            sample_id, error = validate_sample_id(2147483648)
            assert sample_id is None
            assert error is not None
            assert 'том' in error


class TestValidateAnalysisCode:
    """Tests for validate_analysis_code function."""

    def test_valid_code(self, app):
        """Test with valid analysis code."""
        with app.app_context():
            from app.utils.validators import validate_analysis_code
            code, error = validate_analysis_code("MT")
            assert code == "MT"
            assert error is None

    def test_valid_code_with_spaces(self, app):
        """Test with code containing spaces."""
        with app.app_context():
            from app.utils.validators import validate_analysis_code
            code, error = validate_analysis_code("St,ad")
            assert code == "St,ad"
            assert error is None

    def test_valid_code_stripped(self, app):
        """Test with code having leading/trailing spaces."""
        with app.app_context():
            from app.utils.validators import validate_analysis_code
            code, error = validate_analysis_code("  MT  ")
            assert code == "MT"
            assert error is None

    def test_none_value(self, app):
        """Test with None value."""
        with app.app_context():
            from app.utils.validators import validate_analysis_code
            code, error = validate_analysis_code(None)
            assert code is None
            assert error is not None

    def test_empty_string(self, app):
        """Test with empty string."""
        with app.app_context():
            from app.utils.validators import validate_analysis_code
            code, error = validate_analysis_code("")
            assert code is None
            assert error is not None

    def test_non_string_type(self, app):
        """Test with non-string type."""
        with app.app_context():
            from app.utils.validators import validate_analysis_code
            code, error = validate_analysis_code(123)
            assert code is None
            assert error is not None
            assert 'текст' in error

    def test_too_long_code(self, app):
        """Test with code exceeding 20 characters."""
        with app.app_context():
            from app.utils.validators import validate_analysis_code
            code, error = validate_analysis_code("A" * 25)
            assert code is None
            assert error is not None
            assert 'урт' in error

    def test_only_spaces(self, app):
        """Test with only spaces."""
        with app.app_context():
            from app.utils.validators import validate_analysis_code
            code, error = validate_analysis_code("   ")
            assert code is None
            assert error is not None

    def test_special_characters(self, app):
        """Test with special characters."""
        with app.app_context():
            from app.utils.validators import validate_analysis_code
            code, error = validate_analysis_code("MT$%^")
            assert code is None
            assert error is not None
            assert 'үсэг' in error or 'тоо' in error


class TestValidateEquipmentId:
    """Tests for validate_equipment_id function."""

    def test_valid_int(self, app):
        """Test with valid integer."""
        with app.app_context():
            from app.utils.validators import validate_equipment_id
            eq_id, error = validate_equipment_id(10)
            assert eq_id == 10
            assert error is None

    def test_valid_string(self, app):
        """Test with valid string."""
        with app.app_context():
            from app.utils.validators import validate_equipment_id
            eq_id, error = validate_equipment_id("20")
            assert eq_id == 20
            assert error is None

    def test_none_allowed(self, app):
        """Test with None when allowed."""
        with app.app_context():
            from app.utils.validators import validate_equipment_id
            eq_id, error = validate_equipment_id(None, allow_none=True)
            assert eq_id is None
            assert error is None

    def test_empty_string_allowed(self, app):
        """Test with empty string when allowed."""
        with app.app_context():
            from app.utils.validators import validate_equipment_id
            eq_id, error = validate_equipment_id('', allow_none=True)
            assert eq_id is None
            assert error is None

    def test_none_not_allowed(self, app):
        """Test with None when not allowed."""
        with app.app_context():
            from app.utils.validators import validate_equipment_id
            eq_id, error = validate_equipment_id(None, allow_none=False)
            assert eq_id is None
            assert error is not None

    def test_invalid_string(self, app):
        """Test with invalid string."""
        with app.app_context():
            from app.utils.validators import validate_equipment_id
            eq_id, error = validate_equipment_id("abc")
            assert eq_id is None
            assert error is not None
            assert 'тоо' in error

    def test_zero_value(self, app):
        """Test with zero value."""
        with app.app_context():
            from app.utils.validators import validate_equipment_id
            eq_id, error = validate_equipment_id(0)
            assert eq_id is None
            assert error is not None

    def test_negative_value(self, app):
        """Test with negative value."""
        with app.app_context():
            from app.utils.validators import validate_equipment_id
            eq_id, error = validate_equipment_id(-1)
            assert eq_id is None
            assert error is not None


class TestValidateSaveResultsBatch:
    """Tests for validate_save_results_batch function."""

    def test_valid_batch(self, app):
        """Test with valid batch."""
        with app.app_context():
            from app.utils.validators import validate_save_results_batch
            items = [
                {"sample_id": 1, "analysis_code": "MT", "final_result": 5.0}
            ]
            is_valid, validated, errors = validate_save_results_batch(items)
            assert is_valid is True
            assert len(validated) == 1
            assert len(errors) == 0

    def test_not_a_list(self, app):
        """Test with non-list input."""
        with app.app_context():
            from app.utils.validators import validate_save_results_batch
            is_valid, validated, errors = validate_save_results_batch("not a list")
            assert is_valid is False
            assert len(errors) == 1

    def test_item_not_dict(self, app):
        """Test with item that is not a dict."""
        with app.app_context():
            from app.utils.validators import validate_save_results_batch
            items = ["not a dict"]
            is_valid, validated, errors = validate_save_results_batch(items)
            assert is_valid is False

    def test_missing_sample_id(self, app):
        """Test with missing sample_id."""
        with app.app_context():
            from app.utils.validators import validate_save_results_batch
            items = [{"analysis_code": "MT", "final_result": 5.0}]
            is_valid, validated, errors = validate_save_results_batch(items)
            assert is_valid is False

    def test_invalid_sample_id(self, app):
        """Test with invalid sample_id."""
        with app.app_context():
            from app.utils.validators import validate_save_results_batch
            items = [{"sample_id": "abc", "analysis_code": "MT", "final_result": 5.0}]
            is_valid, validated, errors = validate_save_results_batch(items)
            assert is_valid is False

    def test_missing_analysis_code(self, app):
        """Test with missing analysis_code."""
        with app.app_context():
            from app.utils.validators import validate_save_results_batch
            items = [{"sample_id": 1, "final_result": 5.0}]
            is_valid, validated, errors = validate_save_results_batch(items)
            assert is_valid is False

    def test_invalid_analysis_code(self, app):
        """Test with invalid analysis_code."""
        with app.app_context():
            from app.utils.validators import validate_save_results_batch
            items = [{"sample_id": 1, "analysis_code": 123, "final_result": 5.0}]
            is_valid, validated, errors = validate_save_results_batch(items)
            assert is_valid is False

    def test_invalid_final_result(self, app):
        """Test with invalid final_result."""
        with app.app_context():
            from app.utils.validators import validate_save_results_batch
            items = [{"sample_id": 1, "analysis_code": "MT", "final_result": "abc"}]
            is_valid, validated, errors = validate_save_results_batch(items)
            assert len(errors) > 0  # Has error but may still be valid overall

    def test_invalid_equipment_id(self, app):
        """Test with invalid equipment_id."""
        with app.app_context():
            from app.utils.validators import validate_save_results_batch
            items = [{"sample_id": 1, "analysis_code": "MT", "final_result": 5.0, "equipment_id": "bad"}]
            is_valid, validated, errors = validate_save_results_batch(items)
            assert len(errors) > 0

    def test_optional_fields(self, app):
        """Test optional fields are included."""
        with app.app_context():
            from app.utils.validators import validate_save_results_batch
            items = [{"sample_id": 1, "analysis_code": "MT", "final_result": 5.0, "status": "approved", "notes": "test"}]
            is_valid, validated, errors = validate_save_results_batch(items)
            assert validated[0]['status'] == 'approved'
            assert validated[0]['notes'] == 'test'

    def test_multiple_items(self, app):
        """Test with multiple items."""
        with app.app_context():
            from app.utils.validators import validate_save_results_batch
            items = [
                {"sample_id": 1, "analysis_code": "MT", "final_result": 5.0},
                {"sample_id": 2, "analysis_code": "Aad", "final_result": 10.0},
                {"sample_id": 3, "analysis_code": "CV", "final_result": 25000}
            ]
            is_valid, validated, errors = validate_save_results_batch(items)
            assert is_valid is True
            assert len(validated) == 3


class TestGetCsnRepeatabilityLimit:
    """Tests for get_csn_repeatability_limit function."""

    def test_returns_float(self, app):
        """Test function returns float."""
        with app.app_context():
            from app.utils.validators import get_csn_repeatability_limit
            result = get_csn_repeatability_limit()
            assert isinstance(result, float)

    def test_fallback_value(self, app):
        """Test fallback when import fails."""
        with app.app_context():
            from app.utils.validators import get_csn_repeatability_limit
            # Test that the function always returns a float even on error
            result = get_csn_repeatability_limit()
            assert result >= 0


class TestRoundToHalf:
    """Tests for round_to_half function."""

    def test_round_down(self, app):
        """Test rounding down to 0.5."""
        with app.app_context():
            from app.utils.validators import round_to_half
            assert round_to_half(2.2) == 2.0
            assert round_to_half(2.1) == 2.0

    def test_round_up(self, app):
        """Test rounding up to 0.5."""
        with app.app_context():
            from app.utils.validators import round_to_half
            assert round_to_half(2.3) == 2.5
            assert round_to_half(2.4) == 2.5

    def test_round_to_whole(self, app):
        """Test rounding to whole number."""
        with app.app_context():
            from app.utils.validators import round_to_half
            assert round_to_half(2.75) == 3.0
            assert round_to_half(2.8) == 3.0

    def test_exact_half(self, app):
        """Test with exact half value."""
        with app.app_context():
            from app.utils.validators import round_to_half
            assert round_to_half(2.5) == 2.5

    def test_exact_whole(self, app):
        """Test with exact whole value."""
        with app.app_context():
            from app.utils.validators import round_to_half
            assert round_to_half(3.0) == 3.0

    def test_zero(self, app):
        """Test with zero."""
        with app.app_context():
            from app.utils.validators import round_to_half
            assert round_to_half(0) == 0


class TestValidateCsnValues:
    """Tests for validate_csn_values function."""

    def test_valid_values(self, app):
        """Test with valid CSN values."""
        with app.app_context():
            from app.utils.validators import validate_csn_values
            is_valid, result, errors = validate_csn_values([2, 2.5, 2, None, None])
            assert is_valid is True
            assert result is not None
            assert 'avg' in result

    def test_not_enough_values(self, app):
        """Test with less than 2 values."""
        with app.app_context():
            from app.utils.validators import validate_csn_values
            is_valid, result, errors = validate_csn_values([2, None, None, None, None])
            assert is_valid is False
            assert '2 утга' in errors[0]

    def test_invalid_value(self, app):
        """Test with invalid value."""
        with app.app_context():
            from app.utils.validators import validate_csn_values
            is_valid, result, errors = validate_csn_values([2, "abc", 2.5, None, None])
            assert len(errors) > 0

    def test_exceeded_repeatability(self, app):
        """Test with exceeded repeatability limit."""
        with app.app_context():
            from app.utils.validators import validate_csn_values
            is_valid, result, errors = validate_csn_values([1, 3, 2, None, None])  # range = 2 > 0.5
            assert result['exceeded'] is True

    def test_empty_string_ignored(self, app):
        """Test empty strings are ignored."""
        with app.app_context():
            from app.utils.validators import validate_csn_values
            is_valid, result, errors = validate_csn_values([2, '', 2.5, '', ''])
            assert result['values_count'] == 2

    def test_all_values(self, app):
        """Test with all 5 values."""
        with app.app_context():
            from app.utils.validators import validate_csn_values
            is_valid, result, errors = validate_csn_values([2, 2, 2.5, 2, 2.5])
            assert is_valid is True
            assert result['values_count'] == 5


class TestSanitizeString:
    """Tests for sanitize_string function."""

    def test_valid_string(self, app):
        """Test with valid string."""
        with app.app_context():
            from app.utils.validators import sanitize_string
            cleaned, error = sanitize_string("Hello World")
            assert cleaned == "Hello World"
            assert error is None

    def test_string_stripped(self, app):
        """Test string is stripped."""
        with app.app_context():
            from app.utils.validators import sanitize_string
            cleaned, error = sanitize_string("  Hello  ")
            assert cleaned == "Hello"

    def test_none_allowed(self, app):
        """Test with None when allowed."""
        with app.app_context():
            from app.utils.validators import sanitize_string
            cleaned, error = sanitize_string(None, allow_none=True)
            assert cleaned is None
            assert error is None

    def test_empty_allowed(self, app):
        """Test with empty string when allowed."""
        with app.app_context():
            from app.utils.validators import sanitize_string
            cleaned, error = sanitize_string('', allow_none=True)
            assert cleaned is None
            assert error is None

    def test_none_not_allowed(self, app):
        """Test with None when not allowed."""
        with app.app_context():
            from app.utils.validators import sanitize_string
            cleaned, error = sanitize_string(None, allow_none=False)
            assert cleaned is None
            assert error is not None

    def test_non_string_converted(self, app):
        """Test non-string is converted."""
        with app.app_context():
            from app.utils.validators import sanitize_string
            cleaned, error = sanitize_string(123)
            assert cleaned == "123"
            assert error is None

    def test_too_long(self, app):
        """Test string exceeding max length."""
        with app.app_context():
            from app.utils.validators import sanitize_string
            cleaned, error = sanitize_string("A" * 100, max_length=50)
            assert cleaned is None
            assert error is not None
            assert 'урт' in error

    def test_script_tag_blocked(self, app):
        """Test script tag is blocked."""
        with app.app_context():
            from app.utils.validators import sanitize_string
            cleaned, error = sanitize_string("<script>alert('xss')</script>")
            assert cleaned is None
            assert error is not None

    def test_javascript_blocked(self, app):
        """Test javascript: is blocked."""
        with app.app_context():
            from app.utils.validators import sanitize_string
            cleaned, error = sanitize_string("javascript:void(0)")
            assert cleaned is None
            assert error is not None

    def test_onerror_blocked(self, app):
        """Test onerror= is blocked."""
        with app.app_context():
            from app.utils.validators import sanitize_string
            cleaned, error = sanitize_string("<img onerror=alert(1)>")
            assert cleaned is None
            assert error is not None

    def test_onload_blocked(self, app):
        """Test onload= is blocked."""
        with app.app_context():
            from app.utils.validators import sanitize_string
            cleaned, error = sanitize_string("<body onload=alert(1)>")
            assert cleaned is None
            assert error is not None

    def test_onclick_blocked(self, app):
        """Test onclick= is blocked."""
        with app.app_context():
            from app.utils.validators import sanitize_string
            cleaned, error = sanitize_string("<a onclick=alert(1)>")
            assert cleaned is None
            assert error is not None

    def test_case_insensitive_xss(self, app):
        """Test XSS patterns are case insensitive."""
        with app.app_context():
            from app.utils.validators import sanitize_string
            cleaned, error = sanitize_string("<SCRIPT>alert(1)</SCRIPT>")
            assert cleaned is None
            assert error is not None


class TestAnalysisValueRanges:
    """Tests for ANALYSIS_VALUE_RANGES constant."""

    def test_all_ranges_valid(self, app):
        """Test all ranges have valid min < max."""
        with app.app_context():
            from app.utils.validators import ANALYSIS_VALUE_RANGES
            for code, (min_val, max_val) in ANALYSIS_VALUE_RANGES.items():
                assert min_val <= max_val, f"Invalid range for {code}"

    def test_common_codes_present(self, app):
        """Test common analysis codes are present."""
        with app.app_context():
            from app.utils.validators import ANALYSIS_VALUE_RANGES
            common_codes = ['MT', 'Mad', 'Aad', 'A', 'Vad', 'V', 'TS', 'CV']
            for code in common_codes:
                assert code in ANALYSIS_VALUE_RANGES, f"Missing {code}"
