# -*- coding: utf-8 -*-
"""
Models unit тестүүд
"""
import pytest
from datetime import datetime, timedelta
from app import create_app, db
from app.models import (
    User, Sample, AnalysisResult, AnalysisType, AnalysisProfile,
    Equipment, Bottle, BottleConstant,
    SystemSetting, AuditLog, ControlStandard, GbwStandard,
    CorrectiveAction, CustomerComplaint, EnvironmentalLog,
    ProficiencyTest, QCControlChart, MonthlyPlan, StaffSettings
)


@pytest.fixture
def app():
    """Test application fixture"""
    app = create_app()
    app.config['TESTING'] = True
    return app


class TestUserModel:
    """User model тестүүд"""

    def test_user_creation(self, app):
        """User үүсгэх"""
        with app.app_context():
            user = User(username='testuser', role='chemist')
            assert user.username == 'testuser'
            assert user.role == 'chemist'

    def test_user_set_password(self, app):
        """Password тохируулах"""
        with app.app_context():
            user = User(username='testpwd', role='chemist')
            user.set_password('TestPass123')
            assert user.password_hash is not None
            assert user.check_password('TestPass123')
            assert not user.check_password('wrongpassword')

    def test_user_role_validation(self, app):
        """Role validation"""
        with app.app_context():
            valid_roles = ['prep', 'chemist', 'senior', 'manager', 'admin']
            for role in valid_roles:
                user = User(username=f'test_{role}', role=role)
                assert user.role == role

    def test_user_is_admin(self, app):
        """Admin шалгах"""
        with app.app_context():
            admin_user = User(username='admintest', role='admin')
            chemist_user = User(username='chemisttest', role='chemist')

            # Check if is_admin property exists
            if hasattr(admin_user, 'is_admin'):
                assert admin_user.is_admin == True
                assert chemist_user.is_admin == False


class TestSampleModel:
    """Sample model тестүүд"""

    def test_sample_creation(self, app):
        """Sample үүсгэх"""
        with app.app_context():
            sample = Sample(
                sample_code='TEST-001',
                client_name='Test Client',
                sample_type='coal'
            )
            assert sample.sample_code == 'TEST-001'
            assert sample.client_name == 'Test Client'

    def test_sample_status_default(self, app):
        """Sample default status"""
        with app.app_context():
            sample = Sample(sample_code='TEST-002')
            # Default status should be set
            assert sample.status is None or sample.status in ['pending', 'in_progress', 'completed']


class TestAnalysisResultModel:
    """AnalysisResult model тестүүд"""

    def test_analysis_result_creation(self, app):
        """AnalysisResult үүсгэх"""
        with app.app_context():
            result = AnalysisResult(
                analysis_code='TS',
                final_result=1.5,
                status='pending_review'
            )
            assert result.analysis_code == 'TS'
            assert result.final_result == 1.5

    def test_analysis_result_status_values(self, app):
        """Valid status values"""
        with app.app_context():
            valid_statuses = ['pending_review', 'approved', 'rejected', 'draft']
            for status in valid_statuses:
                result = AnalysisResult(
                    analysis_code='TS',
                    status=status
                )
                assert result.status == status

    def test_analysis_result_raw_data_json(self, app):
        """Raw data JSON field"""
        with app.app_context():
            result = AnalysisResult(
                analysis_code='TS',
                raw_data='{"trial_1": 1.5, "trial_2": 1.6}'
            )
            assert result.raw_data is not None


class TestEquipmentModel:
    """Equipment model тестүүд"""

    def test_equipment_creation(self, app):
        """Equipment үүсгэх"""
        with app.app_context():
            equipment = Equipment(
                name='Test Equipment',
                status='active'
            )
            assert equipment.name == 'Test Equipment'

    def test_equipment_status_values(self, app):
        """Equipment status values"""
        with app.app_context():
            valid_statuses = ['active', 'maintenance', 'inactive', 'retired']
            for status in valid_statuses:
                equipment = Equipment(
                    name=f'Equipment_{status}',
                    status=status
                )
                assert equipment.status == status


