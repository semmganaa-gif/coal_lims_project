# app/routes/analysis_routes.py (ШИНЭЧИЛСЭН - 'ahlah_dashboard' функцийг нэмсэн)
# -*- coding: utf-8 -*-

from flask import (
    Blueprint,
    request,
    jsonify,
    current_app,
    url_for,
    redirect,
    render_template,
    flash,
    abort 
)
from flask_login import login_required, current_user
from datetime import datetime, timedelta
from math import inf
import json
from functools import wraps 

from sqlalchemy import or_, func, not_

from app import db
from app import models as M
Sample = M.Sample
AnalysisResult = M.AnalysisResult
AnalysisResultLog = M.AnalysisResultLog
AnalysisType = M.AnalysisType
User = M.User

from app.utils.datetime import now_local
from app.utils.normalize import normalize_raw_data

# ✅ КОДЫН НЭРШЛИЙН НЭГДСЭН MAP/ХЭРЭГСЭЛ
from app.utils.codes import norm_code, to_base_list, BASE_TO_ALIASES
from app.utils.conversions import calculate_all_conversions
from app.utils.parameters import PARAMETER_DEFINITIONS, get_canonical_name

analysis_bp = Blueprint("analysis", __name__)

def analysis_role_required(allowed_roles=None):
    if allowed_roles is None:
        allowed_roles = ["himich", "ahlah", "admin", "beltgegch"]
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                return redirect(url_for("main.login", next=request.url))
            if current_user.role not in allowed_roles:
                abort(403)
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def _sulfur_map_for(sample_ids):
    if not sample_ids:
        return {}
    rows = (
        AnalysisResult.query
        .filter(
            AnalysisResult.sample_id.in_(sample_ids),
            AnalysisResult.analysis_code.in_(['TS', 'St,ad']),
            AnalysisResult.status.in_(["approved", "pending_review"])
        )
        .order_by(AnalysisResult.sample_id.asc(), AnalysisResult.id.desc())
        .all()
    )
    out = {}
    for r in rows:
        if r.final_result is None:
            continue
        if r.sample_id not in out:
            try:
                out[r.sample_id] = float(r.final_result)
            except Exception:
                pass
    return out


TIMER_PRESETS = {
    "Aad": {"layout": "right", "digit_size": "xl", "editable": True, "timers": [{"label": "Зуух #1", "seconds": 3600, "note": "815°C · 60′"}, {"label": "Зуух #2", "seconds": 3600, "note": "815°C · 60′"}, {"label": "Зуух #3", "seconds": 3600, "note": "815°C · 60′"}, {"label": "Десикатор", "seconds": 900, "note": "15′"}]},
    "Vad": {"layout": "right", "digit_size": "xl", "editable": True, "timers": [{"label": "Зуух", "seconds": 25200, "note": "7:00:00"}, {"label": "Десикатор", "seconds": 900, "note": "00:15:00"}]},
    "Mad": {"layout": "right", "digit_size": "lg", "editable": True, "timers": [{"label": "Шат", "seconds": 3600, "note": "60′"}, {"label": "Десикатор", "seconds": 900, "note": "15′"}]},
    "MT": {"layout": "right", "digit_size": "lg", "editable": True, "timers": [{"label": "Шат", "seconds": 3600, "note": "60′"}, {"label": "Десикатор", "seconds": 900, "note": "15′"}]},
    "Gi": {"layout": "right", "digit_size": "xl", "editable": True, "timers": [{"label": "Шат 1", "seconds": 54000, "note": "15:00:00"}, {"label": "Шат 2", "seconds": 1800, "note": "00:30:00"}]},
    "TRD": {"layout": "right", "digit_size": "lg", "editable": True, "timers": [{"label": "Шат", "seconds": 3600, "note": "60′"}, {"label": "Десикатор", "seconds": 900, "note": "15′"}]},
    "P": {"layout": "right", "digit_size": "lg", "editable": False, "timers": []},
    "F": {"layout": "right", "digit_size": "lg", "editable": False, "timers": []},
    "Cl": {"layout": "right", "digit_size": "lg", "editable": False, "timers": []},
    "CSN": {"layout": "right", "digit_size": "lg", "editable": False, "timers": []},
    "FM": {"layout": "right", "digit_size": "lg", "editable": False, "timers": []},
    "SOLID": {"layout": "right", "digit_size": "lg", "editable": False, "timers": []},
}

