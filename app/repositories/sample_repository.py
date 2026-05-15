# app/repositories/sample_repository.py
# -*- coding: utf-8 -*-
"""
Sample Repository - Дээжний database operations.

Бүх Sample model-тэй холбоотой query-уудыг агуулна.
SQLAlchemy 2.0 native API (`select()` / `update()`) ашиглана.
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import select, update

from app import db
from app.models import Sample


class SampleRepository:
    """Sample model-ийн database operations."""

    # =========================================================================
    # Basic CRUD
    # =========================================================================

    @staticmethod
    def get_by_id(sample_id: int) -> Optional[Sample]:
        """ID-аар дээж авах."""
        return db.session.get(Sample, sample_id)

    @staticmethod
    def get_by_id_or_404(sample_id: int) -> Sample:
        """ID-аар дээж авах, олдохгүй бол 404."""
        sample = db.session.get(Sample, sample_id)
        if sample is None:
            from flask import abort
            abort(404)
        return sample

    @staticmethod
    def get_by_ids(sample_ids: list[int]) -> list[Sample]:
        """Олон ID-аар дээжүүд авах."""
        if not sample_ids:
            return []
        stmt = select(Sample).where(Sample.id.in_(sample_ids))
        return list(db.session.execute(stmt).scalars().all())

    @staticmethod
    def get_by_code(sample_code: str) -> Optional[Sample]:
        """Кодоор дээж хайх."""
        stmt = select(Sample).where(Sample.sample_code == sample_code)
        return db.session.execute(stmt).scalar_one_or_none()

    @staticmethod
    def code_exists(sample_code: str, exclude_id: Optional[int] = None) -> bool:
        """Код давхцаж байгаа эсэхийг шалгах."""
        stmt = select(Sample.id).where(Sample.sample_code == sample_code)
        if exclude_id:
            stmt = stmt.where(Sample.id != exclude_id)
        return db.session.execute(stmt.limit(1)).first() is not None

    # =========================================================================
    # Status-based queries
    # =========================================================================

    @staticmethod
    def get_by_status(status: str) -> list[Sample]:
        """Статусаар дээжүүд авах.

        NOTE: 'disposed' нь status биш — `disposal_date` талбараар хянагдана.
        """
        stmt = select(Sample).where(Sample.status == status)
        return list(db.session.execute(stmt).scalars().all())

    @staticmethod
    def get_active(exclude_archived: bool = True) -> list[Sample]:
        """Идэвхтэй дээжүүд авах."""
        stmt = select(Sample)
        if exclude_archived:
            stmt = stmt.where(Sample.status != "archived")
        stmt = stmt.order_by(Sample.received_date.desc())
        return list(db.session.execute(stmt).scalars().all())

    @staticmethod
    def update_status(sample_ids: list[int], new_status: str, commit: bool = False) -> int:
        """Олон дээжний статус шинэчлэх."""
        if not sample_ids:
            return 0
        stmt = (
            update(Sample)
            .where(Sample.id.in_(sample_ids))
            .values(status=new_status)
            .execution_options(synchronize_session=False)
        )
        count = db.session.execute(stmt).rowcount
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
        """Огнооны хүрээгээр дээжүүд авах."""
        stmt = select(Sample)
        if start_date:
            stmt = stmt.where(Sample.received_date >= start_date)
        if end_date:
            stmt = stmt.where(Sample.received_date <= end_date)
        stmt = stmt.order_by(Sample.received_date.desc())
        return list(db.session.execute(stmt).scalars().all())

    # =========================================================================
    # Retention-based queries
    # =========================================================================

    @staticmethod
    def get_expired_retention(reference_date: datetime) -> list[Sample]:
        """Хадгалах хугацаа дууссан, гэвч устгагдаагүй дээжүүд."""
        stmt = select(Sample).where(
            Sample.retention_date.isnot(None),
            Sample.retention_date < reference_date,
            Sample.disposal_date.is_(None),
        )
        return list(db.session.execute(stmt).scalars().all())

    @staticmethod
    def get_upcoming_expiry(
        start_date: datetime,
        end_date: datetime
    ) -> list[Sample]:
        """Удахгүй дуусах, устгагдаагүй дээжүүд."""
        stmt = select(Sample).where(
            Sample.retention_date.isnot(None),
            Sample.retention_date >= start_date,
            Sample.retention_date <= end_date,
            Sample.disposal_date.is_(None),
        )
        return list(db.session.execute(stmt).scalars().all())

    @staticmethod
    def get_disposed() -> list[Sample]:
        """Устгагдсан дээжүүд авах (disposal_date тэмдэглэгдсэн)."""
        stmt = select(Sample).where(Sample.disposal_date.isnot(None))
        return list(db.session.execute(stmt).scalars().all())

    @staticmethod
    def get_no_retention() -> list[Sample]:
        """Хадгалах хугацаа тодорхойгүй, устгагдаагүй дээжүүд."""
        stmt = select(Sample).where(
            Sample.retention_date.is_(None),
            Sample.disposal_date.is_(None),
        )
        return list(db.session.execute(stmt).scalars().all())

    @staticmethod
    def get_return_samples() -> list[Sample]:
        """Буцаах дээжүүд (устгагдаагүй)."""
        stmt = select(Sample).where(
            Sample.return_sample.is_(True),
            Sample.disposal_date.is_(None),
        )
        return list(db.session.execute(stmt).scalars().all())

    # =========================================================================
    # Save operations
    # =========================================================================

    @staticmethod
    def save(sample: Sample, commit: bool = False) -> Sample:
        """Дээж хадгалах (create эсвэл update)."""
        db.session.add(sample)
        if commit:
            db.session.commit()
        return sample

    @staticmethod
    def delete(sample: Sample, commit: bool = False) -> bool:
        """Дээж устгах."""
        db.session.delete(sample)
        if commit:
            db.session.commit()
        return True
