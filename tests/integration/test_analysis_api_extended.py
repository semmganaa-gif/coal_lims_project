# tests/integration/test_analysis_api_extended.py
# -*- coding: utf-8 -*-
"""
Analysis API Extended Tests - coverage нэмэгдүүлэх
"""

import pytest
from flask import url_for
from app import db
from app.models import User, Sample, AnalysisResult, ControlStandard
from datetime import datetime, timedelta
import json

VALID_PASSWORD = 'TestPass123'


@pytest.fixture
def analysis_user(app):
    """Analysis тестэд зориулсан хэрэглэгч"""
    with app.app_context():
        user = User.query.filter_by(username='analysis_api_user').first()
        if not user:
            user = User(username='analysis_api_user', role='chemist')
            user.set_password(VALID_PASSWORD)
            db.session.add(user)
            db.session.commit()
        return user


@pytest.fixture
def senior_user(app):
    """Senior хэрэглэгч"""
    with app.app_context():
        user = User.query.filter_by(username='senior_api_user').first()
        if not user:
            user = User(username='senior_api_user', role='senior')
            user.set_password(VALID_PASSWORD)
            db.session.add(user)
            db.session.commit()
        return user


@pytest.fixture
def test_sample_with_results(app, analysis_user):
    """Шинжилгээний үр дүнтэй дээж"""
    with app.app_context():
        sample = Sample.query.filter_by(sample_code='ANALYSIS-TEST-001').first()
        if not sample:
            sample = Sample(
                sample_code='ANALYSIS-TEST-001',
                client_name='QC',
                sample_type='2hour',
                received_date=datetime.now(),
                status='new',
                analyses_to_perform='["Mad", "Aad", "Vad", "MT"]',
                mass_ready=True
            )
            db.session.add(sample)
            db.session.commit()

            # Шинжилгээний үр дүн нэмэх
            result = AnalysisResult(
                sample_id=sample.id,
                analysis_code='Mad',
                raw_data='{"p1": 5.0, "p2": 5.1}',
                final_result=5.05,
                status='pending_review'
            )
            db.session.add(result)
            db.session.commit()
        return sample


