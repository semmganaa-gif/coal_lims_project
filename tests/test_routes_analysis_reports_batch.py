# tests/test_routes_analysis_reports_batch.py
# -*- coding: utf-8 -*-
"""
Comprehensive tests for:
  - app/routes/analysis/senior.py
  - app/routes/api/analysis_save.py
  - app/routes/reports/dashboard.py

Target: 80%+ coverage for each file.
"""

import pytest
from unittest.mock import patch, MagicMock
from flask import Flask, Blueprint
from datetime import datetime


# =========================================================================
# Helpers
# =========================================================================


def _make_user(role="senior", user_id=1, username="testuser"):
    """Create a mock user with the given role."""
    user = MagicMock()
    user.role = role
    user.id = user_id
    user.username = username
    user.is_authenticated = True
    user.is_active = True
    user.is_anonymous = False
    user.get_id.return_value = str(user_id)
    return user


# =========================================================================
# Fixtures
# =========================================================================


@pytest.fixture
def senior_user():
    return _make_user("senior")


@pytest.fixture
def admin_user():
    return _make_user("admin", user_id=2, username="admin")


@pytest.fixture
def chemist_user():
    return _make_user("chemist", user_id=3, username="chemist")


@pytest.fixture
def viewer_user():
    return _make_user("viewer", user_id=4, username="viewer")


# ---------------------------------------------------------------------------
# App fixture for senior.py
# ---------------------------------------------------------------------------
@pytest.fixture
def senior_app(senior_user):
    """Flask app with senior routes registered."""
    app = Flask(__name__)
    app.config["TESTING"] = True
    app.config["SECRET_KEY"] = "test-secret"
    app.config["WTF_CSRF_ENABLED"] = False
    app.config["LOGIN_DISABLED"] = True

    from flask_login import LoginManager
    lm = LoginManager(app)

    @lm.user_loader
    def load_user(uid):
        return senior_user

    # Babel — `_role_denied_response()` нь `flash(_(...))` дуудна (analyst-role
    # хэрэглэгчийн route-уудад permission деny хийгдэх үед). Babel-гүй бол
    # `KeyError: 'babel'` гарна.
    from flask_babel import Babel
    Babel(app)

    mock_cache = MagicMock()
    mock_cache.cached = lambda **kw: lambda f: f

    with patch("app.routes.analysis.senior.cache", mock_cache):
        bp = Blueprint("analysis", __name__, url_prefix="/analysis")
        from app.routes.analysis.senior import register_routes
        register_routes(bp)
        app.register_blueprint(bp)

    return app


# ---------------------------------------------------------------------------
# App fixture for analysis_save.py  (patches stay active via yield)
# ---------------------------------------------------------------------------
@pytest.fixture
def save_app(chemist_user):
    """Flask app with analysis_save routes registered. Patches remain active."""
    app = Flask(__name__)
    app.config["TESTING"] = True
    app.config["SECRET_KEY"] = "test-secret"
    app.config["WTF_CSRF_ENABLED"] = False
    app.config["LOGIN_DISABLED"] = True

    from flask_login import LoginManager
    lm = LoginManager(app)

    @lm.user_loader
    def load_user(uid):
        return chemist_user

    # Flask-Babel init — route нь `flask_babel.gettext` (`_`) ашигладаг
    # (жишээ: "JSON массив байх ёстой"). Babel extension-гүй бол `_(...)`
    # `KeyError: 'babel'` шиднэ.
    from flask_babel import Babel
    Babel(app)

    mock_limiter = MagicMock()
    mock_limiter.limit = lambda *a, **kw: lambda f: f

    # Sprint 4 closeout-н дараа route нь `db`-г шууд хэрэглэхээ больсон —
    # `save_results_batch` service function-аар дамжуулна. Тиймээс энэ
    # fixture зөвхөн limiter-ийг patch хийнэ. DB-той тестүүд service
    # boundary-р (`app.routes.api.analysis_save.save_results_batch`) mock
    # хийнэ.
    p1 = patch("app.routes.api.analysis_save.limiter", mock_limiter)
    p1.start()

    bp = Blueprint("api", __name__, url_prefix="/api")
    from app.routes.api.analysis_save import register_save_routes
    register_save_routes(bp)
    app.register_blueprint(bp)

    yield app

    p1.stop()


# ---------------------------------------------------------------------------
# App fixture for dashboard.py
# ---------------------------------------------------------------------------
@pytest.fixture
def dashboard_app(senior_user):
    """Flask app with reports dashboard route."""
    flask_app = Flask(__name__)
    flask_app.config["TESTING"] = True
    flask_app.config["SECRET_KEY"] = "test-secret"
    flask_app.config["WTF_CSRF_ENABLED"] = False
    flask_app.config["LOGIN_DISABLED"] = True

    from flask_login import LoginManager
    lm = LoginManager(flask_app)

    @lm.user_loader
    def load_user(uid):
        return senior_user

    # Babel — `_role_denied_response()` `flash(_(...))` дуудна.
    from flask_babel import Babel
    Babel(flask_app)

    # Import the blueprint (module-level singleton)
    from app.routes.reports.routes import reports_bp
    # Import the dashboard module to register its route
    import app.routes.reports.dashboard  # noqa: F401

    try:
        flask_app.register_blueprint(reports_bp)
    except Exception:
        pass

    return flask_app


# =========================================================================
# TESTS FOR: app/routes/analysis/senior.py
# =========================================================================


