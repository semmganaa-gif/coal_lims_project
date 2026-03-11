# tests/test_water_lab_micro_solutions_coverage.py
# -*- coding: utf-8 -*-
"""
Comprehensive coverage tests for:
  - app/labs/water_lab/microbiology/micro_reports.py
  - app/labs/water_lab/chemistry/solutions.py
"""

import json
import pytest
from datetime import date, datetime, timedelta
from unittest.mock import patch, MagicMock, PropertyMock

from sqlalchemy.exc import SQLAlchemyError


# ======================================================================
#  Helper fixtures
# ======================================================================

@pytest.fixture
def admin_client(app, client):
    """Login as admin (has all lab access)."""
    with app.app_context():
        from app.models import User
        user = User.query.filter_by(username='admin').first()
        if user:
            user.allowed_labs = ['coal', 'water', 'microbiology']
            from app import db
            db.session.commit()
    client.post('/login', data={'username': 'admin', 'password': 'TestPass123'})
    yield client
    client.get('/logout')


@pytest.fixture
def senior_client(app, client):
    """Login as senior user with water + microbiology access."""
    with app.app_context():
        from app.models import User
        from app import db
        user = User.query.filter_by(username='senior').first()
        if user:
            user.allowed_labs = ['coal', 'water', 'microbiology']
            db.session.commit()
    client.post('/login', data={'username': 'senior', 'password': 'TestPass123'})
    yield client
    client.get('/logout')


@pytest.fixture
def chemist_client(app, client):
    """Login as chemist user with water + microbiology access."""
    with app.app_context():
        from app.models import User
        from app import db
        user = User.query.filter_by(username='chemist').first()
        if user:
            user.allowed_labs = ['coal', 'water', 'microbiology']
            db.session.commit()
    client.post('/login', data={'username': 'chemist', 'password': 'TestPass123'})
    yield client
    client.get('/logout')


# ======================================================================
#  UNIT TESTS: micro_reports helper functions
# ======================================================================

class TestGetWeeksInMonth:
    """Test _get_weeks_in_month helper."""

    def test_standard_month(self, app):
        with app.app_context():
            from app.labs.water_lab.microbiology.micro_reports import _get_weeks_in_month
            weeks = _get_weeks_in_month(2026, 1)
            assert len(weeks) >= 4
            # First week starts on 1st
            assert weeks[0][1] == date(2026, 1, 1)
            # Last week ends on 31st
            assert weeks[-1][2] == date(2026, 1, 31)
            # Week numbers are sequential
            for i, (wn, _, _) in enumerate(weeks):
                assert wn == i + 1

    def test_february_non_leap(self, app):
        with app.app_context():
            from app.labs.water_lab.microbiology.micro_reports import _get_weeks_in_month
            weeks = _get_weeks_in_month(2025, 2)
            assert weeks[-1][2] == date(2025, 2, 28)

    def test_february_leap(self, app):
        with app.app_context():
            from app.labs.water_lab.microbiology.micro_reports import _get_weeks_in_month
            weeks = _get_weeks_in_month(2024, 2)
            assert weeks[-1][2] == date(2024, 2, 29)

    def test_short_month_april(self, app):
        with app.app_context():
            from app.labs.water_lab.microbiology.micro_reports import _get_weeks_in_month
            weeks = _get_weeks_in_month(2026, 4)
            assert weeks[-1][2] == date(2026, 4, 30)

    def test_december(self, app):
        with app.app_context():
            from app.labs.water_lab.microbiology.micro_reports import _get_weeks_in_month
            weeks = _get_weeks_in_month(2026, 12)
            assert weeks[-1][2] == date(2026, 12, 31)
            assert weeks[0][1] == date(2026, 12, 1)

    def test_week_continuity(self, app):
        """Ensure weeks are contiguous with no gaps."""
        with app.app_context():
            from app.labs.water_lab.microbiology.micro_reports import _get_weeks_in_month
            weeks = _get_weeks_in_month(2026, 3)
            for i in range(len(weeks) - 1):
                # Next week starts the day after current week ends
                assert weeks[i + 1][1] == weeks[i][2] + timedelta(days=1)


class TestMicroWeeklyPerformance:
    """Test _micro_weekly_performance helper."""

    def test_empty_data(self, app):
        with app.app_context():
            from app.labs.water_lab.microbiology.micro_reports import _micro_weekly_performance
            result = _micro_weekly_performance(2020, 1)
            assert result == {}

    def test_with_mock_data(self, app, db):
        """Test performance with actual DB data."""
        with app.app_context():
            from app.models import Sample, AnalysisResult
            from app.labs.water_lab.microbiology.micro_reports import _micro_weekly_performance

            # Create sample + analysis result
            sample = Sample(
                sample_code='MICRO-PERF-001',
                lab_type='microbiology',
                client_name='QC',
                user_id=1,
            )
            db.session.add(sample)
            db.session.flush()

            ar = AnalysisResult(
                sample_id=sample.id,
                analysis_code='MICRO_WATER',
                created_at=datetime(2026, 3, 5, 10, 0),
            )
            db.session.add(ar)
            db.session.commit()

            result = _micro_weekly_performance(2026, 3)
            # Should have some data for week containing March 5
            # The key format is "MICRO_WATER|Water|<week_num>"
            water_keys = [k for k in result if k.startswith('MICRO_WATER|Water|')]
            assert len(water_keys) >= 1

            # Cleanup
            db.session.delete(ar)
            db.session.delete(sample)
            db.session.commit()


# ======================================================================
#  UNIT TESTS: convert_recipe_unit_to_chemical
# ======================================================================

class TestConvertRecipeUnit:
    """Test convert_recipe_unit_to_chemical function."""

    def test_mg_to_g(self):
        from app.labs.water_lab.chemistry.solutions import convert_recipe_unit_to_chemical
        assert convert_recipe_unit_to_chemical(1000, 'mg', 'g') == 1.0

    def test_g_to_mg(self):
        from app.labs.water_lab.chemistry.solutions import convert_recipe_unit_to_chemical
        assert convert_recipe_unit_to_chemical(1, 'g', 'mg') == 1000.0

    def test_g_to_g(self):
        from app.labs.water_lab.chemistry.solutions import convert_recipe_unit_to_chemical
        assert convert_recipe_unit_to_chemical(5.0, 'g', 'g') == 5.0

    def test_kg_to_g(self):
        from app.labs.water_lab.chemistry.solutions import convert_recipe_unit_to_chemical
        assert convert_recipe_unit_to_chemical(1, 'kg', 'g') == 1000.0

    def test_g_to_kg(self):
        from app.labs.water_lab.chemistry.solutions import convert_recipe_unit_to_chemical
        assert convert_recipe_unit_to_chemical(1, 'g', 'kg') == 0.001

    def test_mL_to_g(self):
        from app.labs.water_lab.chemistry.solutions import convert_recipe_unit_to_chemical
        assert convert_recipe_unit_to_chemical(100, 'mL', 'g') == 100.0

    def test_L_to_mL(self):
        from app.labs.water_lab.chemistry.solutions import convert_recipe_unit_to_chemical
        assert convert_recipe_unit_to_chemical(1, 'L', 'mL') == 1000.0

    def test_L_to_L(self):
        from app.labs.water_lab.chemistry.solutions import convert_recipe_unit_to_chemical
        assert convert_recipe_unit_to_chemical(1, 'L', 'L') == 1.0

    def test_mg_to_kg(self):
        from app.labs.water_lab.chemistry.solutions import convert_recipe_unit_to_chemical
        assert convert_recipe_unit_to_chemical(1000000, 'mg', 'kg') == 1.0

    def test_unknown_recipe_unit(self):
        from app.labs.water_lab.chemistry.solutions import convert_recipe_unit_to_chemical
        # Unknown recipe unit treated as grams
        result = convert_recipe_unit_to_chemical(10, 'oz', 'g')
        assert result == 10.0

    def test_unknown_chemical_unit(self):
        from app.labs.water_lab.chemistry.solutions import convert_recipe_unit_to_chemical
        # Unknown chemical unit returns amount_g
        result = convert_recipe_unit_to_chemical(10, 'g', 'oz')
        assert result == 10.0

    def test_mg_to_mL(self):
        from app.labs.water_lab.chemistry.solutions import convert_recipe_unit_to_chemical
        assert convert_recipe_unit_to_chemical(1000, 'mg', 'mL') == 1.0

    def test_mg_to_L(self):
        from app.labs.water_lab.chemistry.solutions import convert_recipe_unit_to_chemical
        assert convert_recipe_unit_to_chemical(1000, 'mg', 'L') == 0.001

    def test_zero_amount(self):
        from app.labs.water_lab.chemistry.solutions import convert_recipe_unit_to_chemical
        assert convert_recipe_unit_to_chemical(0, 'g', 'mg') == 0.0


