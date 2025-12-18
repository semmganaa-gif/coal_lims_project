# app/routes/quality/complaints.py
"""Customer Complaints - ISO 17025 Clause 7.9"""
# Санал гомдлын бүртгэл

from flask import render_template, flash, redirect, url_for, request
from flask_login import login_required, current_user
from app import db
from app.models import CustomerComplaint
from app.utils.quality_helpers import (
    require_quality_edit,
    calculate_status_stats,
    generate_sequential_code
)
from datetime import date
import logging

logger = logging.getLogger(__name__)


def register_routes(bp):
    @bp.route("/complaints")
    @login_required
    def complaints_list():
        complaints = CustomerComplaint.query.order_by(CustomerComplaint.complaint_date.desc()).all()
        stats = calculate_status_stats(
            complaints,
            status_values=['received', 'investigating', 'resolved', 'closed']
        )
        return render_template('quality/complaints_list.html', complaints=complaints, stats=stats, title="Гомдол")

    @bp.route("/complaints/new", methods=["GET", "POST"])
    @login_required
    @require_quality_edit('quality.complaints_list')
    def complaints_new():
        if request.method == "POST":
            # Validate required fields
            client_name = request.form.get('client_name')
            description = request.form.get('description')

            if not client_name or not description:
                flash("Харилцагчийн нэр болон тайлбар шаардлагатай.", "danger")
                return render_template('quality/complaints_form.html', title="Шинэ гомдол")

            # Generate complaint number using helper
            complaint_no = generate_sequential_code(CustomerComplaint, 'complaint_no', 'COMP')

            complaint = CustomerComplaint(
                complaint_no=complaint_no,
                client_name=client_name,
                contact_person=request.form.get('contact_person'),
                contact_email=request.form.get('contact_email'),
                complaint_type=request.form.get('complaint_type'),
                description=description,
                status='received'
            )
            db.session.add(complaint)
            db.session.commit()

            logger.info(f"Complaint created: {complaint_no}, client: {client_name}, user: {current_user.username}")
            flash(f"Гомдол {complaint_no} бүртгэгдлээ", "success")
            return redirect(url_for('quality.complaints_list'))
        return render_template('quality/complaints_form.html', title="Шинэ гомдол")

    @bp.route("/complaints/<int:id>")
    @login_required
    def complaints_detail(id):
        complaint = CustomerComplaint.query.get_or_404(id)
        return render_template('quality/complaints_detail.html', complaint=complaint, title=f"Гомдол - {complaint.complaint_no}")

    @bp.route("/complaints/<int:id>/resolve", methods=["POST"])
    @login_required
    @require_quality_edit('quality.complaints_list')
    def complaints_resolve(id):
        complaint = CustomerComplaint.query.get_or_404(id)
        complaint.investigation_findings = request.form.get('investigation_findings')
        complaint.resolution = request.form.get('resolution')
        complaint.resolution_date = date.today()
        complaint.investigated_by_id = current_user.id
        complaint.status = 'resolved'
        db.session.commit()

        logger.info(f"Complaint resolved: {complaint.complaint_no}, user: {current_user.username}")
        flash(f"Гомдол {complaint.complaint_no} шийдэгдлээ", "success")
        return redirect(url_for('quality.complaints_detail', id=id))
