# app/routes/api_routes.py (ШИНЭЧИЛСЭН - TRD,ad ба TRD,d-г зөв ялгасан)
# -*- coding: utf-8 -*-

from flask import (
    Blueprint,
    request,
    jsonify,
    current_app,
    url_for,
    redirect,
    render_template,   # 🆕 mass_workspace page
)
from flask_login import login_required, current_user
from datetime import datetime, timedelta # (!!!) timedelta-г импортлосон
from math import inf
import json

from sqlalchemy import or_, func, not_, and_

from app import db
from app.models import Sample, AnalysisResult, AnalysisResultLog, Bottle, BottleConstant
from app.utils.datetime import now_local
from app.utils.normalize import normalize_raw_data

# ✅ КОДЫН НЭРШЛИЙН НЭГДСЭН MAP/ХЭРЭГСЭЛ
from app.utils.codes import norm_code, to_base_list, BASE_TO_ALIASES

# (!!! ШИНЭЧЛЭЛ) conversions.py-г энд импортлох шаардлагатай
from app.utils.conversions import calculate_all_conversions
from app.utils.parameters import PARAMETER_DEFINITIONS, get_canonical_name # (!!!) get_canonical_name нэмсэн


api_bp = Blueprint("api", __name__, url_prefix="/api")


# -----------------------------
# 🧩 Mass gate хэрэгтэй эсэх (XY/CRI/CSR-д ХЭРЭГГҮЙ)
# -----------------------------
def _requires_mass_gate(code: str) -> bool:
    base = norm_code(code or "")
    return base not in {"X", "Y", "CRI", "CSR"}


def _has_m_task_sql():
    """analyses_to_perform JSON string дотор "m" байгаа эсэхийг case-insensitive шалгана."""
    return func.lower(Sample.analyses_to_perform).like('%"m"%')


# =========================
# 1) REVIEW/ДҮРЭМ – (өгөгдсөн)
# =========================
EPS = 1e-6

ANALYSIS_RULES = {
    "MT":   {"bands": [{"upper": 10.0, "limit": 0.50, "mode": "abs"},
                       {"upper": inf,  "limit": 0.50, "mode": "percent"}]},
    "Mad":  {"bands": [{"upper": 10.0, "limit": 0.20, "mode": "abs"},
                       {"upper": inf,  "limit": 0.40, "mode": "abs"}],
             "bands_detailed": [
                 {"upper": 0.50, "limit": 0.20, "mode": "abs"},
                 {"upper": 5.00, "limit": 0.20, "mode": "abs"},
                 {"upper": 10.0, "limit": 0.30, "mode": "abs"},
                 {"upper": inf,  "limit": 0.40, "mode": "abs"},
             ]},
    "Vad":  {"bands": [{"upper": 20.0, "limit": 0.30, "mode": "abs"},
                       {"upper": 40.0, "limit": 0.50, "mode": "abs"},
                       {"upper": inf,  "limit": 0.80, "mode": "abs"}]},
    "Aad":  {"bands": [{"upper": 15.0, "limit": 0.20, "mode": "abs"},
                       {"upper": 30.0, "limit": 0.30, "mode": "abs"},
                       {"upper": inf,  "limit": 0.50, "mode": "abs"}]},
    "CSN":  {"single": {"limit": 0.50, "mode": "abs"}},
    "TS":   {"bands": [{"upper": 2.0, "limit": 0.05, "mode": "abs"},
                       {"upper": 5.0, "limit": 0.10, "mode": "abs"},
                       {"upper": inf, "limit": 0.15, "mode": "abs"}]},
    "P":    {"bands": [{"upper": 0.2, "limit": 0.007, "mode": "abs"},
                       {"upper": inf, "limit": 0.010, "mode": "abs"}]},
    "Cl":   {"bands": [{"upper": 150.0, "limit": 15.0, "mode": "abs"},
                       {"upper": inf,   "limit": 0.10, "mode": "percent"}]},
    "F":    {"single": {"limit": 0.01, "mode": "abs"}},
    "CV":   {"single": {"limit": 120.0, "mode": "abs"}},
    "Y":    {"bands": [{"upper": 20.0, "limit": 1.0, "mode": "abs"},
                       {"upper": inf,  "limit": 2.0, "mode": "abs"}]},
}

T_LIMITS = {"Aad": 0.20, "Mad": 0.30, "MT": 0.50, "Vad": 0.30}
DEFAULT_T_LIMIT = 0.30

# (!!! ШИНЭЧЛЭЛ)
# Энэ хэсэг нь analysis_routes.py-аас ирсэн бололтой.
# SUMMARY_VIEW_COLUMNS-ийг энд нэмж, TRD-г засав.
SUMMARY_VIEW_COLUMNS = [
    {'code': 'MT',      'canonical_base': 'total_moisture'},
    {'code': 'Mad',     'canonical_base': 'inherent_moisture'},
    {'code': 'Aad',     'canonical_base': 'ash'},
    {'code': 'Ad',      'canonical_base': 'ash'},
    {'code': 'Vad',     'canonical_base': 'volatile_matter'},
    {'code': 'Vdaf',    'canonical_base': 'volatile_matter'},
    {'code': 'FC,ad',   'canonical_base': 'fixed_carbon_ad'},
    {'code': 'St,ad',   'canonical_base': 'total_sulfur'},
    {'code': 'St,d',    'canonical_base': 'total_sulfur'},
    {'code': 'Qgr,ad',  'canonical_base': 'calorific_value'},
    {'code': 'Qgr,ar',  'canonical_base': 'calorific_value'},
    {'code': 'Qnet,ar', 'canonical_base': 'calorific_value'},
    {'code': 'CSN',     'canonical_base': 'free_swelling_index'},
    {'code': 'Gi',      'canonical_base': 'caking_power'},
    # (!!! ЗАСВАР)
    {'code': 'TRD,ad',  'canonical_base': 'relative_density'},
    {'code': 'TRD,d',   'canonical_base': 'relative_density'}, # 'TRD' -> 'TRD,d' болгов
    # (/!!! ЗАСВАР)
    {'code': 'P,ad',    'canonical_base': 'phosphorus'},
    {'code': 'P,d',     'canonical_base': 'phosphorus'},
    {'code': 'F,ad',    'canonical_base': 'total_fluorine'},
    {'code': 'F,d',     'canonical_base': 'total_fluorine'},
    {'code': 'Cl,ad',   'canonical_base': 'total_chlorine'},
    {'code': 'Cl,d',    'canonical_base': 'total_chlorine'},
    {'code': 'X',       'canonical_base': 'plastometer_x'},
    {'code': 'Y',       'canonical_base': 'plastometer_y'},
    {'code': 'CRI',     'canonical_base': 'coke_reactivity_index'},
    {'code': 'CSR',     'canonical_base': 'coke_strength_after_reaction'},
    {'code': 'Solid',   'canonical_base': 'solid'},
    {'code': 'FM',      'canonical_base': 'free_moisture'},
    {'code': 'm',       'canonical_base': 'mass'},
]