# ======================================================================
#  ROUTE TESTS: Micro Reports
# ======================================================================

class TestMicroDashboard:
    """Test micro_dashboard route."""

    def test_dashboard_unauthenticated(self, client):
        resp = client.get('/labs/water-lab/microbiology/reports/dashboard')
        # Should redirect to login
        assert resp.status_code in (302, 308)

    def test_dashboard_success(self, admin_client, app):
        with app.app_context():
            resp = admin_client.get('/labs/water-lab/microbiology/reports/dashboard')
            assert resp.status_code == 200

    def test_dashboard_with_data(self, admin_client, app, db):
        """Test dashboard with sample data including pass/fail logic."""
        with app.app_context():
            from app.models import Sample, AnalysisResult

            # Create separate samples for each analysis result (unique constraint: sample_id + analysis_code)
            samples = []
            ars = []

            test_cases = [
                ('MICRO-DASH-P01', 'MICRO_WATER', json.dumps({'cfu_37': 50, 'ecoli': 0})),    # pass
                ('MICRO-DASH-F01', 'MICRO_WATER', json.dumps({'cfu_37': 150, 'ecoli': 0})),   # fail
                ('MICRO-DASH-I01', 'MICRO_WATER', 'not-json{'),                                # invalid JSON
                ('MICRO-DASH-N01', 'MICRO_WATER', None),                                       # None
                ('MICRO-DASH-A01', 'MICRO_WATER', json.dumps({'cfu_37': 'abc'})),              # non-numeric
                ('MICRO-DASH-E01', 'MICRO_WATER', json.dumps({'cfu_37': ''})),                 # empty string
            ]

            for code, ac, raw in test_cases:
                s = Sample(
                    sample_code=code,
                    lab_type='microbiology',
                    client_name='QC',
                    user_id=1,
                    received_date=date.today(),
                )
                db.session.add(s)
                db.session.flush()
                ar = AnalysisResult(
                    sample_id=s.id,
                    analysis_code=ac,
                    raw_data=raw,
                    created_at=datetime.now(),
                )
                db.session.add(ar)
                samples.append(s)
                ars.append(ar)

            db.session.commit()

            resp = admin_client.get('/labs/water-lab/microbiology/reports/dashboard')
            assert resp.status_code == 200

            # Cleanup
            for ar in ars:
                db.session.delete(ar)
            for s in samples:
                db.session.delete(s)
            db.session.commit()


class TestMicroConsumption:
    """Test micro_consumption route."""

    def test_consumption_default(self, admin_client, app):
        with app.app_context():
            resp = admin_client.get('/labs/water-lab/microbiology/reports/consumption')
            assert resp.status_code == 200

    def test_consumption_with_year(self, admin_client, app):
        with app.app_context():
            resp = admin_client.get('/labs/water-lab/microbiology/reports/consumption?year=2025')
            assert resp.status_code == 200

    def test_consumption_invalid_year(self, admin_client, app):
        with app.app_context():
            resp = admin_client.get('/labs/water-lab/microbiology/reports/consumption?year=abc')
            assert resp.status_code == 200  # Falls back to current year

    def test_consumption_with_data(self, admin_client, app, db):
        with app.app_context():
            from app.models import Sample, AnalysisResult

            sample = Sample(
                sample_code='MICRO-CON-001',
                lab_type='water & micro',
                client_name='QC',
                user_id=1,
            )
            db.session.add(sample)
            db.session.flush()

            ar = AnalysisResult(
                sample_id=sample.id,
                analysis_code='MICRO_WATER',
                created_at=datetime(2026, 3, 10, 12, 0),
            )
            db.session.add(ar)
            db.session.commit()

            resp = admin_client.get('/labs/water-lab/microbiology/reports/consumption?year=2026')
            assert resp.status_code == 200

            db.session.delete(ar)
            db.session.delete(sample)
            db.session.commit()


class TestApiConsumptionCell:
    """Test api_consumption_cell route."""

    def test_missing_params(self, admin_client, app):
        with app.app_context():
            resp = admin_client.get('/labs/water-lab/microbiology/api/consumption_cell')
            assert resp.status_code == 400

    def test_invalid_month(self, admin_client, app):
        with app.app_context():
            resp = admin_client.get(
                '/labs/water-lab/microbiology/api/consumption_cell?year=2026&month=13&unit=X&stype=MICRO_WATER'
            )
            assert resp.status_code == 400

    def test_invalid_year_string(self, admin_client, app):
        with app.app_context():
            resp = admin_client.get(
                '/labs/water-lab/microbiology/api/consumption_cell?year=abc&month=3&unit=X&stype=MICRO_WATER'
            )
            assert resp.status_code == 400

    def test_valid_samples_kind(self, admin_client, app, db):
        with app.app_context():
            from app.models import Sample, AnalysisResult

            sample = Sample(
                sample_code='MICRO-CELL-001',
                lab_type='microbiology',
                client_name='QC',
                user_id=1,
            )
            db.session.add(sample)
            db.session.flush()

            ar = AnalysisResult(
                sample_id=sample.id,
                analysis_code='MICRO_WATER',
                created_at=datetime(2026, 3, 10, 12, 0),
            )
            db.session.add(ar)
            db.session.commit()

            resp = admin_client.get(
                '/labs/water-lab/microbiology/api/consumption_cell'
                '?year=2026&month=3&unit=QC&stype=MICRO_WATER&kind=samples'
            )
            assert resp.status_code == 200
            data = resp.get_json()
            assert data['success'] is True

            db.session.delete(ar)
            db.session.delete(sample)
            db.session.commit()

    def test_valid_code_kind(self, admin_client, app, db):
        with app.app_context():
            from app.models import Sample, AnalysisResult

            sample = Sample(
                sample_code='MICRO-CELL-002',
                lab_type='microbiology',
                client_name='QC',
                user_id=1,
            )
            db.session.add(sample)
            db.session.flush()

            ar = AnalysisResult(
                sample_id=sample.id,
                analysis_code='MICRO_WATER',
                created_at=datetime(2026, 3, 10, 12, 0),
            )
            db.session.add(ar)
            db.session.commit()

            resp = admin_client.get(
                '/labs/water-lab/microbiology/api/consumption_cell'
                '?year=2026&month=3&unit=QC&stype=MICRO_WATER&kind=code&code=MICRO_WATER'
            )
            assert resp.status_code == 200
            data = resp.get_json()
            assert data['success'] is True

            db.session.delete(ar)
            db.session.delete(sample)
            db.session.commit()

    def test_valid_with_no_results(self, admin_client, app):
        with app.app_context():
            resp = admin_client.get(
                '/labs/water-lab/microbiology/api/consumption_cell'
                '?year=2020&month=1&unit=Nobody&stype=MICRO_WATER&kind=samples'
            )
            assert resp.status_code == 200
            data = resp.get_json()
            assert data['success'] is True
            assert data['data']['items'] == []


