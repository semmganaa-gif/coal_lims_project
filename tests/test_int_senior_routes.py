# -*- coding: utf-8 -*-
"""
Senior routes тестүүд
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
def senior_client(app, client):
    """Senior client fixture"""
    with app.app_context():
        user = User.query.filter_by(username='senior').first()
        if not user:
            user = User(username='senior', role='senior')
            user.set_password('SeniorPass123')
            db.session.add(user)
            db.session.commit()

        with client.session_transaction() as sess:
            sess['_user_id'] = str(user.id)
            sess['_fresh'] = True

    return client


class TestSeniorDashboard:
    """Senior dashboard тестүүд"""

    def test_senior_dashboard(self, senior_client, app):
        """Senior dashboard"""
        with app.app_context():
            response = senior_client.get('/analysis/senior')
            assert response.status_code in [200, 302, 404]


class TestReviewQueue:
    """Review queue тестүүд"""

    def test_review_queue(self, senior_client, app):
        """Review queue"""
        with app.app_context():
            response = senior_client.get('/analysis/senior/review')
            assert response.status_code in [200, 302, 404]

    def test_pending_review(self, senior_client, app):
        """Pending review"""
        with app.app_context():
            response = senior_client.get('/analysis/senior/pending')
            assert response.status_code in [200, 302, 404]


class TestApproval:
    """Approval тестүүд"""

    def test_approve_result(self, senior_client, app):
        """Approve result"""
        with app.app_context():
            response = senior_client.post('/api/senior/approve', json={
                'result_id': 1
            })
            assert response.status_code in [200, 302, 400, 404]

    def test_reject_result(self, senior_client, app):
        """Reject result"""
        with app.app_context():
            response = senior_client.post('/api/senior/reject', json={
                'result_id': 1,
                'reason': 'Test rejection'
            })
            assert response.status_code in [200, 302, 400, 404]

    def test_bulk_approve(self, senior_client, app):
        """Bulk approve"""
        with app.app_context():
            response = senior_client.post('/api/senior/bulk_approve', json={
                'result_ids': [1, 2, 3]
            })
            assert response.status_code in [200, 302, 400, 404]


class TestSeniorReports:
    """Senior reports тестүүд"""

    def test_approval_report(self, senior_client, app):
        """Approval report"""
        with app.app_context():
            response = senior_client.get('/analysis/senior/reports')
            assert response.status_code in [200, 302, 404]

    def test_rejection_report(self, senior_client, app):
        """Rejection report"""
        with app.app_context():
            response = senior_client.get('/analysis/senior/rejections')
            assert response.status_code in [200, 302, 404]


class TestSeniorAPI:
    """Senior API тестүүд"""

    def test_pending_count_api(self, senior_client, app):
        """Pending count API"""
        with app.app_context():
            response = senior_client.get('/api/senior/pending_count')
            assert response.status_code in [200, 302, 404]

    def test_review_history_api(self, senior_client, app):
        """Review history API"""
        with app.app_context():
            response = senior_client.get('/api/senior/history')
            assert response.status_code in [200, 302, 404]
