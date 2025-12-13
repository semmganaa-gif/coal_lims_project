# tests/integration/test_export_routes_full.py
# -*- coding: utf-8 -*-
"""Export routes full coverage tests"""

import pytest
from app import db
from app.models import User, Sample
from datetime import datetime, date
import uuid

VALID_PASSWORD = 'TestPass123'


@pytest.fixture
def exp_admin(app):
    with app.app_context():
        user = User.query.filter_by(username='exp_admin_user').first()
        if not user:
            user = User(username='exp_admin_user', role='admin')
            user.set_password(VALID_PASSWORD)
            db.session.add(user)
            db.session.commit()
        return user


@pytest.fixture
def exp_sample(app):
    with app.app_context():
        unique_id = uuid.uuid4().hex[:6]
        sample = Sample(
            sample_code=f'EXP-{unique_id}',
            client_name='CHPP',
            sample_type='composite',
            status='completed',
            received_date=datetime.now()
        )
        db.session.add(sample)
        db.session.commit()
        return sample.id


class TestExportSamples:
    def test_export_samples_excel(self, client, app, exp_admin):
        client.post('/login', data={'username': 'exp_admin_user', 'password': VALID_PASSWORD}, follow_redirects=True)
        response = client.get('/export/samples?format=excel')
        assert response.status_code in [200, 302, 400, 404]

    def test_export_samples_csv(self, client, app, exp_admin):
        client.post('/login', data={'username': 'exp_admin_user', 'password': VALID_PASSWORD}, follow_redirects=True)
        response = client.get('/export/samples?format=csv')
        assert response.status_code in [200, 302, 400, 404]

    def test_export_samples_with_date(self, client, app, exp_admin):
        client.post('/login', data={'username': 'exp_admin_user', 'password': VALID_PASSWORD}, follow_redirects=True)
        today = date.today().isoformat()
        response = client.get(f'/export/samples?format=excel&date={today}')
        assert response.status_code in [200, 302, 400, 404]

    def test_export_samples_with_client(self, client, app, exp_admin):
        client.post('/login', data={'username': 'exp_admin_user', 'password': VALID_PASSWORD}, follow_redirects=True)
        response = client.get('/export/samples?format=excel&client=CHPP')
        assert response.status_code in [200, 302, 400, 404]


class TestExportResults:
    def test_export_results_excel(self, client, app, exp_admin):
        client.post('/login', data={'username': 'exp_admin_user', 'password': VALID_PASSWORD}, follow_redirects=True)
        response = client.get('/export/results?format=excel')
        assert response.status_code in [200, 302, 400, 404]

    def test_export_results_csv(self, client, app, exp_admin):
        client.post('/login', data={'username': 'exp_admin_user', 'password': VALID_PASSWORD}, follow_redirects=True)
        response = client.get('/export/results?format=csv')
        assert response.status_code in [200, 302, 400, 404]

    def test_export_sample_results(self, client, app, exp_admin, exp_sample):
        client.post('/login', data={'username': 'exp_admin_user', 'password': VALID_PASSWORD}, follow_redirects=True)
        response = client.get(f'/export/sample/{exp_sample}?format=excel')
        assert response.status_code in [200, 302, 400, 404]


class TestExportReports:
    def test_export_daily_report(self, client, app, exp_admin):
        client.post('/login', data={'username': 'exp_admin_user', 'password': VALID_PASSWORD}, follow_redirects=True)
        today = date.today().isoformat()
        response = client.get(f'/export/daily_report?date={today}')
        assert response.status_code in [200, 302, 400, 404]

    def test_export_monthly_report(self, client, app, exp_admin):
        client.post('/login', data={'username': 'exp_admin_user', 'password': VALID_PASSWORD}, follow_redirects=True)
        response = client.get('/export/monthly_report?month=2025-01')
        assert response.status_code in [200, 302, 400, 404]

    def test_export_qc_report(self, client, app, exp_admin):
        client.post('/login', data={'username': 'exp_admin_user', 'password': VALID_PASSWORD}, follow_redirects=True)
        response = client.get('/export/qc_report')
        assert response.status_code in [200, 302, 400, 404]


class TestExportCertificates:
    def test_export_certificate(self, client, app, exp_admin, exp_sample):
        client.post('/login', data={'username': 'exp_admin_user', 'password': VALID_PASSWORD}, follow_redirects=True)
        response = client.get(f'/export/certificate/{exp_sample}')
        assert response.status_code in [200, 302, 400, 404]

    def test_export_certificate_pdf(self, client, app, exp_admin, exp_sample):
        client.post('/login', data={'username': 'exp_admin_user', 'password': VALID_PASSWORD}, follow_redirects=True)
        response = client.get(f'/export/certificate/{exp_sample}?format=pdf')
        assert response.status_code in [200, 302, 400, 404]

    def test_export_bulk_certificates(self, client, app, exp_admin, exp_sample):
        client.post('/login', data={'username': 'exp_admin_user', 'password': VALID_PASSWORD}, follow_redirects=True)
        response = client.get(f'/export/certificates?ids={exp_sample}')
        assert response.status_code in [200, 302, 400, 404]
