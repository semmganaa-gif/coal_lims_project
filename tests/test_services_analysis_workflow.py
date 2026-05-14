# tests/test_services_analysis_workflow.py
# -*- coding: utf-8 -*-
"""Comprehensive tests for app/services/analysis_workflow.py"""

import json
import pytest
from datetime import datetime
from unittest.mock import patch, MagicMock, PropertyMock

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm.exc import StaleDataError


# ---------------------------------------------------------------------------
# Helper: build a mock AnalysisResult that behaves like the ORM object
# ---------------------------------------------------------------------------

def _make_result(id=1, sample_id=10, analysis_code="Mad", final_result=5.5,
                 status="pending_review", raw_data=None, user_id=2,
                 updated_at=None, error_reason=None):
    res = MagicMock()
    res.id = id
    res.sample_id = sample_id
    res.analysis_code = analysis_code
    res.final_result = final_result
    res.status = status
    res.raw_data = raw_data or {"m1": 1.0, "m2": 2.0}
    res.user_id = user_id
    res.updated_at = updated_at or datetime(2026, 3, 10, 9, 0)
    res.error_reason = error_reason
    res.rejection_category = None
    res.rejection_comment = None
    res.set_raw_data = MagicMock()
    res.get_raw_data = MagicMock(return_value=raw_data or {"m1": 1.0, "m2": 2.0})
    return res


def _make_sample(id=10, sample_code="S-001", lab_type="coal", status="in_progress",
                 sample_type="regular", client_name="ClientA", weight=None):
    s = MagicMock()
    s.id = id
    s.sample_code = sample_code
    s.lab_type = lab_type
    s.status = status
    s.sample_type = sample_type
    s.client_name = client_name
    s.weight = weight
    s.received_date = datetime(2026, 3, 10, 8, 0)
    s.get_calculations = MagicMock(return_value=None)
    return s


# ===========================================================================
# TESTS: load_analysis_schemas
# ===========================================================================

class TestLoadAnalysisSchemas:

    @patch("app.services.analysis_workflow.get_analysis_schema")
    @patch("app.services.analysis_workflow.AnalysisTypeRepository")
    def test_loads_all_codes(self, mock_repo, mock_schema, app):
        with app.app_context():
            mock_repo.get_codes.return_value = ["Mad", "Aad", "Vdaf"]
            mock_schema.side_effect = lambda c: {"code": c}

            from app.services.analysis_workflow import load_analysis_schemas
            result = load_analysis_schemas()

            assert "_default" in result
            assert "Mad" in result
            assert "Aad" in result
            assert "Vdaf" in result
            assert len(result) == 4  # 3 codes + _default

    @patch("app.services.analysis_workflow.get_analysis_schema")
    @patch("app.services.analysis_workflow.AnalysisTypeRepository")
    def test_handles_exception(self, mock_repo, mock_schema, app):
        with app.app_context():
            mock_repo.get_codes.side_effect = ValueError("DB error")
            mock_schema.return_value = {"default": True}

            from app.services.analysis_workflow import load_analysis_schemas
            result = load_analysis_schemas()

            assert "_default" in result
            assert len(result) == 1

    @patch("app.services.analysis_workflow.get_analysis_schema")
    @patch("app.services.analysis_workflow.AnalysisTypeRepository")
    def test_empty_codes(self, mock_repo, mock_schema, app):
        with app.app_context():
            mock_repo.get_codes.return_value = []
            mock_schema.return_value = {"default": True}

            from app.services.analysis_workflow import load_analysis_schemas
            result = load_analysis_schemas()

            assert "_default" in result
            assert len(result) == 1


# ===========================================================================
# TESTS: build_pending_results
# ===========================================================================

class TestBuildPendingResults:

    @patch("app.services.analysis_workflow.normalize_raw_data")
    @patch("app.services.analysis_workflow.escape_like_pattern")
    @patch("app.services.analysis_workflow.db")
    def test_basic_query(self, mock_db, mock_escape, mock_norm, app):
        with app.app_context():
            mock_norm.return_value = {}

            mock_result = MagicMock()
            mock_result.id = 1
            mock_result.status = "pending_review"
            mock_result.error_reason = None
            mock_result.raw_data = '{"m1": 1.0}'
            mock_result.final_result = 5.5
            mock_result.updated_at = datetime(2026, 3, 10, 9, 0)

            mock_sample = MagicMock()
            mock_sample.sample_code = "S-001"

            mock_user = MagicMock()
            mock_user.username = "chemist"

            mock_atype = MagicMock()
            mock_atype.code = "Mad"
            mock_atype.name = "Moisture"

            # Build chain mock
            query_mock = MagicMock()
            query_mock.join.return_value = query_mock
            query_mock.filter.return_value = query_mock
            query_mock.order_by.return_value = query_mock
            query_mock.limit.return_value = query_mock
            query_mock.all.return_value = [(mock_result, mock_sample, mock_user, mock_atype)]
            mock_db.session.query.return_value = query_mock

            from app.services.analysis_workflow import build_pending_results
            results = build_pending_results()

            assert len(results) == 1
            assert results[0]["result_id"] == 1
            assert results[0]["sample_code"] == "S-001"
            assert results[0]["analysis_code"] == "Mad"

    @patch("app.services.analysis_workflow.normalize_raw_data")
    @patch("app.services.analysis_workflow.escape_like_pattern")
    @patch("app.services.analysis_workflow.db")
    def test_with_date_filters(self, mock_db, mock_escape, mock_norm, app):
        with app.app_context():
            mock_norm.return_value = {}

            query_mock = MagicMock()
            query_mock.join.return_value = query_mock
            query_mock.filter.return_value = query_mock
            query_mock.order_by.return_value = query_mock
            query_mock.limit.return_value = query_mock
            query_mock.all.return_value = []
            mock_db.session.query.return_value = query_mock

            from app.services.analysis_workflow import build_pending_results
            results = build_pending_results(
                start_date="2026-03-01",
                end_date="2026-03-10",
                sample_name="S-001",
            )
            assert results == []
            mock_escape.assert_called_once_with("S-001")

    @patch("app.services.analysis_workflow.normalize_raw_data")
    @patch("app.services.analysis_workflow.db")
    def test_invalid_date_ignored(self, mock_db, mock_norm, app):
        with app.app_context():
            mock_norm.return_value = {}

            query_mock = MagicMock()
            query_mock.join.return_value = query_mock
            query_mock.filter.return_value = query_mock
            query_mock.order_by.return_value = query_mock
            query_mock.limit.return_value = query_mock
            query_mock.all.return_value = []
            mock_db.session.query.return_value = query_mock

            from app.services.analysis_workflow import build_pending_results
            # Should not raise even with bad dates
            results = build_pending_results(start_date="bad-date", end_date="bad-date")
            assert results == []

    @patch("app.services.analysis_workflow.normalize_raw_data")
    @patch("app.services.analysis_workflow.db")
    def test_raw_data_dict_type(self, mock_db, mock_norm, app):
        """raw_data that is already a dict."""
        with app.app_context():
            mock_norm.return_value = {}

            mock_result = MagicMock()
            mock_result.id = 2
            mock_result.status = "rejected"
            mock_result.error_reason = "qc_fail"
            mock_result.raw_data = {"m1": 1.0}  # already dict
            mock_result.final_result = 3.2
            mock_result.updated_at = datetime(2026, 3, 10, 9, 0)

            mock_sample = MagicMock()
            mock_sample.sample_code = "S-002"

            mock_user = MagicMock()
            mock_user.username = "chem2"

            mock_atype = MagicMock()
            mock_atype.code = "Aad"
            mock_atype.name = "Ash"

            query_mock = MagicMock()
            query_mock.join.return_value = query_mock
            query_mock.filter.return_value = query_mock
            query_mock.order_by.return_value = query_mock
            query_mock.limit.return_value = query_mock
            query_mock.all.return_value = [(mock_result, mock_sample, mock_user, mock_atype)]
            mock_db.session.query.return_value = query_mock

            from app.services.analysis_workflow import build_pending_results
            results = build_pending_results()
            assert len(results) == 1
            assert results[0]["error_reason"] == "qc_fail"

    @patch("app.services.analysis_workflow.normalize_raw_data")
    @patch("app.services.analysis_workflow.db")
    def test_csn_analysis_type(self, mock_db, mock_norm, app):
        """CSN analysis should use t value and final_result for display."""
        with app.app_context():
            mock_norm.return_value = {}

            mock_result = MagicMock()
            mock_result.id = 3
            mock_result.status = "pending_review"
            mock_result.error_reason = None
            mock_result.raw_data = {"t": 2.5, "avg": 4.0}
            mock_result.final_result = 4.0
            mock_result.updated_at = datetime(2026, 3, 10, 9, 0)

            mock_sample = MagicMock()
            mock_sample.sample_code = "S-003"

            mock_user = MagicMock()
            mock_user.username = "chem3"

            mock_atype = MagicMock()
            mock_atype.code = "CSN"
            mock_atype.name = "CSN"

            query_mock = MagicMock()
            query_mock.join.return_value = query_mock
            query_mock.filter.return_value = query_mock
            query_mock.order_by.return_value = query_mock
            query_mock.limit.return_value = query_mock
            query_mock.all.return_value = [(mock_result, mock_sample, mock_user, mock_atype)]
            mock_db.session.query.return_value = query_mock

            from app.services.analysis_workflow import build_pending_results
            results = build_pending_results()
            assert len(results) == 1
            # CSN: t_value is raw_data["t"], final_value is final_result
            assert results[0]["t_value"] == 2.5
            assert results[0]["final_value"] == 4.0

    @patch("app.services.analysis_workflow.normalize_raw_data")
    @patch("app.services.analysis_workflow.db")
    def test_raw_data_non_dict_non_str(self, mock_db, mock_norm, app):
        """raw_data that is neither str nor dict (e.g. None or int)."""
        with app.app_context():
            mock_norm.return_value = {}

            mock_result = MagicMock()
            mock_result.id = 4
            mock_result.status = "pending_review"
            mock_result.error_reason = None
            mock_result.raw_data = 12345  # unusual type
            mock_result.final_result = 1.0
            mock_result.updated_at = None  # test None updated_at

            mock_sample = MagicMock()
            mock_sample.sample_code = "S-004"
            mock_user = MagicMock()
            mock_user.username = "chem4"
            mock_atype = MagicMock()
            mock_atype.code = "Mad"
            mock_atype.name = "Moisture"

            query_mock = MagicMock()
            query_mock.join.return_value = query_mock
            query_mock.filter.return_value = query_mock
            query_mock.order_by.return_value = query_mock
            query_mock.limit.return_value = query_mock
            query_mock.all.return_value = [(mock_result, mock_sample, mock_user, mock_atype)]
            mock_db.session.query.return_value = query_mock

            from app.services.analysis_workflow import build_pending_results
            results = build_pending_results()
            assert len(results) == 1
            assert results[0]["updated_at"] is None
            assert results[0]["raw_data"] == {}


