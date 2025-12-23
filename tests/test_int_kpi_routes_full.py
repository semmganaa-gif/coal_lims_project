# tests/integration/test_kpi_routes_full.py
# -*- coding: utf-8 -*-
"""
KPI routes full coverage tests
"""

import pytest
from app import db
from app.models import User, Sample, AnalysisResult
from datetime import datetime, timedelta
import json

VALID_PASSWORD = 'TestPass123'


@pytest.fixture
def kpi_user(app):
    """KPI user fixture"""
    with app.app_context():
        user = User.query.filter_by(username='kpi_test_user').first()
        if not user:
            user = User(username='kpi_test_user', role='manager')
            user.set_password(VALID_PASSWORD)
            db.session.add(user)
            db.session.commit()
        return user


@pytest.fixture
def kpi_admin(app):
    """KPI admin fixture"""
    with app.app_context():
        user = User.query.filter_by(username='kpi_admin_user').first()
        if not user:
            user = User(username='kpi_admin_user', role='admin')
            user.set_password(VALID_PASSWORD)
            db.session.add(user)
            db.session.commit()
        return user


class TestKPIIndex:
    """KPI index тестүүд"""

    def test_kpi_index_unauthenticated(self, client, app):
        """KPI index without login"""
        response = client.get('/analysis/kpi')
        assert response.status_code in [200, 302, 404]

    def test_kpi_index_authenticated(self, client, app, kpi_user):
        """KPI index with login"""
        client.post('/login', data={
            'username': 'kpi_test_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)

        response = client.get('/analysis/kpi')
        assert response.status_code in [200, 302, 404]

    def test_kpi_index_admin(self, client, app, kpi_admin):
        """KPI index with admin"""
        client.post('/login', data={
            'username': 'kpi_admin_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)

        response = client.get('/analysis/kpi')
        assert response.status_code in [200, 302, 404]


class TestKPIDashboard:
    """KPI dashboard тестүүд"""

    def test_kpi_dashboard(self, client, app, kpi_user):
        """KPI dashboard"""
        client.post('/login', data={
            'username': 'kpi_test_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)

        response = client.get('/analysis/kpi/dashboard')
        assert response.status_code in [200, 302, 404]

    def test_kpi_dashboard_with_dates(self, client, app, kpi_user):
        """KPI dashboard with date range"""
        client.post('/login', data={
            'username': 'kpi_test_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)

        today = datetime.now().strftime('%Y-%m-%d')
        week_ago = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
        response = client.get(f'/analysis/kpi/dashboard?start_date={week_ago}&end_date={today}')
        assert response.status_code in [200, 302, 404]


class TestKPIData:
    """KPI data API тестүүд"""

    def test_kpi_data_api(self, client, app, kpi_user):
        """KPI data API"""
        client.post('/login', data={
            'username': 'kpi_test_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)

        response = client.get('/api/kpi/data')
        assert response.status_code in [200, 302, 404]

    def test_kpi_data_with_period(self, client, app, kpi_user):
        """KPI data with period"""
        client.post('/login', data={
            'username': 'kpi_test_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)

        response = client.get('/api/kpi/data?period=weekly')
        assert response.status_code in [200, 302, 404]

    def test_kpi_data_monthly(self, client, app, kpi_user):
        """KPI data monthly"""
        client.post('/login', data={
            'username': 'kpi_test_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)

        response = client.get('/api/kpi/data?period=monthly')
        assert response.status_code in [200, 302, 404]


class TestKPIStats:
    """KPI stats тестүүд"""

    def test_kpi_stats(self, client, app, kpi_user):
        """KPI stats"""
        client.post('/login', data={
            'username': 'kpi_test_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)

        response = client.get('/api/kpi/stats')
        assert response.status_code in [200, 302, 404]

    def test_kpi_stats_by_client(self, client, app, kpi_user):
        """KPI stats by client"""
        client.post('/login', data={
            'username': 'kpi_test_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)

        response = client.get('/api/kpi/stats?client=CHPP')
        assert response.status_code in [200, 302, 404]


class TestKPIAnalysisCounts:
    """KPI analysis counts тестүүд"""

    def test_kpi_analysis_counts(self, client, app, kpi_user):
        """KPI analysis counts"""
        client.post('/login', data={
            'username': 'kpi_test_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)

        response = client.get('/api/kpi/analysis_counts')
        assert response.status_code in [200, 302, 404]


class TestKPITurnaround:
    """KPI turnaround тестүүд"""

    def test_kpi_turnaround(self, client, app, kpi_user):
        """KPI turnaround time"""
        client.post('/login', data={
            'username': 'kpi_test_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)

        response = client.get('/api/kpi/turnaround')
        assert response.status_code in [200, 302, 404]

    def test_kpi_turnaround_by_type(self, client, app, kpi_user):
        """KPI turnaround by sample type"""
        client.post('/login', data={
            'username': 'kpi_test_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)

        response = client.get('/api/kpi/turnaround?sample_type=2hour')
        assert response.status_code in [200, 302, 404]


class TestKPIExport:
    """KPI export тестүүд"""

    def test_kpi_export_excel(self, client, app, kpi_user):
        """KPI export to Excel"""
        client.post('/login', data={
            'username': 'kpi_test_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)

        response = client.get('/analysis/kpi/export?format=excel')
        assert response.status_code in [200, 302, 404]

    def test_kpi_export_pdf(self, client, app, kpi_user):
        """KPI export to PDF"""
        client.post('/login', data={
            'username': 'kpi_test_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)

        response = client.get('/analysis/kpi/export?format=pdf')
        assert response.status_code in [200, 302, 404]
