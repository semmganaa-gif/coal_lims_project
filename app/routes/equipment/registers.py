# app/routes/equipment/registers.py
# -*- coding: utf-8 -*-
"""Тоног төхөөрөмжийн тусгай бүртгэлүүд (7 журнал)."""

from datetime import timedelta

from flask import (
    render_template, request, redirect, url_for,
    flash, abort, current_app
)
from flask_login import login_required, current_user
from sqlalchemy.exc import SQLAlchemyError

from app import db
from app.models import Equipment
from app.utils.shifts import get_shift_date
from app.routes.equipment import equipment_bp


# -------------------------------------------------
# NAVIGATION
# -------------------------------------------------

@equipment_bp.route("/equipment_journal", endpoint="equipment_journal")
@login_required
def equipment_journal_hub():
    """Төхөөрөмжийн журналын үндсэн хуудас."""
    return render_template("equipment/hub.html")


@equipment_bp.route("/equipment_journal/grid", endpoint="equipment_journal_grid")
@login_required
def equipment_journal_grid():
    """Төхөөрөмжийн журналын grid хуудас."""
    category = request.args.get("category", "all")
    titles = {
        "all": "Нэгдсэн тойм (Бүгд)",
        "furnace": "1. Шатаах зуух",
        "prep": "2. Дээж бэлтгэл",
        "analysis": "3. Шинжилгээний багаж",
        "water": "4. Усны лаб",
        "micro": "5. Микробиологи лаб",
        "wtl": "6. БС лаб",
        "balance": "7. Жин",
        "other": "8. Бусад"
    }
    title = titles.get(category, "Тоног Төхөөрөмжийн Журнал")

    today = get_shift_date()
    return render_template(
        "equipment/journal.html",
        title=title,
        start_date=today - timedelta(days=29),
        end_date=today,
        category=category
    )


# -------------------------------------------------
# SPECIAL REGISTERS (7 журнал)
# -------------------------------------------------

@equipment_bp.route("/equipment_journal/<journal_type>", endpoint="equipment_journal_special")
@login_required
def equipment_journal_special(journal_type):
    """Хэмжих хэрэгсэл / Шилэн хэмжүүрийн журнал."""
    # Redirect spares_register to dedicated Spare Parts module
    if journal_type == "spares_register":
        return redirect(url_for("spare_parts.spare_part_list"))

    templates = {
        "measurement": "equipment/measurement_journal.html",
        "glassware": "equipment/glassware_journal.html",
        "internal_check": "equipment/internal_check.html",
        "new_equipment": "equipment/new_register.html",
        "out_of_service": "equipment/out_of_service.html",
        "balances_register": "equipment/balances_register.html",
    }
    template = templates.get(journal_type)
    if not template:
        flash("Журнал олдсонгүй.", "warning")
        return redirect(url_for("equipment.equipment_journal"))

    if journal_type == 'balances_register':
        items = Equipment.query.filter_by(category='balance')
    elif journal_type == 'out_of_service':
        items = Equipment.query.filter_by(status='retired')
    elif journal_type == 'new_equipment':
        items = Equipment.query.filter(
            Equipment.commissioned_info.isnot(None),
            Equipment.commissioned_info != ''
        )
    else:
        items = Equipment.query.filter_by(register_type=journal_type)
    items = items.order_by(Equipment.id.asc()).all()
    items_data = []
    for item in items:
        row = {
            'id': item.id,
            'name': item.name or '',
            'manufacturer': item.manufacturer or '',
            'model': item.model or '',
            'serial_number': item.serial_number or '',
            'lab_code': item.lab_code or '',
            'quantity': item.quantity or 1,
            'location': item.location or '',
            'remark': item.remark or '',
        }
        if item.extra_data:
            row.update(item.extra_data)
        if 'qty' not in row and item.quantity:
            row['qty'] = item.quantity
        items_data.append(row)

    return render_template(template, journal_type=journal_type, items=items_data)