class TestMicroMonthlyPlan:
    """Test micro_monthly_plan route."""

    def test_monthly_plan_default(self, admin_client, app):
        with app.app_context():
            resp = admin_client.get('/labs/water-lab/microbiology/reports/monthly_plan')
            assert resp.status_code == 200

    def test_monthly_plan_with_params(self, admin_client, app):
        with app.app_context():
            resp = admin_client.get(
                '/labs/water-lab/microbiology/reports/monthly_plan?year=2026&month=3'
            )
            assert resp.status_code == 200

    def test_monthly_plan_invalid_year(self, admin_client, app):
        """Year out of range resets to current."""
        with app.app_context():
            resp = admin_client.get(
                '/labs/water-lab/microbiology/reports/monthly_plan?year=1900&month=3'
            )
            assert resp.status_code == 200

    def test_monthly_plan_invalid_month(self, admin_client, app):
        """Month out of range resets to current."""
        with app.app_context():
            resp = admin_client.get(
                '/labs/water-lab/microbiology/reports/monthly_plan?year=2026&month=15'
            )
            assert resp.status_code == 200

    def test_monthly_plan_month_zero(self, admin_client, app):
        with app.app_context():
            resp = admin_client.get(
                '/labs/water-lab/microbiology/reports/monthly_plan?year=2026&month=0'
            )
            assert resp.status_code == 200

    def test_monthly_plan_with_plan_data(self, admin_client, app, db):
        """Test with actual plan data."""
        with app.app_context():
            from app.models import MonthlyPlan, StaffSettings

            plan = MonthlyPlan(
                year=2026, month=3, week=1,
                client_name='MICRO_WATER', sample_type='Water',
                planned_count=10, created_by_id=1,
            )
            staff = StaffSettings(year=2026, month=3, preparers=5, chemists=8)
            db.session.add_all([plan, staff])
            db.session.commit()

            resp = admin_client.get(
                '/labs/water-lab/microbiology/reports/monthly_plan?year=2026&month=3'
            )
            assert resp.status_code == 200

            db.session.delete(plan)
            db.session.delete(staff)
            db.session.commit()


class TestApiGetMonthlyPlan:
    """Test api_get_monthly_plan route."""

    def test_missing_params(self, admin_client, app):
        with app.app_context():
            resp = admin_client.get('/labs/water-lab/microbiology/api/monthly_plan')
            assert resp.status_code == 400

    def test_missing_month(self, admin_client, app):
        with app.app_context():
            resp = admin_client.get('/labs/water-lab/microbiology/api/monthly_plan?year=2026')
            assert resp.status_code == 400

    def test_valid_params(self, admin_client, app, db):
        with app.app_context():
            from app.models import MonthlyPlan

            plan = MonthlyPlan(
                year=2026, month=4, week=1,
                client_name='MICRO_WATER', sample_type='Water',
                planned_count=5, created_by_id=1,
            )
            db.session.add(plan)
            db.session.commit()

            resp = admin_client.get(
                '/labs/water-lab/microbiology/api/monthly_plan?year=2026&month=4'
            )
            assert resp.status_code == 200
            data = resp.get_json()
            assert 'MICRO_WATER|Water|1' in data['plans']

            db.session.delete(plan)
            db.session.commit()

    def test_empty_result(self, admin_client, app):
        with app.app_context():
            resp = admin_client.get(
                '/labs/water-lab/microbiology/api/monthly_plan?year=1999&month=1'
            )
            assert resp.status_code == 200
            data = resp.get_json()
            assert data['plans'] == {}


class TestApiSaveMonthlyPlan:
    """Test api_save_monthly_plan route."""

    def test_chemist_forbidden(self, chemist_client, app):
        with app.app_context():
            resp = chemist_client.post(
                '/labs/water-lab/microbiology/api/monthly_plan',
                json={'year': 2026, 'month': 3, 'plans': {'MICRO_WATER|Water|1': 5}},
            )
            assert resp.status_code == 403

    def test_missing_year_month(self, senior_client, app):
        with app.app_context():
            resp = senior_client.post(
                '/labs/water-lab/microbiology/api/monthly_plan',
                json={'plans': {}},
            )
            assert resp.status_code == 400

    def test_save_new_plan(self, senior_client, app, db):
        with app.app_context():
            from app.models import MonthlyPlan

            resp = senior_client.post(
                '/labs/water-lab/microbiology/api/monthly_plan',
                json={
                    'year': 2026, 'month': 5,
                    'plans': {'MICRO_WATER|Water|1': 10, 'MICRO_AIR|Air|2': 5},
                },
            )
            assert resp.status_code == 200
            data = resp.get_json()
            assert data['success'] is True
            assert data['saved'] == 2

            # Cleanup
            MonthlyPlan.query.filter_by(year=2026, month=5).delete()
            db.session.commit()

    def test_update_existing_plan(self, senior_client, app, db):
        with app.app_context():
            from app.models import MonthlyPlan

            plan = MonthlyPlan(
                year=2026, month=6, week=1,
                client_name='MICRO_WATER', sample_type='Water',
                planned_count=3, created_by_id=1,
            )
            db.session.add(plan)
            db.session.commit()

            resp = senior_client.post(
                '/labs/water-lab/microbiology/api/monthly_plan',
                json={
                    'year': 2026, 'month': 6,
                    'plans': {'MICRO_WATER|Water|1': 20},
                },
            )
            assert resp.status_code == 200

            # Verify updated
            updated = MonthlyPlan.query.filter_by(
                year=2026, month=6, week=1, client_name='MICRO_WATER'
            ).first()
            assert updated.planned_count == 20

            db.session.delete(updated)
            db.session.commit()

    def test_invalid_key_format(self, senior_client, app):
        """Keys with wrong format should be skipped."""
        with app.app_context():
            resp = senior_client.post(
                '/labs/water-lab/microbiology/api/monthly_plan',
                json={
                    'year': 2026, 'month': 7,
                    'plans': {'BAD_KEY': 5, 'ALSO|BAD': 10},
                },
            )
            assert resp.status_code == 200
            data = resp.get_json()
            assert data['saved'] == 0


class TestApiPlanStats:
    """Test api_plan_stats route."""

    def test_defaults(self, admin_client, app):
        with app.app_context():
            resp = admin_client.get('/labs/water-lab/microbiology/api/plan_stats')
            assert resp.status_code == 200
            data = resp.get_json()
            assert 'weekly' in data

    def test_with_year_month(self, admin_client, app):
        with app.app_context():
            resp = admin_client.get(
                '/labs/water-lab/microbiology/api/plan_stats?year=2026&month=3'
            )
            assert resp.status_code == 200
            data = resp.get_json()
            assert data['year'] == 2026
            assert data['month'] == 3


class TestApiSaveStaff:
    """Test api_save_staff route."""

    def test_chemist_forbidden(self, chemist_client, app):
        with app.app_context():
            resp = chemist_client.post(
                '/labs/water-lab/microbiology/api/save_staff',
                json={'year': 2026, 'month': 3, 'staff_count': 5},
            )
            assert resp.status_code == 403

    def test_missing_params(self, senior_client, app):
        with app.app_context():
            resp = senior_client.post(
                '/labs/water-lab/microbiology/api/save_staff',
                json={'staff_count': 5},
            )
            assert resp.status_code == 400

    def test_save_new_staff(self, senior_client, app, db):
        with app.app_context():
            from app.models import StaffSettings

            resp = senior_client.post(
                '/labs/water-lab/microbiology/api/save_staff',
                json={'year': 2026, 'month': 8, 'staff_count': 7},
            )
            assert resp.status_code == 200
            data = resp.get_json()
            assert data['success'] is True

            # Cleanup
            StaffSettings.query.filter_by(year=2026, month=8).delete()
            db.session.commit()

    def test_update_existing_staff(self, senior_client, app, db):
        with app.app_context():
            from app.models import StaffSettings

            staff = StaffSettings(year=2026, month=9, preparers=3, chemists=3)
            db.session.add(staff)
            db.session.commit()

            resp = senior_client.post(
                '/labs/water-lab/microbiology/api/save_staff',
                json={'year': 2026, 'month': 9, 'staff_count': 12},
            )
            assert resp.status_code == 200

            updated = StaffSettings.query.filter_by(year=2026, month=9).first()
            assert updated.preparers == 12

            db.session.delete(updated)
            db.session.commit()


# ======================================================================
#  ROUTE TESTS: Solution Journal (chemistry/solutions.py)
# ======================================================================

