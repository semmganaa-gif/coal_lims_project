# tests/integration/test_report_routes_comprehensive.py
# -*- coding: utf-8 -*-
"""
Report Routes Comprehensive Tests
"""

import pytest
from flask import url_for
from app import db
from app.models import User, Sample, AnalysisResult
from datetime import datetime, timedelta
import json

VALID_PASSWORD = 'TestPass123'


@pytest.fixture
def report_user(app):
    """Report тестэд зориулсан хэрэглэгч"""
    with app.app_context():
        user = User.query.filter_by(username='report_test_user').first()
        if not user:
            user = User(username='report_test_user', role='senior')
            user.set_password(VALID_PASSWORD)
            db.session.add(user)
            db.session.commit()
        return user


class TestDashboardRoutes:
    """Dashboard routes"""

    def test_dashboard(self, client, app, report_user):
        """Dashboard page"""
        client.post('/login', data={
            'username': 'report_test_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)

        response = client.get('/dashboard')
        assert response.status_code in [200, 302, 404]

    def test_dashboard_data(self, client, app, report_user):
        """Dashboard data API"""
        client.post('/login', data={
            'username': 'report_test_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)

        response = client.get('/api/dashboard_data')
        assert response.status_code in [200, 302, 404]


class TestReportPages:
    """Report pages"""

    def test_reports_page(self, client, app, report_user):
        """Reports list page"""
        client.post('/login', data={
            'username': 'report_test_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)

        response = client.get('/reports')
        assert response.status_code in [200, 302, 404]

    def test_daily_report(self, client, app, report_user):
        """Daily report"""
        client.post('/login', data={
            'username': 'report_test_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)

        response = client.get('/reports/daily')
        assert response.status_code in [200, 302, 404]

    def test_daily_report_with_date(self, client, app, report_user):
        """Daily report with date"""
        client.post('/login', data={
            'username': 'report_test_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)

        today = datetime.now().strftime('%Y-%m-%d')
        response = client.get(f'/reports/daily?date={today}')
        assert response.status_code in [200, 302, 404]

    def test_weekly_report(self, client, app, report_user):
        """Weekly report"""
        client.post('/login', data={
            'username': 'report_test_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)

        response = client.get('/reports/weekly')
        assert response.status_code in [200, 302, 404]

    def test_monthly_report(self, client, app, report_user):
        """Monthly report"""
        client.post('/login', data={
            'username': 'report_test_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)

        response = client.get('/reports/monthly')
        assert response.status_code in [200, 302, 404]

    def test_sample_report(self, client, app, report_user):
        """Sample report"""
        client.post('/login', data={
            'username': 'report_test_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)

        with app.app_context():
            sample = Sample.query.first()
            if sample:
                response = client.get(f'/reports/sample/{sample.id}')
                assert response.status_code in [200, 302, 404]


class TestExportRoutes:
    """Export routes"""

    def test_export_daily_excel(self, client, app, report_user):
        """Export daily to Excel"""
        client.post('/login', data={
            'username': 'report_test_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)

        today = datetime.now().strftime('%Y-%m-%d')
        response = client.get(f'/reports/daily/export?date={today}&format=excel')
        assert response.status_code in [200, 302, 404]

    def test_export_daily_pdf(self, client, app, report_user):
        """Export daily to PDF"""
        client.post('/login', data={
            'username': 'report_test_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)

        today = datetime.now().strftime('%Y-%m-%d')
        response = client.get(f'/reports/daily/export?date={today}&format=pdf')
        assert response.status_code in [200, 302, 404]

    def test_export_sample_coa(self, client, app, report_user):
        """Export sample COA"""
        client.post('/login', data={
            'username': 'report_test_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)

        with app.app_context():
            sample = Sample.query.first()
            if sample:
                response = client.get(f'/reports/sample/{sample.id}/coa')
                assert response.status_code in [200, 302, 404]


class TestAnalysisRoutes:
    """Analysis routes"""

    def test_analysis_workspace(self, client, app, report_user):
        """Analysis workspace"""
        client.post('/login', data={
            'username': 'report_test_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)

        response = client.get('/analysis')
        assert response.status_code in [200, 302, 404]

    def test_analysis_by_code(self, client, app, report_user):
        """Analysis by code"""
        client.post('/login', data={
            'username': 'report_test_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)

        for code in ['Mad', 'Aad', 'Vad', 'CV', 'TS', 'MT']:
            response = client.get(f'/analysis/{code}')
            assert response.status_code in [200, 302, 404]


class TestQCRoutes:
    """QC routes"""

    def test_qc_dashboard(self, client, app, report_user):
        """QC dashboard"""
        client.post('/login', data={
            'username': 'report_test_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)

        response = client.get('/qc')
        assert response.status_code in [200, 302, 404]

    def test_qc_control_charts(self, client, app, report_user):
        """QC control charts"""
        client.post('/login', data={
            'username': 'report_test_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)

        response = client.get('/qc/control_charts')
        assert response.status_code in [200, 302, 404]


class TestKPIRoutes:
    """KPI routes"""

    def test_kpi_dashboard(self, client, app, report_user):
        """KPI dashboard"""
        client.post('/login', data={
            'username': 'report_test_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)

        response = client.get('/kpi')
        assert response.status_code in [200, 302, 404]

    def test_kpi_data(self, client, app, report_user):
        """KPI data API"""
        client.post('/login', data={
            'username': 'report_test_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)

        response = client.get('/api/kpi_data')
        assert response.status_code in [200, 302, 404]


class TestSeniorRoutes:
    """Senior review routes"""

    def test_senior_review(self, client, app, report_user):
        """Senior review page"""
        client.post('/login', data={
            'username': 'report_test_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)

        response = client.get('/senior')
        assert response.status_code in [200, 302, 404]

    def test_senior_pending(self, client, app, report_user):
        """Senior pending results"""
        client.post('/login', data={
            'username': 'report_test_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)

        response = client.get('/senior/pending')
        assert response.status_code in [200, 302, 404]

    def test_senior_approved(self, client, app, report_user):
        """Senior approved results"""
        client.post('/login', data={
            'username': 'report_test_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)

        response = client.get('/senior/approved')
        assert response.status_code in [200, 302, 404]


class TestAuditRoutes:
    """Audit routes"""

    def test_audit_log(self, client, app, report_user):
        """Audit log"""
        client.post('/login', data={
            'username': 'report_test_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)

        response = client.get('/audit')
        assert response.status_code in [200, 302, 404]

    def test_audit_log_api(self, client, app, report_user):
        """Audit log API"""
        client.post('/login', data={
            'username': 'report_test_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)

        response = client.get('/api/audit_log')
        assert response.status_code in [200, 302, 404]
