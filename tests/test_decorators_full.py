# tests/test_decorators_full.py
# -*- coding: utf-8 -*-
"""
Complete tests for app/utils/decorators.py - targeting 100% coverage.
"""

import pytest
from unittest.mock import patch, MagicMock


class TestRoleRequired:
    """Tests for role_required decorator."""

    def test_allows_admin(self, app, client):
        """Test allows admin role."""
        with app.test_request_context('/'):
            from app.utils.decorators import role_required

            @role_required('admin', 'senior')
            def test_view():
                return "Success"

            with patch('app.utils.decorators.current_user') as mock_user:
                mock_user.is_authenticated = True
                mock_user.role = 'admin'
                result = test_view()
                assert result == "Success"

    def test_allows_senior(self, app, client):
        """Test allows senior role."""
        with app.test_request_context('/'):
            from app.utils.decorators import role_required

            @role_required('admin', 'senior')
            def test_view():
                return "Success"

            with patch('app.utils.decorators.current_user') as mock_user:
                mock_user.is_authenticated = True
                mock_user.role = 'senior'
                result = test_view()
                assert result == "Success"

    def test_redirects_unauthenticated(self, app, client):
        """Test redirects unauthenticated user."""
        with app.test_request_context('/'):
            from app.utils.decorators import role_required

            @role_required('admin')
            def test_view():
                return "Success"

            with patch('app.utils.decorators.current_user') as mock_user:
                mock_user.is_authenticated = False
                with patch('app.utils.decorators.flash'):
                    with patch('app.utils.decorators.url_for', return_value='/login'):
                        result = test_view()
                        assert result.status_code == 302

    def test_aborts_unauthorized_role(self, app, client):
        """Test aborts for unauthorized role."""
        with app.test_request_context('/'):
            from app.utils.decorators import role_required

            @role_required('admin')
            def test_view():
                return "Success"

            with patch('app.utils.decorators.current_user') as mock_user:
                mock_user.is_authenticated = True
                mock_user.role = 'chemist'
                with patch('app.utils.decorators.flash'):
                    with pytest.raises(Exception):  # 403 abort
                        test_view()

    def test_wrapper_preserves_name(self, app):
        """Test wrapper preserves function name."""
        with app.app_context():
            from app.utils.decorators import role_required

            @role_required('admin')
            def my_view():
                """My docstring."""
                return "OK"

            assert my_view.__name__ == 'my_view'


class TestAdminRequired:
    """Tests for admin_required decorator."""

    def test_allows_admin(self, app, client):
        """Test allows admin role."""
        with app.test_request_context('/'):
            from app.utils.decorators import admin_required

            @admin_required
            def test_view():
                return "Success"

            with patch('app.utils.decorators.current_user') as mock_user:
                mock_user.is_authenticated = True
                mock_user.role = 'admin'
                result = test_view()
                assert result == "Success"

    def test_redirects_unauthenticated(self, app, client):
        """Test redirects unauthenticated user."""
        with app.test_request_context('/'):
            from app.utils.decorators import admin_required

            @admin_required
            def test_view():
                return "Success"

            with patch('app.utils.decorators.current_user') as mock_user:
                mock_user.is_authenticated = False
                with patch('app.utils.decorators.flash'):
                    with patch('app.utils.decorators.url_for', return_value='/login'):
                        result = test_view()
                        assert result.status_code == 302

    def test_aborts_non_admin(self, app, client):
        """Test aborts for non-admin role."""
        with app.test_request_context('/'):
            from app.utils.decorators import admin_required

            @admin_required
            def test_view():
                return "Success"

            with patch('app.utils.decorators.current_user') as mock_user:
                mock_user.is_authenticated = True
                mock_user.role = 'senior'
                with patch('app.utils.decorators.flash'):
                    with pytest.raises(Exception):  # 403 abort
                        test_view()

    def test_wrapper_preserves_name(self, app):
        """Test wrapper preserves function name."""
        with app.app_context():
            from app.utils.decorators import admin_required

            @admin_required
            def admin_view():
                """Admin docstring."""
                return "OK"

            assert admin_view.__name__ == 'admin_view'


