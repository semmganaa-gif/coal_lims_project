# celery_worker.py
"""
Celery worker entry point.

Start worker:
    celery -A celery_worker.celery_app worker --loglevel=info

Start beat (scheduler):
    celery -A celery_worker.celery_app beat --loglevel=info

Start both (dev):
    celery -A celery_worker.celery_app worker --beat --loglevel=info
"""

from app.bootstrap.celery_app import celery_app  # noqa: F401
