# app/utils/server_calculations.py
# -*- coding: utf-8 -*-
"""
Server-Side Calculation & Verification Module

🔒 SECURITY: Клиентээс ирсэн тооцоололтой утгыг ДАХИН тооцоолж шалгана.
JavaScript-ийг өөрчилж хуурамч утга илгээж болох учраас серверт давхар тооцоолол хийнэ.

Зорилго:
1. Client-submitted final_result-ийг ШАЛГАХ
2. raw_data-аас дахин тооцоолж хамгийн зөв үр дүнг олох
3. Зөрүү байвал LOG бичиж анхааруулах
4. Server-calculated утгыг DB-д хадгалах

Хэрэглээ:
    from app.utils.server_calculations import verify_and_recalculate

    server_result, warnings = verify_and_recalculate(
        analysis_code="Mad",
        client_final_result=3.25,
        raw_data={"p1": {"m1": 10.0, "m2": 1.0, "m3": 10.97}, ...}
    )
"""

import logging
from typing import Tuple, Optional, Dict, Any, List
from math import isfinite

# Security logger
security_logger = logging.getLogger('security')

# Absolute difference threshold for calculation mismatch detection
# Used together with percent threshold (1%) to filter out rounding differences
CALC_MISMATCH_ABS_THRESHOLD = 0.01

# ============================================================================
# UNIT CONVERSION CONSTANTS (CV/Calorific Value)
# ============================================================================
# cal/g (calorie per gram) - Лабораторийн анхны тооцоолол
# kcal/kg = cal/g (тэнцүү, 1 kcal/kg = 1 cal/g)
# MJ/kg = cal/g * 4.1868 / 1000 = cal/g * 0.0041868
#
# CM Standard: kcal/kg (= cal/g)
# GBW Standard: MJ/kg
# ============================================================================
J_PER_CAL = 4.1868  # 1 calorie = 4.1868 joules
MJ_PER_KCAL = 0.0041868  # 1 kcal = 0.0041868 MJ


def cv_cal_to_mj(cv_cal_g: float) -> float:
    """
    Convert CV from cal/g (= kcal/kg) to MJ/kg.

    Args:
        cv_cal_g: Calorific value in cal/g

    Returns:
        Calorific value in MJ/kg
    """
    return cv_cal_g * MJ_PER_KCAL


def cv_mj_to_cal(cv_mj_kg: float) -> float:
    """
    Convert CV from MJ/kg to cal/g (= kcal/kg).

    Args:
        cv_mj_kg: Calorific value in MJ/kg

    Returns:
        Calorific value in cal/g
    """
    return cv_mj_kg / MJ_PER_KCAL


def _safe_float(value: Any) -> Optional[float]:
    """
    Convert value to float safely.

    Args:
        value: Any value to convert

    Returns:
        float or None
    """
    if value is None:
        return None
    try:
        f = float(value)
        return f if isfinite(f) else None
    except (ValueError, TypeError):
        return None


def _get_from_dict(d: Dict, *keys) -> Optional[float]:
    """
    Get nested dict value and convert to float.

    Args:
        d: Dictionary to search
        *keys: Path keys (e.g., "p1", "m1")

    Returns:
        float or None
    """
    current = d
    for key in keys:
        if not isinstance(current, dict):
            return None
        current = current.get(key)
        if current is None:
            return None
    return _safe_float(current)


# ============================================================================
# ANALYSIS CALCULATION FUNCTIONS
# ============================================================================

def calc_moisture_mad(raw_data: Dict) -> Optional[float]:
    """
    Аналитик Чийг (Mad) тооцоолол

    Formula: Mad% = ((m1 + m2) - m3) / m2 * 100

    Args:
        raw_data: {"p1": {"m1": ..., "m2": ..., "m3": ...}, "p2": {...}}

    Returns:
        Average Mad% or None
    """
    # Parallel 1
    m1_p1 = _get_from_dict(raw_data, "p1", "m1")
    m2_p1 = _get_from_dict(raw_data, "p1", "m2")
    m3_p1 = _get_from_dict(raw_data, "p1", "m3")

    # Parallel 2
    m1_p2 = _get_from_dict(raw_data, "p2", "m1")
    m2_p2 = _get_from_dict(raw_data, "p2", "m2")
    m3_p2 = _get_from_dict(raw_data, "p2", "m3")

    results = []

    # Calculate p1
    if m1_p1 is not None and m2_p1 is not None and m3_p1 is not None and m2_p1 > 0:
        wet_weight_loss = (m1_p1 + m2_p1) - m3_p1
        if wet_weight_loss >= 0:
            res1 = (wet_weight_loss / m2_p1) * 100
            results.append(res1)

    # Calculate p2
    if m1_p2 is not None and m2_p2 is not None and m3_p2 is not None and m2_p2 > 0:
        wet_weight_loss = (m1_p2 + m2_p2) - m3_p2
        if wet_weight_loss >= 0:
            res2 = (wet_weight_loss / m2_p2) * 100
            results.append(res2)

    if not results:
        return None

    # Return average
    return sum(results) / len(results)


