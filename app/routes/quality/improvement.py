# app/routes/quality/improvement.py
"""Improvementын бүртгэл - LAB.02.00.03 / ISO 17025 Clause 8.6"""

from flask import render_template, flash, redirect, url_for, request
from flask_login import login_required, current_user
from app import db
from app.models import ImprovementRecord
from app.utils.database import safe_commit
from app.utils.quality_helpers import (
    require_quality_edit,
    calculate_status_stats,
    generate_sequential_code
)
from datetime import date
import logging

logger = logging.getLogger(__name__)


def register_routes(bp):
    """Improvementын route-уудыг бүртгэх."""

    @bp.route("/improvement")
    @login_required
    def improvement_list():
        records = ImprovementRecord.query.order_by(
            ImprovementRecord.record_date.desc()
        ).limit(2000).all()
        stats = calculate_status_stats(
            records,
            status_values=['pending', 'in_progress', 'reviewed', 'closed']
        )
        return render_template(
            'quality/improvement_list.html',
            records=records,
            stats=stats,
            title="Improvement Records"
        )

    @bp.route("/improvement/new", methods=["GET", "POST"])
    @login_required
    @require_quality_edit('quality.improvement_list')
    def improvement_new():
        if request.method == "POST":
            activity = request.form.get('activity_description', '').strip()
            if not activity:
                flash("Сайжруулалтын үйл ажиллагааг тайлбарлана уу.", "danger")
                return render_template(
                    'quality/improvement_form.html',
                    today=date.today().isoformat(),
                    title="Шинэ сайжруулалт"
                )

            record_no = generate_sequential_code(
                ImprovementRecord, 'record_no', 'IMP'
            )

            deadline_str = request.form.get('deadline', '').strip()

            record = ImprovementRecord(
                record_no=record_no,
                record_date=request.form.get('record_date') or date.today(),
                activity_description=activity,
                improvement_plan=request.form.get('improvement_plan', '').strip(),
                deadline=deadline_str if deadline_str else None,
                responsible_person=request.form.get('responsible_person', '').strip(),
                documentation=request.form.get('documentation', '').strip(),
                created_by_id=current_user.id,
                status='pending'
            )
            db.session.add(record)
            if not safe_commit(
                f"Сайжруулалт {record_no} бүртгэгдлээ",
                "Сайжруулалт хадгалахад алдаа гарлаа"
            ):
                return redirect(url_for('quality.improvement_list'))

            logger.info(f"Improvement created: {record_no}, user: {current_user.username}")
            return redirect(url_for('quality.improvement_list'))

        return render_template(
            'quality/improvement_form.html',
            today=date.today().isoformat(),
            title="Шинэ сайжруулалт"
        )

    @bp.route("/improvement/<int:id>")
    @login_required
    def improvement_detail(id):
        record = ImprovementRecord.query.get_or_404(id)
        return render_template(
            'quality/improvement_detail.html',
            record=record,
            title=f"Improvement - {record.record_no}"
        )

    @bp.route("/improvement/<int:id>/fill", methods=["POST"])
    @login_required
    def improvement_fill(id):
        """Хэсэг 1: Ажилтан бөглөх."""
        record = ImprovementRecord.query.get_or_404(id)
        record.activity_description = request.form.get('activity_description', '').strip() or record.activity_description
        record.improvement_plan = request.form.get('improvement_plan', '').strip()
        record.responsible_person = request.form.get('responsible_person', '').strip()
        record.documentation = request.form.get('documentation', '').strip()

        deadline_str = request.form.get('deadline', '').strip()
        record.deadline = deadline_str if deadline_str else None

        record.status = 'in_progress'
        if not safe_commit(
            f"{record.record_no} бөглөгдлөө",
            "Сайжруулалт бөглөхөд алдаа гарлаа"
        ):
            return redirect(url_for('quality.improvement_detail', id=id))

        logger.info(f"Improvement filled: {record.record_no}, user: {current_user.username}")
        return redirect(url_for('quality.improvement_detail', id=id))

    @bp.route("/improvement/<int:id>/review", methods=["POST"])
    @login_required
    @require_quality_edit('quality.improvement_list')
    def improvement_review(id):
        """Хяналтын хэсэг: Техникийн менежер."""
        record = ImprovementRecord.query.get_or_404(id)
        record.completed_on_time = request.form.get('completed_on_time') == '1'
        record.fully_implemented = request.form.get('fully_implemented') == '1'
        record.control_notes = request.form.get('control_notes', '').strip()
        record.control_date = date.today()
        record.technical_manager_id = current_user.id
        record.status = 'reviewed'
        if not safe_commit(
            f"{record.record_no} хяналт дууслаа",
            "Сайжруулалт хянахад алдаа гарлаа"
        ):
            return redirect(url_for('quality.improvement_detail', id=id))

        logger.info(f"Improvement reviewed: {record.record_no}, user: {current_user.username}")
        return redirect(url_for('quality.improvement_detail', id=id))
