# tests/test_routes_reports_full_batch.py
# -*- coding: utf-8 -*-
"""
Comprehensive tests for:
  - app/routes/reports/consumption.py
  - app/routes/reports/crud.py
  - app/routes/reports/monthly_plan.py
  - app/routes/reports/pdf_generator.py

Target: 80%+ coverage for each module.
"""

import os
import io
import types
import pytest
from datetime import datetime, date, timedelta
from unittest.mock import patch, MagicMock, PropertyMock, mock_open

from flask import Flask


# ---------------------------------------------------------------------------
# Helpers – build a minimal Flask app with the two blueprints
# ---------------------------------------------------------------------------

def _make_app():
    """Create a minimal Flask app with reports_bp and pdf_reports_bp."""
    app = Flask(__name__, template_folder=os.path.join(
        os.path.dirname(__file__), '..', 'app', 'templates'
    ))
    app.config.update(
        TESTING=True,
        SECRET_KEY="test-secret",
        WTF_CSRF_ENABLED=False,
        SERVER_NAME="localhost",
        LOGIN_DISABLED=True,
    )

    # Dummy login manager
    from flask_login import LoginManager, UserMixin
    lm = LoginManager(app)

    class FakeUser(UserMixin):
        id = 1
        role = "admin"
        username = "testadmin"
        full_name = "Test Admin"

    @lm.user_loader
    def _load(uid):
        return FakeUser()

    @lm.request_loader
    def _load_req(req):
        return FakeUser()

    return app, FakeUser


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def app_and_client():
    """Yield (app, client, FakeUser) with blueprints registered."""
    app, FakeUser = _make_app()

    # We need to import blueprints *after* mocking heavy deps
    with app.app_context():
        from app.routes.reports.routes import reports_bp
        from app.routes.reports import pdf_reports_bp

        # Remove any previous registrations (idempotent)
        try:
            app.register_blueprint(reports_bp)
        except Exception:
            pass
        try:
            app.register_blueprint(pdf_reports_bp)
        except Exception:
            pass

        # Register a fake analysis.sample_report endpoint via a blueprint
        from flask import Blueprint
        analysis_bp = Blueprint("analysis", __name__, url_prefix="/analysis")

        @analysis_bp.route("/sample_report/<int:sample_id>")
        def sample_report(sample_id):
            return "ok"

        try:
            app.register_blueprint(analysis_bp)
        except Exception:
            pass

    client = app.test_client()
    yield app, client, FakeUser


# =========================================================================
# A) consumption.py — _parse_date_safe (unit, no Flask needed)
# =========================================================================

class TestParseDateSafe:
    def test_valid_date(self):
        from app.routes.reports.consumption import _parse_date_safe
        assert _parse_date_safe("2026-03-10") == date(2026, 3, 10)

    def test_none_returns_none(self):
        from app.routes.reports.consumption import _parse_date_safe
        assert _parse_date_safe(None) is None

    def test_empty_string_returns_none(self):
        from app.routes.reports.consumption import _parse_date_safe
        assert _parse_date_safe("") is None

    def test_bad_format_returns_none(self):
        from app.routes.reports.consumption import _parse_date_safe
        assert _parse_date_safe("10/03/2026") is None

    def test_partial_date_returns_none(self):
        from app.routes.reports.consumption import _parse_date_safe
        assert _parse_date_safe("2026-13-40") is None


# =========================================================================
# B) consumption.py — _calculate_consumption
# =========================================================================

class TestCalculateConsumption:
    @patch("app.routes.reports.consumption.get_shift_info")
    @patch("app.routes.reports.consumption.norm_code")
    @patch("app.routes.reports.consumption.db")
    def test_basic_calculation(self, mock_db, mock_norm, mock_shift):
        from app.routes.reports.consumption import _calculate_consumption

        mock_norm.side_effect = lambda x: x.upper()

        # Build fake result / sample pairs
        mock_result = MagicMock()
        mock_result.created_at = datetime(2026, 3, 15, 10, 0)
        mock_result.analysis_code = "MAD"
        mock_result.status = "approved"

        mock_sample = MagicMock()
        mock_sample.client_name = "CHPP"
        mock_sample.id = 1
        mock_sample.lab_type = "coal"

        shift = MagicMock()
        shift.shift_type = "day"
        shift.anchor_date = date(2026, 3, 15)
        mock_shift.return_value = shift

        q = MagicMock()
        q.join.return_value = q
        q.filter.return_value = q
        q.all.return_value = [(mock_result, mock_sample)]
        mock_db.session.query.return_value = q

        blocks, grand, kpi = _calculate_consumption(2026)
        assert kpi["total_results"] == 1
        assert kpi["distinct_samples"] == 1
        assert len(blocks) == 1
        assert blocks[0]["client_name"] == "CHPP"

    @patch("app.routes.reports.consumption.get_shift_info")
    @patch("app.routes.reports.consumption.norm_code")
    @patch("app.routes.reports.consumption.db")
    def test_with_date_range_and_filters(self, mock_db, mock_norm, mock_shift):
        from app.routes.reports.consumption import _calculate_consumption

        mock_norm.side_effect = lambda x: x
        q = MagicMock()
        q.join.return_value = q
        q.filter.return_value = q
        q.all.return_value = []
        mock_db.session.query.return_value = q

        blocks, grand, kpi = _calculate_consumption(
            2026,
            client_filter="CHPP",
            analysis_filter="MAD",
            shift_filter="day",
            date_from=date(2026, 1, 1),
            date_to=date(2026, 6, 30),
        )
        assert kpi["total_results"] == 0
        assert kpi["distinct_samples"] == 0

    @patch("app.routes.reports.consumption.get_shift_info")
    @patch("app.routes.reports.consumption.norm_code")
    @patch("app.routes.reports.consumption.db")
    def test_shift_filter_skips_non_matching(self, mock_db, mock_norm, mock_shift):
        from app.routes.reports.consumption import _calculate_consumption

        mock_norm.side_effect = lambda x: x

        mock_result = MagicMock()
        mock_result.created_at = datetime(2026, 3, 15, 10, 0)
        mock_result.analysis_code = "MAD"

        mock_sample = MagicMock()
        mock_sample.client_name = "CHPP"
        mock_sample.id = 1

        shift = MagicMock()
        shift.shift_type = "night"
        shift.anchor_date = date(2026, 3, 15)
        mock_shift.return_value = shift

        q = MagicMock()
        q.join.return_value = q
        q.filter.return_value = q
        q.all.return_value = [(mock_result, mock_sample)]
        mock_db.session.query.return_value = q

        blocks, grand, kpi = _calculate_consumption(2026, shift_filter="day")
        assert kpi["total_results"] == 0

    @patch("app.routes.reports.consumption.get_shift_info")
    @patch("app.routes.reports.consumption.norm_code")
    @patch("app.routes.reports.consumption.db")
    def test_result_without_created_at(self, mock_db, mock_norm, mock_shift):
        from app.routes.reports.consumption import _calculate_consumption

        mock_result = MagicMock()
        mock_result.created_at = None

        mock_sample = MagicMock()
        mock_sample.client_name = "X"
        mock_sample.id = 2

        q = MagicMock()
        q.join.return_value = q
        q.filter.return_value = q
        q.all.return_value = [(mock_result, mock_sample)]
        mock_db.session.query.return_value = q

        blocks, grand, kpi = _calculate_consumption(2026)
        assert kpi["total_results"] == 0


# =========================================================================
# C) consumption.py — _count_error_reasons
# =========================================================================

