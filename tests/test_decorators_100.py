# -*- coding: utf-8 -*-
"""
decorators.py модулийн 100% coverage тестүүд
"""
import pytest
from unittest.mock import patch, MagicMock
from flask import Flask


class TestDecoratorsImport:
    """Модуль импорт тест"""

    def test_import_module(self):
        from app.utils import decorators
        assert decorators is not None

    def test_import_role_required(self):
        from app.utils.decorators import role_required
        assert role_required is not None
        assert callable(role_required)

    def test_import_admin_required(self):
        from app.utils.decorators import admin_required
        assert admin_required is not None
        assert callable(admin_required)

    def test_import_role_or_owner_required(self):
        from app.utils.decorators import role_or_owner_required
        assert role_or_owner_required is not None
        assert callable(role_or_owner_required)

    def test_import_analysis_role_required(self):
        from app.utils.decorators import analysis_role_required
        assert analysis_role_required is not None
        assert callable(analysis_role_required)


class TestRoleRequired:
    """role_required декораторын тест"""

    def test_decorator_returns_callable(self):
        from app.utils.decorators import role_required

        decorator = role_required('admin', 'senior')
        assert callable(decorator)

    @patch('app.utils.decorators.redirect')
    @patch('app.utils.decorators.url_for')
    @patch('app.utils.decorators.abort')
    @patch('app.utils.decorators.flash')
    @patch('app.utils.decorators.current_user')
    def test_unauthenticated_user(self, mock_user, mock_flash, mock_abort, mock_url_for, mock_redirect):
        from app.utils.decorators import role_required

        mock_user.is_authenticated = False
        mock_url_for.return_value = '/login'
        mock_redirect.return_value = 'redirect_response'

        @role_required('admin')
        def test_view():
            return "success"

        app = Flask(__name__)
        app.config['SECRET_KEY'] = 'test'
        with app.test_request_context():
            result = test_view()
            mock_flash.assert_called()
            assert "log in" in mock_flash.call_args[0][0].lower()
            mock_redirect.assert_called()

    @patch('app.utils.decorators.abort')
    @patch('app.utils.decorators.flash')
    @patch('app.utils.decorators.current_user')
    def test_authorized_user(self, mock_user, mock_flash, mock_abort):
        from app.utils.decorators import role_required

        mock_user.is_authenticated = True
        mock_user.role = 'admin'

        @role_required('admin', 'senior')
        def test_view():
            return "success"

        app = Flask(__name__)
        app.config['SECRET_KEY'] = 'test'
        with app.test_request_context():
            result = test_view()
            assert result == "success"

    @patch('app.utils.decorators.abort')
    @patch('app.utils.decorators.flash')
    @patch('app.utils.decorators.current_user')
    def test_unauthorized_user(self, mock_user, mock_flash, mock_abort):
        from app.utils.decorators import role_required

        mock_user.is_authenticated = True
        mock_user.role = 'chemist'

        @role_required('admin', 'senior')
        def test_view():
            return "success"

        app = Flask(__name__)
        app.config['SECRET_KEY'] = 'test'
        with app.test_request_context():
            test_view()
            mock_abort.assert_called_with(403)


class TestAdminRequired:
    """admin_required декораторын тест"""

    @patch('app.utils.decorators.redirect')
    @patch('app.utils.decorators.url_for')
    @patch('app.utils.decorators.abort')
    @patch('app.utils.decorators.flash')
    @patch('app.utils.decorators.current_user')
    def test_unauthenticated_user(self, mock_user, mock_flash, mock_abort, mock_url_for, mock_redirect):
        from app.utils.decorators import admin_required

        mock_user.is_authenticated = False
        mock_url_for.return_value = '/login'
        mock_redirect.return_value = 'redirect_response'

        @admin_required
        def test_view():
            return "success"

        app = Flask(__name__)
        app.config['SECRET_KEY'] = 'test'
        with app.test_request_context():
            result = test_view()
            mock_flash.assert_called()
            assert "log in" in mock_flash.call_args[0][0].lower()
            mock_redirect.assert_called()

    @patch('app.utils.decorators.abort')
    @patch('app.utils.decorators.flash')
    @patch('app.utils.decorators.current_user')
    def test_admin_user(self, mock_user, mock_flash, mock_abort):
        from app.utils.decorators import admin_required

        mock_user.is_authenticated = True
        mock_user.role = 'admin'

        @admin_required
        def test_view():
            return "admin success"

        app = Flask(__name__)
        app.config['SECRET_KEY'] = 'test'
        with app.test_request_context():
            result = test_view()
            assert result == "admin success"

    @patch('app.utils.decorators.abort')
    @patch('app.utils.decorators.flash')
    @patch('app.utils.decorators.current_user')
    def test_non_admin_user(self, mock_user, mock_flash, mock_abort):
        from app.utils.decorators import admin_required

        mock_user.is_authenticated = True
        mock_user.role = 'chemist'

        @admin_required
        def test_view():
            return "success"

        app = Flask(__name__)
        app.config['SECRET_KEY'] = 'test'
        with app.test_request_context():
            test_view()
            mock_abort.assert_called_with(403)
            assert "admin" in mock_flash.call_args[0][0].lower()


