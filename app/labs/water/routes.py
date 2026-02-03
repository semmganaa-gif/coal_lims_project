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
        Sample.lab_type.in_(['water', 'microbiology', 'water & micro'])
    ).count()
    return render_template(
        'water_analysis_hub.html',
        title='Усны шинжилгээний төв',
        analysis_types=WATER_ANALYSIS_TYPES,
        params=ALL_WATER_PARAMS,
        sample_count=sample_count,
    )


@water_bp.route('/summary', methods=['GET', 'POST'])
@login_required
@lab_required('water')
def water_summary():
    """Усны хими + микробиологийн нэгдсэн үр дүнгийн нэгтгэл."""
    # POST: Архивлах
    if request.method == 'POST':
        action = request.form.get('action')
        sample_ids_str = request.form.get('sample_ids')
        if sample_ids_str and action == 'archive':
            from app.services import archive_samples
            sample_ids = [int(sid) for sid in sample_ids_str.split(',') if sid.isdigit()]
            result = archive_samples(sample_ids, archive=True)
            flash(result.message, 'success' if result.success else 'danger')
        return redirect(url_for('water.water_summary'))

    return render_template(
        'water_summary.html',
        title='Усны шинжилгээний үр дүнгийн нэгтгэл',
    )


@water_bp.route('/archive', methods=['GET', 'POST'])
@login_required
@lab_required('water')
def water_archive():
    """Усны архив хуудас."""
    # POST: Сэргээх
    if request.method == 'POST':
        action = request.form.get('action')
        sample_ids_str = request.form.get('sample_ids')
        if sample_ids_str and action == 'unarchive':
            from app.services import archive_samples
            sample_ids = [int(sid) for sid in sample_ids_str.split(',') if sid.isdigit()]
            result = archive_samples(sample_ids, archive=False)
            flash(result.message, 'success' if result.success else 'danger')
        return redirect(url_for('water.water_archive'))

    archived_count = Sample.query.filter(
        Sample.lab_type.in_(['water', 'microbiology', 'water & micro']),
        Sample.status == 'archived'
    ).count()

    return render_template(
        'water_archive.html',
        title='Усны архив',
        archived_count=archived_count,
    )


