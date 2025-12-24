# tests/test_validators_deep.py
# -*- coding: utf-8 -*-
"""
Deep coverage tests for app/utils/validators.py
"""

import pytest


class TestValidateAnalysisResult:
    """Tests for validate_analysis_result function."""

    def test_valid_moisture_value(self, app):
        """Test valid moisture value."""
        with app.app_context():
            from app.utils.validators import validate_analysis_result
            result, error = validate_analysis_result(5.2, "Mad")
            assert result == 5.2
            assert error is None

    def test_valid_ash_value(self, app):
        """Test valid ash value."""
        with app.app_context():
            from app.utils.validators import validate_analysis_result
            result, error = validate_analysis_result(10.5, "Aad")
            assert result == 10.5
            assert error is None

    def test_value_above_range(self, app):
        """Test value above allowed range."""
        with app.app_context():
            from app.utils.validators import validate_analysis_result
            result, error = validate_analysis_result(50.0, "Mad")
            assert result is None
            assert "хооронд байх ёстой" in error

    def test_value_below_range(self, app):
        """Test value below allowed range."""
        with app.app_context():
            from app.utils.validators import validate_analysis_result
            result, error = validate_analysis_result(-1.0, "Aad")
            assert result is None
            assert "хооронд байх ёстой" in error

    def test_none_value_allowed(self, app):
        """Test None value when allowed."""
        with app.app_context():
            from app.utils.validators import validate_analysis_result
            result, error = validate_analysis_result(None, "MT", allow_none=True)
            assert result is None
            assert error is None

    def test_none_value_not_allowed(self, app):
        """Test None value when not allowed."""
        with app.app_context():
            from app.utils.validators import validate_analysis_result
            result, error = validate_analysis_result(None, "MT", allow_none=False)
            assert result is None
            assert "шаардлагатай" in error

    def test_empty_string_allowed(self, app):
        """Test empty string when allowed."""
        with app.app_context():
            from app.utils.validators import validate_analysis_result
            result, error = validate_analysis_result('', "MT", allow_none=True)
            assert result is None
            assert error is None

    def test_invalid_string_value(self, app):
        """Test invalid string value."""
        with app.app_context():
            from app.utils.validators import validate_analysis_result
            result, error = validate_analysis_result("abc", "Mad")
            assert result is None
            assert "тоон утга" in error

    def test_string_number_value(self, app):
        """Test string number value."""
        with app.app_context():
            from app.utils.validators import validate_analysis_result
            result, error = validate_analysis_result("5.2", "Mad")
            assert result == 5.2
            assert error is None

    def test_comma_decimal_value(self, app):
        """Test comma as decimal separator."""
        with app.app_context():
            from app.utils.validators import validate_analysis_result
            result, error = validate_analysis_result("5,2", "Mad")
            assert result == 5.2
            assert error is None

    def test_integer_value(self, app):
        """Test integer value."""
        with app.app_context():
            from app.utils.validators import validate_analysis_result
            result, error = validate_analysis_result(5, "Mad")
            assert result == 5.0
            assert error is None

    def test_unknown_analysis_code(self, app):
        """Test unknown analysis code uses default range."""
        with app.app_context():
            from app.utils.validators import validate_analysis_result
            result, error = validate_analysis_result(500.0, "UNKNOWN_CODE")
            assert result == 500.0
            assert error is None

    def test_calorific_value_valid(self, app):
        """Test valid calorific value."""
        with app.app_context():
            from app.utils.validators import validate_analysis_result
            result, error = validate_analysis_result(6500, "CV")
            assert result == 6500.0
            assert error is None

    def test_calorific_value_below_range(self, app):
        """Test calorific value below range."""
        with app.app_context():
            from app.utils.validators import validate_analysis_result
            result, error = validate_analysis_result(100, "CV")
            assert result is None
            assert error is not None

    def test_sulfur_value(self, app):
        """Test sulfur value."""
        with app.app_context():
            from app.utils.validators import validate_analysis_result
            result, error = validate_analysis_result(0.5, "TS")
            assert result == 0.5
            assert error is None

    def test_csn_value(self, app):
        """Test CSN value."""
        with app.app_context():
            from app.utils.validators import validate_analysis_result
            result, error = validate_analysis_result(5.5, "CSN")
            assert result == 5.5
            assert error is None

    def test_infinity_value(self, app):
        """Test infinity value rejected."""
        with app.app_context():
            from app.utils.validators import validate_analysis_result
            result, error = validate_analysis_result(float('inf'), "MT")
            assert result is None
            assert "хэт том" in error or error is not None

    def test_wrong_type_list(self, app):
        """Test wrong type (list) rejected."""
        with app.app_context():
            from app.utils.validators import validate_analysis_result
            result, error = validate_analysis_result([1, 2, 3], "MT")
            assert result is None
            assert "буруу төрөл" in error


