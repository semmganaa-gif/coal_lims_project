# app/services/qc_chart_service.py
# -*- coding: utf-8 -*-
"""
QC Control Chart service — capability indices, trend analysis, export.

ISO 17025 Clause 7.7.1 compliant statistical process control.
"""

import math
import statistics
from dataclasses import dataclass
from typing import Optional

from sqlalchemy import and_

from app.bootstrap.extensions import db
from app.models.core import Sample
from app.models.analysis import AnalysisResult
from app.utils.datetime import now_local
from app.utils.transaction import transactional


@dataclass
class CapabilityIndices:
    """Process capability indices (Cp, Cpk, %RSD)."""
    cp: Optional[float] = None       # Process capability
    cpk: Optional[float] = None      # Process capability (centered)
    rsd_percent: Optional[float] = None  # Relative standard deviation %
    mean: Optional[float] = None
    sd: Optional[float] = None
    n: int = 0
    bias: Optional[float] = None     # Mean - Target
    bias_percent: Optional[float] = None


def calculate_capability(values: list[float], target: float,
                         sd_ref: float, ucl: float, lcl: float) -> CapabilityIndices:
    """
    Calculate process capability indices.

    Cp  = (UCL - LCL) / (6 * sd_observed)
    Cpk = min((UCL - mean) / (3*sd), (mean - LCL) / (3*sd))
    %RSD = (sd / mean) * 100
    """
    if len(values) < 2:
        return CapabilityIndices(n=len(values))

    mean = statistics.mean(values)
    sd = statistics.stdev(values)
    n = len(values)

    result = CapabilityIndices(mean=round(mean, 4), sd=round(sd, 4), n=n)

    if sd > 0:
        result.cp = round((ucl - lcl) / (6 * sd), 3)
        cpu = (ucl - mean) / (3 * sd)
        cpl = (mean - lcl) / (3 * sd)
        result.cpk = round(min(cpu, cpl), 3)

    if mean != 0:
        result.rsd_percent = round((sd / abs(mean)) * 100, 2)

    result.bias = round(mean - target, 4)
    if target != 0:
        result.bias_percent = round(((mean - target) / target) * 100, 2)

    return result


def calculate_moving_average(values: list[float], window: int = 5) -> list[Optional[float]]:
    """Calculate simple moving average."""
    if len(values) < window:
        return [None] * len(values)

    result = [None] * (window - 1)
    for i in range(window - 1, len(values)):
        avg = statistics.mean(values[i - window + 1:i + 1])
        result.append(round(avg, 4))
    return result


def calculate_cusum(values: list[float], target: float,
                    k: float = 0.5, h: float = 5.0,
                    sd: float = 1.0) -> dict:
    """
    Calculate CUSUM (Cumulative Sum) chart data.

    Args:
        values: measurement values
        target: target/reference value
        k: allowance (slack) value in SD units (default 0.5)
        h: decision interval in SD units (default 5.0)
        sd: standard deviation

    Returns:
        dict with cusum_pos, cusum_neg, h_upper, h_lower, signals
    """
    if not values or sd <= 0:
        return {"cusum_pos": [], "cusum_neg": [], "signals": []}

    K = k * sd
    H = h * sd

    cusum_pos = []
    cusum_neg = []
    signals = []

    sp = 0.0  # Positive CUSUM
    sn = 0.0  # Negative CUSUM

    for i, val in enumerate(values):
        sp = max(0, sp + (val - target) - K)
        sn = max(0, sn - (val - target) - K)

        cusum_pos.append(round(sp, 4))
        cusum_neg.append(round(-sn, 4))

        if sp > H:
            signals.append({"index": i, "type": "upper", "value": round(sp, 4)})
        if sn > H:
            signals.append({"index": i, "type": "lower", "value": round(-sn, 4)})

    return {
        "cusum_pos": cusum_pos,
        "cusum_neg": cusum_neg,
        "h_upper": round(H, 4),
        "h_lower": round(-H, 4),
        "signals": signals,
    }


