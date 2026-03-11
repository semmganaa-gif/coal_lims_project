# -*- coding: utf-8 -*-
"""
Tests for app/schemas/*.py
Marshmallow schema validation tests
"""
import pytest
import math
from marshmallow import ValidationError


# ============================================================================
# SampleSchema Tests
# ============================================================================
class TestSampleSchema:
    """SampleSchema tests"""

    def test_import_sample_schema(self):
        """Import SampleSchema"""
        from app.schemas.sample_schema import SampleSchema
        assert SampleSchema is not None

    def test_sample_schema_valid_data(self):
        """Valid data load"""
        from app.schemas.sample_schema import SampleSchema
        from datetime import datetime

        schema = SampleSchema()
        data = {
            'sample_code': 'TEST-001',
            'client_name': 'CHPP',
            'sample_type': 'Coal',
            'received_date': datetime.now().isoformat()
        }
        result = schema.load(data)

        assert result['sample_code'] == 'TEST-001'
        assert result['client_name'] == 'CHPP'

    def test_sample_schema_missing_required(self):
        """Missing required fields"""
        from app.schemas.sample_schema import SampleSchema

        schema = SampleSchema()
        with pytest.raises(ValidationError) as exc:
            schema.load({})

        assert 'sample_code' in exc.value.messages
        assert 'client_name' in exc.value.messages

    def test_sample_schema_empty_sample_code(self):
        """Empty sample_code"""
        from app.schemas.sample_schema import SampleSchema
        from datetime import datetime

        schema = SampleSchema()
        data = {
            'sample_code': '   ',
            'client_name': 'CHPP',
            'sample_type': 'Coal',
            'received_date': datetime.now().isoformat()
        }

        with pytest.raises(ValidationError):
            schema.load(data)

    def test_sample_schema_empty_code_rejected(self):
        """Empty sample_code rejected"""
        from app.schemas.sample_schema import SampleSchema
        from datetime import datetime

        schema = SampleSchema()
        data = {
            'sample_code': '',
            'client_name': 'CHPP',
            'sample_type': 'Coal',
            'received_date': datetime.now().isoformat()
        }

        with pytest.raises(ValidationError):
            schema.load(data)

    def test_sample_schema_weight_validation(self):
        """Weight validation"""
        from app.schemas.sample_schema import SampleSchema
        from datetime import datetime

        schema = SampleSchema()

        # Negative weight
        data = {
            'sample_code': 'TEST-001',
            'client_name': 'CHPP',
            'sample_type': 'Coal',
            'received_date': datetime.now().isoformat(),
            'weight': -5.0
        }

        with pytest.raises(ValidationError):
            schema.load(data)

    def test_sample_schema_valid_weight(self):
        """Valid weight"""
        from app.schemas.sample_schema import SampleSchema
        from datetime import datetime

        schema = SampleSchema()
        data = {
            'sample_code': 'TEST-001',
            'client_name': 'CHPP',
            'sample_type': 'Coal',
            'received_date': datetime.now().isoformat(),
            'weight': 100.5
        }

        result = schema.load(data)
        assert result['weight'] == 100.5

    def test_sample_schema_sample_condition(self):
        """Sample condition validation"""
        from app.schemas.sample_schema import SampleSchema
        from datetime import datetime

        schema = SampleSchema()

        # Valid condition
        data = {
            'sample_code': 'TEST-001',
            'client_name': 'CHPP',
            'sample_type': 'Coal',
            'received_date': datetime.now().isoformat(),
            'sample_condition': 'Хуурай'
        }
        result = schema.load(data)
        assert result['sample_condition'] == 'Хуурай'

    def test_sample_schema_condition_max_length(self):
        """Sample condition max length validation"""
        from app.schemas.sample_schema import SampleSchema
        from datetime import datetime

        schema = SampleSchema()
        data = {
            'sample_code': 'TEST-001',
            'client_name': 'CHPP',
            'sample_type': 'Coal',
            'received_date': datetime.now().isoformat(),
            'sample_condition': 'X' * 101  # Over 100 char limit
        }

        with pytest.raises(ValidationError):
            schema.load(data)

    def test_sample_schema_dump(self):
        """Schema dump"""
        from app.schemas.sample_schema import SampleSchema

        schema = SampleSchema()
        data = {
            'sample_code': 'TEST-001',
            'client_name': 'CHPP',
            'sample_type': 'Coal',
            'status': 'new'
        }

        result = schema.dump(data)
        assert 'sample_code' in result

    def test_sample_schema_unknown_fields_excluded(self):
        """Unknown fields excluded"""
        from app.schemas.sample_schema import SampleSchema
        from datetime import datetime

        schema = SampleSchema()
        data = {
            'sample_code': 'TEST-001',
            'client_name': 'CHPP',
            'sample_type': 'Coal',
            'received_date': datetime.now().isoformat(),
            'unknown_field': 'value'
        }

        result = schema.load(data)
        assert 'unknown_field' not in result