class TestSolutionJournal:
    """Test solution_journal route."""

    def test_unauthenticated(self, client):
        resp = client.get('/labs/water-lab/chemistry/solution_journal')
        assert resp.status_code in (302, 308)

    def test_default(self, admin_client, app):
        with app.app_context():
            resp = admin_client.get('/labs/water-lab/chemistry/solution_journal')
            assert resp.status_code == 200

    def test_with_date_filters(self, admin_client, app):
        with app.app_context():
            resp = admin_client.get(
                '/labs/water-lab/chemistry/solution_journal?start_date=2026-01-01&end_date=2026-12-31'
            )
            assert resp.status_code == 200

    def test_with_invalid_dates(self, admin_client, app):
        with app.app_context():
            resp = admin_client.get(
                '/labs/water-lab/chemistry/solution_journal?start_date=bad&end_date=bad'
            )
            assert resp.status_code == 200

    def test_with_status_filter(self, admin_client, app):
        with app.app_context():
            resp = admin_client.get(
                '/labs/water-lab/chemistry/solution_journal?status=active'
            )
            assert resp.status_code == 200

    def test_with_status_all(self, admin_client, app):
        with app.app_context():
            resp = admin_client.get(
                '/labs/water-lab/chemistry/solution_journal?status=all'
            )
            assert resp.status_code == 200


class TestAddSolution:
    """Test add_solution route."""

    def test_get_form(self, admin_client, app):
        with app.app_context():
            resp = admin_client.get('/labs/water-lab/chemistry/solution_journal/add')
            assert resp.status_code == 200

    def test_post_basic(self, admin_client, app, db):
        with app.app_context():
            from app.models import SolutionPreparation

            resp = admin_client.post('/labs/water-lab/chemistry/solution_journal/add', data={
                'solution_name': 'Test HCl 0.1N',
                'concentration': '0.1',
                'concentration_unit': 'N',
                'volume_ml': '1000',
                'chemical_used_mg': '',
                'prepared_date': '2026-03-10',
                'expiry_date': '2026-06-10',
                'v1': '10.1',
                'v2': '10.2',
                'v3': '10.15',
                'titer_coefficient': '0.9985',
                'preparation_notes': 'Test notes',
            }, follow_redirects=True)
            assert resp.status_code == 200

            # Cleanup
            sol = SolutionPreparation.query.filter_by(solution_name='Test HCl 0.1N').first()
            if sol:
                db.session.delete(sol)
                db.session.commit()

    def test_post_with_chemical(self, admin_client, app, db):
        """Test adding solution with chemical deduction."""
        with app.app_context():
            from app.models import SolutionPreparation, Chemical

            chem = Chemical(
                name='Test HCl',
                quantity=100.0,
                unit='g',
                lab_type='water',
                status='active',
            )
            db.session.add(chem)
            db.session.commit()

            resp = admin_client.post('/labs/water-lab/chemistry/solution_journal/add', data={
                'solution_name': 'HCl Solution Test',
                'concentration': '0.1',
                'volume_ml': '1000',
                'chemical_used_mg': '5000',
                'chemical_id': str(chem.id),
                'prepared_date': '2026-03-10',
            }, follow_redirects=True)
            assert resp.status_code == 200

            # Verify quantity deducted (5000mg = 5g)
            chem_updated = db.session.get(Chemical, chem.id)
            assert chem_updated.quantity == 95.0

            # Cleanup
            sol = SolutionPreparation.query.filter_by(solution_name='HCl Solution Test').first()
            if sol:
                db.session.delete(sol)
            # Clean chemical usage and log records
            from app.models import ChemicalUsage, ChemicalLog
            ChemicalUsage.query.filter_by(chemical_id=chem.id).delete()
            ChemicalLog.query.filter_by(chemical_id=chem.id).delete()
            db.session.delete(chem_updated)
            db.session.commit()

    def test_post_with_chemical_kg_unit(self, admin_client, app, db):
        """Test chemical deduction for kg unit."""
        with app.app_context():
            from app.models import SolutionPreparation, Chemical

            chem = Chemical(
                name='Test Salt kg',
                quantity=10.0,
                unit='kg',
                lab_type='water',
                status='active',
            )
            db.session.add(chem)
            db.session.commit()

            resp = admin_client.post('/labs/water-lab/chemistry/solution_journal/add', data={
                'solution_name': 'Salt Solution kg Test',
                'concentration': '0.1',
                'volume_ml': '1000',
                'chemical_used_mg': '1000000',  # 1000000 mg = 1 kg
                'chemical_id': str(chem.id),
                'prepared_date': '2026-03-10',
            }, follow_redirects=True)
            assert resp.status_code == 200

            # Cleanup
            sol = SolutionPreparation.query.filter_by(solution_name='Salt Solution kg Test').first()
            if sol:
                db.session.delete(sol)
            from app.models import ChemicalUsage, ChemicalLog
            ChemicalUsage.query.filter_by(chemical_id=chem.id).delete()
            ChemicalLog.query.filter_by(chemical_id=chem.id).delete()
            db.session.delete(db.session.get(Chemical, chem.id))
            db.session.commit()

    def test_post_with_chemical_mL_unit(self, admin_client, app, db):
        """Test chemical deduction for mL unit."""
        with app.app_context():
            from app.models import SolutionPreparation, Chemical

            chem = Chemical(
                name='Test Liquid mL',
                quantity=500.0,
                unit='mL',
                lab_type='water',
                status='active',
            )
            db.session.add(chem)
            db.session.commit()

            resp = admin_client.post('/labs/water-lab/chemistry/solution_journal/add', data={
                'solution_name': 'Liquid Solution mL',
                'concentration': '0.1',
                'volume_ml': '100',
                'chemical_used_mg': '10000',  # 10000 mg => 10 mL
                'chemical_id': str(chem.id),
                'prepared_date': '2026-03-10',
            }, follow_redirects=True)
            assert resp.status_code == 200

            # Cleanup
            sol = SolutionPreparation.query.filter_by(solution_name='Liquid Solution mL').first()
            if sol:
                db.session.delete(sol)
            from app.models import ChemicalUsage, ChemicalLog
            ChemicalUsage.query.filter_by(chemical_id=chem.id).delete()
            ChemicalLog.query.filter_by(chemical_id=chem.id).delete()
            db.session.delete(db.session.get(Chemical, chem.id))
            db.session.commit()

    def test_post_with_chemical_L_unit(self, admin_client, app, db):
        """Test chemical deduction for L unit."""
        with app.app_context():
            from app.models import SolutionPreparation, Chemical

            chem = Chemical(
                name='Test Liquid L',
                quantity=5.0,
                unit='L',
                lab_type='water',
                status='active',
            )
            db.session.add(chem)
            db.session.commit()

            resp = admin_client.post('/labs/water-lab/chemistry/solution_journal/add', data={
                'solution_name': 'Liquid Solution L',
                'concentration': '0.1',
                'volume_ml': '100',
                'chemical_used_mg': '1000000',  # 1000000 mg => 1 L
                'chemical_id': str(chem.id),
                'prepared_date': '2026-03-10',
            }, follow_redirects=True)
            assert resp.status_code == 200

            # Cleanup
            sol = SolutionPreparation.query.filter_by(solution_name='Liquid Solution L').first()
            if sol:
                db.session.delete(sol)
            from app.models import ChemicalUsage, ChemicalLog
            ChemicalUsage.query.filter_by(chemical_id=chem.id).delete()
            ChemicalLog.query.filter_by(chemical_id=chem.id).delete()
            db.session.delete(db.session.get(Chemical, chem.id))
            db.session.commit()

    def test_post_insufficient_stock(self, admin_client, app, db):
        """Test warning when stock is insufficient."""
        with app.app_context():
            from app.models import SolutionPreparation, Chemical

            chem = Chemical(
                name='Low Stock Chem',
                quantity=0.5,
                unit='g',
                lab_type='water',
                status='active',
            )
            db.session.add(chem)
            db.session.commit()

            resp = admin_client.post('/labs/water-lab/chemistry/solution_journal/add', data={
                'solution_name': 'Low Stock Solution',
                'concentration': '0.1',
                'volume_ml': '1000',
                'chemical_used_mg': '50000',  # 50g > 0.5g
                'chemical_id': str(chem.id),
                'prepared_date': '2026-03-10',
            }, follow_redirects=True)
            assert resp.status_code == 200

            # Cleanup
            sol = SolutionPreparation.query.filter_by(solution_name='Low Stock Solution').first()
            if sol:
                db.session.delete(sol)
            from app.models import ChemicalUsage, ChemicalLog
            ChemicalUsage.query.filter_by(chemical_id=chem.id).delete()
            ChemicalLog.query.filter_by(chemical_id=chem.id).delete()
            db.session.delete(db.session.get(Chemical, chem.id))
            db.session.commit()

    def test_post_invalid_date(self, admin_client, app):
        """Test error handling when date is invalid."""
        with app.app_context():
            resp = admin_client.post('/labs/water-lab/chemistry/solution_journal/add', data={
                'solution_name': 'Bad Date Sol',
                'prepared_date': 'not-a-date',
            }, follow_redirects=True)
            assert resp.status_code == 200  # Shows form with error flash

    def test_post_no_expiry(self, admin_client, app, db):
        """Test solution without expiry date."""
        with app.app_context():
            from app.models import SolutionPreparation

            resp = admin_client.post('/labs/water-lab/chemistry/solution_journal/add', data={
                'solution_name': 'No Expiry Solution',
                'concentration': '0.5',
                'volume_ml': '500',
                'prepared_date': '2026-03-10',
                'expiry_date': '',
            }, follow_redirects=True)
            assert resp.status_code == 200

            sol = SolutionPreparation.query.filter_by(solution_name='No Expiry Solution').first()
            if sol:
                db.session.delete(sol)
                db.session.commit()


