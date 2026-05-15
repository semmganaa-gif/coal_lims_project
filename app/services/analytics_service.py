# app/services/analytics_service.py
# -*- coding: utf-8 -*-
"""
AI-Powered Analytics Service — LIMS Intelligence Layer.

Дэвшилтэт шинжилгээ:
  - Anomaly detection (Z-score + IQR + historical comparison)
  - Linear regression trend analysis
  - Quality Health Score (0-100)
  - Natural language insight generation (Mongolian + English)
  - Shift performance comparison
  - Predictive alerts
"""

import math
import statistics
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy import and_, func, desc, select
from flask_babel import lazy_gettext as _l

from app.bootstrap.extensions import db
from app.constants import AnalysisResultStatus
from app.models.core import Sample
from app.models.analysis import AnalysisResult
from app.utils.datetime import now_local


# ─── ANALYSIS SPEC (нүүрсний шинжилгээний хэвийн хүрээ) ─────────
ANALYSIS_SPECS = {
    "Mad":   {"name": _l("Чийг (Mad)"),        "unit": "%", "warn_low": 1.0, "warn_high": 12.0, "crit_low": 0.5, "crit_high": 15.0},
    "Aad":   {"name": _l("Үнслэг (Aad)"),      "unit": "%", "warn_low": 5.0, "warn_high": 35.0, "crit_low": 3.0, "crit_high": 45.0},
    "Vdaf":  {"name": _l("Дэгдэмхий (Vdaf)"),  "unit": "%", "warn_low": 20.0, "warn_high": 45.0, "crit_low": 15.0, "crit_high": 50.0},
    "FCd":   {"name": _l("Тогтмол нүүрс"),     "unit": "%", "warn_low": 30.0, "warn_high": 70.0, "crit_low": 25.0, "crit_high": 80.0},
    "St,d":  {"name": _l("Хүхэр (St,d)"),      "unit": "%", "warn_low": 0.1, "warn_high": 3.0,  "crit_low": 0.0, "crit_high": 5.0},
    "Qgr,ad": {"name": _l("Илчлэг (Qgr,ad)"), "unit": "kcal/kg", "warn_low": 3000, "warn_high": 7500, "crit_low": 2000, "crit_high": 8000},
    "CSN":   {"name": _l("Найрлага тоо"),      "unit": "", "warn_low": 0, "warn_high": 9, "crit_low": 0, "crit_high": 9},
    "GI":    {"name": _l("Шаталт индекс"),     "unit": "", "warn_low": 0, "warn_high": 100, "crit_low": 0, "crit_high": 250},
    "MT":    {"name": _l("Нийт чийг (Mt)"),     "unit": "%", "warn_low": 2.0, "warn_high": 15.0, "crit_low": 1.0, "crit_high": 20.0},
}


# ─── DATA CLASSES ───────────────────────────────────────────────

@dataclass
class Anomaly:
    """Нэг аномали илрэл."""
    sample_code: str
    analysis_code: str
    value: float
    z_score: float
    historical_mean: float
    historical_sd: float
    severity: str          # "warning" | "critical"
    message: str
    recommendation: str


@dataclass
class TrendResult:
    """Чиг хандлагын шинжилгээний үр дүн."""
    analysis_code: str
    direction: str         # "increasing" | "decreasing" | "stable"
    slope: float           # Хэвтээ тэнхлэгийн налуу
    r_squared: float       # Детерминацийн коэффициент (0-1)
    change_pct: float      # Хувиар өөрчлөлт
    confidence: str        # "high" | "medium" | "low"
    message: str
    recent_mean: float
    historical_mean: float


@dataclass
class ShiftComparison:
    """Ээлжүүдийн харьцуулалт."""
    shift: str             # "day" | "night"
    mean: float
    sd: float
    count: int
    anomaly_rate: float    # Аномали хувь


