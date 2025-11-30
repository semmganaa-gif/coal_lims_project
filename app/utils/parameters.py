# app/utils/parameters.py
# -*- coding: utf-8 -*-
"""
Параметрийн нэршлийг каноник хэлбэрт хувиргах ба 'ad' суурьтай
зарим тооцооллыг гүйцэтгэх туслах функцууд.
"""

from app.constants import PARAMETER_DEFINITIONS, param_key


def get_canonical_name(input_name):
    """
    Оролтын ямар ч нэршлийг (alias, lab code, base code г.м.) каноник түлхүүрт
    хувиргана. `constants.param_key()` нь бүх цэвэрлэгээг (unicode comma,
    илүүдэл зай, casefold) хийдэг тул түүгээр дамжуулж авч байна.
    """
    if not input_name:
        return None
    name = str(input_name).strip()
    canonical = param_key(name)   # олдвол каноник нэр, үгүй бол None
    # Хэрэв mapping байхгүй бол цэвэрлэсэн нэрээр нь буцаая (defensive fallback)
    return canonical or name


def get_parameter_details(name):
    """
    Аль ч нэршлээс тухайн параметрийн дэлгэрэнгүй тодорхойлолтыг буцаана.
    """
    canonical = get_canonical_name(name)
    if not canonical:
        return None

    details = PARAMETER_DEFINITIONS.get(canonical)
    if details:
        return details

    # Тодорхойлолт олдохгүй бол энгийн мэдээлэл буцаана.
    return {
        "display_name": name,
        "lab_code": None,
        "standard_method": None,
        "aliases": [name],
        "type": "unknown",
    }


def calculate_value(canonical_name, inputs_dict):
    """
    'ad' суурьтай энгийн тооцооллыг хийнэ. (жишээ: fixed_carbon_ad)
    Энэ функц нь хөрвүүлэлт (ar/d/daf) хийхгүй; зөвхөн тухайн 'ad'
    суурь дээрх шууд параметрийг тооцно.
    """
    details = PARAMETER_DEFINITIONS.get(canonical_name)

    # Зөвхөн 'calculated' төрөлд ажиллана
    if not details or details.get("type") != "calculated":
        return None

    required = details.get("calculation_requires", [])
    if not required:
        return None

    # Оролтын утгуудыг шалгаж float болгох
    vals = {}
    try:
        for key in required:
            v = inputs_dict.get(key)
            if v is None:
                return None
            vals[key] = float(v)
    except (TypeError, ValueError):
        return None

    # --- Тооцооллууд ---
    if canonical_name == "fixed_carbon_ad":
        # FC,ad = 100 - (Ash_ad + V_ad + M_ad)
        return round(100.0 - (vals["ash"] + vals["volatile_matter"] + vals["inherent_moisture"]), 2)

    # Ирээдүйд өөр ad-суурьтай тооцооллуудыг энд нэмээрэй (elif ...)

    return None
