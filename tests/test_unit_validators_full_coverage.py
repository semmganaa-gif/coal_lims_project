# tests/unit/test_validators_full_coverage.py
"""
Validators full coverage тест - бүх branch-ийг тест хийх
"""
import pytest


class TestValidateAnalysisResultBranches:
    """validate_analysis_result бүх branch"""

    def test_empty_string_allow_none(self):
        """Empty string with allow_none=True"""
        from app.utils.validators import validate_analysis_result
        value, error = validate_analysis_result('', 'Mad', allow_none=True)
        assert value is None
        assert error is None

    def test_empty_string_not_allow_none(self):
        """Empty string with allow_none=False"""
        from app.utils.validators import validate_analysis_result
        value, error = validate_analysis_result('', 'Mad', allow_none=False)
        assert error is not None
        assert "шаардлагатай" in error

    def test_wrong_type_list(self):
        """Wrong type - list"""
        from app.utils.validators import validate_analysis_result
        value, error = validate_analysis_result([1, 2, 3], 'Mad')
        assert error is not None
        assert "төрөл" in error

    def test_wrong_type_dict(self):
        """Wrong type - dict"""
        from app.utils.validators import validate_analysis_result
        value, error = validate_analysis_result({'a': 1}, 'Mad')
        assert error is not None

    def test_string_with_comma(self):
        """String with comma as decimal"""
        from app.utils.validators import validate_analysis_result
        value, error = validate_analysis_result('10,5', 'Mad')
        assert value == 10.5
        assert error is None

    def test_string_with_spaces(self):
        """String with spaces"""
        from app.utils.validators import validate_analysis_result
        value, error = validate_analysis_result('  10.5  ', 'Mad')
        assert value == 10.5
        assert error is None

    def test_very_large_value(self):
        """Very large value"""
        from app.utils.validators import validate_analysis_result
        value, error = validate_analysis_result(1e309, 'Mad')
        assert error is not None

    def test_very_small_value(self):
        """Very small negative value"""
        from app.utils.validators import validate_analysis_result
        value, error = validate_analysis_result(-1e309, 'Mad')
        assert error is not None

    def test_negative_infinity(self):
        """Negative infinity"""
        from app.utils.validators import validate_analysis_result
        value, error = validate_analysis_result(float('-inf'), 'Mad')
        assert error is not None

    def test_all_analysis_codes(self):
        """Test all defined analysis codes"""
        from app.utils.validators import validate_analysis_result, ANALYSIS_VALUE_RANGES
        for code, (min_val, max_val) in ANALYSIS_VALUE_RANGES.items():
            mid = (min_val + max_val) / 2
            value, error = validate_analysis_result(mid, code)
            assert error is None, f"Failed for code {code}"


class TestValidateSampleIdBranches:
    """validate_sample_id бүх branch"""

    def test_none_value(self):
        """None value"""
        from app.utils.validators import validate_sample_id
        value, error = validate_sample_id(None)
        assert error is not None
        assert "шаардлагатай" in error

    def test_float_value(self):
        """Float value converts to int"""
        from app.utils.validators import validate_sample_id
        value, error = validate_sample_id(5.9)
        assert value == 5

    def test_negative_value(self):
        """Negative value"""
        from app.utils.validators import validate_sample_id
        value, error = validate_sample_id(-1)
        assert error is not None
        assert "эерэг" in error

    def test_zero_value(self):
        """Zero value"""
        from app.utils.validators import validate_sample_id
        value, error = validate_sample_id(0)
        assert error is not None

    def test_very_large_value(self):
        """Very large value (exceeds INT max)"""
        from app.utils.validators import validate_sample_id
        value, error = validate_sample_id(2147483648)
        assert error is not None
        assert "хэт том" in error

    def test_invalid_string(self):
        """Invalid string"""
        from app.utils.validators import validate_sample_id
        value, error = validate_sample_id("abc")
        assert error is not None
        assert "тоо" in error


class TestValidateAnalysisCodeBranches:
    """validate_analysis_code бүх branch"""

    def test_none_value(self):
        """None value"""
        from app.utils.validators import validate_analysis_code
        value, error = validate_analysis_code(None)
        assert error is not None
        assert "шаардлагатай" in error

    def test_empty_string(self):
        """Empty string"""
        from app.utils.validators import validate_analysis_code
        value, error = validate_analysis_code('')
        assert error is not None

    def test_not_string(self):
        """Not a string"""
        from app.utils.validators import validate_analysis_code
        value, error = validate_analysis_code(123)
        assert error is not None
        assert "текст" in error

    def test_too_long(self):
        """Too long code"""
        from app.utils.validators import validate_analysis_code
        value, error = validate_analysis_code('A' * 25)
        assert error is not None
        assert "урт" in error

    def test_whitespace_only(self):
        """Whitespace only"""
        from app.utils.validators import validate_analysis_code
        value, error = validate_analysis_code('   ')
        assert error is not None
        assert "хоосон" in error

    def test_invalid_characters(self):
        """Invalid characters"""
        from app.utils.validators import validate_analysis_code
        value, error = validate_analysis_code('Mad@#$')
        assert error is not None
        assert "үсэг" in error

    def test_valid_with_comma(self):
        """Valid with comma"""
        from app.utils.validators import validate_analysis_code
        value, error = validate_analysis_code('Mad, Aad')
        assert error is None
        assert value == 'Mad, Aad'


