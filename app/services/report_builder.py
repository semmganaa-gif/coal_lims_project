# app/services/report_builder.py
# -*- coding: utf-8 -*-
"""
Ad-hoc Report Builder — dynamic query builder for custom reports.

Хэрэглэгч баганууд, шүүлтүүр, бүлэглэл, эрэмбэлэл сонгож
тайлан бүтээнэ. Template хадгалж дахин ашиглана.

Report config JSON формат:
{
    "name": "Сарын нүүрсний шинжилгээ",
    "entity": "analysis_result",       # analysis_result | sample
    "columns": ["sample_code", "analysis_code", "final_result", "status", "updated_at"],
    "filters": [
        {"field": "lab_type", "op": "eq", "value": "coal"},
        {"field": "updated_at", "op": "gte", "value": "2026-01-01"},
        {"field": "status", "op": "in", "value": ["approved"]}
    ],
    "group_by": ["analysis_code"],
    "aggregations": [
        {"field": "final_result", "func": "avg", "alias": "avg_result"},
        {"field": "final_result", "func": "count", "alias": "count"}
    ],
    "order_by": [{"field": "analysis_code", "dir": "asc"}],
    "limit": 1000
}
"""

import csv
import io
import json
import logging
from datetime import datetime, date
from decimal import Decimal
from typing import Optional

from sqlalchemy import func, and_, or_, cast, String
from sqlalchemy.orm import joinedload

from app.bootstrap.extensions import db
from app.models.core import Sample, User
from app.models.analysis import AnalysisResult, AnalysisType
from app.models.settings import SystemSetting
from app.utils.datetime import now_local

logger = logging.getLogger(__name__)

# Maximum rows in a single report
MAX_REPORT_ROWS = 10000

# ──────────────────────────────────────────
# Column definitions (what users can select)
# ──────────────────────────────────────────

ENTITY_COLUMNS = {
    "analysis_result": {
        # AnalysisResult fields
        "id": {"label": "ID", "type": "int", "model": "AnalysisResult", "field": "id"},
        "sample_code": {"label": "Дээжний код", "type": "str", "model": "Sample", "field": "sample_code", "join": "sample"},
        "analysis_code": {"label": "Шинжилгээний код", "type": "str", "model": "AnalysisResult", "field": "analysis_code"},
        "final_result": {"label": "Эцсийн үр дүн", "type": "float", "model": "AnalysisResult", "field": "final_result"},
        "status": {"label": "Төлөв", "type": "str", "model": "AnalysisResult", "field": "status"},
        "lab_type": {"label": "Лаб", "type": "str", "model": "Sample", "field": "lab_type", "join": "sample"},
        "sample_type": {"label": "Дээжний төрөл", "type": "str", "model": "Sample", "field": "sample_type", "join": "sample"},
        "client_name": {"label": "Захиалагч", "type": "str", "model": "Sample", "field": "client_name", "join": "sample"},
        "received_date": {"label": "Хүлээн авсан", "type": "date", "model": "Sample", "field": "received_date", "join": "sample"},
        "updated_at": {"label": "Шинэчлэгдсэн", "type": "datetime", "model": "AnalysisResult", "field": "updated_at"},
        "created_at": {"label": "Үүсгэсэн", "type": "datetime", "model": "AnalysisResult", "field": "created_at"},
        "rejection_category": {"label": "Татгалзсан шалтгаан", "type": "str", "model": "AnalysisResult", "field": "rejection_category"},
    },
    "sample": {
        "id": {"label": "ID", "type": "int", "model": "Sample", "field": "id"},
        "sample_code": {"label": "Дээжний код", "type": "str", "model": "Sample", "field": "sample_code"},
        "lab_type": {"label": "Лаб", "type": "str", "model": "Sample", "field": "lab_type"},
        "sample_type": {"label": "Дээжний төрөл", "type": "str", "model": "Sample", "field": "sample_type"},
        "client_name": {"label": "Захиалагч", "type": "str", "model": "Sample", "field": "client_name"},
        "status": {"label": "Төлөв", "type": "str", "model": "Sample", "field": "status"},
        "received_date": {"label": "Хүлээн авсан", "type": "date", "model": "Sample", "field": "received_date"},
        "priority": {"label": "Яаралтай", "type": "str", "model": "Sample", "field": "priority"},
        "due_date": {"label": "Хугацаа", "type": "datetime", "model": "Sample", "field": "due_date"},
        "completed_at": {"label": "Дууссан", "type": "datetime", "model": "Sample", "field": "completed_at"},
        "created_at": {"label": "Үүсгэсэн", "type": "datetime", "model": "Sample", "field": "created_at"},
    },
}

# Model class mapping
_MODELS = {
    "AnalysisResult": AnalysisResult,
    "Sample": Sample,
}

