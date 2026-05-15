# app/routes/analysis/qc.py
# -*- coding: utf-8 -*-
"""
Чанарын хяналтын (QC) хэрэгслүүдтэй холбоотой routes:
  - /qc/composite_check - Composite Check (COM vs Hourly дундаж)
  - /qc/norm_limit - Norm Limit (дээж vs spec target ± band)
  - /correlation_check - Correlation check
"""

import re
from collections import defaultdict

from flask import request, render_template, flash, redirect, url_for
from flask_login import login_required
from flask_babel import lazy_gettext as _l

from sqlalchemy import select

from app import db
from app.models import Sample, AnalysisResult
from app.utils.decorators import analysis_role_required
from app.utils.security import escape_like_pattern
from app.utils.conversions import calculate_all_conversions
from app.utils.parameters import PARAMETER_DEFINITIONS, get_canonical_name
from app.constants import NAME_CLASS_MASTER_SPECS, NAME_CLASS_SPEC_BANDS
from app.config.qc_config import (
    QC_PARAM_CODES,
    QC_TOLERANCE,
    QC_SPEC_DEFAULT,
)
from app.utils.qc import (
    qc_to_date,
    qc_split_family,
    qc_is_composite,
    qc_check_spec,
)


def _auto_find_hourly_samples(com_sample_ids: list) -> list:
    """
    COM дээжүүдийн family-тай тохирох hourly дээжүүдийг автоматаар олох.

    Args:
        com_sample_ids: COM дээжийн ID-ууд

    Returns:
        Бүх холбогдох sample ID-ууд (COM + hourly)
    """
    if not com_sample_ids:
        return []

    # COM дээжүүдийг татах
    com_samples = list(db.session.execute(
        select(Sample).where(Sample.id.in_(com_sample_ids))
    ).scalars().all())
    if not com_samples:
        return list(com_sample_ids)

    # Family-уудыг цуглуулах (жишээ: "SC20251205_D")
    families = set()
    for s in com_samples:
        family, slot = qc_split_family(s.sample_code or "")
        if family and slot and "com" in str(slot).lower():
            families.add(family)

    if not families:
        return list(com_sample_ids)

    # Ижил family-тай бүх дээжийг хайх
    all_ids = set(com_sample_ids)

    for family in families:
        # Family pattern: "SC20251205_D" → хайх: "SC20251205_D%"
        # ✅ LIKE injection сэргийлэлт
        safe_family = escape_like_pattern(family)
        pattern = f"{safe_family}%"
        matching_samples = list(db.session.execute(
            select(Sample).where(Sample.sample_code.like(pattern, escape='\\'))
        ).scalars().all())

        for s in matching_samples:
            all_ids.add(s.id)

    return list(all_ids)