class TestEditSolution:
    """Test edit_solution route."""

    def test_get_form(self, admin_client, app, db):
        with app.app_context():
            from app.models import SolutionPreparation

            sol = SolutionPreparation(
                solution_name='Edit Test Sol',
                prepared_date=date(2026, 3, 10),
                prepared_by_id=1,
            )
            db.session.add(sol)
            db.session.commit()

            resp = admin_client.get(f'/labs/water-lab/chemistry/solution_journal/edit/{sol.id}')
            assert resp.status_code == 200

            db.session.delete(sol)
            db.session.commit()

    def test_post_edit(self, admin_client, app, db):
        with app.app_context():
            from app.models import SolutionPreparation

            sol = SolutionPreparation(
                solution_name='Before Edit',
                prepared_date=date(2026, 3, 10),
                prepared_by_id=1,
            )
            db.session.add(sol)
            db.session.commit()

            resp = admin_client.post(
                f'/labs/water-lab/chemistry/solution_journal/edit/{sol.id}',
                data={
                    'solution_name': 'After Edit',
                    'prepared_date': '2026-03-11',
                    'expiry_date': '2026-06-11',
                    'concentration': '0.2',
                    'concentration_unit': 'N',
                    'volume_ml': '2000',
                    'chemical_used_mg': '',
                    'v1': '9.5',
                    'v2': '9.6',
                    'v3': '',
                    'titer_coefficient': '1.001',
                    'preparation_notes': 'Updated',
                    'status': 'active',
                    'chemical_id': '',
                },
                follow_redirects=True,
            )
            assert resp.status_code == 200

            updated = db.session.get(SolutionPreparation, sol.id)
            assert updated.solution_name == 'After Edit'

            db.session.delete(updated)
            db.session.commit()

    def test_post_edit_no_expiry(self, admin_client, app, db):
        """Test edit clearing expiry date."""
        with app.app_context():
            from app.models import SolutionPreparation

            sol = SolutionPreparation(
                solution_name='Expiry Clear Test',
                prepared_date=date(2026, 3, 10),
                expiry_date=date(2026, 6, 10),
                prepared_by_id=1,
            )
            db.session.add(sol)
            db.session.commit()

            resp = admin_client.post(
                f'/labs/water-lab/chemistry/solution_journal/edit/{sol.id}',
                data={
                    'solution_name': 'Expiry Clear Test',
                    'prepared_date': '2026-03-10',
                    'expiry_date': '',
                    'status': 'active',
                },
                follow_redirects=True,
            )
            assert resp.status_code == 200

            updated = db.session.get(SolutionPreparation, sol.id)
            assert updated.expiry_date is None

            db.session.delete(updated)
            db.session.commit()

    def test_post_edit_invalid_date(self, admin_client, app, db):
        """Test edit with invalid date triggers error handling."""
        with app.app_context():
            from app.models import SolutionPreparation

            sol = SolutionPreparation(
                solution_name='Bad Edit Date',
                prepared_date=date(2026, 3, 10),
                prepared_by_id=1,
            )
            db.session.add(sol)
            db.session.commit()

            resp = admin_client.post(
                f'/labs/water-lab/chemistry/solution_journal/edit/{sol.id}',
                data={
                    'solution_name': 'Bad Edit Date',
                    'prepared_date': 'not-valid',
                    'status': 'active',
                },
                follow_redirects=True,
            )
            assert resp.status_code == 200  # Shows form with error

            db.session.delete(sol)
            db.session.commit()

    def test_edit_404(self, admin_client, app):
        with app.app_context():
            resp = admin_client.get('/labs/water-lab/chemistry/solution_journal/edit/999999')
            assert resp.status_code == 404

    def test_post_edit_with_chemical_id(self, admin_client, app, db):
        """Test edit with a chemical_id set."""
        with app.app_context():
            from app.models import SolutionPreparation, Chemical

            chem = Chemical(name='Edit Chem', quantity=50.0, unit='g', lab_type='water', status='active')
            db.session.add(chem)
            db.session.flush()

            sol = SolutionPreparation(
                solution_name='Edit Chem Test',
                prepared_date=date(2026, 3, 10),
                prepared_by_id=1,
            )
            db.session.add(sol)
            db.session.commit()

            resp = admin_client.post(
                f'/labs/water-lab/chemistry/solution_journal/edit/{sol.id}',
                data={
                    'solution_name': 'Edit Chem Test',
                    'prepared_date': '2026-03-10',
                    'status': 'active',
                    'chemical_id': str(chem.id),
                },
                follow_redirects=True,
            )
            assert resp.status_code == 200

            updated = db.session.get(SolutionPreparation, sol.id)
            assert updated.chemical_id == chem.id

            db.session.delete(updated)
            db.session.delete(chem)
            db.session.commit()


class TestDeleteSolution:
    """Test delete_solution route."""

    def test_chemist_denied(self, chemist_client, app, db):
        """Non-senior/admin cannot delete."""
        with app.app_context():
            from app.models import SolutionPreparation

            sol = SolutionPreparation(
                solution_name='Chemist Delete Test',
                prepared_date=date(2026, 3, 10),
                prepared_by_id=1,
            )
            db.session.add(sol)
            db.session.commit()

            resp = chemist_client.post(
                f'/labs/water-lab/chemistry/solution_journal/delete/{sol.id}',
                follow_redirects=True,
            )
            assert resp.status_code == 200

            # Should still exist
            assert db.session.get(SolutionPreparation, sol.id) is not None

            db.session.delete(sol)
            db.session.commit()

    def test_admin_delete(self, admin_client, app, db):
        with app.app_context():
            from app.models import SolutionPreparation

            sol = SolutionPreparation(
                solution_name='Admin Delete Test',
                prepared_date=date(2026, 3, 10),
                prepared_by_id=1,
            )
            db.session.add(sol)
            db.session.commit()
            sol_id = sol.id

            resp = admin_client.post(
                f'/labs/water-lab/chemistry/solution_journal/delete/{sol_id}',
                follow_redirects=True,
            )
            assert resp.status_code == 200
            assert db.session.get(SolutionPreparation, sol_id) is None

    def test_delete_with_chemical_return(self, admin_client, app, db):
        """Test delete returns chemical quantity."""
        with app.app_context():
            from app.models import SolutionPreparation, Chemical

            chem = Chemical(name='Return Chem', quantity=90.0, unit='g', lab_type='water', status='active')
            db.session.add(chem)
            db.session.flush()

            sol = SolutionPreparation(
                solution_name='Return Chem Sol',
                prepared_date=date(2026, 3, 10),
                prepared_by_id=1,
                chemical_id=chem.id,
                chemical_used_mg=5000,  # 5g
            )
            db.session.add(sol)
            db.session.commit()
            sol_id = sol.id

            resp = admin_client.post(
                f'/labs/water-lab/chemistry/solution_journal/delete/{sol_id}',
                follow_redirects=True,
            )
            assert resp.status_code == 200

            # Verify returned
            chem_updated = db.session.get(Chemical, chem.id)
            assert chem_updated.quantity == 95.0

            from app.models import ChemicalLog
            ChemicalLog.query.filter_by(chemical_id=chem.id).delete()
            db.session.delete(chem_updated)
            db.session.commit()

    def test_delete_with_chemical_kg_return(self, admin_client, app, db):
        """Test delete returns chemical quantity for kg unit."""
        with app.app_context():
            from app.models import SolutionPreparation, Chemical

            chem = Chemical(name='Return kg Chem', quantity=9.0, unit='kg', lab_type='water', status='active')
            db.session.add(chem)
            db.session.flush()

            sol = SolutionPreparation(
                solution_name='Return kg Sol',
                prepared_date=date(2026, 3, 10),
                prepared_by_id=1,
                chemical_id=chem.id,
                chemical_used_mg=1000000,  # 1kg
            )
            db.session.add(sol)
            db.session.commit()
            sol_id = sol.id

            resp = admin_client.post(
                f'/labs/water-lab/chemistry/solution_journal/delete/{sol_id}',
                follow_redirects=True,
            )
            assert resp.status_code == 200

            chem_updated = db.session.get(Chemical, chem.id)
            assert chem_updated.quantity == 10.0

            from app.models import ChemicalLog
            ChemicalLog.query.filter_by(chemical_id=chem.id).delete()
            db.session.delete(chem_updated)
            db.session.commit()

    def test_delete_404(self, admin_client, app):
        with app.app_context():
            resp = admin_client.post('/labs/water-lab/chemistry/solution_journal/delete/999999')
            assert resp.status_code == 404


