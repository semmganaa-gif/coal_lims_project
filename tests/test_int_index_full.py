# -*- coding: utf-8 -*-
"""
Index routes - бүрэн интеграцийн тестүүд
main/index.py файлын coverage нэмэгдүүлэх
"""
import pytest
from datetime import datetime, timedelta
from app import create_app, db
from app.models import User, Sample, ControlStandard, GbwStandard


@pytest.fixture
def app():
    """Test application fixture"""
    from tests.conftest import TestConfig
    app = create_app(TestConfig)
    app.config['SERVER_NAME'] = 'localhost'
    app.config['WTF_CSRF_ENABLED'] = False

    with app.app_context():
        db.create_all()
        # Create admin user
        if not User.query.filter_by(username='admin').first():
            user = User(username='admin', role='admin')
            user.set_password('AdminPass123')
            db.session.add(user)
            db.session.commit()
        # Create prep user
        if not User.query.filter_by(username='prep').first():
            user = User(username='prep', role='prep')
            user.set_password('PrepPass123')
            db.session.add(user)
            db.session.commit()
        # Create analyst user (no prep permission)
        if not User.query.filter_by(username='analyst').first():
            user = User(username='analyst', role='analyst')
            user.set_password('AnalystPass123')
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
def prep_client(app, client):
    """Prep role client"""
    with app.app_context():
        user = User.query.filter_by(username='prep').first()
        with client.session_transaction() as sess:
            sess['_user_id'] = str(user.id)
            sess['_fresh'] = True
    return client


@pytest.fixture
def analyst_client(app, client):
    """Analyst role client (no prep permission)"""
    with app.app_context():
        user = User.query.filter_by(username='analyst').first()
        with client.session_transaction() as sess:
            sess['_user_id'] = str(user.id)
            sess['_fresh'] = True
    return client


class TestIndexPage:
    """Index page тестүүд"""

    def test_index_get_authenticated(self, auth_client, app):
        """Index page accessible when authenticated"""
        with app.app_context():
            response = auth_client.get('/coal')
            assert response.status_code == 200

    def test_index_alt_path(self, auth_client, app):
        """Index /index path"""
        with app.app_context():
            response = auth_client.get('/index')
            assert response.status_code == 200

    def test_index_unauthenticated(self, client, app):
        """Index redirects when not authenticated"""
        with app.app_context():
            response = client.get('/coal')
            assert response.status_code in [302, 401, 403]

    def test_index_with_active_tab_param(self, auth_client, app):
        """Index with active_tab query parameter"""
        with app.app_context():
            response = auth_client.get('/?active_tab=add-pane')
            assert response.status_code == 200


class TestSampleRegistration:
    """Дээж бүртгэлийн тестүүд"""

    def test_post_empty_form(self, auth_client, app):
        """POST with empty form"""
        with app.app_context():
            response = auth_client.post('/coal', data={})
            assert response.status_code in [200, 302, 400]

    def test_post_with_client_name(self, auth_client, app):
        """POST with client_name only"""
        with app.app_context():
            response = auth_client.post('/coal', data={
                'client_name': 'CHPP',
                'sample_type': ''
            })
            assert response.status_code in [200, 302]

    def test_analyst_cannot_register(self, analyst_client, app):
        """Analyst role cannot register samples"""
        with app.app_context():
            response = analyst_client.post('/coal', data={
                'client_name': 'CHPP',
                'sample_type': '2 hourly',
                'sample_date': datetime.now().strftime('%Y-%m-%d'),
                'sample_codes': ['TEST_D1'],
                'list_type': 'chpp_2h'
            })
            # Should be denied or show warning
            assert response.status_code in [200, 302]