class TestAhlahDashboard:
    """Tests for GET /analysis/ahlah_dashboard"""

    @patch("app.routes.analysis.senior.get_error_reason_labels", return_value={"ERR1": "Error 1"})
    @patch("app.routes.analysis.senior.load_analysis_schemas", return_value={"Mad": {}})
    @patch("app.routes.analysis.senior.render_template", return_value="OK")
    def test_ahlah_dashboard_success(self, mock_render, mock_schemas, mock_labels, senior_app, senior_user):
        with senior_app.test_client() as client:
            with patch("flask_login.utils._get_user", return_value=senior_user):
                resp = client.get("/analysis/ahlah_dashboard")
        assert resp.status_code == 200
        mock_schemas.assert_called_once()
        mock_labels.assert_called_once()
        mock_render.assert_called_once()
        call_args = mock_render.call_args
        assert call_args[0][0] == "ahlah_dashboard.html"
        assert call_args[1]["use_aggrid"] is True

    @patch("app.routes.analysis.senior.get_error_reason_labels", return_value={})
    @patch("app.routes.analysis.senior.load_analysis_schemas", return_value={})
    @patch("app.routes.analysis.senior.render_template", return_value="OK")
    def test_ahlah_dashboard_admin_access(self, mock_render, mock_schemas, mock_labels, senior_app):
        admin = _make_user("admin")
        with senior_app.test_client() as client:
            with patch("flask_login.utils._get_user", return_value=admin):
                resp = client.get("/analysis/ahlah_dashboard")
        assert resp.status_code == 200

    @patch("app.routes.analysis.senior.get_error_reason_labels", return_value={})
    @patch("app.routes.analysis.senior.load_analysis_schemas", return_value={})
    def test_ahlah_dashboard_forbidden_for_chemist(self, mock_schemas, mock_labels, senior_app):
        chemist = _make_user("chemist")
        with senior_app.test_client() as client:
            with patch("flask_login.utils._get_user", return_value=chemist):
                resp = client.get("/analysis/ahlah_dashboard")
        assert resp.status_code in (302, 403)


class TestApiAhlahData:
    """Tests for GET /analysis/api/ahlah_data"""

    @patch("app.routes.analysis.senior.build_pending_results", return_value=[{"id": 1}])
    def test_api_ahlah_data_success(self, mock_build, senior_app, senior_user):
        with senior_app.test_client() as client:
            with patch("flask_login.utils._get_user", return_value=senior_user):
                resp = client.get("/analysis/api/ahlah_data?start_date=2026-01-01&end_date=2026-01-31&sample_name=S1")
        assert resp.status_code == 200
        data = resp.get_json()
        assert len(data) == 1
        mock_build.assert_called_once_with(
            start_date="2026-01-01",
            end_date="2026-01-31",
            sample_name="S1",
        )

    @patch("app.routes.analysis.senior.build_pending_results", return_value=[])
    def test_api_ahlah_data_no_params(self, mock_build, senior_app, senior_user):
        with senior_app.test_client() as client:
            with patch("flask_login.utils._get_user", return_value=senior_user):
                resp = client.get("/analysis/api/ahlah_data")
        assert resp.status_code == 200
        mock_build.assert_called_once_with(start_date=None, end_date=None, sample_name=None)

    @patch("app.routes.analysis.senior.build_pending_results", return_value=[])
    def test_api_ahlah_data_forbidden_for_viewer(self, mock_build, senior_app):
        viewer = _make_user("viewer")
        with senior_app.test_client() as client:
            with patch("flask_login.utils._get_user", return_value=viewer):
                resp = client.get("/analysis/api/ahlah_data")
        assert resp.status_code in (302, 403)


class TestUpdateResultStatus:
    """Tests for POST /analysis/update_result_status/<result_id>/<new_status>"""

    @patch("app.routes.analysis.senior.update_result_status")
    def test_approve_result_json(self, mock_update, senior_app, senior_user):
        mock_update.return_value = ({"success": True, "id": 1}, None, None)
        with senior_app.test_client() as client:
            with patch("flask_login.utils._get_user", return_value=senior_user):
                resp = client.post(
                    "/analysis/update_result_status/1/approved",
                    json={"rejection_comment": None, "rejection_category": None},
                )
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["success"] is True

    @patch("app.routes.analysis.senior.update_result_status")
    def test_reject_result_with_comment(self, mock_update, senior_app, senior_user):
        mock_update.return_value = ({"success": True}, None, None)
        with senior_app.test_client() as client:
            with patch("flask_login.utils._get_user", return_value=senior_user):
                resp = client.post(
                    "/analysis/update_result_status/5/rejected",
                    json={"rejection_comment": "Bad data", "rejection_category": "RANGE"},
                )
        assert resp.status_code == 200
        mock_update.assert_called_once_with(
            result_id=5,
            new_status="rejected",
            rejection_comment="Bad data",
            rejection_category="RANGE",
        )

    @patch("app.routes.analysis.senior.update_result_status")
    def test_update_result_error(self, mock_update, senior_app, senior_user):
        mock_update.return_value = (None, "Result not found", 404)
        with senior_app.test_client() as client:
            with patch("flask_login.utils._get_user", return_value=senior_user):
                resp = client.post("/analysis/update_result_status/999/approved", json={})
        assert resp.status_code == 404
        assert resp.get_json()["message"] == "Result not found"

    def test_update_result_forbidden_chemist(self, senior_app):
        chemist = _make_user("chemist")
        with senior_app.test_client() as client:
            with patch("flask_login.utils._get_user", return_value=chemist):
                resp = client.post("/analysis/update_result_status/1/approved", json={})
        assert resp.status_code == 403

    def test_update_result_forbidden_viewer(self, senior_app):
        viewer = _make_user("viewer")
        with senior_app.test_client() as client:
            with patch("flask_login.utils._get_user", return_value=viewer):
                resp = client.post("/analysis/update_result_status/1/approved", json={})
        assert resp.status_code == 403

    @patch("app.routes.analysis.senior.update_result_status")
    def test_update_result_form_data(self, mock_update, senior_app, senior_user):
        """Test with form data instead of JSON."""
        mock_update.return_value = ({"success": True}, None, None)
        with senior_app.test_client() as client:
            with patch("flask_login.utils._get_user", return_value=senior_user):
                resp = client.post(
                    "/analysis/update_result_status/1/approved",
                    data={"rejection_comment": "test"},
                )
        assert resp.status_code == 200

    @patch("app.routes.analysis.senior.update_result_status")
    def test_update_result_admin_access(self, mock_update, senior_app):
        admin = _make_user("admin")
        mock_update.return_value = ({"success": True}, None, None)
        with senior_app.test_client() as client:
            with patch("flask_login.utils._get_user", return_value=admin):
                resp = client.post("/analysis/update_result_status/1/approved", json={})
        assert resp.status_code == 200


