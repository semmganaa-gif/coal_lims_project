# tests/test_routes_equipment_batch.py
# -*- coding: utf-8 -*-
"""
Comprehensive tests for equipment routes (api, crud, registers) and api helpers.
Target: 80%+ coverage across all four files.
"""

import os
import json
import warnings
import pytest
from io import BytesIO
from math import inf
from datetime import datetime, date, timedelta
from unittest.mock import patch, MagicMock, PropertyMock

from sqlalchemy.exc import SQLAlchemyError, IntegrityError

from app import create_app, db
from app.models import User, Equipment, MaintenanceLog, UsageLog
from tests.conftest import TestConfig


# =====================================================================
# FIXTURES
# =====================================================================

@pytest.fixture
def eq_app():
    flask_app = create_app(TestConfig)
    flask_app.config['WTF_CSRF_ENABLED'] = False
    flask_app.config['SERVER_NAME'] = 'localhost'
    flask_app.config['UPLOAD_FOLDER'] = os.path.join(
        os.path.dirname(__file__), '_test_uploads_batch'
    )

    with flask_app.app_context():
        db.create_all()
        for role, uname in [('admin', 'btadmin'), ('senior', 'btsenior'), ('analyst', 'btanalyst')]:
            if not User.query.filter_by(username=uname).first():
                u = User(username=uname, role=role)
                u.set_password('Pass1234!@XY')
                db.session.add(u)
        db.session.commit()

    yield flask_app

    with flask_app.app_context():
        db.session.remove()
        db.drop_all()

    upload_dir = flask_app.config['UPLOAD_FOLDER']
    if os.path.exists(upload_dir):
        import shutil
        shutil.rmtree(upload_dir, ignore_errors=True)


@pytest.fixture
def admin_client(eq_app):
    client = eq_app.test_client()
    with eq_app.app_context():
        user = User.query.filter_by(username='btadmin').first()
        with client.session_transaction() as sess:
            sess['_user_id'] = str(user.id)
            sess['_fresh'] = True
    return client


@pytest.fixture
def senior_client(eq_app):
    client = eq_app.test_client()
    with eq_app.app_context():
        user = User.query.filter_by(username='btsenior').first()
        with client.session_transaction() as sess:
            sess['_user_id'] = str(user.id)
            sess['_fresh'] = True
    return client


@pytest.fixture
def analyst_client(eq_app):
    client = eq_app.test_client()
    with eq_app.app_context():
        user = User.query.filter_by(username='btanalyst').first()
        with client.session_transaction() as sess:
            sess['_user_id'] = str(user.id)
            sess['_fresh'] = True
    return client


@pytest.fixture
def sample_eq(eq_app):
    """Create a sample equipment record."""
    with eq_app.app_context():
        eq = Equipment(
            name='Test Furnace',
            manufacturer='TestMfg',
            model='TF-100',
            serial_number='SN001',
            lab_code='LC001',
            quantity=1,
            location='Lab A',
            room_number='101',
            related_analysis='Mad,Aad',
            status='normal',
            category='furnace',
            calibration_date=date(2025, 1, 1),
            next_calibration_date=date(2026, 1, 1),
            calibration_cycle_days=365,
            register_type='main',
        )
        db.session.add(eq)
        db.session.commit()
        eq_id = eq.id
    return eq_id


@pytest.fixture
def eq_with_history(eq_app):
    """Equipment with maintenance/usage history."""
    with eq_app.app_context():
        eq = Equipment(name='Old Furnace', status='normal', category='furnace')
        db.session.add(eq)
        db.session.flush()
        mlog = MaintenanceLog(
            equipment_id=eq.id,
            action_type='Calibration',
            description='Annual cal',
            action_date=datetime(2025, 6, 1),
        )
        db.session.add(mlog)
        db.session.commit()
        return eq.id


# =====================================================================
# FILE 4: app/routes/api/helpers.py  (pure function tests first)
# =====================================================================

class TestApiSuccess:
    def test_basic(self, eq_app):
        with eq_app.app_context():
            from app.routes.api.helpers import api_success
            resp = api_success()
            data = resp.get_json()
            assert data['success'] is True
            assert 'data' not in data

    def test_with_data_and_message(self, eq_app):
        with eq_app.app_context():
            from app.routes.api.helpers import api_success
            resp = api_success({'id': 1}, 'Created')
            data = resp.get_json()
            assert data['success'] is True
            assert data['data'] == {'id': 1}
            assert data['message'] == 'Created'

    def test_with_data_no_message(self, eq_app):
        with eq_app.app_context():
            from app.routes.api.helpers import api_success
            resp = api_success({'x': 2})
            data = resp.get_json()
            assert data['data'] == {'x': 2}
            assert 'message' not in data


class TestApiError:
    def test_basic(self, eq_app):
        with eq_app.app_context():
            from app.routes.api.helpers import api_error
            resp, status = api_error('Bad request')
            data = resp.get_json()
            assert data['success'] is False
            assert data['error'] == 'Bad request'
            assert status == 400

    def test_with_code_and_details(self, eq_app):
        with eq_app.app_context():
            from app.routes.api.helpers import api_error
            resp, status = api_error('Not found', code='NOT_FOUND', status_code=404, details={'id': 5})
            data = resp.get_json()
            assert data['code'] == 'NOT_FOUND'
            assert data['details'] == {'id': 5}
            assert status == 404

    def test_no_code_no_details(self, eq_app):
        with eq_app.app_context():
            from app.routes.api.helpers import api_error
            resp, status = api_error('err', status_code=500)
            data = resp.get_json()
            assert 'code' not in data
            assert 'details' not in data
            assert status == 500


class TestApiOkDeprecated:
    def test_api_ok_warns(self, eq_app):
        with eq_app.app_context():
            from app.routes.api.helpers import api_ok
            with warnings.catch_warnings(record=True) as w:
                warnings.simplefilter('always')
                resp = api_ok('Done', sample_id=42)
                assert len(w) == 1
                assert issubclass(w[0].category, DeprecationWarning)
            data = resp.get_json()
            assert data['ok'] is True
            assert data['message'] == 'Done'
            assert data['sample_id'] == 42

    def test_api_ok_no_message(self, eq_app):
        with eq_app.app_context():
            from app.routes.api.helpers import api_ok
            with warnings.catch_warnings(record=True):
                warnings.simplefilter('always')
                resp = api_ok()
            data = resp.get_json()
            assert data['ok'] is True
            assert 'message' not in data


class TestApiFailDeprecated:
    def test_api_fail_warns(self, eq_app):
        with eq_app.app_context():
            from app.routes.api.helpers import api_fail
            with warnings.catch_warnings(record=True) as w:
                warnings.simplefilter('always')
                resp, code = api_fail('Oops', 422, extra='val')
                assert len(w) == 1
                assert issubclass(w[0].category, DeprecationWarning)
            data = resp.get_json()
            assert data['ok'] is False
            assert data['message'] == 'Oops'
            assert data['extra'] == 'val'
            assert code == 422


class TestApiErrorCodes:
    def test_constants(self):
        from app.routes.api.helpers import ApiErrorCodes
        assert ApiErrorCodes.VALIDATION_ERROR == 'VALIDATION_ERROR'
        assert ApiErrorCodes.NOT_FOUND == 'NOT_FOUND'
        assert ApiErrorCodes.UNAUTHORIZED == 'UNAUTHORIZED'
        assert ApiErrorCodes.FORBIDDEN == 'FORBIDDEN'
        assert ApiErrorCodes.DUPLICATE == 'DUPLICATE'
        assert ApiErrorCodes.DATABASE_ERROR == 'DATABASE_ERROR'
        assert ApiErrorCodes.INTERNAL_ERROR == 'INTERNAL_ERROR'