SUMMARY_VIEW_COLUMNS = [
    {'code': 'MT',      'canonical_base': 'total_moisture'},
    {'code': 'Mad',     'canonical_base': 'inherent_moisture'},
    {'code': 'Aad',     'canonical_base': 'ash'},
    {'code': 'Ad',      'canonical_base': 'ash'},
    {'code': 'Vad',     'canonical_base': 'volatile_matter'},
    {'code': 'Vdaf',    'canonical_base': 'volatile_matter'},
    {'code': 'FC,ad',   'canonical_base': 'fixed_carbon_ad'},
    {'code': 'St,ad',   'canonical_base': 'total_sulfur'},
    {'code': 'St,d',    'canonical_base': 'total_sulfur'},
    {'code': 'Qgr,ad',  'canonical_base': 'calorific_value'},
    {'code': 'Qgr,ar',  'canonical_base': 'calorific_value'},
    {'code': 'Qnet,ar', 'canonical_base': 'calorific_value'},
    {'code': 'CSN',     'canonical_base': 'free_swelling_index'},
    {'code': 'Gi',      'canonical_base': 'caking_power'},
    {'code': 'TRD,ad',  'canonical_base': 'relative_density'},
    {'code': 'TRD,d',   'canonical_base': 'relative_density'}, 
    {'code': 'P,ad',    'canonical_base': 'phosphorus'},
    {'code': 'P,d',     'canonical_base': 'phosphorus'},
    {'code': 'F,ad',    'canonical_base': 'total_fluorine'},
    {'code': 'F,d',     'canonical_base': 'total_fluorine'},
    {'code': 'Cl,ad',   'canonical_base': 'total_chlorine'},
    {'code': 'Cl,d',    'canonical_base': 'total_chlorine'},
    {'code': 'X',       'canonical_base': 'plastometer_x'},
    {'code': 'Y',       'canonical_base': 'plastometer_y'},
    {'code': 'CRI',     'canonical_base': 'coke_reactivity_index'},
    {'code': 'CSR',     'canonical_base': 'coke_strength_after_reaction'},
    {'code': 'Solid',   'canonical_base': 'solid'},
    {'code': 'FM',      'canonical_base': 'free_moisture'},
    {'code': 'm',       'canonical_base': 'mass'},
]

# --------------------------------------------------------------------------------
# --- АЖЛЫН ТАЛБАР ---
# --------------------------------------------------------------------------------
@analysis_bp.route("/analysis_hub")
@login_required
@analysis_role_required(["beltgegch", "himich", "ahlah", "admin"])
def analysis_hub():
    user_role = current_user.role
    if user_role in ["admin", "ahlah"]:
        allowed_analyses = AnalysisType.query.order_by(AnalysisType.order_num).all()
    else:
        allowed_analyses = (
            AnalysisType.query
            .filter_by(required_role=user_role)
            .order_by(AnalysisType.order_num)
            .all()
        )
    return render_template(
        "analysis_hub.html",
        title="Ажлын талбар",
        analysis_types=allowed_analyses,
    )