class TestBulkUpdateStatus:
    """Tests for POST /analysis/bulk_update_status"""

    @patch("app.routes.analysis.senior.bulk_update_result_status")
    def test_bulk_approve(self, mock_bulk, senior_app, senior_user):
        mock_bulk.return_value = ({"updated": 3}, None, None)
        with senior_app.test_client() as client:
            with patch("flask_login.utils._get_user", return_value=senior_user):
                resp = client.post("/analysis/bulk_update_status", json={
                    "result_ids": [1, 2, 3],
                    "status": "approved",
                })
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["updated"] == 3
        mock_bulk.assert_called_once_with(
            result_ids=[1, 2, 3],
            new_status="approved",
            rejection_comment=None,
            rejection_category=None,
            username="testuser",
        )

    @patch("app.routes.analysis.senior.bulk_update_result_status")
    def test_bulk_reject_with_category(self, mock_bulk, senior_app, senior_user):
        mock_bulk.return_value = ({"updated": 2}, None, None)
        with senior_app.test_client() as client:
            with patch("flask_login.utils._get_user", return_value=senior_user):
                resp = client.post("/analysis/bulk_update_status", json={
                    "result_ids": [4, 5],
                    "status": "rejected",
                    "rejection_comment": "Batch reject",
                    "rejection_category": "RANGE",
                })
        assert resp.status_code == 200

    @patch("app.routes.analysis.senior.bulk_update_result_status")
    def test_bulk_update_error(self, mock_bulk, senior_app, senior_user):
        mock_bulk.return_value = (None, "Invalid status", 400)
        with senior_app.test_client() as client:
            with patch("flask_login.utils._get_user", return_value=senior_user):
                resp = client.post("/analysis/bulk_update_status", json={
                    "result_ids": [],
                    "status": "bad_status",
                })
        assert resp.status_code == 400
        assert resp.get_json()["message"] == "Invalid status"

    def test_bulk_update_forbidden(self, senior_app):
        chemist = _make_user("chemist")
        with senior_app.test_client() as client:
            with patch("flask_login.utils._get_user", return_value=chemist):
                resp = client.post("/analysis/bulk_update_status", json={"result_ids": [1]})
        assert resp.status_code == 403

    @patch("app.routes.analysis.senior.bulk_update_result_status")
    def test_bulk_update_no_json(self, mock_bulk, senior_app, senior_user):
        """When no JSON body, defaults to empty dict."""
        mock_bulk.return_value = ({"updated": 0}, None, None)
        with senior_app.test_client() as client:
            with patch("flask_login.utils._get_user", return_value=senior_user):
                resp = client.post("/analysis/bulk_update_status")
        assert resp.status_code == 200


class TestApiAhlahStats:
    """Tests for GET /analysis/api/ahlah_stats"""

    @patch("app.routes.analysis.senior.build_dashboard_stats", return_value={"total": 42})
    def test_stats_success(self, mock_stats, senior_app, senior_user):
        with senior_app.test_client() as client:
            with patch("flask_login.utils._get_user", return_value=senior_user):
                resp = client.get("/analysis/api/ahlah_stats")
        assert resp.status_code == 200
        assert resp.get_json()["total"] == 42
        mock_stats.assert_called_once()

    @patch("app.routes.analysis.senior.build_dashboard_stats", return_value={})
    def test_stats_forbidden_for_viewer(self, mock_stats, senior_app):
        viewer = _make_user("viewer")
        with senior_app.test_client() as client:
            with patch("flask_login.utils._get_user", return_value=viewer):
                resp = client.get("/analysis/api/ahlah_stats")
        assert resp.status_code in (302, 403)


