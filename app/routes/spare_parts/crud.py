# app/routes/spare_parts/crud.py
"""Сэлбэг хэрэгслийн CRUD routes."""

from flask import render_template, request, redirect, url_for, flash, current_app, abort
from flask_login import login_required, current_user
from flask_babel import lazy_gettext as _l

from app.constants import UserRole
from app.repositories import EquipmentRepository
from app.routes.spare_parts import spare_parts_bp, UNITS, STATUS_TYPES
from app.utils.decorators import role_required
from app.services.spare_parts_service import (
    get_categories, get_categories_dict, get_all_categories_ordered,
    create_category, update_category, delete_category as svc_delete_category,
    get_spare_parts_filtered, get_list_stats,
    get_detail_data,
    create_spare_part, update_spare_part,
    save_image_to_disk, delete_image_from_disk,
    receive_stock, consume_stock,
    dispose_spare_part as svc_dispose,
    delete_spare_part_permanently,
)
from app.utils.database import safe_commit


# =====================================================
# КАТЕГОРИ УДИРДЛАГА
# =====================================================

@spare_parts_bp.route('/categories')
@login_required
@role_required(UserRole.MANAGER.value, UserRole.ADMIN.value)
def category_list():
    """Категорийн жагсаалт."""
    categories = get_all_categories_ordered()

    return render_template(
        'spare_parts/category_list.html',
        categories=categories,
    )


@spare_parts_bp.route('/categories/add', methods=['GET', 'POST'])
@login_required
@role_required(UserRole.MANAGER.value, UserRole.ADMIN.value)
def add_category():
    """Шинэ категори нэмэх."""
    if request.method == 'POST':
        code = request.form.get('code', '').strip().lower().replace(' ', '_')
        name = request.form.get('name', '').strip()
        equipment_id_raw = request.form.get('equipment_id')

        cat, error = create_category(
            code=code,
            name=name,
            name_en=request.form.get('name_en', '').strip() or None,
            description=request.form.get('description', '').strip() or None,
            sort_order=int(request.form.get('sort_order', 0) or 0),
            is_active=request.form.get('is_active') == 'on',
            equipment_id=int(equipment_id_raw) if equipment_id_raw else None,
        )
        if error:
            flash(error, 'warning')
        elif safe_commit(f"'{name}' ангилал амжилттай нэмэгдлээ.", "Ангилал нэмэхэд алдаа гарлаа"):
            return redirect(url_for('spare_parts.category_list'))

    equipments = EquipmentRepository.get_all_active()

    return render_template('spare_parts/category_form.html', category=None, mode='add', equipments=equipments)


@spare_parts_bp.route('/categories/edit/<int:id>', methods=['GET', 'POST'])
@login_required
@role_required(UserRole.MANAGER.value, UserRole.ADMIN.value)
def edit_category(id):
    """Категори засварлах."""
    if request.method == 'POST':
        equipment_id_raw = request.form.get('equipment_id')
        cat, error = update_category(
            category_id=id,
            name=request.form.get('name', '').strip(),
            name_en=request.form.get('name_en', '').strip() or None,
            description=request.form.get('description', '').strip() or None,
            sort_order=int(request.form.get('sort_order', 0) or 0),
            is_active=request.form.get('is_active') == 'on',
            equipment_id=int(equipment_id_raw) if equipment_id_raw else None,
        )
        if error == 'not_found':
            abort(404)
        elif error:
            flash(error, 'warning')
        elif safe_commit('Ангилал амжилттай шинэчлэгдлээ.', 'Ангилал шинэчлэхэд алдаа гарлаа'):
            return redirect(url_for('spare_parts.category_list'))
        # On GET or failed POST, we need cat for the form
        # Re-fetch for GET rendering below

    from app import db
    from app.models import SparePartCategory
    cat = db.session.get(SparePartCategory, id)
    if not cat:
        abort(404)

    equipments = EquipmentRepository.get_all_active()

    return render_template('spare_parts/category_form.html', category=cat, mode='edit', equipments=equipments)


