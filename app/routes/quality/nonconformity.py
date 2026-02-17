# app/routes/quality/nonconformity.py
"""Nonconformity / үл тохирох ажлын бүртгэл - LAB.10.00.01 / ISO 17025 Clause 7.10"""

from flask import render_template, flash, redirect, url_for, request
from flask_login import login_required, current_user
from app import db
from app.models import NonConformityRecord
from app.utils.quality_helpers import (
    require_quality_edit,
    calculate_status_stats,
    generate_sequential_code
)
from datetime import date
import logging

logger = logging.getLogger(__name__)


def register_routes(bp):
    """Үл тохирлын route-уудыг бүртгэх."""

    @bp.route("/nonconformity")
    @login_required
    def nonconformity_list():
        records = NonConformityRecord.query.order_by(
            NonConformityRecord.record_date.desc()
        ).limit(2000).all()
        stats = calculate_status_stats(
            records,
            status_values=['pending', 'investigating', 'reviewed', 'closed']
        )
        return render_template(
            'quality/nonconformity_list.html',
            records=records,
            stats=stats,
            title="Үл тохирлын бүртгэл"
        )

    @bp.route("/nonconformity/new", methods=["GET", "POST"])
    @login_required
    @require_quality_edit('quality.nonconformity_list')
    def nonconformity_new():
        if request.method == "POST":
            detector_name = request.form.get('detector_name', '').strip()
            nc_description = request.form.get('nc_description', '').strip()

            if not detector_name or not nc_description:
                flash("Илрүүлсэн хүн болон дэлгэрэнгүй мэдээлэл шаардлагатай.", "danger")
                return render_template(
                    'quality/nonconformity_form.html',
                    today=date.today().isoformat(),
                    title="Шинэ үл тохирол"
                )

            record_no = generate_sequential_code(
                NonConformityRecord, 'record_no', 'NC'
            )

            record = NonConformityRecord(
                record_no=record_no,
                record_date=request.form.get('record_date') or date.today(),
                detector_name=detector_name,
                detector_department=request.form.get('detector_department', '').strip(),
                nc_description=nc_description,
                proposed_action=request.form.get('proposed_action', '').strip(),
                detector_user_id=current_user.id,
                status='pending'
            )
            db.session.add(record)
            db.session.commit()

            logger.info(f"NonConformity created: {record_no}, user: {current_user.username}")
            flash(f"Үл тохирол {record_no} бүртгэгдлээ", "success")
            return redirect(url_for('quality.nonconformity_list'))

        return render_template(
            'quality/nonconformity_form.html',
            today=date.today().isoformat(),
            title="Шинэ үл тохирол"
        )

    @bp.route("/nonconformity/<int:id>")
    @login_required
    def nonconformity_detail(id):
        record = NonConformityRecord.query.get_or_404(id)
        return render_template(
            'quality/nonconformity_detail.html',
            record=record,
            title=f"Nonconformity - {record.record_no}"
        )

    @bp.route("/nonconformity/<int:id>/investigate", methods=["POST"])
    @login_required
    @require_quality_edit('quality.nonconformity_list')
    def nonconformity_investigate(id):
        """Хэсэг 2: Хариуцсан нэгж бөглөх."""
        record = NonConformityRecord.query.get_or_404(id)
        record.responsible_unit = request.form.get('responsible_unit', '').strip()
        record.responsible_person = request.form.get('responsible_person', '').strip()
        record.direct_cause = request.form.get('direct_cause', '').strip()
        record.corrective_action = request.form.get('corrective_action', '').strip()

        deadline_str = request.form.get('corrective_deadline', '').strip()
        record.corrective_deadline = deadline_str if deadline_str else None

        record.root_cause = request.form.get('root_cause', '').strip()
        record.corrective_plan = request.form.get('corrective_plan', '').strip()
        record.responsible_user_id = current_user.id
        record.status = 'investigating'
        db.session.commit()

        logger.info(f"NonConformity investigated: {record.record_no}, user: {current_user.username}")
        flash(f"{record.record_no} хянагдаж байна", "success")
        return redirect(url_for('quality.nonconformity_detail', id=id))

    @bp.route("/nonconformity/<int:id>/review", methods=["POST"])
    @login_required
    @require_quality_edit('quality.nonconformity_list')
    def nonconformity_review(id):
        """Хэсэг 3: Хяналт (Чанарын/Техникийн менежер)."""
        record = NonConformityRecord.query.get_or_404(id)
        record.completed_on_time = request.form.get('completed_on_time') == '1'
        record.fully_implemented = request.form.get('fully_implemented') == '1'
        record.control_notes = request.form.get('control_notes', '').strip()
        record.manager_id = current_user.id
        record.status = 'reviewed'
        db.session.commit()

        logger.info(f"NonConformity reviewed: {record.record_no}, user: {current_user.username}")
        flash(f"{record.record_no} хяналт дууслаа", "success")
        return redirect(url_for('quality.nonconformity_detail', id=id))
