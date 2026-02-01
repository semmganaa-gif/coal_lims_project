# app/services/sample_service.py
# -*- coding: utf-8 -*-
"""
Sample Service - Дээжний бизнес логик.

Routes-аас салгасан бизнес логикийг агуулна:
- Дээж архивлах/сэргээх
- Дээжний тайлан тооцоолол
- Дээжний нэгтгэл өгөгдөл
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Optional

from app import db
from app.models import Sample, AnalysisResult
from app.repositories import SampleRepository, AnalysisResultRepository
from app.utils.conversions import calculate_all_conversions
from app.utils.parameters import PARAMETER_DEFINITIONS, get_canonical_name
from app.utils.sorting import sort_samples
from app.constants import SUMMARY_VIEW_COLUMNS

logger = logging.getLogger(__name__)


# =============================================================================
# Data Classes
# =============================================================================

@dataclass
class ArchiveResult:
    """Архивлах үйлдлийн үр дүн."""
    success: bool
    updated_count: int
    message: str
    error: Optional[str] = None


@dataclass
class SampleReportData:
    """Дээжний тайлангийн өгөгдөл."""
    sample: Sample
    calculations: dict[str, Any]
    report_date: datetime
    error: Optional[str] = None


# =============================================================================
# Service Functions
# =============================================================================

def archive_samples(sample_ids: list[int], archive: bool = True) -> ArchiveResult:
    """
    Дээжүүдийг архивлах эсвэл сэргээх.

    Args:
        sample_ids: Дээжний ID-уудын жагсаалт
        archive: True бол архивлах, False бол сэргээх

    Returns:
        ArchiveResult: Үйлдлийн үр дүн

    Examples:
        >>> result = archive_samples([1, 2, 3], archive=True)
        >>> if result.success:
        ...     print(f"Archived {result.updated_count} samples")
    """
    if not sample_ids:
        return ArchiveResult(
            success=False,
            updated_count=0,
            message="Дээж сонгоогүй байна.",
            error="NO_SAMPLES"
        )

    try:
        new_status = "archived" if archive else "new"
        # Repository ашиглах
        updated_count = SampleRepository.update_status(sample_ids, new_status)

        action_text = "архивд шилжүүллээ" if archive else "архивнаас сэргээллээ"
        message = f"{updated_count} дээжийг амжилттай {action_text}."

        logger.info(f"Samples {'archived' if archive else 'unarchived'}: {sample_ids}")

        return ArchiveResult(
            success=True,
            updated_count=updated_count,
            message=message
        )

    except Exception as e:
        db.session.rollback()
        logger.error(f"Error archiving samples: {e}")
        return ArchiveResult(
            success=False,
            updated_count=0,
            message=f"Архивлах үед алдаа гарлаа: {e}",
            error=str(e)
        )


def get_sample_report_data(sample_id: int) -> SampleReportData:
    """
    Дээжний тайлангийн өгөгдлийг бэлтгэх.

    Args:
        sample_id: Дээжний ID

    Returns:
        SampleReportData: Тайлангийн өгөгдөл

    Examples:
        >>> report = get_sample_report_data(123)
        >>> if not report.error:
        ...     print(f"Report for: {report.sample.sample_code}")
    """
    from app.utils.datetime import now_local

    # Repository ашиглах
    sample = SampleRepository.get_by_id(sample_id)
    if not sample:
        return SampleReportData(
            sample=None,  # type: ignore
            calculations={},
            report_date=now_local(),
            error="SAMPLE_NOT_FOUND"
        )

    # Repository ашиглан approved/pending_review үр дүнгүүд авах
    raw_results = AnalysisResultRepository.get_approved_by_sample(sample_id)

    # Canonical нэрсээр бүлэглэх
    raw_canonical_data = {}
    for r in raw_results:
        canonical_name = get_canonical_name(r.analysis_code)
        if canonical_name:
            raw_canonical_data[canonical_name] = {
                "value": r.final_result,
                "id": r.id,
                "status": r.status,
            }

    # Тооцоолол хийх
    try:
        calculations = calculate_all_conversions(raw_canonical_data, PARAMETER_DEFINITIONS)
    except Exception as e:
        logger.error(f"Calculation error for sample {sample_id}: {e}")
        return SampleReportData(
            sample=sample,
            calculations={},
            report_date=now_local(),
            error=f"Тооцоолол хийхэд алдаа: {e}"
        )

    return SampleReportData(
        sample=sample,
        calculations=calculations,
        report_date=now_local()
    )


def get_samples_with_results(
    exclude_archived: bool = True,
    sort_by: str = "full"
) -> list[Sample]:
    """
    Үр дүнтэй дээжүүдийг авах.

    Args:
        exclude_archived: Архивлагдсан дээжүүдийг хасах эсэх
        sort_by: Эрэмбэлэх арга ("full", "code", "date")

    Returns:
        Дээжүүдийн жагсаалт

    Examples:
        >>> samples = get_samples_with_results(exclude_archived=True)
        >>> print(f"Found {len(samples)} samples with results")
    """
    # Үр дүнтэй дээжүүдийг шүүх subquery
    exists_q = (
        db.session.query(AnalysisResult.id)
        .filter(
            AnalysisResult.sample_id == Sample.id,
            AnalysisResult.status.in_(["approved", "pending_review"]),
        )
        .exists()
    )

    query = db.session.query(Sample).filter(exists_q, Sample.lab_type == 'coal')

    if exclude_archived:
        query = query.filter(Sample.status != "archived")

    samples = query.all()

    # Эрэмбэлэх
    return sort_samples(samples, by=sort_by)


def build_sample_summary_data(samples: list[Sample]) -> dict[str, Any]:
    """
    Дээжний нэгтгэлийн өгөгдлийг бүрдүүлэх.

    Args:
        samples: Дээжүүдийн жагсаалт

    Returns:
        Dict containing:
        - results_map: {sample_id: {code: {value, id, status}}}
        - analysis_dates_map: {sample_id: date_str}
        - analysis_types: Шинжилгээний төрлүүдийн жагсаалт

    Examples:
        >>> samples = get_samples_with_results()
        >>> summary = build_sample_summary_data(samples)
        >>> print(f"Processed {len(summary['results_map'])} samples")
    """
    if not samples:
        return {
            "results_map": {},
            "analysis_dates_map": {},
            "analysis_types": []
        }

    sample_ids = [s.id for s in samples]

    # Repository ашиглан бүх үр дүнг нэг query-р авах
    all_db_results = AnalysisResultRepository.get_approved_by_sample_ids(sample_ids)

    # Sample тус бүрийн canonical үр дүнгүүд
    canonical_results_by_sample: dict[int, dict] = {sid: {} for sid in sample_ids}
    analysis_dates_raw_map: dict[int, list] = {sid: [] for sid in sample_ids}

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

    # Тооцоолол хийх
    results_map: dict[int, dict] = {}
    analysis_dates_map: dict[int, str] = {}

    for sample_id in sample_ids:
        raw_canonical_data = canonical_results_by_sample.get(sample_id, {})

        try:
            all_calculated_data = calculate_all_conversions(
                raw_canonical_data, PARAMETER_DEFINITIONS
            )
        except Exception as e:
            logger.warning(f"Calculation error for sample {sample_id}: {e}")
            all_calculated_data = raw_canonical_data

        # Template-д зориулж alias руу буцаах
        final_data_for_template = _map_to_template_codes(all_calculated_data)
        results_map[sample_id] = final_data_for_template

        # Хамгийн сүүлийн шинжилгээний огноо
        dates = analysis_dates_raw_map.get(sample_id, [])
        if dates:
            latest = max(dates)
            analysis_dates_map[sample_id] = latest.strftime("%Y-%m-%d")

    # Шинжилгээний төрлүүд
    analysis_types = _build_analysis_types()

    return {
        "results_map": results_map,
        "analysis_dates_map": analysis_dates_map,
        "analysis_types": analysis_types
    }


# =============================================================================
# Helper Functions
# =============================================================================

def _map_to_template_codes(calculated_data: dict) -> dict:
    """Canonical нэрсээс template код руу хөрвүүлэх."""
    result = {}

    # Canonical → template code mapping
    CANONICAL_TO_TEMPLATE = {
        "ash_d": "Ad",
        "volatile_matter_daf": "Vdaf",
        "fixed_carbon_ad": "FC,ad",
        "fixed_carbon_d": "FC,d",
        "fixed_carbon_daf": "FC,daf",
        "total_sulfur_d": "St,d",
        "total_sulfur_daf": "St,daf",
        "calorific_value_d": "Qgr,d",
        "calorific_value_daf": "Qgr,daf",
        "qnet_ar": "Qnet,ar",
        "relative_density": "TRD,ad",
        "relative_density_d": "TRD,d",
        "hydrogen_d": "H,d",
        "phosphorus_d": "P,d",
        "total_fluorine_d": "F,d",
        "total_chlorine_d": "Cl,d",
    }

    for col_view in SUMMARY_VIEW_COLUMNS:
        template_code = col_view["code"]

        # Тусгай mapping шалгах
        lookup_key = None
        for canonical, tcode in CANONICAL_TO_TEMPLATE.items():
            if tcode == template_code:
                lookup_key = canonical
                break

        if not lookup_key:
            # canonical_base эсвэл template_code-оос canonical нэр авах
            lookup_key = get_canonical_name(
                col_view.get("canonical_base") or template_code
            )

        if lookup_key and lookup_key in calculated_data:
            result[template_code] = calculated_data[lookup_key]

    return result


def _build_analysis_types() -> list:
    """Summary view-д хэрэгтэй шинжилгээний төрлүүдийг үүсгэх."""
    analysis_types = []

    for col_view in SUMMARY_VIEW_COLUMNS:
        final_code = col_view["code"]
        canonical_name = col_view.get("canonical_base", "")

        # Display name авах
        details = PARAMETER_DEFINITIONS.get(canonical_name)
        display_name = final_code
        if details and details.get("display_name"):
            display_name = details["display_name"]

        # Fake object үүсгэх (template-д code/name хэрэгтэй)
        fake_type = type(
            "FakeType", (object,), {"code": final_code, "name": display_name}
        )()
        analysis_types.append(fake_type)

    return analysis_types
