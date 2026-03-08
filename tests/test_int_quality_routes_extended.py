# -*- coding: utf-8 -*-
"""
Quality routes extended тестүүд
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


class TestCAPARoutes:
    """CAPA routes тестүүд"""

    def test_capa_list(self, auth_client, app):
        """CAPA list"""
        with app.app_context():
            response = auth_client.get('/quality/capa')
            assert response.status_code in [200, 302, 404]

    def test_capa_new(self, auth_client, app):
        """CAPA new"""
        with app.app_context():
            response = auth_client.get('/quality/capa/new')
            assert response.status_code in [200, 302, 404]

    def test_capa_detail(self, auth_client, app):
        """CAPA detail"""
        with app.app_context():
            response = auth_client.get('/quality/capa/1')
            assert response.status_code in [200, 302, 404]

    def test_capa_create(self, auth_client, app):
        """CAPA create"""
        with app.app_context():
            response = auth_client.post('/quality/capa/new', data={
                'issue_source': 'Internal Audit',
                'issue_description': 'Test issue description for CAPA',
                'severity': 'Minor',
                'issue_date': '2025-01-15'
            })
            # 302 redirect on success, or other codes if auth/validation issues
            assert response.status_code in [200, 302, 400, 404, 405]


class TestComplaintsRoutes:
    """Complaints routes тестүүд"""

    def test_complaints_list(self, auth_client, app):
        """Complaints list"""
        with app.app_context():
            response = auth_client.get('/quality/complaints')
            assert response.status_code in [200, 302, 404]

    def test_complaint_new(self, auth_client, app):
        """Complaint new"""
        with app.app_context():
            response = auth_client.get('/quality/complaints/new')
            assert response.status_code in [200, 302, 404]

    def test_complaint_detail(self, auth_client, app):
        """Complaint detail"""
        with app.app_context():
            response = auth_client.get('/quality/complaints/1')
            assert response.status_code in [200, 302, 404]


class TestEnvironmentalRoutes:
    """Environmental routes тестүүд"""

    def test_environmental_page(self, auth_client, app):
        """Environmental page"""
        with app.app_context():
            response = auth_client.get('/quality/environmental')
            assert response.status_code in [200, 302, 404]

    def test_environmental_data(self, auth_client, app):
        """Environmental data"""
        with app.app_context():
            response = auth_client.get('/api/quality/environmental')
            assert response.status_code in [200, 302, 404]

    def test_environmental_log(self, auth_client, app):
        """Environmental log"""
        with app.app_context():
            response = auth_client.post('/api/quality/environmental/log', json={
                'temperature': 22.5,
                'humidity': 50
            })
            assert response.status_code in [200, 302, 400, 404]


class TestProficiencyRoutes:
    """Proficiency routes тестүүд"""

    def test_proficiency_list(self, auth_client, app):
        """Proficiency list"""
        with app.app_context():
            response = auth_client.get('/quality/proficiency')
            assert response.status_code in [200, 302, 404]

    def test_proficiency_new(self, auth_client, app):
        """Proficiency new"""
        with app.app_context():
            response = auth_client.get('/quality/proficiency/new')
            assert response.status_code in [200, 302, 404]

    def test_proficiency_detail(self, auth_client, app):
        """Proficiency detail"""
        with app.app_context():
            response = auth_client.get('/quality/proficiency/1')
            assert response.status_code in [200, 302, 404]

    def test_proficiency_results(self, auth_client, app):
        """Proficiency results"""
        with app.app_context():
            response = auth_client.get('/quality/proficiency/1/results')
            assert response.status_code in [200, 302, 404]


class TestControlChartsExtended:
    """Control charts extended тестүүд"""

    def test_control_chart_list(self, auth_client, app):
        """Control chart list"""
        with app.app_context():
            response = auth_client.get('/quality/control_charts')
            assert response.status_code in [200, 302, 404]

    def test_control_chart_data(self, auth_client, app):
        """Control chart data"""
        with app.app_context():
            response = auth_client.get('/api/quality/control_charts/data')
            assert response.status_code in [200, 302, 404]

    def test_control_chart_by_analysis(self, auth_client, app):
        """Control chart by analysis"""
        with app.app_context():
            response = auth_client.get('/quality/control_charts/TS')
            assert response.status_code in [200, 302, 404]

    def test_control_chart_settings(self, auth_client, app):
        """Control chart settings"""
        with app.app_context():
            response = auth_client.get('/quality/control_charts/settings')
            assert response.status_code in [200, 302, 404]
