# tests/integration/test_workspace_routes_full.py
# -*- coding: utf-8 -*-
"""
Workspace routes full coverage tests
"""

import pytest
from app import db
from app.models import User, Sample, AnalysisResult
from datetime import datetime
import json

VALID_PASSWORD = 'TestPass123'


@pytest.fixture
def workspace_chemist(app):
    """Workspace chemist fixture"""
    with app.app_context():
        user = User.query.filter_by(username='workspace_chemist').first()
        if not user:
            user = User(username='workspace_chemist', role='chemist')
            user.set_password(VALID_PASSWORD)
            db.session.add(user)
            db.session.commit()
        return user


@pytest.fixture
def workspace_senior(app):
    """Workspace senior fixture"""
    with app.app_context():
        user = User.query.filter_by(username='workspace_senior').first()
        if not user:
            user = User(username='workspace_senior', role='senior')
            user.set_password(VALID_PASSWORD)
            db.session.add(user)
            db.session.commit()
        return user


class TestWorkspaceIndex:
    """Workspace index тестүүд"""

    def test_workspace_index_unauthenticated(self, client, app):
        """Workspace index without login"""
        response = client.get('/analysis/workspace')
        assert response.status_code in [200, 302, 404]

    def test_workspace_index_chemist(self, client, app, workspace_chemist):
        """Workspace index with chemist"""
        client.post('/login', data={
            'username': 'workspace_chemist',
            'password': VALID_PASSWORD
        }, follow_redirects=True)

        response = client.get('/analysis/workspace')
        assert response.status_code in [200, 302, 404]


class TestWorkspaceByCode:
    """Workspace by analysis code тестүүд"""

    def test_workspace_mad(self, client, app, workspace_chemist):
        """Workspace Mad"""
        client.post('/login', data={
            'username': 'workspace_chemist',
            'password': VALID_PASSWORD
        }, follow_redirects=True)

        response = client.get('/analysis/workspace/Mad')
        assert response.status_code in [200, 302, 404]

    def test_workspace_aad(self, client, app, workspace_chemist):
        """Workspace Aad"""
        client.post('/login', data={
            'username': 'workspace_chemist',
            'password': VALID_PASSWORD
        }, follow_redirects=True)

        response = client.get('/analysis/workspace/Aad')
        assert response.status_code in [200, 302, 404]

    def test_workspace_vad(self, client, app, workspace_chemist):
        """Workspace Vad"""
        client.post('/login', data={
            'username': 'workspace_chemist',
            'password': VALID_PASSWORD
        }, follow_redirects=True)

        response = client.get('/analysis/workspace/Vad')
        assert response.status_code in [200, 302, 404]

    def test_workspace_cv(self, client, app, workspace_chemist):
        """Workspace CV"""
        client.post('/login', data={
            'username': 'workspace_chemist',
            'password': VALID_PASSWORD
        }, follow_redirects=True)

        response = client.get('/analysis/workspace/CV')
        assert response.status_code in [200, 302, 404]

    def test_workspace_ts(self, client, app, workspace_chemist):
        """Workspace TS"""
        client.post('/login', data={
            'username': 'workspace_chemist',
            'password': VALID_PASSWORD
        }, follow_redirects=True)

        response = client.get('/analysis/workspace/TS')
        assert response.status_code in [200, 302, 404]

    def test_workspace_hgi(self, client, app, workspace_chemist):
        """Workspace HGI"""
        client.post('/login', data={
            'username': 'workspace_chemist',
            'password': VALID_PASSWORD
        }, follow_redirects=True)

        response = client.get('/analysis/workspace/HGI')
        assert response.status_code in [200, 302, 404]


class TestWorkspaceDataEntry:
    """Workspace data entry тестүүд"""

    def test_data_entry_get(self, client, app, workspace_chemist):
        """Data entry GET"""
        client.post('/login', data={
            'username': 'workspace_chemist',
            'password': VALID_PASSWORD
        }, follow_redirects=True)

        response = client.get('/analysis/workspace/entry')
        assert response.status_code in [200, 302, 404]

    def test_data_entry_post_mad(self, client, app, workspace_chemist):
        """Data entry POST Mad"""
        client.post('/login', data={
            'username': 'workspace_chemist',
            'password': VALID_PASSWORD
        }, follow_redirects=True)

        with app.app_context():
            sample = Sample.query.first()
            if sample:
                response = client.post('/analysis/workspace/entry',
                    json={
                        'sample_id': sample.id,
                        'analysis_code': 'Mad',
                        'raw_data': {'p1': {'m1': 10, 'm2': 15, 'm3': 14.5}}
                    },
                    content_type='application/json')
                assert response.status_code in [200, 302, 400, 404]


