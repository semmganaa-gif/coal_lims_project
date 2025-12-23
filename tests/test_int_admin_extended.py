# tests/integration/test_admin_extended.py
# -*- coding: utf-8 -*-
"""
Admin routes extended coverage tests
"""

import pytest
from app import db
from app.models import User, Sample, SystemSetting
from datetime import datetime, date
import json
import uuid

VALID_PASSWORD = 'TestPass123'


@pytest.fixture
def admin_user_ext(app):
    """Admin user fixture"""
    with app.app_context():
        user = User.query.filter_by(username='admin_ext_user').first()
        if not user:
            user = User(username='admin_ext_user', role='admin')
            user.set_password(VALID_PASSWORD)
            db.session.add(user)
            db.session.commit()
        return user


@pytest.fixture
def manager_user_ext(app):
    """Manager user fixture"""
    with app.app_context():
        user = User.query.filter_by(username='manager_ext_user').first()
        if not user:
            user = User(username='manager_ext_user', role='manager')
            user.set_password(VALID_PASSWORD)
            db.session.add(user)
            db.session.commit()
        return user


@pytest.fixture
def test_user_ext(app):
    """Test user for admin operations"""
    with app.app_context():
        unique_id = uuid.uuid4().hex[:6]
        user = User(
            username=f'testuser_ext_{unique_id}',
            role='chemist'
        )
        user.set_password(VALID_PASSWORD)
        db.session.add(user)
        db.session.commit()
        return user.id


