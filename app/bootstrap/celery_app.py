# app/bootstrap/celery_app.py
# -*- coding: utf-8 -*-
"""
Celery application factory.

Flask app context-тэй интеграцлагдсан Celery instance үүсгэнэ.
Task-ууд Flask app context дотор ажиллана (db, config, mail бэлэн).

Usage:
    # celery_worker.py (root directory)
    from app.bootstrap.celery_app import celery_app

    # Start worker:
    celery -A celery_worker.celery_app worker --loglevel=info
"""

from celery import Celery, Task
from celery.schedules import crontab


def make_celery(app=None):
    """
    Flask app-тай холбогдсон Celery instance үүсгэх.

    Args:
        app: Flask application instance (None бол create_app() дуудна)

    Returns:
        Celery instance
    """

    class FlaskTask(Task):
        """Flask app context-д ажилладаг Celery task."""

        def __call__(self, *args, **kwargs):
            with _app.app_context():
                return self.run(*args, **kwargs)

    if app is None:
        from app import create_app
        app = create_app()

    _app = app

    celery = Celery(
        app.import_name,
        task_cls=FlaskTask,
    )

    # Flask config-оос Celery тохиргоо авах
    celery.conf.update(
        broker_url=app.config.get("CELERY_BROKER_URL", "redis://localhost:6379/1"),
        result_backend=app.config.get("CELERY_RESULT_BACKEND", "redis://localhost:6379/2"),
        task_serializer="json",
        result_serializer="json",
        accept_content=["json"],
        timezone=app.config.get("CELERY_TIMEZONE", "Asia/Ulaanbaatar"),
        enable_utc=False,
        # Task-ийн хугацаа
        task_soft_time_limit=300,   # 5 мин soft limit
        task_time_limit=600,        # 10 мин hard limit
        # Retry тохиргоо
        task_acks_late=True,
        worker_prefetch_multiplier=1,
        # Result хугацаа
        result_expires=3600,  # 1 цаг
        # Task discovery
        task_routes={
            "app.tasks.email_tasks.*": {"queue": "email"},
            "app.tasks.report_tasks.*": {"queue": "reports"},
            "app.tasks.import_tasks.*": {"queue": "imports"},
            "app.tasks.sla_tasks.*": {"queue": "default"},
        },
        # Celery Beat schedule (periodic tasks)
        beat_schedule={
            "check-sla-overdue-morning": {
                "task": "app.tasks.sla_tasks.check_sla_overdue",
                "schedule": crontab(hour=8, minute=0),
            },
            "check-sla-overdue-afternoon": {
                "task": "app.tasks.sla_tasks.check_sla_overdue",
                "schedule": crontab(hour=14, minute=0),
            },
            "auto-assign-sla": {
                "task": "app.tasks.sla_tasks.auto_assign_sla",
                "schedule": 900.0,  # 15 минут бүр
            },
            "mark-completed-samples": {
                "task": "app.tasks.sla_tasks.mark_completed_samples",
                "schedule": 600.0,  # 10 минут бүр
            },
            "scan-instrument-dirs": {
                "task": "app.tasks.instrument_tasks.scan_instrument_dirs",
                "schedule": 60.0,  # 1 минут бүр
            },
        },
    )

    # Auto-discover tasks
    celery.autodiscover_tasks(["app.tasks"])

    return celery


# Module-level Celery instance (lazy — worker эхлэхэд Flask app үүснэ)
celery_app = make_celery()
