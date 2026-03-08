# app/routes/chemicals/crud.py
# -*- coding: utf-8 -*-
"""Химийн бодисын үндсэн CRUD үйлдлүүд."""

from datetime import datetime, date, timedelta

from flask import (
    render_template, request, redirect, url_for,
    flash, abort, current_app
)
from flask_login import login_required, current_user
from sqlalchemy.exc import IntegrityError

from app import db
from app.models import Chemical, ChemicalUsage, ChemicalLog
from app.utils.database import safe_commit
from app.utils.datetime import now_local
from app.routes.chemicals import chemicals_bp, LAB_TYPES, CATEGORIES, UNITS, STATUS_TYPES


def log_chemical_action(chemical, action, quantity_change=None,
                        quantity_before=None, quantity_after=None, details=None):
    """Химийн бодисын үйлдлийг бүртгэх (audit log with hash - ISO 17025)."""
    log = ChemicalLog(
        chemical_id=chemical.id,
        user_id=current_user.id,
        action=action,
        quantity_change=quantity_change,
        quantity_before=quantity_before,
        quantity_after=quantity_after,
        details=details
    )
    log.data_hash = log.compute_hash()
    db.session.add(log)


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

    query = Chemical.query

    # Лабаар шүүх
    if lab and lab != "all":
        query = query.filter(
            (Chemical.lab_type == lab) | (Chemical.lab_type == 'all')
        )

    # Категориор шүүх
    if category and category != "all":
        query = query.filter(Chemical.category == category)

    # Статусаар шүүх
    if status and status != "all":
        query = query.filter(Chemical.status == status)

    # Хугацаа дуусах, бага нөөцтэй
    if view == "expiring":
        warning_date = date.today() + timedelta(days=30)
        query = query.filter(
            Chemical.expiry_date <= warning_date,
            Chemical.status != 'disposed'
        )
    elif view == "low_stock":
        query = query.filter(Chemical.status == 'low_stock')

    # Устгагдсан бол харуулахгүй (disposed view-ээс бусад)
    if view != "disposed":
        query = query.filter(Chemical.status != 'disposed')

    chemicals_query = query.order_by(Chemical.name.asc()).all()

    # JSON serializable dict руу хөрвүүлэх
    chemicals = []
    for c in chemicals_query:
        chemicals.append({
            'id': c.id,
            'name': c.name,
            'formula': c.formula,
            'cas_number': c.cas_number,
            'manufacturer': c.manufacturer,
            'supplier': c.supplier,
            'catalog_number': c.catalog_number,
            'lot_number': c.lot_number,
            'grade': c.grade,
            'quantity': c.quantity,
            'unit': c.unit,
            'reorder_level': c.reorder_level,
            'received_date': c.received_date.strftime('%Y-%m-%d') if c.received_date else None,
            'expiry_date': c.expiry_date.strftime('%Y-%m-%d') if c.expiry_date else None,
            'opened_date': c.opened_date.strftime('%Y-%m-%d') if c.opened_date else None,
            'storage_location': c.storage_location,
            'storage_conditions': c.storage_conditions,
            'hazard_class': c.hazard_class,
            'lab_type': c.lab_type,
            'category': c.category,
            'status': c.status,
        })

    # Нөөцийн дүн
    stats = {
        'total': Chemical.query.filter(Chemical.status != 'disposed').count(),
        'low_stock': Chemical.query.filter(Chemical.status == 'low_stock').count(),
        'expired': Chemical.query.filter(Chemical.status == 'expired').count(),
    }

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
    chemical = db.session.get(Chemical, id)
    if not chemical:
        abort(404)

    # Хэрэглээний түүх
    usages = ChemicalUsage.query.filter_by(chemical_id=id)\
        .order_by(ChemicalUsage.used_at.desc()).limit(50).all()

    # Аудит түүх
    logs = ChemicalLog.query.filter_by(chemical_id=id)\
        .order_by(ChemicalLog.timestamp.desc()).limit(50).all()

    return render_template(
        "chemicals/chemical_detail.html",
        chemical=chemical,
        usages=usages,
        logs=logs,
        categories=CATEGORIES,
        status_types=STATUS_TYPES,
        units=UNITS,
        lab_types=LAB_TYPES,
    )


# -------------------------------------------------
# 3. Шинэ нэмэх
# -------------------------------------------------