class TestCountErrorReasons:
    @patch("app.routes.reports.consumption.db")
    def test_with_results(self, mock_db):
        from app.routes.reports.consumption import _count_error_reasons

        q = MagicMock()
        q.filter.return_value = q
        q.group_by.return_value = q
        q.all.return_value = [
            ("measurement_error", 5),
            ("documentation_error", 3),
        ]
        mock_db.session.query.return_value = q

        items, total = _count_error_reasons(2026)
        assert total == 8
        # All labels should be present (6 labels)
        assert len(items) == 6

    @patch("app.routes.reports.consumption.db")
    def test_empty_results(self, mock_db):
        from app.routes.reports.consumption import _count_error_reasons

        q = MagicMock()
        q.filter.return_value = q
        q.group_by.return_value = q
        q.all.return_value = []
        mock_db.session.query.return_value = q

        items, total = _count_error_reasons(2026)
        assert total == 0
        assert len(items) == 6  # all labels still present with count=0

    @patch("app.routes.reports.consumption.db")
    def test_unknown_code(self, mock_db):
        from app.routes.reports.consumption import _count_error_reasons

        q = MagicMock()
        q.filter.return_value = q
        q.group_by.return_value = q
        q.all.return_value = [("custom_reason", 2)]
        mock_db.session.query.return_value = q

        items, total = _count_error_reasons(2026)
        assert total == 2
        codes = [it["code"] for it in items]
        assert "custom_reason" in codes


# =========================================================================
# D) consumption.py — route /reports/consumption
# =========================================================================

class TestConsumptionRoute:
    @patch("app.routes.reports.consumption.render_template", return_value="<html>ok</html>")
    @patch("app.routes.reports.consumption._code_expr_and_join")
    @patch("app.routes.reports.consumption._pick_date_col")
    @patch("app.routes.reports.consumption._year_arg", return_value=2026)
    @patch("app.routes.reports.consumption.db")
    @patch("app.routes.reports.consumption.M")
    def test_consumption_ok(self, mock_M, mock_db, mock_year, mock_pick, mock_code, mock_render, app_and_client):
        app, client, _ = app_and_client

        mock_M.AnalysisType = MagicMock()
        at_q = MagicMock()
        at_q.order_by.return_value.all.return_value = []
        mock_db.session.query.return_value = at_q

        mock_pick.return_value = MagicMock()

        base_q = MagicMock()
        base_q.join.return_value = base_q
        base_q.filter.return_value = base_q
        mock_code.return_value = (base_q, MagicMock())
        base_q.with_entities.return_value.all.return_value = []

        resp = client.get("/reports/consumption")
        assert resp.status_code == 200

    @patch("app.routes.reports.consumption.render_template", return_value="<html>ok</html>")
    @patch("app.routes.reports.consumption._code_expr_and_join")
    @patch("app.routes.reports.consumption._pick_date_col")
    @patch("app.routes.reports.consumption._year_arg", return_value=2026)
    @patch("app.routes.reports.consumption.db")
    @patch("app.routes.reports.consumption.M")
    def test_consumption_with_rows(self, mock_M, mock_db, mock_year, mock_pick, mock_code, mock_render, app_and_client):
        app, client, _ = app_and_client

        # AnalysisType exists with code attr
        mock_at = MagicMock()
        mock_at.code = MagicMock()
        mock_at.code.asc.return_value = "asc"
        mock_M.AnalysisType = mock_at

        at_q = MagicMock()
        at_q.order_by.return_value.all.return_value = []
        mock_db.session.query.return_value = at_q

        mock_pick.return_value = MagicMock()

        row = MagicMock()
        row.mon = 3
        row.unit = "CHPP"
        row.stype = "2 hourly"
        row.code = "MAD"
        row.sid = 1

        base_q = MagicMock()
        base_q.join.return_value = base_q
        base_q.filter.return_value = base_q
        mock_code.return_value = (base_q, MagicMock())
        base_q.with_entities.return_value.all.return_value = [row]

        resp = client.get("/reports/consumption")
        assert resp.status_code == 200


# =========================================================================
# E) consumption.py — route /reports/consumption_cell
# =========================================================================

class TestConsumptionCellRoute:
    @patch("app.routes.reports.consumption._pick_date_col")
    @patch("app.routes.reports.consumption.db")
    def test_missing_params_400(self, mock_db, mock_pick, app_and_client):
        app, client, _ = app_and_client
        resp = client.get("/reports/consumption_cell")
        assert resp.status_code == 400

    @patch("app.routes.reports.consumption._pick_date_col")
    @patch("app.routes.reports.consumption.db")
    def test_invalid_month_400(self, mock_db, mock_pick, app_and_client):
        app, client, _ = app_and_client
        resp = client.get("/reports/consumption_cell?year=2026&month=13&unit=X&stype=Y")
        assert resp.status_code == 400

    @patch("app.routes.reports.consumption.M")
    @patch("app.routes.reports.consumption._pick_date_col")
    @patch("app.routes.reports.consumption.db")
    def test_samples_kind(self, mock_db, mock_pick, mock_M, app_and_client):
        app, client, _ = app_and_client

        mock_pick.return_value = MagicMock()

        row = MagicMock()
        row.sample_id = 1
        row.sample_code = "S001"
        row.name = "Test Sample"
        row.client_name = "CHPP"
        row.sample_type = "2 hourly"
        row.dt = datetime(2026, 3, 15)

        q = MagicMock()
        q.join.return_value = q
        q.filter.return_value = q
        q.order_by.return_value.all.return_value = [row]
        mock_db.session.query.return_value = q

        resp = client.get("/reports/consumption_cell?year=2026&month=3&unit=CHPP&stype=2 hourly&kind=samples")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["success"] is True

    @patch("app.routes.reports.consumption.M")
    @patch("app.routes.reports.consumption._pick_date_col")
    @patch("app.routes.reports.consumption.db")
    def test_code_kind_with_analysis_type_id(self, mock_db, mock_pick, mock_M, app_and_client):
        app, client, _ = app_and_client

        mock_pick.return_value = MagicMock()

        # Make AnalysisResult have analysis_type_id
        mock_ar = MagicMock()
        mock_ar.analysis_type_id = 1
        from app.routes.reports.consumption import AnalysisResult as AR

        row = MagicMock()
        row.sample_id = 1
        row.sample_code = "S001"
        row.name = "Test"
        row.dt = datetime(2026, 3, 15)
        row.code = "MAD"

        q = MagicMock()
        q.join.return_value = q
        q.filter.return_value = q
        q.add_columns.return_value = q
        q.order_by.return_value.all.return_value = [row]
        mock_db.session.query.return_value = q

        resp = client.get("/reports/consumption_cell?year=2026&month=3&unit=CHPP&stype=2 hourly&kind=code&code=MAD")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["success"] is True


# =========================================================================
# F) crud.py — report_list
# =========================================================================

class TestCrudReportList:
    @patch("app.routes.reports.crud.render_template", return_value="<html></html>")
    @patch("app.routes.reports.crud.LabReport")
    def test_report_list_default(self, mock_lr, mock_render, app_and_client):
        app, client, _ = app_and_client
        q = MagicMock()
        q.order_by.return_value.limit.return_value.all.return_value = []
        mock_lr.query = q
        resp = client.get("/pdf-reports/")
        assert resp.status_code == 200

    @patch("app.routes.reports.crud.render_template", return_value="<html></html>")
    @patch("app.routes.reports.crud.LabReport")
    def test_report_list_with_filters(self, mock_lr, mock_render, app_and_client):
        app, client, _ = app_and_client
        q = MagicMock()
        q.filter.return_value = q
        q.order_by.return_value.limit.return_value.all.return_value = []
        mock_lr.query = q
        resp = client.get("/pdf-reports/list?lab=coal&status=draft")
        assert resp.status_code == 200

    @patch("app.routes.reports.crud.render_template", return_value="<html></html>")
    @patch("app.routes.reports.crud.LabReport")
    def test_report_list_all_filters(self, mock_lr, mock_render, app_and_client):
        app, client, _ = app_and_client
        q = MagicMock()
        q.order_by.return_value.limit.return_value.all.return_value = []
        mock_lr.query = q
        resp = client.get("/pdf-reports/?lab=all&status=all")
        assert resp.status_code == 200


