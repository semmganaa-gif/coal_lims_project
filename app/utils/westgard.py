# app/utils/westgard.py
# -*- coding: utf-8 -*-
"""
Westgard Rules - QC автоматжуулалт

ISO 17025 дагуу лабораторийн чанарын хяналт (QC) дүрмүүд.
https://www.westgard.com/mltirule.htm

Дүрмүүд:
- 1:2s  - Нэг утга ±2SD-ээс хэтэрсэн (анхааруулга)
- 1:3s  - Нэг утга ±3SD-ээс хэтэрсэн (REJECT)
- 2:2s  - Хоёр дараалсан утга нэг талын 2SD-ээс хэтэрсэн (REJECT)
- R:4s  - Хоёр дараалсан утгын зөрүү 4SD-ээс их (REJECT)
- 4:1s  - 4 дараалсан утга нэг талын 1SD-ээс хэтэрсэн (REJECT)
- 10x   - 10 дараалсан утга дунджийн нэг талд (REJECT)
"""

from typing import List, Dict, Optional
from dataclasses import dataclass


@dataclass
class WestgardViolation:
    """Westgard дүрмийн зөрчил"""
    rule: str          # Дүрмийн нэр (e.g., "1:3s")
    description: str   # Тайлбар
    severity: str      # "warning" or "reject"
    values: List[float]  # Зөрчил гаргасан утгууд
    indices: List[int]   # Индексүүд


def check_westgard_rules(
    values: List[float],
    mean: float,
    sd: float
) -> List[WestgardViolation]:
    """
    Westgard дүрмүүдийг шалгах

    Args:
        values: Хэмжилтийн утгууд (хамгийн сүүлийнх нь эхэнд)
        mean: Дундаж (target value)
        sd: Стандарт хазайлт

    Returns:
        Зөрчлүүдийн жагсаалт
    """
    if not values or sd <= 0:
        return []

    violations = []

    # Утгуудыг z-score болгох
    z_scores = [(v - mean) / sd for v in values]

    # ================================================================
    # 1:3s - Нэг утга ±3SD-ээс хэтэрсэн (REJECT)
    # ================================================================
    for i, z in enumerate(z_scores):
        if abs(z) > 3:
            violations.append(WestgardViolation(
                rule="1:3s",
                description=f"Утга ({values[i]:.3f}) нь ±3SD хязгаараас хэтэрсэн",
                severity="reject",
                values=[values[i]],
                indices=[i]
            ))

    # ================================================================
    # 1:2s - Нэг утга ±2SD-ээс хэтэрсэн (анхааруулга)
    # ================================================================
    for i, z in enumerate(z_scores):
        if abs(z) > 2 and abs(z) <= 3:
            violations.append(WestgardViolation(
                rule="1:2s",
                description=f"Утга ({values[i]:.3f}) нь ±2SD хязгаараас хэтэрсэн",
                severity="warning",
                values=[values[i]],
                indices=[i]
            ))

    # ================================================================
    # 2:2s - 2 дараалсан утга нэг талын 2SD-ээс хэтэрсэн (REJECT)
    # ================================================================
    if len(z_scores) >= 2:
        for i in range(len(z_scores) - 1):
            z1, z2 = z_scores[i], z_scores[i + 1]
            # Хоёулаа 2SD-ээс их, нэг чиглэлд
            if (z1 > 2 and z2 > 2) or (z1 < -2 and z2 < -2):
                violations.append(WestgardViolation(
                    rule="2:2s",
                    description="2 дараалсан утга нэг талын 2SD-ээс хэтэрсэн",
                    severity="reject",
                    values=[values[i], values[i + 1]],
                    indices=[i, i + 1]
                ))
                break  # Зөвхөн нэг удаа тайлагнах

    # ================================================================
    # R:4s - 2 дараалсан утгын зөрүү 4SD-ээс их (REJECT)
    # ================================================================
    if len(z_scores) >= 2:
        for i in range(len(z_scores) - 1):
            range_z = abs(z_scores[i] - z_scores[i + 1])
            if range_z > 4:
                violations.append(WestgardViolation(
                    rule="R:4s",
                    description=f"2 утгын зөрүү ({abs(values[i] - values[i+1]):.3f}) нь 4SD-ээс их",
                    severity="reject",
                    values=[values[i], values[i + 1]],
                    indices=[i, i + 1]
                ))
                break

    # ================================================================
    # 4:1s - 4 дараалсан утга нэг талын 1SD-ээс хэтэрсэн (REJECT)
    # ================================================================
    if len(z_scores) >= 4:
        for i in range(len(z_scores) - 3):
            window = z_scores[i:i + 4]
            # Бүгд 1SD-ээс их, нэг чиглэлд
            if all(z > 1 for z in window) or all(z < -1 for z in window):
                violations.append(WestgardViolation(
                    rule="4:1s",
                    description="4 дараалсан утга нэг талын 1SD-ээс хэтэрсэн",
                    severity="reject",
                    values=values[i:i + 4],
                    indices=list(range(i, i + 4))
                ))
                break

    # ================================================================
    # 10x - 10 дараалсан утга дунджийн нэг талд (REJECT)
    # ================================================================
    if len(z_scores) >= 10:
        for i in range(len(z_scores) - 9):
            window = z_scores[i:i + 10]
            # Бүгд 0-ээс их эсвэл бага
            if all(z > 0 for z in window) or all(z < 0 for z in window):
                violations.append(WestgardViolation(
                    rule="10x",
                    description="10 дараалсан утга дунджийн нэг талд",
                    severity="reject",
                    values=values[i:i + 10],
                    indices=list(range(i, i + 10))
                ))
                break

    return violations


def get_qc_status(violations: List[WestgardViolation]) -> Dict:
    """
    QC статус тодорхойлох

    Returns:
        {
            "status": "pass" | "warning" | "reject",
            "rules_violated": ["1:2s", ...],
            "message": "..."
        }
    """
    if not violations:
        return {
            "status": "pass",
            "rules_violated": [],
            "message": "Бүх Westgard дүрмүүд хэвийн"
        }

    has_reject = any(v.severity == "reject" for v in violations)
    rules = list(set(v.rule for v in violations))

    if has_reject:
        return {
            "status": "reject",
            "rules_violated": rules,
            "message": f"QC REJECT: {', '.join(rules)} дүрэм зөрчигдсөн"
        }
    else:
        return {
            "status": "warning",
            "rules_violated": rules,
            "message": f"QC Анхааруулга: {', '.join(rules)}"
        }


def check_single_value(
    value: float,
    mean: float,
    sd: float
) -> Dict:
    """
    Нэг утгын хурдан шалгалт

    Returns:
        {
            "z_score": float,
            "in_1sd": bool,
            "in_2sd": bool,
            "in_3sd": bool,
            "status": "ok" | "warning" | "reject"
        }
    """
    if sd <= 0:
        return {"error": "SD must be positive"}

    z = (value - mean) / sd
    abs_z = abs(z)

    status = "ok"
    if abs_z > 3:
        status = "reject"
    elif abs_z > 2:
        status = "warning"

    return {
        "value": value,
        "z_score": round(z, 3),
        "deviation": round(value - mean, 4),
        "in_1sd": abs_z <= 1,
        "in_2sd": abs_z <= 2,
        "in_3sd": abs_z <= 3,
        "status": status
    }