class TestRoleOrOwnerRequired:
    """role_or_owner_required декораторын тест"""

    def test_decorator_returns_callable(self):
        from app.utils.decorators import role_or_owner_required

        decorator = role_or_owner_required('admin', owner_check=lambda x: True)
        assert callable(decorator)

    @patch('app.utils.decorators.redirect')
    @patch('app.utils.decorators.url_for')
    @patch('app.utils.decorators.abort')
    @patch('app.utils.decorators.flash')
    @patch('app.utils.decorators.current_user')
    def test_unauthenticated_user(self, mock_user, mock_flash, mock_abort, mock_url_for, mock_redirect):
        from app.utils.decorators import role_or_owner_required

        mock_user.is_authenticated = False
        mock_url_for.return_value = '/login'
        mock_redirect.return_value = 'redirect_response'

        @role_or_owner_required('admin')
        def test_view(item_id):
            return "success"

        app = Flask(__name__)
        app.config['SECRET_KEY'] = 'test'
        with app.test_request_context():
            result = test_view(1)
            mock_flash.assert_called()
            mock_redirect.assert_called()

    @patch('app.utils.decorators.abort')
    @patch('app.utils.decorators.flash')
    @patch('app.utils.decorators.current_user')
    def test_authorized_by_role(self, mock_user, mock_flash, mock_abort):
        from app.utils.decorators import role_or_owner_required

        mock_user.is_authenticated = True
        mock_user.role = 'admin'

        @role_or_owner_required('admin', 'senior')
        def test_view(item_id):
            return f"success {item_id}"

        app = Flask(__name__)
        app.config['SECRET_KEY'] = 'test'
        with app.test_request_context():
            result = test_view(123)
            assert result == "success 123"

    @patch('app.utils.decorators.abort')
    @patch('app.utils.decorators.flash')
    @patch('app.utils.decorators.current_user')
    def test_authorized_by_owner_check(self, mock_user, mock_flash, mock_abort):
        from app.utils.decorators import role_or_owner_required

        mock_user.is_authenticated = True
        mock_user.role = 'chemist'
        mock_user.id = 5

        # Owner check returns True for item_id=5
        def is_owner(item_id):
            return item_id == 5

        @role_or_owner_required('admin', owner_check=is_owner)
        def test_view(item_id):
            return f"owner access {item_id}"

        app = Flask(__name__)
        app.config['SECRET_KEY'] = 'test'
        with app.test_request_context():
            result = test_view(5)
            assert result == "owner access 5"

    @patch('app.utils.decorators.abort')
    @patch('app.utils.decorators.flash')
    @patch('app.utils.decorators.current_user')
    def test_unauthorized(self, mock_user, mock_flash, mock_abort):
        from app.utils.decorators import role_or_owner_required

        mock_user.is_authenticated = True
        mock_user.role = 'chemist'

        def is_owner(item_id):
            return False

        @role_or_owner_required('admin', owner_check=is_owner)
        def test_view(item_id):
            return "success"

        app = Flask(__name__)
        app.config['SECRET_KEY'] = 'test'
        with app.test_request_context():
            test_view(999)
            mock_abort.assert_called_with(403)

    @patch('app.utils.decorators.abort')
    @patch('app.utils.decorators.flash')
    @patch('app.utils.decorators.current_user')
    def test_no_owner_check_provided(self, mock_user, mock_flash, mock_abort):
        from app.utils.decorators import role_or_owner_required

        mock_user.is_authenticated = True
        mock_user.role = 'chemist'

        # No owner_check provided
        @role_or_owner_required('admin')
        def test_view(item_id):
            return "success"

        app = Flask(__name__)
        app.config['SECRET_KEY'] = 'test'
        with app.test_request_context():
            test_view(1)
            mock_abort.assert_called_with(403)


