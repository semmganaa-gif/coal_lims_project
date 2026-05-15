# app/routes/admin/routes.py
# -*- coding: utf-8 -*-
"""
Админ удирдлагын модуль.

Энэ модуль нь хэрэглэгчийн удирдлага, шинжилгээний тохиргоо,
хяналтын стандартууд болон GBW стандартуудын удирдлагыг хариуцна.
"""

import logging

from flask import render_template, flash, redirect, url_for, request, abort, Blueprint, jsonify
from flask_login import login_required, current_user
from flask_babel import lazy_gettext as _l

from sqlalchemy import select

from app import db
from app.constants import CHPP_CONFIG_GROUPS
from app.forms import UserManagementForm, SimpleProfileForm
from app.models import User, AnalysisProfile
from app.repositories import (
    AnalysisTypeRepository, GbwStandardRepository,
    ControlStandardRepository, UserRepository,
    AnalysisProfileRepository,
)
from app.utils.decorators import admin_required, senior_or_admin_required
from app.services.admin_service import (
    seed_analysis_types,
    auto_populate_profiles,
    load_gi_shift_config,
    validate_and_create_user,
    update_user as svc_update_user,
    delete_user as svc_delete_user,
    save_analysis_config,
    create_standard as svc_create_standard,
    update_standard as svc_update_standard,
    delete_standard as svc_delete_standard,
    activate_standard as svc_activate_standard,
    create_gbw as svc_create_gbw,
    update_gbw as svc_update_gbw,
    delete_gbw as svc_delete_gbw,
    activate_gbw as svc_activate_gbw,
    delete_pattern_profile as svc_delete_pattern_profile,
    deactivate_gbw as svc_deactivate_gbw,
)

logger = logging.getLogger(__name__)

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

# admin_required, senior_or_admin_required нь `app.utils.decorators`-аас
# импорт хийгдсэн (өмнө нь хоёр газар хуулбарласан байсныг нэгтгэв).


# ==============================================================================
# 1. ХЭРЭГЛЭГЧИЙН УДИРДЛАГА
# ==============================================================================
@admin_bp.route('/manage_users', methods=['GET', 'POST'])
@login_required
@admin_required
def manage_users():
    """Хэрэглэгчийн удирдлагын хуудас."""
    form = UserManagementForm()
    if form.validate_on_submit():
        success, message, user_id = validate_and_create_user(
            username=form.username.data,
            password=form.password.data,
            role=form.role.data,
            full_name=form.full_name.data or None,
            email=form.email.data or None,
            phone=form.phone.data or None,
            position=form.position.data or None,
            allowed_labs=form.allowed_labs.data or ['coal'],
        )
        if not success:
            if '\n' in message:
                # Schema validation failed — multiple error messages, re-render form
                for msg in message.split('\n'):
                    flash(msg, 'danger')
                users = list(db.session.execute(
                    select(User).order_by(User.id)
                ).scalars().all())
                return render_template('manage_users.html', title='Хэрэглэгчийн удирдлага', users=users, form=form)
            elif 'Нууц үг' in message:
                # Password policy failed — re-render form
                flash(message, 'danger')
                users = list(db.session.execute(
                    select(User).order_by(User.id)
                ).scalars().all())
                return render_template('manage_users.html', title='Хэрэглэгчийн удирдлага', users=users, form=form)
            elif 'аль хэдийн' in message:
                # Duplicate username
                flash(message, 'warning')
            else:
                # Admin constraint or DB error
                flash(message, 'danger')
        else:
            flash(message, 'success')
        return redirect(url_for('admin.manage_users'))

    users = list(db.session.execute(
        select(User).order_by(User.id)
    ).scalars().all())
    return render_template('manage_users.html', title='Хэрэглэгчийн удирдлага', users=users, form=form)


