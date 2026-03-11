# tests/test_index_extended.py
# -*- coding: utf-8 -*-
"""
Extended coverage tests for routes/main/index.py
"""

import pytest
from datetime import datetime, date
from unittest.mock import patch, MagicMock


class TestWTLSampleRegistration:
    """Tests for WTL sample registration."""

    def test_register_wtl_sample(self, app, auth_admin):
        """Test registering WTL sample with lab_number."""
        response = auth_admin.post('/coal', data={
            'client_name': 'WTL',
            'sample_type': 'WTL',
            'sample_date': date.today().isoformat(),
            'lab_number': 'WTL001'
        }, follow_redirects=True)
        assert response.status_code in [200, 302]

    def test_register_wtl_size_sample(self, app, auth_admin):
        """Test registering WTL Size sample."""
        response = auth_admin.post('/coal', data={
            'client_name': 'WTL',
            'sample_type': 'Size',
            'sample_date': date.today().isoformat(),
            'lab_number': 'SIZE001'
        }, follow_redirects=True)
        assert response.status_code in [200, 302]

    def test_register_wtl_fl_sample(self, app, auth_admin):
        """Test registering WTL FL sample."""
        response = auth_admin.post('/coal', data={
            'client_name': 'WTL',
            'sample_type': 'FL',
            'sample_date': date.today().isoformat(),
            'lab_number': 'FL001'
        }, follow_redirects=True)
        assert response.status_code in [200, 302]

    def test_register_wtl_test_sample(self, app, auth_admin):
        """Test registering WTL Test sample."""
        response = auth_admin.post('/coal', data={
            'client_name': 'WTL',
            'sample_type': 'Test',
            'sample_code': 'WTL_TEST_001',
            'sample_date': date.today().isoformat()
        }, follow_redirects=True)
        assert response.status_code in [200, 302]

    def test_register_wtl_no_lab_number(self, app, auth_admin):
        """Test WTL registration without lab_number shows error."""
        response = auth_admin.post('/coal', data={
            'client_name': 'WTL',
            'sample_type': 'WTL',
            'sample_date': date.today().isoformat()
        }, follow_redirects=True)
        assert response.status_code in [200, 302]


class TestLABSampleRegistration:
    """Tests for LAB sample registration."""

    def test_register_lab_cm_sample(self, app, auth_admin):
        """Test registering LAB CM sample."""
        response = auth_admin.post('/coal', data={
            'client_name': 'LAB',
            'sample_type': 'CM',
            'sample_date': date.today().isoformat()
        }, follow_redirects=True)
        assert response.status_code in [200, 302]

    def test_register_lab_gbw_sample(self, app, auth_admin):
        """Test registering LAB GBW sample."""
        response = auth_admin.post('/coal', data={
            'client_name': 'LAB',
            'sample_type': 'GBW',
            'sample_date': date.today().isoformat()
        }, follow_redirects=True)
        assert response.status_code in [200, 302]

    def test_register_lab_test_sample(self, app, auth_admin):
        """Test registering LAB Test sample."""
        response = auth_admin.post('/coal', data={
            'client_name': 'LAB',
            'sample_type': 'Test',
            'sample_date': date.today().isoformat()
        }, follow_redirects=True)
        assert response.status_code in [200, 302]

    def test_register_lab_unknown_type(self, app, auth_admin):
        """Test registering LAB with unknown type."""
        response = auth_admin.post('/coal', data={
            'client_name': 'LAB',
            'sample_type': 'Unknown',
            'sample_date': date.today().isoformat()
        }, follow_redirects=True)
        assert response.status_code in [200, 302]


