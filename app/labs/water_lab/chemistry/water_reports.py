# app/labs/water_lab/chemistry/water_reports.py
# -*- coding: utf-8 -*-
"""Усны хими тайлангийн routes: dashboard, consumption, monthly plan."""

import json
from datetime import datetime, timedelta
from collections import defaultdict

from flask import render_template, jsonify, request
from flask_login import login_required
from sqlalchemy import extract, func, case, select

from app import db
from app.models import Sample, AnalysisResult
from app.labs.water_lab.chemistry.constants import (
    WATER_ANALYSIS_TYPES, WATER_UNITS,
)
from app.utils.decorators import lab_required
from app.utils.datetime import now_local
from app.labs.water_lab.chemistry.routes import water_bp

_WATER_LAB_TYPES = ['water_chemistry']


def _active_chem_codes():
    return [a['code'] for a in WATER_ANALYSIS_TYPES if 'archive' not in a.get('categories', [])]


# ======================================================================
#  REPORTS: Dashboard
# ======================================================================

@water_bp.route('/reports/dashboard')
@login_required
@lab_required('water_chemistry')
def water_dashboard():
    """Усны хими Dashboard - KPI, тренд."""
    now = now_local()
    year = now.year
    month = now.month

    month_start = datetime(year, month, 1)
    month_end = datetime(year, month + 1, 1) if month < 12 else datetime(year + 1, 1, 1)
    year_start = datetime(year, 1, 1)
    year_end = datetime(year + 1, 1, 1)

    active_chem_codes = _active_chem_codes()

    # -- 1) Дээж тоо: сар + жил нэг query (conditional count) --
    row = db.session.execute(
        select(
            func.count().label('year_cnt'),
            func.count(case(
                (Sample.received_date >= month_start.date(), Sample.id),
                else_=None,
            )).label('month_cnt'),
        ).where(
            Sample.lab_type.in_(_WATER_LAB_TYPES),
            Sample.received_date >= year_start.date(),
            Sample.received_date < year_end.date(),
        )
    ).first()
    samples_year = row.year_cnt if row else 0
    samples_month = row.month_cnt if row else 0

    # -- 2) Шинжилгээ тоо: сар + жил нэг query --
    row2 = db.session.execute(
        select(
            func.count().label('year_cnt'),
            func.count(case(
                (AnalysisResult.created_at >= month_start, AnalysisResult.id),
                else_=None,
            )).label('month_cnt'),
        ).join(Sample, Sample.id == AnalysisResult.sample_id).where(
            Sample.lab_type.in_(_WATER_LAB_TYPES),
            AnalysisResult.analysis_code.in_(active_chem_codes),
            AnalysisResult.created_at >= year_start,
            AnalysisResult.created_at < year_end,
        )
    ).first()
    analyses_year = row2.year_cnt if row2 else 0
    analyses_month = row2.month_cnt if row2 else 0

    # -- 3) Категори тоо: GROUP BY нэг query --
    cat_rows = db.session.query(
        Sample.client_name, func.count()
    ).filter(
        Sample.lab_type.in_(_WATER_LAB_TYPES),
        Sample.received_date >= year_start.date(),
        Sample.received_date < year_end.date()
    ).group_by(Sample.client_name).all()
    cat_counts = [{'label': name, 'count': cnt} for name, cnt in cat_rows if cnt > 0]

    # Pass/Fail тоолох (pH, MNS limit шалгалт)
    pass_count = 0
    fail_count = 0
    ph_results = list(db.session.execute(
        select(AnalysisResult)
        .join(Sample, Sample.id == AnalysisResult.sample_id)
        .where(
            Sample.lab_type.in_(_WATER_LAB_TYPES),
            AnalysisResult.analysis_code == 'PH',
            AnalysisResult.created_at >= year_start,
            AnalysisResult.created_at < year_end,
        )
    ).scalars().all())

    for ar in ph_results:
        try:
            rd = json.loads(ar.raw_data) if ar.raw_data else {}
            val = rd.get('value') or rd.get('result') or ar.final_result
            if val is not None:
                v = float(val)
                if 6.5 <= v <= 8.5:
                    pass_count += 1
                else:
                    fail_count += 1
        except (json.JSONDecodeError, TypeError, ValueError):
            pass

    total_checked = pass_count + fail_count
    pass_rate = (pass_count / total_checked * 100) if total_checked > 0 else 100

    # -- 5) Сүүлийн 6 сарын тренд: нэг GROUP BY query --
    trend_m = month - 5
    trend_y = year
    if trend_m <= 0:
        trend_m += 12
        trend_y -= 1
    trend_start = datetime(trend_y, trend_m, 1)

    trend_rows = db.session.query(
        extract('year', AnalysisResult.created_at).label('yr'),
        extract('month', AnalysisResult.created_at).label('mn'),
        func.count()
    ).join(
        Sample, Sample.id == AnalysisResult.sample_id
    ).filter(
        Sample.lab_type.in_(_WATER_LAB_TYPES),
        AnalysisResult.analysis_code.in_(active_chem_codes),
        AnalysisResult.created_at >= trend_start,
        AnalysisResult.created_at < month_end
    ).group_by('yr', 'mn').all()

    trend_map = {(int(r.yr), int(r.mn)): r[2] for r in trend_rows}
    monthly_stats = []
    for i in range(5, -1, -1):
        m = month - i
        y = year
        if m <= 0:
            m += 12
            y -= 1
        monthly_stats.append({
            'month': m, 'year': y,
            'label': f'{m}-р сар',
            'count': trend_map.get((y, m), 0)
        })

    return render_template(
        'labs/water/chemistry/reports/water_dashboard.html',
        title='Усны хими Dashboard',
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

@water_bp.route('/reports/consumption')
@login_required
@lab_required('water_chemistry')
def water_consumption():
    """Усны хими Consumption тайлан."""
    now = now_local()
    try:
        year = int(request.args.get('year', now.year))
        if not (2000 <= year <= 2100):
            raise ValueError
    except (ValueError, TypeError):
        year = now.year

    active_chem_codes = _active_chem_codes()

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
            Sample.lab_type.in_(_WATER_LAB_TYPES),
            AnalysisResult.analysis_code.in_(active_chem_codes),
            extract('year', date_col) == year
        )
        .all()
    )

    # unit → sample_type → { sample_cnt: {1..12}, prop_rows: [(code, {1..12}, total)] }
    tree = defaultdict(lambda: defaultdict(lambda: {
        'sample_cnt': defaultdict(int),
        'code_cnt': defaultdict(lambda: defaultdict(int)),
    }))

    seen_samples = defaultdict(set)
    for sid, code, mon, unit in rows:
        unit = unit or 'Unknown'
        stype = 'Хими'
        mon = int(mon)
        tree[unit][stype]['code_cnt'][code][mon] += 1
        if sid not in seen_samples[(unit, stype, mon)]:
            seen_samples[(unit, stype, mon)].add(sid)
            tree[unit][stype]['sample_cnt'][mon] += 1

    # Grand totals
    grand_samples = defaultdict(int)
    grand_codes = defaultdict(lambda: defaultdict(int))
    for unit, stypes in tree.items():
        for stype, data in stypes.items():
            for m, c in data['sample_cnt'].items():
                grand_samples[m] += c
            for code, mdict in data['code_cnt'].items():
                for m, c in mdict.items():
                    grand_codes[code][m] += c

    # Build view
    view = []
    for unit in sorted(tree.keys()):
        subs = []
        for stype in sorted(tree[unit].keys()):
            data = tree[unit][stype]
            prop_rows = []
            for code in sorted(data['code_cnt'].keys()):
                monthly = data['code_cnt'][code]
                row_total = sum(monthly.values())
                prop_rows.append((code, monthly, row_total))
            subs.append({
                'stype': stype,
                'sample_cnt': data['sample_cnt'],
                'sample_total': sum(data['sample_cnt'].values()),
                'prop_rows': prop_rows,
            })
        view.append((unit, subs))

    grand_rows = []
    for code in sorted(grand_codes.keys()):
        monthly = grand_codes[code]
        total = sum(monthly.values())
        grand_rows.append((code, monthly, total))

    return render_template(
        'labs/water/chemistry/reports/water_consumption.html',
        title=f'Усны хими Consumption — {year}',
        year=year, data=view,
        grand_samples=grand_samples, grand_rows=grand_rows,
    )