@equipment_bp.route("/add_register_item/<register_type>", methods=["POST"])
@login_required
def add_register_item(register_type):
    """Бүртгэлд шинэ мөр нэмэх."""
    if current_user.role not in ["senior", "manager", "admin"]:
        flash("Хандах эрхгүй.", "danger")
        return redirect(url_for("equipment.equipment_journal_special", journal_type=register_type))

    data = request.form.to_dict()
    data.pop('csrf_token', None)
    data.pop('edit_item_id', None)

    if 'qty' in data and 'quantity' not in data:
        data['quantity'] = data.pop('qty')
    data.pop('qty', None)

    # quantity type coercion with validation
    try:
        quantity = int(data.pop('quantity', '1') or '1')
    except (ValueError, TypeError):
        flash("Буруу тоо ширхэг утга.", "error")
        return redirect(url_for("equipment.equipment_journal_special", journal_type=register_type))

    new_item = Equipment(
        name=data.pop('name', ''),
        manufacturer=data.pop('manufacturer', ''),
        model=data.pop('model', ''),
        serial_number=data.pop('serial_number', ''),
        lab_code=data.pop('lab_code', ''),
        quantity=quantity,
        location=data.pop('location', ''),
        remark=data.pop('remark', ''),
        register_type=register_type,
        status='normal',
        category='other',
        extra_data=data if data else None,
    )
    db.session.add(new_item)
    try:
        db.session.commit()
        flash("Амжилттай нэмэгдлээ.", "success")
    except SQLAlchemyError as e:
        db.session.rollback()
        current_app.logger.error(f"Error adding register item: {e}")
        flash(f"Алдаа: {str(e)[:100]}", "danger")
    return redirect(url_for("equipment.equipment_journal_special", journal_type=register_type))


@equipment_bp.route("/edit_register_item/<int:id>", methods=["POST"])
@login_required
def edit_register_item(id):
    """Бүртгэлийн мөр засах."""
    if current_user.role not in ["senior", "manager", "admin"]:
        flash("Хандах эрхгүй.", "danger")
        return redirect(url_for("equipment.equipment_list"))

    item = db.session.get(Equipment, id)
    if not item:
        abort(404)
    data = request.form.to_dict()
    data.pop('csrf_token', None)
    data.pop('edit_item_id', None)
    register_type = item.register_type

    if 'qty' in data and 'quantity' not in data:
        data['quantity'] = data.pop('qty')
    data.pop('qty', None)

    item.name = data.pop('name', item.name)
    item.manufacturer = data.pop('manufacturer', item.manufacturer)
    item.model = data.pop('model', item.model)
    item.serial_number = data.pop('serial_number', item.serial_number)
    item.lab_code = data.pop('lab_code', item.lab_code)

    # quantity type coercion with validation
    try:
        item.quantity = int(data.pop('quantity', str(item.quantity or 1)) or '1')
    except (ValueError, TypeError):
        flash("Буруу тоо ширхэг утга.", "error")
        return redirect(url_for("equipment.equipment_journal_special", journal_type=register_type))

    item.location = data.pop('location', item.location)
    item.remark = data.pop('remark', item.remark)

    item.extra_data = data if data else None

    try:
        db.session.commit()
        flash("Амжилттай шинэчлэгдлээ.", "success")
    except SQLAlchemyError as e:
        db.session.rollback()
        current_app.logger.error(f"Error editing register item: {e}")
        flash(f"Алдаа: {str(e)[:100]}", "danger")
    return redirect(url_for("equipment.equipment_journal_special", journal_type=register_type))


@equipment_bp.route("/delete_register_items", methods=["POST"])
@login_required
def delete_register_items():
    """Бүртгэлийн мөрүүд устгах."""
    if current_user.role not in ["senior", "manager", "admin"]:
        flash("Хандах эрхгүй.", "danger")
        return redirect(url_for("equipment.equipment_list"))

    ids = request.form.getlist('item_ids')
    register_type = request.form.get('register_type', 'measurement')

    if not ids:
        flash("Мөр сонгогдоогүй байна.", "warning")
        return redirect(url_for("equipment.equipment_journal_special", journal_type=register_type))

    deleted = 0
    for item_id in ids:
        item = db.session.get(Equipment, item_id)
        if item and item.register_type == register_type:
            db.session.delete(item)
            deleted += 1

    try:
        db.session.commit()
        flash(f"{deleted} мөр устгагдлаа.", "success")
    except SQLAlchemyError as e:
        db.session.rollback()
        current_app.logger.error(f"Error deleting register items: {e}")
        flash(f"Устгахад алдаа гарлаа: {str(e)[:100]}", "danger")
    return redirect(url_for("equipment.equipment_journal_special", journal_type=register_type))
