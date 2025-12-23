# tests/unit/test_schemas_comprehensive.py
# -*- coding: utf-8 -*-
"""
Marshmallow Schemas-ийн тест
Coverage: user_schema.py, sample_schema.py, analysis_schema.py
"""

import pytest
from marshmallow import ValidationError
from datetime import datetime


class TestUserSchema:
    """UserSchema тестүүд"""

    @pytest.fixture
    def schema(self):
        from app.schemas.user_schema import UserSchema
        return UserSchema()

    def test_valid_user_data(self, schema):
        """Valid user data should pass validation"""
        data = {
            'username': 'test_user',
            'password': 'Password123',
            'role': 'chemist',
            'email': 'test@example.com',
            'full_name': 'Test User',
            'is_active': True
        }
        result = schema.load(data)
        assert result['username'] == 'test_user'
        assert result['role'] == 'chemist'

    def test_username_required(self, schema):
        """Username is required"""
        with pytest.raises(ValidationError) as exc:
            schema.load({'role': 'chemist', 'password': 'Password123'})
        assert 'username' in exc.value.messages

    def test_username_min_length(self, schema):
        """Username must be at least 3 characters"""
        with pytest.raises(ValidationError) as exc:
            schema.load({'username': 'ab', 'role': 'chemist', 'password': 'Password123'})
        assert 'username' in exc.value.messages

    def test_username_max_length(self, schema):
        """Username must be at most 64 characters"""
        with pytest.raises(ValidationError) as exc:
            schema.load({'username': 'a' * 65, 'role': 'chemist', 'password': 'Password123'})
        assert 'username' in exc.value.messages

    def test_username_alphanumeric_only(self, schema):
        """Username should only contain alphanumeric and underscore"""
        with pytest.raises(ValidationError) as exc:
            schema.load({'username': 'test@user', 'role': 'chemist', 'password': 'Password123'})
        assert 'username' in exc.value.messages

    def test_username_sql_injection_prevention(self, schema):
        """Username should prevent SQL injection"""
        dangerous_usernames = ['test;DROP', 'test--comment', 'test/*', 'testDELETE']
        for username in dangerous_usernames:
            with pytest.raises(ValidationError):
                schema.load({'username': username, 'role': 'chemist', 'password': 'Password123'})

    def test_password_min_length(self, schema):
        """Password must be at least 8 characters"""
        with pytest.raises(ValidationError) as exc:
            schema.load({'username': 'testuser', 'role': 'chemist', 'password': 'Pass1'})
        assert 'password' in exc.value.messages

    def test_password_requires_uppercase(self, schema):
        """Password must contain uppercase letter"""
        with pytest.raises(ValidationError) as exc:
            schema.load({'username': 'testuser', 'role': 'chemist', 'password': 'password123'})
        assert 'password' in exc.value.messages

    def test_password_requires_lowercase(self, schema):
        """Password must contain lowercase letter"""
        with pytest.raises(ValidationError) as exc:
            schema.load({'username': 'testuser', 'role': 'chemist', 'password': 'PASSWORD123'})
        assert 'password' in exc.value.messages

    def test_password_requires_digit(self, schema):
        """Password must contain digit"""
        with pytest.raises(ValidationError) as exc:
            schema.load({'username': 'testuser', 'role': 'chemist', 'password': 'Passwordabc'})
        assert 'password' in exc.value.messages

    def test_role_valid_values(self, schema):
        """Role must be one of valid values"""
        valid_roles = ['prep', 'chemist', 'senior', 'manager', 'admin']
        for role in valid_roles:
            result = schema.load({'username': 'testuser', 'role': role, 'password': 'Password123'})
            assert result['role'] == role

    def test_role_invalid_value(self, schema):
        """Invalid role should fail"""
        with pytest.raises(ValidationError) as exc:
            schema.load({'username': 'testuser', 'role': 'invalid', 'password': 'Password123'})
        assert 'role' in exc.value.messages

    def test_email_validation(self, schema):
        """Email must be valid format"""
        with pytest.raises(ValidationError) as exc:
            schema.load({'username': 'testuser', 'role': 'chemist', 'password': 'Password123', 'email': 'invalid'})
        assert 'email' in exc.value.messages

    def test_email_optional(self, schema):
        """Email is optional"""
        result = schema.load({'username': 'testuser', 'role': 'chemist', 'password': 'Password123'})
        assert 'email' not in result or result.get('email') is None

    def test_is_active_default_true(self, schema):
        """is_active should default to True"""
        result = schema.load({'username': 'testuser', 'role': 'chemist', 'password': 'Password123'})
        assert result.get('is_active', True) is True

    def test_id_dump_only(self, schema):
        """id should be dump only"""
        result = schema.load({'username': 'testuser', 'role': 'chemist', 'password': 'Password123', 'id': 999})
        assert 'id' not in result

    def test_password_not_in_dump(self, schema):
        """password should not be in dump output"""
        data = {'username': 'testuser', 'role': 'chemist', 'password': 'Password123'}
        loaded = schema.load(data)
        dumped = schema.dump(loaded)
        assert 'password' not in dumped


