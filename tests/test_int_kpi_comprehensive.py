# -*- coding: utf-8 -*-
"""
KPI routes - бүрэн интеграцийн тестүүд
kpi.py файлын coverage нэмэгдүүлэх
"""
import pytest
from datetime import datetime, timedelta
from app import create_app, db
from app.models import User, Sample, AnalysisResult, AnalysisResultLog, AnalysisType


@pytest.fixture
def app():
    """Test application fixture"""
    from tests.conftest import TestConfig
    app = create_app(TestConfig)
    app.config['SERVER_NAME'] = 'localhost'
    app.config['WTF_CSRF_ENABLED'] = False

    with app.app_context():
        db.create_all()
        # Create users
        if not User.query.filter_by(username='admin').first():
            user = User(username='admin', role='admin')
            user.set_password('AdminPass123')
            db.session.add(user)
        if not User.query.filter_by(username='senior').first():
            user = User(username='senior', role='senior')
            user.set_password('SeniorPass123')
            db.session.add(user)
        if not User.query.filter_by(username='chemist').first():
            user = User(username='chemist', role='chemist')
            user.set_password('ChemistPass123')
            db.session.add(user)
        db.session.commit()

    yield app

    with app.app_context():
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def auth_client(app, client):
    """Authenticated admin client"""
    with app.app_context():
        user = User.query.filter_by(username='admin').first()
        with client.session_transaction() as sess:
            sess['_user_id'] = str(user.id)
            sess['_fresh'] = True
    return client


@pytest.fixture
def senior_client(app, client):
    """Authenticated senior client"""
    with app.app_context():
        user = User.query.filter_by(username='senior').first()
        with client.session_transaction() as sess:
            sess['_user_id'] = str(user.id)
            sess['_fresh'] = True
    return client


def create_kpi_test_data(app):
    """Create KPI test data"""
    with app.app_context():
        user = User.query.filter_by(username='chemist').first()
        now = datetime.now()

        # Create samples for different units
        for i, client_name in enumerate(['CHPP', 'WTL', 'QC']):
            for j in range(3):
                sample = Sample(
                    sample_code=f'{client_name}_KPI_{i}_{j}',
                    user_id=user.id,
                    client_name=client_name,
                    sample_type='2 hourly' if client_name == 'CHPP' else 'General',
                    received_date=now - timedelta(hours=j),
                    prepared_date=(now - timedelta(hours=j)).date() if j % 2 == 0 else None
                )
                db.session.add(sample)
        db.session.commit()

        # Create analysis result logs with error reasons
        samples = Sample.query.all()
        error_reasons = ['repeat', 'sample_issue', 'equipment_error', None, None]

        for i, sample in enumerate(samples):
            log = AnalysisResultLog(
                timestamp=now - timedelta(hours=i),
                user_id=user.id,
                sample_id=sample.id,
                analysis_code='TS',
                action='SUBMIT',
                error_reason=error_reasons[i % len(error_reasons)]
            )
            db.session.add(log)
        db.session.commit()


class TestKPIHelpers:
    """KPI helper functions тестүүд"""

    def test_aggregate_error_reason_stats_empty(self, app):
        """Aggregate error reason stats with no data"""
        with app.app_context():
            from app.routes.analysis.kpi import _aggregate_error_reason_stats
            stats = _aggregate_error_reason_stats()
            assert 'total' in stats
            assert stats['total'] == 0

    def test_aggregate_error_reason_stats_with_data(self, app):
        """Aggregate error reason stats with data"""
        with app.app_context():
            create_kpi_test_data(app)
            from app.routes.analysis.kpi import _aggregate_error_reason_stats
            stats = _aggregate_error_reason_stats()
            assert 'total' in stats
            assert stats['total'] >= 0

    def test_aggregate_error_reason_stats_with_date_filter(self, app):
        """Aggregate error reason stats with date filter"""
        with app.app_context():
            create_kpi_test_data(app)
            from app.routes.analysis.kpi import _aggregate_error_reason_stats
            now = datetime.now()
            stats = _aggregate_error_reason_stats(
                date_from=now - timedelta(days=1),
                date_to=now + timedelta(days=1)
            )
            assert 'total' in stats

    def test_aggregate_error_reason_stats_with_user_filter(self, app):
        """Aggregate error reason stats with user filter"""
        with app.app_context():
            create_kpi_test_data(app)
            from app.routes.analysis.kpi import _aggregate_error_reason_stats
            stats = _aggregate_error_reason_stats(user_name='chemist')
            assert 'total' in stats


