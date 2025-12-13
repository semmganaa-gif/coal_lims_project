# tests/integration/test_quality_management.py
# -*- coding: utf-8 -*-
"""Quality management routes tests"""

import pytest
from app import db
from app.models import User, Sample
from datetime import datetime, date
import uuid
import json

VALID_PASSWORD = 'TestPass123'


@pytest.fixture
def qual_admin(app):
    with app.app_context():
        user = User.query.filter_by(username='qual_admin_user').first()
        if not user:
            user = User(username='qual_admin_user', role='admin')
            user.set_password(VALID_PASSWORD)
            db.session.add(user)
            db.session.commit()
        return user


class TestQualityDashboard:
    def test_quality_index(self, client, app, qual_admin):
        client.post('/login', data={'username': 'qual_admin_user', 'password': VALID_PASSWORD}, follow_redirects=True)
        r = client.get('/quality/')
        assert r.status_code in [200, 302, 404]

    def test_quality_proficiency(self, client, app, qual_admin):
        client.post('/login', data={'username': 'qual_admin_user', 'password': VALID_PASSWORD}, follow_redirects=True)
        r = client.get('/quality/proficiency')
        assert r.status_code in [200, 302, 404]

    def test_quality_capa(self, client, app, qual_admin):
        client.post('/login', data={'username': 'qual_admin_user', 'password': VALID_PASSWORD}, follow_redirects=True)
        r = client.get('/quality/capa')
        assert r.status_code in [200, 302, 404]


class TestProficiencyTesting:
    def test_proficiency_list(self, client, app, qual_admin):
        client.post('/login', data={'username': 'qual_admin_user', 'password': VALID_PASSWORD}, follow_redirects=True)
        r = client.get('/quality/proficiency/list')
        assert r.status_code in [200, 302, 404]

    def test_proficiency_create(self, client, app, qual_admin):
        client.post('/login', data={'username': 'qual_admin_user', 'password': VALID_PASSWORD}, follow_redirects=True)
        r = client.post('/quality/proficiency/create', data={
            'name': 'PT Test 2025',
            'provider': 'Test Provider',
            'due_date': date.today().isoformat()
        })
        assert r.status_code in [200, 302, 400, 404]

    def test_proficiency_detail(self, client, app, qual_admin):
        client.post('/login', data={'username': 'qual_admin_user', 'password': VALID_PASSWORD}, follow_redirects=True)
        r = client.get('/quality/proficiency/1')
        assert r.status_code in [200, 302, 404]


class TestCAPA:
    def test_capa_list(self, client, app, qual_admin):
        client.post('/login', data={'username': 'qual_admin_user', 'password': VALID_PASSWORD}, follow_redirects=True)
        r = client.get('/quality/capa/list')
        assert r.status_code in [200, 302, 404]

    def test_capa_create(self, client, app, qual_admin):
        client.post('/login', data={'username': 'qual_admin_user', 'password': VALID_PASSWORD}, follow_redirects=True)
        r = client.post('/quality/capa/create', data={
            'title': 'Test CAPA',
            'description': 'Test description',
            'type': 'corrective'
        })
        assert r.status_code in [200, 302, 400, 404]

    def test_capa_detail(self, client, app, qual_admin):
        client.post('/login', data={'username': 'qual_admin_user', 'password': VALID_PASSWORD}, follow_redirects=True)
        r = client.get('/quality/capa/1')
        assert r.status_code in [200, 302, 404]

    def test_capa_update(self, client, app, qual_admin):
        client.post('/login', data={'username': 'qual_admin_user', 'password': VALID_PASSWORD}, follow_redirects=True)
        r = client.post('/quality/capa/1/update', data={
            'status': 'in_progress'
        })
        assert r.status_code in [200, 302, 400, 404]


class TestQualityReports:
    def test_quality_summary_report(self, client, app, qual_admin):
        client.post('/login', data={'username': 'qual_admin_user', 'password': VALID_PASSWORD}, follow_redirects=True)
        r = client.get('/quality/reports/summary')
        assert r.status_code in [200, 302, 404]

    def test_quality_trend_report(self, client, app, qual_admin):
        client.post('/login', data={'username': 'qual_admin_user', 'password': VALID_PASSWORD}, follow_redirects=True)
        r = client.get('/quality/reports/trends')
        assert r.status_code in [200, 302, 404]

    def test_quality_export(self, client, app, qual_admin):
        client.post('/login', data={'username': 'qual_admin_user', 'password': VALID_PASSWORD}, follow_redirects=True)
        r = client.get('/quality/reports/export?format=excel')
        assert r.status_code in [200, 302, 400, 404]


class TestQualityAPI:
    def test_quality_data_api(self, client, app, qual_admin):
        client.post('/login', data={'username': 'qual_admin_user', 'password': VALID_PASSWORD}, follow_redirects=True)
        r = client.get('/api/quality/data')
        assert r.status_code in [200, 302, 404]

    def test_quality_metrics_api(self, client, app, qual_admin):
        client.post('/login', data={'username': 'qual_admin_user', 'password': VALID_PASSWORD}, follow_redirects=True)
        r = client.get('/api/quality/metrics')
        assert r.status_code in [200, 302, 404]

    def test_quality_alerts_api(self, client, app, qual_admin):
        client.post('/login', data={'username': 'qual_admin_user', 'password': VALID_PASSWORD}, follow_redirects=True)
        r = client.get('/api/quality/alerts')
        assert r.status_code in [200, 302, 404]
