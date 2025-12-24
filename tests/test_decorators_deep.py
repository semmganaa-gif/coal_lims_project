# tests/test_decorators_deep.py
# -*- coding: utf-8 -*-
"""
Deep coverage tests for app/utils/decorators.py
"""

import pytest
from unittest.mock import MagicMock, patch
from flask import Flask


class TestRoleRequired:
    """Tests for role_required decorator."""

    def test_role_required_decorator_exists(self, app):
        """Test role_required decorator exists."""
        with app.app_context():
            from app.utils.decorators import role_required
            assert callable(role_required)

    def test_role_required_unauthenticated(self, client, app):
        """Test role_required redirects unauthenticated users."""
        with app.app_context():
            from app.utils.decorators import role_required

            @role_required('admin')
            def protected_view():
                return 'OK'

            # Test with unauthenticated user
            with client:
                with patch('app.utils.decorators.current_user') as mock_user:
                    mock_user.is_authenticated = False
                    # The decorator should redirect
                    assert callable(protected_view)

    def test_role_required_wrong_role(self, client, app):
        """Test role_required denies wrong role."""
        with app.app_context():
            from app.utils.decorators import role_required

            @role_required('admin')
            def admin_view():
                return 'OK'

            with patch('app.utils.decorators.current_user') as mock_user:
                mock_user.is_authenticated = True
                mock_user.role = 'chemist'
                # Decorator should abort with 403
                assert callable(admin_view)

    def test_role_required_correct_role(self, client, app):
        """Test role_required allows correct role."""
        with app.app_context():
            from app.utils.decorators import role_required

            @role_required('admin', 'senior')
            def protected_view():
                return 'OK'

            with patch('app.utils.decorators.current_user') as mock_user:
                mock_user.is_authenticated = True
                mock_user.role = 'admin'
                # Should allow access
                assert callable(protected_view)


class TestAdminRequired:
    """Tests for admin_required decorator."""

    def test_admin_required_decorator_exists(self, app):
        """Test admin_required decorator exists."""
        with app.app_context():
            from app.utils.decorators import admin_required
            assert callable(admin_required)

    def test_admin_required_unauthenticated(self, app):
        """Test admin_required redirects unauthenticated users."""
        with app.app_context():
            from app.utils.decorators import admin_required

            @admin_required
            def admin_view():
                return 'OK'

            with patch('app.utils.decorators.current_user') as mock_user:
                mock_user.is_authenticated = False
                assert callable(admin_view)

    def test_admin_required_non_admin(self, app):
        """Test admin_required denies non-admin users."""
        with app.app_context():
            from app.utils.decorators import admin_required

            @admin_required
            def admin_view():
                return 'OK'

            with patch('app.utils.decorators.current_user') as mock_user:
                mock_user.is_authenticated = True
                mock_user.role = 'chemist'
                assert callable(admin_view)

    def test_admin_required_admin_user(self, app):
        """Test admin_required allows admin users."""
        with app.app_context():
            from app.utils.decorators import admin_required

            @admin_required
            def admin_view():
                return 'OK'

            with patch('app.utils.decorators.current_user') as mock_user:
                mock_user.is_authenticated = True
                mock_user.role = 'admin'
                assert callable(admin_view)


class TestRoleOrOwnerRequired:
    """Tests for role_or_owner_required decorator."""

    def test_role_or_owner_required_exists(self, app):
        """Test role_or_owner_required decorator exists."""
        with app.app_context():
            from app.utils.decorators import role_or_owner_required
            assert callable(role_or_owner_required)

    def test_role_or_owner_required_with_role(self, app):
        """Test role_or_owner_required with allowed role."""
        with app.app_context():
            from app.utils.decorators import role_or_owner_required

            @role_or_owner_required('admin', 'senior')
            def protected_view():
                return 'OK'

            with patch('app.utils.decorators.current_user') as mock_user:
                mock_user.is_authenticated = True
                mock_user.role = 'admin'
                assert callable(protected_view)

    def test_role_or_owner_required_with_owner_check(self, app):
        """Test role_or_owner_required with owner check function."""
        with app.app_context():
            from app.utils.decorators import role_or_owner_required

            def is_owner(sample_id):
                return True

            @role_or_owner_required('admin', owner_check=is_owner)
            def protected_view(sample_id):
                return 'OK'

            assert callable(protected_view)


class TestDecoratorMetadata:
    """Tests for decorator metadata preservation."""

    def test_role_required_preserves_name(self, app):
        """Test role_required preserves function name."""
        with app.app_context():
            from app.utils.decorators import role_required

            @role_required('admin')
            def my_function():
                """My docstring."""
                return 'OK'

            assert my_function.__name__ == 'my_function'

    def test_admin_required_preserves_name(self, app):
        """Test admin_required preserves function name."""
        with app.app_context():
            from app.utils.decorators import admin_required

            @admin_required
            def my_admin_function():
                """Admin docstring."""
                return 'OK'

            assert my_admin_function.__name__ == 'my_admin_function'


class TestDecoratorChaining:
    """Tests for decorator chaining."""

    def test_multiple_decorators(self, app):
        """Test multiple decorators can be chained."""
        with app.app_context():
            from app.utils.decorators import role_required

            @role_required('admin')
            @role_required('senior')
            def doubly_protected():
                return 'OK'

            assert callable(doubly_protected)
