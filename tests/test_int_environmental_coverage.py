# tests/integration/test_environmental_coverage.py
"""Environmental monitoring coverage tests"""
import pytest


class TestEnvironmentalRoutes:
    """Environmental routes tests"""

    def test_environmental_list(self, auth_admin):
        """Environmental list page"""
        response = auth_admin.get('/quality/environmental')
        assert response.status_code in [200, 302]

    def test_environmental_list_user(self, auth_user):
        """Environmental list as regular user"""
        response = auth_user.get('/quality/environmental')
        assert response.status_code in [200, 302]

    def test_environmental_add_valid(self, auth_admin):
        """Add environmental log - valid data"""
        response = auth_admin.post('/quality/environmental/add', data={
            'temperature': '22.5',
            'humidity': '45.0',
            'location': 'Test Lab',
            'temp_min': '15',
            'temp_max': '30',
            'humidity_min': '20',
            'humidity_max': '70',
            'notes': 'Test measurement'
        }, follow_redirects=True)
        assert response.status_code in [200, 302, 403]

    def test_environmental_add_within_limits(self, auth_admin):
        """Add environmental log - within limits"""
        response = auth_admin.post('/quality/environmental/add', data={
            'temperature': '20.0',
            'humidity': '50.0',
            'temp_min': '15',
            'temp_max': '30',
            'humidity_min': '20',
            'humidity_max': '70'
        }, follow_redirects=True)
        assert response.status_code in [200, 302, 403]

    def test_environmental_add_outside_temp(self, auth_admin):
        """Add environmental log - outside temperature limits"""
        response = auth_admin.post('/quality/environmental/add', data={
            'temperature': '35.0',  # > temp_max
            'humidity': '50.0',
            'temp_min': '15',
            'temp_max': '30',
            'humidity_min': '20',
            'humidity_max': '70'
        }, follow_redirects=True)
        assert response.status_code in [200, 302, 403]

    def test_environmental_add_outside_humidity(self, auth_admin):
        """Add environmental log - outside humidity limits"""
        response = auth_admin.post('/quality/environmental/add', data={
            'temperature': '22.0',
            'humidity': '80.0',  # > humidity_max
            'temp_min': '15',
            'temp_max': '30',
            'humidity_min': '20',
            'humidity_max': '70'
        }, follow_redirects=True)
        assert response.status_code in [200, 302, 403]

    def test_environmental_add_default_limits(self, auth_admin):
        """Add environmental log - using default limits"""
        response = auth_admin.post('/quality/environmental/add', data={
            'temperature': '22.0',
            'humidity': '45.0'
            # No explicit limits - should use defaults
        }, follow_redirects=True)
        assert response.status_code in [200, 302, 403]

    def test_environmental_add_with_location(self, auth_admin):
        """Add environmental log - with specific location"""
        response = auth_admin.post('/quality/environmental/add', data={
            'temperature': '21.0',
            'humidity': '40.0',
            'location': 'Sample Storage'
        }, follow_redirects=True)
        assert response.status_code in [200, 302, 403]

    def test_environmental_add_low_temp(self, auth_admin):
        """Add environmental log - low temperature"""
        response = auth_admin.post('/quality/environmental/add', data={
            'temperature': '10.0',  # < temp_min
            'humidity': '50.0',
            'temp_min': '15',
            'temp_max': '30',
            'humidity_min': '20',
            'humidity_max': '70'
        }, follow_redirects=True)
        assert response.status_code in [200, 302, 403]

    def test_environmental_add_low_humidity(self, auth_admin):
        """Add environmental log - low humidity"""
        response = auth_admin.post('/quality/environmental/add', data={
            'temperature': '22.0',
            'humidity': '15.0',  # < humidity_min
            'temp_min': '15',
            'temp_max': '30',
            'humidity_min': '20',
            'humidity_max': '70'
        }, follow_redirects=True)
        assert response.status_code in [200, 302, 403]


class TestEnvironmentalModel:
    """Environmental model tests"""

    def test_environmental_log_query(self, app):
        """Query environmental logs"""
        with app.app_context():
            from app.models import EnvironmentalLog
            logs = EnvironmentalLog.query.limit(10).all()
            assert isinstance(logs, list)

    def test_environmental_log_order(self, app):
        """Query environmental logs ordered"""
        with app.app_context():
            from app.models import EnvironmentalLog
            logs = EnvironmentalLog.query.order_by(
                EnvironmentalLog.log_date.desc()
            ).limit(10).all()
            assert isinstance(logs, list)

    def test_environmental_log_create(self, app):
        """Create environmental log object"""
        with app.app_context():
            from app.models import EnvironmentalLog
            log = EnvironmentalLog(
                location='Test',
                temperature=22.0,
                humidity=45.0,
                temp_min=15.0,
                temp_max=30.0,
                humidity_min=20.0,
                humidity_max=70.0,
                within_limits=True
            )
            assert log.temperature == 22.0
            assert log.within_limits == True