def _to_float_or_none(x):
    try:
        if x is None:
            return None
        return float(x)
    except Exception:
        return None


def _coalesce_diff(raw_norm: dict) -> float | None:
    """raw_data-аас тохирцын зөрүүг (diff) олж буцаана."""
    raw = raw_norm or {}
    t_val = _to_float_or_none(raw.get("t"))
    if t_val is not None:
        return abs(t_val)
    diff = _to_float_or_none(raw.get("diff"))
    if diff is not None:
        return abs(diff)
    p1 = raw.get("p1") or {}
    p2 = raw.get("p2") or {}
    r1 = _to_float_or_none(p1.get("result"))
    r2 = _to_float_or_none(p2.get("result"))
    if r1 is not None and r2 is not None:
        return abs(r1 - r2)
    return None


def _pick_rule(analysis_code: str):
    base = norm_code(analysis_code)
    return ANALYSIS_RULES.get(base, {})


def _effective_limit(analysis_code: str, avg: float | None):
    """returns: (limit_value, mode, band_label)"""
    analysis_code = norm_code(analysis_code)
    rule = _pick_rule(analysis_code)
    band_label = None

    single = rule.get("single")
    if single:
        return single["limit"], single["mode"], band_label

    bands = rule.get("bands_detailed") or rule.get("bands")
    if bands and avg is not None:
        lower = None
        for b in bands:
            upper = b["upper"]
            if avg <= upper:
                if lower is None:
                    band_label = f"<{upper:g}"
                elif upper == inf:
                    band_label = f">{lower:g}"
                else:
                    band_label = f"{lower:.2f}–{upper:.2f}"
                return b["limit"], b["mode"], band_label
            lower = upper

    return T_LIMITS.get(analysis_code, DEFAULT_T_LIMIT), "abs", band_label


def should_require_review(analysis_code: str, raw_norm: dict) -> bool:
    analysis_code = norm_code(analysis_code)

    # Gi 5:1 → <18 бол автоматаар VOID (ахлах руу биш)
    if analysis_code == "Gi" and (raw_norm or {}).get("is_low_avg", False):
        return False

    # (!!!) TRD, CV, CSN, Gi: JS-ээс ирсэн 'limit_used'-г хүндэтгэнэ
    if analysis_code in ["CSN", "Gi", "CV", "TRD"] and "limit_used" in (raw_norm or {}):
        limit = _to_float_or_none(raw_norm.get("limit_used"))
        diff = _coalesce_diff(raw_norm)
        if diff is None or limit is None:
             return True # Алдаатай бол хянуулна
        return (abs(diff) - limit) > EPS

    # CSN/Gi: JS-ээс ирсэн flag-ийг шууд хүндэтгэнэ (Fallback)
    if analysis_code in ["CSN", "Gi"] and "t_exceeded" in (raw_norm or {}):
        return bool((raw_norm or {}).get("t_exceeded", True))

    avg = _to_float_or_none((raw_norm or {}).get("avg"))
    diff = _coalesce_diff(raw_norm)
    if diff is None:
        return True

    limit, mode, _band = _effective_limit(analysis_code, avg)
    effective_limit = (avg * limit) if (mode == "percent" and avg is not None) else limit
    return (abs(diff) - (effective_limit or 0)) > 1e-9


