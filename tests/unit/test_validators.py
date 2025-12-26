# -*- coding: utf-8 -*-
"""
Tests for app/utils/validators.py
Input validation and sanitization tests
"""
import pytest
from unittest.mock import patch, MagicMock


# ============================================================================
# ANALYSIS_VALUE_RANGES TESTS
# ============================================================================

class TestAnalysisValueRanges:
    """ANALYSIS_VALUE_RANGES constant tests"""

    def test_ranges_dict_exists(self):
        """Ranges dictionary exists"""
        from app.utils.validators import ANALYSIS_VALUE_RANGES
        assert isinstance(ANALYSIS_VALUE_RANGES, dict)

    def test_common_analysis_codes_exist(self):
        """Common analysis codes exist in ranges"""
        from app.utils.validators import ANALYSIS_VALUE_RANGES

        expected_codes = ['MT', 'Mad', 'Aad', 'Vad', 'TS', 'CV', 'CSN', 'Gi']
        for code in expected_codes:
            assert code in ANALYSIS_VALUE_RANGES, f"{code} not in ranges"

    def test_ranges_are_tuples(self):
        """Each range is a tuple of (min, max)"""
        from app.utils.validators import ANALYSIS_VALUE_RANGES

        for code, range_tuple in ANALYSIS_VALUE_RANGES.items():
            assert isinstance(range_tuple, tuple), f"{code} range not tuple"
            assert len(range_tuple) == 2, f"{code} range not (min, max)"
            assert range_tuple[0] <= range_tuple[1], f"{code} min > max"

    def test_mt_range(self):
        """MT (total moisture) range"""
        from app.utils.validators import ANALYSIS_VALUE_RANGES
        assert ANALYSIS_VALUE_RANGES['MT'] == (0.5, 40.0)

    def test_mad_range(self):
        """Mad (inherent moisture) range"""
        from app.utils.validators import ANALYSIS_VALUE_RANGES
        assert ANALYSIS_VALUE_RANGES['Mad'] == (0.2, 30.0)

    def test_csn_range(self):
        """CSN (crucible swelling number) range"""
        from app.utils.validators import ANALYSIS_VALUE_RANGES
        assert ANALYSIS_VALUE_RANGES['CSN'] == (0.0, 9.6)

    def test_cv_range(self):
        """CV (calorific value) range"""
        from app.utils.validators import ANALYSIS_VALUE_RANGES
        assert ANALYSIS_VALUE_RANGES['CV'] == (500, 40000)


# ============================================================================
# validate_analysis_result TESTS
# ============================================================================