# --------------------------------------------------------------------------------
# --- АЖЛЫН ХУУДАС ---
# --------------------------------------------------------------------------------
@analysis_bp.route('/analysis_page/<analysis_code>')
@login_required
def analysis_page(analysis_code):
    analysis_type = AnalysisType.query.filter_by(code=analysis_code).first_or_404()
    base_code = norm_code(analysis_type.code) or analysis_type.code
    
    AnalysisView = type("AnalysisView", (), {})
    analysis_view = AnalysisView()
    analysis_view.code = base_code
    analysis_view.name = analysis_type.name

    newly_selected_ids_str = request.args.get('sample_ids', '')
    newly_selected_ids = {int(x) for x in newly_selected_ids_str.split(',') if x.isdigit()}

    approved_sample_ids_subq = (
        db.session.query(AnalysisResult.sample_id)
        .filter(AnalysisResult.analysis_code == analysis_type.code,
                AnalysisResult.status == 'approved')
        .distinct()
        .subquery()
    )
    approved_ids_scalar = db.select(approved_sample_ids_subq.c.sample_id).scalar_subquery()

    previously_saved_results_query = (
        AnalysisResult.query.with_entities(AnalysisResult.sample_id)
        .filter(AnalysisResult.user_id == current_user.id,
                AnalysisResult.analysis_code == analysis_type.code,
                ~AnalysisResult.sample_id.in_(approved_ids_scalar))
        .distinct()
    )
    previously_saved_ids = {row.sample_id for row in previously_saved_results_query.all()}

    all_potential_sample_ids = list(newly_selected_ids.union(previously_saved_ids))

    samples_to_analyze = []
    if all_potential_sample_ids:
        samples_dict = {
            s.id: s
            for s in Sample.query.filter(
                Sample.id.in_(all_potential_sample_ids),
                ~Sample.id.in_(approved_ids_scalar)
            ).all()
        }
        samples_to_analyze = [samples_dict[sid] for sid in all_potential_sample_ids if sid in samples_dict]

    # Vad, TRD → Mad map
    mad_results_map = {}
    if (analysis_type.code == 'Vad' or analysis_type.code == 'TRD') and samples_to_analyze:
        sample_ids = [s.id for s in samples_to_analyze]
        approved_mad_results = (
            AnalysisResult.query
            .filter(AnalysisResult.sample_id.in_(sample_ids),
                    AnalysisResult.analysis_code == 'Mad',
                    AnalysisResult.status == 'approved')
            .all()
        )
        mad_results_map = {r.sample_id: r.final_result for r in approved_mad_results}

    # CV дээр S map
    sulfur_by_sample = {}
    if samples_to_analyze and base_code == 'CV':
        sample_ids = [s.id for s in samples_to_analyze]
        sulfur_by_sample = _sulfur_map_for(sample_ids)

    # Буцаасан мөрүүд
    rejected_samples_info = {}
    if samples_to_analyze:
        sample_ids = [s.id for s in samples_to_analyze]
        rejected_results = (
            AnalysisResult.query
            .filter(AnalysisResult.sample_id.in_(sample_ids),
                    AnalysisResult.analysis_code == analysis_type.code,
                    AnalysisResult.status == 'rejected')
            .all()
        )
        for r in rejected_results:
            reason_val = (
                getattr(r, 'rejection_comment', None)
                or getattr(r, 'reason', None)
                or 'Ахлах буцаасан (Дахин шалгах)'
            )
            rejected_samples_info[r.sample_id] = {
                'reason': reason_val,
                'rejected_at': r.updated_at.strftime('%Y-%m-%d %H:%M') if r.updated_at else ''
            }

    # Өмнө хадгалсан (pending/rejected) үр дүнг сэргээх
    existing_results_map = {}
    if samples_to_analyze:
        sample_ids = [s.id for s in samples_to_analyze]
        existing_results = (
            AnalysisResult.query
            .filter(AnalysisResult.sample_id.in_(sample_ids),
                    AnalysisResult.analysis_code == analysis_type.code,
                    AnalysisResult.status.in_(['pending_review', 'rejected']))
            .all()
        )
        for r in existing_results:
            existing_results_map[r.sample_id] = {
                'status': r.status,
                'raw_data': r.raw_data,
                'final_result': r.final_result
            }

    analysis_configs = {
        'Aad': { 'template': 'analysis_forms/ash_form.html',          'formula': 'ash',            'repeatability_limit': 0.3 },
        'Mad': { 'template': 'analysis_forms/moisture_form.html',      'formula': 'moisture',       'repeatability_limit': 0.2 },
        'Vad': { 'template': 'analysis_forms/volatile_form.html',      'formula': 'volatile',       'repeatability_limit': 0.5 },
        'MT':  { 'template': 'analysis_forms/total_moisture_form.html','formula': 'total_moisture', 'repeatability_limit': 0.5 },
        'TS':  { 'template': 'analysis_forms/sulfur_form.html',        'formula': 'sulfur',         'repeatability_limit': 0.05 },
        'CV':  { 'template': 'analysis_forms/cv_form.html',            'formula': 'cv',             'repeatability_limit': 120 },
        'FM':  { 'template': 'analysis_forms/free_moisture_form.html', 'formula': 'FM',             'repeatability_limit': 0 },
        'CSN': { 'template': 'analysis_forms/csn_form.html',           'formula': 'CSN',            'repeatability_limit': 0.5 },
        'Gi':  { 'template': 'analysis_forms/Gi_form.html',            'formula': 'Gi',             'repeatability_limit': 2.0 },
        'TRD': { 'template': 'analysis_forms/trd_form.html',           'formula': 'TRD',            'repeatability_limit': 0 },
        'P':   { 'template': 'analysis_forms/phosphorus_form.html',    'formula': 'phosphorus',     'repeatability_limit': 0 },
        'F':   { 'template': 'analysis_forms/fluorine_form.html',      'formula': 'fluorine',       'repeatability_limit': 0 },
        'Cl':  { 'template': 'analysis_forms/chlorine_form.html',      'formula': 'chlorine',       'repeatability_limit': 0 },
        'X':   { 'template': 'analysis_forms/xy_form.html',            'formula': 'XY',             'repeatability_limit': 0 },
        'Y':   { 'template': 'analysis_forms/xy_form.html',            'formula': 'XY',             'repeatability_limit': 0 },
        'CRI': { 'template': 'analysis_forms/cricsr_form.html',        'formula': 'CRICSR',         'repeatability_limit': 0 },
        'CSR': { 'template': 'analysis_forms/cricsr_form.html',        'formula': 'CRICSR',         'repeatability_limit': 0 },
        'Solid': { 'template': 'analysis_forms/solid_form.html',       'formula': 'solid',          'repeatability_limit': 0 },
        'SOLID': { 'template': 'analysis_forms/solid_form.html',       'formula': 'solid',          'repeatability_limit': 0 },
        'm':   { 'template': 'analysis_forms/mass_workspace_form.html','formula': 'mass',           'repeatability_limit': 0 },
        'H':   { 'template': 'analysis_forms/default_form.html',       'formula': 'none',           'repeatability_limit': 0 },
        'FC':  { 'template': 'analysis_forms/default_form.html',       'formula': 'none',           'repeatability_limit': 0 },
    }

    config = (
        analysis_configs.get(base_code)
        or analysis_configs.get(analysis_type.code)
        or {"template": "analysis_forms/default_form.html", "formula": "none", "repeatability_limit": 0}
    )
    timer_config = (
        TIMER_PRESETS.get(base_code)
        or TIMER_PRESETS.get(analysis_type.code)
        or {"layout": "right", "digit_size": "lg", "editable": False, "timers": []}
    )

    gi_retest_modes = {}
    if base_code == 'Gi':
        for sample_id, info in rejected_samples_info.items():
            if info.get('reason') == 'GI_RETEST_3_3':
                gi_retest_modes[sample_id] = True

    return render_template(
        "analysis_page.html",
        title=analysis_type.name,
        analysis=analysis_view,
        analysis_type=analysis_type,
        analysis_code=analysis_type.code,
        analysis_name=analysis_type.name,
        samples=samples_to_analyze,
        config=config,
        mad_results_map=mad_results_map,
        rejected_samples_info=rejected_samples_info,
        existing_results_map=existing_results_map,
        timer_config=timer_config,
        gi_retest_modes=gi_retest_modes,
        sulfur_by_sample=sulfur_by_sample,
    )

