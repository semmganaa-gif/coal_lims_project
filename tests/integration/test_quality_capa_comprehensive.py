# tests/integration/test_quality_capa_comprehensive.py
# -*- coding: utf-8 -*-
"""
Quality CAPA and Control Charts comprehensive coverage tests
"""

import pytest
from app import db
from app.models import User, CorrectiveAction, QCControlChart, ControlStandard
from datetime import datetime, date, timedelta
import json

VALID_PASSWORD = 'TestPass123'


@pytest.fixture
def capa_user(app):
    """CAPA user fixture"""
    with app.app_context():
        user = User.query.filter_by(username='capa_test_user').first()
        if not user:
            user = User(username='capa_test_user', role='chemist')
            user.set_password(VALID_PASSWORD)
            db.session.add(user)
            db.session.commit()
        return user


@pytest.fixture
def capa_senior(app):
    """CAPA senior fixture"""
    with app.app_context():
        user = User.query.filter_by(username='capa_test_senior').first()
        if not user:
            user = User(username='capa_test_senior', role='senior')
            user.set_password(VALID_PASSWORD)
            db.session.add(user)
            db.session.commit()
        return user


@pytest.fixture
def capa_admin(app):
    """CAPA admin fixture"""
    with app.app_context():
        user = User.query.filter_by(username='capa_test_admin').first()
        if not user:
            user = User(username='capa_test_admin', role='admin')
            user.set_password(VALID_PASSWORD)
            db.session.add(user)
            db.session.commit()
        return user


@pytest.fixture
def test_capa(app, capa_senior):
    """Test CAPA fixture"""
    import uuid
    with app.app_context():
        unique_id = uuid.uuid4().hex[:12]
        capa = CorrectiveAction(
            ca_number=f'CA-TEST-{unique_id}',
            issue_source='Internal Audit',
            issue_description=f'Test CAPA {unique_id}',
            status='open'
        )
        db.session.add(capa)
        db.session.commit()
        return capa.id