class TestSelectRepeatResult:
    """Tests for POST /analysis/api/select_repeat_result/<result_id>"""

    @patch("app.routes.analysis.senior.select_repeat_result")
    def test_select_repeat_use_original(self, mock_select, senior_app, senior_user):
        mock_select.return_value = ({"success": True}, None, None)
        with senior_app.test_client() as client:
            with patch("flask_login.utils._get_user", return_value=senior_user):
                resp = client.post(
                    "/analysis/api/select_repeat_result/10",
                    json={"use_original": True},
                )
        assert resp.status_code == 200
        mock_select.assert_called_once_with(result_id=10, use_original=True)

    @patch("app.routes.analysis.senior.select_repeat_result")
    def test_select_repeat_use_new(self, mock_select, senior_app, senior_user):
        mock_select.return_value = ({"success": True}, None, None)
        with senior_app.test_client() as client:
            with patch("flask_login.utils._get_user", return_value=senior_user):
                resp = client.post(
                    "/analysis/api/select_repeat_result/10",
                    json={"use_original": False},
                )
        assert resp.status_code == 200
        mock_select.assert_called_once_with(result_id=10, use_original=False)

    @patch("app.routes.analysis.senior.select_repeat_result")
    def test_select_repeat_error(self, mock_select, senior_app, senior_user):
        mock_select.return_value = (None, "Not found", 404)
        with senior_app.test_client() as client:
            with patch("flask_login.utils._get_user", return_value=senior_user):
                resp = client.post("/analysis/api/select_repeat_result/999", json={})
        assert resp.status_code == 404
        assert resp.get_json()["message"] == "Not found"

    @patch("app.routes.analysis.senior.select_repeat_result")
    def test_select_repeat_no_json(self, mock_select, senior_app, senior_user):
        """No JSON body - use_original defaults to False."""
        mock_select.return_value = ({"success": True}, None, None)
        with senior_app.test_client() as client:
            with patch("flask_login.utils._get_user", return_value=senior_user):
                resp = client.post("/analysis/api/select_repeat_result/10")
        assert resp.status_code == 200
        mock_select.assert_called_once_with(result_id=10, use_original=False)

    @patch("app.routes.analysis.senior.select_repeat_result")
    def test_select_repeat_forbidden(self, mock_select, senior_app):
        viewer = _make_user("viewer")
        with senior_app.test_client() as client:
            with patch("flask_login.utils._get_user", return_value=viewer):
                resp = client.post("/analysis/api/select_repeat_result/10", json={})
        assert resp.status_code in (302, 403)


# =========================================================================
# TESTS FOR: app/routes/api/analysis_save.py
# =========================================================================


