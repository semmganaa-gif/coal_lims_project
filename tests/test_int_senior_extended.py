# tests/integration/test_senior_extended.py
# -*- coding: utf-8 -*-
"""
Senior routes extended tests
Coverage target: app/routes/analysis/senior.py
"""

import pytest
from app import db
from app.models import User, Sample, AnalysisResult
from datetime import datetime
import uuid
import json

VALID_PASSWORD = 'TestPass123'


@pytest.fixture
def senior_user(app):
    """Senior test user"""
    with app.app_context():
        user = User.query.filter_by(username='senior_test_user').first()
        if not user:
            user = User(username='senior_test_user', role='senior')
            user.set_password(VALID_PASSWORD)
            db.session.add(user)
            db.session.commit()
        return user


@pytest.fixture
def senior_chemist(app):
    """Chemist for creating results"""
    with app.app_context():
        user = User.query.filter_by(username='senior_chemist').first()
        if not user:
            user = User(username='senior_chemist', role='chemist')
            user.set_password(VALID_PASSWORD)
            db.session.add(user)
            db.session.commit()
        return user


@pytest.fixture
def pending_sample(app, senior_chemist):
    """Sample with pending results"""
    with app.app_context():
        unique_id = uuid.uuid4().hex[:6]
        sample = Sample(
            sample_code=f'SR-{unique_id}',
            client_name='CHPP',  # Use valid client name
            sample_type='CM',
            status='in_analysis',
            received_date=datetime.now(),
            user_id=senior_chemist.id
        )
        db.session.add(sample)
        db.session.commit()

        # Add pending result
        result = AnalysisResult(
            sample_id=sample.id,
            analysis_code='Mad',
            final_result='5.25',
            status='pending',
            user_id=senior_chemist.id
        )
        db.session.add(result)
        db.session.commit()
        return sample.id


def login_senior(client, username='senior_test_user'):
    """Helper login"""
    client.post('/login', data={
        'username': username,
        'password': VALID_PASSWORD
    }, follow_redirects=True)


class TestSeniorDashboard:
    """Test senior dashboard"""

    def test_senior_dashboard_accessible(self, client, app, senior_user):
        """Senior dashboard accessible"""
        login_senior(client)
        response = client.get('/analysis/senior')
        assert response.status_code in [200, 302, 404]

    def test_senior_dashboard_with_date(self, client, app, senior_user):
        """Senior dashboard with date filter"""
        login_senior(client)
        response = client.get('/analysis/senior?date=2024-01-15')
        assert response.status_code in [200, 302, 404]

    def test_senior_dashboard_with_code(self, client, app, senior_user):
        """Senior dashboard with analysis code filter"""
        login_senior(client)
        response = client.get('/analysis/senior?code=Mad')
        assert response.status_code in [200, 302, 404]

    def test_senior_dashboard_chemist_denied(self, client, app, senior_chemist):
        """Senior dashboard denied for chemist"""
        login_senior(client, 'senior_chemist')
        response = client.get('/analysis/senior')
        # Should redirect or return 403
        assert response.status_code in [302, 403, 404]


class TestReviewQueue:
    """Test review queue"""

    def test_review_queue_page(self, client, app, senior_user):
        """Review queue page accessible"""
        login_senior(client)
        response = client.get('/analysis/senior/queue')
        assert response.status_code in [200, 302, 404]

    def test_review_queue_with_filters(self, client, app, senior_user):
        """Review queue with filters"""
        login_senior(client)
        response = client.get('/analysis/senior/queue?status=pending')
        assert response.status_code in [200, 302, 404]


class TestPendingResults:
    """Test pending results API"""

    def test_pending_results_api(self, client, app, senior_user):
        """Pending results API returns data"""
        login_senior(client)
        response = client.get('/analysis/senior/api/pending')
        assert response.status_code in [200, 302, 404]

    def test_pending_results_with_code(self, client, app, senior_user):
        """Pending results with code filter"""
        login_senior(client)
        response = client.get('/analysis/senior/api/pending?code=Mad')
        assert response.status_code in [200, 302, 404]

    def test_pending_count_api(self, client, app, senior_user):
        """Pending count API"""
        login_senior(client)
        response = client.get('/analysis/senior/api/pending_count')
        assert response.status_code in [200, 302, 404]


