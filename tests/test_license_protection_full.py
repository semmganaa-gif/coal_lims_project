# tests/test_license_protection_full.py
# -*- coding: utf-8 -*-
"""
Complete tests for app/utils/license_protection.py
"""

import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta
import base64
import json


class TestHashData:
    """Tests for _hash_data function."""

    def test_returns_string(self, app):
        """Test returns a string."""
        with app.app_context():
            from app.utils.license_protection import _hash_data
            result = _hash_data("test data")
            assert isinstance(result, str)

    def test_returns_64_char_hex(self, app):
        """Test returns 64 character hex (SHA256)."""
        with app.app_context():
            from app.utils.license_protection import _hash_data
            result = _hash_data("test data")
            assert len(result) == 64

    def test_consistent_hash(self, app):
        """Test same input gives same hash."""
        with app.app_context():
            from app.utils.license_protection import _hash_data
            result1 = _hash_data("test data")
            result2 = _hash_data("test data")
            assert result1 == result2

    def test_different_input_different_hash(self, app):
        """Test different input gives different hash."""
        with app.app_context():
            from app.utils.license_protection import _hash_data
            result1 = _hash_data("test data 1")
            result2 = _hash_data("test data 2")
            assert result1 != result2


class TestCreateSignature:
    """Tests for _create_signature function."""

    def test_returns_string(self, app):
        """Test returns a string."""
        with app.app_context():
            from app.utils.license_protection import _create_signature
            data = {'company': 'Test', 'expiry': '2025-01-01', 'hardware_id': 'abc123'}
            result = _create_signature(data)
            assert isinstance(result, str)

    def test_returns_32_chars(self, app):
        """Test returns 32 character signature."""
        with app.app_context():
            from app.utils.license_protection import _create_signature
            data = {'company': 'Test', 'expiry': '2025-01-01', 'hardware_id': 'abc123'}
            result = _create_signature(data)
            assert len(result) == 32

    def test_consistent_signature(self, app):
        """Test same data gives same signature."""
        with app.app_context():
            from app.utils.license_protection import _create_signature
            data = {'company': 'Test', 'expiry': '2025-01-01', 'hardware_id': 'abc123'}
            result1 = _create_signature(data)
            result2 = _create_signature(data)
            assert result1 == result2


class TestVerifySignature:
    """Tests for _verify_signature function."""

    def test_valid_signature(self, app):
        """Test valid signature returns True."""
        with app.app_context():
            from app.utils.license_protection import _create_signature, _verify_signature
            data = {'company': 'Test', 'expiry': '2025-01-01', 'hardware_id': 'abc123'}
            signature = _create_signature(data)
            result = _verify_signature(data, signature)
            assert result is True

    def test_invalid_signature(self, app):
        """Test invalid signature returns False."""
        with app.app_context():
            from app.utils.license_protection import _verify_signature
            data = {'company': 'Test', 'expiry': '2025-01-01', 'hardware_id': 'abc123'}
            result = _verify_signature(data, 'invalid_signature')
            assert result is False


