# -*- coding: utf-8 -*-
"""
Tests for app/utils/audit.py
Audit logging utility tests
"""
import pytest
from unittest.mock import patch, MagicMock


class TestLogAudit:
    """log_audit function tests"""

    def test_import(self):
        """Import function"""
        from app.utils.audit import log_audit
        assert callable(log_audit)

    def test_basic_log(self, app):
        """Basic log without details"""
        from app.utils.audit import log_audit
        from app import db

        with app.test_request_context():
            with patch.object(db.session, 'add') as mock_add:
                with patch.object(db.session, 'commit') as mock_commit:
                    log_audit('test_action')
                    mock_add.assert_called_once()

    def test_log_with_resource(self, app):
        """Log with resource info"""
        from app.utils.audit import log_audit
        from app import db

        with app.test_request_context():
            with patch.object(db.session, 'add') as mock_add:
                with patch.object(db.session, 'commit'):
                    log_audit('delete', resource_type='Sample', resource_id=123)
                    mock_add.assert_called_once()
                    # Check the AuditLog was created with correct params
                    call_args = mock_add.call_args[0][0]
                    assert call_args.resource_type == 'Sample'
                    assert call_args.resource_id == 123

    def test_log_with_details(self, app):
        """Log with details dict"""
        from app.utils.audit import log_audit
        from app import db
        import json

        with app.test_request_context():
            with patch.object(db.session, 'add') as mock_add:
                with patch.object(db.session, 'commit'):
                    log_audit('update', details={'key': 'value'})
                    call_args = mock_add.call_args[0][0]
                    assert call_args.details is not None
                    details = json.loads(call_args.details)
                    assert details['key'] == 'value'

    def test_anonymous_user(self, app):
        """Log with anonymous user"""
        from app.utils.audit import log_audit
        from app import db

        with app.test_request_context():
            with patch.object(db.session, 'add') as mock_add:
                with patch.object(db.session, 'commit'):
                    log_audit('anonymous_action')
                    call_args = mock_add.call_args[0][0]
                    assert call_args.user_id is None

    def test_db_commit_called(self, app):
        """DB commit is called"""
        from app.utils.audit import log_audit
        from app import db

        with app.test_request_context():
            with patch.object(db.session, 'add'):
                with patch.object(db.session, 'commit') as mock_commit:
                    log_audit('test_action')
                    mock_commit.assert_called_once()

    def test_db_error_raises_after_rollback(self, app):
        """ISO 17025: audit DB failure must not be silent — rollback then raise."""
        from app.utils.audit import log_audit
        from app import db
        from sqlalchemy.exc import SQLAlchemyError

        with app.test_request_context():
            with patch.object(db.session, 'add'):
                with patch.object(db.session, 'commit', side_effect=SQLAlchemyError("DB Error")):
                    with patch.object(db.session, 'rollback') as mock_rollback:
                        with pytest.raises(SQLAlchemyError):
                            log_audit('test_action')
                        mock_rollback.assert_called_once()

    def test_ip_address_captured(self, app):
        """IP address is captured from request"""
        from app.utils.audit import log_audit
        from app import db

        with app.test_request_context(environ_base={'REMOTE_ADDR': '192.168.1.1'}):
            with patch.object(db.session, 'add') as mock_add:
                with patch.object(db.session, 'commit'):
                    log_audit('test_action')
                    call_args = mock_add.call_args[0][0]
                    assert call_args.ip_address == '192.168.1.1'


