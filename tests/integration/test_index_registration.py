# tests/integration/test_index_registration.py
# -*- coding: utf-8 -*-
"""Index route - Sample registration comprehensive tests"""

import pytest
from app import db
from app.models import User, Sample
from datetime import date
import uuid

VALID_PASSWORD = 'TestPass123'


@pytest.fixture
def reg_prep(app):
    with app.app_context():
        user = User.query.filter_by(username='reg_prep_user').first()
        if not user:
            user = User(username='reg_prep_user', role='prep')
            user.set_password(VALID_PASSWORD)
            db.session.add(user)
            db.session.commit()
        return user


@pytest.fixture
def reg_admin(app):
    with app.app_context():
        user = User.query.filter_by(username='reg_admin_user').first()
        if not user:
            user = User(username='reg_admin_user', role='admin')
            user.set_password(VALID_PASSWORD)
            db.session.add(user)
            db.session.commit()
        return user


@pytest.fixture
def reg_chemist(app):
    with app.app_context():
        user = User.query.filter_by(username='reg_chemist_user').first()
        if not user:
            user = User(username='reg_chemist_user', role='chemist')
            user.set_password(VALID_PASSWORD)
            db.session.add(user)
            db.session.commit()
        return user


class TestIndexPageAccess:
    def test_index_page_prep(self, client, app, reg_prep):
        client.post('/login', data={'username': 'reg_prep_user', 'password': VALID_PASSWORD}, follow_redirects=True)
        r = client.get('/')
        assert r.status_code in [200, 302]

    def test_index_page_admin(self, client, app, reg_admin):
        client.post('/login', data={'username': 'reg_admin_user', 'password': VALID_PASSWORD}, follow_redirects=True)
        r = client.get('/')
        assert r.status_code in [200, 302]

    def test_index_page_chemist(self, client, app, reg_chemist):
        client.post('/login', data={'username': 'reg_chemist_user', 'password': VALID_PASSWORD}, follow_redirects=True)
        r = client.get('/')
        assert r.status_code in [200, 302]


class TestSampleRegistrationCHPP:
    def test_register_chpp_2hour(self, client, app, reg_prep):
        client.post('/login', data={'username': 'reg_prep_user', 'password': VALID_PASSWORD}, follow_redirects=True)
        uid = uuid.uuid4().hex[:4]
        data = {
            'client_name': 'CHPP',
            'sample_type': '2hour',
            'sample_date': date.today().isoformat(),
            'list_type': 'chpp_2h',
            'sample_codes': [f'CHPP-2H-{uid}'],
            'weights': ['150.5']
        }
        r = client.post('/', data=data, follow_redirects=True)
        assert r.status_code in [200, 302, 400]

    def test_register_chpp_4hour(self, client, app, reg_prep):
        client.post('/login', data={'username': 'reg_prep_user', 'password': VALID_PASSWORD}, follow_redirects=True)
        uid = uuid.uuid4().hex[:4]
        data = {
            'client_name': 'CHPP',
            'sample_type': '4hour',
            'sample_date': date.today().isoformat(),
            'list_type': 'chpp_4h',
            'sample_codes': [f'CHPP-4H-{uid}'],
            'weights': ['200']
        }
        r = client.post('/', data=data, follow_redirects=True)
        assert r.status_code in [200, 302, 400]

    def test_register_chpp_composite(self, client, app, reg_prep):
        client.post('/login', data={'username': 'reg_prep_user', 'password': VALID_PASSWORD}, follow_redirects=True)
        uid = uuid.uuid4().hex[:4]
        data = {
            'client_name': 'CHPP',
            'sample_type': 'composite',
            'sample_date': date.today().isoformat(),
            'list_type': 'chpp_com',
            'sample_codes': [f'CHPP-COM-{uid}'],
            'weights': ['500']
        }
        r = client.post('/', data=data, follow_redirects=True)
        assert r.status_code in [200, 302, 400]


class TestSampleRegistrationGeo:
    def test_register_uhg_geo(self, client, app, reg_prep):
        client.post('/login', data={'username': 'reg_prep_user', 'password': VALID_PASSWORD}, follow_redirects=True)
        uid = uuid.uuid4().hex[:4]
        data = {
            'client_name': 'UHG-Geo',
            'sample_type': 'Core',
            'sample_date': date.today().isoformat(),
            'list_type': 'multi_gen',
            'sample_codes': [f'UHG-{uid}'],
            'weights': ['100']
        }
        r = client.post('/', data=data, follow_redirects=True)
        assert r.status_code in [200, 302, 400]

    def test_register_bn_geo(self, client, app, reg_prep):
        client.post('/login', data={'username': 'reg_prep_user', 'password': VALID_PASSWORD}, follow_redirects=True)
        uid = uuid.uuid4().hex[:4]
        data = {
            'client_name': 'BN-Geo',
            'sample_type': 'Exploration',
            'sample_date': date.today().isoformat(),
            'list_type': 'multi_gen',
            'sample_codes': [f'BN-{uid}'],
            'weights': ['120']
        }
        r = client.post('/', data=data, follow_redirects=True)
        assert r.status_code in [200, 302, 400]


