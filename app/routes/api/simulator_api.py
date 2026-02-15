# app/routes/api/simulator_api.py
# -*- coding: utf-8 -*-
"""
CHPP Simulator руу мэдээлэл илгээх API endpoints:
  - /send_to_simulator/chpp/<sample_id>  → Feed quality илгээх
  - /send_to_simulator/wtl/<lab_number>  → WTL washability илгээх
"""

import logging
import requests
from flask import request, jsonify, current_app
from flask_login import login_required, current_user

from app import db
from app.models import Sample, AnalysisResult

logger = logging.getLogger(__name__)

# LIMS-ийн бүх шинжилгээний кодууд (Simulator руу бүгдийг илгээнэ)
_ALL_ANALYSIS_CODES = {
    "MT", "Mad", "Aad", "Vad", "TS", "CV",
    "CSN", "Gi", "TRD", "P", "F", "Cl",
    "X", "Y", "CRI", "CSR", "FM", "SOLID", "m", "PE",
}

# WTL size class нэрнүүд (sample_code parse хийхэд)
_WTL_SIZE_CLASSES = ["+16.0", "16.0-8.0", "8.0-4.0", "4.0-2.0", "2.0-0.5"]

# WTL density labels
_WTL_DENSITIES = {
    "F1.300": 1.300, "F1.350": 1.350, "F1.400": 1.400, "F1.450": 1.450,
    "F1.500": 1.500, "F1.550": 1.550, "F1.600": 1.600, "F1.650": 1.650,
    "F1.700": 1.700, "F1.750": 1.750, "F1.800": 1.800, "F1.900": 1.900,
    "F2.000": 2.000, "Sink": 2.200,
}


def _get_simulator_url():
    """Simulator URL-г config-оос авах."""
    return current_app.config.get("SIMULATOR_URL", "http://localhost:8000")


