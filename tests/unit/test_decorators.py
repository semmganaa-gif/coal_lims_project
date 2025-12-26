# -*- coding: utf-8 -*-
"""
Tests for app/utils/decorators.py
Authorization decorators comprehensive tests
"""
import pytest
from unittest.mock import patch, MagicMock
from functools import wraps


class TestRoleRequiredBasic:
    """role_required decorator basic tests"""

    def test_import(self):
        """Import decorator"""
        from app.utils.decorators import role_required
        assert callable(role_required)

    def test_single_role_allowed(self, app):
        """Single role allowed"""
        from app.utils.decorators import role_required

        @role_required('admin')
        def view():
            return "success"

        with app.test_request_context('/'):
            with patch('app.utils.decorators.current_user') as mock:
                mock.is_authenticated = True
                mock.role = 'admin'
                assert view() == "success"

    def test_multiple_roles_allowed(self, app):
        """Multiple roles - first match"""
        from app.utils.decorators import role_required

        @role_required('admin', 'senior', 'chemist')
        def view():
            return "success"

        with app.test_request_context('/'):
            with patch('app.utils.decorators.current_user') as mock:
                mock.is_authenticated = True
                mock.role = 'chemist'
                assert view() == "success"

    def test_preserves_function_name(self, app):
        """Wrapper preserves function name (wraps)"""
        from app.utils.decorators import role_required

        @role_required('admin')
        def my_custom_view():
            """My docstring"""
            return "ok"

        assert my_custom_view.__name__ == 'my_custom_view'

    def test_preserves_docstring(self, app):
        """Wrapper preserves docstring"""
        from app.utils.decorators import role_required

        @role_required('admin')
        def my_view():
            """My docstring"""
            return "ok"

        assert 'My docstring' in my_view.__doc__

    def test_passes_args(self, app):
        """Passes positional arguments to wrapped function"""
        from app.utils.decorators import role_required

        @role_required('admin')
        def view_with_args(a, b, c):
            return f"{a}-{b}-{c}"

        with app.test_request_context('/'):
            with patch('app.utils.decorators.current_user') as mock:
                mock.is_authenticated = True
                mock.role = 'admin'
                assert view_with_args(1, 2, 3) == "1-2-3"

    def test_passes_kwargs(self, app):
        """Passes keyword arguments to wrapped function"""
        from app.utils.decorators import role_required

        @role_required('admin')
        def view_with_kwargs(name=None, value=None):
            return f"{name}={value}"

        with app.test_request_context('/'):
            with patch('app.utils.decorators.current_user') as mock:
                mock.is_authenticated = True
                mock.role = 'admin'
                assert view_with_kwargs(name="test", value=42) == "test=42"

    def test_passes_mixed_args_kwargs(self, app):
        """Passes mixed args and kwargs"""
        from app.utils.decorators import role_required

        @role_required('admin')
        def view_mixed(a, b, c=None):
            return f"{a},{b},{c}"

        with app.test_request_context('/'):
            with patch('app.utils.decorators.current_user') as mock:
                mock.is_authenticated = True
                mock.role = 'admin'
                assert view_mixed(1, 2, c=3) == "1,2,3"


class TestRoleRequiredNotAuth:
    """role_required - unauthenticated user tests"""

    def test_redirects_to_login(self, app):
        """Redirects unauthenticated to login"""
        from app.utils.decorators import role_required

        @role_required('admin')
        def view():
            return "success"

        with app.test_request_context('/'):
            with patch('app.utils.decorators.current_user') as mock_user:
                mock_user.is_authenticated = False
                with patch('app.utils.decorators.flash') as mock_flash:
                    with patch('app.utils.decorators.url_for', return_value='/login'):
                        result = view()
                        # Should be redirect
                        assert result.status_code == 302
                        mock_flash.assert_called_once()

    def test_flash_warning_message(self, app):
        """Flashes warning message for unauthenticated"""
        from app.utils.decorators import role_required

        @role_required('admin')
        def view():
            return "success"

        with app.test_request_context('/'):
            with patch('app.utils.decorators.current_user') as mock_user:
                mock_user.is_authenticated = False
                with patch('app.utils.decorators.flash') as mock_flash:
                    with patch('app.utils.decorators.url_for', return_value='/login'):
                        view()
                        # Check flash was called with warning category
                        args = mock_flash.call_args[0]
                        kwargs = mock_flash.call_args[1] if mock_flash.call_args[1] else {}
                        assert 'warning' in str(mock_flash.call_args)


