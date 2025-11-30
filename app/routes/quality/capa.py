# app/routes/quality/capa.py
# -*- coding: utf-8 -*-
"""
CAPA (Corrective and Preventive Actions) Management
ISO 17025 - Clause 8.7
"""

from flask import render_template, flash, redirect, url_for, request, jsonify
from flask_login import login_required, current_user
from app import db
from app.models import CorrectiveAction, User
from app.utils.datetime import now_local
from datetime import datetime, date
import json


def register_routes(bp):
    """CAPA route-ууд бүртгэх"""

    @bp.route("/capa")
    @login_required
    def capa_list():
        """CAPA жагсаалт"""
        capas = CorrectiveAction.query.order_by(CorrectiveAction.issue_date.desc()).all()

        # Statistics
        total = len(capas)
        open_count = len([c for c in capas if c.status == 'open'])
        in_progress = len([c for c in capas if c.status == 'in_progress'])
        closed = len([c for c in capas if c.status == 'closed'])

        stats = {
            'total': total,
            'open': open_count,
            'in_progress': in_progress,
            'closed': closed
        }

        return render_template(
            'quality/capa_list.html',
            capas=capas,
            stats=stats,
            title="CAPA - Засвар арга хэмжээ"
        )

    @bp.route("/capa/new", methods=["GET", "POST"])
    @login_required
    def capa_new():
        """Шинэ CAPA үүсгэх"""
        if request.method == "POST":
            # Generate CA number
            year = datetime.now().year
            last_capa = CorrectiveAction.query.filter(
                CorrectiveAction.ca_number.like(f'CA-{year}-%')
            ).order_by(CorrectiveAction.ca_number.desc()).first()

            if last_capa:
                last_num = int(last_capa.ca_number.split('-')[-1])
                new_num = last_num + 1
            else:
                new_num = 1

            ca_number = f"CA-{year}-{new_num:04d}"

            # Create CAPA
            capa = CorrectiveAction(
                ca_number=ca_number,
                issue_date=datetime.strptime(request.form['issue_date'], '%Y-%m-%d').date() if request.form.get('issue_date') else date.today(),
                issue_source=request.form.get('issue_source'),
                issue_description=request.form.get('issue_description'),
                severity=request.form.get('severity', 'Minor'),
                responsible_person_id=request.form.get('responsible_person_id'),
                target_date=datetime.strptime(request.form['target_date'], '%Y-%m-%d').date() if request.form.get('target_date') else None,
                status='open'
            )

            db.session.add(capa)
            db.session.commit()

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

            if request.form.get('target_date'):
                capa.target_date = datetime.strptime(request.form['target_date'], '%Y-%m-%d').date()

            if request.form.get('completion_date'):
                capa.completion_date = datetime.strptime(request.form['completion_date'], '%Y-%m-%d').date()

            capa.status = request.form.get('status', capa.status)
            capa.notes = request.form.get('notes')

            db.session.commit()
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
        flash(f"CAPA {capa.ca_number} баталгаажлаа", "success")
        return redirect(url_for('quality.capa_detail', id=capa.id))
