from pathlib import Path
import re

def patch_file(path, sub_old, sub_new):
    text = path.read_text(encoding="utf-8")
    if sub_old not in text:
        raise SystemExit("pattern not found")
    path.write_text(text.replace(sub_old, sub_new), encoding="utf-8")


helpers_path = Path("app/routes/api/helpers.py")

old_gi = """    # Gi: avg<18 ???? 3:3 ?????? ??? ?????? ??????? ?????? (pending_review)
    if analysis_code == "Gi":
        if (raw_norm or {}).get("is_low_avg", False):
            return True
        if (raw_norm or {}).get("retest_mode") == "3_3":
            return True
"""
new_gi = """    # Gi: 5:1 дээр <18 бол 3:3 руу шилжүүлнэ; 3:3 хийсний дараа diff хэтрээгүй бол review шаардлагагүй
    if analysis_code == "Gi":
        is_low = (raw_norm or {}).get("is_low_avg", False)
        retest = (raw_norm or {}).get("retest_mode")
        if is_low and retest != "3_3":
            return True
"""

old_limit = """    # (!!!) TRD, CV, CSN, Gi: JS-??? ????? 'limit_used'-? ??????????
    if analysis_code in ["CSN", "Gi", "CV", "TRD"] and "limit_used" in (raw_norm or {}):
        limit = _to_float_or_none(raw_norm.get("limit_used"))
        diff = _coalesce_diff(raw_norm)
        if diff is None or limit is None:
            return True  # ???????? ??? ????????
        return (abs(diff) - limit) > EPS
"""
new_limit = """    # (!!!) TRD, CV, CSN, Gi: JS-ээс ирсэн 'limit_used'-ыг шалгана
    if analysis_code in ["CSN", "Gi", "CV", "TRD"] and "limit_used" in (raw_norm or {}):
        limit = _to_float_or_none(raw_norm.get("limit_used"))
        diff = _coalesce_diff(raw_norm)
        if analysis_code == "CSN":
            # CSN: diff байхгүй бол 0, limit байхгүй бол 0 гэж үзнэ
            diff = diff if diff is not None else 0.0
            limit = limit if limit is not None else 0.0
        if diff is None or limit is None:
            return True  # мэдээлэл дутуу
        return (abs(diff) - limit) > EPS
"""

patch_file(helpers_path, old_gi, new_gi)
patch_file(helpers_path, old_limit, new_limit)
