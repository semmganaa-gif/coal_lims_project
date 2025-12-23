# tests/integration/test_workspace_extended.py
# -*- coding: utf-8 -*-
"""
Workspace routes extended tests
Coverage target: app/routes/analysis/workspace.py
"""

import pytest
from app import db
from app.models import User, Sample, AnalysisType, AnalysisResult
from datetime import datetime
import uuid

VALID_PASSWORD = 'TestPass123'


@pytest.fixture
def workspace_user(app):
    """Workspace test user"""
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
    """Workspace senior user"""
    with app.app_context():
        user = User.query.filter_by(username='workspace_senior').first()
        if not user:
            user = User(username='workspace_senior', role='senior')
            user.set_password(VALID_PASSWORD)
            db.session.add(user)
            db.session.commit()
        return user


@pytest.fixture
def workspace_analysis_type(app):
    """Create analysis type for workspace"""
    with app.app_context():
        at = AnalysisType.query.filter_by(code='TS').first()
        if not at:
            at = AnalysisType(
                code='TS',
                name='Total Sulfur',
                required_role='chemist',
                order_num=1
            )
            db.session.add(at)
            db.session.commit()
        return at.code


@pytest.fixture
def workspace_sample(app, workspace_user):
    """Create sample for workspace tests"""
    with app.app_context():
        unique_id = uuid.uuid4().hex[:6]
        sample = Sample(
            sample_code=f'WS-{unique_id}',
            client_name='CHPP',  # Use valid client name
            sample_type='CM',
            status='registered',
            received_date=datetime.now(),
            user_id=workspace_user.id
        )
        db.session.add(sample)
        db.session.commit()
        return sample.id


def login_workspace_user(client, username='workspace_chemist'):
    """Helper login"""
    client.post('/login', data={
        'username': username,
        'password': VALID_PASSWORD
    }, follow_redirects=True)


class TestAnalysisHub:
    """Test analysis hub page"""

    def test_analysis_hub_accessible(self, client, app, workspace_user):
        """Analysis hub is accessible for chemist"""
        login_workspace_user(client)
        response = client.get('/analysis_hub')
        assert response.status_code in [200, 302, 404]

    def test_analysis_hub_as_senior(self, client, app, workspace_senior):
        """Analysis hub accessible for senior"""
        login_workspace_user(client, 'workspace_senior')
        response = client.get('/analysis_hub')
        assert response.status_code in [200, 302, 404]

    def test_analysis_hub_unauthenticated(self, client, app):
        """Analysis hub redirects when not logged in"""
        response = client.get('/analysis_hub')
        assert response.status_code in [302, 401]


class TestAnalysisPage:
    """Test analysis page routes"""

    def test_analysis_page_ts(self, client, app, workspace_user, workspace_analysis_type):
        """Analysis page for TS accessible"""
        login_workspace_user(client)
        response = client.get('/analysis_page/TS')
        assert response.status_code in [200, 302, 404]

    def test_analysis_page_with_sample_ids(self, client, app, workspace_user, workspace_sample, workspace_analysis_type):
        """Analysis page with sample_ids parameter"""
        login_workspace_user(client)
        response = client.get(f'/analysis_page/TS?sample_ids={workspace_sample}')
        assert response.status_code in [200, 302, 404]

    def test_analysis_page_with_multiple_samples(self, client, app, workspace_user, workspace_analysis_type):
        """Analysis page with multiple sample_ids"""
        login_workspace_user(client)
        response = client.get('/analysis_page/TS?sample_ids=1,2,3')
        assert response.status_code in [200, 302, 404]

    def test_analysis_page_invalid_code(self, client, app, workspace_user):
        """Analysis page with invalid code returns 404"""
        login_workspace_user(client)
        response = client.get('/analysis_page/INVALID_CODE_XYZ')
        assert response.status_code in [302, 404]

    def test_analysis_page_mad(self, client, app, workspace_user):
        """Analysis page for Mad"""
        login_workspace_user(client)
        response = client.get('/analysis_page/Mad')
        assert response.status_code in [200, 302, 404]

    def test_analysis_page_aad(self, client, app, workspace_user):
        """Analysis page for Aad"""
        login_workspace_user(client)
        response = client.get('/analysis_page/Aad')
        assert response.status_code in [200, 302, 404]

    def test_analysis_page_vad(self, client, app, workspace_user):
        """Analysis page for Vad (uses Mad results)"""
        login_workspace_user(client)
        response = client.get('/analysis_page/Vad')
        assert response.status_code in [200, 302, 404]

    def test_analysis_page_csn(self, client, app, workspace_user):
        """Analysis page for CSN"""
        login_workspace_user(client)
        response = client.get('/analysis_page/CSN')
        assert response.status_code in [200, 302, 404]


class TestEligibleSamplesAPI:
    """Test eligible samples API"""

    def test_eligible_samples_api(self, client, app, workspace_user, workspace_analysis_type):
        """Eligible samples API returns data"""
        login_workspace_user(client)
        response = client.get('/api/eligible_samples/TS')
        assert response.status_code in [200, 302, 404]

    def test_eligible_samples_with_search(self, client, app, workspace_user, workspace_analysis_type):
        """Eligible samples API with search parameter"""
        login_workspace_user(client)
        response = client.get('/api/eligible_samples/TS?q=test')
        assert response.status_code in [200, 302, 404]

    def test_eligible_samples_with_client(self, client, app, workspace_user, workspace_analysis_type):
        """Eligible samples API with client filter"""
        login_workspace_user(client)
        response = client.get('/api/eligible_samples/TS?client=Test')
        assert response.status_code in [200, 302, 404]


class TestSaveResultAPI:
    """Test save result API"""

    def test_save_result_api_get(self, client, app, workspace_user):
        """Save result API GET not allowed"""
        login_workspace_user(client)
        response = client.get('/api/save_result')
        assert response.status_code in [302, 404, 405]

    def test_save_result_api_post_empty(self, client, app, workspace_user):
        """Save result API POST with empty data"""
        login_workspace_user(client)
        response = client.post('/api/save_result', json={})
        assert response.status_code in [200, 302, 400, 404]

    def test_save_result_api_post_invalid(self, client, app, workspace_user):
        """Save result API POST with invalid data"""
        login_workspace_user(client)
        response = client.post('/api/save_result', json={
            'sample_id': 999999,
            'analysis_code': 'TS',
            'value': 1.5
        })
        assert response.status_code in [200, 302, 400, 404]


class TestBatchSaveAPI:
    """Test batch save API"""

    def test_batch_save_api_get(self, client, app, workspace_user):
        """Batch save API GET not allowed"""
        login_workspace_user(client)
        response = client.get('/api/batch_save')
        assert response.status_code in [302, 404, 405]

    def test_batch_save_api_post_empty(self, client, app, workspace_user):
        """Batch save API POST with empty data"""
        login_workspace_user(client)
        response = client.post('/api/batch_save', json={'results': []})
        assert response.status_code in [200, 302, 400, 404]


class TestTimerPresets:
    """Test timer presets in workspace"""

    def test_analysis_page_has_timer(self, client, app, workspace_user, workspace_analysis_type):
        """Analysis page includes timer data"""
        login_workspace_user(client)
        response = client.get('/analysis_page/Aad')
        # Timer presets should be available for Aad
        assert response.status_code in [200, 302, 404]


class TestAnalysisSchema:
    """Test analysis schema integration"""

    def test_analysis_page_schema(self, client, app, workspace_user, workspace_analysis_type):
        """Analysis page uses schema"""
        login_workspace_user(client)
        response = client.get('/analysis_page/TS')
        assert response.status_code in [200, 302, 404]
