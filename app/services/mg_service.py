# app/services/mg_service.py
# -*- coding: utf-8 -*-
"""
MG Summary бизнес логик.

WTL MG дээжүүдийн нэгтгэл, давтан шинжилгээ буцаах үйлдлүүд.
"""
from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from typing import Any

from sqlalchemy.exc import SQLAlchemyError
from flask_babel import lazy_gettext as _l

from app import db
from app.models import AnalysisResult, Sample
from app.services.analysis_audit import log_analysis_action
from app.utils.datetime import now_local

logger = logging.getLogger(__name__)

MG_CODES = ["MT", "TRD", "MG", "MG_SIZE"]
MG_ONLY = ["MG", "MG_SIZE"]


@dataclass
class MgSummaryData:
    """MG summary хуудасны өгөгдөл."""

    samples: list[Sample]
    mg_data: dict[int, dict[str, Any]]


@dataclass
class RepeatResult:
    """Давтан шинжилгээ буцаасан үр дүн."""

    success: bool
    message: str
    count: int = 0


def get_mg_summary() -> MgSummaryData:
    """
    MG/MG_SIZE үр дүнтэй бүх идэвхтэй дээжүүд + тэдгээрийн MT, TRD, MG, MG_SIZE үр дүн.

    Returns:
        MgSummaryData объект
    """
    # MG эсвэл MG_SIZE үр дүнтэй дээжүүдийн ID
    q_ids = (
        db.session.query(AnalysisResult.sample_id)
        .join(Sample, Sample.id == AnalysisResult.sample_id)
        .filter(
            AnalysisResult.analysis_code.in_(MG_ONLY),
            AnalysisResult.status.in_(["approved", "pending_review"]),
            Sample.status != "archived",
        )
        .distinct()
    )
    sample_ids = [r.sample_id for r in q_ids.all()]

    if not sample_ids:
        return MgSummaryData(samples=[], mg_data={})

    # Дээж мэдээлэл
    samples = (
        Sample.query.filter(Sample.id.in_(sample_ids))
        .order_by(Sample.received_date.desc())
        .all()
    )

    # Бүх MG кодын үр дүн
    results = AnalysisResult.query.filter(
        AnalysisResult.sample_id.in_(sample_ids),
        AnalysisResult.analysis_code.in_(MG_CODES),
        AnalysisResult.status.in_(["approved", "pending_review"]),
    ).all()

    mg_data: dict[int, dict[str, Any]] = {}
    for r in results:
        raw = r.raw_data
        if isinstance(raw, str):
            try:
                raw = json.loads(raw)
            except (json.JSONDecodeError, TypeError):
                raw = {}
        elif raw is None:
            raw = {}
        mg_data.setdefault(r.sample_id, {})[r.analysis_code] = {
            "id": r.id,
            "final_result": r.final_result,
            "raw_data": raw,
            "status": r.status,
        }

    return MgSummaryData(samples=samples, mg_data=mg_data)


def repeat_analyses(
    sample_ids: list[int],
    codes: list[str],
    user_role: str,
) -> RepeatResult:
    """
    MG Summary-аас давтан шинжилгээ буцаах.

    Approved/pending_review үр дүнгүүдийг rejected болгож,
    химич дахин шинжилгээ хийх боломж олгоно.

    Args:
        sample_ids: Дээжний ID-ууд
        codes: Шинжилгээний кодууд
        user_role: Хэрэглэгчийн role

    Returns:
        RepeatResult объект
    """
    if user_role not in ("senior", "admin"):
        return RepeatResult(success=False, message=_l("Зөвхөн ахлах/админ"))

    if not codes:
        return RepeatResult(success=False, message=_l("Код сонгоогүй"))

    try:
        count = 0
        for sid in sample_ids:
            sample = db.session.get(Sample, sid)
            if not sample:
                continue
            for code in codes:
                ar = AnalysisResult.query.filter_by(
                    sample_id=sid, analysis_code=code
                ).first()
                if ar and ar.status in ("approved", "pending_review"):
                    ar.status = "rejected"
                    ar.updated_at = now_local()
                    if hasattr(ar, "rejection_comment"):
                        ar.rejection_comment = "Returned from MG Summary"
                    log_analysis_action(
                        result_id=ar.id,
                        sample_id=sid,
                        analysis_code=code,
                        action="REJECTED",
                        reason=f"MG Summary-аас '{code}' давтан шинжилгээ буцаасан",
                        sample_code_snapshot=sample.sample_code,
                        final_result=ar.final_result,
                        raw_data_dict=ar.raw_data,
                    )
                    count += 1
        db.session.commit()
        return RepeatResult(
            success=True,
            message=f"{count} шинжилгээг буцаалаа (давтан хийнэ)",
            count=count,
        )
    except (SQLAlchemyError, ValueError, AttributeError) as e:
        db.session.rollback()
        logger.error(f"MG repeat error: {e}", exc_info=True)
        return RepeatResult(
            success=False, message=_l("Давтан шинжилгээ буцаахад алдаа гарлаа")
        )
