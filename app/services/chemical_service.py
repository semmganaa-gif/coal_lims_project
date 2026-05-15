# app/services/chemical_service.py
# -*- coding: utf-8 -*-
"""
Chemical Service - Химийн бодисын бизнес логик.

Routes-аас салгасан бизнес логикийг агуулна:
- Химийн бодис CRUD (create, update, dispose)
- Нөөц нэмэх / хэрэглээ бүртгэх (receive / consume)
- Жагсаалт шүүх, хайлт
- Статистик, хэрэглээний түүх
- Аудит лог бичих (ISO 17025 hash)
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from typing import Any, Optional

from sqlalchemy import func, case, or_, select
from flask_babel import lazy_gettext as _l
from sqlalchemy.exc import SQLAlchemyError

from app import db
from app.constants import AnalysisResultStatus, CHEMICAL_LIST_LIMIT, DASHBOARD_RECENT_LIMIT
from app.models import Chemical, ChemicalUsage, ChemicalLog
from app.repositories import ChemicalUsageRepository
from app.utils.security import escape_like_pattern
from app.utils.transaction import transactional

logger = logging.getLogger(__name__)


# =============================================================================
# Data Classes
# =============================================================================

@dataclass
class ConsumeResult:
    """Consume operation result."""
    success: bool
    new_quantity: float = 0.0
    chemical_status: str = ""
    error: str = ""


@dataclass
class BulkConsumeResult:
    """Bulk consume operation result."""
    success: bool
    count: int = 0
    errors: list = field(default_factory=list)
    error: str = ""


# =============================================================================
# Audit Log Helper
# =============================================================================

def create_chemical_log(chemical_id: int, user_id: int, action: str,
                        quantity_change: Optional[float] = None,
                        quantity_before: Optional[float] = None,
                        quantity_after: Optional[float] = None,
                        details: Optional[str] = None) -> ChemicalLog:
    """Химийн бодисын аудит лог бичих (ISO 17025 hash).

    Note: db.session.add() хийнэ, гэхдээ commit хийхгүй.
    """
    log = ChemicalLog(
        chemical_id=chemical_id,
        user_id=user_id,
        action=action,
        quantity_change=quantity_change,
        quantity_before=quantity_before,
        quantity_after=quantity_after,
        details=details,
    )
    log.data_hash = log.compute_hash()
    db.session.add(log)
    return log


# =============================================================================
# Query / Filter Functions
# =============================================================================

def _lab_conditions(lab: str) -> list:
    """Лабын шүүлтүүрийн SQL conditions буцаах (select.where() дотор spread)."""
    if lab and lab != "all":
        return [or_(Chemical.lab_type == lab, Chemical.lab_type == 'all')]
    return []


def get_chemical_list(lab: str = "all", category: str = "all",
                      status: str = "all", view: str = "all") -> list[dict]:
    """Химийн бодисын жагсаалт (HTML хуудсанд).

    Returns:
        List of chemical dicts (JSON-serializable).
    """
    stmt = select(Chemical).where(*_lab_conditions(lab))

    if category and category != "all":
        stmt = stmt.where(Chemical.category == category)

    if status and status != "all":
        stmt = stmt.where(Chemical.status == status)

    # View-specific filters
    if view == "expiring":
        warning_date = date.today() + timedelta(days=30)
        stmt = stmt.where(
            Chemical.expiry_date <= warning_date,
            Chemical.status != 'disposed'
        )
    elif view == "low_stock":
        stmt = stmt.where(Chemical.status == 'low_stock')

    if view != "disposed":
        stmt = stmt.where(Chemical.status != 'disposed')

    stmt = stmt.order_by(Chemical.name.asc())
    chemicals_query = list(db.session.execute(stmt).scalars().all())

    return [_chemical_to_list_dict(c) for c in chemicals_query]


def _chemical_to_list_dict(c: Chemical) -> dict:
    """Chemical model -> list dict."""
    days = c.days_until_expiry()
    return {
        'id': c.id,
        'name': c.name,
        'formula': c.formula,
        'cas_number': c.cas_number,
        'manufacturer': c.manufacturer,
        'supplier': c.supplier,
        'catalog_number': c.catalog_number,
        'lot_number': c.lot_number,
        'grade': c.grade,
        'quantity': c.quantity,
        'unit': c.unit,
        'reorder_level': c.reorder_level,
        'received_date': c.received_date.strftime('%Y-%m-%d') if c.received_date else None,
        'expiry_date': c.expiry_date.strftime('%Y-%m-%d') if c.expiry_date else None,
        'opened_date': c.opened_date.strftime('%Y-%m-%d') if c.opened_date else None,
        'opened_expiry_date': c.opened_expiry_date.strftime('%Y-%m-%d') if c.opened_expiry_date else None,
        'shelf_life_after_opening_days': c.shelf_life_after_opening_days,
        'storage_location': c.storage_location,
        'storage_conditions': c.storage_conditions,
        'hazard_class': c.hazard_class,
        'lab_type': c.lab_type,
        'category': c.category,
        'status': c.status,
        # GHS & SDS
        'ghs_pictograms': c.ghs_pictograms or [],
        'ghs_signal_word': c.ghs_signal_word or '',
        'sds_version': c.sds_version or '',
        'sds_revision_date': c.sds_revision_date.strftime('%Y-%m-%d') if c.sds_revision_date else None,
        # Expiry
        'days_alert_before_expiry': c.days_alert_before_expiry or 30,
        'prevent_use_if_expired': c.prevent_use_if_expired,
        'days_until_expiry': days,
        'is_expiring_soon': c.is_expiring_soon(),
    }


def get_chemical_stats_summary() -> dict:
    """Нөөцийн дүн (list page sidebar)."""
    def _count(*conds) -> int:
        stmt = select(func.count(Chemical.id)).where(*conds)
        return db.session.execute(stmt).scalar_one()

    return {
        'total': _count(Chemical.status != 'disposed'),
        'low_stock': _count(Chemical.status == 'low_stock'),
        'expired': _count(Chemical.status == 'expired'),
    }


def get_chemical_api_list(lab: str = "all", category: str = "all",
                          status: str = "all",
                          include_disposed: bool = False) -> list[dict]:
    """Химийн бодисын жагсаалт (AG Grid API).

    Returns:
        List of chemical dicts with expiry flags.
    """
    stmt = select(Chemical).where(*_lab_conditions(lab))

    if category and category != "all":
        stmt = stmt.where(Chemical.category == category)

    if status and status != "all":
        stmt = stmt.where(Chemical.status == status)

    if not include_disposed:
        stmt = stmt.where(Chemical.status != 'disposed')

    stmt = stmt.order_by(Chemical.name.asc()).limit(CHEMICAL_LIST_LIMIT)
    chemicals = list(db.session.execute(stmt).scalars().all())
    today = date.today()
    warning_date = today + timedelta(days=30)

    data = []
    for c in chemicals:
        is_expiring = bool(c.expiry_date and c.expiry_date <= warning_date and c.expiry_date > today)
        is_expired = bool(c.expiry_date and c.expiry_date <= today)

        data.append({
            "id": c.id,
            "name": c.name,
            "formula": c.formula or "",
            "cas_number": c.cas_number or "",
            "manufacturer": c.manufacturer or "",
            "lot_number": c.lot_number or "",
            "grade": c.grade or "",
            "quantity": c.quantity,
            "unit": c.unit,
            "reorder_level": c.reorder_level,
            "expiry_date": c.expiry_date.strftime("%Y-%m-%d") if c.expiry_date else "",
            "storage_location": c.storage_location or "",
            "lab_type": c.lab_type,
            "category": c.category,
            "status": c.status,
            "is_low_stock": c.status == 'low_stock',
            "is_expiring": is_expiring,
            "is_expired": is_expired,
        })

    return data


def get_low_stock_chemicals(lab: str = "all") -> dict:
    """Бага нөөцтэй химийн бодисууд.

    Returns:
        {"count": int, "items": list[dict]}
    """
    stmt = (
        select(Chemical)
        .where(Chemical.status == 'low_stock', *_lab_conditions(lab))
        .order_by(Chemical.name.asc())
    )
    chemicals = list(db.session.execute(stmt).scalars().all())

    items = [{
        "id": c.id,
        "name": c.name,
        "quantity": c.quantity,
        "unit": c.unit,
        "reorder_level": c.reorder_level,
        "lab_type": c.lab_type,
    } for c in chemicals]

    return {"count": len(items), "items": items}


def get_expiring_chemicals(lab: str = "all", days: int = 30) -> dict:
    """Хугацаа дуусах химийн бодисууд.

    Returns:
        {"count": int, "items": list[dict]}
    """
    today = date.today()
    warning_date = today + timedelta(days=days)

    stmt = (
        select(Chemical)
        .where(
            Chemical.expiry_date <= warning_date,
            Chemical.expiry_date >= today,
            Chemical.status != 'disposed',
            *_lab_conditions(lab),
        )
        .order_by(Chemical.expiry_date.asc())
    )
    chemicals = list(db.session.execute(stmt).scalars().all())

    items = [{
        "id": c.id,
        "name": c.name,
        "expiry_date": c.expiry_date.strftime("%Y-%m-%d"),
        "days_left": (c.expiry_date - today).days,
        "quantity": c.quantity,
        "unit": c.unit,
        "lab_type": c.lab_type,
    } for c in chemicals]

    return {"count": len(items), "items": items}


def search_chemicals(q: str, lab: str = "all", limit: int = 20) -> list[dict]:
    """Химийн бодис хайх (autocomplete).

    Args:
        q: Search query (min 2 chars).

    Returns:
        List of matching chemical dicts.
    """
    if len(q) < 2:
        return []

    safe_q = escape_like_pattern(q)
    stmt = (
        select(Chemical)
        .where(
            Chemical.status != 'disposed',
            or_(
                Chemical.name.ilike(f"%{safe_q}%"),
                Chemical.formula.ilike(f"%{safe_q}%"),
                Chemical.cas_number.ilike(f"%{safe_q}%"),
            ),
            *_lab_conditions(lab),
        )
        .order_by(Chemical.name.asc())
        .limit(limit)
    )
    chemicals = list(db.session.execute(stmt).scalars().all())

    return [{
        "id": c.id,
        "name": c.name,
        "formula": c.formula or "",
        "quantity": c.quantity,
        "unit": c.unit,
        "status": c.status,
        "label": f"{c.name} ({c.formula})" if c.formula else c.name
    } for c in chemicals]


def get_chemical_stats(lab: str = "all") -> dict:
    """Химийн бодисын статистик (dashboard).

    Returns:
        {"total", "low_stock", "expired", "expiring", "by_category"}
    """
    today = date.today()
    warning_date = today + timedelta(days=30)

    stats_q = db.session.query(
        func.count(Chemical.id).label('total'),
        func.count(case((Chemical.status == 'low_stock', Chemical.id))).label('low_stock'),
        func.count(case((Chemical.status == 'expired', Chemical.id))).label('expired'),
        func.count(case((
            (Chemical.expiry_date <= warning_date) & (Chemical.expiry_date > today),
            Chemical.id
        ))).label('expiring'),
    ).filter(Chemical.status != 'disposed')

    if lab and lab != "all":
        stats_q = stats_q.filter(
            (Chemical.lab_type == lab) | (Chemical.lab_type == 'all')
        )

    row = stats_q.one()

    by_category = db.session.query(
        Chemical.category,
        func.count(Chemical.id)
    ).filter(Chemical.status != 'disposed')

    if lab and lab != "all":
        by_category = by_category.filter(
            (Chemical.lab_type == lab) | (Chemical.lab_type == 'all')
        )

    by_category = by_category.group_by(Chemical.category).all()

    return {
        "total": row.total,
        "low_stock": row.low_stock,
        "expired": row.expired,
        "expiring": row.expiring,
        "by_category": {cat: cnt for cat, cnt in by_category}
    }


def get_usage_history(chemical_id: Optional[int] = None, lab: str = "all",
                      start_date: Optional[str] = None,
                      end_date: Optional[str] = None,
                      limit: int = 100) -> dict:
    """Химийн бодисын хэрэглээний түүх.

    Args:
        start_date/end_date: "YYYY-MM-DD" format strings.

    Returns:
        {"items": list[dict], "count": int}

    Raises:
        ValueError: on bad date format.
    """
    usages = ChemicalUsageRepository.query_with_chemical(
        chemical_id=chemical_id, lab=lab,
        start_date=start_date, end_date=end_date, limit=limit,
    )

    data = [{
        "id": u.id,
        "chemical_id": u.chemical_id,
        "chemical_name": c.name,
        "quantity_used": u.quantity_used,
        "unit": u.unit or c.unit,
        "purpose": u.purpose or "",
        "analysis_code": u.analysis_code or "",
        "used_at": u.used_at.strftime("%Y-%m-%d %H:%M") if u.used_at else "",
        "used_by": u.used_by.username if u.used_by else "",
    } for u, c in usages]

    return {"items": data, "count": len(data)}


def get_journal_rows(lab: str = "all", start_date: Optional[str] = None,
                     end_date: Optional[str] = None) -> list[dict]:
    """Химийн бодисын журнал (бүх хэрэглээ).

    Returns:
        List of row dicts for AG Grid.
    """
    stmt = (
        select(ChemicalUsage, Chemical)
        .join(Chemical, ChemicalUsage.chemical_id == Chemical.id)
        .where(*_lab_conditions(lab))
    )

    if start_date:
        start_dt = datetime.strptime(start_date, "%Y-%m-%d")
        stmt = stmt.where(ChemicalUsage.used_at >= start_dt)

    if end_date:
        end_dt = datetime.strptime(end_date, "%Y-%m-%d")
        end_dt = end_dt.replace(hour=23, minute=59, second=59)
        stmt = stmt.where(ChemicalUsage.used_at <= end_dt)

    stmt = stmt.order_by(ChemicalUsage.used_at.desc()).limit(DASHBOARD_RECENT_LIMIT)
    usages = list(db.session.execute(stmt).all())

    rows = []
    for usage, chemical in usages:
        rows.append({
            "date": usage.used_at.strftime("%Y-%m-%d %H:%M") if usage.used_at else "",
            "chemical": chemical.name,
            "chemical_id": chemical.id,
            "formula": chemical.formula or "",
            "quantity": f"-{usage.quantity_used} {usage.unit or chemical.unit}",
            "purpose": usage.purpose or "",
            "analysis": usage.analysis_code or "",
            "user": usage.used_by.username if usage.used_by else "",
            "before": round(usage.quantity_before, 2) if usage.quantity_before else None,
            "after": round(usage.quantity_after, 2) if usage.quantity_after else None,
        })

    return rows


# =============================================================================
# Create / Update / Delete Operations
# =============================================================================

def create_chemical(data: dict, user_id: int) -> Chemical:
    """Шинэ химийн бодис үүсгэх.

    Args:
        data: Chemical field dict (name, formula, quantity, etc.)
        user_id: Created by user ID.

    Returns:
        Created Chemical instance (flushed, not committed).

    Note:
        Caller must commit the session.
    """
    quantity = float(data.get("quantity", 0) or 0)

    reorder_level = None
    if data.get("reorder_level"):
        reorder_level = float(data["reorder_level"])

    chemical = Chemical(
        name=data.get("name"),
        cas_number=data.get("cas_number"),
        formula=data.get("formula"),
        manufacturer=data.get("manufacturer"),
        supplier=data.get("supplier"),
        catalog_number=data.get("catalog_number"),
        lot_number=data.get("lot_number"),
        grade=data.get("grade"),
        quantity=quantity,
        unit=data.get("unit", "mL"),
        reorder_level=reorder_level,
        received_date=_parse_date(data.get("received_date")),
        expiry_date=_parse_date(data.get("expiry_date")),
        opened_date=_parse_date(data.get("opened_date")),
        storage_location=data.get("storage_location"),
        storage_conditions=data.get("storage_conditions"),
        hazard_class=data.get("hazard_class"),
        lab_type=data.get("lab_type", "all"),
        category=data.get("category", "other"),
        notes=data.get("notes"),
        ghs_pictograms=data.get("ghs_pictograms") or [],
        ghs_signal_word=data.get("ghs_signal_word") or None,
        sds_version=data.get("sds_version") or None,
        sds_revision_date=_parse_date(data.get("sds_revision_date")),
        shelf_life_after_opening_days=int(data["shelf_life_after_opening_days"]) if data.get("shelf_life_after_opening_days") else None,
        days_alert_before_expiry=int(data["days_alert_before_expiry"]) if data.get("days_alert_before_expiry") else 30,
        prevent_use_if_expired=bool(data.get("prevent_use_if_expired")),
        created_by_id=user_id,
    )

    chemical.update_status()
    db.session.add(chemical)
    db.session.flush()  # ID авах

    create_chemical_log(
        chemical.id, user_id, 'created',
        quantity_change=quantity,
        quantity_before=0,
        quantity_after=quantity,
        details=f"Шинээр бүртгэв: {chemical.name}"
    )

    return chemical


def update_chemical(chemical: Chemical, data: dict, user_id: int) -> None:
    """Химийн бодис шинэчлэх.

    Args:
        chemical: Existing Chemical instance.
        data: Updated field dict.
        user_id: User performing the update.

    Note:
        Caller must commit the session.
    """
    old_quantity = chemical.quantity

    # Date fields
    chemical.received_date = _parse_date(data.get("received_date")) or chemical.received_date
    chemical.expiry_date = _parse_date(data.get("expiry_date"))
    chemical.opened_date = _parse_date(data.get("opened_date"))

    # Text fields
    chemical.name = data.get("name")
    chemical.cas_number = data.get("cas_number")
    chemical.formula = data.get("formula")
    chemical.manufacturer = data.get("manufacturer")
    chemical.supplier = data.get("supplier")
    chemical.catalog_number = data.get("catalog_number")
    chemical.lot_number = data.get("lot_number")
    chemical.grade = data.get("grade")
    chemical.unit = data.get("unit", "mL")
    chemical.storage_location = data.get("storage_location")
    chemical.storage_conditions = data.get("storage_conditions")
    chemical.hazard_class = data.get("hazard_class")
    chemical.lab_type = data.get("lab_type", "all")
    chemical.category = data.get("category", "other")
    chemical.notes = data.get("notes")
    # GHS & Safety fields
    chemical.ghs_pictograms = data.get("ghs_pictograms") or []
    chemical.ghs_signal_word = data.get("ghs_signal_word") or None
    chemical.sds_version = data.get("sds_version") or None
    chemical.sds_revision_date = _parse_date(data.get("sds_revision_date"))
    if data.get("shelf_life_after_opening_days"):
        chemical.shelf_life_after_opening_days = int(data["shelf_life_after_opening_days"])
    else:
        chemical.shelf_life_after_opening_days = None
    if data.get("days_alert_before_expiry"):
        chemical.days_alert_before_expiry = int(data["days_alert_before_expiry"])
    else:
        chemical.days_alert_before_expiry = 30
    chemical.prevent_use_if_expired = bool(data.get("prevent_use_if_expired"))

    if data.get("reorder_level"):
        chemical.reorder_level = float(data["reorder_level"])
    else:
        chemical.reorder_level = None

    # Quantity change -> separate log
    new_quantity = float(data.get("quantity", 0) or 0)
    if new_quantity != old_quantity:
        chemical.quantity = new_quantity
        create_chemical_log(
            chemical.id, user_id, 'adjusted',
            quantity_change=new_quantity - old_quantity,
            quantity_before=old_quantity,
            quantity_after=new_quantity,
            details=str(_l("Тоо хэмжээ засварлав"))
        )

    chemical.update_status()

    create_chemical_log(
        chemical.id, user_id, 'updated',
        details=str(_l("Мэдээлэл шинэчлэв"))
    )


def receive_stock(chemical: Chemical, quantity_add: float, user_id: int,
                  lot_number: Optional[str] = None,
                  expiry_date_str: Optional[str] = None) -> tuple[bool, str]:
    """Нөөц нэмэх (receive).

    Returns:
        (success, message)

    Note:
        Caller must commit the session.
    """
    if quantity_add <= 0:
        return False, _l("Тоо хэмжээ эерэг тоо байх ёстой.")

    old_quantity = chemical.quantity
    chemical.quantity += quantity_add
    new_quantity = chemical.quantity

    if lot_number:
        chemical.lot_number = lot_number
    if expiry_date_str:
        chemical.expiry_date = _parse_date(expiry_date_str)

    chemical.received_date = date.today()
    chemical.update_status()

    create_chemical_log(
        chemical.id, user_id, 'received',
        quantity_change=quantity_add,
        quantity_before=old_quantity,
        quantity_after=new_quantity,
        details=f"Нөөц нэмэв: +{quantity_add} {chemical.unit}"
    )

    return True, f"+{quantity_add} {chemical.unit} нэмэгдлээ."


def consume_chemical_stock(chemical: Chemical, quantity_used: float,
                           user_id: int, purpose: str = "",
                           analysis_code: Optional[str] = None,
                           sample_id: Optional[int] = None) -> ConsumeResult:
    """Хэрэглээ бүртгэх (consume).

    Creates ChemicalUsage + ChemicalLog records.

    Note:
        Caller must commit the session.
    """
    if quantity_used <= 0:
        return ConsumeResult(success=False, error=_l("Тоо хэмжээ эерэг тоо байх ёстой."))

    if quantity_used > chemical.quantity:
        return ConsumeResult(
            success=False,
            error=f"Insufficient stock. Available: {chemical.quantity} {chemical.unit}"
        )

    old_quantity = chemical.quantity
    chemical.quantity -= quantity_used
    new_quantity = chemical.quantity

    usage = ChemicalUsage(
        chemical_id=chemical.id,
        quantity_used=quantity_used,
        unit=chemical.unit,
        purpose=purpose,
        analysis_code=analysis_code,
        used_by_id=user_id,
        quantity_before=old_quantity,
        quantity_after=new_quantity,
    )

    if sample_id is not None:
        usage.sample_id = sample_id

    db.session.add(usage)

    if not chemical.opened_date:
        chemical.opened_date = date.today()

    chemical.update_status()

    create_chemical_log(
        chemical.id, user_id, 'consumed',
        quantity_change=-quantity_used,
        quantity_before=old_quantity,
        quantity_after=new_quantity,
        details=purpose or f"Хэрэглэв: -{quantity_used} {chemical.unit}"
    )

    return ConsumeResult(
        success=True,
        new_quantity=new_quantity,
        chemical_status=chemical.status,
    )


def consume_bulk(items: list[dict], user_id: int, purpose: str = "",
                 analysis_code: Optional[str] = None,
                 sample_id: Optional[int] = None) -> BulkConsumeResult:
    """Олон химийн бодис нэг дор хэрэглээ бүртгэх.

    Note:
        Caller must commit the session.
    """
    if not items:
        return BulkConsumeResult(success=False, error="No items provided")

    if len(items) > 100:
        return BulkConsumeResult(success=False, error=_l("Нэг удаад 100-аас ихийг зарцуулах боломжгүй"))

    count = 0
    errors = []

    for item in items:
        chemical_id = item.get("chemical_id")
        try:
            quantity_used = float(item.get("quantity_used", 0))
        except (ValueError, TypeError):
            continue

        if not chemical_id or quantity_used <= 0:
            continue

        chemical = db.session.get(Chemical, chemical_id)
        if not chemical:
            errors.append(f"Chemical {chemical_id} not found")
            continue

        if quantity_used > chemical.quantity:
            errors.append(f"{chemical.name}: insufficient stock")
            continue

        result = consume_chemical_stock(
            chemical=chemical,
            quantity_used=quantity_used,
            user_id=user_id,
            purpose=purpose,
            analysis_code=analysis_code,
            sample_id=sample_id,
        )

        if result.success:
            count += 1
        else:
            errors.append(result.error)

    return BulkConsumeResult(success=True, count=count, errors=errors)


def dispose_chemical(chemical: Chemical, user_id: int,
                     reason: str = _l("Устгав")) -> None:
    """Химийн бодис устгах (dispose).

    Note:
        Caller must commit the session.
    """
    old_quantity = chemical.quantity
    chemical.status = 'disposed'
    chemical.quantity = 0

    create_chemical_log(
        chemical.id, user_id, 'disposed',
        quantity_change=-old_quantity,
        quantity_before=old_quantity,
        quantity_after=0,
        details=f"Устгав: {reason}"
    )


# =============================================================================
# Helpers
# =============================================================================

def _parse_date(date_str: Optional[str]) -> Optional[date]:
    """Parse YYYY-MM-DD string to date, return None on empty/invalid."""
    if not date_str:
        return None
    return datetime.strptime(date_str, "%Y-%m-%d").date()


# =============================================================================
# Lot-based Result Invalidation
# =============================================================================

@dataclass
class LotInvalidationResult:
    """Lot invalidation operation result."""
    lot_id: int
    lot_name: str
    affected_result_ids: list
    affected_sample_ids: list
    flagged_count: int
    errors: list = field(default_factory=list)


@transactional()
def invalidate_results_by_lot(
    lot_id: int,
    reason: str = _l('Урвалжийн lot дохиолол — дахин шинжилгээ шаардлагатай'),
    performed_by_id: Optional[int] = None,
) -> LotInvalidationResult:
    """
    Тодорхой chemical lot ашигласан бүх AnalysisResult-ийг reanalysis руу шилжүүлэх.

    Атомик transaction: status update + audit log нэг unit-ээр. Алдаа гарвал
    @transactional rollback хийнэ.

    Тохиолдол: дохиолсон lot, чанарт үл нийцэх lot гэх мэт.

    Args:
        lot_id:           Chemical.id (дохиологдох lot)
        reason:           Буцаалтын шалтгаан (audit log-д бичигдэнэ)
        performed_by_id:  Үйлдэл хийсэн хэрэглэгч (User.id)

    Returns:
        LotInvalidationResult — хэдэн үр дүн нөлөөлсөн, алдаа
    """
    from app.models import AnalysisResult, Sample

    chemical = db.session.get(Chemical, lot_id)
    if not chemical:
        return LotInvalidationResult(
            lot_id=lot_id, lot_name='?',
            affected_result_ids=[], affected_sample_ids=[],
            flagged_count=0,
            errors=[f'Chemical lot id={lot_id} олдсонгүй'],
        )

    # 1. Тухайн lot ашигласан бүх ChemicalUsage олох
    usages = ChemicalUsageRepository.get_for_lot(lot_id, with_sample=True)

    # 2. WorksheetRow-оор холбогдсон AnalysisResult-үүд
    #    (raw_data-д reagent_lot_id хадгалсан тохиолдол)
    try:
        from app.repositories import WorksheetRowRepository
        ws_rows = WorksheetRowRepository.get_for_lot_with_result(lot_id)
        ws_result_ids = {r.analysis_result_id for r in ws_rows}
    except Exception:
        ws_result_ids = set()

    # 3. Бүх нөлөөлсөн result ID-уудыг нэгтгэх
    usage_sample_ids = {u.sample_id for u in usages if u.sample_id}

    raw_lot_results = list(db.session.execute(
        select(AnalysisResult).where(
            AnalysisResult.raw_data.contains(f'"reagent_lot_id": {lot_id}')
        )
    ).scalars().all()) if usage_sample_ids else []
    raw_lot_result_ids = {r.id for r in raw_lot_results}

    all_result_ids = ws_result_ids | raw_lot_result_ids

    _approveable_statuses = [
        AnalysisResultStatus.APPROVED.value,
        AnalysisResultStatus.PENDING_REVIEW.value,
    ]

    # sample_id-аас AnalysisResult олох
    sample_results = []
    if usage_sample_ids:
        sample_results = list(db.session.execute(
            select(AnalysisResult).where(
                AnalysisResult.sample_id.in_(list(usage_sample_ids)),
                AnalysisResult.status.in_(_approveable_statuses),
            )
        ).scalars().all())
    direct_results = list(db.session.execute(
        select(AnalysisResult).where(
            AnalysisResult.id.in_(list(all_result_ids)),
            AnalysisResult.status.in_(_approveable_statuses),
        )
    ).scalars().all()) if all_result_ids else []

    # Давхардал арилгах
    combined = {r.id: r for r in sample_results + direct_results}
    affected_results = list(combined.values())

    affected_ids = []
    affected_sample_ids_list = []
    errors = []

    for ar in affected_results:
        try:
            ar.status = AnalysisResultStatus.REANALYSIS.value
            ar.rejection_comment = reason
            if performed_by_id:
                ar.user_id = performed_by_id
            affected_ids.append(ar.id)
            if ar.sample_id not in affected_sample_ids_list:
                affected_sample_ids_list.append(ar.sample_id)
        except Exception as e:
            errors.append(f'Result id={ar.id}: {e}')

    # Audit log — @transactional нь commit-ыг хариуцна. Алдаа гарвал бүхэлд нь
    # rollback (status update + audit log нэг atomic unit).
    log = ChemicalLog(
        chemical_id=lot_id,
        action='lot_flagged',
        quantity_change=0,
        quantity_before=chemical.quantity,
        quantity_after=chemical.quantity,
        details=f'Lot дохиолол: {len(affected_ids)} үр дүн reanalysis болсон. Шалтгаан: {reason}',
        performed_by_id=performed_by_id,
    )
    log.set_hash()
    db.session.add(log)

    return LotInvalidationResult(
        lot_id=lot_id,
        lot_name=chemical.name,
        affected_result_ids=affected_ids,
        affected_sample_ids=affected_sample_ids_list,
        flagged_count=len(affected_ids),
        errors=errors,
    )


def get_expiring_soon_chemicals(lab_type: Optional[str] = None) -> list:
    """
    Удахгүй дуусах (days_alert_before_expiry хоног дотор) химийн бодисуудыг буцаана.

    Args:
        lab_type: 'water', 'coal', 'all' гэх мэт. None бол бүгдийг буцаана.

    Returns:
        list of Chemical objects
    """
    stmt = select(Chemical).where(
        Chemical.status.in_(['active', 'low_stock']),
        Chemical.expiry_date.isnot(None),
    )
    if lab_type:
        stmt = stmt.where(Chemical.lab_type.in_([lab_type, 'all']))
    chemicals = list(db.session.execute(stmt).scalars().all())
    return [c for c in chemicals if c.is_expiring_soon()]
