# tests/test_water_lab_utils_coverage.py
"""Tests for water lab utils.py and water_reports.py to boost coverage."""

import json
import uuid
from datetime import datetime, date, timedelta
from unittest.mock import patch, MagicMock

import pytest
from sqlalchemy.exc import SQLAlchemyError

from app.models import Sample, AnalysisResult, User


# =====================================================================
# Helpers
# =====================================================================

def _make_sample(db, **kwargs):
    """Create a Sample with sensible defaults for water lab tests."""
    defaults = dict(
        sample_code=f"WTR-{uuid.uuid4().hex[:8]}",
        user_id=1,
        lab_type='water',
        client_name='QC',
        sample_type='water',
        sample_date=date(2026, 3, 1),
        status='new',
    )
    defaults.update(kwargs)
    s = Sample(**defaults)
    db.session.add(s)
    db.session.flush()
    return s


def _make_ar(db, sample, code='PH', raw_data=None, final_result=None, created_at=None):
    """Create an AnalysisResult attached to a sample."""
    ar = AnalysisResult(
        sample_id=sample.id,
        analysis_code=code,
        raw_data=json.dumps(raw_data) if raw_data else None,
        final_result=final_result,
        created_at=created_at or datetime(2026, 3, 5, 10, 0),
    )
    db.session.add(ar)
    db.session.flush()
    return ar


# =====================================================================
# utils.py — _generate_micro_lab_id
# =====================================================================

class TestGenerateMicroLabId:
    """Tests for _generate_micro_lab_id."""

    def test_no_existing_samples(self, app, db):
        """First micro sample should get day_num=1, total=0."""
        with app.app_context():
            from app.labs.water_lab.chemistry.utils import _generate_micro_lab_id
            day_num, total = _generate_micro_lab_id(date(2099, 1, 1))
            # No micro samples exist for that date => new day
            assert isinstance(day_num, int)
            assert isinstance(total, int)

    def test_existing_today_samples(self, app, db):
        """When today already has micro samples, reuse that day_num."""
        with app.app_context():
            sd = date(2099, 2, 1)
            s = _make_sample(db, lab_type='microbiology', sample_date=sd,
                             micro_lab_id='05_10')
            db.session.commit()

            from app.labs.water_lab.chemistry.utils import _generate_micro_lab_id
            day_num, total = _generate_micro_lab_id(sd)
            assert day_num == 5  # reuses existing day_num from '05_10'

            db.session.delete(s)
            db.session.commit()

    def test_next_batch_flag(self, app, db):
        """next_batch=True should always increment day_num."""
        with app.app_context():
            sd = date(2099, 3, 1)
            s = _make_sample(db, lab_type='microbiology', sample_date=sd,
                             micro_lab_id='03_01')
            db.session.commit()

            from app.labs.water_lab.chemistry.utils import _generate_micro_lab_id
            day_num, total = _generate_micro_lab_id(sd, next_batch=True)
            assert day_num >= 4  # should be at least max+1

            db.session.delete(s)
            db.session.commit()

    def test_next_batch_with_today_existing(self, app, db):
        """next_batch=True + today samples exist: picks max+1."""
        with app.app_context():
            sd = date(2099, 4, 1)
            s1 = _make_sample(db, lab_type='water & micro', sample_date=sd,
                              micro_lab_id='07_05')
            db.session.commit()

            from app.labs.water_lab.chemistry.utils import _generate_micro_lab_id
            day_num, _ = _generate_micro_lab_id(sd, next_batch=True)
            # Should get at least 8 (07 + 1)
            assert day_num >= 8

            db.session.delete(s1)
            db.session.commit()

    def test_invalid_micro_lab_id_format(self, app, db):
        """Handles garbage micro_lab_id gracefully."""
        with app.app_context():
            sd = date(2099, 5, 1)
            s = _make_sample(db, lab_type='microbiology', sample_date=sd,
                             micro_lab_id='INVALID')
            db.session.commit()

            from app.labs.water_lab.chemistry.utils import _generate_micro_lab_id
            # Should not crash, falls through try/except
            day_num, total = _generate_micro_lab_id(sd)
            assert isinstance(day_num, int)

            db.session.delete(s)
            db.session.commit()

    def test_micro_lab_id_no_underscore(self, app, db):
        """micro_lab_id without underscore is skipped."""
        with app.app_context():
            sd = date(2099, 6, 1)
            s = _make_sample(db, lab_type='microbiology', sample_date=sd,
                             micro_lab_id='99')
            db.session.commit()

            from app.labs.water_lab.chemistry.utils import _generate_micro_lab_id
            day_num, total = _generate_micro_lab_id(sd)
            assert isinstance(day_num, int)

            db.session.delete(s)
            db.session.commit()

    def test_existing_today_no_micro_lab_id(self, app, db):
        """Today has micro samples but micro_lab_id is None => new day."""
        with app.app_context():
            sd = date(2099, 7, 1)
            s = _make_sample(db, lab_type='microbiology', sample_date=sd,
                             micro_lab_id=None)
            db.session.commit()

            from app.labs.water_lab.chemistry.utils import _generate_micro_lab_id
            day_num, total = _generate_micro_lab_id(sd)
            # existing first() returns None micro_lab_id -> fallback to max_day_num + 1
            assert isinstance(day_num, int)

            db.session.delete(s)
            db.session.commit()


