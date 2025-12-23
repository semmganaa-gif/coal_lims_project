# tests/unit/test_validators_more.py
# -*- coding: utf-8 -*-
"""
Validators utility additional tests
"""
import pytest
from app.utils.validators import (
    validate_sample_id,
    validate_analysis_code,
    validate_analysis_result,
    validate_equipment_id,
    validate_save_results_batch,
    validate_csn_values,
    round_to_half,
    get_csn_repeatability_limit,
    sanitize_string,
    ANALYSIS_VALUE_RANGES,
    DEFAULT_RANGE,
)


class TestValidateSampleId:
    """validate_sample_id() функцийн тестүүд"""

    def test_valid_sample_id(self):
        """Valid positive integer should pass"""
        sample_id, err = validate_sample_id(1)
        assert sample_id == 1
        assert err is None

        sample_id, err = validate_sample_id(100)
        assert sample_id == 100
        assert err is None

    def test_string_number_converts(self):
        """String number should convert to int"""
        sample_id, err = validate_sample_id("5")
        assert sample_id == 5
        assert err is None

        sample_id, err = validate_sample_id("100")
        assert sample_id == 100
        assert err is None

    def test_none_returns_error(self):
        """None should return error message"""
        sample_id, err = validate_sample_id(None)
        assert sample_id is None
        assert err is not None
        assert "шаардлагатай" in err

    def test_zero_returns_error(self):
        """Zero should return error message"""
        sample_id, err = validate_sample_id(0)
        assert sample_id is None
        assert err is not None
        assert "эерэг" in err

    def test_negative_returns_error(self):
        """Negative number should return error message"""
        sample_id, err = validate_sample_id(-1)
        assert sample_id is None
        assert err is not None

    def test_invalid_string_returns_error(self):
        """Non-numeric string should return error message"""
        sample_id, err = validate_sample_id("abc")
        assert sample_id is None
        assert err is not None

    def test_very_large_number_returns_error(self):
        """Very large number should return error"""
        sample_id, err = validate_sample_id(999999999999)
        assert sample_id is None
        assert err is not None
        assert "хэт том" in err


class TestValidateAnalysisCode:
    """validate_analysis_code() функцийн тестүүд"""

    def test_valid_codes(self):
        """Valid analysis codes should pass"""
        code, err = validate_analysis_code("Mad")
        assert code == "Mad"
        assert err is None

        code, err = validate_analysis_code("TS")
        assert code == "TS"
        assert err is None

        code, err = validate_analysis_code("CV")
        assert code == "CV"
        assert err is None

    def test_strips_whitespace(self):
        """Whitespace should be stripped"""
        code, err = validate_analysis_code("  Mad  ")
        assert code == "Mad"
        assert err is None

    def test_none_returns_error(self):
        """None should return error message"""
        code, err = validate_analysis_code(None)
        assert code is None
        assert err is not None

    def test_empty_string_returns_error(self):
        """Empty string should return error message"""
        code, err = validate_analysis_code("")
        assert code is None
        assert err is not None

    def test_whitespace_only_returns_error(self):
        """Whitespace-only string should return error message"""
        code, err = validate_analysis_code("   ")
        assert code is None
        assert err is not None
        assert "хоосон" in err

    def test_too_long_code_returns_error(self):
        """Too long code should return error"""
        code, err = validate_analysis_code("A" * 25)
        assert code is None
        assert err is not None
        assert "урт" in err

    def test_invalid_characters_returns_error(self):
        """Invalid characters should return error"""
        code, err = validate_analysis_code("Mad@#$")
        assert code is None
        assert err is not None

    def test_non_string_returns_error(self):
        """Non-string type should return error"""
        code, err = validate_analysis_code(123)
        assert code is None
        assert err is not None


