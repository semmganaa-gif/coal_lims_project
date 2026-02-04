# app/routes/chemicals/waste.py
# -*- coding: utf-8 -*-
"""Химийн хог хаягдлын бүртгэл."""

from flask import render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from app import db
from app.models import ChemicalWaste, ChemicalWasteRecord
from datetime import datetime

from app.routes.chemicals import chemicals_bp

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
    'water': 'Усны хими',
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
    year = request.args.get("year", datetime.now().year, type=int)

    query = ChemicalWaste.query.filter(ChemicalWaste.is_active == True)

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
def add_waste():
    """Шинэ хог хаягдал нэмэх."""
    if current_user.role not in ["chemist", "senior", "manager", "admin"]:
        flash("Эрх хүрэхгүй.", "danger")
        return redirect(url_for("chemicals.waste_list"))

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
            db.session.commit()
            flash(f"'{waste.name_mn}' амжилттай нэмэгдлээ.", "success")
            return redirect(url_for("chemicals.waste_list"))

        except Exception as e:
            db.session.rollback()
            flash(f"Алдаа: {str(e)[:100]}", "danger")

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
def edit_waste(id):
    """Хог хаягдал засах."""
    if current_user.role not in ["chemist", "senior", "manager", "admin"]:
        flash("Эрх хүрэхгүй.", "danger")
        return redirect(url_for("chemicals.waste_list"))

    waste = ChemicalWaste.query.get_or_404(id)

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

            db.session.commit()
            flash("Амжилттай шинэчлэгдлээ.", "success")
            return redirect(url_for("chemicals.waste_list"))

        except Exception as e:
            db.session.rollback()
            flash(f"Алдаа: {str(e)[:100]}", "danger")

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
def delete_waste(id):
    """Хог хаягдал устгах (идэвхгүй болгох)."""
    if current_user.role not in ["senior", "manager", "admin"]:
        flash("Эрх хүрэхгүй.", "danger")
        return redirect(url_for("chemicals.waste_list"))

    waste = ChemicalWaste.query.get_or_404(id)
    waste.is_active = False
    db.session.commit()
    flash(f"'{waste.name_mn}' устгагдлаа.", "warning")
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
            record.recorded_at = datetime.now()
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

        db.session.commit()
        return jsonify({"success": True, "message": "Хадгалагдлаа"})

    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "error": str(e)}), 400


# -------------------------------------------------
# 6. Тайлан (Excel export-д зориулсан)
# -------------------------------------------------
@chemicals_bp.route("/waste/report")
@login_required
def waste_report():
    """Хог хаягдлын жилийн тайлан."""
    year = request.args.get("year", datetime.now().year, type=int)
    lab = request.args.get("lab", "all")

    query = ChemicalWaste.query.filter(ChemicalWaste.is_active == True)
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
