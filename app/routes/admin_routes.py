# app/routes/admin_routes.py
# -*- coding: utf-8 -*-
"""
Админ удирдлагын модуль.

Энэ модуль нь хэрэглэгчийн удирдлага, шинжилгээний тохиргоо,
хяналтын стандартууд болон GBW стандартуудын удирдлагыг хариуцна.
"""

from flask import render_template, flash, redirect, url_for, request, abort, Blueprint, jsonify
from flask_login import login_required, current_user
from app import db
from app.models import User, AnalysisType, AnalysisProfile, SystemSetting
import sqlalchemy as sa
from functools import wraps
import json

# Forms болон Constants импорт
from app.forms import UserManagementForm, SimpleProfileForm
from app.constants import SAMPLE_TYPE_CHOICES_MAP, CHPP_CONFIG_GROUPS
from app.models import ControlStandard
from app.models import GbwStandard

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

# --- Админ шаардлагатай үйлдлүүдийг хялбарчлах декоратор ---


def admin_required(f):
    """Зөвхөн admin эрхтэй хэрэглэгчид (хэрэглэгч удирдлага)"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'admin':
            abort(403)
        return f(*args, **kwargs)
    return decorated_function


def senior_or_admin_required(f):
    """Senior, Admin эрхтэй хэрэглэгчид (тохиргоо, стандарт гэх мэт засвар хийх эрх)"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role not in ['senior', 'admin']:
            abort(403)
        return f(*args, **kwargs)
    return decorated_function


# --- Шинжилгээний төрлийг автоматаар үүсгэх/шинэчлэх функц ---
def _seed_analysis_types():
    """Шинжилгээний төрлүүдийг автоматаар үүсгэх/шинэчлэх."""
    required_analyses = [
        {'code': 'MT',    'name': 'Нийт чийг (MT)',               'order': 1,  'role': 'chemist'},
        {'code': 'Mad',   'name': 'Дотоод чийг (Mad)',            'order': 2,  'role': 'chemist'},
        {'code': 'Aad',   'name': 'Үнс (Aad)',                    'order': 3,  'role': 'chemist'},
        {'code': 'Vad',   'name': 'Дэгдэмхий бодис (Vad)',        'order': 4,  'role': 'chemist'},
        {'code': 'TS',    'name': 'Нийт хүхэр (TS)',              'order': 5,  'role': 'chemist'},
        {'code': 'CV',    'name': 'Илчлэг (CV)',                  'order': 6,  'role': 'chemist'},
        {'code': 'CSN',   'name': 'Хөөлтийн зэрэг (CSN)',         'order': 7,  'role': 'chemist'},
        {'code': 'Gi',    'name': 'Барьцалдах чадвар (Gi)',       'order': 8,  'role': 'chemist'},
        {'code': 'TRD',   'name': 'Харьцангуй нягт (TRD)',        'order': 9, 'role': 'chemist'},
        {'code': 'P',     'name': 'Фосфор (P)',                   'order': 10, 'role': 'chemist'},
        {'code': 'F',     'name': 'Фтор (F)',                     'order': 11, 'role': 'chemist'},
        {'code': 'Cl',    'name': 'Хлор (Cl)',                    'order': 12, 'role': 'chemist'},
        {'code': 'X',     'name': 'Пластометр (X)',             'order': 13, 'role': 'chemist'},
        {'code': 'Y',     'name': 'Пластометр (Y)',             'order': 14, 'role': 'chemist'},
        {'code': 'CRI',   'name': 'Коксын урвалын идэвх (CRI)',   'order': 15, 'role': 'chemist'},
        {'code': 'CSR',   'name': 'Урвалын дараах бат бэх (CSR)', 'order': 16, 'role': 'chemist'},
        {'code': 'FM',    'name': 'Чөлөөт чийг (FM)',             'order': 17,  'role': 'prep'},
        {'code': 'Solid', 'name': 'Хатуу бодисын үлдэгдэл (Solid)',            'order': 18, 'role': 'prep'},
        {'code': 'm',     'name': 'Масс (m)',                     'order': 19, 'role': 'chemist'},
        {'code': 'PE',    'name': 'Петрограф (PE)',                 'order': 20, 'role': 'chemist'},
    ]

    existing_analysis_types = {at.code: at for at in AnalysisType.query.all()}
    needs_commit = False

    for req in required_analyses:
        if req['code'] not in existing_analysis_types:
            new_at = AnalysisType(
                code=req['code'],
                name=req['name'],
                order_num=req['order'],
                required_role=req['role']
            )
            db.session.add(new_at)
            needs_commit = True
        else:
            existing = existing_analysis_types[req['code']]
            changed = (
                existing.name != req['name']
                or existing.order_num != req['order']
                or existing.required_role != req['role']
            )
            if changed:
                existing.name = req['name']
                existing.order_num = req['order']
                existing.required_role = req['role']
                db.session.add(existing)
                needs_commit = True

    if needs_commit:
        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            flash(f'Шинжилгээний төрлийг үүсгэх/шинэчлэхэд алдаа гарлаа: {e}', 'danger')


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
        existing_user = db.session.scalar(
            sa.select(User).where(User.username == form.username.data)
        )
        if existing_user:
            flash(f'"{form.username.data}" нэртэй хэрэглэгч аль хэдийн байна.', 'warning')
        else:
            user = User(username=form.username.data, role=form.role.data)
            # Лабораторийн эрх
            user.allowed_labs = form.allowed_labs.data or ['coal']
            # Профайл мэдээлэл нэмэх
            user.full_name = form.full_name.data or None
            user.email = form.email.data or None
            user.phone = form.phone.data or None
            user.position = form.position.data or None
            try:
                user.set_password(form.password.data)
            except ValueError as e:
                flash(str(e), 'danger')
                users = User.query.order_by(User.id).all()
                return render_template('manage_users.html', title='Хэрэглэгчийн удирдлага', users=users, form=form)
            db.session.add(user)
            try:
                db.session.commit()
                flash(f'"{user.username}" нэртэй хэрэглэгч амжилттай нэмэгдлээ.', 'success')
            except Exception as e:
                db.session.rollback()
                flash(f'Хэрэглэгч үүсгэхэд алдаа гарлаа: {str(e)[:100]}', 'danger')
        return redirect(url_for('admin.manage_users'))

    users = User.query.order_by(User.id).all()
    return render_template('manage_users.html', title='Хэрэглэгчийн удирдлага', users=users, form=form)


