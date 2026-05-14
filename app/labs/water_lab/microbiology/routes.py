# app/labs/water_lab/microbiology/routes.py
"""Микробиологийн лабораторийн routes."""

import json
import logging
import re
import calendar
from datetime import datetime, date, timedelta
from collections import defaultdict, OrderedDict

from flask import Blueprint, render_template, jsonify, request, flash, redirect, url_for, current_app
from flask_login import login_required, current_user
from sqlalchemy import extract, func
from sqlalchemy.exc import SQLAlchemyError

from app import db
from app.models import Sample, AnalysisResult
from app.labs.water_lab.microbiology.constants import (
    ALL_MICRO_PARAMS, MICRO_ANALYSIS_TYPES,
    MICRO_WATER_FIELDS, MICRO_AIR_FIELDS, MICRO_SWAB_FIELDS,
    CATEGORY_ANALYSIS_CODES,
)
from app.labs.water_lab.chemistry.constants import (
    WATER_UNITS, ALL_WATER_SAMPLE_NAMES,
)
from app.labs.water_lab.microbiology.constants import MICRO_UNITS
from app.utils.decorators import lab_required
from app.utils.database import safe_commit
from app.utils.datetime import now_local
from app.labs.water_lab.chemistry.constants import parse_display_name as _parse_display_name

logger = logging.getLogger(__name__)

micro_bp = Blueprint(
    'microbiology',
    __name__,
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
        'labs/water/microbiology/micro_hub.html',
        title='Микробиологийн лаборатори',
        analysis_types=MICRO_ANALYSIS_TYPES,
        params=ALL_MICRO_PARAMS,
        total_samples=stats['total'],
        new_samples=stats['new'],
        in_progress=stats['in_progress'],
        completed=stats['completed'],
    )


@micro_bp.route('/edit_sample/<int:sample_id>', methods=['GET', 'POST'])
@login_required
@lab_required('microbiology')
def edit_sample(sample_id):
    """Микробиологийн дээж засах."""
    sample = db.session.get(Sample, sample_id)
    if not sample:
        flash('Sample not found.', 'danger')
        return redirect(url_for('microbiology.register_sample'))

    can_edit = current_user.role in ('admin', 'senior', 'chemist')
    if not can_edit:
        flash('You do not have permission to edit samples.', 'warning')
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
                    sample.analyses_to_perform = json.dumps(selected_analyses)
                if code_changed or analyses_changed:
                    db.session.commit()
                    flash('Sample information updated.', 'success')
                else:
                    flash('No changes were made.', 'info')
                return redirect(url_for('microbiology.register_sample'))
            except (TypeError, SQLAlchemyError):
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


@micro_bp.route('/delete_samples', methods=['POST'])
@login_required
@lab_required('microbiology')
def delete_samples():
    """Микробиологийн дээж устгах (admin, senior)."""
    from app.utils.audit import log_audit

    sample_ids = request.form.getlist('sample_ids')
    if not sample_ids:
        flash('Please select samples to delete!', 'warning')
        return redirect(url_for('microbiology.register_sample'))

    if current_user.role not in ('admin', 'senior', 'chemist'):
        flash('You do not have permission to delete samples.', 'danger')
        return redirect(url_for('microbiology.register_sample'))

    from app.services.analysis_audit import log_analysis_action

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

            # ISO 17025: Үр дүн бүрд устгахаас өмнө audit log бичих.
            for r in sample.results:
                log_analysis_action(
                    result_id=r.id,
                    sample_id=sample.id,
                    analysis_code=r.analysis_code,
                    action='DELETED',
                    final_result=r.final_result,
                    raw_data_dict=r.raw_data,
                    reason=f"Sample {sample.sample_code} устгасан (microbiology lab)",
                    sample_code_snapshot=sample.sample_code,
                )

            log_audit(
                action='sample_deleted',
                resource_type='Sample',
                resource_id=sample.id,
                details={'sample_code': sample.sample_code, 'client_name': sample.client_name},
            )
            db.session.delete(sample)
            deleted += 1
        except (ValueError, TypeError, SQLAlchemyError):
            logger.exception('delete_samples error: sid=%s', sid)
            failed.append(f'ID={sid}')

    if deleted:
        if not safe_commit():
            flash('DB error during delete.', 'danger')
        else:
            flash(f'{deleted} samples deleted successfully.', 'success')
    if failed:
        flash(f'Error: {", ".join(failed)}', 'danger')

    return redirect(url_for('microbiology.register_sample'))


