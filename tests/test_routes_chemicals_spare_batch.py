# tests/test_routes_chemicals_spare_batch.py
# -*- coding: utf-8 -*-
"""Comprehensive tests for chemicals (api, crud, waste) and spare_parts (api, crud) routes.

Targets 80%+ coverage for:
  - app/routes/chemicals/api.py
  - app/routes/chemicals/crud.py
  - app/routes/chemicals/waste.py
  - app/routes/spare_parts/api.py
  - app/routes/spare_parts/crud.py
"""

import json
import types
from datetime import datetime
from unittest.mock import MagicMock, patch, PropertyMock

import pytest
from flask import Flask


# ---------------------------------------------------------------------------
# Helpers / Stubs
# ---------------------------------------------------------------------------

class _FakeUser:
    """Minimal flask-login user stub."""

    def __init__(self, role="admin", user_id=1, username="tester"):
        self.id = user_id
        self.username = username
        self.role = role
        self.is_authenticated = True
        self.is_active = True
        self.is_anonymous = False

    def get_id(self):
        return str(self.id)


class _ConsumeResult:
    """Mimics service consume_chemical_stock result object."""

    def __init__(self, success=True, error=None, new_quantity=90, chemical_status="active"):
        self.success = success
        self.error = error
        self.new_quantity = new_quantity
        self.chemical_status = chemical_status


class _BulkResult:
    """Mimics service consume_bulk result object."""

    def __init__(self, success=True, error=None, count=2, errors=None):
        self.success = success
        self.error = error
        self.count = count
        self.errors = errors or []


def _make_chemical(**overrides):
    c = MagicMock()
    c.id = overrides.get("id", 1)
    c.name = overrides.get("name", "HCl")
    c.unit = overrides.get("unit", "mL")
    return c


def _make_waste(**overrides):
    w = MagicMock()
    w.id = overrides.get("id", 1)
    w.name_mn = overrides.get("name_mn", "TestWaste")
    w.is_active = overrides.get("is_active", True)
    w.lab_type = overrides.get("lab_type", "all")
    return w


def _noop_decorator(*args, **kwargs):
    """Pass-through decorator used to stub limiter.limit."""
    def _dec(fn):
        return fn
    if args and callable(args[0]):
        return args[0]
    return _dec


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def app():
    """Create a Flask app with both blueprints registered, all heavy deps mocked."""

    # -- Mock the `app` package (db, limiter) BEFORE importing blueprints --
    mock_db = MagicMock()
    mock_db.session = MagicMock()
    mock_db.session.get = MagicMock(return_value=None)
    mock_db.session.commit = MagicMock()
    mock_db.session.rollback = MagicMock()
    mock_db.session.add = MagicMock()

    mock_limiter = MagicMock()
    mock_limiter.limit = MagicMock(side_effect=_noop_decorator)

    # Patch at module level so blueprint init picks up stubs
    with patch.dict("sys.modules", {}):
        pass  # ensure clean

    with (
        patch("app.db", mock_db),
        patch("app.limiter", mock_limiter),
    ):
        # Create a fresh Flask app
        flask_app = Flask(__name__)
        flask_app.config["TESTING"] = True
        flask_app.config["SECRET_KEY"] = "test-secret"
        flask_app.config["WTF_CSRF_ENABLED"] = False
        flask_app.config["SERVER_NAME"] = "localhost"

        # Mock login_manager
        from flask_login import LoginManager
        lm = LoginManager()
        lm.init_app(flask_app)

        @lm.user_loader
        def _load(uid):
            return _FakeUser()

        # Import and register blueprints (they use `from app import db, limiter`)
        from app.routes.chemicals import chemicals_bp
        from app.routes.spare_parts import spare_parts_bp

        # Avoid duplicate blueprint registration across tests
        if "chemicals" not in flask_app.blueprints:
            flask_app.register_blueprint(chemicals_bp)
        if "spare_parts" not in flask_app.blueprints:
            flask_app.register_blueprint(spare_parts_bp)

        flask_app._mock_db = mock_db

        yield flask_app


@pytest.fixture()
def client(app):
    return app.test_client()


@pytest.fixture()
def auth_client(client, app):
    """Client that is always logged-in as admin."""
    with app.test_request_context():
        with client.session_transaction() as sess:
            sess["_user_id"] = "1"
    return client


def _login(client, app, role="admin"):
    """Helper to force login_required to pass with a given role."""
    user = _FakeUser(role=role)
    with patch("flask_login.utils._get_user", return_value=user):
        yield client, user


# ---------------------------------------------------------------------------
# ===== CHEMICALS API TESTS =====
# ---------------------------------------------------------------------------