# =========================================================================
# G) crud.py — signature_list
# =========================================================================

class TestCrudSignatureList:
    @patch("app.routes.reports.crud.render_template", return_value="<html></html>")
    @patch("app.routes.reports.crud.ReportSignature")
    @patch("app.routes.reports.crud.current_user")
    def test_signature_list_ok(self, mock_cu, mock_rs, mock_render, app_and_client):
        app, client, _ = app_and_client
        mock_cu.role = "admin"

        sig1 = MagicMock()
        sig1.signature_type = "stamp"
        sig2 = MagicMock()
        sig2.signature_type = "signature"
        mock_rs.query.filter_by.return_value.all.return_value = [sig1, sig2]

        resp = client.get("/pdf-reports/signatures")
        assert resp.status_code == 200

    @patch("app.routes.reports.crud.current_user")
    def test_signature_list_forbidden(self, mock_cu, app_and_client):
        app, client, _ = app_and_client
        mock_cu.role = "analyst"
        resp = client.get("/pdf-reports/signatures", follow_redirects=False)
        assert resp.status_code == 302


# =========================================================================
# H) crud.py — add_signature
# =========================================================================

class TestCrudAddSignature:
    @patch("app.routes.reports.crud.render_template", return_value="<html></html>")
    @patch("app.routes.reports.crud.User")
    @patch("app.routes.reports.crud.current_user")
    def test_add_signature_get(self, mock_cu, mock_user, mock_render, app_and_client):
        app, client, _ = app_and_client
        mock_cu.role = "admin"
        mock_user.query.filter.return_value.all.return_value = []
        resp = client.get("/pdf-reports/signatures/add")
        assert resp.status_code == 200

    @patch("app.routes.reports.crud.current_user")
    def test_add_signature_forbidden(self, mock_cu, app_and_client):
        app, client, _ = app_and_client
        mock_cu.role = "analyst"
        resp = client.post("/pdf-reports/signatures/add", follow_redirects=False)
        assert resp.status_code == 302

    @patch("app.routes.reports.crud.render_template", return_value="<html></html>")
    @patch("app.routes.reports.crud.User")
    @patch("app.routes.reports.crud.ReportSignature")
    @patch("app.routes.reports.crud.safe_commit", return_value=True)
    @patch("app.routes.reports.crud.os.makedirs")
    @patch("app.routes.reports.crud.db")
    @patch("app.routes.reports.crud.current_user")
    def test_add_signature_post_oserror_fallthrough(self, mock_cu, mock_db, mock_mkdirs, mock_commit, mock_rs, mock_user, mock_render, app_and_client):
        """When file.save raises OSError, the except block catches and renders the form (200)."""
        app, client, _ = app_and_client
        mock_cu.role = "admin"
        mock_user.query.filter.return_value.all.return_value = []

        # PNG magic bytes
        png_data = b'\x89PNG\r\n\x1a\n' + b'\x00' * 100
        data = {
            'signature_type': 'signature',
            'name': 'Test Sig',
            'position': 'Manager',
            'lab_type': 'coal',
            'image': (io.BytesIO(png_data), 'test.png'),
        }
        resp = client.post("/pdf-reports/signatures/add", data=data, content_type='multipart/form-data', follow_redirects=False)
        # OSError from file.save is caught, falls through to render form
        assert resp.status_code == 200

    @patch("app.routes.reports.crud.db")
    @patch("app.routes.reports.crud.current_user")
    def test_add_signature_bad_extension(self, mock_cu, mock_db, app_and_client):
        app, client, _ = app_and_client
        mock_cu.role = "admin"

        data = {
            'signature_type': 'signature',
            'name': 'Test',
            'position': 'Manager',
            'image': (io.BytesIO(b'fake'), 'test.exe'),
        }
        resp = client.post("/pdf-reports/signatures/add", data=data, content_type='multipart/form-data', follow_redirects=False)
        assert resp.status_code == 302

    @patch("app.routes.reports.crud.db")
    @patch("app.routes.reports.crud.current_user")
    def test_add_signature_too_large(self, mock_cu, mock_db, app_and_client):
        app, client, _ = app_and_client
        mock_cu.role = "admin"

        big_data = b'\x89PNG\r\n\x1a\n' + b'\x00' * (6 * 1024 * 1024)
        data = {
            'signature_type': 'signature',
            'name': 'Test',
            'position': 'Manager',
            'image': (io.BytesIO(big_data), 'test.png'),
        }
        resp = client.post("/pdf-reports/signatures/add", data=data, content_type='multipart/form-data', follow_redirects=False)
        assert resp.status_code == 302

    @patch("app.routes.reports.crud.db")
    @patch("app.routes.reports.crud.current_user")
    def test_add_signature_bad_magic_bytes(self, mock_cu, mock_db, app_and_client):
        app, client, _ = app_and_client
        mock_cu.role = "admin"

        data = {
            'signature_type': 'signature',
            'name': 'Test',
            'position': 'Manager',
            'image': (io.BytesIO(b'\x00\x00\x00\x00\x00\x00\x00\x00'), 'test.png'),
        }
        resp = client.post("/pdf-reports/signatures/add", data=data, content_type='multipart/form-data', follow_redirects=False)
        assert resp.status_code == 302

    @patch("app.routes.reports.crud.render_template", return_value="<html></html>")
    @patch("app.routes.reports.crud.User")
    @patch("app.routes.reports.crud.safe_commit", return_value=True)
    @patch("app.routes.reports.crud.db")
    @patch("app.routes.reports.crud.current_user")
    def test_add_signature_post_no_image(self, mock_cu, mock_db, mock_commit, mock_user, mock_render, app_and_client):
        app, client, _ = app_and_client
        mock_cu.role = "admin"

        data = {
            'signature_type': 'stamp',
            'name': 'Lab Stamp',
            'position': 'Lab',
            'lab_type': 'all',
        }
        resp = client.post("/pdf-reports/signatures/add", data=data, content_type='multipart/form-data', follow_redirects=False)
        assert resp.status_code == 302


# =========================================================================
# I) crud.py — delete_signature
# =========================================================================

class TestCrudDeleteSignature:
    @patch("app.routes.reports.crud.safe_commit", return_value=True)
    @patch("app.routes.reports.crud.ReportSignatureRepository")
    @patch("app.routes.reports.crud.current_user")
    def test_delete_ok(self, mock_cu, mock_repo, mock_commit, app_and_client):
        app, client, _ = app_and_client
        mock_cu.role = "admin"

        sig = MagicMock()
        mock_repo.get_by_id.return_value = sig

        resp = client.post("/pdf-reports/signatures/delete/1", follow_redirects=False)
        assert resp.status_code == 302
        assert sig.is_active is False

    @patch("app.routes.reports.crud.current_user")
    def test_delete_forbidden(self, mock_cu, app_and_client):
        app, client, _ = app_and_client
        mock_cu.role = "analyst"
        resp = client.post("/pdf-reports/signatures/delete/1", follow_redirects=False)
        assert resp.status_code == 302

    @patch("app.routes.reports.crud.ReportSignatureRepository")
    @patch("app.routes.reports.crud.current_user")
    def test_delete_not_found(self, mock_cu, mock_repo, app_and_client):
        app, client, _ = app_and_client
        mock_cu.role = "admin"
        mock_repo.get_by_id.return_value = None
        resp = client.post("/pdf-reports/signatures/delete/999")
        assert resp.status_code == 404


# =========================================================================
# J) crud.py — report_detail
# =========================================================================

