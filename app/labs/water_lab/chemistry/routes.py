# app/labs/water_lab/chemistry/routes.py
"""Усны хими лабораторийн routes."""

import json as _json
import logging
import re
from datetime import datetime as _dt, timedelta as _td

from flask import Blueprint, render_template, jsonify, request, flash, redirect, url_for
from flask_login import login_required, current_user
from sqlalchemy import or_
from sqlalchemy.exc import SQLAlchemyError

from app import db
from app.models import Sample, AnalysisResult, Equipment
from app.labs.water_lab.chemistry.constants import (
    ALL_WATER_PARAMS, WATER_ANALYSIS_TYPES, WATER_UNITS,
    ALL_WATER_SAMPLE_NAMES, get_mns_standards,
    DEFAULT_FILTER_DAYS, MAX_QUERY_LIMIT,
    parse_display_name as _parse_display_name,
)
from app.labs.water_lab.microbiology.constants import MICRO_ANALYSIS_TYPES
from app.utils.decorators import lab_required
from app.utils.converters import to_float
from app.utils.security import escape_like_pattern, is_safe_url

logger = logging.getLogger(__name__)

water_bp = Blueprint(
    'water',
    __name__,
    url_prefix='/labs/water-lab/chemistry'
)


def _parse_filter_days(default=DEFAULT_FILTER_DAYS):
    """Request args-аас days параметр авч date_cutoff буцаах."""
    days_param = request.args.get('days', str(default))
    try:
        filter_days = int(days_param)
    except (ValueError, TypeError):
        filter_days = default
    date_cutoff = None
    if filter_days > 0:
        date_cutoff = (_dt.now() - _td(days=filter_days)).date()
    return filter_days, date_cutoff


def _build_water_rows(samples, include_lab_type=False):
    """Дээжүүдийн хими + микро үр дүнг rows болгон цуглуулах (archive/summary дундын helper).

    Returns:
        (rows, active_chem_codes)
    """
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
    # result ID maps (давтах товчинд хэрэглэнэ)
    chem_id_map = {}   # sample_id → {code → result_id}
    micro_id_map = {}  # sample_id → result_id
    air_id_map = {}    # sample_id → result_id
    swab_id_map = {}   # sample_id → result_id
    for r in results:
        try:
            raw = _json.loads(r.raw_data) if isinstance(r.raw_data, str) else (r.raw_data or {})
        except (ValueError, TypeError):
            raw = {}

        if r.analysis_code == 'MICRO_WATER':
            micro_map[r.sample_id] = raw
            micro_id_map[r.sample_id] = r.id
        elif r.analysis_code == 'MICRO_AIR':
            air_map[r.sample_id] = raw
            air_id_map[r.sample_id] = r.id
        elif r.analysis_code == 'MICRO_SWAB':
            swab_map[r.sample_id] = raw
            swab_id_map[r.sample_id] = r.id
        else:
            if r.sample_id not in chem_map:
                chem_map[r.sample_id] = {}
            if r.sample_id not in chem_id_map:
                chem_id_map[r.sample_id] = {}
            val = raw.get('value') or raw.get('result') or raw.get('average') or r.final_result
            chem_map[r.sample_id][r.analysis_code] = val
            chem_id_map[r.sample_id][r.analysis_code] = r.id
            if r.analysis_code == 'BOD':
                pur = raw.get('purification')
                if pur is not None:
                    chem_map[r.sample_id]['BOD_PUR'] = pur
                    chem_id_map[r.sample_id]['BOD_PUR'] = r.id

    rows = []
    for s in samples:
        display_name = _parse_display_name(s.sample_code)

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

        # Result ID-ууд (давтах товчинд)
        row['_result_ids'] = chem_id_map.get(s.id, {})
        row['_micro_result_id'] = micro_id_map.get(s.id)
        row['_air_result_id'] = air_id_map.get(s.id)
        row['_swab_result_id'] = swab_id_map.get(s.id)

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
        row['cfu_avg'] = cfu_avg if cfu_avg is not None else sres.get('cfu_swab')
        # E.coli, Salmonella, S.aureus - ус эсвэл арчдасаас авах (нэгтгэсэн)
        row['ecoli'] = mres.get('ecoli') if mres.get('ecoli') is not None else sres.get('ecoli_swab')
        row['salmonella'] = mres.get('salmonella') if mres.get('salmonella') is not None else sres.get('salmonella_swab')
        row['staph'] = ares.get('staphylococcus') if ares.get('staphylococcus') is not None else sres.get('staphylococcus_swab')

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


