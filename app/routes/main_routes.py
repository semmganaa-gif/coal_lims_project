# Энэ файл нь хэрэглэгчийн үндсэн үйлдлүүдтэй холбоотой хуудсуудыг агуулна.
# Жишээ нь: Нүүр хуудас, нэвтрэх, гарах, дээж засах гэх мэт.

from flask import render_template, flash, redirect, url_for, request, Blueprint
from flask_login import login_user, logout_user, current_user, login_required
from app import db
from app.forms import LoginForm, AddSampleForm
import sqlalchemy as sa
from urllib.parse import urlparse, urljoin
from datetime import datetime
from sqlalchemy.exc import IntegrityError
import json

# --- Үндсэн үйлдлүүдэд зориулагдсан шинэ Blueprint үүсгэх ---
main_bp = Blueprint('main', __name__)

# ===================== ТУСЛАХ ФУНКЦУУД =====================

def get_12h_shift_code(dt):
    """12 цагийн ээлжийн код (_D / _N)"""
    hour = dt.hour
    return '_D' if 7 <= hour < 19 else '_N'


def get_quarter_code(dt):
    """Улирлын код (_Q1.._Q4)"""
    month = dt.month
    if month <= 3:
        return '_Q1'
    elif month <= 6:
        return '_Q2'
    elif month <= 9:
        return '_Q3'
    else:
        return '_Q4'


def is_safe_url(target):
    """Аюулгүй redirect шалгах"""
    host_url = urlparse(request.host_url)
    test_url = urlparse(urljoin(request.host_url, target))
    return (test_url.scheme in ('http', 'https') or test_url.scheme == '') and \
           test_url.netloc == host_url.netloc


# ===================== НҮҮР / ДЭЭЖ БҮРТГЭХ =====================