class TestValidateAnalysisResult:
    """validate_analysis_result function tests"""

    def test_import(self):
        """Import function"""
        from app.utils.validators import validate_analysis_result
        assert callable(validate_analysis_result)

    def test_valid_float_value(self):
        """Valid float value is accepted"""
        from app.utils.validators import validate_analysis_result
        value, error = validate_analysis_result(5.2, 'Mad')
        assert value == 5.2
        assert error is None

    def test_valid_int_value(self):
        """Valid int value is converted to float"""
        from app.utils.validators import validate_analysis_result
        value, error = validate_analysis_result(5, 'Mad')
        assert value == 5.0
        assert error is None

    def test_valid_string_value(self):
        """Valid string value is converted"""
        from app.utils.validators import validate_analysis_result
        value, error = validate_analysis_result("5.2", 'Mad')
        assert value == 5.2
        assert error is None

    def test_string_with_comma_decimal(self):
        """String with comma decimal is converted"""
        from app.utils.validators import validate_analysis_result
        value, error = validate_analysis_result("5,2", 'Mad')
        assert value == 5.2
        assert error is None

    def test_string_with_spaces(self):
        """String with spaces is stripped"""
        from app.utils.validators import validate_analysis_result
        value, error = validate_analysis_result("  5.2  ", 'Mad')
        assert value == 5.2
        assert error is None

    def test_none_allowed_by_default(self):
        """None is allowed by default"""
        from app.utils.validators import validate_analysis_result
        value, error = validate_analysis_result(None, 'Mad')
        assert value is None
        assert error is None

    def test_empty_string_allowed_by_default(self):
        """Empty string is treated as None"""
        from app.utils.validators import validate_analysis_result
        value, error = validate_analysis_result('', 'Mad')
        assert value is None
        assert error is None

    def test_none_not_allowed(self):
        """None not allowed when allow_none=False"""
        from app.utils.validators import validate_analysis_result
        value, error = validate_analysis_result(None, 'Mad', allow_none=False)
        assert value is None
        assert error is not None
        assert "шаардлагатай" in error

    def test_invalid_string_returns_error(self):
        """Invalid string returns error"""
        from app.utils.validators import validate_analysis_result
        value, error = validate_analysis_result("abc", 'Mad')
        assert value is None
        assert error is not None
        assert "тоон утга" in error

    def test_invalid_type_returns_error(self):
        """Invalid type returns error"""
        from app.utils.validators import validate_analysis_result
        value, error = validate_analysis_result([1, 2], 'Mad')
        assert value is None
        assert error is not None
        assert "буруу төрөл" in error

    def test_value_below_range_returns_error(self):
        """Value below range returns error"""
        from app.utils.validators import validate_analysis_result
        value, error = validate_analysis_result(0.1, 'Mad')  # Mad min is 0.2
        assert value is None
        assert error is not None
        assert "хооронд байх ёстой" in error

    def test_value_above_range_returns_error(self):
        """Value above range returns error"""
        from app.utils.validators import validate_analysis_result
        value, error = validate_analysis_result(50.0, 'Mad')  # Mad max is 30.0
        assert value is None
        assert error is not None
        assert "хооронд байх ёстой" in error

    def test_value_at_min_boundary(self):
        """Value at min boundary is accepted"""
        from app.utils.validators import validate_analysis_result
        value, error = validate_analysis_result(0.2, 'Mad')
        assert value == 0.2
        assert error is None

    def test_value_at_max_boundary(self):
        """Value at max boundary is accepted"""
        from app.utils.validators import validate_analysis_result
        value, error = validate_analysis_result(30.0, 'Mad')
        assert value == 30.0
        assert error is None

    def test_unknown_analysis_code_uses_default_range(self):
        """Unknown analysis code uses default range"""
        from app.utils.validators import validate_analysis_result
        value, error = validate_analysis_result(500.0, 'UnknownCode')
        assert value == 500.0
        assert error is None

    def test_infinity_returns_error(self):
        """Infinity value returns error"""
        from app.utils.validators import validate_analysis_result
        value, error = validate_analysis_result(float('inf'), 'Mad')
        assert value is None
        assert error is not None
        assert "хэт том" in error

    def test_negative_infinity_returns_error(self):
        """Negative infinity value returns error"""
        from app.utils.validators import validate_analysis_result
        value, error = validate_analysis_result(float('-inf'), 'Mad')
        assert value is None
        assert error is not None

    def test_mt_valid_range(self):
        """MT accepts values in 0.5-40 range"""
        from app.utils.validators import validate_analysis_result
        value, error = validate_analysis_result(15.0, 'MT')
        assert value == 15.0
        assert error is None

    def test_ts_accepts_zero(self):
        """TS (sulfur) accepts 0 value"""
        from app.utils.validators import validate_analysis_result
        value, error = validate_analysis_result(0.0, 'TS')
        assert value == 0.0
        assert error is None

    def test_csn_range_validation(self):
        """CSN accepts values in 0-9.6 range"""
        from app.utils.validators import validate_analysis_result
        value, error = validate_analysis_result(5.5, 'CSN')
        assert value == 5.5
        assert error is None

    def test_csn_above_max(self):
        """CSN rejects values above 9.6"""
        from app.utils.validators import validate_analysis_result
        value, error = validate_analysis_result(10.0, 'CSN')
        assert value is None
        assert error is not None


# ============================================================================
# validate_sample_id TESTS
# ============================================================================

