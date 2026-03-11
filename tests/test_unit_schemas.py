# tests/unit/test_schemas.py
# -*- coding: utf-8 -*-
"""
Marshmallow schema comprehensive tests
"""
import pytest
import math
from marshmallow import ValidationError
from datetime import datetime


class TestAnalysisResultSchema:
    """AnalysisResultSchema тестүүд"""

    def test_valid_data_loads(self, app):
        """Valid data should load successfully"""
        with app.app_context():
            from app.schemas.analysis_schema import AnalysisResultSchema
            schema = AnalysisResultSchema()
            data = {
                "sample_id": 1,
                "analysis_code": "MT",
                "final_result": 8.5,
                "status": "pending_review"
            }
            result = schema.load(data)
            assert result["sample_id"] == 1
            assert result["analysis_code"] == "MT"
            assert result["final_result"] == 8.5

    def test_missing_sample_id_fails(self, app):
        """Missing sample_id should fail validation"""
        with app.app_context():
            from app.schemas.analysis_schema import AnalysisResultSchema
            schema = AnalysisResultSchema()
            data = {
                "analysis_code": "MT",
                "final_result": 8.5
            }
            with pytest.raises(ValidationError) as exc:
                schema.load(data)
            assert "sample_id" in exc.value.messages

    def test_missing_analysis_code_fails(self, app):
        """Missing analysis_code should fail validation"""
        with app.app_context():
            from app.schemas.analysis_schema import AnalysisResultSchema
            schema = AnalysisResultSchema()
            data = {
                "sample_id": 1,
                "final_result": 8.5
            }
            with pytest.raises(ValidationError) as exc:
                schema.load(data)
            assert "analysis_code" in exc.value.messages

    def test_negative_sample_id_fails(self, app):
        """Negative sample_id should fail"""
        with app.app_context():
            from app.schemas.analysis_schema import AnalysisResultSchema
            schema = AnalysisResultSchema()
            data = {
                "sample_id": -1,
                "analysis_code": "MT",
                "final_result": 8.5
            }
            with pytest.raises(ValidationError) as exc:
                schema.load(data)
            assert "sample_id" in exc.value.messages

    def test_empty_analysis_code_fails(self, app):
        """Empty analysis_code should fail"""
        with app.app_context():
            from app.schemas.analysis_schema import AnalysisResultSchema
            schema = AnalysisResultSchema()
            data = {
                "sample_id": 1,
                "analysis_code": "",
                "final_result": 8.5
            }
            with pytest.raises(ValidationError) as exc:
                schema.load(data)
            assert "analysis_code" in exc.value.messages

    def test_sql_injection_in_analysis_code_fails(self, app):
        """SQL injection attempt should fail"""
        with app.app_context():
            from app.schemas.analysis_schema import AnalysisResultSchema
            schema = AnalysisResultSchema()
            data = {
                "sample_id": 1,
                "analysis_code": "MT; DROP TABLE",
                "final_result": 8.5
            }
            with pytest.raises(ValidationError) as exc:
                schema.load(data)
            assert "analysis_code" in exc.value.messages

    def test_nan_result_fails(self, app):
        """NaN final_result should fail"""
        with app.app_context():
            from app.schemas.analysis_schema import AnalysisResultSchema
            schema = AnalysisResultSchema()
            data = {
                "sample_id": 1,
                "analysis_code": "MT",
                "final_result": float('nan')
            }
            with pytest.raises(ValidationError) as exc:
                schema.load(data)
            assert "final_result" in exc.value.messages

    def test_infinity_result_fails(self, app):
        """Infinity final_result should fail"""
        with app.app_context():
            from app.schemas.analysis_schema import AnalysisResultSchema
            schema = AnalysisResultSchema()
            data = {
                "sample_id": 1,
                "analysis_code": "MT",
                "final_result": float('inf')
            }
            with pytest.raises(ValidationError) as exc:
                schema.load(data)
            assert "final_result" in exc.value.messages

    def test_missing_both_result_and_raw_data_fails(self, app):
        """Missing both final_result and raw_data should fail"""
        with app.app_context():
            from app.schemas.analysis_schema import AnalysisResultSchema
            schema = AnalysisResultSchema()
            data = {
                "sample_id": 1,
                "analysis_code": "MT"
            }
            with pytest.raises(ValidationError) as exc:
                schema.load(data)
            assert "_schema" in exc.value.messages

    def test_raw_data_only_is_valid(self, app):
        """Raw data without final_result should be valid"""
        with app.app_context():
            from app.schemas.analysis_schema import AnalysisResultSchema
            schema = AnalysisResultSchema()
            data = {
                "sample_id": 1,
                "analysis_code": "MT",
                "raw_data": '{"m1": 10.5, "m2": 15.3}'
            }
            result = schema.load(data)
            assert result["raw_data"] == '{"m1": 10.5, "m2": 15.3}'

    def test_valid_statuses(self, app):
        """All valid statuses should pass"""
        with app.app_context():
            from app.schemas.analysis_schema import AnalysisResultSchema
            schema = AnalysisResultSchema()
            for status in ['pending_review', 'approved', 'rejected', 'reanalysis']:
                data = {
                    "sample_id": 1,
                    "analysis_code": "MT",
                    "final_result": 8.5,
                    "status": status
                }
                result = schema.load(data)
                assert result["status"] == status

    def test_invalid_status_fails(self, app):
        """Invalid status should fail"""
        with app.app_context():
            from app.schemas.analysis_schema import AnalysisResultSchema
            schema = AnalysisResultSchema()
            data = {
                "sample_id": 1,
                "analysis_code": "MT",
                "final_result": 8.5,
                "status": "invalid_status"
            }
            with pytest.raises(ValidationError) as exc:
                schema.load(data)
            assert "status" in exc.value.messages


