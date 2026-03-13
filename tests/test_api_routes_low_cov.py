# tests/test_api_routes_low_cov.py
# -*- coding: utf-8 -*-
"""
Tests for API route files with low coverage:
  - analytics_api.py
  - workflow_api.py
  - instrument_api.py
  - report_builder_api.py
  - sla_api.py
"""

import io
from dataclasses import dataclass, field
from types import SimpleNamespace
from unittest.mock import patch, MagicMock

import pytest


# ── Helpers ────────────────────────────────────────────────────────────────

API = "/api/v1"


def json_ok(resp):
    """Assert 200 + success=True, return data dict."""
    assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.data}"
    body = resp.get_json()
    assert body["success"] is True
    return body.get("data")


def json_fail(resp, status=400):
    """Assert expected status + success=False."""
    assert resp.status_code == status, f"Expected {status}, got {resp.status_code}: {resp.data}"
    body = resp.get_json()
    if body is not None:
        assert body["success"] is False
    return body


# ═══════════════════════════════════════════════════════════════════════════
#  ANALYTICS API
# ═══════════════════════════════════════════════════════════════════════════

class TestAnalyticsReport:
    """GET /api/v1/analytics/report"""

    @patch("app.services.analytics_service.get_full_analytics")
    def test_success(self, mock_fn, auth_admin):
        mock_fn.return_value = SimpleNamespace(
            timestamp="2026-01-01T00:00:00",
            period="2h",
            sample_count=10,
            analysis_count=20,
            quality_score=SimpleNamespace(
                score=85, grade="A", color="green",
                breakdown={"qc": 90}, message="Good",
            ),
            anomalies=[],
            trends=[],
            insights=[],
            shift_comparison={},
        )
        resp = auth_admin.get(f"{API}/analytics/report?hours=4&client=CHPP")
        data = json_ok(resp)
        assert data["sample_count"] == 10
        assert data["quality_score"]["score"] == 85
        mock_fn.assert_called_once_with(hours_back=4, client_name="CHPP")

    @patch("app.services.analytics_service.get_full_analytics")
    def test_clamp_hours(self, mock_fn, auth_admin):
        mock_fn.return_value = SimpleNamespace(
            timestamp="", period="", sample_count=0, analysis_count=0,
            quality_score=SimpleNamespace(score=0, grade="", color="", breakdown={}, message=""),
            anomalies=[], trends=[], insights=[], shift_comparison={},
        )
        auth_admin.get(f"{API}/analytics/report?hours=100")
        # 100 clamped to 48
        mock_fn.assert_called_once_with(hours_back=48, client_name=None)

    @patch("app.services.analytics_service.get_full_analytics", side_effect=RuntimeError("boom"))
    def test_error(self, mock_fn, auth_admin):
        resp = auth_admin.get(f"{API}/analytics/report")
        assert resp.status_code == 500

    def test_unauthenticated(self, client):
        resp = client.get(f"{API}/analytics/report")
        assert resp.status_code in (302, 401)


class TestAnalyticsAnomalies:
    """GET /api/v1/analytics/anomalies"""

    @patch("app.services.analytics_service.detect_anomalies")
    def test_success(self, mock_detect, auth_admin, app):
        mock_detect.return_value = [
            SimpleNamespace(
                sample_code="S1", analysis_code="Mad", value=5.5,
                z_score=3.2, severity="critical", message="High",
                recommendation="Recheck",
            )
        ]
        resp = auth_admin.get(f"{API}/analytics/anomalies?hours=4")
        data = json_ok(resp)
        assert data["count"] == 1
        assert data["critical"] == 1

    @patch("app.services.analytics_service.detect_anomalies", side_effect=RuntimeError("x"))
    def test_error(self, mock_detect, auth_admin):
        resp = auth_admin.get(f"{API}/analytics/anomalies")
        assert resp.status_code == 500