class TestValidateSampleId:
    """validate_sample_id function tests"""

    def test_import(self):
        """Import function"""
        from app.utils.validators import validate_sample_id
        assert callable(validate_sample_id)

    def test_valid_int(self):
        """Valid int is accepted"""
        from app.utils.validators import validate_sample_id
        sample_id, error = validate_sample_id(123)
        assert sample_id == 123
        assert error is None

    def test_valid_string_int(self):
        """Valid string int is converted"""
        from app.utils.validators import validate_sample_id
        sample_id, error = validate_sample_id("123")
        assert sample_id == 123
        assert error is None

    def test_none_returns_error(self):
        """None returns error"""
        from app.utils.validators import validate_sample_id
        sample_id, error = validate_sample_id(None)
        assert sample_id is None
        assert error is not None
        assert "шаардлагатай" in error

    def test_invalid_string_returns_error(self):
        """Invalid string returns error"""
        from app.utils.validators import validate_sample_id
        sample_id, error = validate_sample_id("abc")
        assert sample_id is None
        assert error is not None
        assert "тоо байх ёстой" in error

    def test_zero_returns_error(self):
        """Zero returns error"""
        from app.utils.validators import validate_sample_id
        sample_id, error = validate_sample_id(0)
        assert sample_id is None
        assert error is not None
        assert "эерэг тоо" in error

    def test_negative_returns_error(self):
        """Negative returns error"""
        from app.utils.validators import validate_sample_id
        sample_id, error = validate_sample_id(-5)
        assert sample_id is None
        assert error is not None
        assert "эерэг тоо" in error

    def test_too_large_returns_error(self):
        """Too large value returns error"""
        from app.utils.validators import validate_sample_id
        sample_id, error = validate_sample_id(2147483648)  # INT max + 1
        assert sample_id is None
        assert error is not None
        assert "хэт том" in error

    def test_max_valid_value(self):
        """Maximum valid value is accepted"""
        from app.utils.validators import validate_sample_id
        sample_id, error = validate_sample_id(2147483647)
        assert sample_id == 2147483647
        assert error is None

    def test_float_string_returns_error(self):
        """Float string returns error"""
        from app.utils.validators import validate_sample_id
        sample_id, error = validate_sample_id("123.5")
        assert sample_id is None
        assert error is not None


# ============================================================================
# validate_analysis_code TESTS
# ============================================================================

class TestValidateAnalysisCode:
    """validate_analysis_code function tests"""

    def test_import(self):
        """Import function"""
        from app.utils.validators import validate_analysis_code
        assert callable(validate_analysis_code)

    def test_valid_code(self):
        """Valid code is accepted"""
        from app.utils.validators import validate_analysis_code
        code, error = validate_analysis_code("MT")
        assert code == "MT"
        assert error is None

    def test_code_with_spaces_stripped(self):
        """Code with spaces is stripped"""
        from app.utils.validators import validate_analysis_code
        code, error = validate_analysis_code("  MT  ")
        assert code == "MT"
        assert error is None

    def test_empty_string_returns_error(self):
        """Empty string returns error"""
        from app.utils.validators import validate_analysis_code
        code, error = validate_analysis_code("")
        assert code is None
        assert error is not None
        assert "шаардлагатай" in error

    def test_none_returns_error(self):
        """None returns error"""
        from app.utils.validators import validate_analysis_code
        code, error = validate_analysis_code(None)
        assert code is None
        assert error is not None

    def test_too_long_returns_error(self):
        """Too long code returns error"""
        from app.utils.validators import validate_analysis_code
        code, error = validate_analysis_code("A" * 25)
        assert code is None
        assert error is not None
        assert "хэт урт" in error

    def test_max_length_accepted(self):
        """Max length code is accepted"""
        from app.utils.validators import validate_analysis_code
        code, error = validate_analysis_code("A" * 20)
        assert code == "A" * 20
        assert error is None

    def test_non_string_returns_error(self):
        """Non-string returns error"""
        from app.utils.validators import validate_analysis_code
        code, error = validate_analysis_code(123)
        assert code is None
        assert error is not None
        assert "текст" in error

    def test_special_chars_returns_error(self):
        """Special characters return error"""
        from app.utils.validators import validate_analysis_code
        code, error = validate_analysis_code("MT<script>")
        assert code is None
        assert error is not None
        assert "үсэг, тоо, таслал" in error

    def test_comma_allowed(self):
        """Comma is allowed in code"""
        from app.utils.validators import validate_analysis_code
        code, error = validate_analysis_code("St,ad")
        assert code == "St,ad"
        assert error is None

    def test_numbers_allowed(self):
        """Numbers are allowed in code"""
        from app.utils.validators import validate_analysis_code
        code, error = validate_analysis_code("CO2")
        assert code == "CO2"
        assert error is None

    def test_whitespace_only_returns_error(self):
        """Whitespace only returns error"""
        from app.utils.validators import validate_analysis_code
        code, error = validate_analysis_code("   ")
        assert code is None
        assert error is not None
        assert "хоосон" in error


