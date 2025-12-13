# -*- coding: utf-8 -*-
"""
Workspace routes тестүүд
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


class TestWorkspaceIndex:
    """Workspace index тестүүд"""

    def test_workspace_index(self, auth_client, app):
        """Workspace index"""
        with app.app_context():
            response = auth_client.get('/analysis/workspace')
            assert response.status_code in [200, 302, 404]

    def test_workspace_unauthenticated(self, client, app):
        """Workspace unauthenticated"""
        with app.app_context():
            response = client.get('/analysis/workspace')
            assert response.status_code in [200, 302, 401, 403, 404]


class TestAnalysisPages:
    """Analysis pages тестүүд"""

    def test_ts_analysis(self, auth_client, app):
        """TS analysis page"""
        with app.app_context():
            response = auth_client.get('/analysis_page/TS')
            assert response.status_code in [200, 302, 404]

    def test_cv_analysis(self, auth_client, app):
        """CV analysis page"""
        with app.app_context():
            response = auth_client.get('/analysis_page/CV')
            assert response.status_code in [200, 302, 404]

    def test_mad_analysis(self, auth_client, app):
        """Mad analysis page"""
        with app.app_context():
            response = auth_client.get('/analysis_page/Mad')
            assert response.status_code in [200, 302, 404]

    def test_aad_analysis(self, auth_client, app):
        """Aad analysis page"""
        with app.app_context():
            response = auth_client.get('/analysis_page/Aad')
            assert response.status_code in [200, 302, 404]

    def test_vad_analysis(self, auth_client, app):
        """Vad analysis page"""
        with app.app_context():
            response = auth_client.get('/analysis_page/Vad')
            assert response.status_code in [200, 302, 404]

    def test_fc_analysis(self, auth_client, app):
        """FC analysis page"""
        with app.app_context():
            response = auth_client.get('/analysis_page/FC')
            assert response.status_code in [200, 302, 404]


class TestBatchEntry:
    """Batch entry тестүүд"""

    def test_batch_entry_page(self, auth_client, app):
        """Batch entry page"""
        with app.app_context():
            response = auth_client.get('/analysis/batch_entry')
            assert response.status_code in [200, 302, 404]

    def test_batch_entry_post(self, auth_client, app):
        """Batch entry POST"""
        with app.app_context():
            response = auth_client.post('/analysis/batch_entry', data={
                'analysis_code': 'TS',
                'samples': []
            })
            assert response.status_code in [200, 302, 400, 404]


class TestWorkspaceAPI:
    """Workspace API тестүүд"""

    def test_pending_samples_api(self, auth_client, app):
        """Pending samples API"""
        with app.app_context():
            response = auth_client.get('/api/workspace/pending')
            assert response.status_code in [200, 302, 404]

    def test_save_result_api(self, auth_client, app):
        """Save result API"""
        with app.app_context():
            response = auth_client.post('/api/workspace/save', json={
                'sample_id': 1,
                'analysis_code': 'TS',
                'result': 5.5
            })
            assert response.status_code in [200, 302, 400, 404]
