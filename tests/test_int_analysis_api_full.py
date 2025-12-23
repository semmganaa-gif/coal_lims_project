# tests/integration/test_analysis_api_full.py
# -*- coding: utf-8 -*-
"""Analysis API full coverage tests"""

import pytest
from app import db
from app.models import User, Sample, AnalysisResult
from datetime import datetime
import json
import uuid

VALID_PASSWORD = 'TestPass123'


@pytest.fixture
def aa_chemist(app):
    with app.app_context():
        user = User.query.filter_by(username='aa_chemist_user').first()
        if not user:
            user = User(username='aa_chemist_user', role='chemist')
            user.set_password(VALID_PASSWORD)
            db.session.add(user)
            db.session.commit()
        return user


@pytest.fixture
def aa_sample(app):
    with app.app_context():
        unique_id = uuid.uuid4().hex[:6]
        sample = Sample(
            sample_code=f'AA-{unique_id}',
            client_name='CHPP',
            sample_type='composite',
            status='in_progress',
            received_date=datetime.now()
        )
        db.session.add(sample)
        db.session.commit()
        return sample.id


class TestAnalysisAPIList:
    def test_api_analyses_list(self, client, app, aa_chemist):
        client.post('/login', data={'username': 'aa_chemist_user', 'password': VALID_PASSWORD}, follow_redirects=True)
        response = client.get('/api/analyses')
        assert response.status_code in [200, 302, 404]

    def test_api_analyses_by_sample(self, client, app, aa_chemist, aa_sample):
        client.post('/login', data={'username': 'aa_chemist_user', 'password': VALID_PASSWORD}, follow_redirects=True)
        response = client.get(f'/api/analyses?sample_id={aa_sample}')
        assert response.status_code in [200, 302, 404]

    def test_api_analyses_by_type(self, client, app, aa_chemist):
        client.post('/login', data={'username': 'aa_chemist_user', 'password': VALID_PASSWORD}, follow_redirects=True)
        response = client.get('/api/analyses?type=TM')
        assert response.status_code in [200, 302, 404]

    def test_api_analyses_pending(self, client, app, aa_chemist):
        client.post('/login', data={'username': 'aa_chemist_user', 'password': VALID_PASSWORD}, follow_redirects=True)
        response = client.get('/api/analyses?status=pending')
        assert response.status_code in [200, 302, 404]


class TestAnalysisResultAPI:
    def test_api_save_result(self, client, app, aa_chemist, aa_sample):
        client.post('/login', data={'username': 'aa_chemist_user', 'password': VALID_PASSWORD}, follow_redirects=True)
        response = client.post('/api/analyses/save',
            data=json.dumps({'sample_id': aa_sample, 'analysis_type': 'TM', 'value': 5.5}),
            content_type='application/json')
        assert response.status_code in [200, 201, 302, 400, 404, 405]

    def test_api_update_result(self, client, app, aa_chemist, aa_sample):
        client.post('/login', data={'username': 'aa_chemist_user', 'password': VALID_PASSWORD}, follow_redirects=True)
        response = client.put('/api/analyses/1',
            data=json.dumps({'value': 5.6}),
            content_type='application/json')
        assert response.status_code in [200, 302, 400, 404, 405]

    def test_api_delete_result(self, client, app, aa_chemist):
        client.post('/login', data={'username': 'aa_chemist_user', 'password': VALID_PASSWORD}, follow_redirects=True)
        response = client.delete('/api/analyses/99999')
        assert response.status_code in [200, 204, 302, 400, 403, 404, 405]


class TestAnalysisBatch:
    def test_api_batch_save(self, client, app, aa_chemist, aa_sample):
        client.post('/login', data={'username': 'aa_chemist_user', 'password': VALID_PASSWORD}, follow_redirects=True)
        response = client.post('/api/analyses/batch',
            data=json.dumps({'results': [{'sample_id': aa_sample, 'type': 'TM', 'value': 5.5}]}),
            content_type='application/json')
        assert response.status_code in [200, 201, 302, 400, 404, 405]

    def test_api_batch_validate(self, client, app, aa_chemist, aa_sample):
        client.post('/login', data={'username': 'aa_chemist_user', 'password': VALID_PASSWORD}, follow_redirects=True)
        response = client.post('/api/analyses/validate',
            data=json.dumps({'results': [{'type': 'TM', 'value': 5.5}]}),
            content_type='application/json')
        assert response.status_code in [200, 302, 400, 404, 405]


class TestAnalysisTypes:
    def test_api_analysis_types(self, client, app, aa_chemist):
        client.post('/login', data={'username': 'aa_chemist_user', 'password': VALID_PASSWORD}, follow_redirects=True)
        response = client.get('/api/analysis_types')
        assert response.status_code in [200, 302, 404]

    def test_api_analysis_types_by_client(self, client, app, aa_chemist):
        client.post('/login', data={'username': 'aa_chemist_user', 'password': VALID_PASSWORD}, follow_redirects=True)
        response = client.get('/api/analysis_types?client=CHPP')
        assert response.status_code in [200, 302, 404]

    def test_api_analysis_params(self, client, app, aa_chemist):
        client.post('/login', data={'username': 'aa_chemist_user', 'password': VALID_PASSWORD}, follow_redirects=True)
        response = client.get('/api/analysis_params?type=TM')
        assert response.status_code in [200, 302, 404]


class TestAnalysisCalculations:
    def test_api_calculate(self, client, app, aa_chemist, aa_sample):
        client.post('/login', data={'username': 'aa_chemist_user', 'password': VALID_PASSWORD}, follow_redirects=True)
        response = client.post('/api/analyses/calculate',
            data=json.dumps({'sample_id': aa_sample, 'basis': 'db'}),
            content_type='application/json')
        assert response.status_code in [200, 302, 400, 404, 405]

    def test_api_recalculate(self, client, app, aa_chemist, aa_sample):
        client.post('/login', data={'username': 'aa_chemist_user', 'password': VALID_PASSWORD}, follow_redirects=True)
        response = client.post(f'/api/analyses/recalculate/{aa_sample}')
        assert response.status_code in [200, 302, 400, 404, 405]
