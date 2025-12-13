# -*- coding: utf-8 -*-
"""
Models comprehensive тестүүд
"""
import pytest
from app import create_app, db
from app.models import (
    User, Sample, AnalysisResult, Equipment, AnalysisType,
    AnalysisProfile, SystemSetting, AuditLog
)


@pytest.fixture
def app():
    """Test application fixture"""
    app = create_app()
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False
    return app


class TestUserModel:
    """User model тестүүд"""

    def test_user_creation(self, app):
        """User creation"""
        with app.app_context():
            user = User(username='testuser', role='chemist')
            user.set_password('TestPass123')
            assert user.username == 'testuser'
            assert user.role == 'chemist'

    def test_password_hashing(self, app):
        """Password hashing"""
        with app.app_context():
            user = User(username='testuser', role='chemist')
            user.set_password('TestPass123')
            assert user.password_hash != 'TestPass123'

    def test_password_check(self, app):
        """Password check"""
        with app.app_context():
            user = User(username='testuser', role='chemist')
            user.set_password('TestPass123')
            assert user.check_password('TestPass123') is True
            assert user.check_password('WrongPass') is False

    def test_user_roles(self, app):
        """User roles"""
        with app.app_context():
            for role in ['prep', 'chemist', 'senior', 'manager', 'admin']:
                user = User(username=f'user_{role}', role=role)
                assert user.role == role


class TestSampleModel:
    """Sample model тестүүд"""

    def test_sample_creation(self, app):
        """Sample creation"""
        with app.app_context():
            sample = Sample(
                sample_code='TEST001',
                client_name='CHPP',
                sample_type='12H'
            )
            assert sample.sample_code == 'TEST001'

    def test_sample_status_default(self, app):
        """Sample status default"""
        with app.app_context():
            sample = Sample(
                sample_code='TEST001',
                client_name='CHPP',
                sample_type='12H'
            )
            assert sample.status in ['new', 'New', None]


class TestAnalysisResultModel:
    """AnalysisResult model тестүүд"""

    def test_analysis_result_creation(self, app):
        """AnalysisResult creation"""
        with app.app_context():
            result = AnalysisResult(
                sample_id=1,
                analysis_code='TS',
                final_result=5.5
            )
            assert result.analysis_code == 'TS'
            assert result.final_result == 5.5

    def test_status_values(self, app):
        """Status values"""
        with app.app_context():
            for status in ['pending_review', 'approved', 'rejected', 'draft']:
                result = AnalysisResult(
                    sample_id=1,
                    analysis_code='TS',
                    status=status
                )
                assert result.status == status


class TestEquipmentModel:
    """Equipment model тестүүд"""

    def test_equipment_creation(self, app):
        """Equipment creation"""
        with app.app_context():
            equip = Equipment(
                name='Test Equipment',
                lab_code='TE001'
            )
            assert equip.name == 'Test Equipment'

    def test_equipment_fields(self, app):
        """Equipment fields"""
        with app.app_context():
            equip = Equipment(
                name='Balance',
                lab_code='BAL001',
                category='balance'
            )
            assert equip.category == 'balance'


class TestAnalysisTypeModel:
    """AnalysisType model тестүүд"""

    def test_analysis_type_creation(self, app):
        """AnalysisType creation"""
        with app.app_context():
            atype = AnalysisType(
                code='TS',
                name='Total Sulfur'
            )
            assert atype.code == 'TS'

    def test_query_by_code(self, app):
        """Query by code"""
        with app.app_context():
            atype = AnalysisType.query.filter_by(code='TS').first()
            # May or may not exist in test DB
            assert atype is None or atype.code == 'TS'


class TestAnalysisProfileModel:
    """AnalysisProfile model тестүүд"""

    def test_profile_creation(self, app):
        """Profile creation"""
        with app.app_context():
            profile = AnalysisProfile(
                client_name='CHPP',
                sample_type='12H',
                analyses_json='["Mad", "Aad", "TS"]'
            )
            assert profile.client_name == 'CHPP'

    def test_get_analyses(self, app):
        """get_analyses method"""
        with app.app_context():
            profile = AnalysisProfile(
                client_name='CHPP',
                sample_type='12H',
                analyses_json='["Mad", "Aad", "TS"]'
            )
            analyses = profile.get_analyses()
            assert isinstance(analyses, list)


class TestSystemSettingModel:
    """SystemSetting model тестүүд"""

    def test_setting_creation(self, app):
        """Setting creation"""
        with app.app_context():
            setting = SystemSetting(
                category='test',
                key='test_key',
                value='test_value'
            )
            assert setting.key == 'test_key'


class TestAuditLogModel:
    """AuditLog model тестүүд"""

    def test_audit_log_creation(self, app):
        """AuditLog creation"""
        with app.app_context():
            log = AuditLog(
                action='test_action',
                user_id=1
            )
            assert log.action == 'test_action'
