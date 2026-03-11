# app/services/__init__.py
# -*- coding: utf-8 -*-
"""
Business logic and service layer

Services модулиуд нь route-уудаас салгасан бизнес логикийг агуулна.

Available services:
- analysis_audit: Шинжилгээний аудит логын үйлчилгээ
- analysis_workflow: Шинжилгээний approve/reject/save workflow
- sample_service: Дээжний бизнес логик
- report_service: Тайлан, статистик, химичийн гүйцэтгэл
- equipment_service: Тоног төхөөрөмжийн калибровка, ашиглалт
- admin_service: Хэрэглэгч, тохиргоо, стандарт удирдлага
- chemical_service: Химийн бодисын бизнес логик
- import_service: CSV/Excel импорт
- spare_parts_service: Сэлбэг хэрэгслийн бизнес логик
"""

from app.services.analysis_audit import log_analysis_action
from app.services.sample_service import (
    archive_samples,
    get_sample_report_data,
    get_samples_with_results,
    build_sample_summary_data,
    ArchiveResult,
    SampleReportData,
)

__all__ = [
    "log_analysis_action",
    "archive_samples",
    "get_sample_report_data",
    "get_samples_with_results",
    "build_sample_summary_data",
    "ArchiveResult",
    "SampleReportData",
]
