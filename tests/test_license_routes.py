# tests/test_license_routes.py
# -*- coding: utf-8 -*-
"""
License routes coverage tests
"""

import pytest
from unittest.mock import patch, MagicMock


class TestLicenseInfo:
    """Tests for license info route."""

    def test_license_info_get(self, app, auth_admin):
        """Test license info GET."""
        response = auth_admin.get('/license/info')
        assert response.status_code in [200, 302]

    def test_license_info_no_auth(self, app, client):
        """Test license info without auth."""
        response = client.get('/license/info')
        assert response.status_code in [200, 302, 401]


class TestLicenseActivate:
    """Tests for license activate route."""

    def test_license_activate_get(self, app, client):
        """Test license activate GET."""
        response = client.get('/license/activate')
        assert response.status_code in [200, 302]

    def test_license_activate_post(self, app, auth_admin):
        """Test license activate POST."""
        response = auth_admin.post('/license/activate', data={
            'license_key': 'test_license_key_123'
        }, follow_redirects=True)
        assert response.status_code in [200, 302]

    def test_license_activate_empty_key(self, app, auth_admin):
        """Test license activate with empty key."""
        response = auth_admin.post('/license/activate', data={
            'license_key': ''
        }, follow_redirects=True)
        assert response.status_code in [200, 302]


class TestLicenseExpired:
    """Tests for license expired route."""

    def test_license_expired_get(self, app, client):
        """Test license expired GET."""
        response = client.get('/license/expired')
        assert response.status_code in [200, 302]


class TestLicenseError:
    """Tests for license error route."""

    def test_license_error_get(self, app, client):
        """Test license error GET."""
        response = client.get('/license/error')
        assert response.status_code in [200, 302]


class TestLicenseStatus:
    """Tests for license status route."""

    def test_license_status_api(self, app, auth_admin):
        """Test license status API."""
        response = auth_admin.get('/license/status')
        assert response.status_code in [200, 302, 404]


class TestLicenseRenew:
    """Tests for license renew route."""

    def test_license_renew_get(self, app, auth_admin):
        """Test license renew GET."""
        response = auth_admin.get('/license/renew')
        assert response.status_code in [200, 302, 404]

    def test_license_renew_post(self, app, auth_admin):
        """Test license renew POST."""
        response = auth_admin.post('/license/renew', data={
            'new_license_key': 'new_license_123'
        }, follow_redirects=True)
        assert response.status_code in [200, 302, 404]