@spare_parts_bp.route('/categories/delete/<int:id>', methods=['POST'])
@login_required
@role_required(UserRole.ADMIN.value)
def delete_category(id):
    """Категори устгах."""
    name, error = svc_delete_category(id)
    if error == 'not_found':
        abort(404)
    elif error:
        flash(error, 'warning')
    else:
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

    spare_parts = get_spare_parts_filtered(
        category=category, status=status, view=view
    )
    stats = get_list_stats()

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
    spare_part, usages, logs = get_detail_data(id)
    if not spare_part:
        abort(404)

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
@role_required(UserRole.CHEMIST.value, UserRole.SENIOR.value, UserRole.MANAGER.value, UserRole.ADMIN.value)
def add_spare_part():
    """Шинэ сэлбэг нэмэх."""
    if request.method == 'POST':
        data = {
            'name': request.form.get('name'),
            'name_en': request.form.get('name_en'),
            'part_number': request.form.get('part_number'),
            'description': request.form.get('description'),
            'manufacturer': request.form.get('manufacturer'),
            'supplier': request.form.get('supplier'),
            'quantity': request.form.get('quantity'),
            'unit': request.form.get('unit', 'pcs'),
            'reorder_level': request.form.get('reorder_level'),
            'unit_price': request.form.get('unit_price'),
            'storage_location': request.form.get('storage_location'),
            'compatible_equipment': request.form.get('compatible_equipment'),
            'usage_life_months': request.form.get('usage_life_months'),
            'category': request.form.get('category', 'general'),
            'equipment_id': request.form.get('equipment_id'),
        }

        # Handle image upload
        if 'image' in request.files:
            file = request.files['image']
            if file and file.filename:
                image_path = save_image_to_disk(file, current_app.root_path)
                if image_path:
                    data['image_path'] = image_path

        spare_part, error = create_spare_part(data, user_id=current_user.id)
        if error:
            flash(_l('Алдаа: %(error)s') % {'error': error}, 'danger')
        elif safe_commit(f"'{spare_part.name}' амжилттай нэмэгдлээ.", "Сэлбэг нэмэхэд алдаа гарлаа"):
            return redirect(url_for('spare_parts.spare_part_list'))

    # GET
    equipments = EquipmentRepository.get_all_active()

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
@role_required(UserRole.CHEMIST.value, UserRole.SENIOR.value, UserRole.MANAGER.value, UserRole.ADMIN.value)
def edit_spare_part(id):
    """Сэлбэг засварлах."""
    from app import db
    from app.models import SparePart as SparePartModel
    spare_part = db.session.get(SparePartModel, id)
    if not spare_part:
        abort(404)

    if request.method == 'POST':
        data = {
            'name': request.form.get('name'),
            'name_en': request.form.get('name_en'),
            'part_number': request.form.get('part_number'),
            'description': request.form.get('description'),
            'manufacturer': request.form.get('manufacturer'),
            'supplier': request.form.get('supplier'),
            'quantity': request.form.get('quantity'),
            'unit': request.form.get('unit', 'pcs'),
            'reorder_level': request.form.get('reorder_level'),
            'unit_price': request.form.get('unit_price'),
            'storage_location': request.form.get('storage_location'),
            'compatible_equipment': request.form.get('compatible_equipment'),
            'usage_life_months': request.form.get('usage_life_months'),
            'category': request.form.get('category', 'general'),
            'equipment_id': request.form.get('equipment_id'),
        }

        # Handle image upload
        if 'image' in request.files:
            file = request.files['image']
            if file and file.filename:
                # Delete old image
                if spare_part.image_path:
                    delete_image_from_disk(spare_part.image_path, current_app.root_path)
                # Save new image
                image_path = save_image_to_disk(file, current_app.root_path)
                if image_path:
                    data['image_path'] = image_path

        # Handle image delete checkbox
        if request.form.get('delete_image') == 'yes':
            if spare_part.image_path:
                delete_image_from_disk(spare_part.image_path, current_app.root_path)
                data['image_path'] = None

        updated_part, error = update_spare_part(id, data, user_id=current_user.id)
        if error == 'not_found':
            abort(404)
        elif error:
            flash(_l('Алдаа: %(error)s') % {'error': error}, 'danger')
        elif safe_commit('Амжилттай шинэчлэгдлээ.', 'Сэлбэг шинэчлэхэд алдаа гарлаа'):
            return redirect(url_for('spare_parts.spare_part_detail', id=id))

    # GET
    equipments = EquipmentRepository.get_all_active()

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
@role_required(UserRole.CHEMIST.value, UserRole.SENIOR.value, UserRole.MANAGER.value, UserRole.ADMIN.value)
def receive_spare_part(id):
    """Сэлбэг нөөц нэмэх (шинээр ирсэн)."""
    try:
        quantity = float(request.form.get('quantity', 0))
        notes = request.form.get('notes', 'Шинээр ирсэн')

        result, error = receive_stock(id, quantity, user_id=current_user.id, notes=notes)
        if error == 'not_found':
            abort(404)
        elif error:
            flash(error, 'warning')
        else:
            safe_commit(
                f"{result['quantity_added']} {result['unit']} нэмэгдлээ. Нийт: {result['new_total']}",
                'Нөөц нэмэхэд алдаа гарлаа'
            )

    except (ValueError, TypeError) as e:
        from app import db
        db.session.rollback()
        current_app.logger.error(f"Error receiving spare part: {e}")
        flash(f'Error: {str(e)[:100]}', 'danger')

    return redirect(url_for('spare_parts.spare_part_detail', id=id))


