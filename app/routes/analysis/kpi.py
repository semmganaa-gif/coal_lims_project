# app/routes/analysis/kpi.py
# -*- coding: utf-8 -*-
"""
KPI болон ээлжийн гүйцэтгэлийн тайлантай холбоотой routes:
  - /kpi_report - Ээлжийн гүйцэтгэлийн тайлан
"""

from flask import request, render_template
from flask_login import login_required
from sqlalchemy import func
from datetime import datetime, time, timedelta
from collections import defaultdict

from app import db
from app.models import Sample, AnalysisResultLog
from app.utils.datetime import now_local
from app.utils.security import escape_like_pattern
from app.forms import KPIReportFilterForm
from app.constants import ERROR_REASON_KEYS
from app.utils.shifts import get_shift_info
from app.utils.settings import get_error_reason_labels  # ✅ DB-ээс унших


def _aggregate_error_reason_stats(date_from=None, date_to=None):
    """Timestamp ашиглан алдааны статистик гаргах"""
    q = db.session.query(
        AnalysisResultLog.error_reason,
        func.count(AnalysisResultLog.id),
    ).filter(
        AnalysisResultLog.error_reason.isnot(None),
        AnalysisResultLog.error_reason != "",
    )

    if date_from is not None:
        q = q.filter(AnalysisResultLog.timestamp >= date_from)
    if date_to is not None:
        q = q.filter(AnalysisResultLog.timestamp < date_to)

    rows = q.group_by(AnalysisResultLog.error_reason).all()

    stats = {code: 0 for code in ERROR_REASON_KEYS}
    other_total = 0

    for code, cnt in rows:
        if code in stats:
            stats[code] = cnt
        else:
            other_total += cnt

    if other_total:
        stats["other"] = other_total

    stats["total"] = sum(stats.get(code, 0) for code in ERROR_REASON_KEYS) + other_total
    return stats


def register_routes(bp):
    """Route-уудыг өгөгдсөн blueprint дээр бүртгэх"""

    # =====================================================================
    # KPI / ЭЭЛЖИЙН ГҮЙЦЭТГЭЛИЙН ТАЙЛАН
    # =====================================================================
    @bp.route("/kpi_report", methods=["GET"])
    @login_required
    def kpi_report():
        # 1. Form үүсгэх
        form = KPIReportFilterForm(request.args, meta={'csrf': False})
        # --- НЭМЭЛТ: Unit dropdown-ийг DB-ээс дүүргэх ---
        distinct_units = db.session.query(Sample.client_name).distinct().order_by(Sample.client_name).all()
        unit_choices = [("all", "Бүх нэгж")] + [(u[0], u[0]) for u in distinct_units if u[0]]
        form.unit.choices = unit_choices

        # 2. Анх ороход огноо хоосон бол Өнөөдрийг оноох
        if not form.start_date.data:
            form.start_date.data = now_local().date()
        if not form.end_date.data:
            form.end_date.data = now_local().date()

        if not form.time_base.data:
            form.time_base.data = 'received'
        if not form.group_by.data:
            form.group_by.data = 'shift'

        # 3. Огноо боловсруулах
        start_date = form.start_date.data
        end_date = form.end_date.data
        start_dt = None
        end_dt = None

        if start_date:
            start_dt = datetime.combine(start_date, time(0, 0, 0))
        if end_date:
            end_dt = datetime.combine(end_date + timedelta(days=1), time(0, 0, 0))

        # Шүүлтүүрийн утгууд
        time_base = form.time_base.data
        kpi_target = form.kpi_target.data
        group_by = form.group_by.data
        filter_shift_team = form.shift_team.data
        filter_shift_type = form.shift_type.data
        filter_unit = form.unit.data
        sample_code_q = (form.sample_code.data or "").strip()
        storage_q = (form.storage_location.data or "").strip()

        # Багана сонгох
        if time_base == "received":
            date_column = Sample.received_date
        elif time_base == "prepared":
            date_column = Sample.prepared_date
        elif time_base == "mass":
            date_column = getattr(Sample, "mass_ready_at", Sample.received_date)
        else:
            date_column = Sample.received_date

        q = Sample.query
        if start_dt:
            q = q.filter(date_column >= start_dt)
        if end_dt:
            q = q.filter(date_column < end_dt)
        if filter_unit and filter_unit != "all":
            q = q.filter(Sample.client_name == filter_unit)
        if sample_code_q:
            safe_code = escape_like_pattern(sample_code_q)
            q = q.filter(Sample.sample_code.ilike(f"%{safe_code}%"))
        if storage_q:
            safe_storage = escape_like_pattern(storage_q)
            q = q.filter(Sample.storage_location.ilike(f"%{safe_storage}%"))

        samples = q.order_by(Sample.received_date.desc()).limit(5000).all()

        # Counters
        counters = defaultdict(int)
        for s in samples:
            ts = s.received_date
            if time_base == "prepared":
                ts = s.prepared_date
            elif time_base == "mass":
                ts = getattr(s, "mass_ready_at", None)

            if not ts:
                continue

            info = get_shift_info(ts)

            if filter_shift_team and filter_shift_team != "all" and info.team != filter_shift_team:
                continue
            if filter_shift_type and filter_shift_type != "all" and info.shift_type != filter_shift_type:
                continue

            if kpi_target == "samples_prepared" and not s.prepared_date:
                continue
            if kpi_target == "mass_ready" and not getattr(s, "mass_ready", False):
                continue

            if group_by == "shift":
                key = (info.team, info.shift_type)
            elif group_by == "unit":
                key = (info.team, info.shift_type, s.client_name or "—")
            elif group_by == "sample_state":
                state = (getattr(s, "sample_condition", None) or getattr(s, "sample_state", None) or "—")
                key = (info.team, info.shift_type, state)
            elif group_by == "storage":
                loc = getattr(s, "storage_location", None) or "—"
                key = (info.team, info.shift_type, loc)
            else:
                key = (info.team, info.shift_type)

            counters[key] += 1

        result_rows = []
        for key, count in counters.items():
            if group_by == "shift":
                team, shift_type = key
                extra = ""
            else:
                team, shift_type, extra = key

            result_rows.append({
                "team": team,
                "shift_type": shift_type,
                "shift_label": f"{team}-" + ("Өдөр" if shift_type == "day" else "Шөнө"),
                "extra": extra,
                "count": count
            })

        def _sort_key(r):
            t_map = {"A": 0, "B": 1, "C": 2, "D": 3}
            return (t_map.get(r["team"], 99), 0 if r["shift_type"] == "day" else 1, r["extra"])

        result_rows.sort(key=_sort_key)
        total_count = sum(r["count"] for r in result_rows)

        error_stats = _aggregate_error_reason_stats(date_from=start_dt, date_to=end_dt)

        return render_template(
            "kpi_report.html",
            title="Ээлжийн гүйцэтгэл (Daily)",  # Нэршил шинэчилсэн
            form=form,
            rows=result_rows,
            total_count=total_count,
            error_stats=error_stats,
            error_reason_labels=get_error_reason_labels(),  # ✅ DB-ээс унших
            group_by=group_by
        )