class TestValidateSampleId:
    """Tests for validate_sample_id function."""

    def test_valid_sample_id(self, app):
        """Test valid sample ID."""
        with app.app_context():
            from app.utils.validators import validate_sample_id
            result, error = validate_sample_id("123")
            assert result == 123
            assert error is None

    def test_valid_integer_sample_id(self, app):
        """Test valid integer sample ID."""
        with app.app_context():
            from app.utils.validators import validate_sample_id
            result, error = validate_sample_id(456)
            assert result == 456
            assert error is None

    def test_none_sample_id(self, app):
        """Test None sample ID."""
        with app.app_context():
            from app.utils.validators import validate_sample_id
            result, error = validate_sample_id(None)
            assert result is None
            assert "шаардлагатай" in error

    def test_negative_sample_id(self, app):
        """Test negative sample ID."""
        with app.app_context():
            from app.utils.validators import validate_sample_id
            result, error = validate_sample_id("-5")
            assert result is None
            assert "эерэг тоо" in error

    def test_zero_sample_id(self, app):
        """Test zero sample ID."""
        with app.app_context():
            from app.utils.validators import validate_sample_id
            result, error = validate_sample_id(0)
            assert result is None
            assert "эерэг тоо" in error

    def test_invalid_string_sample_id(self, app):
        """Test invalid string sample ID."""
        with app.app_context():
            from app.utils.validators import validate_sample_id
            result, error = validate_sample_id("abc")
            assert result is None
            assert "тоо байх ёстой" in error

    def test_very_large_sample_id(self, app):
        """Test very large sample ID."""
        with app.app_context():
            from app.utils.validators import validate_sample_id
            result, error = validate_sample_id(999999999999999)
            assert result is None
            assert "хэт том" in error


class TestValidateAnalysisCode:
    """Tests for validate_analysis_code function."""

    def test_valid_analysis_code(self, app):
        """Test valid analysis code."""
        with app.app_context():
            from app.utils.validators import validate_analysis_code
            result, error = validate_analysis_code("MT")
            assert result == "MT"
            assert error is None

    def test_valid_code_with_comma(self, app):
        """Test valid code with comma."""
        with app.app_context():
            from app.utils.validators import validate_analysis_code
            result, error = validate_analysis_code("St,ad")
            assert result == "St,ad"
            assert error is None

    def test_empty_code(self, app):
        """Test empty analysis code."""
        with app.app_context():
            from app.utils.validators import validate_analysis_code
            result, error = validate_analysis_code("")
            assert result is None
            assert "шаардлагатай" in error

    def test_none_code(self, app):
        """Test None analysis code."""
        with app.app_context():
            from app.utils.validators import validate_analysis_code
            result, error = validate_analysis_code(None)
            assert result is None
            assert "шаардлагатай" in error

    def test_too_long_code(self, app):
        """Test too long analysis code."""
        with app.app_context():
            from app.utils.validators import validate_analysis_code
            result, error = validate_analysis_code("A" * 25)
            assert result is None
            assert "хэт урт" in error

    def test_invalid_characters(self, app):
        """Test code with invalid characters."""
        with app.app_context():
            from app.utils.validators import validate_analysis_code
            result, error = validate_analysis_code("MT@#$")
            assert result is None
            assert "тэмдэгт" in error or "агуулна" in error

    def test_number_code(self, app):
        """Test non-string code."""
        with app.app_context():
            from app.utils.validators import validate_analysis_code
            result, error = validate_analysis_code(123)
            assert result is None
            assert "текст" in error

    def test_code_with_whitespace(self, app):
        """Test code with whitespace."""
        with app.app_context():
            from app.utils.validators import validate_analysis_code
            result, error = validate_analysis_code("  MT  ")
            assert result == "MT"
            assert error is None


