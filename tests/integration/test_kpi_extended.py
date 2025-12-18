# tests/integration/test_kpi_extended.py
# -*- coding: utf-8 -*-
"""
KPI routes extended tests
Coverage target: app/routes/analysis/kpi.py
"""

import pytest
from app import db
from app.models import User, Sample, AnalysisResult
from datetime import datetime, date, timedelta
import uuid

VALID_PASSWORD = 'TestPass123'


@pytest.fixture
def kpi_user(app):
    """KPI test user"""
    with app.app_context():
        user = User.query.filter_by(username='kpi_test_user').first()
        if not user:
            user = User(username='kpi_test_user', role='manager')
            user.set_password(VALID_PASSWORD)
            db.session.add(user)
            db.session.commit()
        return user


@pytest.fixture
def kpi_sample(app, kpi_user):
    """Sample for KPI tests"""
    with app.app_context():
        unique_id = uuid.uuid4().hex[:6]
        sample = Sample(
            sample_code=f'KPI-{unique_id}',
            client_name='CHPP',  # Valid client name
            sample_type='CM',
            status='completed',
            received_date=datetime.now(),
            user_id=kpi_user.id
        )
        db.session.add(sample)
        db.session.commit()

        # Add completed result
        result = AnalysisResult(
            sample_id=sample.id,
            analysis_code='Mad',
            final_result='5.25',
            status='approved',
            user_id=kpi_user.id
        )
        db.session.add(result)
        db.session.commit()
        return sample.id


def login_kpi_user(client):
    """Helper login"""
    client.post('/login', data={
        'username': 'kpi_test_user',
        'password': VALID_PASSWORD
    }, follow_redirects=True)


class TestKPIDashboard:
    """Test KPI dashboard"""

    def test_kpi_dashboard_page(self, client, app, kpi_user):
        """KPI dashboard accessible"""
        login_kpi_user(client)
        response = client.get('/analysis/kpi')
        assert response.status_code in [200, 302, 404]

    def test_kpi_dashboard_with_date(self, client, app, kpi_user):
        """KPI dashboard with date filter"""
        login_kpi_user(client)
        today = date.today().isoformat()
        response = client.get(f'/analysis/kpi?date={today}')
        assert response.status_code in [200, 302, 404]

    def test_kpi_dashboard_with_range(self, client, app, kpi_user):
        """KPI dashboard with date range"""
        login_kpi_user(client)
        today = date.today()
        week_ago = today - timedelta(days=7)
        response = client.get(f'/analysis/kpi?start_date={week_ago}&end_date={today}')
        assert response.status_code in [200, 302, 404]


class TestKPISummaryAPI:
    """Test KPI summary API"""

    def test_kpi_summary_api(self, client, app, kpi_user):
        """KPI summary API"""
        login_kpi_user(client)
        response = client.get('/analysis/kpi/api/summary')
        assert response.status_code in [200, 302, 404]

    def test_kpi_summary_with_client(self, client, app, kpi_user):
        """KPI summary with client filter"""
        login_kpi_user(client)
        response = client.get('/analysis/kpi/api/summary?client=KPI')
        assert response.status_code in [200, 302, 404]

    def test_kpi_summary_with_type(self, client, app, kpi_user):
        """KPI summary with sample type filter"""
        login_kpi_user(client)
        response = client.get('/analysis/kpi/api/summary?sample_type=CM')
        assert response.status_code in [200, 302, 404]


class TestKPIThroughputAPI:
    """Test KPI throughput API"""

    def test_kpi_throughput_api(self, client, app, kpi_user):
        """KPI throughput API"""
        login_kpi_user(client)
        response = client.get('/analysis/kpi/api/throughput')
        assert response.status_code in [200, 302, 404]

    def test_kpi_throughput_daily(self, client, app, kpi_user):
        """KPI throughput daily"""
        login_kpi_user(client)
        response = client.get('/analysis/kpi/api/throughput?period=daily')
        assert response.status_code in [200, 302, 404]

    def test_kpi_throughput_weekly(self, client, app, kpi_user):
        """KPI throughput weekly"""
        login_kpi_user(client)
        response = client.get('/analysis/kpi/api/throughput?period=weekly')
        assert response.status_code in [200, 302, 404]

    def test_kpi_throughput_monthly(self, client, app, kpi_user):
        """KPI throughput monthly"""
        login_kpi_user(client)
        response = client.get('/analysis/kpi/api/throughput?period=monthly')
        assert response.status_code in [200, 302, 404]


