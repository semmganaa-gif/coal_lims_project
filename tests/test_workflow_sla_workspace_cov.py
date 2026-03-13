# tests/test_workflow_sla_workspace_cov.py
# -*- coding: utf-8 -*-
"""
Coverage tests for:
  1. app/services/workflow_engine.py
  2. app/services/sla_service.py
  3. app/routes/analysis/workspace.py
  4. app/services/analytics_service.py
  5. app/labs/water_lab/chemistry/utils.py
"""

import json
import uuid
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock, PropertyMock

import pytest

from app.models import User, Sample, AnalysisResult, AnalysisType


# =====================================================================
# 1. WORKFLOW ENGINE TESTS
# =====================================================================

class TestTransitionResult:
    """Test TransitionResult dataclass."""

    def test_default_values(self, app):
        from app.services.workflow_engine import TransitionResult
        tr = TransitionResult(allowed=True)
        assert tr.allowed is True
        assert tr.reason == ""
        assert tr.transition == {}

    def test_with_reason(self, app):
        from app.services.workflow_engine import TransitionResult
        tr = TransitionResult(allowed=False, reason="test reason")
        assert tr.allowed is False
        assert tr.reason == "test reason"


class TestWorkflowEngine:
    """Test WorkflowEngine class."""

    def test_load_default_analysis_result_config(self, app):
        with app.app_context():
            from app.services.workflow_engine import WorkflowEngine
            engine = WorkflowEngine("analysis_result")
            config = engine.config
            assert config["name"] == "analysis_result"
            assert "pending_review" in config["states"]
            assert "approved" in config["states"]

    def test_load_default_sample_config(self, app):
        with app.app_context():
            from app.services.workflow_engine import WorkflowEngine
            engine = WorkflowEngine("sample")
            config = engine.config
            assert config["name"] == "sample"
            assert "new" in config["states"]
            assert "completed" in config["states"]

    def test_unknown_workflow_raises(self, app):
        with app.app_context():
            from app.services.workflow_engine import WorkflowEngine
            engine = WorkflowEngine("nonexistent_workflow")
            with pytest.raises(ValueError, match="Unknown workflow"):
                _ = engine.config

    def test_load_from_db_valid_json(self, app, db):
        """When a SystemSetting exists with valid JSON, use it."""
        with app.app_context():
            from app.services.workflow_engine import WorkflowEngine
            from app.models.settings import SystemSetting

            custom_config = {
                "name": "analysis_result",
                "states": {"draft": {"label": "Draft", "order": 1}},
                "initial_state": "draft",
                "transitions": [],
            }
            setting = SystemSetting(
                category="workflow",
                key="analysis_result",
                value=json.dumps(custom_config),
                is_active=True,
            )
            db.session.add(setting)
            db.session.commit()

            engine = WorkflowEngine("analysis_result")
            config = engine.config
            assert "draft" in config["states"]

            # Cleanup
            db.session.delete(setting)
            db.session.commit()

    def test_load_from_db_invalid_json_falls_back(self, app, db):
        """Invalid JSON in DB falls back to default."""
        with app.app_context():
            from app.services.workflow_engine import WorkflowEngine
            from app.models.settings import SystemSetting

            setting = SystemSetting(
                category="workflow",
                key="analysis_result",
                value="NOT VALID JSON {{{",
                is_active=True,
            )
            db.session.add(setting)
            db.session.commit()

            engine = WorkflowEngine("analysis_result")
            config = engine.config
            assert config["name"] == "analysis_result"  # default

            db.session.delete(setting)
            db.session.commit()

    def test_reload_clears_cache(self, app):
        with app.app_context():
            from app.services.workflow_engine import WorkflowEngine
            engine = WorkflowEngine("analysis_result")
            _ = engine.config  # cache it
            assert engine._config is not None
            engine.reload()
            assert engine._config is None

    def test_get_states(self, app):
        with app.app_context():
            from app.services.workflow_engine import WorkflowEngine
            engine = WorkflowEngine("analysis_result")
            states = engine.get_states()
            assert "pending_review" in states
            assert "approved" in states
            assert "rejected" in states
            assert "reanalysis" in states

    def test_get_state_info(self, app):
        with app.app_context():
            from app.services.workflow_engine import WorkflowEngine
            engine = WorkflowEngine("analysis_result")
            info = engine.get_state_info("approved")
            assert info is not None
            assert "color" in info
            assert info["order"] == 2

    def test_get_state_info_nonexistent(self, app):
        with app.app_context():
            from app.services.workflow_engine import WorkflowEngine
            engine = WorkflowEngine("analysis_result")
            assert engine.get_state_info("nonexistent") is None

    def test_get_initial_state(self, app):
        with app.app_context():
            from app.services.workflow_engine import WorkflowEngine
            engine = WorkflowEngine("analysis_result")
            assert engine.get_initial_state() == "pending_review"

    def test_get_final_states(self, app):
        with app.app_context():
            from app.services.workflow_engine import WorkflowEngine
            engine = WorkflowEngine("analysis_result")
            assert "approved" in engine.get_final_states()

    def test_is_final_state(self, app):
        with app.app_context():
            from app.services.workflow_engine import WorkflowEngine
            engine = WorkflowEngine("analysis_result")
            assert engine.is_final_state("approved") is True
            assert engine.is_final_state("pending_review") is False

    def test_get_transitions_all(self, app):
        with app.app_context():
            from app.services.workflow_engine import WorkflowEngine
            engine = WorkflowEngine("analysis_result")
            transitions = engine.get_transitions()
            assert len(transitions) > 0

    def test_get_transitions_filtered(self, app):
        with app.app_context():
            from app.services.workflow_engine import WorkflowEngine
            engine = WorkflowEngine("analysis_result")
            transitions = engine.get_transitions(from_state="pending_review")
            assert all(t["from"] == "pending_review" for t in transitions)
            assert len(transitions) >= 2  # approved, rejected, reanalysis

    def test_get_available_transitions(self, app):
        with app.app_context():
            from app.services.workflow_engine import WorkflowEngine
            engine = WorkflowEngine("analysis_result")
            transitions = engine.get_available_transitions("pending_review", "admin")
            assert len(transitions) >= 2
            # analyst cannot transition from pending_review in analysis_result
            transitions_analyst = engine.get_available_transitions("pending_review", "analyst")
            assert len(transitions_analyst) == 0

    def test_can_transition_allowed(self, app):
        with app.app_context():
            from app.services.workflow_engine import WorkflowEngine
            engine = WorkflowEngine("analysis_result")
            result = engine.can_transition("pending_review", "approved", user_role="admin")
            assert result.allowed is True

    def test_can_transition_undefined(self, app):
        with app.app_context():
            from app.services.workflow_engine import WorkflowEngine
            engine = WorkflowEngine("analysis_result")
            result = engine.can_transition("approved", "rejected")
            assert result.allowed is False
            assert "тодорхойлогдоогүй" in result.reason

    def test_can_transition_role_denied(self, app):
        with app.app_context():
            from app.services.workflow_engine import WorkflowEngine
            engine = WorkflowEngine("analysis_result")
            result = engine.can_transition("pending_review", "approved", user_role="analyst")
            assert result.allowed is False
            assert "эрх" in result.reason

    def test_can_transition_require_comment_missing(self, app):
        with app.app_context():
            from app.services.workflow_engine import WorkflowEngine
            engine = WorkflowEngine("analysis_result")
            result = engine.can_transition(
                "pending_review", "rejected",
                user_role="admin",
                context={}
            )
            assert result.allowed is False
            assert "Тайлбар" in result.reason

    def test_can_transition_require_comment_provided(self, app):
        with app.app_context():
            from app.services.workflow_engine import WorkflowEngine
            engine = WorkflowEngine("analysis_result")
            result = engine.can_transition(
                "pending_review", "rejected",
                user_role="admin",
                context={"comment": "Not good enough"}
            )
            assert result.allowed is True

    def test_evaluate_condition_all_results_approved(self, app):
        with app.app_context():
            from app.services.workflow_engine import WorkflowEngine
            engine = WorkflowEngine("sample")
            # analysis -> completed requires all_results_approved
            result = engine.can_transition(
                "analysis", "completed",
                user_role="admin",
                context={"all_results_approved": False}
            )
            assert result.allowed is False

            result = engine.can_transition(
                "analysis", "completed",
                user_role="admin",
                context={"all_results_approved": True}
            )
            assert result.allowed is True

    def test_evaluate_condition_require_reanalysis_reason(self, app):
        with app.app_context():
            from app.services.workflow_engine import WorkflowEngine
            engine = WorkflowEngine("analysis_result")
            ok, msg = engine._evaluate_condition("require_reanalysis_reason", {})
            assert ok is False
            ok, msg = engine._evaluate_condition("require_reanalysis_reason", {"reanalysis_reason": "Bad sample"})
            assert ok is True

    def test_evaluate_condition_min_results(self, app):
        with app.app_context():
            from app.services.workflow_engine import WorkflowEngine
            engine = WorkflowEngine("analysis_result")
            ok, msg = engine._evaluate_condition("min_results:3", {"result_count": 2})
            assert ok is False
            assert "3" in msg
            ok, msg = engine._evaluate_condition("min_results:3", {"result_count": 5})
            assert ok is True

    def test_evaluate_condition_min_results_bad_format(self, app):
        with app.app_context():
            from app.services.workflow_engine import WorkflowEngine
            engine = WorkflowEngine("analysis_result")
            # Bad format defaults to min_count=1
            ok, msg = engine._evaluate_condition("min_results:", {"result_count": 0})
            assert ok is False
            ok, msg = engine._evaluate_condition("min_results:", {"result_count": 1})
            assert ok is True

    def test_evaluate_condition_unknown(self, app):
        with app.app_context():
            from app.services.workflow_engine import WorkflowEngine
            engine = WorkflowEngine("analysis_result")
            ok, msg = engine._evaluate_condition("some_unknown_condition", {})
            assert ok is True  # unknown conditions pass by default

    def test_get_hooks(self, app):
        with app.app_context():
            from app.services.workflow_engine import WorkflowEngine
            engine = WorkflowEngine("analysis_result")
            hooks = engine.get_hooks("approved")
            assert "invalidate_cache" in hooks
            assert "log_audit" in hooks

    def test_get_hooks_no_match(self, app):
        with app.app_context():
            from app.services.workflow_engine import WorkflowEngine
            engine = WorkflowEngine("analysis_result")
            hooks = engine.get_hooks("nonexistent_state")
            assert hooks == []

    def test_can_transition_no_role(self, app):
        """When user_role is None, role check is skipped."""
        with app.app_context():
            from app.services.workflow_engine import WorkflowEngine
            engine = WorkflowEngine("analysis_result")
            result = engine.can_transition("pending_review", "approved", user_role=None)
            assert result.allowed is True


