# app/routes/reports/crud.py
# -*- coding: utf-8 -*-
"""Тайлангийн CRUD үйлдлүүд."""

import os
import uuid
from datetime import datetime

from flask import (
    render_template, request, redirect, url_for,
    flash, jsonify, send_file, current_app, abort
)
from flask_login import login_required, current_user
from flask_babel import lazy_gettext as _l
from werkzeug.utils import secure_filename

from sqlalchemy import func, select
from sqlalchemy.exc import SQLAlchemyError

from app import db
from app.constants import UserRole
from app.utils.decorators import role_required
from app.utils.datetime import now_local
from app.models import LabReport, ReportSignature, AnalysisResult, User
from app.repositories import LabReportRepository, ReportSignatureRepository
from app.routes.reports import pdf_reports_bp, LAB_TYPES, REPORT_STATUSES
from app.utils.database import safe_commit

ALLOWED_IMAGE_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
IMAGE_MAGIC_BYTES = {
    b'\x89PNG': 'png',
    b'\xff\xd8\xff': 'jpg',
    b'GIF87a': 'gif',
    b'GIF89a': 'gif',
    b'RIFF': 'webp',
}
MAX_SIGNATURE_FILE_SIZE = 5 * 1024 * 1024  # 5MB


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
@role_required(UserRole.SENIOR.value, UserRole.MANAGER.value, UserRole.ADMIN.value)
def signature_list():
    """Гарын үсэг, тамгын жагсаалт."""
    signatures = list(db.session.execute(
        select(ReportSignature).where(ReportSignature.is_active.is_(True))
    ).scalars().all())
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
@role_required(UserRole.SENIOR.value, UserRole.MANAGER.value, UserRole.ADMIN.value)
def add_signature():
    """Гарын үсэг/тамга нэмэх."""
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
                    # Extension whitelist шалгах
                    raw_name = secure_filename(file.filename)
                    ext = raw_name.rsplit('.', 1)[-1].lower() if '.' in raw_name else ''
                    if ext not in ALLOWED_IMAGE_EXTENSIONS:
                        flash(
                            _l("Зөвшөөрөгдөөгүй файлын төрөл: .%(ext)s. Зөвхөн %(allowed)s") % {
                                'ext': ext, 'allowed': ', '.join(ALLOWED_IMAGE_EXTENSIONS),
                            },
                            "danger",
                        )
                        return redirect(url_for("pdf_reports.signature_list"))

                    # Файлын хэмжээ шалгах
                    file.seek(0, 2)
                    file_size = file.tell()
                    file.seek(0)
                    if file_size > MAX_SIGNATURE_FILE_SIZE:
                        flash(_l("Файлын хэмжээ хэт их (max 5MB)."), "danger")
                        return redirect(url_for("pdf_reports.signature_list"))

                    # Magic bytes шалгах
                    header_bytes = file.read(8)
                    file.seek(0)
                    valid_magic = any(header_bytes.startswith(magic) for magic in IMAGE_MAGIC_BYTES)
                    if not valid_magic:
                        flash(_l("Файлын агуулга зургийн формат биш байна."), "danger")
                        return redirect(url_for("pdf_reports.signature_list"))

                    # Хадгалах folder
                    upload_folder = os.path.join(
                        current_app.root_path, 'static', 'uploads', 'signatures'
                    )
                    os.makedirs(upload_folder, exist_ok=True)

                    # UUID filename
                    filename = f"{sig_type}_{uuid.uuid4().hex}.{ext}"
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
            if not safe_commit(f"'{name}' амжилттай нэмэгдлэн.", "Гарын үсэг нэмэхэд алдаа гарлаа."):
                return redirect(url_for("pdf_reports.signature_list"))
            return redirect(url_for("pdf_reports.signature_list"))

        except (OSError, SQLAlchemyError, ValueError) as e:
            db.session.rollback()
            flash(_l("Алдаа: %(error)s") % {"error": str(e)[:100]}, "danger")

    users = list(db.session.execute(
        select(User).where(User.role.in_(['senior', 'manager', 'admin']))
    ).scalars().all())
    return render_template(
        "reports/signature_form.html",
        signature=None,
        mode="add",
        users=users,
        lab_types=LAB_TYPES,
    )


@pdf_reports_bp.route("/signatures/delete/<int:id>", methods=["POST"])
@login_required
@role_required(UserRole.MANAGER.value, UserRole.ADMIN.value)
def delete_signature(id):
    """Гарын үсэг/тамга устгах."""
    sig = ReportSignatureRepository.get_by_id(id)
    if not sig:
        abort(404)
    sig.is_active = False
    safe_commit("Устгагдлаа.", "Устгахад алдаа гарлаа.")
    return redirect(url_for("pdf_reports.signature_list"))