# ===========================================================================
# TESTS: build_dashboard_stats
# ===========================================================================

class TestBuildDashboardStats:

    @patch("app.services.analysis_workflow.get_shift_info")
    @patch("app.services.analysis_workflow.now_local")
    @patch("app.services.analysis_workflow.db")
    def test_returns_expected_keys(self, mock_db, mock_now, mock_shift, app):
        with app.app_context():
            mock_now.return_value = datetime(2026, 3, 10, 12, 0)
            shift = MagicMock()
            shift.shift_start = datetime(2026, 3, 10, 8, 0)
            shift.shift_end = datetime(2026, 3, 10, 20, 0)
            mock_shift.return_value = shift

            # Mock different query calls
            query_mock = MagicMock()
            query_mock.join.return_value = query_mock
            query_mock.filter.return_value = query_mock
            query_mock.group_by.return_value = query_mock
            query_mock.order_by.return_value = query_mock

            # chemist_stats: list of rows
            chemist_row = MagicMock()
            chemist_row.username = "chem1"
            chemist_row.user_id = 2
            chemist_row.total = 10
            chemist_row.approved = 8
            chemist_row.pending = 1
            chemist_row.rejected = 1

            # summary_row
            summary_row = MagicMock()
            summary_row.total = 50
            summary_row.approved = 40
            summary_row.pending = 5
            summary_row.rejected = 5

            # We need to handle multiple db.session.query() calls
            call_count = [0]
            def query_side_effect(*args):
                call_count[0] += 1
                q = MagicMock()
                q.join.return_value = q
                q.filter.return_value = q
                q.group_by.return_value = q
                q.order_by.return_value = q

                if call_count[0] == 1:  # chemist_stats
                    q.all.return_value = [chemist_row]
                elif call_count[0] == 2:  # today_samples
                    q.scalar.return_value = 25
                elif call_count[0] == 3:  # samples_by_unit
                    unit_row = MagicMock()
                    unit_row.client_name = "UnitA"
                    unit_row.count = 15
                    q.all.return_value = [unit_row]
                elif call_count[0] == 4:  # samples_by_type
                    type_row = MagicMock()
                    type_row.sample_type = "regular"
                    type_row.count = 20
                    q.all.return_value = [type_row]
                elif call_count[0] == 5:  # analysis_type_stats
                    at_row = MagicMock()
                    at_row.code = "Mad"
                    at_row.name = "Moisture"
                    at_row.total = 30
                    at_row.approved = 25
                    at_row.pending = 3
                    at_row.rejected = 2
                    q.all.return_value = [at_row]
                elif call_count[0] == 6:  # summary
                    q.one.return_value = summary_row
                return q

            mock_db.session.query.side_effect = query_side_effect

            from app.services.analysis_workflow import build_dashboard_stats
            stats = build_dashboard_stats()

            assert "chemists" in stats
            assert "analysis_types" in stats
            assert "samples_today" in stats
            assert "samples_by_unit" in stats
            assert "samples_by_type" in stats
            assert "summary" in stats
            assert stats["chemists"][0]["username"] == "chem1"
            assert stats["samples_today"] == 25
            assert stats["summary"]["total"] == 50


# ===========================================================================
# TESTS: _apply_status_fields
# ===========================================================================

class TestApplyStatusFields:

    def test_approved_clears_rejection_fields(self, app):
        with app.app_context():
            from app.services.analysis_workflow import _apply_status_fields
            res = _make_result(status="pending_review")
            _apply_status_fields(res, "approved")
            assert res.status == "approved"
            assert res.rejection_category is None
            assert res.rejection_comment is None
            assert res.error_reason is None

    def test_rejected_sets_fields(self, app):
        with app.app_context():
            from app.services.analysis_workflow import _apply_status_fields
            res = _make_result(status="pending_review")
            _apply_status_fields(res, "rejected", "qc_fail", "Bad result")
            assert res.status == "rejected"
            assert res.rejection_category == "qc_fail"
            assert res.rejection_comment == "Bad result"
            assert res.error_reason == "qc_fail"

    def test_rejected_default_comment(self, app):
        with app.app_context():
            from app.services.analysis_workflow import _apply_status_fields
            res = _make_result()
            _apply_status_fields(res, "rejected", "qc_fail", None)
            assert res.rejection_comment == "Ахлах буцаасан"


# ===========================================================================
# TESTS: update_result_status
# ===========================================================================