@admin_bp.route('/edit_user/<int:user_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_user(user_id):
    """Хэрэглэгчийн мэдээлэл засах."""
    user_to_edit = UserRepository.get_by_id_or_404(user_id)
    form = UserManagementForm(obj=user_to_edit)

    if form.validate_on_submit():
        success, message = svc_update_user(
            user_id=user_id,
            username=form.username.data,
            password=form.password.data,
            role=form.role.data,
            full_name=form.full_name.data or None,
            email=form.email.data or None,
            phone=form.phone.data or None,
            position=form.position.data or None,
            allowed_labs=form.allowed_labs.data or ['coal'],
        )
        if message == 'not_found':
            abort(404)
        if not success:
            flash(message, 'danger')
            # Duplicate or password error — re-render form
            return render_template('edit_user.html',
                                   title='Хэрэглэгч засах',
                                   form=form,
                                   user=user_to_edit)
        # Success — may include admin role warning prefix
        if 'эрхийн түвшинг' in message:
            # Split: warning part + success part
            parts = message.split(' ', 1)
            warning_msg = 'Админ хэрэглэгчийн эрхийн түвшинг өөрчлөх боломжгүй.'
            success_msg = message.replace(warning_msg + ' ', '')
            flash(warning_msg, 'warning')
            flash(success_msg, 'success')
        else:
            flash(message, 'success')
        return redirect(url_for('admin.manage_users'))

    form.username.data = user_to_edit.username
    form.role.data = user_to_edit.role
    form.allowed_labs.data = user_to_edit.allowed_labs or ['coal']
    # Профайл мэдээллийг form-д дүүргэх
    form.full_name.data = user_to_edit.full_name or ""
    form.email.data = user_to_edit.email or ""
    form.phone.data = user_to_edit.phone or ""
    form.position.data = user_to_edit.position or ""
    return render_template('edit_user.html', title='Хэрэглэгч засах', form=form, user=user_to_edit)


@admin_bp.route('/delete_user/<int:user_id>', methods=['POST'])
@login_required
@admin_required
def delete_user(user_id):
    """Хэрэглэгч устгах."""
    success, message = svc_delete_user(user_id, current_user.id)
    if message == 'not_found':
        abort(404)
    flash(message, 'success' if success else 'danger')
    return redirect(url_for('admin.manage_users'))


# ==============================================================================
# 2. ШИНЖИЛГЭЭНИЙ ТОХИРГОО (ANALYSIS CONFIG)
# ==============================================================================
@admin_bp.route('/analysis_config', methods=['GET', 'POST'])
@login_required
@senior_or_admin_required
def analysis_config():
    """Шинжилгээний тохиргоо удирдах."""
    # 1. DB Sync
    seed_analysis_types()

    # 2. --- FORM SUBMIT (POST эхэнд шалгах) ---
    if request.method == 'POST':
        success, message = save_analysis_config(request.form)
        flash(message, 'success' if success else 'danger')
        return redirect(url_for('admin.analysis_config'))

    # 3. Auto-populate profiles
    if auto_populate_profiles():
        return redirect(url_for('admin.analysis_config'))

    # 4. Data Fetch for GET
    # MG codes belong to WTL_MG multi-code page — exclude from config matrix
    MG_EXCLUDE = ['MG', 'MG_SIZE']
    analysis_types = AnalysisTypeRepository.get_all_excluding(MG_EXCLUDE)

    simple_profiles = AnalysisProfileRepository.get_simple_profiles(ordered=True)
    chpp_profiles = AnalysisProfileRepository.get_chpp_profiles(ordered=True)

    simple_form = SimpleProfileForm()

    from app.services.sla_service import get_sla_config_all, DEFAULT_SLA_HOURS, DEFAULT_SLA_FALLBACK

    # SLA config map: {"CHPP:2 hourly": 48, "QC": 72, ...}
    sla_configs = get_sla_config_all()
    sla_config_map = {}
    for c in sla_configs:
        key = f"{c['client_name']}:{c['sample_type']}" if c['sample_type'] else c['client_name']
        sla_config_map[key] = c['hours']

    return render_template(
        'analysis_config.html',
        simple_form=simple_form,
        analysis_types=analysis_types,
        simple_profiles=simple_profiles,
        chpp_profiles=chpp_profiles,
        chpp_config_groups=CHPP_CONFIG_GROUPS,
        gi_shift_config=load_gi_shift_config(),
        sla_config_map=sla_config_map,
        sla_defaults=DEFAULT_SLA_HOURS,
        sla_fallback=DEFAULT_SLA_FALLBACK,
    )


# ==============================================================================
# 2.1 ШИНЭ ЭНГИЙН ТОХИРГОО (Card-based UI)
# ==============================================================================
@admin_bp.route('/analysis_config_simple', methods=['GET'])
@login_required
@senior_or_admin_required
def analysis_config_simple():
    """Шинэ энгийн Card-based шинжилгээний тохиргоо"""
    seed_analysis_types()
    auto_populate_profiles()

    # Fetch data
    analysis_types = AnalysisTypeRepository.get_all_ordered()

    # Simple profiles grouped by client
    simple_profiles = AnalysisProfileRepository.get_simple_profiles(ordered=True)

    # Group by client name
    grouped_profiles = {}
    for profile in simple_profiles:
        if profile.client_name not in grouped_profiles:
            grouped_profiles[profile.client_name] = []
        grouped_profiles[profile.client_name].append(profile)

    # CHPP profiles
    chpp_profiles = AnalysisProfileRepository.get_chpp_profiles(ordered=True)

    from app.services.sla_service import get_sla_config_all, DEFAULT_SLA_HOURS, DEFAULT_SLA_FALLBACK

    sla_configs = get_sla_config_all()
    sla_config_map = {}
    for c in sla_configs:
        key = f"{c['client_name']}:{c['sample_type']}" if c['sample_type'] else c['client_name']
        sla_config_map[key] = c['hours']

    form = SimpleProfileForm()
    return render_template(
        'analysis_config_simple.html',
        form=form,
        analysis_types=analysis_types,
        grouped_profiles=grouped_profiles,
        chpp_profiles=chpp_profiles,
        chpp_config_groups=CHPP_CONFIG_GROUPS,
        gi_shift_config=load_gi_shift_config(),
        sla_config_map=sla_config_map,
        sla_defaults=DEFAULT_SLA_HOURS,
        sla_fallback=DEFAULT_SLA_FALLBACK,
    )


@admin_bp.route('/analysis_config_simple_save', methods=['POST'])
@login_required
@senior_or_admin_required
def analysis_config_simple_save():
    """Шинэ энгийн тохиргоог хадгалах"""
    success, message = save_analysis_config(request.form)
    flash(message, 'success' if success else 'danger')
    return redirect(url_for('admin.analysis_config_simple'))


# --- Pattern дүрэм устгах ---
@admin_bp.route('/delete_pattern_profile/<int:profile_id>', methods=['POST'])
@login_required
@senior_or_admin_required
def delete_pattern_profile(profile_id):
    """Pattern профайл устгах."""
    success, msg = svc_delete_pattern_profile(profile_id)
    if msg == 'not_found':
        abort(404)
    if success:
        flash(msg, 'success')
    elif str(msg).startswith('Устгах алдаа'):
        flash(msg, 'danger')
    else:
        flash(msg, 'warning')
    return redirect(url_for('admin.analysis_config'))

# ==============================================================================
# А. Хуудас харуулах (Бүгдэд харагдана)


@admin_bp.route('/control_standards', methods=['GET'])
@login_required
def manage_standards():
    """Хяналтын стандартуудын жагсаалт."""
    standards = ControlStandardRepository.get_all_ordered()
    return render_template('admin/control_standards.html', standards=standards)

# 1. ШИНЭЭР ҮҮСГЭХ (Senior, Manager, Admin)


@admin_bp.route('/control_standards/create', methods=['POST'])
@login_required
@senior_or_admin_required
def create_standard():
    """Шинэ хяналтын стандарт үүсгэх."""
    data = request.get_json()
    success, message = svc_create_standard(data.get('name'), data.get('targets'))
    status = 200 if success else 400 if 'шаардлагатай' in message else 500
    return jsonify({"message": message}), (200 if success else status)

# 2. ЗАСАХ (UPDATE) (Senior, Manager, Admin)


@admin_bp.route('/control_standards/<int:id>/update', methods=['POST'])
@login_required
@senior_or_admin_required
def update_standard(id):
    """Хяналтын стандарт засах."""
    data = request.get_json()
    success, message = svc_update_standard(id, data.get('name'), data.get('targets'))
    if message == 'not_found':
        abort(404)
    return jsonify({"message": message}), (200 if success else 400 if 'Бүрэн бус' in message else 500)

# 3. УСТГАХ (DELETE) (Senior, Manager, Admin)


@admin_bp.route('/control_standards/<int:id>/delete', methods=['POST'])
@login_required
@senior_or_admin_required
def delete_standard(id):
    """Хяналтын стандарт устгах."""
    success, message = svc_delete_standard(id)
    if message == 'not_found':
        abort(404)
    return jsonify({"message": message}), (200 if success else 400)

# 4. ИДЭВХЖҮҮЛЭХ (ACTIVATE) (Senior, Manager, Admin)


@admin_bp.route('/control_standards/<int:id>/activate', methods=['POST'])
@login_required
@senior_or_admin_required
def activate_standard(id):
    """Хяналтын стандарт идэвхжүүлэх."""
    success, message = svc_activate_standard(id)
    if message == 'not_found':
        abort(404)
    return jsonify({"message": message}), (200 if success else 500)

# ==============================================================================
# Б. GBW Хуудас харуулах (Бүгдэд харагдана)


@admin_bp.route('/gbw_standards', methods=['GET'])
@login_required
def manage_gbw():
    """GBW стандартуудын жагсаалт."""
    # HTML дээр бид {% for gbw in gbw_list %} гэж бичсэн тул хувьсагчийн нэр 'gbw_list' байна
    gbw_list = GbwStandardRepository.get_all_ordered()
    return render_template('admin/gbw_list.html', gbw_list=gbw_list)

# 1. ШИНЭЭР ҮҮСГЭХ (GBW) (Senior, Manager, Admin)


@admin_bp.route('/gbw_standards/create', methods=['POST'])
@login_required
@senior_or_admin_required
def create_gbw():
    """Шинэ GBW стандарт үүсгэх."""
    data = request.get_json()
    success, message = svc_create_gbw(data.get('name'), data.get('targets'))
    status = 200 if success else 400 if 'шаардлагатай' in message else 500
    return jsonify({"message": message}), (200 if success else status)

# 2. ЗАСАХ (GBW UPDATE) (Senior, Manager, Admin)


@admin_bp.route('/gbw_standards/<int:id>/update', methods=['POST'])
@login_required
@senior_or_admin_required
def update_gbw(id):
    """GBW стандарт засах."""
    data = request.get_json()
    success, message = svc_update_gbw(id, data.get('name'), data.get('targets'))
    if message == 'not_found':
        abort(404)
    return jsonify({"message": message}), (200 if success else 400 if 'Бүрэн бус' in message else 500)

# 3. УСТГАХ (GBW DELETE) (Senior, Manager, Admin)


@admin_bp.route('/gbw_standards/<int:id>/delete', methods=['POST'])
@login_required
@senior_or_admin_required
def delete_gbw(id):
    """GBW стандарт устгах."""
    success, message = svc_delete_gbw(id)
    if message == 'not_found':
        abort(404)
    return jsonify({"message": message}), (200 if success else 400)

# 4. ИДЭВХЖҮҮЛЭХ (GBW ACTIVATE) (Senior, Manager, Admin)


@admin_bp.route('/gbw_standards/<int:id>/activate', methods=['POST'])
@login_required
@senior_or_admin_required
def activate_gbw(id):
    """GBW стандарт идэвхжүүлэх."""
    success, message = svc_activate_gbw(id)
    if message == 'not_found':
        abort(404)
    return jsonify({"message": message}), (200 if success else 500)


# 5. ИДЭВХГҮЙ БОЛГОХ (GBW DEACTIVATE) (Senior, Manager, Admin)
@admin_bp.route('/gbw_standards/<int:id>/deactivate', methods=['POST'])
@login_required
@senior_or_admin_required
def deactivate_gbw(id):
    """GBW стандарт идэвхгүй болгох."""
    success, message = svc_deactivate_gbw(id)
    if message == 'not_found':
        abort(404)
    return jsonify({"message": message}), (200 if success else 500)
