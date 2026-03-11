# app/utils/server_calculations/mg_calcs.py
# -*- coding: utf-8 -*-
"""
WTL MG (Монгол Газрын) analysis calculations: MG_MT, MG_TRD, MG_TUBE, MG_SIZE.
"""

from typing import Optional, Dict
from math import isfinite

from ._helpers import _safe_float


def calc_mg_mt(raw_data: Dict) -> Optional[float]:
    """
    МГ Чийг (MG_MT) тооцоолол

    Formula: Result% = ((m1 + m2 - m3) / m2) * 100

    Args:
        raw_data: {"m1": crucible, "m2": sample, "m3": dried, "result": ...}

    Returns:
        Result% or None
    """
    m1 = _safe_float(raw_data.get("m1"))
    m2 = _safe_float(raw_data.get("m2"))
    m3 = _safe_float(raw_data.get("m3"))

    if m1 is None or m2 is None or m3 is None or m2 <= 0:
        return None

    result = ((m1 + m2 - m3) / m2) * 100

    if not isfinite(result) or result < 0:
        return None

    return result


def calc_mg_trd(raw_data: Dict) -> Optional[float]:
    """
    МГ Нягт (MG_TRD) тооцоолол — Mad/kt correction шаардлагагүй

    Formula: TRD = m / (m2 + m - m1)

    Args:
        raw_data: {"p1": {"m": 15, "m2": 82, "m1": 94, ...}, "p2": {...}, "avg": ...}

    Returns:
        Average TRD or None
    """
    results = []

    for pkey in ("p1", "p2"):
        p = raw_data.get(pkey) or {}
        m = _safe_float(p.get("m"))
        m1 = _safe_float(p.get("m1"))
        m2 = _safe_float(p.get("m2"))

        if m is None or m1 is None or m2 is None:
            continue

        denom = m2 + m - m1
        if denom <= 0:
            continue

        trd = m / denom
        if isfinite(trd) and trd > 0:
            results.append(trd)

    if not results:
        return None

    return sum(results) / len(results)


def calc_mg_tube(raw_data: Dict) -> Optional[float]:
    """
    МГ Соронзон (MG_TUBE) тооцоолол

    Formula: MG% = 100 * (dried_weight - empty_crucible) / sample_mass

    Args:
        raw_data: {"empty_crucible": ..., "sample_mass": ..., "dried_weight": ..., ...}

    Returns:
        MG% or None
    """
    empty = _safe_float(raw_data.get("empty_crucible"))
    sample = _safe_float(raw_data.get("sample_mass"))
    dried = _safe_float(raw_data.get("dried_weight"))

    if empty is None or sample is None or dried is None or sample <= 0:
        return None

    mg_mass = dried - empty
    result = 100 * mg_mass / sample

    if not isfinite(result) or result < 0:
        return None

    return result


def calc_mg_size(raw_data: Dict) -> Optional[float]:
    """
    МГ Ширхэглэл (MG_SIZE) тооцоолол

    Returns None — fractions stored in raw_data, no single final_result
    """
    return None
