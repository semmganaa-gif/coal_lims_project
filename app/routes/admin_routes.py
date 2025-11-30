# app/routes/admin_routes.py
# -*- coding: utf-8 -*-

from flask import render_template, flash, redirect, url_for, request, abort, Blueprint, jsonify
from flask_login import login_required, current_user
from app import db
from app.models import User, AnalysisType, AnalysisProfile
import sqlalchemy as sa
from functools import wraps
import json

# Forms болон Constants импорт
from app.forms import UserManagementForm, SimpleProfileForm, PatternProfileForm
from app.constants import SAMPLE_TYPE_CHOICES_MAP
from app.models import db, ControlStandard

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

# --- Админ шаардлагатай үйлдлүүдийг хялбарчлах декоратор ---
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'admin':
            abort(403)
        return f(*args, **kwargs)
    return decorated_function


# --- Шинжилгээний төрлийг автоматаар үүсгэх/шинэчлэх функц ---
def _seed_analysis_types():
    required_analyses = [
        {'code': 'MT',    'name': 'Нийт чийг (MT)',               'order': 1,  'role': 'himich'},
        {'code': 'Mad',   'name': 'Дотоод чийг (Mad)',            'order': 2,  'role': 'himich'},
        {'code': 'Aad',   'name': 'Үнс (Aad)',                    'order': 3,  'role': 'himich'},
        {'code': 'Vad',   'name': 'Дэгдэмхий бодис (Vad)',        'order': 4,  'role': 'himich'},
        {'code': 'TS',    'name': 'Нийт хүхэр (TS)',              'order': 5,  'role': 'himich'},
        {'code': 'CV',    'name': 'Илчлэг (CV)',                  'order': 6,  'role': 'himich'},        
        {'code': 'CSN',   'name': 'Хөөлтийн зэрэг (CSN)',         'order': 7,  'role': 'himich'},
        {'code': 'Gi',    'name': 'Барьцалдах чадвар (Gi)',       'order': 8,  'role': 'himich'},
        {'code': 'TRD',   'name': 'Харьцангуй нягт (TRD)',        'order': 9, 'role': 'himich'},
        {'code': 'P',     'name': 'Фосфор (P)',                   'order': 10, 'role': 'himich'},
        {'code': 'F',     'name': 'Фтор (F)',                     'order': 11, 'role': 'himich'},
        {'code': 'Cl',    'name': 'Хлор (Cl)',                    'order': 12, 'role': 'himich'},
        {'code': 'X',     'name': 'Пластометр (X)',             'order': 13, 'role': 'himich'},
        {'code': 'Y',     'name': 'Пластометр (Y)',             'order': 14, 'role': 'himich'},
        {'code': 'CRI',   'name': 'Коксын урвалын идэвх (CRI)',   'order': 15, 'role': 'himich'},
        {'code': 'CSR',   'name': 'Урвалын дараах бат бэх (CSR)', 'order': 16, 'role': 'himich'},
        {'code': 'FM',    'name': 'Чөлөөт чийг (FM)',             'order': 17,  'role': 'beltgegch'},
        {'code': 'Solid', 'name': 'Хатуу бодисын үлдэгдэл (Solid)',            'order': 18, 'role': 'beltgegch'},
        {'code': 'm',     'name': 'Масс (m)',                     'order': 19, 'role': 'himich'},
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
    form = UserManagementForm()
    if form.validate_on_submit():
        existing_user = db.session.scalar(
            sa.select(User).where(User.username == form.username.data)
        )
        if existing_user:
            flash(f'"{form.username.data}" нэртэй хэрэглэгч аль хэдийн байна.', 'warning')
        else:
            user = User(username=form.username.data, role=form.role.data)
            try:
                user.set_password(form.password.data)
            except ValueError as e:
                flash(str(e), 'danger')
                users = User.query.order_by(User.id).all()
                return render_template('manage_users.html', title='Хэрэглэгчийн удирдлага', users=users, form=form)
            db.session.add(user)
            db.session.commit()
            flash(f'"{user.username}" нэртэй хэрэглэгч амжилттай нэмэгдлээ.', 'success')
        return redirect(url_for('admin.manage_users'))

    users = User.query.order_by(User.id).all()
    return render_template('manage_users.html', title='Хэрэглэгчийн удирдлага', users=users, form=form)


@admin_bp.route('/edit_user/<int:user_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_user(user_id):
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
        if form.password.data:
            try:
                user_to_edit.set_password(form.password.data)
            except ValueError as e:
                flash(str(e), 'danger')
                return render_template('edit_user.html',
                                       title='Хэрэглэгч засах',
                                       form=form,
                                       user=user_to_edit)

        db.session.commit()
        flash(f'"{user_to_edit.username}" хэрэглэгчийн мэдээлэл амжилттай шинэчлэгдлээ.', 'success')
        return redirect(url_for('admin.manage_users'))

    form.username.data = user_to_edit.username
    form.role.data = user_to_edit.role
    return render_template('edit_user.html', title='Хэрэглэгч засах', form=form, user=user_to_edit)


@admin_bp.route('/delete_user/<int:user_id>', methods=['POST'])
@login_required
@admin_required
def delete_user(user_id):
    if current_user.id == user_id:
        flash("Админ хэрэглэгч өөрийгөө устгах боломжгүй.", 'danger')
        return redirect(url_for('admin.manage_users'))

    user_to_delete = User.query.get_or_404(user_id)
    db.session.delete(user_to_delete)
    db.session.commit()
    flash(f"“{user_to_delete.username}” нэртэй хэрэглэгч амжилттай устгагдлаа.", 'success')
    return redirect(url_for('admin.manage_users'))


# ==============================================================================
# 2. ШИНЖИЛГЭЭНИЙ ТОХИРГОО (ANALYSIS CONFIG)
# ==============================================================================
@admin_bp.route('/analysis_config', methods=['GET', 'POST'])
@login_required
@admin_required
def analysis_config():
    # 1. DB Sync
    _seed_analysis_types()

    # 2. Auto-populate Simple Profiles
    added_new = False
    for client, types in SAMPLE_TYPE_CHOICES_MAP.items():
        for s_type in types:
            exists = AnalysisProfile.query.filter(
                (AnalysisProfile.pattern == None) | (AnalysisProfile.pattern == ''),
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
    
    if added_new:
        db.session.commit()
        return redirect(url_for('admin.analysis_config'))

    # 3. Data Fetch
    analysis_types = AnalysisType.query.order_by(AnalysisType.order_num).all()
    
    simple_profiles = AnalysisProfile.query.filter(
        (AnalysisProfile.pattern == None) | (AnalysisProfile.pattern == '')
    ).order_by(AnalysisProfile.client_name, AnalysisProfile.sample_type).all()
    
    pattern_profiles = AnalysisProfile.query.filter(
        AnalysisProfile.pattern != None, 
        AnalysisProfile.pattern != ''
    ).order_by(AnalysisProfile.priority.asc()).all()

    # 4. Forms
    simple_form = SimpleProfileForm()
    pattern_form = PatternProfileForm()
    
    pattern_form.analyses.choices = [(at.code, at.code) for at in analysis_types]

    # --- A. SIMPLE FORM SUBMIT ---
    if simple_form.submit_simple.data and simple_form.validate_on_submit():
        updated_count = 0
        for profile in simple_profiles:
            input_name = f"simple-{profile.id}-analyses"
            selected_codes = request.form.getlist(input_name)
            
            # List -> JSON
            profile.analyses_json = json.dumps(selected_codes)
            updated_count += 1
        
        db.session.commit()
        flash(f'{updated_count} энгийн тохиргоо (Matrix) шинэчлэгдлээ.', 'success')
        return redirect(url_for('admin.analysis_config'))

    # --- B. PATTERN FORM SUBMIT ---
    if pattern_form.submit_pattern.data and pattern_form.validate_on_submit():
        try:
            prio = int(request.form.get('priority', 50))
        except (ValueError, TypeError) as e:
            current_app.logger.warning(f"Invalid priority value: {request.form.get('priority')} - {e}")
            prio = 50
        
        rule_val = request.form.get('rule', 'merge')
        
        new_pattern = AnalysisProfile(
            pattern=pattern_form.pattern.data.strip(),
            analyses_json=json.dumps(pattern_form.analyses.data),
            priority=prio,
            # ✅ ЗАСВАР: Model дээр 'match_rule' гэж нэрлэсэн тул энд бас 'match_rule' ашиглана
            match_rule=rule_val, 
            client_name="Pattern Rule", 
            sample_type="Regex"
        )
        db.session.add(new_pattern)
        db.session.commit()
        flash('Шинэ нарийвчилсан дүрэм (Pattern) амжилттай нэмэгдлээ.', 'success')
        return redirect(url_for('admin.analysis_config'))

    return render_template(
        'analysis_config.html',
        simple_form=simple_form,
        pattern_form=pattern_form,
        analysis_types=analysis_types,
        simple_profiles=simple_profiles,
        pattern_profiles=pattern_profiles
    )


# --- Pattern дүрэм устгах ---
@admin_bp.route('/delete_pattern_profile/<int:profile_id>', methods=['POST'])
@login_required
@admin_required
def delete_pattern_profile(profile_id):
    profile = AnalysisProfile.query.get_or_404(profile_id)
    if profile.pattern:
        db.session.delete(profile)
        db.session.commit()
        flash('Дүрэм устгагдлаа.', 'success')
    else:
        flash('Энгийн тохиргоог устгах боломжгүй.', 'warning')
    return redirect(url_for('admin.analysis_config'))

# ==============================================================================
# А. Хуудас харуулах
@admin_bp.route('/control_standards', methods=['GET'])
@login_required
def manage_standards():
    standards = ControlStandard.query.order_by(ControlStandard.created_at.desc()).all()
    return render_template('admin/control_standards.html', standards=standards)

# 1. ШИНЭЭР ҮҮСГЭХ
@admin_bp.route('/control_standards/create', methods=['POST'])
@login_required
def create_standard():
    data = request.get_json()
    name = data.get('name')
    targets = data.get('targets')

    if not name or not targets:
        return jsonify({"message": "Нэр болон утгууд шаардлагатай"}), 400

    new_std = ControlStandard(name=name, targets=targets, is_active=False)
    db.session.add(new_std)
    db.session.commit()

    return jsonify({"message": "Амжилттай үүсгэлээ"})

# 2. ЗАСАХ (UPDATE)
@admin_bp.route('/control_standards/<int:id>/update', methods=['POST'])
@login_required
def update_standard(id):
    std = ControlStandard.query.get_or_404(id)
    data = request.get_json()
    
    # Validation
    if not data.get('name') or not data.get('targets'):
        return jsonify({"message": "Мэдээлэл дутуу байна"}), 400

    std.name = data.get('name')
    std.targets = data.get('targets')
    db.session.commit()

    return jsonify({"message": "Амжилттай шинэчиллээ"})

# 3. УСТГАХ (DELETE)
@admin_bp.route('/control_standards/<int:id>/delete', methods=['POST'])
@login_required
def delete_standard(id):
    std = ControlStandard.query.get_or_404(id)
    
    if std.is_active:
        return jsonify({"message": "Идэвхтэй стандартыг устгах боломжгүй!"}), 400

    db.session.delete(std)
    db.session.commit()
    
    return jsonify({"message": "Устгагдлаа"})

# 4. ИДЭВХЖҮҮЛЭХ (ACTIVATE)
@admin_bp.route('/control_standards/<int:id>/activate', methods=['POST'])
@login_required
def activate_standard(id):
    ControlStandard.query.update({ControlStandard.is_active: False})
    std = ControlStandard.query.get_or_404(id)
    std.is_active = True
    db.session.commit()
    return jsonify({"message": "Идэвхжлээ"})