# --------------------------------------------------------------------------------
# --- АХЛАХЫН ХЯНАЛТЫН САМБАР ---
# --------------------------------------------------------------------------------
@analysis_bp.route("/ahlah_dashboard", endpoint="ahlah_dashboard")
@login_required
@analysis_role_required(["ahlah", "admin"])
def ahlah_dashboard():
    return render_template(
        "ahlah_dashboard.html",
        title="Ахлахын хяналтын самбар",
        request=request
    )

@analysis_bp.route("/api/ahlah_data")
@login_required
@analysis_role_required(["ahlah", "admin"])
def api_ahlah_data():
    start_date = request.args.get("start_date")
    end_date = request.args.get("end_date")
    sample_name = request.args.get("sample_name")

    q = (
        db.session.query(AnalysisResult, Sample, User, AnalysisType)
        .join(Sample, AnalysisResult.sample_id == Sample.id)
        .join(User, AnalysisResult.user_id == User.id)
        .join(AnalysisType, AnalysisResult.analysis_code == AnalysisType.code)
        .filter(or_(AnalysisResult.status == "pending_review",
                    AnalysisResult.status == "rejected"))
    )

    if start_date:
        try:
            sd = datetime.strptime(start_date, "%Y-%m-%d")
            q = q.filter(AnalysisResult.updated_at >= sd)
        except ValueError:
            pass
    if end_date:
        try:
            ed = datetime.strptime(end_date, "%Y-%m-%d")
            ed = datetime.combine(ed, datetime.max.time())
            q = q.filter(AnalysisResult.updated_at <= ed)
        except ValueError:
            pass
    if sample_name:
        q = q.filter(Sample.sample_code.ilike(f"%{sample_name}%"))

    results_to_review = q.order_by(AnalysisResult.updated_at.desc()).all()

    processed_results = []
    for result, sample, user, analysis_type in results_to_review:
        data_dict = {}
        raw_data = result.raw_data
        if isinstance(raw_data, str):
            try:
                data_dict = json.loads(raw_data)
            except json.JSONDecodeError:
                pass
        elif isinstance(raw_data, dict):
            data_dict = raw_data

        is_csn = (analysis_type.code == 'CSN')
        diff = data_dict.get('diff')
        avg  = data_dict.get('avg')

        t_val = data_dict.get('t') if is_csn else diff
        avg_val = data_dict.get('avg') if is_csn else avg
        final_display = avg_val if not is_csn else result.final_result

        processed_results.append({
            "result_id": result.id,
            "sample_code": sample.sample_code,
            "analysis_name": analysis_type.name,
            "analysis_code": analysis_type.code,
            "status": result.status,
            "raw_data": data_dict,
            "t_value": t_val,
            "final_value": final_display if final_display is not None else result.final_result,
            "user_name": user.username,
            "updated_at": result.updated_at.strftime('%Y-%m-%d %H:%M') if result.updated_at else None
        })

    return jsonify(processed_results)