class TestWorkflowConfigFunctions:
    """Test module-level config management functions."""

    def test_get_workflow_config(self, app):
        with app.app_context():
            from app.services.workflow_engine import get_workflow_config
            config = get_workflow_config("analysis_result")
            assert config["name"] == "analysis_result"

    def test_save_workflow_config_missing_fields(self, app):
        with app.app_context():
            from app.services.workflow_engine import save_workflow_config
            with pytest.raises(ValueError, match="шаардлагатай"):
                save_workflow_config("test", {"name": "test"})

    def test_save_workflow_config_invalid_initial_state(self, app):
        with app.app_context():
            from app.services.workflow_engine import save_workflow_config
            config = {
                "name": "test",
                "states": {"a": {}},
                "initial_state": "nonexistent",
                "transitions": [],
            }
            with pytest.raises(ValueError, match="initial_state"):
                save_workflow_config("test", config)

    def test_save_workflow_config_invalid_transition_from(self, app):
        with app.app_context():
            from app.services.workflow_engine import save_workflow_config
            config = {
                "name": "test",
                "states": {"a": {}, "b": {}},
                "initial_state": "a",
                "transitions": [{"from": "nonexistent", "to": "b"}],
            }
            with pytest.raises(ValueError, match="'from' state"):
                save_workflow_config("test", config)

    def test_save_workflow_config_invalid_transition_to(self, app):
        with app.app_context():
            from app.services.workflow_engine import save_workflow_config
            config = {
                "name": "test",
                "states": {"a": {}, "b": {}},
                "initial_state": "a",
                "transitions": [{"from": "a", "to": "nonexistent"}],
            }
            with pytest.raises(ValueError, match="'to' state"):
                save_workflow_config("test", config)

    def test_save_and_load_workflow_config(self, app, db):
        with app.app_context():
            from app.services.workflow_engine import save_workflow_config, get_workflow_config
            from app.models.settings import SystemSetting

            config = {
                "name": "test_wf",
                "description": "Test workflow",
                "states": {"s1": {"label": "S1"}, "s2": {"label": "S2"}},
                "initial_state": "s1",
                "transitions": [{"from": "s1", "to": "s2"}],
            }
            result = save_workflow_config("test_wf", config, user_id=1)
            assert result is True

            # Update existing
            config["description"] = "Updated"
            result = save_workflow_config("test_wf", config, user_id=1)
            assert result is True

            # Cleanup
            setting = SystemSetting.query.filter_by(category="workflow", key="test_wf").first()
            if setting:
                db.session.delete(setting)
                db.session.commit()

    def test_reset_workflow_config(self, app, db):
        with app.app_context():
            from app.services.workflow_engine import save_workflow_config, reset_workflow_config
            from app.models.settings import SystemSetting

            config = {
                "name": "reset_test",
                "states": {"a": {}},
                "initial_state": "a",
                "transitions": [],
            }
            save_workflow_config("reset_test", config)
            result = reset_workflow_config("reset_test")
            assert result is True

            setting = SystemSetting.query.filter_by(category="workflow", key="reset_test").first()
            assert setting.is_active is False

            # Cleanup
            db.session.delete(setting)
            db.session.commit()

    def test_reset_nonexistent_config(self, app):
        with app.app_context():
            from app.services.workflow_engine import reset_workflow_config
            result = reset_workflow_config("totally_nonexistent_12345")
            assert result is True

    def test_list_workflows(self, app):
        with app.app_context():
            from app.services.workflow_engine import list_workflows
            workflows = list_workflows()
            assert len(workflows) >= 2
            names = [w["name"] for w in workflows]
            assert "analysis_result" in names
            assert "sample" in names
            for w in workflows:
                assert "state_count" in w
                assert "transition_count" in w