@dataclass
class QualityScore:
    """Чанарын нийт оноо."""
    score: int             # 0-100
    grade: str             # "A+" | "A" | "B" | "C" | "D" | "F"
    color: str             # "#22c55e" | "#f59e0b" | "#ef4444"
    breakdown: dict        # Нарийвчилсан задаргаа
    message: str


@dataclass
class AnalyticsReport:
    """Бүрэн AI analytics тайлан."""
    timestamp: str
    period: str
    quality_score: QualityScore
    anomalies: list
    trends: list
    insights: list
    shift_comparison: dict
    sample_count: int
    analysis_count: int


# ─── CORE ANALYTICS ─────────────────────────────────────────────

def get_historical_stats(analysis_code: str, days: int = 90,
                         client_name: str = None) -> dict:
    """
    Тухайн шинжилгээний түүхэн статистик авах.

    Returns:
        {"mean": float, "sd": float, "median": float, "q1": float,
         "q3": float, "iqr": float, "count": int, "values": list}
    """
    cutoff = now_local() - timedelta(days=days)

    query = db.session.query(AnalysisResult.final_result).join(
        Sample, AnalysisResult.sample_id == Sample.id
    ).filter(
        AnalysisResult.analysis_code == analysis_code,
        AnalysisResult.final_result.isnot(None),
        AnalysisResult.status == AnalysisResultStatus.APPROVED.value,
        Sample.received_date >= cutoff,
    )

    if client_name:
        query = query.filter(Sample.client_name == client_name)

    rows = query.order_by(desc(Sample.received_date)).limit(500).all()
    values = [float(r[0]) for r in rows if r[0] is not None]

    if len(values) < 3:
        return {"mean": None, "sd": None, "count": len(values), "values": values}

    mean = statistics.mean(values)
    sd = statistics.stdev(values)
    sorted_vals = sorted(values)
    n = len(sorted_vals)
    q1 = sorted_vals[n // 4]
    q3 = sorted_vals[3 * n // 4]
    median = statistics.median(values)

    return {
        "mean": round(mean, 4),
        "sd": round(sd, 4),
        "median": round(median, 4),
        "q1": round(q1, 4),
        "q3": round(q3, 4),
        "iqr": round(q3 - q1, 4),
        "count": n,
        "min": round(min(values), 4),
        "max": round(max(values), 4),
        "values": values,
    }


def detect_anomalies(samples: list, lookback_days: int = 90) -> list[Anomaly]:
    """
    Дээжүүдийн шинжилгээний үр дүнг түүхэн хуваарилалттай харьцуулж
    аномалиуд илрүүлэх.

    Аргачлал:
      1. Z-score (|z| > 2 warning, |z| > 3 critical)
      2. IQR fence (< Q1-1.5*IQR эсвэл > Q3+1.5*IQR)
      3. Spec limit шалгалт
    """
    anomalies = []
    stats_cache = {}

    for sample in samples:
        results = list(db.session.execute(
            select(AnalysisResult).where(AnalysisResult.sample_id == sample.id)
        ).scalars().all())

        for result in results:
            if result.final_result is None:
                continue

            code = result.analysis_code
            val = float(result.final_result)

            # Түүхэн статистик (cache)
            cache_key = f"{code}_{sample.client_name or 'all'}"
            if cache_key not in stats_cache:
                stats_cache[cache_key] = get_historical_stats(
                    code, lookback_days, sample.client_name
                )
            stats = stats_cache[cache_key]

            if stats["mean"] is None or stats["sd"] is None or stats["sd"] == 0:
                # Spec-based шалгалт
                spec = ANALYSIS_SPECS.get(code)
                if spec and (val < spec["crit_low"] or val > spec["crit_high"]):
                    anomalies.append(Anomaly(
                        sample_code=sample.sample_code,
                        analysis_code=code,
                        value=val,
                        z_score=0,
                        historical_mean=0,
                        historical_sd=0,
                        severity="critical",
                        message=f"{spec['name']}: {val}{spec['unit']} — "
                                f"зөвшөөрөгдөх хүрээнээс ({spec['crit_low']}-{spec['crit_high']}) гадна",
                        recommendation=_l("Дахин шинжилгээ хийх, дээж чанар шалгах"),
                    ))
                continue

            # Z-score
            z = (val - stats["mean"]) / stats["sd"]

            # IQR fence
            iqr = stats.get("iqr", 0)
            q1 = stats.get("q1", stats["mean"])
            q3 = stats.get("q3", stats["mean"])
            iqr_lower = q1 - 1.5 * iqr
            iqr_upper = q3 + 1.5 * iqr
            is_iqr_outlier = val < iqr_lower or val > iqr_upper

            severity = None
            if abs(z) > 3 or (is_iqr_outlier and abs(z) > 2):
                severity = "critical"
            elif abs(z) > 2:
                severity = "warning"

            if severity:
                spec = ANALYSIS_SPECS.get(code, {})
                name = spec.get("name", code)
                unit = spec.get("unit", "")

                direction = _l("өндөр") if z > 0 else _l("бага")
                recommendation = _get_recommendation(code, z, val, stats)

                anomalies.append(Anomaly(
                    sample_code=sample.sample_code,
                    analysis_code=code,
                    value=round(val, 3),
                    z_score=round(z, 2),
                    historical_mean=stats["mean"],
                    historical_sd=stats["sd"],
                    severity=severity,
                    message=f"{name}: {val:.3f}{unit} — дундажнаас {direction} "
                            f"(z={z:.1f}, дундаж={stats['mean']:.3f}±{stats['sd']:.3f})",
                    recommendation=recommendation,
                ))

    # Severity, z-score-аар эрэмбэлэх
    anomalies.sort(key=lambda a: (0 if a.severity == "critical" else 1, -abs(a.z_score)))
    return anomalies


def analyze_trends(analysis_code: str, days: int = 30,
                   client_name: str = None) -> TrendResult:
    """
    Шинжилгээний үр дүнгийн чиг хандлагыг шугаман регрессээр тодорхойлох.

    Аргачлал:
      - Simple linear regression (least squares)
      - R² (determinant) тооцоолол
      - Slope direction + magnitude → direction + confidence
    """
    cutoff = now_local() - timedelta(days=days)

    rows = db.session.query(
        Sample.received_date,
        AnalysisResult.final_result,
    ).join(
        AnalysisResult, AnalysisResult.sample_id == Sample.id
    ).filter(
        AnalysisResult.analysis_code == analysis_code,
        AnalysisResult.final_result.isnot(None),
        AnalysisResult.status == AnalysisResultStatus.APPROVED.value,
        Sample.received_date >= cutoff,
    )

    if client_name:
        rows = rows.filter(Sample.client_name == client_name)

    rows = rows.order_by(Sample.received_date.asc()).all()

    if len(rows) < 5:
        return TrendResult(
            analysis_code=analysis_code,
            direction="stable",
            slope=0, r_squared=0, change_pct=0,
            confidence="low",
            message=_l("Хангалттай өгөгдөл байхгүй (< 5 бичлэг)"),
            recent_mean=0, historical_mean=0,
        )

    # X = day index (0, 1, 2, ...), Y = values
    base_date = rows[0][0]
    xs = [(r[0] - base_date).total_seconds() / 86400 for r in rows]
    ys = [float(r[1]) for r in rows]

    # Simple linear regression
    slope, intercept, r_sq = _linear_regression(xs, ys)

    # Split: recent (last 25%) vs earlier (first 75%)
    split = max(1, len(ys) * 3 // 4)
    historical_mean = statistics.mean(ys[:split])
    recent_mean = statistics.mean(ys[split:])

    # Change %
    change_pct = 0
    if historical_mean != 0:
        change_pct = ((recent_mean - historical_mean) / abs(historical_mean)) * 100

    # Direction + confidence
    if abs(change_pct) < 2 and r_sq < 0.1:
        direction = "stable"
        confidence = "high"
    elif r_sq > 0.5:
        direction = "increasing" if slope > 0 else "decreasing"
        confidence = "high"
    elif r_sq > 0.2:
        direction = "increasing" if slope > 0 else "decreasing"
        confidence = "medium"
    else:
        direction = "stable"
        confidence = "low"

    spec = ANALYSIS_SPECS.get(analysis_code, {})
    name = spec.get("name", analysis_code)
    message = _trend_message(name, direction, change_pct, confidence)

    return TrendResult(
        analysis_code=analysis_code,
        direction=direction,
        slope=round(slope, 6),
        r_squared=round(r_sq, 3),
        change_pct=round(change_pct, 2),
        confidence=confidence,
        message=message,
        recent_mean=round(recent_mean, 3),
        historical_mean=round(historical_mean, 3),
    )


def calculate_quality_score(samples: list, anomalies: list = None) -> QualityScore:
    """
    Чанарын нэгдсэн оноо тооцоолох (0-100).

    Задаргаа:
      - completeness (30%): Шинжилгээ бүрэн гүйцэт эсэх
      - accuracy (30%): Аномали байхгүй байх
      - timeliness (20%): Цаг хугацаанд хийгдсэн эсэх
      - consistency (20%): Тогтвортой байдал (CV%)
    """
    if not samples:
        return QualityScore(
            score=0, grade="N/A", color="#94a3b8",
            breakdown={}, message=_l("Дээж байхгүй"),
        )

    # 1. COMPLETENESS (30 оноо)
    total_results = 0
    approved_results = 0
    for s in samples:
        results = list(db.session.execute(
            select(AnalysisResult).where(AnalysisResult.sample_id == s.id)
        ).scalars().all())
        total_results += len(results)
        approved_results += sum(1 for r in results if r.status == "approved")

    completeness = (approved_results / max(total_results, 1)) * 30

    # 2. ACCURACY (30 оноо) — аномали цөөн байх тусам сайн
    if anomalies is None:
        anomalies = detect_anomalies(samples)

    critical_count = sum(1 for a in anomalies if a.severity == "critical")
    warning_count = sum(1 for a in anomalies if a.severity == "warning")
    anomaly_penalty = (critical_count * 10 + warning_count * 3)
    accuracy = max(0, 30 - anomaly_penalty)

    # 3. TIMELINESS (20 оноо)
    on_time = 0
    for s in samples:
        results = list(db.session.execute(
            select(AnalysisResult).where(AnalysisResult.sample_id == s.id)
        ).scalars().all())
        if results:
            latest = max(r.created_at for r in results if r.created_at)
            if s.received_date:
                hours_diff = (latest - s.received_date).total_seconds() / 3600
                if hours_diff <= 4:
                    on_time += 1
                elif hours_diff <= 8:
                    on_time += 0.5

    timeliness = (on_time / max(len(samples), 1)) * 20

    # 4. CONSISTENCY (20 оноо) — CV% бага байх тусам сайн
    cv_scores = []
    for code in ["Mad", "Aad", "Vdaf"]:
        stats = get_historical_stats(code, days=7)
        if stats["mean"] and stats["sd"] and stats["mean"] != 0:
            cv = (stats["sd"] / abs(stats["mean"])) * 100
            if cv < 5:
                cv_scores.append(1.0)
            elif cv < 10:
                cv_scores.append(0.7)
            elif cv < 20:
                cv_scores.append(0.4)
            else:
                cv_scores.append(0.1)

    consistency = (statistics.mean(cv_scores) if cv_scores else 0.5) * 20

    # TOTAL
    score = int(round(completeness + accuracy + timeliness + consistency))
    score = max(0, min(100, score))

    grade, color = _score_to_grade(score)

    return QualityScore(
        score=score,
        grade=grade,
        color=color,
        breakdown={
            "completeness": round(completeness, 1),
            "accuracy": round(accuracy, 1),
            "timeliness": round(timeliness, 1),
            "consistency": round(consistency, 1),
        },
        message=_quality_message(score, grade, critical_count, warning_count),
    )


def generate_insights(samples: list, anomalies: list = None,
                      trends: list = None) -> list[str]:
    """
    AI-powered natural language insights үүсгэх.

    Дээжүүдийн шинжилгээний үр дүн, аномали, чиг хандлагыг
    уншигдахуйц мэдээлэл болгон хөрвүүлнэ.
    """
    insights = []

    if not samples:
        return [_l("Тайлант хугацаанд дээж бүртгэгдээгүй.")]

    # ── Sample overview ──
    insights.append(
        f"Нийт {len(samples)} дээж шинжлэгдсэн."
    )

    # ── Client distribution ──
    clients = defaultdict(int)
    for s in samples:
        clients[s.client_name or "Unknown"] += 1
    if len(clients) > 1:
        top_client = max(clients, key=clients.get)
        insights.append(
            f"Хамгийн олон дээж: {top_client} ({clients[top_client]} ш)."
        )

    # ── Anomaly insights ──
    if anomalies is None:
        anomalies = detect_anomalies(samples)

    if not anomalies:
        insights.append(_l("Бүх шинжилгээний үр дүн хэвийн хүрээнд байна."))
    else:
        critical = [a for a in anomalies if a.severity == "critical"]
        warnings = [a for a in anomalies if a.severity == "warning"]

        if critical:
            codes = set(a.analysis_code for a in critical)
            insights.append(
                f"⚠ {len(critical)} ноцтой аномали: "
                + ", ".join(ANALYSIS_SPECS.get(c, {}).get("name", c) for c in codes)
                + _l(". Нэн даруй шалгах шаардлагатай.")
            )

        if warnings:
            insights.append(
                f"📋 {len(warnings)} анхааруулга — хэвийн хүрээнд ойрхон "
                f"боловч хяналтад авах."
            )

        # Нэг дээжинд олон аномали
        anomaly_by_sample = defaultdict(int)
        for a in anomalies:
            anomaly_by_sample[a.sample_code] += 1
        multi = {k: v for k, v in anomaly_by_sample.items() if v >= 3}
        if multi:
            for sc, cnt in multi.items():
                insights.append(
                    f"🔍 {sc}: {cnt} шинжилгээнд аномали — "
                    f"дээжийн чанар/бэлтгэлийг шалгах."
                )

    # ── Trend insights ──
    if trends:
        increasing = [t for t in trends if t.direction == "increasing" and t.confidence != "low"]
        decreasing = [t for t in trends if t.direction == "decreasing" and t.confidence != "low"]

        if increasing:
            names = [ANALYSIS_SPECS.get(t.analysis_code, {}).get("name", t.analysis_code)
                     for t in increasing]
            insights.append(
                f"📈 Өсөх хандлага: {', '.join(names)}."
            )

        if decreasing:
            names = [ANALYSIS_SPECS.get(t.analysis_code, {}).get("name", t.analysis_code)
                     for t in decreasing]
            insights.append(
                f"📉 Буурах хандлага: {', '.join(names)}."
            )

    # ── Approval rate ──
    total = 0
    approved = 0
    for s in samples:
        results = list(db.session.execute(
            select(AnalysisResult).where(AnalysisResult.sample_id == s.id)
        ).scalars().all())
        total += len(results)
        approved += sum(1 for r in results if r.status == "approved")

    if total > 0:
        rate = (approved / total) * 100
        if rate >= 95:
            insights.append(f"Баталгаажуулалтын хувь: {rate:.0f}% — маш сайн.")
        elif rate >= 80:
            insights.append(f"Баталгаажуулалтын хувь: {rate:.0f}%.")
        else:
            insights.append(
                f"⚠ Баталгаажуулалтын хувь бага: {rate:.0f}%. "
                f"Pending шинжилгээнүүдийг шалгах."
            )

    return insights


def get_full_analytics(hours_back: int = 2,
                       client_name: str = None) -> AnalyticsReport:
    """
    Бүрэн AI analytics тайлан үүсгэх.

    Цагийн тайлан болон dashboard-д ашиглагдана.
    """
    now = now_local()
    start = now - timedelta(hours=hours_back)

    stmt = select(Sample).where(
        Sample.received_date >= start,
        Sample.received_date <= now,
    )
    if client_name:
        stmt = stmt.where(Sample.client_name == client_name)

    samples = list(db.session.execute(stmt).scalars().all())

    # Anomalies
    anomalies = detect_anomalies(samples)

    # Trends (main coal analyses)
    trend_codes = ["Mad", "Aad", "Vdaf", "St,d", "Qgr,ad"]
    trends = [analyze_trends(code, days=30, client_name=client_name)
              for code in trend_codes]
    trends = [t for t in trends if t.confidence != "low"]

    # Quality score
    quality = calculate_quality_score(samples, anomalies)

    # Insights
    insights = generate_insights(samples, anomalies, trends)

    # Shift comparison
    shift_comp = _compare_shifts(samples)

    # Counts
    def _count_for_sample(s_id: int) -> int:
        return db.session.execute(
            select(func.count(AnalysisResult.id))
            .where(AnalysisResult.sample_id == s_id)
        ).scalar_one()
    analysis_count = sum(_count_for_sample(s.id) for s in samples)

    return AnalyticsReport(
        timestamp=now.isoformat(),
        period=f"{start.strftime('%H:%M')} - {now.strftime('%H:%M')}",
        quality_score=quality,
        anomalies=[_anomaly_to_dict(a) for a in anomalies],
        trends=[_trend_to_dict(t) for t in trends],
        insights=insights,
        shift_comparison=shift_comp,
        sample_count=len(samples),
        analysis_count=analysis_count,
    )


# ─── HELPER FUNCTIONS ───────────────────────────────────────────

def _linear_regression(xs, ys):
    """Simple linear regression: y = slope * x + intercept."""
    n = len(xs)
    if n < 2:
        return 0, 0, 0

    mean_x = sum(xs) / n
    mean_y = sum(ys) / n

    ss_xx = sum((x - mean_x) ** 2 for x in xs)
    ss_yy = sum((y - mean_y) ** 2 for y in ys)
    ss_xy = sum((x - mean_x) * (y - mean_y) for x, y in zip(xs, ys))

    if ss_xx == 0:
        return 0, mean_y, 0

    slope = ss_xy / ss_xx
    intercept = mean_y - slope * mean_x

    r_squared = (ss_xy ** 2) / (ss_xx * ss_yy) if ss_yy != 0 else 0

    return slope, intercept, max(0, min(1, r_squared))


def _get_recommendation(code: str, z: float, value: float, stats: dict) -> str:
    """Аномалид тохирох зөвлөмж үүсгэх."""
    abs_z = abs(z)

    if abs_z > 3:
        if code in ("Mad", "MT"):
            return (
                str(_l("Дээжийн хатаалт/чийгийг шалгах. "))
                + str(_l("Агаарын чийглэг, жингийн нарийвчлал баталгаажуулах."))
            )
        if code in ("Aad",):
            return (
                str(_l("Зуух температур, шатаалтын хугацаа шалгах. "))
                + str(_l("Стандарт дээж ажиллуулах."))
            )
        if code in ("Vdaf",):
            return (
                str(_l("Зуухны температур (900±10°C) баталгаажуулах. "))
                + str(_l("N₂ хийн урсгал шалгах."))
            )
        if code in ("St,d",):
            return _l("Хүхрийн анализатор калибрлэх. Стандарт дээж шалгах.")
        if code in ("Qgr,ad",):
            return _l("Калориметрийн калибрлэлт шалгах. Бензой хүчил стандарт ажиллуулах.")
        return _l("Дахин шинжилгээ хийх. Багаж калибрлэлт шалгах.")

    if code in ("Mad", "MT"):
        return _l("Дээжийн хадгалалтын нөхцөл шалгах.")
    return _l("Дараагийн хэмжилтийг анхааралтай хянах.")


def _trend_message(name: str, direction: str, change_pct: float,
                   confidence: str) -> str:
    """Чиг хандлагын мэдээлэл үүсгэх."""
    if direction == "stable":
        return f"{name}: Тогтвортой ({change_pct:+.1f}%)."

    dir_mn = _l("өсөж") if direction == "increasing" else _l("буурч")
    conf_mn = {"high": _l("тодорхой"), "medium": _l("магадлалтай"), "low": _l("бага")}

    return (f"{name}: {dir_mn} байна ({change_pct:+.1f}%), "
            f"итгэмжлэл: {conf_mn.get(confidence, confidence)}.")


def _score_to_grade(score: int) -> tuple[str, str]:
    """Score-г grade, color болгох."""
    if score >= 95:
        return "A+", "#22c55e"
    if score >= 85:
        return "A", "#22c55e"
    if score >= 75:
        return "B", "#84cc16"
    if score >= 60:
        return "C", "#f59e0b"
    if score >= 40:
        return "D", "#f97316"
    return "F", "#ef4444"


def _quality_message(score: int, grade: str, critical: int, warning: int) -> str:
    """Чанарын оноонд тохирох мэдээлэл."""
    if score >= 90:
        msg = _l("Маш сайн. Лабораторийн чанар өндөр түвшинд.")
    elif score >= 75:
        msg = _l("Сайн. Зарим сайжруулах боломжтой хэсэг бий.")
    elif score >= 60:
        msg = _l("Дунд зэрэг. Анхаарал хандуулах шаардлагатай.")
    else:
        msg = _l("Анхааруулга! Чанарын хяналтыг нэн даруй сайжруулах.")

    if critical > 0:
        msg += f" ({critical} ноцтой аномали.)"

    return msg


def _compare_shifts(samples: list) -> dict:
    """Өдөр/шөнийн ээлжийн харьцуулалт."""
    day_vals = defaultdict(list)
    night_vals = defaultdict(list)

    for s in samples:
        if not s.received_date:
            continue
        hour = s.received_date.hour
        is_day = 8 <= hour < 20

        results = list(db.session.execute(
            select(AnalysisResult).where(
                AnalysisResult.sample_id == s.id,
                AnalysisResult.status == AnalysisResultStatus.APPROVED.value,
            )
        ).scalars().all())

        for r in results:
            if r.final_result is None:
                continue
            bucket = day_vals if is_day else night_vals
            bucket[r.analysis_code].append(float(r.final_result))

    comparison = {}
    for code in set(list(day_vals.keys()) + list(night_vals.keys())):
        dv = day_vals.get(code, [])
        nv = night_vals.get(code, [])

        comparison[code] = {
            "day": {
                "count": len(dv),
                "mean": round(statistics.mean(dv), 3) if dv else None,
                "sd": round(statistics.stdev(dv), 3) if len(dv) >= 2 else None,
            },
            "night": {
                "count": len(nv),
                "mean": round(statistics.mean(nv), 3) if nv else None,
                "sd": round(statistics.stdev(nv), 3) if len(nv) >= 2 else None,
            },
        }

    return comparison


def _anomaly_to_dict(a: Anomaly) -> dict:
    """Anomaly → JSON dict."""
    return {
        "sample_code": a.sample_code,
        "analysis_code": a.analysis_code,
        "value": a.value,
        "z_score": a.z_score,
        "historical_mean": a.historical_mean,
        "historical_sd": a.historical_sd,
        "severity": a.severity,
        "message": a.message,
        "recommendation": a.recommendation,
    }


def _trend_to_dict(t: TrendResult) -> dict:
    """TrendResult → JSON dict."""
    return {
        "analysis_code": t.analysis_code,
        "direction": t.direction,
        "slope": t.slope,
        "r_squared": t.r_squared,
        "change_pct": t.change_pct,
        "confidence": t.confidence,
        "message": t.message,
        "recent_mean": t.recent_mean,
        "historical_mean": t.historical_mean,
    }
