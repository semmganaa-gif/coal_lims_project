# tests/test_int_index_coverage_new.py
# -*- coding: utf-8 -*-
"""
main/index.py модулийн coverage нэмэгдүүлэх тестүүд.
"""

import pytest
from datetime import datetime, date, timedelta


class TestIndexHelperFunctions:
    """Index helper функцүүдийн тест."""

    def test_get_report_email_recipients_empty(self, app):
        """Test email recipients when no settings."""
        from app.routes.main.index import get_report_email_recipients

        with app.app_context():
            result = get_report_email_recipients()
            assert 'to' in result
            assert 'cc' in result
            assert isinstance(result['to'], list)
            assert isinstance(result['cc'], list)

    def test_get_report_email_recipients_with_settings(self, app):
        """Test email recipients with settings."""
        from app.routes.main.index import get_report_email_recipients
        from app.models import SystemSetting
        from app import db

        with app.app_context():
            # Clean up existing settings first to avoid UniqueConstraint
            SystemSetting.query.filter(
                SystemSetting.category == 'email',
                SystemSetting.key.in_(['report_recipients_to', 'report_recipients_cc'])
            ).delete(synchronize_session=False)
            db.session.commit()

            # Add TO setting
            to_setting = SystemSetting(
                category='email',
                key='report_recipients_to',
                value='test@example.com, test2@example.com',
                is_active=True
            )
            # Add CC setting
            cc_setting = SystemSetting(
                category='email',
                key='report_recipients_cc',
                value='cc@example.com',
                is_active=True
            )
            db.session.add_all([to_setting, cc_setting])
            db.session.commit()

            result = get_report_email_recipients()
            assert 'test@example.com' in result['to']
            assert 'cc@example.com' in result['cc']

    def test_get_12h_shift_code(self, app):
        """Test shift code generation."""
        from app.routes.main.helpers import get_12h_shift_code
        from datetime import datetime

        # Morning shift (8:00)
        morning = datetime(2025, 12, 23, 8, 0, 0)
        code = get_12h_shift_code(morning)
        assert code in ['D', 'N', '_D', '_N']  # Day or Night (with or without prefix)

        # Night shift (20:00)
        night = datetime(2025, 12, 23, 20, 0, 0)
        code = get_12h_shift_code(night)
        assert code in ['D', 'N', '_D', '_N']

    def test_get_quarter_code(self, app):
        """Test quarter code generation."""
        from app.routes.main.helpers import get_quarter_code
        from datetime import datetime

        # January - Q1
        jan = datetime(2025, 1, 15)
        result = get_quarter_code(jan)
        assert 'Q1' in result

        # April - Q2
        apr = datetime(2025, 4, 15)
        result = get_quarter_code(apr)
        assert 'Q2' in result

        # July - Q3
        jul = datetime(2025, 7, 15)
        result = get_quarter_code(jul)
        assert 'Q3' in result

        # October - Q4
        oct_date = datetime(2025, 10, 15)
        result = get_quarter_code(oct_date)
        assert 'Q4' in result


class TestIndexRoutes:
    """Index route тестүүд."""

    def test_index_get(self, app, auth_admin):
        """Test index page GET."""
        response = auth_admin.get('/coal')
        assert response.status_code in [200, 302]

    def test_index_get_with_active_tab(self, app, auth_admin):
        """Test index with active tab parameter."""
        response = auth_admin.get('/coal?active_tab=add-pane')
        assert response.status_code in [200, 302]

    def test_index_post_admin_role(self, app, auth_admin):
        """Admin user can register samples."""
        response = auth_admin.post('/coal', data={
            'client_name': 'CHPP',
            'sample_type': 'SC',
            'sample_condition': 'good',
            'sample_date': date.today().strftime('%Y-%m-%d'),
            'retention_period': '7',
        }, follow_redirects=True)
        assert response.status_code == 200


class TestIndexMultiSampleRegistration:
    """Олон дээж бүртгэлийн тестүүд."""

    def test_chpp_2h_registration(self, app, auth_admin):
        """Register CHPP 2h samples."""
        response = auth_admin.post('/coal', data={
            'client_name': 'CHPP',
            'sample_type': 'SC',
            'sample_codes': ['SC_2H_001', 'SC_2H_002'],
            'weights': ['100.5', '150.2'],
            'list_type': 'chpp_2h',
            'sample_condition': 'good',
            'sample_date': date.today().strftime('%Y-%m-%d'),
            'retention_period': '7',
        }, follow_redirects=True)
        assert response.status_code == 200

    def test_chpp_4h_registration(self, app, auth_admin):
        """Register CHPP 4h samples."""
        response = auth_admin.post('/coal', data={
            'client_name': 'CHPP',
            'sample_type': 'SC',
            'sample_codes': ['SC_4H_001'],
            'list_type': 'chpp_4h',
            'sample_condition': 'good',
            'sample_date': date.today().strftime('%Y-%m-%d'),
            'retention_period': '7',
        }, follow_redirects=True)
        assert response.status_code == 200