# =====================================================================
# 2. SLA SERVICE TESTS
# =====================================================================

class TestSLAService:
    """Test SLA service functions."""

    def test_get_default_sla_hours_known_client(self, app):
        with app.app_context():
            from app.services.sla_service import get_default_sla_hours
            assert get_default_sla_hours("CHPP") == 72
            assert get_default_sla_hours("QC") == 48
            assert get_default_sla_hours("UHG-Geo") == 120

    def test_get_default_sla_hours_unknown_client(self, app):
        with app.app_context():
            from app.services.sla_service import get_default_sla_hours
            assert get_default_sla_hours("UnknownClient") == 72  # DEFAULT_SLA_FALLBACK

    def test_assign_sla_no_received_date(self, app):
        with app.app_context():
            from app.services.sla_service import assign_sla
            sample = MagicMock()
            sample.received_date = None
            assign_sla(sample)
            # Should not set due_date

    def test_assign_sla_sets_due_date(self, app):
        with app.app_context():
            from app.services.sla_service import assign_sla
            sample = MagicMock()
            sample.received_date = datetime(2026, 1, 1, 8, 0)
            sample.sla_hours = None
            sample.client_name = "CHPP"
            assign_sla(sample)
            assert sample.sla_hours == 72
            assert sample.due_date == datetime(2026, 1, 1, 8, 0) + timedelta(hours=72)

    def test_assign_sla_preserves_existing_sla_hours(self, app):
        with app.app_context():
            from app.services.sla_service import assign_sla
            sample = MagicMock()
            sample.received_date = datetime(2026, 1, 1, 8, 0)
            sample.sla_hours = 24  # already set
            sample.client_name = "CHPP"
            assign_sla(sample)
            assert sample.sla_hours == 24  # unchanged
            assert sample.due_date == datetime(2026, 1, 1, 8, 0) + timedelta(hours=24)

    def test_mark_completed(self, app):
        from app.services.sla_service import mark_completed
        sample = MagicMock()
        with patch("app.services.sla_service.now_local", return_value=datetime(2026, 3, 1, 12, 0)):
            mark_completed(sample)
        assert sample.completed_at == datetime(2026, 3, 1, 12, 0)

    def test_sla_summary_dataclass(self, app):
        from app.services.sla_service import SLASummary
        s = SLASummary()
        assert s.overdue == 0
        assert s.avg_turnaround_hours == 0.0

    def test_overdue_sample_dataclass(self, app):
        from app.services.sla_service import OverdueSample
        o = OverdueSample(
            id=1, sample_code="S-001", client_name="CHPP",
            lab_type="coal", received_date="2026-01-01",
            due_date="2026-01-04", overdue_hours=12.5,
            priority="high", pending_analyses=3,
        )
        assert o.sample_code == "S-001"
        assert o.overdue_hours == 12.5

    def test_get_sla_summary(self, app, db):
        """Test SLA summary with real DB queries."""
        with app.app_context():
            from app.services.sla_service import get_sla_summary
            summary = get_sla_summary("coal")
            assert isinstance(summary.overdue, int)
            assert isinstance(summary.on_track, int)

    def test_get_overdue_samples_empty(self, app, db):
        with app.app_context():
            from app.services.sla_service import get_overdue_samples
            result = get_overdue_samples("coal")
            assert isinstance(result, list)

    def test_get_due_soon_samples_empty(self, app, db):
        with app.app_context():
            from app.services.sla_service import get_due_soon_samples
            result = get_due_soon_samples("coal", hours=24)
            assert isinstance(result, list)

    def test_bulk_assign_sla_no_samples(self, app, db):
        with app.app_context():
            from app.services.sla_service import bulk_assign_sla
            count = bulk_assign_sla("coal")
            assert count >= 0

    def test_get_sla_summary_with_data(self, app, db):
        """Test SLA summary with actual sample data."""
        with app.app_context():
            from app.services.sla_service import get_sla_summary
            now = datetime.utcnow()

            user = User.query.filter_by(username="chemist").first()
            # Create overdue, due soon, and on-track samples
            samples = []
            s_overdue = Sample(
                sample_code=f"SLA-OD-{uuid.uuid4().hex[:6]}",
                user_id=user.id, lab_type="coal", status="new",
                client_name="CHPP",
                received_date=now - timedelta(days=10),
                due_date=now - timedelta(hours=5),
            )
            samples.append(s_overdue)

            s_soon = Sample(
                sample_code=f"SLA-DS-{uuid.uuid4().hex[:6]}",
                user_id=user.id, lab_type="coal", status="new",
                client_name="CHPP",
                received_date=now - timedelta(days=1),
                due_date=now + timedelta(hours=12),
            )
            samples.append(s_soon)

            s_ok = Sample(
                sample_code=f"SLA-OK-{uuid.uuid4().hex[:6]}",
                user_id=user.id, lab_type="coal", status="new",
                client_name="QC",
                received_date=now - timedelta(hours=2),
                due_date=now + timedelta(hours=48),
            )
            samples.append(s_ok)

            s_no_sla = Sample(
                sample_code=f"SLA-NO-{uuid.uuid4().hex[:6]}",
                user_id=user.id, lab_type="coal", status="new",
                client_name="QC",
            )
            samples.append(s_no_sla)

            # Completed sample for turnaround stats
            s_done = Sample(
                sample_code=f"SLA-DN-{uuid.uuid4().hex[:6]}",
                user_id=user.id, lab_type="coal", status="completed",
                client_name="CHPP",
                received_date=now - timedelta(days=2),
                completed_at=now - timedelta(hours=1),
                due_date=now + timedelta(hours=10),
            )
            samples.append(s_done)

            for s in samples:
                db.session.add(s)
            db.session.commit()

            summary = get_sla_summary("coal")
            assert summary.overdue >= 1
            assert summary.due_soon >= 1
            assert summary.on_track >= 1
            assert summary.no_sla >= 1

            # Cleanup
            for s in samples:
                db.session.delete(s)
            db.session.commit()

    def test_get_overdue_samples_with_data(self, app, db):
        with app.app_context():
            from app.services.sla_service import get_overdue_samples
            # Use naive datetimes (SQLite stores naive)
            now = datetime.utcnow()
            user = User.query.filter_by(username="chemist").first()

            s = Sample(
                sample_code=f"OD-{uuid.uuid4().hex[:6]}",
                user_id=user.id, lab_type="coal", status="new",
                client_name="CHPP",
                received_date=now - timedelta(days=5),
                due_date=now - timedelta(hours=10),
            )
            db.session.add(s)
            db.session.commit()

            # Mock now_local to return naive datetime (matching SQLite)
            with patch("app.services.sla_service.now_local", return_value=now):
                result = get_overdue_samples("coal")
            assert len(result) >= 1
            overdue = [r for r in result if r.sample_code == s.sample_code]
            assert len(overdue) == 1
            assert overdue[0].overdue_hours > 0

            db.session.delete(s)
            db.session.commit()

    def test_bulk_assign_sla_with_data(self, app, db):
        with app.app_context():
            from app.services.sla_service import bulk_assign_sla
            now = datetime.utcnow()
            user = User.query.filter_by(username="chemist").first()

            s = Sample(
                sample_code=f"BULK-{uuid.uuid4().hex[:6]}",
                user_id=user.id, lab_type="coal", status="new",
                client_name="CHPP",
                received_date=now - timedelta(days=1),
                due_date=None,
            )
            db.session.add(s)
            db.session.commit()

            count = bulk_assign_sla("coal")
            assert count >= 1

            # Verify due_date was set
            db.session.refresh(s)
            assert s.due_date is not None

            db.session.delete(s)
            db.session.commit()