class TestRoleRequiredForbidden:
    """role_required - forbidden access tests"""

    def test_aborts_403_wrong_role(self, app):
        """Aborts 403 for wrong role"""
        from app.utils.decorators import role_required

        @role_required('admin')
        def view():
            return "success"

        with app.test_request_context('/'):
            with patch('app.utils.decorators.current_user') as mock:
                mock.is_authenticated = True
                mock.role = 'viewer'  # Not admin
                with patch('app.utils.decorators.flash'):
                    with pytest.raises(Exception):  # werkzeug HTTPException
                        view()

    def test_flash_danger_message(self, app):
        """Flashes danger message for forbidden"""
        from app.utils.decorators import role_required

        @role_required('admin', 'senior')
        def view():
            return "success"

        with app.test_request_context('/'):
            with patch('app.utils.decorators.current_user') as mock:
                mock.is_authenticated = True
                mock.role = 'chemist'
                with patch('app.utils.decorators.flash') as mock_flash:
                    with patch('app.utils.decorators.abort') as mock_abort:
                        mock_abort.side_effect = Exception("403")
                        try:
                            view()
                        except Exception:
                            pass
                        # Check danger category
                        assert 'danger' in str(mock_flash.call_args)

    def test_flash_contains_required_roles(self, app):
        """Flash message contains required roles list"""
        from app.utils.decorators import role_required

        @role_required('admin', 'senior')
        def view():
            return "success"

        with app.test_request_context('/'):
            with patch('app.utils.decorators.current_user') as mock:
                mock.is_authenticated = True
                mock.role = 'viewer'
                with patch('app.utils.decorators.flash') as mock_flash:
                    with patch('app.utils.decorators.abort') as mock_abort:
                        mock_abort.side_effect = Exception("403")
                        try:
                            view()
                        except Exception:
                            pass
                        # Check message contains roles
                        flash_msg = mock_flash.call_args[0][0]
                        assert 'admin' in flash_msg or 'senior' in flash_msg


class TestAdminRequiredBasic:
    """admin_required decorator basic tests"""

    def test_import(self):
        """Import decorator"""
        from app.utils.decorators import admin_required
        assert callable(admin_required)

    def test_admin_allowed(self, app):
        """Admin role allowed"""
        from app.utils.decorators import admin_required

        @admin_required
        def admin_view():
            return "admin success"

        with app.test_request_context('/'):
            with patch('app.utils.decorators.current_user') as mock:
                mock.is_authenticated = True
                mock.role = 'admin'
                assert admin_view() == "admin success"

    def test_preserves_function_name(self, app):
        """Wrapper preserves function name"""
        from app.utils.decorators import admin_required

        @admin_required
        def admin_panel():
            return "ok"

        assert admin_panel.__name__ == 'admin_panel'

    def test_passes_args(self, app):
        """Passes arguments to wrapped function"""
        from app.utils.decorators import admin_required

        @admin_required
        def admin_edit(user_id, action):
            return f"edit:{user_id}:{action}"

        with app.test_request_context('/'):
            with patch('app.utils.decorators.current_user') as mock:
                mock.is_authenticated = True
                mock.role = 'admin'
                assert admin_edit(123, "delete") == "edit:123:delete"


class TestAdminRequiredDenied:
    """admin_required - denied access tests"""

    def test_senior_denied(self, app):
        """Senior role denied"""
        from app.utils.decorators import admin_required

        @admin_required
        def view():
            return "success"

        with app.test_request_context('/'):
            with patch('app.utils.decorators.current_user') as mock:
                mock.is_authenticated = True
                mock.role = 'senior'
                with patch('app.utils.decorators.flash'):
                    with pytest.raises(Exception):
                        view()

    def test_chemist_denied(self, app):
        """Chemist role denied"""
        from app.utils.decorators import admin_required

        @admin_required
        def view():
            return "success"

        with app.test_request_context('/'):
            with patch('app.utils.decorators.current_user') as mock:
                mock.is_authenticated = True
                mock.role = 'chemist'
                with patch('app.utils.decorators.flash'):
                    with pytest.raises(Exception):
                        view()

    def test_unauthenticated_redirect(self, app):
        """Unauthenticated redirects to login"""
        from app.utils.decorators import admin_required

        @admin_required
        def view():
            return "success"

        with app.test_request_context('/'):
            with patch('app.utils.decorators.current_user') as mock:
                mock.is_authenticated = False
                with patch('app.utils.decorators.flash'):
                    with patch('app.utils.decorators.url_for', return_value='/login'):
                        result = view()
                        assert result.status_code == 302


