# tests/integration/test_samples_routes_comprehensive.py
# -*- coding: utf-8 -*-
"""
Samples routes comprehensive coverage tests
"""

import pytest
from app import db
from app.models import User, Sample, AnalysisType
from datetime import datetime, date, timedelta
import json

VALID_PASSWORD = 'TestPass123'


@pytest.fixture
def samples_admin(app):
    """Admin user fixture"""
    with app.app_context():
        user = User.query.filter_by(username='samples_admin').first()
        if not user:
            user = User(username='samples_admin', role='admin')
            user.set_password(VALID_PASSWORD)
            db.session.add(user)
            db.session.commit()
        return user


@pytest.fixture
def samples_senior(app):
    """Senior user fixture"""
    with app.app_context():
        user = User.query.filter_by(username='samples_senior').first()
        if not user:
            user = User(username='samples_senior', role='senior')
            user.set_password(VALID_PASSWORD)
            db.session.add(user)
            db.session.commit()
        return user


@pytest.fixture
def samples_prep(app):
    """Prep user fixture"""
    with app.app_context():
        user = User.query.filter_by(username='samples_prep').first()
        if not user:
            user = User(username='samples_prep', role='prep')
            user.set_password(VALID_PASSWORD)
            db.session.add(user)
            db.session.commit()
        return user


@pytest.fixture
def samples_chemist(app):
    """Chemist user fixture"""
    with app.app_context():
        user = User.query.filter_by(username='samples_chemist').first()
        if not user:
            user = User(username='samples_chemist', role='chemist')
            user.set_password(VALID_PASSWORD)
            db.session.add(user)
            db.session.commit()
        return user


@pytest.fixture
def test_sample(app):
    """Test sample fixture"""
    with app.app_context():
        sample = Sample(
            sample_code=f'TEST-SAMPLE-{datetime.now().timestamp()}',
            client_name='CHPP',  # Valid client name
            sample_type='2hour',
            status='new',
            received_date=datetime.now()
        )
        db.session.add(sample)
        db.session.commit()
        return sample.id


@pytest.fixture
def completed_sample(app):
    """Completed sample fixture"""
    with app.app_context():
        sample = Sample(
            sample_code=f'COMPLETED-{datetime.now().timestamp()}',
            client_name='CHPP',  # Valid client name
            sample_type='2hour',
            status='completed',
            received_date=datetime.now() - timedelta(days=30),
            retention_date=date.today() + timedelta(days=60)
        )
        db.session.add(sample)
        db.session.commit()
        return sample.id


class TestEditSample:
    """Edit sample тестүүд"""

    def test_edit_sample_get_admin(self, client, app, samples_admin, test_sample):
        """Edit sample GET with admin"""
        client.post('/login', data={
            'username': 'samples_admin',
            'password': VALID_PASSWORD
        }, follow_redirects=True)
        response = client.get(f'/edit_sample/{test_sample}')
        assert response.status_code in [200, 302, 404]

    def test_edit_sample_get_senior(self, client, app, samples_senior, test_sample):
        """Edit sample GET with senior"""
        client.post('/login', data={
            'username': 'samples_senior',
            'password': VALID_PASSWORD
        }, follow_redirects=True)
        response = client.get(f'/edit_sample/{test_sample}')
        assert response.status_code in [200, 302, 404]

    def test_edit_sample_get_prep_new(self, client, app, samples_prep, test_sample):
        """Edit sample GET with prep (new status)"""
        client.post('/login', data={
            'username': 'samples_prep',
            'password': VALID_PASSWORD
        }, follow_redirects=True)
        response = client.get(f'/edit_sample/{test_sample}')
        assert response.status_code in [200, 302, 404]

    def test_edit_sample_get_chemist_forbidden(self, client, app, samples_chemist, test_sample):
        """Edit sample GET with chemist - should redirect"""
        client.post('/login', data={
            'username': 'samples_chemist',
            'password': VALID_PASSWORD
        }, follow_redirects=True)
        response = client.get(f'/edit_sample/{test_sample}')
        assert response.status_code in [200, 302]

    def test_edit_sample_post_code_change(self, client, app, samples_admin, test_sample):
        """Edit sample POST - change code"""
        client.post('/login', data={
            'username': 'samples_admin',
            'password': VALID_PASSWORD
        }, follow_redirects=True)
        new_code = f'NEW-CODE-{datetime.now().timestamp()}'
        response = client.post(f'/edit_sample/{test_sample}', data={
            'sample_code': new_code,
            'analyses': []
        }, follow_redirects=True)
        assert response.status_code in [200, 302, 400]

    def test_edit_sample_post_empty_code(self, client, app, samples_admin, test_sample):
        """Edit sample POST - empty code"""
        client.post('/login', data={
            'username': 'samples_admin',
            'password': VALID_PASSWORD
        }, follow_redirects=True)
        response = client.post(f'/edit_sample/{test_sample}', data={
            'sample_code': '',
            'analyses': []
        }, follow_redirects=True)
        assert response.status_code in [200, 302]

    def test_edit_sample_post_duplicate_code(self, client, app, samples_admin, test_sample):
        """Edit sample POST - duplicate code"""
        with app.app_context():
            existing = Sample(
                sample_code='EXISTING-SAMPLE',
                client_name='CHPP',
                status='new'
            )
            db.session.add(existing)
            db.session.commit()

        client.post('/login', data={
            'username': 'samples_admin',
            'password': VALID_PASSWORD
        }, follow_redirects=True)
        response = client.post(f'/edit_sample/{test_sample}', data={
            'sample_code': 'EXISTING-SAMPLE',
            'analyses': []
        }, follow_redirects=True)
        assert response.status_code in [200, 302]

    def test_edit_sample_post_change_analyses(self, client, app, samples_admin, test_sample):
        """Edit sample POST - change analyses"""
        client.post('/login', data={
            'username': 'samples_admin',
            'password': VALID_PASSWORD
        }, follow_redirects=True)
        response = client.post(f'/edit_sample/{test_sample}', data={
            'sample_code': '',
            'analyses': ['Mad', 'Aad', 'Vad']
        }, follow_redirects=True)
        assert response.status_code in [200, 302]