# -----------------------------------------------------------
# 1) DataTables-д өгөгдөл өгөх (index.html)
#    GET /api/data
# -----------------------------------------------------------
@api_bp.route("/data", methods=["GET"])
@login_required
def data():
    draw = int(request.args.get("draw", 1))
    start = int(request.args.get("start", 0))
    length = int(request.args.get("length", 25))

    # DataTables-н багана тус бүрийн шүүлтүүр
    column_search = {}
    i = 0
    while True:
        col_data = request.args.get(f"columns[{i}][data]")
        if col_data is None:
            break
        search_val = request.args.get(f"columns[{i}][search][value]", "").strip()
        column_search[i] = search_val
        i += 1

    date_start = request.args.get("dateFilterStart")
    date_end   = request.args.get("dateFilterEnd")

    q = Sample.query

    if date_start:
        try:
            ds = datetime.fromisoformat(date_start)
            q = q.filter(Sample.received_date >= ds)
        except Exception:
            pass
    if date_end:
        try:
            de = datetime.fromisoformat(date_end)
            q = q.filter(Sample.received_date <= de)
        except Exception:
            pass

    for idx, val in column_search.items():
        if not val:
            continue
        if idx == 1:
            try:
                q = q.filter(Sample.id == int(val))
            except Exception:
                pass
        elif idx == 2:
            q = q.filter(Sample.sample_code.ilike(f"%{val}%"))
        elif idx == 3:
            q = q.filter(Sample.client_name.ilike(f"%{val}%"))
        elif idx == 4:
            q = q.filter(Sample.sample_type.ilike(f"%{val}%"))
        elif idx == 5:
            q = q.filter(Sample.status.ilike(f"%{val}%"))
        elif idx == 6:
            q = q.filter(Sample.delivered_by.ilike(f"%{val}%"))
        elif idx == 7:
            q = q.filter(Sample.prepared_by.ilike(f"%{val}%"))
        elif idx == 9:
            q = q.filter(Sample.notes.ilike(f"%{val}%"))
        elif idx == 11:
            try:
                w = float(val)
                q = q.filter(Sample.weight == w)
            except Exception:
                pass
        elif idx == 13:
            q = q.filter(Sample.analyses_to_perform.ilike(f"%{val}%"))

    records_total = q.count()
    records_filtered = records_total

    samples = (
        q.order_by(Sample.received_date.desc())
         .offset(start)
         .limit(length)
         .all()
    )

    data_rows = []
    for s in samples:
        try:
            raw_codes = json.loads(s.analyses_to_perform or "[]")
        except Exception:
            raw_codes = []
        analyses_base = to_base_list(raw_codes)
        analyses_txt  = json.dumps(analyses_base, ensure_ascii=False)

        action_html = (
            f'<a href="{url_for("main.edit_sample", sample_id=s.id)}" '
            f'class="btn btn-sm btn-outline-primary">Засах</a>'
        )

        data_rows.append(
            [
                f'<input type="checkbox" class="sample-checkbox" value="{s.id}">',  # 0
                s.id,                                # 1
                s.sample_code or "",                 # 2
                s.client_name or "",                 # 3
                s.sample_type or "",                 # 4
                s.status or "",                      # 5
                s.delivered_by or "",                # 6
                s.prepared_by or "",                 # 7
                s.prepared_date.strftime("%Y-%m-%d") if s.prepared_date else "",  # 8
                s.notes or "",                       # 9
                s.received_date.strftime("%Y-%m-%d %H:%M") if s.received_date else "",  # 10
                s.weight or "",                      # 11
                s.status or "",                      # 12 (давхцаж буй ч таны өмнөх формат хадгалав)
                analyses_txt,                        # 13
                action_html,                         # 14
            ]
        )

    return jsonify(
        {
            "draw": draw,
            "recordsTotal": records_total,
            "recordsFiltered": records_filtered,
            "data": data_rows,
        }
    )


# -----------------------------------------------------------
# 2) Ажлын талбарын “дээжүүд”
#    GET /api/eligible_samples/<analysis_code>
# -----------------------------------------------------------
@api_bp.route("/eligible_samples/<analysis_code>", methods=["GET"])
@login_required
def eligible_samples(analysis_code):
    base_code = norm_code(analysis_code).strip()
    if not base_code:
        return jsonify({"samples": []})

    # 1) Энэ анализ дээр ХАДГАЛАГДСАН дээжүүдийг хасах
    existing_ids_subq = (
        db.session.query(AnalysisResult.sample_id)
        .filter(AnalysisResult.analysis_code == base_code)
        .distinct()
    )

    # 2) analyses_to_perform JSON string дотор кодыг case-insensitive барих
    text_lc = func.lower(Sample.analyses_to_perform)
    terms = [base_code.lower()]
    for alias_lc in (BASE_TO_ALIASES.get(base_code, []) or []):
        terms.append(alias_lc)

    like_clauses = [text_lc.like(f'%"{t}"%') for t in terms]

    # 3) Суурь query
    q = Sample.query.filter(
        Sample.status.in_(["new", "New"]),
        or_(*like_clauses),
        ~Sample.id.in_(existing_ids_subq),
    )

    # 4) Mass gate — XY/CRI/CSR-оос бусдад л,
    #    ГЭХДЭЭ зөвхөн дээж нь "m даалгавартай" бол gate-ийг шаардана.
    if _requires_mass_gate(base_code):
        q = q.filter(or_(not_(_has_m_task_sql()), Sample.mass_ready.is_(True)))

    rows = q.order_by(Sample.received_date.desc()).limit(200).all()

    # 5) Клиент рүү буцах JSON
    samples = []
    for s in rows:
        samples.append(
            {
                "id": s.id,
                "sample_code": s.sample_code or "",
                "name": getattr(s, "sample_name", None) or getattr(s, "name", None) or "",
                "client_name": s.client_name or "",
                "sample_type": s.sample_type or "",
                "received_date": s.received_date.strftime("%Y-%m-%d %H:%M") if s.received_date else "",
            }
        )

    return jsonify({"samples": samples})


