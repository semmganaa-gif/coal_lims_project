# app/labs/water_lab/chemistry/routes.py
"""Усны хими лабораторийн routes."""

from flask import Blueprint, render_template, jsonify, request, flash, redirect, url_for
from flask_login import login_required, current_user
from app import db
from app.models import Sample, AnalysisResult, Equipment
from sqlalchemy import or_
from app.labs.water_lab.chemistry.constants import (
    ALL_WATER_PARAMS, WATER_ANALYSIS_TYPES, WATER_UNITS,
    ALL_WATER_SAMPLE_NAMES, get_mns_standards
)
from app.labs.water_lab.microbiology.constants import MICRO_ANALYSIS_TYPES
from app.utils.decorators import lab_required
from app.utils.converters import to_float
from app.utils.security import escape_like_pattern
from markupsafe import escape as html_escape

water_bp = Blueprint(
    'water',
    __name__,
    url_prefix='/labs/water-lab/chemistry'
)


def _build_water_rows(samples, include_lab_type=False):
    """Дээжүүдийн хими + микро үр дүнг rows болгон цуглуулах (archive/summary дундын helper).

    Returns:
        (rows, active_chem_codes)
    """
    import re
    import json as _json

    if not samples:
        return [], []

    sample_ids = [s.id for s in samples]

    # ── Химийн идэвхтэй анализ кодууд ──
    active_chem_codes = [
        a['code'] for a in WATER_ANALYSIS_TYPES
        if 'archive' not in a.get('categories', [])
    ]

    # ── Бүх үр дүн (хими + микро) нэг query ──
    all_codes = active_chem_codes + ['MICRO_WATER', 'MICRO_AIR', 'MICRO_SWAB']
    results = AnalysisResult.query.filter(
        AnalysisResult.sample_id.in_(sample_ids),
        AnalysisResult.analysis_code.in_(all_codes),
    ).all()

    # sample_id → { code → value } (хими)
    # sample_id → { micro fields } (микро water + air + swab)
    chem_map = {}
    micro_map = {}
    air_map = {}
    swab_map = {}
    for r in results:
        try:
            raw = _json.loads(r.raw_data) if isinstance(r.raw_data, str) else (r.raw_data or {})
        except (ValueError, TypeError):
            raw = {}

        if r.analysis_code == 'MICRO_WATER':
            micro_map[r.sample_id] = raw
        elif r.analysis_code == 'MICRO_AIR':
            air_map[r.sample_id] = raw
        elif r.analysis_code == 'MICRO_SWAB':
            swab_map[r.sample_id] = raw
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
        }
        if include_lab_type:
            row['lab_type'] = s.lab_type or ''

        # Хими
        cres = chem_map.get(s.id, {})
        for code in active_chem_codes:
            row[code] = cres.get(code)
        # Микро (усны)
        mres = micro_map.get(s.id, {})
        row['cfu_22'] = mres.get('cfu_22')
        row['cfu_37'] = mres.get('cfu_37')
        # CFU дундаж - raw_data-д байвал авах, үгүй бол тооцоолох
        cfu_avg = mres.get('cfu_avg')
        if cfu_avg is None:
            c22 = mres.get('cfu_22')
            c37 = mres.get('cfu_37')
            if c22 is not None and c37 is not None:
                try:
                    cfu_avg = round((float(c22) + float(c37)) / 2)
                except (ValueError, TypeError):
                    cfu_avg = None
        # Агаарын микро (MICRO_AIR)
        ares = air_map.get(s.id, {})
        row['air_cfu'] = ares.get('cfu_air')
        # Арчдасны микро (MICRO_SWAB)
        sres = swab_map.get(s.id, {})
        # CFU дундаж - ус эсвэл арчдасаас авах (нэгтгэсэн)
        row['cfu_avg'] = cfu_avg or sres.get('cfu_swab')
        # E.coli, Salmonella, S.aureus - ус эсвэл арчдасаас авах (нэгтгэсэн)
        row['ecoli'] = mres.get('ecoli') or sres.get('ecoli_swab')
        row['salmonella'] = mres.get('salmonella') or sres.get('salmonella_swab')
        row['staph'] = ares.get('staphylococcus') or sres.get('staphylococcus_swab')

        rows.append(row)

    return rows, active_chem_codes


def _build_chem_params(active_chem_codes):
    """Химийн параметрүүдийн мэдээлэл (MNS limit-тэй) буцаах."""
    chem_params = []
    for code in active_chem_codes:
        p = ALL_WATER_PARAMS.get(code, {})
        chem_params.append({
            'code': code,
            'name': p.get('name_mn', code),
            'unit': p.get('unit', ''),
            'mns_limit': p.get('mns_limit'),
        })
    return chem_params


@water_bp.route('/')
@login_required
@lab_required('water')
def water_hub():
    """Усны хими лабораторийн dashboard."""
    from app.labs import get_lab
    stats = get_lab('water').sample_stats()
    water_count = len(WATER_ANALYSIS_TYPES)
    micro_count = len(MICRO_ANALYSIS_TYPES)
    return render_template(
        'labs/water/chemistry/water_hub.html',
        title='Хими лаборатори',
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
        'labs/water/chemistry/water_analysis_hub.html',
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
        'labs/water/chemistry/water_summary.html',
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
        'labs/water/chemistry/water_archive.html',
        title='Усны архив',
        archived_count=archived_count,
    )


