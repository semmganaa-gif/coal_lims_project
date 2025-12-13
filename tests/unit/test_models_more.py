# tests/unit/test_models_more.py
# -*- coding: utf-8 -*-
"""
Model additional tests - coverage нэмэгдүүлэх
"""

import pytest
from datetime import datetime, date, timedelta
from app import db
from app.models import (
    User, Sample, AnalysisResult, AnalysisResultLog,
    ControlStandard, Equipment,
    SystemSetting, CorrectiveAction
)


class TestUserModel:
    """User model тестүүд"""

    def test_user_creation(self, app):
        """User үүсгэх"""
        with app.app_context():
            user = User(username='model_test_user', role='chemist')
            user.set_password('TestPass123')
            assert user.username == 'model_test_user'
            assert user.role == 'chemist'
            assert user.check_password('TestPass123')

    def test_user_password_check(self, app):
        """Password check"""
        with app.app_context():
            user = User(username='pwd_test', role='chemist')
            user.set_password('MySecretPass123')
            assert user.check_password('MySecretPass123') is True
            assert user.check_password('WrongPassword') is False

    def test_user_roles(self, app):
        """User roles"""
        with app.app_context():
            for role in ['prep', 'chemist', 'senior', 'manager', 'admin']:
                user = User(username=f'role_{role}', role=role)
                user.set_password('TestPass123')
                assert user.role == role

    def test_user_repr(self, app):
        """User repr"""
        with app.app_context():
            user = User(username='repr_test', role='chemist')
            repr_str = repr(user)
            assert 'repr_test' in repr_str


class TestSampleModel:
    """Sample model тестүүд"""

    def test_sample_creation(self, app):
        """Sample үүсгэх"""
        with app.app_context():
            sample = Sample(
                sample_code='MODEL-TEST-001',
                client_name='QC',
                sample_type='2hour',
                received_date=datetime.now()
            )
            assert sample.sample_code == 'MODEL-TEST-001'
            assert sample.client_name == 'QC'

    def test_sample_status_default(self, app):
        """Sample default status"""
        with app.app_context():
            sample = Sample(
                sample_code='STATUS-TEST-001',
                client_name='QC',
                sample_type='2hour',
                received_date=datetime.now()
            )
            # Default status should be 'new' or None
            assert sample.status in ['new', None, 'New']

    def test_sample_mass_ready(self, app):
        """Sample mass ready"""
        with app.app_context():
            sample = Sample(
                sample_code='MASS-TEST-001',
                client_name='QC',
                sample_type='2hour',
                received_date=datetime.now(),
                mass_ready=True
            )
            assert sample.mass_ready is True

    def test_sample_analyses_to_perform(self, app):
        """Sample analyses to perform"""
        with app.app_context():
            sample = Sample(
                sample_code='ANALYSES-TEST-001',
                client_name='QC',
                sample_type='2hour',
                received_date=datetime.now(),
                analyses_to_perform='["Mad", "Aad", "Vad"]'
            )
            assert sample.analyses_to_perform == '["Mad", "Aad", "Vad"]'

    def test_sample_notes(self, app):
        """Sample notes"""
        with app.app_context():
            sample = Sample(
                sample_code='NOTES-TEST-001',
                client_name='QC',
                sample_type='2hour',
                received_date=datetime.now(),
                notes='Test notes'
            )
            assert sample.notes == 'Test notes'


class TestAnalysisResultModel:
    """AnalysisResult model тестүүд"""

    def test_result_creation(self, app):
        """Result үүсгэх"""
        with app.app_context():
            result = AnalysisResult(
                sample_id=1,
                analysis_code='Mad',
                final_result=5.25
            )
            assert result.analysis_code == 'Mad'
            assert result.final_result == 5.25

    def test_result_status(self, app):
        """Result status"""
        with app.app_context():
            for status in ['pending_review', 'approved', 'rejected', 'draft']:
                result = AnalysisResult(
                    sample_id=1,
                    analysis_code='Mad',
                    final_result=5.25,
                    status=status
                )
                assert result.status == status

    def test_result_raw_data(self, app):
        """Result raw data"""
        with app.app_context():
            result = AnalysisResult(
                sample_id=1,
                analysis_code='Mad',
                raw_data='{"p1": 5.0, "p2": 5.5}'
            )
            assert result.raw_data == '{"p1": 5.0, "p2": 5.5}'


class TestControlStandardModel:
    """ControlStandard model тестүүд"""

    def test_control_standard_exists(self, app):
        """Control standard model exists"""
        with app.app_context():
            # Just verify the model can be queried
            standards = ControlStandard.query.all()
            assert isinstance(standards, list)


class TestEquipmentModel:
    """Equipment model тестүүд"""

    def test_equipment_query(self, app):
        """Equipment query"""
        with app.app_context():
            # Just verify the model can be queried
            equipment = Equipment.query.all()
            assert isinstance(equipment, list)


class TestSystemSettingModel:
    """SystemSetting model тестүүд"""

    def test_system_setting_query(self, app):
        """System setting query"""
        with app.app_context():
            # Just verify the model can be queried
            settings = SystemSetting.query.all()
            assert isinstance(settings, list)


class TestCorrectiveActionModel:
    """CorrectiveAction model тестүүд"""

    def test_capa_query(self, app):
        """CAPA query"""
        with app.app_context():
            # Just verify the model can be queried
            capas = CorrectiveAction.query.all()
            assert isinstance(capas, list)
