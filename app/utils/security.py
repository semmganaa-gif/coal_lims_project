# app/utils/security.py
# -*- coding: utf-8 -*-
"""
Аюулгүй байдлын utility функцүүд.

Энэ модуль нь системийн аюулгүй байдалтай холбоотой utility функцүүдийг агуулна:
- SQL injection сэргийлэлт
- Input sanitization
- Security validation

Author: Energy Resources IT Team
Date: 2025-11-24
"""

from typing import Optional


def escape_like_pattern(text: Optional[str]) -> Optional[str]:
    """
    LIKE операторын тусгай тэмдэгтүүдийг escape хийж SQL injection сэргийлнэ.

    SQL LIKE операторт `%` болон `_` тэмдэгтүүд wildcard болж ашиглагддаг.
    Хэрэглэгчийн оролтонд эдгээр тэмдэгтүүд байвал хүсээгүй үр дүн гарч,
    эсвэл SQL injection халдлага хийх боломжтой болно.

    Энэ функц эдгээр тэмдэгтүүдийг escape хийж, аюулгүй болгоно.

    Args:
        text (str, optional): Escape хийх текст. None байж болно.

    Returns:
        str, optional: Escape хийгдсэн текст. Input None бол None буцаана.

    Example:
        >>> escape_like_pattern("test%value")
        'test\\%value'
        >>> escape_like_pattern("user_input")
        'user\\_input'
        >>> escape_like_pattern(None)
        None

    Notes:
        - Backslash (\\) эхлээд escape хийгдэнэ
        - Percent (%) → \\%
        - Underscore (_) → \\_
        - SQLAlchemy-тай хамт ашиглахад тохиромжтой

    Security:
        Энэ функцийг БҮГД хэрэглэгчийн оролттой LIKE query-д заавал ашиглах!
    """
    if not text:
        return text

    # Backslash-ийг эхлээд escape хийх (давхар escape үүсэхээс сэргийлнэ)
    # Дараа нь % болон _ тэмдэгтүүдийг escape хийх
    return text.replace('\\', '\\\\').replace('%', '\\%').replace('_', '\\_')