class TestUpdateResultStatus:

    @patch("app.utils.transaction.db")
    @patch("app.services.analysis_workflow.log_audit")
    @patch("app.services.analysis_workflow.cache")
    @patch("app.services.analysis_workflow.log_analysis_action")
    @patch("app.services.analysis_workflow.db")
    @patch("app.services.analysis_workflow.AnalysisResult")
    def test_approve_success(self, mock_AR, mock_db, mock_log_action, mock_cache,
                             mock_log_audit, mock_tx_db, app):
        with app.app_context():
            res = _make_result()
            sample = _make_sample()
            mock_AR.query.filter_by.return_value.with_for_update.return_value.first.return_value = res
            mock_db.session.get.return_value = sample

            from app.services.analysis_workflow import update_result_status
            data, err, code = update_result_status(1, "approved")

            assert code == 200
            assert err is None
            assert data["status"] == "approved"
            mock_tx_db.session.commit.assert_called_once()
            mock_cache.delete.assert_any_call('kpi_summary_ahlah')

    @patch("app.services.analysis_workflow.db")
    @patch("app.services.analysis_workflow.AnalysisResult")
    def test_invalid_status(self, mock_AR, mock_db, app):
        with app.app_context():
            from app.services.analysis_workflow import update_result_status
            data, err, code = update_result_status(1, "invalid_status")
            assert code == 400
            assert data is None

    @patch("app.services.analysis_workflow.db")
    @patch("app.services.analysis_workflow.AnalysisResult")
    def test_not_found(self, mock_AR, mock_db, app):
        with app.app_context():
            mock_AR.query.filter_by.return_value.with_for_update.return_value.first.return_value = None

            from app.services.analysis_workflow import update_result_status
            data, err, code = update_result_status(999, "approved")
            assert code == 404
            assert data is None

    @patch("app.utils.transaction.db")
    @patch("app.services.analysis_workflow.log_analysis_action")
    @patch("app.services.analysis_workflow.db")
    @patch("app.services.analysis_workflow.AnalysisResult")
    def test_stale_data_error(self, mock_AR, mock_db, mock_log_action, mock_tx_db, app):
        with app.app_context():
            res = _make_result()
            mock_AR.query.filter_by.return_value.with_for_update.return_value.first.return_value = res
            mock_db.session.get.return_value = _make_sample()
            mock_tx_db.session.commit.side_effect = StaleDataError()

            from app.services.analysis_workflow import update_result_status
            data, err, code = update_result_status(1, "approved")
            assert code == 409
            assert data is None
            mock_tx_db.session.rollback.assert_called_once()

    @patch("app.services.analysis_workflow.log_audit")
    @patch("app.services.analysis_workflow.cache")
    @patch("app.services.analysis_workflow.log_analysis_action")
    @patch("app.services.analysis_workflow.db")
    @patch("app.services.analysis_workflow.AnalysisResult")
    def test_reject_with_comment(self, mock_AR, mock_db, mock_log_action,
                                  mock_cache, mock_log_audit, app):
        with app.app_context():
            res = _make_result()
            mock_AR.query.filter_by.return_value.with_for_update.return_value.first.return_value = res
            mock_db.session.get.return_value = _make_sample()

            from app.services.analysis_workflow import update_result_status
            data, err, code = update_result_status(
                1, "rejected",
                rejection_comment="<script>alert(1)</script>",
                rejection_category="qc_fail",
            )
            assert code == 200
            # XSS should be escaped in the log call
            mock_log_action.assert_called_once()

    @patch("app.services.analysis_workflow.log_audit")
    @patch("app.services.analysis_workflow.cache")
    @patch("app.services.analysis_workflow.log_analysis_action")
    @patch("app.services.analysis_workflow.db")
    @patch("app.services.analysis_workflow.AnalysisResult")
    def test_approve_no_sample(self, mock_AR, mock_db, mock_log_action,
                                mock_cache, mock_log_audit, app):
        """Result with no associated sample (sample_id is None)."""
        with app.app_context():
            res = _make_result(sample_id=None)
            res.sample_id = None
            mock_AR.query.filter_by.return_value.with_for_update.return_value.first.return_value = res
            mock_db.session.get.return_value = None

            from app.services.analysis_workflow import update_result_status
            data, err, code = update_result_status(1, "approved")
            assert code == 200


# ===========================================================================
# TESTS: bulk_update_result_status
# ===========================================================================