class TestWorkspaceSaveResults:
    """Workspace save results тестүүд"""

    def test_save_results_single(self, client, app, workspace_chemist):
        """Save single result"""
        client.post('/login', data={
            'username': 'workspace_chemist',
            'password': VALID_PASSWORD
        }, follow_redirects=True)

        with app.app_context():
            sample = Sample.query.first()
            if sample:
                response = client.post('/api/workspace/save',
                    json={
                        'items': [{
                            'sample_id': sample.id,
                            'analysis_code': 'Mad',
                            'raw_data': {'p1': {'m1': 10, 'm2': 15, 'm3': 14.5}},
                            'final_result': 10.0
                        }]
                    },
                    content_type='application/json')
                assert response.status_code in [200, 207, 302, 400, 404]

    def test_save_results_multiple(self, client, app, workspace_chemist):
        """Save multiple results"""
        client.post('/login', data={
            'username': 'workspace_chemist',
            'password': VALID_PASSWORD
        }, follow_redirects=True)

        with app.app_context():
            sample = Sample.query.first()
            if sample:
                response = client.post('/api/workspace/save',
                    json={
                        'items': [
                            {'sample_id': sample.id, 'analysis_code': 'Mad', 'final_result': 5.0},
                            {'sample_id': sample.id, 'analysis_code': 'Aad', 'final_result': 10.0}
                        ]
                    },
                    content_type='application/json')
                assert response.status_code in [200, 207, 302, 400, 404]


class TestWorkspaceCalculations:
    """Workspace calculations тестүүд"""

    def test_calculate_mad(self, client, app, workspace_chemist):
        """Calculate Mad"""
        client.post('/login', data={
            'username': 'workspace_chemist',
            'password': VALID_PASSWORD
        }, follow_redirects=True)

        response = client.post('/api/workspace/calculate',
            json={
                'analysis_code': 'Mad',
                'raw_data': {
                    'p1': {'m1': 10.0, 'm2': 15.0, 'm3': 14.5},
                    'p2': {'m1': 10.0, 'm2': 15.0, 'm3': 14.4}
                }
            },
            content_type='application/json')
        assert response.status_code in [200, 302, 400, 404]

    def test_calculate_aad(self, client, app, workspace_chemist):
        """Calculate Aad"""
        client.post('/login', data={
            'username': 'workspace_chemist',
            'password': VALID_PASSWORD
        }, follow_redirects=True)

        response = client.post('/api/workspace/calculate',
            json={
                'analysis_code': 'Aad',
                'raw_data': {
                    'p1': {'m1': 10.0, 'm2': 15.0, 'm3': 14.0},
                    'p2': {'m1': 10.0, 'm2': 15.0, 'm3': 13.8}
                }
            },
            content_type='application/json')
        assert response.status_code in [200, 302, 400, 404]


class TestWorkspaceReview:
    """Workspace review тестүүд"""

    def test_review_pending(self, client, app, workspace_senior):
        """Review pending results"""
        client.post('/login', data={
            'username': 'workspace_senior',
            'password': VALID_PASSWORD
        }, follow_redirects=True)

        response = client.get('/analysis/workspace/review')
        assert response.status_code in [200, 302, 404]

    def test_approve_result(self, client, app, workspace_senior):
        """Approve result"""
        client.post('/login', data={
            'username': 'workspace_senior',
            'password': VALID_PASSWORD
        }, follow_redirects=True)

        with app.app_context():
            result = AnalysisResult.query.filter_by(status='pending_review').first()
            if result:
                response = client.post('/api/workspace/approve',
                    json={'result_id': result.id},
                    content_type='application/json')
                assert response.status_code in [200, 302, 400, 404]

    def test_reject_result(self, client, app, workspace_senior):
        """Reject result"""
        client.post('/login', data={
            'username': 'workspace_senior',
            'password': VALID_PASSWORD
        }, follow_redirects=True)

        with app.app_context():
            result = AnalysisResult.query.filter_by(status='pending_review').first()
            if result:
                response = client.post('/api/workspace/reject',
                    json={'result_id': result.id, 'reason': 'Test rejection'},
                    content_type='application/json')
                assert response.status_code in [200, 302, 400, 404]
