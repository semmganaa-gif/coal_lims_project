# app/repositories/planning_repository.py
# -*- coding: utf-8 -*-
"""
Planning Repository - MonthlyPlan + StaffSettings database operations.

Сар бүрийн төлөвлөгөө, хүний нөөц тохиргооны query-ууд.
"""

from __future__ import annotations

from typing import Optional

from app import db
from app.models.planning import MonthlyPlan, StaffSettings


class MonthlyPlanRepository:
    """MonthlyPlan model-ийн database operations."""

    @staticmethod
    def get_by_id(plan_id: int) -> Optional[MonthlyPlan]:
        return db.session.get(MonthlyPlan, plan_id)

    @staticmethod
    def get_by_month(year: int, month: int) -> list[MonthlyPlan]:
        """Тухайн жил/сарын бүх төлөвлөгөө."""
        return MonthlyPlan.query.filter_by(year=year, month=month).all()

    @staticmethod
    def find_for_week(year: int, month: int, week: int,
                      client_name: str, sample_type: str) -> Optional[MonthlyPlan]:
        """Тодорхой жил/сар/долоо хоног/харилцагч/дээж-ийн төлөвлөгөө."""
        return MonthlyPlan.query.filter_by(
            year=year, month=month, week=week,
            client_name=client_name, sample_type=sample_type,
        ).first()


class StaffSettingsRepository:
    """StaffSettings model-ийн database operations."""

    @staticmethod
    def get_by_id(settings_id: int) -> Optional[StaffSettings]:
        return db.session.get(StaffSettings, settings_id)

    @staticmethod
    def find_by_month(year: int, month: int) -> Optional[StaffSettings]:
        """Тухайн жил/сарын хүний нөөц тохиргоо."""
        return StaffSettings.query.filter_by(year=year, month=month).first()