class TestAnalysisRoleRequired:
    """analysis_role_required декораторын тест"""

    def test_decorator_returns_callable(self):
        from app.utils.decorators import analysis_role_required

        decorator = analysis_role_required()
        assert callable(decorator)

    def test_default_roles(self):
        from app.utils.decorators import analysis_role_required

        # Default roles should be set
        decorator = analysis_role_required()
        # The decorator should accept the default roles
        assert decorator is not None

    def test_custom_roles(self):
        from app.utils.decorators import analysis_role_required

        decorator = analysis_role_required(['admin', 'senior'])
        assert callable(decorator)

    @patch('app.utils.decorators.redirect')
    @patch('app.utils.decorators.url_for')
    @patch('app.utils.decorators.abort')
    @patch('app.utils.decorators.current_user')
    def test_unauthenticated_user(self, mock_user, mock_abort, mock_url_for, mock_redirect):
        from app.utils.decorators import analysis_role_required

        mock_user.is_authenticated = False
        mock_url_for.return_value = '/login'
        mock_redirect.return_value = 'redirect_response'

        @analysis_role_required()
        def test_view():
            return "success"

        app = Flask(__name__)
        app.config['SECRET_KEY'] = 'test'
        with app.test_request_context():
            result = test_view()
            mock_redirect.assert_called()

    @patch('app.utils.decorators.abort')
    @patch('app.utils.decorators.current_user')
    def test_authorized_chemist(self, mock_user, mock_abort):
        from app.utils.decorators import analysis_role_required

        mock_user.is_authenticated = True
        mock_user.role = 'chemist'

        @analysis_role_required()
        def test_view():
            return "chemist success"

        app = Flask(__name__)
        app.config['SECRET_KEY'] = 'test'
        with app.test_request_context():
            result = test_view()
            assert result == "chemist success"

    @patch('app.utils.decorators.abort')
    @patch('app.utils.decorators.current_user')
    def test_authorized_admin(self, mock_user, mock_abort):
        from app.utils.decorators import analysis_role_required

        mock_user.is_authenticated = True
        mock_user.role = 'admin'

        @analysis_role_required(['admin'])
        def test_view():
            return "admin only"

        app = Flask(__name__)
        app.config['SECRET_KEY'] = 'test'
        with app.test_request_context():
            result = test_view()
            assert result == "admin only"

    @patch('app.utils.decorators.abort')
    @patch('app.utils.decorators.current_user')
    def test_unauthorized_role(self, mock_user, mock_abort):
        from app.utils.decorators import analysis_role_required

        mock_user.is_authenticated = True
        mock_user.role = 'guest'

        @analysis_role_required(['admin', 'senior'])
        def test_view():
            return "success"

        app = Flask(__name__)
        app.config['SECRET_KEY'] = 'test'
        with app.test_request_context():
            test_view()
            mock_abort.assert_called_with(403)

    @patch('app.utils.decorators.abort')
    @patch('app.utils.decorators.current_user')
    def test_prep_role_allowed_by_default(self, mock_user, mock_abort):
        from app.utils.decorators import analysis_role_required

        mock_user.is_authenticated = True
        mock_user.role = 'prep'

        @analysis_role_required()
        def test_view():
            return "prep success"

        app = Flask(__name__)
        app.config['SECRET_KEY'] = 'test'
        with app.test_request_context():
            result = test_view()
            assert result == "prep success"

    @patch('app.utils.decorators.abort')
    @patch('app.utils.decorators.current_user')
    def test_manager_role_allowed_by_default(self, mock_user, mock_abort):
        from app.utils.decorators import analysis_role_required

        mock_user.is_authenticated = True
        mock_user.role = 'manager'

        @analysis_role_required()
        def test_view():
            return "manager success"

        app = Flask(__name__)
        app.config['SECRET_KEY'] = 'test'
        with app.test_request_context():
            result = test_view()
            assert result == "manager success"


class TestDecoratorFunctionPreservation:
    """Декораторууд функцийн metadata хадгалж байгаа эсэхийг шалгах"""

    def test_role_required_preserves_name(self):
        from app.utils.decorators import role_required

        @role_required('admin')
        def my_special_function():
            """My docstring"""
            pass

        assert my_special_function.__name__ == 'my_special_function'

    def test_admin_required_preserves_name(self):
        from app.utils.decorators import admin_required

        @admin_required
        def admin_only_function():
            """Admin docstring"""
            pass

        assert admin_only_function.__name__ == 'admin_only_function'

    def test_role_or_owner_preserves_name(self):
        from app.utils.decorators import role_or_owner_required

        @role_or_owner_required('admin')
        def owner_function(item_id):
            """Owner docstring"""
            pass

        assert owner_function.__name__ == 'owner_function'

    def test_analysis_role_preserves_name(self):
        from app.utils.decorators import analysis_role_required

        @analysis_role_required()
        def analysis_function():
            """Analysis docstring"""
            pass

        assert analysis_function.__name__ == 'analysis_function'