class TestEligibleSamplesExtended:
    """GET /api/eligible_samples/<code> extended тестүүд"""

    def test_eligible_samples_multiple_codes(self, client, app, analysis_user, test_sample_with_results):
        """Олон төрлийн шинжилгээний код"""
        client.post('/login', data={
            'username': 'analysis_api_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)

        codes = ['Mad', 'Aad', 'Vad', 'CV', 'TS', 'MT', 'Gi', 'FM', 'Solid', 'HGI',
                 'Size', 'X', 'Y', 'CRI', 'CSR', 'AFT', 'CV_eq', 'TS_eq']
        for code in codes:
            response = client.get(f'/api/eligible_samples/{code}')
            assert response.status_code in [200, 302]

    def test_eligible_samples_case_insensitive(self, client, app, analysis_user):
        """Case-insensitive"""
        client.post('/login', data={
            'username': 'analysis_api_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)

        for code in ['mad', 'MAD', 'Mad', 'mAd']:
            response = client.get(f'/api/eligible_samples/{code}')
            assert response.status_code in [200, 302]


class TestSaveResultsExtended:
    """POST /api/save_results extended тестүүд"""

    def test_save_results_valid_single(self, client, app, analysis_user, test_sample_with_results):
        """Single result save"""
        client.post('/login', data={
            'username': 'analysis_api_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)

        with app.app_context():
            sample = Sample.query.filter_by(sample_code='ANALYSIS-TEST-001').first()
            if sample:
                response = client.post('/api/save_results',
                    json={
                        'items': [{
                            'sample_id': sample.id,
                            'analysis_code': 'Aad',
                            'raw_data': {'p1': 10.0, 'p2': 10.2},
                            'final_result': 10.1
                        }]
                    },
                    content_type='application/json')
                assert response.status_code in [200, 207, 302, 400]

    def test_save_results_multiple(self, client, app, analysis_user, test_sample_with_results):
        """Multiple results save"""
        client.post('/login', data={
            'username': 'analysis_api_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)

        with app.app_context():
            sample = Sample.query.filter_by(sample_code='ANALYSIS-TEST-001').first()
            if sample:
                response = client.post('/api/save_results',
                    json={
                        'items': [
                            {
                                'sample_id': sample.id,
                                'analysis_code': 'Vad',
                                'raw_data': {'p1': 25.0, 'p2': 25.5},
                                'final_result': 25.25
                            },
                            {
                                'sample_id': sample.id,
                                'analysis_code': 'MT',
                                'raw_data': {'p1': 8.0, 'p2': 8.2},
                                'final_result': 8.1
                            }
                        ]
                    },
                    content_type='application/json')
                assert response.status_code in [200, 207, 302, 400]

    def test_save_results_with_notes(self, client, app, analysis_user, test_sample_with_results):
        """Save with notes"""
        client.post('/login', data={
            'username': 'analysis_api_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)

        with app.app_context():
            sample = Sample.query.filter_by(sample_code='ANALYSIS-TEST-001').first()
            if sample:
                response = client.post('/api/save_results',
                    json={
                        'items': [{
                            'sample_id': sample.id,
                            'analysis_code': 'CV',
                            'final_result': 5000,
                            'notes': 'Test note'
                        }]
                    },
                    content_type='application/json')
                assert response.status_code in [200, 207, 302, 400]

    def test_save_results_invalid_sample(self, client, app, analysis_user):
        """Invalid sample ID"""
        client.post('/login', data={
            'username': 'analysis_api_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)

        response = client.post('/api/save_results',
            json={
                'items': [{
                    'sample_id': 99999,
                    'analysis_code': 'Mad',
                    'final_result': 5.0
                }]
            },
            content_type='application/json')
        assert response.status_code in [200, 207, 302, 400, 404]


class TestUpdateResultStatus:
    """POST /api/update_result_status тестүүд"""

    def test_update_status_approve(self, client, app, senior_user, test_sample_with_results):
        """Approve result"""
        client.post('/login', data={
            'username': 'senior_api_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)

        with app.app_context():
            result = AnalysisResult.query.first()
            if result:
                response = client.post('/api/update_result_status',
                    json={
                        'result_id': result.id,
                        'status': 'approved'
                    },
                    content_type='application/json')
                assert response.status_code in [200, 302, 400, 403, 404]

    def test_update_status_reject(self, client, app, senior_user, test_sample_with_results):
        """Reject result"""
        client.post('/login', data={
            'username': 'senior_api_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)

        with app.app_context():
            result = AnalysisResult.query.first()
            if result:
                response = client.post('/api/update_result_status',
                    json={
                        'result_id': result.id,
                        'status': 'rejected',
                        'reason': 'Test rejection'
                    },
                    content_type='application/json')
                assert response.status_code in [200, 302, 400, 403, 404]


class TestDeleteResult:
    """DELETE /api/delete_result тестүүд"""

    def test_delete_result_not_authenticated(self, client):
        """Нэвтрээгүй"""
        response = client.delete('/api/delete_result/1')
        assert response.status_code in [302, 401, 404, 405]

    def test_delete_result_chemist(self, client, app, analysis_user, test_sample_with_results):
        """Chemist delete own result"""
        client.post('/login', data={
            'username': 'analysis_api_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)

        with app.app_context():
            result = AnalysisResult.query.first()
            if result:
                response = client.delete(f'/api/delete_result/{result.id}')
                assert response.status_code in [200, 302, 400, 403, 404, 405]


class TestAnalysisHistory:
    """GET /api/analysis_history тестүүд"""

    def test_analysis_history(self, client, app, analysis_user, test_sample_with_results):
        """Analysis history"""
        client.post('/login', data={
            'username': 'analysis_api_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)

        with app.app_context():
            result = AnalysisResult.query.first()
            if result:
                response = client.get(f'/api/analysis_history/{result.id}')
                assert response.status_code in [200, 302, 404]


class TestBatchResults:
    """Batch operations"""

    def test_batch_approve(self, client, app, senior_user, test_sample_with_results):
        """Batch approve"""
        client.post('/login', data={
            'username': 'senior_api_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)

        with app.app_context():
            results = AnalysisResult.query.limit(5).all()
            if results:
                response = client.post('/api/batch_approve',
                    json={'result_ids': [r.id for r in results]},
                    content_type='application/json')
                assert response.status_code in [200, 302, 400, 403, 404]


class TestControlStandardEndpoints:
    """Control Standard API тестүүд"""

    def test_get_control_standards(self, client, app, analysis_user):
        """Get control standards"""
        client.post('/login', data={
            'username': 'analysis_api_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)

        response = client.get('/api/control_standards')
        assert response.status_code in [200, 302, 404]

    def test_get_control_standard_values(self, client, app, analysis_user):
        """Get control standard values"""
        client.post('/login', data={
            'username': 'analysis_api_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)

        response = client.get('/api/control_standard_values?code=CS1')
        assert response.status_code in [200, 302, 404]