class TestSampleListSchema:
    """SampleListSchema tests"""

    def test_import_sample_list_schema(self):
        """Import SampleListSchema"""
        from app.schemas.sample_schema import SampleListSchema
        assert SampleListSchema is not None

    def test_sample_list_schema_valid(self):
        """Valid list schema"""
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


# ============================================================================
# AnalysisResultSchema Tests
# ============================================================================
class TestAnalysisResultSchema:
    """AnalysisResultSchema tests"""

    def test_import_analysis_schema(self):
        """Import AnalysisResultSchema"""
        from app.schemas.analysis_schema import AnalysisResultSchema
        assert AnalysisResultSchema is not None

    def test_analysis_schema_valid_data(self):
        """Valid data"""
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

    def test_analysis_schema_missing_sample_id(self):
        """Missing sample_id"""
        from app.schemas.analysis_schema import AnalysisResultSchema

        schema = AnalysisResultSchema()
        data = {
            'analysis_code': 'Mad',
            'final_result': 8.5
        }

        with pytest.raises(ValidationError) as exc:
            schema.load(data)
        assert 'sample_id' in exc.value.messages

    def test_analysis_schema_invalid_sample_id(self):
        """Invalid sample_id (negative)"""
        from app.schemas.analysis_schema import AnalysisResultSchema

        schema = AnalysisResultSchema()
        data = {
            'sample_id': -1,
            'analysis_code': 'Mad',
            'final_result': 8.5
        }

        with pytest.raises(ValidationError):
            schema.load(data)

    def test_analysis_schema_empty_code(self):
        """Empty analysis_code"""
        from app.schemas.analysis_schema import AnalysisResultSchema

        schema = AnalysisResultSchema()
        data = {
            'sample_id': 1,
            'analysis_code': '   ',
            'final_result': 8.5
        }

        with pytest.raises(ValidationError):
            schema.load(data)

    def test_analysis_schema_sql_injection_code(self):
        """SQL injection in analysis_code"""
        from app.schemas.analysis_schema import AnalysisResultSchema

        schema = AnalysisResultSchema()
        data = {
            'sample_id': 1,
            'analysis_code': 'Mad; DROP TABLE--',
            'final_result': 8.5
        }

        with pytest.raises(ValidationError):
            schema.load(data)

    def test_analysis_schema_nan_result(self):
        """NaN final_result"""
        from app.schemas.analysis_schema import AnalysisResultSchema

        schema = AnalysisResultSchema()
        data = {
            'sample_id': 1,
            'analysis_code': 'Mad',
            'final_result': float('nan')
        }

        with pytest.raises(ValidationError):
            schema.load(data)

    def test_analysis_schema_inf_result(self):
        """Infinity final_result"""
        from app.schemas.analysis_schema import AnalysisResultSchema

        schema = AnalysisResultSchema()
        data = {
            'sample_id': 1,
            'analysis_code': 'Mad',
            'final_result': float('inf')
        }

        with pytest.raises(ValidationError):
            schema.load(data)

    def test_analysis_schema_valid_status(self):
        """Valid status values"""
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

    def test_analysis_schema_invalid_status(self):
        """Invalid status"""
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

    def test_analysis_schema_default_status(self):
        """Default status"""
        from app.schemas.analysis_schema import AnalysisResultSchema

        schema = AnalysisResultSchema()
        data = {
            'sample_id': 1,
            'analysis_code': 'Mad',
            'final_result': 8.5
        }

        result = schema.load(data)
        assert result['status'] == 'pending_review'

    def test_analysis_schema_requires_result_or_raw(self):
        """Requires final_result or raw_data"""
        from app.schemas.analysis_schema import AnalysisResultSchema

        schema = AnalysisResultSchema()
        data = {
            'sample_id': 1,
            'analysis_code': 'Mad'
        }

        with pytest.raises(ValidationError) as exc:
            schema.load(data)
        assert '_schema' in exc.value.messages

    def test_analysis_schema_with_raw_data(self):
        """With raw_data only"""
        from app.schemas.analysis_schema import AnalysisResultSchema

        schema = AnalysisResultSchema()
        data = {
            'sample_id': 1,
            'analysis_code': 'Mad',
            'raw_data': '{"m1": 10.2, "m2": 10.3}'
        }

        result = schema.load(data)
        assert result['raw_data'] == '{"m1": 10.2, "m2": 10.3}'


class TestAnalysisResultListSchema:
    """AnalysisResultListSchema tests"""

    def test_import_list_schema(self):
        """Import AnalysisResultListSchema"""
        from app.schemas.analysis_schema import AnalysisResultListSchema
        assert AnalysisResultListSchema is not None


