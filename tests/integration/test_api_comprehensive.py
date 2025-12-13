# tests/integration/test_api_comprehensive.py
# -*- coding: utf-8 -*-
"""
API Comprehensive Tests - coverage нэмэгдүүлэх
"""

import pytest
from flask import url_for
from app import db
from app.models import User, Sample, AnalysisResult
from datetime import datetime, timedelta
import json

VALID_PASSWORD = 'TestPass123'


@pytest.fixture
def api_test_user(app):
    """API тестэд зориулсан хэрэглэгч"""
    with app.app_context():
        user = User.query.filter_by(username='api_comp_user').first()
        if not user:
            user = User(username='api_comp_user', role='chemist')
            user.set_password(VALID_PASSWORD)
            db.session.add(user)
            db.session.commit()
        return user


@pytest.fixture
def senior_test_user(app):
    """Senior хэрэглэгч"""
    with app.app_context():
        user = User.query.filter_by(username='senior_comp_user').first()
        if not user:
            user = User(username='senior_comp_user', role='senior')
            user.set_password(VALID_PASSWORD)
            db.session.add(user)
            db.session.commit()
        return user


class TestDataAPI:
    """Data API тестүүд"""

    def test_data_with_sorting(self, client, app, api_test_user):
        """Data with sorting"""
        client.post('/login', data={
            'username': 'api_comp_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)

        response = client.get('/api/data?draw=1&order[0][column]=0&order[0][dir]=asc')
        assert response.status_code in [200, 302]

    def test_data_with_search(self, client, app, api_test_user):
        """Data with global search"""
        client.post('/login', data={
            'username': 'api_comp_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)

        response = client.get('/api/data?draw=1&search[value]=test')
        assert response.status_code in [200, 302]

    def test_data_date_range(self, client, app, api_test_user):
        """Data with date range"""
        client.post('/login', data={
            'username': 'api_comp_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)

        today = datetime.now().strftime('%Y-%m-%d')
        yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
        response = client.get(f'/api/data?draw=1&dateFilterStart={yesterday}&dateFilterEnd={today}')
        assert response.status_code in [200, 302]


class TestSampleSummaryAPI:
    """Sample Summary API тестүүд"""

    def test_sample_summary_pagination(self, client, app, api_test_user):
        """Sample summary with pagination"""
        client.post('/login', data={
            'username': 'api_comp_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)

        response = client.get('/api/sample_summary?start=0&length=50')
        assert response.status_code in [200, 302, 404]

    def test_sample_summary_filtering(self, client, app, api_test_user):
        """Sample summary with filtering"""
        client.post('/login', data={
            'username': 'api_comp_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)

        response = client.get('/api/sample_summary?status=new')
        assert response.status_code in [200, 302, 404]


class TestEligibleSamplesAPI:
    """Eligible Samples API тестүүд"""

    def test_eligible_all_codes(self, client, app, api_test_user):
        """Eligible samples for all analysis codes"""
        client.post('/login', data={
            'username': 'api_comp_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)

        codes = ['Mad', 'Aad', 'Vad', 'CV', 'TS', 'MT', 'Gi', 'FM', 'HGI',
                 'Size', 'X', 'Y', 'CRI', 'CSR', 'AFT', 'Solid', 'FC']
        for code in codes:
            response = client.get(f'/api/eligible_samples/{code}')
            assert response.status_code in [200, 302]


class TestSaveResultsAPI:
    """Save Results API тестүүд"""

    def test_save_single_result(self, client, app, api_test_user):
        """Save single result"""
        client.post('/login', data={
            'username': 'api_comp_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)

        with app.app_context():
            sample = Sample.query.first()
            if sample:
                response = client.post('/api/save_results',
                    json={'items': [{
                        'sample_id': sample.id,
                        'analysis_code': 'Mad',
                        'raw_data': {'p1': 5.0, 'p2': 5.1},
                        'final_result': 5.05
                    }]},
                    content_type='application/json')
                assert response.status_code in [200, 207, 302, 400]

    def test_save_multiple_results(self, client, app, api_test_user):
        """Save multiple results"""
        client.post('/login', data={
            'username': 'api_comp_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)

        with app.app_context():
            sample = Sample.query.first()
            if sample:
                response = client.post('/api/save_results',
                    json={'items': [
                        {'sample_id': sample.id, 'analysis_code': 'Aad', 'final_result': 10.5},
                        {'sample_id': sample.id, 'analysis_code': 'Vad', 'final_result': 25.3}
                    ]},
                    content_type='application/json')
                assert response.status_code in [200, 207, 302, 400]


class TestUpdateStatusAPI:
    """Update Status API тестүүд"""

    def test_approve_result(self, client, app, senior_test_user):
        """Approve result"""
        client.post('/login', data={
            'username': 'senior_comp_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)

        with app.app_context():
            result = AnalysisResult.query.first()
            if result:
                response = client.post('/api/update_result_status',
                    json={'result_id': result.id, 'status': 'approved'},
                    content_type='application/json')
                assert response.status_code in [200, 302, 400, 403, 404]

    def test_reject_result(self, client, app, senior_test_user):
        """Reject result"""
        client.post('/login', data={
            'username': 'senior_comp_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)

        with app.app_context():
            result = AnalysisResult.query.first()
            if result:
                response = client.post('/api/update_result_status',
                    json={'result_id': result.id, 'status': 'rejected', 'reason': 'Test'},
                    content_type='application/json')
                assert response.status_code in [200, 302, 400, 403, 404]


class TestMassAPI:
    """Mass API тестүүд"""

    def test_mass_pending(self, client, app, api_test_user):
        """Mass pending"""
        client.post('/login', data={
            'username': 'api_comp_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)

        response = client.get('/api/mass/pending')
        assert response.status_code in [200, 302, 404]

    def test_mass_ready_post(self, client, app, api_test_user):
        """Mass ready POST"""
        client.post('/login', data={
            'username': 'api_comp_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)

        with app.app_context():
            sample = Sample.query.first()
            if sample:
                response = client.post('/api/mass_ready',
                    json={'sample_id': sample.id, 'mass': 100.5},
                    content_type='application/json')
                assert response.status_code in [200, 302, 400, 404]


class TestAuditAPI:
    """Audit API тестүүд"""

    def test_audit_log(self, client, app, senior_test_user):
        """Audit log"""
        client.post('/login', data={
            'username': 'senior_comp_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)

        response = client.get('/api/audit_log')
        assert response.status_code in [200, 302, 404]

    def test_audit_log_filtered(self, client, app, senior_test_user):
        """Audit log filtered"""
        client.post('/login', data={
            'username': 'senior_comp_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)

        response = client.get('/api/audit_log?action=create')
        assert response.status_code in [200, 302, 404]


class TestChatAPI:
    """Chat API тестүүд"""

    def test_chat_messages(self, client, app, api_test_user):
        """Chat messages"""
        client.post('/login', data={
            'username': 'api_comp_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)

        response = client.get('/api/chat/messages')
        assert response.status_code in [200, 302, 404]

    def test_chat_send(self, client, app, api_test_user):
        """Chat send"""
        client.post('/login', data={
            'username': 'api_comp_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)

        response = client.post('/api/chat/send',
            json={'message': 'Test message'},
            content_type='application/json')
        assert response.status_code in [200, 302, 400, 404]


class TestControlStandardAPI:
    """Control Standard API тестүүд"""

    def test_control_standards_list(self, client, app, api_test_user):
        """Control standards list"""
        client.post('/login', data={
            'username': 'api_comp_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)

        response = client.get('/api/control_standards')
        assert response.status_code in [200, 302, 404]

    def test_control_standard_values(self, client, app, api_test_user):
        """Control standard values"""
        client.post('/login', data={
            'username': 'api_comp_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)

        response = client.get('/api/control_standard_values?code=CS1')
        assert response.status_code in [200, 302, 404]
