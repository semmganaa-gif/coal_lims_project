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
from app.utils.datetime import now_local
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


def generate_water_coa(sample_id: int, created_by_id: int):
    """
    Нэг дээжийн хими + микробиологийн нэгдсэн CoA PDF үүсгэх.

    Args:
        sample_id:       CoA гаргах Sample.id
        created_by_id:   Үүсгэж буй хэрэглэгч

    Returns:
        (LabReport | None, error_message | None)
    """
    from app.routes.reports.crud import get_next_report_number
    from app.labs.water_lab.chemistry.constants import ALL_WATER_PARAMS

    sample = Sample.query.get(sample_id)
    if not sample:
        return None, 'Дээж олдсонгүй'

    # ── Бүх үр дүн (хими + микро) ──
    all_results = AnalysisResult.query.filter_by(sample_id=sample_id).all()
    results_by_code = {r.analysis_code: r for r in all_results}

    # ── Химийн үр дүнгийн мөрүүд ──
    chem_rows = []
    for code, param in ALL_WATER_PARAMS.items():
        ar = results_by_code.get(code)
        if not ar or ar.status not in ('approved', 'pending_review'):
            continue
        result_val = ar.final_result
        limit = param.get('mns_limit')
        pass_fail = None
        if result_val is not None and limit:
            if isinstance(limit, (list, tuple)):
                lo, hi = limit[0], limit[1]
                ok = True
                if lo is not None and result_val < lo:
                    ok = False
                if hi is not None and result_val > hi:
                    ok = False
                pass_fail = ok
            else:
                pass_fail = result_val <= float(limit)
        chem_rows.append({
            'code': code,
            'name_mn': param.get('name_mn', code),
            'unit': param.get('unit', ''),
            'limit': limit,
            'standard': param.get('standard', 'MNS 4586:2007'),
            'result': result_val,
            'pass_fail': pass_fail,
        })

    # ── Микробиологийн үр дүнгийн мөрүүд ──
    # (field_key, name_mn, unit, limit_hi, is_presence)
    MICRO_FIELDS = {
        'MICRO_WATER': [
            ('cfu_22', 'КҮБ (22°C)', 'КҮБ/мл', 100, False),
            ('cfu_37', 'КҮБ (37°C)', 'КҮБ/мл', 100, False),
            ('ecoli', 'E.coli', 'КҮБ/100мл', None, True),
            ('salmonella', 'Сальмонелла', 'КҮБ/25мл', None, True),
        ],
        'MICRO_AIR': [
            ('cfu_air', 'КҮБ (агаар)', 'КҮБ/м³', 3000, False),
            ('staphylococcus', 'Стафилококк (S.aureus)', 'КҮБ/м³', 50, False),
            ('mold_fungi', 'Мөөгөнцөр', 'КҮБ/м³', 500, False),
        ],
        'MICRO_SWAB': [
            ('cfu_swab', 'КҮБ (арчдас)', 'КҮБ/50см²', 100, False),
            ('ecoli_swab', 'E.coli (арчдас)', '—', None, True),
            ('salmonella_swab', 'Сальмонелла (арчдас)', '—', None, True),
            ('staphylococcus_swab', 'S.aureus (арчдас)', '—', None, True),
        ],
    }
    _PRESENCE_DETECTED = ('detected', 'илэрсэн')

    micro_rows = []
    for micro_code, fields in MICRO_FIELDS.items():
        ar = results_by_code.get(micro_code)
        if not ar or ar.status not in ('approved', 'pending_review'):
            continue
        import json as _json
        raw = {}
        if ar.raw_data:
            try:
                raw = _json.loads(ar.raw_data)
            except (ValueError, TypeError):
                raw = {}

        for field_key, field_name, unit, limit_hi, is_presence in fields:
            val = raw.get(field_key)
            if val is None:
                continue

            pass_fail = None
            limit_str = None

            if is_presence:
                # Pass = Not Detected
                limit_str = 'Илрэхгүй'
                pass_fail = str(val).lower() not in _PRESENCE_DETECTED
            else:
                try:
                    val_f = float(val)
                    if limit_hi is not None:
                        pass_fail = val_f <= limit_hi
                        limit_str = f'≤ {limit_hi}'
                    val = val_f
                except (TypeError, ValueError):
                    pass

            micro_rows.append({
                'name_mn': field_name,
                'unit': unit,
                'limit_str': limit_str,
                'result': val,
                'pass_fail': pass_fail,
            })

    if not chem_rows and not micro_rows:
        return None, 'Батлагдсан шинжилгээний үр дүн олдсонгүй'

    # ── LabReport бүртгэл ──
    report_number = get_next_report_number('water_chemistry')
    report_data = {
        'sample_id': sample_id,
        'sample_code': sample.sample_code,
        'chem_count': len(chem_rows),
        'micro_count': len(micro_rows),
    }

    report = LabReport(
        report_number=report_number,
        lab_type='water_chemistry',
        report_type='coa',
        title=f'Усны шинжилгээний дүгнэлт — {sample.sample_code}',
        status='draft',
        sample_ids=[sample_id],
        date_from=sample.sample_date,
        date_to=sample.sample_date,
        report_data=report_data,
        created_by_id=created_by_id,
    )
    db.session.add(report)
    db.session.flush()

    # ── PDF үүсгэх ──
    upload_folder = os.path.join(current_app.root_path, 'static', 'uploads', 'reports')
    os.makedirs(upload_folder, exist_ok=True)
    filename = f"COA_{report.report_number.replace('/', '_')}.pdf"
    filepath = os.path.join(upload_folder, filename)

    font_path = os.path.join(current_app.root_path, 'static', 'fonts', 'DejaVuSans.ttf').replace('\\', '/')
    company_logo = None
    logo_path = os.path.join(current_app.root_path, 'static', 'images', 'energy_resources_logo.png')
    if os.path.exists(logo_path):
        company_logo = logo_path.replace('\\', '/')

    html_content = render_template(
        'reports/pdf/water_coa.html',
        report=report,
        sample=sample,
        chem_results=chem_rows,
        micro_results=micro_rows,
        now=now_local(),
        font_path=font_path,
        company_logo=company_logo,
    )

    try:
        create_pdf_from_html(html_content, filepath)
        report.pdf_path = f'uploads/reports/{filename}'
    except Exception as e:
        _logger.error('CoA PDF үүсгэх алдаа: %s', e)
        report.pdf_path = None

    try:
        db.session.commit()
    except SQLAlchemyError as e:
        db.session.rollback()
        _logger.error('CoA commit алдаа: %s', e)
        return None, 'CoA хадгалахад алдаа гарлаа'

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
        now=now_local(),
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
        now=now_local(),
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
