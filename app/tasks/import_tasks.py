# app/tasks/import_tasks.py
# -*- coding: utf-8 -*-
"""
CSV/Excel импорт background tasks.

Том файл (1000+ мөр) импортлоход 10-60 секунд зарцуулагддаг →
Celery worker-д шилжүүлнэ.
"""

import logging
from celery import shared_task

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=0, soft_time_limit=300, time_limit=600)
def import_csv_async(self, file_path, lab_type, user_id, options=None):
    """
    CSV/Excel файл background-д импортлох.

    Args:
        file_path: Серверт хадгалагдсан файлын зам
        lab_type: 'coal', 'water', 'microbiology'
        user_id: Импорт хийж буй хэрэглэгчийн ID
        options: dict — нэмэлт тохиргоо (dry_run, batch_size, ...)

    Returns:
        dict: {success, imported_count, errors, skipped}
    """
    options = options or {}

    try:
        from app.services.import_service import process_import_file

        result = process_import_file(
            file_path=file_path,
            lab_type=lab_type,
            user_id=user_id,
            dry_run=options.get("dry_run", False),
            batch_size=options.get("batch_size", 1000),
        )

        logger.info(
            "Import completed: %s — %d imported, %d errors",
            file_path, result.get("imported", 0), len(result.get("errors", [])),
        )
        return result

    except Exception as exc:
        logger.error("Import failed: %s — %s", file_path, exc)
        return {"success": False, "error": str(exc)}
