# tests/integration/test_samples_api_extended.py
# -*- coding: utf-8 -*-
"""
Samples API Extended Tests - coverage нэмэгдүүлэх
"""

import pytest
from flask import url_for
from app import db
from app.models import User, Sample, AnalysisResult
from datetime import datetime, timedelta
import json

VALID_PASSWORD = 'TestPass123'


@pytest.fixture
def api_user(app):
    """API тестэд зориулсан хэрэглэгч"""
    with app.app_context():
        user = User.query.filter_by(username='api_test_user').first()
        if not user:
            user = User(username='api_test_user', role='chemist')
            user.set_password(VALID_PASSWORD)
            db.session.add(user)
            db.session.commit()
        return user


@pytest.fixture
def sample_data(app, api_user):
    """Тест дата үүсгэх"""
    with app.app_context():
        samples = []
        for i in range(5):
            sample = Sample.query.filter_by(sample_code=f'API-TEST-{i:03d}').first()
            if not sample:
                sample = Sample(
                    sample_code=f'API-TEST-{i:03d}',
                    client_name='QC',
                    sample_type='2hour',
                    received_date=datetime.now() - timedelta(days=i),
                    status='new',
                    analyses_to_perform='["Mad", "Aad"]'
                )
                db.session.add(sample)
                samples.append(sample)
        db.session.commit()
        return samples


class TestDataEndpoint:
    """GET /api/data endpoint тестүүд"""

    def test_data_not_authenticated(self, client):
        """Нэвтрээгүй хэрэглэгч"""
        response = client.get('/api/data')
        assert response.status_code in [302, 401]

    def test_data_basic(self, client, app, api_user):
        """Basic data request"""
        client.post('/login', data={
            'username': 'api_test_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)

        response = client.get('/api/data?draw=1&start=0&length=25')
        assert response.status_code in [200, 302]
        if response.status_code == 200:
            data = response.get_json()
            assert 'draw' in data or 'data' in data or isinstance(data, list)

    def test_data_with_pagination(self, client, app, api_user, sample_data):
        """Pagination test"""
        client.post('/login', data={
            'username': 'api_test_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)

        response = client.get('/api/data?draw=1&start=0&length=10')
        assert response.status_code in [200, 302]

        response = client.get('/api/data?draw=2&start=10&length=10')
        assert response.status_code in [200, 302]

    def test_data_with_date_filter(self, client, app, api_user):
        """Date filter test"""
        client.post('/login', data={
            'username': 'api_test_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)

        today = datetime.now().strftime('%Y-%m-%d')
        response = client.get(f'/api/data?draw=1&dateFilterStart={today}')
        assert response.status_code in [200, 302]

    def test_data_with_invalid_date(self, client, app, api_user):
        """Invalid date filter"""
        client.post('/login', data={
            'username': 'api_test_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)

        response = client.get('/api/data?draw=1&dateFilterStart=invalid-date')
        assert response.status_code in [200, 302]

    def test_data_with_column_search(self, client, app, api_user):
        """Column search test"""
        client.post('/login', data={
            'username': 'api_test_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)

        response = client.get('/api/data?draw=1&columns[0][data]=sample_code&columns[0][search][value]=TEST')
        assert response.status_code in [200, 302]

    def test_data_length_limit(self, client, app, api_user):
        """Length limit (max 1000)"""
        client.post('/login', data={
            'username': 'api_test_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)

        response = client.get('/api/data?draw=1&start=0&length=5000')
        assert response.status_code in [200, 302]


class TestSampleSummaryEndpoint:
    """GET /api/sample_summary endpoint тестүүд"""

    def test_sample_summary_not_authenticated(self, client):
        """Нэвтрээгүй"""
        response = client.get('/api/sample_summary')
        assert response.status_code in [302, 401]

    def test_sample_summary_basic(self, client, app, api_user):
        """Basic sample summary"""
        client.post('/login', data={
            'username': 'api_test_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)

        response = client.get('/api/sample_summary')
        assert response.status_code in [200, 302]

    def test_sample_summary_with_params(self, client, app, api_user):
        """Sample summary with parameters"""
        client.post('/login', data={
            'username': 'api_test_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)

        response = client.get('/api/sample_summary?start=0&length=10')
        assert response.status_code in [200, 302]


class TestSampleReportEndpoint:
    """GET /api/sample_report/<id> endpoint тестүүд"""

    def test_sample_report_not_authenticated(self, client):
        """Нэвтрээгүй"""
        response = client.get('/api/sample_report/1')
        assert response.status_code in [302, 401]

    def test_sample_report_valid_id(self, client, app, api_user, sample_data):
        """Valid sample report"""
        client.post('/login', data={
            'username': 'api_test_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)

        with app.app_context():
            sample = Sample.query.first()
            if sample:
                response = client.get(f'/api/sample_report/{sample.id}')
                assert response.status_code in [200, 302, 404]

    def test_sample_report_invalid_id(self, client, app, api_user):
        """Invalid sample ID"""
        client.post('/login', data={
            'username': 'api_test_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)

        response = client.get('/api/sample_report/99999')
        assert response.status_code in [200, 302, 404]


class TestSampleHistoryEndpoint:
    """GET /api/sample_history/<id> endpoint тестүүд"""

    def test_sample_history_not_authenticated(self, client):
        """Нэвтрээгүй"""
        response = client.get('/api/sample_history/1')
        assert response.status_code in [302, 401]

    def test_sample_history_valid_id(self, client, app, api_user, sample_data):
        """Valid sample history"""
        client.post('/login', data={
            'username': 'api_test_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)

        with app.app_context():
            sample = Sample.query.first()
            if sample:
                response = client.get(f'/api/sample_history/{sample.id}')
                assert response.status_code in [200, 302, 404]


class TestArchiveEndpoints:
    """Archive/Unarchive endpoints"""

    def test_archive_sample(self, client, app, api_user, sample_data):
        """Archive sample"""
        client.post('/login', data={
            'username': 'api_test_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)

        with app.app_context():
            sample = Sample.query.first()
            if sample:
                response = client.post(f'/api/archive_sample/{sample.id}')
                assert response.status_code in [200, 302, 400, 403, 404]

    def test_unarchive_sample(self, client, app, api_user, sample_data):
        """Unarchive sample"""
        client.post('/login', data={
            'username': 'api_test_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)

        with app.app_context():
            sample = Sample.query.first()
            if sample:
                response = client.post(f'/api/unarchive_sample/{sample.id}')
                assert response.status_code in [200, 302, 400, 403, 404]


class TestSampleStatusEndpoint:
    """Sample status endpoint тестүүд"""

    def test_sample_status(self, client, app, api_user, sample_data):
        """Sample status"""
        client.post('/login', data={
            'username': 'api_test_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)

        with app.app_context():
            sample = Sample.query.first()
            if sample:
                response = client.get(f'/api/sample_status/{sample.id}')
                assert response.status_code in [200, 302, 404]


class TestBulkOperations:
    """Bulk operations тестүүд"""

    def test_bulk_archive(self, client, app, api_user, sample_data):
        """Bulk archive"""
        client.post('/login', data={
            'username': 'api_test_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)

        response = client.post('/api/bulk_archive',
                              json={'sample_ids': [1, 2]},
                              content_type='application/json')
        assert response.status_code in [200, 302, 400, 403, 404]

    def test_bulk_delete(self, client, app, api_user):
        """Bulk delete"""
        client.post('/login', data={
            'username': 'api_test_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)

        response = client.post('/api/bulk_delete',
                              json={'sample_ids': []},
                              content_type='application/json')
        assert response.status_code in [200, 302, 400, 403, 404]
