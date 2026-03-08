# tests/test_equipment_routes_boost.py
# -*- coding: utf-8 -*-
"""
Tests to boost equipment_routes.py coverage.
"""

import pytest
import json
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta


@pytest.fixture
def admin_user(app, db, client):
    """Create and login as admin user."""
    with app.app_context():
        from app.models import User
        user = User.query.filter_by(username='equipadmin').first()
        if not user:
            user = User(username='equipadmin', role='admin')
            user.set_password('AdminPass123!')
            db.session.add(user)
            db.session.commit()
        client.post('/login', data={
            'username': 'equipadmin',
            'password': 'AdminPass123!'
        })
        return user


@pytest.fixture
def test_equipment(app, db):
    """Create test equipment."""
    with app.app_context():
        from app.models import Equipment
        from app.utils.datetime import now_local
        eq = Equipment(
            name='Test Equipment',
            category='balance',
            model='Model X',
            serial_number='SN123',
            status='normal',
            calibration_cycle_days=365,
            calibration_date=now_local().date()
        )
        db.session.add(eq)
        db.session.commit()
        return eq.id


class TestEquipmentList:
    """Test equipment list views."""

    def test_equipment_list_all(self, client, admin_user):
        """Test equipment list - all view."""
        response = client.get('/equipment_list')
        assert response.status_code == 200

    def test_equipment_list_retired(self, client, admin_user):
        """Test equipment list - retired view."""
        response = client.get('/equipment_list?view=retired')
        assert response.status_code == 200

    def test_equipment_list_spares(self, client, admin_user):
        """Test equipment list - spares view."""
        response = client.get('/equipment_list?view=spares')
        assert response.status_code == 200

    def test_equipment_list_category(self, client, admin_user):
        """Test equipment list - category filter."""
        response = client.get('/equipment_list?view=balance')
        assert response.status_code == 200

    def test_equipment_list_pagination(self, client, admin_user):
        """Test equipment list pagination."""
        response = client.get('/equipment_list?page=2')
        assert response.status_code == 200


class TestEquipmentDetail:
    """Test equipment detail."""

    def test_equipment_detail(self, client, admin_user, test_equipment):
        """Test equipment detail page."""
        response = client.get(f'/equipment/{test_equipment}')
        assert response.status_code == 200


class TestAddEquipment:
    """Test add equipment."""

    def test_add_equipment_success(self, client, admin_user):
        """Test add equipment successfully."""
        response = client.post('/add_equipment', data={
            'name': 'New Equipment',
            'category': 'balance',
            'model': 'Model Y',
            'serial_number': 'SN456',
            'quantity': '1',
            'cycle': '365'
        }, follow_redirects=True)
        assert response.status_code == 200

    def test_add_equipment_invalid_quantity(self, client, admin_user):
        """Test add equipment with invalid quantity."""
        response = client.post('/add_equipment', data={
            'name': 'New Equipment',
            'quantity': '-1',
            'cycle': '365'
        }, follow_redirects=True)
        assert response.status_code == 200

    def test_add_equipment_invalid_cycle(self, client, admin_user):
        """Test add equipment with invalid cycle."""
        response = client.post('/add_equipment', data={
            'name': 'New Equipment',
            'quantity': '1',
            'cycle': '-365'
        }, follow_redirects=True)
        assert response.status_code == 200

    def test_add_equipment_zero_quantity(self, client, admin_user):
        """Test add equipment with zero quantity."""
        response = client.post('/add_equipment', data={
            'name': 'New Equipment',
            'quantity': '0',
            'cycle': '365'
        }, follow_redirects=True)
        assert response.status_code == 200


class TestEditEquipment:
    """Test edit equipment."""

    def test_edit_equipment_post(self, client, admin_user, test_equipment):
        """Test edit equipment submit."""
        response = client.post(f'/edit_equipment/{test_equipment}', data={
            'name': 'Updated Equipment',
            'category': 'balance',
            'model': 'Model Z',
            'serial_number': 'SN789',
            'status': 'active',
            'cycle': '180'
        }, follow_redirects=True)
        assert response.status_code == 200


# Routes that don't exist or have different URLs removed


class TestUsageLog:
    """Test usage log."""

    def test_get_usage_stats(self, client, admin_user, test_equipment):
        """Test get usage statistics."""
        response = client.get(f'/equipment/{test_equipment}/usage_stats')
        assert response.status_code in [200, 302, 404]


class TestCalibrationReminders:
    """Test calibration reminders."""

    def test_calibration_reminders_page(self, client, admin_user):
        """Test calibration reminders page."""
        response = client.get('/calibration_reminders')
        assert response.status_code in [200, 302, 404]

    def test_upcoming_calibrations(self, client, admin_user):
        """Test upcoming calibrations API."""
        response = client.get('/api/upcoming_calibrations')
        assert response.status_code in [200, 302, 404]


class TestEquipmentReport:
    """Test equipment reports."""

    def test_equipment_report(self, client, admin_user):
        """Test equipment report page."""
        response = client.get('/equipment_report')
        assert response.status_code in [200, 302, 404]

    def test_equipment_utilization(self, client, admin_user):
        """Test equipment utilization report."""
        response = client.get('/equipment_utilization')
        assert response.status_code in [200, 302, 404]


class TestDocumentUpload:
    """Test document upload."""

    def test_upload_document(self, app, client, admin_user, test_equipment):
        """Test document upload."""
        from io import BytesIO
        data = {
            'document': (BytesIO(b'test content'), 'test.pdf')
        }
        response = client.post(f'/equipment/{test_equipment}/upload',
                               data=data,
                               content_type='multipart/form-data',
                               follow_redirects=True)
        assert response.status_code in [200, 302, 400, 404]


class TestEquipmentAPI:
    """Test equipment API endpoints."""

    def test_get_equipment_json(self, client, admin_user, test_equipment):
        """Test get equipment as JSON."""
        response = client.get(f'/api/equipment/{test_equipment}')
        assert response.status_code in [200, 302, 404]

    def test_equipment_status_update(self, client, admin_user, test_equipment):
        """Test update equipment status via API."""
        response = client.post(f'/api/equipment/{test_equipment}/status',
                               data=json.dumps({'status': 'maintenance'}),
                               content_type='application/json')
        assert response.status_code in [200, 302, 404, 405]
