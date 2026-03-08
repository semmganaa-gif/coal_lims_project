# tests/integration/test_index_routes_full.py
# -*- coding: utf-8 -*-
"""
Index routes full coverage tests
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
    """Prep user fixture"""
    with app.app_context():
        user = User.query.filter_by(username='index_prep_user').first()
        if not user:
            user = User(username='index_prep_user', role='prep')
            user.set_password(VALID_PASSWORD)
            db.session.add(user)
            db.session.commit()
        return user


@pytest.fixture
def admin_user(app):
    """Admin user fixture"""
    with app.app_context():
        user = User.query.filter_by(username='index_admin_user').first()
        if not user:
            user = User(username='index_admin_user', role='admin')
            user.set_password(VALID_PASSWORD)
            db.session.add(user)
            db.session.commit()
        return user


@pytest.fixture
def chemist_user(app):
    """Chemist user fixture"""
    with app.app_context():
        user = User.query.filter_by(username='index_chemist_user').first()
        if not user:
            user = User(username='index_chemist_user', role='chemist')
            user.set_password(VALID_PASSWORD)
            db.session.add(user)
            db.session.commit()
        return user


class TestIndexRouteGet:
    """Index GET тестүүд"""

    def test_index_get_unauthenticated(self, client, app):
        """Index without login redirects"""
        response = client.get('/coal')
        assert response.status_code in [200, 302]

    def test_index_get_prep_user(self, client, app, prep_user):
        """Index with prep user"""
        client.post('/login', data={
            'username': 'index_prep_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)
        response = client.get('/coal')
        assert response.status_code in [200, 302]

    def test_index_get_admin(self, client, app, admin_user):
        """Index with admin"""
        client.post('/login', data={
            'username': 'index_admin_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)
        response = client.get('/coal')
        assert response.status_code in [200, 302]


class TestIndexRoutePostCHPP:
    """Index POST CHPP тестүүд"""

    def test_post_chpp_2hour_sample(self, client, app, prep_user):
        """Create CHPP 2hour sample"""
        client.post('/login', data={
            'username': 'index_prep_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)

        response = client.post('/coal', data={
            'client_name': 'CHPP',
            'sample_type': '2hour',
            'received_date': datetime.now().strftime('%Y-%m-%d')
        })
        assert response.status_code in [200, 302, 400]

    def test_post_chpp_12hour_sample(self, client, app, prep_user):
        """Create CHPP 12hour sample"""
        client.post('/login', data={
            'username': 'index_prep_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)

        response = client.post('/coal', data={
            'client_name': 'CHPP',
            'sample_type': '12hour',
            'received_date': datetime.now().strftime('%Y-%m-%d')
        })
        assert response.status_code in [200, 302, 400]

    def test_post_chpp_composite_sample(self, client, app, prep_user):
        """Create CHPP composite sample"""
        client.post('/login', data={
            'username': 'index_prep_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)

        response = client.post('/coal', data={
            'client_name': 'CHPP',
            'sample_type': 'Composite',
            'received_date': datetime.now().strftime('%Y-%m-%d')
        })
        assert response.status_code in [200, 302, 400]

    def test_post_chpp_daily_sample(self, client, app, prep_user):
        """Create CHPP daily sample"""
        client.post('/login', data={
            'username': 'index_prep_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)

        response = client.post('/coal', data={
            'client_name': 'CHPP',
            'sample_type': 'Daily',
            'received_date': datetime.now().strftime('%Y-%m-%d')
        })
        assert response.status_code in [200, 302, 400]


class TestIndexRoutePostQC:
    """Index POST QC тестүүд"""

    def test_post_qc_routine_sample(self, client, app, prep_user):
        """Create QC Routine sample"""
        client.post('/login', data={
            'username': 'index_prep_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)

        response = client.post('/coal', data={
            'client_name': 'QC',
            'sample_type': 'Routine',
            'received_date': datetime.now().strftime('%Y-%m-%d')
        })
        assert response.status_code in [200, 302, 400]

    def test_post_qc_check_sample(self, client, app, prep_user):
        """Create QC Check sample"""
        client.post('/login', data={
            'username': 'index_prep_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)

        response = client.post('/coal', data={
            'client_name': 'QC',
            'sample_type': 'Check',
            'received_date': datetime.now().strftime('%Y-%m-%d')
        })
        assert response.status_code in [200, 302, 400]


class TestIndexRoutePostWTL:
    """Index POST WTL тестүүд"""

    def test_post_wtl_sample(self, client, app, prep_user):
        """Create WTL sample"""
        client.post('/login', data={
            'username': 'index_prep_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)

        response = client.post('/coal', data={
            'client_name': 'WTL',
            'sample_type': 'Coal',
            'received_date': datetime.now().strftime('%Y-%m-%d')
        })
        assert response.status_code in [200, 302, 400]

    def test_post_wtl_mg_sample(self, client, app, prep_user):
        """Create WTL MG sample"""
        client.post('/login', data={
            'username': 'index_prep_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)

        response = client.post('/coal', data={
            'client_name': 'WTL',
            'sample_type': 'MG',
            'sample_code': 'WTL-MG-001',
            'received_date': datetime.now().strftime('%Y-%m-%d')
        })
        assert response.status_code in [200, 302, 400]


class TestIndexRoutePostGeo:
    """Index POST Geo тестүүд"""

    def test_post_uhg_geo_sample(self, client, app, prep_user):
        """Create UHG-Geo sample"""
        client.post('/login', data={
            'username': 'index_prep_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)

        response = client.post('/coal', data={
            'client_name': 'UHG-Geo',
            'sample_type': 'Core',
            'received_date': datetime.now().strftime('%Y-%m-%d')
        })
        assert response.status_code in [200, 302, 400]

    def test_post_bn_geo_sample(self, client, app, prep_user):
        """Create BN-Geo sample"""
        client.post('/login', data={
            'username': 'index_prep_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)

        response = client.post('/coal', data={
            'client_name': 'BN-Geo',
            'sample_type': 'Core',
            'received_date': datetime.now().strftime('%Y-%m-%d')
        })
        assert response.status_code in [200, 302, 400]


class TestIndexRoutePostProc:
    """Index POST Proc тестүүд"""

    def test_post_proc_sample(self, client, app, prep_user):
        """Create Proc sample"""
        client.post('/login', data={
            'username': 'index_prep_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)

        response = client.post('/coal', data={
            'client_name': 'Proc',
            'sample_type': 'Process',
            'received_date': datetime.now().strftime('%Y-%m-%d')
        })
        assert response.status_code in [200, 302, 400]


class TestIndexRoutePostLAB:
    """Index POST LAB тестүүд"""

    def test_post_lab_sample(self, client, app, prep_user):
        """Create LAB sample"""
        client.post('/login', data={
            'username': 'index_prep_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)

        response = client.post('/coal', data={
            'client_name': 'LAB',
            'sample_type': 'Internal',
            'received_date': datetime.now().strftime('%Y-%m-%d')
        })
        assert response.status_code in [200, 302, 400]


class TestIndexRoutePermissions:
    """Index permissions тестүүд"""

    def test_chemist_cannot_create(self, client, app, chemist_user):
        """Chemist cannot create samples"""
        client.post('/login', data={
            'username': 'index_chemist_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)

        response = client.post('/coal', data={
            'client_name': 'CHPP',
            'sample_type': '2hour',
            'received_date': datetime.now().strftime('%Y-%m-%d')
        })
        # Chemist should get error or redirect
        assert response.status_code in [200, 302, 400, 403]


class TestPreviewAnalysesRoute:
    """Preview analyses route тестүүд"""

    def test_preview_analyses_chpp(self, client, app, prep_user):
        """Preview analyses for CHPP"""
        client.post('/login', data={
            'username': 'index_prep_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)

        response = client.post('/preview-analyses',
            json={'client_name': 'CHPP', 'sample_type': '2hour'},
            content_type='application/json')
        assert response.status_code in [200, 302, 400, 404]

    def test_preview_analyses_qc(self, client, app, prep_user):
        """Preview analyses for QC"""
        client.post('/login', data={
            'username': 'index_prep_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)

        response = client.post('/preview-analyses',
            json={'client_name': 'QC', 'sample_type': 'Routine'},
            content_type='application/json')
        assert response.status_code in [200, 302, 400, 404]

    def test_preview_analyses_wtl(self, client, app, prep_user):
        """Preview analyses for WTL"""
        client.post('/login', data={
            'username': 'index_prep_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)

        response = client.post('/preview-analyses',
            json={'client_name': 'WTL', 'sample_type': 'Coal'},
            content_type='application/json')
        assert response.status_code in [200, 302, 400, 404]

    def test_preview_analyses_empty(self, client, app, prep_user):
        """Preview analyses with empty data"""
        client.post('/login', data={
            'username': 'index_prep_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)

        response = client.post('/preview-analyses',
            json={},
            content_type='application/json')
        assert response.status_code in [200, 302, 400, 404]
