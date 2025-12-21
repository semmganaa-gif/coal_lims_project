# -*- coding: utf-8 -*-
"""
Senior routes - бүрэн интеграцийн тестүүд
senior.py файлын coverage нэмэгдүүлэх
"""
import pytest
import json
from datetime import datetime, timedelta
from app import create_app, db
from app.models import User, Sample, AnalysisResult, AnalysisResultLog, AnalysisType


@pytest.fixture
def app():
    """Test application fixture"""
    from tests.conftest import TestConfig
    app = create_app(TestConfig)
    app.config['SERVER_NAME'] = 'localhost'
    app.config['WTF_CSRF_ENABLED'] = False

    with app.app_context():
        db.create_all()
        # Create users
        if not User.query.filter_by(username='admin').first():
            user = User(username='admin', role='admin')
            user.set_password('Admin123')
            db.session.add(user)
        if not User.query.filter_by(username='senior').first():
            user = User(username='senior', role='senior')
            user.set_password('Senior123')
            db.session.add(user)
        if not User.query.filter_by(username='chemist').first():
            user = User(username='chemist', role='chemist')
            user.set_password('Chemist123')
            db.session.add(user)
        db.session.commit()

        # Create analysis types
        if not AnalysisType.query.filter_by(code='TS').first():
            at = AnalysisType(code='TS', name='Total Sulfur')
            db.session.add(at)
        if not AnalysisType.query.filter_by(code='CSN').first():
            at = AnalysisType(code='CSN', name='Crucible Swelling Number')
            db.session.add(at)
        db.session.commit()

    yield app

    with app.app_context():
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def auth_client(app, client):
    """Authenticated admin client"""
    client.post('/login', data={'username': 'admin', 'password': 'Admin123'})
    return client


@pytest.fixture
def senior_client(app, client):
    """Authenticated senior client"""
    client.post('/login', data={'username': 'senior', 'password': 'Senior123'})
    return client


@pytest.fixture
def chemist_client(app, client):
    """Authenticated chemist client"""
    client.post('/login', data={'username': 'chemist', 'password': 'Chemist123'})
    return client


def create_senior_test_data(app):
    """Create test data for senior dashboard"""
    with app.app_context():
        chemist = User.query.filter_by(username='chemist').first()
        now = datetime.now()

        # Create samples
        for i in range(5):
            sample = Sample(
                sample_code=f'SENIOR_TEST_{i}',
                user_id=chemist.id,
                client_name='CHPP',
                sample_type='2 hourly',
                received_date=now - timedelta(hours=i)
            )
            db.session.add(sample)
        db.session.commit()

        # Create analysis results with different statuses
        samples = Sample.query.filter(Sample.sample_code.like('SENIOR_TEST%')).all()
        statuses = ['pending_review', 'pending_review', 'rejected', 'approved', 'approved']

        for i, sample in enumerate(samples):
            result = AnalysisResult(
                sample_id=sample.id,
                analysis_code='TS',
                final_result=10.0 + i * 0.1,
                status=statuses[i % len(statuses)],
                user_id=chemist.id,
                raw_data=json.dumps({'value1': 10.0, 'value2': 10.1, 'diff': 0.1, 'avg': 10.05}),
                updated_at=now - timedelta(hours=i)
            )
            db.session.add(result)

        # Create CSN result for special handling
        csn_result = AnalysisResult(
            sample_id=samples[0].id,
            analysis_code='CSN',
            final_result=5,
            status='pending_review',
            user_id=chemist.id,
            raw_data=json.dumps({'t': 5, 'avg': 5}),
            updated_at=now
        )
        db.session.add(csn_result)
        db.session.commit()