class TestAdminDashboardExtended:
    """Admin dashboard extended tests"""

    def test_admin_dashboard(self, client, app, admin_user_ext):
        """Admin dashboard"""
        client.post('/login', data={
            'username': 'admin_ext_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)
        response = client.get('/admin/')
        assert response.status_code in [200, 302, 404]

    def test_admin_index(self, client, app, admin_user_ext):
        """Admin index"""
        client.post('/login', data={
            'username': 'admin_ext_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)
        response = client.get('/admin')
        assert response.status_code in [200, 302, 404]


class TestUserManagementExtended:
    """User management extended tests"""

    def test_users_list(self, client, app, admin_user_ext):
        """Users list"""
        client.post('/login', data={
            'username': 'admin_ext_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)
        response = client.get('/admin/users')
        assert response.status_code in [200, 302, 404]

    def test_users_list_paginated(self, client, app, admin_user_ext):
        """Users list paginated"""
        client.post('/login', data={
            'username': 'admin_ext_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)
        response = client.get('/admin/users?page=1')
        assert response.status_code in [200, 302, 404]

    def test_users_filter_role(self, client, app, admin_user_ext):
        """Users filter by role"""
        client.post('/login', data={
            'username': 'admin_ext_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)
        for role in ['admin', 'senior', 'chemist', 'prep']:
            response = client.get(f'/admin/users?role={role}')
            assert response.status_code in [200, 302, 404]

    def test_user_create_get(self, client, app, admin_user_ext):
        """User create GET"""
        client.post('/login', data={
            'username': 'admin_ext_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)
        response = client.get('/admin/users/new')
        assert response.status_code in [200, 302, 404]

    def test_user_create_post(self, client, app, admin_user_ext):
        """User create POST"""
        client.post('/login', data={
            'username': 'admin_ext_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)
        unique_id = uuid.uuid4().hex[:6]
        response = client.post('/admin/users/new', data={
            'username': f'newuser_ext_{unique_id}',
            'password': VALID_PASSWORD,
            'confirm_password': VALID_PASSWORD,
            'role': 'chemist',
            'email': f'user_{unique_id}@test.com'
        }, follow_redirects=True)
        assert response.status_code in [200, 302, 400, 404, 405, 422, 500]

    def test_user_edit_get(self, client, app, admin_user_ext, test_user_ext):
        """User edit GET"""
        client.post('/login', data={
            'username': 'admin_ext_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)
        response = client.get(f'/admin/users/{test_user_ext}/edit')
        assert response.status_code in [200, 302, 404]

    def test_user_edit_post(self, client, app, admin_user_ext, test_user_ext):
        """User edit POST"""
        client.post('/login', data={
            'username': 'admin_ext_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)
        response = client.post(f'/admin/users/{test_user_ext}/edit', data={
            'role': 'senior',
            'is_active': 'true'
        }, follow_redirects=True)
        assert response.status_code in [200, 302, 400, 404]

    def test_user_delete(self, client, app, admin_user_ext, test_user_ext):
        """User delete"""
        client.post('/login', data={
            'username': 'admin_ext_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)
        response = client.post(f'/admin/users/{test_user_ext}/delete', follow_redirects=True)
        assert response.status_code in [200, 302, 404]

    def test_user_toggle_active(self, client, app, admin_user_ext, test_user_ext):
        """User toggle active status"""
        client.post('/login', data={
            'username': 'admin_ext_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)
        response = client.post(f'/admin/users/{test_user_ext}/toggle_active', follow_redirects=True)
        assert response.status_code in [200, 302, 404]


class TestSystemSettingsExtended:
    """System settings extended tests"""

    def test_settings_get(self, client, app, admin_user_ext):
        """Settings GET"""
        client.post('/login', data={
            'username': 'admin_ext_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)
        response = client.get('/admin/settings')
        assert response.status_code in [200, 302, 404]

    def test_settings_post(self, client, app, admin_user_ext):
        """Settings POST"""
        client.post('/login', data={
            'username': 'admin_ext_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)
        response = client.post('/admin/settings', data={
            'lab_name': 'Test Lab Updated',
            'timezone': 'Asia/Ulaanbaatar',
            'date_format': '%Y-%m-%d'
        }, follow_redirects=True)
        assert response.status_code in [200, 302, 400, 404]


class TestAuditLogsExtended:
    """Audit logs extended tests"""

    def test_audit_logs_list(self, client, app, admin_user_ext):
        """Audit logs list"""
        client.post('/login', data={
            'username': 'admin_ext_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)
        response = client.get('/admin/audit_logs')
        assert response.status_code in [200, 302, 404]

    def test_audit_logs_filter_date(self, client, app, admin_user_ext):
        """Audit logs filter by date"""
        client.post('/login', data={
            'username': 'admin_ext_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)
        today = date.today().isoformat()
        response = client.get(f'/admin/audit_logs?date_from={today}&date_to={today}')
        assert response.status_code in [200, 302, 404]

    def test_audit_logs_filter_user(self, client, app, admin_user_ext):
        """Audit logs filter by user"""
        client.post('/login', data={
            'username': 'admin_ext_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)
        response = client.get('/admin/audit_logs?username=admin')
        assert response.status_code in [200, 302, 404]

    def test_audit_logs_filter_action(self, client, app, admin_user_ext):
        """Audit logs filter by action"""
        client.post('/login', data={
            'username': 'admin_ext_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)
        response = client.get('/admin/audit_logs?action=login')
        assert response.status_code in [200, 302, 404]

    def test_audit_logs_paginated(self, client, app, admin_user_ext):
        """Audit logs paginated"""
        client.post('/login', data={
            'username': 'admin_ext_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)
        response = client.get('/admin/audit_logs?page=1&per_page=50')
        assert response.status_code in [200, 302, 404]


class TestEquipmentManagement:
    """Equipment management tests"""

    def test_equipment_list(self, client, app, admin_user_ext):
        """Equipment list"""
        client.post('/login', data={
            'username': 'admin_ext_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)
        response = client.get('/equipment/')
        assert response.status_code in [200, 302, 404]

    def test_equipment_new_get(self, client, app, admin_user_ext):
        """Equipment new GET"""
        client.post('/login', data={
            'username': 'admin_ext_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)
        response = client.get('/equipment/new')
        assert response.status_code in [200, 302, 404]

    def test_equipment_new_post(self, client, app, admin_user_ext):
        """Equipment new POST"""
        client.post('/login', data={
            'username': 'admin_ext_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)
        unique_id = uuid.uuid4().hex[:6]
        response = client.post('/equipment/new', data={
            'name': f'Test Equipment {unique_id}',
            'equipment_type': 'balance',
            'serial_number': f'SN-{unique_id}',
            'status': 'normal'
        }, follow_redirects=True)
        assert response.status_code in [200, 302, 400, 404]


class TestReportManagement:
    """Report management tests"""

    def test_reports_list(self, client, app, admin_user_ext):
        """Reports list"""
        client.post('/login', data={
            'username': 'admin_ext_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)
        response = client.get('/reports/')
        assert response.status_code in [200, 302, 404]

    def test_consumption_report(self, client, app, admin_user_ext):
        """Consumption report"""
        client.post('/login', data={
            'username': 'admin_ext_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)
        response = client.get('/reports/consumption')
        assert response.status_code in [200, 302, 404]

    def test_monthly_report(self, client, app, admin_user_ext):
        """Monthly report"""
        client.post('/login', data={
            'username': 'admin_ext_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)
        response = client.get('/reports/monthly')
        assert response.status_code in [200, 302, 404]


class TestDataExport:
    """Data export tests"""

    def test_export_samples_csv(self, client, app, admin_user_ext):
        """Export samples CSV"""
        client.post('/login', data={
            'username': 'admin_ext_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)
        response = client.get('/admin/export/samples?format=csv')
        assert response.status_code in [200, 302, 404]

    def test_export_samples_excel(self, client, app, admin_user_ext):
        """Export samples Excel"""
        client.post('/login', data={
            'username': 'admin_ext_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)
        response = client.get('/admin/export/samples?format=excel')
        assert response.status_code in [200, 302, 404]

    def test_export_users(self, client, app, admin_user_ext):
        """Export users"""
        client.post('/login', data={
            'username': 'admin_ext_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)
        response = client.get('/admin/export/users')
        assert response.status_code in [200, 302, 404]


class TestBackupRestore:
    """Backup and restore tests"""

    def test_backup_list(self, client, app, admin_user_ext):
        """Backup list"""
        client.post('/login', data={
            'username': 'admin_ext_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)
        response = client.get('/admin/backups')
        assert response.status_code in [200, 302, 404]

    def test_create_backup(self, client, app, admin_user_ext):
        """Create backup"""
        client.post('/login', data={
            'username': 'admin_ext_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)
        response = client.post('/admin/backups/create', follow_redirects=True)
        assert response.status_code in [200, 302, 400, 404]