def register_routes(bp):
    """Route-уудыг өгөгдсөн blueprint дээр бүртгэх."""

    @bp.route("/send_to_simulator/chpp/<int:sample_id>", methods=["POST"])
    @login_required
    def send_chpp_to_simulator(sample_id):
        """Баталсан CHPP дээжний үр дүнг Simulator руу илгээх.

        1. Sample + approved AnalysisResult-ууд авах
        2. analyses dict бүрдүүлэх: {code: value}
        3. POST → SIMULATOR_URL/api/v1/lims/receive/chpp
        4. Амжилттай бол хариу буцаах
        """
        sample = db.session.get(Sample, sample_id)
        if not sample:
            return jsonify({"error": "Sample not found"}), 404

        # Зөвхөн CHPP client-ийн дээж
        if sample.client_name != "CHPP":
            return jsonify({"error": "Only CHPP samples can be sent"}), 400

        # Approved шинжилгээний үр дүнгүүд авах
        results = AnalysisResult.query.filter_by(
            sample_id=sample_id,
            status="approved",
        ).all()

        if not results:
            return jsonify({"error": "No approved analysis results found"}), 400

        # analyses dict бүрдүүлэх (бүх шинжилгээ)
        analyses = {}
        for r in results:
            if r.analysis_code in _ALL_ANALYSIS_CODES and r.final_result is not None:
                analyses[r.analysis_code] = r.final_result

        if not analyses:
            return jsonify({"error": "No analysis results to send"}), 400

        # Payload бүрдүүлэх
        payload = {
            "source": "lims",
            "client_name": "CHPP",
            "samples": [
                {
                    "sample_code": sample.sample_code,
                    "sample_type": (sample.sample_type or "").replace(" ", "_").lower(),
                    "module_name": None,  # TODO: sample-аас module тодорхойлох
                    "analyses": analyses,
                }
            ],
        }

        # Simulator руу илгээх
        url = f"{_get_simulator_url()}/api/v1/lims/receive/chpp"
        try:
            resp = requests.post(url, json=payload, timeout=10)
            resp.raise_for_status()
            data = resp.json()
            logger.info(
                f"CHPP data sent to simulator: sample={sample.sample_code}, "
                f"user={current_user.username}, response={data.get('status')}"
            )
            return jsonify({
                "success": True,
                "message": f"Sent to Simulator successfully ({len(analyses)} шинжилгээ)",
                "simulator_response": data,
            })
        except requests.ConnectionError:
            logger.error(f"Simulator холболт амжилтгүй: {url}")
            return jsonify({"error": "Could not connect to Simulator server"}), 502
        except requests.Timeout:
            logger.error(f"Simulator timeout: {url}")
            return jsonify({"error": "Simulator server response timed out"}), 504
        except requests.HTTPError as e:
            logger.error(f"Simulator HTTP error: {e.response.status_code} - {e.response.text}")
            return jsonify({"error": f"Simulator error: {e.response.status_code}"}), 502

    @bp.route("/send_to_simulator/wtl/<lab_number>", methods=["POST"])
    @login_required
    def send_wtl_to_simulator(lab_number):
        """WTL washability бүх fraction-ийг Simulator руу илгээх.

        1. lab_number-ээр WTL samples бүгдийг авах (70 ширхэг)
        2. sample_code parse → size_class + density
        3. AnalysisResult-аас mass, ash, sulfur, vm авах
        4. POST → SIMULATOR_URL/api/v1/lims/receive/wtl
        """
        # WTL client-ийн дээжүүд lab_number-ээр
        samples = Sample.query.filter(
            Sample.client_name == "WTL",
            Sample.sample_code.like(f"%{lab_number}%"),
        ).all()

        if not samples:
            return jsonify({"error": f"WTL sample not found: {lab_number}"}), 404

        # Бүх дээжний approved шинжилгээ шалгах
        fractions = []
        unapproved = []

        for sample in samples:
            results = AnalysisResult.query.filter_by(
                sample_id=sample.id,
                status="approved",
            ).all()

            # Шинжилгээний үр дүнгээс fraction бүрдүүлэх
            result_map = {}
            for r in results:
                if r.final_result is not None:
                    result_map[r.analysis_code] = r.final_result

            # Бүх шинжилгээ approved биш бол тэмдэглэх
            all_results = AnalysisResult.query.filter_by(sample_id=sample.id).all()
            if any(r.status != "approved" for r in all_results):
                unapproved.append(sample.sample_code)
                continue

            # sample_code-оос size_class, density parse
            size_class, density = _parse_wtl_sample_code(sample.sample_code)
            if size_class is None or density is None:
                logger.warning(f"WTL sample_code parse алдаа: {sample.sample_code}")
                continue

            fractions.append({
                "size_class": size_class,
                "density": density,
                "mass_pct": result_map.get("mass_pct", result_map.get("Mass", 0)),
                "ash_pct": result_map.get("Aad", 0),
                "sulfur_pct": result_map.get("TS", 0),
                "vm_pct": result_map.get("Vad", 0),
            })

        if unapproved:
            return jsonify({
                "error": f"Not all samples approved: {', '.join(unapproved[:5])}",
            }), 400

        if not fractions:
            return jsonify({"error": "No fractions found to send"}), 400

        # Sample date авах
        sample_date = None
        if samples and samples[0].sample_date:
            sample_date = str(samples[0].sample_date)

        # Payload
        payload = {
            "source": "lims",
            "client_name": "WTL",
            "lab_number": lab_number,
            "sample_date": sample_date,
            "fractions": fractions,
        }

        # Simulator руу илгээх
        url = f"{_get_simulator_url()}/api/v1/lims/receive/wtl"
        try:
            resp = requests.post(url, json=payload, timeout=15)
            resp.raise_for_status()
            data = resp.json()
            logger.info(
                f"WTL data sent to simulator: lab={lab_number}, "
                f"fractions={len(fractions)}, user={current_user.username}, "
                f"washability_set_id={data.get('washability_set_id')}"
            )
            return jsonify({
                "success": True,
                "message": f"Sent to Simulator successfully ({len(fractions)} fraction)",
                "simulator_response": data,
            })
        except requests.ConnectionError:
            logger.error(f"Simulator холболт амжилтгүй: {url}")
            return jsonify({"error": "Could not connect to Simulator server"}), 502
        except requests.Timeout:
            logger.error(f"Simulator timeout: {url}")
            return jsonify({"error": "Simulator server response timed out"}), 504
        except requests.HTTPError as e:
            logger.error(f"Simulator HTTP error: {e.response.status_code} - {e.response.text}")
            return jsonify({"error": f"Simulator error: {e.response.status_code}"}), 502


def _parse_wtl_sample_code(sample_code: str) -> tuple:
    """WTL sample_code-оос size_class болон density задлах.

    Жишээ sample_code формат: "BN-112/+16.0/F1.300"
    → size_class="+16.0", density=1.300

    Returns:
        (size_class, density) tuple, эсвэл (None, None) хэрэв parse амжилтгүй
    """
    parts = sample_code.split("/")
    if len(parts) < 3:
        return None, None

    size_part = parts[1]  # "+16.0" or "+8.0" etc.
    density_part = parts[2]  # "F1.300" or "Sink"

    # Size class тодорхойлох
    size_class = None
    for sc in _WTL_SIZE_CLASSES:
        # "+16.0" → "+16.0", "+8.0" → "16.0-8.0" гэх мэт
        if size_part in sc or sc.startswith(size_part.lstrip("+")):
            size_class = sc
            break
    # Шууд тохирвол
    if size_class is None and size_part in _WTL_SIZE_CLASSES:
        size_class = size_part
    # "+" prefix-тэй бол тохируулах
    if size_class is None:
        stripped = size_part.lstrip("+")
        for sc in _WTL_SIZE_CLASSES:
            if sc.startswith(f"+{stripped}") or sc.startswith(stripped):
                size_class = sc
                break

    # Density тодорхойлох
    density = _WTL_DENSITIES.get(density_part)

    return size_class, density
