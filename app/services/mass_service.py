# app/services/mass_service.py
# -*- coding: utf-8 -*-
"""
Массын ажлын талбарын бизнес логик.

Route layer-аас тусгаарлагдсан — DB query, validation, audit logging.
"""

import logging
from dataclasses import dataclass, field

from flask_login import current_user
from sqlalchemy import or_, and_, select
from flask_babel import lazy_gettext as _l
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm.exc import StaleDataError

from app import db
from app.constants import SampleStatus
from app.models import Sample, AnalysisResult, AnalysisResultLog
from app.repositories import SampleRepository, AnalysisResultRepository
from app.utils.datetime import now_local
from app.utils.security import escape_like_pattern
from app.utils.transaction import transactional

logger = logging.getLogger(__name__)


@dataclass
class ServiceResult:
    success: bool
    message: str
    data: dict = field(default_factory=dict)
    status_code: int = 200


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _upsert_mass_result(sample_id: int, weight_g: float, user_id: int | None = None):
    """AnalysisResult(code='m') үүсгэх/шинэчлэх — sample summary-д харагдана."""
    ar = AnalysisResultRepository.get_by_sample_and_code(sample_id, "m")
    if ar is None:
        ar = AnalysisResult(
            sample_id=sample_id,
            analysis_code="m",
            final_result=weight_g,
            status="approved",
            user_id=user_id,
        )
        db.session.add(ar)
    else:
        ar.final_result = weight_g
        ar.status = "approved"


def _has_m_task_sql():
    """analyses_to_perform JSON string дотор "m" байгаа эсэх."""
    from sqlalchemy import func
    return func.lower(Sample.analyses_to_perform).like('%"m"%')


def _db_error_to_result(exc: Exception) -> ServiceResult:
    """SQLAlchemy exception-ыг тогтсон ServiceResult болгож хөрвүүлэх.

    @transactional decorator-аас raise хийсэн алдааг public function-д
    барих үед ашиглана. Тус бүрт онцлох HTTP status code:
      409 — StaleDataError (concurrent edit), IntegrityError (constraint)
      500 — бусад DB алдаа
    """
    if isinstance(exc, StaleDataError):
        return ServiceResult(
            False,
            _l("Өгөгдөл өөрчлөгдсөн байна. Refresh хийнэ үү."),
            status_code=409,
        )
    if isinstance(exc, IntegrityError):
        logger.error("Integrity error: %s", exc)
        return ServiceResult(False, _l("Өгөгдлийн зөрчил гарлаа"), status_code=409)
    logger.error("Database error: %s", exc)
    return ServiceResult(False, _l("Өгөгдлийн санд алдаа гарлаа"), status_code=500)


# ---------------------------------------------------------------------------
# Public service functions
# ---------------------------------------------------------------------------

@transactional()
def _update_sample_status_atomic(sample_ids: list[int], new_status: str) -> ServiceResult:
    """update_sample_status-ийн atomic core."""
    count = SampleRepository.update_status(sample_ids, new_status, commit=False)
    return ServiceResult(True, f"{count} sample status updated.", data={"count": count})


def update_sample_status(sample_ids: list[int], action: str) -> ServiceResult:
    """
    Дээжүүдийн статусыг archive/unarchive хийх.

    Args:
        sample_ids: Дээжний ID-ууд
        action: "archive" | "unarchive"
    """
    if not sample_ids:
        return ServiceResult(False, _l("Дээж сонгогдоогүй байна"), status_code=400)

    # Sample workflow: completed → archived (Архивлах), archived → completed (Сэргээх).
    # Unarchive нь workflow-ийн зөвшөөрөгдсөн "completed" төлөв рүү буцаана
    # (өмнө 'new' гэж буруу тохируулсан тул workflow check failed).
    new_status = "archived" if action == "archive" else "completed"

    # Validate via workflow engine
    try:
        from app.services.workflow_engine import WorkflowEngine
        engine = WorkflowEngine("sample")
        user_role = getattr(current_user, 'role', 'admin')
        # Check first sample to validate transition
        first_sample = db.session.get(Sample, sample_ids[0])
        if first_sample:
            check = engine.can_transition(first_sample.status, new_status, user_role)
            if not check.allowed:
                return ServiceResult(False, check.reason, status_code=403)
    except Exception:
        pass  # Fallback: allow if workflow unavailable

    try:
        return _update_sample_status_atomic(sample_ids, new_status)
    except SQLAlchemyError as exc:
        return _db_error_to_result(exc)


