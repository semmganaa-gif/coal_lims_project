# app/labs/water_lab/microbiology/routes.py
"""Микробиологийн лабораторийн routes."""

import os
import json
import calendar
from datetime import datetime, date, timedelta
from collections import defaultdict, OrderedDict
from flask import Blueprint, render_template, jsonify, request, flash, redirect, url_for
from flask_login import login_required, current_user
from sqlalchemy import extract, func
from app import db
from app.models import Sample, AnalysisResult
from app.labs.water_lab.microbiology.constants import (
    ALL_MICRO_PARAMS, MICRO_ANALYSIS_TYPES,
    MICRO_WATER_FIELDS, MICRO_AIR_FIELDS, MICRO_SWAB_FIELDS,
    CATEGORY_ANALYSIS_CODES,
)
from app.labs.water_lab.chemistry.constants import (
    WATER_ANALYSIS_TYPES, WATER_UNITS, ALL_WATER_SAMPLE_NAMES,
)
from app.utils.decorators import lab_required
from app.utils.datetime import now_local

_template_dir = os.path.join(os.path.dirname(__file__), 'templates')
micro_bp = Blueprint(
    'microbiology',
    __name__,
    template_folder=_template_dir,
    url_prefix='/labs/water-lab/microbiology'
)

# Workspace code → field list mapping
_FIELD_MAP = {
    'water': MICRO_WATER_FIELDS,
    'air': MICRO_AIR_FIELDS,
    'swab': MICRO_SWAB_FIELDS,
}


@micro_bp.route('/')
@login_required
@lab_required('microbiology')
def micro_hub():
    """Микробиологийн лабораторийн төв хуудас."""
    from app.labs import get_lab
    stats = get_lab('microbiology').sample_stats()
    return render_template(
        'micro_hub.html',
        title='Микробиологийн лаборатори',
        analysis_types=MICRO_ANALYSIS_TYPES,
        params=ALL_MICRO_PARAMS,
        total_samples=stats['total'],
        new_samples=stats['new'],
        in_progress=stats['in_progress'],
        completed=stats['completed'],
    )


@micro_bp.route('/edit_sample/<int:sample_id>', methods=['GET', 'POST'])
@login_required
@lab_required('microbiology')
def edit_sample(sample_id):
    """Микробиологийн дээж засах."""
    sample = db.session.get(Sample, sample_id)
    if not sample:
        flash('Дээж олдсонгүй.', 'danger')
        return redirect(url_for('microbiology.register_sample'))

    can_edit = current_user.role in ('admin', 'senior', 'chemist')
    if not can_edit:
        flash('Дээж засах эрх танд байхгүй.', 'warning')
        return redirect(url_for('microbiology.register_sample'))

    analyses_list = MICRO_ANALYSIS_TYPES
    try:
        current_analyses = json.loads(sample.analyses_to_perform or '[]')
    except (ValueError, TypeError):
        current_analyses = []

    if request.method == 'POST':
        new_code = request.form.get('sample_code', '').strip()
        selected_analyses = request.form.getlist('analyses')

        original_code = sample.sample_code
        code_changed = new_code and new_code != original_code
        analyses_changed = set(selected_analyses) != set(current_analyses)

        if not new_code:
            flash('Дээжний код хоосон байх боломжгүй.', 'danger')
        elif code_changed and Sample.query.filter(
            Sample.sample_code == new_code, Sample.id != sample_id
        ).first():
            flash(f'"{new_code}" нэртэй дээж аль хэдийн бүртгэлтэй.', 'danger')
        else:
            try:
                if code_changed:
                    sample.sample_code = new_code
                if analyses_changed:
                    sample.analyses_to_perform = json.dumps(selected_analyses)
                if code_changed or analyses_changed:
                    db.session.commit()
                    flash('Дээжний мэдээлэл шинэчлэгдлээ.', 'success')
                else:
                    flash('Өөрчлөлт хийгдээгүй.', 'info')
                return redirect(url_for('microbiology.register_sample'))
            except Exception as e:
                db.session.rollback()
                flash(f'Алдаа: {e}', 'danger')

    return render_template(
        'water_edit_sample.html',
        title='Дээж засах',
        sample=sample,
        analyses_list=analyses_list,
        current_analyses=current_analyses,
    )