@water_bp.route('/api/archive_data')
@login_required
@lab_required('water')
def archive_data():
    """Архивлагдсан усны дээжүүд + шинжилгээний үр дүн."""
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
    water_count = Sample.query.filter(
        Sample.lab_type == 'water',
        Sample.status == 'archived'
    ).count()
    micro_count = Sample.query.filter(
        Sample.lab_type == 'microbiology',
        Sample.status == 'archived'
    ).count()
    combined_count = Sample.query.filter(
        Sample.lab_type == 'water & micro',
        Sample.status == 'archived'
    ).count()
    total_archived = water_count + micro_count + combined_count

    if not samples:
        return jsonify({
            'rows': [],
            'chem_params': [],
            'water_count': water_count,
            'micro_count': micro_count,
            'combined_count': combined_count,
            'total_count': total_archived,
        })

    rows, active_chem_codes = _build_water_rows(samples, include_lab_type=True)

    return jsonify({
        'rows': rows,
        'chem_params': _build_chem_params(active_chem_codes),
        'water_count': water_count,
        'micro_count': micro_count,
        'combined_count': combined_count,
        'total_count': total_archived,
    })


@water_bp.route('/api/summary_data')
@login_required
@lab_required('water')
def summary_data():
    """Усны хими + микробиологийн үр дүнг нэгтгэж буцаана."""
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

    rows, active_chem_codes = _build_water_rows(samples)

    # Микро баганууд
    micro_fields = [
        {'code': 'cfu_22', 'name': 'CFU 22°C', 'unit': 'CFU/мл', 'mns_limit': [None, 100]},
        {'code': 'cfu_37', 'name': 'CFU 37°C', 'unit': 'CFU/мл', 'mns_limit': [None, 100]},
        {'code': 'cfu_avg', 'name': 'CFU дундаж', 'unit': 'CFU/мл', 'mns_limit': [None, 100]},
        {'code': 'ecoli', 'name': 'E.coli', 'unit': '100мл', 'mns_limit': None, 'detect': True},
        {'code': 'salmonella', 'name': 'Salmonella', 'unit': '25мл', 'mns_limit': None, 'detect': True},
    ]

    return jsonify({
        'rows': rows,
        'chem_params': _build_chem_params(active_chem_codes),
        'micro_fields': micro_fields,
    })