def get_eligible_samples(include_ready: bool = False, q_text: str = "") -> list[dict]:
    """
    Массын ажлын талбарт харагдах дээжүүд.

    Returns:
        Дээжүүдийн dict жагсаалт (JSON-д бэлэн)
    """
    base_filters = [
        Sample.status == SampleStatus.NEW.value,
        _has_m_task_sql(),
    ]

    if not include_ready:
        base_filters.append(
            or_(Sample.mass_ready.is_(False), Sample.mass_ready.is_(None))
        )

    stmt = select(Sample).where(and_(*base_filters))

    if q_text:
        safe_text = escape_like_pattern(q_text)
        stmt = stmt.where(Sample.sample_code.ilike(f"%{safe_text}%"))

    stmt = stmt.order_by(Sample.received_date.desc()).limit(400)
    rows = list(db.session.execute(stmt).scalars().all())

    return [
        {
            "id": s.id,
            "sample_code": s.sample_code or "",
            "client_name": s.client_name or "",
            "sample_type": s.sample_type or "",
            "weight": s.weight,
            "received_date": (
                s.received_date.strftime("%Y-%m-%d %H:%M") if s.received_date else ""
            ),
            "mass_ready": bool(getattr(s, "mass_ready", False)),
        }
        for s in rows
    ]


@transactional()
def _save_mass_measurements_atomic(
    sample_ids: list[int],
    weight_map: dict,
    mark_ready: bool,
    user_id: int | None,
) -> ServiceResult:
    """save_mass_measurements-ийн atomic core (Sample weight + mass_ready + audit)."""
    samples_stmt = (
        select(Sample).where(Sample.id.in_(sample_ids)).with_for_update()
    )
    samples_map = {
        s.id: s for s in db.session.execute(samples_stmt).scalars().all()
    }
    now_ts = now_local()

    updated = []
    for sid in sample_ids:
        s = samples_map.get(sid)
        if not s:
            continue
        if sid in weight_map and isinstance(weight_map[sid], (int, float)):
            weight_g = float(weight_map[sid])
            s.weight = round(weight_g / 1000, 3)
            _upsert_mass_result(sid, weight_g, user_id)
        if mark_ready:
            s.mass_ready = True
            s.mass_ready_at = now_ts
            s.mass_ready_by_id = user_id
        updated.append(sid)

    if not updated:
        return ServiceResult(False, "Rows are not valid.", status_code=400)
    return ServiceResult(
        True,
        f"{len(updated)} дээж шинэчлэгдлээ.",
        data={"updated_ids": updated},
    )


def save_mass_measurements(
    items: list[dict], mark_ready: bool = True, user_id: int | None = None
) -> ServiceResult:
    """Масс хэмжилтийн үр дүнг хадгалах (атомик transaction).

    Args:
        items: [{"sample_id": 123, "weight": 2500.0}, ...]
        mark_ready: mass_ready тэмдэглэх эсэх
        user_id: Хэрэглэгчийн ID
    """
    if not items:
        return ServiceResult(False, "No rows to save.", status_code=400)
    sample_ids = [it.get("sample_id") for it in items if it.get("sample_id")]
    if not sample_ids:
        return ServiceResult(False, "No valid IDs found.", status_code=400)
    weight_map = {it.get("sample_id"): it.get("weight") for it in items if "weight" in it}

    try:
        return _save_mass_measurements_atomic(sample_ids, weight_map, mark_ready, user_id)
    except SQLAlchemyError as exc:
        return _db_error_to_result(exc)


