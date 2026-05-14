# app/services/report_service.py
# -*- coding: utf-8 -*-
"""
Monthly Plan & Chemist Report — business logic extracted from routes.

All functions accept plain Python params and return plain Python dicts/tuples.
No Flask request/jsonify/render_template/flash/current_user imports allowed.
"""

import calendar
from collections import OrderedDict, defaultdict
from datetime import date, datetime, timedelta

from sqlalchemy import extract, func
from sqlalchemy.exc import SQLAlchemyError

from app import db
from app import models as M
from app.repositories import MonthlyPlanRepository, StaffSettingsRepository
from app.utils.datetime import now_local
from app.utils.transaction import transactional


# ------------------------------------------------------------------
#  Helper: format short name  (moved here as a pure utility)
# ------------------------------------------------------------------

def format_short_name(full_name: str) -> str:
    """
    "Нэр Овог" → "Нэр.О" болгох
    Жишээ: "GANTULGA Ulziibuyan" → "Gantulga.U"
    """
    if not full_name:
        return ""
    parts = full_name.strip().split()
    if len(parts) >= 2:
        first_name = parts[0].capitalize()
        last_name = parts[1]
        return f"{first_name}.{last_name[0].upper()}"
    return full_name


# ------------------------------------------------------------------
#  Weeks in month
# ------------------------------------------------------------------

def get_weeks_in_month(year, month):
    """
    Сарын долоо хоногуудын эхлэл/төгсгөл огноог буцаах.
    Returns: [(week_num, start_date, end_date), ...]
    """
    _, last_day = calendar.monthrange(year, month)
    first = date(year, month, 1)
    last = date(year, month, last_day)

    weeks = []
    week_num = 1
    current = first

    while current <= last:
        week_start = current
        week_end = min(current + timedelta(days=6), last)
        weeks.append((week_num, week_start, week_end))
        current = week_end + timedelta(days=1)
        week_num += 1

    return weeks


# ------------------------------------------------------------------
#  Weekly performance
# ------------------------------------------------------------------

def calculate_weekly_performance(year, month):
    """
    Долоо хоног бүрийн гүйцэтгэл (дээжийн тоо) тооцох.
    Returns: (result_dict, weeks_list)
        result_dict: { "CHPP|2 hourly|1": count, ... }
        weeks_list:  [(week_num, start_date, end_date), ...]
    """
    weeks = get_weeks_in_month(year, month)
    result = {}

    for week_num, week_start, week_end in weeks:
        samples = M.Sample.query.filter(
            func.date(M.Sample.received_date) >= week_start,
            func.date(M.Sample.received_date) <= week_end
        ).all()

        counts = defaultdict(int)
        for s in samples:
            if s.client_name and s.sample_type:
                key = f"{s.client_name}|{s.sample_type}|{week_num}"
                counts[key] += 1

        result.update(counts)

    return result, weeks


# ------------------------------------------------------------------
#  Build monthly plan context
# ------------------------------------------------------------------