# -------------------------------------------------
# 3. Тайлан дэлгэрэнгүй
# -------------------------------------------------
@pdf_reports_bp.route("/<int:id>")
@login_required
def report_detail(id):
    """Тайлангийн дэлгэрэнгүй."""
    report = LabReportRepository.get_by_id_or_404(id)

    # Гарын үсэг, тамгын сонголт
    from sqlalchemy import or_
    sig_lab_filter = or_(
        ReportSignature.lab_type == report.lab_type,
        ReportSignature.lab_type == 'all',
    )
    signatures = list(db.session.execute(
        select(ReportSignature).where(
            ReportSignature.is_active.is_(True),
            ReportSignature.signature_type == 'signature',
            sig_lab_filter,
        )
    ).scalars().all())

    stamps = list(db.session.execute(
        select(ReportSignature).where(
            ReportSignature.is_active.is_(True),
            ReportSignature.signature_type == 'stamp',
            sig_lab_filter,
        )
    ).scalars().all())

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
@role_required(UserRole.SENIOR.value, UserRole.MANAGER.value, UserRole.ADMIN.value)
def approve_report(id):
    """Тайлан баталгаажуулах."""
    report = LabReportRepository.get_by_id_or_404(id)

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
    report.approved_at = now_local()

    if not safe_commit("Тайлан зөвшөөрөгдлөө.", "Тайлан баталгаажуулахад алдаа гарлаа."):
        return redirect(url_for("pdf_reports.report_detail", id=id))

    # PDF дахин үүсгэх (гарын үсэгтэй)
    from app.routes.reports.pdf_generator import regenerate_pdf
    regenerate_pdf(report)

    return redirect(url_for("pdf_reports.report_detail", id=id))


# -------------------------------------------------
# 5. PDF татах
# -------------------------------------------------
@pdf_reports_bp.route("/<int:id>/download")
@login_required
def download_report(id):
    """PDF татах."""
    report = LabReportRepository.get_by_id_or_404(id)

    if not report.pdf_path:
        flash(_l("PDF файл олдсонгүй."), "warning")
        return redirect(url_for("pdf_reports.report_detail", id=id))

    pdf_full_path = os.path.realpath(os.path.join(current_app.root_path, 'static', report.pdf_path))
    safe_dir = os.path.realpath(os.path.join(current_app.root_path, 'static'))
    if not pdf_full_path.startswith(safe_dir):
        flash(_l("Зөвшөөрөгдөөгүй файлын зам."), "danger")
        return redirect(url_for("pdf_reports.report_detail", id=id))

    if not os.path.exists(pdf_full_path):
        flash(_l("PDF файл олдсонгүй."), "warning")
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
@role_required(UserRole.MANAGER.value, UserRole.ADMIN.value)
def delete_report(id):
    """Тайлан устгах."""
    report = LabReportRepository.get_by_id_or_404(id)

    # PDF файл устгах
    if report.pdf_path:
        pdf_full_path = os.path.join(current_app.root_path, 'static', report.pdf_path)
        if os.path.exists(pdf_full_path):
            os.remove(pdf_full_path)

    db.session.delete(report)
    safe_commit("Тайлан устгагдлаа.", "Тайлан устгахад алдаа гарлаа.")
    return redirect(url_for("pdf_reports.report_list"))


# -------------------------------------------------
# 7. Дараагийн дугаар авах
# -------------------------------------------------
def get_next_report_number(lab_type):
    """Дараагийн тайлангийн дугаар авах."""
    year = now_local().year

    # Сүүлийн тайлангийн дугаар
    last_report = db.session.execute(
        select(LabReport)
        .where(LabReport.report_number.like(f"{year}_%"))
        .order_by(LabReport.id.desc())
        .limit(1)
    ).scalar_one_or_none()

    if last_report:
        try:
            last_num = int(last_report.report_number.split('_')[1])
            return f"{year}_{last_num + 1}"
        except (IndexError, ValueError):
            pass

    # Тоолох
    count = db.session.execute(
        select(func.count(LabReport.id)).where(
            LabReport.report_number.like(f"{year}_%")
        )
    ).scalar_one()

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
        try:
            if date_from_str:
                date_from = datetime.strptime(date_from_str, "%Y-%m-%d").date()
            if date_to_str:
                date_to = datetime.strptime(date_to_str, "%Y-%m-%d").date()
        except ValueError:
            return jsonify({"success": False, "error": "Буруу огнооны формат. YYYY-MM-DD байх ёстой"}), 400

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
        elif lab_type == 'water_chemistry':
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

    except (SQLAlchemyError, ValueError, TypeError, OSError) as e:
        current_app.logger.error(f"Error creating report: {e}", exc_info=True)
        return jsonify({"success": False, "error": "Тайлан үүсгэхэд алдаа гарлаа."}), 500
