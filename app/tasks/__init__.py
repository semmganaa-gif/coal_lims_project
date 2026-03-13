# app/tasks/__init__.py
# -*- coding: utf-8 -*-
"""
Celery background tasks.

Modules:
  - email_tasks: Email илгээх (SMTP blocking → async)
  - report_tasks: PDF тайлан үүсгэх
  - import_tasks: CSV/Excel импорт
  - sla_tasks: SLA хяналт, notification
"""