@chemicals_bp.route("/add", methods=["GET", "POST"])
@login_required
def add_chemical():
    """Шинэ химийн бодис нэмэх."""
    if current_user.role not in ["chemist", "senior", "manager", "admin"]:
        flash("Хандах эрхгүй.", "danger")
        return redirect(url_for("chemicals.chemical_list"))

    if request.method == "POST":
        try:
            # Огноо parse хийх
            received_date = None
            expiry_date = None
            opened_date = None

            if request.form.get("received_date"):
                received_date = datetime.strptime(
                    request.form.get("received_date"), "%Y-%m-%d"
                ).date()
            if request.form.get("expiry_date"):
                expiry_date = datetime.strptime(
                    request.form.get("expiry_date"), "%Y-%m-%d"
                ).date()
            if request.form.get("opened_date"):
                opened_date = datetime.strptime(
                    request.form.get("opened_date"), "%Y-%m-%d"
                ).date()

            quantity = float(request.form.get("quantity", 0) or 0)
            reorder_level = None
            if request.form.get("reorder_level"):
                reorder_level = float(request.form.get("reorder_level"))

            chemical = Chemical(
                name=request.form.get("name"),
                cas_number=request.form.get("cas_number"),
                formula=request.form.get("formula"),
                manufacturer=request.form.get("manufacturer"),
                supplier=request.form.get("supplier"),
                catalog_number=request.form.get("catalog_number"),
                lot_number=request.form.get("lot_number"),
                grade=request.form.get("grade"),
                quantity=quantity,
                unit=request.form.get("unit", "mL"),
                reorder_level=reorder_level,
                received_date=received_date,
                expiry_date=expiry_date,
                opened_date=opened_date,
                storage_location=request.form.get("storage_location"),
                storage_conditions=request.form.get("storage_conditions"),
                hazard_class=request.form.get("hazard_class"),
                lab_type=request.form.get("lab_type", "all"),
                category=request.form.get("category", "other"),
                notes=request.form.get("notes"),
                created_by_id=current_user.id,
            )

            # Төлөв автоматаар тохируулах
            chemical.update_status()

            db.session.add(chemical)
            db.session.flush()  # ID авах

            # Аудит лог
            log_chemical_action(
                chemical, 'created',
                quantity_change=quantity,
                quantity_before=0,
                quantity_after=quantity,
                details=f"Шинээр бүртгэв: {chemical.name}"
            )

            if safe_commit(
                success_msg=f"'{chemical.name}' амжилттай бүртгэгдлээ.",
                error_msg="Химийн бодис бүртгэхэд алдаа гарлаа"
            ):
                return redirect(url_for("chemicals.chemical_detail", id=chemical.id))

        except ValueError as e:
            db.session.rollback()
            flash(f"Буруу утга: {e}", "danger")
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error adding chemical: {e}")
            flash(f"Алдаа гарлаа: {str(e)[:100]}", "danger")

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
def edit_chemical(id):
    """Химийн бодис засварлах."""
    if current_user.role not in ["chemist", "senior", "manager", "admin"]:
        flash("Хандах эрхгүй.", "danger")
        return redirect(url_for("chemicals.chemical_detail", id=id))

    chemical = db.session.get(Chemical, id)
    if not chemical:
        abort(404)

    if request.method == "POST":
        try:
            old_quantity = chemical.quantity

            # Огноо parse
            if request.form.get("received_date"):
                chemical.received_date = datetime.strptime(
                    request.form.get("received_date"), "%Y-%m-%d"
                ).date()
            if request.form.get("expiry_date"):
                chemical.expiry_date = datetime.strptime(
                    request.form.get("expiry_date"), "%Y-%m-%d"
                ).date()
            else:
                chemical.expiry_date = None
            if request.form.get("opened_date"):
                chemical.opened_date = datetime.strptime(
                    request.form.get("opened_date"), "%Y-%m-%d"
                ).date()
            else:
                chemical.opened_date = None

            chemical.name = request.form.get("name")
            chemical.cas_number = request.form.get("cas_number")
            chemical.formula = request.form.get("formula")
            chemical.manufacturer = request.form.get("manufacturer")
            chemical.supplier = request.form.get("supplier")
            chemical.catalog_number = request.form.get("catalog_number")
            chemical.lot_number = request.form.get("lot_number")
            chemical.grade = request.form.get("grade")
            chemical.unit = request.form.get("unit", "mL")

            if request.form.get("reorder_level"):
                chemical.reorder_level = float(request.form.get("reorder_level"))
            else:
                chemical.reorder_level = None

            chemical.storage_location = request.form.get("storage_location")
            chemical.storage_conditions = request.form.get("storage_conditions")
            chemical.hazard_class = request.form.get("hazard_class")
            chemical.lab_type = request.form.get("lab_type", "all")
            chemical.category = request.form.get("category", "other")
            chemical.notes = request.form.get("notes")

            # Тоо хэмжээ өөрчлөгдвөл
            new_quantity = float(request.form.get("quantity", 0) or 0)
            if new_quantity != old_quantity:
                chemical.quantity = new_quantity
                log_chemical_action(
                    chemical, 'adjusted',
                    quantity_change=new_quantity - old_quantity,
                    quantity_before=old_quantity,
                    quantity_after=new_quantity,
                    details="Тоо хэмжээ засварлав"
                )

            chemical.update_status()

            # Ерөнхий засварын лог
            log_chemical_action(
                chemical, 'updated',
                details="Мэдээлэл шинэчлэв"
            )

            if safe_commit(
                success_msg="Амжилттай шинэчлэгдлээ.",
                error_msg="Химийн бодис шинэчлэхэд алдаа гарлаа"
            ):
                return redirect(url_for("chemicals.chemical_detail", id=id))

        except ValueError as e:
            db.session.rollback()
            flash(f"Буруу утга: {e}", "danger")
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error editing chemical: {e}")
            flash(f"Алдаа: {str(e)[:100]}", "danger")

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
def receive_chemical(id):
    """Химийн бодисын нөөц нэмэх."""
    if current_user.role not in ["chemist", "senior", "manager", "admin"]:
        flash("Хандах эрхгүй.", "danger")
        return redirect(url_for("chemicals.chemical_detail", id=id))

    chemical = db.session.get(Chemical, id)
    if not chemical:
        abort(404)

    try:
        quantity_add = float(request.form.get("quantity_add", 0))
        if quantity_add <= 0:
            flash("Тоо хэмжээ эерэг тоо байх ёстой.", "warning")
            return redirect(url_for("chemicals.chemical_detail", id=id))

        old_quantity = chemical.quantity
        chemical.quantity += quantity_add
        new_quantity = chemical.quantity

        # Lot number шинэчлэх (шинэ багц)
        if request.form.get("lot_number"):
            chemical.lot_number = request.form.get("lot_number")
        if request.form.get("expiry_date"):
            chemical.expiry_date = datetime.strptime(
                request.form.get("expiry_date"), "%Y-%m-%d"
            ).date()

        chemical.received_date = date.today()
        chemical.update_status()

        log_chemical_action(
            chemical, 'received',
            quantity_change=quantity_add,
            quantity_before=old_quantity,
            quantity_after=new_quantity,
            details=f"Нөөц нэмэв: +{quantity_add} {chemical.unit}"
        )

        safe_commit(
            success_msg=f"+{quantity_add} {chemical.unit} нэмэгдлээ.",
            error_msg="Нөөц нэмэхэд алдаа гарлаа"
        )

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error receiving chemical: {e}")
        flash(f"Алдаа: {str(e)[:100]}", "danger")

    return redirect(url_for("chemicals.chemical_detail", id=id))


