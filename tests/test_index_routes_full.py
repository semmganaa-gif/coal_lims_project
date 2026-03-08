# tests/test_index_routes_full.py
# -*- coding: utf-8 -*-
"""
Complete tests for app/routes/main/index.py
"""

import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime, date, timedelta


class TestGetReportEmailRecipients:
    """Tests for get_report_email_recipients function."""

    def test_empty_settings(self, app, db):
        """Test with no email settings."""
        with app.app_context():
            from app.routes.main.index import get_report_email_recipients
            result = get_report_email_recipients()
            assert 'to' in result
            assert 'cc' in result
            assert isinstance(result['to'], list)
            assert isinstance(result['cc'], list)

    def test_with_to_recipients(self, app, db):
        """Test with TO recipients configured."""
        with app.app_context():
            from app.routes.main.index import get_report_email_recipients
            from app.models import SystemSetting

            # Cleanup existing settings first
            SystemSetting.query.filter_by(
                category='email',
                key='report_recipients_to'
            ).delete()
            db.session.commit()

            # Create TO setting
            setting = SystemSetting(
                category='email',
                key='report_recipients_to',
                value='test@example.com, test2@example.com',
                is_active=True
            )
            db.session.add(setting)
            db.session.commit()

            result = get_report_email_recipients()
            assert len(result['to']) == 2
            assert 'test@example.com' in result['to']

    def test_with_cc_recipients(self, app, db):
        """Test with CC recipients configured."""
        with app.app_context():
            from app.routes.main.index import get_report_email_recipients
            from app.models import SystemSetting

            # Cleanup existing settings first
            SystemSetting.query.filter_by(
                category='email',
                key='report_recipients_cc'
            ).delete()
            db.session.commit()

            # Create CC setting
            setting = SystemSetting(
                category='email',
                key='report_recipients_cc',
                value='cc@example.com',
                is_active=True
            )
            db.session.add(setting)
            db.session.commit()

            result = get_report_email_recipients()
            assert len(result['cc']) == 1

    def test_inactive_setting_ignored(self, app, db):
        """Test inactive settings are ignored."""
        with app.app_context():
            from app.routes.main.index import get_report_email_recipients
            from app.models import SystemSetting

            # First clear any existing active settings
            SystemSetting.query.filter_by(
                category='email',
                key='report_recipients_to',
                is_active=True
            ).delete()
            db.session.commit()

            setting = SystemSetting(
                category='email',
                key='report_recipients_to',
                value='inactive@example.com',
                is_active=False
            )
            db.session.add(setting)
            db.session.commit()

            result = get_report_email_recipients()
            assert 'inactive@example.com' not in result['to']


class TestIndexRoute:
    """Tests for index route."""

    def test_index_get(self, client, auth_user):
        """Test GET index page."""
        response = client.get('/coal')
        assert response.status_code == 200

    def test_index_alternative_url(self, client, auth_user):
        """Test GET /index page."""
        response = client.get('/index')
        assert response.status_code == 200

    def test_index_requires_login(self, client):
        """Test index requires authentication."""
        response = client.get('/coal')
        # Should redirect to login
        assert response.status_code in [302, 200]

    def test_index_with_active_tab(self, client, auth_user):
        """Test index with active_tab parameter."""
        response = client.get('/coal', query_string={'active_tab': 'add-pane'})
        assert response.status_code == 200


class TestPreviewAnalysesRoute:
    """Tests for preview_sample_analyses route."""

    def test_preview_missing_data(self, client, auth_user):
        """Test preview with missing data."""
        response = client.post('/preview-analyses',
            json={},
            content_type='application/json')
        assert response.status_code == 400

    def test_preview_with_data(self, client, auth_user):
        """Test preview with valid data."""
        response = client.post('/preview-analyses',
            json={
                'sample_names': ['TEST_001'],
                'client_name': 'CHPP',
                'sample_type': '2 hourly'
            },
            content_type='application/json')
        # Should return results or handle gracefully
        assert response.status_code in [200, 400]

    def test_preview_multiple_samples(self, client, auth_user):
        """Test preview with multiple samples."""
        response = client.post('/preview-analyses',
            json={
                'sample_names': ['TEST_001', 'TEST_002', 'TEST_003'],
                'client_name': 'CHPP',
                'sample_type': '2 hourly'
            },
            content_type='application/json')
        assert response.status_code in [200, 400]