# -----------------------------------------------------------
# 5) ДЭЭЖНИЙ НЭГТГЭЛ (sample_summary)
# -----------------------------------------------------------
@analysis_bp.route("/sample_summary", methods=["GET", "POST"])
@login_required
def sample_summary():

    # --- POST (Архивлах) ---
    if request.method == "POST":
        action = request.form.get("action")
        sample_ids_str = request.form.get("sample_ids")
        if sample_ids_str and action in ["archive", "unarchive"]:
            try:
                sample_ids = [int(sid) for sid in sample_ids_str.split(',') if sid.isdigit()]
                if sample_ids:
                    new_status = "archived" if action == "archive" else "new" 
                    updated_count = (
                        db.session.query(Sample)
                        .filter(Sample.id.in_(sample_ids))
                        .update({Sample.status: new_status}, synchronize_session=False)
                    )
                    db.session.commit()
                    msg = (
                        f"{updated_count} дээжийг амжилттай архивд шилжүүллээ."
                        if action == "archive"
                        else f"{updated_count} дээжийг архивнаас амжилттай сэргээллээ."
                    )
                    flash(msg, "success")
                return redirect(url_for('analysis.sample_summary', **request.args))
            except Exception as e:
                db.session.rollback()
                flash(f"Архивлах үед алдаа гарлаа: {e}", "danger")

    # -----------------------------------------------------------------
    # --- GET (Хуудас ачааллах) ---
    # -----------------------------------------------------------------

    page = request.args.get("page", 1, type=int)
    start_date_str = request.args.get("start_date")
    end_date_str = request.args.get("end_date")
    show_archived = request.args.get("show_archived") == "on"
    filter_name = request.args.get("filter_name")

    # 1. Дээжүүдийг шүүж авах
    query = db.session.query(Sample)
    if show_archived:
        query = query.filter(Sample.status == "archived")
    else:
        query = query.filter(Sample.status != "archived")

    exists_q = (
        db.session.query(AnalysisResult.id)
        .filter(
            AnalysisResult.sample_id == Sample.id,
            AnalysisResult.status.in_(["approved", "pending_review"]),
        )
        .exists()
    )
    query = query.filter(exists_q)

    if start_date_str:
        try:
            start_date = datetime.strptime(start_date_str, "%Y-%m-%d")
            query = query.filter(Sample.received_date >= start_date)
        except ValueError:
            flash(f"'{start_date_str}' буруу огнооны формат байна.", "warning")
    if end_date_str:
        try:
            end_date = datetime.strptime(end_date_str, "%Y-%m-%d") + timedelta(days=1)
            query = query.filter(Sample.received_date < end_date)
        except ValueError:
            flash(f"'{end_date_str}' буруу огнооны формат байна.", "warning")
    if filter_name:
        query = query.filter(Sample.sample_code.ilike(f"%{filter_name}%"))

    query = query.order_by(Sample.received_date.desc())
    pagination = query.paginate(page=page, per_page=50, error_out=False)
    samples = pagination.items

    # -----------------------------------------------------------------
    # 🧮 ШИНЭЧИЛСЭН ТООЦООЛЛЫН ЛОГИК
    # -----------------------------------------------------------------

    results_map = {}
    analysis_dates_map = {}

    if samples:
        sample_ids = [s.id for s in samples]

        # 2) түүхий үр дүнг нэг дор
        all_db_results = (
            AnalysisResult.query
            .filter(
                AnalysisResult.sample_id.in_(sample_ids),
                AnalysisResult.status.in_(["approved", "pending_review"]),
            )
            .all()
        )

        # 3) sample + canonical
        canonical_results_by_sample = {sid: {} for sid in sample_ids}
        analysis_dates_raw_map = {sid: [] for sid in sample_ids}

        for r in all_db_results:
            canonical_name = get_canonical_name(r.analysis_code)
            if canonical_name:
                canonical_results_by_sample[r.sample_id][canonical_name] = {
                    "value": r.final_result,
                    "id": r.id,
                    "status": r.status,
                }
            if r.created_at:
                analysis_dates_raw_map[r.sample_id].append(r.created_at)

        # 4) тооцооллын хөдөлгүүр
        for sample_id in sample_ids:
            raw_canonical_data = canonical_results_by_sample.get(sample_id, {})

            all_calculated_data = calculate_all_conversions(
                raw_canonical_data,
                PARAMETER_DEFINITIONS
            )

            # 5) Template-д зориулж alias руу буцаах
            final_data_for_template = {}
            for col_view in SUMMARY_VIEW_COLUMNS:
                template_code = col_view['code']
                canonical_base = col_view['canonical_base']

                lookup_key = get_canonical_name(template_code)

                if   template_code == 'Ad':     lookup_key = 'ash_d'
                elif template_code == 'Vdaf':   lookup_key = 'volatile_matter_daf'
                elif template_code == 'FC,ad':  lookup_key = 'fixed_carbon_ad'
                elif template_code == 'FC,d':   lookup_key = 'fixed_carbon_d'
                elif template_code == 'FC,daf': lookup_key = 'fixed_carbon_daf'
                elif template_code == 'St,d':   lookup_key = 'total_sulfur_d'
                elif template_code == 'St,daf': lookup_key = 'total_sulfur_daf'
                elif template_code == 'Qgr,d':  lookup_key = 'calorific_value_d'
                elif template_code == 'Qgr,daf': lookup_key = 'calorific_value_daf'
                elif template_code == 'Qnet,ar': lookup_key = 'qnet_ar'
                # (!!! ШИНЭЧЛЭЛ)
                elif template_code == 'TRD,ad': lookup_key = 'relative_density'
                elif template_code == 'TRD,d':  lookup_key = 'relative_density_d'
                # (/!!! ШИНЭЧЛЭЛ)
                elif template_code == 'H,d':     lookup_key = 'hydrogen_d'
                elif template_code == 'P,d':     lookup_key = 'phosphorus_d'
                elif template_code == 'F,d':     lookup_key = 'total_fluorine_d'
                elif template_code == 'Cl,d':    lookup_key = 'total_chlorine_d'

                if lookup_key in all_calculated_data:
                    calculated_value = all_calculated_data[lookup_key]
                    if calculated_value is None:
                        continue

                    if isinstance(calculated_value, (int, float)):
                        raw_data_base = raw_canonical_data.get(canonical_base, {})
                        final_data_for_template[template_code] = {
                            "value": calculated_value,
                            "id": raw_data_base.get('id'),
                            "status": "calculated"
                        }
                    elif isinstance(calculated_value, dict):
                        final_data_for_template[template_code] = calculated_value

            results_map[sample_id] = final_data_for_template

        # 6) хамгийн эртний огноо
        for sample_id, dates in analysis_dates_raw_map.items():
            if dates:
                analysis_dates_map[sample_id] = min(dates).strftime("%Y-%m-%d")

        # 7) grid-д харуулах нэршлүүд
        final_analysis_types = []
        for col_map in SUMMARY_VIEW_COLUMNS:
            final_code = col_map['code']
            canonical_name = get_canonical_name(final_code)

            if   final_code == 'Ad':     canonical_name = 'ash_d'
            elif final_code == 'Vdaf':   canonical_name = 'volatile_matter_daf'
            elif final_code == 'FC,ad':  canonical_name = 'fixed_carbon_ad'
            elif final_code == 'FC,d':   canonical_name = 'fixed_carbon_d'
            elif final_code == 'FC,daf': canonical_name = 'fixed_carbon_daf'
            elif final_code == 'St,d':   canonical_name = 'total_sulfur_d'
            elif final_code == 'St,daf': canonical_name = 'total_sulfur_daf'
            elif final_code == 'Qgr,d':  canonical_name = 'calorific_value_d'
            elif final_code == 'Qgr,daf': canonical_name = 'calorific_value_daf'
            elif final_code == 'Qnet,ar': canonical_name = 'qnet_ar'
            # (!!! ШИНЭЧЛЭЛ)
            elif final_code == 'TRD,ad': canonical_name = 'relative_density'
            elif final_code == 'TRD,d':  canonical_name = 'relative_density_d'
            # (/!!! ШИНЭЧЛЭЛ)
            elif final_code == 'H,d':    canonical_name = 'hydrogen_d'
            elif final_code == 'P,d':    canonical_name = 'phosphorus_d'
            elif final_code == 'F,d':    canonical_name = 'total_fluorine_d'
            elif final_code == 'Cl,d':   canonical_name = 'total_chlorine_d'

            details = PARAMETER_DEFINITIONS.get(canonical_name)
            display_name = final_code
            if details and details.get('display_name'):
                display_name = details['display_name']
            
            fake_analysis_type = AnalysisType(code=final_code, name=display_name)
            final_analysis_types.append(fake_analysis_type)

    return render_template(
        "sample_summary.html",
        title="Дээжний нэгтгэл",
        samples=samples,
        analysis_types=final_analysis_types,
        results_map=results_map,
        analysis_dates_map=analysis_dates_map,
        pagination=pagination,
        show_archived=show_archived
    )


