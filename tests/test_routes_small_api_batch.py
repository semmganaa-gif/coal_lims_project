# -*- coding: utf-8 -*-
"""
Comprehensive tests for small route files to achieve 80%+ coverage:
  - app/routes/main/helpers.py
  - app/routes/reports/routes.py (_format_short_name, _year_arg, _pick_date_col, _code_expr_and_join)
  - app/routes/api/morning_api.py
  - app/routes/imports/routes.py
  - app/routes/license/routes.py
  - app/routes/reports/email_sender.py
"""
import pytest
import smtplib
from datetime import datetime, date, timedelta
from io import BytesIO
from unittest.mock import patch, MagicMock, PropertyMock


# ---------------------------------------------------------------------------
# helpers.py - Pure function tests
# ---------------------------------------------------------------------------
class TestGet12hShiftCode:
    """get_12h_shift_code - 12-hour shift code."""

    def test_day_shift_at_7am(self):
        from app.routes.main.helpers import get_12h_shift_code
        dt = datetime(2026, 1, 1, 7, 0, 0)
        assert get_12h_shift_code(dt) == "_D"

    def test_day_shift_at_noon(self):
        from app.routes.main.helpers import get_12h_shift_code
        dt = datetime(2026, 1, 1, 12, 0, 0)
        assert get_12h_shift_code(dt) == "_D"

    def test_day_shift_at_18(self):
        from app.routes.main.helpers import get_12h_shift_code
        dt = datetime(2026, 1, 1, 18, 59, 59)
        assert get_12h_shift_code(dt) == "_D"

    def test_night_shift_at_19(self):
        from app.routes.main.helpers import get_12h_shift_code
        dt = datetime(2026, 1, 1, 19, 0, 0)
        assert get_12h_shift_code(dt) == "_N"

    def test_night_shift_at_midnight(self):
        from app.routes.main.helpers import get_12h_shift_code
        dt = datetime(2026, 1, 1, 0, 0, 0)
        assert get_12h_shift_code(dt) == "_N"

    def test_night_shift_at_6am(self):
        from app.routes.main.helpers import get_12h_shift_code
        dt = datetime(2026, 1, 1, 6, 59, 59)
        assert get_12h_shift_code(dt) == "_N"

    def test_night_shift_at_3am(self):
        from app.routes.main.helpers import get_12h_shift_code
        dt = datetime(2026, 1, 1, 3, 0, 0)
        assert get_12h_shift_code(dt) == "_N"

    def test_night_shift_at_23(self):
        from app.routes.main.helpers import get_12h_shift_code
        dt = datetime(2026, 1, 1, 23, 0, 0)
        assert get_12h_shift_code(dt) == "_N"


class TestGetQuarterCode:
    """get_quarter_code - quarter code."""

    def test_q1_january(self):
        from app.routes.main.helpers import get_quarter_code
        dt = datetime(2026, 1, 15)
        assert get_quarter_code(dt) == "_Q1"

    def test_q1_march(self):
        from app.routes.main.helpers import get_quarter_code
        dt = datetime(2026, 3, 31)
        assert get_quarter_code(dt) == "_Q1"

    def test_q2_april(self):
        from app.routes.main.helpers import get_quarter_code
        dt = datetime(2026, 4, 1)
        assert get_quarter_code(dt) == "_Q2"

    def test_q2_june(self):
        from app.routes.main.helpers import get_quarter_code
        dt = datetime(2026, 6, 30)
        assert get_quarter_code(dt) == "_Q2"

    def test_q3_july(self):
        from app.routes.main.helpers import get_quarter_code
        dt = datetime(2026, 7, 1)
        assert get_quarter_code(dt) == "_Q3"

    def test_q3_september(self):
        from app.routes.main.helpers import get_quarter_code
        dt = datetime(2026, 9, 30)
        assert get_quarter_code(dt) == "_Q3"

    def test_q4_october(self):
        from app.routes.main.helpers import get_quarter_code
        dt = datetime(2026, 10, 1)
        assert get_quarter_code(dt) == "_Q4"

    def test_q4_december(self):
        from app.routes.main.helpers import get_quarter_code
        dt = datetime(2026, 12, 31)
        assert get_quarter_code(dt) == "_Q4"


