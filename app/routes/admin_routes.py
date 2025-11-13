# Энэ файл нь зөвхөн админ эрхтэй хэрэглэгчийн хандах хуудсуудыг агуулна.
# Жишээ: Хэрэглэгчийн удирдлага, Шинжилгээний тохиргоо.

from flask import render_template, flash, redirect, url_for, request, abort, Blueprint
from flask_login import login_required, current_user
from app import db
from app.models import User, AnalysisType, AnalysisProfile
from app.forms import UserManagementForm, SimpleProfileForm, PatternProfileForm
import sqlalchemy as sa
from functools import wraps

# --- Админы хуудсуудын зориулсан Blueprint ---
# /admin/... замаар дуудагдана.
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
# analysis_config route дуудаж ажиллуулна.
def _seed_analysis_types():
    required_analyses = [
        {'code': 'MT',    'name': 'Нийт чийг (MT)',                          'order': 1,  'role': 'himich'},
        {'code': 'Mad',   'name': 'Дотоод чийг (Mad)',                        'order': 2,  'role': 'himich'},
        {'code': 'Aad',   'name': 'Үнс (Aad)',                                'order': 3,  'role': 'himich'},
        {'code': 'Vad',   'name': 'Дэгдэмхий бодис (Vad)',                    'order': 4,  'role': 'himich'},
        {'code': 'TS',    'name': 'Нийт хүхэр (TS)',                          'order': 5,  'role': 'himich'},
        {'code': 'CV',    'name': 'Илчлэг (CV)',                              'order': 6,  'role': 'himich'},
        {'code': 'FM',    'name': 'Чөлөөт чийг (FM)',                         'order': 7,  'role': 'beltgegch'},
        {'code': 'CSN',   'name': 'Хөөтийн дугаар (CSN)',                     'order': 8,  'role': 'himich'},
        {'code': 'Gi',    'name': 'Кейкингийн индекс (Gi)',                   'order': 9,  'role': 'himich'},
        {'code': 'TRD',   'name': 'Харьцангуй нягт (TRD)',                    'order': 10, 'role': 'himich'},
        {'code': 'P',     'name': 'Фосфор (P)',                               'order': 11, 'role': 'himich'},
        {'code': 'F',     'name': 'Фтор (F)',                                 'order': 12, 'role': 'himich'},
        {'code': 'Cl',    'name': 'Хлор (Cl)',                                'order': 13, 'role': 'himich'},
        {'code': 'X',     'name': 'Пластометр X (X)',                          'order': 14, 'role': 'himich'},
        {'code': 'Y',     'name': 'Пластометр Y (Y)',                          'order': 15, 'role': 'himich'},
        {'code': 'CRI',   'name': 'Коксын урвалын идэвх (CRI)',               'order': 16, 'role': 'himich'},
        {'code': 'CSR',   'name': 'Урвалын дараах бат бэх (CSR)',             'order': 17, 'role': 'himich'},
        {'code': 'Solid', 'name': 'Хат бодис (Solid)',                        'order': 18, 'role': 'beltgegch'},
        {'code': 'm',     'name': 'Масс (m)',                                 'order': 19, 'role': 'himich'},
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


# --- ХЭРЭГЛЭГЧИЙН УДИРДЛАГА (АДМИН) ---
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
            flash(f"“{form.username.data}” нэртэй хэрэглэгч аль хэдийн байна.", 'warning')
        else:
            user = User(username=form.username.data, role=form.role.data)
            user.set_password(form.password.data)
            db.session.add(user)
            db.session.commit()
            flash(f"“{user.username}” нэртэй хэрэглэгч амжилттай нэмэгдлээ.", 'success')
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
                flash(f"“{new_username}” нэртэй хэрэглэгч аль хэдийн байна.", 'danger')
                return render_template('edit_user.html',
                                       title='Хэрэглэгч засах',
                                       form=form,
                                       user=user_to_edit)

        user_to_edit.username = new_username
        user_to_edit.role = form.role.data
        if form.password.data:
            user_to_edit.set_password(form.password.data)

        db.session.commit()
        flash(f"“{user_to_edit.username}” хэрэглэгчийн мэдээлэл амжилттай шинэчлэгдлээ.", 'success')
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


# --- ШИНЖИЛГЭЭНИЙ ТОХИРГОО (АДМИН) ---
@admin_bp.route('/analysis-config', methods=['GET', 'POST'])
@login_required
@admin_required
def analysis_config():
    # DB-д шаардлагатай анализын төрлүүдийг баталгаажуулна
    _seed_analysis_types()

    simple_form = SimpleProfileForm()
    pattern_form = PatternProfileForm()
    analysis_types = AnalysisType.query.order_by(AnalysisType.order_num).all()

    # SelectMultipleField-ийн сонголтуудыг populate хийх
    pattern_form.analyses.choices = [(at.code, at.name) for at in analysis_types]
    analysis_map = {at.code: at.name for at in analysis_types}

    if request.method == 'POST':
        # Энгийн тохиргоог хадгалах
        if 'submit_simple' in request.form:
            simple_profiles_to_save = AnalysisProfile.query.filter_by(profile_type='simple').all()
            for profile in simple_profiles_to_save:
                checked_codes = request.form.getlist(f'simple-{profile.id}-analyses')
                profile.set_analyses(checked_codes)
                db.session.add(profile)
            db.session.commit()
            flash('Энгийн тохиргоо амжилттай хадгалагдлаа.', 'success')
            return redirect(url_for('admin.analysis_config'))

        # Бүтцийн (pattern) тохиргоог хадгалах
        if 'submit_pattern' in request.form and pattern_form.validate():
            pattern_str = pattern_form.pattern.data
            analyses_list = pattern_form.analyses.data

            existing = AnalysisProfile.query.filter_by(
                profile_type='pattern', pattern=pattern_str
            ).first()
            if existing:
                flash(f"“{pattern_str}” нэртэй бүтэц аль хэдийн байна. Эхлээд хуучнаа устгана уу.", 'danger')
            else:
                new_profile = AnalysisProfile(profile_type='pattern', pattern=pattern_str)
                new_profile.set_analyses(analyses_list)
                db.session.add(new_profile)
                db.session.commit()
                flash('Шинэ бүтцийн тохиргоо амжилттай нэмэгдлээ.', 'success')

            return redirect(url_for('admin.analysis_config'))

    # GET хүсэлт: энгийн профайлуудын жагсаалт бэлдэх
    sample_type_choices_map = {
        'UHG-Geo': ['S', 'TR', 'GRD', 'TE', 'PE', 'CQ'],
        'BN-Geo':  ['S', 'TR', 'GRD', 'TE', 'PE', 'CQ'],
        'QC':      ['HCC', 'SSCC', 'MASHCC', 'TC', 'Fine', 'Test'],
        'Proc': ['CHP', 'HCC', 'SSCC', 'MASHCC', 'Test'],
        'LAB':     ['CM', 'GBW', 'Test'],
        'WTL':     ['WTL', 'Size', 'FL'],
    }
    simple_clients = list(sample_type_choices_map.keys())

    simple_profiles = []
    new_profiles_added_to_db = False

    for client_name in simple_clients:
        for sample_type in sample_type_choices_map.get(client_name, []):
            profile = AnalysisProfile.query.filter_by(
                profile_type='simple',
                client_name=client_name,
                sample_type=sample_type
            ).first()
            if not profile:
                profile = AnalysisProfile(
                    profile_type='simple',
                    client_name=client_name,
                    sample_type=sample_type,
                    analyses='[]'
                )
                db.session.add(profile)
                new_profiles_added_to_db = True
            simple_profiles.append(profile)

    if new_profiles_added_to_db:
        db.session.commit()

    pattern_profiles = AnalysisProfile.query.filter_by(
        profile_type='pattern'
    ).order_by(AnalysisProfile.pattern).all()

    return render_template(
        'analysis_config.html',
        title='Шинжилгээний тохиргоо',
        simple_form=simple_form,
        pattern_form=pattern_form,
        analysis_types=analysis_types,
        analysis_map=analysis_map,
        simple_profiles=simple_profiles,
        pattern_profiles=pattern_profiles
    )


@admin_bp.route('/delete-pattern-profile/<int:profile_id>', methods=['POST'])
@login_required
@admin_required
def delete_pattern_profile(profile_id):
    profile_to_delete = AnalysisProfile.query.get_or_404(profile_id)
    if profile_to_delete.profile_type == 'pattern':
        pattern_name = profile_to_delete.pattern
        db.session.delete(profile_to_delete)
        db.session.commit()
        flash(f"“{pattern_name}” бүтцийн тохиргоо амжилттай устгагдлаа.", 'success')
    else:
        flash('Буруу үйлдэл: Зөвхөн бүтцийн тохиргоог устгах боломжтой.', 'danger')
    return redirect(url_for('admin.analysis_config'))
