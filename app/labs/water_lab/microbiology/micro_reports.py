# app/labs/water_lab/microbiology/micro_reports.py
# -*- coding: utf-8 -*-
"""Микробиологийн тайлангийн routes: dashboard, consumption, monthly plan."""

import json
import calendar
from datetime import datetime, date, timedelta
from collections import defaultdict, OrderedDict

from flask import render_template, jsonify, request
from flask_login import login_required, current_user
from sqlalchemy import extract, func, select

from app import db
from app.models import Sample, AnalysisResult
from app.utils.decorators import lab_required
from app.utils.datetime import now_local
from app.labs.water_lab.microbiology.routes import micro_bp

# ============ Micro lab types for monthly plan ============
MICRO_SAMPLE_TYPES = {
    'MICRO_WATER': ['Water'],
    'MICRO_AIR': ['Air'],
    'MICRO_SWAB': ['Swab'],
}

_MICRO_LAB_TYPES = ['microbiology']
_MICRO_CODES = ['MICRO_WATER', 'MICRO_AIR', 'MICRO_SWAB']


def _get_weeks_in_month(year, month):
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


def _micro_weekly_performance(year, month):
    weeks = _get_weeks_in_month(year, month)
    result = {}
    for week_num, week_start, week_end in weeks:
        rows = (
            db.session.query(
                AnalysisResult.analysis_code,
                func.count(AnalysisResult.id).label('cnt')
            )
            .join(Sample, Sample.id == AnalysisResult.sample_id)
            .filter(
                Sample.lab_type.in_(_MICRO_LAB_TYPES),
                AnalysisResult.analysis_code.in_(_MICRO_CODES),
                func.date(AnalysisResult.created_at) >= week_start,
                func.date(AnalysisResult.created_at) <= week_end,
            )
            .group_by(AnalysisResult.analysis_code)
            .all()
        )
        for ac, cnt in rows:
            types = MICRO_SAMPLE_TYPES.get(ac, ['Default'])
            per_type = cnt // len(types) if types else cnt
            remainder = cnt % len(types) if types else 0
            for i, st in enumerate(types):
                key = f"{ac}|{st}|{week_num}"
                result[key] = per_type + (1 if i < remainder else 0)
    return result


# ======================================================================
#  REPORTS: Dashboard
# ======================================================================

