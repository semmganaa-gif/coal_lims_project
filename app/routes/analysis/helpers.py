# app/routes/analysis/helpers.py
# -*- coding: utf-8 -*-
"""
Analysis модулиудын хамтын хэрэгсэл, тогтмол, декоратор.
"""

from flask import request, redirect, url_for, abort
from flask_login import current_user
from functools import wraps
from datetime import datetime
import re

from app.models import AnalysisResult, Sample

# =====================================================================
# QC DASHBOARD – тогтмолууд
# =====================================================================

# QC дээр харуулах үндсэн параметрүүд
QC_PARAM_CODES = ["Mad", "Aad", "Vdaf", "Qnet,ar", "CSN", "Gi"]

# Composite vs Hourly Avg-ийн хооронд зөвшөөрөгдөх зөрүү
QC_TOLERANCE = {
    "Mad": 0.30,
    "Aad": 0.50,
    "Vdaf": 0.50,
    "Qnet,ar": 150.0,
    "CSN": 0.30,
    "Gi": 3.0,
}

# Name/Class QC – default specification (fallback)
QC_SPEC_DEFAULT = {
    "Vdaf": (20.0, 30.0),
    "Aad": (8.0, 12.0),
    "CSN": (7.0, None),
    "Gi": (80.0, None),
}

# =====================================================================
# COMPOSITE QC тохиргоо
# =====================================================================
COMPOSITE_QC_CODES = ["Mt,ar", "Mad", "Aad", "Vad", "Vdaf", "Qgr,ar", "Qnet,ar", "CSN", "Gi", "TRD,ad"]

COMPOSITE_QC_LIMITS = {
    "Mt,ar": {"mode": "abs", "warn": 0.3, "fail": 0.6},
    "Mad": {"mode": "abs", "warn": 0.3, "fail": 0.5},
    "Aad": {"mode": "abs", "warn": 0.5, "fail": 1.0},
    "Vad": {"mode": "rel", "warn": 2.5, "fail": 5.0},
    "Vdaf": {"mode": "rel", "warn": 2.0, "fail": 4.0},
    "Qgr,ar": {"mode": "abs", "warn": 100, "fail": 200},
    "Qnet,ar": {"mode": "abs", "warn": 100, "fail": 200},
    "TRD,ad": {"mode": "rel", "warn": 1.0, "fail": 2.0},
    "CSN": {"mode": "abs", "warn": 0.5, "fail": 1.0},
    "Gi": {"mode": "rel", "warn": 5.0, "fail": 10.0},
}

_STREAM_SUFFIX_RE = re.compile(r"^([ND])(\d{1,2})$", re.IGNORECASE)

# =====================================================================
# TIMER PRESETS
# =====================================================================
TIMER_PRESETS = {
    "Aad": {"layout": "right", "digit_size": "xl", "editable": True, "timers": [{"label": "Зуух #1", "seconds": 3600, "note": "815°C · 60′"}, {"label": "Зуух #2", "seconds": 3600, "note": "815°C · 60′"}, {"label": "Зуух #3", "seconds": 3600, "note": "815°C · 60′"}, {"label": "Десикатор", "seconds": 900, "note": "15′"}]},
    "Vad": {"layout": "right", "digit_size": "xl", "editable": True, "timers": [{"label": "Зуух", "seconds": 25200, "note": "7:00:00"}, {"label": "Десикатор", "seconds": 900, "note": "00:15:00"}]},
    "Mad": {"layout": "right", "digit_size": "lg", "editable": True, "timers": [{"label": "Шат", "seconds": 3600, "note": "60′"}, {"label": "Десикатор", "seconds": 900, "note": "15′"}]},
    "MT": {"layout": "right", "digit_size": "lg", "editable": True, "timers": [{"label": "Шат", "seconds": 3600, "note": "60′"}, {"label": "Десикатор", "seconds": 900, "note": "15′"}]},
    "Gi": {"layout": "right", "digit_size": "xl", "editable": True, "timers": [{"label": "Шат 1", "seconds": 54000, "note": "15:00:00"}, {"label": "Шат 2", "seconds": 1800, "note": "00:30:00"}]},
    "TRD": {"layout": "right", "digit_size": "lg", "editable": True, "timers": [{"label": "Шат", "seconds": 3600, "note": "60′"}, {"label": "Десикатор", "seconds": 900, "note": "15′"}]},
    "P": {"layout": "right", "digit_size": "lg", "editable": False, "timers": []},
    "F": {"layout": "right", "digit_size": "lg", "editable": False, "timers": []},
    "Cl": {"layout": "right", "digit_size": "lg", "editable": False, "timers": []},
    "CSN": {"layout": "right", "digit_size": "lg", "editable": False, "timers": []},
    "FM": {"layout": "right", "digit_size": "lg", "editable": False, "timers": []},
    "SOLID": {"layout": "right", "digit_size": "lg", "editable": False, "timers": []},
}