class TestRequiresMassGate:
    def test_normal_code(self):
        from app.routes.api.helpers import _requires_mass_gate
        assert _requires_mass_gate('Mad') is True
        assert _requires_mass_gate('Aad') is True

    def test_excluded_codes(self):
        from app.routes.api.helpers import _requires_mass_gate
        assert _requires_mass_gate('X') is False
        assert _requires_mass_gate('Y') is False
        assert _requires_mass_gate('CRI') is False
        assert _requires_mass_gate('CSR') is False

    def test_none_empty(self):
        from app.routes.api.helpers import _requires_mass_gate
        assert _requires_mass_gate(None) is True
        assert _requires_mass_gate('') is True


class TestCanDeleteSample:
    def test_admin(self, eq_app):
        with eq_app.app_context():
            from app.routes.api.helpers import _can_delete_sample
            with patch('app.routes.api.helpers.current_user') as mock_u:
                mock_u.role = 'admin'
                assert _can_delete_sample() is True

    def test_senior(self, eq_app):
        with eq_app.app_context():
            from app.routes.api.helpers import _can_delete_sample
            with patch('app.routes.api.helpers.current_user') as mock_u:
                mock_u.role = 'senior'
                assert _can_delete_sample() is True

    def test_analyst(self, eq_app):
        with eq_app.app_context():
            from app.routes.api.helpers import _can_delete_sample
            with patch('app.routes.api.helpers.current_user') as mock_u:
                mock_u.role = 'analyst'
                assert _can_delete_sample() is False

    def test_no_role(self, eq_app):
        with eq_app.app_context():
            from app.routes.api.helpers import _can_delete_sample
            with patch('app.routes.api.helpers.current_user') as mock_u:
                type(mock_u).role = PropertyMock(side_effect=AttributeError)
                # getattr with default should return ""
                assert _can_delete_sample() is False


class TestAggregateSampleStatus:
    def test_archived(self):
        from app.routes.api.helpers import _aggregate_sample_status
        assert _aggregate_sample_status('archived', {'approved'}) == 'archived'

    def test_pending_review(self):
        from app.routes.api.helpers import _aggregate_sample_status
        assert _aggregate_sample_status('active', {'approved', 'pending_review'}) == 'pending_review'

    def test_rejected(self):
        from app.routes.api.helpers import _aggregate_sample_status
        assert _aggregate_sample_status('active', {'approved', 'rejected'}) == 'rejected'

    def test_approved(self):
        from app.routes.api.helpers import _aggregate_sample_status
        assert _aggregate_sample_status('active', {'approved'}) == 'approved'

    def test_no_statuses(self):
        from app.routes.api.helpers import _aggregate_sample_status
        assert _aggregate_sample_status('active', None) == 'active'
        assert _aggregate_sample_status('active', set()) == 'active'

    def test_empty_sample_status(self):
        from app.routes.api.helpers import _aggregate_sample_status
        assert _aggregate_sample_status(None, set()) == ''
        assert _aggregate_sample_status('', set()) == ''


class TestCoalesceDiff:
    def test_t_value(self):
        from app.routes.api.helpers import _coalesce_diff
        assert _coalesce_diff({'t': -2.5}) == 2.5

    def test_diff_value(self):
        from app.routes.api.helpers import _coalesce_diff
        assert _coalesce_diff({'diff': -1.3}) == 1.3

    def test_p1_p2_results(self):
        from app.routes.api.helpers import _coalesce_diff
        result = _coalesce_diff({'p1': {'result': 10.0}, 'p2': {'result': 8.5}})
        assert abs(result - 1.5) < 1e-9

    def test_none_raw(self):
        from app.routes.api.helpers import _coalesce_diff
        assert _coalesce_diff(None) is None
        assert _coalesce_diff({}) is None

    def test_partial_p1_p2(self):
        from app.routes.api.helpers import _coalesce_diff
        assert _coalesce_diff({'p1': {'result': 5.0}, 'p2': {}}) is None
        assert _coalesce_diff({'p1': {}, 'p2': {'result': 3.0}}) is None

    def test_t_takes_precedence(self):
        from app.routes.api.helpers import _coalesce_diff
        assert _coalesce_diff({'t': 1.0, 'diff': 2.0}) == 1.0


class TestPickRule:
    def test_known_code(self):
        from app.routes.api.helpers import _pick_rule
        rule = _pick_rule('CSN')
        assert 'single' in rule

    def test_unknown_code(self):
        from app.routes.api.helpers import _pick_rule
        assert _pick_rule('UNKNOWN_CODE_XYZ') == {}


class TestEffectiveLimit:
    def test_single_rule(self):
        from app.routes.api.helpers import _effective_limit
        limit, mode, band = _effective_limit('CSN', 5.0)
        assert limit == 0.60
        assert mode == 'abs'
        assert band is None

    def test_bands_low(self):
        from app.routes.api.helpers import _effective_limit
        # Aad: <=15 -> 0.20 abs
        limit, mode, band = _effective_limit('Aad', 10.0)
        assert limit == 0.20
        assert mode == 'abs'
        assert band is not None

    def test_bands_high(self):
        from app.routes.api.helpers import _effective_limit
        # Aad: >30 -> 0.50 abs  (upper=inf)
        limit, mode, band = _effective_limit('Aad', 50.0)
        assert limit == 0.50
        assert mode == 'abs'

    def test_bands_mid(self):
        from app.routes.api.helpers import _effective_limit
        # Aad: 15<x<=30 -> 0.30 abs
        limit, mode, band = _effective_limit('Aad', 20.0)
        assert limit == 0.30
        assert mode == 'abs'

    def test_unknown_code_fallback(self):
        from app.routes.api.helpers import _effective_limit
        limit, mode, band = _effective_limit('NONEXISTENT', 5.0)
        assert limit == 0.30
        assert mode == 'abs'

    def test_bands_with_none_avg(self):
        from app.routes.api.helpers import _effective_limit
        # bands but avg is None -> fallback
        limit, mode, band = _effective_limit('Aad', None)
        assert limit == 0.30
        assert mode == 'abs'

    def test_bands_detailed_takes_precedence(self):
        from app.routes.api.helpers import _effective_limit
        # Mad has bands_detailed
        limit, mode, band = _effective_limit('Mad', 0.3)
        assert limit == 0.20

    def test_percent_mode_band(self):
        from app.routes.api.helpers import _effective_limit
        # Cl has single percent
        limit, mode, band = _effective_limit('Cl', 100.0)
        assert mode == 'percent'