def _build_multi_workspace(codes, template, title, analysis_code,
                           param, extra_ctx=None, equipment_patterns=None):
    """C-1 fix: Олон workspace-ийн давхардсан логикийг нэгтгэсэн helper.

    Args:
        codes: шинжилгээний кодуудын list (e.g. ['NH4', 'NO2', ...])
        template: render хийх template path
        title: хуудасны гарчиг
        analysis_code: workspace analysis_code (e.g. 'SFT')
        param: {'name_mn': ..., 'unit': ..., 'mns_limit': ..., 'standard': ...}
        extra_ctx: нэмэлт template context dict
        equipment_patterns: Equipment.related_analysis ILIKE patterns (list of str)
    """
    filter_days, date_cutoff = _parse_filter_days()

    newly_selected_ids_str = request.args.get('sample_ids', '')
    new_ids = [int(x) for x in newly_selected_ids_str.split(',') if x.isdigit()]

    seen = set()
    samples_to_analyze = []

    # A: Одоо байгаа үр дүнтэй дээжүүд (pending/rejected)
    existing_q = (
        db.session.query(AnalysisResult, Sample)
        .join(Sample, Sample.id == AnalysisResult.sample_id)
        .filter(
            AnalysisResult.user_id == current_user.id,
            AnalysisResult.analysis_code.in_(codes),
            AnalysisResult.status.in_(['pending_review', 'rejected']),
        )
    )
    if date_cutoff:
        existing_q = existing_q.filter(Sample.received_date >= date_cutoff)
    for r, s in existing_q.all():
        if s.id not in seen:
            samples_to_analyze.append(s)
            seen.add(s.id)

    # B: Шинэ сонгосон
    if new_ids:
        new_samples = Sample.query.filter(Sample.id.in_(new_ids)).all()
        smap = {s.id: s for s in new_samples}
        for sid in new_ids:
            if sid not in seen and sid in smap:
                samples_to_analyze.append(smap[sid])
                seen.add(sid)

    # Existing results map
    existing_results_map = {}
    rejected_samples_info = {}
    if samples_to_analyze:
        sample_ids = [s.id for s in samples_to_analyze]
        results = AnalysisResult.query.filter(
            AnalysisResult.sample_id.in_(sample_ids),
            AnalysisResult.analysis_code.in_(codes),
            AnalysisResult.status.in_(['pending_review', 'rejected', 'approved'])
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
                rejected_samples_info.setdefault(r.sample_id, {})[r.analysis_code] = {
                    'reason': reason,
                    'reason_code': reason_code,
                }
                if reason_code != 'data_entry':
                    raw = {}

            existing_results_map.setdefault(r.sample_id, {})[r.analysis_code] = {
                'status': r.status,
                'raw_data': raw,
                'final_result': r.final_result,
            }

    # H-6 fix: Equipment query — silent except → logger.debug
    related_equipments = []
    try:
        eq_filters = [Equipment.category == 'water']
        if equipment_patterns:
            for pat in equipment_patterns:
                safe_pat = escape_like_pattern(pat)
                eq_filters.append(
                    Equipment.related_analysis.ilike(f'%{safe_pat}%', escape='\\')
                )
        related_equipments = (
            Equipment.query
            .filter(
                or_(*eq_filters),
                or_(Equipment.status.is_(None), Equipment.status != 'retired')
            )
            .order_by(Equipment.name.asc())
            .all()
        )
    except SQLAlchemyError:
        logger.debug('Equipment query failed for codes=%s', codes, exc_info=True)

    limits = {code: ALL_WATER_PARAMS.get(code, {}).get('mns_limit') for code in codes}

    ctx = {
        'title': title,
        'analysis_code': analysis_code,
        'param': param,
        'use_aggrid': True,
        'samples': samples_to_analyze,
        'aggrid_samples': samples_to_analyze,
        'existing_results_map': existing_results_map,
        'rejected_samples_info': rejected_samples_info,
        'error_labels': {},
        'related_equipments': related_equipments,
        'filter_days': filter_days,
    }
    if extra_ctx:
        ctx.update(extra_ctx)

    # Limits-ийг analysis_code-оор нэрлэнэ
    limits_key = analysis_code.lower() + '_limits'
    if analysis_code == 'SFT_PHYS' or analysis_code == 'SFT_PHYS_WW':
        limits_key = 'phys_limits'
    ctx[limits_key] = limits

    return render_template(template, **ctx)


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

    # M-1 fix: 3 query → 1 conditional count query
    from sqlalchemy import func, case
    count_row = db.session.query(
        func.count(case((Sample.lab_type == 'water', Sample.id))).label('water'),
        func.count(case((Sample.lab_type == 'microbiology', Sample.id))).label('micro'),
        func.count(case((Sample.lab_type == 'water & micro', Sample.id))).label('combined'),
    ).filter(
        Sample.lab_type.in_(['water', 'microbiology', 'water & micro']),
        Sample.status == 'archived'
    ).first()
    water_count = count_row.water if count_row else 0
    micro_count = count_row.micro if count_row else 0
    combined_count = count_row.combined if count_row else 0
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
        except (ValueError, TypeError, SQLAlchemyError) as e:
            db.session.rollback()
            logger.exception('register_sample error')
            flash('Дээж бүртгэхэд алдаа гарлаа.', 'danger')
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
        sla_lab_types=['water', 'microbiology'],
    )


