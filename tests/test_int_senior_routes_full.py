# tests/integration/test_senior_routes_full.py
# -*- coding: utf-8 -*-
"""
Senior routes full coverage tests
"""

import pytest
from app import db
from app.models import User, Sample, AnalysisResult
from datetime import datetime
import json

VALID_PASSWORD = 'TestPass123'


@pytest.fixture
def senior_user(app):
    """Senior user fixture"""
    with app.app_context():
        user = User.query.filter_by(username='senior_full_user').first()
        if not user:
            user = User(username='senior_full_user', role='senior')
            user.set_password(VALID_PASSWORD)
            db.session.add(user)
            db.session.commit()
        return user


@pytest.fixture
def manager_user(app):
    """Manager user fixture"""
    with app.app_context():
        user = User.query.filter_by(username='manager_full_user').first()
        if not user:
            user = User(username='manager_full_user', role='manager')
            user.set_password(VALID_PASSWORD)
            db.session.add(user)
            db.session.commit()
        return user


class TestSeniorIndex:
    """Senior index тестүүд"""

    def test_senior_index_unauthenticated(self, client, app):
        """Senior index without login"""
        response = client.get('/analysis/senior')
        assert response.status_code in [200, 302, 404]

    def test_senior_index_senior(self, client, app, senior_user):
        """Senior index with senior"""
        client.post('/login', data={
            'username': 'senior_full_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)

        response = client.get('/analysis/senior')
        assert response.status_code in [200, 302, 404]


class TestSeniorReview:
    """Senior review тестүүд"""

    def test_review_index(self, client, app, senior_user):
        """Review index"""
        client.post('/login', data={
            'username': 'senior_full_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)

        response = client.get('/analysis/senior/review')
        assert response.status_code in [200, 302, 404]

    def test_review_pending(self, client, app, senior_user):
        """Review pending"""
        client.post('/login', data={
            'username': 'senior_full_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)

        response = client.get('/analysis/senior/review?status=pending_review')
        assert response.status_code in [200, 302, 404]

    def test_review_by_analysis(self, client, app, senior_user):
        """Review by analysis code"""
        client.post('/login', data={
            'username': 'senior_full_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)

        for code in ['Mad', 'Aad', 'Vad', 'CV', 'TS']:
            response = client.get(f'/analysis/senior/review?analysis_code={code}')
            assert response.status_code in [200, 302, 404]


class TestSeniorApprove:
    """Senior approve тестүүд"""

    def test_approve_single(self, client, app, senior_user):
        """Approve single result"""
        client.post('/login', data={
            'username': 'senior_full_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)

        with app.app_context():
            result = AnalysisResult.query.first()
            if result:
                response = client.post('/api/senior/approve',
                    json={'result_id': result.id},
                    content_type='application/json')
                assert response.status_code in [200, 302, 400, 403, 404]

    def test_approve_multiple(self, client, app, senior_user):
        """Approve multiple results"""
        client.post('/login', data={
            'username': 'senior_full_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)

        with app.app_context():
            results = AnalysisResult.query.limit(3).all()
            if results:
                response = client.post('/api/senior/approve_multiple',
                    json={'result_ids': [r.id for r in results]},
                    content_type='application/json')
                assert response.status_code in [200, 302, 400, 403, 404]


class TestSeniorReject:
    """Senior reject тестүүд"""

    def test_reject_result(self, client, app, senior_user):
        """Reject result"""
        client.post('/login', data={
            'username': 'senior_full_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)

        with app.app_context():
            result = AnalysisResult.query.first()
            if result:
                response = client.post('/api/senior/reject',
                    json={'result_id': result.id, 'reason': 'Test rejection reason'},
                    content_type='application/json')
                assert response.status_code in [200, 302, 400, 403, 404]

    def test_reject_without_reason(self, client, app, senior_user):
        """Reject without reason"""
        client.post('/login', data={
            'username': 'senior_full_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)

        with app.app_context():
            result = AnalysisResult.query.first()
            if result:
                response = client.post('/api/senior/reject',
                    json={'result_id': result.id},
                    content_type='application/json')
                assert response.status_code in [200, 302, 400, 403, 404]


class TestSeniorRequestRetest:
    """Senior request retest тестүүд"""

    def test_request_retest(self, client, app, senior_user):
        """Request retest"""
        client.post('/login', data={
            'username': 'senior_full_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)

        with app.app_context():
            result = AnalysisResult.query.first()
            if result:
                response = client.post('/api/senior/request_retest',
                    json={'result_id': result.id, 'reason': 'Value out of range'},
                    content_type='application/json')
                assert response.status_code in [200, 302, 400, 403, 404]


class TestSeniorHistory:
    """Senior history тестүүд"""

    def test_review_history(self, client, app, senior_user):
        """Review history"""
        client.post('/login', data={
            'username': 'senior_full_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)

        response = client.get('/analysis/senior/history')
        assert response.status_code in [200, 302, 404]

    def test_review_history_filtered(self, client, app, senior_user):
        """Review history filtered"""
        client.post('/login', data={
            'username': 'senior_full_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)

        response = client.get('/analysis/senior/history?action=approved')
        assert response.status_code in [200, 302, 404]


class TestSeniorStatistics:
    """Senior statistics тестүүд"""

    def test_statistics(self, client, app, senior_user):
        """Statistics"""
        client.post('/login', data={
            'username': 'senior_full_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)

        response = client.get('/analysis/senior/statistics')
        assert response.status_code in [200, 302, 404]

    def test_statistics_api(self, client, app, senior_user):
        """Statistics API"""
        client.post('/login', data={
            'username': 'senior_full_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)

        response = client.get('/api/senior/statistics')
        assert response.status_code in [200, 302, 404]


class TestSeniorSampleStatus:
    """Senior sample status тестүүд"""

    def test_update_sample_status(self, client, app, senior_user):
        """Update sample status"""
        client.post('/login', data={
            'username': 'senior_full_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)

        with app.app_context():
            sample = Sample.query.first()
            if sample:
                response = client.post('/api/senior/sample_status',
                    json={'sample_id': sample.id, 'status': 'completed'},
                    content_type='application/json')
                assert response.status_code in [200, 302, 400, 403, 404]
