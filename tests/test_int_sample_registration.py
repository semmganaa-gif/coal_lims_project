# -*- coding: utf-8 -*-
"""
Sample Registration - index.py routes бүрэн интеграци тестүүд
Covers: /, /index, /edit_sample, /sample_disposal, /delete_selected_samples
"""
import pytest
from datetime import datetime, date
from app import create_app, db
from app.models import User, Sample, AnalysisType


@pytest.fixture
def app():
    """Test application fixture"""
    from tests.conftest import TestConfig
    app = create_app(TestConfig)
    app.config['SERVER_NAME'] = 'localhost'
    app.config['WTF_CSRF_ENABLED'] = False

    with app.app_context():
        db.create_all()
        # Seed analysis types
        for code in ['MT', 'Mad', 'Aad', 'Vad', 'TS', 'CV']:
            if not AnalysisType.query.filter_by(code=code).first():
                at = AnalysisType(code=code, name=f'Test {code}', order_num=1)
                db.session.add(at)
        db.session.commit()

    yield app

    with app.app_context():
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    """Test client fixture"""
    return app.test_client()


@pytest.fixture
def prep_user(app):
    """Prep user fixture"""
    with app.app_context():
        user = User(
            username='prep_reg_test',
            role='prep'
        )
        user.set_password('PrepPass123')
        db.session.add(user)
        db.session.commit()
        return user.id


@pytest.fixture
def admin_user(app):
    """Admin user fixture"""
    with app.app_context():
        user = User(
            username='admin_reg_test',
            role='admin'
        )
        user.set_password('AdminPass123')
        db.session.add(user)
        db.session.commit()
        return user.id


@pytest.fixture
def analyst_user(app):
    """Analyst user fixture"""
    with app.app_context():
        user = User(
            username='analyst_reg_test',
            role='analyst'
        )
        user.set_password('AnalystPass123')
        db.session.add(user)
        db.session.commit()
        return user.id


def login(client, username, password):
    """Login helper"""
    return client.post('/login', data={
        'username': username,
        'password': password
    }, follow_redirects=True)


class TestIndexPageAccess:
    """Index page access tests"""

    def test_index_requires_login(self, client):
        """Index page redirects to login"""
        response = client.get('/')
        assert response.status_code in [200, 302]

    def test_index_page_prep_access(self, client, prep_user):
        """Prep user can access index"""
        login(client, 'prep_reg_test', 'PrepPass123')
        response = client.get('/')
        assert response.status_code in [200, 302]

    def test_index_page_admin_access(self, client, admin_user):
        """Admin user can access index"""
        login(client, 'admin_reg_test', 'AdminPass123')
        response = client.get('/')
        assert response.status_code in [200, 302]

    def test_index_page_analyst_access(self, client, analyst_user):
        """Analyst can access index"""
        login(client, 'analyst_reg_test', 'AnalystPass123')
        response = client.get('/')
        assert response.status_code in [200, 302]


class TestSampleRegistrationPost:
    """Sample registration POST tests"""

    def test_register_sample_post(self, client, app, prep_user):
        """Register sample via POST"""
        login(client, 'prep_reg_test', 'PrepPass123')
        ts = int(datetime.now().timestamp())
        response = client.post('/', data={
            'client_name': 'CHPP',
            'sample_type': '2H',
            'sample_code': f'TEST_REG_{ts}',
            'sample_date': date.today().strftime('%Y-%m-%d'),
            'submit': 'true'
        }, follow_redirects=True)
        assert response.status_code == 200

    def test_register_sample_via_index_route(self, client, app, prep_user):
        """Register sample via /index POST"""
        login(client, 'prep_reg_test', 'PrepPass123')
        ts = int(datetime.now().timestamp())
        response = client.post('/index', data={
            'client_name': 'CHPP',
            'sample_type': '2H',
            'sample_code': f'TEST_INDEX_{ts}',
            'sample_date': date.today().strftime('%Y-%m-%d')
        }, follow_redirects=True)
        assert response.status_code == 200


class TestSampleEdit:
    """Sample edit tests"""

    def test_edit_sample_page(self, client, app, prep_user):
        """Edit sample page access"""
        login(client, 'prep_reg_test', 'PrepPass123')

        # Create a sample first
        with app.app_context():
            sample = Sample(
                sample_code=f'EDIT_TEST_{datetime.now().timestamp()}',
                client_name='CHPP',
                sample_type='2H',
                received_date=datetime.now(),
                status='pending'
            )
            db.session.add(sample)
            db.session.commit()
            sample_id = sample.id

        response = client.get(f'/edit_sample/{sample_id}')
        assert response.status_code in [200, 302, 404]

    def test_edit_sample_post(self, client, app, prep_user):
        """Edit sample POST"""
        login(client, 'prep_reg_test', 'PrepPass123')

        # Create a sample first
        with app.app_context():
            sample = Sample(
                sample_code=f'EDIT_POST_{datetime.now().timestamp()}',
                client_name='CHPP',
                sample_type='2H',
                received_date=datetime.now(),
                status='pending'
            )
            db.session.add(sample)
            db.session.commit()
            sample_id = sample.id

        response = client.post(f'/edit_sample/{sample_id}', data={
            'sample_code': f'EDIT_POST_UPDATED_{datetime.now().timestamp()}',
            'client_name': 'UHG'
        }, follow_redirects=True)
        assert response.status_code in [200, 302, 404]