# -----------------------------------------------------------
# 3) Химич хадгалсан үр дүн → /api/save_results
# -----------------------------------------------------------
@api_bp.route("/save_results", methods=["POST"])
@login_required
def save_results():
    current_app.logger.warning("HIT /api/save_results in %s", __file__)
    current_app.logger.warning("payload preview: %r", request.get_json(silent=True))

    data = request.get_json(silent=True)
    if not data or not isinstance(data, list):
        return jsonify({"message": "JSON массив ирсэнгүй"}), 400

    saved_count = 0
    results_for_response = []

    SINGLE_VALUE_CODES = {'FM', 'SOLID', 'X', 'Y', 'CRI', 'CSR'}
    PARALLEL_LIMITED_CODES = {'P,ad', 'F,ad', 'Cl,ad'}
    
    # (!!! ШИНЭЧЛЭЛ) TRD-г CV, TS-тэй ижил JS-д итгэх жагсаалтад нэмэв.
    JS_TRUSTED_CODES = {'CSN', 'Gi', 'TS', 'CV', 'TRD'}

    for item in data:
        sample_id = item.get("sample_id")
        analysis_code_in = item.get("analysis_code")
        analysis_code = norm_code(analysis_code_in)
        final_result = item.get("final_result")
        raw_in = item.get("raw_data") or {}

        if not sample_id or not analysis_code:
            continue

        # --- RAW normalization ---
        # (!!! ШИНЭЧЛЭЛ) TRD-г энэ жагсаалтад нэмсэн
        if analysis_code in (SINGLE_VALUE_CODES | JS_TRUSTED_CODES):
            # CV, TS, Gi, CSN, TRD, X, Y г.м. - JS-ээс ирсэн raw_data-г шууд авна
            raw_norm = raw_in
        else:
            # Mad, Aad, Vad г.м. - Сервер дээр Т-г дахин шалгана
            raw_norm = normalize_raw_data(raw_in, analysis_code)
            avg  = _to_float_or_none(raw_norm.get("avg"))
            diff = _coalesce_diff(raw_norm)
            limit, mode, band = _effective_limit(analysis_code, avg)
            effective_limit = (avg * limit) if (mode == "percent" and avg is not None) else limit
            t_exceeded = (diff is not None) and ((abs(diff) - (effective_limit or 0)) > 1e-9)
            raw_norm.update({
                "t_band": band,
                "limit_used": effective_limit,
                "limit_mode": mode,
                "t_exceeded": bool(t_exceeded),
            })

        # --- require_review тогтоох ---
        if analysis_code in SINGLE_VALUE_CODES:
            require_review = False
        elif analysis_code in PARALLEL_LIMITED_CODES:
            require_review = bool(raw_norm.get("t_exceeded", False))
        else:
            # (!!!) Энэ нь одоо TRD-г зөв шалгана (JS-ээс ирсэн limit_used-г ашиглана)
            require_review = should_require_review(analysis_code, raw_norm)

        # --- статус оноох ---
        new_status = ""
        rejection_comment_override = None
        if analysis_code == 'Gi' and (raw_norm or {}).get('is_low_avg', False):
            new_status = "rejected"
            final_result = None
            raw_norm = {"p1": {}, "p2": {}}
            rejection_comment_override = "GI_RETEST_3_3"
        elif require_review:
            new_status = "pending_review"
        else:
            new_status = "approved"

        # --- НЭГДСЭН ХАДГАЛАЛТ ---
        existing = (
            AnalysisResult.query.filter_by(
                sample_id=sample_id, analysis_code=analysis_code
            )
            .order_by(AnalysisResult.id.desc())
            .first()
        )

        is_single = analysis_code in SINGLE_VALUE_CODES
        def _auto_reason():
            return ("Single-entry (давталтгүй) тул автоматаар батлав"
                    if is_single else
                    "Т тохирц дотор тул автоматаар батлав")

        action = ""
        reason = item.get("rejection_comment") or "Химич хадгалсан"

        if not existing:
            new_res = AnalysisResult(
                sample_id=sample_id,
                user_id=current_user.id,
                analysis_code=analysis_code,
                final_result=final_result,
                status=new_status,
                created_at=now_local(),
                updated_at=now_local(),
                rejection_comment=rejection_comment_override
            )
            new_res.set_raw_data(raw_norm)
            db.session.add(new_res)
            db.session.flush()

            if new_status == "approved":
                action = "CREATED_AUTO_APPROVED"
                reason = _auto_reason()
            elif new_status == "rejected" and rejection_comment_override == "GI_RETEST_3_3":
                action = "CREATED_VOID_RETEST"
                reason = "Gi дундаж < 18 тул 3:3 дахин шинжилгээ рүү шилжүүлэв."
            elif new_status == "pending_review":
                action = "CREATED_PENDING"
                reason = "Химич хадгалсан (ахлах хяналт шаардлагатай)"
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
            existing.rejection_comment = rejection_comment_override
            db.session.flush()

            if new_status == "approved":
                action = "UPDATED_AUTO_APPROVED"
                reason = _auto_reason()
            elif new_status == "rejected" and rejection_comment_override == "GI_RETEST_3_3":
                action = "UPDATED_VOID_RETEST"
                reason = "Gi дундаж < 18 тул 3:3 дахин шинжилгээ рүү шилжүүлэв."
            elif new_status == "pending_review":
                action = "UPDATED_PENDING"
                reason = "Химич дахин хадгалсан (ахлах хяналт шаардлагатай)"
            else:
                action = "UPDATED"

            target_res_id = existing.id
            raw_snapshot = existing.raw_data
            final_snapshot = existing.final_result

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
        )
        db.session.add(audit)

        results_for_response.append({
            "sample_id": sample_id,
            "status": new_status,
            "raw_data": raw_norm
        })
        saved_count += 1

    db.session.commit()
    return jsonify({
        "message": f"{saved_count} мөр амжилттай хадгаллаа/боловсрууллаа.",
        "results": results_for_response
    }), 200


# -----------------------------------------------------------
# 4) Ахлахын буцаах/батлах → /api/update_result_status/<id>/<new_status>
# -----------------------------------------------------------
@api_bp.route("/update_result_status/<int:result_id>/<new_status>", methods=["POST"])
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

    res.status = new_status
    res.updated_at = now_local()
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
        reason=(
            rejection_comment
            or (f"{default_reason}. action={action_type}" if action_type else default_reason)
        ),
    )
    db.session.add(audit)
    db.session.commit()

    if request.headers.get("X-Requested-With") == "XMLHttpRequest" or request.is_json:
        return jsonify({"message": "OK", "status": new_status})

    if "analysis" in current_app.blueprints:
        return redirect(url_for("analysis.ahlah_dashboard"))
    return redirect(url_for("main.index"))


