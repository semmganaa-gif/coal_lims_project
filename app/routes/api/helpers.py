# app/routes/api/helpers.py
# -*- coding: utf-8 -*-
"""
API Ð¼Ð¾Ð´ÑƒÐ»Ð¸ÑƒÐ´Ñ‹Ð½ Ñ…Ð°Ð¼Ñ‚Ñ‹Ð½ Ñ…ÑÑ€ÑÐ³ÑÑÐ», Ð´Ò¯Ñ€ÑÐ¼, ÑˆÐ°Ð»Ð³Ð°Ð»Ñ‚ÑƒÑƒÐ´.
"""

from flask_login import current_user
from sqlalchemy import func
from math import inf
from app.config.repeatability import LIMIT_RULES

from app.models import Sample
from app.utils.codes import norm_code, BASE_TO_ALIASES


# -----------------------------
# ðŸ§© Mass gate Ñ…ÑÑ€ÑÐ³Ñ‚ÑÐ¹ ÑÑÑÑ… (XY/CRI/CSR-Ð´ Ð¥Ð­Ð Ð­Ð“Ð“Ò®Ð™)
# -----------------------------
def _requires_mass_gate(code: str) -> bool:
    base = norm_code(code or "")
    return base not in {"X", "Y", "CRI", "CSR"}


def _has_m_task_sql():
    """analyses_to_perform JSON string Ð´Ð¾Ñ‚Ð¾Ñ€ "m" Ð±Ð°Ð¹Ð³Ð°Ð° ÑÑÑÑ…Ð¸Ð¹Ð³ case-insensitive ÑˆÐ°Ð»Ð³Ð°Ð½Ð°."""
    return func.lower(Sample.analyses_to_perform).like('%"m"%')


def _can_delete_sample() -> bool:
    """ÐÐ´Ð¼Ð¸Ð½ ÑÑÐ²ÑÐ» Ð°Ñ…Ð»Ð°Ñ… Ð» Ð±Ò¯Ñ€ÑÐ½ ÑƒÑÑ‚Ð³Ð°Ñ… ÑÑ€Ñ…Ñ‚ÑÐ¹."""
    return getattr(current_user, "role", "") in {"admin", "ahlah"}


# -----------------------------
# ðŸ§© Ð”ÑÑÐ¶Ð¸Ð¹Ð½ Ð½ÑÐ³Ñ‚Ð³ÑÑÑÐ½ Ð¢Ó¨Ð›Ó¨Ð’
# -----------------------------
def _aggregate_sample_status(sample_status: str, result_statuses: set[str] | None) -> str:
    """
    - Ð¥ÑÑ€ÑÐ² Ð´ÑÑÐ¶ archived Ð±Ð¾Ð» Ò¯Ñ€ Ð´Ò¯Ð½Ð³ÑÑÑ Ò¯Ð» Ñ…Ð°Ð¼Ð°Ð°Ñ€Ð°Ð½ 'archived'
    - Ò®Ð³Ò¯Ð¹ Ð±Ð¾Ð» ÑˆÐ¸Ð½Ð¶Ð¸Ð»Ð³ÑÑÐ½Ð¸Ð¹ ÑÑ‚Ð°Ñ‚ÑƒÑÑƒÑƒÐ´Ð°Ð°Ñ:
        pending_review > rejected > approved
    - Ð¥ÑÑ€ÑÐ² ÑˆÐ¸Ð½Ð¶Ð¸Ð»Ð³ÑÑ Ð±Ð°Ð¹Ñ…Ð³Ò¯Ð¹ Ð±Ð¾Ð» sample_status-Ð³ Ð±ÑƒÑ†Ð°Ð°Ð½Ð°.
    """
    if sample_status == "archived":
        return "archived"

    sts = result_statuses or set()

    if "pending_review" in sts:
        return "pending_review"
    if "rejected" in sts:
        return "rejected"
    if "approved" in sts:
        return "approved"

    return sample_status or ""


