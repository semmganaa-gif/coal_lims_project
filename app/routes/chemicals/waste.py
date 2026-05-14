# app/routes/chemicals/waste.py
# -*- coding: utf-8 -*-
"""Химийн хог хаягдлын бүртгэл."""

import logging
from datetime import datetime

from flask import render_template, request, redirect, url_for, flash, abort, jsonify
from flask_login import login_required, current_user
from flask_babel import lazy_gettext as _l

from sqlalchemy.exc import SQLAlchemyError

from app import db
from app.constants import UserRole
from app.utils.decorators import role_required
from app.utils.datetime import now_local
from app.models import ChemicalWaste, ChemicalWasteRecord
from app.utils.database import safe_commit
from app.routes.chemicals import chemicals_bp

logger = logging.getLogger(__name__)

# Хаягдах арга
DISPOSAL_METHODS = {
    'sewer': 'Бохирын шугамд',
    'evaporate': 'Агаарт ууршина',
    'special': 'Тусгай хаягдлын сав',
    'incinerate': 'Шатаах',
    'recycle': 'Дахин боловсруулах',
    'external': 'Гадны байгууллагад өгөх',
}

# Аюулын төрөл
HAZARD_TYPES = {
    'corrosive': 'Идэмхий',
    'toxic': 'Хортой',
    'flammable': 'Шатамхай',
    'oxidizing': 'Исэлдүүлэгч',
    'irritant': 'Цочроогч',
    'environmental': 'Байгаль орчинд хортой',
}

LAB_TYPES = {
    'all': 'Бүх лаб',
    'coal': 'Нүүрсний лаб',
    'water_chemistry': 'Усны хими',
    'microbiology': 'Микробиологи',
    'petrography': 'Петрограф',
}


# -------------------------------------------------
# 1. Хог хаягдлын жагсаалт
# -------------------------------------------------
@chemicals_bp.route("/waste")
@login_required
def waste_list():
    """Хог хаягдлын жагсаалт."""
    lab = request.args.get("lab", "all")
    year = request.args.get("year", now_local().year, type=int)

    query = ChemicalWaste.query.filter(ChemicalWaste.is_active.is_(True))

    if lab and lab != "all":
        query = query.filter(
            (ChemicalWaste.lab_type == lab) | (ChemicalWaste.lab_type == 'all')
        )

    wastes = query.order_by(ChemicalWaste.name_mn.asc()).all()

    # Сарын бүртгэл татах
    waste_data = []
    for w in wastes:
        records = ChemicalWasteRecord.query.filter_by(
            waste_id=w.id, year=year
        ).all()

        monthly = {r.month: r.quantity for r in records}
        total = sum(monthly.values())

        # Эцсийн үлдэгдэл (12-р сарын эсвэл сүүлийн бүртгэлийн)
        ending = 0
        for r in records:
            if r.ending_balance:
                ending = r.ending_balance

        waste_data.append({
            'waste': w,
            'monthly': monthly,
            'total': total,
            'ending_balance': ending,
        })

    return render_template(
        "chemicals/waste_list.html",
        waste_data=waste_data,
        year=year,
        lab=lab,
        lab_types=LAB_TYPES,
        disposal_methods=DISPOSAL_METHODS,
        hazard_types=HAZARD_TYPES,
    )


# -------------------------------------------------
# 2. Хог хаягдал нэмэх
# -------------------------------------------------
@chemicals_bp.route("/waste/add", methods=["GET", "POST"])
@login_required
@role_required(UserRole.CHEMIST.value, UserRole.SENIOR.value, UserRole.MANAGER.value, UserRole.ADMIN.value)
def add_waste():
    """Шинэ хог хаягдал нэмэх."""
    if request.method == "POST":
        try:
            waste = ChemicalWaste(
                name_mn=request.form.get("name_mn"),
                name_en=request.form.get("name_en"),
                monthly_amount=float(request.form.get("monthly_amount") or 0),
                unit=request.form.get("unit", "л"),
                disposal_method=request.form.get("disposal_method"),
                disposal_location=request.form.get("disposal_location"),
                is_hazardous=request.form.get("is_hazardous") == "on",
                hazard_type=request.form.get("hazard_type"),
                lab_type=request.form.get("lab_type", "all"),
                notes=request.form.get("notes"),
                created_by_id=current_user.id,
            )

            db.session.add(waste)
            if safe_commit(
                success_msg=f"'{waste.name_mn}' амжилттай нэмэгдлээ.",
                error_msg="Хог хаягдал нэмэхэд алдаа гарлаа"
            ):
                return redirect(url_for("chemicals.waste_list"))

        except (ValueError, TypeError) as e:
            db.session.rollback()
            flash(_l("Алдаа: %(error)s") % {"error": str(e)[:100]}, "danger")

    return render_template(
        "chemicals/waste_form.html",
        waste=None,
        mode="add",
        disposal_methods=DISPOSAL_METHODS,
        hazard_types=HAZARD_TYPES,
        lab_types=LAB_TYPES,
    )


