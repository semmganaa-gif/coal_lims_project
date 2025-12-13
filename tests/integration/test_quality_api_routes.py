# -*- coding: utf-8 -*-
"""
Quality API routes тестүүд
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


class TestQualityApiRoutes:
    """Quality API routes тестүүд"""

    def test_control_charts(self, auth_client, app):
        """Control charts page"""
        with app.app_context():
            response = auth_client.get('/quality/control_charts')
            assert response.status_code in [200, 302]

    def test_westgard_summary_api(self, auth_client, app):
        """Westgard summary API"""
        with app.app_context():
            response = auth_client.get('/quality/api/westgard_summary')
            assert response.status_code in [200, 302, 404]

    def test_westgard_detail_ts(self, auth_client, app):
        """Westgard detail for TS"""
        with app.app_context():
            response = auth_client.get('/quality/api/westgard_detail/GBW/TS')
            assert response.status_code in [200, 302, 404]

    def test_westgard_detail_mad(self, auth_client, app):
        """Westgard detail for Mad"""
        with app.app_context():
            response = auth_client.get('/quality/api/westgard_detail/GBW/Mad')
            assert response.status_code in [200, 302, 404]

    def test_control_chart_data_ts(self, auth_client, app):
        """Control chart data for TS"""
        with app.app_context():
            response = auth_client.get('/quality/api/control_chart_data/TS')
            assert response.status_code in [200, 302, 404]

    def test_control_chart_data_mad(self, auth_client, app):
        """Control chart data for Mad"""
        with app.app_context():
            response = auth_client.get('/quality/api/control_chart_data/Mad')
            assert response.status_code in [200, 302, 404]


class TestCapaApiRoutes:
    """CAPA API routes тестүүд"""

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


class TestComplaintsApiRoutes:
    """Complaints API routes тестүүд"""

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


class TestProficiencyApiRoutes:
    """Proficiency API routes тестүүд"""

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


class TestEnvironmentalApiRoutes:
    """Environmental API routes тестүүд"""

    def test_environmental_list(self, auth_client, app):
        """Environmental list"""
        with app.app_context():
            response = auth_client.get('/quality/environmental')
            assert response.status_code in [200, 302]
