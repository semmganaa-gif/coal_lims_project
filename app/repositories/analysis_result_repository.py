# app/repositories/analysis_result_repository.py
# -*- coding: utf-8 -*-
"""
AnalysisResult Repository - Шинжилгээний үр дүнгийн database operations.

Бүх AnalysisResult model-тэй холбоотой query-уудыг агуулна.
"""

from __future__ import annotations

from typing import Optional

from app import db
from app.models import AnalysisResult


class AnalysisResultRepository:
    """AnalysisResult model-ийн database operations."""

    # =========================================================================
    # Basic CRUD
    # =========================================================================

    @staticmethod
    def get_by_id(result_id: int) -> Optional[AnalysisResult]:
        """
        ID-аар үр дүн авах.

        Args:
            result_id: Үр дүнгийн ID

        Returns:
            AnalysisResult эсвэл None
        """
        return db.session.get(AnalysisResult, result_id)

    @staticmethod
    def get_by_id_or_404(result_id: int) -> AnalysisResult:
        """
        ID-аар үр дүн авах, олдохгүй бол 404.

        Args:
            result_id: Үр дүнгийн ID

        Returns:
            AnalysisResult

        Raises:
            404 error if not found
        """
        result = db.session.get(AnalysisResult, result_id)
        if result is None:
            from flask import abort
            abort(404)
        return result

    @staticmethod
    def get_by_ids(result_ids: list[int]) -> list[AnalysisResult]:
        """
        Олон ID-аар үр дүнгүүд авах.

        Args:
            result_ids: ID-уудын жагсаалт

        Returns:
            Үр дүнгүүдийн жагсаалт
        """
        if not result_ids:
            return []
        return AnalysisResult.query.filter(AnalysisResult.id.in_(result_ids)).all()

    # =========================================================================
    # Sample-based queries
    # =========================================================================

    @staticmethod
    def get_by_sample_id(sample_id: int) -> list[AnalysisResult]:
        """
        Дээжний ID-аар бүх үр дүнг авах.

        Args:
            sample_id: Дээжний ID

        Returns:
            Үр дүнгүүдийн жагсаалт
        """
        return (
            AnalysisResult.query
            .filter(AnalysisResult.sample_id == sample_id)
            .order_by(AnalysisResult.created_at.desc())
            .all()
        )

    @staticmethod
    def get_by_sample_ids(sample_ids: list[int]) -> list[AnalysisResult]:
        """
        Олон дээжний ID-аар үр дүнгүүд авах.

        Args:
            sample_ids: Дээжний ID-уудын жагсаалт

        Returns:
            Үр дүнгүүдийн жагсаалт
        """
        if not sample_ids:
            return []
        return (
            AnalysisResult.query
            .filter(AnalysisResult.sample_id.in_(sample_ids))
            .all()
        )

    @staticmethod
    def get_approved_by_sample(sample_id: int) -> list[AnalysisResult]:
        """
        Дээжний батлагдсан/pending үр дүнгүүд.

        Args:
            sample_id: Дээжний ID

        Returns:
            Үр дүнгүүдийн жагсаалт
        """
        return (
            AnalysisResult.query
            .filter(
                AnalysisResult.sample_id == sample_id,
                AnalysisResult.status.in_(["approved", "pending_review"]),
            )
            .all()
        )

    @staticmethod
    def get_approved_by_sample_ids(sample_ids: list[int]) -> list[AnalysisResult]:
        """
        Олон дээжний батлагдсан/pending үр дүнгүүд.

        Args:
            sample_ids: Дээжний ID-уудын жагсаалт

        Returns:
            Үр дүнгүүдийн жагсаалт
        """
        if not sample_ids:
            return []
        return (
            AnalysisResult.query
            .filter(
                AnalysisResult.sample_id.in_(sample_ids),
                AnalysisResult.status.in_(["approved", "pending_review"]),
            )
            .all()
        )

    # =========================================================================
    # Status-based queries
    # =========================================================================

    @staticmethod
    def get_by_status(status: str) -> list[AnalysisResult]:
        """
        Статусаар үр дүнгүүд авах.

        Args:
            status: "pending", "approved", "rejected" гэх мэт

        Returns:
            Үр дүнгүүдийн жагсаалт
        """
        return AnalysisResult.query.filter(AnalysisResult.status == status).all()

    @staticmethod
    def get_pending_review() -> list[AnalysisResult]:
        """Хянагдаж буй үр дүнгүүд."""
        return AnalysisResult.query.filter(
            AnalysisResult.status == "pending_review"
        ).all()

    @staticmethod
    def update_status(result_ids: list[int], new_status: str, commit: bool = True) -> int:
        """
        Олон үр дүнгийн статус шинэчлэх.

        Args:
            result_ids: ID-уудын жагсаалт
            new_status: Шинэ статус

        Returns:
            Шинэчлэгдсэн тоо
        """
        if not result_ids:
            return 0
        count = (
            db.session.query(AnalysisResult)
            .filter(AnalysisResult.id.in_(result_ids))
            .update({AnalysisResult.status: new_status}, synchronize_session=False)
        )
        if commit:
            db.session.commit()
        return count

    # =========================================================================
    # Analysis code queries
    # =========================================================================

    @staticmethod
    def get_by_analysis_code(analysis_code: str) -> list[AnalysisResult]:
        """
        Шинжилгээний кодоор үр дүнгүүд авах.

        Args:
            analysis_code: Шинжилгээний код (жнь: "Mt", "Mad", "Ad")

        Returns:
            Үр дүнгүүдийн жагсаалт
        """
        return (
            AnalysisResult.query
            .filter(AnalysisResult.analysis_code == analysis_code)
            .all()
        )

    @staticmethod
    def get_by_sample_and_code(
        sample_id: int,
        analysis_code: str
    ) -> Optional[AnalysisResult]:
        """
        Дээж + кодоор үр дүн авах.

        Args:
            sample_id: Дээжний ID
            analysis_code: Шинжилгээний код

        Returns:
            AnalysisResult эсвэл None
        """
        return (
            AnalysisResult.query
            .filter(
                AnalysisResult.sample_id == sample_id,
                AnalysisResult.analysis_code == analysis_code,
            )
            .first()
        )

    # =========================================================================
    # Aggregation queries
    # =========================================================================

    @staticmethod
    def get_status_map_for_samples(sample_ids: list[int]) -> dict[int, set[str]]:
        """
        Дээжүүдийн үр дүнгийн статус map.

        Args:
            sample_ids: Дээжний ID-уудын жагсаалт

        Returns:
            {sample_id: {status1, status2, ...}}
        """
        if not sample_ids:
            return {}

        rows = (
            db.session.query(AnalysisResult.sample_id, AnalysisResult.status)
            .filter(AnalysisResult.sample_id.in_(sample_ids))
            .all()
        )

        status_map: dict[int, set[str]] = {sid: set() for sid in sample_ids}
        for sample_id, status in rows:
            if sample_id in status_map:
                status_map[sample_id].add(status)

        return status_map

    @staticmethod
    def samples_with_approved_results() -> list[int]:
        """
        Батлагдсан үр дүнтэй дээжний ID-ууд.

        Returns:
            Sample ID-уудын жагсаалт
        """
        rows = (
            db.session.query(AnalysisResult.sample_id)
            .filter(AnalysisResult.status.in_(["approved", "pending_review"]))
            .distinct()
            .all()
        )
        return [row[0] for row in rows]

    # =========================================================================
    # Save operations
    # =========================================================================

    @staticmethod
    def save(result: AnalysisResult, commit: bool = True) -> AnalysisResult:
        """
        Үр дүн хадгалах.

        Args:
            result: AnalysisResult object

        Returns:
            Хадгалагдсан AnalysisResult
        """
        db.session.add(result)
        if commit:
            db.session.commit()
        return result

    @staticmethod
    def delete(result: AnalysisResult, commit: bool = True) -> bool:
        """
        Үр дүн устгах.

        Args:
            result: AnalysisResult object

        Returns:
            True бол амжилттай
        """
        db.session.delete(result)
        if commit:
            db.session.commit()
        return True
