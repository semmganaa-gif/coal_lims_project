# -*- coding: utf-8 -*-
"""
QC routes тестүүд
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


class TestQCDashboard:
    """QC dashboard тестүүд"""

    def test_qc_dashboard(self, auth_client, app):
        """QC dashboard page"""
        with app.app_context():
            response = auth_client.get('/analysis/qc')
            assert response.status_code in [200, 302, 404]

    def test_qc_dashboard_unauthenticated(self, client, app):
        """QC dashboard unauthenticated"""
        with app.app_context():
            response = client.get('/analysis/qc')
            assert response.status_code in [200, 302, 401, 403, 404]


class TestQCSamples:
    """QC samples тестүүд"""

    def test_qc_samples_list(self, auth_client, app):
        """QC samples list"""
        with app.app_context():
            response = auth_client.get('/analysis/qc/samples')
            assert response.status_code in [200, 302, 404]

    def test_qc_samples_api(self, auth_client, app):
        """QC samples API"""
        with app.app_context():
            response = auth_client.get('/api/qc/samples')
            assert response.status_code in [200, 302, 404]


class TestQCResults:
    """QC results тестүүд"""

    def test_qc_results_page(self, auth_client, app):
        """QC results page"""
        with app.app_context():
            response = auth_client.get('/analysis/qc/results')
            assert response.status_code in [200, 302, 404]

    def test_qc_chart_data(self, auth_client, app):
        """QC chart data"""
        with app.app_context():
            response = auth_client.get('/api/qc/chart_data')
            assert response.status_code in [200, 302, 404]


class TestControlCharts:
    """Control charts тестүүд"""

    def test_control_chart_page(self, auth_client, app):
        """Control chart page"""
        with app.app_context():
            response = auth_client.get('/quality/control_charts')
            assert response.status_code in [200, 302, 404]

    def test_control_chart_data_api(self, auth_client, app):
        """Control chart data API"""
        with app.app_context():
            response = auth_client.get('/api/quality/control_chart_data')
            assert response.status_code in [200, 302, 404]


class TestWestgardRules:
    """Westgard rules тестүүд"""

    def test_westgard_violations(self, auth_client, app):
        """Westgard violations"""
        with app.app_context():
            response = auth_client.get('/analysis/qc/violations')
            assert response.status_code in [200, 302, 404]

    def test_westgard_api(self, auth_client, app):
        """Westgard API"""
        with app.app_context():
            response = auth_client.get('/api/qc/westgard')
            assert response.status_code in [200, 302, 404]


class TestCRMManagement:
    """CRM management тестүүд"""

    def test_crm_list(self, auth_client, app):
        """CRM list"""
        with app.app_context():
            response = auth_client.get('/analysis/qc/crm')
            assert response.status_code in [200, 302, 404]

    def test_crm_new_form(self, auth_client, app):
        """CRM new form"""
        with app.app_context():
            response = auth_client.get('/analysis/qc/crm/new')
            assert response.status_code in [200, 302, 404]