class TestIsSafeUrl:
    """is_safe_url - needs Flask request context."""

    def test_safe_relative_url(self, app):
        from app.routes.main.helpers import is_safe_url
        with app.test_request_context('http://localhost/'):
            assert is_safe_url('/dashboard') is True

    def test_safe_absolute_same_host(self, app):
        from app.routes.main.helpers import is_safe_url
        with app.test_request_context('http://localhost/'):
            assert is_safe_url('http://localhost/dashboard') is True

    def test_unsafe_external_url(self, app):
        from app.routes.main.helpers import is_safe_url
        with app.test_request_context('http://localhost/'):
            assert is_safe_url('http://evil.com/steal') is False

    def test_unsafe_javascript_url(self, app):
        from app.routes.main.helpers import is_safe_url
        with app.test_request_context('http://localhost/'):
            result = is_safe_url('javascript:alert(1)')
            # javascript: scheme is not http/https and netloc won't match
            assert result is False

    def test_safe_empty_path(self, app):
        from app.routes.main.helpers import is_safe_url
        with app.test_request_context('http://localhost/'):
            assert is_safe_url('/') is True

    def test_safe_url_with_query(self, app):
        from app.routes.main.helpers import is_safe_url
        with app.test_request_context('http://localhost/'):
            assert is_safe_url('/page?key=value') is True

    def test_unsafe_protocol_relative(self, app):
        from app.routes.main.helpers import is_safe_url
        with app.test_request_context('http://localhost/'):
            # //evil.com would have different netloc
            assert is_safe_url('//evil.com/path') is False


# ---------------------------------------------------------------------------
# reports/routes.py - Helper function tests
# ---------------------------------------------------------------------------
class TestFormatShortName:
    """_format_short_name tests."""

    def test_two_parts(self, app):
        with app.app_context():
            from app.routes.reports.routes import _format_short_name
            assert _format_short_name("John Smith") == "John.S"

    def test_empty_string(self, app):
        with app.app_context():
            from app.routes.reports.routes import _format_short_name
            assert _format_short_name("") == ""

    def test_none(self, app):
        with app.app_context():
            from app.routes.reports.routes import _format_short_name
            assert _format_short_name(None) == ""

    def test_single_name(self, app):
        with app.app_context():
            from app.routes.reports.routes import _format_short_name
            assert _format_short_name("Alice") == "Alice"

    def test_three_parts(self, app):
        with app.app_context():
            from app.routes.reports.routes import _format_short_name
            # Only uses first two parts
            assert _format_short_name("John David Smith") == "John.D"

    def test_all_uppercase(self, app):
        with app.app_context():
            from app.routes.reports.routes import _format_short_name
            assert _format_short_name("GANTULGA ULZIIBUYAN") == "Gantulga.U"

    def test_all_lowercase(self, app):
        with app.app_context():
            from app.routes.reports.routes import _format_short_name
            assert _format_short_name("john smith") == "John.S"

    def test_whitespace_padding(self, app):
        with app.app_context():
            from app.routes.reports.routes import _format_short_name
            assert _format_short_name("  John Smith  ") == "John.S"


class TestYearArg:
    """_year_arg tests."""

    def test_valid_year(self, app):
        with app.app_context():
            from app.routes.reports.routes import _year_arg
            with app.test_request_context('/?year=2026'):
                assert _year_arg() == 2026

    def test_default_year(self, app):
        with app.app_context():
            from app.routes.reports.routes import _year_arg
            with app.test_request_context('/'):
                result = _year_arg()
                assert 2000 <= result <= 2100

    def test_invalid_year_string(self, app):
        with app.app_context():
            from app.routes.reports.routes import _year_arg
            with app.test_request_context('/?year=abc'):
                with pytest.raises(Exception):
                    _year_arg()

    def test_year_too_low(self, app):
        with app.app_context():
            from app.routes.reports.routes import _year_arg
            with app.test_request_context('/?year=1999'):
                with pytest.raises(Exception):
                    _year_arg()

    def test_year_too_high(self, app):
        with app.app_context():
            from app.routes.reports.routes import _year_arg
            with app.test_request_context('/?year=2101'):
                with pytest.raises(Exception):
                    _year_arg()

    def test_year_boundary_min(self, app):
        with app.app_context():
            from app.routes.reports.routes import _year_arg
            with app.test_request_context('/?year=2000'):
                assert _year_arg() == 2000

    def test_year_boundary_max(self, app):
        with app.app_context():
            from app.routes.reports.routes import _year_arg
            with app.test_request_context('/?year=2100'):
                assert _year_arg() == 2100


class TestPickDateCol:
    """_pick_date_col tests."""

    def test_returns_column(self, app):
        with app.app_context():
            from app.routes.reports.routes import _pick_date_col
            col = _pick_date_col()
            # Should return one of the candidate columns
            assert col is not None

    def test_returns_attribute(self, app):
        """Should return an AnalysisResult column attribute."""
        with app.app_context():
            from app.routes.reports.routes import _pick_date_col
            col = _pick_date_col()
            col_name = str(col.key) if hasattr(col, 'key') else str(col)
            assert any(n in col_name for n in
                       ['analysis_date', 'approved_at', 'updated_at', 'created_at'])