class TestCrudReportDetail:
    @patch("app.routes.reports.crud.render_template", return_value="<html></html>")
    @patch("app.routes.reports.crud.ReportSignature")
    @patch("app.routes.reports.crud.LabReportRepository")
    def test_detail_ok(self, mock_repo, mock_rs, mock_render, app_and_client):
        app, client, _ = app_and_client

        report = MagicMock()
        report.lab_type = "coal"
        mock_repo.get_by_id_or_404.return_value = report

        fq = MagicMock()
        fq.filter.return_value.all.return_value = []
        mock_rs.query.filter_by.return_value = fq

        resp = client.get("/pdf-reports/1")
        assert resp.status_code == 200

    @patch("app.routes.reports.crud.LabReportRepository")
    def test_detail_not_found(self, mock_repo, app_and_client):
        app, client, _ = app_and_client
        from werkzeug.exceptions import NotFound
        mock_repo.get_by_id_or_404.side_effect = NotFound()
        resp = client.get("/pdf-reports/999")
        assert resp.status_code == 404


# =========================================================================
# K) crud.py — approve_report
# =========================================================================

class TestCrudApproveReport:
    @patch("app.routes.reports.pdf_generator.regenerate_pdf")
    @patch("app.routes.reports.crud.safe_commit", return_value=True)
    @patch("app.routes.reports.crud.LabReportRepository")
    @patch("app.routes.reports.crud.current_user")
    def test_approve_ok(self, mock_cu, mock_repo, mock_commit, mock_regen, app_and_client):
        app, client, _ = app_and_client
        mock_cu.role = "admin"
        mock_cu.id = 1

        report = MagicMock()
        mock_repo.get_by_id_or_404.return_value = report

        resp = client.post("/pdf-reports/1/approve", data={
            'analyst_signature_id': '2',
            'manager_signature_id': '3',
            'stamp_id': '4',
        }, follow_redirects=False)
        assert resp.status_code == 302
        assert report.status == 'approved'
        mock_regen.assert_called_once_with(report)

    @patch("app.routes.reports.crud.current_user")
    def test_approve_forbidden(self, mock_cu, app_and_client):
        app, client, _ = app_and_client
        mock_cu.role = "analyst"
        resp = client.post("/pdf-reports/1/approve", follow_redirects=False)
        assert resp.status_code == 302

    @patch("app.routes.reports.crud.LabReportRepository")
    @patch("app.routes.reports.crud.current_user")
    def test_approve_not_found(self, mock_cu, mock_repo, app_and_client):
        app, client, _ = app_and_client
        mock_cu.role = "admin"
        from werkzeug.exceptions import NotFound
        mock_repo.get_by_id_or_404.side_effect = NotFound()
        resp = client.post("/pdf-reports/999/approve")
        assert resp.status_code == 404

    @patch("app.routes.reports.crud.safe_commit", return_value=False)
    @patch("app.routes.reports.crud.LabReportRepository")
    @patch("app.routes.reports.crud.current_user")
    def test_approve_commit_fails(self, mock_cu, mock_repo, mock_commit, app_and_client):
        app, client, _ = app_and_client
        mock_cu.role = "admin"
        mock_cu.id = 1

        report = MagicMock()
        mock_repo.get_by_id_or_404.return_value = report

        resp = client.post("/pdf-reports/1/approve", follow_redirects=False)
        assert resp.status_code == 302


# =========================================================================
# L) crud.py — download_report
# =========================================================================

class TestCrudDownloadReport:
    @patch("app.routes.reports.crud.LabReportRepository")
    def test_download_not_found(self, mock_repo, app_and_client):
        app, client, _ = app_and_client
        from werkzeug.exceptions import NotFound
        mock_repo.get_by_id_or_404.side_effect = NotFound()
        resp = client.get("/pdf-reports/999/download")
        assert resp.status_code == 404

    @patch("app.routes.reports.crud.LabReportRepository")
    def test_download_no_pdf_path(self, mock_repo, app_and_client):
        app, client, _ = app_and_client
        report = MagicMock()
        report.pdf_path = None
        report.id = 1
        mock_repo.get_by_id_or_404.return_value = report
        resp = client.get("/pdf-reports/1/download", follow_redirects=False)
        assert resp.status_code == 302

    @patch("app.routes.reports.crud.os.path.exists", return_value=False)
    @patch("app.routes.reports.crud.os.path.realpath")
    @patch("app.routes.reports.crud.LabReportRepository")
    def test_download_path_traversal(self, mock_repo, mock_realpath, mock_exists, app_and_client):
        app, client, _ = app_and_client
        report = MagicMock()
        report.pdf_path = "../../etc/passwd"
        report.id = 1
        mock_repo.get_by_id_or_404.return_value = report

        # Simulate path traversal - realpath returns outside safe_dir
        mock_realpath.side_effect = lambda p: "/etc/passwd" if "passwd" in str(p) else "/app/static"

        resp = client.get("/pdf-reports/1/download", follow_redirects=False)
        assert resp.status_code == 302

    @patch("app.routes.reports.crud.send_file", return_value=MagicMock(status_code=200))
    @patch("app.routes.reports.crud.os.path.exists", return_value=True)
    @patch("app.routes.reports.crud.os.path.realpath")
    @patch("app.routes.reports.crud.LabReportRepository")
    def test_download_ok(self, mock_repo, mock_realpath, mock_exists, mock_send, app_and_client):
        app, client, _ = app_and_client

        report = MagicMock()
        report.pdf_path = "uploads/reports/2026_1.pdf"
        report.report_number = "2026_1"
        report.id = 1
        mock_repo.get_by_id_or_404.return_value = report

        safe_dir = os.path.join(app.root_path, 'static')
        pdf_full = os.path.join(safe_dir, report.pdf_path)
        mock_realpath.side_effect = lambda p: pdf_full if "2026_1" in str(p) else safe_dir

        resp = client.get("/pdf-reports/1/download")
        mock_send.assert_called_once()


# =========================================================================
# M) crud.py — delete_report
# =========================================================================

class TestCrudDeleteReport:
    @patch("app.routes.reports.crud.current_user")
    def test_delete_report_forbidden(self, mock_cu, app_and_client):
        app, client, _ = app_and_client
        mock_cu.role = "analyst"
        resp = client.post("/pdf-reports/1/delete", follow_redirects=False)
        assert resp.status_code == 302

    @patch("app.routes.reports.crud.LabReportRepository")
    @patch("app.routes.reports.crud.current_user")
    def test_delete_report_not_found(self, mock_cu, mock_repo, app_and_client):
        app, client, _ = app_and_client
        mock_cu.role = "admin"
        from werkzeug.exceptions import NotFound
        mock_repo.get_by_id_or_404.side_effect = NotFound()
        resp = client.post("/pdf-reports/999/delete")
        assert resp.status_code == 404

    @patch("app.routes.reports.crud.safe_commit", return_value=True)
    @patch("app.routes.reports.crud.os.remove")
    @patch("app.routes.reports.crud.os.path.exists", return_value=True)
    @patch("app.routes.reports.crud.LabReportRepository")
    @patch("app.routes.reports.crud.current_user")
    def test_delete_report_with_pdf(self, mock_cu, mock_repo, mock_exists, mock_remove, mock_commit, app_and_client):
        app, client, _ = app_and_client
        mock_cu.role = "admin"

        report = MagicMock()
        report.pdf_path = "uploads/reports/test.pdf"
        mock_repo.get_by_id_or_404.return_value = report

        resp = client.post("/pdf-reports/1/delete", follow_redirects=False)
        assert resp.status_code == 302
        mock_remove.assert_called_once()

    @patch("app.routes.reports.crud.safe_commit", return_value=True)
    @patch("app.routes.reports.crud.LabReportRepository")
    @patch("app.routes.reports.crud.current_user")
    def test_delete_report_no_pdf(self, mock_cu, mock_repo, mock_commit, app_and_client):
        app, client, _ = app_and_client
        mock_cu.role = "admin"

        report = MagicMock()
        report.pdf_path = None
        mock_repo.get_by_id_or_404.return_value = report

        resp = client.post("/pdf-reports/1/delete", follow_redirects=False)
        assert resp.status_code == 302


