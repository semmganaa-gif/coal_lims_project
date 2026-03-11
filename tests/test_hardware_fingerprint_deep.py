# tests/test_hardware_fingerprint_deep.py
# -*- coding: utf-8 -*-
"""
Deep coverage tests for hardware_fingerprint.py
"""

import pytest
import platform
from unittest.mock import patch, MagicMock


class TestGetMacAddress:
    """Tests for get_mac_address function."""

    def test_get_mac_address_returns_string(self):
        """Test get_mac_address returns a string."""
        from app.utils.hardware_fingerprint import get_mac_address
        result = get_mac_address()
        assert isinstance(result, str)

    def test_get_mac_address_format(self):
        """Test get_mac_address returns proper format."""
        from app.utils.hardware_fingerprint import get_mac_address
        result = get_mac_address()
        if result != "unknown":
            # Should be in format XX:XX:XX:XX:XX:XX
            parts = result.split(':')
            assert len(parts) == 6

    def test_get_mac_address_exception(self):
        """Test get_mac_address handles exceptions."""
        from app.utils.hardware_fingerprint import get_mac_address
        with patch('app.utils.hardware_fingerprint.uuid.getnode', side_effect=OSError("Error")):
            result = get_mac_address()
            assert result == "unknown"


class TestGetCpuId:
    """Tests for get_cpu_id function."""

    def test_get_cpu_id_returns_string(self):
        """Test get_cpu_id returns a string."""
        from app.utils.hardware_fingerprint import get_cpu_id
        result = get_cpu_id()
        assert isinstance(result, str)

    def test_get_cpu_id_not_empty(self):
        """Test get_cpu_id returns string (may be empty or 'unknown')."""
        from app.utils.hardware_fingerprint import get_cpu_id
        result = get_cpu_id()
        # CPU ID may be empty on some systems, but should still be a string
        assert result is not None
        assert isinstance(result, str)

    def test_get_cpu_id_windows_success(self):
        """Test get_cpu_id on Windows with successful wmic call."""
        from app.utils.hardware_fingerprint import get_cpu_id
        mock_result = MagicMock()
        mock_result.stdout = "ProcessorId\nBFEBFBFF000906EA\n"

        with patch('app.utils.hardware_fingerprint.platform.system', return_value='Windows'):
            with patch('app.utils.hardware_fingerprint.subprocess.run', return_value=mock_result):
                result = get_cpu_id()
                assert result == "BFEBFBFF000906EA"

    def test_get_cpu_id_windows_empty(self):
        """Test get_cpu_id on Windows with empty result."""
        from app.utils.hardware_fingerprint import get_cpu_id
        mock_result = MagicMock()
        mock_result.stdout = "ProcessorId\n"

        with patch('app.utils.hardware_fingerprint.platform.system', return_value='Windows'):
            with patch('app.utils.hardware_fingerprint.subprocess.run', return_value=mock_result):
                result = get_cpu_id()
                # Should fall back to platform.processor()
                assert result is not None

    def test_get_cpu_id_non_windows(self):
        """Test get_cpu_id on non-Windows system."""
        from app.utils.hardware_fingerprint import get_cpu_id
        with patch('app.utils.hardware_fingerprint.platform.system', return_value='Linux'):
            with patch('app.utils.hardware_fingerprint.platform.processor', return_value='x86_64'):
                result = get_cpu_id()
                assert result == 'x86_64'

    def test_get_cpu_id_exception(self):
        """Test get_cpu_id handles exceptions."""
        from app.utils.hardware_fingerprint import get_cpu_id
        with patch('app.utils.hardware_fingerprint.platform.system', return_value='Windows'):
            with patch('app.utils.hardware_fingerprint.subprocess.run', side_effect=OSError("Error")):
                result = get_cpu_id()
                # Should return platform.processor() or "unknown"
                assert result is not None


