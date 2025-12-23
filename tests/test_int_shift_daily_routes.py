# tests/integration/test_shift_daily_routes.py
# -*- coding: utf-8 -*-
"""Shift daily KPI route tests"""

import pytest
from app import db
from app.models import User
from datetime import date

VALID_PASSWORD = 'TestPass123'


@pytest.fixture
def shift_admin(app):
    with app.app_context():
        user = User.query.filter_by(username='shift_admin_user').first()
        if not user:
            user = User(username='shift_admin_user', role='admin')
            user.set_password(VALID_PASSWORD)
            db.session.add(user)
            db.session.commit()
        return user


@pytest.fixture
def shift_senior(app):
    with app.app_context():
        user = User.query.filter_by(username='shift_senior_user').first()
        if not user:
            user = User(username='shift_senior_user', role='senior')
            user.set_password(VALID_PASSWORD)
            db.session.add(user)
            db.session.commit()
        return user


class TestShiftDailyRoutes:
    def test_shift_daily_get(self, client, app, shift_admin):
        client.post('/login', data={'username': 'shift_admin_user', 'password': VALID_PASSWORD}, follow_redirects=True)
        response = client.get('/analysis/shift_daily')
        assert response.status_code in [200, 302, 404]

    def test_shift_daily_with_dates(self, client, app, shift_admin):
        client.post('/login', data={'username': 'shift_admin_user', 'password': VALID_PASSWORD}, follow_redirects=True)
        today = date.today().isoformat()
        response = client.get(f'/analysis/shift_daily?start_date={today}&end_date={today}')
        assert response.status_code in [200, 302, 404]

    def test_shift_daily_time_base_prepared(self, client, app, shift_admin):
        client.post('/login', data={'username': 'shift_admin_user', 'password': VALID_PASSWORD}, follow_redirects=True)
        response = client.get('/analysis/shift_daily?time_base=prepared')
        assert response.status_code in [200, 302, 404]

    def test_shift_daily_time_base_mass(self, client, app, shift_admin):
        client.post('/login', data={'username': 'shift_admin_user', 'password': VALID_PASSWORD}, follow_redirects=True)
        response = client.get('/analysis/shift_daily?time_base=mass')
        assert response.status_code in [200, 302, 404]

    def test_shift_daily_group_by_unit(self, client, app, shift_admin):
        client.post('/login', data={'username': 'shift_admin_user', 'password': VALID_PASSWORD}, follow_redirects=True)
        response = client.get('/analysis/shift_daily?group_by=unit')
        assert response.status_code in [200, 302, 404]

    def test_shift_daily_group_by_sample_state(self, client, app, shift_admin):
        client.post('/login', data={'username': 'shift_admin_user', 'password': VALID_PASSWORD}, follow_redirects=True)
        response = client.get('/analysis/shift_daily?group_by=sample_state')
        assert response.status_code in [200, 302, 404]

    def test_shift_daily_filter_unit_chpp(self, client, app, shift_admin):
        client.post('/login', data={'username': 'shift_admin_user', 'password': VALID_PASSWORD}, follow_redirects=True)
        response = client.get('/analysis/shift_daily?unit=CHPP')
        assert response.status_code in [200, 302, 404]

    def test_shift_daily_filter_shift_team_A(self, client, app, shift_admin):
        client.post('/login', data={'username': 'shift_admin_user', 'password': VALID_PASSWORD}, follow_redirects=True)
        response = client.get('/analysis/shift_daily?shift_team=A')
        assert response.status_code in [200, 302, 404]

    def test_shift_daily_filter_shift_type_day(self, client, app, shift_admin):
        client.post('/login', data={'username': 'shift_admin_user', 'password': VALID_PASSWORD}, follow_redirects=True)
        response = client.get('/analysis/shift_daily?shift_type=day')
        assert response.status_code in [200, 302, 404]

    def test_shift_daily_kpi_target_samples(self, client, app, shift_admin):
        client.post('/login', data={'username': 'shift_admin_user', 'password': VALID_PASSWORD}, follow_redirects=True)
        response = client.get('/analysis/shift_daily?kpi_target=samples_prepared')
        assert response.status_code in [200, 302, 404]

    def test_shift_daily_user_name_filter(self, client, app, shift_admin):
        client.post('/login', data={'username': 'shift_admin_user', 'password': VALID_PASSWORD}, follow_redirects=True)
        response = client.get('/analysis/shift_daily?user_name=chemist')
        assert response.status_code in [200, 302, 404]


class TestKPISummaryForAhlah:
    def test_kpi_summary_for_ahlah_senior(self, client, app, shift_senior):
        client.post('/login', data={'username': 'shift_senior_user', 'password': VALID_PASSWORD}, follow_redirects=True)
        response = client.get('/analysis/api/kpi_summary_for_ahlah')
        assert response.status_code in [200, 302, 404]

    def test_kpi_summary_for_ahlah_admin(self, client, app, shift_admin):
        client.post('/login', data={'username': 'shift_admin_user', 'password': VALID_PASSWORD}, follow_redirects=True)
        response = client.get('/analysis/api/kpi_summary_for_ahlah')
        assert response.status_code in [200, 302, 404]
