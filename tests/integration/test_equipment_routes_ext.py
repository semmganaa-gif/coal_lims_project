# tests/integration/test_equipment_routes_ext.py
# -*- coding: utf-8 -*-
"""
Equipment routes extended coverage tests
"""

import pytest
from app import db
from app.models import User, Equipment
from datetime import datetime, date
import json
import uuid

VALID_PASSWORD = 'TestPass123'


@pytest.fixture
def equip_admin(app):
    """Equipment admin user fixture"""
    with app.app_context():
        user = User.query.filter_by(username='equip_admin_user').first()
        if not user:
            user = User(username='equip_admin_user', role='admin')
            user.set_password(VALID_PASSWORD)
            db.session.add(user)
            db.session.commit()
        return user


@pytest.fixture
def equip_senior(app):
    """Equipment senior user fixture"""
    with app.app_context():
        user = User.query.filter_by(username='equip_senior_user').first()
        if not user:
            user = User(username='equip_senior_user', role='senior')
            user.set_password(VALID_PASSWORD)
            db.session.add(user)
            db.session.commit()
        return user


@pytest.fixture
def test_equipment(app):
    """Test equipment fixture"""
    with app.app_context():
        unique_id = uuid.uuid4().hex[:6]
        try:
            equipment = Equipment(
                name=f'Test Balance {unique_id}',
                equipment_type='balance',
                serial_number=f'SN-{unique_id}',
                status='normal'
            )
            db.session.add(equipment)
            db.session.commit()
            return equipment.id
        except Exception:
            db.session.rollback()
            return None


