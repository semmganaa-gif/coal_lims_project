# app/services/analysis_workflow.py
# -*- coding: utf-8 -*-
"""
Analysis workflow service: business logic extracted from route handlers.

All functions accept plain Python parameters and return plain Python objects.
No Flask request/jsonify/flash/redirect/current_user imports.
"""

import json
import logging
from datetime import datetime

from markupsafe import escape
from sqlalchemy import or_, func, case
from flask_babel import lazy_gettext as _l
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm.exc import StaleDataError

from app import db, cache
from app.config.analysis_schema import get_analysis_schema
from app.models import (
    AnalysisResult, AnalysisResultLog, Sample, User, AnalysisType,
    ControlStandard, GbwStandard,
)
from app.repositories import (
    AnalysisTypeRepository, ControlStandardRepository,
    GbwStandardRepository, EquipmentRepository,
)
from app.services.analysis_audit import log_analysis_action
from app.utils.audit import log_audit
from app.utils.codes import norm_code
from app.utils.converters import to_float
from app.utils.datetime import now_local
from app.utils.normalize import normalize_raw_data
from app.utils.notifications import notify_sample_status_change
from app.utils.security import escape_like_pattern
from app.utils.settings import get_error_reason_labels
from app.utils.shifts import get_shift_info
from app.utils.analysis_rules import determine_result_status
from app.utils.server_calculations import verify_and_recalculate
from app.utils.transaction import transactional
from app.utils.validators import (
    validate_sample_id,
    validate_analysis_code,
    validate_analysis_result,
    validate_equipment_id,
)

logger = logging.getLogger(__name__)

# DB code -> Standard code mapping (used in QC checks)
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
    'CV': 'CVdb,MJ/kg',
    'TS': 'Stdb,%',
    'TRD': 'TRDdb,g/cm3',
    'CSN': 'CSN',
    'Gi': 'Gi',
    'P': 'Pdb,%',
    'F': 'Fdb,mg/g',
    'Cl': 'Cldb,%',
    'Mad': 'Mad',
}


# =========================================================================
# SCHEMA LOADING
# =========================================================================

def load_analysis_schemas():
    """
    Load analysis schemas for all known analysis type codes.

    Returns:
        dict: Mapping of code -> schema, with '_default' key for fallback.
    """
    schema_map = {"_default": get_analysis_schema(None)}
    try:
        codes = AnalysisTypeRepository.get_codes()
        for code in codes:
            schema_map[code] = get_analysis_schema(code)
    except (ValueError, KeyError) as exc:
        logger.warning("Failed to load analysis schemas: %s", exc)
    return schema_map


# =========================================================================
# DASHBOARD DATA
# =========================================================================

def build_pending_results(start_date=None, end_date=None, sample_name=None):
    """
    Query pending/rejected analysis results for senior dashboard.

    Args:
        start_date: Optional date string 'YYYY-MM-DD'
        end_date: Optional date string 'YYYY-MM-DD'
        sample_name: Optional sample code search term

    Returns:
        list[dict]: Processed result dicts ready for JSON serialization.
    """
    q = (
        db.session.query(AnalysisResult, Sample, User, AnalysisType)
        .join(Sample, AnalysisResult.sample_id == Sample.id)
        .join(User, AnalysisResult.user_id == User.id)
        .join(AnalysisType, AnalysisResult.analysis_code == AnalysisType.code)
        .filter(
            or_(
                AnalysisResult.status == "pending_review",
                AnalysisResult.status == "rejected",
            )
        )
    )

    if start_date:
        try:
            sd = datetime.strptime(start_date, "%Y-%m-%d")
            q = q.filter(AnalysisResult.updated_at >= sd)
        except ValueError:
            pass

    if end_date:
        try:
            ed = datetime.strptime(end_date, "%Y-%m-%d")
            ed = datetime.combine(ed, datetime.max.time())
            q = q.filter(AnalysisResult.updated_at <= ed)
        except ValueError:
            pass

    if sample_name:
        safe_name = escape_like_pattern(sample_name)
        q = q.filter(Sample.sample_code.ilike(f"%{safe_name}%"))

    results_to_review = q.order_by(AnalysisResult.updated_at.desc()).limit(500).all()

    processed_results = []
    for result, sample, user, analysis_type in results_to_review:
        data_dict = {}
        raw_data = result.raw_data
        if isinstance(raw_data, str):
            try:
                data_dict = json.loads(raw_data)
            except json.JSONDecodeError:
                data_dict = {}
        elif isinstance(raw_data, dict):
            data_dict = dict(raw_data)
        else:
            data_dict = {}

        normalized = normalize_raw_data(data_dict, analysis_type.code)
        if normalized:
            data_dict.update(normalized)

        is_csn = analysis_type.code == "CSN"
        diff = data_dict.get("diff")
        avg = data_dict.get("avg")
        t_val = data_dict.get("t") if is_csn else diff
        avg_val = data_dict.get("avg") if is_csn else avg
        final_display = avg_val if not is_csn else result.final_result

        processed_results.append({
            "result_id": result.id,
            "sample_code": sample.sample_code,
            "analysis_name": analysis_type.name,
            "analysis_code": analysis_type.code,
            "status": result.status,
            "error_reason": result.error_reason,
            "raw_data": data_dict,
            "t_value": t_val,
            "final_value": final_display if final_display is not None else result.final_result,
            "user_name": user.username,
            "updated_at": result.updated_at.strftime("%Y-%m-%d %H:%M") if result.updated_at else None,
        })

    return processed_results


