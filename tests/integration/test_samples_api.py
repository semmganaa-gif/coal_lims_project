# tests/integration/test_samples_api.py
# -*- coding: utf-8 -*-
"""
Samples API Integration Tests

Tests for sample-related API endpoints.
"""

import pytest
from flask import url_for
from app import db
from app.models import User, Sample, AnalysisResult
from datetime import datetime, timedelta
import json

VALID_PASSWORD = 'TestPass123'


class TestDataEndpoint:
    """GET /api/data endpoint тест"""

    def test_data_not_authenticated(self, client):
        """Нэвтрээгүй"""
        response = client.get('/api/data')
        assert response.status_code in [302, 401]

    def test_data_basic_request(self, client, app):
        """Энгийн DataTables request"""
        with app.app_context():
            user = User.query.filter_by(username='testuser').first()
            if not user:
                user = User(username='testuser', role='chemist')
                user.set_password(VALID_PASSWORD)
                db.session.add(user)
                db.session.commit()

        client.post('/login', data={
            'username': 'testuser',
            'password': VALID_PASSWORD
        }, follow_redirects=True)

        response = client.get('/api/data?draw=1&start=0&length=25')
        assert response.status_code in [200, 302]

    def test_data_with_date_filters(self, client, app):
        """Огноогоор шүүх"""
        with app.app_context():
            user = User.query.filter_by(username='testuser2').first()
            if not user:
                user = User(username='testuser2', role='chemist')
                user.set_password(VALID_PASSWORD)
                db.session.add(user)
                db.session.commit()

        client.post('/login', data={
            'username': 'testuser2',
            'password': VALID_PASSWORD
        }, follow_redirects=True)

        today = datetime.now().strftime('%Y-%m-%d')
        response = client.get(f'/api/data?draw=1&start=0&length=25&dateFilterStart={today}&dateFilterEnd={today}')
        assert response.status_code in [200, 302]

    def test_data_with_column_search(self, client, app):
        """Баганын хайлт"""
        with app.app_context():
            user = User.query.filter_by(username='testuser3').first()
            if not user:
                user = User(username='testuser3', role='chemist')
                user.set_password(VALID_PASSWORD)
                db.session.add(user)
                db.session.commit()

        client.post('/login', data={
            'username': 'testuser3',
            'password': VALID_PASSWORD
        }, follow_redirects=True)

        response = client.get('/api/data?draw=1&start=0&length=25&columns[2][data]=sample_code&columns[2][search][value]=TT')
        assert response.status_code in [200, 302]

    def test_data_pagination(self, client, app):
        """Хуудаслалт"""
        with app.app_context():
            user = User.query.filter_by(username='testuser4').first()
            if not user:
                user = User(username='testuser4', role='chemist')
                user.set_password(VALID_PASSWORD)
                db.session.add(user)
                db.session.commit()

        client.post('/login', data={
            'username': 'testuser4',
            'password': VALID_PASSWORD
        }, follow_redirects=True)

        response = client.get('/api/data?draw=1&start=25&length=25')
        assert response.status_code in [200, 302]


class TestSampleSummaryEndpoint:
    """GET /api/sample_summary endpoint тест"""

    def test_sample_summary_not_authenticated(self, client):
        """Нэвтрээгүй"""
        response = client.get('/api/sample_summary')
        assert response.status_code in [302, 401]

    def test_sample_summary_basic(self, client, app):
        """Энгийн sample summary"""
        with app.app_context():
            user = User.query.filter_by(username='summaryuser').first()
            if not user:
                user = User(username='summaryuser', role='chemist')
                user.set_password(VALID_PASSWORD)
                db.session.add(user)
                db.session.commit()

        client.post('/login', data={
            'username': 'summaryuser',
            'password': VALID_PASSWORD
        }, follow_redirects=True)

        response = client.get('/api/sample_summary')
        assert response.status_code in [200, 302]

    def test_sample_summary_with_date(self, client, app):
        """Огноогоор шүүсэн summary"""
        with app.app_context():
            user = User.query.filter_by(username='summaryuser2').first()
            if not user:
                user = User(username='summaryuser2', role='chemist')
                user.set_password(VALID_PASSWORD)
                db.session.add(user)
                db.session.commit()

        client.post('/login', data={
            'username': 'summaryuser2',
            'password': VALID_PASSWORD
        }, follow_redirects=True)

        today = datetime.now().strftime('%Y-%m-%d')
        response = client.get(f'/api/sample_summary?date={today}')
        assert response.status_code in [200, 302]


class TestSampleReportEndpoint:
    """GET /api/sample_report/<id> endpoint тест"""

    def test_sample_report_not_authenticated(self, client, app):
        """Нэвтрээгүй"""
        with app.app_context():
            sample = Sample.query.first()
            if sample:
                sample_id = sample.id
            else:
                sample_id = 1

        response = client.get(f'/api/sample_report/{sample_id}')
        assert response.status_code in [302, 401]

    def test_sample_report_not_found(self, client, app):
        """Байхгүй дээж"""
        with app.app_context():
            user = User.query.filter_by(username='reportuser').first()
            if not user:
                user = User(username='reportuser', role='chemist')
                user.set_password(VALID_PASSWORD)
                db.session.add(user)
                db.session.commit()

        client.post('/login', data={
            'username': 'reportuser',
            'password': VALID_PASSWORD
        }, follow_redirects=True)

        response = client.get('/api/sample_report/99999')
        assert response.status_code in [302, 404]


