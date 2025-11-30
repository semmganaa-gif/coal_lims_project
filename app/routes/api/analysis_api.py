# app/routes/api/analysis_api.py
# -*- coding: utf-8 -*-
"""
Шинжилгээтэй холбоотой API endpoints:
  - /eligible_samples/<analysis_code>
  - /save_results (Logic from analysis_rules.py + Control Standards)
  - /update_result_status
"""

from flask import (
    request,
    jsonify,
    current_app,
    url_for,
    redirect,
)
from flask_login import login_required, current_user
from sqlalchemy import or_, not_
import traceback
import json

from app import db, limiter
from app.models import Sample, AnalysisResult, AnalysisResultLog, ControlStandard
from app.utils.datetime import now_local
from app.utils.normalize import normalize_raw_data
from app.utils.codes import norm_code, BASE_TO_ALIASES

# ✅ Дүрмийн логик импортлох (Шинэ файл)
from app.utils.analysis_rules import determine_result_status

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
    _to_float_or_none,
    _coalesce_diff,
    _effective_limit,
)


def register_routes(bp):
    """Route-уудыг өгөгдсөн blueprint дээр бүртгэх"""

    # -----------------------------------------------------------
    # 1) Ажлын талбарын "дээжүүд"
    # -----------------------------------------------------------
    @bp.route("/eligible_samples/<analysis_code>", methods=["GET"])
    @login_required
    @limiter.limit("30 per minute")
    def eligible_samples(analysis_code):
        base_code = norm_code(analysis_code).strip()
        if not base_code:
            return jsonify({"samples": []})

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
            Sample.status.in_(["new", "New"]),
            or_(*like_clauses),
            ~Sample.id.in_(existing_ids_subq),
        )

        if _requires_mass_gate(base_code):
            q = q.filter(or_(not_(_has_m_task_sql()), Sample.mass_ready.is_(True)))

        from app.constants import MAX_ANALYSIS_RESULTS
        rows = q.order_by(Sample.received_date.desc()).limit(MAX_ANALYSIS_RESULTS).all()

        samples = []
        for s in rows:
            samples.append({
                "id": s.id,
                "sample_code": s.sample_code or "",
                "name": getattr(s, "sample_name", None) or getattr(s, "name", None) or "",
                "client_name": s.client_name or "",
                "sample_type": s.sample_type or "",
                "received_date": s.received_date.strftime("%Y-%m-%d %H:%M") if s.received_date else "",
            })

        return jsonify({"samples": samples})

    # -----------------------------------------------------------
    # 2) Химич хадгалсан үр дүн → /api/save_results
    # -----------------------------------------------------------
    @bp.route("/save_results", methods=["POST"])
    @login_required
    @limiter.limit("30 per minute")
    def save_results():
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

                    sample = Sample.query.get(sample_id)
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
                    avg = _to_float_or_none(raw_norm.get("avg"))
                    diff = _coalesce_diff(raw_norm)
                    limit, mode, band = _effective_limit(analysis_code, avg)
                    effective_limit = (avg * limit) if (mode == "percent" and avg is not None) else limit
                    
                    if analysis_code == "CSN" and diff is None: diff = 0.0
                    t_exceeded = (diff is not None) and ((abs(diff) - (effective_limit or 0)) > 1e-9)
                    
                    raw_norm.update({
                        "t_band": band,
                        "limit_used": effective_limit,
                        "limit_mode": mode,
                        "t_exceeded": bool(t_exceeded),
                    })

                    # ============================================================
                    # 🛠 CONTROL SAMPLE LOGIC (Dry Basis Conversion)
                    # ============================================================
                    control_targets = None
                    val_to_check = final_result
                    
                    try:
                        # 1. Дээжийг таних
                        stype = (sample.sample_type or "").lower()
                        scode = (sample.sample_code or "")
                        is_control = (stype == "control") or ("CM-" in scode) or ("CM_" in scode)

                        if is_control and final_result is not None:
                            # 2. Идэвхтэй стандарт хайх
                            active_std = ControlStandard.query.filter_by(is_active=True).first()
                            
                            if active_std:
                                # JSON targets-ийг dict болгох
                                targets_map = active_std.targets
                                if isinstance(targets_map, str):
                                    try: targets_map = json.loads(targets_map)
                                    except: targets_map = {}

                                # 3. Стандарт дотор энэ код байгаа эсэх?
                                if isinstance(targets_map, dict) and analysis_code in targets_map:
                                    control_targets = targets_map[analysis_code]
                                    
                                    # --- 4. MAD (Чийг) ОЛОХ ЛОГИК ---
                                    current_mad = None
                                    
                                    # А. Одоо ирж буй өгөгдлөөс хайх
                                    for d in data:
                                        ac = (d.get("analysis_code") or "").lower()
                                        if ac == "mad": 
                                            try:
                                                current_mad = float(d.get("final_result"))
                                            except: pass
                                            break
                                    
                                    # Б. Баазаас хайх (Өмнө нь хадгалсан бол)
                                    if current_mad is None:
                                        calc = sample.get_calculations()
                                        if calc and calc.mad is not None:
                                            current_mad = calc.mad

                                    # 5. Хөрвүүлэлт (Mad олдсон бол)
                                    if current_mad is not None and 0 < current_mad < 100:
                                        # Эдгээр үзүүлэлтүүд л Dry руу хөрвөнө
                                        if analysis_code in ["Aad", "Vad", "CV", "TS", "St,ad", "S", "Qgr,ad"]:
                                            factor = 100.0 / (100.0 - current_mad)
                                            val_to_check = final_result * factor
                                            # Debug
                                            # print(f"Conversion: {final_result} -> {val_to_check}")

                    except Exception as e:
                        current_app.logger.error(f"CM Logic Error: {e}")
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
                    if new_status == "rejected" and "Control Failure" in (status_reason or ""):
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

                        if new_status == "approved": action = "CREATED_AUTO_APPROVED"
                        elif new_status == "rejected": action = "CREATED_REJECTED"
                        elif new_status == "pending_review": action = "CREATED_PENDING"
                        else: action = "CREATED"
                        
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

                        if new_status == "approved": action = "UPDATED_AUTO_APPROVED"
                        elif new_status == "rejected": action = "UPDATED_REJECTED"
                        elif new_status == "pending_review": action = "UPDATED_PENDING"
                        else: action = "UPDATED"

                        target_res_id = existing.id
                        raw_snapshot = existing.raw_data
                        final_snapshot = existing.final_result

                    # Audit Log
                    audit = AnalysisResultLog(
                        timestamp=now_local(),
                        user_id=current_user.id,
                        sample_id=sample_id,
                        analysis_result_id=target_res_id,
                        analysis_code=analysis_code,
                        action=action,
                        raw_data_snapshot=raw_snapshot,
                        final_result_snapshot=final_snapshot,
                        reason=reason,
                        error_reason=auto_error_reason,
                    )
                    db.session.add(audit)

                    saved_count += 1
                    results_for_response.append({
                        "sample_id": sample_id,
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
    def update_result_status(result_id, new_status):
        if getattr(current_user, "role", None) not in ("ahlah", "admin"):
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
    # 4) Notification Check
    # -----------------------------------------------------------
    @bp.route("/check_ready_samples", methods=["GET"])
    @login_required
    def check_ready_samples():
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
                    if (calc.mt is not None) and (calc.mad is not None) and (calc.aad is not None) and (calc.vad is not None) and (calc.gi is not None):
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