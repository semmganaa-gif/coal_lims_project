# -*- coding: utf-8 -*-
"""
Analysis Business Rules
-----------------------
Энэ модуль нь шинжилгээний үр дүнгийн статусыг тодорхойлох логикийг агуулна.
Validators.py нь "Hard Limit" (Алдаа) шалгадаг бол,
Rules.py нь "Soft Limit" (Анхааруулга/Pending) шалгана.
"""

from typing import Optional, Tuple, Dict, Any

# ============================================================================
# 1. SOFT LIMITS (УЯН ХАТАН ХЯЗГААР - MAX VALUE)
# ============================================================================
SOFT_LIMITS: Dict[str, float] = {
    # --- Чийг (Moisture) ---
    'MT': 35.0,         # Нийт чийг 35%-иас их бол шалгах
    'Mad': 15.0,        # Агаарын чийг 15%-иас их бол шалгах

    # --- Үнс (Ash) ---
    'Aad': 90.0,        # Үнс 50%-иас их бол (Hard limit нь 100% байгаа)
    'A': 90.0,

    # --- Дэгдэмхий (Volatile) ---
    'Vad': 90.0,
    'V': 90.0,
    'Vdaf': 95.0,       # Vdaf 60%-иас их бол сэжигтэй

    # --- Хүхэр (Sulfur) ---
    'TS': 20.0,          # Нийт хүхэр 5%-иас их бол
    'St,ad': 20.0,
    'St,d': 20.0,

    # --- Химийн элементүүд (Elements) ---
    'N': 3.0,           # Азот
    'O': 25.0,          # Хүчилтөрөгч (өндөр байвал исэлдсэн байж болно)

    # --- Хорт хольцууд (Trace Elements) ---
    'P': 0.250,
    'P,ad': 0.250,
    'P,d': 0.250,

    # Cl, F - ppm нэгжтэй (MNS 7057:2024, MNS GB/T 4633:2024)
    'Cl': 600.0,         # Cl 600 ppm хүртэл хэвийн
    'Cl,ad': 600.0,
    'Cl,d': 600.0,

    'F': 500.0,          # F 500 ppm хүртэл хэвийн
    'F,ad': 500.0,
    'F,d': 500.0,

    # --- Коксын шинж чанар (Caking & Coke) ---
    'CRI': 60.0,

    # --- Бусад ---
    'SOLID': 80.0,      # Solid residue (Vad-тай холбоотой)
    'FM': 60.0,
    'TRD': 3.00,       # Relative Density хэт өндөр байвал шалгах
}
# Keep max limits aligned with soft limits by default.
SOFT_MAX_LIMITS: Dict[str, float] = SOFT_LIMITS.copy()

# ============================================================================
# 2. SOFT MIN LIMITS (ДООД ХЯЗГААР)
# ============================================================================
SOFT_MIN_LIMITS: Dict[str, float] = {
    # --- Илчлэг (Calorific Value) ---
    'CV': 1000.0,
    'Qgr,ad': 1000.0,
    'Qnet,ar': 1000.0,

    # --- Коксын бат бэх ---
    'CSR': 20.0,

    'Mad': 0.40,      # Inherent moisture - доод хязгаар
}