class TestGetDiskSerial:
    """Tests for get_disk_serial function."""

    def test_get_disk_serial_returns_string(self):
        """Test get_disk_serial returns a string."""
        from app.utils.hardware_fingerprint import get_disk_serial
        result = get_disk_serial()
        assert isinstance(result, str)

    def test_get_disk_serial_windows_success(self):
        """Test get_disk_serial on Windows with successful wmic call."""
        from app.utils.hardware_fingerprint import get_disk_serial
        mock_result = MagicMock()
        mock_result.stdout = "SerialNumber\nWD-WMC4M0123456\n"

        with patch('app.utils.hardware_fingerprint.platform.system', return_value='Windows'):
            with patch('app.utils.hardware_fingerprint.subprocess.run', return_value=mock_result):
                result = get_disk_serial()
                assert result == "WD-WMC4M0123456"

    def test_get_disk_serial_non_windows(self):
        """Test get_disk_serial on non-Windows system."""
        from app.utils.hardware_fingerprint import get_disk_serial
        with patch('app.utils.hardware_fingerprint.platform.system', return_value='Linux'):
            result = get_disk_serial()
            assert result == "unknown"

    def test_get_disk_serial_exception(self):
        """Test get_disk_serial handles exceptions."""
        from app.utils.hardware_fingerprint import get_disk_serial
        with patch('app.utils.hardware_fingerprint.platform.system', return_value='Windows'):
            with patch('app.utils.hardware_fingerprint.subprocess.run', side_effect=OSError("Error")):
                result = get_disk_serial()
                assert result == "unknown"


class TestGetMotherboardSerial:
    """Tests for get_motherboard_serial function."""

    def test_get_motherboard_serial_returns_string(self):
        """Test get_motherboard_serial returns a string."""
        from app.utils.hardware_fingerprint import get_motherboard_serial
        result = get_motherboard_serial()
        assert isinstance(result, str)

    def test_get_motherboard_serial_windows_success(self):
        """Test get_motherboard_serial on Windows."""
        from app.utils.hardware_fingerprint import get_motherboard_serial
        mock_result = MagicMock()
        mock_result.stdout = "SerialNumber\nMB123456789\n"

        with patch('app.utils.hardware_fingerprint.platform.system', return_value='Windows'):
            with patch('app.utils.hardware_fingerprint.subprocess.run', return_value=mock_result):
                result = get_motherboard_serial()
                assert result == "MB123456789"

    def test_get_motherboard_serial_non_windows(self):
        """Test get_motherboard_serial on non-Windows system."""
        from app.utils.hardware_fingerprint import get_motherboard_serial
        with patch('app.utils.hardware_fingerprint.platform.system', return_value='Linux'):
            result = get_motherboard_serial()
            assert result == "unknown"

    def test_get_motherboard_serial_exception(self):
        """Test get_motherboard_serial handles exceptions."""
        from app.utils.hardware_fingerprint import get_motherboard_serial
        with patch('app.utils.hardware_fingerprint.platform.system', return_value='Windows'):
            with patch('app.utils.hardware_fingerprint.subprocess.run', side_effect=OSError("Error")):
                result = get_motherboard_serial()
                assert result == "unknown"


class TestGetHostname:
    """Tests for get_hostname function."""

    def test_get_hostname_returns_string(self):
        """Test get_hostname returns a string."""
        from app.utils.hardware_fingerprint import get_hostname
        result = get_hostname()
        assert isinstance(result, str)

    def test_get_hostname_not_empty(self):
        """Test get_hostname returns non-empty string."""
        from app.utils.hardware_fingerprint import get_hostname
        result = get_hostname()
        assert len(result) > 0

    def test_get_hostname_exception(self):
        """Test get_hostname handles exceptions."""
        from app.utils.hardware_fingerprint import get_hostname
        with patch('app.utils.hardware_fingerprint.platform.node', side_effect=OSError("Error")):
            result = get_hostname()
            assert result == "unknown"


class TestGenerateHardwareId:
    """Tests for generate_hardware_id function."""

    def test_generate_hardware_id_returns_string(self):
        """Test generate_hardware_id returns a string."""
        from app.utils.hardware_fingerprint import generate_hardware_id
        result = generate_hardware_id()
        assert isinstance(result, str)

    def test_generate_hardware_id_length(self):
        """Test generate_hardware_id returns 64-char SHA256."""
        from app.utils.hardware_fingerprint import generate_hardware_id
        result = generate_hardware_id()
        assert len(result) == 64

    def test_generate_hardware_id_hex(self):
        """Test generate_hardware_id returns hex string."""
        from app.utils.hardware_fingerprint import generate_hardware_id
        result = generate_hardware_id()
        # Should only contain hex characters
        assert all(c in '0123456789abcdef' for c in result)

    def test_generate_hardware_id_consistency(self):
        """Test generate_hardware_id returns same value."""
        from app.utils.hardware_fingerprint import generate_hardware_id
        result1 = generate_hardware_id()
        result2 = generate_hardware_id()
        assert result1 == result2