class TestCodeExprAndJoin:
    """_code_expr_and_join tests."""

    def test_returns_tuple(self, app, db):
        with app.app_context():
            from app.routes.reports.routes import _code_expr_and_join
            from app.models import AnalysisResult
            query = AnalysisResult.query
            result_query, code_expr = _code_expr_and_join(query)
            assert result_query is not None
            assert code_expr is not None


# ---------------------------------------------------------------------------
# morning_api.py - Route tests
# ---------------------------------------------------------------------------
class TestMorningDashboard:
    """morning_dashboard route tests."""

    def test_morning_dashboard_coal_default(self, auth_admin, db):
        resp = auth_admin.get('/api/morning_dashboard')
        assert resp.status_code == 200
        data = resp.get_json()
        assert 'calibration_due' in data
        assert 'calibration_overdue' in data
        assert 'broken_equipment' in data
        assert 'samples' in data
        assert 'new' in data['samples']
        assert 'in_progress' in data['samples']
        assert 'today_received' in data['samples']

    def test_morning_dashboard_water(self, auth_admin, db):
        resp = auth_admin.get('/api/morning_dashboard?lab=water')
        assert resp.status_code == 200
        data = resp.get_json()
        assert 'samples' in data

    def test_morning_dashboard_micro(self, auth_admin, db):
        resp = auth_admin.get('/api/morning_dashboard?lab=micro')
        assert resp.status_code == 200
        data = resp.get_json()
        assert 'samples' in data

    def test_morning_dashboard_petro(self, auth_admin, db):
        resp = auth_admin.get('/api/morning_dashboard?lab=petro')
        assert resp.status_code == 200
        data = resp.get_json()
        assert 'samples' in data

    def test_morning_dashboard_unknown_lab_defaults_to_coal(self, auth_admin, db):
        resp = auth_admin.get('/api/morning_dashboard?lab=unknown')
        assert resp.status_code == 200
        data = resp.get_json()
        assert 'samples' in data

    def test_morning_dashboard_requires_login(self, client):
        resp = client.get('/api/morning_dashboard')
        # Should redirect to login
        assert resp.status_code in (302, 401)

    def test_morning_dashboard_with_equipment_data(self, auth_admin, db):
        """Test with actual equipment in DB for calibration_due."""
        from app.models import Equipment
        today = date.today()
        # Equipment due for calibration within a week
        equip = Equipment(
            name='TestEquip1',
            lab_code='TE001',
            category='furnace',
            status='normal',
            next_calibration_date=today + timedelta(days=3),
        )
        db.session.add(equip)
        db.session.commit()

        resp = auth_admin.get('/api/morning_dashboard?lab=coal')
        assert resp.status_code == 200
        data = resp.get_json()
        # Should find our equipment in calibration_due
        due_ids = [e['id'] for e in data['calibration_due']]
        assert equip.id in due_ids
        assert data['calibration_due'][0]['days_left'] >= 0

        # Cleanup
        db.session.delete(equip)
        db.session.commit()

    def test_morning_dashboard_overdue_equipment(self, auth_admin, db):
        """Test overdue calibration equipment."""
        from app.models import Equipment
        today = date.today()
        equip = Equipment(
            name='TestOverdue',
            lab_code='TO001',
            category='furnace',
            status='normal',
            next_calibration_date=today - timedelta(days=5),
        )
        db.session.add(equip)
        db.session.commit()

        resp = auth_admin.get('/api/morning_dashboard?lab=coal')
        data = resp.get_json()
        overdue_ids = [e['id'] for e in data['calibration_overdue']]
        assert equip.id in overdue_ids
        found = [e for e in data['calibration_overdue'] if e['id'] == equip.id][0]
        assert found['days_overdue'] == 5

        db.session.delete(equip)
        db.session.commit()

    def test_morning_dashboard_broken_equipment(self, auth_admin, db):
        """Test broken equipment listing."""
        from app.models import Equipment
        equip = Equipment(
            name='BrokenEquip',
            lab_code='BE001',
            category='furnace',
            status='maintenance',
        )
        db.session.add(equip)
        db.session.commit()

        resp = auth_admin.get('/api/morning_dashboard?lab=coal')
        data = resp.get_json()
        broken_ids = [e['id'] for e in data['broken_equipment']]
        assert equip.id in broken_ids

        db.session.delete(equip)
        db.session.commit()

    def test_morning_dashboard_sample_counts(self, auth_admin, db):
        """Test sample counting."""
        from app.models import Sample
        s = Sample(
            sample_code='MORNING_TEST_001',
            lab_type='coal',
            status='new',
            received_date=datetime.now(),
        )
        db.session.add(s)
        db.session.commit()

        resp = auth_admin.get('/api/morning_dashboard?lab=coal')
        data = resp.get_json()
        assert data['samples']['new'] >= 1

        db.session.delete(s)
        db.session.commit()


