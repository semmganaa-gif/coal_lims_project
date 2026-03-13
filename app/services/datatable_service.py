# app/services/datatable_service.py
# -*- coding: utf-8 -*-
"""
DataTables server-side processing бизнес логик.

Sample listing, column filtering, status aggregation.
"""
from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from datetime import date, datetime
from typing import Any, Optional

from app import db
from app.models import AnalysisResult, Sample
from app.repositories import AnalysisResultRepository
from app.utils.codes import to_base_list
from app.utils.security import escape_like_pattern

logger = logging.getLogger(__name__)


@dataclass
class DataTableResult:
    """DataTables response data."""

    draw: int
    records_total: int
    records_filtered: int
    data: list[list]


# Column index → Sample attribute mapping
_LIKE_COLUMNS = {
    2: "sample_code",
    3: "client_name",
    4: "sample_type",
    5: "sample_condition",
    6: "delivered_by",
    7: "prepared_by",
    9: "notes",
    13: "analyses_to_perform",
}


def query_samples_datatable(
    draw: int,
    start: int,
    length: int,
    column_search: dict[int, str],
    date_start: Optional[str] = None,
    date_end: Optional[str] = None,
) -> DataTableResult:
    """
    DataTables server-side query.

    Args:
        draw: DataTables draw counter
        start: Pagination offset
        length: Page size (max 1000)
        column_search: {column_index: search_value}
        date_start: Date filter start (ISO format)
        date_end: Date filter end (ISO format)

    Returns:
        DataTableResult объект
    """
    length = min(length, 1000)
    q = Sample.query.filter(Sample.lab_type == "coal")

    # Date range filter
    q = _apply_date_filter(q, date_start, date_end)

    # Column filters
    q = _apply_column_filters(q, column_search)

    records_total = q.count()

    samples = (
        q.order_by(Sample.received_date.desc())
        .offset(start)
        .limit(length)
        .all()
    )

    # Status map (нэг query-ээр бүх дээжүүдийн статус)
    sample_ids = [s.id for s in samples]
    status_map = AnalysisResultRepository.get_status_map_for_samples(sample_ids)

    # Row data бэлдэх
    data_rows = [_build_sample_row(s, status_map) for s in samples]

    return DataTableResult(
        draw=draw,
        records_total=records_total,
        records_filtered=records_total,
        data=data_rows,
    )


def _apply_date_filter(q, date_start: Optional[str], date_end: Optional[str]):
    """Date range filter."""
    if date_start:
        try:
            q = q.filter(Sample.received_date >= datetime.fromisoformat(date_start))
        except ValueError:
            pass
    if date_end:
        try:
            q = q.filter(Sample.received_date <= datetime.fromisoformat(date_end))
        except ValueError:
            pass
    return q


def _apply_column_filters(q, column_search: dict[int, str]):
    """Column-тус бүрийн filter."""
    for idx, val in column_search.items():
        if not val:
            continue

        # ID column (exact int match)
        if idx == 1:
            try:
                q = q.filter(Sample.id == int(val))
            except ValueError:
                pass
            continue

        # Weight column (exact float match)
        if idx == 11:
            try:
                q = q.filter(Sample.weight == float(val))
            except ValueError:
                pass
            continue

        # LIKE columns
        attr_name = _LIKE_COLUMNS.get(idx)
        if attr_name:
            safe_val = escape_like_pattern(val)
            col = getattr(Sample, attr_name, None)
            if col is not None:
                q = q.filter(col.ilike(f"%{safe_val}%"))

    return q


def _build_sample_row(s: Sample, status_map: dict[int, set[str]]) -> list:
    """Нэг дээжний DataTables row бэлдэх."""
    from markupsafe import escape
    from flask import url_for
    from app.routes.api.helpers import _aggregate_sample_status

    # analyses_to_perform → base code list
    try:
        raw_codes = json.loads(s.analyses_to_perform or "[]")
    except (json.JSONDecodeError, TypeError):
        raw_codes = []
    analyses_txt = json.dumps(to_base_list(raw_codes), ensure_ascii=False)

    # Sample condition
    sample_condition_val = getattr(s, "sample_condition", None) or getattr(s, "sample_state", None) or ""

    # Aggregated status
    result_statuses = status_map.get(s.id, set())
    workflow_status = _aggregate_sample_status(s.status or "", result_statuses)

    # Action button
    action_html = (
        f'<a href="{url_for("main.edit_sample", sample_id=s.id)}" '
        f'class="btn btn-sm btn-outline-primary">Edit</a>'
    )

    # Retention badge
    retention_html = _build_retention_badge(s)

    return [
        f'<input type="checkbox" class="sample-checkbox" value="{s.id}">',
        s.id,
        escape(s.sample_code or ""),
        escape(s.client_name or ""),
        escape(s.sample_type or ""),
        escape(sample_condition_val or ""),
        escape(s.delivered_by or ""),
        escape(s.prepared_by or ""),
        escape(s.prepared_date.strftime("%Y-%m-%d") if s.prepared_date else ""),
        escape(s.notes or ""),
        s.received_date.strftime("%Y-%m-%d %H:%M") if s.received_date else "",
        s.weight or "",
        escape(workflow_status),
        escape(analyses_txt),
        retention_html,
        action_html,
    ]


def _build_retention_badge(s: Sample) -> str:
    """Хадгалах хугацааны badge HTML."""
    if s.return_sample:
        return '<span class="badge bg-primary">Return</span>'
    if not s.retention_date:
        return '<span class="badge bg-secondary">-</span>'

    days_left = (s.retention_date - date.today()).days
    if days_left < 0:
        return f'<span class="badge bg-danger">{abs(days_left)} days overdue</span>'
    if days_left <= 7:
        return f'<span class="badge bg-warning text-dark">{days_left} days</span>'
    if days_left <= 30:
        return f'<span class="badge bg-info">{days_left} days</span>'
    return f'<span class="badge bg-success">{days_left} days</span>'
