# app/routes/quality/capa.py
"""Залруулах ажиллагааны бүртгэл - LAB.02.00.04 / ISO 17025 Clause 8.7"""

from flask import render_template, flash, redirect, url_for, request
from flask_login import login_required, current_user
from app import db
from app.models import CorrectiveAction
from app.utils.quality_helpers import (
    require_quality_edit,
    calculate_status_stats,
    generate_sequential_code
)
from datetime import date
import logging

logger = logging.getLogger(__name__)


def register_routes(bp):
    """Залруулах ажиллагааны route-уудыг бүртгэх."""

    @bp.route("/capa")
    @login_required
    def capa_list():
        records = CorrectiveAction.query.order_by(
            CorrectiveAction.issue_date.desc()
        ).limit(2000).all()
        stats = calculate_status_stats(
            records,
            status_values=['open', 'in_progress', 'reviewed', 'closed']
        )
        return render_template(
            'quality/capa_list.html',
            records=records,
            stats=stats,
            title="Залруулах ажиллагааны бүртгэл"
        )

    @bp.route("/capa/new", methods=["GET", "POST"])
    @login_required
    @require_quality_edit('quality.capa_list')
    def capa_new():
        if request.method == "POST":
            desc = request.form.get('issue_description', '').strip()
            if not desc:
                flash("Үл тохирлын тайлбар шаардлагатай.", "danger")
                return render_template(
                    'quality/capa_form.html',
                    today=date.today().isoformat(),
                    title="Шинэ залруулах ажиллагаа"
                )

            ca_number = generate_sequential_code(
                CorrectiveAction, 'ca_number', 'CA'
            )

            target_str = request.form.get('target_date', '').strip()

            record = CorrectiveAction(
                ca_number=ca_number,
                issue_date=request.form.get('issue_date') or date.today(),
                issue_description=desc,
                corrective_action=request.form.get('corrective_action', '').strip(),
                target_date=target_str if target_str else None,
                responsible_person_id=current_user.id,
                notes=request.form.get('notes', '').strip(),
                status='open'
            )
            db.session.add(record)
            db.session.commit()

            logger.info(f"CAPA created: {ca_number}, user: {current_user.username}")
            flash(f"Залруулах ажиллагаа {ca_number} бүртгэгдлээ", "success")
            return redirect(url_for('quality.capa_list'))

        return render_template(
            'quality/capa_form.html',
            today=date.today().isoformat(),
            title="Шинэ залруулах ажиллагаа"
        )

    @bp.route("/capa/<int:id>")
    @login_required
    def capa_detail(id):
        record = CorrectiveAction.query.get_or_404(id)
        return render_template(
            'quality/capa_detail.html',
            record=record,
            title=f"Залруулах ажиллагаа - {record.ca_number}"
        )

    @bp.route("/capa/<int:id>/fill", methods=["POST"])
    @login_required
    @require_quality_edit('quality.capa_list')
    def capa_fill(id):
        """Хэсэг 1: Хэрэгжүүлэгч бөглөх."""
        record = CorrectiveAction.query.get_or_404(id)
        record.issue_description = request.form.get('issue_description', '').strip() or record.issue_description
        record.corrective_action = request.form.get('corrective_action', '').strip()
        record.notes = request.form.get('notes', '').strip()

        target_str = request.form.get('target_date', '').strip()
        record.target_date = target_str if target_str else None

        record.status = 'in_progress'
        db.session.commit()

        logger.info(f"CAPA filled: {record.ca_number}, user: {current_user.username}")
        flash(f"{record.ca_number} бөглөгдлөө", "success")
        return redirect(url_for('quality.capa_detail', id=id))

    @bp.route("/capa/<int:id>/review", methods=["POST"])
    @login_required
    @require_quality_edit('quality.capa_list')
    def capa_review(id):
        """Хэсэг 2: Хяналт (Техникийн менежер)."""
        record = CorrectiveAction.query.get_or_404(id)
        record.completed_on_time = request.form.get('completed_on_time') == '1'
        record.fully_resolved = request.form.get('fully_resolved') == '1'
        record.residual_risk_exists = request.form.get('residual_risk_exists') == '1'
        record.management_change_needed = request.form.get('management_change_needed') == '1'
        record.control_notes = request.form.get('control_notes', '').strip()
        record.control_date = date.today()
        record.technical_manager_id = current_user.id
        record.status = 'reviewed'
        db.session.commit()

        logger.info(f"CAPA reviewed: {record.ca_number}, user: {current_user.username}")
        flash(f"{record.ca_number} хянагдлаа", "success")
        return redirect(url_for('quality.capa_detail', id=id))
