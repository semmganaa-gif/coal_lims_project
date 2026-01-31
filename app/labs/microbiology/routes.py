# app/labs/microbiology/routes.py
"""Микробиологийн лабораторийн routes."""

import os
import json
from datetime import datetime, date
from flask import Blueprint, render_template, jsonify, request
from flask_login import login_required, current_user
from app import db
from app.models import Sample, AnalysisResult
from app.labs.microbiology.constants import ALL_MICRO_PARAMS, MICRO_ANALYSIS_TYPES

_template_dir = os.path.join(os.path.dirname(__file__), 'templates')
micro_bp = Blueprint(
    'microbiology',
    __name__,
    template_folder=_template_dir,
    url_prefix='/labs/microbiology'
)


@micro_bp.route('/')
@login_required
def micro_hub():
    """Микробиологийн лабораторийн төв хуудас."""
    return render_template(
        'micro_hub.html',
        title='Микробиологийн лаборатори',
        analysis_types=MICRO_ANALYSIS_TYPES,
        params=ALL_MICRO_PARAMS,
    )


@micro_bp.route('/workspace/<code>')
@login_required
def workspace(code):
    """Шинжилгээний ажлын талбар (категориор)."""
    code_upper = code.upper()

    # Category-р workspace нээх
    from app.labs.microbiology.constants import (
        WATER_MICRO_PARAMS, AIR_MICRO_PARAMS, SURFACE_MICRO_PARAMS,
        AIR_SAMPLE_NAMES, SURFACE_SAMPLE_NAMES
    )

    category_map = {
        'WATER': {'params': WATER_MICRO_PARAMS, 'title': 'Усны микробиологи', 'category': 'water'},
        'AIR': {'params': AIR_MICRO_PARAMS, 'title': 'Агаарын микробиологи', 'category': 'air',
                'sample_names': AIR_SAMPLE_NAMES},
        'SURFACE': {'params': SURFACE_MICRO_PARAMS, 'title': 'Гадаргуугийн микробиологи', 'category': 'surface',
                    'sample_names': SURFACE_SAMPLE_NAMES},
    }

    # Шууд код (CFU_W, ECOLI_W гэх мэт) эсвэл категори (WATER, AIR, SURFACE)
    if code_upper in category_map:
        cat_info = category_map[code_upper]
        return render_template(
            'analysis_forms/micro_workspace.html',
            title=cat_info['title'],
            category=cat_info['category'],
            params=cat_info['params'],
            sample_names=cat_info.get('sample_names', []),
        )

    # Хуучин кодоор хандах → категори руу redirect
    param = ALL_MICRO_PARAMS.get(code_upper)
    if not param:
        return jsonify({'error': f'Unknown analysis code: {code}'}), 404

    # Find category from MICRO_ANALYSIS_TYPES
    cat = 'water'
    for at in MICRO_ANALYSIS_TYPES:
        if at['code'] == code_upper:
            cat = at.get('category', 'water')
            break

    from flask import redirect, url_for as _url_for
    return redirect(_url_for('microbiology.workspace', code=cat.upper()))


# ============ API endpoints ============

@micro_bp.route('/api/samples')
@login_required
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


def _get_or_create_micro_sample(category, sample_code, sample_date_str):
    """Микробиологийн дээж хайх эсвэл үүсгэх.

    Water: sample_code-р хайна.
    Air/Surface: Огноо+категориор автомат дээж үүсгэнэ.
    """
    if category == 'water':
        if not sample_code:
            return None
        sample = Sample.query.filter_by(sample_code=sample_code).first()
        return sample
    else:
        # Air/Surface: auto-generate sample code from date + category
        today_str = sample_date_str or date.today().isoformat()
        prefix = 'CM-AIR' if category == 'air' else 'CM-SUR'
        auto_code = f'{prefix}-{today_str}'

        sample = Sample.query.filter_by(sample_code=auto_code).first()
        if not sample:
            sample = Sample(
                sample_code=auto_code,
                lab_type='microbiology',
                status='analysis',
                sample_date=datetime.strptime(today_str, '%Y-%m-%d').date() if today_str else date.today(),
                client_name='LAB',
                user_id=current_user.id,
            )
            db.session.add(sample)
            db.session.flush()
        return sample


@micro_bp.route('/api/save_batch', methods=['POST'])
@login_required
def save_batch():
    """Багцаар үр дүн хадгалах (workspace grid-ээс)."""
    data = request.get_json()
    if not data or not data.get('rows'):
        return jsonify({'error': 'No data provided'}), 400

    category = data.get('category', 'water')
    rows = data['rows']
    saved = 0
    errors = []

    for row in rows:
        sample_code = row.get('sample_code', '').strip()
        if not sample_code:
            continue

        # Build result dict (only non-empty fields)
        results = {}
        for key in ['bbet_s1', 'bbet_s2', 'bbet_avg', 'ecoli', 'gbet', 'gbet_thermo',
                     'cfu_air', 'staph', 'cfu_surface', 'ecoli_s', 'salm_s']:
            if row.get(key) is not None and row.get(key) != '':
                results[key] = row[key]

        if not results:
            continue

        # Get or create sample
        sample = _get_or_create_micro_sample(category, sample_code, row.get('start_date'))
        if not sample:
            errors.append(f'Дээж олдсонгүй: {sample_code}')
            continue

        analysis_code = f'MICRO_{category.upper()}'
        raw = json.dumps({
            'sample_code': sample_code,
            'start_date': row.get('start_date'),
            'end_date': row.get('end_date'),
            'category': category,
            **results,
        }, ensure_ascii=False)

        # Upsert: update if exists, insert if not
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
def load_batch():
    """Хадгалсан үр дүнг ачаалах.

    GET /api/load_batch?category=water&date=2026-01-31
    """
    category = request.args.get('category', 'water')
    date_str = request.args.get('date')
    analysis_code = f'MICRO_{category.upper()}'

    query = AnalysisResult.query.filter_by(analysis_code=analysis_code)

    if date_str:
        # Filter by date in raw_data (start_date field)
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

    # Reverse so oldest first (natural order)
    rows.reverse()
    return jsonify({'rows': rows})


@micro_bp.route('/api/data')
@login_required
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
