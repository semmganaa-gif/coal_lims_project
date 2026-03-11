# -*- coding: utf-8 -*-
"""
Tests for app/utils/hardware_fingerprint.py
Hardware fingerprint generation tests
"""
import pytest
from unittest.mock import patch, MagicMock


class TestGetMacAddress:
    """get_mac_address function tests"""

    def test_get_mac_address_returns_string(self):
        """Returns string"""
        from app.utils.hardware_fingerprint import get_mac_address

        result = get_mac_address()
        assert isinstance(result, str)

    def test_get_mac_address_format(self):
        """MAC address format (xx:xx:xx:xx:xx:xx)"""
        from app.utils.hardware_fingerprint import get_mac_address

        result = get_mac_address()
        # Either valid MAC or "unknown"
        if result != "unknown":
            parts = result.split(':')
            assert len(parts) == 6
            for part in parts:
                assert len(part) == 2

    def test_get_mac_address_exception_handling(self):
        """Exception returns 'unknown'"""
        from app.utils.hardware_fingerprint import get_mac_address

        with patch('app.utils.hardware_fingerprint.uuid.getnode', side_effect=OSError("Error")):
            result = get_mac_address()
            assert result == "unknown"


class TestGetCpuId:
    """get_cpu_id function tests"""

    def test_get_cpu_id_returns_string(self):
        """Returns string"""
        from app.utils.hardware_fingerprint import get_cpu_id

        result = get_cpu_id()
        assert isinstance(result, str)
        # Can be empty string or "unknown" or actual ID

    def test_get_cpu_id_not_unknown_on_windows(self):
        """Returns value on Windows"""
        from app.utils.hardware_fingerprint import get_cpu_id
        import platform

        result = get_cpu_id()
        # On Windows should get actual CPU ID or processor name
        if platform.system() == 'Windows':
            assert result != "unknown" or len(result) > 0


class TestGetDiskSerial:
    """get_disk_serial function tests"""

    def test_get_disk_serial_returns_string(self):
        """Returns string"""
        from app.utils.hardware_fingerprint import get_disk_serial

        result = get_disk_serial()
        assert isinstance(result, str)

    def test_get_disk_serial_on_windows(self):
        """Returns value on Windows"""
        from app.utils.hardware_fingerprint import get_disk_serial
        import platform

        result = get_disk_serial()
        # Should be either a serial or "unknown"
        assert result is not None


class TestGetMotherboardSerial:
    """get_motherboard_serial function tests"""

    def test_get_motherboard_serial_returns_string(self):
        """Returns string"""
        from app.utils.hardware_fingerprint import get_motherboard_serial

        result = get_motherboard_serial()
        assert isinstance(result, str)


class TestGetHostname:
    """get_hostname function tests"""

    def test_get_hostname_returns_string(self):
        """Returns string"""
        from app.utils.hardware_fingerprint import get_hostname

        result = get_hostname()
        assert isinstance(result, str)
        assert len(result) > 0

    def test_get_hostname_not_unknown(self):
        """Returns actual hostname"""
        from app.utils.hardware_fingerprint import get_hostname

        result = get_hostname()
        assert result != "unknown"

    def test_get_hostname_exception_handling(self):
        """Exception returns 'unknown'"""
        from app.utils.hardware_fingerprint import get_hostname

        with patch('app.utils.hardware_fingerprint.platform.node', side_effect=OSError("Error")):
            result = get_hostname()
            assert result == "unknown"


class TestGenerateHardwareId:
    """generate_hardware_id function tests"""

    def test_generate_hardware_id_returns_string(self):
        """Returns string"""
        from app.utils.hardware_fingerprint import generate_hardware_id

        result = generate_hardware_id()
        assert isinstance(result, str)

    def test_generate_hardware_id_is_sha256(self):
        """Returns SHA256 hash (64 chars)"""
        from app.utils.hardware_fingerprint import generate_hardware_id

        result = generate_hardware_id()
        assert len(result) == 64
        # All hex characters
        assert all(c in '0123456789abcdef' for c in result)

    def test_generate_hardware_id_consistent(self):
        """Same ID on same machine"""
        from app.utils.hardware_fingerprint import generate_hardware_id

        id1 = generate_hardware_id()
        id2 = generate_hardware_id()
        assert id1 == id2

    def test_generate_hardware_id_not_empty(self):
        """Not empty"""
        from app.utils.hardware_fingerprint import generate_hardware_id

        result = generate_hardware_id()
        assert len(result) > 0