@micro_bp.route('/analysis')
@login_required
@lab_required('microbiology')
def analysis_hub():
    """Микробиологийн шинжилгээний карт сонгох хуудас."""
    return render_template('labs/water/microbiology/micro_analysis_hub.html', title='Микробиологийн шинжилгээ')


@micro_bp.route('/register', methods=['GET', 'POST'])
@login_required
@lab_required('microbiology')
def register_sample():
    """Микробиологийн дээж бүртгэх."""
    if request.method == 'POST':
        sample_names = request.form.getlist('sample_codes')
        if not sample_names:
            flash('Sample name is required.', 'danger')
            return redirect(url_for('microbiology.register_sample'))

        from app.labs.water_lab.chemistry.utils import create_water_micro_samples
        try:
            created, skipped, n_analyses = create_water_micro_samples(request.form, current_user.id)
            if created:
                flash(f'{len(created)} дээж registered successfully. ({n_analyses} шинжилгээ)', 'success')
            if skipped:
                flash(f'{len(skipped)} дээж аль хэдийн бүртгэгдсэн: {", ".join(skipped)}', 'warning')
            return redirect(url_for('microbiology.register_sample'))
        except (ValueError, TypeError, SQLAlchemyError):
            db.session.rollback()
            logger.exception('register_sample error')
            flash('Дээж бүртгэхэд алдаа гарлаа.', 'danger')
            return redirect(url_for('microbiology.register_sample'))

    return render_template(
        'labs/water/microbiology/micro_register.html',
        title='Микробиологийн дээж бүртгэл',
        units={**WATER_UNITS, **MICRO_UNITS},
        total_samples=len(ALL_WATER_SAMPLE_NAMES),
        micro_analyses=MICRO_ANALYSIS_TYPES,
        use_aggrid=True,
        sla_lab_types=['microbiology'],
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
        'water': 'labs/water/microbiology/analysis_forms/micro_workspace.html',
        'air': 'labs/water/microbiology/analysis_forms/micro_air_workspace.html',
        'swab': 'labs/water/microbiology/analysis_forms/micro_swab_workspace.html',
    }

    title = titles.get(code_lower, f'Микробиологи — {code}')
    template = templates.get(code_lower)
    if not template:
        return jsonify({'error': f'Unknown workspace: {code}'}), 404

    from app.repositories import EquipmentRepository
    try:
        related_equipments = EquipmentRepository.get_by_category('micro')
    except SQLAlchemyError:
        related_equipments = []

    return render_template(
        template, title=title, workspace_code=code_lower,
        related_equipments=related_equipments,
    )


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
    from app.labs.water_lab.microbiology.constants import CATEGORY_ANALYSIS_CODES

    category = request.args.get('category')

    query = Sample.query.filter(
        Sample.lab_type.in_(['microbiology'])
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

    # Previous result per sample (last approved/pending result for this category)
    _prev_key_map = {
        'MICRO_WATER': 'cfu_37',
        'MICRO_AIR': 'cfu_air',
        'MICRO_SWAB': 'cfu_swab',
    }
    prev_results = {}
    if category in _prev_key_map and samples:
        result_key = _prev_key_map[category]
        sample_ids = [s.id for s in samples]
        prev_ars = (
            AnalysisResult.query
            .filter(
                AnalysisResult.sample_id.in_(sample_ids),
                AnalysisResult.analysis_code == category,
                AnalysisResult.status.in_(['approved', 'pending_review']),
            )
            .order_by(AnalysisResult.id.desc())
            .all()
        )
        seen = set()
        for ar in prev_ars:
            if ar.sample_id not in seen:
                seen.add(ar.sample_id)
                try:
                    rd = json.loads(ar.raw_data or '{}')
                    val = rd.get(result_key)
                    if val is not None:
                        prev_results[ar.sample_id] = val
                except (json.JSONDecodeError, TypeError):
                    pass

    return jsonify([{
        'id': s.id,
        'sample_code': s.sample_code,
        'client_name': s.client_name,
        'status': s.status,
        'sample_date': s.sample_date.isoformat() if s.sample_date else None,
        'sampled_by': s.sampled_by or '',
        'sampling_location': s.sampling_location or '',
        'prev_result': prev_results.get(s.id),
    } for s in samples])


@micro_bp.route('/api/data')
@login_required
@lab_required('microbiology')
def micro_grid_data():
    """Микробиологийн дээжний жагсаалт (grid-д зориулсан)."""
    q = Sample.query.filter(
        Sample.lab_type.in_(['microbiology'])
    )
    date_from = request.args.get('date_from')
    date_to = request.args.get('date_to')
    if date_from:
        q = q.filter(Sample.sample_date >= datetime.strptime(date_from, '%Y-%m-%d').date())
    if date_to:
        q = q.filter(Sample.sample_date <= datetime.strptime(date_to, '%Y-%m-%d').date())
    samples = q.order_by(Sample.id.desc()).limit(500).all()

    result = []
    for idx, s in enumerate(reversed(samples), 1):
        display_name = _parse_display_name(s.sample_code)

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


@micro_bp.route('/api/save_results', methods=['POST'])
@login_required
@lab_required('microbiology')
def save_results():
    """Үр дүн хадгалах (нэг дээжид). H-1 fix: UPSERT логик нэмэгдсэн."""
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data provided'}), 400

    sample = db.session.get(Sample, data.get('sample_id'))
    if not sample:
        return jsonify({'error': 'Sample not found'}), 404

    analysis_code = data.get('analysis_code')
    raw = json.dumps(data.get('results', {}), ensure_ascii=False)

    # UPSERT: pending/rejected байвал шинэчлэх
    ar = AnalysisResult.query.filter_by(
        sample_id=sample.id,
        analysis_code=analysis_code,
    ).filter(
        AnalysisResult.status.in_(['pending_review', 'rejected'])
    ).first()

    if ar:
        ar.raw_data = raw
        ar.user_id = current_user.id
        ar.status = 'pending_review'
    else:
        ar = AnalysisResult(
            sample_id=sample.id,
            analysis_code=analysis_code,
            raw_data=raw,
            user_id=current_user.id,
        )
        db.session.add(ar)

    if not safe_commit():
        return jsonify({'error': 'DB error'}), 500
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

        # CC-4: Lock parent sample row to serialize concurrent saves
        sample = Sample.query.filter_by(sample_code=sample_code).with_for_update().first()
        if not sample:
            errors.append(f'Sample not found. {sample_code}')
            continue

        analysis_code = category
        raw = json.dumps({
            'sample_code': sample_code,
            'start_date': row.get('start_date'),
            'end_date': row.get('end_date'),
            'category': category,
            **results,
        }, ensure_ascii=False)

        try:
            with db.session.begin_nested():
                existing = AnalysisResult.query.filter_by(
                    sample_id=sample.id,
                    analysis_code=analysis_code,
                ).with_for_update().first()

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
        except SQLAlchemyError as e:
            current_app.logger.warning("Batch row %s failed: %s", sample_code, e)
            errors.append(f'Save failed for {sample_code}: {str(e)[:100]}')

    if not safe_commit():
        return jsonify({'error': 'DB error'}), 500
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


# ============ Summary / Archive ============

def _build_micro_row(s, results_by_code, idx):
    """Нэг дээжийг summary grid-ийн мөр болгон хөрвүүлэх."""
    row = {
        'seq': idx,
        'id': s.id,
        'sample_id': s.id,
        'sample_code': s.sample_code,
        'micro_lab_id': s.micro_lab_id or '',
        'client_name': s.client_name or '',
        'sampled_by': s.sampled_by or '',
        'sampling_location': s.sampling_location or '',
        'sample_date': s.sample_date.isoformat() if s.sample_date else None,
        'received_date': s.received_date.strftime('%Y-%m-%d %H:%M') if s.received_date else None,
        'status': s.status,
    }
    # Шинжилгээний үр дүн нэмэх
    for code in ('MICRO_WATER', 'MICRO_AIR', 'MICRO_SWAB'):
        ar = results_by_code.get((s.id, code))
        row[f'{code.lower()}_status'] = ar.status if ar else None
        if ar and ar.raw_data:
            try:
                rd = json.loads(ar.raw_data)
                for field in ('cfu_22', 'cfu_37', 'cfu_avg', 'ecoli', 'salmonella',
                              'cfu_air', 'staphylococcus', 'mold_fungi',
                              'cfu_swab', 'ecoli_swab', 'salmonella_swab', 'staphylococcus_swab',
                              'start_date', 'end_date', 'room_temp', 'room_humidity',
                              'plating_method', 'media_lot'):
                    if field in rd:
                        row[field] = rd[field]
            except (json.JSONDecodeError, TypeError):
                pass
    return row


@micro_bp.route('/summary', methods=['GET', 'POST'])
@login_required
@lab_required('microbiology')
def micro_summary():
    """Микробиологийн нэгтгэл хуудас."""
    if request.method == 'POST':
        action = request.form.get('action')
        sample_ids_str = request.form.get('sample_ids', '')
        if sample_ids_str and action == 'archive':
            from app.services import archive_samples
            sample_ids = [int(sid) for sid in sample_ids_str.split(',') if sid.isdigit()]
            result = archive_samples(sample_ids, archive=True)
            flash(result.message, 'success' if result.success else 'danger')
        return redirect(url_for('microbiology.micro_summary'))

    return render_template(
        'labs/water/microbiology/micro_summary.html',
        title='Микробиологийн шинжилгээний нэгтгэл',
    )


@micro_bp.route('/api/micro_summary_data')
@login_required
@lab_required('microbiology')
def micro_summary_data():
    """Микробиологийн нэгтгэлийн өгөгдөл (AG Grid)."""
    date_from = request.args.get('date_from')
    date_to = request.args.get('date_to')

    q = Sample.query.filter(
        Sample.lab_type == 'microbiology',
        Sample.status != 'archived',
    )
    if date_from:
        try:
            q = q.filter(Sample.sample_date >= datetime.strptime(date_from, '%Y-%m-%d').date())
        except ValueError:
            pass
    if date_to:
        try:
            q = q.filter(Sample.sample_date <= datetime.strptime(date_to, '%Y-%m-%d').date())
        except ValueError:
            pass

    samples = q.order_by(Sample.sample_date.desc(), Sample.id.desc()).limit(300).all()
    if not samples:
        return jsonify({'rows': []})

    sample_ids = [s.id for s in samples]
    all_results = AnalysisResult.query.filter(
        AnalysisResult.sample_id.in_(sample_ids),
        AnalysisResult.analysis_code.in_(['MICRO_WATER', 'MICRO_AIR', 'MICRO_SWAB']),
    ).all()
    results_by_code = {(ar.sample_id, ar.analysis_code): ar for ar in all_results}

    rows = [_build_micro_row(s, results_by_code, idx) for idx, s in enumerate(samples, 1)]
    return jsonify({'rows': rows})


@micro_bp.route('/micro_archive', methods=['GET', 'POST'])
@login_required
@lab_required('microbiology')
def micro_archive():
    """Микробиологийн архив хуудас."""
    if request.method == 'POST':
        action = request.form.get('action')
        sample_ids_str = request.form.get('sample_ids', '')
        if sample_ids_str and action == 'unarchive':
            from app.services import archive_samples
            sample_ids = [int(sid) for sid in sample_ids_str.split(',') if sid.isdigit()]
            result = archive_samples(sample_ids, archive=False)
            flash(result.message, 'success' if result.success else 'danger')
        return redirect(url_for('microbiology.micro_archive'))

    archived_count = Sample.query.filter(
        Sample.lab_type == 'microbiology',
        Sample.status == 'archived',
    ).count()
    return render_template(
        'labs/water/microbiology/micro_archive.html',
        title='Микробиологийн архив',
        archived_count=archived_count,
    )


@micro_bp.route('/api/micro_archive_data')
@login_required
@lab_required('microbiology')
def micro_archive_data():
    """Архивлагдсан микробиологийн дээж."""
    q = Sample.query.filter(
        Sample.lab_type == 'microbiology',
        Sample.status == 'archived',
    )
    date_from = request.args.get('date_from')
    date_to = request.args.get('date_to')
    if date_from:
        try:
            q = q.filter(Sample.sample_date >= datetime.strptime(date_from, '%Y-%m-%d').date())
        except ValueError:
            pass
    if date_to:
        try:
            q = q.filter(Sample.sample_date <= datetime.strptime(date_to, '%Y-%m-%d').date())
        except ValueError:
            pass

    samples = q.order_by(Sample.sample_date.desc(), Sample.id.desc()).limit(500).all()
    total = Sample.query.filter(
        Sample.lab_type == 'microbiology', Sample.status == 'archived'
    ).count()

    if not samples:
        return jsonify({'rows': [], 'total_count': total})

    sample_ids = [s.id for s in samples]
    all_results = AnalysisResult.query.filter(
        AnalysisResult.sample_id.in_(sample_ids),
        AnalysisResult.analysis_code.in_(['MICRO_WATER', 'MICRO_AIR', 'MICRO_SWAB']),
    ).all()
    results_by_code = {(ar.sample_id, ar.analysis_code): ar for ar in all_results}

    rows = [_build_micro_row(s, results_by_code, idx) for idx, s in enumerate(samples, 1)]
    return jsonify({'rows': rows, 'total_count': total})


# C-2 fix: Duplicate /api/data route устгагдсан (micro_data).
# micro_grid_data() нь бүх water/micro type шүүдэг тул зөв хувилбар.

# Report routes (dashboard, consumption, monthly plan) — тусдаа файлд
from app.labs.water_lab.microbiology import micro_reports  # noqa: E402, F401