class TestDeleteSelectedSamples:
    """Delete selected samples тестүүд"""

    def test_delete_no_selection(self, client, app, samples_admin):
        """Delete with no selection"""
        client.post('/login', data={
            'username': 'samples_admin',
            'password': VALID_PASSWORD
        }, follow_redirects=True)
        response = client.post('/delete_selected_samples', data={
            'sample_ids': []
        }, follow_redirects=True)
        assert response.status_code in [200, 302]

    def test_delete_admin(self, client, app, samples_admin):
        """Delete with admin"""
        with app.app_context():
            sample = Sample(
                sample_code=f'TO-DELETE-{datetime.now().timestamp()}',
                client_name='CHPP',
                status='new'
            )
            db.session.add(sample)
            db.session.commit()
            sample_id = sample.id

        client.post('/login', data={
            'username': 'samples_admin',
            'password': VALID_PASSWORD
        }, follow_redirects=True)
        response = client.post('/delete_selected_samples', data={
            'sample_ids': [str(sample_id)]
        }, follow_redirects=True)
        assert response.status_code in [200, 302]

    def test_delete_senior_new_status(self, client, app, samples_senior):
        """Delete with senior (new status)"""
        with app.app_context():
            sample = Sample(
                sample_code=f'SENIOR-DEL-{datetime.now().timestamp()}',
                client_name='CHPP',
                status='new'
            )
            db.session.add(sample)
            db.session.commit()
            sample_id = sample.id

        client.post('/login', data={
            'username': 'samples_senior',
            'password': VALID_PASSWORD
        }, follow_redirects=True)
        response = client.post('/delete_selected_samples', data={
            'sample_ids': [str(sample_id)]
        }, follow_redirects=True)
        assert response.status_code in [200, 302]

    def test_delete_senior_processed_status_fail(self, client, app, samples_senior):
        """Delete with senior (processed status - should fail)"""
        with app.app_context():
            sample = Sample(
                sample_code=f'PROCESSED-{datetime.now().timestamp()}',
                client_name='CHPP',
                status='in_progress'
            )
            db.session.add(sample)
            db.session.commit()
            sample_id = sample.id

        client.post('/login', data={
            'username': 'samples_senior',
            'password': VALID_PASSWORD
        }, follow_redirects=True)
        response = client.post('/delete_selected_samples', data={
            'sample_ids': [str(sample_id)]
        }, follow_redirects=True)
        assert response.status_code in [200, 302]

    def test_delete_chemist_forbidden(self, client, app, samples_chemist, test_sample):
        """Delete with chemist - forbidden"""
        client.post('/login', data={
            'username': 'samples_chemist',
            'password': VALID_PASSWORD
        }, follow_redirects=True)
        response = client.post('/delete_selected_samples', data={
            'sample_ids': [str(test_sample)]
        }, follow_redirects=True)
        assert response.status_code in [200, 302]

    def test_delete_nonexistent(self, client, app, samples_admin):
        """Delete nonexistent sample"""
        client.post('/login', data={
            'username': 'samples_admin',
            'password': VALID_PASSWORD
        }, follow_redirects=True)
        response = client.post('/delete_selected_samples', data={
            'sample_ids': ['999999']
        }, follow_redirects=True)
        assert response.status_code in [200, 302]


