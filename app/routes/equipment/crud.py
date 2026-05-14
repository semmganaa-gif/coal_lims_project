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
from flask_babel import lazy_gettext as _l
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from werkzeug.utils import secure_filename

from app import db
from app.constants import UserRole
from app.models import Equipment, MaintenanceLog, UsageLog
from app.repositories import EquipmentRepository, MaintenanceLogRepository
from app.utils.audit import log_audit
from app.utils.database import safe_commit
from app.utils.datetime import now_local
from app.utils.decorators import role_required
from app.utils.shifts import get_shift_date
from app.routes.equipment import equipment_bp, MAX_FILE_SIZE, ALLOWED_EXTENSIONS


# -------------------------------------------------
# Form helpers
# -------------------------------------------------

# Equipment model-д шууд map хийгдэх form талбарууд
_BASE_FIELDS = frozenset({
    'csrf_token', 'name', 'manufacturer', 'model', 'serial', 'lab_code',
    'quantity', 'cycle', 'location', 'room', 'related', 'chk_checked',
    'chk_calibrated', 'manufactured_info', 'commissioned_info', 'remark',
    'category', 'register_type', 'status', 'calibration_note',
    'initial_price', 'residual_price', 'calibration_date', 'next_calibration_date',
    'edit_item_id',
})


def _parse_date(value: str | None):
    """Form-оос огноо parse. None бол None буцаана."""
    if not value:
        return None
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError:
        return None


def _parse_int(value: str | None, default: int = 0, positive: bool = False) -> int:
    """Form-оос int parse. ValueError үед default буцаана."""
    if not value:
        return default
    try:
        v = int(value)
        if positive and v <= 0:
            raise ValueError
        return v
    except ValueError:
        return default


def _parse_float(value: str | None) -> float | None:
    """Form-оос float parse. Алдаатай бол None."""
    if not value:
        return None
    try:
        return float(value)
    except ValueError:
        return None


def _extract_extra_data(form, register_type: str) -> dict | None:
    """Register type-д тохирох нэмэлт талбаруудыг extra_data dict болгоно."""
    if register_type == "main":
        return None
    extra = {k: form[k] for k in form if k not in _BASE_FIELDS and form[k]}
    return extra or None


def _populate_equipment(eq: Equipment, form) -> None:
    """Form өгөгдлөөр Equipment объектыг бөглөнө (add/edit хоёуланд ашиглагдана)."""
    eq.name = form.get("name")
    eq.manufacturer = form.get("manufacturer")
    eq.model = form.get("model")
    if form.get("serial"):
        eq.serial_number = form.get("serial")
    eq.lab_code = form.get("lab_code")
    eq.location = form.get("location")
    eq.room_number = form.get("room")
    eq.related_analysis = form.get("related")
    eq.manufactured_info = form.get("manufactured_info")
    eq.commissioned_info = form.get("commissioned_info")
    eq.remark = form.get("remark")
    eq.category = form.get("category") or "other"
    eq.register_type = form.get("register_type") or "main"

    # Тоон талбарууд
    qty = _parse_int(form.get("quantity"), default=eq.quantity or 1, positive=True)
    if qty > 0:
        eq.quantity = qty

    cycle = _parse_int(form.get("cycle"), default=eq.calibration_cycle_days or 365, positive=True)
    if cycle > 0:
        eq.calibration_cycle_days = cycle

    eq.initial_price = _parse_float(form.get("initial_price")) or eq.initial_price
    eq.residual_price = _parse_float(form.get("residual_price")) or eq.residual_price

    # Огноонууд
    cal_str = form.get("calibration_date")
    if cal_str:
        eq.calibration_date = _parse_date(cal_str)
    elif cal_str == "":
        eq.calibration_date = None

    next_cal_str = form.get("next_calibration_date")
    if next_cal_str:
        eq.next_calibration_date = _parse_date(next_cal_str)
    elif next_cal_str == "":
        eq.next_calibration_date = None

    # Калибрацийн тэмдэглэл
    if form.get("calibration_note") is not None:
        eq.calibration_note = form.get("calibration_note")
    else:
        eq.calibration_note = ", ".join(filter(None, [
            form.get("chk_checked"), form.get("chk_calibrated")
        ]))

    # Статус (edit-д л байна)
    if form.get("status"):
        eq.status = form.get("status")

    # Extra data
    eq.extra_data = _extract_extra_data(form, eq.register_type)


