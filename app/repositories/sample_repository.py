# app/repositories/sample_repository.py
# -*- coding: utf-8 -*-
"""
Sample Repository - Дээжний database operations.

Бүх Sample model-тэй холбоотой query-уудыг агуулна.
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from app import db
from app.models import Sample


class SampleRepository:
    """Sample model-ийн database operations."""

    # =========================================================================
    # Basic CRUD
    # =========================================================================

    @staticmethod
    def get_by_id(sample_id: int) -> Optional[Sample]:
        """
        ID-аар дээж авах.

        Args:
            sample_id: Дээжний ID

        Returns:
            Sample эсвэл None

        Examples:
            >>> sample = SampleRepository.get_by_id(123)
            >>> if sample:
            ...     print(sample.sample_code)
        """
        return db.session.get(Sample, sample_id)

    @staticmethod
    def get_by_id_or_404(sample_id: int) -> Sample:
        """
        ID-аар дээж авах, олдохгүй бол 404.

        Args:
            sample_id: Дээжний ID

        Returns:
            Sample

        Raises:
            404 error if not found
        """
        sample = db.session.get(Sample, sample_id)
        if sample is None:
            from flask import abort
            abort(404)
        return sample

    @staticmethod
    def get_by_ids(sample_ids: list[int]) -> list[Sample]:
        """
        Олон ID-аар дээжүүд авах.

        Args:
            sample_ids: ID-уудын жагсаалт

        Returns:
            Дээжүүдийн жагсаалт
        """
        if not sample_ids:
            return []
        return Sample.query.filter(Sample.id.in_(sample_ids)).all()

    @staticmethod
    def get_by_code(sample_code: str) -> Optional[Sample]:
        """
        Код-оор дээж хайх.

        Args:
            sample_code: Дээжний код

        Returns:
            Sample эсвэл None
        """
        return Sample.query.filter(Sample.sample_code == sample_code).first()

    @staticmethod
    def code_exists(sample_code: str, exclude_id: Optional[int] = None) -> bool:
        """
        Код давхцаж байгаа эсэхийг шалгах.

        Args:
            sample_code: Шалгах код
            exclude_id: Хасах ID (өөрийгөө шалгахаас сэргийлэх)

        Returns:
            True бол давхцаж байна
        """
        query = Sample.query.filter(Sample.sample_code == sample_code)
        if exclude_id:
            query = query.filter(Sample.id != exclude_id)
        return query.first() is not None

    # =========================================================================
    # Status-based queries
    # =========================================================================

    @staticmethod
    def get_by_status(status: str) -> list[Sample]:
        """
        Статусаар дээжүүд авах.

        Args:
            status: Sample.status CheckConstraint утга
                    ('new','in_progress','analysis','completed','archived').
                    NOTE: 'disposed' нь status биш — `disposal_date` талбараар
                    хянагдана.

        Returns:
            Дээжүүдийн жагсаалт
        """
        return Sample.query.filter(Sample.status == status).all()

    @staticmethod
    def get_active(exclude_archived: bool = True) -> list[Sample]:
        """
        Идэвхтэй дээжүүд авах.

        Args:
            exclude_archived: Архивлагдсан дээжүүд хасах эсэх

        Returns:
            Дээжүүдийн жагсаалт
        """
        query = Sample.query
        if exclude_archived:
            query = query.filter(Sample.status != "archived")
        return query.order_by(Sample.received_date.desc()).all()

    @staticmethod
    def update_status(sample_ids: list[int], new_status: str, commit: bool = False) -> int:
        """
        Олон дээжний статус шинэчлэх.

        Args:
            sample_ids: ID-уудын жагсаалт
            new_status: Шинэ статус

        Returns:
            Шинэчлэгдсэн тоо
        """
        if not sample_ids:
            return 0
        count = (
            db.session.query(Sample)
            .filter(Sample.id.in_(sample_ids))
            .update({Sample.status: new_status}, synchronize_session=False)
        )
        if commit:
            db.session.commit()
        return count

    # =========================================================================
    # Date-based queries
    # =========================================================================

    @staticmethod
    def get_by_date_range(
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> list[Sample]:
        """
        Огнооны хүрээгээр дээжүүд авах.

        Args:
            start_date: Эхлэх огноо
            end_date: Дуусах огноо

        Returns:
            Дээжүүдийн жагсаалт
        """
        query = Sample.query
        if start_date:
            query = query.filter(Sample.received_date >= start_date)
        if end_date:
            query = query.filter(Sample.received_date <= end_date)
        return query.order_by(Sample.received_date.desc()).all()

    # =========================================================================
    # Retention-based queries
    # =========================================================================

    @staticmethod
    def get_expired_retention(reference_date: datetime) -> list[Sample]:
        """
        Хадгалах хугацаа дууссан, гэвч устгагдаагүй дээжүүд.

        Args:
            reference_date: Харьцуулах огноо

        Returns:
            Хугацаа дууссан дээжүүд
        """
        return Sample.query.filter(
            Sample.retention_date.isnot(None),
            Sample.retention_date < reference_date,
            Sample.disposal_date.is_(None),
        ).all()

    @staticmethod
    def get_upcoming_expiry(
        start_date: datetime,
        end_date: datetime
    ) -> list[Sample]:
        """
        Удахгүй дуусах, устгагдаагүй дээжүүд.

        Args:
            start_date: Эхлэх огноо
            end_date: Дуусах огноо

        Returns:
            Дээжүүдийн жагсаалт
        """
        return Sample.query.filter(
            Sample.retention_date.isnot(None),
            Sample.retention_date >= start_date,
            Sample.retention_date <= end_date,
            Sample.disposal_date.is_(None),
        ).all()

    @staticmethod
    def get_disposed() -> list[Sample]:
        """Устгагдсан дээжүүд авах (disposal_date тэмдэглэгдсэн)."""
        return Sample.query.filter(Sample.disposal_date.isnot(None)).all()

    @staticmethod
    def get_no_retention() -> list[Sample]:
        """Хадгалах хугацаа тодорхойгүй, устгагдаагүй дээжүүд."""
        return Sample.query.filter(
            Sample.retention_date.is_(None),
            Sample.disposal_date.is_(None),
        ).all()

    @staticmethod
    def get_return_samples() -> list[Sample]:
        """Буцаах дээжүүд (устгагдаагүй)."""
        return Sample.query.filter(
            Sample.return_sample.is_(True),
            Sample.disposal_date.is_(None),
        ).all()

    # =========================================================================
    # Save operations
    # =========================================================================

    @staticmethod
    def save(sample: Sample, commit: bool = False) -> Sample:
        """
        Дээж хадгалах (create эсвэл update).

        Args:
            sample: Sample object

        Returns:
            Хадгалагдсан Sample
        """
        db.session.add(sample)
        if commit:
            db.session.commit()
        return sample

    @staticmethod
    def delete(sample: Sample, commit: bool = False) -> bool:
        """
        Дээж устгах.

        Args:
            sample: Sample object

        Returns:
            True бол амжилттай
        """
        db.session.delete(sample)
        if commit:
            db.session.commit()
        return True
