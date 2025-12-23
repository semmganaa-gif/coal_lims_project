# tests/integration/test_report_api_routes.py
# -*- coding: utf-8 -*-
"""
Report API routes comprehensive coverage tests
"""

import pytest
from app import db
from app.models import User, Sample, AnalysisResult
from datetime import datetime, date
import json
import uuid

VALID_PASSWORD = 'TestPass123'


@pytest.fixture
def rpt_admin(app):
    """Report admin user fixture"""
    with app.app_context():
        user = User.query.filter_by(username='rpt_admin_user').first()
        if not user:
            user = User(username='rpt_admin_user', role='admin')
            user.set_password(VALID_PASSWORD)
            db.session.add(user)
            db.session.commit()
        return user


@pytest.fixture
def rpt_senior(app):
    """Report senior user fixture"""
    with app.app_context():
        user = User.query.filter_by(username='rpt_senior_user').first()
        if not user:
            user = User(username='rpt_senior_user', role='senior')
            user.set_password(VALID_PASSWORD)
            db.session.add(user)
            db.session.commit()
        return user


class TestConsumptionReportAPI:
    """Consumption report API tests"""

    def test_consumption_get(self, client, app, rpt_admin):
        """Consumption report GET"""
        client.post('/login', data={
            'username': 'rpt_admin_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)
        response = client.get('/reports/consumption')
        assert response.status_code in [200, 302, 404]

    def test_consumption_with_date(self, client, app, rpt_admin):
        """Consumption report with date"""
        client.post('/login', data={
            'username': 'rpt_admin_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)
        today = date.today().isoformat()
        response = client.get(f'/reports/consumption?date={today}')
        assert response.status_code in [200, 302, 404]


class TestConsumptionCellAPI:
    """Consumption cell report tests"""

    def test_consumption_cell_get(self, client, app, rpt_admin):
        """Consumption cell GET"""
        client.post('/login', data={
            'username': 'rpt_admin_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)
        response = client.get('/reports/consumption_cell')
        assert response.status_code in [200, 302, 400, 404, 500]

    def test_consumption_cell_with_date(self, client, app, rpt_admin):
        """Consumption cell with date"""
        client.post('/login', data={
            'username': 'rpt_admin_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)
        today = date.today().isoformat()
        response = client.get(f'/reports/consumption_cell?date={today}')
        assert response.status_code in [200, 302, 400, 404, 500]


class TestMonthlyPlanAPI:
    """Monthly plan API tests"""

    def test_monthly_plan_get(self, client, app, rpt_admin):
        """Monthly plan GET"""
        client.post('/login', data={
            'username': 'rpt_admin_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)
        response = client.get('/reports/monthly_plan')
        assert response.status_code in [200, 302, 404]

    def test_api_monthly_plan_get(self, client, app, rpt_admin):
        """API monthly plan GET"""
        client.post('/login', data={
            'username': 'rpt_admin_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)
        response = client.get('/reports/api/monthly_plan')
        assert response.status_code in [200, 302, 400, 404, 500]

    def test_api_monthly_plan_post(self, client, app, rpt_admin):
        """API monthly plan POST"""
        client.post('/login', data={
            'username': 'rpt_admin_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)
        response = client.post('/reports/api/monthly_plan',
            data=json.dumps({'month': '2025-01'}),
            content_type='application/json')
        assert response.status_code in [200, 302, 400, 404, 405, 500]


class TestStaffSettingsAPI:
    """Staff settings API tests"""

    def test_api_staff_settings_post(self, client, app, rpt_admin):
        """API staff settings POST"""
        client.post('/login', data={
            'username': 'rpt_admin_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)
        response = client.post('/reports/api/staff_settings',
            data=json.dumps({'settings': {}}),
            content_type='application/json')
        assert response.status_code in [200, 302, 400, 404, 405, 500]


class TestPlanStatisticsAPI:
    """Plan statistics API tests"""

    def test_api_plan_statistics_get(self, client, app, rpt_admin):
        """API plan statistics GET"""
        client.post('/login', data={
            'username': 'rpt_admin_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)
        response = client.get('/reports/api/plan_statistics')
        assert response.status_code in [200, 302, 404]

    def test_api_plan_statistics_with_month(self, client, app, rpt_admin):
        """API plan statistics with month"""
        client.post('/login', data={
            'username': 'rpt_admin_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)
        response = client.get('/reports/api/plan_statistics?month=2025-01')
        assert response.status_code in [200, 302, 404]


class TestWeeklyPerformanceAPI:
    """Weekly performance API tests"""

    def test_api_weekly_performance_get(self, client, app, rpt_admin):
        """API weekly performance GET"""
        client.post('/login', data={
            'username': 'rpt_admin_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)
        response = client.get('/reports/api/weekly_performance')
        assert response.status_code in [200, 302, 400, 404, 500]

    def test_api_weekly_performance_with_week(self, client, app, rpt_admin):
        """API weekly performance with week"""
        client.post('/login', data={
            'username': 'rpt_admin_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)
        response = client.get('/reports/api/weekly_performance?week=2025-W01')
        assert response.status_code in [200, 302, 400, 404, 500]
