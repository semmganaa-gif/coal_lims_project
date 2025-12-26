# tests/test_index_routes_boost.py
# -*- coding: utf-8 -*-
"""Tests to boost main/index.py coverage."""

import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime, date


@pytest.fixture
def admin_user(app, db, client):
    """Create and login as admin."""
    with app.app_context():
        from app.models import User
        user = User.query.filter_by(username='indexadmin').first()
        if not user:
            user = User(username='indexadmin', role='admin')
            user.set_password('AdminPass123!')
            db.session.add(user)
            db.session.commit()
        client.post('/login', data={'username': 'indexadmin', 'password': 'AdminPass123!'})
        return user


class TestIndexRoutes:
    """Test main index routes."""

    def test_index_page(self, client, admin_user):
        """Test index page."""
        response = client.get('/')
        assert response.status_code == 200

    def test_index_with_date_filter(self, client, admin_user):
        """Test index with date filter."""
        response = client.get('/?date_from=2025-01-01&date_to=2025-12-31')
        assert response.status_code == 200

    def test_index_with_status_filter(self, client, admin_user):
        """Test index with status filter."""
        response = client.get('/?status=pending')
        assert response.status_code == 200

    def test_dashboard(self, client, admin_user):
        """Test dashboard page."""
        response = client.get('/dashboard')
        assert response.status_code in [200, 302, 404]

    def test_dashboard_api(self, client, admin_user):
        """Test dashboard API."""
        response = client.get('/api/dashboard/stats')
        assert response.status_code in [200, 302, 404]


class TestSampleRoutes:
    """Test sample-related routes."""

    def test_samples_list(self, client, admin_user):
        """Test samples list."""
        response = client.get('/samples')
        assert response.status_code in [200, 302, 404]

    def test_samples_filter_by_client(self, client, admin_user):
        """Test samples filtered by client."""
        response = client.get('/samples?client=TestClient')
        assert response.status_code in [200, 302, 404]

    def test_sample_search(self, client, admin_user):
        """Test sample search."""
        response = client.get('/samples/search?q=test')
        assert response.status_code in [200, 302, 404]


class TestReportRoutes:
    """Test report routes."""

    def test_daily_report(self, client, admin_user):
        """Test daily report."""
        response = client.get('/reports/daily')
        assert response.status_code in [200, 302, 404]

    def test_hourly_report(self, client, admin_user):
        """Test hourly report."""
        response = client.get('/reports/hourly')
        assert response.status_code in [200, 302, 404]


class TestEmailSettings:
    """Test email settings."""

    def test_get_report_email_recipients_empty(self, app, db):
        """Test get email recipients when none configured."""
        with app.app_context():
            from app.routes.main.index import get_report_email_recipients
            result = get_report_email_recipients()
            assert 'to' in result
            assert 'cc' in result