@micro_bp.route('/reports/dashboard')
@login_required
@lab_required('microbiology')
def micro_dashboard():
    now = now_local()
    year = now.year
    month = now.month

    month_start = datetime(year, month, 1)
    month_end = datetime(year, month + 1, 1) if month < 12 else datetime(year + 1, 1, 1)
    year_start = datetime(year, 1, 1)
    year_end = datetime(year + 1, 1, 1)

    samples_month = db.session.execute(
        select(func.count(Sample.id)).where(
            Sample.lab_type.in_(_MICRO_LAB_TYPES),
            Sample.received_date >= month_start.date(),
            Sample.received_date < month_end.date(),
        )
    ).scalar_one()

    samples_year = db.session.execute(
        select(func.count(Sample.id)).where(
            Sample.lab_type.in_(_MICRO_LAB_TYPES),
            Sample.received_date >= year_start.date(),
            Sample.received_date < year_end.date(),
        )
    ).scalar_one()

    analyses_month = db.session.execute(
        select(func.count(AnalysisResult.id))
        .join(Sample, Sample.id == AnalysisResult.sample_id)
        .where(
            Sample.lab_type.in_(_MICRO_LAB_TYPES),
            AnalysisResult.analysis_code.in_(_MICRO_CODES),
            AnalysisResult.created_at >= month_start,
            AnalysisResult.created_at < month_end,
        )
    ).scalar_one()

    analyses_year = db.session.execute(
        select(func.count(AnalysisResult.id))
        .join(Sample, Sample.id == AnalysisResult.sample_id)
        .where(
            Sample.lab_type.in_(_MICRO_LAB_TYPES),
            AnalysisResult.analysis_code.in_(_MICRO_CODES),
            AnalysisResult.created_at >= year_start,
            AnalysisResult.created_at < year_end,
        )
    ).scalar_one()

    cat_counts = []
    cat_labels = {'MICRO_WATER': 'Ус', 'MICRO_AIR': 'Агаар', 'MICRO_SWAB': 'Арчдас'}
    for code in _MICRO_CODES:
        cnt = db.session.execute(
            select(func.count(AnalysisResult.id))
            .join(Sample, Sample.id == AnalysisResult.sample_id)
            .where(
                Sample.lab_type.in_(_MICRO_LAB_TYPES),
                AnalysisResult.analysis_code == code,
                AnalysisResult.created_at >= year_start,
                AnalysisResult.created_at < year_end,
            )
        ).scalar_one()
        cat_counts.append({'label': cat_labels.get(code, code), 'count': cnt})

    all_results = list(db.session.execute(
        select(AnalysisResult)
        .join(Sample, Sample.id == AnalysisResult.sample_id)
        .where(
            Sample.lab_type.in_(_MICRO_LAB_TYPES),
            AnalysisResult.analysis_code.in_(_MICRO_CODES),
            AnalysisResult.created_at >= year_start,
            AnalysisResult.created_at < year_end,
        )
    ).scalars().all())

    # MNS limits per analysis code and field
    _LIMITS = {
        'MICRO_WATER': {'cfu_22': 100, 'cfu_37': 100, 'cfu_avg': 100},
        'MICRO_AIR': {'cfu_air': 3000, 'staphylococcus': 50, 'mold_fungi': 500},
        'MICRO_SWAB': {'cfu_swab': 100},
    }
    _PRESENCE_FAIL = {
        'MICRO_WATER': ['ecoli', 'salmonella'],
        'MICRO_SWAB': ['ecoli_swab', 'salmonella_swab', 'staphylococcus_swab'],
    }

    pass_count = 0
    fail_count = 0
    for ar in all_results:
        try:
            rd = json.loads(ar.raw_data) if ar.raw_data else {}
        except (json.JSONDecodeError, TypeError):
            continue
        code = ar.analysis_code
        failed = False
        # Numeric limit checks
        for field, limit in _LIMITS.get(code, {}).items():
            val = rd.get(field)
            if val is not None and val != '':
                try:
                    if float(val) > limit:
                        failed = True
                        break
                except (ValueError, TypeError):
                    pass
        # Presence/absence checks
        if not failed:
            for field in _PRESENCE_FAIL.get(code, []):
                val = rd.get(field)
                if val and str(val).lower() in ('detected', 'илэрсэн'):
                    failed = True
                    break
        if failed:
            fail_count += 1
        else:
            pass_count += 1

    total_checked = pass_count + fail_count
    pass_rate = (pass_count / total_checked * 100) if total_checked > 0 else 100

    monthly_stats = []
    for i in range(5, -1, -1):
        m = month - i
        y = year
        if m <= 0:
            m += 12
            y -= 1
        m_start = datetime(y, m, 1)
        m_end = datetime(y, m + 1, 1) if m < 12 else datetime(y + 1, 1, 1)
        cnt = db.session.execute(
            select(func.count(AnalysisResult.id))
            .join(Sample, Sample.id == AnalysisResult.sample_id)
            .where(
                Sample.lab_type.in_(_MICRO_LAB_TYPES),
                AnalysisResult.analysis_code.in_(_MICRO_CODES),
                AnalysisResult.created_at >= m_start,
                AnalysisResult.created_at < m_end,
            )
        ).scalar_one()
        monthly_stats.append({'month': m, 'year': y, 'label': f'{m}-р сар', 'count': cnt})

    return render_template(
        'labs/water/microbiology/reports/micro_dashboard.html',
        title='Микро Dashboard',
        year=year, month=month,
        samples_month=samples_month, samples_year=samples_year,
        analyses_month=analyses_month, analyses_year=analyses_year,
        category_counts=cat_counts,
        pass_count=pass_count, fail_count=fail_count, pass_rate=pass_rate,
        monthly_stats=monthly_stats,
    )


# ======================================================================
#  REPORTS: Consumption
# ======================================================================

