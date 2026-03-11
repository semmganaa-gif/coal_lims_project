# app/utils/server_calculations/proximate.py
# -*- coding: utf-8 -*-
"""
Proximate analysis calculations: Mad, Aad, Vad, MT.
"""

from typing import Optional, Dict

from ._helpers import _safe_float, _get_from_dict


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

    SOP LAB.07.04 / MNS GB/T 212:2015:
    Vad% = ((m1 + m2 - m3) / m2) * 100 - Mad

    Args:
        raw_data: {"p1": {"m1": ..., "m2": ..., "m3": ...}, "p2": {...}, "mad_used": ...}

    Returns:
        Average Vad% or None
    """
    # Mad утгыг raw_data-аас авна
    mad = _safe_float(raw_data.get("mad_used"))

    m1_p1 = _get_from_dict(raw_data, "p1", "m1")
    m2_p1 = _get_from_dict(raw_data, "p1", "m2")
    m3_p1 = _get_from_dict(raw_data, "p1", "m3")

    m1_p2 = _get_from_dict(raw_data, "p2", "m1")
    m2_p2 = _get_from_dict(raw_data, "p2", "m2")
    m3_p2 = _get_from_dict(raw_data, "p2", "m3")

    results = []

    if all(x is not None for x in [m1_p1, m2_p1, m3_p1]) and m2_p1 > 0:
        weight_loss = (m1_p1 + m2_p1) - m3_p1
        if weight_loss >= 0:
            res1 = (weight_loss / m2_p1) * 100
            if mad is not None:
                res1 -= mad
            if res1 < 0:
                res1 = 0
            results.append(res1)

    if all(x is not None for x in [m1_p2, m2_p2, m3_p2]) and m2_p2 > 0:
        weight_loss = (m1_p2 + m2_p2) - m3_p2
        if weight_loss >= 0:
            res2 = (weight_loss / m2_p2) * 100
            if mad is not None:
                res2 -= mad
            if res2 < 0:
                res2 = 0
            results.append(res2)

    if not results:
        return None

    return sum(results) / len(results)


def calc_total_moisture_mt(raw_data: Dict) -> Optional[float]:
    """
    Нийт Чийг (MT) тооцоолол

    Formula: MT% = ((m2 - m3) / (m2 - m1)) * 100
    MG format: Result% = ((m1 + m2 - m3) / m2) * 100

    Args:
        raw_data: {"p1": {"m1": ..., "m2": ..., "m3": ...}, "p2": {...}}
                  OR MG format: {"m1": crucible, "m2": sample, "m3": dried}

    Returns:
        Average MT% or None
    """
    from .mg_calcs import calc_mg_mt

    # MG format detection: flat m1/m2/m3 without p1/p2
    is_flat = all(k in raw_data for k in ['m1', 'm2', 'm3']) and 'p1' not in raw_data
    if is_flat:
        return calc_mg_mt(raw_data)

    m1_p1 = _get_from_dict(raw_data, "p1", "m1")
    m2_p1 = _get_from_dict(raw_data, "p1", "m2")
    m3_p1 = _get_from_dict(raw_data, "p1", "m3")

    m1_p2 = _get_from_dict(raw_data, "p2", "m1")
    m2_p2 = _get_from_dict(raw_data, "p2", "m2")
    m3_p2 = _get_from_dict(raw_data, "p2", "m3")

    results = []

    if all(x is not None and x > 0 for x in [m1_p1, m2_p1, m3_p1]):
        sample_mass = m2_p1 - m1_p1
        if sample_mass > 0:
            res1 = ((m2_p1 - m3_p1) / sample_mass) * 100
            if res1 >= 0:
                results.append(res1)

    if all(x is not None and x > 0 for x in [m1_p2, m2_p2, m3_p2]):
        sample_mass = m2_p2 - m1_p2
        if sample_mass > 0:
            res2 = ((m2_p2 - m3_p2) / sample_mass) * 100
            if res2 >= 0:
                results.append(res2)

    if not results:
        return None

    return sum(results) / len(results)