class TestRoleOrOwnerRequiredBasic:
    """role_or_owner_required decorator basic tests"""

    def test_import(self):
        """Import decorator"""
        from app.utils.decorators import role_or_owner_required
        assert callable(role_or_owner_required)

    def test_role_allowed(self, app):
        """Allowed role passes"""
        from app.utils.decorators import role_or_owner_required

        @role_or_owner_required('admin', 'senior')
        def view(item_id):
            return f"view:{item_id}"

        with app.test_request_context('/'):
            with patch('app.utils.decorators.current_user') as mock:
                mock.is_authenticated = True
                mock.role = 'senior'
                assert view(123) == "view:123"

    def test_owner_allowed(self, app):
        """Owner check passes"""
        from app.utils.decorators import role_or_owner_required

        def check_owner(item_id):
            return item_id == 42

        @role_or_owner_required('admin', owner_check=check_owner)
        def view(item_id):
            return f"owner:{item_id}"

        with app.test_request_context('/'):
            with patch('app.utils.decorators.current_user') as mock:
                mock.is_authenticated = True
                mock.role = 'viewer'  # Not admin
                assert view(42) == "owner:42"

    def test_owner_with_kwargs(self, app):
        """Owner check with kwargs"""
        from app.utils.decorators import role_or_owner_required

        def check_owner(*args, **kwargs):
            return kwargs.get('item_id') == 99

        @role_or_owner_required('admin', owner_check=check_owner)
        def view(item_id=None):
            return f"owner:{item_id}"

        with app.test_request_context('/'):
            with patch('app.utils.decorators.current_user') as mock:
                mock.is_authenticated = True
                mock.role = 'viewer'
                assert view(item_id=99) == "owner:99"

    def test_preserves_function_name(self, app):
        """Wrapper preserves function name"""
        from app.utils.decorators import role_or_owner_required

        @role_or_owner_required('admin')
        def my_resource():
            return "ok"

        assert my_resource.__name__ == 'my_resource'


class TestRoleOrOwnerRequiredDenied:
    """role_or_owner_required - denied access tests"""

    def test_neither_role_nor_owner(self, app):
        """Neither role nor owner denied"""
        from app.utils.decorators import role_or_owner_required

        def check_owner(item_id):
            return False  # Not owner

        @role_or_owner_required('admin', owner_check=check_owner)
        def view(item_id):
            return "success"

        with app.test_request_context('/'):
            with patch('app.utils.decorators.current_user') as mock:
                mock.is_authenticated = True
                mock.role = 'viewer'
                with patch('app.utils.decorators.flash'):
                    with pytest.raises(Exception):
                        view(123)

    def test_no_owner_check_wrong_role(self, app):
        """No owner_check and wrong role denied"""
        from app.utils.decorators import role_or_owner_required

        @role_or_owner_required('admin')  # No owner_check
        def view():
            return "success"

        with app.test_request_context('/'):
            with patch('app.utils.decorators.current_user') as mock:
                mock.is_authenticated = True
                mock.role = 'viewer'
                with patch('app.utils.decorators.flash'):
                    with pytest.raises(Exception):
                        view()

    def test_unauthenticated_redirect(self, app):
        """Unauthenticated redirects to login"""
        from app.utils.decorators import role_or_owner_required

        @role_or_owner_required('admin')
        def view():
            return "success"

        with app.test_request_context('/'):
            with patch('app.utils.decorators.current_user') as mock:
                mock.is_authenticated = False
                with patch('app.utils.decorators.flash'):
                    with patch('app.utils.decorators.url_for', return_value='/login'):
                        result = view()
                        assert result.status_code == 302


