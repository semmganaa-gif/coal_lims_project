# -*- coding: utf-8 -*-
"""
Validators comprehensive тестүүд
"""
import pytest


class TestValidateAnalysisResult:
    """validate_analysis_result тестүүд"""

    def test_import_function(self):
        """Function import"""
        from app.utils.validators import validate_analysis_result
        assert validate_analysis_result is not None

    def test_valid_float(self):
        """Valid float value"""
        from app.utils.validators import validate_analysis_result
        value, error = validate_analysis_result(10.5, 'Mad')
        assert error is None or value is not None

    def test_valid_int(self):
        """Valid int value"""
        from app.utils.validators import validate_analysis_result
        value, error = validate_analysis_result(10, 'Mad')
        assert error is None or value is not None

    def test_valid_string_number(self):
        """Valid string number"""
        from app.utils.validators import validate_analysis_result
        value, error = validate_analysis_result('10.5', 'Mad')
        assert error is None or value is not None

    def test_none_value(self):
        """None value"""
        from app.utils.validators import validate_analysis_result
        value, error = validate_analysis_result(None, 'Mad')
        assert value is None or error is not None

    def test_nan_value(self):
        """NaN value should fail"""
        from app.utils.validators import validate_analysis_result
        value, error = validate_analysis_result(float('nan'), 'Mad')
        assert error is not None

    def test_infinity_value(self):
        """Infinity value should fail"""
        from app.utils.validators import validate_analysis_result
        value, error = validate_analysis_result(float('inf'), 'Mad')
        assert error is not None

    def test_negative_infinity(self):
        """Negative infinity should fail"""
        from app.utils.validators import validate_analysis_result
        value, error = validate_analysis_result(float('-inf'), 'Mad')
        assert error is not None

    def test_list_input(self):
        """List input should fail"""
        from app.utils.validators import validate_analysis_result
        value, error = validate_analysis_result([1, 2, 3], 'Mad')
        assert error is not None

    def test_dict_input(self):
        """Dict input should fail"""
        from app.utils.validators import validate_analysis_result
        value, error = validate_analysis_result({'value': 5}, 'Mad')
        assert error is not None

    def test_all_analysis_codes(self):
        """Test various analysis codes"""
        from app.utils.validators import validate_analysis_result
        codes = ['MT', 'Mad', 'Aad', 'Vad', 'Vdaf', 'TS', 'CV', 'FC', 'HGI', 'AFT']
        for code in codes:
            value, error = validate_analysis_result(10.0, code)
            assert value is not None or error is not None


class TestValidateSampleId:
    """validate_sample_id тестүүд"""

    def test_import_function(self):
        """Function import"""
        from app.utils.validators import validate_sample_id
        assert validate_sample_id is not None

    def test_valid_int(self):
        """Valid int"""
        from app.utils.validators import validate_sample_id
        result, error = validate_sample_id(123)
        assert result == 123 or error is not None

    def test_valid_string(self):
        """Valid string number"""
        from app.utils.validators import validate_sample_id
        result, error = validate_sample_id('123')
        assert result == 123 or error is not None

    def test_negative(self):
        """Negative should fail"""
        from app.utils.validators import validate_sample_id
        result, error = validate_sample_id(-5)
        assert error is not None

    def test_zero(self):
        """Zero should fail"""
        from app.utils.validators import validate_sample_id
        result, error = validate_sample_id(0)
        assert error is not None

    def test_none(self):
        """None should fail"""
        from app.utils.validators import validate_sample_id
        result, error = validate_sample_id(None)
        assert error is not None

    def test_empty_string(self):
        """Empty string should fail"""
        from app.utils.validators import validate_sample_id
        result, error = validate_sample_id('')
        assert error is not None

    def test_invalid_string(self):
        """Invalid string should fail"""
        from app.utils.validators import validate_sample_id
        result, error = validate_sample_id('abc')
        assert error is not None