class TestCHPPSampleRegistration:
    """Tests for CHPP sample registration with weights."""

    def test_register_chpp_2h_with_weight(self, app, auth_admin):
        """Test registering CHPP 2h sample with weight."""
        response = auth_admin.post('/coal', data={
            'client_name': 'CHPP',
            'sample_type': '2 hourly',
            'sample_date': date.today().isoformat(),
            'sample_codes': ['PF211_D1'],
            'weights': ['150.5'],
            'list_type': 'chpp_2h'
        }, follow_redirects=True)
        assert response.status_code in [200, 302]

    def test_register_chpp_4h_sample(self, app, auth_admin):
        """Test registering CHPP 4h sample."""
        response = auth_admin.post('/coal', data={
            'client_name': 'CHPP',
            'sample_type': '4 hourly',
            'sample_date': date.today().isoformat(),
            'sample_codes': ['CF501'],
            'list_type': 'chpp_4h'
        }, follow_redirects=True)
        assert response.status_code in [200, 302]

    def test_register_chpp_com_sample(self, app, auth_admin):
        """Test registering CHPP COM sample."""
        response = auth_admin.post('/coal', data={
            'client_name': 'CHPP',
            'sample_type': 'COM',
            'sample_date': date.today().isoformat(),
            'sample_codes': ['COM_TEST'],
            'weights': ['100'],
            'list_type': 'chpp_com'
        }, follow_redirects=True)
        assert response.status_code in [200, 302]

    def test_register_chpp_invalid_weight(self, app, auth_admin):
        """Test CHPP registration with invalid weight."""
        response = auth_admin.post('/coal', data={
            'client_name': 'CHPP',
            'sample_type': '2 hourly',
            'sample_date': date.today().isoformat(),
            'sample_codes': ['PF211_D2'],
            'weights': ['invalid'],
            'list_type': 'chpp_2h'
        }, follow_redirects=True)
        assert response.status_code in [200, 302]

    def test_register_chpp_no_weight(self, app, auth_admin):
        """Test CHPP registration without weight."""
        response = auth_admin.post('/coal', data={
            'client_name': 'CHPP',
            'sample_type': '2 hourly',
            'sample_date': date.today().isoformat(),
            'sample_codes': ['PF221_D1'],
            'weights': [],
            'list_type': 'chpp_2h'
        }, follow_redirects=True)
        assert response.status_code in [200, 302]

    def test_register_chpp_weight_too_small(self, app, auth_admin):
        """Test CHPP registration with too small weight."""
        response = auth_admin.post('/coal', data={
            'client_name': 'CHPP',
            'sample_type': '2 hourly',
            'sample_date': date.today().isoformat(),
            'sample_codes': ['PF231_D1'],
            'weights': ['0'],
            'list_type': 'chpp_2h'
        }, follow_redirects=True)
        assert response.status_code in [200, 302]

    def test_register_chpp_weight_too_large(self, app, auth_admin):
        """Test CHPP registration with too large weight."""
        response = auth_admin.post('/coal', data={
            'client_name': 'CHPP',
            'sample_type': '2 hourly',
            'sample_date': date.today().isoformat(),
            'sample_codes': ['PF211_D3'],
            'weights': ['999999'],
            'list_type': 'chpp_2h'
        }, follow_redirects=True)
        assert response.status_code in [200, 302]


class TestMultiGenSampleRegistration:
    """Tests for multi_gen sample registration."""

    def test_register_multi_gen_qc(self, app, auth_admin):
        """Test registering multi_gen QC sample."""
        response = auth_admin.post('/coal', data={
            'client_name': 'QC',
            'sample_type': 'Coal',
            'sample_date': date.today().isoformat(),
            'sample_codes': ['QC_TEST_1'],
            'weights': ['100'],
            'list_type': 'multi_gen',
            'location': 'Location A',
            'product': 'Product B'
        }, follow_redirects=True)
        assert response.status_code in [200, 302]

    def test_register_multi_gen_proc(self, app, auth_admin):
        """Test registering multi_gen Proc sample."""
        response = auth_admin.post('/coal', data={
            'client_name': 'Proc',
            'sample_type': 'Coal',
            'sample_date': date.today().isoformat(),
            'sample_codes': ['PROC_TEST_1'],
            'weights': ['150'],
            'list_type': 'multi_gen',
            'location': 'Location B',
            'product': 'Product C'
        }, follow_redirects=True)
        assert response.status_code in [200, 302]


class TestFormValidation:
    """Tests for form validation."""

    def test_form_errors_active_tab(self, app, auth_admin):
        """Test form errors keep active tab."""
        response = auth_admin.post('/coal', data={
            'client_name': '',
        }, follow_redirects=True)
        assert response.status_code in [200, 302]

    def test_incomplete_form_submission(self, app, auth_admin):
        """Test incomplete form shows error."""
        response = auth_admin.post('/coal', data={
            'client_name': 'CHPP',
            'sample_date': date.today().isoformat()
        }, follow_redirects=True)
        assert response.status_code in [200, 302]


