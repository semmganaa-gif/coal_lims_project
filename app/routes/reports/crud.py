# app/routes/reports/crud.py
# -*- coding: utf-8 -*-
"""Тайлангийн CRUD үйлдлүүд."""

import os
from flask import (
    render_template, request, redirect, url_for,
    flash, jsonify, send_file, current_app
)
from flask_login import login_required, current_user
from app import db
from app.models import LabReport, ReportSignature, Sample, AnalysisResult, User
from datetime import datetime, date
from app.routes.reports import pdf_reports_bp, LAB_TYPES, REPORT_STATUSES


# -------------------------------------------------
# 1. Тайлангийн жагсаалт
# -------------------------------------------------
@pdf_reports_bp.route("/")
@pdf_reports_bp.route("/list")
@login_required
def report_list():
    """Тайлангийн жагсаалт."""
    lab = request.args.get("lab", "all")
    status = request.args.get("status", "all")

    query = LabReport.query

    if lab and lab != "all":
        query = query.filter(LabReport.lab_type == lab)

    if status and status != "all":
        query = query.filter(LabReport.status == status)

    reports = query.order_by(LabReport.created_at.desc()).limit(100).all()

    return render_template(
        "reports/report_list.html",
        reports=reports,
        lab=lab,
        status=status,
        lab_types=LAB_TYPES,
        report_statuses=REPORT_STATUSES,
    )


# -------------------------------------------------
# 2. Гарын үсэг, тамга удирдлага
# -------------------------------------------------
@pdf_reports_bp.route("/signatures")
@login_required
def signature_list():
    """Гарын үсэг, тамгын жагсаалт."""
    if current_user.role not in ["senior", "manager", "admin"]:
        flash("Хандах эрхгүй.", "danger")
        return redirect(url_for("pdf_reports.report_list"))

    signatures = ReportSignature.query.filter_by(is_active=True).all()
    stamps = [s for s in signatures if s.signature_type == 'stamp']
    sigs = [s for s in signatures if s.signature_type == 'signature']

    return render_template(
        "reports/signature_list.html",
        signatures=sigs,
        stamps=stamps,
        lab_types=LAB_TYPES,
    )


@pdf_reports_bp.route("/signatures/add", methods=["GET", "POST"])
@login_required
def add_signature():
    """Гарын үсэг/тамга нэмэх."""
    if current_user.role not in ["senior", "manager", "admin"]:
        flash("Хандах эрхгүй.", "danger")
        return redirect(url_for("pdf_reports.signature_list"))

    if request.method == "POST":
        try:
            sig_type = request.form.get("signature_type", "signature")
            name = request.form.get("name")
            position = request.form.get("position")
            lab_type = request.form.get("lab_type", "all")

            # Файл хадгалах
            image_path = None
            if 'image' in request.files:
                file = request.files['image']
                if file and file.filename:
                    # Хадгалах folder
                    upload_folder = os.path.join(
                        current_app.root_path, 'static', 'uploads', 'signatures'
                    )
                    os.makedirs(upload_folder, exist_ok=True)

                    # Файлын нэр
                    ext = file.filename.rsplit('.', 1)[-1].lower()
                    filename = f"{sig_type}_{datetime.now().strftime('%Y%m%d%H%M%S')}.{ext}"
                    filepath = os.path.join(upload_folder, filename)
                    file.save(filepath)
                    image_path = f"uploads/signatures/{filename}"

            sig = ReportSignature(
                name=name,
                signature_type=sig_type,
                image_path=image_path,
                position=position,
                lab_type=lab_type,
                user_id=request.form.get("user_id") or None,
            )

            db.session.add(sig)
            db.session.commit()
            flash(f"'{name}' амжилттай нэмэгдлэн.", "success")
            return redirect(url_for("pdf_reports.signature_list"))

        except Exception as e:
            db.session.rollback()
            flash(f"Алдаа: {str(e)[:100]}", "danger")

    users = User.query.filter(User.role.in_(['senior', 'manager', 'admin'])).all()
    return render_template(
        "reports/signature_form.html",
        signature=None,
        mode="add",
        users=users,
        lab_types=LAB_TYPES,
    )


@pdf_reports_bp.route("/signatures/delete/<int:id>", methods=["POST"])
@login_required
def delete_signature(id):
    """Гарын үсэг/тамга устгах."""
    if current_user.role not in ["manager", "admin"]:
        flash("Хандах эрхгүй.", "danger")
        return redirect(url_for("pdf_reports.signature_list"))

    sig = ReportSignature.query.get_or_404(id)
    sig.is_active = False
    db.session.commit()
    flash("Устгагдлаа.", "warning")
    return redirect(url_for("pdf_reports.signature_list"))


# -------------------------------------------------
# 3. Тайлан дэлгэрэнгүй
# -------------------------------------------------
@pdf_reports_bp.route("/<int:id>")
@login_required
def report_detail(id):
    """Тайлангийн дэлгэрэнгүй."""
    report = LabReport.query.get_or_404(id)

    # Гарын үсэг, тамгын сонголт
    signatures = ReportSignature.query.filter_by(
        is_active=True, signature_type='signature'
    ).filter(
        (ReportSignature.lab_type == report.lab_type) | (ReportSignature.lab_type == 'all')
    ).all()

    stamps = ReportSignature.query.filter_by(
        is_active=True, signature_type='stamp'
    ).filter(
        (ReportSignature.lab_type == report.lab_type) | (ReportSignature.lab_type == 'all')
    ).all()

    return render_template(
        "reports/report_detail.html",
        report=report,
        signatures=signatures,
        stamps=stamps,
        lab_types=LAB_TYPES,
        report_statuses=REPORT_STATUSES,
    )