@micro_bp.route('/reports/consumption')
@login_required
@lab_required('microbiology')
def micro_consumption():
    now = now_local()
    try:
        year = int(request.args.get('year', now.year))
    except (ValueError, TypeError):
        year = now.year

    date_col = AnalysisResult.created_at
    rows = (
        db.session.query(
            AnalysisResult.sample_id.label('sid'),
            AnalysisResult.analysis_code.label('code'),
            extract('month', date_col).label('mon'),
            Sample.client_name.label('unit'),
        )
        .join(Sample, Sample.id == AnalysisResult.sample_id)
        .filter(
            Sample.lab_type.in_(_MICRO_LAB_TYPES),
            AnalysisResult.analysis_code.in_(_MICRO_CODES),
            date_col.isnot(None),
            extract('year', date_col) == year,
        )
        .all()
    )

    def blank_table():
        return {
            'samples': {m: set() for m in range(1, 13)},
            'props': defaultdict(lambda: {m: 0 for m in range(1, 13)}),
        }

    data = defaultdict(lambda: defaultdict(blank_table))

    for r in rows:
        mon = int(r.mon) if r.mon else None
        if not mon:
            continue
        unit = (r.unit or '—').strip()
        code = (r.code or '').strip()
        tbl = data[unit][code]
        tbl['samples'][mon].add(r.sid)
        if code:
            tbl['props'][code][mon] += 1

    ordered = OrderedDict(sorted(data.items(), key=lambda kv: kv[0].lower()))
    for unit, stypes in list(ordered.items()):
        ordered[unit] = OrderedDict(sorted(stypes.items(), key=lambda kv: kv[0]))

    view = []
    for unit, stypes in ordered.items():
        sub_views = []
        for stype, tbl in stypes.items():
            sample_cnt = {m: len(tbl['samples'][m]) for m in range(1, 13)}
            sample_total = sum(sample_cnt.values())
            prop_rows = []
            for code in sorted(tbl['props'].keys()):
                monthly = tbl['props'][code]
                row_total = sum(monthly[m] for m in range(1, 13))
                if row_total > 0:
                    prop_rows.append((code, monthly, row_total))
            sub_views.append({
                'stype': stype,
                'sample_cnt': sample_cnt,
                'sample_total': sample_total,
                'prop_rows': prop_rows,
            })
        view.append((unit, sub_views))

    grand = {
        'samples': {m: 0 for m in range(1, 13)},
        'props': defaultdict(lambda: {m: 0 for m in range(1, 13)}),
    }
    for _, stypes in ordered.items():
        for _, tbl in stypes.items():
            for m in range(1, 13):
                grand['samples'][m] += len(tbl['samples'][m])
            for c, monthly in tbl['props'].items():
                for m in range(1, 13):
                    grand['props'][c][m] += monthly[m]

    grand_rows = []
    for c in sorted(grand['props'].keys()):
        monthly = grand['props'][c]
        total = sum(monthly[m] for m in range(1, 13))
        if total > 0:
            grand_rows.append((c, monthly, total))

    return render_template(
        'labs/water/microbiology/reports/micro_consumption.html',
        title=f'Микро Consumption — {year}',
        year=year, data=view,
        grand_samples=grand['samples'], grand_rows=grand_rows,
    )


@micro_bp.route('/api/consumption_cell')
@login_required
@lab_required('microbiology')
def api_consumption_cell():
    try:
        year = int(request.args.get('year'))
        month = int(request.args.get('month'))
        unit = (request.args.get('unit') or '').strip()
        stype = (request.args.get('stype') or '').strip()
        kind = (request.args.get('kind') or 'samples').strip()
        code = (request.args.get('code') or '').strip()
        if not (1 <= month <= 12):
            raise ValueError
    except (ValueError, TypeError):
        return jsonify({'success': False, 'error': 'Invalid parameter'}), 400

    date_col = AnalysisResult.created_at
    q = (
        db.session.query(
            Sample.id.label('sample_id'),
            Sample.sample_code,
            AnalysisResult.analysis_code.label('code'),
            date_col.label('dt'),
        )
        .join(AnalysisResult, AnalysisResult.sample_id == Sample.id)
        .filter(
            Sample.client_name == unit,
            AnalysisResult.analysis_code == stype,
            date_col.isnot(None),
            extract('year', date_col) == year,
            extract('month', date_col) == month,
        )
    )

    if kind == 'code' and code:
        q = q.filter(AnalysisResult.analysis_code == code)

    results = q.order_by(date_col.desc()).all()

    if kind == 'samples':
        seen = set()
        items = []
        for r in results:
            if r.sample_id in seen:
                continue
            seen.add(r.sample_id)
            items.append({
                'sample_id': r.sample_id, 'sample_code': r.sample_code,
                'code': r.code,
                'analysis_date': r.dt.isoformat() if r.dt else '',
            })
    else:
        items = [{
            'sample_id': r.sample_id, 'sample_code': r.sample_code,
            'code': r.code,
            'analysis_date': r.dt.isoformat() if r.dt else '',
        } for r in results]

    return jsonify({'success': True, 'data': {'items': items}})