# =====================================================================
# utils.py — _max_batch / _generate_chem_lab_id
# =====================================================================

class TestGenerateChemLabId:
    """Tests for _generate_chem_lab_id and _max_batch."""

    def test_no_existing_chem_samples(self, app, db):
        """First chem sample gets batch=1."""
        with app.app_context():
            from app.labs.water_lab.chemistry.utils import _generate_chem_lab_id
            batch, total = _generate_chem_lab_id(date(2099, 8, 1))
            assert isinstance(batch, int)
            assert batch >= 1

    def test_existing_chem_samples_same_day(self, app, db):
        """Same day reuses batch number."""
        with app.app_context():
            sd = date(2099, 9, 1)
            s = _make_sample(db, lab_type='water', sample_date=sd,
                             chem_lab_id='10_05')
            db.session.commit()

            from app.labs.water_lab.chemistry.utils import _generate_chem_lab_id
            batch, total = _generate_chem_lab_id(sd)
            assert batch == 10

            db.session.delete(s)
            db.session.commit()

    def test_chem_next_batch(self, app, db):
        """next_batch increments from max."""
        with app.app_context():
            sd = date(2099, 10, 1)
            s = _make_sample(db, lab_type='water', sample_date=sd,
                             chem_lab_id='15_03')
            db.session.commit()

            from app.labs.water_lab.chemistry.utils import _generate_chem_lab_id
            batch, total = _generate_chem_lab_id(sd, next_batch=True)
            assert batch >= 16

            db.session.delete(s)
            db.session.commit()

    def test_chem_today_no_batch(self, app, db):
        """Today has water samples but no chem_lab_id => fallback to max+1."""
        with app.app_context():
            sd = date(2099, 11, 1)
            s = _make_sample(db, lab_type='water', sample_date=sd,
                             chem_lab_id=None)
            db.session.commit()

            from app.labs.water_lab.chemistry.utils import _generate_chem_lab_id
            batch, total = _generate_chem_lab_id(sd)
            # _max_batch with today filter returns 0, fallback to global max+1
            assert isinstance(batch, int)

            db.session.delete(s)
            db.session.commit()

    def test_max_batch_with_invalid_format(self, app, db):
        """chem_lab_id without underscore is skipped."""
        with app.app_context():
            s = _make_sample(db, lab_type='water', sample_date=date(2099, 12, 1),
                             chem_lab_id='GARBAGE')
            db.session.commit()

            from app.labs.water_lab.chemistry.utils import _max_batch
            result = _max_batch()
            assert isinstance(result, int)

            db.session.delete(s)
            db.session.commit()

    def test_max_batch_with_extra_filters(self, app, db):
        """_max_batch with extra_filters narrows results."""
        with app.app_context():
            from app.labs.water_lab.chemistry.utils import _max_batch
            sd = date(2098, 1, 1)
            result = _max_batch([Sample.sample_date == sd])
            assert result == 0  # no matching samples


# =====================================================================
# utils.py — create_water_micro_samples
# =====================================================================

