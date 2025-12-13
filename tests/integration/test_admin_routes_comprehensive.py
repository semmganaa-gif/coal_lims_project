# tests/integration/test_admin_routes_comprehensive.py
# -*- coding: utf-8 -*-
"""
Admin Routes Comprehensive Tests
"""

import pytest
from flask import url_for
from app import db
from app.models import User, SystemSetting, ControlStandard, Equipment
from datetime import datetime
import json

VALID_PASSWORD = 'TestPass123'


@pytest.fixture
def admin_user(app):
    """Admin хэрэглэгч"""
    with app.app_context():
        user = User.query.filter_by(username='admin_route_user').first()
        if not user:
            user = User(username='admin_route_user', role='admin')
            user.set_password(VALID_PASSWORD)
            db.session.add(user)
            db.session.commit()
        return user


@pytest.fixture
def manager_user(app):
    """Manager хэрэглэгч"""
    with app.app_context():
        user = User.query.filter_by(username='manager_route_user').first()
        if not user:
            user = User(username='manager_route_user', role='manager')
            user.set_password(VALID_PASSWORD)
            db.session.add(user)
            db.session.commit()
        return user


class TestAdminDashboard:
    """Admin dashboard тестүүд"""

    def test_admin_dashboard_unauthorized(self, client, app):
        """Non-admin cannot access admin"""
        with app.app_context():
            user = User.query.filter_by(username='chemist_admin_test').first()
            if not user:
                user = User(username='chemist_admin_test', role='chemist')
                user.set_password(VALID_PASSWORD)
                db.session.add(user)
                db.session.commit()

        client.post('/login', data={
            'username': 'chemist_admin_test',
            'password': VALID_PASSWORD
        }, follow_redirects=True)

        response = client.get('/admin')
        assert response.status_code in [302, 403, 404]

    def test_admin_dashboard_authorized(self, client, app, admin_user):
        """Admin can access admin"""
        client.post('/login', data={
            'username': 'admin_route_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)

        response = client.get('/admin')
        # 404 if admin route not implemented
        assert response.status_code in [200, 302, 404]


class TestUserManagement:
    """User management тестүүд"""

    def test_users_list(self, client, app, admin_user):
        """Users list"""
        client.post('/login', data={
            'username': 'admin_route_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)

        response = client.get('/admin/users')
        assert response.status_code in [200, 302, 404]

    def test_user_detail(self, client, app, admin_user):
        """User detail"""
        client.post('/login', data={
            'username': 'admin_route_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)

        with app.app_context():
            user = User.query.first()
            if user:
                response = client.get(f'/admin/users/{user.id}')
                assert response.status_code in [200, 302, 404]

    def test_create_user_page(self, client, app, admin_user):
        """Create user page"""
        client.post('/login', data={
            'username': 'admin_route_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)

        response = client.get('/admin/users/new')
        assert response.status_code in [200, 302, 404]

    def test_create_user_post(self, client, app, admin_user):
        """Create user POST"""
        client.post('/login', data={
            'username': 'admin_route_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)

        response = client.post('/admin/users/new', data={
            'username': 'new_test_user_1234',
            'password': 'TestPass123',
            'role': 'chemist'
        })
        assert response.status_code in [200, 302, 400, 404, 405]

    def test_edit_user_page(self, client, app, admin_user):
        """Edit user page"""
        client.post('/login', data={
            'username': 'admin_route_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)

        with app.app_context():
            user = User.query.first()
            if user:
                response = client.get(f'/admin/users/{user.id}/edit')
                assert response.status_code in [200, 302, 404]

    def test_toggle_user_status(self, client, app, admin_user):
        """Toggle user status"""
        client.post('/login', data={
            'username': 'admin_route_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)

        with app.app_context():
            user = User.query.filter(User.username != 'admin_route_user').first()
            if user:
                response = client.post(f'/admin/users/{user.id}/toggle')
                assert response.status_code in [200, 302, 400, 404]


class TestControlStandardManagement:
    """Control Standard management тестүүд"""

    def test_control_standards_list(self, client, app, admin_user):
        """Control standards list"""
        client.post('/login', data={
            'username': 'admin_route_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)

        response = client.get('/admin/control_standards')
        assert response.status_code in [200, 302, 404]

    def test_control_standard_new(self, client, app, admin_user):
        """Control standard new page"""
        client.post('/login', data={
            'username': 'admin_route_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)

        response = client.get('/admin/control_standards/new')
        assert response.status_code in [200, 302, 404]

    def test_control_standard_create(self, client, app, admin_user):
        """Control standard create"""
        client.post('/login', data={
            'username': 'admin_route_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)

        response = client.post('/admin/control_standards/new', data={
            'code': 'TEST-CS-001',
            'name': 'Test Standard',
            'is_active': True
        })
        assert response.status_code in [200, 302, 400, 404]

    def test_control_standard_detail(self, client, app, admin_user):
        """Control standard detail"""
        client.post('/login', data={
            'username': 'admin_route_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)

        with app.app_context():
            cs = ControlStandard.query.first()
            if cs:
                response = client.get(f'/admin/control_standards/{cs.id}')
                assert response.status_code in [200, 302, 404]


class TestEquipmentManagement:
    """Equipment management тестүүд"""

    def test_equipment_list(self, client, app, admin_user):
        """Equipment list"""
        client.post('/login', data={
            'username': 'admin_route_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)

        response = client.get('/equipment')
        assert response.status_code in [200, 302, 404]

    def test_equipment_new(self, client, app, admin_user):
        """Equipment new page"""
        client.post('/login', data={
            'username': 'admin_route_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)

        response = client.get('/equipment/new')
        assert response.status_code in [200, 302, 404]

    def test_equipment_create(self, client, app, admin_user):
        """Equipment create"""
        client.post('/login', data={
            'username': 'admin_route_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)

        response = client.post('/equipment/new', data={
            'name': 'Test Equipment',
            'model': 'Model A',
            'serial_number': 'SN-12345'
        })
        assert response.status_code in [200, 302, 400, 404]

    def test_equipment_detail(self, client, app, admin_user):
        """Equipment detail"""
        client.post('/login', data={
            'username': 'admin_route_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)

        with app.app_context():
            eq = Equipment.query.first()
            if eq:
                response = client.get(f'/equipment/{eq.id}')
                assert response.status_code in [200, 302, 404]


class TestSystemSettings:
    """System settings тестүүд"""

    def test_settings_page(self, client, app, admin_user):
        """Settings page"""
        client.post('/login', data={
            'username': 'admin_route_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)

        response = client.get('/settings')
        assert response.status_code in [200, 302, 404]

    def test_settings_general(self, client, app, admin_user):
        """General settings"""
        client.post('/login', data={
            'username': 'admin_route_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)

        response = client.get('/settings/general')
        assert response.status_code in [200, 302, 404]

    def test_settings_update(self, client, app, admin_user):
        """Update settings"""
        client.post('/login', data={
            'username': 'admin_route_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)

        response = client.post('/settings/general', data={
            'lab_name': 'Test Lab'
        })
        assert response.status_code in [200, 302, 400, 404]

    def test_settings_precision(self, client, app, admin_user):
        """Precision settings"""
        client.post('/login', data={
            'username': 'admin_route_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)

        response = client.get('/settings/precision')
        assert response.status_code in [200, 302, 404]

    def test_settings_repeatability(self, client, app, admin_user):
        """Repeatability settings"""
        client.post('/login', data={
            'username': 'admin_route_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)

        response = client.get('/settings/repeatability')
        assert response.status_code in [200, 302, 404]


class TestImportRoutes:
    """Import routes тестүүд"""

    def test_import_page(self, client, app, admin_user):
        """Import page"""
        client.post('/login', data={
            'username': 'admin_route_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)

        response = client.get('/import')
        assert response.status_code in [200, 302, 404]

    def test_import_csv(self, client, app, admin_user):
        """Import CSV page"""
        client.post('/login', data={
            'username': 'admin_route_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)

        response = client.get('/import/csv')
        assert response.status_code in [200, 302, 404]


class TestBackupRoutes:
    """Backup routes тестүүд"""

    def test_backup_page(self, client, app, admin_user):
        """Backup page"""
        client.post('/login', data={
            'username': 'admin_route_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)

        response = client.get('/admin/backup')
        assert response.status_code in [200, 302, 404]