def build_dashboard_stats():
    """
    Build senior dashboard statistics (chemist counts, sample counts, etc.).

    Returns:
        dict: Statistics data ready for JSON serialization.
    """
    shift_info = get_shift_info(now_local())
    today_start = shift_info.shift_start
    today_end = shift_info.shift_end

    # 1. Analysis count per chemist today
    chemist_stats = (
        db.session.query(
            User.username,
            User.id.label("user_id"),
            func.count(AnalysisResult.id).label("total"),
            func.sum(case((AnalysisResult.status == "approved", 1), else_=0)).label("approved"),
            func.sum(case((AnalysisResult.status == "pending_review", 1), else_=0)).label("pending"),
            func.sum(case((AnalysisResult.status == "rejected", 1), else_=0)).label("rejected"),
        )
        .join(AnalysisResult, AnalysisResult.user_id == User.id)
        .filter(User.role.in_(["chemist", "senior", "preparer"]))
        .filter(AnalysisResult.updated_at >= today_start)
        .filter(AnalysisResult.updated_at <= today_end)
        .group_by(User.id, User.username)
        .order_by(func.count(AnalysisResult.id).desc())
        .all()
    )

    chemist_list = [
        {
            "username": row.username,
            "user_id": row.user_id,
            "total": row.total,
            "approved": row.approved or 0,
            "pending": row.pending or 0,
            "rejected": row.rejected or 0,
        }
        for row in chemist_stats
    ]

    # 2. Sample registration count today
    today_samples = (
        db.session.query(func.count(Sample.id))
        .filter(Sample.received_date >= today_start)
        .filter(Sample.received_date <= today_end)
        .scalar() or 0
    )

    # 2a. Samples by unit (client_name)
    samples_by_unit = (
        db.session.query(
            Sample.client_name,
            func.count(Sample.id).label("count"),
        )
        .filter(Sample.received_date >= today_start)
        .filter(Sample.received_date <= today_end)
        .group_by(Sample.client_name)
        .order_by(func.count(Sample.id).desc())
        .all()
    )

    unit_list = [
        {"name": row.client_name or _l("Тодорхойгүй"), "count": row.count}
        for row in samples_by_unit
    ]

    # 2b. Samples by type (sample_type)
    samples_by_type = (
        db.session.query(
            Sample.sample_type,
            func.count(Sample.id).label("count"),
        )
        .filter(Sample.received_date >= today_start)
        .filter(Sample.received_date <= today_end)
        .group_by(Sample.sample_type)
        .order_by(func.count(Sample.id).desc())
        .all()
    )

    type_list = [
        {"name": row.sample_type or _l("Тодорхойгүй"), "count": row.count}
        for row in samples_by_type
    ]

    # 3. Analysis count by type (today)
    analysis_type_stats = (
        db.session.query(
            AnalysisType.code,
            AnalysisType.name,
            func.count(AnalysisResult.id).label("total"),
            func.sum(case((AnalysisResult.status == "approved", 1), else_=0)).label("approved"),
            func.sum(case((AnalysisResult.status == "pending_review", 1), else_=0)).label("pending"),
            func.sum(case((AnalysisResult.status == "rejected", 1), else_=0)).label("rejected"),
        )
        .join(AnalysisResult, AnalysisResult.analysis_code == AnalysisType.code)
        .filter(AnalysisResult.updated_at >= today_start)
        .filter(AnalysisResult.updated_at <= today_end)
        .group_by(AnalysisType.code, AnalysisType.name)
        .order_by(func.count(AnalysisResult.id).desc())
        .all()
    )

    analysis_list = [
        {
            "code": row.code,
            "name": row.name,
            "total": row.total,
            "approved": row.approved or 0,
            "pending": row.pending or 0,
            "rejected": row.rejected or 0,
        }
        for row in analysis_type_stats
    ]

    # 4. Total counts (today)
    summary_row = (
        db.session.query(
            func.count(AnalysisResult.id).label("total"),
            func.sum(case((AnalysisResult.status == "approved", 1), else_=0)).label("approved"),
            func.sum(case((AnalysisResult.status == "pending_review", 1), else_=0)).label("pending"),
            func.sum(case((AnalysisResult.status == "rejected", 1), else_=0)).label("rejected"),
        )
        .filter(AnalysisResult.updated_at >= today_start)
        .filter(AnalysisResult.updated_at <= today_end)
        .one()
    )

    return {
        "chemists": chemist_list,
        "analysis_types": analysis_list,
        "samples_today": today_samples,
        "samples_by_unit": unit_list,
        "samples_by_type": type_list,
        "summary": {
            "total": summary_row.total or 0,
            "approved": summary_row.approved or 0,
            "pending": summary_row.pending or 0,
            "rejected": summary_row.rejected or 0,
        },
    }