# -------------------------------------------------
# 3. Хог хаягдал засах
# -------------------------------------------------
@chemicals_bp.route("/waste/edit/<int:id>", methods=["GET", "POST"])
@login_required
@role_required(UserRole.CHEMIST.value, UserRole.SENIOR.value, UserRole.MANAGER.value, UserRole.ADMIN.value)
def edit_waste(id):
    """Хог хаягдал засах."""
    waste = db.session.get(ChemicalWaste, id)
    if not waste:
        abort(404)

    if request.method == "POST":
        try:
            waste.name_mn = request.form.get("name_mn")
            waste.name_en = request.form.get("name_en")
            waste.monthly_amount = float(request.form.get("monthly_amount") or 0)
            waste.unit = request.form.get("unit", "л")
            waste.disposal_method = request.form.get("disposal_method")
            waste.disposal_location = request.form.get("disposal_location")
            waste.is_hazardous = request.form.get("is_hazardous") == "on"
            waste.hazard_type = request.form.get("hazard_type")
            waste.lab_type = request.form.get("lab_type", "all")
            waste.notes = request.form.get("notes")

            if safe_commit(
                success_msg="Амжилттай шинэчлэгдлээ.",
                error_msg="Хог хаягдал шинэчлэхэд алдаа гарлаа"
            ):
                return redirect(url_for("chemicals.waste_list"))

        except (ValueError, TypeError) as e:
            db.session.rollback()
            flash(_l("Алдаа: %(error)s") % {"error": str(e)[:100]}, "danger")

    return render_template(
        "chemicals/waste_form.html",
        waste=waste,
        mode="edit",
        disposal_methods=DISPOSAL_METHODS,
        hazard_types=HAZARD_TYPES,
        lab_types=LAB_TYPES,
    )


# -------------------------------------------------
# 4. Хог хаягдал устгах
# -------------------------------------------------
@chemicals_bp.route("/waste/delete/<int:id>", methods=["POST"])
@login_required
@role_required(UserRole.SENIOR.value, UserRole.MANAGER.value, UserRole.ADMIN.value)
def delete_waste(id):
    """Хог хаягдал устгах (идэвхгүй болгох)."""
    waste = db.session.get(ChemicalWaste, id)
    if not waste:
        abort(404)
    waste.is_active = False
    safe_commit(
        success_msg=f"'{waste.name_mn}' устгагдлаа.",
        error_msg="Хог хаягдал устгахад алдаа гарлаа"
    )
    return redirect(url_for("chemicals.waste_list"))


# -------------------------------------------------
# 5. Сарын бүртгэл хадгалах (API)
# -------------------------------------------------
@chemicals_bp.route("/waste/api/save_record", methods=["POST"])
@login_required
def save_waste_record():
    """Хог хаягдлын сарын бүртгэл хадгалах."""
    try:
        data = request.get_json()
        waste_id = data.get("waste_id")
        year = data.get("year")
        month = data.get("month")
        quantity = float(data.get("quantity", 0))
        ending_balance = float(data.get("ending_balance", 0)) if data.get("ending_balance") else None

        # Бүртгэл байгаа эсэх шалгах
        record = ChemicalWasteRecord.query.filter_by(
            waste_id=waste_id, year=year, month=month
        ).first()

        if record:
            record.quantity = quantity
            if ending_balance is not None:
                record.ending_balance = ending_balance
            record.recorded_at = now_local()
            record.recorded_by_id = current_user.id
        else:
            record = ChemicalWasteRecord(
                waste_id=waste_id,
                year=year,
                month=month,
                quantity=quantity,
                ending_balance=ending_balance or 0,
                recorded_by_id=current_user.id,
            )
            db.session.add(record)

        try:
            db.session.commit()
        except SQLAlchemyError as e:
            db.session.rollback()
            logger.error(f"Waste record commit error: {e}", exc_info=True)
            return jsonify({"success": False, "error": "Хадгалахад алдаа гарлаа"}), 500

        return jsonify({"success": True, "message": "Хадгалагдлаа"})

    except (ValueError, TypeError) as e:
        db.session.rollback()
        logger.error(f"Waste record save error: {e}", exc_info=True)
        return jsonify({"success": False, "error": "Хадгалахад алдаа гарлаа"}), 500


# -------------------------------------------------
# 6. Тайлан (Excel export-д зориулсан)
# -------------------------------------------------
@chemicals_bp.route("/waste/report")
@login_required
def waste_report():
    """Хог хаягдлын жилийн тайлан."""
    year = request.args.get("year", now_local().year, type=int)
    lab = request.args.get("lab", "all")

    query = ChemicalWaste.query.filter(ChemicalWaste.is_active.is_(True))
    if lab and lab != "all":
        query = query.filter(
            (ChemicalWaste.lab_type == lab) | (ChemicalWaste.lab_type == 'all')
        )

    wastes = query.order_by(ChemicalWaste.name_mn.asc()).all()

    report_data = []
    for w in wastes:
        records = ChemicalWasteRecord.query.filter_by(
            waste_id=w.id, year=year
        ).all()

        monthly = {r.month: {'qty': r.quantity, 'balance': r.ending_balance} for r in records}
        total = sum(r.quantity for r in records)

        report_data.append({
            'name_mn': w.name_mn,
            'name_en': w.name_en,
            'monthly_amount': w.monthly_amount,
            'unit': w.unit,
            'disposal_location': w.disposal_location,
            'monthly': monthly,
            'total': total,
        })

    return render_template(
        "chemicals/waste_report.html",
        report_data=report_data,
        year=year,
        lab=lab,
        lab_types=LAB_TYPES,
    )
