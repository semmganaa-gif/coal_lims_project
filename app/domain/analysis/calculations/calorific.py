# app/utils/server_calculations/calorific.py
# -*- coding: utf-8 -*-
"""
Calorific value (CV) calculation — Bomb Calorimeter Method.
"""

from typing import Optional, Dict
from math import isfinite

from ._helpers import _safe_float, cv_cal_to_mj, J_PER_CAL


def calc_calorific_value_cv(raw_data: Dict, unit: str = "cal/g") -> Optional[float]:
    """
    Илчлэг (CV) тооцоолол - Bomb Calorimeter Method

    Formula (multi-step):
    1. Qb_Jg = ((E * dT) - q1 - q2) / m
    2. alpha = temperature dependent coefficient (0.0010, 0.0012, or 0.0016)
    3. acid_corr = alpha * Qb_Jg
    4. S_corr = 94.1 * S (sulfur correction)
    5. Qgr_ad_Jg = Qb_Jg - (S_corr + acid_corr)
    6. Qgr_cal_g = Qgr_ad_Jg / 4.1868 (J to cal conversion)

    Args:
        raw_data: {
            "p1": {"m": ..., "delta_t": ..., "s": ...},
            "p2": {"m": ..., "delta_t": ..., "s": ...},
            "batch": {"E": ..., "q1": ..., "q2": ...},
            "s_used": ... (sulfur value)
        }
        unit: Output unit - "cal/g" (default, = kcal/kg), "MJ/kg", or "J/g"

    Returns:
        Average CV in specified unit or None
    """
    # Constants
    S_CORR_FACTOR = 94.1

    def get_alpha(qb_jg: float) -> float:
        """Get alpha coefficient per MNS ISO 1928 (discrete values)."""
        qb_mjkg = qb_jg / 1000.0
        if qb_mjkg <= 16.70:
            return 0.0010
        elif qb_mjkg <= 25.10:
            return 0.0012
        else:
            return 0.0016

    def calc_single_cv(m, dt, e, q1, q2, s) -> Optional[float]:
        """Calculate CV for single parallel."""
        if m is None or dt is None or e is None or q1 is None:
            return None
        if not all(isfinite(x) for x in [m, dt, e, q1]):
            return None
        if abs(m) < 1e-10:
            return None

        s_val = s if (s is not None and isfinite(s)) else 0
        q2_val = q2 if (q2 is not None and isfinite(q2)) else 0

        # Step 1: Bomb calorific value
        qb_jg = ((e * dt) - q1 - q2_val) / m

        # Step 2-3: Acid correction
        alpha = get_alpha(qb_jg)
        acid_corr = alpha * qb_jg

        # Step 4: Sulfur correction
        s_corr = S_CORR_FACTOR * s_val

        # Step 5: Gross calorific value in J/g
        qgr_ad_jg = qb_jg - (s_corr + acid_corr)

        # Step 6: Convert to cal/g
        qgr_cal_g = qgr_ad_jg / J_PER_CAL

        return qgr_cal_g if isfinite(qgr_cal_g) else None

    # Extract batch parameters
    batch = raw_data.get("batch") or {}
    e = _safe_float(batch.get("E"))
    q1 = _safe_float(batch.get("q1"))
    q2 = _safe_float(batch.get("q2"))
    s_used = _safe_float(raw_data.get("s_used")) or 0

    # Parallel 1
    p1 = raw_data.get("p1") or {}
    m1 = _safe_float(p1.get("m") or p1.get("m1"))
    dt1 = _safe_float(p1.get("delta_t") or p1.get("dT") or p1.get("temp"))
    s1 = _safe_float(p1.get("s")) or s_used

    # Parallel 2
    p2 = raw_data.get("p2") or {}
    m2 = _safe_float(p2.get("m") or p2.get("m1"))
    dt2 = _safe_float(p2.get("delta_t") or p2.get("dT") or p2.get("temp"))
    s2 = _safe_float(p2.get("s")) or s_used

    results = []

    # Calculate p1
    r1 = calc_single_cv(m1, dt1, e, q1, q2, s1)
    if r1 is not None and r1 >= 0:
        results.append(r1)

    # Calculate p2
    r2 = calc_single_cv(m2, dt2, e, q1, q2, s2)
    if r2 is not None and r2 >= 0:
        results.append(r2)

    if not results:
        return None

    avg_cal_g = sum(results) / len(results)

    # Unit conversion
    if unit == "MJ/kg":
        return cv_cal_to_mj(avg_cal_g)
    elif unit == "J/g":
        return avg_cal_g * J_PER_CAL
    else:  # Default: cal/g = kcal/kg
        return avg_cal_g