@micro_bp.route('/delete_samples', methods=['POST'])
@login_required
@lab_required('microbiology')
def delete_samples():
    """Микробиологийн дээж устгах (admin, senior)."""
    from app.utils.audit import log_audit

    sample_ids = request.form.getlist('sample_ids')
    if not sample_ids:
        flash('Устгах дээжээ сонгоно уу!', 'warning')
        return redirect(url_for('microbiology.register_sample'))

    if current_user.role not in ('admin', 'senior', 'chemist'):
        flash('Дээж устгах эрх танд байхгүй.', 'danger')
        return redirect(url_for('microbiology.register_sample'))

    deleted = 0
    failed = []
    for sid in sample_ids:
        try:
            sample = db.session.get(Sample, int(sid))
            if not sample:
                failed.append(f'ID={sid} (Олдсонгүй)')
                continue
            if current_user.role in ('senior', 'chemist') and sample.status != 'new':
                failed.append(f'{sample.sample_code} (Боловсруулалтад орсон)')
                continue
            log_audit(
                action='sample_deleted',
                resource_type='Sample',
                resource_id=sample.id,
                details={'sample_code': sample.sample_code, 'client_name': sample.client_name},
            )
            db.session.delete(sample)
            deleted += 1
        except Exception as e:
            failed.append(f'ID={sid} ({e})')

    if deleted:
        db.session.commit()
        flash(f'{deleted} дээж амжилттай устгагдлаа.', 'success')
    if failed:
        flash(f'Алдаа: {", ".join(failed)}', 'danger')

    return redirect(url_for('microbiology.register_sample'))


@micro_bp.route('/analysis')
@login_required
@lab_required('microbiology')
def analysis_hub():
    """Микробиологийн шинжилгээний карт сонгох хуудас."""
    return render_template('micro_analysis_hub.html', title='Микробиологийн шинжилгээ')


@micro_bp.route('/register', methods=['GET', 'POST'])
@login_required
@lab_required('microbiology')
def register_sample():
    """Микробиологийн дээж бүртгэх."""
    if request.method == 'POST':
        sample_names = request.form.getlist('sample_codes')
        if not sample_names:
            flash('Дээжний нэр заавал сонгоно уу.', 'danger')
            return redirect(url_for('microbiology.register_sample'))

        from app.labs.water_lab.chemistry.utils import create_water_micro_samples
        try:
            created, skipped, n_analyses = create_water_micro_samples(request.form, current_user.id)
            if created:
                flash(f'{len(created)} дээж амжилттай бүртгэгдлээ! ({n_analyses} шинжилгээ)', 'success')
            if skipped:
                flash(f'{len(skipped)} дээж аль хэдийн бүртгэгдсэн: {", ".join(skipped)}', 'warning')
            return redirect(url_for('microbiology.register_sample'))
        except Exception as e:
            db.session.rollback()
            flash(f'Алдаа: {e}', 'danger')
            return redirect(url_for('microbiology.register_sample'))

    return render_template(
        'water_register.html',
        title='Микробиологийн дээж бүртгэл',
        units=WATER_UNITS,
        total_samples=len(ALL_WATER_SAMPLE_NAMES),
        water_analyses=WATER_ANALYSIS_TYPES,
        micro_analyses=MICRO_ANALYSIS_TYPES,
        use_aggrid=True,
        is_micro_lab=True,
    )


@micro_bp.route('/workspace/<code>')
@login_required
@lab_required('microbiology')
def workspace(code):
    """Микробиологийн ажлын хуудас.

    /workspace/water, /workspace/air, /workspace/surface
    """
    code_lower = code.lower()
    titles = {
        'water': 'Усны микробиологийн ажлын хуудас',
        'air': 'Агаарын микробиологийн ажлын хуудас',
        'swab': 'Арчдасны микробиологийн ажлын хуудас',
    }
    templates = {
        'water': 'analysis_forms/micro_workspace.html',
        'air': 'analysis_forms/micro_air_workspace.html',
        'swab': 'analysis_forms/micro_swab_workspace.html',
    }

    title = titles.get(code_lower, f'Микробиологи — {code}')
    template = templates.get(code_lower)
    if not template:
        return jsonify({'error': f'Unknown workspace: {code}'}), 404

    from app.models import Equipment
    from sqlalchemy import or_
    try:
        related_equipments = Equipment.query.filter(
            Equipment.category == 'micro',
            or_(Equipment.status.is_(None), Equipment.status != 'retired')
        ).order_by(Equipment.name.asc()).all()
    except Exception:
        related_equipments = []

    return render_template(
        template, title=title, workspace_code=code_lower,
        related_equipments=related_equipments,
    )


