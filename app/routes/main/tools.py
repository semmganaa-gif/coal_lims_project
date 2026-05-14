# app/routes/main/tools.py
# -*- coding: utf-8 -*-
"""
Tool pages: Report Builder, Instrument Readings, SLA Dashboard, Workflow Admin.

All backend APIs are in app/routes/api/ — these routes only serve templates.
"""

from flask import render_template
from flask_login import login_required, current_user
from app.constants import UserRole
from app.utils.decorators import role_required
from werkzeug.exceptions import abort


def register_routes(bp):
    """Register tool page routes on main_bp."""

    @bp.route("/report-builder")
    @login_required
    def report_builder():
        """Ad-hoc Report Builder UI."""
        return render_template("report_builder.html", title="Report Builder")

    @bp.route("/instrument-readings")
    @login_required
    @role_required(UserRole.ADMIN.value, UserRole.MANAGER.value, UserRole.SENIOR.value)
    def instrument_readings():
        """Instrument Readings review UI."""
        return render_template("instrument_readings.html", title="Instrument Readings")

    @bp.route("/sla-dashboard")
    @login_required
    def sla_dashboard():
        """SLA Turnaround Dashboard."""
        return render_template("sla_dashboard.html", title="SLA Dashboard")

    @bp.route("/workflow-admin")
    @login_required
    @role_required(UserRole.ADMIN.value, UserRole.MANAGER.value, UserRole.SENIOR.value)
    def workflow_admin():
        """Workflow configuration admin page."""
        return render_template("workflow_admin.html", title="Workflow Configuration")
