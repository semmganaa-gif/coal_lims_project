# app/routes/spare_parts/crud.py
"""Сэлбэг хэрэгслийн CRUD routes."""

import os
import uuid
from flask import render_template, request, redirect, url_for, flash, current_app
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from sqlalchemy import func, case
from app import db
from app.models import SparePart, SparePartUsage, SparePartLog, SparePartCategory, Equipment
from datetime import datetime, date
from app.routes.spare_parts import spare_parts_bp, UNITS, STATUS_TYPES
from app.utils.converters import to_float
from app.utils.database import safe_commit


# Зураг upload тохиргоо
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
UPLOAD_FOLDER = 'spare_parts'


def allowed_file(filename):
    """Файлын өргөтгөл зөвшөөрөгдсөн эсэх."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def save_image(file):
    """Зураг хадгалж, path буцаах."""
    if file and allowed_file(file.filename):
        # Unique filename үүсгэх
        ext = file.filename.rsplit('.', 1)[1].lower()
        filename = f"{uuid.uuid4().hex}.{ext}"

        # Upload folder
        upload_path = os.path.join(
            current_app.root_path, 'static', 'uploads', UPLOAD_FOLDER
        )
        os.makedirs(upload_path, exist_ok=True)

        # Файл хадгалах
        file_path = os.path.join(upload_path, filename)
        file.save(file_path)

        return f"uploads/{UPLOAD_FOLDER}/{filename}"
    return None


def delete_image(image_path):
    """Хуучин зураг устгах."""
    if image_path:
        full_path = os.path.join(current_app.root_path, 'static', image_path)
        if os.path.exists(full_path):
            os.remove(full_path)


def log_spare_part_action(spare_part, action, quantity_change=None,
                          quantity_before=None, quantity_after=None, details=None):
    """Сэлбэг хэрэгслийн үйлдлийг бүртгэх (audit log with hash - ISO 17025)."""
    log = SparePartLog(
        spare_part_id=spare_part.id,
        user_id=current_user.id,
        action=action,
        quantity_change=quantity_change,
        quantity_before=quantity_before,
        quantity_after=quantity_after,
        details=details
    )
    log.data_hash = log.compute_hash()
    db.session.add(log)


def get_categories():
    """Database-аас категориудыг авах."""
    cats = SparePartCategory.query.filter_by(is_active=True)\
        .order_by(SparePartCategory.sort_order, SparePartCategory.name).all()
    return [(c.code, c.name) for c in cats]


def get_categories_dict():
    """Категорийн code -> name dict."""
    cats = SparePartCategory.query.filter_by(is_active=True).all()
    return {c.code: c.name for c in cats}


# =====================================================
# КАТЕГОРИ УДИРДЛАГА
# =====================================================

@spare_parts_bp.route('/categories')
@login_required
def category_list():
    """Категорийн жагсаалт."""
    if current_user.role not in ['manager', 'admin']:
        flash('Хандах эрхгүй.', 'danger')
        return redirect(url_for('spare_parts.spare_part_list'))

    categories = SparePartCategory.query.order_by(
        SparePartCategory.sort_order, SparePartCategory.name
    ).all()

    return render_template(
        'spare_parts/category_list.html',
        categories=categories,
    )


@spare_parts_bp.route('/categories/add', methods=['GET', 'POST'])
@login_required
def add_category():
    """Шинэ категори нэмэх."""
    if current_user.role not in ['manager', 'admin']:
        flash('Хандах эрхгүй.', 'danger')
        return redirect(url_for('spare_parts.category_list'))

    if request.method == 'POST':
        code = request.form.get('code', '').strip().lower().replace(' ', '_')
        name = request.form.get('name', '').strip()

        if not code or not name:
            flash('Код болон нэр шаардлагатай.', 'warning')
        elif SparePartCategory.query.filter_by(code=code).first():
            flash(f"'{code}' код аль хэдийн бүртгэгдсэн байна.", 'warning')
        else:
            equipment_id = request.form.get('equipment_id')
            cat = SparePartCategory(
                code=code,
                name=name,
                name_en=request.form.get('name_en', '').strip() or None,
                description=request.form.get('description', '').strip() or None,
                sort_order=int(request.form.get('sort_order', 0) or 0),
                is_active=request.form.get('is_active') == 'on',
                equipment_id=int(equipment_id) if equipment_id else None,
            )
            db.session.add(cat)
            if safe_commit(f"'{name}' ангилал амжилттай нэмэгдлээ.", "Ангилал нэмэхэд алдаа гарлаа"):
                return redirect(url_for('spare_parts.category_list'))

    equipments = Equipment.query.filter(
        Equipment.status != 'retired'
    ).order_by(Equipment.name).all()

    return render_template('spare_parts/category_form.html', category=None, mode='add', equipments=equipments)


@spare_parts_bp.route('/categories/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_category(id):
    """Категори засварлах."""
    if current_user.role not in ['manager', 'admin']:
        flash('Хандах эрхгүй.', 'danger')
        return redirect(url_for('spare_parts.category_list'))

    cat = SparePartCategory.query.get_or_404(id)

    if request.method == 'POST':
        cat.name = request.form.get('name', '').strip()
        cat.name_en = request.form.get('name_en', '').strip() or None
        cat.description = request.form.get('description', '').strip() or None
        cat.sort_order = int(request.form.get('sort_order', 0) or 0)
        cat.is_active = request.form.get('is_active') == 'on'
        equipment_id = request.form.get('equipment_id')
        cat.equipment_id = int(equipment_id) if equipment_id else None

        if safe_commit('Ангилал амжилттай шинэчлэгдлээ.', 'Ангилал шинэчлэхэд алдаа гарлаа'):
            return redirect(url_for('spare_parts.category_list'))

    equipments = Equipment.query.filter(
        Equipment.status != 'retired'
    ).order_by(Equipment.name).all()

    return render_template('spare_parts/category_form.html', category=cat, mode='edit', equipments=equipments)


@spare_parts_bp.route('/categories/delete/<int:id>', methods=['POST'])
@login_required
def delete_category(id):
    """Категори устгах."""
    if current_user.role != 'admin':
        flash('Хандах эрхгүй.', 'danger')
        return redirect(url_for('spare_parts.category_list'))

    cat = SparePartCategory.query.get_or_404(id)

    # Энэ категорид сэлбэг байгаа эсэх шалгах
    count = SparePart.query.filter_by(category=cat.code).count()
    if count > 0:
        flash(f"'{cat.name}' ангилалд {count} сэлбэг бүртгэлтэй байна. Эхлээд тэдгээрийг шилжүүлнэ үү.", 'warning')
        return redirect(url_for('spare_parts.category_list'))

    name = cat.name
    db.session.delete(cat)
    safe_commit(f"'{name}' ангилал устгагдлаа.", "Ангилал устгахад алдаа гарлаа")
    return redirect(url_for('spare_parts.category_list'))


# =====================================================
# СЭЛБЭГ ХЭРЭГСЭЛ CRUD
# =====================================================

@spare_parts_bp.route('/')
@login_required
def spare_part_list():
    """Сэлбэг хэрэгслийн жагсаалт."""
    category = request.args.get('category', '')
    status = request.args.get('status', '')
    view = request.args.get('view', 'all')

    query = SparePart.query

    if category:
        query = query.filter(SparePart.category == category)

    if status:
        query = query.filter(SparePart.status == status)

    if view == "low_stock":
        query = query.filter(SparePart.status.in_(['low_stock', 'out_of_stock']))

    # Устгагдсан сэлбэгийг default-аар нуух (disposed view-ээс бусад)
    if view != "disposed" and status != "disposed":
        query = query.filter(SparePart.status != 'disposed')

    spare_parts_query = query.order_by(SparePart.name.asc()).all()

    # JSON serializable
    spare_parts = []
    for sp in spare_parts_query:
        spare_parts.append({
            'id': sp.id,
            'name': sp.name,
            'name_en': sp.name_en,
            'part_number': sp.part_number,
            'manufacturer': sp.manufacturer,
            'supplier': sp.supplier,
            'quantity': sp.quantity,
            'unit': sp.unit,
            'reorder_level': sp.reorder_level,
            'unit_price': sp.unit_price,
            'storage_location': sp.storage_location,
            'compatible_equipment': sp.compatible_equipment,
            'usage_life_months': sp.usage_life_months,
            'category': sp.category,
            'status': sp.status,
            'equipment_name': sp.equipment.name if sp.equipment else None,
        })

    # P-H3: Нэг query-гээр stats авах (3 COUNT → 1 query)
    stats_row = db.session.query(
        func.count(case((SparePart.status != 'disposed', SparePart.id))).label('total'),
        func.count(case((SparePart.status == 'low_stock', SparePart.id))).label('low_stock'),
        func.count(case((SparePart.status == 'out_of_stock', SparePart.id))).label('out_of_stock'),
    ).one()
    stats = {
        'total': stats_row.total,
        'low_stock': stats_row.low_stock,
        'out_of_stock': stats_row.out_of_stock,
    }

    return render_template(
        "spare_parts/spare_part_list.html",
        spare_parts=spare_parts,
        category=category,
        status=status,
        view=view,
        stats=stats,
        categories=get_categories(),
        categories_dict=get_categories_dict(),
        units=UNITS,
        status_types=STATUS_TYPES,
    )


@spare_parts_bp.route('/<int:id>')
@login_required
def spare_part_detail(id):
    """Сэлбэг хэрэгслийн дэлгэрэнгүй."""
    spare_part = SparePart.query.get_or_404(id)

    # Хэрэглээний түүх
    usages = SparePartUsage.query.filter_by(spare_part_id=id)\
        .order_by(SparePartUsage.used_at.desc()).limit(50).all()

    # Аудит түүх
    logs = SparePartLog.query.filter_by(spare_part_id=id)\
        .order_by(SparePartLog.timestamp.desc()).limit(50).all()

    return render_template(
        "spare_parts/spare_part_detail.html",
        spare_part=spare_part,
        usages=usages,
        logs=logs,
        categories=get_categories(),
        units=UNITS,
    )


@spare_parts_bp.route('/add', methods=['GET', 'POST'])
@login_required
def add_spare_part():
    """Шинэ сэлбэг нэмэх."""
    if current_user.role not in ['chemist', 'senior', 'manager', 'admin']:
        flash('Хандах эрхгүй.', 'danger')
        return redirect(url_for('spare_parts.spare_part_list'))

    if request.method == 'POST':
        try:
            def parse_int(val):
                if val and val.strip():
                    return int(val)
                return None

            spare_part = SparePart(
                name=request.form.get('name'),
                name_en=request.form.get('name_en'),
                part_number=request.form.get('part_number'),
                description=request.form.get('description'),
                manufacturer=request.form.get('manufacturer'),
                supplier=request.form.get('supplier'),
                quantity=to_float(request.form.get('quantity')) or 0,
                unit=request.form.get('unit', 'pcs'),
                reorder_level=to_float(request.form.get('reorder_level')) or 1,
                unit_price=to_float(request.form.get('unit_price')),
                storage_location=request.form.get('storage_location'),
                compatible_equipment=request.form.get('compatible_equipment'),
                usage_life_months=parse_int(request.form.get('usage_life_months')),
                category=request.form.get('category', 'general'),
                created_by_id=current_user.id,
            )

            # Тоног төхөөрөмжтэй холбох
            equipment_id = request.form.get('equipment_id')
            if equipment_id:
                spare_part.equipment_id = int(equipment_id)

            # Зураг upload
            if 'image' in request.files:
                file = request.files['image']
                if file and file.filename:
                    image_path = save_image(file)
                    if image_path:
                        spare_part.image_path = image_path

            spare_part.update_status()
            db.session.add(spare_part)
            db.session.flush()

            # Аудит лог
            log_spare_part_action(
                spare_part, 'created',
                quantity_change=spare_part.quantity,
                quantity_before=0,
                quantity_after=spare_part.quantity,
                details=f"Шинээр үүсгэв: {spare_part.name}"
            )
            if safe_commit(f"'{spare_part.name}' амжилттай нэмэгдлээ.", "Сэлбэг нэмэхэд алдаа гарлаа"):
                return redirect(url_for('spare_parts.spare_part_list'))

        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error creating spare part: {e}")
            flash(f'Алдаа: {str(e)[:100]}', 'danger')

    # GET
    equipments = Equipment.query.filter(
        Equipment.status != 'retired'
    ).order_by(Equipment.name).all()

    return render_template(
        "spare_parts/spare_part_form.html",
        title='Шинэ сэлбэг нэмэх',
        spare_part=None,
        equipments=equipments,
        categories=get_categories(),
        units=UNITS,
        mode='add',
    )


@spare_parts_bp.route('/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_spare_part(id):
    """Сэлбэг засварлах."""
    if current_user.role not in ['chemist', 'senior', 'manager', 'admin']:
        flash('Хандах эрхгүй.', 'danger')
        return redirect(url_for('spare_parts.spare_part_detail', id=id))

    spare_part = SparePart.query.get_or_404(id)

    if request.method == 'POST':
        try:
            def parse_int(val):
                if val and val.strip():
                    return int(val)
                return None

            old_quantity = spare_part.quantity

            spare_part.name = request.form.get('name')
            spare_part.name_en = request.form.get('name_en')
            spare_part.part_number = request.form.get('part_number')
            spare_part.description = request.form.get('description')
            spare_part.manufacturer = request.form.get('manufacturer')
            spare_part.supplier = request.form.get('supplier')
            spare_part.quantity = to_float(request.form.get('quantity')) or 0
            spare_part.unit = request.form.get('unit', 'pcs')
            spare_part.reorder_level = to_float(request.form.get('reorder_level')) or 1
            spare_part.unit_price = to_float(request.form.get('unit_price'))
            spare_part.storage_location = request.form.get('storage_location')
            spare_part.compatible_equipment = request.form.get('compatible_equipment')
            spare_part.usage_life_months = parse_int(request.form.get('usage_life_months'))
            spare_part.category = request.form.get('category', 'general')

            equipment_id = request.form.get('equipment_id')
            spare_part.equipment_id = int(equipment_id) if equipment_id else None

            # Зураг upload
            if 'image' in request.files:
                file = request.files['image']
                if file and file.filename:
                    # Хуучин зураг устгах
                    if spare_part.image_path:
                        delete_image(spare_part.image_path)
                    # Шинэ зураг хадгалах
                    image_path = save_image(file)
                    if image_path:
                        spare_part.image_path = image_path

            # Зураг устгах checkbox
            if request.form.get('delete_image') == 'yes':
                if spare_part.image_path:
                    delete_image(spare_part.image_path)
                    spare_part.image_path = None

            spare_part.update_status()

            # Тоо хэмжээ өөрчлөгдсөн бол лог
            if old_quantity != spare_part.quantity:
                log_spare_part_action(
                    spare_part, 'adjusted',
                    quantity_change=spare_part.quantity - old_quantity,
                    quantity_before=old_quantity,
                    quantity_after=spare_part.quantity,
                    details="Гараар тохируулав"
                )

            # Ерөнхий засварын лог
            log_spare_part_action(
                spare_part, 'updated',
                details="Мэдээлэл шинэчлэв"
            )

            if safe_commit('Амжилттай шинэчлэгдлээ.', 'Сэлбэг шинэчлэхэд алдаа гарлаа'):
                return redirect(url_for('spare_parts.spare_part_detail', id=id))

        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error updating spare part: {e}")
            flash(f'Алдаа: {str(e)[:100]}', 'danger')

    # GET
    equipments = Equipment.query.filter(
        Equipment.status != 'retired'
    ).order_by(Equipment.name).all()

    return render_template(
        "spare_parts/spare_part_form.html",
        title='Сэлбэг засварлах',
        spare_part=spare_part,
        equipments=equipments,
        categories=get_categories(),
        units=UNITS,
        mode='edit',
    )


@spare_parts_bp.route('/receive/<int:id>', methods=['POST'])
@login_required
def receive_spare_part(id):
    """Сэлбэг нөөц нэмэх (шинээр ирсэн)."""
    if current_user.role not in ['chemist', 'senior', 'manager', 'admin']:
        flash('Хандах эрхгүй.', 'danger')
        return redirect(url_for('spare_parts.spare_part_detail', id=id))

    spare_part = SparePart.query.get_or_404(id)

    try:
        quantity = float(request.form.get('quantity', 0))
        if quantity <= 0:
            flash('Тоо хэмжээ 0-ээс их байх ёстой.', 'warning')
            return redirect(url_for('spare_parts.spare_part_detail', id=id))

        old_quantity = spare_part.quantity
        spare_part.quantity += quantity
        spare_part.update_status()

        spare_part.received_date = date.today()

        # Аудит лог
        log_spare_part_action(
            spare_part, 'received',
            quantity_change=quantity,
            quantity_before=old_quantity,
            quantity_after=spare_part.quantity,
            details=request.form.get('notes', 'Шинээр ирсэн')
        )
        safe_commit(
            f'{quantity} {spare_part.unit} нэмэгдлээ. Нийт: {spare_part.quantity}',
            'Нөөц нэмэхэд алдаа гарлаа'
        )

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error receiving spare part: {e}")
        flash(f'Error: {str(e)[:100]}', 'danger')

    return redirect(url_for('spare_parts.spare_part_detail', id=id))


@spare_parts_bp.route('/consume/<int:id>', methods=['POST'])
@login_required
def consume_spare_part(id):
    """Сэлбэг зарцуулах (ашиглах)."""
    spare_part = SparePart.query.get_or_404(id)

    try:
        quantity = float(request.form.get('quantity', 0))
        if quantity <= 0:
            flash('Тоо хэмжээ 0-ээс их байх ёстой.', 'warning')
            return redirect(url_for('spare_parts.spare_part_detail', id=id))

        if quantity > spare_part.quantity:
            flash(f'Нөөц хүрэлцэхгүй байна! Боломжит: {spare_part.quantity} {spare_part.unit}', 'danger')
            return redirect(url_for('spare_parts.spare_part_detail', id=id))

        old_quantity = spare_part.quantity
        spare_part.quantity -= quantity
        spare_part.update_status()

        spare_part.last_used_date = date.today()

        # Equipment холбоос
        equipment_id = request.form.get('equipment_id')

        # Usage бүртгэл
        usage = SparePartUsage(
            spare_part_id=spare_part.id,
            equipment_id=int(equipment_id) if equipment_id else None,
            quantity_used=quantity,
            unit=spare_part.unit,
            purpose=request.form.get('purpose', ''),
            used_by_id=current_user.id,
            quantity_before=old_quantity,
            quantity_after=spare_part.quantity,
            notes=request.form.get('notes'),
        )
        db.session.add(usage)

        # Аудит лог
        log_spare_part_action(
            spare_part, 'consumed',
            quantity_change=-quantity,
            quantity_before=old_quantity,
            quantity_after=spare_part.quantity,
            details=f"Зарцуулав: {request.form.get('purpose', '-')}"
        )
        safe_commit(
            f'{quantity} {spare_part.unit} зарцуулагдлаа. Үлдэгдэл: {spare_part.quantity}',
            'Сэлбэг зарцуулахад алдаа гарлаа'
        )

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error consuming spare part: {e}")
        flash(f'Error: {str(e)[:100]}', 'danger')

    return redirect(url_for('spare_parts.spare_part_detail', id=id))


@spare_parts_bp.route('/dispose/<int:id>', methods=['POST'])
@login_required
def dispose_spare_part(id):
    """Сэлбэг устгах (disposal)."""
    if current_user.role not in ['senior', 'manager', 'admin']:
        flash('Хандах эрхгүй.', 'danger')
        return redirect(url_for('spare_parts.spare_part_detail', id=id))

    spare_part = SparePart.query.get_or_404(id)

    try:
        old_quantity = spare_part.quantity
        reason = request.form.get('reason', 'Устгав')

        spare_part.status = 'disposed'
        spare_part.quantity = 0

        log_spare_part_action(
            spare_part, 'disposed',
            quantity_change=-old_quantity,
            quantity_before=old_quantity,
            quantity_after=0,
            details=f"Устгав: {reason}"
        )

        safe_commit(f"'{spare_part.name}' устгагдлаа.", 'Сэлбэг устгахад алдаа гарлаа')

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error disposing spare part: {e}")
        flash(f'Error: {str(e)[:100]}', 'danger')

    return redirect(url_for('spare_parts.spare_part_list'))


@spare_parts_bp.route('/delete/<int:id>', methods=['POST'])
@login_required
def delete_spare_part(id):
    """Сэлбэг бүрмөсөн устгах (зөвхөн admin)."""
    if current_user.role != 'admin':
        flash('Хандах эрхгүй.', 'danger')
        return redirect(url_for('spare_parts.spare_part_list'))

    spare_part = SparePart.query.get_or_404(id)
    name = spare_part.name

    db.session.delete(spare_part)
    safe_commit(f"'{name}' бүрмөсөн устгагдлаа.", "Сэлбэг устгахад алдаа гарлаа")
    return redirect(url_for('spare_parts.spare_part_list'))