@transactional()
def _update_weight_atomic(sample_id: int, weight_g: float, user_id: int | None) -> ServiceResult:
    """update_weight-ийн atomic core."""
    s = db.session.query(Sample).filter_by(id=sample_id).with_for_update().first()
    if not s:
        return ServiceResult(False, "Sample not found.", status_code=404)
    s.weight = round(weight_g / 1000, 3)
    s.received_date = s.received_date or now_local()
    _upsert_mass_result(sample_id, weight_g, user_id)
    return ServiceResult(True, "Weight updated.", data={"sample_id": s.id})


def update_weight(sample_id: int, weight_g: float, user_id: int | None = None) -> ServiceResult:
    """Нэг дээжийн жинг шинэчлэх."""
    try:
        return _update_weight_atomic(sample_id, weight_g, user_id)
    except SQLAlchemyError as exc:
        return _db_error_to_result(exc)


@transactional()
def _unready_samples_atomic(sample_ids: list[int]) -> ServiceResult:
    """unready_samples-ийн atomic core."""
    stmt = select(Sample).where(Sample.id.in_(sample_ids)).with_for_update()
    rows = list(db.session.execute(stmt).scalars().all())
    for s in rows:
        s.mass_ready = False
        s.mass_ready_at = None
        s.mass_ready_by_id = None
    return ServiceResult(True, f"{len(rows)} дээжийг Unready болголоо.")


def unready_samples(sample_ids: list[int]) -> ServiceResult:
    """mass_ready-г буцааж false болгох."""
    if not sample_ids:
        return ServiceResult(False, "No ID provided.", status_code=400)
    try:
        return _unready_samples_atomic(sample_ids)
    except SQLAlchemyError as exc:
        return _db_error_to_result(exc)


@transactional()
def _delete_sample_atomic(sample_id: int, user_id: int | None) -> ServiceResult:
    """delete_sample-ийн atomic core (audit log + cascade delete нэг transaction).

    ISO 17025: Audit log үүсгэхэд алдаа гарвал бүх transaction rollback болж,
    дээж устгагдахгүй. Audit log байхгүй устгал гарахаас сэргийлнэ.
    """
    s = SampleRepository.get_by_id(sample_id)
    if not s:
        return ServiceResult(False, "Sample not found.", status_code=404)

    sample_code = s.sample_code
    results = AnalysisResultRepository.get_by_sample_id(sample_id)
    for r in results:
        log_entry = AnalysisResultLog(
            user_id=user_id,
            sample_id=sample_id,
            analysis_result_id=r.id,
            analysis_code=r.analysis_code,
            action="DELETED",
            final_result_snapshot=r.final_result,
            raw_data_snapshot=str(r.raw_data) if r.raw_data else None,
            reason=f"Sample {sample_code} deleted by user",
            sample_code_snapshot=sample_code,
            timestamp=now_local(),
        )
        db.session.add(log_entry)

    db.session.delete(s)
    return ServiceResult(True, "Sample deleted.", data={"deleted_id": sample_id})


def delete_sample(sample_id: int, user_id: int | None = None) -> ServiceResult:
    """Дээжийг бүр мөсөн устгах (каскадтай) + audit log бичих.

    ISO 17025: Устгасан дээжний шинжилгээний бүртгэлийг AnalysisResultLog-д хадгална.
    Audit log болон cascade delete нэг atomic transaction — аль нь нэг нь алдаа
    өгвөл бүхэлдээ rollback хийнэ.
    """
    try:
        return _delete_sample_atomic(sample_id, user_id)
    except SQLAlchemyError as exc:
        return _db_error_to_result(exc)
