# app/services/mine2nemo_service.py
# -*- coding: utf-8 -*-
"""Mine2NEMO ProcessControl SQL Server integration.

Зорилго: CHPP 2-hourly дээжүүдийн approved үр дүнг Mine2NEMO дэх
QualityPlantFeed / QualityPrimaryProduct / QualitySecondaryProduct
table-руу INSERT/UPDATE хийх.

Хэрэглэгчийн workflow (Sample Summary → "Mine2NEMO" button):
  1. Хэрэглэгч grid дээрээс CHPP 2-hourly дээж сонгоно
  2. POST /api/v1/mine2nemo/send {sample_ids: [...]}
  3. Backend:
     a. Sample → table routing (mine2nemo_mapping.route_to_mine2nemo)
     b. Mine2NEMO-д тус sample код байгаа эсэх шалгана
     c. Байгаагүй бол INSERT, байгаа бол UPDATE
     d. QualityDate-р parent date table-руу row insert (idempotent)
  4. Result: success/failed counts + per-sample status

Конфиг (.env):
  MINE2NEMO_DATABASE_URL=mssql+pymssql://user:pass@host:port/Mine2NEMO

Note: Энэ сервис нь тусдаа DB-руу шууд бичдэг. Шинэ Mine2NEMO API байх
үед энэ нь deprecated болж REST POST-руу шилжинэ.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, date
from typing import Optional

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

from flask import current_app

from app import db
from app.constants import AnalysisResultStatus
from app.constants.mine2nemo_mapping import (
    TABLE_PLANT_FEED,
    TABLE_PRIMARY,
    TABLE_SECONDARY,
    route_to_mine2nemo,
)
from app.models import Sample, AnalysisResult
from app.utils.conversions import calculate_all_conversions
from app.utils.parameters import PARAMETER_DEFINITIONS, get_canonical_name

logger = logging.getLogger(__name__)


# =============================================================================
# Connection management
# =============================================================================

_engine: Optional[Engine] = None


def _get_engine() -> Optional[Engine]:
    """Mine2NEMO SQL Server engine singleton.

    Returns None config байхгүй бол (graceful — feature optional).
    """
    global _engine
    if _engine is not None:
        return _engine

    url = current_app.config.get("MINE2NEMO_DATABASE_URL")
    if not url:
        return None

    try:
        _engine = create_engine(
            url,
            pool_size=2,
            max_overflow=2,
            pool_pre_ping=True,
            pool_recycle=300,
        )
        return _engine
    except Exception as exc:
        logger.error("Mine2NEMO engine create failed: %s", exc)
        return None


def is_configured() -> bool:
    """Mine2NEMO config байгаа эсэх."""
    return bool(current_app.config.get("MINE2NEMO_DATABASE_URL"))


# =============================================================================
# Result helpers
# =============================================================================


@dataclass
class SendResult:
    """Нэг дээж илгээх үр дүн."""
    sample_id: int
    sample_code: str            # LIMS sample code
    success: bool
    action: str = ""            # "inserted" | "updated" | "skipped"
    error: Optional[str] = None
    target_table: Optional[str] = None
    mine2nemo_code: Optional[str] = None  # Mine2NEMO-руу очсон rewritten code
    # SELECT-back verification (INSERT/UPDATE-ийн дараа Mine2NEMO-аас row-аа дахин уншиж шалгах)
    verified: bool = False
    verification: Optional[dict] = None  # {Mt_ar, Mad, Aad, CreatedDate, CreatedBy}


@dataclass
class BulkSendResult:
    """Олон дээж илгээх нэгдсэн үр дүн."""
    success_count: int = 0
    failed_count: int = 0
    skipped_count: int = 0
    items: list[SendResult] = field(default_factory=list)


# =============================================================================
# Data preparation — sample results → Mine2NEMO row
# =============================================================================


def _gather_results(sample_id: int) -> dict[str, float]:
    """Sample-ийн approved canonical үр дүнг dict-ээр буцаах.

    Returns:
        {canonical_name: float_value} dict
    """
    results = db.session.execute(
        db.select(AnalysisResult).where(
            AnalysisResult.sample_id == sample_id,
            AnalysisResult.status == AnalysisResultStatus.APPROVED.value,
        )
    ).scalars().all()

    canonical: dict[str, float] = {}
    for r in results:
        cname = get_canonical_name(r.analysis_code)
        if cname and r.final_result is not None:
            try:
                canonical[cname] = float(r.final_result)
            except (TypeError, ValueError):
                continue
    return canonical


def _compute_quality_row(sample: Sample) -> dict[str, float | None]:
    """Sample-ийн final_results + бүх basis conversions-ыг тооцоолох.

    Returns:
        Mine2NEMO row-руу шууд орох mapping:
        {Mt_ar, Mad, Aad, Ad, Vad, Vdaf, St_ad, St_d, CSN, Gi, TRD_ad, TRD_d,
         Qgr_ad, Qgr_ar, Qnet_ar (secondary-д хэрэгтэй)}
    """
    raw = _gather_results(sample.id)
    final = calculate_all_conversions(raw, PARAMETER_DEFINITIONS)

    def _v(key: str) -> float | None:
        v = final.get(key)
        if isinstance(v, dict):
            v = v.get("value")
        return float(v) if v is not None else None

    return {
        "Mt_ar": _v("total_moisture"),
        "Mad": _v("inherent_moisture"),
        "Aad": _v("ash"),
        "Ad": _v("ash_d"),
        "Vad": _v("volatile_matter"),
        "Vdaf": _v("volatile_matter_daf"),
        "St_ad": _v("total_sulfur"),
        "St_d": _v("total_sulfur_d"),
        "CSN": _v("free_swelling_index"),
        "Gi": _v("caking_power"),
        "TRD_ad": _v("relative_density"),
        "TRD_d": _v("relative_density_d"),
        # Calorific (Secondary product-д)
        "Qgr_ad": _v("calorific_value"),
        "Qgr_ar": _v("calorific_value_ar"),
        "Qnet_ar": _v("qnet_ar"),
    }


def _build_param_dict(sample: Sample, values: dict, route: dict, username: str) -> dict:
    """SQL parameter dict бүтээх — INSERT/UPDATE-д ашиглана."""
    sd: date | None = sample.sample_date or (
        sample.received_date.date() if sample.received_date else None
    )
    # Mine2NEMO-руу очих rewriten SampleCode (CC/TC-д бүтээгдэхүүний нэр CC/TC болж rewrite)
    mine2nemo_code = route.get("mine2nemo_code") or sample.sample_code
    sample_time = route.get("sample_time")

    return {
        "QualityCategoryID": route.get("category_id"),  # UUID from mapping
        "QualityDate": sd,
        "SampleCode": mine2nemo_code,
        "SampleTime": sample_time,
        "Mt_ar": values.get("Mt_ar"),
        "Mad": values.get("Mad"),
        "Aad": values.get("Aad"),
        "Ad": values.get("Ad"),
        "Vad": values.get("Vad"),
        "Vdaf": values.get("Vdaf"),
        "St_ad": values.get("St_ad"),
        "St_d": values.get("St_d"),
        "CSN": values.get("CSN"),
        "Gi": values.get("Gi"),
        "TRD_ad": values.get("TRD_ad"),
        "TRD_d": values.get("TRD_d"),
        "Qgr_ad": values.get("Qgr_ad"),
        "Qgr_ar": values.get("Qgr_ar"),
        "Qnet_ar": values.get("Qnet_ar"),
        "CreatedDate": datetime.now(),
        "CreatedBy": username,
        "ProductionDate": datetime.combine(sd, datetime.min.time()) if sd else None,
        "ProductionDateShift": str(sd) if sd else "",
        "GroupName": route.get("group_name"),
    }


# =============================================================================
# SQL builders
# =============================================================================


def _build_check_sql(table: str) -> str:
    """Mine2NEMO-д энэ SampleCode байгаа эсэх шалгах SQL."""
    return f"SELECT TOP 1 1 FROM [Mine2NEMO].[ProcessControl].[{table}] WHERE SampleCode = :sample_code"


def _build_verify_sql(table: str) -> str:
    """INSERT/UPDATE-ийн дараа Mine2NEMO-аас row-аа дахин уншиж баталгаажуулах SQL.

    Note: QualityPlantFeed нь `ModifedDate` (typo) гэж бичигдсэн, бусад table-д
    `ModifiedDate` (зөв). Энэ нь Mine2NEMO schema-ийн legacy bug.
    """
    if table == TABLE_PLANT_FEED:
        mod_date_col = "ModifedDate"  # typo preserved (schema legacy)
    else:
        mod_date_col = "ModifiedDate"
    return (
        f"SELECT TOP 1 Mt_ar, Mad, Aad, CreatedDate, CreatedBy, "
        f"{mod_date_col}, ModifiedBy "
        f"FROM [Mine2NEMO].[ProcessControl].[{table}] WHERE SampleCode = :sample_code"
    )


def _build_insert_sql(table: str) -> str:
    """Mine2NEMO table-руу INSERT хийх SQL.

    Note: Table-уудын schema нь бараг ижил, гэхдээ Secondary-д Qgr_*/Qnet_*
    нэмэлт field бий. Энэ SQL нь бүх field-ыг агуулна — Primary/PlantFeed
    table-д Qgr_* field байхгүй бол алдаа гарна. Тиймээс table тус бүрт
    тусдаа SQL бүтээнэ.
    """
    if table == TABLE_SECONDARY:
        cols = (
            "QualityCategoryID, QualityDate, SampleCode, SampleTime, "
            "Mt_ar, Mad, Aad, Ad, Vad, Vdaf, St_ad, St_d, CSN, "
            "Qgr_ad, Qgr_ar, Qnet_ar, "
            "CreatedDate, CreatedBy, ProductionDate, ProductionDateShift"
        )
        vals = (
            ":QualityCategoryID, :QualityDate, :SampleCode, :SampleTime, "
            ":Mt_ar, :Mad, :Aad, :Ad, :Vad, :Vdaf, :St_ad, :St_d, :CSN, "
            ":Qgr_ad, :Qgr_ar, :Qnet_ar, "
            ":CreatedDate, :CreatedBy, :ProductionDate, :ProductionDateShift"
        )
    elif table == TABLE_PLANT_FEED:
        cols = (
            "QualityCategoryID, QualityDate, SampleCode, SampleTime, "
            "Mt_ar, Mad, Aad, Ad, Vad, Vdaf, St_ad, St_d, CSN, Gi, TRD_ad, TRDd, "
            "CreatedDate, CreatedBy, ProductionDate, ProductionDateShift, GroupName"
        )
        vals = (
            ":QualityCategoryID, :QualityDate, :SampleCode, :SampleTime, "
            ":Mt_ar, :Mad, :Aad, :Ad, :Vad, :Vdaf, :St_ad, :St_d, :CSN, :Gi, :TRD_ad, :TRD_d, "
            ":CreatedDate, :CreatedBy, :ProductionDate, :ProductionDateShift, :GroupName"
        )
    else:  # TABLE_PRIMARY
        cols = (
            "QualityCategoryID, QualityDate, SampleCode, SampleTime, "
            "Mt_ar, Mad, Aad, Ad, Vad, Vdaf, St_ad, St_d, CSN, Gi, TRD_ad, TRD_d, "
            "CreatedDate, CreatedBy, ProductionDate, ProductionDateShift"
        )
        vals = (
            ":QualityCategoryID, :QualityDate, :SampleCode, :SampleTime, "
            ":Mt_ar, :Mad, :Aad, :Ad, :Vad, :Vdaf, :St_ad, :St_d, :CSN, :Gi, :TRD_ad, :TRD_d, "
            ":CreatedDate, :CreatedBy, :ProductionDate, :ProductionDateShift"
        )

    return f"INSERT INTO [Mine2NEMO].[ProcessControl].[{table}] ({cols}) VALUES ({vals})"


def _build_update_sql(table: str) -> str:
    """SampleCode-аар Mine2NEMO row-г UPDATE."""
    if table == TABLE_SECONDARY:
        sets = (
            "QualityDate = :QualityDate, Mt_ar = :Mt_ar, Mad = :Mad, "
            "Aad = :Aad, Ad = :Ad, Vad = :Vad, Vdaf = :Vdaf, "
            "St_ad = :St_ad, St_d = :St_d, CSN = :CSN, "
            "Qgr_ad = :Qgr_ad, Qgr_ar = :Qgr_ar, Qnet_ar = :Qnet_ar, "
            "ModifiedDate = :CreatedDate, ModifiedBy = :CreatedBy, "
            "ProductionDate = :ProductionDate, ProductionDateShift = :ProductionDateShift"
        )
    elif table == TABLE_PLANT_FEED:
        sets = (
            "QualityDate = :QualityDate, Mt_ar = :Mt_ar, Mad = :Mad, "
            "Aad = :Aad, Ad = :Ad, Vad = :Vad, Vdaf = :Vdaf, "
            "St_ad = :St_ad, St_d = :St_d, CSN = :CSN, Gi = :Gi, "
            "TRD_ad = :TRD_ad, TRDd = :TRD_d, "
            "ModifedDate = :CreatedDate, ModifiedBy = :CreatedBy, "
            "ProductionDate = :ProductionDate, ProductionDateShift = :ProductionDateShift, "
            "GroupName = :GroupName"
        )
    else:  # TABLE_PRIMARY
        sets = (
            "QualityDate = :QualityDate, Mt_ar = :Mt_ar, Mad = :Mad, "
            "Aad = :Aad, Ad = :Ad, Vad = :Vad, Vdaf = :Vdaf, "
            "St_ad = :St_ad, St_d = :St_d, CSN = :CSN, Gi = :Gi, "
            "TRD_ad = :TRD_ad, TRD_d = :TRD_d, "
            "ModifiedDate = :CreatedDate, ModifiedBy = :CreatedBy, "
            "ProductionDate = :ProductionDate, ProductionDateShift = :ProductionDateShift"
        )

    return f"UPDATE [Mine2NEMO].[ProcessControl].[{table}] SET {sets} WHERE SampleCode = :SampleCode"


def _build_date_upsert_sql(date_table: str) -> str:
    """QualityDate-ыг date tracking table-руу idempotent insert (parent record)."""
    return (
        f"IF NOT EXISTS (SELECT 1 FROM [Mine2NEMO].[ProcessControl].[{date_table}] "
        f"WHERE QualityDate = :QualityDate) "
        f"INSERT INTO [Mine2NEMO].[ProcessControl].[{date_table}] (QualityDate) "
        f"VALUES (:QualityDate)"
    )


# =============================================================================
# Public API
# =============================================================================


def send_sample(sample_id: int, username: str) -> SendResult:
    """Нэг дээжийг Mine2NEMO-руу илгээх (INSERT эсвэл UPDATE).

    Returns:
        SendResult — success/failure + action.
    """
    sample = db.session.get(Sample, sample_id)
    if sample is None:
        return SendResult(sample_id, "", False, error="Дээж олдсонгүй")

    # Route шалгах
    route = route_to_mine2nemo(
        sample.client_name or "",
        sample.sample_type or "",
        sample.sample_code or "",
    )
    if route is None:
        return SendResult(
            sample_id, sample.sample_code or "",
            success=False, action="skipped",
            error="Mine2NEMO-руу очих дээж биш (CHPP/2 hourly биш эсвэл mapping олдсонгүй)",
        )

    table = route["table"]
    date_table = route["date_table"]

    engine = _get_engine()
    if engine is None:
        return SendResult(
            sample_id, sample.sample_code,
            success=False, error="Mine2NEMO config байхгүй (.env-д MINE2NEMO_DATABASE_URL)",
            target_table=table,
        )

    try:
        values = _compute_quality_row(sample)
        params = _build_param_dict(sample, values, route, username)
        mine2nemo_code = params["SampleCode"]  # rewritten code (CC_<date>_<shift>)

        verification: dict | None = None
        with engine.begin() as conn:
            # 1. QualityDate parent table — idempotent
            if params.get("QualityDate"):
                conn.execute(text(_build_date_upsert_sql(date_table)), {"QualityDate": params["QualityDate"]})

            # 2. Sample exists? (Mine2NEMO sample_code-аар шалгана)
            exists = conn.execute(
                text(_build_check_sql(table)),
                {"sample_code": mine2nemo_code},
            ).first()

            if exists:
                conn.execute(text(_build_update_sql(table)), params)
                action = "updated"
            else:
                conn.execute(text(_build_insert_sql(table)), params)
                action = "inserted"

            # 3. SELECT-back verification — Mine2NEMO-аас row-аа дахин уншиж
            row = conn.execute(
                text(_build_verify_sql(table)),
                {"sample_code": mine2nemo_code},
            ).first()
            if row:
                verification = {
                    "Mt_ar": float(row[0]) if row[0] is not None else None,
                    "Mad": float(row[1]) if row[1] is not None else None,
                    "Aad": float(row[2]) if row[2] is not None else None,
                    "CreatedDate": str(row[3]) if row[3] is not None else None,
                    "CreatedBy": row[4] if row[4] is not None else None,
                    "ModifiedDate": str(row[5]) if row[5] is not None else None,
                    "ModifiedBy": row[6] if row[6] is not None else None,
                }

        verified = verification is not None
        logger.info(
            "Mine2NEMO %s: lims=%s nemo=%s table=%s user=%s verified=%s",
            action, sample.sample_code, mine2nemo_code, table, username, verified,
        )

        # 4. Audit log — ISO 17025 trail
        try:
            from app.utils.audit import log_audit
            log_audit(
                action=f"mine2nemo_{action}",
                resource_type="Sample",
                resource_id=sample.id,
                details={
                    "lims_sample_code": sample.sample_code,
                    "mine2nemo_sample_code": mine2nemo_code,
                    "target_table": table,
                    "verified": verified,
                    "verification": verification,
                },
            )
        except Exception as audit_exc:
            logger.warning("Audit log failed for Mine2NEMO send: %s", audit_exc)

        return SendResult(
            sample_id, sample.sample_code,
            success=True, action=action, target_table=table,
            mine2nemo_code=mine2nemo_code,
            verified=verified, verification=verification,
        )

    except Exception as exc:
        logger.exception("Mine2NEMO send failed: sample=%s", sample.sample_code)
        # Failure audit log
        try:
            from app.utils.audit import log_audit
            log_audit(
                action="mine2nemo_send_failed",
                resource_type="Sample",
                resource_id=sample.id,
                details={
                    "sample_code": sample.sample_code,
                    "target_table": table,
                    "error": str(exc)[:500],
                },
            )
        except Exception:
            pass
        return SendResult(
            sample_id, sample.sample_code,
            success=False, error=f"SQL alda: {exc}", target_table=table,
        )


def send_samples_bulk(sample_ids: list[int], username: str) -> BulkSendResult:
    """Олон дээжийг Mine2NEMO-руу илгээх."""
    bulk = BulkSendResult()
    for sid in sample_ids:
        res = send_sample(sid, username)
        bulk.items.append(res)
        if res.success:
            bulk.success_count += 1
        elif res.action == "skipped":
            bulk.skipped_count += 1
        else:
            bulk.failed_count += 1
    return bulk