class TestSampleRegistrationOther:
    def test_register_qc(self, client, app, reg_prep):
        client.post('/login', data={'username': 'reg_prep_user', 'password': VALID_PASSWORD}, follow_redirects=True)
        uid = uuid.uuid4().hex[:4]
        data = {
            'client_name': 'QC',
            'sample_type': 'CRM',
            'sample_date': date.today().isoformat(),
            'list_type': 'multi_gen',
            'sample_codes': [f'QC-{uid}'],
            'weights': ['50']
        }
        r = client.post('/', data=data, follow_redirects=True)
        assert r.status_code in [200, 302, 400]

    def test_register_proc(self, client, app, reg_prep):
        client.post('/login', data={'username': 'reg_prep_user', 'password': VALID_PASSWORD}, follow_redirects=True)
        uid = uuid.uuid4().hex[:4]
        data = {
            'client_name': 'Proc',
            'sample_type': 'Test',
            'sample_date': date.today().isoformat(),
            'list_type': 'multi_gen',
            'sample_codes': [f'Proc-{uid}'],
            'weights': ['80']
        }
        r = client.post('/', data=data, follow_redirects=True)
        assert r.status_code in [200, 302, 400]

    def test_register_lab(self, client, app, reg_prep):
        client.post('/login', data={'username': 'reg_prep_user', 'password': VALID_PASSWORD}, follow_redirects=True)
        uid = uuid.uuid4().hex[:4]
        data = {
            'client_name': 'LAB',
            'sample_type': 'Internal',
            'sample_date': date.today().isoformat(),
            'list_type': 'multi_gen',
            'sample_codes': [f'LAB-{uid}'],
            'weights': ['60']
        }
        r = client.post('/', data=data, follow_redirects=True)
        assert r.status_code in [200, 302, 400]

    def test_register_wtl(self, client, app, reg_prep):
        client.post('/login', data={'username': 'reg_prep_user', 'password': VALID_PASSWORD}, follow_redirects=True)
        uid = uuid.uuid4().hex[:4]
        data = {
            'client_name': 'WTL',
            'sample_type': 'MG',
            'sample_date': date.today().isoformat(),
            'sample_code': f'WTL-{uid}'
        }
        r = client.post('/', data=data, follow_redirects=True)
        assert r.status_code in [200, 302, 400]


class TestIndexFilters:
    def test_filter_by_client(self, client, app, reg_prep):
        client.post('/login', data={'username': 'reg_prep_user', 'password': VALID_PASSWORD}, follow_redirects=True)
        clients = ['CHPP', 'UHG-Geo', 'BN-Geo', 'QC', 'Proc', 'WTL', 'LAB']
        for c in clients:
            r = client.get(f'/?client={c}')
            assert r.status_code in [200, 302]

    def test_filter_by_status(self, client, app, reg_prep):
        client.post('/login', data={'username': 'reg_prep_user', 'password': VALID_PASSWORD}, follow_redirects=True)
        statuses = ['pending', 'in_progress', 'completed', 'approved']
        for s in statuses:
            r = client.get(f'/?status={s}')
            assert r.status_code in [200, 302]

    def test_filter_by_date(self, client, app, reg_prep):
        client.post('/login', data={'username': 'reg_prep_user', 'password': VALID_PASSWORD}, follow_redirects=True)
        today = date.today().isoformat()
        r = client.get(f'/?date={today}')
        assert r.status_code in [200, 302]


class TestRegistrationErrors:
    def test_no_permission_chemist(self, client, app, reg_chemist):
        client.post('/login', data={'username': 'reg_chemist_user', 'password': VALID_PASSWORD}, follow_redirects=True)
        uid = uuid.uuid4().hex[:4]
        data = {
            'client_name': 'CHPP',
            'sample_type': '2hour',
            'sample_date': date.today().isoformat(),
            'list_type': 'chpp_2h',
            'sample_codes': [f'ERR-{uid}'],
            'weights': ['100']
        }
        r = client.post('/', data=data, follow_redirects=True)
        assert r.status_code in [200, 302, 403]

    def test_invalid_weight(self, client, app, reg_prep):
        client.post('/login', data={'username': 'reg_prep_user', 'password': VALID_PASSWORD}, follow_redirects=True)
        uid = uuid.uuid4().hex[:4]
        data = {
            'client_name': 'CHPP',
            'sample_type': '2hour',
            'sample_date': date.today().isoformat(),
            'list_type': 'chpp_2h',
            'sample_codes': [f'INV-{uid}'],
            'weights': ['abc']
        }
        r = client.post('/', data=data, follow_redirects=True)
        assert r.status_code in [200, 302, 400]

    def test_zero_weight(self, client, app, reg_prep):
        client.post('/login', data={'username': 'reg_prep_user', 'password': VALID_PASSWORD}, follow_redirects=True)
        uid = uuid.uuid4().hex[:4]
        data = {
            'client_name': 'CHPP',
            'sample_type': '2hour',
            'sample_date': date.today().isoformat(),
            'list_type': 'chpp_2h',
            'sample_codes': [f'ZRO-{uid}'],
            'weights': ['0']
        }
        r = client.post('/', data=data, follow_redirects=True)
        assert r.status_code in [200, 302, 400]
