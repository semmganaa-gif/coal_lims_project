# app/utils/sorting.py
# -*- coding: utf-8 -*-
"""
Дээжний кодыг эрэмбэлэх нэгдсэн функцууд.

Сайжруулалтууд:
- O(1) dict lookup (performance)
- Edge case handling (None, empty)
- Уян хатан төрөл бүрийн эрэмбэ
- Type hints
"""
import re
from typing import Any, List, Tuple, Union, Optional

from app.constants import CHPP_2H_SAMPLES_ORDER, ALL_12H_SAMPLES


# =============================================================================
# O(1) LOOKUP DICTIONARIES
# =============================================================================

# CHPP 2H - prefix → index
CHPP_2H_INDEX: dict[str, int] = {
    name: idx for idx, name in enumerate(CHPP_2H_SAMPLES_ORDER)
}

# CHPP 12H - name → index
CHPP_12H_INDEX: dict[str, int] = {
    item['name']: idx for idx, item in enumerate(ALL_12H_SAMPLES)
}

# Клиент + төрлөөр эрэмбийн priority
SORT_PRIORITY: dict[str, dict[str, int]] = {
    "CHPP": {
        "2 hourly": 0,
        "4 hourly": 1,
        "12 hourly": 2,
        "com": 3,
    },
    "UHG-Geo": {
        "Stock": 0,
        "TR": 1,
        "GRD": 2,
        "TE": 3,
        "PE": 4,
        "CQ": 5,
    },
    "BN-Geo": {
        "Stock": 0,
        "TR": 1,
        "GRD": 2,
        "TE": 3,
        "PE": 4,
        "CQ": 5,
    },
    "QC": {
        "HCC": 0,
        "SSCC": 1,
        "MASHCC": 2,
        "TC": 3,
        "Fine": 4,
        "Test": 5,
    },
    "Proc": {
        "CHP": 0,
        "HCC": 1,
        "SSCC": 2,
        "MASHCC": 3,
        "Test": 4,
    },
    "WTL": {
        "WTL": 0,
        "Size": 1,
        "FL": 2,
        "MG": 3,
        "Test": 4,
    },
    "LAB": {
        "CM": 0,
        "GBW": 1,
        "Test": 2,
    },
}


# =============================================================================
# NATURAL SORT
# =============================================================================

def natural_sort_key(s: Any) -> List[Union[int, str]]:
    """
    Текст доторх тоог тоо гэж таньж эрэмбэлнэ.

    Жишээ:
        ["N10", "N2", "N1"] → ["N1", "N2", "N10"]

    Args:
        s: Эрэмбэлэх текст (None, тоо байж болно)

    Returns:
        Эрэмбэлэх түлхүүр (тоо болон текст)
    """
    if s is None:
        return [""]

    text = str(s).strip()
    if not text:
        return [""]

    return [
        int(part) if part.isdigit() else part.lower()
        for part in re.split(r'(\d+)', text)
        if part  # Хоосон string-ийг алгасах
    ]


# =============================================================================
# SAMPLE CODE SORTING
# =============================================================================