@water_bp.route('/api/archive_data')
@login_required
@lab_required('water')
def archive_data():
    """Архивлагдсан усны дээжүүд + шинжилгээний үр дүн."""
    import re
    import json as _json

    lab_type_filter = request.args.get('lab_type', 'all')

    q = Sample.query.filter(Sample.status == 'archived')

    if lab_type_filter == 'water':
        q = q.filter(Sample.lab_type == 'water')
    elif lab_type_filter == 'microbiology':
        q = q.filter(Sample.lab_type == 'microbiology')
    elif lab_type_filter == 'water & micro':
        q = q.filter(Sample.lab_type == 'water & micro')
    else:
        q = q.filter(Sample.lab_type.in_(['water', 'microbiology', 'water & micro']))

    samples = q.order_by(Sample.sample_date.desc(), Sample.id.desc()).limit(500).all()

    # Тоо тоолох
    all_archived = Sample.query.filter(
        Sample.lab_type.in_(['water', 'microbiology', 'water & micro']),
        Sample.status == 'archived'
    ).all()
    water_count = sum(1 for s in all_archived if s.lab_type == 'water')
    micro_count = sum(1 for s in all_archived if s.lab_type == 'microbiology')
    combined_count = sum(1 for s in all_archived if s.lab_type == 'water & micro')

    if not samples:
        return jsonify({
            'rows': [],
            'water_count': water_count,
            'micro_count': micro_count,
            'combined_count': combined_count,
            'total_count': len(all_archived),
        })

    sample_ids = [s.id for s in samples]

    # ── Химийн идэвхтэй анализ кодууд ──
    active_chem_codes = [
        a['code'] for a in WATER_ANALYSIS_TYPES
        if 'archive' not in a.get('categories', [])
    ]

    # ── Бүх үр дүн (хими + микро) ──
    all_codes = active_chem_codes + ['MICRO_WATER']
    results = AnalysisResult.query.filter(
        AnalysisResult.sample_id.in_(sample_ids),
        AnalysisResult.analysis_code.in_(all_codes),
    ).all()

    # sample_id → { code → value } (хими)
    # sample_id → { micro fields } (микро)
    chem_map = {}
    micro_map = {}
    for r in results:
        try:
            raw = _json.loads(r.raw_data) if isinstance(r.raw_data, str) else (r.raw_data or {})
        except (ValueError, TypeError):
            raw = {}

        if r.analysis_code == 'MICRO_WATER':
            micro_map[r.sample_id] = raw
        else:
            if r.sample_id not in chem_map:
                chem_map[r.sample_id] = {}
            val = raw.get('value') or raw.get('result') or raw.get('average') or r.final_result
            chem_map[r.sample_id][r.analysis_code] = val

    rows = []
    for s in samples:
        display_name = s.sample_code
        m = re.match(r'^(\d{2}_\d{2})_(.+)_(\d{4}-\d{2}-\d{2})$', s.sample_code)
        if m:
            display_name = m.group(2)
        else:
            m2 = re.match(r'^(.+)_(\d{4}-\d{2}-\d{2})$', s.sample_code)
            if m2:
                display_name = m2.group(1)

        row = {
            'sample_id': s.id,
            'sample_code': s.sample_code,
            'sample_name': display_name,
            'sample_date': s.sample_date.isoformat() if s.sample_date else '',
            'received_date': s.received_date.strftime('%Y-%m-%d') if s.received_date else '',
            'chem_lab_id': s.chem_lab_id or '',
            'micro_lab_id': s.micro_lab_id or '',
            'client_name': s.client_name or '',
            'lab_type': s.lab_type or '',
        }
        # Хими
        cres = chem_map.get(s.id, {})
        for code in active_chem_codes:
            row[code] = cres.get(code)
        # Микро
        mres = micro_map.get(s.id, {})
        row['cfu_22'] = mres.get('cfu_22')
        row['cfu_37'] = mres.get('cfu_37')
        row['cfu_avg'] = mres.get('cfu_avg')
        row['ecoli'] = mres.get('ecoli')
        row['salmonella'] = mres.get('salmonella')
        row['air_cfu'] = mres.get('air_cfu')
        row['staph'] = mres.get('staph')

        rows.append(row)

    return jsonify({
        'rows': rows,
        'water_count': water_count,
        'micro_count': micro_count,
        'combined_count': combined_count,
        'total_count': len(all_archived),
    })