def calculate_ewma(values: list[float], target: float,
                   lam: float = 0.2, sd: float = 1.0,
                   L: float = 3.0) -> dict:
    """
    Calculate EWMA (Exponentially Weighted Moving Average) chart data.

    Args:
        values: measurement values
        target: target value
        lam: smoothing parameter (0 < lambda <= 1, default 0.2)
        sd: standard deviation
        L: width of control limits in sigma units (default 3.0)
    """
    if not values or sd <= 0:
        return {"ewma": [], "ucl": [], "lcl": []}

    ewma_vals = []
    ucl_vals = []
    lcl_vals = []

    z = target  # Initial EWMA = target

    for i, val in enumerate(values):
        z = lam * val + (1 - lam) * z
        ewma_vals.append(round(z, 4))

        # Time-varying control limits
        n = i + 1
        factor = math.sqrt(lam / (2 - lam) * (1 - (1 - lam) ** (2 * n)))
        ucl_vals.append(round(target + L * sd * factor, 4))
        lcl_vals.append(round(target - L * sd * factor, 4))

    return {
        "ewma": ewma_vals,
        "ucl": ucl_vals,
        "lcl": lcl_vals,
        "target": round(target, 4),
    }


def export_chart_data(data_points: list[dict], analysis_code: str,
                      standard_name: str, target: float,
                      sd: float, format: str = "csv") -> str:
    """
    Export chart data as CSV string.

    Args:
        data_points: list of {value, date, sample_code, operator}
        format: "csv" or "json"
    """
    if format == "json":
        import json
        return json.dumps({
            "standard_name": standard_name,
            "analysis_code": analysis_code,
            "target": target,
            "sd": sd,
            "ucl": round(target + 2 * sd, 4),
            "lcl": round(target - 2 * sd, 4),
            "data_points": data_points,
        }, ensure_ascii=False, indent=2)

    # CSV format
    lines = [
        f"# QC Control Chart: {standard_name} - {analysis_code}",
        f"# Target: {target}, SD: {sd}, UCL: {target + 2*sd:.4f}, LCL: {target - 2*sd:.4f}",
        "Date,Sample Code,Value,Z-Score,Status,Operator"
    ]

    for p in data_points:
        val = p.get("value", 0)
        z = (val - target) / sd if sd > 0 else 0
        status = "REJECT" if abs(z) > 3 else "WARNING" if abs(z) > 2 else "OK"
        lines.append(
            f"{p.get('date', '')},{p.get('sample_code', '')},"
            f"{val:.4f},{z:.3f},{status},{p.get('operator', '')}"
        )

    return "\n".join(lines)


@transactional()
def create_corrective_action_from_violation(
    standard_name: str,
    analysis_code: str,
    violations: list,
    user_id: int
) -> Optional[int]:
    """
    Auto-create a Corrective Action record when Westgard reject is triggered.

    Returns: CorrectiveAction.id or None
    """
    from app.models.quality_records import CorrectiveAction

    reject_violations = [v for v in violations if v.get("severity") == "reject"]
    if not reject_violations:
        return None

    # Generate CA number
    from sqlalchemy import func
    max_ca = db.session.query(func.max(CorrectiveAction.ca_number)).scalar()
    year = now_local().year
    if max_ca and max_ca.startswith(f"CA-{year}-"):
        try:
            seq = int(max_ca.split("-")[-1]) + 1
        except ValueError:
            seq = 1
    else:
        seq = 1
    ca_number = f"CA-{year}-{seq:03d}"

    # Build description
    rules = ", ".join(v["rule"] for v in reject_violations)
    desc = (
        f"Westgard QC REJECT — {standard_name} / {analysis_code}\n"
        f"Зөрчигдсөн дүрмүүд: {rules}\n"
        f"Автоматаар үүсгэсэн (QC Control Chart)"
    )

    ca = CorrectiveAction(
        ca_number=ca_number,
        issue_date=now_local().date(),
        issue_source="QC Control Chart",
        issue_description=desc,
        severity="Major",
        responsible_person_id=user_id,
    )
    db.session.add(ca)
    return ca.id