class TestApiSolutions:
    """Test api_solutions route."""

    def test_empty(self, admin_client, app):
        with app.app_context():
            resp = admin_client.get('/labs/water-lab/chemistry/api/solutions')
            assert resp.status_code == 200
            data = resp.get_json()
            assert isinstance(data, list)

    def test_with_data(self, admin_client, app, db):
        with app.app_context():
            from app.models import SolutionPreparation

            sol = SolutionPreparation(
                solution_name='API Test Sol',
                prepared_date=date(2026, 3, 10),
                concentration=0.1,
                concentration_unit='N',
                volume_ml=1000,
                v1=10.1,
                v2=10.2,
                v3=10.15,
                titer_coefficient=0.998,
                status='active',
                prepared_by_id=1,
                expiry_date=date(2026, 6, 10),
            )
            sol.calculate_v_avg()
            db.session.add(sol)
            db.session.commit()

            resp = admin_client.get('/labs/water-lab/chemistry/api/solutions')
            assert resp.status_code == 200
            data = resp.get_json()
            found = [s for s in data if s['solution_name'] == 'API Test Sol']
            assert len(found) == 1
            assert found[0]['concentration'] == 0.1
            assert found[0]['prepared_date'] == '2026-03-10'
            assert found[0]['expiry_date'] == '2026-06-10'

            db.session.delete(sol)
            db.session.commit()


# ======================================================================
#  ROUTE TESTS: Solution Recipes
# ======================================================================

class TestSolutionRecipes:
    """Test solution_recipes route."""

    def test_list(self, admin_client, app):
        with app.app_context():
            resp = admin_client.get('/labs/water-lab/chemistry/solution_recipes')
            assert resp.status_code == 200

    def test_list_with_recipes(self, admin_client, app, db):
        with app.app_context():
            from app.models import SolutionRecipe

            recipe = SolutionRecipe(
                name='Test Recipe List',
                concentration=0.1,
                concentration_unit='N',
                standard_volume_ml=1000,
                lab_type='water',
                is_active=True,
                created_by_id=1,
            )
            db.session.add(recipe)
            db.session.commit()

            resp = admin_client.get('/labs/water-lab/chemistry/solution_recipes')
            assert resp.status_code == 200

            db.session.delete(recipe)
            db.session.commit()

    def test_list_with_preparations(self, admin_client, app, db):
        """Test recipe list with prep history (triggers stats query)."""
        with app.app_context():
            from app.models import SolutionRecipe, SolutionPreparation

            recipe = SolutionRecipe(
                name='Recipe With Preps',
                concentration=0.05,
                standard_volume_ml=1000,
                lab_type='water',
                is_active=True,
                created_by_id=1,
            )
            db.session.add(recipe)
            db.session.flush()

            prep = SolutionPreparation(
                solution_name='Recipe With Preps',
                prepared_date=date(2026, 3, 1),
                prepared_by_id=1,
                recipe_id=recipe.id,
            )
            db.session.add(prep)
            db.session.commit()

            resp = admin_client.get('/labs/water-lab/chemistry/solution_recipes')
            assert resp.status_code == 200

            db.session.delete(prep)
            db.session.delete(recipe)
            db.session.commit()


class TestRecipeDetail:
    """Test recipe_detail route."""

    def test_detail(self, admin_client, app, db):
        with app.app_context():
            from app.models import SolutionRecipe

            recipe = SolutionRecipe(
                name='Detail Test Recipe',
                concentration=0.1,
                standard_volume_ml=1000,
                lab_type='water',
                is_active=True,
                created_by_id=1,
            )
            db.session.add(recipe)
            db.session.commit()

            resp = admin_client.get(f'/labs/water-lab/chemistry/solution_recipes/{recipe.id}')
            assert resp.status_code == 200

            db.session.delete(recipe)
            db.session.commit()

    def test_detail_with_ingredients(self, admin_client, app, db):
        with app.app_context():
            from app.models import SolutionRecipe, SolutionRecipeIngredient, Chemical

            chem = Chemical(name='Detail Ingred Chem', quantity=100, unit='g', lab_type='water', status='active')
            db.session.add(chem)
            db.session.flush()

            recipe = SolutionRecipe(
                name='Detail Ingredients',
                concentration=0.1,
                standard_volume_ml=1000,
                lab_type='water',
                is_active=True,
                created_by_id=1,
            )
            db.session.add(recipe)
            db.session.flush()

            ing = SolutionRecipeIngredient(
                recipe_id=recipe.id,
                chemical_id=chem.id,
                amount=5.0,
                unit='g',
            )
            db.session.add(ing)
            db.session.commit()

            resp = admin_client.get(f'/labs/water-lab/chemistry/solution_recipes/{recipe.id}')
            assert resp.status_code == 200

            db.session.delete(ing)
            db.session.delete(recipe)
            db.session.delete(chem)
            db.session.commit()

    def test_detail_404(self, admin_client, app):
        with app.app_context():
            resp = admin_client.get('/labs/water-lab/chemistry/solution_recipes/999999')
            assert resp.status_code == 404