class TestUserListSchema:
    """UserListSchema тестүүд"""

    def test_user_list_schema(self):
        from app.schemas.user_schema import UserListSchema
        schema = UserListSchema()
        data = {
            'users': [{'username': 'user1', 'role': 'chemist'}],
            'total': 1,
            'page': 1,
            'per_page': 10
        }
        result = schema.dump(data)
        assert result['total'] == 1


class TestSampleSchema:
    """SampleSchema тестүүд"""

    @pytest.fixture
    def schema(self):
        from app.schemas.sample_schema import SampleSchema
        return SampleSchema()

    def test_valid_sample_data(self, schema):
        """Valid sample data should pass validation"""
        data = {
            'sample_code': 'SAMPLE-001',
            'client_name': 'Test Client',
            'sample_type': 'Coal',
            'received_date': datetime.now().isoformat()
        }
        result = schema.load(data)
        assert result['sample_code'] == 'SAMPLE-001'

    def test_sample_code_required(self, schema):
        """sample_code is required"""
        with pytest.raises(ValidationError) as exc:
            schema.load({'client_name': 'Test', 'sample_type': 'Coal', 'received_date': datetime.now().isoformat()})
        assert 'sample_code' in exc.value.messages

    def test_sample_code_sql_injection(self, schema):
        """sample_code should prevent SQL injection"""
        with pytest.raises(ValidationError):
            schema.load({
                'sample_code': 'test;--comment',
                'client_name': 'Test',
                'sample_type': 'Coal',
                'received_date': datetime.now().isoformat()
            })

    def test_weight_positive(self, schema):
        """weight must be positive"""
        with pytest.raises(ValidationError):
            schema.load({
                'sample_code': 'TEST-001',
                'client_name': 'Test',
                'sample_type': 'Coal',
                'received_date': datetime.now().isoformat(),
                'weight': -5.0
            })

    def test_weight_range(self, schema):
        """weight must be within range"""
        # Too small
        with pytest.raises(ValidationError):
            schema.load({
                'sample_code': 'TEST-001',
                'client_name': 'Test',
                'sample_type': 'Coal',
                'received_date': datetime.now().isoformat(),
                'weight': 0.0001
            })

    def test_sample_condition_valid_values(self, schema):
        """sample_condition must be valid"""
        valid_conditions = ['Хуурай', 'Чийгтэй', 'Шингэн']
        for condition in valid_conditions:
            result = schema.load({
                'sample_code': 'TEST-001',
                'client_name': 'Test',
                'sample_type': 'Coal',
                'received_date': datetime.now().isoformat(),
                'sample_condition': condition
            })
            assert result['sample_condition'] == condition

    def test_status_default_value(self, schema):
        """status should default to 'new'"""
        result = schema.load({
            'sample_code': 'TEST-001',
            'client_name': 'Test',
            'sample_type': 'Coal',
            'received_date': datetime.now().isoformat()
        })
        assert result.get('status', 'new') == 'new'

    def test_analyses_to_perform_list(self, schema):
        """analyses_to_perform should be a list"""
        result = schema.load({
            'sample_code': 'TEST-001',
            'client_name': 'Test',
            'sample_type': 'Coal',
            'received_date': datetime.now().isoformat(),
            'analyses_to_perform': ['Mad', 'Aad', 'Vad']
        })
        assert result['analyses_to_perform'] == ['Mad', 'Aad', 'Vad']