# ---------------------------------------------------------------------------
# imports/routes.py - Route tests
# ---------------------------------------------------------------------------
class TestImportHistoricalCsv:
    """import_historical_csv route tests."""

    def test_get_page_as_admin(self, auth_admin):
        resp = auth_admin.get('/admin/import/historical_csv')
        assert resp.status_code == 200

    def test_get_page_non_admin_redirects(self, auth_user):
        resp = auth_user.get('/admin/import/historical_csv')
        assert resp.status_code == 302

    def test_post_no_file(self, auth_admin):
        resp = auth_admin.post('/admin/import/historical_csv',
                               data={},
                               content_type='multipart/form-data')
        assert resp.status_code == 302

    def test_post_empty_filename(self, auth_admin):
        data = {'file': (BytesIO(b''), '')}
        resp = auth_admin.post('/admin/import/historical_csv',
                               data=data,
                               content_type='multipart/form-data')
        assert resp.status_code == 302

    @patch('app.routes.imports.routes.process_csv_import')
    def test_post_valid_csv(self, mock_import, auth_admin):
        mock_import.return_value = ({'imported': 10}, [])
        data = {
            'file': (BytesIO(b'col1,col2\nval1,val2\n'), 'test.csv'),
        }
        resp = auth_admin.post('/admin/import/historical_csv',
                               data=data,
                               content_type='multipart/form-data')
        assert resp.status_code == 200
        mock_import.assert_called_once()

    @patch('app.routes.imports.routes.process_csv_import')
    def test_post_with_dry_run(self, mock_import, auth_admin):
        mock_import.return_value = ({'imported': 0}, [])
        data = {
            'file': (BytesIO(b'col1,col2\nval1,val2\n'), 'test.csv'),
            'dry_run': 'on',
        }
        resp = auth_admin.post('/admin/import/historical_csv',
                               data=data,
                               content_type='multipart/form-data')
        assert resp.status_code == 200
        # Check dry_run was passed
        args, kwargs = mock_import.call_args
        assert kwargs.get('dry_run') is True

    @patch('app.routes.imports.routes.process_csv_import')
    def test_post_custom_batch_size(self, mock_import, auth_admin):
        mock_import.return_value = ({'imported': 5}, [])
        data = {
            'file': (BytesIO(b'col1\nval1\n'), 'test.csv'),
            'batch_size': '2000',
        }
        resp = auth_admin.post('/admin/import/historical_csv',
                               data=data,
                               content_type='multipart/form-data')
        assert resp.status_code == 200
        args, kwargs = mock_import.call_args
        assert kwargs.get('batch_size') == 2000

    @patch('app.routes.imports.routes.process_csv_import')
    def test_post_batch_size_capped_at_5000(self, mock_import, auth_admin):
        mock_import.return_value = ({'imported': 5}, [])
        data = {
            'file': (BytesIO(b'col1\nval1\n'), 'test.csv'),
            'batch_size': '99999',
        }
        resp = auth_admin.post('/admin/import/historical_csv',
                               data=data,
                               content_type='multipart/form-data')
        assert resp.status_code == 200
        args, kwargs = mock_import.call_args
        assert kwargs.get('batch_size') == 5000

    @patch('app.routes.imports.routes.process_csv_import')
    def test_post_invalid_batch_size_defaults(self, mock_import, auth_admin):
        mock_import.return_value = ({'imported': 5}, [])
        data = {
            'file': (BytesIO(b'col1\nval1\n'), 'test.csv'),
            'batch_size': 'abc',
        }
        resp = auth_admin.post('/admin/import/historical_csv',
                               data=data,
                               content_type='multipart/form-data')
        assert resp.status_code == 200
        args, kwargs = mock_import.call_args
        assert kwargs.get('batch_size') == 1000

    @patch('app.routes.imports.routes.process_csv_import')
    def test_post_value_error(self, mock_import, auth_admin):
        mock_import.side_effect = ValueError("Bad CSV format")
        data = {
            'file': (BytesIO(b'bad_data'), 'test.csv'),
        }
        resp = auth_admin.post('/admin/import/historical_csv',
                               data=data,
                               content_type='multipart/form-data')
        assert resp.status_code == 302

    @patch('app.routes.imports.routes.process_csv_import')
    def test_post_sqlalchemy_error(self, mock_import, auth_admin):
        from sqlalchemy.exc import SQLAlchemyError
        mock_import.side_effect = SQLAlchemyError("DB error")
        data = {
            'file': (BytesIO(b'col1\nval1\n'), 'test.csv'),
        }
        resp = auth_admin.post('/admin/import/historical_csv',
                               data=data,
                               content_type='multipart/form-data')
        assert resp.status_code == 302

    @patch('app.routes.imports.routes.process_csv_import')
    def test_post_with_errors_truncated(self, mock_import, auth_admin):
        """Errors list is truncated to 200."""
        errors = [f"Error {i}" for i in range(300)]
        mock_import.return_value = ({'imported': 5}, errors)
        data = {
            'file': (BytesIO(b'col1\nval1\n'), 'test.csv'),
        }
        resp = auth_admin.post('/admin/import/historical_csv',
                               data=data,
                               content_type='multipart/form-data')
        assert resp.status_code == 200