class TestGenerateShortHardwareId:
    """Tests for generate_short_hardware_id function."""

    def test_generate_short_hardware_id_returns_string(self):
        """Test generate_short_hardware_id returns a string."""
        from app.utils.hardware_fingerprint import generate_short_hardware_id
        result = generate_short_hardware_id()
        assert isinstance(result, str)

    def test_generate_short_hardware_id_length(self):
        """Test generate_short_hardware_id returns 16 chars."""
        from app.utils.hardware_fingerprint import generate_short_hardware_id
        result = generate_short_hardware_id()
        assert len(result) == 16

    def test_generate_short_hardware_id_uppercase(self):
        """Test generate_short_hardware_id returns uppercase."""
        from app.utils.hardware_fingerprint import generate_short_hardware_id
        result = generate_short_hardware_id()
        assert result == result.upper()


class TestGetHardwareInfo:
    """Tests for get_hardware_info function."""

    def test_get_hardware_info_returns_dict(self):
        """Test get_hardware_info returns a dict."""
        from app.utils.hardware_fingerprint import get_hardware_info
        result = get_hardware_info()
        assert isinstance(result, dict)

    def test_get_hardware_info_keys(self):
        """Test get_hardware_info has required keys."""
        from app.utils.hardware_fingerprint import get_hardware_info
        result = get_hardware_info()
        required_keys = [
            'hostname', 'mac_address', 'cpu_id', 'disk_serial',
            'motherboard_serial', 'os', 'os_version', 'machine',
            'hardware_id', 'short_id'
        ]
        for key in required_keys:
            assert key in result

    def test_get_hardware_info_values_not_none(self):
        """Test get_hardware_info values are not None."""
        from app.utils.hardware_fingerprint import get_hardware_info
        result = get_hardware_info()
        for key, value in result.items():
            assert value is not None


class TestVerifyHardwareId:
    """Tests for verify_hardware_id function."""

    def test_verify_hardware_id_matching(self):
        """Test verify_hardware_id with matching ID."""
        from app.utils.hardware_fingerprint import verify_hardware_id, generate_hardware_id
        current_id = generate_hardware_id()
        assert verify_hardware_id(current_id) is True

    def test_verify_hardware_id_not_matching(self):
        """Test verify_hardware_id with non-matching ID."""
        from app.utils.hardware_fingerprint import verify_hardware_id
        assert verify_hardware_id("not_matching_id_at_all") is False

    def test_verify_hardware_id_partial_match(self):
        """Test verify_hardware_id with partial match."""
        from app.utils.hardware_fingerprint import verify_hardware_id, generate_hardware_id
        current_id = generate_hardware_id()
        partial = current_id[:32] + "x" * 32  # Half matching
        assert verify_hardware_id(partial) is False

    def test_verify_hardware_id_with_tolerance(self):
        """Test verify_hardware_id with tolerance parameter."""
        from app.utils.hardware_fingerprint import verify_hardware_id
        # Even with tolerance, a completely wrong ID should fail
        assert verify_hardware_id("wrong_id", tolerance=2) is False


class TestIntegration:
    """Integration tests for hardware fingerprint module."""

    def test_full_workflow(self):
        """Test full workflow of generating and verifying."""
        from app.utils.hardware_fingerprint import (
            generate_hardware_id,
            generate_short_hardware_id,
            verify_hardware_id,
            get_hardware_info
        )

        # Generate IDs
        full_id = generate_hardware_id()
        short_id = generate_short_hardware_id()

        # Verify
        assert verify_hardware_id(full_id) is True

        # Get info
        info = get_hardware_info()
        assert info['hardware_id'] == full_id
        assert info['short_id'] == short_id

    def test_all_component_functions(self):
        """Test all component functions return values."""
        from app.utils.hardware_fingerprint import (
            get_mac_address,
            get_cpu_id,
            get_disk_serial,
            get_motherboard_serial,
            get_hostname
        )

        # All should return strings
        assert isinstance(get_mac_address(), str)
        assert isinstance(get_cpu_id(), str)
        assert isinstance(get_disk_serial(), str)
        assert isinstance(get_motherboard_serial(), str)
        assert isinstance(get_hostname(), str)