def calc_ash_aad(raw_data: Dict) -> Optional[float]:
    """
    Үнс (Aad) тооцоолол

    Formula: Aad% = (m3 - m1) / m2 * 100

    Args:
        raw_data: {"p1": {"m1": ..., "m2": ..., "m3": ...}, "p2": {...}}

    Returns:
        Average Aad% or None
    """
    # Parallel 1
    m1_p1 = _get_from_dict(raw_data, "p1", "m1")
    m2_p1 = _get_from_dict(raw_data, "p1", "m2")
    m3_p1 = _get_from_dict(raw_data, "p1", "m3")

    # Parallel 2
    m1_p2 = _get_from_dict(raw_data, "p2", "m1")
    m2_p2 = _get_from_dict(raw_data, "p2", "m2")
    m3_p2 = _get_from_dict(raw_data, "p2", "m3")

    results = []

    # Calculate p1
    if all(x is not None and x > 0 for x in [m1_p1, m2_p1, m3_p1]):
        res1 = ((m3_p1 - m1_p1) / m2_p1) * 100
        if res1 >= 0:
            results.append(res1)

    # Calculate p2
    if all(x is not None and x > 0 for x in [m1_p2, m2_p2, m3_p2]):
        res2 = ((m3_p2 - m1_p2) / m2_p2) * 100
        if res2 >= 0:
            results.append(res2)

    if not results:
        return None

    return sum(results) / len(results)


def calc_volatile_vad(raw_data: Dict) -> Optional[float]:
    """
    Дэгдэмхий бодис (Vad) тооцоолол

    Formula: Vad% = ((m2 - m3) / m1) * 100

    Args:
        raw_data: {"p1": {"m1": ..., "m2": ..., "m3": ...}, "p2": {...}}

    Returns:
        Average Vad% or None
    """
    m1_p1 = _get_from_dict(raw_data, "p1", "m1")
    m2_p1 = _get_from_dict(raw_data, "p1", "m2")
    m3_p1 = _get_from_dict(raw_data, "p1", "m3")

    m1_p2 = _get_from_dict(raw_data, "p2", "m1")
    m2_p2 = _get_from_dict(raw_data, "p2", "m2")
    m3_p2 = _get_from_dict(raw_data, "p2", "m3")

    results = []

    if all(x is not None and x > 0 for x in [m1_p1, m2_p1, m3_p1]):
        res1 = ((m2_p1 - m3_p1) / m1_p1) * 100
        if res1 >= 0:
            results.append(res1)

    if all(x is not None and x > 0 for x in [m1_p2, m2_p2, m3_p2]):
        res2 = ((m2_p2 - m3_p2) / m1_p2) * 100
        if res2 >= 0:
            results.append(res2)

    if not results:
        return None

    return sum(results) / len(results)


def calc_total_moisture_mt(raw_data: Dict) -> Optional[float]:
    """
    Нийт Чийг (MT) тооцоолол

    Formula: MT% = ((m1 - m2) / m1) * 100

    Args:
        raw_data: {"p1": {"m1": ..., "m2": ...}, "p2": {...}}

    Returns:
        Average MT% or None
    """
    m1_p1 = _get_from_dict(raw_data, "p1", "m1")
    m2_p1 = _get_from_dict(raw_data, "p1", "m2")

    m1_p2 = _get_from_dict(raw_data, "p2", "m1")
    m2_p2 = _get_from_dict(raw_data, "p2", "m2")

    results = []

    if all(x is not None and x > 0 for x in [m1_p1, m2_p1]):
        res1 = ((m1_p1 - m2_p1) / m1_p1) * 100
        if res1 >= 0:
            results.append(res1)

    if all(x is not None and x > 0 for x in [m1_p2, m2_p2]):
        res2 = ((m1_p2 - m2_p2) / m1_p2) * 100
        if res2 >= 0:
            results.append(res2)

    if not results:
        return None

    return sum(results) / len(results)