# -----------------------------------------------------------
# 5) sample_summary.html → архив / сэргээх (POST /api/update_sample_status)
# -----------------------------------------------------------
# (!!! Энэ хэсэг нь analysis_routes.py-аас ирсэн бололтой)
@api_bp.route("/sample_summary", methods=["GET", "POST"])
@login_required
def sample_summary():

    # --- POST (Архивлах) ---
    if request.method == "POST":
        action = request.form.get("action")
        sample_ids_str = request.form.get("sample_ids")
        if sample_ids_str and action in ["archive", "unarchive"]:
            try:
                sample_ids = [int(sid) for sid in sample_ids_str.split(',') if sid.isdigit()]
                if sample_ids:
                    new_status = "archived" if action == "archive" else "new" # (!!! "received" биш "new" болгов)
                    updated_count = (
                        db.session.query(Sample)
                        .filter(Sample.id.in_(sample_ids))
                        .update({Sample.status: new_status}, synchronize_session=False)
                    )
                    db.session.commit()
                    msg = (
                        f"{updated_count} дээжийг амжилттай архивд шилжүүллээ."
                        if action == "archive"
                        else f"{updated_count} дээжийг архивнаас амжилттай сэргээллээ."
                    )
                    flash(msg, "success")
                return redirect(url_for('api.sample_summary', **request.args))
            except Exception as e:
                db.session.rollback()
                flash(f"Архивлах үед алдаа гарлаа: {e}", "danger")

    # -----------------------------------------------------------------
    # --- GET (Хуудас ачааллах) ---
    # -----------------------------------------------------------------

    page = request.args.get("page", 1, type=int)
    start_date_str = request.args.get("start_date")
    end_date_str = request.args.get("end_date")
    show_archived = request.args.get("show_archived") == "on"
    filter_name = request.args.get("filter_name")

    # 1. Дээжүүдийг шүүж авах
    query = db.session.query(Sample)
    if show_archived:
        query = query.filter(Sample.status == "archived")
    else:
        query = query.filter(Sample.status != "archived")

    exists_q = (
        db.session.query(AnalysisResult.id)
        .filter(
            AnalysisResult.sample_id == Sample.id,
            AnalysisResult.status.in_(["approved", "pending_review"]),
        )
        .exists()
    )
    query = query.filter(exists_q)

    if start_date_str:
        try:
            start_date = datetime.strptime(start_date_str, "%Y-%m-%d")
            query = query.filter(Sample.received_date >= start_date)
        except ValueError:
            flash(f"'{start_date_str}' буруу огнооны формат байна.", "warning")
    if end_date_str:
        try:
            end_date = datetime.strptime(end_date_str, "%Y-%m-%d") + timedelta(days=1)
            query = query.filter(Sample.received_date < end_date)
        except ValueError:
            flash(f"'{end_date_str}' буруу огнооны формат байна.", "warning")
    if filter_name:
        query = query.filter(Sample.sample_code.ilike(f"%{filter_name}%"))

    query = query.order_by(Sample.received_date.desc())
    pagination = query.paginate(page=page, per_page=50, error_out=False)
    samples = pagination.items

    # -----------------------------------------------------------------
    # 🧮 ШИНЭЧИЛСЭН ТООЦООЛЛЫН ЛОГИК
    # -----------------------------------------------------------------

    results_map = {}
    analysis_dates_map = {}

    if samples:
        sample_ids = [s.id for s in samples]

        # 2) түүхий үр дүнг нэг дор
        all_db_results = (
            AnalysisResult.query
            .filter(
                AnalysisResult.sample_id.in_(sample_ids),
                AnalysisResult.status.in_(["approved", "pending_review"]),
            )
            .all()
        )

        # 3) sample + canonical
        canonical_results_by_sample = {sid: {} for sid in sample_ids}
        analysis_dates_raw_map = {sid: [] for sid in sample_ids}

        for r in all_db_results:
            canonical_name = get_canonical_name(r.analysis_code)
            if canonical_name:
                canonical_results_by_sample[r.sample_id][canonical_name] = {
                    "value": r.final_result,
                    "id": r.id,
                    "status": r.status,
                }
            if r.created_at:
                analysis_dates_raw_map[r.sample_id].append(r.created_at)

        # 4) тооцооллын хөдөлгүүр
        for sample_id in sample_ids:
            raw_canonical_data = canonical_results_by_sample.get(sample_id, {})

            all_calculated_data = calculate_all_conversions(
                raw_canonical_data,
                PARAMETER_DEFINITIONS
            )

            # 5) Template-д зориулж alias руу буцаах
            final_data_for_template = {}
            for col_view in SUMMARY_VIEW_COLUMNS:
                template_code = col_view['code']
                canonical_base = col_view['canonical_base']

                lookup_key = get_canonical_name(template_code)

                if   template_code == 'Ad':     lookup_key = 'ash_d'
                elif template_code == 'Vdaf':   lookup_key = 'volatile_matter_daf'
                elif template_code == 'FC,ad':  lookup_key = 'fixed_carbon_ad'
                elif template_code == 'FC,d':   lookup_key = 'fixed_carbon_d'
                elif template_code == 'FC,daf': lookup_key = 'fixed_carbon_daf'
                elif template_code == 'St,d':   lookup_key = 'total_sulfur_d'
                elif template_code == 'St,daf': lookup_key = 'total_sulfur_daf'
                elif template_code == 'Qgr,d':  lookup_key = 'calorific_value_d'
                elif template_code == 'Qgr,daf': lookup_key = 'calorific_value_daf'
                elif template_code == 'Qnet,ar': lookup_key = 'qnet_ar'
                # (!!! ШИНЭЧЛЭЛ)
                elif template_code == 'TRD,ad': lookup_key = 'relative_density'
                elif template_code == 'TRD,d':  lookup_key = 'relative_density_d'
                # (/!!! ШИНЭЧЛЭЛ)
                elif template_code == 'H,d':     lookup_key = 'hydrogen_d'
                elif template_code == 'P,d':     lookup_key = 'phosphorus_d'
                elif template_code == 'F,d':     lookup_key = 'total_fluorine_d'
                elif template_code == 'Cl,d':    lookup_key = 'total_chlorine_d'

                if lookup_key in all_calculated_data:
                    calculated_value = all_calculated_data[lookup_key]
                    if calculated_value is None:
                        continue

                    if isinstance(calculated_value, (int, float)):
                        raw_data_base = raw_canonical_data.get(canonical_base, {})
                        final_data_for_template[template_code] = {
                            "value": calculated_value,
                            "id": raw_data_base.get('id'),
                            "status": "calculated"
                        }
                    elif isinstance(calculated_value, dict):
                        final_data_for_template[template_code] = calculated_value

            results_map[sample_id] = final_data_for_template

        # 6) хамгийн эртний огноо
        for sample_id, dates in analysis_dates_raw_map.items():
            if dates:
                analysis_dates_map[sample_id] = min(dates).strftime("%Y-%m-%d")

        # 7) grid-д харуулах нэршлүүд
        final_analysis_types = []
        for col_map in SUMMARY_VIEW_COLUMNS:
            final_code = col_map['code']
            canonical_name = get_canonical_name(final_code)

            if   final_code == 'Ad':     canonical_name = 'ash_d'
            elif final_code == 'Vdaf':   canonical_name = 'volatile_matter_daf'
            elif final_code == 'FC,ad':  canonical_name = 'fixed_carbon_ad'
            elif final_code == 'FC,d':   canonical_name = 'fixed_carbon_d'
            elif final_code == 'FC,daf': canonical_name = 'fixed_carbon_daf'
            elif final_code == 'St,d':   canonical_name = 'total_sulfur_d'
            elif final_code == 'St,daf': canonical_name = 'total_sulfur_daf'
            elif final_code == 'Qgr,d':  canonical_name = 'calorific_value_d'
            elif final_code == 'Qgr,daf': canonical_name = 'calorific_value_daf'
            elif final_code == 'Qnet,ar': canonical_name = 'qnet_ar'
            # (!!! ШИНЭЧЛЭЛ)
            elif final_code == 'TRD,ad': canonical_name = 'relative_density'
            elif final_code == 'TRD,d':  canonical_name = 'relative_density_d'
            # (/!!! ШИНЭЧЛЭЛ)
            elif final_code == 'H,d':    canonical_name = 'hydrogen_d'
            elif final_code == 'P,d':    canonical_name = 'phosphorus_d'
            elif final_code == 'F,d':    canonical_name = 'total_fluorine_d'
            elif final_code == 'Cl,d':   canonical_name = 'total_chlorine_d'

            details = PARAMETER_DEFINITIONS.get(canonical_name)
            display_name = final_code
            if details and details.get('display_name'):
                display_name = details['display_name']
            
            # (!!! AnalysisType-г db.models-оос авах)
            try:
                fake_analysis_type = db.models.AnalysisType(code=final_code, name=display_name)
            except Exception:
                 fake_analysis_type = type("FakeType", (object,), {"code": final_code, "name": display_name})()
            final_analysis_types.append(fake_analysis_type)

    return render_template(
        "sample_summary.html",
        title="Дээжний нэгтгэл",
        samples=samples,
        analysis_types=final_analysis_types,
        results_map=results_map,
        analysis_dates_map=analysis_dates_map,
        pagination=pagination,
        show_archived=show_archived
    )