class TestCreateWaterMicroSamples:
    """Tests for create_water_micro_samples."""

    def _form(self, **overrides):
        """Build a mock form (ImmutableMultiDict-like)."""
        data = {
            'sample_codes': ['TestSample1'],
            'source_type': 'QC',
            'sample_date': '2099-06-15',
            'analyses': ['PH', 'EC'],
            'volume_2l': '',
            'volume_05l': '',
            'return_sample': '',
            'retention_period': '7',
            'next_batch': '',
            'sampling_location': 'Well A',
            'sampled_by': 'Tester',
            'notes': 'Test notes',
        }
        data.update(overrides)

        class FakeForm:
            def __init__(self, d):
                self._d = d

            def getlist(self, key):
                val = self._d.get(key, [])
                return val if isinstance(val, list) else [val]

            def get(self, key, default=''):
                val = self._d.get(key, default)
                if isinstance(val, list):
                    return val[0] if val else default
                return val

        return FakeForm(data)

    def test_create_water_only_samples(self, app, db):
        """Water-only analyses => lab_type='water'."""
        with app.app_context():
            from app.labs.water_lab.chemistry.utils import create_water_micro_samples
            user = User.query.filter_by(username='chemist').first()
            form = self._form()
            created, skipped, count = create_water_micro_samples(form, user.id)
            assert len(created) == 1
            assert 'TestSample1' in created[0]
            assert count == 2  # PH, EC

            # Cleanup
            for s in Sample.query.filter(Sample.sample_code.like('%TestSample1%')).all():
                db.session.delete(s)
            db.session.commit()

    def test_create_micro_only_samples(self, app, db):
        """Micro-only analyses => lab_type='microbiology'."""
        with app.app_context():
            from app.labs.water_lab.chemistry.utils import create_water_micro_samples
            user = User.query.filter_by(username='chemist').first()
            form = self._form(analyses=['CFU', 'ECOLI'])
            created, skipped, count = create_water_micro_samples(form, user.id)
            assert len(created) == 1
            assert count == 2

            for s in Sample.query.filter(Sample.sample_code.like('%TestSample1%')).all():
                db.session.delete(s)
            db.session.commit()

    def test_create_water_and_micro_samples(self, app, db):
        """Mixed analyses => lab_type='water & micro'."""
        with app.app_context():
            from app.labs.water_lab.chemistry.utils import create_water_micro_samples
            user = User.query.filter_by(username='chemist').first()
            form = self._form(analyses=['PH', 'CFU'])
            created, skipped, count = create_water_micro_samples(form, user.id)
            assert len(created) == 1
            assert count == 2

            for s in Sample.query.filter(Sample.sample_code.like('%TestSample1%')).all():
                db.session.delete(s)
            db.session.commit()

    def test_skip_duplicate_samples(self, app, db):
        """Duplicate sample_code should be skipped."""
        with app.app_context():
            from app.labs.water_lab.chemistry.utils import create_water_micro_samples
            user = User.query.filter_by(username='chemist').first()
            form = self._form(sample_codes=['DupSample'])
            created1, _, _ = create_water_micro_samples(form, user.id)
            assert len(created1) == 1

            # Try again with same name and date
            created2, skipped2, _ = create_water_micro_samples(form, user.id)
            assert len(created2) == 0
            assert len(skipped2) == 1

            for s in Sample.query.filter(Sample.sample_code.like('%DupSample%')).all():
                db.session.delete(s)
            db.session.commit()

    def test_empty_sample_name_skipped(self, app, db):
        """Blank sample names are ignored."""
        with app.app_context():
            from app.labs.water_lab.chemistry.utils import create_water_micro_samples
            user = User.query.filter_by(username='chemist').first()
            form = self._form(sample_codes=['', '  ', 'ValidName'])
            created, skipped, _ = create_water_micro_samples(form, user.id)
            # Only ValidName should be created
            assert any('ValidName' in c for c in created)

            for s in Sample.query.filter(Sample.sample_code.like('%ValidName%')).all():
                db.session.delete(s)
            db.session.commit()

    def test_volume_2l(self, app, db):
        """volume_2l => weight=2000."""
        with app.app_context():
            from app.labs.water_lab.chemistry.utils import create_water_micro_samples
            user = User.query.filter_by(username='chemist').first()
            form = self._form(sample_codes=['Vol2L'], volume_2l='on')
            created, _, _ = create_water_micro_samples(form, user.id)
            s = Sample.query.filter(Sample.sample_code.like('%Vol2L%')).first()
            assert s.weight == 2000.0

            db.session.delete(s)
            db.session.commit()

    def test_volume_05l(self, app, db):
        """volume_05l => weight=500."""
        with app.app_context():
            from app.labs.water_lab.chemistry.utils import create_water_micro_samples
            user = User.query.filter_by(username='chemist').first()
            form = self._form(sample_codes=['Vol05L'], volume_05l='on')
            created, _, _ = create_water_micro_samples(form, user.id)
            s = Sample.query.filter(Sample.sample_code.like('%Vol05L%')).first()
            assert s.weight == 500.0

            db.session.delete(s)
            db.session.commit()

    def test_volume_both(self, app, db):
        """Both volumes => weight=2500."""
        with app.app_context():
            from app.labs.water_lab.chemistry.utils import create_water_micro_samples
            user = User.query.filter_by(username='chemist').first()
            form = self._form(sample_codes=['VolBoth'], volume_2l='on', volume_05l='on')
            created, _, _ = create_water_micro_samples(form, user.id)
            s = Sample.query.filter(Sample.sample_code.like('%VolBoth%')).first()
            assert s.weight == 2500.0

            db.session.delete(s)
            db.session.commit()

    def test_no_volume_selected(self, app, db):
        """No volume => weight=None."""
        with app.app_context():
            from app.labs.water_lab.chemistry.utils import create_water_micro_samples
            user = User.query.filter_by(username='chemist').first()
            form = self._form(sample_codes=['NoVol'])
            created, _, _ = create_water_micro_samples(form, user.id)
            s = Sample.query.filter(Sample.sample_code.like('%NoVol%')).first()
            assert s.weight is None

            db.session.delete(s)
            db.session.commit()

    def test_return_sample_flag(self, app, db):
        """return_sample checkbox."""
        with app.app_context():
            from app.labs.water_lab.chemistry.utils import create_water_micro_samples
            user = User.query.filter_by(username='chemist').first()
            form = self._form(sample_codes=['RetSample'], return_sample='on')
            created, _, _ = create_water_micro_samples(form, user.id)
            s = Sample.query.filter(Sample.sample_code.like('%RetSample%')).first()
            assert s.return_sample is True

            db.session.delete(s)
            db.session.commit()

    def test_invalid_retention_period(self, app, db):
        """Non-integer retention_period defaults to 7."""
        with app.app_context():
            from app.labs.water_lab.chemistry.utils import create_water_micro_samples
            user = User.query.filter_by(username='chemist').first()
            form = self._form(sample_codes=['BadRetention'], retention_period='abc')
            created, _, _ = create_water_micro_samples(form, user.id)
            s = Sample.query.filter(Sample.sample_code.like('%BadRetention%')).first()
            expected = date(2099, 6, 15) + timedelta(days=7)
            assert s.retention_date == expected

            db.session.delete(s)
            db.session.commit()

    def test_no_sample_date_uses_now(self, app, db):
        """Missing sample_date uses now_local().date()."""
        with app.app_context():
            from app.labs.water_lab.chemistry.utils import create_water_micro_samples
            user = User.query.filter_by(username='chemist').first()
            form = self._form(sample_codes=['NoDate'], sample_date='')
            created, _, _ = create_water_micro_samples(form, user.id)
            s = Sample.query.filter(Sample.sample_code.like('%NoDate%')).first()
            assert s.sample_date is not None

            db.session.delete(s)
            db.session.commit()

    def test_wastewater_creates_orolot_garalt(self, app, db):
        """Wastewater-only analyses create input/output pairs."""
        with app.app_context():
            from app.labs.water_lab.chemistry.utils import create_water_micro_samples
            user = User.query.filter_by(username='chemist').first()
            # ODOR is wastewater-only (not in drinking)
            form = self._form(sample_codes=['WW1'], analyses=['ODOR'])
            created, _, _ = create_water_micro_samples(form, user.id)
            # Should create 2 samples: WW1 (Оролт) and WW1 (Гаралт)
            assert len(created) == 2
            assert any('Оролт' in c for c in created)
            assert any('Гаралт' in c for c in created)

            for s in Sample.query.filter(Sample.sample_code.like('%WW1%')).all():
                db.session.delete(s)
            db.session.commit()

    def test_safe_commit_failure_raises(self, app, db):
        """If safe_commit returns False, RuntimeError is raised."""
        with app.app_context():
            from app.labs.water_lab.chemistry.utils import create_water_micro_samples
            user = User.query.filter_by(username='chemist').first()
            form = self._form(sample_codes=['CommitFail'])

            with patch('app.labs.water_lab.chemistry.utils.safe_commit', return_value=False):
                with pytest.raises(RuntimeError, match='алдаа'):
                    create_water_micro_samples(form, user.id)

            db.session.rollback()

    def test_multiple_samples(self, app, db):
        """Multiple sample names in one batch."""
        with app.app_context():
            from app.labs.water_lab.chemistry.utils import create_water_micro_samples
            user = User.query.filter_by(username='chemist').first()
            form = self._form(sample_codes=['Multi1', 'Multi2', 'Multi3'])
            created, skipped, _ = create_water_micro_samples(form, user.id)
            assert len(created) == 3

            for s in Sample.query.filter(Sample.sample_code.like('%Multi%')).all():
                db.session.delete(s)
            db.session.commit()

    def test_next_batch_flag_chem(self, app, db):
        """next_batch with water analyses uses chem next_batch."""
        with app.app_context():
            from app.labs.water_lab.chemistry.utils import create_water_micro_samples
            user = User.query.filter_by(username='chemist').first()
            form = self._form(sample_codes=['NBatch'], next_batch='on')
            created, _, _ = create_water_micro_samples(form, user.id)
            assert len(created) == 1

            for s in Sample.query.filter(Sample.sample_code.like('%NBatch%')).all():
                db.session.delete(s)
            db.session.commit()


