# -*- coding: utf-8 -*-
"""
Report Routes модулийн coverage тестүүд
"""
import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime, date, timedelta
from collections import defaultdict


class TestYearArg:
    """_year_arg функц тест"""

    def test_import_function(self):
        from app.routes.reports.routes import _year_arg
        assert _year_arg is not None

    def test_default_year(self, app):
        from app.routes.reports.routes import _year_arg
        with app.test_request_context('/test'):
            with patch('app.routes.reports.routes.now_local') as mock_now:
                mock_now.return_value = datetime(2026, 5, 15)
                result = _year_arg()
                assert result == 2026

    def test_valid_year_param(self, app):
        from app.routes.reports.routes import _year_arg
        with app.test_request_context('/test?year=2024'):
            result = _year_arg()
            assert result == 2024

    def test_year_out_of_range_low(self, app):
        from app.routes.reports.routes import _year_arg
        from werkzeug.exceptions import BadRequest
        with app.test_request_context('/test?year=1999'):
            with pytest.raises(BadRequest):
                _year_arg()

    def test_year_out_of_range_high(self, app):
        from app.routes.reports.routes import _year_arg
        from werkzeug.exceptions import BadRequest
        with app.test_request_context('/test?year=2101'):
            with pytest.raises(BadRequest):
                _year_arg()

    def test_invalid_year_param(self, app):
        from app.routes.reports.routes import _year_arg
        from werkzeug.exceptions import BadRequest
        with app.test_request_context('/test?year=abc'):
            with pytest.raises(BadRequest):
                _year_arg()


class TestPickDateCol:
    """_pick_date_col функц тест"""

    def test_import_function(self):
        from app.routes.reports.routes import _pick_date_col
        assert _pick_date_col is not None

    def test_returns_column(self):
        from app.routes.reports.routes import _pick_date_col
        col = _pick_date_col()
        assert col is not None


class TestCodeExprAndJoin:
    """_code_expr_and_join функц тест"""

    def test_import_function(self):
        from app.routes.reports.routes import _code_expr_and_join
        assert _code_expr_and_join is not None


class TestParseDateSafe:
    """_parse_date_safe функц тест"""

    def test_import_function(self):
        from app.routes.reports.consumption import _parse_date_safe
        assert _parse_date_safe is not None

    def test_valid_date(self):
        from app.routes.reports.consumption import _parse_date_safe
        result = _parse_date_safe("2026-05-15")
        assert result == date(2026, 5, 15)

    def test_empty_value(self):
        from app.routes.reports.consumption import _parse_date_safe
        result = _parse_date_safe("")
        assert result is None

    def test_none_value(self):
        from app.routes.reports.consumption import _parse_date_safe
        result = _parse_date_safe(None)
        assert result is None

    def test_invalid_format(self):
        from app.routes.reports.consumption import _parse_date_safe
        result = _parse_date_safe("15/05/2026")
        assert result is None

    def test_invalid_string(self):
        from app.routes.reports.consumption import _parse_date_safe
        result = _parse_date_safe("not-a-date")
        assert result is None


class TestGetWeeksInMonth:
    """_get_weeks_in_month функц тест"""

    def test_import_function(self):
        from app.services.report_service import get_weeks_in_month as _get_weeks_in_month
        assert _get_weeks_in_month is not None

    def test_january_2026(self):
        from app.services.report_service import get_weeks_in_month as _get_weeks_in_month
        weeks = _get_weeks_in_month(2026, 1)
        assert len(weeks) > 0
        assert weeks[0][0] == 1  # week 1
        assert weeks[0][1] == date(2026, 1, 1)  # starts on Jan 1

    def test_february_2024_leap_year(self):
        from app.services.report_service import get_weeks_in_month as _get_weeks_in_month
        weeks = _get_weeks_in_month(2024, 2)
        assert len(weeks) > 0
        # February 2024 has 29 days (leap year)
        last_week = weeks[-1]
        assert last_week[2].day == 29

    def test_february_2025_non_leap(self):
        from app.services.report_service import get_weeks_in_month as _get_weeks_in_month
        weeks = _get_weeks_in_month(2025, 2)
        last_week = weeks[-1]
        assert last_week[2].day == 28

    def test_week_structure(self):
        from app.services.report_service import get_weeks_in_month as _get_weeks_in_month
        weeks = _get_weeks_in_month(2026, 3)
        for week_num, start, end in weeks:
            assert isinstance(week_num, int)
            assert isinstance(start, date)
            assert isinstance(end, date)
            assert start <= end
            assert (end - start).days <= 6  # max 7 days in a week


