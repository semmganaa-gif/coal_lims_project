# -*- coding: utf-8 -*-
"""
License models.
"""

from app import db
from app.utils.datetime import now_local as _now_mn_raw


def _safe_now():
    """Naive datetime буцаана (DB-д хадгалсан expiry_date-тэй зэрэгцүүлэхэд)."""
    return _now_mn_raw().replace(tzinfo=None)

class SystemLicense(db.Model):
    """
    Системийн лиценз.
    Програмыг хамгаалж, хугацаа, hardware-д холбоно.
    """
    __tablename__ = 'system_license'

    id = db.Column(db.Integer, primary_key=True)
    license_key = db.Column(db.String(128), unique=True, nullable=False)
    company_name = db.Column(db.String(200), nullable=False)
    company_code = db.Column(db.String(50))

    # Хугацаа
    issued_date = db.Column(db.DateTime, default=_safe_now)
    expiry_date = db.Column(db.DateTime, nullable=False)

    # Хязгаарлалт
    max_users = db.Column(db.Integer, default=10)
    max_samples_per_month = db.Column(db.Integer, default=10000)

    # Hardware binding
    hardware_id = db.Column(db.String(128))
    allowed_hardware_ids = db.Column(db.Text)  # JSON array

    # Төлөв
    is_active = db.Column(db.Boolean, default=True)
    is_trial = db.Column(db.Boolean, default=False)

    # Шалгалт
    last_check = db.Column(db.DateTime)
    check_count = db.Column(db.Integer, default=0)
    tampering_detected = db.Column(db.Boolean, default=False)
    tampering_details = db.Column(db.Text)

    created_at = db.Column(db.DateTime, default=_safe_now)
    updated_at = db.Column(db.DateTime, default=_safe_now, onupdate=_safe_now)

    @property
    def is_valid(self):
        """Лиценз хүчинтэй эсэх"""
        if not self.is_active:
            return False
        if self.tampering_detected:
            return False
        if _safe_now() > self.expiry_date:
            return False
        return True

    @property
    def days_remaining(self):
        """Үлдсэн хоног"""
        if _safe_now() > self.expiry_date:
            return 0
        delta = self.expiry_date - _safe_now()
        return max(0, delta.days)

    @property
    def is_expiring_soon(self):
        """30 хоногоос бага үлдсэн эсэх"""
        return 0 < self.days_remaining <= 30

    def __repr__(self):
        return f'<License {self.company_name} - expires {self.expiry_date}>'


class LicenseLog(db.Model):
    """Лицензийн лог - бүх үйлдлийг бүртгэх"""
    __tablename__ = 'license_log'

    id = db.Column(db.Integer, primary_key=True)
    license_id = db.Column(db.Integer, db.ForeignKey('system_license.id'), index=True)

    event_type = db.Column(db.String(50))
    event_details = db.Column(db.Text)
    hardware_id = db.Column(db.String(128))
    ip_address = db.Column(db.String(50))

    created_at = db.Column(db.DateTime, default=_safe_now)

    license = db.relationship('SystemLicense', backref='logs')


# -------------------------
# WASHABILITY / THEORETICAL YIELD
# -------------------------