class TestAnalysisRoleRequiredBasic:
    """analysis_role_required decorator basic tests"""

    def test_import(self):
        """Import decorator"""
        from app.utils.decorators import analysis_role_required
        assert callable(analysis_role_required)

    def test_default_chemist_allowed(self, app):
        """Default roles - chemist allowed"""
        from app.utils.decorators import analysis_role_required

        @analysis_role_required()
        def view():
            return "chemist"

        with app.test_request_context('/'):
            with patch('app.utils.decorators.current_user') as mock:
                mock.is_authenticated = True
                mock.role = 'chemist'
                assert view() == "chemist"

    def test_default_senior_allowed(self, app):
        """Default roles - senior allowed"""
        from app.utils.decorators import analysis_role_required

        @analysis_role_required()
        def view():
            return "senior"

        with app.test_request_context('/'):
            with patch('app.utils.decorators.current_user') as mock:
                mock.is_authenticated = True
                mock.role = 'senior'
                assert view() == "senior"

    def test_default_manager_allowed(self, app):
        """Default roles - manager allowed"""
        from app.utils.decorators import analysis_role_required

        @analysis_role_required()
        def view():
            return "manager"

        with app.test_request_context('/'):
            with patch('app.utils.decorators.current_user') as mock:
                mock.is_authenticated = True
                mock.role = 'manager'
                assert view() == "manager"

    def test_default_admin_allowed(self, app):
        """Default roles - admin allowed"""
        from app.utils.decorators import analysis_role_required

        @analysis_role_required()
        def view():
            return "admin"

        with app.test_request_context('/'):
            with patch('app.utils.decorators.current_user') as mock:
                mock.is_authenticated = True
                mock.role = 'admin'
                assert view() == "admin"

    def test_default_prep_allowed(self, app):
        """Default roles - prep allowed"""
        from app.utils.decorators import analysis_role_required

        @analysis_role_required()
        def view():
            return "prep"

        with app.test_request_context('/'):
            with patch('app.utils.decorators.current_user') as mock:
                mock.is_authenticated = True
                mock.role = 'prep'
                assert view() == "prep"

    def test_custom_roles_list(self, app):
        """Custom roles list"""
        from app.utils.decorators import analysis_role_required

        @analysis_role_required(['admin', 'senior'])
        def view():
            return "custom"

        with app.test_request_context('/'):
            with patch('app.utils.decorators.current_user') as mock:
                mock.is_authenticated = True
                mock.role = 'admin'
                assert view() == "custom"

    def test_preserves_function_name(self, app):
        """Wrapper preserves function name"""
        from app.utils.decorators import analysis_role_required

        @analysis_role_required()
        def analysis_workspace():
            return "ok"

        assert analysis_workspace.__name__ == 'analysis_workspace'


class TestAnalysisRoleRequiredDenied:
    """analysis_role_required - denied access tests"""

    def test_viewer_denied(self, app):
        """Viewer role denied with default roles"""
        from app.utils.decorators import analysis_role_required

        @analysis_role_required()
        def view():
            return "success"

        with app.test_request_context('/'):
            with patch('app.utils.decorators.current_user') as mock:
                mock.is_authenticated = True
                mock.role = 'viewer'
                with pytest.raises(Exception):
                    view()

    def test_chemist_denied_custom_roles(self, app):
        """Chemist denied with custom roles"""
        from app.utils.decorators import analysis_role_required

        @analysis_role_required(['admin'])
        def view():
            return "success"

        with app.test_request_context('/'):
            with patch('app.utils.decorators.current_user') as mock:
                mock.is_authenticated = True
                mock.role = 'chemist'
                with pytest.raises(Exception):
                    view()

    def test_unauthenticated_redirect(self, app):
        """Unauthenticated redirects to login with next"""
        from app.utils.decorators import analysis_role_required

        @analysis_role_required()
        def my_analysis_view():
            return "success"

        with app.test_request_context('/'):
            with patch('app.utils.decorators.current_user') as mock:
                mock.is_authenticated = False
                with patch('app.utils.decorators.url_for') as mock_url_for:
                    mock_url_for.return_value = '/login'
                    result = my_analysis_view()
                    assert result.status_code == 302
                    # Check url_for was called with main.login
                    assert mock_url_for.called


class TestDecoratorChaining:
    """Test chaining multiple decorators"""

    def test_role_required_with_login_required(self, app):
        """role_required works after login_required style check"""
        from app.utils.decorators import role_required

        @role_required('admin')
        def protected_view():
            return "protected"

        with app.test_request_context('/'):
            with patch('app.utils.decorators.current_user') as mock:
                mock.is_authenticated = True
                mock.role = 'admin'
                assert protected_view() == "protected"

    def test_multiple_decorators_order(self, app):
        """Multiple decorators in correct order"""
        from app.utils.decorators import role_required

        def log_decorator(f):
            @wraps(f)
            def wrapper(*args, **kwargs):
                return f(*args, **kwargs) + "_logged"
            return wrapper

        @log_decorator
        @role_required('admin')
        def view():
            return "result"

        with app.test_request_context('/'):
            with patch('app.utils.decorators.current_user') as mock:
                mock.is_authenticated = True
                mock.role = 'admin'
                assert view() == "result_logged"