# =====================================================================
# 3. WORKSPACE ROUTE TESTS
# =====================================================================

class TestWorkspaceRoutes:
    """Test analysis workspace routes."""

    def test_analysis_hub_requires_login(self, client):
        resp = client.get("/analysis_hub")
        assert resp.status_code in (302, 401)

    def test_analysis_hub_logged_in_admin(self, app, db, client):
        with app.app_context():
            client.post("/login", data={"username": "admin", "password": "TestPass123"})
            resp = client.get("/analysis_hub")
            # May redirect or render depending on role decorator
            assert resp.status_code in (200, 302)

    def test_analysis_hub_logged_in_senior(self, app, db, client):
        with app.app_context():
            client.post("/login", data={"username": "senior", "password": "TestPass123"})
            resp = client.get("/analysis_hub")
            assert resp.status_code in (200, 302)

    def test_analysis_page_requires_login(self, client):
        resp = client.get("/analysis_page/Mad")
        assert resp.status_code in (302, 401)

    def test_analysis_page_mg_redirect(self, app, client):
        """MG_ONLY codes redirect to WTL_MG page."""
        with app.app_context():
            client.post("/login", data={"username": "admin", "password": "TestPass123"})
            resp = client.get("/analysis_page/MG")
            assert resp.status_code == 302
            assert "WTL_MG" in resp.headers.get("Location", "")

    def test_analysis_page_wtl_mg_code_renders(self, app, client):
        """WTL_MG code redirects to wtl_mg_page which renders."""
        with app.app_context():
            client.post("/login", data={"username": "admin", "password": "TestPass123"})
            resp = client.get("/analysis_page/WTL_MG")
            # May render directly (302 redirect followed) or render 200
            assert resp.status_code in (200, 302)

    def test_analysis_page_valid_code(self, app, db, client):
        """Test analysis page with a valid analysis code."""
        with app.app_context():
            # Ensure we have an AnalysisType for Mad
            at = AnalysisType.query.filter_by(code="Mad").first()
            if not at:
                at = AnalysisType(code="Mad", name="Moisture (Mad)", required_role="chemist")
                db.session.add(at)
                db.session.commit()

            client.post("/login", data={"username": "admin", "password": "TestPass123"})
            resp = client.get("/analysis_page/Mad")
            assert resp.status_code == 200

    def test_analysis_page_with_sample_ids(self, app, db, client):
        """Test analysis page with sample_ids parameter."""
        with app.app_context():
            at = AnalysisType.query.filter_by(code="Mad").first()
            if not at:
                at = AnalysisType(code="Mad", name="Moisture (Mad)", required_role="chemist")
                db.session.add(at)
                db.session.commit()

            user = User.query.filter_by(username="admin").first()
            s = Sample(
                sample_code=f"WS-{uuid.uuid4().hex[:6]}",
                user_id=user.id,
                client_name="CHPP",
            )
            db.session.add(s)
            db.session.commit()

            client.post("/login", data={"username": "admin", "password": "TestPass123"})
            resp = client.get(f"/analysis_page/Mad?sample_ids={s.id}")
            assert resp.status_code == 200

            db.session.delete(s)
            db.session.commit()

    def test_analysis_page_sulfur(self, app, db, client):
        """Test analysis page for sulfur (TS/St,ad)."""
        with app.app_context():
            at = AnalysisType.query.filter_by(code="St,ad").first()
            if not at:
                at = AnalysisType(code="St,ad", name="Total Sulfur", required_role="chemist")
                db.session.add(at)
                db.session.commit()

            client.post("/login", data={"username": "admin", "password": "TestPass123"})
            resp = client.get("/analysis_page/St,ad")
            assert resp.status_code == 200

    def test_analysis_page_vad_with_mad_lookup(self, app, db, client):
        """Test Vad page which looks up Mad results."""
        with app.app_context():
            at = AnalysisType.query.filter_by(code="Vad").first()
            if not at:
                at = AnalysisType(code="Vad", name="Volatile Matter", required_role="chemist")
                db.session.add(at)
                db.session.commit()

            client.post("/login", data={"username": "admin", "password": "TestPass123"})
            resp = client.get("/analysis_page/Vad")
            assert resp.status_code == 200

    def test_analysis_page_xy_paired(self, app, db, client):
        """Test X/Y paired analysis page."""
        with app.app_context():
            at = AnalysisType.query.filter_by(code="X").first()
            if not at:
                at = AnalysisType(code="X", name="X", required_role="chemist")
                db.session.add(at)
                db.session.commit()

            user = User.query.filter_by(username="admin").first()
            s = Sample(
                sample_code=f"XY-{uuid.uuid4().hex[:6]}",
                user_id=user.id, client_name="CHPP",
            )
            db.session.add(s)
            db.session.commit()

            client.post("/login", data={"username": "admin", "password": "TestPass123"})
            resp = client.get(f"/analysis_page/X?sample_ids={s.id}")
            assert resp.status_code == 200

            db.session.delete(s)
            db.session.commit()

    def test_analysis_page_nonexistent_code(self, app, db, client):
        """Test analysis page with nonexistent code."""
        with app.app_context():
            client.post("/login", data={"username": "admin", "password": "TestPass123"})
            resp = client.get("/analysis_page/NONEXISTENT_CODE_XYZ")
            assert resp.status_code == 404

    def test_wtl_mg_page_requires_login(self, client):
        resp = client.get("/analysis_page/WTL_MG")
        assert resp.status_code in (302, 401)

    def test_analysis_page_gi_retest(self, app, db, client):
        """Test Gi analysis page with retest logic."""
        with app.app_context():
            at = AnalysisType.query.filter_by(code="Gi").first()
            if not at:
                at = AnalysisType(code="Gi", name="Gi Index", required_role="chemist")
                db.session.add(at)
                db.session.commit()

            user = User.query.filter_by(username="admin").first()
            s = Sample(
                sample_code=f"GI-{uuid.uuid4().hex[:6]}",
                user_id=user.id, client_name="CHPP",
            )
            db.session.add(s)
            db.session.commit()

            # Create a rejected result with GI_RETEST_3_3
            ar = AnalysisResult(
                sample_id=s.id, analysis_code="Gi",
                user_id=user.id, status="rejected",
                rejection_category="GI_RETEST_3_3",
            )
            db.session.add(ar)
            db.session.commit()

            client.post("/login", data={"username": "admin", "password": "TestPass123"})
            resp = client.get(f"/analysis_page/Gi?sample_ids={s.id}")
            assert resp.status_code == 200

            db.session.delete(ar)
            db.session.delete(s)
            db.session.commit()

    def test_analysis_page_cv_sulfur_map(self, app, db, client):
        """Test CV page which loads sulfur map."""
        with app.app_context():
            at = AnalysisType.query.filter_by(code="CV").first()
            if not at:
                at = AnalysisType(code="CV", name="Calorific Value", required_role="chemist")
                db.session.add(at)
                db.session.commit()

            client.post("/login", data={"username": "admin", "password": "TestPass123"})
            resp = client.get("/analysis_page/CV")
            assert resp.status_code == 200


