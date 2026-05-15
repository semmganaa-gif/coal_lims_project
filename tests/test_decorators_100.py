# -*- coding: utf-8 -*-
"""
decorators.py модулийн 100% coverage тестүүд.

Real Flask test client + LoginManager-ээр бодит зан төлвийг шалгана. Mock-аар
дотоод дуудлагыг шалгахын оронд route-ийн ажиглагдаж буй output-ыг (status,
redirect, JSON) шалгана — тиймээс decorator-ын дотоод implementation өөрчлөгдөх
үед тэст эвдрэхгүй (root-cause stability).
"""
import pytest
from unittest.mock import MagicMock
from flask import Flask
from flask_babel import Babel
from flask_login import LoginManager


def _make_app(role: str | None = None, authenticated: bool = True):
    """Decorator-той route бүхий жижиг Flask app үүсгэх.

    Args:
        role: Hэвтэрсэн хэрэглэгчийн role (None бол anonymous).
        authenticated: Authenticated эсэх.
    """
    app = Flask(__name__)
    app.config["TESTING"] = True
    app.config["SECRET_KEY"] = "test"
    app.config["WTF_CSRF_ENABLED"] = False
    Babel(app)

    lm = LoginManager(app)

    user = MagicMock()
    user.is_authenticated = authenticated
    user.is_active = authenticated
    user.is_anonymous = not authenticated
    user.get_id = lambda: "1" if authenticated else None
    user.role = role
    user.id = 5

    @lm.user_loader
    def load_user(_uid):
        return user

    # Login user via session by patching current_user globally for this request
    @app.before_request
    def _login_user():
        from flask_login import login_user
        if authenticated:
            login_user(user)

    @app.route('/login')
    def login_page():
        return "login page", 200

    @app.route('/')
    def home():
        return "home", 200

    return app, user


# ─────────────────────────────────────────────────────────────
# Import sanity
# ─────────────────────────────────────────────────────────────
class TestDecoratorsImport:
    def test_import_module(self):
        from app.utils import decorators
        assert decorators is not None

    def test_import_role_required(self):
        from app.utils.decorators import role_required
        assert callable(role_required)

    def test_import_admin_required(self):
        from app.utils.decorators import admin_required
        assert callable(admin_required)

    def test_import_role_or_owner_required(self):
        from app.utils.decorators import role_or_owner_required
        assert callable(role_or_owner_required)

    def test_import_analysis_role_required(self):
        from app.utils.decorators import analysis_role_required
        assert callable(analysis_role_required)

    def test_import_role_denied_response_helper(self):
        from app.utils.decorators import _role_denied_response
        assert callable(_role_denied_response)


# ─────────────────────────────────────────────────────────────
# role_required
# ─────────────────────────────────────────────────────────────
class TestRoleRequired:
    def test_authorized_role_passes(self):
        from app.utils.decorators import role_required

        app, _ = _make_app(role='admin')

        @app.route('/protected')
        @role_required('admin', 'senior')
        def view():
            return "OK", 200

        client = app.test_client()
        resp = client.get('/protected')
        assert resp.status_code == 200
        assert resp.data == b"OK"

    def test_unauthorized_role_ui_redirects(self):
        """UI route (non-/api/) — flash + redirect."""
        from app.utils.decorators import role_required

        app, _ = _make_app(role='chemist')

        @app.route('/protected')
        @role_required('admin', 'senior')
        def view():
            return "OK", 200

        client = app.test_client()
        resp = client.get('/protected')
        assert resp.status_code == 302  # redirect

    def test_unauthorized_role_api_returns_json_403(self):
        """API route (/api/ prefix) — JSON 403."""
        from app.utils.decorators import role_required

        app, _ = _make_app(role='chemist')

        @app.route('/api/protected')
        @role_required('admin', 'senior')
        def view():
            return "OK", 200

        client = app.test_client()
        resp = client.get('/api/protected')
        assert resp.status_code == 403
        assert resp.is_json
        assert resp.json["error"] == "Permission denied"