# -------------------------------------------------
# 4. Тайлан баталгаажуулах
# -------------------------------------------------
@pdf_reports_bp.route("/<int:id>/approve", methods=["POST"])
@login_required
def approve_report(id):
    """Тайлан баталгаажуулах."""
    if current_user.role not in ["senior", "manager", "admin"]:
        flash("Хандах эрхгүй.", "danger")
        return redirect(url_for("pdf_reports.report_detail", id=id))

    report = LabReport.query.get_or_404(id)

    # Гарын үсэг, тамга сонгох
    analyst_sig_id = request.form.get("analyst_signature_id")
    manager_sig_id = request.form.get("manager_signature_id")
    stamp_id = request.form.get("stamp_id")

    if analyst_sig_id:
        report.analyst_signature_id = int(analyst_sig_id)
    if manager_sig_id:
        report.manager_signature_id = int(manager_sig_id)
    if stamp_id:
        report.stamp_id = int(stamp_id)

    report.status = 'approved'
    report.approved_by_id = current_user.id
    report.approved_at = datetime.now()

    db.session.commit()

    # PDF дахин үүсгэх (гарын үсэгтэй)
    from app.routes.reports.pdf_generator import regenerate_pdf
    regenerate_pdf(report)

    flash("Тайлан зөвшөөрөгдлөө.", "success")
    return redirect(url_for("pdf_reports.report_detail", id=id))


# -------------------------------------------------
# 5. PDF татах
# -------------------------------------------------
@pdf_reports_bp.route("/<int:id>/download")
@login_required
def download_report(id):
    """PDF татах."""
    report = LabReport.query.get_or_404(id)

    if not report.pdf_path:
        flash("PDF файл олдсонгүй.", "warning")
        return redirect(url_for("pdf_reports.report_detail", id=id))

    pdf_full_path = os.path.join(current_app.root_path, 'static', report.pdf_path)

    if not os.path.exists(pdf_full_path):
        flash("PDF файл олдсонгүй.", "warning")
        return redirect(url_for("pdf_reports.report_detail", id=id))

    return send_file(
        pdf_full_path,
        as_attachment=True,
        download_name=f"{report.report_number}.pdf"
    )


# -------------------------------------------------
# 6. Тайлан устгах
# -------------------------------------------------
@pdf_reports_bp.route("/<int:id>/delete", methods=["POST"])
@login_required
def delete_report(id):
    """Тайлан устгах."""
    if current_user.role not in ["manager", "admin"]:
        flash("Хандах эрхгүй.", "danger")
        return redirect(url_for("pdf_reports.report_list"))

    report = LabReport.query.get_or_404(id)

    # PDF файл устгах
    if report.pdf_path:
        pdf_full_path = os.path.join(current_app.root_path, 'static', report.pdf_path)
        if os.path.exists(pdf_full_path):
            os.remove(pdf_full_path)

    db.session.delete(report)
    db.session.commit()
    flash("Тайлан устгагдлаа.", "warning")
    return redirect(url_for("pdf_reports.report_list"))


# -------------------------------------------------
# 7. Дараагийн дугаар авах
# -------------------------------------------------
def get_next_report_number(lab_type):
    """Дараагийн тайлангийн дугаар авах."""
    year = datetime.now().year

    # Сүүлийн тайлангийн дугаар
    last_report = LabReport.query.filter(
        LabReport.report_number.like(f"{year}_%")
    ).order_by(LabReport.id.desc()).first()

    if last_report:
        try:
            last_num = int(last_report.report_number.split('_')[1])
            return f"{year}_{last_num + 1}"
        except (IndexError, ValueError):
            pass

    # Тоолох
    count = LabReport.query.filter(
        LabReport.report_number.like(f"{year}_%")
    ).count()

    return f"{year}_{count + 1}"


# -------------------------------------------------
# 8. Тайлан үүсгэх API (Нэгтгэлээс дуудах)
# -------------------------------------------------
@pdf_reports_bp.route("/api/create", methods=["POST"])
@login_required
def api_create_report():
    """Тайлан үүсгэх API."""
    try:
        data = request.get_json()
        lab_type = data.get("lab_type")
        sample_ids = data.get("sample_ids", [])
        date_from_str = data.get("date_from")
        date_to_str = data.get("date_to")

        if not lab_type or not sample_ids:
            return jsonify({"success": False, "error": "lab_type болон sample_ids шаардлагатай"}), 400

        # Огноо parse
        date_from = None
        date_to = None
        if date_from_str:
            date_from = datetime.strptime(date_from_str, "%Y-%m-%d").date()
        if date_to_str:
            date_to = datetime.strptime(date_to_str, "%Y-%m-%d").date()

        # Лаб төрлөөр тайлан үүсгэх
        from app.routes.reports.pdf_generator import (
            generate_microbiology_report,
            generate_water_report,
            generate_coal_report
        )

        report = None
        error = None

        if lab_type == 'microbiology':
            report, error = generate_microbiology_report(
                sample_ids, date_from, date_to, current_user.id
            )
        elif lab_type == 'water':
            report, error = generate_water_report(
                sample_ids, date_from, date_to, current_user.id
            )
        elif lab_type == 'coal':
            report, error = generate_coal_report(
                sample_ids, date_from, date_to, current_user.id
            )
        else:
            return jsonify({"success": False, "error": f"Тодорхойгүй лабораторийн төрөл: {lab_type}"}), 400

        if error:
            return jsonify({"success": False, "error": error}), 400

        return jsonify({
            "success": True,
            "report_id": report.id,
            "report_number": report.report_number,
            "redirect_url": url_for("pdf_reports.report_detail", id=report.id)
        })

    except Exception as e:
        current_app.logger.error(f"Error creating report: {e}")
        return jsonify({"success": False, "error": str(e)}), 500