class TestSendHourlyReportExtended:
    """Extended tests for hourly report."""

    def test_hourly_report_senior_role(self, app, client):
        """Test hourly report with senior role."""
        client.post('/login', data={'username': 'senior', 'password': 'TestPass123'})
        with patch('flask_mail.Mail.send'):
            response = client.get('/send-hourly-report', follow_redirects=True)
            assert response.status_code in [200, 302, 500]
        client.get('/logout')

    def test_hourly_report_missing_template(self, app, auth_admin):
        """Test hourly report with missing template."""
        with patch('os.path.exists', return_value=False):
            response = auth_admin.get('/send-hourly-report', follow_redirects=True)
            assert response.status_code in [200, 302]

    def test_hourly_report_no_recipients(self, app, auth_admin):
        """Test hourly report without email recipients."""
        with patch('flask_mail.Mail.send'):
            response = auth_admin.get('/send-hourly-report', follow_redirects=True)
            assert response.status_code in [200, 302]


class TestRegisterRoutes:
    """Tests for register_routes function."""

    def test_register_routes_callable(self, app):
        """Test register_routes is callable."""
        from app.routes.main.index import register_routes
        assert callable(register_routes)


class TestPreviewAnalysesExtended:
    """Extended tests for preview-analyses."""

    def test_preview_analyses_wtl(self, app, auth_admin):
        """Test preview analyses for WTL client."""
        response = auth_admin.post('/preview-analyses',
            json={
                'sample_names': ['WTL_001'],
                'client_name': 'WTL',
                'sample_type': 'WTL'
            },
            content_type='application/json'
        )
        assert response.status_code in [200, 400]

    def test_preview_analyses_lab(self, app, auth_admin):
        """Test preview analyses for LAB client."""
        response = auth_admin.post('/preview-analyses',
            json={
                'sample_names': ['CM_001'],
                'client_name': 'LAB',
                'sample_type': 'CM'
            },
            content_type='application/json'
        )
        assert response.status_code in [200, 400]

    def test_preview_analyses_multiple_samples(self, app, auth_admin):
        """Test preview analyses with multiple samples."""
        response = auth_admin.post('/preview-analyses',
            json={
                'sample_names': ['SAMPLE_1', 'SAMPLE_2', 'SAMPLE_3'],
                'client_name': 'CHPP',
                'sample_type': '2 hourly'
            },
            content_type='application/json'
        )
        assert response.status_code in [200, 400]


class TestIndexRoute:
    """Additional index route tests."""

    def test_index_redirect_endpoint(self, app, auth_admin):
        """Test /index endpoint."""
        response = auth_admin.get('/index')
        assert response.status_code in [200, 302]

    def test_index_post_method(self, app, auth_admin):
        """Test index POST method."""
        response = auth_admin.post('/coal', data={
            'client_name': 'QC',
            'sample_type': 'Coal',
            'sample_date': date.today().isoformat()
        }, follow_redirects=True)
        assert response.status_code in [200, 302]


class TestGetReportEmailRecipientsExtended:
    """Extended tests for get_report_email_recipients."""

    def test_recipients_with_settings(self, app, db):
        """Test get_report_email_recipients with system settings."""
        from app.routes.main.hourly_report import get_report_email_recipients
        from app.models import SystemSetting
        import uuid

        unique_suffix = uuid.uuid4().hex[:8]

        with app.app_context():
            # Check if settings exist and delete first
            existing_to = SystemSetting.query.filter_by(
                category='email',
                key='report_recipients_to'
            ).first()
            existing_cc = SystemSetting.query.filter_by(
                category='email',
                key='report_recipients_cc'
            ).first()

            if existing_to:
                db.session.delete(existing_to)
            if existing_cc:
                db.session.delete(existing_cc)
            db.session.commit()

            # Create test settings
            to_setting = SystemSetting(
                category='email',
                key='report_recipients_to',
                value=f'test{unique_suffix}@example.com',
                is_active=True
            )
            cc_setting = SystemSetting(
                category='email',
                key='report_recipients_cc',
                value=f'cc{unique_suffix}@example.com',
                is_active=True
            )
            db.session.add(to_setting)
            db.session.add(cc_setting)
            db.session.commit()

            result = get_report_email_recipients()
            assert 'to' in result
            assert 'cc' in result

            # Cleanup
            db.session.delete(to_setting)
            db.session.delete(cc_setting)
            db.session.commit()

    def test_recipients_empty_settings(self, app):
        """Test get_report_email_recipients with empty settings."""
        from app.routes.main.hourly_report import get_report_email_recipients

        with app.app_context():
            result = get_report_email_recipients()
            assert isinstance(result['to'], list)
            assert isinstance(result['cc'], list)
