# app/utils/converters.py
# -*- coding: utf-8 -*-
"""
Төрөл хөрвүүлэх туслах функцүүд
"""
from typing import Any, Optional


def to_float(v: Any) -> Optional[float]:
    """
    Утгыг float болгох. Буруу утгад None буцаана.

    Args:
        v: Хөрвүүлэх утга (string, int, float)

    Returns:
        Optional[float]: Хөрвүүлсэн тоо эсвэл None

    Note:
        - "null", "none", "na", "n/a", "-" утгуудыг None гэж үзнэ
        - Таслалыг (,) цэг (.) болгож хөрвүүлнэ
        - Хоосон зай, non-breaking space арилгана
    """
    if v is None:
        return None
    if isinstance(v, (int, float)):
        return float(v)
    if isinstance(v, str):
        s = v.strip().replace(" ", "").replace("\u00A0", "")
        if not s or s.lower() in ("null", "none", "na", "n/a", "-"):
            return None
        try:
            return float(s.replace(",", "."))
        except ValueError:
            return None
    return None