class TestValidateAnalysisResult:
    """validate_analysis_result() функцийн тестүүд"""

    def test_valid_float(self):
        """Valid float should pass"""
        value, err = validate_analysis_result(8.5, "Mad")
        assert value == 8.5
        assert err is None

    def test_valid_int(self):
        """Valid int should convert to float"""
        value, err = validate_analysis_result(10, "Mad")
        assert value == 10.0
        assert err is None

    def test_valid_string_number(self):
        """Valid string number should convert"""
        value, err = validate_analysis_result("8.5", "Mad")
        assert value == 8.5
        assert err is None

    def test_string_with_comma(self):
        """String with comma should convert"""
        value, err = validate_analysis_result("8,5", "Mad")
        assert value == 8.5
        assert err is None

    def test_none_returns_none_when_allowed(self):
        """None should return None when allowed"""
        value, err = validate_analysis_result(None, "Mad", allow_none=True)
        assert value is None
        assert err is None

    def test_none_returns_error_when_not_allowed(self):
        """None should return error when not allowed"""
        value, err = validate_analysis_result(None, "Mad", allow_none=False)
        assert value is None
        assert err is not None

    def test_empty_string_returns_none(self):
        """Empty string should return None"""
        value, err = validate_analysis_result("", "Mad")
        assert value is None
        assert err is None

    def test_invalid_string_returns_error(self):
        """Invalid string should return error"""
        value, err = validate_analysis_result("not a number", "Mad")
        assert value is None
        assert err is not None

    def test_out_of_range_returns_error(self):
        """Out of range value should return error"""
        # Mad range is 0.2-30.0
        value, err = validate_analysis_result(50.0, "Mad")
        assert value is None
        assert err is not None
        assert "хооронд" in err

    def test_unknown_code_uses_default_range(self):
        """Unknown code should use default range"""
        value, err = validate_analysis_result(100.0, "UNKNOWN_CODE")
        assert value == 100.0
        assert err is None

    def test_invalid_type_returns_error(self):
        """Invalid type should return error"""
        value, err = validate_analysis_result([1, 2, 3], "Mad")
        assert value is None
        assert err is not None


class TestValidateEquipmentId:
    """validate_equipment_id() функцийн тестүүд"""

    def test_valid_equipment_id(self):
        """Valid equipment id should pass"""
        eq_id, err = validate_equipment_id(1)
        assert eq_id == 1
        assert err is None

    def test_string_number_converts(self):
        """String number should convert"""
        eq_id, err = validate_equipment_id("5")
        assert eq_id == 5
        assert err is None

    def test_none_returns_none_when_allowed(self):
        """None should return None when allowed"""
        eq_id, err = validate_equipment_id(None, allow_none=True)
        assert eq_id is None
        assert err is None

    def test_none_returns_error_when_not_allowed(self):
        """None should return error when not allowed"""
        eq_id, err = validate_equipment_id(None, allow_none=False)
        assert eq_id is None
        assert err is not None

    def test_zero_returns_error(self):
        """Zero should return error"""
        eq_id, err = validate_equipment_id(0, allow_none=False)
        assert eq_id is None
        assert err is not None

    def test_negative_returns_error(self):
        """Negative should return error"""
        eq_id, err = validate_equipment_id(-1)
        assert eq_id is None
        assert err is not None

    def test_empty_string_returns_none_when_allowed(self):
        """Empty string should return None when allowed"""
        eq_id, err = validate_equipment_id("", allow_none=True)
        assert eq_id is None
        assert err is None