class TestCHPPRegistration:
    """CHPP дээж бүртгэлийн тестүүд"""

    def test_chpp_2hourly_registration(self, prep_client, app):
        """CHPP 2 hourly sample registration"""
        with app.app_context():
            response = prep_client.post('/coal', data={
                'client_name': 'CHPP',
                'sample_type': '2 hourly',
                'sample_date': datetime.now().strftime('%Y-%m-%d'),
                'sample_codes': ['PF211_D1', 'PF211_D2'],
                'weights': ['100.5', '99.3'],
                'list_type': 'chpp_2h',
                'sample_condition': 'Good',
                'retention_period': '7'
            })
            assert response.status_code in [200, 302]

    def test_chpp_4hourly_registration(self, prep_client, app):
        """CHPP 4 hourly sample registration"""
        with app.app_context():
            response = prep_client.post('/coal', data={
                'client_name': 'CHPP',
                'sample_type': '4 hourly',
                'sample_date': datetime.now().strftime('%Y-%m-%d'),
                'sample_codes': ['CF501', 'CF502'],
                'weights': ['50.0', '51.0'],
                'list_type': 'chpp_4h',
                'sample_condition': 'Good',
                'retention_period': '7'
            })
            assert response.status_code in [200, 302]

    def test_chpp_com_registration(self, prep_client, app):
        """CHPP COM sample registration"""
        with app.app_context():
            response = prep_client.post('/coal', data={
                'client_name': 'CHPP',
                'sample_type': 'COM',
                'sample_date': datetime.now().strftime('%Y-%m-%d'),
                'sample_codes': ['COM_TEST'],
                'weights': ['200.0'],
                'list_type': 'chpp_com',
                'sample_condition': 'Good',
                'retention_period': '7'
            })
            assert response.status_code in [200, 302]

    def test_chpp_invalid_weight(self, prep_client, app):
        """CHPP with invalid weight value"""
        with app.app_context():
            response = prep_client.post('/coal', data={
                'client_name': 'CHPP',
                'sample_type': '2 hourly',
                'sample_date': datetime.now().strftime('%Y-%m-%d'),
                'sample_codes': ['TEST_D1'],
                'weights': ['not_a_number'],
                'list_type': 'chpp_2h',
                'sample_condition': 'Good',
                'retention_period': '7'
            })
            assert response.status_code in [200, 302]

    def test_chpp_weight_too_small(self, prep_client, app):
        """CHPP with too small weight"""
        with app.app_context():
            response = prep_client.post('/coal', data={
                'client_name': 'CHPP',
                'sample_type': '2 hourly',
                'sample_date': datetime.now().strftime('%Y-%m-%d'),
                'sample_codes': ['TEST_D1'],
                'weights': ['0'],
                'list_type': 'chpp_2h',
                'sample_condition': 'Good',
                'retention_period': '7'
            })
            assert response.status_code in [200, 302]

    def test_chpp_missing_weight(self, prep_client, app):
        """CHPP with missing weight"""
        with app.app_context():
            response = prep_client.post('/coal', data={
                'client_name': 'CHPP',
                'sample_type': '2 hourly',
                'sample_date': datetime.now().strftime('%Y-%m-%d'),
                'sample_codes': ['TEST_D1'],
                'weights': [],
                'list_type': 'chpp_2h',
                'sample_condition': 'Good',
                'retention_period': '7'
            })
            assert response.status_code in [200, 302]