class TestErrorReasonLabels:
    """ERROR_REASON_LABELS тест"""

    def test_labels_exist(self):
        from app.routes.reports.consumption import ERROR_REASON_LABELS
        assert isinstance(ERROR_REASON_LABELS, dict)
        assert "measurement_error" in ERROR_REASON_LABELS
        assert "documentation_error" in ERROR_REASON_LABELS
        assert "equipment_or_env" in ERROR_REASON_LABELS


class TestReportsBlueprintRegistered:
    """Blueprint бүртгэгдсэн эсэх"""

    def test_blueprint_exists(self):
        from app.routes.reports.routes import reports_bp
        assert reports_bp is not None
        assert reports_bp.name == "reports"
        assert reports_bp.url_prefix == "/reports"


# ============================================================
# Route Tests with Flask Client
# ============================================================

class TestConsumptionRoute:
    """consumption route тест"""

    def test_with_logged_in_user(self, logged_in_user):
        """Нэвтэрсэн хэрэглэгчид хуудас харуулна"""
        response = logged_in_user.get('/reports/consumption')
        assert response.status_code == 200

    def test_with_year_param(self, logged_in_user):
        """year параметртай дуудах"""
        response = logged_in_user.get('/reports/consumption?year=2025')
        assert response.status_code == 200

    def test_invalid_year_returns_400(self, logged_in_user):
        """Буруу year параметр"""
        response = logged_in_user.get('/reports/consumption?year=1800')
        assert response.status_code == 400


class TestConsumptionCellRoute:
    """consumption_cell route тест"""

    def test_missing_params_returns_400(self, logged_in_user):
        """Параметргүй дуудвал 400"""
        response = logged_in_user.get('/reports/consumption_cell')
        assert response.status_code == 400

    def test_invalid_month_returns_400(self, logged_in_user):
        """Буруу сар"""
        response = logged_in_user.get('/reports/consumption_cell?year=2026&month=15&unit=QC&stype=Coal')
        assert response.status_code == 400

    def test_valid_params(self, logged_in_user):
        """Зөв параметр"""
        response = logged_in_user.get('/reports/consumption_cell?year=2026&month=5&unit=QC&stype=Coal')
        assert response.status_code == 200
        data = response.get_json()
        assert data.get("success") is True


class TestMonthlyPlanRoute:
    """monthly_plan route тест"""

    def test_with_logged_in_user(self, logged_in_user):
        """Нэвтэрсэн хэрэглэгчид хуудас харуулна"""
        response = logged_in_user.get('/reports/monthly_plan')
        assert response.status_code == 200

    def test_with_year_month_params(self, logged_in_user):
        """year, month параметр"""
        response = logged_in_user.get('/reports/monthly_plan?year=2025&month=6')
        assert response.status_code == 200

    def test_invalid_month_defaults(self, logged_in_user):
        """Буруу сар default болно"""
        response = logged_in_user.get('/reports/monthly_plan?year=2026&month=15')
        # Should default to current month
        assert response.status_code == 200


class TestApiGetMonthlyPlan:
    """api_get_monthly_plan тест"""

    def test_missing_params(self, logged_in_user):
        response = logged_in_user.get('/reports/api/monthly_plan')
        assert response.status_code == 400

    def test_valid_params(self, logged_in_user):
        response = logged_in_user.get('/reports/api/monthly_plan?year=2026&month=5')
        assert response.status_code == 200
        data = response.get_json()
        assert "year" in data
        assert "month" in data
        assert "plans" in data


class TestApiSaveMonthlyPlan:
    """api_save_monthly_plan тест"""

    def test_regular_user_forbidden(self, logged_in_user):
        """Энгийн хэрэглэгч хадгалж чадахгүй"""
        response = logged_in_user.post('/reports/api/monthly_plan',
                              json={"year": 2026, "month": 5, "plans": {}})
        assert response.status_code == 403

    def test_senior_user_can_save(self, logged_in_senior):
        """Senior хэрэглэгч хадгалж чадна"""
        response = logged_in_senior.post('/reports/api/monthly_plan',
                              json={"year": 2026, "month": 5, "plans": {}})
        assert response.status_code == 200
        data = response.get_json()
        assert data.get("success") is True

    def test_admin_user_can_save(self, logged_in_admin):
        """Admin хэрэглэгч хадгалж чадна"""
        response = logged_in_admin.post('/reports/api/monthly_plan',
                              json={"year": 2026, "month": 5, "plans": {"CHPP|Coal|1": 10}})
        assert response.status_code == 200

    def test_missing_year(self, logged_in_admin):
        response = logged_in_admin.post('/reports/api/monthly_plan',
                              json={"month": 5, "plans": {}})
        assert response.status_code == 400

    def test_invalid_key_format(self, logged_in_admin):
        """Буруу формат key-г алгасна"""
        response = logged_in_admin.post('/reports/api/monthly_plan',
                              json={"year": 2026, "month": 5, "plans": {"invalid_key": 10}})
        assert response.status_code == 200
        # Should succeed but not save invalid key


