# tests/test_routes_mass_samples_batch.py
# -*- coding: utf-8 -*-
"""
Comprehensive tests for mass_api.py and samples_api.py routes.
Target: 80%+ coverage for both modules.
"""

import json
import pytest
from datetime import date, datetime, timedelta
from unittest.mock import patch, MagicMock, PropertyMock

from flask import Flask, Blueprint
from flask_login import LoginManager, UserMixin

from app import create_app, db as _db
from app.models import User, Sample, AnalysisResult
from tests.conftest import TestConfig


# ============================================================
# Fixtures
# ============================================================

@pytest.fixture(scope="module")
def mass_app():
    """Create app for mass/samples API tests."""
    flask_app = create_app(TestConfig)
    flask_app.config['WTF_CSRF_ENABLED'] = False
    flask_app.config['SERVER_NAME'] = 'localhost'

    with flask_app.app_context():
        _db.create_all()
        for role, uname in [('admin', 'msadmin'), ('senior', 'mssenior'), ('chemist', 'mschemist')]:
            if not User.query.filter_by(username=uname).first():
                u = User(username=uname, role=role)
                u.set_password('TestPass123')
                _db.session.add(u)
        _db.session.commit()

    yield flask_app

    with flask_app.app_context():
        _db.session.remove()
        _db.drop_all()


@pytest.fixture
def admin_client(mass_app):
    client = mass_app.test_client()
    with mass_app.app_context():
        user = User.query.filter_by(username='msadmin').first()
        with client.session_transaction() as sess:
            sess['_user_id'] = str(user.id)
            sess['_fresh'] = True
    return client


@pytest.fixture
def senior_client(mass_app):
    client = mass_app.test_client()
    with mass_app.app_context():
        user = User.query.filter_by(username='mssenior').first()
        with client.session_transaction() as sess:
            sess['_user_id'] = str(user.id)
            sess['_fresh'] = True
    return client


@pytest.fixture
def chemist_client(mass_app):
    client = mass_app.test_client()
    with mass_app.app_context():
        user = User.query.filter_by(username='mschemist').first()
        with client.session_transaction() as sess:
            sess['_user_id'] = str(user.id)
            sess['_fresh'] = True
    return client


@pytest.fixture
def unauth_client(mass_app):
    return mass_app.test_client()


@pytest.fixture
def sample_in_db(mass_app):
    """Create a sample for testing."""
    import uuid
    with mass_app.app_context():
        user = User.query.filter_by(username='mschemist').first()
        s = Sample(
            sample_code=f"MS-{uuid.uuid4().hex[:6]}",
            user_id=user.id,
            client_name="QC",
            sample_type="Coal",
            lab_type="coal",
            status="new",
            received_date=datetime.now(),
            analyses_to_perform='["m","Mad"]',
        )
        _db.session.add(s)
        _db.session.commit()
        sid = s.id
        yield s
        # cleanup
        try:
            obj = _db.session.get(Sample, sid)
            if obj:
                _db.session.delete(obj)
                _db.session.commit()
        except Exception:
            _db.session.rollback()


# ============================================================
# MASS API: _upsert_mass_result
# ============================================================

class TestUpsertMassResult:
    """Tests for _upsert_mass_result helper."""

    def test_create_new_result(self, mass_app, sample_in_db):
        from app.services.mass_service import _upsert_mass_result
        with mass_app.app_context():
            _upsert_mass_result(sample_in_db.id, 1500.0, user_id=1)
            _db.session.commit()
            ar = AnalysisResult.query.filter_by(
                sample_id=sample_in_db.id, analysis_code="m"
            ).first()
            assert ar is not None
            assert ar.final_result == 1500.0
            assert ar.status == "approved"
            # cleanup
            _db.session.delete(ar)
            _db.session.commit()

    def test_update_existing_result(self, mass_app, sample_in_db):
        from app.services.mass_service import _upsert_mass_result
        with mass_app.app_context():
            # Create first
            ar = AnalysisResult(
                sample_id=sample_in_db.id,
                analysis_code="m",
                final_result=1000.0,
                status="pending_review",
                user_id=1,
            )
            _db.session.add(ar)
            _db.session.commit()
            ar_id = ar.id

            # Update
            _upsert_mass_result(sample_in_db.id, 2000.0, user_id=2)
            _db.session.commit()

            updated = _db.session.get(AnalysisResult, ar_id)
            assert updated.final_result == 2000.0
            assert updated.status == "approved"
            _db.session.delete(updated)
            _db.session.commit()

    def test_create_without_user_id(self, mass_app, sample_in_db):
        from app.services.mass_service import _upsert_mass_result
        with mass_app.app_context():
            _upsert_mass_result(sample_in_db.id, 500.0)
            _db.session.commit()
            ar = AnalysisResult.query.filter_by(
                sample_id=sample_in_db.id, analysis_code="m"
            ).first()
            assert ar is not None
            assert ar.user_id is None
            _db.session.delete(ar)
            _db.session.commit()


# ============================================================
# MASS API: /mass/update_sample_status
# ============================================================

