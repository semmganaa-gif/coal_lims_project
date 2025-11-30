# app/routes/main/helpers.py
# -*- coding: utf-8 -*-
"""
Main модулийн туслах функцүүд
"""

from flask import request
from urllib.parse import urlparse, urljoin


def get_12h_shift_code(dt):
    """12 цагийн ээлжийн код (_D / _N)"""
    hour = dt.hour
    return "_D" if 7 <= hour < 19 else "_N"


def get_quarter_code(dt):
    """Улирлын код (_Q1.._Q4)"""
    month = dt.month
    if month <= 3:
        return "_Q1"
    elif month <= 6:
        return "_Q2"
    elif month <= 9:
        return "_Q3"
    else:
        return "_Q4"


def is_safe_url(target):
    """Аюулгүй redirect шалгах"""
    host_url = urlparse(request.host_url)
    test_url = urlparse(urljoin(request.host_url, target))
    return (
        test_url.scheme in ("http", "https") or test_url.scheme == ""
    ) and test_url.netloc == host_url.netloc