class TestLicenseManager:
    """Tests for LicenseManager class."""

    def test_init(self, app):
        """Test LicenseManager initialization."""
        with app.app_context():
            from app.utils.license_protection import LicenseManager
            manager = LicenseManager(app)
            assert manager.app == app

    def test_init_app(self, app):
        """Test init_app method."""
        with app.app_context():
            from app.utils.license_protection import LicenseManager
            manager = LicenseManager()
            manager.init_app(app)
            assert manager.app == app

    def test_get_current_license_no_license(self, app, db):
        """Test get_current_license when no license exists."""
        with app.app_context():
            from app.utils.license_protection import LicenseManager
            manager = LicenseManager(app)
            manager._license_cache = None
            result = manager.get_current_license()
            # May be None if no license in DB

    def test_validate_license_no_license(self, app, db):
        """Test validate_license when no license exists."""
        with app.app_context():
            from app.utils.license_protection import LicenseManager
            manager = LicenseManager(app)
            manager._license_cache = None

            with patch.object(manager, 'get_current_license', return_value=None):
                result = manager.validate_license()
                assert result['valid'] is False
                assert result['error'] == 'LICENSE_NOT_FOUND'

    def test_validate_license_inactive(self, app, db):
        """Test validate_license when license is inactive."""
        with app.app_context():
            from app.utils.license_protection import LicenseManager
            manager = LicenseManager(app)

            mock_license = MagicMock()
            mock_license.is_active = False
            mock_license.id = 1

            with patch.object(manager, 'get_current_license', return_value=mock_license):
                with patch.object(manager, '_log_event'):
                    result = manager.validate_license()
                    assert result['valid'] is False
                    assert result['error'] == 'LICENSE_INACTIVE'

    def test_validate_license_expired(self, app, db):
        """Test validate_license when license is expired."""
        with app.app_context():
            from app.utils.license_protection import LicenseManager
            manager = LicenseManager(app)

            mock_license = MagicMock()
            mock_license.is_active = True
            mock_license.tampering_detected = False
            mock_license.expiry_date = datetime.utcnow() - timedelta(days=1)
            mock_license.id = 1

            with patch.object(manager, 'get_current_license', return_value=mock_license):
                with patch.object(manager, '_log_event'):
                    result = manager.validate_license()
                    assert result['valid'] is False
                    assert result['error'] == 'LICENSE_EXPIRED'

    def test_decode_license_key(self, app):
        """Test _decode_license_key method."""
        with app.app_context():
            from app.utils.license_protection import LicenseManager
            manager = LicenseManager(app)

            # Create a valid encoded license
            data = {'company': 'Test', 'expiry': '2025-12-31'}
            encoded = base64.b64encode(json.dumps(data).encode()).decode()

            result = manager._decode_license_key(encoded)
            assert result['company'] == 'Test'
            assert result['expiry'] == '2025-12-31'

    def test_decode_license_key_invalid(self, app):
        """Test _decode_license_key with invalid key."""
        with app.app_context():
            from app.utils.license_protection import LicenseManager
            manager = LicenseManager(app)

            with pytest.raises(ValueError):
                manager._decode_license_key('not valid base64')

    def test_generate_license_key(self, app):
        """Test generate_license_key method."""
        with app.app_context():
            from app.utils.license_protection import LicenseManager
            manager = LicenseManager(app)

            result = manager.generate_license_key(
                company='Test Company',
                expiry_date='2025-12-31',
                hardware_id='test_hw_id'
            )
            assert isinstance(result, str)
            # Should be valid base64
            decoded = base64.b64decode(result.encode()).decode()
            data = json.loads(decoded)
            assert data['company'] == 'Test Company'

    def test_clear_cache(self, app):
        """Test clear_cache method."""
        with app.app_context():
            from app.utils.license_protection import LicenseManager
            manager = LicenseManager(app)
            manager._license_cache = 'some_cache'
            manager._last_check = datetime.utcnow()

            manager.clear_cache()

            assert manager._license_cache is None
            assert manager._last_check is None


class TestRequireLicenseDecorator:
    """Tests for require_license decorator."""

    def test_decorator_exists(self, app):
        """Test require_license decorator exists."""
        with app.app_context():
            from app.utils.license_protection import require_license
            assert callable(require_license)

    def test_decorated_function(self, app):
        """Test decorated function."""
        with app.app_context():
            from app.utils.license_protection import require_license

            @require_license
            def test_func():
                return 'success'

            # Function should be wrapped
            assert hasattr(test_func, '__wrapped__')


class TestCheckLicenseMiddleware:
    """Tests for check_license_middleware function."""

    def test_skips_static_paths(self, app):
        """Test skips static paths."""
        with app.app_context():
            from app.utils.license_protection import check_license_middleware

            with app.test_request_context('/static/css/style.css'):
                result = check_license_middleware()
                assert result is None  # Should skip


class TestLicenseManagerGlobal:
    """Tests for global license_manager instance."""

    def test_global_instance_exists(self, app):
        """Test global license_manager exists."""
        with app.app_context():
            from app.utils.license_protection import license_manager
            assert license_manager is not None

    def test_global_instance_is_license_manager(self, app):
        """Test global instance is LicenseManager."""
        with app.app_context():
            from app.utils.license_protection import license_manager, LicenseManager
            assert isinstance(license_manager, LicenseManager)