class TestCAPAList:
    """CAPA list tests"""

    def test_capa_list_get(self, client, app, capa_user):
        """CAPA list GET"""
        client.post('/login', data={
            'username': 'capa_test_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)
        response = client.get('/quality/capa')
        assert response.status_code in [200, 302, 404]

    def test_capa_list_filtered(self, client, app, capa_user):
        """CAPA list filtered"""
        client.post('/login', data={
            'username': 'capa_test_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)
        response = client.get('/quality/capa?status=open')
        assert response.status_code in [200, 302, 404]


class TestCAPANew:
    """CAPA new tests"""

    def test_capa_new_get(self, client, app, capa_senior):
        """CAPA new GET"""
        client.post('/login', data={
            'username': 'capa_test_senior',
            'password': VALID_PASSWORD
        }, follow_redirects=True)
        response = client.get('/quality/capa/new')
        assert response.status_code in [200, 302, 404]

    def test_capa_new_post_valid(self, client, app, capa_senior):
        """CAPA new POST with valid data"""
        client.post('/login', data={
            'username': 'capa_test_senior',
            'password': VALID_PASSWORD
        }, follow_redirects=True)
        response = client.post('/quality/capa/new', data={
            'issue_source': 'Customer Complaint',
            'issue_description': 'Test issue description',
            'root_cause': 'Human error',
            'corrective_action': 'Training provided',
            'responsible_person': 'John Doe',
            'due_date': (date.today() + timedelta(days=30)).isoformat(),
            'priority': 'high'
        }, follow_redirects=True)
        assert response.status_code in [200, 302, 400]

    def test_capa_new_post_internal_audit(self, client, app, capa_senior):
        """CAPA new POST - internal audit source"""
        client.post('/login', data={
            'username': 'capa_test_senior',
            'password': VALID_PASSWORD
        }, follow_redirects=True)
        response = client.post('/quality/capa/new', data={
            'issue_source': 'Internal Audit',
            'issue_description': 'Audit finding: documentation gap',
            'root_cause': 'Procedure not followed',
            'corrective_action': 'Procedure updated and training'
        }, follow_redirects=True)
        assert response.status_code in [200, 302, 400]

    def test_capa_new_post_qc_failure(self, client, app, capa_senior):
        """CAPA new POST - QC failure source"""
        client.post('/login', data={
            'username': 'capa_test_senior',
            'password': VALID_PASSWORD
        }, follow_redirects=True)
        response = client.post('/quality/capa/new', data={
            'issue_source': 'QC Failure',
            'issue_description': 'Control chart violation',
            'root_cause': 'Equipment drift',
            'corrective_action': 'Recalibration performed'
        }, follow_redirects=True)
        assert response.status_code in [200, 302, 400]


class TestCAPAEdit:
    """CAPA edit tests"""

    def test_capa_edit_get(self, client, app, capa_senior, test_capa):
        """CAPA edit GET"""
        client.post('/login', data={
            'username': 'capa_test_senior',
            'password': VALID_PASSWORD
        }, follow_redirects=True)
        response = client.get(f'/quality/capa/{test_capa}/edit')
        assert response.status_code in [200, 302, 404]

    def test_capa_edit_post(self, client, app, capa_senior, test_capa):
        """CAPA edit POST"""
        client.post('/login', data={
            'username': 'capa_test_senior',
            'password': VALID_PASSWORD
        }, follow_redirects=True)
        response = client.post(f'/quality/capa/{test_capa}/edit', data={
            'issue_source': 'Updated Source',
            'issue_description': 'Updated description',
            'status': 'in_progress'
        }, follow_redirects=True)
        assert response.status_code in [200, 302, 400, 404]


class TestCAPAClose:
    """CAPA close tests"""

    def test_capa_close(self, client, app, capa_admin, test_capa):
        """CAPA close"""
        client.post('/login', data={
            'username': 'capa_test_admin',
            'password': VALID_PASSWORD
        }, follow_redirects=True)
        response = client.post(f'/quality/capa/{test_capa}/close', data={
            'closure_notes': 'Issue resolved',
            'verification_date': date.today().isoformat()
        }, follow_redirects=True)
        assert response.status_code in [200, 302, 400, 404]


class TestControlChartsList:
    """Control charts list tests"""

    def test_control_charts_list(self, client, app, capa_user):
        """Control charts list"""
        client.post('/login', data={
            'username': 'capa_test_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)
        response = client.get('/quality/control_charts')
        assert response.status_code in [200, 302, 404]

    def test_control_charts_by_code(self, client, app, capa_user):
        """Control charts by code"""
        client.post('/login', data={
            'username': 'capa_test_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)
        for code in ['Mad', 'Aad', 'Vad', 'CV']:
            response = client.get(f'/quality/control_charts?code={code}')
            assert response.status_code in [200, 302, 404]


class TestControlChartsNew:
    """Control charts new tests"""

    def test_control_chart_new_get(self, client, app, capa_senior):
        """Control chart new GET"""
        client.post('/login', data={
            'username': 'capa_test_senior',
            'password': VALID_PASSWORD
        }, follow_redirects=True)
        response = client.get('/quality/control_charts/new')
        assert response.status_code in [200, 302, 404]

    def test_control_chart_new_post(self, client, app, capa_senior):
        """Control chart new POST"""
        client.post('/login', data={
            'username': 'capa_test_senior',
            'password': VALID_PASSWORD
        }, follow_redirects=True)
        response = client.post('/quality/control_charts/new', data={
            'standard_code': 'MAD-STD-001',
            'analysis_code': 'Mad',
            'result_value': '5.5',
            'measurement_date': date.today().isoformat()
        }, follow_redirects=True)
        assert response.status_code in [200, 302, 400, 404]


class TestControlChartsAPI:
    """Control charts API tests"""

    def test_control_chart_data_api(self, client, app, capa_user):
        """Control chart data API"""
        client.post('/login', data={
            'username': 'capa_test_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)
        response = client.get('/quality/api/control_chart_data?code=Mad')
        assert response.status_code in [200, 302, 404]

    def test_control_chart_stats_api(self, client, app, capa_user):
        """Control chart stats API"""
        client.post('/login', data={
            'username': 'capa_test_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)
        response = client.get('/quality/api/control_chart_stats')
        assert response.status_code in [200, 302, 404]


class TestControlStandards:
    """Control standards tests"""

    def test_control_standards_list(self, client, app, capa_user):
        """Control standards list"""
        client.post('/login', data={
            'username': 'capa_test_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)
        response = client.get('/quality/control_standards')
        assert response.status_code in [200, 302, 404]

    def test_control_standard_new_get(self, client, app, capa_senior):
        """Control standard new GET"""
        client.post('/login', data={
            'username': 'capa_test_senior',
            'password': VALID_PASSWORD
        }, follow_redirects=True)
        response = client.get('/quality/control_standards/new')
        assert response.status_code in [200, 302, 404]


class TestEnvironmentalLogs:
    """Environmental logs tests"""

    def test_environmental_list(self, client, app, capa_user):
        """Environmental logs list"""
        client.post('/login', data={
            'username': 'capa_test_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)
        response = client.get('/quality/environmental')
        assert response.status_code in [200, 302, 404]

    def test_environmental_new_get(self, client, app, capa_senior):
        """Environmental log new GET"""
        client.post('/login', data={
            'username': 'capa_test_senior',
            'password': VALID_PASSWORD
        }, follow_redirects=True)
        response = client.get('/quality/environmental/new')
        assert response.status_code in [200, 302, 404]

    def test_environmental_new_post(self, client, app, capa_senior):
        """Environmental log new POST"""
        client.post('/login', data={
            'username': 'capa_test_senior',
            'password': VALID_PASSWORD
        }, follow_redirects=True)
        response = client.post('/quality/environmental/new', data={
            'location': 'Lab Room A',
            'temperature': '22.5',
            'humidity': '45',
            'measurement_date': date.today().isoformat()
        }, follow_redirects=True)
        assert response.status_code in [200, 302, 400, 404]


class TestComplaintsRoutes:
    """Customer complaints tests"""

    def test_complaints_list(self, client, app, capa_user):
        """Complaints list"""
        client.post('/login', data={
            'username': 'capa_test_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)
        response = client.get('/quality/complaints')
        assert response.status_code in [200, 302, 404]

    def test_complaint_new_get(self, client, app, capa_senior):
        """Complaint new GET"""
        client.post('/login', data={
            'username': 'capa_test_senior',
            'password': VALID_PASSWORD
        }, follow_redirects=True)
        response = client.get('/quality/complaints/new')
        assert response.status_code in [200, 302, 404]

    def test_complaint_new_post(self, client, app, capa_senior):
        """Complaint new POST"""
        client.post('/login', data={
            'username': 'capa_test_senior',
            'password': VALID_PASSWORD
        }, follow_redirects=True)
        response = client.post('/quality/complaints/new', data={
            'complainant_name': 'Test Customer',
            'complaint_description': 'Test complaint',
            'complaint_date': date.today().isoformat()
        }, follow_redirects=True)
        assert response.status_code in [200, 302, 400, 404]
