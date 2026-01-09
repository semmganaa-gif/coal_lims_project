# -*- coding: utf-8 -*-
"""
ICPMS Integration API Routes

LIMS-ээс ICPMS систем рүү өгөгдөл илгээх API endpoint-ууд.
"""

from flask import request, jsonify, current_app
from flask_login import login_required, current_user

from app import db, limiter
from app.services.icpms_integration import get_icpms_integration, ICPMSIntegrationError


def register_routes(bp):
    """Route-уудыг өгөгдсөн blueprint дээр бүртгэх"""

    # -----------------------------------------------------------
    # 1) ICPMS Холболт шалгах
    # -----------------------------------------------------------
    @bp.route("/icpms/status", methods=["GET"])
    @login_required
    @limiter.limit("30 per minute")
    def icpms_status():
        """
        ICPMS системтэй холболтыг шалгах.

        Returns:
            {"status": "ok/error", "message": str, "url": str}
        """
        icpms = get_icpms_integration()
        result = icpms.check_connection()
        return jsonify(result)

    # -----------------------------------------------------------
    # 2) Дээж ICPMS руу илгээх
    # -----------------------------------------------------------
    @bp.route("/icpms/send", methods=["POST"])
    @login_required
    @limiter.limit("10 per minute")
    def icpms_send_samples():
        """
        Сонгосон дээжүүдийг ICPMS руу илгээх.

        Request Body:
            {
                "sample_ids": [1, 2, 3],
                "include_washability": true
            }

        Returns:
            {"success": bool, "sent_count": int, "errors": list}
        """
        data = request.get_json()

        if not data:
            return jsonify({"success": False, "error": "Request body хоосон байна"}), 400

        sample_ids = data.get('sample_ids', [])
        include_washability = data.get('include_washability', True)

        if not sample_ids:
            return jsonify({"success": False, "error": "sample_ids заавал шаардлагатай"}), 400

        if not isinstance(sample_ids, list):
            return jsonify({"success": False, "error": "sample_ids list байх ёстой"}), 400

        try:
            icpms = get_icpms_integration()

            result = icpms.send_sample_results(
                sample_ids=sample_ids,
                include_washability=include_washability
            )

            # Audit log
            current_app.logger.info(
                f"ICPMS илгээлт: User={current_user.username}, "
                f"Samples={len(sample_ids)}, Sent={result.get('sent_count', 0)}"
            )

            return jsonify(result)

        except ICPMSIntegrationError as e:
            current_app.logger.error(f"ICPMS интеграцийн алдаа: {e}")
            return jsonify({"success": False, "error": str(e)}), 500

        except Exception as e:
            current_app.logger.error(f"ICPMS илгээлтийн алдаа: {e}")
            return jsonify({"success": False, "error": "Серверийн алдаа"}), 500

    # -----------------------------------------------------------
    # 3) CHPP Batch илгээх
    # -----------------------------------------------------------
    @bp.route("/icpms/send-chpp", methods=["POST"])
    @login_required
    @limiter.limit("5 per minute")
    def icpms_send_chpp():
        """
        CHPP нэгжийн сүүлийн үеийн үр дүнг ICPMS руу илгээх.

        Request Body:
            {
                "days_back": 7  (optional, default 7)
            }

        Returns:
            {"success": bool, "sent_count": int, "message": str}
        """
        data = request.get_json() or {}
        days_back = data.get('days_back', 7)

        try:
            icpms = get_icpms_integration()

            result = icpms.send_batch_results(
                client_name='CHPP',
                days_back=days_back,
                status='approved'
            )

            # Audit log
            current_app.logger.info(
                f"ICPMS CHPP илгээлт: User={current_user.username}, "
                f"Days={days_back}, Sent={result.get('sent_count', 0)}"
            )

            return jsonify(result)

        except Exception as e:
            current_app.logger.error(f"ICPMS CHPP илгээлтийн алдаа: {e}")
            return jsonify({"success": False, "error": "Серверийн алдаа"}), 500

    # -----------------------------------------------------------
    # 4) Оновчлолын үр дүн авах
    # -----------------------------------------------------------
    @bp.route("/icpms/optimization/<int:scenario_id>", methods=["GET"])
    @login_required
    @limiter.limit("30 per minute")
    def icpms_get_optimization(scenario_id):
        """
        ICPMS-ээс оновчлолын үр дүн авах.

        Args:
            scenario_id: ICPMS дээрх scenario ID

        Returns:
            Оновчлолын үр дүн
        """
        try:
            icpms = get_icpms_integration()

            result = icpms.get_optimization_result(scenario_id)

            if result:
                return jsonify(result)
            else:
                return jsonify({"error": "Scenario олдсонгүй"}), 404

        except Exception as e:
            current_app.logger.error(f"ICPMS optimization авах алдаа: {e}")
            return jsonify({"error": "Серверийн алдаа"}), 500

    # -----------------------------------------------------------
    # 5) ICPMS тохиргоо авах
    # -----------------------------------------------------------
    @bp.route("/icpms/config", methods=["GET"])
    @login_required
    def icpms_config():
        """
        ICPMS интеграцийн тохиргоо авах (нууц үг хасаад).

        Returns:
            {"url": str, "enabled": bool}
        """
        import os

        url = os.getenv('ICPMS_API_URL', 'http://localhost:8000')
        enabled = bool(os.getenv('ICPMS_API_URL'))

        return jsonify({
            "url": url,
            "enabled": enabled,
            "timeout": int(os.getenv('ICPMS_TIMEOUT', '30'))
        })