@main_bp.route('/', methods=['GET', 'POST'])
@main_bp.route('/index', methods=['GET', 'POST'])
@login_required
def index():
    """
    - Зүүн тал: жагсаалт (DataTables – template талд)
    - Баруун тал: 'Шинэ дээж бүртгэх' form
    - Олон үүсгэгч (CHPP, UHG/BN/QC/Proc, WTL, LAB) логик энд байна.
    """
    # тойрог импорт сэргээлт
    from app.models import Sample, AnalysisProfile

    form = AddSampleForm()

    # ✅ Клиентуудын төрөл мап (Proc багтсан!)
    sample_type_choices_map = {
        'CHPP':    ['2 hourly', '4 hourly', '12 hourly'],
        'UHG-Geo': ['S', 'TR', 'GRD', 'TE', 'PE', 'CQ'],
        'BN-Geo':  ['S', 'TR', 'GRD', 'TE', 'PE', 'CQ'],
        'QC':      ['HCC', 'SSCC', 'MASHCC', 'TC', 'Fine', 'Test'],
        'Proc':    ['CHP', 'HCC', 'SSCC', 'MASHCC', 'Test'],
        'WTL':     ['WTL', 'Size', 'FL', 'MG', 'Test'],
        'LAB':     ['CM', 'GBW', 'Test'],
    }

    # 🛑 form client_name choices-ийг энд тогтооно (GET ба POST аль алинд)
    form.client_name.choices = [
        ('CHPP', 'CHPP'),
        ('UHG-Geo', 'UHG-Geo'),
        ('BN-Geo', 'BN-Geo'),
        ('QC', 'QC'),
        ('Proc', 'Proc'),
        ('WTL', 'WTL'),
        ('LAB', 'LAB'),
    ]

    # ---------- Dynamic sample_type + validators ----------
    # POST үед хэрэглэгчийн сонголтоор sample_type.choices/validators-ийг тохируулна
    if request.method == 'POST':
        selected_client = request.form.get('client_name')
        # sample_type choices
        form.sample_type.choices = [(v, v) for v in sample_type_choices_map.get(selected_client, [])]

        # WTL: MG/Test үед sample_code заавал
        if selected_client == 'WTL' and request.form.get('sample_type') in ['MG', 'Test']:
            from wtforms.validators import DataRequired
            form.sample_code.validators = [DataRequired(message="Sample name заавал оруулна уу.")]
        else:
            from wtforms.validators import Optional
            form.sample_code.validators = [Optional()]
    else:
        # GET: эхний байдлаар sample_type хоосон (хэрэглэгч client-ээ сонгосны дараа JS-аар үүсгэнэ)
        form.sample_type.choices = []

    # ---------- Үндсэн submit ----------
    if form.validate_on_submit():
        if current_user.role not in ['beltgegch', 'admin']:
            flash('Дээж бүртгэх эрх танд байхгүй.', 'danger')
            return redirect(url_for('main.index'))

        submitted_codes = request.form.getlist('sample_codes')
        list_type = request.form.get('list_type')  # chpp_2h / chpp_4h / chpp_12h / multi_gen / None
        client_name = form.client_name.data
        sample_type = form.sample_type.data
        sample_date_obj = form.sample_date.data

        successful_samples, failed_samples = [], []
        count = 0

        # --- 1) ОЛОН ДЭЭЖ БҮРТГЭХ (CHPP, UHG/BN/QC/Proc/LAB(simple)) ---
        if submitted_codes and list_type:
            analysis_codes_json = '[]'
            pattern_profiles = []

            if client_name in ['UHG-Geo', 'BN-Geo', 'QC', 'Proc', 'LAB']:
                profile = AnalysisProfile.query.filter_by(
                    profile_type='simple', client_name=client_name, sample_type=sample_type
                ).first()
                if profile:
                    analysis_codes_json = profile.analyses
            elif client_name == 'CHPP':
                pattern_profiles = AnalysisProfile.query.filter_by(profile_type='pattern').all()

            requires_weight = (list_type == 'chpp_2h' or list_type == 'multi_gen')
            submitted_weights = request.form.getlist('weights') if requires_weight else [None] * len(submitted_codes)

            for code, weight_str in zip(submitted_codes, submitted_weights):
                if not code:
                    continue

                # Жин шалгах (хэрэгтэй үед)
                weight, is_valid = None, True
                if requires_weight:
                    if weight_str:
                        try:
                            weight = float(weight_str)
                        except ValueError:
                            failed_samples.append(f'{code} (жин: "{weight_str}" буруу)')
                            is_valid = False
                    else:
                        failed_samples.append(f'{code} (жин оруулаагүй)')
                        is_valid = False
                if not is_valid:
                    continue

                # Шинжилгээ оноох
                assigned_analyses = analysis_codes_json
                if client_name == 'CHPP':
                    assigned_analyses = '[]'
                    for p in pattern_profiles:
                        if p.pattern in code:
                            assigned_analyses = p.analyses
                            break

                sample = Sample(
                    sample_code=code,
                    weight=weight,
                    user_id=current_user.id,
                    client_name=client_name,
                    sample_type=sample_type,
                    sample_condition=form.sample_condition.data,
                    sample_date=sample_date_obj,
                    return_sample=form.return_sample.data,
                    delivered_by=form.delivered_by.data,
                    prepared_date=form.prepared_date.data,
                    prepared_by=form.prepared_by.data,
                    notes=form.notes.data,
                    location=form.location.data if list_type == 'multi_gen' else None,
                    product=form.product.data if list_type == 'multi_gen' and client_name == 'QC' else None,
                    hourly_system=list_type.replace('chpp_', '') if 'chpp' in list_type else None,
                    analyses_to_perform=assigned_analyses,
                )
                db.session.add(sample)
                successful_samples.append(code)
                count += 1

            if count > 0:
                try:
                    db.session.commit()
                    flash(f'{count} ш дээж амжилттай бүртгэгдлээ!', 'success')
                except IntegrityError:
                    db.session.rollback()
                    flash('БҮРТГЭЛ АМЖИЛТГҮЙ: Дээжний код давхардсан байна.', 'danger')
                    return render_template('index.html', title='Нүүр хуудас', form=form, active_tab='add-pane')

            if failed_samples:
                flash(f'Анхаар: Дараах дээжнүүд бүртгэгдсэнгүй: {", ".join(failed_samples)}', 'warning')

            return redirect(url_for('main.index', active_tab='add-pane'))

        # --- 2) WTL (WTL/Size/FL) – автоматаар олон нэр үүсгэх ---
        elif not list_type and client_name == 'WTL' and sample_type in ['WTL', 'Size', 'FL']:
            lab_number = form.lab_number.data
            if not lab_number:
                flash('WTL-ийн хувьд Лаб дугаар заавал оруулна уу.', 'danger')
            else:
                wtl_profiles = AnalysisProfile.query.filter_by(profile_type='pattern').all()
                all_wtl_names = []
                if sample_type == 'WTL':
                    wtl_sample_names_19 = [
                        'Dry_/+31.5', 'Dry_/+16.0', 'Dry_/+8.0', 'Dry_/+4.75', 'Dry_/+2.0', 'Dry_/+1.0', 'Dry_/-1.0',
                        'Wet_/+31.5', 'Wet_/+16.0', 'Wet_/+8.0', 'Wet_/+4.75', 'Wet_/+2.0', 'Wet_/+1.0',
                        'Wet_/+0.5','Wet_/+0.25', 'Wet_/+0.15', 'Wet_/+0.074', 'Wet_/+0.038', 'Wet_/-0.038',
                    ]
                    wtl_sample_names_70 = [
                        '/+16.0/_F1.300','/+16.0/_F1.325','/+16.0/_F1.350','/+16.0/_F1.375','/+16.0/_F1.400',
                        '/+16.0/_F1.425','/+16.0/_F1.450','/+16.0/_F1.50','/+16.0/_F1.60','/+16.0/_F1.70',
                        '/+16.0/_F1.80','/+16.0/_F2.0','/+16.0/_F2.2','/+16.0/_S2.2',
                        '/+8.0/_F1.300','/+8.0/_F1.325','/+8.0/_F1.350','/+8.0/_F1.375','/+8.0/_F1.400',
                        '/+8.0/_F1.425','/+8.0/_F1.450','/+8.0/_F1.50','/+8.0/_F1.60','/+8.0/_F1.70',
                        '/+8.0/_F1.80','/+8.0/_F2.0','/+8.0/_F2.2','/+8.0/_S2.2',
                        '/+2.0/_F1.300','/+2.0/_F1.325','/+2.0/_F1.350','/+2.0/_F1.375','/+2.0/_F1.400',
                        '/+2.0/_F1.425','/+2.0/_F1.450','/+2.0/_F1.50','/+2.0/_F1.60','/+2.0/_F1.70',
                        '/+2.0/_F1.80','/+2.0/_F2.0','/+2.0/_F2.2','/+2.0/_S2.2',
                        '/+0.5/_F1.300','/+0.5/_F1.325','/+0.5/_F1.350','/+0.5/_F1.375','/+0.5/_F1.400',
                        '/+0.5/_F1.425','/+0.5/_F1.450','/+0.5/_F1.50','/+0.5/_F1.60','/+0.5/_F1.70',
                        '/+0.5/_F1.80','/+0.5/_F2.0','/+0.5/_F2.2','/+0.5/_S2.2',
                        '/+0.25/_F1.300','/+0.25/_F1.325','/+0.25/_F1.350','/+0.25/_F1.375','/+0.25/_F1.400',
                        '/+0.25/_F1.425','/+0.25/_F1.450','/+0.25/_F1.50','/+0.25/_F1.60','/+0.25/_F1.70',
                        '/+0.25/_F1.80','/+0.25/_F2.0','/+0.25/_F2.2','/+0.25/_S2.2'
                    ]
                    wtl_sample_names_6 = ['C1', 'C2', 'C3', 'C4', 'T1', 'T2']
                    wtl_sample_names_2 = ['Initial', 'Comp']
                    all_wtl_names = wtl_sample_names_19 + wtl_sample_names_70 + wtl_sample_names_6 + wtl_sample_names_2
                elif sample_type == 'Size':
                    all_wtl_names = [
                        '/+31.5', '/+16.0', '/+8.0', '/+4.75', '/+2.0', '/+1.0',
                        '/+0.5','/+0.25', '/+0.15', '/+0.074', '/+0.038', '/-0.038', 'Initial'
                    ]
                elif sample_type == 'FL':
                    all_wtl_names = ['C1', 'C2', 'C3', 'C4', 'T1', 'T2', 'Initial']

                count = 0
                for name in all_wtl_names:
                    final_sample_code = f"{lab_number}_{name}"
                    assigned_analyses_json = '[]'
                    for profile in wtl_profiles:
                        if profile.pattern in final_sample_code:
                            assigned_analyses_json = profile.analyses
                            break

                    sample = Sample(
                        sample_code=final_sample_code,
                        user_id=current_user.id,
                        client_name=client_name,
                        sample_type=sample_type,
                        sample_condition=form.sample_condition.data,
                        sample_date=sample_date_obj,
                        return_sample=form.return_sample.data,
                        delivered_by=form.delivered_by.data,
                        prepared_date=form.prepared_date.data,
                        prepared_by=form.prepared_by.data,
                        notes=form.notes.data,
                        weight=None,
                        analyses_to_perform=assigned_analyses_json,
                    )
                    db.session.add(sample)
                    count += 1

                if count > 0:
                    try:
                        db.session.commit()
                        flash(f'{count} ш {sample_type} дээж амжилттай бүртгэгдлээ!', 'success')
                    except IntegrityError:
                        db.session.rollback()
                        flash('БҮРТГЭЛ АМЖИЛТГҮЙ: Дээжний код давхардсан байна (магадгүй энэ Лаб дугаартай дээж аль хэдийн бүртгэлтэй).', 'danger')
                        return render_template('index.html', title='Нүүр хуудас', form=form, active_tab='add-pane')

                return redirect(url_for('main.index', active_tab='add-pane'))

        # --- 3) LAB — автоматаар нэр үүсгэх ---
        elif not list_type and client_name == 'LAB':
            analysis_codes_json = '[]'
            profile = AnalysisProfile.query.filter_by(
                profile_type='simple', client_name=client_name, sample_type=sample_type
            ).first()
            if profile:
                analysis_codes_json = profile.analyses

            formatted_date = sample_date_obj.strftime('%Y%m%d')
            shift_code = get_12h_shift_code(datetime.now())

            if sample_type == 'CM':
                quarter_code = get_quarter_code(sample_date_obj)
                final_sample_code = f"CM_{formatted_date}{shift_code}{quarter_code}"
            elif sample_type in ['GBW', 'Test']:
                final_sample_code = f"{sample_type}_{formatted_date}{shift_code}"
            else:
                final_sample_code = f"LAB_UNKNOWN_{formatted_date}"

            sample = Sample(
                sample_code=final_sample_code,
                user_id=current_user.id,
                client_name=client_name,
                sample_type=sample_type,
                sample_condition=form.sample_condition.data,
                sample_date=sample_date_obj,
                return_sample=form.return_sample.data,
                delivered_by=form.delivered_by.data,
                prepared_date=form.prepared_date.data,
                prepared_by=form.prepared_by.data,
                notes=form.notes.data,
                weight=None,
                analyses_to_perform=analysis_codes_json,
            )
            db.session.add(sample)
            try:
                db.session.commit()
                flash(f'Дээж амжилттай бүртгэгдлээ: {final_sample_code}', 'success')
            except IntegrityError:
                db.session.rollback()
                flash(f'БҮРТГЭЛ АМЖИЛТГҮЙ: "{final_sample_code}" нэртэй дээж аль хэдийн бүртгэлтэй байна.', 'danger')
                return render_template('index.html', title='Нүүр хуудас', form=form, active_tab='add-pane')

            return redirect(url_for('main.index', active_tab='add-pane'))

        # --- 4) WTL – MG/Test (гар аргаар sample_code) ---
        elif not list_type and client_name == 'WTL' and sample_type in ['MG', 'Test']:
            if not form.sample_code.data:
                flash('WTL-ийн энэ төрлийн хувьд Sample name заавал оруулна уу.', 'danger')
            else:
                final_sample_code = form.sample_code.data
                assigned_analyses_json = '[]'
                wtl_profiles = AnalysisProfile.query.filter_by(profile_type='pattern').all()
                for profile in wtl_profiles:
                    if profile.pattern in final_sample_code:
                        assigned_analyses_json = profile.analyses
                        break

                sample = Sample(
                    sample_code=final_sample_code,
                    user_id=current_user.id,
                    client_name=client_name,
                    sample_type=sample_type,
                    sample_condition=form.sample_condition.data,
                    sample_date=sample_date_obj,
                    return_sample=form.return_sample.data,
                    delivered_by=form.delivered_by.data,
                    prepared_date=form.prepared_date.data,
                    prepared_by=form.prepared_by.data,
                    notes=form.notes.data,
                    analyses_to_perform=assigned_analyses_json,
                )
                db.session.add(sample)
                try:
                    db.session.commit()
                    flash('Шинэ дээж амжилттай бүртгэгдлээ!', 'success')
                except IntegrityError:
                    db.session.rollback()
                    flash(f'БҮРТГЭЛ АМЖИЛТГҮЙ: "{final_sample_code}" нэртэй дээж аль хэдийн бүртгэлтэй байна.', 'danger')
                    return render_template('index.html', title='Нүүр хуудас', form=form, active_tab='add-pane')

                return redirect(url_for('main.index', active_tab='add-pane'))

        else:
            flash('Форм бүрэн гүйцэд бөглөгдөөгүй эсвэл буруу байна.', 'danger')

    # GET эсвэл POST validation алдаатай үед — аль табыг идэвхтэй байлгах
    active_tab = 'add-pane' if form.errors else request.args.get('active_tab', 'list-pane')
    return render_template('index.html', title='Нүүр хуудас', form=form, active_tab=active_tab)