class TestSampleListSchema:
    """SampleListSchema тестүүд"""

    def test_sample_list_schema(self):
        from app.schemas.sample_schema import SampleListSchema
        schema = SampleListSchema()
        data = {
            'draw': 1,
            'recordsTotal': 100,
            'recordsFiltered': 50,
            'data': [{'id': 1, 'sample_code': 'S001'}]
        }
        result = schema.dump(data)
        assert result['recordsTotal'] == 100


class TestAnalysisResultSchema:
    """AnalysisResultSchema тестүүд"""

    @pytest.fixture
    def schema(self):
        from app.schemas.analysis_schema import AnalysisResultSchema
        return AnalysisResultSchema()

    def test_valid_analysis_data(self, schema):
        """Valid analysis data should pass validation"""
        data = {
            'sample_id': 1,
            'analysis_code': 'Mad',
            'final_result': 3.25,
            'raw_data': '{"p1": {"m1": 10}}'
        }
        result = schema.load(data)
        assert result['sample_id'] == 1
        assert result['analysis_code'] == 'Mad'

    def test_sample_id_required(self, schema):
        """sample_id is required"""
        with pytest.raises(ValidationError) as exc:
            schema.load({'analysis_code': 'Mad', 'final_result': 3.25})
        assert 'sample_id' in exc.value.messages

    def test_sample_id_positive(self, schema):
        """sample_id must be positive"""
        with pytest.raises(ValidationError):
            schema.load({'sample_id': 0, 'analysis_code': 'Mad', 'final_result': 3.25})

    def test_analysis_code_required(self, schema):
        """analysis_code is required"""
        with pytest.raises(ValidationError) as exc:
            schema.load({'sample_id': 1, 'final_result': 3.25})
        assert 'analysis_code' in exc.value.messages

    def test_analysis_code_sql_injection(self, schema):
        """analysis_code should prevent SQL injection"""
        with pytest.raises(ValidationError):
            schema.load({
                'sample_id': 1,
                'analysis_code': 'Mad;DROP',
                'final_result': 3.25
            })

    def test_final_result_nan(self, schema):
        """final_result cannot be NaN"""
        import math
        with pytest.raises(ValidationError):
            schema.load({
                'sample_id': 1,
                'analysis_code': 'Mad',
                'final_result': float('nan')
            })

    def test_final_result_infinity(self, schema):
        """final_result cannot be Infinity"""
        with pytest.raises(ValidationError):
            schema.load({
                'sample_id': 1,
                'analysis_code': 'Mad',
                'final_result': float('inf')
            })

    def test_status_valid_values(self, schema):
        """status must be valid"""
        valid_statuses = ['pending_review', 'approved', 'rejected', 'draft']
        for status in valid_statuses:
            result = schema.load({
                'sample_id': 1,
                'analysis_code': 'Mad',
                'final_result': 3.25,
                'status': status
            })
            assert result['status'] == status

    def test_status_default_value(self, schema):
        """status should default to pending_review"""
        result = schema.load({
            'sample_id': 1,
            'analysis_code': 'Mad',
            'final_result': 3.25
        })
        assert result.get('status', 'pending_review') == 'pending_review'

    def test_equipment_id_positive(self, schema):
        """equipment_id must be positive if provided"""
        with pytest.raises(ValidationError):
            schema.load({
                'sample_id': 1,
                'analysis_code': 'Mad',
                'final_result': 3.25,
                'equipment_id': 0
            })

    def test_schema_validation_requires_result_or_data(self, schema):
        """Either final_result or raw_data must be provided"""
        with pytest.raises(ValidationError) as exc:
            schema.load({
                'sample_id': 1,
                'analysis_code': 'Mad'
            })
        assert '_schema' in exc.value.messages

    def test_raw_data_alone_valid(self, schema):
        """raw_data alone should be valid"""
        result = schema.load({
            'sample_id': 1,
            'analysis_code': 'Mad',
            'raw_data': '{"p1": {"m1": 10}}'
        })
        assert result['raw_data'] == '{"p1": {"m1": 10}}'


class TestAnalysisResultListSchema:
    """AnalysisResultListSchema тестүүд"""

    def test_analysis_list_schema(self):
        from app.schemas.analysis_schema import AnalysisResultListSchema
        schema = AnalysisResultListSchema()
        data = {
            'results': [
                {'sample_id': 1, 'analysis_code': 'Mad', 'final_result': 3.25}
            ]
        }
        result = schema.dump(data)
        assert len(result['results']) == 1
