# app/routes/equipment/crud.py
# -*- coding: utf-8 -*-
"""Тоног төхөөрөмжийн үндсэн CRUD үйлдлүүд."""

import os
from datetime import datetime, timedelta

from flask import (
    render_template, request, redirect, url_for,
    flash, abort, send_from_directory, current_app
)
from flask_login import login_required, current_user
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from werkzeug.utils import secure_filename

from app import db
from app.models import Equipment, MaintenanceLog, UsageLog
from app.repositories import EquipmentRepository, MaintenanceLogRepository
from app.utils.audit import log_audit
from app.utils.datetime import now_local
from app.utils.shifts import get_shift_date
from app.routes.equipment import equipment_bp, MAX_FILE_SIZE, ALLOWED_EXTENSIONS


# -------------------------------------------------
# 1. Төхөөрөмжийн жагсаалт
# -------------------------------------------------

@equipment_bp.route("/equipment_list")
@login_required
def equipment_list():
    """Төхөөрөмжийн жагсаалт хуудас."""
    today = now_local().date()
    warning_date = today + timedelta(days=30)
    view = request.args.get("view", "all")
    page = request.args.get("page", 1, type=int)
    per_page = 500

    query = Equipment.query

    if view == "retired":
        query = query.filter(Equipment.status == "retired")
    elif view == "spares":
        query = query.filter(Equipment.status.in_(["needs_spare", "broken"]))
    elif view == "coal":
        query = query.filter(Equipment.category.in_(["furnace", "prep", "analysis", "other"]))
    elif view == "new":
        query = query.filter(Equipment.status == "normal").order_by(Equipment.id.desc())
    elif view != "all":
        query = query.filter(Equipment.category == view)

    if view != "retired":
        query = query.filter(Equipment.status != "retired")

    pagination = query.order_by(Equipment.name.asc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    equipments = pagination.items
    view_counts = {}

    return render_template(
        "equipment/list.html",
        equipments=equipments,
        pagination=pagination,
        today=today,
        warning_date=warning_date,
        view=view,
        view_counts=view_counts,
    )


# -------------------------------------------------
# 2. Дэлгэрэнгүй & CRUD
# -------------------------------------------------

@equipment_bp.route("/equipment/<int:id>")
@login_required
def equipment_detail(id):
    """Төхөөрөмжийн дэлгэрэнгүй мэдээлэл + журнал."""
    eq = EquipmentRepository.get_by_id(id)
    if not eq:
        abort(404)
    usage_logs = UsageLog.query.filter_by(equipment_id=id).order_by(UsageLog.start_time.desc()).all()
    return render_template("equipment/detail.html", eq=eq, usage_logs=usage_logs)


@equipment_bp.route("/equipment/<int:id>/journal")
@login_required
def equipment_journal_page(id):
    """Тухайн багажийн тусдаа журнал хуудас."""
    eq = EquipmentRepository.get_by_id(id)
    if not eq:
        abort(404)
    today = get_shift_date()
    return render_template(
        "equipment/eq_journal.html",
        eq=eq,
        start_date=today - timedelta(days=29),
        end_date=today,
    )


@equipment_bp.route("/add_equipment", methods=["POST"])
@login_required
def add_equipment():
    """Шинэ төхөөрөмж нэмэх."""
    if current_user.role not in ["senior", "manager", "admin"]:
        flash("Эрх хүрэлцэхгүй байна.", "danger")
        return redirect(url_for("equipment.equipment_list"))

    try:
        quantity = int(request.form.get("quantity", "1"))
        if quantity <= 0:
            raise ValueError("Тоо ширхэг эерэг тоо байх ёстой")
    except ValueError as e:
        flash(f"Буруу тоо ширхэг: {e}", "error")
        return redirect(url_for("equipment.equipment_list"))

    try:
        calibration_cycle_days = int(request.form.get("cycle", "365"))
        if calibration_cycle_days <= 0:
            raise ValueError("Калибрацийн мөчлөг эерэг тоо байх ёстой")
    except ValueError as e:
        flash(f"Буруу калибрацийн мөчлөг: {e}", "error")
        return redirect(url_for("equipment.equipment_list"))

    register_type = request.form.get("register_type", "main") or "main"

    # Баталгаажуулалтын огноонууд
    calibration_date = None
    calibration_date_str = request.form.get("calibration_date")
    if calibration_date_str:
        try:
            calibration_date = datetime.strptime(calibration_date_str, "%Y-%m-%d").date()
        except ValueError:
            pass

    next_calibration_date = None
    next_calibration_date_str = request.form.get("next_calibration_date")
    if next_calibration_date_str:
        try:
            next_calibration_date = datetime.strptime(next_calibration_date_str, "%Y-%m-%d").date()
        except ValueError:
            pass

    # Үндсэн талбаруудаас гадна register_type-д зориулсан нэмэлт талбаруудыг extra_data-д хадгална
    base_fields = {
        'csrf_token', 'name', 'manufacturer', 'model', 'serial', 'lab_code',
        'quantity', 'cycle', 'location', 'room', 'related', 'chk_checked',
        'chk_calibrated', 'manufactured_info', 'commissioned_info', 'remark',
        'category', 'register_type', 'calibration_date', 'next_calibration_date',
    }
    extra_data = {}
    if register_type != 'main':
        for key in request.form:
            if key not in base_fields and request.form.get(key):
                extra_data[key] = request.form.get(key)
        extra_data.pop('csrf_token', None)
        extra_data.pop('edit_item_id', None)

    new_eq = Equipment(
        name=request.form.get("name"),
        manufacturer=request.form.get("manufacturer"),
        model=request.form.get("model"),
        serial_number=request.form.get("serial"),
        lab_code=request.form.get("lab_code"),
        quantity=quantity,
        calibration_cycle_days=calibration_cycle_days,
        calibration_date=calibration_date,
        next_calibration_date=next_calibration_date,
        location=request.form.get("location"),
        room_number=request.form.get("room"),
        related_analysis=request.form.get("related"),
        calibration_note=', '.join(filter(None, [request.form.get("chk_checked"), request.form.get("chk_calibrated")])),
        manufactured_info=request.form.get("manufactured_info"),
        commissioned_info=request.form.get("commissioned_info"),
        remark=request.form.get("remark"),
        status="normal",
        category=request.form.get("category") or "other",
        register_type=register_type,
        extra_data=extra_data if extra_data else None,
    )
    new_eq.created_by_id = current_user.id
    db.session.add(new_eq)
    try:
        db.session.commit()
        # Audit log
        log_audit(
            action='create_equipment',
            resource_type='Equipment',
            resource_id=new_eq.id,
            details={
                'name': new_eq.name,
                'category': new_eq.category,
                'register_type': register_type
            }
        )
        flash("Амжилттай бүртгэгдлээ.", "success")
    except SQLAlchemyError as e:
        db.session.rollback()
        current_app.logger.error(f"Database error in add_equipment: {e}")
        flash(f"Алдаа гарлаа: {str(e)[:100]}", "danger")
    view = request.form.get("category") or "all"
    return redirect(url_for("equipment.equipment_list", view=view))


@equipment_bp.route("/edit_equipment/<int:id>", methods=["POST"])
@login_required
def edit_equipment(id):
    """Төхөөрөмжийн мэдээлэл засах."""
    if current_user.role not in ["senior", "manager", "admin"]:
        flash("Эрх хүрэлцэхгүй байна.", "danger")
        return redirect(url_for("equipment.equipment_detail", id=id))

    eq = EquipmentRepository.get_by_id(id)
    if not eq:
        abort(404)
    eq.name = request.form.get("name")
    eq.manufacturer = request.form.get("manufacturer")
    eq.model = request.form.get("model")
    if request.form.get("serial"):
        eq.serial_number = request.form.get("serial")
    eq.lab_code = request.form.get("lab_code")
    eq.location = request.form.get("location")
    eq.room_number = request.form.get("room")
    eq.related_analysis = request.form.get("related")

    if request.form.get("cycle"):
        try:
            cycle_value = int(request.form.get("cycle"))
            if cycle_value <= 0:
                raise ValueError("Калибрацийн мөчлөг эерэг тоо байх ёстой")
            eq.calibration_cycle_days = cycle_value
        except ValueError as e:
            flash(f"Буруу калибрацийн мөчлөг: {e}", "error")
            return redirect(url_for("equipment.equipment_detail", id=id))

    if request.form.get("status"):
        eq.status = request.form.get("status")
    eq.calibration_note = request.form.get("calibration_note")
    eq.remark = request.form.get("remark")
    eq.category = request.form.get("category") or "other"
    eq.register_type = request.form.get("register_type") or "main"

    # Баталгаажуулалтын огноонууд
    calibration_date_str = request.form.get("calibration_date")
    if calibration_date_str:
        try:
            eq.calibration_date = datetime.strptime(calibration_date_str, "%Y-%m-%d").date()
        except ValueError:
            pass
    elif calibration_date_str == '':
        eq.calibration_date = None

    next_calibration_date_str = request.form.get("next_calibration_date")
    if next_calibration_date_str:
        try:
            eq.next_calibration_date = datetime.strptime(next_calibration_date_str, "%Y-%m-%d").date()
        except ValueError:
            pass
    elif next_calibration_date_str == '':
        eq.next_calibration_date = None

    if request.form.get("quantity"):
        try:
            eq.quantity = int(request.form.get("quantity"))
        except ValueError:
            pass
    eq.manufactured_info = request.form.get("manufactured_info")
    eq.commissioned_info = request.form.get("commissioned_info")

    # register_type-д тохирох extra fields-г extra_data-д хадгалах
    base_fields = {
        'csrf_token', 'name', 'manufacturer', 'model', 'serial', 'lab_code',
        'quantity', 'cycle', 'location', 'room', 'related', 'chk_checked',
        'chk_calibrated', 'manufactured_info', 'commissioned_info', 'remark',
        'category', 'register_type', 'status', 'calibration_note',
        'initial_price', 'residual_price', 'calibration_date', 'next_calibration_date',
    }
    extra_data = {}
    for key in request.form:
        if key not in base_fields and request.form.get(key):
            extra_data[key] = request.form.get(key)
    eq.extra_data = extra_data if extra_data else None


    if request.form.get("initial_price"):
        try:
            eq.initial_price = float(request.form.get("initial_price"))
        except ValueError:
            pass
    if request.form.get("residual_price"):
        try:
            eq.residual_price = float(request.form.get("residual_price"))
        except ValueError:
            pass

    try:
        db.session.commit()
        # Audit log
        log_audit(
            action='update_equipment',
            resource_type='Equipment',
            resource_id=eq.id,
            details={
                'name': eq.name,
                'status': eq.status,
                'category': eq.category
            }
        )
        flash("Амжилттай шинэчлэгдлээ.", "success")
    except IntegrityError as e:
        db.session.rollback()
        current_app.logger.error(f"IntegrityError in edit_equipment: {e}")
        flash("Өгөгдөл зөрчилдлөө (давхардсан утга).", "danger")
    except SQLAlchemyError as e:
        db.session.rollback()
        current_app.logger.error(f"Database error in edit_equipment: {e}")
        flash(f"Алдаа гарлаа: {str(e)[:100]}", "danger")
    return redirect(url_for("equipment.equipment_detail", id=id))


# --- ГАНЦААРЧИЛЖ УСТГАХ ---

@equipment_bp.route("/equipment/delete/<int:id>", methods=["POST"])
@login_required
def delete_equipment(id):
    """Төхөөрөмж устгах (түүхтэй бол retired болгоно)."""
    if current_user.role not in ["senior", "manager", "admin"]:
        flash("Эрх хүрэлцэхгүй байна.", "danger")
        return redirect(url_for("equipment.equipment_list"))

    eq = EquipmentRepository.get_by_id(id)
    if not eq:
        abort(404)
    eq_name = eq.name
    eq_id = eq.id
    has_history = MaintenanceLog.query.filter_by(equipment_id=eq.id).first() or \
                  UsageLog.query.filter_by(equipment_id=eq.id).first()

    action = 'retire_equipment' if has_history else 'delete_equipment'
    if has_history:
        eq.status = "retired"
        flash(f"'{eq_name}' багаж түүхтэй тул 'Ашиглалтаас гарсан' төлөвт шилжүүллээ.", "warning")
    else:
        db.session.delete(eq)
        flash(f"'{eq_name}' устгагдлаа.", "success")

    try:
        db.session.commit()
        # Audit log
        log_audit(
            action=action,
            resource_type='Equipment',
            resource_id=eq_id,
            details={'name': eq_name, 'had_history': has_history}
        )
    except SQLAlchemyError as e:
        db.session.rollback()
        current_app.logger.error(f"Database error in delete_equipment: {e}")
        flash(f"Устгахад алдаа гарлаа: {str(e)[:100]}", "danger")
    return redirect(url_for("equipment.equipment_list"))


# --- ОЛНООР УСТГАХ ---

@equipment_bp.route("/bulk_delete", methods=["POST"])
@login_required
def bulk_delete():
    """Олон төхөөрөмж нэг дор устгах."""
    if current_user.role not in ["senior", "manager", "admin"]:
        flash("Эрх хүрэлцэхгүй байна.", "danger")
        return redirect(url_for("equipment.equipment_list"))

    ids = request.form.getlist('equipment_ids')
    if not ids:
        flash("Багаж сонгогдоогүй байна.", "warning")
        return redirect(url_for("equipment.equipment_list"))

    deleted_count = 0
    retired_count = 0
    deleted_names = []
    retired_names = []

    for eq_id in ids:
        eq = EquipmentRepository.get_by_id(eq_id)
        if eq:
            has_history = MaintenanceLog.query.filter_by(equipment_id=eq.id).first() or \
                          UsageLog.query.filter_by(equipment_id=eq.id).first()
            if has_history:
                eq.status = "retired"
                retired_count += 1
                retired_names.append(eq.name)
            else:
                deleted_names.append(eq.name)
                db.session.delete(eq)
                deleted_count += 1

    try:
        db.session.commit()
        # Audit log
        if deleted_count > 0 or retired_count > 0:
            log_audit(
                action='bulk_delete_equipment',
                resource_type='Equipment',
                resource_id=None,
                details={
                    'deleted_count': deleted_count,
                    'retired_count': retired_count,
                    'deleted_names': deleted_names[:10],  # Эхний 10
                    'retired_names': retired_names[:10]
                }
            )
    except SQLAlchemyError as e:
        db.session.rollback()
        current_app.logger.error(f"Database error in bulk_delete: {e}")
        flash(f"Олноор устгахад алдаа гарлаа: {str(e)[:100]}", "danger")
        return redirect(url_for("equipment.equipment_list"))

    msg = []
    if deleted_count > 0:
        msg.append(f"{deleted_count} багаж устгагдлаа.")
    if retired_count > 0:
        msg.append(f"{retired_count} багаж түүхтэй тул 'Ашиглалтаас гарсан' төлөвт шилжүүллээ.")

    flash(" ".join(msg), "success" if msg else "info")
    return redirect(url_for("equipment.equipment_list"))


# -------------------------------------------------
# 3. LOGS & FILES
# -------------------------------------------------

@equipment_bp.route("/add_log/<int:id>", methods=["POST"])
@login_required
def add_maintenance_log(id):
    """Засвар үйлчилгээний бүртгэл нэмэх."""
    eq = EquipmentRepository.get_by_id(id)
    if not eq:
        abort(404)
    action_type = request.form.get("action_type")
    next_url = request.form.get("next") or url_for("equipment.equipment_detail", id=id)

    action_date_str = request.form.get("action_date")
    action_date = now_local()
    if action_date_str:
        try:
            action_date = datetime.strptime(action_date_str, "%Y-%m-%d")
        except ValueError:
            pass

    file_filename = None
    if 'certificate_file' in request.files:
        file = request.files['certificate_file']
        if file and file.filename != '':
            file.seek(0, 2)
            file_size = file.tell()
            file.seek(0)

            if file_size > MAX_FILE_SIZE:
                flash(f"Файл хэт том байна (дээд хэмжээ {MAX_FILE_SIZE/1024/1024:.0f}MB).", "danger")
                return redirect(next_url)

            filename = secure_filename(file.filename)
            if '.' not in filename:
                flash("Файлын өргөтгөл тодорхойгүй байна.", "danger")
                return redirect(next_url)

            ext = filename.rsplit('.', 1)[1].lower()
            if ext not in ALLOWED_EXTENSIONS:
                flash(
                    f"Файлын төрөл зөвшөөрөгдөөгүй (.{ext}). "
                    f"Зөвшөөрөгдөх: {', '.join(ALLOWED_EXTENSIONS)}",
                    "danger"
                )
                return redirect(next_url)

            unique_filename = f"{int(now_local().timestamp())}_{filename}"
            upload_folder = current_app.config.get('UPLOAD_FOLDER')
            if not os.path.exists(upload_folder):
                os.makedirs(upload_folder, mode=0o755)

            # Файлын замыг шалгах
            full_save_path = os.path.realpath(os.path.join(upload_folder, unique_filename))
            real_upload = os.path.realpath(upload_folder)
            if not full_save_path.startswith(real_upload):
                current_app.logger.warning(f"Path traversal attempt in file save: {unique_filename}")
                flash("Буруу файлын нэр.", "danger")
                return redirect(next_url)

            file.save(full_save_path)
            file_filename = unique_filename

    # --- Ашиглалт бүртгэл (UsageLog) ---
    if action_type == "Usage":
        try:
            minutes = int(request.form.get("duration_minutes", 0))
        except (TypeError, ValueError):
            minutes = 0
        usage = UsageLog(
            equipment_id=eq.id,
            start_time=action_date,
            end_time=action_date + timedelta(minutes=minutes),
            duration_minutes=minutes,
            used_by=request.form.get("performed_by") or current_user.username,
            used_by_id=current_user.id,
            purpose=request.form.get("description"),
        )
        db.session.add(usage)
        try:
            db.session.commit()
            log_audit(
                action='add_usage_log',
                resource_type='Equipment',
                resource_id=eq.id,
                details={
                    'equipment_name': eq.name,
                    'duration_minutes': minutes,
                }
            )
            flash("Ашиглалтын бүртгэл хадгалагдлаа.", "success")
        except SQLAlchemyError as e:
            db.session.rollback()
            current_app.logger.error(f"Database error in add_usage_log: {e}")
            flash(f"Алдаа: {str(e)[:100]}", "danger")
        return redirect(next_url)

    # --- Засвар/Калибровка/Шалгалт (MaintenanceLog) ---
    log = MaintenanceLog(
        equipment_id=eq.id, action_type=action_type, description=request.form.get("description"),
        performed_by=request.form.get("performed_by"), certificate_no=request.form.get("certificate_no"),
        action_date=action_date, file_path=file_filename,
        performed_by_id=current_user.id
    )

    if action_type == "Calibration":
        eq.calibration_date = action_date.date()
        eq.next_calibration_date = eq.calibration_date + timedelta(days=eq.calibration_cycle_days or 365)
        if eq.status != "retired":
            eq.status = "normal"
    elif action_type == "Repair":
        eq.status = "maintenance"

    db.session.add(log)
    try:
        db.session.commit()
        log_audit(
            action='add_maintenance_log',
            resource_type='Equipment',
            resource_id=eq.id,
            details={
                'equipment_name': eq.name,
                'action_type': action_type,
                'log_id': log.id,
                'has_file': file_filename is not None
            }
        )
        flash("Бүртгэл хадгалагдлаа.", "success")
    except SQLAlchemyError as e:
        db.session.rollback()
        current_app.logger.error(f"Database error in add_maintenance_log: {e}")
        flash(f"Бүртгэл хадгалахад алдаа гарлаа: {str(e)[:100]}", "danger")
    return redirect(next_url)


@equipment_bp.route("/download_cert/<int:log_id>")
@login_required
def download_certificate(log_id):
    """Гэрчилгээний файл татах."""
    log = MaintenanceLogRepository.get_by_id(log_id)
    if not log:
        abort(404)
    if not log.file_path:
        flash("Файл олдсонгүй.", "warning")
        return redirect(request.referrer or url_for('equipment.equipment_list'))

    upload_folder = os.path.abspath(current_app.config.get('UPLOAD_FOLDER', ''))
    safe_filename = os.path.basename(log.file_path)

    full_path = os.path.join(upload_folder, safe_filename)
    if not os.path.exists(full_path):
        flash("Файл олдсонгүй.", "warning")
        return redirect(request.referrer or url_for('equipment.equipment_list'))

    real_path = os.path.realpath(full_path)
    real_upload = os.path.realpath(upload_folder)
    if not real_path.startswith(real_upload):
        current_app.logger.warning(f"Path traversal attempt: {log.file_path}")
        flash("Файлд хандах эрхгүй.", "danger")
        return redirect(request.referrer or url_for('equipment.equipment_list'))

    return send_from_directory(upload_folder, safe_filename, as_attachment=True)
