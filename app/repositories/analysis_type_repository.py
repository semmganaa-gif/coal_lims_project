# app/repositories/analysis_type_repository.py
# -*- coding: utf-8 -*-
"""AnalysisType Repository — шинжилгээний төрлийн database operations.

SQLAlchemy 2.0 native API (`select()` builder) ашиглана.
"""

from __future__ import annotations
from typing import Optional

from sqlalchemy import select

from app import db
from app.models import AnalysisType


class AnalysisTypeRepository:
    """AnalysisType model-ийн database operations."""

    @staticmethod
    def get_by_id(type_id: int) -> Optional[AnalysisType]:
        return db.session.get(AnalysisType, type_id)

    @staticmethod
    def get_by_code(code: str) -> Optional[AnalysisType]:
        stmt = select(AnalysisType).where(AnalysisType.code == code)
        return db.session.execute(stmt).scalar_one_or_none()

    @staticmethod
    def get_by_code_or_404(code: str) -> AnalysisType:
        at = AnalysisTypeRepository.get_by_code(code)
        if at is None:
            from flask import abort
            abort(404)
        return at

    @staticmethod
    def get_all_ordered() -> list[AnalysisType]:
        stmt = select(AnalysisType).order_by(AnalysisType.order_num)
        return list(db.session.execute(stmt).scalars().all())

    @staticmethod
    def get_all() -> list[AnalysisType]:
        stmt = select(AnalysisType)
        return list(db.session.execute(stmt).scalars().all())

    @staticmethod
    def get_by_role(role: str) -> list[AnalysisType]:
        stmt = (
            select(AnalysisType)
            .where(AnalysisType.required_role == role)
            .order_by(AnalysisType.order_num)
        )
        return list(db.session.execute(stmt).scalars().all())

    @staticmethod
    def get_codes() -> list[str]:
        stmt = select(AnalysisType.code)
        return list(db.session.execute(stmt).scalars().all())

    @staticmethod
    def get_all_excluding(exclude_codes: list[str]) -> list[AnalysisType]:
        stmt = (
            select(AnalysisType)
            .where(~AnalysisType.code.in_(exclude_codes))
            .order_by(AnalysisType.order_num)
        )
        return list(db.session.execute(stmt).scalars().all())
