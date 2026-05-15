# app/repositories/spare_parts_repository.py
# -*- coding: utf-8 -*-
"""
Spare Parts Repository - SparePart family-ийн database operations.

4 model:
- SparePartCategory
- SparePart
- SparePartUsage
- SparePartLog (HashableMixin audit log, ISO 17025)

SQLAlchemy 2.0 native API (`select()` builder) ашиглана.
"""

from __future__ import annotations

from typing import Optional

from sqlalchemy import case, func, or_, select

from app import db
from app.models.spare_parts import (
    SparePart, SparePartCategory, SparePartUsage, SparePartLog,
)
from app.utils.security import escape_like_pattern


# =========================================================================
# SparePartCategoryRepository
# =========================================================================

class SparePartCategoryRepository:
    """SparePartCategory model-ийн database operations."""

    @staticmethod
    def get_by_id(category_id: int) -> Optional[SparePartCategory]:
        return db.session.get(SparePartCategory, category_id)

    @staticmethod
    def get_by_code(code: str) -> Optional[SparePartCategory]:
        stmt = select(SparePartCategory).where(SparePartCategory.code == code)
        return db.session.execute(stmt).scalar_one_or_none()

    @staticmethod
    def get_active(ordered: bool = True) -> list[SparePartCategory]:
        """Идэвхтэй ангиллууд."""
        stmt = select(SparePartCategory).where(SparePartCategory.is_active.is_(True))
        if ordered:
            stmt = stmt.order_by(
                SparePartCategory.sort_order, SparePartCategory.name
            )
        return list(db.session.execute(stmt).scalars().all())

    @staticmethod
    def get_all_ordered() -> list[SparePartCategory]:
        """Бүх ангилал (active + inactive), sort_order + name-аар."""
        stmt = select(SparePartCategory).order_by(
            SparePartCategory.sort_order, SparePartCategory.name
        )
        return list(db.session.execute(stmt).scalars().all())


# =========================================================================
# SparePartRepository
# =========================================================================

class SparePartRepository:
    """SparePart model-ийн database operations."""

    @staticmethod
    def get_by_id(spare_part_id: int) -> Optional[SparePart]:
        return db.session.get(SparePart, spare_part_id)

    @staticmethod
    def count_by_category(category_code: str) -> int:
        """Тухайн ангилалд багтах сэлбэгийн тоо."""
        stmt = select(func.count(SparePart.id)).where(SparePart.category == category_code)
        return db.session.execute(stmt).scalar_one()

    @staticmethod
    def get_filtered(category: Optional[str] = None,
                     status: Optional[str] = None,
                     view: str = 'all') -> list[SparePart]:
        """Filter + view-аар сэлбэг авах."""
        stmt = select(SparePart)

        if category:
            stmt = stmt.where(SparePart.category == category)
        if status:
            stmt = stmt.where(SparePart.status == status)

        if view == 'low_stock':
            stmt = stmt.where(SparePart.status.in_(['low_stock', 'out_of_stock']))

        # Hide disposed by default
        if view != 'disposed' and status != 'disposed':
            stmt = stmt.where(SparePart.status != 'disposed')

        stmt = stmt.order_by(SparePart.name.asc())
        return list(db.session.execute(stmt).scalars().all())

    @staticmethod
    def get_all_ordered() -> list[SparePart]:
        """Бүх сэлбэг, нэрээр sort."""
        stmt = select(SparePart).order_by(SparePart.name)
        return list(db.session.execute(stmt).scalars().all())

    @staticmethod
    def get_low_stock() -> list[SparePart]:
        """Дутагдалтай эсвэл дуусч буй сэлбэгүүд."""
        stmt = (
            select(SparePart)
            .where(SparePart.status.in_(['low_stock', 'out_of_stock']))
            .order_by(SparePart.quantity.asc())
        )
        return list(db.session.execute(stmt).scalars().all())

    @staticmethod
    def search(query_str: str, limit: int = 20) -> list[SparePart]:
        """Нэр / name_en / part_number-аар хайх (LIKE)."""
        if not query_str or len(query_str) < 2:
            return []
        safe_q = escape_like_pattern(query_str)
        stmt = select(SparePart).where(
            or_(
                SparePart.name.ilike(f'%{safe_q}%'),
                SparePart.name_en.ilike(f'%{safe_q}%'),
                SparePart.part_number.ilike(f'%{safe_q}%'),
            )
        ).limit(limit)
        return list(db.session.execute(stmt).scalars().all())

    @staticmethod
    def get_list_stats() -> dict[str, int]:
        """{total, low_stock, out_of_stock} тоонууд."""
        stmt = select(
            func.count(case((SparePart.status != 'disposed', SparePart.id))).label('total'),
            func.count(case((SparePart.status == 'low_stock', SparePart.id))).label('low_stock'),
            func.count(case((SparePart.status == 'out_of_stock', SparePart.id))).label('out_of_stock'),
        )
        row = db.session.execute(stmt).one()
        return {
            'total': row.total or 0,
            'low_stock': row.low_stock or 0,
            'out_of_stock': row.out_of_stock or 0,
        }


# =========================================================================
# SparePartUsageRepository
# =========================================================================

class SparePartUsageRepository:
    """SparePartUsage model-ийн database operations."""

    @staticmethod
    def get_for_spare(spare_part_id: int, limit: int = 50) -> list[SparePartUsage]:
        """Сэлбэгийн хэрэглээний түүх."""
        stmt = (
            select(SparePartUsage)
            .where(SparePartUsage.spare_part_id == spare_part_id)
            .order_by(SparePartUsage.used_at.desc())
            .limit(limit)
        )
        return list(db.session.execute(stmt).scalars().all())


# =========================================================================
# SparePartLogRepository (ISO 17025 audit log, HashableMixin)
# =========================================================================

class SparePartLogRepository:
    """SparePartLog model-ийн database operations.

    ⚠️ HashableMixin model — DELETE/UPDATE blocked (audit immutability).
    """

    @staticmethod
    def get_for_spare(spare_part_id: int, limit: int = 50) -> list[SparePartLog]:
        """Сэлбэгийн audit log."""
        stmt = (
            select(SparePartLog)
            .where(SparePartLog.spare_part_id == spare_part_id)
            .order_by(SparePartLog.timestamp.desc())
            .limit(limit)
        )
        return list(db.session.execute(stmt).scalars().all())
