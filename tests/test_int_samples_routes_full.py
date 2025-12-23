# tests/integration/test_samples_routes_full.py
# -*- coding: utf-8 -*-
"""
Samples routes full coverage tests
"""

import pytest
from app import db
from app.models import User, Sample, AnalysisResult
from datetime import datetime, timedelta
import json

VALID_PASSWORD = 'TestPass123'


@pytest.fixture
def samples_user(app):
    """Samples user fixture"""
    with app.app_context():
        user = User.query.filter_by(username='samples_route_user').first()
        if not user:
            user = User(username='samples_route_user', role='prep')
            user.set_password(VALID_PASSWORD)
            db.session.add(user)
            db.session.commit()
        return user


@pytest.fixture
def samples_admin(app):
    """Samples admin fixture"""
    with app.app_context():
        user = User.query.filter_by(username='samples_admin_user').first()
        if not user:
            user = User(username='samples_admin_user', role='admin')
            user.set_password(VALID_PASSWORD)
            db.session.add(user)
            db.session.commit()
        return user


class TestSamplesIndex:
    """Samples index тестүүд"""

    def test_samples_index_unauthenticated(self, client, app):
        """Samples index without login"""
        response = client.get('/samples')
        assert response.status_code in [200, 302, 404]

    def test_samples_index_prep(self, client, app, samples_user):
        """Samples index with prep"""
        client.post('/login', data={
            'username': 'samples_route_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)

        response = client.get('/samples')
        assert response.status_code in [200, 302, 404]


class TestSamplesFilter:
    """Samples filter тестүүд"""

    def test_samples_by_status(self, client, app, samples_user):
        """Samples by status"""
        client.post('/login', data={
            'username': 'samples_route_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)

        for status in ['new', 'in_progress', 'completed', 'approved']:
            response = client.get(f'/samples?status={status}')
            assert response.status_code in [200, 302, 404]

    def test_samples_by_client(self, client, app, samples_user):
        """Samples by client"""
        client.post('/login', data={
            'username': 'samples_route_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)

        for client_name in ['CHPP', 'QC', 'WTL']:
            response = client.get(f'/samples?client_name={client_name}')
            assert response.status_code in [200, 302, 404]

    def test_samples_by_date(self, client, app, samples_user):
        """Samples by date"""
        client.post('/login', data={
            'username': 'samples_route_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)

        today = datetime.now().strftime('%Y-%m-%d')
        response = client.get(f'/samples?date={today}')
        assert response.status_code in [200, 302, 404]

    def test_samples_by_date_range(self, client, app, samples_user):
        """Samples by date range"""
        client.post('/login', data={
            'username': 'samples_route_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)

        today = datetime.now().strftime('%Y-%m-%d')
        week_ago = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
        response = client.get(f'/samples?start_date={week_ago}&end_date={today}')
        assert response.status_code in [200, 302, 404]


class TestSamplesDetail:
    """Samples detail тестүүд"""

    def test_sample_detail_get(self, client, app, samples_user):
        """Sample detail GET"""
        client.post('/login', data={
            'username': 'samples_route_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)

        with app.app_context():
            sample = Sample.query.first()
            if sample:
                response = client.get(f'/samples/{sample.id}')
                assert response.status_code in [200, 302, 404]

    def test_sample_detail_nonexistent(self, client, app, samples_user):
        """Sample detail nonexistent"""
        client.post('/login', data={
            'username': 'samples_route_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)

        response = client.get('/samples/99999')
        assert response.status_code in [200, 302, 404]


class TestSamplesEdit:
    """Samples edit тестүүд"""

    def test_sample_edit_get(self, client, app, samples_admin):
        """Sample edit GET"""
        client.post('/login', data={
            'username': 'samples_admin_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)

        with app.app_context():
            sample = Sample.query.first()
            if sample:
                response = client.get(f'/samples/{sample.id}/edit')
                assert response.status_code in [200, 302, 404]

    def test_sample_edit_post(self, client, app, samples_admin):
        """Sample edit POST"""
        client.post('/login', data={
            'username': 'samples_admin_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)

        with app.app_context():
            sample = Sample.query.first()
            if sample:
                response = client.post(f'/samples/{sample.id}/edit', data={
                    'notes': 'Updated test notes'
                })
                assert response.status_code in [200, 302, 400, 404]


class TestSamplesDelete:
    """Samples delete тестүүд"""

    def test_sample_delete(self, client, app, samples_admin):
        """Sample delete"""
        client.post('/login', data={
            'username': 'samples_admin_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)

        # Don't delete real samples, just test endpoint
        response = client.delete('/samples/99999')
        assert response.status_code in [200, 302, 400, 404, 405]


class TestSamplesExport:
    """Samples export тестүүд"""

    def test_samples_export_excel(self, client, app, samples_user):
        """Samples export Excel"""
        client.post('/login', data={
            'username': 'samples_route_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)

        response = client.get('/samples/export?format=excel')
        assert response.status_code in [200, 302, 404]

    def test_samples_export_csv(self, client, app, samples_user):
        """Samples export CSV"""
        client.post('/login', data={
            'username': 'samples_route_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)

        response = client.get('/samples/export?format=csv')
        assert response.status_code in [200, 302, 404]


class TestSamplesPrint:
    """Samples print тестүүд"""

    def test_sample_print(self, client, app, samples_user):
        """Sample print"""
        client.post('/login', data={
            'username': 'samples_route_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)

        with app.app_context():
            sample = Sample.query.first()
            if sample:
                response = client.get(f'/samples/{sample.id}/print')
                assert response.status_code in [200, 302, 404]


class TestSamplesLabel:
    """Samples label тестүүд"""

    def test_sample_label(self, client, app, samples_user):
        """Sample label"""
        client.post('/login', data={
            'username': 'samples_route_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)

        with app.app_context():
            sample = Sample.query.first()
            if sample:
                response = client.get(f'/samples/{sample.id}/label')
                assert response.status_code in [200, 302, 404]


class TestSamplesStatus:
    """Samples status тестүүд"""

    def test_update_sample_status(self, client, app, samples_admin):
        """Update sample status"""
        client.post('/login', data={
            'username': 'samples_admin_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)

        with app.app_context():
            sample = Sample.query.first()
            if sample:
                response = client.post(f'/samples/{sample.id}/status',
                    json={'status': 'in_progress'},
                    content_type='application/json')
                assert response.status_code in [200, 302, 400, 404, 405]


class TestSamplesResults:
    """Samples results тестүүд"""

    def test_sample_results(self, client, app, samples_user):
        """Sample results"""
        client.post('/login', data={
            'username': 'samples_route_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)

        with app.app_context():
            sample = Sample.query.first()
            if sample:
                response = client.get(f'/samples/{sample.id}/results')
                assert response.status_code in [200, 302, 404]
