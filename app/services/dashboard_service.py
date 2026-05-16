# app/services/dashboard_service.py
# -*- coding: utf-8 -*-
"""
Dashboard statistics and archive hub бизнес логик.

Route-ийн inline DB query-уудыг энд төвлөрүүлсэн.
"""
from __future__ import annotations

import logging
from collections import defaultdict
from dataclasses import dataclass
from datetime import date, timedelta
from typing import Optional

from sqlalchemy import case, extract, func, select

from app import db
from app.constants import AnalysisResultStatus, SampleStatus, DASHBOARD_RECENT_LIMIT
from app.models import AnalysisResult, Sample
from app.repositories import AnalysisTypeRepository
from app.utils.datetime import now_local

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------


@dataclass
class DashboardStats:
    """Dashboard chart data."""

    samples_by_day: list[dict]
    samples_by_client: list[dict]
    analysis_by_status: list[dict]
    approval_stats: dict[str, int]
    today: dict[str, int]


@dataclass
class ArchiveTreeData:
    """Archive hub tree structure."""

    tree_data: dict
    client_totals: dict[str, int]
    total_archived: int
    samples: list
    results_map: dict[int, dict]
    analysis_types: list


# ---------------------------------------------------------------------------
# Dashboard statistics
# ---------------------------------------------------------------------------


def get_dashboard_stats() -> DashboardStats:
    """
    Dashboard-ийн Chart.js-д шаардлагатай бүх статистик.

    Returns:
        DashboardStats объект
    """
    today = now_local().date()
    first_of_month = today.replace(day=1)

    # 1. Сүүлийн 7 хоногийн дээж тоо
    samples_by_day = _get_samples_by_day(today)

    # 2. Клиент тус бүрийн дээж тоо (энэ сар)
    client_rows = (
        db.session.query(Sample.client_name, func.count(Sample.id))
        .filter(Sample.lab_type == "coal", Sample.received_date >= first_of_month)
        .group_by(Sample.client_name)
        .all()
    )
    samples_by_client = [{"client": c, "count": cnt} for c, cnt in client_rows]

    # 3. Шинжилгээний статус тоо (өнөөдөр)
    status_rows = (
        db.session.query(AnalysisResult.status, func.count(AnalysisResult.id))
        .join(Sample, AnalysisResult.sample_id == Sample.id)
        .filter(Sample.lab_type == "coal", func.date(AnalysisResult.updated_at) == today)
        .group_by(AnalysisResult.status)
        .all()
    )
    analysis_by_status = [{"status": s, "count": cnt} for s, cnt in status_rows]

    # 4. Энэ сарын approve/reject/pending харьцаа
    approval = (
        db.session.query(
            func.sum(case((AnalysisResult.status == AnalysisResultStatus.APPROVED.value, 1), else_=0)).label("approved"),
            func.sum(case((AnalysisResult.status == AnalysisResultStatus.REJECTED.value, 1), else_=0)).label("rejected"),
            func.sum(case((AnalysisResult.status == AnalysisResultStatus.PENDING_REVIEW.value, 1), else_=0)).label("pending"),
        )
        .join(Sample, AnalysisResult.sample_id == Sample.id)
        .filter(Sample.lab_type == "coal", AnalysisResult.updated_at >= first_of_month)
        .first()
    )

    # 5. Өнөөдрийн нэгдсэн статистик
    today_samples = db.session.execute(
        select(func.count(Sample.id)).where(
            Sample.lab_type == "coal",
            func.date(Sample.received_date) == today,
        )
    ).scalar_one()

    today_analyses = (
        db.session.query(func.count(AnalysisResult.id))
        .join(Sample, AnalysisResult.sample_id == Sample.id)
        .filter(Sample.lab_type == "coal", func.date(AnalysisResult.created_at) == today)
        .scalar()
    )

    pending_review = (
        db.session.query(func.count(AnalysisResult.id))
        .join(Sample, AnalysisResult.sample_id == Sample.id)
        .filter(Sample.lab_type == "coal", AnalysisResult.status == AnalysisResultStatus.PENDING_REVIEW.value)
        .scalar()
    )

    return DashboardStats(
        samples_by_day=samples_by_day,
        samples_by_client=samples_by_client,
        analysis_by_status=analysis_by_status,
        approval_stats={
            "approved": approval.approved or 0,
            "rejected": approval.rejected or 0,
            "pending": approval.pending or 0,
        },
        today={
            "samples": today_samples,
            "analyses": today_analyses,
            "pending_review": pending_review,
        },
    )


