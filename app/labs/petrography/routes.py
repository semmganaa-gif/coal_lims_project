# app/labs/petrography/routes.py
"""Петрограф лабораторийн routes."""

import json
from flask import Blueprint, render_template, jsonify, request
from flask_login import login_required, current_user
from markupsafe import escape as html_escape
from app import db
from app.models import Sample, AnalysisResult
from app.labs.petrography.constants import ALL_PETRO_PARAMS, PETRO_ANALYSIS_TYPES
from app.utils.decorators import lab_required
from app.routes.api.helpers import api_success, api_error

petro_bp = Blueprint(
    'petrography',
    __name__,
    url_prefix='/labs/petrography'
)


def _pe_samples(statuses):
    """Петрограф дээжүүдийг шүүх.

    2 нөхцлийн аль нэг:
    1. sample_type == 'PE' (PE төрлийн дээж)
    2. analyses_to_perform дотор 'PE' код байвал (шинжилгээний тохиргоогоор PE чек хийгдсэн)
    """
    from sqlalchemy import or_
    return Sample.query.filter(
        Sample.status.in_(statuses),
        or_(
            Sample.lab_type == 'petrography',
            Sample.sample_type == 'PE',
            Sample.analyses_to_perform.contains('"PE"'),
        )
    )


@petro_bp.route('/')
@login_required
@lab_required('petrography')
def petro_hub():
    """Петрограф лабораторийн төв хуудас."""
    all_statuses = ['new', 'in_progress', 'analysis', 'prepared', 'completed']
    pending_pe = _pe_samples(['new', 'in_progress', 'analysis']).count()
    total_petro = _pe_samples(all_statuses).count()
    in_progress = _pe_samples(['in_progress', 'analysis', 'prepared']).count()
    completed = _pe_samples(['completed']).count()
    return render_template(
        'labs/petrography/petro_hub.html',
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
@lab_required('petrography')
def workspace(code):
    """Шинжилгээний ажлын талбар."""
    code_upper = code.upper()
    param = ALL_PETRO_PARAMS.get(code_upper)
    if not param:
        return jsonify({'error': f'Unknown analysis code: {code}'}), 404

    # Форм template mapping
    form_templates = {
        'MAC': 'labs/petrography/analysis_forms/maceral_form.html',
        'VR': 'labs/petrography/analysis_forms/vitrinite_form.html',
        'MM': 'labs/petrography/analysis_forms/mineral_form.html',
        'TS_PETRO': 'labs/petrography/analysis_forms/thin_section_form.html',
        'MOD': 'labs/petrography/analysis_forms/mineral_form.html',
        'TEX': 'labs/petrography/analysis_forms/thin_section_form.html',
        'GS': 'labs/petrography/analysis_forms/mineral_form.html',
    }

    template = form_templates.get(code_upper, 'labs/petrography/analysis_forms/maceral_form.html')
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
@lab_required('petrography')
def eligible_samples(code):
    """Боломжит дээж (петрограф шинжилгээнд).

    Нүүрсний лаб-аас sample_type='PE' гэж бүртгэгдсэн дээжүүд.
    """
    # ✅ Pagination limit нэмсэн
    samples = _pe_samples(
        ['new', 'in_progress', 'analysis', 'prepared']
    ).order_by(Sample.received_date.desc()).limit(500).all()
    result = []
    for s in samples:
        result.append({
            'id': s.id,
            'sample_code': s.sample_code,
            # ✅ XSS сэргийлэлт: client_name escape
            'client_name': str(html_escape(s.client_name)) if s.client_name else None,
            'sample_date': s.sample_date.isoformat() if s.sample_date else None,
        })
    # ✅ API response format стандартчилсан
    return api_success(result)


@petro_bp.route('/api/save_results', methods=['POST'])
@login_required
@lab_required('petrography')
def save_results():
    """Үр дүн хадгалах."""
    data = request.get_json()
    if not data:
        return api_error('No data provided', status_code=400)

    sample_id = data.get('sample_id')
    analysis_code = data.get('analysis_code')
    results = data.get('results', {})

    # ✅ Input validation
    if not sample_id or not analysis_code:
        return api_error('sample_id and analysis_code are required', status_code=400)

    # ✅ analysis_code validation
    valid_codes = [a['code'] for a in PETRO_ANALYSIS_TYPES]
    if analysis_code.upper() not in valid_codes:
        return api_error(f'Invalid analysis_code: {analysis_code}', status_code=400)

    sample = db.session.get(Sample, sample_id)
    if not sample:
        return api_error('Sample not found', status_code=404)

    # Үр дүнг хадгалах
    try:
        ar = AnalysisResult(
            sample_id=sample_id,
            analysis_code=analysis_code.upper(),
            raw_data=json.dumps(results, ensure_ascii=False),
            user_id=current_user.id,
        )
        db.session.add(ar)

        from app.utils.database import safe_commit
        if not safe_commit():
            return api_error('Error saving results', status_code=500)

        return api_success({'id': ar.id}, 'Results saved')
    except Exception as e:
        db.session.rollback()
        return api_error(f'Error: {html_escape(str(e))}', status_code=500)


@petro_bp.route('/api/data')
@login_required
@lab_required('petrography')
def petro_data():
    """Петрограф дээжийн жагсаалт (PE төрлийн дээжүүд)."""
    samples = _pe_samples(
        ['new', 'in_progress', 'analysis', 'prepared', 'completed']
    ).order_by(Sample.received_date.desc()).limit(200).all()

    result = []
    for s in samples:
        result.append({
            'id': s.id,
            'sample_code': s.sample_code,
            # ✅ XSS сэргийлэлт
            'client_name': str(html_escape(s.client_name)) if s.client_name else None,
            'status': s.status,
            'sample_date': s.sample_date.isoformat() if s.sample_date else None,
            'received_date': s.received_date.isoformat() if s.received_date else None,
        })
    # ✅ API response format стандартчилсан
    return api_success(result)