class TestValidateSaveResultsBatch:
    """validate_save_results_batch() функцийн тестүүд"""

    def test_valid_batch(self):
        """Valid batch data should pass"""
        items = [
            {"sample_id": 1, "analysis_code": "Mad", "final_result": "8.5"},
            {"sample_id": 2, "analysis_code": "TS", "final_result": "0.5"}
        ]
        is_valid, validated, errors = validate_save_results_batch(items)
        assert len(validated) == 2
        assert validated[0]["sample_id"] == 1

    def test_empty_list_returns_valid(self):
        """Empty list should return valid"""
        is_valid, validated, errors = validate_save_results_batch([])
        assert is_valid is True
        assert validated == []

    def test_non_list_returns_error(self):
        """Non-list should return error"""
        is_valid, validated, errors = validate_save_results_batch("not a list")
        assert is_valid is False
        assert "array" in errors[0]

    def test_non_dict_item_returns_error(self):
        """Non-dict item should return error"""
        is_valid, validated, errors = validate_save_results_batch(["string"])
        assert is_valid is False
        assert "Dictionary" in errors[0]

    def test_missing_sample_id_returns_error(self):
        """Missing sample_id should return error"""
        items = [{"analysis_code": "Mad", "final_result": "8.5"}]
        is_valid, validated, errors = validate_save_results_batch(items)
        assert len(errors) > 0

    def test_missing_analysis_code_returns_error(self):
        """Missing analysis_code should return error"""
        items = [{"sample_id": 1, "final_result": "8.5"}]
        is_valid, validated, errors = validate_save_results_batch(items)
        assert len(errors) > 0

    def test_preserves_optional_fields(self):
        """Optional fields should be preserved"""
        items = [{
            "sample_id": 1,
            "analysis_code": "Mad",
            "final_result": "8.5",
            "status": "approved",
            "notes": "Test note"
        }]
        is_valid, validated, errors = validate_save_results_batch(items)
        assert validated[0]["status"] == "approved"
        assert validated[0]["notes"] == "Test note"


class TestValidateCsnValues:
    """validate_csn_values() функцийн тестүүд"""

    def test_valid_two_values(self):
        """Two valid values should pass"""
        is_valid, result, errors = validate_csn_values([2.0, 2.5])
        assert is_valid is True
        assert result is not None
        assert result["values_count"] == 2

    def test_valid_five_values(self):
        """Five valid values should pass"""
        is_valid, result, errors = validate_csn_values([2.0, 2.5, 2.5, 2.0, 2.5])
        assert is_valid is True
        assert result["values_count"] == 5

    def test_less_than_two_values_fails(self):
        """Less than two values should fail"""
        is_valid, result, errors = validate_csn_values([2.0])
        assert is_valid is False
        assert "2 утга" in errors[0]

    def test_none_values_ignored(self):
        """None values should be ignored"""
        is_valid, result, errors = validate_csn_values([2.0, None, 2.5, None, None])
        assert is_valid is True
        assert result["values_count"] == 2

    def test_empty_values_ignored(self):
        """Empty string values should be ignored"""
        is_valid, result, errors = validate_csn_values([2.0, "", 2.5, "", ""])
        assert is_valid is True
        assert result["values_count"] == 2

    def test_invalid_value_adds_error(self):
        """Invalid value should add error"""
        is_valid, result, errors = validate_csn_values([2.0, "abc", 2.5])
        assert any("буруу" in e for e in errors)

    def test_exceeded_range_adds_warning(self):
        """Exceeded range should add warning but still be valid"""
        is_valid, result, errors = validate_csn_values([1.0, 5.0])  # Range = 4.0
        assert is_valid is True  # Still valid because 2 values
        assert result["exceeded"] is True
        assert any("давсан" in e for e in errors)

    def test_calculates_average_correctly(self):
        """Average should be calculated correctly"""
        is_valid, result, errors = validate_csn_values([2.0, 3.0])
        assert result["raw_avg"] == 2.5

    def test_rounds_to_half(self):
        """Result should be rounded to 0.5"""
        is_valid, result, errors = validate_csn_values([2.0, 2.3])
        # Raw avg = 2.15, rounded to 0.5 = 2.0
        assert result["avg"] in [2.0, 2.5]


class TestRoundToHalf:
    """round_to_half() функцийн тестүүд"""

    def test_round_down(self):
        """Values below .25 should round down"""
        assert round_to_half(2.1) == 2.0
        assert round_to_half(2.2) == 2.0

    def test_round_to_half(self):
        """Values around .5 should round to .5"""
        assert round_to_half(2.3) == 2.5
        assert round_to_half(2.5) == 2.5
        assert round_to_half(2.7) == 2.5

    def test_round_up(self):
        """Values above .75 should round up"""
        assert round_to_half(2.8) == 3.0
        assert round_to_half(2.9) == 3.0

    def test_exact_values(self):
        """Exact 0.5 increments should remain unchanged"""
        assert round_to_half(0.0) == 0.0
        assert round_to_half(0.5) == 0.5
        assert round_to_half(1.0) == 1.0
        assert round_to_half(1.5) == 1.5


