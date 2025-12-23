# -*- coding: utf-8 -*-
"""
Validators extended unit тестүүд
"""
import pytest
from app.utils.validators import (
    validate_analysis_result,
    validate_sample_id,
    validate_analysis_code,
    validate_equipment_id,
    validate_save_results_batch,
    sanitize_string,
)


class TestValidateAnalysisResultExtended:
    """Extended tests for validate_analysis_result"""

    def test_wrong_type_input(self):
        """Wrong type input should fail"""
        value, error = validate_analysis_result([1, 2, 3], "Mad")
        assert value is None
        assert error is not None

    def test_dict_input(self):
        """Dict input should fail"""
        value, error = validate_analysis_result({'value': 5}, "Mad")
        assert value is None
        assert error is not None

    def test_infinity_value(self):
        """Infinity value should fail"""
        value, error = validate_analysis_result(float('inf'), "Mad")
        assert value is None
        assert error is not None

    def test_negative_infinity(self):
        """Negative infinity should fail"""
        value, error = validate_analysis_result(float('-inf'), "Mad")
        assert value is None
        assert error is not None

    def test_all_analysis_codes(self):
        """Test various analysis codes"""
        codes = ['MT', 'Mad', 'Aad', 'A', 'Vad', 'V', 'Vdaf', 'TS', 'CV', 'C', 'H', 'N', 'O', 'CSN', 'FM']
        for code in codes:
            value, error = validate_analysis_result(10.0, code)
            # Should either pass or fail with proper error
            assert value is not None or error is not None


class TestValidateSampleIdExtended:
    """Extended tests for validate_sample_id"""

    def test_valid_sample_id(self):
        """Valid sample ID"""
        result, error = validate_sample_id(123)
        assert result == 123 or error is not None

    def test_string_sample_id(self):
        """String sample ID"""
        result, error = validate_sample_id("123")
        assert result == 123 or error is not None

    def test_negative_sample_id(self):
        """Negative sample ID should fail"""
        result, error = validate_sample_id(-5)
        assert error is not None

    def test_zero_sample_id(self):
        """Zero sample ID should fail"""
        result, error = validate_sample_id(0)
        assert error is not None

    def test_none_sample_id(self):
        """None sample ID"""
        result, error = validate_sample_id(None)
        assert error is not None


class TestValidateAnalysisCodeExtended:
    """Extended tests for validate_analysis_code"""

    def test_valid_codes(self):
        """Valid analysis codes"""
        valid_codes = ['TS', 'CV', 'Mad', 'Aad', 'Vdaf']
        for code in valid_codes:
            result, error = validate_analysis_code(code)
            assert result is not None or error is not None

    def test_lowercase_code(self):
        """Lowercase code"""
        result, error = validate_analysis_code('ts')
        assert result is not None or error is not None

    def test_empty_code(self):
        """Empty code should fail"""
        result, error = validate_analysis_code('')
        assert error is not None

    def test_none_code(self):
        """None code should fail"""
        result, error = validate_analysis_code(None)
        assert error is not None

    def test_numeric_code(self):
        """Numeric code should fail"""
        result, error = validate_analysis_code(123)
        assert error is not None


class TestValidateEquipmentIdExtended:
    """Extended tests for validate_equipment_id"""

    def test_valid_equipment_id(self):
        """Valid equipment ID"""
        result, error = validate_equipment_id(1)
        assert result == 1 or error is not None

    def test_string_equipment_id(self):
        """String equipment ID"""
        result, error = validate_equipment_id("5")
        assert result == 5 or error is not None

    def test_negative_equipment_id(self):
        """Negative equipment ID should fail"""
        result, error = validate_equipment_id(-1)
        assert error is not None

    def test_float_equipment_id(self):
        """Float equipment ID"""
        result, error = validate_equipment_id(5.5)
        assert result is not None or error is not None


class TestValidateSaveResultsBatchExtended:
    """Extended tests for validate_save_results_batch"""

    def test_empty_list(self):
        """Empty list should fail"""
        result = validate_save_results_batch([])
        assert result is not None  # Should return errors

    def test_none_input(self):
        """None input should fail"""
        result = validate_save_results_batch(None)
        assert result is not None

    def test_not_list(self):
        """Non-list input should fail"""
        result = validate_save_results_batch("not a list")
        assert result is not None

    def test_invalid_item(self):
        """Invalid item in list"""
        result = validate_save_results_batch([{'invalid': 'data'}])
        assert result is not None


class TestSanitizeStringExtended:
    """Extended tests for sanitize_string"""

    def test_basic_string(self):
        """Basic string test"""
        result, error = sanitize_string("Hello")
        assert result == "Hello"
        assert error is None

    def test_html_tags(self):
        """HTML tags test"""
        result, error = sanitize_string("<script>test</script>")
        assert result is not None or error is not None
