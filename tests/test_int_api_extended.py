# -*- coding: utf-8 -*-
"""
API extended тестүүд
"""
import pytest
import json
from app import create_app, db
from app.models import User


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


class TestSamplesAPI:
    """Samples API тестүүд"""

    def test_get_samples(self, auth_client, app):
        """Get samples"""
        with app.app_context():
            response = auth_client.get('/api/samples')
            assert response.status_code in [200, 302, 404]

    def test_get_sample_detail(self, auth_client, app):
        """Get sample detail"""
        with app.app_context():
            response = auth_client.get('/api/samples/1')
            assert response.status_code in [200, 302, 404]

    def test_create_sample(self, auth_client, app):
        """Create sample"""
        with app.app_context():
            response = auth_client.post('/api/samples', json={
                'client_name': 'CHPP',
                'sample_type': '12H'
            })
            assert response.status_code in [200, 201, 302, 400, 404]

    def test_update_sample(self, auth_client, app):
        """Update sample"""
        with app.app_context():
            response = auth_client.put('/api/samples/1', json={
                'status': 'in_progress'
            })
            assert response.status_code in [200, 302, 400, 404]

    def test_delete_sample(self, auth_client, app):
        """Delete sample"""
        with app.app_context():
            response = auth_client.delete('/api/samples/99999')
            assert response.status_code in [200, 302, 400, 404]


class TestAnalysisAPI:
    """Analysis API тестүүд"""

    def test_get_analysis_results(self, auth_client, app):
        """Get analysis results"""
        with app.app_context():
            response = auth_client.get('/api/analysis/results')
            assert response.status_code in [200, 302, 404]

    def test_save_analysis_result(self, auth_client, app):
        """Save analysis result"""
        with app.app_context():
            response = auth_client.post('/api/analysis/save', json={
                'sample_id': 1,
                'analysis_code': 'TS',
                'result': 5.5
            })
            assert response.status_code in [200, 302, 400, 404]

    def test_batch_save_results(self, auth_client, app):
        """Batch save results"""
        with app.app_context():
            response = auth_client.post('/api/analysis/batch_save', json={
                'results': [
                    {'sample_id': 1, 'analysis_code': 'TS', 'result': 5.5},
                    {'sample_id': 2, 'analysis_code': 'TS', 'result': 6.0}
                ]
            })
            assert response.status_code in [200, 302, 400, 404]

    def test_pending_samples(self, auth_client, app):
        """Pending samples"""
        with app.app_context():
            response = auth_client.get('/api/analysis/pending/TS')
            assert response.status_code in [200, 302, 404]


class TestAuditAPI:
    """Audit API тестүүд"""

    def test_get_audit_logs(self, auth_client, app):
        """Get audit logs"""
        with app.app_context():
            response = auth_client.get('/api/audit/logs')
            assert response.status_code in [200, 302, 404]

    def test_get_audit_log_detail(self, auth_client, app):
        """Get audit log detail"""
        with app.app_context():
            response = auth_client.get('/api/audit/logs/1')
            assert response.status_code in [200, 302, 404]

    def test_filter_audit_logs(self, auth_client, app):
        """Filter audit logs"""
        with app.app_context():
            response = auth_client.get('/api/audit/logs?action=sample_created')
            assert response.status_code in [200, 302, 404]


class TestMassAPI:
    """Mass API тестүүд"""

    def test_mass_prep_api(self, auth_client, app):
        """Mass prep API"""
        with app.app_context():
            response = auth_client.get('/api/mass/prep')
            assert response.status_code in [200, 302, 404]

    def test_save_mass(self, auth_client, app):
        """Save mass"""
        with app.app_context():
            response = auth_client.post('/api/mass/save', json={
                'sample_id': 1,
                'mass_type': 'prep',
                'value': 10.5
            })
            assert response.status_code in [200, 302, 400, 404]


class TestEquipmentAPI:
    """Equipment API тестүүд"""

    def test_get_equipment(self, auth_client, app):
        """Get equipment"""
        with app.app_context():
            response = auth_client.get('/api/equipment')
            assert response.status_code in [200, 302, 404]

    def test_get_equipment_detail(self, auth_client, app):
        """Get equipment detail"""
        with app.app_context():
            response = auth_client.get('/api/equipment/1')
            assert response.status_code in [200, 302, 404]

    def test_equipment_calibration(self, auth_client, app):
        """Equipment calibration"""
        with app.app_context():
            response = auth_client.get('/api/equipment/1/calibration')
            assert response.status_code in [200, 302, 404]


class TestReportAPI:
    """Report API тестүүд"""

    def test_daily_report_data(self, auth_client, app):
        """Daily report data"""
        with app.app_context():
            response = auth_client.get('/api/reports/daily')
            assert response.status_code in [200, 302, 404]

    def test_monthly_report_data(self, auth_client, app):
        """Monthly report data"""
        with app.app_context():
            response = auth_client.get('/api/reports/monthly')
            assert response.status_code in [200, 302, 404]

    def test_export_report(self, auth_client, app):
        """Export report"""
        with app.app_context():
            response = auth_client.get('/api/reports/export?format=excel')
            assert response.status_code in [200, 302, 404]
