# app/repositories/qc_chart_repository.py
# -*- coding: utf-8 -*-
"""
QCControlChart Repository - Westgard QC хяналтын картын database operations.

⚠️ QCControlChart нь HashableMixin model — UPDATE/DELETE blocked
(audit immutability, ISO 17025 clause 7.7.1 statistical process control).
"""

from __future__ import annotations

from typing import Optional

from sqlalchemy import select

from app import db
from app.models.quality_records import QCControlChart


class QCControlChartRepository:
    """QCControlChart model-ийн database operations.

    ⚠️ HashableMixin model — DELETE/UPDATE blocked at SQLAlchemy event level.
    """

    @staticmethod
    def get_by_id(chart_id: int) -> Optional[QCControlChart]:
        return db.session.get(QCControlChart, chart_id)

    @staticmethod
    def get_unique_analysis_qc_pairs() -> list[tuple[str, str]]:
        """Distinct (analysis_code, qc_sample_name) хосууд.

        Westgard rule-ийг бүх QC дээж тус бүрээр шалгахад ашиглана.
        """
        return db.session.query(
            QCControlChart.analysis_code,
            QCControlChart.qc_sample_name,
        ).distinct().all()

    @staticmethod
    def get_recent_for_qc(analysis_code: str, qc_sample_name: str,
                          limit: int = 20) -> list[QCControlChart]:
        """Тухайн analysis_code + qc_sample-ын сүүлийн хяналтын картууд.

        measurement_date desc-ээр sort — Westgard rule-д сүүлийн утгууд хэрэгтэй.
        """
        return db.session.execute(
            select(QCControlChart).filter_by(
                analysis_code=analysis_code,
                qc_sample_name=qc_sample_name,
            ).order_by(QCControlChart.measurement_date.desc()).limit(limit)
        ).scalars().all()
