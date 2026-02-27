# app/routes/reports/email_sender.py
# -*- coding: utf-8 -*-
"""Имэйл илгээх модуль."""

import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from flask import current_app, render_template, flash, redirect, url_for, request
from flask_login import login_required, current_user
from datetime import datetime
from app import db
from app.models import LabReport
from app.utils.database import safe_commit
from app.routes.reports import pdf_reports_bp


def send_report_email(report, recipients, subject=None, body=None):
    """
    Тайлангийн PDF-г имэйлээр илгээх.

    Args:
        report: LabReport instance
        recipients: list of email addresses
        subject: Custom subject (optional)
        body: Custom body (optional)

    Returns:
        (success: bool, error_message: str or None)
    """
    try:
        # SMTP тохиргоо
        smtp_server = current_app.config.get('MAIL_SERVER', 'smtp.gmail.com')
        smtp_port = current_app.config.get('MAIL_PORT', 587)
        smtp_user = current_app.config.get('MAIL_USERNAME')
        smtp_password = current_app.config.get('MAIL_PASSWORD')
        sender_email = current_app.config.get('MAIL_DEFAULT_SENDER', smtp_user)

        if not smtp_user or not smtp_password:
            return False, "SMTP тохиргоо дутуу байна"

        # Имэйл бэлдэх
        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = ', '.join(recipients)
        msg['Subject'] = subject or f"Сорилтын тайлан - {report.report_number}"

        # Body
        if not body:
            body = f"""
Эрхэм хүндэт,

Энэхүү имэйлд "{report.title}" сорилтын тайлан хавсаргав.

Тайлангийн дугаар: {report.report_number}
Огноо: {report.date_from} - {report.date_to}

Асуулт байвал бидэнтэй холбоо барина уу.

Хүндэтгэсэн,
Усны шинжилгээний лаборатори
И-мэйл: laboratory@mmc.mn
            """

        msg.attach(MIMEText(body, 'plain', 'utf-8'))

        # PDF хавсаргах
        if report.pdf_path:
            pdf_full_path = os.path.join(current_app.root_path, 'static', report.pdf_path)
            if os.path.exists(pdf_full_path):
                with open(pdf_full_path, 'rb') as f:
                    part = MIMEBase('application', 'octet-stream')
                    part.set_payload(f.read())
                    encoders.encode_base64(part)
                    filename = f"{report.report_number}.pdf"
                    part.add_header('Content-Disposition', f'attachment; filename="{filename}"')
                    msg.attach(part)

        # Илгээх
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(smtp_user, smtp_password)
            server.send_message(msg)

        return True, None

    except smtplib.SMTPAuthenticationError:
        return False, "SMTP нэвтрэлт амжилтгүй. Нууц үг шалгана уу."
    except smtplib.SMTPException as e:
        return False, f"SMTP алдаа: {str(e)}"
    except Exception as e:
        return False, f"Error: {str(e)}"


# -------------------------------------------------
# Имэйл илгээх route
# -------------------------------------------------
@pdf_reports_bp.route("/<int:id>/send_email", methods=["GET", "POST"])
@login_required
def send_email(id):
    """Тайлан имэйлээр илгээх."""
    if current_user.role not in ["senior", "manager", "admin"]:
        flash("Хандах эрхгүй.", "danger")
        return redirect(url_for("pdf_reports.report_detail", id=id))

    report = LabReport.query.get_or_404(id)

    if report.status not in ['approved', 'sent']:
        flash("Зөвхөн батлагдсан тайланг илгээх боломжтой.", "warning")
        return redirect(url_for("pdf_reports.report_detail", id=id))

    if request.method == "POST":
        recipients_str = request.form.get("recipients", "")
        recipients = [e.strip() for e in recipients_str.split(',') if e.strip()]

        if not recipients:
            flash("Хүлээн авагчийн имэйл хаяг оруулна уу.", "warning")
            return redirect(url_for("pdf_reports.send_email", id=id))

        subject = request.form.get("subject")
        body = request.form.get("body")

        success, error = send_report_email(report, recipients, subject, body)

        if success:
            report.email_sent = True
            report.email_sent_at = datetime.now()
            report.email_recipients = recipients_str
            report.status = 'sent'
            safe_commit("Имэйл амжилттай илгээгдлэн.", "Имэйл статус хадгалахад алдаа гарлаа")
            return redirect(url_for("pdf_reports.report_detail", id=id))
        else:
            flash(f"Имэйл илгээхэд алдаа: {error}", "danger")

    return render_template(
        "reports/send_email.html",
        report=report,
    )
