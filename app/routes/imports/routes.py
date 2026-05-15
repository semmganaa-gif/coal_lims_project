# app/routes/imports/routes.py
# -*- coding: utf-8 -*-
"""
Түүхэн CSV импорт — thin route layer.

Business logic is in app.services.import_service.
"""

import logging

from flask import Blueprint, render_template, request, flash, redirect, url_for
from flask_login import login_required
from flask_babel import lazy_gettext as _l
from sqlalchemy.exc import SQLAlchemyError

from app import db
from app.constants import UserRole
from app.utils.decorators import role_required
from app.services.import_service import process_csv_import

logger = logging.getLogger(__name__)

import_bp = Blueprint("importer", __name__, url_prefix="/admin/import")


@import_bp.route("/historical_csv", methods=["GET", "POST"])
@login_required
@role_required(UserRole.ADMIN.value)
def import_historical_csv():
    if request.method == "GET":
        return render_template("admin/import_historical.html", title="Түүхэн CSV импорт")

    # --- POST: handle file upload ---
    file = request.files.get("file")
    dry_run = request.form.get("dry_run") == "on"
    try:
        batch_size = min(int(request.form.get("batch_size") or 1000), 5000)
    except (ValueError, TypeError):
        batch_size = 1000

    if not file or file.filename == "":
        flash(_l("Файл сонгогдоогүй байна."), "danger")
        return redirect(url_for("importer.import_historical_csv"))

    raw = file.read()

    try:
        summary, errors = process_csv_import(raw, dry_run=dry_run, batch_size=batch_size)
    except ValueError as ve:
        flash(str(ve), "danger")
        return redirect(url_for("importer.import_historical_csv"))
    except SQLAlchemyError as db_err:
        db.session.rollback()
        logger.error("CSV import DB error: %s", db_err, exc_info=True)
        flash(_l("Мэдээллийн сан бичих алдаа гарлаа."), "danger")
        return redirect(url_for("importer.import_historical_csv"))

    return render_template(
        "admin/import_historical.html",
        title="Түүхэн CSV импорт",
        summary=summary,
        errors=errors[:200],
    )
