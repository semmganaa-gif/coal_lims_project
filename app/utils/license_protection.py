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
import json
import base64
import os
from datetime import datetime, timedelta
from functools import wraps
from flask import redirect, url_for, flash, request, current_app, g
import logging

from app.utils.hardware_fingerprint import generate_hardware_id, generate_short_hardware_id

logger = logging.getLogger(__name__)

# =====================================================
# НУУЦ ТҮЛХҮҮРҮҮД - Эдгээрийг ӨӨРЧЛӨХ хэрэгтэй!
# =====================================================
# Та эдгээр утгыг өөрийн санамсаргүй утгаар солих ёстой
LICENSE_SECRET_KEY = "ТАНЫ_НУУЦ_ТҮЛХҮҮР_ЭНД_32_ТЭМДЭГТ"  # 32+ тэмдэгт
LICENSE_SALT = "COAL_LIMS_2024_LICENSE_SALT_V1"
SIGNATURE_KEY = "ТАНЫ_ГАРЫН_ҮСГИЙН_ТҮЛХҮҮР_ЭНД"


def _hash_data(data: str) -> str:
    """Өгөгдлийг hash хийх"""
    combined = f"{data}{LICENSE_SALT}{LICENSE_SECRET_KEY}"
    return hashlib.sha256(combined.encode()).hexdigest()


def _create_signature(data: dict) -> str:
    """Лицензийн гарын үсэг үүсгэх"""
    # Чухал талбаруудыг нэгтгэх
    sign_data = f"{data.get('company', '')}{data.get('expiry', '')}{data.get('hardware_id', '')}{SIGNATURE_KEY}"
    return hashlib.sha256(sign_data.encode()).hexdigest()[:32]


def _verify_signature(data: dict, signature: str) -> bool:
    """Гарын үсэг шалгах"""
    expected = _create_signature(data)
    return expected == signature


class LicenseManager:
    """Лиценз менежер"""

    def __init__(self, app=None):
        self.app = app
        self._license_cache = None
        self._last_check = None
        self._check_interval = timedelta(hours=1)  # 1 цаг тутамд шалгах

    def init_app(self, app):
        self.app = app

    def get_current_license(self):
        """Одоогийн лиценз авах"""
        from app.models import SystemLicense

        # Cache шалгах
        now = datetime.utcnow()
        if self._license_cache and self._last_check:
            if now - self._last_check < self._check_interval:
                return self._license_cache

        # Database-аас авах
        license_obj = SystemLicense.query.filter_by(is_active=True).first()
        self._license_cache = license_obj
        self._last_check = now

        return license_obj

    def validate_license(self) -> dict:
        """
        Лиценз бүрэн шалгах
        Returns: {'valid': bool, 'error': str, 'license': obj, 'warning': str}
        """
        from app.models import SystemLicense, LicenseLog
        from app import db

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
        if datetime.utcnow() > license_obj.expiry_date:
            result['error'] = 'LICENSE_EXPIRED'
            self._log_event(license_obj, 'expired', 'License has expired')
            return result

        # 5. Hardware ID шалгах
        current_hw_id = generate_hardware_id()
        if license_obj.hardware_id:
            if license_obj.hardware_id != current_hw_id:
                # Allowed list шалгах
                allowed_ids = []
                if license_obj.allowed_hardware_ids:
                    try:
                        allowed_ids = json.loads(license_obj.allowed_hardware_ids)
                    except Exception:
                        pass

                if current_hw_id not in allowed_ids:
                    # Tampering илэрсэн!
                    license_obj.tampering_detected = True
                    license_obj.tampering_details = json.dumps({
                        'type': 'hardware_mismatch',
                        'expected': license_obj.hardware_id[:16],
                        'found': current_hw_id[:16],
                        'detected_at': datetime.utcnow().isoformat()
                    })
                    db.session.commit()

                    result['error'] = 'HARDWARE_MISMATCH'
                    self._log_event(license_obj, 'hardware_mismatch',
                                    f'Expected: {license_obj.hardware_id[:16]}, Found: {current_hw_id[:16]}')
                    return result

        # 6. Шалгалтын тоо нэмэх
        license_obj.last_check = datetime.utcnow()
        license_obj.check_count = (license_obj.check_count or 0) + 1
        db.session.commit()

        # 7. Анхааруулга
        if license_obj.days_remaining <= 30:
            result['warning'] = f'LICENSE_EXPIRING_SOON:{license_obj.days_remaining}'

        result['valid'] = True
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
        if expiry < datetime.utcnow():
            return {'success': False, 'error': 'License has already expired'}

        # Hardware ID шалгах (хэрвээ заасан бол)
        if license_data.get('hardware_id'):
            current_hw = generate_hardware_id()
            if license_data['hardware_id'] != current_hw:
                return {'success': False, 'error': 'License is for different hardware'}

        # Хуучин лицензийг идэвхгүй болгох
        SystemLicense.query.update({'is_active': False})

        # Шинэ лиценз үүсгэх
        new_license = SystemLicense(
            license_key=license_key[:64],  # Богиносгох
            company_name=license_data.get('company', 'Unknown'),
            company_code=license_data.get('company_code', ''),
            issued_date=datetime.fromisoformat(license_data.get('issued', datetime.utcnow().isoformat())),
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
        self._license_cache = None  # Cache цэвэрлэх

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
            'issued': datetime.utcnow().isoformat(),
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
                flash('Лиценз олдсонгүй. Системийн админтай холбогдоно уу.', 'error')
                return redirect(url_for('license.activate'))

            elif error == 'LICENSE_EXPIRED':
                flash('Лицензийн хугацаа дууссан байна.', 'error')
                return redirect(url_for('license.expired'))

            elif error in ('HARDWARE_MISMATCH', 'TAMPERING_DETECTED'):
                flash('Лицензийн алдаа илэрлээ. Системийн админтай холбогдоно уу.', 'error')
                return redirect(url_for('license.error'))

            else:
                flash('Лицензийн алдаа. Системийн админтай холбогдоно уу.', 'error')
                return redirect(url_for('license.expired'))

        # Анхааруулга
        if result.get('warning'):
            warning = result['warning']
            if warning.startswith('LICENSE_EXPIRING_SOON:'):
                days = warning.split(':')[1]
                flash(f'Анхааруулга: Лицензийн хугацаа {days} хоногийн дараа дуусна!', 'warning')

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
        'static',
        'auth.login',
        'auth.logout'
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
