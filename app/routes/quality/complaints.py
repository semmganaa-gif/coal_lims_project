# app/routes/quality/complaints.py
"""Customer Complaints - ISO 17025 Clause 8.9"""
from flask import render_template, flash, redirect, url_for, request
from flask_login import login_required, current_user
from app import db
from app.models import CustomerComplaint
from datetime import datetime, date

def register_routes(bp):
    @bp.route("/complaints")
    @login_required
    def complaints_list():
        complaints = CustomerComplaint.query.order_by(CustomerComplaint.complaint_date.desc()).all()
        stats = {
            'total': len(complaints),
            'received': len([c for c in complaints if c.status == 'received']),
            'investigating': len([c for c in complaints if c.status == 'investigating']),
            'resolved': len([c for c in complaints if c.status == 'resolved']),
            'closed': len([c for c in complaints if c.status == 'closed'])
        }
        return render_template('quality/complaints_list.html', complaints=complaints, stats=stats, title="Гомдол")

    @bp.route("/complaints/new", methods=["GET", "POST"])
    @login_required
    def complaints_new():
        if request.method == "POST":
            year = datetime.now().year
            last = CustomerComplaint.query.filter(CustomerComplaint.complaint_no.like(f'COMP-{year}-%')).order_by(CustomerComplaint.complaint_no.desc()).first()
            num = int(last.complaint_no.split('-')[-1]) + 1 if last else 1
            complaint_no = f"COMP-{year}-{num:04d}"

            complaint = CustomerComplaint(
                complaint_no=complaint_no,
                client_name=request.form['client_name'],
                contact_person=request.form.get('contact_person'),
                contact_email=request.form.get('contact_email'),
                complaint_type=request.form.get('complaint_type'),
                description=request.form['description'],
                status='received'
            )
            db.session.add(complaint)
            db.session.commit()
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
    def complaints_resolve(id):
        complaint = CustomerComplaint.query.get_or_404(id)
        complaint.investigation_findings = request.form.get('investigation_findings')
        complaint.resolution = request.form.get('resolution')
        complaint.resolution_date = date.today()
        complaint.investigated_by_id = current_user.id
        complaint.status = 'resolved'
        db.session.commit()
        flash(f"Гомдол {complaint.complaint_no} шийдэгдлээ", "success")
        return redirect(url_for('quality.complaints_detail', id=id))
