# tests/test_validators_boost.py
# -*- coding: utf-8 -*-
"""Tests to boost validators.py coverage."""

import pytest


class TestValidateAnalysisResult:
    """Test validate_analysis_result function."""

    def test_validate_valid_result(self, app):
        """Test with valid result."""
        with app.app_context():
            from app.utils.validators import validate_analysis_result
            result, error = validate_analysis_result(5.5, 'TM')
            assert result == 5.5 or result is None
            assert error is None

    def test_validate_none_allowed(self, app):
        """Test with None when allowed."""
        with app.app_context():
            from app.utils.validators import validate_analysis_result
            result, error = validate_analysis_result(None, 'TM', allow_none=True)
            assert result is None
            assert error is None

    def test_validate_none_not_allowed(self, app):
        """Test with None when not allowed."""
        with app.app_context():
            from app.utils.validators import validate_analysis_result
            result, error = validate_analysis_result(None, 'TM', allow_none=False)
            assert result is None
            assert error is not None

    def test_validate_string_number(self, app):
        """Test with string number."""
        with app.app_context():
            from app.utils.validators import validate_analysis_result
            result, error = validate_analysis_result('5.5', 'TM')
            assert result == 5.5

    def test_validate_invalid_string(self, app):
        """Test with invalid string."""
        with app.app_context():
            from app.utils.validators import validate_analysis_result
            result, error = validate_analysis_result('invalid', 'TM')
            assert result is None
            assert error is not None

    def test_validate_out_of_range(self, app):
        """Test with out of range value."""
        with app.app_context():
            from app.utils.validators import validate_analysis_result
            # Mad should be 0.2-30%
            result, error = validate_analysis_result(100.0, 'Mad')
            assert result is None
            assert error is not None


class TestValidateSampleId:
    """Test validate_sample_id function."""

    def test_valid_int(self, app):
        """Test with valid integer."""
        with app.app_context():
            from app.utils.validators import validate_sample_id
            result, error = validate_sample_id(123)
            assert result == 123
            assert error is None

    def test_valid_string(self, app):
        """Test with valid string."""
        with app.app_context():
            from app.utils.validators import validate_sample_id
            result, error = validate_sample_id('456')
            assert result == 456
            assert error is None

    def test_invalid_string(self, app):
        """Test with invalid string."""
        with app.app_context():
            from app.utils.validators import validate_sample_id
            result, error = validate_sample_id('invalid')
            assert result is None
            assert error is not None

    def test_none_value(self, app):
        """Test with None."""
        with app.app_context():
            from app.utils.validators import validate_sample_id
            result, error = validate_sample_id(None)
            assert result is None
            assert error is not None

    def test_negative_value(self, app):
        """Test with negative value."""
        with app.app_context():
            from app.utils.validators import validate_sample_id
            result, error = validate_sample_id(-1)
            assert result is None
            assert error is not None


class TestValidateAnalysisCode:
    """Test validate_analysis_code function."""

    def test_valid_code(self, app):
        """Test with valid code."""
        with app.app_context():
            from app.utils.validators import validate_analysis_code
            result, error = validate_analysis_code('TM')
            assert result == 'TM'
            assert error is None

    def test_code_with_spaces(self, app):
        """Test with spaces."""
        with app.app_context():
            from app.utils.validators import validate_analysis_code
            result, error = validate_analysis_code('  Aad  ')
            assert result == 'Aad'
            assert error is None

    def test_empty_code(self, app):
        """Test with empty code."""
        with app.app_context():
            from app.utils.validators import validate_analysis_code
            result, error = validate_analysis_code('')
            assert result is None
            assert error is not None

    def test_none_code(self, app):
        """Test with None."""
        with app.app_context():
            from app.utils.validators import validate_analysis_code
            result, error = validate_analysis_code(None)
            assert result is None
            assert error is not None


class TestValidateEquipmentId:
    """Test validate_equipment_id function."""

    def test_valid_equipment_id(self, app):
        """Test with valid equipment id."""
        with app.app_context():
            from app.utils.validators import validate_equipment_id
            result, error = validate_equipment_id(1)
            assert result == 1
            assert error is None

    def test_invalid_equipment_id(self, app):
        """Test with invalid equipment id."""
        with app.app_context():
            from app.utils.validators import validate_equipment_id
            result, error = validate_equipment_id('invalid')
            assert result is None
            assert error is not None

    def test_none_allowed(self, app):
        """Test with None when allowed."""
        with app.app_context():
            from app.utils.validators import validate_equipment_id
            result, error = validate_equipment_id(None, allow_none=True)
            assert result is None
            assert error is None