# ===================== НЭВТРЭХ / ГАРАХ =====================

@main_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))

    from app.models import User  # lazy import
    form = LoginForm()

    if form.validate_on_submit():
        user = db.session.scalar(sa.select(User).where(User.username == form.username.data))
        if user is None or not user.check_password(form.password.data):
            flash('Нэр эсвэл нууц үг буруу байна', 'danger')
            return redirect(url_for('main.login'))
        login_user(user, remember=form.remember_me.data)
        next_page = request.args.get('next')
        if not next_page or not is_safe_url(next_page):
            next_page = url_for('main.index')
        return redirect(next_page)

    return render_template('login.html', title='Нэвтрэх', form=form)


@main_bp.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('main.login'))


# ===================== ДЭЭЖ ЗАСАХ / УСТГАХ =====================

@main_bp.route('/edit_sample/<int:sample_id>', methods=['GET', 'POST'])
@login_required
def edit_sample(sample_id):
    from app.models import Sample, AnalysisType  # lazy import

    sample = Sample.query.get_or_404(sample_id)

    # Засах эрх шалгана
    can_edit = (
        current_user.role in ['admin', 'ahlah']
        or (current_user.role == 'beltgegch' and sample.status == 'new')
    )
    if not can_edit:
        flash('Энэ дээжийг засах эрх танд байхгүй эсвэл дээж аль хэдийн боловсруулалтад орсон байна.', 'warning')
        return redirect(url_for('main.index'))

    # Боломжит шинжилгээний төрлүүд
    all_analysis_types = AnalysisType.query.order_by(AnalysisType.order_num).all()

    # Дээжид оноогдсон шинжилгээ (JSON -> list)
    try:
        current_analyses = json.loads(sample.analyses_to_perform or '[]')
    except json.JSONDecodeError:
        current_analyses = []

    if request.method == 'POST':
        new_code = request.form.get('sample_code', '').strip()
        selected_analyses = request.form.getlist('analyses')

        original_code = sample.sample_code
        code_changed = new_code and new_code != original_code
        analyses_changed = set(selected_analyses) != set(current_analyses)

        if not new_code:
            flash('Дээжний код хоосон байх боломжгүй.', 'danger')
        elif code_changed and Sample.query.filter(Sample.sample_code == new_code).first():
            flash(f'АЛДАА: "{new_code}" нэртэй дээж аль хэдийн бүртгэлтэй тул солих боломжгүй.', 'danger')
        elif code_changed or analyses_changed:
            try:
                if code_changed:
                    sample.sample_code = new_code
                if analyses_changed:
                    sample.analyses_to_perform = json.dumps(selected_analyses)

                db.session.commit()
                flash('Дээжний мэдээлэл амжилттай шинэчлэгдлээ.', 'success')
                return redirect(url_for('main.index'))
            except Exception as e:
                db.session.rollback()
                flash(f'Хадгалахад алдаа гарлаа: {e}', 'danger')
        else:
            flash('Ямар нэгэн өөрчлөлт хийгдээгүй.', 'info')
            return redirect(url_for('main.index'))

    return render_template(
        'edit_sample.html',
        title='Дээж засах',
        sample=sample,
        all_analysis_types=all_analysis_types,
        current_analyses=current_analyses
    )


