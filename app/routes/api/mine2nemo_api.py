# app/routes/api/mine2nemo_api.py
# -*- coding: utf-8 -*-
"""Mine2NEMO ProcessControl API endpoint.

Sample Summary хуудаснаас "Mine2NEMO-руу илгээх" товч дарахад дуудагдана.
Role: senior + admin (төв процесст бичих учир).
"""

import logging
from flask import request, jsonify
from flask_login import login_required, current_user

from app import limiter
from app.constants import UserRole
from app.services.mine2nemo_service import is_configured, send_samples_bulk
from app.utils.decorators import role_required

logger = logging.getLogger(__name__)


def register_routes(bp):
    """Mine2NEMO route-уудыг api_bp дээр бүртгэх."""

    @bp.route("/mine2nemo/status")
    @login_required
    def mine2nemo_status():
        """Mine2NEMO config байгаа эсэхийг үзүүлэх (UI button disable хийхэд)."""
        return jsonify({"configured": is_configured()})

    @bp.route("/mine2nemo/send", methods=["POST"])
    @login_required
    @role_required(UserRole.SENIOR.value, UserRole.ADMIN.value)
    @limiter.limit("20 per minute")
    def mine2nemo_send():
        """Сонгосон дээжүүдийг Mine2NEMO-руу илгээх.

        Body:
            {"sample_ids": [123, 124, ...]}

        Response:
            {
                "success_count": 5,
                "failed_count": 1,
                "skipped_count": 2,
                "items": [
                    {"sample_id": 123, "sample_code": "PF211_D1",
                     "success": true, "action": "inserted",
                     "target_table": "QualityPlantFeed", "error": null},
                    ...
                ]
            }
        """
        data = request.get_json(silent=True) or {}
        raw_ids = data.get("sample_ids") or []

        try:
            sample_ids = [int(x) for x in raw_ids if x]
        except (ValueError, TypeError):
            return jsonify({"error": "sample_ids must be list of integers"}), 400

        if not sample_ids:
            return jsonify({"error": "sample_ids хоосон байна"}), 400

        if len(sample_ids) > 100:
            return jsonify({"error": "Нэг удаад 100-аас дээш дээж илгээх боломжгүй"}), 400

        username = getattr(current_user, "username", "unknown")

        bulk = send_samples_bulk(sample_ids, username)

        logger.info(
            "Mine2NEMO bulk send: user=%s total=%d ok=%d fail=%d skip=%d",
            username, len(sample_ids),
            bulk.success_count, bulk.failed_count, bulk.skipped_count,
        )

        return jsonify({
            "success_count": bulk.success_count,
            "failed_count": bulk.failed_count,
            "skipped_count": bulk.skipped_count,
            "items": [
                {
                    "sample_id": r.sample_id,
                    "sample_code": r.sample_code,           # LIMS-ийн нэр
                    "mine2nemo_code": r.mine2nemo_code,     # Mine2NEMO-руу очсон rewritten
                    "success": r.success,
                    "action": r.action,
                    "target_table": r.target_table,
                    "verified": r.verified,
                    "verification": r.verification,
                    "error": r.error,
                }
                for r in bulk.items
            ],
        })