class TestShouldRequireReview:
    def test_gi_low_avg_no_retest(self):
        from app.routes.api.helpers import should_require_review
        assert should_require_review('Gi', {'is_low_avg': True}) is True

    def test_gi_low_avg_with_33_retest(self):
        from app.routes.api.helpers import should_require_review
        # retest_mode=3_3 -> should NOT trigger early return
        result = should_require_review('Gi', {'is_low_avg': True, 'retest_mode': '3_3', 'diff': 0.1, 'limit_used': 5.0})
        # diff < limit -> no review
        assert result is False

    def test_csn_with_limit_used(self):
        from app.routes.api.helpers import should_require_review
        # diff=0.5, limit=0.6 -> no review
        assert should_require_review('CSN', {'limit_used': 0.6, 'diff': 0.5}) is False
        # diff=0.8, limit=0.6 -> review
        assert should_require_review('CSN', {'limit_used': 0.6, 'diff': 0.8}) is True

    def test_csn_none_diff_limit(self):
        from app.routes.api.helpers import should_require_review
        # CSN with limit_used but no diff -> CSN sets diff=0, limit defaults
        result = should_require_review('CSN', {'limit_used': 0.6})
        # diff=0, limit=0.6 -> 0 - 0.6 = -0.6 < EPS -> False
        assert result is False

    def test_trd_limit_used(self):
        from app.routes.api.helpers import should_require_review
        assert should_require_review('TRD', {'limit_used': 0.02, 'diff': 0.03}) is True
        assert should_require_review('TRD', {'limit_used': 0.02, 'diff': 0.01}) is False

    def test_cv_limit_used(self):
        from app.routes.api.helpers import should_require_review
        assert should_require_review('CV', {'limit_used': 120.0, 'diff': 130.0}) is True
        assert should_require_review('CV', {'limit_used': 120.0, 'diff': 100.0}) is False

    def test_csn_t_exceeded_fallback(self):
        from app.routes.api.helpers import should_require_review
        # No limit_used, but has t_exceeded
        assert should_require_review('CSN', {'t_exceeded': True}) is True
        assert should_require_review('CSN', {'t_exceeded': False}) is False

    def test_gi_t_exceeded_fallback(self):
        from app.routes.api.helpers import should_require_review
        assert should_require_review('Gi', {'t_exceeded': True}) is True

    def test_normal_code_diff_under_limit(self):
        from app.routes.api.helpers import should_require_review
        # Aad avg=10, diff=0.1 -> limit=0.20 -> 0.1 < 0.20 -> no review
        assert should_require_review('Aad', {'avg': 10.0, 'diff': 0.1}) is False

    def test_normal_code_diff_over_limit(self):
        from app.routes.api.helpers import should_require_review
        # Aad avg=10, diff=0.5 -> limit=0.20 -> 0.5 > 0.20 -> review
        assert should_require_review('Aad', {'avg': 10.0, 'diff': 0.5}) is True

    def test_no_diff_returns_true(self):
        from app.routes.api.helpers import should_require_review
        assert should_require_review('Aad', {'avg': 10.0}) is True

    def test_percent_mode(self):
        from app.routes.api.helpers import should_require_review
        # Cl percent mode: limit=0.10 -> effective = avg * 0.10
        # avg=100, diff=5 -> effective=10 -> 5 < 10 -> no review
        assert should_require_review('Cl', {'avg': 100.0, 'diff': 5.0}) is False
        # avg=100, diff=15 -> effective=10 -> 15 > 10 -> review
        assert should_require_review('Cl', {'avg': 100.0, 'diff': 15.0}) is True

    def test_gi_with_limit_used_none_diff_none_limit(self):
        from app.routes.api.helpers import should_require_review
        # Gi with limit_used present but no diff/t -> diff=None, limit not None -> return True
        result = should_require_review('Gi', {'limit_used': 3.0})
        assert result is True


class TestHasMTaskSql:
    def test_returns_expression(self, eq_app):
        with eq_app.app_context():
            from app.routes.api.helpers import _has_m_task_sql
            expr = _has_m_task_sql()
            assert expr is not None


class TestRunSync:
    @pytest.mark.asyncio
    async def test_run_sync_basic(self, eq_app):
        with eq_app.app_context():
            from app.routes.api.helpers import run_sync
            result = await run_sync(lambda: 42)
            assert result == 42

    @pytest.mark.asyncio
    async def test_run_sync_with_args(self, eq_app):
        with eq_app.app_context():
            from app.routes.api.helpers import run_sync
            result = await run_sync(lambda x, y: x + y, 3, 4)
            assert result == 7

    @pytest.mark.asyncio
    async def test_run_sync_with_kwargs(self, eq_app):
        with eq_app.app_context():
            from app.routes.api.helpers import run_sync

            def fn(a, b=10):
                return a + b

            result = await run_sync(fn, 5, b=20)
            assert result == 25


# =====================================================================
# FILE 1: app/routes/equipment/api.py
# =====================================================================

class TestLogUsageBulk:
    def test_empty_items(self, admin_client, eq_app):
        with eq_app.app_context():
            resp = admin_client.post(
                '/api/log_usage_bulk',
                json={'items': []},
                content_type='application/json',
            )
            data = resp.get_json()
            assert data['success'] is False

    def test_no_json(self, admin_client, eq_app):
        with eq_app.app_context():
            resp = admin_client.post(
                '/api/log_usage_bulk',
                json={},
                content_type='application/json',
            )
            data = resp.get_json()
            assert data['success'] is False

    def test_too_many_items(self, admin_client, eq_app):
        with eq_app.app_context():
            items = [{'eq_id': i} for i in range(101)]
            resp = admin_client.post(
                '/api/log_usage_bulk',
                json={'items': items},
                content_type='application/json',
            )
            data = resp.get_json()
            assert data['success'] is False

    @patch('app.routes.equipment.api.process_bulk_usage_items')
    def test_success(self, mock_bulk, admin_client, eq_app):
        mock_bulk.return_value = (True, 2, None)
        with eq_app.app_context():
            resp = admin_client.post(
                '/api/log_usage_bulk',
                json={'items': [{'eq_id': 1}, {'eq_id': 2}]},
                content_type='application/json',
            )
            data = resp.get_json()
            assert data['success'] is True
            assert data['data']['count'] == 2

    @patch('app.routes.equipment.api.process_bulk_usage_items')
    def test_service_error(self, mock_bulk, admin_client, eq_app):
        mock_bulk.return_value = (False, 0, 'DB error')
        with eq_app.app_context():
            resp = admin_client.post(
                '/api/log_usage_bulk',
                json={'items': [{'eq_id': 1}]},
                content_type='application/json',
            )
            data = resp.get_json()
            assert data['success'] is False

    @patch('app.routes.equipment.api.process_bulk_usage_items')
    def test_exception(self, mock_bulk, admin_client, eq_app):
        mock_bulk.side_effect = ValueError('bad')
        with eq_app.app_context():
            resp = admin_client.post(
                '/api/log_usage_bulk',
                json={'items': [{'eq_id': 1}]},
                content_type='application/json',
            )
            data = resp.get_json()
            assert data['success'] is False


class TestUsageSummaryApi:
    @patch('app.routes.equipment.api.get_usage_summary')
    def test_with_dates(self, mock_summary, admin_client, eq_app):
        mock_summary.return_value = [{'name': 'X', 'count': 5}]
        with eq_app.app_context():
            resp = admin_client.get(
                '/api/equipment/usage_summary?start_date=2025-01-01&end_date=2025-06-30&category=furnace'
            )
            data = resp.get_json()
            assert 'rows' in data
            assert data['start_date'] == '2025-01-01'
            assert data['end_date'] == '2025-06-30'

    @patch('app.routes.equipment.api.get_usage_summary')
    def test_no_dates(self, mock_summary, admin_client, eq_app):
        mock_summary.return_value = []
        with eq_app.app_context():
            resp = admin_client.get('/api/equipment/usage_summary')
            data = resp.get_json()
            assert 'rows' in data
            # Should default to 30 days ago

    @patch('app.routes.equipment.api.get_usage_summary')
    def test_invalid_dates(self, mock_summary, admin_client, eq_app):
        mock_summary.return_value = []
        with eq_app.app_context():
            resp = admin_client.get(
                '/api/equipment/usage_summary?start_date=bad&end_date=bad'
            )
            data = resp.get_json()
            assert 'rows' in data


class TestJournalDetailedApi:
    @patch('app.routes.equipment.api.get_journal_detailed')
    def test_with_dates_and_equipment_id(self, mock_jd, admin_client, eq_app):
        mock_jd.return_value = [{'log': 1}]
        with eq_app.app_context():
            resp = admin_client.get(
                '/api/equipment/journal_detailed?start_date=2025-01-01&end_date=2025-06-30&equipment_id=5'
            )
            data = resp.get_json()
            assert 'rows' in data
            mock_jd.assert_called_once()
            args = mock_jd.call_args
            assert args[0][3] == 5  # equipment_id

    @patch('app.routes.equipment.api.get_journal_detailed')
    def test_no_dates(self, mock_jd, admin_client, eq_app):
        mock_jd.return_value = []
        with eq_app.app_context():
            resp = admin_client.get('/api/equipment/journal_detailed')
            data = resp.get_json()
            assert 'rows' in data

    @patch('app.routes.equipment.api.get_journal_detailed')
    def test_invalid_dates(self, mock_jd, admin_client, eq_app):
        mock_jd.return_value = []
        with eq_app.app_context():
            resp = admin_client.get(
                '/api/equipment/journal_detailed?start_date=xxx&end_date=yyy'
            )
            data = resp.get_json()
            assert 'rows' in data


