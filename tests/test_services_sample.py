# tests/test_services_sample.py
# -*- coding: utf-8 -*-
"""Comprehensive tests for app/services/sample_service.py."""

from __future__ import annotations

import pytest
from datetime import datetime
from unittest.mock import patch, MagicMock, PropertyMock

from sqlalchemy.exc import SQLAlchemyError


# ---------------------------------------------------------------------------
# Fixtures & helpers
# ---------------------------------------------------------------------------

SAMPLE_SERVICE = "app.services.sample_service"


def _make_sample(id_=1, sample_code="S-001", lab_type="coal", status="new"):
    s = MagicMock()
    s.id = id_
    s.sample_code = sample_code
    s.lab_type = lab_type
    s.status = status
    return s


def _make_result(id_=10, sample_id=1, analysis_code="Mad", final_result=5.5,
                 status="approved", created_at=None):
    r = MagicMock()
    r.id = id_
    r.sample_id = sample_id
    r.analysis_code = analysis_code
    r.final_result = final_result
    r.status = status
    r.created_at = created_at or datetime(2026, 3, 1, 10, 0, 0)
    return r


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------

class TestDataClasses:
    def test_analysis_type_view(self):
        from app.services.sample_service import _AnalysisTypeView
        v = _AnalysisTypeView(code="Mad", name="Inherent Moisture")
        assert v.code == "Mad"
        assert v.name == "Inherent Moisture"

    def test_archive_result_defaults(self):
        from app.services.sample_service import ArchiveResult
        r = ArchiveResult(success=True, updated_count=3, message="ok")
        assert r.success is True
        assert r.updated_count == 3
        assert r.message == "ok"
        assert r.error is None

    def test_archive_result_with_error(self):
        from app.services.sample_service import ArchiveResult
        r = ArchiveResult(success=False, updated_count=0, message="fail", error="DB_ERR")
        assert r.error == "DB_ERR"

    def test_sample_report_data_defaults(self):
        from app.services.sample_service import SampleReportData
        s = _make_sample()
        r = SampleReportData(sample=s, calculations={"x": 1}, report_date=datetime.now())
        assert r.error is None
        assert r.calculations == {"x": 1}

    def test_sample_report_data_with_error(self):
        from app.services.sample_service import SampleReportData
        s = _make_sample()
        r = SampleReportData(sample=s, calculations={}, report_date=datetime.now(), error="ERR")
        assert r.error == "ERR"


# ---------------------------------------------------------------------------
# archive_samples
# ---------------------------------------------------------------------------

class TestArchiveSamples:
    @patch(f"{SAMPLE_SERVICE}.log_audit")
    @patch(f"{SAMPLE_SERVICE}.SampleRepository")
    def test_archive_success(self, mock_repo, mock_audit):
        from app.services.sample_service import archive_samples
        mock_repo.update_status.return_value = 2

        result = archive_samples([1, 2], archive=True)

        assert result.success is True
        assert result.updated_count == 2
        assert result.error is None
        mock_repo.update_status.assert_called_once_with([1, 2], "archived")
        assert mock_audit.call_count == 2
        # Verify audit args for first call
        call_args = mock_audit.call_args_list[0]
        assert call_args[1]["action"] == "sample_archived"
        assert call_args[1]["resource_type"] == "Sample"
        assert call_args[1]["resource_id"] == 1

    @patch(f"{SAMPLE_SERVICE}.log_audit")
    @patch(f"{SAMPLE_SERVICE}.SampleRepository")
    def test_unarchive_success(self, mock_repo, mock_audit):
        from app.services.sample_service import archive_samples
        mock_repo.update_status.return_value = 1

        result = archive_samples([5], archive=False)

        assert result.success is True
        assert result.updated_count == 1
        mock_repo.update_status.assert_called_once_with([5], "new")
        call_args = mock_audit.call_args_list[0]
        assert call_args[1]["action"] == "sample_unarchived"

    def test_empty_sample_ids(self):
        from app.services.sample_service import archive_samples
        result = archive_samples([])
        assert result.success is False
        assert result.updated_count == 0
        assert result.error == "NO_SAMPLES"

    def test_none_sample_ids_falsy(self):
        from app.services.sample_service import archive_samples
        # None is falsy, same branch
        result = archive_samples(None)  # type: ignore
        assert result.success is False
        assert result.error == "NO_SAMPLES"

    @patch(f"{SAMPLE_SERVICE}.db")
    @patch(f"{SAMPLE_SERVICE}.SampleRepository")
    def test_sqlalchemy_error_rollback(self, mock_repo, mock_db):
        from app.services.sample_service import archive_samples
        mock_repo.update_status.side_effect = SQLAlchemyError("connection lost")

        result = archive_samples([1, 2])

        assert result.success is False
        assert result.updated_count == 0
        assert result.error is not None
        assert "connection lost" in result.error
        mock_db.session.rollback.assert_called_once()

    @patch(f"{SAMPLE_SERVICE}.log_audit")
    @patch(f"{SAMPLE_SERVICE}.SampleRepository")
    def test_archive_multiple_ids_audit_each(self, mock_repo, mock_audit):
        from app.services.sample_service import archive_samples
        mock_repo.update_status.return_value = 3

        result = archive_samples([10, 20, 30], archive=True)
        assert result.success is True
        assert mock_audit.call_count == 3
        audit_ids = [c[1]["resource_id"] for c in mock_audit.call_args_list]
        assert audit_ids == [10, 20, 30]