def build_monthly_plan_context(year, month):
    """
    Build all template context data for the monthly plan page.

    Returns a dict with keys:
        data, weeks, plans, performance, week_totals, grand_total,
        grand_pct, staff_preparers, staff_chemists, month_name, years
    """
    from app.constants import SAMPLE_TYPE_CHOICES_MAP

    now = now_local()
    current_year = now.year

    years = list(range(current_year - 3, current_year + 1))

    # Сарын нэр
    month_names = [
        '', 'January', 'February', 'March', 'April', 'May', 'June',
        'July', 'August', 'September', 'October', 'November', 'December',
    ]
    month_name = month_names[month]

    # Долоо хоногууд
    weeks_raw = get_weeks_in_month(year, month)
    weeks = []
    for week_num, start_date, end_date in weeks_raw:
        days_count = (end_date - start_date).days + 1
        weeks.append({
            'week': week_num,
            'start': start_date,
            'end': end_date,
            'days': days_count,
        })

    # Planned тоонууд (DB-с)
    plans_db = MonthlyPlanRepository.get_by_month(year, month)
    plans = {}
    for p in plans_db:
        key = f"{p.client_name}|{p.sample_type}|{p.week}"
        plans[key] = p.planned_count or 0

    # Performance тоонууд (дээж хүлээн авсан)
    performance, _ = calculate_weekly_performance(year, month)

    # Data structure with pre-calculated sums
    data = OrderedDict()
    week_totals = {w['week']: {'plan': 0, 'perf': 0} for w in weeks}
    grand_total = {'plan': 0, 'perf': 0}

    # Тодорхой дараалал
    consignor_order = ['UHG-Geo', 'BN-Geo', 'QC', 'Proc', 'WTL', 'CHPP', 'LAB']
    ordered_clients = [c for c in consignor_order if c in SAMPLE_TYPE_CHOICES_MAP]
    for c in SAMPLE_TYPE_CHOICES_MAP.keys():
        if c not in ordered_clients:
            ordered_clients.append(c)

    for client_name in ordered_clients:
        client_data = OrderedDict()
        client_week_sums = {w['week']: {'plan': 0, 'perf': 0} for w in weeks}
        client_total = {'plan': 0, 'perf': 0}

        for sample_type in SAMPLE_TYPE_CHOICES_MAP[client_name]:
            row_total_plan = 0
            row_total_perf = 0
            week_values = {}

            for w in weeks:
                key = f"{client_name}|{sample_type}|{w['week']}"
                plan_val = plans.get(key, 0)
                perf_val = performance.get(key, 0)

                week_values[w['week']] = {'plan': plan_val, 'perf': perf_val}
                row_total_plan += plan_val
                row_total_perf += perf_val

                client_week_sums[w['week']]['plan'] += plan_val
                client_week_sums[w['week']]['perf'] += perf_val

                week_totals[w['week']]['plan'] += plan_val
                week_totals[w['week']]['perf'] += perf_val

            client_total['plan'] += row_total_plan
            client_total['perf'] += row_total_perf

            pct = (row_total_perf / row_total_plan * 100) if row_total_plan > 0 else 0

            client_data[sample_type] = {
                'weeks': week_values,
                'total_plan': row_total_plan,
                'total_perf': row_total_perf,
                'pct': pct,
            }

        client_pct = (
            (client_total['perf'] / client_total['plan'] * 100)
            if client_total['plan'] > 0 else 0
        )

        data[client_name] = {
            'types': client_data,
            'week_sums': client_week_sums,
            'total': client_total,
            'pct': client_pct,
        }

        grand_total['plan'] += client_total['plan']
        grand_total['perf'] += client_total['perf']

    # Grand percentage
    grand_pct = (
        (grand_total['perf'] / grand_total['plan'] * 100)
        if grand_total['plan'] > 0 else 0
    )

    # Өдрийн ачаалал тооцох (долоо хоног бүрд)
    for w in weeks:
        wt = week_totals[w['week']]
        wt['daily_plan'] = round(wt['plan'] / w['days'], 1) if w['days'] > 0 else 0
        wt['daily_perf'] = round(wt['perf'] / w['days'], 1) if w['days'] > 0 else 0

    # Сарын нийт өдөр
    total_days = sum(w['days'] for w in weeks)
    grand_total['daily_plan'] = round(grand_total['plan'] / total_days, 1) if total_days > 0 else 0
    grand_total['daily_perf'] = round(grand_total['perf'] / total_days, 1) if total_days > 0 else 0

    # Staff settings
    staff_settings = StaffSettingsRepository.find_by_month(year, month)
    staff_preparers = staff_settings.preparers if staff_settings else 6
    staff_chemists = staff_settings.chemists if staff_settings else 10

    return {
        'data': data,
        'weeks': weeks,
        'plans': plans,
        'performance': performance,
        'week_totals': week_totals,
        'grand_total': grand_total,
        'grand_pct': grand_pct,
        'staff_preparers': staff_preparers,
        'staff_chemists': staff_chemists,
        'month_name': month_name,
        'years': years,
    }