# =========================================================================
# N) crud.py — get_next_report_number
# =========================================================================

class TestGetNextReportNumber:
    @patch("app.routes.reports.crud.LabReport")
    def test_first_report(self, mock_lr):
        from app.routes.reports.crud import get_next_report_number

        q = MagicMock()
        q.filter.return_value = q
        q.order_by.return_value.first.return_value = None
        q.count.return_value = 0
        mock_lr.query = q
        mock_lr.report_number = MagicMock()
        mock_lr.id = MagicMock()

        result = get_next_report_number("coal")
        year = datetime.now().year
        assert result == f"{year}_1"

    @patch("app.routes.reports.crud.LabReport")
    def test_increment_existing(self, mock_lr):
        from app.routes.reports.crud import get_next_report_number

        year = datetime.now().year
        last = MagicMock()
        last.report_number = f"{year}_5"

        q = MagicMock()
        q.filter.return_value = q
        q.order_by.return_value.first.return_value = last
        mock_lr.query = q
        mock_lr.report_number = MagicMock()
        mock_lr.id = MagicMock()

        result = get_next_report_number("coal")
        assert result == f"{year}_6"

    @patch("app.routes.reports.crud.LabReport")
    def test_bad_format_fallback(self, mock_lr):
        from app.routes.reports.crud import get_next_report_number

        year = datetime.now().year
        last = MagicMock()
        last.report_number = "bad_format"

        q = MagicMock()
        q.filter.return_value = q
        q.order_by.return_value.first.return_value = last
        q.count.return_value = 3
        mock_lr.query = q
        mock_lr.report_number = MagicMock()
        mock_lr.id = MagicMock()

        result = get_next_report_number("coal")
        assert result == f"{year}_4"


# =========================================================================
# O) crud.py — api_create_report
# =========================================================================

class TestApiCreateReport:
    @patch("app.routes.reports.crud.current_user")
    def test_create_missing_fields(self, mock_cu, app_and_client):
        app, client, _ = app_and_client
        mock_cu.id = 1
        resp = client.post("/pdf-reports/api/create",
                           json={},
                           content_type="application/json")
        assert resp.status_code == 400

    @patch("app.routes.reports.crud.current_user")
    def test_create_bad_date(self, mock_cu, app_and_client):
        app, client, _ = app_and_client
        mock_cu.id = 1
        resp = client.post("/pdf-reports/api/create",
                           json={"lab_type": "coal", "sample_ids": [1], "date_from": "bad"},
                           content_type="application/json")
        assert resp.status_code == 400

    @patch("app.routes.reports.crud.current_user")
    def test_create_unknown_lab_type(self, mock_cu, app_and_client):
        app, client, _ = app_and_client
        mock_cu.id = 1
        resp = client.post("/pdf-reports/api/create",
                           json={"lab_type": "unknown", "sample_ids": [1]},
                           content_type="application/json")
        assert resp.status_code == 400

    @patch("app.routes.reports.pdf_generator.generate_microbiology_report")
    @patch("app.routes.reports.crud.current_user")
    def test_create_microbiology_ok(self, mock_cu, mock_gen, app_and_client):
        app, client, _ = app_and_client
        mock_cu.id = 1

        report = MagicMock()
        report.id = 10
        report.report_number = "2026_10"
        mock_gen.return_value = (report, None)

        resp = client.post("/pdf-reports/api/create",
                           json={"lab_type": "microbiology", "sample_ids": [1, 2]},
                           content_type="application/json")
        assert resp.status_code == 200
        assert resp.get_json()["success"] is True

    @patch("app.routes.reports.pdf_generator.generate_water_report")
    @patch("app.routes.reports.crud.current_user")
    def test_create_water_ok(self, mock_cu, mock_gen, app_and_client):
        app, client, _ = app_and_client
        mock_cu.id = 1

        report = MagicMock()
        report.id = 11
        report.report_number = "2026_11"
        mock_gen.return_value = (report, None)

        resp = client.post("/pdf-reports/api/create",
                           json={"lab_type": "water", "sample_ids": [3]},
                           content_type="application/json")
        assert resp.status_code == 200

    @patch("app.routes.reports.pdf_generator.generate_coal_report")
    @patch("app.routes.reports.crud.current_user")
    def test_create_coal_ok(self, mock_cu, mock_gen, app_and_client):
        app, client, _ = app_and_client
        mock_cu.id = 1

        report = MagicMock()
        report.id = 12
        report.report_number = "2026_12"
        mock_gen.return_value = (report, None)

        resp = client.post("/pdf-reports/api/create",
                           json={"lab_type": "coal", "sample_ids": [4]},
                           content_type="application/json")
        assert resp.status_code == 200

    @patch("app.routes.reports.pdf_generator.generate_coal_report")
    @patch("app.routes.reports.crud.current_user")
    def test_create_with_error(self, mock_cu, mock_gen, app_and_client):
        app, client, _ = app_and_client
        mock_cu.id = 1
        mock_gen.return_value = (None, "Sample not found")

        resp = client.post("/pdf-reports/api/create",
                           json={"lab_type": "coal", "sample_ids": [4]},
                           content_type="application/json")
        assert resp.status_code == 400


# =========================================================================
# P) monthly_plan.py — monthly_plan page
# =========================================================================

class TestMonthlyPlanPage:
    @patch("app.routes.reports.monthly_plan.render_template", return_value="<html></html>")
    @patch("app.routes.reports.monthly_plan.build_monthly_plan_context")
    @patch("app.routes.reports.monthly_plan.now_local")
    def test_monthly_plan_default(self, mock_now, mock_ctx, mock_render, app_and_client):
        app, client, _ = app_and_client
        mock_now.return_value = datetime(2026, 3, 11, 10, 0)
        mock_ctx.return_value = {"weeks": [], "data": {}}

        resp = client.get("/reports/monthly_plan")
        assert resp.status_code == 200
        mock_ctx.assert_called_once_with(2026, 3)

    @patch("app.routes.reports.monthly_plan.render_template", return_value="<html></html>")
    @patch("app.routes.reports.monthly_plan.build_monthly_plan_context")
    @patch("app.routes.reports.monthly_plan.now_local")
    def test_monthly_plan_params(self, mock_now, mock_ctx, mock_render, app_and_client):
        app, client, _ = app_and_client
        mock_now.return_value = datetime(2026, 3, 11, 10, 0)
        mock_ctx.return_value = {}

        resp = client.get("/reports/monthly_plan?year=2025&month=6")
        assert resp.status_code == 200
        mock_ctx.assert_called_once_with(2025, 6)

    @patch("app.routes.reports.monthly_plan.render_template", return_value="<html></html>")
    @patch("app.routes.reports.monthly_plan.build_monthly_plan_context")
    @patch("app.routes.reports.monthly_plan.now_local")
    def test_monthly_plan_invalid_year_reset(self, mock_now, mock_ctx, mock_render, app_and_client):
        app, client, _ = app_and_client
        mock_now.return_value = datetime(2026, 3, 11, 10, 0)
        mock_ctx.return_value = {}

        resp = client.get("/reports/monthly_plan?year=1900&month=13")
        assert resp.status_code == 200
        mock_ctx.assert_called_once_with(2026, 3)


# =========================================================================
# Q) monthly_plan.py — api_get_monthly_plan
# =========================================================================