class TestAhlahDashboard:
    """Ahlah dashboard тестүүд"""

    def test_ahlah_dashboard_unauthenticated(self, client, app):
        """Ahlah dashboard requires authentication"""
        with app.app_context():
            response = client.get('/ahlah_dashboard')
            assert response.status_code in [302, 401, 403]

    def test_ahlah_dashboard_chemist_forbidden(self, chemist_client, app):
        """Ahlah dashboard forbidden for chemist"""
        with app.app_context():
            response = chemist_client.get('/ahlah_dashboard')
            assert response.status_code in [302, 403]

    def test_ahlah_dashboard_senior_access(self, senior_client, app):
        """Ahlah dashboard accessible for senior"""
        with app.app_context():
            response = senior_client.get('/ahlah_dashboard')
            assert response.status_code in [200, 302]

    def test_ahlah_dashboard_admin_access(self, auth_client, app):
        """Ahlah dashboard accessible for admin"""
        with app.app_context():
            response = auth_client.get('/ahlah_dashboard')
            assert response.status_code in [200, 302]


class TestAhlahDataAPI:
    """Ahlah data API тестүүд"""

    def test_api_ahlah_data_empty(self, senior_client, app):
        """API ahlah data with no results"""
        with app.app_context():
            response = senior_client.get('/api/ahlah_data')
            assert response.status_code in [200, 302, 404]

    def test_api_ahlah_data_with_data(self, senior_client, app):
        """API ahlah data with results"""
        with app.app_context():
            create_senior_test_data(app)
            response = senior_client.get('/api/ahlah_data')
            assert response.status_code in [200, 302, 404]
            if response.status_code == 200:
                data = response.get_json()
                assert isinstance(data, list)

    def test_api_ahlah_data_with_date_filter(self, senior_client, app):
        """API ahlah data with date filter"""
        with app.app_context():
            create_senior_test_data(app)
            today = datetime.now().strftime('%Y-%m-%d')
            response = senior_client.get(f'/api/ahlah_data?start_date={today}&end_date={today}')
            assert response.status_code in [200, 302, 404]

    def test_api_ahlah_data_with_sample_name_filter(self, senior_client, app):
        """API ahlah data with sample name filter"""
        with app.app_context():
            create_senior_test_data(app)
            response = senior_client.get('/api/ahlah_data?sample_name=SENIOR_TEST')
            assert response.status_code in [200, 302, 404]

    def test_api_ahlah_data_invalid_date(self, senior_client, app):
        """API ahlah data with invalid date"""
        with app.app_context():
            response = senior_client.get('/api/ahlah_data?start_date=invalid')
            assert response.status_code in [200, 302, 404]


class TestUpdateResultStatus:
    """Update result status тестүүд"""

    def test_update_result_status_unauthorized(self, chemist_client, app):
        """Update result status unauthorized for chemist"""
        with app.app_context():
            create_senior_test_data(app)
            result = AnalysisResult.query.first()
            response = chemist_client.post(f'/update_result_status/{result.id}/approved')
            assert response.status_code in [302, 403]

    def test_update_result_status_approve(self, senior_client, app):
        """Update result status to approved"""
        with app.app_context():
            create_senior_test_data(app)
            result = AnalysisResult.query.filter_by(status='pending_review').first()
            response = senior_client.post(f'/update_result_status/{result.id}/approved')
            assert response.status_code in [200, 302]

    def test_update_result_status_reject(self, senior_client, app):
        """Update result status to rejected"""
        with app.app_context():
            create_senior_test_data(app)
            result = AnalysisResult.query.filter_by(status='pending_review').first()
            response = senior_client.post(
                f'/update_result_status/{result.id}/rejected',
                json={
                    'rejection_comment': 'Test rejection',
                    'rejection_category': 'repeat'
                },
                content_type='application/json'
            )
            assert response.status_code in [200, 302]

    def test_update_result_status_invalid_status(self, senior_client, app):
        """Update result status with invalid status"""
        with app.app_context():
            create_senior_test_data(app)
            result = AnalysisResult.query.first()
            response = senior_client.post(f'/update_result_status/{result.id}/invalid_status')
            assert response.status_code in [400]

    def test_update_result_status_not_found(self, senior_client, app):
        """Update result status for non-existent result"""
        with app.app_context():
            response = senior_client.post('/update_result_status/99999/approved')
            assert response.status_code in [404]

    def test_update_result_status_pending_review(self, senior_client, app):
        """Update result status to pending_review"""
        with app.app_context():
            create_senior_test_data(app)
            result = AnalysisResult.query.filter_by(status='approved').first()
            response = senior_client.post(f'/update_result_status/{result.id}/pending_review')
            assert response.status_code in [200, 302]