class TestBulkUpdateResultStatus:

    @patch("app.services.analysis_workflow.notify_sample_status_change")
    @patch("app.utils.transaction.db")
    @patch("app.services.analysis_workflow.log_audit")
    @patch("app.services.analysis_workflow.log_analysis_action")
    @patch("app.services.analysis_workflow.db")
    @patch("app.services.analysis_workflow.Sample")
    @patch("app.services.analysis_workflow.AnalysisResult")
    def test_bulk_approve_success(self, mock_AR, mock_Sample, mock_db,
                                   mock_log_action, mock_log_audit,
                                   mock_tx_db, mock_notify, app):
        with app.app_context():
            res1 = _make_result(id=1, sample_id=10, status="pending_review")
            res2 = _make_result(id=2, sample_id=11, status="pending_review")

            mock_AR.query.filter.return_value.with_for_update.return_value.all.return_value = [res1, res2]

            sample1 = _make_sample(id=10)
            sample2 = _make_sample(id=11)
            mock_Sample.query.filter.return_value.all.return_value = [sample1, sample2]

            from app.services.analysis_workflow import bulk_update_result_status
            data, err, code = bulk_update_result_status([1, 2], "approved", username="senior")

            assert code == 200
            assert data["success_count"] == 2
            assert data["failed_count"] == 0
            mock_tx_db.session.commit.assert_called_once()

    def test_empty_result_ids(self, app):
        with app.app_context():
            from app.services.analysis_workflow import bulk_update_result_status
            data, err, code = bulk_update_result_status([], "approved")
            assert code == 400
            assert data is None

    def test_too_many_ids(self, app):
        with app.app_context():
            from app.services.analysis_workflow import bulk_update_result_status
            data, err, code = bulk_update_result_status(list(range(201)), "approved")
            assert code == 400

    def test_invalid_status(self, app):
        with app.app_context():
            from app.services.analysis_workflow import bulk_update_result_status
            data, err, code = bulk_update_result_status([1], "pending_review")
            assert code == 400

    def test_reject_without_category(self, app):
        with app.app_context():
            from app.services.analysis_workflow import bulk_update_result_status
            data, err, code = bulk_update_result_status([1], "rejected")
            assert code == 400
            assert "шалтгаан" in err

    @patch("app.services.analysis_workflow.log_analysis_action")
    @patch("app.services.analysis_workflow.db")
    @patch("app.services.analysis_workflow.Sample")
    @patch("app.services.analysis_workflow.AnalysisResult")
    def test_invalid_id_type(self, mock_AR, mock_Sample, mock_db,
                              mock_log_action, app):
        with app.app_context():
            from app.services.analysis_workflow import bulk_update_result_status
            data, err, code = bulk_update_result_status(["abc", "xyz"], "approved")
            assert code == 400
            assert "ID буруу" in err

    @patch("app.services.analysis_workflow.log_analysis_action")
    @patch("app.services.analysis_workflow.db")
    @patch("app.services.analysis_workflow.Sample")
    @patch("app.services.analysis_workflow.AnalysisResult")
    def test_result_not_found_in_db(self, mock_AR, mock_Sample, mock_db,
                                     mock_log_action, app):
        """Result IDs that don't exist in DB should be counted as failed."""
        with app.app_context():
            mock_AR.query.filter.return_value.with_for_update.return_value.all.return_value = []
            mock_Sample.query.filter.return_value.all.return_value = []

            from app.services.analysis_workflow import bulk_update_result_status
            data, err, code = bulk_update_result_status([999], "approved")
            assert code == 200
            assert data["success_count"] == 0
            assert data["failed_count"] == 1

    @patch("app.services.analysis_workflow.log_analysis_action")
    @patch("app.services.analysis_workflow.db")
    @patch("app.services.analysis_workflow.Sample")
    @patch("app.services.analysis_workflow.AnalysisResult")
    def test_skip_already_approved(self, mock_AR, mock_Sample, mock_db,
                                    mock_log_action, app):
        """Results not in pending_review/rejected should be skipped."""
        with app.app_context():
            res = _make_result(id=1, status="approved")
            mock_AR.query.filter.return_value.with_for_update.return_value.all.return_value = [res]
            mock_Sample.query.filter.return_value.all.return_value = []

            from app.services.analysis_workflow import bulk_update_result_status
            data, err, code = bulk_update_result_status([1], "approved")
            assert data["failed_count"] == 1
            assert data["success_count"] == 0

    @patch("app.services.analysis_workflow.notify_sample_status_change")
    @patch("app.utils.transaction.db")
    @patch("app.services.analysis_workflow.log_audit")
    @patch("app.services.analysis_workflow.log_analysis_action")
    @patch("app.services.analysis_workflow.db")
    @patch("app.services.analysis_workflow.Sample")
    @patch("app.services.analysis_workflow.AnalysisResult")
    def test_stale_data_on_commit(self, mock_AR, mock_Sample, mock_db,
                                   mock_log_action, mock_log_audit,
                                   mock_tx_db, mock_notify, app):
        with app.app_context():
            res = _make_result(id=1, status="pending_review")
            mock_AR.query.filter.return_value.with_for_update.return_value.all.return_value = [res]
            mock_Sample.query.filter.return_value.all.return_value = [_make_sample()]
            mock_tx_db.session.commit.side_effect = StaleDataError()

            from app.services.analysis_workflow import bulk_update_result_status
            data, err, code = bulk_update_result_status([1], "approved")
            assert code == 409
            mock_tx_db.session.rollback.assert_called_once()

    @patch("app.utils.transaction.db")
    @patch("app.services.analysis_workflow.notify_sample_status_change")
    @patch("app.services.analysis_workflow.log_audit")
    @patch("app.services.analysis_workflow.log_analysis_action")
    @patch("app.services.analysis_workflow.db")
    @patch("app.services.analysis_workflow.Sample")
    @patch("app.services.analysis_workflow.AnalysisResult")
    def test_sqlalchemy_error_on_commit(self, mock_AR, mock_Sample, mock_db,
                                         mock_log_action, mock_log_audit,
                                         mock_notify, mock_tx_db, app):
        with app.app_context():
            res = _make_result(id=1, status="pending_review")
            mock_AR.query.filter.return_value.with_for_update.return_value.all.return_value = [res]
            mock_Sample.query.filter.return_value.all.return_value = [_make_sample()]
            mock_tx_db.session.commit.side_effect = SQLAlchemyError("DB gone")

            from app.services.analysis_workflow import bulk_update_result_status
            data, err, code = bulk_update_result_status([1], "approved")
            assert code == 500

    @patch("app.services.analysis_workflow.notify_sample_status_change")
    @patch("app.services.analysis_workflow.log_audit")
    @patch("app.services.analysis_workflow.log_analysis_action")
    @patch("app.services.analysis_workflow.db")
    @patch("app.services.analysis_workflow.Sample")
    @patch("app.services.analysis_workflow.AnalysisResult")
    def test_bulk_reject_with_comment(self, mock_AR, mock_Sample, mock_db,
                                       mock_log_action, mock_log_audit,
                                       mock_notify, app):
        with app.app_context():
            res = _make_result(id=1, status="pending_review")
            mock_AR.query.filter.return_value.with_for_update.return_value.all.return_value = [res]
            mock_Sample.query.filter.return_value.all.return_value = [_make_sample()]

            from app.services.analysis_workflow import bulk_update_result_status
            data, err, code = bulk_update_result_status(
                [1], "rejected",
                rejection_comment="bad data",
                rejection_category="qc_fail",
                username="senior",
            )
            assert code == 200
            assert data["success_count"] == 1

    @patch("app.services.analysis_workflow.notify_sample_status_change")
    @patch("app.services.analysis_workflow.log_audit")
    @patch("app.services.analysis_workflow.log_analysis_action")
    @patch("app.services.analysis_workflow.db")
    @patch("app.services.analysis_workflow.Sample")
    @patch("app.services.analysis_workflow.AnalysisResult")
    def test_email_notification_failure(self, mock_AR, mock_Sample, mock_db,
                                         mock_log_action, mock_log_audit,
                                         mock_notify, app):
        """Email failure should not break the response."""
        with app.app_context():
            res = _make_result(id=1, status="pending_review")
            mock_AR.query.filter.return_value.with_for_update.return_value.all.return_value = [res]
            mock_Sample.query.filter.return_value.all.return_value = [_make_sample()]
            mock_notify.side_effect = OSError("SMTP down")

            from app.services.analysis_workflow import bulk_update_result_status
            data, err, code = bulk_update_result_status([1], "approved")
            assert code == 200


# ===========================================================================
# TESTS: select_repeat_result
# ===========================================================================

class TestSelectRepeatResult:

    @patch("app.services.analysis_workflow.log_audit")
    @patch("app.services.analysis_workflow.log_analysis_action")
    @patch("app.services.analysis_workflow.db")
    @patch("app.services.analysis_workflow.AnalysisResult")
    def test_select_original(self, mock_AR, mock_db, mock_log_action,
                              mock_log_audit, app):
        with app.app_context():
            res = _make_result()
            res.get_raw_data.return_value = {
                "_repeat": {
                    "original_final_result": 5.0,
                    "repeat_final_result": 5.5,
                }
            }
            mock_AR.query.filter_by.return_value.with_for_update.return_value.first.return_value = res
            mock_db.session.get.return_value = _make_sample()

            from app.services.analysis_workflow import select_repeat_result
            data, err, code = select_repeat_result(1, use_original=True)

            assert code == 200
            assert data["use_original"] is True
            assert res.final_result == 5.0

    @patch("app.services.analysis_workflow.log_audit")
    @patch("app.services.analysis_workflow.log_analysis_action")
    @patch("app.services.analysis_workflow.db")
    @patch("app.services.analysis_workflow.AnalysisResult")
    def test_select_repeat(self, mock_AR, mock_db, mock_log_action,
                            mock_log_audit, app):
        with app.app_context():
            res = _make_result()
            res.get_raw_data.return_value = {
                "_repeat": {
                    "original_final_result": 5.0,
                    "repeat_final_result": 5.5,
                }
            }
            mock_AR.query.filter_by.return_value.with_for_update.return_value.first.return_value = res
            mock_db.session.get.return_value = _make_sample()

            from app.services.analysis_workflow import select_repeat_result
            data, err, code = select_repeat_result(1, use_original=False)

            assert code == 200
            assert data["use_original"] is False
            assert res.final_result == 5.5

    @patch("app.services.analysis_workflow.db")
    @patch("app.services.analysis_workflow.AnalysisResult")
    def test_not_found(self, mock_AR, mock_db, app):
        with app.app_context():
            mock_AR.query.filter_by.return_value.with_for_update.return_value.first.return_value = None

            from app.services.analysis_workflow import select_repeat_result
            data, err, code = select_repeat_result(999)
            assert code == 404

    @patch("app.services.analysis_workflow.db")
    @patch("app.services.analysis_workflow.AnalysisResult")
    def test_no_repeat_info(self, mock_AR, mock_db, app):
        with app.app_context():
            res = _make_result()
            res.get_raw_data.return_value = {}  # no _repeat key
            mock_AR.query.filter_by.return_value.with_for_update.return_value.first.return_value = res

            from app.services.analysis_workflow import select_repeat_result
            data, err, code = select_repeat_result(1)
            assert code == 400

    @patch("app.services.analysis_workflow.db")
    @patch("app.services.analysis_workflow.AnalysisResult")
    def test_missing_values(self, mock_AR, mock_db, app):
        with app.app_context():
            res = _make_result()
            res.get_raw_data.return_value = {
                "_repeat": {
                    "original_final_result": None,
                    "repeat_final_result": None,
                }
            }
            mock_AR.query.filter_by.return_value.with_for_update.return_value.first.return_value = res

            from app.services.analysis_workflow import select_repeat_result
            data, err, code = select_repeat_result(1)
            assert code == 400

    @patch("app.utils.transaction.db")
    @patch("app.services.analysis_workflow.log_analysis_action")
    @patch("app.services.analysis_workflow.db")
    @patch("app.services.analysis_workflow.AnalysisResult")
    def test_stale_data_error(self, mock_AR, mock_db, mock_log_action, mock_tx_db, app):
        with app.app_context():
            res = _make_result()
            res.get_raw_data.return_value = {
                "_repeat": {
                    "original_final_result": 5.0,
                    "repeat_final_result": 5.5,
                }
            }
            mock_AR.query.filter_by.return_value.with_for_update.return_value.first.return_value = res
            mock_db.session.get.return_value = _make_sample()
            mock_tx_db.session.commit.side_effect = StaleDataError()

            from app.services.analysis_workflow import select_repeat_result
            data, err, code = select_repeat_result(1, use_original=True)
            assert code == 409