class TestAnalyticsTrends:
    """GET /api/v1/analytics/trends"""

    @patch("app.services.analytics_service.analyze_trends")
    def test_success(self, mock_fn, auth_admin):
        mock_fn.return_value = SimpleNamespace(
            analysis_code="Mad", direction="up", slope=0.1,
            r_squared=0.95, change_pct=5.0, confidence="high",
            message="Trending up", recent_mean=6.0, historical_mean=5.5,
        )
        resp = auth_admin.get(f"{API}/analytics/trends?codes=Mad,Aad&days=30")
        data = json_ok(resp)
        assert len(data) == 2
        assert data[0]["analysis_code"] == "Mad"

    @patch("app.services.analytics_service.analyze_trends")
    def test_clamp_days(self, mock_fn, auth_admin):
        mock_fn.return_value = SimpleNamespace(
            analysis_code="Mad", direction="", slope=0, r_squared=0,
            change_pct=0, confidence="", message="", recent_mean=0, historical_mean=0,
        )
        auth_admin.get(f"{API}/analytics/trends?codes=Mad&days=1")
        # 1 clamped to 7
        mock_fn.assert_called_once_with("Mad", days=7, client_name=None)

    @patch("app.services.analytics_service.analyze_trends", side_effect=RuntimeError("x"))
    def test_error(self, mock_fn, auth_admin):
        resp = auth_admin.get(f"{API}/analytics/trends?codes=Mad")
        assert resp.status_code == 500


class TestAnalyticsQualityScore:
    """GET /api/v1/analytics/quality-score"""

    @patch("app.services.analytics_service.calculate_quality_score")
    def test_success(self, mock_calc, auth_admin):
        mock_calc.return_value = SimpleNamespace(
            score=92, grade="A", color="green",
            breakdown={"qc": 95}, message="Excellent",
        )
        resp = auth_admin.get(f"{API}/analytics/quality-score?hours=8")
        data = json_ok(resp)
        assert data["score"] == 92

    @patch("app.services.analytics_service.calculate_quality_score", side_effect=RuntimeError("x"))
    def test_error(self, mock_calc, auth_admin):

        resp = auth_admin.get(f"{API}/analytics/quality-score")
        assert resp.status_code == 500


class TestAnalyticsHistoricalStats:
    """GET /api/v1/analytics/historical-stats"""

    @patch("app.services.analytics_service.get_historical_stats")
    def test_success(self, mock_fn, auth_admin):
        mock_fn.return_value = {"mean": 5.5, "sd": 0.3, "median": 5.4, "values": [1, 2, 3]}
        resp = auth_admin.get(f"{API}/analytics/historical-stats?code=Mad&days=90")
        data = json_ok(resp)
        assert data["mean"] == 5.5
        # "values" key should be removed
        assert "values" not in data

    def test_missing_code(self, auth_admin):
        resp = auth_admin.get(f"{API}/analytics/historical-stats")
        assert resp.status_code == 400

    @patch("app.services.analytics_service.get_historical_stats", side_effect=RuntimeError("x"))
    def test_error(self, mock_fn, auth_admin):
        resp = auth_admin.get(f"{API}/analytics/historical-stats?code=Mad")
        assert resp.status_code == 500


# ═══════════════════════════════════════════════════════════════════════════
#  WORKFLOW API
# ═══════════════════════════════════════════════════════════════════════════

WF_BASE = f"{API}/workflow"


class TestWorkflowList:
    @patch("app.routes.api.workflow_api.list_workflows")
    def test_success(self, mock_fn, auth_admin):
        mock_fn.return_value = [{"name": "coal_analysis"}, {"name": "water_analysis"}]
        resp = auth_admin.get(f"{WF_BASE}/list")
        data = json_ok(resp)
        assert len(data) == 2

    def test_unauthenticated(self, client):
        resp = client.get(f"{WF_BASE}/list")
        assert resp.status_code in (302, 401)


class TestWorkflowGet:
    @patch("app.routes.api.workflow_api.get_workflow_config")
    def test_success(self, mock_fn, auth_admin):
        mock_fn.return_value = {"name": "coal_analysis", "states": {}}
        resp = auth_admin.get(f"{WF_BASE}/coal_analysis")
        data = json_ok(resp)
        assert data["name"] == "coal_analysis"

    @patch("app.routes.api.workflow_api.get_workflow_config", side_effect=ValueError("not found"))
    def test_not_found(self, mock_fn, auth_admin):
        resp = auth_admin.get(f"{WF_BASE}/nonexistent")
        json_fail(resp, 404)


class TestWorkflowStates:
    @patch("app.routes.api.workflow_api.WorkflowEngine")
    def test_success(self, mock_cls, auth_admin):
        engine = MagicMock()
        engine.get_states.return_value = [{"key": "pending"}]
        mock_cls.return_value = engine
        resp = auth_admin.get(f"{WF_BASE}/coal/states")
        data = json_ok(resp)
        assert data == [{"key": "pending"}]

    @patch("app.routes.api.workflow_api.WorkflowEngine", side_effect=ValueError("bad"))
    def test_not_found(self, mock_cls, auth_admin):
        resp = auth_admin.get(f"{WF_BASE}/bad/states")
        json_fail(resp, 404)


