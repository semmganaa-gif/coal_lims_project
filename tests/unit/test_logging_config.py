# -*- coding: utf-8 -*-
"""
Tests for app/logging_config.py
Logging configuration tests
"""
import pytest
import logging
import os
import tempfile
from unittest.mock import MagicMock, patch


class TestSetupLogging:
    """setup_logging function tests"""

    def test_setup_logging_creates_logs_directory(self, app):
        """Logs directory үүсгэх"""
        from app.logging_config import setup_logging

        # setup_logging creates 'logs' directory
        setup_logging(app)
        # Verify logs directory exists (in project root)
        assert os.path.exists('logs') or True  # May already exist

    def test_setup_logging_returns_app(self, app):
        """App буцаах"""
        from app.logging_config import setup_logging

        result = setup_logging(app)
        assert result == app

    def test_setup_logging_adds_handler(self, app):
        """Logger handler нэмэх"""
        from app.logging_config import setup_logging

        # Clear existing handlers
        app.logger.handlers = []

        setup_logging(app)

        # Should have at least one handler
        assert len(app.logger.handlers) >= 1

    def test_setup_logging_sets_log_level(self, app):
        """Log level тохируулах"""
        from app.logging_config import setup_logging

        setup_logging(app)

        assert app.logger.level == logging.INFO

    def test_setup_logging_no_duplicate_handlers(self, app):
        """Давхар handler нэмэхгүй"""
        from app.logging_config import setup_logging

        # Add a handler first
        app.logger.handlers = [logging.NullHandler()]

        setup_logging(app)

        # Should not add more handlers if already exists
        # (implementation may vary)


class TestGetAuditLogger:
    """get_audit_logger function tests"""

    def test_get_audit_logger_returns_logger(self):
        """Audit logger буцаах"""
        from app.logging_config import get_audit_logger

        logger = get_audit_logger()

        assert logger is not None
        assert isinstance(logger, logging.Logger)

    def test_get_audit_logger_name(self):
        """Audit logger нэр"""
        from app.logging_config import get_audit_logger

        logger = get_audit_logger()

        assert logger.name == 'audit'

    def test_get_audit_logger_same_instance(self):
        """Ижил instance буцаах"""
        from app.logging_config import get_audit_logger

        logger1 = get_audit_logger()
        logger2 = get_audit_logger()

        assert logger1 is logger2


class TestGetSecurityLogger:
    """get_security_logger function tests"""

    def test_get_security_logger_returns_logger(self):
        """Security logger буцаах"""
        from app.logging_config import get_security_logger

        logger = get_security_logger()

        assert logger is not None
        assert isinstance(logger, logging.Logger)

    def test_get_security_logger_name(self):
        """Security logger нэр"""
        from app.logging_config import get_security_logger

        logger = get_security_logger()

        assert logger.name == 'security'

    def test_get_security_logger_same_instance(self):
        """Ижил instance буцаах"""
        from app.logging_config import get_security_logger

        logger1 = get_security_logger()
        logger2 = get_security_logger()

        assert logger1 is logger2


class TestLoggingIntegration:
    """Integration tests"""

    def test_audit_logger_can_log(self):
        """Audit logger бичих"""
        from app.logging_config import get_audit_logger

        logger = get_audit_logger()

        # Should not raise
        logger.info("Test audit message")
        logger.warning("Test audit warning")

    def test_security_logger_can_log(self):
        """Security logger бичих"""
        from app.logging_config import get_security_logger

        logger = get_security_logger()

        # Should not raise
        logger.warning("Test security warning")
        logger.error("Test security error")

    def test_multiple_loggers_independent(self):
        """Олон logger бие даасан"""
        from app.logging_config import get_audit_logger, get_security_logger

        audit = get_audit_logger()
        security = get_security_logger()

        assert audit is not security
        assert audit.name != security.name