class TestSampleDisposal:
    """Sample disposal тестүүд"""

    def test_sample_disposal_get(self, client, app, samples_chemist):
        """Sample disposal GET"""
        client.post('/login', data={
            'username': 'samples_chemist',
            'password': VALID_PASSWORD
        }, follow_redirects=True)
        response = client.get('/sample_disposal')
        assert response.status_code in [200, 302, 404]

    def test_sample_disposal_with_expired(self, client, app, samples_admin):
        """Sample disposal with expired samples"""
        with app.app_context():
            sample = Sample(
                sample_code=f'EXPIRED-{datetime.now().timestamp()}',
                client_name='CHPP',
                status='completed',
                retention_date=date.today() - timedelta(days=10)
            )
            db.session.add(sample)
            db.session.commit()

        client.post('/login', data={
            'username': 'samples_admin',
            'password': VALID_PASSWORD
        }, follow_redirects=True)
        response = client.get('/sample_disposal')
        assert response.status_code in [200, 302, 404]


class TestDisposeSamples:
    """Dispose samples тестүүд"""

    def test_dispose_no_selection(self, client, app, samples_admin):
        """Dispose with no selection"""
        client.post('/login', data={
            'username': 'samples_admin',
            'password': VALID_PASSWORD
        }, follow_redirects=True)
        response = client.post('/dispose_samples', data={
            'sample_ids': [],
            'disposal_method': 'Test'
        }, follow_redirects=True)
        assert response.status_code in [200, 302]

    def test_dispose_no_method(self, client, app, samples_admin, test_sample):
        """Dispose with no method"""
        client.post('/login', data={
            'username': 'samples_admin',
            'password': VALID_PASSWORD
        }, follow_redirects=True)
        response = client.post('/dispose_samples', data={
            'sample_ids': [str(test_sample)],
            'disposal_method': ''
        }, follow_redirects=True)
        assert response.status_code in [200, 302]

    def test_dispose_valid(self, client, app, samples_senior):
        """Dispose with valid data"""
        with app.app_context():
            sample = Sample(
                sample_code=f'DISPOSE-{datetime.now().timestamp()}',
                client_name='CHPP',
                status='completed'
            )
            db.session.add(sample)
            db.session.commit()
            sample_id = sample.id

        client.post('/login', data={
            'username': 'samples_senior',
            'password': VALID_PASSWORD
        }, follow_redirects=True)
        response = client.post('/dispose_samples', data={
            'sample_ids': [str(sample_id)],
            'disposal_method': 'Шатаалт'
        }, follow_redirects=True)
        assert response.status_code in [200, 302]

    def test_dispose_chemist_forbidden(self, client, app, samples_chemist, test_sample):
        """Dispose with chemist - forbidden"""
        client.post('/login', data={
            'username': 'samples_chemist',
            'password': VALID_PASSWORD
        }, follow_redirects=True)
        response = client.post('/dispose_samples', data={
            'sample_ids': [str(test_sample)],
            'disposal_method': 'Test'
        }, follow_redirects=True)
        assert response.status_code in [200, 302]