# =========================================================================
# APPROVAL / REJECTION LOGIC
# =========================================================================

def _apply_status_fields(res, new_status, rejection_category=None, rejection_comment=None):
    """Apply status-related field changes to an AnalysisResult."""
    res.status = new_status
    res.updated_at = now_local()

    if new_status == "rejected":
        if hasattr(res, "rejection_category"):
            res.rejection_category = rejection_category
        if hasattr(res, "rejection_comment"):
            res.rejection_comment = rejection_comment or _l("Ахлах буцаасан")
        if hasattr(res, "error_reason"):
            res.error_reason = rejection_category
    else:
        if hasattr(res, "rejection_category"):
            res.rejection_category = None
        if hasattr(res, "rejection_comment"):
            res.rejection_comment = None
        if hasattr(res, "error_reason"):
            res.error_reason = None


@transactional()
def _update_result_status_atomic(result_id, new_status, rejection_category,
                                 safe_comment, rejection_comment_raw):
    """update_result_status-ийн atomic core (lock + workflow check + update + audit).

    Returns:
        tuple: (payload_dict_or_None, error_msg, status_code)
            payload: {"res_id", "sample_id", "old_status", "engine", "res"}
                — engine, res нь post-commit hook-д хэрэгтэй
    """
    # Row lock to prevent lost update
    res = AnalysisResult.query.filter_by(id=result_id).with_for_update().first()
    if not res:
        return None, _l("Үр дүн олдсонгүй"), 404

    old_status = res.status

    # Workflow engine validation (configurable transitions)
    from app.services.workflow_engine import WorkflowEngine
    engine = None
    try:
        engine = WorkflowEngine("analysis_result")
        from flask_login import current_user as _cu
        user_role = _cu.role if hasattr(_cu, 'role') else "admin"
        ctx = {"comment": rejection_comment_raw or ""}
        check = engine.can_transition(res.status, new_status, user_role, ctx)
        if not check.allowed:
            return None, check.reason, 403
    except Exception:
        pass  # Fallback: workflow engine unavailable → allow (backward compat)

    _apply_status_fields(res, new_status, rejection_category, safe_comment)
    db.session.flush()

    action_text = new_status.upper()
    reason_text = safe_comment or (
        _l("Зөвшөөрөгдсөн") if new_status == "approved" else _l("Хянагдаж буй")
    )

    sample = db.session.get(Sample, res.sample_id) if res.sample_id else None
    log_analysis_action(
        result_id=res.id,
        sample_id=res.sample_id,
        analysis_code=res.analysis_code,
        action=action_text,
        raw_data_dict=res.raw_data,
        final_result=res.final_result,
        rejection_category=rejection_category,
        error_reason=rejection_category,
        reason=reason_text,
        sample_code_snapshot=sample.sample_code if sample else None,
        previous_value=res.final_result,
        old_status=old_status,
        new_status=new_status,
    )

    return {
        "res_id": res.id,
        "sample_id": res.sample_id,
        "analysis_code": res.analysis_code,
        "final_result": res.final_result,
        "old_status": old_status,
        "engine": engine,
        "res": res,
    }, None, 200


def update_result_status(result_id, new_status, rejection_comment=None,
                         rejection_category=None):
    """
    Approve, reject, or return-to-pending a single analysis result.

    Args:
        result_id: int
        new_status: 'approved' | 'rejected' | 'pending_review'
        rejection_comment: Optional raw comment string (will be XSS-escaped)
        rejection_category: Optional category string

    Returns:
        tuple: (result_dict, error_msg, http_status_code)
            On success: ({"message": "OK", "status": ...}, None, 200)
            On error:   (None, error_message, http_status)
    """
    if new_status not in {"approved", "rejected", "pending_review"}:
        return None, _l("Төлөв буруу байна"), 400

    safe_comment = str(escape(rejection_comment)) if rejection_comment else None

    try:
        payload, err, code = _update_result_status_atomic(
            result_id, new_status, rejection_category,
            safe_comment, rejection_comment,
        )
    except StaleDataError:
        return None, _l("Өөр хэрэглэгч энэ үр дүнг өөрчилсөн байна. Refresh хийнэ үү."), 409
    except SQLAlchemyError as exc:
        logger.error("update_result_status DB error: %s", exc)
        return None, _l("Мэдээллийн сан хадгалах алдаа"), 500

    if err is not None:
        return None, err, code

    # Invalidate cached stats after status change
    cache.delete('kpi_summary_ahlah')
    cache.delete('ahlah_stats')

    # ISO 17025 compliance audit log
    log_audit(
        action=f'result_{new_status}',
        resource_type='AnalysisResult',
        resource_id=payload["res_id"],
        details={
            'sample_id': payload["sample_id"],
            'analysis_code': payload["analysis_code"],
            'final_result': payload["final_result"],
            'rejection_comment': safe_comment,
        },
        old_value={'status': payload["old_status"]},
        new_value={'status': new_status},
    )

    # Execute workflow hooks
    engine = payload.get("engine")
    if engine is not None:
        try:
            engine.execute_hooks(new_status, {
                'workflow_name': 'analysis_result',
                'entity_type': 'AnalysisResult',
                'entity_id': payload["res_id"],
                'entity': payload["res"],
                'from_state': payload["old_status"],
                'to_state': new_status,
                'comment': safe_comment or '',
                'sample_id': payload["sample_id"],
            })
        except Exception:
            logger.exception("Workflow hook execution failed")

    return {"message": "OK", "status": new_status}, None, 200


