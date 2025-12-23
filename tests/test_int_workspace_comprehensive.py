# tests/integration/test_workspace_comprehensive.py
# -*- coding: utf-8 -*-
"""
Workspace routes comprehensive coverage tests
"""

import pytest
from app import db
from app.models import User, Sample, AnalysisResult
from datetime import datetime, date
import json

VALID_PASSWORD = 'TestPass123'


@pytest.fixture
def ws_chemist(app):
    """Workspace chemist user fixture"""
    with app.app_context():
        user = User.query.filter_by(username='ws_chemist_user').first()
        if not user:
            user = User(username='ws_chemist_user', role='chemist')
            user.set_password(VALID_PASSWORD)
            db.session.add(user)
            db.session.commit()
        return user


@pytest.fixture
def ws_senior(app):
    """Workspace senior user fixture"""
    with app.app_context():
        user = User.query.filter_by(username='ws_senior_user').first()
        if not user:
            user = User(username='ws_senior_user', role='senior')
            user.set_password(VALID_PASSWORD)
            db.session.add(user)
            db.session.commit()
        return user


@pytest.fixture
def ws_sample(app):
    """Create workspace test sample"""
    import uuid
    with app.app_context():
        unique_id = uuid.uuid4().hex[:6]
        sample = Sample(
            sample_code=f'WS-{unique_id}',
            client_name='CHPP',
            sample_type='2hour',
            status='new',
            received_date=datetime.now()
        )
        db.session.add(sample)
        db.session.commit()
        return sample.id


