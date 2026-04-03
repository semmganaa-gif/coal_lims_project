# app/routes/reports/pdf_generator.py
# -*- coding: utf-8 -*-
"""PDF тайлан үүсгэгч."""

import logging
import os
from datetime import datetime
from io import BytesIO

from flask import render_template, current_app, url_for, request
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

from sqlalchemy.exc import SQLAlchemyError

from app import db
from app.models import LabReport, Sample, AnalysisResult, ReportSignature

# Optional import - xhtml2pdf дутуу байж болно
try:
    from xhtml2pdf import pisa
    XHTML2PDF_AVAILABLE = True
except ImportError:
    pisa = None
    XHTML2PDF_AVAILABLE = False

_logger = logging.getLogger(__name__)

_font_registered = False

def register_fonts():
    """DejaVu font бүртгэх (Кирилл дэмжлэгтэй)."""
    global _font_registered
    if _font_registered:
        return

    try:
        font_path = os.path.join(
            current_app.root_path, 'static', 'fonts', 'DejaVuSans.ttf'
        )
        if os.path.exists(font_path):
            pdfmetrics.registerFont(TTFont('DejaVuSans', font_path))
            _font_registered = True
    except (OSError, ValueError) as e:
        current_app.logger.warning(f"Font registration failed: {e}")


def create_pdf_from_html(html_content, output_path):
    """HTML-ээс PDF үүсгэх."""
    if not XHTML2PDF_AVAILABLE:
        raise RuntimeError("xhtml2pdf модуль суулгаагүй байна. pip install xhtml2pdf")

    register_fonts()

    try:
        with open(output_path, "wb") as pdf_file:
            pisa_status = pisa.CreatePDF(
                html_content,
                dest=pdf_file,
                encoding='utf-8'
            )
    except (OSError, Exception) as e:
        _logger.exception("PDF үүсгэхэд алдаа гарлаа: %s", output_path)
        raise RuntimeError(f"PDF үүсгэхэд алдаа гарлаа: {e}") from e

    if pisa_status.err:
        _logger.error("xhtml2pdf алдаа: %s — файл: %s", pisa_status.err, output_path)
        return False
    return True


def generate_microbiology_report(sample_ids, date_from, date_to, created_by_id):
    """Микробиологийн тайлан үүсгэх."""
    from app.routes.reports.crud import get_next_report_number

    # Дээжүүд татах (microbiology, water & micro дээжүүд)
    samples = Sample.query.filter(
        Sample.id.in_(sample_ids),
        Sample.lab_type.in_(['microbiology', 'water_chemistry'])
    ).order_by(Sample.sample_date, Sample.id).all()

    if not samples:
        return None, "Sample not found"

    # Тайлангийн дугаар
    report_number = get_next_report_number('microbiology')

    # Үр дүн татах
    results_data = []
    for sample in samples:
        results = AnalysisResult.query.filter_by(sample_id=sample.id).all()
        results_data.append({
            'sample': sample,
            'results': {r.analysis_code: r for r in results if r.analysis_code}
        })

    # Тайлангийн өгөгдөл
    report_data = {
        'samples': [s.id for s in samples],
        'sample_names': [s.sample_code for s in samples],
        'date_from': date_from.isoformat() if date_from else None,
        'date_to': date_to.isoformat() if date_to else None,
    }

    # Тайлан үүсгэх
    report = LabReport(
        report_number=report_number,
        lab_type='microbiology',
        report_type='analysis',
        title=f"Микробиологийн шинжилгээний тайлан",
        status='draft',
        sample_ids=sample_ids,
        date_from=date_from,
        date_to=date_to,
        report_data=report_data,
        created_by_id=created_by_id,
    )

    db.session.add(report)
    db.session.flush()

    # PDF үүсгэх
    pdf_path = generate_pdf_file(report, samples, results_data)
    report.pdf_path = pdf_path

    try:
        db.session.commit()
    except SQLAlchemyError as e:
        db.session.rollback()
        _logger.error(f"Microbiology report commit error: {e}")
        return None, "Микробиологийн тайлан хадгалахад алдаа гарлаа."

    return report, None


def generate_water_report(sample_ids, date_from, date_to, created_by_id):
    """Усны химийн тайлан үүсгэх."""
    from app.routes.reports.crud import get_next_report_number

    samples = Sample.query.filter(
        Sample.id.in_(sample_ids),
        Sample.lab_type.in_(['water_chemistry', 'microbiology'])
    ).order_by(Sample.sample_date, Sample.id).all()

    if not samples:
        return None, "Sample not found"

    report_number = get_next_report_number('water_chemistry')

    results_data = []
    for sample in samples:
        results = AnalysisResult.query.filter_by(sample_id=sample.id).all()
        results_data.append({
            'sample': sample,
            'results': {r.analysis_code: r for r in results if r.analysis_code}
        })

    report_data = {
        'samples': [s.id for s in samples],
        'sample_names': [s.sample_code for s in samples],
        'date_from': date_from.isoformat() if date_from else None,
        'date_to': date_to.isoformat() if date_to else None,
    }

    report = LabReport(
        report_number=report_number,
        lab_type='water_chemistry',
        report_type='analysis',
        title=f"Усны химийн шинжилгээний тайлан",
        status='draft',
        sample_ids=sample_ids,
        date_from=date_from,
        date_to=date_to,
        report_data=report_data,
        created_by_id=created_by_id,
    )

    db.session.add(report)
    db.session.flush()

    pdf_path = generate_pdf_file(report, samples, results_data)
    report.pdf_path = pdf_path

    try:
        db.session.commit()
    except SQLAlchemyError as e:
        db.session.rollback()
        _logger.error(f"Water report commit error: {e}")
        return None, "Усны тайлан хадгалахад алдаа гарлаа."

    return report, None


