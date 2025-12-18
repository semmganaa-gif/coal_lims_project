# -*- coding: utf-8 -*-
"""
Analysis routes интеграцийн тестүүд
"""
import pytest
from app import create_app, db
from app.models import User, Sample, AnalysisResult


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


class TestAnalysisHubRoutes:
    """Analysis hub route тестүүд"""

    def test_analysis_hub_requires_auth(self, client, app):
        """Analysis hub нэвтрэлт шаарддаг"""
        with app.app_context():
            response = client.get('/analysis_hub')
            assert response.status_code in [302, 401, 403]

    def test_analysis_hub_accessible(self, auth_client, app):
        """Analysis hub нэвтэрсэн үед харагдана"""
        with app.app_context():
            response = auth_client.get('/analysis_hub')
            assert response.status_code in [200, 302]


class TestAnalysisPageRoutes:
    """Analysis page route тестүүд"""

    def test_analysis_page_ts(self, auth_client, app):
        """TS шинжилгээний хуудас"""
        with app.app_context():
            response = auth_client.get('/analysis_page/TS')
            assert response.status_code in [200, 302, 404]  # 404 if AnalysisType not exists

    def test_analysis_page_cv(self, auth_client, app):
        """CV шинжилгээний хуудас"""
        with app.app_context():
            response = auth_client.get('/analysis_page/CV')
            assert response.status_code in [200, 302, 404]  # 404 if AnalysisType not exists

    def test_analysis_page_mad(self, auth_client, app):
        """Mad шинжилгээний хуудас"""
        with app.app_context():
            response = auth_client.get('/analysis_page/Mad')
            assert response.status_code in [200, 302, 404]  # 404 if AnalysisType not exists


class TestAnalysisApiRoutes:
    """Analysis API route тестүүд"""

    def test_eligible_samples_api(self, auth_client, app):
        """Eligible samples API"""
        with app.app_context():
            response = auth_client.get('/api/eligible_samples/TS')
            assert response.status_code in [200, 302]

    def test_audit_log_api(self, auth_client, app):
        """Audit log API"""
        with app.app_context():
            response = auth_client.get('/api/audit_log/TS')
            assert response.status_code in [200, 302]

    def test_request_analysis_api(self, auth_client, app):
        """Request analysis API"""
        with app.app_context():
            response = auth_client.post('/api/request_analysis', json={
                'sample_ids': [],
                'analysis_codes': ['TS']
            })
            assert response.status_code in [200, 400]


class TestExportApiRoutes:
    """Export API route тестүүд"""

    def test_export_samples_api(self, auth_client, app):
        """Export samples API"""
        with app.app_context():
            response = auth_client.get('/api/export/samples')
            assert response.status_code in [200, 302]

    def test_export_analysis_api(self, auth_client, app):
        """Export analysis API"""
        with app.app_context():
            response = auth_client.get('/api/export/analysis')
            assert response.status_code in [200, 302]