# =====================================================================
# 4. ANALYTICS SERVICE TESTS
# =====================================================================

class TestAnalyticsHelpers:
    """Test analytics helper functions (no DB needed)."""

    def test_linear_regression_basic(self, app):
        from app.services.analytics_service import _linear_regression
        xs = [0, 1, 2, 3, 4]
        ys = [2, 4, 6, 8, 10]
        slope, intercept, r_sq = _linear_regression(xs, ys)
        assert abs(slope - 2.0) < 0.001
        assert abs(intercept - 2.0) < 0.001
        assert abs(r_sq - 1.0) < 0.001

    def test_linear_regression_single_point(self, app):
        from app.services.analytics_service import _linear_regression
        slope, intercept, r_sq = _linear_regression([1], [5])
        assert slope == 0
        assert r_sq == 0

    def test_linear_regression_constant_x(self, app):
        from app.services.analytics_service import _linear_regression
        xs = [5, 5, 5]
        ys = [1, 2, 3]
        slope, intercept, r_sq = _linear_regression(xs, ys)
        assert slope == 0  # ss_xx == 0

    def test_linear_regression_constant_y(self, app):
        from app.services.analytics_service import _linear_regression
        xs = [1, 2, 3]
        ys = [5, 5, 5]
        slope, intercept, r_sq = _linear_regression(xs, ys)
        assert abs(slope) < 0.001
        assert r_sq == 0  # ss_yy == 0

    def test_score_to_grade(self, app):
        from app.services.analytics_service import _score_to_grade
        assert _score_to_grade(100) == ("A+", "#22c55e")
        assert _score_to_grade(95) == ("A+", "#22c55e")
        assert _score_to_grade(90) == ("A", "#22c55e")
        assert _score_to_grade(80) == ("B", "#84cc16")
        assert _score_to_grade(70) == ("C", "#f59e0b")
        assert _score_to_grade(50) == ("D", "#f97316")
        assert _score_to_grade(30) == ("F", "#ef4444")

    def test_quality_message(self, app):
        from app.services.analytics_service import _quality_message
        msg = _quality_message(95, "A+", 0, 0)
        assert "Маш сайн" in msg

        msg = _quality_message(80, "B", 0, 0)
        assert "Сайн" in msg

        msg = _quality_message(65, "C", 0, 0)
        assert "Дунд" in msg

        msg = _quality_message(30, "F", 2, 3)
        assert "Анхааруулга" in msg
        assert "2 ноцтой" in msg

    def test_trend_message_stable(self, app):
        from app.services.analytics_service import _trend_message
        msg = _trend_message("Test", "stable", 1.5, "high")
        assert "Тогтвортой" in msg

    def test_trend_message_increasing(self, app):
        from app.services.analytics_service import _trend_message
        msg = _trend_message("Test", "increasing", 5.0, "high")
        assert "өсөж" in msg

    def test_trend_message_decreasing(self, app):
        from app.services.analytics_service import _trend_message
        msg = _trend_message("Test", "decreasing", -3.0, "medium")
        assert "буурч" in msg

    def test_get_recommendation_high_z_mad(self, app):
        from app.services.analytics_service import _get_recommendation
        rec = _get_recommendation("Mad", 4.0, 15.0, {"mean": 5.0, "sd": 2.5})
        assert "чийг" in rec.lower() or "хатаалт" in rec.lower()

    def test_get_recommendation_high_z_aad(self, app):
        from app.services.analytics_service import _get_recommendation
        rec = _get_recommendation("Aad", 4.0, 50.0, {"mean": 20.0, "sd": 7.0})
        assert "температур" in rec.lower() or "зуух" in rec.lower()

    def test_get_recommendation_high_z_vdaf(self, app):
        from app.services.analytics_service import _get_recommendation
        rec = _get_recommendation("Vdaf", 4.0, 55.0, {"mean": 35.0, "sd": 5.0})
        assert "температур" in rec.lower() or "900" in rec

    def test_get_recommendation_high_z_std(self, app):
        from app.services.analytics_service import _get_recommendation
        rec = _get_recommendation("St,d", 4.0, 5.0, {"mean": 1.0, "sd": 1.0})
        assert "калибр" in rec.lower() or "хүхр" in rec.lower()

    def test_get_recommendation_high_z_cv(self, app):
        from app.services.analytics_service import _get_recommendation
        rec = _get_recommendation("Qgr,ad", 4.0, 9000, {"mean": 5000, "sd": 1000})
        assert "калориметр" in rec.lower() or "калибр" in rec.lower()

    def test_get_recommendation_high_z_unknown(self, app):
        from app.services.analytics_service import _get_recommendation
        rec = _get_recommendation("UNKNOWN", 4.0, 99, {"mean": 50, "sd": 10})
        assert "шинжилгээ" in rec.lower() or "калибр" in rec.lower()

    def test_get_recommendation_moderate_z_mad(self, app):
        from app.services.analytics_service import _get_recommendation
        rec = _get_recommendation("Mad", 2.5, 10.0, {"mean": 5.0, "sd": 2.0})
        assert "хадгалалт" in rec.lower()

    def test_get_recommendation_moderate_z_other(self, app):
        from app.services.analytics_service import _get_recommendation
        rec = _get_recommendation("Aad", 2.5, 30.0, {"mean": 20.0, "sd": 4.0})
        assert "хянах" in rec.lower()

    def test_anomaly_to_dict(self, app):
        from app.services.analytics_service import _anomaly_to_dict, Anomaly
        a = Anomaly(
            sample_code="S-1", analysis_code="Mad",
            value=15.0, z_score=3.5,
            historical_mean=5.0, historical_sd=2.8,
            severity="critical",
            message="Test message",
            recommendation="Test rec",
        )
        d = _anomaly_to_dict(a)
        assert d["sample_code"] == "S-1"
        assert d["severity"] == "critical"

    def test_trend_to_dict(self, app):
        from app.services.analytics_service import _trend_to_dict, TrendResult
        t = TrendResult(
            analysis_code="Mad", direction="increasing",
            slope=0.05, r_squared=0.8, change_pct=10.0,
            confidence="high", message="Test",
            recent_mean=6.0, historical_mean=5.5,
        )
        d = _trend_to_dict(t)
        assert d["direction"] == "increasing"
        assert d["r_squared"] == 0.8