# ------------------------------------------------------------------
#  Save monthly plans (upsert)
# ------------------------------------------------------------------

@transactional()
def _save_monthly_plans_atomic(plans_dict, year, month, user_id):
    saved_count = 0
    for key, planned_count in plans_dict.items():
        parts = key.split("|")
        if len(parts) != 3:
            continue

        client_name, sample_type, week = parts
        week = int(week)

        existing = MonthlyPlanRepository.find_for_week(
            year, month, week, client_name, sample_type
        )

        if existing:
            existing.planned_count = planned_count
            existing.updated_at = now_local()
        else:
            new_plan = M.MonthlyPlan(
                year=year, month=month, week=week,
                client_name=client_name, sample_type=sample_type,
                planned_count=planned_count,
                created_by_id=user_id,
            )
            db.session.add(new_plan)

        saved_count += 1
    return saved_count


def save_monthly_plans(plans_dict, year, month, user_id):
    """
    Upsert monthly plan rows.

    Args:
        plans_dict: { "CHPP|2 hourly|1": 10, ... }
        year, month: int
        user_id: int (created_by_id for new rows)

    Returns:
        (success: bool, saved_count: int, error_msg: str | None)
    """
    try:
        saved_count = _save_monthly_plans_atomic(plans_dict, year, month, user_id)
    except SQLAlchemyError as e:
        return False, 0, f"Monthly plan save error: {e}"
    return True, saved_count, None


# ------------------------------------------------------------------
#  Save staff settings (upsert)
# ------------------------------------------------------------------

@transactional()
def _save_staff_settings_atomic(year, month, preparers, chemists):
    existing = StaffSettingsRepository.find_by_month(year, month)

    if existing:
        existing.preparers = preparers
        existing.chemists = chemists
        existing.updated_at = now_local()
    else:
        new_settings = M.StaffSettings(
            year=year, month=month,
            preparers=preparers, chemists=chemists,
        )
        db.session.add(new_settings)


def save_staff_settings(year, month, preparers, chemists):
    """
    Upsert staff settings for a given year/month.

    Returns:
        (success: bool, error_msg: str | None)
    """
    try:
        _save_staff_settings_atomic(year, month, preparers, chemists)
    except SQLAlchemyError as e:
        return False, f"Staff settings save error: {e}"
    return True, None


# ------------------------------------------------------------------
#  Plan statistics
# ------------------------------------------------------------------

