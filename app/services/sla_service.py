# app/services/sla_service.py
# -*- coding: utf-8 -*-
"""
SLA (Service Level Agreement) turnaround tracking бизнес логик.

Дээжний хүлээн авснаас хариу өгөх хүртэлх хугацааг хянах.
"""

import json
import logging
from dataclasses import dataclass, field
from datetime import timedelta

from sqlalchemy import and_, func, case

from app import db
from app.models import Sample, AnalysisResult, SystemSetting
from app.utils.datetime import now_local
from app.utils.transaction import transactional

logger = logging.getLogger(__name__)

# Client бүрийн default SLA (цагаар) — DB-д тохиргоо байхгүй бол ашиглана
DEFAULT_SLA_HOURS = {
    "CHPP": 72,       # 3 хоног
    "UHG-Geo": 120,   # 5 хоног
    "BN-Geo": 120,    # 5 хоног
    "QC": 48,          # 2 хоног (QC дээж яаралтай)
    "WTL": 72,         # 3 хоног
    "Proc": 72,        # 3 хоног
    "LAB": 48,         # 2 хоног
}
DEFAULT_SLA_FALLBACK = 72  # Бусад бүх client-д 3 хоног

SLA_CONFIG_CATEGORY = "sla_config"


# ---------------------------------------------------------------------------
# SLA тохиргоо (DB-based, category='sla_config')
# key формат: "CHPP" (client default) эсвэл "CHPP:2 hourly" (client+type)
# value: цагаар (жишээ: "72")
# ---------------------------------------------------------------------------

def get_sla_config_all() -> list[dict]:
    """DB-д хадгалагдсан бүх SLA тохиргоог буцаах."""
    settings = SystemSetting.query.filter_by(
        category=SLA_CONFIG_CATEGORY, is_active=True
    ).order_by(SystemSetting.sort_order, SystemSetting.key).all()

    result = []
    for s in settings:
        parts = s.key.split(":", 1)
        result.append({
            "id": s.id,
            "client_name": parts[0],
            "sample_type": parts[1] if len(parts) > 1 else "",
            "hours": int(s.value),
            "description": s.description or "",
        })
    return result


@transactional()
def set_sla_config(client_name: str, sample_type: str, hours: int,
                   description: str = "", user_id: int = None) -> SystemSetting:
    """SLA тохиргоо хадгалах (upsert)."""
    key = f"{client_name}:{sample_type}" if sample_type else client_name
    setting = SystemSetting.query.filter_by(
        category=SLA_CONFIG_CATEGORY, key=key
    ).first()

    if setting:
        setting.value = str(hours)
        setting.description = description
        if user_id:
            setting.updated_by_id = user_id
    else:
        setting = SystemSetting(
            category=SLA_CONFIG_CATEGORY,
            key=key,
            value=str(hours),
            description=description,
            is_active=True,
            updated_by_id=user_id,
        )
        db.session.add(setting)
    return setting


@transactional()
def delete_sla_config(config_id: int) -> bool:
    """SLA тохиргоо устгах."""
    setting = SystemSetting.query.filter_by(
        id=config_id, category=SLA_CONFIG_CATEGORY
    ).first()
    if not setting:
        return False
    db.session.delete(setting)
    return True


@dataclass
class SLASummary:
    """SLA dashboard summary."""
    overdue: int = 0          # Хугацаа хэтэрсэн
    due_soon: int = 0         # 24 цагийн дотор дуусна
    on_track: int = 0         # Хугацаандаа байгаа
    no_sla: int = 0           # SLA тохируулаагүй
    avg_turnaround_hours: float = 0.0  # Дундаж turnaround (энэ сар)
    completed_on_time: int = 0  # Хугацаандаа дуусгасан (энэ сар)
    completed_late: int = 0     # Хоцорсон (энэ сар)


@dataclass
class OverdueSample:
    """Хугацаа хэтэрсэн дээжний мэдээлэл."""
    id: int
    sample_code: str
    client_name: str
    lab_type: str
    received_date: str
    due_date: str
    overdue_hours: float
    priority: str
    pending_analyses: int


# ---------------------------------------------------------------------------
# SLA тооцоолол
# ---------------------------------------------------------------------------