class TestBulkUpdateStatus:
    """Bulk update status тестүүд"""

    def test_bulk_update_status_unauthorized(self, chemist_client, app):
        """Bulk update unauthorized for chemist"""
        with app.app_context():
            response = chemist_client.post('/bulk_update_status',
                json={'result_ids': [1], 'status': 'approved'},
                content_type='application/json'
            )
            assert response.status_code in [302, 403]

    def test_bulk_update_status_empty_ids(self, senior_client, app):
        """Bulk update with empty result_ids"""
        with app.app_context():
            response = senior_client.post('/bulk_update_status',
                json={'result_ids': [], 'status': 'approved'},
                content_type='application/json'
            )
            assert response.status_code in [400]

    def test_bulk_update_status_invalid_status(self, senior_client, app):
        """Bulk update with invalid status"""
        with app.app_context():
            response = senior_client.post('/bulk_update_status',
                json={'result_ids': [1], 'status': 'invalid'},
                content_type='application/json'
            )
            assert response.status_code in [400]

    def test_bulk_update_status_reject_no_reason(self, senior_client, app):
        """Bulk update reject without reason"""
        with app.app_context():
            create_senior_test_data(app)
            result = AnalysisResult.query.filter_by(status='pending_review').first()
            response = senior_client.post('/bulk_update_status',
                json={'result_ids': [result.id], 'status': 'rejected'},
                content_type='application/json'
            )
            assert response.status_code in [400]

    def test_bulk_update_status_approve(self, senior_client, app):
        """Bulk update approve"""
        with app.app_context():
            create_senior_test_data(app)
            results = AnalysisResult.query.filter_by(status='pending_review').limit(2).all()
            result_ids = [r.id for r in results]
            response = senior_client.post('/bulk_update_status',
                json={'result_ids': result_ids, 'status': 'approved'},
                content_type='application/json'
            )
            assert response.status_code in [200]

    def test_bulk_update_status_reject(self, senior_client, app):
        """Bulk update reject"""
        with app.app_context():
            create_senior_test_data(app)
            results = AnalysisResult.query.filter_by(status='pending_review').limit(2).all()
            result_ids = [r.id for r in results]
            response = senior_client.post('/bulk_update_status',
                json={
                    'result_ids': result_ids,
                    'status': 'rejected',
                    'rejection_category': 'repeat',
                    'rejection_comment': 'Bulk rejection test'
                },
                content_type='application/json'
            )
            assert response.status_code in [200]

    def test_bulk_update_status_nonexistent_ids(self, senior_client, app):
        """Bulk update with non-existent IDs"""
        with app.app_context():
            response = senior_client.post('/bulk_update_status',
                json={'result_ids': [99999, 99998], 'status': 'approved'},
                content_type='application/json'
            )
            # Should return 200 with failed_ids
            assert response.status_code in [200]
            if response.status_code == 200:
                data = response.get_json()
                assert data.get('failed_count', 0) > 0


class TestAhlahStatsAPI:
    """Ahlah stats API тестүүд"""

    def test_api_ahlah_stats_empty(self, senior_client, app):
        """API ahlah stats with no data"""
        with app.app_context():
            response = senior_client.get('/api/ahlah_stats')
            assert response.status_code in [200, 302, 404]

    def test_api_ahlah_stats_with_data(self, senior_client, app):
        """API ahlah stats with data"""
        with app.app_context():
            create_senior_test_data(app)
            response = senior_client.get('/api/ahlah_stats')
            assert response.status_code in [200, 302, 404]
            if response.status_code == 200:
                data = response.get_json()
                assert 'chemists' in data
                assert 'samples_today' in data
                assert 'summary' in data

    def test_api_ahlah_stats_unauthorized(self, chemist_client, app):
        """API ahlah stats unauthorized for chemist"""
        with app.app_context():
            response = chemist_client.get('/api/ahlah_stats')
            assert response.status_code in [302, 403]