def calc_sulfur_ts(raw_data: Dict) -> Optional[float]:
    """
    Хүхэр (TS) тооцоолол - Gravimetric method

    Formula: S% = ((m2 - m1) / m_sample) * K * 100

    Args:
        raw_data: {"p1": {"m1": ..., "m2": ..., "m_sample": ..., "k": ...}, ...}

    Returns:
        Average S% or None
    """
    m1_p1 = _get_from_dict(raw_data, "p1", "m1")
    m2_p1 = _get_from_dict(raw_data, "p1", "m2")
    ms_p1 = _get_from_dict(raw_data, "p1", "m_sample")
    k_p1 = _get_from_dict(raw_data, "p1", "k") or 0.34296

    m1_p2 = _get_from_dict(raw_data, "p2", "m1")
    m2_p2 = _get_from_dict(raw_data, "p2", "m2")
    ms_p2 = _get_from_dict(raw_data, "p2", "m_sample")
    k_p2 = _get_from_dict(raw_data, "p2", "k") or 0.34296

    results = []

    if all(x is not None and x > 0 for x in [m1_p1, m2_p1, ms_p1]):
        res1 = ((m2_p1 - m1_p1) / ms_p1) * k_p1 * 100
        if res1 >= 0:
            results.append(res1)

    if all(x is not None and x > 0 for x in [m1_p2, m2_p2, ms_p2]):
        res2 = ((m2_p2 - m1_p2) / ms_p2) * k_p2 * 100
        if res2 >= 0:
            results.append(res2)

    if not results:
        return None

    return sum(results) / len(results)


def calc_phosphorus_p(raw_data: Dict) -> Optional[float]:
    """
    Фосфор (P) тооцоолол

    Formula: P% = ((V - V0) * C * 0.0030974 * 100) / m_sample

    Args:
        raw_data: {"p1": {"v": ..., "v0": ..., "c": ..., "m_sample": ...}, ...}

    Returns:
        Average P% or None
    """
    v_p1 = _get_from_dict(raw_data, "p1", "v")
    v0_p1 = _get_from_dict(raw_data, "p1", "v0")
    c_p1 = _get_from_dict(raw_data, "p1", "c")
    ms_p1 = _get_from_dict(raw_data, "p1", "m_sample")

    v_p2 = _get_from_dict(raw_data, "p2", "v")
    v0_p2 = _get_from_dict(raw_data, "p2", "v0")
    c_p2 = _get_from_dict(raw_data, "p2", "c")
    ms_p2 = _get_from_dict(raw_data, "p2", "m_sample")

    K = 0.0030974  # P conversion factor

    results = []

    if all(x is not None for x in [v_p1, v0_p1, c_p1, ms_p1]) and ms_p1 > 0:
        res1 = ((v_p1 - v0_p1) * c_p1 * K * 100) / ms_p1
        if res1 >= 0:
            results.append(res1)

    if all(x is not None for x in [v_p2, v0_p2, c_p2, ms_p2]) and ms_p2 > 0:
        res2 = ((v_p2 - v0_p2) * c_p2 * K * 100) / ms_p2
        if res2 >= 0:
            results.append(res2)

    if not results:
        return None

    return sum(results) / len(results)


def calc_fluorine_f(raw_data: Dict) -> Optional[float]:
    """
    Фтор (F) тооцоолол

    Uses manually entered results from parallel measurements

    Args:
        raw_data: {"p1": {"result": ...}, "p2": {"result": ...}}

    Returns:
        Average F% or None
    """
    result_p1 = _get_from_dict(raw_data, "p1", "result")
    result_p2 = _get_from_dict(raw_data, "p2", "result")

    results = []

    if result_p1 is not None and result_p1 >= 0:
        results.append(result_p1)

    if result_p2 is not None and result_p2 >= 0:
        results.append(result_p2)

    if not results:
        return None

    return sum(results) / len(results)


