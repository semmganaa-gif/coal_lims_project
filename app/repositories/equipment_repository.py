# app/repositories/equipment_repository.py
# -*- coding: utf-8 -*-
"""Equipment Repository — тоног төхөөрөмжийн database operations."""

from __future__ import annotations
from datetime import date
from typing import Optional

from sqlalchemy import or_

from app import db
from app.models import Equipment


class EquipmentRepository:
    """Equipment model-ийн database operations."""

    @staticmethod
    def get_by_id(equipment_id: int) -> Optional[Equipment]:
        return db.session.get(Equipment, equipment_id)

    @staticmethod
    def get_all_active() -> list[Equipment]:
        """Retired биш бүх багажийг нэрээр эрэмбэлж авах."""
        return (
            Equipment.query
            .filter(or_(Equipment.status.is_(None), Equipment.status != 'retired'))
            .order_by(Equipment.name.asc())
            .all()
        )

    @staticmethod
    def get_by_category(category: str) -> list[Equipment]:
        """Категориор шүүж, retired биш."""
        return (
            Equipment.query
            .filter(
                Equipment.category == category,
                or_(Equipment.status.is_(None), Equipment.status != 'retired'),
            )
            .order_by(Equipment.name.asc())
            .all()
        )

    @staticmethod
    def get_by_categories(categories: list[str]) -> list[Equipment]:
        """Олон категориор шүүж, retired биш."""
        return (
            Equipment.query
            .filter(
                Equipment.category.in_(categories),
                or_(Equipment.status.is_(None), Equipment.status != 'retired'),
            )
            .order_by(Equipment.name.asc())
            .all()
        )

    @staticmethod
    def get_calibration_due(start_date: date, end_date: date,
                            categories: Optional[list[str]] = None) -> list[Equipment]:
        """Калибровкын хугацаа ойртож буй багажууд."""
        q = Equipment.query.filter(
            Equipment.status != 'retired',
            Equipment.next_calibration_date <= end_date,
            Equipment.next_calibration_date >= start_date,
        )
        if categories:
            q = q.filter(Equipment.category.in_(categories))
        return q.order_by(Equipment.next_calibration_date).all()

    @staticmethod
    def get_calibration_overdue(before_date: date,
                                categories: Optional[list[str]] = None) -> list[Equipment]:
        """Калибровкын хугацаа хэтэрсэн багажууд."""
        q = Equipment.query.filter(
            Equipment.status != 'retired',
            Equipment.next_calibration_date < before_date,
        )
        if categories:
            q = q.filter(Equipment.category.in_(categories))
        return q.order_by(Equipment.next_calibration_date).all()

    @staticmethod
    def get_by_statuses(statuses: list[str],
                        categories: Optional[list[str]] = None) -> list[Equipment]:
        """Статусаар шүүх (broken, maintenance гэх мэт)."""
        q = Equipment.query.filter(Equipment.status.in_(statuses))
        if categories:
            q = q.filter(Equipment.category.in_(categories))
        return q.all()

    @staticmethod
    def get_by_related_analysis(pattern: str, category: Optional[str] = None) -> list[Equipment]:
        """Related analysis талбараар ILIKE хайлт хийх."""
        q = Equipment.query.filter(
            or_(Equipment.status.is_(None), Equipment.status != 'retired'),
        )
        if category:
            q = q.filter(
                or_(Equipment.related_analysis.ilike(pattern), Equipment.category == category)
            )
        else:
            q = q.filter(Equipment.related_analysis.ilike(pattern))
        return q.order_by(Equipment.name.asc()).all()

    @staticmethod
    def save(equipment: Equipment, commit: bool = True) -> Equipment:
        db.session.add(equipment)
        if commit:
            db.session.commit()
        return equipment

    @staticmethod
    def delete(equipment: Equipment, commit: bool = True) -> bool:
        db.session.delete(equipment)
        if commit:
            db.session.commit()
        return True
