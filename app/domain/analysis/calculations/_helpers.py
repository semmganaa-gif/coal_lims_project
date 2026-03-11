# app/utils/server_calculations/_helpers.py
# -*- coding: utf-8 -*-
"""
Shared helper functions and constants for server-side calculations.
"""

import logging
from typing import Optional, Dict, Any
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