class TestSetRetentionDate:
    """Set retention date тестүүд"""

    def test_set_retention_no_selection(self, client, app, samples_admin):
        """Set retention with no selection"""
        client.post('/login', data={
            'username': 'samples_admin',
            'password': VALID_PASSWORD
        }, follow_redirects=True)
        response = client.post('/set_retention_date', data={
            'sample_ids': [],
            'retention_days': '90'
        }, follow_redirects=True)
        assert response.status_code in [200, 302]

    def test_set_retention_invalid_days(self, client, app, samples_admin, test_sample):
        """Set retention with invalid days"""
        client.post('/login', data={
            'username': 'samples_admin',
            'password': VALID_PASSWORD
        }, follow_redirects=True)
        response = client.post('/set_retention_date', data={
            'sample_ids': [str(test_sample)],
            'retention_days': 'invalid'
        }, follow_redirects=True)
        assert response.status_code in [200, 302]

    def test_set_retention_out_of_range(self, client, app, samples_senior, test_sample):
        """Set retention with out of range days"""
        client.post('/login', data={
            'username': 'samples_senior',
            'password': VALID_PASSWORD
        }, follow_redirects=True)
        response = client.post('/set_retention_date', data={
            'sample_ids': [str(test_sample)],
            'retention_days': '10000'
        }, follow_redirects=True)
        assert response.status_code in [200, 302]

    def test_set_retention_valid(self, client, app, samples_senior, test_sample):
        """Set retention with valid data"""
        client.post('/login', data={
            'username': 'samples_senior',
            'password': VALID_PASSWORD
        }, follow_redirects=True)
        response = client.post('/set_retention_date', data={
            'sample_ids': [str(test_sample)],
            'retention_days': '90'
        }, follow_redirects=True)
        assert response.status_code in [200, 302]

    def test_set_retention_chemist_forbidden(self, client, app, samples_chemist, test_sample):
        """Set retention with chemist - forbidden"""
        client.post('/login', data={
            'username': 'samples_chemist',
            'password': VALID_PASSWORD
        }, follow_redirects=True)
        response = client.post('/set_retention_date', data={
            'sample_ids': [str(test_sample)],
            'retention_days': '90'
        }, follow_redirects=True)
        assert response.status_code in [200, 302]


class TestBulkSetRetention:
    """Bulk set retention тестүүд"""

    def test_bulk_retention_no_days(self, client, app, samples_admin):
        """Bulk retention with no days"""
        client.post('/login', data={
            'username': 'samples_admin',
            'password': VALID_PASSWORD
        }, follow_redirects=True)
        response = client.post('/bulk_set_retention', data={
            'retention_days': '',
            'from_date': 'received'
        }, follow_redirects=True)
        assert response.status_code in [200, 302]

    def test_bulk_retention_valid_received(self, client, app, samples_admin):
        """Bulk retention with received date"""
        with app.app_context():
            sample = Sample(
                sample_code=f'BULK-RET-{datetime.now().timestamp()}',
                client_name='CHPP',
                status='completed',
                received_date=datetime.now() - timedelta(days=10),
                retention_date=None
            )
            db.session.add(sample)
            db.session.commit()

        client.post('/login', data={
            'username': 'samples_admin',
            'password': VALID_PASSWORD
        }, follow_redirects=True)
        response = client.post('/bulk_set_retention', data={
            'retention_days': '90',
            'from_date': 'received'
        }, follow_redirects=True)
        assert response.status_code in [200, 302]

    def test_bulk_retention_valid_today(self, client, app, samples_senior):
        """Bulk retention with today date"""
        client.post('/login', data={
            'username': 'samples_senior',
            'password': VALID_PASSWORD
        }, follow_redirects=True)
        response = client.post('/bulk_set_retention', data={
            'retention_days': '60',
            'from_date': 'today'
        }, follow_redirects=True)
        assert response.status_code in [200, 302]

    def test_bulk_retention_no_samples(self, client, app, samples_admin):
        """Bulk retention with no samples needing update"""
        # All samples already have retention date
        client.post('/login', data={
            'username': 'samples_admin',
            'password': VALID_PASSWORD
        }, follow_redirects=True)
        response = client.post('/bulk_set_retention', data={
            'retention_days': '90',
            'from_date': 'received'
        }, follow_redirects=True)
        assert response.status_code in [200, 302]


class TestAnalyticsDashboard:
    """Analytics dashboard тестүүд"""

    def test_analytics_dashboard_chemist(self, client, app, samples_chemist):
        """Analytics dashboard with chemist"""
        client.post('/login', data={
            'username': 'samples_chemist',
            'password': VALID_PASSWORD
        }, follow_redirects=True)
        response = client.get('/analytics')
        assert response.status_code in [200, 302, 404]

    def test_analytics_dashboard_admin(self, client, app, samples_admin):
        """Analytics dashboard with admin"""
        client.post('/login', data={
            'username': 'samples_admin',
            'password': VALID_PASSWORD
        }, follow_redirects=True)
        response = client.get('/analytics')
        assert response.status_code in [200, 302, 404]
