# app/tasks/sla_tasks.py
# -*- coding: utf-8 -*-
"""
SLA хяналтын scheduled tasks.

Celery Beat-аар тогтмол хугацаанд ажиллана.
"""

import logging
from celery import shared_task

logger = logging.getLogger(__name__)


@shared_task
def check_sla_overdue():
    """
    SLA хугацаа хэтэрсэн дээжүүдийг шалгаж, мэдэгдэл илгээх.

    Celery Beat: Өглөө 08:00, 14:00 бүр ажиллана.
    """
    from app.services.sla_service import get_sla_summary
    from app.tasks.email_tasks import send_sla_overdue_alert

    for lab_type in ("coal", "water", "microbiology"):
        summary = get_sla_summary(lab_type)
        if summary.overdue > 0:
            send_sla_overdue_alert.delay(lab_type)
            logger.info("SLA alert triggered: %s — %d overdue", lab_type, summary.overdue)


@shared_task
def auto_assign_sla():
    """
    SLA тохируулаагүй шинэ дээжүүдэд автоматаар SLA оноох.

    Celery Beat: 15 минут бүр ажиллана.
    """
    from app.services.sla_service import bulk_assign_sla

    total = 0
    for lab_type in ("coal", "water", "microbiology"):
        count = bulk_assign_sla(lab_type)
        total += count

    if total > 0:
        logger.info("Auto-assigned SLA to %d samples", total)

    return {"assigned": total}


@shared_task
def mark_completed_samples():
    """
    Бүх шинжилгээ approved болсон дээжүүдийг completed_at тэмдэглэх.

    Celery Beat: 10 минут бүр ажиллана.
    """
    from app import db
    from app.models import Sample, AnalysisResult
    from app.utils.datetime import now_local
    from sqlalchemy import func, and_

    # completed_at байхгүй, status='new'/'in_progress' дээжүүд
    candidates = Sample.query.filter(
        Sample.completed_at.is_(None),
        Sample.status.notin_(["archived", "completed"]),
    ).all()

    marked = 0
    for s in candidates:
        # Бүх result approved эсэх шалгах
        total = AnalysisResult.query.filter_by(sample_id=s.id).count()
        if total == 0:
            continue

        approved = AnalysisResult.query.filter_by(
            sample_id=s.id, status="approved"
        ).count()

        if approved == total:
            s.completed_at = now_local()
            s.status = "completed"
            marked += 1

    if marked > 0:
        db.session.commit()
        logger.info("Marked %d samples as completed", marked)

    return {"marked": marked}
