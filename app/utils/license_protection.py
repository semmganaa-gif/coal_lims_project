# -*- coding: utf-8 -*-
"""
License Protection - LIMS системийн лиценз хамгаалалт
Энэ модуль нь:
1. Лицензийн хүчинтэй байдлыг шалгах
2. Hardware ID шалгах
3. Tampering (хууран мэхлэх) илрүүлэх
4. Лиценз файл шифрлэх/тайлах
"""
import hashlib
import hmac
import json
import os
import base64
import secrets
from datetime import datetime, timedelta
from functools import wraps
from flask import redirect, url_for, flash, request, g
import logging

from app.utils.hardware_fingerprint import generate_hardware_id, generate_short_hardware_id
from app.utils.datetime import now_local as _now_mn_raw


def now_mn():
    """Naive datetime буцаана (DB-д хадгалсан expiry_date-тэй зэрэгцүүлэхэд)."""
    return _now_mn_raw().replace(tzinfo=None)

logger = logging.getLogger(__name__)

# =====================================================
# НУУЦ ТҮЛХҮҮРҮҮД - ENV эсвэл auto-generated
# =====================================================
_INSTANCE_DIR = os.path.join(os.path.abspath(os.path.dirname(__file__)), '..', '..', 'instance')


def _load_or_generate_key(env_var: str, filename: str, length: int = 48) -> str:
    """ENV-ээс уншиж, байхгүй бол instance/ файлд auto-generate хийнэ."""
    val = os.getenv(env_var)
    if val:
        return val
    key_path = os.path.join(_INSTANCE_DIR, filename)
    if os.path.exists(key_path):
        with open(key_path, 'r', encoding='utf-8') as f:
            return f.read().strip()
    # Файл байхгүй үед import дээр бичихгүй — runtime-д түр түлхүүр ашиглана
    key = secrets.token_urlsafe(length)
    logger.warning(f"{env_var} not found; using ephemeral key (not persisted).")
    return key


LICENSE_SECRET_KEY = _load_or_generate_key('LICENSE_SECRET_KEY', 'license_secret_key')
LICENSE_SALT = "COAL_LIMS_2024_LICENSE_SALT_V1"
SIGNATURE_KEY = _load_or_generate_key('LICENSE_SIGNATURE_KEY', 'license_signature_key')


def _hash_data(data: str) -> str:
    """Өгөгдлийг HMAC hash хийх"""
    return hmac.new(
        LICENSE_SECRET_KEY.encode(),
        (data + LICENSE_SALT).encode(),
        hashlib.sha256
    ).hexdigest()


def _create_signature(data: dict) -> str:
    """Лицензийн HMAC гарын үсэг үүсгэх"""
    sign_data = f"{data.get('company', '')}|{data.get('expiry', '')}|{data.get('hardware_id', '')}"
    return hmac.new(
        SIGNATURE_KEY.encode(),
        sign_data.encode(),
        hashlib.sha256
    ).hexdigest()


def _verify_signature(data: dict, signature: str) -> bool:
    """Гарын үсэг шалгах (timing-safe comparison)"""
    expected = _create_signature(data)
    return hmac.compare_digest(expected, signature)


