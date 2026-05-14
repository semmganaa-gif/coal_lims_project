# app/repositories/solutions_repository.py
# -*- coding: utf-8 -*-
"""
Solution Repository - Уусмал бэлдэх / жорын database operations.

3 model:
- SolutionRecipe — уусмалын жор
- SolutionPreparation — бэлдсэн уусмалын бүртгэл
- SolutionRecipeIngredient — жорын орц
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Optional

from sqlalchemy import func

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
        query = SolutionRecipe.query.filter_by(
            lab_type=lab_type, is_active=True
        )
        if ordered:
            query = query.order_by(SolutionRecipe.name)
        return query.all()


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
        query = SolutionPreparation.query

        if start_date:
            try:
                start_dt = datetime.strptime(start_date, '%Y-%m-%d').date()
                query = query.filter(SolutionPreparation.prepared_date >= start_dt)
            except (ValueError, TypeError):
                pass

        if end_date:
            try:
                end_dt = datetime.strptime(end_date, '%Y-%m-%d').date()
                query = query.filter(SolutionPreparation.prepared_date <= end_dt)
            except (ValueError, TypeError):
                pass

        if status and status != 'all':
            query = query.filter(SolutionPreparation.status == status)

        return query.order_by(SolutionPreparation.prepared_date.desc()).all()

    @staticmethod
    def get_all_ordered() -> list[SolutionPreparation]:
        """Бүх уусмал, шинээр бэлдсэнээр sort."""
        return SolutionPreparation.query.order_by(
            SolutionPreparation.prepared_date.desc()
        ).all()

    @staticmethod
    def get_for_recipe(recipe_id: int,
                       limit: Optional[int] = None) -> list[SolutionPreparation]:
        """Тухайн жороор бэлдсэн уусмалууд."""
        query = SolutionPreparation.query.filter_by(recipe_id=recipe_id) \
            .order_by(SolutionPreparation.prepared_date.desc())
        if limit is not None:
            query = query.limit(limit)
        return query.all()

    @staticmethod
    def get_journal_stats() -> dict[str, int]:
        """Journal-ийн дээд статистик: total / active / expired."""
        today = date.today()
        return {
            'total': SolutionPreparation.query.count(),
            'active': SolutionPreparation.query.filter_by(status='active').count(),
            'expired': SolutionPreparation.query.filter(
                SolutionPreparation.expiry_date < today
            ).count(),
        }

    @staticmethod
    def get_recipe_stats(recipe_ids: list[int]) -> dict[int, dict]:
        """Жорын статистик: {recipe_id: {prep_count, last_prep}}."""
        stats = {rid: {'last_prep': None, 'prep_count': 0} for rid in recipe_ids}
        if not recipe_ids:
            return stats

        count_rows = db.session.query(
            SolutionPreparation.recipe_id,
            func.count(SolutionPreparation.id),
            func.max(SolutionPreparation.prepared_date),
        ).filter(
            SolutionPreparation.recipe_id.in_(recipe_ids)
        ).group_by(SolutionPreparation.recipe_id).all()

        max_dates = {}
        for rid, cnt, max_date in count_rows:
            stats[rid]['prep_count'] = cnt
            max_dates[rid] = max_date

        if max_dates:
            last_preps = SolutionPreparation.query.filter(
                SolutionPreparation.recipe_id.in_(list(max_dates.keys()))
            ).order_by(SolutionPreparation.prepared_date.desc()).all()
            seen = set()
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
        return SolutionRecipeIngredient.query.filter_by(
            recipe_id=recipe_id
        ).delete()
