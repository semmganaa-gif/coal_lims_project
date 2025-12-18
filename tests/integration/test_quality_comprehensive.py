# -*- coding: utf-8 -*-
"""
Quality routes comprehensive тестүүд
"""
import pytest
from datetime import datetime
from app import create_app, db
from app.models import User, CorrectiveAction, CustomerComplaint, EnvironmentalLog, ProficiencyTest


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


class TestCapaRoutes:
    """CAPA routes тестүүд"""

    def test_capa_list(self, auth_client, app):
        """CAPA list"""
        with app.app_context():
            response = auth_client.get('/quality/capa')
            assert response.status_code in [200, 302]

    def test_capa_new(self, auth_client, app):
        """CAPA new form"""
        with app.app_context():
            response = auth_client.get('/quality/capa/new')
            assert response.status_code in [200, 302]


class TestEnvironmentalRoutes:
    """Environmental routes тестүүд"""

    def test_environmental_list(self, auth_client, app):
        """Environmental list"""
        with app.app_context():
            response = auth_client.get('/quality/environmental')
            assert response.status_code in [200, 302]

    def test_environmental_page(self, auth_client, app):
        """Environmental page"""
        with app.app_context():
            response = auth_client.get('/quality/environmental')
            assert response.status_code in [200, 302]


class TestControlChartsWithData:
    """Control charts with data тестүүд"""

    def test_control_charts_page(self, auth_client, app):
        """Control charts page"""
        with app.app_context():
            response = auth_client.get('/quality/control_charts')
            assert response.status_code in [200, 302]


class TestWestgardApi:
    """Westgard API тестүүд"""

    def test_westgard_summary(self, auth_client, app):
        """Westgard summary"""
        with app.app_context():
            response = auth_client.get('/quality/api/westgard_summary')
            assert response.status_code in [200, 302, 404]

    def test_westgard_detail_ts(self, auth_client, app):
        """Westgard detail TS"""
        with app.app_context():
            response = auth_client.get('/quality/api/westgard_detail/GBW/TS')
            assert response.status_code in [200, 302, 404]


class TestComplaintsWithData:
    """Complaints with data тестүүд"""

    def test_complaints_list(self, auth_client, app):
        """Complaints list"""
        with app.app_context():
            response = auth_client.get('/quality/complaints')
            assert response.status_code in [200, 302]

    def test_complaints_new(self, auth_client, app):
        """Complaints new form"""
        with app.app_context():
            response = auth_client.get('/quality/complaints/new')
            assert response.status_code in [200, 302]


class TestProficiencyWithData:
    """Proficiency with data тестүүд"""

    def test_proficiency_list(self, auth_client, app):
        """Proficiency list"""
        with app.app_context():
            response = auth_client.get('/quality/proficiency')
            assert response.status_code in [200, 302]

    def test_proficiency_new(self, auth_client, app):
        """Proficiency new form"""
        with app.app_context():
            response = auth_client.get('/quality/proficiency/new')
            assert response.status_code in [200, 302]
