# -*- coding: utf-8 -*-
"""
Validators модулийн coverage тестүүд
"""
import pytest
from unittest.mock import patch, MagicMock


class TestValidateAnalysisResult:
    """validate_analysis_result тестүүд"""

    def test_import_function(self):
        """Function import"""
        from app.utils.validators import validate_analysis_result
        assert validate_analysis_result is not None

    def test_none_allowed(self):
        """None with allow_none=True"""
        from app.utils.validators import validate_analysis_result
        result, err = validate_analysis_result(None, "MT", allow_none=True)
        assert result is None
        assert err is None

    def test_none_not_allowed(self):
        """None with allow_none=False"""
        from app.utils.validators import validate_analysis_result
        result, err = validate_analysis_result(None, "MT", allow_none=False)
        assert result is None
        assert err is not None

    def test_empty_string_allowed(self):
        """Empty string with allow_none=True"""
        from app.utils.validators import validate_analysis_result
        result, err = validate_analysis_result('', "MT", allow_none=True)
        assert result is None
        assert err is None

    def test_valid_int(self):
        """Valid integer value"""
        from app.utils.validators import validate_analysis_result
        result, err = validate_analysis_result(5, "Mad")
        assert result == 5.0
        assert err is None

    def test_valid_float(self):
        """Valid float value"""
        from app.utils.validators import validate_analysis_result
        result, err = validate_analysis_result(5.25, "Mad")
        assert result == 5.25
        assert err is None

    def test_valid_string_number(self):
        """Valid string number"""
        from app.utils.validators import validate_analysis_result
        result, err = validate_analysis_result("5.25", "Mad")
        assert result == 5.25
        assert err is None

    def test_string_with_comma(self):
        """String with comma as decimal"""
        from app.utils.validators import validate_analysis_result
        result, err = validate_analysis_result("5,25", "Mad")
        assert result == 5.25
        assert err is None

    def test_invalid_string(self):
        """Invalid string value"""
        from app.utils.validators import validate_analysis_result
        result, err = validate_analysis_result("abc", "MT")
        assert result is None
        assert err is not None

    def test_wrong_type(self):
        """Wrong type (list)"""
        from app.utils.validators import validate_analysis_result
        result, err = validate_analysis_result([1, 2, 3], "MT")
        assert result is None
        assert "буруу төрөл" in err

    def test_out_of_range_high(self):
        """Value above max range"""
        from app.utils.validators import validate_analysis_result
        result, err = validate_analysis_result(50.0, "Mad")  # Mad max is 30.0
        assert result is None
        assert "хооронд байх ёстой" in err

    def test_out_of_range_low(self):
        """Value below min range"""
        from app.utils.validators import validate_analysis_result
        result, err = validate_analysis_result(0.0, "Mad")  # Mad min is 0.2
        assert result is None
        assert "хооронд байх ёстой" in err

    def test_unknown_analysis_uses_default(self):
        """Unknown analysis code uses default range"""
        from app.utils.validators import validate_analysis_result
        result, err = validate_analysis_result(50000.0, "UNKNOWN")
        assert result == 50000.0
        assert err is None

    def test_extreme_value(self):
        """Extremely large value"""
        from app.utils.validators import validate_analysis_result
        result, err = validate_analysis_result(float('inf'), "MT")
        assert result is None
        assert "хэт том" in err

    def test_cv_valid(self):
        """Valid CV value"""
        from app.utils.validators import validate_analysis_result
        result, err = validate_analysis_result(25000, "CV")
        assert result == 25000.0
        assert err is None

    def test_csn_valid(self):
        """Valid CSN value"""
        from app.utils.validators import validate_analysis_result
        result, err = validate_analysis_result(5.5, "CSN")
        assert result == 5.5
        assert err is None