@water_bp.route('/workspace/<code>')
@login_required
@lab_required('water')
def workspace(code):
    """Шинжилгээний ажлын талбар."""
    code_upper = code.upper()
    if code_upper == 'SFT':
        return sft_workspace()
    if code_upper == 'SFT_PHYS':
        return sft_physical_workspace()
    param = ALL_WATER_PARAMS.get(code_upper)
    if not param:
        return jsonify({'success': False, 'message': 'Unknown analysis code'}), 404

    # ── Огнооны шүүлтүүр ──
    filter_days, date_cutoff = _parse_filter_days()

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
        'ODOR': 'labs/water/chemistry/analysis_forms/ph_ec_form.html',
        'SLUDGE': 'labs/water/chemistry/analysis_forms/ph_ec_form.html',
        'BOD': 'labs/water/chemistry/analysis_forms/bod_form.html',
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

    # A: Одоо байгаа үр дүнтэй дээжүүд (огнооны шүүлтүүрээр)
    # ✅ H-1 fix: N+1 query → joinedload
    existing_q = (
        db.session.query(AnalysisResult, Sample)
        .join(Sample, Sample.id == AnalysisResult.sample_id)
        .filter(
            AnalysisResult.user_id == current_user.id,
            AnalysisResult.analysis_code == code_upper,
        )
    )
    if approved_ids:
        existing_q = existing_q.filter(~AnalysisResult.sample_id.in_(approved_ids))
    if date_cutoff:
        existing_q = existing_q.filter(Sample.received_date >= date_cutoff)
    for r, s in existing_q.all():
        if s.id not in seen:
            samples_to_analyze.append(s)
            seen.add(s.id)

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
    except SQLAlchemyError:
        logger.debug('Equipment query failed for code=%s', code_upper, exc_info=True)

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
        filter_days=filter_days,
    )


@water_bp.route('/workspace/sft-phys')
@login_required
@lab_required('water')
def sft_physical_workspace():
    """Физик нэгтгэсэн ажлын талбар (COLOR/TEMP/EC/PH/F_W/CL_FREE)."""
    return _build_multi_workspace(
        codes=['COLOR_TEMP', 'EC', 'PH', 'F_W', 'CL_FREE'],
        template='labs/water/chemistry/analysis_forms/sft_physical_form.html',
        title='Физик (нэгтгэсэн) - Ажлын талбар',
        analysis_code='SFT_PHYS',
        param={'name_mn': 'Физик (нэгтгэсэн)', 'unit': '', 'mns_limit': None, 'standard': 'MNS 4586:2007'},
        equipment_patterns=['COLOR_TEMP', 'EC', 'PH', 'F_W', 'CL_FREE'],
    )


@water_bp.route('/workspace/phys-ww')
@login_required
@lab_required('water')
def phys_wastewater_workspace():
    """Ахуйн бохир ус — PHYS нэгтгэсэн ажлын талбар (ундны PHYS-тэй адил)."""
    return _build_multi_workspace(
        codes=['COLOR_TEMP', 'EC', 'PH', 'F_W', 'CL_FREE'],
        template='labs/water/chemistry/analysis_forms/sft_physical_form.html',
        title='Физик (Ахуйн бохир ус) - Ажлын талбар',
        analysis_code='SFT_PHYS_WW',
        param={'name_mn': 'Физик (Ахуйн бохир ус)', 'unit': '', 'mns_limit': None, 'standard': 'MNS 4586:2007'},
        equipment_patterns=['COLOR_TEMP', 'EC', 'PH', 'F_W', 'CL_FREE'],
    )