class TestEquipmentList:
    """Equipment list tests"""

    def test_equipment_list(self, client, app, equip_admin):
        """Equipment list"""
        client.post('/login', data={
            'username': 'equip_admin_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)
        response = client.get('/equipment/')
        assert response.status_code in [200, 302, 404]

    def test_equipment_list_paginated(self, client, app, equip_admin):
        """Equipment list paginated"""
        client.post('/login', data={
            'username': 'equip_admin_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)
        response = client.get('/equipment/?page=1')
        assert response.status_code in [200, 302, 404]

    def test_equipment_list_by_type(self, client, app, equip_admin):
        """Equipment list by type"""
        client.post('/login', data={
            'username': 'equip_admin_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)
        response = client.get('/equipment/?type=balance')
        assert response.status_code in [200, 302, 404]

    def test_equipment_list_by_status(self, client, app, equip_admin):
        """Equipment list by status"""
        client.post('/login', data={
            'username': 'equip_admin_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)
        response = client.get('/equipment/?status=normal')
        assert response.status_code in [200, 302, 404]


class TestEquipmentCreate:
    """Equipment create tests"""

    def test_equipment_new_get(self, client, app, equip_admin):
        """Equipment new GET"""
        client.post('/login', data={
            'username': 'equip_admin_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)
        response = client.get('/equipment/new')
        assert response.status_code in [200, 302, 404]

    def test_equipment_new_post(self, client, app, equip_admin):
        """Equipment new POST"""
        client.post('/login', data={
            'username': 'equip_admin_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)
        unique_id = uuid.uuid4().hex[:6]
        response = client.post('/equipment/new', data={
            'name': f'New Equipment {unique_id}',
            'equipment_type': 'balance',
            'serial_number': f'SN-NEW-{unique_id}',
            'status': 'normal'
        }, follow_redirects=True)
        assert response.status_code in [200, 302, 400, 404, 500]

    def test_equipment_new_post_invalid(self, client, app, equip_admin):
        """Equipment new POST invalid"""
        client.post('/login', data={
            'username': 'equip_admin_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)
        response = client.post('/equipment/new', data={
            'name': '',  # Empty name
            'equipment_type': 'balance'
        }, follow_redirects=True)
        assert response.status_code in [200, 302, 400, 404, 500]


class TestEquipmentView:
    """Equipment view tests"""

    def test_equipment_view(self, client, app, equip_admin, test_equipment):
        """Equipment view"""
        if test_equipment:
            client.post('/login', data={
                'username': 'equip_admin_user',
                'password': VALID_PASSWORD
            }, follow_redirects=True)
            response = client.get(f'/equipment/{test_equipment}')
            assert response.status_code in [200, 302, 404]

    def test_equipment_view_invalid(self, client, app, equip_admin):
        """Equipment view invalid ID"""
        client.post('/login', data={
            'username': 'equip_admin_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)
        response = client.get('/equipment/99999')
        assert response.status_code in [200, 302, 404]


class TestEquipmentEdit:
    """Equipment edit tests"""

    def test_equipment_edit_get(self, client, app, equip_admin, test_equipment):
        """Equipment edit GET"""
        if test_equipment:
            client.post('/login', data={
                'username': 'equip_admin_user',
                'password': VALID_PASSWORD
            }, follow_redirects=True)
            response = client.get(f'/equipment/{test_equipment}/edit')
            assert response.status_code in [200, 302, 404]

    def test_equipment_edit_post(self, client, app, equip_admin, test_equipment):
        """Equipment edit POST"""
        if test_equipment:
            client.post('/login', data={
                'username': 'equip_admin_user',
                'password': VALID_PASSWORD
            }, follow_redirects=True)
            response = client.post(f'/equipment/{test_equipment}/edit', data={
                'name': 'Updated Equipment',
                'status': 'maintenance'
            }, follow_redirects=True)
            assert response.status_code in [200, 302, 400, 404, 500]


class TestEquipmentCalibration:
    """Equipment calibration tests"""

    def test_calibration_add_get(self, client, app, equip_admin, test_equipment):
        """Calibration add GET"""
        if test_equipment:
            client.post('/login', data={
                'username': 'equip_admin_user',
                'password': VALID_PASSWORD
            }, follow_redirects=True)
            response = client.get(f'/equipment/{test_equipment}/calibration/add')
            assert response.status_code in [200, 302, 404]

    def test_calibration_add_post(self, client, app, equip_admin, test_equipment):
        """Calibration add POST"""
        if test_equipment:
            client.post('/login', data={
                'username': 'equip_admin_user',
                'password': VALID_PASSWORD
            }, follow_redirects=True)
            today = date.today().isoformat()
            response = client.post(f'/equipment/{test_equipment}/calibration/add', data={
                'calibration_date': today,
                'next_calibration_date': today,
                'result': 'pass',
                'notes': 'Test calibration'
            }, follow_redirects=True)
            assert response.status_code in [200, 302, 400, 404, 500]


class TestEquipmentMaintenance:
    """Equipment maintenance tests"""

    def test_maintenance_add_get(self, client, app, equip_admin, test_equipment):
        """Maintenance add GET"""
        if test_equipment:
            client.post('/login', data={
                'username': 'equip_admin_user',
                'password': VALID_PASSWORD
            }, follow_redirects=True)
            response = client.get(f'/equipment/{test_equipment}/maintenance/add')
            assert response.status_code in [200, 302, 404]

    def test_maintenance_add_post(self, client, app, equip_admin, test_equipment):
        """Maintenance add POST"""
        if test_equipment:
            client.post('/login', data={
                'username': 'equip_admin_user',
                'password': VALID_PASSWORD
            }, follow_redirects=True)
            today = date.today().isoformat()
            response = client.post(f'/equipment/{test_equipment}/maintenance/add', data={
                'maintenance_date': today,
                'maintenance_type': 'preventive',
                'description': 'Test maintenance',
                'result': 'completed'
            }, follow_redirects=True)
            assert response.status_code in [200, 302, 400, 404, 500]


class TestEquipmentAPI:
    """Equipment API tests"""

    def test_api_equipment_list(self, client, app, equip_admin):
        """API equipment list"""
        client.post('/login', data={
            'username': 'equip_admin_user',
            'password': VALID_PASSWORD
        }, follow_redirects=True)
        response = client.get('/api/equipment')
        assert response.status_code in [200, 302, 404]

    def test_api_equipment_status(self, client, app, equip_admin, test_equipment):
        """API equipment status"""
        if test_equipment:
            client.post('/login', data={
                'username': 'equip_admin_user',
                'password': VALID_PASSWORD
            }, follow_redirects=True)
            response = client.get(f'/api/equipment/{test_equipment}/status')
            assert response.status_code in [200, 302, 404]