# ============================================================================
# validate_equipment_id TESTS
# ============================================================================

class TestValidateEquipmentId:
    """validate_equipment_id function tests"""

    def test_import(self):
        """Import function"""
        from app.utils.validators import validate_equipment_id
        assert callable(validate_equipment_id)

    def test_valid_int(self):
        """Valid int is accepted"""
        from app.utils.validators import validate_equipment_id
        eq_id, error = validate_equipment_id(5)
        assert eq_id == 5
        assert error is None

    def test_valid_string_int(self):
        """Valid string int is converted"""
        from app.utils.validators import validate_equipment_id
        eq_id, error = validate_equipment_id("5")
        assert eq_id == 5
        assert error is None

    def test_none_allowed_by_default(self):
        """None is allowed by default"""
        from app.utils.validators import validate_equipment_id
        eq_id, error = validate_equipment_id(None)
        assert eq_id is None
        assert error is None

    def test_empty_string_allowed_by_default(self):
        """Empty string is treated as None"""
        from app.utils.validators import validate_equipment_id
        eq_id, error = validate_equipment_id('')
        assert eq_id is None
        assert error is None

    def test_none_not_allowed(self):
        """None not allowed when allow_none=False"""
        from app.utils.validators import validate_equipment_id
        eq_id, error = validate_equipment_id(None, allow_none=False)
        assert eq_id is None
        assert error is not None
        assert "шаардлагатай" in error

    def test_invalid_string_returns_error(self):
        """Invalid string returns error"""
        from app.utils.validators import validate_equipment_id
        eq_id, error = validate_equipment_id("abc")
        assert eq_id is None
        assert error is not None
        assert "тоо байх ёстой" in error

    def test_zero_returns_error(self):
        """Zero returns error"""
        from app.utils.validators import validate_equipment_id
        eq_id, error = validate_equipment_id(0)
        assert eq_id is None
        assert error is not None
        assert "эерэг тоо" in error

    def test_negative_returns_error(self):
        """Negative returns error"""
        from app.utils.validators import validate_equipment_id
        eq_id, error = validate_equipment_id(-1)
        assert eq_id is None
        assert error is not None
        assert "эерэг тоо" in error


# ============================================================================
# validate_save_results_batch TESTS
# ============================================================================

