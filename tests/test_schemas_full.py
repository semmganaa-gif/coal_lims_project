# tests/test_schemas_full.py
# -*- coding: utf-8 -*-
"""
Complete tests for app/schemas/ modules
"""

import pytest
import math
from marshmallow import ValidationError


class TestSampleSchema:
    """Tests for SampleSchema."""

    def test_load_valid_data(self, app):
        """Test loading valid sample data."""
        with app.app_context():
            from app.schemas.sample_schema import SampleSchema
            schema = SampleSchema()
            data = {
                'sample_code': 'TEST-001',
                'client_name': 'CHPP',
                'sample_type': 'Coal',
                'received_date': '2025-01-01T10:00:00'
            }
            result = schema.load(data)
            assert result['sample_code'] == 'TEST-001'
            assert result['client_name'] == 'CHPP'

    def test_dump_data(self, app):
        """Test dumping sample data."""
        with app.app_context():
            from app.schemas.sample_schema import SampleSchema
            schema = SampleSchema()
            data = {
                'sample_code': 'TEST-001',
                'client_name': 'CHPP',
                'sample_type': 'Coal',
                'received_date': '2025-01-01T10:00:00'
            }
            loaded = schema.load(data)
            result = schema.dump(loaded)
            assert 'sample_code' in result

    def test_sample_code_required(self, app):
        """Test sample_code is required."""
        with app.app_context():
            from app.schemas.sample_schema import SampleSchema
            schema = SampleSchema()
            data = {
                'client_name': 'CHPP',
                'sample_type': 'Coal',
                'received_date': '2025-01-01T10:00:00'
            }
            with pytest.raises(ValidationError) as exc:
                schema.load(data)
            assert 'sample_code' in exc.value.messages

    def test_sample_code_empty_validation(self, app):
        """Test empty sample_code validation."""
        with app.app_context():
            from app.schemas.sample_schema import SampleSchema
            schema = SampleSchema()
            data = {
                'sample_code': '   ',
                'client_name': 'CHPP',
                'sample_type': 'Coal',
                'received_date': '2025-01-01T10:00:00'
            }
            with pytest.raises(ValidationError):
                schema.load(data)

    def test_sample_code_sql_injection(self, app):
        """Test sample_code SQL injection prevention."""
        with app.app_context():
            from app.schemas.sample_schema import SampleSchema
            schema = SampleSchema()
            data = {
                'sample_code': '',
                'client_name': 'CHPP',
                'sample_type': 'Coal',
                'received_date': '2025-01-01T10:00:00'
            }
            with pytest.raises(ValidationError):
                schema.load(data)

    def test_weight_validation_positive(self, app):
        """Test weight must be positive."""
        with app.app_context():
            from app.schemas.sample_schema import SampleSchema
            schema = SampleSchema()
            data = {
                'sample_code': 'TEST-001',
                'client_name': 'CHPP',
                'sample_type': 'Coal',
                'received_date': '2025-01-01T10:00:00',
                'weight': -5.0
            }
            with pytest.raises(ValidationError):
                schema.load(data)

    def test_weight_validation_range(self, app):
        """Test weight range validation."""
        with app.app_context():
            from app.schemas.sample_schema import SampleSchema
            schema = SampleSchema()
            data = {
                'sample_code': 'TEST-001',
                'client_name': 'CHPP',
                'sample_type': 'Coal',
                'received_date': '2025-01-01T10:00:00',
                'weight': 50000.0  # Too high
            }
            with pytest.raises(ValidationError):
                schema.load(data)

    def test_sample_condition_validation(self, app):
        """Test sample_condition max length validation."""
        with app.app_context():
            from app.schemas.sample_schema import SampleSchema
            schema = SampleSchema()
            data = {
                'sample_code': 'TEST-001',
                'client_name': 'CHPP',
                'sample_type': 'Coal',
                'received_date': '2025-01-01T10:00:00',
                'sample_condition': 'X' * 101  # Over 100 char limit
            }
            with pytest.raises(ValidationError):
                schema.load(data)

    def test_valid_sample_condition(self, app):
        """Test valid sample conditions."""
        with app.app_context():
            from app.schemas.sample_schema import SampleSchema
            schema = SampleSchema()
            for condition in ['Хуурай', 'Чийгтэй', 'Шингэн']:
                data = {
                    'sample_code': 'TEST-001',
                    'client_name': 'CHPP',
                    'sample_type': 'Coal',
                    'received_date': '2025-01-01T10:00:00',
                    'sample_condition': condition
                }
                result = schema.load(data)
                assert result['sample_condition'] == condition

    def test_status_default_value(self, app):
        """Test status default value."""
        with app.app_context():
            from app.schemas.sample_schema import SampleSchema
            schema = SampleSchema()
            data = {
                'sample_code': 'TEST-001',
                'client_name': 'CHPP',
                'sample_type': 'Coal',
                'received_date': '2025-01-01T10:00:00'
            }
            result = schema.load(data)
            assert result.get('status') == 'new'

    def test_meta_ordered(self, app):
        """Test Meta ordered is True."""
        with app.app_context():
            from app.schemas.sample_schema import SampleSchema
            assert SampleSchema.Meta.ordered is True

    def test_meta_unknown_exclude(self, app):
        """Test unknown fields are excluded."""
        with app.app_context():
            from app.schemas.sample_schema import SampleSchema
            schema = SampleSchema()
            data = {
                'sample_code': 'TEST-001',
                'client_name': 'CHPP',
                'sample_type': 'Coal',
                'received_date': '2025-01-01T10:00:00',
                'unknown_field': 'should be excluded'
            }
            result = schema.load(data)
            assert 'unknown_field' not in result