class TestSaveResults:
    """Tests for POST /api/save_results"""

    @patch("app.routes.api.analysis_save.track_analysis")
    @patch("app.routes.api.analysis_save.save_results_batch")
    @patch("app.routes.api.analysis_save.validate_save_results_batch")
    @patch("app.routes.api.analysis_save.AnalysisResultSchema")
    def test_save_single_item_success(self, mock_schema_cls, mock_validate, mock_batch, mock_track, save_app, chemist_user):
        mock_schema_cls.return_value.validate.return_value = {}
        mock_validate.return_value = (True, [{"sample_id": 1}], [])
        mock_batch.return_value = {
            "status": "ok",
            "saved": [{"success": True, "analysis_code": "Mad", "status": "completed"}],
            "errors": [],
            "message": None,
        }

        with save_app.test_client() as client:
            with patch("flask_login.utils._get_user", return_value=chemist_user):
                resp = client.post("/api/save_results", json={"sample_id": 1, "analysis_code": "Mad"})

        assert resp.status_code == 200
        data = resp.get_json()
        assert "1" in data["message"]
        mock_track.assert_called_once_with(analysis_type="Mad", status="completed")

    @patch("app.routes.api.analysis_save.track_analysis")
    @patch("app.routes.api.analysis_save.save_results_batch")
    @patch("app.routes.api.analysis_save.validate_save_results_batch")
    @patch("app.routes.api.analysis_save.AnalysisResultSchema")
    def test_save_batch_success(self, mock_schema_cls, mock_validate, mock_batch, mock_track, save_app, chemist_user):
        mock_schema_cls.return_value.validate.return_value = {}
        mock_validate.return_value = (True, [{}, {}], [])
        mock_batch.return_value = {
            "status": "ok",
            "saved": [
                {"success": True, "analysis_code": "Aad", "status": "completed"},
                {"success": True, "analysis_code": "Aad", "status": "completed"},
            ],
            "errors": [],
            "message": None,
        }

        with save_app.test_client() as client:
            with patch("flask_login.utils._get_user", return_value=chemist_user):
                resp = client.post("/api/save_results", json=[
                    {"sample_id": 1, "analysis_code": "Mad"},
                    {"sample_id": 2, "analysis_code": "Aad"},
                ])

        assert resp.status_code == 200
        data = resp.get_json()
        assert "2" in data["message"]
        assert mock_track.call_count == 2

    @patch("app.routes.api.analysis_save.track_analysis")
    @patch("app.routes.api.analysis_save.save_results_batch")
    @patch("app.routes.api.analysis_save.validate_save_results_batch")
    @patch("app.routes.api.analysis_save.AnalysisResultSchema")
    def test_save_partial_failure(self, mock_schema_cls, mock_validate, mock_batch, mock_track, save_app, chemist_user):
        mock_schema_cls.return_value.validate.return_value = {}
        mock_validate.return_value = (True, [{}, {}], [])
        mock_batch.return_value = {
            "status": "ok",
            "saved": [{"success": True, "analysis_code": "Mad", "status": "completed"}],
            "errors": [{"index": 1, "sample_id": None, "error": "Invalid data"}],
            "message": None,
        }

        with save_app.test_client() as client:
            with patch("flask_login.utils._get_user", return_value=chemist_user):
                resp = client.post("/api/save_results", json=[{"a": 1}, {"a": 2}])

        assert resp.status_code == 207
        data = resp.get_json()
        assert len(data["errors"]) == 1

    def test_save_no_json(self, save_app, chemist_user):
        with save_app.test_client() as client:
            with patch("flask_login.utils._get_user", return_value=chemist_user):
                resp = client.post("/api/save_results", content_type="application/json", data="not json")
        assert resp.status_code == 400

    def test_save_empty_array(self, save_app, chemist_user):
        with save_app.test_client() as client:
            with patch("flask_login.utils._get_user", return_value=chemist_user):
                resp = client.post("/api/save_results", json=[])
        assert resp.status_code == 400

    def test_save_forbidden_viewer(self, save_app):
        viewer = _make_user("viewer")
        with save_app.test_client() as client:
            with patch("flask_login.utils._get_user", return_value=viewer):
                resp = client.post("/api/save_results", json=[{"a": 1}])
        assert resp.status_code == 403

    @patch("app.routes.api.analysis_save.track_analysis")
    @patch("app.routes.api.analysis_save.save_results_batch")
    @patch("app.routes.api.analysis_save.validate_save_results_batch")
    @patch("app.routes.api.analysis_save.AnalysisResultSchema")
    def test_save_schema_validation_warnings(self, mock_schema_cls, mock_validate, mock_batch, mock_track, save_app, chemist_user):
        """Schema validation errors are logged but do not block saving."""
        mock_schema_cls.return_value.validate.return_value = {"sample_id": ["Required"]}
        mock_validate.return_value = (False, [{}], ["warning"])
        mock_batch.return_value = {
            "status": "ok",
            "saved": [{"success": True, "analysis_code": "X", "status": "done"}],
            "errors": [],
            "message": None,
        }

        with save_app.test_client() as client:
            with patch("flask_login.utils._get_user", return_value=chemist_user):
                resp = client.post("/api/save_results", json={"sample_id": 1})

        assert resp.status_code == 200

    @patch("app.routes.api.analysis_save.save_results_batch")
    @patch("app.routes.api.analysis_save.validate_save_results_batch")
    @patch("app.routes.api.analysis_save.AnalysisResultSchema")
    def test_save_stale_data_error(self, mock_schema_cls, mock_validate, mock_batch, save_app, chemist_user):
        """Service-аас 'conflict' статус ирэх үед 409 буцаах."""
        mock_schema_cls.return_value.validate.return_value = {}
        mock_validate.return_value = (True, [{}], [])
        mock_batch.return_value = {
            "status": "conflict",
            "saved": [],
            "errors": [],
            "message": "Concurrent edit",
        }

        with save_app.test_client() as client:
            with patch("flask_login.utils._get_user", return_value=chemist_user):
                resp = client.post("/api/save_results", json={"sample_id": 1})

        assert resp.status_code == 409

    @patch("app.routes.api.analysis_save.save_results_batch")
    @patch("app.routes.api.analysis_save.validate_save_results_batch")
    @patch("app.routes.api.analysis_save.AnalysisResultSchema")
    def test_save_sqlalchemy_error_on_commit(self, mock_schema_cls, mock_validate, mock_batch, save_app, chemist_user):
        """Service-аас 'db_error' статус ирэх үед 500 буцаах."""
        mock_schema_cls.return_value.validate.return_value = {}
        mock_validate.return_value = (True, [{}], [])

        mock_batch.return_value = {
            "status": "db_error",
            "saved": [],
            "errors": [],
            "message": "DB error",
        }

        with save_app.test_client() as client:
            with patch("flask_login.utils._get_user", return_value=chemist_user):
                resp = client.post("/api/save_results", json={"sample_id": 1})

        assert resp.status_code == 500

    @patch("app.routes.api.analysis_save.track_analysis")
    @patch("app.routes.api.analysis_save.save_results_batch")
    @patch("app.routes.api.analysis_save.validate_save_results_batch")
    @patch("app.routes.api.analysis_save.AnalysisResultSchema")
    def test_save_value_error_in_loop(self, mock_schema_cls, mock_validate, mock_batch, mock_track, save_app, chemist_user):
        """Item-level ValueError бол service-аас errors жагсаалтад орно (207)."""
        mock_schema_cls.return_value.validate.return_value = {}
        mock_validate.return_value = (True, [{}], [])
        mock_batch.return_value = {
            "status": "ok",
            "saved": [],
            "errors": [{"index": 0, "sample_id": 1, "error": "bad value"}],
            "message": None,
        }

        with save_app.test_client() as client:
            with patch("flask_login.utils._get_user", return_value=chemist_user):
                resp = client.post("/api/save_results", json={"sample_id": 1})

        assert resp.status_code == 207
        data = resp.get_json()
        assert len(data["errors"]) == 1
        assert data["errors"][0]["error"] == "bad value"

    @patch("app.routes.api.analysis_save.track_analysis")
    @patch("app.routes.api.analysis_save.save_results_batch")
    @patch("app.routes.api.analysis_save.validate_save_results_batch")
    @patch("app.routes.api.analysis_save.AnalysisResultSchema")
    def test_save_sqlalchemy_error_in_loop(self, mock_schema_cls, mock_validate, mock_batch, mock_track, save_app, chemist_user):
        """Item-level SQLAlchemyError бол service-аас errors-д орно (207)."""
        mock_schema_cls.return_value.validate.return_value = {}
        mock_validate.return_value = (True, [{}], [])
        mock_batch.return_value = {
            "status": "ok",
            "saved": [],
            "errors": [{"index": 0, "sample_id": 1, "error": "db error in loop"}],
            "message": None,
        }

        with save_app.test_client() as client:
            with patch("flask_login.utils._get_user", return_value=chemist_user):
                resp = client.post("/api/save_results", json={"sample_id": 1})

        assert resp.status_code == 207
        data = resp.get_json()
        assert len(data["errors"]) == 1

    def test_save_senior_role_allowed(self, save_app):
        """Senior role should also be allowed to save."""
        senior = _make_user("senior")
        with save_app.test_client() as client:
            with patch("flask_login.utils._get_user", return_value=senior):
                resp = client.post("/api/save_results", json=[])
        assert resp.status_code == 400

    def test_save_admin_role_allowed(self, save_app):
        """Admin role should also be allowed to save."""
        admin = _make_user("admin")
        with save_app.test_client() as client:
            with patch("flask_login.utils._get_user", return_value=admin):
                resp = client.post("/api/save_results", json=[])
        assert resp.status_code == 400

    @patch("app.routes.api.analysis_save.track_analysis")
    @patch("app.routes.api.analysis_save.save_results_batch")
    @patch("app.routes.api.analysis_save.validate_save_results_batch")
    @patch("app.routes.api.analysis_save.AnalysisResultSchema")
    def test_save_result_not_tracked_if_not_success(self, mock_schema_cls, mock_validate, mock_batch, mock_track, save_app, chemist_user):
        """track_analysis үл дуудагдах: saved result-ийн success=False үед."""
        mock_schema_cls.return_value.validate.return_value = {}
        mock_validate.return_value = (True, [{}], [])
        mock_batch.return_value = {
            "status": "ok",
            "saved": [{"success": False, "analysis_code": "Mad"}],
            "errors": [],
            "message": None,
        }

        with save_app.test_client() as client:
            with patch("flask_login.utils._get_user", return_value=chemist_user):
                resp = client.post("/api/save_results", json={"sample_id": 1})

        assert resp.status_code == 200
        mock_track.assert_not_called()

    def test_save_non_list_non_dict(self, save_app, chemist_user):
        """Sending a string JSON body (not list or dict)."""
        with save_app.test_client() as client:
            with patch("flask_login.utils._get_user", return_value=chemist_user):
                resp = client.post(
                    "/api/save_results",
                    data='"just a string"',
                    content_type="application/json",
                )
        assert resp.status_code == 400


