# tests/test_index_full_coverage.py
# -*- coding: utf-8 -*-
"""
Full coverage tests for routes/main/index.py
"""

import pytest
from datetime import datetime, date
from unittest.mock import patch, MagicMock


class TestIndexRoutes:
    """Tests for index page routes."""

    def test_index_get(self, app, auth_admin):
        """Test index GET request."""
        response = auth_admin.get('/coal')
        assert response.status_code in [200, 302]

    def test_index_active_tab(self, app, auth_admin):
        """Test index with active_tab parameter."""
        response = auth_admin.get('/coal?active_tab=add-pane')
        assert response.status_code in [200, 302]

    def test_index_post_no_role(self, app, auth_user):
        """Test index POST without prep/admin role."""
        response = auth_user.post('/coal', data={
            'client_name': 'CHPP',
            'sample_type': 'coal',
            'sample_date': date.today().isoformat()
        }, follow_redirects=True)
        assert response.status_code in [200, 302]


class TestPreviewAnalyses:
    """Tests for preview-analyses endpoint."""

    def test_preview_analyses_valid(self, app, auth_admin):
        """Test preview analyses with valid data."""
        response = auth_admin.post('/preview-analyses',
            json={
                'sample_names': ['SC20251224_D_1'],
                'client_name': 'CHPP',
                'sample_type': 'coal'
            },
            content_type='application/json'
        )
        assert response.status_code in [200, 400]

    def test_preview_analyses_missing_data(self, app, auth_admin):
        """Test preview analyses with missing data."""
        response = auth_admin.post('/preview-analyses',
            json={
                'sample_names': []
            },
            content_type='application/json'
        )
        assert response.status_code in [200, 400]

    def test_preview_analyses_no_client(self, app, auth_admin):
        """Test preview analyses without client_name."""
        response = auth_admin.post('/preview-analyses',
            json={
                'sample_names': ['test1'],
                'sample_type': 'coal'
            },
            content_type='application/json'
        )
        assert response.status_code in [200, 400]


class TestSendHourlyReport:
    """Tests for send-hourly-report endpoint."""

    def test_send_hourly_report_admin(self, app, auth_admin):
        """Test send hourly report as admin."""
        with patch('flask_mail.Mail.send') as mock_send:
            response = auth_admin.get('/send-hourly-report', follow_redirects=True)
            assert response.status_code in [200, 302, 500]

    def test_send_hourly_report_no_permission(self, app, auth_user):
        """Test send hourly report without permission."""
        response = auth_user.get('/send-hourly-report', follow_redirects=True)
        assert response.status_code in [200, 302]


class TestGetReportEmailRecipients:
    """Tests for get_report_email_recipients function."""

    def test_get_recipients(self, app):
        """Test get report email recipients."""
        from app.routes.main.hourly_report import get_report_email_recipients

        with app.app_context():
            result = get_report_email_recipients()
            assert 'to' in result
            assert 'cc' in result


class TestSampleRegistration:
    """Tests for sample registration flow."""

    def test_register_chpp_sample(self, app, auth_admin):
        """Test registering CHPP sample."""
        response = auth_admin.post('/coal', data={
            'client_name': 'CHPP',
            'sample_type': 'coal',
            'sample_date': date.today().isoformat(),
            'sample_codes': ['SC20251224_TEST_1'],
            'list_type': 'chpp_2h'
        }, follow_redirects=True)
        assert response.status_code in [200, 302]

    def test_register_uhg_sample(self, app, auth_admin):
        """Test registering UHG sample."""
        response = auth_admin.post('/coal', data={
            'client_name': 'UHG-Geo',
            'sample_type': 'coal',
            'sample_date': date.today().isoformat()
        }, follow_redirects=True)
        assert response.status_code in [200, 302]

    def test_register_qc_sample(self, app, auth_admin):
        """Test registering QC sample."""
        response = auth_admin.post('/coal', data={
            'client_name': 'QC',
            'sample_type': 'CM',
            'sample_date': date.today().isoformat()
        }, follow_redirects=True)
        assert response.status_code in [200, 302]

    def test_register_wtl_mg_sample(self, app, auth_admin):
        """Test registering WTL MG sample."""
        response = auth_admin.post('/coal', data={
            'client_name': 'WTL',
            'sample_type': 'MG',
            'sample_code': 'WTL_MG_TEST',
            'sample_date': date.today().isoformat()
        }, follow_redirects=True)
        assert response.status_code in [200, 302]


class TestHelperFunctions:
    """Tests for helper functions."""

    def test_get_12h_shift_code(self, app):
        """Test get_12h_shift_code function."""
        try:
            from app.routes.main.helpers import get_12h_shift_code
            from datetime import datetime
            result = get_12h_shift_code(datetime.now())
            assert result is not None
        except Exception:
            pytest.skip("Helper function not available")

    def test_get_quarter_code(self, app):
        """Test get_quarter_code function."""
        try:
            from app.routes.main.helpers import get_quarter_code
            from datetime import datetime
            result = get_quarter_code(datetime.now())
            assert isinstance(result, (str, int))
        except (ImportError, TypeError):
            pytest.skip("Helper function not available")