def _get_samples_by_day(today: date) -> list[dict]:
    """Сүүлийн 7 хоногийн дээж тоо."""
    day_names = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    result = []
    for i in range(6, -1, -1):
        day = today - timedelta(days=i)
        count = db.session.execute(
            select(func.count(Sample.id)).where(
                Sample.lab_type == "coal",
                func.date(Sample.received_date) == day,
            )
        ).scalar_one()
        result.append({
            "date": day.strftime("%m/%d"),
            "day_name": day_names[day.weekday()],
            "count": count,
        })
    return result


# ---------------------------------------------------------------------------
# Archive hub
# ---------------------------------------------------------------------------


def get_archive_tree(
    selected_client: Optional[str] = None,
    selected_type: Optional[str] = None,
    selected_year: Optional[int] = None,
    selected_month: Optional[int] = None,
) -> ArchiveTreeData:
    """
    Archive hub-ийн tree бүтэц + шүүсэн дээжүүд.

    Args:
        selected_client: Сонгосон клиент
        selected_type: Сонгосон дээжний төрөл
        selected_year: Сонгосон жил
        selected_month: Сонгосон сар

    Returns:
        ArchiveTreeData объект
    """
    # 1. Архивлагдсан дээжний статистик (Client → Type → Year → Month)
    archive_stats = (
        db.session.query(
            Sample.client_name,
            Sample.sample_type,
            extract("year", Sample.received_date).label("year"),
            extract("month", Sample.received_date).label("month"),
            func.count(Sample.id).label("count"),
        )
        .filter(Sample.status == SampleStatus.ARCHIVED.value, Sample.lab_type == "coal")
        .group_by(
            Sample.client_name,
            Sample.sample_type,
            extract("year", Sample.received_date),
            extract("month", Sample.received_date),
        )
        .order_by(
            Sample.client_name,
            Sample.sample_type,
            extract("year", Sample.received_date).desc(),
            extract("month", Sample.received_date).desc(),
        )
        .all()
    )

    # 2. Tree бүтэц
    tree_data: dict = defaultdict(
        lambda: defaultdict(lambda: defaultdict(lambda: defaultdict(int)))
    )
    client_totals: dict[str, int] = defaultdict(int)
    total_archived = 0

    for row in archive_stats:
        client = row.client_name or "Unknown"
        stype = row.sample_type or "Other"
        year = int(row.year) if row.year else 0
        month = int(row.month) if row.month else 0
        count = row.count
        tree_data[client][stype][year][month] = count
        client_totals[client] += count
        total_archived += count

    # 3. Drill-down дээжүүд НЕ ачаалагдана энэ funkc-аас — Frontend AG Grid
    #    /api/v1/archive_hub/page endpoint-аас server-side pagination-аар татна.
    #    DASHBOARD_RECENT_LIMIT (500)-аар hardcap байсныг арилгасан.
    samples: list = []
    results_map: dict[int, dict] = {}

    analysis_types = AnalysisTypeRepository.get_all_ordered()

    return ArchiveTreeData(
        tree_data=dict(tree_data),
        client_totals=dict(client_totals),
        total_archived=total_archived,
        samples=samples,
        results_map=results_map,
        analysis_types=analysis_types,
    )


MONTH_NAMES = {
    1: "Jan", 2: "Feb", 3: "Mar", 4: "Apr",
    5: "May", 6: "Jun", 7: "Jul", 8: "Aug",
    9: "Sep", 10: "Oct", 11: "Nov", 12: "Dec",
}