class TestUpdateResultStatusSave:
    """Tests for POST /api/update_result_status/<result_id>/<new_status>"""

    @patch("app.routes.api.analysis_save.update_result_status_api")
    def test_approve_ajax(self, mock_update, save_app):
        senior = _make_user("senior")
        mock_update.return_value = ({"success": True}, None, None)
        with save_app.test_client() as client:
            with patch("flask_login.utils._get_user", return_value=senior):
                resp = client.post(
                    "/api/update_result_status/1/approved",
                    json={"action_type": "approve"},
                    headers={"X-Requested-With": "XMLHttpRequest"},
                )
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["success"] is True

    @patch("app.routes.api.analysis_save.update_result_status_api")
    def test_update_error(self, mock_update, save_app):
        senior = _make_user("senior")
        mock_update.return_value = (None, "Not found", 404)
        with save_app.test_client() as client:
            with patch("flask_login.utils._get_user", return_value=senior):
                resp = client.post("/api/update_result_status/999/approved", json={})
        assert resp.status_code == 404

    def test_update_forbidden_chemist(self, save_app, chemist_user):
        with save_app.test_client() as client:
            with patch("flask_login.utils._get_user", return_value=chemist_user):
                resp = client.post("/api/update_result_status/1/approved", json={})
        assert resp.status_code == 403

    def test_update_forbidden_viewer(self, save_app):
        viewer = _make_user("viewer")
        with save_app.test_client() as client:
            with patch("flask_login.utils._get_user", return_value=viewer):
                resp = client.post("/api/update_result_status/1/approved", json={})
        assert resp.status_code == 403

    @patch("app.routes.api.analysis_save.update_result_status_api")
    def test_update_admin_access(self, mock_update, save_app):
        admin = _make_user("admin")
        mock_update.return_value = ({"ok": True}, None, None)
        with save_app.test_client() as client:
            with patch("flask_login.utils._get_user", return_value=admin):
                resp = client.post(
                    "/api/update_result_status/1/approved",
                    json={"action_type": "approve"},
                )
        assert resp.status_code == 200

    @patch("app.routes.api.analysis_save.update_result_status_api")
    def test_update_json_body_full_params(self, mock_update, save_app):
        """JSON body with all rejection fields."""
        senior = _make_user("senior")
        mock_update.return_value = ({"result": "updated"}, None, None)
        with save_app.test_client() as client:
            with patch("flask_login.utils._get_user", return_value=senior):
                resp = client.post(
                    "/api/update_result_status/5/rejected",
                    json={
                        "rejection_category": "RANGE",
                        "rejection_subcategory": "HIGH",
                        "rejection_comment": "too high",
                        "error_reason": "range violation",
                    },
                )
        assert resp.status_code == 200
        mock_update.assert_called_once_with(
            result_id=5,
            new_status="rejected",
            action_type=None,
            rejection_category="RANGE",
            rejection_subcategory="HIGH",
            rejection_comment="too high",
            error_reason="range violation",
        )

    @patch("app.routes.api.analysis_save.update_result_status_api")
    def test_update_redirect_to_main_index(self, mock_update, save_app):
        """Non-AJAX, non-JSON, 'analysis' not in blueprints -> redirect main.index."""
        senior = _make_user("senior")
        mock_update.return_value = ({"ok": True}, None, None)

        main_bp = Blueprint("main", __name__)

        @main_bp.route("/")
        def index():
            return "OK"

        try:
            save_app.register_blueprint(main_bp)
        except Exception:
            pass

        with save_app.test_client() as client:
            with patch("flask_login.utils._get_user", return_value=senior):
                resp = client.post(
                    "/api/update_result_status/1/approved",
                    data={"action_type": "approve"},
                )
        assert resp.status_code == 302

    @patch("app.routes.api.analysis_save.update_result_status_api")
    def test_update_redirect_to_ahlah_dashboard(self, mock_update, save_app):
        """Non-AJAX, 'analysis' in blueprints -> redirect analysis.ahlah_dashboard."""
        senior = _make_user("senior")
        mock_update.return_value = ({"ok": True}, None, None)

        analysis_bp = Blueprint("analysis", __name__, url_prefix="/analysis")

        @analysis_bp.route("/ahlah_dashboard")
        def ahlah_dashboard():
            return "OK"

        try:
            save_app.register_blueprint(analysis_bp)
        except Exception:
            pass

        with save_app.test_client() as client:
            with patch("flask_login.utils._get_user", return_value=senior):
                resp = client.post(
                    "/api/update_result_status/1/approved",
                    data={"action_type": "approve"},
                )
        assert resp.status_code == 302
        assert "ahlah_dashboard" in resp.location or "analysis" in resp.location

    @patch("app.routes.api.analysis_save.update_result_status_api")
    def test_update_with_form_data_xhr(self, mock_update, save_app):
        """Form data with XMLHttpRequest header returns JSON."""
        senior = _make_user("senior")
        mock_update.return_value = ({"ok": True}, None, None)

        with save_app.test_client() as client:
            with patch("flask_login.utils._get_user", return_value=senior):
                resp = client.post(
                    "/api/update_result_status/7/rejected",
                    data={"rejection_comment": "Bad", "rejection_category": "CALC"},
                    headers={"X-Requested-With": "XMLHttpRequest"},
                )
        assert resp.status_code == 200
        mock_update.assert_called_once()