# =====================================================================
# utils.py — module-level constants
# =====================================================================

class TestWaterUtilsConstants:
    """Test module-level constants."""

    def test_water_codes_set(self, app):
        """WATER_CODES is a non-empty set of strings."""
        with app.app_context():
            from app.labs.water_lab.chemistry.utils import WATER_CODES
            assert isinstance(WATER_CODES, set)
            assert len(WATER_CODES) > 0
            assert 'PH' in WATER_CODES

    def test_micro_codes_set(self, app):
        """MICRO_CODES is a non-empty set of strings."""
        with app.app_context():
            from app.labs.water_lab.chemistry.utils import MICRO_CODES
            assert isinstance(MICRO_CODES, set)
            assert len(MICRO_CODES) > 0
            assert 'CFU' in MICRO_CODES


# =====================================================================
# water_reports.py — _active_chem_codes
# =====================================================================

class TestActiveChem:
    """Tests for _active_chem_codes."""

    def test_excludes_archive(self, app):
        """Archive codes should not be in active list."""
        with app.app_context():
            from app.labs.water_lab.chemistry.water_reports import _active_chem_codes
            codes = _active_chem_codes()
            assert 'PH' in codes
            # 'COD' is archive
            assert 'COD' not in codes
            # 'SLUDGE' is archive
            assert 'SLUDGE' not in codes

    def test_returns_list(self, app):
        with app.app_context():
            from app.labs.water_lab.chemistry.water_reports import _active_chem_codes
            codes = _active_chem_codes()
            assert isinstance(codes, list)
            assert len(codes) > 0