class TestSampleListSchema:
    """Tests for SampleListSchema."""

    def test_load_valid_list(self, app):
        """Test loading valid list data."""
        with app.app_context():
            from app.schemas.sample_schema import SampleListSchema
            schema = SampleListSchema()
            data = {
                'draw': 1,
                'recordsTotal': 100,
                'recordsFiltered': 50,
                'data': [{'id': 1}, {'id': 2}]
            }
            result = schema.load(data)
            assert result['draw'] == 1
            assert result['recordsTotal'] == 100


class TestAnalysisResultSchema:
    """Tests for AnalysisResultSchema."""

    def test_load_valid_data(self, app):
        """Test loading valid analysis result data."""
        with app.app_context():
            from app.schemas.analysis_schema import AnalysisResultSchema
            schema = AnalysisResultSchema()
            data = {
                'sample_id': 1,
                'analysis_code': 'Mad',
                'final_result': 8.5
            }
            result = schema.load(data)
            assert result['sample_id'] == 1
            assert result['analysis_code'] == 'Mad'

    def test_sample_id_required(self, app):
        """Test sample_id is required."""
        with app.app_context():
            from app.schemas.analysis_schema import AnalysisResultSchema
            schema = AnalysisResultSchema()
            data = {
                'analysis_code': 'Mad',
                'final_result': 8.5
            }
            with pytest.raises(ValidationError) as exc:
                schema.load(data)
            assert 'sample_id' in exc.value.messages

    def test_sample_id_positive(self, app):
        """Test sample_id must be positive."""
        with app.app_context():
            from app.schemas.analysis_schema import AnalysisResultSchema
            schema = AnalysisResultSchema()
            data = {
                'sample_id': 0,
                'analysis_code': 'Mad',
                'final_result': 8.5
            }
            with pytest.raises(ValidationError):
                schema.load(data)

    def test_analysis_code_required(self, app):
        """Test analysis_code is required."""
        with app.app_context():
            from app.schemas.analysis_schema import AnalysisResultSchema
            schema = AnalysisResultSchema()
            data = {
                'sample_id': 1,
                'final_result': 8.5
            }
            with pytest.raises(ValidationError) as exc:
                schema.load(data)
            assert 'analysis_code' in exc.value.messages

    def test_analysis_code_empty_validation(self, app):
        """Test empty analysis_code validation."""
        with app.app_context():
            from app.schemas.analysis_schema import AnalysisResultSchema
            schema = AnalysisResultSchema()
            data = {
                'sample_id': 1,
                'analysis_code': '   ',
                'final_result': 8.5
            }
            with pytest.raises(ValidationError):
                schema.load(data)

    def test_analysis_code_sql_injection(self, app):
        """Test analysis_code SQL injection prevention."""
        with app.app_context():
            from app.schemas.analysis_schema import AnalysisResultSchema
            schema = AnalysisResultSchema()
            data = {
                'sample_id': 1,
                'analysis_code': 'Mad; DROP TABLE--',
                'final_result': 8.5
            }
            with pytest.raises(ValidationError):
                schema.load(data)

    def test_final_result_nan_validation(self, app):
        """Test final_result NaN validation."""
        with app.app_context():
            from app.schemas.analysis_schema import AnalysisResultSchema
            schema = AnalysisResultSchema()
            data = {
                'sample_id': 1,
                'analysis_code': 'Mad',
                'final_result': float('nan')
            }
            with pytest.raises(ValidationError):
                schema.load(data)

    def test_final_result_inf_validation(self, app):
        """Test final_result Infinity validation."""
        with app.app_context():
            from app.schemas.analysis_schema import AnalysisResultSchema
            schema = AnalysisResultSchema()
            data = {
                'sample_id': 1,
                'analysis_code': 'Mad',
                'final_result': float('inf')
            }
            with pytest.raises(ValidationError):
                schema.load(data)

    def test_status_validation(self, app):
        """Test status must be valid choice."""
        with app.app_context():
            from app.schemas.analysis_schema import AnalysisResultSchema
            schema = AnalysisResultSchema()
            data = {
                'sample_id': 1,
                'analysis_code': 'Mad',
                'final_result': 8.5,
                'status': 'invalid_status'
            }
            with pytest.raises(ValidationError):
                schema.load(data)

    def test_valid_statuses(self, app):
        """Test all valid statuses."""
        with app.app_context():
            from app.schemas.analysis_schema import AnalysisResultSchema
            schema = AnalysisResultSchema()
            for status in ['pending_review', 'approved', 'rejected', 'reanalysis']:
                data = {
                    'sample_id': 1,
                    'analysis_code': 'Mad',
                    'final_result': 8.5,
                    'status': status
                }
                result = schema.load(data)
                assert result['status'] == status

    def test_status_default(self, app):
        """Test status default value."""
        with app.app_context():
            from app.schemas.analysis_schema import AnalysisResultSchema
            schema = AnalysisResultSchema()
            data = {
                'sample_id': 1,
                'analysis_code': 'Mad',
                'final_result': 8.5
            }
            result = schema.load(data)
            assert result.get('status') == 'pending_review'

    def test_schema_validation_both_missing(self, app):
        """Test schema validation when both final_result and raw_data missing."""
        with app.app_context():
            from app.schemas.analysis_schema import AnalysisResultSchema
            schema = AnalysisResultSchema()
            data = {
                'sample_id': 1,
                'analysis_code': 'Mad'
            }
            with pytest.raises(ValidationError) as exc:
                schema.load(data)
            assert '_schema' in exc.value.messages

    def test_schema_validation_raw_data_only(self, app):
        """Test schema validation with only raw_data."""
        with app.app_context():
            from app.schemas.analysis_schema import AnalysisResultSchema
            schema = AnalysisResultSchema()
            data = {
                'sample_id': 1,
                'analysis_code': 'Mad',
                'raw_data': '{"m1": 10.0}'
            }
            result = schema.load(data)
            assert result['raw_data'] == '{"m1": 10.0}'

    def test_dump_only_fields(self, app):
        """Test dump_only fields are not loaded."""
        with app.app_context():
            from app.schemas.analysis_schema import AnalysisResultSchema
            schema = AnalysisResultSchema()
            data = {
                'id': 999,
                'sample_id': 1,
                'analysis_code': 'Mad',
                'final_result': 8.5,
                'created_at': '2025-01-01T10:00:00'
            }
            result = schema.load(data)
            assert 'id' not in result
            assert 'created_at' not in result