class TestSampleSchema:
    """SampleSchema тестүүд"""

    def test_valid_data_loads(self, app):
        """Valid data should load successfully"""
        with app.app_context():
            from app.schemas.sample_schema import SampleSchema
            schema = SampleSchema()
            data = {
                "sample_code": "SAMPLE-001",
                "client_name": "CHPP",
                "sample_type": "Coal",
                "received_date": "2025-01-15T10:00:00"
            }
            result = schema.load(data)
            assert result["sample_code"] == "SAMPLE-001"
            assert result["client_name"] == "CHPP"

    def test_missing_sample_code_fails(self, app):
        """Missing sample_code should fail"""
        with app.app_context():
            from app.schemas.sample_schema import SampleSchema
            schema = SampleSchema()
            data = {
                "client_name": "CHPP",
                "sample_type": "Coal",
                "received_date": "2025-01-15T10:00:00"
            }
            with pytest.raises(ValidationError) as exc:
                schema.load(data)
            assert "sample_code" in exc.value.messages

    def test_empty_sample_code_fails(self, app):
        """Empty sample_code should fail"""
        with app.app_context():
            from app.schemas.sample_schema import SampleSchema
            schema = SampleSchema()
            data = {
                "sample_code": "",
                "client_name": "CHPP",
                "sample_type": "Coal",
                "received_date": "2025-01-15T10:00:00"
            }
            with pytest.raises(ValidationError) as exc:
                schema.load(data)
            assert "sample_code" in exc.value.messages

    def test_negative_weight_fails(self, app):
        """Negative weight should fail"""
        with app.app_context():
            from app.schemas.sample_schema import SampleSchema
            schema = SampleSchema()
            data = {
                "sample_code": "SAMPLE-001",
                "client_name": "CHPP",
                "sample_type": "Coal",
                "received_date": "2025-01-15T10:00:00",
                "weight": -10
            }
            with pytest.raises(ValidationError) as exc:
                schema.load(data)
            assert "weight" in exc.value.messages

    def test_valid_sample_conditions(self, app):
        """Valid sample conditions should pass"""
        with app.app_context():
            from app.schemas.sample_schema import SampleSchema
            schema = SampleSchema()
            for condition in ['Хуурай', 'Чийгтэй', 'Шингэн']:
                data = {
                    "sample_code": "SAMPLE-001",
                    "client_name": "CHPP",
                    "sample_type": "Coal",
                    "received_date": "2025-01-15T10:00:00",
                    "sample_condition": condition
                }
                result = schema.load(data)
                assert result["sample_condition"] == condition