# ============ API endpoints ============

@micro_bp.route('/api/samples')
@login_required
@lab_required('microbiology')
def api_samples():
    """Микробиологийн дээж.

    ?category=MICRO_WATER|MICRO_AIR|MICRO_SWAB
      → тухайн category-д хамааралтай шинжилгээтэй дээжийг шүүж,
        аль хэдийн үр дүн хадгалсан дээжийг хасна.
    """
    from app.labs.water_lab.microbiology.constants import CATEGORY_ANALYSIS_CODES

    category = request.args.get('category')

    query = Sample.query.filter(
        Sample.lab_type.in_(['water', 'microbiology', 'water & micro'])
    )

    # Category-д хамааралтай analysis код бүхий дээжийг шүүх
    if category and category in CATEGORY_ANALYSIS_CODES:
        codes = CATEGORY_ANALYSIS_CODES[category]
        # analyses_to_perform JSON массив — exact match: '"CFU"' гэж хайна
        like_clauses = [Sample.analyses_to_perform.contains(f'"{c}"') for c in codes]
        from sqlalchemy import or_
        query = query.filter(or_(*like_clauses))

        # Аль хэдийн үр дүн хадгалсан дээжийг хасах
        saved_ids = db.session.query(AnalysisResult.sample_id).filter_by(
            analysis_code=category
        ).subquery()
        query = query.filter(~Sample.id.in_(saved_ids))

    samples = query.order_by(Sample.id.desc()).limit(200).all()
    return jsonify([{
        'id': s.id,
        'sample_code': s.sample_code,
        'client_name': s.client_name,
        'status': s.status,
        'sample_date': s.sample_date.isoformat() if s.sample_date else None,
    } for s in samples])


@micro_bp.route('/api/data')
@login_required
@lab_required('microbiology')
def micro_grid_data():
    """Микробиологийн дээжний жагсаалт (grid-д зориулсан)."""
    import re
    q = Sample.query.filter(
        Sample.lab_type.in_(['water', 'microbiology', 'water & micro'])
    )
    date_from = request.args.get('date_from')
    date_to = request.args.get('date_to')
    if date_from:
        q = q.filter(Sample.sample_date >= datetime.strptime(date_from, '%Y-%m-%d').date())
    if date_to:
        q = q.filter(Sample.sample_date <= datetime.strptime(date_to, '%Y-%m-%d').date())
    samples = q.order_by(Sample.id.desc()).limit(500).all()

    result = []
    for idx, s in enumerate(reversed(samples), 1):
        display_name = s.sample_code
        m = re.match(r'^(\d{2}_\d{2})_(.+)_(\d{4}-\d{2}-\d{2})$', s.sample_code)
        if m:
            display_name = m.group(2)
        else:
            m2 = re.match(r'^(.+)_(\d{4}-\d{2}-\d{2})$', s.sample_code)
            if m2:
                display_name = m2.group(1)

        unit_info = WATER_UNITS.get(s.client_name)
        unit_name = unit_info.get('short_name', unit_info['name']) if unit_info else s.client_name
        result.append({
            'seq': idx,
            'id': s.id,
            'chem_lab_id': s.chem_lab_id or '',
            'micro_lab_id': s.micro_lab_id or '',
            'sample_name': display_name,
            'sample_code': s.sample_code,
            'unit_name': unit_name,
            'lab_type': s.lab_type,
            'status': s.status,
            'sample_date': s.sample_date.isoformat() if s.sample_date else None,
            'received_date': s.received_date.strftime('%Y-%m-%d %H:%M') if s.received_date else None,
            'sampled_by': s.sampled_by or '',
            'volume': '2л + 0.5л' if s.weight == 2500 else '2л' if s.weight == 2000 else '0.5л' if s.weight == 500 else '',
            'return_sample': s.return_sample,
            'retention_date': s.retention_date.isoformat() if s.retention_date else None,
            'analyses': s.analyses_to_perform or '',
            'notes': s.notes or '',
        })
    result.reverse()
    return jsonify(result)