class TestAnalyticsDB:
    """Test analytics functions that need DB context."""

    def test_get_historical_stats_no_data(self, app, db):
        with app.app_context():
            from app.services.analytics_service import get_historical_stats
            stats = get_historical_stats("Mad", days=1)
            # Might have data from other tests but should not error
            assert "count" in stats

    def test_get_historical_stats_with_client(self, app, db):
        with app.app_context():
            from app.services.analytics_service import get_historical_stats
            stats = get_historical_stats("Mad", days=90, client_name="NONEXISTENT")
            assert stats["count"] == 0

    def test_detect_anomalies_empty(self, app, db):
        with app.app_context():
            from app.services.analytics_service import detect_anomalies
            result = detect_anomalies([])
            assert result == []

    def test_detect_anomalies_with_sample(self, app, db):
        with app.app_context():
            from app.services.analytics_service import detect_anomalies
            user = User.query.filter_by(username="chemist").first()
            s = Sample(
                sample_code=f"ANOM-{uuid.uuid4().hex[:6]}",
                user_id=user.id, client_name="CHPP",
            )
            db.session.add(s)
            db.session.commit()

            # Add a result with extreme value
            ar = AnalysisResult(
                sample_id=s.id, analysis_code="Mad",
                user_id=user.id, status="approved",
                final_result=99.9,  # extreme
            )
            db.session.add(ar)
            db.session.commit()

            anomalies = detect_anomalies([s])
            # May or may not detect anomaly depending on historical data
            assert isinstance(anomalies, list)

            db.session.delete(ar)
            db.session.delete(s)
            db.session.commit()

    def test_analyze_trends_insufficient_data(self, app, db):
        with app.app_context():
            from app.services.analytics_service import analyze_trends
            result = analyze_trends("NONEXISTENT_CODE_XYZ", days=1)
            assert result.direction == "stable"
            assert result.confidence == "low"

    def test_calculate_quality_score_empty(self, app, db):
        with app.app_context():
            from app.services.analytics_service import calculate_quality_score
            qs = calculate_quality_score([])
            assert qs.score == 0
            assert qs.grade == "N/A"

    def test_calculate_quality_score_with_anomalies(self, app, db):
        with app.app_context():
            from app.services.analytics_service import calculate_quality_score, Anomaly
            user = User.query.filter_by(username="chemist").first()
            s = Sample(
                sample_code=f"QS-{uuid.uuid4().hex[:6]}",
                user_id=user.id, client_name="CHPP",
                received_date=datetime.utcnow() - timedelta(hours=2),
            )
            db.session.add(s)
            db.session.commit()

            ar = AnalysisResult(
                sample_id=s.id, analysis_code="Mad",
                user_id=user.id, status="approved",
                final_result=5.5,
                created_at=datetime.utcnow(),
            )
            db.session.add(ar)
            db.session.commit()

            anomalies = [
                Anomaly("S1", "Mad", 99, 4.0, 5, 2, "critical", "msg", "rec"),
                Anomaly("S1", "Aad", 50, 2.5, 20, 5, "warning", "msg", "rec"),
            ]

            qs = calculate_quality_score([s], anomalies=anomalies)
            assert 0 <= qs.score <= 100
            assert qs.grade in ("A+", "A", "B", "C", "D", "F")
            assert "accuracy" in qs.breakdown

            db.session.delete(ar)
            db.session.delete(s)
            db.session.commit()

    def test_generate_insights_empty(self, app, db):
        with app.app_context():
            from app.services.analytics_service import generate_insights
            insights = generate_insights([])
            assert len(insights) == 1
            assert "бүртгэгдээгүй" in insights[0]

    def test_generate_insights_with_samples(self, app, db):
        with app.app_context():
            from app.services.analytics_service import generate_insights
            user = User.query.filter_by(username="chemist").first()
            samples = []
            for i in range(3):
                s = Sample(
                    sample_code=f"INS-{uuid.uuid4().hex[:6]}",
                    user_id=user.id,
                    client_name="CHPP" if i < 2 else "QC",
                )
                db.session.add(s)
                samples.append(s)
            db.session.commit()

            insights = generate_insights(samples, anomalies=[], trends=None)
            assert any("3 дээж" in i for i in insights)
            assert any("CHPP" in i for i in insights)

            for s in samples:
                db.session.delete(s)
            db.session.commit()

    def test_generate_insights_with_anomalies(self, app, db):
        with app.app_context():
            from app.services.analytics_service import generate_insights, Anomaly, TrendResult
            user = User.query.filter_by(username="chemist").first()
            s = Sample(
                sample_code=f"INSA-{uuid.uuid4().hex[:6]}",
                user_id=user.id, client_name="CHPP",
            )
            db.session.add(s)
            db.session.commit()

            anomalies = [
                Anomaly("S1", "Mad", 99, 4.0, 5, 2, "critical", "msg", "rec"),
                Anomaly("S1", "Aad", 50, 2.5, 20, 5, "warning", "msg", "rec"),
                Anomaly("S1", "Vdaf", 55, 3.0, 35, 5, "critical", "msg", "rec"),
            ]
            trends = [
                TrendResult("Mad", "increasing", 0.05, 0.8, 10.0, "high", "msg", 6.0, 5.5),
                TrendResult("Aad", "decreasing", -0.03, 0.6, -5.0, "medium", "msg", 18.0, 19.0),
            ]

            insights = generate_insights([s], anomalies=anomalies, trends=trends)
            assert any("ноцтой" in i for i in insights)
            assert any("анхааруулга" in i.lower() for i in insights)
            # Multi-anomaly warning for S1 (3 anomalies)
            assert any("S1" in i for i in insights)
            # Trend insights
            assert any("Өсөх" in i for i in insights)
            assert any("Буурах" in i for i in insights)

            db.session.delete(s)
            db.session.commit()

    def test_compare_shifts(self, app, db):
        with app.app_context():
            from app.services.analytics_service import _compare_shifts
            result = _compare_shifts([])
            assert result == {}

    def test_compare_shifts_with_data(self, app, db):
        with app.app_context():
            from app.services.analytics_service import _compare_shifts
            user = User.query.filter_by(username="chemist").first()
            now = datetime.utcnow()

            # Day sample (hour=10)
            s_day = Sample(
                sample_code=f"SH-D-{uuid.uuid4().hex[:6]}",
                user_id=user.id, client_name="CHPP",
                received_date=now.replace(hour=10),
            )
            # Night sample (hour=22)
            s_night = Sample(
                sample_code=f"SH-N-{uuid.uuid4().hex[:6]}",
                user_id=user.id, client_name="CHPP",
                received_date=now.replace(hour=22),
            )
            db.session.add_all([s_day, s_night])
            db.session.commit()

            ar_day = AnalysisResult(
                sample_id=s_day.id, analysis_code="Mad",
                user_id=user.id, status="approved", final_result=5.5,
            )
            ar_night = AnalysisResult(
                sample_id=s_night.id, analysis_code="Mad",
                user_id=user.id, status="approved", final_result=6.0,
            )
            db.session.add_all([ar_day, ar_night])
            db.session.commit()

            result = _compare_shifts([s_day, s_night])
            assert "Mad" in result
            assert result["Mad"]["day"]["count"] == 1
            assert result["Mad"]["night"]["count"] == 1

            db.session.delete(ar_day)
            db.session.delete(ar_night)
            db.session.delete(s_day)
            db.session.delete(s_night)
            db.session.commit()