@water_bp.route('/workspace/sft')
@login_required
@lab_required('water')
def sft_workspace():
    """СФТ нэгтгэсэн ажлын талбар (NH4/NO2/NO3/FE_W)."""
    return _build_multi_workspace(
        codes=['NH4', 'NO2', 'NO3', 'FE_W'],
        template='labs/water/chemistry/analysis_forms/sft_form.html',
        title='СФТ - Ажлын талбар',
        analysis_code='SFT',
        param={'name_mn': 'СФТ', 'unit': 'mg/L', 'mns_limit': None, 'standard': 'MNS 4586:2007'},
        equipment_patterns=['NH4', 'NO2', 'NO3', 'FE_W'],
    )


@water_bp.route('/workspace/sfm')
@login_required
@lab_required('water')
def sfm_workspace():
    """СФМ нэгтгэсэн ажлын талбар (NH4/NO2/PO4/FE_W)."""
    return _build_multi_workspace(
        codes=['NH4', 'NO2', 'PO4', 'FE_W'],
        template='labs/water/chemistry/analysis_forms/sfm_form.html',
        title='СФМ - Ажлын талбар',
        analysis_code='SFM',
        param={'name_mn': 'СФМ', 'unit': 'mg/L', 'mns_limit': None, 'standard': 'MNS 4586:2007'},
        equipment_patterns=['NH4', 'NO2', 'PO4', 'FE_W'],
    )


@water_bp.route('/workspace/sludge')
@login_required
@lab_required('water')
def sludge_workspace():
    """Лагийн нэгтгэсэн ажлын талбар (SV/SD/SI)."""
    return _build_multi_workspace(
        codes=['SLUDGE_VOL', 'SLUDGE_DOSE', 'SLUDGE_INDEX'],
        template='labs/water/chemistry/analysis_forms/sludge_form.html',
        title='Лаг - Ажлын талбар',
        analysis_code='SLUDGE',
        param={'name_mn': 'Лаг', 'unit': '', 'mns_limit': None, 'standard': 'MNS 4586:2007'},
        equipment_patterns=['SLUDGE'],
    )


# ============ API endpoints ============

@water_bp.route('/api/retest/<int:result_id>', methods=['POST'])
@login_required
@lab_required('water')
def retest_result(result_id):
    """Давтах шинжилгээ — хуучин үр дүнг устгаж аудит бичлэг үүсгэнэ."""
    from app.services.analysis_audit import log_analysis_action
    from app.utils.database import safe_commit

    result = db.session.get(AnalysisResult, result_id)
    if not result:
        return jsonify({'success': False, 'message': 'Үр дүн олдсонгүй'}), 404

    # Delete хийхээс өмнө утгуудыг хадгалах
    analysis_code_snapshot = result.analysis_code
    sample = db.session.get(Sample, result.sample_id)

    # Аудит бичлэг (result устахаас ӨМНӨ)
    log_analysis_action(
        result_id=result.id,
        sample_id=result.sample_id,
        analysis_code=analysis_code_snapshot,
        action='RETEST_DELETED',
        raw_data_dict=result.raw_data,
        final_result=result.final_result,
        sample_code_snapshot=sample.sample_code if sample else None,
        reason=f'Давтах шинжилгээ ({current_user.username})',
    )

    # Үр дүн устгах
    db.session.delete(result)

    if not safe_commit():
        return jsonify({'success': False, 'message': 'DB алдаа'}), 500

    return jsonify({
        'success': True,
        'message': f'{analysis_code_snapshot} үр дүн устгагдлаа. Дахин оруулна уу.'
    })


