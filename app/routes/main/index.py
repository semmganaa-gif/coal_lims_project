# app/routes/main/index.py
# -*- coding: utf-8 -*-
"""
Нүүр хуудас - Дээж бүртгэх (Index/Registration) routes
"""

# 1. Standard Library Imports (Python-ы үндсэн сангууд)
from datetime import timedelta

# 2. Third-Party Imports (Гараас суулгасан сангууд)
from flask import render_template, flash, redirect, url_for, request, jsonify, current_app
from flask_login import login_required, current_user

# 3. Local Application Imports (Таны төслийн файлууд)
from sqlalchemy.exc import SQLAlchemyError

from app import db
from app.models import Sample
from app.forms import AddSampleForm

# Current Blueprint & Local Helpers
from .helpers import get_12h_shift_code

# Utils
from app.utils.datetime import now_local
from app.utils.analysis_assignment import assign_analyses_to_sample


from app.utils.sorting import custom_sample_sort_key
from app.utils.database import safe_commit
from app.utils.audit import log_audit
from app.utils.settings import get_sample_type_choices_map, get_unit_abbreviations

# Monitoring
from app.monitoring import track_sample

# Constants
from app.constants import (
    ALL_12H_SAMPLES,
    CONSTANT_12H_SAMPLES,
    COM_PRIMARY_PRODUCTS,
    COM_SECONDARY_MAP,
    WTL_SAMPLE_NAMES_19,
    WTL_SAMPLE_NAMES_70,
    WTL_SAMPLE_NAMES_6,
    WTL_SAMPLE_NAMES_2,
    WTL_SIZE_NAMES,
    WTL_FL_NAMES,
)