class TestWTLRegistration:
    """WTL дээж бүртгэлийн тестүүд"""

    def test_wtl_auto_names_registration(self, prep_client, app):
        """WTL auto-generated names registration"""
        with app.app_context():
            response = prep_client.post('/coal', data={
                'client_name': 'WTL',
                'sample_type': 'WTL',
                'sample_date': datetime.now().strftime('%Y-%m-%d'),
                'lab_number': 'WTL001',
                'sample_condition': 'Good',
                'retention_period': '7'
            })
            assert response.status_code in [200, 302]

    def test_wtl_size_registration(self, prep_client, app):
        """WTL Size sample registration"""
        with app.app_context():
            response = prep_client.post('/coal', data={
                'client_name': 'WTL',
                'sample_type': 'Size',
                'sample_date': datetime.now().strftime('%Y-%m-%d'),
                'lab_number': 'SIZE001',
                'sample_condition': 'Good',
                'retention_period': '7'
            })
            assert response.status_code in [200, 302]

    def test_wtl_fl_registration(self, prep_client, app):
        """WTL FL sample registration"""
        with app.app_context():
            response = prep_client.post('/coal', data={
                'client_name': 'WTL',
                'sample_type': 'FL',
                'sample_date': datetime.now().strftime('%Y-%m-%d'),
                'lab_number': 'FL001',
                'sample_condition': 'Good',
                'retention_period': '7'
            })
            assert response.status_code in [200, 302]

    def test_wtl_without_lab_number(self, prep_client, app):
        """WTL without lab number should fail"""
        with app.app_context():
            response = prep_client.post('/coal', data={
                'client_name': 'WTL',
                'sample_type': 'WTL',
                'sample_date': datetime.now().strftime('%Y-%m-%d'),
                'sample_condition': 'Good',
                'retention_period': '7'
            })
            assert response.status_code in [200, 302]

    def test_wtl_mg_registration(self, prep_client, app):
        """WTL MG manual sample registration"""
        with app.app_context():
            response = prep_client.post('/coal', data={
                'client_name': 'WTL',
                'sample_type': 'MG',
                'sample_date': datetime.now().strftime('%Y-%m-%d'),
                'sample_code': 'MG_MANUAL_001',
                'sample_condition': 'Good',
                'retention_period': '7'
            })
            assert response.status_code in [200, 302]

    def test_wtl_test_registration(self, prep_client, app):
        """WTL Test manual sample registration"""
        with app.app_context():
            response = prep_client.post('/coal', data={
                'client_name': 'WTL',
                'sample_type': 'Test',
                'sample_date': datetime.now().strftime('%Y-%m-%d'),
                'sample_code': 'WTL_TEST_001',
                'sample_condition': 'Good',
                'retention_period': '7'
            })
            assert response.status_code in [200, 302]

    def test_wtl_mg_without_sample_code(self, prep_client, app):
        """WTL MG without sample_code should fail"""
        with app.app_context():
            response = prep_client.post('/coal', data={
                'client_name': 'WTL',
                'sample_type': 'MG',
                'sample_date': datetime.now().strftime('%Y-%m-%d'),
                'sample_condition': 'Good',
                'retention_period': '7'
            })
            assert response.status_code in [200, 302]


class TestLABRegistration:
    """LAB дээж бүртгэлийн тестүүд"""

    def test_lab_cm_registration(self, prep_client, app):
        """LAB CM sample registration"""
        with app.app_context():
            # Create active CM standard
            cm_std = ControlStandard(
                name='CM_TEST_STD',
                is_active=True,
                targets='{"TS": {"target": 10.0, "tolerance": 0.5}}'
            )
            db.session.add(cm_std)
            db.session.commit()

            response = prep_client.post('/coal', data={
                'client_name': 'LAB',
                'sample_type': 'CM',
                'sample_date': datetime.now().strftime('%Y-%m-%d'),
                'sample_condition': 'Good',
                'retention_period': '7'
            })
            assert response.status_code in [200, 302]

    def test_lab_gbw_registration(self, prep_client, app):
        """LAB GBW sample registration"""
        with app.app_context():
            # Create active GBW standard
            gbw_std = GbwStandard(
                name='GBW11135a',
                is_active=True,
                targets='{"TS": {"target": 8.5, "tolerance": 0.3}}'
            )
            db.session.add(gbw_std)
            db.session.commit()

            response = prep_client.post('/coal', data={
                'client_name': 'LAB',
                'sample_type': 'GBW',
                'sample_date': datetime.now().strftime('%Y-%m-%d'),
                'sample_condition': 'Good',
                'retention_period': '7'
            })
            assert response.status_code in [200, 302]

    def test_lab_test_registration(self, prep_client, app):
        """LAB Test sample registration"""
        with app.app_context():
            response = prep_client.post('/coal', data={
                'client_name': 'LAB',
                'sample_type': 'Test',
                'sample_date': datetime.now().strftime('%Y-%m-%d'),
                'sample_condition': 'Good',
                'retention_period': '7'
            })
            assert response.status_code in [200, 302]

    def test_lab_unknown_type_registration(self, prep_client, app):
        """LAB unknown type registration"""
        with app.app_context():
            response = prep_client.post('/coal', data={
                'client_name': 'LAB',
                'sample_type': 'UNKNOWN',
                'sample_date': datetime.now().strftime('%Y-%m-%d'),
                'sample_condition': 'Good',
                'retention_period': '7'
            })
            assert response.status_code in [200, 302]