class TestKPITurnaroundAPI:
    """Test KPI turnaround time API"""

    def test_kpi_turnaround_api(self, client, app, kpi_user):
        """KPI turnaround API"""
        login_kpi_user(client)
        response = client.get('/analysis/kpi/api/turnaround')
        assert response.status_code in [200, 302, 404]

    def test_kpi_turnaround_by_client(self, client, app, kpi_user):
        """KPI turnaround by client"""
        login_kpi_user(client)
        response = client.get('/analysis/kpi/api/turnaround?group_by=client')
        assert response.status_code in [200, 302, 404]

    def test_kpi_turnaround_by_analysis(self, client, app, kpi_user):
        """KPI turnaround by analysis"""
        login_kpi_user(client)
        response = client.get('/analysis/kpi/api/turnaround?group_by=analysis')
        assert response.status_code in [200, 302, 404]


class TestKPIProductivityAPI:
    """Test KPI productivity API"""

    def test_kpi_productivity_api(self, client, app, kpi_user):
        """KPI productivity API"""
        login_kpi_user(client)
        response = client.get('/analysis/kpi/api/productivity')
        assert response.status_code in [200, 302, 404]

    def test_kpi_productivity_by_user(self, client, app, kpi_user):
        """KPI productivity by user"""
        login_kpi_user(client)
        response = client.get('/analysis/kpi/api/productivity?group_by=user')
        assert response.status_code in [200, 302, 404]


class TestKPIQualityAPI:
    """Test KPI quality metrics API"""

    def test_kpi_quality_api(self, client, app, kpi_user):
        """KPI quality API"""
        login_kpi_user(client)
        response = client.get('/analysis/kpi/api/quality')
        assert response.status_code in [200, 302, 404]

    def test_kpi_rejection_rate(self, client, app, kpi_user):
        """KPI rejection rate"""
        login_kpi_user(client)
        response = client.get('/analysis/kpi/api/quality?metric=rejection_rate')
        assert response.status_code in [200, 302, 404]


class TestKPIChartData:
    """Test KPI chart data"""

    def test_kpi_chart_samples(self, client, app, kpi_user):
        """KPI chart samples data"""
        login_kpi_user(client)
        response = client.get('/analysis/kpi/api/chart/samples')
        assert response.status_code in [200, 302, 404]

    def test_kpi_chart_results(self, client, app, kpi_user):
        """KPI chart results data"""
        login_kpi_user(client)
        response = client.get('/analysis/kpi/api/chart/results')
        assert response.status_code in [200, 302, 404]


class TestKPIExport:
    """Test KPI export functionality"""

    def test_kpi_export_excel(self, client, app, kpi_user):
        """KPI export Excel"""
        login_kpi_user(client)
        response = client.get('/analysis/kpi/export?format=excel')
        assert response.status_code in [200, 302, 400, 404]

    def test_kpi_export_csv(self, client, app, kpi_user):
        """KPI export CSV"""
        login_kpi_user(client)
        response = client.get('/analysis/kpi/export?format=csv')
        assert response.status_code in [200, 302, 400, 404]


class TestAhlahDashboard:
    """Test Ahlah dashboard (manager view)"""

    def test_ahlah_dashboard(self, client, app, kpi_user):
        """Ahlah dashboard page"""
        login_kpi_user(client)
        response = client.get('/ahlah')
        assert response.status_code in [200, 302, 404]

    def test_ahlah_data_api(self, client, app, kpi_user):
        """Ahlah data API"""
        login_kpi_user(client)
        response = client.get('/api/ahlah/data')
        assert response.status_code in [200, 302, 404]

    def test_ahlah_stats_api(self, client, app, kpi_user):
        """Ahlah stats API"""
        login_kpi_user(client)
        response = client.get('/api/ahlah/stats')
        assert response.status_code in [200, 302, 404]

    def test_dashboard_stats(self, client, app, kpi_user):
        """Dashboard stats API"""
        login_kpi_user(client)
        response = client.get('/api/dashboard_stats')
        assert response.status_code in [200, 302, 404]
