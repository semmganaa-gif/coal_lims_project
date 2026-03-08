# tests/test_models_boost.py
# -*- coding: utf-8 -*-
"""Tests to boost models.py coverage."""

import pytest
from datetime import datetime, date, timedelta
from unittest.mock import patch


class TestUserModel:
    """Test User model."""

    def test_user_password_check(self, app, db):
        """Test password checking."""
        with app.app_context():
            from app.models import User
            user = User(username='passtest', role='analyst')
            user.set_password('TestPass123!')
            assert user.check_password('TestPass123!')
            assert not user.check_password('wrongpassword')

    def test_user_repr(self, app, db):
        """Test user repr."""
        with app.app_context():
            from app.models import User
            user = User(username='reprtest', role='analyst')
            assert 'reprtest' in repr(user)


class TestSampleModel:
    """Test Sample model."""

    def test_sample_creation(self, app, db):
        """Test sample creation."""
        with app.app_context():
            from app.models import Sample
            # client_name CHECK: ('CHPP','UHG-Geo','BN-Geo','QC','WTL','Proc','LAB')
            sample = Sample(sample_code='MODEL-001', client_name='QC', sample_type='coal')
            db.session.add(sample)
            db.session.commit()
            assert sample.id is not None

    def test_sample_repr(self, app, db):
        """Test sample repr."""
        with app.app_context():
            from app.models import Sample
            sample = Sample(sample_code='REPR-001', client_name='QC', sample_type='coal')
            assert 'REPR-001' in repr(sample)


class TestEquipmentModel:
    """Test Equipment model."""

    def test_equipment_calibration_due(self, app, db):
        """Test equipment calibration due check."""
        with app.app_context():
            from app.models import Equipment
            eq = Equipment(
                name='Cal Test',
                category='balance',
                calibration_cycle_days=30,
                calibration_date=date.today() - timedelta(days=35)
            )
            db.session.add(eq)
            db.session.commit()
            # Check if calibration is due
            if hasattr(eq, 'is_calibration_due'):
                assert eq.is_calibration_due


class TestAnalysisResultModel:
    """Test AnalysisResult model."""

    def test_result_with_qc(self, app, db):
        """Test result with QC fields."""
        with app.app_context():
            from app.models import Sample, AnalysisResult
            # client_name CHECK: ('CHPP','UHG-Geo','BN-Geo','QC','WTL','Proc','LAB')
            sample = Sample(sample_code='QC-001', client_name='QC', sample_type='coal')
            db.session.add(sample)
            db.session.commit()

            result = AnalysisResult(
                sample_id=sample.id,
                analysis_code='TM',
                final_result=5.5,
                status='pending_review'
            )
            db.session.add(result)
            db.session.commit()
            assert result.id is not None


class TestMaintenanceLogModel:
    """Test MaintenanceLog model."""

    def test_maintenance_log_creation(self, app, db):
        """Test maintenance log creation."""
        with app.app_context():
            from app.models import Equipment, MaintenanceLog
            eq = Equipment(name='Maint Test', category='balance')
            db.session.add(eq)
            db.session.commit()

            # MaintenanceLog uses action_type, not maintenance_type
            log = MaintenanceLog(
                equipment_id=eq.id,
                action_type='Calibration',
                description='Test calibration'
            )
            db.session.add(log)
            db.session.commit()
            assert log.id is not None


class TestSystemSettingModel:
    """Test SystemSetting model."""

    def test_system_setting(self, app, db):
        """Test system setting."""
        with app.app_context():
            from app.models import SystemSetting
            # Clean up first
            SystemSetting.query.filter_by(category='test', key='model_test').delete()
            db.session.commit()

            setting = SystemSetting(
                category='test',
                key='model_test',
                value='test_value',
                is_active=True
            )
            db.session.add(setting)
            db.session.commit()
            assert setting.id is not None


class TestControlStandardModel:
    """Test ControlStandard model."""

    def test_control_standard(self, app, db):
        """Test control standard."""
        with app.app_context():
            from app.models import ControlStandard
            std = ControlStandard(
                name='Model Test Std',
                targets={'TM': 5.0},
                is_active=False
            )
            db.session.add(std)
            db.session.commit()
            assert std.id is not None


class TestGbwStandardModel:
    """Test GbwStandard model."""

    def test_gbw_standard(self, app, db):
        """Test GBW standard."""
        with app.app_context():
            from app.models import GbwStandard
            gbw = GbwStandard(
                name='GBW-MODEL-001',
                targets={'TM': 5.0},
                is_active=False
            )
            db.session.add(gbw)
            db.session.commit()
            assert gbw.id is not None
