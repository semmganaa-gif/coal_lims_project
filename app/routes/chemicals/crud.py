# app/routes/chemicals/crud.py
# -*- coding: utf-8 -*-
"""Химийн бодисын үндсэн CRUD үйлдлүүд."""

from flask import (
    render_template, request, redirect, url_for,
    flash, abort, current_app
)
from flask_login import login_required, current_user
from flask_babel import lazy_gettext as _l
from sqlalchemy.exc import SQLAlchemyError

from app import db
from app.constants import UserRole
from app.utils.decorators import role_required
from app.repositories import ChemicalUsageRepository, ChemicalLogRepository
from app.repositories import ChemicalRepository
from app.utils.database import safe_commit
from app.routes.chemicals import chemicals_bp, LAB_TYPES, CATEGORIES, UNITS, STATUS_TYPES
from app.services.chemical_service import (
    get_chemical_list,
    get_chemical_stats_summary,
    create_chemical,
    update_chemical,
    receive_stock,
    consume_chemical_stock,
    dispose_chemical as svc_dispose_chemical,
    get_journal_rows,
)


# -------------------------------------------------
# 1. Химийн бодисын жагсаалт
# -------------------------------------------------

@chemicals_bp.route("/")
@chemicals_bp.route("/list")
@login_required
def chemical_list():
    """Химийн бодисын жагсаалт хуудас."""
    lab = request.args.get("lab", "all")
    category = request.args.get("category", "all")
    status = request.args.get("status", "all")
    view = request.args.get("view", "all")

    chemicals = get_chemical_list(lab=lab, category=category, status=status, view=view)
    stats = get_chemical_stats_summary()

    return render_template(
        "chemicals/chemical_list.html",
        chemicals=chemicals,
        lab=lab,
        category=category,
        status=status,
        view=view,
        stats=stats,
        lab_types=LAB_TYPES,
        categories=CATEGORIES,
        status_types=STATUS_TYPES,
        units=UNITS,
    )


# -------------------------------------------------
# 2. Дэлгэрэнгүй харах
# -------------------------------------------------

@chemicals_bp.route("/<int:id>")
@login_required
def chemical_detail(id):
    """Химийн бодисын дэлгэрэнгүй мэдээлэл."""
    chemical = ChemicalRepository.get_by_id(id)
    if not chemical:
        abort(404)

    # Хэрэглээний түүх
    usages = ChemicalUsageRepository.get_for_chemical(id, limit=50)

    # Аудит түүх
    logs = ChemicalLogRepository.get_for_chemical(id, limit=50)

    from datetime import date as _date
    return render_template(
        "chemicals/chemical_detail.html",
        chemical=chemical,
        usages=usages,
        logs=logs,
        categories=CATEGORIES,
        status_types=STATUS_TYPES,
        units=UNITS,
        lab_types=LAB_TYPES,
        today=_date.today(),
    )


# -------------------------------------------------
# 3. Шинэ нэмэх
# -------------------------------------------------

@chemicals_bp.route("/add", methods=["GET", "POST"])
@login_required
@role_required(UserRole.CHEMIST.value, UserRole.SENIOR.value, UserRole.MANAGER.value, UserRole.ADMIN.value)
def add_chemical():
    """Шинэ химийн бодис нэмэх."""
    if request.method == "POST":
        try:
            data = {
                "name": request.form.get("name"),
                "cas_number": request.form.get("cas_number"),
                "formula": request.form.get("formula"),
                "manufacturer": request.form.get("manufacturer"),
                "supplier": request.form.get("supplier"),
                "catalog_number": request.form.get("catalog_number"),
                "lot_number": request.form.get("lot_number"),
                "grade": request.form.get("grade"),
                "quantity": request.form.get("quantity", 0),
                "unit": request.form.get("unit", "mL"),
                "reorder_level": request.form.get("reorder_level"),
                "received_date": request.form.get("received_date"),
                "expiry_date": request.form.get("expiry_date"),
                "opened_date": request.form.get("opened_date"),
                "storage_location": request.form.get("storage_location"),
                "storage_conditions": request.form.get("storage_conditions"),
                "hazard_class": request.form.get("hazard_class"),
                "lab_type": request.form.get("lab_type", "all"),
                "category": request.form.get("category", "other"),
                "notes": request.form.get("notes"),
                "ghs_pictograms": request.form.getlist("ghs_pictograms"),
                "ghs_signal_word": request.form.get("ghs_signal_word"),
                "sds_version": request.form.get("sds_version"),
                "sds_revision_date": request.form.get("sds_revision_date"),
                "shelf_life_after_opening_days": request.form.get("shelf_life_after_opening_days"),
                "days_alert_before_expiry": request.form.get("days_alert_before_expiry"),
                "prevent_use_if_expired": request.form.get("prevent_use_if_expired"),
            }

            chemical = create_chemical(data, user_id=current_user.id)

            if safe_commit(
                success_msg=f"'{chemical.name}' амжилттай бүртгэгдлээ.",
                error_msg="Химийн бодис бүртгэхэд алдаа гарлаа"
            ):
                return redirect(url_for("chemicals.chemical_detail", id=chemical.id))

        except ValueError as e:
            db.session.rollback()
            flash(_l("Буруу утга: %(value)s") % {"value": e}, "danger")
        except SQLAlchemyError as e:
            db.session.rollback()
            current_app.logger.error(f"Error adding chemical: {e}")
            flash(_l("Алдаа гарлаа: %(error)s") % {"error": str(e)[:100]}, "danger")

    lab = request.args.get("lab", "all")
    return render_template(
        "chemicals/chemical_form.html",
        chemical=None,
        mode="add",
        lab=lab,
        categories=CATEGORIES,
        status_types=STATUS_TYPES,
        units=UNITS,
        lab_types=LAB_TYPES,
    )


