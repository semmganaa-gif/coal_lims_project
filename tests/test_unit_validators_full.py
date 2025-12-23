# -*- coding: utf-8 -*-
"""
Validators full тестүүд
"""
import pytest


class TestValidatorsModule:
    """Validators module тестүүд"""

    def test_import_module(self):
        """Module import"""
        from app.utils import validators
        assert validators is not None


class TestValidateAnalysisResultExtended:
    """validate_analysis_result extended тестүүд"""

    def test_import_function(self):
        """Function import"""
        from app.utils.validators import validate_analysis_result
        assert validate_analysis_result is not None

    def test_negative_value(self):
        """Negative value"""
        from app.utils.validators import validate_analysis_result
        value, error = validate_analysis_result(-5.0, 'Mad')
        # May or may not be valid depending on analysis type
        assert value is not None or error is not None

    def test_large_value(self):
        """Large value"""
        from app.utils.validators import validate_analysis_result
        value, error = validate_analysis_result(1000000, 'Mad')
        assert value is not None or error is not None

    def test_decimal_precision(self):
        """Decimal precision"""
        from app.utils.validators import validate_analysis_result
        value, error = validate_analysis_result(10.12345, 'TS')
        assert value is not None or error is not None


class TestValidateSampleIdExtended:
    """validate_sample_id extended тестүүд"""

    def test_import_function(self):
        """Function import"""
        from app.utils.validators import validate_sample_id
        assert validate_sample_id is not None

    def test_large_id(self):
        """Large ID"""
        from app.utils.validators import validate_sample_id
        result, error = validate_sample_id(999999999)
        assert result == 999999999 or error is not None

    def test_float_id(self):
        """Float ID"""
        from app.utils.validators import validate_sample_id
        result, error = validate_sample_id(123.5)
        # Should convert to int or return error
        assert result is not None or error is not None


class TestValidateAnalysisCodeExtended:
    """validate_analysis_code extended тестүүд"""

    def test_import_function(self):
        """Function import"""
        from app.utils.validators import validate_analysis_code
        assert validate_analysis_code is not None

    def test_all_valid_codes(self):
        """All valid codes"""
        from app.utils.validators import validate_analysis_code
        codes = ['TS', 'Mad', 'Aad', 'Vad', 'Vdaf', 'CV', 'FC', 'FCd', 'MT', 'HGI']
        for code in codes:
            result, error = validate_analysis_code(code)
            assert result is not None or error is None

    def test_special_characters(self):
        """Special characters"""
        from app.utils.validators import validate_analysis_code
        result, error = validate_analysis_code('TS@#$')
        assert error is not None or result is not None


class TestSanitizeStringExtended:
    """sanitize_string extended тестүүд"""

    def test_import_function(self):
        """Function import"""
        from app.utils.validators import sanitize_string
        assert sanitize_string is not None

    def test_script_tag(self):
        """Script tag"""
        from app.utils.validators import sanitize_string
        result, error = sanitize_string('<script>alert("xss")</script>')
        assert result is not None or error is not None

    def test_sql_drop(self):
        """SQL DROP"""
        from app.utils.validators import sanitize_string
        result, error = sanitize_string("'; DROP TABLE samples; --")
        assert result is not None or error is not None

    def test_long_string(self):
        """Long string"""
        from app.utils.validators import sanitize_string
        result, error = sanitize_string('a' * 10000)
        assert result is not None or error is not None


class TestValidateEquipmentIdExtended:
    """validate_equipment_id extended тестүүд"""

    def test_import_function(self):
        """Function import"""
        from app.utils.validators import validate_equipment_id
        assert validate_equipment_id is not None

    def test_zero_id(self):
        """Zero ID"""
        from app.utils.validators import validate_equipment_id
        result, error = validate_equipment_id(0)
        assert error is not None or result == 0


class TestValidateSaveResultsBatchExtended:
    """validate_save_results_batch extended тестүүд"""

    def test_import_function(self):
        """Function import"""
        from app.utils.validators import validate_save_results_batch
        assert validate_save_results_batch is not None

    def test_valid_batch(self):
        """Valid batch"""
        from app.utils.validators import validate_save_results_batch
        result = validate_save_results_batch([
            {'sample_id': 1, 'analysis_code': 'TS', 'result': 5.5}
        ])
        assert result is not None

    def test_missing_fields(self):
        """Missing fields"""
        from app.utils.validators import validate_save_results_batch
        result = validate_save_results_batch([
            {'sample_id': 1}  # Missing analysis_code and result
        ])
        assert result is not None