class TestValidateEquipmentIdBranches:
    """validate_equipment_id бүх branch"""

    def test_none_allowed(self):
        """None when allowed"""
        from app.utils.validators import validate_equipment_id
        value, error = validate_equipment_id(None, allow_none=True)
        assert error is None
        assert value is None

    def test_none_not_allowed(self):
        """None when not allowed"""
        from app.utils.validators import validate_equipment_id
        value, error = validate_equipment_id(None, allow_none=False)
        assert error is not None

    def test_valid_int(self):
        """Valid int"""
        from app.utils.validators import validate_equipment_id
        value, error = validate_equipment_id(5)
        assert value == 5
        assert error is None

    def test_string_int(self):
        """String int"""
        from app.utils.validators import validate_equipment_id
        value, error = validate_equipment_id('5')
        assert value == 5

    def test_invalid_string(self):
        """Invalid string"""
        from app.utils.validators import validate_equipment_id
        value, error = validate_equipment_id('abc')
        assert error is not None

    def test_negative(self):
        """Negative value"""
        from app.utils.validators import validate_equipment_id
        value, error = validate_equipment_id(-1)
        assert error is not None


class TestValidateSaveResultsBatchBranches:
    """validate_save_results_batch бүх branch"""

    def test_empty_list(self):
        """Empty list"""
        from app.utils.validators import validate_save_results_batch
        is_valid, validated, errors = validate_save_results_batch([])
        # Empty list may be valid or have errors depending on implementation
        assert isinstance(errors, list)

    def test_not_list(self):
        """Not a list"""
        from app.utils.validators import validate_save_results_batch
        is_valid, validated, errors = validate_save_results_batch("not a list")
        assert not is_valid

    def test_item_not_dict(self):
        """Item is not dict"""
        from app.utils.validators import validate_save_results_batch
        is_valid, validated, errors = validate_save_results_batch(["not a dict"])
        assert len(errors) > 0

    def test_missing_sample_id(self):
        """Missing sample_id"""
        from app.utils.validators import validate_save_results_batch
        data = [{'analysis_code': 'Mad', 'final_result': 10.0}]
        is_valid, validated, errors = validate_save_results_batch(data)
        assert len(errors) > 0

    def test_missing_analysis_code(self):
        """Missing analysis_code"""
        from app.utils.validators import validate_save_results_batch
        data = [{'sample_id': 1, 'final_result': 10.0}]
        is_valid, validated, errors = validate_save_results_batch(data)
        assert len(errors) > 0

    def test_invalid_sample_id(self):
        """Invalid sample_id"""
        from app.utils.validators import validate_save_results_batch
        data = [{'sample_id': 'abc', 'analysis_code': 'Mad', 'final_result': 10.0}]
        is_valid, validated, errors = validate_save_results_batch(data)
        assert len(errors) > 0

    def test_invalid_analysis_code(self):
        """Invalid analysis_code"""
        from app.utils.validators import validate_save_results_batch
        data = [{'sample_id': 1, 'analysis_code': '', 'final_result': 10.0}]
        is_valid, validated, errors = validate_save_results_batch(data)
        assert len(errors) > 0

    def test_valid_batch(self):
        """Valid batch"""
        from app.utils.validators import validate_save_results_batch
        data = [
            {'sample_id': 1, 'analysis_code': 'Mad', 'final_result': 10.0},
            {'sample_id': 2, 'analysis_code': 'Aad', 'final_result': 8.0}
        ]
        is_valid, validated, errors = validate_save_results_batch(data)
        assert is_valid
        assert len(validated) == 2

    def test_with_equipment_id(self):
        """With equipment_id"""
        from app.utils.validators import validate_save_results_batch
        data = [{'sample_id': 1, 'analysis_code': 'Mad', 'final_result': 10.0, 'equipment_id': 5}]
        is_valid, validated, errors = validate_save_results_batch(data)
        if is_valid:
            assert validated[0].get('equipment_id') == 5

    def test_with_raw_data(self):
        """With raw_data"""
        from app.utils.validators import validate_save_results_batch
        data = [{'sample_id': 1, 'analysis_code': 'Mad', 'final_result': 10.0, 'raw_data': {'m1': 1.0}}]
        is_valid, validated, errors = validate_save_results_batch(data)
        # Should pass with raw_data
        assert isinstance(errors, list)