class TestUserSchema:
    """UserSchema тестүүд"""

    def test_valid_data_loads(self, app):
        """Valid data should load successfully"""
        with app.app_context():
            from app.schemas.user_schema import UserSchema
            schema = UserSchema()
            data = {
                "username": "test_user",
                "password": "TestPass123",
                "role": "chemist",
                "email": "test@example.com"
            }
            result = schema.load(data)
            assert result["username"] == "test_user"
            assert result["role"] == "chemist"

    def test_missing_username_fails(self, app):
        """Missing username should fail"""
        with app.app_context():
            from app.schemas.user_schema import UserSchema
            schema = UserSchema()
            data = {
                "password": "TestPass123",
                "role": "chemist"
            }
            with pytest.raises(ValidationError) as exc:
                schema.load(data)
            assert "username" in exc.value.messages

    def test_short_username_fails(self, app):
        """Username shorter than 3 chars should fail"""
        with app.app_context():
            from app.schemas.user_schema import UserSchema
            schema = UserSchema()
            data = {
                "username": "ab",
                "password": "TestPass123",
                "role": "chemist"
            }
            with pytest.raises(ValidationError) as exc:
                schema.load(data)
            assert "username" in exc.value.messages

    def test_invalid_username_characters_fails(self, app):
        """Username with invalid characters should fail"""
        with app.app_context():
            from app.schemas.user_schema import UserSchema
            schema = UserSchema()
            data = {
                "username": "test@user!",
                "password": "TestPass123",
                "role": "chemist"
            }
            with pytest.raises(ValidationError) as exc:
                schema.load(data)
            assert "username" in exc.value.messages

    def test_password_without_uppercase_fails(self, app):
        """Password without uppercase should fail"""
        with app.app_context():
            from app.schemas.user_schema import UserSchema
            schema = UserSchema()
            data = {
                "username": "test_user",
                "password": "testpass123",
                "role": "chemist"
            }
            with pytest.raises(ValidationError) as exc:
                schema.load(data)
            assert "password" in exc.value.messages

    def test_valid_roles(self, app):
        """All valid roles should pass"""
        with app.app_context():
            from app.schemas.user_schema import UserSchema
            schema = UserSchema()
            for role in ['prep', 'chemist', 'senior', 'manager', 'admin']:
                data = {
                    "username": "test_user",
                    "password": "TestPass123",
                    "role": role
                }
                result = schema.load(data)
                assert result["role"] == role

    def test_invalid_role_fails(self, app):
        """Invalid role should fail"""
        with app.app_context():
            from app.schemas.user_schema import UserSchema
            schema = UserSchema()
            data = {
                "username": "test_user",
                "password": "TestPass123",
                "role": "invalid_role"
            }
            with pytest.raises(ValidationError) as exc:
                schema.load(data)
            assert "role" in exc.value.messages

    def test_invalid_email_fails(self, app):
        """Invalid email should fail"""
        with app.app_context():
            from app.schemas.user_schema import UserSchema
            schema = UserSchema()
            data = {
                "username": "test_user",
                "password": "TestPass123",
                "role": "chemist",
                "email": "not-an-email"
            }
            with pytest.raises(ValidationError) as exc:
                schema.load(data)
            assert "email" in exc.value.messages