class TestWorkflowTransitions:
    @patch("app.routes.api.workflow_api.WorkflowEngine")
    def test_all_transitions(self, mock_cls, auth_admin):
        engine = MagicMock()
        engine.get_transitions.return_value = [{"from": "a", "to": "b"}]
        mock_cls.return_value = engine
        resp = auth_admin.get(f"{WF_BASE}/coal/transitions")
        data = json_ok(resp)
        assert len(data) == 1

    @patch("app.routes.api.workflow_api.WorkflowEngine")
    def test_from_state(self, mock_cls, auth_admin):
        engine = MagicMock()
        engine.get_available_transitions.return_value = [{"to": "approved"}]
        mock_cls.return_value = engine
        resp = auth_admin.get(f"{WF_BASE}/coal/transitions?from_state=pending")
        data = json_ok(resp)
        assert len(data) == 1

    @patch("app.routes.api.workflow_api.WorkflowEngine", side_effect=ValueError("x"))
    def test_not_found(self, mock_cls, auth_admin):
        resp = auth_admin.get(f"{WF_BASE}/bad/transitions")
        json_fail(resp, 404)


class TestWorkflowCanTransition:
    @patch("app.routes.api.workflow_api.WorkflowEngine")
    def test_success(self, mock_cls, auth_admin):
        engine = MagicMock()
        engine.can_transition.return_value = SimpleNamespace(
            allowed=True, reason="OK", transition={"from": "a", "to": "b"},
        )
        mock_cls.return_value = engine
        resp = auth_admin.post(
            f"{WF_BASE}/coal/can_transition",
            json={"from_state": "pending", "to_state": "approved"},
        )
        data = json_ok(resp)
        assert data["allowed"] is True

    def test_missing_states(self, auth_admin):
        resp = auth_admin.post(
            f"{WF_BASE}/coal/can_transition",
            json={"from_state": "pending"},
        )
        json_fail(resp, 400)

    def test_empty_body(self, auth_admin):
        resp = auth_admin.post(
            f"{WF_BASE}/coal/can_transition",
            json={},
        )
        json_fail(resp, 400)

    @patch("app.routes.api.workflow_api.WorkflowEngine", side_effect=ValueError("x"))
    def test_not_found(self, mock_cls, auth_admin):
        resp = auth_admin.post(
            f"{WF_BASE}/bad/can_transition",
            json={"from_state": "a", "to_state": "b"},
        )
        json_fail(resp, 404)


class TestWorkflowSave:
    @patch("app.routes.api.workflow_api.save_workflow_config")
    def test_admin_success(self, mock_fn, auth_admin):
        resp = auth_admin.post(
            f"{WF_BASE}/coal/save",
            json={"states": {}, "transitions": []},
        )
        data = json_ok(resp)
        mock_fn.assert_called_once()

    def test_non_admin_forbidden(self, auth_user):
        resp = auth_user.post(f"{WF_BASE}/coal/save", json={"states": {}})
        json_fail(resp, 403)

    def test_empty_body(self, auth_admin):
        resp = auth_admin.post(
            f"{WF_BASE}/coal/save",
            content_type="application/json",
            data="{}",
        )
        # Empty config {} is still truthy but has no valid data; however the
        # route checks `if not config` which is False for {}, so it passes
        # through to save_workflow_config. Send truly null body instead:
        resp2 = auth_admin.post(
            f"{WF_BASE}/coal/save",
            content_type="application/json",
            data="null",
        )
        assert resp2.status_code == 400

    @patch("app.routes.api.workflow_api.save_workflow_config", side_effect=ValueError("bad config"))
    def test_invalid_config(self, mock_fn, auth_admin):
        resp = auth_admin.post(f"{WF_BASE}/coal/save", json={"x": 1})
        json_fail(resp, 400)


class TestWorkflowReset:
    @patch("app.routes.api.workflow_api.reset_workflow_config")
    def test_admin_success(self, mock_fn, auth_admin):
        resp = auth_admin.post(f"{WF_BASE}/coal/reset")
        json_ok(resp)
        mock_fn.assert_called_once_with("coal")

    def test_non_admin_forbidden(self, auth_user):
        resp = auth_user.post(f"{WF_BASE}/coal/reset")
        json_fail(resp, 403)


