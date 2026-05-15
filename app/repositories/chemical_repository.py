# app/repositories/chemical_repository.py
# -*- coding: utf-8 -*-
"""Chemical Repository — химийн бодисын database operations.

SQLAlchemy 2.0 native API (`select()` builder) ашиглана.
"""

from __future__ import annotations
from datetime import date
from typing import Optional

from sqlalchemy import func, or_, select

from app import db
from app.models import Chemical


class ChemicalRepository:
    """Chemical model-ийн database operations."""

    @staticmethod
    def get_by_id(chemical_id: int) -> Optional[Chemical]:
        return db.session.get(Chemical, chemical_id)

    @staticmethod
    def get_active_count() -> int:
        stmt = select(func.count(Chemical.id)).where(Chemical.status != 'disposed')
        return db.session.execute(stmt).scalar_one()

    @staticmethod
    def get_low_stock_count() -> int:
        stmt = select(func.count(Chemical.id)).where(Chemical.status == 'low_stock')
        return db.session.execute(stmt).scalar_one()

    @staticmethod
    def get_expired_count() -> int:
        stmt = select(func.count(Chemical.id)).where(Chemical.status == 'expired')
        return db.session.execute(stmt).scalar_one()

    @staticmethod
    def get_low_stock() -> list[Chemical]:
        stmt = select(Chemical).where(Chemical.status == 'low_stock')
        return list(db.session.execute(stmt).scalars().all())

    @staticmethod
    def get_expiring_before(before_date: date) -> list[Chemical]:
        """Хугацаа дуусах гэж буй бодисууд."""
        stmt = select(Chemical).where(
            Chemical.expiry_date <= before_date,
            Chemical.status != 'disposed',
        )
        return list(db.session.execute(stmt).scalars().all())

    @staticmethod
    def get_active(lab_type: Optional[str] = None) -> list[Chemical]:
        """Идэвхтэй (disposed биш) бодисууд."""
        stmt = select(Chemical).where(Chemical.status != 'disposed')
        if lab_type:
            stmt = stmt.where(or_(
                Chemical.lab_type == lab_type,
                Chemical.lab_type == 'all',
            ))
        stmt = stmt.order_by(Chemical.name)
        return list(db.session.execute(stmt).scalars().all())

    @staticmethod
    def get_for_water_lab() -> list[Chemical]:
        """Усны лабд хэрэглэгддэг бодисууд."""
        stmt = (
            select(Chemical)
            .where(
                Chemical.status != 'disposed',
                or_(Chemical.lab_type == 'water_chemistry', Chemical.lab_type == 'all'),
            )
            .order_by(Chemical.name)
        )
        return list(db.session.execute(stmt).scalars().all())

    @staticmethod
    def save(chemical: Chemical, commit: bool = False) -> Chemical:
        db.session.add(chemical)
        if commit:
            db.session.commit()
        return chemical

    @staticmethod
    def delete(chemical: Chemical, commit: bool = False) -> bool:
        db.session.delete(chemical)
        if commit:
            db.session.commit()
        return True
