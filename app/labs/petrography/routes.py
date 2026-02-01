# app/labs/petrography/routes.py
"""Петрограф лабораторийн routes."""

import os
from flask import Blueprint, render_template, jsonify, request
from flask_login import login_required, current_user
from app import db
from app.models import Sample, AnalysisResult, AnalysisType
from app.labs.petrography.constants import ALL_PETRO_PARAMS, PETRO_ANALYSIS_TYPES

# Template folder тохируулах
_template_dir = os.path.join(os.path.dirname(__file__), 'templates')
petro_bp = Blueprint(
    'petrography',
    __name__,
    template_folder=_template_dir,
    url_prefix='/labs/petrography'
)


@petro_bp.route('/')
@login_required
def petro_hub():
    """Петрограф лабораторийн төв хуудас."""
    # PE дээжүүд (нүүрсний лаб-аас ирсэн)
    pending_pe = Sample.query.filter(
        Sample.sample_type == 'PE',
        Sample.status.in_(['new', 'in_progress', 'analysis'])
    ).count()
    # Петрограф лабын дээжүүд
    total_petro = Sample.query.filter_by(lab_type='petrography').count()
    in_progress = Sample.query.filter(
        Sample.lab_type == 'petrography',
        Sample.status.in_(['in_progress', 'analysis', 'prepared'])
    ).count()
    completed = Sample.query.filter(
        Sample.lab_type == 'petrography',
        Sample.status == 'completed'
    ).count()
    return render_template(
        'petro_hub.html',
        title='Петрограф лаборатори',
        analysis_types=PETRO_ANALYSIS_TYPES,
        params=ALL_PETRO_PARAMS,
        pending_pe=pending_pe,
        total_petro=total_petro,
        in_progress=in_progress,
        completed=completed,
    )


@petro_bp.route('/workspace/<code>')
@login_required
def workspace(code):
    """Шинжилгээний ажлын талбар."""
    code_upper = code.upper()
    param = ALL_PETRO_PARAMS.get(code_upper)
    if not param:
        return jsonify({'error': f'Unknown analysis code: {code}'}), 404

    # Форм template mapping
    form_templates = {
        'MAC': 'analysis_forms/maceral_form.html',
        'VR': 'analysis_forms/vitrinite_form.html',
        'MM': 'analysis_forms/mineral_form.html',
        'TS': 'analysis_forms/thin_section_form.html',
        'MOD': 'analysis_forms/mineral_form.html',
        'TEX': 'analysis_forms/thin_section_form.html',
        'GS': 'analysis_forms/mineral_form.html',
    }

    template = form_templates.get(code_upper, 'analysis_forms/maceral_form.html')
    return render_template(
        template,
        title=f'{param["name_mn"]} - Ажлын талбар',
        analysis_code=code_upper,
        param=param,
        use_aggrid=True,
    )


# ============ API endpoints ============

@petro_bp.route('/api/eligible/<code>')
@login_required
def eligible_samples(code):
    """Боломжит дээж (петрограф шинжилгээнд).

    PE sample_type-тай coal дээж + petrography lab дээж хоёуланг харуулна.
    """
    from sqlalchemy import or_
    samples = Sample.query.filter(
        or_(
            # Нүүрсний лаб-аас PE гэж бүртгэгдсэн дээжүүд
            db.and_(Sample.sample_type == 'PE', Sample.status.in_(['new', 'in_progress', 'analysis', 'prepared'])),
            # Петрограф лабын дээжүүд
            db.and_(Sample.lab_type == 'petrography', Sample.status.in_(['new', 'in_progress', 'analysis', 'prepared'])),
        )
    ).order_by(Sample.received_date.desc()).all()
    result = []
    for s in samples:
        result.append({
            'id': s.id,
            'sample_code': s.sample_code,
            'client_name': s.client_name,
            'sample_date': s.sample_date.isoformat() if s.sample_date else None,
        })
    return jsonify(result)


@petro_bp.route('/api/save_results', methods=['POST'])
@login_required
def save_results():
    """Үр дүн хадгалах."""
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data provided'}), 400

    sample_id = data.get('sample_id')
    analysis_code = data.get('analysis_code')
    results = data.get('results', {})

    sample = db.session.get(Sample, sample_id)
    if not sample:
        return jsonify({'error': 'Sample not found'}), 404

    # Үр дүнг хадгалах
    import json
    ar = AnalysisResult(
        sample_id=sample_id,
        analysis_type=analysis_code,
        result_value=json.dumps(results, ensure_ascii=False),
        chemist=current_user.username,
    )
    db.session.add(ar)
    db.session.commit()

    return jsonify({'success': True, 'id': ar.id})


@petro_bp.route('/api/data')
@login_required
def petro_data():
    """Петрограф дээжийн жагсаалт."""
    samples = Sample.query.filter_by(lab_type='petrography').order_by(
        Sample.received_date.desc()
    ).limit(200).all()

    result = []
    for s in samples:
        result.append({
            'id': s.id,
            'sample_code': s.sample_code,
            'client_name': s.client_name,
            'status': s.status,
            'sample_date': s.sample_date.isoformat() if s.sample_date else None,
            'received_date': s.received_date.isoformat() if s.received_date else None,
        })
    return jsonify(result)
