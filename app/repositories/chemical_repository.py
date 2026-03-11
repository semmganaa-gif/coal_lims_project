# app/repositories/chemical_repository.py
# -*- coding: utf-8 -*-
"""Chemical Repository — химийн бодисын database operations."""

from __future__ import annotations
from datetime import date
from typing import Optional

from app import db
from app.models import Chemical


class ChemicalRepository:
    """Chemical model-ийн database operations."""

    @staticmethod
    def get_by_id(chemical_id: int) -> Optional[Chemical]:
        return db.session.get(Chemical, chemical_id)

    @staticmethod
    def get_active_count() -> int:
        return Chemical.query.filter(Chemical.status != 'disposed').count()

    @staticmethod
    def get_low_stock_count() -> int:
        return Chemical.query.filter(Chemical.status == 'low_stock').count()

    @staticmethod
    def get_expired_count() -> int:
        return Chemical.query.filter(Chemical.status == 'expired').count()

    @staticmethod
    def get_low_stock() -> list[Chemical]:
        return Chemical.query.filter(Chemical.status == 'low_stock').all()

    @staticmethod
    def get_expiring_before(before_date: date) -> list[Chemical]:
        """Хугацаа дуусах гэж буй бодисууд."""
        return Chemical.query.filter(
            Chemical.expiry_date <= before_date,
            Chemical.status != 'disposed',
        ).all()

    @staticmethod
    def get_active(lab_type: Optional[str] = None) -> list[Chemical]:
        """Идэвхтэй (disposed биш) бодисууд."""
        q = Chemical.query.filter(Chemical.status != 'disposed')
        if lab_type:
            q = q.filter(
                (Chemical.lab_type == lab_type) | (Chemical.lab_type == 'all')
            )
        return q.order_by(Chemical.name).all()

    @staticmethod
    def get_for_water_lab() -> list[Chemical]:
        """Усны лабд хэрэглэгддэг бодисууд."""
        return (
            Chemical.query
            .filter(
                Chemical.status != 'disposed',
                (Chemical.lab_type == 'water') | (Chemical.lab_type == 'all'),
            )
            .order_by(Chemical.name)
            .all()
        )

    @staticmethod
    def save(chemical: Chemical, commit: bool = True) -> Chemical:
        db.session.add(chemical)
        if commit:
            db.session.commit()
        return chemical

    @staticmethod
    def delete(chemical: Chemical, commit: bool = True) -> bool:
        db.session.delete(chemical)
        if commit:
            db.session.commit()
        return True
