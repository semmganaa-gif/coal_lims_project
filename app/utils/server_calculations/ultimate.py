# app/utils/server_calculations/ultimate.py
# -*- coding: utf-8 -*-
"""
Ultimate analysis calculations: Sulfur (TS), Phosphorus (P), Fluorine (F), Chlorine (Cl).
"""

from typing import Optional, Dict

from ._helpers import _get_from_dict


def calc_sulfur_ts(raw_data: Dict) -> Optional[float]:
    """
    Хүхэр (TS / St,ad) тооцоолол — Автомат анализатор (MNS ISO 19579)

    Инструментээс шууд ирсэн хоёр зэрэгцээ үр дүнгийн дундаж.
    Formula: avg = (p1.result + p2.result) / 2

    Args:
        raw_data: {"p1": {"result": ..., "weight": ...}, "p2": {"result": ..., "weight": ...}}

    Returns:
        Average St,ad% or None
    """
    r1 = _get_from_dict(raw_data, "p1", "result")
    r2 = _get_from_dict(raw_data, "p2", "result")

    results = []

    if r1 is not None:
        results.append(r1)
    if r2 is not None:
        results.append(r2)

    if not results:
        return None

    return sum(results) / len(results)


def calc_phosphorus_p(raw_data: Dict) -> Optional[float]:
    """
    Фосфор (P) тооцоолол — Автомат анализатор (багажит шинжилгээ)

    Formula: avg = (p1.result + p2.result) / 2

    Args:
        raw_data: {"p1": {"result": ...}, "p2": {"result": ...}}

    Returns:
        Average P% or None
    """
    r1 = _get_from_dict(raw_data, "p1", "result")
    r2 = _get_from_dict(raw_data, "p2", "result")

    results = []
    if r1 is not None:
        results.append(r1)
    if r2 is not None:
        results.append(r2)

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