class TestValidateSampleId:
    """validate_sample_id тестүүд"""

    def test_import_function(self):
        """Function import"""
        from app.utils.validators import validate_sample_id
        assert validate_sample_id is not None

    def test_valid_int(self):
        """Valid integer"""
        from app.utils.validators import validate_sample_id
        result, err = validate_sample_id(123)
        assert result == 123
        assert err is None

    def test_valid_string(self):
        """Valid string number"""
        from app.utils.validators import validate_sample_id
        result, err = validate_sample_id("456")
        assert result == 456
        assert err is None

    def test_none(self):
        """None value"""
        from app.utils.validators import validate_sample_id
        result, err = validate_sample_id(None)
        assert result is None
        assert "шаардлагатай" in err

    def test_invalid_string(self):
        """Invalid string"""
        from app.utils.validators import validate_sample_id
        result, err = validate_sample_id("abc")
        assert result is None
        assert "тоо байх ёстой" in err

    def test_negative(self):
        """Negative value"""
        from app.utils.validators import validate_sample_id
        result, err = validate_sample_id(-5)
        assert result is None
        assert "эерэг тоо" in err

    def test_zero(self):
        """Zero value"""
        from app.utils.validators import validate_sample_id
        result, err = validate_sample_id(0)
        assert result is None
        assert "эерэг тоо" in err

    def test_too_large(self):
        """Too large value"""
        from app.utils.validators import validate_sample_id
        result, err = validate_sample_id(3000000000)
        assert result is None
        assert "хэт том" in err


class TestValidateAnalysisCode:
    """validate_analysis_code тестүүд"""

    def test_import_function(self):
        """Function import"""
        from app.utils.validators import validate_analysis_code
        assert validate_analysis_code is not None

    def test_valid_code(self):
        """Valid analysis code"""
        from app.utils.validators import validate_analysis_code
        result, err = validate_analysis_code("MT")
        assert result == "MT"
        assert err is None

    def test_valid_with_spaces(self):
        """Valid with spaces (trimmed)"""
        from app.utils.validators import validate_analysis_code
        result, err = validate_analysis_code("  MT  ")
        assert result == "MT"
        assert err is None

    def test_valid_with_comma(self):
        """Valid with comma"""
        from app.utils.validators import validate_analysis_code
        result, err = validate_analysis_code("St,ad")
        assert result == "St,ad"
        assert err is None

    def test_none(self):
        """None value"""
        from app.utils.validators import validate_analysis_code
        result, err = validate_analysis_code(None)
        assert result is None
        assert "шаардлагатай" in err

    def test_empty(self):
        """Empty string"""
        from app.utils.validators import validate_analysis_code
        result, err = validate_analysis_code("")
        assert result is None
        assert "шаардлагатай" in err

    def test_not_string(self):
        """Not a string"""
        from app.utils.validators import validate_analysis_code
        result, err = validate_analysis_code(123)
        assert result is None
        assert "текст байх ёстой" in err

    def test_too_long(self):
        """Too long code"""
        from app.utils.validators import validate_analysis_code
        result, err = validate_analysis_code("A" * 25)
        assert result is None
        assert "хэт урт" in err

    def test_invalid_chars(self):
        """Invalid characters"""
        from app.utils.validators import validate_analysis_code
        result, err = validate_analysis_code("MT@#$")
        assert result is None
        assert "зөвхөн үсэг" in err


