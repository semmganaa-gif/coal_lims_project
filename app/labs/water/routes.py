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


@water_bp.route('/summary')
@login_required
@lab_required('water')
def water_summary():
    """Усны хими + микробиологийн нэгдсэн үр дүнгийн нэгтгэл."""
    return render_template(
        'water_summary.html',
        title='Усны шинжилгээний үр дүнгийн нэгтгэл',
    )


@water_bp.route('/api/summary_data')
@login_required
@lab_required('water')
def summary_data():
    """Усны хими + микробиологийн үр дүнг нэгтгэж буцаана."""
    import json as _json
    from datetime import datetime as _dt

    date_from = request.args.get('date_from')
    date_to = request.args.get('date_to')

    # Ус + микро дээжүүд бүгд
    q = Sample.query.filter(
        Sample.lab_type.in_(['water', 'microbiology', 'water & micro'])
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
