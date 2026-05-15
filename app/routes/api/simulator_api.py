# app/routes/api/simulator_api.py
# -*- coding: utf-8 -*-
"""
CHPP Simulator руу мэдээлэл илгээх API endpoints:
  - /send_to_simulator/chpp/<sample_id>  → Feed quality илгээх
  - /send_to_simulator/wtl/<lab_number>  → WTL бүх дээжийг илгээх
"""

import logging
import requests
from flask import request, jsonify, current_app
from flask_login import login_required, current_user
from flask_babel import gettext as _

from sqlalchemy import select

from app import db
from app.constants import AnalysisResultStatus
from app.models import Sample, AnalysisResult
from app.utils.security import escape_like_pattern

logger = logging.getLogger(__name__)

# LIMS-ийн бүх шинжилгээний кодууд (Simulator руу бүгдийг илгээнэ)
_ALL_ANALYSIS_CODES = {
    "MT", "Mad", "Aad", "Vad", "TS", "CV",
    "CSN", "Gi", "TRD", "P", "F", "Cl",
    "X", "Y", "CRI", "CSR", "FM", "SOLID", "m", "PE",
}

# WTL density labels (бодит DB формат)
_WTL_DENSITIES = {
    "_F1.300": 1.300, "_F1.325": 1.325, "_F1.350": 1.350, "_F1.375": 1.375,
    "_F1.400": 1.400, "_F1.425": 1.425, "_F1.450": 1.450,
    "_F1.50": 1.500, "_F1.60": 1.600, "_F1.70": 1.700,
    "_F1.80": 1.800, "_F2.0": 2.000, "_F2.2": 2.200, "_S2.2": 2.200,
}


def _get_simulator_url():
    """Simulator URL-г config-оос авах."""
    return current_app.config.get("SIMULATOR_URL", "http://localhost:8000")


def _get_approved_results(sample_id):
    """Дээжний approved шинжилгээний үр дүнг dict-ээр буцаах."""
    results = list(db.session.execute(
        select(AnalysisResult).where(
            AnalysisResult.sample_id == sample_id,
            AnalysisResult.status == AnalysisResultStatus.APPROVED.value,
        )
    ).scalars().all())
    return {r.analysis_code: r.final_result for r in results if r.final_result is not None}


def _classify_wtl_sample(sample_code):
    """WTL sample_code-г ангилах.

    Returns:
        (category, size_class, density) tuple
        category: 'fraction' | 'dry_screen' | 'wet_screen' | 'composite'
    """
    parts = sample_code.split("/")

    # Фракц: "26_01_/+16.0/_F1.300" (3 part)
    if len(parts) == 3:
        size_class = parts[1]       # "+16.0"
        density_part = parts[2]     # "_F1.300"
        density = _WTL_DENSITIES.get(density_part)
        return "fraction", size_class, density

    # DRY/WET шигшүүр: "26_01_DRY_/+16.0" (2 part)
    if len(parts) == 2:
        lab_prefix = parts[0]       # "26_01_DRY_" or "26_01_WET_"
        size_class = parts[1]       # "+16.0"
        if "DRY" in lab_prefix.upper():
            return "dry_screen", size_class, None
        elif "WET" in lab_prefix.upper():
            return "wet_screen", size_class, None

    # 1 part: "26_01_C1", "26_01_COMP", "26_01_INITIAL", "26_01_T1"
    if len(parts) == 1:
        suffix = parts[0].rsplit("_", 1)[-1].upper()  # C1, COMP, INITIAL, T1
        # C1-C4, T1-T2 → flotation
        if suffix.startswith("C") and suffix[1:].isdigit():
            return "flotation", None, None
        if suffix.startswith("T") and suffix[1:].isdigit():
            return "flotation", None, None
        return "composite", None, None

    return "unknown", None, None


def _send_to_simulator(url, payload, timeout=15):
    """Simulator руу POST илгээх, алдаа handle хийх."""
    try:
        resp = requests.post(url, json=payload, timeout=timeout)
        resp.raise_for_status()
        return resp.json(), None
    except requests.ConnectionError:
        logger.error(f"Simulator холболт амжилтгүй: {url}")
        return None, "Симулятор сервертэй холбогдож чадсангүй"
    except requests.Timeout:
        logger.error(f"Simulator timeout: {url}")
        return None, "Симулятор серверийн хариу хугацаа хэтэрсэн"
    except requests.HTTPError as e:
        logger.error(f"Simulator HTTP error: {e.response.status_code} - {e.response.text}")
        return None, f"Симулятор алдаа: {e.response.status_code}"