class TestValidateEquipmentId:
    """validate_equipment_id тестүүд"""

    def test_import_function(self):
        """Function import"""
        from app.utils.validators import validate_equipment_id
        assert validate_equipment_id is not None

    def test_valid_int(self):
        """Valid integer"""
        from app.utils.validators import validate_equipment_id
        result, err = validate_equipment_id(10)
        assert result == 10
        assert err is None

    def test_valid_string(self):
        """Valid string number"""
        from app.utils.validators import validate_equipment_id
        result, err = validate_equipment_id("20")
        assert result == 20
        assert err is None

    def test_none_allowed(self):
        """None with allow_none=True"""
        from app.utils.validators import validate_equipment_id
        result, err = validate_equipment_id(None, allow_none=True)
        assert result is None
        assert err is None

    def test_none_not_allowed(self):
        """None with allow_none=False"""
        from app.utils.validators import validate_equipment_id
        result, err = validate_equipment_id(None, allow_none=False)
        assert result is None
        assert "шаардлагатай" in err

    def test_empty_allowed(self):
        """Empty string with allow_none=True"""
        from app.utils.validators import validate_equipment_id
        result, err = validate_equipment_id('', allow_none=True)
        assert result is None
        assert err is None

    def test_invalid_string(self):
        """Invalid string"""
        from app.utils.validators import validate_equipment_id
        result, err = validate_equipment_id("abc")
        assert result is None
        assert "тоо байх ёстой" in err

    def test_negative(self):
        """Negative value"""
        from app.utils.validators import validate_equipment_id
        result, err = validate_equipment_id(-1)
        assert result is None
        assert "эерэг тоо" in err


class TestValidateSaveResultsBatch:
    """validate_save_results_batch тестүүд"""

    def test_import_function(self):
        """Function import"""
        from app.utils.validators import validate_save_results_batch
        assert validate_save_results_batch is not None

    def test_not_list(self):
        """Not a list"""
        from app.utils.validators import validate_save_results_batch
        is_valid, items, errors = validate_save_results_batch("not a list")
        assert is_valid is False
        assert "array байх ёстой" in errors[0]

    def test_empty_list(self):
        """Empty list"""
        from app.utils.validators import validate_save_results_batch
        is_valid, items, errors = validate_save_results_batch([])
        assert is_valid is True
        assert len(items) == 0

    def test_valid_item(self):
        """Valid item"""
        from app.utils.validators import validate_save_results_batch
        data = [{
            "sample_id": 1,
            "analysis_code": "MT",
            "final_result": 5.0
        }]
        is_valid, items, errors = validate_save_results_batch(data)
        assert is_valid is True
        assert len(items) == 1
        assert items[0]['sample_id'] == 1

    def test_not_dict(self):
        """Item not a dict"""
        from app.utils.validators import validate_save_results_batch
        is_valid, items, errors = validate_save_results_batch(["string"])
        assert "Dictionary байх ёстой" in errors[0]

    def test_missing_sample_id(self):
        """Missing sample_id"""
        from app.utils.validators import validate_save_results_batch
        data = [{"analysis_code": "MT"}]
        is_valid, items, errors = validate_save_results_batch(data)
        assert is_valid is False

    def test_invalid_sample_id(self):
        """Invalid sample_id"""
        from app.utils.validators import validate_save_results_batch
        data = [{"sample_id": "abc", "analysis_code": "MT"}]
        is_valid, items, errors = validate_save_results_batch(data)
        assert is_valid is False

    def test_invalid_analysis_code(self):
        """Invalid analysis_code"""
        from app.utils.validators import validate_save_results_batch
        data = [{"sample_id": 1, "analysis_code": None}]
        is_valid, items, errors = validate_save_results_batch(data)
        assert is_valid is False

    def test_out_of_range_result(self):
        """Out of range result (warning)"""
        from app.utils.validators import validate_save_results_batch
        data = [{
            "sample_id": 1,
            "analysis_code": "MT",
            "final_result": 100.0  # Out of range for MT
        }]
        is_valid, items, errors = validate_save_results_batch(data)
        assert len(errors) >= 1  # Has warning

    def test_invalid_equipment_id(self):
        """Invalid equipment_id (warning)"""
        from app.utils.validators import validate_save_results_batch
        data = [{
            "sample_id": 1,
            "analysis_code": "MT",
            "equipment_id": -1  # Invalid
        }]
        is_valid, items, errors = validate_save_results_batch(data)
        assert len(errors) >= 1

    def test_full_item(self):
        """Full item with all fields"""
        from app.utils.validators import validate_save_results_batch
        data = [{
            "sample_id": 1,
            "analysis_code": "MT",
            "final_result": 5.0,
            "equipment_id": 10,
            "status": "completed",
            "notes": "Test note",
            "raw_data": {"key": "value"}
        }]
        is_valid, items, errors = validate_save_results_batch(data)
        assert is_valid is True
        assert items[0]['status'] == "completed"
        assert items[0]['notes'] == "Test note"