# ======================================================================
#  REPORTS: Monthly Plan
# ======================================================================

@micro_bp.route('/reports/monthly_plan')
@login_required
@lab_required('microbiology')
def micro_monthly_plan():
    from app import models as M

    now = now_local()
    current_year = now.year
    current_month = now.month

    years = list(range(current_year - 3, current_year + 1))
    year = request.args.get('year', type=int) or current_year
    month = request.args.get('month', type=int) or current_month

    if year < current_year - 20 or year > current_year + 1:
        year = current_year
    if month < 1 or month > 12:
        month = current_month

    month_names = ['', 'January', 'February', 'March', 'April', 'May', 'June',
                   'July', 'August', 'September', 'October', 'November', 'December']
    month_name = month_names[month]

    weeks_raw = _get_weeks_in_month(year, month)
    weeks = [{'week': w, 'start': s, 'end': e, 'days': (e - s).days + 1}
             for w, s, e in weeks_raw]

    plans_db = list(db.session.execute(
        select(M.MonthlyPlan).where(
            M.MonthlyPlan.year == year,
            M.MonthlyPlan.month == month,
            M.MonthlyPlan.client_name.in_(_MICRO_CODES),
        )
    ).scalars().all())
    plans = {}
    for p in plans_db:
        key = f"{p.client_name}|{p.sample_type}|{p.week}"
        plans[key] = p.planned_count or 0

    performance = _micro_weekly_performance(year, month)

    data = OrderedDict()
    week_totals = {w['week']: {'plan': 0, 'perf': 0} for w in weeks}
    grand_total = {'plan': 0, 'perf': 0}

    for cat_code, sample_types in MICRO_SAMPLE_TYPES.items():
        cat_data = OrderedDict()
        cat_week_sums = {w['week']: {'plan': 0, 'perf': 0} for w in weeks}
        cat_total = {'plan': 0, 'perf': 0}

        for sample_type in sample_types:
            row_total_plan = 0
            row_total_perf = 0
            week_values = {}

            for w in weeks:
                key = f"{cat_code}|{sample_type}|{w['week']}"
                plan_val = plans.get(key, 0)
                perf_val = performance.get(key, 0)
                week_values[w['week']] = {'plan': plan_val, 'perf': perf_val}
                row_total_plan += plan_val
                row_total_perf += perf_val
                cat_week_sums[w['week']]['plan'] += plan_val
                cat_week_sums[w['week']]['perf'] += perf_val
                week_totals[w['week']]['plan'] += plan_val
                week_totals[w['week']]['perf'] += perf_val

            cat_total['plan'] += row_total_plan
            cat_total['perf'] += row_total_perf
            pct = (row_total_perf / row_total_plan * 100) if row_total_plan > 0 else 0
            cat_data[sample_type] = {
                'weeks': week_values,
                'total_plan': row_total_plan, 'total_perf': row_total_perf, 'pct': pct,
            }

        cat_pct = (cat_total['perf'] / cat_total['plan'] * 100) if cat_total['plan'] > 0 else 0
        data[cat_code] = {
            'types': cat_data, 'week_sums': cat_week_sums,
            'total': cat_total, 'pct': cat_pct,
        }
        grand_total['plan'] += cat_total['plan']
        grand_total['perf'] += cat_total['perf']

    staff_settings = db.session.execute(
        select(M.StaffSettings).where(
            M.StaffSettings.year == year,
            M.StaffSettings.month == month,
        )
    ).scalar_one_or_none()
    staff_count = staff_settings.preparers if staff_settings else 3

    return render_template(
        'labs/water/microbiology/reports/micro_monthly_plan.html',
        title='Микро Monthly Plan',
        years=years, year=year, month=month, month_name=month_name,
        weeks=weeks, data=data,
        week_totals=week_totals, grand_total=grand_total,
        grand_pct=(grand_total['perf'] / grand_total['plan'] * 100) if grand_total['plan'] > 0 else 0,
        staff_count=staff_count,
    )


