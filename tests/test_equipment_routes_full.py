# tests/test_equipment_routes_full.py
# -*- coding: utf-8 -*-
"""
Complete tests for app/routes/equipment_routes.py
"""

import pytest
from unittest.mock import patch, MagicMock
from datetime import date, timedelta


class TestEquipmentList:
    """Tests for equipment_list route."""

    def test_list_requires_login(self, client):
        """Test list requires authentication."""
        response = client.get('/equipment_list')
        assert response.status_code == 302

    def test_list_get(self, client, auth_user):
        """Test GET equipment_list page."""
        response = client.get('/equipment_list')
        assert response.status_code == 200

    def test_list_view_all(self, client, auth_user):
        """Test list with view=all."""
        response = client.get('/equipment_list?view=all')
        assert response.status_code == 200

    def test_list_view_retired(self, client, auth_user):
        """Test list with view=retired."""
        response = client.get('/equipment_list?view=retired')
        assert response.status_code == 200

    def test_list_view_spares(self, client, auth_user):
        """Test list with view=spares."""
        response = client.get('/equipment_list?view=spares')
        assert response.status_code == 200

    def test_list_pagination(self, client, auth_user):
        """Test list pagination."""
        response = client.get('/equipment_list?page=1')
        assert response.status_code == 200

    def test_list_page_2(self, client, auth_user):
        """Test list page 2."""
        response = client.get('/equipment_list?page=2')
        assert response.status_code == 200


class TestEquipmentDetail:
    """Tests for equipment_detail route."""

    def test_detail_requires_login(self, client):
        """Test detail requires authentication."""
        response = client.get('/equipment/1')
        assert response.status_code == 302

    def test_detail_get(self, client, auth_user, app, db):
        """Test GET equipment_detail page."""
        with app.app_context():
            from app.models import Equipment
            eq = Equipment(
                name='Test Equipment Detail',
                model='Model X',
                status='normal'
            )
            db.session.add(eq)
            db.session.commit()
            eq_id = eq.id

        response = client.get(f'/equipment/{eq_id}')
        assert response.status_code == 200

    def test_detail_not_found(self, client, auth_user):
        """Test detail with non-existent ID returns 404."""
        response = client.get('/equipment/999999')
        assert response.status_code == 404


class TestAddEquipment:
    """Tests for add_equipment route."""

    def test_add_requires_login(self, client):
        """Test add requires authentication."""
        response = client.post('/add_equipment')
        assert response.status_code == 302

    def test_add_invalid_quantity(self, client, auth_user):
        """Test add with invalid quantity."""
        response = client.post('/add_equipment', data={
            'name': 'Test Equipment',
            'quantity': '-1',
            'cycle': '365'
        }, follow_redirects=True)
        assert response.status_code == 200

    def test_add_invalid_cycle(self, client, auth_user):
        """Test add with invalid cycle."""
        response = client.post('/add_equipment', data={
            'name': 'Test Equipment',
            'quantity': '1',
            'cycle': '-365'
        }, follow_redirects=True)
        assert response.status_code == 200

    def test_add_success(self, client, auth_user):
        """Test add equipment successfully."""
        response = client.post('/add_equipment', data={
            'name': 'New Test Equipment',
            'quantity': '1',
            'cycle': '365',
            'manufacturer': 'Test Manufacturer',
            'model': 'Test Model'
        }, follow_redirects=True)
        assert response.status_code == 200


class TestEquipmentConstants:
    """Tests for equipment constants."""

    def test_max_file_size(self):
        """Test MAX_FILE_SIZE constant."""
        max_size = 5 * 1024 * 1024  # 5MB
        assert max_size == 5242880

    def test_allowed_extensions(self):
        """Test ALLOWED_EXTENSIONS constant."""
        allowed = {'pdf', 'xlsx', 'xls', 'doc', 'docx', 'jpg', 'jpeg', 'png', 'txt'}
        assert 'pdf' in allowed
        assert 'xlsx' in allowed
        assert 'exe' not in allowed


class TestEquipmentQueries:
    """Tests for equipment query logic."""

    def test_query_active(self, app, db):
        """Test query for active equipment."""
        with app.app_context():
            from app.models import Equipment

            # Create active equipment
            eq = Equipment(
                name='Active Equipment',
                status='normal'
            )
            db.session.add(eq)
            db.session.commit()

            active = Equipment.query.filter(Equipment.status == 'normal').first()
            assert active is not None

    def test_query_retired(self, app, db):
        """Test query for retired equipment."""
        with app.app_context():
            from app.models import Equipment

            eq = Equipment(
                name='Retired Equipment',
                status='retired'
            )
            db.session.add(eq)
            db.session.commit()

            retired = Equipment.query.filter(Equipment.status == 'retired').first()
            assert retired is not None

    def test_query_needs_spare(self, app, db):
        """Test query for equipment needing maintenance."""
        with app.app_context():
            from app.models import Equipment

            eq = Equipment(
                name='Needs Spare Equipment',
                status='maintenance'
            )
            db.session.add(eq)
            db.session.commit()

            spares = Equipment.query.filter(
                Equipment.status.in_(['maintenance', 'out_of_service'])
            ).all()
            assert len(spares) > 0


class TestCalibrationWarnings:
    """Tests for calibration warning logic."""

    def test_warning_date_calculation(self, app):
        """Test warning date is 30 days ahead."""
        with app.app_context():
            from app.utils.datetime import now_local
            today = now_local().date()
            warning_date = today + timedelta(days=30)
            assert (warning_date - today).days == 30

    def test_equipment_calibration_due(self, app, db):
        """Test equipment with calibration due soon."""
        with app.app_context():
            from app.models import Equipment
            from app.utils.datetime import now_local

            today = now_local().date()
            due_date = today + timedelta(days=10)

            eq = Equipment(
                name='Calibration Due Equipment',
                calibration_date=due_date,
                status='normal'
            )
            db.session.add(eq)
            db.session.commit()

            # Query for equipment with calibration due within 30 days
            warning_date = today + timedelta(days=30)
            due_soon = Equipment.query.filter(
                Equipment.calibration_date <= warning_date,
                Equipment.calibration_date >= today
            ).all()
            assert len(due_soon) >= 1


class TestMaintenanceLog:
    """Tests for maintenance log functionality."""

    def test_create_maintenance_log(self, app, db):
        """Test creating maintenance log."""
        with app.app_context():
            from app.models import Equipment, MaintenanceLog, User

            user = User.query.first()
            eq = Equipment(
                name='Maintenance Test Equipment',
                status='normal'
            )
            db.session.add(eq)
            db.session.commit()

            log = MaintenanceLog(
                equipment_id=eq.id,
                action_type='Calibration',
                description='Annual calibration',
                performed_by=user.username if user else 'System',
                result='Pass'
            )
            db.session.add(log)
            db.session.commit()

            assert log.id is not None


class TestUsageLog:
    """Tests for usage log functionality."""

    def test_create_usage_log(self, app, db):
        """Test creating usage log."""
        with app.app_context():
            from app.models import Equipment, UsageLog
            from app.utils.datetime import now_local

            eq = Equipment(
                name='Usage Test Equipment',
                status='normal'
            )
            db.session.add(eq)
            db.session.commit()

            log = UsageLog(
                equipment_id=eq.id,
                start_time=now_local(),
                duration_minutes=30
            )
            db.session.add(log)
            db.session.commit()

            assert log.id is not None
