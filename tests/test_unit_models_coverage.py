# tests/unit/test_models_coverage.py
"""
Models coverage тест
"""
import pytest
from datetime import datetime, timedelta
from app.models import (
    User, Sample, AnalysisResult, Equipment,
    SystemSetting, ControlStandard, GbwStandard,
    AnalysisResultLog
)


class TestUserModel:
    """User model тест"""

    def test_user_creation(self, app):
        """User үүсгэх"""
        with app.app_context():
            user = User(username='test_user', role='chemist')
            user.set_password('TestPass123')

            assert user.username == 'test_user'
            assert user.role == 'chemist'

    def test_user_password(self, app):
        """Password check"""
        with app.app_context():
            user = User(username='test_pw')
            user.set_password('TestPass123')

            assert user.check_password('TestPass123') == True
            assert user.check_password('WrongPass') == False

    def test_user_repr(self, app):
        """User repr"""
        with app.app_context():
            user = User(username='test_repr')
            assert 'test_repr' in str(user)


class TestSampleModel:
    """Sample model тест"""

    def test_sample_creation(self, app):
        """Sample үүсгэх"""
        with app.app_context():
            sample = Sample(
                sample_code='TEST-001',
                client_name='Test Client',
                sample_type='Test Type',
                status='new'
            )

            assert sample.sample_code == 'TEST-001'
            assert sample.client_name == 'Test Client'

    def test_sample_status_change(self, app):
        """Sample status change"""
        with app.app_context():
            sample = Sample(sample_code='TEST-002', status='new')
            sample.status = 'completed'

            assert sample.status == 'completed'

    def test_sample_with_dates(self, app):
        """Sample with dates"""
        with app.app_context():
            now = datetime.now()
            sample = Sample(
                sample_code='TEST-003',
                received_date=now
            )

            assert sample.received_date == now


class TestAnalysisResultModel:
    """AnalysisResult model тест"""

    def test_result_creation(self, app):
        """Result үүсгэх"""
        with app.app_context():
            result = AnalysisResult(
                sample_id=1,
                analysis_code='Mad',
                final_result=10.5,
                status='pending'
            )

            assert result.analysis_code == 'Mad'
            assert result.final_result == 10.5

    def test_result_with_raw_data(self, app):
        """Result with raw_data"""
        with app.app_context():
            import json
            raw = {'r1': 10.4, 'r2': 10.6}
            result = AnalysisResult(
                sample_id=1,
                analysis_code='Aad',
                raw_data=json.dumps(raw)
            )

            assert result.raw_data is not None


class TestEquipmentModel:
    """Equipment model тест"""

    def test_equipment_creation(self, app):
        """Equipment үүсгэх"""
        with app.app_context():
            equipment = Equipment(
                name='Test Equipment',
                serial_number='SN-001',
                manufacturer='Test Manufacturer'
            )

            assert equipment.name == 'Test Equipment'
            assert equipment.serial_number == 'SN-001'


class TestSystemSettingModel:
    """SystemSetting model тест"""

    def test_setting_creation(self, app):
        """Setting үүсгэх"""
        with app.app_context():
            setting = SystemSetting(
                category='test',
                key='test_key',
                value='test_value',
                is_active=True
            )

            assert setting.category == 'test'
            assert setting.key == 'test_key'


class TestControlStandardModel:
    """ControlStandard model тест"""

    def test_standard_creation(self, app):
        """Standard үүсгэх"""
        with app.app_context():
            standard = ControlStandard(
                name='CM-001',
                is_active=True
            )

            assert standard.name == 'CM-001'


class TestGbwStandardModel:
    """GbwStandard model тест"""

    def test_gbw_creation(self, app):
        """GBW үүсгэх"""
        with app.app_context():
            gbw = GbwStandard(
                name='GBW-001',
                is_active=True
            )

            assert gbw.name == 'GBW-001'


class TestAnalysisResultLogModel:
    """AnalysisResultLog model тест"""

    def test_log_creation(self, app):
        """Log үүсгэх"""
        with app.app_context():
            log = AnalysisResultLog(
                analysis_result_id=1,
                action='create',
                user_id=1
            )

            assert log.action == 'create'
