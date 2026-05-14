# app/routes/main/samples.py
# -*- coding: utf-8 -*-
"""
Sample management routes (edit/delete/disposal)
"""

import json
import logging
from datetime import date, timedelta

from flask import render_template, flash, redirect, url_for, request, abort, current_app
from flask_login import login_required, current_user
from flask_babel import lazy_gettext as _l

from sqlalchemy.exc import SQLAlchemyError

from app import db
from app.repositories import SampleRepository
from app.schemas import SampleSchema
from app.utils.audit import log_audit
from app.utils.database import safe_commit
from app.services.sample_service import get_retention_context

logger = logging.getLogger(__name__)


def register_routes(bp):
    """Register routes on the given blueprint"""

    # =====================================================================
    # 1. EDIT SAMPLE
    # =====================================================================
    @bp.route("/edit_sample/<int:sample_id>", methods=["GET", "POST"])
    @login_required
    def edit_sample(sample_id):
        from app.models import Sample, AnalysisType
        from app.repositories import AnalysisTypeRepository
        sample = SampleRepository.get_by_id_or_404(sample_id)

        can_edit = current_user.role in ["admin", "senior"] or (
            current_user.role == "prep" and sample.status == "new"
        )
        if not can_edit:
            flash(_l("Энэ дээжийг засах эрхгүй, эсвэл аль хэдийн боловсруулалтанд орсон байна."), "warning")
            return redirect(url_for("main.index"))

        all_analysis_types = AnalysisTypeRepository.get_all_ordered()

        try:
            current_analyses = json.loads(sample.analyses_to_perform or "[]")
        except json.JSONDecodeError:
            current_analyses = []

        if request.method == "POST":
            new_code = request.form.get("sample_code", "").strip().upper()  # Convert to uppercase
            selected_analyses = request.form.getlist("analyses")

            original_code = sample.sample_code
            code_changed = new_code and new_code.upper() != (original_code or "").upper()
            analyses_changed = set(selected_analyses) != set(current_analyses)

            if not new_code:
                flash(_l("Дээжний код хоосон байж болохгүй."), "danger")
            # Case-insensitive duplicate check
            elif code_changed and Sample.query.filter(
                db.func.upper(Sample.sample_code) == new_code.upper(),
                Sample.id != sample_id
            ).first():
                flash(
                    _l('АЛДАА: "%(code)s" кодтой дээж аль хэдийн бүртгэгдсэн байна.') % {'code': new_code},
                    "danger",
                )
            else:
                try:
                    if code_changed:
                        sample.sample_code = new_code  # Model @validates auto-uppercases
                    if analyses_changed:
                        sample.analyses_to_perform = json.dumps(selected_analyses)

                    if code_changed or analyses_changed:
                        db.session.commit()
                        flash(_l("Дээжний мэдээлэл амжилттай шинэчлэгдлээ."), "success")
                    else:
                        flash(_l("Өөрчлөлт хийгдээгүй."), "info")
                    return redirect(url_for("main.index"))
                except SQLAlchemyError as e:
                    db.session.rollback()
                    current_app.logger.error(f"Sample save error: {e}", exc_info=True)
                    flash(_l("Хадгалахад алдаа гарлаа."), "danger")

        return render_template(
            "edit_sample.html",
            title="Edit Sample",
            sample=sample,
            all_analysis_types=all_analysis_types,
            current_analyses=current_analyses,
        )

    # =====================================================================
    # 2. DELETE SAMPLES
    # =====================================================================
    @bp.route("/delete_selected_samples", methods=["POST"])
    @login_required
    def delete_selected_samples():
        from app.models import Sample
        sample_ids_to_delete = request.form.getlist("sample_ids")

        if not sample_ids_to_delete:
            flash(_l("Устгах дээжүүдээ сонгоно уу!"), "warning")
            return redirect(url_for("main.index"))

        if current_user.role not in ["admin", "senior"]:
            flash(_l("Дээж устгах эрхгүй байна."), "danger")
            return redirect(url_for("main.index"))

        deleted_count = 0
        failed_samples = []
        for sample_id_str in sample_ids_to_delete:
            try:
                sample_id = int(sample_id_str)
                sample_to_delete = SampleRepository.get_by_id(sample_id)
                if sample_to_delete:
                    if current_user.role == "senior" and sample_to_delete.status != "new":
                        failed_samples.append(f"{sample_to_delete.sample_code} (Боловсруулалтанд орсон)")
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
            except (ValueError, TypeError) as e:
                failed_samples.append(f"ID={sample_id_str} (Алдаа: {e})")

        if deleted_count > 0:
            try:
                db.session.commit()
                flash(_l("%(count)s дээж амжилттай устгагдлаа.") % {"count": deleted_count}, "success")
            except SQLAlchemyError as e:
                db.session.rollback()
                current_app.logger.error(f"Bulk delete commit error: {e}")
                flash(_l("Устгах үед алдаа гарлаа. Дахин оролдоно уу."), "danger")
        if failed_samples:
            flash(
                _l('Алдаа: Дараах дээжүүд устгагдсангүй: %(samples)s') % {'samples': ", ".join(failed_samples)},
                "danger",
            )

        return redirect(url_for("main.index"))

    # =====================================================================
    # 3. SAMPLE RETENTION & DISPOSAL
    # =====================================================================
    @bp.route("/sample_disposal")
    @login_required
    def sample_disposal():
        """Sample retention and disposal management - Visible to all"""
        return render_template(
            "sample_disposal.html",
            title="Sample Retention & Disposal",
            **get_retention_context(lab_type="coal"),
        )

    @bp.route("/dispose_samples", methods=["POST"])
    @login_required
    def dispose_samples():
        """Mark samples as disposed (Bulk disposal)"""
        from app.models import Sample

        if current_user.role not in ["admin", "senior"]:
            flash(_l("Энэ үйлдлийг гүйцэтгэх эрхгүй байна."), "danger")
            return redirect(url_for("main.sample_disposal"))

        sample_ids = request.form.getlist("sample_ids")
        disposal_method = request.form.get("disposal_method", "").strip()

        if not sample_ids:
            flash(_l("Устгах дээж сонгогдоогүй байна."), "warning")
            return redirect(url_for("main.sample_disposal"))

        if not disposal_method:
            flash(_l("Устгалын аргыг оруулна уу."), "warning")
            return redirect(url_for("main.sample_disposal"))

        disposed_count = 0
        today = date.today()

        for sid in sample_ids:
            try:
                sample = SampleRepository.get_by_id(int(sid))
                if sample and sample.disposal_date is None:
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
            except (ValueError, TypeError) as e:
                current_app.logger.warning(f"dispose_samples: sample_id={sid} error: {e}")
                continue

        if disposed_count > 0:
            try:
                db.session.commit()
                flash(_l("%(count)s дээж устгагдсан гэж тэмдэглэгдлээ.") % {"count": disposed_count}, "success")
            except SQLAlchemyError as e:
                db.session.rollback()
                flash(_l("Алдаа: %(error)s") % {"error": str(e)[:100]}, "danger")

        return redirect(url_for("main.sample_disposal"))

    @bp.route("/set_retention_date", methods=["POST"])
    @login_required
    def set_retention_date():
        """Set sample retention date"""
        from app.models import Sample

        if current_user.role not in ["admin", "senior"]:
            flash(_l("Энэ үйлдлийг гүйцэтгэх эрхгүй байна."), "danger")
            return redirect(url_for("main.sample_disposal"))

        sample_ids = request.form.getlist("sample_ids")
        retention_days = request.form.get("retention_days", "90")

        if not sample_ids:
            flash(_l("Дээж сонгогдоогүй байна."), "warning")
            return redirect(url_for("main.sample_disposal"))

        try:
            days = int(retention_days)
            if days < 1 or days > 3650:
                raise ValueError("Хугацаа 1-3650 хоногийн хооронд байх ёстой")
        except ValueError as e:
            flash(_l("Буруу хугацаа: %(time)s") % {"time": e}, "danger")
            return redirect(url_for("main.sample_disposal"))

        updated_count = 0
        retention_date = date.today() + timedelta(days=days)

        for sid in sample_ids:
            try:
                sample = SampleRepository.get_by_id(int(sid))
                if sample:
                    sample.retention_date = retention_date
                    updated_count += 1
            except (ValueError, TypeError):
                continue

        if updated_count > 0:
            try:
                db.session.commit()
                flash(
                    _l("%(count)s дээжинд хадгалах хугацаа %(date)s гэж тохирууллаа.") % {
                        'count': updated_count, 'date': retention_date,
                    },
                    "success",
                )
                # Audit: Хадгалах хугацаа тохируулсан
                log_audit(
                    action='retention_date_set',
                    resource_type='Sample',
                    details={
                        'sample_count': updated_count,
                        'retention_date': str(retention_date),
                        'retention_days': days,
                    }
                )
            except SQLAlchemyError as e:
                db.session.rollback()
                flash(_l("Алдаа: %(error)s") % {"error": str(e)[:100]}, "danger")

        return redirect(url_for("main.sample_disposal"))

    @bp.route("/bulk_set_retention", methods=["POST"])
    @login_required
    def bulk_set_retention():
        """Set retention date for all samples without one"""
        from app.models import Sample

        retention_days = request.form.get("retention_days", type=int)
        from_date_type = request.form.get("from_date", "received")

        if not retention_days:
            flash(_l("Хугацаа сонгоно уу."), "warning")
            return redirect(url_for("main.sample_disposal"))

        # Find coal samples without retention date
        samples = Sample.query.filter(
            Sample.lab_type == 'coal',
            Sample.retention_date.is_(None),
            Sample.disposal_date.is_(None)
        ).all()

        if not samples:
            flash(_l("Хадгалах хугацаагүй дээж олдсонгүй."), "info")
            return redirect(url_for("main.sample_disposal"))

        today = date.today()
        updated_count = 0

        for s in samples:
            if from_date_type == "received" and s.received_date:
                base_date = s.received_date
            else:
                base_date = today

            s.retention_date = base_date + timedelta(days=retention_days)
            updated_count += 1

        if updated_count > 0:
            safe_commit(
                f"{updated_count} дээжинд хадгалах хугацаа тохируулагдлаа.",
                "Хадгалах хугацаа тохируулахад алдаа гарлаа"
            )
            # Audit: Bulk хадгалах хугацаа
            log_audit(
                action='bulk_retention_date_set',
                resource_type='Sample',
                details={
                    'sample_count': updated_count,
                    'retention_days': retention_days,
                    'from_date': from_date_type,
                }
            )

        return redirect(url_for("main.sample_disposal"))

    # =====================================================================
    # 5. ANALYTICS DASHBOARD
    # =====================================================================
    @bp.route("/analytics")
    @login_required
    def analytics_dashboard():
        """Analysis statistics dashboard"""
        return render_template(
            "analytics_dashboard.html",
            title="Analysis Statistics"
        )