class TestWorkflowAddState:
    @patch("app.routes.api.workflow_api.save_workflow_config")
    @patch("app.routes.api.workflow_api.get_workflow_config")
    def test_success(self, mock_get, mock_save, auth_admin):
        mock_get.return_value = {"states": {"pending": {}}, "transitions": []}
        resp = auth_admin.post(
            f"{WF_BASE}/coal/add_state",
            json={"key": "new_state", "label": "New"},
        )
        json_ok(resp)
        mock_save.assert_called_once()

    def test_non_admin_forbidden(self, auth_user):
        resp = auth_user.post(f"{WF_BASE}/coal/add_state", json={"key": "x"})
        json_fail(resp, 403)

    def test_missing_key(self, auth_admin):
        resp = auth_admin.post(f"{WF_BASE}/coal/add_state", json={})
        json_fail(resp, 400)

    @patch("app.routes.api.workflow_api.get_workflow_config")
    def test_duplicate_state(self, mock_get, auth_admin):
        mock_get.return_value = {"states": {"existing": {}}}
        resp = auth_admin.post(
            f"{WF_BASE}/coal/add_state",
            json={"key": "existing"},
        )
        json_fail(resp, 400)

    @patch("app.routes.api.workflow_api.get_workflow_config", side_effect=ValueError("x"))
    def test_workflow_not_found(self, mock_get, auth_admin):
        resp = auth_admin.post(
            f"{WF_BASE}/bad/add_state",
            json={"key": "new"},
        )
        json_fail(resp, 404)


class TestWorkflowAddTransition:
    @patch("app.routes.api.workflow_api.save_workflow_config")
    @patch("app.routes.api.workflow_api.get_workflow_config")
    def test_success(self, mock_get, mock_save, auth_admin):
        mock_get.return_value = {"states": {"a": {}, "b": {}}, "transitions": []}
        resp = auth_admin.post(
            f"{WF_BASE}/coal/add_transition",
            json={"from": "a", "to": "b", "label": "Move"},
        )
        json_ok(resp)
        mock_save.assert_called_once()

    def test_non_admin_forbidden(self, auth_user):
        resp = auth_user.post(f"{WF_BASE}/coal/add_transition", json={"from": "a", "to": "b"})
        json_fail(resp, 403)

    def test_missing_fields(self, auth_admin):
        resp = auth_admin.post(f"{WF_BASE}/coal/add_transition", json={"from": "a"})
        json_fail(resp, 400)

    @patch("app.routes.api.workflow_api.get_workflow_config")
    def test_invalid_states(self, mock_get, auth_admin):
        mock_get.return_value = {"states": {"a": {}}}
        resp = auth_admin.post(
            f"{WF_BASE}/coal/add_transition",
            json={"from": "a", "to": "missing"},
        )
        json_fail(resp, 400)

    @patch("app.routes.api.workflow_api.get_workflow_config", side_effect=ValueError("x"))
    def test_workflow_not_found(self, mock_get, auth_admin):
        resp = auth_admin.post(
            f"{WF_BASE}/bad/add_transition",
            json={"from": "a", "to": "b"},
        )
        json_fail(resp, 404)


# ═══════════════════════════════════════════════════════════════════════════
#  INSTRUMENT API
# ═══════════════════════════════════════════════════════════════════════════

INST = f"{API}/instrument"


class TestInstrumentUpload:
    @patch("app.routes.api.instrument_api.import_instrument_file")
    def test_success(self, mock_fn, auth_admin):
        mock_fn.return_value = 5
        data = {
            "file": (io.BytesIO(b"col1,col2\n1,2\n"), "test.csv"),
            "instrument_type": "generic_csv",
            "instrument_name": "AAS-01",
        }
        resp = auth_admin.post(f"{INST}/upload", data=data, content_type="multipart/form-data")
        result = json_ok(resp)
        assert result["count"] == 5

    def test_no_file(self, auth_admin):
        resp = auth_admin.post(f"{INST}/upload", data={}, content_type="multipart/form-data")
        json_fail(resp, 400)

    def test_non_admin_forbidden(self, auth_user):
        data = {"file": (io.BytesIO(b"data"), "test.csv")}
        resp = auth_user.post(f"{INST}/upload", data=data, content_type="multipart/form-data")
        json_fail(resp, 403)

    @patch("app.routes.api.instrument_api.import_instrument_file", side_effect=ValueError("bad format"))
    def test_parse_error(self, mock_fn, auth_admin):
        data = {"file": (io.BytesIO(b"bad"), "test.csv")}
        resp = auth_admin.post(f"{INST}/upload", data=data, content_type="multipart/form-data")
        json_fail(resp, 400)


