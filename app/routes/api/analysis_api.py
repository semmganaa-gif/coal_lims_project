# app/routes/api/analysis_api.py
# -*- coding: utf-8 -*-
"""
Шинжилгээтэй холбоотой API endpoints:
  - /eligible_samples/<analysis_code>
  - /save_results (Logic from analysis_rules.py + Control Standards)
  - /update_result_status
"""

import asyncio

from flask import (
    request,
    jsonify,
    current_app,
    url_for,
    redirect,
)
from flask_login import login_required, current_user
from sqlalchemy import or_, not_
import json

from app import db, limiter
from app.utils.converters import to_float
from app.models import Sample, AnalysisResult, AnalysisResultLog, ControlStandard, GbwStandard
from app.utils.datetime import now_local
from app.utils.normalize import normalize_raw_data
from app.utils.codes import norm_code, BASE_TO_ALIASES

# ✅ Дүрмийн логик импортлох (Шинэ файл)
from app.utils.analysis_rules import determine_result_status

# ✅ DB код -> Стандарт код mapping (QC шалгалтад хэрэглэгдэнэ)
# DB дахь кодууд (Aad, CV, TS) -> CM/GBW стандарт дахь кодууд (Adb,%, CVdb,kcal/kg г.м)
# CM: CVdb,kcal/kg | GBW: CVdb,MJ/kg (нэгж өөр)
DB_TO_STANDARD_CODE_CM = {
    'Aad': 'Adb,%',
    'Vad': 'Vdb,%',
    'CV': 'CVdb,kcal/kg',
    'TS': 'Stdb,%',
    'TRD': 'TRDdb,g/cm3',
    'CSN': 'CSN',
    'Gi': 'Gi',
    'P': 'Pdb,%',
    'F': 'Fdb,mg/g',
    'Cl': 'Cldb,%',
    'Mad': 'Mad',
}
DB_TO_STANDARD_CODE_GBW = {
    'Aad': 'Adb,%',
    'Vad': 'Vdb,%',
    'CV': 'CVdb,MJ/kg',  # GBW нь MJ нэгжтэй
    'TS': 'Stdb,%',
    'TRD': 'TRDdb,g/cm3',
    'CSN': 'CSN',
    'Gi': 'Gi',
    'P': 'Pdb,%',
    'F': 'Fdb,mg/g',
    'Cl': 'Cldb,%',
    'Mad': 'Mad',
}

# Server-side verification (Security)
from app.utils.server_calculations import verify_and_recalculate

from app.utils.validators import (
    validate_save_results_batch,
    validate_sample_id,
    validate_analysis_code,
    validate_analysis_result,
    validate_equipment_id,
)
from datetime import timedelta
from .helpers import (
    _requires_mass_gate,
    _has_m_task_sql,

    _coalesce_diff,
    _effective_limit,
)

# Monitoring
from app.monitoring import track_analysis


