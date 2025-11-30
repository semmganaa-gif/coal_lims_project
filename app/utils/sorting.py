# app/utils/sorting.py
# -*- coding: utf-8 -*-
"""
Дээжний кодыг эрэмбэлэх нэгдсэн функцууд.
Давхардлыг арилгахын тулд main_routes ба analysis_routes-аас энд шилжүүлсэн.
"""
import re
from app.constants import CHPP_2H_SAMPLES_ORDER, ALL_12H_SAMPLES


def natural_sort_key(s):
    """
    Текст доторх тоог тоо гэж таньж эрэмбэлнэ (N1, N2, N10).

    Жишээ:
        ["N10", "N2", "N1"] -> ["N1", "N2", "N10"]

    Args:
        s: Эрэмбэлэх текст

    Returns:
        list: Эрэмбэлэх түлхүүр (тоо болон текст)
    """
    return [int(text) if text.isdigit() else text.lower()
            for text in re.split('([0-9]+)', str(s))]


def custom_sample_sort_key(code):
    """
    Дээжний нэрийг эрэмбэлэх хатуу логик:
    1. CHPP 2H (PF211 -> PF221 -> PF231 -> CC -> TC)
    2. CHPP 12H (Жагсаалтын индексээр)
    3. Бусад (Natural Sort)

    Args:
        code: Дээжний код

    Returns:
        tuple: Эрэмбэлэх түлхүүр (эрэмбийн групп, индекс, нэр)
    """
    code_str = str(code)

    # 1. CHPP 2H дараалал
    for idx, prefix in enumerate(CHPP_2H_SAMPLES_ORDER):
        if code_str.startswith(prefix):
            suffix = code_str[len(prefix):]
            return (0, idx, natural_sort_key(suffix))

    # 2. CHPP 12H дараалал (Жагсаалтын индексээр)
    for idx, item in enumerate(ALL_12H_SAMPLES):
        if code_str.startswith(item['name']):
            return (1, idx, natural_sort_key(code_str))

    # 3. Бусад (Natural Sort)
    return (2, natural_sort_key(code_str))