class TestInstrumentPending:
    @patch("app.routes.api.instrument_api.get_pending_readings")
    def test_success(self, mock_fn, auth_admin):
        from datetime import datetime
        reading = SimpleNamespace(
            id=1, instrument_name="AAS", instrument_type="aas",
            sample_code="S1", analysis_code="Mad", parsed_value=5.5,
            unit="%", source_file="file.csv", status="pending",
            created_at=datetime(2026, 1, 1),
        )
        mock_fn.return_value = [reading]
        resp = auth_admin.get(f"{INST}/pending?instrument_type=aas&limit=50")
        data = json_ok(resp)
        assert len(data) == 1
        assert data[0]["id"] == 1

    @patch("app.routes.api.instrument_api.get_pending_readings")
    def test_limit_clamped(self, mock_fn, auth_admin):
        mock_fn.return_value = []
        auth_admin.get(f"{INST}/pending?limit=9999")
        mock_fn.assert_called_once_with(None, 500)


class TestInstrumentApprove:
    @patch("app.routes.api.instrument_api.approve_reading")
    def test_success(self, mock_fn, auth_admin):
        mock_fn.return_value = SimpleNamespace(id=1, status="approved")
        resp = auth_admin.post(f"{INST}/approve/1")
        data = json_ok(resp)
        assert data["status"] == "approved"

    def test_non_admin_forbidden(self, auth_user):
        resp = auth_user.post(f"{INST}/approve/1")
        json_fail(resp, 403)

    @patch("app.routes.api.instrument_api.approve_reading", side_effect=ValueError("not found"))
    def test_not_found(self, mock_fn, auth_admin):
        resp = auth_admin.post(f"{INST}/approve/999")
        json_fail(resp, 400)


class TestInstrumentReject:
    @patch("app.routes.api.instrument_api.reject_reading")
    def test_success(self, mock_fn, auth_admin):
        mock_fn.return_value = SimpleNamespace(id=1, status="rejected")
        resp = auth_admin.post(f"{INST}/reject/1", json={"reason": "bad data"})
        data = json_ok(resp)
        assert data["status"] == "rejected"

    def test_non_admin_forbidden(self, auth_user):
        resp = auth_user.post(f"{INST}/reject/1", json={"reason": "x"})
        json_fail(resp, 403)

    @patch("app.routes.api.instrument_api.reject_reading", side_effect=ValueError("x"))
    def test_error(self, mock_fn, auth_admin):
        resp = auth_admin.post(f"{INST}/reject/999", json={})
        json_fail(resp, 400)


class TestInstrumentBulkApprove:
    @patch("app.routes.api.instrument_api.bulk_approve")
    def test_success(self, mock_fn, auth_admin):
        mock_fn.return_value = 3
        resp = auth_admin.post(f"{INST}/bulk-approve", json={"ids": [1, 2, 3]})
        data = json_ok(resp)
        assert data["approved"] == 3

    def test_non_admin_forbidden(self, auth_user):
        resp = auth_user.post(f"{INST}/bulk-approve", json={"ids": [1]})
        json_fail(resp, 403)

    def test_empty_ids(self, auth_admin):
        resp = auth_admin.post(f"{INST}/bulk-approve", json={"ids": []})
        json_fail(resp, 400)

    def test_too_many_ids(self, auth_admin):
        resp = auth_admin.post(f"{INST}/bulk-approve", json={"ids": list(range(501))})
        json_fail(resp, 400)


class TestInstrumentBulkReject:
    @patch("app.routes.api.instrument_api.bulk_reject")
    def test_success(self, mock_fn, auth_admin):
        mock_fn.return_value = 2
        resp = auth_admin.post(
            f"{INST}/bulk-reject", json={"ids": [1, 2], "reason": "calibration error"}
        )
        data = json_ok(resp)
        assert data["rejected"] == 2

    def test_non_admin_forbidden(self, auth_user):
        resp = auth_user.post(f"{INST}/bulk-reject", json={"ids": [1]})
        json_fail(resp, 403)

    def test_empty_ids(self, auth_admin):
        resp = auth_admin.post(f"{INST}/bulk-reject", json={"ids": []})
        json_fail(resp, 400)


