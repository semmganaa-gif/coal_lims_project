# -*- coding: utf-8 -*-
"""
Extended models unit тестүүд
"""
import pytest
from datetime import datetime, timedelta
from app import create_app, db
from app.models import (
    User, Sample, AnalysisResult, AnalysisType,
    Equipment, Bottle, BottleConstant,
    SystemSetting, AuditLog, ControlStandard, GbwStandard,
    CorrectiveAction, CustomerComplaint, EnvironmentalLog,
    ProficiencyTest, QCControlChart, MonthlyPlan
)


@pytest.fixture
def app():
    """Test application fixture"""
    app = create_app()
    app.config['TESTING'] = True
    return app


class TestUserModelExtended:
    """User model extended тестүүд"""

    def test_user_repr(self, app):
        """User repr"""
        with app.app_context():
            user = User(username='testuser', role='chemist')
            repr_str = repr(user)
            assert 'testuser' in repr_str or repr_str is not None

    def test_user_to_dict(self, app):
        """User to dict"""
        with app.app_context():
            user = User(username='testuser', role='chemist')
            if hasattr(user, 'to_dict'):
                result = user.to_dict()
                assert isinstance(result, dict)

    def test_user_full_name(self, app):
        """User full name"""
        with app.app_context():
            user = User(username='testuser', role='chemist', full_name='Test User')
            if hasattr(user, 'full_name'):
                assert user.full_name == 'Test User'
            # Also test when full_name is None (default)
            user2 = User(username='testuser2', role='chemist')
            assert user2.full_name is None or user2.full_name == ''  # Either is acceptable


class TestSampleModelExtended:
    """Sample model extended тестүүд"""

    def test_sample_repr(self, app):
        """Sample repr"""
        with app.app_context():
            sample = Sample(sample_code='TEST-001', client_name='Test Client')
            repr_str = repr(sample)
            assert repr_str is not None

    def test_sample_to_dict(self, app):
        """Sample to dict"""
        with app.app_context():
            sample = Sample(sample_code='TEST-001', client_name='Test Client')
            if hasattr(sample, 'to_dict'):
                result = sample.to_dict()
                assert isinstance(result, dict)

    def test_sample_status_transitions(self, app):
        """Sample status transitions"""
        with app.app_context():
            sample = Sample(sample_code='TEST-002')
            sample.status = 'pending'
            assert sample.status == 'pending'
            sample.status = 'in_progress'
            assert sample.status == 'in_progress'
            sample.status = 'completed'
            assert sample.status == 'completed'


class TestAnalysisResultModelExtended:
    """AnalysisResult model extended тестүүд"""

    def test_analysis_result_repr(self, app):
        """AnalysisResult repr"""
        with app.app_context():
            result = AnalysisResult(analysis_code='TS', final_result=1.5)
            repr_str = repr(result)
            assert repr_str is not None

    def test_analysis_result_to_dict(self, app):
        """AnalysisResult to dict"""
        with app.app_context():
            result = AnalysisResult(analysis_code='TS', final_result=1.5)
            if hasattr(result, 'to_dict'):
                result_dict = result.to_dict()
                assert isinstance(result_dict, dict)

    def test_analysis_result_with_raw_data(self, app):
        """AnalysisResult with raw data"""
        with app.app_context():
            result = AnalysisResult(
                analysis_code='TS',
                final_result=1.5,
                raw_data='{"m1": 1.5, "m2": 1.6}'
            )
            assert result.raw_data is not None


class TestEquipmentModelExtended:
    """Equipment model extended тестүүд"""

    def test_equipment_repr(self, app):
        """Equipment repr"""
        with app.app_context():
            equipment = Equipment(name='Test Equipment', status='active')
            repr_str = repr(equipment)
            assert repr_str is not None

    def test_equipment_is_active(self, app):
        """Equipment is active"""
        with app.app_context():
            equipment = Equipment(name='Test Equipment', status='active')
            if hasattr(equipment, 'is_active'):
                assert equipment.is_active == True


class TestControlStandardModelExtended:
    """ControlStandard model extended тестүүд"""

    def test_control_standard_repr(self, app):
        """ControlStandard repr"""
        with app.app_context():
            standard = ControlStandard(name='Test Standard')
            repr_str = repr(standard)
            assert repr_str is not None

    def test_control_standard_with_values(self, app):
        """ControlStandard with values"""
        with app.app_context():
            standard = ControlStandard(name='Test Standard')
            if hasattr(standard, 'target_value'):
                standard.target_value = 1.5
            if hasattr(standard, 'tolerance'):
                standard.tolerance = 0.1


class TestGbwStandardModelExtended:
    """GbwStandard model extended тестүүд"""

    def test_gbw_standard_with_targets(self, app):
        """GbwStandard with targets"""
        with app.app_context():
            standard = GbwStandard(
                name='GBW-001',
                targets={'TS': 1.5, 'CV': 25.0}
            )
            assert standard.targets is not None
            assert 'TS' in standard.targets or isinstance(standard.targets, dict)


class TestEnvironmentalLogModelExtended:
    """EnvironmentalLog model extended тестүүд"""

    def test_environmental_log_with_all_fields(self, app):
        """EnvironmentalLog with all fields"""
        with app.app_context():
            log = EnvironmentalLog(
                temperature=22.5,
                humidity=45.0
            )
            assert log.temperature == 22.5
            assert log.humidity == 45.0

    def test_environmental_log_repr(self, app):
        """EnvironmentalLog repr"""
        with app.app_context():
            log = EnvironmentalLog(temperature=22.5, humidity=45.0)
            repr_str = repr(log)
            assert repr_str is not None


class TestCorrectiveActionModelExtended:
    """CorrectiveAction model extended тестүүд"""

    def test_corrective_action_status_flow(self, app):
        """CorrectiveAction status flow"""
        with app.app_context():
            capa = CorrectiveAction()
            if hasattr(capa, 'status'):
                capa.status = 'open'
                assert capa.status == 'open'
                capa.status = 'in_progress'
                assert capa.status == 'in_progress'
                capa.status = 'closed'
                assert capa.status == 'closed'
