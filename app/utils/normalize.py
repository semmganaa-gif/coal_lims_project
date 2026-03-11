# app/utils/normalize.py
"""
Шинжилгээний raw_data нормчлолын модуль.

Янз бүрийн форматаар орж ирсэн raw_data-г стандарт формат руу хөрвүүлнэ:
{
    "p1": {"num": "...", "m1": ..., "m2": ..., "m3": ..., "result": ...},
    "p2": {...},
    "diff": ...,
    "avg": ...
}
"""
from __future__ import annotations
import json
from typing import Any, Dict, Optional

# Аль алинд нь ижил формат болгон буцаана:
# {
#   "p1": {"num": "...", "m1": ..., "m2": ..., "m3": ..., "result": ...},
#   "p2": {...},
#   "diff": ...,
#   "avg": ...
# }

# Нийтлэг alias-ууд
NUM_ALIASES = [
    "num", "box_no", "box_num", "box",
    "crucible_no", "crucible_num", "tigel_no", "tigel_num",
    "dish_num", "bottle_num", "bottle",  # ⬅️ TRD-д зориулж нэмсэн
    "can_no", "can_num", "tin_no", "tin_num",
    "tray_no", "pan_no",
]

M1_ALIASES = [
    # ерөнхий
    "m1",
    # MT, various tare names
    "m1_empty", "m1_box_empty", "empty_box", "box_tare", "tare", "m1_tare",
    # ⬅️ Фтор / Хлор / Фосфор зэрэгт ашиглах “масс” талбарууд
    "weight", "weight_g", "mass", "sample_weight",
]

M2_ALIASES = [
    "m2", "m2_sample", "m2_with_sample",
    "m",  # ⬅️ TRD-д зориулж нэмсэн: 'm' = нүүрсний жин
]

M3_ALIASES = [
    "m3",
    # бусад анализ
    "m3_ashy", "m3_dish_dry", "m3_residue",
    # MT хувилбарууд
    "m3_dried_box", "m3_dry", "after_dry", "m3_box_dry",
]

RESULT_ALIASES = ["result", "res", "value"]

# Нийтлэг нэг утгатай aliases (Solid гэх мэт)
COMMON_VALUE_ALIASES = {
    "A": ["A", "a", "mass_a", "total_mass", "gross_mass", "bucket_with_sample"],
    "B": ["B", "b", "mass_b", "tare_mass", "bucket_mass", "bucket_only"],
    "C": ["C", "c", "mass_c", "dry_mass", "residue_mass", "solid_mass"],
}


def _pick(d: Dict[str, Any], keys: list[str]) -> Optional[Any]:
    """Dict-ээс эхний олдсон утгыг буцаах."""
    for k in keys:
        if k in d and d[k] not in (None, ""):
            return d[k]
    return None


def _norm_parallel(raw: Dict[str, Any]) -> Dict[str, Any]:
    """Нэг зэрэгцээ (p1 эсвэл p2) өгөгдлийг нормчлох."""
    if not isinstance(raw, dict):
        return {}

    out = {
        "num": _pick(raw, NUM_ALIASES),
        "m1": _pick(raw, M1_ALIASES),
        "m2": _pick(raw, M2_ALIASES),
        "m3": _pick(raw, M3_ALIASES),
        "result": _pick(raw, RESULT_ALIASES),
    }

    # тоонуудад float хувиргалт (боломжтой бол)
    for k in ("m1", "m2", "m3", "result"):
        v = out.get(k)
        if isinstance(v, str):
            try:
                out[k] = float(v)
            except (ValueError, TypeError):
                pass

    # UI-д weight нэртэй талбарууд ч ашиглагддаг тул m1-г дутуу байвал weight болгон давхар хадгална
    if "m1" in out and "weight" not in out:
        out["weight"] = out["m1"]

    # хоосон утгуудыг хасна
    return {k: v for k, v in out.items() if v not in (None, "")}