class TestChemicalsApi:
    """Tests for app/routes/chemicals/api.py"""

    # -- /api/list --
    @patch("app.routes.chemicals.api.get_chemical_api_list", return_value=[{"id": 1}])
    def test_api_list_success(self, mock_svc, client, app):
        with patch("flask_login.utils._get_user", return_value=_FakeUser()):
            resp = client.get("/chemicals/api/list?lab=coal&category=acid&status=active&include_disposed=true")
        assert resp.status_code == 200
        data = resp.get_json()
        assert isinstance(data, list)
        mock_svc.assert_called_once_with(lab="coal", category="acid", status="active", include_disposed=True)

    @patch("app.routes.chemicals.api.get_chemical_api_list", return_value=[])
    def test_api_list_defaults(self, mock_svc, client, app):
        with patch("flask_login.utils._get_user", return_value=_FakeUser()):
            resp = client.get("/chemicals/api/list")
        assert resp.status_code == 200
        mock_svc.assert_called_once_with(lab="all", category="all", status="all", include_disposed=False)

    # -- /api/low_stock --
    @patch("app.routes.chemicals.api.get_low_stock_chemicals", return_value=[])
    def test_api_low_stock(self, mock_svc, client, app):
        with patch("flask_login.utils._get_user", return_value=_FakeUser()):
            resp = client.get("/chemicals/api/low_stock?lab=water")
        assert resp.status_code == 200
        mock_svc.assert_called_once_with(lab="water")

    # -- /api/expiring --
    @patch("app.routes.chemicals.api.get_expiring_chemicals", return_value=[])
    def test_api_expiring_with_days(self, mock_svc, client, app):
        with patch("flask_login.utils._get_user", return_value=_FakeUser()):
            resp = client.get("/chemicals/api/expiring?days=60")
        assert resp.status_code == 200
        mock_svc.assert_called_once_with(lab="all", days=60)

    @patch("app.routes.chemicals.api.get_expiring_chemicals", return_value=[])
    def test_api_expiring_invalid_days(self, mock_svc, client, app):
        with patch("flask_login.utils._get_user", return_value=_FakeUser()):
            resp = client.get("/chemicals/api/expiring?days=abc")
        assert resp.status_code == 200
        mock_svc.assert_called_once_with(lab="all", days=30)

    # -- /api/consume --
    @patch("app.routes.chemicals.api.db")
    @patch("app.routes.chemicals.api.consume_chemical_stock")
    @patch("app.routes.chemicals.api.ChemicalRepository")
    def test_api_consume_success(self, mock_repo, mock_consume, mock_db, client, app):
        chem = _make_chemical()
        mock_repo.get_by_id.return_value = chem
        mock_consume.return_value = _ConsumeResult(success=True, new_quantity=90)

        with patch("flask_login.utils._get_user", return_value=_FakeUser()):
            resp = client.post(
                "/chemicals/api/consume",
                data=json.dumps({"chemical_id": 1, "quantity_used": 10, "purpose": "test", "sample_id": "5"}),
                content_type="application/json",
            )
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["success"] is True

    def test_api_consume_invalid_quantity_non_numeric(self, client, app):
        with patch("flask_login.utils._get_user", return_value=_FakeUser()):
            resp = client.post(
                "/chemicals/api/consume",
                data=json.dumps({"chemical_id": 1, "quantity_used": "abc"}),
                content_type="application/json",
            )
        assert resp.status_code == 400
        data = resp.get_json()
        assert data["success"] is False

    def test_api_consume_missing_chemical_id(self, client, app):
        with patch("flask_login.utils._get_user", return_value=_FakeUser()):
            resp = client.post(
                "/chemicals/api/consume",
                data=json.dumps({"quantity_used": 10}),
                content_type="application/json",
            )
        assert resp.status_code == 400

    def test_api_consume_zero_quantity(self, client, app):
        with patch("flask_login.utils._get_user", return_value=_FakeUser()):
            resp = client.post(
                "/chemicals/api/consume",
                data=json.dumps({"chemical_id": 1, "quantity_used": 0}),
                content_type="application/json",
            )
        assert resp.status_code == 400

    @patch("app.routes.chemicals.api.ChemicalRepository")
    def test_api_consume_chemical_not_found(self, mock_repo, client, app):
        mock_repo.get_by_id.return_value = None
        with patch("flask_login.utils._get_user", return_value=_FakeUser()):
            resp = client.post(
                "/chemicals/api/consume",
                data=json.dumps({"chemical_id": 999, "quantity_used": 5}),
                content_type="application/json",
            )
        assert resp.status_code == 404

    @patch("app.routes.chemicals.api.db")
    @patch("app.routes.chemicals.api.consume_chemical_stock")
    @patch("app.routes.chemicals.api.ChemicalRepository")
    def test_api_consume_service_error(self, mock_repo, mock_consume, mock_db, client, app):
        mock_repo.get_by_id.return_value = _make_chemical()
        mock_consume.return_value = _ConsumeResult(success=False, error="Insufficient stock")
        with patch("flask_login.utils._get_user", return_value=_FakeUser()):
            resp = client.post(
                "/chemicals/api/consume",
                data=json.dumps({"chemical_id": 1, "quantity_used": 10}),
                content_type="application/json",
            )
        assert resp.status_code == 400

    @patch("app.routes.chemicals.api.db")
    @patch("app.routes.chemicals.api.consume_chemical_stock")
    @patch("app.routes.chemicals.api.ChemicalRepository")
    def test_api_consume_commit_error(self, mock_repo, mock_consume, mock_db, client, app):
        from sqlalchemy.exc import SQLAlchemyError
        mock_repo.get_by_id.return_value = _make_chemical()
        mock_consume.return_value = _ConsumeResult(success=True)
        mock_db.session.commit.side_effect = SQLAlchemyError("db error")
        with patch("flask_login.utils._get_user", return_value=_FakeUser()):
            resp = client.post(
                "/chemicals/api/consume",
                data=json.dumps({"chemical_id": 1, "quantity_used": 5}),
                content_type="application/json",
            )
        assert resp.status_code == 500

    @patch("app.routes.chemicals.api.db")
    @patch("app.routes.chemicals.api.consume_chemical_stock", side_effect=ValueError("bad"))
    @patch("app.routes.chemicals.api.ChemicalRepository")
    def test_api_consume_value_error(self, mock_repo, mock_consume, mock_db, client, app):
        mock_repo.get_by_id.return_value = _make_chemical()
        with patch("flask_login.utils._get_user", return_value=_FakeUser()):
            resp = client.post(
                "/chemicals/api/consume",
                data=json.dumps({"chemical_id": 1, "quantity_used": 5}),
                content_type="application/json",
            )
        assert resp.status_code == 500

    @patch("app.routes.chemicals.api.db")
    @patch("app.routes.chemicals.api.consume_chemical_stock")
    @patch("app.routes.chemicals.api.ChemicalRepository")
    def test_api_consume_invalid_sample_id(self, mock_repo, mock_consume, mock_db, client, app):
        """sample_id that cannot be parsed as int should be silently ignored."""
        mock_repo.get_by_id.return_value = _make_chemical()
        mock_consume.return_value = _ConsumeResult(success=True)
        with patch("flask_login.utils._get_user", return_value=_FakeUser()):
            resp = client.post(
                "/chemicals/api/consume",
                data=json.dumps({"chemical_id": 1, "quantity_used": 5, "sample_id": "bad"}),
                content_type="application/json",
            )
        assert resp.status_code == 200

    def test_api_consume_empty_json(self, client, app):
        with patch("flask_login.utils._get_user", return_value=_FakeUser()):
            resp = client.post(
                "/chemicals/api/consume",
                data="{}",
                content_type="application/json",
            )
        # Should handle gracefully - missing chemical_id
        assert resp.status_code == 400

    # -- /api/search --
    @patch("app.routes.chemicals.api.search_chemicals", return_value=[])
    def test_api_search(self, mock_svc, client, app):
        with patch("flask_login.utils._get_user", return_value=_FakeUser()):
            resp = client.get("/chemicals/api/search?q=HCl&lab=coal&limit=5")
        assert resp.status_code == 200
        mock_svc.assert_called_once_with(q="HCl", lab="coal", limit=5)

    @patch("app.routes.chemicals.api.search_chemicals", return_value=[])
    def test_api_search_invalid_limit(self, mock_svc, client, app):
        with patch("flask_login.utils._get_user", return_value=_FakeUser()):
            resp = client.get("/chemicals/api/search?q=x&limit=bad")
        assert resp.status_code == 200
        mock_svc.assert_called_once_with(q="x", lab="all", limit=20)

    # -- /api/stats --
    @patch("app.routes.chemicals.api.get_chemical_stats", return_value={"total": 10})
    def test_api_stats(self, mock_svc, client, app):
        with patch("flask_login.utils._get_user", return_value=_FakeUser()):
            resp = client.get("/chemicals/api/stats?lab=coal")
        assert resp.status_code == 200
        mock_svc.assert_called_once_with(lab="coal")

    # -- /api/usage_history --
    @patch("app.routes.chemicals.api.get_usage_history", return_value={"items": [], "count": 0})
    def test_api_usage_history_success(self, mock_svc, client, app):
        with patch("flask_login.utils._get_user", return_value=_FakeUser()):
            resp = client.get("/chemicals/api/usage_history?chemical_id=5&limit=10")
        assert resp.status_code == 200
        mock_svc.assert_called_once()

    @patch("app.routes.chemicals.api.get_usage_history", return_value={"items": []})
    def test_api_usage_history_invalid_limit(self, mock_svc, client, app):
        with patch("flask_login.utils._get_user", return_value=_FakeUser()):
            resp = client.get("/chemicals/api/usage_history?limit=bad")
        assert resp.status_code == 200

    def test_api_usage_history_invalid_chemical_id(self, client, app):
        with patch("flask_login.utils._get_user", return_value=_FakeUser()):
            resp = client.get("/chemicals/api/usage_history?chemical_id=abc")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["items"] == []

    @patch("app.routes.chemicals.api.get_usage_history", side_effect=ValueError("bad date"))
    def test_api_usage_history_bad_date(self, mock_svc, client, app):
        with patch("flask_login.utils._get_user", return_value=_FakeUser()):
            resp = client.get("/chemicals/api/usage_history?start_date=bad")
        assert resp.status_code == 400

    # -- /api/consume_bulk --
    @patch("app.routes.chemicals.api.db")
    @patch("app.routes.chemicals.api.consume_bulk")
    def test_api_consume_bulk_success(self, mock_bulk, mock_db, client, app):
        mock_bulk.return_value = _BulkResult(success=True, count=2)
        with patch("flask_login.utils._get_user", return_value=_FakeUser()):
            resp = client.post(
                "/chemicals/api/consume_bulk",
                data=json.dumps({
                    "items": [{"chemical_id": 1, "quantity_used": 5}],
                    "purpose": "test",
                    "sample_id": "10",
                }),
                content_type="application/json",
            )
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["success"] is True

    @patch("app.routes.chemicals.api.db")
    @patch("app.routes.chemicals.api.consume_bulk")
    def test_api_consume_bulk_service_error(self, mock_bulk, mock_db, client, app):
        mock_bulk.return_value = _BulkResult(success=False, error="Something wrong")
        with patch("flask_login.utils._get_user", return_value=_FakeUser()):
            resp = client.post(
                "/chemicals/api/consume_bulk",
                data=json.dumps({"items": [{"chemical_id": 1, "quantity_used": 5}]}),
                content_type="application/json",
            )
        assert resp.status_code == 400

    @patch("app.routes.chemicals.api.db")
    @patch("app.routes.chemicals.api.consume_bulk")
    def test_api_consume_bulk_commit_error(self, mock_bulk, mock_db, client, app):
        from sqlalchemy.exc import SQLAlchemyError
        mock_bulk.return_value = _BulkResult(success=True, count=1)
        mock_db.session.commit.side_effect = SQLAlchemyError("db err")
        with patch("flask_login.utils._get_user", return_value=_FakeUser()):
            resp = client.post(
                "/chemicals/api/consume_bulk",
                data=json.dumps({"items": [{"chemical_id": 1, "quantity_used": 5}]}),
                content_type="application/json",
            )
        assert resp.status_code == 500

    @patch("app.routes.chemicals.api.db")
    @patch("app.routes.chemicals.api.consume_bulk", side_effect=TypeError("bad"))
    def test_api_consume_bulk_type_error(self, mock_bulk, mock_db, client, app):
        with patch("flask_login.utils._get_user", return_value=_FakeUser()):
            resp = client.post(
                "/chemicals/api/consume_bulk",
                data=json.dumps({"items": []}),
                content_type="application/json",
            )
        assert resp.status_code == 500

    @patch("app.routes.chemicals.api.db")
    @patch("app.routes.chemicals.api.consume_bulk")
    def test_api_consume_bulk_invalid_sample_id(self, mock_bulk, mock_db, client, app):
        mock_bulk.return_value = _BulkResult(success=True, count=1)
        with patch("flask_login.utils._get_user", return_value=_FakeUser()):
            resp = client.post(
                "/chemicals/api/consume_bulk",
                data=json.dumps({"items": [{"chemical_id": 1, "quantity_used": 5}], "sample_id": "bad"}),
                content_type="application/json",
            )
        assert resp.status_code == 200


# ---------------------------------------------------------------------------
# ===== CHEMICALS CRUD TESTS =====
# ---------------------------------------------------------------------------