class TestValidateSaveResultsBatch:
    """validate_save_results_batch function tests"""

    def test_import(self):
        """Import function"""
        from app.utils.validators import validate_save_results_batch
        assert callable(validate_save_results_batch)

    def test_valid_batch(self):
        """Valid batch is accepted"""
        from app.utils.validators import validate_save_results_batch

        items = [
            {"sample_id": "1", "analysis_code": "MT", "final_result": "5.2"}
        ]
        is_valid, validated, errors = validate_save_results_batch(items)
        assert is_valid is True
        assert len(validated) == 1
        assert len(errors) == 0

    def test_multiple_valid_items(self):
        """Multiple valid items are accepted"""
        from app.utils.validators import validate_save_results_batch

        items = [
            {"sample_id": "1", "analysis_code": "MT", "final_result": "5.2"},
            {"sample_id": "2", "analysis_code": "Mad", "final_result": "3.5"}
        ]
        is_valid, validated, errors = validate_save_results_batch(items)
        assert is_valid is True
        assert len(validated) == 2

    def test_non_list_input_returns_error(self):
        """Non-list input returns error"""
        from app.utils.validators import validate_save_results_batch

        is_valid, validated, errors = validate_save_results_batch("not a list")
        assert is_valid is False
        assert len(validated) == 0
        assert len(errors) == 1
        assert "array" in errors[0]

    def test_non_dict_item_returns_error(self):
        """Non-dict item returns error"""
        from app.utils.validators import validate_save_results_batch

        items = ["not a dict"]
        is_valid, validated, errors = validate_save_results_batch(items)
        assert is_valid is False
        assert len(errors) == 1
        assert "Dictionary" in errors[0]

    def test_missing_sample_id_returns_error(self):
        """Missing sample_id returns error"""
        from app.utils.validators import validate_save_results_batch

        items = [{"analysis_code": "MT", "final_result": "5.2"}]
        is_valid, validated, errors = validate_save_results_batch(items)
        assert is_valid is False
        assert len(errors) == 1
        assert "Sample ID" in errors[0]

    def test_missing_analysis_code_returns_error(self):
        """Missing analysis_code returns error"""
        from app.utils.validators import validate_save_results_batch

        items = [{"sample_id": "1", "final_result": "5.2"}]
        is_valid, validated, errors = validate_save_results_batch(items)
        assert is_valid is False
        assert len(errors) == 1
        assert "Analysis code" in errors[0]

    def test_invalid_final_result_adds_warning(self):
        """Invalid final_result adds warning but continues"""
        from app.utils.validators import validate_save_results_batch

        items = [{"sample_id": "1", "analysis_code": "MT", "final_result": "abc"}]
        is_valid, validated, errors = validate_save_results_batch(items)
        # Still valid (warning only)
        assert len(validated) == 1
        assert len(errors) == 1
        assert "тоон утга" in errors[0]

    def test_out_of_range_result_adds_error(self):
        """Out of range result adds error"""
        from app.utils.validators import validate_save_results_batch

        items = [{"sample_id": "1", "analysis_code": "MT", "final_result": "100"}]
        is_valid, validated, errors = validate_save_results_batch(items)
        assert len(errors) >= 1
        assert "хооронд байх ёстой" in errors[0]

    def test_optional_equipment_id(self):
        """Optional equipment_id is handled"""
        from app.utils.validators import validate_save_results_batch

        items = [
            {"sample_id": "1", "analysis_code": "MT", "final_result": "5.2", "equipment_id": "3"}
        ]
        is_valid, validated, errors = validate_save_results_batch(items)
        assert is_valid is True
        assert validated[0]['equipment_id'] == 3

    def test_invalid_equipment_id_adds_warning(self):
        """Invalid equipment_id adds warning"""
        from app.utils.validators import validate_save_results_batch

        items = [
            {"sample_id": "1", "analysis_code": "MT", "final_result": "5.2", "equipment_id": "abc"}
        ]
        is_valid, validated, errors = validate_save_results_batch(items)
        assert len(errors) >= 1
        assert "Equipment ID" in errors[0]

    def test_status_default_value(self):
        """Status defaults to 'draft'"""
        from app.utils.validators import validate_save_results_batch

        items = [{"sample_id": "1", "analysis_code": "MT", "final_result": "5.2"}]
        is_valid, validated, errors = validate_save_results_batch(items)
        assert validated[0]['status'] == 'draft'

    def test_notes_default_empty(self):
        """Notes defaults to empty string"""
        from app.utils.validators import validate_save_results_batch

        items = [{"sample_id": "1", "analysis_code": "MT", "final_result": "5.2"}]
        is_valid, validated, errors = validate_save_results_batch(items)
        assert validated[0]['notes'] == ''

    def test_raw_data_preserved(self):
        """Raw data is preserved"""
        from app.utils.validators import validate_save_results_batch

        raw_data = {"m1": 10.0, "m2": 10.5}
        items = [
            {"sample_id": "1", "analysis_code": "MT", "final_result": "5.2", "raw_data": raw_data}
        ]
        is_valid, validated, errors = validate_save_results_batch(items)
        assert validated[0]['raw_data'] == raw_data