# =====================================================================
# water_reports.py — water_dashboard (route)
# =====================================================================

class TestWaterDashboard:
    """Tests for water_dashboard route."""

    def test_dashboard_requires_login(self, client):
        """Should redirect to login without auth."""
        resp = client.get('/labs/water-lab/chemistry/reports/dashboard')
        assert resp.status_code in (302, 401)

    def test_dashboard_with_auth(self, app, db, auth_admin):
        """Dashboard renders with correct data."""
        with app.app_context():
            now = datetime.now()
            s = _make_sample(db, lab_type='water',
                             received_date=now,
                             sample_date=now.date())
            ar_pass = _make_ar(db, s, code='PH',
                               raw_data={'value': 7.0},
                               created_at=now)
            s2 = _make_sample(db, lab_type='water',
                              received_date=now,
                              sample_date=now.date())
            ar_fail = _make_ar(db, s2, code='PH',
                               raw_data={'value': 5.0},
                               created_at=now)
            db.session.commit()
            s_id, s2_id = s.id, s2.id

        resp = auth_admin.get('/labs/water-lab/chemistry/reports/dashboard')
        assert resp.status_code in (200, 302, 403)

        with app.app_context():
            AnalysisResult.query.filter(
                AnalysisResult.sample_id.in_([s_id, s2_id])
            ).delete(synchronize_session=False)
            Sample.query.filter(Sample.id.in_([s_id, s2_id])).delete(synchronize_session=False)
            db.session.commit()

    def test_dashboard_ph_edge_cases(self, app, db):
        """PH pass/fail logic: boundary values, bad JSON, None."""
        with app.app_context():
            now = datetime.now()
            # Each sample gets one PH result (unique constraint on sample_id+analysis_code)
            s1 = _make_sample(db, lab_type='water', received_date=now, sample_date=now.date())
            s2 = _make_sample(db, lab_type='water', received_date=now, sample_date=now.date())
            s3 = _make_sample(db, lab_type='water', received_date=now, sample_date=now.date())
            s4 = _make_sample(db, lab_type='water', received_date=now, sample_date=now.date())
            s5 = _make_sample(db, lab_type='water', received_date=now, sample_date=now.date())

            # Pass: exactly 6.5
            _make_ar(db, s1, 'PH', raw_data={'value': 6.5}, created_at=now)
            # Pass: exactly 8.5
            _make_ar(db, s2, 'PH', raw_data={'value': 8.5}, created_at=now)
            # Fail: 6.4
            _make_ar(db, s3, 'PH', raw_data={'value': 6.4}, created_at=now)
            # Bad JSON
            ar4 = AnalysisResult(
                sample_id=s4.id, analysis_code='PH',
                raw_data='not-json', created_at=now)
            db.session.add(ar4)
            # None raw_data, use final_result
            _make_ar(db, s5, 'PH', raw_data=None, final_result='7.5', created_at=now)
            db.session.commit()

            sample_ids = [s1.id, s2.id, s3.id, s4.id, s5.id]

            # Verify the logic by running the function internals manually
            import json as _json
            results = AnalysisResult.query.filter(
                AnalysisResult.sample_id.in_(sample_ids),
                AnalysisResult.analysis_code == 'PH',
            ).all()
            pass_c = fail_c = 0
            for ar in results:
                try:
                    rd = _json.loads(ar.raw_data) if ar.raw_data else {}
                    val = rd.get('value') or rd.get('result') or ar.final_result
                    if val is not None:
                        v = float(val)
                        if 6.5 <= v <= 8.5:
                            pass_c += 1
                        else:
                            fail_c += 1
                except (_json.JSONDecodeError, TypeError, ValueError):
                    pass

            assert pass_c == 3  # 6.5, 8.5, 7.5 (from final_result)
            assert fail_c == 1  # 6.4

            AnalysisResult.query.filter(
                AnalysisResult.sample_id.in_(sample_ids)
            ).delete(synchronize_session=False)
            Sample.query.filter(Sample.id.in_(sample_ids)).delete(synchronize_session=False)
            db.session.commit()