# =====================================================================
# QC HELPER FUNCTIONS
# =====================================================================

def _qc_to_date(dt):
    if not dt:
        return None
    if isinstance(dt, datetime):
        return dt.date()
    return dt


def _qc_split_family(sample_code: str):
    if not sample_code:
        return sample_code, None
    m = re.search(r"(.*_[ND])(\d+|com)$", sample_code)
    if m:
        return m.group(1), m.group(2)
    return sample_code, None


def _qc_is_composite(sample, slot: str | None):
    st = (sample.sample_type or "").lower()
    if st in ("com", "composite"):
        return True
    if slot and "com" in slot.lower():
        return True
    return False


def _qc_check_spec(value, spec_tuple):
    if value is None or spec_tuple is None:
        return False
    min_v, max_v = spec_tuple
    try:
        v = float(value)
    except (TypeError, ValueError):
        return False
    if min_v is not None and v < min_v:
        return True
    if max_v is not None and v > max_v:
        return True
    return False


def _parse_numeric(val):
    if val is None:
        return None
    try:
        return float(str(val).replace(",", "").strip())
    except (TypeError, ValueError):
        return None


def _eval_qc_status(param_code, diff, diff_pct):
    rule = COMPOSITE_QC_LIMITS.get(param_code)
    if rule is None:
        if diff_pct is None:
            return "ok"
        ap = abs(diff_pct)
        if ap > 5:
            return "fail"
        elif ap > 2:
            return "warn"
        return "ok"

    mode = rule.get("mode", "rel")
    warn = rule.get("warn")
    fail = rule.get("fail")

    if mode == "abs":
        if diff is None:
            return "ok"
        ad = abs(diff)
        if fail is not None and ad > fail:
            return "fail"
        if warn is not None and ad > warn:
            return "warn"
        return "ok"

    if diff_pct is None:
        return "ok"
    ap = abs(diff_pct)
    if fail is not None and ap > fail:
        return "fail"
    if warn is not None and ap > warn:
        return "warn"
    return "ok"


def _split_stream_key(sample: Sample):
    raw_name = sample.sample_code or sample.name or sample.sample_name or f"ID {sample.id}"
    tokens = str(raw_name).strip().split()
    if not tokens:
        return raw_name, "unknown", None
    suffix = tokens[-1]
    prefix = " ".join(tokens[:-1]) or raw_name
    suf_lower = suffix.lower()
    m = _STREAM_SUFFIX_RE.match(suffix)
    if m:
        idx = int(m.group(2))
        return prefix, "two_hour", idx
    if suf_lower in {"ncom", "ncomp", "ncomp.", "comp", "comp.", "ncom.", "com"}:
        return prefix, "composite", None
    return raw_name, "unknown", None


# =====================================================================
# ROLE DECORATOR
# =====================================================================

def analysis_role_required(allowed_roles=None):
    """Шинжилгээний модульд хандах эрх шалгах декоратор"""
    if allowed_roles is None:
        allowed_roles = ["himich", "ahlah", "admin", "beltgegch"]

    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                return redirect(url_for("main.login", next=request.url))
            if current_user.role not in allowed_roles:
                abort(403)
            return f(*args, **kwargs)
        return decorated_function
    return decorator


# =====================================================================
# SULFUR MAP (CV тооцоололд)
# =====================================================================

def _sulfur_map_for(sample_ids):
    """S утгыг sample_id-гаар map үүсгэнэ (CV тооцоололд)"""
    if not sample_ids:
        return {}
    rows = (
        AnalysisResult.query.filter(
            AnalysisResult.sample_id.in_(sample_ids),
            AnalysisResult.analysis_code.in_(["TS", "St,ad"]),
            AnalysisResult.status.in_(["approved", "pending_review"]),
        )
        .order_by(AnalysisResult.sample_id.asc(), AnalysisResult.id.desc())
        .all()
    )
    out = {}
    for r in rows:
        if r.final_result is None:
            continue
        if r.sample_id not in out:
            try:
                out[r.sample_id] = float(r.final_result)
            except Exception:
                pass
    return out