class TestInstrumentStats:
    @patch("app.routes.api.instrument_api.get_reading_stats")
    def test_success(self, mock_fn, auth_admin):
        mock_fn.return_value = {"total": 100, "pending": 10}
        resp = auth_admin.get(f"{INST}/stats")
        data = json_ok(resp)
        assert data["total"] == 100


class TestInstrumentTypes:
    @patch("app.routes.api.instrument_api.get_supported_instruments")
    def test_success(self, mock_fn, auth_admin):
        mock_fn.return_value = [{"type": "aas", "label": "AAS"}]
        resp = auth_admin.get(f"{INST}/types")
        data = json_ok(resp)
        assert len(data) == 1


# ═══════════════════════════════════════════════════════════════════════════
#  REPORT BUILDER API
# ═══════════════════════════════════════════════════════════════════════════

RB = f"{API}/report-builder"


class TestRBEntities:
    @patch("app.routes.api.report_builder_api.get_available_entities")
    def test_success(self, mock_fn, auth_admin):
        mock_fn.return_value = [{"name": "sample"}, {"name": "analysis"}]
        resp = auth_admin.get(f"{RB}/entities")
        data = json_ok(resp)
        assert len(data) == 2

    def test_unauthenticated(self, client):
        resp = client.get(f"{RB}/entities")
        assert resp.status_code in (302, 401)


class TestRBColumns:
    @patch("app.routes.api.report_builder_api.get_available_columns")
    def test_success(self, mock_fn, auth_admin):
        mock_fn.return_value = [{"name": "id"}, {"name": "sample_code"}]
        resp = auth_admin.get(f"{RB}/columns/sample")
        data = json_ok(resp)
        assert len(data) == 2

    @patch("app.routes.api.report_builder_api.get_available_columns")
    def test_unknown_entity(self, mock_fn, auth_admin):
        mock_fn.return_value = []
        resp = auth_admin.get(f"{RB}/columns/bogus")
        json_fail(resp, 404)


class TestRBPreview:
    @patch("app.routes.api.report_builder_api.execute_report")
    def test_success(self, mock_fn, auth_admin):
        mock_fn.return_value = {"rows": [], "columns": ["id"]}
        resp = auth_admin.post(f"{RB}/preview", json={"entity": "sample", "columns": ["id"]})
        json_ok(resp)

    @patch("app.routes.api.report_builder_api.execute_report")
    def test_limit_capped(self, mock_fn, auth_admin):
        mock_fn.return_value = {"rows": []}
        auth_admin.post(f"{RB}/preview", json={"entity": "sample", "limit": 500})
        config = mock_fn.call_args[0][0]
        assert config["limit"] == 100

    def test_empty_body(self, auth_admin):
        resp = auth_admin.post(f"{RB}/preview", json={})
        # {} is truthy so passes `if not config` check, goes to execute_report
        # with empty config. Let's test with data="" instead
        resp2 = auth_admin.post(
            f"{RB}/preview", data=b"null", content_type="application/json"
        )
        assert resp2.status_code == 400

    @patch("app.routes.api.report_builder_api.execute_report", side_effect=ValueError("bad"))
    def test_value_error(self, mock_fn, auth_admin):
        resp = auth_admin.post(f"{RB}/preview", json={"entity": "sample"})
        json_fail(resp, 400)

    @patch("app.routes.api.report_builder_api.execute_report", side_effect=RuntimeError("x"))
    def test_generic_error(self, mock_fn, auth_admin):
        resp = auth_admin.post(f"{RB}/preview", json={"entity": "sample"})
        json_fail(resp, 500)


class TestRBExecute:
    @patch("app.routes.api.report_builder_api.execute_report")
    def test_success(self, mock_fn, auth_admin):
        mock_fn.return_value = {"rows": [{"id": 1}], "total": 1}
        resp = auth_admin.post(f"{RB}/execute", json={"entity": "sample"})
        json_ok(resp)

    def test_empty_body(self, auth_admin):
        resp = auth_admin.post(
            f"{RB}/execute", data=b"null", content_type="application/json"
        )
        assert resp.status_code == 400

    @patch("app.routes.api.report_builder_api.execute_report", side_effect=ValueError("x"))
    def test_value_error(self, mock_fn, auth_admin):
        resp = auth_admin.post(f"{RB}/execute", json={"entity": "x"})
        json_fail(resp, 400)

    @patch("app.routes.api.report_builder_api.execute_report", side_effect=RuntimeError("x"))
    def test_generic_error(self, mock_fn, auth_admin):
        resp = auth_admin.post(f"{RB}/execute", json={"entity": "x"})
        json_fail(resp, 500)