def normalize_raw_data(raw_data: Any, analysis_code: str | None = None) -> Dict[str, Any]:
    """
    raw_data нь dict эсвэл JSON string байж болно.
    Ямар ч анализын хувьд p1/p2-г нэг стандарт руу буулгаж буцаана.
    """
    obj: Dict[str, Any] = {}

    if isinstance(raw_data, dict):
        obj = dict(raw_data)
    elif isinstance(raw_data, str):
        s = raw_data.strip()
        if s.startswith("{") and s.endswith("}"):
            try:
                obj = json.loads(s)
            except (json.JSONDecodeError, TypeError):
                obj = {}

    # p1/p2-г нормчлох
    p1 = obj.get("p1", {}) or {}
    p2 = obj.get("p2", {}) or {}

    norm_p1 = _norm_parallel(p1)
    norm_p2 = _norm_parallel(p2)

    out = {
        "p1": norm_p1,
        "p2": norm_p2,
    }

    parallels = []
    if norm_p1:
        parallels.append({"label": "p1", **norm_p1})
    if norm_p2:
        parallels.append({"label": "p2", **norm_p2})
    if parallels:
        out["parallels"] = parallels

    if analysis_code and analysis_code.upper() == "CSN":
        csn_row = {}
        rep_count = 0
        for idx in range(1, 6):
            key = f"v{idx}"
            val = obj.get(key)
            if val in (None, ""):
                continue
            try:
                val = float(val)
            except (ValueError, TypeError):
                pass
            csn_row[key] = val
            rep_count += 1
        if csn_row:
            out["parallels"] = [csn_row]
            out.setdefault("_schema", {})["csn_values"] = rep_count

    # diff/avg зэрэг нийлбэр утгууд
    if obj.get("diff") not in (None, ""):
        out["diff"] = obj.get("diff")
    if obj.get("avg") not in (None, ""):
        out["avg"] = obj.get("avg")

    for target, aliases in COMMON_VALUE_ALIASES.items():
        val = _pick_numeric(obj, aliases)
        if val not in (None, ""):
            out[target] = val

    # FM гэх мэт p1/p2 бүтэцгүй шинжилгээнүүдийн талбаруудыг хадгалах
    # Шууд top-level талбаруудыг хуулах (p1, p2, parallels, _schema-аас бусад)
    preserve_keys = [
        # FM талбарууд
        "tray_g", "before_g", "after_g", "loss_g", "loss",
        "wet_mass_g", "dry_mass_g", "fm_wet", "fm_dry",
        "fm_wet_pct", "fm_dry_pct", "fm_pct", "fm_pct_wet",
        "formula_wet", "formula_dry", "final_basis",
        # CV талбарууд
        "batch", "s_used", "E", "q1", "q2",
        # Repeatability талбарууд
        "repeatability", "t_exceeded", "t_band", "limit_used", "limit_mode",
        # SOLID талбарууд
        "solid_pct", "wet_mass", "formula",
        # Бусад
        "retest_mode", "is_low_avg",
    ]
    for key in preserve_keys:
        if key in obj and obj[key] not in (None, ""):
            out[key] = obj[key]

    # CV, TRD-ийн p1/p2 дотор m, delta_t хадгалах (normalize хийхгүй)
    # Original p1/p2 утгуудыг шууд хуулах
    orig_p1 = obj.get("p1", {}) or {}
    orig_p2 = obj.get("p2", {}) or {}

    # CV-ийн m, delta_t талбаруудыг хадгалах
    if "m" in orig_p1:
        out["p1"]["m"] = orig_p1["m"]
    if "delta_t" in orig_p1:
        out["p1"]["delta_t"] = orig_p1["delta_t"]
    if "m" in orig_p2:
        out["p2"]["m"] = orig_p2["m"]
    if "delta_t" in orig_p2:
        out["p2"]["delta_t"] = orig_p2["delta_t"]

    # TRD-ийн mad_used, temp_c, kt_used хадгалах
    if "mad_used" in obj:
        out["mad_used"] = obj["mad_used"]
    if "temp_c" in obj:
        out["temp_c"] = obj["temp_c"]
    if "kt_used" in obj:
        out["kt_used"] = obj["kt_used"]

    out["_schema"] = {
        "version": 1,
        "parallels_count": len(parallels),
        "has_parallels": bool(parallels),
    }

    return out


def _pick_numeric(d: Dict[str, Any], keys: list[str]) -> Optional[Any]:
    """Dict-ээс утга сонгож тоо руу хөрвүүлэх."""
    val = _pick(d, keys)
    if isinstance(val, str):
        try:
            return float(val)
        except (ValueError, TypeError):
            return val
    return val
