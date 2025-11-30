# app/routes/main/samples.py
# -*- coding: utf-8 -*-
"""
Дээж засах/устгах (Sample management) routes
"""

from flask import render_template, flash, redirect, url_for, request
from flask_login import login_required, current_user
from app import db
import json


def register_routes(bp):
    """Route-уудыг өгөгдсөн blueprint дээр бүртгэх"""

    # =====================================================================
    # 1. ДЭЭЖ ЗАСАХ
    # =====================================================================
    @bp.route("/edit_sample/<int:sample_id>", methods=["GET", "POST"])
    @login_required
    def edit_sample(sample_id):
        from app.models import Sample, AnalysisType
        sample = Sample.query.get_or_404(sample_id)

        can_edit = current_user.role in ["admin", "ahlah"] or (
            current_user.role == "beltgegch" and sample.status == "new"
        )
        if not can_edit:
            flash("Энэ дээжийг засах эрх танд байхгүй эсвэл дээж аль хэдийн боловсруулалтад орсон байна.", "warning")
            return redirect(url_for("main.index"))

        all_analysis_types = AnalysisType.query.order_by(AnalysisType.order_num).all()

        try:
            current_analyses = json.loads(sample.analyses_to_perform or "[]")
        except json.JSONDecodeError:
            current_analyses = []

        if request.method == "POST":
            new_code = request.form.get("sample_code", "").strip()
            selected_analyses = request.form.getlist("analyses")

            original_code = sample.sample_code
            code_changed = new_code and new_code != original_code
            analyses_changed = set(selected_analyses) != set(current_analyses)

            if not new_code:
                flash("Дээжний код хоосон байх боломжгүй.", "danger")
            elif code_changed and Sample.query.filter(Sample.sample_code == new_code, Sample.id != sample_id).first():
                flash(f'АЛДАА: "{new_code}" нэртэй дээж аль хэдийн бүртгэлтэй тул солих боломжгүй.', "danger")
            else:
                try:
                    if code_changed:
                        sample.sample_code = new_code
                    if analyses_changed:
                        sample.analyses_to_perform = json.dumps(selected_analyses)

                    if code_changed or analyses_changed:
                        db.session.commit()
                        flash("Дээжний мэдээлэл амжилттай шинэчлэгдлээ.", "success")
                    else:
                        flash("Ямар нэгэн өөрчлөлт хийгдээгүй.", "info")
                    return redirect(url_for("main.index"))
                except Exception as e:
                    db.session.rollback()
                    flash(f"Хадгалахад алдаа гарлаа: {e}", "danger")

        return render_template(
            "edit_sample.html",
            title="Дээж засах",
            sample=sample,
            all_analysis_types=all_analysis_types,
            current_analyses=current_analyses,
        )

    # =====================================================================
    # 2. ДЭЭЖ УСТГАХ
    # =====================================================================
    @bp.route("/delete_selected_samples", methods=["POST"])
    @login_required
    def delete_selected_samples():
        from app.models import Sample
        sample_ids_to_delete = request.form.getlist("sample_ids")

        if not sample_ids_to_delete:
            flash("Устгах дээжээ сонгоно уу!", "warning")
            return redirect(url_for("main.index"))

        if current_user.role not in ["admin", "ahlah"]:
            flash("Сонгосон дээжийг устгах эрх танд байхгүй.", "danger")
            return redirect(url_for("main.index"))

        deleted_count = 0
        failed_samples = []
        for sample_id_str in sample_ids_to_delete:
            try:
                sample_id = int(sample_id_str)
                sample_to_delete = Sample.query.get(sample_id)
                if sample_to_delete:
                    if current_user.role == "ahlah" and sample_to_delete.status != "new":
                        failed_samples.append(f"{sample_to_delete.sample_code} (Боловсруулалтад орсон)")
                        continue
                    db.session.delete(sample_to_delete)
                    deleted_count += 1
                else:
                    failed_samples.append(f"ID={sample_id_str} (Олдсонгүй)")
            except Exception as e:
                failed_samples.append(f"ID={sample_id_str} (Алдаа: {e})")

        if deleted_count > 0:
            db.session.commit()
            flash(f"{deleted_count} ш дээж амжилттай устгагдлаа.", "success")
        if failed_samples:
            flash(f'Алдаа: Дараах дээжнүүдийг устгаж чадсангүй: {", ".join(failed_samples)}', "danger")

        return redirect(url_for("main.index"))
