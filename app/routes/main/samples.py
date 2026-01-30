# app/routes/main/samples.py
# -*- coding: utf-8 -*-
"""
Дээж засах/устгах (Sample management) routes
"""

from flask import render_template, flash, redirect, url_for, request
from flask_login import login_required, current_user
from app import db
import json
from datetime import date, timedelta
from app.utils.audit import log_audit


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

        can_edit = current_user.role in ["admin", "senior"] or (
            current_user.role == "prep" and sample.status == "new"
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
            new_code = request.form.get("sample_code", "").strip().upper()  # ✅ Том үсэг болгох
            selected_analyses = request.form.getlist("analyses")

            original_code = sample.sample_code
            code_changed = new_code and new_code.upper() != (original_code or "").upper()
            analyses_changed = set(selected_analyses) != set(current_analyses)

            if not new_code:
                flash("Дээжний код хоосон байх боломжгүй.", "danger")
            # ✅ Case-insensitive давхардал шалгах
            elif code_changed and Sample.query.filter(
                db.func.upper(Sample.sample_code) == new_code.upper(),
                Sample.id != sample_id
            ).first():
                flash(f'АЛДАА: "{new_code}" нэртэй дээж аль хэдийн бүртгэлтэй тул солих боломжгүй.', "danger")
            else:
                try:
                    if code_changed:
                        sample.sample_code = new_code  # Model-д @validates автоматаар uppercase болгоно
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

        if current_user.role not in ["admin", "senior"]:
            flash("Сонгосон дээжийг устгах эрх танд байхгүй.", "danger")
            return redirect(url_for("main.index"))

        deleted_count = 0
        failed_samples = []
        for sample_id_str in sample_ids_to_delete:
            try:
                sample_id = int(sample_id_str)
                sample_to_delete = Sample.query.get(sample_id)
                if sample_to_delete:
                    if current_user.role == "senior" and sample_to_delete.status != "new":
                        failed_samples.append(f"{sample_to_delete.sample_code} (Боловсруулалтад орсон)")
                        continue
                    # Audit log before deletion
                    log_audit(
                        action='sample_deleted',
                        resource_type='Sample',
                        resource_id=sample_to_delete.id,
                        details={
                            'sample_code': sample_to_delete.sample_code,
                            'client_name': sample_to_delete.client_name
                        }
                    )
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

    # =====================================================================
    # 3. ДЭЭЖ ХАДГАЛАЛТ & УСТГАЛ (Sample Retention & Disposal)
    # =====================================================================
    @bp.route("/sample_disposal")
    @login_required
    def sample_disposal():
        """Дээж хадгалалт ба устгалын удирдлага - Бүгдэд харагдана"""
        from app.models import Sample

        today = date.today()
        warning_days = 30  # 30 хоногийн өмнө анхааруулга

        # Хугацаа дууссан дээжүүд (retention_date < today, disposal_date = None)
        expired_samples = Sample.query.filter(
            Sample.retention_date < today,
            Sample.disposal_date is None
        ).order_by(Sample.retention_date.asc()).all()

        # Удахгүй дуусах дээжүүд (retention_date <= today + 30 days)
        warning_date = today + timedelta(days=warning_days)
        upcoming_samples = Sample.query.filter(
            Sample.retention_date >= today,
            Sample.retention_date <= warning_date,
            Sample.disposal_date is None
        ).order_by(Sample.retention_date.asc()).all()

        # Устгагдсан дээжүүд (сүүлийн 90 хоног)
        disposed_since = today - timedelta(days=90)
        disposed_samples = Sample.query.filter(
            Sample.disposal_date >= disposed_since
        ).order_by(Sample.disposal_date.desc()).limit(100).all()

        # Хадгалах хугацаа тодорхойгүй дээжүүд (бүх статус)
        no_retention_samples = Sample.query.filter(
            Sample.retention_date.is_(None),
            Sample.disposal_date.is_(None),
            Sample.return_sample.is_(False)
        ).order_by(Sample.received_date.desc()).limit(100).all()

        # Буцаах дээжүүд (return_sample=True, шинжилгээ дууссан)
        return_samples = Sample.query.filter(
            Sample.return_sample.is_(True),
            Sample.disposal_date.is_(None),
            Sample.status == 'completed'
        ).order_by(Sample.received_date.desc()).all()

        return render_template(
            "sample_disposal.html",
            title="Дээж хадгалалт & устгал",
            expired_samples=expired_samples,
            upcoming_samples=upcoming_samples,
            disposed_samples=disposed_samples,
            no_retention_samples=no_retention_samples,
            return_samples=return_samples,
            today=today,
            warning_days=warning_days
        )

    @bp.route("/dispose_samples", methods=["POST"])
    @login_required
    def dispose_samples():
        """Дээжүүдийг устгасанд тооцох (Bulk disposal)"""
        from app.models import Sample

        if current_user.role not in ["admin", "senior"]:
            flash("Энэ үйлдлийг хийх эрх байхгүй.", "danger")
            return redirect(url_for("main.sample_disposal"))

        sample_ids = request.form.getlist("sample_ids")
        disposal_method = request.form.get("disposal_method", "").strip()

        if not sample_ids:
            flash("Устгах дээж сонгоогүй байна.", "warning")
            return redirect(url_for("main.sample_disposal"))

        if not disposal_method:
            flash("Устгасан арга оруулна уу.", "warning")
            return redirect(url_for("main.sample_disposal"))

        disposed_count = 0
        today = date.today()

        for sid in sample_ids:
            try:
                sample = Sample.query.get(int(sid))
                if sample and Sample.disposal_date is None:
                    sample.disposal_date = today
                    sample.disposal_method = disposal_method

                    log_audit(
                        action='sample_disposed',
                        resource_type='Sample',
                        resource_id=sample.id,
                        details={
                            'sample_code': sample.sample_code,
                            'disposal_method': disposal_method
                        }
                    )
                    disposed_count += 1
            except (ValueError, Exception):
                continue

        if disposed_count > 0:
            try:
                db.session.commit()
                flash(f"{disposed_count} дээж амжилттай устгагдсанд тооцогдлоо.", "success")
            except Exception as e:
                db.session.rollback()
                flash(f"Алдаа: {str(e)[:100]}", "danger")

        return redirect(url_for("main.sample_disposal"))

    @bp.route("/set_retention_date", methods=["POST"])
    @login_required
    def set_retention_date():
        """Дээжийн хадгалах хугацаа тохируулах"""
        from app.models import Sample

        if current_user.role not in ["admin", "senior"]:
            flash("Энэ үйлдлийг хийх эрх байхгүй.", "danger")
            return redirect(url_for("main.sample_disposal"))

        sample_ids = request.form.getlist("sample_ids")
        retention_days = request.form.get("retention_days", "90")

        if not sample_ids:
            flash("Дээж сонгоогүй байна.", "warning")
            return redirect(url_for("main.sample_disposal"))

        try:
            days = int(retention_days)
            if days < 1 or days > 3650:
                raise ValueError("Хугацаа 1-3650 хоногийн хооронд байх ёстой")
        except ValueError as e:
            flash(f"Буруу хугацаа: {e}", "danger")
            return redirect(url_for("main.sample_disposal"))

        updated_count = 0
        retention_date = date.today() + timedelta(days=days)

        for sid in sample_ids:
            try:
                sample = Sample.query.get(int(sid))
                if sample:
                    sample.retention_date = retention_date
                    updated_count += 1
            except (ValueError, Exception):
                continue

        if updated_count > 0:
            try:
                db.session.commit()
                flash(f"{updated_count} дээжийн хадгалах хугацаа {retention_date} болгож тохируулагдлаа.", "success")
            except Exception as e:
                db.session.rollback()
                flash(f"Алдаа: {str(e)[:100]}", "danger")

        return redirect(url_for("main.sample_disposal"))

    @bp.route("/bulk_set_retention", methods=["POST"])
    @login_required
    def bulk_set_retention():
        """Бүх хугацаагүй дээжид retention тохируулах"""
        from app.models import Sample

        retention_days = request.form.get("retention_days", type=int)
        from_date_type = request.form.get("from_date", "received")

        if not retention_days:
            flash("Хугацаа сонгоно уу.", "warning")
            return redirect(url_for("main.sample_disposal"))

        # Хугацаагүй бүх дээжийг олох
        samples = Sample.query.filter(
            Sample.retention_date is None,
            Sample.disposal_date is None
        ).all()

        if not samples:
            flash("Хугацаа тодорхойгүй дээж байхгүй.", "info")
            return redirect(url_for("main.sample_disposal"))

        today = date.today()
        updated_count = 0

        try:
            for s in samples:
                if from_date_type == "received" and s.received_date:
                    base_date = s.received_date
                else:
                    base_date = today

                s.retention_date = base_date + timedelta(days=retention_days)
                updated_count += 1

            db.session.commit()
            flash(f"{updated_count} дээжид хадгалах хугацаа тохируулагдлаа.", "success")
        except Exception as e:
            db.session.rollback()
            flash(f"Алдаа: {str(e)[:100]}", "danger")

        return redirect(url_for("main.sample_disposal"))

    # =====================================================================
    # 5. ANALYTICS DASHBOARD
    # =====================================================================
    @bp.route("/analytics")
    @login_required
    def analytics_dashboard():
        """Шинжилгээний статистик дашбоард"""
        return render_template(
            "analytics_dashboard.html",
            title="Шинжилгээний статистик"
        )