@water_bp.route('/register', methods=['GET', 'POST'])
@login_required
@lab_required('water')
def register_sample():
    """Усны дээж бүртгэх (Ус + Микробиологи дундын)."""
    if request.method == 'POST':
        sample_names = request.form.getlist('sample_codes')
        if not sample_names:
            flash('Please select a sample name.', 'danger')
            return redirect(url_for('water.register_sample', **({'from': 'micro'} if request.args.get('from') == 'micro' else {})))

        from app.labs.water_lab.chemistry.utils import create_water_micro_samples
        try:
            created, skipped, n_analyses = create_water_micro_samples(request.form, current_user.id)
            if created:
                flash(f'{len(created)} дээж registered successfully. ({n_analyses} шинжилгээ)', 'success')
            if skipped:
                flash(f'{len(skipped)} дээж аль хэдийн бүртгэгдсэн: {", ".join(skipped)}', 'warning')
            if request.args.get('from') == 'micro' or request.form.get('from') == 'micro':
                return redirect(url_for('microbiology.register_sample'))
            return redirect(url_for('water.register_sample'))
        except Exception as e:
            db.session.rollback()
            # ✅ XSS сэргийлэлт: exception message escape
            flash(f'Error: {html_escape(str(e))}', 'danger')
            from_param = request.args.get('from', '')
            return redirect(url_for('water.register_sample', **({'from': 'micro'} if from_param == 'micro' else {})))

    return render_template(
        'labs/water/chemistry/water_register.html',
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
        'PH': 'labs/water/chemistry/analysis_forms/ph_ec_form.html',
        'EC': 'labs/water/chemistry/analysis_forms/ph_ec_form.html',
        'TEMP': 'labs/water/chemistry/analysis_forms/ph_ec_form.html',
        'F_W': 'labs/water/chemistry/analysis_forms/ph_ec_form.html',
        'CL_FREE': 'labs/water/chemistry/analysis_forms/ph_ec_form.html',
        'DS': 'labs/water/chemistry/analysis_forms/ph_ec_form.html',
        'TURB': 'labs/water/chemistry/analysis_forms/ph_ec_form.html',
        'DUST': 'labs/water/chemistry/analysis_forms/ph_ec_form.html',
        'SLUDGE': 'labs/water/chemistry/analysis_forms/ph_ec_form.html',
        'BOD': 'labs/water/chemistry/analysis_forms/ph_ec_form.html',
        'COD': 'labs/water/chemistry/analysis_forms/ph_ec_form.html',
        'DO_W': 'labs/water/chemistry/analysis_forms/ph_ec_form.html',
        'CA': 'labs/water/chemistry/analysis_forms/ph_ec_form.html',
        'MG': 'labs/water/chemistry/analysis_forms/ph_ec_form.html',
        'ALK': 'labs/water/chemistry/analysis_forms/ph_ec_form.html',
        # Спектрофотометр
        'NH4': 'labs/water/chemistry/analysis_forms/nh4_form.html',
        'NO2': 'labs/water/chemistry/analysis_forms/no2_form.html',
        'NO3': 'labs/water/chemistry/analysis_forms/spectro_form.html',
        'FE_W': 'labs/water/chemistry/analysis_forms/spectro_form.html',
        'COLOR': 'labs/water/chemistry/analysis_forms/color_form.html',
        'PO4': 'labs/water/chemistry/analysis_forms/po4_form.html',
        # Титрлэлт
        'HARD': 'labs/water/chemistry/analysis_forms/titration_form.html',
        'CL_W': 'labs/water/chemistry/analysis_forms/cl_w_form.html',
        # Жингийн арга
        'TDS': 'labs/water/chemistry/analysis_forms/tds_form.html',
        # Архив
        'MN_W': 'labs/water/chemistry/analysis_forms/spectro_form.html',
        'CU_W': 'labs/water/chemistry/analysis_forms/spectro_form.html',
        'ZN_W': 'labs/water/chemistry/analysis_forms/spectro_form.html',
        'PB_W': 'labs/water/chemistry/analysis_forms/spectro_form.html',
        'AS_W': 'labs/water/chemistry/analysis_forms/spectro_form.html',
        'CD_W': 'labs/water/chemistry/analysis_forms/spectro_form.html',
        'CR_W': 'labs/water/chemistry/analysis_forms/spectro_form.html',
        'HG_W': 'labs/water/chemistry/analysis_forms/spectro_form.html',
        'SO4': 'labs/water/chemistry/analysis_forms/spectro_form.html',
        'CN_W': 'labs/water/chemistry/analysis_forms/spectro_form.html',
        'TSS': 'labs/water/chemistry/analysis_forms/ph_ec_form.html',
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

    template = form_templates.get(code_upper, 'labs/water/chemistry/analysis_forms/ph_ec_form.html')

    # Related equipments for this analysis
    # ✅ LIKE injection сэргийлэлт
    related_equipments = []
    try:
        safe_code = escape_like_pattern(code_upper)
        related_equipments = (
            Equipment.query
            .filter(
                or_(
                    Equipment.related_analysis.ilike(f'%{safe_code}%', escape='\\'),
                    Equipment.category == 'water'
                ),
                or_(Equipment.status.is_(None), Equipment.status != 'retired')
            )
            .order_by(Equipment.name.asc())
            .all()
        )
    except Exception:
        pass

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
        related_equipments=related_equipments,
    )


# ============ API endpoints ============