# ============================================================================
# UserSchema Tests
# ============================================================================
class TestUserSchema:
    """UserSchema tests"""

    def test_import_user_schema(self):
        """Import UserSchema"""
        from app.schemas.user_schema import UserSchema
        assert UserSchema is not None

    def test_user_schema_valid_data(self):
        """Valid user data"""
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

    def test_user_schema_missing_username(self):
        """Missing username"""
        from app.schemas.user_schema import UserSchema

        schema = UserSchema()
        data = {
            'password': 'TestPass123',
            'role': 'chemist'
        }

        with pytest.raises(ValidationError) as exc:
            schema.load(data)
        assert 'username' in exc.value.messages

    def test_user_schema_short_username(self):
        """Username too short"""
        from app.schemas.user_schema import UserSchema

        schema = UserSchema()
        data = {
            'username': 'ab',
            'password': 'TestPass123',
            'role': 'chemist'
        }

        with pytest.raises(ValidationError):
            schema.load(data)

    def test_user_schema_empty_username(self):
        """Empty username"""
        from app.schemas.user_schema import UserSchema

        schema = UserSchema()
        data = {
            'username': '   ',
            'password': 'TestPass123',
            'role': 'chemist'
        }

        with pytest.raises(ValidationError):
            schema.load(data)

    def test_user_schema_invalid_username_chars(self):
        """Invalid characters in username"""
        from app.schemas.user_schema import UserSchema

        schema = UserSchema()
        data = {
            'username': 'test@user!',
            'password': 'TestPass123',
            'role': 'chemist'
        }

        with pytest.raises(ValidationError):
            schema.load(data)

    def test_user_schema_sql_injection_username(self):
        """SQL injection in username"""
        from app.schemas.user_schema import UserSchema

        schema = UserSchema()
        data = {
            'username': 'admin; DROP TABLE--',
            'password': 'TestPass123',
            'role': 'chemist'
        }

        with pytest.raises(ValidationError):
            schema.load(data)

    def test_user_schema_valid_roles(self):
        """Valid role values"""
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

    def test_user_schema_invalid_role(self):
        """Invalid role"""
        from app.schemas.user_schema import UserSchema

        schema = UserSchema()
        data = {
            'username': 'testuser',
            'password': 'TestPass123',
            'role': 'superadmin'
        }

        with pytest.raises(ValidationError):
            schema.load(data)

    def test_user_schema_password_too_short(self):
        """Password too short"""
        from app.schemas.user_schema import UserSchema

        schema = UserSchema()
        data = {
            'username': 'testuser',
            'password': 'Test1',
            'role': 'chemist'
        }

        with pytest.raises(ValidationError):
            schema.load(data)

    def test_user_schema_password_no_uppercase(self):
        """Password without uppercase"""
        from app.schemas.user_schema import UserSchema

        schema = UserSchema()
        data = {
            'username': 'testuser',
            'password': 'testpass123',
            'role': 'chemist'
        }

        with pytest.raises(ValidationError):
            schema.load(data)

    def test_user_schema_password_no_lowercase(self):
        """Password without lowercase"""
        from app.schemas.user_schema import UserSchema

        schema = UserSchema()
        data = {
            'username': 'testuser',
            'password': 'TESTPASS123',
            'role': 'chemist'
        }

        with pytest.raises(ValidationError):
            schema.load(data)

    def test_user_schema_password_no_number(self):
        """Password without number"""
        from app.schemas.user_schema import UserSchema

        schema = UserSchema()
        data = {
            'username': 'testuser',
            'password': 'TestPassword',
            'role': 'chemist'
        }

        with pytest.raises(ValidationError):
            schema.load(data)

    def test_user_schema_password_load_only(self):
        """Password is load_only"""
        from app.schemas.user_schema import UserSchema

        schema = UserSchema()
        data = {
            'username': 'testuser',
            'password': 'TestPass123',
            'role': 'chemist'
        }

        loaded = schema.load(data)
        dumped = schema.dump(loaded)

        # Password should not be in dump output
        assert 'password' not in dumped

    def test_user_schema_valid_email(self):
        """Valid email"""
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

    def test_user_schema_invalid_email(self):
        """Invalid email"""
        from app.schemas.user_schema import UserSchema

        schema = UserSchema()
        data = {
            'username': 'testuser',
            'password': 'TestPass123',
            'role': 'chemist',
            'email': 'not-an-email'
        }

        with pytest.raises(ValidationError):
            schema.load(data)

    def test_user_schema_is_active_default(self):
        """is_active default value"""
        from app.schemas.user_schema import UserSchema

        schema = UserSchema()
        data = {
            'username': 'testuser',
            'password': 'TestPass123',
            'role': 'chemist'
        }

        result = schema.load(data)
        assert result['is_active'] == True


class TestUserListSchema:
    """UserListSchema tests"""

    def test_import_user_list_schema(self):
        """Import UserListSchema"""
        from app.schemas.user_schema import UserListSchema
        assert UserListSchema is not None


# ============================================================================
# Schemas __init__ Tests
# ============================================================================
class TestSchemasInit:
    """Schemas __init__.py tests"""

    def test_import_from_init(self):
        """Import from schemas package"""
        from app.schemas import SampleSchema, AnalysisResultSchema, UserSchema

        assert SampleSchema is not None
        assert AnalysisResultSchema is not None
        assert UserSchema is not None

    def test_all_exports(self):
        """Check __all__ exports"""
        from app import schemas

        assert 'SampleSchema' in schemas.__all__
        assert 'AnalysisResultSchema' in schemas.__all__
        assert 'UserSchema' in schemas.__all__