class TestGetCsnRepeatabilityLimit:
    """get_csn_repeatability_limit тестүүд"""

    def test_import_function(self):
        """Function import"""
        from app.utils.validators import get_csn_repeatability_limit
        assert get_csn_repeatability_limit is not None

    def test_returns_float(self):
        """Returns float"""
        from app.utils.validators import get_csn_repeatability_limit
        result = get_csn_repeatability_limit()
        assert isinstance(result, float)

    def test_default_value(self):
        """Default value is 0.5 or from config"""
        from app.utils.validators import get_csn_repeatability_limit
        result = get_csn_repeatability_limit()
        # Should return value from config or fallback 0.5
        assert result >= 0.0


class TestRoundToHalf:
    """round_to_half тестүүд"""

    def test_import_function(self):
        """Function import"""
        from app.utils.validators import round_to_half
        assert round_to_half is not None

    def test_exact_half(self):
        """Already at 0.5"""
        from app.utils.validators import round_to_half
        assert round_to_half(2.5) == 2.5

    def test_round_down(self):
        """Round down to 0.5"""
        from app.utils.validators import round_to_half
        assert round_to_half(2.3) == 2.5

    def test_round_up(self):
        """Round up to next 0.5"""
        from app.utils.validators import round_to_half
        assert round_to_half(2.8) == 3.0

    def test_whole_number(self):
        """Whole number"""
        from app.utils.validators import round_to_half
        assert round_to_half(3.0) == 3.0

    def test_zero(self):
        """Zero"""
        from app.utils.validators import round_to_half
        assert round_to_half(0.0) == 0.0


class TestValidateCsnValues:
    """validate_csn_values тестүүд"""

    def test_import_function(self):
        """Function import"""
        from app.utils.validators import validate_csn_values
        assert validate_csn_values is not None

    def test_valid_values(self):
        """Valid CSN values"""
        from app.utils.validators import validate_csn_values
        is_valid, result, errors = validate_csn_values([2, 2.5, 2, None, None])
        assert is_valid is True
        assert result is not None
        assert 'avg' in result

    def test_less_than_2_values(self):
        """Less than 2 values"""
        from app.utils.validators import validate_csn_values
        is_valid, result, errors = validate_csn_values([2, None, None, None, None])
        assert is_valid is False
        assert "хамгийн багадаа 2" in errors[0].lower()

    def test_all_none(self):
        """All None values"""
        from app.utils.validators import validate_csn_values
        is_valid, result, errors = validate_csn_values([None, None, None, None, None])
        assert is_valid is False

    def test_invalid_value(self):
        """Invalid value in list"""
        from app.utils.validators import validate_csn_values
        is_valid, result, errors = validate_csn_values([2, "abc", 3, None, None])
        assert "буруу утга" in errors[0]

    def test_range_exceeded(self):
        """Range exceeded (warning)"""
        from app.utils.validators import validate_csn_values
        is_valid, result, errors = validate_csn_values([2, 5, 3, None, None])  # Range = 3
        assert result['exceeded'] is True
        assert "зөрүү давсан" in errors[0]

    def test_empty_string_ignored(self):
        """Empty string treated as None"""
        from app.utils.validators import validate_csn_values
        is_valid, result, errors = validate_csn_values([2, 3, '', '', ''])
        assert is_valid is True
        assert result['values_count'] == 2


