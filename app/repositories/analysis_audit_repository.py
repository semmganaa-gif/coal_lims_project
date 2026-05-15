# app/repositories/analysis_audit_repository.py
# -*- coding: utf-8 -*-
"""
AnalysisResultLog Repository — Шинжилгээний үр дүнгийн audit log (read-only).

⚠️ AnalysisResultLog нь HashableMixin model — UPDATE/DELETE blocked at
SQLAlchemy event level (ISO 17025 audit immutability). Repository нь зөвхөн
read query-уудыг агуулна; бичих үйлдлийг шууд session.add() хийнэ.

SQLAlchemy 2.0 native API (`select()` builder) ашиглана.
"""

from __future__ import annotations

from typing import Optional

from sqlalchemy import func, select

from app import db
from app.models.analysis_audit import AnalysisResultLog
from app.models.core import User


class AnalysisResultLogRepository:
    """AnalysisResultLog model-ийн read-only database operations."""

    # =========================================================================
    # Basic queries
    # =========================================================================

    @staticmethod
    def get_by_id(log_id: int) -> Optional[AnalysisResultLog]:
        return db.session.get(AnalysisResultLog, log_id)

    @staticmethod
    def get_for_sample(sample_id: int,
                       limit: Optional[int] = None) -> list[AnalysisResultLog]:
        """Тухайн дээжний бүх audit log (timestamp desc).

        Args:
            sample_id: Sample.id
            limit: hard limit, None бол бүх log
        """
        stmt = (
            select(AnalysisResultLog)
            .where(AnalysisResultLog.sample_id == sample_id)
            .order_by(AnalysisResultLog.timestamp.desc())
        )
        if limit is not None:
            stmt = stmt.limit(limit)
        return list(db.session.execute(stmt).scalars().all())

    @staticmethod
    def get_for_result(result_id: int) -> list[AnalysisResultLog]:
        """Тухайн AnalysisResult-ийн бүх log."""
        stmt = (
            select(AnalysisResultLog)
            .where(AnalysisResultLog.analysis_result_id == result_id)
            .order_by(AnalysisResultLog.timestamp.desc())
        )
        return list(db.session.execute(stmt).scalars().all())

    # =========================================================================
    # Aggregation queries (KPI dashboards)
    # =========================================================================

    @staticmethod
    def get_error_reason_counts(date_from=None, date_to=None,
                                username: Optional[str] = None) -> list[tuple]:
        """Алдааны шалтгаанаар group-by count.

        Returns: list of (error_reason, count) tuples.

        Args:
            date_from: timestamp >= date_from (datetime)
            date_to:   timestamp <  date_to (datetime, exclusive)
            username:  ilike pattern (user-аар шүүх)
        """
        stmt = select(
            AnalysisResultLog.error_reason,
            func.count(AnalysisResultLog.id),
        ).where(
            AnalysisResultLog.error_reason.isnot(None),
            AnalysisResultLog.error_reason != "",
        )

        if date_from is not None:
            stmt = stmt.where(AnalysisResultLog.timestamp >= date_from)
        if date_to is not None:
            stmt = stmt.where(AnalysisResultLog.timestamp < date_to)

        if username:
            from app.utils.security import escape_like_pattern
            safe = escape_like_pattern(username)
            stmt = stmt.join(User, AnalysisResultLog.user_id == User.id).where(
                User.username.ilike(f"%{safe}%")
            )

        stmt = stmt.group_by(AnalysisResultLog.error_reason)
        return list(db.session.execute(stmt).all())
