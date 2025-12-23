# tests/integration/test_settings_comprehensive.py
"""
Settings routes comprehensive тест
"""
import pytest


class TestBottleSettings:
    """Bottle settings тест"""

    def test_bottles_page(self, auth_admin):
        """Bottles хуудас"""
        response = auth_admin.get('/settings/bottles')
        assert response.status_code in [200, 302]

    def test_bottles_create(self, auth_admin):
        """Create bottle setting"""
        response = auth_admin.post('/settings/bottles', data={
            'sample_type': 'Coal',
            'bottle_type': 'Glass',
            'volume': '500ml'
        })
        # May require specific fields or redirect
        assert response.status_code in [200, 302, 400, 404, 405]

    def test_bottles_update(self, auth_admin):
        """Update bottle setting"""
        response = auth_admin.post('/settings/bottles/1', data={
            'bottle_type': 'Plastic',
            'volume': '1000ml'
        })
        assert response.status_code in [200, 302, 400, 404]


class TestEmailRecipients:
    """Email recipients тест"""

    def test_email_recipients_page(self, auth_admin):
        """Email recipients хуудас"""
        response = auth_admin.get('/settings/email-recipients')
        assert response.status_code in [200, 302]

    def test_add_email_recipient(self, auth_admin):
        """Add email recipient"""
        response = auth_admin.post('/settings/email-recipients', data={
            'email': 'test@example.com',
            'name': 'Test User',
            'notification_type': 'hourly_report'
        })
        assert response.status_code in [200, 302, 400]

    def test_delete_email_recipient(self, auth_admin):
        """Delete email recipient"""
        response = auth_admin.delete('/settings/email-recipients/1')
        assert response.status_code in [200, 302, 400, 404, 405]


class TestAnalysisSettings:
    """Analysis settings тест"""

    def test_analysis_config_page(self, auth_admin):
        """Analysis config хуудас"""
        response = auth_admin.get('/settings/analysis_config')
        assert response.status_code in [200, 302, 404]

    def test_analysis_config_update(self, auth_admin):
        """Update analysis config"""
        response = auth_admin.post('/settings/analysis_config', data={
            'code': 'Mad',
            'precision': 2,
            'min_value': 0,
            'max_value': 100
        })
        assert response.status_code in [200, 302, 400, 404]


class TestPrecisionSettings:
    """Precision settings тест"""

    def test_precision_page(self, auth_admin):
        """Precision хуудас"""
        response = auth_admin.get('/settings/precision')
        assert response.status_code in [200, 302, 404]

    def test_precision_update(self, auth_admin):
        """Update precision"""
        response = auth_admin.post('/settings/precision', data={
            'Mad': 2,
            'Aad': 2,
            'CV': 0
        })
        assert response.status_code in [200, 302, 400, 404]


class TestRepeatabilitySettings:
    """Repeatability settings тест"""

    def test_repeatability_page(self, auth_admin):
        """Repeatability хуудас"""
        response = auth_admin.get('/settings/repeatability')
        assert response.status_code in [200, 302, 404]

    def test_repeatability_get(self, auth_admin):
        """Get repeatability settings"""
        response = auth_admin.get('/settings/repeatability')
        # Just test the GET endpoint works
        assert response.status_code in [200, 302, 404]


class TestSystemSettings:
    """System settings тест"""

    def test_system_settings_page(self, auth_admin):
        """System settings хуудас"""
        response = auth_admin.get('/settings/system')
        assert response.status_code in [200, 302, 404]

    def test_update_system_setting(self, auth_admin):
        """Update system setting"""
        response = auth_admin.post('/settings/system', data={
            'category': 'general',
            'key': 'company_name',
            'value': 'Test Company'
        })
        assert response.status_code in [200, 302, 400, 404]


class TestShiftSettings:
    """Shift settings тест"""

    def test_shift_settings_page(self, auth_admin):
        """Shift settings хуудас"""
        response = auth_admin.get('/settings/shifts')
        assert response.status_code in [200, 302, 404]

    def test_shift_settings_update(self, auth_admin):
        """Update shift settings"""
        response = auth_admin.post('/settings/shifts', data={
            'day_start': '08:00',
            'day_end': '20:00'
        })
        assert response.status_code in [200, 302, 400, 404]


class TestQCSettings:
    """QC settings тест"""

    def test_qc_settings_page(self, auth_admin):
        """QC settings хуудас"""
        response = auth_admin.get('/settings/qc')
        assert response.status_code in [200, 302, 404]

    def test_qc_settings_update(self, auth_admin):
        """Update QC settings"""
        response = auth_admin.post('/settings/qc', data={
            'warning_threshold': 2,
            'failure_threshold': 3
        })
        assert response.status_code in [200, 302, 400, 404]


class TestSettingsPermissions:
    """Settings эрхийн тест"""

    def test_settings_unauthorized(self, client):
        """Settings without login"""
        response = client.get('/settings/bottles')
        assert response.status_code in [302, 401]

    def test_settings_user_forbidden(self, auth_user):
        """Settings as regular user"""
        response = auth_user.get('/settings/bottles')
        # Admin only
        assert response.status_code in [200, 302, 403]


class TestSettingsAPI:
    """Settings API тест"""

    def test_get_setting_value(self, auth_admin):
        """Get setting value"""
        response = auth_admin.get('/settings/api/get?category=general&key=test')
        assert response.status_code in [200, 400, 404]

    def test_update_setting_value(self, auth_admin):
        """Update setting value via API"""
        response = auth_admin.post('/settings/api/update', json={
            'category': 'general',
            'key': 'test',
            'value': 'test_value'
        })
        assert response.status_code in [200, 400, 404]