def calc_chlorine_cl(raw_data: Dict) -> Optional[float]:
    """
    Хлор (Cl) тооцоолол

    Uses manually entered results from parallel measurements

    Args:
        raw_data: {"p1": {"result": ...}, "p2": {"result": ...}}

    Returns:
        Average Cl% or None
    """
    result_p1 = _get_from_dict(raw_data, "p1", "result")
    result_p2 = _get_from_dict(raw_data, "p2", "result")

    results = []

    if result_p1 is not None and result_p1 >= 0:
        results.append(result_p1)

    if result_p2 is not None and result_p2 >= 0:
        results.append(result_p2)

    if not results:
        return None

    return sum(results) / len(results)


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

    Unit Notes:
        - cal/g = kcal/kg (CM Standard)
        - MJ/kg = cal/g * 0.0041868 (GBW Standard)
        - J/g = cal/g * 4.1868
    """
    # Constants
    J_PER_CAL = 4.1868
    S_CORR_FACTOR = 94.1

    def get_alpha(qb_jg: float) -> float:
        """Get temperature-dependent alpha coefficient."""
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
        if m == 0:
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


def calc_gray_king_gi(raw_data: Dict) -> Optional[float]:
    """
    Gray-King Index (Gi) тооцоолол

    Formula (two modes):
    - 5:1 mode (default): Gi = 10 + (30*m2 + 70*m3) / m1
    - 3:3 mode (retest):  Gi = (30*m2 + 70*m3) / (5*m1)

    Mode detection: Check if "mode" or "retest" field indicates 3:3 mode

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
        is_33_mode = mode and ("3:3" in str(mode) or "retest" in str(mode).lower())

        if is_33_mode:
            # 3:3 mode (retest)
            gi = numerator / (5 * m1)
        else:
            # 5:1 mode (default)
            gi = 10 + (numerator / m1)

        return round(gi) if isfinite(gi) else None

    # Parallel 1
    p1 = raw_data.get("p1") or {}
    m1_p1 = _safe_float(p1.get("m1"))
    m2_p1 = _safe_float(p1.get("m2"))
    m3_p1 = _safe_float(p1.get("m3"))
    mode_p1 = p1.get("mode") or p1.get("retest_mode")

    # Parallel 2
    p2 = raw_data.get("p2") or {}
    m1_p2 = _safe_float(p2.get("m1"))
    m2_p2 = _safe_float(p2.get("m2"))
    m3_p2 = _safe_float(p2.get("m3"))
    mode_p2 = p2.get("mode") or p2.get("retest_mode")

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

    # Return average (already rounded)
    return sum(results) / len(results)


def calc_free_moisture_fm(raw_data: Dict) -> Optional[float]:
    """
    Чөлөөт чийг (FM) тооцоолол

    Formula: FM% = ((Wb - Wa) / (Wa - Wt)) * 100

    Where:
    - Wt = Tray weight (тавиурын жин)
    - Wb = Weight before drying (хатаахын өмнө)
    - Wa = Weight after drying (хатаасны дараа)

    Args:
        raw_data: {
            "p1": {"wt": ..., "wb": ..., "wa": ...},
            "p2": {...}
        }

    Returns:
        Average FM% or None
    """
    def calc_single_fm(wt, wb, wa) -> Optional[float]:
        """Calculate FM for single parallel."""
        if not all(x is not None and isfinite(x) for x in [wt, wb, wa]):
            return None

        numerator = wb - wa
        denominator = wa - wt

        if denominator == 0:
            return None

        fm = (numerator / denominator) * 100

        return fm if isfinite(fm) and fm >= 0 else None

    # Parallel 1
    p1 = raw_data.get("p1") or {}
    wt_p1 = _safe_float(p1.get("wt") or p1.get("Wt"))
    wb_p1 = _safe_float(p1.get("wb") or p1.get("Wb"))
    wa_p1 = _safe_float(p1.get("wa") or p1.get("Wa"))

    # Parallel 2
    p2 = raw_data.get("p2") or {}
    wt_p2 = _safe_float(p2.get("wt") or p2.get("Wt"))
    wb_p2 = _safe_float(p2.get("wb") or p2.get("Wb"))
    wa_p2 = _safe_float(p2.get("wa") or p2.get("Wa"))

    results = []

    # Calculate p1
    r1 = calc_single_fm(wt_p1, wb_p1, wa_p1)
    if r1 is not None:
        results.append(r1)

    # Calculate p2
    r2 = calc_single_fm(wt_p2, wb_p2, wa_p2)
    if r2 is not None:
        results.append(r2)

    if not results:
        return None

    return sum(results) / len(results)


