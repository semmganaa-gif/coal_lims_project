# tests/unit/test_validators.py
"""
Unit tests for app/utils/validators.py

Энэ тестүүд нь input validation-ий зөв ажиллахыг шалгана.
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


class TestValidateAnalysisResult:
    """Tests for validate_analysis_result()"""

    def test_valid_moisture_value(self):
        """Valid moisture value should pass"""
        value, error = validate_analysis_result(5.2, "Mad")
        assert value == 5.2
        assert error is None

    def test_moisture_value_too_high(self):
        """Moisture > 20% should fail"""
        value, error = validate_analysis_result(25.0, "Mad")
        assert value is None
        assert "0.0-20.0" in error

    def test_ash_valid_range(self):
        """Ash within 0-50% should pass"""
        value, error = validate_analysis_result(15.5, "Aad")
        assert value == 15.5
        assert error is None

    def test_ash_out_of_range(self):
        """Ash > 50% should fail"""
        value, error = validate_analysis_result(60.0, "Aad")
        assert value is None
        assert error is not None

    def test_string_to_float_conversion(self):
        """String "5.2" should convert to float"""
        value, error = validate_analysis_result("5.2", "Mad")
        assert value == 5.2
        assert error is None

    def test_comma_decimal_separator(self):
        """Comma as decimal separator should work"""
        value, error = validate_analysis_result("5,2", "Mad")
        assert value == 5.2
        assert error is None

    def test_none_value_allowed(self):
        """None should be allowed when allow_none=True"""
        value, error = validate_analysis_result(None, "Mad", allow_none=True)
        assert value is None
        assert error is None

    def test_none_value_not_allowed(self):
        """None should fail when allow_none=False"""
        value, error = validate_analysis_result(None, "Mad", allow_none=False)
        assert value is None
        assert error == "Үр дүн шаардлагатай"

    def test_invalid_string(self):
        """Invalid string should fail"""
        value, error = validate_analysis_result("abc", "Mad")
        assert value is None
        assert "тоон утга" in error

    def test_calorific_value_range(self):
        """CV 1000-40000 range"""
        value, error = validate_analysis_result(25000, "CV")
        assert value == 25000.0
        assert error is None

    def test_calorific_value_too_low(self):
        """CV < 1000 should fail"""
        value, error = validate_analysis_result(500, "CV")
        assert value is None
        assert error is not None

    def test_unknown_analysis_code_uses_default_range(self):
        """Unknown code should use default range"""
        value, error = validate_analysis_result(5000, "UNKNOWN_CODE")
        assert value == 5000.0
        assert error is None


class TestValidateSampleId:
    """Tests for validate_sample_id()"""

    def test_valid_integer(self):
        """Valid integer should pass"""
        sample_id, error = validate_sample_id(123)
        assert sample_id == 123
        assert error is None

    def test_valid_string_number(self):
        """String "123" should convert"""
        sample_id, error = validate_sample_id("123")
        assert sample_id == 123
        assert error is None

    def test_negative_number(self):
        """Negative number should fail"""
        sample_id, error = validate_sample_id(-5)
        assert sample_id is None
        assert "эерэг тоо" in error

    def test_zero(self):
        """Zero should fail"""
        sample_id, error = validate_sample_id(0)
        assert sample_id is None
        assert error is not None

    def test_none_value(self):
        """None should fail"""
        sample_id, error = validate_sample_id(None)
        assert sample_id is None
        assert "шаардлагатай" in error

    def test_invalid_string(self):
        """Non-numeric string should fail"""
        sample_id, error = validate_sample_id("abc")
        assert sample_id is None
        assert "тоо байх ёстой" in error

    def test_too_large_number(self):
        """Number > INT_MAX should fail"""
        sample_id, error = validate_sample_id(9999999999)
        assert sample_id is None
        assert "хэт том" in error


class TestValidateAnalysisCode:
    """Tests for validate_analysis_code()"""

    def test_valid_simple_code(self):
        """Simple code like "MT" should pass"""
        code, error = validate_analysis_code("MT")
        assert code == "MT"
        assert error is None

    def test_valid_complex_code(self):
        """Complex code like "St,ad" should pass"""
        code, error = validate_analysis_code("St,ad")
        assert code == "St,ad"
        assert error is None

    def test_code_with_whitespace(self):
        """Code with whitespace should be trimmed"""
        code, error = validate_analysis_code("  MT  ")
        assert code == "MT"
        assert error is None

    def test_empty_string(self):
        """Empty string should fail"""
        code, error = validate_analysis_code("")
        assert code is None
        assert "хоосон" in error

    def test_none_value(self):
        """None should fail"""
        code, error = validate_analysis_code(None)
        assert code is None
        assert "шаардлагатай" in error

    def test_too_long_code(self):
        """Code > 20 chars should fail"""
        code, error = validate_analysis_code("A" * 25)
        assert code is None
        assert "хэт урт" in error

    def test_invalid_characters(self):
        """Special chars should fail"""
        code, error = validate_analysis_code("MT<script>")
        assert code is None
        assert error is not None


class TestValidateSaveResultsBatch:
    """Tests for validate_save_results_batch()"""

    def test_valid_batch(self):
        """Valid batch should pass"""
        items = [
            {"sample_id": "1", "analysis_code": "MT", "final_result": "5.2"},
            {"sample_id": "2", "analysis_code": "Aad", "final_result": "10.5"},
        ]
        is_valid, validated, errors = validate_save_results_batch(items)
        assert is_valid
        assert len(validated) == 2
        assert len(errors) == 0

    def test_invalid_sample_id_in_batch(self):
        """Invalid sample_id should produce error"""
        items = [
            {"sample_id": "-1", "analysis_code": "MT", "final_result": "5.2"},
        ]
        is_valid, validated, errors = validate_save_results_batch(items)
        assert not is_valid
        assert len(errors) > 0

    def test_empty_list(self):
        """Empty list should be valid but empty"""
        is_valid, validated, errors = validate_save_results_batch([])
        assert is_valid
        assert len(validated) == 0

    def test_not_a_list(self):
        """Non-list input should fail"""
        is_valid, validated, errors = validate_save_results_batch({"not": "list"})
        assert not is_valid
        assert len(errors) > 0

    def test_item_not_dict(self):
        """Non-dict item should produce error"""
        items = ["not a dict", {"sample_id": "1", "analysis_code": "MT"}]
        is_valid, validated, errors = validate_save_results_batch(items)
        assert not is_valid

    def test_validated_items_structure(self):
        """Validated items should have correct structure"""
        items = [
            {
                "sample_id": "1",
                "analysis_code": "MT",
                "final_result": "5.2",
                "equipment_id": "10",
            },
        ]
        is_valid, validated, errors = validate_save_results_batch(items)
        assert is_valid
        assert validated[0]["sample_id"] == 1
        assert validated[0]["analysis_code"] == "MT"
        assert validated[0]["final_result"] == 5.2
        assert validated[0]["equipment_id"] == 10


class TestSanitizeString:
    """Tests for sanitize_string()"""

    def test_normal_string(self):
        """Normal string should pass"""
        result, error = sanitize_string("Hello World")
        assert result == "Hello World"
        assert error is None

    def test_string_with_whitespace(self):
        """Whitespace should be trimmed"""
        result, error = sanitize_string("  Hello  ")
        assert result == "Hello"
        assert error is None

    def test_none_allowed(self):
        """None should be allowed when allow_none=True"""
        result, error = sanitize_string(None, allow_none=True)
        assert result is None
        assert error is None

    def test_none_not_allowed(self):
        """None should fail when allow_none=False"""
        result, error = sanitize_string(None, allow_none=False)
        assert result is None
        assert "шаардлагатай" in error

    def test_too_long_string(self):
        """String exceeding max_length should fail"""
        long_string = "A" * 1001
        result, error = sanitize_string(long_string, max_length=1000)
        assert result is None
        assert "хэт урт" in error

    def test_xss_script_tag(self):
        """Script tag should be rejected"""
        result, error = sanitize_string("<script>alert('xss')</script>")
        assert result is None
        assert "хориотой" in error

    def test_xss_javascript_protocol(self):
        """javascript: protocol should be rejected"""
        result, error = sanitize_string("javascript:alert(1)")
        assert result is None
        assert error is not None

    def test_xss_onerror_attribute(self):
        """onerror attribute should be rejected"""
        result, error = sanitize_string("<img onerror='alert(1)'>")
        assert result is None
        assert error is not None