# ---------------------------------------------------------------------------
# get_sample_report_data
# ---------------------------------------------------------------------------

class TestGetSampleReportData:
    @patch("app.utils.datetime.now_local")
    @patch(f"{SAMPLE_SERVICE}.calculate_all_conversions")
    @patch(f"{SAMPLE_SERVICE}.get_canonical_name")
    @patch(f"{SAMPLE_SERVICE}.AnalysisResultRepository")
    @patch(f"{SAMPLE_SERVICE}.SampleRepository")
    def test_success(self, mock_sample_repo, mock_result_repo,
                     mock_canonical, mock_calc, mock_now):
        from app.services.sample_service import get_sample_report_data
        sample = _make_sample(id_=1)
        mock_sample_repo.get_by_id.return_value = sample
        mock_result_repo.get_approved_by_sample.return_value = [
            _make_result(analysis_code="Mad", final_result=5.5),
        ]
        mock_canonical.return_value = "inherent_moisture"
        mock_calc.return_value = {"inherent_moisture": {"value": 5.5}}
        mock_now.return_value = datetime(2026, 3, 11)

        result = get_sample_report_data(1)

        assert result.error is None
        assert result.sample is sample
        assert result.calculations == {"inherent_moisture": {"value": 5.5}}
        assert result.report_date == datetime(2026, 3, 11)
        mock_sample_repo.get_by_id.assert_called_once_with(1)

    @patch("app.utils.datetime.now_local")
    @patch(f"{SAMPLE_SERVICE}.SampleRepository")
    def test_sample_not_found(self, mock_sample_repo, mock_now):
        from app.services.sample_service import get_sample_report_data
        mock_sample_repo.get_by_id.return_value = None
        mock_now.return_value = datetime(2026, 3, 11)

        result = get_sample_report_data(999)

        assert result.error == "SAMPLE_NOT_FOUND"
        assert result.sample is None
        assert result.calculations == {}

    @patch("app.utils.datetime.now_local")
    @patch(f"{SAMPLE_SERVICE}.calculate_all_conversions")
    @patch(f"{SAMPLE_SERVICE}.get_canonical_name")
    @patch(f"{SAMPLE_SERVICE}.AnalysisResultRepository")
    @patch(f"{SAMPLE_SERVICE}.SampleRepository")
    def test_calculation_error(self, mock_sample_repo, mock_result_repo,
                               mock_canonical, mock_calc, mock_now):
        from app.services.sample_service import get_sample_report_data
        sample = _make_sample()
        mock_sample_repo.get_by_id.return_value = sample
        mock_result_repo.get_approved_by_sample.return_value = [
            _make_result(),
        ]
        mock_canonical.return_value = "inherent_moisture"
        mock_calc.side_effect = ValueError("division issue")
        mock_now.return_value = datetime(2026, 3, 11)

        result = get_sample_report_data(1)

        assert result.error is not None
        assert "division issue" in result.error
        assert result.sample is sample
        assert result.calculations == {}

    @patch("app.utils.datetime.now_local")
    @patch(f"{SAMPLE_SERVICE}.calculate_all_conversions")
    @patch(f"{SAMPLE_SERVICE}.get_canonical_name")
    @patch(f"{SAMPLE_SERVICE}.AnalysisResultRepository")
    @patch(f"{SAMPLE_SERVICE}.SampleRepository")
    def test_calculation_type_error(self, mock_sample_repo, mock_result_repo,
                                     mock_canonical, mock_calc, mock_now):
        from app.services.sample_service import get_sample_report_data
        mock_sample_repo.get_by_id.return_value = _make_sample()
        mock_result_repo.get_approved_by_sample.return_value = [_make_result()]
        mock_canonical.return_value = "ash"
        mock_calc.side_effect = TypeError("bad type")
        mock_now.return_value = datetime(2026, 3, 11)

        result = get_sample_report_data(1)
        assert result.error is not None
        assert "bad type" in result.error

    @patch("app.utils.datetime.now_local")
    @patch(f"{SAMPLE_SERVICE}.calculate_all_conversions")
    @patch(f"{SAMPLE_SERVICE}.get_canonical_name")
    @patch(f"{SAMPLE_SERVICE}.AnalysisResultRepository")
    @patch(f"{SAMPLE_SERVICE}.SampleRepository")
    def test_calculation_key_error(self, mock_sample_repo, mock_result_repo,
                                    mock_canonical, mock_calc, mock_now):
        from app.services.sample_service import get_sample_report_data
        mock_sample_repo.get_by_id.return_value = _make_sample()
        mock_result_repo.get_approved_by_sample.return_value = [_make_result()]
        mock_canonical.return_value = "ash"
        mock_calc.side_effect = KeyError("missing_key")
        mock_now.return_value = datetime(2026, 3, 11)

        result = get_sample_report_data(1)
        assert result.error is not None

    @patch("app.utils.datetime.now_local")
    @patch(f"{SAMPLE_SERVICE}.calculate_all_conversions")
    @patch(f"{SAMPLE_SERVICE}.get_canonical_name")
    @patch(f"{SAMPLE_SERVICE}.AnalysisResultRepository")
    @patch(f"{SAMPLE_SERVICE}.SampleRepository")
    def test_calculation_zero_division(self, mock_sample_repo, mock_result_repo,
                                       mock_canonical, mock_calc, mock_now):
        from app.services.sample_service import get_sample_report_data
        mock_sample_repo.get_by_id.return_value = _make_sample()
        mock_result_repo.get_approved_by_sample.return_value = [_make_result()]
        mock_canonical.return_value = "ash"
        mock_calc.side_effect = ZeroDivisionError("div by zero")
        mock_now.return_value = datetime(2026, 3, 11)

        result = get_sample_report_data(1)
        assert result.error is not None
        assert "div by zero" in result.error

    @patch("app.utils.datetime.now_local")
    @patch(f"{SAMPLE_SERVICE}.calculate_all_conversions")
    @patch(f"{SAMPLE_SERVICE}.get_canonical_name")
    @patch(f"{SAMPLE_SERVICE}.AnalysisResultRepository")
    @patch(f"{SAMPLE_SERVICE}.SampleRepository")
    def test_no_results(self, mock_sample_repo, mock_result_repo,
                        mock_canonical, mock_calc, mock_now):
        from app.services.sample_service import get_sample_report_data
        sample = _make_sample()
        mock_sample_repo.get_by_id.return_value = sample
        mock_result_repo.get_approved_by_sample.return_value = []
        mock_calc.return_value = {}
        mock_now.return_value = datetime(2026, 3, 11)

        result = get_sample_report_data(1)

        assert result.error is None
        assert result.calculations == {}

    @patch("app.utils.datetime.now_local")
    @patch(f"{SAMPLE_SERVICE}.calculate_all_conversions")
    @patch(f"{SAMPLE_SERVICE}.get_canonical_name")
    @patch(f"{SAMPLE_SERVICE}.AnalysisResultRepository")
    @patch(f"{SAMPLE_SERVICE}.SampleRepository")
    def test_canonical_name_none_skipped(self, mock_sample_repo, mock_result_repo,
                                         mock_canonical, mock_calc, mock_now):
        """When get_canonical_name returns None, that result is skipped."""
        from app.services.sample_service import get_sample_report_data
        mock_sample_repo.get_by_id.return_value = _make_sample()
        mock_result_repo.get_approved_by_sample.return_value = [
            _make_result(analysis_code="UNKNOWN"),
        ]
        mock_canonical.return_value = None  # not recognized
        mock_calc.return_value = {}
        mock_now.return_value = datetime(2026, 3, 11)

        result = get_sample_report_data(1)

        assert result.error is None
        # raw_canonical_data should be empty since canonical was None
        mock_calc.assert_called_once()
        raw_data_arg = mock_calc.call_args[0][0]
        assert raw_data_arg == {}

    @patch("app.utils.datetime.now_local")
    @patch(f"{SAMPLE_SERVICE}.calculate_all_conversions")
    @patch(f"{SAMPLE_SERVICE}.get_canonical_name")
    @patch(f"{SAMPLE_SERVICE}.AnalysisResultRepository")
    @patch(f"{SAMPLE_SERVICE}.SampleRepository")
    def test_multiple_results_grouped(self, mock_sample_repo, mock_result_repo,
                                       mock_canonical, mock_calc, mock_now):
        """Multiple results with different codes are grouped by canonical name."""
        from app.services.sample_service import get_sample_report_data
        mock_sample_repo.get_by_id.return_value = _make_sample()
        r1 = _make_result(id_=10, analysis_code="Mad", final_result=5.5)
        r2 = _make_result(id_=11, analysis_code="Aad", final_result=12.3)
        mock_result_repo.get_approved_by_sample.return_value = [r1, r2]
        mock_canonical.side_effect = ["inherent_moisture", "ash"]
        mock_calc.return_value = {"inherent_moisture": {"value": 5.5}, "ash": {"value": 12.3}}
        mock_now.return_value = datetime(2026, 3, 11)

        result = get_sample_report_data(1)

        assert result.error is None
        raw_data_arg = mock_calc.call_args[0][0]
        assert "inherent_moisture" in raw_data_arg
        assert "ash" in raw_data_arg


