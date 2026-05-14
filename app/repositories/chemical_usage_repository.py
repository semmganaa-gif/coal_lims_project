# app/repositories/chemical_usage_repository.py
# -*- coding: utf-8 -*-
"""
Chemical Usage / Log / Waste Repository — Chemical family-ийн child model-ууд.

Models:
- ChemicalUsage — өдөр тутмын хэрэглээний бүртгэл
- ChemicalLog — HashableMixin audit log (ISO 17025)
- ChemicalWaste — хог хаягдлын ангилал/нэр
- ChemicalWasteRecord — сар бүрийн хог хаягдлын бүртгэл
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from app import db
from app.models import (
    Chemical, ChemicalUsage, ChemicalLog,
    ChemicalWaste, ChemicalWasteRecord,
)


# =========================================================================
# ChemicalUsageRepository
# =========================================================================

class ChemicalUsageRepository:
    """ChemicalUsage model-ийн database operations (журнал, түүх, фильтр)."""

    @staticmethod
    def get_for_chemical(chemical_id: int, limit: int = 50) -> list[ChemicalUsage]:
        """Тухайн химийн бодисын хэрэглээний түүх."""
        return ChemicalUsage.query.filter_by(chemical_id=chemical_id) \
            .order_by(ChemicalUsage.used_at.desc()).limit(limit).all()

    @staticmethod
    def get_for_lot(lot_id: int, with_sample: bool = True) -> list[ChemicalUsage]:
        """Lot ашигласан бүх ChemicalUsage (lot invalidation-д)."""
        query = ChemicalUsage.query.filter_by(chemical_id=lot_id)
        if with_sample:
            query = query.filter(ChemicalUsage.sample_id.isnot(None))
        return query.all()

    @staticmethod
    def query_with_chemical(chemical_id: Optional[int] = None,
                            lab: str = "all",
                            start_date: Optional[str] = None,
                            end_date: Optional[str] = None,
                            limit: int = 100) -> list[tuple]:
        """Chemical-тай join хийсэн query (consumption summary, journal).

        Returns: list of (usage, chemical) tuples.
        """
        query = db.session.query(ChemicalUsage, Chemical).join(Chemical)

        if chemical_id is not None:
            query = query.filter(ChemicalUsage.chemical_id == chemical_id)

        if lab and lab != "all":
            query = query.filter(
                (Chemical.lab_type == lab) | (Chemical.lab_type == 'all')
            )

        if start_date:
            start_dt = datetime.strptime(start_date, "%Y-%m-%d")
            query = query.filter(ChemicalUsage.used_at >= start_dt)

        if end_date:
            end_dt = datetime.strptime(end_date, "%Y-%m-%d")
            end_dt = end_dt.replace(hour=23, minute=59, second=59)
            query = query.filter(ChemicalUsage.used_at <= end_dt)

        return query.order_by(ChemicalUsage.used_at.desc()).limit(limit).all()


# =========================================================================
# ChemicalLogRepository (HashableMixin audit, ISO 17025)
# =========================================================================

class ChemicalLogRepository:
    """ChemicalLog model-ийн database operations.

    ⚠️ HashableMixin model — DELETE/UPDATE blocked (audit immutability).
    """

    @staticmethod
    def get_for_chemical(chemical_id: int, limit: int = 50) -> list[ChemicalLog]:
        """Тухайн химийн бодисын audit log."""
        return ChemicalLog.query.filter_by(chemical_id=chemical_id) \
            .order_by(ChemicalLog.timestamp.desc()).limit(limit).all()


# =========================================================================
# ChemicalWasteRepository
# =========================================================================

class ChemicalWasteRepository:
    """ChemicalWaste model-ийн database operations (хог хаягдлын ангилал)."""

    @staticmethod
    def get_by_id(waste_id: int) -> Optional[ChemicalWaste]:
        return db.session.get(ChemicalWaste, waste_id)

    @staticmethod
    def get_active(lab: str = "all") -> list[ChemicalWaste]:
        """Идэвхтэй хог хаягдлын ангилалууд (lab-аар фильтр).

        Args:
            lab: "all" эсвэл лаб код ("coal", "water_chemistry", ...)
        """
        query = ChemicalWaste.query.filter(ChemicalWaste.is_active.is_(True))
        if lab != "all":
            query = query.filter(
                (ChemicalWaste.lab_type == lab) | (ChemicalWaste.lab_type == 'all')
            )
        return query.order_by(ChemicalWaste.name_mn.asc()).all()


# =========================================================================
# ChemicalWasteRecordRepository
# =========================================================================

class ChemicalWasteRecordRepository:
    """ChemicalWasteRecord model-ийн database operations (сар бүрийн бүртгэл)."""

    @staticmethod
    def find(waste_id: int, year: int, month: int) -> Optional[ChemicalWasteRecord]:
        """Тодорхой ангилал/жил/сарын бүртгэл (upsert lookup)."""
        return ChemicalWasteRecord.query.filter_by(
            waste_id=waste_id, year=year, month=month,
        ).first()

    @staticmethod
    def get_for_year(waste_id: int, year: int) -> list[ChemicalWasteRecord]:
        """Тухайн жилийн бүх сарын бүртгэл (тайланд)."""
        return ChemicalWasteRecord.query.filter_by(
            waste_id=waste_id, year=year,
        ).all()

    @staticmethod
    def get_for_month(year: int, month: int,
                      waste_ids: Optional[list[int]] = None) -> list[ChemicalWasteRecord]:
        """Тухайн жил/сарын бүх бүртгэл (тайланд).

        Args:
            waste_ids: байгаа бол зөвхөн тэдгээрт хязгаарлах.
        """
        query = ChemicalWasteRecord.query.filter_by(year=year, month=month)
        if waste_ids is not None:
            query = query.filter(ChemicalWasteRecord.waste_id.in_(waste_ids))
        return query.all()
