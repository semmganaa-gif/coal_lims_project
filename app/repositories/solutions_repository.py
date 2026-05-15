# app/repositories/solutions_repository.py
# -*- coding: utf-8 -*-
"""
Solution Repository - Уусмал бэлдэх / жорын database operations.

3 model:
- SolutionRecipe — уусмалын жор
- SolutionPreparation — бэлдсэн уусмалын бүртгэл
- SolutionRecipeIngredient — жорын орц

SQLAlchemy 2.0 native API (`select()` / `delete()`) ашиглана.
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Optional

from sqlalchemy import delete, func, select

from app import db
from app.models.solutions import (
    SolutionRecipe, SolutionPreparation, SolutionRecipeIngredient,
)


# =========================================================================
# SolutionRecipeRepository
# =========================================================================

class SolutionRecipeRepository:
    """SolutionRecipe model-ийн database operations."""

    @staticmethod
    def get_by_id(recipe_id: int) -> Optional[SolutionRecipe]:
        return db.session.get(SolutionRecipe, recipe_id)

    @staticmethod
    def get_by_id_or_404(recipe_id: int) -> SolutionRecipe:
        """ID-аар жор авах, олдохгүй бол 404."""
        recipe = db.session.get(SolutionRecipe, recipe_id)
        if recipe is None:
            from flask import abort
            abort(404)
        return recipe

    @staticmethod
    def get_active_for_lab(lab_type: str = "water_chemistry",
                           ordered: bool = True) -> list[SolutionRecipe]:
        """Идэвхтэй жорууд (lab-аар фильтр)."""
        stmt = select(SolutionRecipe).where(
            SolutionRecipe.lab_type == lab_type,
            SolutionRecipe.is_active.is_(True),
        )
        if ordered:
            stmt = stmt.order_by(SolutionRecipe.name)
        return list(db.session.execute(stmt).scalars().all())


# =========================================================================
# SolutionPreparationRepository
# =========================================================================

class SolutionPreparationRepository:
    """SolutionPreparation model-ийн database operations."""

    @staticmethod
    def get_by_id(prep_id: int) -> Optional[SolutionPreparation]:
        return db.session.get(SolutionPreparation, prep_id)

    @staticmethod
    def get_by_id_or_404(prep_id: int) -> SolutionPreparation:
        prep = db.session.get(SolutionPreparation, prep_id)
        if prep is None:
            from flask import abort
            abort(404)
        return prep

    @staticmethod
    def get_filtered(start_date: Optional[str] = None,
                     end_date: Optional[str] = None,
                     status: str = "all") -> list[SolutionPreparation]:
        """Хугацаа + статусаар уусмал хайх (journal page-д)."""
        stmt = select(SolutionPreparation)

        if start_date:
            try:
                start_dt = datetime.strptime(start_date, '%Y-%m-%d').date()
                stmt = stmt.where(SolutionPreparation.prepared_date >= start_dt)
            except (ValueError, TypeError):
                pass

        if end_date:
            try:
                end_dt = datetime.strptime(end_date, '%Y-%m-%d').date()
                stmt = stmt.where(SolutionPreparation.prepared_date <= end_dt)
            except (ValueError, TypeError):
                pass

        if status and status != 'all':
            stmt = stmt.where(SolutionPreparation.status == status)

        stmt = stmt.order_by(SolutionPreparation.prepared_date.desc())
        return list(db.session.execute(stmt).scalars().all())

    @staticmethod
    def get_all_ordered() -> list[SolutionPreparation]:
        """Бүх уусмал, шинээр бэлдсэнээр sort."""
        stmt = select(SolutionPreparation).order_by(
            SolutionPreparation.prepared_date.desc()
        )
        return list(db.session.execute(stmt).scalars().all())

    @staticmethod
    def get_for_recipe(recipe_id: int,
                       limit: Optional[int] = None) -> list[SolutionPreparation]:
        """Тухайн жороор бэлдсэн уусмалууд."""
        stmt = (
            select(SolutionPreparation)
            .where(SolutionPreparation.recipe_id == recipe_id)
            .order_by(SolutionPreparation.prepared_date.desc())
        )
        if limit is not None:
            stmt = stmt.limit(limit)
        return list(db.session.execute(stmt).scalars().all())

    @staticmethod
    def get_journal_stats() -> dict[str, int]:
        """Journal-ийн дээд статистик: total / active / expired."""
        today = date.today()
        total = db.session.execute(
            select(func.count(SolutionPreparation.id))
        ).scalar_one()
        active = db.session.execute(
            select(func.count(SolutionPreparation.id))
            .where(SolutionPreparation.status == 'active')
        ).scalar_one()
        expired = db.session.execute(
            select(func.count(SolutionPreparation.id))
            .where(SolutionPreparation.expiry_date < today)
        ).scalar_one()
        return {
            'total': total,
            'active': active,
            'expired': expired,
        }

    @staticmethod
    def get_recipe_stats(recipe_ids: list[int]) -> dict[int, dict]:
        """Жорын статистик: {recipe_id: {prep_count, last_prep}}."""
        stats: dict[int, dict] = {rid: {'last_prep': None, 'prep_count': 0} for rid in recipe_ids}
        if not recipe_ids:
            return stats

        count_stmt = (
            select(
                SolutionPreparation.recipe_id,
                func.count(SolutionPreparation.id),
                func.max(SolutionPreparation.prepared_date),
            )
            .where(SolutionPreparation.recipe_id.in_(recipe_ids))
            .group_by(SolutionPreparation.recipe_id)
        )
        count_rows = db.session.execute(count_stmt).all()

        max_dates = {}
        for rid, cnt, max_date in count_rows:
            stats[rid]['prep_count'] = cnt
            max_dates[rid] = max_date

        if max_dates:
            last_preps_stmt = (
                select(SolutionPreparation)
                .where(SolutionPreparation.recipe_id.in_(list(max_dates.keys())))
                .order_by(SolutionPreparation.prepared_date.desc())
            )
            last_preps = db.session.execute(last_preps_stmt).scalars().all()
            seen: set[int] = set()
            for p in last_preps:
                if p.recipe_id not in seen:
                    stats[p.recipe_id]['last_prep'] = p
                    seen.add(p.recipe_id)

        return stats


# =========================================================================
# SolutionRecipeIngredientRepository
# =========================================================================

class SolutionRecipeIngredientRepository:
    """SolutionRecipeIngredient model-ийн database operations."""

    @staticmethod
    def delete_for_recipe(recipe_id: int) -> int:
        """Жорын бүх орцыг устгах (edit recipe үед хуучнаа цэвэрлэх).

        Returns: устгасан тоо.
        """
        stmt = delete(SolutionRecipeIngredient).where(
            SolutionRecipeIngredient.recipe_id == recipe_id
        )
        return db.session.execute(stmt).rowcount
