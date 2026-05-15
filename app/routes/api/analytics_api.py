# app/routes/api/analytics_api.py
# -*- coding: utf-8 -*-
"""
AI Analytics API endpoints.

Provides anomaly detection, trend analysis, quality scoring,
and intelligent insights for the LIMS dashboard.
"""

from flask import request
from flask_login import login_required
from sqlalchemy import select

from app import db
from app.routes.api.helpers import api_success, api_error


def register_routes(bp):
    """Register analytics API routes on the given blueprint."""

    @bp.route("/analytics/report")
    @login_required
    def analytics_report():
        """
        GET /api/v1/analytics/report?hours=2&client=CHPP

        Бүрэн AI analytics тайлан.
        """
        from app.services.analytics_service import get_full_analytics

        hours = request.args.get("hours", 2, type=int)
        client = request.args.get("client", None)

        hours = min(max(hours, 1), 48)

        try:
            report = get_full_analytics(hours_back=hours, client_name=client)
            return api_success({
                "timestamp": report.timestamp,
                "period": report.period,
                "sample_count": report.sample_count,
                "analysis_count": report.analysis_count,
                "quality_score": {
                    "score": report.quality_score.score,
                    "grade": report.quality_score.grade,
                    "color": report.quality_score.color,
                    "breakdown": report.quality_score.breakdown,
                    "message": report.quality_score.message,
                },
                "anomalies": report.anomalies,
                "trends": report.trends,
                "insights": report.insights,
                "shift_comparison": report.shift_comparison,
            })
        except Exception as e:
            return api_error(f"Analytics error: {e}", status_code=500)

    @bp.route("/analytics/anomalies")
    @login_required
    def analytics_anomalies():
        """
        GET /api/v1/analytics/anomalies?hours=8&client=CHPP

        Аномали илрүүлэлт.
        """
        from datetime import timedelta
        from app.models.core import Sample
        from app.services.analytics_service import detect_anomalies
        from app.utils.datetime import now_local

        hours = request.args.get("hours", 8, type=int)
        client = request.args.get("client", None)

        now = now_local()
        start = now - timedelta(hours=min(hours, 48))

        stmt = select(Sample).where(
            Sample.received_date >= start,
            Sample.received_date <= now,
        )
        if client:
            stmt = stmt.where(Sample.client_name == client)

        samples = list(db.session.execute(stmt).scalars().all())

        try:
            anomalies = detect_anomalies(samples)
            return api_success({
                "count": len(anomalies),
                "critical": sum(1 for a in anomalies if a.severity == "critical"),
                "warning": sum(1 for a in anomalies if a.severity == "warning"),
                "anomalies": [
                    {
                        "sample_code": a.sample_code,
                        "analysis_code": a.analysis_code,
                        "value": a.value,
                        "z_score": a.z_score,
                        "severity": a.severity,
                        "message": a.message,
                        "recommendation": a.recommendation,
                    }
                    for a in anomalies
                ],
            })
        except Exception as e:
            return api_error(f"Anomaly detection error: {e}", status_code=500)

    @bp.route("/analytics/trends")
    @login_required
    def analytics_trends():
        """
        GET /api/v1/analytics/trends?codes=Mad,Aad,Vdaf&days=30&client=CHPP

        Чиг хандлагын шинжилгээ.
        """
        from app.services.analytics_service import analyze_trends

        codes_str = request.args.get("codes", "Mad,Aad,Vdaf,St,d,Qgr,ad")
        codes = [c.strip() for c in codes_str.split(",") if c.strip()]
        days = request.args.get("days", 30, type=int)
        client = request.args.get("client", None)

        days = min(max(days, 7), 365)

        try:
            results = []
            for code in codes:
                t = analyze_trends(code, days=days, client_name=client)
                results.append({
                    "analysis_code": t.analysis_code,
                    "direction": t.direction,
                    "slope": t.slope,
                    "r_squared": t.r_squared,
                    "change_pct": t.change_pct,
                    "confidence": t.confidence,
                    "message": t.message,
                    "recent_mean": t.recent_mean,
                    "historical_mean": t.historical_mean,
                })

            return api_success(results)
        except Exception as e:
            return api_error(f"Trend analysis error: {e}", status_code=500)

    @bp.route("/analytics/quality-score")
    @login_required
    def analytics_quality_score():
        """
        GET /api/v1/analytics/quality-score?hours=8&client=CHPP

        Чанарын нэгдсэн оноо.
        """
        from datetime import timedelta
        from app.models.core import Sample
        from app.services.analytics_service import calculate_quality_score
        from app.utils.datetime import now_local

        hours = request.args.get("hours", 8, type=int)
        client = request.args.get("client", None)

        now = now_local()
        start = now - timedelta(hours=min(hours, 48))

        stmt = select(Sample).where(
            Sample.received_date >= start,
            Sample.received_date <= now,
        )
        if client:
            stmt = stmt.where(Sample.client_name == client)

        samples = list(db.session.execute(stmt).scalars().all())

        try:
            qs = calculate_quality_score(samples)
            return api_success({
                "score": qs.score,
                "grade": qs.grade,
                "color": qs.color,
                "breakdown": qs.breakdown,
                "message": qs.message,
                "sample_count": len(samples),
            })
        except Exception as e:
            return api_error(f"Quality score error: {e}", status_code=500)

    @bp.route("/analytics/historical-stats")
    @login_required
    def analytics_historical_stats():
        """
        GET /api/v1/analytics/historical-stats?code=Mad&days=90&client=CHPP

        Түүхэн статистик (mean, sd, median, IQR г.м.).
        """
        from app.services.analytics_service import get_historical_stats

        code = request.args.get("code")
        if not code:
            return api_error("'code' parameter required")

        days = request.args.get("days", 90, type=int)
        client = request.args.get("client", None)

        try:
            stats = get_historical_stats(code, days=days, client_name=client)
            # values жагсаалт хэт том байж болох тул хасах
            stats.pop("values", None)
            return api_success(stats)
        except Exception as e:
            return api_error(f"Stats error: {e}", status_code=500)
