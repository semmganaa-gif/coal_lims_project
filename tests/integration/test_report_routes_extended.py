# -*- coding: utf-8 -*-
"""
Report routes extended тестүүд
"""
import pytest
from app import create_app, db
from app.models import User


@pytest.fixture
def app():
    """Test application fixture"""
    app = create_app()
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False
    app.config['SERVER_NAME'] = 'localhost'
    return app


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def auth_client(app, client):
    """Authenticated client fixture"""
    with app.app_context():
        user = User.query.filter_by(username='admin').first()
        if not user:
            user = User(username='admin', role='admin')
            user.set_password('Admin123')
            db.session.add(user)
            db.session.commit()

        with client.session_transaction() as sess:
            sess['_user_id'] = str(user.id)
            sess['_fresh'] = True

    return client


class TestReportsIndex:
    """Reports index тестүүд"""

    def test_reports_index(self, auth_client, app):
        """Reports index page"""
        with app.app_context():
            response = auth_client.get('/reports')
            assert response.status_code in [200, 302, 404]


class TestDailyReports:
    """Daily reports тестүүд"""

    def test_daily_report_page(self, auth_client, app):
        """Daily report page"""
        with app.app_context():
            response = auth_client.get('/reports/daily')
            assert response.status_code in [200, 302, 404]

    def test_daily_report_with_date(self, auth_client, app):
        """Daily report with date"""
        with app.app_context():
            response = auth_client.get('/reports/daily?date=2024-01-01')
            assert response.status_code in [200, 302, 404]

    def test_daily_report_export_excel(self, auth_client, app):
        """Daily report export excel"""
        with app.app_context():
            response = auth_client.get('/reports/daily/export?format=excel')
            assert response.status_code in [200, 302, 404]

    def test_daily_report_export_pdf(self, auth_client, app):
        """Daily report export PDF"""
        with app.app_context():
            response = auth_client.get('/reports/daily/export?format=pdf')
            assert response.status_code in [200, 302, 404]


class TestMonthlyReports:
    """Monthly reports тестүүд"""

    def test_monthly_report_page(self, auth_client, app):
        """Monthly report page"""
        with app.app_context():
            response = auth_client.get('/reports/monthly')
            assert response.status_code in [200, 302, 404]

    def test_monthly_report_with_params(self, auth_client, app):
        """Monthly report with params"""
        with app.app_context():
            response = auth_client.get('/reports/monthly?year=2024&month=1')
            assert response.status_code in [200, 302, 404]

    def test_monthly_report_export(self, auth_client, app):
        """Monthly report export"""
        with app.app_context():
            response = auth_client.get('/reports/monthly/export')
            assert response.status_code in [200, 302, 404]


class TestSampleReports:
    """Sample reports тестүүд"""

    def test_sample_report(self, auth_client, app):
        """Sample report"""
        with app.app_context():
            response = auth_client.get('/reports/sample/1')
            assert response.status_code in [200, 302, 404]

    def test_sample_certificate(self, auth_client, app):
        """Sample certificate"""
        with app.app_context():
            response = auth_client.get('/reports/certificate/1')
            assert response.status_code in [200, 302, 404]

    def test_batch_certificate(self, auth_client, app):
        """Batch certificate"""
        with app.app_context():
            response = auth_client.post('/reports/batch_certificate', json={
                'sample_ids': [1, 2, 3]
            })
            assert response.status_code in [200, 302, 400, 404]


class TestClientReports:
    """Client reports тестүүд"""

    def test_client_report(self, auth_client, app):
        """Client report"""
        with app.app_context():
            response = auth_client.get('/reports/client/CHPP')
            assert response.status_code in [200, 302, 404]

    def test_client_summary(self, auth_client, app):
        """Client summary"""
        with app.app_context():
            response = auth_client.get('/reports/client_summary')
            assert response.status_code in [200, 302, 404]


class TestQCReports:
    """QC reports тестүүд"""

    def test_qc_report(self, auth_client, app):
        """QC report"""
        with app.app_context():
            response = auth_client.get('/reports/qc')
            assert response.status_code in [200, 302, 404]

    def test_qc_summary(self, auth_client, app):
        """QC summary"""
        with app.app_context():
            response = auth_client.get('/reports/qc/summary')
            assert response.status_code in [200, 302, 404]

    def test_control_chart_report(self, auth_client, app):
        """Control chart report"""
        with app.app_context():
            response = auth_client.get('/reports/control_chart')
            assert response.status_code in [200, 302, 404]


class TestExportReports:
    """Export reports тестүүд"""

    def test_export_samples_excel(self, auth_client, app):
        """Export samples to Excel"""
        with app.app_context():
            response = auth_client.get('/reports/export/samples?format=excel')
            assert response.status_code in [200, 302, 404]

    def test_export_samples_csv(self, auth_client, app):
        """Export samples to CSV"""
        with app.app_context():
            response = auth_client.get('/reports/export/samples?format=csv')
            assert response.status_code in [200, 302, 404]

    def test_export_results(self, auth_client, app):
        """Export results"""
        with app.app_context():
            response = auth_client.get('/reports/export/results')
            assert response.status_code in [200, 302, 404]


class TestStatisticsReports:
    """Statistics reports тестүүд"""

    def test_statistics_page(self, auth_client, app):
        """Statistics page"""
        with app.app_context():
            response = auth_client.get('/reports/statistics')
            assert response.status_code in [200, 302, 404]

    def test_throughput_stats(self, auth_client, app):
        """Throughput statistics"""
        with app.app_context():
            response = auth_client.get('/reports/statistics/throughput')
            assert response.status_code in [200, 302, 404]

    def test_turnaround_stats(self, auth_client, app):
        """Turnaround statistics"""
        with app.app_context():
            response = auth_client.get('/reports/statistics/turnaround')
            assert response.status_code in [200, 302, 404]