class TestApiGetMonthlyPlan:
    @patch("app.models.MonthlyPlan")
    def test_get_plan_ok(self, mock_mp, app_and_client):
        app, client, _ = app_and_client

        plan = MagicMock()
        plan.client_name = "CHPP"
        plan.sample_type = "2 hourly"
        plan.week = 1
        plan.planned_count = 10
        mock_mp.query.filter_by.return_value.all.return_value = [plan]

        resp = client.get("/reports/api/monthly_plan?year=2026&month=3")
        assert resp.status_code == 200
        data = resp.get_json()
        assert "plans" in data

    def test_get_plan_missing_params(self, app_and_client):
        app, client, _ = app_and_client
        resp = client.get("/reports/api/monthly_plan")
        assert resp.status_code == 400


# =========================================================================
# R) monthly_plan.py — api_save_monthly_plan
# =========================================================================

class TestApiSaveMonthlyPlan:
    @patch("app.routes.reports.monthly_plan.save_monthly_plans")
    @patch("app.routes.reports.monthly_plan.current_user")
    def test_save_ok(self, mock_cu, mock_save, app_and_client):
        app, client, _ = app_and_client
        mock_cu.role = "admin"
        mock_cu.id = 1
        mock_save.return_value = (True, 5, None)

        resp = client.post("/reports/api/monthly_plan",
                           json={"year": 2026, "month": 3, "plans": {"CHPP|2h|1": 10}},
                           content_type="application/json")
        assert resp.status_code == 200
        assert resp.get_json()["saved"] == 5

    @patch("app.routes.reports.monthly_plan.current_user")
    def test_save_forbidden(self, mock_cu, app_and_client):
        app, client, _ = app_and_client
        mock_cu.role = "analyst"
        resp = client.post("/reports/api/monthly_plan",
                           json={"year": 2026, "month": 3, "plans": {}},
                           content_type="application/json")
        assert resp.status_code == 403

    @patch("app.routes.reports.monthly_plan.current_user")
    def test_save_missing_params(self, mock_cu, app_and_client):
        app, client, _ = app_and_client
        mock_cu.role = "admin"
        resp = client.post("/reports/api/monthly_plan",
                           json={"plans": {}},
                           content_type="application/json")
        assert resp.status_code == 400

    @patch("app.routes.reports.monthly_plan.save_monthly_plans")
    @patch("app.routes.reports.monthly_plan.current_user")
    def test_save_service_error(self, mock_cu, mock_save, app_and_client):
        app, client, _ = app_and_client
        mock_cu.role = "admin"
        mock_cu.id = 1
        mock_save.return_value = (False, 0, "DB error")

        resp = client.post("/reports/api/monthly_plan",
                           json={"year": 2026, "month": 3, "plans": {}},
                           content_type="application/json")
        assert resp.status_code == 500


# =========================================================================
# S) monthly_plan.py — api_save_staff_settings
# =========================================================================

class TestApiSaveStaffSettings:
    @patch("app.routes.reports.monthly_plan.save_staff_settings")
    @patch("app.routes.reports.monthly_plan.current_user")
    def test_save_staff_ok(self, mock_cu, mock_save, app_and_client):
        app, client, _ = app_and_client
        mock_cu.role = "admin"
        mock_save.return_value = (True, None)

        resp = client.post("/reports/api/staff_settings",
                           json={"year": 2026, "month": 3, "staff_preparers": 5, "staff_chemists": 8},
                           content_type="application/json")
        assert resp.status_code == 200

    @patch("app.routes.reports.monthly_plan.current_user")
    def test_save_staff_forbidden(self, mock_cu, app_and_client):
        app, client, _ = app_and_client
        mock_cu.role = "analyst"
        resp = client.post("/reports/api/staff_settings",
                           json={"year": 2026, "month": 3},
                           content_type="application/json")
        assert resp.status_code == 403

    @patch("app.routes.reports.monthly_plan.current_user")
    def test_save_staff_missing_params(self, mock_cu, app_and_client):
        app, client, _ = app_and_client
        mock_cu.role = "admin"
        resp = client.post("/reports/api/staff_settings",
                           json={"staff_preparers": 5},
                           content_type="application/json")
        assert resp.status_code == 400

    @patch("app.routes.reports.monthly_plan.save_staff_settings")
    @patch("app.routes.reports.monthly_plan.current_user")
    def test_save_staff_error(self, mock_cu, mock_save, app_and_client):
        app, client, _ = app_and_client
        mock_cu.role = "admin"
        mock_save.return_value = (False, "DB error")

        resp = client.post("/reports/api/staff_settings",
                           json={"year": 2026, "month": 3},
                           content_type="application/json")
        assert resp.status_code == 500


# =========================================================================
# T) monthly_plan.py — api_plan_statistics
# =========================================================================

class TestApiPlanStatistics:
    @patch("app.routes.reports.monthly_plan.get_plan_statistics")
    @patch("app.routes.reports.monthly_plan.now_local")
    def test_statistics_ok(self, mock_now, mock_stats, app_and_client):
        app, client, _ = app_and_client
        mock_now.return_value = datetime(2026, 3, 11)
        mock_stats.return_value = {"monthly": [], "total": 0}

        resp = client.get("/reports/api/plan_statistics")
        assert resp.status_code == 200

    @patch("app.routes.reports.monthly_plan.get_plan_statistics")
    @patch("app.routes.reports.monthly_plan.now_local")
    def test_statistics_with_params(self, mock_now, mock_stats, app_and_client):
        app, client, _ = app_and_client
        mock_now.return_value = datetime(2026, 3, 11)
        mock_stats.return_value = {"data": []}

        resp = client.get("/reports/api/plan_statistics?from_year=2025&from_month=1&to_year=2026&to_month=3")
        assert resp.status_code == 200
        mock_stats.assert_called_once_with(2025, 1, 2026, 3)


# =========================================================================
# U) monthly_plan.py — api_weekly_performance
# =========================================================================

class TestApiWeeklyPerformance:
    @patch("app.routes.reports.monthly_plan.calculate_weekly_performance")
    def test_performance_ok(self, mock_calc, app_and_client):
        app, client, _ = app_and_client

        week_info = (1, date(2026, 3, 2), date(2026, 3, 8))
        mock_calc.return_value = ({"CHPP": [10]}, [week_info])

        resp = client.get("/reports/api/weekly_performance?year=2026&month=3")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["year"] == 2026

    def test_performance_missing_params(self, app_and_client):
        app, client, _ = app_and_client
        resp = client.get("/reports/api/weekly_performance")
        assert resp.status_code == 400


# =========================================================================
# V) monthly_plan.py — chemist_report
# =========================================================================

class TestChemistReport:
    @patch("app.routes.reports.monthly_plan.render_template", return_value="<html></html>")
    @patch("app.routes.reports.monthly_plan.build_chemist_report_data")
    @patch("app.routes.reports.monthly_plan._year_arg", return_value=2026)
    def test_chemist_report_ok(self, mock_year, mock_build, mock_render, app_and_client):
        app, client, _ = app_and_client
        mock_build.return_value = {"year": 2026, "data": []}

        resp = client.get("/reports/chemist_report")
        assert resp.status_code == 200

    @patch("app.routes.reports.monthly_plan.render_template", return_value="<html></html>")
    @patch("app.routes.reports.monthly_plan.build_chemist_report_data")
    @patch("app.routes.reports.monthly_plan._year_arg", return_value=2026)
    def test_chemist_report_with_dates(self, mock_year, mock_build, mock_render, app_and_client):
        app, client, _ = app_and_client
        mock_build.return_value = {"year": 2026, "data": []}

        resp = client.get("/reports/chemist_report?date_from=2026-01-01&date_to=2026-03-31")
        assert resp.status_code == 200
        mock_build.assert_called_once_with(2026, "2026-01-01", "2026-03-31")


# =========================================================================
# W) pdf_generator.py — create_pdf_from_html
# =========================================================================