@water_bp.route('/api/consumption_cell')
@login_required
@lab_required('water_chemistry')
def api_consumption_cell():
    """Consumption drill-down."""
    try:
        year = int(request.args.get('year'))
        month = int(request.args.get('month'))
        if not (1 <= month <= 12) or not (2000 <= year <= 2100):
            raise ValueError('Invalid year/month range')
        unit = request.args.get('unit', '').strip()
        stype = request.args.get('stype', '').strip()
        kind = request.args.get('kind', 'samples').strip()
        code = request.args.get('code', '').strip()
        if kind not in ('samples', 'code'):
            kind = 'samples'
    except (ValueError, TypeError):
        return jsonify({'success': False, 'data': {'items': []}})

    active_chem_codes = _active_chem_codes()

    q = (
        db.session.query(
            AnalysisResult.sample_id,
            AnalysisResult.analysis_code,
            Sample.sample_code,
            AnalysisResult.created_at
        )
        .join(Sample, Sample.id == AnalysisResult.sample_id)
        .filter(
            Sample.lab_type.in_(_WATER_LAB_TYPES),
            Sample.client_name == unit,
            extract('year', AnalysisResult.created_at) == year,
            extract('month', AnalysisResult.created_at) == month,
        )
    )

    if kind == 'code' and code:
        q = q.filter(AnalysisResult.analysis_code == code)
    else:
        q = q.filter(AnalysisResult.analysis_code.in_(active_chem_codes))

    rows = q.limit(200).all()
    items = [
        {
            'sample_id': r.sample_id,
            'code': r.analysis_code,
            'sample_code': r.sample_code,
            'analysis_date': r.created_at.isoformat() if r.created_at else None,
        }
        for r in rows
    ]
    return jsonify({'success': True, 'data': {'items': items}})


