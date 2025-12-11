# app/routes/analysis/kpi.py
# -*- coding: utf-8 -*-
"""
KPI болон ээлжийн гүйцэтгэлийн тайлантай холбоотой routes:
  - /shift_daily - Ээлжийн гүйцэтгэл (Daily)
"""

from flask import request, render_template, jsonify
from flask_login import login_required
from sqlalchemy import func
from datetime import datetime, time, timedelta
from collections import defaultdict

from app import db
from app.models import Sample, AnalysisResultLog, User
from app.utils.datetime import now_local
from app.utils.security import escape_like_pattern
from app.forms import KPIReportFilterForm
from app.constants import ERROR_REASON_KEYS
from app.utils.shifts import get_shift_info
from app.utils.settings import get_error_reason_labels  # ✅ DB-ээс унших


def _aggregate_error_reason_stats(date_from=None, date_to=None, user_name=None):
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

    # Химичийн нэрээр шүүх
    if user_name:
        from app.utils.security import escape_like_pattern
        safe_user = escape_like_pattern(user_name)
        q = q.join(User, AnalysisResultLog.user_id == User.id).filter(
            User.username.ilike(f"%{safe_user}%")
        )

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
    @bp.route("/shift_daily", methods=["GET"])
    @login_required
    def shift_daily():
        from app.constants import SAMPLE_TYPE_CHOICES_MAP

        # 1. Form үүсгэх
        form = KPIReportFilterForm(request.args, meta={'csrf': False})

        # --- Unit dropdown-ийг DB-ээс дүүргэх ---
        distinct_units = db.session.query(Sample.client_name).distinct().order_by(Sample.client_name).all()
        unit_choices = [("all", "Бүх нэгж")] + [(u[0], u[0]) for u in distinct_units if u[0]]
        form.unit.choices = unit_choices

        # --- Sample type dropdown-ийг SAMPLE_TYPE_CHOICES_MAP-аас дүүргэх ---
        selected_unit = request.args.get("unit", "all")
        if selected_unit and selected_unit != "all" and selected_unit in SAMPLE_TYPE_CHOICES_MAP:
            type_list = SAMPLE_TYPE_CHOICES_MAP[selected_unit]
        else:
            # Бүх төрлүүдийг нэгтгэх
            all_types = set()
            for types in SAMPLE_TYPE_CHOICES_MAP.values():
                all_types.update(types)
            type_list = sorted(all_types)
        type_choices = [("all", "Бүх төрөл")] + [(t, t) for t in type_list]
        form.sample_type.choices = type_choices

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
        filter_sample_type = form.sample_type.data
        user_name_q = (form.user_name.data or "").strip()

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
        if filter_sample_type and filter_sample_type != "all":
            q = q.filter(Sample.sample_type == filter_sample_type)

        # Химичийн нэрээр шүүх (AnalysisResultLog → User)
        if user_name_q:
            safe_user = escape_like_pattern(user_name_q)
            # Тухайн хэрэглэгчийн шинжилгээ хийсэн sample_id-уудыг олох
            user_sample_ids = db.session.query(AnalysisResultLog.sample_id).join(
                User, AnalysisResultLog.user_id == User.id
            ).filter(
                User.username.ilike(f"%{safe_user}%")
            ).distinct().subquery()
            q = q.filter(Sample.id.in_(db.session.query(user_sample_ids)))

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

        error_stats = _aggregate_error_reason_stats(date_from=start_dt, date_to=end_dt, user_name=user_name_q)

        # =====================================================================
        # Хүлээн авсан / Бэлтгэсэн тоог ээлжээр гаргах
        # =====================================================================
        shift_kpi = {'received': {}, 'prepared': {}}

        # Хүлээн авсан (received_date дээр суурилсан)
        for s in samples:
            if s.received_date:
                info = get_shift_info(s.received_date)
                key = (info.team, info.shift_type)
                if key not in shift_kpi['received']:
                    shift_kpi['received'][key] = 0
                shift_kpi['received'][key] += 1

        # Бэлтгэсэн (prepared_date дээр суурилсан)
        for s in samples:
            if s.prepared_date:
                # prepared_date нь date эсвэл datetime байж болно
                prep_dt = s.prepared_date
                if not isinstance(prep_dt, datetime):
                    prep_dt = datetime.combine(prep_dt, time(12, 0, 0))  # Өдрийн дунд гэж үзэх
                info = get_shift_info(prep_dt)
                key = (info.team, info.shift_type)
                if key not in shift_kpi['prepared']:
                    shift_kpi['prepared'][key] = 0
                shift_kpi['prepared'][key] += 1

        # Ээлж бүрээр нэгтгэх
        shift_summary = []
        for team in ['A', 'B', 'C']:
            received_day = shift_kpi['received'].get((team, 'day'), 0)
            received_night = shift_kpi['received'].get((team, 'night'), 0)
            prepared_day = shift_kpi['prepared'].get((team, 'day'), 0)
            prepared_night = shift_kpi['prepared'].get((team, 'night'), 0)

            if received_day + received_night + prepared_day + prepared_night > 0:
                shift_summary.append({
                    'team': team,
                    'received_day': received_day,
                    'received_night': received_night,
                    'received_total': received_day + received_night,
                    'prepared_day': prepared_day,
                    'prepared_night': prepared_night,
                    'prepared_total': prepared_day + prepared_night,
                })

        return render_template(
            "reports/shift_daily.html",
            title="Ээлжийн гүйцэтгэл (Daily)",
            form=form,
            rows=result_rows,
            total_count=total_count,
            error_stats=error_stats,
            error_reason_labels=get_error_reason_labels(),  # ✅ DB-ээс унших
            group_by=group_by,
            shift_summary=shift_summary
        )
