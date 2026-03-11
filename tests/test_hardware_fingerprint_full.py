# tests/test_hardware_fingerprint_full.py
# -*- coding: utf-8 -*-
"""
Complete tests for app/utils/hardware_fingerprint.py
"""

import pytest
from unittest.mock import patch, MagicMock
import platform


class TestGetMacAddress:
    """Tests for get_mac_address function."""

    def test_returns_string(self, app):
        """Test returns a string."""
        with app.app_context():
            from app.utils.hardware_fingerprint import get_mac_address
            result = get_mac_address()
            assert isinstance(result, str)

    def test_mac_format(self, app):
        """Test MAC address format (xx:xx:xx:xx:xx:xx)."""
        with app.app_context():
            from app.utils.hardware_fingerprint import get_mac_address
            result = get_mac_address()
            if result != "unknown":
                parts = result.split(':')
                assert len(parts) == 6
                for part in parts:
                    assert len(part) == 2

    def test_exception_returns_unknown(self, app):
        """Test exception returns 'unknown'."""
        with app.app_context():
            from app.utils.hardware_fingerprint import get_mac_address
            with patch('uuid.getnode', side_effect=OSError("Test error")):
                result = get_mac_address()
                assert result == "unknown"


class TestGetCpuId:
    """Tests for get_cpu_id function."""

    def test_returns_string(self, app):
        """Test returns a string (may be empty on some systems)."""
        with app.app_context():
            from app.utils.hardware_fingerprint import get_cpu_id
            result = get_cpu_id()
            assert isinstance(result, str)

    @pytest.mark.skipif(platform.system() != 'Windows', reason="Windows only")
    def test_windows_wmic(self, app):
        """Test Windows WMIC command is used."""
        with app.app_context():
            from app.utils.hardware_fingerprint import get_cpu_id
            result = get_cpu_id()
            assert result != "unknown"

    def test_exception_returns_processor_or_unknown(self, app):
        """Test exception returns processor() or 'unknown'."""
        with app.app_context():
            from app.utils.hardware_fingerprint import get_cpu_id
            with patch('subprocess.run', side_effect=OSError("Test error")):
                result = get_cpu_id()
                assert isinstance(result, str)


class TestGetDiskSerial:
    """Tests for get_disk_serial function."""

    def test_returns_string(self, app):
        """Test returns a string."""
        with app.app_context():
            from app.utils.hardware_fingerprint import get_disk_serial
            result = get_disk_serial()
            assert isinstance(result, str)

    @pytest.mark.skipif(platform.system() != 'Windows', reason="Windows only")
    def test_windows_returns_value(self, app):
        """Test Windows returns a value."""
        with app.app_context():
            from app.utils.hardware_fingerprint import get_disk_serial
            result = get_disk_serial()
            assert isinstance(result, str)

    def test_exception_returns_unknown(self, app):
        """Test exception returns 'unknown'."""
        with app.app_context():
            from app.utils.hardware_fingerprint import get_disk_serial
            with patch('subprocess.run', side_effect=OSError("Test error")):
                result = get_disk_serial()
                assert result == "unknown"


class TestGetMotherboardSerial:
    """Tests for get_motherboard_serial function."""

    def test_returns_string(self, app):
        """Test returns a string."""
        with app.app_context():
            from app.utils.hardware_fingerprint import get_motherboard_serial
            result = get_motherboard_serial()
            assert isinstance(result, str)

    @pytest.mark.skipif(platform.system() != 'Windows', reason="Windows only")
    def test_windows_returns_value(self, app):
        """Test Windows returns a value."""
        with app.app_context():
            from app.utils.hardware_fingerprint import get_motherboard_serial
            result = get_motherboard_serial()
            assert isinstance(result, str)

    def test_exception_returns_unknown(self, app):
        """Test exception returns 'unknown'."""
        with app.app_context():
            from app.utils.hardware_fingerprint import get_motherboard_serial
            with patch('subprocess.run', side_effect=OSError("Test error")):
                result = get_motherboard_serial()
                assert result == "unknown"


class TestGetHostname:
    """Tests for get_hostname function."""

    def test_returns_string(self, app):
        """Test returns a string."""
        with app.app_context():
            from app.utils.hardware_fingerprint import get_hostname
            result = get_hostname()
            assert isinstance(result, str)

    def test_not_empty(self, app):
        """Test returns non-empty string."""
        with app.app_context():
            from app.utils.hardware_fingerprint import get_hostname
            result = get_hostname()
            assert len(result) > 0

    def test_exception_returns_unknown(self, app):
        """Test exception returns 'unknown'."""
        with app.app_context():
            from app.utils.hardware_fingerprint import get_hostname
            with patch('platform.node', side_effect=OSError("Test error")):
                result = get_hostname()
                assert result == "unknown"