class TestRoleOrOwnerRequired:
    """Tests for role_or_owner_required decorator."""

    def test_allows_role(self, app, client):
        """Test allows user with allowed role."""
        with app.test_request_context('/'):
            from app.utils.decorators import role_or_owner_required

            @role_or_owner_required('admin', 'senior')
            def test_view():
                return "Success"

            with patch('app.utils.decorators.current_user') as mock_user:
                mock_user.is_authenticated = True
                mock_user.role = 'admin'
                result = test_view()
                assert result == "Success"

    def test_allows_owner(self, app, client):
        """Test allows owner."""
        with app.test_request_context('/'):
            from app.utils.decorators import role_or_owner_required

            def owner_check(item_id):
                return True

            @role_or_owner_required('admin', owner_check=owner_check)
            def test_view(item_id):
                return "Success"

            with patch('app.utils.decorators.current_user') as mock_user:
                mock_user.is_authenticated = True
                mock_user.role = 'chemist'
                result = test_view(item_id=1)
                assert result == "Success"

    def test_redirects_unauthenticated(self, app, client):
        """Test redirects unauthenticated user."""
        with app.test_request_context('/'):
            from app.utils.decorators import role_or_owner_required

            @role_or_owner_required('admin')
            def test_view():
                return "Success"

            with patch('app.utils.decorators.current_user') as mock_user:
                mock_user.is_authenticated = False
                with patch('app.utils.decorators.flash'):
                    with patch('app.utils.decorators.url_for', return_value='/login'):
                        result = test_view()
                        assert result.status_code == 302

    def test_aborts_non_role_non_owner(self, app, client):
        """Test aborts for non-role and non-owner."""
        with app.test_request_context('/'):
            from app.utils.decorators import role_or_owner_required

            def owner_check(item_id):
                return False

            @role_or_owner_required('admin', owner_check=owner_check)
            def test_view(item_id):
                return "Success"

            with patch('app.utils.decorators.current_user') as mock_user:
                mock_user.is_authenticated = True
                mock_user.role = 'chemist'
                with patch('app.utils.decorators.flash'):
                    with pytest.raises(Exception):  # 403 abort
                        test_view(item_id=1)

    def test_aborts_no_owner_check(self, app, client):
        """Test aborts when no owner_check provided."""
        with app.test_request_context('/'):
            from app.utils.decorators import role_or_owner_required

            @role_or_owner_required('admin')
            def test_view():
                return "Success"

            with patch('app.utils.decorators.current_user') as mock_user:
                mock_user.is_authenticated = True
                mock_user.role = 'chemist'
                with patch('app.utils.decorators.flash'):
                    with pytest.raises(Exception):  # 403 abort
                        test_view()


class TestAnalysisRoleRequired:
    """Tests for analysis_role_required decorator."""

    def test_allows_default_roles(self, app, client):
        """Test allows default roles (chemist, senior, manager, admin, prep)."""
        with app.test_request_context('/'):
            from app.utils.decorators import analysis_role_required

            @analysis_role_required()
            def test_view():
                return "Success"

            for role in ['chemist', 'senior', 'manager', 'admin', 'prep']:
                with patch('app.utils.decorators.current_user') as mock_user:
                    mock_user.is_authenticated = True
                    mock_user.role = role
                    result = test_view()
                    assert result == "Success"

    def test_allows_custom_roles(self, app, client):
        """Test allows custom roles."""
        with app.test_request_context('/'):
            from app.utils.decorators import analysis_role_required

            @analysis_role_required(['admin', 'senior'])
            def test_view():
                return "Success"

            with patch('app.utils.decorators.current_user') as mock_user:
                mock_user.is_authenticated = True
                mock_user.role = 'admin'
                result = test_view()
                assert result == "Success"

    def test_redirects_unauthenticated(self, app, client):
        """Test redirects unauthenticated user."""
        with app.test_request_context('/'):
            from app.utils.decorators import analysis_role_required

            @analysis_role_required()
            def test_view():
                return "Success"

            with patch('app.utils.decorators.current_user') as mock_user:
                mock_user.is_authenticated = False
                with patch('app.utils.decorators.url_for', return_value='/login'):
                    result = test_view()
                    assert result.status_code == 302

    def test_aborts_unauthorized_role(self, app, client):
        """Test aborts for unauthorized role."""
        with app.test_request_context('/'):
            from app.utils.decorators import analysis_role_required

            @analysis_role_required(['admin'])
            def test_view():
                return "Success"

            with patch('app.utils.decorators.current_user') as mock_user:
                mock_user.is_authenticated = True
                mock_user.role = 'viewer'
                with pytest.raises(Exception):  # 403 abort
                    test_view()

    def test_wrapper_preserves_name(self, app):
        """Test wrapper preserves function name."""
        with app.app_context():
            from app.utils.decorators import analysis_role_required

            @analysis_role_required()
            def analysis_view():
                """Analysis docstring."""
                return "OK"

            assert analysis_view.__name__ == 'analysis_view'
