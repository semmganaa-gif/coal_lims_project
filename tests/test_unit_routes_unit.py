# -*- coding: utf-8 -*-
"""
Routes unit тестүүд (mock ашигласан)
"""
import pytest
from unittest.mock import patch, MagicMock
from app import create_app, db
from app.models import User, Sample, AnalysisResult


# Skip entire module if database not available
pytestmark = pytest.mark.skip(reason="Requires PostgreSQL database connection")


@pytest.fixture
def app():
    """Test application fixture"""
    app = create_app()
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False
    return app


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def auth_client(app, client):
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


class TestIndexRouteUnit:
    """Index route unit тестүүд"""

    def test_index_get_request(self, auth_client, app):
        """Index GET"""
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


class TestAnalysisHubUnit:
    """Analysis hub unit тестүүд"""

    def test_analysis_hub_get(self, auth_client, app):
        """Analysis hub GET"""
        with app.app_context():
            response = auth_client.get('/analysis_hub')
            assert response.status_code in [200, 302]


class TestAnalysisPageUnit:
    """Analysis page unit тестүүд"""

    def test_ts_page(self, auth_client, app):
        """TS page"""
        with app.app_context():
            response = auth_client.get('/analysis_page/TS')
            assert response.status_code in [200, 302]

    def test_cv_page(self, auth_client, app):
        """CV page"""
        with app.app_context():
            response = auth_client.get('/analysis_page/CV')
            assert response.status_code in [200, 302]

    def test_mad_page(self, auth_client, app):
        """Mad page"""
        with app.app_context():
            response = auth_client.get('/analysis_page/Mad')
            assert response.status_code in [200, 302]

    def test_vdaf_page(self, auth_client, app):
        """Vdaf page"""
        with app.app_context():
            response = auth_client.get('/analysis_page/Vdaf')
            assert response.status_code in [200, 302, 404]

    def test_aad_page(self, auth_client, app):
        """Aad page"""
        with app.app_context():
            response = auth_client.get('/analysis_page/Aad')
            assert response.status_code in [200, 302, 404]

    def test_fc_page(self, auth_client, app):
        """FC page"""
        with app.app_context():
            response = auth_client.get('/analysis_page/FC')
            assert response.status_code in [200, 302, 404]

    def test_gcv_page(self, auth_client, app):
        """GCV page"""
        with app.app_context():
            response = auth_client.get('/analysis_page/GCV')
            assert response.status_code in [200, 302, 404]

    def test_ncv_page(self, auth_client, app):
        """NCV page"""
        with app.app_context():
            response = auth_client.get('/analysis_page/NCV')
            assert response.status_code in [200, 302, 404]

    def test_hgi_page(self, auth_client, app):
        """HGI page"""
        with app.app_context():
            response = auth_client.get('/analysis_page/HGI')
            assert response.status_code in [200, 302, 404]

    def test_aft_page(self, auth_client, app):
        """AFT page"""
        with app.app_context():
            response = auth_client.get('/analysis_page/AFT')
            assert response.status_code in [200, 302, 404]


class TestApiEndpointsUnit:
    """API endpoints unit тестүүд"""

    def test_eligible_samples_ts(self, auth_client, app):
        """Eligible samples TS"""
        with app.app_context():
            response = auth_client.get('/api/eligible_samples/TS')
            assert response.status_code in [200, 302]

    def test_eligible_samples_cv(self, auth_client, app):
        """Eligible samples CV"""
        with app.app_context():
            response = auth_client.get('/api/eligible_samples/CV')
            assert response.status_code in [200, 302]

    def test_audit_log_ts(self, auth_client, app):
        """Audit log TS"""
        with app.app_context():
            response = auth_client.get('/api/audit_log/TS')
            assert response.status_code in [200, 302]

    def test_check_ready_samples(self, auth_client, app):
        """Check ready samples"""
        with app.app_context():
            response = auth_client.get('/api/check_ready_samples')
            assert response.status_code in [200, 302, 404]

    def test_dashboard_stats(self, auth_client, app):
        """Dashboard stats"""
        with app.app_context():
            response = auth_client.get('/api/dashboard_stats')
            assert response.status_code in [200, 302, 404]

    def test_data_api(self, auth_client, app):
        """Data API"""
        with app.app_context():
            response = auth_client.get('/api/data')
            assert response.status_code in [200, 302, 404]


class TestExportEndpointsUnit:
    """Export endpoints unit тестүүд"""

    def test_export_samples(self, auth_client, app):
        """Export samples"""
        with app.app_context():
            response = auth_client.get('/api/export/samples')
            assert response.status_code in [200, 302]

    def test_export_analysis(self, auth_client, app):
        """Export analysis"""
        with app.app_context():
            response = auth_client.get('/api/export/analysis')
            assert response.status_code in [200, 302]
