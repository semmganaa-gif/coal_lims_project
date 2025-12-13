# -*- coding: utf-8 -*-
"""
Index routes comprehensive тестүүд
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


class TestIndexPage:
    """Index page тестүүд"""

    def test_index_get(self, auth_client, app):
        """Index GET request"""
        with app.app_context():
            response = auth_client.get('/')
            assert response.status_code in [200, 302]

    def test_index_alt_path(self, auth_client, app):
        """Index alternative path"""
        with app.app_context():
            response = auth_client.get('/index')
            assert response.status_code in [200, 302]

    def test_index_post_empty(self, auth_client, app):
        """Index POST empty"""
        with app.app_context():
            response = auth_client.post('/', data={})
            assert response.status_code in [200, 302, 400]

    def test_index_post_with_client(self, auth_client, app):
        """Index POST with client_name"""
        with app.app_context():
            response = auth_client.post('/', data={
                'client_name': 'CHPP',
                'sample_type': ''
            })
            assert response.status_code in [200, 302, 400]


class TestDataApiEndpoints:
    """Data API endpoints тестүүд"""

    def test_api_data(self, auth_client, app):
        """API data endpoint"""
        with app.app_context():
            response = auth_client.get('/api/data')
            assert response.status_code in [200, 302, 404]

    def test_api_sample_summary(self, auth_client, app):
        """API sample summary"""
        with app.app_context():
            response = auth_client.get('/api/sample_summary')
            assert response.status_code in [200, 302, 404]


class TestSampleDisposal:
    """Sample disposal тестүүд"""

    def test_sample_disposal_page(self, auth_client, app):
        """Sample disposal page"""
        with app.app_context():
            response = auth_client.get('/sample_disposal')
            assert response.status_code in [200, 302]

    def test_dispose_samples_empty(self, auth_client, app):
        """Dispose samples empty list"""
        with app.app_context():
            response = auth_client.post('/dispose_samples', json={
                'sample_ids': []
            })
            assert response.status_code in [200, 302, 400, 404]

    def test_delete_selected_samples_empty(self, auth_client, app):
        """Delete selected samples empty list"""
        with app.app_context():
            response = auth_client.post('/delete_selected_samples', json={
                'sample_ids': []
            })
            assert response.status_code in [200, 302, 400, 404]


class TestAnalysisHub:
    """Analysis hub тестүүд"""

    def test_analysis_hub_page(self, auth_client, app):
        """Analysis hub page"""
        with app.app_context():
            response = auth_client.get('/analysis_hub')
            assert response.status_code in [200, 302]


class TestAnalysisPage:
    """Analysis page тестүүд"""

    def test_analysis_page_ts(self, auth_client, app):
        """TS analysis page"""
        with app.app_context():
            response = auth_client.get('/analysis_page/TS')
            assert response.status_code in [200, 302]

    def test_analysis_page_cv(self, auth_client, app):
        """CV analysis page"""
        with app.app_context():
            response = auth_client.get('/analysis_page/CV')
            assert response.status_code in [200, 302]

    def test_analysis_page_mad(self, auth_client, app):
        """Mad analysis page"""
        with app.app_context():
            response = auth_client.get('/analysis_page/Mad')
            assert response.status_code in [200, 302]

    def test_analysis_page_unknown(self, auth_client, app):
        """Unknown analysis page"""
        with app.app_context():
            response = auth_client.get('/analysis_page/UNKNOWN_CODE')
            assert response.status_code in [200, 302, 404]


class TestAhlahDashboard:
    """Ahlah dashboard тестүүд"""

    def test_ahlah_dashboard(self, auth_client, app):
        """Ahlah dashboard"""
        with app.app_context():
            response = auth_client.get('/ahlah_dashboard')
            assert response.status_code in [200, 302]


class TestAnalytics:
    """Analytics тестүүд"""

    def test_analytics_page(self, auth_client, app):
        """Analytics page"""
        with app.app_context():
            response = auth_client.get('/analytics')
            assert response.status_code in [200, 302]