# ---------------------------------------------------------------------------
# get_samples_with_results
# ---------------------------------------------------------------------------

class TestGetSamplesWithResults:
    @patch(f"{SAMPLE_SERVICE}.sort_samples")
    @patch(f"{SAMPLE_SERVICE}.db")
    def test_default_exclude_archived(self, mock_db, mock_sort):
        from app.services.sample_service import get_samples_with_results

        mock_query = MagicMock()
        mock_db.session.query.return_value.filter.return_value = mock_query
        mock_query.filter.return_value = mock_query
        samples = [_make_sample(id_=1), _make_sample(id_=2)]
        mock_query.all.return_value = samples
        mock_sort.return_value = samples

        result = get_samples_with_results()

        # exclude_archived=True by default, so filter is called again
        mock_query.filter.assert_called()
        mock_sort.assert_called_once_with(samples, by="full")
        assert result == samples

    @patch(f"{SAMPLE_SERVICE}.sort_samples")
    @patch(f"{SAMPLE_SERVICE}.db")
    def test_include_archived(self, mock_db, mock_sort):
        from app.services.sample_service import get_samples_with_results

        mock_query = MagicMock()
        mock_db.session.query.return_value.filter.return_value = mock_query
        samples = [_make_sample()]
        mock_query.all.return_value = samples
        mock_sort.return_value = samples

        result = get_samples_with_results(exclude_archived=False)

        mock_sort.assert_called_once_with(samples, by="full")
        assert result == samples

    @patch(f"{SAMPLE_SERVICE}.sort_samples")
    @patch(f"{SAMPLE_SERVICE}.db")
    def test_custom_sort(self, mock_db, mock_sort):
        from app.services.sample_service import get_samples_with_results

        mock_query = MagicMock()
        mock_db.session.query.return_value.filter.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = []
        mock_sort.return_value = []

        get_samples_with_results(sort_by="code")

        mock_sort.assert_called_once_with([], by="code")

    @patch(f"{SAMPLE_SERVICE}.sort_samples")
    @patch(f"{SAMPLE_SERVICE}.db")
    def test_empty_results(self, mock_db, mock_sort):
        from app.services.sample_service import get_samples_with_results

        mock_query = MagicMock()
        mock_db.session.query.return_value.filter.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = []
        mock_sort.return_value = []

        result = get_samples_with_results()
        assert result == []


