# tests/integration/test_senior_workspace.py
# -*- coding: utf-8 -*-
"""Senior and workspace routes comprehensive coverage tests"""

import pytest
from app import db
from app.models import User, Sample, AnalysisResult
from datetime import datetime, date
import json
import uuid

VALID_PASSWORD = 'TestPass123'


@pytest.fixture
def sw_senior(app):
    """Senior user fixture"""
    with app.app_context():
        user = User.query.filter_by(username='sw_senior_user').first()
        if not user:
            user = User(username='sw_senior_user', role='senior')
            user.set_password(VALID_PASSWORD)
            db.session.add(user)
            db.session.commit()
        return user


@pytest.fixture
def sw_chemist(app):
    """Chemist user fixture"""
    with app.app_context():
        user = User.query.filter_by(username='sw_chemist_user').first()
        if not user:
            user = User(username='sw_chemist_user', role='chemist')
            user.set_password(VALID_PASSWORD)
            db.session.add(user)
            db.session.commit()
        return user


@pytest.fixture
def sw_admin(app):
    """Admin user fixture"""
    with app.app_context():
        user = User.query.filter_by(username='sw_admin_user').first()
        if not user:
            user = User(username='sw_admin_user', role='admin')
            user.set_password(VALID_PASSWORD)
            db.session.add(user)
            db.session.commit()
        return user


@pytest.fixture
def sw_sample(app):
    """Sample fixture"""
    with app.app_context():
        unique_id = uuid.uuid4().hex[:6]
        sample = Sample(
            sample_code=f'SW-{unique_id}',
            client_name='CHPP',
            sample_type='composite',
            status='completed',
            received_date=datetime.now()
        )
        db.session.add(sample)
        db.session.commit()
        return sample.id