@water_bp.route('/api/summary_data')
@login_required
@lab_required('water')
def summary_data():
    """Усны хими + микробиологийн үр дүнг нэгтгэж буцаана."""
    import json as _json
    from datetime import datetime as _dt

    date_from = request.args.get('date_from')
    date_to = request.args.get('date_to')

    # Ус + микро дээжүүд (архивлагдаагүй)
    q = Sample.query.filter(
        Sample.lab_type.in_(['water', 'microbiology', 'water & micro']),
        Sample.status != 'archived'
    )
    if date_from:
        q = q.filter(Sample.sample_date >= _dt.strptime(date_from, '%Y-%m-%d').date())
    if date_to:
        q = q.filter(Sample.sample_date <= _dt.strptime(date_to, '%Y-%m-%d').date())
    samples = q.order_by(Sample.sample_date.desc(), Sample.id.desc()).limit(300).all()
    if not samples:
        return jsonify({'rows': [], 'chem_params': [], 'micro_fields': []})

    sample_ids = [s.id for s in samples]

    # ── Химийн идэвхтэй анализ кодууд ──
    active_chem_codes = [
        a['code'] for a in WATER_ANALYSIS_TYPES
        if 'archive' not in a.get('categories', [])
    ]

    # ── Бүх үр дүн (хими + микро) нэг query ──
    all_codes = active_chem_codes + ['MICRO_WATER']
    results = AnalysisResult.query.filter(
        AnalysisResult.sample_id.in_(sample_ids),
        AnalysisResult.analysis_code.in_(all_codes),
    ).all()

    # sample_id → { code → value } (хими)
    # sample_id → { micro fields } (микро)
    chem_map = {}
    micro_map = {}
    for r in results:
        try:
            raw = _json.loads(r.raw_data) if isinstance(r.raw_data, str) else (r.raw_data or {})
        except (ValueError, TypeError):
            raw = {}

        if r.analysis_code == 'MICRO_WATER':
            # Микро raw_data: {cfu_22, cfu_37, ecoli, salmonella, ...}
            micro_map[r.sample_id] = raw
        else:
            if r.sample_id not in chem_map:
                chem_map[r.sample_id] = {}
            val = raw.get('value') or raw.get('result') or raw.get('average') or r.final_result
            chem_map[r.sample_id][r.analysis_code] = val

    import re
    rows = []
    for s in samples:
        display_name = s.sample_code
        m = re.match(r'^(\d{2}_\d{2})_(.+)_(\d{4}-\d{2}-\d{2})$', s.sample_code)
        if m:
            display_name = m.group(2)
        else:
            m2 = re.match(r'^(.+)_(\d{4}-\d{2}-\d{2})$', s.sample_code)
            if m2:
                display_name = m2.group(1)

        row = {
            'sample_id': s.id,
            'sample_code': s.sample_code,
            'sample_name': display_name,
            'sample_date': s.sample_date.isoformat() if s.sample_date else '',
            'received_date': s.received_date.strftime('%Y-%m-%d') if s.received_date else '',
            'chem_lab_id': s.chem_lab_id or '',
            'micro_lab_id': s.micro_lab_id or '',
            'client_name': s.client_name or '',
        }
        # Хими
        cres = chem_map.get(s.id, {})
        for code in active_chem_codes:
            row[code] = cres.get(code)
        # Микро
        mres = micro_map.get(s.id, {})
        row['cfu_22'] = mres.get('cfu_22')
        row['cfu_37'] = mres.get('cfu_37')
        row['cfu_avg'] = mres.get('cfu_avg')
        row['ecoli'] = mres.get('ecoli')
        row['salmonella'] = mres.get('salmonella')

        rows.append(row)

    # Химийн параметр мэдээлэл
    chem_params = []
    for code in active_chem_codes:
        p = ALL_WATER_PARAMS.get(code, {})
        chem_params.append({
            'code': code,
            'name': p.get('name_mn', code),
            'unit': p.get('unit', ''),
            'mns_limit': p.get('mns_limit'),
        })

    # Микро баганууд
    micro_fields = [
        {'code': 'cfu_22', 'name': 'CFU 22°C', 'unit': 'CFU/мл', 'mns_limit': [None, 100]},
        {'code': 'cfu_37', 'name': 'CFU 37°C', 'unit': 'CFU/мл', 'mns_limit': [None, 100]},
        {'code': 'cfu_avg', 'name': 'CFU дундаж', 'unit': 'CFU/мл', 'mns_limit': [None, 100]},
        {'code': 'ecoli', 'name': 'E.coli', 'unit': '100мл', 'mns_limit': None, 'detect': True},
        {'code': 'salmonella', 'name': 'Salmonella', 'unit': '25мл', 'mns_limit': None, 'detect': True},
    ]

    return jsonify({'rows': rows, 'chem_params': chem_params, 'micro_fields': micro_fields})


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
                return redirect(url_for('microbiology.register_sample'))
            return redirect(url_for('water.register_sample'))
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
    import json as _json
    code_upper = code.upper()
    param = ALL_WATER_PARAMS.get(code_upper)
    if not param:
        return jsonify({'error': f'Unknown analysis code: {code}'}), 404

    form_templates = {
        # Шууд хэмжилт
        'PH': 'analysis_forms/ph_ec_form.html',
        'EC': 'analysis_forms/ph_ec_form.html',
        'TEMP': 'analysis_forms/ph_ec_form.html',
        'F_W': 'analysis_forms/ph_ec_form.html',
        'CL_FREE': 'analysis_forms/ph_ec_form.html',
        'DS': 'analysis_forms/ph_ec_form.html',
        'TURB': 'analysis_forms/ph_ec_form.html',
        'DUST': 'analysis_forms/ph_ec_form.html',
        'SLUDGE': 'analysis_forms/ph_ec_form.html',
        'BOD': 'analysis_forms/ph_ec_form.html',
        'COD': 'analysis_forms/ph_ec_form.html',
        'DO_W': 'analysis_forms/ph_ec_form.html',
        'CA': 'analysis_forms/ph_ec_form.html',
        'MG': 'analysis_forms/ph_ec_form.html',
        'ALK': 'analysis_forms/ph_ec_form.html',
        # Спектрофотометр
        'NH4': 'analysis_forms/spectro_form.html',
        'NO2': 'analysis_forms/spectro_form.html',
        'NO3': 'analysis_forms/spectro_form.html',
        'FE_W': 'analysis_forms/spectro_form.html',
        'COLOR': 'analysis_forms/spectro_form.html',
        'PO4': 'analysis_forms/spectro_form.html',
        # Титрлэлт
        'HARD': 'analysis_forms/titration_form.html',
        'CL_W': 'analysis_forms/titration_form.html',
        # Жингийн арга
        'TDS': 'analysis_forms/gravimetric_form.html',
        # Архив
        'MN_W': 'analysis_forms/spectro_form.html',
        'CU_W': 'analysis_forms/spectro_form.html',
        'ZN_W': 'analysis_forms/spectro_form.html',
        'PB_W': 'analysis_forms/spectro_form.html',
        'AS_W': 'analysis_forms/spectro_form.html',
        'CD_W': 'analysis_forms/spectro_form.html',
        'CR_W': 'analysis_forms/spectro_form.html',
        'HG_W': 'analysis_forms/spectro_form.html',
        'SO4': 'analysis_forms/spectro_form.html',
        'CN_W': 'analysis_forms/spectro_form.html',
        'TSS': 'analysis_forms/ph_ec_form.html',
    }

    # ── Дээж бэлтгэх (нүүрсний лабын загвараар) ──
    newly_selected_ids_str = request.args.get('sample_ids', '')
    new_ids = [int(x) for x in newly_selected_ids_str.split(',') if x.isdigit()]

    # Approved дээжүүдийг хасах
    approved_ids = {r.sample_id for r in db.session.query(AnalysisResult.sample_id).filter(
        AnalysisResult.analysis_code == code_upper,
        AnalysisResult.status == 'approved'
    ).distinct().all()}

    # Хуучин хадгалагдсан (pending/rejected) + шинэ сонгосон
    seen = set()
    samples_to_analyze = []

    # A: Одоо байгаа үр дүнтэй дээжүүд
    existing_results_q = AnalysisResult.query.filter(
        AnalysisResult.user_id == current_user.id,
        AnalysisResult.analysis_code == code_upper,
        ~AnalysisResult.sample_id.in_(approved_ids) if approved_ids else True
    ).all()
    for r in existing_results_q:
        if r.sample_id not in seen:
            s = db.session.get(Sample, r.sample_id)
            if s:
                samples_to_analyze.append(s)
                seen.add(r.sample_id)

    # B: Шинэ сонгосон
    if new_ids:
        new_samples = Sample.query.filter(Sample.id.in_(new_ids)).all()
        smap = {s.id: s for s in new_samples}
        for sid in new_ids:
            if sid not in seen and sid not in approved_ids and sid in smap:
                samples_to_analyze.append(smap[sid])
                seen.add(sid)

    # Existing results map
    existing_results_map = {}
    rejected_samples_info = {}
    if samples_to_analyze:
        sample_ids = [s.id for s in samples_to_analyze]
        results = AnalysisResult.query.filter(
            AnalysisResult.sample_id.in_(sample_ids),
            AnalysisResult.analysis_code == code_upper,
            AnalysisResult.status.in_(['pending_review', 'rejected'])
        ).all()
        for r in results:
            raw = r.raw_data
            if isinstance(raw, str):
                try:
                    raw = _json.loads(raw)
                except (ValueError, TypeError):
                    raw = {}
            elif raw is None:
                raw = {}

            if r.status == 'rejected':
                reason = getattr(r, 'rejection_comment', None) or 'Ахлах буцаасан'
                reason_code = getattr(r, 'rejection_category', None) or getattr(r, 'error_reason', None)
                rejected_samples_info[r.sample_id] = {
                    'reason': reason,
                    'reason_code': reason_code,
                }
                if reason_code != 'data_entry':
                    raw = {}

            existing_results_map[r.sample_id] = {
                'status': r.status,
                'raw_data': raw,
                'final_result': r.final_result,
            }

    template = form_templates.get(code_upper, 'analysis_forms/ph_ec_form.html')
    return render_template(
        template,
        title=f'{param["name_mn"]} - Ажлын талбар',
        analysis_code=code_upper,
        param=param,
        use_aggrid=True,
        samples=samples_to_analyze,
        aggrid_samples=samples_to_analyze,
        existing_results_map=existing_results_map,
        rejected_samples_info=rejected_samples_info,
        error_labels={},
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
    from datetime import datetime as _dt
    q = Sample.query.filter(
        Sample.lab_type.in_(['water', 'microbiology', 'water & micro'])
    )
    date_from = request.args.get('date_from')
    date_to = request.args.get('date_to')
    if date_from:
        q = q.filter(Sample.sample_date >= _dt.strptime(date_from, '%Y-%m-%d').date())
    if date_to:
        q = q.filter(Sample.sample_date <= _dt.strptime(date_to, '%Y-%m-%d').date())
    samples = q.order_by(Sample.id.desc()).limit(500).all()

    import re
    result = []
    for idx, s in enumerate(reversed(samples), 1):
        # display_name: sample_code-оос огноо, lab_id хассан нэр
        display_name = s.sample_code
        m = re.match(r'^(\d{2}_\d{2})_(.+)_(\d{4}-\d{2}-\d{2})$', s.sample_code)
        if m:
            display_name = m.group(2)
        else:
            m2 = re.match(r'^(.+)_(\d{4}-\d{2}-\d{2})$', s.sample_code)
            if m2:
                display_name = m2.group(1)

        # Нэгжийн нэр
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


@water_bp.route('/edit_sample/<int:sample_id>', methods=['GET', 'POST'])
@login_required
@lab_required('water')
def edit_sample(sample_id):
    """Усны дээж засах."""
    import json as _json
    sample = db.session.get(Sample, sample_id)
    if not sample:
        flash('Дээж олдсонгүй.', 'danger')
        return redirect(url_for('water.register_sample'))

    can_edit = current_user.role in ('admin', 'senior', 'chemist')
    if not can_edit:
        flash('Дээж засах эрх танд байхгүй.', 'warning')
        return redirect(url_for('water.register_sample'))

    analyses_list = WATER_ANALYSIS_TYPES + MICRO_ANALYSIS_TYPES
    try:
        current_analyses = _json.loads(sample.analyses_to_perform or '[]')
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
                    sample.analyses_to_perform = _json.dumps(selected_analyses)
                if code_changed or analyses_changed:
                    db.session.commit()
                    flash('Дээжний мэдээлэл шинэчлэгдлээ.', 'success')
                else:
                    flash('Өөрчлөлт хийгдээгүй.', 'info')
                return redirect(url_for('water.register_sample'))
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


@water_bp.route('/delete_samples', methods=['POST'])
@login_required
@lab_required('water')
def delete_samples():
    """Усны/микро дээж устгах (admin, senior эрхтэй)."""
    from app.utils.audit import log_audit

    sample_ids = request.form.getlist('sample_ids')
    if not sample_ids:
        flash('Устгах дээжээ сонгоно уу!', 'warning')
        return redirect(request.referrer or url_for('water.register_sample'))

    if current_user.role not in ('admin', 'senior', 'chemist'):
        flash('Дээж устгах эрх танд байхгүй.', 'danger')
        return redirect(request.referrer or url_for('water.register_sample'))

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

    return redirect(request.referrer or url_for('water.register_sample'))


@water_bp.route('/api/standards')
@login_required
@lab_required('water')
def standards():
    """MNS/WHO стандартын хязгаарууд."""
    return jsonify(get_mns_standards())


# ======================================================================
#  REPORTS: Dashboard
# ======================================================================

@water_bp.route('/reports/dashboard')
@login_required
@lab_required('water')
def water_dashboard():
    """Усны хими Dashboard - KPI, тренд."""
    from datetime import datetime
    from sqlalchemy import extract

    now = datetime.now()
    year = now.year
    month = now.month

    month_start = datetime(year, month, 1)
    month_end = datetime(year, month + 1, 1) if month < 12 else datetime(year + 1, 1, 1)
    year_start = datetime(year, 1, 1)
    year_end = datetime(year + 1, 1, 1)

    _WATER_LAB_TYPES = ['water', 'water & micro']

    # Дээжний тоо
    samples_month = Sample.query.filter(
        Sample.lab_type.in_(_WATER_LAB_TYPES),
        Sample.received_date >= month_start.date(),
        Sample.received_date < month_end.date()
    ).count()

    samples_year = Sample.query.filter(
        Sample.lab_type.in_(_WATER_LAB_TYPES),
        Sample.received_date >= year_start.date(),
        Sample.received_date < year_end.date()
    ).count()

    # Шинжилгээний тоо
    active_chem_codes = [a['code'] for a in WATER_ANALYSIS_TYPES if 'archive' not in a.get('categories', [])]

    analyses_month = AnalysisResult.query.join(
        Sample, Sample.id == AnalysisResult.sample_id
    ).filter(
        Sample.lab_type.in_(_WATER_LAB_TYPES),
        AnalysisResult.analysis_code.in_(active_chem_codes),
        AnalysisResult.created_at >= month_start,
        AnalysisResult.created_at < month_end
    ).count()

    analyses_year = AnalysisResult.query.join(
        Sample, Sample.id == AnalysisResult.sample_id
    ).filter(
        Sample.lab_type.in_(_WATER_LAB_TYPES),
        AnalysisResult.analysis_code.in_(active_chem_codes),
        AnalysisResult.created_at >= year_start,
        AnalysisResult.created_at < year_end
    ).count()

    # Категори тоо
    cat_counts = []
    cat_labels = {'Унд ахуй': 'Унд ахуй', 'Бохир ус': 'Бохир ус', 'Лаг': 'Лаг'}
    for unit_name in WATER_UNITS:
        cnt = Sample.query.filter(
            Sample.lab_type.in_(_WATER_LAB_TYPES),
            Sample.client_name == unit_name,
            Sample.received_date >= year_start.date(),
            Sample.received_date < year_end.date()
        ).count()
        if cnt > 0:
            cat_counts.append({'label': unit_name, 'count': cnt})

    # Pass/Fail тоолох (pH, MNS limit шалгалт)
    pass_count = 0
    fail_count = 0
    ph_results = AnalysisResult.query.join(
        Sample, Sample.id == AnalysisResult.sample_id
    ).filter(
        Sample.lab_type.in_(_WATER_LAB_TYPES),
        AnalysisResult.analysis_code == 'PH',
        AnalysisResult.created_at >= year_start,
        AnalysisResult.created_at < year_end
    ).all()

    import json
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

    # Сүүлийн 6 сарын тренд
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
            Sample.lab_type.in_(_WATER_LAB_TYPES),
            AnalysisResult.analysis_code.in_(active_chem_codes),
            AnalysisResult.created_at >= m_start,
            AnalysisResult.created_at < m_end
        ).count()
        monthly_stats.append({'month': m, 'year': y, 'label': f'{m}-р сар', 'count': cnt})

    return render_template(
        'reports/water_dashboard.html',
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
@lab_required('water')
def water_consumption():
    """Усны хими Consumption тайлан."""
    from datetime import datetime
    from sqlalchemy import extract
    from collections import defaultdict

    now = datetime.now()
    try:
        year = int(request.args.get('year', now.year))
    except (ValueError, TypeError):
        year = now.year

    _WATER_LAB_TYPES = ['water', 'water & micro']
    active_chem_codes = [a['code'] for a in WATER_ANALYSIS_TYPES if 'archive' not in a.get('categories', [])]

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
        'reports/water_consumption.html',
        title=f'Усны хими Consumption — {year}',
        year=year, data=view,
        grand_samples=grand_samples, grand_rows=grand_rows,
    )