@micro_bp.route('/api/save_results', methods=['POST'])
@login_required
@lab_required('microbiology')
def save_results():
    """Үр дүн хадгалах (нэг дээжид)."""
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data provided'}), 400

    sample = db.session.get(Sample, data.get('sample_id'))
    if not sample:
        return jsonify({'error': 'Sample not found'}), 404

    ar = AnalysisResult(
        sample_id=sample.id,
        analysis_code=data.get('analysis_code'),
        raw_data=json.dumps(data.get('results', {}), ensure_ascii=False),
        user_id=current_user.id,
    )
    db.session.add(ar)
    db.session.commit()
    return jsonify({'success': True, 'id': ar.id})


@micro_bp.route('/api/save_batch', methods=['POST'])
@login_required
@lab_required('microbiology')
def save_batch():
    """Багцаар үр дүн хадгалах (workspace grid-ээс)."""
    data = request.get_json()
    if not data or not data.get('rows'):
        return jsonify({'error': 'No data provided'}), 400

    category = data.get('category', 'MICRO_WATER')
    fields = _FIELD_MAP.get(category.replace('MICRO_', '').lower(), MICRO_WATER_FIELDS)
    rows = data['rows']
    saved = 0
    errors = []

    for row in rows:
        sample_code = row.get('sample_code', '').strip()
        if not sample_code:
            continue

        results = {}
        for key in fields:
            if row.get(key) is not None and row.get(key) != '':
                results[key] = row[key]

        if not results:
            continue

        sample = Sample.query.filter_by(sample_code=sample_code).first()
        if not sample:
            errors.append(f'Дээж олдсонгүй: {sample_code}')
            continue

        analysis_code = category
        raw = json.dumps({
            'sample_code': sample_code,
            'start_date': row.get('start_date'),
            'end_date': row.get('end_date'),
            'category': category,
            **results,
        }, ensure_ascii=False)

        existing = AnalysisResult.query.filter_by(
            sample_id=sample.id,
            analysis_code=analysis_code,
        ).first()

        if existing:
            existing.raw_data = raw
            existing.user_id = current_user.id
        else:
            ar = AnalysisResult(
                sample_id=sample.id,
                analysis_code=analysis_code,
                raw_data=raw,
                user_id=current_user.id,
            )
            db.session.add(ar)

        saved += 1

    db.session.commit()
    resp = {'success': True, 'count': saved}
    if errors:
        resp['errors'] = errors
    return jsonify(resp)


@micro_bp.route('/api/load_batch')
@login_required
@lab_required('microbiology')
def load_batch():
    """Хадгалсан үр дүнг ачаалах."""
    category = request.args.get('category', 'MICRO_WATER')
    date_str = request.args.get('date')

    query = AnalysisResult.query.filter_by(analysis_code=category)

    if date_str:
        query = query.filter(AnalysisResult.raw_data.contains(date_str))

    results = query.order_by(AnalysisResult.id.desc()).limit(200).all()

    rows = []
    for ar in results:
        try:
            rd = json.loads(ar.raw_data) if ar.raw_data else {}
        except (json.JSONDecodeError, TypeError):
            continue
        rd['id'] = ar.id
        rd['sample_id'] = ar.sample_id
        rows.append(rd)

    rows.reverse()
    return jsonify({'rows': rows})


@micro_bp.route('/api/data')
@login_required
@lab_required('microbiology')
def micro_data():
    """Микробиологийн дээжийн жагсаалт."""
    samples = Sample.query.filter_by(lab_type='microbiology').order_by(
        Sample.received_date.desc()
    ).limit(200).all()
    return jsonify([{
        'id': s.id,
        'sample_code': s.sample_code,
        'client_name': s.client_name,
        'status': s.status,
        'sample_date': s.sample_date.isoformat() if s.sample_date else None,
    } for s in samples])


# ============ Micro lab types for monthly plan ============
MICRO_SAMPLE_TYPES = {
    'MICRO_WATER': ['Water'],
    'MICRO_AIR': ['Air'],
    'MICRO_SWAB': ['Swab'],
}

