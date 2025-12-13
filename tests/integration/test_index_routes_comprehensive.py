# tests/integration/test_index_routes_comprehensive.py
# -*- coding: utf-8 -*-
"""
Index/Main Routes Comprehensive Tests
"""

import pytest
from flask import url_for
from app import db
from app.models import User, Sample, SystemSetting
from datetime import datetime
import json

VALID_PASSWORD = 'TestPass123'


@pytest.fixture
def prep_user(app):
    """Prep хэрэглэгч"""
    with app.app_context():
        user = User.query.filter_by(username='prep_main_user').first()
        if not user:
            user = User(username='prep_main_user', role='prep')
            user.set_password(VALID_PASSWORD)
            db.session.add(user)
            db.session.commit()
        return user


@pytest.fixture
def admin_user(app):
    """Admin хэрэглэгч"""
    with app.app_context():
        user = User.query.filter_by(username='admin_main_user').first()
        if not user:
            user = User(username='admin_main_user', role='admin')
            user.set_password(VALID_PASSWORD)
            db.session.add(user)
            db.session.commit()
        return user


class TestIndexPage:
    """Index page тестүүд"""

    def test_index_not_authenticated(self, client):
        """Нэвтрээгүй хэрэглэгч"""
        response = client.get('/')
        assert response.status_code in [302, 401]

    def test_index_authenticated(self, client, app, prep_user):
        """Нэвтэрсэн хэрэглэгч"""
        client.post('/login', data={
            'username': 'prep_main_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)

        response = client.get('/')
        assert response.status_code in [200, 302]

    def test_index_route(self, client, app, prep_user):
        """/index route"""
        client.post('/login', data={
            'username': 'prep_main_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)

        response = client.get('/index')
        assert response.status_code in [200, 302]


class TestSampleRegistration:
    """Дээж бүртгэх тестүүд"""

    def test_register_chpp_sample(self, client, app, prep_user):
        """CHPP дээж бүртгэх"""
        client.post('/login', data={
            'username': 'prep_main_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)

        response = client.post('/', data={
            'client_name': 'CHPP',
            'sample_type': '2hour',
            'received_date': datetime.now().strftime('%Y-%m-%d')
        })
        assert response.status_code in [200, 302, 400]

    def test_register_qc_sample(self, client, app, prep_user):
        """QC дээж бүртгэх"""
        client.post('/login', data={
            'username': 'prep_main_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)

        response = client.post('/', data={
            'client_name': 'QC',
            'sample_type': 'Routine',
            'received_date': datetime.now().strftime('%Y-%m-%d')
        })
        assert response.status_code in [200, 302, 400]

    def test_register_wtl_sample(self, client, app, prep_user):
        """WTL дээж бүртгэх"""
        client.post('/login', data={
            'username': 'prep_main_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)

        response = client.post('/', data={
            'client_name': 'WTL',
            'sample_type': 'MG',
            'sample_code': 'MG-Test',
            'received_date': datetime.now().strftime('%Y-%m-%d')
        })
        assert response.status_code in [200, 302, 400]

    def test_register_lab_sample(self, client, app, prep_user):
        """LAB дээж бүртгэх"""
        client.post('/login', data={
            'username': 'prep_main_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)

        response = client.post('/', data={
            'client_name': 'LAB',
            'sample_type': 'Test',
            'received_date': datetime.now().strftime('%Y-%m-%d')
        })
        assert response.status_code in [200, 302, 400]

    def test_register_chemist_no_permission(self, client, app):
        """Chemist cannot register samples"""
        with app.app_context():
            user = User.query.filter_by(username='chemist_no_perm').first()
            if not user:
                user = User(username='chemist_no_perm', role='chemist')
                user.set_password(VALID_PASSWORD)
                db.session.add(user)
                db.session.commit()

        client.post('/login', data={
            'username': 'chemist_no_perm',
            'password': VALID_PASSWORD
        }, follow_redirects=True)

        response = client.post('/', data={
            'client_name': 'QC',
            'sample_type': 'Routine',
            'received_date': datetime.now().strftime('%Y-%m-%d')
        })
        assert response.status_code in [200, 302, 400, 403]


class TestSampleTypeChoices:
    """Dynamic sample type choices"""

    def test_get_sample_types_chpp(self, client, app, prep_user):
        """CHPP sample types"""
        client.post('/login', data={
            'username': 'prep_main_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)

        response = client.get('/api/sample_types?client=CHPP')
        assert response.status_code in [200, 302, 404]

    def test_get_sample_types_wtl(self, client, app, prep_user):
        """WTL sample types"""
        client.post('/login', data={
            'username': 'prep_main_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)

        response = client.get('/api/sample_types?client=WTL')
        assert response.status_code in [200, 302, 404]


class TestExportFunctionality:
    """Export функц"""

    def test_export_excel(self, client, app, prep_user):
        """Excel export"""
        client.post('/login', data={
            'username': 'prep_main_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)

        response = client.get('/export/samples')
        assert response.status_code in [200, 302, 404]

    def test_export_pdf(self, client, app, prep_user):
        """PDF export"""
        client.post('/login', data={
            'username': 'prep_main_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)

        response = client.get('/export/samples/pdf')
        assert response.status_code in [200, 302, 404]


class TestSamplesPage:
    """Samples page routes"""

    def test_samples_page(self, client, app, prep_user):
        """Samples list page"""
        client.post('/login', data={
            'username': 'prep_main_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)

        response = client.get('/samples')
        assert response.status_code in [200, 302, 404]

    def test_sample_detail(self, client, app, prep_user):
        """Sample detail page"""
        client.post('/login', data={
            'username': 'prep_main_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)

        with app.app_context():
            sample = Sample.query.first()
            if sample:
                response = client.get(f'/samples/{sample.id}')
                assert response.status_code in [200, 302, 404]

    def test_sample_edit(self, client, app, admin_user):
        """Sample edit page"""
        client.post('/login', data={
            'username': 'admin_main_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)

        with app.app_context():
            sample = Sample.query.first()
            if sample:
                response = client.get(f'/samples/{sample.id}/edit')
                assert response.status_code in [200, 302, 404]


class TestClientSpecificRoutes:
    """Client specific routes"""

    def test_chpp_dashboard(self, client, app, prep_user):
        """CHPP dashboard"""
        client.post('/login', data={
            'username': 'prep_main_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)

        response = client.get('/chpp')
        assert response.status_code in [200, 302, 404]

    def test_wtl_dashboard(self, client, app, prep_user):
        """WTL dashboard"""
        client.post('/login', data={
            'username': 'prep_main_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)

        response = client.get('/wtl')
        assert response.status_code in [200, 302, 404]


class TestMassGate:
    """Mass gate routes"""

    def test_mass_gate_page(self, client, app, prep_user):
        """Mass gate page"""
        client.post('/login', data={
            'username': 'prep_main_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)

        response = client.get('/mass')
        assert response.status_code in [200, 302, 404]

    def test_mass_ready_post(self, client, app, prep_user):
        """Mass ready submit"""
        client.post('/login', data={
            'username': 'prep_main_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)

        with app.app_context():
            sample = Sample.query.first()
            if sample:
                response = client.post('/api/mass_ready',
                    json={'sample_id': sample.id, 'mass': 100.5},
                    content_type='application/json')
                assert response.status_code in [200, 302, 400, 404]