def get_default_sla_hours(client_name: str, sample_type: str = None) -> int:
    """
    Client + sample_type-ийн SLA цаг.

    Хайлтын дараалал:
      1. DB: sla_config / "CHPP:2 hourly" (client+type)
      2. DB: sla_config / "CHPP"           (client default)
      3. Hardcoded DEFAULT_SLA_HOURS
      4. DEFAULT_SLA_FALLBACK (72)
    """
    # 1) client+type тусгай тохиргоо
    if sample_type:
        specific = SystemSetting.query.filter_by(
            category=SLA_CONFIG_CATEGORY,
            key=f"{client_name}:{sample_type}",
            is_active=True,
        ).first()
        if specific:
            try:
                return int(specific.value)
            except (ValueError, TypeError):
                pass

    # 2) client default
    client_default = SystemSetting.query.filter_by(
        category=SLA_CONFIG_CATEGORY,
        key=client_name,
        is_active=True,
    ).first()
    if client_default:
        try:
            return int(client_default.value)
        except (ValueError, TypeError):
            pass

    # 3) Hardcoded fallback
    return DEFAULT_SLA_HOURS.get(client_name, DEFAULT_SLA_FALLBACK)


def assign_sla(sample: Sample) -> None:
    """
    Дээжинд SLA тохируулах (received_date + sla_hours → due_date).

    Хэрэв sla_hours тохируулаагүй бол client_name + sample_type-аас default авна.
    """
    if not sample.received_date:
        return

    if not sample.sla_hours:
        sample.sla_hours = get_default_sla_hours(
            sample.client_name or "", sample.sample_type
        )

    sample.due_date = sample.received_date + timedelta(hours=sample.sla_hours)


def mark_completed(sample: Sample) -> None:
    """Дээжийг дуусгах (бүх шинжилгээ approved)."""
    sample.completed_at = now_local()


@transactional()
def set_sample_sla(sample_id: int, sla_hours: int | None,
                   priority: str | None) -> Sample | None:
    """Нэг дээжийн SLA тохируулах: sla_hours, priority шинэчилж due_date тооцох.

    Returns:
        Sample object on success, None if not found.
    """
    sample = db.session.get(Sample, sample_id)
    if not sample:
        return None
    if sla_hours is not None:
        sample.sla_hours = int(sla_hours)
    if priority in ("normal", "urgent", "rush"):
        sample.priority = priority
    assign_sla(sample)
    return sample


# ---------------------------------------------------------------------------
# SLA summary (dashboard)
# ---------------------------------------------------------------------------

def _now_naive():
    """now_local() timezone-гүй болгож буцаах (DB datetime-тай харьцуулахад)."""
    return now_local().replace(tzinfo=None)


def get_sla_summary(lab_type: str = "coal") -> SLASummary:
    """
    SLA dashboard-ийн нэгдсэн статистик.

    Args:
        lab_type: Лабын төрөл

    Returns:
        SLASummary объект
    """
    now = _now_naive()
    soon_threshold = now + timedelta(hours=24)
    first_of_month = now.date().replace(day=1)

    # Active (archived/completed биш) дээжүүд
    active = Sample.query.filter(
        Sample.lab_type == lab_type,
        Sample.status.notin_(["archived", "completed"]),
    )

    # due_date тохируулсан дээжүүд
    with_sla = active.filter(Sample.due_date.isnot(None))

    overdue = with_sla.filter(Sample.due_date < now).count()
    due_soon = with_sla.filter(
        and_(Sample.due_date >= now, Sample.due_date <= soon_threshold)
    ).count()
    on_track = with_sla.filter(Sample.due_date > soon_threshold).count()
    no_sla = active.filter(Sample.due_date.is_(None)).count()

    # Энэ сарын дуусгасан дээжүүдийн turnaround
    completed_this_month = Sample.query.filter(
        Sample.lab_type == lab_type,
        Sample.completed_at.isnot(None),
        Sample.completed_at >= first_of_month,
        Sample.received_date.isnot(None),
    ).all()

    turnaround_hours = []
    completed_on_time = 0
    completed_late = 0

    for s in completed_this_month:
        hours = (s.completed_at - s.received_date).total_seconds() / 3600
        turnaround_hours.append(hours)
        if s.due_date and s.completed_at <= s.due_date:
            completed_on_time += 1
        elif s.due_date:
            completed_late += 1

    avg_hours = round(sum(turnaround_hours) / len(turnaround_hours), 1) if turnaround_hours else 0.0

    return SLASummary(
        overdue=overdue,
        due_soon=due_soon,
        on_track=on_track,
        no_sla=no_sla,
        avg_turnaround_hours=avg_hours,
        completed_on_time=completed_on_time,
        completed_late=completed_late,
    )


# ---------------------------------------------------------------------------
# Overdue дэлгэрэнгүй
# ---------------------------------------------------------------------------