# ---------------------------------------------------------------------------
# build_sample_summary_data
# ---------------------------------------------------------------------------

class TestBuildSampleSummaryData:
    def test_empty_samples(self):
        from app.services.sample_service import build_sample_summary_data
        result = build_sample_summary_data([])
        assert result == {
            "results_map": {},
            "analysis_dates_map": {},
            "analysis_types": []
        }

    @patch(f"{SAMPLE_SERVICE}._build_analysis_types")
    @patch(f"{SAMPLE_SERVICE}._map_to_template_codes")
    @patch(f"{SAMPLE_SERVICE}.calculate_all_conversions")
    @patch(f"{SAMPLE_SERVICE}.get_canonical_name")
    @patch(f"{SAMPLE_SERVICE}.AnalysisResultRepository")
    def test_single_sample_success(self, mock_result_repo, mock_canonical,
                                    mock_calc, mock_map, mock_build_types):
        from app.services.sample_service import build_sample_summary_data
        sample = _make_sample(id_=1)
        r1 = _make_result(sample_id=1, analysis_code="Mad", final_result=5.0,
                          created_at=datetime(2026, 3, 1))
        mock_result_repo.get_approved_by_sample_ids.return_value = [r1]
        mock_canonical.return_value = "inherent_moisture"
        mock_calc.return_value = {"inherent_moisture": {"value": 5.0}}
        mock_map.return_value = {"Mad": {"value": 5.0}}
        mock_build_types.return_value = [MagicMock(code="Mad", name="Moisture")]

        result = build_sample_summary_data([sample])

        assert 1 in result["results_map"]
        assert result["results_map"][1] == {"Mad": {"value": 5.0}}
        assert result["analysis_dates_map"][1] == "2026-03-01"
        assert len(result["analysis_types"]) == 1

    @patch(f"{SAMPLE_SERVICE}._build_analysis_types")
    @patch(f"{SAMPLE_SERVICE}._map_to_template_codes")
    @patch(f"{SAMPLE_SERVICE}.calculate_all_conversions")
    @patch(f"{SAMPLE_SERVICE}.get_canonical_name")
    @patch(f"{SAMPLE_SERVICE}.AnalysisResultRepository")
    def test_multiple_samples(self, mock_result_repo, mock_canonical,
                               mock_calc, mock_map, mock_build_types):
        from app.services.sample_service import build_sample_summary_data
        s1 = _make_sample(id_=1)
        s2 = _make_sample(id_=2)
        r1 = _make_result(sample_id=1, created_at=datetime(2026, 3, 1))
        r2 = _make_result(sample_id=2, created_at=datetime(2026, 3, 5))
        mock_result_repo.get_approved_by_sample_ids.return_value = [r1, r2]
        mock_canonical.return_value = "inherent_moisture"
        mock_calc.return_value = {"inherent_moisture": {"value": 5.0}}
        mock_map.return_value = {"Mad": {"value": 5.0}}
        mock_build_types.return_value = []

        result = build_sample_summary_data([s1, s2])

        assert 1 in result["results_map"]
        assert 2 in result["results_map"]
        assert result["analysis_dates_map"][1] == "2026-03-01"
        assert result["analysis_dates_map"][2] == "2026-03-05"

    @patch(f"{SAMPLE_SERVICE}._build_analysis_types")
    @patch(f"{SAMPLE_SERVICE}._map_to_template_codes")
    @patch(f"{SAMPLE_SERVICE}.calculate_all_conversions")
    @patch(f"{SAMPLE_SERVICE}.get_canonical_name")
    @patch(f"{SAMPLE_SERVICE}.AnalysisResultRepository")
    def test_calculation_error_graceful(self, mock_result_repo, mock_canonical,
                                        mock_calc, mock_map, mock_build_types):
        """Calculation error sets _calc_error flag and continues."""
        from app.services.sample_service import build_sample_summary_data
        sample = _make_sample(id_=1)
        r1 = _make_result(sample_id=1, analysis_code="Mad", final_result=5.0,
                          created_at=datetime(2026, 3, 1))
        mock_result_repo.get_approved_by_sample_ids.return_value = [r1]
        mock_canonical.return_value = "inherent_moisture"
        mock_calc.side_effect = ValueError("calc failed")
        # _map_to_template_codes receives fallback data with _calc_error
        mock_map.return_value = {"Mad": {"value": 5.0}}
        mock_build_types.return_value = []

        result = build_sample_summary_data([sample])

        # Should still have results (fallback with raw data)
        assert 1 in result["results_map"]
        # _map_to_template_codes was called with data containing _calc_error
        call_arg = mock_map.call_args[0][0]
        assert call_arg.get("_calc_error") is True

    @patch(f"{SAMPLE_SERVICE}._build_analysis_types")
    @patch(f"{SAMPLE_SERVICE}._map_to_template_codes")
    @patch(f"{SAMPLE_SERVICE}.calculate_all_conversions")
    @patch(f"{SAMPLE_SERVICE}.get_canonical_name")
    @patch(f"{SAMPLE_SERVICE}.AnalysisResultRepository")
    def test_no_dates_no_entry_in_dates_map(self, mock_result_repo, mock_canonical,
                                             mock_calc, mock_map, mock_build_types):
        """Sample with no created_at dates should not appear in analysis_dates_map."""
        from app.services.sample_service import build_sample_summary_data
        sample = _make_sample(id_=1)
        r1 = MagicMock()
        r1.sample_id = 1
        r1.analysis_code = "Mad"
        r1.final_result = 5.0
        r1.id = 10
        r1.status = "approved"
        r1.created_at = None  # explicitly None
        mock_result_repo.get_approved_by_sample_ids.return_value = [r1]
        mock_canonical.return_value = "inherent_moisture"
        mock_calc.return_value = {}
        mock_map.return_value = {}
        mock_build_types.return_value = []

        result = build_sample_summary_data([sample])

        assert 1 not in result["analysis_dates_map"]

    @patch(f"{SAMPLE_SERVICE}._build_analysis_types")
    @patch(f"{SAMPLE_SERVICE}._map_to_template_codes")
    @patch(f"{SAMPLE_SERVICE}.calculate_all_conversions")
    @patch(f"{SAMPLE_SERVICE}.get_canonical_name")
    @patch(f"{SAMPLE_SERVICE}.AnalysisResultRepository")
    def test_canonical_none_skipped(self, mock_result_repo, mock_canonical,
                                     mock_calc, mock_map, mock_build_types):
        """Results with None canonical name are skipped."""
        from app.services.sample_service import build_sample_summary_data
        sample = _make_sample(id_=1)
        r1 = _make_result(sample_id=1, analysis_code="UNKNOWN", created_at=datetime(2026, 1, 1))
        mock_result_repo.get_approved_by_sample_ids.return_value = [r1]
        mock_canonical.return_value = None
        mock_calc.return_value = {}
        mock_map.return_value = {}
        mock_build_types.return_value = []

        result = build_sample_summary_data([sample])

        raw_data_arg = mock_calc.call_args[0][0]
        assert raw_data_arg == {}

    @patch(f"{SAMPLE_SERVICE}._build_analysis_types")
    @patch(f"{SAMPLE_SERVICE}._map_to_template_codes")
    @patch(f"{SAMPLE_SERVICE}.calculate_all_conversions")
    @patch(f"{SAMPLE_SERVICE}.get_canonical_name")
    @patch(f"{SAMPLE_SERVICE}.AnalysisResultRepository")
    def test_multiple_dates_picks_latest(self, mock_result_repo, mock_canonical,
                                          mock_calc, mock_map, mock_build_types):
        """When multiple results, the latest date is used."""
        from app.services.sample_service import build_sample_summary_data
        sample = _make_sample(id_=1)
        r1 = _make_result(sample_id=1, analysis_code="Mad", created_at=datetime(2026, 1, 1))
        r2 = _make_result(sample_id=1, analysis_code="Aad", created_at=datetime(2026, 6, 15))
        mock_result_repo.get_approved_by_sample_ids.return_value = [r1, r2]
        mock_canonical.side_effect = ["inherent_moisture", "ash"]
        mock_calc.return_value = {}
        mock_map.return_value = {}
        mock_build_types.return_value = []

        result = build_sample_summary_data([sample])

        assert result["analysis_dates_map"][1] == "2026-06-15"

    @patch(f"{SAMPLE_SERVICE}._build_analysis_types")
    @patch(f"{SAMPLE_SERVICE}._map_to_template_codes")
    @patch(f"{SAMPLE_SERVICE}.calculate_all_conversions")
    @patch(f"{SAMPLE_SERVICE}.get_canonical_name")
    @patch(f"{SAMPLE_SERVICE}.AnalysisResultRepository")
    def test_type_error_in_calculation(self, mock_result_repo, mock_canonical,
                                        mock_calc, mock_map, mock_build_types):
        from app.services.sample_service import build_sample_summary_data
        sample = _make_sample(id_=1)
        mock_result_repo.get_approved_by_sample_ids.return_value = []
        mock_calc.side_effect = TypeError("type err")
        mock_map.return_value = {}
        mock_build_types.return_value = []

        result = build_sample_summary_data([sample])
        call_arg = mock_map.call_args[0][0]
        assert call_arg.get("_calc_error") is True

    @patch(f"{SAMPLE_SERVICE}._build_analysis_types")
    @patch(f"{SAMPLE_SERVICE}._map_to_template_codes")
    @patch(f"{SAMPLE_SERVICE}.calculate_all_conversions")
    @patch(f"{SAMPLE_SERVICE}.get_canonical_name")
    @patch(f"{SAMPLE_SERVICE}.AnalysisResultRepository")
    def test_zero_division_in_calculation(self, mock_result_repo, mock_canonical,
                                           mock_calc, mock_map, mock_build_types):
        from app.services.sample_service import build_sample_summary_data
        sample = _make_sample(id_=1)
        mock_result_repo.get_approved_by_sample_ids.return_value = []
        mock_calc.side_effect = ZeroDivisionError("zero div")
        mock_map.return_value = {}
        mock_build_types.return_value = []

        result = build_sample_summary_data([sample])
        call_arg = mock_map.call_args[0][0]
        assert call_arg.get("_calc_error") is True

    @patch(f"{SAMPLE_SERVICE}._build_analysis_types")
    @patch(f"{SAMPLE_SERVICE}._map_to_template_codes")
    @patch(f"{SAMPLE_SERVICE}.calculate_all_conversions")
    @patch(f"{SAMPLE_SERVICE}.get_canonical_name")
    @patch(f"{SAMPLE_SERVICE}.AnalysisResultRepository")
    def test_key_error_in_calculation(self, mock_result_repo, mock_canonical,
                                       mock_calc, mock_map, mock_build_types):
        from app.services.sample_service import build_sample_summary_data
        sample = _make_sample(id_=1)
        mock_result_repo.get_approved_by_sample_ids.return_value = []
        mock_calc.side_effect = KeyError("key err")
        mock_map.return_value = {}
        mock_build_types.return_value = []

        result = build_sample_summary_data([sample])
        call_arg = mock_map.call_args[0][0]
        assert call_arg.get("_calc_error") is True


