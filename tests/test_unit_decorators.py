# tests/unit/test_decorators.py
# -*- coding: utf-8 -*-
"""
Decorator functions тест

Tests for authorization decorators.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from functools import wraps


class TestRoleRequired:
    """role_required() декораторын тест"""

    def test_role_required_authenticated_allowed(self, app):
        """Нэвтэрсэн, зөвшөөрөгдсөн эрхтэй"""
        from app.utils.decorators import role_required

        @role_required('admin', 'senior')
        def test_func():
            return "success"

        with app.test_request_context():
            with patch('app.utils.decorators.current_user') as mock_user:
                mock_user.is_authenticated = True
                mock_user.role = 'admin'
                result = test_func()
                assert result == "success"

    def test_role_required_authenticated_not_allowed(self, app):
        """Нэвтэрсэн, эрхгүй"""
        from app.utils.decorators import role_required

        @role_required('admin', 'senior')
        def test_func():
            return "success"

        with app.test_request_context():
            with patch('app.utils.decorators.current_user') as mock_user:
                mock_user.is_authenticated = True
                mock_user.role = 'chemist'
                with pytest.raises(Exception):  # Should abort(403)
                    test_func()

    def test_role_required_not_authenticated(self, app):
        """Нэвтрээгүй"""
        from app.utils.decorators import role_required
        from flask import redirect

        @role_required('admin')
        def test_func():
            return "success"

        with app.test_request_context():
            with patch('app.utils.decorators.current_user') as mock_user:
                with patch('app.utils.decorators.redirect') as mock_redirect:
                    with patch('app.utils.decorators.url_for') as mock_url_for:
                        mock_url_for.return_value = '/login'
                        mock_redirect.return_value = redirect('/')
                        mock_user.is_authenticated = False
                        result = test_func()
                        mock_redirect.assert_called_once()


class TestAdminRequired:
    """admin_required() декораторын тест"""

    def test_admin_required_is_admin(self, app):
        """Админ хэрэглэгч"""
        from app.utils.decorators import admin_required

        @admin_required
        def test_func():
            return "admin success"

        with app.test_request_context():
            with patch('app.utils.decorators.current_user') as mock_user:
                mock_user.is_authenticated = True
                mock_user.role = 'admin'
                result = test_func()
                assert result == "admin success"

    def test_admin_required_not_admin(self, app):
        """Админ биш"""
        from app.utils.decorators import admin_required

        @admin_required
        def test_func():
            return "success"

        with app.test_request_context():
            with patch('app.utils.decorators.current_user') as mock_user:
                mock_user.is_authenticated = True
                mock_user.role = 'senior'
                with pytest.raises(Exception):  # Should abort(403)
                    test_func()

    def test_admin_required_not_authenticated(self, app):
        """Нэвтрээгүй"""
        from app.utils.decorators import admin_required
        from flask import redirect

        @admin_required
        def test_func():
            return "success"

        with app.test_request_context():
            with patch('app.utils.decorators.current_user') as mock_user:
                with patch('app.utils.decorators.redirect') as mock_redirect:
                    with patch('app.utils.decorators.url_for') as mock_url_for:
                        mock_url_for.return_value = '/login'
                        mock_redirect.return_value = redirect('/')
                        mock_user.is_authenticated = False
                        result = test_func()
                        mock_redirect.assert_called_once()


class TestRoleOrOwnerRequired:
    """role_or_owner_required() декораторын тест"""

    def test_has_allowed_role(self, app):
        """Зөвшөөрөгдсөн эрхтэй"""
        from app.utils.decorators import role_or_owner_required

        @role_or_owner_required('admin', 'senior')
        def test_func(item_id):
            return f"success {item_id}"

        with app.test_request_context():
            with patch('app.utils.decorators.current_user') as mock_user:
                mock_user.is_authenticated = True
                mock_user.role = 'admin'
                result = test_func(123)
                assert result == "success 123"

    def test_is_owner(self, app):
        """Эзэмшигч (owner)"""
        from app.utils.decorators import role_or_owner_required

        def owner_check(item_id):
            return item_id == 123  # User owns item 123

        @role_or_owner_required('admin', owner_check=owner_check)
        def test_func(item_id):
            return f"success {item_id}"

        with app.test_request_context():
            with patch('app.utils.decorators.current_user') as mock_user:
                mock_user.is_authenticated = True
                mock_user.role = 'chemist'  # Not admin
                result = test_func(123)  # But is owner
                assert result == "success 123"

    def test_neither_role_nor_owner(self, app):
        """Эрхгүй бас эзэмшигч биш"""
        from app.utils.decorators import role_or_owner_required

        def owner_check(item_id):
            return item_id == 999  # User owns item 999, not 123

        @role_or_owner_required('admin', owner_check=owner_check)
        def test_func(item_id):
            return f"success {item_id}"

        with app.test_request_context():
            with patch('app.utils.decorators.current_user') as mock_user:
                mock_user.is_authenticated = True
                mock_user.role = 'chemist'
                with pytest.raises(Exception):  # Should abort(403)
                    test_func(123)

    def test_not_authenticated(self, app):
        """Нэвтрээгүй"""
        from app.utils.decorators import role_or_owner_required
        from flask import redirect

        @role_or_owner_required('admin')
        def test_func(item_id):
            return f"success {item_id}"

        with app.test_request_context():
            with patch('app.utils.decorators.current_user') as mock_user:
                with patch('app.utils.decorators.redirect') as mock_redirect:
                    with patch('app.utils.decorators.url_for') as mock_url_for:
                        mock_url_for.return_value = '/login'
                        mock_redirect.return_value = redirect('/')
                        mock_user.is_authenticated = False
                        result = test_func(123)
                        mock_redirect.assert_called_once()


class TestAnalysisRoleRequired:
    """analysis_role_required() декораторын тест"""

    def test_default_roles_chemist(self, app):
        """Default эрхүүд - chemist"""
        from app.utils.decorators import analysis_role_required

        @analysis_role_required()
        def test_func():
            return "analysis success"

        with app.test_request_context():
            with patch('app.utils.decorators.current_user') as mock_user:
                mock_user.is_authenticated = True
                mock_user.role = 'chemist'
                result = test_func()
                assert result == "analysis success"

    def test_default_roles_prep(self, app):
        """Default эрхүүд - prep"""
        from app.utils.decorators import analysis_role_required

        @analysis_role_required()
        def test_func():
            return "prep success"

        with app.test_request_context():
            with patch('app.utils.decorators.current_user') as mock_user:
                mock_user.is_authenticated = True
                mock_user.role = 'prep'
                result = test_func()
                assert result == "prep success"

    def test_custom_roles(self, app):
        """Custom эрхүүд"""
        from app.utils.decorators import analysis_role_required

        @analysis_role_required(['admin'])
        def test_func():
            return "admin only"

        with app.test_request_context():
            with patch('app.utils.decorators.current_user') as mock_user:
                mock_user.is_authenticated = True
                mock_user.role = 'admin'
                result = test_func()
                assert result == "admin only"

    def test_role_not_allowed(self, app):
        """Эрхгүй"""
        from app.utils.decorators import analysis_role_required

        @analysis_role_required(['admin'])
        def test_func():
            return "admin only"

        with app.test_request_context():
            with patch('app.utils.decorators.current_user') as mock_user:
                mock_user.is_authenticated = True
                mock_user.role = 'chemist'
                with pytest.raises(Exception):  # Should abort(403)
                    test_func()

    def test_not_authenticated(self, app):
        """Нэвтрээгүй"""
        from app.utils.decorators import analysis_role_required
        from flask import redirect

        @analysis_role_required()
        def test_func():
            return "success"

        test_func.__name__ = 'test_func'  # For url_for

        with app.test_request_context():
            with patch('app.utils.decorators.current_user') as mock_user:
                with patch('app.utils.decorators.redirect') as mock_redirect:
                    with patch('app.utils.decorators.url_for') as mock_url_for:
                        mock_url_for.return_value = '/login'
                        mock_redirect.return_value = redirect('/')
                        mock_user.is_authenticated = False
                        result = test_func()
                        mock_redirect.assert_called_once()