# =====================================================================
# 5. WATER CHEMISTRY UTILS TESTS
# =====================================================================

class FormLike:
    """Helper to simulate Flask request.form for water chemistry tests."""
    def __init__(self, data):
        self._data = data
    def getlist(self, key):
        val = self._data.get(key, [])
        return val if isinstance(val, list) else [val]
    def get(self, key, default=None):
        return self._data.get(key, default)


def _mock_safe_commit(db_session):
    """Create a mock for safe_commit that does a real commit."""
    def _commit(*a, **kw):
        db_session.commit()
        return True
    return _commit


class TestWaterChemUtils:
    """Test water chemistry utility functions."""

    def test_water_codes_populated(self, app):
        from app.labs.water_lab.chemistry.utils import WATER_CODES
        assert len(WATER_CODES) > 0
        assert "PH" in WATER_CODES or "NH4" in WATER_CODES

    def test_micro_codes_populated(self, app):
        from app.labs.water_lab.chemistry.utils import MICRO_CODES
        assert len(MICRO_CODES) > 0
        assert "CFU" in MICRO_CODES

    def test_generate_micro_lab_id_new_day(self, app, db):
        """Test micro lab ID generation for a new day (no existing samples)."""
        with app.app_context():
            from app.labs.water_lab.chemistry.utils import _generate_micro_lab_id
            from datetime import date
            # Use a far-future date unlikely to have data
            future_date = date(2030, 12, 31)
            day_num, total = _generate_micro_lab_id(future_date)
            assert isinstance(day_num, int)
            assert day_num >= 1
            assert isinstance(total, int)

    def test_generate_micro_lab_id_next_batch(self, app, db):
        with app.app_context():
            from app.labs.water_lab.chemistry.utils import _generate_micro_lab_id
            from datetime import date
            future_date = date(2030, 12, 30)
            day_num, total = _generate_micro_lab_id(future_date, next_batch=True)
            assert isinstance(day_num, int)
            assert day_num >= 1

    def test_generate_micro_lab_id_with_existing_data(self, app, db):
        """Test micro lab ID when today already has samples."""
        with app.app_context():
            from app.labs.water_lab.chemistry.utils import _generate_micro_lab_id
            from datetime import date
            user = User.query.filter_by(username="chemist").first()
            test_date = date(2029, 6, 15)

            s = Sample(
                sample_code=f"MICRO-EXIST-{uuid.uuid4().hex[:6]}",
                user_id=user.id, lab_type="microbiology",
                sample_date=test_date,
                micro_lab_id="05_10",
            )
            db.session.add(s)
            db.session.commit()

            day_num, total = _generate_micro_lab_id(test_date)
            assert day_num == 5  # should use existing day_num

            # Next batch should be higher
            day_num_nb, _ = _generate_micro_lab_id(test_date, next_batch=True)
            assert day_num_nb >= 6

            db.session.delete(s)
            db.session.commit()

    def test_max_batch(self, app, db):
        with app.app_context():
            from app.labs.water_lab.chemistry.utils import _max_batch
            result = _max_batch()
            assert isinstance(result, int)
            assert result >= 0

    def test_max_batch_with_extra_filters(self, app, db):
        with app.app_context():
            from app.labs.water_lab.chemistry.utils import _max_batch
            from datetime import date
            result = _max_batch([Sample.sample_date == date(2030, 1, 1)])
            assert result == 0  # no data for that date

    def test_generate_chem_lab_id_new_day(self, app, db):
        with app.app_context():
            from app.labs.water_lab.chemistry.utils import _generate_chem_lab_id
            from datetime import date
            future_date = date(2030, 12, 31)
            batch, total = _generate_chem_lab_id(future_date)
            assert isinstance(batch, int)
            assert batch >= 1
            assert isinstance(total, int)

    def test_generate_chem_lab_id_next_batch(self, app, db):
        with app.app_context():
            from app.labs.water_lab.chemistry.utils import _generate_chem_lab_id
            from datetime import date
            future_date = date(2030, 12, 30)
            batch, total = _generate_chem_lab_id(future_date, next_batch=True)
            assert isinstance(batch, int)
            assert batch >= 1

    def test_generate_chem_lab_id_existing_today(self, app, db):
        with app.app_context():
            from app.labs.water_lab.chemistry.utils import _generate_chem_lab_id
            from datetime import date
            user = User.query.filter_by(username="chemist").first()
            test_date = date(2029, 7, 20)

            s = Sample(
                sample_code=f"CHEM-EXIST-{uuid.uuid4().hex[:6]}",
                user_id=user.id, lab_type="water",
                sample_date=test_date,
                chem_lab_id="03_05",
            )
            db.session.add(s)
            db.session.commit()

            batch, total = _generate_chem_lab_id(test_date)
            assert batch == 3  # should use existing batch

            db.session.delete(s)
            db.session.commit()

    def test_create_water_micro_samples_water_only(self, app, db):
        """Test creating water-only samples."""
        with app.app_context():
            from app.labs.water_lab.chemistry.utils import create_water_micro_samples
            user = User.query.filter_by(username="chemist").first()

            form = {
                "sample_codes": ["Test-Water-1"],
                "source_type": "busad",
                "sample_date": "2030-01-15",
                "analyses": ["PH", "EC"],
            }

            with patch("app.labs.water_lab.chemistry.utils.safe_commit", side_effect=_mock_safe_commit(db.session)):
                created, skipped, count = create_water_micro_samples(FormLike(form), user.id)
            assert len(created) == 1
            assert count == 2  # PH + EC

            # Cleanup
            s = Sample.query.filter(Sample.sample_code.like("%Test-Water-1%")).first()
            if s:
                db.session.delete(s)
                db.session.commit()

    def test_create_water_micro_samples_micro_only(self, app, db):
        with app.app_context():
            from app.labs.water_lab.chemistry.utils import create_water_micro_samples
            user = User.query.filter_by(username="chemist").first()

            form = {
                "sample_codes": ["Test-Micro-1"],
                "source_type": "busad",
                "sample_date": "2030-02-20",
                "analyses": ["CFU", "ECOLI"],
            }

            with patch("app.labs.water_lab.chemistry.utils.safe_commit", side_effect=_mock_safe_commit(db.session)):
                created, skipped, count = create_water_micro_samples(FormLike(form), user.id)
            assert len(created) == 1
            assert count == 2

            # Cleanup
            s = Sample.query.filter(Sample.sample_code.like("%Test-Micro-1%")).first()
            if s:
                db.session.delete(s)
                db.session.commit()

    def test_create_water_micro_samples_combined(self, app, db):
        with app.app_context():
            from app.labs.water_lab.chemistry.utils import create_water_micro_samples
            user = User.query.filter_by(username="chemist").first()

            form = {
                "sample_codes": ["Test-Combined-1"],
                "source_type": "busad",
                "sample_date": "2030-03-10",
                "analyses": ["PH", "CFU"],
                "volume_2l": "on",
                "volume_05l": "on",
                "return_sample": "on",
                "retention_period": "14",
            }

            with patch("app.labs.water_lab.chemistry.utils.safe_commit", side_effect=_mock_safe_commit(db.session)):
                created, skipped, count = create_water_micro_samples(FormLike(form), user.id)
            assert len(created) == 1
            assert count == 2

            # Verify sample attributes
            s = Sample.query.filter(Sample.sample_code.like("%Test-Combined-1%")).first()
            assert s is not None
            assert s.lab_type == "water & micro"
            assert s.weight == 2500.0
            assert s.return_sample is True

            db.session.delete(s)
            db.session.commit()

    def test_create_water_micro_samples_skip_duplicate(self, app, db):
        with app.app_context():
            from app.labs.water_lab.chemistry.utils import create_water_micro_samples
            user = User.query.filter_by(username="chemist").first()

            form_data = {
                "sample_codes": ["Test-Dup-1"],
                "source_type": "busad",
                "sample_date": "2030-04-15",
                "analyses": ["PH"],
            }

            with patch("app.labs.water_lab.chemistry.utils.safe_commit", side_effect=_mock_safe_commit(db.session)):
                # Create first time
                created1, _, _ = create_water_micro_samples(FormLike(form_data), user.id)
                assert len(created1) == 1

                # Create again - should skip
                created2, skipped2, _ = create_water_micro_samples(FormLike(form_data), user.id)
                assert len(created2) == 0
                assert len(skipped2) == 1

            # Cleanup
            s = Sample.query.filter(Sample.sample_code.like("%Test-Dup-1%")).first()
            if s:
                db.session.delete(s)
                db.session.commit()

    def test_create_water_micro_samples_empty_name(self, app, db):
        with app.app_context():
            from app.labs.water_lab.chemistry.utils import create_water_micro_samples
            user = User.query.filter_by(username="chemist").first()

            form = {
                "sample_codes": ["", "  "],
                "source_type": "busad",
                "sample_date": "2030-05-01",
                "analyses": ["PH"],
            }

            with patch("app.labs.water_lab.chemistry.utils.safe_commit", side_effect=_mock_safe_commit(db.session)):
                created, skipped, _ = create_water_micro_samples(FormLike(form), user.id)
            assert len(created) == 0

    def test_create_water_micro_samples_no_date(self, app, db):
        """When sample_date is not provided, default to today."""
        with app.app_context():
            from app.labs.water_lab.chemistry.utils import create_water_micro_samples
            user = User.query.filter_by(username="chemist").first()

            unique_name = f"Test-NoDate-{uuid.uuid4().hex[:4]}"
            form = {
                "sample_codes": [unique_name],
                "source_type": "busad",
                "analyses": ["PH"],
            }

            with patch("app.labs.water_lab.chemistry.utils.safe_commit", side_effect=_mock_safe_commit(db.session)):
                created, _, _ = create_water_micro_samples(FormLike(form), user.id)
            assert len(created) == 1

            # Cleanup
            for name in created:
                s = Sample.query.filter(Sample.sample_code.like(f"%{name}%")).first()
                if s:
                    db.session.delete(s)
            db.session.commit()

    def test_create_water_micro_samples_volume_2l_only(self, app, db):
        with app.app_context():
            from app.labs.water_lab.chemistry.utils import create_water_micro_samples
            user = User.query.filter_by(username="chemist").first()

            form = {
                "sample_codes": [f"Test-V2L-{uuid.uuid4().hex[:4]}"],
                "source_type": "busad",
                "sample_date": "2030-06-01",
                "analyses": ["PH"],
                "volume_2l": "on",
            }

            with patch("app.labs.water_lab.chemistry.utils.safe_commit", side_effect=_mock_safe_commit(db.session)):
                created, _, _ = create_water_micro_samples(FormLike(form), user.id)
            assert len(created) == 1

            s = Sample.query.filter(Sample.sample_code.like(f"%{created[0]}%")).first()
            assert s.weight == 2000.0

            db.session.delete(s)
            db.session.commit()

    def test_create_water_micro_samples_volume_05l_only(self, app, db):
        with app.app_context():
            from app.labs.water_lab.chemistry.utils import create_water_micro_samples
            user = User.query.filter_by(username="chemist").first()

            form = {
                "sample_codes": [f"Test-V05-{uuid.uuid4().hex[:4]}"],
                "source_type": "busad",
                "sample_date": "2030-06-02",
                "analyses": ["PH"],
                "volume_05l": "on",
            }

            with patch("app.labs.water_lab.chemistry.utils.safe_commit", side_effect=_mock_safe_commit(db.session)):
                created, _, _ = create_water_micro_samples(FormLike(form), user.id)
            assert len(created) == 1

            s = Sample.query.filter(Sample.sample_code.like(f"%{created[0]}%")).first()
            assert s.weight == 500.0

            db.session.delete(s)
            db.session.commit()

    def test_create_water_micro_samples_bad_retention(self, app, db):
        """Invalid retention_period defaults to 7."""
        with app.app_context():
            from app.labs.water_lab.chemistry.utils import create_water_micro_samples
            user = User.query.filter_by(username="chemist").first()

            form = {
                "sample_codes": [f"Test-BadRet-{uuid.uuid4().hex[:4]}"],
                "source_type": "busad",
                "sample_date": "2030-07-01",
                "analyses": ["PH"],
                "retention_period": "not_a_number",
            }

            with patch("app.labs.water_lab.chemistry.utils.safe_commit", side_effect=_mock_safe_commit(db.session)):
                created, _, _ = create_water_micro_samples(FormLike(form), user.id)
            assert len(created) == 1

            s = Sample.query.filter(Sample.sample_code.like(f"%{created[0]}%")).first()
            from datetime import date
            expected_retention = date(2030, 7, 1) + timedelta(days=7)
            assert s.retention_date == expected_retention

            db.session.delete(s)
            db.session.commit()
