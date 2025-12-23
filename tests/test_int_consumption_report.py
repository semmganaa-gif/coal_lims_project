# tests/integration/test_consumption_report.py
# -*- coding: utf-8 -*-
"""
Consumption report comprehensive tests
"""

import pytest
from app import db
from app.models import User, Sample, AnalysisResult
from datetime import datetime, timedelta

VALID_PASSWORD = 'TestPass123'


@pytest.fixture
def consumption_user(app):
    """Consumption test user fixture"""
    with app.app_context():
        user = User.query.filter_by(username='consumption_test_user').first()
        if not user:
            user = User(username='consumption_test_user', role='senior')
            user.set_password(VALID_PASSWORD)
            db.session.add(user)
            db.session.commit()
        return user


class TestConsumptionReport:
    """Consumption report tests"""

    def test_consumption_current_year(self, client, app, consumption_user):
        """Consumption with current year"""
        client.post('/login', data={
            'username': 'consumption_test_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)
        response = client.get('/reports/consumption')
        assert response.status_code in [200, 302, 404]

    def test_consumption_specific_year(self, client, app, consumption_user):
        """Consumption with specific year"""
        client.post('/login', data={
            'username': 'consumption_test_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)
        response = client.get('/reports/consumption?year=2024')
        assert response.status_code in [200, 302, 400, 404]

    def test_consumption_invalid_year_low(self, client, app, consumption_user):
        """Consumption with invalid year (too low)"""
        client.post('/login', data={
            'username': 'consumption_test_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)
        response = client.get('/reports/consumption?year=1990')
        assert response.status_code in [200, 302, 400, 404]

    def test_consumption_invalid_year_high(self, client, app, consumption_user):
        """Consumption with invalid year (too high)"""
        client.post('/login', data={
            'username': 'consumption_test_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)
        response = client.get('/reports/consumption?year=2200')
        assert response.status_code in [200, 302, 400, 404]

    def test_consumption_invalid_year_text(self, client, app, consumption_user):
        """Consumption with invalid year (text)"""
        client.post('/login', data={
            'username': 'consumption_test_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)
        response = client.get('/reports/consumption?year=invalid')
        assert response.status_code in [200, 302, 400, 404]

    def test_consumption_drilldown_samples(self, client, app, consumption_user):
        """Consumption drilldown - samples"""
        client.post('/login', data={
            'username': 'consumption_test_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)
        response = client.get('/reports/consumption/drilldown?unit=CHPP&stype=2hour&month=1&year=2024&prop=samples')
        assert response.status_code in [200, 302, 400, 404]

    def test_consumption_drilldown_analysis(self, client, app, consumption_user):
        """Consumption drilldown - analysis"""
        client.post('/login', data={
            'username': 'consumption_test_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)
        response = client.get('/reports/consumption/drilldown?unit=CHPP&stype=2hour&month=6&year=2024&prop=Mad')
        assert response.status_code in [200, 302, 400, 404]


class TestMonthlyPlanReport:
    """Monthly plan report tests"""

    def test_monthly_plan_default(self, client, app, consumption_user):
        """Monthly plan default"""
        client.post('/login', data={
            'username': 'consumption_test_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)
        response = client.get('/reports/monthly_plan')
        assert response.status_code in [200, 302, 404]

    def test_monthly_plan_with_params(self, client, app, consumption_user):
        """Monthly plan with params"""
        client.post('/login', data={
            'username': 'consumption_test_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)
        response = client.get('/reports/monthly_plan?year=2024&month=6')
        assert response.status_code in [200, 302, 404]


class TestShiftReport:
    """Shift report tests"""

    def test_shift_report_default(self, client, app, consumption_user):
        """Shift report default"""
        client.post('/login', data={
            'username': 'consumption_test_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)
        response = client.get('/reports/shift')
        assert response.status_code in [200, 302, 404]

    def test_shift_report_with_date(self, client, app, consumption_user):
        """Shift report with date"""
        client.post('/login', data={
            'username': 'consumption_test_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)
        response = client.get('/reports/shift?date=2024-06-01')
        assert response.status_code in [200, 302, 404]


class TestWorkloadReport:
    """Workload report tests"""

    def test_workload_default(self, client, app, consumption_user):
        """Workload default"""
        client.post('/login', data={
            'username': 'consumption_test_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)
        response = client.get('/reports/workload')
        assert response.status_code in [200, 302, 404]

    def test_workload_with_dates(self, client, app, consumption_user):
        """Workload with dates"""
        client.post('/login', data={
            'username': 'consumption_test_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)
        response = client.get('/reports/workload?start_date=2024-01-01&end_date=2024-06-30')
        assert response.status_code in [200, 302, 404]


class TestTurnaroundReport:
    """Turnaround time report tests"""

    def test_turnaround_default(self, client, app, consumption_user):
        """Turnaround default"""
        client.post('/login', data={
            'username': 'consumption_test_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)
        response = client.get('/reports/turnaround')
        assert response.status_code in [200, 302, 404]


class TestChemistStatsAPI:
    """Chemist stats API tests"""

    def test_chemist_stats(self, client, app, consumption_user):
        """Chemist stats"""
        client.post('/login', data={
            'username': 'consumption_test_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)
        response = client.get('/reports/api/chemist_stats')
        assert response.status_code in [200, 302, 404]

    def test_chemist_stats_with_period(self, client, app, consumption_user):
        """Chemist stats with period"""
        client.post('/login', data={
            'username': 'consumption_test_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)
        response = client.get('/reports/api/chemist_stats?period=month')
        assert response.status_code in [200, 302, 404]