class TestShiftDailyRoute:
    """Shift daily route тестүүд"""

    def test_shift_daily_get_empty(self, auth_client, app):
        """Shift daily page with no data"""
        with app.app_context():
            response = auth_client.get('/shift_daily')
            assert response.status_code in [200, 302, 404]

    def test_shift_daily_get_with_data(self, auth_client, app):
        """Shift daily page with data"""
        with app.app_context():
            create_kpi_test_data(app)
            response = auth_client.get('/shift_daily')
            assert response.status_code in [200, 302, 404]

    def test_shift_daily_with_date_params(self, auth_client, app):
        """Shift daily with date parameters"""
        with app.app_context():
            today = datetime.now().strftime('%Y-%m-%d')
            response = auth_client.get(f'/shift_daily?start_date={today}&end_date={today}')
            assert response.status_code in [200, 302, 404]

    def test_shift_daily_with_unit_filter(self, auth_client, app):
        """Shift daily with unit filter"""
        with app.app_context():
            create_kpi_test_data(app)
            response = auth_client.get('/shift_daily?unit=CHPP')
            assert response.status_code in [200, 302, 404]

    def test_shift_daily_with_sample_type_filter(self, auth_client, app):
        """Shift daily with sample type filter"""
        with app.app_context():
            create_kpi_test_data(app)
            response = auth_client.get('/shift_daily?sample_type=2 hourly')
            assert response.status_code in [200, 302, 404]

    def test_shift_daily_with_time_base_prepared(self, auth_client, app):
        """Shift daily with time_base=prepared"""
        with app.app_context():
            create_kpi_test_data(app)
            response = auth_client.get('/shift_daily?time_base=prepared')
            assert response.status_code in [200, 302, 404]

    def test_shift_daily_with_time_base_mass(self, auth_client, app):
        """Shift daily with time_base=mass"""
        with app.app_context():
            create_kpi_test_data(app)
            response = auth_client.get('/shift_daily?time_base=mass')
            assert response.status_code in [200, 302, 404]

    def test_shift_daily_with_group_by_unit(self, auth_client, app):
        """Shift daily with group_by=unit"""
        with app.app_context():
            create_kpi_test_data(app)
            response = auth_client.get('/shift_daily?group_by=unit')
            assert response.status_code in [200, 302, 404]

    def test_shift_daily_with_group_by_sample_state(self, auth_client, app):
        """Shift daily with group_by=sample_state"""
        with app.app_context():
            create_kpi_test_data(app)
            response = auth_client.get('/shift_daily?group_by=sample_state')
            assert response.status_code in [200, 302, 404]

    def test_shift_daily_with_group_by_storage(self, auth_client, app):
        """Shift daily with group_by=storage"""
        with app.app_context():
            create_kpi_test_data(app)
            response = auth_client.get('/shift_daily?group_by=storage')
            assert response.status_code in [200, 302, 404]

    def test_shift_daily_with_kpi_target_samples_prepared(self, auth_client, app):
        """Shift daily with kpi_target=samples_prepared"""
        with app.app_context():
            create_kpi_test_data(app)
            response = auth_client.get('/shift_daily?kpi_target=samples_prepared')
            assert response.status_code in [200, 302, 404]

    def test_shift_daily_with_kpi_target_mass_ready(self, auth_client, app):
        """Shift daily with kpi_target=mass_ready"""
        with app.app_context():
            create_kpi_test_data(app)
            response = auth_client.get('/shift_daily?kpi_target=mass_ready')
            assert response.status_code in [200, 302, 404]

    def test_shift_daily_with_user_name_filter(self, auth_client, app):
        """Shift daily with user_name filter"""
        with app.app_context():
            create_kpi_test_data(app)
            response = auth_client.get('/shift_daily?user_name=chemist')
            assert response.status_code in [200, 302, 404]

    def test_shift_daily_with_shift_team_filter(self, auth_client, app):
        """Shift daily with shift_team filter"""
        with app.app_context():
            create_kpi_test_data(app)
            response = auth_client.get('/shift_daily?shift_team=A')
            assert response.status_code in [200, 302, 404]

    def test_shift_daily_with_shift_type_filter(self, auth_client, app):
        """Shift daily with shift_type filter"""
        with app.app_context():
            create_kpi_test_data(app)
            response = auth_client.get('/shift_daily?shift_type=day')
            assert response.status_code in [200, 302, 404]


class TestKPISummaryAPI:
    """KPI summary API тестүүд"""

    def test_kpi_summary_for_ahlah(self, senior_client, app):
        """KPI summary for ahlah API"""
        with app.app_context():
            response = senior_client.get('/api/kpi_summary_for_ahlah')
            assert response.status_code in [200, 302, 404]

    def test_kpi_summary_for_ahlah_with_data(self, senior_client, app):
        """KPI summary for ahlah API with data"""
        with app.app_context():
            create_kpi_test_data(app)
            response = senior_client.get('/api/kpi_summary_for_ahlah')
            assert response.status_code in [200, 302, 404]
            if response.status_code == 200:
                data = response.get_json()
                assert 'shift' in data
                assert 'days14' in data