class TestMonthlyStatsApi:
    @patch('app.routes.equipment.api.get_monthly_stats')
    def test_with_year(self, mock_ms, admin_client, eq_app):
        mock_ms.return_value = [{'month': 1, 'count': 10}]
        with eq_app.app_context():
            resp = admin_client.get('/api/equipment/monthly_stats?year=2025')
            data = resp.get_json()
            assert data['year'] == 2025

    @patch('app.routes.equipment.api.get_monthly_stats')
    def test_no_year(self, mock_ms, admin_client, eq_app):
        mock_ms.return_value = []
        with eq_app.app_context():
            resp = admin_client.get('/api/equipment/monthly_stats')
            data = resp.get_json()
            assert 'year' in data

    @patch('app.routes.equipment.api.get_monthly_stats')
    def test_invalid_year(self, mock_ms, admin_client, eq_app):
        mock_ms.return_value = []
        with eq_app.app_context():
            resp = admin_client.get('/api/equipment/monthly_stats?year=abc')
            data = resp.get_json()
            assert 'year' in data


class TestEquipmentListJson:
    def test_basic(self, admin_client, eq_app, sample_eq):
        with eq_app.app_context():
            resp = admin_client.get('/api/equipment_list_json')
            data = resp.get_json()
            assert isinstance(data, list)
            assert len(data) >= 1
            item = data[0]
            assert 'id' in item
            assert 'is_expired' in item

    def test_include_retired(self, admin_client, eq_app):
        with eq_app.app_context():
            eq = Equipment(name='Retired Equip', status='retired', category='other')
            db.session.add(eq)
            db.session.commit()
            # Without retired
            resp1 = admin_client.get('/api/equipment_list_json')
            data1 = resp1.get_json()
            names1 = [d['name'] for d in data1]
            assert 'Retired Equip' not in names1
            # With retired
            resp2 = admin_client.get('/api/equipment_list_json?include_retired=true')
            data2 = resp2.get_json()
            names2 = [d['name'] for d in data2]
            assert 'Retired Equip' in names2

    def test_expired_calibration(self, admin_client, eq_app):
        with eq_app.app_context():
            eq = Equipment(
                name='Expired Cal',
                status='normal',
                category='other',
                next_calibration_date=date(2020, 1, 1),
            )
            db.session.add(eq)
            db.session.commit()

            resp = admin_client.get('/api/equipment_list_json')
            data = resp.get_json()
            expired_items = [d for d in data if d['name'] == 'Expired Cal']
            assert len(expired_items) == 1
            assert expired_items[0]['is_expired'] is True

    def test_no_calibration_date(self, admin_client, eq_app):
        with eq_app.app_context():
            eq = Equipment(name='No Cal', status='normal', category='other')
            db.session.add(eq)
            db.session.commit()
            resp = admin_client.get('/api/equipment_list_json')
            data = resp.get_json()
            no_cal = [d for d in data if d['name'] == 'No Cal']
            assert no_cal[0]['is_expired'] is False
            assert no_cal[0]['calibration_date'] == ''


# =====================================================================
# FILE 2: app/routes/equipment/crud.py
# =====================================================================

class TestEquipmentList:
    def test_all_view(self, admin_client, eq_app, sample_eq):
        with eq_app.app_context():
            resp = admin_client.get('/equipment_list')
            assert resp.status_code == 200

    def test_retired_view(self, admin_client, eq_app):
        with eq_app.app_context():
            resp = admin_client.get('/equipment_list?view=retired')
            assert resp.status_code == 200

    def test_spares_view(self, admin_client, eq_app):
        with eq_app.app_context():
            resp = admin_client.get('/equipment_list?view=spares')
            assert resp.status_code == 200

    def test_coal_view(self, admin_client, eq_app):
        with eq_app.app_context():
            resp = admin_client.get('/equipment_list?view=coal')
            assert resp.status_code == 200

    def test_new_view(self, admin_client, eq_app):
        with eq_app.app_context():
            resp = admin_client.get('/equipment_list?view=new')
            assert resp.status_code == 200

    def test_category_view(self, admin_client, eq_app):
        with eq_app.app_context():
            resp = admin_client.get('/equipment_list?view=furnace')
            assert resp.status_code == 200


class TestEquipmentDetail:
    def test_exists(self, admin_client, eq_app, sample_eq):
        with eq_app.app_context():
            resp = admin_client.get(f'/equipment/{sample_eq}')
            assert resp.status_code == 200

    def test_not_found(self, admin_client, eq_app):
        with eq_app.app_context():
            resp = admin_client.get('/equipment/99999')
            assert resp.status_code == 404


class TestEquipmentJournalPage:
    def test_exists(self, admin_client, eq_app, sample_eq):
        with eq_app.app_context():
            resp = admin_client.get(f'/equipment/{sample_eq}/journal')
            assert resp.status_code == 200

    def test_not_found(self, admin_client, eq_app):
        with eq_app.app_context():
            resp = admin_client.get('/equipment/99999/journal')
            assert resp.status_code == 404


class TestAddEquipment:
    def test_success(self, admin_client, eq_app):
        with eq_app.app_context():
            resp = admin_client.post('/add_equipment', data={
                'name': 'New Eq',
                'manufacturer': 'Mfg',
                'model': 'M1',
                'serial': 'S1',
                'lab_code': 'L1',
                'quantity': '2',
                'cycle': '180',
                'location': 'Lab B',
                'room': '202',
                'related': 'St,d',
                'category': 'analysis',
                'register_type': 'main',
                'calibration_date': '2025-06-01',
                'next_calibration_date': '2025-12-01',
                'chk_checked': 'Yes',
                'chk_calibrated': 'Done',
                'manufactured_info': '2020',
                'commissioned_info': '2021',
                'remark': 'test remark',
            }, follow_redirects=True)
            assert resp.status_code == 200
            eq = Equipment.query.filter_by(name='New Eq').first()
            assert eq is not None
            assert eq.quantity == 2

    def test_bad_quantity(self, admin_client, eq_app):
        with eq_app.app_context():
            resp = admin_client.post('/add_equipment', data={
                'name': 'Bad Qty',
                'quantity': 'abc',
            }, follow_redirects=True)
            assert resp.status_code == 200

    def test_zero_quantity(self, admin_client, eq_app):
        with eq_app.app_context():
            resp = admin_client.post('/add_equipment', data={
                'name': 'Zero Qty',
                'quantity': '0',
            }, follow_redirects=True)
            assert resp.status_code == 200

    def test_bad_cycle(self, admin_client, eq_app):
        with eq_app.app_context():
            resp = admin_client.post('/add_equipment', data={
                'name': 'Bad Cycle',
                'quantity': '1',
                'cycle': 'abc',
            }, follow_redirects=True)
            assert resp.status_code == 200

    def test_zero_cycle(self, admin_client, eq_app):
        with eq_app.app_context():
            resp = admin_client.post('/add_equipment', data={
                'name': 'Zero Cycle',
                'quantity': '1',
                'cycle': '0',
            }, follow_redirects=True)
            assert resp.status_code == 200

    def test_analyst_denied(self, analyst_client, eq_app):
        with eq_app.app_context():
            resp = analyst_client.post('/add_equipment', data={
                'name': 'Denied',
                'quantity': '1',
            }, follow_redirects=True)
            assert resp.status_code == 200

    def test_invalid_dates(self, admin_client, eq_app):
        with eq_app.app_context():
            resp = admin_client.post('/add_equipment', data={
                'name': 'Bad Dates',
                'quantity': '1',
                'cycle': '365',
                'calibration_date': 'not-a-date',
                'next_calibration_date': 'also-bad',
            }, follow_redirects=True)
            assert resp.status_code == 200
            eq = Equipment.query.filter_by(name='Bad Dates').first()
            assert eq is not None
            assert eq.calibration_date is None
            assert eq.next_calibration_date is None

    def test_register_type_with_extra_data(self, admin_client, eq_app):
        with eq_app.app_context():
            resp = admin_client.post('/add_equipment', data={
                'name': 'Register Eq',
                'quantity': '1',
                'cycle': '365',
                'register_type': 'measurement',
                'range_info': '0-100C',
                'accuracy': '0.1',
            }, follow_redirects=True)
            assert resp.status_code == 200
            eq = Equipment.query.filter_by(name='Register Eq').first()
            assert eq is not None
            assert eq.extra_data is not None
            assert 'range_info' in eq.extra_data

    @patch('app.routes.equipment.crud.db.session.commit', side_effect=SQLAlchemyError('DB fail'))
    @patch('app.routes.equipment.crud.log_audit')
    def test_db_error(self, mock_audit, mock_commit, admin_client, eq_app):
        with eq_app.app_context():
            resp = admin_client.post('/add_equipment', data={
                'name': 'DB Err',
                'quantity': '1',
                'cycle': '365',
            }, follow_redirects=True)
            assert resp.status_code == 200


