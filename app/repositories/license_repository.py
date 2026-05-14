# app/repositories/license_repository.py
# -*- coding: utf-8 -*-
"""
License Repository - SystemLicense + LicenseLog database operations.

Хэрэглээ:
- `license_protection.py` дотроос license_manager
- `app/cli.py` license command (info/extend/allow-hardware/clear-tamper)
"""

from __future__ import annotations

from typing import Optional

from sqlalchemy import select, update

from app import db
from app.models.license import SystemLicense, LicenseLog


class SystemLicenseRepository:
    """SystemLicense model-ийн database operations."""

    @staticmethod
    def get_by_id(license_id: int) -> Optional[SystemLicense]:
        return db.session.get(SystemLicense, license_id)

    @staticmethod
    def get_active() -> Optional[SystemLicense]:
        """Идэвхтэй лицензийг буцаах (нэгэн зэрэг ганц л байх ёстой)."""
        return db.session.execute(
            select(SystemLicense).filter_by(is_active=True)
        ).scalars().first()

    @staticmethod
    def deactivate_all() -> None:
        """Бүх лицензийг идэвхгүй болгох (шинэ лиценз идэвхжүүлэхээс өмнө).

        Бөөнөөр UPDATE — commit-ыг caller хариуцна (@transactional эсвэл safe_commit).
        """
        db.session.execute(update(SystemLicense).values(is_active=False))


class LicenseLogRepository:
    """LicenseLog model-ийн database operations.

    Зөвхөн append-only audit log — get + write methods.
    """

    @staticmethod
    def get_recent(limit: int = 50) -> list[LicenseLog]:
        """Сүүлийн N audit log."""
        return LicenseLog.query.order_by(
            LicenseLog.created_at.desc()
        ).limit(limit).all()

    @staticmethod
    def get_for_license(license_id: int, limit: int = 100) -> list[LicenseLog]:
        """Тухайн лицензийн event-ууд."""
        return LicenseLog.query.filter_by(license_id=license_id) \
            .order_by(LicenseLog.created_at.desc()) \
            .limit(limit).all()
