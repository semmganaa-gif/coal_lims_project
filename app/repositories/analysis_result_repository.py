# app/repositories/analysis_result_repository.py
# -*- coding: utf-8 -*-
"""
AnalysisResult Repository - Шинжилгээний үр дүнгийн database operations.

Бүх AnalysisResult model-тэй холбоотой query-уудыг агуулна.
SQLAlchemy 2.0 native API (`select()` builder) ашиглана.
"""

from __future__ import annotations

from typing import Optional

from sqlalchemy import select

from app import db
from app.constants import AnalysisResultStatus
from app.models import AnalysisResult


class AnalysisResultRepository:
    """AnalysisResult model-ийн database operations."""

    # =========================================================================
    # Basic CRUD
    # =========================================================================

    @staticmethod
    def get_by_id(result_id: int) -> Optional[AnalysisResult]:
        """ID-аар үр дүн авах."""
        return db.session.get(AnalysisResult, result_id)

    @staticmethod
    def get_by_id_or_404(result_id: int) -> AnalysisResult:
        """ID-аар үр дүн авах, олдохгүй бол 404."""
        result = db.session.get(AnalysisResult, result_id)
        if result is None:
            from flask import abort
            abort(404)
        return result

    @staticmethod
    def get_by_ids(result_ids: list[int]) -> list[AnalysisResult]:
        """Олон ID-аар үр дүнгүүд авах."""
        if not result_ids:
            return []
        stmt = select(AnalysisResult).where(AnalysisResult.id.in_(result_ids))
        return list(db.session.execute(stmt).scalars().all())

    # =========================================================================
    # Sample-based queries
    # =========================================================================

    @staticmethod
    def get_by_sample_id(sample_id: int) -> list[AnalysisResult]:
        """Дээжний ID-аар бүх үр дүнг авах."""
        stmt = (
            select(AnalysisResult)
            .where(AnalysisResult.sample_id == sample_id)
            .order_by(AnalysisResult.created_at.desc())
        )
        return list(db.session.execute(stmt).scalars().all())

    @staticmethod
    def get_by_sample_ids(sample_ids: list[int]) -> list[AnalysisResult]:
        """Олон дээжний ID-аар үр дүнгүүд авах."""
        if not sample_ids:
            return []
        stmt = select(AnalysisResult).where(AnalysisResult.sample_id.in_(sample_ids))
        return list(db.session.execute(stmt).scalars().all())

    @staticmethod
    def get_approved_by_sample(sample_id: int) -> list[AnalysisResult]:
        """Дээжний батлагдсан/pending үр дүнгүүд."""
        stmt = select(AnalysisResult).where(
            AnalysisResult.sample_id == sample_id,
            AnalysisResult.status.in_([AnalysisResultStatus.APPROVED.value, AnalysisResultStatus.PENDING_REVIEW.value]),
        )
        return list(db.session.execute(stmt).scalars().all())

    @staticmethod
    def get_approved_by_sample_ids(sample_ids: list[int]) -> list[AnalysisResult]:
        """Олон дээжний батлагдсан/pending үр дүнгүүд."""
        if not sample_ids:
            return []
        stmt = select(AnalysisResult).where(
            AnalysisResult.sample_id.in_(sample_ids),
            AnalysisResult.status.in_([AnalysisResultStatus.APPROVED.value, AnalysisResultStatus.PENDING_REVIEW.value]),
        )
        return list(db.session.execute(stmt).scalars().all())

    # =========================================================================
    # Status-based queries
    # =========================================================================

    @staticmethod
    def get_by_status(status: str) -> list[AnalysisResult]:
        """Статусаар үр дүнгүүд авах."""
        stmt = select(AnalysisResult).where(AnalysisResult.status == status)
        return list(db.session.execute(stmt).scalars().all())

    @staticmethod
    def get_pending_review() -> list[AnalysisResult]:
        """Хянагдаж буй үр дүнгүүд."""
        stmt = select(AnalysisResult).where(AnalysisResult.status == AnalysisResultStatus.PENDING_REVIEW.value)
        return list(db.session.execute(stmt).scalars().all())

    @staticmethod
    def update_status(result_ids: list[int], new_status: str, commit: bool = False) -> int:
        """Олон үр дүнгийн статус шинэчлэх."""
        if not result_ids:
            return 0
        from sqlalchemy import update
        stmt = (
            update(AnalysisResult)
            .where(AnalysisResult.id.in_(result_ids))
            .values(status=new_status)
            .execution_options(synchronize_session=False)
        )
        count = db.session.execute(stmt).rowcount
        if commit:
            db.session.commit()
        return count

    # =========================================================================
    # Analysis code queries
    # =========================================================================

    @staticmethod
    def get_by_analysis_code(analysis_code: str) -> list[AnalysisResult]:
        """Шинжилгээний кодоор үр дүнгүүд авах."""
        stmt = select(AnalysisResult).where(AnalysisResult.analysis_code == analysis_code)
        return list(db.session.execute(stmt).scalars().all())

    @staticmethod
    def get_by_sample_and_code(
        sample_id: int,
        analysis_code: str
    ) -> Optional[AnalysisResult]:
        """Дээж + кодоор үр дүн авах."""
        stmt = select(AnalysisResult).where(
            AnalysisResult.sample_id == sample_id,
            AnalysisResult.analysis_code == analysis_code,
        )
        return db.session.execute(stmt).scalar_one_or_none()

    # =========================================================================
    # Aggregation queries
    # =========================================================================

    @staticmethod
    def get_status_map_for_samples(sample_ids: list[int]) -> dict[int, set[str]]:
        """Дээжүүдийн үр дүнгийн статус map. {sample_id: {status1, ...}}"""
        if not sample_ids:
            return {}

        stmt = (
            select(AnalysisResult.sample_id, AnalysisResult.status)
            .where(AnalysisResult.sample_id.in_(sample_ids))
        )
        rows = db.session.execute(stmt).all()

        status_map: dict[int, set[str]] = {sid: set() for sid in sample_ids}
        for sample_id, status in rows:
            if sample_id in status_map:
                status_map[sample_id].add(status)

        return status_map

    @staticmethod
    def samples_with_approved_results() -> list[int]:
        """Батлагдсан үр дүнтэй дээжний ID-ууд."""
        stmt = (
            select(AnalysisResult.sample_id)
            .where(AnalysisResult.status.in_([AnalysisResultStatus.APPROVED.value, AnalysisResultStatus.PENDING_REVIEW.value]))
            .distinct()
        )
        return list(db.session.execute(stmt).scalars().all())

    # =========================================================================
    # Save operations
    # =========================================================================

    @staticmethod
    def save(result: AnalysisResult, commit: bool = False) -> AnalysisResult:
        """Үр дүн хадгалах."""
        db.session.add(result)
        if commit:
            db.session.commit()
        return result

    @staticmethod
    def delete(result: AnalysisResult, commit: bool = False) -> bool:
        """Үр дүн устгах."""
        db.session.delete(result)
        if commit:
            db.session.commit()
        return True
