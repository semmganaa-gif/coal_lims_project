# app/repositories/maintenance_repository.py
# -*- coding: utf-8 -*-
"""Maintenance & Usage Repository - Засвар/ашиглалтын database operations.

SQLAlchemy 2.0 native API (`select()` builder) ашиглана.
"""

from __future__ import annotations

from typing import Optional

from sqlalchemy import select

from app import db
from app.models import MaintenanceLog, UsageLog


class MaintenanceLogRepository:
    """MaintenanceLog model-ийн database operations."""

    @staticmethod
    def get_by_id(log_id: int) -> Optional[MaintenanceLog]:
        return db.session.get(MaintenanceLog, log_id)

    @staticmethod
    def get_by_equipment(equipment_id: int) -> list[MaintenanceLog]:
        stmt = (
            select(MaintenanceLog)
            .where(MaintenanceLog.equipment_id == equipment_id)
            .order_by(MaintenanceLog.action_date.desc())
        )
        return list(db.session.execute(stmt).scalars().all())

    @staticmethod
    def has_records(equipment_id: int) -> bool:
        stmt = select(MaintenanceLog.id).where(MaintenanceLog.equipment_id == equipment_id)
        return db.session.execute(stmt.limit(1)).first() is not None

    @staticmethod
    def save(log: MaintenanceLog, commit: bool = False) -> MaintenanceLog:
        db.session.add(log)
        if commit:
            db.session.commit()
        return log

    @staticmethod
    def delete(log: MaintenanceLog, commit: bool = False) -> bool:
        db.session.delete(log)
        if commit:
            db.session.commit()
        return True


class UsageLogRepository:
    """UsageLog model-ийн database operations."""

    @staticmethod
    def get_by_id(log_id: int) -> Optional[UsageLog]:
        return db.session.get(UsageLog, log_id)

    @staticmethod
    def get_by_equipment(equipment_id: int) -> list[UsageLog]:
        stmt = (
            select(UsageLog)
            .where(UsageLog.equipment_id == equipment_id)
            .order_by(UsageLog.start_time.desc())
        )
        return list(db.session.execute(stmt).scalars().all())

    @staticmethod
    def has_records(equipment_id: int) -> bool:
        stmt = select(UsageLog.id).where(UsageLog.equipment_id == equipment_id)
        return db.session.execute(stmt.limit(1)).first() is not None

    @staticmethod
    def save(log: UsageLog, commit: bool = False) -> UsageLog:
        db.session.add(log)
        if commit:
            db.session.commit()
        return log
