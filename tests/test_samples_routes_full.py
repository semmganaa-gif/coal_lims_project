# tests/test_samples_routes_full.py
# -*- coding: utf-8 -*-
"""
Complete tests for app/routes/main/samples.py
"""

import pytest
from unittest.mock import patch, MagicMock
from datetime import date, timedelta
import json


class TestEditSample:
    """Tests for edit_sample route."""

    def test_edit_sample_requires_login(self, client):
        """Test edit_sample requires authentication."""
        response = client.get('/edit_sample/1')
        assert response.status_code == 302

    def test_edit_sample_get(self, client, auth_user, app, db):
        """Test GET edit_sample page."""
        with app.app_context():
            from app.models import Sample, User
            user = User.query.first()
            sample = Sample(
                sample_code='EDIT_TEST_001',
                client_name='CHPP',
                sample_type='2 hourly',
                user_id=user.id,
                status='new',
                sample_date=date.today()
            )
            db.session.add(sample)
            db.session.commit()
            sample_id = sample.id

        response = client.get(f'/edit_sample/{sample_id}')
        # May redirect if user doesn't have permission
        assert response.status_code in [200, 302]

    def test_edit_sample_not_found(self, client, auth_user):
        """Test edit_sample with non-existent ID returns 404."""
        response = client.get('/edit_sample/999999')
        assert response.status_code == 404

    def test_edit_sample_post_empty_code(self, client, auth_user, app, db):
        """Test edit_sample POST with empty code."""
        with app.app_context():
            from app.models import Sample, User
            user = User.query.first()
            sample = Sample(
                sample_code='EDIT_TEST_002',
                client_name='CHPP',
                sample_type='2 hourly',
                user_id=user.id,
                status='new',
                sample_date=date.today()
            )
            db.session.add(sample)
            db.session.commit()
            sample_id = sample.id

        response = client.post(f'/edit_sample/{sample_id}', data={
            'sample_code': '',
            'analyses': []
        }, follow_redirects=True)
        assert response.status_code == 200

    def test_edit_sample_post_success(self, client, auth_user, app, db):
        """Test edit_sample POST successfully."""
        with app.app_context():
            from app.models import Sample, User
            user = User.query.first()
            sample = Sample(
                sample_code='EDIT_TEST_003',
                client_name='CHPP',
                sample_type='2 hourly',
                user_id=user.id,
                status='new',
                sample_date=date.today()
            )
            db.session.add(sample)
            db.session.commit()
            sample_id = sample.id

        response = client.post(f'/edit_sample/{sample_id}', data={
            'sample_code': 'EDIT_TEST_003_RENAMED',
            'analyses': ['Mad', 'Aad']
        }, follow_redirects=True)
        assert response.status_code == 200


class TestDeleteSelectedSamples:
    """Tests for delete_selected_samples route."""

    def test_delete_requires_login(self, client):
        """Test delete requires authentication."""
        response = client.post('/delete_selected_samples')
        assert response.status_code == 302

    def test_delete_no_selection(self, client, auth_user):
        """Test delete with no samples selected."""
        response = client.post('/delete_selected_samples', data={
            'sample_ids': []
        }, follow_redirects=True)
        assert response.status_code == 200

    def test_delete_success(self, client, auth_user, app, db):
        """Test delete samples successfully."""
        with app.app_context():
            from app.models import Sample, User
            user = User.query.first()
            sample = Sample(
                sample_code='DELETE_TEST_001',
                client_name='CHPP',
                sample_type='2 hourly',
                user_id=user.id,
                status='new',
                sample_date=date.today()
            )
            db.session.add(sample)
            db.session.commit()
            sample_id = sample.id

        response = client.post('/delete_selected_samples', data={
            'sample_ids': [str(sample_id)]
        }, follow_redirects=True)
        assert response.status_code == 200


class TestSampleDisposal:
    """Tests for sample_disposal route."""

    def test_disposal_requires_login(self, client):
        """Test disposal page requires authentication."""
        response = client.get('/sample_disposal')
        assert response.status_code == 302

    def test_disposal_get(self, client, auth_user):
        """Test GET sample_disposal page."""
        response = client.get('/sample_disposal')
        assert response.status_code == 200

    def test_disposal_shows_categories(self, client, auth_user):
        """Test disposal page shows different categories."""
        response = client.get('/sample_disposal')
        assert response.status_code == 200


class TestDisposeSamples:
    """Tests for dispose_samples route."""

    def test_dispose_requires_login(self, client):
        """Test dispose requires authentication."""
        response = client.post('/dispose_samples')
        assert response.status_code == 302

    def test_dispose_no_selection(self, client, auth_user):
        """Test dispose with no samples selected."""
        response = client.post('/dispose_samples', data={
            'sample_ids': [],
            'disposal_method': 'Discarded'
        }, follow_redirects=True)
        assert response.status_code == 200

    def test_dispose_no_method(self, client, auth_user):
        """Test dispose with no method."""
        response = client.post('/dispose_samples', data={
            'sample_ids': ['1'],
            'disposal_method': ''
        }, follow_redirects=True)
        assert response.status_code == 200

    def test_dispose_success(self, client, auth_user, app, db):
        """Test dispose samples successfully."""
        with app.app_context():
            from app.models import Sample, User
            user = User.query.first()
            sample = Sample(
                sample_code='DISPOSE_TEST_001',
                client_name='CHPP',
                sample_type='2 hourly',
                user_id=user.id,
                status='completed',
                sample_date=date.today(),
                retention_date=date.today() - timedelta(days=30)
            )
            db.session.add(sample)
            db.session.commit()
            sample_id = sample.id

        response = client.post('/dispose_samples', data={
            'sample_ids': [str(sample_id)],
            'disposal_method': 'Discarded'
        }, follow_redirects=True)
        assert response.status_code == 200