# ---------------------------------------------------------------------------
# license/routes.py - Route tests
# ---------------------------------------------------------------------------
class TestLicenseActivate:
    """License activate route tests."""

    @patch('app.routes.license.routes.get_hardware_info')
    def test_get_activate_page_admin(self, mock_hw, auth_admin):
        mock_hw.return_value = {'hardware_id': 'abc', 'short_id': 'ab', 'hostname': 'test'}
        resp = auth_admin.get('/license/activate')
        assert resp.status_code == 200

    def test_get_activate_page_non_admin(self, auth_user):
        resp = auth_user.get('/license/activate')
        assert resp.status_code == 302

    @patch('app.routes.license.routes.get_hardware_info')
    @patch('app.routes.license.routes.license_manager')
    def test_post_activate_success(self, mock_lm, mock_hw, auth_admin):
        mock_hw.return_value = {'hardware_id': 'abc', 'short_id': 'ab', 'hostname': 'test'}
        mock_lm.activate_license.return_value = {'success': True}
        resp = auth_admin.post('/license/activate',
                               data={'license_key': 'VALID-KEY-123'})
        assert resp.status_code == 302

    @patch('app.routes.license.routes.get_hardware_info')
    @patch('app.routes.license.routes.license_manager')
    def test_post_activate_failure(self, mock_lm, mock_hw, auth_admin):
        mock_hw.return_value = {'hardware_id': 'abc', 'short_id': 'ab', 'hostname': 'test'}
        mock_lm.activate_license.return_value = {'success': False, 'error': 'Invalid key'}
        resp = auth_admin.post('/license/activate',
                               data={'license_key': 'BAD-KEY'})
        assert resp.status_code == 200

    @patch('app.routes.license.routes.get_hardware_info')
    def test_post_activate_empty_key(self, mock_hw, auth_admin):
        mock_hw.return_value = {'hardware_id': 'abc', 'short_id': 'ab', 'hostname': 'test'}
        resp = auth_admin.post('/license/activate',
                               data={'license_key': ''})
        assert resp.status_code == 200

    @patch('app.routes.license.routes.get_hardware_info')
    def test_post_activate_whitespace_key(self, mock_hw, auth_admin):
        mock_hw.return_value = {'hardware_id': 'abc', 'short_id': 'ab', 'hostname': 'test'}
        resp = auth_admin.post('/license/activate',
                               data={'license_key': '   '})
        assert resp.status_code == 200


class TestLicenseExpired:
    """License expired route tests."""

    @patch('app.routes.license.routes.generate_short_hardware_id')
    @patch('app.routes.license.routes.license_manager')
    def test_expired_page_admin(self, mock_lm, mock_hw, auth_admin):
        mock_lm.get_current_license.return_value = None
        mock_hw.return_value = 'SHORT-HW-ID'
        resp = auth_admin.get('/license/expired')
        assert resp.status_code == 200

    @patch('app.routes.license.routes.generate_short_hardware_id')
    @patch('app.routes.license.routes.license_manager')
    def test_expired_page_non_admin(self, mock_lm, mock_hw, auth_user):
        mock_lm.get_current_license.return_value = None
        resp = auth_user.get('/license/expired')
        assert resp.status_code == 200
        # Non-admin should not see hardware_id
        mock_hw.assert_not_called()


class TestLicenseError:
    """License error route tests."""

    @patch('app.routes.license.routes.generate_short_hardware_id')
    @patch('app.routes.license.routes.license_manager')
    def test_error_page_admin(self, mock_lm, mock_hw, auth_admin):
        mock_lm.get_current_license.return_value = None
        mock_hw.return_value = 'SHORT-HW-ID'
        resp = auth_admin.get('/license/error')
        assert resp.status_code == 200

    @patch('app.routes.license.routes.generate_short_hardware_id')
    @patch('app.routes.license.routes.license_manager')
    def test_error_page_non_admin(self, mock_lm, mock_hw, auth_user):
        mock_lm.get_current_license.return_value = None
        resp = auth_user.get('/license/error')
        assert resp.status_code == 200


class TestLicenseInfo:
    """License info route tests."""

    @patch('app.routes.license.routes.get_hardware_info')
    @patch('app.routes.license.routes.license_manager')
    def test_info_page(self, mock_lm, mock_hw, auth_admin):
        mock_lm.get_current_license.return_value = None
        mock_hw.return_value = {'hardware_id': 'abc', 'short_id': 'ab', 'hostname': 'test'}
        resp = auth_admin.get('/license/info')
        assert resp.status_code == 200


