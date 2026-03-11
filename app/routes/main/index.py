# app/routes/main/index.py
# -*- coding: utf-8 -*-
"""
Нүүр хуудас - Дээж бүртгэх (Index/Registration) routes
"""

from flask import render_template, flash, redirect, url_for, request, jsonify
from flask_login import login_required, current_user

from app.models import Sample
from app.forms import AddSampleForm

from app.utils.analysis_assignment import assign_analyses_to_sample
from app.utils.settings import get_sample_type_choices_map, get_unit_abbreviations

from app.constants import (
    ALL_12H_SAMPLES,
    CONSTANT_12H_SAMPLES,
    COM_PRIMARY_PRODUCTS,
    COM_SECONDARY_MAP,
)

from app.services.sample_service import (
    register_batch_samples,
    register_wtl_auto_samples,
    register_lab_sample,
    register_wtl_mg_test,
)


def _index_template_context(form):
    """render_template-д дамжуулах нийтлэг context."""
    return dict(
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


def register_routes(bp):
    """Route-уудыг өгөгдсөн blueprint дээр бүртгэх"""

    # =====================================================================
    # 0. ЛАБ СОНГОГЧ (НҮҮР ХУУДАС)
    # =====================================================================
    @bp.route("/")
    @bp.route("/labs")
    @login_required
    def lab_selector():
        return render_template("lab_selector.html", title="Лаборатори сонгох")

    # =====================================================================
    # 0.5. НҮҮРСНИЙ ЛАБ — НҮҮР ХУУДАС (HUB)
    # =====================================================================
    @bp.route("/coal/hub")
    @login_required
    def coal_hub():
        total_samples = Sample.query.filter_by(lab_type='coal').count()
        new_samples = Sample.query.filter(
            Sample.lab_type == 'coal', Sample.status == 'new'
        ).count()
        in_progress = Sample.query.filter(
            Sample.lab_type == 'coal', Sample.status.in_(['in_progress', 'analysis'])
        ).count()
        completed = Sample.query.filter(
            Sample.lab_type == 'coal', Sample.status == 'completed'
        ).count()
        return render_template(
            'coal_hub.html', title='Нүүрсний лаборатори',
            total_samples=total_samples, new_samples=new_samples,
            in_progress=in_progress, completed=completed,
        )

    # =====================================================================
    # 1. НҮҮРСНИЙ ЛАБ / ДЭЭЖ БҮРТГЭХ
    # =====================================================================
    @bp.route("/coal", methods=["GET", "POST"])
    @bp.route("/index", methods=["GET", "POST"])
    @login_required
    def index():
        form = AddSampleForm()
        sample_type_choices_map = get_sample_type_choices_map()

        form.client_name.choices = [
            ("CHPP", "CHPP"), ("UHG-Geo", "UHG-Geo"), ("BN-Geo", "BN-Geo"),
            ("QC", "QC"), ("Proc", "Proc"), ("WTL", "WTL"), ("LAB", "LAB"),
        ]

        # Dynamic sample_type + validators
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

        # Submit
        if form.validate_on_submit():
            if current_user.role not in ["prep", "admin"]:
                flash("Дээж бүртгэх эрхгүй байна.", "danger")
                return redirect(url_for("main.index"))

            raw_codes = request.form.getlist("sample_codes")
            list_type = request.form.get("list_type")
            client_name = form.client_name.data
            sample_type = form.sample_type.data
            retention_days = int(form.retention_period.data or 7)

            # Common form data
            common = dict(
                user_id=current_user.id,
                sample_condition=form.sample_condition.data,
                sample_date=form.sample_date.data,
                return_sample=form.return_sample.data,
                retention_days=retention_days,
                delivered_by=form.delivered_by.data,
                prepared_date=form.prepared_date.data,
                prepared_by=form.prepared_by.data,
                notes=form.notes.data,
            )

            result = None

            # --- 1) ОЛОН ДЭЭЖ (CHPP, UHG/BN/QC/Proc/LAB multi-gen) ---
            if raw_codes and list_type:
                requires_weight = list_type in ("chpp_2h", "multi_gen", "chpp_com")
                raw_weights = request.form.getlist("weights") if requires_weight else []
                weights_map = {}
                for idx, c in enumerate(raw_codes):
                    weights_map[c] = raw_weights[idx] if idx < len(raw_weights) else None

                result = register_batch_samples(
                    codes=raw_codes,
                    weights_map=weights_map,
                    requires_weight=requires_weight,
                    client_name=client_name,
                    sample_type=sample_type,
                    location=form.location.data,
                    product=form.product.data,
                    list_type=list_type,
                    **common,
                )
                if not result.success and result.error == "DUPLICATE_CODE":
                    return render_template("index.html", **_index_template_context(form))
                if result.failed_codes:
                    flash(f'Анхааруулга: {", ".join(result.failed_codes)}', "warning")

            # --- 2) WTL auto-generate (WTL/Size/FL) ---
            elif not list_type and client_name == "WTL" and sample_type in ["WTL", "Size", "FL"]:
                result = register_wtl_auto_samples(
                    sample_type=sample_type,
                    lab_number=form.lab_number.data,
                    sample_condition=common["sample_condition"],
                    sample_date=common["sample_date"],
                    return_sample=common["return_sample"],
                    retention_days=common["retention_days"],
                    delivered_by=common["delivered_by"],
                    prepared_date=common["prepared_date"],
                    prepared_by=common["prepared_by"],
                    notes=common["notes"],
                    user_id=common["user_id"],
                )
                if not result.success:
                    flash(result.message, "danger")
                    if result.error == "DUPLICATE_CODE":
                        return render_template("index.html", **_index_template_context(form))

            # --- 3) LAB auto-name (CM/GBW/Test) ---
            elif not list_type and client_name == "LAB":
                result = register_lab_sample(
                    sample_type=sample_type,
                    sample_date=common["sample_date"],
                    user_id=common["user_id"],
                    sample_condition=common["sample_condition"],
                    return_sample=common["return_sample"],
                    delivered_by=common["delivered_by"],
                    prepared_date=common["prepared_date"],
                    prepared_by=common["prepared_by"],
                    notes=common["notes"],
                )

            # --- 4) WTL MG / Test ---
            elif not list_type and client_name == "WTL" and sample_type in ["MG", "Test"]:
                result = register_wtl_mg_test(
                    sample_type=sample_type,
                    sample_code=form.sample_code.data,
                    wtl_module=form.wtl_module.data,
                    wtl_supplier=form.wtl_supplier.data,
                    wtl_vehicle=form.wtl_vehicle.data,
                    sample_date=common["sample_date"],
                    **common,
                )
                if not result.success:
                    flash(result.message, "danger")

            else:
                flash("Маягт дутуу эсвэл алдаатай байна.", "danger")

            if result and result.success:
                return redirect(url_for("main.index", active_tab="add-pane"))

        active_tab = "add-pane" if form.errors else request.args.get("active_tab", "list-pane")

        return render_template(
            "index.html",
            **{**_index_template_context(form), "active_tab": active_tab},
        )

    # =====================================================================
    # 2. LIVE PREVIEW (AJAX)
    # =====================================================================
    @bp.route("/preview-analyses", methods=["POST"])
    @login_required
    def preview_sample_analyses():
        data = request.json
        sample_names = data.get("sample_names", [])
        client_name = data.get("client_name")
        sample_type = data.get("sample_type")

        if not all([sample_names, client_name, sample_type]):
            return jsonify({"error": "Мэдээлэл дутуу байна"}), 400

        results = {}
        for name in sample_names:
            assigned_list = assign_analyses_to_sample(
                client_name=client_name, sample_type=sample_type, sample_code=name
            )
            results[name] = assigned_list
        return jsonify(results)