class TestEditEquipment:
    def test_success(self, admin_client, eq_app, sample_eq):
        with eq_app.app_context():
            resp = admin_client.post(f'/edit_equipment/{sample_eq}', data={
                'name': 'Updated Furnace',
                'manufacturer': 'NewMfg',
                'model': 'TF-200',
                'serial': 'SN002',
                'lab_code': 'LC002',
                'location': 'Lab C',
                'room': '303',
                'related': 'Vdaf',
                'cycle': '180',
                'status': 'maintenance',
                'calibration_note': 'Updated note',
                'remark': 'Updated remark',
                'category': 'prep',
                'register_type': 'main',
                'calibration_date': '2025-06-15',
                'next_calibration_date': '2025-12-15',
                'quantity': '3',
                'manufactured_info': '2019',
                'commissioned_info': '2020',
                'initial_price': '1000.50',
                'residual_price': '500.25',
            }, follow_redirects=True)
            assert resp.status_code == 200

    def test_not_found(self, admin_client, eq_app):
        with eq_app.app_context():
            resp = admin_client.post('/edit_equipment/99999', data={'name': 'X'})
            assert resp.status_code == 404

    def test_analyst_denied(self, analyst_client, eq_app, sample_eq):
        with eq_app.app_context():
            resp = analyst_client.post(f'/edit_equipment/{sample_eq}', data={
                'name': 'Denied Edit',
            }, follow_redirects=True)
            assert resp.status_code == 200

    def test_bad_cycle(self, admin_client, eq_app, sample_eq):
        with eq_app.app_context():
            resp = admin_client.post(f'/edit_equipment/{sample_eq}', data={
                'name': 'CycleErr',
                'cycle': 'bad',
            }, follow_redirects=True)
            assert resp.status_code == 200

    def test_zero_cycle(self, admin_client, eq_app, sample_eq):
        with eq_app.app_context():
            resp = admin_client.post(f'/edit_equipment/{sample_eq}', data={
                'name': 'ZeroCycle',
                'cycle': '0',
            }, follow_redirects=True)
            assert resp.status_code == 200

    def test_clear_dates(self, admin_client, eq_app, sample_eq):
        with eq_app.app_context():
            resp = admin_client.post(f'/edit_equipment/{sample_eq}', data={
                'name': 'ClearDates',
                'calibration_date': '',
                'next_calibration_date': '',
            }, follow_redirects=True)
            assert resp.status_code == 200
            eq = db.session.get(Equipment, sample_eq)
            assert eq.calibration_date is None
            assert eq.next_calibration_date is None

    def test_invalid_dates(self, admin_client, eq_app, sample_eq):
        with eq_app.app_context():
            resp = admin_client.post(f'/edit_equipment/{sample_eq}', data={
                'name': 'InvalidDates',
                'calibration_date': 'bad-date',
                'next_calibration_date': 'also-bad',
            }, follow_redirects=True)
            assert resp.status_code == 200

    def test_no_serial_no_cycle(self, admin_client, eq_app, sample_eq):
        with eq_app.app_context():
            resp = admin_client.post(f'/edit_equipment/{sample_eq}', data={
                'name': 'NoSerial',
                # no serial, no cycle, no status, no quantity fields
            }, follow_redirects=True)
            assert resp.status_code == 200

    def test_bad_quantity(self, admin_client, eq_app, sample_eq):
        with eq_app.app_context():
            resp = admin_client.post(f'/edit_equipment/{sample_eq}', data={
                'name': 'BadQty',
                'quantity': 'abc',
            }, follow_redirects=True)
            assert resp.status_code == 200

    def test_bad_prices(self, admin_client, eq_app, sample_eq):
        with eq_app.app_context():
            resp = admin_client.post(f'/edit_equipment/{sample_eq}', data={
                'name': 'BadPrices',
                'initial_price': 'not-a-number',
                'residual_price': 'bad',
            }, follow_redirects=True)
            assert resp.status_code == 200

    def test_extra_data_fields(self, admin_client, eq_app, sample_eq):
        with eq_app.app_context():
            resp = admin_client.post(f'/edit_equipment/{sample_eq}', data={
                'name': 'ExtraFields',
                'register_type': 'measurement',
                'custom_field': 'custom_val',
            }, follow_redirects=True)
            assert resp.status_code == 200
            eq = db.session.get(Equipment, sample_eq)
            assert eq.extra_data is not None
            assert 'custom_field' in eq.extra_data

    @patch('app.routes.equipment.crud.db.session.commit', side_effect=IntegrityError('dup', {}, None))
    @patch('app.routes.equipment.crud.log_audit')
    def test_integrity_error(self, mock_audit, mock_commit, admin_client, eq_app, sample_eq):
        with eq_app.app_context():
            resp = admin_client.post(f'/edit_equipment/{sample_eq}', data={
                'name': 'IntegrityErr',
            }, follow_redirects=True)
            assert resp.status_code == 200

    @patch('app.routes.equipment.crud.db.session.commit', side_effect=SQLAlchemyError('db err'))
    @patch('app.routes.equipment.crud.log_audit')
    def test_sqlalchemy_error(self, mock_audit, mock_commit, admin_client, eq_app, sample_eq):
        with eq_app.app_context():
            resp = admin_client.post(f'/edit_equipment/{sample_eq}', data={
                'name': 'SqlErr',
            }, follow_redirects=True)
            assert resp.status_code == 200


class TestDeleteEquipment:
    def test_delete_no_history(self, admin_client, eq_app):
        with eq_app.app_context():
            eq = Equipment(name='ToDelete', status='normal', category='other')
            db.session.add(eq)
            db.session.commit()
            eq_id = eq.id
            resp = admin_client.post(f'/equipment/delete/{eq_id}', follow_redirects=True)
            assert resp.status_code == 200
            assert db.session.get(Equipment, eq_id) is None

    def test_retire_with_history(self, admin_client, eq_app, eq_with_history):
        with eq_app.app_context():
            resp = admin_client.post(f'/equipment/delete/{eq_with_history}', follow_redirects=True)
            assert resp.status_code == 200
            eq = db.session.get(Equipment, eq_with_history)
            assert eq.status == 'retired'

    def test_not_found(self, admin_client, eq_app):
        with eq_app.app_context():
            resp = admin_client.post('/equipment/delete/99999')
            assert resp.status_code == 404

    def test_analyst_denied(self, analyst_client, eq_app, sample_eq):
        with eq_app.app_context():
            resp = analyst_client.post(f'/equipment/delete/{sample_eq}', follow_redirects=True)
            assert resp.status_code == 200

    @patch('app.routes.equipment.crud.db.session.commit', side_effect=SQLAlchemyError('fail'))
    @patch('app.routes.equipment.crud.log_audit')
    def test_db_error(self, mock_audit, mock_commit, admin_client, eq_app, sample_eq):
        with eq_app.app_context():
            resp = admin_client.post(f'/equipment/delete/{sample_eq}', follow_redirects=True)
            assert resp.status_code == 200


