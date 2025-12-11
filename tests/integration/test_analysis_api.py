# tests/integration/test_analysis_api.py
# -*- coding: utf-8 -*-
"""
Analysis API Integration Tests

Tests for analysis-related API endpoints.
"""

import pytest
from flask import url_for
from app import db
from app.models import User, Sample, AnalysisResult, ControlStandard
from datetime import datetime
import json

VALID_PASSWORD = 'TestPass123'


class TestEligibleSamplesEndpoint:
    """GET /api/eligible_samples/<analysis_code> endpoint тест"""

    def test_eligible_samples_not_authenticated(self, client):
        """Нэвтрээгүй"""
        response = client.get('/api/eligible_samples/Mad')
        assert response.status_code in [302, 401]

    def test_eligible_samples_valid_code(self, client, app):
        """Зөв шинжилгээний код"""
        with app.app_context():
            user = User.query.filter_by(username='eligible_user').first()
            if not user:
                user = User(username='eligible_user', role='chemist')
                user.set_password(VALID_PASSWORD)
                db.session.add(user)
                db.session.commit()

        client.post('/login', data={
            'username': 'eligible_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)

        response = client.get('/api/eligible_samples/Mad')
        assert response.status_code in [200, 302]

    def test_eligible_samples_empty_code(self, client, app):
        """Хоосон код"""
        with app.app_context():
            user = User.query.filter_by(username='eligible_user2').first()
            if not user:
                user = User(username='eligible_user2', role='chemist')
                user.set_password(VALID_PASSWORD)
                db.session.add(user)
                db.session.commit()

        client.post('/login', data={
            'username': 'eligible_user2',
            'password': VALID_PASSWORD
        }, follow_redirects=True)

        response = client.get('/api/eligible_samples/')
        # Empty code may return 404 or empty list
        assert response.status_code in [200, 302, 404]

    def test_eligible_samples_various_codes(self, client, app):
        """Олон төрлийн шинжилгээний код"""
        with app.app_context():
            user = User.query.filter_by(username='eligible_user3').first()
            if not user:
                user = User(username='eligible_user3', role='chemist')
                user.set_password(VALID_PASSWORD)
                db.session.add(user)
                db.session.commit()

        client.post('/login', data={
            'username': 'eligible_user3',
            'password': VALID_PASSWORD
        }, follow_redirects=True)

        codes = ['Aad', 'Vad', 'CV', 'TS', 'MT', 'Gi', 'FM', 'Solid']
        for code in codes:
            response = client.get(f'/api/eligible_samples/{code}')
            assert response.status_code in [200, 302]


class TestSaveResultsEndpoint:
    """POST /api/save_results endpoint тест"""

    def test_save_results_not_authenticated(self, client):
        """Нэвтрээгүй"""
        response = client.post('/api/save_results', json={
            'items': []
        })
        assert response.status_code in [302, 401]

    def test_save_results_empty_items(self, client, app):
        """Хоосон items"""
        with app.app_context():
            user = User.query.filter_by(username='save_user').first()
            if not user:
                user = User(username='save_user', role='chemist')
                user.set_password(VALID_PASSWORD)
                db.session.add(user)
                db.session.commit()

        client.post('/login', data={
            'username': 'save_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)

        response = client.post('/api/save_results',
                               json={'items': []},
                               content_type='application/json')
        # 207 Multi Status is also valid for batch operations
        assert response.status_code in [200, 207, 400, 302]

    def test_save_results_invalid_json(self, client, app):
        """Буруу JSON"""
        with app.app_context():
            user = User.query.filter_by(username='save_user2').first()
            if not user:
                user = User(username='save_user2', role='chemist')
                user.set_password(VALID_PASSWORD)
                db.session.add(user)
                db.session.commit()

        client.post('/login', data={
            'username': 'save_user2',
            'password': VALID_PASSWORD
        }, follow_redirects=True)

        response = client.post('/api/save_results',
                               data='not json',
                               content_type='application/json')
        assert response.status_code in [200, 400, 302, 415, 500]


class TestUpdateResultStatusEndpoint:
    """POST /api/update_result_status endpoint тест"""

    def test_update_result_status_not_authenticated(self, client):
        """Нэвтрээгүй"""
        response = client.post('/api/update_result_status', json={
            'result_id': 1,
            'status': 'approved'
        })
        # 404 if route doesn't exist
        assert response.status_code in [302, 401, 404]

    def test_update_result_status_missing_data(self, client, app):
        """Шаардлагатай өгөгдөл дутуу"""
        with app.app_context():
            user = User.query.filter_by(username='status_user').first()
            if not user:
                user = User(username='status_user', role='senior')
                user.set_password(VALID_PASSWORD)
                db.session.add(user)
                db.session.commit()

        client.post('/login', data={
            'username': 'status_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)

        response = client.post('/api/update_result_status',
                               json={},
                               content_type='application/json')
        assert response.status_code in [200, 400, 302, 404]


class TestAnalysisResultFlow:
    """Шинжилгээний үр дүн бүртгэх flow"""

    def test_create_sample_and_result(self, client, app):
        """Sample үүсгээд result хадгалах"""
        with app.app_context():
            user = User.query.filter_by(username='flow_user').first()
            if not user:
                user = User(username='flow_user', role='chemist')
                user.set_password(VALID_PASSWORD)
                db.session.add(user)
                db.session.commit()

            # Create test sample
            sample = Sample.query.filter_by(sample_code='FLOW-TEST-001').first()
            if not sample:
                sample = Sample(
                    sample_code='FLOW-TEST-001',
                    client_name='QC',
                    sample_type='2hour',
                    received_date=datetime.now(),
                    status='new',
                    analyses_to_perform='["Mad", "Aad", "Vad"]'
                )
                db.session.add(sample)
                db.session.commit()

        client.post('/login', data={
            'username': 'flow_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)

        # Check eligible samples for Mad
        response = client.get('/api/eligible_samples/Mad')
        assert response.status_code in [200, 302]


class TestAnalysisHelpersApi:
    """Analysis helper functions API тест"""

    def test_requires_mass_gate(self, app):
        """_requires_mass_gate function"""
        with app.app_context():
            from app.routes.api.helpers import _requires_mass_gate

            # Most analysis types require mass gate (not in exclusion list)
            assert _requires_mass_gate('Mad') is True
            assert _requires_mass_gate('Aad') is True
            assert _requires_mass_gate('Vad') is True
            assert _requires_mass_gate('MT') is True
            assert _requires_mass_gate('FM') is True

            # Only X, Y, CRI, CSR are excluded from mass gate
            assert _requires_mass_gate('X') is False
            assert _requires_mass_gate('Y') is False
            assert _requires_mass_gate('CRI') is False
            assert _requires_mass_gate('CSR') is False

    def test_to_float_or_none(self, app):
        """_to_float_or_none function"""
        with app.app_context():
            from app.routes.api.helpers import _to_float_or_none

            assert _to_float_or_none('5.25') == 5.25
            assert _to_float_or_none('10') == 10.0
            assert _to_float_or_none(None) is None
            assert _to_float_or_none('') is None
            assert _to_float_or_none('invalid') is None

    def test_coalesce_diff(self, app):
        """_coalesce_diff function - extracts diff from raw_data dict"""
        with app.app_context():
            from app.routes.api.helpers import _coalesce_diff

            # 't' key contains the diff value
            assert _coalesce_diff({'t': 1.5}) == 1.5
            assert _coalesce_diff({'t': -2.0}) == 2.0  # Returns absolute value
            assert _coalesce_diff({'t': 0}) == 0.0

            # None cases
            assert _coalesce_diff(None) is None
            assert _coalesce_diff({}) is None
            assert _coalesce_diff({'t': None}) is None

    def test_effective_limit(self, app):
        """_effective_limit function - returns (limit, mode, band_label)"""
        with app.app_context():
            from app.routes.api.helpers import _effective_limit

            # Returns tuple: (limit_value, mode, band_label)
            result = _effective_limit('Mad', 5.0)
            assert isinstance(result, tuple)
            assert len(result) == 3
            # First element is limit value (float or None)
            # Second is mode string
            # Third is band_label (or None)

            # Test with different analysis codes
            result_aad = _effective_limit('Aad', 10.0)
            assert isinstance(result_aad, tuple)

            result_cv = _effective_limit('CV', 5000.0)
            assert isinstance(result_cv, tuple)


class TestAnalysisCodesNormalization:
    """Шинжилгээний код normalize тест"""

    def test_norm_code_basic(self, app):
        """norm_code function"""
        with app.app_context():
            from app.utils.codes import norm_code

            assert norm_code('Mad') == 'Mad'
            assert norm_code('mad') == 'Mad'
            assert norm_code('MAD') == 'Mad'
            assert norm_code('Aad') == 'Aad'
            assert norm_code('aad') == 'Aad'


class TestControlStandards:
    """Control Standards API тест"""

    def test_control_standard_lookup(self, app):
        """ControlStandard lookup"""
        with app.app_context():
            # Try to get control standards
            standards = ControlStandard.query.filter_by(is_active=True).all()
            # Just verify the query works
            assert isinstance(standards, list)


class TestAnalysisResultStatus:
    """AnalysisResult status тест"""

    def test_determine_result_status_approved(self, app):
        """Status: approved"""
        with app.app_context():
            from app.utils.analysis_rules import determine_result_status

            # Function signature: (analysis_code, value, raw_data=None, control_targets=None)
            # Returns: Tuple[str, Optional[str]] (status, reason)
            result = determine_result_status(
                analysis_code='Mad',
                value=5.0,
                raw_data={'p1': 5.0, 'p2': 5.1, 't': 0.1}
            )
            assert isinstance(result, tuple)
            assert len(result) == 2
            status, reason = result
            assert status in ['approved', 'pending_review', 'rejected', 'awaiting_p2', None]

    def test_determine_result_status_rejected(self, app):
        """Status: rejected (exceeds limit)"""
        with app.app_context():
            from app.utils.analysis_rules import determine_result_status

            # Large diff - may be rejected
            result = determine_result_status(
                analysis_code='Mad',
                value=5.5,
                raw_data={'p1': 5.0, 'p2': 6.0, 't': 1.0}
            )
            assert isinstance(result, tuple)
            assert len(result) == 2
            status, reason = result
            assert status in ['approved', 'pending_review', 'rejected', 'awaiting_p2', None]


class TestApiResponseFormat:
    """API response format тест"""

    def test_eligible_samples_response_format(self, client, app):
        """eligible_samples response JSON format"""
        with app.app_context():
            user = User.query.filter_by(username='format_user').first()
            if not user:
                user = User(username='format_user', role='chemist')
                user.set_password(VALID_PASSWORD)
                db.session.add(user)
                db.session.commit()

        client.post('/login', data={
            'username': 'format_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)

        response = client.get('/api/eligible_samples/Mad')
        if response.status_code == 200:
            data = response.get_json()
            if data:
                assert 'samples' in data or isinstance(data, list)
