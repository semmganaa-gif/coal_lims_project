# app/logging_config.py
# -*- coding: utf-8 -*-
"""
Structured logging тохиргоо
"""

import logging
from logging.handlers import RotatingFileHandler
import os


def setup_logging(app):
    """
    Configure structured logging with multiple log files

    Creates three log files:
    - logs/app.log: General application logs
    - logs/audit.log: User actions and data changes
    - logs/security.log: Security events (failed logins, tampering, etc.)
    """
    # Create logs directory
    os.makedirs('logs', exist_ok=True)

    # ========================================================
    # 1) APPLICATION LOG
    # ========================================================
    if not app.logger.handlers:
        app_handler = RotatingFileHandler(
            app.config.get('APP_LOG_FILE', 'logs/app.log'),
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=5
        )
        app_handler.setLevel(logging.INFO)

        app_formatter = logging.Formatter(
            '[%(asctime)s] %(levelname)s in %(module)s: %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        app_handler.setFormatter(app_formatter)
        app.logger.addHandler(app_handler)
        app.logger.setLevel(logging.INFO)

    # ========================================================
    # 2) AUDIT LOG
    # ========================================================
    audit_logger = logging.getLogger('audit')
    audit_logger.setLevel(logging.INFO)

    if not audit_logger.handlers:
        audit_handler = RotatingFileHandler(
            'logs/audit.log',
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=10
        )
        audit_handler.setLevel(logging.INFO)

        audit_formatter = logging.Formatter(
            '[%(asctime)s] AUDIT %(levelname)s: %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        audit_handler.setFormatter(audit_formatter)
        audit_logger.addHandler(audit_handler)

    # ========================================================
    # 3) SECURITY LOG
    # ========================================================
    security_logger = logging.getLogger('security')
    security_logger.setLevel(logging.INFO)

    if not security_logger.handlers:
        security_handler = RotatingFileHandler(
            app.config.get('SECURITY_LOG_FILE', 'logs/security.log'),
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=10
        )
        security_handler.setLevel(logging.INFO)

        security_formatter = logging.Formatter(
            '%(asctime)s [SECURITY] %(levelname)s: %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        security_handler.setFormatter(security_formatter)
        security_logger.addHandler(security_handler)

    app.logger.info("Logging system initialized")

    return app


def get_audit_logger():
    """Get audit logger instance"""
    return logging.getLogger('audit')


def get_security_logger():
    """Get security logger instance"""
    return logging.getLogger('security')