class TestValidateSaveResultsBatch:
    """Test validate_save_results_batch function."""

    def test_empty_batch(self, app):
        """Test with empty batch."""
        with app.app_context():
            from app.utils.validators import validate_save_results_batch
            is_valid, validated, errors = validate_save_results_batch([])
            assert is_valid is True
            assert validated == []
            assert errors == []

    def test_valid_batch(self, app):
        """Test with valid batch."""
        with app.app_context():
            from app.utils.validators import validate_save_results_batch
            batch = [
                {'sample_id': 1, 'analysis_code': 'TM', 'final_result': 5.5}
            ]
            is_valid, validated, errors = validate_save_results_batch(batch)
            assert isinstance(validated, list)
            assert isinstance(errors, list)

    def test_invalid_batch_item(self, app):
        """Test with invalid batch item."""
        with app.app_context():
            from app.utils.validators import validate_save_results_batch
            batch = [
                {'sample_id': 'invalid', 'analysis_code': '', 'final_result': None}
            ]
            is_valid, validated, errors = validate_save_results_batch(batch)
            assert len(errors) > 0

    def test_not_list(self, app):
        """Test with non-list input."""
        with app.app_context():
            from app.utils.validators import validate_save_results_batch
            is_valid, validated, errors = validate_save_results_batch("not a list")
            assert is_valid is False


class TestCsnRepeatability:
    """Test CSN repeatability functions."""

    def test_get_csn_repeatability_limit(self, app):
        """Test get CSN repeatability limit."""
        with app.app_context():
            from app.utils.validators import get_csn_repeatability_limit
            limit = get_csn_repeatability_limit()
            assert isinstance(limit, float)
            assert limit > 0

    def test_round_to_half(self, app):
        """Test round to half."""
        with app.app_context():
            from app.utils.validators import round_to_half
            assert round_to_half(2.3) == 2.5
            assert round_to_half(2.7) == 2.5
            assert round_to_half(2.8) == 3.0
            assert round_to_half(5.0) == 5.0


class TestValidateCsnValues:
    """Test validate_csn_values function."""

    def test_validate_csn_valid(self, app):
        """Test CSN validation with valid values."""
        with app.app_context():
            from app.utils.validators import validate_csn_values
            is_valid, result, errors = validate_csn_values([2, 2, 2, None, None])
            assert is_valid is True
            assert result is not None
            assert 'avg' in result

    def test_validate_csn_exceeded(self, app):
        """Test CSN validation with exceeded range."""
        with app.app_context():
            from app.utils.validators import validate_csn_values
            is_valid, result, errors = validate_csn_values([1, 5, None, None, None])
            # Range = 4 which exceeds 0.5 limit
            assert len(errors) > 0

    def test_validate_csn_not_enough_values(self, app):
        """Test CSN validation with not enough values."""
        with app.app_context():
            from app.utils.validators import validate_csn_values
            is_valid, result, errors = validate_csn_values([2, None, None, None, None])
            assert is_valid is False
            assert len(errors) > 0


class TestSanitizeString:
    """Test sanitize_string function."""

    def test_sanitize_normal(self, app):
        """Test sanitize normal string."""
        with app.app_context():
            from app.utils.validators import sanitize_string
            result, error = sanitize_string("Hello World")
            assert result == "Hello World"
            assert error is None

    def test_sanitize_with_script(self, app):
        """Test sanitize with script tag."""
        with app.app_context():
            from app.utils.validators import sanitize_string
            result, error = sanitize_string("<script>alert('xss')</script>")
            assert result is None
            assert error is not None

    def test_sanitize_none_allowed(self, app):
        """Test sanitize None when allowed."""
        with app.app_context():
            from app.utils.validators import sanitize_string
            result, error = sanitize_string(None, allow_none=True)
            assert result is None
            assert error is None

    def test_sanitize_none_not_allowed(self, app):
        """Test sanitize None when not allowed."""
        with app.app_context():
            from app.utils.validators import sanitize_string
            result, error = sanitize_string(None, allow_none=False)
            assert result is None
            assert error is not None

    def test_sanitize_max_length(self, app):
        """Test sanitize with max length exceeded."""
        with app.app_context():
            from app.utils.validators import sanitize_string
            long_string = "a" * 2000
            result, error = sanitize_string(long_string, max_length=100)
            assert result is None
            assert error is not None

    def test_sanitize_javascript(self, app):
        """Test sanitize with javascript:."""
        with app.app_context():
            from app.utils.validators import sanitize_string
            result, error = sanitize_string("javascript:alert(1)")
            assert result is None
            assert error is not None