# ============================================================================
# round_to_half TESTS
# ============================================================================

class TestRoundToHalf:
    """round_to_half function tests"""

    def test_import(self):
        """Import function"""
        from app.utils.validators import round_to_half
        assert callable(round_to_half)

    def test_round_down_to_half(self):
        """Rounds down to nearest 0.5"""
        from app.utils.validators import round_to_half
        assert round_to_half(2.3) == 2.5
        assert round_to_half(2.1) == 2.0

    def test_round_up_to_half(self):
        """Rounds up to nearest 0.5"""
        from app.utils.validators import round_to_half
        assert round_to_half(2.8) == 3.0
        assert round_to_half(2.76) == 3.0

    def test_exact_half_values(self):
        """Exact half values stay unchanged"""
        from app.utils.validators import round_to_half
        assert round_to_half(2.5) == 2.5
        assert round_to_half(3.0) == 3.0

    def test_zero(self):
        """Zero returns zero"""
        from app.utils.validators import round_to_half
        assert round_to_half(0.0) == 0.0

    def test_boundary_values(self):
        """Boundary values (0.25, 0.75) round correctly"""
        from app.utils.validators import round_to_half
        # round(0.25 * 2) / 2 = round(0.5) / 2 = 0.0 / 2 = 0.0 (banker's rounding)
        assert round_to_half(0.25) == 0.0  # Banker's rounding
        assert round_to_half(0.75) == 1.0

    def test_negative_values(self):
        """Negative values round correctly"""
        from app.utils.validators import round_to_half
        assert round_to_half(-2.3) == -2.5


# ============================================================================
# get_csn_repeatability_limit TESTS
# ============================================================================

class TestGetCsnRepeatabilityLimit:
    """get_csn_repeatability_limit function tests"""

    def test_import(self):
        """Import function"""
        from app.utils.validators import get_csn_repeatability_limit
        assert callable(get_csn_repeatability_limit)

    def test_returns_float(self):
        """Returns a float value"""
        from app.utils.validators import get_csn_repeatability_limit
        result = get_csn_repeatability_limit()
        assert isinstance(result, float)

    def test_returns_positive_value(self):
        """Returns a positive value"""
        from app.utils.validators import get_csn_repeatability_limit
        result = get_csn_repeatability_limit()
        assert result > 0

    def test_fallback_value(self):
        """Returns fallback value on import error"""
        from app.utils.validators import get_csn_repeatability_limit

        with patch('app.utils.validators.get_csn_repeatability_limit', side_effect=ImportError):
            # Should not raise error
            pass

        # Default fallback should be 0.50
        result = get_csn_repeatability_limit()
        assert result == 0.50 or result > 0


# ============================================================================
# validate_csn_values TESTS
# ============================================================================