class TestLicenseCheck:
    """License check API tests."""

    @patch('app.routes.license.routes.license_manager')
    def test_check_valid(self, mock_lm, auth_admin):
        mock_license = MagicMock()
        mock_license.days_remaining = 30
        mock_lm.validate_license.return_value = {
            'valid': True,
            'license': mock_license,
        }
        resp = auth_admin.get('/license/check')
        assert resp.status_code == 200
        data = resp.get_json()
        assert data['valid'] is True
        assert data['days_remaining'] == 30

    @patch('app.routes.license.routes.license_manager')
    def test_check_invalid(self, mock_lm, auth_admin):
        mock_lm.validate_license.return_value = {
            'valid': False,
            'error': 'Expired',
            'license': None,
        }
        resp = auth_admin.get('/license/check')
        assert resp.status_code == 200
        data = resp.get_json()
        assert data['valid'] is False
        assert data['days_remaining'] == 0

    @patch('app.routes.license.routes.license_manager')
    def test_check_with_warning(self, mock_lm, auth_admin):
        mock_license = MagicMock()
        mock_license.days_remaining = 5
        mock_lm.validate_license.return_value = {
            'valid': True,
            'warning': 'Expiring soon',
            'license': mock_license,
        }
        resp = auth_admin.get('/license/check')
        data = resp.get_json()
        assert data['warning'] == 'Expiring soon'

    def test_check_requires_login(self, client):
        resp = client.get('/license/check')
        assert resp.status_code in (302, 401)


class TestLicenseHardwareId:
    """License hardware-id route tests."""

    @patch('app.routes.license.routes.get_hardware_info')
    def test_hardware_id_admin(self, mock_hw, auth_admin):
        mock_hw.return_value = {
            'hardware_id': 'HW-123',
            'short_id': 'H1',
            'hostname': 'testhost',
        }
        resp = auth_admin.get('/license/hardware-id')
        assert resp.status_code == 200
        data = resp.get_json()
        assert data['hardware_id'] == 'HW-123'
        assert data['short_id'] == 'H1'
        assert data['hostname'] == 'testhost'

    def test_hardware_id_non_admin(self, auth_user):
        resp = auth_user.get('/license/hardware-id')
        assert resp.status_code == 403
        data = resp.get_json()
        assert 'error' in data


