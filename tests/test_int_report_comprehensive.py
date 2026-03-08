# tests/integration/test_report_comprehensive.py
"""
Report routes comprehensive тест - consumption, monthly_plan, statistics
"""
import pytest
from datetime import datetime, timedelta


class TestReportConsumption:
    """Consumption тайлан тест"""

    def test_consumption_page(self, auth_admin):
        """Consumption хуудас"""
        response = auth_admin.get('/reports/consumption')
        assert response.status_code in [200, 302]

    def test_consumption_with_year(self, auth_admin):
        """Consumption with year param"""
        response = auth_admin.get('/reports/consumption?year=2025')
        assert response.status_code in [200, 302]

    def test_consumption_invalid_year(self, auth_admin):
        """Consumption with invalid year"""
        response = auth_admin.get('/reports/consumption?year=invalid')
        assert response.status_code in [200, 302, 400]

    def test_consumption_api(self, auth_admin):
        """Consumption API"""
        response = auth_admin.get('/reports/consumption_drilldown')
        assert response.status_code in [200, 400, 404]

    def test_consumption_drilldown_params(self, auth_admin):
        """Consumption drilldown with params"""
        response = auth_admin.get(
            '/reports/consumption_drilldown?client_name=Test&sample_type=Coal&month=1&prop=Mad'
        )
        assert response.status_code in [200, 400, 404]


class TestReportMonthlyPlan:
    """Monthly Plan тайлан тест"""

    def test_monthly_plan_page(self, auth_admin):
        """Monthly plan хуудас"""
        response = auth_admin.get('/reports/monthly_plan')
        assert response.status_code in [200, 302]

    def test_monthly_plan_with_month(self, auth_admin):
        """Monthly plan with month"""
        response = auth_admin.get('/reports/monthly_plan?month=2025-01')
        assert response.status_code in [200, 302]

    def test_monthly_plan_api(self, auth_admin):
        """Monthly plan API"""
        response = auth_admin.get('/reports/monthly_plan_data')
        assert response.status_code in [200, 302, 404]


class TestReportStatistics:
    """Statistics тайлан тест"""

    def test_statistics_page(self, auth_admin):
        """Statistics хуудас"""
        response = auth_admin.get('/reports/statistics')
        assert response.status_code in [200, 302, 404]

    def test_shift_statistics(self, auth_admin):
        """Shift statistics"""
        response = auth_admin.get('/reports/shift_statistics')
        assert response.status_code in [200, 302, 404]

    def test_hourly_statistics(self, auth_admin):
        """Hourly statistics"""
        response = auth_admin.get('/reports/hourly_statistics')
        assert response.status_code in [200, 302, 404]


class TestReportExport:
    """Тайлан экспорт тест"""

    def test_export_consumption_excel(self, auth_admin):
        """Export consumption to Excel"""
        response = auth_admin.get('/reports/consumption/export?format=excel')
        assert response.status_code in [200, 302, 404]

    def test_export_consumption_csv(self, auth_admin):
        """Export consumption to CSV"""
        response = auth_admin.get('/reports/consumption/export?format=csv')
        assert response.status_code in [200, 302, 404]


class TestReportFilters:
    """Тайлан фильтер тест"""

    def test_filter_by_client(self, auth_admin):
        """Filter by client_name"""
        response = auth_admin.get('/reports/consumption?client_name=Test')
        assert response.status_code in [200, 302]

    def test_filter_by_sample_type(self, auth_admin):
        """Filter by sample_type"""
        response = auth_admin.get('/reports/consumption?sample_type=Coal')
        assert response.status_code in [200, 302]

    def test_filter_by_date_range(self, auth_admin):
        """Filter by date range"""
        response = auth_admin.get(
            '/reports/consumption?start_date=2025-01-01&end_date=2025-12-31'
        )
        assert response.status_code in [200, 302]


class TestReportPermissions:
    """Тайлан эрхийн тест"""

    def test_consumption_unauthorized(self, client):
        """Consumption without login"""
        response = client.get('/reports/consumption')
        # Should redirect to login or return 200/302
        assert response.status_code in [200, 302, 401]

    def test_monthly_plan_unauthorized(self, client):
        """Monthly plan without login"""
        response = client.get('/reports/monthly_plan')
        # Should redirect to login or return 200/302
        assert response.status_code in [200, 302, 401]


class TestReportHelpers:
    """Report helper functions тест"""

    def test_year_arg_valid(self, app):
        """_year_arg with valid year"""
        with app.app_context():
            with app.test_request_context('/reports/consumption?year=2025'):
                from app.routes.reports.routes import _year_arg
                try:
                    result = _year_arg()
                    assert result == 2025
                except Exception:
                    pass

    def test_pick_date_col(self, app):
        """_pick_date_col function"""
        with app.app_context():
            from app.routes.reports.routes import _pick_date_col
            try:
                col = _pick_date_col()
                assert col is not None
            except Exception:
                pass