class TestGetCsnRepeatabilityLimit:
    """get_csn_repeatability_limit() функцийн тестүүд"""

    def test_returns_float(self):
        """Should return a float"""
        result = get_csn_repeatability_limit()
        assert isinstance(result, float)

    def test_returns_positive(self):
        """Should return positive value"""
        result = get_csn_repeatability_limit()
        assert result > 0


class TestSanitizeString:
    """sanitize_string() функцийн тестүүд"""

    def test_valid_string_passes(self):
        """Valid string should pass"""
        result, err = sanitize_string("Hello World")
        assert result == "Hello World"
        assert err is None

    def test_strips_whitespace(self):
        """Whitespace should be stripped"""
        result, err = sanitize_string("  Hello  ")
        assert result == "Hello"
        assert err is None

    def test_none_returns_none_when_allowed(self):
        """None should return None when allowed"""
        result, err = sanitize_string(None, allow_none=True)
        assert result is None
        assert err is None

    def test_none_returns_error_when_not_allowed(self):
        """None should return error when not allowed"""
        result, err = sanitize_string(None, allow_none=False)
        assert result is None
        assert err is not None

    def test_empty_string_returns_none_when_allowed(self):
        """Empty string should return None when allowed"""
        result, err = sanitize_string("", allow_none=True)
        assert result is None
        assert err is None

    def test_too_long_returns_error(self):
        """Too long string should return error"""
        result, err = sanitize_string("A" * 1001, max_length=1000)
        assert result is None
        assert err is not None
        assert "урт" in err

    def test_script_tag_blocked(self):
        """Script tag should be blocked"""
        result, err = sanitize_string("<script>alert('xss')</script>")
        assert result is None
        assert err is not None
        assert "Хориотой" in err

    def test_javascript_protocol_blocked(self):
        """JavaScript protocol should be blocked"""
        result, err = sanitize_string("javascript:alert('xss')")
        assert result is None
        assert err is not None

    def test_event_handlers_blocked(self):
        """Event handlers should be blocked"""
        result, err = sanitize_string("<img onerror='alert(1)'>")
        assert result is None
        assert err is not None

    def test_onclick_blocked(self):
        """onclick handler should be blocked"""
        result, err = sanitize_string("<div onclick='alert(1)'>")
        assert result is None
        assert err is not None

    def test_non_string_converts(self):
        """Non-string should be converted"""
        result, err = sanitize_string(123)
        assert result == "123"
        assert err is None


class TestAnalysisValueRanges:
    """ANALYSIS_VALUE_RANGES constant tests"""

    def test_contains_common_codes(self):
        """Should contain common analysis codes"""
        assert "MT" in ANALYSIS_VALUE_RANGES
        assert "Mad" in ANALYSIS_VALUE_RANGES
        assert "Aad" in ANALYSIS_VALUE_RANGES
        assert "TS" in ANALYSIS_VALUE_RANGES
        assert "CV" in ANALYSIS_VALUE_RANGES
        assert "CSN" in ANALYSIS_VALUE_RANGES

    def test_ranges_are_tuples(self):
        """All ranges should be tuples"""
        for code, range_val in ANALYSIS_VALUE_RANGES.items():
            assert isinstance(range_val, tuple)
            assert len(range_val) == 2

    def test_min_less_than_max(self):
        """Min should be less than max for all ranges"""
        for code, (min_val, max_val) in ANALYSIS_VALUE_RANGES.items():
            assert min_val <= max_val, f"{code}: min ({min_val}) > max ({max_val})"


class TestDefaultRange:
    """DEFAULT_RANGE constant tests"""

    def test_default_range_is_tuple(self):
        """Default range should be tuple"""
        assert isinstance(DEFAULT_RANGE, tuple)
        assert len(DEFAULT_RANGE) == 2

    def test_default_range_is_wide(self):
        """Default range should be very wide"""
        min_val, max_val = DEFAULT_RANGE
        assert max_val - min_val > 100000