@micro_bp.route('/api/monthly_plan', methods=['GET'])
@login_required
@lab_required('microbiology')
def api_get_monthly_plan():
    from app import models as M
    year = request.args.get('year', type=int)
    month = request.args.get('month', type=int)
    if not year or not month:
        return jsonify({'error': 'year and month required'}), 400
    plans = list(db.session.execute(
        select(M.MonthlyPlan).where(
            M.MonthlyPlan.year == year,
            M.MonthlyPlan.month == month,
            M.MonthlyPlan.client_name.in_(_MICRO_CODES),
        )
    ).scalars().all())
    result = {}
    for p in plans:
        result[f"{p.client_name}|{p.sample_type}|{p.week}"] = p.planned_count
    return jsonify({'year': year, 'month': month, 'plans': result})


@micro_bp.route('/api/monthly_plan', methods=['POST'])
@login_required
@lab_required('microbiology')
def api_save_monthly_plan():
    from app import models as M
    if current_user.role not in ['senior', 'admin']:
        return jsonify({'error': 'Senior access only'}), 403

    req_data = request.get_json()
    year = req_data.get('year')
    month = req_data.get('month')
    plans_data = req_data.get('plans', {})
    if not year or not month:
        return jsonify({'error': 'year and month required'}), 400

    saved = 0
    for key, planned_count in plans_data.items():
        parts = key.split('|')
        if len(parts) != 3:
            continue
        client_name, sample_type, week = parts
        week = int(week)
        existing = db.session.execute(
            select(M.MonthlyPlan).where(
                M.MonthlyPlan.year == year,
                M.MonthlyPlan.month == month,
                M.MonthlyPlan.week == week,
                M.MonthlyPlan.client_name == client_name,
                M.MonthlyPlan.sample_type == sample_type,
            )
        ).scalar_one_or_none()
        if existing:
            existing.planned_count = planned_count
            existing.updated_at = now_local()
        else:
            db.session.add(M.MonthlyPlan(
                year=year, month=month, week=week,
                client_name=client_name, sample_type=sample_type,
                planned_count=planned_count, created_by_id=current_user.id,
            ))
        saved += 1

    db.session.commit()
    return jsonify({'success': True, 'saved': saved})


@micro_bp.route('/api/plan_stats')
@login_required
@lab_required('microbiology')
def api_plan_stats():
    from app import models as M
    now = now_local()
    year = request.args.get('year', type=int) or now.year
    month = request.args.get('month', type=int) or now.month

    weeks_raw = _get_weeks_in_month(year, month)
    performance = _micro_weekly_performance(year, month)

    weekly = []
    for wn, ws, we in weeks_raw:
        planned = db.session.query(
            func.sum(M.MonthlyPlan.planned_count)
        ).filter_by(year=year, month=month, week=wn).filter(
            M.MonthlyPlan.client_name.in_(_MICRO_CODES)
        ).scalar() or 0
        actual = sum(v for k, v in performance.items() if k.endswith(f'|{wn}'))
        weekly.append({'week': wn, 'start': ws.isoformat(), 'end': we.isoformat(),
                       'planned': planned, 'actual': actual})

    return jsonify({'year': year, 'month': month, 'weekly': weekly})


@micro_bp.route('/api/save_staff', methods=['POST'])
@login_required
@lab_required('microbiology')
def api_save_staff():
    from app import models as M
    if current_user.role not in ['senior', 'admin']:
        return jsonify({'error': 'Senior access only'}), 403

    req_data = request.get_json()
    year = req_data.get('year')
    month = req_data.get('month')
    count = req_data.get('staff_count', 3)
    if not year or not month:
        return jsonify({'error': 'year and month required'}), 400

    existing = db.session.execute(
        select(M.StaffSettings).where(
            M.StaffSettings.year == year,
            M.StaffSettings.month == month,
        )
    ).scalar_one_or_none()
    if existing:
        existing.preparers = count
        existing.updated_at = now_local()
    else:
        db.session.add(M.StaffSettings(year=year, month=month, preparers=count, chemists=count))
    db.session.commit()
    return jsonify({'success': True})