# -----------------------------------------------------------
# 6) ДЭЭЖНИЙ ТАЙЛАН (analysis_routes.py-аас)
# -----------------------------------------------------------
@api_bp.route("/sample_report/<int:sample_id>")
@login_required
def sample_report(sample_id):
    sample = Sample.query.get_or_404(sample_id)
    report_date = now_local()
    
    raw_results = (
        AnalysisResult.query
        .filter(
            AnalysisResult.sample_id == sample_id,
            AnalysisResult.status.in_(["approved", "pending_review"])
        )
        .all()
    )
    
    raw_canonical_data = {}
    for r in raw_results:
        canonical_name = get_canonical_name(r.analysis_code)
        if canonical_name:
            raw_canonical_data[canonical_name] = {
                "value": r.final_result,
                "id": r.id,
                "status": r.status,
            }

    try:
        sample_calcs = calculate_all_conversions(
            raw_canonical_data,
            PARAMETER_DEFINITIONS
        )
    except Exception as e:
        flash(
            f"Тооцоолол хийхэд алдаа гарлаа: {e}. Шаардлагатай (MT, Mad) утгууд орсон эсэхийг шалгана уу.",
            "danger",
        )
        return redirect(request.referrer or url_for("api.sample_summary"))

    return render_template(
        "report.html",
        title=f"Тайлан: {sample.sample_code}",
        sample=sample,
        calcs=sample_calcs, # Энэ бол тооцоолсон бүх утгатай dict
        report_date=report_date,
    )


# -----------------------------------------------------------
# 7) АУДИТЫН ТӨВ (analysis_routes.py-аас)
# -----------------------------------------------------------
@api_bp.route("/audit_hub")
@login_required
def audit_hub():
    return render_template("audit_hub.html", title="Аудитын мөр")