@water_bp.route('/api/consumption_cell')
@login_required
@lab_required('water')
def api_consumption_cell():
    """Consumption drill-down."""
    from datetime import datetime
    from sqlalchemy import extract

    try:
        year = int(request.args.get('year'))
        month = int(request.args.get('month'))
        unit = request.args.get('unit', '')
        stype = request.args.get('stype', '')
        kind = request.args.get('kind', 'samples')
        code = request.args.get('code', '')
    except (ValueError, TypeError):
        return jsonify({'ok': False, 'items': []})

    _WATER_LAB_TYPES = ['water', 'water & micro']
    active_chem_codes = [a['code'] for a in WATER_ANALYSIS_TYPES if 'archive' not in a.get('categories', [])]

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
    return jsonify({'ok': True, 'items': items})


# ======================================================================
#  REPORTS: Monthly Plan
# ======================================================================

@water_bp.route('/reports/monthly_plan')
@login_required
@lab_required('water')
def water_monthly_plan():
    """Усны хими Monthly Plan."""
    from datetime import datetime, timedelta
    from calendar import monthrange
    from collections import defaultdict
    from sqlalchemy import extract

    now = datetime.now()
    try:
        year = int(request.args.get('year', now.year))
        month = int(request.args.get('month', now.month))
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

    _WATER_LAB_TYPES = ['water', 'water & micro']
    active_chem_codes = [a['code'] for a in WATER_ANALYSIS_TYPES if 'archive' not in a.get('categories', [])]

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
        'reports/water_monthly_plan.html',
        title='Water Monthly Plan',
        years=years, year=year, month=month, month_name=month_name,
        weeks=weeks, data=data,
        week_totals=week_totals, grand_total=grand_total,
        staff_count=staff_count,
    )


@water_bp.route('/api/save_monthly_plan', methods=['POST'])
@login_required
@lab_required('water')
def api_save_monthly_plan():
    """Monthly plan хадгалах."""
    if current_user.role not in ('senior', 'admin'):
        return jsonify({'success': False, 'error': 'Permission denied'})
    # TODO: Implement plan saving
    return jsonify({'success': True})


@water_bp.route('/api/save_staff', methods=['POST'])
@login_required
@lab_required('water')
def api_save_staff():
    """Staff count хадгалах."""
    if current_user.role not in ('senior', 'admin'):
        return jsonify({'success': False, 'error': 'Permission denied'})
    # TODO: Implement staff saving
    return jsonify({'success': True})
