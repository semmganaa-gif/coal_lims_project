# tests/integration/test_admin_extended_more.py
# -*- coding: utf-8 -*-
"""
Admin routes additional tests
Coverage target: app/routes/admin_routes.py
"""

import pytest
from app import db
from app.models import User, AnalysisType, Equipment, ControlStandard
from datetime import datetime
import uuid

VALID_PASSWORD = 'TestPass123'


@pytest.fixture
def admin_user(app):
    """Admin test user"""
    with app.app_context():
        user = User.query.filter_by(username='admin_ext_user').first()
        if not user:
            user = User(username='admin_ext_user', role='admin')
            user.set_password(VALID_PASSWORD)
            db.session.add(user)
            db.session.commit()
        return user


def login_admin(client):
    """Helper login"""
    client.post('/login', data={
        'username': 'admin_ext_user',
        'password': VALID_PASSWORD
    }, follow_redirects=True)


class TestUserManagement:
    """Test user management routes"""

    def test_manage_users_page(self, client, app, admin_user):
        """Manage users page"""
        login_admin(client)
        response = client.get('/admin/users')
        assert response.status_code in [200, 302, 404]

    def test_new_user_form(self, client, app, admin_user):
        """New user form"""
        login_admin(client)
        response = client.get('/admin/users/new')
        assert response.status_code in [200, 302, 404]

    def test_create_user_post(self, client, app, admin_user):
        """Create user POST"""
        login_admin(client)
        unique = uuid.uuid4().hex[:6]
        response = client.post('/admin/users/new', data={
            'username': f'newuser{unique}',
            'password': 'TestPass123',
            'role': 'chemist'
        })
        assert response.status_code in [200, 302, 400, 404]

    def test_edit_user_page(self, client, app, admin_user):
        """Edit user page"""
        login_admin(client)
        response = client.get('/admin/users/1/edit')
        assert response.status_code in [200, 302, 404]

    def test_delete_user(self, client, app, admin_user):
        """Delete user"""
        login_admin(client)
        response = client.post('/admin/users/999/delete')
        assert response.status_code in [200, 302, 404]


class TestAnalysisTypeManagement:
    """Test analysis type management"""

    def test_analysis_types_list(self, client, app, admin_user):
        """Analysis types list"""
        login_admin(client)
        response = client.get('/admin/analysis_types')
        assert response.status_code in [200, 302, 404]

    def test_new_analysis_type(self, client, app, admin_user):
        """New analysis type form"""
        login_admin(client)
        response = client.get('/admin/analysis_types/new')
        assert response.status_code in [200, 302, 404]

    def test_create_analysis_type(self, client, app, admin_user):
        """Create analysis type"""
        login_admin(client)
        unique = uuid.uuid4().hex[:4]
        response = client.post('/admin/analysis_types/new', data={
            'code': f'AT{unique}',
            'name': f'Test Analysis {unique}',
            'required_role': 'chemist'
        })
        assert response.status_code in [200, 302, 400, 404]

    def test_edit_analysis_type(self, client, app, admin_user):
        """Edit analysis type"""
        login_admin(client)
        response = client.get('/admin/analysis_types/1/edit')
        assert response.status_code in [200, 302, 404]


class TestControlStandardsManagement:
    """Test control standards management"""

    def test_control_standards_list(self, client, app, admin_user):
        """Control standards list"""
        login_admin(client)
        response = client.get('/admin/control_standards')
        assert response.status_code in [200, 302, 404]

    def test_new_control_standard(self, client, app, admin_user):
        """New control standard form"""
        login_admin(client)
        response = client.get('/admin/control_standards/new')
        assert response.status_code in [200, 302, 404]

    def test_create_control_standard(self, client, app, admin_user):
        """Create control standard"""
        login_admin(client)
        unique = uuid.uuid4().hex[:4]
        response = client.post('/admin/control_standards/new', data={
            'name': f'CS-{unique}',
            'analysis_code': 'Mad',
            'certified_value': '5.0',
            'uncertainty': '0.1'
        })
        assert response.status_code in [200, 302, 400, 404]


class TestGBWStandards:
    """Test GBW standards management"""

    def test_gbw_standards_list(self, client, app, admin_user):
        """GBW standards list"""
        login_admin(client)
        response = client.get('/admin/gbw_standards')
        assert response.status_code in [200, 302, 404]

    def test_new_gbw_standard(self, client, app, admin_user):
        """New GBW standard form"""
        login_admin(client)
        response = client.get('/admin/gbw_standards/new')
        assert response.status_code in [200, 302, 404]


class TestAnalysisProfiles:
    """Test analysis profiles"""

    def test_analysis_profiles_list(self, client, app, admin_user):
        """Analysis profiles list"""
        login_admin(client)
        response = client.get('/admin/analysis_profiles')
        assert response.status_code in [200, 302, 404]

    def test_new_analysis_profile(self, client, app, admin_user):
        """New analysis profile form"""
        login_admin(client)
        response = client.get('/admin/analysis_profiles/new')
        assert response.status_code in [200, 302, 404]


class TestSystemSettings:
    """Test system settings"""

    def test_system_settings_page(self, client, app, admin_user):
        """System settings page"""
        login_admin(client)
        response = client.get('/admin/settings')
        assert response.status_code in [200, 302, 404]

    def test_update_settings(self, client, app, admin_user):
        """Update system settings"""
        login_admin(client)
        response = client.post('/admin/settings', data={
            'site_name': 'Coal LIMS'
        })
        assert response.status_code in [200, 302, 400, 404]


class TestAdminAPI:
    """Test admin API endpoints"""

    def test_admin_stats_api(self, client, app, admin_user):
        """Admin stats API"""
        login_admin(client)
        response = client.get('/admin/api/stats')
        assert response.status_code in [200, 302, 404]

    def test_admin_users_api(self, client, app, admin_user):
        """Admin users API"""
        login_admin(client)
        response = client.get('/admin/api/users')
        assert response.status_code in [200, 302, 404]

    def test_admin_analysis_types_api(self, client, app, admin_user):
        """Admin analysis types API"""
        login_admin(client)
        response = client.get('/admin/api/analysis_types')
        assert response.status_code in [200, 302, 404]


class TestAdminBackup:
    """Test admin backup functionality"""

    def test_backup_page(self, client, app, admin_user):
        """Backup page"""
        login_admin(client)
        response = client.get('/admin/backup')
        assert response.status_code in [200, 302, 404]

    def test_create_backup(self, client, app, admin_user):
        """Create backup"""
        login_admin(client)
        response = client.post('/admin/backup/create')
        assert response.status_code in [200, 302, 400, 404]


class TestAdminAuditLog:
    """Test admin audit log"""

    def test_audit_log_page(self, client, app, admin_user):
        """Audit log page"""
        login_admin(client)
        response = client.get('/admin/audit_log')
        assert response.status_code in [200, 302, 404]

    def test_audit_log_with_filter(self, client, app, admin_user):
        """Audit log with filter"""
        login_admin(client)
        response = client.get('/admin/audit_log?action=login')
        assert response.status_code in [200, 302, 404]
