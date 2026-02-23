# app/routes/analysis/workspace.py
# -*- coding: utf-8 -*-
"""
Химичийн ажлын талбартай холбоотой routes:
  - /analysis_hub - Шинжилгээний хэлтсийн төв хуудас
  - /analysis_page/<analysis_code> - Тухайн шинжилгээний ажлын талбар
"""

import json

from flask import request, render_template, current_app, redirect, url_for
from flask_login import login_required, current_user
from sqlalchemy import or_
from sqlalchemy.orm import joinedload

from app import db
from app.models import AnalysisType, AnalysisResult, Sample, Equipment
from app.utils.codes import norm_code
from app.utils.security import escape_like_pattern
from app.constants import ERROR_REASON_LABELS
from app.config.analysis_schema import get_analysis_schema
from app.utils.sorting import custom_sample_sort_key
from app.utils.decorators import analysis_role_required
from app.config.qc_config import TIMER_PRESETS
from app.utils.qc import sulfur_map_for


# Codes used on WTL_MG combined page (for queries)
WTL_MG_CODES = ['MT', 'TRD', 'MG', 'MG_SIZE']
# Codes unique to MG only (hide from hub, redirect to WTL_MG)
MG_ONLY_CODES = ['MG', 'MG_SIZE']


def register_routes(bp):
    """Route-уудыг өгөгдсөн blueprint дээр бүртгэх"""

    # =====================================================================
    # 0. WTL_MG WORKSHEET (4 analyses on one page)
    # =====================================================================
    @bp.route("/analysis_page/WTL_MG")
    @login_required
    def wtl_mg_page():
        newly_selected_ids_str = request.args.get("sample_ids", "")
        new_ids_list = []
        if newly_selected_ids_str:
            temp_ids = [int(x) for x in newly_selected_ids_str.split(",") if x.isdigit()]
            new_ids_list = list(dict.fromkeys(temp_ids))

        # Approved sample IDs — only when ALL MG-only codes are approved
        # (MT/TRD are shared codes, only check MG-specific ones)
        code_approved_sets = {}
        for code in MG_ONLY_CODES:
            rows = db.session.query(AnalysisResult.sample_id).filter(
                AnalysisResult.analysis_code == code,
                AnalysisResult.status == "approved"
            ).distinct().all()
            code_approved_sets[code] = {r.sample_id for r in rows}
        if all(code_approved_sets.values()):
            approved_ids = set.intersection(*code_approved_sets.values())
        else:
            approved_ids = set()

        # Existing results: auto-load only by MG-only codes (not shared MT/TRD)
        # This prevents coal samples with MT/TRD from appearing here
        q = (
            AnalysisResult.query
            .options(joinedload(AnalysisResult.sample))
            .filter(
                AnalysisResult.user_id == current_user.id,
                AnalysisResult.analysis_code.in_(MG_ONLY_CODES),
            )
        )
        if approved_ids:
            q = q.filter(~AnalysisResult.sample_id.in_(approved_ids))
        existing_results = q.all()

        seen_ids = set()
        batch_a = []
        for res in existing_results:
            if res.sample and res.sample_id not in seen_ids:
                batch_a.append(res.sample)
                seen_ids.add(res.sample_id)

        batch_b = []
        if new_ids_list:
            new_samples_db = Sample.query.filter(Sample.id.in_(new_ids_list)).all()
            new_samples_map = {s.id: s for s in new_samples_db}
            for sid in new_ids_list:
                if sid not in seen_ids and sid not in approved_ids:
                    if sid in new_samples_map:
                        batch_b.append(new_samples_map[sid])
                        seen_ids.add(sid)

        batch_a.sort(key=lambda s: custom_sample_sort_key(s.sample_code or ""))
        samples_to_analyze = batch_a + batch_b

        if not samples_to_analyze and new_ids_list:
            valid_ids = [sid for sid in new_ids_list if sid not in approved_ids]
            if valid_ids:
                fallback_samples = Sample.query.filter(Sample.id.in_(valid_ids)).all()
                fallback_map = {s.id: s for s in fallback_samples}
                samples_to_analyze = [fallback_map[sid] for sid in valid_ids if sid in fallback_map]

        # Build results map per code: {code: {sample_id: {status, raw_data, final_result}}}
        mg_results_map = {code: {} for code in WTL_MG_CODES}
        if samples_to_analyze:
            sample_ids = [s.id for s in samples_to_analyze]
            all_results = AnalysisResult.query.filter(
                AnalysisResult.sample_id.in_(sample_ids),
                AnalysisResult.analysis_code.in_(WTL_MG_CODES),
                AnalysisResult.status.in_(["approved", "pending_review", "rejected"])
            ).all()
            for r in all_results:
                raw = r.raw_data
                if isinstance(raw, str):
                    try:
                        raw = json.loads(raw)
                    except (json.JSONDecodeError, TypeError):
                        raw = {}
                elif raw is None:
                    raw = {}
                reason_code = getattr(r, "rejection_category", None) or getattr(r, "error_reason", None)
                if r.status == "rejected" and reason_code != "data_entry":
                    raw = {}
                    final_result = None
                else:
                    final_result = r.final_result
                mg_results_map[r.analysis_code][r.sample_id] = {
                    "status": r.status,
                    "raw_data": raw,
                    "final_result": final_result
                }

        # Rejected samples info
        rejected_samples_info = {}
        if samples_to_analyze:
            sample_ids = [s.id for s in samples_to_analyze]
            rejected_results = AnalysisResult.query.filter(
                AnalysisResult.sample_id.in_(sample_ids),
                AnalysisResult.analysis_code.in_(WTL_MG_CODES),
                AnalysisResult.status == "rejected"
            ).all()
            for r in rejected_results:
                reason_val = getattr(r, "rejection_comment", None) or getattr(r, "reason", None) or "Ахлахаас буцаагдсан"
                rejected_samples_info[r.sample_id] = {
                    "reason": reason_val,
                    "reason_code": getattr(r, "rejection_category", None) or getattr(r, "error_reason", None) or getattr(r, "rejection_comment", None),
                    "rejected_at": r.updated_at.strftime("%Y-%m-%d %H:%M") if r.updated_at else "",
                }

        related_equipments = []
        try:
            related_equipments = (
                Equipment.query
                .filter(
                    or_(Equipment.status.is_(None), Equipment.status != 'retired')
                )
                .order_by(Equipment.name.asc())
                .limit(50)
                .all()
            )
        except Exception:
            pass

        return render_template(
            "analysis_page.html",
            title="WTL MG Шинжилгээ",
            analysis=type("V", (), {"code": "WTL_MG", "name": "WTL MG Шинжилгээ"})(),
            analysis_type=type("V", (), {"code": "WTL_MG", "name": "WTL MG Шинжилгээ"})(),
            analysis_code="WTL_MG",
            analysis_name="WTL MG Шинжилгээ",
            samples=samples_to_analyze,
            config={"template": "analysis_forms/wtl_mg_aggrid.html", "formula": "wtl_mg_aggrid"},
            mad_results_map={},
            rejected_samples_info=rejected_samples_info,
            existing_results_map={},
            timer_config={"layout": "right", "digit_size": "lg", "editable": False, "timers": []},
            gi_retest_modes={},
            sulfur_by_sample={},
            error_labels=ERROR_REASON_LABELS,
            related_equipments=related_equipments,
            paired_results_map={},
            aggrid_samples=samples_to_analyze,
            analysis_schema={},
            use_aggrid=True,
            mg_results_map=mg_results_map,
        )

    # =====================================================================
    # 1. АЖЛЫН ТАЛБАР (analysis_hub)
    # =====================================================================
    @bp.route("/analysis_hub")
    @login_required
    @analysis_role_required(["prep", "chemist", "senior", "manager", "admin"])
    def analysis_hub():
        user_role = current_user.role
        if user_role in ["admin", "senior", "manager"]:
            allowed_analyses = AnalysisType.query.order_by(AnalysisType.order_num).all()
        else:
            allowed_analyses = (
                AnalysisType.query.filter_by(required_role=user_role)
                .order_by(AnalysisType.order_num)
                .all()
            )

        # MG/MG_SIZE → нэг "WTL_MG" карт болгох (MT, TRD хэвээр үлдэнэ)
        has_mg = any(a.code in MG_ONLY_CODES for a in allowed_analyses)
        allowed_analyses = [a for a in allowed_analyses if a.code not in MG_ONLY_CODES]

        return render_template(
            "analysis_hub.html",
            title="Ажлын талбар",
            analysis_types=allowed_analyses,
            show_mg_card=has_mg,
        )

    # =====================================================================
    # 2. АЖЛЫН ХУУДАС (Analysis Page)
    # =====================================================================
    @bp.route("/analysis_page/<analysis_code>")
    @login_required
    def analysis_page(analysis_code):
        # MG-only codes redirect to combined WTL_MG page
        if analysis_code in MG_ONLY_CODES or analysis_code == 'WTL_MG':
            return redirect(url_for('analysis.wtl_mg_page', **request.args))

        analysis_type = AnalysisType.query.filter_by(code=analysis_code).first_or_404()
        base_code = norm_code(analysis_type.code) or analysis_type.code

        AnalysisView = type("AnalysisView", (), {})
        analysis_view = AnalysisView()
        analysis_view.code = base_code
        analysis_view.name = analysis_type.name

        # 1. ШИНЭЭР СОНГОСОН ID-НУУД
        newly_selected_ids_str = request.args.get("sample_ids", "")
        new_ids_list = []

        if newly_selected_ids_str:
            temp_ids = [int(x) for x in newly_selected_ids_str.split(",") if x.isdigit()]
            new_ids_list = list(dict.fromkeys(temp_ids))

        try:
            msg = (
                f"analysis_page code={analysis_type.code} "
                f"sample_ids_raw={newly_selected_ids_str} parsed_ids={new_ids_list}"
            )
            current_app.logger.warning(msg)
        except Exception:
            pass

        # 2. ХУУЧИН ХАДГАЛАГДСАН ҮР ДҮНГҮҮД
        approved_ids = [r.sample_id for r in db.session.query(AnalysisResult.sample_id).filter(
            AnalysisResult.analysis_code == analysis_type.code,
            AnalysisResult.status == "approved"
        ).distinct().all()]

        # ✅ joinedload ашиглан N+1 query асуудлыг шийдэв
        existing_results = (
            AnalysisResult.query
            .options(joinedload(AnalysisResult.sample))
            .filter(
                AnalysisResult.user_id == current_user.id,
                AnalysisResult.analysis_code == analysis_type.code,
                ~AnalysisResult.sample_id.in_(approved_ids)
            )
            .all()
        )

        seen_ids = set()

        # A. Хадгалагдсан дээжүүд (Багц A)
        batch_a = []
        for res in existing_results:
            if res.sample:
                batch_a.append(res.sample)
                seen_ids.add(res.sample_id)

        # B. Шинэ нэмсэн дээжүүд (Багц B)
        batch_b = []
        if new_ids_list:
            new_samples_db = Sample.query.filter(Sample.id.in_(new_ids_list)).all()
            new_samples_map = {s.id: s for s in new_samples_db}

            for sid in new_ids_list:
                if sid not in seen_ids and sid not in approved_ids:
                    if sid in new_samples_map:
                        batch_b.append(new_samples_map[sid])
                        seen_ids.add(sid)

        # 3. БАГЦ БҮРИЙН ДОТОР ЭРЭМБЭЛЭХ
        # Багц A - дотроо кодоор эрэмбэлнэ (хуучин хадгалагдсан дээжүүд)
        batch_a.sort(key=lambda s: custom_sample_sort_key(s.sample_code or ""))
        # Багц B - URL дарааллаар үлдээх (хэрэглэгчийн нэмсэн дараалал)
        # batch_b эрэмбэлэхгүй - нэмсэн дарааллаар харуулна

        # Багцын дараалал хадгалж нэгтгэх: A эхэнд, B дараа нь
        samples_to_analyze = batch_a + batch_b

        if new_ids_list:
            loaded_ids = {s.id for s in samples_to_analyze}
            # ✅ approved_ids шалгах - батлагдсан дээжийг нэмэхгүй
            missing_ids = [sid for sid in new_ids_list if sid not in loaded_ids and sid not in approved_ids]
            if missing_ids:
                fallback_samples = Sample.query.filter(Sample.id.in_(missing_ids)).all()
                fallback_map = {s.id: s for s in fallback_samples}
                ordered_extra = [fallback_map[sid] for sid in missing_ids if sid in fallback_map]
                samples_to_analyze.extend(ordered_extra)

        # Absolute fallback: if still empty but sample_ids were provided, load by ids as-is
        # ✅ approved_ids шалгах - батлагдсан дээжийг нэмэхгүй
        if not samples_to_analyze and new_ids_list:
            valid_ids = [sid for sid in new_ids_list if sid not in approved_ids]
            if valid_ids:
                fallback_samples = Sample.query.filter(Sample.id.in_(valid_ids)).all()
                fallback_map = {s.id: s for s in fallback_samples}
                samples_to_analyze = [fallback_map[sid] for sid in valid_ids if sid in fallback_map]

        try:
            msg = (
                f"analysis_page code={analysis_type.code} "
                f"samples_to_analyze={len(samples_to_analyze)} "
                f"ids={[s.id for s in samples_to_analyze]}"
            )
            current_app.logger.warning(msg)
        except Exception:
            pass

        # 4. БУСАД ӨГӨГДӨЛ
        mad_results_map = {}
        if (analysis_type.code == "Vad" or analysis_type.code == "TRD") and samples_to_analyze:
            sample_ids = [s.id for s in samples_to_analyze]
            approved_mad_results = AnalysisResult.query.filter(
                AnalysisResult.sample_id.in_(sample_ids),
                AnalysisResult.analysis_code == "Mad",
                AnalysisResult.status == "approved"
            ).all()
            mad_results_map = {r.sample_id: r.final_result for r in approved_mad_results}

        sulfur_by_sample = {}
        if samples_to_analyze and base_code == "CV":
            sample_ids = [s.id for s in samples_to_analyze]
            sulfur_by_sample = sulfur_map_for(sample_ids)

        rejected_samples_info = {}
        if samples_to_analyze:
            sample_ids = [s.id for s in samples_to_analyze]
            rejected_results = AnalysisResult.query.filter(
                AnalysisResult.sample_id.in_(sample_ids),
                AnalysisResult.analysis_code == analysis_type.code,
                AnalysisResult.status == "rejected"
            ).all()
            for r in rejected_results:
                reason_val = getattr(r, "rejection_comment", None) or getattr(r, "reason", None) or "Ахлахаас буцаагдсан"
                rejected_samples_info[r.sample_id] = {
                    "reason": reason_val,
                    "reason_code": getattr(r, "rejection_category", None) or getattr(r, "error_reason", None) or getattr(r, "rejection_comment", None),
                    "rejected_at": r.updated_at.strftime("%Y-%m-%d %H:%M") if r.updated_at else "",
                }

        existing_results_map = {}
        if samples_to_analyze:
            sample_ids = [s.id for s in samples_to_analyze]
            existing_results = AnalysisResult.query.filter(
                AnalysisResult.sample_id.in_(sample_ids),
                AnalysisResult.analysis_code == analysis_type.code,
                AnalysisResult.status.in_(["pending_review", "rejected"])
            ).all()
            for r in existing_results:
                raw = r.raw_data
                if isinstance(raw, str):
                    try:
                        raw = json.loads(raw)
                    except (json.JSONDecodeError, TypeError):
                        raw = {}
                elif raw is None:
                    raw = {}
                reason_code = getattr(r, "rejection_category", None) or getattr(r, "error_reason", None)

                # Ахлахын буцаалтын дүрэм:
                #  - "data_entry" (шивэлт/тооцооллын алдаа) → хуучин дүнгээ сэргээнэ.
                #  - Бусад шалтгаан → хуучин дүнг хоосолж шинээр оруулна.
                if r.status == "rejected" and reason_code != "data_entry":
                    raw = {}
                    final_result = None
                else:
                    final_result = r.final_result

                existing_results_map[r.sample_id] = {
                    "status": r.status,
                    "raw_data": raw,
                    "final_result": final_result
                }

        paired_results_map: dict[int, dict[str, dict]] = {}
        if samples_to_analyze:
            sample_ids = [s.id for s in samples_to_analyze]
            paired_targets = None
            if base_code in {"X", "Y"}:
                paired_targets = {"X", "Y"}
            elif base_code in {"CRI", "CSR"}:
                paired_targets = {"CRI", "CSR"}

            if paired_targets:
                paired_results = AnalysisResult.query.filter(
                    AnalysisResult.sample_id.in_(sample_ids),
                    AnalysisResult.analysis_code.in_(paired_targets),
                    AnalysisResult.status.in_(["pending_review", "rejected"])
                ).all()
                for r in paired_results:
                    raw = r.raw_data
                    if isinstance(raw, str):
                        try:
                            raw = json.loads(raw)
                        except (json.JSONDecodeError, TypeError):
                            raw = {}
                    elif raw is None:
                        raw = {}
                    reason_code = getattr(r, "rejection_category", None) or getattr(r, "error_reason", None)
                    if r.status == "rejected" and reason_code != "data_entry":
                        raw = {}
                        final_result = None
                    else:
                        final_result = r.final_result
                    base_pair_code = norm_code(r.analysis_code)
                    paired_results_map.setdefault(r.sample_id, {})[base_pair_code] = {
                        "status": r.status,
                        "raw_data": raw,
                        "final_result": final_result,
                    }

        # Template Config
        form_map = {
            "Aad": "ash_form_aggrid",
            "Mad": "mad_aggrid", "Vad": "vad_aggrid", "MT": "mt_aggrid",
            "TS": "sulfur_aggrid", "St,ad": "sulfur_aggrid",
            "CV": "cv_aggrid", "CSN": "csn_aggrid", "Gi": "Gi_aggrid", "TRD": "trd_aggrid",
            "P": "phosphorus_aggrid", "F": "fluorine_aggrid", "Cl": "chlorine_aggrid",
            "X": "xy_aggrid", "Y": "xy_aggrid",
            "CRI": "cricsr_aggrid", "CSR": "cricsr_aggrid",
            "Solid": "solid_aggrid", "SOLID": "solid_aggrid", "solid": "solid_aggrid",
            "FM": "free_moisture_aggrid",
            "m": "mass_aggrid",
            "WTL_MG": "wtl_mg_aggrid",
        }
        template_name = form_map.get(base_code, "default")

        config = {
            "template": f"analysis_forms/{template_name}.html",
            "formula": template_name
        }
        timer_config = TIMER_PRESETS.get(base_code, {
            "layout": "right",
            "digit_size": "lg",
            "editable": False,
            "timers": []
        })

        gi_retest_modes = {}
        if base_code == "Gi":
            for sample_id, info in rejected_samples_info.items():
                if info.get("reason_code") == "GI_RETEST_3_3":
                    gi_retest_modes[sample_id] = True

        related_equipments = []
        try:
            safe_code = escape_like_pattern(base_code)
            related_equipments = (
                Equipment.query
                .filter(
                    Equipment.related_analysis.ilike(f"%{safe_code}%"),
                    or_(Equipment.status.is_(None), Equipment.status != 'retired')
                )
                .order_by(Equipment.name.asc())
                .all()
            )
        except Exception:
            related_equipments = []

        # ✨ Check if this analysis uses AG Grid
        uses_aggrid = template_name.endswith('_aggrid') or template_name == 'ash_form_aggrid'

        return render_template(
            "analysis_page.html",
            title=analysis_type.name,
            analysis=analysis_view,
            analysis_type=analysis_type,
            analysis_code=analysis_type.code,
            analysis_name=analysis_type.name,
            samples=samples_to_analyze,
            config=config,
            mad_results_map=mad_results_map,
            rejected_samples_info=rejected_samples_info,
            existing_results_map=existing_results_map,
            timer_config=timer_config,
            gi_retest_modes=gi_retest_modes,
            sulfur_by_sample=sulfur_by_sample,
            error_labels=ERROR_REASON_LABELS,
            related_equipments=related_equipments,
            paired_results_map=paired_results_map,
            aggrid_samples=samples_to_analyze,
            analysis_schema=get_analysis_schema(base_code),
            use_aggrid=uses_aggrid,
        )
