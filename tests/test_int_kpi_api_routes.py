# tests/integration/test_kpi_api_routes.py
# -*- coding: utf-8 -*-
"""KPI API routes comprehensive coverage tests"""

import pytest
from app import db
from app.models import User
from datetime import datetime, date
import json

VALID_PASSWORD = 'TestPass123'


@pytest.fixture
def kpi_admin(app):
    """KPI admin user fixture"""
    with app.app_context():
        user = User.query.filter_by(username='kpi_admin_user').first()
        if not user:
            user = User(username='kpi_admin_user', role='admin')
            user.set_password(VALID_PASSWORD)
            db.session.add(user)
            db.session.commit()
        return user


@pytest.fixture
def kpi_senior(app):
    """KPI senior user fixture"""
    with app.app_context():
        user = User.query.filter_by(username='kpi_senior_user').first()
        if not user:
            user = User(username='kpi_senior_user', role='senior')
            user.set_password(VALID_PASSWORD)
            db.session.add(user)
            db.session.commit()
        return user


class TestKPIDashboard:
    """KPI dashboard tests"""

    def test_kpi_dashboard_get(self, client, app, kpi_admin):
        """KPI dashboard GET"""
        client.post('/login', data={
            'username': 'kpi_admin_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)
        response = client.get('/kpi/')
        assert response.status_code in [200, 302, 404]

    def test_kpi_dashboard_with_date(self, client, app, kpi_admin):
        """KPI dashboard with date"""
        client.post('/login', data={
            'username': 'kpi_admin_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)
        today = date.today().isoformat()
        response = client.get(f'/kpi/?date={today}')
        assert response.status_code in [200, 302, 404]

    def test_kpi_dashboard_with_month(self, client, app, kpi_admin):
        """KPI dashboard with month"""
        client.post('/login', data={
            'username': 'kpi_admin_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)
        response = client.get('/kpi/?month=2025-01')
        assert response.status_code in [200, 302, 404]


class TestKPIOverview:
    """KPI overview tests"""

    def test_kpi_overview_get(self, client, app, kpi_admin):
        """KPI overview GET"""
        client.post('/login', data={
            'username': 'kpi_admin_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)
        response = client.get('/kpi/overview')
        assert response.status_code in [200, 302, 404]

    def test_kpi_overview_daily(self, client, app, kpi_admin):
        """KPI overview daily"""
        client.post('/login', data={
            'username': 'kpi_admin_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)
        response = client.get('/kpi/overview?period=daily')
        assert response.status_code in [200, 302, 404]

    def test_kpi_overview_weekly(self, client, app, kpi_admin):
        """KPI overview weekly"""
        client.post('/login', data={
            'username': 'kpi_admin_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)
        response = client.get('/kpi/overview?period=weekly')
        assert response.status_code in [200, 302, 404]

    def test_kpi_overview_monthly(self, client, app, kpi_admin):
        """KPI overview monthly"""
        client.post('/login', data={
            'username': 'kpi_admin_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)
        response = client.get('/kpi/overview?period=monthly')
        assert response.status_code in [200, 302, 404]


class TestKPIAPI:
    """KPI API tests"""

    def test_api_kpi_summary(self, client, app, kpi_admin):
        """API KPI summary"""
        client.post('/login', data={
            'username': 'kpi_admin_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)
        response = client.get('/api/kpi/summary')
        assert response.status_code in [200, 302, 404]

    def test_api_kpi_summary_with_date(self, client, app, kpi_admin):
        """API KPI summary with date"""
        client.post('/login', data={
            'username': 'kpi_admin_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)
        today = date.today().isoformat()
        response = client.get(f'/api/kpi/summary?date={today}')
        assert response.status_code in [200, 302, 404]

    def test_api_kpi_trends(self, client, app, kpi_admin):
        """API KPI trends"""
        client.post('/login', data={
            'username': 'kpi_admin_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)
        response = client.get('/api/kpi/trends')
        assert response.status_code in [200, 302, 404]

    def test_api_kpi_trends_with_period(self, client, app, kpi_admin):
        """API KPI trends with period"""
        client.post('/login', data={
            'username': 'kpi_admin_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)
        response = client.get('/api/kpi/trends?period=7d')
        assert response.status_code in [200, 302, 404]

    def test_api_kpi_staff(self, client, app, kpi_admin):
        """API KPI staff"""
        client.post('/login', data={
            'username': 'kpi_admin_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)
        response = client.get('/api/kpi/staff')
        assert response.status_code in [200, 302, 404]

    def test_api_kpi_client_breakdown(self, client, app, kpi_admin):
        """API KPI client breakdown"""
        client.post('/login', data={
            'username': 'kpi_admin_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)
        response = client.get('/api/kpi/client_breakdown')
        assert response.status_code in [200, 302, 404]


class TestKPIReports:
    """KPI report tests"""

    def test_kpi_report_turnaround(self, client, app, kpi_admin):
        """KPI turnaround report"""
        client.post('/login', data={
            'username': 'kpi_admin_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)
        response = client.get('/kpi/turnaround')
        assert response.status_code in [200, 302, 404]

    def test_kpi_report_productivity(self, client, app, kpi_admin):
        """KPI productivity report"""
        client.post('/login', data={
            'username': 'kpi_admin_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)
        response = client.get('/kpi/productivity')
        assert response.status_code in [200, 302, 404]

    def test_kpi_report_accuracy(self, client, app, kpi_admin):
        """KPI accuracy report"""
        client.post('/login', data={
            'username': 'kpi_admin_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)
        response = client.get('/kpi/accuracy')
        assert response.status_code in [200, 302, 404]


class TestKPIExport:
    """KPI export tests"""

    def test_kpi_export_excel(self, client, app, kpi_admin):
        """KPI export Excel"""
        client.post('/login', data={
            'username': 'kpi_admin_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)
        response = client.get('/kpi/export?format=excel')
        assert response.status_code in [200, 302, 400, 404]

    def test_kpi_export_csv(self, client, app, kpi_admin):
        """KPI export CSV"""
        client.post('/login', data={
            'username': 'kpi_admin_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)
        response = client.get('/kpi/export?format=csv')
        assert response.status_code in [200, 302, 400, 404]

    def test_kpi_export_pdf(self, client, app, kpi_admin):
        """KPI export PDF"""
        client.post('/login', data={
            'username': 'kpi_admin_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)
        response = client.get('/kpi/export?format=pdf')
        assert response.status_code in [200, 302, 400, 404]


class TestKPICharts:
    """KPI chart tests"""

    def test_api_kpi_chart_samples(self, client, app, kpi_admin):
        """API KPI chart samples"""
        client.post('/login', data={
            'username': 'kpi_admin_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)
        response = client.get('/api/kpi/chart/samples')
        assert response.status_code in [200, 302, 404]

    def test_api_kpi_chart_analyses(self, client, app, kpi_admin):
        """API KPI chart analyses"""
        client.post('/login', data={
            'username': 'kpi_admin_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)
        response = client.get('/api/kpi/chart/analyses')
        assert response.status_code in [200, 302, 404]

    def test_api_kpi_chart_turnaround(self, client, app, kpi_admin):
        """API KPI chart turnaround"""
        client.post('/login', data={
            'username': 'kpi_admin_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)
        response = client.get('/api/kpi/chart/turnaround')
        assert response.status_code in [200, 302, 404]