@transactional()
def _bulk_update_result_status_atomic(int_ids, new_status, rejection_category, safe_comment):
    """bulk_update_result_status-ийн atomic core (lock + apply + audit).

    Returns:
        tuple: (payload_dict, error_msg, status_code)
            payload: {"success_count", "failed_ids", "results_map", "int_ids"}
    """
    results_map = {
        r.id: r for r in
        AnalysisResult.query.filter(
            AnalysisResult.id.in_(int_ids)
        ).with_for_update().all()
    }

    # Batch-load samples (avoid N+1)
    sample_ids = {r.sample_id for r in results_map.values()}
    samples_map = {
        s.id: s for s in
        Sample.query.filter(Sample.id.in_(sample_ids)).all()
    } if sample_ids else {}

    now_ts = now_local()
    success_count = 0
    failed_ids = []

    for rid in int_ids:
        try:
            res = results_map.get(rid)
            if not res:
                failed_ids.append(rid)
                continue

            # Only modify pending_review or rejected status
            if res.status not in ("pending_review", "rejected"):
                failed_ids.append(rid)
                continue

            _apply_status_fields(res, new_status, rejection_category, safe_comment)
            res.updated_at = now_ts

            sample = samples_map.get(res.sample_id)
            log_analysis_action(
                result_id=res.id,
                sample_id=res.sample_id,
                analysis_code=res.analysis_code,
                action=f"BULK_{new_status.upper()}",
                raw_data_dict=res.raw_data,
                final_result=res.final_result,
                rejection_category=rejection_category if new_status == "rejected" else None,
                error_reason=rejection_category if new_status == "rejected" else None,
                reason=safe_comment or (
                    _l("Бөөнөөр зөвшөөрөгдсөн") if new_status == "approved"
                    else _l("Бөөнөөр буцаагдсан")
                ),
                sample_code_snapshot=sample.sample_code if sample else None,
                timestamp=now_ts,
            )
            success_count += 1

        except (ValueError, AttributeError) as exc:
            # SQLAlchemyError-ыг @transactional-д rollback хийлгэх — энд барихгүй
            logger.warning("bulk_update_status: result_id=%s error: %s", rid, exc)
            failed_ids.append(rid)
            continue

    return {
        "success_count": success_count,
        "failed_ids": failed_ids,
        "results_map": results_map,
        "int_ids": int_ids,
    }, None, 200


def bulk_update_result_status(result_ids, new_status, rejection_comment=None,
                              rejection_category=None, username=None):
    """
    Bulk approve/reject multiple analysis results.

    Args:
        result_ids: list of result ID values
        new_status: 'approved' | 'rejected'
        rejection_comment: Optional raw comment string (will be XSS-escaped)
        rejection_category: Optional category string
        username: Username of the person performing the action (for notifications)

    Returns:
        tuple: (result_dict, error_msg, http_status_code)
    """
    if not result_ids:
        return None, _l("Үр дүн сонгогдоогүй байна"), 400

    if len(result_ids) > 200:
        return None, _l("Нэг удаад 200-аас их үр дүн шинэчлэх боломжгүй"), 400

    if new_status not in {"approved", "rejected"}:
        return None, _l("Төлөв буруу байна"), 400

    if new_status == "rejected" and not rejection_category:
        return None, _l("Буцаах шалтгаанаа сонгоно уу"), 400

    # XSS protection
    safe_comment = str(escape(rejection_comment)) if rejection_comment else None

    try:
        int_ids = [int(rid) for rid in result_ids]
    except (ValueError, TypeError):
        return None, _l("ID буруу байна"), 400

    try:
        payload, err, code = _bulk_update_result_status_atomic(
            int_ids, new_status, rejection_category, safe_comment,
        )
    except StaleDataError:
        return None, _l("Зарим үр дүнг өөр хэрэглэгч өөрчилсөн байна. Refresh хийнэ үү."), 409
    except SQLAlchemyError as exc:
        logger.error("bulk_update_result_status DB error: %s", exc)
        return None, _l("Мэдээллийн сангийн алдаа"), 500

    if err is not None:
        return None, err, code

    success_count = payload["success_count"]
    failed_ids = payload["failed_ids"]
    results_map = payload["results_map"]

    if success_count > 0:
        log_audit(
            action=f'bulk_result_{new_status}',
            resource_type='AnalysisResult',
            resource_id=None,
            details={
                'count': success_count,
                'status': new_status,
                'rejection_category': rejection_category,
            },
        )

        # Execute workflow hooks for each updated result
        try:
            from app.services.workflow_engine import WorkflowEngine
            engine = WorkflowEngine("analysis_result")
            for rid in int_ids:
                res = results_map.get(rid)
                if res and rid not in failed_ids:
                    engine.execute_hooks(new_status, {
                        'workflow_name': 'analysis_result',
                        'entity_type': 'AnalysisResult',
                        'entity_id': res.id,
                        'entity': res,
                        'from_state': '',
                        'to_state': new_status,
                        'comment': safe_comment or '',
                        'sample_id': res.sample_id,
                    })
        except Exception:
            logger.exception("Bulk workflow hook execution failed")

        # Email notification (don't block)
        try:
            notify_sample_status_change(
                sample_code=f"Бөөнөөр ({success_count} үр дүн)",
                new_status=new_status,
                changed_by=username or "unknown",
                reason=safe_comment if new_status == "rejected" else None,
            )
        except (OSError, RuntimeError) as exc:
            logger.warning("Email notification failed: %s", exc)

    return {
        "message": f"{success_count} үр дүн амжилттай {new_status} төлөвт шилжлээ.",
        "success_count": success_count,
        "failed_count": len(failed_ids),
        "failed_ids": failed_ids,
    }, None, 200