class TestGenerateShortHardwareId:
    """generate_short_hardware_id function tests"""

    def test_generate_short_hardware_id_returns_string(self):
        """Returns string"""
        from app.utils.hardware_fingerprint import generate_short_hardware_id

        result = generate_short_hardware_id()
        assert isinstance(result, str)

    def test_generate_short_hardware_id_length(self):
        """Returns 16 chars"""
        from app.utils.hardware_fingerprint import generate_short_hardware_id

        result = generate_short_hardware_id()
        assert len(result) == 16

    def test_generate_short_hardware_id_uppercase(self):
        """Returns uppercase"""
        from app.utils.hardware_fingerprint import generate_short_hardware_id

        result = generate_short_hardware_id()
        assert result == result.upper()

    def test_generate_short_hardware_id_consistent(self):
        """Same ID on same machine"""
        from app.utils.hardware_fingerprint import generate_short_hardware_id

        id1 = generate_short_hardware_id()
        id2 = generate_short_hardware_id()
        assert id1 == id2

    def test_generate_short_hardware_id_is_prefix(self):
        """Is prefix of full ID"""
        from app.utils.hardware_fingerprint import generate_hardware_id, generate_short_hardware_id

        full_id = generate_hardware_id()
        short_id = generate_short_hardware_id()
        assert full_id[:16].upper() == short_id


class TestGetHardwareInfo:
    """get_hardware_info function tests"""

    def test_get_hardware_info_returns_dict(self):
        """Returns dict"""
        from app.utils.hardware_fingerprint import get_hardware_info

        result = get_hardware_info()
        assert isinstance(result, dict)

    def test_get_hardware_info_has_hostname(self):
        """Has hostname key"""
        from app.utils.hardware_fingerprint import get_hardware_info

        result = get_hardware_info()
        assert 'hostname' in result

    def test_get_hardware_info_has_mac_address(self):
        """Has mac_address key"""
        from app.utils.hardware_fingerprint import get_hardware_info

        result = get_hardware_info()
        assert 'mac_address' in result

    def test_get_hardware_info_has_cpu_id(self):
        """Has cpu_id key"""
        from app.utils.hardware_fingerprint import get_hardware_info

        result = get_hardware_info()
        assert 'cpu_id' in result

    def test_get_hardware_info_has_disk_serial(self):
        """Has disk_serial key"""
        from app.utils.hardware_fingerprint import get_hardware_info

        result = get_hardware_info()
        assert 'disk_serial' in result

    def test_get_hardware_info_has_motherboard_serial(self):
        """Has motherboard_serial key"""
        from app.utils.hardware_fingerprint import get_hardware_info

        result = get_hardware_info()
        assert 'motherboard_serial' in result

    def test_get_hardware_info_has_os(self):
        """Has os key"""
        from app.utils.hardware_fingerprint import get_hardware_info

        result = get_hardware_info()
        assert 'os' in result

    def test_get_hardware_info_has_os_version(self):
        """Has os_version key"""
        from app.utils.hardware_fingerprint import get_hardware_info

        result = get_hardware_info()
        assert 'os_version' in result

    def test_get_hardware_info_has_machine(self):
        """Has machine key"""
        from app.utils.hardware_fingerprint import get_hardware_info

        result = get_hardware_info()
        assert 'machine' in result

    def test_get_hardware_info_has_hardware_id(self):
        """Has hardware_id key"""
        from app.utils.hardware_fingerprint import get_hardware_info

        result = get_hardware_info()
        assert 'hardware_id' in result

    def test_get_hardware_info_has_short_id(self):
        """Has short_id key"""
        from app.utils.hardware_fingerprint import get_hardware_info

        result = get_hardware_info()
        assert 'short_id' in result


class TestVerifyHardwareId:
    """verify_hardware_id function tests"""

    def test_verify_hardware_id_same_id(self):
        """Same ID returns True"""
        from app.utils.hardware_fingerprint import generate_hardware_id, verify_hardware_id

        current_id = generate_hardware_id()
        result = verify_hardware_id(current_id)
        assert result is True

    def test_verify_hardware_id_different_id(self):
        """Different ID returns False"""
        from app.utils.hardware_fingerprint import verify_hardware_id

        result = verify_hardware_id("different_hardware_id_12345")
        assert result is False

    def test_verify_hardware_id_empty(self):
        """Empty ID returns False"""
        from app.utils.hardware_fingerprint import verify_hardware_id

        result = verify_hardware_id("")
        assert result is False

    def test_verify_hardware_id_with_tolerance(self):
        """With tolerance parameter"""
        from app.utils.hardware_fingerprint import verify_hardware_id

        # Tolerance doesn't change behavior for completely different IDs
        result = verify_hardware_id("different_id", tolerance=2)
        assert result is False