# ======================================================================
#  REPORTS: Monthly Plan
# ======================================================================

@water_bp.route('/reports/monthly_plan')
@login_required
@lab_required('water_chemistry')
def water_monthly_plan():
    """Усны хими Monthly Plan."""
    from calendar import monthrange

    now = now_local()
    try:
        year = int(request.args.get('year', now.year))
        month = int(request.args.get('month', now.month))
        if not (2000 <= year <= 2100) or not (1 <= month <= 12):
            raise ValueError
    except (ValueError, TypeError):
        year, month = now.year, now.month

    years = list(range(now.year - 2, now.year + 2))
    month_names = ['', 'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
    month_name = month_names[month]

    # Долоо хоногууд
    _, days_in_month = monthrange(year, month)
    first_day = datetime(year, month, 1)
    weeks = []
    wk = 1
    d = first_day
    while d.month == month:
        week_start = d
        week_end = min(d + timedelta(days=6 - d.weekday()), datetime(year, month, days_in_month))
        if week_end.month != month:
            week_end = datetime(year, month, days_in_month)
        weeks.append({'week': wk, 'start': week_start, 'end': week_end})
        d = week_end + timedelta(days=1)
        wk += 1

    active_chem_codes = _active_chem_codes()

    # Performance data
    perf_data = defaultdict(lambda: defaultdict(lambda: defaultdict(int)))
    results = (
        db.session.query(
            Sample.client_name,
            AnalysisResult.analysis_code,
            AnalysisResult.created_at
        )
        .join(Sample, Sample.id == AnalysisResult.sample_id)
        .filter(
            Sample.lab_type.in_(_WATER_LAB_TYPES),
            AnalysisResult.analysis_code.in_(active_chem_codes),
            extract('year', AnalysisResult.created_at) == year,
            extract('month', AnalysisResult.created_at) == month,
        )
        .all()
    )

    for client, code, created_at in results:
        cat = client or 'Unknown'
        for w in weeks:
            if w['start'] <= created_at <= w['end'] + timedelta(days=1):
                perf_data[cat][code][w['week']] += 1
                break

    # Build data structure
    data = {}
    for cat in set(perf_data.keys()) | set(WATER_UNITS):
        if cat not in data:
            data[cat] = {'types': {}, 'total': {'plan': 0, 'perf': 0}, 'pct': 0}
        types = data[cat]['types']
        if 'Хими' not in types:
            types['Хими'] = {
                'weeks': {w['week']: {'plan': 0, 'perf': 0} for w in weeks},
                'total_plan': 0, 'total_perf': 0, 'pct': 0
            }
        for code in active_chem_codes:
            for w in weeks:
                types['Хими']['weeks'][w['week']]['perf'] += perf_data[cat].get(code, {}).get(w['week'], 0)
        types['Хими']['total_perf'] = sum(wd['perf'] for wd in types['Хими']['weeks'].values())
        data[cat]['total']['perf'] = types['Хими']['total_perf']

    # Week totals
    week_totals = {w['week']: {'plan': 0, 'perf': 0} for w in weeks}
    for cat_info in data.values():
        for row_data in cat_info['types'].values():
            for wk, wd in row_data['weeks'].items():
                week_totals[wk]['plan'] += wd['plan']
                week_totals[wk]['perf'] += wd['perf']

    grand_total = {
        'plan': sum(wt['plan'] for wt in week_totals.values()),
        'perf': sum(wt['perf'] for wt in week_totals.values())
    }

    staff_count = 2

    return render_template(
        'labs/water/chemistry/reports/water_monthly_plan.html',
        title='Water Monthly Plan',
        years=years, year=year, month=month, month_name=month_name,
        weeks=weeks, data=data,
        week_totals=week_totals, grand_total=grand_total,
        staff_count=staff_count,
    )