@transactional()
def _select_repeat_result_atomic(result_id, use_original):
    """select_repeat_result-ийн atomic core (final_result + raw_data + audit log).

    Returns:
        tuple: (payload_dict_or_None, error_msg, status_code)
            payload: {"res_id", "old_final", "new_final", "sample_id", "analysis_code"}
    """
    res = AnalysisResult.query.filter_by(id=result_id).with_for_update().first()
    if not res:
        return None, _l("Үр дүн олдсонгүй"), 404

    raw = res.get_raw_data()
    repeat_info = raw.get("_repeat")
    if not repeat_info:
        return None, _l("Давтан шинжилгээний мэдээлэл олдсонгүй"), 400

    original_val = repeat_info.get("original_final_result")
    repeat_val = repeat_info.get("repeat_final_result")

    if original_val is None or repeat_val is None:
        return None, _l("Анхны/давтан утга олдсонгүй"), 400

    old_final = res.final_result
    res.final_result = original_val if use_original else repeat_val

    repeat_info["use_original"] = use_original
    raw["_repeat"] = repeat_info
    res.set_raw_data(raw)
    res.updated_at = now_local()

    db.session.flush()

    sample = db.session.get(Sample, res.sample_id)
    choice = "ORIGINAL" if use_original else "REPEAT"
    log_analysis_action(
        result_id=res.id,
        sample_id=res.sample_id,
        analysis_code=res.analysis_code,
        action=f"SELECT_{choice}",
        raw_data_dict=res.raw_data,
        final_result=res.final_result,
        reason=f"Ахлах {choice.lower()} үр дүнг сонгосон: {old_final} -> {res.final_result}",
        sample_code_snapshot=sample.sample_code if sample else None,
    )

    return {
        "res_id": res.id,
        "sample_id": res.sample_id,
        "analysis_code": res.analysis_code,
        "old_final": old_final,
        "new_final": res.final_result,
    }, None, 200


def select_repeat_result(result_id, use_original=False):
    """
    Select which result to use for a repeated analysis.

    Args:
        result_id: int
        use_original: bool - True to use original value, False for repeat value

    Returns:
        tuple: (result_dict, error_msg, http_status_code)
    """
    try:
        payload, err, code = _select_repeat_result_atomic(result_id, use_original)
    except StaleDataError:
        return None, _l("Өөр хэрэглэгч энэ үр дүнг өөрчилсөн байна. Refresh хийнэ үү."), 409
    except SQLAlchemyError as exc:
        logger.error("select_repeat_result DB error: %s", exc)
        return None, _l("Мэдээллийн сан хадгалах алдаа"), 500

    if err is not None:
        return None, err, code

    choice = "ORIGINAL" if use_original else "REPEAT"
    log_audit(
        action=f"select_{choice.lower()}_result",
        resource_type="AnalysisResult",
        resource_id=payload["res_id"],
        details={
            "sample_id": payload["sample_id"],
            "analysis_code": payload["analysis_code"],
            "old_final": payload["old_final"],
            "new_final": payload["new_final"],
            "use_original": use_original,
        },
    )

    return {
        "message": f"{_l('Анхны') if use_original else _l('Давтан')} үр дүн сонгогдлоо",
        "final_result": payload["new_final"],
        "use_original": use_original,
    }, None, 200


# =========================================================================
# API STATUS UPDATE (from analysis_save.py)
# =========================================================================