# =========================================================================
# TESTS FOR: app/routes/reports/dashboard.py
# =========================================================================


class TestReportsDashboard:
    """Tests for GET /reports/dashboard"""

    def _setup_mocks(self, mock_sample, mock_db, mock_now, dt, top_users_raw=None, scalar_val=0, sample_count=0):
        """Common setup for dashboard mocks (SQLAlchemy 2.0 native API)."""
        mock_now.return_value = dt

        # Create column mocks that support comparison operators
        col_mock = MagicMock()
        col_mock.__ge__ = MagicMock(return_value=True)
        col_mock.__lt__ = MagicMock(return_value=True)
        col_mock.__eq__ = MagicMock(return_value=True)

        mock_sample.lab_type = col_mock
        mock_sample.received_date = col_mock
        mock_sample.id = MagicMock()

        # db.session.execute(...).scalar_one() — Sample count queries
        # db.session.execute(...).scalar() — scalar query (sub query helpers)
        # db.session.execute(...).all() — group_by + limit + all (top_users_raw)
        exec_result = MagicMock()
        exec_result.scalar_one.return_value = sample_count
        exec_result.scalar.return_value = scalar_val
        exec_result.all.return_value = top_users_raw or []
        mock_db.session.execute.return_value = exec_result

        # Legacy chains (analyses_month/year + top_users use db.session.query)
        mock_chain = MagicMock()
        mock_chain.scalar.return_value = scalar_val
        mock_chain.group_by.return_value.order_by.return_value.limit.return_value.all.return_value = (
            top_users_raw or []
        )
        mock_db.session.query.return_value.join.return_value.filter.return_value = mock_chain

    def test_dashboard_success(self, dashboard_app, senior_user):
        with patch("app.routes.reports.dashboard.render_template", return_value="dashboard_html") as mock_render, \
             patch("app.routes.reports.dashboard.now_local") as mock_now, \
             patch("app.routes.reports.dashboard.db") as mock_db, \
             patch("app.routes.reports.dashboard.Sample") as mock_sample:

            self._setup_mocks(mock_sample, mock_db, mock_now, datetime(2026, 3, 11, 10, 0, 0),
                              top_users_raw=[(1, 20), (2, 15)], scalar_val=100, sample_count=42)

            mock_user = MagicMock()
            mock_user.full_name = "Gantulga Ulziibuyan"
            mock_user.username = "gantulga"
            mock_db.session.get.return_value = mock_user

            with dashboard_app.test_client() as client:
                with patch("flask_login.utils._get_user", return_value=senior_user):
                    resp = client.get("/reports/dashboard")

            assert resp.status_code == 200
            mock_render.assert_called_once()
            call_kw = mock_render.call_args[1]
            assert call_kw["samples_month"] == 42
            assert call_kw["analyses_month"] == 100
            assert len(call_kw["top_users"]) == 2

    def test_dashboard_december(self, dashboard_app, senior_user):
        """Test the month==12 branch for month_end calculation."""
        with patch("app.routes.reports.dashboard.render_template", return_value="ok") as mock_render, \
             patch("app.routes.reports.dashboard.now_local") as mock_now, \
             patch("app.routes.reports.dashboard.db") as mock_db, \
             patch("app.routes.reports.dashboard.Sample") as mock_sample:

            self._setup_mocks(mock_sample, mock_db, mock_now, datetime(2026, 12, 15, 10, 0, 0))
            mock_db.session.get.return_value = None

            with dashboard_app.test_client() as client:
                with patch("flask_login.utils._get_user", return_value=senior_user):
                    resp = client.get("/reports/dashboard")

            assert resp.status_code == 200
            call_kw = mock_render.call_args[1]
            assert call_kw["month"] == 12

    def test_dashboard_user_not_found(self, dashboard_app, senior_user):
        """When db.session.get(User, uid) returns None, user is skipped."""
        with patch("app.routes.reports.dashboard.render_template", return_value="ok") as mock_render, \
             patch("app.routes.reports.dashboard.now_local") as mock_now, \
             patch("app.routes.reports.dashboard.db") as mock_db, \
             patch("app.routes.reports.dashboard.Sample") as mock_sample:

            self._setup_mocks(mock_sample, mock_db, mock_now, datetime(2026, 6, 15, 10, 0, 0),
                              top_users_raw=[(99, 5)])
            mock_db.session.get.return_value = None

            with dashboard_app.test_client() as client:
                with patch("flask_login.utils._get_user", return_value=senior_user):
                    resp = client.get("/reports/dashboard")

            assert resp.status_code == 200
            call_kw = mock_render.call_args[1]
            assert call_kw["top_users"] == []

    def test_dashboard_january(self, dashboard_app, senior_user):
        """Test January: monthly_stats loop with negative month wrapping to previous year."""
        with patch("app.routes.reports.dashboard.render_template", return_value="ok") as mock_render, \
             patch("app.routes.reports.dashboard.now_local") as mock_now, \
             patch("app.routes.reports.dashboard.db") as mock_db, \
             patch("app.routes.reports.dashboard.Sample") as mock_sample:

            self._setup_mocks(mock_sample, mock_db, mock_now, datetime(2026, 1, 10, 10, 0, 0))

            with dashboard_app.test_client() as client:
                with patch("flask_login.utils._get_user", return_value=senior_user):
                    resp = client.get("/reports/dashboard")

            assert resp.status_code == 200
            call_kw = mock_render.call_args[1]
            monthly = call_kw["monthly_stats"]
            assert len(monthly) == 6
            assert any(m["year"] == 2025 for m in monthly)

    def test_dashboard_with_full_name_format(self, dashboard_app, senior_user):
        """Test that _format_short_name is used for top_users."""
        with patch("app.routes.reports.dashboard.render_template", return_value="ok") as mock_render, \
             patch("app.routes.reports.dashboard.now_local") as mock_now, \
             patch("app.routes.reports.dashboard.db") as mock_db, \
             patch("app.routes.reports.dashboard.Sample") as mock_sample:

            self._setup_mocks(mock_sample, mock_db, mock_now, datetime(2026, 3, 11, 10, 0, 0),
                              top_users_raw=[(1, 20)])

            mock_user = MagicMock()
            mock_user.full_name = "GANTULGA Ulziibuyan"
            mock_user.username = "gantulga"
            mock_db.session.get.return_value = mock_user

            with dashboard_app.test_client() as client:
                with patch("flask_login.utils._get_user", return_value=senior_user):
                    resp = client.get("/reports/dashboard")

            assert resp.status_code == 200
            call_kw = mock_render.call_args[1]
            top_users = call_kw["top_users"]
            assert len(top_users) == 1
            assert top_users[0]["name"] == "Gantulga.U"
            assert top_users[0]["count"] == 20

    def test_dashboard_scalar_returns_none(self, dashboard_app, senior_user):
        """When scalar() returns None, should default to 0 via 'or 0'."""
        with patch("app.routes.reports.dashboard.render_template", return_value="ok") as mock_render, \
             patch("app.routes.reports.dashboard.now_local") as mock_now, \
             patch("app.routes.reports.dashboard.db") as mock_db, \
             patch("app.routes.reports.dashboard.Sample") as mock_sample:

            self._setup_mocks(mock_sample, mock_db, mock_now, datetime(2026, 3, 11, 10, 0, 0),
                              scalar_val=None)

            with dashboard_app.test_client() as client:
                with patch("flask_login.utils._get_user", return_value=senior_user):
                    resp = client.get("/reports/dashboard")

            assert resp.status_code == 200
            call_kw = mock_render.call_args[1]
            assert call_kw["analyses_month"] == 0
            assert call_kw["analyses_year"] == 0
            assert call_kw["errors_month"] == 0
            assert call_kw["errors_year"] == 0
            assert call_kw["active_users_month"] == 0

    def test_dashboard_user_with_empty_full_name(self, dashboard_app, senior_user):
        """User with empty full_name falls back to username."""
        with patch("app.routes.reports.dashboard.render_template", return_value="ok") as mock_render, \
             patch("app.routes.reports.dashboard.now_local") as mock_now, \
             patch("app.routes.reports.dashboard.db") as mock_db, \
             patch("app.routes.reports.dashboard.Sample") as mock_sample:

            self._setup_mocks(mock_sample, mock_db, mock_now, datetime(2026, 5, 15, 10, 0, 0),
                              top_users_raw=[(1, 10)])

            mock_user = MagicMock()
            mock_user.full_name = ""
            mock_user.username = "noname_user"
            mock_db.session.get.return_value = mock_user

            with dashboard_app.test_client() as client:
                with patch("flask_login.utils._get_user", return_value=senior_user):
                    resp = client.get("/reports/dashboard")

            assert resp.status_code == 200
            call_kw = mock_render.call_args[1]
            top_users = call_kw["top_users"]
            assert len(top_users) == 1
            assert top_users[0]["name"] == "noname_user"


# =========================================================================
# TESTS FOR: _format_short_name (used by dashboard)
# =========================================================================


class TestFormatShortName:
    """Tests for the _format_short_name helper."""

    def test_normal_name(self):
        from app.routes.reports.routes import _format_short_name
        assert _format_short_name("GANTULGA Ulziibuyan") == "Gantulga.U"

    def test_single_name(self):
        from app.routes.reports.routes import _format_short_name
        assert _format_short_name("Admin") == "Admin"

    def test_empty_string(self):
        from app.routes.reports.routes import _format_short_name
        assert _format_short_name("") == ""

    def test_none(self):
        from app.routes.reports.routes import _format_short_name
        assert _format_short_name(None) == ""

    def test_three_part_name(self):
        from app.routes.reports.routes import _format_short_name
        result = _format_short_name("First Middle Last")
        assert result == "First.M"
