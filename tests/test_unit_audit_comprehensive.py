# tests/unit/test_audit_comprehensive.py
# -*- coding: utf-8 -*-
"""
Audit utility comprehensive tests
"""
import pytest


class TestGetRecentAuditLogs:
    """get_recent_audit_logs() функцийн тестүүд"""

    def test_returns_list(self, app, db):
        """Should return a list"""
        with app.app_context():
            from app.utils.audit import get_recent_audit_logs
            result = get_recent_audit_logs(limit=10)
            assert isinstance(result, list)

    def test_respects_limit(self, app, db):
        """Should respect limit parameter"""
        with app.app_context():
            from app.utils.audit import get_recent_audit_logs
            result = get_recent_audit_logs(limit=5)
            assert len(result) <= 5

    def test_returns_empty_list(self, app, db):
        """Should return empty list when no logs"""
        with app.app_context():
            from app.utils.audit import get_recent_audit_logs
            result = get_recent_audit_logs(limit=10, action='nonexistent_action_xyz')
            assert result == []


class TestGetUserAuditLogs:
    """get_user_audit_logs() функцийн тестүүд"""

    def test_returns_list(self, app, db):
        """Should return a list"""
        with app.app_context():
            from app.utils.audit import get_user_audit_logs
            result = get_user_audit_logs(user_id=999, limit=10)
            assert isinstance(result, list)

    def test_returns_empty_for_nonexistent_user(self, app, db):
        """Should return empty list for nonexistent user"""
        with app.app_context():
            from app.utils.audit import get_user_audit_logs
            result = get_user_audit_logs(user_id=99999, limit=10)
            assert result == []


class TestGetResourceAuditLogs:
    """get_resource_audit_logs() функцийн тестүүд"""

    def test_returns_list(self, app, db):
        """Should return a list"""
        with app.app_context():
            from app.utils.audit import get_resource_audit_logs
            result = get_resource_audit_logs(
                resource_type='Sample',
                resource_id=999,
                limit=10
            )
            assert isinstance(result, list)

    def test_returns_empty_for_nonexistent_resource(self, app, db):
        """Should return empty list for nonexistent resource"""
        with app.app_context():
            from app.utils.audit import get_resource_audit_logs
            result = get_resource_audit_logs(
                resource_type='NonexistentType',
                resource_id=99999,
                limit=10
            )
            assert result == []
