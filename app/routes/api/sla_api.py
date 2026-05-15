# app/routes/api/sla_api.py
# -*- coding: utf-8 -*-
"""
SLA turnaround tracking API endpoints.

Endpoints:
  GET  /sla/summary     — SLA dashboard статистик
  GET  /sla/overdue      — Хугацаа хэтэрсэн дээжүүд
  GET  /sla/due_soon     — Удахгүй хугацаа дуусах дээжүүд
  POST /sla/assign       — Bulk SLA тохируулах
  POST /sla/set/<id>     — Нэг дээжийн SLA тохируулах
"""

from dataclasses import asdict

from flask import jsonify, request
from flask_login import login_required, current_user
from flask_babel import gettext as _

from app import limiter
from app.services.sla_service import (
    get_sla_summary,
    get_overdue_samples,
    get_due_soon_samples,
    get_on_track_samples,
    bulk_assign_sla,
    get_sla_config_all,
    set_sla_config,
    delete_sla_config,
    set_sample_sla,
)


def register_routes(bp):
    """SLA route-уудыг blueprint дээр бүртгэх."""

    @bp.route("/sla/summary")
    @login_required
    @limiter.limit("60 per minute")
    def sla_summary():
        """SLA dashboard нэгдсэн статистик."""
        lab_type = request.args.get("lab_type", "coal")
        summary = get_sla_summary(lab_type)
        return jsonify({"success": True, "data": asdict(summary)})

    @bp.route("/sla/overdue")
    @login_required
    @limiter.limit("30 per minute")
    def sla_overdue():
        """Хугацаа хэтэрсэн дээжүүд."""
        lab_type = request.args.get("lab_type", "coal")
        limit = min(int(request.args.get("limit", 100)), 500)
        samples = get_overdue_samples(lab_type, limit)
        return jsonify({
            "success": True,
            "data": [asdict(s) for s in samples],
            "count": len(samples),
        })

    @bp.route("/sla/due_soon")
    @login_required
    @limiter.limit("30 per minute")
    def sla_due_soon():
        """Удахгүй хугацаа дуусах дээжүүд."""
        lab_type = request.args.get("lab_type", "coal")
        hours = min(int(request.args.get("hours", 24)), 168)  # max 7 хоног
        samples = get_due_soon_samples(lab_type, hours)
        return jsonify({
            "success": True,
            "data": samples,
            "count": len(samples),
        })

    @bp.route("/sla/on_track")
    @login_required
    @limiter.limit("30 per minute")
    def sla_on_track():
        """Хугацаандаа байгаа дээжүүд."""
        lab_type = request.args.get("lab_type", "coal")
        samples = get_on_track_samples(lab_type)
        return jsonify({
            "success": True,
            "data": samples,
            "count": len(samples),
        })

    @bp.route("/sla/assign", methods=["POST"])
    @login_required
    @limiter.limit("10 per minute")
    def sla_bulk_assign():
        """Active дээжүүдэд SLA автоматаар тохируулах."""
        if getattr(current_user, "role", None) not in ("manager", "admin"):
            return jsonify({"success": False, "message": _("Эрх хүрэлцэхгүй")}), 403

        lab_type = request.args.get("lab_type", "coal")
        count = bulk_assign_sla(lab_type)
        return jsonify({
            "success": True,
            "message": f"{count} дээжинд SLA тохируулагдлаа",
            "data": {"count": count},
        })

    @bp.route("/sla/set/<int:sample_id>", methods=["POST"])
    @login_required
    @limiter.limit("60 per minute")
    def sla_set(sample_id):
        """Нэг дээжийн SLA тохируулах."""
        if getattr(current_user, "role", None) not in ("senior", "manager", "admin"):
            return jsonify({"success": False, "message": _("Эрх хүрэлцэхгүй")}), 403

        data = request.get_json(silent=True) or {}
        sample = set_sample_sla(
            sample_id,
            sla_hours=data.get("sla_hours"),
            priority=data.get("priority"),
        )
        if sample is None:
            return jsonify({"success": False, "message": _("Дээж олдсонгүй")}), 404

        return jsonify({
            "success": True,
            "message": "SLA тохируулагдлаа",
            "data": {
                "sample_id": sample.id,
                "sla_hours": sample.sla_hours,
                "due_date": sample.due_date.strftime("%Y-%m-%d %H:%M") if sample.due_date else None,
                "priority": sample.priority,
            },
        })

    @bp.route("/sla/defaults")
    @login_required
    def sla_defaults():
        """Client бүрийн default SLA цагууд."""
        from app.services.sla_service import DEFAULT_SLA_HOURS, DEFAULT_SLA_FALLBACK
        return jsonify({
            "success": True,
            "data": {
                "defaults": DEFAULT_SLA_HOURS,
                "fallback": DEFAULT_SLA_FALLBACK,
            },
        })

    # ----- SLA Config CRUD -----

    @bp.route("/sla/config")
    @login_required
    def sla_config_list():
        """SLA тохиргооны жагсаалт."""
        from app.services.sla_service import DEFAULT_SLA_HOURS, DEFAULT_SLA_FALLBACK
        configs = get_sla_config_all()
        return jsonify({
            "success": True,
            "data": configs,
            "defaults": DEFAULT_SLA_HOURS,
            "fallback": DEFAULT_SLA_FALLBACK,
        })

    @bp.route("/sla/config", methods=["POST"])
    @login_required
    @limiter.limit("30 per minute")
    def sla_config_save():
        """SLA тохиргоо хадгалах (upsert)."""
        if getattr(current_user, "role", None) not in ("manager", "admin"):
            return jsonify({"success": False, "message": _("Эрх хүрэлцэхгүй")}), 403

        data = request.get_json(silent=True) or {}
        client_name = (data.get("client_name") or "").strip()
        sample_type = (data.get("sample_type") or "").strip()
        hours = data.get("hours")
        description = (data.get("description") or "").strip()

        if not client_name or hours is None:
            return jsonify({"success": False, "message": _("client_name, hours заавал")}), 400

        try:
            hours = int(hours)
            if hours < 1 or hours > 8760:
                raise ValueError
        except (ValueError, TypeError):
            return jsonify({"success": False, "message": _("hours: 1-8760 цаг")}), 400

        set_sla_config(client_name, sample_type, hours, description, current_user.id)
        return jsonify({"success": True, "message": _("SLA тохиргоо хадгалагдлаа")})

    @bp.route("/sla/config/<int:config_id>", methods=["DELETE"])
    @login_required
    @limiter.limit("30 per minute")
    def sla_config_delete(config_id):
        """SLA тохиргоо устгах."""
        if getattr(current_user, "role", None) not in ("manager", "admin"):
            return jsonify({"success": False, "message": _("Эрх хүрэлцэхгүй")}), 403

        if delete_sla_config(config_id):
            return jsonify({"success": True, "message": _("Устгагдлаа")})
        return jsonify({"success": False, "message": _("Олдсонгүй")}), 404
