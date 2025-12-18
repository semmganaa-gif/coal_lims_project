# -*- coding: utf-8 -*-
"""
Page routes интеграцийн тестүүд
"""
import pytest
from app import create_app, db
from app.models import User


@pytest.fixture
def app():
    """Test application fixture"""
    from tests.conftest import TestConfig
    app = create_app(TestConfig)
    app.config['SERVER_NAME'] = 'localhost'

    with app.app_context():
        db.create_all()
        from app.models import User
        if not User.query.filter_by(username='admin').first():
            user = User(username='admin', role='admin')
            user.set_password('Admin123')
            db.session.add(user)
            db.session.commit()

    yield app

    with app.app_context():
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    """Test client fixture"""
    return app.test_client()


@pytest.fixture
def auth_client(app, client):
    """Authenticated client fixture"""
    with app.app_context():
        user = User.query.filter_by(username='admin').first()
        if not user:
            user = User(username='admin', role='admin')
            user.set_password('Admin123')
            db.session.add(user)
            db.session.commit()

        with client.session_transaction() as sess:
            sess['_user_id'] = str(user.id)
            sess['_fresh'] = True

    return client


class TestDashboardPages:
    """Dashboard page тестүүд"""

    def test_index_page(self, auth_client, app):
        """Index хуудас"""
        with app.app_context():
            response = auth_client.get('/')
            assert response.status_code in [200, 302]

    def test_ahlah_dashboard(self, auth_client, app):
        """Ahlah dashboard"""
        with app.app_context():
            response = auth_client.get('/ahlah_dashboard')
            assert response.status_code in [200, 302]

    def test_analytics(self, auth_client, app):
        """Analytics хуудас"""
        with app.app_context():
            response = auth_client.get('/analytics')
            assert response.status_code in [200, 302]


class TestEquipmentPages:
    """Equipment page тестүүд"""

    def test_equipment_api(self, auth_client, app):
        """Equipment API"""
        with app.app_context():
            response = auth_client.get('/api/equipment_list_json')
            assert response.status_code in [200, 302, 404]


class TestSamplePages:
    """Sample page тестүүд"""

    def test_sample_disposal(self, auth_client, app):
        """Sample disposal хуудас"""
        with app.app_context():
            response = auth_client.get('/sample_disposal')
            assert response.status_code in [200, 302]

    def test_delete_selected_samples(self, auth_client, app):
        """Delete selected samples"""
        with app.app_context():
            response = auth_client.post('/delete_selected_samples', json={
                'sample_ids': []
            })
            assert response.status_code in [200, 302, 400, 404]

    def test_dispose_samples(self, auth_client, app):
        """Dispose samples"""
        with app.app_context():
            response = auth_client.post('/dispose_samples', json={
                'sample_ids': []
            })
            assert response.status_code in [200, 302, 400, 404]


class TestStandardsPages:
    """Standards page тестүүд"""

    def test_control_standards(self, auth_client, app):
        """Control standards хуудас"""
        with app.app_context():
            response = auth_client.get('/admin/control_standards')
            assert response.status_code in [200, 302]

    def test_gbw_standards(self, auth_client, app):
        """GBW standards хуудас"""
        with app.app_context():
            response = auth_client.get('/admin/gbw_standards')
            assert response.status_code in [200, 302]

    def test_control_standards_list(self, auth_client, app):
        """Control standards list"""
        with app.app_context():
            response = auth_client.get('/admin/control_standards')
            assert response.status_code in [200, 302]

    def test_gbw_standards_list(self, auth_client, app):
        """GBW standards list"""
        with app.app_context():
            response = auth_client.get('/admin/gbw_standards')
            assert response.status_code in [200, 302]