class TestChemicalsCrud:
    """Tests for app/routes/chemicals/crud.py"""

    # -- / and /list --
    @patch("app.routes.chemicals.crud.get_chemical_stats_summary", return_value={})
    @patch("app.routes.chemicals.crud.get_chemical_list", return_value=[])
    @patch("app.routes.chemicals.crud.render_template", return_value="ok")
    def test_chemical_list(self, mock_rt, mock_list, mock_stats, client, app):
        with patch("flask_login.utils._get_user", return_value=_FakeUser()):
            resp = client.get("/chemicals/?lab=coal&category=acid&status=active&view=low")
        assert resp.status_code == 200
        mock_list.assert_called_once()
        mock_stats.assert_called_once()

    @patch("app.routes.chemicals.crud.get_chemical_stats_summary", return_value={})
    @patch("app.routes.chemicals.crud.get_chemical_list", return_value=[])
    @patch("app.routes.chemicals.crud.render_template", return_value="ok")
    def test_chemical_list_route(self, mock_rt, mock_list, mock_stats, client, app):
        with patch("flask_login.utils._get_user", return_value=_FakeUser()):
            resp = client.get("/chemicals/list")
        assert resp.status_code == 200

    # -- /<int:id> --
    @patch("app.routes.chemicals.crud.render_template", return_value="ok")
    @patch("app.routes.chemicals.crud.ChemicalLog")
    @patch("app.routes.chemicals.crud.ChemicalUsage")
    @patch("app.routes.chemicals.crud.ChemicalRepository")
    def test_chemical_detail_found(self, mock_repo, mock_usage, mock_log, mock_rt, client, app):
        chem = _make_chemical()
        mock_repo.get_by_id.return_value = chem
        # Mock query chains
        mock_usage.query.filter_by.return_value.order_by.return_value.limit.return_value.all.return_value = []
        mock_log.query.filter_by.return_value.order_by.return_value.limit.return_value.all.return_value = []
        with patch("flask_login.utils._get_user", return_value=_FakeUser()):
            resp = client.get("/chemicals/1")
        assert resp.status_code == 200

    @patch("app.routes.chemicals.crud.ChemicalRepository")
    def test_chemical_detail_not_found(self, mock_repo, client, app):
        mock_repo.get_by_id.return_value = None
        with patch("flask_login.utils._get_user", return_value=_FakeUser()):
            resp = client.get("/chemicals/999")
        assert resp.status_code == 404

    # -- /add GET --
    @patch("app.routes.chemicals.crud.render_template", return_value="ok")
    def test_add_chemical_get(self, mock_rt, client, app):
        with patch("flask_login.utils._get_user", return_value=_FakeUser(role="admin")):
            resp = client.get("/chemicals/add")
        assert resp.status_code == 200

    def test_add_chemical_forbidden(self, client, app):
        with patch("flask_login.utils._get_user", return_value=_FakeUser(role="viewer")):
            resp = client.get("/chemicals/add")
        assert resp.status_code == 302  # redirect

    # -- /add POST success --
    @patch("app.routes.chemicals.crud.render_template", return_value="ok")
    @patch("app.routes.chemicals.crud.safe_commit", return_value=True)
    @patch("app.routes.chemicals.crud.create_chemical")
    def test_add_chemical_post_success(self, mock_create, mock_commit, mock_rt, client, app):
        chem = _make_chemical()
        mock_create.return_value = chem
        with patch("flask_login.utils._get_user", return_value=_FakeUser(role="chemist")):
            resp = client.post("/chemicals/add", data={"name": "HCl", "quantity": "10"})
        assert resp.status_code == 302
        mock_create.assert_called_once()

    # -- /add POST safe_commit fails --
    @patch("app.routes.chemicals.crud.render_template", return_value="ok")
    @patch("app.routes.chemicals.crud.safe_commit", return_value=False)
    @patch("app.routes.chemicals.crud.create_chemical")
    def test_add_chemical_post_commit_fail(self, mock_create, mock_commit, mock_rt, client, app):
        mock_create.return_value = _make_chemical()
        with patch("flask_login.utils._get_user", return_value=_FakeUser(role="admin")):
            resp = client.post("/chemicals/add", data={"name": "X"})
        assert resp.status_code == 200  # renders form again

    # -- /add POST ValueError --
    @patch("app.routes.chemicals.crud.render_template", return_value="ok")
    @patch("app.routes.chemicals.crud.db")
    @patch("app.routes.chemicals.crud.create_chemical", side_effect=ValueError("bad value"))
    def test_add_chemical_post_value_error(self, mock_create, mock_db, mock_rt, client, app):
        with patch("flask_login.utils._get_user", return_value=_FakeUser(role="admin")):
            resp = client.post("/chemicals/add", data={"name": "X"})
        assert resp.status_code == 200

    # -- /add POST SQLAlchemyError --
    @patch("app.routes.chemicals.crud.render_template", return_value="ok")
    @patch("app.routes.chemicals.crud.db")
    @patch("app.routes.chemicals.crud.create_chemical")
    def test_add_chemical_post_sqlalchemy_error(self, mock_create, mock_db, mock_rt, client, app):
        from sqlalchemy.exc import SQLAlchemyError
        mock_create.side_effect = SQLAlchemyError("db err")
        with patch("flask_login.utils._get_user", return_value=_FakeUser(role="admin")):
            resp = client.post("/chemicals/add", data={"name": "X"})
        assert resp.status_code == 200

    # -- /edit/<id> GET --
    @patch("app.routes.chemicals.crud.render_template", return_value="ok")
    @patch("app.routes.chemicals.crud.ChemicalRepository")
    def test_edit_chemical_get(self, mock_repo, mock_rt, client, app):
        mock_repo.get_by_id.return_value = _make_chemical()
        with patch("flask_login.utils._get_user", return_value=_FakeUser(role="admin")):
            resp = client.get("/chemicals/edit/1")
        assert resp.status_code == 200

    def test_edit_chemical_forbidden(self, client, app):
        with patch("flask_login.utils._get_user", return_value=_FakeUser(role="viewer")):
            resp = client.get("/chemicals/edit/1")
        assert resp.status_code == 302

    @patch("app.routes.chemicals.crud.ChemicalRepository")
    def test_edit_chemical_not_found(self, mock_repo, client, app):
        mock_repo.get_by_id.return_value = None
        with patch("flask_login.utils._get_user", return_value=_FakeUser(role="admin")):
            resp = client.get("/chemicals/edit/999")
        assert resp.status_code == 404

    # -- /edit/<id> POST success --
    @patch("app.routes.chemicals.crud.render_template", return_value="ok")
    @patch("app.routes.chemicals.crud.safe_commit", return_value=True)
    @patch("app.routes.chemicals.crud.update_chemical")
    @patch("app.routes.chemicals.crud.ChemicalRepository")
    def test_edit_chemical_post_success(self, mock_repo, mock_update, mock_commit, mock_rt, client, app):
        mock_repo.get_by_id.return_value = _make_chemical()
        with patch("flask_login.utils._get_user", return_value=_FakeUser(role="admin")):
            resp = client.post("/chemicals/edit/1", data={"name": "NaOH"})
        assert resp.status_code == 302

    # -- /edit/<id> POST commit fail --
    @patch("app.routes.chemicals.crud.render_template", return_value="ok")
    @patch("app.routes.chemicals.crud.safe_commit", return_value=False)
    @patch("app.routes.chemicals.crud.update_chemical")
    @patch("app.routes.chemicals.crud.ChemicalRepository")
    def test_edit_chemical_post_commit_fail(self, mock_repo, mock_update, mock_commit, mock_rt, client, app):
        mock_repo.get_by_id.return_value = _make_chemical()
        with patch("flask_login.utils._get_user", return_value=_FakeUser(role="admin")):
            resp = client.post("/chemicals/edit/1", data={"name": "NaOH"})
        assert resp.status_code == 200

    # -- /edit/<id> POST ValueError --
    @patch("app.routes.chemicals.crud.render_template", return_value="ok")
    @patch("app.routes.chemicals.crud.db")
    @patch("app.routes.chemicals.crud.update_chemical", side_effect=ValueError("bad"))
    @patch("app.routes.chemicals.crud.ChemicalRepository")
    def test_edit_chemical_post_value_error(self, mock_repo, mock_update, mock_db, mock_rt, client, app):
        mock_repo.get_by_id.return_value = _make_chemical()
        with patch("flask_login.utils._get_user", return_value=_FakeUser(role="admin")):
            resp = client.post("/chemicals/edit/1", data={"name": "X"})
        assert resp.status_code == 200

    # -- /edit/<id> POST SQLAlchemyError --
    @patch("app.routes.chemicals.crud.render_template", return_value="ok")
    @patch("app.routes.chemicals.crud.db")
    @patch("app.routes.chemicals.crud.update_chemical")
    @patch("app.routes.chemicals.crud.ChemicalRepository")
    def test_edit_chemical_post_sqlalchemy_error(self, mock_repo, mock_update, mock_db, mock_rt, client, app):
        from sqlalchemy.exc import SQLAlchemyError
        mock_update.side_effect = SQLAlchemyError("err")
        mock_repo.get_by_id.return_value = _make_chemical()
        with patch("flask_login.utils._get_user", return_value=_FakeUser(role="admin")):
            resp = client.post("/chemicals/edit/1", data={"name": "X"})
        assert resp.status_code == 200

    # -- /receive/<id> --
    @patch("app.routes.chemicals.crud.safe_commit", return_value=True)
    @patch("app.routes.chemicals.crud.receive_stock", return_value=(True, "Added 10"))
    @patch("app.routes.chemicals.crud.ChemicalRepository")
    def test_receive_chemical_success(self, mock_repo, mock_svc, mock_commit, client, app):
        mock_repo.get_by_id.return_value = _make_chemical()
        with patch("flask_login.utils._get_user", return_value=_FakeUser(role="admin")):
            resp = client.post("/chemicals/receive/1", data={"quantity_add": "10"})
        assert resp.status_code == 302

    @patch("app.routes.chemicals.crud.receive_stock", return_value=(False, "Invalid quantity"))
    @patch("app.routes.chemicals.crud.ChemicalRepository")
    def test_receive_chemical_service_fail(self, mock_repo, mock_svc, client, app):
        mock_repo.get_by_id.return_value = _make_chemical()
        with patch("flask_login.utils._get_user", return_value=_FakeUser(role="admin")):
            resp = client.post("/chemicals/receive/1", data={"quantity_add": "0"})
        assert resp.status_code == 302

    def test_receive_chemical_forbidden(self, client, app):
        with patch("flask_login.utils._get_user", return_value=_FakeUser(role="viewer")):
            resp = client.post("/chemicals/receive/1", data={"quantity_add": "10"})
        assert resp.status_code == 302

    @patch("app.routes.chemicals.crud.ChemicalRepository")
    def test_receive_chemical_not_found(self, mock_repo, client, app):
        mock_repo.get_by_id.return_value = None
        with patch("flask_login.utils._get_user", return_value=_FakeUser(role="admin")):
            resp = client.post("/chemicals/receive/1", data={"quantity_add": "10"})
        assert resp.status_code == 404

    @patch("app.routes.chemicals.crud.db")
    @patch("app.routes.chemicals.crud.ChemicalRepository")
    def test_receive_chemical_value_error(self, mock_repo, mock_db, client, app):
        mock_repo.get_by_id.return_value = _make_chemical()
        with patch("flask_login.utils._get_user", return_value=_FakeUser(role="admin")):
            resp = client.post("/chemicals/receive/1", data={"quantity_add": "bad"})
        assert resp.status_code == 302

    # -- /consume/<id> --
    @patch("app.routes.chemicals.crud.safe_commit", return_value=True)
    @patch("app.routes.chemicals.crud.consume_chemical_stock")
    @patch("app.routes.chemicals.crud.ChemicalRepository")
    def test_consume_chemical_success(self, mock_repo, mock_consume, mock_commit, client, app):
        mock_repo.get_by_id.return_value = _make_chemical()
        mock_consume.return_value = _ConsumeResult(success=True)
        with patch("flask_login.utils._get_user", return_value=_FakeUser()):
            resp = client.post("/chemicals/consume/1", data={
                "quantity_used": "5", "purpose": "test", "sample_id": "10"
            })
        assert resp.status_code == 302

    @patch("app.routes.chemicals.crud.consume_chemical_stock")
    @patch("app.routes.chemicals.crud.ChemicalRepository")
    def test_consume_chemical_fail(self, mock_repo, mock_consume, client, app):
        mock_repo.get_by_id.return_value = _make_chemical()
        mock_consume.return_value = _ConsumeResult(success=False, error="No stock")
        with patch("flask_login.utils._get_user", return_value=_FakeUser()):
            resp = client.post("/chemicals/consume/1", data={"quantity_used": "5"})
        assert resp.status_code == 302

    @patch("app.routes.chemicals.crud.ChemicalRepository")
    def test_consume_chemical_not_found(self, mock_repo, client, app):
        mock_repo.get_by_id.return_value = None
        with patch("flask_login.utils._get_user", return_value=_FakeUser()):
            resp = client.post("/chemicals/consume/999", data={"quantity_used": "5"})
        assert resp.status_code == 404

    @patch("app.routes.chemicals.crud.db")
    @patch("app.routes.chemicals.crud.ChemicalRepository")
    def test_consume_chemical_value_error(self, mock_repo, mock_db, client, app):
        mock_repo.get_by_id.return_value = _make_chemical()
        with patch("flask_login.utils._get_user", return_value=_FakeUser()):
            resp = client.post("/chemicals/consume/1", data={"quantity_used": "bad"})
        assert resp.status_code == 302

    @patch("app.routes.chemicals.crud.consume_chemical_stock")
    @patch("app.routes.chemicals.crud.ChemicalRepository")
    def test_consume_chemical_invalid_sample_id(self, mock_repo, mock_consume, client, app):
        mock_repo.get_by_id.return_value = _make_chemical()
        mock_consume.return_value = _ConsumeResult(success=True)
        with patch("app.routes.chemicals.crud.safe_commit", return_value=True):
            with patch("flask_login.utils._get_user", return_value=_FakeUser()):
                resp = client.post("/chemicals/consume/1", data={
                    "quantity_used": "5", "sample_id": "abc"
                })
        assert resp.status_code == 302

    # -- /dispose/<id> --
    @patch("app.routes.chemicals.crud.safe_commit", return_value=True)
    @patch("app.routes.chemicals.crud.svc_dispose_chemical")
    @patch("app.routes.chemicals.crud.ChemicalRepository")
    def test_dispose_chemical_success(self, mock_repo, mock_dispose, mock_commit, client, app):
        mock_repo.get_by_id.return_value = _make_chemical()
        with patch("flask_login.utils._get_user", return_value=_FakeUser(role="senior")):
            resp = client.post("/chemicals/dispose/1", data={"reason": "Expired"})
        assert resp.status_code == 302
        mock_dispose.assert_called_once()

    def test_dispose_chemical_forbidden(self, client, app):
        with patch("flask_login.utils._get_user", return_value=_FakeUser(role="chemist")):
            resp = client.post("/chemicals/dispose/1")
        assert resp.status_code == 302

    @patch("app.routes.chemicals.crud.ChemicalRepository")
    def test_dispose_chemical_not_found(self, mock_repo, client, app):
        mock_repo.get_by_id.return_value = None
        with patch("flask_login.utils._get_user", return_value=_FakeUser(role="admin")):
            resp = client.post("/chemicals/dispose/999")
        assert resp.status_code == 404

    @patch("app.routes.chemicals.crud.db")
    @patch("app.routes.chemicals.crud.svc_dispose_chemical")
    @patch("app.routes.chemicals.crud.ChemicalRepository")
    def test_dispose_chemical_sqlalchemy_error(self, mock_repo, mock_dispose, mock_db, client, app):
        from sqlalchemy.exc import SQLAlchemyError
        mock_repo.get_by_id.return_value = _make_chemical()
        mock_dispose.side_effect = SQLAlchemyError("err")
        with patch("flask_login.utils._get_user", return_value=_FakeUser(role="admin")):
            resp = client.post("/chemicals/dispose/1")
        assert resp.status_code == 302

    # -- /journal --
    @patch("app.routes.chemicals.crud.render_template", return_value="ok")
    @patch("app.routes.chemicals.crud.get_journal_rows", return_value=[])
    def test_chemical_journal(self, mock_svc, mock_rt, client, app):
        with patch("flask_login.utils._get_user", return_value=_FakeUser()):
            resp = client.get("/chemicals/journal?lab=coal&start_date=2026-01-01&end_date=2026-12-31")
        assert resp.status_code == 200
        mock_svc.assert_called_once_with(lab="coal", start_date="2026-01-01", end_date="2026-12-31")