# ===========================================================================
# TESTS: update_result_status_api
# ===========================================================================

class TestUpdateResultStatusApi:

    @patch("app.services.analysis_workflow.log_audit")
    @patch("app.services.analysis_workflow.log_analysis_action")
    @patch("app.services.analysis_workflow.db")
    def test_approve_success(self, mock_db, mock_log_action, mock_log_audit, app):
        with app.app_context():
            res = _make_result()
            sample = _make_sample()
            mock_db.session.get.side_effect = lambda model, id: (
                res if model.__name__ == "AnalysisResult" else sample
            )

            from app.services.analysis_workflow import update_result_status_api
            data, err, code = update_result_status_api(1, "approved")

            assert code == 200
            assert data["status"] == "approved"

    @patch("app.services.analysis_workflow.db")
    def test_not_found(self, mock_db, app):
        with app.app_context():
            mock_db.session.get.return_value = None

            from app.services.analysis_workflow import update_result_status_api
            data, err, code = update_result_status_api(999, "approved")
            assert code == 404

    @patch("app.services.analysis_workflow.db")
    def test_invalid_status(self, mock_db, app):
        with app.app_context():
            res = _make_result()
            mock_db.session.get.return_value = res

            from app.services.analysis_workflow import update_result_status_api
            data, err, code = update_result_status_api(1, "bogus")
            assert code == 400

    @patch("app.utils.transaction.db")
    @patch("app.services.analysis_workflow.log_analysis_action")
    @patch("app.services.analysis_workflow.db")
    def test_reject_with_comment(self, mock_db, mock_log_action, mock_tx_db, app):
        with app.app_context():
            res = _make_result()
            sample = _make_sample()
            mock_db.session.get.side_effect = lambda model, id: (
                res if model.__name__ == "AnalysisResult" else sample
            )
            mock_tx_db.session.commit.side_effect = StaleDataError()

            from app.services.analysis_workflow import update_result_status_api
            data, err, code = update_result_status_api(
                1, "rejected",
                rejection_comment="Bad data",
                rejection_category="qc_fail",
                error_reason="qc_fail",
            )
            assert code == 409

    @patch("app.utils.transaction.db")
    @patch("app.services.analysis_workflow.log_analysis_action")
    @patch("app.services.analysis_workflow.db")
    def test_sqlalchemy_error(self, mock_db, mock_log_action, mock_tx_db, app):
        with app.app_context():
            res = _make_result()
            sample = _make_sample()
            mock_db.session.get.side_effect = lambda model, id: (
                res if model.__name__ == "AnalysisResult" else sample
            )
            mock_tx_db.session.commit.side_effect = SQLAlchemyError("DB error")

            from app.services.analysis_workflow import update_result_status_api
            data, err, code = update_result_status_api(1, "approved")
            assert code == 500

    @patch("app.services.analysis_workflow.log_audit")
    @patch("app.services.analysis_workflow.log_analysis_action")
    @patch("app.services.analysis_workflow.db")
    def test_pending_review_status(self, mock_db, mock_log_action,
                                    mock_log_audit, app):
        with app.app_context():
            res = _make_result()
            sample = _make_sample()
            mock_db.session.get.side_effect = lambda model, id: (
                res if model.__name__ == "AnalysisResult" else sample
            )

            from app.services.analysis_workflow import update_result_status_api
            data, err, code = update_result_status_api(1, "pending_review")
            assert code == 200

    @patch("app.services.analysis_workflow.log_audit")
    @patch("app.services.analysis_workflow.log_analysis_action")
    @patch("app.services.analysis_workflow.db")
    def test_with_action_type(self, mock_db, mock_log_action,
                               mock_log_audit, app):
        with app.app_context():
            res = _make_result()
            sample = _make_sample()
            mock_db.session.get.side_effect = lambda model, id: (
                res if model.__name__ == "AnalysisResult" else sample
            )

            from app.services.analysis_workflow import update_result_status_api
            data, err, code = update_result_status_api(
                1, "approved", action_type="senior_approve"
            )
            assert code == 200
            # Check action_type is appended to reason
            call_kwargs = mock_log_action.call_args[1]
            assert "senior_approve" in call_kwargs["reason"]


# ===========================================================================
# TESTS: _process_control_gbw
# ===========================================================================