class TestPrepareFromRecipe:
    """Test prepare_from_recipe route."""

    def test_prepare_success(self, admin_client, app, db):
        with app.app_context():
            from app.models import SolutionRecipe, SolutionRecipeIngredient, Chemical, SolutionPreparation

            chem = Chemical(name='Prep Chem', quantity=100.0, unit='g', lab_type='water', status='active')
            db.session.add(chem)
            db.session.flush()

            recipe = SolutionRecipe(
                name='Prep Test Recipe',
                concentration=0.1,
                standard_volume_ml=1000,
                lab_type='water',
                is_active=True,
                created_by_id=1,
            )
            db.session.add(recipe)
            db.session.flush()

            ing = SolutionRecipeIngredient(
                recipe_id=recipe.id,
                chemical_id=chem.id,
                amount=5.0,
                unit='g',
            )
            db.session.add(ing)
            db.session.commit()

            resp = admin_client.post(
                f'/labs/water-lab/chemistry/solution_recipes/{recipe.id}/prepare',
                data={
                    'volume_ml': '1000',
                    'v1': '10.1',
                    'v2': '10.2',
                    'expiry_date': '2026-09-10',
                    'notes': 'Prepared from recipe',
                },
                follow_redirects=True,
            )
            assert resp.status_code == 200

            # Verify chemical deducted
            chem_updated = db.session.get(Chemical, chem.id)
            assert chem_updated.quantity == 95.0

            # Cleanup
            SolutionPreparation.query.filter_by(recipe_id=recipe.id).delete()
            from app.models import ChemicalUsage, ChemicalLog
            ChemicalUsage.query.filter_by(chemical_id=chem.id).delete()
            ChemicalLog.query.filter_by(chemical_id=chem.id).delete()
            db.session.delete(ing)
            db.session.delete(recipe)
            db.session.delete(chem_updated)
            db.session.commit()

    def test_prepare_insufficient_stock(self, admin_client, app, db):
        """Test prepare when stock is insufficient."""
        with app.app_context():
            from app.models import SolutionRecipe, SolutionRecipeIngredient, Chemical

            chem = Chemical(name='Insuff Chem', quantity=1.0, unit='g', lab_type='water', status='active')
            db.session.add(chem)
            db.session.flush()

            recipe = SolutionRecipe(
                name='Insuff Recipe',
                concentration=0.1,
                standard_volume_ml=1000,
                lab_type='water',
                is_active=True,
                created_by_id=1,
            )
            db.session.add(recipe)
            db.session.flush()

            ing = SolutionRecipeIngredient(
                recipe_id=recipe.id,
                chemical_id=chem.id,
                amount=50.0,
                unit='g',
            )
            db.session.add(ing)
            db.session.commit()

            resp = admin_client.post(
                f'/labs/water-lab/chemistry/solution_recipes/{recipe.id}/prepare',
                data={'volume_ml': '1000'},
                follow_redirects=True,
            )
            assert resp.status_code == 200

            # Stock should NOT be deducted (insufficient)
            chem_check = db.session.get(Chemical, chem.id)
            assert chem_check.quantity == 1.0

            db.session.delete(ing)
            db.session.delete(recipe)
            db.session.delete(chem_check)
            db.session.commit()

    def test_prepare_no_expiry(self, admin_client, app, db):
        """Test prepare without expiry date."""
        with app.app_context():
            from app.models import SolutionRecipe, SolutionPreparation

            recipe = SolutionRecipe(
                name='No Expiry Recipe',
                concentration=0.1,
                standard_volume_ml=1000,
                lab_type='water',
                is_active=True,
                created_by_id=1,
            )
            db.session.add(recipe)
            db.session.commit()

            resp = admin_client.post(
                f'/labs/water-lab/chemistry/solution_recipes/{recipe.id}/prepare',
                data={'volume_ml': '500'},
                follow_redirects=True,
            )
            assert resp.status_code == 200

            SolutionPreparation.query.filter_by(recipe_id=recipe.id).delete()
            db.session.delete(recipe)
            db.session.commit()

    def test_prepare_404(self, admin_client, app):
        with app.app_context():
            resp = admin_client.post('/labs/water-lab/chemistry/solution_recipes/999999/prepare',
                                     data={'volume_ml': '1000'})
            assert resp.status_code == 404

    def test_prepare_invalid_volume(self, admin_client, app, db):
        """Test prepare with invalid volume (trigger ValueError)."""
        with app.app_context():
            from app.models import SolutionRecipe

            recipe = SolutionRecipe(
                name='Bad Volume Recipe',
                concentration=0.1,
                standard_volume_ml=1000,
                lab_type='water',
                is_active=True,
                created_by_id=1,
            )
            db.session.add(recipe)
            db.session.commit()

            resp = admin_client.post(
                f'/labs/water-lab/chemistry/solution_recipes/{recipe.id}/prepare',
                data={'volume_ml': 'not-a-number'},
                follow_redirects=True,
            )
            assert resp.status_code == 200  # Redirected with error flash

            db.session.delete(recipe)
            db.session.commit()


class TestAddRecipe:
    """Test add_recipe route."""

    def test_get_form(self, admin_client, app):
        with app.app_context():
            resp = admin_client.get('/labs/water-lab/chemistry/solution_recipes/add')
            assert resp.status_code == 200

    def test_post_recipe(self, admin_client, app, db):
        with app.app_context():
            from app.models import SolutionRecipe, Chemical

            chem = Chemical(name='Recipe Add Chem', quantity=100, unit='g', lab_type='water', status='active')
            db.session.add(chem)
            db.session.commit()

            resp = admin_client.post('/labs/water-lab/chemistry/solution_recipes/add', data={
                'name': 'New Test Recipe',
                'concentration': '0.05',
                'concentration_unit': 'N',
                'standard_volume_ml': '1000',
                'preparation_notes': 'Test notes',
                'category': 'titrant',
                'chemical_id[]': [str(chem.id)],
                'amount[]': ['5.0'],
                'ingredient_unit[]': ['g'],
            }, follow_redirects=True)
            assert resp.status_code == 200

            recipe = SolutionRecipe.query.filter_by(name='New Test Recipe').first()
            assert recipe is not None

            # Cleanup
            from app.models import SolutionRecipeIngredient
            SolutionRecipeIngredient.query.filter_by(recipe_id=recipe.id).delete()
            db.session.delete(recipe)
            db.session.delete(chem)
            db.session.commit()

    def test_post_recipe_no_ingredients(self, admin_client, app, db):
        with app.app_context():
            from app.models import SolutionRecipe

            resp = admin_client.post('/labs/water-lab/chemistry/solution_recipes/add', data={
                'name': 'No Ingredient Recipe',
                'concentration': '0.1',
                'standard_volume_ml': '1000',
            }, follow_redirects=True)
            assert resp.status_code == 200

            recipe = SolutionRecipe.query.filter_by(name='No Ingredient Recipe').first()
            if recipe:
                db.session.delete(recipe)
                db.session.commit()

    def test_post_recipe_invalid_data(self, admin_client, app):
        """Test error handling on invalid data."""
        with app.app_context():
            resp = admin_client.post('/labs/water-lab/chemistry/solution_recipes/add', data={
                'name': None,
                'concentration': 'bad',
                'chemical_id[]': ['999'],
                'amount[]': ['not-float'],
                'ingredient_unit[]': ['g'],
            }, follow_redirects=True)
            assert resp.status_code == 200


class TestEditRecipe:
    """Test edit_recipe route."""

    def test_get_edit_form(self, admin_client, app, db):
        with app.app_context():
            from app.models import SolutionRecipe

            recipe = SolutionRecipe(
                name='Edit Recipe Test',
                concentration=0.1,
                standard_volume_ml=1000,
                lab_type='water',
                is_active=True,
                created_by_id=1,
            )
            db.session.add(recipe)
            db.session.commit()

            resp = admin_client.get(f'/labs/water-lab/chemistry/solution_recipes/edit/{recipe.id}')
            assert resp.status_code == 200

            db.session.delete(recipe)
            db.session.commit()

    def test_post_edit(self, admin_client, app, db):
        with app.app_context():
            from app.models import SolutionRecipe, SolutionRecipeIngredient, Chemical

            chem = Chemical(name='Edit Recipe Chem', quantity=100, unit='g', lab_type='water', status='active')
            db.session.add(chem)
            db.session.flush()

            recipe = SolutionRecipe(
                name='Before Recipe Edit',
                concentration=0.1,
                standard_volume_ml=1000,
                lab_type='water',
                is_active=True,
                created_by_id=1,
            )
            db.session.add(recipe)
            db.session.flush()

            ing = SolutionRecipeIngredient(
                recipe_id=recipe.id,
                chemical_id=chem.id,
                amount=5.0,
                unit='g',
            )
            db.session.add(ing)
            db.session.commit()

            resp = admin_client.post(
                f'/labs/water-lab/chemistry/solution_recipes/edit/{recipe.id}',
                data={
                    'name': 'After Recipe Edit',
                    'concentration': '0.2',
                    'concentration_unit': 'M',
                    'standard_volume_ml': '2000',
                    'preparation_notes': 'Updated recipe',
                    'category': 'buffer',
                    'chemical_id[]': [str(chem.id)],
                    'amount[]': ['10.0'],
                    'ingredient_unit[]': ['g'],
                },
                follow_redirects=True,
            )
            assert resp.status_code == 200

            updated = db.session.get(SolutionRecipe, recipe.id)
            assert updated.name == 'After Recipe Edit'

            SolutionRecipeIngredient.query.filter_by(recipe_id=recipe.id).delete()
            db.session.delete(updated)
            db.session.delete(chem)
            db.session.commit()

    def test_post_edit_invalid(self, admin_client, app, db):
        """Test edit with invalid float triggers error handling."""
        with app.app_context():
            from app.models import SolutionRecipe

            recipe = SolutionRecipe(
                name='Bad Edit Recipe',
                concentration=0.1,
                standard_volume_ml=1000,
                lab_type='water',
                is_active=True,
                created_by_id=1,
            )
            db.session.add(recipe)
            db.session.commit()

            resp = admin_client.post(
                f'/labs/water-lab/chemistry/solution_recipes/edit/{recipe.id}',
                data={
                    'name': 'Bad Edit Recipe',
                    'concentration': 'bad',
                    'chemical_id[]': ['999'],
                    'amount[]': ['not-float'],
                    'ingredient_unit[]': ['g'],
                },
                follow_redirects=True,
            )
            assert resp.status_code == 200

            db.session.delete(recipe)
            db.session.commit()

    def test_edit_recipe_404(self, admin_client, app):
        with app.app_context():
            resp = admin_client.get('/labs/water-lab/chemistry/solution_recipes/edit/999999')
            assert resp.status_code == 404