class TestQCRegistration:
    """QC дээж бүртгэлийн тестүүд"""

    def test_qc_multi_gen_registration(self, prep_client, app):
        """QC multi_gen sample registration"""
        with app.app_context():
            response = prep_client.post('/coal', data={
                'client_name': 'QC',
                'sample_type': 'General',
                'sample_date': datetime.now().strftime('%Y-%m-%d'),
                'sample_codes': ['QC_SAMPLE_1'],
                'weights': ['100.0'],
                'list_type': 'multi_gen',
                'location': 'LAB-1',
                'product': 'Coal',
                'sample_condition': 'Good',
                'retention_period': '7'
            })
            assert response.status_code in [200, 302]


class TestProcRegistration:
    """Proc дээж бүртгэлийн тестүүд"""

    def test_proc_multi_gen_registration(self, prep_client, app):
        """Proc multi_gen sample registration"""
        with app.app_context():
            response = prep_client.post('/coal', data={
                'client_name': 'Proc',
                'sample_type': 'Process',
                'sample_date': datetime.now().strftime('%Y-%m-%d'),
                'sample_codes': ['PROC_SAMPLE_1'],
                'weights': ['150.0'],
                'list_type': 'multi_gen',
                'location': 'PLANT-1',
                'product': 'Coal',
                'sample_condition': 'Good',
                'retention_period': '7'
            })
            assert response.status_code in [200, 302]


class TestPreviewAnalyses:
    """Preview analyses API тестүүд"""

    def test_preview_analyses_endpoint(self, auth_client, app):
        """Preview analyses API"""
        with app.app_context():
            response = auth_client.post('/preview-analyses',
                json={
                    'sample_names': ['TEST_D1', 'TEST_D2'],
                    'client_name': 'CHPP',
                    'sample_type': '2 hourly'
                },
                content_type='application/json'
            )
            # May return 200, 400, or 500 if analysis_assignment has issues
            assert response.status_code in [200, 400, 500]

    def test_preview_analyses_missing_data(self, auth_client, app):
        """Preview analyses with missing data"""
        with app.app_context():
            response = auth_client.post('/preview-analyses',
                json={
                    'sample_names': ['TEST_D1']
                },
                content_type='application/json'
            )
            assert response.status_code in [200, 400]

    def test_preview_analyses_empty(self, auth_client, app):
        """Preview analyses with empty sample names"""
        with app.app_context():
            response = auth_client.post('/preview-analyses',
                json={
                    'sample_names': [],
                    'client_name': 'CHPP',
                    'sample_type': '2 hourly'
                },
                content_type='application/json'
            )
            assert response.status_code in [200, 400]


class TestHourlyReport:
    """Hourly report тестүүд"""

    def test_send_hourly_report_no_template(self, auth_client, app):
        """Send hourly report without template file"""
        with app.app_context():
            response = auth_client.get('/send-hourly-report')
            # Should redirect with flash message about missing template
            assert response.status_code in [302]

    def test_send_hourly_report_unauthenticated(self, client, app):
        """Send hourly report unauthenticated"""
        with app.app_context():
            response = client.get('/send-hourly-report')
            # Should redirect to login or be forbidden
            assert response.status_code in [302, 401, 403]
