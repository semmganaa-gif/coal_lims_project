# app/repositories/audit_repository.py
# -*- coding: utf-8 -*-
"""Audit Repository - Аудит логийн database operations."""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from app import db
from app.models import AuditLog


class AuditLogRepository:
    """AuditLog model-ийн database operations."""

    @staticmethod
    def get_by_id(log_id: int) -> Optional[AuditLog]:
        return db.session.get(AuditLog, log_id)

    @staticmethod
    def get_recent(limit: int = 100) -> list[AuditLog]:
        return (
            AuditLog.query
            .order_by(AuditLog.timestamp.desc())
            .limit(limit)
            .all()
        )

    @staticmethod
    def get_by_user(user_id: int, limit: int = 100) -> list[AuditLog]:
        return (
            AuditLog.query
            .filter_by(user_id=user_id)
            .order_by(AuditLog.timestamp.desc())
            .limit(limit)
            .all()
        )

    @staticmethod
    def get_by_action(action: str, limit: int = 100) -> list[AuditLog]:
        return (
            AuditLog.query
            .filter_by(action=action)
            .order_by(AuditLog.timestamp.desc())
            .limit(limit)
            .all()
        )

    @staticmethod
    def get_by_resource(resource_type: str, resource_id: int) -> list[AuditLog]:
        return (
            AuditLog.query
            .filter_by(resource_type=resource_type, resource_id=resource_id)
            .order_by(AuditLog.timestamp.desc())
            .all()
        )

    @staticmethod
    def get_by_date_range(
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        action: Optional[str] = None,
        user_id: Optional[int] = None,
    ) -> list[AuditLog]:
        query = AuditLog.query
        if start_date:
            query = query.filter(AuditLog.timestamp >= start_date)
        if end_date:
            query = query.filter(AuditLog.timestamp <= end_date)
        if action:
            query = query.filter_by(action=action)
        if user_id:
            query = query.filter_by(user_id=user_id)
        return query.order_by(AuditLog.timestamp.desc()).all()

    @staticmethod
    def save(log: AuditLog, commit: bool = False) -> AuditLog:
        db.session.add(log)
        if commit:
            db.session.commit()
        return log