def register_routes(bp):
    """Route-уудыг өгөгдсөн blueprint дээр бүртгэх"""

    # =====================================================================
    # 0. ЛАБ СОНГОГЧ (НҮҮР ХУУДАС)
    # =====================================================================
    @bp.route("/")
    @bp.route("/labs")
    @login_required
    def lab_selector():
        """Лаборатори сонгох хуудас."""
        return render_template("lab_selector.html", title="Лаборатори сонгох")

    # =====================================================================
    # 0.5. НҮҮРСНИЙ ЛАБ — НҮҮР ХУУДАС (HUB)
    # =====================================================================
    @bp.route("/coal/hub")
    @login_required
    def coal_hub():
        """Нүүрсний лабораторийн dashboard."""
        total_samples = Sample.query.filter_by(lab_type='coal').count()
        new_samples = Sample.query.filter(
            Sample.lab_type == 'coal',
            Sample.status == 'new'
        ).count()
        in_progress = Sample.query.filter(
            Sample.lab_type == 'coal',
            Sample.status.in_(['in_progress', 'analysis'])
        ).count()
        completed = Sample.query.filter(
            Sample.lab_type == 'coal',
            Sample.status == 'completed'
        ).count()
        return render_template(
            'coal_hub.html',
            title='Нүүрсний лаборатори',
            total_samples=total_samples,
            new_samples=new_samples,
            in_progress=in_progress,
            completed=completed,
        )

    # =====================================================================
    # 1. НҮҮРСНИЙ ЛАБ / ДЭЭЖ БҮРТГЭХ
    # =====================================================================
    @bp.route("/coal", methods=["GET", "POST"])
    @bp.route("/index", methods=["GET", "POST"])
    @login_required
    def index():
        """
        - Зүүн тал: жагсаалт (DataTables)
        - Баруун тал: 'Шинэ дээж бүртгэх' form
        """
        from app.models import Sample

        form = AddSampleForm()
        sample_type_choices_map = get_sample_type_choices_map()  # ✅ DB

        # client_name choices
        form.client_name.choices = [
            ("CHPP", "CHPP"),
            ("UHG-Geo", "UHG-Geo"),
            ("BN-Geo", "BN-Geo"),
            ("QC", "QC"),
            ("Proc", "Proc"),
            ("WTL", "WTL"),
            ("LAB", "LAB"),
        ]

        # ---------- Dynamic sample_type + validators ----------
        if request.method == "POST":
            selected_client = request.form.get("client_name")
            form.sample_type.choices = [
                (v, v) for v in sample_type_choices_map.get(selected_client, [])
            ]
            if selected_client == "WTL" and request.form.get("sample_type") in ["MG", "Test"]:
                from wtforms.validators import DataRequired
                form.sample_code.validators = [DataRequired(message="Sample name заавал оруулна уу.")]
            else:
                from wtforms.validators import Optional
                form.sample_code.validators = [Optional()]
        else:
            form.sample_type.choices = []

        # ---------- Үндсэн submit ----------
        if form.validate_on_submit():
            if current_user.role not in ["prep", "admin"]:
                flash("Дээж бүртгэх эрхгүй байна.", "danger")
                return redirect(url_for("main.index"))

            raw_submitted_codes = request.form.getlist("sample_codes")
            list_type = request.form.get("list_type")  # chpp_2h / chpp_4h / ...
            client_name = form.client_name.data
            sample_type = form.sample_type.data
            sample_date_obj = form.sample_date.data

            successful_samples, failed_samples = [], []
            count = 0

            # --- 1) ОЛОН ДЭЭЖ БҮРТГЭХ (CHPP, UHG/BN/QC/Proc/LAB(simple)) ---
            if raw_submitted_codes and list_type:
                requires_weight = (
                    list_type == "chpp_2h"
                    or list_type == "multi_gen"
                    or list_type == "chpp_com"
                )

                # Жингийн мэдээллийг Map болгож авна (Code -> Weight)
                raw_weights = request.form.getlist("weights") if requires_weight else []
                code_weight_map = {}
                for idx, c in enumerate(raw_submitted_codes):
                    w = raw_weights[idx] if idx < len(raw_weights) else None
                    code_weight_map[c] = w

                # ✅ ЛОГИК ЗАСВАР: Ирсэн кодуудыг "Хатуу дүрмээр" эрэмбэлнэ.
                sorted_codes = sorted(raw_submitted_codes, key=custom_sample_sort_key)

                # ✅ Бүх үйлдлийг нэг transaction-д багтаана (atomicity)
                try:
                    for code in sorted_codes:
                        if not code:
                            continue

                        # Жин шалгах
                        weight, is_valid = None, True
                        if requires_weight:
                            weight_str = code_weight_map.get(code)
                            if weight_str:
                                try:
                                    weight = float(weight_str)
                                    # Жингийн утгын хязгаар шалгах
                                    from app.constants import MIN_SAMPLE_WEIGHT, MAX_SAMPLE_WEIGHT
                                    if weight <= MIN_SAMPLE_WEIGHT:
                                        failed_samples.append(f'{code} (жин хэт бага байна: {weight}г)')
                                        is_valid = False
                                    elif weight > MAX_SAMPLE_WEIGHT:
                                        failed_samples.append(
                                            f'{code} (жин хэт том байна: {weight}г, '
                                            f'max {MAX_SAMPLE_WEIGHT}г)'
                                        )
                                        is_valid = False
                                except ValueError:
                                    failed_samples.append(f'{code} (жин: "{weight_str}" буруу)')
                                    is_valid = False
                            else:
                                failed_samples.append(f"{code} (жин оруулаагүй)")
                                is_valid = False

                        if not is_valid:
                            continue

                        # Дээж үүсгэх
                        sample = Sample(
                            sample_code=code,
                            weight=weight,
                            user_id=current_user.id,
                            client_name=client_name,
                            sample_type=sample_type,
                            sample_condition=form.sample_condition.data,
                            sample_date=sample_date_obj,
                            return_sample=form.return_sample.data,
                            retention_date=(now_local() + timedelta(days=int(form.retention_period.data or 7))).date(),
                            delivered_by=form.delivered_by.data,
                            prepared_date=form.prepared_date.data,
                            prepared_by=form.prepared_by.data,
                            notes=form.notes.data,
                            location=form.location.data if list_type == "multi_gen" else None,
                            product=(
                                form.product.data
                                if list_type == "multi_gen" and client_name in ("QC", "Proc")
                                else None
                            ),
                            hourly_system=list_type.replace("chpp_", "") if "chpp" in list_type else None,
                            analyses_to_perform="[]"
                        )

                        # PE дээжид lab_type='petrography' оноох
                        if sample_type == 'PE':
                            sample.lab_type = 'petrography'

                        # Шинжилгээ оноох
                        # ✅ no_autoflush: Query хийхэд sample-г flush хийхгүй байх
                        with db.session.no_autoflush:
                            assign_analyses_to_sample(sample)

                        db.session.add(sample)
                        successful_samples.append(code)
                        count += 1

                except (SQLAlchemyError, ValueError, TypeError) as e:
                    # Loop-н дундаас алдаа гарвал бүх partial changes-ийг rollback хийнэ
                    db.session.rollback()
                    current_app.logger.error(f"Error during sample registration loop: {e}")
                    flash("Дээж бүртгэхэд алдаа гарлаа.", "danger")
                    # Continue to render template with errors below

                # ✅ Сайжруулсан error handling - давхардлыг арилгасан
                if count > 0:
                    if not safe_commit(
                        f"{count} ш дээж амжилттай бүртгэгдлээ.",
                        "БҮРТГЭЛ АМЖИЛТГҮЙ: Дээжний код давхардсан байна."
                    ):
                        # ✅ Бүх template variable дамжуулах
                        return render_template(
                            "index.html",
                            title="Нүүр хуудас",
                            form=form,
                            active_tab="add-pane",
                            sample_type_map=get_sample_type_choices_map(),
                            all_12h_samples=ALL_12H_SAMPLES,
                            constant_12h_samples=CONSTANT_12H_SAMPLES,
                            com_primary_products=COM_PRIMARY_PRODUCTS,
                            com_secondary_map=COM_SECONDARY_MAP,
                            unit_abbreviations=get_unit_abbreviations(),
                        )

                if failed_samples:
                    flash(f'Анхааруулга: Дараах дээжүүд бүртгэгдсэнгүй: {", ".join(failed_samples)}', "warning")

                # Audit: Дээж бүртгэлийн лог
                for code in successful_samples:
                    log_audit(
                        action='sample_created',
                        resource_type='Sample',
                        details={
                            'sample_code': code,
                            'client_name': client_name,
                            'sample_type': sample_type,
                        }
                    )

                # ✅ Prometheus metrics: Дээж бүртгэлийг track хийх
                for _ in range(count):
                    track_sample(client=client_name, sample_type=sample_type)

                return redirect(url_for("main.index", active_tab="add-pane"))

            # --- 2) WTL (WTL/Size/FL) – автоматаар олон нэр үүсгэх ---
            elif not list_type and client_name == "WTL" and sample_type in ["WTL", "Size", "FL"]:
                lab_number = form.lab_number.data
                if not lab_number:
                    flash("WTL-д лабораторийн дугаар шаардлагатай.", "danger")
                else:
                    all_wtl_names = []
                    if sample_type == "WTL":
                        all_wtl_names = (
                            WTL_SAMPLE_NAMES_19 + WTL_SAMPLE_NAMES_70 +
                            WTL_SAMPLE_NAMES_6 + WTL_SAMPLE_NAMES_2
                        )
                    elif sample_type == "Size":
                        all_wtl_names = WTL_SIZE_NAMES
                    elif sample_type == "FL":
                        all_wtl_names = WTL_FL_NAMES

                    count = 0
                    # ✅ try блокийг устгасан - safe_commit ашиглаж байгаа учир
                    for name in all_wtl_names:
                        final_sample_code = f"{lab_number}_{name}"

                        sample = Sample(
                            client_name=client_name,
                            sample_code=final_sample_code,
                            user_id=current_user.id,
                            sample_type=sample_type,
                            sample_condition=form.sample_condition.data,
                            sample_date=sample_date_obj,
                            return_sample=form.return_sample.data,
                            retention_date=(now_local() + timedelta(days=int(form.retention_period.data or 7))).date(),
                            delivered_by=form.delivered_by.data,
                            prepared_date=form.prepared_date.data,
                            prepared_by=form.prepared_by.data,
                            notes=form.notes.data,
                            weight=None,
                            analyses_to_perform="[]"
                        )

                        # ✅ no_autoflush: Query хийхэд sample-г flush хийхгүй байх
                        with db.session.no_autoflush:
                            assign_analyses_to_sample(sample)
                        db.session.add(sample)
                        count += 1

                    # ✅ Сайжруулсан error handling
                    if count > 0:
                        if not safe_commit(
                            f"{count} ш {sample_type} дээж амжилттай бүртгэгдлээ.",
                            "БҮРТГЭЛ АМЖИЛТГҮЙ: Дээжний код давхардсан байна."
                        ):
                            return render_template(
                                "index.html",
                                title="Нүүр хуудас",
                                form=form,
                                active_tab="add-pane",
                                sample_type_map=get_sample_type_choices_map(),
                                all_12h_samples=ALL_12H_SAMPLES,
                                constant_12h_samples=CONSTANT_12H_SAMPLES,
                                com_primary_products=COM_PRIMARY_PRODUCTS,
                                com_secondary_map=COM_SECONDARY_MAP,
                                unit_abbreviations=get_unit_abbreviations(),
                            )
                        # Audit: WTL дээж бүртгэл
                        for name in all_wtl_names:
                            log_audit(
                                action='sample_created',
                                resource_type='Sample',
                                details={
                                    'sample_code': f"{lab_number}_{name}",
                                    'client_name': client_name,
                                    'sample_type': sample_type,
                                    'lab_type': 'water',
                                }
                            )

                    return redirect(url_for("main.index", active_tab="add-pane"))

            # --- 3) LAB — автоматаар нэр үүсгэх ---
            elif not list_type and client_name == "LAB":
                formatted_date = sample_date_obj.strftime("%Y%m%d")
                shift_code = get_12h_shift_code(now_local())

                if sample_type == "CM":
                    # Идэвхтэй CM стандартын нэрийг авах
                    from app.repositories import ControlStandardRepository
                    active_cm = ControlStandardRepository.get_active()
                    cm_name = active_cm.name if active_cm else "CM"
                    # CM стандарт нэр аль хэдийн улирал агуулсан (жнь: CM-2025-Q4)
                    # Тиймээс quarter_code нэмэхгүй - давхардахаас сэргийлж
                    final_sample_code = f"{cm_name}_{formatted_date}{shift_code}"
                elif sample_type == "GBW":
                    # Идэвхтэй GBW стандартын нэрийг авах
                    from app.repositories import GbwStandardRepository
                    active_gbw = GbwStandardRepository.get_active()
                    gbw_name = active_gbw.name if active_gbw else "GBW"
                    final_sample_code = f"{gbw_name}_{formatted_date}{shift_code}"
                elif sample_type == "Test":
                    final_sample_code = f"Test_{formatted_date}{shift_code}"
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
                    analyses_to_perform="[]"
                )

                # ✅ no_autoflush: Query хийхэд sample-г flush хийхгүй байх
                with db.session.no_autoflush:
                    assign_analyses_to_sample(sample)
                db.session.add(sample)
                # ✅ Сайжруулсан error handling
                safe_commit(
                    f"Дээж амжилттай бүртгэгдлээ. {final_sample_code}",
                    f'БҮРТГЭЛ АМЖИЛТГҮЙ: "{final_sample_code}" дээж аль хэдийн бүртгэгдсэн байна.'
                )
                # Audit: LAB дээж бүртгэл
                log_audit(
                    action='sample_created',
                    resource_type='Sample',
                    resource_id=sample.id,
                    details={
                        'sample_code': final_sample_code,
                        'client_name': client_name,
                        'sample_type': sample_type,
                    }
                )
                return redirect(url_for("main.index", active_tab="add-pane"))

            # --- 4) WTL – MG (structured) / Test (manual sample_code) ---
            elif not list_type and client_name == "WTL" and sample_type in ["MG", "Test"]:
                if sample_type == "MG":
                    # MG: structured code from module/supplier/vehicle
                    wtl_module = form.wtl_module.data
                    wtl_supplier = (form.wtl_supplier.data or "").strip()
                    wtl_vehicle = (form.wtl_vehicle.data or "").strip()
                    if not wtl_module or not wtl_supplier or not wtl_vehicle:
                        flash("MG-д Module, Supplier, Vehicle талбарууд шаардлагатай.", "danger")
                        return redirect(url_for("main.index", active_tab="add-pane"))
                    formatted_date = sample_date_obj.strftime("%Y%m%d")
                    final_sample_code = f"MG_{wtl_module}_{wtl_supplier}_{formatted_date}_{wtl_vehicle}"
                    notes_data = form.notes.data or ""
                    if wtl_module:
                        notes_data = f"Module: {wtl_module}; {notes_data}".strip("; ")
                else:
                    # Test: manual sample_code
                    if not form.sample_code.data:
                        flash("Энэ WTL төрөлд дээжний нэр шаардлагатай.", "danger")
                        return redirect(url_for("main.index", active_tab="add-pane"))
                    final_sample_code = form.sample_code.data
                    notes_data = form.notes.data

                sample = Sample(
                    client_name=client_name,
                    sample_code=final_sample_code,
                    user_id=current_user.id,
                    sample_type=sample_type,
                    sample_condition=form.sample_condition.data,
                    sample_date=sample_date_obj,
                    return_sample=form.return_sample.data,
                    delivered_by=form.delivered_by.data,
                    prepared_date=form.prepared_date.data,
                    prepared_by=form.prepared_by.data,
                    notes=notes_data,
                    analyses_to_perform="[]"
                )

                # ✅ no_autoflush: Query хийхэд sample-г flush хийхгүй байх
                with db.session.no_autoflush:
                    assign_analyses_to_sample(sample)
                db.session.add(sample)
                # ✅ Сайжруулсан error handling
                safe_commit(
                    "Шинэ дээж амжилттай бүртгэгдлээ.",
                    f'БҮРТГЭЛ АМЖИЛТГҮЙ: "{final_sample_code}" дээж аль хэдийн бүртгэгдсэн байна.'
                )
                # Audit: WTL MG/Test дээж бүртгэл
                log_audit(
                    action='sample_created',
                    resource_type='Sample',
                    resource_id=sample.id,
                    details={
                        'sample_code': final_sample_code,
                        'client_name': client_name,
                        'sample_type': sample_type,
                        'lab_type': 'water',
                    }
                )
                return redirect(url_for("main.index", active_tab="add-pane"))

            else:
                flash("Маягт дутуу эсвэл алдаатай байна.", "danger")

        active_tab = "add-pane" if form.errors else request.args.get("active_tab", "list-pane")

        return render_template(
            "index.html",
            title="Нүүр хуудас",
            form=form,
            active_tab=active_tab,
            sample_type_map=get_sample_type_choices_map(),
            all_12h_samples=ALL_12H_SAMPLES,
            constant_12h_samples=CONSTANT_12H_SAMPLES,
            com_primary_products=COM_PRIMARY_PRODUCTS,
            com_secondary_map=COM_SECONDARY_MAP,
            unit_abbreviations=get_unit_abbreviations(),
        )

    # =====================================================================
    # 2. LIVE PREVIEW (AJAX)
    # =====================================================================
    @bp.route("/preview-analyses", methods=["POST"])
    @login_required
    def preview_sample_analyses():
        """
        Frontend-ээс (JS) дээжний нэр ирэхэд ямар анализ хийгдэхийг урьдчилан харуулна.
        """
        data = request.json
        sample_names = data.get("sample_names", [])
        client_name = data.get("client_name")
        sample_type = data.get("sample_type")

        if not all([sample_names, client_name, sample_type]):
            return jsonify({"error": "Мэдээлэл дутуу байна"}), 400

        results = {}

        # ✅ САЙЖРУУЛСАН: Fake объект үүсгэхгүй, шууд параметр дамжуулах
        for name in sample_names:
            assigned_list = assign_analyses_to_sample(
                client_name=client_name,
                sample_type=sample_type,
                sample_code=name
            )
            results[name] = assigned_list

        return jsonify(results)