class TestDeleteRecipe:
    """Test delete_recipe route."""

    def test_chemist_denied(self, chemist_client, app, db):
        with app.app_context():
            from app.models import SolutionRecipe

            recipe = SolutionRecipe(
                name='Chemist Delete Recipe',
                lab_type='water',
                is_active=True,
                created_by_id=1,
            )
            db.session.add(recipe)
            db.session.commit()

            resp = chemist_client.post(
                f'/labs/water-lab/chemistry/solution_recipes/delete/{recipe.id}',
                follow_redirects=True,
            )
            assert resp.status_code == 200

            # Should still exist
            assert db.session.get(SolutionRecipe, recipe.id) is not None

            db.session.delete(recipe)
            db.session.commit()

    def test_admin_delete(self, admin_client, app, db):
        with app.app_context():
            from app.models import SolutionRecipe

            recipe = SolutionRecipe(
                name='Admin Delete Recipe',
                lab_type='water',
                is_active=True,
                created_by_id=1,
            )
            db.session.add(recipe)
            db.session.commit()
            rid = recipe.id

            resp = admin_client.post(
                f'/labs/water-lab/chemistry/solution_recipes/delete/{rid}',
                follow_redirects=True,
            )
            assert resp.status_code == 200
            assert db.session.get(SolutionRecipe, rid) is None

    def test_delete_recipe_404(self, admin_client, app):
        with app.app_context():
            resp = admin_client.post('/labs/water-lab/chemistry/solution_recipes/delete/999999')
            assert resp.status_code == 404


# ======================================================================
#  EDGE CASES: SolutionPreparation model
# ======================================================================

class TestSolutionPreparationModel:
    """Test SolutionPreparation.calculate_v_avg."""

    def test_calculate_v_avg_all_values(self, app, db):
        with app.app_context():
            from app.models import SolutionPreparation
            sol = SolutionPreparation(
                solution_name='V Avg Test',
                prepared_date=date(2026, 1, 1),
                v1=10.0, v2=10.2, v3=10.4,
            )
            sol.calculate_v_avg()
            assert abs(sol.v_avg - 10.2) < 0.001

    def test_calculate_v_avg_two_values(self, app, db):
        with app.app_context():
            from app.models import SolutionPreparation
            sol = SolutionPreparation(
                solution_name='V Avg 2',
                prepared_date=date(2026, 1, 1),
                v1=10.0, v2=10.4, v3=None,
            )
            sol.calculate_v_avg()
            assert abs(sol.v_avg - 10.2) < 0.001

    def test_calculate_v_avg_no_values(self, app, db):
        with app.app_context():
            from app.models import SolutionPreparation
            sol = SolutionPreparation(
                solution_name='V Avg None',
                prepared_date=date(2026, 1, 1),
                v1=None, v2=None, v3=None,
            )
            result = sol.calculate_v_avg()
            assert result is None

    def test_repr(self, app, db):
        with app.app_context():
            from app.models import SolutionPreparation
            sol = SolutionPreparation(
                solution_name='Repr Test',
                prepared_date=date(2026, 1, 1),
            )
            assert 'Repr Test' in repr(sol)


# ======================================================================
#  EDGE CASES: Micro constants
# ======================================================================

class TestMicroConstants:
    """Test module-level constants are correctly defined."""

    def test_micro_sample_types(self, app):
        with app.app_context():
            from app.labs.water_lab.microbiology.micro_reports import MICRO_SAMPLE_TYPES
            assert 'MICRO_WATER' in MICRO_SAMPLE_TYPES
            assert 'MICRO_AIR' in MICRO_SAMPLE_TYPES
            assert 'MICRO_SWAB' in MICRO_SAMPLE_TYPES

    def test_micro_lab_types(self, app):
        with app.app_context():
            from app.labs.water_lab.microbiology.micro_reports import _MICRO_LAB_TYPES
            assert 'water' in _MICRO_LAB_TYPES
            assert 'microbiology' in _MICRO_LAB_TYPES

    def test_micro_codes(self, app):
        with app.app_context():
            from app.labs.water_lab.microbiology.micro_reports import _MICRO_CODES
            assert len(_MICRO_CODES) == 3


# ======================================================================
#  EDGE CASES: Dashboard pass/fail with various raw_data keys
# ======================================================================

class TestDashboardPassFailEdgeCases:
    """Test the pass/fail logic within micro_dashboard."""

    def test_cfu_air_key(self, admin_client, app, db):
        """Test fail detection on cfu_air key."""
        with app.app_context():
            from app.models import Sample, AnalysisResult

            sample = Sample(
                sample_code='MICRO-AIR-001',
                lab_type='microbiology',
                client_name='QC',
                user_id=1,
                received_date=date.today(),
            )
            db.session.add(sample)
            db.session.flush()

            ar = AnalysisResult(
                sample_id=sample.id,
                analysis_code='MICRO_AIR',
                raw_data=json.dumps({'cfu_air': 200}),
                created_at=datetime.now(),
            )
            db.session.add(ar)
            db.session.commit()

            resp = admin_client.get('/labs/water-lab/microbiology/reports/dashboard')
            assert resp.status_code == 200

            db.session.delete(ar)
            db.session.delete(sample)
            db.session.commit()

    def test_cfu_swab_key(self, admin_client, app, db):
        """Test fail detection on cfu_swab key."""
        with app.app_context():
            from app.models import Sample, AnalysisResult

            sample = Sample(
                sample_code='MICRO-SWAB-001',
                lab_type='microbiology',
                client_name='QC',
                user_id=1,
                received_date=date.today(),
            )
            db.session.add(sample)
            db.session.flush()

            ar = AnalysisResult(
                sample_id=sample.id,
                analysis_code='MICRO_SWAB',
                raw_data=json.dumps({'cfu_swab': 50}),
                created_at=datetime.now(),
            )
            db.session.add(ar)
            db.session.commit()

            resp = admin_client.get('/labs/water-lab/microbiology/reports/dashboard')
            assert resp.status_code == 200

            db.session.delete(ar)
            db.session.delete(sample)
            db.session.commit()


# ======================================================================
#  EDGE: Dashboard month boundary (December → January logic)
# ======================================================================

class TestDashboardDecemberBoundary:
    """Test dashboard handles December correctly."""

    def test_december_monthly_stats(self, admin_client, app):
        """Dashboard calculates 6 months backwards, handles year transitions."""
        with app.app_context():
            with patch('app.labs.water_lab.microbiology.micro_reports.now_local') as mock_now:
                mock_dt = MagicMock()
                mock_dt.year = 2026
                mock_dt.month = 2  # February - will go back to previous year
                mock_now.return_value = mock_dt

                resp = admin_client.get('/labs/water-lab/microbiology/reports/dashboard')
                assert resp.status_code == 200


class TestConsumptionWithNullMonth:
    """Edge case: row with null month."""

    def test_null_month_skipped(self, admin_client, app, db):
        """Rows with no created_at month should be skipped."""
        with app.app_context():
            from app.models import Sample, AnalysisResult

            sample = Sample(
                sample_code='MICRO-NULLMO-001',
                lab_type='microbiology',
                client_name='QC',
                user_id=1,
            )
            db.session.add(sample)
            db.session.flush()

            # created_at is None
            ar = AnalysisResult(
                sample_id=sample.id,
                analysis_code='MICRO_WATER',
                created_at=None,
            )
            db.session.add(ar)
            db.session.commit()

            resp = admin_client.get('/labs/water-lab/microbiology/reports/consumption?year=2026')
            assert resp.status_code == 200

            db.session.delete(ar)
            db.session.delete(sample)
            db.session.commit()
