# app/services/analysis_audit.py
# -*- coding: utf-8 -*-
"""
Analysis Result Audit Service

Шинжилгээний үр дүнгийн аудит логыг бичих үйлчилгээ.
"""

from __future__ import annotations

import json
import logging
from dataclasses import asdict, is_dataclass
from typing import Any, Mapping, Optional

from flask_login import current_user

from app import db
from app.models import AnalysisResultLog
from app.constants import MAX_JSON_PAYLOAD_BYTES

logger = logging.getLogger(__name__)


def _to_jsonable(data: Any) -> Any:
    """
    dataclass → dict, SQLAlchemy model → id гэх мэтээр JSON болох хэлбэрт хөрвүүлнэ.
    """
    try:
        if is_dataclass(data):
            return asdict(data)
        if hasattr(data, "id"):
            return getattr(data, "id")
    except Exception:
        pass
    return data


def _safe_json_dumps(payload: Any, *, limit_bytes: int = MAX_JSON_PAYLOAD_BYTES) -> str:
    """
    Монгол тэмдэгтийг алдагдуулахгүйгээр JSON болгож,
    асар том payload ирвэл хэмжээг хязгаарлана.
    """
    try:
        s = json.dumps(payload, ensure_ascii=False, default=_to_jsonable)
    except TypeError:
        s = json.dumps(str(payload), ensure_ascii=False)

    if len(s.encode("utf-8")) > limit_bytes:
        head = s.encode("utf-8")[:limit_bytes].decode("utf-8", errors="ignore")
        s = f'{head}… [truncated]'
    return s


def _to_float(value: Any) -> Optional[float]:
    """final_result-г float руу хөрвүүлэх (model-д Float column)."""
    if value is None:
        return None
    try:
        return float(value)
    except (ValueError, TypeError):
        return None


def log_analysis_action(
    result_id: Optional[int],
    sample_id: int,
    analysis_code: str,
    action: str,
    final_result: Optional[Any] = None,
    raw_data_dict: Optional[Any] = None,
    reason: Optional[str] = None,
    error_reason: Optional[str] = None,
    rejection_category: Optional[str] = None,
    rejection_subcategory: Optional[str] = None,
    sample_code_snapshot: Optional[str] = None,
    original_user_id: Optional[int] = None,
    original_timestamp: Optional[Any] = None,
    timestamp: Optional[Any] = None,
) -> None:
    """
    Шинжилгээний үр дүн дээр хийсэн өөрчлөлтийг аудитын хүснэгтэд нэмнэ.

    Commit-ийг ДУУДАГЧ тал хийнэ (энд commit хийхгүй).

    Args:
        result_id: AnalysisResult.id (None байж болно - жнь ANALYSIS_REQUESTED)
        sample_id: Sample.id
        analysis_code: жишээ нь 'Aad', 'Mad', 'TS'
        action: 'CREATED' | 'UPDATED' | 'APPROVED' | 'REJECTED' | 'REANALYSIS' гэх мэт
        final_result: тухайн мөчийн эцсийн тооцоолол (float/str/None)
        raw_data_dict: түүхий өгөгдлийн snapshot (dict эсвэл JSON string)
        reason: буцаалт, засварын шалтгаан
        error_reason: Алдааны шалтгааны код
        rejection_category: Буцаалтын ангилал
        rejection_subcategory: Буцаалтын дэд ангилал
        sample_code_snapshot: Дээжний код (sample устсан ч харагдана)
        original_user_id: Анхны хадгалсан химичийн ID
        original_timestamp: Анхны хадгалсан цаг
        timestamp: Тусгай timestamp (None бол автомат)
    """
    try:
        user_id = current_user.id if getattr(current_user, "is_authenticated", False) else -1

        # raw_data нь dict бол JSON руу хөрвүүлнэ, string бол шууд ашиглана
        if isinstance(raw_data_dict, str):
            raw_data_snapshot = raw_data_dict
        else:
            raw_data_snapshot = _safe_json_dumps(raw_data_dict or {})

        kwargs = dict(
            user_id=user_id,
            sample_id=sample_id,
            analysis_result_id=result_id,
            analysis_code=analysis_code,
            action=action,
            final_result_snapshot=_to_float(final_result),
            raw_data_snapshot=raw_data_snapshot,
            reason=reason,
            error_reason=error_reason,
            rejection_category=rejection_category,
            rejection_subcategory=rejection_subcategory,
            sample_code_snapshot=sample_code_snapshot,
            original_user_id=original_user_id,
            original_timestamp=original_timestamp,
        )
        if timestamp is not None:
            kwargs['timestamp'] = timestamp

        new_log = AnalysisResultLog(**kwargs)

        # ISO 17025: Audit log integrity hash
        new_log.data_hash = new_log.compute_hash()

        db.session.add(new_log)

        logger.debug(
            "[AUDIT] action=%s analysis=%s sample_id=%s result_id=%s user_id=%s reason=%s",
            action, analysis_code, sample_id, result_id, user_id, reason or '-',
        )

    except Exception as e:
        # Аудит алдаанаас болж үндсэн transaction нурахгүй байх ёстой.
        # rollback хийхгүй — дуудагч тал шийднэ.
        logger.error("CRITICAL ERROR in log_analysis_action: %s", e)
