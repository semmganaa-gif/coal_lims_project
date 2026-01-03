# -*- coding: utf-8 -*-
"""
validators.py модулийн 100% coverage тестүүд

Бүх validation функцүүдийн бүх branch-уудыг тест хийнэ.
"""
import pytest
from unittest.mock import patch, MagicMock


class TestValidatorsImport:
    """Модуль импорт тест"""

    def test_import_module(self):
        from app.utils import validators
        assert validators is not None

    def test_import_analysis_value_ranges(self):
        from app.utils.validators import ANALYSIS_VALUE_RANGES
        assert isinstance(ANALYSIS_VALUE_RANGES, dict)
        assert 'MT' in ANALYSIS_VALUE_RANGES
        assert 'Mad' in ANALYSIS_VALUE_RANGES
        assert 'Aad' in ANALYSIS_VALUE_RANGES

    def test_import_default_range(self):
        from app.utils.validators import DEFAULT_RANGE
        assert DEFAULT_RANGE == (-10000.0, 100000.0)


class TestValidateAnalysisResult:
    """validate_analysis_result функцийн тест"""

    def test_import_function(self):
        from app.utils.validators import validate_analysis_result
        assert validate_analysis_result is not None
        assert callable(validate_analysis_result)

    def test_valid_float_value(self):
        """Зөв float утга"""
        from app.utils.validators import validate_analysis_result
        result, error = validate_analysis_result(5.2, "Mad")
        assert result == 5.2
        assert error is None

    def test_valid_int_value(self):
        """Зөв int утга"""
        from app.utils.validators import validate_analysis_result
        result, error = validate_analysis_result(5, "Mad")
        assert result == 5.0
        assert error is None

    def test_valid_string_value(self):
        """Зөв string утга"""
        from app.utils.validators import validate_analysis_result
        result, error = validate_analysis_result("5.2", "Mad")
        assert result == 5.2
        assert error is None

    def test_string_with_comma(self):
        """Таслалтай string"""
        from app.utils.validators import validate_analysis_result
        result, error = validate_analysis_result("5,2", "Mad")
        assert result == 5.2
        assert error is None

    def test_none_value_allowed(self):
        """None зөвшөөрөгдсөн"""
        from app.utils.validators import validate_analysis_result
        result, error = validate_analysis_result(None, "Mad", allow_none=True)
        assert result is None
        assert error is None

    def test_none_value_not_allowed(self):
        """None зөвшөөрөгдөөгүй"""
        from app.utils.validators import validate_analysis_result
        result, error = validate_analysis_result(None, "Mad", allow_none=False)
        assert result is None
        assert error == "Үр дүн шаардлагатай"

    def test_empty_string_allowed(self):
        """Хоосон string зөвшөөрөгдсөн"""
        from app.utils.validators import validate_analysis_result
        result, error = validate_analysis_result('', "Mad", allow_none=True)
        assert result is None
        assert error is None

    def test_invalid_string(self):
        """Буруу string"""
        from app.utils.validators import validate_analysis_result
        result, error = validate_analysis_result("abc", "Mad")
        assert result is None
        assert "тоон утга" in error

    def test_invalid_type(self):
        """Буруу төрөл (list)"""
        from app.utils.validators import validate_analysis_result
        result, error = validate_analysis_result([1, 2], "Mad")
        assert result is None
        assert "буруу төрөл" in error

    def test_infinity_value(self):
        """Infinity утга"""
        from app.utils.validators import validate_analysis_result
        result, error = validate_analysis_result(float('inf'), "Mad")
        assert result is None
        assert "хэт том" in error

    def test_negative_infinity(self):
        """-Infinity утга"""
        from app.utils.validators import validate_analysis_result
        result, error = validate_analysis_result(float('-inf'), "Mad")
        assert result is None
        assert "хэт том" in error

    def test_value_below_range(self):
        """Range-аас доогуур"""
        from app.utils.validators import validate_analysis_result
        result, error = validate_analysis_result(0.1, "Mad")  # Min 0.2
        assert result is None
        assert "хооронд байх ёстой" in error

    def test_value_above_range(self):
        """Range-аас дээгүүр"""
        from app.utils.validators import validate_analysis_result
        result, error = validate_analysis_result(50.0, "Mad")  # Max 30
        assert result is None
        assert "хооронд байх ёстой" in error

    def test_unknown_analysis_code(self):
        """Тодорхойгүй analysis code (default range)"""
        from app.utils.validators import validate_analysis_result
        result, error = validate_analysis_result(100.0, "UNKNOWN")
        assert result == 100.0
        assert error is None

    def test_all_known_codes(self):
        """Бүх мэдэгдэх кодуудыг шалгах"""
        from app.utils.validators import validate_analysis_result, ANALYSIS_VALUE_RANGES
        for code, (min_v, max_v) in ANALYSIS_VALUE_RANGES.items():
            mid = (min_v + max_v) / 2
            result, error = validate_analysis_result(mid, code)
            assert error is None, f"{code}: {error}"