# ---------------------------------------------------------------------------
# ===== CHEMICALS WASTE TESTS =====
# ---------------------------------------------------------------------------

class TestChemicalsWaste:
    """Tests for app/routes/chemicals/waste.py"""

    # -- /waste --
    @patch("app.routes.chemicals.waste.render_template", return_value="ok")
    @patch("app.routes.chemicals.waste.ChemicalWasteRecord")
    @patch("app.routes.chemicals.waste.ChemicalWaste")
    def test_waste_list(self, mock_cw, mock_cwr, mock_rt, client, app):
        w = _make_waste()
        mock_cw.query.filter.return_value.filter.return_value.order_by.return_value.all.return_value = [w]
        mock_cw.query.filter.return_value.order_by.return_value.all.return_value = [w]
        # Records for the waste
        rec = MagicMock()
        rec.month = 1
        rec.quantity = 5.0
        rec.ending_balance = 10.0
        mock_cwr.query.filter_by.return_value.all.return_value = [rec]
        with patch("flask_login.utils._get_user", return_value=_FakeUser()):
            resp = client.get("/chemicals/waste?lab=coal&year=2026")
        assert resp.status_code == 200

    @patch("app.routes.chemicals.waste.render_template", return_value="ok")
    @patch("app.routes.chemicals.waste.ChemicalWasteRecord")
    @patch("app.routes.chemicals.waste.ChemicalWaste")
    def test_waste_list_all_labs(self, mock_cw, mock_cwr, mock_rt, client, app):
        mock_cw.query.filter.return_value.order_by.return_value.all.return_value = []
        with patch("flask_login.utils._get_user", return_value=_FakeUser()):
            resp = client.get("/chemicals/waste?lab=all")
        assert resp.status_code == 200

    @patch("app.routes.chemicals.waste.render_template", return_value="ok")
    @patch("app.routes.chemicals.waste.ChemicalWasteRecord")
    @patch("app.routes.chemicals.waste.ChemicalWaste")
    def test_waste_list_no_ending_balance(self, mock_cw, mock_cwr, mock_rt, client, app):
        w = _make_waste()
        mock_cw.query.filter.return_value.order_by.return_value.all.return_value = [w]
        rec = MagicMock()
        rec.month = 1
        rec.quantity = 5.0
        rec.ending_balance = None  # No ending balance
        mock_cwr.query.filter_by.return_value.all.return_value = [rec]
        with patch("flask_login.utils._get_user", return_value=_FakeUser()):
            resp = client.get("/chemicals/waste")
        assert resp.status_code == 200

    # -- /waste/add GET --
    @patch("app.routes.chemicals.waste.render_template", return_value="ok")
    def test_add_waste_get(self, mock_rt, client, app):
        with patch("flask_login.utils._get_user", return_value=_FakeUser(role="admin")):
            resp = client.get("/chemicals/waste/add")
        assert resp.status_code == 200

    def test_add_waste_forbidden(self, client, app):
        with patch("flask_login.utils._get_user", return_value=_FakeUser(role="viewer")):
            resp = client.get("/chemicals/waste/add")
        assert resp.status_code == 302

    # -- /waste/add POST --
    @patch("app.routes.chemicals.waste.render_template", return_value="ok")
    @patch("app.routes.chemicals.waste.safe_commit", return_value=True)
    @patch("app.routes.chemicals.waste.db")
    def test_add_waste_post_success(self, mock_db, mock_commit, mock_rt, client, app):
        with patch("flask_login.utils._get_user", return_value=_FakeUser(role="chemist")):
            resp = client.post("/chemicals/waste/add", data={
                "name_mn": "TestWaste", "monthly_amount": "5.0",
                "unit": "L", "is_hazardous": "on", "hazard_type": "toxic",
            })
        assert resp.status_code == 302

    @patch("app.routes.chemicals.waste.render_template", return_value="ok")
    @patch("app.routes.chemicals.waste.safe_commit", return_value=False)
    @patch("app.routes.chemicals.waste.db")
    def test_add_waste_post_commit_fail(self, mock_db, mock_commit, mock_rt, client, app):
        with patch("flask_login.utils._get_user", return_value=_FakeUser(role="admin")):
            resp = client.post("/chemicals/waste/add", data={
                "name_mn": "W", "monthly_amount": "1",
            })
        assert resp.status_code == 200

    @patch("app.routes.chemicals.waste.render_template", return_value="ok")
    @patch("app.routes.chemicals.waste.db")
    def test_add_waste_post_value_error(self, mock_db, mock_rt, client, app):
        with patch("flask_login.utils._get_user", return_value=_FakeUser(role="admin")):
            resp = client.post("/chemicals/waste/add", data={
                "name_mn": "W", "monthly_amount": "bad",
            })
        assert resp.status_code == 200

    # -- /waste/edit/<id> GET --
    @patch("app.routes.chemicals.waste.render_template", return_value="ok")
    @patch("app.routes.chemicals.waste.db")
    def test_edit_waste_get(self, mock_db, mock_rt, client, app):
        mock_db.session.get.return_value = _make_waste()
        with patch("flask_login.utils._get_user", return_value=_FakeUser(role="admin")):
            resp = client.get("/chemicals/waste/edit/1")
        assert resp.status_code == 200

    def test_edit_waste_forbidden(self, client, app):
        with patch("flask_login.utils._get_user", return_value=_FakeUser(role="viewer")):
            resp = client.get("/chemicals/waste/edit/1")
        assert resp.status_code == 302

    @patch("app.routes.chemicals.waste.db")
    def test_edit_waste_not_found(self, mock_db, client, app):
        mock_db.session.get.return_value = None
        with patch("flask_login.utils._get_user", return_value=_FakeUser(role="admin")):
            resp = client.get("/chemicals/waste/edit/999")
        assert resp.status_code == 404

    # -- /waste/edit/<id> POST --
    @patch("app.routes.chemicals.waste.render_template", return_value="ok")
    @patch("app.routes.chemicals.waste.safe_commit", return_value=True)
    @patch("app.routes.chemicals.waste.db")
    def test_edit_waste_post_success(self, mock_db, mock_commit, mock_rt, client, app):
        mock_db.session.get.return_value = _make_waste()
        with patch("flask_login.utils._get_user", return_value=_FakeUser(role="admin")):
            resp = client.post("/chemicals/waste/edit/1", data={
                "name_mn": "Updated", "monthly_amount": "10",
            })
        assert resp.status_code == 302

    @patch("app.routes.chemicals.waste.render_template", return_value="ok")
    @patch("app.routes.chemicals.waste.safe_commit", return_value=False)
    @patch("app.routes.chemicals.waste.db")
    def test_edit_waste_post_commit_fail(self, mock_db, mock_commit, mock_rt, client, app):
        mock_db.session.get.return_value = _make_waste()
        with patch("flask_login.utils._get_user", return_value=_FakeUser(role="admin")):
            resp = client.post("/chemicals/waste/edit/1", data={
                "name_mn": "X", "monthly_amount": "1",
            })
        assert resp.status_code == 200

    @patch("app.routes.chemicals.waste.render_template", return_value="ok")
    @patch("app.routes.chemicals.waste.db")
    def test_edit_waste_post_value_error(self, mock_db, mock_rt, client, app):
        mock_db.session.get.return_value = _make_waste()
        with patch("flask_login.utils._get_user", return_value=_FakeUser(role="admin")):
            resp = client.post("/chemicals/waste/edit/1", data={
                "name_mn": "X", "monthly_amount": "bad",
            })
        assert resp.status_code == 200

    # -- /waste/delete/<id> --
    @patch("app.routes.chemicals.waste.safe_commit", return_value=True)
    @patch("app.routes.chemicals.waste.db")
    def test_delete_waste_success(self, mock_db, mock_commit, client, app):
        w = _make_waste()
        mock_db.session.get.return_value = w
        with patch("flask_login.utils._get_user", return_value=_FakeUser(role="senior")):
            resp = client.post("/chemicals/waste/delete/1")
        assert resp.status_code == 302
        assert w.is_active is False

    def test_delete_waste_forbidden(self, client, app):
        with patch("flask_login.utils._get_user", return_value=_FakeUser(role="chemist")):
            resp = client.post("/chemicals/waste/delete/1")
        assert resp.status_code == 302

    @patch("app.routes.chemicals.waste.db")
    def test_delete_waste_not_found(self, mock_db, client, app):
        mock_db.session.get.return_value = None
        with patch("flask_login.utils._get_user", return_value=_FakeUser(role="admin")):
            resp = client.post("/chemicals/waste/delete/999")
        assert resp.status_code == 404

    # -- /waste/api/save_record --
    @patch("app.routes.chemicals.waste.db")
    @patch("app.routes.chemicals.waste.ChemicalWasteRecord")
    def test_save_waste_record_new(self, mock_cwr, mock_db, client, app):
        mock_cwr.query.filter_by.return_value.first.return_value = None
        with patch("flask_login.utils._get_user", return_value=_FakeUser()):
            resp = client.post(
                "/chemicals/waste/api/save_record",
                data=json.dumps({
                    "waste_id": 1, "year": 2026, "month": 3,
                    "quantity": 5.0, "ending_balance": 10.0,
                }),
                content_type="application/json",
            )
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["success"] is True

    @patch("app.routes.chemicals.waste.db")
    @patch("app.routes.chemicals.waste.ChemicalWasteRecord")
    def test_save_waste_record_update_existing(self, mock_cwr, mock_db, client, app):
        existing = MagicMock()
        mock_cwr.query.filter_by.return_value.first.return_value = existing
        with patch("flask_login.utils._get_user", return_value=_FakeUser()):
            resp = client.post(
                "/chemicals/waste/api/save_record",
                data=json.dumps({
                    "waste_id": 1, "year": 2026, "month": 3,
                    "quantity": 8.0, "ending_balance": 15.0,
                }),
                content_type="application/json",
            )
        assert resp.status_code == 200
        assert existing.quantity == 8.0

    @patch("app.routes.chemicals.waste.db")
    @patch("app.routes.chemicals.waste.ChemicalWasteRecord")
    def test_save_waste_record_update_no_ending(self, mock_cwr, mock_db, client, app):
        existing = MagicMock()
        existing.ending_balance = 5.0
        mock_cwr.query.filter_by.return_value.first.return_value = existing
        with patch("flask_login.utils._get_user", return_value=_FakeUser()):
            resp = client.post(
                "/chemicals/waste/api/save_record",
                data=json.dumps({
                    "waste_id": 1, "year": 2026, "month": 3,
                    "quantity": 8.0,
                }),
                content_type="application/json",
            )
        assert resp.status_code == 200
        # ending_balance should NOT have been updated since it was not provided
        assert existing.ending_balance == 5.0

    @patch("app.routes.chemicals.waste.db")
    @patch("app.routes.chemicals.waste.ChemicalWasteRecord")
    def test_save_waste_record_commit_error(self, mock_cwr, mock_db, client, app):
        from sqlalchemy.exc import SQLAlchemyError
        mock_cwr.query.filter_by.return_value.first.return_value = None
        mock_db.session.commit.side_effect = SQLAlchemyError("err")
        with patch("flask_login.utils._get_user", return_value=_FakeUser()):
            resp = client.post(
                "/chemicals/waste/api/save_record",
                data=json.dumps({
                    "waste_id": 1, "year": 2026, "month": 1, "quantity": 1,
                }),
                content_type="application/json",
            )
        assert resp.status_code == 500

    @patch("app.routes.chemicals.waste.db")
    def test_save_waste_record_value_error(self, mock_db, client, app):
        with patch("flask_login.utils._get_user", return_value=_FakeUser()):
            resp = client.post(
                "/chemicals/waste/api/save_record",
                data=json.dumps({
                    "waste_id": 1, "year": 2026, "month": 1, "quantity": "bad",
                }),
                content_type="application/json",
            )
        assert resp.status_code == 500

    # -- /waste/report --
    @patch("app.routes.chemicals.waste.render_template", return_value="ok")
    @patch("app.routes.chemicals.waste.ChemicalWasteRecord")
    @patch("app.routes.chemicals.waste.ChemicalWaste")
    def test_waste_report(self, mock_cw, mock_cwr, mock_rt, client, app):
        w = _make_waste()
        mock_cw.query.filter.return_value.filter.return_value.order_by.return_value.all.return_value = [w]
        rec = MagicMock()
        rec.month = 1
        rec.quantity = 5.0
        rec.ending_balance = 10.0
        mock_cwr.query.filter_by.return_value.all.return_value = [rec]
        with patch("flask_login.utils._get_user", return_value=_FakeUser()):
            resp = client.get("/chemicals/waste/report?year=2026&lab=coal")
        assert resp.status_code == 200

    @patch("app.routes.chemicals.waste.render_template", return_value="ok")
    @patch("app.routes.chemicals.waste.ChemicalWasteRecord")
    @patch("app.routes.chemicals.waste.ChemicalWaste")
    def test_waste_report_all_labs(self, mock_cw, mock_cwr, mock_rt, client, app):
        mock_cw.query.filter.return_value.order_by.return_value.all.return_value = []
        with patch("flask_login.utils._get_user", return_value=_FakeUser()):
            resp = client.get("/chemicals/waste/report?lab=all")
        assert resp.status_code == 200


