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


def is_safe_url(target):
    """
    Аюулгүй redirect URL эсэхийг шалгах (Open Redirect халдлагаас хамгаалах).

    Open Redirect халдлага нь хортой URL руу redirect хийлгэх халдлагын төрөл.
    Жишээ: http://mysite.com/login?next=http://evil.com

    Энэ функц зөвхөн өөрийн domain дотор redirect хийхийг зөвшөөрнө.

    Args:
        target: Redirect хийх URL (жишээ: "/dashboard", "http://mysite.com/profile")

    Returns:
        bool: Аюулгүй бол True, эсрэг тохиолдолд False

    Examples:
        >>> # Flask request context дотор:
        >>> is_safe_url("/dashboard")  # Харьцангуй URL - OK
        True
        >>> is_safe_url("http://mysite.com/profile")  # Өөрийн domain - OK
        True
        >>> is_safe_url("http://evil.com")  # Өөр domain - Аюултай!
        False

    Notes:
        - Flask request context шаардлагатай (request.host_url ашиглана)
        - Харьцангуй URL-үүд ("/path") автоматаар аюулгүй гэж үзнэ
        - Өмнө нь app/routes/main/helpers.py-д байсан
    """
    from flask import request
    from urllib.parse import urlparse, urljoin

    host_url = urlparse(request.host_url)
    test_url = urlparse(urljoin(request.host_url, target))

    return (
        test_url.scheme in ("http", "https") or test_url.scheme == ""
    ) and test_url.netloc == host_url.netloc