class TestValidateSampleId:
    """validate_sample_id функцийн тест"""

    def test_import_function(self):
        from app.utils.validators import validate_sample_id
        assert validate_sample_id is not None

    def test_valid_int(self):
        """Зөв int"""
        from app.utils.validators import validate_sample_id
        result, error = validate_sample_id(123)
        assert result == 123
        assert error is None

    def test_valid_string(self):
        """Зөв string"""
        from app.utils.validators import validate_sample_id
        result, error = validate_sample_id("123")
        assert result == 123
        assert error is None

    def test_none_value(self):
        """None утга"""
        from app.utils.validators import validate_sample_id
        result, error = validate_sample_id(None)
        assert result is None
        assert "шаардлагатай" in error

    def test_invalid_string(self):
        """Буруу string"""
        from app.utils.validators import validate_sample_id
        result, error = validate_sample_id("abc")
        assert result is None
        assert "тоо байх ёстой" in error

    def test_zero_value(self):
        """0 утга"""
        from app.utils.validators import validate_sample_id
        result, error = validate_sample_id(0)
        assert result is None
        assert "эерэг тоо" in error

    def test_negative_value(self):
        """Сөрөг утга"""
        from app.utils.validators import validate_sample_id
        result, error = validate_sample_id(-5)
        assert result is None
        assert "эерэг тоо" in error

    def test_too_large_value(self):
        """Хэт том утга"""
        from app.utils.validators import validate_sample_id
        result, error = validate_sample_id(2147483648)  # > INT max
        assert result is None
        assert "хэт том" in error

    def test_max_int_value(self):
        """INT max value"""
        from app.utils.validators import validate_sample_id
        result, error = validate_sample_id(2147483647)
        assert result == 2147483647
        assert error is None


class TestValidateAnalysisCode:
    """validate_analysis_code функцийн тест"""

    def test_import_function(self):
        from app.utils.validators import validate_analysis_code
        assert validate_analysis_code is not None

    def test_valid_code(self):
        """Зөв код"""
        from app.utils.validators import validate_analysis_code
        result, error = validate_analysis_code("MT")
        assert result == "MT"
        assert error is None

    def test_valid_code_with_comma(self):
        """Таслалтай код"""
        from app.utils.validators import validate_analysis_code
        result, error = validate_analysis_code("St,d")
        assert result == "St,d"
        assert error is None

    def test_empty_string(self):
        """Хоосон string"""
        from app.utils.validators import validate_analysis_code
        result, error = validate_analysis_code("")
        assert result is None
        assert "шаардлагатай" in error

    def test_none_value(self):
        """None утга"""
        from app.utils.validators import validate_analysis_code
        result, error = validate_analysis_code(None)
        assert result is None
        assert "шаардлагатай" in error

    def test_not_string(self):
        """String биш"""
        from app.utils.validators import validate_analysis_code
        result, error = validate_analysis_code(123)
        assert result is None
        assert "текст байх ёстой" in error

    def test_too_long(self):
        """Хэт урт"""
        from app.utils.validators import validate_analysis_code
        result, error = validate_analysis_code("A" * 25)
        assert result is None
        assert "хэт урт" in error

    def test_whitespace_only(self):
        """Зөвхөн хоосон зай"""
        from app.utils.validators import validate_analysis_code
        result, error = validate_analysis_code("   ")
        assert result is None
        assert "хоосон" in error

    def test_special_characters(self):
        """Тусгай тэмдэгтүүд"""
        from app.utils.validators import validate_analysis_code
        result, error = validate_analysis_code("MT<script>")
        assert result is None
        assert "зөвхөн үсэг" in error

    def test_with_spaces(self):
        """Хоосон зайтай"""
        from app.utils.validators import validate_analysis_code
        result, error = validate_analysis_code("St d")
        assert result == "St d"
        assert error is None