class TestEdgeCases:
    """Edge case tests"""

    def test_role_required_empty_string_role(self, app):
        """User with empty string role"""
        from app.utils.decorators import role_required

        @role_required('admin')
        def view():
            return "success"

        with app.test_request_context('/'):
            with patch('app.utils.decorators.current_user') as mock:
                mock.is_authenticated = True
                mock.role = ''  # Empty role
                with patch('app.utils.decorators.flash'):
                    with pytest.raises(Exception):
                        view()

    def test_role_required_none_role(self, app):
        """User with None role"""
        from app.utils.decorators import role_required

        @role_required('admin')
        def view():
            return "success"

        with app.test_request_context('/'):
            with patch('app.utils.decorators.current_user') as mock:
                mock.is_authenticated = True
                mock.role = None
                with patch('app.utils.decorators.flash'):
                    with pytest.raises(Exception):
                        view()

    def test_owner_check_returns_truthy(self, app):
        """Owner check returning truthy value (not just True)"""
        from app.utils.decorators import role_or_owner_required

        def check_owner(item_id):
            return "yes"  # Truthy but not True

        @role_or_owner_required('admin', owner_check=check_owner)
        def view(item_id):
            return "ok"

        with app.test_request_context('/'):
            with patch('app.utils.decorators.current_user') as mock:
                mock.is_authenticated = True
                mock.role = 'viewer'
                assert view(1) == "ok"

    def test_owner_check_returns_falsy(self, app):
        """Owner check returning falsy value (not just False)"""
        from app.utils.decorators import role_or_owner_required

        def check_owner(item_id):
            return 0  # Falsy

        @role_or_owner_required('admin', owner_check=check_owner)
        def view(item_id):
            return "ok"

        with app.test_request_context('/'):
            with patch('app.utils.decorators.current_user') as mock:
                mock.is_authenticated = True
                mock.role = 'viewer'
                with patch('app.utils.decorators.flash'):
                    with pytest.raises(Exception):
                        view(1)

    def test_owner_check_none_passes_to_abort(self, app):
        """When owner_check is None, goes to abort"""
        from app.utils.decorators import role_or_owner_required

        @role_or_owner_required('admin', owner_check=None)
        def view():
            return "ok"

        with app.test_request_context('/'):
            with patch('app.utils.decorators.current_user') as mock:
                mock.is_authenticated = True
                mock.role = 'viewer'
                with patch('app.utils.decorators.flash'):
                    with pytest.raises(Exception):
                        view()


class TestFlashMessages:
    """Flash message verification tests"""

    def test_role_required_flash_on_redirect(self, app):
        """role_required flashes on redirect"""
        from app.utils.decorators import role_required

        @role_required('admin')
        def view():
            return "ok"

        with app.test_request_context('/'):
            with patch('app.utils.decorators.current_user') as mock:
                mock.is_authenticated = False
                with patch('app.utils.decorators.flash') as mock_flash:
                    with patch('app.utils.decorators.url_for', return_value='/'):
                        view()
                        mock_flash.assert_called()

    def test_admin_required_flash_on_redirect(self, app):
        """admin_required flashes on redirect"""
        from app.utils.decorators import admin_required

        @admin_required
        def view():
            return "ok"

        with app.test_request_context('/'):
            with patch('app.utils.decorators.current_user') as mock:
                mock.is_authenticated = False
                with patch('app.utils.decorators.flash') as mock_flash:
                    with patch('app.utils.decorators.url_for', return_value='/'):
                        view()
                        mock_flash.assert_called()

    def test_role_or_owner_flash_on_redirect(self, app):
        """role_or_owner_required flashes on redirect"""
        from app.utils.decorators import role_or_owner_required

        @role_or_owner_required('admin')
        def view():
            return "ok"

        with app.test_request_context('/'):
            with patch('app.utils.decorators.current_user') as mock:
                mock.is_authenticated = False
                with patch('app.utils.decorators.flash') as mock_flash:
                    with patch('app.utils.decorators.url_for', return_value='/'):
                        view()
                        mock_flash.assert_called()

    def test_admin_required_flash_on_forbidden(self, app):
        """admin_required flashes danger on forbidden"""
        from app.utils.decorators import admin_required

        @admin_required
        def view():
            return "ok"

        with app.test_request_context('/'):
            with patch('app.utils.decorators.current_user') as mock:
                mock.is_authenticated = True
                mock.role = 'viewer'
                with patch('app.utils.decorators.flash') as mock_flash:
                    with patch('app.utils.decorators.abort') as mock_abort:
                        mock_abort.side_effect = Exception("403")
                        try:
                            view()
                        except Exception:
                            pass
                        mock_flash.assert_called()
                        # Check danger category
                        assert 'danger' in str(mock_flash.call_args)