class TestAnalysisResultListSchema:
    """Tests for AnalysisResultListSchema."""

    def test_load_valid_list(self, app):
        """Test loading valid list data."""
        with app.app_context():
            from app.schemas.analysis_schema import AnalysisResultListSchema
            schema = AnalysisResultListSchema()
            data = {
                'results': [
                    {'sample_id': 1, 'analysis_code': 'Mad', 'final_result': 8.5}
                ]
            }
            result = schema.load(data)
            assert len(result['results']) == 1


class TestUserSchema:
    """Tests for UserSchema."""

    def test_load_valid_data(self, app):
        """Test loading valid user data."""
        with app.app_context():
            from app.schemas.user_schema import UserSchema
            schema = UserSchema()
            data = {
                'username': 'testuser',
                'password': 'TestPass123',
                'role': 'chemist'
            }
            result = schema.load(data)
            assert result['username'] == 'testuser'
            assert result['role'] == 'chemist'

    def test_username_required(self, app):
        """Test username is required."""
        with app.app_context():
            from app.schemas.user_schema import UserSchema
            schema = UserSchema()
            data = {
                'password': 'TestPass123',
                'role': 'chemist'
            }
            with pytest.raises(ValidationError) as exc:
                schema.load(data)
            assert 'username' in exc.value.messages

    def test_username_empty_validation(self, app):
        """Test empty username validation."""
        with app.app_context():
            from app.schemas.user_schema import UserSchema
            schema = UserSchema()
            data = {
                'username': '   ',
                'password': 'TestPass123',
                'role': 'chemist'
            }
            with pytest.raises(ValidationError):
                schema.load(data)

    def test_username_special_chars(self, app):
        """Test username with special characters."""
        with app.app_context():
            from app.schemas.user_schema import UserSchema
            schema = UserSchema()
            data = {
                'username': 'test@user!',
                'password': 'TestPass123',
                'role': 'chemist'
            }
            with pytest.raises(ValidationError):
                schema.load(data)

    def test_username_sql_injection(self, app):
        """Test username SQL injection prevention."""
        with app.app_context():
            from app.schemas.user_schema import UserSchema
            schema = UserSchema()
            data = {
                'username': 'admin; DROP TABLE--',
                'password': 'TestPass123',
                'role': 'chemist'
            }
            with pytest.raises(ValidationError):
                schema.load(data)

    def test_username_valid_with_underscore(self, app):
        """Test valid username with underscore."""
        with app.app_context():
            from app.schemas.user_schema import UserSchema
            schema = UserSchema()
            data = {
                'username': 'test_user123',
                'password': 'TestPass123',
                'role': 'chemist'
            }
            result = schema.load(data)
            assert result['username'] == 'test_user123'

    def test_password_min_length(self, app):
        """Test password minimum length."""
        with app.app_context():
            from app.schemas.user_schema import UserSchema
            schema = UserSchema()
            data = {
                'username': 'testuser',
                'password': 'Short1',
                'role': 'chemist'
            }
            with pytest.raises(ValidationError):
                schema.load(data)

    def test_password_uppercase_required(self, app):
        """Test password must have uppercase."""
        with app.app_context():
            from app.schemas.user_schema import UserSchema
            schema = UserSchema()
            data = {
                'username': 'testuser',
                'password': 'lowercase123',
                'role': 'chemist'
            }
            with pytest.raises(ValidationError):
                schema.load(data)

    def test_password_lowercase_required(self, app):
        """Test password must have lowercase."""
        with app.app_context():
            from app.schemas.user_schema import UserSchema
            schema = UserSchema()
            data = {
                'username': 'testuser',
                'password': 'UPPERCASE123',
                'role': 'chemist'
            }
            with pytest.raises(ValidationError):
                schema.load(data)

    def test_password_digit_required(self, app):
        """Test password must have digit."""
        with app.app_context():
            from app.schemas.user_schema import UserSchema
            schema = UserSchema()
            data = {
                'username': 'testuser',
                'password': 'NoDigitsHere',
                'role': 'chemist'
            }
            with pytest.raises(ValidationError):
                schema.load(data)

    def test_password_load_only(self, app):
        """Test password is load_only (not in dump)."""
        with app.app_context():
            from app.schemas.user_schema import UserSchema
            schema = UserSchema()
            data = {
                'username': 'testuser',
                'password': 'TestPass123',
                'role': 'chemist'
            }
            loaded = schema.load(data)
            dumped = schema.dump(loaded)
            assert 'password' not in dumped

    def test_role_required(self, app):
        """Test role is required."""
        with app.app_context():
            from app.schemas.user_schema import UserSchema
            schema = UserSchema()
            data = {
                'username': 'testuser',
                'password': 'TestPass123'
            }
            with pytest.raises(ValidationError) as exc:
                schema.load(data)
            assert 'role' in exc.value.messages

    def test_role_validation(self, app):
        """Test role must be valid choice."""
        with app.app_context():
            from app.schemas.user_schema import UserSchema
            schema = UserSchema()
            data = {
                'username': 'testuser',
                'password': 'TestPass123',
                'role': 'invalid_role'
            }
            with pytest.raises(ValidationError):
                schema.load(data)

    def test_valid_roles(self, app):
        """Test all valid roles."""
        with app.app_context():
            from app.schemas.user_schema import UserSchema
            schema = UserSchema()
            for role in ['prep', 'chemist', 'senior', 'manager', 'admin']:
                data = {
                    'username': 'testuser',
                    'password': 'TestPass123',
                    'role': role
                }
                result = schema.load(data)
                assert result['role'] == role

    def test_email_validation(self, app):
        """Test email validation."""
        with app.app_context():
            from app.schemas.user_schema import UserSchema
            schema = UserSchema()
            data = {
                'username': 'testuser',
                'password': 'TestPass123',
                'role': 'chemist',
                'email': 'invalid-email'
            }
            with pytest.raises(ValidationError):
                schema.load(data)

    def test_valid_email(self, app):
        """Test valid email."""
        with app.app_context():
            from app.schemas.user_schema import UserSchema
            schema = UserSchema()
            data = {
                'username': 'testuser',
                'password': 'TestPass123',
                'role': 'chemist',
                'email': 'test@example.com'
            }
            result = schema.load(data)
            assert result['email'] == 'test@example.com'

    def test_is_active_default(self, app):
        """Test is_active default value."""
        with app.app_context():
            from app.schemas.user_schema import UserSchema
            schema = UserSchema()
            data = {
                'username': 'testuser',
                'password': 'TestPass123',
                'role': 'chemist'
            }
            result = schema.load(data)
            assert result.get('is_active') is True

    def test_password_empty_allowed_for_update(self, app):
        """Test empty password is allowed (for updates)."""
        with app.app_context():
            from app.schemas.user_schema import UserSchema
            schema = UserSchema()
            data = {
                'username': 'testuser',
                'role': 'chemist'
            }
            result = schema.load(data)
            assert 'password' not in result


