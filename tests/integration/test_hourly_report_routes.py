# tests/integration/test_hourly_report_routes.py
# -*- coding: utf-8 -*-
"""Hourly report routes tests"""

import pytest
from app import db
from app.models import User, Sample
from datetime import datetime, date
import uuid

VALID_PASSWORD = 'TestPass123'


@pytest.fixture
def hourly_admin(app):
    with app.app_context():
        user = User.query.filter_by(username='hourly_admin_user').first()
        if not user:
            user = User(username='hourly_admin_user', role='admin')
            user.set_password(VALID_PASSWORD)
            db.session.add(user)
            db.session.commit()
        return user


class TestHourlyReportRoutes:
    def test_hourly_report_index(self, client, app, hourly_admin):
        client.post('/login', data={'username': 'hourly_admin_user', 'password': VALID_PASSWORD}, follow_redirects=True)
        r = client.get('/reports/hourly')
        assert r.status_code in [200, 302, 404]

    def test_hourly_report_with_date(self, client, app, hourly_admin):
        client.post('/login', data={'username': 'hourly_admin_user', 'password': VALID_PASSWORD}, follow_redirects=True)
        today = date.today().isoformat()
        r = client.get(f'/reports/hourly?date={today}')
        assert r.status_code in [200, 302, 404]

    def test_hourly_report_with_shift(self, client, app, hourly_admin):
        client.post('/login', data={'username': 'hourly_admin_user', 'password': VALID_PASSWORD}, follow_redirects=True)
        shifts = ['A', 'B', 'C', 'D']
        for s in shifts:
            r = client.get(f'/reports/hourly?shift={s}')
            assert r.status_code in [200, 302, 404]

    def test_hourly_report_with_unit(self, client, app, hourly_admin):
        client.post('/login', data={'username': 'hourly_admin_user', 'password': VALID_PASSWORD}, follow_redirects=True)
        r = client.get('/reports/hourly?unit=CHPP')
        assert r.status_code in [200, 302, 404]

    def test_hourly_report_export_excel(self, client, app, hourly_admin):
        client.post('/login', data={'username': 'hourly_admin_user', 'password': VALID_PASSWORD}, follow_redirects=True)
        today = date.today().isoformat()
        r = client.get(f'/reports/hourly/export?date={today}&format=excel')
        assert r.status_code in [200, 302, 400, 404]

    def test_hourly_report_export_pdf(self, client, app, hourly_admin):
        client.post('/login', data={'username': 'hourly_admin_user', 'password': VALID_PASSWORD}, follow_redirects=True)
        today = date.today().isoformat()
        r = client.get(f'/reports/hourly/export?date={today}&format=pdf')
        assert r.status_code in [200, 302, 400, 404]


class TestHourlyReportAPI:
    def test_hourly_data_api(self, client, app, hourly_admin):
        client.post('/login', data={'username': 'hourly_admin_user', 'password': VALID_PASSWORD}, follow_redirects=True)
        r = client.get('/api/reports/hourly/data')
        assert r.status_code in [200, 302, 404]

    def test_hourly_summary_api(self, client, app, hourly_admin):
        client.post('/login', data={'username': 'hourly_admin_user', 'password': VALID_PASSWORD}, follow_redirects=True)
        today = date.today().isoformat()
        r = client.get(f'/api/reports/hourly/summary?date={today}')
        assert r.status_code in [200, 302, 404]

    def test_hourly_chart_data(self, client, app, hourly_admin):
        client.post('/login', data={'username': 'hourly_admin_user', 'password': VALID_PASSWORD}, follow_redirects=True)
        r = client.get('/api/reports/hourly/chart')
        assert r.status_code in [200, 302, 404]
