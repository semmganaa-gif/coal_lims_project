# app/repositories/instrument_repository.py
# -*- coding: utf-8 -*-
"""
InstrumentReading Repository - Багажийн уншилтын database operations.

Файлаас parse хийсэн уншилтуудыг хадгалах, хянах, статистик query-ууд.
SQLAlchemy 2.0 native API (`select()` builder) ашиглана.
"""

from __future__ import annotations

from typing import Optional

from sqlalchemy import func, select

from app import db
from app.models.instrument import InstrumentReading


class InstrumentReadingRepository:
    """InstrumentReading model-ийн database operations."""

    # =========================================================================
    # Basic CRUD
    # =========================================================================

    @staticmethod
    def get_by_id(reading_id: int) -> Optional[InstrumentReading]:
        return db.session.get(InstrumentReading, reading_id)

    # =========================================================================
    # Filtered queries
    # =========================================================================

    @staticmethod
    def get_by_file_hash(file_hash: str) -> Optional[InstrumentReading]:
        """SHA-256 hash-аар уншилт хайх (file deduplication)."""
        stmt = select(InstrumentReading).where(InstrumentReading.file_hash == file_hash)
        return db.session.execute(stmt).scalar_one_or_none()

    @staticmethod
    def get_pending(instrument_type: Optional[str] = None,
                    limit: int = 100) -> list[InstrumentReading]:
        """Хянах хэрэгтэй уншилтууд."""
        stmt = select(InstrumentReading).where(InstrumentReading.status == "pending")
        if instrument_type:
            stmt = stmt.where(InstrumentReading.instrument_type == instrument_type)
        stmt = stmt.order_by(InstrumentReading.created_at.desc()).limit(limit)
        return list(db.session.execute(stmt).scalars().all())

    # =========================================================================
    # Aggregation
    # =========================================================================

    @staticmethod
    def get_status_counts() -> dict[str, int]:
        """Status-аар бүлэглэсэн тоо: {pending: N, approved: N, rejected: N, total: N}."""
        stmt = (
            select(InstrumentReading.status, func.count(InstrumentReading.id))
            .group_by(InstrumentReading.status)
        )
        rows = db.session.execute(stmt).all()

        result = {"pending": 0, "approved": 0, "rejected": 0, "total": 0}
        for status, count in rows:
            result[status] = count
            result["total"] += count
        return result