# ---------------------------------------------------------------------------
# ===== SPARE PARTS API TESTS =====
# ---------------------------------------------------------------------------

class TestSparePartsApi:
    """Tests for app/routes/spare_parts/api.py"""

    # -- /api/list --
    @patch("app.routes.spare_parts.api.get_spare_parts_list_simple", return_value=[])
    def test_api_list(self, mock_svc, client, app):
        with patch("flask_login.utils._get_user", return_value=_FakeUser()):
            resp = client.get("/spare_parts/api/list")
        assert resp.status_code == 200

    # -- /api/low_stock --
    @patch("app.routes.spare_parts.api.get_low_stock_parts", return_value=[])
    def test_api_low_stock(self, mock_svc, client, app):
        with patch("flask_login.utils._get_user", return_value=_FakeUser()):
            resp = client.get("/spare_parts/api/low_stock")
        assert resp.status_code == 200

    # -- /api/stats --
    @patch("app.routes.spare_parts.api.get_full_stats", return_value={})
    def test_api_stats(self, mock_svc, client, app):
        with patch("flask_login.utils._get_user", return_value=_FakeUser()):
            resp = client.get("/spare_parts/api/stats")
        assert resp.status_code == 200

    # -- /api/consume --
    @patch("app.routes.spare_parts.api.db")
    @patch("app.routes.spare_parts.api.consume_stock")
    def test_api_consume_success(self, mock_consume, mock_db, client, app):
        mock_consume.return_value = (
            {"consumed": 5, "unit": "pcs", "remaining": 15, "status": "active"},
            None,
        )
        with patch("flask_login.utils._get_user", return_value=_FakeUser()):
            resp = client.post(
                "/spare_parts/api/consume",
                data=json.dumps({"spare_part_id": 1, "quantity": 5, "purpose": "repair"}),
                content_type="application/json",
            )
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["success"] is True

    def test_api_consume_invalid_quantity(self, client, app):
        with patch("flask_login.utils._get_user", return_value=_FakeUser()):
            resp = client.post(
                "/spare_parts/api/consume",
                data=json.dumps({"spare_part_id": 1, "quantity": "bad"}),
                content_type="application/json",
            )
        assert resp.status_code == 400

    def test_api_consume_missing_id(self, client, app):
        with patch("flask_login.utils._get_user", return_value=_FakeUser()):
            resp = client.post(
                "/spare_parts/api/consume",
                data=json.dumps({"quantity": 5}),
                content_type="application/json",
            )
        assert resp.status_code == 400

    def test_api_consume_zero_quantity(self, client, app):
        with patch("flask_login.utils._get_user", return_value=_FakeUser()):
            resp = client.post(
                "/spare_parts/api/consume",
                data=json.dumps({"spare_part_id": 1, "quantity": 0}),
                content_type="application/json",
            )
        assert resp.status_code == 400

    @patch("app.routes.spare_parts.api.consume_stock")
    def test_api_consume_not_found(self, mock_consume, client, app):
        mock_consume.return_value = (None, "not_found")
        with patch("flask_login.utils._get_user", return_value=_FakeUser()):
            resp = client.post(
                "/spare_parts/api/consume",
                data=json.dumps({"spare_part_id": 999, "quantity": 1}),
                content_type="application/json",
            )
        assert resp.status_code == 404

    @patch("app.routes.spare_parts.api.consume_stock")
    def test_api_consume_other_error(self, mock_consume, client, app):
        mock_consume.return_value = (None, "Insufficient stock")
        with patch("flask_login.utils._get_user", return_value=_FakeUser()):
            resp = client.post(
                "/spare_parts/api/consume",
                data=json.dumps({"spare_part_id": 1, "quantity": 100}),
                content_type="application/json",
            )
        assert resp.status_code == 400

    @patch("app.routes.spare_parts.api.db")
    @patch("app.routes.spare_parts.api.consume_stock")
    def test_api_consume_commit_error(self, mock_consume, mock_db, client, app):
        from sqlalchemy.exc import SQLAlchemyError
        mock_consume.return_value = (
            {"consumed": 1, "unit": "pcs", "remaining": 0, "status": "out_of_stock"},
            None,
        )
        mock_db.session.commit.side_effect = SQLAlchemyError("err")
        with patch("flask_login.utils._get_user", return_value=_FakeUser()):
            resp = client.post(
                "/spare_parts/api/consume",
                data=json.dumps({"spare_part_id": 1, "quantity": 1}),
                content_type="application/json",
            )
        assert resp.status_code == 500

    @patch("app.routes.spare_parts.api.consume_stock", side_effect=ValueError("bad"))
    def test_api_consume_value_error(self, mock_consume, client, app):
        with patch("flask_login.utils._get_user", return_value=_FakeUser()):
            resp = client.post(
                "/spare_parts/api/consume",
                data=json.dumps({"spare_part_id": 1, "quantity": 1}),
                content_type="application/json",
            )
        assert resp.status_code == 500

    # -- /api/consume_bulk --
    @patch("app.routes.spare_parts.api.db")
    @patch("app.routes.spare_parts.api.consume_stock_bulk")
    def test_api_consume_bulk_success(self, mock_bulk, mock_db, client, app):
        mock_bulk.return_value = ([{"id": 1, "consumed": 5}], [])
        with patch("flask_login.utils._get_user", return_value=_FakeUser()):
            resp = client.post(
                "/spare_parts/api/consume_bulk",
                data=json.dumps({
                    "items": [{"spare_part_id": 1, "quantity": 5}],
                    "purpose": "repair",
                }),
                content_type="application/json",
            )
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["success"] is True

    def test_api_consume_bulk_empty_items(self, client, app):
        with patch("flask_login.utils._get_user", return_value=_FakeUser()):
            resp = client.post(
                "/spare_parts/api/consume_bulk",
                data=json.dumps({"items": []}),
                content_type="application/json",
            )
        assert resp.status_code == 400

    def test_api_consume_bulk_too_many(self, client, app):
        items = [{"spare_part_id": i, "quantity": 1} for i in range(101)]
        with patch("flask_login.utils._get_user", return_value=_FakeUser()):
            resp = client.post(
                "/spare_parts/api/consume_bulk",
                data=json.dumps({"items": items}),
                content_type="application/json",
            )
        assert resp.status_code == 400

    @patch("app.routes.spare_parts.api.db")
    @patch("app.routes.spare_parts.api.consume_stock_bulk")
    def test_api_consume_bulk_commit_error(self, mock_bulk, mock_db, client, app):
        from sqlalchemy.exc import SQLAlchemyError
        mock_bulk.return_value = ([], [])
        mock_db.session.commit.side_effect = SQLAlchemyError("err")
        with patch("flask_login.utils._get_user", return_value=_FakeUser()):
            resp = client.post(
                "/spare_parts/api/consume_bulk",
                data=json.dumps({"items": [{"spare_part_id": 1, "quantity": 1}]}),
                content_type="application/json",
            )
        assert resp.status_code == 500

    @patch("app.routes.spare_parts.api.consume_stock_bulk", side_effect=TypeError("bad"))
    def test_api_consume_bulk_type_error(self, mock_bulk, client, app):
        with patch("flask_login.utils._get_user", return_value=_FakeUser()):
            resp = client.post(
                "/spare_parts/api/consume_bulk",
                data=json.dumps({"items": [{"spare_part_id": 1, "quantity": 1}]}),
                content_type="application/json",
            )
        assert resp.status_code == 500

    # -- /api/search --
    @patch("app.routes.spare_parts.api.search_spare_parts", return_value=[])
    def test_api_search(self, mock_svc, client, app):
        with patch("flask_login.utils._get_user", return_value=_FakeUser()):
            resp = client.get("/spare_parts/api/search?q=bearing")
        assert resp.status_code == 200
        mock_svc.assert_called_once_with("bearing")

    # -- /api/usage_history/<id> --
    @patch("app.routes.spare_parts.api.get_usage_history", return_value=[])
    def test_api_usage_history(self, mock_svc, client, app):
        with patch("flask_login.utils._get_user", return_value=_FakeUser()):
            resp = client.get("/spare_parts/api/usage_history/1")
        assert resp.status_code == 200
        mock_svc.assert_called_once_with(1)


