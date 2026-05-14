# app/repositories/maintenance_repository.py
# -*- coding: utf-8 -*-
"""Maintenance & Usage Repository - Засвар/ашиглалтын database operations."""

from __future__ import annotations

from typing import Optional

from app import db
from app.models import MaintenanceLog, UsageLog


class MaintenanceLogRepository:
    """MaintenanceLog model-ийн database operations."""

    @staticmethod
    def get_by_id(log_id: int) -> Optional[MaintenanceLog]:
        return db.session.get(MaintenanceLog, log_id)

    @staticmethod
    def get_by_equipment(equipment_id: int) -> list[MaintenanceLog]:
        return (
            MaintenanceLog.query
            .filter_by(equipment_id=equipment_id)
            .order_by(MaintenanceLog.action_date.desc())
            .all()
        )

    @staticmethod
    def has_records(equipment_id: int) -> bool:
        return MaintenanceLog.query.filter_by(equipment_id=equipment_id).first() is not None

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
        return (
            UsageLog.query
            .filter_by(equipment_id=equipment_id)
            .order_by(UsageLog.start_time.desc())
            .all()
        )

    @staticmethod
    def has_records(equipment_id: int) -> bool:
        return UsageLog.query.filter_by(equipment_id=equipment_id).first() is not None

    @staticmethod
    def save(log: UsageLog, commit: bool = False) -> UsageLog:
        db.session.add(log)
        if commit:
            db.session.commit()
        return log