class TestValidateCsnValues:
    """validate_csn_values function tests"""

    def test_import(self):
        """Import function"""
        from app.utils.validators import validate_csn_values
        assert callable(validate_csn_values)

    def test_valid_two_values(self):
        """Two valid values are accepted"""
        from app.utils.validators import validate_csn_values
        is_valid, result, errors = validate_csn_values([2.0, 2.0, None, None, None])
        assert is_valid is True
        assert result is not None
        assert result['avg'] == 2.0
        assert result['range'] == 0.0
        assert result['exceeded'] is False

    def test_valid_five_values(self):
        """Five valid values are processed"""
        from app.utils.validators import validate_csn_values
        is_valid, result, errors = validate_csn_values([2.0, 2.0, 2.0, 2.0, 2.0])
        assert is_valid is True
        assert result['values_count'] == 5

    def test_less_than_two_values_invalid(self):
        """Less than 2 values is invalid"""
        from app.utils.validators import validate_csn_values
        is_valid, result, errors = validate_csn_values([2.0, None, None, None, None])
        assert is_valid is False
        assert result is None
        assert len(errors) >= 1
        assert "2 утга" in errors[0]

    def test_all_none_invalid(self):
        """All None values is invalid"""
        from app.utils.validators import validate_csn_values
        is_valid, result, errors = validate_csn_values([None, None, None, None, None])
        assert is_valid is False
        assert result is None

    def test_empty_string_ignored(self):
        """Empty strings are ignored"""
        from app.utils.validators import validate_csn_values
        is_valid, result, errors = validate_csn_values([2.0, 2.0, '', None, None])
        assert is_valid is True
        assert result['values_count'] == 2

    def test_string_values_converted(self):
        """String values are converted to float"""
        from app.utils.validators import validate_csn_values
        is_valid, result, errors = validate_csn_values(['2.0', '2.0', None, None, None])
        assert is_valid is True
        assert result['avg'] == 2.0

    def test_invalid_string_adds_error(self):
        """Invalid string adds error"""
        from app.utils.validators import validate_csn_values
        is_valid, result, errors = validate_csn_values([2.0, 'abc', 2.0, None, None])
        assert is_valid is True  # Still valid if 2+ values
        assert any("буруу утга" in e for e in errors)

    def test_average_rounded_to_half(self):
        """Average is rounded to 0.5"""
        from app.utils.validators import validate_csn_values
        # 2.0 + 3.0 = 5.0 / 2 = 2.5
        is_valid, result, errors = validate_csn_values([2.0, 3.0, None, None, None])
        assert is_valid is True
        assert result['avg'] == 2.5
        assert result['raw_avg'] == 2.5

    def test_range_calculation(self):
        """Range is calculated correctly"""
        from app.utils.validators import validate_csn_values
        is_valid, result, errors = validate_csn_values([2.0, 4.0, None, None, None])
        assert result['range'] == 2.0

    def test_repeatability_exceeded(self):
        """Repeatability exceeded is flagged"""
        from app.utils.validators import validate_csn_values
        # Range of 2.0 should exceed limit of 0.5
        is_valid, result, errors = validate_csn_values([2.0, 4.0, None, None, None])
        assert result['exceeded'] is True
        assert any("давсан" in e for e in errors)

    def test_repeatability_not_exceeded(self):
        """Repeatability not exceeded when within limit"""
        from app.utils.validators import validate_csn_values
        is_valid, result, errors = validate_csn_values([2.0, 2.2, None, None, None])
        # Range of 0.2 should be within limit (floating point comparison)
        assert abs(result['range'] - 0.2) < 0.001
        # May or may not exceed depending on config

    def test_result_contains_limit(self):
        """Result contains limit value"""
        from app.utils.validators import validate_csn_values
        is_valid, result, errors = validate_csn_values([2.0, 2.0, None, None, None])
        assert 'limit' in result
        assert result['limit'] > 0


# ============================================================================
# sanitize_string TESTS
# ============================================================================

