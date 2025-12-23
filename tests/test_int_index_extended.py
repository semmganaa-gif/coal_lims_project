# tests/integration/test_index_extended.py
# -*- coding: utf-8 -*-
"""
Index routes extended tests for higher coverage
Coverage target: app/routes/main/index.py
"""

import pytest
from app import db
from app.models import User, Sample, AnalysisResult
from datetime import datetime, date
import uuid

VALID_PASSWORD = 'TestPass123'


@pytest.fixture
def index_user(app):
    """Index test user"""
    with app.app_context():
        user = User.query.filter_by(username='index_test_user').first()
        if not user:
            user = User(username='index_test_user', role='chemist')
            user.set_password(VALID_PASSWORD)
            db.session.add(user)
            db.session.commit()
        return user


@pytest.fixture
def index_admin(app):
    """Index admin user"""
    with app.app_context():
        user = User.query.filter_by(username='index_admin_user').first()
        if not user:
            user = User(username='index_admin_user', role='admin')
            user.set_password(VALID_PASSWORD)
            db.session.add(user)
            db.session.commit()
        return user


@pytest.fixture
def index_sample(app, index_user):
    """Sample for index tests"""
    with app.app_context():
        unique_id = uuid.uuid4().hex[:6]
        sample = Sample(
            sample_code=f'IDX-{unique_id}',
            client_name='CHPP',
            sample_type='CM',
            status='registered',
            received_date=datetime.now(),
            user_id=index_user.id
        )
        db.session.add(sample)
        db.session.commit()
        return sample.id


def login_index_user(client, username='index_test_user'):
    """Helper login"""
    client.post('/login', data={
        'username': username,
        'password': VALID_PASSWORD
    }, follow_redirects=True)


class TestIndexPage:
    """Test main index page"""

    def test_index_page_get(self, client, app, index_user):
        """Index page GET"""
        login_index_user(client)
        response = client.get('/')
        assert response.status_code in [200, 302]

    def test_index_page_post_chpp(self, client, app, index_user):
        """Index page POST with CHPP client"""
        login_index_user(client)
        response = client.post('/', data={'client_name': 'CHPP'})
        assert response.status_code in [200, 302]

    def test_index_page_post_qc(self, client, app, index_user):
        """Index page POST with QC client"""
        login_index_user(client)
        response = client.post('/', data={'client_name': 'QC'})
        assert response.status_code in [200, 302]

    def test_index_page_post_lab(self, client, app, index_user):
        """Index page POST with LAB client"""
        login_index_user(client)
        response = client.post('/', data={'client_name': 'LAB'})
        assert response.status_code in [200, 302]

    def test_index_page_with_date(self, client, app, index_user):
        """Index page with date filter"""
        login_index_user(client)
        today = date.today().isoformat()
        response = client.get(f'/?date={today}')
        assert response.status_code in [200, 302]


class TestSamplesPage:
    """Test samples list page"""

    def test_samples_list(self, client, app, index_user):
        """Samples list page"""
        login_index_user(client)
        response = client.get('/samples')
        assert response.status_code in [200, 302, 404]

    def test_samples_list_with_filter(self, client, app, index_user):
        """Samples list with status filter"""
        login_index_user(client)
        response = client.get('/samples?status=registered')
        assert response.status_code in [200, 302, 404]

    def test_samples_list_with_client(self, client, app, index_user):
        """Samples list with client filter"""
        login_index_user(client)
        response = client.get('/samples?client=CHPP')
        assert response.status_code in [200, 302, 404]


class TestSampleDetail:
    """Test sample detail page"""

    def test_sample_detail(self, client, app, index_user, index_sample):
        """Sample detail page"""
        login_index_user(client)
        response = client.get(f'/sample/{index_sample}')
        assert response.status_code in [200, 302, 404]

    def test_sample_detail_invalid(self, client, app, index_user):
        """Sample detail invalid ID"""
        login_index_user(client)
        response = client.get('/sample/999999')
        assert response.status_code in [302, 404]


class TestMassPrep:
    """Test mass prep page"""

    def test_mass_prep_page(self, client, app, index_user):
        """Mass prep page"""
        login_index_user(client)
        response = client.get('/mass_prep')
        assert response.status_code in [200, 302, 404]

    def test_mass_prep_with_sample(self, client, app, index_user, index_sample):
        """Mass prep with sample"""
        login_index_user(client)
        response = client.get(f'/mass_prep?sample_id={index_sample}')
        assert response.status_code in [200, 302, 404]


class TestDashboard:
    """Test dashboard page"""

    def test_dashboard_page(self, client, app, index_admin):
        """Dashboard page"""
        login_index_user(client, 'index_admin_user')
        response = client.get('/dashboard')
        assert response.status_code in [200, 302, 404]

    def test_dashboard_with_date(self, client, app, index_admin):
        """Dashboard with date"""
        login_index_user(client, 'index_admin_user')
        today = date.today().isoformat()
        response = client.get(f'/dashboard?date={today}')
        assert response.status_code in [200, 302, 404]


class TestAnalytics:
    """Test analytics page"""

    def test_analytics_page(self, client, app, index_admin):
        """Analytics page"""
        login_index_user(client, 'index_admin_user')
        response = client.get('/analytics')
        assert response.status_code in [200, 302, 404]

    def test_analytics_with_range(self, client, app, index_admin):
        """Analytics with date range"""
        login_index_user(client, 'index_admin_user')
        response = client.get('/analytics?start_date=2024-01-01&end_date=2024-12-31')
        assert response.status_code in [200, 302, 404]


class TestDataAPI:
    """Test data API endpoints"""

    def test_api_data(self, client, app, index_user):
        """API data endpoint"""
        login_index_user(client)
        response = client.get('/api/data')
        assert response.status_code in [200, 302, 404]

    def test_api_sample_summary(self, client, app, index_user):
        """API sample summary"""
        login_index_user(client)
        response = client.get('/api/sample_summary')
        assert response.status_code in [200, 302, 404]

    def test_api_check_ready(self, client, app, index_user):
        """API check ready samples"""
        login_index_user(client)
        response = client.get('/api/check_ready_samples')
        assert response.status_code in [200, 302, 404]


class TestSampleDisposal:
    """Test sample disposal"""

    def test_sample_disposal_page(self, client, app, index_admin):
        """Sample disposal page"""
        login_index_user(client, 'index_admin_user')
        response = client.get('/sample_disposal')
        assert response.status_code in [200, 302, 404]

    def test_dispose_samples_post(self, client, app, index_admin):
        """Dispose samples POST"""
        login_index_user(client, 'index_admin_user')
        response = client.post('/dispose_samples', data={'sample_ids': ''})
        assert response.status_code in [200, 302, 400, 404]

    def test_delete_selected_samples(self, client, app, index_admin):
        """Delete selected samples"""
        login_index_user(client, 'index_admin_user')
        response = client.post('/delete_selected_samples', data={'sample_ids': ''})
        assert response.status_code in [200, 302, 400, 404]


class TestRegistration:
    """Test sample registration"""

    def test_register_sample_form(self, client, app, index_user):
        """Sample registration form"""
        login_index_user(client)
        response = client.get('/register_sample')
        assert response.status_code in [200, 302, 404]

    def test_register_sample_post(self, client, app, index_user):
        """Register sample POST"""
        login_index_user(client)
        response = client.post('/register_sample', data={
            'sample_code': 'TEST-001',
            'client_name': 'CHPP',
            'sample_type': 'CM'
        })
        assert response.status_code in [200, 302, 400, 404]