# ---------------------------------------------------------------------------
# _map_to_template_codes
# ---------------------------------------------------------------------------

class TestMapToTemplateCodes:
    @patch(f"{SAMPLE_SERVICE}.get_canonical_name")
    @patch(f"{SAMPLE_SERVICE}.SUMMARY_VIEW_COLUMNS", [
        {"code": "Ad", "canonical_base": "ash"},
    ])
    def test_direct_canonical_mapping(self, mock_canonical):
        """'Ad' is in CANONICAL_TO_TEMPLATE -> maps to 'ash_d'."""
        from app.services.sample_service import _map_to_template_codes
        # Ad -> lookup_key = TEMPLATE_TO_CANONICAL["Ad"] = "ash_d"
        data = {"ash_d": {"value": 10.5}}
        result = _map_to_template_codes(data)
        assert result.get("Ad") == {"value": 10.5}

    @patch(f"{SAMPLE_SERVICE}.get_canonical_name")
    @patch(f"{SAMPLE_SERVICE}.SUMMARY_VIEW_COLUMNS", [
        {"code": "Mad", "canonical_base": "inherent_moisture"},
    ])
    def test_fallback_canonical_name_lookup(self, mock_canonical):
        """Code not in CANONICAL_TO_TEMPLATE -> falls back to get_canonical_name."""
        from app.services.sample_service import _map_to_template_codes
        mock_canonical.return_value = "inherent_moisture"
        data = {"inherent_moisture": {"value": 5.0}}
        result = _map_to_template_codes(data)
        assert result.get("Mad") == {"value": 5.0}

    @patch(f"{SAMPLE_SERVICE}.get_canonical_name")
    @patch(f"{SAMPLE_SERVICE}.SUMMARY_VIEW_COLUMNS", [
        {"code": "XYZ"},
    ])
    def test_no_canonical_base_uses_code(self, mock_canonical):
        """When canonical_base is missing, uses code for get_canonical_name."""
        from app.services.sample_service import _map_to_template_codes
        mock_canonical.return_value = None
        data = {"something": {"value": 1}}
        result = _map_to_template_codes(data)
        assert result == {}
        mock_canonical.assert_called_with("XYZ")

    @patch(f"{SAMPLE_SERVICE}.get_canonical_name")
    @patch(f"{SAMPLE_SERVICE}.SUMMARY_VIEW_COLUMNS", [
        {"code": "Mad", "canonical_base": "inherent_moisture"},
    ])
    def test_key_not_in_data(self, mock_canonical):
        """Even if lookup_key is found, if not in data -> not included."""
        from app.services.sample_service import _map_to_template_codes
        mock_canonical.return_value = "inherent_moisture"
        data = {"ash": {"value": 10}}  # no inherent_moisture
        result = _map_to_template_codes(data)
        assert "Mad" not in result

    @patch(f"{SAMPLE_SERVICE}.get_canonical_name")
    @patch(f"{SAMPLE_SERVICE}.SUMMARY_VIEW_COLUMNS", [
        {"code": "Vdaf", "canonical_base": "volatile_matter"},
    ])
    def test_vdaf_direct_mapping(self, mock_canonical):
        """'Vdaf' is in CANONICAL_TO_TEMPLATE -> volatile_matter_daf."""
        from app.services.sample_service import _map_to_template_codes
        data = {"volatile_matter_daf": {"value": 30.0}}
        result = _map_to_template_codes(data)
        assert result.get("Vdaf") == {"value": 30.0}

    @patch(f"{SAMPLE_SERVICE}.get_canonical_name")
    @patch(f"{SAMPLE_SERVICE}.SUMMARY_VIEW_COLUMNS", [])
    def test_empty_columns(self, mock_canonical):
        from app.services.sample_service import _map_to_template_codes
        result = _map_to_template_codes({"x": 1})
        assert result == {}

    @patch(f"{SAMPLE_SERVICE}.get_canonical_name")
    @patch(f"{SAMPLE_SERVICE}.SUMMARY_VIEW_COLUMNS", [
        {"code": "St,d", "canonical_base": "total_sulfur"},
        {"code": "Qgr,daf", "canonical_base": "calorific_value"},
        {"code": "Qnet,ar", "canonical_base": "calorific_value"},
        {"code": "FC,ad", "canonical_base": "fixed_carbon_ad"},
        {"code": "FC,d", "canonical_base": "fixed_carbon_ad"},
        {"code": "FC,daf", "canonical_base": "fixed_carbon_ad"},
        {"code": "St,daf", "canonical_base": "total_sulfur"},
        {"code": "TRD,ad", "canonical_base": "relative_density"},
        {"code": "TRD,d", "canonical_base": "relative_density"},
        {"code": "H,d", "canonical_base": "hydrogen"},
        {"code": "P,d", "canonical_base": "phosphorus"},
        {"code": "F,d", "canonical_base": "total_fluorine"},
        {"code": "Cl,d", "canonical_base": "total_chlorine"},
    ])
    def test_all_canonical_to_template_entries(self, mock_canonical):
        """Test all entries in CANONICAL_TO_TEMPLATE mapping."""
        from app.services.sample_service import _map_to_template_codes
        data = {
            "total_sulfur_d": {"value": 0.5},
            "calorific_value_daf": {"value": 7500},
            "qnet_ar": {"value": 6000},
            "fixed_carbon_ad": {"value": 55.0},
            "fixed_carbon_d": {"value": 56.0},
            "fixed_carbon_daf": {"value": 57.0},
            "total_sulfur_daf": {"value": 0.6},
            "relative_density": {"value": 1.3},
            "relative_density_d": {"value": 1.35},
            "hydrogen_d": {"value": 4.5},
            "phosphorus_d": {"value": 0.01},
            "total_fluorine_d": {"value": 0.02},
            "total_chlorine_d": {"value": 0.03},
        }
        result = _map_to_template_codes(data)
        assert result["St,d"] == {"value": 0.5}
        assert result["Qnet,ar"] == {"value": 6000}
        assert result["FC,ad"] == {"value": 55.0}
        assert result["FC,d"] == {"value": 56.0}
        assert result["FC,daf"] == {"value": 57.0}
        assert result["St,daf"] == {"value": 0.6}
        assert result["TRD,ad"] == {"value": 1.3}
        assert result["TRD,d"] == {"value": 1.35}
        assert result["H,d"] == {"value": 4.5}
        assert result["P,d"] == {"value": 0.01}
        assert result["F,d"] == {"value": 0.02}
        assert result["Cl,d"] == {"value": 0.03}


