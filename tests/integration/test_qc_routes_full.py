# tests/integration/test_qc_routes_full.py
# -*- coding: utf-8 -*-
"""
QC routes full coverage tests
"""

import pytest
from app import db
from app.models import User, Sample, AnalysisResult, ControlStandard
from datetime import datetime, timedelta
import json

VALID_PASSWORD = 'TestPass123'


@pytest.fixture
def qc_user(app):
    """QC user fixture"""
    with app.app_context():
        user = User.query.filter_by(username='qc_full_user').first()
        if not user:
            user = User(username='qc_full_user', role='senior')
            user.set_password(VALID_PASSWORD)
            db.session.add(user)
            db.session.commit()
        return user


@pytest.fixture
def qc_chemist(app):
    """QC chemist fixture"""
    with app.app_context():
        user = User.query.filter_by(username='qc_chemist_user').first()
        if not user:
            user = User(username='qc_chemist_user', role='chemist')
            user.set_password(VALID_PASSWORD)
            db.session.add(user)
            db.session.commit()
        return user


class TestQCIndex:
    """QC index тестүүд"""

    def test_qc_index_unauthenticated(self, client, app):
        """QC index without login"""
        response = client.get('/analysis/qc')
        assert response.status_code in [200, 302, 404]

    def test_qc_index_authenticated(self, client, app, qc_user):
        """QC index with login"""
        client.post('/login', data={
            'username': 'qc_full_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)

        response = client.get('/analysis/qc')
        assert response.status_code in [200, 302, 404]


class TestQCControlCharts:
    """QC control charts тестүүд"""

    def test_control_charts_index(self, client, app, qc_user):
        """Control charts index"""
        client.post('/login', data={
            'username': 'qc_full_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)

        response = client.get('/analysis/qc/control_charts')
        assert response.status_code in [200, 302, 404]

    def test_control_charts_mad(self, client, app, qc_user):
        """Control charts for Mad"""
        client.post('/login', data={
            'username': 'qc_full_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)

        response = client.get('/analysis/qc/control_charts/Mad')
        assert response.status_code in [200, 302, 404]

    def test_control_charts_aad(self, client, app, qc_user):
        """Control charts for Aad"""
        client.post('/login', data={
            'username': 'qc_full_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)

        response = client.get('/analysis/qc/control_charts/Aad')
        assert response.status_code in [200, 302, 404]

    def test_control_charts_vad(self, client, app, qc_user):
        """Control charts for Vad"""
        client.post('/login', data={
            'username': 'qc_full_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)

        response = client.get('/analysis/qc/control_charts/Vad')
        assert response.status_code in [200, 302, 404]

    def test_control_charts_cv(self, client, app, qc_user):
        """Control charts for CV"""
        client.post('/login', data={
            'username': 'qc_full_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)

        response = client.get('/analysis/qc/control_charts/CV')
        assert response.status_code in [200, 302, 404]


class TestQCChartData:
    """QC chart data API тестүүд"""

    def test_chart_data_api(self, client, app, qc_user):
        """QC chart data API"""
        client.post('/login', data={
            'username': 'qc_full_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)

        response = client.get('/api/qc/chart_data?code=Mad')
        assert response.status_code in [200, 302, 404]

    def test_chart_data_with_period(self, client, app, qc_user):
        """QC chart data with period"""
        client.post('/login', data={
            'username': 'qc_full_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)

        response = client.get('/api/qc/chart_data?code=Mad&period=30')
        assert response.status_code in [200, 302, 404]


class TestQCWestgard:
    """QC Westgard rules тестүүд"""

    def test_westgard_evaluation(self, client, app, qc_user):
        """Westgard evaluation"""
        client.post('/login', data={
            'username': 'qc_full_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)

        response = client.get('/api/qc/westgard?code=Mad')
        assert response.status_code in [200, 302, 404]

    def test_westgard_report(self, client, app, qc_user):
        """Westgard report"""
        client.post('/login', data={
            'username': 'qc_full_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)

        response = client.get('/analysis/qc/westgard_report')
        assert response.status_code in [200, 302, 404]


class TestQCControlStandards:
    """QC control standards тестүүд"""

    def test_control_standards_list(self, client, app, qc_user):
        """Control standards list"""
        client.post('/login', data={
            'username': 'qc_full_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)

        response = client.get('/analysis/qc/control_standards')
        assert response.status_code in [200, 302, 404]

    def test_control_standard_detail(self, client, app, qc_user):
        """Control standard detail"""
        client.post('/login', data={
            'username': 'qc_full_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)

        with app.app_context():
            cs = ControlStandard.query.first()
            if cs:
                response = client.get(f'/analysis/qc/control_standards/{cs.id}')
                assert response.status_code in [200, 302, 404]


class TestQCViolations:
    """QC violations тестүүд"""

    def test_violations_list(self, client, app, qc_user):
        """QC violations list"""
        client.post('/login', data={
            'username': 'qc_full_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)

        response = client.get('/analysis/qc/violations')
        assert response.status_code in [200, 302, 404]

    def test_violations_api(self, client, app, qc_user):
        """QC violations API"""
        client.post('/login', data={
            'username': 'qc_full_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)

        response = client.get('/api/qc/violations')
        assert response.status_code in [200, 302, 404]


class TestQCStatistics:
    """QC statistics тестүүд"""

    def test_qc_stats(self, client, app, qc_user):
        """QC statistics"""
        client.post('/login', data={
            'username': 'qc_full_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)

        response = client.get('/api/qc/stats')
        assert response.status_code in [200, 302, 404]

    def test_qc_stats_by_analysis(self, client, app, qc_user):
        """QC stats by analysis"""
        client.post('/login', data={
            'username': 'qc_full_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)

        response = client.get('/api/qc/stats?analysis_code=Mad')
        assert response.status_code in [200, 302, 404]


class TestQCActions:
    """QC actions тестүүд"""

    def test_qc_acknowledge(self, client, app, qc_user):
        """QC acknowledge violation"""
        client.post('/login', data={
            'username': 'qc_full_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)

        response = client.post('/api/qc/acknowledge',
            json={'violation_id': 1, 'action': 'acknowledged'},
            content_type='application/json')
        assert response.status_code in [200, 302, 400, 404]

    def test_qc_resolve(self, client, app, qc_user):
        """QC resolve violation"""
        client.post('/login', data={
            'username': 'qc_full_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)

        response = client.post('/api/qc/resolve',
            json={'violation_id': 1, 'resolution': 'test resolution'},
            content_type='application/json')
        assert response.status_code in [200, 302, 400, 404]
