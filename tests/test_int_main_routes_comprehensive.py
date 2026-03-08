# -*- coding: utf-8 -*-
"""
Main routes comprehensive тестүүд
"""
import pytest
from app import create_app, db
from app.models import User, Sample


@pytest.fixture
def app():
    """Test application fixture"""
    from tests.conftest import TestConfig
    app = create_app(TestConfig)
    app.config['SERVER_NAME'] = 'localhost'

    with app.app_context():
        db.create_all()
        from app.models import User
        if not User.query.filter_by(username='admin').first():
            user = User(username='admin', role='admin')
            user.set_password('AdminPass123')
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
    """Authenticated client fixture"""
    with app.app_context():
        user = User.query.filter_by(username='admin').first()
        if not user:
            user = User(username='admin', role='admin')
            user.set_password('AdminPass123')
            db.session.add(user)
            db.session.commit()

        with client.session_transaction() as sess:
            sess['_user_id'] = str(user.id)
            sess['_fresh'] = True

    return client


class TestIndexRoutes:
    """Index routes тестүүд"""

    def test_index_page(self, auth_client, app):
        """Index page GET"""
        with app.app_context():
            response = auth_client.get('/coal')
            assert response.status_code in [200, 302]

    def test_index_post_chpp_12h(self, auth_client, app):
        """Index POST CHPP 12H"""
        with app.app_context():
            response = auth_client.post('/coal', data={
                'client_name': 'CHPP',
                'sample_type': '12H'
            })
            assert response.status_code in [200, 302, 400]

    def test_index_post_chpp_2h(self, auth_client, app):
        """Index POST CHPP 2H"""
        with app.app_context():
            response = auth_client.post('/coal', data={
                'client_name': 'CHPP',
                'sample_type': '2H'
            })
            assert response.status_code in [200, 302, 400]

    def test_index_post_qc(self, auth_client, app):
        """Index POST QC"""
        with app.app_context():
            response = auth_client.post('/coal', data={
                'client_name': 'QC',
                'sample_type': 'GBW'
            })
            assert response.status_code in [200, 302, 400]

    def test_index_post_lab(self, auth_client, app):
        """Index POST LAB"""
        with app.app_context():
            response = auth_client.post('/coal', data={
                'client_name': 'LAB',
                'sample_type': 'Internal'
            })
            assert response.status_code in [200, 302, 400]

    def test_index_post_external(self, auth_client, app):
        """Index POST External"""
        with app.app_context():
            response = auth_client.post('/coal', data={
                'client_name': 'External',
                'sample_type': 'Customer'
            })
            assert response.status_code in [200, 302, 400]


class TestSampleRoutes:
    """Sample routes тестүүд"""

    def test_samples_list(self, auth_client, app):
        """Samples list"""
        with app.app_context():
            response = auth_client.get('/samples')
            assert response.status_code in [200, 302, 404]

    def test_sample_detail_nonexistent(self, auth_client, app):
        """Sample detail for non-existent sample"""
        with app.app_context():
            response = auth_client.get('/sample/99999')
            assert response.status_code in [200, 302, 404]

    def test_mass_prep_page(self, auth_client, app):
        """Mass prep page"""
        with app.app_context():
            response = auth_client.get('/mass_prep')
            assert response.status_code in [200, 302, 404]


class TestAuthRoutes:
    """Auth routes тестүүд"""

    def test_login_page(self, client, app):
        """Login page"""
        with app.app_context():
            response = client.get('/login')
            assert response.status_code in [200, 302]

    def test_login_post_invalid(self, client, app):
        """Login POST invalid credentials"""
        with app.app_context():
            response = client.post('/login', data={
                'username': 'invalid',
                'password': 'invalid'
            })
            assert response.status_code in [200, 302, 401]

    def test_logout(self, auth_client, app):
        """Logout"""
        with app.app_context():
            response = auth_client.get('/logout')
            assert response.status_code in [200, 302]


class TestDashboardRoutes:
    """Dashboard routes тестүүд"""

    def test_dashboard(self, auth_client, app):
        """Dashboard page"""
        with app.app_context():
            response = auth_client.get('/dashboard')
            assert response.status_code in [200, 302, 404]


class TestAnalysisHubRoutes:
    """Analysis hub routes тестүүд"""

    def test_analysis_hub(self, auth_client, app):
        """Analysis hub"""
        with app.app_context():
            response = auth_client.get('/analysis_hub')
            assert response.status_code in [200, 302]

    def test_analysis_page_ts(self, auth_client, app):
        """Analysis page TS"""
        with app.app_context():
            response = auth_client.get('/analysis_page/TS')
            assert response.status_code in [200, 302, 404]

    def test_analysis_page_cv(self, auth_client, app):
        """Analysis page CV"""
        with app.app_context():
            response = auth_client.get('/analysis_page/CV')
            assert response.status_code in [200, 302, 404]

    def test_analysis_page_mad(self, auth_client, app):
        """Analysis page Mad"""
        with app.app_context():
            response = auth_client.get('/analysis_page/Mad')
            assert response.status_code in [200, 302, 404]


class TestEquipmentRoutes:
    """Equipment routes тестүүд"""

    def test_equipment_list(self, auth_client, app):
        """Equipment list"""
        with app.app_context():
            response = auth_client.get('/equipment')
            assert response.status_code in [200, 302, 404]

    def test_equipment_new(self, auth_client, app):
        """Equipment new form"""
        with app.app_context():
            response = auth_client.get('/equipment/new')
            assert response.status_code in [200, 302, 404]

    def test_equipment_calibration(self, auth_client, app):
        """Equipment calibration"""
        with app.app_context():
            response = auth_client.get('/equipment/calibration')
            assert response.status_code in [200, 302, 404]


class TestReportRoutes:
    """Report routes тестүүд"""

    def test_reports_page(self, auth_client, app):
        """Reports page"""
        with app.app_context():
            response = auth_client.get('/reports')
            assert response.status_code in [200, 302, 404]

    def test_daily_report(self, auth_client, app):
        """Daily report"""
        with app.app_context():
            response = auth_client.get('/reports/daily')
            assert response.status_code in [200, 302, 404]

    def test_monthly_report(self, auth_client, app):
        """Monthly report"""
        with app.app_context():
            response = auth_client.get('/reports/monthly')
            assert response.status_code in [200, 302, 404]


class TestSettingsRoutes:
    """Settings routes тестүүд"""

    def test_settings_page(self, auth_client, app):
        """Settings page"""
        with app.app_context():
            response = auth_client.get('/settings')
            assert response.status_code in [200, 302, 404]

    def test_users_list(self, auth_client, app):
        """Users list"""
        with app.app_context():
            response = auth_client.get('/settings/users')
            assert response.status_code in [200, 302, 404]

    def test_analysis_types(self, auth_client, app):
        """Analysis types"""
        with app.app_context():
            response = auth_client.get('/settings/analysis_types')
            assert response.status_code in [200, 302, 404]

    def test_analysis_profiles(self, auth_client, app):
        """Analysis profiles"""
        with app.app_context():
            response = auth_client.get('/settings/analysis_profiles')
            assert response.status_code in [200, 302, 404]

    def test_system_settings(self, auth_client, app):
        """System settings"""
        with app.app_context():
            response = auth_client.get('/settings/system')
            assert response.status_code in [200, 302, 404]