@water_bp.route('/api/eligible/<code>')
@login_required
@lab_required('water')
def eligible_samples(code):
    """Боломжит дээж (усны химийн шинжилгээнд)."""
    from datetime import datetime as _dt, timedelta as _td

    q = Sample.query.filter(
        Sample.lab_type.in_(['water', 'water & micro']),
        Sample.status.in_(['new', 'in_progress'])
    )

    # Огнооны шүүлтүүр (workspace-тэй sync)
    days_param = request.args.get('days', '7')
    try:
        filter_days = int(days_param)
    except (ValueError, TypeError):
        filter_days = 7
    if filter_days > 0:
        cutoff = (_dt.now() - _td(days=filter_days)).date()
        q = q.filter(Sample.received_date >= cutoff)

    samples = q.order_by(Sample.received_date.desc()).all()
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
        return jsonify({'success': False, 'message': 'No data provided'}), 400

    sample_id = data.get('sample_id')
    analysis_code = data.get('analysis_code', '')
    results = data.get('results', {})

    # M-9: analysis_code whitelist validation
    from app.labs.water_lab.chemistry.constants import VALID_WATER_ANALYSIS_CODES
    if not analysis_code or analysis_code not in VALID_WATER_ANALYSIS_CODES:
        return jsonify({'success': False, 'message': 'Invalid analysis code'}), 400

    # CC-3: Lock parent sample row to serialize concurrent saves
    sample = db.session.query(Sample).filter_by(id=sample_id).with_for_update().first()
    if not sample:
        return jsonify({'success': False, 'message': 'Sample not found'}), 404

    # B-M4: Archived/completed дээж дээр шинэ шинжилгээ хориглох
    if sample.status in ('archived', 'completed'):
        return jsonify({'success': False, 'message': f"Энэ дээж '{sample.status}' төлөвтэй — шинэ шинжилгээ хадгалах боломжгүй"}), 400

    import json

    # final_result: raw_data-аас тоон үр дүн авах
    final_val = to_float(
        results.get('result') or results.get('value') or results.get('average')
    )

    # ✅ C-2 fix: Давхардал шалгах — UPSERT логик (with_for_update lock)
    ar = AnalysisResult.query.filter_by(
        sample_id=sample_id,
        analysis_code=analysis_code,
    ).filter(
        AnalysisResult.status.in_(['pending_review', 'rejected'])
    ).with_for_update().first()

    if ar:
        # Одоо байгаа pending/rejected үр дүнг шинэчлэх
        ar.raw_data = json.dumps(results, ensure_ascii=False)
        ar.final_result = final_val
        ar.user_id = current_user.id
        ar.status = 'pending_review'
    else:
        # Approved үр дүн байгаа эсэх шалгах
        approved = AnalysisResult.query.filter_by(
            sample_id=sample_id,
            analysis_code=analysis_code,
            status='approved'
        ).with_for_update().first()
        if approved:
            return jsonify({'success': False, 'message': 'This analysis is already approved. Use retest to re-enter.'}), 409

        ar = AnalysisResult(
            sample_id=sample_id,
            analysis_code=analysis_code,
            raw_data=json.dumps(results, ensure_ascii=False),
            final_result=final_val,
            user_id=current_user.id,
        )
        db.session.add(ar)

    from app.utils.database import safe_commit
    if not safe_commit():
        return jsonify({'success': False, 'message': 'Error saving results'}), 500

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
    samples = q.order_by(Sample.id.desc()).limit(MAX_QUERY_LIMIT).all()

    result = []
    for idx, s in enumerate(reversed(samples), 1):
        display_name = _parse_display_name(s.sample_code)

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
            except (TypeError, SQLAlchemyError) as e:
                db.session.rollback()
                logger.exception('edit_sample error: sample_id=%s', sample_id)
                flash('Дээж засахад алдаа гарлаа.', 'danger')

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
        return redirect(request.referrer if request.referrer and is_safe_url(request.referrer) else url_for('water.register_sample'))

    if current_user.role not in ('admin', 'senior', 'chemist'):
        flash('You do not have permission to delete samples.', 'danger')
        return redirect(request.referrer if request.referrer and is_safe_url(request.referrer) else url_for('water.register_sample'))

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

            # ✅ C-3 fix: Approved үр дүнтэй дээжийг хамгаалах
            approved_count = AnalysisResult.query.filter_by(
                sample_id=sample.id, status='approved'
            ).count()
            if approved_count > 0 and current_user.role != 'admin':
                failed.append(f'{sample.sample_code} (Батлагдсан үр дүнтэй)')
                continue

            # Холбогдох AnalysisResult-уудыг эхлээд устгах (orphan сэргийлэлт)
            AnalysisResult.query.filter_by(sample_id=sample.id).delete()

            log_audit(
                action='sample_deleted',
                resource_type='Sample',
                resource_id=sample.id,
                details={'sample_code': sample.sample_code, 'client_name': sample.client_name},
            )
            db.session.delete(sample)
            deleted += 1
        except (ValueError, TypeError, SQLAlchemyError) as e:
            logger.exception('delete_samples error: sid=%s', sid)
            failed.append(f'ID={sid}')

    if deleted:
        from app.utils.database import safe_commit
        if not safe_commit():
            flash('DB error during delete.', 'danger')
        else:
            flash(f'{deleted} samples deleted successfully.', 'success')
    if failed:
        flash(f'Error: {", ".join(failed)}', 'danger')

    return redirect(request.referrer if request.referrer and is_safe_url(request.referrer) else url_for('water.register_sample'))


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


# Report routes (dashboard, consumption, monthly plan) + Solution journal — тусдаа файлд
from app.labs.water_lab.chemistry import water_reports  # noqa: E402, F401
from app.labs.water_lab.chemistry import solutions  # noqa: E402, F401
