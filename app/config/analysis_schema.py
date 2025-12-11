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

# Audit log хуудасны баганы тохиргоо
# decimals: тоон нарийвчлал (0=бүхэл, 2=0.01, 3=0.001, 4=0.0001)
# highlight: өнгө тодруулах (p1, p2, diff, avg)
DEFAULT_AUDIT_COLUMNS = [
    {"key": "num", "label": "Тигель", "decimals": 0},
    {"key": "m1", "label": "m1", "decimals": 4},
    {"key": "m2", "label": "m2", "decimals": 4},
    {"key": "m3", "label": "m3", "decimals": 4},
    {"key": "result", "label": "Үр дүн", "decimals": 2},
]

ANALYSIS_SCHEMAS: dict[str, dict] = {
    "MT": {
        "parallels": {
            "title": "Туршилтын жин / үр дүн (m1/m2/m3)",
            "columns": DEFAULT_PARALLEL_COLUMNS,
        },
        "audit_columns": DEFAULT_AUDIT_COLUMNS,
    },
    "Mad": {
        "parallels": {"columns": DEFAULT_PARALLEL_COLUMNS},
        "audit_columns": DEFAULT_AUDIT_COLUMNS,
    },
    "Aad": {
        "parallels": {"columns": DEFAULT_PARALLEL_COLUMNS},
        "audit_columns": DEFAULT_AUDIT_COLUMNS,
    },
    "Vad": {
        "parallels": {"columns": DEFAULT_PARALLEL_COLUMNS},
        "audit_columns": DEFAULT_AUDIT_COLUMNS,
        # Vad-д Mad утга ашигладаг
        "audit_extra_columns": [
            {"key": "mad_used", "label": "Mad", "decimals": 2, "path": "mad_used"},
        ],
    },
    "TS": {
        "parallels": {"columns": DEFAULT_PARALLEL_COLUMNS},
        "audit_columns": [
            {"key": "weight", "label": "Жин", "decimals": 3},
            {"key": "result", "label": "Үр дүн", "decimals": 2},
        ],
    },
    "P": {
        "parallels": {"columns": DEFAULT_PARALLEL_COLUMNS},
        "audit_columns": [
            {"key": "weight", "label": "Жин", "decimals": 3},
            {"key": "result", "label": "Үр дүн", "decimals": 2},
        ],
    },
    "F": {
        "parallels": {"columns": DEFAULT_PARALLEL_COLUMNS},
        "audit_columns": [
            {"key": "weight", "label": "Жин", "decimals": 3},
            {"key": "result", "label": "Үр дүн", "decimals": 2},
        ],
    },
    "Cl": {
        "parallels": {"columns": DEFAULT_PARALLEL_COLUMNS},
        "audit_columns": [
            {"key": "weight", "label": "Жин", "decimals": 3},
            {"key": "result", "label": "Үр дүн", "decimals": 2},
        ],
    },
    "CV": {
        "parallels": {
            "title": "Илчлэг (CV)",
            "columns": [
                {"key": "m", "label": "m (g)", "format": "float"},
                {"key": "dT", "label": "dT", "format": "float"},
                {"key": "S", "label": "S", "format": "float"},
                {"key": "result", "label": "Үр дүн", "format": "float"},
            ],
        },
        "audit_columns": [
            {"key": "m", "label": "m", "decimals": 4},
            {"key": "delta_t", "label": "dT", "decimals": 4},
            {"key": "result", "label": "Үр дүн", "decimals": 2},
        ],
        # CV-д нэмэлт тогтмол утгууд (batch constants)
        "audit_extra_columns": [
            {"key": "E", "label": "E", "decimals": 2, "path": "batch.E"},
            {"key": "q1", "label": "q1", "decimals": 1, "path": "batch.q1"},
            {"key": "q2", "label": "q2", "decimals": 1, "path": "batch.q2"},
            {"key": "s_used", "label": "S", "decimals": 3, "path": "s_used"},
        ],
    },
    "TRD": {
        "parallels": {
            "columns": [
                {"key": "num", "label": "Тигель №"},
                {"key": "m1", "label": "m1 (хоосон)", "unit": "g"},
                {"key": "m2", "label": "m2 (дүүрэн)", "unit": "g"},
                {"key": "m", "label": "m (нүүрсний масс)", "unit": "g"},
                {"key": "result", "label": "TRD", "format": "float"},
            ]
        },
        "audit_columns": [
            {"key": "num", "label": "Бортого", "decimals": 0},
            {"key": "m1", "label": "m1", "decimals": 4},
            {"key": "m2", "label": "m2", "decimals": 4},
            {"key": "m", "label": "m", "decimals": 4},
            {"key": "result", "label": "Үр дүн", "decimals": 3},
        ],
        # TRD-д нэмэлт тогтмол утгууд
        "audit_extra_columns": [
            {"key": "mad_used", "label": "Mad", "decimals": 2, "path": "mad_used"},
            {"key": "temp_c", "label": "T°C", "decimals": 1, "path": "temp_c"},
        ],
    },
    "CSN": {
        "parallels": {
            "title": "CSN хэмжилт",
            "columns": [
                {"key": "v1", "label": "v1", "format": "float"},
                {"key": "v2", "label": "v2", "format": "float"},
                {"key": "v3", "label": "v3", "format": "float"},
                {"key": "v4", "label": "v4", "format": "float"},
                {"key": "v5", "label": "v5", "format": "float"},
            ],
        },
        "audit_columns": [
            {"key": "v1", "label": "v1", "decimals": 1},
            {"key": "v2", "label": "v2", "decimals": 1},
            {"key": "v3", "label": "v3", "decimals": 1},
            {"key": "v4", "label": "v4", "decimals": 1},
            {"key": "v5", "label": "v5", "decimals": 1},
        ],
        # CSN-д нэмэлт үр дүн баганууд
        "audit_result_columns": [
            {"key": "avg", "label": "Дундаж", "decimals": 1, "path": "avg"},
            {"key": "range", "label": "Тохирц", "decimals": 1, "path": "repeatability.range"},
        ],
        "audit_no_parallel": True,  # CSN нь p1/p2 биш, зүгээр л утгууд
    },
    "Gi": {
        "parallels": {
            "columns": [
                {"key": "index", "label": "№"},
                {"key": "result", "label": "Үр дүн", "format": "float"},
            ]
        },
        "audit_columns": [
            {"key": "num", "label": "Тигель", "decimals": 0},
            {"key": "m1", "label": "m1", "decimals": 4},
            {"key": "m2", "label": "m2", "decimals": 4},
            {"key": "m3", "label": "m3", "decimals": 4},
            {"key": "result", "label": "Үр дүн", "decimals": 0},
        ],
    },
    "X": {
        "audit_columns": [
            {"key": "result", "label": "Үр дүн", "decimals": 0},
        ],
    },
    "Y": {
        "audit_columns": [
            {"key": "result", "label": "Үр дүн", "decimals": 0},
        ],
    },
    "CRI": {
        "audit_columns": [
            {"key": "result", "label": "Үр дүн", "decimals": 2},
        ],
    },
    "CSR": {
        "audit_columns": [
            {"key": "result", "label": "Үр дүн", "decimals": 2},
        ],
    },
    "FM": {
        "audit_columns": [
            {"key": "tray_g", "label": "Тавиур", "decimals": 2},
            {"key": "before_g", "label": "Нойтон", "decimals": 2},
            {"key": "after_g", "label": "Хуурай", "decimals": 2},
        ],
        # Үр дүн баганууд (тооцоолсон)
        "audit_result_columns": [
            {"key": "fm_wet_pct", "label": "Wet%", "decimals": 2},
            {"key": "fm_dry_pct", "label": "Dry%", "decimals": 2},
        ],
        "audit_no_parallel": True,  # FM нь p1/p2 биш, дан дээж
    },
    "SOLID": {
        "audit_columns": [
            {"key": "A", "label": "A", "decimals": 4},
            {"key": "B", "label": "B", "decimals": 4},
            {"key": "C", "label": "C", "decimals": 4},
        ],
        "audit_result_columns": [
            {"key": "solid_pct", "label": "Solid%", "decimals": 2},
        ],
        "audit_no_parallel": True,  # SOLID нь p1/p2 биш, дан дээж
    },
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
        },
        "audit_columns": deepcopy(DEFAULT_AUDIT_COLUMNS),
        "audit_extra_columns": [],  # Нэмэлт тогтмол утгууд (CV-д E, q1, q2, S гэх мэт)
        "audit_result_columns": [],  # Тооцоолсон үр дүн баганууд (FM-д Wet%, Dry%)
        "audit_no_parallel": False,  # CSN, FM гэх мэт p1/p2 биш шинжилгээнүүд
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

    # Audit columns
    if base.get("audit_columns"):
        merged["audit_columns"] = deepcopy(base["audit_columns"])

    # Audit extra columns (constants like E, q1, q2 for CV)
    if base.get("audit_extra_columns"):
        merged["audit_extra_columns"] = deepcopy(base["audit_extra_columns"])

    # Audit result columns (FM-д Wet%, Dry% гэх мэт тооцоолсон үр дүн)
    if base.get("audit_result_columns"):
        merged["audit_result_columns"] = deepcopy(base["audit_result_columns"])

    # Audit no parallel flag (CSN, FM гэх мэт)
    if base.get("audit_no_parallel"):
        merged["audit_no_parallel"] = True

    return merged