class LicenseManager:
    """Лиценз менежер"""

    def __init__(self, app=None):
        self.app = app
        self._license_cache = None
        self._last_check = None
        self._check_interval = timedelta(hours=1)  # 1 цаг тутамд шалгах
        self._last_valid_result = None
        self._last_validate_time = None
        self._validate_cache_interval = timedelta(minutes=5)  # 5 мин кэш

    def init_app(self, app):
        self.app = app

    def get_current_license(self):
        """Одоогийн лиценз авах"""
        from app.models import SystemLicense
        from app import db

        # Cache шалгах
        now = now_mn()
        if self._license_cache and self._last_check:
            if now - self._last_check < self._check_interval:
                try:
                    return db.session.merge(self._license_cache, load=False)
                except Exception:
                    pass

        # Database-аас авах
        from sqlalchemy import select
        license_obj = db.session.execute(
            select(SystemLicense).filter_by(is_active=True)
        ).scalars().first()
        self._license_cache = license_obj
        self._last_check = now

        return license_obj

    def validate_license(self) -> dict:
        """
        Лиценз бүрэн шалгах
        Returns: {'valid': bool, 'error': str, 'license': obj, 'warning': str}
        """
        from app import db

        # Cached valid result-г буцаах (5 мин дотор DB бичихгүй)
        now = now_mn()
        if (self._last_valid_result and self._last_validate_time
                and now - self._last_validate_time < self._validate_cache_interval
                and self._last_valid_result.get('valid')):
            return self._last_valid_result

        result = {
            'valid': False,
            'error': None,
            'license': None,
            'warning': None
        }

        # 1. Лиценз олох
        license_obj = self.get_current_license()
        if not license_obj:
            result['error'] = 'LICENSE_NOT_FOUND'
            return result

        result['license'] = license_obj

        # 2. Идэвхтэй эсэх
        if not license_obj.is_active:
            result['error'] = 'LICENSE_INACTIVE'
            self._log_event(license_obj, 'check_failed', 'License is inactive')
            return result

        # 3. Tampering шалгах
        if license_obj.tampering_detected:
            result['error'] = 'TAMPERING_DETECTED'
            self._log_event(license_obj, 'tamper_blocked', 'Access blocked due to tampering')
            return result

        # 4. Хугацаа шалгах
        if now_mn() > license_obj.expiry_date:
            result['error'] = 'LICENSE_EXPIRED'
            self._log_event(license_obj, 'expired', 'License has expired')
            return result

        # 5. Hardware ID шалгах
        current_hw_id = generate_hardware_id()
        current_short = generate_short_hardware_id()
        if license_obj.hardware_id:
            # Support both full and short IDs in stored/allowed values
            stored_id = (license_obj.hardware_id or "").strip().lower()
            stored_short = stored_id[:16]
            if stored_id != current_hw_id.lower() and stored_short != current_short.lower():
                # Allowed list шалгах
                allowed_ids = []
                if license_obj.allowed_hardware_ids:
                    try:
                        allowed_ids = json.loads(license_obj.allowed_hardware_ids)
                    except (json.JSONDecodeError, TypeError):
                        pass

                allowed_norm = [str(x).strip().lower() for x in allowed_ids if x]
                allowed_ok = (
                    current_hw_id.lower() in allowed_norm
                    or current_short.lower() in allowed_norm
                )

                if not allowed_ok:
                    # Tampering илэрсэн!
                    license_obj.tampering_detected = True
                    license_obj.tampering_details = json.dumps({
                        'type': 'hardware_mismatch',
                        'expected': stored_short,
                        'found': current_short,
                        'detected_at': now_mn().isoformat()
                    })
                    db.session.commit()

                    result['error'] = 'HARDWARE_MISMATCH'
                    self._log_event(license_obj, 'hardware_mismatch',
                                    f'Expected: {stored_short}, Found: {current_short}')
                    return result

        # 6. Шалгалтын тоо нэмэх (1 цаг тутамд л DB бичнэ)
        if (not self._last_validate_time
                or now - self._last_validate_time >= self._check_interval):
            license_obj.last_check = now
            license_obj.check_count = (license_obj.check_count or 0) + 1
            try:
                db.session.commit()
            except Exception:
                db.session.rollback()

        # 7. Анхааруулга
        if license_obj.days_remaining <= 30:
            result['warning'] = f'LICENSE_EXPIRING_SOON:{license_obj.days_remaining}'

        result['valid'] = True
        self._last_valid_result = result
        self._last_validate_time = now
        return result

    def _log_event(self, license_obj, event_type: str, details: str):
        """Лог бүртгэх"""
        from app.models import LicenseLog
        from app import db

        try:
            log = LicenseLog(
                license_id=license_obj.id if license_obj else None,
                event_type=event_type,
                event_details=details,
                hardware_id=generate_short_hardware_id(),
                ip_address=request.remote_addr if request else None
            )
            db.session.add(log)
            db.session.commit()
        except Exception as e:
            logger.error(f"Failed to log license event: {e}")

    def activate_license(self, license_key: str) -> dict:
        """Лиценз идэвхжүүлэх"""
        from app.models import SystemLicense
        from app import db

        # Лиценз файл уншаад decode хийх
        try:
            license_data = self._decode_license_key(license_key)
        except Exception as e:
            return {'success': False, 'error': f'Invalid license format: {e}'}

        # Гарын үсэг шалгах
        if not _verify_signature(license_data, license_data.get('signature', '')):
            return {'success': False, 'error': 'Invalid license signature'}

        # Хугацаа шалгах
        expiry = datetime.fromisoformat(license_data['expiry'])
        if expiry < now_mn():
            return {'success': False, 'error': 'License has already expired'}

        # Hardware ID шалгах (хэрвээ заасан бол)
        if license_data.get('hardware_id'):
            current_hw = generate_hardware_id()
            if license_data['hardware_id'] != current_hw:
                return {'success': False, 'error': 'License is for different hardware'}

        # Хуучин лицензийг идэвхгүй болгох
        from sqlalchemy import update
        db.session.execute(update(SystemLicense).values(is_active=False))

        # Шинэ лиценз үүсгэх
        new_license = SystemLicense(
            license_key=license_key[:64],  # Богиносгох
            company_name=license_data.get('company', 'Unknown'),
            company_code=license_data.get('company_code', ''),
            issued_date=datetime.fromisoformat(license_data.get('issued', now_mn().isoformat())),
            expiry_date=expiry,
            max_users=license_data.get('max_users', 10),
            max_samples_per_month=license_data.get('max_samples', 10000),
            hardware_id=generate_hardware_id(),
            is_active=True,
            is_trial=license_data.get('is_trial', False)
        )

        db.session.add(new_license)
        db.session.commit()

        self._log_event(new_license, 'activated', f'License activated for {new_license.company_name}')
        # Cache бүрэн цэвэрлэх — stale result үлдэхээс сэргийлнэ
        self._license_cache = None
        self._last_check = None
        self._last_valid_result = None
        self._last_validate_time = None

        return {'success': True, 'license': new_license}

    def _decode_license_key(self, license_key: str) -> dict:
        """Лиценз түлхүүр decode хийх"""
        # Base64 decode
        try:
            decoded = base64.b64decode(license_key.encode()).decode()
            data = json.loads(decoded)
            return data
        except Exception as e:
            raise ValueError(f"Cannot decode license: {e}")

    def generate_license_key(self, company: str, expiry_date: str, hardware_id: str = None, **kwargs) -> str:
        """
        Лиценз түлхүүр үүсгэх (ЗОВхон та ашиглана!)
        Энэ функц нь лиценз үүсгэхэд л ашиглагдана
        """
        data = {
            'company': company,
            'company_code': kwargs.get('company_code', ''),
            'expiry': expiry_date,
            'issued': now_mn().isoformat(),
            'hardware_id': hardware_id,
            'max_users': kwargs.get('max_users', 10),
            'max_samples': kwargs.get('max_samples', 10000),
            'is_trial': kwargs.get('is_trial', False),
            'version': '1.0'
        }

        # Гарын үсэг нэмэх
        data['signature'] = _create_signature(data)

        # JSON -> Base64
        json_str = json.dumps(data, ensure_ascii=False)
        encoded = base64.b64encode(json_str.encode()).decode()

        return encoded

    def clear_cache(self):
        """Cache цэвэрлэх"""
        self._license_cache = None
        self._last_check = None
        self._last_valid_result = None
        self._last_validate_time = None