class TestApiSaveStaffSettings:
    """api_save_staff_settings тест"""

    def test_regular_user_forbidden(self, logged_in_user):
        response = logged_in_user.post('/reports/api/staff_settings',
                              json={"year": 2026, "month": 5})
        assert response.status_code == 403

    def test_admin_can_save(self, logged_in_admin):
        response = logged_in_admin.post('/reports/api/staff_settings',
                              json={"year": 2026, "month": 5,
                                   "staff_preparers": 8, "staff_chemists": 12})
        assert response.status_code == 200
        data = response.get_json()
        assert data.get("success") is True

    def test_missing_params(self, logged_in_admin):
        response = logged_in_admin.post('/reports/api/staff_settings',
                              json={})
        assert response.status_code == 400


class TestApiPlanStatistics:
    """api_plan_statistics тест"""

    def test_default_params(self, logged_in_user):
        """Default параметрүүдтэй ажиллана"""
        response = logged_in_user.get('/reports/api/plan_statistics')
        assert response.status_code == 200
        data = response.get_json()
        assert "yearly" in data
        assert "monthly" in data
        assert "weekly" in data
        assert "consignor" in data

    def test_with_date_range(self, logged_in_user):
        """Date range-тай"""
        response = logged_in_user.get('/reports/api/plan_statistics?from_year=2025&from_month=1&to_year=2026&to_month=6')
        assert response.status_code == 200
        data = response.get_json()
        assert data["from_year"] == 2025
        assert data["to_year"] == 2026

    def test_reversed_date_range(self, logged_in_user):
        """Урвуу date range автоматаар засагдана"""
        response = logged_in_user.get('/reports/api/plan_statistics?from_year=2026&from_month=6&to_year=2025&to_month=1')
        assert response.status_code == 200
        data = response.get_json()
        # Should swap the dates
        assert data["from_year"] <= data["to_year"]


class TestApiWeeklyPerformance:
    """api_weekly_performance тест"""

    def test_missing_params(self, logged_in_user):
        response = logged_in_user.get('/reports/api/weekly_performance')
        assert response.status_code == 400

    def test_valid_params(self, logged_in_user):
        response = logged_in_user.get('/reports/api/weekly_performance?year=2026&month=5')
        assert response.status_code == 200
        data = response.get_json()
        assert "year" in data
        assert "month" in data
        assert "weeks" in data
        assert "performance" in data


class TestCalculateConsumption:
    """_calculate_consumption функц тест"""

    def test_import_function(self):
        from app.routes.reports.consumption import _calculate_consumption
        assert _calculate_consumption is not None


class TestCalculateWeeklyPerformance:
    """_calculate_weekly_performance функц тест"""

    def test_import_function(self):
        from app.services.report_service import calculate_weekly_performance as _calculate_weekly_performance
        assert _calculate_weekly_performance is not None


class TestCountErrorReasons:
    """_count_error_reasons функц тест"""

    def test_import_function(self):
        from app.routes.reports.consumption import _count_error_reasons
        assert _count_error_reasons is not None


# ============================================================
# Fixtures - conftest.py дээрээс app, client, auth_user, auth_admin авна
# ============================================================

@pytest.fixture
def logged_in_user(auth_user):
    """auth_user-г ашиглана (chemist role)"""
    return auth_user


@pytest.fixture
def logged_in_senior(client, app):
    """Senior user (login via API)"""
    from app.models import User
    from app import db
    with app.app_context():
        user = User.query.filter_by(username='senior').first()
        if not user:
            user = User(username='senior', role='senior')
            user.set_password('TestPass123')
            db.session.add(user)
            db.session.commit()
    client.post('/login', data={'username': 'senior', 'password': 'TestPass123'})
    return client


@pytest.fixture
def logged_in_admin(auth_admin):
    """auth_admin-г ашиглана"""
    return auth_admin