class TestFileLoggers:
    """File-based audit/security logger тест (b94d34c — ISO 17025 retention)."""

    def test_audit_action_writes_to_audit_logger(self, app, caplog):
        """Бүх log_audit дуудлага 'audit' logger-д INFO record үүсгэх."""
        import logging
        from app.utils.audit import log_audit
        from app import db

        with app.test_request_context():
            with patch.object(db.session, 'add'):
                with patch.object(db.session, 'commit'):
                    with caplog.at_level(logging.INFO, logger='audit'):
                        log_audit('view_dashboard', resource_type='Sample', resource_id=42)

        audit_records = [r for r in caplog.records if r.name == 'audit']
        assert audit_records, "Audit logger record хүлээн авсангүй"
        msg = audit_records[-1].message
        assert 'action=view_dashboard' in msg
        assert 'resource=Sample#42' in msg

    def test_security_action_writes_to_both_loggers(self, app, caplog):
        """Security action ('login_success') нь audit + security хоёуланд бичигдэх."""
        import logging
        from app.utils.audit import log_audit
        from app import db

        with app.test_request_context():
            with patch.object(db.session, 'add'):
                with patch.object(db.session, 'commit'):
                    with caplog.at_level(logging.INFO):
                        log_audit('login_success')

        audit_msgs = [r.message for r in caplog.records if r.name == 'audit']
        security_msgs = [r.message for r in caplog.records if r.name == 'security']
        assert any('action=login_success' in m for m in audit_msgs)
        assert any('action=login_success' in m for m in security_msgs)

    def test_non_security_action_stays_out_of_security_logger(self, app, caplog):
        """Энгийн action ('view_dashboard') security.log-д бичигдэхгүй."""
        import logging
        from app.utils.audit import log_audit
        from app import db

        with app.test_request_context():
            with patch.object(db.session, 'add'):
                with patch.object(db.session, 'commit'):
                    with caplog.at_level(logging.INFO, logger='security'):
                        log_audit('view_dashboard')

        sec_records = [
            r for r in caplog.records
            if r.name == 'security' and 'action=view_dashboard' in r.message
        ]
        assert sec_records == []

    def test_file_logger_failure_does_not_break_main_flow(self, app):
        """File logger exception нь audit DB write-ийг блоклохгүй."""
        from app.utils.audit import log_audit
        from app import db

        with app.test_request_context():
            with patch.object(db.session, 'add') as mock_add:
                with patch.object(db.session, 'commit'):
                    with patch('app.utils.audit._audit_file_logger.info',
                               side_effect=OSError("disk full")):
                        # Алдаа throw хийхгүй байх ёстой
                        log_audit('test_action')
                        mock_add.assert_called_once()


class TestGetRecentAuditLogs:
    """get_recent_audit_logs function tests"""

    def test_import(self):
        """Import function"""
        from app.utils.audit import get_recent_audit_logs
        assert callable(get_recent_audit_logs)

    def test_signature(self):
        """Function accepts expected parameters"""
        from app.utils.audit import get_recent_audit_logs
        import inspect

        sig = inspect.signature(get_recent_audit_logs)
        params = list(sig.parameters.keys())
        assert 'limit' in params
        assert 'action' in params

    def test_default_parameters(self):
        """Default parameter values"""
        from app.utils.audit import get_recent_audit_logs
        import inspect

        sig = inspect.signature(get_recent_audit_logs)
        assert sig.parameters['limit'].default == 100
        assert sig.parameters['action'].default is None


class TestGetUserAuditLogs:
    """get_user_audit_logs function tests"""

    def test_import(self):
        """Import function"""
        from app.utils.audit import get_user_audit_logs
        assert callable(get_user_audit_logs)

    def test_signature(self):
        """Function accepts expected parameters"""
        from app.utils.audit import get_user_audit_logs
        import inspect

        sig = inspect.signature(get_user_audit_logs)
        params = list(sig.parameters.keys())
        assert 'user_id' in params
        assert 'limit' in params

    def test_default_limit(self):
        """Default limit is 100"""
        from app.utils.audit import get_user_audit_logs
        import inspect

        sig = inspect.signature(get_user_audit_logs)
        assert sig.parameters['limit'].default == 100


class TestGetResourceAuditLogs:
    """get_resource_audit_logs function tests"""

    def test_import(self):
        """Import function"""
        from app.utils.audit import get_resource_audit_logs
        assert callable(get_resource_audit_logs)

    def test_signature(self):
        """Function accepts expected parameters"""
        from app.utils.audit import get_resource_audit_logs
        import inspect

        sig = inspect.signature(get_resource_audit_logs)
        params = list(sig.parameters.keys())
        assert 'resource_type' in params
        assert 'resource_id' in params
        assert 'limit' in params

    def test_default_limit(self):
        """Default limit is 100"""
        from app.utils.audit import get_resource_audit_logs
        import inspect

        sig = inspect.signature(get_resource_audit_logs)
        assert sig.parameters['limit'].default == 100
