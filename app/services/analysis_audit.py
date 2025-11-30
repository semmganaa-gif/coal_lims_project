# app/services/analysis_audit.py
# -*- coding: utf-8 -*-
"""
Analysis Result Audit Service

Шинжилгээний үр дүнгийн аудит логыг бичих үйлчилгээ.
Өмнө нь app/routes/audit_log_service.py-д байсан.
"""

from __future__ import annotations

import json
import logging
from dataclasses import asdict, is_dataclass
from typing import Any, Mapping, Optional

from flask_login import current_user

from app import db
from app.models import AnalysisResultLog

logger = logging.getLogger(__name__)


def _to_jsonable(data: Any) -> Any:
    """
    dataclass → dict, SQLAlchemy model → id гэх мэтээр JSON болох хэлбэрт оймсолж өгнө.

    Args:
        data: Хөрвүүлэх өгөгдөл

    Returns:
        JSON-д хөрвүүлж болох утга
    """
    try:
        if is_dataclass(data):
            return asdict(data)
        # SQLAlchemy объект байж магадгүй: id талбар байвал авч болно
        if hasattr(data, "id"):
            return getattr(data, "id")
    except Exception:
        pass
    return data


def _safe_json_dumps(payload: Any, *, limit_bytes: int = 200_000) -> str:
    """
    Монгол тэмдэгтийг алдагдуулахгүйгээр JSON болгож (ensure_ascii=False),
    асар том payload ирвэл хэмжээг хязгаарлаж (байт-аар) тайлбар хавсаргана.

    Args:
        payload: JSON-д хөрвүүлэх өгөгдөл
        limit_bytes: Хамгийн их байт (default: 200KB)

    Returns:
        JSON string (шаардлагатай бол truncate хийгдсэн)
    """
    try:
        s = json.dumps(payload, ensure_ascii=False, default=_to_jsonable)
    except TypeError:
        s = json.dumps(str(payload), ensure_ascii=False)

    # тэмдэгт урт нь UTF-8-д яг байт биш, гэхдээ ойролцоо хяналт хангалттай
    if len(s.encode("utf-8")) > limit_bytes:
        head = s.encode("utf-8")[: limit_bytes].decode("utf-8", errors="ignore")
        s = f'{head}… [truncated]'
    return s


def log_analysis_action(
    result_id: int,
    sample_id: int,
    analysis_code: str,
    action: str,
    final_result: Optional[Any],
    raw_data_dict: Optional[Mapping[str, Any]],
    reason: Optional[str] = None,
    error_reason: Optional[str] = None,
) -> None:
    """
    Шинжилгээний үр дүн дээр хийсэн өөрчлөлтийг аудитын хүснэгтэд БЭЛДЭЖ нэмнэ.

    ⚠️ Commit-ийг ДУУДАГЧ тал хийнэ (энд commit хийхгүй).

    Args:
        result_id: AnalysisResult.id
        sample_id: Sample.id
        analysis_code: жишээ нь 'Aad', 'Mad', 'TS', ...
        action: 'created' | 'updated' | 'approved' | 'rejected' | 'edited_raw' гэх мэт
        final_result: тухайн мөчийн эцсийн тооцоолол (float/str/None)
        raw_data_dict: тооцоонд хэрэглэсэн түүхий өгөгдлийн snapshot (dict)
        reason: буцаалт, засварын шалтгаан (заавал биш)
        error_reason: Алдааны шалтгааны код (заавал биш)

    Returns:
        None

    Raises:
        Алдаа гарсан ч exception throw хийхгүй, зөвхөн log-д бичнэ.

    Examples:
        >>> log_analysis_action(
        ...     result_id=123,
        ...     sample_id=456,
        ...     analysis_code='Mad',
        ...     action='approved',
        ...     final_result=8.5,
        ...     raw_data_dict={'m1': 10.2, 'm2': 10.3},
        ...     reason='Normal approval'
        ... )
    """
    try:
        # Хэн:
        user_id = current_user.id if getattr(current_user, "is_authenticated", False) else -1

        # Түүхий өгөгдөл + эцсийн үр дүнг snapshot болгох
        raw_data_snapshot = _safe_json_dumps(raw_data_dict or {})
        final_result_snapshot = _safe_json_dumps(final_result)

        new_log = AnalysisResultLog(
            user_id=user_id,
            sample_id=sample_id,
            analysis_result_id=result_id,
            analysis_code=analysis_code,
            action=action,
            final_result_snapshot=final_result_snapshot,
            raw_data_snapshot=raw_data_snapshot,
            reason=reason,
            error_reason=error_reason,
        )

        db.session.add(new_log)

        # Энд commit ХИЙХГҮЙ — гаднах route/service commit хийнэ
        logger.debug(
            f"[AUDIT] action={action} analysis={analysis_code} "
            f"sample_id={sample_id} result_id={result_id} user_id={user_id} "
            f"reason={reason or '-'}"
        )

    except Exception as e:
        # Логын алдаанаас болж үндсэн транзакц нурж болохгүй тул rollback зөвхөн энэ add-д
        try:
            db.session.rollback()
        except Exception:
            pass
        logger.error(f"CRITICAL ERROR in log_analysis_action: {e}")