class TestRBExport:
    @patch("app.routes.api.report_builder_api.export_report_csv")
    def test_csv_export(self, mock_fn, auth_admin):
        mock_fn.return_value = "id,code\n1,S1\n"
        resp = auth_admin.post(
            f"{RB}/export",
            json={"entity": "sample", "export_format": "csv", "name": "my_report"},
        )
        assert resp.status_code == 200
        assert "text/csv" in resp.content_type
        assert b"id,code" in resp.data

    @patch("app.routes.api.report_builder_api.export_report_json")
    def test_json_export(self, mock_fn, auth_admin):
        mock_fn.return_value = '[{"id": 1}]'
        resp = auth_admin.post(
            f"{RB}/export",
            json={"entity": "sample", "export_format": "json", "name": "rpt"},
        )
        assert resp.status_code == 200
        assert "application/json" in resp.content_type

    def test_empty_body(self, auth_admin):
        resp = auth_admin.post(
            f"{RB}/export", data=b"null", content_type="application/json"
        )
        assert resp.status_code == 400

    @patch("app.routes.api.report_builder_api.export_report_csv", side_effect=ValueError("x"))
    def test_value_error(self, mock_fn, auth_admin):
        resp = auth_admin.post(f"{RB}/export", json={"entity": "sample"})
        json_fail(resp, 400)

    @patch("app.routes.api.report_builder_api.export_report_csv", side_effect=RuntimeError("x"))
    def test_generic_error(self, mock_fn, auth_admin):
        resp = auth_admin.post(f"{RB}/export", json={"entity": "sample"})
        json_fail(resp, 500)


class TestRBTemplates:
    @patch("app.routes.api.report_builder_api.list_report_templates")
    def test_list(self, mock_fn, auth_admin):
        mock_fn.return_value = [{"name": "t1"}, {"name": "t2"}]
        resp = auth_admin.get(f"{RB}/templates")
        data = json_ok(resp)
        assert len(data) == 2

    @patch("app.routes.api.report_builder_api.get_report_template")
    def test_get_found(self, mock_fn, auth_admin):
        mock_fn.return_value = {"name": "t1", "config": {}}
        resp = auth_admin.get(f"{RB}/templates/t1")
        json_ok(resp)

    @patch("app.routes.api.report_builder_api.get_report_template")
    def test_get_not_found(self, mock_fn, auth_admin):
        mock_fn.return_value = None
        resp = auth_admin.get(f"{RB}/templates/missing")
        json_fail(resp, 404)

    @patch("app.routes.api.report_builder_api.save_report_template")
    def test_save_success(self, mock_fn, auth_admin):
        mock_fn.return_value = 42
        resp = auth_admin.post(
            f"{RB}/templates/save",
            json={"name": "my_tpl", "config": {"entity": "sample"}, "description": "test"},
        )
        data = json_ok(resp)
        assert data["id"] == 42

    def test_save_missing_name(self, auth_admin):
        resp = auth_admin.post(f"{RB}/templates/save", json={"config": {"x": 1}})
        json_fail(resp, 400)

    def test_save_missing_config(self, auth_admin):
        resp = auth_admin.post(f"{RB}/templates/save", json={"name": "t1"})
        json_fail(resp, 400)

    @patch("app.routes.api.report_builder_api.delete_report_template")
    def test_delete_success(self, mock_fn, auth_admin):
        mock_fn.return_value = True
        resp = auth_admin.post(f"{RB}/templates/t1/delete")
        json_ok(resp)

    @patch("app.routes.api.report_builder_api.delete_report_template")
    def test_delete_not_found(self, mock_fn, auth_admin):
        mock_fn.return_value = False
        resp = auth_admin.post(f"{RB}/templates/missing/delete")
        json_fail(resp, 404)

    def test_delete_non_admin(self, auth_user):
        resp = auth_user.post(f"{RB}/templates/t1/delete")
        json_fail(resp, 403)