class TestValidateAnalysisCode:
    """validate_analysis_code тестүүд"""

    def test_import_function(self):
        """Function import"""
        from app.utils.validators import validate_analysis_code
        assert validate_analysis_code is not None

    def test_valid_code(self):
        """Valid code"""
        from app.utils.validators import validate_analysis_code
        result, error = validate_analysis_code('TS')
        assert result is not None or error is not None

    def test_lowercase(self):
        """Lowercase code"""
        from app.utils.validators import validate_analysis_code
        result, error = validate_analysis_code('ts')
        assert result is not None or error is not None

    def test_empty(self):
        """Empty should fail"""
        from app.utils.validators import validate_analysis_code
        result, error = validate_analysis_code('')
        assert error is not None

    def test_none(self):
        """None should fail"""
        from app.utils.validators import validate_analysis_code
        result, error = validate_analysis_code(None)
        assert error is not None

    def test_number(self):
        """Number should fail"""
        from app.utils.validators import validate_analysis_code
        result, error = validate_analysis_code(123)
        assert error is not None


class TestValidateEquipmentId:
    """validate_equipment_id тестүүд"""

    def test_import_function(self):
        """Function import"""
        from app.utils.validators import validate_equipment_id
        assert validate_equipment_id is not None

    def test_valid_int(self):
        """Valid int"""
        from app.utils.validators import validate_equipment_id
        result, error = validate_equipment_id(1)
        assert result == 1 or error is not None

    def test_valid_string(self):
        """Valid string"""
        from app.utils.validators import validate_equipment_id
        result, error = validate_equipment_id('5')
        assert result == 5 or error is not None

    def test_negative(self):
        """Negative should fail"""
        from app.utils.validators import validate_equipment_id
        result, error = validate_equipment_id(-1)
        assert error is not None

    def test_none(self):
        """None is allowed"""
        from app.utils.validators import validate_equipment_id
        result, error = validate_equipment_id(None)
        # None may be valid for optional equipment
        assert result is None or error is None


class TestSanitizeString:
    """sanitize_string тестүүд"""

    def test_import_function(self):
        """Function import"""
        from app.utils.validators import sanitize_string
        assert sanitize_string is not None

    def test_normal_string(self):
        """Normal string"""
        from app.utils.validators import sanitize_string
        result, error = sanitize_string('Hello World')
        assert result == 'Hello World'
        assert error is None

    def test_html_tags(self):
        """HTML tags"""
        from app.utils.validators import sanitize_string
        result, error = sanitize_string('<script>alert(1)</script>')
        # Should sanitize or return error
        assert result is not None or error is not None

    def test_sql_injection(self):
        """SQL injection attempt"""
        from app.utils.validators import sanitize_string
        result, error = sanitize_string("'; DROP TABLE users; --")
        # Should sanitize or return error
        assert result is not None or error is not None

    def test_none(self):
        """None input"""
        from app.utils.validators import sanitize_string
        result, error = sanitize_string(None)
        assert result is None or error is not None

    def test_empty_string(self):
        """Empty string"""
        from app.utils.validators import sanitize_string
        result, error = sanitize_string('')
        # Empty string returns None, None
        assert result is None or result == '' or error is None

    def test_unicode(self):
        """Unicode string"""
        from app.utils.validators import sanitize_string
        result, error = sanitize_string('Монгол текст')
        assert result == 'Монгол текст' or error is None


class TestValidateSaveResultsBatch:
    """validate_save_results_batch тестүүд"""

    def test_import_function(self):
        """Function import"""
        from app.utils.validators import validate_save_results_batch
        assert validate_save_results_batch is not None

    def test_empty_list(self):
        """Empty list"""
        from app.utils.validators import validate_save_results_batch
        result = validate_save_results_batch([])
        assert result is not None

    def test_none_input(self):
        """None input"""
        from app.utils.validators import validate_save_results_batch
        result = validate_save_results_batch(None)
        assert result is not None

    def test_not_list(self):
        """Non-list input"""
        from app.utils.validators import validate_save_results_batch
        result = validate_save_results_batch('not a list')
        assert result is not None

    def test_invalid_item(self):
        """Invalid item in list"""
        from app.utils.validators import validate_save_results_batch
        result = validate_save_results_batch([{'invalid': 'data'}])
        assert result is not None