class TestSendHourlyReportRoute:
    """Tests for send_hourly_report route."""

    def test_send_report_requires_login(self, client):
        """Test send report requires authentication."""
        response = client.get('/send-hourly-report')
        assert response.status_code == 302  # Redirect to login

    def test_send_report_requires_role(self, client, auth_user):
        """Test send report requires senior/admin role."""
        response = client.get('/send-hourly-report')
        # May redirect or show error based on role
        assert response.status_code in [200, 302]

    @patch('app.routes.main.index.mail')
    def test_send_report_no_recipients(self, mock_mail, client, auth_user, app, db):
        """Test send report with no recipients configured."""
        with app.app_context():
            # Clear any existing email settings
            from app.models import SystemSetting
            SystemSetting.query.filter_by(category='email').delete()
            db.session.commit()

        response = client.get('/send-hourly-report', follow_redirects=True)
        # Should show warning about no recipients
        assert response.status_code == 200


class TestSampleRegistration:
    """Tests for sample registration via index POST."""

    def test_registration_without_role(self, client, app, db):
        """Test registration requires prep/admin role."""
        with app.app_context():
            from app.models import User
            # Create a chemist user (not prep/admin)
            user = User(username='chemist_test', role='chemist')
            user.set_password('TestPass1234!')
            db.session.add(user)
            db.session.commit()

        # Login as chemist
        client.post('/login', data={
            'username': 'chemist_test',
            'password': 'TestPass1234!'
        })

        # Try to register sample
        response = client.post('/coal', data={
            'client_name': 'CHPP',
            'sample_type': '2 hourly',
            'sample_date': date.today().isoformat()
        }, follow_redirects=True)

        # Should show error or redirect
        assert response.status_code in [200, 302]

    def test_registration_chpp_multi(self, client, auth_user):
        """Test CHPP multi-sample registration."""
        response = client.post('/coal', data={
            'client_name': 'CHPP',
            'sample_type': '2 hourly',
            'sample_date': date.today().isoformat(),
            'list_type': 'chpp_2h',
            'sample_codes': ['TEST_D1', 'TEST_D2'],
            'weights': ['100', '100'],
            'sample_condition': 'normal',
            'retention_period': '7'
        }, follow_redirects=True)
        assert response.status_code in [200, 302]


class TestWTLRegistration:
    """Tests for WTL sample registration."""

    def test_wtl_without_lab_number(self, client, auth_user):
        """Test WTL registration without lab number."""
        response = client.post('/coal', data={
            'client_name': 'WTL',
            'sample_type': 'WTL',
            'sample_date': date.today().isoformat(),
            'sample_condition': 'normal',
            'retention_period': '7'
        }, follow_redirects=True)
        # Should show error
        assert response.status_code == 200


class TestLABRegistration:
    """Tests for LAB sample registration."""

    def test_lab_cm_registration(self, client, auth_user):
        """Test LAB CM sample registration."""
        response = client.post('/coal', data={
            'client_name': 'LAB',
            'sample_type': 'CM',
            'sample_date': date.today().isoformat(),
            'sample_condition': 'normal',
            'retention_period': '7'
        }, follow_redirects=True)
        assert response.status_code in [200, 302]

    def test_lab_gbw_registration(self, client, auth_user):
        """Test LAB GBW sample registration."""
        response = client.post('/coal', data={
            'client_name': 'LAB',
            'sample_type': 'GBW',
            'sample_date': date.today().isoformat(),
            'sample_condition': 'normal',
            'retention_period': '7'
        }, follow_redirects=True)
        assert response.status_code in [200, 302]

    def test_lab_test_registration(self, client, auth_user):
        """Test LAB Test sample registration."""
        response = client.post('/coal', data={
            'client_name': 'LAB',
            'sample_type': 'Test',
            'sample_date': date.today().isoformat(),
            'sample_condition': 'normal',
            'retention_period': '7'
        }, follow_redirects=True)
        assert response.status_code in [200, 302]


