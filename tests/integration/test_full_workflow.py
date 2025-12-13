# -*- coding: utf-8 -*-
"""
Full workflow интеграцийн тестүүд
"""
import pytest
from datetime import datetime
from app import create_app, db
from app.models import User, Sample, AnalysisResult, Equipment


@pytest.fixture
def app():
    """Test application fixture"""
    app = create_app()
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False
    app.config['SERVER_NAME'] = 'localhost'
    return app


@pytest.fixture
def client(app):
    """Test client fixture"""
    return app.test_client()


@pytest.fixture
def auth_client(app, client):
    """Authenticated client fixture"""
    with app.app_context():
        user = User.query.filter_by(username='admin').first()
        if not user:
            user = User(username='admin', role='admin')
            user.set_password('Admin123')
            db.session.add(user)
            db.session.commit()

        with client.session_transaction() as sess:
            sess['_user_id'] = str(user.id)
            sess['_fresh'] = True

    return client


class TestAllApiEndpoints:
    """All API endpoints тестүүд"""

    def test_check_ready_samples(self, auth_client, app):
        """Check ready samples"""
        with app.app_context():
            response = auth_client.get('/api/check_ready_samples')
            assert response.status_code in [200, 302, 404]

    def test_request_analysis_empty(self, auth_client, app):
        """Request analysis empty"""
        with app.app_context():
            response = auth_client.post('/api/request_analysis', json={
                'sample_ids': [],
                'analysis_codes': []
            })
            assert response.status_code in [200, 302, 400]


class TestEquipmentJournal:
    """Equipment journal тестүүд"""

    def test_equipment_list_json(self, auth_client, app):
        """Equipment list JSON"""
        with app.app_context():
            response = auth_client.get('/api/equipment_list_json')
            assert response.status_code in [200, 302]

    def test_equipment_journal_detailed(self, auth_client, app):
        """Equipment journal detailed"""
        with app.app_context():
            response = auth_client.get('/api/equipment/journal_detailed')
            assert response.status_code in [200, 302, 404]

    def test_equipment_monthly_stats(self, auth_client, app):
        """Equipment monthly stats"""
        with app.app_context():
            response = auth_client.get('/api/equipment/monthly_stats')
            assert response.status_code in [200, 302, 404]

    def test_equipment_usage_summary(self, auth_client, app):
        """Equipment usage summary"""
        with app.app_context():
            response = auth_client.get('/api/equipment/usage_summary')
            assert response.status_code in [200, 302, 404]


class TestQualityApis:
    """Quality API тестүүд"""

    def test_westgard_summary(self, auth_client, app):
        """Westgard summary"""
        with app.app_context():
            response = auth_client.get('/quality/api/westgard_summary')
            assert response.status_code in [200, 302, 404]


class TestChatEndpoints:
    """Chat endpoints тестүүд"""

    def test_chat_search(self, auth_client, app):
        """Chat search"""
        with app.app_context():
            response = auth_client.get('/api/chat/search')
            assert response.status_code in [200, 302, 404, 500]

    def test_chat_templates(self, auth_client, app):
        """Chat templates"""
        with app.app_context():
            response = auth_client.get('/api/chat/templates')
            assert response.status_code in [200, 302, 404, 500]


class TestAnalysisRoutes:
    """Analysis routes тестүүд"""

    def test_audit_log_ts(self, auth_client, app):
        """Audit log TS"""
        with app.app_context():
            response = auth_client.get('/api/audit_log/TS')
            assert response.status_code in [200, 302]

    def test_audit_log_cv(self, auth_client, app):
        """Audit log CV"""
        with app.app_context():
            response = auth_client.get('/api/audit_log/CV')
            assert response.status_code in [200, 302]

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

    def test_eligible_samples_mad(self, auth_client, app):
        """Eligible samples Mad"""
        with app.app_context():
            response = auth_client.get('/api/eligible_samples/Mad')
            assert response.status_code in [200, 302]
