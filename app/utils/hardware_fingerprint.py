# -*- coding: utf-8 -*-
"""
Hardware Fingerprint - Компьютерийн өвөрмөц ID үүсгэх.

Лицензийг тодорхой компьютерт холбох зорилготой. Платформ бүрд тохиромжтой
системийн identifier-ийг ашиглана:

- Windows 10:  wmic (CPU/Disk/Motherboard serial)
- Windows 11+: wmic байхгүй бол PowerShell CIM-руу унана.
- Linux:       /etc/machine-id болон /sys/class/dmi/id/* (systemd standard)
- macOS:       ioreg IOPlatformUUID
- Fallback:    Hostname + MAC (uuid.getnode())

Платформ бүрд `"unknown"` тоо багасах боломжтой бол `generate_hardware_id`
илүү бат бөх hash гаргана. Audit H13.
"""
import hashlib
import logging
import platform
import re
import subprocess
import uuid

logger = logging.getLogger(__name__)

# subprocess timeout — Win11-д wmic байхгүй бол хурдан fall back болох
_SUBPROCESS_TIMEOUT = 5

# Cache hardware ID нэг удаа тооцоолоод хадгалах (дахин-дахин subprocess дуудах
# performance асуудлаас сэргийлэх)
_HARDWARE_ID_CACHE: str | None = None


# ─────────────────────────────────────────────────────────────
# Platform-specific helpers
# ─────────────────────────────────────────────────────────────

def _is_windows() -> bool:
    return platform.system() == 'Windows'


def _is_linux() -> bool:
    return platform.system() == 'Linux'


def _is_macos() -> bool:
    return platform.system() == 'Darwin'


def _run(cmd: list[str]) -> str | None:
    """subprocess wrapper — timeout + error logging. Алдааны үед None."""
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=_SUBPROCESS_TIMEOUT,
        )
        if result.returncode == 0:
            return result.stdout.strip()
        return None
    except (OSError, subprocess.SubprocessError, ValueError) as e:
        logger.debug(f"Subprocess failed ({cmd[0]}): {e}")
        return None


def _read_file(path: str) -> str | None:
    """Файлаас уншиж stripped utga буцаах. Алдааны үед None."""
    try:
        with open(path, 'r', encoding='utf-8') as f:
            val = f.read().strip()
            return val or None
    except OSError:
        return None


def _wmic(*args: str) -> str | None:
    """Windows wmic command-ын хоёр дахь мөрийг буцаах (header-ыг алгасах)."""
    out = _run(['wmic', *args])
    if not out:
        return None
    lines = out.split('\n')
    if len(lines) > 1:
        return lines[1].strip() or None
    return None


def _powershell(script: str) -> str | None:
    """Windows PowerShell — wmic байхгүй Win11+-д fallback."""
    out = _run(['powershell', '-NoProfile', '-Command', script])
    return out if out else None


# ─────────────────────────────────────────────────────────────
# Component getters
# ─────────────────────────────────────────────────────────────

def get_mac_address() -> str:
    """MAC хаяг авах (cross-platform, uuid.getnode())."""
    try:
        mac = uuid.getnode()
        # NOTE: uuid.getnode() нь MAC байхгүй үед random буцаадаг. Random бит-ийг
        # шалгах боломж байхгүй тул enterprise environment-д VPN/virtual NIC
        # анхааруулга бичих.
        return ':'.join(('%012x' % mac)[i:i+2] for i in range(0, 12, 2))
    except (OSError, ValueError) as e:
        logger.warning(f"Failed to get MAC address: {e}")
        return "unknown"


def get_cpu_id() -> str:
    """CPU ID авах (платформоос хамаарна)."""
    if _is_windows():
        # Win10: wmic, Win11+: PowerShell fallback
        val = _wmic('cpu', 'get', 'processorid')
        if val:
            return val
        val = _powershell(
            'Get-CimInstance Win32_Processor | Select -First 1 -ExpandProperty ProcessorId'
        )
        if val:
            return val
    elif _is_linux():
        # /proc/cpuinfo-аас "Serial" эсвэл model name + flags хэлбэрлэх
        try:
            with open('/proc/cpuinfo', 'r', encoding='utf-8') as f:
                content = f.read()
            match = re.search(r'^Serial\s*:\s*(\S+)', content, re.MULTILINE)
            if match:
                return match.group(1)
            # ARM/x86-аас serial байхгүй бол model name
            match = re.search(r'^model name\s*:\s*(.+)$', content, re.MULTILINE)
            if match:
                return match.group(1).strip()
        except OSError as e:
            logger.debug(f"Failed to read /proc/cpuinfo: {e}")
    elif _is_macos():
        # sysctl-аас CPU brand string
        val = _run(['sysctl', '-n', 'machdep.cpu.brand_string'])
        if val:
            return val
    return platform.processor() or "unknown"