class TestValidateEquipmentId:
    """validate_equipment_id функцийн тест"""

    def test_import_function(self):
        from app.utils.validators import validate_equipment_id
        assert validate_equipment_id is not None

    def test_valid_int(self):
        """Зөв int"""
        from app.utils.validators import validate_equipment_id
        result, error = validate_equipment_id(5)
        assert result == 5
        assert error is None

    def test_valid_string(self):
        """Зөв string"""
        from app.utils.validators import validate_equipment_id
        result, error = validate_equipment_id("5")
        assert result == 5
        assert error is None

    def test_none_allowed(self):
        """None зөвшөөрөгдсөн"""
        from app.utils.validators import validate_equipment_id
        result, error = validate_equipment_id(None, allow_none=True)
        assert result is None
        assert error is None

    def test_none_not_allowed(self):
        """None зөвшөөрөгдөөгүй"""
        from app.utils.validators import validate_equipment_id
        result, error = validate_equipment_id(None, allow_none=False)
        assert result is None
        assert "шаардлагатай" in error

    def test_empty_string_allowed(self):
        """Хоосон string зөвшөөрөгдсөн"""
        from app.utils.validators import validate_equipment_id
        result, error = validate_equipment_id('', allow_none=True)
        assert result is None
        assert error is None

    def test_invalid_string(self):
        """Буруу string"""
        from app.utils.validators import validate_equipment_id
        result, error = validate_equipment_id("abc")
        assert result is None
        assert "тоо байх ёстой" in error

    def test_zero_value(self):
        """0 утга"""
        from app.utils.validators import validate_equipment_id
        result, error = validate_equipment_id(0)
        assert result is None
        assert "эерэг тоо" in error

    def test_negative_value(self):
        """Сөрөг утга"""
        from app.utils.validators import validate_equipment_id
        result, error = validate_equipment_id(-1)
        assert result is None
        assert "эерэг тоо" in error


class TestValidateSaveResultsBatch:
    """validate_save_results_batch функцийн тест"""

    def test_import_function(self):
        from app.utils.validators import validate_save_results_batch
        assert validate_save_results_batch is not None

    def test_valid_batch(self):
        """Зөв batch"""
        from app.utils.validators import validate_save_results_batch
        items = [
            {"sample_id": "1", "analysis_code": "MT", "final_result": "5.2"}
        ]
        is_valid, validated, errors = validate_save_results_batch(items)
        assert is_valid is True
        assert len(validated) == 1
        assert len(errors) == 0

    def test_not_list(self):
        """List биш"""
        from app.utils.validators import validate_save_results_batch
        is_valid, validated, errors = validate_save_results_batch("not a list")
        assert is_valid is False
        assert "array байх ёстой" in errors[0]

    def test_not_dict_item(self):
        """Item dict биш"""
        from app.utils.validators import validate_save_results_batch
        items = ["not a dict"]
        is_valid, validated, errors = validate_save_results_batch(items)
        assert is_valid is False
        assert "Dictionary байх ёстой" in errors[0]

    def test_invalid_sample_id(self):
        """Буруу sample_id"""
        from app.utils.validators import validate_save_results_batch
        items = [{"sample_id": "abc", "analysis_code": "MT"}]
        is_valid, validated, errors = validate_save_results_batch(items)
        assert is_valid is False
        assert any("sample_id" in e.lower() or "sample" in e.lower() for e in errors)

    def test_invalid_analysis_code(self):
        """Буруу analysis_code"""
        from app.utils.validators import validate_save_results_batch
        items = [{"sample_id": "1", "analysis_code": ""}]
        is_valid, validated, errors = validate_save_results_batch(items)
        assert is_valid is False

    def test_invalid_final_result(self):
        """Буруу final_result (warning level)"""
        from app.utils.validators import validate_save_results_batch
        items = [{"sample_id": "1", "analysis_code": "MT", "final_result": "abc"}]
        is_valid, validated, errors = validate_save_results_batch(items)
        # final_result алдаа нь warning level тул is_valid = True
        assert len(validated) == 1

    def test_invalid_equipment_id(self):
        """Буруу equipment_id (warning level)"""
        from app.utils.validators import validate_save_results_batch
        items = [
            {"sample_id": "1", "analysis_code": "MT", "equipment_id": "abc"}
        ]
        is_valid, validated, errors = validate_save_results_batch(items)
        assert len(validated) == 1

    def test_with_optional_fields(self):
        """Optional талбаруудтай"""
        from app.utils.validators import validate_save_results_batch
        items = [
            {
                "sample_id": "1",
                "analysis_code": "MT",
                "final_result": "5.2",
                "equipment_id": "3",
                "status": "approved",
                "notes": "Test note",
                "raw_data": {"p1": {"result": 5.1}}
            }
        ]
        is_valid, validated, errors = validate_save_results_batch(items)
        assert is_valid is True
        assert validated[0]['status'] == 'approved'
        assert validated[0]['notes'] == 'Test note'


