# -*- coding: utf-8 -*-
"""
Main routes интеграцийн тестүүд
"""
import pytest
from app import create_app, db
from app.models import User, Sample


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


class TestAuthRoutes:
    """Authentication route тестүүд"""

    def test_login_page_accessible(self, client, app):
        """Login хуудас нээгддэг"""
        with app.app_context():
            response = client.get('/login')
            assert response.status_code == 200

    def test_login_with_valid_credentials(self, client, app):
        """Зөв мэдээллээр нэвтрэх"""
        with app.app_context():
            user = User.query.filter_by(username='admin').first()
            if not user:
                user = User(username='admin', role='admin')
                user.set_password('Admin123')
                db.session.add(user)
                db.session.commit()

            response = client.post('/login', data={
                'username': 'admin',
                'password': 'Admin123'
            }, follow_redirects=True)
            assert response.status_code == 200

    def test_login_with_invalid_credentials(self, client, app):
        """Буруу мэдээллээр нэвтрэх"""
        with app.app_context():
            response = client.post('/login', data={
                'username': 'nonexistent',
                'password': 'wrongpass'
            })
            assert response.status_code in [200, 302]

    def test_logout(self, auth_client, app):
        """Гарах"""
        with app.app_context():
            response = auth_client.get('/logout', follow_redirects=True)
            assert response.status_code == 200


class TestIndexRoutes:
    """Index route тестүүд"""

    def test_index_requires_auth(self, client, app):
        """Index хуудас нэвтрэлт шаарддаг"""
        with app.app_context():
            response = client.get('/')
            assert response.status_code in [302, 401]

    def test_index_accessible_when_logged_in(self, auth_client, app):
        """Index хуудас нэвтэрсэн үед харагдана"""
        with app.app_context():
            response = auth_client.get('/')
            assert response.status_code in [200, 302]


class TestAdminRoutes:
    """Admin route тестүүд"""

    def test_manage_users_requires_auth(self, client, app):
        """Manage users нэвтрэлт шаарддаг"""
        with app.app_context():
            response = client.get('/admin/manage_users')
            assert response.status_code in [302, 401, 403]

    def test_manage_users_accessible(self, auth_client, app):
        """Manage users нэвтэрсэн үед харагдана"""
        with app.app_context():
            response = auth_client.get('/admin/manage_users')
            assert response.status_code in [200, 302]

    def test_analysis_config_requires_auth(self, client, app):
        """Analysis config нэвтрэлт шаарддаг"""
        with app.app_context():
            response = client.get('/admin/analysis_config')
            assert response.status_code in [302, 401, 403]

    def test_analysis_config_accessible(self, auth_client, app):
        """Analysis config нэвтэрсэн үед харагдана"""
        with app.app_context():
            response = auth_client.get('/admin/analysis_config')
            assert response.status_code in [200, 302]

    def test_control_standards_accessible(self, auth_client, app):
        """Control standards нэвтэрсэн үед харагдана"""
        with app.app_context():
            response = auth_client.get('/admin/control_standards')
            assert response.status_code in [200, 302]

    def test_gbw_standards_accessible(self, auth_client, app):
        """GBW standards нэвтэрсэн үед харагдана"""
        with app.app_context():
            response = auth_client.get('/admin/gbw_standards')
            assert response.status_code in [200, 302]


class TestImportRoutes:
    """Import route тестүүд"""

    def test_import_csv_requires_auth(self, client, app):
        """Import CSV нэвтрэлт шаарддаг"""
        with app.app_context():
            response = client.get('/admin/import/historical_csv')
            assert response.status_code in [302, 401, 403]

    def test_import_csv_accessible(self, auth_client, app):
        """Import CSV нэвтэрсэн үед харагдана"""
        with app.app_context():
            response = auth_client.get('/admin/import/historical_csv')
            assert response.status_code in [200, 302]


class TestErrorHandlers:
    """Error handler тестүүд"""

    def test_404_error(self, auth_client, app):
        """404 алдаа"""
        with app.app_context():
            response = auth_client.get('/nonexistent-page-12345')
            assert response.status_code == 404
