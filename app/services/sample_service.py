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
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from typing import Any, Optional

from sqlalchemy.exc import SQLAlchemyError

from app import db
from app.models import Sample, AnalysisResult
from app.utils.audit import log_audit
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
class _AnalysisTypeView:
    """Template-д шаардлагатай code/name бүтэц."""
    code: str
    name: str


@dataclass
class RegistrationResult:
    """Дээж бүртгэлийн үр дүн."""
    success: bool
    count: int
    message: str
    successful_codes: list[str] = field(default_factory=list)
    failed_codes: list[str] = field(default_factory=list)
    error: Optional[str] = None


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

        # Audit: Архивлах/сэргээх лог
        old_status = "new" if archive else "archived"
        action_name = 'sample_archived' if archive else 'sample_unarchived'
        for sid in sample_ids:
            log_audit(
                action=action_name,
                resource_type='Sample',
                resource_id=sid,
                details={'new_status': new_status},
                old_value={'status': old_status},
                new_value={'status': new_status},
            )

        return ArchiveResult(
            success=True,
            updated_count=updated_count,
            message=message
        )

    except SQLAlchemyError as e:
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
    except (ValueError, TypeError, KeyError, ZeroDivisionError) as e:
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
    # MG дээжийг хасна: Mad, Aad гэх мэт стандарт нүүрсний шинжилгээ байхгүй бол summary-д оруулахгүй
    WTL_MG_CODES = ['MG', 'MG_SIZE', 'MT', 'TRD']
    exists_q = (
        db.session.query(AnalysisResult.id)
        .filter(
            AnalysisResult.sample_id == Sample.id,
            AnalysisResult.status.in_(["approved", "pending_review"]),
            ~AnalysisResult.analysis_code.in_(WTL_MG_CODES),
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
        except (ValueError, TypeError, KeyError, ZeroDivisionError) as e:
            logger.error(f"Calculation error for sample {sample_id}: {e}", exc_info=True)
            all_calculated_data = {**raw_canonical_data, "_calc_error": True}

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

    # Canonical → template code mapping (reverse lookup-д ашиглана)
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
    # O(1) reverse lookup dict
    TEMPLATE_TO_CANONICAL = {v: k for k, v in CANONICAL_TO_TEMPLATE.items()}

    for col_view in SUMMARY_VIEW_COLUMNS:
        template_code = col_view["code"]

        # O(1) reverse lookup
        lookup_key = TEMPLATE_TO_CANONICAL.get(template_code)

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

        analysis_types.append(_AnalysisTypeView(code=final_code, name=display_name))

    return analysis_types


# =============================================================================
# Sample Registration Functions (Phase 7: extracted from routes/main/index.py)
# =============================================================================

def _build_sample_base(
    *,
    sample_code: str,
    user_id: int,
    client_name: str,
    sample_type: str,
    sample_condition: str,
    sample_date,
    return_sample: bool,
    retention_days: int,
    delivered_by: str,
    prepared_date,
    prepared_by: str,
    notes: Optional[str] = None,
    weight=None,
    location: Optional[str] = None,
    product: Optional[str] = None,
    hourly_system: Optional[str] = None,
    lab_type: str = "coal",
) -> Sample:
    """Дээж бүртгэлийн нийтлэг талбаруудыг бөглөх."""
    from app.utils.datetime import now_local

    sample = Sample(
        sample_code=sample_code,
        user_id=user_id,
        client_name=client_name,
        sample_type=sample_type,
        sample_condition=sample_condition,
        sample_date=sample_date,
        return_sample=return_sample,
        retention_date=(now_local() + timedelta(days=retention_days)).date(),
        delivered_by=delivered_by,
        prepared_date=prepared_date,
        prepared_by=prepared_by,
        notes=notes,
        weight=weight,
        location=location,
        product=product,
        hourly_system=hourly_system,
        analyses_to_perform="[]",
    )

    if lab_type != "coal":
        sample.lab_type = lab_type
    # PE дээжид lab_type='petrography' оноох
    if sample_type == "PE":
        sample.lab_type = "petrography"

    return sample


def _assign_and_add(sample: Sample) -> None:
    """Шинжилгээ оноож, SLA тохируулж, session-д нэмэх."""
    from app.utils.analysis_assignment import assign_analyses_to_sample
    from app.services.sla_service import assign_sla

    with db.session.no_autoflush:
        assign_analyses_to_sample(sample)
    assign_sla(sample)
    db.session.add(sample)


def register_batch_samples(
    *,
    codes: list[str],
    weights_map: dict[str, Optional[str]],
    requires_weight: bool,
    user_id: int,
    client_name: str,
    sample_type: str,
    sample_condition: str,
    sample_date,
    return_sample: bool,
    retention_days: int,
    delivered_by: str,
    prepared_date,
    prepared_by: str,
    notes: Optional[str],
    location: Optional[str],
    product: Optional[str],
    list_type: str,
) -> RegistrationResult:
    """
    Олон дээж нэг удаа бүртгэх (CHPP 2h/4h/12h, COM, multi_gen).

    Args:
        codes: Дээжний кодуудын жагсаалт
        weights_map: {code: weight_str} жин Map
        requires_weight: Жин шаардлагатай эсэх
        ... (бусад form талбарууд)

    Returns:
        RegistrationResult
    """
    from app.utils.sorting import custom_sample_sort_key
    from app.constants import MIN_SAMPLE_WEIGHT, MAX_SAMPLE_WEIGHT
    from app.monitoring import track_sample

    sorted_codes = sorted(codes, key=custom_sample_sort_key)
    successful, failed = [], []
    count = 0

    try:
        for code in sorted_codes:
            if not code:
                continue

            weight, is_valid = None, True
            if requires_weight:
                weight_str = weights_map.get(code)
                if weight_str:
                    try:
                        weight = float(weight_str)
                        if weight <= MIN_SAMPLE_WEIGHT:
                            failed.append(f"{code} (жин хэт бага: {weight}г)")
                            is_valid = False
                        elif weight > MAX_SAMPLE_WEIGHT:
                            failed.append(f"{code} (жин хэт том: {weight}г, max {MAX_SAMPLE_WEIGHT}г)")
                            is_valid = False
                    except ValueError:
                        failed.append(f'{code} (жин: "{weight_str}" буруу)')
                        is_valid = False
                else:
                    failed.append(f"{code} (жин оруулаагүй)")
                    is_valid = False

            if not is_valid:
                continue

            sample = _build_sample_base(
                sample_code=code,
                user_id=user_id,
                client_name=client_name,
                sample_type=sample_type,
                sample_condition=sample_condition,
                sample_date=sample_date,
                return_sample=return_sample,
                retention_days=retention_days,
                delivered_by=delivered_by,
                prepared_date=prepared_date,
                prepared_by=prepared_by,
                notes=notes,
                weight=weight,
                location=location if list_type == "multi_gen" else None,
                product=product if list_type == "multi_gen" and client_name in ("QC", "Proc") else None,
                hourly_system=list_type.replace("chpp_", "") if "chpp" in list_type else None,
            )
            _assign_and_add(sample)
            successful.append(code)
            count += 1

    except (SQLAlchemyError, ValueError, TypeError) as e:
        db.session.rollback()
        logger.error(f"Error during batch registration: {e}")
        return RegistrationResult(
            success=False, count=0, message="Дээж бүртгэхэд алдаа гарлаа.",
            failed_codes=failed, error=str(e),
        )

    if count > 0:
        from app.utils.database import safe_commit
        if not safe_commit(
            f"{count} ш дээж амжилттай бүртгэгдлээ.",
            "БҮРТГЭЛ АМЖИЛТГҮЙ: Дээжний код давхардсан байна.",
        ):
            return RegistrationResult(
                success=False, count=0, message="Дээжний код давхардсан байна.",
                failed_codes=failed, error="DUPLICATE_CODE",
            )

        for code in successful:
            log_audit(
                action="sample_created", resource_type="Sample",
                details={"sample_code": code, "client_name": client_name, "sample_type": sample_type},
            )
        for _ in range(count):
            track_sample(client=client_name, sample_type=sample_type)

    return RegistrationResult(
        success=True, count=count,
        message=f"{count} ш дээж амжилттай бүртгэгдлээ.",
        successful_codes=successful, failed_codes=failed,
    )


def register_wtl_auto_samples(
    *,
    sample_type: str,
    lab_number: str,
    user_id: int,
    sample_condition: str,
    sample_date,
    return_sample: bool,
    retention_days: int,
    delivered_by: str,
    prepared_date,
    prepared_by: str,
    notes: Optional[str],
) -> RegistrationResult:
    """
    WTL (WTL/Size/FL) дээжүүдийг автоматаар олон нэрээр үүсгэх.

    Returns:
        RegistrationResult
    """
    from app.constants import (
        WTL_SAMPLE_NAMES_19, WTL_SAMPLE_NAMES_70,
        WTL_SAMPLE_NAMES_6, WTL_SAMPLE_NAMES_2,
        WTL_SIZE_NAMES, WTL_FL_NAMES,
    )

    if not lab_number:
        return RegistrationResult(
            success=False, count=0,
            message="WTL-д лабораторийн дугаар шаардлагатай.",
            error="MISSING_LAB_NUMBER",
        )

    name_map = {
        "WTL": WTL_SAMPLE_NAMES_19 + WTL_SAMPLE_NAMES_70 + WTL_SAMPLE_NAMES_6 + WTL_SAMPLE_NAMES_2,
        "Size": WTL_SIZE_NAMES,
        "FL": WTL_FL_NAMES,
    }
    all_wtl_names = name_map.get(sample_type, [])

    count = 0
    for name in all_wtl_names:
        final_code = f"{lab_number}_{name}"
        sample = _build_sample_base(
            sample_code=final_code,
            user_id=user_id,
            client_name="WTL",
            sample_type=sample_type,
            sample_condition=sample_condition,
            sample_date=sample_date,
            return_sample=return_sample,
            retention_days=retention_days,
            delivered_by=delivered_by,
            prepared_date=prepared_date,
            prepared_by=prepared_by,
            notes=notes,
        )
        _assign_and_add(sample)
        count += 1

    if count > 0:
        from app.utils.database import safe_commit
        if not safe_commit(
            f"{count} ш {sample_type} дээж амжилттай бүртгэгдлээ.",
            "БҮРТГЭЛ АМЖИЛТГҮЙ: Дээжний код давхардсан байна.",
        ):
            return RegistrationResult(
                success=False, count=0, message="Дээжний код давхардсан байна.",
                error="DUPLICATE_CODE",
            )
        for name in all_wtl_names:
            log_audit(
                action="sample_created", resource_type="Sample",
                details={
                    "sample_code": f"{lab_number}_{name}",
                    "client_name": "WTL", "sample_type": sample_type, "lab_type": "water",
                },
            )

    return RegistrationResult(
        success=True, count=count,
        message=f"{count} ш {sample_type} дээж амжилттай бүртгэгдлээ.",
    )


def register_lab_sample(
    *,
    sample_type: str,
    sample_date,
    user_id: int,
    sample_condition: str,
    return_sample: bool,
    delivered_by: str,
    prepared_date,
    prepared_by: str,
    notes: Optional[str],
) -> RegistrationResult:
    """
    LAB дээж бүртгэх (CM/GBW/Test) — автоматаар нэр үүсгэнэ.

    Returns:
        RegistrationResult
    """
    from app.utils.datetime import now_local

    formatted_date = sample_date.strftime("%Y%m%d")
    # 12h shift code
    from app.routes.main.helpers import get_12h_shift_code
    shift_code = get_12h_shift_code(now_local())

    if sample_type == "CM":
        from app.repositories import ControlStandardRepository
        active_cm = ControlStandardRepository.get_active()
        cm_name = active_cm.name if active_cm else "CM"
        final_code = f"{cm_name}_{formatted_date}{shift_code}"
    elif sample_type == "GBW":
        from app.repositories import GbwStandardRepository
        active_gbw = GbwStandardRepository.get_active()
        gbw_name = active_gbw.name if active_gbw else "GBW"
        final_code = f"{gbw_name}_{formatted_date}{shift_code}"
    elif sample_type == "Test":
        final_code = f"Test_{formatted_date}{shift_code}"
    else:
        final_code = f"LAB_UNKNOWN_{formatted_date}"

    sample = _build_sample_base(
        sample_code=final_code,
        user_id=user_id,
        client_name="LAB",
        sample_type=sample_type,
        sample_condition=sample_condition,
        sample_date=sample_date,
        return_sample=return_sample,
        retention_days=30,
        delivered_by=delivered_by,
        prepared_date=prepared_date,
        prepared_by=prepared_by,
        notes=notes,
    )
    _assign_and_add(sample)

    from app.utils.database import safe_commit
    if not safe_commit(
        f"Дээж амжилттай бүртгэгдлээ. {final_code}",
        f'БҮРТГЭЛ АМЖИЛТГҮЙ: "{final_code}" дээж аль хэдийн бүртгэгдсэн байна.',
    ):
        return RegistrationResult(
            success=False, count=0, message=f'"{final_code}" давхардсан.',
            error="DUPLICATE_CODE",
        )

    log_audit(
        action="sample_created", resource_type="Sample", resource_id=sample.id,
        details={"sample_code": final_code, "client_name": "LAB", "sample_type": sample_type},
    )
    return RegistrationResult(success=True, count=1, message=f"Дээж бүртгэгдлээ: {final_code}")


def register_wtl_mg_test(
    *,
    sample_type: str,
    sample_code: Optional[str],
    wtl_module: Optional[str],
    wtl_supplier: Optional[str],
    wtl_vehicle: Optional[str],
    sample_date,
    user_id: int,
    sample_condition: str,
    return_sample: bool,
    retention_days: int,
    delivered_by: str,
    prepared_date,
    prepared_by: str,
    notes: Optional[str],
) -> RegistrationResult:
    """
    WTL MG (structured) / Test (manual sample_code) дээж бүртгэх.

    Returns:
        RegistrationResult
    """
    if sample_type == "MG":
        wtl_supplier = (wtl_supplier or "").strip()
        wtl_vehicle = (wtl_vehicle or "").strip()
        if not wtl_module or not wtl_supplier or not wtl_vehicle:
            return RegistrationResult(
                success=False, count=0,
                message="MG-д Module, Supplier, Vehicle талбарууд шаардлагатай.",
                error="MISSING_FIELDS",
            )
        formatted_date = sample_date.strftime("%Y%m%d")
        final_code = f"MG_{wtl_module}_{wtl_supplier}_{formatted_date}_{wtl_vehicle}"
        notes_data = notes or ""
        if wtl_module:
            notes_data = f"Module: {wtl_module}; {notes_data}".strip("; ")
    else:
        if not sample_code:
            return RegistrationResult(
                success=False, count=0,
                message="Энэ WTL төрөлд дээжний нэр шаардлагатай.",
                error="MISSING_SAMPLE_CODE",
            )
        final_code = sample_code
        notes_data = notes

    sample = _build_sample_base(
        sample_code=final_code,
        user_id=user_id,
        client_name="WTL",
        sample_type=sample_type,
        sample_condition=sample_condition,
        sample_date=sample_date,
        return_sample=return_sample,
        retention_days=retention_days,
        delivered_by=delivered_by,
        prepared_date=prepared_date,
        prepared_by=prepared_by,
        notes=notes_data,
    )
    _assign_and_add(sample)

    from app.utils.database import safe_commit
    if not safe_commit(
        "Шинэ дээж амжилттай бүртгэгдлээ.",
        f'БҮРТГЭЛ АМЖИЛТГҮЙ: "{final_code}" дээж аль хэдийн бүртгэгдсэн байна.',
    ):
        return RegistrationResult(
            success=False, count=0, message=f'"{final_code}" давхардсан.',
            error="DUPLICATE_CODE",
        )

    log_audit(
        action="sample_created", resource_type="Sample", resource_id=sample.id,
        details={
            "sample_code": final_code, "client_name": "WTL",
            "sample_type": sample_type, "lab_type": "water",
        },
    )
    return RegistrationResult(success=True, count=1, message="Шинэ дээж амжилттай бүртгэгдлээ.")


# ==========================================================================
# RETENTION & DISPOSAL
# ==========================================================================

def get_retention_context(lab_type: str = "coal", warning_days: int = 30) -> dict:
    """
    Sample retention dashboard-д шаардлагатай бүх query-г нэг дор гүйцэтгэнэ.

    Returns:
        dict with keys: expired_samples, upcoming_samples, disposed_samples,
                        no_retention_samples, return_samples, today, warning_days
    """
    today = date.today()

    expired_samples = Sample.query.filter(
        Sample.lab_type == lab_type,
        Sample.retention_date < today,
        Sample.disposal_date.is_(None),
    ).order_by(Sample.retention_date.asc()).limit(200).all()

    upcoming_samples = Sample.query.filter(
        Sample.lab_type == lab_type,
        Sample.retention_date >= today,
        Sample.retention_date <= today + timedelta(days=warning_days),
        Sample.disposal_date.is_(None),
    ).order_by(Sample.retention_date.asc()).limit(200).all()

    disposed_samples = Sample.query.filter(
        Sample.lab_type == lab_type,
        Sample.disposal_date >= today - timedelta(days=90),
    ).order_by(Sample.disposal_date.desc()).limit(100).all()

    no_retention_samples = Sample.query.filter(
        Sample.lab_type == lab_type,
        Sample.retention_date.is_(None),
        Sample.disposal_date.is_(None),
        Sample.return_sample.is_(False),
    ).order_by(Sample.received_date.desc()).limit(100).all()

    return_samples = Sample.query.filter(
        Sample.lab_type == lab_type,
        Sample.return_sample.is_(True),
        Sample.disposal_date.is_(None),
        Sample.status == "completed",
    ).order_by(Sample.received_date.desc()).limit(100).all()

    return dict(
        expired_samples=expired_samples,
        upcoming_samples=upcoming_samples,
        disposed_samples=disposed_samples,
        no_retention_samples=no_retention_samples,
        return_samples=return_samples,
        today=today,
        warning_days=warning_days,
    )
