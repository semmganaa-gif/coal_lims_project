# app/routes/api/instrument_api.py
# -*- coding: utf-8 -*-
"""
Instrument reading API endpoints — import, review, approve/reject.
"""

import os
import tempfile

from flask import request, jsonify
from flask_login import login_required, current_user
from flask_babel import gettext as _
from werkzeug.utils import secure_filename

from app.routes.api import api_bp
from app.services.instrument_service import (
    import_instrument_file,
    get_pending_readings,
    approve_reading,
    reject_reading,
    bulk_approve,
    bulk_reject,
    get_reading_stats,
    get_supported_instruments,
)


@api_bp.route("/instrument/upload", methods=["POST"])
@login_required
def instrument_upload():
    """Upload and parse an instrument output file."""
    if current_user.role not in ("admin", "manager", "senior_analyst"):
        return jsonify(success=False, message=_("Эрх хүрэлцэхгүй")), 403

    file = request.files.get("file")
    instrument_type = request.form.get("instrument_type", "generic_csv")
    instrument_name = request.form.get("instrument_name", "")

    if not file or not file.filename:
        return jsonify(success=False, message=_("Файл сонгоогүй")), 400

    filename = secure_filename(file.filename)
    tmp_dir = tempfile.mkdtemp()
    tmp_path = os.path.join(tmp_dir, filename)

    try:
        file.save(tmp_path)
        count = import_instrument_file(tmp_path, instrument_type, instrument_name)
        return jsonify(success=True, data={"count": count},
                       message=f"{count} хэмжилт амжилттай импортлогдлоо")
    except ValueError as e:
        return jsonify(success=False, message=str(e)), 400
    finally:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)
        if os.path.exists(tmp_dir):
            os.rmdir(tmp_dir)


@api_bp.route("/instrument/pending")
@login_required
def instrument_pending():
    """Get pending readings for review."""
    instrument_type = request.args.get("instrument_type")
    limit = min(int(request.args.get("limit", 100)), 500)

    readings = get_pending_readings(instrument_type, limit)
    data = []
    for r in readings:
        data.append({
            "id": r.id,
            "instrument_name": r.instrument_name,
            "instrument_type": r.instrument_type,
            "sample_code": r.sample_code,
            "analysis_code": r.analysis_code,
            "parsed_value": r.parsed_value,
            "unit": r.unit,
            "source_file": os.path.basename(r.source_file or ""),
            "status": r.status,
            "created_at": r.created_at.isoformat() if r.created_at else None,
        })
    return jsonify(success=True, data=data)


@api_bp.route("/instrument/approve/<int:reading_id>", methods=["POST"])
@login_required
def instrument_approve(reading_id):
    """Approve a single reading."""
    if current_user.role not in ("admin", "manager", "senior_analyst"):
        return jsonify(success=False, message=_("Эрх хүрэлцэхгүй")), 403

    try:
        reading = approve_reading(reading_id, current_user.id)
        return jsonify(success=True, message=f"Reading {reading.id} approved",
                       data={"id": reading.id, "status": reading.status})
    except ValueError as e:
        return jsonify(success=False, message=str(e)), 400


@api_bp.route("/instrument/reject/<int:reading_id>", methods=["POST"])
@login_required
def instrument_reject(reading_id):
    """Reject a single reading."""
    if current_user.role not in ("admin", "manager", "senior_analyst"):
        return jsonify(success=False, message=_("Эрх хүрэлцэхгүй")), 403

    reason = (request.json or {}).get("reason", "")
    try:
        reading = reject_reading(reading_id, current_user.id, reason)
        return jsonify(success=True, message=f"Reading {reading.id} rejected",
                       data={"id": reading.id, "status": reading.status})
    except ValueError as e:
        return jsonify(success=False, message=str(e)), 400


@api_bp.route("/instrument/bulk-approve", methods=["POST"])
@login_required
def instrument_bulk_approve():
    """Approve multiple readings."""
    if current_user.role not in ("admin", "manager", "senior_analyst"):
        return jsonify(success=False, message=_("Эрх хүрэлцэхгүй")), 403

    ids = (request.json or {}).get("ids", [])
    if not ids or len(ids) > 500:
        return jsonify(success=False, message=_("1-500 хэмжилт сонгоно уу")), 400

    count = bulk_approve(ids, current_user.id)
    return jsonify(success=True, data={"approved": count},
                   message=f"{count} хэмжилт зөвшөөрөгдлөө")


@api_bp.route("/instrument/bulk-reject", methods=["POST"])
@login_required
def instrument_bulk_reject():
    """Reject multiple readings."""
    if current_user.role not in ("admin", "manager", "senior_analyst"):
        return jsonify(success=False, message=_("Эрх хүрэлцэхгүй")), 403

    data = request.json or {}
    ids = data.get("ids", [])
    reason = data.get("reason", "")
    if not ids or len(ids) > 500:
        return jsonify(success=False, message=_("1-500 хэмжилт сонгоно уу")), 400

    count = bulk_reject(ids, current_user.id, reason)
    return jsonify(success=True, data={"rejected": count},
                   message=f"{count} хэмжилт татгалзагдлаа")


@api_bp.route("/instrument/stats")
@login_required
def instrument_stats():
    """Get instrument reading statistics."""
    stats = get_reading_stats()
    return jsonify(success=True, data=stats)


@api_bp.route("/instrument/types")
@login_required
def instrument_types():
    """List supported instrument types."""
    types = get_supported_instruments()
    return jsonify(success=True, data=types)
