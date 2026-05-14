# app/repositories/instrument_repository.py
# -*- coding: utf-8 -*-
"""
InstrumentReading Repository - Багажийн уншилтын database operations.

Файлаас parse хийсэн уншилтуудыг хадгалах, хянах, статистик query-ууд.
"""

from __future__ import annotations

from typing import Optional

from sqlalchemy import func

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
        return InstrumentReading.query.filter_by(file_hash=file_hash).first()

    @staticmethod
    def get_pending(instrument_type: Optional[str] = None,
                    limit: int = 100) -> list[InstrumentReading]:
        """Хянах хэрэгтэй уншилтууд."""
        query = InstrumentReading.query.filter_by(status="pending")
        if instrument_type:
            query = query.filter_by(instrument_type=instrument_type)
        return query.order_by(InstrumentReading.created_at.desc()).limit(limit).all()

    # =========================================================================
    # Aggregation
    # =========================================================================

    @staticmethod
    def get_status_counts() -> dict[str, int]:
        """Status-аар бүлэглэсэн тоо: {pending: N, approved: N, rejected: N, total: N}."""
        rows = db.session.query(
            InstrumentReading.status,
            func.count(InstrumentReading.id)
        ).group_by(InstrumentReading.status).all()

        result = {"pending": 0, "approved": 0, "rejected": 0, "total": 0}
        for status, count in rows:
            result[status] = count
            result["total"] += count
        return result