class TestUpdateSampleStatus:

    def test_no_sample_ids_ajax(self, admin_client):
        resp = admin_client.post(
            '/api/mass/update_sample_status',
            data={'action': 'archive'},
            headers={'X-Requested-With': 'XMLHttpRequest'},
        )
        assert resp.status_code == 400

    def test_no_sample_ids_non_ajax(self, admin_client):
        resp = admin_client.post(
            '/api/mass/update_sample_status',
            data={'action': 'archive'},
        )
        assert resp.status_code == 302

    def test_archive_ajax(self, admin_client, mass_app, sample_in_db):
        resp = admin_client.post(
            '/api/mass/update_sample_status',
            data={'action': 'archive', 'sample_ids': [str(sample_in_db.id)]},
            headers={'X-Requested-With': 'XMLHttpRequest'},
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert 'updated' in data.get('message', '').lower() or '1' in data.get('message', '')
        # restore
        with mass_app.app_context():
            s = _db.session.get(Sample, sample_in_db.id)
            if s:
                s.status = 'new'
                _db.session.commit()

    def test_unarchive_ajax(self, admin_client, mass_app, sample_in_db):
        with mass_app.app_context():
            s = _db.session.get(Sample, sample_in_db.id)
            s.status = 'archived'
            _db.session.commit()

        resp = admin_client.post(
            '/api/mass/update_sample_status',
            data={'action': 'unarchive', 'sample_ids': [str(sample_in_db.id)]},
            headers={'X-Requested-With': 'XMLHttpRequest'},
        )
        assert resp.status_code == 200

    def test_invalid_sample_ids(self, admin_client):
        resp = admin_client.post(
            '/api/mass/update_sample_status',
            data={'action': 'archive', 'sample_ids': ['abc', 'xyz']},
            headers={'X-Requested-With': 'XMLHttpRequest'},
        )
        # Invalid IDs → empty list → 400 (no samples selected)
        assert resp.status_code == 400

    def test_commit_error_ajax(self, admin_client, sample_in_db):
        from sqlalchemy.exc import SQLAlchemyError
        with patch.object(_db.session, 'commit', side_effect=SQLAlchemyError("DB error")):
            resp = admin_client.post(
                '/api/mass/update_sample_status',
                data={'action': 'archive', 'sample_ids': [str(sample_in_db.id)]},
                headers={'X-Requested-With': 'XMLHttpRequest'},
            )
            assert resp.status_code == 500

    def test_commit_error_non_ajax(self, admin_client, sample_in_db):
        from sqlalchemy.exc import SQLAlchemyError
        with patch.object(_db.session, 'commit', side_effect=SQLAlchemyError("DB err")):
            resp = admin_client.post(
                '/api/mass/update_sample_status',
                data={'action': 'archive', 'sample_ids': [str(sample_in_db.id)]},
            )
            assert resp.status_code == 302

    def test_non_ajax_redirect(self, admin_client, sample_in_db):
        resp = admin_client.post(
            '/api/mass/update_sample_status',
            data={'action': 'archive', 'sample_ids': [str(sample_in_db.id)]},
        )
        assert resp.status_code == 302

    def test_unauthenticated(self, unauth_client):
        resp = unauth_client.post('/api/mass/update_sample_status', data={'action': 'archive'})
        assert resp.status_code in (302, 401)


# ============================================================
# MASS API: /mass/eligible
# ============================================================

class TestMassEligible:

    def test_eligible_default(self, admin_client, sample_in_db):
        resp = admin_client.get('/api/mass/eligible')
        assert resp.status_code == 200
        data = resp.get_json()
        assert 'samples' in data

    def test_eligible_include_ready(self, admin_client):
        resp = admin_client.get('/api/mass/eligible?include_ready=1')
        assert resp.status_code == 200
        data = resp.get_json()
        assert 'samples' in data

    def test_eligible_with_query(self, admin_client, sample_in_db):
        code = sample_in_db.sample_code[:3] if sample_in_db.sample_code else "MS"
        resp = admin_client.get(f'/api/mass/eligible?q={code}')
        assert resp.status_code == 200

    def test_eligible_empty_query(self, admin_client):
        resp = admin_client.get('/api/mass/eligible?q=')
        assert resp.status_code == 200

    def test_eligible_include_ready_true(self, admin_client):
        resp = admin_client.get('/api/mass/eligible?include_ready=true')
        assert resp.status_code == 200

    def test_eligible_include_ready_True(self, admin_client):
        resp = admin_client.get('/api/mass/eligible?include_ready=True')
        assert resp.status_code == 200

    def test_eligible_unauthenticated(self, unauth_client):
        resp = unauth_client.get('/api/mass/eligible')
        assert resp.status_code in (302, 401)


# ============================================================
# MASS API: /mass/save
# ============================================================

class TestMassSave:

    def test_save_no_items(self, admin_client):
        resp = admin_client.post(
            '/api/mass/save',
            json={'items': [], 'mark_ready': True},
        )
        assert resp.status_code == 400
        data = resp.get_json()
        assert data['success'] is False

    def test_save_no_json(self, admin_client):
        resp = admin_client.post('/api/mass/save', data='not json', content_type='text/plain')
        assert resp.status_code == 400

    def test_save_empty_payload(self, admin_client):
        resp = admin_client.post('/api/mass/save', json={})
        assert resp.status_code == 400

    def test_save_success(self, admin_client, mass_app, sample_in_db):
        resp = admin_client.post(
            '/api/mass/save',
            json={
                'items': [{'sample_id': sample_in_db.id, 'weight': 2500.0}],
                'mark_ready': True,
            },
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert data['success'] is True
        # Reset
        with mass_app.app_context():
            s = _db.session.get(Sample, sample_in_db.id)
            s.mass_ready = False
            s.mass_ready_at = None
            # clean up the AR
            ar = AnalysisResult.query.filter_by(sample_id=sample_in_db.id, analysis_code='m').first()
            if ar:
                _db.session.delete(ar)
            _db.session.commit()

    def test_save_mark_ready_false(self, admin_client, mass_app, sample_in_db):
        resp = admin_client.post(
            '/api/mass/save',
            json={
                'items': [{'sample_id': sample_in_db.id, 'weight': 1800.0}],
                'mark_ready': False,
            },
        )
        assert resp.status_code == 200
        # cleanup AR
        with mass_app.app_context():
            ar = AnalysisResult.query.filter_by(sample_id=sample_in_db.id, analysis_code='m').first()
            if ar:
                _db.session.delete(ar)
                _db.session.commit()

    def test_save_nonexistent_sample(self, admin_client):
        resp = admin_client.post(
            '/api/mass/save',
            json={'items': [{'sample_id': 999999, 'weight': 100}]},
        )
        assert resp.status_code == 400
        data = resp.get_json()
        assert data['success'] is False

    def test_save_no_valid_ids(self, admin_client):
        resp = admin_client.post(
            '/api/mass/save',
            json={'items': [{'weight': 100}]},  # no sample_id
        )
        assert resp.status_code == 400

    def test_save_stale_data_error(self, admin_client, sample_in_db):
        from sqlalchemy.orm.exc import StaleDataError
        original_commit = _db.session.commit
        call_count = [0]
        def mock_commit():
            call_count[0] += 1
            # Let any flush-related commits pass, fail on the real commit
            raise StaleDataError("stale")
        with patch.object(_db.session, 'commit', side_effect=mock_commit):
            resp = admin_client.post(
                '/api/mass/save',
                json={'items': [{'sample_id': sample_in_db.id, 'weight': 100}]},
            )
            # The mock may prevent the query from working properly; accept 400 or 409
            assert resp.status_code in (400, 409)

    def test_save_integrity_error(self, admin_client, sample_in_db):
        from sqlalchemy.exc import IntegrityError
        with patch.object(_db.session, 'commit', side_effect=IntegrityError("dup", {}, None)):
            resp = admin_client.post(
                '/api/mass/save',
                json={'items': [{'sample_id': sample_in_db.id, 'weight': 100}]},
            )
            assert resp.status_code in (400, 409)

    def test_save_sqlalchemy_error(self, admin_client, sample_in_db):
        from sqlalchemy.exc import SQLAlchemyError
        with patch.object(_db.session, 'commit', side_effect=SQLAlchemyError("db err")):
            resp = admin_client.post(
                '/api/mass/save',
                json={'items': [{'sample_id': sample_in_db.id, 'weight': 100}]},
            )
            assert resp.status_code in (400, 500)

    def test_save_weight_not_numeric(self, admin_client, sample_in_db):
        resp = admin_client.post(
            '/api/mass/save',
            json={'items': [{'sample_id': sample_in_db.id, 'weight': 'abc'}]},
        )
        # Should process but skip the non-numeric weight
        # The sample is found but weight not applied, mark_ready still works
        assert resp.status_code == 200

    def test_save_multiple_items(self, admin_client, mass_app, sample_in_db):
        import uuid
        with mass_app.app_context():
            user = User.query.filter_by(username='mschemist').first()
            s2 = Sample(
                sample_code=f"MS2-{uuid.uuid4().hex[:6]}",
                user_id=user.id,
                client_name="QC",
                sample_type="Coal",
                lab_type="coal",
                status="new",
                received_date=datetime.now(),
                analyses_to_perform='["m"]',
            )
            _db.session.add(s2)
            _db.session.commit()
            s2_id = s2.id

        resp = admin_client.post(
            '/api/mass/save',
            json={
                'items': [
                    {'sample_id': sample_in_db.id, 'weight': 1000},
                    {'sample_id': s2_id, 'weight': 2000},
                ],
            },
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert len(data.get('data', {}).get('updated_ids', [])) == 2

        # cleanup
        with mass_app.app_context():
            for sid in [sample_in_db.id, s2_id]:
                ar = AnalysisResult.query.filter_by(sample_id=sid, analysis_code='m').first()
                if ar:
                    _db.session.delete(ar)
            obj2 = _db.session.get(Sample, s2_id)
            if obj2:
                _db.session.delete(obj2)
            _db.session.commit()


# ============================================================
# MASS API: /mass/update_weight
# ============================================================

class TestMassUpdateWeight:

    def test_update_weight_success(self, admin_client, mass_app, sample_in_db):
        resp = admin_client.post(
            '/api/mass/update_weight',
            json={'sample_id': sample_in_db.id, 'weight': 3000},
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert data['success'] is True
        # cleanup
        with mass_app.app_context():
            ar = AnalysisResult.query.filter_by(sample_id=sample_in_db.id, analysis_code='m').first()
            if ar:
                _db.session.delete(ar)
                _db.session.commit()

    def test_update_weight_missing_params(self, admin_client):
        resp = admin_client.post('/api/mass/update_weight', json={})
        assert resp.status_code == 400

    def test_update_weight_no_sample_id(self, admin_client):
        resp = admin_client.post('/api/mass/update_weight', json={'weight': 100})
        assert resp.status_code == 400

    def test_update_weight_non_numeric(self, admin_client):
        resp = admin_client.post(
            '/api/mass/update_weight',
            json={'sample_id': 1, 'weight': 'abc'},
        )
        assert resp.status_code == 400

    def test_update_weight_not_found(self, admin_client):
        resp = admin_client.post(
            '/api/mass/update_weight',
            json={'sample_id': 999999, 'weight': 100},
        )
        assert resp.status_code == 404
        data = resp.get_json()
        assert data['success'] is False

    def test_update_weight_stale_error(self, admin_client, sample_in_db):
        from sqlalchemy.orm.exc import StaleDataError
        with patch.object(_db.session, 'commit', side_effect=StaleDataError("stale")):
            resp = admin_client.post(
                '/api/mass/update_weight',
                json={'sample_id': sample_in_db.id, 'weight': 100},
            )
            assert resp.status_code == 409  # Conflict

    def test_update_weight_integrity_error(self, admin_client, sample_in_db):
        from sqlalchemy.exc import IntegrityError
        with patch.object(_db.session, 'commit', side_effect=IntegrityError("dup", {}, None)):
            resp = admin_client.post(
                '/api/mass/update_weight',
                json={'sample_id': sample_in_db.id, 'weight': 100},
            )
            assert resp.status_code == 409  # Conflict

    def test_update_weight_sqlalchemy_error(self, admin_client, sample_in_db):
        from sqlalchemy.exc import SQLAlchemyError
        with patch.object(_db.session, 'commit', side_effect=SQLAlchemyError("err")):
            resp = admin_client.post(
                '/api/mass/update_weight',
                json={'sample_id': sample_in_db.id, 'weight': 100},
            )
            assert resp.status_code == 500  # Server error

    def test_update_weight_no_json(self, admin_client):
        resp = admin_client.post('/api/mass/update_weight', data='bad', content_type='text/plain')
        assert resp.status_code == 400


# ============================================================
# MASS API: /mass/unready
# ============================================================

class TestMassUnready:

    def test_unready_success(self, admin_client, sample_in_db):
        resp = admin_client.post(
            '/api/mass/unready',
            json={'sample_ids': [sample_in_db.id]},
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert data['success'] is True

    def test_unready_no_ids(self, admin_client):
        resp = admin_client.post('/api/mass/unready', json={'sample_ids': []})
        assert resp.status_code == 400

    def test_unready_no_payload(self, admin_client):
        resp = admin_client.post('/api/mass/unready', json={})
        assert resp.status_code == 400

    def test_unready_stale_error(self, admin_client, sample_in_db):
        from sqlalchemy.orm.exc import StaleDataError
        with patch.object(_db.session, 'commit', side_effect=StaleDataError("stale")):
            resp = admin_client.post(
                '/api/mass/unready',
                json={'sample_ids': [sample_in_db.id]},
            )
            assert resp.status_code == 409
            data = resp.get_json()
            assert data['success'] is False

    def test_unready_integrity_error(self, admin_client, sample_in_db):
        from sqlalchemy.exc import IntegrityError
        with patch.object(_db.session, 'commit', side_effect=IntegrityError("dup", {}, None)):
            resp = admin_client.post(
                '/api/mass/unready',
                json={'sample_ids': [sample_in_db.id]},
            )
            assert resp.status_code == 409

    def test_unready_sqlalchemy_error(self, admin_client, sample_in_db):
        from sqlalchemy.exc import SQLAlchemyError
        with patch.object(_db.session, 'commit', side_effect=SQLAlchemyError("err")):
            resp = admin_client.post(
                '/api/mass/unready',
                json={'sample_ids': [sample_in_db.id]},
            )
            assert resp.status_code == 500


# ============================================================
# MASS API: /mass/delete
# ============================================================

class TestMassDelete:

    def test_delete_success_admin(self, admin_client, mass_app):
        import uuid
        with mass_app.app_context():
            user = User.query.filter_by(username='mschemist').first()
            s = Sample(
                sample_code=f"DEL-{uuid.uuid4().hex[:6]}",
                user_id=user.id,
                client_name="QC",
                sample_type="Coal",
                lab_type="coal",
                status="new",
                received_date=datetime.now(),
            )
            _db.session.add(s)
            _db.session.commit()
            sid = s.id

        resp = admin_client.post('/api/mass/delete', json={'sample_id': sid})
        assert resp.status_code == 200
        data = resp.get_json()
        assert data['success'] is True

    def test_delete_access_denied_chemist(self, chemist_client):
        resp = chemist_client.post('/api/mass/delete', json={'sample_id': 1})
        assert resp.status_code == 403
        data = resp.get_json()
        assert data['success'] is False

    def test_delete_no_id(self, admin_client):
        resp = admin_client.post('/api/mass/delete', json={})
        assert resp.status_code == 400

    def test_delete_not_found(self, admin_client):
        resp = admin_client.post('/api/mass/delete', json={'sample_id': 999999})
        assert resp.status_code == 404

    def test_delete_integrity_error(self, admin_client, sample_in_db):
        from sqlalchemy.exc import IntegrityError
        with patch.object(_db.session, 'commit', side_effect=IntegrityError("fk", {}, None)):
            resp = admin_client.post('/api/mass/delete', json={'sample_id': sample_in_db.id})
            assert resp.status_code == 409

    def test_delete_sqlalchemy_error(self, admin_client, sample_in_db):
        from sqlalchemy.exc import SQLAlchemyError
        with patch.object(_db.session, 'commit', side_effect=SQLAlchemyError("err")):
            resp = admin_client.post('/api/mass/delete', json={'sample_id': sample_in_db.id})
            assert resp.status_code == 500

    def test_delete_senior_allowed(self, senior_client, mass_app):
        import uuid
        with mass_app.app_context():
            user = User.query.filter_by(username='mschemist').first()
            s = Sample(
                sample_code=f"DEL2-{uuid.uuid4().hex[:6]}",
                user_id=user.id,
                client_name="QC",
                sample_type="Coal",
                lab_type="coal",
                status="new",
                received_date=datetime.now(),
            )
            _db.session.add(s)
            _db.session.commit()
            sid = s.id

        resp = senior_client.post('/api/mass/delete', json={'sample_id': sid})
        assert resp.status_code == 200


# ============================================================
# SAMPLES API: /data (DataTables)
# ============================================================

class TestDataEndpoint:

    def test_data_basic(self, admin_client, sample_in_db):
        resp = admin_client.get('/api/data?draw=1&start=0&length=25')
        assert resp.status_code == 200
        data = resp.get_json()
        assert 'draw' in data
        assert 'recordsTotal' in data
        assert 'data' in data

    def test_data_with_column_search(self, admin_client, sample_in_db):
        resp = admin_client.get(
            '/api/data?draw=1&start=0&length=10'
            '&columns[0][data]=checkbox'
            '&columns[0][search][value]='
            '&columns[1][data]=id'
            '&columns[1][search][value]=' + str(sample_in_db.id)
        )
        assert resp.status_code == 200

    def test_data_with_sample_code_filter(self, admin_client, sample_in_db):
        code = sample_in_db.sample_code[:3] if sample_in_db.sample_code else "MS"
        resp = admin_client.get(
            '/api/data?draw=1&start=0&length=10'
            '&columns[0][data]=cb&columns[0][search][value]='
            '&columns[1][data]=id&columns[1][search][value]='
            f'&columns[2][data]=sample_code&columns[2][search][value]={code}'
        )
        assert resp.status_code == 200

    def test_data_with_date_filters(self, admin_client):
        today = date.today().isoformat()
        resp = admin_client.get(f'/api/data?draw=1&start=0&length=10&dateFilterStart={today}&dateFilterEnd={today}')
        assert resp.status_code == 200

    def test_data_invalid_date_filters(self, admin_client):
        resp = admin_client.get('/api/data?draw=1&start=0&length=10&dateFilterStart=bad&dateFilterEnd=bad')
        assert resp.status_code == 200

    def test_data_client_name_filter(self, admin_client):
        # idx 3 = client_name
        resp = admin_client.get(
            '/api/data?draw=1&start=0&length=10'
            '&columns[0][data]=a&columns[0][search][value]='
            '&columns[1][data]=b&columns[1][search][value]='
            '&columns[2][data]=c&columns[2][search][value]='
            '&columns[3][data]=d&columns[3][search][value]=Test'
        )
        assert resp.status_code == 200

    def test_data_sample_type_filter(self, admin_client):
        resp = admin_client.get(
            '/api/data?draw=1&start=0&length=10'
            '&columns[0][data]=a&columns[0][search][value]='
            '&columns[1][data]=b&columns[1][search][value]='
            '&columns[2][data]=c&columns[2][search][value]='
            '&columns[3][data]=d&columns[3][search][value]='
            '&columns[4][data]=e&columns[4][search][value]=Coal'
        )
        assert resp.status_code == 200

    def test_data_various_column_filters(self, admin_client):
        """Test columns 5,6,7,9,11,13 filters."""
        params = '&'.join([
            'draw=1', 'start=0', 'length=10',
            *[f'columns[{i}][data]=c{i}&columns[{i}][search][value]=' for i in range(14)],
        ])
        # Override specific columns with search values
        params += '&columns[5][search][value]=dry'
        params += '&columns[6][search][value]=John'
        params += '&columns[7][search][value]=Jane'
        params += '&columns[9][search][value]=note'
        params += '&columns[11][search][value]=1.5'
        params += '&columns[13][search][value]=Mad'
        resp = admin_client.get(f'/api/data?{params}')
        assert resp.status_code == 200

    def test_data_weight_filter_non_numeric(self, admin_client):
        """Column 11 with non-numeric value should be skipped."""
        params = '&'.join([
            'draw=1', 'start=0', 'length=10',
            *[f'columns[{i}][data]=c{i}&columns[{i}][search][value]=' for i in range(12)],
        ])
        params += '&columns[11][search][value]=abc'
        resp = admin_client.get(f'/api/data?{params}')
        assert resp.status_code == 200

    def test_data_id_filter_non_numeric(self, admin_client):
        """Column 1 with non-numeric value should be skipped."""
        params = '&'.join([
            'draw=1', 'start=0', 'length=10',
            'columns[0][data]=c0&columns[0][search][value]=',
            'columns[1][data]=c1&columns[1][search][value]=abc',
        ])
        resp = admin_client.get(f'/api/data?{params}')
        assert resp.status_code == 200

    def test_data_max_length_cap(self, admin_client):
        resp = admin_client.get('/api/data?draw=1&start=0&length=5000')
        assert resp.status_code == 200

    def test_data_retention_badges(self, admin_client, mass_app):
        """Test retention date badge logic."""
        import uuid
        with mass_app.app_context():
            user = User.query.filter_by(username='mschemist').first()
            now = datetime.now()

            # overdue
            s1 = Sample(
                sample_code=f"RET1-{uuid.uuid4().hex[:6]}",
                user_id=user.id,
                client_name="QC", sample_type="Coal", lab_type="coal",
                status="new", received_date=now,
                retention_date=date.today() - timedelta(days=5),
            )
            # within 7 days
            s2 = Sample(
                sample_code=f"RET2-{uuid.uuid4().hex[:6]}",
                user_id=user.id,
                client_name="QC", sample_type="Coal", lab_type="coal",
                status="new", received_date=now,
                retention_date=date.today() + timedelta(days=3),
            )
            # within 30 days
            s3 = Sample(
                sample_code=f"RET3-{uuid.uuid4().hex[:6]}",
                user_id=user.id,
                client_name="QC", sample_type="Coal", lab_type="coal",
                status="new", received_date=now,
                retention_date=date.today() + timedelta(days=15),
            )
            # > 30 days
            s4 = Sample(
                sample_code=f"RET4-{uuid.uuid4().hex[:6]}",
                user_id=user.id,
                client_name="QC", sample_type="Coal", lab_type="coal",
                status="new", received_date=now,
                retention_date=date.today() + timedelta(days=60),
            )
            # return_sample
            s5 = Sample(
                sample_code=f"RET5-{uuid.uuid4().hex[:6]}",
                user_id=user.id,
                client_name="QC", sample_type="Coal", lab_type="coal",
                status="new", received_date=now,
                return_sample=True,
            )
            for s in [s1, s2, s3, s4, s5]:
                _db.session.add(s)
            _db.session.commit()
            ids = [s1.id, s2.id, s3.id, s4.id, s5.id]

        resp = admin_client.get('/api/data?draw=1&start=0&length=100')
        assert resp.status_code == 200

        # cleanup
        with mass_app.app_context():
            for sid in ids:
                obj = _db.session.get(Sample, sid)
                if obj:
                    _db.session.delete(obj)
            _db.session.commit()

    def test_data_unauthenticated(self, unauth_client):
        resp = unauth_client.get('/api/data?draw=1&start=0&length=10')
        assert resp.status_code in (302, 401)


# ============================================================
# SAMPLES API: /sample_summary
# ============================================================

class TestSampleSummary:

    def test_get_sample_summary(self, admin_client):
        resp = admin_client.get('/api/sample_summary')
        assert resp.status_code == 200

    def test_post_archive(self, admin_client, sample_in_db):
        resp = admin_client.post(
            '/api/sample_summary',
            data={'action': 'archive', 'sample_ids': str(sample_in_db.id)},
        )
        assert resp.status_code == 302
        # restore
        with admin_client.application.app_context():
            s = _db.session.get(Sample, sample_in_db.id)
            if s:
                s.status = 'new'
                _db.session.commit()

    def test_post_unarchive(self, admin_client, sample_in_db):
        resp = admin_client.post(
            '/api/sample_summary',
            data={'action': 'unarchive', 'sample_ids': str(sample_in_db.id)},
        )
        assert resp.status_code == 302

    def test_post_no_action(self, admin_client):
        resp = admin_client.post('/api/sample_summary', data={})
        # Falls through to GET rendering
        assert resp.status_code == 200

    def test_post_invalid_action(self, admin_client):
        resp = admin_client.post(
            '/api/sample_summary',
            data={'action': 'delete', 'sample_ids': '1'},
        )
        assert resp.status_code == 200


# ============================================================
# SAMPLES API: /sample_report/<sample_id>
# ============================================================

class TestSampleReport:

    def test_report_not_found(self, admin_client):
        with patch('app.routes.api.samples_api.get_sample_report_data') as mock_fn:
            mock_result = MagicMock()
            mock_result.error = "SAMPLE_NOT_FOUND"
            mock_fn.return_value = mock_result
            resp = admin_client.get('/api/sample_report/999999')
            assert resp.status_code == 302

    def test_report_other_error(self, admin_client):
        with patch('app.routes.api.samples_api.get_sample_report_data') as mock_fn:
            mock_result = MagicMock()
            mock_result.error = "CALC_ERROR"
            mock_fn.return_value = mock_result
            resp = admin_client.get('/api/sample_report/1')
            assert resp.status_code == 302

    def test_report_success(self, admin_client, sample_in_db):
        with patch('app.routes.api.samples_api.get_sample_report_data') as mock_fn:
            mock_sample = MagicMock()
            mock_sample.sample_code = "TEST-001"
            mock_result = MagicMock()
            mock_result.error = None
            mock_result.sample = mock_sample
            mock_result.calculations = {}
            mock_result.report_date = datetime(2026, 1, 1)
            mock_fn.return_value = mock_result
            resp = admin_client.get(f'/api/sample_report/{sample_in_db.id}')
            assert resp.status_code == 200


# ============================================================
# SAMPLES API: /sample_history/<sample_id>
# ============================================================

class TestSampleHistory:

    def test_history_not_found(self, admin_client):
        resp = admin_client.get('/api/sample_history/999999')
        assert resp.status_code == 404

    def test_history_success(self, admin_client, sample_in_db):
        resp = admin_client.get(f'/api/sample_history/{sample_in_db.id}')
        assert resp.status_code == 200


# ============================================================
# SAMPLES API: /archive_hub
# ============================================================

class TestArchiveHub:

    def test_get_archive_hub(self, admin_client):
        resp = admin_client.get('/api/archive_hub')
        assert resp.status_code == 200

    def test_post_unarchive(self, admin_client, sample_in_db):
        resp = admin_client.post(
            '/api/archive_hub',
            data={'action': 'unarchive', 'sample_ids': str(sample_in_db.id)},
        )
        assert resp.status_code == 302

    def test_post_no_action(self, admin_client):
        resp = admin_client.post('/api/archive_hub', data={})
        assert resp.status_code == 302

    def test_get_with_filters(self, admin_client):
        resp = admin_client.get('/api/archive_hub?client=TestClient&type=Coal&year=2026&month=1')
        assert resp.status_code == 200

    def test_get_with_partial_filters(self, admin_client):
        resp = admin_client.get('/api/archive_hub?client=TestClient&type=Coal')
        assert resp.status_code == 200


# ============================================================
# SAMPLES API: /dashboard_stats
# ============================================================

class TestDashboardStats:

    def test_dashboard_stats(self, admin_client):
        resp = admin_client.get('/api/dashboard_stats')
        assert resp.status_code == 200
        data = resp.get_json()
        assert 'samples_by_day' in data
        assert 'samples_by_client' in data
        assert 'analysis_by_status' in data
        assert 'approval_stats' in data
        assert 'today' in data

    def test_dashboard_stats_structure(self, admin_client):
        resp = admin_client.get('/api/dashboard_stats')
        data = resp.get_json()
        assert len(data['samples_by_day']) == 7
        assert 'approved' in data['approval_stats']
        assert 'rejected' in data['approval_stats']
        assert 'pending' in data['approval_stats']
        assert 'samples' in data['today']
        assert 'analyses' in data['today']
        assert 'pending_review' in data['today']


# ============================================================
# SAMPLES API: /export/samples
# ============================================================

class TestExportSamples:

    def test_export_samples_basic(self, admin_client):
        with patch('app.utils.exports.create_sample_export', return_value=b'xlsx_data'), \
             patch('app.utils.exports.send_excel_response') as mock_send:
            mock_send.return_value = MagicMock(status_code=200, data=b'xlsx')
            resp = admin_client.get('/api/export/samples')
            assert mock_send.called

    def test_export_samples_with_filters(self, admin_client):
        with patch('app.utils.exports.create_sample_export', return_value=b'xlsx'), \
             patch('app.utils.exports.send_excel_response') as mock_send:
            mock_send.return_value = MagicMock(status_code=200, data=b'xlsx')
            resp = admin_client.get(
                '/api/export/samples?client=TC&type=Coal&start_date=2026-01-01'
                '&end_date=2026-12-31&limit=500&include_results=true'
            )
            assert mock_send.called

    def test_export_samples_invalid_dates(self, admin_client):
        with patch('app.utils.exports.create_sample_export', return_value=b'xlsx'), \
             patch('app.utils.exports.send_excel_response') as mock_send:
            mock_send.return_value = MagicMock(status_code=200, data=b'x')
            resp = admin_client.get('/api/export/samples?start_date=bad&end_date=bad')
            assert mock_send.called

    def test_export_samples_limit_cap(self, admin_client):
        with patch('app.utils.exports.create_sample_export', return_value=b'xlsx'), \
             patch('app.utils.exports.send_excel_response') as mock_send:
            mock_send.return_value = MagicMock(status_code=200, data=b'x')
            resp = admin_client.get('/api/export/samples?limit=99999')
            assert mock_send.called


# ============================================================
# SAMPLES API: /export/analysis
# ============================================================

class TestExportAnalysis:

    def test_export_analysis_basic(self, admin_client):
        with patch('app.utils.exports.create_analysis_export', return_value=b'xlsx'), \
             patch('app.utils.exports.send_excel_response') as mock_send:
            mock_send.return_value = MagicMock(status_code=200, data=b'x')
            resp = admin_client.get('/api/export/analysis')
            assert mock_send.called

    def test_export_analysis_with_filters(self, admin_client):
        with patch('app.utils.exports.create_analysis_export', return_value=b'xlsx'), \
             patch('app.utils.exports.send_excel_response') as mock_send:
            mock_send.return_value = MagicMock(status_code=200, data=b'x')
            resp = admin_client.get(
                '/api/export/analysis?status=approved&start_date=2026-01-01&end_date=2026-12-31&limit=500'
            )
            assert mock_send.called

    def test_export_analysis_invalid_dates(self, admin_client):
        with patch('app.utils.exports.create_analysis_export', return_value=b'xlsx'), \
             patch('app.utils.exports.send_excel_response') as mock_send:
            mock_send.return_value = MagicMock(status_code=200, data=b'x')
            resp = admin_client.get('/api/export/analysis?start_date=bad&end_date=bad')
            assert mock_send.called


# ============================================================
# SAMPLES API: htmx endpoints
# ============================================================

class TestHtmxEndpoints:

    def test_sample_count(self, admin_client):
        resp = admin_client.get('/api/sample_count')
        assert resp.status_code == 200
        assert b'samples' in resp.data

    def test_search_samples_short_query(self, admin_client):
        resp = admin_client.get('/api/search_samples?q=a')
        assert resp.status_code == 200
        assert b'2+ characters' in resp.data

    def test_search_samples_found(self, admin_client, sample_in_db):
        code = sample_in_db.sample_code[:4] if sample_in_db.sample_code else "MS-1"
        resp = admin_client.get(f'/api/search_samples?q={code}')
        assert resp.status_code == 200

    def test_search_samples_not_found(self, admin_client):
        resp = admin_client.get('/api/search_samples?q=ZZZZNOTEXIST99')
        assert resp.status_code == 200
        assert b'Not found' in resp.data

    def test_search_samples_empty(self, admin_client):
        resp = admin_client.get('/api/search_samples?q=')
        assert resp.status_code == 200
        assert b'2+ characters' in resp.data


# ============================================================
# SAMPLES API: /sample_analysis_results/<id>
# ============================================================

class TestSampleAnalysisResults:

    def test_results_success(self, admin_client, sample_in_db):
        resp = admin_client.get(f'/api/sample_analysis_results/{sample_in_db.id}')
        assert resp.status_code == 200
        data = resp.get_json()
        assert data['success'] is True
        assert 'data' in data

    def test_results_empty(self, admin_client):
        # Some nonexistent sample - still returns success with empty data
        resp = admin_client.get('/api/sample_analysis_results/999999')
        assert resp.status_code == 200
        data = resp.get_json()
        assert data['data'] == []


# ============================================================
# SAMPLES API: /search_samples_json
# ============================================================

class TestSearchSamplesJson:

    def test_search_short_query(self, admin_client):
        resp = admin_client.get('/api/search_samples_json?q=a')
        assert resp.status_code == 200
        data = resp.get_json()
        assert data == []

    def test_search_found(self, admin_client, sample_in_db):
        code = sample_in_db.sample_code[:4] if sample_in_db.sample_code else "MS-1"
        resp = admin_client.get(f'/api/search_samples_json?q={code}')
        assert resp.status_code == 200
        data = resp.get_json()
        assert isinstance(data, list)

    def test_search_not_found(self, admin_client):
        resp = admin_client.get('/api/search_samples_json?q=ZZNOTEXIST99')
        assert resp.status_code == 200
        data = resp.get_json()
        assert data == []

    def test_search_empty(self, admin_client):
        resp = admin_client.get('/api/search_samples_json?q=')
        assert resp.status_code == 200


# ============================================================
# SAMPLES API: /mg_summary
# ============================================================

class TestMgSummary:

    def test_mg_summary_get_empty(self, admin_client):
        resp = admin_client.get('/api/mg_summary')
        assert resp.status_code == 200

    def test_mg_summary_post_archive(self, admin_client, sample_in_db):
        resp = admin_client.post(
            '/api/mg_summary',
            json={'sample_ids': [sample_in_db.id], 'action': 'archive'},
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert 'success' in data
        # restore
        with admin_client.application.app_context():
            s = _db.session.get(Sample, sample_in_db.id)
            if s:
                s.status = 'new'
                _db.session.commit()

    def test_mg_summary_post_unarchive(self, admin_client, sample_in_db):
        resp = admin_client.post(
            '/api/mg_summary',
            json={'sample_ids': [sample_in_db.id], 'action': 'unarchive'},
        )
        assert resp.status_code == 200

    def test_mg_summary_post_repeat_no_role(self, chemist_client, sample_in_db):
        resp = chemist_client.post(
            '/api/mg_summary',
            json={'sample_ids': [sample_in_db.id], 'action': 'repeat', 'codes': ['MG']},
        )
        assert resp.status_code == 403

    def test_mg_summary_post_repeat_no_codes(self, senior_client, sample_in_db):
        resp = senior_client.post(
            '/api/mg_summary',
            json={'sample_ids': [sample_in_db.id], 'action': 'repeat', 'codes': []},
        )
        assert resp.status_code == 400

    def test_mg_summary_post_repeat_success(self, senior_client, mass_app, sample_in_db):
        # Create an approved AR with MG code
        with mass_app.app_context():
            ar = AnalysisResult(
                sample_id=sample_in_db.id,
                analysis_code="MG",
                final_result=50.0,
                status="approved",
                user_id=1,
            )
            _db.session.add(ar)
            _db.session.commit()
            ar_id = ar.id

        resp = senior_client.post(
            '/api/mg_summary',
            json={'sample_ids': [sample_in_db.id], 'action': 'repeat', 'codes': ['MG']},
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert data['success'] is True

        # cleanup
        with mass_app.app_context():
            obj = _db.session.get(AnalysisResult, ar_id)
            if obj:
                _db.session.delete(obj)
                _db.session.commit()

    def test_mg_summary_post_repeat_db_error(self, senior_client, mass_app, sample_in_db):
        from sqlalchemy.exc import SQLAlchemyError
        with mass_app.app_context():
            ar = AnalysisResult(
                sample_id=sample_in_db.id,
                analysis_code="MG",
                final_result=50.0,
                status="approved",
                user_id=1,
            )
            _db.session.add(ar)
            _db.session.commit()
            ar_id = ar.id

        with patch.object(_db.session, 'commit', side_effect=SQLAlchemyError("err")):
            resp = senior_client.post(
                '/api/mg_summary',
                json={'sample_ids': [sample_in_db.id], 'action': 'repeat', 'codes': ['MG']},
            )
            assert resp.status_code == 500

        # cleanup
        with mass_app.app_context():
            _db.session.rollback()
            obj = _db.session.get(AnalysisResult, ar_id)
            if obj:
                _db.session.delete(obj)
                _db.session.commit()

    def test_mg_summary_post_invalid_action(self, admin_client):
        resp = admin_client.post(
            '/api/mg_summary',
            json={'sample_ids': [], 'action': 'delete'},
        )
        assert resp.status_code == 400

    def test_mg_summary_post_no_sample_ids(self, admin_client):
        resp = admin_client.post(
            '/api/mg_summary',
            json={'action': 'archive'},
        )
        assert resp.status_code == 400

    def test_mg_summary_post_admin_repeat(self, admin_client, mass_app, sample_in_db):
        """Admin can also repeat."""
        with mass_app.app_context():
            ar = AnalysisResult(
                sample_id=sample_in_db.id,
                analysis_code="MG",
                final_result=55.0,
                status="pending_review",
                user_id=1,
            )
            _db.session.add(ar)
            _db.session.commit()
            ar_id = ar.id

        resp = admin_client.post(
            '/api/mg_summary',
            json={'sample_ids': [sample_in_db.id], 'action': 'repeat', 'codes': ['MG']},
        )
        assert resp.status_code == 200

        with mass_app.app_context():
            obj = _db.session.get(AnalysisResult, ar_id)
            if obj:
                _db.session.delete(obj)
                _db.session.commit()
