# app/utils/qc.py
# -*- coding: utf-8 -*-
"""
QC (Quality Control) утилити функцүүд

QC dashboard болон composite QC шалгалтанд хэрэглэгдэх
бүх утилити функцүүдыг агуулна.
"""

from datetime import datetime
import re

from app.constants import AnalysisResultStatus
from app.models import AnalysisResult, Sample
from app.config.qc_config import COMPOSITE_QC_LIMITS, STREAM_SUFFIX_RE


def qc_to_date(dt):
    """
    Datetime объектыг date болгох.

    Args:
        dt: datetime объект эсвэл date объект

    Returns:
        date объект эсвэл None
    """
    if not dt:
        return None
    if isinstance(dt, datetime):
        return dt.date()
    return dt


def qc_split_family(sample_code: str):
    """
    Дээжийн кодыг family болон slot-д хуваах.

    Args:
        sample_code: Дээжийн код (жишээ: "TT_D1" эсвэл "TT_Dcom")

    Returns:
        tuple: (family, slot) - жишээ: ("TT_D", "1") эсвэл ("TT_D", "com")

    Examples:
        >>> qc_split_family("TT_D1")
        ("TT_D", "1")
        >>> qc_split_family("TT_Dcom")
        ("TT_D", "com")
    """
    if not sample_code:
        return sample_code, None
    m = re.search(r"(.*_[ND])(\d+|com)$", sample_code)
    if m:
        return m.group(1), m.group(2)
    return sample_code, None


def qc_is_composite(sample, slot: str | None):
    """
    Дээж composite эсэхийг шалгах.

    Args:
        sample: Sample объект
        slot: Slot утга (жишээ: "com", "1", "2")

    Returns:
        bool: Composite бол True
    """
    st = (sample.sample_type or "").lower()
    if st in ("com", "composite"):
        return True
    if slot and "com" in slot.lower():
        return True
    return False


def qc_check_spec(value, spec_tuple):
    """
    Утга specification-ий хязгаараас хэтэрсэн эсэхийг шалгах.

    Args:
        value: Шалгах утга
        spec_tuple: (min_value, max_value) tuple. None байж болно.

    Returns:
        bool: Specification хэтэрсэн бол True

    Examples:
        >>> qc_check_spec(10.0, (8.0, 12.0))
        False
        >>> qc_check_spec(15.0, (8.0, 12.0))
        True
    """
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


def parse_numeric(val):
    """
    String утгыг float болгох (таслал арилгах).

    Args:
        val: Хөрвүүлэх утга

    Returns:
        float эсвэл None

    Examples:
        >>> parse_numeric("1,234.56")
        1234.56
        >>> parse_numeric("abc")
        None
    """
    if val is None:
        return None
    try:
        return float(str(val).replace(",", "").strip())
    except (TypeError, ValueError):
        return None


def eval_qc_status(param_code, diff, diff_pct):
    """
    QC статусыг үнэлэх (ok/warn/fail).

    Composite QC limit-ийг ашиглаж зөрүүг шалгана.

    Args:
        param_code: Параметрийн код (жишээ: "Mad", "Aad")
        diff: Абсолют зөрүү
        diff_pct: Хувийн зөрүү

    Returns:
        str: "ok", "warn", эсвэл "fail"
    """
    rule = COMPOSITE_QC_LIMITS.get(param_code)
    if rule is None:
        # Default rule: хувь ашиглах
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
        # Абсолют зөрүү
        if diff is None:
            return "ok"
        ad = abs(diff)
        if fail is not None and ad > fail:
            return "fail"
        if warn is not None and ad > warn:
            return "warn"
        return "ok"

    # Харьцангуй зөрүү (хувь)
    if diff_pct is None:
        return "ok"
    ap = abs(diff_pct)
    if fail is not None and ap > fail:
        return "fail"
    if warn is not None and ap > warn:
        return "warn"
    return "ok"


def split_stream_key(sample: Sample):
    """
    Stream task-уудад зориулж sample-ийг задлах.

    Sample code-оос prefix, stream type болон index-ийг задлана.

    Args:
        sample: Sample объект

    Returns:
        tuple: (prefix, stream_type, index)
            - stream_type: "two_hour", "composite", эсвэл "unknown"
            - index: 2-цагийн дээжийн дугаар (1-12), composite бол None

    Examples:
        >>> split_stream_key(sample_with_code("TT D1"))
        ("TT", "two_hour", 1)
        >>> split_stream_key(sample_with_code("TT Ncom"))
        ("TT", "composite", None)
    """
    raw_name = sample.sample_code or sample.name or sample.sample_name or f"ID {sample.id}"
    tokens = str(raw_name).strip().split()
    if not tokens:
        return raw_name, "unknown", None

    suffix = tokens[-1]
    prefix = " ".join(tokens[:-1]) or raw_name
    suf_lower = suffix.lower()

    # Check if it's a 2-hour sample (D1, D2, ..., N1, N2, ...)
    m = STREAM_SUFFIX_RE.match(suffix)
    if m:
        idx = int(m.group(2))
        return prefix, "two_hour", idx

    # Check if it's a composite
    if suf_lower in {"ncom", "ncomp", "ncomp.", "comp", "comp.", "ncom.", "com"}:
        return prefix, "composite", None

    return raw_name, "unknown", None


def sulfur_map_for(sample_ids):
    """
    S утгыг sample_id-гаар map үүсгэнэ (CV тооцоололд).

    Args:
        sample_ids: Sample ID-уудын жагсаалт

    Returns:
        dict: {sample_id: sulfur_value}

    Examples:
        >>> sulfur_map_for([1, 2, 3])
        {1: 0.45, 2: 0.52, 3: 0.48}
    """
    if not sample_ids:
        return {}

    from app import db
    from sqlalchemy import select
    rows = db.session.execute(
        select(AnalysisResult).filter(
            AnalysisResult.sample_id.in_(sample_ids),
            AnalysisResult.analysis_code.in_(["TS", "St,ad"]),
            AnalysisResult.status.in_([AnalysisResultStatus.APPROVED.value, AnalysisResultStatus.PENDING_REVIEW.value]),
        ).order_by(AnalysisResult.sample_id.asc(), AnalysisResult.id.desc())
    ).scalars().all()

    out = {}
    for r in rows:
        if r.final_result is None:
            continue
        if r.sample_id not in out:
            try:
                out[r.sample_id] = float(r.final_result)
            except (ValueError, TypeError):
                pass
    return out