@transactional()
def _update_result_status_api_atomic(result_id, new_status, action_type,
                                     rejection_category, rejection_subcategory,
                                     safe_comment, error_reason):
    """update_result_status_api-ийн atomic core."""
    res = db.session.get(AnalysisResult, result_id)
    if not res:
        return None, _l("Үр дүн олдсонгүй"), 404

    res.status = new_status
    res.updated_at = now_local()

    if hasattr(res, "rejection_comment"):
        if new_status == "rejected":
            res.rejection_comment = safe_comment if safe_comment else _l("Ахлахаас буцаагдсан")
        elif new_status == "approved":
            res.rejection_comment = None

    if hasattr(res, "error_reason") and error_reason:
        res.error_reason = error_reason

    db.session.flush()

    if new_status == "approved":
        action_text = "APPROVED"
        default_reason = _l("Ахлахаас зөвшөөрөгдсөн")
    elif new_status == "rejected":
        action_text = "REJECTED"
        default_reason = _l("Ахлахаас буцаагдсан")
    else:
        action_text = "PENDING_REVIEW"
        default_reason = _l("Ахлахын хяналтад буцаагдсан")

    reason_text = safe_comment or default_reason
    if action_type:
        reason_text = f"{reason_text}. action={action_type}"

    sample = db.session.get(Sample, res.sample_id)
    sample_code_snap = sample.sample_code if sample else None

    log_analysis_action(
        result_id=res.id,
        sample_id=res.sample_id,
        analysis_code=res.analysis_code,
        action=action_text,
        raw_data_dict=res.raw_data,
        final_result=res.final_result,
        rejection_category=rejection_category,
        rejection_subcategory=rejection_subcategory,
        reason=reason_text,
        error_reason=error_reason,
        sample_code_snapshot=sample_code_snap,
    )

    return {
        "res_id": res.id,
        "sample_id": res.sample_id,
        "res": res,
    }, None, 200


def update_result_status_api(result_id, new_status, action_type=None,
                             rejection_category=None, rejection_subcategory=None,
                             rejection_comment=None, error_reason=None):
    """
    Senior approve/reject from API endpoint (analysis_save.py variant).

    Args:
        result_id: int
        new_status: 'approved' | 'rejected' | 'pending_review'
        action_type: Optional action type string
        rejection_category: Optional category
        rejection_subcategory: Optional subcategory
        rejection_comment: Optional raw comment (will be XSS-escaped)
        error_reason: Optional error reason

    Returns:
        tuple: (result_dict, error_msg, http_status_code)
    """
    allowed = {"approved", "rejected", "pending_review"}
    if new_status not in allowed:
        return None, _l("Буруу статус"), 400

    safe_comment = str(escape(rejection_comment)) if rejection_comment else None

    try:
        payload, err, code = _update_result_status_api_atomic(
            result_id, new_status, action_type,
            rejection_category, rejection_subcategory,
            safe_comment, error_reason,
        )
    except StaleDataError:
        return None, _l("Өөр хэрэглэгч энэ үр дүнг засварласан байна. Дахин оролдоно уу."), 409
    except SQLAlchemyError as exc:
        logger.error("update_result_status_api DB error: %s", exc, exc_info=True)
        return None, _l("Мэдээллийн сан хадгалах алдаа"), 500

    if err is not None:
        return None, err, code

    # Execute workflow hooks (check_sample_complete, mark_sla_completed, etc.)
    try:
        from app.services.workflow_engine import WorkflowEngine
        engine = WorkflowEngine("analysis_result")
        engine.execute_hooks(new_status, {
            'workflow_name': 'analysis_result',
            'entity_type': 'AnalysisResult',
            'entity_id': payload["res_id"],
            'entity': payload["res"],
            'from_state': '',
            'to_state': new_status,
            'comment': safe_comment or '',
            'sample_id': payload["sample_id"],
        })
    except Exception:
        logger.exception("Workflow hook execution failed (API path)")

    return {"message": _l("Амжилттай"), "status": new_status}, None, 200


# =========================================================================
# ANALYSIS SAVE LOGIC
# =========================================================================

def _process_control_gbw(sample, analysis_code, final_result, raw_norm,
                         batch_data=None):
    """
    Process control/GBW sample QC checks with dry-basis conversion.

    Args:
        sample: Sample ORM object
        analysis_code: Normalized analysis code
        final_result: The calculated final result
        raw_norm: Normalized raw data dict
        batch_data: Full batch list (to look up current Mad value)

    Returns:
        tuple: (control_targets, val_to_check, is_gbw)
    """
    control_targets = None
    val_to_check = final_result
    is_gbw = False

    stype = (sample.sample_type or "").lower()
    scode = (sample.sample_code or "").upper()

    is_cm = (stype == "control") or ("CM-" in scode) or ("CM_" in scode)
    is_gbw = (stype == "gbw") or ("GBW" in scode)

    if not (is_cm or is_gbw) or final_result is None:
        return control_targets, val_to_check, is_gbw

    active_std = None
    if is_cm:
        active_std = ControlStandardRepository.get_active()
    elif is_gbw:
        active_std = GbwStandardRepository.get_active()

    if not active_std:
        return control_targets, val_to_check, is_gbw

    targets_map = active_std.targets
    if isinstance(targets_map, str):
        try:
            targets_map = json.loads(targets_map)
        except (json.JSONDecodeError, ValueError):
            targets_map = {}

    code_map = DB_TO_STANDARD_CODE_GBW if is_gbw else DB_TO_STANDARD_CODE_CM
    standard_code = code_map.get(analysis_code, analysis_code)
    if isinstance(targets_map, dict):
        if analysis_code in targets_map:
            control_targets = targets_map[analysis_code]
        elif standard_code in targets_map:
            control_targets = targets_map[standard_code]

    if not control_targets:
        return control_targets, val_to_check, is_gbw

    # --- MAD lookup logic ---
    current_mad = None

    # A. Look in current batch data
    if batch_data:
        for d in batch_data:
            ac = (d.get("analysis_code") or "").lower()
            if ac == "mad":
                try:
                    current_mad = float(d.get("final_result"))
                except (ValueError, TypeError):
                    pass
                break

    # B. Look in database
    if current_mad is None:
        calc = sample.get_calculations()
        if calc and calc.mad is not None:
            current_mad = calc.mad

    needs_dry_conversion = analysis_code in [
        "Aad", "Vad", "CV", "TS", "St,ad", "S", "Qgr,ad",
    ]

    if needs_dry_conversion:
        if current_mad is not None and 0 < current_mad < 100:
            factor = 100.0 / (100.0 - current_mad)
            val_dry = final_result * factor

            if is_gbw and analysis_code in ["CV", "Qgr,ad"]:
                if val_dry > 100:
                    val_to_check = (val_dry * 4.1868) / 1000.0
                else:
                    val_to_check = val_dry
            else:
                val_to_check = val_dry
        else:
            control_targets = None
            raw_norm["_mad_required"] = True
            logger.info(
                "CM/GBW check skipped for %s: Mad not available yet",
                analysis_code,
            )

    return control_targets, val_to_check, is_gbw


