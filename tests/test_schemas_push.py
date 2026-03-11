# -*- coding: utf-8 -*-
"""
Schemas модулийн coverage тестүүд
"""
import pytest
from marshmallow import ValidationError
import math


# ============================================================
# SampleSchema Tests
# ============================================================

class TestSampleSchemaImport:
    """SampleSchema импорт тест"""

    def test_import_from_init(self):
        from app.schemas import SampleSchema
        assert SampleSchema is not None

    def test_import_direct(self):
        from app.schemas.sample_schema import SampleSchema
        assert SampleSchema is not None

    def test_import_list_schema(self):
        from app.schemas.sample_schema import SampleListSchema
        assert SampleListSchema is not None


class TestSampleSchemaFields:
    """SampleSchema талбарын тест"""

    def test_schema_fields_exist(self):
        from app.schemas.sample_schema import SampleSchema
        schema = SampleSchema()
        fields = schema.fields
        assert 'id' in fields
        assert 'sample_code' in fields
        assert 'client_name' in fields
        assert 'sample_type' in fields
        assert 'weight' in fields
        assert 'received_date' in fields
        assert 'status' in fields

    def test_dump_only_fields(self):
        from app.schemas.sample_schema import SampleSchema
        schema = SampleSchema()
        assert schema.fields['id'].dump_only is True
        assert schema.fields['created_at'].dump_only is True
        assert schema.fields['updated_at'].dump_only is True


class TestSampleSchemaValidation:
    """SampleSchema validation тест"""

    def test_valid_sample(self):
        from app.schemas.sample_schema import SampleSchema
        from datetime import datetime
        schema = SampleSchema()
        data = {
            'sample_code': 'TEST-001',
            'client_name': 'CHPP',
            'sample_type': 'Coal',
            'received_date': datetime.now()
        }
        result = schema.load(data)
        assert result['sample_code'] == 'TEST-001'

    def test_missing_sample_code(self):
        from app.schemas.sample_schema import SampleSchema
        from datetime import datetime
        schema = SampleSchema()
        data = {
            'client_name': 'CHPP',
            'sample_type': 'Coal',
            'received_date': datetime.now()
        }
        with pytest.raises(ValidationError) as exc:
            schema.load(data)
        assert 'sample_code' in exc.value.messages

    def test_empty_sample_code(self):
        from app.schemas.sample_schema import SampleSchema
        from datetime import datetime
        schema = SampleSchema()
        data = {
            'sample_code': '   ',
            'client_name': 'CHPP',
            'sample_type': 'Coal',
            'received_date': datetime.now()
        }
        with pytest.raises(ValidationError):
            schema.load(data)

    def test_empty_sample_code_fails(self):
        from app.schemas.sample_schema import SampleSchema
        from datetime import datetime
        schema = SampleSchema()
        data = {
            'sample_code': '',
            'client_name': 'CHPP',
            'sample_type': 'Coal',
            'received_date': datetime.now()
        }
        with pytest.raises(ValidationError):
            schema.load(data)

    def test_negative_weight(self):
        from app.schemas.sample_schema import SampleSchema
        from datetime import datetime
        schema = SampleSchema()
        data = {
            'sample_code': 'TEST-001',
            'client_name': 'CHPP',
            'sample_type': 'Coal',
            'received_date': datetime.now(),
            'weight': -10.5
        }
        with pytest.raises(ValidationError):
            schema.load(data)

    def test_valid_weight(self):
        from app.schemas.sample_schema import SampleSchema
        from datetime import datetime
        schema = SampleSchema()
        data = {
            'sample_code': 'TEST-001',
            'client_name': 'CHPP',
            'sample_type': 'Coal',
            'received_date': datetime.now(),
            'weight': 100.5
        }
        result = schema.load(data)
        assert result['weight'] == 100.5

    def test_sample_condition_valid(self):
        from app.schemas.sample_schema import SampleSchema
        from datetime import datetime
        schema = SampleSchema()
        for condition in ["Хуурай", "Чийгтэй", "Шингэн"]:
            data = {
                'sample_code': 'TEST-001',
                'client_name': 'CHPP',
                'sample_type': 'Coal',
                'received_date': datetime.now(),
                'sample_condition': condition
            }
            result = schema.load(data)
            assert result['sample_condition'] == condition

    def test_sample_condition_too_long(self):
        from app.schemas.sample_schema import SampleSchema
        from datetime import datetime
        schema = SampleSchema()
        data = {
            'sample_code': 'TEST-001',
            'client_name': 'CHPP',
            'sample_type': 'Coal',
            'received_date': datetime.now(),
            'sample_condition': 'X' * 101  # Over 100 char limit
        }
        with pytest.raises(ValidationError):
            schema.load(data)

    def test_status_default(self):
        from app.schemas.sample_schema import SampleSchema
        from datetime import datetime
        schema = SampleSchema()
        data = {
            'sample_code': 'TEST-001',
            'client_name': 'CHPP',
            'sample_type': 'Coal',
            'received_date': datetime.now()
        }
        result = schema.load(data)
        assert result.get('status', 'new') == 'new'

    def test_analyses_to_perform_string(self):
        from app.schemas.sample_schema import SampleSchema
        from datetime import datetime
        schema = SampleSchema()
        data = {
            'sample_code': 'TEST-001',
            'client_name': 'CHPP',
            'sample_type': 'Coal',
            'received_date': datetime.now(),
            'analyses_to_perform': 'CV,TS,Mad'
        }
        result = schema.load(data)
        assert result['analyses_to_perform'] == 'CV,TS,Mad'