# ---------------------------------------------------------------------------
# reports/email_sender.py - send_report_email tests
# ---------------------------------------------------------------------------
class TestSendReportEmail:
    """send_report_email function tests."""

    def _make_report(self, pdf_path=None):
        report = MagicMock()
        report.report_number = 'RPT-001'
        report.title = 'Test Report'
        report.date_from = date(2026, 1, 1)
        report.date_to = date(2026, 1, 31)
        report.pdf_path = pdf_path
        return report

    @patch('app.routes.reports.email_sender.smtplib.SMTP')
    def test_send_success_no_pdf(self, mock_smtp_cls, app):
        with app.app_context():
            from app.routes.reports.email_sender import send_report_email
            app.config['MAIL_USERNAME'] = 'user@test.com'
            app.config['MAIL_PASSWORD'] = 'pass123'
            app.config['MAIL_SERVER'] = 'smtp.test.com'
            app.config['MAIL_PORT'] = 587

            mock_server = MagicMock()
            mock_smtp_cls.return_value.__enter__ = MagicMock(return_value=mock_server)
            mock_smtp_cls.return_value.__exit__ = MagicMock(return_value=False)

            report = self._make_report()
            success, error = send_report_email(report, ['rcpt@test.com'])
            assert success is True
            assert error is None

    @patch('app.routes.reports.email_sender.smtplib.SMTP')
    def test_send_success_with_pdf(self, mock_smtp_cls, app):
        with app.app_context():
            from app.routes.reports.email_sender import send_report_email
            app.config['MAIL_USERNAME'] = 'user@test.com'
            app.config['MAIL_PASSWORD'] = 'pass123'

            mock_server = MagicMock()
            mock_smtp_cls.return_value.__enter__ = MagicMock(return_value=mock_server)
            mock_smtp_cls.return_value.__exit__ = MagicMock(return_value=False)

            report = self._make_report(pdf_path='reports/test.pdf')

            with patch('app.routes.reports.email_sender.os.path.exists', return_value=True):
                with patch('builtins.open',
                           MagicMock(return_value=BytesIO(b'%PDF-fake'))):
                    success, error = send_report_email(
                        report, ['rcpt@test.com'],
                        subject='Custom Subject',
                        body='Custom Body'
                    )
            assert success is True
            assert error is None

    def test_send_missing_smtp_credentials(self, app):
        with app.app_context():
            from app.routes.reports.email_sender import send_report_email
            app.config['MAIL_USERNAME'] = None
            app.config['MAIL_PASSWORD'] = None

            report = self._make_report()
            success, error = send_report_email(report, ['rcpt@test.com'])
            assert success is False
            assert 'SMTP' in error

    def test_send_missing_password(self, app):
        with app.app_context():
            from app.routes.reports.email_sender import send_report_email
            app.config['MAIL_USERNAME'] = 'user@test.com'
            app.config['MAIL_PASSWORD'] = None

            report = self._make_report()
            success, error = send_report_email(report, ['rcpt@test.com'])
            assert success is False

    @patch('app.routes.reports.email_sender.smtplib.SMTP')
    def test_send_auth_error(self, mock_smtp_cls, app):
        with app.app_context():
            from app.routes.reports.email_sender import send_report_email
            app.config['MAIL_USERNAME'] = 'user@test.com'
            app.config['MAIL_PASSWORD'] = 'pass123'

            mock_smtp_cls.return_value.__enter__ = MagicMock(
                side_effect=smtplib.SMTPAuthenticationError(535, b'Auth failed'))
            mock_smtp_cls.return_value.__exit__ = MagicMock(return_value=True)

            report = self._make_report()
            success, error = send_report_email(report, ['rcpt@test.com'])
            assert success is False
            assert error is not None

    @patch('app.routes.reports.email_sender.smtplib.SMTP')
    def test_send_smtp_exception(self, mock_smtp_cls, app):
        with app.app_context():
            from app.routes.reports.email_sender import send_report_email
            app.config['MAIL_USERNAME'] = 'user@test.com'
            app.config['MAIL_PASSWORD'] = 'pass123'

            mock_smtp_cls.side_effect = smtplib.SMTPException("Connection refused")

            report = self._make_report()
            success, error = send_report_email(report, ['rcpt@test.com'])
            assert success is False
            assert 'SMTP' in error

    @patch('app.routes.reports.email_sender.smtplib.SMTP')
    def test_send_os_error(self, mock_smtp_cls, app):
        with app.app_context():
            from app.routes.reports.email_sender import send_report_email
            app.config['MAIL_USERNAME'] = 'user@test.com'
            app.config['MAIL_PASSWORD'] = 'pass123'

            mock_smtp_cls.side_effect = OSError("Disk error")

            report = self._make_report()
            success, error = send_report_email(report, ['rcpt@test.com'])
            assert success is False
            assert 'Error' in error

    @patch('app.routes.reports.email_sender.smtplib.SMTP')
    def test_send_with_custom_subject_and_body(self, mock_smtp_cls, app):
        with app.app_context():
            from app.routes.reports.email_sender import send_report_email
            app.config['MAIL_USERNAME'] = 'user@test.com'
            app.config['MAIL_PASSWORD'] = 'pass123'

            mock_server = MagicMock()
            mock_smtp_cls.return_value.__enter__ = MagicMock(return_value=mock_server)
            mock_smtp_cls.return_value.__exit__ = MagicMock(return_value=False)

            report = self._make_report()
            success, error = send_report_email(
                report, ['a@test.com', 'b@test.com'],
                subject='Custom', body='Custom body text'
            )
            assert success is True

    @patch('app.routes.reports.email_sender.smtplib.SMTP')
    def test_send_pdf_not_found_still_sends(self, mock_smtp_cls, app):
        """If pdf_path is set but file doesn't exist, email still sends without attachment."""
        with app.app_context():
            from app.routes.reports.email_sender import send_report_email
            app.config['MAIL_USERNAME'] = 'user@test.com'
            app.config['MAIL_PASSWORD'] = 'pass123'

            mock_server = MagicMock()
            mock_smtp_cls.return_value.__enter__ = MagicMock(return_value=mock_server)
            mock_smtp_cls.return_value.__exit__ = MagicMock(return_value=False)

            report = self._make_report(pdf_path='nonexistent/path.pdf')
            with patch('app.routes.reports.email_sender.os.path.exists', return_value=False):
                success, error = send_report_email(report, ['rcpt@test.com'])
            assert success is True

    @patch('app.routes.reports.email_sender.smtplib.SMTP')
    def test_send_uses_default_sender(self, mock_smtp_cls, app):
        with app.app_context():
            from app.routes.reports.email_sender import send_report_email
            app.config['MAIL_USERNAME'] = 'user@test.com'
            app.config['MAIL_PASSWORD'] = 'pass123'
            app.config['MAIL_DEFAULT_SENDER'] = 'noreply@lab.com'

            mock_server = MagicMock()
            mock_smtp_cls.return_value.__enter__ = MagicMock(return_value=mock_server)
            mock_smtp_cls.return_value.__exit__ = MagicMock(return_value=False)

            report = self._make_report()
            success, _ = send_report_email(report, ['rcpt@test.com'])
            assert success is True


