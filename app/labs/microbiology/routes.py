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
            return redirect(url_for('microbiology.micro_hub'))
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
    """Микробиологийн дээж (Ус+Микро)."""
    samples = Sample.query.filter(
        Sample.lab_type.in_(['water', 'microbiology'])
    ).order_by(Sample.id.desc()).limit(200).all()
    return jsonify([{
        'id': s.id,
        'sample_code': s.sample_code,
        'client_name': s.client_name,
        'status': s.status,
        'sample_date': s.sample_date.isoformat() if s.sample_date else None,
    } for s in samples])


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
