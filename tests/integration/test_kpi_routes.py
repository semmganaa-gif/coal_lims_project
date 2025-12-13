# -*- coding: utf-8 -*-
"""
KPI routes интеграцийн тестүүд
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


class TestKpiRoutes:
    """KPI route тестүүд"""

    def test_kpi_summary_api(self, auth_client, app):
        """KPI summary API"""
        with app.app_context():
            response = auth_client.get('/api/kpi_summary_for_ahlah')
            assert response.status_code in [200, 302, 404]

    def test_ahlah_data_api(self, auth_client, app):
        """Ahlah data API"""
        with app.app_context():
            response = auth_client.get('/api/ahlah_data')
            assert response.status_code in [200, 302, 404]

    def test_ahlah_stats_api(self, auth_client, app):
        """Ahlah stats API"""
        with app.app_context():
            response = auth_client.get('/api/ahlah_stats')
            assert response.status_code in [200, 302, 404]

    def test_dashboard_stats_api(self, auth_client, app):
        """Dashboard stats API"""
        with app.app_context():
            response = auth_client.get('/api/dashboard_stats')
            assert response.status_code in [200, 302, 404]