# -------------------------------------------------
# 4. Засварлах
# -------------------------------------------------

@chemicals_bp.route("/edit/<int:id>", methods=["GET", "POST"])
@login_required
@role_required(UserRole.CHEMIST.value, UserRole.SENIOR.value, UserRole.MANAGER.value, UserRole.ADMIN.value)
def edit_chemical(id):
    """Химийн бодис засварлах."""
    chemical = ChemicalRepository.get_by_id(id)
    if not chemical:
        abort(404)

    if request.method == "POST":
        try:
            data = {
                "name": request.form.get("name"),
                "cas_number": request.form.get("cas_number"),
                "formula": request.form.get("formula"),
                "manufacturer": request.form.get("manufacturer"),
                "supplier": request.form.get("supplier"),
                "catalog_number": request.form.get("catalog_number"),
                "lot_number": request.form.get("lot_number"),
                "grade": request.form.get("grade"),
                "quantity": request.form.get("quantity", 0),
                "unit": request.form.get("unit", "mL"),
                "reorder_level": request.form.get("reorder_level"),
                "received_date": request.form.get("received_date"),
                "expiry_date": request.form.get("expiry_date"),
                "opened_date": request.form.get("opened_date"),
                "storage_location": request.form.get("storage_location"),
                "storage_conditions": request.form.get("storage_conditions"),
                "hazard_class": request.form.get("hazard_class"),
                "lab_type": request.form.get("lab_type", "all"),
                "category": request.form.get("category", "other"),
                "notes": request.form.get("notes"),
                "ghs_pictograms": request.form.getlist("ghs_pictograms"),
                "ghs_signal_word": request.form.get("ghs_signal_word"),
                "sds_version": request.form.get("sds_version"),
                "sds_revision_date": request.form.get("sds_revision_date"),
                "shelf_life_after_opening_days": request.form.get("shelf_life_after_opening_days"),
                "days_alert_before_expiry": request.form.get("days_alert_before_expiry"),
                "prevent_use_if_expired": request.form.get("prevent_use_if_expired"),
            }

            update_chemical(chemical, data, user_id=current_user.id)

            if safe_commit(
                success_msg="Амжилттай шинэчлэгдлээ.",
                error_msg="Химийн бодис шинэчлэхэд алдаа гарлаа"
            ):
                return redirect(url_for("chemicals.chemical_detail", id=id))

        except ValueError as e:
            db.session.rollback()
            flash(_l("Буруу утга: %(value)s") % {"value": e}, "danger")
        except SQLAlchemyError as e:
            db.session.rollback()
            current_app.logger.error(f"Error editing chemical: {e}")
            flash(_l("Алдаа: %(error)s") % {"error": str(e)[:100]}, "danger")

    return render_template(
        "chemicals/chemical_form.html",
        chemical=chemical,
        mode="edit",
        categories=CATEGORIES,
        status_types=STATUS_TYPES,
        units=UNITS,
        lab_types=LAB_TYPES,
    )


# -------------------------------------------------
# 5. Нөөц нэмэх (Receive)
# -------------------------------------------------