class TestSampleListSchema:
    """SampleListSchema тест"""

    def test_schema_fields(self):
        from app.schemas.sample_schema import SampleListSchema
        schema = SampleListSchema()
        assert 'draw' in schema.fields
        assert 'recordsTotal' in schema.fields
        assert 'recordsFiltered' in schema.fields
        assert 'data' in schema.fields


# ============================================================
# UserSchema Tests
# ============================================================

class TestUserSchemaImport:
    """UserSchema импорт тест"""

    def test_import_from_init(self):
        from app.schemas import UserSchema
        assert UserSchema is not None

    def test_import_direct(self):
        from app.schemas.user_schema import UserSchema
        assert UserSchema is not None

    def test_import_list_schema(self):
        from app.schemas.user_schema import UserListSchema
        assert UserListSchema is not None


class TestUserSchemaFields:
    """UserSchema талбарын тест"""

    def test_schema_fields_exist(self):
        from app.schemas.user_schema import UserSchema
        schema = UserSchema()
        fields = schema.fields
        assert 'id' in fields
        assert 'username' in fields
        assert 'password' in fields
        assert 'role' in fields
        assert 'email' in fields

    def test_password_load_only(self):
        from app.schemas.user_schema import UserSchema
        schema = UserSchema()
        assert schema.fields['password'].load_only is True


class TestUserSchemaValidation:
    """UserSchema validation тест"""

    def test_valid_user(self):
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

    def test_username_too_short(self):
        from app.schemas.user_schema import UserSchema
        schema = UserSchema()
        data = {
            'username': 'ab',
            'role': 'chemist'
        }
        with pytest.raises(ValidationError):
            schema.load(data)

    def test_username_empty(self):
        from app.schemas.user_schema import UserSchema
        schema = UserSchema()
        data = {
            'username': '  ',
            'role': 'chemist'
        }
        with pytest.raises(ValidationError):
            schema.load(data)

    def test_username_special_chars(self):
        from app.schemas.user_schema import UserSchema
        schema = UserSchema()
        data = {
            'username': 'test@user!',
            'role': 'chemist'
        }
        with pytest.raises(ValidationError):
            schema.load(data)

    def test_username_sql_injection(self):
        from app.schemas.user_schema import UserSchema
        schema = UserSchema()
        # Only usernames with special chars fail (regex: ^[a-zA-Z0-9_]+$)
        data = {
            'username': "admin';DROP TABLE--",
            'role': 'chemist'
        }
        with pytest.raises(ValidationError):
            schema.load(data)

    def test_password_too_short(self):
        from app.schemas.user_schema import UserSchema
        schema = UserSchema()
        data = {
            'username': 'testuser',
            'password': 'short',
            'role': 'chemist'
        }
        with pytest.raises(ValidationError):
            schema.load(data)

    def test_password_no_uppercase(self):
        from app.schemas.user_schema import UserSchema
        schema = UserSchema()
        data = {
            'username': 'testuser',
            'password': 'testpass1',
            'role': 'chemist'
        }
        with pytest.raises(ValidationError):
            schema.load(data)

    def test_password_no_lowercase(self):
        from app.schemas.user_schema import UserSchema
        schema = UserSchema()
        data = {
            'username': 'testuser',
            'password': 'TESTPASS1',
            'role': 'chemist'
        }
        with pytest.raises(ValidationError):
            schema.load(data)

    def test_password_no_digit(self):
        from app.schemas.user_schema import UserSchema
        schema = UserSchema()
        data = {
            'username': 'testuser',
            'password': 'TestPass',
            'role': 'chemist'
        }
        with pytest.raises(ValidationError):
            schema.load(data)

    def test_valid_roles(self):
        from app.schemas.user_schema import UserSchema
        schema = UserSchema()
        for role in ['prep', 'chemist', 'senior', 'manager', 'admin']:
            data = {
                'username': 'testuser',
                'role': role
            }
            result = schema.load(data)
            assert result['role'] == role

    def test_invalid_role(self):
        from app.schemas.user_schema import UserSchema
        schema = UserSchema()
        data = {
            'username': 'testuser',
            'role': 'superadmin'
        }
        with pytest.raises(ValidationError):
            schema.load(data)

    def test_valid_email(self):
        from app.schemas.user_schema import UserSchema
        schema = UserSchema()
        data = {
            'username': 'testuser',
            'role': 'chemist',
            'email': 'test@example.com'
        }
        result = schema.load(data)
        assert result['email'] == 'test@example.com'

    def test_invalid_email(self):
        from app.schemas.user_schema import UserSchema
        schema = UserSchema()
        data = {
            'username': 'testuser',
            'role': 'chemist',
            'email': 'not-an-email'
        }
        with pytest.raises(ValidationError):
            schema.load(data)