# =====================================================================
    # 🔹 АХЛАХЫН ХЯНАЛТАД ХАРАХ KPI ТОЙМ (ЭЭЛЖ + 14 ХОНОГ)
    # =====================================================================
    @bp.route("/api/kpi_summary_for_ahlah", methods=["GET"])
    @login_required
    def kpi_summary_for_ahlah():
        """
        Ахлахын хяналтын хуудасны дээр харагдах "COUNT" маягийн KPI:

          - shift.total_errors  -> одоогийн ээлжид бүртгэгдсэн буцаалтын (error_reason бүхий) тоо
          - days14.total_errors -> сүүлийн 14 хоногт бүртгэгдсэн буцаалтын тоо

        Real-time статус биш, AnalysisResultLog.timestamp дээр тулгуурласан "count" KPI.
        """
        now = now_local()

        # 1) Одоогийн ээлж
        shift_info = get_shift_info(now)
        shift_stats = _aggregate_error_reason_stats(
            date_from=shift_info.shift_start,
            date_to=shift_info.shift_end,
        )

        # 2) Сүүлийн 14 хоног (өнөөдөр орсон 14 бүтэн өдөр)
        tomorrow = now.date() + timedelta(days=1)
        end_dt = datetime.combine(tomorrow, time(0, 0, 0))
        start_dt = end_dt - timedelta(days=14)

        days14_stats = _aggregate_error_reason_stats(
            date_from=start_dt,
            date_to=end_dt,
        )

        payload = {
            "shift": {
                "label": shift_info.label,  # Ж: "A-Өдөр"
                "start": shift_info.shift_start.strftime("%Y-%m-%d %H:%M"),
                "end": shift_info.shift_end.strftime("%Y-%m-%d %H:%M"),
                "total_errors": int(shift_stats.get("total", 0)),
            },
            "days14": {
                "from": start_dt.strftime("%Y-%m-%d"),
                "to": (end_dt - timedelta(seconds=1)).strftime("%Y-%m-%d"),
                "total_errors": int(days14_stats.get("total", 0)),
            },
        }
        return jsonify(payload)