def _commit_with_audit(action: str, eq: Equipment, **extra_details) -> bool:
    """Commit + audit log + flash. Амжилтгүй бол False."""
    try:
        db.session.commit()
        details = {"name": eq.name, "category": eq.category}
        details.update(extra_details)
        log_audit(action=action, resource_type="Equipment", resource_id=eq.id, details=details)
        return True
    except IntegrityError as e:
        db.session.rollback()
        current_app.logger.error(f"IntegrityError in {action}: {e}")
        flash(_l("Өгөгдөл зөрчилдлөө (давхардсан утга)."), "danger")
        return False
    except SQLAlchemyError as e:
        db.session.rollback()
        current_app.logger.error(f"Database error in {action}: {e}")
        flash(_l("Алдаа гарлаа: %(error)s") % {"error": str(e)[:100]}, "danger")
        return False


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
        page=page, per_page=500, error_out=False
    )

    return render_template(
        "equipment/list.html",
        equipments=pagination.items,
        pagination=pagination,
        today=today,
        warning_date=warning_date,
        view=view,
        view_counts={},
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
@role_required(UserRole.SENIOR.value, UserRole.MANAGER.value, UserRole.ADMIN.value)
def add_equipment():
    """Шинэ төхөөрөмж нэмэх."""
    new_eq = Equipment(status="normal")
    new_eq.created_by_id = current_user.id
    _populate_equipment(new_eq, request.form)

    db.session.add(new_eq)
    if _commit_with_audit("create_equipment", new_eq, register_type=new_eq.register_type):
        flash(_l("Амжилттай бүртгэгдлээ."), "success")

    return redirect(url_for("equipment.equipment_list", view=new_eq.category or "all"))


@equipment_bp.route("/edit_equipment/<int:id>", methods=["POST"])
@login_required
@role_required(UserRole.SENIOR.value, UserRole.MANAGER.value, UserRole.ADMIN.value)
def edit_equipment(id):
    """Төхөөрөмжийн мэдээлэл засах."""
    eq = EquipmentRepository.get_by_id(id)
    if not eq:
        abort(404)

    _populate_equipment(eq, request.form)

    if _commit_with_audit("update_equipment", eq, status=eq.status):
        flash(_l("Амжилттай шинэчлэгдлээ."), "success")

    return redirect(url_for("equipment.equipment_detail", id=id))


# --- ГАНЦААРЧИЛЖ УСТГАХ ---

@equipment_bp.route("/equipment/delete/<int:id>", methods=["POST"])
@login_required
@role_required(UserRole.SENIOR.value, UserRole.MANAGER.value, UserRole.ADMIN.value)
def delete_equipment(id):
    """Төхөөрөмж устгах (түүхтэй бол retired болгоно)."""
    eq = EquipmentRepository.get_by_id(id)
    if not eq:
        abort(404)

    eq_name = eq.name
    has_history = (
        MaintenanceLog.query.filter_by(equipment_id=eq.id).first()
        or UsageLog.query.filter_by(equipment_id=eq.id).first()
    )

    if has_history:
        eq.status = "retired"
        flash(f"'{eq_name}_l(' багаж түүхтэй тул ')Ашиглалтаас гарсан' төлөвт шилжүүллээ.", "warning")
    else:
        db.session.delete(eq)
        flash(f"'{eq_name}' устгагдлаа.", "success")

    action = "retire_equipment" if has_history else "delete_equipment"
    _commit_with_audit(action, eq, had_history=has_history)
    return redirect(url_for("equipment.equipment_list"))


# --- ОЛНООР УСТГАХ ---

@equipment_bp.route("/bulk_delete", methods=["POST"])
@login_required
@role_required(UserRole.SENIOR.value, UserRole.MANAGER.value, UserRole.ADMIN.value)
def bulk_delete():
    """Олон төхөөрөмж нэг дор устгах."""
    ids = request.form.getlist("equipment_ids")
    if not ids:
        flash(_l("Багаж сонгогдоогүй байна."), "warning")
        return redirect(url_for("equipment.equipment_list"))

    deleted_names, retired_names = [], []

    for eq_id in ids:
        eq = EquipmentRepository.get_by_id(eq_id)
        if not eq:
            continue
        has_history = (
            MaintenanceLog.query.filter_by(equipment_id=eq.id).first()
            or UsageLog.query.filter_by(equipment_id=eq.id).first()
        )
        if has_history:
            eq.status = "retired"
            retired_names.append(eq.name)
        else:
            deleted_names.append(eq.name)
            db.session.delete(eq)

    if not safe_commit(error_msg="Bulk delete equipment commit error", notify=False):
        flash(_l("Олноор устгахад алдаа гарлаа."), "danger")
        return redirect(url_for("equipment.equipment_list"))

    if deleted_names or retired_names:
        log_audit(
            action="bulk_delete_equipment",
            resource_type="Equipment",
            resource_id=None,
            details={
                "deleted_count": len(deleted_names),
                "retired_count": len(retired_names),
                "deleted_names": deleted_names[:10],
                "retired_names": retired_names[:10],
            },
        )

    msg = []
    if deleted_names:
        msg.append(f"{len(deleted_names)} багаж устгагдлаа.")
    if retired_names:
        msg.append(f"{len(retired_names)} багаж түүхтэй тул 'Ашиглалтаас гарсан' төлөвт шилжүүллээ.")
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

    file_filename = _handle_file_upload(next_url)
    if file_filename is False:
        return redirect(next_url)

    # --- Ашиглалт бүртгэл (UsageLog) ---
    if action_type == "Usage":
        minutes = _parse_int(request.form.get("duration_minutes"))
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
        if _commit_with_audit("add_usage_log", eq, duration_minutes=minutes):
            flash(_l("Ашиглалтын бүртгэл хадгалагдлаа."), "success")
        return redirect(next_url)

    # --- Засвар/Калибровка/Шалгалт (MaintenanceLog) ---
    log = MaintenanceLog(
        equipment_id=eq.id,
        action_type=action_type,
        description=request.form.get("description"),
        performed_by=request.form.get("performed_by"),
        certificate_no=request.form.get("certificate_no"),
        action_date=action_date,
        file_path=file_filename,
        performed_by_id=current_user.id,
    )

    if action_type == "Calibration":
        eq.calibration_date = action_date.date()
        eq.next_calibration_date = eq.calibration_date + timedelta(days=eq.calibration_cycle_days or 365)
        if eq.status != "retired":
            eq.status = "normal"
    elif action_type == "Repair":
        eq.status = "maintenance"

    db.session.add(log)
    if _commit_with_audit(
        "add_maintenance_log", eq,
        action_type=action_type, log_id=log.id, has_file=file_filename is not None,
    ):
        flash(_l("Бүртгэл хадгалагдлаа."), "success")
    return redirect(next_url)


def _handle_file_upload(error_redirect_url: str) -> str | None | bool:
    """
    File upload шалгаж хадгална.

    Returns:
        str: Хадгалсан файлын нэр
        None: Файл байхгүй
        False: Алдаа гарсан (redirect хэрэгтэй)
    """
    if "certificate_file" not in request.files:
        return None
    file = request.files["certificate_file"]
    if not file or file.filename == "":
        return None

    file.seek(0, 2)
    file_size = file.tell()
    file.seek(0)

    if file_size > MAX_FILE_SIZE:
        max_mb = f"{MAX_FILE_SIZE / 1024 / 1024:.0f}"
        flash(_l("Файл хэт том байна (дээд хэмжээ %(max)sMB).") % {"max": max_mb}, "danger")
        return False

    filename = secure_filename(file.filename)
    if "." not in filename:
        flash(_l("Файлын өргөтгөл тодорхойгүй байна."), "danger")
        return False

    ext = filename.rsplit(".", 1)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        flash(
            _l("Файлын төрөл зөвшөөрөгдөөгүй (.%(ext)s). Зөвшөөрөгдөх: %(allowed)s") % {
                "ext": ext,
                "allowed": ', '.join(ALLOWED_EXTENSIONS),
            },
            "danger",
        )
        return False

    unique_filename = f"{int(now_local().timestamp())}_{filename}"
    upload_folder = current_app.config.get("UPLOAD_FOLDER")
    if not os.path.exists(upload_folder):
        os.makedirs(upload_folder, mode=0o755)

    full_save_path = os.path.realpath(os.path.join(upload_folder, unique_filename))
    real_upload = os.path.realpath(upload_folder)
    if not full_save_path.startswith(real_upload):
        current_app.logger.warning(f"Path traversal attempt in file save: {unique_filename}")
        flash(_l("Буруу файлын нэр."), "danger")
        return False

    file.save(full_save_path)
    return unique_filename


@equipment_bp.route("/download_cert/<int:log_id>")
@login_required
def download_certificate(log_id):
    """Гэрчилгээний файл татах."""
    log = MaintenanceLogRepository.get_by_id(log_id)
    if not log:
        abort(404)
    if not log.file_path:
        flash(_l("Файл олдсонгүй."), "warning")
        return redirect(request.referrer or url_for("equipment.equipment_list"))

    upload_folder = os.path.abspath(current_app.config.get("UPLOAD_FOLDER", ""))
    safe_filename = os.path.basename(log.file_path)

    full_path = os.path.join(upload_folder, safe_filename)
    if not os.path.exists(full_path):
        flash(_l("Файл олдсонгүй."), "warning")
        return redirect(request.referrer or url_for("equipment.equipment_list"))

    real_path = os.path.realpath(full_path)
    real_upload = os.path.realpath(upload_folder)
    if not real_path.startswith(real_upload):
        current_app.logger.warning(f"Path traversal attempt: {log.file_path}")
        flash(_l("Файлд хандах эрхгүй."), "danger")
        return redirect(request.referrer or url_for("equipment.equipment_list"))

    return send_from_directory(upload_folder, safe_filename, as_attachment=True)