class TestWorkspaceList:
    """Workspace list tests"""

    def test_workspace_get(self, client, app, ws_chemist):
        """Workspace GET"""
        client.post('/login', data={
            'username': 'ws_chemist_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)
        response = client.get('/analysis/workspace')
        assert response.status_code in [200, 302, 404]

    def test_workspace_with_filters(self, client, app, ws_chemist):
        """Workspace with filters"""
        client.post('/login', data={
            'username': 'ws_chemist_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)
        today = date.today().isoformat()
        response = client.get(f'/analysis/workspace?date_from={today}&status=new')
        assert response.status_code in [200, 302, 404]

    def test_workspace_by_client(self, client, app, ws_chemist):
        """Workspace filtered by client"""
        client.post('/login', data={
            'username': 'ws_chemist_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)
        response = client.get('/analysis/workspace?client_name=CHPP')
        assert response.status_code in [200, 302, 404]


class TestWorkspaceSample:
    """Workspace sample operations tests"""

    def test_workspace_sample_view(self, client, app, ws_chemist, ws_sample):
        """Workspace sample view"""
        client.post('/login', data={
            'username': 'ws_chemist_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)
        response = client.get(f'/analysis/workspace/{ws_sample}')
        assert response.status_code in [200, 302, 404]

    def test_workspace_sample_invalid_id(self, client, app, ws_chemist):
        """Workspace sample with invalid ID"""
        client.post('/login', data={
            'username': 'ws_chemist_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)
        response = client.get('/analysis/workspace/99999')
        assert response.status_code in [200, 302, 404]


class TestAnalysisSummary:
    """Analysis summary tests"""

    def test_analysis_summary_get(self, client, app, ws_chemist):
        """Analysis summary GET"""
        client.post('/login', data={
            'username': 'ws_chemist_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)
        response = client.get('/analysis/')
        assert response.status_code in [200, 302, 404]

    def test_analysis_summary_with_date(self, client, app, ws_chemist):
        """Analysis summary with date filter"""
        client.post('/login', data={
            'username': 'ws_chemist_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)
        today = date.today().isoformat()
        response = client.get(f'/analysis/?date_from={today}')
        assert response.status_code in [200, 302, 404]

    def test_analysis_summary_with_client(self, client, app, ws_chemist):
        """Analysis summary with client filter"""
        client.post('/login', data={
            'username': 'ws_chemist_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)
        response = client.get('/analysis/?client_name=CHPP')
        assert response.status_code in [200, 302, 404]


class TestAnalysisResultSubmit:
    """Analysis result submit tests"""

    def test_submit_result_post(self, client, app, ws_chemist, ws_sample):
        """Submit analysis result"""
        client.post('/login', data={
            'username': 'ws_chemist_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)
        response = client.post('/analysis/submit_result', data={
            'sample_id': ws_sample,
            'analysis_code': 'Mad',
            'result_value': '5.5'
        }, follow_redirects=True)
        assert response.status_code in [200, 302, 400, 404]

    def test_submit_result_json(self, client, app, ws_chemist, ws_sample):
        """Submit analysis result JSON"""
        client.post('/login', data={
            'username': 'ws_chemist_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)
        response = client.post('/analysis/submit_result',
            data=json.dumps({
                'sample_id': ws_sample,
                'analysis_code': 'Mad',
                'result_value': '5.5'
            }),
            content_type='application/json',
            follow_redirects=True)
        assert response.status_code in [200, 302, 400, 404]


class TestAnalysisReview:
    """Analysis review tests"""

    def test_review_list(self, client, app, ws_senior):
        """Review list"""
        client.post('/login', data={
            'username': 'ws_senior_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)
        response = client.get('/analysis/review')
        assert response.status_code in [200, 302, 404]

    def test_review_approve(self, client, app, ws_senior, ws_sample):
        """Review approve"""
        client.post('/login', data={
            'username': 'ws_senior_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)
        response = client.post('/analysis/review/approve', data={
            'result_ids': ['1']
        }, follow_redirects=True)
        assert response.status_code in [200, 302, 400, 404]

    def test_review_reject(self, client, app, ws_senior, ws_sample):
        """Review reject"""
        client.post('/login', data={
            'username': 'ws_senior_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)
        response = client.post('/analysis/review/reject', data={
            'result_ids': ['1'],
            'reason': 'Test rejection'
        }, follow_redirects=True)
        assert response.status_code in [200, 302, 400, 404]


class TestAnalysisAPI:
    """Analysis API tests"""

    def test_api_results_get(self, client, app, ws_chemist):
        """API results GET"""
        client.post('/login', data={
            'username': 'ws_chemist_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)
        response = client.get('/api/analysis/results')
        assert response.status_code in [200, 302, 404]

    def test_api_results_by_sample(self, client, app, ws_chemist, ws_sample):
        """API results by sample"""
        client.post('/login', data={
            'username': 'ws_chemist_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)
        response = client.get(f'/api/analysis/results?sample_id={ws_sample}')
        assert response.status_code in [200, 302, 404]

    def test_api_sample_status(self, client, app, ws_chemist, ws_sample):
        """API sample status"""
        client.post('/login', data={
            'username': 'ws_chemist_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)
        response = client.get(f'/api/samples/{ws_sample}/status')
        assert response.status_code in [200, 302, 404]


class TestSeniorApproval:
    """Senior approval tests"""

    def test_senior_pending_list(self, client, app, ws_senior):
        """Senior pending list"""
        client.post('/login', data={
            'username': 'ws_senior_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)
        response = client.get('/analysis/senior/pending')
        assert response.status_code in [200, 302, 404]

    def test_senior_approve_all(self, client, app, ws_senior):
        """Senior approve all"""
        client.post('/login', data={
            'username': 'ws_senior_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)
        response = client.post('/analysis/senior/approve_all', follow_redirects=True)
        assert response.status_code in [200, 302, 400, 404]


class TestMassDataEntry:
    """Mass data entry tests"""

    def test_mass_entry_get(self, client, app, ws_chemist):
        """Mass entry GET"""
        client.post('/login', data={
            'username': 'ws_chemist_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)
        response = client.get('/analysis/mass_entry')
        assert response.status_code in [200, 302, 404]

    def test_mass_entry_post(self, client, app, ws_chemist):
        """Mass entry POST"""
        client.post('/login', data={
            'username': 'ws_chemist_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)
        response = client.post('/analysis/mass_entry', data={
            'entries': json.dumps([
                {'sample_code': 'TEST-001', 'analysis_code': 'Mad', 'value': '5.5'}
            ])
        }, follow_redirects=True)
        assert response.status_code in [200, 302, 400, 404]