class TestProcessControlGbw:

    def test_regular_sample_skipped(self, app):
        with app.app_context():
            from app.services.analysis_workflow import _process_control_gbw
            sample = _make_sample(sample_type="regular", sample_code="S-001")
            targets, val, is_gbw = _process_control_gbw(
                sample, "Mad", 5.0, {}
            )
            assert targets is None
            assert val == 5.0
            assert is_gbw is False

    def test_none_final_result(self, app):
        with app.app_context():
            from app.services.analysis_workflow import _process_control_gbw
            sample = _make_sample(sample_type="control", sample_code="CM-001")
            targets, val, is_gbw = _process_control_gbw(
                sample, "Mad", None, {}
            )
            assert targets is None

    @patch("app.services.analysis_workflow.ControlStandardRepository")
    def test_cm_sample_with_targets(self, mock_repo, app):
        with app.app_context():
            from app.services.analysis_workflow import _process_control_gbw

            std = MagicMock()
            std.targets = {"Mad": {"mean": 5.0, "tolerance": 0.3}}
            mock_repo.get_active.return_value = std

            sample = _make_sample(sample_type="control", sample_code="CM-001")
            targets, val, is_gbw = _process_control_gbw(
                sample, "Mad", 5.1, {}
            )
            assert targets == {"mean": 5.0, "tolerance": 0.3}
            assert val == 5.1
            assert is_gbw is False

    @patch("app.services.analysis_workflow.GbwStandardRepository")
    def test_gbw_sample(self, mock_repo, app):
        with app.app_context():
            from app.services.analysis_workflow import _process_control_gbw

            std = MagicMock()
            std.targets = {"Mad": {"mean": 4.5, "tolerance": 0.2}}
            mock_repo.get_active.return_value = std

            sample = _make_sample(sample_type="gbw", sample_code="GBW-001")
            targets, val, is_gbw = _process_control_gbw(
                sample, "Mad", 4.6, {}
            )
            assert targets is not None
            assert is_gbw is True

    @patch("app.services.analysis_workflow.ControlStandardRepository")
    def test_no_active_standard(self, mock_repo, app):
        with app.app_context():
            from app.services.analysis_workflow import _process_control_gbw

            mock_repo.get_active.return_value = None

            sample = _make_sample(sample_type="control", sample_code="CM-001")
            targets, val, is_gbw = _process_control_gbw(
                sample, "Mad", 5.0, {}
            )
            assert targets is None

    @patch("app.services.analysis_workflow.ControlStandardRepository")
    def test_dry_conversion_with_mad(self, mock_repo, app):
        with app.app_context():
            from app.services.analysis_workflow import _process_control_gbw

            std = MagicMock()
            std.targets = {"Adb,%": {"mean": 10.0, "tolerance": 0.5}}
            mock_repo.get_active.return_value = std

            sample = _make_sample(sample_type="control", sample_code="CM-001")
            sample.get_calculations.return_value = MagicMock(mad=5.0)

            targets, val, is_gbw = _process_control_gbw(
                sample, "Aad", 9.0, {}
            )
            # dry conversion: 9.0 * 100/(100-5.0) = 9.473...
            assert targets is not None
            assert abs(val - 9.0 * 100.0 / 95.0) < 0.01

    @patch("app.services.analysis_workflow.ControlStandardRepository")
    def test_dry_conversion_no_mad_available(self, mock_repo, app):
        with app.app_context():
            from app.services.analysis_workflow import _process_control_gbw

            std = MagicMock()
            std.targets = {"Adb,%": {"mean": 10.0, "tolerance": 0.5}}
            mock_repo.get_active.return_value = std

            sample = _make_sample(sample_type="control", sample_code="CM-001")
            sample.get_calculations.return_value = None

            raw_norm = {}
            targets, val, is_gbw = _process_control_gbw(
                sample, "Aad", 9.0, raw_norm
            )
            # No Mad -> targets set to None, _mad_required flag set
            assert targets is None
            assert raw_norm.get("_mad_required") is True

    @patch("app.services.analysis_workflow.ControlStandardRepository")
    def test_mad_from_batch_data(self, mock_repo, app):
        with app.app_context():
            from app.services.analysis_workflow import _process_control_gbw

            std = MagicMock()
            std.targets = {"Adb,%": {"mean": 10.0, "tolerance": 0.5}}
            mock_repo.get_active.return_value = std

            sample = _make_sample(sample_type="control", sample_code="CM-001")
            sample.get_calculations.return_value = None

            batch = [{"analysis_code": "Mad", "final_result": 3.0}]
            targets, val, is_gbw = _process_control_gbw(
                sample, "Aad", 9.0, {}, batch_data=batch
            )
            assert targets is not None
            # 9.0 * 100/(100-3.0)
            assert abs(val - 9.0 * 100.0 / 97.0) < 0.01

    @patch("app.services.analysis_workflow.GbwStandardRepository")
    def test_gbw_cv_conversion(self, mock_repo, app):
        """GBW CV analysis with val_dry > 100 should convert to MJ/kg."""
        with app.app_context():
            from app.services.analysis_workflow import _process_control_gbw

            std = MagicMock()
            std.targets = {"CVdb,MJ/kg": {"mean": 28.0, "tolerance": 1.0}}
            mock_repo.get_active.return_value = std

            sample = _make_sample(sample_type="gbw", sample_code="GBW-001")
            sample.get_calculations.return_value = MagicMock(mad=2.0)

            targets, val, is_gbw = _process_control_gbw(
                sample, "CV", 6500.0, {}
            )
            # 6500 * 100/98 = 6632.65... > 100 -> (6632.65 * 4.1868) / 1000
            assert is_gbw is True
            expected_dry = 6500.0 * 100.0 / 98.0
            expected_val = (expected_dry * 4.1868) / 1000.0
            assert abs(val - expected_val) < 0.1

    @patch("app.services.analysis_workflow.ControlStandardRepository")
    def test_targets_as_json_string(self, mock_repo, app):
        with app.app_context():
            from app.services.analysis_workflow import _process_control_gbw

            std = MagicMock()
            std.targets = json.dumps({"Mad": {"mean": 5.0, "tolerance": 0.3}})
            mock_repo.get_active.return_value = std

            sample = _make_sample(sample_type="control", sample_code="CM-001")
            targets, val, is_gbw = _process_control_gbw(
                sample, "Mad", 5.1, {}
            )
            assert targets == {"mean": 5.0, "tolerance": 0.3}


# ===========================================================================
# TESTS: save_single_result
# ===========================================================================