# -----------------------------------------------------------
# 8) АУДИТЫН МӨР ХУУДАС (analysis_routes.py-аас)
# -----------------------------------------------------------
@api_bp.route("/audit_log/<analysis_code>")
@login_required
def audit_log_page(analysis_code):
    # AnalysisType хэрэгтэй
    try:
        AnalysisType = db.models.AnalysisType
    except Exception:
        # Хэрэв models.py-д байхгүй бол AnalysisResult-аас нэрийг нь таамаглана
        first_res = AnalysisResult.query.filter_by(analysis_code=analysis_code).first()
        if first_res:
            analysis_type = type("FakeType", (object,), {"code": analysis_code, "name": first_res.analysis_code})()
        else:
            analysis_type = type("FakeType", (object,), {"code": analysis_code, "name": analysis_code})()
    else:
        analysis_type = AnalysisType.query.filter_by(code=analysis_code).first_or_404()


    start_date_str = request.args.get("start_date")
    end_date_str = request.args.get("end_date")
    sample_name_str = request.args.get("sample_name")
    user_name_str = request.args.get("user_name")

    q = (
        db.session.query(AnalysisResultLog, Sample, db.models.User)
        .join(Sample, AnalysisResultLog.sample_id == Sample.id)
        .join(db.models.User, AnalysisResultLog.user_id == db.models.User.id)
        .filter(AnalysisResultLog.analysis_code == analysis_code)
    )

    if start_date_str:
        try:
            start_date = datetime.strptime(start_date_str, "%Y-%m-%d")
            q = q.filter(AnalysisResultLog.timestamp >= start_date)
        except ValueError:
            flash("Буруу эхлэх огноо.", "warning")
    if end_date_str:
        try:
            end_date = datetime.strptime(end_date_str, "%Y-%m-%d")
            end_dt = datetime.combine(end_date, datetime.max.time())
            q = q.filter(AnalysisResultLog.timestamp <= end_dt)
        except ValueError:
            flash("Буруу дуусах огноо.", "warning")
    if sample_name_str:
        q = q.filter(Sample.sample_code.ilike(f"%{sample_name_str}%"))
    if user_name_str:
        q = q.filter(db.models.User.username.ilike(f"%{user_name_str}%"))

    rows = q.order_by(AnalysisResultLog.timestamp.desc()).all()

    prepared_logs = []
    for log_obj, sample_obj, user_obj in rows:
        view_obj = type("AuditView", (), {})()
        view_obj.id = log_obj.id
        view_obj.sample_id = log_obj.sample_id
        view_obj.analysis_result_id = log_obj.analysis_result_id
        view_obj.analysis_code = log_obj.analysis_code
        view_obj.action = log_obj.action
        view_obj.final_result_snapshot = log_obj.final_result_snapshot
        view_obj.raw_data_snapshot = log_obj.raw_data_snapshot
        view_obj.reason = log_obj.reason
        view_obj.timestamp = log_obj.timestamp
        view_obj.sample = sample_obj
        view_obj.user = user_obj
        prepared_logs.append(view_obj)

    from app.utils.normalize import normalize_raw_data

    def get_log_raw_data(log):
        try:
            parsed = json.loads(log.raw_data_snapshot or "{}")
        except Exception:
            parsed = {}
        return normalize_raw_data(parsed, analysis_type.code)

    return render_template(
        "audit_log_page.html",
        title=f"Аудит: {analysis_type.name}",
        analysis_type=analysis_type,
        logs=prepared_logs,
        get_log_raw_data=get_log_raw_data,
    )

# -----------------------------------------------------------
# 9) ДЭЭЖНИЙ ТҮҮХ (analysis_routes.py-аас)
# -----------------------------------------------------------
@api_bp.route("/sample_history/<int:sample_id>")
@login_required
def sample_history(sample_id):
    sample = Sample.query.get_or_404(sample_id)
    results = (
        AnalysisResult.query
        .filter_by(sample_id=sample_id)
        .order_by(AnalysisResult.created_at.desc())
        .all()
    )
    logs = (
        AnalysisResultLog.query
        .filter_by(sample_id=sample_id)
        .order_by(AnalysisResultLog.timestamp.desc())
        .all()
    )
    return render_template(
        "sample_history.html",
        title=f"Түүх: {sample.sample_id}", # (!!! sample.sample_id биш sample.sample_code байх)
        sample=sample,
        results=results,
        logs=logs,
    )

# -----------------------------------------------------------
# 10) МАССЫН АЖЛЫН ТАЛБАР (analysis_routes.py-аас)
# -----------------------------------------------------------
@api_bp.route("/mass/update_sample_status", methods=["POST"])
@login_required
def update_sample_status():
    action = request.form.get("action")
    sample_ids = request.form.getlist("sample_ids")

    if not sample_ids:
        if request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return jsonify({"message": "Дээж сонгогдоогүй"}), 400
        return redirect(url_for("api.sample_summary"))

    try:
        sample_ids_int = [int(sid) for sid in sample_ids]
    except ValueError:
        sample_ids_int = []

    samples = Sample.query.filter(Sample.id.in_(sample_ids_int)).all()
    count = 0
    for s in samples:
        if action == "archive":
            s.status = "archived"
            count += 1
        elif action == "unarchive":
            s.status = "new"
            count += 1

    db.session.commit()

    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        return jsonify({"message": f"{count} дээжийн статус шинэчлэгдлээ."}), 200

    return redirect(url_for("api.sample_summary"))


# ===========================================================
# 6) 🆕 Массын ажлын талбар (+ delete / unready / update)
# ===========================================================

from sqlalchemy import and_

# (!!! Энэ 2 функцийг дээр тодорхойлсон тул эндээс хасав)
# def _has_m_task_sql():
#     """analyses_to_perform JSON string дотор "m" байгаа эсэхийг case-insensitive шалгана."""
#     return func.lower(Sample.analyses_to_perform).like('%"m"%')