class TestReturnValues:
    """Test return value handling"""

    def test_returns_none(self, app):
        """Function returning None"""
        from app.utils.decorators import role_required

        @role_required('admin')
        def view():
            return None

        with app.test_request_context('/'):
            with patch('app.utils.decorators.current_user') as mock:
                mock.is_authenticated = True
                mock.role = 'admin'
                assert view() is None

    def test_returns_dict(self, app):
        """Function returning dict (API style)"""
        from app.utils.decorators import role_required

        @role_required('admin')
        def api_view():
            return {"status": "ok", "data": [1, 2, 3]}

        with app.test_request_context('/'):
            with patch('app.utils.decorators.current_user') as mock:
                mock.is_authenticated = True
                mock.role = 'admin'
                result = api_view()
                assert result["status"] == "ok"
                assert result["data"] == [1, 2, 3]

    def test_returns_tuple(self, app):
        """Function returning tuple (Flask response style)"""
        from app.utils.decorators import role_required

        @role_required('admin')
        def view():
            return "OK", 200

        with app.test_request_context('/'):
            with patch('app.utils.decorators.current_user') as mock:
                mock.is_authenticated = True
                mock.role = 'admin'
                result = view()
                assert result == ("OK", 200)

    def test_returns_list(self, app):
        """Function returning list"""
        from app.utils.decorators import role_required

        @role_required('admin')
        def view():
            return [1, 2, 3]

        with app.test_request_context('/'):
            with patch('app.utils.decorators.current_user') as mock:
                mock.is_authenticated = True
                mock.role = 'admin'
                assert view() == [1, 2, 3]


class TestComplexArgs:
    """Test complex argument handling"""

    def test_default_args(self, app):
        """Function with default arguments"""
        from app.utils.decorators import role_required

        @role_required('admin')
        def view(a, b=10, c=20):
            return a + b + c

        with app.test_request_context('/'):
            with patch('app.utils.decorators.current_user') as mock:
                mock.is_authenticated = True
                mock.role = 'admin'
                assert view(1) == 31
                assert view(1, 2) == 23
                assert view(1, 2, 3) == 6

    def test_star_args(self, app):
        """Function with *args"""
        from app.utils.decorators import role_required

        @role_required('admin')
        def view(*args):
            return sum(args)

        with app.test_request_context('/'):
            with patch('app.utils.decorators.current_user') as mock:
                mock.is_authenticated = True
                mock.role = 'admin'
                assert view(1, 2, 3, 4, 5) == 15

    def test_star_kwargs(self, app):
        """Function with **kwargs"""
        from app.utils.decorators import role_required

        @role_required('admin')
        def view(**kwargs):
            return kwargs

        with app.test_request_context('/'):
            with patch('app.utils.decorators.current_user') as mock:
                mock.is_authenticated = True
                mock.role = 'admin'
                result = view(a=1, b=2, c=3)
                assert result == {"a": 1, "b": 2, "c": 3}

    def test_all_arg_types(self, app):
        """Function with all argument types"""
        from app.utils.decorators import role_required

        @role_required('admin')
        def view(a, b, *args, c=None, **kwargs):
            return {
                "a": a, "b": b,
                "args": args, "c": c,
                "kwargs": kwargs
            }

        with app.test_request_context('/'):
            with patch('app.utils.decorators.current_user') as mock:
                mock.is_authenticated = True
                mock.role = 'admin'
                result = view(1, 2, 3, 4, c=5, d=6, e=7)
                assert result["a"] == 1
                assert result["b"] == 2
                assert result["args"] == (3, 4)
                assert result["c"] == 5
                assert result["kwargs"] == {"d": 6, "e": 7}