def register_routes(bp):
    """Route-уудыг өгөгдсөн blueprint дээр бүртгэх."""

    @bp.route("/send_to_simulator/chpp/<int:sample_id>", methods=["POST"])
    @login_required
    def send_chpp_to_simulator(sample_id):
        """Баталсан CHPP дээжний үр дүнг Simulator руу илгээх."""
        sample = db.session.get(Sample, sample_id)
        if not sample:
            return jsonify({"error": _("Дээж олдсонгүй")}), 404

        if sample.client_name != "CHPP":
            return jsonify({"error": _("Зөвхөн CHPP дээжийг илгээх боломжтой")}), 400

        result_map = _get_approved_results(sample_id)
        analyses = {k: v for k, v in result_map.items() if k in _ALL_ANALYSIS_CODES}

        if not analyses:
            return jsonify({"error": _("Баталгаажсан шинжилгээний үр дүн олдсонгүй")}), 400

        payload = {
            "source": "lims",
            "client_name": "CHPP",
            "samples": [{
                "sample_code": sample.sample_code,
                "sample_type": (sample.sample_type or "").replace(" ", "_").lower(),
                "module_name": None,
                "analyses": analyses,
            }],
        }

        url = f"{_get_simulator_url()}/api/v1/lims/receive/chpp"
        data, err = _send_to_simulator(url, payload, timeout=10)
        if err:
            return jsonify({"error": err}), 502

        logger.info(
            f"CHPP data sent: sample={sample.sample_code}, "
            f"user={current_user.username}, analyses={len(analyses)}"
        )
        return jsonify({
            "success": True,
            "message": f"Симулятор руу амжилттай илгээгдлэн ({len(analyses)} шинжилгээ)",
            "simulator_response": data,
        })

    @bp.route("/send_to_simulator/wtl/<lab_number>", methods=["POST"])
    @login_required
    def send_wtl_to_simulator(lab_number):
        """WTL бүх дээжийг Simulator руу илгээх.

        Дээжүүдийг ангилж:
        - fraction → washability fractions (float-sink)
        - dry_screen → хуурай шигшүүрийн хуваарилалт
        - wet_screen → нойтон шигшүүрийн хуваарилалт
        - composite → нэгдсэн/эхлэл дээжний чанар
        """
        safe_lab = escape_like_pattern(lab_number)
        samples = list(db.session.execute(
            select(Sample).where(
                Sample.client_name == "WTL",
                Sample.sample_code.like(f"{safe_lab}%", escape='\\'),
            )
        ).scalars().all())

        if not samples:
            return jsonify({"error": _("WTL дээж олдсонгүй: %(lab)s") % {"lab": lab_number}}), 404

        fractions = []
        dry_screen = []
        wet_screen = []
        composites = []
        flotation = []
        skipped = []

        for sample in samples:
            result_map = _get_approved_results(sample.id)
            # Масс: Sample.weight (kg) — mass workspace-аас хадгалагдсан
            mass_kg = sample.weight or 0

            category, size_class, density = _classify_wtl_sample(sample.sample_code)

            if category == "fraction":
                if density is None:
                    skipped.append(sample.sample_code)
                    continue
                fractions.append({
                    "size_class": size_class,
                    "density": density,
                    "mass_pct": mass_kg,  # Simulator нормализ хийнэ
                    "ash_pct": result_map.get("Aad", 0),
                    "sulfur_pct": result_map.get("TS", 0),
                    "vm_pct": result_map.get("Vad", 0),
                })

            elif category == "dry_screen":
                dry_screen.append({
                    "size_class": size_class,
                    "mass_pct": mass_kg,  # Дараа нормализ хийгдэнэ
                    "ash_pct": result_map.get("Aad", 0),
                    "moisture_pct": result_map.get("MT", result_map.get("Mad", 0)),
                })

            elif category == "wet_screen":
                wet_screen.append({
                    "size_class": size_class,
                    "mass_pct": mass_kg,  # Дараа нормализ хийгдэнэ
                    "ash_pct": result_map.get("Aad", 0),
                    "moisture_pct": result_map.get("MT", result_map.get("Mad", 0)),
                })

            elif category == "flotation":
                analyses = {k: v for k, v in result_map.items() if k in _ALL_ANALYSIS_CODES}
                if analyses or mass_kg > 0:
                    flotation.append({
                        "sample_code": sample.sample_code,
                        "category": "flotation",
                        "analyses": analyses,
                    })

            elif category == "composite":
                analyses = {k: v for k, v in result_map.items() if k in _ALL_ANALYSIS_CODES}
                if analyses or mass_kg > 0:
                    composites.append({
                        "sample_code": sample.sample_code,
                        "category": "composite",
                        "analyses": analyses,
                    })

        all_composites = composites + flotation
        total_items = len(fractions) + len(dry_screen) + len(wet_screen) + len(all_composites)
        if total_items == 0:
            return jsonify({"error": _("Илгээх өгөгдөл олдсонгүй")}), 400

        # Sample date
        sample_date = None
        if samples and samples[0].sample_date:
            sample_date = str(samples[0].sample_date)

        payload = {
            "source": "lims",
            "client_name": "WTL",
            "lab_number": lab_number,
            "sample_date": sample_date,
            "fractions": fractions,
            "dry_screen": dry_screen,
            "wet_screen": wet_screen,
            "composites": all_composites,
        }

        url = f"{_get_simulator_url()}/api/v1/lims/receive/wtl"
        data, err = _send_to_simulator(url, payload)
        if err:
            return jsonify({"error": err}), 502

        logger.info(
            f"WTL data sent: lab={lab_number}, fractions={len(fractions)}, "
            f"dry={len(dry_screen)}, wet={len(wet_screen)}, "
            f"composites={len(composites)}, flotation={len(flotation)}, "
            f"user={current_user.username}"
        )

        msg_parts = []
        if fractions:
            msg_parts.append(f"{len(fractions)} фракц")
        if dry_screen:
            msg_parts.append(f"{len(dry_screen)} хуурай шигшүүр")
        if wet_screen:
            msg_parts.append(f"{len(wet_screen)} нойтон шигшүүр")
        if composites:
            msg_parts.append(f"{len(composites)} нэгдсэн дээж")
        if flotation:
            msg_parts.append(f"{len(flotation)} флотаци")

        return jsonify({
            "success": True,
            "message": f"Симулятор руу амжилттай илгээгдлэн ({', '.join(msg_parts)})",
            "simulator_response": data,
        })