class TestSanitizeString:
    """sanitize_string тестүүд"""

    def test_import_function(self):
        """Function import"""
        from app.utils.validators import sanitize_string
        assert sanitize_string is not None

    def test_none_allowed(self):
        """None with allow_none=True"""
        from app.utils.validators import sanitize_string
        result, err = sanitize_string(None, allow_none=True)
        assert result is None
        assert err is None

    def test_none_not_allowed(self):
        """None with allow_none=False"""
        from app.utils.validators import sanitize_string
        result, err = sanitize_string(None, allow_none=False)
        assert result is None
        assert "шаардлагатай" in err

    def test_empty_allowed(self):
        """Empty string with allow_none=True"""
        from app.utils.validators import sanitize_string
        result, err = sanitize_string('', allow_none=True)
        assert result is None
        assert err is None

    def test_valid_string(self):
        """Valid string"""
        from app.utils.validators import sanitize_string
        result, err = sanitize_string("Hello world")
        assert result == "Hello world"
        assert err is None

    def test_trimmed(self):
        """String is trimmed"""
        from app.utils.validators import sanitize_string
        result, err = sanitize_string("  test  ")
        assert result == "test"

    def test_too_long(self):
        """Too long string"""
        from app.utils.validators import sanitize_string
        result, err = sanitize_string("x" * 2000, max_length=1000)
        assert result is None
        assert "урт" in err.lower()

    def test_xss_script(self):
        """XSS: script tag"""
        from app.utils.validators import sanitize_string
        result, err = sanitize_string("<script>alert('xss')</script>")
        assert result is None
        assert "хориотой" in err.lower()

    def test_xss_javascript(self):
        """XSS: javascript: protocol"""
        from app.utils.validators import sanitize_string
        result, err = sanitize_string("javascript:alert(1)")
        assert result is None
        assert "хориотой" in err.lower()

    def test_xss_onerror(self):
        """XSS: onerror attribute"""
        from app.utils.validators import sanitize_string
        result, err = sanitize_string("<img onerror=alert(1)>")
        assert result is None

    def test_xss_onclick(self):
        """XSS: onclick attribute"""
        from app.utils.validators import sanitize_string
        result, err = sanitize_string("<div onclick=alert(1)>")
        assert result is None

    def test_non_string_converted(self):
        """Non-string is converted"""
        from app.utils.validators import sanitize_string
        result, err = sanitize_string(12345)
        assert result == "12345"
        assert err is None

    def test_mongolian_text(self):
        """Mongolian text allowed"""
        from app.utils.validators import sanitize_string
        result, err = sanitize_string("Монгол хэл тест")
        assert result == "Монгол хэл тест"
        assert err is None


class TestAnalysisValueRanges:
    """ANALYSIS_VALUE_RANGES тестүүд"""

    def test_import_constant(self):
        """Import constant"""
        from app.utils.validators import ANALYSIS_VALUE_RANGES
        assert ANALYSIS_VALUE_RANGES is not None
        assert isinstance(ANALYSIS_VALUE_RANGES, dict)

    def test_has_mt(self):
        """Has MT range"""
        from app.utils.validators import ANALYSIS_VALUE_RANGES
        assert 'MT' in ANALYSIS_VALUE_RANGES

    def test_has_cv(self):
        """Has CV range"""
        from app.utils.validators import ANALYSIS_VALUE_RANGES
        assert 'CV' in ANALYSIS_VALUE_RANGES

    def test_has_csn(self):
        """Has CSN range"""
        from app.utils.validators import ANALYSIS_VALUE_RANGES
        assert 'CSN' in ANALYSIS_VALUE_RANGES

    def test_range_is_tuple(self):
        """Range is tuple of 2"""
        from app.utils.validators import ANALYSIS_VALUE_RANGES
        for code, range_val in ANALYSIS_VALUE_RANGES.items():
            assert isinstance(range_val, tuple)
            assert len(range_val) == 2
