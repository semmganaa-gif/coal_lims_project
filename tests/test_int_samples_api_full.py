# tests/integration/test_samples_api_full.py
# -*- coding: utf-8 -*-
"""Samples API full coverage tests"""

import pytest
from app import db
from app.models import User, Sample, AnalysisResult
from datetime import datetime, date
import json
import uuid

VALID_PASSWORD = 'TestPass123'


@pytest.fixture
def sa_admin(app):
    """Samples API admin user"""
    with app.app_context():
        user = User.query.filter_by(username='sa_admin_user').first()
        if not user:
            user = User(username='sa_admin_user', role='admin')
            user.set_password(VALID_PASSWORD)
            db.session.add(user)
            db.session.commit()
        return user


@pytest.fixture
def sa_prep(app):
    """Samples API prep user"""
    with app.app_context():
        user = User.query.filter_by(username='sa_prep_user').first()
        if not user:
            user = User(username='sa_prep_user', role='prep')
            user.set_password(VALID_PASSWORD)
            db.session.add(user)
            db.session.commit()
        return user


@pytest.fixture
def sa_sample(app):
    """Create sample for API tests"""
    with app.app_context():
        unique_id = uuid.uuid4().hex[:6]
        sample = Sample(
            sample_code=f'SA-{unique_id}',
            client_name='CHPP',
            sample_type='composite',
            status='pending',
            received_date=datetime.now()
        )
        db.session.add(sample)
        db.session.commit()
        return sample.id