def calc_solid(raw_data: Dict) -> Optional[float]:
    """
    Хатуу бодис (Solid) тооцоолол

    Formula: Solid% = C * 100 / (A - B)

    Where:
    - A, B, C = Mass measurements
    - wet_mass = A - B

    Args:
        raw_data: {
            "p1": {"a": ..., "b": ..., "c": ...},
            "p2": {...}
        }

    Returns:
        Average Solid% or None
    """
    def calc_single_solid(a, b, c) -> Optional[float]:
        """Calculate Solid for single parallel."""
        if not all(x is not None and isfinite(x) for x in [a, b, c]):
            return None

        denominator = a - b

        if denominator == 0:
            return None

        solid = (c * 100) / denominator

        return solid if isfinite(solid) and solid >= 0 else None

    # Parallel 1
    p1 = raw_data.get("p1") or {}
    a_p1 = _safe_float(p1.get("a") or p1.get("A"))
    b_p1 = _safe_float(p1.get("b") or p1.get("B"))
    c_p1 = _safe_float(p1.get("c") or p1.get("C"))

    # Parallel 2
    p2 = raw_data.get("p2") or {}
    a_p2 = _safe_float(p2.get("a") or p2.get("A"))
    b_p2 = _safe_float(p2.get("b") or p2.get("B"))
    c_p2 = _safe_float(p2.get("c") or p2.get("C"))

    results = []

    # Calculate p1
    r1 = calc_single_solid(a_p1, b_p1, c_p1)
    if r1 is not None:
        results.append(r1)

    # Calculate p2
    r2 = calc_single_solid(a_p2, b_p2, c_p2)
    if r2 is not None:
        results.append(r2)

    if not results:
        return None

    return sum(results) / len(results)


def calc_trd(raw_data: Dict) -> Optional[float]:
    """
    Үнэн харьцангуй нягт (TRD) тооцоолол

    Formula:
    1. md = m * (100 - mad) / 100  (dry mass)
    2. TRD = (md / (md + m2 - m1)) * kt

    Where:
    - m = coal sample mass
    - mad = moisture content (from previous analysis)
    - m1 = bottle + water mass
    - m2 = bottle + water + coal mass
    - kt = temperature coefficient (from KT_TABLE)

    Note: This calculation requires mad from previous analysis and kt from temperature.

    Args:
        raw_data: {
            "p1": {"m": ..., "m1": ..., "m2": ..., "temp": ..., "mad": ...},
            "p2": {...},
            "mad": ... (global moisture value if not in p1/p2)
        }

    Returns:
        Average TRD or None
    """
    # Temperature coefficient table (6-35°C)
    KT_TABLE = {
        6: 0.99997, 7: 0.99993, 8: 0.99988, 9: 0.99981, 10: 0.99973,
        11: 0.99963, 12: 0.99952, 13: 0.99940, 14: 0.99927, 15: 0.99913,
        16: 0.99897, 17: 0.99880, 18: 0.99862, 19: 0.99843, 20: 0.99823,
        21: 0.99802, 22: 0.99780, 23: 0.99756, 24: 0.99732, 25: 0.99707,
        26: 0.99681, 27: 0.99654, 28: 0.99626, 29: 0.99597, 30: 0.99567,
        31: 0.99537, 32: 0.99505, 33: 0.99473, 34: 0.99440, 35: 0.99406
    }

    def get_kt(temp: Optional[float]) -> Optional[float]:
        """Get kt coefficient from temperature (with interpolation)."""
        if temp is None or not isfinite(temp):
            return None

        # Round to nearest integer
        temp_int = round(temp)

        # Check bounds
        if temp_int < 6 or temp_int > 35:
            return None

        return KT_TABLE.get(temp_int)

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

        if denominator == 0:
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


# ============================================================================
# CALCULATION DISPATCHER
# ============================================================================

# Map analysis codes to calculation functions
CALCULATION_FUNCTIONS = {
    # ---- Moisture & Ash ----
    "Mad": calc_moisture_mad,
    "M": calc_moisture_mad,

    "Aad": calc_ash_aad,
    "A": calc_ash_aad,

    "Vad": calc_volatile_vad,
    "V": calc_volatile_vad,

    "MT": calc_total_moisture_mt,

    # ---- Sulfur, Phosphorus ----
    "TS": calc_sulfur_ts,
    "St,ad": calc_sulfur_ts,
    "S": calc_sulfur_ts,

    "P": calc_phosphorus_p,
    "P,ad": calc_phosphorus_p,

    # ---- Fluorine, Chlorine ----
    "F": calc_fluorine_f,
    "F,ad": calc_fluorine_f,

    "Cl": calc_chlorine_cl,
    "Cl,ad": calc_chlorine_cl,

    # ---- Calorific Value ----
    "CV": calc_calorific_value_cv,
    "Qgr,ad": calc_calorific_value_cv,
    "Qgr": calc_calorific_value_cv,

    # ---- Gray-King Index ----
    "Gi": calc_gray_king_gi,
    "GI": calc_gray_king_gi,

    # ---- Free Moisture ----
    "FM": calc_free_moisture_fm,

    # ---- Solid Content ----
    "Solid": calc_solid,

    # ---- True Relative Density ----
    "TRD": calc_trd,
    "TRD,d": calc_trd,
}


