# app/labs/water/routes.py
"""Усны лабораторийн routes."""

import os
from flask import Blueprint, render_template, jsonify, request, flash, redirect, url_for
from flask_login import login_required, current_user
from app import db
from app.models import Sample, AnalysisResult, AnalysisType
from app.labs.water.constants import (
    ALL_WATER_PARAMS, WATER_ANALYSIS_TYPES, WATER_UNITS,
    ALL_WATER_SAMPLE_NAMES, get_mns_standards
)
from app.labs.microbiology.constants import MICRO_ANALYSIS_TYPES
from app.utils.decorators import lab_required

_template_dir = os.path.join(os.path.dirname(__file__), 'templates')
water_bp = Blueprint(
    'water',
    __name__,
    template_folder=_template_dir,
    url_prefix='/labs/water'
)


@water_bp.route('/')
@login_required
@lab_required('water')
def water_hub():
    """Усны лабораторийн dashboard."""
    from app.labs import get_lab
    stats = get_lab('water').sample_stats()
    water_count = len(WATER_ANALYSIS_TYPES)
    micro_count = len(MICRO_ANALYSIS_TYPES)
    return render_template(
        'water_hub.html',
        title='Усны лаборатори',
        total_samples=stats['total'],
        new_samples=stats['new'],
        in_progress=stats['in_progress'],
        completed=stats['completed'],
        water_analysis_count=water_count,
        micro_analysis_count=micro_count,
    )


@water_bp.route('/analysis')
@login_required
@lab_required('water')
def water_analysis_hub():
    """Усны шинжилгээний төв (картууд)."""
    sample_count = Sample.query.filter(
        Sample.lab_type.in_(['water', 'microbiology'])
    ).count()
    return render_template(
        'water_analysis_hub.html',
        title='Усны шинжилгээний төв',
        analysis_types=WATER_ANALYSIS_TYPES,
        params=ALL_WATER_PARAMS,
        sample_count=sample_count,
    )


@water_bp.route('/register', methods=['GET', 'POST'])
@login_required
@lab_required('water')
def register_sample():
    """Усны дээж бүртгэх (Ус + Микробиологи дундын)."""
    if request.method == 'POST':
        sample_names = request.form.getlist('sample_codes')
        if not sample_names:
            flash('Дээжний нэр заавал сонгоно уу.', 'danger')
            return redirect(url_for('water.register_sample', **({'from': 'micro'} if request.args.get('from') == 'micro' else {})))

        from app.labs.water.utils import create_water_micro_samples
        try:
            created, skipped, n_analyses = create_water_micro_samples(request.form, current_user.id)
            if created:
                flash(f'{len(created)} дээж амжилттай бүртгэгдлээ! ({n_analyses} шинжилгээ)', 'success')
            if skipped:
                flash(f'{len(skipped)} дээж аль хэдийн бүртгэгдсэн: {", ".join(skipped)}', 'warning')
            if request.args.get('from') == 'micro' or request.form.get('from') == 'micro':
                return redirect(url_for('microbiology.micro_hub'))
            return redirect(url_for('water.water_hub'))
        except Exception as e:
            db.session.rollback()
            flash(f'Алдаа: {e}', 'danger')
            from_param = request.args.get('from', '')
            return redirect(url_for('water.register_sample', **({'from': 'micro'} if from_param == 'micro' else {})))

    return render_template(
        'water_register.html',
        title='Усны дээж бүртгэл',
        units=WATER_UNITS,
        total_samples=len(ALL_WATER_SAMPLE_NAMES),
        water_analyses=WATER_ANALYSIS_TYPES,
        micro_analyses=MICRO_ANALYSIS_TYPES,
        use_aggrid=True,
    )


@water_bp.route('/workspace/<code>')
@login_required
@lab_required('water')
def workspace(code):
    """Шинжилгээний ажлын талбар."""
    code_upper = code.upper()
    param = ALL_WATER_PARAMS.get(code_upper)
    if not param:
        return jsonify({'error': f'Unknown analysis code: {code}'}), 404

    form_templates = {
        'PH': 'analysis_forms/ph_ec_form.html',
        'EC': 'analysis_forms/ph_ec_form.html',
        'TEMP': 'analysis_forms/ph_ec_form.html',
        'FE_W': 'analysis_forms/metals_form.html',
        'MN_W': 'analysis_forms/metals_form.html',
        'CU_W': 'analysis_forms/metals_form.html',
        'ZN_W': 'analysis_forms/metals_form.html',
        'PB_W': 'analysis_forms/metals_form.html',
        'AS_W': 'analysis_forms/metals_form.html',
        'CD_W': 'analysis_forms/metals_form.html',
        'CR_W': 'analysis_forms/metals_form.html',
        'HG_W': 'analysis_forms/metals_form.html',
        'CL_W': 'analysis_forms/anions_form.html',
        'SO4': 'analysis_forms/anions_form.html',
        'NO3': 'analysis_forms/anions_form.html',
        'CN_W': 'analysis_forms/anions_form.html',
        'TURB': 'analysis_forms/physical_form.html',
        'TSS': 'analysis_forms/physical_form.html',
        'COLOR': 'analysis_forms/physical_form.html',
    }

    template = form_templates.get(code_upper, 'analysis_forms/ph_ec_form.html')
    return render_template(
        template,
        title=f'{param["name_mn"]} - Ажлын талбар',
        analysis_code=code_upper,
        param=param,
        use_aggrid=True,
    )


# ============ API endpoints ============

@water_bp.route('/api/eligible/<code>')
@login_required
@lab_required('water')
def eligible_samples(code):
    """Боломжит дээж (усны шинжилгээнд)."""
    samples = Sample.query.filter(
        Sample.lab_type == 'water',
        Sample.status.in_(['new', 'in_progress'])
    ).all()
    result = []
    for s in samples:
        result.append({
            'id': s.id,
            'sample_code': s.sample_code,
            'client_name': s.client_name,
            'sample_date': s.sample_date.isoformat() if s.sample_date else None,
        })
    return jsonify(result)


@water_bp.route('/api/save_results', methods=['POST'])
@login_required
@lab_required('water')
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

    import json
    ar = AnalysisResult(
        sample_id=sample_id,
        analysis_code=analysis_code,
        raw_data=json.dumps(results, ensure_ascii=False),
        user_id=current_user.id,
    )
    db.session.add(ar)

    from app.utils.database import safe_commit
    if not safe_commit():
        return jsonify({'error': 'Үр дүн хадгалахад алдаа гарлаа'}), 500

    return jsonify({'success': True, 'id': ar.id})


@water_bp.route('/api/data')
@login_required
@lab_required('water')
def water_data():
    """Усны дээжийн жагсаалт (ус + микробиологи)."""
    samples = Sample.query.filter(
        Sample.lab_type.in_(['water', 'microbiology'])
    ).order_by(Sample.id.desc()).limit(200).all()

    result = []
    for idx, s in enumerate(reversed(samples), 1):
        # Дээжний нэрийг огноогүй харуулах
        display_name = s.sample_code.rsplit('_', 1)[0] if '_' in s.sample_code else s.sample_code
        # Нэгжийн нэр
        unit_info = WATER_UNITS.get(s.client_name, {})
        unit_name = unit_info.get('name', s.client_name) if unit_info else s.client_name
        result.append({
            'seq': idx,
            'id': s.id,
            'sample_name': display_name,
            'sample_code': s.sample_code,
            'unit_name': unit_name,
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


@water_bp.route('/api/standards')
@login_required
@lab_required('water')
def standards():
    """MNS/WHO стандартын хязгаарууд."""
    return jsonify(get_mns_standards())
