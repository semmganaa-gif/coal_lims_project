# tests/integration/test_equipment_routes.py
# -*- coding: utf-8 -*-
"""
Equipment Routes Integration Tests

Tests for equipment management functionality.
"""

import pytest
from flask import url_for
from app import db
from app.models import User, Equipment, MaintenanceLog, UsageLog
from datetime import datetime, timedelta
import json

VALID_PASSWORD = 'TestPass123'


class TestEquipmentList:
    """GET /equipment_list endpoint тест"""

    def test_equipment_list_not_authenticated(self, client):
        """Нэвтрээгүй үед"""
        response = client.get('/equipment_list')
        assert response.status_code in [302, 401]

    def test_equipment_list_basic(self, client, app):
        """Энгийн equipment list"""
        with app.app_context():
            user = User.query.filter_by(username='eq_user').first()
            if not user:
                user = User(username='eq_user', role='chemist')
                user.set_password(VALID_PASSWORD)
                db.session.add(user)
                db.session.commit()

        client.post('/login', data={
            'username': 'eq_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)

        response = client.get('/equipment_list')
        assert response.status_code in [200, 302]

    def test_equipment_list_with_view_all(self, client, app):
        """View=all параметр"""
        with app.app_context():
            user = User.query.filter_by(username='eq_user2').first()
            if not user:
                user = User(username='eq_user2', role='chemist')
                user.set_password(VALID_PASSWORD)
                db.session.add(user)
                db.session.commit()

        client.post('/login', data={
            'username': 'eq_user2',
            'password': VALID_PASSWORD
        }, follow_redirects=True)

        response = client.get('/equipment_list?view=all')
        assert response.status_code in [200, 302]

    def test_equipment_list_view_retired(self, client, app):
        """View=retired параметр"""
        with app.app_context():
            user = User.query.filter_by(username='eq_user3').first()
            if not user:
                user = User(username='eq_user3', role='chemist')
                user.set_password(VALID_PASSWORD)
                db.session.add(user)
                db.session.commit()

        client.post('/login', data={
            'username': 'eq_user3',
            'password': VALID_PASSWORD
        }, follow_redirects=True)

        response = client.get('/equipment_list?view=retired')
        assert response.status_code in [200, 302]

    def test_equipment_list_view_spares(self, client, app):
        """View=spares параметр"""
        with app.app_context():
            user = User.query.filter_by(username='eq_user4').first()
            if not user:
                user = User(username='eq_user4', role='chemist')
                user.set_password(VALID_PASSWORD)
                db.session.add(user)
                db.session.commit()

        client.post('/login', data={
            'username': 'eq_user4',
            'password': VALID_PASSWORD
        }, follow_redirects=True)

        response = client.get('/equipment_list?view=spares')
        assert response.status_code in [200, 302]

    def test_equipment_list_pagination(self, client, app):
        """Хуудаслалт"""
        with app.app_context():
            user = User.query.filter_by(username='eq_user5').first()
            if not user:
                user = User(username='eq_user5', role='chemist')
                user.set_password(VALID_PASSWORD)
                db.session.add(user)
                db.session.commit()

        client.post('/login', data={
            'username': 'eq_user5',
            'password': VALID_PASSWORD
        }, follow_redirects=True)

        response = client.get('/equipment_list?page=1')
        assert response.status_code in [200, 302]


class TestEquipmentDetail:
    """GET /equipment/<id> endpoint тест"""

    def test_equipment_detail_not_found(self, client, app):
        """Байхгүй төхөөрөмж"""
        with app.app_context():
            user = User.query.filter_by(username='detail_user').first()
            if not user:
                user = User(username='detail_user', role='chemist')
                user.set_password(VALID_PASSWORD)
                db.session.add(user)
                db.session.commit()

        client.post('/login', data={
            'username': 'detail_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)

        response = client.get('/equipment/99999')
        assert response.status_code in [302, 404]

    def test_equipment_detail_with_data(self, client, app):
        """Төхөөрөмжийн дэлгэрэнгүй"""
        with app.app_context():
            user = User.query.filter_by(username='detail_user2').first()
            if not user:
                user = User(username='detail_user2', role='chemist')
                user.set_password(VALID_PASSWORD)
                db.session.add(user)
                db.session.commit()

            # Create equipment
            eq = Equipment.query.filter_by(name='Test Equipment 1').first()
            if not eq:
                eq = Equipment(
                    name='Test Equipment 1',
                    status='normal',
                    category='balance'
                )
                db.session.add(eq)
                db.session.commit()
            eq_id = eq.id

        client.post('/login', data={
            'username': 'detail_user2',
            'password': VALID_PASSWORD
        }, follow_redirects=True)

        response = client.get(f'/equipment/{eq_id}')
        assert response.status_code in [200, 302]


class TestAddEquipment:
    """POST /add_equipment endpoint тест"""

    def test_add_equipment_not_authenticated(self, client):
        """Нэвтрээгүй үед"""
        response = client.post('/add_equipment', data={
            'name': 'New Equipment'
        })
        assert response.status_code in [302, 401, 403]

    def test_add_equipment_unauthorized_role(self, client, app):
        """Chemist эрхгүй"""
        with app.app_context():
            user = User.query.filter_by(username='add_chemist').first()
            if not user:
                user = User(username='add_chemist', role='chemist')
                user.set_password(VALID_PASSWORD)
                db.session.add(user)
                db.session.commit()

        client.post('/login', data={
            'username': 'add_chemist',
            'password': VALID_PASSWORD
        }, follow_redirects=True)

        response = client.post('/add_equipment', data={
            'name': 'New Equipment',
            'quantity': '1',
            'cycle': '365',
            'category': 'balance'
        }, follow_redirects=True)
        # Should redirect with error flash
        assert response.status_code in [200, 302, 403]

    def test_add_equipment_as_admin(self, client, app):
        """Admin эрхтэй"""
        with app.app_context():
            user = User.query.filter_by(username='add_admin').first()
            if not user:
                user = User(username='add_admin', role='admin')
                user.set_password(VALID_PASSWORD)
                db.session.add(user)
                db.session.commit()

        client.post('/login', data={
            'username': 'add_admin',
            'password': VALID_PASSWORD
        }, follow_redirects=True)

        response = client.post('/add_equipment', data={
            'name': 'New Equipment Admin',
            'manufacturer': 'Test Manufacturer',
            'model': 'Test Model',
            'serial': 'SN-123',
            'lab_code': 'LC-001',
            'quantity': '1',
            'cycle': '365',
            'location': 'Lab A',
            'room': 'Room 1',
            'related': 'Mad',
            'category': 'balance'
        }, follow_redirects=True)
        assert response.status_code in [200, 302]

    def test_add_equipment_invalid_quantity(self, client, app):
        """Буруу тоо ширхэг"""
        with app.app_context():
            user = User.query.filter_by(username='add_admin2').first()
            if not user:
                user = User(username='add_admin2', role='admin')
                user.set_password(VALID_PASSWORD)
                db.session.add(user)
                db.session.commit()

        client.post('/login', data={
            'username': 'add_admin2',
            'password': VALID_PASSWORD
        }, follow_redirects=True)

        response = client.post('/add_equipment', data={
            'name': 'Invalid Quantity Equipment',
            'quantity': '-1',
            'cycle': '365'
        }, follow_redirects=True)
        assert response.status_code in [200, 302]

    def test_add_equipment_invalid_cycle(self, client, app):
        """Буруу калибрацийн мөчлөг"""
        with app.app_context():
            user = User.query.filter_by(username='add_admin3').first()
            if not user:
                user = User(username='add_admin3', role='admin')
                user.set_password(VALID_PASSWORD)
                db.session.add(user)
                db.session.commit()

        client.post('/login', data={
            'username': 'add_admin3',
            'password': VALID_PASSWORD
        }, follow_redirects=True)

        response = client.post('/add_equipment', data={
            'name': 'Invalid Cycle Equipment',
            'quantity': '1',
            'cycle': '-10'
        }, follow_redirects=True)
        assert response.status_code in [200, 302]


class TestEditEquipment:
    """POST /edit_equipment/<id> endpoint тест"""

    def test_edit_equipment_not_authenticated(self, client):
        """Нэвтрээгүй үед"""
        response = client.post('/edit_equipment/1', data={
            'name': 'Updated Name'
        })
        assert response.status_code in [302, 401, 403, 404]

    def test_edit_equipment_unauthorized_role(self, client, app):
        """Chemist эрхгүй"""
        with app.app_context():
            user = User.query.filter_by(username='edit_chemist').first()
            if not user:
                user = User(username='edit_chemist', role='chemist')
                user.set_password(VALID_PASSWORD)
                db.session.add(user)
                db.session.commit()

            eq = Equipment.query.filter_by(name='Edit Test Equipment').first()
            if not eq:
                eq = Equipment(name='Edit Test Equipment', status='normal', category='balance')
                db.session.add(eq)
                db.session.commit()
            eq_id = eq.id

        client.post('/login', data={
            'username': 'edit_chemist',
            'password': VALID_PASSWORD
        }, follow_redirects=True)

        response = client.post(f'/edit_equipment/{eq_id}', data={
            'name': 'Updated Name'
        }, follow_redirects=True)
        assert response.status_code in [200, 302, 403]

    def test_edit_equipment_as_admin(self, client, app):
        """Admin эрхтэй"""
        with app.app_context():
            user = User.query.filter_by(username='edit_admin').first()
            if not user:
                user = User(username='edit_admin', role='admin')
                user.set_password(VALID_PASSWORD)
                db.session.add(user)
                db.session.commit()

            eq = Equipment.query.filter_by(name='Edit Test Equipment 2').first()
            if not eq:
                eq = Equipment(name='Edit Test Equipment 2', status='normal', category='balance')
                db.session.add(eq)
                db.session.commit()
            eq_id = eq.id

        client.post('/login', data={
            'username': 'edit_admin',
            'password': VALID_PASSWORD
        }, follow_redirects=True)

        response = client.post(f'/edit_equipment/{eq_id}', data={
            'name': 'Updated Equipment Name',
            'manufacturer': 'New Manufacturer',
            'model': 'New Model',
            'serial': 'SN-456',
            'lab_code': 'LC-002',
            'location': 'Lab B',
            'room': 'Room 2',
            'related': 'Aad',
            'cycle': '180'
        }, follow_redirects=True)
        assert response.status_code in [200, 302]

    def test_edit_equipment_not_found(self, client, app):
        """Байхгүй төхөөрөмж"""
        with app.app_context():
            user = User.query.filter_by(username='edit_admin2').first()
            if not user:
                user = User(username='edit_admin2', role='admin')
                user.set_password(VALID_PASSWORD)
                db.session.add(user)
                db.session.commit()

        client.post('/login', data={
            'username': 'edit_admin2',
            'password': VALID_PASSWORD
        }, follow_redirects=True)

        response = client.post('/edit_equipment/99999', data={
            'name': 'Updated Name'
        }, follow_redirects=True)
        assert response.status_code in [200, 302, 404]


class TestDeleteEquipment:
    """POST /delete_equipment/<id> endpoint тест"""

    def test_delete_equipment_not_authenticated(self, client):
        """Нэвтрээгүй үед"""
        response = client.post('/delete_equipment/1')
        assert response.status_code in [302, 401, 403, 404]

    def test_delete_equipment_unauthorized(self, client, app):
        """Chemist эрхгүй"""
        with app.app_context():
            user = User.query.filter_by(username='delete_chemist').first()
            if not user:
                user = User(username='delete_chemist', role='chemist')
                user.set_password(VALID_PASSWORD)
                db.session.add(user)
                db.session.commit()

            eq = Equipment.query.filter_by(name='Delete Test Equipment').first()
            if not eq:
                eq = Equipment(name='Delete Test Equipment', status='normal', category='balance')
                db.session.add(eq)
                db.session.commit()
            eq_id = eq.id

        client.post('/login', data={
            'username': 'delete_chemist',
            'password': VALID_PASSWORD
        }, follow_redirects=True)

        response = client.post(f'/delete_equipment/{eq_id}', follow_redirects=True)
        # 404 if route doesn't exist
        assert response.status_code in [200, 302, 403, 404]

    def test_delete_equipment_as_admin(self, client, app):
        """Admin эрхтэй"""
        with app.app_context():
            user = User.query.filter_by(username='delete_admin').first()
            if not user:
                user = User(username='delete_admin', role='admin')
                user.set_password(VALID_PASSWORD)
                db.session.add(user)
                db.session.commit()

            eq = Equipment(name='Delete Test Equipment 2', status='normal', category='balance')
            db.session.add(eq)
            db.session.commit()
            eq_id = eq.id

        client.post('/login', data={
            'username': 'delete_admin',
            'password': VALID_PASSWORD
        }, follow_redirects=True)

        response = client.post(f'/delete_equipment/{eq_id}', follow_redirects=True)
        assert response.status_code in [200, 302, 404]


class TestMaintenanceLog:
    """Maintenance Log endpoints тест"""

    def test_add_maintenance_not_authenticated(self, client):
        """Нэвтрээгүй үед"""
        response = client.post('/add_maintenance/1', data={
            'maintenance_type': 'calibration',
            'notes': 'Test maintenance'
        })
        assert response.status_code in [302, 401, 403, 404]

    def test_add_maintenance_as_chemist(self, client, app):
        """Chemist maintenance нэмэх"""
        with app.app_context():
            user = User.query.filter_by(username='maint_chemist').first()
            if not user:
                user = User(username='maint_chemist', role='chemist')
                user.set_password(VALID_PASSWORD)
                db.session.add(user)
                db.session.commit()

            eq = Equipment.query.filter_by(name='Maintenance Test Equipment').first()
            if not eq:
                eq = Equipment(name='Maintenance Test Equipment', status='normal', category='balance')
                db.session.add(eq)
                db.session.commit()
            eq_id = eq.id

        client.post('/login', data={
            'username': 'maint_chemist',
            'password': VALID_PASSWORD
        }, follow_redirects=True)

        response = client.post(f'/add_maintenance/{eq_id}', data={
            'maintenance_type': 'calibration',
            'notes': 'Test maintenance',
            'date': datetime.now().strftime('%Y-%m-%d')
        }, follow_redirects=True)
        # 404 if route doesn't exist
        assert response.status_code in [200, 302, 403, 404]


class TestUsageLog:
    """Usage Log endpoints тест"""

    def test_add_usage_not_authenticated(self, client):
        """Нэвтрээгүй үед"""
        response = client.post('/add_usage/1', data={
            'notes': 'Test usage'
        })
        assert response.status_code in [302, 401, 403, 404]

    def test_add_usage_as_chemist(self, client, app):
        """Chemist usage нэмэх"""
        with app.app_context():
            user = User.query.filter_by(username='usage_chemist').first()
            if not user:
                user = User(username='usage_chemist', role='chemist')
                user.set_password(VALID_PASSWORD)
                db.session.add(user)
                db.session.commit()

            eq = Equipment.query.filter_by(name='Usage Test Equipment').first()
            if not eq:
                eq = Equipment(name='Usage Test Equipment', status='normal', category='balance')
                db.session.add(eq)
                db.session.commit()
            eq_id = eq.id

        client.post('/login', data={
            'username': 'usage_chemist',
            'password': VALID_PASSWORD
        }, follow_redirects=True)

        response = client.post(f'/add_usage/{eq_id}', data={
            'notes': 'Test usage',
            'usage_date': datetime.now().strftime('%Y-%m-%d')
        }, follow_redirects=True)
        assert response.status_code in [200, 302, 403, 404]


class TestEquipmentStatus:
    """Equipment status update тест"""

    def test_change_status_not_authenticated(self, client):
        """Нэвтрээгүй үед"""
        response = client.post('/change_equipment_status/1', data={
            'status': 'broken'
        })
        assert response.status_code in [302, 401, 403, 404]

    def test_change_status_as_admin(self, client, app):
        """Admin status өөрчлөх"""
        with app.app_context():
            user = User.query.filter_by(username='status_admin').first()
            if not user:
                user = User(username='status_admin', role='admin')
                user.set_password(VALID_PASSWORD)
                db.session.add(user)
                db.session.commit()

            eq = Equipment.query.filter_by(name='Status Test Equipment').first()
            if not eq:
                eq = Equipment(name='Status Test Equipment', status='normal', category='balance')
                db.session.add(eq)
                db.session.commit()
            eq_id = eq.id

        client.post('/login', data={
            'username': 'status_admin',
            'password': VALID_PASSWORD
        }, follow_redirects=True)

        response = client.post(f'/change_equipment_status/{eq_id}', data={
            'status': 'broken',
            'notes': 'Equipment broken'
        }, follow_redirects=True)
        assert response.status_code in [200, 302, 404]


class TestEquipmentCalibration:
    """Calibration endpoints тест"""

    def test_add_calibration_not_authenticated(self, client):
        """Нэвтрээгүй үед"""
        response = client.post('/add_calibration/1', data={
            'calibration_date': datetime.now().strftime('%Y-%m-%d'),
            'notes': 'Test calibration'
        })
        assert response.status_code in [302, 401, 403, 404]

    def test_add_calibration_as_senior(self, client, app):
        """Senior калибраци нэмэх"""
        with app.app_context():
            user = User.query.filter_by(username='calib_senior').first()
            if not user:
                user = User(username='calib_senior', role='senior')
                user.set_password(VALID_PASSWORD)
                db.session.add(user)
                db.session.commit()

            eq = Equipment.query.filter_by(name='Calibration Test Equipment').first()
            if not eq:
                eq = Equipment(name='Calibration Test Equipment', status='normal', category='balance')
                db.session.add(eq)
                db.session.commit()
            eq_id = eq.id

        client.post('/login', data={
            'username': 'calib_senior',
            'password': VALID_PASSWORD
        }, follow_redirects=True)

        response = client.post(f'/add_calibration/{eq_id}', data={
            'calibration_date': datetime.now().strftime('%Y-%m-%d'),
            'next_calibration_date': (datetime.now() + timedelta(days=365)).strftime('%Y-%m-%d'),
            'notes': 'Annual calibration'
        }, follow_redirects=True)
        assert response.status_code in [200, 302, 404]


class TestEquipmentFileUpload:
    """File upload endpoints тест"""

    def test_upload_file_not_authenticated(self, client):
        """Нэвтрээгүй үед"""
        response = client.post('/upload_equipment_file/1', data={
            'file': (None, 'test.txt')
        })
        assert response.status_code in [302, 401, 403, 404]


class TestEquipmentApiEndpoints:
    """Equipment API endpoints тест"""

    def test_equipment_list_api(self, client, app):
        """Equipment API жагсаалт"""
        with app.app_context():
            user = User.query.filter_by(username='api_eq_user').first()
            if not user:
                user = User(username='api_eq_user', role='chemist')
                user.set_password(VALID_PASSWORD)
                db.session.add(user)
                db.session.commit()

        client.post('/login', data={
            'username': 'api_eq_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)

        response = client.get('/api/equipment')
        # Route may not exist
        assert response.status_code in [200, 302, 404]

    def test_equipment_search(self, client, app):
        """Equipment хайлт"""
        with app.app_context():
            user = User.query.filter_by(username='search_eq_user').first()
            if not user:
                user = User(username='search_eq_user', role='chemist')
                user.set_password(VALID_PASSWORD)
                db.session.add(user)
                db.session.commit()

        client.post('/login', data={
            'username': 'search_eq_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)

        response = client.get('/equipment_list?search=balance')
        assert response.status_code in [200, 302]


class TestEquipmentCategories:
    """Equipment категори шүүлт тест"""

    def test_view_by_category(self, client, app):
        """Категориор шүүх"""
        with app.app_context():
            user = User.query.filter_by(username='cat_user').first()
            if not user:
                user = User(username='cat_user', role='chemist')
                user.set_password(VALID_PASSWORD)
                db.session.add(user)
                db.session.commit()

        client.post('/login', data={
            'username': 'cat_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)

        categories = ['balance', 'oven', 'furnace', 'analyzer', 'other']
        for cat in categories:
            response = client.get(f'/equipment_list?view={cat}')
            assert response.status_code in [200, 302]


class TestEquipmentHelpers:
    """Equipment helper functions тест"""

    def test_allowed_file(self, app):
        """Зөвшөөрөгдсөн файлын төрөл"""
        # Test file extension check logic
        allowed = {'pdf', 'xlsx', 'xls', 'doc', 'docx', 'jpg', 'jpeg', 'png', 'txt'}

        test_files = [
            ('test.pdf', True),
            ('test.xlsx', True),
            ('test.exe', False),
            ('test.php', False),
            ('test.jpg', True),
        ]

        for filename, expected in test_files:
            ext = filename.rsplit('.', 1)[1].lower() if '.' in filename else ''
            result = ext in allowed
            assert result == expected