# -----------------------------------------------------------
# 6) ДЭЭЖНИЙ ТАЙЛАН
# -----------------------------------------------------------
@analysis_bp.route("/sample_report/<int:sample_id>")
@login_required
def sample_report(sample_id):
    sample = Sample.query.get_or_404(sample_id)
    report_date = now_local()
    
    raw_results = (
        AnalysisResult.query
        .filter(
            AnalysisResult.sample_id == sample_id,
            AnalysisResult.status.in_(["approved", "pending_review"])
        )
        .all()
    )
    
    raw_canonical_data = {}
    for r in raw_results:
        canonical_name = get_canonical_name(r.analysis_code)
        if canonical_name:
            raw_canonical_data[canonical_name] = {
                "value": r.final_result,
                "id": r.id,
                "status": r.status,
            }

    try:
        sample_calcs = calculate_all_conversions(
            raw_canonical_data,
            PARAMETER_DEFINITIONS
        )
    except Exception as e:
        flash(
            f"Тооцоолол хийхэд алдаа гарлаа: {e}. Шаардлагатай (MT, Mad) утгууд орсон эсэхийг шалгана уу.",
            "danger",
        )
        return redirect(request.referrer or url_for("analysis.sample_summary"))

    return render_template(
        "report.html",
        title=f"Тайлан: {sample.sample_code}",
        sample=sample,
        calcs=sample_calcs, 
        report_date=report_date,
    )