def save_single_result(item, user_id, batch_data=None, coalesce_diff_fn=None,
                       effective_limit_fn=None):
    """
    Process and save a single analysis result item.

    Args:
        item: dict with keys: sample_id, analysis_code, final_result, raw_data,
              equipment_id, rejection_comment
        user_id: int - current user's ID
        batch_data: list[dict] - full batch (for Mad cross-lookup)
        coalesce_diff_fn: callable - function to extract diff from raw_data
        effective_limit_fn: callable - function to compute tolerance limit

    Returns:
        tuple: (result_info_dict, error_msg)
            On success: ({"sample_id": ..., "analysis_code": ..., ...}, None)
            On error:   (None, "error message string")
    """
    # --- 1. Validation ---
    sample_id_raw = item.get("sample_id")
    sample_id, s_err = validate_sample_id(sample_id_raw)
    if s_err:
        raise ValueError(f"Дээжийн ID алдаа: {s_err}")

    analysis_code_in = item.get("analysis_code")
    _, c_err = validate_analysis_code(analysis_code_in)
    if c_err:
        raise ValueError(f"Кодын алдаа: {c_err}")

    analysis_code = norm_code(analysis_code_in)

    final_result_raw = item.get("final_result")
    final_result, r_err = validate_analysis_result(
        final_result_raw, analysis_code, allow_none=True,
    )
    if r_err:
        return None, f"({analysis_code}): {r_err}"

    equipment_id_raw = item.get("equipment_id")
    equipment_id, _ = validate_equipment_id(equipment_id_raw, allow_none=True)

    if equipment_id is not None:
        equipment = EquipmentRepository.get_by_id(equipment_id)
        if not equipment:
            logger.warning("Equipment ID %s not found, ignoring", equipment_id)
            equipment_id = None

    # Lock parent sample row
    sample = db.session.query(Sample).filter_by(id=sample_id).with_for_update().first()
    if not sample:
        raise ValueError(f"Дээж {sample_id} олдсонгүй")

    # Lab type validation
    if sample.lab_type and sample.lab_type not in ('coal', 'petrography'):
        raise ValueError(
            f"Энэ дээж {sample.lab_type} лабынх — нүүрсний API-аар хадгалах боломжгүй"
        )

    # Archived/completed sample
    if sample.status in ('archived', 'completed'):
        raise ValueError(
            f"Энэ дээж '{sample.status}' төлөвтэй — шинэ шинжилгээ хадгалах боломжгүй"
        )

    # --- 2. Normalization & Calculation ---
    raw_in = item.get("raw_data") or {}
    if not isinstance(raw_in, dict):
        raise ValueError(_l("raw_data нь dict байх ёстой"))

    _mg_flat = (
        analysis_code in ('MG', 'MG_SIZE') or
        (analysis_code == 'MT' and isinstance(raw_in, dict) and 'p1' not in raw_in)
    )

    if analysis_code == "CSN" and isinstance(raw_in, dict):
        raw_norm = dict(raw_in)
        raw_norm.update(normalize_raw_data(raw_in, analysis_code))
    elif _mg_flat:
        raw_norm = dict(raw_in)
    else:
        raw_norm = normalize_raw_data(raw_in, analysis_code)

    # UI flags preserve
    for key in ("is_low_avg", "retest_mode", "limit_used", "limit_mode",
                "t_exceeded", "t_band"):
        if isinstance(raw_in, dict) and key in raw_in:
            raw_norm[key] = raw_in[key]

    # Tolerance logic
    avg = to_float(raw_norm.get("avg"))
    diff = coalesce_diff_fn(raw_norm) if coalesce_diff_fn else None
    limit, mode, band = effective_limit_fn(analysis_code, avg) if effective_limit_fn else (0.30, "abs", None)
    effective_limit = (avg * limit) if (mode == "percent" and avg is not None) else limit

    if analysis_code == "CSN" and diff is None:
        diff = 0.0
    FLOAT_TOLERANCE = 1e-6
    t_exceeded = (diff is not None) and (
        (abs(diff) - (effective_limit or 0)) > FLOAT_TOLERANCE
    )

    raw_norm.update({
        "t_band": band,
        "limit_used": effective_limit,
        "limit_mode": mode,
        "t_exceeded": bool(t_exceeded),
    })

    # Server-side calculation verification
    if final_result is not None and raw_norm:
        server_result, calc_warnings = verify_and_recalculate(
            analysis_code=analysis_code,
            client_final_result=final_result,
            raw_data=raw_norm,
            user_id=user_id,
            sample_id=sample_id,
        )
        if server_result is not None:
            final_result = server_result
        if calc_warnings:
            for warn in calc_warnings:
                logger.warning(warn)

    # --- 3. Control / GBW logic ---
    try:
        control_targets, val_to_check, is_gbw = _process_control_gbw(
            sample, analysis_code, final_result, raw_norm, batch_data,
        )
    except (ValueError, TypeError, KeyError, AttributeError) as exc:
        logger.error("Control/GBW Logic Error: %s", exc)
        control_targets = None
        val_to_check = final_result
        is_gbw = False

    # --- 4. Status determination ---
    new_status, status_reason = determine_result_status(
        analysis_code, val_to_check, raw_norm, control_targets=control_targets,
    )

    if new_status == "rejected" and is_gbw and status_reason:
        status_reason = status_reason.replace("Control Failure", "GBW Failure")

    if raw_norm.get("_mad_required") and new_status == "approved":
        new_status = "pending_review"
        status_reason = _l("Mad шаардлагатай (CM/GBW хуурай суурийн шалгалт)")

    # --- 5. DB Operations ---
    existing = (
        AnalysisResult.query.filter_by(
            sample_id=sample_id, analysis_code=analysis_code,
        )
        .order_by(AnalysisResult.id.desc())
        .with_for_update()
        .first()
    )

    action = ""
    user_comment = item.get("rejection_comment")
    safe_comment = str(escape(user_comment)) if user_comment else None
    reason = status_reason if status_reason else (safe_comment or _l("Химичээр хадгалагдсан"))

    auto_error_reason = None
    if new_status == "rejected":
        if status_reason and ("Failure" in status_reason):
            auto_error_reason = "qc_fail"

    # Өмнөх утга хадгалах (before/after audit)
    prev_final_result = existing.final_result if existing else None
    prev_status = existing.status if existing else None

    if not existing:
        new_res = AnalysisResult(
            sample_id=sample_id,
            user_id=user_id,
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
        # Repeat analysis logic
        if new_status == "approved":
            prev_approved = (
                AnalysisResultLog.query
                .filter_by(sample_id=sample_id, analysis_code=analysis_code)
                .filter(
                    AnalysisResultLog.action.in_([
                        "CREATED_AUTO_APPROVED",
                        "UPDATED_AUTO_APPROVED",
                        "APPROVED",
                        "BULK_APPROVED",
                    ])
                )
                .first()
            )
            if prev_approved:
                raw_norm["_repeat"] = {
                    "original_final_result": prev_approved.final_result_snapshot,
                    "repeat_final_result": final_result,
                    "original_raw": existing.get_raw_data(),
                    "repeated_at": now_local().isoformat(),
                    "use_original": False,
                }

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

    # SOLID: Auto-update sample weight
    if analysis_code.upper() == "SOLID":
        try:
            A = raw_norm.get("A")
            B = raw_norm.get("B")
            if A is not None and B is not None:
                A_val = float(A)
                B_val = float(B)
                sample_weight = round(A_val - B_val, 2)
                if sample_weight > 0:
                    sample.weight = sample_weight
                    logger.info(
                        "Sample %s weight updated to %s kg from Solid analysis",
                        sample_id, sample_weight,
                    )
        except (ValueError, TypeError) as exc:
            logger.warning("Could not calculate sample weight from Solid: %s", exc)

    # First-saved info for audit
    first_log = (
        AnalysisResultLog.query
        .filter_by(sample_id=sample_id, analysis_code=analysis_code)
        .order_by(AnalysisResultLog.id.asc())
        .first()
    )

    if first_log:
        original_user_id = first_log.original_user_id or first_log.user_id
        original_timestamp = first_log.original_timestamp or first_log.timestamp
    else:
        original_user_id = user_id
        original_timestamp = now_local()

    # Audit Log
    log_analysis_action(
        result_id=target_res_id,
        sample_id=sample_id,
        analysis_code=analysis_code,
        action=action,
        raw_data_dict=raw_snapshot,
        final_result=final_snapshot,
        reason=reason,
        error_reason=auto_error_reason,
        original_user_id=original_user_id,
        original_timestamp=original_timestamp,
        sample_code_snapshot=sample.sample_code,
        previous_value=prev_final_result,
        old_status=prev_status,
        new_status=new_status,
    )

    return {
        "sample_id": sample_id,
        "analysis_code": analysis_code,
        "status": new_status,
        "final_result": final_result,
        "raw_data": raw_norm,
        "success": True,
        "reason": reason,
    }, None