def _get_qc_stream_data(ids: list):
    """QC талбаруудын хамтын өгөгдөл боловсруулалт"""
    samples = list(db.session.execute(
        select(Sample).where(Sample.id.in_(ids)).order_by(Sample.sample_code.asc())
    ).scalars().all())
    if not samples:
        return []
    samples_by_id = {s.id: s for s in samples}

    # ✅ Vdaf тооцоолоход Vad хэрэгтэй тул нэмж query хийх
    query_codes = list(QC_PARAM_CODES) + ["Vad"]  # Vad нэмэх

    results = db.session.query(AnalysisResult).filter(
        AnalysisResult.sample_id.in_(ids),
        AnalysisResult.status.in_(["approved", "pending_review"]),
        AnalysisResult.analysis_code.in_(query_codes),
    ).all()
    values_by_sample = {sid: {} for sid in ids}
    for r in results:
        try:
            values_by_sample[r.sample_id][r.analysis_code] = float(r.final_result)
        except (ValueError, TypeError):
            continue

    # ✅ Vdaf тооцоолол: Vdaf = Vad × 100 / (100 - Mad - Aad)
    for sid in ids:
        vals = values_by_sample.get(sid, {})
        vad = vals.get("Vad")
        mad = vals.get("Mad")
        aad = vals.get("Aad")
        if vad is not None and mad is not None and aad is not None:
            divisor = 100 - mad - aad
            if divisor > 0:
                vals["Vdaf"] = round(vad * 100 / divisor, 2)

    grouped = {}
    for sid in ids:
        sample = samples_by_id.get(sid)
        if not sample:
            continue
        family, slot = qc_split_family(sample.sample_code or "")
        key = family
        if key not in grouped:
            grouped[key] = {
                "family": family,
                "unit": sample.client_name or "",
                "date": qc_to_date(sample.sample_date or sample.received_date),
                "hourly_rows": [],
                "comp_row": None
            }

        row_values = {code: values_by_sample.get(sid, {}).get(code) for code in QC_PARAM_CODES}
        row_info = {"slot": slot or "", "sample": sample, "values": row_values}
        if qc_is_composite(sample, slot):
            grouped[key]["comp_row"] = row_info
        else:
            grouped[key]["hourly_rows"].append(row_info)

    streams = []
    for key, data in grouped.items():
        hourly_rows = data["hourly_rows"]

        def _slot_sort_value(row):
            s = row.get("slot") or ""
            digits = re.sub(r"\D", "", s)
            return int(digits) if digits else 0
        hourly_rows.sort(key=_slot_sort_value)

        avg_values = {}
        for code in QC_PARAM_CODES:
            vals = [
                float(row["values"].get(code))
                for row in hourly_rows
                if isinstance(row["values"].get(code), (int, float))
            ]
            if vals:
                avg_values[code] = round(sum(vals) / len(vals), 2)

        comp_row = data.get("comp_row")
        comp_values = comp_row["values"] if comp_row else {}
        delta = {}
        tol_flags = {}
        avg_spec_flags = {}
        comp_spec_flags = {}

        for code in QC_PARAM_CODES:
            v_avg = avg_values.get(code)
            v_comp = comp_values.get(code)
            if v_avg is not None and v_comp is not None:
                d = v_comp - v_avg
                delta[code] = round(d, 2)
                tol = QC_TOLERANCE.get(code)
                tol_flags[code] = bool(tol is not None and abs(d) > tol)
            else:
                delta[code] = None
                tol_flags[code] = False

            spec = QC_SPEC_DEFAULT.get(code)
            avg_spec_flags[code] = qc_check_spec(v_avg, spec)
            comp_spec_flags[code] = qc_check_spec(v_comp, spec)

        streams.append({
            "family": data["family"],
            "unit": data["unit"],
            "date": data["date"],
            "n_hourly": len(hourly_rows),
            "hourly_rows": hourly_rows,
            "avg_row": {"values": avg_values, "spec_flags": avg_spec_flags},
            "comp_row": {
                "sample": comp_row["sample"] if comp_row else None,
                "values": comp_values,
                "delta": delta,
                "tol_flags": tol_flags,
                "spec_flags": comp_spec_flags
            }
        })
    streams.sort(key=lambda s: s["family"])
    return streams