# ---------------------------------------------------------------------------
# ===== SPARE PARTS CRUD TESTS =====
# ---------------------------------------------------------------------------

class TestSparePartsCrud:
    """Tests for app/routes/spare_parts/crud.py"""

    # -- /categories --
    @patch("app.routes.spare_parts.crud.render_template", return_value="ok")
    @patch("app.routes.spare_parts.crud.get_all_categories_ordered", return_value=[])
    def test_category_list(self, mock_svc, mock_rt, client, app):
        with patch("flask_login.utils._get_user", return_value=_FakeUser(role="admin")):
            resp = client.get("/spare_parts/categories")
        assert resp.status_code == 200

    def test_category_list_forbidden(self, client, app):
        with patch("flask_login.utils._get_user", return_value=_FakeUser(role="chemist")):
            resp = client.get("/spare_parts/categories")
        assert resp.status_code == 302

    # -- /categories/add GET --
    @patch("app.routes.spare_parts.crud.render_template", return_value="ok")
    @patch("app.routes.spare_parts.crud.EquipmentRepository")
    def test_add_category_get(self, mock_eq, mock_rt, client, app):
        mock_eq.get_all_active.return_value = []
        with patch("flask_login.utils._get_user", return_value=_FakeUser(role="manager")):
            resp = client.get("/spare_parts/categories/add")
        assert resp.status_code == 200

    def test_add_category_forbidden(self, client, app):
        with patch("flask_login.utils._get_user", return_value=_FakeUser(role="chemist")):
            resp = client.get("/spare_parts/categories/add")
        assert resp.status_code == 302

    # -- /categories/add POST success --
    @patch("app.routes.spare_parts.crud.render_template", return_value="ok")
    @patch("app.routes.spare_parts.crud.EquipmentRepository")
    @patch("app.routes.spare_parts.crud.safe_commit", return_value=True)
    @patch("app.routes.spare_parts.crud.create_category")
    def test_add_category_post_success(self, mock_create, mock_commit, mock_eq, mock_rt, client, app):
        mock_create.return_value = (MagicMock(), None)
        mock_eq.get_all_active.return_value = []
        with patch("flask_login.utils._get_user", return_value=_FakeUser(role="admin")):
            resp = client.post("/spare_parts/categories/add", data={
                "code": "test_cat", "name": "Test Cat", "sort_order": "0",
            })
        assert resp.status_code == 302

    @patch("app.routes.spare_parts.crud.render_template", return_value="ok")
    @patch("app.routes.spare_parts.crud.EquipmentRepository")
    @patch("app.routes.spare_parts.crud.create_category")
    def test_add_category_post_error(self, mock_create, mock_eq, mock_rt, client, app):
        mock_create.return_value = (None, "Duplicate code")
        mock_eq.get_all_active.return_value = []
        with patch("flask_login.utils._get_user", return_value=_FakeUser(role="admin")):
            resp = client.post("/spare_parts/categories/add", data={
                "code": "dup", "name": "Dup",
            })
        assert resp.status_code == 200

    # -- /categories/edit/<id> GET --
    # Note: edit_category imports `db` and `SparePartCategory` locally via `from app import db`
    @patch("app.routes.spare_parts.crud.render_template", return_value="ok")
    @patch("app.routes.spare_parts.crud.EquipmentRepository")
    @patch("app.models.SparePartCategory")
    @patch("app.db")
    def test_edit_category_get(self, mock_db, mock_spc, mock_eq, mock_rt, client, app):
        cat = MagicMock()
        mock_db.session.get.return_value = cat
        mock_eq.get_all_active.return_value = []
        with patch("flask_login.utils._get_user", return_value=_FakeUser(role="admin")):
            resp = client.get("/spare_parts/categories/edit/1")
        assert resp.status_code == 200

    def test_edit_category_forbidden(self, client, app):
        with patch("flask_login.utils._get_user", return_value=_FakeUser(role="chemist")):
            resp = client.get("/spare_parts/categories/edit/1")
        assert resp.status_code == 302

    @patch("app.models.SparePartCategory")
    @patch("app.db")
    def test_edit_category_not_found(self, mock_db, mock_spc, client, app):
        mock_db.session.get.return_value = None
        with patch("flask_login.utils._get_user", return_value=_FakeUser(role="admin")):
            resp = client.get("/spare_parts/categories/edit/999")
        assert resp.status_code == 404

    # -- /categories/edit/<id> POST success --
    @patch("app.routes.spare_parts.crud.render_template", return_value="ok")
    @patch("app.routes.spare_parts.crud.EquipmentRepository")
    @patch("app.routes.spare_parts.crud.safe_commit", return_value=True)
    @patch("app.routes.spare_parts.crud.update_category")
    @patch("app.models.SparePartCategory")
    @patch("app.db")
    def test_edit_category_post_success(self, mock_db, mock_spc, mock_update, mock_commit, mock_eq, mock_rt, client, app):
        mock_update.return_value = (MagicMock(), None)
        mock_db.session.get.return_value = MagicMock()
        mock_eq.get_all_active.return_value = []
        with patch("flask_login.utils._get_user", return_value=_FakeUser(role="admin")):
            resp = client.post("/spare_parts/categories/edit/1", data={
                "name": "Updated", "sort_order": "1",
            })
        assert resp.status_code == 302

    @patch("app.routes.spare_parts.crud.render_template", return_value="ok")
    @patch("app.routes.spare_parts.crud.EquipmentRepository")
    @patch("app.routes.spare_parts.crud.update_category")
    @patch("app.models.SparePartCategory")
    @patch("app.db")
    def test_edit_category_post_not_found(self, mock_db, mock_spc, mock_update, mock_eq, mock_rt, client, app):
        mock_update.return_value = (None, "not_found")
        mock_db.session.get.return_value = None
        with patch("flask_login.utils._get_user", return_value=_FakeUser(role="admin")):
            resp = client.post("/spare_parts/categories/edit/1", data={"name": "X"})
        assert resp.status_code == 404

    @patch("app.routes.spare_parts.crud.render_template", return_value="ok")
    @patch("app.routes.spare_parts.crud.EquipmentRepository")
    @patch("app.routes.spare_parts.crud.update_category")
    @patch("app.models.SparePartCategory")
    @patch("app.db")
    def test_edit_category_post_other_error(self, mock_db, mock_spc, mock_update, mock_eq, mock_rt, client, app):
        mock_update.return_value = (None, "Validation error")
        mock_db.session.get.return_value = MagicMock()
        mock_eq.get_all_active.return_value = []
        with patch("flask_login.utils._get_user", return_value=_FakeUser(role="admin")):
            resp = client.post("/spare_parts/categories/edit/1", data={"name": "X"})
        assert resp.status_code == 200

    # -- /categories/delete/<id> --
    @patch("app.routes.spare_parts.crud.safe_commit", return_value=True)
    @patch("app.routes.spare_parts.crud.svc_delete_category")
    def test_delete_category_success(self, mock_delete, mock_commit, client, app):
        mock_delete.return_value = ("CatName", None)
        with patch("flask_login.utils._get_user", return_value=_FakeUser(role="admin")):
            resp = client.post("/spare_parts/categories/delete/1")
        assert resp.status_code == 302

    def test_delete_category_forbidden(self, client, app):
        with patch("flask_login.utils._get_user", return_value=_FakeUser(role="manager")):
            resp = client.post("/spare_parts/categories/delete/1")
        assert resp.status_code == 302

    @patch("app.routes.spare_parts.crud.svc_delete_category")
    def test_delete_category_not_found(self, mock_delete, client, app):
        mock_delete.return_value = (None, "not_found")
        with patch("flask_login.utils._get_user", return_value=_FakeUser(role="admin")):
            resp = client.post("/spare_parts/categories/delete/999")
        assert resp.status_code == 404

    @patch("app.routes.spare_parts.crud.svc_delete_category")
    def test_delete_category_has_parts(self, mock_delete, client, app):
        mock_delete.return_value = (None, "Category has parts")
        with patch("flask_login.utils._get_user", return_value=_FakeUser(role="admin")):
            resp = client.post("/spare_parts/categories/delete/1")
        assert resp.status_code == 302

    # -- / (spare_part_list) --
    @patch("app.routes.spare_parts.crud.render_template", return_value="ok")
    @patch("app.routes.spare_parts.crud.get_categories_dict", return_value={})
    @patch("app.routes.spare_parts.crud.get_categories", return_value=[])
    @patch("app.routes.spare_parts.crud.get_list_stats", return_value={})
    @patch("app.routes.spare_parts.crud.get_spare_parts_filtered", return_value=[])
    def test_spare_part_list(self, mock_filtered, mock_stats, mock_cats, mock_dict, mock_rt, client, app):
        with patch("flask_login.utils._get_user", return_value=_FakeUser()):
            resp = client.get("/spare_parts/?category=general&status=active&view=low")
        assert resp.status_code == 200

    # -- /<int:id> --
    @patch("app.routes.spare_parts.crud.render_template", return_value="ok")
    @patch("app.routes.spare_parts.crud.get_categories", return_value=[])
    @patch("app.routes.spare_parts.crud.get_detail_data")
    def test_spare_part_detail(self, mock_detail, mock_cats, mock_rt, client, app):
        sp = MagicMock()
        mock_detail.return_value = (sp, [], [])
        with patch("flask_login.utils._get_user", return_value=_FakeUser()):
            resp = client.get("/spare_parts/1")
        assert resp.status_code == 200

    @patch("app.routes.spare_parts.crud.get_detail_data")
    def test_spare_part_detail_not_found(self, mock_detail, client, app):
        mock_detail.return_value = (None, [], [])
        with patch("flask_login.utils._get_user", return_value=_FakeUser()):
            resp = client.get("/spare_parts/999")
        assert resp.status_code == 404

    # -- /add GET --
    @patch("app.routes.spare_parts.crud.render_template", return_value="ok")
    @patch("app.routes.spare_parts.crud.get_categories", return_value=[])
    @patch("app.routes.spare_parts.crud.EquipmentRepository")
    def test_add_spare_part_get(self, mock_eq, mock_cats, mock_rt, client, app):
        mock_eq.get_all_active.return_value = []
        with patch("flask_login.utils._get_user", return_value=_FakeUser(role="admin")):
            resp = client.get("/spare_parts/add")
        assert resp.status_code == 200

    def test_add_spare_part_forbidden(self, client, app):
        with patch("flask_login.utils._get_user", return_value=_FakeUser(role="viewer")):
            resp = client.get("/spare_parts/add")
        assert resp.status_code == 302

    # -- /add POST success --
    @patch("app.routes.spare_parts.crud.render_template", return_value="ok")
    @patch("app.routes.spare_parts.crud.get_categories", return_value=[])
    @patch("app.routes.spare_parts.crud.EquipmentRepository")
    @patch("app.routes.spare_parts.crud.safe_commit", return_value=True)
    @patch("app.routes.spare_parts.crud.create_spare_part")
    def test_add_spare_part_post_success(self, mock_create, mock_commit, mock_eq, mock_cats, mock_rt, client, app):
        sp = MagicMock()
        sp.name = "Bearing"
        mock_create.return_value = (sp, None)
        mock_eq.get_all_active.return_value = []
        with patch("flask_login.utils._get_user", return_value=_FakeUser(role="admin")):
            resp = client.post("/spare_parts/add", data={"name": "Bearing", "quantity": "10"})
        assert resp.status_code == 302

    @patch("app.routes.spare_parts.crud.render_template", return_value="ok")
    @patch("app.routes.spare_parts.crud.get_categories", return_value=[])
    @patch("app.routes.spare_parts.crud.EquipmentRepository")
    @patch("app.routes.spare_parts.crud.create_spare_part")
    def test_add_spare_part_post_error(self, mock_create, mock_eq, mock_cats, mock_rt, client, app):
        mock_create.return_value = (None, "Missing name")
        mock_eq.get_all_active.return_value = []
        with patch("flask_login.utils._get_user", return_value=_FakeUser(role="admin")):
            resp = client.post("/spare_parts/add", data={"quantity": "10"})
        assert resp.status_code == 200

    # -- /add POST with image upload --
    @patch("app.routes.spare_parts.crud.render_template", return_value="ok")
    @patch("app.routes.spare_parts.crud.get_categories", return_value=[])
    @patch("app.routes.spare_parts.crud.EquipmentRepository")
    @patch("app.routes.spare_parts.crud.safe_commit", return_value=True)
    @patch("app.routes.spare_parts.crud.save_image_to_disk", return_value="/uploads/img.jpg")
    @patch("app.routes.spare_parts.crud.create_spare_part")
    def test_add_spare_part_with_image(self, mock_create, mock_save_img, mock_commit, mock_eq, mock_cats, mock_rt, client, app):
        sp = MagicMock()
        sp.name = "Bearing"
        mock_create.return_value = (sp, None)
        mock_eq.get_all_active.return_value = []
        import io
        data = {
            "name": "Bearing",
            "quantity": "10",
            "image": (io.BytesIO(b"fake-image"), "test.jpg"),
        }
        with patch("flask_login.utils._get_user", return_value=_FakeUser(role="admin")):
            resp = client.post("/spare_parts/add", data=data, content_type="multipart/form-data")
        assert resp.status_code == 302
        mock_save_img.assert_called_once()

    # -- /edit/<id> GET --
    # Note: edit_spare_part imports `db` and `SparePart` locally via `from app import db`
    @patch("app.routes.spare_parts.crud.render_template", return_value="ok")
    @patch("app.routes.spare_parts.crud.get_categories", return_value=[])
    @patch("app.routes.spare_parts.crud.EquipmentRepository")
    @patch("app.db")
    def test_edit_spare_part_get(self, mock_db, mock_eq, mock_cats, mock_rt, client, app):
        mock_db.session.get.return_value = MagicMock()
        mock_eq.get_all_active.return_value = []
        with patch("flask_login.utils._get_user", return_value=_FakeUser(role="admin")):
            resp = client.get("/spare_parts/edit/1")
        assert resp.status_code == 200

    def test_edit_spare_part_forbidden(self, client, app):
        with patch("flask_login.utils._get_user", return_value=_FakeUser(role="viewer")):
            resp = client.get("/spare_parts/edit/1")
        assert resp.status_code == 302

    @patch("app.db")
    def test_edit_spare_part_not_found(self, mock_db, client, app):
        mock_db.session.get.return_value = None
        with patch("flask_login.utils._get_user", return_value=_FakeUser(role="admin")):
            resp = client.get("/spare_parts/edit/999")
        assert resp.status_code == 404

    # -- /edit/<id> POST success --
    @patch("app.routes.spare_parts.crud.render_template", return_value="ok")
    @patch("app.routes.spare_parts.crud.get_categories", return_value=[])
    @patch("app.routes.spare_parts.crud.EquipmentRepository")
    @patch("app.routes.spare_parts.crud.safe_commit", return_value=True)
    @patch("app.routes.spare_parts.crud.update_spare_part")
    @patch("app.db")
    def test_edit_spare_part_post_success(self, mock_db, mock_update, mock_commit, mock_eq, mock_cats, mock_rt, client, app):
        sp = MagicMock()
        sp.image_path = None
        mock_db.session.get.return_value = sp
        mock_update.return_value = (sp, None)
        mock_eq.get_all_active.return_value = []
        with patch("flask_login.utils._get_user", return_value=_FakeUser(role="admin")):
            resp = client.post("/spare_parts/edit/1", data={"name": "Updated"})
        assert resp.status_code == 302

    @patch("app.routes.spare_parts.crud.render_template", return_value="ok")
    @patch("app.routes.spare_parts.crud.get_categories", return_value=[])
    @patch("app.routes.spare_parts.crud.EquipmentRepository")
    @patch("app.routes.spare_parts.crud.update_spare_part")
    @patch("app.db")
    def test_edit_spare_part_post_not_found_error(self, mock_db, mock_update, mock_eq, mock_cats, mock_rt, client, app):
        sp = MagicMock()
        sp.image_path = None
        mock_db.session.get.return_value = sp
        mock_update.return_value = (None, "not_found")
        mock_eq.get_all_active.return_value = []
        with patch("flask_login.utils._get_user", return_value=_FakeUser(role="admin")):
            resp = client.post("/spare_parts/edit/1", data={"name": "X"})
        assert resp.status_code == 404

    @patch("app.routes.spare_parts.crud.render_template", return_value="ok")
    @patch("app.routes.spare_parts.crud.get_categories", return_value=[])
    @patch("app.routes.spare_parts.crud.EquipmentRepository")
    @patch("app.routes.spare_parts.crud.update_spare_part")
    @patch("app.db")
    def test_edit_spare_part_post_other_error(self, mock_db, mock_update, mock_eq, mock_cats, mock_rt, client, app):
        sp = MagicMock()
        sp.image_path = None
        mock_db.session.get.return_value = sp
        mock_update.return_value = (None, "Validation error")
        mock_eq.get_all_active.return_value = []
        with patch("flask_login.utils._get_user", return_value=_FakeUser(role="admin")):
            resp = client.post("/spare_parts/edit/1", data={"name": "X"})
        assert resp.status_code == 200

    # -- /edit/<id> POST with image upload + delete old --
    @patch("app.routes.spare_parts.crud.render_template", return_value="ok")
    @patch("app.routes.spare_parts.crud.get_categories", return_value=[])
    @patch("app.routes.spare_parts.crud.EquipmentRepository")
    @patch("app.routes.spare_parts.crud.safe_commit", return_value=True)
    @patch("app.routes.spare_parts.crud.save_image_to_disk", return_value="/uploads/new.jpg")
    @patch("app.routes.spare_parts.crud.delete_image_from_disk")
    @patch("app.routes.spare_parts.crud.update_spare_part")
    @patch("app.db")
    def test_edit_spare_part_post_with_image(self, mock_db, mock_update, mock_del_img, mock_save_img,
                                              mock_commit, mock_eq, mock_cats, mock_rt, client, app):
        sp = MagicMock()
        sp.image_path = "/uploads/old.jpg"
        mock_db.session.get.return_value = sp
        mock_update.return_value = (sp, None)
        mock_eq.get_all_active.return_value = []
        import io
        data = {
            "name": "Updated",
            "image": (io.BytesIO(b"fake"), "new.jpg"),
        }
        with patch("flask_login.utils._get_user", return_value=_FakeUser(role="admin")):
            resp = client.post("/spare_parts/edit/1", data=data, content_type="multipart/form-data")
        assert resp.status_code == 302
        mock_del_img.assert_called_once()
        mock_save_img.assert_called_once()

    # -- /edit/<id> POST with delete_image checkbox --
    @patch("app.routes.spare_parts.crud.render_template", return_value="ok")
    @patch("app.routes.spare_parts.crud.get_categories", return_value=[])
    @patch("app.routes.spare_parts.crud.EquipmentRepository")
    @patch("app.routes.spare_parts.crud.safe_commit", return_value=True)
    @patch("app.routes.spare_parts.crud.delete_image_from_disk")
    @patch("app.routes.spare_parts.crud.update_spare_part")
    @patch("app.db")
    def test_edit_spare_part_delete_image(self, mock_db, mock_update, mock_del_img,
                                           mock_commit, mock_eq, mock_cats, mock_rt, client, app):
        sp = MagicMock()
        sp.image_path = "/uploads/old.jpg"
        mock_db.session.get.return_value = sp
        mock_update.return_value = (sp, None)
        mock_eq.get_all_active.return_value = []
        with patch("flask_login.utils._get_user", return_value=_FakeUser(role="admin")):
            resp = client.post("/spare_parts/edit/1", data={
                "name": "Updated", "delete_image": "yes",
            })
        assert resp.status_code == 302
        mock_del_img.assert_called_once()

    # -- /receive/<id> --
    @patch("app.routes.spare_parts.crud.safe_commit", return_value=True)
    @patch("app.routes.spare_parts.crud.receive_stock")
    def test_receive_spare_part_success(self, mock_receive, mock_commit, client, app):
        mock_receive.return_value = ({"quantity_added": 10, "unit": "pcs", "new_total": 20}, None)
        with patch("flask_login.utils._get_user", return_value=_FakeUser(role="admin")):
            resp = client.post("/spare_parts/receive/1", data={"quantity": "10"})
        assert resp.status_code == 302

    def test_receive_spare_part_forbidden(self, client, app):
        with patch("flask_login.utils._get_user", return_value=_FakeUser(role="viewer")):
            resp = client.post("/spare_parts/receive/1", data={"quantity": "10"})
        assert resp.status_code == 302

    @patch("app.routes.spare_parts.crud.receive_stock")
    def test_receive_spare_part_not_found(self, mock_receive, client, app):
        mock_receive.return_value = (None, "not_found")
        with patch("flask_login.utils._get_user", return_value=_FakeUser(role="admin")):
            resp = client.post("/spare_parts/receive/1", data={"quantity": "10"})
        assert resp.status_code == 404

    @patch("app.routes.spare_parts.crud.receive_stock")
    def test_receive_spare_part_error(self, mock_receive, client, app):
        mock_receive.return_value = (None, "Invalid quantity")
        with patch("flask_login.utils._get_user", return_value=_FakeUser(role="admin")):
            resp = client.post("/spare_parts/receive/1", data={"quantity": "0"})
        assert resp.status_code == 302

    def test_receive_spare_part_value_error(self, client, app):
        with patch("flask_login.utils._get_user", return_value=_FakeUser(role="admin")):
            with patch("app.routes.spare_parts.crud.receive_stock", side_effect=ValueError("bad")):
                resp = client.post("/spare_parts/receive/1", data={"quantity": "bad"})
        assert resp.status_code == 302

    # -- /consume/<id> --
    @patch("app.routes.spare_parts.crud.safe_commit", return_value=True)
    @patch("app.routes.spare_parts.crud.consume_stock")
    def test_consume_spare_part_success(self, mock_consume, mock_commit, client, app):
        mock_consume.return_value = ({"consumed": 5, "unit": "pcs", "remaining": 15}, None)
        with patch("flask_login.utils._get_user", return_value=_FakeUser()):
            resp = client.post("/spare_parts/consume/1", data={
                "quantity": "5", "purpose": "repair",
            })
        assert resp.status_code == 302

    @patch("app.routes.spare_parts.crud.consume_stock")
    def test_consume_spare_part_not_found(self, mock_consume, client, app):
        mock_consume.return_value = (None, "not_found")
        with patch("flask_login.utils._get_user", return_value=_FakeUser()):
            resp = client.post("/spare_parts/consume/1", data={"quantity": "5"})
        assert resp.status_code == 404

    @patch("app.routes.spare_parts.crud.consume_stock")
    def test_consume_spare_part_insufficient(self, mock_consume, client, app):
        mock_consume.return_value = (None, "Insufficient stock")
        with patch("flask_login.utils._get_user", return_value=_FakeUser()):
            resp = client.post("/spare_parts/consume/1", data={"quantity": "100"})
        assert resp.status_code == 302

    def test_consume_spare_part_value_error(self, client, app):
        with patch("flask_login.utils._get_user", return_value=_FakeUser()):
            resp = client.post("/spare_parts/consume/1", data={"quantity": "bad"})
        assert resp.status_code == 302

    # -- /dispose/<id> --
    @patch("app.routes.spare_parts.crud.safe_commit", return_value=True)
    @patch("app.routes.spare_parts.crud.svc_dispose")
    def test_dispose_spare_part_success(self, mock_dispose, mock_commit, client, app):
        mock_dispose.return_value = ("Bearing", None)
        with patch("flask_login.utils._get_user", return_value=_FakeUser(role="senior")):
            resp = client.post("/spare_parts/dispose/1", data={"reason": "Worn out"})
        assert resp.status_code == 302

    def test_dispose_spare_part_forbidden(self, client, app):
        with patch("flask_login.utils._get_user", return_value=_FakeUser(role="chemist")):
            resp = client.post("/spare_parts/dispose/1")
        assert resp.status_code == 302

    @patch("app.routes.spare_parts.crud.svc_dispose")
    def test_dispose_spare_part_not_found(self, mock_dispose, client, app):
        mock_dispose.return_value = (None, "not_found")
        with patch("flask_login.utils._get_user", return_value=_FakeUser(role="admin")):
            resp = client.post("/spare_parts/dispose/999")
        assert resp.status_code == 404

    @patch("app.routes.spare_parts.crud.svc_dispose")
    def test_dispose_spare_part_error(self, mock_dispose, client, app):
        mock_dispose.return_value = (None, "Already disposed")
        with patch("flask_login.utils._get_user", return_value=_FakeUser(role="admin")):
            resp = client.post("/spare_parts/dispose/1")
        assert resp.status_code == 302

    # -- /delete/<id> --
    @patch("app.routes.spare_parts.crud.safe_commit", return_value=True)
    @patch("app.routes.spare_parts.crud.delete_spare_part_permanently")
    def test_delete_spare_part_success(self, mock_delete, mock_commit, client, app):
        mock_delete.return_value = ("Bearing", None)
        with patch("flask_login.utils._get_user", return_value=_FakeUser(role="admin")):
            resp = client.post("/spare_parts/delete/1")
        assert resp.status_code == 302

    def test_delete_spare_part_forbidden(self, client, app):
        with patch("flask_login.utils._get_user", return_value=_FakeUser(role="manager")):
            resp = client.post("/spare_parts/delete/1")
        assert resp.status_code == 302

    @patch("app.routes.spare_parts.crud.delete_spare_part_permanently")
    def test_delete_spare_part_not_found(self, mock_delete, client, app):
        mock_delete.return_value = (None, "not_found")
        with patch("flask_login.utils._get_user", return_value=_FakeUser(role="admin")):
            resp = client.post("/spare_parts/delete/999")
        assert resp.status_code == 404

    @patch("app.routes.spare_parts.crud.delete_spare_part_permanently")
    def test_delete_spare_part_error(self, mock_delete, client, app):
        mock_delete.return_value = (None, "Has active usages")
        with patch("flask_login.utils._get_user", return_value=_FakeUser(role="admin")):
            resp = client.post("/spare_parts/delete/1")
        assert resp.status_code == 302


# ---------------------------------------------------------------------------
# Constants coverage for waste.py module-level dicts
# ---------------------------------------------------------------------------

class TestWasteConstants:
    """Ensure module-level constants are accessible (covers import lines)."""

    def test_disposal_methods_dict(self):
        from app.routes.chemicals.waste import DISPOSAL_METHODS
        assert "sewer" in DISPOSAL_METHODS
        assert len(DISPOSAL_METHODS) == 6

    def test_hazard_types_dict(self):
        from app.routes.chemicals.waste import HAZARD_TYPES
        assert "toxic" in HAZARD_TYPES
        assert len(HAZARD_TYPES) == 6

    def test_lab_types_dict(self):
        from app.routes.chemicals.waste import LAB_TYPES
        assert "coal" in LAB_TYPES