def custom_sample_sort_key(code: Optional[str]) -> Tuple[int, int, List[Union[int, str]]]:
    """
    Дээжний нэрийг эрэмбэлэх хатуу логик (O(1) lookup):

    1. CHPP 2H (PF211 → PF221 → PF231 → CC → TC)
    2. CHPP 12H (Жагсаалтын индексээр)
    3. Бусад (Natural Sort)

    Args:
        code: Дээжний код

    Returns:
        Эрэмбэлэх түлхүүр (групп, индекс, natural_key)
    """
    # Edge case: None эсвэл хоосон
    if not code:
        return (99, 0, [""])

    code_str = str(code).strip()
    if not code_str:
        return (99, 0, [""])

    # 1. CHPP 2H - O(1) exact match эхлээд шалгах
    if code_str in CHPP_2H_INDEX:
        return (0, CHPP_2H_INDEX[code_str], natural_sort_key(code_str))

    # 1b. CHPP 2H - prefix match (PF211_D1 гэх мэт)
    for prefix, idx in CHPP_2H_INDEX.items():
        if code_str.startswith(prefix):
            suffix = code_str[len(prefix):]
            return (0, idx, natural_sort_key(suffix))

    # 2. CHPP 12H - O(1) exact match
    if code_str in CHPP_12H_INDEX:
        return (1, CHPP_12H_INDEX[code_str], natural_sort_key(code_str))

    # 2b. CHPP 12H - prefix match
    for name, idx in CHPP_12H_INDEX.items():
        if code_str.startswith(name):
            return (1, idx, natural_sort_key(code_str))

    # 3. Бусад - Natural Sort
    return (2, 0, natural_sort_key(code_str))


def get_client_type_priority(
    client_name: Optional[str],
    sample_type: Optional[str]
) -> int:
    """
    Клиент + төрлөөр эрэмбийн priority авах.

    Args:
        client_name: Клиентийн нэр (CHPP, UHG-Geo, г.м.)
        sample_type: Дээжний төрөл (2 hourly, S, г.м.)

    Returns:
        Priority тоо (бага = эхэнд)
    """
    if not client_name:
        return 99

    client_priorities = SORT_PRIORITY.get(client_name, {})
    return client_priorities.get(sample_type or "", 50)


def sample_full_sort_key(sample: Any) -> Tuple[int, int, List[Union[int, str]]]:
    """
    Sample объектыг бүрэн эрэмбэлэх түлхүүр.

    Эрэмбэ:
    1. Клиент + төрлийн priority
    2. Дээжний код (custom_sample_sort_key)

    Args:
        sample: Sample объект (client_name, sample_type, sample_code attributes)

    Returns:
        Эрэмбэлэх түлхүүр
    """
    # Sample объектоос attribute авах
    client = getattr(sample, 'client_name', None)
    stype = getattr(sample, 'sample_type', None)
    code = getattr(sample, 'sample_code', None) or getattr(sample, 'name', None)

    # Priority тооцоолох
    priority = get_client_type_priority(client, stype)

    # Custom sort key
    _, sub_idx, natural_key = custom_sample_sort_key(code)

    return (priority, sub_idx, natural_key)


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

def sort_samples(samples: List[Any], by: str = "code") -> List[Any]:
    """
    Дээжнүүдийг эрэмбэлэх.

    Args:
        samples: Дээжний жагсаалт
        by: Эрэмбэлэх арга
            - "code": Зөвхөн кодоор (custom_sample_sort_key)
            - "full": Клиент + төрөл + код (sample_full_sort_key)
            - "natural": Natural sort (кодоор)

    Returns:
        Эрэмблэгдсэн жагсаалт
    """
    if not samples:
        return []

    if by == "full":
        return sorted(samples, key=sample_full_sort_key)
    elif by == "natural":
        key_fn = lambda s: natural_sort_key(
            getattr(s, 'sample_code', None) or getattr(s, 'name', s)
        )
        return sorted(samples, key=key_fn)
    else:  # "code" - default
        key_fn = lambda s: custom_sample_sort_key(
            getattr(s, 'sample_code', None) or getattr(s, 'name', s)
        )
        return sorted(samples, key=key_fn)


def sort_codes(codes: List[str], method: str = "custom") -> List[str]:
    """
    Дээжний кодуудыг (string) эрэмбэлэх.

    Args:
        codes: Кодын жагсаалт
        method: Эрэмбэлэх арга
            - "custom": CHPP priority + natural
            - "natural": Зөвхөн natural sort

    Returns:
        Эрэмблэгдсэн жагсаалт
    """
    if not codes:
        return []

    if method == "natural":
        return sorted(codes, key=natural_sort_key)
    else:
        return sorted(codes, key=custom_sample_sort_key)