class TestBulkDelete:
    def test_success_mixed(self, admin_client, eq_app, eq_with_history):
        with eq_app.app_context():
            eq_no_hist = Equipment(name='NoHist', status='normal', category='other')
            db.session.add(eq_no_hist)
            db.session.commit()
            no_hist_id = eq_no_hist.id
            resp = admin_client.post('/bulk_delete', data={
                'equipment_ids': [str(eq_with_history), str(no_hist_id)],
            }, follow_redirects=True)
            assert resp.status_code == 200

    def test_no_ids(self, admin_client, eq_app):
        with eq_app.app_context():
            resp = admin_client.post('/bulk_delete', data={}, follow_redirects=True)
            assert resp.status_code == 200

    def test_analyst_denied(self, analyst_client, eq_app):
        with eq_app.app_context():
            resp = analyst_client.post('/bulk_delete', data={
                'equipment_ids': ['1'],
            }, follow_redirects=True)
            assert resp.status_code == 200

    def test_nonexistent_ids(self, admin_client, eq_app):
        with eq_app.app_context():
            resp = admin_client.post('/bulk_delete', data={
                'equipment_ids': ['99999'],
            }, follow_redirects=True)
            assert resp.status_code == 200

    @patch('app.routes.equipment.crud.db.session.commit', side_effect=SQLAlchemyError('bulk fail'))
    @patch('app.routes.equipment.crud.log_audit')
    def test_db_error(self, mock_audit, mock_commit, admin_client, eq_app, sample_eq):
        with eq_app.app_context():
            resp = admin_client.post('/bulk_delete', data={
                'equipment_ids': [str(sample_eq)],
            }, follow_redirects=True)
            assert resp.status_code == 200


class TestAddMaintenanceLog:
    def test_calibration_log(self, admin_client, eq_app, sample_eq):
        with eq_app.app_context():
            resp = admin_client.post(f'/add_log/{sample_eq}', data={
                'action_type': 'Calibration',
                'description': 'Annual calibration',
                'performed_by': 'tech1',
                'certificate_no': 'CERT-001',
                'action_date': '2025-06-15',
            }, follow_redirects=True)
            assert resp.status_code == 200
            eq = db.session.get(Equipment, sample_eq)
            assert eq.calibration_date == date(2025, 6, 15)

    def test_repair_log(self, admin_client, eq_app, sample_eq):
        with eq_app.app_context():
            resp = admin_client.post(f'/add_log/{sample_eq}', data={
                'action_type': 'Repair',
                'description': 'Motor replacement',
                'action_date': '2025-07-01',
            }, follow_redirects=True)
            assert resp.status_code == 200
            eq = db.session.get(Equipment, sample_eq)
            assert eq.status == 'maintenance'

    def test_usage_log(self, admin_client, eq_app, sample_eq):
        with eq_app.app_context():
            resp = admin_client.post(f'/add_log/{sample_eq}', data={
                'action_type': 'Usage',
                'description': 'Sample analysis',
                'duration_minutes': '60',
                'performed_by': 'user1',
                'action_date': '2025-06-20',
            }, follow_redirects=True)
            assert resp.status_code == 200

    def test_usage_log_bad_minutes(self, admin_client, eq_app, sample_eq):
        with eq_app.app_context():
            resp = admin_client.post(f'/add_log/{sample_eq}', data={
                'action_type': 'Usage',
                'duration_minutes': 'bad',
            }, follow_redirects=True)
            assert resp.status_code == 200

    def test_not_found(self, admin_client, eq_app):
        with eq_app.app_context():
            resp = admin_client.post('/add_log/99999', data={'action_type': 'Repair'})
            assert resp.status_code == 404

    def test_no_action_date(self, admin_client, eq_app, sample_eq):
        with eq_app.app_context():
            resp = admin_client.post(f'/add_log/{sample_eq}', data={
                'action_type': 'Inspection',
                'description': 'Routine',
            }, follow_redirects=True)
            assert resp.status_code == 200

    def test_invalid_action_date(self, admin_client, eq_app, sample_eq):
        with eq_app.app_context():
            resp = admin_client.post(f'/add_log/{sample_eq}', data={
                'action_type': 'Inspection',
                'action_date': 'not-a-date',
            }, follow_redirects=True)
            assert resp.status_code == 200

    def test_file_upload_valid(self, admin_client, eq_app, sample_eq):
        with eq_app.app_context():
            data = {
                'action_type': 'Calibration',
                'description': 'With cert',
                'certificate_file': (BytesIO(b'PDF content'), 'cert.pdf'),
            }
            resp = admin_client.post(
                f'/add_log/{sample_eq}',
                data=data,
                content_type='multipart/form-data',
                follow_redirects=True,
            )
            assert resp.status_code == 200

    def test_file_upload_too_large(self, admin_client, eq_app, sample_eq):
        with eq_app.app_context():
            big_content = b'x' * (6 * 1024 * 1024)  # 6MB > 5MB
            data = {
                'action_type': 'Calibration',
                'certificate_file': (BytesIO(big_content), 'big.pdf'),
            }
            resp = admin_client.post(
                f'/add_log/{sample_eq}',
                data=data,
                content_type='multipart/form-data',
                follow_redirects=True,
            )
            assert resp.status_code == 200

    def test_file_upload_no_extension(self, admin_client, eq_app, sample_eq):
        with eq_app.app_context():
            data = {
                'action_type': 'Calibration',
                'certificate_file': (BytesIO(b'data'), 'noext'),
            }
            resp = admin_client.post(
                f'/add_log/{sample_eq}',
                data=data,
                content_type='multipart/form-data',
                follow_redirects=True,
            )
            assert resp.status_code == 200

    def test_file_upload_bad_extension(self, admin_client, eq_app, sample_eq):
        with eq_app.app_context():
            data = {
                'action_type': 'Calibration',
                'certificate_file': (BytesIO(b'data'), 'virus.exe'),
            }
            resp = admin_client.post(
                f'/add_log/{sample_eq}',
                data=data,
                content_type='multipart/form-data',
                follow_redirects=True,
            )
            assert resp.status_code == 200

    def test_calibration_retired_status_preserved(self, admin_client, eq_app):
        with eq_app.app_context():
            eq = Equipment(name='Retired Cal', status='retired', category='furnace',
                           calibration_cycle_days=365)
            db.session.add(eq)
            db.session.commit()
            eq_id = eq.id
            resp = admin_client.post(f'/add_log/{eq_id}', data={
                'action_type': 'Calibration',
                'action_date': '2025-06-01',
            }, follow_redirects=True)
            assert resp.status_code == 200
            eq = db.session.get(Equipment, eq_id)
            assert eq.status == 'retired'

    def test_next_url_from_form(self, admin_client, eq_app, sample_eq):
        with eq_app.app_context():
            resp = admin_client.post(f'/add_log/{sample_eq}', data={
                'action_type': 'Inspection',
                'next': '/equipment_list',
            }, follow_redirects=True)
            assert resp.status_code == 200

    @patch('app.routes.equipment.crud.db.session.commit', side_effect=SQLAlchemyError('usage db err'))
    @patch('app.routes.equipment.crud.log_audit')
    def test_usage_log_db_error(self, mock_audit, mock_commit, admin_client, eq_app, sample_eq):
        with eq_app.app_context():
            resp = admin_client.post(f'/add_log/{sample_eq}', data={
                'action_type': 'Usage',
                'duration_minutes': '30',
            }, follow_redirects=True)
            assert resp.status_code == 200

    @patch('app.routes.equipment.crud.db.session.commit', side_effect=SQLAlchemyError('maint db err'))
    @patch('app.routes.equipment.crud.log_audit')
    def test_maintenance_log_db_error(self, mock_audit, mock_commit, admin_client, eq_app, sample_eq):
        with eq_app.app_context():
            resp = admin_client.post(f'/add_log/{sample_eq}', data={
                'action_type': 'Inspection',
            }, follow_redirects=True)
            assert resp.status_code == 200