class TestCreatePdfFromHtml:
    @patch("app.routes.reports.pdf_generator.XHTML2PDF_AVAILABLE", False)
    def test_raises_when_xhtml2pdf_unavailable(self, app_and_client):
        app, _, _ = app_and_client
        from app.routes.reports.pdf_generator import create_pdf_from_html
        with app.app_context():
            with pytest.raises(RuntimeError, match="xhtml2pdf"):
                create_pdf_from_html("<html></html>", "/tmp/test.pdf")

    @patch("app.routes.reports.pdf_generator.register_fonts")
    @patch("app.routes.reports.pdf_generator.pisa")
    @patch("app.routes.reports.pdf_generator.XHTML2PDF_AVAILABLE", True)
    @patch("builtins.open", new_callable=mock_open)
    def test_create_pdf_ok(self, mock_file, mock_pisa, mock_fonts, app_and_client):
        app, _, _ = app_and_client
        from app.routes.reports.pdf_generator import create_pdf_from_html

        status = MagicMock()
        status.err = 0
        mock_pisa.CreatePDF.return_value = status

        with app.app_context():
            result = create_pdf_from_html("<html>test</html>", "/tmp/out.pdf")
        assert result is True

    @patch("app.routes.reports.pdf_generator.register_fonts")
    @patch("app.routes.reports.pdf_generator.pisa")
    @patch("app.routes.reports.pdf_generator.XHTML2PDF_AVAILABLE", True)
    @patch("builtins.open", new_callable=mock_open)
    def test_create_pdf_error(self, mock_file, mock_pisa, mock_fonts, app_and_client):
        app, _, _ = app_and_client
        from app.routes.reports.pdf_generator import create_pdf_from_html

        status = MagicMock()
        status.err = 1
        mock_pisa.CreatePDF.return_value = status

        with app.app_context():
            result = create_pdf_from_html("<html></html>", "/tmp/out.pdf")
        assert result is False


# =========================================================================
# X) pdf_generator.py — register_fonts
# =========================================================================

class TestRegisterFonts:
    @patch("app.routes.reports.pdf_generator.TTFont", return_value=MagicMock())
    @patch("app.routes.reports.pdf_generator.os.path.exists", return_value=True)
    @patch("app.routes.reports.pdf_generator.pdfmetrics")
    def test_register_fonts_ok(self, mock_metrics, mock_exists, mock_ttfont, app_and_client):
        app, _, _ = app_and_client
        import app.routes.reports.pdf_generator as pg
        pg._font_registered = False
        with app.app_context():
            pg.register_fonts()
        assert pg._font_registered is True

    @patch("app.routes.reports.pdf_generator.os.path.exists", return_value=False)
    @patch("app.routes.reports.pdf_generator.pdfmetrics")
    def test_register_fonts_no_file(self, mock_metrics, mock_exists, app_and_client):
        app, _, _ = app_and_client
        import app.routes.reports.pdf_generator as pg
        pg._font_registered = False
        with app.app_context():
            pg.register_fonts()
        assert pg._font_registered is False

    def test_register_fonts_already_registered(self, app_and_client):
        app, _, _ = app_and_client
        import app.routes.reports.pdf_generator as pg
        pg._font_registered = True
        with app.app_context():
            pg.register_fonts()  # should be a no-op
        assert pg._font_registered is True


# =========================================================================
# Y) pdf_generator.py — generate_microbiology_report
# =========================================================================

class TestGenerateMicrobiologyReport:
    @patch("app.routes.reports.pdf_generator.generate_pdf_file", return_value="uploads/reports/test.pdf")
    @patch("app.routes.reports.crud.get_next_report_number", return_value="2026_1")
    @patch("app.routes.reports.pdf_generator.AnalysisResult")
    @patch("app.routes.reports.pdf_generator.Sample")
    @patch("app.routes.reports.pdf_generator.db")
    def test_ok(self, mock_db, mock_sample, mock_ar, mock_num, mock_gen_pdf, app_and_client):
        app, _, _ = app_and_client
        from app.routes.reports.pdf_generator import generate_microbiology_report

        s = MagicMock()
        s.id = 1
        s.sample_code = "S001"
        s.sample_date = date(2026, 3, 1)
        mock_sample.query.filter.return_value.order_by.return_value.all.return_value = [s]

        r = MagicMock()
        r.analysis_code = "MICRO_WATER"
        mock_ar.query.filter_by.return_value.all.return_value = [r]

        with app.app_context():
            report, error = generate_microbiology_report([1], date(2026, 3, 1), date(2026, 3, 31), 1)
        assert error is None

    @patch("app.routes.reports.pdf_generator.Sample")
    def test_no_samples(self, mock_sample, app_and_client):
        app, _, _ = app_and_client
        from app.routes.reports.pdf_generator import generate_microbiology_report

        mock_sample.query.filter.return_value.order_by.return_value.all.return_value = []
        with app.app_context():
            report, error = generate_microbiology_report([999], None, None, 1)
        assert report is None
        assert error == "Sample not found"


# =========================================================================
# Z) pdf_generator.py — generate_water_report
# =========================================================================

class TestGenerateWaterReport:
    @patch("app.routes.reports.pdf_generator.generate_pdf_file", return_value="uploads/reports/test.pdf")
    @patch("app.routes.reports.crud.get_next_report_number", return_value="2026_2")
    @patch("app.routes.reports.pdf_generator.AnalysisResult")
    @patch("app.routes.reports.pdf_generator.Sample")
    @patch("app.routes.reports.pdf_generator.db")
    def test_ok(self, mock_db, mock_sample, mock_ar, mock_num, mock_gen_pdf, app_and_client):
        app, _, _ = app_and_client
        from app.routes.reports.pdf_generator import generate_water_report

        s = MagicMock()
        s.id = 1
        s.sample_code = "W001"
        s.sample_date = date(2026, 3, 1)
        mock_sample.query.filter.return_value.order_by.return_value.all.return_value = [s]
        mock_ar.query.filter_by.return_value.all.return_value = []

        with app.app_context():
            report, error = generate_water_report([1], None, None, 1)
        assert error is None

    @patch("app.routes.reports.pdf_generator.Sample")
    def test_no_samples(self, mock_sample, app_and_client):
        app, _, _ = app_and_client
        from app.routes.reports.pdf_generator import generate_water_report

        mock_sample.query.filter.return_value.order_by.return_value.all.return_value = []
        with app.app_context():
            report, error = generate_water_report([999], None, None, 1)
        assert error == "Sample not found"

    @patch("app.routes.reports.pdf_generator.generate_pdf_file", return_value="uploads/reports/test.pdf")
    @patch("app.routes.reports.crud.get_next_report_number", return_value="2026_3")
    @patch("app.routes.reports.pdf_generator.AnalysisResult")
    @patch("app.routes.reports.pdf_generator.Sample")
    @patch("app.routes.reports.pdf_generator.db")
    def test_commit_error(self, mock_db, mock_sample, mock_ar, mock_num, mock_gen_pdf, app_and_client):
        app, _, _ = app_and_client
        from app.routes.reports.pdf_generator import generate_water_report
        from sqlalchemy.exc import SQLAlchemyError

        s = MagicMock()
        s.id = 1
        s.sample_code = "W001"
        s.sample_date = date(2026, 3, 1)
        mock_sample.query.filter.return_value.order_by.return_value.all.return_value = [s]
        mock_ar.query.filter_by.return_value.all.return_value = []

        mock_db.session.commit.side_effect = SQLAlchemyError("commit fail")

        with app.app_context():
            report, error = generate_water_report([1], None, None, 1)
        assert report is None
        assert error is not None


# =========================================================================
# AA) pdf_generator.py — generate_coal_report
# =========================================================================