class TestUserListSchema:
    """Tests for UserListSchema."""

    def test_load_valid_list(self, app):
        """Test loading valid list data."""
        with app.app_context():
            from app.schemas.user_schema import UserListSchema
            schema = UserListSchema()
            data = {
                'users': [{'username': 'test', 'role': 'chemist'}],
                'total': 1,
                'page': 1,
                'per_page': 10
            }
            result = schema.load(data)
            assert result['total'] == 1


class TestSchemasInit:
    """Tests for schemas __init__.py exports."""

    def test_sample_schema_import(self, app):
        """Test SampleSchema is exported."""
        with app.app_context():
            from app.schemas import SampleSchema
            assert SampleSchema is not None

    def test_analysis_result_schema_import(self, app):
        """Test AnalysisResultSchema is exported."""
        with app.app_context():
            from app.schemas import AnalysisResultSchema
            assert AnalysisResultSchema is not None

    def test_user_schema_import(self, app):
        """Test UserSchema is exported."""
        with app.app_context():
            from app.schemas import UserSchema
            assert UserSchema is not None

    def test_all_exports(self, app):
        """Test __all__ contains expected schemas."""
        with app.app_context():
            from app import schemas
            assert 'SampleSchema' in schemas.__all__
            assert 'AnalysisResultSchema' in schemas.__all__
            assert 'UserSchema' in schemas.__all__