_MICRO_LAB_TYPES = ['water', 'microbiology', 'water & micro']
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

    samples_month = Sample.query.filter(
        Sample.lab_type.in_(_MICRO_LAB_TYPES),
        Sample.received_date >= month_start.date(),
        Sample.received_date < month_end.date()
    ).count()

    samples_year = Sample.query.filter(
        Sample.lab_type.in_(_MICRO_LAB_TYPES),
        Sample.received_date >= year_start.date(),
        Sample.received_date < year_end.date()
    ).count()

    analyses_month = AnalysisResult.query.join(
        Sample, Sample.id == AnalysisResult.sample_id
    ).filter(
        Sample.lab_type.in_(_MICRO_LAB_TYPES),
        AnalysisResult.analysis_code.in_(_MICRO_CODES),
        AnalysisResult.created_at >= month_start,
        AnalysisResult.created_at < month_end
    ).count()

    analyses_year = AnalysisResult.query.join(
        Sample, Sample.id == AnalysisResult.sample_id
    ).filter(
        Sample.lab_type.in_(_MICRO_LAB_TYPES),
        AnalysisResult.analysis_code.in_(_MICRO_CODES),
        AnalysisResult.created_at >= year_start,
        AnalysisResult.created_at < year_end
    ).count()

    cat_counts = []
    cat_labels = {'MICRO_WATER': 'Ус', 'MICRO_AIR': 'Агаар', 'MICRO_SWAB': 'Арчдас'}
    for code in _MICRO_CODES:
        cnt = AnalysisResult.query.join(
            Sample, Sample.id == AnalysisResult.sample_id
        ).filter(
            Sample.lab_type.in_(_MICRO_LAB_TYPES),
            AnalysisResult.analysis_code == code,
            AnalysisResult.created_at >= year_start,
            AnalysisResult.created_at < year_end
        ).count()
        cat_counts.append({'label': cat_labels.get(code, code), 'count': cnt})

    all_results = AnalysisResult.query.join(
        Sample, Sample.id == AnalysisResult.sample_id
    ).filter(
        Sample.lab_type.in_(_MICRO_LAB_TYPES),
        AnalysisResult.analysis_code.in_(_MICRO_CODES),
        AnalysisResult.created_at >= year_start,
        AnalysisResult.created_at < year_end
    ).all()

    pass_count = 0
    fail_count = 0
    for ar in all_results:
        try:
            rd = json.loads(ar.raw_data) if ar.raw_data else {}
        except (json.JSONDecodeError, TypeError):
            continue
        failed = False
        for key in ('cfu_37', 'ecoli', 'cfu_air', 'cfu_swab'):
            val = rd.get(key)
            if val is not None and val != '':
                try:
                    if float(val) > 100:
                        failed = True
                        break
                except (ValueError, TypeError):
                    pass
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
        cnt = AnalysisResult.query.join(
            Sample, Sample.id == AnalysisResult.sample_id
        ).filter(
            Sample.lab_type.in_(_MICRO_LAB_TYPES),
            AnalysisResult.analysis_code.in_(_MICRO_CODES),
            AnalysisResult.created_at >= m_start,
            AnalysisResult.created_at < m_end
        ).count()
        monthly_stats.append({'month': m, 'year': y, 'label': f'{m}-р сар', 'count': cnt})

    return render_template(
        'reports/micro_dashboard.html',
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
        'reports/micro_consumption.html',
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
    except Exception:
        return jsonify({'success': False, 'error': 'параметр буруу'}), 400

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

    plans_db = M.MonthlyPlan.query.filter_by(year=year, month=month).filter(
        M.MonthlyPlan.client_name.in_(_MICRO_CODES)
    ).all()
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

    staff_settings = M.StaffSettings.query.filter_by(year=year, month=month).first()
    staff_count = staff_settings.preparers if staff_settings else 3

    return render_template(
        'reports/micro_monthly_plan.html',
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
    plans = M.MonthlyPlan.query.filter_by(year=year, month=month).filter(
        M.MonthlyPlan.client_name.in_(_MICRO_CODES)
    ).all()
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
        return jsonify({'error': 'Зөвхөн ахлах эрхтэй'}), 403

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
        existing = M.MonthlyPlan.query.filter_by(
            year=year, month=month, week=week,
            client_name=client_name, sample_type=sample_type
        ).first()
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
        return jsonify({'error': 'Зөвхөн ахлах эрхтэй'}), 403

    req_data = request.get_json()
    year = req_data.get('year')
    month = req_data.get('month')
    count = req_data.get('staff_count', 3)
    if not year or not month:
        return jsonify({'error': 'year and month required'}), 400

    existing = M.StaffSettings.query.filter_by(year=year, month=month).first()
    if existing:
        existing.preparers = count
        existing.updated_at = now_local()
    else:
        db.session.add(M.StaffSettings(year=year, month=month, preparers=count, chemists=count))
    db.session.commit()
    return jsonify({'success': True})
