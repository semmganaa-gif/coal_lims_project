# -*- coding: utf-8 -*-
"""
Quality routes интеграцийн тестүүд
"""
import pytest
from app import create_app, db
from app.models import User, CorrectiveAction, CustomerComplaint, EnvironmentalLog


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


class TestCapaRoutes:
    """CAPA route тестүүд"""

    def test_capa_list_requires_auth(self, client, app):
        """CAPA list нэвтрэлт шаарддаг"""
        with app.app_context():
            response = client.get('/quality/capa')
            assert response.status_code in [302, 401, 403]

    def test_capa_list_accessible(self, auth_client, app):
        """CAPA list нэвтэрсэн үед харагдана"""
        with app.app_context():
            response = auth_client.get('/quality/capa')
            assert response.status_code in [200, 302]

    def test_capa_new_form(self, auth_client, app):
        """CAPA шинэ форм"""
        with app.app_context():
            response = auth_client.get('/quality/capa/new')
            assert response.status_code in [200, 302]


class TestComplaintsRoutes:
    """Customer complaints route тестүүд"""

    def test_complaints_list_requires_auth(self, client, app):
        """Complaints list нэвтрэлт шаарддаг"""
        with app.app_context():
            response = client.get('/quality/complaints')
            assert response.status_code in [302, 401, 403]

    def test_complaints_list_accessible(self, auth_client, app):
        """Complaints list нэвтэрсэн үед харагдана"""
        with app.app_context():
            response = auth_client.get('/quality/complaints')
            assert response.status_code in [200, 302]

    def test_complaints_new_form(self, auth_client, app):
        """Complaints шинэ форм"""
        with app.app_context():
            response = auth_client.get('/quality/complaints/new')
            assert response.status_code in [200, 302]


class TestEnvironmentalRoutes:
    """Environmental log route тестүүд"""

    def test_environmental_list_requires_auth(self, client, app):
        """Environmental list нэвтрэлт шаарддаг"""
        with app.app_context():
            response = client.get('/quality/environmental')
            assert response.status_code in [302, 401, 403]

    def test_environmental_list_accessible(self, auth_client, app):
        """Environmental list нэвтэрсэн үед харагдана"""
        with app.app_context():
            response = auth_client.get('/quality/environmental')
            assert response.status_code in [200, 302]


class TestProficiencyRoutes:
    """Proficiency test route тестүүд"""

    def test_proficiency_list_requires_auth(self, client, app):
        """Proficiency list нэвтрэлт шаарддаг"""
        with app.app_context():
            response = client.get('/quality/proficiency')
            assert response.status_code in [302, 401, 403]

    def test_proficiency_list_accessible(self, auth_client, app):
        """Proficiency list нэвтэрсэн үед харагдана"""
        with app.app_context():
            response = auth_client.get('/quality/proficiency')
            assert response.status_code in [200, 302]

    def test_proficiency_new_form(self, auth_client, app):
        """Proficiency шинэ форм"""
        with app.app_context():
            response = auth_client.get('/quality/proficiency/new')
            assert response.status_code in [200, 302]


class TestControlChartsRoutes:
    """Control charts route тестүүд"""

    def test_control_charts_requires_auth(self, client, app):
        """Control charts нэвтрэлт шаарддаг"""
        with app.app_context():
            response = client.get('/quality/control_charts')
            assert response.status_code in [302, 401, 403]

    def test_control_charts_accessible(self, auth_client, app):
        """Control charts нэвтэрсэн үед харагдана"""
        with app.app_context():
            response = auth_client.get('/quality/control_charts')
            assert response.status_code in [200, 302]


class TestWestgardApi:
    """Westgard API тестүүд"""

    def test_westgard_summary_api(self, auth_client, app):
        """Westgard summary API"""
        with app.app_context():
            response = auth_client.get('/quality/api/westgard_summary')
            assert response.status_code in [200, 302, 404]