# Глобал instance
license_manager = LicenseManager()


def require_license(f):
    """
    Decorator - лиценз шаардах
    Хамгаалагдсан route-уудад ашиглана
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        result = license_manager.validate_license()

        if not result['valid']:
            error = result.get('error', 'UNKNOWN_ERROR')

            if error == 'LICENSE_NOT_FOUND':
                flash('License not found. Please contact system administrator.', 'error')
                return redirect(url_for('license.activate'))

            elif error == 'LICENSE_EXPIRED':
                flash('License has expired.', 'error')
                return redirect(url_for('license.expired'))

            elif error in ('HARDWARE_MISMATCH', 'TAMPERING_DETECTED'):
                flash('License error detected. Please contact system administrator.', 'error')
                return redirect(url_for('license.error'))

            else:
                flash('License error. Please contact system administrator.', 'error')
                return redirect(url_for('license.expired'))

        # Анхааруулга
        if result.get('warning'):
            warning = result['warning']
            if warning.startswith('LICENSE_EXPIRING_SOON:'):
                days = warning.split(':')[1]
                flash(f'Warning: License expires in {days} days!', 'warning')

        # License-г g объектод хадгалах
        g.license = result.get('license')

        return f(*args, **kwargs)
    return decorated_function


def check_license_middleware():
    """
    Before request middleware
    App-д бүртгэж ашиглана
    """
    from flask import request

    # Зарим route-г алгасах
    skip_endpoints = [
        'license.activate',
        'license.expired',
        'license.error',
        'license.info',
        'license.check',
        'license.hardware_id',
        'static',
        'main.login',
        'main.logout',
        'auth.login',
        'auth.logout',
    ]

    if request.endpoint in skip_endpoints:
        return None

    # Static файлуудыг алгасах
    if request.path.startswith('/static'):
        return None

    result = license_manager.validate_license()

    if not result['valid']:
        error = result.get('error', 'UNKNOWN_ERROR')

        if error == 'LICENSE_NOT_FOUND':
            return redirect(url_for('license.activate'))
        elif error == 'LICENSE_EXPIRED':
            return redirect(url_for('license.expired'))
        else:
            return redirect(url_for('license.error'))

    # Анхааруулга - g объектод хадгалах
    if result.get('warning'):
        g.license_warning = result['warning']

    g.license = result.get('license')
    return None