@spare_parts_bp.route('/consume/<int:id>', methods=['POST'])
@login_required
def consume_spare_part(id):
    """Сэлбэг зарцуулах (ашиглах)."""
    try:
        quantity = float(request.form.get('quantity', 0))
        equipment_id = request.form.get('equipment_id')
        purpose = request.form.get('purpose', '')
        notes = request.form.get('notes')

        result, error = consume_stock(
            spare_part_id=id,
            quantity=quantity,
            user_id=current_user.id,
            equipment_id=equipment_id,
            purpose=purpose,
            notes=notes,
        )
        if error == 'not_found':
            abort(404)
        elif error:
            flash(error, 'warning' if _l('Тоо хэмжээ') in error else 'danger')
        else:
            safe_commit(
                f"{result['consumed']} {result['unit']} зарцуулагдлаа. Үлдэгдэл: {result['remaining']}",
                'Сэлбэг зарцуулахад алдаа гарлаа'
            )

    except (ValueError, TypeError) as e:
        from app import db
        db.session.rollback()
        current_app.logger.error(f"Error consuming spare part: {e}")
        flash(f'Error: {str(e)[:100]}', 'danger')

    return redirect(url_for('spare_parts.spare_part_detail', id=id))


@spare_parts_bp.route('/dispose/<int:id>', methods=['POST'])
@login_required
@role_required(UserRole.SENIOR.value, UserRole.MANAGER.value, UserRole.ADMIN.value)
def dispose_spare_part(id):
    """Сэлбэг устгах (disposal)."""
    reason = request.form.get('reason', 'Устгав')
    name, error = svc_dispose(id, user_id=current_user.id, reason=reason)
    if error == 'not_found':
        abort(404)
    elif error:
        flash(error, 'danger')
    else:
        safe_commit(f"'{name}' устгагдлаа.", 'Сэлбэг устгахад алдаа гарлаа')

    return redirect(url_for('spare_parts.spare_part_list'))


@spare_parts_bp.route('/delete/<int:id>', methods=['POST'])
@login_required
@role_required(UserRole.ADMIN.value)
def delete_spare_part(id):
    """Сэлбэг бүрмөсөн устгах (зөвхөн admin)."""
    name, error = delete_spare_part_permanently(id)
    if error == 'not_found':
        abort(404)
    elif error:
        flash(error, 'danger')
    else:
        safe_commit(f"'{name}' бүрмөсөн устгагдлаа.", "Сэлбэг устгахад алдаа гарлаа")

    return redirect(url_for('spare_parts.spare_part_list'))