class TestUserListSchema:
    """UserListSchema тест"""

    def test_schema_fields(self):
        from app.schemas.user_schema import UserListSchema
        schema = UserListSchema()
        assert 'users' in schema.fields
        assert 'total' in schema.fields
        assert 'page' in schema.fields


# ============================================================
# AnalysisResultSchema Tests
# ============================================================

class TestAnalysisResultSchemaImport:
    """AnalysisResultSchema импорт тест"""

    def test_import_from_init(self):
        from app.schemas import AnalysisResultSchema
        assert AnalysisResultSchema is not None

    def test_import_direct(self):
        from app.schemas.analysis_schema import AnalysisResultSchema
        assert AnalysisResultSchema is not None

    def test_import_list_schema(self):
        from app.schemas.analysis_schema import AnalysisResultListSchema
        assert AnalysisResultListSchema is not None


class TestAnalysisResultSchemaFields:
    """AnalysisResultSchema талбарын тест"""

    def test_schema_fields_exist(self):
        from app.schemas.analysis_schema import AnalysisResultSchema
        schema = AnalysisResultSchema()
        fields = schema.fields
        assert 'id' in fields
        assert 'sample_id' in fields
        assert 'analysis_code' in fields
        assert 'final_result' in fields
        assert 'status' in fields

    def test_dump_only_fields(self):
        from app.schemas.analysis_schema import AnalysisResultSchema
        schema = AnalysisResultSchema()
        assert schema.fields['id'].dump_only is True
        assert schema.fields['created_at'].dump_only is True