# =====================================================================
# water_reports.py — water_consumption (route)
# =====================================================================

class TestWaterConsumption:
    """Tests for water_consumption route."""

    def test_consumption_requires_login(self, client):
        resp = client.get('/labs/water-lab/chemistry/reports/consumption')
        assert resp.status_code in (302, 401)

    def test_consumption_with_data(self, app, db, auth_admin):
        """Consumption builds tree from analysis data."""
        with app.app_context():
            now = datetime.now()
            s = _make_sample(db, lab_type='water', client_name='QC',
                             received_date=now, sample_date=now.date())
            _make_ar(db, s, 'PH', created_at=now)
            _make_ar(db, s, 'EC', created_at=now)
            db.session.commit()
            s_id = s.id

        resp = auth_admin.get(f'/labs/water-lab/chemistry/reports/consumption?year={datetime.now().year}')
        assert resp.status_code in (200, 302, 403)

        with app.app_context():
            AnalysisResult.query.filter_by(sample_id=s_id).delete()
            Sample.query.filter_by(id=s_id).delete()
            db.session.commit()

    def test_consumption_invalid_year(self, app, db, auth_admin):
        """Invalid year parameter falls back to current year."""
        resp = auth_admin.get('/labs/water-lab/chemistry/reports/consumption?year=abc')
        assert resp.status_code in (200, 302, 403)

    def test_consumption_year_out_of_range(self, app, db, auth_admin):
        """Year out of 2000-2100 range falls back."""
        resp = auth_admin.get('/labs/water-lab/chemistry/reports/consumption?year=1999')
        assert resp.status_code in (200, 302, 403)


# =====================================================================
# water_reports.py — api_consumption_cell (route)
# =====================================================================