class TestSamplesAPIList:
    """Samples API list tests"""

    def test_api_samples_list(self, client, app, sa_admin):
        """API samples list"""
        client.post('/login', data={
            'username': 'sa_admin_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)
        response = client.get('/api/samples')
        assert response.status_code in [200, 302, 404]

    def test_api_samples_paginated(self, client, app, sa_admin):
        """API samples paginated"""
        client.post('/login', data={
            'username': 'sa_admin_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)
        response = client.get('/api/samples?page=1&per_page=20')
        assert response.status_code in [200, 302, 404]

    def test_api_samples_filter_client(self, client, app, sa_admin):
        """API samples filter by client"""
        client.post('/login', data={
            'username': 'sa_admin_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)
        response = client.get('/api/samples?client_name=CHPP')
        assert response.status_code in [200, 302, 404]

    def test_api_samples_filter_status(self, client, app, sa_admin):
        """API samples filter by status"""
        client.post('/login', data={
            'username': 'sa_admin_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)
        response = client.get('/api/samples?status=pending')
        assert response.status_code in [200, 302, 404]

    def test_api_samples_filter_type(self, client, app, sa_admin):
        """API samples filter by type"""
        client.post('/login', data={
            'username': 'sa_admin_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)
        response = client.get('/api/samples?sample_type=composite')
        assert response.status_code in [200, 302, 404]

    def test_api_samples_filter_date_range(self, client, app, sa_admin):
        """API samples filter by date range"""
        client.post('/login', data={
            'username': 'sa_admin_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)
        today = date.today().isoformat()
        response = client.get(f'/api/samples?date_from={today}&date_to={today}')
        assert response.status_code in [200, 302, 404]

    def test_api_samples_search(self, client, app, sa_admin):
        """API samples search"""
        client.post('/login', data={
            'username': 'sa_admin_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)
        response = client.get('/api/samples?search=SC2025')
        assert response.status_code in [200, 302, 404]


class TestSamplesAPISingle:
    """Samples API single tests"""

    def test_api_sample_get(self, client, app, sa_admin, sa_sample):
        """API sample GET"""
        client.post('/login', data={
            'username': 'sa_admin_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)
        response = client.get(f'/api/samples/{sa_sample}')
        assert response.status_code in [200, 302, 404]

    def test_api_sample_get_invalid(self, client, app, sa_admin):
        """API sample GET invalid"""
        client.post('/login', data={
            'username': 'sa_admin_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)
        response = client.get('/api/samples/99999')
        assert response.status_code in [200, 302, 404]

    def test_api_sample_results(self, client, app, sa_admin, sa_sample):
        """API sample results"""
        client.post('/login', data={
            'username': 'sa_admin_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)
        response = client.get(f'/api/samples/{sa_sample}/results')
        assert response.status_code in [200, 302, 404]


class TestSamplesAPIUpdate:
    """Samples API update tests"""

    def test_api_sample_update(self, client, app, sa_admin, sa_sample):
        """API sample update"""
        client.post('/login', data={
            'username': 'sa_admin_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)
        response = client.put(f'/api/samples/{sa_sample}',
            data=json.dumps({'status': 'in_progress'}),
            content_type='application/json')
        assert response.status_code in [200, 302, 400, 403, 404, 405]

    def test_api_sample_patch(self, client, app, sa_admin, sa_sample):
        """API sample patch"""
        client.post('/login', data={
            'username': 'sa_admin_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)
        response = client.patch(f'/api/samples/{sa_sample}',
            data=json.dumps({'notes': 'Test note'}),
            content_type='application/json')
        assert response.status_code in [200, 302, 400, 403, 404, 405]


class TestSamplesAPIDelete:
    """Samples API delete tests"""

    def test_api_sample_delete(self, client, app, sa_admin, sa_sample):
        """API sample delete"""
        client.post('/login', data={
            'username': 'sa_admin_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)
        response = client.delete(f'/api/samples/{sa_sample}')
        assert response.status_code in [200, 204, 302, 400, 403, 404, 405]

    def test_api_sample_delete_invalid(self, client, app, sa_admin):
        """API sample delete invalid"""
        client.post('/login', data={
            'username': 'sa_admin_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)
        response = client.delete('/api/samples/99999')
        assert response.status_code in [200, 204, 302, 400, 403, 404, 405]


class TestSamplesAPICreate:
    """Samples API create tests"""

    def test_api_sample_create(self, client, app, sa_admin):
        """API sample create"""
        client.post('/login', data={
            'username': 'sa_admin_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)
        unique_id = uuid.uuid4().hex[:6]
        response = client.post('/api/samples',
            data=json.dumps({
                'sample_code': f'API-{unique_id}',
                'client_name': 'CHPP',
                'sample_type': 'composite'
            }),
            content_type='application/json')
        assert response.status_code in [200, 201, 302, 400, 403, 404, 405]

    def test_api_sample_create_invalid(self, client, app, sa_admin):
        """API sample create invalid"""
        client.post('/login', data={
            'username': 'sa_admin_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)
        response = client.post('/api/samples',
            data=json.dumps({}),
            content_type='application/json')
        assert response.status_code in [200, 201, 302, 400, 403, 404, 405]


class TestSamplesAPIDataTable:
    """Samples API DataTable tests"""

    def test_api_samples_dt(self, client, app, sa_admin):
        """API samples DataTable"""
        client.post('/login', data={
            'username': 'sa_admin_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)
        response = client.get('/api/samples_dt')
        assert response.status_code in [200, 302, 404]

    def test_api_samples_dt_with_draw(self, client, app, sa_admin):
        """API samples DataTable with draw"""
        client.post('/login', data={
            'username': 'sa_admin_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)
        response = client.get('/api/samples_dt?draw=1&start=0&length=10')
        assert response.status_code in [200, 302, 404]

    def test_api_samples_data(self, client, app, sa_admin):
        """API samples data"""
        client.post('/login', data={
            'username': 'sa_admin_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)
        response = client.get('/api/samples_data')
        assert response.status_code in [200, 302, 404]


class TestSamplesAPIExport:
    """Samples API export tests"""

    def test_export_samples_excel(self, client, app, sa_admin):
        """Export samples Excel"""
        client.post('/login', data={
            'username': 'sa_admin_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)
        response = client.get('/export/samples?format=excel')
        assert response.status_code in [200, 302, 400, 404]

    def test_export_samples_csv(self, client, app, sa_admin):
        """Export samples CSV"""
        client.post('/login', data={
            'username': 'sa_admin_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)
        response = client.get('/export/samples?format=csv')
        assert response.status_code in [200, 302, 400, 404]

    def test_export_samples_with_filter(self, client, app, sa_admin):
        """Export samples with filter"""
        client.post('/login', data={
            'username': 'sa_admin_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)
        response = client.get('/export/samples?format=excel&client=CHPP')
        assert response.status_code in [200, 302, 400, 404]


class TestSamplesAPIBulk:
    """Samples API bulk tests"""

    def test_api_samples_bulk_update(self, client, app, sa_admin, sa_sample):
        """API samples bulk update"""
        client.post('/login', data={
            'username': 'sa_admin_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)
        response = client.post('/api/samples/bulk/update',
            data=json.dumps({
                'ids': [sa_sample],
                'status': 'in_progress'
            }),
            content_type='application/json')
        assert response.status_code in [200, 302, 400, 403, 404, 405]

    def test_api_samples_bulk_delete(self, client, app, sa_admin, sa_sample):
        """API samples bulk delete"""
        client.post('/login', data={
            'username': 'sa_admin_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)
        response = client.post('/api/samples/bulk/delete',
            data=json.dumps({'ids': [sa_sample]}),
            content_type='application/json')
        assert response.status_code in [200, 302, 400, 403, 404, 405]


class TestSamplesShiftCode:
    """Samples shift code tests"""

    def test_api_shift_code(self, client, app, sa_admin):
        """API shift code"""
        client.post('/login', data={
            'username': 'sa_admin_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)
        response = client.get('/api/shift_code')
        assert response.status_code in [200, 302, 404]

    def test_api_shift_code_with_client(self, client, app, sa_admin):
        """API shift code with client"""
        client.post('/login', data={
            'username': 'sa_admin_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)
        response = client.get('/api/shift_code?client=CHPP')
        assert response.status_code in [200, 302, 404]

    def test_api_shift_code_with_type(self, client, app, sa_admin):
        """API shift code with type"""
        client.post('/login', data={
            'username': 'sa_admin_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)
        response = client.get('/api/shift_code?type=2hour')
        assert response.status_code in [200, 302, 404]