def generate_coal_report(sample_ids, date_from, date_to, created_by_id):
    """Нүүрсний тайлан үүсгэх."""
    from app.routes.reports.crud import get_next_report_number

    samples = Sample.query.filter(
        Sample.id.in_(sample_ids),
        Sample.lab_type == 'coal'
    ).order_by(Sample.sample_date, Sample.id).all()

    if not samples:
        return None, "Sample not found"

    report_number = get_next_report_number('coal')

    results_data = []
    for sample in samples:
        results = AnalysisResult.query.filter_by(sample_id=sample.id).all()
        results_data.append({
            'sample': sample,
            'results': {r.analysis_code: r for r in results if r.analysis_code}
        })

    report_data = {
        'samples': [s.id for s in samples],
        'sample_names': [s.sample_code for s in samples],
        'date_from': date_from.isoformat() if date_from else None,
        'date_to': date_to.isoformat() if date_to else None,
    }

    report = LabReport(
        report_number=report_number,
        lab_type='coal',
        report_type='analysis',
        title=f"Нүүрсний шинжилгээний тайлан",
        status='draft',
        sample_ids=sample_ids,
        date_from=date_from,
        date_to=date_to,
        report_data=report_data,
        created_by_id=created_by_id,
    )

    db.session.add(report)
    db.session.flush()

    pdf_path = generate_pdf_file(report, samples, results_data)
    report.pdf_path = pdf_path

    try:
        db.session.commit()
    except SQLAlchemyError as e:
        db.session.rollback()
        _logger.error(f"Coal report commit error: {e}")
        return None, "Нүүрсний тайлан хадгалахад алдаа гарлаа."

    return report, None


def generate_pdf_file(report, samples, results_data):
    """PDF файл үүсгэх."""
    # PDF хадгалах folder
    upload_folder = os.path.join(
        current_app.root_path, 'static', 'uploads', 'reports'
    )
    os.makedirs(upload_folder, exist_ok=True)

    filename = f"{report.report_number.replace('/', '_')}.pdf"
    filepath = os.path.join(upload_folder, filename)

    # Font path
    font_path = os.path.join(
        current_app.root_path, 'static', 'fonts', 'DejaVuSans.ttf'
    ).replace('\\', '/')

    # Logo paths (optional)
    company_logo = None
    mnas_logo = None
    logo_path = os.path.join(current_app.root_path, 'static', 'images', 'energy_resources_logo.png')
    if os.path.exists(logo_path):
        company_logo = logo_path.replace('\\', '/')
    mnas_path = os.path.join(current_app.root_path, 'static', 'images', 'mnas_logo.png')
    if os.path.exists(mnas_path):
        mnas_logo = mnas_path.replace('\\', '/')

    # HTML template render
    html_content = render_template(
        f"reports/pdf/{report.lab_type}_report.html",
        report=report,
        samples=samples,
        results_data=results_data,
        now=datetime.now(),
        font_path=font_path,
        company_logo=company_logo,
        mnas_logo=mnas_logo,
    )

    # PDF үүсгэх
    create_pdf_from_html(html_content, filepath)

    return f"uploads/reports/{filename}"


def regenerate_pdf(report):
    """Баталгаажуулсан тайлангийн PDF дахин үүсгэх (гарын үсэгтэй)."""
    samples = Sample.query.filter(Sample.id.in_(report.sample_ids or [])).all()

    results_data = []
    for sample in samples:
        results = AnalysisResult.query.filter_by(sample_id=sample.id).all()
        results_data.append({
            'sample': sample,
            'results': {r.analysis_code: r for r in results if r.analysis_code}
        })

    # PDF хадгалах folder
    upload_folder = os.path.join(
        current_app.root_path, 'static', 'uploads', 'reports'
    )
    os.makedirs(upload_folder, exist_ok=True)

    filename = f"{report.report_number.replace('/', '_')}.pdf"
    filepath = os.path.join(upload_folder, filename)

    # Font path
    font_path = os.path.join(
        current_app.root_path, 'static', 'fonts', 'DejaVuSans.ttf'
    ).replace('\\', '/')

    # Logo paths (optional)
    company_logo = None
    mnas_logo = None
    logo_path = os.path.join(current_app.root_path, 'static', 'images', 'energy_resources_logo.png')
    if os.path.exists(logo_path):
        company_logo = logo_path.replace('\\', '/')
    mnas_path = os.path.join(current_app.root_path, 'static', 'images', 'mnas_logo.png')
    if os.path.exists(mnas_path):
        mnas_logo = mnas_path.replace('\\', '/')

    # HTML template render
    html_content = render_template(
        f"reports/pdf/{report.lab_type}_report.html",
        report=report,
        samples=samples,
        results_data=results_data,
        now=datetime.now(),
        font_path=font_path,
        company_logo=company_logo,
        mnas_logo=mnas_logo,
    )

    # PDF үүсгэх
    create_pdf_from_html(html_content, filepath)

    report.pdf_path = f"uploads/reports/{filename}"
    try:
        db.session.commit()
    except SQLAlchemyError as e:
        db.session.rollback()
        _logger.error(f"Regenerate PDF commit error: {e}")