# -------------------------------------------------
# 6. Хэрэглээ бүртгэх (Consume)
# -------------------------------------------------

@chemicals_bp.route("/consume/<int:id>", methods=["POST"])
@login_required
def consume_chemical(id):
    """Химийн бодисын хэрэглээ бүртгэх."""
    chemical = db.session.get(Chemical, id)
    if not chemical:
        abort(404)

    try:
        quantity_used = float(request.form.get("quantity_used", 0))
        if quantity_used <= 0:
            flash("Тоо хэмжээ эерэг тоо байх ёстой.", "warning")
            return redirect(url_for("chemicals.chemical_detail", id=id))

        if quantity_used > chemical.quantity:
            flash(f"Хэрэглээний хэмжээ ({quantity_used}) нөөцийн хэмжээнээс ({chemical.quantity}) хэтэрсэн байна.", "danger")
            return redirect(url_for("chemicals.chemical_detail", id=id))

        old_quantity = chemical.quantity
        chemical.quantity -= quantity_used
        new_quantity = chemical.quantity

        # Хэрэглээний бүртгэл
        usage = ChemicalUsage(
            chemical_id=chemical.id,
            quantity_used=quantity_used,
            unit=chemical.unit,
            purpose=request.form.get("purpose"),
            analysis_code=request.form.get("analysis_code"),
            used_by_id=current_user.id,
            quantity_before=old_quantity,
            quantity_after=new_quantity,
        )

        # Sample холбох (optional)
        sample_id = request.form.get("sample_id")
        if sample_id:
            try:
                usage.sample_id = int(sample_id)
            except ValueError:
                pass

        db.session.add(usage)

        # Анх нээсэн огноо
        if not chemical.opened_date:
            chemical.opened_date = date.today()

        chemical.update_status()

        log_chemical_action(
            chemical, 'consumed',
            quantity_change=-quantity_used,
            quantity_before=old_quantity,
            quantity_after=new_quantity,
            details=f"Хэрэглэв: -{quantity_used} {chemical.unit}, {request.form.get('purpose', '')}"
        )

        safe_commit(
            success_msg=f"-{quantity_used} {chemical.unit} хэрэглэгдлээ.",
            error_msg="Хэрэглээ бүртгэхэд алдаа гарлаа"
        )

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error consuming chemical: {e}")
        flash(f"Алдаа: {str(e)[:100]}", "danger")

    return redirect(url_for("chemicals.chemical_detail", id=id))


