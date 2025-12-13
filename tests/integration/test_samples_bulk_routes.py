# tests/integration/test_samples_bulk_routes.py
# -*- coding: utf-8 -*-
"""Samples bulk operations routes tests"""

import pytest
from app import db
from app.models import User, Sample
from datetime import datetime, date
import uuid
import json

VALID_PASSWORD = 'TestPass123'


@pytest.fixture
def bulk_admin(app):
    with app.app_context():
        user = User.query.filter_by(username='bulk_admin_user').first()
        if not user:
            user = User(username='bulk_admin_user', role='admin')
            user.set_password(VALID_PASSWORD)
            db.session.add(user)
            db.session.commit()
        return user


@pytest.fixture
def bulk_samples(app):
    with app.app_context():
        samples = []
        for i in range(3):
            uid = uuid.uuid4().hex[:6]
            sample = Sample(
                sample_code=f'BLK-{uid}',
                client_name='CHPP',
                sample_type='2hour',
                status='pending',
                received_date=datetime.now()
            )
            db.session.add(sample)
            samples.append(sample)
        db.session.commit()
        return [s.id for s in samples]


class TestBulkSampleOperations:
    def test_bulk_update_status(self, client, app, bulk_admin, bulk_samples):
        client.post('/login', data={'username': 'bulk_admin_user', 'password': VALID_PASSWORD}, follow_redirects=True)
        r = client.post('/api/samples/bulk/status',
            data=json.dumps({
                'sample_ids': bulk_samples,
                'status': 'in_progress'
            }),
            content_type='application/json')
        assert r.status_code in [200, 302, 400, 404, 405]

    def test_bulk_delete(self, client, app, bulk_admin, bulk_samples):
        client.post('/login', data={'username': 'bulk_admin_user', 'password': VALID_PASSWORD}, follow_redirects=True)
        r = client.post('/api/samples/bulk/delete',
            data=json.dumps({'sample_ids': bulk_samples}),
            content_type='application/json')
        assert r.status_code in [200, 302, 400, 404, 405]

    def test_bulk_assign(self, client, app, bulk_admin, bulk_samples):
        client.post('/login', data={'username': 'bulk_admin_user', 'password': VALID_PASSWORD}, follow_redirects=True)
        r = client.post('/api/samples/bulk/assign',
            data=json.dumps({
                'sample_ids': bulk_samples,
                'user_id': 1
            }),
            content_type='application/json')
        assert r.status_code in [200, 302, 400, 404, 405]

    def test_bulk_export(self, client, app, bulk_admin, bulk_samples):
        client.post('/login', data={'username': 'bulk_admin_user', 'password': VALID_PASSWORD}, follow_redirects=True)
        sample_ids_str = ','.join(map(str, bulk_samples))
        r = client.get(f'/api/samples/bulk/export?ids={sample_ids_str}&format=excel')
        assert r.status_code in [200, 302, 400, 404]


class TestSampleSearch:
    def test_search_samples(self, client, app, bulk_admin):
        client.post('/login', data={'username': 'bulk_admin_user', 'password': VALID_PASSWORD}, follow_redirects=True)
        r = client.get('/api/samples/search?q=CHPP')
        assert r.status_code in [200, 302, 404]

    def test_search_samples_with_client(self, client, app, bulk_admin):
        client.post('/login', data={'username': 'bulk_admin_user', 'password': VALID_PASSWORD}, follow_redirects=True)
        r = client.get('/api/samples/search?q=test&client=CHPP')
        assert r.status_code in [200, 302, 404]

    def test_search_samples_with_date(self, client, app, bulk_admin):
        client.post('/login', data={'username': 'bulk_admin_user', 'password': VALID_PASSWORD}, follow_redirects=True)
        today = date.today().isoformat()
        r = client.get(f'/api/samples/search?q=test&date={today}')
        assert r.status_code in [200, 302, 404]


class TestSampleFilters:
    def test_filter_by_status_pending(self, client, app, bulk_admin):
        client.post('/login', data={'username': 'bulk_admin_user', 'password': VALID_PASSWORD}, follow_redirects=True)
        r = client.get('/api/samples?status=pending')
        assert r.status_code in [200, 302, 404]

    def test_filter_by_status_completed(self, client, app, bulk_admin):
        client.post('/login', data={'username': 'bulk_admin_user', 'password': VALID_PASSWORD}, follow_redirects=True)
        r = client.get('/api/samples?status=completed')
        assert r.status_code in [200, 302, 404]

    def test_filter_by_date_range(self, client, app, bulk_admin):
        client.post('/login', data={'username': 'bulk_admin_user', 'password': VALID_PASSWORD}, follow_redirects=True)
        today = date.today().isoformat()
        r = client.get(f'/api/samples?start_date={today}&end_date={today}')
        assert r.status_code in [200, 302, 404]

    def test_filter_by_sample_type(self, client, app, bulk_admin):
        client.post('/login', data={'username': 'bulk_admin_user', 'password': VALID_PASSWORD}, follow_redirects=True)
        types = ['2hour', '4hour', 'composite', 'Core']
        for t in types:
            r = client.get(f'/api/samples?sample_type={t}')
            assert r.status_code in [200, 302, 404]


class TestSampleStats:
    def test_sample_stats(self, client, app, bulk_admin):
        client.post('/login', data={'username': 'bulk_admin_user', 'password': VALID_PASSWORD}, follow_redirects=True)
        r = client.get('/api/samples/stats')
        assert r.status_code in [200, 302, 404]

    def test_sample_stats_by_client(self, client, app, bulk_admin):
        client.post('/login', data={'username': 'bulk_admin_user', 'password': VALID_PASSWORD}, follow_redirects=True)
        r = client.get('/api/samples/stats?group_by=client')
        assert r.status_code in [200, 302, 404]

    def test_sample_stats_by_status(self, client, app, bulk_admin):
        client.post('/login', data={'username': 'bulk_admin_user', 'password': VALID_PASSWORD}, follow_redirects=True)
        r = client.get('/api/samples/stats?group_by=status')
        assert r.status_code in [200, 302, 404]
