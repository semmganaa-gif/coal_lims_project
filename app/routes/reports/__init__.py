# app/routes/reports/__init__.py
# -*- coding: utf-8 -*-
"""
Тайлангийн систем - PDF үүсгэх, баталгаажуулах, имэйлээр илгээх.
"""

from flask import Blueprint

pdf_reports_bp = Blueprint("pdf_reports", __name__, url_prefix="/pdf-reports")

# Constants
LAB_TYPES = {
    'coal': 'Нүүрсний лаб',
    'water': 'Усны хими',
    'microbiology': 'Микробиологи',
    'petrography': 'Петрограф',
}

REPORT_STATUSES = {
    'draft': 'Ноорог',
    'pending_approval': 'Хүлээгдэж буй',
    'approved': 'Баталгаажсан',
    'sent': 'Илгээсэн',
}

# Route модулиудыг бүртгэх (import-ийг доод талд байрлуулах - circular import-аас сэргийлэх)
from app.routes.reports import crud  # noqa: E402, F401
from app.routes.reports import pdf_generator  # noqa: E402, F401
from app.routes.reports import email_sender  # noqa: E402, F401