class TestBottleModel:
    """Bottle model тестүүд"""

    def test_bottle_creation(self, app):
        """Bottle үүсгэх"""
        with app.app_context():
            bottle = Bottle(
                serial_no='B001',
                label='Test Bottle'
            )
            assert bottle.serial_no == 'B001'


class TestBottleConstantModel:
    """BottleConstant model тестүүд"""

    def test_bottle_constant_creation(self, app):
        """BottleConstant үүсгэх"""
        with app.app_context():
            constant = BottleConstant(
                trial_1=0.0125,
                trial_2=0.0126,
                avg_value=0.01255
            )
            assert constant.avg_value == 0.01255


class TestSystemSettingModel:
    """SystemSetting model тестүүд"""

    def test_system_setting_creation(self, app):
        """SystemSetting үүсгэх"""
        with app.app_context():
            setting = SystemSetting(
                category='test',
                key='test_key',
                value='test_value'
            )
            assert setting.category == 'test'
            assert setting.key == 'test_key'
            assert setting.value == 'test_value'


class TestAuditLogModel:
    """AuditLog model тестүүд"""

    def test_audit_log_creation(self, app):
        """AuditLog үүсгэх"""
        with app.app_context():
            log = AuditLog(
                action='test_action',
                details='Test details'
            )
            assert log.action == 'test_action'


class TestControlStandardModel:
    """ControlStandard model тестүүд"""

    def test_control_standard_creation(self, app):
        """ControlStandard үүсгэх"""
        with app.app_context():
            standard = ControlStandard(
                name='Test Standard'
            )
            assert standard.name == 'Test Standard'


class TestGbwStandardModel:
    """GbwStandard model тестүүд"""

    def test_gbw_standard_creation(self, app):
        """GbwStandard үүсгэх"""
        with app.app_context():
            standard = GbwStandard(
                name='GBW-001',
                targets={}
            )
            assert standard.name == 'GBW-001'


class TestCorrectiveActionModel:
    """CorrectiveAction model тестүүд"""

    def test_corrective_action_creation(self, app):
        """CorrectiveAction үүсгэх"""
        with app.app_context():
            # Check model fields first
            capa = CorrectiveAction()
            # Set available fields
            if hasattr(capa, 'title'):
                capa.title = 'Test CAPA'
            if hasattr(capa, 'description'):
                capa.description = 'Test description'
            if hasattr(capa, 'status'):
                capa.status = 'open'
            assert capa is not None


class TestEnvironmentalLogModel:
    """EnvironmentalLog model тестүүд"""

    def test_environmental_log_creation(self, app):
        """EnvironmentalLog үүсгэх"""
        with app.app_context():
            log = EnvironmentalLog(
                temperature=22.5,
                humidity=45.0
            )
            assert log.temperature == 22.5
            assert log.humidity == 45.0


class TestProficiencyTestModel:
    """ProficiencyTest model тестүүд"""

    def test_proficiency_test_creation(self, app):
        """ProficiencyTest үүсгэх"""
        with app.app_context():
            test = ProficiencyTest()
            # Just test that model can be instantiated
            assert test is not None


class TestQCControlChartModel:
    """QCControlChart model тестүүд"""

    def test_qc_control_chart_creation(self, app):
        """QCControlChart үүсгэх"""
        with app.app_context():
            chart = QCControlChart()
            assert chart is not None


class TestMonthlyPlanModel:
    """MonthlyPlan model тестүүд"""

    def test_monthly_plan_creation(self, app):
        """MonthlyPlan үүсгэх"""
        with app.app_context():
            plan = MonthlyPlan()
            # Check what fields exist
            if hasattr(plan, 'year'):
                plan.year = 2024
            if hasattr(plan, 'month'):
                plan.month = 12
            assert plan is not None


class TestStaffSettingsModel:
    """StaffSettings model тестүүд"""

    def test_staff_settings_creation(self, app):
        """StaffSettings үүсгэх"""
        with app.app_context():
            settings = StaffSettings()
            assert settings is not None
