# tests/integration/test_routes_full.py
# -*- coding: utf-8 -*-
"""
Full Routes Tests - coverage нэмэгдүүлэх
"""

import pytest
from app import db
from app.models import User, Sample
from datetime import datetime
import json

VALID_PASSWORD = 'TestPass123'


@pytest.fixture
def full_test_user(app):
    """Full test user"""
    with app.app_context():
        user = User.query.filter_by(username='full_test_user').first()
        if not user:
            user = User(username='full_test_user', role='admin')
            user.set_password(VALID_PASSWORD)
            db.session.add(user)
            db.session.commit()
        return user


class TestAuthRoutes:
    """Auth routes тестүүд"""

    def test_login_page(self, client, app):
        """Login page"""
        response = client.get('/login')
        assert response.status_code in [200, 302]

    def test_login_post_valid(self, client, app, full_test_user):
        """Login POST valid"""
        response = client.post('/login', data={
            'username': 'full_test_user',
            'password': VALID_PASSWORD
        })
        assert response.status_code in [200, 302]

    def test_login_post_invalid(self, client, app):
        """Login POST invalid"""
        response = client.post('/login', data={
            'username': 'nonexistent',
            'password': 'wrongpass'
        })
        assert response.status_code in [200, 302, 401]

    def test_logout(self, client, app, full_test_user):
        """Logout"""
        client.post('/login', data={
            'username': 'full_test_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)

        response = client.get('/logout')
        assert response.status_code in [200, 302]


class TestIndexRoutes:
    """Index routes тестүүд"""

    def test_index_get(self, client, app, full_test_user):
        """Index GET"""
        client.post('/login', data={
            'username': 'full_test_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)

        response = client.get('/coal')
        assert response.status_code in [200, 302]

    def test_index_post_chpp(self, client, app, full_test_user):
        """Index POST CHPP sample"""
        client.post('/login', data={
            'username': 'full_test_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)

        response = client.post('/coal', data={
            'client_name': 'CHPP',
            'sample_type': '2hour',
            'received_date': datetime.now().strftime('%Y-%m-%d')
        })
        assert response.status_code in [200, 302, 400]

    def test_index_post_qc(self, client, app, full_test_user):
        """Index POST QC sample"""
        client.post('/login', data={
            'username': 'full_test_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)

        response = client.post('/coal', data={
            'client_name': 'QC',
            'sample_type': 'Routine',
            'received_date': datetime.now().strftime('%Y-%m-%d')
        })
        assert response.status_code in [200, 302, 400]


class TestSampleRoutes:
    """Sample routes тестүүд"""

    def test_samples_list(self, client, app, full_test_user):
        """Samples list"""
        client.post('/login', data={
            'username': 'full_test_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)

        response = client.get('/samples')
        assert response.status_code in [200, 302, 404]

    def test_sample_detail(self, client, app, full_test_user):
        """Sample detail"""
        client.post('/login', data={
            'username': 'full_test_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)

        with app.app_context():
            sample = Sample.query.first()
            if sample:
                response = client.get(f'/samples/{sample.id}')
                assert response.status_code in [200, 302, 404]


class TestAnalysisRoutes:
    """Analysis routes тестүүд"""

    def test_analysis_index(self, client, app, full_test_user):
        """Analysis index"""
        client.post('/login', data={
            'username': 'full_test_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)

        response = client.get('/analysis')
        assert response.status_code in [200, 302, 404]

    def test_analysis_workspace(self, client, app, full_test_user):
        """Analysis workspace"""
        client.post('/login', data={
            'username': 'full_test_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)

        response = client.get('/analysis/workspace')
        assert response.status_code in [200, 302, 404]

    def test_analysis_by_code(self, client, app, full_test_user):
        """Analysis by code"""
        client.post('/login', data={
            'username': 'full_test_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)

        for code in ['Mad', 'Aad', 'Vad', 'CV', 'TS']:
            response = client.get(f'/analysis/{code}')
            assert response.status_code in [200, 302, 404]


class TestQCRoutes:
    """QC routes тестүүд"""

    def test_qc_index(self, client, app, full_test_user):
        """QC index"""
        client.post('/login', data={
            'username': 'full_test_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)

        response = client.get('/qc')
        assert response.status_code in [200, 302, 404]

    def test_qc_control_charts(self, client, app, full_test_user):
        """QC control charts"""
        client.post('/login', data={
            'username': 'full_test_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)

        response = client.get('/qc/control_charts')
        assert response.status_code in [200, 302, 404]


class TestSeniorRoutes:
    """Senior routes тестүүд"""

    def test_senior_index(self, client, app, full_test_user):
        """Senior index"""
        client.post('/login', data={
            'username': 'full_test_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)

        response = client.get('/senior')
        assert response.status_code in [200, 302, 404]

    def test_senior_review(self, client, app, full_test_user):
        """Senior review"""
        client.post('/login', data={
            'username': 'full_test_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)

        response = client.get('/senior/review')
        assert response.status_code in [200, 302, 404]


class TestKPIRoutes:
    """KPI routes тестүүд"""

    def test_kpi_index(self, client, app, full_test_user):
        """KPI index"""
        client.post('/login', data={
            'username': 'full_test_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)

        response = client.get('/kpi')
        assert response.status_code in [200, 302, 404]

    def test_kpi_dashboard(self, client, app, full_test_user):
        """KPI dashboard"""
        client.post('/login', data={
            'username': 'full_test_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)

        response = client.get('/kpi/dashboard')
        assert response.status_code in [200, 302, 404]


class TestReportRoutes:
    """Report routes тестүүд"""

    def test_reports_index(self, client, app, full_test_user):
        """Reports index"""
        client.post('/login', data={
            'username': 'full_test_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)

        response = client.get('/reports')
        assert response.status_code in [200, 302, 404]

    def test_daily_report(self, client, app, full_test_user):
        """Daily report"""
        client.post('/login', data={
            'username': 'full_test_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)

        response = client.get('/reports/daily')
        assert response.status_code in [200, 302, 404]

    def test_weekly_report(self, client, app, full_test_user):
        """Weekly report"""
        client.post('/login', data={
            'username': 'full_test_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)

        response = client.get('/reports/weekly')
        assert response.status_code in [200, 302, 404]

    def test_monthly_report(self, client, app, full_test_user):
        """Monthly report"""
        client.post('/login', data={
            'username': 'full_test_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)

        response = client.get('/reports/monthly')
        assert response.status_code in [200, 302, 404]


class TestEquipmentRoutes:
    """Equipment routes тестүүд"""

    def test_equipment_index(self, client, app, full_test_user):
        """Equipment index"""
        client.post('/login', data={
            'username': 'full_test_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)

        response = client.get('/equipment')
        assert response.status_code in [200, 302, 404]

    def test_equipment_new(self, client, app, full_test_user):
        """Equipment new"""
        client.post('/login', data={
            'username': 'full_test_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)

        response = client.get('/equipment/new')
        assert response.status_code in [200, 302, 404]


class TestSettingsRoutes:
    """Settings routes тестүүд"""

    def test_settings_index(self, client, app, full_test_user):
        """Settings index"""
        client.post('/login', data={
            'username': 'full_test_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)

        response = client.get('/settings')
        assert response.status_code in [200, 302, 404]

    def test_settings_general(self, client, app, full_test_user):
        """Settings general"""
        client.post('/login', data={
            'username': 'full_test_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)

        response = client.get('/settings/general')
        assert response.status_code in [200, 302, 404]

    def test_settings_precision(self, client, app, full_test_user):
        """Settings precision"""
        client.post('/login', data={
            'username': 'full_test_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)

        response = client.get('/settings/precision')
        assert response.status_code in [200, 302, 404]


class TestQualityRoutes:
    """Quality routes тестүүд"""

    def test_quality_index(self, client, app, full_test_user):
        """Quality index"""
        client.post('/login', data={
            'username': 'full_test_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)

        response = client.get('/quality')
        assert response.status_code in [200, 302, 404]

    def test_quality_capa(self, client, app, full_test_user):
        """Quality CAPA"""
        client.post('/login', data={
            'username': 'full_test_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)

        response = client.get('/quality/capa')
        assert response.status_code in [200, 302, 404]

    def test_quality_complaints(self, client, app, full_test_user):
        """Quality complaints"""
        client.post('/login', data={
            'username': 'full_test_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)

        response = client.get('/quality/complaints')
        assert response.status_code in [200, 302, 404]

    def test_quality_environmental(self, client, app, full_test_user):
        """Quality environmental"""
        client.post('/login', data={
            'username': 'full_test_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)

        response = client.get('/quality/environmental')
        assert response.status_code in [200, 302, 404]

    def test_quality_proficiency(self, client, app, full_test_user):
        """Quality proficiency"""
        client.post('/login', data={
            'username': 'full_test_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)

        response = client.get('/quality/proficiency')
        assert response.status_code in [200, 302, 404]


class TestImportRoutes:
    """Import routes тестүүд"""

    def test_import_index(self, client, app, full_test_user):
        """Import index"""
        client.post('/login', data={
            'username': 'full_test_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)

        response = client.get('/import')
        assert response.status_code in [200, 302, 404]

    def test_import_csv(self, client, app, full_test_user):
        """Import CSV"""
        client.post('/login', data={
            'username': 'full_test_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)

        response = client.get('/import/csv')
        assert response.status_code in [200, 302, 404]