class TestWTLRegistration:
    """WTL бүртгэлийн тестүүд."""

    def test_wtl_registration(self, app, auth_admin):
        """Register WTL samples."""
        response = auth_admin.post('/coal', data={
            'client_name': 'WTL',
            'sample_type': 'WTL',
            'lab_number': 'WTL001',
            'sample_condition': 'good',
            'sample_date': date.today().strftime('%Y-%m-%d'),
            'retention_period': '7',
        }, follow_redirects=True)
        assert response.status_code == 200

    def test_wtl_size_registration(self, app, auth_admin):
        """Register Size samples."""
        response = auth_admin.post('/coal', data={
            'client_name': 'WTL',
            'sample_type': 'Size',
            'lab_number': 'SIZE001',
            'sample_condition': 'good',
            'sample_date': date.today().strftime('%Y-%m-%d'),
            'retention_period': '7',
        }, follow_redirects=True)
        assert response.status_code == 200

    def test_wtl_fl_registration(self, app, auth_admin):
        """Register FL samples."""
        response = auth_admin.post('/coal', data={
            'client_name': 'WTL',
            'sample_type': 'FL',
            'lab_number': 'FL001',
            'sample_condition': 'good',
            'sample_date': date.today().strftime('%Y-%m-%d'),
            'retention_period': '7',
        }, follow_redirects=True)
        assert response.status_code == 200


class TestLABRegistration:
    """LAB бүртгэлийн тестүүд."""

    def test_lab_cm_registration(self, app, auth_admin):
        """Register LAB CM sample."""
        response = auth_admin.post('/coal', data={
            'client_name': 'LAB',
            'sample_type': 'CM',
            'sample_condition': 'good',
            'sample_date': date.today().strftime('%Y-%m-%d'),
            'retention_period': '7',
        }, follow_redirects=True)
        assert response.status_code == 200

    def test_lab_gbw_registration(self, app, auth_admin):
        """Register LAB GBW sample."""
        response = auth_admin.post('/coal', data={
            'client_name': 'LAB',
            'sample_type': 'GBW',
            'sample_condition': 'good',
            'sample_date': date.today().strftime('%Y-%m-%d'),
            'retention_period': '7',
        }, follow_redirects=True)
        assert response.status_code == 200

    def test_lab_test_registration(self, app, auth_admin):
        """Register LAB Test sample."""
        response = auth_admin.post('/coal', data={
            'client_name': 'LAB',
            'sample_type': 'Test',
            'sample_condition': 'good',
            'sample_date': date.today().strftime('%Y-%m-%d'),
            'retention_period': '7',
        }, follow_redirects=True)
        assert response.status_code == 200


class TestGenericRegistration:
    """Generic бүртгэлийн тестүүд."""

    def test_uhg_geo_registration(self, app, auth_admin):
        """Register UHG-Geo sample."""
        response = auth_admin.post('/coal', data={
            'client_name': 'UHG-Geo',
            'sample_type': 'coal',
            'sample_code': 'GEO_001',
            'sample_condition': 'good',
            'sample_date': date.today().strftime('%Y-%m-%d'),
            'retention_period': '7',
        }, follow_redirects=True)
        assert response.status_code == 200

    def test_bn_geo_registration(self, app, auth_admin):
        """Register BN-Geo sample."""
        response = auth_admin.post('/coal', data={
            'client_name': 'BN-Geo',
            'sample_type': 'coal',
            'sample_code': 'BN_001',
            'sample_condition': 'good',
            'sample_date': date.today().strftime('%Y-%m-%d'),
            'retention_period': '7',
        }, follow_redirects=True)
        assert response.status_code == 200

    def test_qc_registration(self, app, auth_admin):
        """Register QC sample."""
        response = auth_admin.post('/coal', data={
            'client_name': 'QC',
            'sample_type': 'coal',
            'sample_code': 'QC_001',
            'sample_condition': 'good',
            'sample_date': date.today().strftime('%Y-%m-%d'),
            'retention_period': '7',
        }, follow_redirects=True)
        assert response.status_code == 200

    def test_proc_registration(self, app, auth_admin):
        """Register Proc sample."""
        response = auth_admin.post('/coal', data={
            'client_name': 'Proc',
            'sample_type': 'coal',
            'sample_code': 'PROC_001',
            'sample_condition': 'good',
            'sample_date': date.today().strftime('%Y-%m-%d'),
            'retention_period': '7',
        }, follow_redirects=True)
        assert response.status_code == 200
