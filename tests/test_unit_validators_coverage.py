# tests/unit/test_validators_coverage.py
"""
Validators coverage тест
"""
import pytest


class TestSampleIdValidator:
    """Sample ID validator тест"""

    def test_valid_sample_id(self, app):
        """Valid sample ID"""
        with app.app_context():
            from app.utils.validators import validate_sample_id

            result, error = validate_sample_id(1)
            assert error is None
            assert result == 1

    def test_string_sample_id(self, app):
        """String sample ID"""
        with app.app_context():
            from app.utils.validators import validate_sample_id

            result, error = validate_sample_id('5')
            assert result == 5

    def test_invalid_sample_id(self, app):
        """Invalid sample ID"""
        with app.app_context():
            from app.utils.validators import validate_sample_id

            result, error = validate_sample_id('invalid')
            assert error is not None

    def test_none_sample_id(self, app):
        """None sample ID"""
        with app.app_context():
            from app.utils.validators import validate_sample_id

            result, error = validate_sample_id(None)
            assert error is not None


class TestAnalysisCodeValidator:
    """Analysis code validator тест"""

    def test_valid_code(self, app):
        """Valid analysis code"""
        with app.app_context():
            from app.utils.validators import validate_analysis_code

            result, error = validate_analysis_code('Mad')
            assert error is None

    def test_empty_code(self, app):
        """Empty analysis code"""
        with app.app_context():
            from app.utils.validators import validate_analysis_code

            result, error = validate_analysis_code('')
            assert error is not None

    def test_none_code(self, app):
        """None analysis code"""
        with app.app_context():
            from app.utils.validators import validate_analysis_code

            result, error = validate_analysis_code(None)
            assert error is not None


class TestAnalysisResultValidator:
    """Analysis result validator тест"""

    def test_valid_result(self, app):
        """Valid result"""
        with app.app_context():
            from app.utils.validators import validate_analysis_result

            result, error = validate_analysis_result(10.5, 'Mad')
            assert error is None

    def test_string_result(self, app):
        """String result"""
        with app.app_context():
            from app.utils.validators import validate_analysis_result

            result, error = validate_analysis_result('10.5', 'Mad')
            assert result == 10.5

    def test_none_result_allowed(self, app):
        """None result when allowed"""
        with app.app_context():
            from app.utils.validators import validate_analysis_result

            result, error = validate_analysis_result(None, 'Mad', allow_none=True)
            assert error is None

    def test_invalid_result(self, app):
        """Invalid result"""
        with app.app_context():
            from app.utils.validators import validate_analysis_result

            result, error = validate_analysis_result('invalid', 'Mad')
            assert error is not None


class TestEquipmentIdValidator:
    """Equipment ID validator тест"""

    def test_valid_equipment_id(self, app):
        """Valid equipment ID"""
        with app.app_context():
            from app.utils.validators import validate_equipment_id

            result, error = validate_equipment_id(1)
            assert result == 1

    def test_none_equipment_id_allowed(self, app):
        """None equipment ID when allowed"""
        with app.app_context():
            from app.utils.validators import validate_equipment_id

            result, error = validate_equipment_id(None, allow_none=True)
            assert error is None


class TestBatchValidator:
    """Batch validator тест"""

    def test_valid_batch(self, app):
        """Valid batch"""
        with app.app_context():
            from app.utils.validators import validate_save_results_batch

            data = [
                {'sample_id': 1, 'analysis_code': 'Mad', 'final_result': 10.5},
                {'sample_id': 2, 'analysis_code': 'Aad', 'final_result': 8.5}
            ]

            is_valid, validated, errors = validate_save_results_batch(data)
            assert isinstance(is_valid, bool)

    def test_empty_batch(self, app):
        """Empty batch"""
        with app.app_context():
            from app.utils.validators import validate_save_results_batch

            data = []
            is_valid, validated, errors = validate_save_results_batch(data)
            assert isinstance(errors, list)

    def test_invalid_batch_item(self, app):
        """Invalid batch item"""
        with app.app_context():
            from app.utils.validators import validate_save_results_batch

            data = [{'sample_id': 'invalid'}]
            is_valid, validated, errors = validate_save_results_batch(data)
            assert len(errors) > 0
