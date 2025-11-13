# app/utils/normalize.py
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
    "dish_num", "bottle_num", "bottle", # ⬅️ (TRD-д зориулж нэмсэн)
    "can_no", "can_num", "tin_no", "tin_num",
    "tray_no", "pan_no"
]
M1_ALIASES = [
    # ерөнхий
    "m1",
    # MT, various tare names
    "m1_empty", "m1_box_empty", "empty_box", "box_tare", "tare", "m1_tare"
]
M2_ALIASES = [
    "m2", "m2_sample", "m2_with_sample",
    "m" # ⬅️ (TRD-д зориулж нэмсэн: 'm' = Нүүрсний жин)
]
M3_ALIASES = [
    "m3",
    # бусад анализ
    "m3_ashy", "m3_dish_dry", "m3_residue",
    # MT хувилбарууд
    "m3_dried_box", "m3_dry", "after_dry", "m3_box_dry"
]
RESULT_ALIASES = ["result", "res", "value"]

def _pick(d: Dict[str, Any], keys: list[str]) -> Optional[Any]:
    for k in keys:
        if k in d and d[k] not in (None, ""):
            return d[k]
    return None

def _norm_parallel(raw: Dict[str, Any]) -> Dict[str, Any]:
    if not isinstance(raw, dict):
        return {}
    out = {
        "num": _pick(raw, NUM_ALIASES),
        "m1":  _pick(raw, M1_ALIASES),
        "m2":  _pick(raw, M2_ALIASES),
        "m3":  _pick(raw, M3_ALIASES),
        "result": _pick(raw, RESULT_ALIASES),
    }
    # тоонуудад float хувиргалт (боломжтой бол)
    for k in ("m1", "m2", "m3", "result"):
        v = out.get(k)
        if isinstance(v, str):
            try:
                out[k] = float(v)
            except Exception:
                pass
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
            except Exception:
                obj = {}
    # p1/p2-г нормчлох
    p1 = obj.get("p1", {}) or {}
    p2 = obj.get("p2", {}) or {}
    out = {
        "p1": _norm_parallel(p1),
        "p2": _norm_parallel(p2),
    }
    # diff/avg зэрэг нийлбэр утгууд
    if obj.get("diff") not in (None, ""):
        out["diff"] = obj.get("diff")
    if obj.get("avg") not in (None, ""):
        out["avg"] = obj.get("avg")
    return out