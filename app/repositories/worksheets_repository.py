# app/repositories/worksheets_repository.py
# -*- coding: utf-8 -*-
"""
Water Worksheet Repository - QC ажлын хуудасны database operations.

2 model:
- WaterWorksheet — усны хими QC worksheet header
- WorksheetRow — worksheet-ийн мөр (QC, sample, blank, spike, etc.)

SQLAlchemy 2.0 native API (`select()` / `delete()`) ашиглана.
"""

from __future__ import annotations

from typing import Optional

from sqlalchemy import delete, select

from app import db
from app.models.worksheets import WaterWorksheet, WorksheetRow


# =========================================================================
# WaterWorksheetRepository
# =========================================================================

class WaterWorksheetRepository:
    """WaterWorksheet model-ийн database operations."""

    @staticmethod
    def get_by_id(ws_id: int) -> Optional[WaterWorksheet]:
        return db.session.get(WaterWorksheet, ws_id)

    @staticmethod
    def get_by_id_or_404(ws_id: int) -> WaterWorksheet:
        """ID-аар worksheet авах, олдохгүй бол 404."""
        ws = db.session.get(WaterWorksheet, ws_id)
        if ws is None:
            from flask import abort
            abort(404)
        return ws

    @staticmethod
    def get_filtered(status: Optional[str] = None,
                     limit: int = 200) -> list[WaterWorksheet]:
        """Status-аар фильтр + analysis_date desc-ээр sort.

        Args:
            status: байгаа бол тухайн төлвөөр шүүх ('open', 'submitted', ...)
            limit: дээд мөрийн тоо (default 200).
        """
        stmt = select(WaterWorksheet)
        if status:
            stmt = stmt.where(WaterWorksheet.status == status)
        stmt = stmt.order_by(
            WaterWorksheet.analysis_date.desc(),
            WaterWorksheet.id.desc(),
        ).limit(limit)
        return list(db.session.execute(stmt).scalars().all())


# =========================================================================
# WorksheetRowRepository
# =========================================================================

class WorksheetRowRepository:
    """WorksheetRow model-ийн database operations."""

    @staticmethod
    def get_by_id(row_id: int) -> Optional[WorksheetRow]:
        return db.session.get(WorksheetRow, row_id)

    @staticmethod
    def get_for_worksheet(worksheet_id: int) -> list[WorksheetRow]:
        """Worksheet-ийн бүх мөр, position-аар sort."""
        stmt = (
            select(WorksheetRow)
            .where(WorksheetRow.worksheet_id == worksheet_id)
            .order_by(WorksheetRow.position)
        )
        return list(db.session.execute(stmt).scalars().all())

    @staticmethod
    def delete_for_worksheet(worksheet_id: int) -> int:
        """Worksheet-ийн бүх мөрийг устгах (мөр save хийхээс өмнө).

        Returns: устгасан тоо.
        """
        stmt = delete(WorksheetRow).where(WorksheetRow.worksheet_id == worksheet_id)
        return db.session.execute(stmt).rowcount

    @staticmethod
    def get_for_lot_with_result(lot_id: int) -> list[WorksheetRow]:
        """Тухайн reagent lot хэрэглэсэн, AnalysisResult-той холбоотой мөрүүд.

        chemical_service.invalidate_results_by_lot-д ашиглана.
        """
        stmt = select(WorksheetRow).where(
            WorksheetRow.reagent_lot_id == lot_id,
            WorksheetRow.analysis_result_id.isnot(None),
        )
        return list(db.session.execute(stmt).scalars().all())