def get_overdue_samples(lab_type: str = "coal", limit: int = 100) -> list[OverdueSample]:
    """
    Хугацаа хэтэрсэн дээжний жагсаалт (ноцтойгоор эрэмбэлсэн).

    Args:
        lab_type: Лабын төрөл
        limit: Дээд тоо

    Returns:
        OverdueSample жагсаалт
    """
    now = _now_naive()

    samples = (
        Sample.query
        .filter(
            Sample.lab_type == lab_type,
            Sample.status.notin_(["archived", "completed"]),
            Sample.due_date.isnot(None),
            Sample.due_date < now,
        )
        .order_by(Sample.due_date.asc())  # Хамгийн удаан хэтэрсэн нь эхэнд
        .limit(limit)
        .all()
    )

    result = []
    for s in samples:
        # Pending шинжилгээний тоо
        pending = AnalysisResult.query.filter(
            AnalysisResult.sample_id == s.id,
            AnalysisResult.status.in_(["pending_review", "rejected"]),
        ).count()

        overdue_hours = (now - s.due_date).total_seconds() / 3600

        result.append(OverdueSample(
            id=s.id,
            sample_code=s.sample_code or "",
            client_name=s.client_name or "",
            lab_type=s.lab_type or "",
            received_date=s.received_date.strftime("%Y-%m-%d %H:%M") if s.received_date else "",
            due_date=s.due_date.strftime("%Y-%m-%d %H:%M") if s.due_date else "",
            overdue_hours=round(overdue_hours, 1),
            priority=s.priority or "normal",
            pending_analyses=pending,
        ))

    return result


# ---------------------------------------------------------------------------
# Due soon дэлгэрэнгүй
# ---------------------------------------------------------------------------

def get_due_soon_samples(
    lab_type: str = "coal", hours: int = 24, limit: int = 100
) -> list[dict]:
    """
    Удахгүй хугацаа дуусах дээжүүд.

    Args:
        lab_type: Лабын төрөл
        hours: Хэдэн цагийн дотор
        limit: Дээд тоо

    Returns:
        Dict жагсаалт
    """
    now = _now_naive()
    threshold = now + timedelta(hours=hours)

    samples = (
        Sample.query
        .filter(
            Sample.lab_type == lab_type,
            Sample.status.notin_(["archived", "completed"]),
            Sample.due_date.isnot(None),
            Sample.due_date >= now,
            Sample.due_date <= threshold,
        )
        .order_by(Sample.due_date.asc())
        .limit(limit)
        .all()
    )

    return [
        {
            "id": s.id,
            "sample_code": s.sample_code or "",
            "client_name": s.client_name or "",
            "due_date": s.due_date.strftime("%Y-%m-%d %H:%M") if s.due_date else "",
            "hours_remaining": round((s.due_date - now).total_seconds() / 3600, 1),
            "priority": s.priority or "normal",
        }
        for s in samples
    ]


# ---------------------------------------------------------------------------
# On track дэлгэрэнгүй
# ---------------------------------------------------------------------------

def get_on_track_samples(
    lab_type: str = "coal", limit: int = 100
) -> list[dict]:
    """Хугацаандаа байгаа (due_date > now + 24h) дээжүүд."""
    now = _now_naive()
    threshold = now + timedelta(hours=24)

    samples = (
        Sample.query
        .filter(
            Sample.lab_type == lab_type,
            Sample.status.notin_(["archived", "completed"]),
            Sample.due_date.isnot(None),
            Sample.due_date > threshold,
        )
        .order_by(Sample.due_date.asc())
        .limit(limit)
        .all()
    )

    return [
        {
            "id": s.id,
            "sample_code": s.sample_code or "",
            "client_name": s.client_name or "",
            "due_date": s.due_date.strftime("%Y-%m-%d %H:%M") if s.due_date else "",
            "hours_remaining": round((s.due_date - now).total_seconds() / 3600, 1),
            "priority": s.priority or "normal",
        }
        for s in samples
    ]


# ---------------------------------------------------------------------------
# Bulk SLA assign (одоо байгаа дээжүүдэд SLA тохируулах)
# ---------------------------------------------------------------------------

@transactional()
def bulk_assign_sla(lab_type: str = "coal") -> int:
    """
    due_date байхгүй active дээжүүдэд SLA автоматаар тохируулах (атомик).

    Returns:
        Шинэчилсэн дээжний тоо
    """
    samples = Sample.query.filter(
        Sample.lab_type == lab_type,
        Sample.status.notin_(["archived", "completed"]),
        Sample.due_date.is_(None),
        Sample.received_date.isnot(None),
    ).all()

    count = 0
    for s in samples:
        assign_sla(s)
        count += 1
    if count > 0:
        logger.info("Bulk SLA assigned: %d samples", count)
    return count