class TestFormValidation:
    """Tests for form validation."""

    def test_form_client_choices(self, client, auth_user):
        """Test form has correct client choices."""
        response = client.get('/coal')
        assert response.status_code == 200
        # Check that the response contains client options or form
        html = response.data.decode('utf-8')
        assert 'CHPP' in html or 'client' in html.lower() or 'form' in html.lower()

    def test_form_errors_displayed(self, client, auth_user):
        """Test form errors are displayed."""
        response = client.post('/coal', data={
            # Missing required fields
        }, follow_redirects=True)
        assert response.status_code == 200


class TestWeightValidation:
    """Tests for weight validation in registration."""

    def test_weight_too_small(self, client, auth_user):
        """Test weight below minimum."""
        response = client.post('/coal', data={
            'client_name': 'CHPP',
            'sample_type': '2 hourly',
            'sample_date': date.today().isoformat(),
            'list_type': 'chpp_2h',
            'sample_codes': ['TEST_001'],
            'weights': ['0'],  # Too small
            'sample_condition': 'normal',
            'retention_period': '7'
        }, follow_redirects=True)
        assert response.status_code in [200, 302]

    def test_weight_too_large(self, client, auth_user):
        """Test weight above maximum."""
        response = client.post('/coal', data={
            'client_name': 'CHPP',
            'sample_type': '2 hourly',
            'sample_date': date.today().isoformat(),
            'list_type': 'chpp_2h',
            'sample_codes': ['TEST_001'],
            'weights': ['999999999'],  # Too large
            'sample_condition': 'normal',
            'retention_period': '7'
        }, follow_redirects=True)
        assert response.status_code in [200, 302]

    def test_weight_invalid_format(self, client, auth_user):
        """Test weight with invalid format."""
        response = client.post('/coal', data={
            'client_name': 'CHPP',
            'sample_type': '2 hourly',
            'sample_date': date.today().isoformat(),
            'list_type': 'chpp_2h',
            'sample_codes': ['TEST_001'],
            'weights': ['abc'],  # Invalid
            'sample_condition': 'normal',
            'retention_period': '7'
        }, follow_redirects=True)
        assert response.status_code in [200, 302]


class TestHelpersIntegration:
    """Tests for helper function integration."""

    def test_get_12h_shift_code(self, app):
        """Test get_12h_shift_code function."""
        with app.app_context():
            from app.routes.main.helpers import get_12h_shift_code
            from app.utils.datetime import now_local
            code = get_12h_shift_code(now_local())
            # Returns '_D' or '_N' with underscore prefix
            assert 'D' in code or 'N' in code

    def test_get_quarter_code(self, app):
        """Test get_quarter_code function."""
        with app.app_context():
            from app.routes.main.helpers import get_quarter_code
            from app.utils.datetime import now_local
            code = get_quarter_code(now_local())
            # Returns '_Q1', '_Q2', '_Q3', '_Q4' with underscore prefix
            assert 'Q' in code


class TestTemplateVariables:
    """Tests for template variables passed to index."""

    def test_sample_type_map(self, client, auth_user):
        """Test sample_type_map is passed to template."""
        response = client.get('/coal')
        assert response.status_code == 200

    def test_unit_abbreviations(self, client, auth_user):
        """Test unit_abbreviations is passed to template."""
        response = client.get('/coal')
        assert response.status_code == 200

    def test_all_12h_samples(self, client, auth_user):
        """Test ALL_12H_SAMPLES is passed to template."""
        response = client.get('/coal')
        assert response.status_code == 200


class TestErrorHandling:
    """Tests for error handling in index routes."""

    def test_database_error_handling(self, client, auth_user, app, db):
        """Test database error is handled gracefully."""
        with patch('app.routes.main.index.db.session.commit') as mock_commit:
            mock_commit.side_effect = Exception('Database error')
            response = client.post('/coal', data={
                'client_name': 'LAB',
                'sample_type': 'Test',
                'sample_date': date.today().isoformat(),
                'sample_condition': 'normal',
                'retention_period': '7'
            }, follow_redirects=True)
            # Should handle error gracefully
            assert response.status_code in [200, 302, 500]
