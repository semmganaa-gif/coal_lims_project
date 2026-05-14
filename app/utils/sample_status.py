# app/utils/sample_status.py
# -*- coding: utf-8 -*-
"""Sample status нэгтгэлийн helper.

Дээж + дотроос нь шинжилгээний үр дүнгийн статусуудаас тодорхой workflow
status нэг утгыг буцаана.
"""

from __future__ import annotations


def aggregate_sample_status(
    sample_status: str,
    result_statuses: set[str] | None,
) -> str:
    """
    Дээжийн нэгтгэсэн төлвийг тооцоолох.

    Дүрэм:
    - sample.status == 'archived' бол үр дүнгээс үл хамааран 'archived'.
    - Үгүй бол шинжилгээний статусуудаас: pending_review > rejected > approved.
    - Шинжилгээ байхгүй бол sample_status хэвээр.

    Args:
        sample_status: Sample.status утга.
        result_statuses: Тухайн дээжний AnalysisResult.status-уудын set.

    Returns:
        str: Нэгтгэсэн workflow status.
    """
    if sample_status == "archived":
        return "archived"

    sts = result_statuses or set()

    if "pending_review" in sts:
        return "pending_review"
    if "rejected" in sts:
        return "rejected"
    if "approved" in sts:
        return "approved"

    return sample_status or ""