# ─────────────────────────────────────────────────────────────
# admin_required
# ─────────────────────────────────────────────────────────────
class TestAdminRequired:
    def test_admin_passes(self):
        from app.utils.decorators import admin_required

        app, _ = _make_app(role='admin')

        @app.route('/admin-only')
        @admin_required
        def view():
            return "ADMIN OK", 200

        client = app.test_client()
        resp = client.get('/admin-only')
        assert resp.status_code == 200

    def test_non_admin_ui_redirects(self):
        from app.utils.decorators import admin_required

        app, _ = _make_app(role='chemist')

        @app.route('/admin-only')
        @admin_required
        def view():
            return "ADMIN OK", 200

        client = app.test_client()
        resp = client.get('/admin-only')
        assert resp.status_code == 302

    def test_non_admin_api_returns_403_json(self):
        from app.utils.decorators import admin_required

        app, _ = _make_app(role='chemist')

        @app.route('/api/admin-only')
        @admin_required
        def view():
            return "ADMIN OK", 200

        client = app.test_client()
        resp = client.get('/api/admin-only')
        assert resp.status_code == 403
        assert resp.json["error"] == "Permission denied"


# ─────────────────────────────────────────────────────────────
# senior_or_admin_required
# ─────────────────────────────────────────────────────────────
class TestSeniorOrAdminRequired:
    @pytest.mark.parametrize("role", ['senior', 'admin'])
    def test_allowed_roles_pass(self, role):
        from app.utils.decorators import senior_or_admin_required

        app, _ = _make_app(role=role)

        @app.route('/restricted')
        @senior_or_admin_required
        def view():
            return "OK", 200

        client = app.test_client()
        resp = client.get('/restricted')
        assert resp.status_code == 200

    def test_chemist_denied(self):
        from app.utils.decorators import senior_or_admin_required

        app, _ = _make_app(role='chemist')

        @app.route('/restricted')
        @senior_or_admin_required
        def view():
            return "OK", 200

        client = app.test_client()
        resp = client.get('/restricted')
        assert resp.status_code == 302


# ─────────────────────────────────────────────────────────────
# role_or_owner_required
# ─────────────────────────────────────────────────────────────
class TestRoleOrOwnerRequired:
    def test_authorized_by_role(self):
        from app.utils.decorators import role_or_owner_required

        app, _ = _make_app(role='admin')

        @app.route('/item/<int:item_id>')
        @role_or_owner_required('admin', 'senior')
        def view(item_id):
            return f"OK {item_id}", 200

        client = app.test_client()
        resp = client.get('/item/123')
        assert resp.status_code == 200
        assert b"OK 123" in resp.data

    def test_authorized_by_owner_check(self):
        from app.utils.decorators import role_or_owner_required

        app, user = _make_app(role='chemist')

        @app.route('/item/<int:item_id>')
        @role_or_owner_required('admin', owner_check=lambda item_id: item_id == 5)
        def view(item_id):
            return f"owner {item_id}", 200

        client = app.test_client()
        resp = client.get('/item/5')
        assert resp.status_code == 200
        assert b"owner 5" in resp.data

    def test_unauthorized_redirects(self):
        from app.utils.decorators import role_or_owner_required

        app, _ = _make_app(role='chemist')

        @app.route('/item/<int:item_id>')
        @role_or_owner_required('admin', owner_check=lambda item_id: False)
        def view(item_id):
            return "OK", 200

        client = app.test_client()
        resp = client.get('/item/999')
        assert resp.status_code == 302

    def test_no_owner_check_provided(self):
        from app.utils.decorators import role_or_owner_required

        app, _ = _make_app(role='chemist')

        @app.route('/item/<int:item_id>')
        @role_or_owner_required('admin')
        def view(item_id):
            return "OK", 200

        client = app.test_client()
        resp = client.get('/item/1')
        assert resp.status_code == 302


