# app/utils/server_calculations/physical.py
# -*- coding: utf-8 -*-
"""
Physical property calculations: CSN, Gray-King (Gi), Free Moisture (FM), Solid, TRD.
"""

from typing import Optional, Dict
from math import isfinite, floor

from ._helpers import _safe_float, _get_from_dict


def calc_csn(raw_data: Dict) -> Optional[float]:
    """
    Бөсөх зэрэг (CSN / Crucible Swelling Number) тооцоолол

    5 давталтын утгуудаас (v1–v5) доод тал нь 2 зөв утга байвал
    дунджийг тооцоолж 0.5 алхамаар бөөрөнхийлнө.

    Args:
        raw_data: {"v1": ..., "v2": ..., "v3": ..., "v4": ..., "v5": ..., ...}

    Returns:
        CSN index (0.5 step rounded) or None
    """
    values = []
    for key in ("v1", "v2", "v3", "v4", "v5"):
        v = _safe_float(raw_data.get(key))
        if v is not None and 0 <= v <= 9:
            # 0.5 алхамтай утга мөн эсэхийг шалгана
            if abs(v * 2 - round(v * 2)) < 1e-9:
                values.append(v)

    if len(values) < 2:
        return None

    avg_raw = sum(values) / len(values)
    # 0.5 алхамаар бөөрөнхийлөх
    return round(avg_raw * 2) / 2


def calc_gray_king_gi(raw_data: Dict) -> Optional[float]:
    """
    Gray-King Index (Gi) тооцоолол

    Formula (two modes):
    - 5:1 mode (default): Gi = 10 + (30*m2 + 70*m3) / m1
    - 3:3 mode (retest):  Gi = (30*m2 + 70*m3) / (5*m1)

    Args:
        raw_data: {
            "p1": {"m1": ..., "m2": ..., "m3": ..., "mode": "3:3" or "5:1"},
            "p2": {...}
        }

    Returns:
        Average Gi (rounded to integer) or None
    """
    def calc_single_gi(m1, m2, m3, mode) -> Optional[float]:
        """Calculate Gi for single parallel."""
        if not all(x is not None and isfinite(x) and x > 0 for x in [m1, m2, m3]):
            return None

        numerator = 30 * m2 + 70 * m3

        # Check mode
        is_33_mode = mode and ("3:3" in str(mode) or "3_3" in str(mode) or "retest" in str(mode).lower())

        if is_33_mode:
            # 3:3 mode (retest)
            gi = numerator / (5 * m1)
        else:
            # 5:1 mode (default)
            gi = 10 + (numerator / m1)

        return gi if isfinite(gi) else None

    # Top-level mode (frontend sends retest_mode at raw_data level)
    top_mode = raw_data.get("retest_mode") or raw_data.get("mode")

    # Parallel 1
    p1 = raw_data.get("p1") or {}
    m1_p1 = _safe_float(p1.get("m1"))
    m2_p1 = _safe_float(p1.get("m2"))
    m3_p1 = _safe_float(p1.get("m3"))
    mode_p1 = p1.get("mode") or p1.get("retest_mode") or top_mode

    # Parallel 2
    p2 = raw_data.get("p2") or {}
    m1_p2 = _safe_float(p2.get("m1"))
    m2_p2 = _safe_float(p2.get("m2"))
    m3_p2 = _safe_float(p2.get("m3"))
    mode_p2 = p2.get("mode") or p2.get("retest_mode") or top_mode

    results = []

    # Calculate p1
    r1 = calc_single_gi(m1_p1, m2_p1, m3_p1, mode_p1)
    if r1 is not None:
        results.append(r1)

    # Calculate p2
    r2 = calc_single_gi(m1_p2, m2_p2, m3_p2, mode_p2)
    if r2 is not None:
        results.append(r2)

    if not results:
        return None

    # ASTM: дундажилсаны ДАРАА round хийх
    # floor(x + 0.5) = half-up rounding (JS Math.round-тай ижил)
    # Python round() banker's rounding: round(18.5)=18, but JS Math.round(18.5)=19
    avg = sum(results) / len(results)
    return int(floor(avg + 0.5))


def calc_free_moisture_fm(raw_data: Dict) -> Optional[float]:
    """
    Чөлөөт чийг (FM) тооцоолол

    Formula: FM% = ((Wb - Wa) / (Wa - Wt)) * 100

    Args:
        raw_data: {
            "tray_g": ..., "before_g": ..., "after_g": ...,
            "fm_wet_pct": ... (шууд тооцсон утга)
        }

    Returns:
        FM% or None
    """
    # Top-level талбаруудаас авах (aggrid template илгээдэг формат)
    wt = _safe_float(raw_data.get("tray_g") or raw_data.get("tray"))
    wb = _safe_float(raw_data.get("before_g") or raw_data.get("before"))
    wa = _safe_float(raw_data.get("after_g") or raw_data.get("after"))

    if all(x is not None and isfinite(x) for x in [wt, wb, wa]):
        denominator = wa - wt
        if abs(denominator) < 1e-10:
            return None
        fm = ((wb - wa) / denominator) * 100
        if isfinite(fm) and fm >= 0:
            return fm

    return None