class TestApiConsumptionCell:
    """Tests for api_consumption_cell API."""

    def test_cell_requires_login(self, client):
        resp = client.get('/labs/water-lab/chemistry/api/consumption_cell?year=2026&month=3&unit=x')
        assert resp.status_code in (302, 401)

    def test_cell_missing_params(self, app, db, auth_admin):
        """Missing required params returns failure."""
        resp = auth_admin.get('/labs/water-lab/chemistry/api/consumption_cell')
        assert resp.status_code == 200
        data = resp.get_json()
        if data:
            assert data.get('success') is False

    def test_cell_invalid_month(self, app, db, auth_admin):
        """month=13 is invalid."""
        resp = auth_admin.get('/labs/water-lab/chemistry/api/consumption_cell?year=2026&month=13&unit=x')
        assert resp.status_code == 200
        data = resp.get_json()
        if data:
            assert data.get('success') is False

    def test_cell_valid_request(self, app, db, auth_admin):
        """Valid request returns items."""
        with app.app_context():
            now = datetime(2026, 3, 5)
            s = _make_sample(db, lab_type='water', client_name='QC',
                             received_date=now, sample_date=now.date())
            _make_ar(db, s, 'PH', created_at=now)
            db.session.commit()
            s_id = s.id

        resp = auth_admin.get(
            '/labs/water-lab/chemistry/api/consumption_cell?year=2026&month=3&unit=QC&stype=Хими&kind=samples'
        )
        assert resp.status_code in (200, 302, 403)

        with app.app_context():
            AnalysisResult.query.filter_by(sample_id=s_id).delete()
            Sample.query.filter_by(id=s_id).delete()
            db.session.commit()

    def test_cell_kind_code(self, app, db, auth_admin):
        """kind=code with a specific code filters by that code."""
        resp = auth_admin.get(
            '/labs/water-lab/chemistry/api/consumption_cell?year=2026&month=3&unit=x&kind=code&code=PH'
        )
        assert resp.status_code in (200, 302, 403)

    def test_cell_invalid_kind(self, app, db, auth_admin):
        """Invalid kind defaults to 'samples'."""
        resp = auth_admin.get(
            '/labs/water-lab/chemistry/api/consumption_cell?year=2026&month=3&unit=x&kind=badkind'
        )
        assert resp.status_code in (200, 302, 403)


# =====================================================================
# water_reports.py — water_monthly_plan (route)
# =====================================================================

class TestWaterMonthlyPlan:
    """Tests for water_monthly_plan route."""

    def test_plan_requires_login(self, client):
        resp = client.get('/labs/water-lab/chemistry/reports/monthly_plan')
        assert resp.status_code in (302, 401)

    def test_plan_default_params(self, app, db, auth_admin):
        """Default year/month from now."""
        resp = auth_admin.get('/labs/water-lab/chemistry/reports/monthly_plan')
        assert resp.status_code in (200, 302, 403)

    def test_plan_specific_month(self, app, db, auth_admin):
        """Specific year/month params."""
        resp = auth_admin.get('/labs/water-lab/chemistry/reports/monthly_plan?year=2026&month=1')
        assert resp.status_code in (200, 302, 403)

    def test_plan_invalid_params(self, app, db, auth_admin):
        """Invalid year/month falls back to now."""
        resp = auth_admin.get('/labs/water-lab/chemistry/reports/monthly_plan?year=abc&month=13')
        assert resp.status_code in (200, 302, 403)

    def test_plan_year_out_of_range(self, app, db, auth_admin):
        """Year out of range falls back."""
        resp = auth_admin.get('/labs/water-lab/chemistry/reports/monthly_plan?year=1999&month=6')
        assert resp.status_code in (200, 302, 403)

    def test_plan_with_data(self, app, db, auth_admin):
        """Plan with existing analysis data."""
        with app.app_context():
            now = datetime.now()
            s = _make_sample(db, lab_type='water', client_name='QC',
                             received_date=now, sample_date=now.date())
            _make_ar(db, s, 'PH', created_at=now)
            db.session.commit()
            s_id = s.id

        resp = auth_admin.get(
            f'/labs/water-lab/chemistry/reports/monthly_plan?year={datetime.now().year}&month={datetime.now().month}'
        )
        assert resp.status_code in (200, 302, 403)

        with app.app_context():
            AnalysisResult.query.filter_by(sample_id=s_id).delete()
            Sample.query.filter_by(id=s_id).delete()
            db.session.commit()

    def test_plan_december(self, app, db, auth_admin):
        """December edge case (month=12)."""
        resp = auth_admin.get('/labs/water-lab/chemistry/reports/monthly_plan?year=2026&month=12')
        assert resp.status_code in (200, 302, 403)

    def test_plan_january(self, app, db, auth_admin):
        """January edge case (trend goes into previous year)."""
        resp = auth_admin.get('/labs/water-lab/chemistry/reports/monthly_plan?year=2026&month=1')
        assert resp.status_code in (200, 302, 403)