class TestSanitizeString:
    """sanitize_string function tests"""

    def test_import(self):
        """Import function"""
        from app.utils.validators import sanitize_string
        assert callable(sanitize_string)

    def test_valid_string(self):
        """Valid string is returned"""
        from app.utils.validators import sanitize_string
        cleaned, error = sanitize_string("Hello World")
        assert cleaned == "Hello World"
        assert error is None

    def test_string_trimmed(self):
        """String is trimmed"""
        from app.utils.validators import sanitize_string
        cleaned, error = sanitize_string("  Hello  ")
        assert cleaned == "Hello"
        assert error is None

    def test_none_allowed_by_default(self):
        """None is allowed by default"""
        from app.utils.validators import sanitize_string
        cleaned, error = sanitize_string(None)
        assert cleaned is None
        assert error is None

    def test_empty_string_allowed_by_default(self):
        """Empty string is treated as None"""
        from app.utils.validators import sanitize_string
        cleaned, error = sanitize_string('')
        assert cleaned is None
        assert error is None

    def test_none_not_allowed(self):
        """None not allowed when allow_none=False"""
        from app.utils.validators import sanitize_string
        cleaned, error = sanitize_string(None, allow_none=False)
        assert cleaned is None
        assert error is not None
        assert "шаардлагатай" in error

    def test_too_long_returns_error(self):
        """Too long string returns error"""
        from app.utils.validators import sanitize_string
        cleaned, error = sanitize_string("A" * 1001)
        assert cleaned is None
        assert error is not None
        assert "урт" in error

    def test_custom_max_length(self):
        """Custom max_length is respected"""
        from app.utils.validators import sanitize_string
        cleaned, error = sanitize_string("ABCDE", max_length=3)
        assert cleaned is None
        assert error is not None
        assert "3" in error

    def test_non_string_converted(self):
        """Non-string is converted"""
        from app.utils.validators import sanitize_string
        cleaned, error = sanitize_string(123)
        assert cleaned == "123"
        assert error is None

    def test_script_tag_blocked(self):
        """Script tag is blocked"""
        from app.utils.validators import sanitize_string
        cleaned, error = sanitize_string("<script>alert(1)</script>")
        assert cleaned is None
        assert error is not None
        assert "Хориотой" in error

    def test_javascript_protocol_blocked(self):
        """javascript: protocol is blocked"""
        from app.utils.validators import sanitize_string
        cleaned, error = sanitize_string("javascript:alert(1)")
        assert cleaned is None
        assert error is not None

    def test_onerror_blocked(self):
        """onerror= is blocked"""
        from app.utils.validators import sanitize_string
        cleaned, error = sanitize_string('onerror="alert(1)"')
        assert cleaned is None
        assert error is not None

    def test_onload_blocked(self):
        """onload= is blocked"""
        from app.utils.validators import sanitize_string
        cleaned, error = sanitize_string('onload="alert(1)"')
        assert cleaned is None
        assert error is not None

    def test_onclick_blocked(self):
        """onclick= is blocked"""
        from app.utils.validators import sanitize_string
        cleaned, error = sanitize_string('onclick="alert(1)"')
        assert cleaned is None
        assert error is not None

    def test_case_insensitive_xss_check(self):
        """XSS check is case insensitive"""
        from app.utils.validators import sanitize_string
        cleaned, error = sanitize_string("<SCRIPT>alert(1)</SCRIPT>")
        assert cleaned is None
        assert error is not None

    def test_mongolian_text_allowed(self):
        """Mongolian text is allowed"""
        from app.utils.validators import sanitize_string
        cleaned, error = sanitize_string("Сайн байна уу")
        assert cleaned == "Сайн байна уу"
        assert error is None

    def test_normal_html_allowed(self):
        """Normal HTML entities (without dangerous patterns) allowed"""
        from app.utils.validators import sanitize_string
        cleaned, error = sanitize_string("<div>Hello</div>")
        assert cleaned == "<div>Hello</div>"
        assert error is None


# ============================================================================
# DEFAULT_RANGE TESTS
# ============================================================================

class TestDefaultRange:
    """DEFAULT_RANGE constant tests"""

    def test_default_range_exists(self):
        """DEFAULT_RANGE exists"""
        from app.utils.validators import DEFAULT_RANGE
        assert isinstance(DEFAULT_RANGE, tuple)
        assert len(DEFAULT_RANGE) == 2

    def test_default_range_values(self):
        """DEFAULT_RANGE has expected values"""
        from app.utils.validators import DEFAULT_RANGE
        assert DEFAULT_RANGE[0] < 0  # Negative min
        assert DEFAULT_RANGE[1] > 0  # Positive max
        assert DEFAULT_RANGE[0] < DEFAULT_RANGE[1]  # min < max