def get_plan_statistics(from_year, from_month, to_year, to_month):
    """
    Build plan statistics (yearly, monthly, weekly, consignor).

    Returns a dict ready for jsonify.
    """
    from app.constants import SAMPLE_TYPE_CHOICES_MAP

    now = now_local()
    current_year = now.year

    # Validate / swap
    if from_year > to_year or (from_year == to_year and from_month > to_month):
        from_year, from_month, to_year, to_month = to_year, to_month, from_year, from_month

    range_start = date(from_year, from_month, 1)
    _, last_day = calendar.monthrange(to_year, to_month)
    range_end = date(to_year, to_month, last_day)

    # ===== Жилийн статистик =====
    yearly_stats = []
    for year in range(from_year, to_year + 1):
        year_start = date(year, 1, 1)
        year_end = date(year, 12, 31)

        if year == from_year:
            year_start = range_start
        if year == to_year:
            year_end = range_end

        plan_query = db.session.query(func.sum(M.MonthlyPlan.planned_count)).filter(
            M.MonthlyPlan.year == year
        )
        if year == from_year:
            plan_query = plan_query.filter(M.MonthlyPlan.month >= from_month)
        if year == to_year:
            plan_query = plan_query.filter(M.MonthlyPlan.month <= to_month)
        planned = plan_query.scalar() or 0

        perf_count = M.Sample.query.filter(
            M.Sample.received_date.between(year_start, year_end),
            M.Sample.status != 'cancelled'
        ).count()

        pct = round((perf_count / planned * 100), 1) if planned > 0 else 0
        yearly_stats.append({
            'year': year,
            'planned': planned,
            'actual': perf_count,
            'pct': pct,
        })

    # ===== Сарын статистик =====
    monthly_stats = []
    for year in range(from_year, to_year + 1):
        start_m = from_month if year == from_year else 1
        end_m = to_month if year == to_year else 12

        for month in range(start_m, end_m + 1):
            if year == current_year and month > now.month:
                continue

            month_start = date(year, month, 1)
            _, last_day = calendar.monthrange(year, month)
            month_end = date(year, month, last_day)

            planned = db.session.query(
                func.sum(M.MonthlyPlan.planned_count)
            ).filter_by(year=year, month=month).scalar() or 0

            perf_count = M.Sample.query.filter(
                M.Sample.received_date.between(month_start, month_end),
                M.Sample.status != 'cancelled'
            ).count()

            pct = round((perf_count / planned * 100), 1) if planned > 0 else 0
            monthly_stats.append({
                'year': year,
                'month': month,
                'month_name': [
                    '', 'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
                    'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec',
                ][month],
                'planned': planned,
                'actual': perf_count,
                'pct': pct,
            })

    # ===== Долоо хоногийн статистик =====
    weekly_stats = []
    for year in range(from_year, to_year + 1):
        start_m = from_month if year == from_year else 1
        end_m = to_month if year == to_year else 12

        for month in range(start_m, end_m + 1):
            if year == current_year and month > now.month:
                continue

            weeks_raw = get_weeks_in_month(year, month)

            for week_num, start, end in weeks_raw:
                if start < range_start or end > range_end:
                    if start < range_start and end < range_start:
                        continue
                    if start > range_end and end > range_end:
                        continue

                planned = db.session.query(
                    func.sum(M.MonthlyPlan.planned_count)
                ).filter_by(year=year, month=month, week=week_num).scalar() or 0

                perf_count = M.Sample.query.filter(
                    M.Sample.received_date.between(start, end),
                    M.Sample.status != 'cancelled'
                ).count()

                pct = round((perf_count / planned * 100), 1) if planned > 0 else 0
                weekly_stats.append({
                    'year': year,
                    'month': month,
                    'week': week_num,
                    'label': f"{year}/{month}/W{week_num}",
                    'start': start.isoformat(),
                    'end': end.isoformat(),
                    'planned': planned,
                    'actual': perf_count,
                    'pct': pct,
                })

    # ===== CONSIGNOR статистик =====
    consignor_stats = []
    consignor_order = ['UHG-Geo', 'BN-Geo', 'QC', 'Proc', 'WTL', 'CHPP', 'LAB']

    for client in consignor_order:
        if client not in SAMPLE_TYPE_CHOICES_MAP:
            continue

        plan_query = db.session.query(func.sum(M.MonthlyPlan.planned_count)).filter(
            M.MonthlyPlan.client_name == client,
            M.MonthlyPlan.year.between(from_year, to_year)
        )
        planned = plan_query.scalar() or 0

        perf_count = M.Sample.query.filter(
            M.Sample.received_date.between(range_start, range_end),
            M.Sample.client_name == client,
            M.Sample.status != 'cancelled'
        ).count()

        pct = round((perf_count / planned * 100), 1) if planned > 0 else 0
        consignor_stats.append({
            'client': client,
            'planned': planned,
            'actual': perf_count,
            'pct': pct,
        })

    # Summary totals
    total_planned = sum(m['planned'] for m in monthly_stats)
    total_actual = sum(m['actual'] for m in monthly_stats)
    total_pct = round((total_actual / total_planned * 100), 1) if total_planned > 0 else 0

    days_in_range = (range_end - range_start).days + 1
    if range_end > now.date():
        days_in_range = (now.date() - range_start).days + 1
    daily_avg = round(total_actual / days_in_range, 1) if days_in_range > 0 else 0

    return {
        'current_year': current_year,
        'from_year': from_year,
        'from_month': from_month,
        'to_year': to_year,
        'to_month': to_month,
        'range_label': f"{from_year}/{from_month} - {to_year}/{to_month}",
        'total_planned': total_planned,
        'total_actual': total_actual,
        'total_pct': total_pct,
        'daily_avg': daily_avg,
        'yearly': yearly_stats,
        'monthly': monthly_stats,
        'weekly': weekly_stats,
        'consignor': consignor_stats,
    }