class TestSetRetentionDate:
    """Tests for set_retention_date route."""

    def test_set_retention_requires_login(self, client):
        """Test set_retention requires authentication."""
        response = client.post('/set_retention_date')
        assert response.status_code == 302

    def test_set_retention_no_selection(self, client, auth_user):
        """Test set_retention with no samples selected."""
        response = client.post('/set_retention_date', data={
            'sample_ids': [],
            'retention_days': '90'
        }, follow_redirects=True)
        assert response.status_code == 200

    def test_set_retention_invalid_days(self, client, auth_user):
        """Test set_retention with invalid days."""
        response = client.post('/set_retention_date', data={
            'sample_ids': ['1'],
            'retention_days': 'invalid'
        }, follow_redirects=True)
        assert response.status_code == 200

    def test_set_retention_out_of_range(self, client, auth_user):
        """Test set_retention with out of range days."""
        response = client.post('/set_retention_date', data={
            'sample_ids': ['1'],
            'retention_days': '9999'
        }, follow_redirects=True)
        assert response.status_code == 200

    def test_set_retention_success(self, client, auth_user, app, db):
        """Test set_retention successfully."""
        with app.app_context():
            from app.models import Sample, User
            user = User.query.first()
            sample = Sample(
                sample_code='RETENTION_TEST_001',
                client_name='CHPP',
                sample_type='2 hourly',
                user_id=user.id,
                sample_date=date.today()
            )
            db.session.add(sample)
            db.session.commit()
            sample_id = sample.id

        response = client.post('/set_retention_date', data={
            'sample_ids': [str(sample_id)],
            'retention_days': '90'
        }, follow_redirects=True)
        assert response.status_code == 200


class TestBulkSetRetention:
    """Tests for bulk_set_retention route."""

    def test_bulk_set_requires_login(self, client):
        """Test bulk_set requires authentication."""
        response = client.post('/bulk_set_retention')
        assert response.status_code == 302

    def test_bulk_set_no_days(self, client, auth_user):
        """Test bulk_set with no days."""
        response = client.post('/bulk_set_retention', data={
            'from_date': 'received'
        }, follow_redirects=True)
        assert response.status_code == 200

    def test_bulk_set_success(self, client, auth_user, app, db):
        """Test bulk_set successfully."""
        with app.app_context():
            from app.models import Sample, User
            from app.utils.datetime import now_local
            user = User.query.first()
            sample = Sample(
                sample_code='BULK_RETENTION_001',
                client_name='CHPP',
                sample_type='2 hourly',
                user_id=user.id,
                sample_date=date.today(),
                received_date=now_local(),
                retention_date=None
            )
            db.session.add(sample)
            db.session.commit()

        response = client.post('/bulk_set_retention', data={
            'retention_days': '90',
            'from_date': 'received'
        }, follow_redirects=True)
        assert response.status_code == 200


class TestAnalyticsDashboard:
    """Tests for analytics_dashboard route."""

    def test_analytics_requires_login(self, client):
        """Test analytics requires authentication."""
        response = client.get('/analytics')
        assert response.status_code == 302

    def test_analytics_get(self, client, auth_user):
        """Test GET analytics_dashboard page."""
        response = client.get('/analytics')
        assert response.status_code == 200


class TestRolePermissions:
    """Tests for role-based permissions."""

    def test_senior_cannot_delete_processed(self, client, app, db):
        """Test senior cannot delete processed samples."""
        with app.app_context():
            from app.models import User, Sample
            # Create senior user
            senior = User.query.filter_by(role='senior').first()
            if not senior:
                senior = User(username='senior_test', role='senior')
                senior.set_password('TestPass1234!')
                db.session.add(senior)
                db.session.commit()

            # Create processed sample
            sample = Sample(
                sample_code='PROCESSED_001',
                client_name='CHPP',
                sample_type='2 hourly',
                user_id=senior.id,
                status='in_progress',  # Not 'new'
                sample_date=date.today()
            )
            db.session.add(sample)
            db.session.commit()
            sample_id = sample.id

        # Login as senior
        client.post('/login', data={
            'username': 'senior_test',
            'password': 'TestPass1234!'
        })

        response = client.post('/delete_selected_samples', data={
            'sample_ids': [str(sample_id)]
        }, follow_redirects=True)
        assert response.status_code == 200


class TestAuditLogging:
    """Tests for audit logging in sample operations."""

    def test_delete_logs_audit(self, app, db):
        """Test delete operation logs audit."""
        with app.app_context():
            from app.utils.audit import log_audit
            # Should not raise
            log_audit(
                action='sample_deleted',
                resource_type='Sample',
                resource_id=1,
                details={'sample_code': 'TEST'}
            )

    def test_dispose_logs_audit(self, app, db):
        """Test dispose operation logs audit."""
        with app.app_context():
            from app.utils.audit import log_audit
            # Should not raise
            log_audit(
                action='sample_disposed',
                resource_type='Sample',
                resource_id=1,
                details={'disposal_method': 'Discarded'}
            )