class TestGenerateHardwareId:
    """Tests for generate_hardware_id function."""

    def test_returns_string(self, app):
        """Test returns a string."""
        with app.app_context():
            from app.utils.hardware_fingerprint import generate_hardware_id
            result = generate_hardware_id()
            assert isinstance(result, str)

    def test_returns_64_char_hex(self, app):
        """Test returns 64 character hex string (SHA256)."""
        with app.app_context():
            from app.utils.hardware_fingerprint import generate_hardware_id
            result = generate_hardware_id()
            assert len(result) == 64
            # Check it's valid hex
            int(result, 16)

    def test_consistent_result(self, app):
        """Test returns consistent result on same machine."""
        with app.app_context():
            from app.utils.hardware_fingerprint import generate_hardware_id
            result1 = generate_hardware_id()
            result2 = generate_hardware_id()
            assert result1 == result2


class TestGenerateShortHardwareId:
    """Tests for generate_short_hardware_id function."""

    def test_returns_string(self, app):
        """Test returns a string."""
        with app.app_context():
            from app.utils.hardware_fingerprint import generate_short_hardware_id
            result = generate_short_hardware_id()
            assert isinstance(result, str)

    def test_returns_16_chars(self, app):
        """Test returns 16 characters."""
        with app.app_context():
            from app.utils.hardware_fingerprint import generate_short_hardware_id
            result = generate_short_hardware_id()
            assert len(result) == 16

    def test_uppercase(self, app):
        """Test returns uppercase."""
        with app.app_context():
            from app.utils.hardware_fingerprint import generate_short_hardware_id
            result = generate_short_hardware_id()
            assert result == result.upper()

    def test_consistent_result(self, app):
        """Test returns consistent result."""
        with app.app_context():
            from app.utils.hardware_fingerprint import generate_short_hardware_id
            result1 = generate_short_hardware_id()
            result2 = generate_short_hardware_id()
            assert result1 == result2


class TestGetHardwareInfo:
    """Tests for get_hardware_info function."""

    def test_returns_dict(self, app):
        """Test returns a dictionary."""
        with app.app_context():
            from app.utils.hardware_fingerprint import get_hardware_info
            result = get_hardware_info()
            assert isinstance(result, dict)

    def test_has_required_keys(self, app):
        """Test has all required keys."""
        with app.app_context():
            from app.utils.hardware_fingerprint import get_hardware_info
            result = get_hardware_info()
            required_keys = [
                'hostname', 'mac_address', 'cpu_id', 'disk_serial',
                'motherboard_serial', 'os', 'os_version', 'machine',
                'hardware_id', 'short_id'
            ]
            for key in required_keys:
                assert key in result

    def test_values_are_strings(self, app):
        """Test all values are strings."""
        with app.app_context():
            from app.utils.hardware_fingerprint import get_hardware_info
            result = get_hardware_info()
            for value in result.values():
                assert isinstance(value, str)


class TestVerifyHardwareId:
    """Tests for verify_hardware_id function."""

    def test_matching_id_returns_true(self, app):
        """Test matching ID returns True."""
        with app.app_context():
            from app.utils.hardware_fingerprint import verify_hardware_id, generate_hardware_id
            current_id = generate_hardware_id()
            result = verify_hardware_id(current_id)
            assert result is True

    def test_different_id_returns_false(self, app):
        """Test different ID returns False."""
        with app.app_context():
            from app.utils.hardware_fingerprint import verify_hardware_id
            result = verify_hardware_id("different_id_12345678901234567890")
            assert result is False

    def test_empty_id_returns_false(self, app):
        """Test empty ID returns False."""
        with app.app_context():
            from app.utils.hardware_fingerprint import verify_hardware_id
            result = verify_hardware_id("")
            assert result is False

    def test_with_tolerance_parameter(self, app):
        """Test with tolerance parameter (currently unused)."""
        with app.app_context():
            from app.utils.hardware_fingerprint import verify_hardware_id, generate_hardware_id
            current_id = generate_hardware_id()
            result = verify_hardware_id(current_id, tolerance=2)
            assert result is True