class TestSampleHistoryEndpoint:
    """GET /api/sample_history/<id> endpoint тест"""

    def test_sample_history_not_authenticated(self, client):
        """Нэвтрээгүй"""
        response = client.get('/api/sample_history/1')
        assert response.status_code in [302, 401]

    def test_sample_history_not_found(self, client, app):
        """Байхгүй дээж"""
        with app.app_context():
            user = User.query.filter_by(username='historyuser').first()
            if not user:
                user = User(username='historyuser', role='chemist')
                user.set_password(VALID_PASSWORD)
                db.session.add(user)
                db.session.commit()

        client.post('/login', data={
            'username': 'historyuser',
            'password': VALID_PASSWORD
        }, follow_redirects=True)

        response = client.get('/api/sample_history/99999')
        assert response.status_code in [302, 404]


class TestArchiveEndpoints:
    """Archive/Unarchive endpoints тест"""

    def test_archive_sample_not_authenticated(self, client):
        """Archive - нэвтрээгүй"""
        response = client.post('/api/sample/1/archive')
        assert response.status_code in [302, 401, 404, 405]

    def test_unarchive_sample_not_authenticated(self, client):
        """Unarchive - нэвтрээгүй"""
        response = client.post('/api/sample/1/unarchive')
        assert response.status_code in [302, 401, 404, 405]


class TestSampleStatusEndpoints:
    """Sample status-related endpoints тест"""

    def test_sample_status_update_not_authenticated(self, client):
        """Status update - нэвтрээгүй"""
        response = client.post('/api/sample/1/status', json={'status': 'completed'})
        assert response.status_code in [302, 401, 404, 405]


class TestSampleWithData:
    """Sample data-тай тест"""

    def test_create_sample_and_query(self, client, app):
        """Sample үүсгээд query хийх"""
        with app.app_context():
            user = User.query.filter_by(username='datauser').first()
            if not user:
                user = User(username='datauser', role='chemist')
                user.set_password(VALID_PASSWORD)
                db.session.add(user)
                db.session.commit()

            # Create a test sample
            sample = Sample.query.filter_by(sample_code='TEST-API-001').first()
            if not sample:
                sample = Sample(
                    sample_code='TEST-API-001',
                    client_name='QC',
                    sample_type='2hour',
                    received_date=datetime.now()
                )
                db.session.add(sample)
                db.session.commit()
            sample_id = sample.id

        client.post('/login', data={
            'username': 'datauser',
            'password': VALID_PASSWORD
        }, follow_redirects=True)

        # Query the sample through the API
        response = client.get('/api/data?draw=1&start=0&length=25')
        assert response.status_code in [200, 302]


class TestApiHelpers:
    """API helper functions тест"""

    def test_aggregate_sample_status_empty(self, app):
        """_aggregate_sample_status - хоосон"""
        with app.app_context():
            from app.routes.api.helpers import _aggregate_sample_status

            # Test empty result_statuses
            result = _aggregate_sample_status('received', None)
            assert result == 'received'

    def test_aggregate_sample_status_archived(self, app):
        """_aggregate_sample_status - archived"""
        with app.app_context():
            from app.routes.api.helpers import _aggregate_sample_status

            result = _aggregate_sample_status('archived', {'approved', 'pending'})
            assert result == 'archived'

    def test_aggregate_sample_status_pending_review(self, app):
        """_aggregate_sample_status - pending_review"""
        with app.app_context():
            from app.routes.api.helpers import _aggregate_sample_status

            result = _aggregate_sample_status('received', {'pending_review', 'approved'})
            assert result == 'pending_review'

    def test_aggregate_sample_status_rejected(self, app):
        """_aggregate_sample_status - rejected"""
        with app.app_context():
            from app.routes.api.helpers import _aggregate_sample_status

            result = _aggregate_sample_status('received', {'rejected', 'approved'})
            assert result == 'rejected'

    def test_aggregate_sample_status_approved(self, app):
        """_aggregate_sample_status - approved"""
        with app.app_context():
            from app.routes.api.helpers import _aggregate_sample_status

            result = _aggregate_sample_status('received', {'approved'})
            assert result == 'approved'


class TestRateLimiting:
    """Rate limiting тест"""

    def test_rate_limit_header(self, client, app):
        """Rate limit header байгаа эсэх"""
        with app.app_context():
            user = User.query.filter_by(username='ratelimituser').first()
            if not user:
                user = User(username='ratelimituser', role='chemist')
                user.set_password(VALID_PASSWORD)
                db.session.add(user)
                db.session.commit()

        client.post('/login', data={
            'username': 'ratelimituser',
            'password': VALID_PASSWORD
        }, follow_redirects=True)

        response = client.get('/api/data?draw=1&start=0&length=25')
        # Rate limit headers may or may not be present
        assert response.status_code in [200, 302, 429]