class TestDownloadCertificate:
    def test_not_found(self, admin_client, eq_app):
        with eq_app.app_context():
            resp = admin_client.get('/download_cert/99999')
            assert resp.status_code == 404

    def test_no_file_path(self, admin_client, eq_app, sample_eq):
        with eq_app.app_context():
            log = MaintenanceLog(
                equipment_id=sample_eq,
                action_type='Inspection',
                action_date=datetime(2025, 1, 1),
                file_path=None,
            )
            db.session.add(log)
            db.session.commit()
            resp = admin_client.get(f'/download_cert/{log.id}', follow_redirects=True)
            assert resp.status_code == 200

    def test_file_not_exists(self, admin_client, eq_app, sample_eq):
        with eq_app.app_context():
            log = MaintenanceLog(
                equipment_id=sample_eq,
                action_type='Inspection',
                action_date=datetime(2025, 1, 1),
                file_path='nonexistent_file.pdf',
            )
            db.session.add(log)
            db.session.commit()
            resp = admin_client.get(f'/download_cert/{log.id}', follow_redirects=True)
            assert resp.status_code == 200

    def test_file_exists_and_downloads(self, admin_client, eq_app, sample_eq):
        with eq_app.app_context():
            upload_folder = eq_app.config['UPLOAD_FOLDER']
            os.makedirs(upload_folder, exist_ok=True)
            test_file = os.path.join(upload_folder, 'test_cert.pdf')
            with open(test_file, 'wb') as f:
                f.write(b'%PDF-1.4 test content')

            log = MaintenanceLog(
                equipment_id=sample_eq,
                action_type='Calibration',
                action_date=datetime(2025, 1, 1),
                file_path='test_cert.pdf',
            )
            db.session.add(log)
            db.session.commit()

            resp = admin_client.get(f'/download_cert/{log.id}')
            assert resp.status_code == 200

    def test_path_traversal_blocked(self, admin_client, eq_app, sample_eq):
        with eq_app.app_context():
            log = MaintenanceLog(
                equipment_id=sample_eq,
                action_type='Calibration',
                action_date=datetime(2025, 1, 1),
                file_path='../../etc/passwd',
            )
            db.session.add(log)
            db.session.commit()

            # The basename will strip the path traversal; file won't exist
            resp = admin_client.get(f'/download_cert/{log.id}', follow_redirects=True)
            assert resp.status_code == 200  # redirected with flash


# =====================================================================
# FILE 3: app/routes/equipment/registers.py
# =====================================================================

class TestEquipmentJournalHub:
    def test_hub(self, admin_client, eq_app):
        with eq_app.app_context():
            resp = admin_client.get('/equipment_journal')
            assert resp.status_code == 200


class TestEquipmentJournalGrid:
    def test_default_category(self, admin_client, eq_app):
        with eq_app.app_context():
            resp = admin_client.get('/equipment_journal/grid')
            assert resp.status_code == 200

    def test_specific_category(self, admin_client, eq_app):
        with eq_app.app_context():
            resp = admin_client.get('/equipment_journal/grid?category=furnace')
            assert resp.status_code == 200

    def test_unknown_category(self, admin_client, eq_app):
        with eq_app.app_context():
            resp = admin_client.get('/equipment_journal/grid?category=unknown_cat')
            assert resp.status_code == 200


class TestEquipmentJournalSpecial:
    def test_spares_redirect(self, admin_client, eq_app):
        with eq_app.app_context():
            resp = admin_client.get('/equipment_journal/spares_register')
            assert resp.status_code == 302

    def test_measurement(self, admin_client, eq_app):
        with eq_app.app_context():
            resp = admin_client.get('/equipment_journal/measurement')
            assert resp.status_code == 200

    def test_glassware(self, admin_client, eq_app):
        with eq_app.app_context():
            resp = admin_client.get('/equipment_journal/glassware')
            assert resp.status_code == 200

    def test_internal_check(self, admin_client, eq_app):
        with eq_app.app_context():
            resp = admin_client.get('/equipment_journal/internal_check')
            assert resp.status_code == 200

    def test_new_equipment(self, admin_client, eq_app):
        with eq_app.app_context():
            # Add equipment with commissioned_info
            eq = Equipment(name='Commissioned', status='normal', category='other',
                           commissioned_info='2025-01-01')
            db.session.add(eq)
            db.session.commit()
            resp = admin_client.get('/equipment_journal/new_equipment')
            assert resp.status_code == 200

    def test_out_of_service(self, admin_client, eq_app):
        with eq_app.app_context():
            eq = Equipment(name='Retired One', status='retired', category='other')
            db.session.add(eq)
            db.session.commit()
            resp = admin_client.get('/equipment_journal/out_of_service')
            assert resp.status_code == 200

    def test_balances_register(self, admin_client, eq_app):
        with eq_app.app_context():
            eq = Equipment(name='Balance X', status='normal', category='balance')
            db.session.add(eq)
            db.session.commit()
            resp = admin_client.get('/equipment_journal/balances_register')
            assert resp.status_code == 200

    def test_unknown_journal_type(self, admin_client, eq_app):
        with eq_app.app_context():
            resp = admin_client.get('/equipment_journal/unknown_type', follow_redirects=True)
            assert resp.status_code == 200

    def test_items_with_extra_data(self, admin_client, eq_app):
        with eq_app.app_context():
            eq = Equipment(
                name='Measurement Tool',
                status='normal',
                category='other',
                register_type='measurement',
                quantity=5,
                extra_data={'range': '0-100', 'accuracy': '0.01'},
            )
            db.session.add(eq)
            db.session.commit()
            resp = admin_client.get('/equipment_journal/measurement')
            assert resp.status_code == 200

    def test_items_without_extra_data(self, admin_client, eq_app):
        with eq_app.app_context():
            eq = Equipment(
                name='Simple Tool',
                status='normal',
                category='other',
                register_type='glassware',
                quantity=3,
                extra_data=None,
            )
            db.session.add(eq)
            db.session.commit()
            resp = admin_client.get('/equipment_journal/glassware')
            assert resp.status_code == 200