# -----------------------------------------------------------
# 7) АУДИТЫН ТӨВ
# -----------------------------------------------------------
@analysis_bp.route("/audit_hub")
@login_required
def audit_hub():
    return render_template("audit_hub.html", title="Аудитын мөр")


# -----------------------------------------------------------
# 8) АУДИТЫН МӨР ХУУДАС
# -----------------------------------------------------------
@analysis_bp.route("/audit_log/<analysis_code>")
@login_required
def audit_log_page(analysis_code):
    analysis_type = AnalysisType.query.filter_by(code=analysis_code).first_or_404()

    start_date_str = request.args.get("start_date")
    end_date_str = request.args.get("end_date")
    sample_name_str = request.args.get("sample_name")
    user_name_str = request.args.get("user_name")

    q = (
        db.session.query(AnalysisResultLog, Sample, User)
        .join(Sample, AnalysisResultLog.sample_id == Sample.id)
        .join(User, AnalysisResultLog.user_id == User.id)
        .filter(AnalysisResultLog.analysis_code == analysis_code)
    )

    if start_date_str:
        try:
            start_date = datetime.strptime(start_date_str, "%Y-%m-%d")
            q = q.filter(AnalysisResultLog.timestamp >= start_date)
        except ValueError:
            flash("Буруу эхлэх огноо.", "warning")
    if end_date_str:
        try:
            end_date = datetime.strptime(end_date_str, "%Y-%m-%d")
            end_dt = datetime.combine(end_date, datetime.max.time())
            q = q.filter(AnalysisResultLog.timestamp <= end_dt)
        except ValueError:
            flash("Буруу дуусах огноо.", "warning")
    if sample_name_str:
        q = q.filter(Sample.sample_code.ilike(f"%{sample_name_str}%"))
    if user_name_str:
        q = q.filter(User.username.ilike(f"%{user_name_str}%"))

    rows = q.order_by(AnalysisResultLog.timestamp.desc()).all()

    prepared_logs = []
    for log_obj, sample_obj, user_obj in rows:
        view_obj = type("AuditView", (), {})()
        view_obj.id = log_obj.id
        view_obj.sample_id = log_obj.sample_id
        view_obj.analysis_result_id = log_obj.analysis_result_id
        view_obj.analysis_code = log_obj.analysis_code
        view_obj.action = log_obj.action
        view_obj.final_result_snapshot = log_obj.final_result_snapshot
        view_obj.raw_data_snapshot = log_obj.raw_data_snapshot
        view_obj.reason = log_obj.reason
        view_obj.timestamp = log_obj.timestamp
        view_obj.sample = sample_obj
        view_obj.user = user_obj
        prepared_logs.append(view_obj)

    from app.utils.normalize import normalize_raw_data

    def get_log_raw_data(log):
        try:
            parsed = json.loads(log.raw_data_snapshot or "{}")
        except Exception:
            parsed = {}
        return normalize_raw_data(parsed, analysis_type.code)

    return render_template(
        "audit_log_page.html",
        title=f"Аудит: {analysis_type.name}",
        analysis_type=analysis_type,
        logs=prepared_logs,
        get_log_raw_data=get_log_raw_data,
    )

# -----------------------------------------------------------
# 9) ДЭЭЖНИЙ ТҮҮХ
# -----------------------------------------------------------
@analysis_bp.route("/sample_history/<int:sample_id>")
@login_required
def sample_history(sample_id):
    sample = Sample.query.get_or_404(sample_id)
    results = (
        AnalysisResult.query
        .filter_by(sample_id=sample_id)
        .order_by(AnalysisResult.created_at.desc())
        .all()
    )
    logs = (
        AnalysisResultLog.query
        .filter_by(sample_id=sample_id)
        .order_by(AnalysisResultLog.timestamp.desc())
        .all()
    )
    return render_template(
        "sample_history.html",
        title=f"Түүх: {sample.sample_code}",
        sample=sample,
        results=results,
        logs=logs,
    )