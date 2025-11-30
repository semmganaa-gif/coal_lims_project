# app/config/analysis_schema.py
# -*- coding: utf-8 -*-
from __future__ import annotations
from copy import deepcopy

DEFAULT_PARALLEL_TITLE = "Туршилтын жин / үр дүн"
DEFAULT_PARALLEL_COLUMNS = [
    {"key": "num", "label": "№"},
    {"key": "m1", "label": "m1", "unit": "g"},
    {"key": "m2", "label": "m2", "unit": "g"},
    {"key": "m3", "label": "m3", "unit": "g"},
    {"key": "result", "label": "Үр дүн", "format": "float"},
]

ANALYSIS_SCHEMAS: dict[str, dict] = {
    "MT": {
        "parallels": {
            "title": "Туршилтын жин / үр дүн (m1/m2/m3)",
            "columns": DEFAULT_PARALLEL_COLUMNS,
        }
    },
    "Mad": {"parallels": {"columns": DEFAULT_PARALLEL_COLUMNS}},
    "Aad": {"parallels": {"columns": DEFAULT_PARALLEL_COLUMNS}},
    "Vad": {"parallels": {"columns": DEFAULT_PARALLEL_COLUMNS}},
    "TS": {"parallels": {"columns": DEFAULT_PARALLEL_COLUMNS}},
    "P": {"parallels": {"columns": DEFAULT_PARALLEL_COLUMNS}},
    "F": {"parallels": {"columns": DEFAULT_PARALLEL_COLUMNS}},
    "Cl": {"parallels": {"columns": DEFAULT_PARALLEL_COLUMNS}},
    "TRD": {
        "parallels": {
            "columns": [
                {"key": "num", "label": "Тигель №"},
                {"key": "m1", "label": "m1 (хоосон)", "unit": "g"},
                {"key": "m2", "label": "m2 (дүүрэн)", "unit": "g"},
                {"key": "m", "label": "m (нүүрсний масс)", "unit": "g"},
                {"key": "result", "label": "TRD", "format": "float"},
            ]
        }
    },
    "CSN": {
        "parallels": {
            "title": "CSN ?? ???",
            "columns": [
                {"key": "v1", "label": "v1", "format": "float"},
                {"key": "v2", "label": "v2", "format": "float"},
                {"key": "v3", "label": "v3", "format": "float"},
                {"key": "v4", "label": "v4", "format": "float"},
                {"key": "v5", "label": "v5", "format": "float"},
            ],
        }
    }
}


def get_analysis_schema(analysis_code: str | None) -> dict:
    """
    Return schema metadata for the given analysis code.
    A shallow copy is returned so callers can mutate safely.
    """
    defaults = {
        "parallels": {
            "title": DEFAULT_PARALLEL_TITLE,
            "columns": deepcopy(DEFAULT_PARALLEL_COLUMNS),
        }
    }
    if not analysis_code:
        return defaults
    base = ANALYSIS_SCHEMAS.get(analysis_code, {}) or ANALYSIS_SCHEMAS.get(
        analysis_code.upper(), {}
    )
    merged = deepcopy(defaults)
    parallels = base.get("parallels")
    if parallels:
        merged["parallels"]["title"] = parallels.get("title") or merged["parallels"]["title"]
        if parallels.get("columns"):
            merged["parallels"]["columns"] = deepcopy(parallels["columns"])
    return merged