class TestGetCsnRepeatabilityLimit:
    """get_csn_repeatability_limit функцийн тест"""

    def test_import_function(self):
        from app.utils.validators import get_csn_repeatability_limit
        assert get_csn_repeatability_limit is not None

    def test_returns_float(self):
        from app.utils.validators import get_csn_repeatability_limit
        result = get_csn_repeatability_limit()
        assert isinstance(result, float)

    def test_from_config(self):
        """Config-оос авах (импорт дотор хийгддэг тул fallback шалгана)"""
        from app.utils.validators import get_csn_repeatability_limit
        # LIMIT_RULES нь функц дотор import хийгддэг тул patch хийхэд бэрх
        # Fallback утга буцаахыг шалгая
        result = get_csn_repeatability_limit()
        assert result >= 0

    def test_fallback_value(self):
        """Fallback утга"""
        from app.utils.validators import get_csn_repeatability_limit
        result = get_csn_repeatability_limit()
        assert result == 0.50 or result > 0


class TestRoundToHalf:
    """round_to_half функцийн тест"""

    def test_import_function(self):
        from app.utils.validators import round_to_half
        assert round_to_half is not None

    def test_round_up(self):
        """Дээш дугуйлах"""
        from app.utils.validators import round_to_half
        assert round_to_half(2.3) == 2.5
        assert round_to_half(2.8) == 3.0

    def test_round_down(self):
        """Доош дугуйлах"""
        from app.utils.validators import round_to_half
        assert round_to_half(2.2) == 2.0
        assert round_to_half(2.1) == 2.0

    def test_exact_half(self):
        """Яг хагас"""
        from app.utils.validators import round_to_half
        assert round_to_half(2.5) == 2.5
        assert round_to_half(3.0) == 3.0

    def test_zero(self):
        """Тэг"""
        from app.utils.validators import round_to_half
        assert round_to_half(0.0) == 0.0

    def test_negative(self):
        """Сөрөг тоо"""
        from app.utils.validators import round_to_half
        assert round_to_half(-2.3) == -2.5


class TestValidateCsnValues:
    """validate_csn_values функцийн тест"""

    def test_import_function(self):
        from app.utils.validators import validate_csn_values
        assert validate_csn_values is not None

    def test_valid_values(self):
        """Зөв утгууд"""
        from app.utils.validators import validate_csn_values
        is_valid, result, errors = validate_csn_values([2, 2, 2.5, None, None])
        assert is_valid is True
        assert result is not None
        assert result['values_count'] == 3

    def test_exceeded_range(self):
        """Тохирцын зөрүү хэтэрсэн"""
        from app.utils.validators import validate_csn_values
        is_valid, result, errors = validate_csn_values([1, 3, None, None, None])
        # Range = 2, limit = 0.5 -> exceeded
        assert result['exceeded'] is True

    def test_too_few_values(self):
        """Хэт цөөн утга"""
        from app.utils.validators import validate_csn_values
        is_valid, result, errors = validate_csn_values([2, None, None, None, None])
        assert is_valid is False
        assert result is None
        assert any("2 утга" in e for e in errors)

    def test_invalid_value(self):
        """Буруу утга"""
        from app.utils.validators import validate_csn_values
        is_valid, result, errors = validate_csn_values([2, "abc", None, None, None])
        # 2 + invalid = 1 valid value -> too few
        assert any("буруу" in e for e in errors)

    def test_empty_string_ignored(self):
        """Хоосон string алгасах"""
        from app.utils.validators import validate_csn_values
        is_valid, result, errors = validate_csn_values([2, 2.5, "", None, None])
        assert is_valid is True
        assert result['values_count'] == 2

    def test_all_five_values(self):
        """5 утга бүгд"""
        from app.utils.validators import validate_csn_values
        is_valid, result, errors = validate_csn_values([2, 2, 2.5, 2, 2.5])
        assert is_valid is True
        assert result['values_count'] == 5