class TestSaveSingleResult:

    def _base_patches(self):
        """Return a dict of common patches for save_single_result tests."""
        return {
            "validate_sample_id": patch(
                "app.services.analysis_workflow.validate_sample_id",
                return_value=(10, None),
            ),
            "validate_analysis_code": patch(
                "app.services.analysis_workflow.validate_analysis_code",
                return_value=("Mad", None),
            ),
            "validate_analysis_result": patch(
                "app.services.analysis_workflow.validate_analysis_result",
                return_value=(5.5, None),
            ),
            "validate_equipment_id": patch(
                "app.services.analysis_workflow.validate_equipment_id",
                return_value=(None, None),
            ),
            "norm_code": patch(
                "app.services.analysis_workflow.norm_code",
                return_value="Mad",
            ),
            "normalize_raw_data": patch(
                "app.services.analysis_workflow.normalize_raw_data",
                return_value={"m1": 1.0, "m2": 2.0, "avg": 1.5, "diff": 0.1},
            ),
            "verify_and_recalculate": patch(
                "app.services.analysis_workflow.verify_and_recalculate",
                return_value=(5.5, []),
            ),
            "determine_result_status": patch(
                "app.services.analysis_workflow.determine_result_status",
                return_value=("approved", None),
            ),
            "log_analysis_action": patch(
                "app.services.analysis_workflow.log_analysis_action",
            ),
            "db": patch("app.services.analysis_workflow.db"),
            "AnalysisResult": patch("app.services.analysis_workflow.AnalysisResult"),
            "AnalysisResultLog": patch("app.services.analysis_workflow.AnalysisResultLog"),
            "to_float": patch(
                "app.services.analysis_workflow.to_float",
                return_value=1.5,
            ),
        }

    def test_create_new_result(self, app):
        with app.app_context():
            patches = self._base_patches()
            mocks = {}
            for name, p in patches.items():
                mocks[name] = p.start()

            try:
                # No existing result
                mocks["AnalysisResult"].query.filter_by.return_value.order_by.return_value.with_for_update.return_value.first.return_value = None

                # No first log
                mocks["AnalysisResultLog"].query.filter_by.return_value.order_by.return_value.first.return_value = None

                # Sample
                sample = _make_sample()
                mocks["db"].session.query.return_value.filter_by.return_value.with_for_update.return_value.first.return_value = sample

                # Mock the new AnalysisResult constructor
                new_res = MagicMock()
                new_res.id = 100
                new_res.raw_data = {"m1": 1.0}
                new_res.final_result = 5.5
                new_res.set_raw_data = MagicMock()
                mocks["AnalysisResult"].return_value = new_res

                from app.services.analysis_workflow import save_single_result
                item = {
                    "sample_id": 10,
                    "analysis_code": "Mad",
                    "final_result": 5.5,
                    "raw_data": {"m1": 1.0, "m2": 2.0},
                }

                result, err = save_single_result(item, user_id=2)

                assert err is None
                assert result["success"] is True
                assert result["sample_id"] == 10
                assert result["analysis_code"] == "Mad"
                assert result["status"] == "approved"

            finally:
                for p in patches.values():
                    p.stop()

    def test_update_existing_result(self, app):
        with app.app_context():
            patches = self._base_patches()
            mocks = {}
            for name, p in patches.items():
                mocks[name] = p.start()

            try:
                existing = _make_result(id=50)
                mocks["AnalysisResult"].query.filter_by.return_value.order_by.return_value.with_for_update.return_value.first.return_value = existing

                # No previous approved log
                log_query = MagicMock()
                log_query.filter_by.return_value = log_query
                log_query.filter.return_value = log_query
                log_query.first.return_value = None
                log_query.order_by.return_value = log_query
                mocks["AnalysisResultLog"].query = log_query

                sample = _make_sample()
                mocks["db"].session.query.return_value.filter_by.return_value.with_for_update.return_value.first.return_value = sample

                from app.services.analysis_workflow import save_single_result
                item = {
                    "sample_id": 10,
                    "analysis_code": "Mad",
                    "final_result": 5.5,
                    "raw_data": {"m1": 1.0, "m2": 2.0},
                }

                result, err = save_single_result(item, user_id=2)

                assert err is None
                assert result["success"] is True

            finally:
                for p in patches.values():
                    p.stop()

    def test_validation_error_sample_id(self, app):
        with app.app_context():
            with patch("app.services.analysis_workflow.validate_sample_id",
                       return_value=(None, "ID буруу")):
                from app.services.analysis_workflow import save_single_result
                with pytest.raises(ValueError, match="Дээжийн ID алдаа"):
                    save_single_result({"sample_id": "bad"}, user_id=1)

    def test_validation_error_analysis_code(self, app):
        with app.app_context():
            with patch("app.services.analysis_workflow.validate_sample_id",
                       return_value=(10, None)), \
                 patch("app.services.analysis_workflow.validate_analysis_code",
                       return_value=(None, "Код буруу")):
                from app.services.analysis_workflow import save_single_result
                with pytest.raises(ValueError, match="Кодын алдаа"):
                    save_single_result(
                        {"sample_id": 10, "analysis_code": ""},
                        user_id=1,
                    )

    def test_validation_error_final_result(self, app):
        with app.app_context():
            with patch("app.services.analysis_workflow.validate_sample_id",
                       return_value=(10, None)), \
                 patch("app.services.analysis_workflow.validate_analysis_code",
                       return_value=("Mad", None)), \
                 patch("app.services.analysis_workflow.norm_code",
                       return_value="Mad"), \
                 patch("app.services.analysis_workflow.validate_analysis_result",
                       return_value=(None, "Утга буруу")):
                from app.services.analysis_workflow import save_single_result
                result, err = save_single_result(
                    {"sample_id": 10, "analysis_code": "Mad", "final_result": "bad"},
                    user_id=1,
                )
                assert result is None
                assert "Утга буруу" in err

    def test_sample_not_found(self, app):
        with app.app_context():
            patches = self._base_patches()
            mocks = {}
            for name, p in patches.items():
                mocks[name] = p.start()

            try:
                mocks["db"].session.query.return_value.filter_by.return_value.with_for_update.return_value.first.return_value = None

                from app.services.analysis_workflow import save_single_result
                with pytest.raises(ValueError, match="олдсонгүй"):
                    save_single_result(
                        {"sample_id": 999, "analysis_code": "Mad",
                         "final_result": 5.5, "raw_data": {}},
                        user_id=1,
                    )
            finally:
                for p in patches.values():
                    p.stop()

    def test_wrong_lab_type(self, app):
        with app.app_context():
            patches = self._base_patches()
            mocks = {}
            for name, p in patches.items():
                mocks[name] = p.start()

            try:
                sample = _make_sample(lab_type="water")
                mocks["db"].session.query.return_value.filter_by.return_value.with_for_update.return_value.first.return_value = sample

                from app.services.analysis_workflow import save_single_result
                with pytest.raises(ValueError, match="water"):
                    save_single_result(
                        {"sample_id": 10, "analysis_code": "Mad",
                         "final_result": 5.5, "raw_data": {}},
                        user_id=1,
                    )
            finally:
                for p in patches.values():
                    p.stop()

    def test_archived_sample(self, app):
        with app.app_context():
            patches = self._base_patches()
            mocks = {}
            for name, p in patches.items():
                mocks[name] = p.start()

            try:
                sample = _make_sample(status="archived")
                mocks["db"].session.query.return_value.filter_by.return_value.with_for_update.return_value.first.return_value = sample

                from app.services.analysis_workflow import save_single_result
                with pytest.raises(ValueError, match="archived"):
                    save_single_result(
                        {"sample_id": 10, "analysis_code": "Mad",
                         "final_result": 5.5, "raw_data": {}},
                        user_id=1,
                    )
            finally:
                for p in patches.values():
                    p.stop()

    def test_raw_data_not_dict(self, app):
        with app.app_context():
            patches = self._base_patches()
            mocks = {}
            for name, p in patches.items():
                mocks[name] = p.start()

            try:
                sample = _make_sample()
                mocks["db"].session.query.return_value.filter_by.return_value.with_for_update.return_value.first.return_value = sample

                from app.services.analysis_workflow import save_single_result
                with pytest.raises(ValueError, match="dict"):
                    save_single_result(
                        {"sample_id": 10, "analysis_code": "Mad",
                         "final_result": 5.5, "raw_data": "not a dict"},
                        user_id=1,
                    )
            finally:
                for p in patches.values():
                    p.stop()

    def test_solid_weight_update(self, app):
        """SOLID analysis should update sample weight."""
        with app.app_context():
            patches = self._base_patches()
            mocks = {}
            for name, p in patches.items():
                mocks[name] = p.start()

            try:
                mocks["norm_code"].return_value = "SOLID"
                mocks["validate_analysis_code"].return_value = ("SOLID", None)
                mocks["normalize_raw_data"].return_value = {
                    "A": 100.5, "B": 50.2, "avg": 50.3, "diff": 0.0,
                }

                existing = _make_result(id=50, analysis_code="SOLID")
                mocks["AnalysisResult"].query.filter_by.return_value.order_by.return_value.with_for_update.return_value.first.return_value = existing

                log_query = MagicMock()
                log_query.filter_by.return_value = log_query
                log_query.filter.return_value = log_query
                log_query.first.return_value = None
                log_query.order_by.return_value = log_query
                mocks["AnalysisResultLog"].query = log_query

                sample = _make_sample()
                mocks["db"].session.query.return_value.filter_by.return_value.with_for_update.return_value.first.return_value = sample

                from app.services.analysis_workflow import save_single_result
                result, err = save_single_result(
                    {"sample_id": 10, "analysis_code": "SOLID",
                     "final_result": 50.3, "raw_data": {"A": 100.5, "B": 50.2}},
                    user_id=2,
                )

                assert err is None
                assert sample.weight == 50.3  # 100.5 - 50.2 = 50.3

            finally:
                for p in patches.values():
                    p.stop()

    def test_rejected_status_with_qc_fail(self, app):
        """When status is rejected with 'Failure' in reason, auto_error_reason should be qc_fail."""
        with app.app_context():
            patches = self._base_patches()
            mocks = {}
            for name, p in patches.items():
                mocks[name] = p.start()

            try:
                mocks["determine_result_status"].return_value = (
                    "rejected", "Control Failure: exceeded tolerance"
                )

                mocks["AnalysisResult"].query.filter_by.return_value.order_by.return_value.with_for_update.return_value.first.return_value = None
                mocks["AnalysisResultLog"].query.filter_by.return_value.order_by.return_value.first.return_value = None

                new_res = MagicMock()
                new_res.id = 101
                new_res.raw_data = {}
                new_res.final_result = 5.5
                new_res.set_raw_data = MagicMock()
                mocks["AnalysisResult"].return_value = new_res

                sample = _make_sample()
                mocks["db"].session.query.return_value.filter_by.return_value.with_for_update.return_value.first.return_value = sample

                from app.services.analysis_workflow import save_single_result
                result, err = save_single_result(
                    {"sample_id": 10, "analysis_code": "Mad",
                     "final_result": 5.5, "raw_data": {}},
                    user_id=2,
                )

                assert err is None
                assert result["status"] == "rejected"
                # Check AnalysisResult was constructed with error_reason="qc_fail"
                call_kwargs = mocks["AnalysisResult"].call_args[1]
                assert call_kwargs["error_reason"] == "qc_fail"

            finally:
                for p in patches.values():
                    p.stop()

    def test_repeat_analysis_logic(self, app):
        """When saving over an existing approved result, repeat info should be created."""
        with app.app_context():
            patches = self._base_patches()
            mocks = {}
            for name, p in patches.items():
                mocks[name] = p.start()

            try:
                existing = _make_result(id=50)

                mocks["AnalysisResult"].query.filter_by.return_value.order_by.return_value.with_for_update.return_value.first.return_value = existing

                # Simulate a previous approved log entry
                prev_log = MagicMock()
                prev_log.final_result_snapshot = 5.0
                prev_log.original_user_id = 2
                prev_log.original_timestamp = datetime(2026, 3, 9)
                prev_log.user_id = 2
                prev_log.timestamp = datetime(2026, 3, 9)

                log_query = MagicMock()
                log_query.filter_by.return_value = log_query
                log_query.filter.return_value = log_query
                log_query.first.side_effect = [prev_log, prev_log]  # prev_approved, then first_log
                log_query.order_by.return_value = log_query
                mocks["AnalysisResultLog"].query = log_query

                sample = _make_sample()
                mocks["db"].session.query.return_value.filter_by.return_value.with_for_update.return_value.first.return_value = sample

                from app.services.analysis_workflow import save_single_result
                result, err = save_single_result(
                    {"sample_id": 10, "analysis_code": "Mad",
                     "final_result": 5.5, "raw_data": {"m1": 1.0}},
                    user_id=2,
                )

                assert err is None
                assert result["success"] is True

            finally:
                for p in patches.values():
                    p.stop()

    def test_csn_diff_none_defaults_zero(self, app):
        """CSN analysis: when diff is None it should default to 0.0."""
        with app.app_context():
            patches = self._base_patches()
            mocks = {}
            for name, p in patches.items():
                mocks[name] = p.start()

            try:
                mocks["norm_code"].return_value = "CSN"
                mocks["validate_analysis_code"].return_value = ("CSN", None)
                mocks["normalize_raw_data"].return_value = {"avg": 4.0}
                mocks["to_float"].return_value = 4.0

                mocks["AnalysisResult"].query.filter_by.return_value.order_by.return_value.with_for_update.return_value.first.return_value = None
                mocks["AnalysisResultLog"].query.filter_by.return_value.order_by.return_value.first.return_value = None

                new_res = MagicMock()
                new_res.id = 102
                new_res.raw_data = {}
                new_res.final_result = 4.0
                new_res.set_raw_data = MagicMock()
                mocks["AnalysisResult"].return_value = new_res

                sample = _make_sample()
                mocks["db"].session.query.return_value.filter_by.return_value.with_for_update.return_value.first.return_value = sample

                # coalesce_diff_fn returns None -> CSN should default to 0.0
                from app.services.analysis_workflow import save_single_result
                result, err = save_single_result(
                    {"sample_id": 10, "analysis_code": "CSN",
                     "final_result": 4.0, "raw_data": {"avg": 4.0}},
                    user_id=2,
                    coalesce_diff_fn=lambda r: None,
                    effective_limit_fn=lambda c, a: (0.3, "abs", None),
                )

                assert err is None

            finally:
                for p in patches.values():
                    p.stop()

    def test_equipment_not_found(self, app):
        """When equipment_id is given but not found in DB, it should be set to None."""
        with app.app_context():
            patches = self._base_patches()
            mocks = {}
            for name, p in patches.items():
                mocks[name] = p.start()

            try:
                mocks["validate_equipment_id"].return_value = (99, None)

                with patch("app.services.analysis_workflow.EquipmentRepository") as mock_equip:
                    mock_equip.get_by_id.return_value = None

                    mocks["AnalysisResult"].query.filter_by.return_value.order_by.return_value.with_for_update.return_value.first.return_value = None
                    mocks["AnalysisResultLog"].query.filter_by.return_value.order_by.return_value.first.return_value = None

                    new_res = MagicMock()
                    new_res.id = 103
                    new_res.raw_data = {}
                    new_res.final_result = 5.5
                    new_res.set_raw_data = MagicMock()
                    mocks["AnalysisResult"].return_value = new_res

                    sample = _make_sample()
                    mocks["db"].session.query.return_value.filter_by.return_value.with_for_update.return_value.first.return_value = sample

                    from app.services.analysis_workflow import save_single_result
                    result, err = save_single_result(
                        {"sample_id": 10, "analysis_code": "Mad",
                         "final_result": 5.5, "raw_data": {},
                         "equipment_id": 99},
                        user_id=2,
                    )
                    assert err is None

            finally:
                for p in patches.values():
                    p.stop()

    def test_mad_required_overrides_approved(self, app):
        """If _mad_required is set and status is approved, it should be overridden to pending_review."""
        with app.app_context():
            patches = self._base_patches()
            mocks = {}
            for name, p in patches.items():
                mocks[name] = p.start()

            try:
                # normalize_raw_data returns data with _mad_required
                mocks["normalize_raw_data"].return_value = {
                    "m1": 1.0, "avg": 1.5, "diff": 0.1, "_mad_required": True,
                }
                mocks["determine_result_status"].return_value = ("approved", None)

                mocks["AnalysisResult"].query.filter_by.return_value.order_by.return_value.with_for_update.return_value.first.return_value = None
                mocks["AnalysisResultLog"].query.filter_by.return_value.order_by.return_value.first.return_value = None

                new_res = MagicMock()
                new_res.id = 104
                new_res.raw_data = {}
                new_res.final_result = 5.5
                new_res.set_raw_data = MagicMock()
                mocks["AnalysisResult"].return_value = new_res

                sample = _make_sample()
                mocks["db"].session.query.return_value.filter_by.return_value.with_for_update.return_value.first.return_value = sample

                from app.services.analysis_workflow import save_single_result
                result, err = save_single_result(
                    {"sample_id": 10, "analysis_code": "Mad",
                     "final_result": 5.5, "raw_data": {}},
                    user_id=2,
                )

                assert err is None
                assert result["status"] == "pending_review"

            finally:
                for p in patches.values():
                    p.stop()

    def test_gbw_failure_reason_replacement(self, app):
        """GBW rejected result should have 'Control Failure' replaced with 'GBW Failure'."""
        with app.app_context():
            patches = self._base_patches()
            mocks = {}
            for name, p in patches.items():
                mocks[name] = p.start()

            try:
                mocks["determine_result_status"].return_value = (
                    "rejected", "Control Failure: exceeded tolerance"
                )

                # Need to mock _process_control_gbw to return is_gbw=True
                with patch("app.services.analysis_workflow._process_control_gbw",
                           return_value=({"mean": 5.0}, 5.5, True)):

                    mocks["AnalysisResult"].query.filter_by.return_value.order_by.return_value.with_for_update.return_value.first.return_value = None
                    mocks["AnalysisResultLog"].query.filter_by.return_value.order_by.return_value.first.return_value = None

                    new_res = MagicMock()
                    new_res.id = 105
                    new_res.raw_data = {}
                    new_res.final_result = 5.5
                    new_res.set_raw_data = MagicMock()
                    mocks["AnalysisResult"].return_value = new_res

                    sample = _make_sample()
                    mocks["db"].session.query.return_value.filter_by.return_value.with_for_update.return_value.first.return_value = sample

                    from app.services.analysis_workflow import save_single_result
                    result, err = save_single_result(
                        {"sample_id": 10, "analysis_code": "Mad",
                         "final_result": 5.5, "raw_data": {}},
                        user_id=2,
                    )

                    assert err is None
                    assert "GBW Failure" in result["reason"]

            finally:
                for p in patches.values():
                    p.stop()
