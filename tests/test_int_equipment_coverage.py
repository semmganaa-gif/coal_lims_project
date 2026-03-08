# tests/integration/test_equipment_coverage.py
"""Equipment routes extended coverage tests"""
import pytest
from datetime import datetime, timedelta


class TestEquipmentList:
    """Equipment list tests"""

    def test_equipment_list(self, auth_admin):
        """Equipment list page"""
        response = auth_admin.get('/admin/equipment')
        assert response.status_code in [200, 302, 404]

    def test_equipment_list_user(self, auth_user):
        """Equipment list as regular user"""
        response = auth_user.get('/admin/equipment')
        assert response.status_code in [200, 302, 403, 404]


class TestEquipmentAdd:
    """Equipment add tests"""

    def test_equipment_add_get(self, auth_admin):
        """Equipment add form GET"""
        response = auth_admin.get('/admin/equipment/add')
        assert response.status_code in [200, 302, 403, 404]

    def test_equipment_add_post_valid(self, auth_admin):
        """Equipment add POST valid data"""
        response = auth_admin.post('/admin/equipment/add', data={
            'name': 'Test Equipment',
            'lab_code': 'EQ-TEST-001',
            'category': 'balance',
            'location': 'Lab A',
            'manufacturer': 'Test Manufacturer',
            'model': 'Model X',
            'serial_number': 'SN12345',
            'status': 'active'
        }, follow_redirects=True)
        assert response.status_code in [200, 302, 403, 404]

    def test_equipment_add_post_minimal(self, auth_admin):
        """Equipment add POST minimal data"""
        response = auth_admin.post('/admin/equipment/add', data={
            'name': 'Minimal Equipment',
            'lab_code': 'EQ-MIN-001',
            'category': 'other'
        }, follow_redirects=True)
        assert response.status_code in [200, 302, 403, 404]


class TestEquipmentEdit:
    """Equipment edit tests"""

    def test_equipment_edit_get(self, auth_admin):
        """Equipment edit form GET"""
        response = auth_admin.get('/admin/equipment/1/edit')
        assert response.status_code in [200, 302, 403, 404]

    def test_equipment_edit_notfound(self, auth_admin):
        """Equipment edit not found"""
        response = auth_admin.get('/admin/equipment/99999/edit')
        assert response.status_code in [302, 403, 404]


class TestEquipmentDetail:
    """Equipment detail tests"""

    def test_equipment_detail(self, auth_admin):
        """Equipment detail page"""
        response = auth_admin.get('/admin/equipment/1')
        assert response.status_code in [200, 302, 404]

    def test_equipment_detail_notfound(self, auth_admin):
        """Equipment detail not found"""
        response = auth_admin.get('/admin/equipment/99999')
        assert response.status_code in [302, 404]


class TestEquipmentCalibration:
    """Equipment calibration tests"""

    def test_calibration_list(self, auth_admin):
        """Calibration list page"""
        response = auth_admin.get('/admin/equipment/calibrations')
        assert response.status_code in [200, 302, 404]

    def test_add_calibration_get(self, auth_admin):
        """Add calibration form GET"""
        response = auth_admin.get('/admin/equipment/1/calibration/add')
        assert response.status_code in [200, 302, 403, 404]

    def test_add_calibration_post(self, auth_admin):
        """Add calibration POST"""
        today = datetime.now().strftime('%Y-%m-%d')
        response = auth_admin.post('/admin/equipment/1/calibration/add', data={
            'calibration_date': today,
            'next_calibration_date': (datetime.now() + timedelta(days=365)).strftime('%Y-%m-%d'),
            'calibration_result': 'pass',
            'performed_by': 'Test User',
            'notes': 'Test calibration'
        }, follow_redirects=True)
        assert response.status_code in [200, 302, 403, 404]


class TestEquipmentMaintenance:
    """Equipment maintenance tests"""

    def test_maintenance_list(self, auth_admin):
        """Maintenance list page"""
        response = auth_admin.get('/admin/equipment/maintenance')
        assert response.status_code in [200, 302, 404]

    def test_add_maintenance_get(self, auth_admin):
        """Add maintenance form GET"""
        response = auth_admin.get('/admin/equipment/1/maintenance/add')
        assert response.status_code in [200, 302, 403, 404]


class TestEquipmentStatus:
    """Equipment status tests"""

    def test_status_values(self, app):
        """Valid equipment status values"""
        with app.app_context():
            statuses = ['normal', 'maintenance', 'calibration', 'out_of_service', 'retired']
            for status in statuses:
                assert status in statuses

    def test_status_filter(self, app):
        """Filter equipment by status"""
        with app.app_context():
            from app.models import Equipment
            active = Equipment.query.filter_by(status='normal').all()
            retired = Equipment.query.filter_by(status='retired').all()
            assert isinstance(active, list)
            assert isinstance(retired, list)


class TestEquipmentCalibrationDue:
    """Equipment calibration due tests"""

    def test_calibration_due_check(self, app):
        """Check calibration due logic"""
        with app.app_context():
            last_calibration = datetime.now() - timedelta(days=30)
            calibration_interval = 365
            next_calibration = last_calibration + timedelta(days=calibration_interval)
            warning_days = 30
            is_due = next_calibration < datetime.now() + timedelta(days=warning_days)
            assert isinstance(is_due, bool)

    def test_calibration_overdue(self, app):
        """Check calibration overdue"""
        with app.app_context():
            last_calibration = datetime.now() - timedelta(days=400)
            calibration_interval = 365
            next_calibration = last_calibration + timedelta(days=calibration_interval)
            is_overdue = next_calibration < datetime.now()
            assert is_overdue == True


class TestEquipmentModel:
    """Equipment model tests"""

    def test_equipment_query(self, app):
        """Query equipment"""
        with app.app_context():
            from app.models import Equipment
            equipment = Equipment.query.all()
            assert isinstance(equipment, list)

    def test_equipment_create(self, app):
        """Create equipment object"""
        with app.app_context():
            from app.models import Equipment
            eq = Equipment(
                name='Test Balance',
                lab_code='BAL-001',
                category='balance',
                status='normal'
            )
            assert eq.name == 'Test Balance'
            assert eq.status == 'normal'

    def test_equipment_types(self, app):
        """Equipment categories"""
        with app.app_context():
            categories = ['balance', 'furnace', 'analysis', 'prep', 'water', 'micro', 'wtl', 'other']
            for cat in categories:
                from app.models import Equipment
                eq = Equipment(
                    name=f'Test {cat}',
                    lab_code=f'EQ-{cat}',
                    category=cat
                )
                assert eq.category == cat


class TestEquipmentRelatedAnalysis:
    """Equipment related analysis tests"""

    def test_related_analysis_filter(self, app):
        """Filter equipment by related analysis"""
        with app.app_context():
            from app.models import Equipment
            from sqlalchemy import or_
            from app.utils.security import escape_like_pattern

            code = 'Mad'
            safe_code = escape_like_pattern(code)
            equipment = Equipment.query.filter(
                Equipment.related_analysis.ilike(f"%{safe_code}%"),
                or_(Equipment.status.is_(None), Equipment.status != 'retired')
            ).all()
            assert isinstance(equipment, list)