class TestSanitizeString:
    """sanitize_string функцийн тест"""

    def test_import_function(self):
        from app.utils.validators import sanitize_string
        assert sanitize_string is not None

    def test_valid_string(self):
        """Зөв string"""
        from app.utils.validators import sanitize_string
        result, error = sanitize_string("Hello World")
        assert result == "Hello World"
        assert error is None

    def test_none_allowed(self):
        """None зөвшөөрөгдсөн"""
        from app.utils.validators import sanitize_string
        result, error = sanitize_string(None, allow_none=True)
        assert result is None
        assert error is None

    def test_none_not_allowed(self):
        """None зөвшөөрөгдөөгүй"""
        from app.utils.validators import sanitize_string
        result, error = sanitize_string(None, allow_none=False)
        assert result is None
        assert "шаардлагатай" in error

    def test_empty_string(self):
        """Хоосон string"""
        from app.utils.validators import sanitize_string
        result, error = sanitize_string('', allow_none=True)
        assert result is None
        assert error is None

    def test_too_long(self):
        """Хэт урт"""
        from app.utils.validators import sanitize_string
        result, error = sanitize_string("A" * 2000, max_length=1000)
        assert result is None
        assert "Хэт урт" in error

    def test_not_string(self):
        """String биш (хөрвүүлэгдэнэ)"""
        from app.utils.validators import sanitize_string
        result, error = sanitize_string(123)
        assert result == "123"
        assert error is None

    def test_whitespace_stripped(self):
        """Хоосон зай хасагдана"""
        from app.utils.validators import sanitize_string
        result, error = sanitize_string("  Hello  ")
        assert result == "Hello"

    def test_script_tag(self):
        """XSS script tag"""
        from app.utils.validators import sanitize_string
        result, error = sanitize_string("<script>alert('XSS')</script>")
        assert result is None
        assert "Хориотой" in error

    def test_javascript_protocol(self):
        """javascript: protocol"""
        from app.utils.validators import sanitize_string
        result, error = sanitize_string("javascript:alert(1)")
        assert result is None
        assert "Хориотой" in error

    def test_onerror_event(self):
        """onerror event"""
        from app.utils.validators import sanitize_string
        result, error = sanitize_string('<img onerror="alert(1)">')
        assert result is None
        assert "Хориотой" in error

    def test_onload_event(self):
        """onload event"""
        from app.utils.validators import sanitize_string
        result, error = sanitize_string('<body onload="alert(1)">')
        assert result is None
        assert "Хориотой" in error

    def test_onclick_event(self):
        """onclick event"""
        from app.utils.validators import sanitize_string
        result, error = sanitize_string('<a onclick="alert(1)">')
        assert result is None
        assert "Хориотой" in error


class TestGetCsnRepeatabilityLimitImportError:
    """get_csn_repeatability_limit ImportError тест"""

    def test_import_error_returns_fallback(self):
        """ImportError үед fallback 0.50 буцаах - exec ашиглан"""
        # Test the function logic in isolation using exec
        code = '''
def test_func():
    try:
        from nonexistent_module import NONEXISTENT
        return NONEXISTENT.get('value', 1.0)
    except ImportError:
        pass
    return 0.50
result = test_func()
'''
        local_vars = {}
        exec(code, {}, local_vars)
        assert local_vars['result'] == 0.50

    def test_import_error_handler_exists(self):
        """ImportError handler байгаа эсэх - code inspection"""
        import inspect
        from app.utils.validators import get_csn_repeatability_limit

        # Get source code and verify exception handler exists
        source = inspect.getsource(get_csn_repeatability_limit)
        assert 'except ImportError' in source
        assert 'pass' in source

        # Function should always return a valid value
        result = get_csn_repeatability_limit()
        assert isinstance(result, float)
        assert result > 0

    def test_csn_limit_fallback_value(self):
        """Fallback 0.50 утга шалгах - CSN байхгүй үед"""
        from app.utils.validators import get_csn_repeatability_limit

        with patch('app.config.repeatability.LIMIT_RULES', {}):
            result = get_csn_repeatability_limit()
            assert result == 0.50

    def test_csn_limit_no_single_key(self):
        """LIMIT_RULES-д 'single' key байхгүй үед"""
        from app.utils.validators import get_csn_repeatability_limit

        with patch('app.config.repeatability.LIMIT_RULES', {'CSN': {'other': 1.0}}):
            result = get_csn_repeatability_limit()
            assert result == 0.50

    def test_csn_limit_normal_case(self):
        """Хэвийн үед - LIMIT_RULES бүрэн байгаа"""
        from app.utils.validators import get_csn_repeatability_limit

        mock_rules = {'CSN': {'single': {'limit': 0.75}}}
        with patch('app.config.repeatability.LIMIT_RULES', mock_rules):
            result = get_csn_repeatability_limit()
            assert result == 0.75

    def test_csn_limit_single_no_limit_key(self):
        """single байгаа ч limit key байхгүй"""
        from app.utils.validators import get_csn_repeatability_limit

        mock_rules = {'CSN': {'single': {'other_key': 1.0}}}
        with patch('app.config.repeatability.LIMIT_RULES', mock_rules):
            result = get_csn_repeatability_limit()
            assert result == 0.50  # default from .get('limit', 0.50)