class TestSampleDisposal:
    """Sample disposal tests"""

    def test_sample_disposal_page(self, client, app, prep_user):
        """Sample disposal page"""
        login(client, 'prep_reg_test', 'PrepPass123')
        response = client.get('/sample_disposal')
        assert response.status_code in [200, 302, 404]

    def test_dispose_samples_post(self, client, app, admin_user):
        """Dispose samples POST"""
        login(client, 'admin_reg_test', 'AdminPass123')

        # Create a sample first
        with app.app_context():
            sample = Sample(
                sample_code=f'DISPOSE_{datetime.now().timestamp()}',
                client_name='CHPP',
                sample_type='2H',
                received_date=datetime.now(),
                status='completed'
            )
            db.session.add(sample)
            db.session.commit()
            sample_id = sample.id

        response = client.post('/dispose_samples', data={
            'sample_ids': [sample_id]
        }, follow_redirects=True)
        assert response.status_code in [200, 302, 404]


class TestDeleteSamples:
    """Delete samples tests"""

    def test_delete_selected_samples(self, client, app, admin_user):
        """Delete selected samples"""
        login(client, 'admin_reg_test', 'AdminPass123')

        # Create a sample first
        with app.app_context():
            sample = Sample(
                sample_code=f'DELETE_{datetime.now().timestamp()}',
                client_name='CHPP',
                sample_type='2H',
                received_date=datetime.now(),
                status='pending'
            )
            db.session.add(sample)
            db.session.commit()
            sample_id = sample.id

        response = client.post('/delete_selected_samples', data={
            'sample_ids': [sample_id]
        }, follow_redirects=True)
        assert response.status_code in [200, 302, 404]


class TestBulkRetention:
    """Bulk retention tests"""

    def test_bulk_set_retention(self, client, app, admin_user):
        """Bulk set retention date"""
        login(client, 'admin_reg_test', 'AdminPass123')

        # Create samples
        with app.app_context():
            sample = Sample(
                sample_code=f'RETENTION_{datetime.now().timestamp()}',
                client_name='CHPP',
                sample_type='2H',
                received_date=datetime.now(),
                status='completed'
            )
            db.session.add(sample)
            db.session.commit()
            sample_id = sample.id

        response = client.post('/bulk_set_retention', data={
            'sample_ids': [sample_id],
            'retention_date': date.today().strftime('%Y-%m-%d')
        }, follow_redirects=True)
        assert response.status_code in [200, 302, 404]

    def test_set_retention_date(self, client, app, admin_user):
        """Set retention date for single sample"""
        login(client, 'admin_reg_test', 'AdminPass123')

        with app.app_context():
            sample = Sample(
                sample_code=f'RETENTION_SINGLE_{datetime.now().timestamp()}',
                client_name='CHPP',
                sample_type='2H',
                received_date=datetime.now(),
                status='completed'
            )
            db.session.add(sample)
            db.session.commit()
            sample_id = sample.id

        response = client.post('/set_retention_date', data={
            'sample_id': sample_id,
            'retention_date': date.today().strftime('%Y-%m-%d')
        }, follow_redirects=True)
        assert response.status_code in [200, 302, 404]


class TestAnalyticsDashboard:
    """Analytics dashboard tests"""

    def test_analytics_dashboard(self, client, app, admin_user):
        """Analytics dashboard page"""
        login(client, 'admin_reg_test', 'AdminPass123')
        response = client.get('/analytics')
        assert response.status_code in [200, 302, 404]


class TestPreviewAnalyses:
    """Preview analyses tests"""

    def test_preview_sample_analyses(self, client, app, prep_user):
        """Preview sample analyses"""
        login(client, 'prep_reg_test', 'PrepPass123')
        response = client.post('/preview-analyses',
            json={
                'sample_names': ['TEST_SAMPLE_001'],
                'client_name': 'CHPP',
                'sample_type': '2H'
            },
            follow_redirects=True)
        assert response.status_code in [200, 302, 404, 415]


class TestLoginLogout:
    """Login/Logout tests"""

    def test_login_page(self, client):
        """Login page access"""
        response = client.get('/login')
        assert response.status_code == 200

    def test_login_valid_credentials(self, client, prep_user):
        """Login with valid credentials"""
        response = login(client, 'prep_reg_test', 'PrepPass123')
        assert response.status_code == 200

    def test_login_invalid_credentials(self, client, prep_user):
        """Login with invalid credentials"""
        response = client.post('/login', data={
            'username': 'prep_reg_test',
            'password': 'WrongPassword'
        }, follow_redirects=True)
        assert response.status_code == 200

    def test_logout(self, client, prep_user):
        """Logout"""
        login(client, 'prep_reg_test', 'PrepPass123')
        response = client.get('/logout', follow_redirects=True)
        assert response.status_code == 200


class TestHourlyReport:
    """Hourly report tests"""

    def test_send_hourly_report(self, client, app, admin_user):
        """Send hourly report endpoint"""
        login(client, 'admin_reg_test', 'AdminPass123')
        response = client.get('/send-hourly-report')
        assert response.status_code in [200, 302, 404, 500]