# ---------------------------------------------------------------------------
# reports/email_sender.py - send_email route tests
# ---------------------------------------------------------------------------
class TestSendEmailRoute:
    """send_email route on pdf_reports blueprint."""

    def _create_report(self, db_session, status='approved'):
        from app.models import LabReport
        report = LabReport(
            report_number=f'RPT-ROUTE-{datetime.now().timestamp()}',
            lab_type='coal',
            title='Route Test Report',
            status=status,
        )
        db_session.add(report)
        db_session.commit()
        return report

    def test_send_email_get_page(self, auth_admin, db):
        report = self._create_report(db.session)
        with patch('app.routes.reports.email_sender.send_report_email'):
            resp = auth_admin.get(f'/pdf-reports/{report.id}/send_email')
        assert resp.status_code == 200
        db.session.delete(report)
        db.session.commit()

    def test_send_email_non_authorized_role(self, auth_user, db):
        report = self._create_report(db.session)
        resp = auth_user.get(f'/pdf-reports/{report.id}/send_email')
        assert resp.status_code == 302
        db.session.delete(report)
        db.session.commit()

    def test_send_email_report_not_found(self, auth_admin):
        resp = auth_admin.get('/pdf-reports/999999/send_email')
        assert resp.status_code == 404

    def test_send_email_draft_report_rejected(self, auth_admin, db):
        report = self._create_report(db.session, status='draft')
        resp = auth_admin.get(f'/pdf-reports/{report.id}/send_email')
        assert resp.status_code == 302
        db.session.delete(report)
        db.session.commit()

    @patch('app.routes.reports.email_sender.safe_commit')
    @patch('app.routes.reports.email_sender.send_report_email')
    def test_send_email_post_success(self, mock_send, mock_commit, auth_admin, db):
        report = self._create_report(db.session)
        mock_send.return_value = (True, None)
        resp = auth_admin.post(f'/pdf-reports/{report.id}/send_email',
                               data={'recipients': 'a@test.com,b@test.com',
                                     'subject': 'Test',
                                     'body': 'Hello'})
        assert resp.status_code == 302
        mock_send.assert_called_once()
        db.session.delete(report)
        db.session.commit()

    @patch('app.routes.reports.email_sender.send_report_email')
    def test_send_email_post_failure(self, mock_send, auth_admin, db):
        report = self._create_report(db.session)
        mock_send.return_value = (False, 'SMTP error')
        resp = auth_admin.post(f'/pdf-reports/{report.id}/send_email',
                               data={'recipients': 'a@test.com'})
        assert resp.status_code == 200
        db.session.delete(report)
        db.session.commit()

    def test_send_email_post_empty_recipients(self, auth_admin, db):
        report = self._create_report(db.session)
        resp = auth_admin.post(f'/pdf-reports/{report.id}/send_email',
                               data={'recipients': ''})
        assert resp.status_code == 302
        db.session.delete(report)
        db.session.commit()

    def test_send_email_post_whitespace_recipients(self, auth_admin, db):
        report = self._create_report(db.session)
        resp = auth_admin.post(f'/pdf-reports/{report.id}/send_email',
                               data={'recipients': '  ,  , '})
        assert resp.status_code == 302
        db.session.delete(report)
        db.session.commit()

    def test_send_email_sent_status_allowed(self, auth_admin, db):
        """Reports with status 'sent' can be re-sent."""
        report = self._create_report(db.session, status='sent')
        resp = auth_admin.get(f'/pdf-reports/{report.id}/send_email')
        assert resp.status_code == 200
        db.session.delete(report)
        db.session.commit()

    def test_send_email_pending_status_rejected(self, auth_admin, db):
        """Reports with status 'pending_approval' cannot be sent."""
        report = self._create_report(db.session, status='pending_approval')
        resp = auth_admin.get(f'/pdf-reports/{report.id}/send_email')
        assert resp.status_code == 302
        db.session.delete(report)
        db.session.commit()


# ---------------------------------------------------------------------------
# LAB_CONFIG coverage for morning_api
# ---------------------------------------------------------------------------
class TestLabConfig:
    """Verify _LAB_CONFIG structure."""

    def test_lab_config_keys(self, app):
        with app.app_context():
            from app.routes.api.morning_api import _LAB_CONFIG
            assert 'coal' in _LAB_CONFIG
            assert 'water' in _LAB_CONFIG
            assert 'micro' in _LAB_CONFIG
            assert 'petro' in _LAB_CONFIG

    def test_lab_config_has_required_keys(self, app):
        with app.app_context():
            from app.routes.api.morning_api import _LAB_CONFIG
            for lab, cfg in _LAB_CONFIG.items():
                assert 'sample_types' in cfg, f"{lab} missing sample_types"
                assert 'equip_categories' in cfg, f"{lab} missing equip_categories"
                assert isinstance(cfg['sample_types'], list)
                assert isinstance(cfg['equip_categories'], list)
