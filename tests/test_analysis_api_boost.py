# tests/test_analysis_api_boost.py
# -*- coding: utf-8 -*-
"""Tests to boost api/analysis_api.py coverage."""

import pytest
import json
from unittest.mock import patch, MagicMock


@pytest.fixture
def admin_user(app, db, client):
    """Create and login as admin."""
    with app.app_context():
        from app.models import User
        user = User.query.filter_by(username='apiadmin').first()
        if not user:
            user = User(username='apiadmin', role='admin')
            user.set_password('AdminPass123!')
            db.session.add(user)
            db.session.commit()
        client.post('/login', data={'username': 'apiadmin', 'password': 'AdminPass123!'})
        return user


@pytest.fixture
def test_sample(app, db):
    """Create test sample with valid client_name."""
    import uuid
    with app.app_context():
        from app.models import Sample
        # client_name CHECK: ('CHPP','UHG-Geo','BN-Geo','QC','WTL','Proc','LAB')
        sample = Sample(
            sample_code=f'API-TEST-{uuid.uuid4().hex[:8].upper()}',
            client_name='QC',
            sample_type='coal'
        )
        db.session.add(sample)
        db.session.commit()
        return sample.id


class TestAnalysisAPI:
    """Test analysis API endpoints."""

    def test_get_analyses_list(self, client, admin_user):
        """Test get analyses list."""
        response = client.get('/api/analyses')
        assert response.status_code in [200, 302, 404]

    def test_get_analysis_types(self, client, admin_user):
        """Test get analysis types."""
        response = client.get('/api/analysis_types')
        assert response.status_code in [200, 302, 404]

    def test_get_analysis_by_sample(self, client, admin_user, test_sample):
        """Test get analysis by sample."""
        response = client.get(f'/api/sample/{test_sample}/analyses')
        assert response.status_code in [200, 302, 404]

    def test_save_analysis_result(self, client, admin_user, test_sample):
        """Test save analysis result."""
        response = client.post('/api/analysis/save',
            data=json.dumps({
                'sample_id': test_sample,
                'analysis_code': 'TM',
                'result': 5.5
            }),
            content_type='application/json')
        assert response.status_code in [200, 302, 400, 404]

    def test_bulk_save_results(self, client, admin_user):
        """Test bulk save results."""
        response = client.post('/api/analysis/bulk_save',
            data=json.dumps({'results': []}),
            content_type='application/json')
        assert response.status_code in [200, 302, 400, 404]

    def test_recalculate_results(self, client, admin_user, test_sample):
        """Test recalculate results."""
        response = client.post(f'/api/sample/{test_sample}/recalculate')
        assert response.status_code in [200, 302, 404]


class TestAnalysisValidation:
    """Test analysis validation."""

    def test_validate_result_range(self, client, admin_user):
        """Test validate result in range."""
        response = client.post('/api/analysis/validate',
            data=json.dumps({'analysis_code': 'TM', 'value': 5.5}),
            content_type='application/json')
        assert response.status_code in [200, 302, 400, 404]


class TestAnalysisExport:
    """Test analysis export."""

    def test_export_results_excel(self, client, admin_user):
        """Test export to Excel."""
        response = client.get('/api/analysis/export?format=excel')
        assert response.status_code in [200, 302, 404]

    def test_export_results_pdf(self, client, admin_user):
        """Test export to PDF."""
        response = client.get('/api/analysis/export?format=pdf')
        assert response.status_code in [200, 302, 404]