# Aggregation functions
_AGG_FUNCS = {
    "count": func.count,
    "sum": func.sum,
    "avg": func.avg,
    "min": func.min,
    "max": func.max,
}

# Filter operators
_FILTER_OPS = {
    "eq": lambda col, val: col == val,
    "ne": lambda col, val: col != val,
    "gt": lambda col, val: col > val,
    "gte": lambda col, val: col >= val,
    "lt": lambda col, val: col < val,
    "lte": lambda col, val: col <= val,
    "in": lambda col, val: col.in_(val) if isinstance(val, list) else col == val,
    "not_in": lambda col, val: ~col.in_(val) if isinstance(val, list) else col != val,
    "like": lambda col, val: col.ilike(f"%{val}%"),
    "is_null": lambda col, val: col.is_(None),
    "not_null": lambda col, val: col.isnot(None),
}


def _get_column(entity: str, col_name: str):
    """Get SQLAlchemy column from entity + column name."""
    col_def = ENTITY_COLUMNS.get(entity, {}).get(col_name)
    if not col_def:
        raise ValueError(f"Unknown column: {entity}.{col_name}")

    model_cls = _MODELS.get(col_def["model"])
    if not model_cls:
        raise ValueError(f"Unknown model: {col_def['model']}")

    return getattr(model_cls, col_def["field"])


def _coerce_value(val, col_type: str):
    """Coerce filter value to appropriate Python type."""
    if val is None:
        return None
    if col_type == "int":
        return int(val)
    if col_type == "float":
        return float(val)
    if col_type == "date":
        if isinstance(val, str):
            return datetime.strptime(val, "%Y-%m-%d").date()
        return val
    if col_type == "datetime":
        if isinstance(val, str):
            return datetime.fromisoformat(val)
        return val
    return str(val)


def build_query(config: dict):
    """
    Build SQLAlchemy query from report config.

    Returns: (query, column_labels)
    """
    entity = config.get("entity", "analysis_result")
    columns = config.get("columns", [])
    filters = config.get("filters", [])
    group_by = config.get("group_by", [])
    aggregations = config.get("aggregations", [])
    order_by = config.get("order_by", [])
    limit = min(config.get("limit", 1000), MAX_REPORT_ROWS)

    if entity not in ENTITY_COLUMNS:
        raise ValueError(f"Unknown entity: {entity}")

    # Determine base model
    if entity == "analysis_result":
        base_model = AnalysisResult
    else:
        base_model = Sample

    # Build select columns
    needs_join = False
    select_cols = []
    col_labels = []

    if aggregations and group_by:
        # Aggregation query
        for gb in group_by:
            col = _get_column(entity, gb)
            select_cols.append(col.label(gb))
            col_labels.append(gb)
            col_def = ENTITY_COLUMNS[entity].get(gb, {})
            if col_def.get("join"):
                needs_join = True

        for agg in aggregations:
            agg_field = agg.get("field", "id")
            agg_func_name = agg.get("func", "count")
            alias = agg.get("alias", f"{agg_func_name}_{agg_field}")

            agg_func = _AGG_FUNCS.get(agg_func_name)
            if not agg_func:
                raise ValueError(f"Unknown aggregation: {agg_func_name}")

            col = _get_column(entity, agg_field)
            select_cols.append(agg_func(col).label(alias))
            col_labels.append(alias)
    else:
        # Regular query
        if not columns:
            columns = list(ENTITY_COLUMNS[entity].keys())[:10]

        for col_name in columns:
            col = _get_column(entity, col_name)
            select_cols.append(col.label(col_name))
            col_labels.append(col_name)
            col_def = ENTITY_COLUMNS[entity].get(col_name, {})
            if col_def.get("join"):
                needs_join = True

    # Build query
    query = db.session.query(*select_cols)

    # Join if needed
    if needs_join and entity == "analysis_result":
        query = query.join(Sample, AnalysisResult.sample_id == Sample.id)

    # Apply filters
    for f in filters:
        field_name = f.get("field", "")
        op = f.get("op", "eq")
        value = f.get("value")

        col_def = ENTITY_COLUMNS[entity].get(field_name)
        if not col_def:
            continue

        col = _get_column(entity, field_name)
        op_func = _FILTER_OPS.get(op)
        if not op_func:
            continue

        if op not in ("is_null", "not_null"):
            if isinstance(value, list):
                value = [_coerce_value(v, col_def["type"]) for v in value]
            else:
                value = _coerce_value(value, col_def["type"])

        if col_def.get("join") and not needs_join and entity == "analysis_result":
            query = query.join(Sample, AnalysisResult.sample_id == Sample.id)
            needs_join = True

        query = query.filter(op_func(col, value))

    # Group by
    if group_by:
        for gb in group_by:
            col = _get_column(entity, gb)
            query = query.group_by(col)

    # Order by
    for ob in order_by:
        field_name = ob.get("field", "")
        direction = ob.get("dir", "asc")
        col = _get_column(entity, field_name)
        if direction == "desc":
            query = query.order_by(col.desc())
        else:
            query = query.order_by(col.asc())

    query = query.limit(limit)

    return query, col_labels