# ─────────────────────────────────────────────────────────────
# analysis_role_required
# ─────────────────────────────────────────────────────────────
class TestAnalysisRoleRequired:
    def test_decorator_returns_callable(self):
        from app.utils.decorators import analysis_role_required
        assert callable(analysis_role_required())

    def test_custom_roles_callable(self):
        from app.utils.decorators import analysis_role_required
        assert callable(analysis_role_required(['admin', 'senior']))

    @pytest.mark.parametrize("role", ['chemist', 'senior', 'manager', 'admin', 'prep'])
    def test_default_roles_pass(self, role):
        from app.utils.decorators import analysis_role_required

        app, _ = _make_app(role=role)

        @app.route('/analysis-only')
        @analysis_role_required()
        def view():
            return "OK", 200

        client = app.test_client()
        resp = client.get('/analysis-only')
        assert resp.status_code == 200

    def test_unauthorized_role_redirects(self):
        from app.utils.decorators import analysis_role_required

        app, _ = _make_app(role='guest')

        @app.route('/analysis-only')
        @analysis_role_required(['admin', 'senior'])
        def view():
            return "OK", 200

        client = app.test_client()
        resp = client.get('/analysis-only')
        assert resp.status_code == 302


# ─────────────────────────────────────────────────────────────
# Function metadata (functools.wraps)
# ─────────────────────────────────────────────────────────────
class TestDecoratorFunctionPreservation:
    def test_role_required_preserves_name(self):
        from app.utils.decorators import role_required

        @role_required('admin')
        def my_special_function():
            """Docstring"""

        assert my_special_function.__name__ == 'my_special_function'

    def test_admin_required_preserves_name(self):
        from app.utils.decorators import admin_required

        @admin_required
        def admin_only_function():
            """Docstring"""

        assert admin_only_function.__name__ == 'admin_only_function'

    def test_role_or_owner_preserves_name(self):
        from app.utils.decorators import role_or_owner_required

        @role_or_owner_required('admin')
        def owner_function(item_id):
            """Docstring"""

        assert owner_function.__name__ == 'owner_function'

    def test_analysis_role_preserves_name(self):
        from app.utils.decorators import analysis_role_required

        @analysis_role_required()
        def analysis_function():
            """Docstring"""

        assert analysis_function.__name__ == 'analysis_function'


# ─────────────────────────────────────────────────────────────
# _role_denied_response helper
# ─────────────────────────────────────────────────────────────
class TestRoleDeniedResponse:
    def test_ui_path_returns_redirect(self):
        from app.utils.decorators import _role_denied_response

        app = Flask(__name__)
        app.config["SECRET_KEY"] = "test"
        Babel(app)

        @app.route('/ui-page')
        def trigger():
            return _role_denied_response()

        client = app.test_client()
        resp = client.get('/ui-page')
        assert resp.status_code == 302

    def test_api_path_returns_json_403(self):
        from app.utils.decorators import _role_denied_response

        app = Flask(__name__)
        app.config["SECRET_KEY"] = "test"
        Babel(app)

        @app.route('/api/endpoint')
        def trigger():
            return _role_denied_response()

        client = app.test_client()
        resp = client.get('/api/endpoint')
        assert resp.status_code == 403
        assert resp.is_json
        assert resp.json["status"] == 403

    def test_api_accept_header_returns_json(self):
        """JSON Accept header байвал JSON 403 — path-аас үл хамаарна."""
        from app.utils.decorators import _role_denied_response

        app = Flask(__name__)
        app.config["SECRET_KEY"] = "test"
        Babel(app)

        @app.route('/some-route')
        def trigger():
            return _role_denied_response()

        client = app.test_client()
        resp = client.get('/some-route', headers={"Accept": "application/json"})
        assert resp.status_code == 403
        assert resp.is_json
