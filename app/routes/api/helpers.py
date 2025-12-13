# app/routes/api/helpers.py
# -*- coding: utf-8 -*-
"""
API модульуудын хамтын хэрэгсэл, дүрэм, шалгалтууд.
"""

from flask import jsonify
from flask_login import current_user
from sqlalchemy import func
from math import inf
from app.config.repeatability import LIMIT_RULES

from app.models import Sample
from app.utils.codes import norm_code
from app.utils.converters import to_float


# =============================================================================
# СТАНДАРТ API RESPONSE FORMAT
# =============================================================================

def api_success(data=None, message=None):
    """
    Амжилттай API хариу буцаах

    Args:
        data: Буцаах өгөгдөл
        message: Нэмэлт мессеж

    Returns:
        Flask Response (JSON)

    Example:
        return api_success({"sample_id": 123}, "Дээж үүсгэгдлээ")
    """
    response = {"success": True}
    if data is not None:
        response["data"] = data
    if message:
        response["message"] = message
    return jsonify(response)


def api_error(message, code=None, status_code=400, details=None):
    """
    Алдааны API хариу буцаах

    Args:
        message: Алдааны мессеж
        code: Алдааны код (optional, e.g., "VALIDATION_ERROR")
        status_code: HTTP status code (default: 400)
        details: Нэмэлт дэлгэрэнгүй мэдээлэл

    Returns:
        Flask Response (JSON) with status code

    Example:
        return api_error("Буруу утга", "INVALID_VALUE", 400)
    """
    response = {
        "success": False,
        "error": message
    }
    if code:
        response["code"] = code
    if details:
        response["details"] = details
    return jsonify(response), status_code


# =============================================================================
# ХУУЧИН API ХАРИУНЫ ФОРМАТ (ok: True/False)
# =============================================================================

def api_ok(message=None, **kwargs):
    """
    Legacy амжилттай API хариу (ok формат)

    Args:
        message: Мессеж
        **kwargs: Нэмэлт утгууд (sample_id, count, гэх мэт)

    Returns:
        Flask Response (JSON)

    Example:
        return api_ok("Амжилттай", sample_id=123)
    """
    response = {"ok": True}
    if message:
        response["message"] = message
    response.update(kwargs)
    return jsonify(response)


def api_fail(message, status_code=400, **kwargs):
    """
    Legacy алдааны API хариу (ok формат)

    Args:
        message: Алдааны мессеж
        status_code: HTTP status code (default: 400)
        **kwargs: Нэмэлт утгууд

    Returns:
        Flask Response (JSON) with status code

    Example:
        return api_fail("Олдсонгүй", 404)
    """
    response = {"ok": False, "message": message}
    response.update(kwargs)
    return jsonify(response), status_code


# Түгээмэл алдааны кодууд
class ApiErrorCodes:
    """API алдааны кодууд"""
    VALIDATION_ERROR = "VALIDATION_ERROR"
    NOT_FOUND = "NOT_FOUND"
    UNAUTHORIZED = "UNAUTHORIZED"
    FORBIDDEN = "FORBIDDEN"
    DUPLICATE = "DUPLICATE"
    DATABASE_ERROR = "DATABASE_ERROR"
    INTERNAL_ERROR = "INTERNAL_ERROR"


# -----------------------------
# 🧬 Mass gate хэрэгтэй эсэх (XY/CRI/CSR-д ХЭРЭГГҮЙ)
# -----------------------------
def _requires_mass_gate(code: str) -> bool:
    base = norm_code(code or "")
    return base not in {"X", "Y", "CRI", "CSR"}


def _has_m_task_sql():
    """analyses_to_perform JSON string дотор "m" байгаа эсэхийг case-insensitive шалгана."""
    return func.lower(Sample.analyses_to_perform).like('%"m"%')


def _can_delete_sample() -> bool:
    """Админ эсвэл ахлах л бүрэн устгах эрхтэй."""
    return getattr(current_user, "role", "") in {"admin", "senior"}


# -----------------------------
# 🧬 Дээжийн нэгтгэсэн ТӨЛӨВ
# -----------------------------
def _aggregate_sample_status(sample_status: str, result_statuses: set[str] | None) -> str:
    """
    - Хэрэв дээж archived бол үр дүнгээс үл хамааран 'archived'
    - Өөргүй бол шинжилгээний статусуудаас:
        pending_review > rejected > approved
    - Хэрэв шинжилгээ байхгүй бол sample_status-г буцаана.
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
# REVIEW/ДҮРЭМ – (өгөгдсөн)
# =========================
EPS = 1e-6
DEFAULT_LIMIT_RULE = {"single": {"limit": 0.30, "mode": "abs"}}


def _coalesce_diff(raw_norm: dict) -> float | None:
    """raw_data-гаас тохирцын зөрүүг (diff) олж буцаана."""
    raw = raw_norm or {}
    t_val = to_float(raw.get("t"))
    if t_val is not None:
        return abs(t_val)
    diff = to_float(raw.get("diff"))
    if diff is not None:
        return abs(diff)
    p1 = raw.get("p1") or {}
    p2 = raw.get("p2") or {}
    r1 = to_float(p1.get("result"))
    r2 = to_float(p2.get("result"))
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
                    band_label = f"{lower:.2f}–{upper:.2f}"
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
        limit = to_float(raw_norm.get("limit_used"))
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

    avg = to_float((raw_norm or {}).get("avg"))
    diff = _coalesce_diff(raw_norm)
    if diff is None:
        return True

    limit, mode, _band = _effective_limit(analysis_code, avg)
    effective_limit = (avg * limit) if (mode == "percent" and avg is not None) else limit
    return (abs(diff) - (effective_limit or 0)) > EPS  # EPS = 1e-6