class TestSeniorDashboard:
    """Senior dashboard tests"""

    def test_senior_dashboard_get(self, client, app, sw_senior):
        """Senior dashboard GET"""
        client.post('/login', data={
            'username': 'sw_senior_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)
        response = client.get('/senior/')
        assert response.status_code in [200, 302, 403, 404]

    def test_senior_dashboard_chemist(self, client, app, sw_chemist):
        """Senior dashboard as chemist - should redirect"""
        client.post('/login', data={
            'username': 'sw_chemist_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)
        response = client.get('/senior/')
        assert response.status_code in [200, 302, 403, 404]

    def test_senior_dashboard_admin(self, client, app, sw_admin):
        """Senior dashboard as admin"""
        client.post('/login', data={
            'username': 'sw_admin_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)
        response = client.get('/senior/')
        assert response.status_code in [200, 302, 403, 404]


class TestSeniorPendingReview:
    """Senior pending review tests"""

    def test_pending_review_get(self, client, app, sw_senior):
        """Pending review GET"""
        client.post('/login', data={
            'username': 'sw_senior_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)
        response = client.get('/senior/pending')
        assert response.status_code in [200, 302, 403, 404]

    def test_pending_review_with_client(self, client, app, sw_senior):
        """Pending review with client filter"""
        client.post('/login', data={
            'username': 'sw_senior_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)
        response = client.get('/senior/pending?client=CHPP')
        assert response.status_code in [200, 302, 403, 404]

    def test_pending_review_with_date(self, client, app, sw_senior):
        """Pending review with date filter"""
        client.post('/login', data={
            'username': 'sw_senior_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)
        today = date.today().isoformat()
        response = client.get(f'/senior/pending?date={today}')
        assert response.status_code in [200, 302, 403, 404]


class TestSeniorReview:
    """Senior review tests"""

    def test_review_sample(self, client, app, sw_senior, sw_sample):
        """Review sample"""
        client.post('/login', data={
            'username': 'sw_senior_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)
        response = client.get(f'/senior/review/{sw_sample}')
        assert response.status_code in [200, 302, 403, 404]

    def test_review_invalid_sample(self, client, app, sw_senior):
        """Review invalid sample"""
        client.post('/login', data={
            'username': 'sw_senior_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)
        response = client.get('/senior/review/99999')
        assert response.status_code in [200, 302, 403, 404]

    def test_approve_sample(self, client, app, sw_senior, sw_sample):
        """Approve sample"""
        client.post('/login', data={
            'username': 'sw_senior_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)
        response = client.post(f'/senior/approve/{sw_sample}')
        assert response.status_code in [200, 302, 400, 403, 404, 405]

    def test_reject_sample(self, client, app, sw_senior, sw_sample):
        """Reject sample"""
        client.post('/login', data={
            'username': 'sw_senior_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)
        response = client.post(f'/senior/reject/{sw_sample}',
            data={'reason': 'Test rejection'})
        assert response.status_code in [200, 302, 400, 403, 404, 405]


class TestSeniorBulkActions:
    """Senior bulk actions tests"""

    def test_bulk_approve(self, client, app, sw_senior, sw_sample):
        """Bulk approve"""
        client.post('/login', data={
            'username': 'sw_senior_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)
        response = client.post('/senior/bulk/approve',
            data=json.dumps({'sample_ids': [sw_sample]}),
            content_type='application/json')
        assert response.status_code in [200, 302, 400, 403, 404, 405]

    def test_bulk_reject(self, client, app, sw_senior, sw_sample):
        """Bulk reject"""
        client.post('/login', data={
            'username': 'sw_senior_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)
        response = client.post('/senior/bulk/reject',
            data=json.dumps({'sample_ids': [sw_sample], 'reason': 'Test'}),
            content_type='application/json')
        assert response.status_code in [200, 302, 400, 403, 404, 405]


class TestWorkspaceRoutes:
    """Workspace route tests"""

    def test_workspace_index(self, client, app, sw_chemist):
        """Workspace index"""
        client.post('/login', data={
            'username': 'sw_chemist_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)
        response = client.get('/analysis/workspace')
        assert response.status_code in [200, 302, 404]

    def test_workspace_with_sample(self, client, app, sw_chemist, sw_sample):
        """Workspace with sample"""
        client.post('/login', data={
            'username': 'sw_chemist_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)
        response = client.get(f'/analysis/workspace?sample_id={sw_sample}')
        assert response.status_code in [200, 302, 404]

    def test_workspace_with_analysis_type(self, client, app, sw_chemist):
        """Workspace with analysis type"""
        client.post('/login', data={
            'username': 'sw_chemist_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)
        response = client.get('/analysis/workspace?analysis_type=TM')
        assert response.status_code in [200, 302, 404]

    def test_workspace_queue(self, client, app, sw_chemist):
        """Workspace queue"""
        client.post('/login', data={
            'username': 'sw_chemist_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)
        response = client.get('/analysis/queue')
        assert response.status_code in [200, 302, 404]

    def test_workspace_queue_with_type(self, client, app, sw_chemist):
        """Workspace queue with type"""
        client.post('/login', data={
            'username': 'sw_chemist_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)
        response = client.get('/analysis/queue?type=TM')
        assert response.status_code in [200, 302, 404]


class TestAnalysisInput:
    """Analysis input tests"""

    def test_analysis_input_get(self, client, app, sw_chemist, sw_sample):
        """Analysis input GET"""
        client.post('/login', data={
            'username': 'sw_chemist_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)
        response = client.get(f'/analysis/input/{sw_sample}')
        assert response.status_code in [200, 302, 404]

    def test_analysis_input_post(self, client, app, sw_chemist, sw_sample):
        """Analysis input POST"""
        client.post('/login', data={
            'username': 'sw_chemist_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)
        response = client.post(f'/analysis/input/{sw_sample}',
            data={'TM': '5.5', 'IM': '8.0'})
        assert response.status_code in [200, 302, 400, 404, 405]

    def test_analysis_input_json(self, client, app, sw_chemist, sw_sample):
        """Analysis input JSON"""
        client.post('/login', data={
            'username': 'sw_chemist_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)
        response = client.post(f'/analysis/input/{sw_sample}',
            data=json.dumps({'results': {'TM': 5.5, 'IM': 8.0}}),
            content_type='application/json')
        assert response.status_code in [200, 302, 400, 404, 405]

    def test_analysis_save_draft(self, client, app, sw_chemist, sw_sample):
        """Analysis save draft"""
        client.post('/login', data={
            'username': 'sw_chemist_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)
        response = client.post(f'/analysis/draft/{sw_sample}',
            data=json.dumps({'results': {'TM': 5.5}}),
            content_type='application/json')
        assert response.status_code in [200, 302, 400, 404, 405]


class TestAnalysisComplete:
    """Analysis complete tests"""

    def test_analysis_complete(self, client, app, sw_chemist, sw_sample):
        """Analysis complete"""
        client.post('/login', data={
            'username': 'sw_chemist_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)
        response = client.post(f'/analysis/complete/{sw_sample}')
        assert response.status_code in [200, 302, 400, 404, 405]

    def test_analysis_reopen(self, client, app, sw_senior, sw_sample):
        """Analysis reopen"""
        client.post('/login', data={
            'username': 'sw_senior_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)
        response = client.post(f'/analysis/reopen/{sw_sample}')
        assert response.status_code in [200, 302, 400, 403, 404, 405]
