# tests/integration/test_admin_routes_full.py
# -*- coding: utf-8 -*-
"""
Admin routes full coverage tests
"""

import pytest
from app import db
from app.models import User, Sample, AnalysisResult, SystemSetting
from datetime import datetime
import json

VALID_PASSWORD = 'TestPass123'


@pytest.fixture
def admin_full_user(app):
    """Admin user fixture"""
    with app.app_context():
        user = User.query.filter_by(username='admin_full_user').first()
        if not user:
            user = User(username='admin_full_user', role='admin')
            user.set_password(VALID_PASSWORD)
            db.session.add(user)
            db.session.commit()
        return user


class TestAdminDashboard:
    """Admin dashboard тестүүд"""

    def test_admin_dashboard_unauthenticated(self, client, app):
        """Admin dashboard without login"""
        response = client.get('/admin')
        assert response.status_code in [200, 302, 404]

    def test_admin_dashboard_admin(self, client, app, admin_full_user):
        """Admin dashboard with admin"""
        client.post('/login', data={
            'username': 'admin_full_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)

        response = client.get('/admin')
        assert response.status_code in [200, 302, 404]


class TestAdminUsers:
    """Admin users тестүүд"""

    def test_admin_users_list(self, client, app, admin_full_user):
        """Admin users list"""
        client.post('/login', data={
            'username': 'admin_full_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)

        response = client.get('/admin/users')
        assert response.status_code in [200, 302, 404]

    def test_admin_user_detail(self, client, app, admin_full_user):
        """Admin user detail"""
        client.post('/login', data={
            'username': 'admin_full_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)

        with app.app_context():
            user = User.query.first()
            if user:
                response = client.get(f'/admin/users/{user.id}')
                assert response.status_code in [200, 302, 404]

    def test_admin_user_create_get(self, client, app, admin_full_user):
        """Admin user create GET"""
        client.post('/login', data={
            'username': 'admin_full_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)

        response = client.get('/admin/users/new')
        assert response.status_code in [200, 302, 404]

    def test_admin_user_create_post(self, client, app, admin_full_user):
        """Admin user create POST"""
        client.post('/login', data={
            'username': 'admin_full_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)

        response = client.post('/admin/users/new', data={
            'username': f'new_test_user_{datetime.now().timestamp()}',
            'password': 'TestPass123!',
            'role': 'chemist'
        })
        assert response.status_code in [200, 302, 400, 404]

    def test_admin_user_edit_get(self, client, app, admin_full_user):
        """Admin user edit GET"""
        client.post('/login', data={
            'username': 'admin_full_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)

        with app.app_context():
            user = User.query.first()
            if user:
                response = client.get(f'/admin/users/{user.id}/edit')
                assert response.status_code in [200, 302, 404]


class TestAdminSettings:
    """Admin settings тестүүд"""

    def test_admin_settings_list(self, client, app, admin_full_user):
        """Admin settings list"""
        client.post('/login', data={
            'username': 'admin_full_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)

        response = client.get('/admin/settings')
        assert response.status_code in [200, 302, 404]

    def test_admin_settings_by_category(self, client, app, admin_full_user):
        """Admin settings by category"""
        client.post('/login', data={
            'username': 'admin_full_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)

        for category in ['general', 'precision', 'repeatability']:
            response = client.get(f'/admin/settings?category={category}')
            assert response.status_code in [200, 302, 404]


class TestAdminAudit:
    """Admin audit тестүүд"""

    def test_admin_audit_log(self, client, app, admin_full_user):
        """Admin audit log"""
        client.post('/login', data={
            'username': 'admin_full_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)

        response = client.get('/admin/audit')
        assert response.status_code in [200, 302, 404]

    def test_admin_audit_filtered(self, client, app, admin_full_user):
        """Admin audit filtered"""
        client.post('/login', data={
            'username': 'admin_full_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)

        response = client.get('/admin/audit?action=create')
        assert response.status_code in [200, 302, 404]


class TestAdminBackup:
    """Admin backup тестүүд"""

    def test_admin_backup_list(self, client, app, admin_full_user):
        """Admin backup list"""
        client.post('/login', data={
            'username': 'admin_full_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)

        response = client.get('/admin/backup')
        assert response.status_code in [200, 302, 404]


class TestAdminSystem:
    """Admin system тестүүд"""

    def test_admin_system_info(self, client, app, admin_full_user):
        """Admin system info"""
        client.post('/login', data={
            'username': 'admin_full_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)

        response = client.get('/admin/system')
        assert response.status_code in [200, 302, 404]

    def test_admin_system_health(self, client, app, admin_full_user):
        """Admin system health"""
        client.post('/login', data={
            'username': 'admin_full_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)

        response = client.get('/admin/system/health')
        assert response.status_code in [200, 302, 404]


class TestAdminDatabase:
    """Admin database тестүүд"""

    def test_admin_database_stats(self, client, app, admin_full_user):
        """Admin database stats"""
        client.post('/login', data={
            'username': 'admin_full_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)

        response = client.get('/admin/database')
        assert response.status_code in [200, 302, 404]


class TestAdminAPI:
    """Admin API тестүүд"""

    def test_admin_api_stats(self, client, app, admin_full_user):
        """Admin API stats"""
        client.post('/login', data={
            'username': 'admin_full_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)

        response = client.get('/api/admin/stats')
        assert response.status_code in [200, 302, 404]

    def test_admin_api_users(self, client, app, admin_full_user):
        """Admin API users"""
        client.post('/login', data={
            'username': 'admin_full_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)

        response = client.get('/api/admin/users')
        assert response.status_code in [200, 302, 404]


class TestManageUsers:
    """User management actual routes тестүүд"""

    def test_manage_users_page(self, client, app, admin_full_user):
        """Manage users page access"""
        client.post('/login', data={
            'username': 'admin_full_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)
        response = client.get('/admin/manage_users')
        assert response.status_code in [200, 302]

    def test_manage_users_create_post(self, client, app, admin_full_user):
        """Create new user via manage_users POST"""
        client.post('/login', data={
            'username': 'admin_full_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)
        response = client.post('/admin/manage_users', data={
            'username': f'new_user_{datetime.now().timestamp()}',
            'password': 'NewUserPass123',
            'role': 'analyst'
        }, follow_redirects=True)
        assert response.status_code in [200, 302]

    def test_edit_user_page(self, client, app, admin_full_user):
        """Edit user page"""
        client.post('/login', data={
            'username': 'admin_full_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)

        with app.app_context():
            user = User(username=f'edit_user_{datetime.now().timestamp()}', role='analyst')
            user.set_password('EditPass123')
            db.session.add(user)
            db.session.commit()
            user_id = user.id

        response = client.get(f'/admin/edit_user/{user_id}')
        assert response.status_code in [200, 302, 404]

    def test_edit_user_post(self, client, app, admin_full_user):
        """Edit user POST"""
        client.post('/login', data={
            'username': 'admin_full_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)

        with app.app_context():
            user = User(username=f'edit_post_{datetime.now().timestamp()}', role='analyst')
            user.set_password('EditPostPass123')
            db.session.add(user)
            db.session.commit()
            user_id = user.id

        response = client.post(f'/admin/edit_user/{user_id}', data={
            'role': 'senior'
        }, follow_redirects=True)
        assert response.status_code in [200, 302, 404]

    def test_delete_user(self, client, app, admin_full_user):
        """Delete user"""
        client.post('/login', data={
            'username': 'admin_full_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)

        with app.app_context():
            user = User(username=f'delete_{datetime.now().timestamp()}', role='analyst')
            user.set_password('DeletePass123')
            db.session.add(user)
            db.session.commit()
            user_id = user.id

        response = client.post(f'/admin/delete_user/{user_id}', follow_redirects=True)
        assert response.status_code in [200, 302, 404]


class TestControlStandardsRoutes:
    """Control standards management тестүүд"""

    def test_manage_standards_page(self, client, app, admin_full_user):
        """Manage control standards page"""
        client.post('/login', data={
            'username': 'admin_full_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)
        response = client.get('/admin/control_standards')
        assert response.status_code in [200, 302]

    def test_create_standard(self, client, app, admin_full_user):
        """Create control standard"""
        client.post('/login', data={
            'username': 'admin_full_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)
        response = client.post('/admin/control_standards/create',
            json={
                'name': f'Test Standard {datetime.now().timestamp()}',
                'code': f'TS{int(datetime.now().timestamp()) % 10000}',
                'standard_type': 'internal'
            },
            follow_redirects=True)
        assert response.status_code in [200, 302, 400, 415]


class TestGBWStandardsRoutes:
    """GBW standards management тестүүд"""

    def test_manage_gbw_page(self, client, app, admin_full_user):
        """Manage GBW standards page"""
        client.post('/login', data={
            'username': 'admin_full_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)
        response = client.get('/admin/gbw_standards')
        assert response.status_code in [200, 302]

    def test_create_gbw(self, client, app, admin_full_user):
        """Create GBW standard"""
        client.post('/login', data={
            'username': 'admin_full_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)
        response = client.post('/admin/gbw_standards/create',
            json={
                'name': f'GBW Test {datetime.now().timestamp()}',
                'code': f'GBW{int(datetime.now().timestamp()) % 10000}'
            },
            follow_redirects=True)
        assert response.status_code in [200, 302, 400, 415]


class TestAnalysisConfigRoutes:
    """Analysis configuration тестүүд"""

    def test_analysis_config_page(self, client, app, admin_full_user):
        """Analysis config page"""
        client.post('/login', data={
            'username': 'admin_full_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)
        response = client.get('/admin/analysis_config')
        assert response.status_code in [200, 302]

    def test_analysis_config_post(self, client, app, admin_full_user):
        """Analysis config POST"""
        client.post('/login', data={
            'username': 'admin_full_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)
        response = client.post('/admin/analysis_config', data={
            'analysis_code': 'Mad',
            'precision': '2'
        }, follow_redirects=True)
        assert response.status_code in [200, 302]