@chemicals_bp.route("/receive/<int:id>", methods=["POST"])
@login_required
@role_required(UserRole.CHEMIST.value, UserRole.SENIOR.value, UserRole.MANAGER.value, UserRole.ADMIN.value)
def receive_chemical(id):
    """Химийн бодисын нөөц нэмэх."""
    chemical = ChemicalRepository.get_by_id(id)
    if not chemical:
        abort(404)

    try:
        quantity_add = float(request.form.get("quantity_add", 0))

        success, message = receive_stock(
            chemical=chemical,
            quantity_add=quantity_add,
            user_id=current_user.id,
            lot_number=request.form.get("lot_number"),
            expiry_date_str=request.form.get("expiry_date"),
        )

        if not success:
            flash(message, "warning")
            return redirect(url_for("chemicals.chemical_detail", id=id))

        safe_commit(
            success_msg=message,
            error_msg="Нөөц нэмэхэд алдаа гарлаа"
        )

    except (ValueError, TypeError) as e:
        db.session.rollback()
        current_app.logger.error(f"Error receiving chemical: {e}")
        flash(_l("Алдаа: %(error)s") % {"error": str(e)[:100]}, "danger")

    return redirect(url_for("chemicals.chemical_detail", id=id))


# -------------------------------------------------
# 6. Хэрэглээ бүртгэх (Consume)
# -------------------------------------------------

@chemicals_bp.route("/consume/<int:id>", methods=["POST"])
@login_required
def consume_chemical(id):
    """Химийн бодисын хэрэглээ бүртгэх."""
    chemical = ChemicalRepository.get_by_id(id)
    if not chemical:
        abort(404)

    try:
        quantity_used = float(request.form.get("quantity_used", 0))
        purpose = request.form.get("purpose", "")

        # Parse sample_id safely
        sample_id = None
        raw_sample_id = request.form.get("sample_id")
        if raw_sample_id:
            try:
                sample_id = int(raw_sample_id)
            except ValueError:
                pass

        result = consume_chemical_stock(
            chemical=chemical,
            quantity_used=quantity_used,
            user_id=current_user.id,
            purpose=purpose,
            analysis_code=request.form.get("analysis_code"),
            sample_id=sample_id,
        )

        if not result.success:
            flash(result.error, "danger")
            return redirect(url_for("chemicals.chemical_detail", id=id))

        safe_commit(
            success_msg=f"-{quantity_used} {chemical.unit} хэрэглэгдлээ.",
            error_msg="Хэрэглээ бүртгэхэд алдаа гарлаа"
        )

    except (ValueError, TypeError) as e:
        db.session.rollback()
        current_app.logger.error(f"Error consuming chemical: {e}")
        flash(_l("Алдаа: %(error)s") % {"error": str(e)[:100]}, "danger")

    return redirect(url_for("chemicals.chemical_detail", id=id))


# -------------------------------------------------
# 7. Устгах (Dispose)
# -------------------------------------------------

@chemicals_bp.route("/dispose/<int:id>", methods=["POST"])
@login_required
@role_required(UserRole.SENIOR.value, UserRole.MANAGER.value, UserRole.ADMIN.value)
def dispose_chemical(id):
    """Химийн бодис устгах."""
    chemical = ChemicalRepository.get_by_id(id)
    if not chemical:
        abort(404)

    try:
        reason = request.form.get("reason", "Устгав")
        svc_dispose_chemical(chemical, user_id=current_user.id, reason=reason)

        safe_commit(
            success_msg=f"'{chemical.name}' устгагдлаа.",
            error_msg="Устгахад алдаа гарлаа"
        )

    except SQLAlchemyError as e:
        db.session.rollback()
        current_app.logger.error(f"Error disposing chemical: {e}")
        flash(_l("Алдаа: %(error)s") % {"error": str(e)[:100]}, "danger")

    return redirect(url_for("chemicals.chemical_list"))


# -------------------------------------------------
# 8. Журнал харах
# -------------------------------------------------

@chemicals_bp.route("/journal")
@login_required
def chemical_journal():
    """Химийн бодисын журнал (бүх хэрэглээ)."""
    lab = request.args.get("lab", "all")
    start_date = request.args.get("start_date")
    end_date = request.args.get("end_date")

    rows = get_journal_rows(lab=lab, start_date=start_date, end_date=end_date)

    return render_template(
        "chemicals/chemical_journal.html",
        rows_json=rows,
        lab=lab,
        start_date=start_date,
        end_date=end_date,
        lab_types=LAB_TYPES,
    )