def determine_result_status(
    analysis_code: str,
    value: float,
    raw_data: Optional[Dict[str, Any]] = None,
    control_targets: Optional[Dict[str, Any]] = None
) -> Tuple[str, Optional[str]]:
    """
    Шинжилгээний үр дүнгээс хамаарч статус болон тайлбарыг тодорхойлох функц.
    Бүх төрлийн шинжилгээний кодыг дэмжинэ.

    Returns:
        Tuple[str, str]: (status, rejection_comment)
            - status: 'approved' | 'pending_review' | 'rejected'
            - rejection_comment: Тайлбар
    """

    if raw_data is None:
        raw_data = {}

    # ========================================================================
    # 0. TOLERANCE CHECK (ТОХИРЦЫН ЗӨРҮҮ) - БҮХ ДЭЭЖИНД ШАЛГАНА
    # ========================================================================
    # Энэ шалгалт нь control sample болон жирийн дээж аль алинд нь хамаарна
    if raw_data.get("t_exceeded", False):
        return "pending_review", "Tolerance Exceeded (Стандарт тохирц зөрүүтэй)"

    # ========================================================================
    # 1. CONTROL SAMPLE CHECK (ХЯНАЛТЫН ДЭЭЖНИЙ ШАЛГАЛТ)
    # ========================================================================
    # ✅ ТАНЫ ХУУЧИН КОД ДЭЭР ЭНЭ ХЭСЭГ ДУТУУ БАЙСАН!

    if control_targets:
        mean = control_targets.get("mean")
        sd = control_targets.get("sd")

        # Хэрэв Mean, SD хоёулаа байвал тооцоолол хийнэ
        if mean is not None and sd is not None:
            # Зөрүүг олох (absolute difference)
            diff = abs(value - mean)

            # Дүрэм А: Action Limit (2SD) -> REJECTED (Улаан)
            # Танай лабораторийн дүрмээр 2SD-ээс их бол шууд Алдаа
            if diff > (2 * sd):
                return "rejected", f"Control Failure: > 2SD (Mean: {mean}, SD: {sd}, Diff: {diff:.4f})"

            # Дүрэм Б: Warning Limit (1SD) -> PENDING REVIEW (Шар)
            # 1SD-ээс их бол Анхааруулга
            if diff > (1 * sd):
                return "pending_review", f"Control Warning: > 1SD (Mean: {mean}, SD: {sd}, Diff: {diff:.4f})"

            # Дүрэм В: Success (1SD дотор) -> APPROVED (Ногоон)
            return "approved", "Control Pass"

    # ========================================================================
    # 2. BUSINESS LOGIC RULES (Тусгай дүрмүүд - Жирийн дээжинд)
    # ========================================================================

    # ДҮРЭМ: Gi (Gray-King) индекс
    # Хэрэв Gi-ийн дундаж хэт бага (is_low_avg) байвал шууд REJECT
    if analysis_code == 'Gi':
        if raw_data.get("is_low_avg", False):
            return "rejected", "GI_RETEST_3_3"

    # ДҮРЭМ: CSN (Crucible Swelling Number) - MNS ISO 501
    # CSN утга 0-9 хооронд байх ёстой (0, 0.5, 1, 1.5, ..., 9)
    if analysis_code == 'CSN':
        # A. Хүчинтэй утга шалгах (0-9)
        if value is not None:
            if value < 0 or value > 9:
                return "rejected", f"CSN утга хүчингүй ({value}). 0-9 байх ёстой."

        # B. Parallel зөрүү шалгах (хэрэв raw_data-д байвал)
        p1_csn = raw_data.get("p1_csn") or raw_data.get("p1", {}).get("csn")
        p2_csn = raw_data.get("p2_csn") or raw_data.get("p2", {}).get("csn")

        if p1_csn is not None and p2_csn is not None:
            try:
                p1_val = float(p1_csn)
                p2_val = float(p2_csn)
                csn_diff = abs(p1_val - p2_val)

                # MNS ISO 501: 2 дээжийн зөрүү 1-ээс их байвал давтах
                if csn_diff > 1.0:
                    return "pending_review", f"CSN parallel зөрүү хэтэрсэн ({csn_diff} > 1.0)"

                # Хэрэв зөрүү нь яг 1 бол анхааруулга
                if csn_diff == 1.0:
                    return "pending_review", f"CSN parallel зөрүү хязгаарт ({csn_diff} = 1.0)"

            except (ValueError, TypeError):
                pass  # Тоо биш бол алгасна

        # C. Хэрэв CSN = 0 бол coking coal биш гэсэн үг (мэдээлэл)
        if value == 0:
            # Зөвшөөрнө гэхдээ тайлбар нэмнэ
            pass  # approved болно, тайлбаргүй

    # ДҮРЭМ: CSR (Coke Strength after Reaction)
    if analysis_code == 'CSR' and value is not None:
        if value < 20.0:
            return "pending_review", f"CSR хэт бага ({value} < 20.0)"

    # ДҮРЭМ: CV (Calorific Value)
    if analysis_code in ['CV', 'Qgr,ad', 'Qnet,ar'] and value is not None:
        if value < 2000:
            return "pending_review", f"Илчлэг хэт бага ({value})"

    # ========================================================================
    # 3. SOFT LIMIT CHECK (Max Value Check - Жирийн дээжинд)
    # ========================================================================

    if value is not None:
        # A. MAX Limit Check (Дээд хязгаар)
        max_limit = SOFT_MAX_LIMITS.get(analysis_code)
        if max_limit is not None and value > max_limit:
            return "pending_review", f"Soft Limit Exceeded ({analysis_code} > {max_limit})"

        # B. MIN Limit Check (Доод хязгаар)
        min_limit = SOFT_MIN_LIMITS.get(analysis_code)
        if min_limit is not None and value < min_limit:
            return "pending_review", f"Soft Limit Exceeded ({analysis_code} < {min_limit})"

    # ========================================================================
    # 4. DEFAULT (Зөвшөөрөх)
    # ========================================================================

    return "approved", None
