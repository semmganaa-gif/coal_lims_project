# -*- coding: utf-8 -*-
"""
Hardware Fingerprint - Компьютерийн өвөрмөц ID үүсгэх
Энэ нь лицензийг тодорхой компьютерт холбох зорилготой
"""
import hashlib
import logging
import platform
import uuid
import subprocess

logger = logging.getLogger(__name__)


def get_mac_address():
    """MAC хаяг авах"""
    try:
        mac = uuid.getnode()
        return ':'.join(('%012x' % mac)[i:i+2] for i in range(0, 12, 2))
    except Exception as e:
        logger.warning(f"Failed to get MAC address: {e}")
        return "unknown"


def get_cpu_id():
    """CPU ID авах (Windows)"""
    try:
        if platform.system() == 'Windows':
            result = subprocess.run(
                ['wmic', 'cpu', 'get', 'processorid'],
                capture_output=True,
                text=True,
                timeout=10
            )
            lines = result.stdout.strip().split('\n')
            if len(lines) > 1:
                return lines[1].strip()
    except (OSError, subprocess.TimeoutExpired) as e:
        logger.warning(f"Failed to get CPU ID: {e}")
    return platform.processor() or "unknown"


def get_disk_serial():
    """Диск серийн дугаар авах (Windows)"""
    try:
        if platform.system() == 'Windows':
            result = subprocess.run(
                ['wmic', 'diskdrive', 'get', 'serialnumber'],
                capture_output=True,
                text=True,
                timeout=10
            )
            lines = result.stdout.strip().split('\n')
            if len(lines) > 1:
                return lines[1].strip()
    except (OSError, subprocess.TimeoutExpired) as e:
        logger.warning(f"Failed to get disk serial: {e}")
    return "unknown"


def get_motherboard_serial():
    """Motherboard серийн дугаар авах (Windows)"""
    try:
        if platform.system() == 'Windows':
            result = subprocess.run(
                ['wmic', 'baseboard', 'get', 'serialnumber'],
                capture_output=True,
                text=True,
                timeout=10
            )
            lines = result.stdout.strip().split('\n')
            if len(lines) > 1:
                return lines[1].strip()
    except (OSError, subprocess.TimeoutExpired) as e:
        logger.warning(f"Failed to get motherboard serial: {e}")
    return "unknown"


def get_hostname():
    """Hostname авах"""
    try:
        return platform.node()
    except Exception as e:
        logger.warning(f"Failed to get hostname: {e}")
        return "unknown"


def generate_hardware_id():
    """
    Компьютерийн өвөрмөц hardware ID үүсгэх
    Олон параметрийг хослуулснаар найдвартай болно
    """
    components = [
        get_hostname(),
        get_mac_address(),
        get_cpu_id(),
        get_disk_serial(),
        get_motherboard_serial(),
        platform.system(),
        platform.machine(),
    ]

    # Бүгдийг нэгтгэж hash хийх
    combined = '|'.join(str(c) for c in components)
    hardware_id = hashlib.sha256(combined.encode()).hexdigest()

    return hardware_id


def generate_short_hardware_id():
    """Богино hardware ID (харуулахад хялбар)"""
    full_id = generate_hardware_id()
    return full_id[:16].upper()


def get_hardware_info():
    """Hardware мэдээлэл дэлгэрэнгүй авах"""
    return {
        'hostname': get_hostname(),
        'mac_address': get_mac_address(),
        'cpu_id': get_cpu_id(),
        'disk_serial': get_disk_serial(),
        'motherboard_serial': get_motherboard_serial(),
        'os': platform.system(),
        'os_version': platform.version(),
        'machine': platform.machine(),
        'hardware_id': generate_hardware_id(),
        'short_id': generate_short_hardware_id()
    }


def verify_hardware_id(stored_id, tolerance=1):
    """
    Hardware ID шалгах
    tolerance - хэдэн component өөрчлөгдөж болох (VM-д шилжих үед)
    """
    current_id = generate_hardware_id()

    if stored_id == current_id:
        return True

    # Хэрвээ яг таарахгүй бол, зөвхөн хатуу шалгалт хийх
    # VM эсвэл hardware солигдсон үед
    return False


# Test
if __name__ == '__main__':
    print("Hardware Information:")
    print("-" * 50)
    info = get_hardware_info()
    for key, value in info.items():
        print(f"{key}: {value}")
