# app/repositories/analysis_audit_repository.py
# -*- coding: utf-8 -*-
"""
AnalysisResultLog Repository — Шинжилгээний үр дүнгийн audit log (read-only).

⚠️ AnalysisResultLog нь HashableMixin model — UPDATE/DELETE blocked at
SQLAlchemy event level (ISO 17025 audit immutability). Repository нь зөвхөн
read query-уудыг агуулна; бичих үйлдлийг шууд session.add() хийнэ.
"""

from __future__ import annotations

from typing import Optional

from sqlalchemy import func

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
        query = AnalysisResultLog.query.filter_by(sample_id=sample_id) \
            .order_by(AnalysisResultLog.timestamp.desc())
        if limit is not None:
            query = query.limit(limit)
        return query.all()

    @staticmethod
    def get_for_result(result_id: int) -> list[AnalysisResultLog]:
        """Тухайн AnalysisResult-ийн бүх log."""
        return AnalysisResultLog.query.filter_by(analysis_result_id=result_id) \
            .order_by(AnalysisResultLog.timestamp.desc()).all()

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
        q = db.session.query(
            AnalysisResultLog.error_reason,
            func.count(AnalysisResultLog.id),
        ).filter(
            AnalysisResultLog.error_reason.isnot(None),
            AnalysisResultLog.error_reason != "",
        )

        if date_from is not None:
            q = q.filter(AnalysisResultLog.timestamp >= date_from)
        if date_to is not None:
            q = q.filter(AnalysisResultLog.timestamp < date_to)

        if username:
            from app.utils.security import escape_like_pattern
            safe = escape_like_pattern(username)
            q = q.join(User, AnalysisResultLog.user_id == User.id).filter(
                User.username.ilike(f"%{safe}%")
            )

        return q.group_by(AnalysisResultLog.error_reason).all()