@admin_bp.route('/edit_user/<int:user_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_user(user_id):
    """Хэрэглэгчийн мэдээлэл засах."""
    user_to_edit = User.query.get_or_404(user_id)
    form = UserManagementForm(obj=user_to_edit)

    if form.validate_on_submit():
        original_username = user_to_edit.username
        new_username = form.username.data

        if original_username != new_username:
            existing_user = db.session.scalar(
                sa.select(User).where(User.username == new_username)
            )
            if existing_user:
                flash(f'"{new_username}" нэртэй хэрэглэгч аль хэдийн байна.', 'danger')
                return render_template('edit_user.html',
                                       title='Хэрэглэгч засах',
                                       form=form,
                                       user=user_to_edit)

        user_to_edit.username = new_username
        user_to_edit.role = form.role.data
        # Лабораторийн эрх
        user_to_edit.allowed_labs = form.allowed_labs.data or ['coal']
        # Профайл мэдээлэл шинэчлэх
        user_to_edit.full_name = form.full_name.data or None
        user_to_edit.email = form.email.data or None
        user_to_edit.phone = form.phone.data or None
        user_to_edit.position = form.position.data or None

        if form.password.data:
            try:
                user_to_edit.set_password(form.password.data)
            except ValueError as e:
                flash(str(e), 'danger')
                return render_template('edit_user.html',
                                       title='Хэрэглэгч засах',
                                       form=form,
                                       user=user_to_edit)

        try:
            db.session.commit()
            flash(f'"{user_to_edit.username}" хэрэглэгчийн мэдээлэл амжилттай шинэчлэгдлээ.', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'Хэрэглэгч шинэчлэхэд алдаа гарлаа: {str(e)[:100]}', 'danger')
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
    if current_user.id == user_id:
        flash("Админ хэрэглэгч өөрийгөө устгах боломжгүй.", 'danger')
        return redirect(url_for('admin.manage_users'))

    user_to_delete = User.query.get_or_404(user_id)
    username = user_to_delete.username
    db.session.delete(user_to_delete)
    try:
        db.session.commit()
        flash(f'"{username}" нэртэй хэрэглэгч амжилттай устгагдлаа.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Хэрэглэгч устгахад алдаа гарлаа: {str(e)[:100]}', 'danger')
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
    _seed_analysis_types()

    # 2. --- FORM SUBMIT (POST эхэнд шалгах) ---
    if request.method == 'POST':
        # Profiles авах
        simple_profiles = AnalysisProfile.query.filter(
            (AnalysisProfile.pattern.is_(None)) | (AnalysisProfile.pattern == ''),
            AnalysisProfile.client_name != 'CHPP'
        ).all()

        chpp_profiles = AnalysisProfile.query.filter(
            AnalysisProfile.client_name == 'CHPP',
            AnalysisProfile.pattern is not None,
            AnalysisProfile.pattern != ''
        ).all()

        updated_count = 0

        # Simple profiles хадгалах
        for profile in simple_profiles:
            input_name = f"simple-{profile.id}-analyses"
            selected_codes = request.form.getlist(input_name)
            profile.analyses_json = json.dumps(selected_codes)
            updated_count += 1

        # CHPP profiles хадгалах
        for profile in chpp_profiles:
            input_name = f"chpp-{profile.id}-analyses"
            selected_codes = request.form.getlist(input_name)
            profile.analyses_json = json.dumps(selected_codes)
            updated_count += 1

        # ✅ Gi ээлжийн тохиргоо хадгалах
        gi_config = {}
        for pf_code in ['PF211', 'PF221', 'PF231']:
            shifts = request.form.getlist(f'gi_shifts_{pf_code}')
            if shifts:
                gi_config[pf_code] = shifts

        if gi_config:
            setting = SystemSetting.query.filter_by(category='gi_shift', key='config').first()
            if not setting:
                setting = SystemSetting(category='gi_shift', key='config')
                db.session.add(setting)
            setting.value = json.dumps(gi_config)

        try:
            db.session.commit()
            flash(f'{updated_count} тохиргоо амжилттай хадгалагдлаа.', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'Тохиргоо хадгалахад алдаа гарлаа: {str(e)[:100]}', 'danger')
        return redirect(url_for('admin.analysis_config'))

    # 3. Auto-populate Simple Profiles (CHPP-ээс бусад)
    added_new = False
    for client, types in SAMPLE_TYPE_CHOICES_MAP.items():
        if client == 'CHPP':
            continue
        for s_type in types:
            exists = AnalysisProfile.query.filter(
                (AnalysisProfile.pattern.is_(None)) | (AnalysisProfile.pattern == ''),
                AnalysisProfile.client_name == client,
                AnalysisProfile.sample_type == s_type
            ).first()

            if not exists:
                new_profile = AnalysisProfile(
                    client_name=client,
                    sample_type=s_type,
                    pattern=None,
                    analyses_json="[]"
                )
                db.session.add(new_profile)
                added_new = True

    # 4. Auto-populate CHPP Pattern Profiles
    for hourly_type, config in CHPP_CONFIG_GROUPS.items():
        for sample in config['samples']:
            sample_name = sample['name']
            exists = AnalysisProfile.query.filter(
                AnalysisProfile.pattern == sample_name,
                AnalysisProfile.client_name == 'CHPP',
                AnalysisProfile.sample_type == hourly_type
            ).first()

            if not exists:
                new_profile = AnalysisProfile(
                    client_name='CHPP',
                    sample_type=hourly_type,
                    pattern=sample_name,
                    analyses_json="[]",
                    priority=10
                )
                db.session.add(new_profile)
                added_new = True

    if added_new:
        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            flash(f'Profile үүсгэхэд алдаа: {str(e)[:100]}', 'danger')
        return redirect(url_for('admin.analysis_config'))

    # 5. Data Fetch for GET
    analysis_types = AnalysisType.query.order_by(AnalysisType.order_num).all()

    simple_profiles = AnalysisProfile.query.filter(
        (AnalysisProfile.pattern.is_(None)) | (AnalysisProfile.pattern == ''),
        AnalysisProfile.client_name != 'CHPP'
    ).order_by(AnalysisProfile.client_name, AnalysisProfile.sample_type).all()

    chpp_profiles = AnalysisProfile.query.filter(
        AnalysisProfile.client_name == 'CHPP',
        AnalysisProfile.pattern is not None,
        AnalysisProfile.pattern != ''
    ).order_by(AnalysisProfile.sample_type, AnalysisProfile.pattern).all()

    simple_form = SimpleProfileForm()

    # ✅ Gi ээлжийн тохиргоо унших
    gi_shift_config = {}
    gi_setting = SystemSetting.query.filter_by(category='gi_shift', key='config').first()
    if gi_setting and gi_setting.value:
        try:
            gi_shift_config = json.loads(gi_setting.value)
        except (json.JSONDecodeError, TypeError):
            gi_shift_config = {}

    # Default утга (хэрэв DB-д байхгүй бол)
    if not gi_shift_config:
        gi_shift_config = {
            'PF211': ['D1', 'D3', 'D5', 'N1', 'N3', 'N5'],
            'PF221': ['D2', 'D4', 'D6', 'N2', 'N4', 'N6'],
            'PF231': ['D1', 'D3', 'D5', 'N1', 'N3', 'N5'],
        }

    return render_template(
        'analysis_config.html',
        simple_form=simple_form,
        analysis_types=analysis_types,
        simple_profiles=simple_profiles,
        chpp_profiles=chpp_profiles,
        chpp_config_groups=CHPP_CONFIG_GROUPS,
        gi_shift_config=gi_shift_config,
    )


# ==============================================================================
# 2.1 ШИНЭ ЭНГИЙН ТОХИРГОО (Card-based UI)
# ==============================================================================
@admin_bp.route('/analysis_config_simple', methods=['GET'])
@login_required
@senior_or_admin_required
def analysis_config_simple():
    """Шинэ энгийн Card-based шинжилгээний тохиргоо"""
    _seed_analysis_types()

    # Auto-populate profiles (same as original)
    added_new = False
    for client, types in SAMPLE_TYPE_CHOICES_MAP.items():
        if client == 'CHPP':
            continue
        for s_type in types:
            exists = AnalysisProfile.query.filter(
                (AnalysisProfile.pattern.is_(None)) | (AnalysisProfile.pattern == ''),
                AnalysisProfile.client_name == client,
                AnalysisProfile.sample_type == s_type
            ).first()
            if not exists:
                new_profile = AnalysisProfile(
                    client_name=client,
                    sample_type=s_type,
                    pattern=None,
                    analyses_json="[]"
                )
                db.session.add(new_profile)
                added_new = True

    # Auto-populate CHPP Pattern Profiles
    for hourly_type, config in CHPP_CONFIG_GROUPS.items():
        for sample in config['samples']:
            sample_name = sample['name']
            exists = AnalysisProfile.query.filter(
                AnalysisProfile.pattern == sample_name,
                AnalysisProfile.client_name == 'CHPP',
                AnalysisProfile.sample_type == hourly_type
            ).first()
            if not exists:
                new_profile = AnalysisProfile(
                    client_name='CHPP',
                    sample_type=hourly_type,
                    pattern=sample_name,
                    analyses_json="[]",
                    priority=10
                )
                db.session.add(new_profile)
                added_new = True

    if added_new:
        try:
            db.session.commit()
        except Exception:
            db.session.rollback()

    # Fetch data
    analysis_types = AnalysisType.query.order_by(AnalysisType.order_num).all()

    # Simple profiles grouped by client
    simple_profiles = AnalysisProfile.query.filter(
        (AnalysisProfile.pattern.is_(None)) | (AnalysisProfile.pattern == ''),
        AnalysisProfile.client_name != 'CHPP'
    ).order_by(AnalysisProfile.client_name, AnalysisProfile.sample_type).all()

    # Group by client name
    grouped_profiles = {}
    for profile in simple_profiles:
        if profile.client_name not in grouped_profiles:
            grouped_profiles[profile.client_name] = []
        grouped_profiles[profile.client_name].append(profile)

    # CHPP profiles
    chpp_profiles = AnalysisProfile.query.filter(
        AnalysisProfile.client_name == 'CHPP',
        AnalysisProfile.pattern.isnot(None),
        AnalysisProfile.pattern != ''
    ).order_by(AnalysisProfile.sample_type, AnalysisProfile.pattern).all()

    # Gi shift config
    gi_shift_config = {}
    gi_setting = SystemSetting.query.filter_by(category='gi_shift', key='config').first()
    if gi_setting and gi_setting.value:
        try:
            gi_shift_config = json.loads(gi_setting.value)
        except (json.JSONDecodeError, TypeError):
            pass

    if not gi_shift_config:
        gi_shift_config = {
            'PF211': ['D1', 'D3', 'D5', 'N1', 'N3', 'N5'],
            'PF221': ['D2', 'D4', 'D6', 'N2', 'N4', 'N6'],
            'PF231': ['D1', 'D3', 'D5', 'N1', 'N3', 'N5'],
        }

    form = SimpleProfileForm()
    return render_template(
        'analysis_config_simple.html',
        form=form,
        analysis_types=analysis_types,
        grouped_profiles=grouped_profiles,
        chpp_profiles=chpp_profiles,
        chpp_config_groups=CHPP_CONFIG_GROUPS,
        gi_shift_config=gi_shift_config,
    )


@admin_bp.route('/analysis_config_simple_save', methods=['POST'])
@login_required
@senior_or_admin_required
def analysis_config_simple_save():
    """Шинэ энгийн тохиргоог хадгалах"""
    # Simple profiles
    simple_profiles = AnalysisProfile.query.filter(
        (AnalysisProfile.pattern.is_(None)) | (AnalysisProfile.pattern == ''),
        AnalysisProfile.client_name != 'CHPP'
    ).all()

    # CHPP profiles
    chpp_profiles = AnalysisProfile.query.filter(
        AnalysisProfile.client_name == 'CHPP',
        AnalysisProfile.pattern.isnot(None),
        AnalysisProfile.pattern != ''
    ).all()

    updated_count = 0

    # Save simple profiles
    for profile in simple_profiles:
        input_name = f"simple-{profile.id}-analyses"
        selected_codes = request.form.getlist(input_name)
        profile.analyses_json = json.dumps(selected_codes)
        updated_count += 1

    # Save CHPP profiles
    for profile in chpp_profiles:
        input_name = f"chpp-{profile.id}-analyses"
        selected_codes = request.form.getlist(input_name)
        profile.analyses_json = json.dumps(selected_codes)
        updated_count += 1

    # Save Gi shift config
    gi_config = {}
    for pf_code in ['PF211', 'PF221', 'PF231']:
        shifts = request.form.getlist(f'gi_shifts_{pf_code}')
        if shifts:
            gi_config[pf_code] = shifts

    if gi_config:
        setting = SystemSetting.query.filter_by(category='gi_shift', key='config').first()
        if not setting:
            setting = SystemSetting(category='gi_shift', key='config')
            db.session.add(setting)
        setting.value = json.dumps(gi_config)

    try:
        db.session.commit()
        flash(f'{updated_count} тохиргоо амжилттай хадгалагдлаа.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Алдаа гарлаа: {str(e)[:100]}', 'danger')

    return redirect(url_for('admin.analysis_config_simple'))


# --- Pattern дүрэм устгах ---
@admin_bp.route('/delete_pattern_profile/<int:profile_id>', methods=['POST'])
@login_required
@senior_or_admin_required
def delete_pattern_profile(profile_id):
    """Pattern профайл устгах."""
    profile = AnalysisProfile.query.get_or_404(profile_id)
    if profile.pattern:
        db.session.delete(profile)
        try:
            db.session.commit()
            flash('Дүрэм устгагдлаа.', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'Устгахад алдаа: {str(e)[:100]}', 'danger')
    else:
        flash('Энгийн тохиргоог устгах боломжгүй.', 'warning')
    return redirect(url_for('admin.analysis_config'))

# ==============================================================================
# А. Хуудас харуулах (Бүгдэд харагдана)


@admin_bp.route('/control_standards', methods=['GET'])
@login_required
def manage_standards():
    """Хяналтын стандартуудын жагсаалт."""
    standards = ControlStandard.query.order_by(ControlStandard.created_at.desc()).all()
    return render_template('admin/control_standards.html', standards=standards)

# 1. ШИНЭЭР ҮҮСГЭХ (Senior, Manager, Admin)


@admin_bp.route('/control_standards/create', methods=['POST'])
@login_required
@senior_or_admin_required
def create_standard():
    """Шинэ хяналтын стандарт үүсгэх."""
    data = request.get_json()
    name = data.get('name')
    targets = data.get('targets')

    if not name or not targets:
        return jsonify({"message": "Нэр болон утгууд шаардлагатай"}), 400

    new_std = ControlStandard(name=name, targets=targets, is_active=False)
    db.session.add(new_std)
    try:
        db.session.commit()
        return jsonify({"message": "Амжилттай үүсгэлээ"})
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": f"Алдаа: {str(e)[:100]}"}), 500

# 2. ЗАСАХ (UPDATE) (Senior, Manager, Admin)


@admin_bp.route('/control_standards/<int:id>/update', methods=['POST'])
@login_required
@senior_or_admin_required
def update_standard(id):
    """Хяналтын стандарт засах."""
    std = ControlStandard.query.get_or_404(id)
    data = request.get_json()

    # Validation
    if not data.get('name') or not data.get('targets'):
        return jsonify({"message": "Мэдээлэл дутуу байна"}), 400

    std.name = data.get('name')
    std.targets = data.get('targets')
    try:
        db.session.commit()
        return jsonify({"message": "Амжилттай шинэчиллээ"})
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": f"Алдаа: {str(e)[:100]}"}), 500

# 3. УСТГАХ (DELETE) (Senior, Manager, Admin)


@admin_bp.route('/control_standards/<int:id>/delete', methods=['POST'])
@login_required
@senior_or_admin_required
def delete_standard(id):
    """Хяналтын стандарт устгах."""
    std = ControlStandard.query.get_or_404(id)

    if std.is_active:
        return jsonify({"message": "Идэвхтэй стандартыг устгах боломжгүй!"}), 400

    db.session.delete(std)
    try:
        db.session.commit()
        return jsonify({"message": "Устгагдлаа"})
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": f"Алдаа: {str(e)[:100]}"}), 500

# 4. ИДЭВХЖҮҮЛЭХ (ACTIVATE) (Senior, Manager, Admin)


@admin_bp.route('/control_standards/<int:id>/activate', methods=['POST'])
@login_required
@senior_or_admin_required
def activate_standard(id):
    """Хяналтын стандарт идэвхжүүлэх."""
    ControlStandard.query.update({ControlStandard.is_active: False})
    std = ControlStandard.query.get_or_404(id)
    std.is_active = True
    try:
        db.session.commit()
        return jsonify({"message": "Идэвхжлээ"})
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": f"Алдаа: {str(e)[:100]}"}), 500

# ==============================================================================
# Б. GBW Хуудас харуулах (Бүгдэд харагдана)


@admin_bp.route('/gbw_standards', methods=['GET'])
@login_required
def manage_gbw():
    """GBW стандартуудын жагсаалт."""
    # HTML дээр бид {% for gbw in gbw_list %} гэж бичсэн тул хувьсагчийн нэр 'gbw_list' байна
    gbw_list = GbwStandard.query.order_by(GbwStandard.created_at.desc()).all()
    return render_template('admin/gbw_list.html', gbw_list=gbw_list)

# 1. ШИНЭЭР ҮҮСГЭХ (GBW) (Senior, Manager, Admin)


@admin_bp.route('/gbw_standards/create', methods=['POST'])
@login_required
@senior_or_admin_required
def create_gbw():
    """Шинэ GBW стандарт үүсгэх."""
    data = request.get_json()
    name = data.get('name')
    targets = data.get('targets')

    if not name or not targets:
        return jsonify({"message": "GBW дугаар болон утгууд шаардлагатай"}), 400

    # Шинэ GBW үүсгэх
    new_gbw = GbwStandard(name=name, targets=targets, is_active=False)
    db.session.add(new_gbw)
    try:
        db.session.commit()
        return jsonify({"message": "GBW амжилттай бүртгэгдлээ"})
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": f"Алдаа: {str(e)[:100]}"}), 500

# 2. ЗАСАХ (GBW UPDATE) (Senior, Manager, Admin)


@admin_bp.route('/gbw_standards/<int:id>/update', methods=['POST'])
@login_required
@senior_or_admin_required
def update_gbw(id):
    """GBW стандарт засах."""
    gbw = GbwStandard.query.get_or_404(id)
    data = request.get_json()

    if not data.get('name') or not data.get('targets'):
        return jsonify({"message": "Мэдээлэл дутуу байна"}), 400

    gbw.name = data.get('name')
    gbw.targets = data.get('targets')
    try:
        db.session.commit()
        return jsonify({"message": "GBW мэдээлэл шинэчлэгдлээ"})
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": f"Алдаа: {str(e)[:100]}"}), 500

# 3. УСТГАХ (GBW DELETE) (Senior, Manager, Admin)


@admin_bp.route('/gbw_standards/<int:id>/delete', methods=['POST'])
@login_required
@senior_or_admin_required
def delete_gbw(id):
    """GBW стандарт устгах."""
    gbw = GbwStandard.query.get_or_404(id)

    if gbw.is_active:
        return jsonify({"message": "Ашиглагдаж буй GBW-ийг устгах боломжгүй!"}), 400

    db.session.delete(gbw)
    try:
        db.session.commit()
        return jsonify({"message": "GBW устгагдлаа"})
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": f"Алдаа: {str(e)[:100]}"}), 500

# 4. ИДЭВХЖҮҮЛЭХ (GBW ACTIVATE) (Senior, Manager, Admin)


@admin_bp.route('/gbw_standards/<int:id>/activate', methods=['POST'])
@login_required
@senior_or_admin_required
def activate_gbw(id):
    """GBW стандарт идэвхжүүлэх."""
    # 1. Бүх GBW-ийг идэвхгүй болгоно (Зөвхөн нэг GBW идэвхтэй байх зарчмаар)
    GbwStandard.query.update({GbwStandard.is_active: False})

    # 2. Сонгосон GBW-ийг идэвхжүүлнэ
    gbw = GbwStandard.query.get_or_404(id)
    gbw.is_active = True

    try:
        db.session.commit()
        return jsonify({"message": "GBW идэвхжлээ"})
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": f"Алдаа: {str(e)[:100]}"}), 500


# 5. ИДЭВХГҮЙ БОЛГОХ (GBW DEACTIVATE) (Senior, Manager, Admin)
@admin_bp.route('/gbw_standards/<int:id>/deactivate', methods=['POST'])
@login_required
@senior_or_admin_required
def deactivate_gbw(id):
    """GBW стандарт идэвхгүй болгох."""
    gbw = GbwStandard.query.get_or_404(id)
    gbw.is_active = False
    try:
        db.session.commit()
        return jsonify({"message": "Амжилттай идэвхгүй болголоо"})
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": f"Алдаа: {str(e)[:100]}"}), 500