# -------------------------------------------------
# 7. Устгах (Dispose)
# -------------------------------------------------

@chemicals_bp.route("/dispose/<int:id>", methods=["POST"])
@login_required
def dispose_chemical(id):
    """Химийн бодис устгах."""
    if current_user.role not in ["senior", "manager", "admin"]:
        flash("Хандах эрхгүй.", "danger")
        return redirect(url_for("chemicals.chemical_detail", id=id))

    chemical = db.session.get(Chemical, id)
    if not chemical:
        abort(404)

    try:
        old_quantity = chemical.quantity
        reason = request.form.get("reason", "Устгав")

        chemical.status = 'disposed'
        chemical.quantity = 0

        log_chemical_action(
            chemical, 'disposed',
            quantity_change=-old_quantity,
            quantity_before=old_quantity,
            quantity_after=0,
            details=f"Устгав: {reason}"
        )

        safe_commit(
            success_msg=f"'{chemical.name}' устгагдлаа.",
            error_msg="Устгахад алдаа гарлаа"
        )

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error disposing chemical: {e}")
        flash(f"Алдаа: {str(e)[:100]}", "danger")

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

    query = db.session.query(ChemicalUsage, Chemical).join(Chemical)

    if lab and lab != "all":
        query = query.filter(
            (Chemical.lab_type == lab) | (Chemical.lab_type == 'all')
        )

    if start_date:
        start_dt = datetime.strptime(start_date, "%Y-%m-%d")
        query = query.filter(ChemicalUsage.used_at >= start_dt)

    if end_date:
        end_dt = datetime.strptime(end_date, "%Y-%m-%d")
        end_dt = end_dt.replace(hour=23, minute=59, second=59)
        query = query.filter(ChemicalUsage.used_at <= end_dt)

    usages = query.order_by(ChemicalUsage.used_at.desc()).limit(500).all()

    rows = []
    for usage, chemical in usages:
        rows.append({
            "date": usage.used_at.strftime("%Y-%m-%d %H:%M") if usage.used_at else "",
            "chemical": chemical.name,
            "chemical_id": chemical.id,
            "formula": chemical.formula or "",
            "quantity": f"-{usage.quantity_used} {usage.unit or chemical.unit}",
            "purpose": usage.purpose or "",
            "analysis": usage.analysis_code or "",
            "user": usage.used_by.username if usage.used_by else "",
            "before": round(usage.quantity_before, 2) if usage.quantity_before else None,
            "after": round(usage.quantity_after, 2) if usage.quantity_after else None,
        })

    return render_template(
        "chemicals/chemical_journal.html",
        rows_json=rows,
        lab=lab,
        start_date=start_date,
        end_date=end_date,
        lab_types=LAB_TYPES,
    )