def register_routes(bp):
    """Route-уудыг өгөгдсөн blueprint дээр бүртгэх"""

    # =====================================================================
    # 1. COMPOSITE CHECK (COM vs Hourly дундаж)
    # =====================================================================
    @bp.route("/qc/composite_check")
    @login_required
    @analysis_role_required()
    def qc_composite_check():
        ids_str = request.args.get("ids", "").strip()
        ids = [int(x) for x in ids_str.split(",") if x.strip().isdigit()]
        if not ids:
            flash(_l("QC Dashboard-д дээж олдсонгүй."), "warning")
            return redirect(url_for("analysis.sample_summary"))

        # ✅ COM дээж сонгосон бол автоматаар hourly дээжүүдийг олох
        ids = _auto_find_hourly_samples(ids)

        streams = _get_qc_stream_data(ids)
        return render_template(
            "qc_composite_check.html",
            title="Composite Check",
            streams=streams,
            param_codes=QC_PARAM_CODES,
            raw_ids=",".join(str(i) for i in ids)  # Шинэчлэгдсэн IDs
        )

    # =====================================================================
    # 2. NORM LIMIT (дээж vs spec target ± band)
    # =====================================================================
    @bp.route("/qc/norm_limit")
    @login_required
    @analysis_role_required()
    def qc_norm_limit():
        """
        Дээж тус бүрийн утгыг сонгосон Spec (Name Class)-тэй харьцуулах.
        Stream бүлэглэлгүй - зөвхөн дээж vs spec target ± band.
        """
        ids_str = request.args.get("ids", "").strip()
        ids = [int(x) for x in ids_str.split(",") if x.strip().isdigit()]
        if not ids:
            flash(_l("Spec шалгалтад дээж олдсонгүй."), "warning")
            return redirect(url_for("analysis.sample_summary"))

        # Дээжүүдийг татах (✅ pagination limit нэмсэн)
        samples = list(db.session.execute(
            select(Sample)
            .where(Sample.id.in_(ids))
            .order_by(Sample.sample_code.asc())
            .limit(5000)
        ).scalars().all())
        if not samples:
            flash(_l("Дээж олдсонгүй."), "warning")
            return redirect(url_for("analysis.sample_summary"))

        # ✅ Vdaf тооцоолоход Vad хэрэгтэй
        query_codes = list(QC_PARAM_CODES) + ["Vad"]

        # Үр дүнгүүдийг татах
        results = db.session.query(AnalysisResult).filter(
            AnalysisResult.sample_id.in_(ids),
            AnalysisResult.status.in_(["approved", "pending_review"]),
            AnalysisResult.analysis_code.in_(query_codes),
        ).all()

        # Дээж тус бүрийн утгуудыг бэлдэх
        values_by_sample = {s.id: {} for s in samples}
        for r in results:
            try:
                values_by_sample[r.sample_id][r.analysis_code] = float(r.final_result)
            except (ValueError, TypeError):
                continue

        # ✅ Vdaf тооцоолол: Vdaf = Vad × 100 / (100 - Mad - Aad)
        for sid in ids:
            vals = values_by_sample.get(sid, {})
            vad = vals.get("Vad")
            mad = vals.get("Mad")
            aad = vals.get("Aad")
            if vad is not None and mad is not None and aad is not None:
                divisor = 100 - mad - aad
                if divisor > 0:
                    vals["Vdaf"] = round(vad * 100 / divisor, 2)

        # Spec сонголт
        spec_key = request.args.get("spec_key", "").strip()
        active_spec_row = NAME_CLASS_MASTER_SPECS.get(spec_key) if spec_key else None

        # Range spec бэлдэх
        def build_range_spec(row):
            if not row:
                return {}
            spec = {}
            for code in QC_PARAM_CODES:
                target = row.get(code)
                band = NAME_CLASS_SPEC_BANDS.get(code)
                if target is None or band is None:
                    continue
                spec[code] = {"target": target, "min": target - band, "max": target + band}
            return spec

        active_range_spec = build_range_spec(active_spec_row)

        # Дээж тус бүрийн өгөгдөл бэлдэх
        def _range_out(val, rule):
            if val is None or not rule:
                return False
            return val < rule["min"] or val > rule["max"]

        sample_rows = []
        for s in samples:
            vals = values_by_sample.get(s.id, {})
            row_values = {code: vals.get(code) for code in QC_PARAM_CODES}

            # Spec flag тус бүр
            spec_flags = {}
            for code in QC_PARAM_CODES:
                rule = active_range_spec.get(code)
                spec_flags[code] = _range_out(row_values.get(code), rule)

            sample_rows.append({
                "sample": s,
                "values": row_values,
                "spec_flags": spec_flags
            })

        return render_template(
            "qc_norm_limit.html",
            title="Norm Limit",
            sample_rows=sample_rows,
            param_codes=QC_PARAM_CODES,
            raw_ids=ids_str,
            name_class_master_specs=NAME_CLASS_MASTER_SPECS,
            tolerance_bands=NAME_CLASS_SPEC_BANDS,
            active_spec_key=spec_key,
            active_range_spec=active_range_spec
        )

    # =====================================================================
    # 3. CORRELATION CHECK
    # =====================================================================
    @bp.route("/correlation_check")
    @login_required
    @analysis_role_required()
    def correlation_check():
        ids_str = request.args.get("ids", "").strip()
        ids = [int(x) for x in ids_str.split(",") if x.strip().isdigit()]

        if not ids:
            flash(_l("Корреляци шалгалтад дээж олдсонгүй."), "warning")
            return redirect(url_for("analysis.sample_summary"))

        # ✅ Pagination limit нэмсэн
        samples = list(db.session.execute(
            select(Sample).where(Sample.id.in_(ids)).limit(5000)
        ).scalars().all())
        if not samples:
            flash(_l("Дээж олдсонгүй."), "warning")
            return redirect(url_for("analysis.sample_summary"))

        # ✅ N+1 QUERY ЗАСВАР: Бүх үр дүнг нэг query-ээр татах
        sample_ids = [s.id for s in samples]
        all_results = list(db.session.execute(
            select(AnalysisResult).where(
                AnalysisResult.sample_id.in_(sample_ids),
                AnalysisResult.status.in_(["approved", "pending_review"]),
            )
        ).scalars().all())

        # sample_id-аар group хийх
        results_by_sample = defaultdict(list)
        for r in all_results:
            results_by_sample[r.sample_id].append(r)

        data_list = []

        for s in samples:
            # 1. DB-ээс түүхий өгөгдөл (✅ N+1 засагдсан)
            results = results_by_sample.get(s.id, [])

            res_map = {r.analysis_code: r.final_result for r in results}

            # 2. Тооцоолол (Calculated values)
            raw_canonical_data = {}
            for r in results:
                c = get_canonical_name(r.analysis_code)
                if c:
                    # Анхаар: Энд dict хэлбэрээр хадгалж байна
                    raw_canonical_data[c] = {"value": r.final_result}

            calcs = calculate_all_conversions(raw_canonical_data, PARAMETER_DEFINITIONS)

            # Hybrid Getter (ЗАСВАРЛАСАН: Dict check нэмсэн)
            def get_val(ckeys, rcodes):
                # 1. Calculated values шалгах
                if isinstance(ckeys, str):
                    ckeys = [ckeys]
                for k in ckeys:
                    v = calcs.get(k)
                    if v is not None:
                        # ✅ ЗАСВАР: Хэрэв v нь dict байвал дотроос нь 'value' түлхүүрийг авна
                        if isinstance(v, dict):
                            v = v.get('value')

                        try:
                            return float(v)
                        except (TypeError, ValueError):
                            pass

                # 2. Raw DB values шалгах
                if isinstance(rcodes, str):
                    rcodes = [rcodes]
                for c in rcodes:
                    v = res_map.get(c)
                    if v is not None:
                        try:
                            if isinstance(v, str):
                                v = v.replace(',', '.').strip()
                            if v == "":
                                continue
                            return float(v)
                        except (TypeError, ValueError):
                            pass
                return None

            # 3. БҮХ ҮЗҮҮЛЭЛТ
            item = {
                "id": s.id,
                "sample_code": s.sample_code,

                # --- Техникийн шинжилгээ ---
                "Aad": get_val(["ash", "ash_ad"], ["Aad", "Ad"]),
                "Mad": get_val(["inherent_moisture", "moisture"], ["Mad", "M_ad"]),
                "Mtar": get_val(["total_moisture", "total_moisture_ar"], ["Mt,ar", "Mtar", "TM"]),
                "Vdaf": get_val(["volatile_matter_daf"], ["Vdaf", "V_daf"]),
                "Vad": get_val(["volatile_matter", "volatile_matter_ad"], ["Vad"]),

                # --- Илчлэг ---
                "Qgr_ad": get_val(["calorific_value", "qgr_ad"], ["Qgr,ad", "CV"]),
                "Qnet_ar": get_val(["net_calorific_value", "qnet_ar"], ["Qnet,ar", "NCV"]),

                # --- Элемент ---
                "St_ad": get_val(["total_sulfur", "sulfur"], ["St,ad", "TS"]),
                "Had": get_val(["hydrogen", "hydrogen_ad"], ["H", "Had"]),

                # --- Коксжих шинж чанар ---
                "CSN": get_val(["free_swelling_index", "csn"], ["CSN", "FSI"]),
                "Gi": get_val(["caking_power", "g_index"], ["Gi", "G"]),
                "Y": get_val(["plastometer_y", "layer_thickness"], ["Y"]),
                "CRC": get_val(["coke_reference_button"], ["CRC"]),

                # --- Физик ---
                "TRD": get_val(["relative_density", "relative_density_ad"], ["TRD", "RD", "TRD,ad"]),
            }
            data_list.append(item)

        return render_template(
            "correlation_check.html",
            title="Correlation Check",
            data_list=data_list,
            raw_ids=ids_str
        )
