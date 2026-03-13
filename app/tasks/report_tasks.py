# app/tasks/report_tasks.py
# -*- coding: utf-8 -*-
"""
Тайлан үүсгэх background tasks.

PDF/Excel тайлан generate хийхэд 5-30 секунд зарцуулагддаг →
Celery worker-д шилжүүлнэ.
"""

import logging
from celery import shared_task

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=1, soft_time_limit=120, time_limit=180)
def generate_report_async(self, report_type, params):
    """
    PDF тайлан background-д үүсгэх.

    Args:
        report_type: 'analysis', 'summary', 'monthly', 'consumption'
        params: dict — report-д шаардлагатай параметрүүд

    Returns:
        dict: {success, file_path or error}
    """
    try:
        if report_type == "monthly":
            from app.routes.reports.monthly_plan import _generate_monthly_report
            result = _generate_monthly_report(**params)
        elif report_type == "consumption":
            from app.routes.reports.consumption import _generate_consumption_report
            result = _generate_consumption_report(**params)
        else:
            return {"success": False, "error": f"Unknown report type: {report_type}"}

        logger.info("Report generated: %s", report_type)
        return {"success": True, "data": result}

    except Exception as exc:
        logger.error("Report generation failed: %s — %s", report_type, exc)
        return {"success": False, "error": str(exc)}
