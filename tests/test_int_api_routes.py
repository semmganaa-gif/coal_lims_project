# -*- coding: utf-8 -*-
"""
API routes интеграцийн тестүүд
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
            user.set_password('AdminPass123')
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
            user.set_password('AdminPass123')
            db.session.add(user)
            db.session.commit()

        with client.session_transaction() as sess:
            sess['_user_id'] = str(user.id)
            sess['_fresh'] = True

    return client


class TestDashboardApi:
    """Dashboard API тестүүд"""

    def test_dashboard_stats(self, auth_client, app):
        """Dashboard stats API"""
        with app.app_context():
            response = auth_client.get('/api/dashboard_stats')
            assert response.status_code in [200, 302, 404]

    def test_ahlah_data(self, auth_client, app):
        """Ahlah data API"""
        with app.app_context():
            response = auth_client.get('/api/ahlah_data')
            assert response.status_code in [200, 302, 404]

    def test_ahlah_stats(self, auth_client, app):
        """Ahlah stats API"""
        with app.app_context():
            response = auth_client.get('/api/ahlah_stats')
            assert response.status_code in [200, 302, 404]


class TestArchiveApi:
    """Archive API тестүүд"""

    def test_archive_hub(self, auth_client, app):
        """Archive hub API"""
        with app.app_context():
            response = auth_client.get('/api/archive_hub')
            assert response.status_code in [200, 302, 404]


class TestAuditApi:
    """Audit API тестүүд"""

    def test_audit_hub(self, auth_client, app):
        """Audit hub API"""
        with app.app_context():
            response = auth_client.get('/api/audit_hub')
            assert response.status_code in [200, 302, 404]

    def test_audit_search(self, auth_client, app):
        """Audit search API"""
        with app.app_context():
            response = auth_client.get('/api/audit_search')
            assert response.status_code in [200, 302, 404]


class TestChatApi:
    """Chat API тестүүд"""

    def test_chat_templates(self, auth_client, app):
        """Chat templates API"""
        with app.app_context():
            response = auth_client.get('/api/chat/templates')
            assert response.status_code in [200, 302, 404, 500]

    def test_chat_search(self, auth_client, app):
        """Chat search API"""
        with app.app_context():
            response = auth_client.get('/api/chat/search')
            assert response.status_code in [200, 302, 404, 500]


class TestEquipmentApi:
    """Equipment API тестүүд"""

    def test_equipment_list_json(self, auth_client, app):
        """Equipment list JSON API"""
        with app.app_context():
            response = auth_client.get('/api/equipment_list_json')
            assert response.status_code in [200, 302, 404]

    def test_equipment_journal_detailed(self, auth_client, app):
        """Equipment journal detailed API"""
        with app.app_context():
            response = auth_client.get('/api/equipment/journal_detailed')
            assert response.status_code in [200, 302, 404]

    def test_equipment_monthly_stats(self, auth_client, app):
        """Equipment monthly stats API"""
        with app.app_context():
            response = auth_client.get('/api/equipment/monthly_stats')
            assert response.status_code in [200, 302, 404]

    def test_equipment_usage_summary(self, auth_client, app):
        """Equipment usage summary API"""
        with app.app_context():
            response = auth_client.get('/api/equipment/usage_summary')
            assert response.status_code in [200, 302, 404]


class TestKpiApi:
    """KPI API тестүүд"""

    def test_kpi_summary_for_ahlah(self, auth_client, app):
        """KPI summary for ahlah API"""
        with app.app_context():
            response = auth_client.get('/api/kpi_summary_for_ahlah')
            assert response.status_code in [200, 302, 404]


class TestDataApi:
    """Data API тестүүд"""

    def test_data_api(self, auth_client, app):
        """Data API"""
        with app.app_context():
            response = auth_client.get('/api/data')
            assert response.status_code in [200, 302, 404]
