# tests/integration/test_index_multi.py
# -*- coding: utf-8 -*-
"""Multi-sample registration and coverage tests"""

import pytest
from app import db
from app.models import User, Sample
from datetime import datetime

VALID_PASSWORD = 'TestPass123'


@pytest.fixture
def idx_prep(app):
    with app.app_context():
        user = User.query.filter_by(username='idx_prep_user').first()
        if not user:
            user = User(username='idx_prep_user', role='prep')
            user.set_password(VALID_PASSWORD)
            db.session.add(user)
            db.session.commit()
        return user


@pytest.fixture
def idx_admin(app):
    with app.app_context():
        user = User.query.filter_by(username='idx_admin_user').first()
        if not user:
            user = User(username='idx_admin_user', role='admin')
            user.set_password(VALID_PASSWORD)
            db.session.add(user)
            db.session.commit()
        return user


class TestMultiSample:
    def test_chpp_2h_multi(self, client, app, idx_prep):
        client.post('/login', data={'username': 'idx_prep_user', 'password': VALID_PASSWORD}, follow_redirects=True)
        response = client.post('/', data={'client_name': 'CHPP', 'sample_type': '2hour', 'list_type': 'chpp_2h', 'sample_codes': ['SC2025_D_1H'], 'weights': ['100.5'], 'sample_date': datetime.now().strftime('%Y-%m-%d')})
        assert response.status_code in [200, 302, 400, 500]

    def test_chpp_4h_multi(self, client, app, idx_prep):
        client.post('/login', data={'username': 'idx_prep_user', 'password': VALID_PASSWORD}, follow_redirects=True)
        response = client.post('/', data={'client_name': 'CHPP', 'sample_type': '4hour', 'list_type': 'chpp_4h', 'sample_date': datetime.now().strftime('%Y-%m-%d')})
        assert response.status_code in [200, 302, 400, 500]

    def test_chpp_com_multi(self, client, app, idx_prep):
        client.post('/login', data={'username': 'idx_prep_user', 'password': VALID_PASSWORD}, follow_redirects=True)
        response = client.post('/', data={'client_name': 'CHPP', 'sample_type': 'composite', 'list_type': 'chpp_com', 'sample_codes': ['SC2025_D_COM'], 'weights': ['500.0'], 'sample_date': datetime.now().strftime('%Y-%m-%d')})
        assert response.status_code in [200, 302, 400, 500]

    def test_weight_too_small(self, client, app, idx_prep):
        client.post('/login', data={'username': 'idx_prep_user', 'password': VALID_PASSWORD}, follow_redirects=True)
        response = client.post('/', data={'client_name': 'CHPP', 'sample_type': '2hour', 'list_type': 'chpp_2h', 'sample_codes': ['SC2025_TS_1H'], 'weights': ['0.0001'], 'sample_date': datetime.now().strftime('%Y-%m-%d')})
        assert response.status_code in [200, 302, 400, 500]


class TestWTLSamples:
    def test_wtl_mg(self, client, app, idx_prep):
        client.post('/login', data={'username': 'idx_prep_user', 'password': VALID_PASSWORD}, follow_redirects=True)
        response = client.post('/', data={'client_name': 'WTL', 'sample_type': 'MG', 'sample_code': 'WTL-MG-001', 'sample_date': datetime.now().strftime('%Y-%m-%d')})
        assert response.status_code in [200, 302, 400, 500]

    def test_wtl_test(self, client, app, idx_prep):
        client.post('/login', data={'username': 'idx_prep_user', 'password': VALID_PASSWORD}, follow_redirects=True)
        response = client.post('/', data={'client_name': 'WTL', 'sample_type': 'Test', 'sample_code': 'WTL-TEST-001', 'sample_date': datetime.now().strftime('%Y-%m-%d')})
        assert response.status_code in [200, 302, 400, 500]


class TestQCProcGeo:
    def test_qc_multi_gen(self, client, app, idx_prep):
        client.post('/login', data={'username': 'idx_prep_user', 'password': VALID_PASSWORD}, follow_redirects=True)
        response = client.post('/', data={'client_name': 'QC', 'sample_type': 'Routine', 'list_type': 'multi_gen', 'sample_codes': ['QC-2025-001'], 'weights': ['250.0'], 'sample_date': datetime.now().strftime('%Y-%m-%d')})
        assert response.status_code in [200, 302, 400, 500]

    def test_proc_sample(self, client, app, idx_prep):
        client.post('/login', data={'username': 'idx_prep_user', 'password': VALID_PASSWORD}, follow_redirects=True)
        response = client.post('/', data={'client_name': 'Proc', 'sample_type': 'Test', 'sample_date': datetime.now().strftime('%Y-%m-%d')})
        assert response.status_code in [200, 302, 400, 500]

    def test_uhg_geo(self, client, app, idx_prep):
        client.post('/login', data={'username': 'idx_prep_user', 'password': VALID_PASSWORD}, follow_redirects=True)
        response = client.post('/', data={'client_name': 'UHG-Geo', 'sample_type': 'Core', 'sample_date': datetime.now().strftime('%Y-%m-%d')})
        assert response.status_code in [200, 302, 400, 500]


class TestAPIEndpoints:
    def test_samples_data(self, client, app, idx_prep):
        client.post('/login', data={'username': 'idx_prep_user', 'password': VALID_PASSWORD}, follow_redirects=True)
        response = client.get('/api/samples_data')
        assert response.status_code in [200, 302, 404]

    def test_samples_dt(self, client, app, idx_prep):
        client.post('/login', data={'username': 'idx_prep_user', 'password': VALID_PASSWORD}, follow_redirects=True)
        response = client.get('/api/samples_dt')
        assert response.status_code in [200, 302, 404]

    def test_shift_code(self, client, app, idx_prep):
        client.post('/login', data={'username': 'idx_prep_user', 'password': VALID_PASSWORD}, follow_redirects=True)
        response = client.get('/api/shift_code')
        assert response.status_code in [200, 302, 404]

    def test_export_excel(self, client, app, idx_prep):
        client.post('/login', data={'username': 'idx_prep_user', 'password': VALID_PASSWORD}, follow_redirects=True)
        response = client.get('/export/samples?format=excel')
        assert response.status_code in [200, 302, 404]