@water_bp.route('/api/eligible/<code>')
@login_required
@lab_required('water')
def eligible_samples(code):
    """Боломжит дээж (усны химийн шинжилгээнд)."""
    samples = Sample.query.filter(
        Sample.lab_type.in_(['water', 'water & micro']),  # microbiology хасагдсан
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
        return jsonify({'error': 'Error saving results'}), 500

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
        flash('Sample not found.', 'danger')
        return redirect(url_for('water.register_sample'))

    can_edit = current_user.role in ('admin', 'senior', 'chemist')
    if not can_edit:
        flash('You do not have permission to edit samples.', 'warning')
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
            flash('Sample code cannot be empty.', 'danger')
        elif code_changed and Sample.query.filter(
            Sample.sample_code == new_code, Sample.id != sample_id
        ).first():
            flash(f'"{new_code}" sample already registered.', 'danger')
        else:
            try:
                if code_changed:
                    sample.sample_code = new_code
                if analyses_changed:
                    sample.analyses_to_perform = _json.dumps(selected_analyses)
                if code_changed or analyses_changed:
                    db.session.commit()
                    flash('Sample information updated.', 'success')
                else:
                    flash('No changes were made.', 'info')
                return redirect(url_for('water.register_sample'))
            except Exception as e:
                db.session.rollback()
                # ✅ XSS сэргийлэлт
                flash(f'Error: {html_escape(str(e))}', 'danger')

    return render_template(
        'labs/water/chemistry/water_edit_sample.html',
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
        flash('Please select samples to delete!', 'warning')
        return redirect(request.referrer or url_for('water.register_sample'))

    if current_user.role not in ('admin', 'senior', 'chemist'):
        flash('You do not have permission to delete samples.', 'danger')
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
        flash(f'{deleted} samples deleted successfully.', 'success')
    if failed:
        flash(f'Error: {", ".join(failed)}', 'danger')

    return redirect(request.referrer or url_for('water.register_sample'))


@water_bp.route('/standards')
@login_required
@lab_required('water')
def standards():
    """MNS/WHO стандартын хуудас."""
    standards_data = get_mns_standards()
    return render_template('labs/water/chemistry/water_standards.html', standards=standards_data)


@water_bp.route('/api/standards')
@login_required
@lab_required('water')
def api_standards():
    """MNS/WHO стандартын хязгаарууд (API)."""
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
        'labs/water/chemistry/reports/water_consumption.html',
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
        return jsonify({'success': False, 'data': {'items': []}})

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
    return jsonify({'success': True, 'data': {'items': items}})


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
        'labs/water/chemistry/reports/water_monthly_plan.html',
        title='Water Monthly Plan',
        years=years, year=year, month=month, month_name=month_name,
        weeks=weeks, data=data,
        week_totals=week_totals, grand_total=grand_total,
        staff_count=staff_count,
    )


# ============================================================
# УУСМАЛ БЭЛДЭХ ДЭВТЭР (Solution Journal)
# Note: api_save_monthly_plan, api_save_staff → report_routes.py дээр бүрэн хэрэгжүүлсэн
# ============================================================

@water_bp.route('/solution_journal')
@login_required
@lab_required('water')
def solution_journal():
    """Уусмал бэлдэх дэвтэр - жагсаалт."""
    from app.models import SolutionPreparation
    from datetime import date, datetime, timedelta

    # Шүүлтүүр
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    status = request.args.get('status', 'all')

    query = SolutionPreparation.query

    if start_date:
        start_dt = datetime.strptime(start_date, '%Y-%m-%d').date()
        query = query.filter(SolutionPreparation.prepared_date >= start_dt)

    if end_date:
        end_dt = datetime.strptime(end_date, '%Y-%m-%d').date()
        query = query.filter(SolutionPreparation.prepared_date <= end_dt)

    if status and status != 'all':
        query = query.filter(SolutionPreparation.status == status)

    solutions = query.order_by(SolutionPreparation.prepared_date.desc()).all()

    # Статистик
    today = date.today()
    stats = {
        'total': SolutionPreparation.query.count(),
        'active': SolutionPreparation.query.filter_by(status='active').count(),
        'expired': SolutionPreparation.query.filter(
            SolutionPreparation.expiry_date < today
        ).count() if SolutionPreparation.query.first() else 0,
    }

    return render_template(
        'labs/water/chemistry/solution_journal.html',
        title='Уусмал бэлдэх дэвтэр',
        solutions=solutions,
        stats=stats,
        start_date=start_date,
        end_date=end_date,
        status=status,
    )


@water_bp.route('/solution_journal/add', methods=['GET', 'POST'])
@login_required
@lab_required('water')
def add_solution():
    """Шинэ уусмал бүртгэх."""
    from app.models import SolutionPreparation, Chemical, ChemicalUsage, ChemicalLog
    from datetime import datetime

    if request.method == 'POST':
        try:
            # Огноо parse
            prepared_date = datetime.strptime(
                request.form.get('prepared_date'), '%Y-%m-%d'
            ).date()

            expiry_date = None
            if request.form.get('expiry_date'):
                expiry_date = datetime.strptime(
                    request.form.get('expiry_date'), '%Y-%m-%d'
                ).date()

            # Float талбарууд
            chemical_used_mg = to_float(request.form.get('chemical_used_mg'))
            chemical_id = request.form.get('chemical_id')

            solution = SolutionPreparation(
                solution_name=request.form.get('solution_name'),
                concentration=to_float(request.form.get('concentration')),
                concentration_unit=request.form.get('concentration_unit', 'mg/L'),
                volume_ml=to_float(request.form.get('volume_ml')),
                chemical_used_mg=chemical_used_mg,
                prepared_date=prepared_date,
                expiry_date=expiry_date,
                v1=to_float(request.form.get('v1')),
                v2=to_float(request.form.get('v2')),
                v3=to_float(request.form.get('v3')),
                titer_coefficient=to_float(request.form.get('titer_coefficient')),
                preparation_notes=request.form.get('preparation_notes'),
                prepared_by_id=current_user.id,
            )

            # Дундаж тооцоолох
            solution.calculate_v_avg()

            # Chemical холбох + автомат зарцуулалт
            if chemical_id and chemical_used_mg and chemical_used_mg > 0:
                chemical = Chemical.query.get(int(chemical_id))
                if chemical:
                    solution.chemical_id = chemical.id

                    # mg → g хөрвүүлэх (хэрэв chemical нь g нэгжтэй бол)
                    quantity_to_deduct = chemical_used_mg
                    if chemical.unit == 'g':
                        quantity_to_deduct = chemical_used_mg / 1000  # mg to g
                    elif chemical.unit == 'kg':
                        quantity_to_deduct = chemical_used_mg / 1000000  # mg to kg
                    elif chemical.unit == 'mL' or chemical.unit == 'L':
                        # mL/L нэгжтэй бодисын хувьд mg-ыг шууд хасахгүй
                        # Нягт мэдэхгүй тул mg-ыг mL гэж тооцно (ойролцоо)
                        if chemical.unit == 'L':
                            quantity_to_deduct = chemical_used_mg / 1000000
                        else:
                            quantity_to_deduct = chemical_used_mg / 1000

                    old_quantity = chemical.quantity

                    # Хүрэлцэхгүй бол анхааруулга
                    if quantity_to_deduct > chemical.quantity:
                        flash(f"Warning: {chemical.name} stock ({chemical.quantity} {chemical.unit}) is insufficient!", 'warning')

                    # Хасах
                    chemical.quantity = max(0, chemical.quantity - quantity_to_deduct)
                    new_quantity = chemical.quantity

                    # ChemicalUsage бүртгэл үүсгэх
                    usage = ChemicalUsage(
                        chemical_id=chemical.id,
                        quantity_used=quantity_to_deduct,
                        unit=chemical.unit,
                        purpose=f"Уусмал бэлдэх: {solution.solution_name}",
                        analysis_code='SOLUTION_PREP',
                        used_by_id=current_user.id,
                        quantity_before=old_quantity,
                        quantity_after=new_quantity,
                    )
                    db.session.add(usage)

                    # ChemicalLog аудит бүртгэл (with hash - ISO 17025)
                    log = ChemicalLog(
                        chemical_id=chemical.id,
                        user_id=current_user.id,
                        action='consumed',
                        quantity_change=-quantity_to_deduct,
                        quantity_before=old_quantity,
                        quantity_after=new_quantity,
                        details=f"Уусмал бэлдэхэд зарцуулав: {solution.solution_name} ({chemical_used_mg} мг)"
                    )
                    log.data_hash = log.compute_hash()
                    db.session.add(log)

                    # Химийн бодисын төлөв шинэчлэх
                    chemical.update_status()

            db.session.add(solution)
            db.session.commit()

            flash(f"'{solution.solution_name}' registered successfully.", 'success')
            return redirect(url_for('water.solution_journal'))

        except Exception as e:
            db.session.rollback()
            # ✅ XSS сэргийлэлт
            flash(f'Error: {html_escape(str(e))}', 'danger')

    # GET - Химийн бодисын жагсаалт
    chemicals = Chemical.query.filter(
        Chemical.status != 'disposed',
        (Chemical.lab_type == 'water') | (Chemical.lab_type == 'all')
    ).order_by(Chemical.name).all()

    return render_template(
        'labs/water/chemistry/solution_form.html',
        title='Шинэ уусмал бүртгэх',
        solution=None,
        chemicals=chemicals,
        mode='add',
    )


@water_bp.route('/solution_journal/edit/<int:id>', methods=['GET', 'POST'])
@login_required
@lab_required('water')
def edit_solution(id):
    """Уусмал засварлах."""
    from app.models import SolutionPreparation, Chemical
    from datetime import datetime

    solution = SolutionPreparation.query.get_or_404(id)

    if request.method == 'POST':
        try:
            # Огноо parse
            solution.prepared_date = datetime.strptime(
                request.form.get('prepared_date'), '%Y-%m-%d'
            ).date()

            if request.form.get('expiry_date'):
                solution.expiry_date = datetime.strptime(
                    request.form.get('expiry_date'), '%Y-%m-%d'
                ).date()
            else:
                solution.expiry_date = None

            # Float талбарууд
            solution.solution_name = request.form.get('solution_name')
            solution.concentration = to_float(request.form.get('concentration'))
            solution.concentration_unit = request.form.get('concentration_unit', 'mg/L')
            solution.volume_ml = to_float(request.form.get('volume_ml'))
            solution.chemical_used_mg = to_float(request.form.get('chemical_used_mg'))
            solution.v1 = to_float(request.form.get('v1'))
            solution.v2 = to_float(request.form.get('v2'))
            solution.v3 = to_float(request.form.get('v3'))
            solution.titer_coefficient = to_float(request.form.get('titer_coefficient'))
            solution.preparation_notes = request.form.get('preparation_notes')
            solution.status = request.form.get('status', 'active')

            # Дундаж тооцоолох
            solution.calculate_v_avg()

            # Chemical холбох
            chemical_id = request.form.get('chemical_id')
            if chemical_id:
                solution.chemical_id = int(chemical_id)
            else:
                solution.chemical_id = None

            db.session.commit()
            flash('Updated successfully.', 'success')
            return redirect(url_for('water.solution_journal'))

        except Exception as e:
            db.session.rollback()
            # ✅ XSS сэргийлэлт
            flash(f'Error: {html_escape(str(e))}', 'danger')

    # GET
    chemicals = Chemical.query.filter(
        Chemical.status != 'disposed',
        (Chemical.lab_type == 'water') | (Chemical.lab_type == 'all')
    ).order_by(Chemical.name).all()

    return render_template(
        'labs/water/chemistry/solution_form.html',
        title='Уусмал засварлах',
        solution=solution,
        chemicals=chemicals,
        mode='edit',
    )


@water_bp.route('/solution_journal/delete/<int:id>', methods=['POST'])
@login_required
@lab_required('water')
def delete_solution(id):
    """Уусмал устгах."""
    from app.models import SolutionPreparation

    if current_user.role not in ('senior', 'admin'):
        flash('Access denied.', 'danger')
        return redirect(url_for('water.solution_journal'))

    solution = SolutionPreparation.query.get_or_404(id)
    name = solution.solution_name

    db.session.delete(solution)
    db.session.commit()

    flash(f"'{name}' deleted.", 'warning')
    return redirect(url_for('water.solution_journal'))


@water_bp.route('/api/solutions')
@login_required
@lab_required('water')
def api_solutions():
    """Уусмалын жагсаалт API."""
    from app.models import SolutionPreparation

    solutions = SolutionPreparation.query.order_by(
        SolutionPreparation.prepared_date.desc()
    ).all()

    data = [{
        'id': s.id,
        'solution_name': s.solution_name,
        'concentration': s.concentration,
        'concentration_unit': s.concentration_unit,
        'volume_ml': s.volume_ml,
        'chemical_used_mg': s.chemical_used_mg,
        'prepared_date': s.prepared_date.strftime('%Y-%m-%d') if s.prepared_date else '',
        'expiry_date': s.expiry_date.strftime('%Y-%m-%d') if s.expiry_date else '',
        'v1': s.v1,
        'v2': s.v2,
        'v3': s.v3,
        'v_avg': s.v_avg,
        'titer_coefficient': s.titer_coefficient,
        'status': s.status,
        'prepared_by': s.prepared_by.username if s.prepared_by else '',
    } for s in solutions]

    return jsonify(data)


# ============================================================
# УУСМАЛЫН ЖОР (Solution Recipes) - Карт систем
# ============================================================

@water_bp.route('/solution_recipes')
@login_required
@lab_required('water')
def solution_recipes():
    """Уусмалын жорын жагсаалт - карт хэлбэрээр."""
    from app.models import SolutionRecipe, SolutionPreparation

    recipes = SolutionRecipe.query.filter_by(
        lab_type='water', is_active=True
    ).order_by(SolutionRecipe.name).all()

    # Recipe бүрийн сүүлийн бэлдэлтийн мэдээлэл
    recipe_stats = {}
    for recipe in recipes:
        last_prep = SolutionPreparation.query.filter_by(
            recipe_id=recipe.id
        ).order_by(SolutionPreparation.prepared_date.desc()).first()
        prep_count = SolutionPreparation.query.filter_by(recipe_id=recipe.id).count()
        recipe_stats[recipe.id] = {
            'last_prep': last_prep,
            'prep_count': prep_count,
        }

    return render_template(
        'labs/water/chemistry/solution_recipes.html',
        title='Уусмалын жор',
        recipes=recipes,
        recipe_stats=recipe_stats,
    )


@water_bp.route('/solution_recipes/<int:id>')
@login_required
@lab_required('water')
def recipe_detail(id):
    """Уусмалын жорын дэлгэрэнгүй + найруулах форм."""
    from app.models import SolutionRecipe, SolutionPreparation

    recipe = SolutionRecipe.query.get_or_404(id)

    # Сүүлийн 10 бэлдэлт
    recent_preps = SolutionPreparation.query.filter_by(
        recipe_id=recipe.id
    ).order_by(SolutionPreparation.prepared_date.desc()).limit(10).all()

    # Орц бодисуудын одоогийн нөөц
    ingredients_info = []
    for ing in recipe.ingredients:
        chemical = ing.chemical
        if chemical:
            ingredients_info.append({
                'ingredient': ing,
                'chemical': chemical,
                'stock': chemical.quantity,
                'stock_unit': chemical.unit,
            })

    return render_template(
        'labs/water/chemistry/solution_recipe_detail.html',
        title=recipe.name,
        recipe=recipe,
        recent_preps=recent_preps,
        ingredients_info=ingredients_info,
    )


@water_bp.route('/solution_recipes/<int:id>/prepare', methods=['POST'])
@login_required
@lab_required('water')
def prepare_from_recipe(id):
    """Жороор уусмал найруулах - химийн бодис автоматаар хасагдана."""
    from app.models import SolutionRecipe, SolutionPreparation, Chemical, ChemicalUsage, ChemicalLog
    from datetime import datetime, date

    recipe = SolutionRecipe.query.get_or_404(id)

    try:
        # Найруулах эзэлхүүн
        target_volume = float(request.form.get('volume_ml', recipe.standard_volume_ml or 1000))

        # Шаардлагатай бодисуудыг тооцоолох
        required_ingredients = recipe.calculate_ingredients(target_volume)

        # Нөөц шалгах
        insufficient = []
        for item in required_ingredients:
            chemical = item['chemical']
            if chemical:
                required_amount = item['amount']
                # Нэгж хөрвүүлэлт (жорын нэгж → химийн бодисын нэгж)
                converted_amount = convert_recipe_unit_to_chemical(
                    required_amount, item['unit'], chemical.unit
                )
                if converted_amount > chemical.quantity:
                    insufficient.append({
                        'chemical': chemical.name,
                        'required': f"{converted_amount:.4f} {chemical.unit}",
                        'available': f"{chemical.quantity:.4f} {chemical.unit}",
                    })

        if insufficient:
            msg = "Нөөц хүрэлцэхгүй: " + ", ".join(
                [f"{i['chemical']} (хэрэгтэй: {i['required']}, байгаа: {i['available']})" for i in insufficient]
            )
            flash(msg, 'danger')
            return redirect(url_for('water.recipe_detail', id=id))

        # Титрийн утгууд (optional)
        v1 = to_float(request.form.get('v1'))
        v2 = to_float(request.form.get('v2'))
        v3 = to_float(request.form.get('v3'))
        titer_coefficient = to_float(request.form.get('titer_coefficient'))

        # Хугацаа
        expiry_date = None
        if request.form.get('expiry_date'):
            expiry_date = datetime.strptime(request.form.get('expiry_date'), '%Y-%m-%d').date()

        # Бэлдэлт үүсгэх
        preparation = SolutionPreparation(
            solution_name=recipe.name,
            concentration=recipe.concentration,
            concentration_unit=recipe.concentration_unit,
            volume_ml=target_volume,
            recipe_id=recipe.id,
            prepared_date=date.today(),
            expiry_date=expiry_date,
            v1=v1,
            v2=v2,
            v3=v3,
            titer_coefficient=titer_coefficient,
            preparation_notes=request.form.get('notes'),
            prepared_by_id=current_user.id,
        )

        # Дундаж тооцоолох
        preparation.calculate_v_avg()

        # Бодис хасах + бүртгэл
        total_consumed = []
        for item in required_ingredients:
            chemical = item['chemical']
            if chemical:
                required_amount = item['amount']
                converted_amount = convert_recipe_unit_to_chemical(
                    required_amount, item['unit'], chemical.unit
                )

                old_quantity = chemical.quantity
                chemical.quantity = max(0, chemical.quantity - converted_amount)
                new_quantity = chemical.quantity

                # ChemicalUsage бүртгэл
                usage = ChemicalUsage(
                    chemical_id=chemical.id,
                    quantity_used=converted_amount,
                    unit=chemical.unit,
                    purpose=f"Уусмал найруулах: {recipe.name} ({target_volume}мл)",
                    analysis_code='SOLUTION_PREP',
                    used_by_id=current_user.id,
                    quantity_before=old_quantity,
                    quantity_after=new_quantity,
                )
                db.session.add(usage)

                # ChemicalLog аудит (with hash - ISO 17025)
                log = ChemicalLog(
                    chemical_id=chemical.id,
                    user_id=current_user.id,
                    action='consumed',
                    quantity_change=-converted_amount,
                    quantity_before=old_quantity,
                    quantity_after=new_quantity,
                    details=f"Уусмал найруулахад зарцуулав: {recipe.name} ({target_volume}мл)"
                )
                log.data_hash = log.compute_hash()
                db.session.add(log)

                # Төлөв шинэчлэх
                chemical.update_status()

                total_consumed.append(f"{chemical.name}: {converted_amount:.4f} {chemical.unit}")

        # Нийт зарцуулсан бодисыг mg-ээр хадгалах (эхний бодис)
        if required_ingredients:
            first_ing = required_ingredients[0]
            if first_ing['chemical']:
                preparation.chemical_id = first_ing['chemical'].id
                preparation.chemical_used_mg = first_ing['amount'] * (
                    1000 if first_ing['unit'] == 'g' else 1
                )

        db.session.add(preparation)
        db.session.commit()

        consumed_str = ", ".join(total_consumed) if total_consumed else "бодис байхгүй"
        flash(f"'{recipe.name}' ({target_volume}мл) амжилттай найруулагдлаа. Зарцуулсан: {consumed_str}", 'success')
        return redirect(url_for('water.recipe_detail', id=id))

    except Exception as e:
        db.session.rollback()
        # ✅ XSS сэргийлэлт
        flash(f'Error: {html_escape(str(e))}', 'danger')
        return redirect(url_for('water.recipe_detail', id=id))


def convert_recipe_unit_to_chemical(amount, recipe_unit, chemical_unit):
    """
    Жорын нэгжийг химийн бодисын нэгж рүү хөрвүүлэх.

    Args:
        amount: Хэмжээ
        recipe_unit: Жорын нэгж (g, mg, mL)
        chemical_unit: Химийн бодисын нэгж (g, kg, mL, L)

    Returns:
        Хөрвүүлсэн хэмжээ
    """
    # Эхлээд грамм руу хөрвүүлэх
    if recipe_unit == 'mg':
        amount_g = amount / 1000
    elif recipe_unit == 'g':
        amount_g = amount
    elif recipe_unit == 'kg':
        amount_g = amount * 1000
    elif recipe_unit == 'mL':
        amount_g = amount  # Нягт ~1 гэж үзнэ
    elif recipe_unit == 'L':
        amount_g = amount * 1000
    else:
        amount_g = amount

    # Химийн бодисын нэгж рүү хөрвүүлэх
    if chemical_unit == 'mg':
        return amount_g * 1000
    elif chemical_unit == 'g':
        return amount_g
    elif chemical_unit == 'kg':
        return amount_g / 1000
    elif chemical_unit == 'mL':
        return amount_g  # Нягт ~1 гэж үзнэ
    elif chemical_unit == 'L':
        return amount_g / 1000
    else:
        return amount_g


@water_bp.route('/solution_recipes/add', methods=['GET', 'POST'])
@login_required
@lab_required('water')
def add_recipe():
    """Шинэ уусмалын жор нэмэх."""
    from app.models import SolutionRecipe, SolutionRecipeIngredient, Chemical

    if request.method == 'POST':
        try:
            recipe = SolutionRecipe(
                name=request.form.get('name'),
                concentration=to_float(request.form.get('concentration')),
                concentration_unit=request.form.get('concentration_unit', 'N'),
                standard_volume_ml=to_float(request.form.get('standard_volume_ml')) or 1000,
                preparation_notes=request.form.get('preparation_notes'),
                lab_type='water',
                category=request.form.get('category'),
                created_by_id=current_user.id,
            )
            db.session.add(recipe)
            db.session.flush()  # ID авахын тулд

            # Орц нэмэх
            chemical_ids = request.form.getlist('chemical_id[]')
            amounts = request.form.getlist('amount[]')
            units = request.form.getlist('ingredient_unit[]')

            for i, chem_id in enumerate(chemical_ids):
                if chem_id and amounts[i]:
                    ingredient = SolutionRecipeIngredient(
                        recipe_id=recipe.id,
                        chemical_id=int(chem_id),
                        amount=float(amounts[i]),
                        unit=units[i] if i < len(units) else 'g',
                    )
                    db.session.add(ingredient)

            db.session.commit()
            flash(f"'{recipe.name}' recipe created successfully.", 'success')
            return redirect(url_for('water.solution_recipes'))

        except Exception as e:
            db.session.rollback()
            # ✅ XSS сэргийлэлт
            flash(f'Error: {html_escape(str(e))}', 'danger')

    # GET
    chemicals = Chemical.query.filter(
        Chemical.status != 'disposed',
        (Chemical.lab_type == 'water') | (Chemical.lab_type == 'all')
    ).order_by(Chemical.name).all()

    return render_template(
        'labs/water/chemistry/solution_recipe_form.html',
        title='Шинэ жор нэмэх',
        recipe=None,
        chemicals=chemicals,
        mode='add',
    )


@water_bp.route('/solution_recipes/edit/<int:id>', methods=['GET', 'POST'])
@login_required
@lab_required('water')
def edit_recipe(id):
    """Уусмалын жор засварлах."""
    from app.models import SolutionRecipe, SolutionRecipeIngredient, Chemical

    recipe = SolutionRecipe.query.get_or_404(id)

    if request.method == 'POST':
        try:
            recipe.name = request.form.get('name')
            recipe.concentration = to_float(request.form.get('concentration'))
            recipe.concentration_unit = request.form.get('concentration_unit', 'N')
            recipe.standard_volume_ml = to_float(request.form.get('standard_volume_ml')) or 1000
            recipe.preparation_notes = request.form.get('preparation_notes')
            recipe.category = request.form.get('category')

            # Хуучин орц устгаад шинээр нэмэх
            SolutionRecipeIngredient.query.filter_by(recipe_id=recipe.id).delete()

            chemical_ids = request.form.getlist('chemical_id[]')
            amounts = request.form.getlist('amount[]')
            units = request.form.getlist('ingredient_unit[]')

            for i, chem_id in enumerate(chemical_ids):
                if chem_id and amounts[i]:
                    ingredient = SolutionRecipeIngredient(
                        recipe_id=recipe.id,
                        chemical_id=int(chem_id),
                        amount=float(amounts[i]),
                        unit=units[i] if i < len(units) else 'g',
                    )
                    db.session.add(ingredient)

            db.session.commit()
            flash('Recipe updated successfully.', 'success')
            return redirect(url_for('water.solution_recipes'))

        except Exception as e:
            db.session.rollback()
            # ✅ XSS сэргийлэлт
            flash(f'Error: {html_escape(str(e))}', 'danger')

    # GET
    chemicals = Chemical.query.filter(
        Chemical.status != 'disposed',
        (Chemical.lab_type == 'water') | (Chemical.lab_type == 'all')
    ).order_by(Chemical.name).all()

    return render_template(
        'labs/water/chemistry/solution_recipe_form.html',
        title='Жор засварлах',
        recipe=recipe,
        chemicals=chemicals,
        mode='edit',
    )


@water_bp.route('/solution_recipes/delete/<int:id>', methods=['POST'])
@login_required
@lab_required('water')
def delete_recipe(id):
    """Уусмалын жор устгах."""
    from app.models import SolutionRecipe

    if current_user.role not in ('senior', 'admin'):
        flash('Access denied.', 'danger')
        return redirect(url_for('water.solution_recipes'))

    recipe = SolutionRecipe.query.get_or_404(id)
    name = recipe.name

    db.session.delete(recipe)
    db.session.commit()

    flash(f"'{name}' recipe deleted.", 'warning')
    return redirect(url_for('water.solution_recipes'))