class TestAnalysisResultSchemaValidation:
    """AnalysisResultSchema validation тест"""

    def test_valid_analysis(self):
        from app.schemas.analysis_schema import AnalysisResultSchema
        schema = AnalysisResultSchema()
        data = {
            'sample_id': 1,
            'analysis_code': 'CV',
            'final_result': 25.5
        }
        result = schema.load(data)
        assert result['analysis_code'] == 'CV'
        assert result['final_result'] == 25.5

    def test_missing_sample_id(self):
        from app.schemas.analysis_schema import AnalysisResultSchema
        schema = AnalysisResultSchema()
        data = {
            'analysis_code': 'CV',
            'final_result': 25.5
        }
        with pytest.raises(ValidationError) as exc:
            schema.load(data)
        assert 'sample_id' in exc.value.messages

    def test_invalid_sample_id(self):
        from app.schemas.analysis_schema import AnalysisResultSchema
        schema = AnalysisResultSchema()
        data = {
            'sample_id': 0,
            'analysis_code': 'CV',
            'final_result': 25.5
        }
        with pytest.raises(ValidationError):
            schema.load(data)

    def test_negative_sample_id(self):
        from app.schemas.analysis_schema import AnalysisResultSchema
        schema = AnalysisResultSchema()
        data = {
            'sample_id': -1,
            'analysis_code': 'CV',
            'final_result': 25.5
        }
        with pytest.raises(ValidationError):
            schema.load(data)

    def test_empty_analysis_code(self):
        from app.schemas.analysis_schema import AnalysisResultSchema
        schema = AnalysisResultSchema()
        data = {
            'sample_id': 1,
            'analysis_code': '   ',
            'final_result': 25.5
        }
        with pytest.raises(ValidationError):
            schema.load(data)

    def test_sql_injection_in_analysis_code(self):
        from app.schemas.analysis_schema import AnalysisResultSchema
        schema = AnalysisResultSchema()
        data = {
            'sample_id': 1,
            'analysis_code': 'CV; DELETE FROM results--',
            'final_result': 25.5
        }
        with pytest.raises(ValidationError):
            schema.load(data)

    def test_nan_final_result(self):
        from app.schemas.analysis_schema import AnalysisResultSchema
        schema = AnalysisResultSchema()
        data = {
            'sample_id': 1,
            'analysis_code': 'CV',
            'final_result': float('nan')
        }
        with pytest.raises(ValidationError):
            schema.load(data)

    def test_infinity_final_result(self):
        from app.schemas.analysis_schema import AnalysisResultSchema
        schema = AnalysisResultSchema()
        data = {
            'sample_id': 1,
            'analysis_code': 'CV',
            'final_result': float('inf')
        }
        with pytest.raises(ValidationError):
            schema.load(data)

    def test_negative_infinity_final_result(self):
        from app.schemas.analysis_schema import AnalysisResultSchema
        schema = AnalysisResultSchema()
        data = {
            'sample_id': 1,
            'analysis_code': 'CV',
            'final_result': float('-inf')
        }
        with pytest.raises(ValidationError):
            schema.load(data)

    def test_valid_status_values(self):
        from app.schemas.analysis_schema import AnalysisResultSchema
        schema = AnalysisResultSchema()
        for status in ['pending_review', 'approved', 'rejected', 'reanalysis']:
            data = {
                'sample_id': 1,
                'analysis_code': 'CV',
                'final_result': 25.5,
                'status': status
            }
            result = schema.load(data)
            assert result['status'] == status

    def test_invalid_status(self):
        from app.schemas.analysis_schema import AnalysisResultSchema
        schema = AnalysisResultSchema()
        data = {
            'sample_id': 1,
            'analysis_code': 'CV',
            'final_result': 25.5,
            'status': 'invalid_status'
        }
        with pytest.raises(ValidationError):
            schema.load(data)

    def test_schema_validation_no_result_or_raw(self):
        from app.schemas.analysis_schema import AnalysisResultSchema
        schema = AnalysisResultSchema()
        data = {
            'sample_id': 1,
            'analysis_code': 'CV'
        }
        with pytest.raises(ValidationError) as exc:
            schema.load(data)
        assert '_schema' in exc.value.messages

    def test_schema_validation_with_raw_data(self):
        from app.schemas.analysis_schema import AnalysisResultSchema
        schema = AnalysisResultSchema()
        data = {
            'sample_id': 1,
            'analysis_code': 'CV',
            'raw_data': '{"p1": {"m1": 10.0}}'
        }
        result = schema.load(data)
        assert result['raw_data'] == '{"p1": {"m1": 10.0}}'


class TestAnalysisResultListSchema:
    """AnalysisResultListSchema тест"""

    def test_schema_fields(self):
        from app.schemas.analysis_schema import AnalysisResultListSchema
        schema = AnalysisResultListSchema()
        assert 'results' in schema.fields


# ============================================================
# __init__.py Tests
# ============================================================

class TestSchemasInit:
    """schemas __init__.py тест"""

    def test_all_exports(self):
        from app.schemas import __all__
        assert 'SampleSchema' in __all__
        assert 'AnalysisResultSchema' in __all__
        assert 'UserSchema' in __all__

    def test_direct_imports(self):
        from app.schemas import SampleSchema, AnalysisResultSchema, UserSchema
        assert SampleSchema is not None
        assert AnalysisResultSchema is not None
        assert UserSchema is not None