class TestGenerateCoalReport:
    @patch("app.routes.reports.pdf_generator.generate_pdf_file", return_value="uploads/reports/coal.pdf")
    @patch("app.routes.reports.crud.get_next_report_number", return_value="2026_4")
    @patch("app.routes.reports.pdf_generator.AnalysisResult")
    @patch("app.routes.reports.pdf_generator.Sample")
    @patch("app.routes.reports.pdf_generator.db")
    def test_ok(self, mock_db, mock_sample, mock_ar, mock_num, mock_gen_pdf, app_and_client):
        app, _, _ = app_and_client
        from app.routes.reports.pdf_generator import generate_coal_report

        s = MagicMock()
        s.id = 1
        s.sample_code = "C001"
        s.sample_date = date(2026, 3, 1)
        mock_sample.query.filter.return_value.order_by.return_value.all.return_value = [s]
        mock_ar.query.filter_by.return_value.all.return_value = []

        with app.app_context():
            report, error = generate_coal_report([1], date(2026, 3, 1), date(2026, 3, 31), 1)
        assert error is None

    @patch("app.routes.reports.pdf_generator.Sample")
    def test_no_samples(self, mock_sample, app_and_client):
        app, _, _ = app_and_client
        from app.routes.reports.pdf_generator import generate_coal_report

        mock_sample.query.filter.return_value.order_by.return_value.all.return_value = []
        with app.app_context():
            report, error = generate_coal_report([999], None, None, 1)
        assert error == "Sample not found"

    @patch("app.routes.reports.pdf_generator.generate_pdf_file", return_value="uploads/reports/coal.pdf")
    @patch("app.routes.reports.crud.get_next_report_number", return_value="2026_5")
    @patch("app.routes.reports.pdf_generator.AnalysisResult")
    @patch("app.routes.reports.pdf_generator.Sample")
    @patch("app.routes.reports.pdf_generator.db")
    def test_commit_error(self, mock_db, mock_sample, mock_ar, mock_num, mock_gen_pdf, app_and_client):
        app, _, _ = app_and_client
        from app.routes.reports.pdf_generator import generate_coal_report
        from sqlalchemy.exc import SQLAlchemyError

        s = MagicMock()
        s.id = 1
        s.sample_code = "C001"
        s.sample_date = date(2026, 3, 1)
        mock_sample.query.filter.return_value.order_by.return_value.all.return_value = [s]
        mock_ar.query.filter_by.return_value.all.return_value = []
        mock_db.session.commit.side_effect = SQLAlchemyError("fail")

        with app.app_context():
            report, error = generate_coal_report([1], None, None, 1)
        assert report is None


# =========================================================================
# AB) pdf_generator.py — generate_pdf_file
# =========================================================================

class TestGeneratePdfFile:
    @patch("app.routes.reports.pdf_generator.create_pdf_from_html")
    @patch("app.routes.reports.pdf_generator.render_template", return_value="<html>pdf</html>")
    @patch("app.routes.reports.pdf_generator.os.path.exists")
    @patch("app.routes.reports.pdf_generator.os.makedirs")
    def test_generate_pdf_file(self, mock_mkdirs, mock_exists, mock_render, mock_create, app_and_client):
        app, _, _ = app_and_client
        from app.routes.reports.pdf_generator import generate_pdf_file

        mock_exists.return_value = True

        report = MagicMock()
        report.report_number = "2026_1"
        report.lab_type = "coal"
        samples = [MagicMock()]
        results = [{"sample": MagicMock(), "results": {}}]

        with app.app_context():
            path = generate_pdf_file(report, samples, results)
        assert "2026_1.pdf" in path
        mock_create.assert_called_once()

    @patch("app.routes.reports.pdf_generator.create_pdf_from_html")
    @patch("app.routes.reports.pdf_generator.render_template", return_value="<html>pdf</html>")
    @patch("app.routes.reports.pdf_generator.os.path.exists", return_value=False)
    @patch("app.routes.reports.pdf_generator.os.makedirs")
    def test_generate_pdf_file_no_logos(self, mock_mkdirs, mock_exists, mock_render, mock_create, app_and_client):
        app, _, _ = app_and_client
        from app.routes.reports.pdf_generator import generate_pdf_file

        report = MagicMock()
        report.report_number = "2026/2"
        report.lab_type = "water"
        samples = []
        results = []

        with app.app_context():
            path = generate_pdf_file(report, samples, results)
        assert "2026_2.pdf" in path


# =========================================================================
# AC) pdf_generator.py — regenerate_pdf
# =========================================================================

class TestRegeneratePdf:
    @patch("app.routes.reports.pdf_generator.create_pdf_from_html")
    @patch("app.routes.reports.pdf_generator.render_template", return_value="<html></html>")
    @patch("app.routes.reports.pdf_generator.os.path.exists", return_value=False)
    @patch("app.routes.reports.pdf_generator.os.makedirs")
    @patch("app.routes.reports.pdf_generator.AnalysisResult")
    @patch("app.routes.reports.pdf_generator.Sample")
    @patch("app.routes.reports.pdf_generator.db")
    def test_regenerate_ok(self, mock_db, mock_sample, mock_ar, mock_mkdirs, mock_exists, mock_render, mock_create, app_and_client):
        app, _, _ = app_and_client
        from app.routes.reports.pdf_generator import regenerate_pdf

        report = MagicMock()
        report.sample_ids = [1, 2]
        report.report_number = "2026_1"
        report.lab_type = "coal"

        s = MagicMock()
        s.id = 1
        mock_sample.query.filter.return_value.all.return_value = [s]

        r = MagicMock()
        r.analysis_code = "MAD"
        mock_ar.query.filter_by.return_value.all.return_value = [r]

        with app.app_context():
            regenerate_pdf(report)
        mock_db.session.commit.assert_called_once()

    @patch("app.routes.reports.pdf_generator.create_pdf_from_html")
    @patch("app.routes.reports.pdf_generator.render_template", return_value="<html></html>")
    @patch("app.routes.reports.pdf_generator.os.path.exists", return_value=False)
    @patch("app.routes.reports.pdf_generator.os.makedirs")
    @patch("app.routes.reports.pdf_generator.AnalysisResult")
    @patch("app.routes.reports.pdf_generator.Sample")
    @patch("app.routes.reports.pdf_generator.db")
    def test_regenerate_commit_error(self, mock_db, mock_sample, mock_ar, mock_mkdirs, mock_exists, mock_render, mock_create, app_and_client):
        app, _, _ = app_and_client
        from app.routes.reports.pdf_generator import regenerate_pdf
        from sqlalchemy.exc import SQLAlchemyError

        report = MagicMock()
        report.sample_ids = []
        report.report_number = "2026_2"
        report.lab_type = "water"

        mock_sample.query.filter.return_value.all.return_value = []

        mock_db.session.commit.side_effect = SQLAlchemyError("fail")

        with app.app_context():
            regenerate_pdf(report)  # should not raise
        mock_db.session.rollback.assert_called_once()

    @patch("app.routes.reports.pdf_generator.create_pdf_from_html")
    @patch("app.routes.reports.pdf_generator.render_template", return_value="<html></html>")
    @patch("app.routes.reports.pdf_generator.os.path.exists", return_value=False)
    @patch("app.routes.reports.pdf_generator.os.makedirs")
    @patch("app.routes.reports.pdf_generator.AnalysisResult")
    @patch("app.routes.reports.pdf_generator.Sample")
    @patch("app.routes.reports.pdf_generator.db")
    def test_regenerate_no_sample_ids(self, mock_db, mock_sample, mock_ar, mock_mkdirs, mock_exists, mock_render, mock_create, app_and_client):
        app, _, _ = app_and_client
        from app.routes.reports.pdf_generator import regenerate_pdf

        report = MagicMock()
        report.sample_ids = None
        report.report_number = "2026_3"
        report.lab_type = "microbiology"

        mock_sample.query.filter.return_value.all.return_value = []

        with app.app_context():
            regenerate_pdf(report)
