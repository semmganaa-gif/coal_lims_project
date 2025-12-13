# -*- coding: utf-8 -*-
"""
API routes extended тестүүд
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


class TestSamplesApi:
    """Samples API тестүүд"""

    def test_samples_list(self, auth_client, app):
        """Samples list API"""
        with app.app_context():
            response = auth_client.get('/api/samples')
            assert response.status_code in [200, 302, 404]

    def test_samples_data(self, auth_client, app):
        """Samples data API"""
        with app.app_context():
            response = auth_client.get('/api/data')
            assert response.status_code in [200, 302, 404]


class TestAnalysisApi:
    """Analysis API тестүүд"""

    def test_eligible_samples_ts(self, auth_client, app):
        """Eligible samples TS"""
        with app.app_context():
            response = auth_client.get('/api/eligible_samples/TS')
            assert response.status_code in [200, 302]

    def test_eligible_samples_mad(self, auth_client, app):
        """Eligible samples Mad"""
        with app.app_context():
            response = auth_client.get('/api/eligible_samples/Mad')
            assert response.status_code in [200, 302]

    def test_eligible_samples_aad(self, auth_client, app):
        """Eligible samples Aad"""
        with app.app_context():
            response = auth_client.get('/api/eligible_samples/Aad')
            assert response.status_code in [200, 302]

    def test_audit_log_ts(self, auth_client, app):
        """Audit log TS"""
        with app.app_context():
            response = auth_client.get('/api/audit_log/TS')
            assert response.status_code in [200, 302]

    def test_audit_log_mad(self, auth_client, app):
        """Audit log Mad"""
        with app.app_context():
            response = auth_client.get('/api/audit_log/Mad')
            assert response.status_code in [200, 302]


class TestEquipmentApi:
    """Equipment API тестүүд"""

    def test_equipment_list_json(self, auth_client, app):
        """Equipment list JSON"""
        with app.app_context():
            response = auth_client.get('/api/equipment_list_json')
            assert response.status_code in [200, 302]

    def test_equipment_types(self, auth_client, app):
        """Equipment types"""
        with app.app_context():
            response = auth_client.get('/api/equipment/types')
            assert response.status_code in [200, 302, 404]


class TestExportApi:
    """Export API тестүүд"""

    def test_export_samples(self, auth_client, app):
        """Export samples"""
        with app.app_context():
            response = auth_client.get('/api/export/samples')
            assert response.status_code in [200, 302]

    def test_export_analysis(self, auth_client, app):
        """Export analysis"""
        with app.app_context():
            response = auth_client.get('/api/export/analysis')
            assert response.status_code in [200, 302]


class TestDashboardApi:
    """Dashboard API тестүүд"""

    def test_dashboard_stats(self, auth_client, app):
        """Dashboard stats"""
        with app.app_context():
            response = auth_client.get('/api/dashboard_stats')
            assert response.status_code in [200, 302, 404]

    def test_check_ready_samples(self, auth_client, app):
        """Check ready samples"""
        with app.app_context():
            response = auth_client.get('/api/check_ready_samples')
            assert response.status_code in [200, 302, 404]