class TestAddRegisterItem:
    def test_success(self, admin_client, eq_app):
        with eq_app.app_context():
            resp = admin_client.post('/add_register_item/measurement', data={
                'name': 'New Gauge',
                'manufacturer': 'GaugeCo',
                'model': 'G100',
                'serial_number': 'GS001',
                'lab_code': 'GL01',
                'quantity': '2',
                'location': 'Lab D',
                'remark': 'Test',
                'range_info': '0-200',
            }, follow_redirects=True)
            assert resp.status_code == 200
            eq = Equipment.query.filter_by(name='New Gauge').first()
            assert eq is not None
            assert eq.register_type == 'measurement'
            assert eq.quantity == 2
            assert eq.extra_data is not None
            assert 'range_info' in eq.extra_data

    def test_qty_alias(self, admin_client, eq_app):
        with eq_app.app_context():
            resp = admin_client.post('/add_register_item/glassware', data={
                'name': 'Beaker',
                'qty': '10',
            }, follow_redirects=True)
            assert resp.status_code == 200
            eq = Equipment.query.filter_by(name='Beaker').first()
            assert eq.quantity == 10

    def test_bad_quantity(self, admin_client, eq_app):
        with eq_app.app_context():
            resp = admin_client.post('/add_register_item/measurement', data={
                'name': 'BadQty',
                'quantity': 'abc',
            }, follow_redirects=True)
            assert resp.status_code == 200

    def test_analyst_denied(self, analyst_client, eq_app):
        with eq_app.app_context():
            resp = analyst_client.post('/add_register_item/measurement', data={
                'name': 'Denied',
            }, follow_redirects=True)
            assert resp.status_code == 200

    @patch('app.routes.equipment.registers.db.session.commit', side_effect=SQLAlchemyError('err'))
    def test_db_error(self, mock_commit, admin_client, eq_app):
        with eq_app.app_context():
            resp = admin_client.post('/add_register_item/measurement', data={
                'name': 'DbErr',
            }, follow_redirects=True)
            assert resp.status_code == 200

    def test_no_extra_data(self, admin_client, eq_app):
        with eq_app.app_context():
            resp = admin_client.post('/add_register_item/measurement', data={
                'name': 'NoExtra',
                'manufacturer': 'X',
                'model': 'Y',
                'serial_number': 'Z',
                'lab_code': 'L',
                'quantity': '1',
                'location': 'A',
                'remark': 'B',
            }, follow_redirects=True)
            assert resp.status_code == 200
            eq = Equipment.query.filter_by(name='NoExtra').first()
            assert eq.extra_data is None


class TestEditRegisterItem:
    def test_success(self, admin_client, eq_app):
        with eq_app.app_context():
            eq = Equipment(name='EditMe', register_type='measurement', status='normal', category='other')
            db.session.add(eq)
            db.session.commit()
            eq_id = eq.id

            resp = admin_client.post(f'/edit_register_item/{eq_id}', data={
                'name': 'Edited',
                'manufacturer': 'NewMfg',
                'model': 'NewModel',
                'serial_number': 'NS1',
                'lab_code': 'NL1',
                'quantity': '5',
                'location': 'NewLoc',
                'remark': 'Updated',
                'custom_field': 'custom_val',
            }, follow_redirects=True)
            assert resp.status_code == 200
            eq = db.session.get(Equipment, eq_id)
            assert eq.name == 'Edited'
            assert eq.quantity == 5

    def test_not_found(self, admin_client, eq_app):
        with eq_app.app_context():
            resp = admin_client.post('/edit_register_item/99999', data={'name': 'X'})
            assert resp.status_code == 404

    def test_analyst_denied(self, analyst_client, eq_app, sample_eq):
        with eq_app.app_context():
            resp = analyst_client.post(f'/edit_register_item/{sample_eq}', data={
                'name': 'Denied',
            }, follow_redirects=True)
            assert resp.status_code == 200

    def test_qty_alias(self, admin_client, eq_app):
        with eq_app.app_context():
            eq = Equipment(name='QtyAlias', register_type='glassware', status='normal', category='other')
            db.session.add(eq)
            db.session.commit()
            eq_id = eq.id

            resp = admin_client.post(f'/edit_register_item/{eq_id}', data={
                'name': 'QtyAlias',
                'qty': '7',
            }, follow_redirects=True)
            assert resp.status_code == 200
            eq = db.session.get(Equipment, eq_id)
            assert eq.quantity == 7

    def test_bad_quantity(self, admin_client, eq_app):
        with eq_app.app_context():
            eq = Equipment(name='BadQtyEdit', register_type='measurement', status='normal',
                           category='other', quantity=1)
            db.session.add(eq)
            db.session.commit()
            eq_id = eq.id

            resp = admin_client.post(f'/edit_register_item/{eq_id}', data={
                'name': 'BadQtyEdit',
                'quantity': 'bad',
            }, follow_redirects=True)
            assert resp.status_code == 200

    @patch('app.routes.equipment.registers.db.session.commit', side_effect=SQLAlchemyError('edit err'))
    def test_db_error(self, mock_commit, admin_client, eq_app):
        with eq_app.app_context():
            eq = Equipment(name='EditDbErr', register_type='measurement', status='normal', category='other')
            db.session.add(eq)
            # Force flush to get ID without commit mock interfering
            db.session.flush()
            eq_id = eq.id
            # Reset mock for test - the flush above won't trigger it since we mock commit
            mock_commit.reset_mock()
            mock_commit.side_effect = SQLAlchemyError('edit err')

            resp = admin_client.post(f'/edit_register_item/{eq_id}', data={
                'name': 'EditDbErr Updated',
            }, follow_redirects=True)
            assert resp.status_code == 200

    def test_no_extra_data(self, admin_client, eq_app):
        with eq_app.app_context():
            eq = Equipment(name='NoExtraEdit', register_type='measurement', status='normal',
                           category='other', quantity=1)
            db.session.add(eq)
            db.session.commit()
            eq_id = eq.id

            resp = admin_client.post(f'/edit_register_item/{eq_id}', data={
                'name': 'NoExtraEdit',
                'manufacturer': 'M',
                'model': 'Mo',
                'serial_number': 'S',
                'lab_code': 'L',
                'quantity': '1',
                'location': 'Lo',
                'remark': 'R',
            }, follow_redirects=True)
            assert resp.status_code == 200
            eq = db.session.get(Equipment, eq_id)
            assert eq.extra_data is None


class TestDeleteRegisterItems:
    def test_success(self, admin_client, eq_app):
        with eq_app.app_context():
            eq1 = Equipment(name='Del1', register_type='measurement', status='normal', category='other')
            eq2 = Equipment(name='Del2', register_type='measurement', status='normal', category='other')
            db.session.add_all([eq1, eq2])
            db.session.commit()

            resp = admin_client.post('/delete_register_items', data={
                'item_ids': [str(eq1.id), str(eq2.id)],
                'register_type': 'measurement',
            }, follow_redirects=True)
            assert resp.status_code == 200

    def test_no_ids(self, admin_client, eq_app):
        with eq_app.app_context():
            resp = admin_client.post('/delete_register_items', data={
                'register_type': 'measurement',
            }, follow_redirects=True)
            assert resp.status_code == 200

    def test_mismatched_register_type(self, admin_client, eq_app):
        with eq_app.app_context():
            eq = Equipment(name='WrongType', register_type='glassware', status='normal', category='other')
            db.session.add(eq)
            db.session.commit()

            resp = admin_client.post('/delete_register_items', data={
                'item_ids': [str(eq.id)],
                'register_type': 'measurement',  # Does not match glassware
            }, follow_redirects=True)
            assert resp.status_code == 200
            # Should NOT be deleted because register_type doesn't match
            assert db.session.get(Equipment, eq.id) is not None

    def test_analyst_denied(self, analyst_client, eq_app):
        with eq_app.app_context():
            resp = analyst_client.post('/delete_register_items', data={
                'item_ids': ['1'],
                'register_type': 'measurement',
            }, follow_redirects=True)
            assert resp.status_code == 200

    @patch('app.routes.equipment.registers.db.session.commit', side_effect=SQLAlchemyError('del err'))
    def test_db_error(self, mock_commit, admin_client, eq_app):
        with eq_app.app_context():
            eq = Equipment(name='DelErr', register_type='measurement', status='normal', category='other')
            db.session.add(eq)
            db.session.flush()
            eq_id = eq.id
            mock_commit.reset_mock()
            mock_commit.side_effect = SQLAlchemyError('del err')

            resp = admin_client.post('/delete_register_items', data={
                'item_ids': [str(eq_id)],
                'register_type': 'measurement',
            }, follow_redirects=True)
            assert resp.status_code == 200