# ---------------------------------------------------------------------------
# _build_analysis_types
# ---------------------------------------------------------------------------

class TestBuildAnalysisTypes:
    @patch(f"{SAMPLE_SERVICE}.PARAMETER_DEFINITIONS", {
        "inherent_moisture": {"display_name": "Inherent Moisture"},
        "ash": {"display_name": "Ash Content"},
    })
    @patch(f"{SAMPLE_SERVICE}.SUMMARY_VIEW_COLUMNS", [
        {"code": "Mad", "canonical_base": "inherent_moisture"},
        {"code": "Aad", "canonical_base": "ash"},
    ])
    def test_with_display_names(self):
        from app.services.sample_service import _build_analysis_types
        result = _build_analysis_types()
        assert len(result) == 2
        assert result[0].code == "Mad"
        assert result[0].name == "Inherent Moisture"
        assert result[1].code == "Aad"
        assert result[1].name == "Ash Content"

    @patch(f"{SAMPLE_SERVICE}.PARAMETER_DEFINITIONS", {})
    @patch(f"{SAMPLE_SERVICE}.SUMMARY_VIEW_COLUMNS", [
        {"code": "XYZ", "canonical_base": "unknown_param"},
    ])
    def test_no_param_definition_uses_code(self):
        from app.services.sample_service import _build_analysis_types
        result = _build_analysis_types()
        assert len(result) == 1
        assert result[0].code == "XYZ"
        assert result[0].name == "XYZ"  # falls back to code

    @patch(f"{SAMPLE_SERVICE}.PARAMETER_DEFINITIONS", {
        "some_param": {},  # no display_name key
    })
    @patch(f"{SAMPLE_SERVICE}.SUMMARY_VIEW_COLUMNS", [
        {"code": "SP", "canonical_base": "some_param"},
    ])
    def test_param_exists_but_no_display_name(self):
        from app.services.sample_service import _build_analysis_types
        result = _build_analysis_types()
        assert result[0].name == "SP"  # falls back to code

    @patch(f"{SAMPLE_SERVICE}.PARAMETER_DEFINITIONS", {
        "some_param": {"display_name": ""},  # empty display_name
    })
    @patch(f"{SAMPLE_SERVICE}.SUMMARY_VIEW_COLUMNS", [
        {"code": "SP", "canonical_base": "some_param"},
    ])
    def test_empty_display_name_uses_code(self):
        from app.services.sample_service import _build_analysis_types
        result = _build_analysis_types()
        assert result[0].name == "SP"  # empty string is falsy

    @patch(f"{SAMPLE_SERVICE}.PARAMETER_DEFINITIONS", {})
    @patch(f"{SAMPLE_SERVICE}.SUMMARY_VIEW_COLUMNS", [])
    def test_empty_columns(self):
        from app.services.sample_service import _build_analysis_types
        result = _build_analysis_types()
        assert result == []

    @patch(f"{SAMPLE_SERVICE}.PARAMETER_DEFINITIONS", {})
    @patch(f"{SAMPLE_SERVICE}.SUMMARY_VIEW_COLUMNS", [
        {"code": "NoBase"},  # no canonical_base key
    ])
    def test_no_canonical_base_key(self):
        from app.services.sample_service import _build_analysis_types
        result = _build_analysis_types()
        assert len(result) == 1
        assert result[0].code == "NoBase"
        assert result[0].name == "NoBase"