def verify_and_recalculate(
    analysis_code: str,
    client_final_result: Optional[float],
    raw_data: Dict[str, Any],
    user_id: Optional[int] = None,
    sample_id: Optional[int] = None
) -> Tuple[Optional[float], List[str]]:
    """
    Verify client-submitted result by recalculating on server.

    🔒 SECURITY: Клиентээс ирсэн үр дүнг дахин тооцоолж шалгана.

    Args:
        analysis_code: Analysis code (e.g., "Mad", "Aad")
        client_final_result: Final result submitted by client
        raw_data: Raw measurement data
        user_id: User ID (for logging)
        sample_id: Sample ID (for logging)

    Returns:
        (final_result, warnings)
        - final_result: Server-calculated result (or client if no calculation available)
        - warnings: List of warning messages
    """
    warnings = []

    # Normalize code
    from app.utils.codes import norm_code
    analysis_code = norm_code(analysis_code)

    # Get calculation function
    calc_func = CALCULATION_FUNCTIONS.get(analysis_code)

    if calc_func is None:
        # No server-side calculation available for this analysis
        # Use client value but log it
        if client_final_result is not None:
            security_logger.info(
                f"No server calculation for {analysis_code} - using client value: "
                f"{client_final_result} (user={user_id}, sample={sample_id})"
            )
        return client_final_result, warnings

    # Calculate on server
    try:
        server_result = calc_func(raw_data)
    except Exception as e:
        error_msg = f"Server calculation error for {analysis_code}: {str(e)}"
        security_logger.error(
            f"{error_msg} (user={user_id}, sample={sample_id})",
            exc_info=True
        )
        warnings.append(error_msg)
        # Fallback to client value
        return client_final_result, warnings

    # Compare server vs client
    if server_result is not None and client_final_result is not None:
        diff = abs(server_result - client_final_result)
        percent_diff = (diff / max(abs(server_result), 0.0001)) * 100

        if diff > CALC_MISMATCH_ABS_THRESHOLD and percent_diff > 1.0:  # More than 1% difference
            warning_msg = (
                f"⚠️ CALCULATION MISMATCH: {analysis_code} - "
                f"Client={client_final_result:.4f}, Server={server_result:.4f}, "
                f"Diff={diff:.4f} ({percent_diff:.2f}%)"
            )
            warnings.append(warning_msg)

            # 🔒 SECURITY LOG
            security_logger.warning(
                f"POTENTIAL TAMPERING: {analysis_code} calculation mismatch - "
                f"client={client_final_result:.4f}, server={server_result:.4f}, "
                f"diff={diff:.4f} ({percent_diff:.2f}%) "
                f"(user={user_id}, sample={sample_id}, raw_data={raw_data})"
            )

    # Use server-calculated result if available
    if server_result is not None:
        return server_result, warnings

    # Fallback to client value
    return client_final_result, warnings


def bulk_verify_results(
    items: List[Dict[str, Any]],
    user_id: Optional[int] = None
) -> Dict[str, Any]:
    """
    Verify multiple results in bulk.

    Args:
        items: List of items with analysis_code, final_result, raw_data
        user_id: User ID for logging

    Returns:
        {
            "verified_items": [...],  # Items with server-calculated results
            "total_warnings": int,
            "total_mismatches": int,
        }
    """
    verified_items = []
    total_warnings = 0
    total_mismatches = 0

    for item in items:
        analysis_code = item.get("analysis_code")
        client_result = item.get("final_result")
        raw_data = item.get("raw_data") or {}
        sample_id = item.get("sample_id")

        server_result, warnings = verify_and_recalculate(
            analysis_code=analysis_code,
            client_final_result=client_result,
            raw_data=raw_data,
            user_id=user_id,
            sample_id=sample_id
        )

        # Create verified item
        verified_item = dict(item)
        verified_item["final_result"] = server_result
        verified_item["server_verified"] = True
        verified_item["verification_warnings"] = warnings

        if warnings:
            total_warnings += len(warnings)
            if any("MISMATCH" in w for w in warnings):
                total_mismatches += 1

        verified_items.append(verified_item)

    return {
        "verified_items": verified_items,
        "total_warnings": total_warnings,
        "total_mismatches": total_mismatches,
    }
