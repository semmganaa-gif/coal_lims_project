# app/routes/quality/capa.py
# -*- coding: utf-8 -*-
"""
CAPA (Corrective and Preventive Actions) Management
ISO 17025 - Clause 8.7
"""
# Залруулах ажиллагааны бүртгэл

from flask import render_template, flash, redirect, url_for, request
from flask_login import login_required, current_user
from app import db
from app.models import CorrectiveAction, User
from app.utils.quality_helpers import (
    require_quality_edit,
    calculate_status_stats,
    generate_sequential_code,
    parse_date
)
from datetime import date
import logging

logger = logging.getLogger(__name__)


def register_routes(bp):
    """CAPA route-ууд бүртгэх"""

    @bp.route("/capa")
    @login_required
    def capa_list():
        """CAPA жагсаалт"""
        capas = CorrectiveAction.query.order_by(CorrectiveAction.issue_date.desc()).all()
        stats = calculate_status_stats(capas, status_values=['open', 'in_progress', 'closed'])

        return render_template(
            'quality/capa_list.html',
            capas=capas,
            stats=stats,
            title="CAPA - Засвар арга хэмжээ"
        )

    @bp.route("/capa/new", methods=["GET", "POST"])
    @login_required
    @require_quality_edit('quality.capa_list')
    def capa_new():
        """Шинэ CAPA үүсгэх"""
        if request.method == "POST":
            # Generate CA number using helper
            ca_number = generate_sequential_code(CorrectiveAction, 'ca_number', 'CA')

            # Parse dates safely
            issue_date = parse_date(request.form.get('issue_date'), date.today())
            target_date = parse_date(request.form.get('target_date'))

            # Create CAPA
            capa = CorrectiveAction(
                ca_number=ca_number,
                issue_date=issue_date,
                issue_source=request.form.get('issue_source'),
                issue_description=request.form.get('issue_description'),
                severity=request.form.get('severity', 'Minor'),
                responsible_person_id=request.form.get('responsible_person_id'),
                target_date=target_date,
                status='open'
            )

            db.session.add(capa)
            db.session.commit()

            logger.info(f"CAPA created: {ca_number}, severity: {capa.severity}, user: {current_user.username}")
            flash(f"CAPA {ca_number} амжилттай үүслээ", "success")
            return redirect(url_for('quality.capa_detail', id=capa.id))

        # GET - form харуулах
        users = User.query.all()
        return render_template(
            'quality/capa_form.html',
            users=users,
            title="Шинэ CAPA үүсгэх"
        )

    @bp.route("/capa/<int:id>")
    @login_required
    def capa_detail(id):
        """CAPA дэлгэрэнгүй"""
        capa = CorrectiveAction.query.get_or_404(id)
        return render_template(
            'quality/capa_detail.html',
            capa=capa,
            title=f"CAPA - {capa.ca_number}"
        )

    @bp.route("/capa/<int:id>/edit", methods=["GET", "POST"])
    @login_required
    @require_quality_edit('quality.capa_list')
    def capa_edit(id):
        """CAPA засах"""
        capa = CorrectiveAction.query.get_or_404(id)

        if request.method == "POST":
            capa.issue_source = request.form.get('issue_source')
            capa.issue_description = request.form.get('issue_description')
            capa.severity = request.form.get('severity')
            capa.root_cause = request.form.get('root_cause')
            capa.root_cause_method = request.form.get('root_cause_method')
            capa.corrective_action = request.form.get('corrective_action')
            capa.preventive_action = request.form.get('preventive_action')
            capa.responsible_person_id = request.form.get('responsible_person_id')

            # Parse dates safely
            target_date = parse_date(request.form.get('target_date'))
            if target_date:
                capa.target_date = target_date

            completion_date = parse_date(request.form.get('completion_date'))
            if completion_date:
                capa.completion_date = completion_date

            capa.status = request.form.get('status', capa.status)
            capa.notes = request.form.get('notes')

            db.session.commit()
            
            logger.info(f"CAPA updated: {capa.ca_number}, status: {capa.status}, user: {current_user.username}")
            flash(f"CAPA {capa.ca_number} шинэчлэгдлээ", "success")
            return redirect(url_for('quality.capa_detail', id=capa.id))

        users = User.query.all()
        return render_template(
            'quality/capa_form.html',
            capa=capa,
            users=users,
            title=f"CAPA засах - {capa.ca_number}"
        )

    @bp.route("/capa/<int:id>/verify", methods=["POST"])
    @login_required
    @require_quality_edit('quality.capa_list')
    def capa_verify(id):
        """CAPA баталгаажуулах"""
        capa = CorrectiveAction.query.get_or_404(id)

        capa.verification_method = request.form.get('verification_method')
        capa.verification_date = date.today()
        capa.verified_by_id = current_user.id
        capa.effectiveness = request.form.get('effectiveness', 'Pending')

        if capa.effectiveness == 'Effective':
            capa.status = 'closed'

        db.session.commit()
        
        logger.info(f"CAPA verified: {capa.ca_number}, effectiveness: {capa.effectiveness}, user: {current_user.username}")
        flash(f"CAPA {capa.ca_number} баталгаажлаа", "success")
        return redirect(url_for('quality.capa_detail', id=capa.id))
