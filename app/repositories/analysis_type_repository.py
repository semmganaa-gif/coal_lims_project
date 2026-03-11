# app/repositories/analysis_type_repository.py
# -*- coding: utf-8 -*-
"""AnalysisType Repository — шинжилгээний төрлийн database operations."""

from __future__ import annotations
from typing import Optional

from app import db
from app.models import AnalysisType


class AnalysisTypeRepository:
    """AnalysisType model-ийн database operations."""

    @staticmethod
    def get_by_id(type_id: int) -> Optional[AnalysisType]:
        return db.session.get(AnalysisType, type_id)

    @staticmethod
    def get_by_code(code: str) -> Optional[AnalysisType]:
        return AnalysisType.query.filter_by(code=code).first()

    @staticmethod
    def get_by_code_or_404(code: str) -> AnalysisType:
        at = AnalysisType.query.filter_by(code=code).first()
        if at is None:
            from flask import abort
            abort(404)
        return at

    @staticmethod
    def get_all_ordered() -> list[AnalysisType]:
        return AnalysisType.query.order_by(AnalysisType.order_num).all()

    @staticmethod
    def get_all() -> list[AnalysisType]:
        return AnalysisType.query.all()

    @staticmethod
    def get_by_role(role: str) -> list[AnalysisType]:
        return (
            AnalysisType.query
            .filter_by(required_role=role)
            .order_by(AnalysisType.order_num)
            .all()
        )

    @staticmethod
    def get_codes() -> list[str]:
        rows = AnalysisType.query.with_entities(AnalysisType.code).all()
        return [r.code for r in rows]

    @staticmethod
    def get_all_excluding(exclude_codes: list[str]) -> list[AnalysisType]:
        return (
            AnalysisType.query
            .filter(~AnalysisType.code.in_(exclude_codes))
            .order_by(AnalysisType.order_num)
            .all()
        )
