# tests/unit/test_decorators_audit_db.py
# -*- coding: utf-8 -*-
"""
Decorators, Audit, Database utilities тест
Coverage: decorators.py, audit.py, database.py
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from functools import wraps


# ========== Fixtures ==========

@pytest.fixture
def app():
    """Create test app"""
    from app import create_app
    app = create_app()
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False
    app.config['SERVER_NAME'] = 'localhost'

    with app.app_context():
        yield app


@pytest.fixture
def client(app):
    """Create test client"""
    return app.test_client()


# ========== TestRoleRequired ==========

class TestRoleRequired:
    """role_required decorator тестүүд"""

    def test_role_required_allows_matching_role(self, app):
        """Matching role should be allowed"""
        from app.utils.decorators import role_required

        with app.test_request_context():
            with patch('app.utils.decorators.current_user') as mock_user:
                mock_user.is_authenticated = True
                mock_user.role = 'admin'

                @role_required('admin', 'senior')
                def test_func():
                    return 'success'

                result = test_func()
                assert result == 'success'

    def test_role_required_denies_non_matching_role(self, app):
        """Non-matching role should be denied with 403"""
        from app.utils.decorators import role_required
        from werkzeug.exceptions import Forbidden

        with app.test_request_context():
            with patch('app.utils.decorators.current_user') as mock_user:
                mock_user.is_authenticated = True
                mock_user.role = 'chemist'

                @role_required('admin')
                def test_func():
                    return 'success'

                with pytest.raises(Forbidden):
                    test_func()

    def test_role_required_senior_role(self, app):
        """Senior role should work"""
        from app.utils.decorators import role_required

        with app.test_request_context():
            with patch('app.utils.decorators.current_user') as mock_user:
                mock_user.is_authenticated = True
                mock_user.role = 'senior'

                @role_required('senior', 'admin')
                def test_func():
                    return 'success'

                result = test_func()
                assert result == 'success'


# ========== TestAdminRequired ==========

class TestAdminRequired:
    """admin_required decorator тестүүд"""

    def test_admin_required_allows_admin(self, app):
        """Admin should be allowed"""
        from app.utils.decorators import admin_required

        with app.test_request_context():
            with patch('app.utils.decorators.current_user') as mock_user:
                mock_user.is_authenticated = True
                mock_user.role = 'admin'

                @admin_required
                def test_func():
                    return 'success'

                result = test_func()
                assert result == 'success'

    def test_admin_required_denies_non_admin(self, app):
        """Non-admin should be denied"""
        from app.utils.decorators import admin_required
        from werkzeug.exceptions import Forbidden

        with app.test_request_context():
            with patch('app.utils.decorators.current_user') as mock_user:
                mock_user.is_authenticated = True
                mock_user.role = 'senior'

                @admin_required
                def test_func():
                    return 'success'

                with pytest.raises(Forbidden):
                    test_func()


# ========== TestRoleOrOwnerRequired ==========

class TestRoleOrOwnerRequired:
    """role_or_owner_required decorator тестүүд"""

    def test_role_or_owner_allows_role(self, app):
        """Matching role should be allowed"""
        from app.utils.decorators import role_or_owner_required

        with app.test_request_context():
            with patch('app.utils.decorators.current_user') as mock_user:
                mock_user.is_authenticated = True
                mock_user.role = 'admin'

                @role_or_owner_required('admin', owner_check=lambda: False)
                def test_func():
                    return 'success'

                result = test_func()
                assert result == 'success'

    def test_role_or_owner_allows_owner(self, app):
        """Owner should be allowed even without role"""
        from app.utils.decorators import role_or_owner_required

        with app.test_request_context():
            with patch('app.utils.decorators.current_user') as mock_user:
                mock_user.is_authenticated = True
                mock_user.role = 'chemist'

                owner_check = lambda: True  # User is owner

                @role_or_owner_required('admin', owner_check=owner_check)
                def test_func():
                    return 'success'

                result = test_func()
                assert result == 'success'

    def test_role_or_owner_denies_non_owner_non_role(self, app):
        """Non-owner without role should be denied"""
        from app.utils.decorators import role_or_owner_required
        from werkzeug.exceptions import Forbidden

        with app.test_request_context():
            with patch('app.utils.decorators.current_user') as mock_user:
                mock_user.is_authenticated = True
                mock_user.role = 'chemist'

                owner_check = lambda: False  # User is not owner

                @role_or_owner_required('admin', owner_check=owner_check)
                def test_func():
                    return 'success'

                with pytest.raises(Forbidden):
                    test_func()


# ========== TestAnalysisRoleRequired ==========

class TestAnalysisRoleRequired:
    """analysis_role_required decorator тестүүд"""

    def test_analysis_role_default_roles(self, app):
        """Default roles should include chemist, senior, manager, admin, prep"""
        from app.utils.decorators import analysis_role_required

        with app.test_request_context():
            with patch('app.utils.decorators.current_user') as mock_user:
                mock_user.is_authenticated = True

                default_roles = ['chemist', 'senior', 'manager', 'admin', 'prep']
                for role in default_roles:
                    mock_user.role = role

                    @analysis_role_required()
                    def test_func():
                        return 'success'

                    result = test_func()
                    assert result == 'success'

    def test_analysis_role_custom_roles(self, app):
        """Custom roles should work"""
        from app.utils.decorators import analysis_role_required
        from werkzeug.exceptions import Forbidden

        with app.test_request_context():
            with patch('app.utils.decorators.current_user') as mock_user:
                mock_user.is_authenticated = True
                mock_user.role = 'chemist'

                @analysis_role_required(['admin'])
                def test_func():
                    return 'success'

                with pytest.raises(Forbidden):
                    test_func()


# ========== TestDatabaseHelpers ==========

class TestDatabaseHelpers:
    """Database helper functions тестүүд"""

    def test_safe_commit_success(self, app):
        """safe_commit should return True on success"""
        with app.test_request_context():
            with patch('app.utils.database.db') as mock_db:
                from app.utils.database import safe_commit

                result = safe_commit(success_msg="Success!")
                assert result is True
                mock_db.session.commit.assert_called_once()

    def test_safe_commit_integrity_error(self, app):
        """safe_commit should return False on IntegrityError"""
        from sqlalchemy.exc import IntegrityError

        with app.test_request_context():
            with patch('app.utils.database.db') as mock_db:
                mock_db.session.commit.side_effect = IntegrityError(None, None, None)

                from app.utils.database import safe_commit

                result = safe_commit(error_msg="Error!")
                assert result is False
                mock_db.session.rollback.assert_called_once()

    def test_safe_commit_general_exception(self, app):
        """safe_commit should return False on general exception"""
        with app.test_request_context():
            with patch('app.utils.database.db') as mock_db:
                from sqlalchemy.exc import SQLAlchemyError
                mock_db.session.commit.side_effect = SQLAlchemyError("DB error")

                from app.utils.database import safe_commit

                result = safe_commit()
                assert result is False
                mock_db.session.rollback.assert_called_once()

    def test_safe_delete_success(self, app):
        """safe_delete should return True on success"""
        with app.test_request_context():
            with patch('app.utils.database.db') as mock_db:
                from app.utils.database import safe_delete

                mock_obj = Mock()
                result = safe_delete(mock_obj, success_msg="Deleted!")
                assert result is True
                mock_db.session.delete.assert_called_with(mock_obj)
                mock_db.session.commit.assert_called_once()

    def test_safe_delete_error(self, app):
        """safe_delete should return False on error"""
        with app.test_request_context():
            with patch('app.utils.database.db') as mock_db:
                from sqlalchemy.exc import SQLAlchemyError
                mock_db.session.delete.side_effect = SQLAlchemyError("Delete error")

                from app.utils.database import safe_delete

                mock_obj = Mock()
                result = safe_delete(mock_obj)
                assert result is False
                mock_db.session.rollback.assert_called_once()

    def test_safe_add_single_object(self, app):
        """safe_add should add single object"""
        with app.test_request_context():
            with patch('app.utils.database.db') as mock_db:
                from app.utils.database import safe_add

                mock_obj = Mock()
                result = safe_add(mock_obj, success_msg="Added!")
                assert result is True
                mock_db.session.add.assert_called_with(mock_obj)
                mock_db.session.commit.assert_called_once()

    def test_safe_add_list_of_objects(self, app):
        """safe_add should add list of objects"""
        with app.test_request_context():
            with patch('app.utils.database.db') as mock_db:
                from app.utils.database import safe_add

                mock_objects = [Mock(), Mock()]
                result = safe_add(mock_objects)
                assert result is True
                mock_db.session.add_all.assert_called_with(mock_objects)

    def test_safe_add_integrity_error(self, app):
        """safe_add should return False on IntegrityError"""
        from sqlalchemy.exc import IntegrityError

        with app.test_request_context():
            with patch('app.utils.database.db') as mock_db:
                mock_db.session.add.side_effect = IntegrityError(None, None, None)

                from app.utils.database import safe_add

                mock_obj = Mock()
                result = safe_add(mock_obj)
                assert result is False


# ========== TestAuditFunctions ==========

class TestAuditFunctions:
    """Audit function тестүүд (mock-тэй)"""

    def test_log_audit_function_signature(self, app):
        """log_audit function should have correct signature"""
        from app.utils.audit import log_audit
        import inspect
        sig = inspect.signature(log_audit)
        params = list(sig.parameters.keys())
        assert 'action' in params
        assert 'resource_type' in params
        assert 'resource_id' in params
        assert 'details' in params

    def test_get_recent_audit_logs_function_exists(self, app):
        """get_recent_audit_logs function should exist"""
        from app.utils.audit import get_recent_audit_logs
        assert callable(get_recent_audit_logs)

    def test_get_user_audit_logs_function_exists(self, app):
        """get_user_audit_logs function should exist"""
        from app.utils.audit import get_user_audit_logs
        assert callable(get_user_audit_logs)

    def test_get_resource_audit_logs_function_exists(self, app):
        """get_resource_audit_logs function should exist"""
        from app.utils.audit import get_resource_audit_logs
        assert callable(get_resource_audit_logs)

    def test_audit_functions_have_docstrings(self, app):
        """Audit functions should have docstrings"""
        from app.utils.audit import (
            log_audit, get_recent_audit_logs,
            get_user_audit_logs, get_resource_audit_logs
        )
        assert log_audit.__doc__ is not None
        assert get_recent_audit_logs.__doc__ is not None
        assert get_user_audit_logs.__doc__ is not None
        assert get_resource_audit_logs.__doc__ is not None


# ========== TestDecoratorEdgeCases ==========

class TestDecoratorEdgeCases:
    """Decorator edge case тестүүд"""

    def test_role_required_with_multiple_allowed_roles(self, app):
        """Multiple allowed roles should work"""
        from app.utils.decorators import role_required

        with app.test_request_context():
            with patch('app.utils.decorators.current_user') as mock_user:
                mock_user.is_authenticated = True

                for role in ['chemist', 'senior', 'admin']:
                    mock_user.role = role

                    @role_required('chemist', 'senior', 'admin')
                    def test_func():
                        return f'success_{role}'

                    result = test_func()
                    assert result == f'success_{role}'

    def test_role_required_preserves_function_name(self, app):
        """Decorator should preserve function name"""
        from app.utils.decorators import role_required

        @role_required('admin')
        def my_special_function():
            pass

        assert my_special_function.__name__ == 'my_special_function'

    def test_admin_required_preserves_function_name(self, app):
        """admin_required should preserve function name"""
        from app.utils.decorators import admin_required

        @admin_required
        def admin_only_function():
            pass

        assert admin_only_function.__name__ == 'admin_only_function'
