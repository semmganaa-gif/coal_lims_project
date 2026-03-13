# app/routes/api/report_builder_api.py
# -*- coding: utf-8 -*-
"""
Ad-hoc Report Builder API — build, preview, save, export custom reports.
"""

from flask import request, jsonify, Response
from flask_login import login_required, current_user

from app.routes.api import api_bp
from app.services.report_builder import (
    execute_report,
    export_report_csv,
    export_report_json,
    save_report_template,
    get_report_template,
    list_report_templates,
    delete_report_template,
    get_available_columns,
    get_available_entities,
)


@api_bp.route("/report-builder/entities")
@login_required
def rb_entities():
    """List available entities for reporting."""
    entities = get_available_entities()
    return jsonify(success=True, data=entities)


@api_bp.route("/report-builder/columns/<entity>")
@login_required
def rb_columns(entity):
    """Get available columns for an entity."""
    columns = get_available_columns(entity)
    if not columns:
        return jsonify(success=False, message=f"Unknown entity: {entity}"), 404
    return jsonify(success=True, data=columns)


@api_bp.route("/report-builder/preview", methods=["POST"])
@login_required
def rb_preview():
    """Preview report results (limited to 100 rows)."""
    config = request.json
    if not config:
        return jsonify(success=False, message="Config шаардлагатай"), 400

    # Limit preview rows
    config["limit"] = min(config.get("limit", 100), 100)

    try:
        result = execute_report(config)
        return jsonify(success=True, data=result)
    except ValueError as e:
        return jsonify(success=False, message=str(e)), 400
    except Exception as e:
        return jsonify(success=False, message=f"Query алдаа: {str(e)}"), 500


@api_bp.route("/report-builder/execute", methods=["POST"])
@login_required
def rb_execute():
    """Execute full report query."""
    config = request.json
    if not config:
        return jsonify(success=False, message="Config шаардлагатай"), 400

    try:
        result = execute_report(config)
        return jsonify(success=True, data=result)
    except ValueError as e:
        return jsonify(success=False, message=str(e)), 400
    except Exception as e:
        return jsonify(success=False, message=f"Query алдаа: {str(e)}"), 500


@api_bp.route("/report-builder/export", methods=["POST"])
@login_required
def rb_export():
    """Export report as CSV or JSON."""
    config = request.json
    if not config:
        return jsonify(success=False, message="Config шаардлагатай"), 400

    fmt = config.pop("export_format", "csv")
    report_name = config.get("name", "report")

    try:
        if fmt == "json":
            content = export_report_json(config)
            return Response(
                content, mimetype="application/json",
                headers={"Content-Disposition": f"attachment; filename={report_name}.json"}
            )
        else:
            content = export_report_csv(config)
            return Response(
                content, mimetype="text/csv; charset=utf-8",
                headers={"Content-Disposition": f"attachment; filename={report_name}.csv"}
            )
    except ValueError as e:
        return jsonify(success=False, message=str(e)), 400
    except Exception as e:
        return jsonify(success=False, message=f"Export алдаа: {str(e)}"), 500


# ──────────────────────────────────────────
# Template management
# ──────────────────────────────────────────

@api_bp.route("/report-builder/templates")
@login_required
def rb_template_list():
    """List saved report templates."""
    templates = list_report_templates()
    return jsonify(success=True, data=templates)


@api_bp.route("/report-builder/templates/<name>")
@login_required
def rb_template_get(name):
    """Get a saved report template."""
    template = get_report_template(name)
    if not template:
        return jsonify(success=False, message="Template олдсонгүй"), 404
    return jsonify(success=True, data=template)


@api_bp.route("/report-builder/templates/save", methods=["POST"])
@login_required
def rb_template_save():
    """Save a report template."""
    data = request.json or {}
    name = data.get("name", "").strip()
    config = data.get("config", {})
    description = data.get("description", "")

    if not name:
        return jsonify(success=False, message="Template нэр шаардлагатай"), 400
    if not config:
        return jsonify(success=False, message="Config шаардлагатай"), 400

    template_id = save_report_template(name, config, current_user.id, description)
    return jsonify(success=True, data={"id": template_id},
                   message=f"'{name}' template хадгалагдлаа")


@api_bp.route("/report-builder/templates/<name>/delete", methods=["POST"])
@login_required
def rb_template_delete(name):
    """Delete a report template."""
    if current_user.role not in ("admin", "manager"):
        return jsonify(success=False, message="Эрх хүрэлцэхгүй"), 403

    deleted = delete_report_template(name)
    if deleted:
        return jsonify(success=True, message=f"'{name}' template устгагдлаа")
    return jsonify(success=False, message="Template олдсонгүй"), 404