# ------------------------------------------------------------------
#  Build chemist report data
# ------------------------------------------------------------------

def build_chemist_report_data(year, date_from_str, date_to_str):
    """
    Build all data for the chemist performance report.

    Args:
        year: int
        date_from_str: str (YYYY-MM-DD) or ""
        date_to_str: str (YYYY-MM-DD) or ""

    Returns a dict with keys:
        year, date_from, date_to, chemists, chemists_by_quality,
        analysis_codes, error_reason_keys, error_reason_labels,
        grand_monthly, grand_by_analysis, grand_errors,
        grand_total, grand_error_total, prev_year, prev_monthly
    """
    from app.models import User, AnalysisResult, AnalysisResultLog, UsageLog, MaintenanceLog
    from app.constants import ERROR_REASON_KEYS, ERROR_REASON_LABELS

    # Parse date range
    if date_from_str:
        try:
            start_dt = datetime.strptime(date_from_str, "%Y-%m-%d")
        except ValueError:
            start_dt = datetime(year, 1, 1)
    else:
        start_dt = datetime(year, 1, 1)
        date_from_str = start_dt.strftime("%Y-%m-%d")

    if date_to_str:
        try:
            end_dt = datetime.strptime(date_to_str, "%Y-%m-%d") + timedelta(days=1)
        except ValueError:
            end_dt = datetime(year + 1, 1, 1)
    else:
        end_dt = datetime(year + 1, 1, 1)
        date_to_str = (end_dt - timedelta(days=1)).strftime("%Y-%m-%d")

    # Шинжилгээ хийсэн action-ууд
    work_actions = [
        'CREATED_AUTO_APPROVED',
        'CREATED_PENDING',
        'CREATED_REJECTED',
        'CREATED_VOID_RETEST',
        'UPDATED_AUTO_APPROVED',
        'UPDATED_PENDING',
        'UPDATED_REJECTED',
        'UPDATED_VOID_RETEST',
    ]

    # 1) Шинжилгээ хийсэн бүх хэрэглэгчдийг авах
    user_ids_with_results = (
        db.session.query(AnalysisResultLog.user_id)
        .filter(
            AnalysisResultLog.action.in_(work_actions),
            AnalysisResultLog.user_id.isnot(None),
            AnalysisResultLog.timestamp >= start_dt,
            AnalysisResultLog.timestamp < end_dt,
        )
        .distinct()
        .all()
    )
    user_ids = [uid[0] for uid in user_ids_with_results]

    chemists = (
        User.query.filter(User.id.in_(user_ids)).order_by(User.full_name).all()
        if user_ids else []
    )

    # 2) Шинжилгээний үр дүн
    results = (
        db.session.query(
            AnalysisResultLog.user_id,
            AnalysisResultLog.analysis_code,
            extract("month", AnalysisResultLog.timestamp).label("month"),
            func.count(AnalysisResultLog.id).label("cnt"),
        )
        .filter(
            AnalysisResultLog.action.in_(work_actions),
            AnalysisResultLog.user_id.isnot(None),
            AnalysisResultLog.timestamp >= start_dt,
            AnalysisResultLog.timestamp < end_dt,
        )
        .group_by(
            AnalysisResultLog.user_id,
            AnalysisResultLog.analysis_code,
            extract("month", AnalysisResultLog.timestamp),
        )
        .all()
    )

    # 3) Алдааны логууд
    error_logs = (
        db.session.query(
            AnalysisResult.user_id,
            AnalysisResultLog.error_reason,
            func.count(AnalysisResultLog.id).label("cnt"),
        )
        .join(AnalysisResult, AnalysisResult.id == AnalysisResultLog.analysis_result_id)
        .filter(
            AnalysisResultLog.action == "REJECTED",
            AnalysisResultLog.error_reason.isnot(None),
            AnalysisResultLog.timestamp >= start_dt,
            AnalysisResultLog.timestamp < end_dt,
        )
        .group_by(
            AnalysisResult.user_id,
            AnalysisResultLog.error_reason,
        )
        .all()
    )

    # 4) Өгөгдлийг бүтэцлэх
    def _make_chemist_entry(uid, name):
        return {
            'id': uid,
            'name': name,
            'monthly': {m: 0 for m in range(1, 13)},
            'by_analysis': defaultdict(int),
            'errors': {key: 0 for key in ERROR_REASON_KEYS},
            'total': 0,
            'error_total': 0,
            'rank_total': None,
            'rank_quality': None,
            'quarterly': [0, 0, 0, 0],
            'quarterly_growth': [0, 0, 0],
            'eq_usage_count': 0,
            'eq_usage_hours': 0.0,
            'eq_maint_count': 0,
            'eq_calib_count': 0,
        }

    chemist_data = {}
    for user in chemists:
        chemist_data[user.id] = _make_chemist_entry(
            user.id,
            format_short_name(user.full_name) or user.username,
        )

    all_analysis_codes = set()
    for row in results:
        user_id = row.user_id
        if user_id not in chemist_data:
            user = db.session.get(User, user_id)
            if user:
                chemist_data[user_id] = _make_chemist_entry(
                    user_id,
                    format_short_name(user.full_name) or user.username,
                )
            else:
                continue

        month_val = int(row.month) if row.month else 0
        code = row.analysis_code or ""
        cnt = row.cnt

        if 1 <= month_val <= 12:
            chemist_data[user_id]['monthly'][month_val] += cnt
        chemist_data[user_id]['by_analysis'][code] += cnt
        chemist_data[user_id]['total'] += cnt
        all_analysis_codes.add(code)

    # Алдааны логуудыг нэмэх
    for row in error_logs:
        user_id = row.user_id
        if user_id not in chemist_data:
            continue
        reason = row.error_reason or ""
        cnt = row.cnt
        if reason in chemist_data[user_id]['errors']:
            chemist_data[user_id]['errors'][reason] += cnt
            chemist_data[user_id]['error_total'] += cnt

    # 5) Нийт дүн
    grand_monthly = {m: 0 for m in range(1, 13)}
    grand_by_analysis = defaultdict(int)
    grand_errors = {key: 0 for key in ERROR_REASON_KEYS}
    grand_total = 0
    grand_error_total = 0

    for uid, cdata in chemist_data.items():
        for m in range(1, 13):
            grand_monthly[m] += cdata['monthly'][m]
        for code, cnt in cdata['by_analysis'].items():
            grand_by_analysis[code] += cnt
        for key in ERROR_REASON_KEYS:
            grand_errors[key] += cdata['errors'][key]
        grand_total += cdata['total']
        grand_error_total += cdata['error_total']

    # 6) Өмнөх жилийн өгөгдөл
    prev_year = year - 1
    prev_start_dt = datetime(prev_year, 1, 1)
    prev_end_dt = datetime(prev_year + 1, 1, 1)

    prev_year_results = (
        db.session.query(
            extract("month", AnalysisResultLog.timestamp).label("month"),
            func.count(AnalysisResultLog.id).label("cnt"),
        )
        .filter(
            AnalysisResultLog.action.in_(work_actions),
            AnalysisResultLog.user_id.isnot(None),
            AnalysisResultLog.timestamp >= prev_start_dt,
            AnalysisResultLog.timestamp < prev_end_dt,
        )
        .group_by(extract("month", AnalysisResultLog.timestamp))
        .all()
    )

    prev_monthly = {m: 0 for m in range(1, 13)}
    for row in prev_year_results:
        month_val = int(row.month) if row.month else 0
        if 1 <= month_val <= 12:
            prev_monthly[month_val] = row.cnt

    # 7) Эрэмбэлэх
    sorted_chemists = sorted(
        chemist_data.values(),
        key=lambda x: x['total'],
        reverse=True,
    )

    for idx, chemist in enumerate(sorted_chemists):
        chemist['rank_total'] = idx + 1

    sorted_by_quality = sorted(
        [c for c in chemist_data.values() if c['total'] >= 10],
        key=lambda x: (x['error_total'] / x['total'] * 100) if x['total'] > 0 else 100,
    )
    for idx, chemist in enumerate(sorted_by_quality):
        chemist['rank_quality'] = idx + 1

    # Сар бүрийн өсөлт/бууралт
    for chemist in chemist_data.values():
        monthly = chemist['monthly']
        growth = []
        for m in range(2, 13):
            prev = monthly.get(m - 1, 0)
            curr = monthly.get(m, 0)
            if prev > 0:
                pct = ((curr - prev) / prev) * 100
            elif curr > 0:
                pct = 100
            else:
                pct = 0
            growth.append(round(pct, 1))
        chemist['monthly_growth'] = growth

        # Улирлын дүн
        q1 = sum(monthly.get(m, 0) for m in [1, 2, 3])
        q2 = sum(monthly.get(m, 0) for m in [4, 5, 6])
        q3 = sum(monthly.get(m, 0) for m in [7, 8, 9])
        q4 = sum(monthly.get(m, 0) for m in [10, 11, 12])
        chemist['quarterly'] = [q1, q2, q3, q4]

        quarterly_growth = []
        quarters = [q1, q2, q3, q4]
        for i in range(1, 4):
            prev = quarters[i - 1]
            curr = quarters[i]
            if prev > 0:
                pct = ((curr - prev) / prev) * 100
            elif curr > 0:
                pct = 100
            else:
                pct = 0
            quarterly_growth.append(round(pct, 1))
        chemist['quarterly_growth'] = quarterly_growth

    # 8) Багаж ашиглалтын статистик
    eq_user_ids = list(chemist_data.keys())
    if eq_user_ids:
        usage_stats = (
            db.session.query(
                UsageLog.used_by_id,
                func.count(UsageLog.id),
                func.coalesce(func.sum(UsageLog.duration_minutes), 0),
            )
            .filter(
                UsageLog.used_by_id.in_(eq_user_ids),
                UsageLog.start_time >= start_dt,
                UsageLog.start_time < end_dt,
            )
            .group_by(UsageLog.used_by_id)
            .all()
        )
        for uid, cnt, mins in usage_stats:
            if uid in chemist_data:
                chemist_data[uid]['eq_usage_count'] = cnt
                chemist_data[uid]['eq_usage_hours'] = round(int(mins) / 60.0, 1)

        maint_stats = (
            db.session.query(
                MaintenanceLog.performed_by_id,
                MaintenanceLog.action_type,
                func.count(MaintenanceLog.id),
            )
            .filter(
                MaintenanceLog.performed_by_id.in_(eq_user_ids),
                MaintenanceLog.action_date >= start_dt,
                MaintenanceLog.action_date < end_dt,
            )
            .group_by(MaintenanceLog.performed_by_id, MaintenanceLog.action_type)
            .all()
        )
        for uid, action_type, cnt in maint_stats:
            if uid in chemist_data:
                if action_type == 'Calibration':
                    chemist_data[uid]['eq_calib_count'] += cnt
                else:
                    chemist_data[uid]['eq_maint_count'] += cnt

    sorted_analysis_codes = sorted(all_analysis_codes)

    return {
        'year': year,
        'date_from': date_from_str,
        'date_to': date_to_str,
        'chemists': sorted_chemists,
        'chemists_by_quality': sorted_by_quality,
        'analysis_codes': sorted_analysis_codes,
        'error_reason_keys': ERROR_REASON_KEYS,
        'error_reason_labels': ERROR_REASON_LABELS,
        'grand_monthly': grand_monthly,
        'grand_by_analysis': dict(grand_by_analysis),
        'grand_errors': grand_errors,
        'grand_total': grand_total,
        'grand_error_total': grand_error_total,
        'prev_year': prev_year,
        'prev_monthly': prev_monthly,
    }