def get_disk_serial() -> str:
    """Диск серийн дугаар авах (платформоос хамаарна)."""
    if _is_windows():
        val = _wmic('diskdrive', 'get', 'serialnumber')
        if val:
            return val
        val = _powershell(
            'Get-CimInstance Win32_DiskDrive | Select -First 1 -ExpandProperty SerialNumber'
        )
        if val:
            return val
    elif _is_linux():
        # /etc/machine-id нь systemd-ын generated unique ID (хатуу диск-той
        # тогтвортой холбоотой биш ч machine-уникал нь үнэн).
        val = _read_file('/etc/machine-id')
        if val:
            return val
        val = _read_file('/var/lib/dbus/machine-id')
        if val:
            return val
        # lsblk-аас disk serial — root шаардлагатай байж болзошгүй
        val = _run(['lsblk', '-d', '-no', 'SERIAL'])
        if val:
            return val.split('\n')[0].strip()
    elif _is_macos():
        # ioreg-аас IOPlatformUUID (machine UUID, диск биш гэхдээ unique)
        out = _run(['ioreg', '-rd1', '-c', 'IOPlatformExpertDevice'])
        if out:
            match = re.search(r'"IOPlatformUUID"\s*=\s*"([^"]+)"', out)
            if match:
                return match.group(1)
    return "unknown"


def get_motherboard_serial() -> str:
    """Motherboard серийн дугаар авах (платформоос хамаарна)."""
    if _is_windows():
        val = _wmic('baseboard', 'get', 'serialnumber')
        if val:
            return val
        val = _powershell(
            'Get-CimInstance Win32_BaseBoard | Select -First 1 -ExpandProperty SerialNumber'
        )
        if val:
            return val
    elif _is_linux():
        # DMI-аас board serial (root биш хэрэглэгчид өрөвдөх боломжтой)
        for path in ('/sys/class/dmi/id/board_serial', '/sys/class/dmi/id/product_uuid'):
            val = _read_file(path)
            if val:
                return val
    elif _is_macos():
        # macOS-д motherboard serial гэх ангиал байхгүй; system serial
        out = _run(['ioreg', '-rd1', '-c', 'IOPlatformExpertDevice'])
        if out:
            match = re.search(r'"IOPlatformSerialNumber"\s*=\s*"([^"]+)"', out)
            if match:
                return match.group(1)
    return "unknown"


def get_hostname() -> str:
    """Hostname авах."""
    try:
        return platform.node() or "unknown"
    except OSError as e:
        logger.warning(f"Failed to get hostname: {e}")
        return "unknown"


# ─────────────────────────────────────────────────────────────
# Fingerprint generation
# ─────────────────────────────────────────────────────────────

def generate_hardware_id() -> str:
    """
    Компьютерийн өвөрмөц hardware ID үүсгэх.

    Олон параметрийг hash хийж байгаа учраас аль нэг хувьсалтад нөлөөгүй —
    зөвхөн олон component нэг зэрэг өөрчлөгдсөн үед л ID өөрчлөгдөнө.

    Cache: Нэг процессын турш нэг л удаа тооцоолно (subprocess slow).
    """
    global _HARDWARE_ID_CACHE
    if _HARDWARE_ID_CACHE is not None:
        return _HARDWARE_ID_CACHE

    components = [
        get_hostname(),
        get_mac_address(),
        get_cpu_id(),
        get_disk_serial(),
        get_motherboard_serial(),
        platform.system(),
        platform.machine(),
    ]

    combined = '|'.join(str(c) for c in components)
    _HARDWARE_ID_CACHE = hashlib.sha256(combined.encode()).hexdigest()
    return _HARDWARE_ID_CACHE


def generate_short_hardware_id() -> str:
    """Богино hardware ID (харуулахад хялбар, эхний 16 hex char)."""
    return generate_hardware_id()[:16].upper()


def clear_cache() -> None:
    """Cache-ыг цэвэрлэх (тестэд эсвэл hardware өөрчлөгдөх сэжигтэй үед)."""
    global _HARDWARE_ID_CACHE
    _HARDWARE_ID_CACHE = None


def get_hardware_info() -> dict:
    """Hardware мэдээлэл дэлгэрэнгүй авах (license activation хуудаст)."""
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
        'short_id': generate_short_hardware_id(),
    }


def verify_hardware_id(stored_id: str) -> bool:
    """
    Hardware ID шалгах — яг adain match.

    NOTE: Audit M7-ийн дагуу `tolerance` параметрийг устгасан (огт ашиглагдаагүй
    байсан). Хэсэгчилсэн match хэрэгтэй бол license_protection.allowed_hardware_ids
    list-ийг ашиглах.
    """
    return stored_id == generate_hardware_id()