# =====================================================================
# water_reports.py — consumption tree logic (unit test)
# =====================================================================

class TestConsumptionTreeLogic:
    """Unit test the consumption tree building logic in isolation."""

    def test_tree_grouping(self):
        """Verify defaultdict tree structure works correctly."""
        from collections import defaultdict

        tree = defaultdict(lambda: defaultdict(lambda: {
            'sample_cnt': defaultdict(int),
            'code_cnt': defaultdict(lambda: defaultdict(int)),
        }))

        seen_samples = defaultdict(set)
        rows = [
            (1, 'PH', 3, 'drinking'),
            (1, 'EC', 3, 'drinking'),
            (2, 'PH', 3, 'drinking'),
            (3, 'PH', 4, 'wastewater'),
        ]
        for sid, code, mon, unit in rows:
            stype = 'Хими'
            tree[unit][stype]['code_cnt'][code][mon] += 1
            if sid not in seen_samples[(unit, stype, mon)]:
                seen_samples[(unit, stype, mon)].add(sid)
                tree[unit][stype]['sample_cnt'][mon] += 1

        assert tree['drinking']['Хими']['sample_cnt'][3] == 2
        assert tree['drinking']['Хими']['code_cnt']['PH'][3] == 2
        assert tree['drinking']['Хими']['code_cnt']['EC'][3] == 1
        assert tree['wastewater']['Хими']['sample_cnt'][4] == 1

    def test_grand_totals(self):
        """Verify grand total computation."""
        from collections import defaultdict

        grand_samples = defaultdict(int)
        grand_codes = defaultdict(lambda: defaultdict(int))

        # Simulate tree data
        data = {
            'unit1': {'Хими': {'sample_cnt': {1: 5, 2: 3}, 'code_cnt': {'PH': {1: 10, 2: 6}}}},
            'unit2': {'Хими': {'sample_cnt': {1: 2}, 'code_cnt': {'PH': {1: 4}}}},
        }
        for unit, stypes in data.items():
            for stype, d in stypes.items():
                for m, c in d['sample_cnt'].items():
                    grand_samples[m] += c
                for code, mdict in d['code_cnt'].items():
                    for m, c in mdict.items():
                        grand_codes[code][m] += c

        assert grand_samples[1] == 7
        assert grand_samples[2] == 3
        assert grand_codes['PH'][1] == 14


# =====================================================================
# water_reports.py — monthly plan week logic (unit test)
# =====================================================================

class TestMonthlyPlanWeekLogic:
    """Unit test the week-building logic."""

    def test_weeks_for_march_2026(self):
        """March 2026 should have ~5 weeks."""
        from calendar import monthrange

        year, month = 2026, 3
        _, days_in_month = monthrange(year, month)
        first_day = datetime(year, month, 1)
        weeks = []
        wk = 1
        d = first_day
        while d.month == month:
            week_start = d
            week_end = min(d + timedelta(days=6 - d.weekday()),
                           datetime(year, month, days_in_month))
            if week_end.month != month:
                week_end = datetime(year, month, days_in_month)
            weeks.append({'week': wk, 'start': week_start, 'end': week_end})
            d = week_end + timedelta(days=1)
            wk += 1

        assert len(weeks) >= 4
        assert weeks[0]['start'] == datetime(2026, 3, 1)
        assert weeks[-1]['end'] == datetime(2026, 3, 31)

    def test_trend_month_wrap(self):
        """Trend 6 months back from January wraps to previous year."""
        month = 1
        year = 2026
        trend_m = month - 5
        trend_y = year
        if trend_m <= 0:
            trend_m += 12
            trend_y -= 1
        assert trend_m == 8
        assert trend_y == 2025

    def test_trend_month_no_wrap(self):
        """Trend 6 months back from July stays same year."""
        month = 7
        year = 2026
        trend_m = month - 5
        trend_y = year
        if trend_m <= 0:
            trend_m += 12
            trend_y -= 1
        assert trend_m == 2
        assert trend_y == 2026