# =========================
# REVIEW/Ð”Ò®Ð Ð­Ðœ â€“ (Ó©Ð³Ó©Ð³Ð´ÑÓ©Ð½)
# =========================
EPS = 1e-6
DEFAULT_LIMIT_RULE = {"single": {"limit": 0.30, "mode": "abs"}}


def _to_float_or_none(x):
    try:
        if x is None:
            return None
        return float(x)
    except Exception:
        return None


def _coalesce_diff(raw_norm: dict) -> float | None:
    """raw_data-Ð°Ð°Ñ Ñ‚Ð¾Ñ…Ð¸Ñ€Ñ†Ñ‹Ð½ Ð·Ó©Ñ€Ò¯Ò¯Ð³ (diff) Ð¾Ð»Ð¶ Ð±ÑƒÑ†Ð°Ð°Ð½Ð°."""
    raw = raw_norm or {}
    t_val = _to_float_or_none(raw.get("t"))
    if t_val is not None:
        return abs(t_val)
    diff = _to_float_or_none(raw.get("diff"))
    if diff is not None:
        return abs(diff)
    p1 = raw.get("p1") or {}
    p2 = raw.get("p2") or {}
    r1 = _to_float_or_none(p1.get("result"))
    r2 = _to_float_or_none(p2.get("result"))
    if r1 is not None and r2 is not None:
        return abs(r1 - r2)
    return None


def _pick_rule(analysis_code: str):
    base = norm_code(analysis_code)
    return LIMIT_RULES.get(base, {})


def _effective_limit(analysis_code: str, avg: float | None):
    """returns: (limit_value, mode, band_label)"""
    analysis_code = norm_code(analysis_code)
    rule = _pick_rule(analysis_code)
    band_label = None

    single = rule.get("single")
    if single:
        return single["limit"], single["mode"], band_label

    bands = rule.get("bands_detailed") or rule.get("bands")
    if bands and avg is not None:
        lower = None
        for b in bands:
            upper = b["upper"]
            if avg <= upper:
                if lower is None:
                    band_label = f"<{upper:g}"
                elif upper == inf:
                    band_label = f">{lower:g}"
                else:
                    band_label = f"{lower:.2f}â€“{upper:.2f}"
                return b["limit"], b["mode"], band_label
            lower = upper

    fallback = DEFAULT_LIMIT_RULE.get("single", {"limit": 0.30, "mode": "abs"})
    return fallback["limit"], fallback["mode"], band_label


def should_require_review(analysis_code: str, raw_norm: dict) -> bool:
    analysis_code = norm_code(analysis_code)

    # Gi: 5:1 туршилтаар 18-аас доош гарвал 3:3 давтан хийлгэнэ; 3:3 дээр diff лимит давсан тохиолдолд л review.
    if analysis_code == "Gi":
        is_low = (raw_norm or {}).get("is_low_avg", False)
        retest = (raw_norm or {}).get("retest_mode")
        if is_low and retest != "3_3":
            return True

    # TRD, CV, CSN, Gi: front-end тооцоолсон limit_used/diff-ийг шууд шалгана.
    if analysis_code in ["CSN", "Gi", "CV", "TRD"] and "limit_used" in (raw_norm or {}):
        limit = _to_float_or_none(raw_norm.get("limit_used"))
        diff = _coalesce_diff(raw_norm)
        if analysis_code == "CSN":
            diff = diff if diff is not None else 0.0
            limit = limit if limit is not None else 0.0
        if diff is None or limit is None:
            return True
        return (abs(diff) - (limit or 0)) > EPS

    # CSN/Gi: fallback flag
    if analysis_code in ["CSN", "Gi"] and "t_exceeded" in (raw_norm or {}):
        return bool((raw_norm or {}).get("t_exceeded", True))

    avg = _to_float_or_none((raw_norm or {}).get("avg"))
    diff = _coalesce_diff(raw_norm)
    if diff is None:
        return True

    limit, mode, _band = _effective_limit(analysis_code, avg)
    effective_limit = (avg * limit) if (mode == "percent" and avg is not None) else limit
    return (abs(diff) - (effective_limit or 0)) > 1e-9