# def _can_delete_sample() -> bool:
#     """Админ эсвэл ахлах л бүрэн устгах эрхтэй гэж тогтоож байна."""
#     return getattr(current_user, "role", "") in {"admin", "ahlah"}

@api_bp.route("/mass/eligible", methods=["GET"])
@login_required
def mass_eligible():
    """
    Массын ажлын талбарт харагдах дээжүүд:
      - status ∈ {"new","New"}
      - analyses_to_perform дотор "m" байгаа
      - include_ready=0 (default) үед mass_ready != True л гарна
      - include_ready=1 үед mass_ready == True мөрүүдийг ч хамт харуулна (саарал badge)
      - q=<sample_code> хайлт
    """
    include_ready = request.args.get("include_ready", "0") in ("1", "true", "True")
    q_text = (request.args.get("q") or "").strip()

    base_filters = [
        Sample.status.in_(["new", "New"]),
        _has_m_task_sql(),
    ]

    if not include_ready:
        base_filters.append(or_(Sample.mass_ready.is_(False), Sample.mass_ready.is_(None)))

    q = Sample.query.filter(and_(*base_filters))

    if q_text:
        q = q.filter(Sample.sample_code.ilike(f"%{q_text}%"))

    rows = (
        q.order_by(Sample.received_date.desc())
         .limit(400)
         .all()
    )

    return jsonify({
        "samples": [
            {
                "id": s.id,
                "sample_code": s.sample_code or "",
                "client_name": s.client_name or "",
                "sample_type": s.sample_type or "",
                "weight": s.weight,
                "received_date": s.received_date.strftime("%Y-%m-%d %H:%M") if s.received_date else "",
                "mass_ready": bool(getattr(s, "mass_ready", False)),
            } for s in rows
        ]
    })


@api_bp.route("/mass/save", methods=["POST"])
@login_required
def mass_save():
    """
    Payload:
    {
      "items": [{"sample_id": 123, "weight": 2500.0}, ...],
      "mark_ready": true   # default: true
    }
    """
    data = request.get_json(silent=True) or {}
    items = data.get("items") or []
    mark_ready = bool(data.get("mark_ready", True))

    if not items:
        return jsonify({"ok": False, "message": "Хадгалах мөр олдсонгүй."}), 400

    user_id = getattr(current_user, "id", None)
    now_ts = now_local()

    updated = []
    for it in items:
        sid = it.get("sample_id")
        if not sid:
            continue
        s = Sample.query.get(sid)
        if not s:
            continue

        # weight шинэчлэх
        if "weight" in it and isinstance(it.get("weight"), (int, float)):
            s.weight = float(it["weight"])

        # mass_ready тэмдэглэх эсэх
        if mark_ready:
            s.mass_ready = True
            s.mass_ready_at = now_ts
            s.mass_ready_by_id = user_id

        db.session.add(s)
        updated.append(sid)

    if not updated:
        return jsonify({"ok": False, "message": "Мөрүүд хүчинтэй биш байна."}), 400

    db.session.commit()
    return jsonify({"ok": True, "message": f"{len(updated)} дээж шинэчлэгдлээ.", "updated_ids": updated})


@api_bp.route("/mass/update_weight", methods=["POST"])
@login_required
def mass_update_weight():
    """
    Mass Ready болсон байсан ч зөвхөн жинг нь засаж хадгална.
    Payload: {"sample_id": 123, "weight": 1800}
    """
    data = request.get_json(silent=True) or {}
    sid = data.get("sample_id")
    w = data.get("weight")
    if not sid or not isinstance(w, (int, float)):
        return jsonify({"ok": False, "message": "Параметр дутуу."}), 400

    s = Sample.query.get(sid)
    if not s:
        return jsonify({"ok": False, "message": "Дээж олдсонгүй."}), 404

    s.weight = float(w)
    s.received_date = s.received_date or now_local()  # хоосон байсан тохиолдолд
    db.session.add(s)
    db.session.commit()
    return jsonify({"ok": True, "message": "Жин шинэчлэгдлээ.", "sample_id": s.id})


@api_bp.route("/mass/unready", methods=["POST"])
@login_required
def mass_unready():
    """
    mass_ready-г буцааж false болгоно.
    Payload: {"sample_ids":[1,2,3]}
    """
    data = request.get_json(silent=True) or {}
    ids = data.get("sample_ids") or []
    if not ids:
        return jsonify({"ok": False, "message": "ID ирсэнгүй."}), 400

    rows = Sample.query.filter(Sample.id.in_(ids)).all()
    for s in rows:
        s.mass_ready = False
        s.mass_ready_at = None
        s.mass_ready_by_id = None
        db.session.add(s)
    db.session.commit()
    return jsonify({"ok": True, "message": f"{len(rows)} дээжийг Unready болголоо."})


@api_bp.route("/mass/delete", methods=["POST"])
@login_required
def mass_delete():
    """
    Дээжийг бүртгэлээс бүр мөсөн устгана (каскадтай).
    Payload: {"sample_id": 123}
    Зөвхөн admin/ahlah.
    """
    if not _can_delete_sample():
        return jsonify({"ok": False, "message": "Энэ үйлдэлд эрх хүрэхгүй."}), 403

    data = request.get_json(silent=True) or {}
    sid = data.get("sample_id")
    if not sid:
        return jsonify({"ok": False, "message": "ID дутуу."}), 400

    s = Sample.query.get(sid)
    if not s:
        return jsonify({"ok": False, "message": "Дээж олдсонгүй."}), 404

    db.session.delete(s)
    db.session.commit()
    return jsonify({"ok": True, "message": "Дээж устгагдлаа.", "deleted_id": sid})