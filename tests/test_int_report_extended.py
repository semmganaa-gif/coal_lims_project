# -*- coding: utf-8 -*-
"""
Report routes extended тестүүд
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
            user.set_password('Admin123')
            db.session.add(user)
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


class TestSampleReportApi:
    """Sample report API тестүүд"""

    def test_sample_report_nonexistent(self, auth_client, app):
        """Nonexistent sample report"""
        with app.app_context():
            response = auth_client.get('/api/sample_report/99999')
            assert response.status_code in [200, 302, 404]

    def test_sample_history_nonexistent(self, auth_client, app):
        """Nonexistent sample history"""
        with app.app_context():
            response = auth_client.get('/api/sample_history/99999')
            assert response.status_code in [200, 302, 404]


class TestExportApi:
    """Export API тестүүд"""

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

    def test_export_audit(self, auth_client, app):
        """Export audit"""
        with app.app_context():
            response = auth_client.get('/api/export/audit')
            assert response.status_code in [200, 302, 404]


class TestArchiveApi:
    """Archive API тестүүд"""

    def test_archive_hub(self, auth_client, app):
        """Archive hub"""
        with app.app_context():
            response = auth_client.get('/api/archive_hub')
            assert response.status_code in [200, 302, 404]


class TestAuditApi:
    """Audit API тестүүд"""

    def test_audit_hub(self, auth_client, app):
        """Audit hub"""
        with app.app_context():
            response = auth_client.get('/api/audit_hub')
            assert response.status_code in [200, 302, 404]

    def test_audit_search(self, auth_client, app):
        """Audit search"""
        with app.app_context():
            response = auth_client.get('/api/audit_search')
            assert response.status_code in [200, 302, 404]
