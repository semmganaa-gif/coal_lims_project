# app/routes/api/mass_api.py
# -*- coding: utf-8 -*-
"""
Массын ажлын талбартай холбоотой API endpoints.

Бизнес логик mass_service.py-д, route layer зөвхөн HTTP concerns хариуцна.
"""

from flask import request, jsonify, url_for, redirect
from flask_login import login_required, current_user

from app import limiter
from app.constants import UserRole
from app.services.mass_service import (
    update_sample_status,
    get_eligible_samples,
    save_mass_measurements,
    update_weight,
    unready_samples,
    delete_sample,
)
from app.utils.decorators import role_required
from .helpers import api_success, api_error


def register_routes(bp):
    """Route-уудыг өгөгдсөн blueprint дээр бүртгэх"""

    @bp.route("/mass/update_sample_status", methods=["POST"])
    @login_required
    @limiter.limit("100 per minute")
    async def mass_update_sample_status():
        action = request.form.get("action")
        sample_ids_raw = request.form.getlist("sample_ids")
        is_ajax = request.headers.get("X-Requested-With") == "XMLHttpRequest"

        try:
            sample_ids = [int(sid) for sid in sample_ids_raw]
        except ValueError:
            sample_ids = []

        result = update_sample_status(sample_ids, action)

        if is_ajax:
            if result.success:
                return jsonify({"message": result.message}), 200
            return jsonify({"message": result.message}), result.status_code

        return redirect(url_for("api.sample_summary"))

    @bp.route("/mass/eligible", methods=["GET"])
    @login_required
    @limiter.limit("100 per minute")
    async def mass_eligible():
        include_ready = request.args.get("include_ready", "0") in ("1", "true", "True")
        q_text = (request.args.get("q") or "").strip()

        samples = get_eligible_samples(include_ready=include_ready, q_text=q_text)
        return jsonify({"samples": samples})

    @bp.route("/mass/save", methods=["POST"])
    @login_required
    @limiter.limit("100 per minute")
    async def mass_save():
        data = request.get_json(silent=True) or {}
        items = data.get("items") or []
        mark_ready = bool(data.get("mark_ready", True))
        user_id = getattr(current_user, "id", None)

        result = save_mass_measurements(items, mark_ready=mark_ready, user_id=user_id)

        if result.success:
            return api_success(result.data, result.message)
        return api_error(result.message, status_code=result.status_code)

    @bp.route("/mass/update_weight", methods=["POST"])
    @login_required
    @limiter.limit("100 per minute")
    async def mass_update_weight():
        data = request.get_json(silent=True) or {}
        sid = data.get("sample_id")
        w = data.get("weight")

        if not sid or not isinstance(w, (int, float)):
            return api_error("Missing parameter.")

        user_id = getattr(current_user, "id", None)
        result = update_weight(sid, float(w), user_id=user_id)

        if result.success:
            return api_success(result.data, result.message)
        return api_error(result.message, status_code=result.status_code)

    @bp.route("/mass/unready", methods=["POST"])
    @login_required
    @limiter.limit("100 per minute")
    async def mass_unready():
        data = request.get_json(silent=True) or {}
        ids = data.get("sample_ids") or []

        result = unready_samples(ids)

        if result.success:
            return api_success(None, result.message)
        return api_error(result.message, status_code=result.status_code)

    @bp.route("/mass/delete", methods=["POST"])
    @login_required
    @role_required(UserRole.SENIOR.value, UserRole.ADMIN.value)
    @limiter.limit("100 per minute")
    async def mass_delete():
        data = request.get_json(silent=True) or {}
        sid = data.get("sample_id")

        if not sid:
            return api_error("ID missing.")

        user_id = getattr(current_user, "id", None)
        result = delete_sample(sid, user_id=user_id)

        if result.success:
            return api_success(result.data, result.message)
        return api_error(result.message, status_code=result.status_code)