class TestValidateEquipmentId:
    """Tests for validate_equipment_id function."""

    def test_valid_equipment_id(self, app):
        """Test valid equipment ID."""
        with app.app_context():
            from app.utils.validators import validate_equipment_id
            result, error = validate_equipment_id(5)
            assert result == 5
            assert error is None

    def test_valid_string_equipment_id(self, app):
        """Test valid string equipment ID."""
        with app.app_context():
            from app.utils.validators import validate_equipment_id
            result, error = validate_equipment_id("10")
            assert result == 10
            assert error is None

    def test_none_allowed(self, app):
        """Test None when allowed."""
        with app.app_context():
            from app.utils.validators import validate_equipment_id
            result, error = validate_equipment_id(None, allow_none=True)
            assert result is None
            assert error is None

    def test_none_not_allowed(self, app):
        """Test None when not allowed."""
        with app.app_context():
            from app.utils.validators import validate_equipment_id
            result, error = validate_equipment_id(None, allow_none=False)
            assert result is None
            assert "шаардлагатай" in error

    def test_empty_string_allowed(self, app):
        """Test empty string when allowed."""
        with app.app_context():
            from app.utils.validators import validate_equipment_id
            result, error = validate_equipment_id('', allow_none=True)
            assert result is None
            assert error is None

    def test_negative_equipment_id(self, app):
        """Test negative equipment ID."""
        with app.app_context():
            from app.utils.validators import validate_equipment_id
            result, error = validate_equipment_id(-1)
            assert result is None
            assert "эерэг тоо" in error

    def test_zero_equipment_id(self, app):
        """Test zero equipment ID."""
        with app.app_context():
            from app.utils.validators import validate_equipment_id
            result, error = validate_equipment_id(0)
            assert result is None
            assert "эерэг тоо" in error

    def test_invalid_equipment_id(self, app):
        """Test invalid equipment ID."""
        with app.app_context():
            from app.utils.validators import validate_equipment_id
            result, error = validate_equipment_id("abc")
            assert result is None
            assert "тоо байх ёстой" in error


class TestValidateSaveResultsBatch:
    """Tests for validate_save_results_batch function."""

    def test_valid_batch(self, app):
        """Test valid batch."""
        with app.app_context():
            from app.utils.validators import validate_save_results_batch
            items = [
                {"sample_id": "1", "analysis_code": "MT", "final_result": "5.2"}
            ]
            is_valid, validated, errors = validate_save_results_batch(items)
            assert len(validated) == 1
            assert validated[0]['sample_id'] == 1
            assert validated[0]['analysis_code'] == "MT"

    def test_invalid_sample_id_in_batch(self, app):
        """Test batch with invalid sample ID."""
        with app.app_context():
            from app.utils.validators import validate_save_results_batch
            items = [
                {"sample_id": "abc", "analysis_code": "MT", "final_result": "5.2"}
            ]
            is_valid, validated, errors = validate_save_results_batch(items)
            assert len(errors) > 0

    def test_invalid_analysis_code_in_batch(self, app):
        """Test batch with invalid analysis code."""
        with app.app_context():
            from app.utils.validators import validate_save_results_batch
            items = [
                {"sample_id": "1", "analysis_code": "", "final_result": "5.2"}
            ]
            is_valid, validated, errors = validate_save_results_batch(items)
            assert len(errors) > 0

    def test_not_list_input(self, app):
        """Test non-list input."""
        with app.app_context():
            from app.utils.validators import validate_save_results_batch
            is_valid, validated, errors = validate_save_results_batch("not a list")
            assert is_valid is False
            assert len(errors) > 0

    def test_non_dict_item(self, app):
        """Test non-dict item in batch."""
        with app.app_context():
            from app.utils.validators import validate_save_results_batch
            items = ["not a dict"]
            is_valid, validated, errors = validate_save_results_batch(items)
            assert len(errors) > 0

    def test_batch_with_equipment_id(self, app):
        """Test batch with equipment ID."""
        with app.app_context():
            from app.utils.validators import validate_save_results_batch
            items = [
                {"sample_id": "1", "analysis_code": "MT", "final_result": "5.2", "equipment_id": "1"}
            ]
            is_valid, validated, errors = validate_save_results_batch(items)
            assert len(validated) == 1


class TestAnalysisValueRanges:
    """Tests for ANALYSIS_VALUE_RANGES constant."""

    def test_ranges_exist(self, app):
        """Test ANALYSIS_VALUE_RANGES exists."""
        with app.app_context():
            from app.utils.validators import ANALYSIS_VALUE_RANGES
            assert isinstance(ANALYSIS_VALUE_RANGES, dict)
            assert len(ANALYSIS_VALUE_RANGES) > 0

    def test_mt_range(self, app):
        """Test MT range."""
        with app.app_context():
            from app.utils.validators import ANALYSIS_VALUE_RANGES
            assert 'MT' in ANALYSIS_VALUE_RANGES
            min_val, max_val = ANALYSIS_VALUE_RANGES['MT']
            assert min_val < max_val

    def test_aad_range(self, app):
        """Test Aad range."""
        with app.app_context():
            from app.utils.validators import ANALYSIS_VALUE_RANGES
            assert 'Aad' in ANALYSIS_VALUE_RANGES

    def test_cv_range(self, app):
        """Test CV range."""
        with app.app_context():
            from app.utils.validators import ANALYSIS_VALUE_RANGES
            assert 'CV' in ANALYSIS_VALUE_RANGES

    def test_default_range(self, app):
        """Test DEFAULT_RANGE constant."""
        with app.app_context():
            from app.utils.validators import DEFAULT_RANGE
            assert isinstance(DEFAULT_RANGE, tuple)
            assert len(DEFAULT_RANGE) == 2