def calc_solid(raw_data: Dict) -> Optional[float]:
    """
    Хатуу бодис (Solid) тооцоолол

    Formula: Solid% = C * 100 / (A - B)

    Args:
        raw_data: {"A": ..., "B": ..., "C": ...}

    Returns:
        Solid% or None
    """
    a = _safe_float(raw_data.get("A") or raw_data.get("a"))
    b = _safe_float(raw_data.get("B") or raw_data.get("b"))
    c = _safe_float(raw_data.get("C") or raw_data.get("c"))

    if not all(x is not None and isfinite(x) for x in [a, b, c]):
        return None

    denominator = a - b
    if abs(denominator) < 1e-10:
        return None

    solid = (c * 100) / denominator
    return solid if isfinite(solid) and solid >= 0 else None


def calc_trd(raw_data: Dict) -> Optional[float]:
    """
    Үнэн харьцангуй нягт (TRD) тооцоолол

    Formula (coal):
    1. md = m * (100 - mad) / 100  (dry mass)
    2. TRD = (md / (md + m2 - m1)) * kt

    Formula (MG — no mad/kt correction):
    TRD = m / (m2 + m - m1)

    Args:
        raw_data: {
            "p1": {"m": ..., "m1": ..., "m2": ..., "temp": ..., "mad": ...},
            "p2": {...},
            "mad": ... (global moisture value if not in p1/p2)
        }

    Returns:
        Average TRD or None
    """
    from .mg_calcs import calc_mg_trd

    # MG format detection: no mad_used or temp_c at top level
    # Coal TRD always has mad_used + temp_c, MG TRD has neither
    if 'mad_used' not in raw_data and 'temp_c' not in raw_data:
        return calc_mg_trd(raw_data)

    # Temperature coefficient table (6-35°C)
    # SOP LAB.07.12 / MNS GB/T 217:2015 — Kt = ρ(t)/ρ(20°C)
    KT_TABLE = {
        6: 1.00174, 7: 1.00170, 8: 1.00165, 9: 1.00158, 10: 1.00150,
        11: 1.00140, 12: 1.00129, 13: 1.00117, 14: 1.00100, 15: 1.00090,
        16: 1.00074, 17: 1.00057, 18: 1.00039, 19: 1.00020, 20: 1.00000,
        21: 0.99979, 22: 0.99956, 23: 0.99953, 24: 0.99909, 25: 0.99883,
        26: 0.99857, 27: 0.99831, 28: 0.99803, 29: 0.99773, 30: 0.99743,
        31: 0.99713, 32: 0.99682, 33: 0.99649, 34: 0.99616, 35: 0.99582
    }

    def get_kt(temp: Optional[float]) -> Optional[float]:
        """Get kt coefficient from temperature (linear interpolation)."""
        if temp is None or not isfinite(temp):
            return None

        # Check bounds
        if temp < 6.0 or temp > 35.0:
            return None

        # Linear interpolation between table values
        t_low = int(temp)
        t_high = t_low + 1

        if t_low == temp or t_high > 35:
            return KT_TABLE.get(t_low)

        kt_low = KT_TABLE.get(t_low)
        kt_high = KT_TABLE.get(t_high)
        if kt_low is None or kt_high is None:
            return None

        frac = temp - t_low
        return kt_low + (kt_high - kt_low) * frac

    def calc_single_trd(m, m1, m2, temp, mad) -> Optional[float]:
        """Calculate TRD for single parallel."""
        if not all(x is not None and isfinite(x) for x in [m, m1, m2]):
            return None

        # Get mad
        if mad is None or not isfinite(mad) or mad < 0:
            return None

        # Get kt from temperature
        kt = get_kt(temp)
        if kt is None:
            return None

        # Step 1: Calculate dry mass
        md = m * (100 - mad) / 100

        if md <= 0:
            return None

        # Step 2: Calculate TRD
        denominator = md + m2 - m1

        if abs(denominator) < 1e-10:
            return None

        trd = (md / denominator) * kt

        return trd if isfinite(trd) and trd > 0 else None

    # Global mad (if provided)
    global_mad = _safe_float(raw_data.get("mad"))

    # Parallel 1
    p1 = raw_data.get("p1") or {}
    m_p1 = _safe_float(p1.get("m"))
    m1_p1 = _safe_float(p1.get("m1"))
    m2_p1 = _safe_float(p1.get("m2"))
    temp_p1 = _safe_float(p1.get("temp") or p1.get("temperature"))
    mad_p1 = _safe_float(p1.get("mad")) or global_mad

    # Parallel 2
    p2 = raw_data.get("p2") or {}
    m_p2 = _safe_float(p2.get("m"))
    m1_p2 = _safe_float(p2.get("m1"))
    m2_p2 = _safe_float(p2.get("m2"))
    temp_p2 = _safe_float(p2.get("temp") or p2.get("temperature"))
    mad_p2 = _safe_float(p2.get("mad")) or global_mad

    results = []

    # Calculate p1
    r1 = calc_single_trd(m_p1, m1_p1, m2_p1, temp_p1, mad_p1)
    if r1 is not None:
        results.append(r1)

    # Calculate p2
    r2 = calc_single_trd(m_p2, m1_p2, m2_p2, temp_p2, mad_p2)
    if r2 is not None:
        results.append(r2)

    if not results:
        return None

    return sum(results) / len(results)