@main_bp.route('/delete_selected_samples', methods=['POST'])
@login_required
def delete_selected_samples():
    from app.models import Sample  # lazy import

    sample_ids_to_delete = request.form.getlist('sample_ids')
    if not sample_ids_to_delete:
        flash('Устгах дээжээ сонгоно уу!', 'warning')
        return redirect(url_for('main.index'))

    # Зөвхөн Админ эсвэл Ахлах
    if current_user.role not in ['admin', 'ahlah']:
        flash('Сонгосон дээжийг устгах эрх танд байхгүй.', 'danger')
        return redirect(url_for('main.index'))

    deleted_count = 0
    failed_samples = []
    for sample_id_str in sample_ids_to_delete:
        try:
            sample_id = int(sample_id_str)
            sample_to_delete = Sample.query.get(sample_id)
            if sample_to_delete:
                db.session.delete(sample_to_delete)
                deleted_count += 1
            else:
                failed_samples.append(f'ID={sample_id_str} (Олдсонгүй)')
        except Exception as e:
            failed_samples.append(f'ID={sample_id_str} (Алдаа: {e})')

    if deleted_count > 0:
        db.session.commit()
        flash(f'{deleted_count} ш дээж амжилттай устгагдлаа.', 'success')
    if failed_samples:
        flash(f'Алдаа: Дараах дээжнүүдийг устгаж чадсангүй: {", ".join(failed_samples)}', 'danger')

    return redirect(url_for('main.index'))
