# -*- coding: utf-8 -*-
"""
Settings routes comprehensive тестүүд
"""
import pytest
from app import create_app, db
from app.models import User


@pytest.fixture
def app():
    """Test application fixture"""
    app = create_app()
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False
    app.config['SERVER_NAME'] = 'localhost'
    return app


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


class TestUserManagement:
    """User management тестүүд"""

    def test_manage_users(self, auth_client, app):
        """Manage users page"""
        with app.app_context():
            response = auth_client.get('/admin/manage_users')
            assert response.status_code in [200, 302]

    def test_edit_user_nonexistent(self, auth_client, app):
        """Edit nonexistent user"""
        with app.app_context():
            response = auth_client.get('/admin/edit_user/99999')
            assert response.status_code in [200, 302, 404]


class TestAnalysisConfig:
    """Analysis config тестүүд"""

    def test_analysis_config(self, auth_client, app):
        """Analysis config page"""
        with app.app_context():
            response = auth_client.get('/admin/analysis_config')
            assert response.status_code in [200, 302]


class TestControlStandards:
    """Control standards тестүүд"""

    def test_control_standards_list(self, auth_client, app):
        """Control standards list"""
        with app.app_context():
            response = auth_client.get('/admin/control_standards')
            assert response.status_code in [200, 302]


class TestGbwStandards:
    """GBW standards тестүүд"""

    def test_gbw_standards_list(self, auth_client, app):
        """GBW standards list"""
        with app.app_context():
            response = auth_client.get('/admin/gbw_standards')
            assert response.status_code in [200, 302]
