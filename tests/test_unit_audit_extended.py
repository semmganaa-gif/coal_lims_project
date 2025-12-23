# -*- coding: utf-8 -*-
"""
Audit utils extended тестүүд
"""
import pytest
from unittest.mock import patch, MagicMock


class TestAuditModule:
    """Audit module тестүүд"""

    def test_import_module(self):
        """Module import"""
        from app.utils import audit
        assert audit is not None


class TestLogAudit:
    """log_audit function тестүүд"""

    def test_import_function(self):
        """Function import"""
        from app.utils.audit import log_audit
        assert log_audit is not None