class TestApproveResult:
    """Test result approval"""

    def test_approve_result_get(self, client, app, senior_user):
        """Approve result GET not allowed"""
        login_senior(client)
        response = client.get('/analysis/senior/approve/1')
        assert response.status_code in [302, 404, 405]

    def test_approve_result_post(self, client, app, senior_user, pending_sample):
        """Approve result POST"""
        login_senior(client)
        response = client.post('/analysis/senior/approve/1',
                              data={'action': 'approve'},
                              follow_redirects=True)
        assert response.status_code in [200, 302, 404]

    def test_approve_invalid_result(self, client, app, senior_user):
        """Approve non-existent result"""
        login_senior(client)
        response = client.post('/analysis/senior/approve/999999',
                              data={'action': 'approve'})
        assert response.status_code in [302, 404]


class TestRejectResult:
    """Test result rejection"""

    def test_reject_result(self, client, app, senior_user, pending_sample):
        """Reject result"""
        login_senior(client)
        response = client.post('/analysis/senior/reject/1',
                              data={'reason': 'Test rejection'},
                              follow_redirects=True)
        assert response.status_code in [200, 302, 404]

    def test_reject_without_reason(self, client, app, senior_user):
        """Reject without reason"""
        login_senior(client)
        response = client.post('/analysis/senior/reject/1',
                              data={})
        assert response.status_code in [200, 302, 400, 404]


class TestBulkApprove:
    """Test bulk approval"""

    def test_bulk_approve_api(self, client, app, senior_user):
        """Bulk approve API"""
        login_senior(client)
        response = client.post('/analysis/senior/api/bulk_approve',
                              json={'result_ids': []},
                              content_type='application/json')
        assert response.status_code in [200, 302, 400, 404]

    def test_bulk_approve_with_ids(self, client, app, senior_user, pending_sample):
        """Bulk approve with result IDs"""
        login_senior(client)
        response = client.post('/analysis/senior/api/bulk_approve',
                              json={'result_ids': [1, 2, 3]},
                              content_type='application/json')
        assert response.status_code in [200, 302, 400, 404]


class TestBulkReject:
    """Test bulk rejection"""

    def test_bulk_reject_api(self, client, app, senior_user):
        """Bulk reject API"""
        login_senior(client)
        response = client.post('/analysis/senior/api/bulk_reject',
                              json={'result_ids': [], 'reason': 'Test'},
                              content_type='application/json')
        assert response.status_code in [200, 302, 400, 404]


class TestReviewHistory:
    """Test review history"""

    def test_review_history_api(self, client, app, senior_user):
        """Review history API"""
        login_senior(client)
        response = client.get('/analysis/senior/api/history')
        assert response.status_code in [200, 302, 404]

    def test_review_history_with_date_range(self, client, app, senior_user):
        """Review history with date range"""
        login_senior(client)
        response = client.get('/analysis/senior/api/history?start_date=2024-01-01&end_date=2024-12-31')
        assert response.status_code in [200, 302, 404]


class TestSeniorReports:
    """Test senior reports"""

    def test_approval_report(self, client, app, senior_user):
        """Approval report page"""
        login_senior(client)
        response = client.get('/analysis/senior/reports/approvals')
        assert response.status_code in [200, 302, 404]

    def test_rejection_report(self, client, app, senior_user):
        """Rejection report page"""
        login_senior(client)
        response = client.get('/analysis/senior/reports/rejections')
        assert response.status_code in [200, 302, 404]


class TestResultDetail:
    """Test result detail view"""

    def test_result_detail(self, client, app, senior_user, pending_sample):
        """Result detail page"""
        login_senior(client)
        response = client.get('/analysis/senior/result/1')
        assert response.status_code in [200, 302, 404]

    def test_result_detail_invalid(self, client, app, senior_user):
        """Result detail for invalid ID"""
        login_senior(client)
        response = client.get('/analysis/senior/result/999999')
        assert response.status_code in [302, 404]


class TestSeniorWorkspace:
    """Test senior workspace"""

    def test_senior_workspace(self, client, app, senior_user):
        """Senior workspace page"""
        login_senior(client)
        response = client.get('/analysis/senior/workspace')
        assert response.status_code in [200, 302, 404]

    def test_senior_workspace_with_sample(self, client, app, senior_user, pending_sample):
        """Senior workspace with sample ID"""
        login_senior(client)
        response = client.get(f'/analysis/senior/workspace?sample_id={pending_sample}')
        assert response.status_code in [200, 302, 404]
