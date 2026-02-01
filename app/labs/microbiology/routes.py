# app/labs/microbiology/routes.py
"""Микробиологийн лабораторийн routes."""

import os
import json
from datetime import datetime, date, timedelta
from flask import Blueprint, render_template, jsonify, request, flash, redirect, url_for
from flask_login import login_required, current_user
from app import db
from app.models import Sample, AnalysisResult
from app.labs.microbiology.constants import (
    ALL_MICRO_PARAMS, MICRO_ANALYSIS_TYPES,
    MICRO_WATER_FIELDS, MICRO_AIR_FIELDS, MICRO_SWAB_FIELDS,
)
from app.labs.water.constants import (
    WATER_ANALYSIS_TYPES, WATER_UNITS, ALL_WATER_SAMPLE_NAMES,
)
from app.utils.decorators import lab_required

_template_dir = os.path.join(os.path.dirname(__file__), 'templates')
micro_bp = Blueprint(
    'microbiology',
    __name__,
    template_folder=_template_dir,
    url_prefix='/labs/microbiology'
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


@micro_bp.route('/summary')
@login_required
@lab_required('microbiology')
def summary():
    """Микробиологийн нэгтгэл хуудас."""
    return render_template('micro_summary.html', title='Микробиологийн нэгтгэл')


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

        from app.labs.water.utils import create_water_micro_samples
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

    return render_template(template, title=title, workspace_code=code_lower)


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
    from app.labs.microbiology.constants import CATEGORY_ANALYSIS_CODES

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
    samples = Sample.query.filter(
        Sample.lab_type.in_(['water', 'microbiology', 'water & micro'])
    ).order_by(Sample.id.desc()).limit(200).all()

    result = []
    for idx, s in enumerate(reversed(samples), 1):
        lab_id = ''
        display_name = s.sample_code
        m = re.match(r'^(\d{2}_\d{2})_(.+)_(\d{4}-\d{2}-\d{2})$', s.sample_code)
        if m:
            lab_id = m.group(1)
            display_name = m.group(2)
        else:
            m2 = re.match(r'^(.+)_(\d{4}-\d{2}-\d{2})$', s.sample_code)
            if m2:
                display_name = m2.group(1)

        result.append({
            'seq': idx,
            'id': s.id,
            'lab_id': lab_id,
            'sample_name': display_name,
            'sample_code': s.sample_code,
            'unit_name': s.client_name or '',
            'lab_type': s.lab_type,
            'status': s.status,
            'sample_date': s.sample_date.isoformat() if s.sample_date else None,
            'received_date': s.received_date.strftime('%Y-%m-%d %H:%M') if s.received_date else None,
            'sampled_by': s.sampled_by or '',
            'sampling_location': s.sampling_location or '',
            'weight': s.weight,
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