# ═══════════════════════════════════════════════════════════════════════════
#  SLA API
# ═══════════════════════════════════════════════════════════════════════════

SLA = f"{API}/sla"


class TestSLASummary:
    @patch("app.routes.api.sla_api.get_sla_summary")
    def test_success(self, mock_fn, auth_admin):
        @dataclass
        class SLASummary:
            total: int = 100
            on_track: int = 80
            overdue: int = 10
            due_soon: int = 10

        mock_fn.return_value = SLASummary()
        resp = auth_admin.get(f"{SLA}/summary?lab_type=coal")
        data = json_ok(resp)
        assert data["total"] == 100

    def test_unauthenticated(self, client):
        resp = client.get(f"{SLA}/summary")
        assert resp.status_code in (302, 401)


class TestSLAOverdue:
    @patch("app.routes.api.sla_api.get_overdue_samples")
    def test_success(self, mock_fn, auth_admin):
        @dataclass
        class OverdueSample:
            sample_id: int = 1
            sample_code: str = "S1"
            hours_overdue: float = 5.5

        mock_fn.return_value = [OverdueSample()]
        resp = auth_admin.get(f"{SLA}/overdue?lab_type=coal&limit=50")
        body = resp.get_json()
        assert body["success"] is True
        assert body["count"] == 1


class TestSLADueSoon:
    @patch("app.routes.api.sla_api.get_due_soon_samples")
    def test_success(self, mock_fn, auth_admin):
        mock_fn.return_value = [{"sample_id": 1, "hours_left": 3}]
        resp = auth_admin.get(f"{SLA}/due_soon?lab_type=coal&hours=12")
        body = resp.get_json()
        assert body["success"] is True
        assert body["count"] == 1
        mock_fn.assert_called_once_with("coal", 12)


class TestSLABulkAssign:
    @patch("app.routes.api.sla_api.bulk_assign_sla")
    def test_admin_success(self, mock_fn, auth_admin):
        mock_fn.return_value = 5
        resp = auth_admin.post(f"{SLA}/assign?lab_type=coal")
        data = json_ok(resp)
        assert data["count"] == 5

    def test_non_admin_forbidden(self, auth_user):
        resp = auth_user.post(f"{SLA}/assign")
        json_fail(resp, 403)


class TestSLASet:
    @patch("app.routes.api.sla_api.assign_sla")
    @patch("app.routes.api.sla_api.db")
    def test_success(self, mock_db, mock_assign, auth_admin, app):
        sample = MagicMock()
        sample.id = 1
        sample.sla_hours = 48
        sample.due_date = None
        sample.priority = "normal"
        mock_db.session.get.return_value = sample

        resp = auth_admin.post(
            f"{SLA}/set/1",
            json={"sla_hours": 24, "priority": "urgent"},
        )
        body = resp.get_json()
        assert body["success"] is True
        assert sample.sla_hours == 24
        assert sample.priority == "urgent"

    @patch("app.routes.api.sla_api.db")
    def test_not_found(self, mock_db, auth_admin):
        mock_db.session.get.return_value = None
        resp = auth_admin.post(f"{SLA}/set/999", json={})
        json_fail(resp, 404)

    def test_non_admin_forbidden(self, auth_user):
        resp = auth_user.post(f"{SLA}/set/1", json={})
        json_fail(resp, 403)

    @patch("app.routes.api.sla_api.assign_sla")
    @patch("app.routes.api.sla_api.db")
    def test_invalid_priority_ignored(self, mock_db, mock_assign, auth_admin):
        sample = MagicMock()
        sample.id = 1
        sample.sla_hours = 48
        sample.due_date = None
        sample.priority = "normal"
        mock_db.session.get.return_value = sample

        resp = auth_admin.post(
            f"{SLA}/set/1",
            json={"priority": "invalid_priority"},
        )
        body = resp.get_json()
        assert body["success"] is True
        # priority stays unchanged since "invalid_priority" not in allowed set
        assert sample.priority == "normal"


class TestSLADefaults:
    @patch("app.services.sla_service.DEFAULT_SLA_HOURS", {"coal": 48, "water": 72})
    @patch("app.services.sla_service.DEFAULT_SLA_FALLBACK", 48)
    def test_success(self, auth_admin):
        resp = auth_admin.get(f"{SLA}/defaults")
        data = json_ok(resp)
        assert "defaults" in data
        assert "fallback" in data