def execute_report(config: dict) -> dict:
    """
    Execute report query and return results.

    Returns:
        {
            "columns": [...],
            "rows": [[...], ...],
            "total": int,
            "config": {...}
        }
    """
    query, col_labels = build_query(config)
    results = query.all()

    rows = []
    for row in results:
        row_data = []
        for i, label in enumerate(col_labels):
            val = row[i] if hasattr(row, '__getitem__') else getattr(row, label, None)
            # Serialize
            if isinstance(val, (datetime, date)):
                val = val.isoformat()
            elif isinstance(val, (float, Decimal)):
                val = round(float(val), 4)
            row_data.append(val)
        rows.append(row_data)

    return {
        "columns": col_labels,
        "column_labels": {
            c: ENTITY_COLUMNS.get(config.get("entity", "analysis_result"), {}).get(c, {}).get("label", c)
            for c in col_labels
        },
        "rows": rows,
        "total": len(rows),
    }


def export_report_csv(config: dict) -> str:
    """Export report as CSV string."""
    result = execute_report(config)
    output = io.StringIO()
    writer = csv.writer(output)

    # Header with labels
    headers = [result["column_labels"].get(c, c) for c in result["columns"]]
    writer.writerow(headers)

    for row in result["rows"]:
        writer.writerow(row)

    return output.getvalue()


def export_report_json(config: dict) -> str:
    """Export report as JSON string."""
    result = execute_report(config)

    # Convert rows to list of dicts
    records = []
    for row in result["rows"]:
        record = {}
        for i, col in enumerate(result["columns"]):
            record[col] = row[i]
        records.append(record)

    return json.dumps({
        "report_name": config.get("name", "Ad-hoc Report"),
        "generated_at": now_local().isoformat(),
        "total": result["total"],
        "columns": result["columns"],
        "column_labels": result["column_labels"],
        "data": records,
    }, ensure_ascii=False, indent=2)


# ──────────────────────────────────────────
# Report template management
# ──────────────────────────────────────────

def save_report_template(name: str, config: dict, user_id: int,
                         description: str = "") -> int:
    """Save report template to SystemSetting."""
    config["name"] = name

    setting = SystemSetting.query.filter_by(
        category="report_template",
        key=name,
    ).first()

    if setting:
        setting.value = json.dumps(config, ensure_ascii=False)
        setting.description = description
        setting.updated_by_id = user_id
    else:
        setting = SystemSetting(
            category="report_template",
            key=name,
            value=json.dumps(config, ensure_ascii=False),
            description=description,
            is_active=True,
            updated_by_id=user_id,
        )
        db.session.add(setting)

    db.session.commit()
    return setting.id


def get_report_template(name: str) -> Optional[dict]:
    """Get saved report template."""
    setting = SystemSetting.query.filter_by(
        category="report_template",
        key=name,
        is_active=True,
    ).first()

    if not setting:
        return None

    try:
        return json.loads(setting.value)
    except (json.JSONDecodeError, TypeError):
        return None


def list_report_templates() -> list[dict]:
    """List all saved report templates."""
    settings = SystemSetting.query.filter_by(
        category="report_template",
        is_active=True,
    ).order_by(SystemSetting.sort_order, SystemSetting.key).all()

    result = []
    for s in settings:
        try:
            config = json.loads(s.value)
        except (json.JSONDecodeError, TypeError):
            continue

        result.append({
            "id": s.id,
            "name": s.key,
            "description": s.description or "",
            "entity": config.get("entity", ""),
            "column_count": len(config.get("columns", [])),
            "filter_count": len(config.get("filters", [])),
            "updated_at": s.updated_at.isoformat() if s.updated_at else None,
        })

    return result


def delete_report_template(name: str) -> bool:
    """Soft-delete report template."""
    setting = SystemSetting.query.filter_by(
        category="report_template",
        key=name,
    ).first()

    if setting:
        setting.is_active = False
        db.session.commit()
        return True
    return False


def get_available_columns(entity: str) -> list[dict]:
    """Get available columns for an entity."""
    cols = ENTITY_COLUMNS.get(entity, {})
    return [
        {
            "name": name,
            "label": info["label"],
            "type": info["type"],
        }
        for name, info in cols.items()
    ]


def get_available_entities() -> list[dict]:
    """Get available entities for report building."""
    return [
        {"name": "analysis_result", "label": "Шинжилгээний үр дүн", "label_en": "Analysis Results"},
        {"name": "sample", "label": "Дээж", "label_en": "Samples"},
    ]