def register_routes(bp):
    """Route-уудыг өгөгдсөн blueprint дээр бүртгэх"""

    # -----------------------------------------------------------
    # 1) Ажлын талбарын "дээжүүд"
    # -----------------------------------------------------------
    @bp.route("/eligible_samples/<analysis_code>", methods=["GET"])
    @login_required
    @limiter.limit("100 per minute")
    async def eligible_samples(analysis_code):
        base_code = norm_code(analysis_code).strip()
        if not base_code:
            return jsonify({"samples": []})

        def _query_eligible():
            existing_ids_subq = (
                db.session.query(AnalysisResult.sample_id)
                .filter(AnalysisResult.analysis_code == base_code)
                .distinct()
            )

            from sqlalchemy import func
            text_lc = func.lower(Sample.analyses_to_perform)
            terms = [base_code.lower()]
            for alias_lc in (BASE_TO_ALIASES.get(base_code, []) or []):
                terms.append(alias_lc)

            like_clauses = [text_lc.like(f'%"{t}"%') for t in terms]

            q = Sample.query.filter(
                Sample.lab_type == 'coal',
                Sample.status.in_(["new", "New"]),
                or_(*like_clauses),
                ~Sample.id.in_(existing_ids_subq),
            )

            if _requires_mass_gate(base_code):
                q = q.filter(or_(not_(_has_m_task_sql()), Sample.mass_ready.is_(True)))

            from app.constants import MAX_ANALYSIS_RESULTS
            return q.order_by(Sample.received_date.desc(), Sample.id.desc()).limit(MAX_ANALYSIS_RESULTS).all()

        rows = await asyncio.to_thread(_query_eligible)
        from app.constants import CHPP_2H_SAMPLES_ORDER

        # CHPP дээжүүдийг зөв дарааллаар эрэмбэлэх
        def get_chpp_order(sample):
            """CHPP дээжийн дараалал олох"""
            sample_name = getattr(sample, "sample_name", None) or getattr(sample, "name", None) or ""
            # Огноогоор групплэх (received_date)
            date_key = sample.received_date.strftime("%Y%m%d") if sample.received_date else "00000000"
            # CHPP дарааллаас хайх
            for idx, chpp_name in enumerate(CHPP_2H_SAMPLES_ORDER):
                if chpp_name in sample_name:
                    return (date_key, idx)
            # CHPP биш бол ID-аар
            return (date_key, 1000 + sample.id)

        # Огноогоор буурах + CHPP дотор дараалал
        rows_sorted = sorted(rows, key=lambda s: (
            -(int(get_chpp_order(s)[0])),  # Огноо буурах
            get_chpp_order(s)[1]            # CHPP дараалал өсөх
        ))

        samples = []
        for s in rows_sorted:
            samples.append({
                "id": s.id,
                "sample_code": s.sample_code or "",
                "name": getattr(s, "sample_name", None) or getattr(s, "name", None) or "",
                "client_name": s.client_name or "",
                "sample_type": s.sample_type or "",
                "received_date": s.received_date.strftime("%Y-%m-%d %H:%M") if s.received_date else "",
            })

        # ✅ Rejected дээжүүд - давтах шаардлагатай
        # Химич: зөвхөн өөрийнхөө rejected дээж
        # Ахлах/Админ: бүх rejected дээж
        def _query_rejected():
            rejected_query = (
                db.session.query(AnalysisResult, Sample)
                .join(Sample, AnalysisResult.sample_id == Sample.id)
                .filter(
                    AnalysisResult.analysis_code == base_code,
                    AnalysisResult.status == "rejected"
                )
            )

            if current_user.role == "chemist":
                rejected_query = rejected_query.filter(AnalysisResult.user_id == current_user.id)

            return rejected_query.order_by(AnalysisResult.updated_at.desc()).all()

        rejected_rows = await asyncio.to_thread(_query_rejected)

        rejected_samples = []
        for result, sample in rejected_rows:
            rejected_samples.append({
                "id": sample.id,
                "result_id": result.id,
                "sample_code": sample.sample_code or "",
                "client_name": sample.client_name or "",
                "sample_type": sample.sample_type or "",
                "error_reason": result.error_reason or "",
                "updated_at": result.updated_at.strftime("%Y-%m-%d %H:%M") if result.updated_at else "",
            })

        return jsonify({
            "samples": samples,
            "rejected": rejected_samples,
            "rejected_count": len(rejected_samples)
        })

    # -----------------------------------------------------------
    # 1.5) Дээжийг шинжилгээнээс хасах (senior/admin only)
    # -----------------------------------------------------------
    @bp.route("/unassign_sample", methods=["POST"])
    @login_required
    @limiter.limit("100 per minute")
    async def unassign_sample():
        """
        Дээжийг тухайн шинжилгээнээс хасах.
        Зөвхөн senior, admin эрхтэй хэрэглэгч.
        """
        if current_user.role not in ("senior", "admin"):
            return jsonify({"success": False, "message": "Зөвхөн ахлах болон админ хийх эрхтэй"}), 403

        data = request.get_json(silent=True)
        if not data:
            return jsonify({"success": False, "message": "JSON өгөгдөл ирсэнгүй"}), 400

        sample_id = data.get("sample_id")
        analysis_code = data.get("analysis_code")

        if not sample_id or not analysis_code:
            return jsonify({"success": False, "message": "sample_id болон analysis_code шаардлагатай"}), 400

        sample = Sample.query.get(sample_id)
        if not sample:
            return jsonify({"success": False, "message": "Дээж олдсонгүй"}), 404

        # analyses_to_perform-оос хасах
        import json
        try:
            analyses = json.loads(sample.analyses_to_perform or "[]")
        except (json.JSONDecodeError, TypeError, ValueError):
            analyses = []

        base_code = norm_code(analysis_code).strip()
        # Код болон alias-уудыг хасах
        codes_to_remove = [base_code.lower()] + [a.lower() for a in (BASE_TO_ALIASES.get(base_code, []) or [])]

        original_count = len(analyses)
        analyses = [a for a in analyses if a.lower() not in codes_to_remove]

        if len(analyses) == original_count:
            return jsonify({"success": False, "message": f"{analysis_code} шинжилгээ оноогдоогүй байна"}), 400

        sample.analyses_to_perform = json.dumps(analyses)

        # Audit log
        from app.services.audit_log_service import log_action
        log_action(
            action="unassign_analysis",
            entity_type="sample",
            entity_id=sample.id,
            details=f"Дээж {sample.sample_code}-аас {analysis_code} шинжилгээг хассан"
        )

        db.session.commit()

        return jsonify({
            "success": True,
            "message": f"{sample.sample_code} дээжээс {analysis_code} шинжилгээг хаслаа",
            "remaining_analyses": analyses
        })

    # -----------------------------------------------------------
    # 2) Химич хадгалсан үр дүн → /api/save_results
    # -----------------------------------------------------------
    @bp.route("/save_results", methods=["POST"])
    @login_required
    @limiter.limit("100 per minute")
    async def save_results():
        data = request.get_json(silent=True)

        if data is None:
            return jsonify({"message": "JSON өгөгдөл ирсэнгүй."}), 400

        if isinstance(data, dict):
            data = [data]

        if not isinstance(data, list) or len(data) == 0:
            return jsonify({"message": "JSON массив байх ёстой"}), 400

        # Input validation
        is_valid, validated_items, validation_errors = validate_save_results_batch(data)

        if not is_valid:
            current_app.logger.warning(f"Validation warnings: {validation_errors}")

        saved_count = 0
        failed_count = 0
        results_for_response = []
        errors = []

        for index, item in enumerate(data):
            try:
                with db.session.begin_nested():
                    # --- 1. Validation Logic ---
                    sample_id_raw = item.get("sample_id")
                    sample_id, s_err = validate_sample_id(sample_id_raw)
                    if s_err:
                        raise ValueError(f"Sample ID Error: {s_err}")

                    analysis_code_in = item.get("analysis_code")
                    _, c_err = validate_analysis_code(analysis_code_in)
                    if c_err:
                        raise ValueError(f"Code Error: {c_err}")

                    analysis_code = norm_code(analysis_code_in)

                    final_result_raw = item.get("final_result")
                    final_result, r_err = validate_analysis_result(final_result_raw, analysis_code, allow_none=True)
                    if r_err:
                        current_app.logger.warning(f"Item {index}: {r_err}")
                        errors.append(f"Item {index} ({analysis_code}): {r_err}")
                        failed_count += 1
                        continue

                    equipment_id_raw = item.get("equipment_id")
                    equipment_id, _ = validate_equipment_id(equipment_id_raw, allow_none=True)

                    sample = db.session.get(Sample, sample_id)
                    if not sample:
                        raise ValueError(f"Sample {sample_id} not found")

                    # --- 2. Normalization & Calculation ---
                    raw_in = item.get("raw_data") or {}

                    if analysis_code == "CSN" and isinstance(raw_in, dict):
                        raw_norm = dict(raw_in)
                        raw_norm.update(normalize_raw_data(raw_in, analysis_code))
                    else:
                        raw_norm = normalize_raw_data(raw_in, analysis_code)

                    # UI flags preserve
                    for key in ("is_low_avg", "retest_mode", "limit_used", "limit_mode", "t_exceeded", "t_band"):
                        if isinstance(raw_in, dict) and key in raw_in:
                            raw_norm[key] = raw_in[key]

                    # Tolerance logic
                    avg = to_float(raw_norm.get("avg"))
                    diff = _coalesce_diff(raw_norm)
                    limit, mode, band = _effective_limit(analysis_code, avg)
                    effective_limit = (avg * limit) if (mode == "percent" and avg is not None) else limit

                    if analysis_code == "CSN" and diff is None:
                        diff = 0.0
                    # Floating point tolerance: 1e-6 (яг тэнцүү бол тохирсон гэж үзнэ)
                    EPSILON = 1e-6
                    t_exceeded = (diff is not None) and ((abs(diff) - (effective_limit or 0)) > EPSILON)

                    raw_norm.update({
                        "t_band": band,
                        "limit_used": effective_limit,
                        "limit_mode": mode,
                        "t_exceeded": bool(t_exceeded),
                    })

                    # ============================================================
                    # 🔒 SERVER-SIDE CALCULATION VERIFICATION (Security)
                    # ============================================================
                    if final_result is not None and raw_norm:
                        server_result, calc_warnings = verify_and_recalculate(
                            analysis_code=analysis_code,
                            client_final_result=final_result,
                            raw_data=raw_norm,
                            user_id=current_user.id,
                            sample_id=sample_id
                        )
                        if server_result is not None:
                            final_result = server_result
                        if calc_warnings:
                            for warn in calc_warnings:
                                current_app.logger.warning(warn)

                    # ============================================================
                    # 🛠 CONTROL & GBW LOGIC (Dry Basis Conversion)
                    # ============================================================
                    control_targets = None
                    val_to_check = final_result

                    try:
                        # 1. Дээжийг таних (CM эсвэл GBW эсэхийг шалгах)
                        stype = (sample.sample_type or "").lower()
                        scode = (sample.sample_code or "").upper() # Upper болгож шалгах нь найдвартай

                        is_cm = (stype == "control") or ("CM-" in scode) or ("CM_" in scode)
                        is_gbw = (stype == "gbw") or ("GBW" in scode)

                        if (is_cm or is_gbw) and final_result is not None:
                            active_std = None

                            # 2. Идэвхтэй стандарт хайх (Төрлөөс хамаарч)
                            if is_cm:
                                active_std = ControlStandard.query.filter_by(is_active=True).first()
                            elif is_gbw:
                                # ✅ GBW стандарт хайх (Models дотор GbwStandard байгаа гэж үзэв)
                                active_std = GbwStandard.query.filter_by(is_active=True).first()

                            if active_std:
                                # JSON targets-ийг dict болгох
                                targets_map = active_std.targets
                                if isinstance(targets_map, str):
                                    try:
                                        targets_map = json.loads(targets_map)
                                    except (json.JSONDecodeError, ValueError):
                                        targets_map = {}

                                # 3. Стандарт дотор энэ код (Aad, Vad г.м) байгаа эсэх?
                                # Эхлээд шууд analysis_code-оор хайна, олдохгүй бол standard_code
                                # CM болон GBW өөр mapping ашиглана (CV нэгж өөр)
                                code_map = DB_TO_STANDARD_CODE_GBW if is_gbw else DB_TO_STANDARD_CODE_CM
                                standard_code = code_map.get(analysis_code, analysis_code)
                                if isinstance(targets_map, dict):
                                    # Эхлээд шууд хайх (Aad, Vad, CV, TS г.м)
                                    if analysis_code in targets_map:
                                        control_targets = targets_map[analysis_code]
                                    # Олдохгүй бол хөрвүүлсэн код хайх (Ad, Vd, CV,d г.м)
                                    elif standard_code in targets_map:
                                        control_targets = targets_map[standard_code]

                                if control_targets:

                                    # --- 4. MAD (Чийг) ОЛОХ ЛОГИК ---
                                    # CM болон GBW нь ихэвчлэн Хуурай суурь (Dry Basis) дээр сертификаттай байдаг тул
                                    # Лабораторийн үр дүнг (Air Dry) -> Dry Basis руу хөрвүүлж байж шалгана.

                                    current_mad = None

                                    # А. Одоо ирж буй (save хийж буй) өгөгдлөөс Mad хайх
                                    for d in data:
                                        ac = (d.get("analysis_code") or "").lower()
                                        if ac == "mad":
                                            try:
                                                current_mad = float(d.get("final_result"))
                                            except (ValueError, TypeError):
                                                pass  # final_result хоосон эсвэл тоо биш бол алгасна
                                            break

                                    # Б. Баазаас хайх (Өмнө нь Mad хадгалсан бол)
                                    if current_mad is None:
                                        calc = sample.get_calculations()
                                        if calc and calc.mad is not None:
                                            current_mad = calc.mad

                                        # 5. Хөрвүүлэлт (Mad олдсон бол)
                                    # Dry basis руу хөрвүүлэх шаардлагатай үзүүлэлтүүд
                                    needs_dry_conversion = analysis_code in ["Aad", "Vad", "CV", "TS", "St,ad", "S", "Qgr,ad"]

                                    if needs_dry_conversion:
                                        if current_mad is not None and 0 < current_mad < 100:
                                            # Mad байгаа - dry basis руу хөрвүүлж шалгана

                                            # АЛХАМ 1: Эхлээд Хуурай суурь руу хөрвүүлэх (Air Dry -> Dry Basis)
                                            factor = 100.0 / (100.0 - current_mad)
                                            val_dry = final_result * factor  # Энд ккал хэвээрээ (Хуурай)

                                            # АЛХАМ 2: GBW дээр MJ руу хөрвүүлэх, CM дээр kcal хэвээр
                                            if is_gbw and analysis_code in ["CV", "Qgr,ad"]:
                                                # GBW target нь MJ нэгжтэй хадгалагдсан
                                                if val_dry > 100:
                                                    val_to_check = (val_dry * 4.1868) / 1000.0
                                                else:
                                                    val_to_check = val_dry
                                            else:
                                                # CM болон бусад үзүүлэлтүүд kcal/шууд утгаараа шалгагдана
                                                val_to_check = val_dry
                                        else:
                                            # ⚠️ Mad байхгүй - dry basis руу хөрвүүлэх боломжгүй
                                            # CM/GBW шалгалт хийхгүй, pending_review болгоно
                                            control_targets = None
                                            # Flag тавих - дараа нь pending_review болгохын тулд
                                            raw_norm["_mad_required"] = True
                                            current_app.logger.info(
                                                f"CM/GBW check skipped for {analysis_code}: Mad not available yet"
                                            )
                    except Exception as e:
                        current_app.logger.error(f"Control/GBW Logic Error: {e}")
                        control_targets = None
                        val_to_check = final_result

                    # ============================================================
                    # ✅ 3. STATUS DETERMINATION
                    # ============================================================

                    new_status, status_reason = determine_result_status(
                        analysis_code,
                        val_to_check,
                        raw_norm,
                        control_targets=control_targets,
                    )

                    # ------------------------------------------------------------
                    # ✅ FIX: GBW vs CM Тайлбарыг ялгах (Text adjustment)
                    # ------------------------------------------------------------
                    # determine_result_status функц нь ихэвчлэн "Control Failure" гэж буцаадаг тул
                    # хэрэв энэ нь GBW дээж байвал үгийг нь сольж "GBW Failure" болгоё.
                    # (is_gbw хувьсагч өмнөх блокоос ирж байгаа гэж тооцов)
                    is_gbw_sample = locals().get('is_gbw', False) # Аюулгүй байдлын үүднээс шалгах

                    if new_status == "rejected" and is_gbw_sample and status_reason:
                        status_reason = status_reason.replace("Control Failure", "GBW Failure")

                    # ------------------------------------------------------------
                    # ✅ FIX: Mad байхгүй үед pending_review болгох
                    # ------------------------------------------------------------
                    # CM/GBW дээжинд Mad шаардлагатай үзүүлэлт (Aad, Vad, CV г.м)
                    # Mad байхгүй бол ахлахын хяналт руу илгээнэ
                    if raw_norm.get("_mad_required") and new_status == "approved":
                        new_status = "pending_review"
                        status_reason = "Mad шаардлагатай (CM/GBW dry basis шалгалт)"

                    # ============================================================

                    # --- 4. DB Operations ---
                    existing = (
                        AnalysisResult.query.filter_by(sample_id=sample_id, analysis_code=analysis_code)
                        .order_by(AnalysisResult.id.desc()).first()
                    )

                    action = ""
                    # UI-аас ирсэн коммент эсвэл автомат статус тайлбар
                    reason = status_reason if status_reason else (item.get("rejection_comment") or "Химич хадгалсан")

                    # Автомат KPI алдаа оноох (QC Failure)
                    auto_error_reason = None

                    # ✅ ЭНД ӨӨРЧЛӨЛТ: CM болон GBW хоёулаа 'qc_fail' гэсэн нэг ангилалд орно.
                    if new_status == "rejected":
                        # "Control Failure" эсвэл "GBW Failure" гэсэн үг байвал QC алдаа гэж тооцно
                        # (determine_result_status функцээс "Failure" гэсэн үгтэй ирдэг)
                        if status_reason and ("Failure" in status_reason):
                            auto_error_reason = "qc_fail"

                    if not existing:
                        new_res = AnalysisResult(
                            sample_id=sample_id,
                            user_id=current_user.id,
                            analysis_code=analysis_code,
                            final_result=final_result,
                            status=new_status,
                            created_at=now_local(),
                            updated_at=now_local(),
                            rejection_comment=status_reason,
                            error_reason=auto_error_reason,
                        )
                        new_res.set_raw_data(raw_norm)
                        db.session.add(new_res)
                        db.session.flush()

                        if new_status == "approved":
                            action = "CREATED_AUTO_APPROVED"
                        elif new_status == "rejected":
                            action = "CREATED_REJECTED"
                        elif new_status == "pending_review":
                            action = "CREATED_PENDING"
                        else:
                            action = "CREATED"

                        target_res_id = new_res.id
                        raw_snapshot = new_res.raw_data
                        final_snapshot = new_res.final_result

                    else:
                        existing.final_result = final_result
                        existing.set_raw_data(raw_norm)
                        existing.status = new_status
                        existing.updated_at = now_local()
                        existing.rejection_comment = status_reason

                        if auto_error_reason:
                            existing.error_reason = auto_error_reason

                        db.session.flush()

                        if new_status == "approved":
                            action = "UPDATED_AUTO_APPROVED"
                        elif new_status == "rejected":
                            action = "UPDATED_REJECTED"
                        elif new_status == "pending_review":
                            action = "UPDATED_PENDING"
                        else:
                            action = "UPDATED"

                        target_res_id = existing.id
                        raw_snapshot = existing.raw_data
                        final_snapshot = existing.final_result

                    # ============================================================
                    # ✅ SOLID: Дээжний жинг автоматаар шинэчлэх
                    # A = хувинтай дээжний жин, B = хувины жин
                    # Дээжний жин = A - B
                    # ============================================================
                    if analysis_code.upper() == "SOLID":
                        try:
                            A = raw_norm.get("A")  # bucket_with_sample
                            B = raw_norm.get("B")  # bucket_only
                            if A is not None and B is not None:
                                A_val = float(A)
                                B_val = float(B)
                                sample_weight = round(A_val - B_val, 2)
                                if sample_weight > 0:
                                    sample.weight = sample_weight
                                    current_app.logger.info(
                                        f"Sample {sample_id} weight updated to {sample_weight} kg from Solid analysis"
                                    )
                        except (ValueError, TypeError) as e:
                            current_app.logger.warning(f"Could not calculate sample weight from Solid: {e}")

                    # ============================================================
                    # ✅ АНХНЫ ХАДГАЛСАН МЭДЭЭЛЭЛ ОЛОХ (Аудит хамгаалалт)
                    # ============================================================
                    # Энэ дээж + analysis_code-ийн хамгийн анхны бүртгэлийг хайх
                    first_log = (
                        AnalysisResultLog.query
                        .filter_by(sample_id=sample_id, analysis_code=analysis_code)
                        .order_by(AnalysisResultLog.id.asc())
                        .first()
                    )

                    # Анхны химич, анхны цаг
                    if first_log:
                        original_user_id = first_log.original_user_id or first_log.user_id
                        original_timestamp = first_log.original_timestamp or first_log.timestamp
                    else:
                        # Энэ бол хамгийн анхны бүртгэл
                        original_user_id = current_user.id
                        original_timestamp = now_local()

                    # Audit Log
                    current_ts = now_local()
                    audit = AnalysisResultLog(
                        timestamp=current_ts,
                        user_id=current_user.id,
                        sample_id=sample_id,
                        analysis_result_id=target_res_id,
                        analysis_code=analysis_code,
                        action=action,
                        raw_data_snapshot=raw_snapshot,
                        final_result_snapshot=final_snapshot,
                        reason=reason,
                        error_reason=auto_error_reason,
                        # ✅ ШИНЭ: Анхны мэдээлэл (хэзээ ч өөрчлөгдөхгүй)
                        original_user_id=original_user_id,
                        original_timestamp=original_timestamp,
                        # ✅ ШИНЭ: Дээжний код snapshot (sample устсан ч харагдана)
                        sample_code_snapshot=sample.sample_code,
                    )
                    # ✅ ШИНЭ: Hash тооцоолох (өөрчлөгдсөн эсэхийг шалгах)
                    audit.data_hash = audit.compute_hash()
                    db.session.add(audit)

                    saved_count += 1
                    results_for_response.append({
                        "sample_id": sample_id,
                        "analysis_code": analysis_code,  # ✅ X, Y worksheet removal-д хэрэгтэй
                        "status": new_status,
                        "raw_data": raw_norm,
                        "success": True,
                        "reason": reason  # ✅ ШИНЭ: Тайлбарыг Frontend рүү буцаана (Badge харуулахад хэрэгтэй)
                    })

            except Exception as e:
                failed_count += 1
                error_msg = str(e)
                errors.append({"index": index, "sample_id": item.get("sample_id"), "error": error_msg})

        # Commit All
        try:
            db.session.commit()

            # ✅ Prometheus metrics: Шинжилгээ хадгалсныг track хийх
            for res in results_for_response:
                if res.get("success"):
                    track_analysis(
                        analysis_type=res.get("analysis_code", "unknown"),
                        status=res.get("status", "completed")
                    )

        except Exception as e:
            db.session.rollback()
            return jsonify({"message": "Database Commit Error", "error": str(e)}), 500

        # Response
        response_data = {
            "message": f"{saved_count} мөр амжилттай, {failed_count} алдаатай.",
            "results": results_for_response,
            "errors": errors
        }
        status_code = 200 if failed_count == 0 else 207
        return jsonify(response_data), status_code

    # -----------------------------------------------------------
    # 3) Ахлахын буцаах/батлах
    # -----------------------------------------------------------
    @bp.route("/update_result_status/<int:result_id>/<new_status>", methods=["POST"])
    @login_required
    async def update_result_status(result_id, new_status):
        if getattr(current_user, "role", None) not in ("senior", "admin"):
            return jsonify({"message": "Эрх хүрэхгүй"}), 403

        res = AnalysisResult.query.get_or_404(result_id)
        allowed = {"approved", "rejected", "pending_review"}

        if new_status not in allowed:
            return jsonify({"message": "Буруу статус"}), 400

        if request.is_json:
            data = request.get_json(silent=True) or {}
        else:
            data = request.form.to_dict()

        action_type = data.get("action_type")
        rejection_category = data.get("rejection_category")
        rejection_subcategory = data.get("rejection_subcategory")
        rejection_comment = data.get("rejection_comment")
        error_reason = data.get("error_reason") or None

        res.status = new_status
        res.updated_at = now_local()

        if hasattr(res, "rejection_comment"):
            if new_status == "rejected":
                res.rejection_comment = rejection_comment if rejection_comment else "Ахлах буцаасан"
            elif new_status == "approved":
                res.rejection_comment = None

        if hasattr(res, "error_reason") and error_reason:
            res.error_reason = error_reason

        db.session.flush()

        if new_status == "approved":
            action_text = "APPROVED"
            default_reason = "Ахлах баталгаажуулсан"
        elif new_status == "rejected":
            action_text = "REJECTED"
            default_reason = "Ахлах буцаасан"
        else:
            action_text = "PENDING_REVIEW"
            default_reason = "Ахлах хяналт руу буцаасан"

        reason_text = rejection_comment or default_reason
        if action_type:
            reason_text = f"{reason_text}. action={action_type}"

        audit = AnalysisResultLog(
            timestamp=now_local(),
            user_id=current_user.id,
            sample_id=res.sample_id,
            analysis_result_id=res.id,
            analysis_code=res.analysis_code,
            action=action_text,
            raw_data_snapshot=res.raw_data,
            final_result_snapshot=res.final_result,
            rejection_category=rejection_category,
            rejection_subcategory=rejection_subcategory,
            reason=reason_text,
            error_reason=error_reason,
        )
        db.session.add(audit)
        db.session.commit()

        if request.headers.get("X-Requested-With") == "XMLHttpRequest" or request.is_json:
            return jsonify({"message": "OK", "status": new_status})

        if "analysis" in current_app.blueprints:
            return redirect(url_for("analysis.ahlah_dashboard"))
        return redirect(url_for("main.index"))

    # -----------------------------------------------------------
    # 4) Шинжилгээ захиалах (Нэгтгэлээс)
    # -----------------------------------------------------------
    @bp.route("/request_analysis", methods=["POST"])
    @login_required
    async def request_analysis():
        """
        Нэгтгэлээс хоосон нүдэн дээр дарж шинжилгээ захиалах.
        Дээжний analyses_to_perform талбарт шинэ код нэмнэ.
        """
        if getattr(current_user, "role", None) not in ("senior", "admin"):
            return jsonify({"message": "Зөвхөн ахлах болон админ захиалж болно"}), 403

        data = request.get_json(silent=True) or {}
        sample_id = data.get("sample_id")
        analysis_code = data.get("analysis_code")

        if not sample_id or not analysis_code:
            return jsonify({"message": "sample_id болон analysis_code шаардлагатай"}), 400

        try:
            sample = Sample.query.get(sample_id)
            if not sample:
                return jsonify({"message": f"Дээж #{sample_id} олдсонгүй"}), 404

            # Одоо байгаа analyses_to_perform-г авах
            current_analyses = sample.analyses_to_perform or []
            if isinstance(current_analyses, str):
                try:
                    current_analyses = json.loads(current_analyses)
                except (json.JSONDecodeError, TypeError, ValueError):
                    current_analyses = []

            # Normalize code
            base_code = norm_code(analysis_code)
            if not base_code:
                base_code = analysis_code

            # Аль хэдийн байгаа эсэхийг шалгах
            existing_codes = [norm_code(c) for c in current_analyses]
            if base_code in existing_codes:
                return jsonify({"message": f"'{base_code}' шинжилгээ аль хэдийн захиалагдсан байна"}), 400

            # Шинэ код нэмэх
            current_analyses.append(base_code)
            sample.analyses_to_perform = json.dumps(current_analyses)
            sample.updated_at = now_local()

            # Audit log
            audit = AnalysisResultLog(
                timestamp=now_local(),
                user_id=current_user.id,
                sample_id=sample_id,
                analysis_code=base_code,
                action="ANALYSIS_REQUESTED",
                reason=f"Нэгтгэлээс '{base_code}' шинжилгээ захиалсан",
                sample_code_snapshot=sample.sample_code,
            )
            db.session.add(audit)
            db.session.commit()

            return jsonify({
                "message": f"'{base_code}' шинжилгээ амжилттай захиалагдлаа",
                "sample_id": sample_id,
                "analysis_code": base_code
            })

        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Request analysis error: {e}")
            return jsonify({"message": f"Алдаа: {str(e)}"}), 500

    # -----------------------------------------------------------
    # 5) Notification Check
    # -----------------------------------------------------------
    @bp.route("/check_ready_samples", methods=["GET"])
    @login_required
    async def check_ready_samples():
        try:
            cutoff_time = now_local() - timedelta(hours=12)
            pending_samples = Sample.query.filter(
                Sample.received_date >= cutoff_time,
                Sample.client_name == 'CHPP',
                Sample.sample_type.in_(['2 hourly', '4 hourly', '2 Hourly', '4 Hourly']),
                ~Sample.status.in_(['completed', 'reported', 'archived'])
            ).all()

            ready_count = 0
            ready_samples_list = []

            for s in pending_samples:
                calc = s.get_calculations()
                p_name = (s.product or "").upper()
                is_ready = False

                if "PF" in p_name:
                    if (calc.mt is not None) and (calc.aad is not None):
                        is_ready = True
                else:
                    if (
                        (calc.mt is not None) and (calc.mad is not None) and
                        (calc.aad is not None) and (calc.vad is not None) and
                        (calc.gi is not None)
                    ):
                        is_ready = True

                if is_ready:
                    ready_count += 1
                    ready_samples_list.append({
                        "sample_code": s.sample_code,
                        "time": s.received_date.strftime("%H:%M"),
                        "product": s.product
                    })

            return jsonify({
                "ready_count": ready_count,
                "samples": ready_samples_list,
                "timestamp": now_local().strftime("%H:%M:%S")
            })

        except Exception as e:
            current_app.logger.error(f"Notification Check Error: {e}")
            return jsonify({"ready_count": 0, "error": str(e)}), 500
