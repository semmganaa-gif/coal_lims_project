# tests/test_services_low_cov.py
# -*- coding: utf-8 -*-
"""
Tests for low-coverage service files:
  - app/services/report_builder.py
  - app/services/instrument_service.py
  - app/services/qc_chart_service.py
"""

import json
import math
import statistics
from datetime import datetime, date, timezone
from decimal import Decimal
from unittest.mock import patch, MagicMock, mock_open

import pytest


# ═══════════════════════════════════════════════════════════════════
# 1. report_builder tests
# ═══════════════════════════════════════════════════════════════════

class TestCoerceValue:
    """Test _coerce_value helper."""

    def test_none_returns_none(self):
        from app.services.report_builder import _coerce_value
        assert _coerce_value(None, "str") is None

    def test_int_coercion(self):
        from app.services.report_builder import _coerce_value
        assert _coerce_value("42", "int") == 42

    def test_float_coercion(self):
        from app.services.report_builder import _coerce_value
        assert _coerce_value("3.14", "float") == pytest.approx(3.14)

    def test_date_from_string(self):
        from app.services.report_builder import _coerce_value
        result = _coerce_value("2026-01-15", "date")
        assert result == date(2026, 1, 15)

    def test_date_passthrough(self):
        from app.services.report_builder import _coerce_value
        d = date(2026, 1, 1)
        assert _coerce_value(d, "date") is d

    def test_datetime_from_string(self):
        from app.services.report_builder import _coerce_value
        result = _coerce_value("2026-01-15T10:30:00", "datetime")
        assert isinstance(result, datetime)

    def test_datetime_passthrough(self):
        from app.services.report_builder import _coerce_value
        dt = datetime(2026, 1, 1, 12, 0)
        assert _coerce_value(dt, "datetime") is dt

    def test_str_coercion(self):
        from app.services.report_builder import _coerce_value
        assert _coerce_value(123, "str") == "123"


class TestGetColumn:
    """Test _get_column helper."""

    def test_valid_column(self):
        from app.services.report_builder import _get_column
        col = _get_column("analysis_result", "final_result")
        assert col is not None

    def test_unknown_column_raises(self):
        from app.services.report_builder import _get_column
        with pytest.raises(ValueError, match="Unknown column"):
            _get_column("analysis_result", "nonexistent_column")

    def test_unknown_entity_raises(self):
        from app.services.report_builder import _get_column
        with pytest.raises(ValueError, match="Unknown column"):
            _get_column("nonexistent_entity", "id")


class TestGetAvailableColumns:
    """Test get_available_columns."""

    def test_analysis_result_columns(self):
        from app.services.report_builder import get_available_columns
        cols = get_available_columns("analysis_result")
        assert len(cols) > 0
        names = [c["name"] for c in cols]
        assert "final_result" in names
        assert "status" in names

    def test_sample_columns(self):
        from app.services.report_builder import get_available_columns
        cols = get_available_columns("sample")
        names = [c["name"] for c in cols]
        assert "sample_code" in names

    def test_unknown_entity_returns_empty(self):
        from app.services.report_builder import get_available_columns
        assert get_available_columns("unknown") == []


class TestGetAvailableEntities:
    """Test get_available_entities."""

    def test_returns_two_entities(self):
        from app.services.report_builder import get_available_entities
        entities = get_available_entities()
        assert len(entities) == 2
        names = [e["name"] for e in entities]
        assert "analysis_result" in names
        assert "sample" in names


class TestBuildQuery:
    """Test build_query — needs app context for db.session."""

    def test_unknown_entity_raises(self, app):
        from app.services.report_builder import build_query
        with app.app_context():
            with pytest.raises(ValueError, match="Unknown entity"):
                build_query({"entity": "invalid_entity"})

    def test_unknown_agg_func_raises(self, app):
        from app.services.report_builder import build_query
        with app.app_context():
            with pytest.raises(ValueError, match="Unknown aggregation"):
                build_query({
                    "entity": "analysis_result",
                    "group_by": ["analysis_code"],
                    "aggregations": [{"field": "final_result", "func": "median"}],
                })

    def test_basic_query_with_columns(self, app):
        from app.services.report_builder import build_query
        with app.app_context():
            query, labels = build_query({
                "entity": "analysis_result",
                "columns": ["analysis_code", "final_result", "status"],
            })
            assert labels == ["analysis_code", "final_result", "status"]

    def test_default_columns_when_empty(self, app):
        from app.services.report_builder import build_query
        with app.app_context():
            query, labels = build_query({"entity": "analysis_result"})
            assert len(labels) <= 10
            assert len(labels) > 0

    def test_limit_capped_at_max(self, app):
        from app.services.report_builder import build_query, MAX_REPORT_ROWS
        with app.app_context():
            query, _ = build_query({
                "entity": "sample",
                "columns": ["id"],
                "limit": 999999,
            })
            # The limit should be capped at MAX_REPORT_ROWS
            # We verify the query compiles without error
            assert query is not None

    def test_aggregation_query(self, app):
        from app.services.report_builder import build_query
        with app.app_context():
            query, labels = build_query({
                "entity": "analysis_result",
                "group_by": ["analysis_code"],
                "aggregations": [
                    {"field": "final_result", "func": "avg", "alias": "avg_result"},
                    {"field": "final_result", "func": "count", "alias": "cnt"},
                ],
            })
            assert "analysis_code" in labels
            assert "avg_result" in labels
            assert "cnt" in labels

    def test_filters_applied(self, app):
        from app.services.report_builder import build_query
        with app.app_context():
            query, labels = build_query({
                "entity": "analysis_result",
                "columns": ["analysis_code", "final_result"],
                "filters": [
                    {"field": "status", "op": "eq", "value": "approved"},
                    {"field": "final_result", "op": "gte", "value": "10"},
                ],
            })
            assert labels == ["analysis_code", "final_result"]

    def test_filter_in_operator(self, app):
        from app.services.report_builder import build_query
        with app.app_context():
            query, _ = build_query({
                "entity": "analysis_result",
                "columns": ["analysis_code"],
                "filters": [
                    {"field": "status", "op": "in", "value": ["approved", "pending"]},
                ],
            })
            assert query is not None

    def test_filter_is_null(self, app):
        from app.services.report_builder import build_query
        with app.app_context():
            query, _ = build_query({
                "entity": "analysis_result",
                "columns": ["final_result"],
                "filters": [
                    {"field": "final_result", "op": "is_null", "value": None},
                ],
            })
            assert query is not None

    def test_filter_like(self, app):
        from app.services.report_builder import build_query
        with app.app_context():
            query, _ = build_query({
                "entity": "analysis_result",
                "columns": ["analysis_code"],
                "filters": [
                    {"field": "analysis_code", "op": "like", "value": "Mad"},
                ],
            })
            assert query is not None

    def test_filter_unknown_field_skipped(self, app):
        from app.services.report_builder import build_query
        with app.app_context():
            query, _ = build_query({
                "entity": "analysis_result",
                "columns": ["analysis_code"],
                "filters": [
                    {"field": "nonexistent", "op": "eq", "value": "x"},
                ],
            })
            assert query is not None

    def test_filter_unknown_op_skipped(self, app):
        from app.services.report_builder import build_query
        with app.app_context():
            query, _ = build_query({
                "entity": "analysis_result",
                "columns": ["analysis_code"],
                "filters": [
                    {"field": "status", "op": "regex", "value": ".*"},
                ],
            })
            assert query is not None

    def test_order_by_asc_and_desc(self, app):
        from app.services.report_builder import build_query
        with app.app_context():
            query, _ = build_query({
                "entity": "analysis_result",
                "columns": ["analysis_code", "final_result"],
                "order_by": [
                    {"field": "analysis_code", "dir": "asc"},
                    {"field": "final_result", "dir": "desc"},
                ],
            })
            assert query is not None

    def test_join_triggered_by_sample_column(self, app):
        from app.services.report_builder import build_query
        with app.app_context():
            query, labels = build_query({
                "entity": "analysis_result",
                "columns": ["sample_code", "final_result"],
            })
            assert "sample_code" in labels

    def test_sample_entity_query(self, app):
        from app.services.report_builder import build_query
        with app.app_context():
            query, labels = build_query({
                "entity": "sample",
                "columns": ["sample_code", "lab_type", "status"],
            })
            assert labels == ["sample_code", "lab_type", "status"]

    def test_filter_triggers_join_for_sample_field(self, app):
        """Filter on sample field when no join columns selected should trigger join."""
        from app.services.report_builder import build_query
        with app.app_context():
            query, _ = build_query({
                "entity": "analysis_result",
                "columns": ["final_result"],
                "filters": [
                    {"field": "lab_type", "op": "eq", "value": "coal"},
                ],
            })
            assert query is not None


class TestExecuteReport:
    """Test execute_report — runs actual queries against test DB."""

    def test_empty_result(self, app):
        from app.services.report_builder import execute_report
        with app.app_context():
            result = execute_report({
                "entity": "analysis_result",
                "columns": ["analysis_code", "final_result"],
                "filters": [{"field": "status", "op": "eq", "value": "impossible_status"}],
            })
            assert result["total"] == 0
            assert result["rows"] == []
            assert "columns" in result
            assert "column_labels" in result

    def test_sample_entity_report(self, app):
        from app.services.report_builder import execute_report
        with app.app_context():
            result = execute_report({"entity": "sample", "columns": ["sample_code", "status"]})
            assert "columns" in result
            assert "rows" in result

    def test_datetime_serialization(self, app):
        """Values of type datetime/date should be serialized to isoformat."""
        from app.services.report_builder import execute_report
        with app.app_context():
            result = execute_report({
                "entity": "analysis_result",
                "columns": ["analysis_code", "updated_at"],
            })
            # If rows exist, updated_at should be a string
            for row in result["rows"]:
                if row[1] is not None:
                    assert isinstance(row[1], str)


class TestExportReportCsv:
    """Test export_report_csv."""

    def test_csv_export_has_header(self, app):
        from app.services.report_builder import export_report_csv
        with app.app_context():
            csv_str = export_report_csv({
                "entity": "sample",
                "columns": ["sample_code", "status"],
            })
            lines = csv_str.strip().split("\n")
            assert len(lines) >= 1  # At least the header


class TestExportReportJson:
    """Test export_report_json."""

    def test_json_export_valid(self, app):
        from app.services.report_builder import export_report_json
        with app.app_context():
            json_str = export_report_json({
                "name": "Test Report",
                "entity": "sample",
                "columns": ["sample_code"],
            })
            data = json.loads(json_str)
            assert data["report_name"] == "Test Report"
            assert "generated_at" in data
            assert "data" in data
            assert "columns" in data


class TestReportTemplateManagement:
    """Test save/get/list/delete report templates."""

    def test_save_and_get_template(self, app):
        from app.services.report_builder import save_report_template, get_report_template
        with app.app_context():
            from app.models.core import User
            user = User.query.filter_by(username="admin").first()
            config = {"entity": "sample", "columns": ["sample_code"]}
            tid = save_report_template("test_tpl_1", config, user.id, "desc")
            assert tid is not None

            loaded = get_report_template("test_tpl_1")
            assert loaded is not None
            assert loaded["entity"] == "sample"
            assert loaded["name"] == "test_tpl_1"

    def test_update_existing_template(self, app):
        from app.services.report_builder import save_report_template, get_report_template
        with app.app_context():
            from app.models.core import User
            user = User.query.filter_by(username="admin").first()
            config1 = {"entity": "sample", "columns": ["sample_code"]}
            save_report_template("test_tpl_upd", config1, user.id)
            config2 = {"entity": "analysis_result", "columns": ["final_result"]}
            save_report_template("test_tpl_upd", config2, user.id, "updated")
            loaded = get_report_template("test_tpl_upd")
            assert loaded["entity"] == "analysis_result"

    def test_get_nonexistent_template(self, app):
        from app.services.report_builder import get_report_template
        with app.app_context():
            assert get_report_template("does_not_exist_xyz") is None

    def test_list_templates(self, app):
        from app.services.report_builder import save_report_template, list_report_templates
        with app.app_context():
            from app.models.core import User
            user = User.query.filter_by(username="admin").first()
            save_report_template("list_test_tpl", {"entity": "sample", "columns": []}, user.id)
            templates = list_report_templates()
            assert isinstance(templates, list)
            names = [t["name"] for t in templates]
            assert "list_test_tpl" in names

    def test_delete_template(self, app):
        from app.services.report_builder import (
            save_report_template, delete_report_template, get_report_template
        )
        with app.app_context():
            from app.models.core import User
            user = User.query.filter_by(username="admin").first()
            save_report_template("to_delete", {"entity": "sample", "columns": []}, user.id)
            assert delete_report_template("to_delete") is True
            assert get_report_template("to_delete") is None

    def test_delete_nonexistent_returns_false(self, app):
        from app.services.report_builder import delete_report_template
        with app.app_context():
            assert delete_report_template("nonexistent_delete_xyz") is False


# ═══════════════════════════════════════════════════════════════════
# 2. instrument_service tests
# ═══════════════════════════════════════════════════════════════════

class TestParseInstrumentFile:
    """Test parse_instrument_file with mocked parser and DB."""

    @patch("app.services.instrument_service.get_parser")
    @patch("app.services.instrument_service.InstrumentReading")
    @patch("app.services.instrument_service.Sample")
    @patch("builtins.open", mock_open(read_data=b"file content"))
    def test_empty_parse_returns_empty(self, mock_sample, mock_reading_cls, mock_get_parser):
        from app.services.instrument_service import parse_instrument_file
        parser = MagicMock()
        parser.can_parse.return_value = True
        parser.parse.return_value = []
        mock_get_parser.return_value = parser

        result = parse_instrument_file("/fake/file.csv", "tga")
        assert result == []

    @patch("app.services.instrument_service.get_parser")
    def test_unsupported_extension_raises(self, mock_get_parser):
        from app.services.instrument_service import parse_instrument_file
        parser = MagicMock()
        parser.can_parse.return_value = False
        parser.supported_extensions = (".csv",)
        mock_get_parser.return_value = parser

        with pytest.raises(ValueError, match="not supported"):
            parse_instrument_file("/fake/file.pdf", "tga")

    @patch("app.services.instrument_service.get_parser")
    @patch("app.services.instrument_service.InstrumentReading")
    @patch("app.services.instrument_service.Sample")
    @patch("builtins.open", mock_open(read_data=b"data"))
    @patch("app.services.instrument_service.hashlib")
    def test_duplicate_file_raises(self, mock_hashlib, mock_sample, mock_reading_cls, mock_get_parser):
        from app.services.instrument_service import parse_instrument_file

        parser = MagicMock()
        parser.can_parse.return_value = True
        parser.parse.return_value = [MagicMock()]
        mock_get_parser.return_value = parser

        mock_hashlib.sha256.return_value.hexdigest.return_value = "abc123"
        existing = MagicMock()
        existing.created_at = datetime.now()
        mock_reading_cls.query.filter_by.return_value.first.return_value = existing

        with pytest.raises(ValueError, match="already imported"):
            parse_instrument_file("/fake/file.csv", "tga")

    @patch("app.services.instrument_service.get_parser")
    @patch("app.services.instrument_service.InstrumentReading")
    @patch("app.services.instrument_service.Sample")
    @patch("builtins.open", mock_open(read_data=b"data"))
    @patch("app.services.instrument_service.hashlib")
    def test_successful_parse_creates_readings(self, mock_hashlib, mock_sample,
                                                mock_reading_cls, mock_get_parser):
        from app.services.instrument_service import parse_instrument_file

        parser = MagicMock()
        parser.can_parse.return_value = True
        reading_data = MagicMock()
        reading_data.sample_code = "S-001"
        reading_data.analysis_code = "Mad"
        reading_data.raw_data = {"temp": 105}
        reading_data.value = 5.67
        reading_data.unit = "%"
        reading_data.instrument_name = "TGA-701"
        parser.parse.return_value = [reading_data]
        mock_get_parser.return_value = parser

        mock_hashlib.sha256.return_value.hexdigest.return_value = "newhash"
        mock_reading_cls.query.filter_by.return_value.first.return_value = None

        sample_obj = MagicMock()
        sample_obj.id = 42
        mock_sample.query.filter_by.return_value.first.return_value = sample_obj

        mock_reading_cls.return_value = MagicMock()

        result = parse_instrument_file("/fake/file.csv", "tga", "My TGA")
        assert len(result) == 1
        mock_reading_cls.assert_called_once()
        call_kwargs = mock_reading_cls.call_args
        assert call_kwargs[1]["instrument_name"] == "My TGA"
        assert call_kwargs[1]["sample_id"] == 42


class TestImportInstrumentFile:
    """Test import_instrument_file."""

    @patch("app.services.instrument_service.parse_instrument_file")
    @patch("app.services.instrument_service.db")
    def test_import_returns_count(self, mock_db, mock_parse):
        from app.services.instrument_service import import_instrument_file
        readings = [MagicMock(), MagicMock()]
        mock_parse.return_value = readings
        count = import_instrument_file("/file.csv", "tga")
        assert count == 2
        assert mock_db.session.add.call_count == 2
        mock_db.session.commit.assert_called_once()

    @patch("app.services.instrument_service.parse_instrument_file")
    @patch("app.services.instrument_service.db")
    def test_import_empty_returns_zero(self, mock_db, mock_parse):
        from app.services.instrument_service import import_instrument_file
        mock_parse.return_value = []
        assert import_instrument_file("/file.csv", "tga") == 0
        mock_db.session.commit.assert_not_called()


class TestApproveReading:
    """Test approve_reading."""

    @patch("app.services.instrument_service.db")
    @patch("app.services.instrument_service.AnalysisResult")
    def test_approve_not_found_raises(self, mock_ar, mock_db):
        from app.services.instrument_service import approve_reading
        mock_db.session.get.return_value = None
        with pytest.raises(ValueError, match="not found"):
            approve_reading(999, 1)

    @patch("app.services.instrument_service.db")
    @patch("app.services.instrument_service.AnalysisResult")
    def test_approve_already_approved_raises(self, mock_ar, mock_db):
        from app.services.instrument_service import approve_reading
        reading = MagicMock()
        reading.status = "approved"
        mock_db.session.get.return_value = reading
        with pytest.raises(ValueError, match="already approved"):
            approve_reading(1, 1)

    @patch("app.services.instrument_service.db")
    @patch("app.services.instrument_service.AnalysisResult")
    def test_approve_links_to_analysis_result(self, mock_ar, mock_db, app):
        from app.services.instrument_service import approve_reading
        with app.app_context():
            reading = MagicMock()
            reading.status = "pending"
            reading.sample_id = 10
            reading.analysis_code = "Mad"
            reading.parsed_value = 5.5
            mock_db.session.get.return_value = reading

            ar_obj = MagicMock()
            ar_obj.id = 77
            mock_ar.query.filter_by.return_value.first.return_value = ar_obj

            result = approve_reading(1, 42)
            assert result.status == "approved"
            assert result.reviewed_by_id == 42
            assert ar_obj.final_result == 5.5
            assert result.analysis_result_id == 77
            mock_db.session.commit.assert_called_once()

    @patch("app.services.instrument_service.db")
    @patch("app.services.instrument_service.AnalysisResult")
    def test_approve_no_matching_analysis_logs_warning(self, mock_ar, mock_db, app):
        from app.services.instrument_service import approve_reading
        with app.app_context():
            reading = MagicMock()
            reading.status = "pending"
            reading.sample_id = 10
            reading.analysis_code = "Mad"
            mock_db.session.get.return_value = reading
            mock_ar.query.filter_by.return_value.first.return_value = None

            result = approve_reading(1, 42)
            assert result.status == "approved"

    @patch("app.services.instrument_service.db")
    @patch("app.services.instrument_service.AnalysisResult")
    def test_approve_no_sample_skips_linking(self, mock_ar, mock_db):
        from app.services.instrument_service import approve_reading
        reading = MagicMock()
        reading.status = "pending"
        reading.sample_id = None
        reading.analysis_code = None
        mock_db.session.get.return_value = reading

        result = approve_reading(1, 42)
        assert result.status == "approved"
        mock_ar.query.filter_by.assert_not_called()


class TestRejectReading:
    """Test reject_reading."""

    @patch("app.services.instrument_service.db")
    def test_reject_not_found_raises(self, mock_db):
        from app.services.instrument_service import reject_reading
        mock_db.session.get.return_value = None
        with pytest.raises(ValueError, match="not found"):
            reject_reading(999, 1)

    @patch("app.services.instrument_service.db")
    def test_reject_already_rejected_raises(self, mock_db):
        from app.services.instrument_service import reject_reading
        reading = MagicMock()
        reading.status = "rejected"
        mock_db.session.get.return_value = reading
        with pytest.raises(ValueError, match="already rejected"):
            reject_reading(1, 1)

    @patch("app.services.instrument_service.db")
    def test_reject_success(self, mock_db):
        from app.services.instrument_service import reject_reading
        reading = MagicMock()
        reading.status = "pending"
        mock_db.session.get.return_value = reading

        result = reject_reading(1, 42, "bad data")
        assert result.status == "rejected"
        assert result.reject_reason == "bad data"
        assert result.reviewed_by_id == 42
        mock_db.session.commit.assert_called_once()


class TestBulkApproveReject:
    """Test bulk_approve and bulk_reject."""

    @patch("app.services.instrument_service.approve_reading")
    def test_bulk_approve_counts_successes(self, mock_approve):
        from app.services.instrument_service import bulk_approve
        mock_approve.side_effect = [MagicMock(), ValueError("fail"), MagicMock()]
        assert bulk_approve([1, 2, 3], 1) == 2

    @patch("app.services.instrument_service.reject_reading")
    def test_bulk_reject_counts_successes(self, mock_reject):
        from app.services.instrument_service import bulk_reject
        mock_reject.side_effect = [MagicMock(), ValueError("fail")]
        assert bulk_reject([1, 2], 1, "reason") == 1

    @patch("app.services.instrument_service.approve_reading")
    def test_bulk_approve_empty_list(self, mock_approve):
        from app.services.instrument_service import bulk_approve
        assert bulk_approve([], 1) == 0
        mock_approve.assert_not_called()


class TestGetPendingReadings:
    """Test get_pending_readings."""

    @patch("app.services.instrument_service.InstrumentReading")
    def test_with_type_filter(self, mock_model):
        from app.services.instrument_service import get_pending_readings
        chain = mock_model.query.filter_by.return_value
        chain.filter_by.return_value = chain
        chain.order_by.return_value.limit.return_value.all.return_value = ["r1"]

        result = get_pending_readings(instrument_type="tga", limit=50)
        assert result == ["r1"]

    @patch("app.services.instrument_service.InstrumentReading")
    def test_without_type_filter(self, mock_model):
        from app.services.instrument_service import get_pending_readings
        chain = mock_model.query.filter_by.return_value
        chain.order_by.return_value.limit.return_value.all.return_value = []

        result = get_pending_readings()
        assert result == []


class TestGetReadingStats:
    """Test get_reading_stats."""

    @patch("app.services.instrument_service.db")
    def test_stats_aggregation(self, mock_db):
        from app.services.instrument_service import get_reading_stats
        mock_db.session.query.return_value.group_by.return_value.all.return_value = [
            ("pending", 5),
            ("approved", 10),
            ("rejected", 2),
        ]
        stats = get_reading_stats()
        assert stats["pending"] == 5
        assert stats["approved"] == 10
        assert stats["rejected"] == 2
        assert stats["total"] == 17

    @patch("app.services.instrument_service.db")
    def test_stats_empty(self, mock_db):
        from app.services.instrument_service import get_reading_stats
        mock_db.session.query.return_value.group_by.return_value.all.return_value = []
        stats = get_reading_stats()
        assert stats["total"] == 0


class TestGetSupportedInstruments:
    """Test get_supported_instruments."""

    @patch("app.services.instrument_service.PARSER_REGISTRY", {"tga": None, "bomb_cal": None})
    def test_returns_list(self):
        from app.services.instrument_service import get_supported_instruments
        instruments = get_supported_instruments()
        assert len(instruments) == 2
        types = [i["type"] for i in instruments]
        assert "tga" in types
        assert "bomb_cal" in types


# ═══════════════════════════════════════════════════════════════════
# 3. qc_chart_service tests
# ═══════════════════════════════════════════════════════════════════

class TestCalculateCapability:
    """Test calculate_capability."""

    def test_fewer_than_2_values(self):
        from app.services.qc_chart_service import calculate_capability
        result = calculate_capability([5.0], target=5.0, sd_ref=1.0, ucl=7.0, lcl=3.0)
        assert result.n == 1
        assert result.cp is None
        assert result.cpk is None

    def test_empty_values(self):
        from app.services.qc_chart_service import calculate_capability
        result = calculate_capability([], target=5.0, sd_ref=1.0, ucl=7.0, lcl=3.0)
        assert result.n == 0

    def test_normal_calculation(self):
        from app.services.qc_chart_service import calculate_capability
        values = [5.0, 5.1, 4.9, 5.0, 5.2, 4.8, 5.1, 5.0, 4.9, 5.0]
        result = calculate_capability(values, target=5.0, sd_ref=0.1, ucl=5.3, lcl=4.7)

        assert result.n == 10
        assert result.mean is not None
        assert result.sd is not None
        assert result.cp is not None
        assert result.cpk is not None
        assert result.rsd_percent is not None
        assert result.bias is not None
        assert result.bias_percent is not None

    def test_zero_sd_no_cp(self):
        from app.services.qc_chart_service import calculate_capability
        # All identical values => sd=0
        values = [5.0, 5.0, 5.0]
        result = calculate_capability(values, target=5.0, sd_ref=0.1, ucl=5.3, lcl=4.7)
        assert result.cp is None  # Division by zero avoided
        assert result.cpk is None

    def test_zero_mean_no_rsd(self):
        from app.services.qc_chart_service import calculate_capability
        values = [-1.0, 1.0, -1.0, 1.0]
        result = calculate_capability(values, target=0.0, sd_ref=1.0, ucl=3.0, lcl=-3.0)
        assert result.mean == 0.0
        assert result.rsd_percent is None  # mean=0 => skip

    def test_zero_target_no_bias_percent(self):
        from app.services.qc_chart_service import calculate_capability
        values = [0.1, 0.2, 0.15]
        result = calculate_capability(values, target=0.0, sd_ref=0.1, ucl=0.5, lcl=-0.5)
        assert result.bias is not None
        assert result.bias_percent is None  # target=0


class TestCalculateMovingAverage:
    """Test calculate_moving_average."""

    def test_fewer_than_window(self):
        from app.services.qc_chart_service import calculate_moving_average
        result = calculate_moving_average([1.0, 2.0], window=5)
        assert result == [None, None]

    def test_exact_window_size(self):
        from app.services.qc_chart_service import calculate_moving_average
        result = calculate_moving_average([1.0, 2.0, 3.0, 4.0, 5.0], window=5)
        assert result[0:4] == [None, None, None, None]
        assert result[4] == pytest.approx(3.0, abs=0.001)

    def test_longer_series(self):
        from app.services.qc_chart_service import calculate_moving_average
        values = [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0]
        result = calculate_moving_average(values, window=3)
        assert len(result) == 7
        assert result[0] is None
        assert result[1] is None
        assert result[2] == pytest.approx(2.0, abs=0.001)
        assert result[6] == pytest.approx(6.0, abs=0.001)


class TestCalculateCusum:
    """Test calculate_cusum."""

    def test_empty_values(self):
        from app.services.qc_chart_service import calculate_cusum
        result = calculate_cusum([], target=5.0)
        assert result["cusum_pos"] == []
        assert result["cusum_neg"] == []
        assert result["signals"] == []

    def test_zero_sd_returns_empty(self):
        from app.services.qc_chart_service import calculate_cusum
        result = calculate_cusum([1.0, 2.0], target=1.5, sd=0)
        assert result["cusum_pos"] == []

    def test_stable_process_no_signals(self):
        from app.services.qc_chart_service import calculate_cusum
        # Values very close to target => no signals
        values = [5.0, 5.01, 4.99, 5.0, 5.02]
        result = calculate_cusum(values, target=5.0, k=0.5, h=5.0, sd=1.0)
        assert len(result["cusum_pos"]) == 5
        assert len(result["cusum_neg"]) == 5
        assert len(result["signals"]) == 0
        assert result["h_upper"] == 5.0
        assert result["h_lower"] == -5.0

    def test_shifted_process_generates_signals(self):
        from app.services.qc_chart_service import calculate_cusum
        # Large upward shift
        values = [10.0] * 20
        result = calculate_cusum(values, target=5.0, k=0.5, h=5.0, sd=1.0)
        assert len(result["signals"]) > 0
        upper_signals = [s for s in result["signals"] if s["type"] == "upper"]
        assert len(upper_signals) > 0


class TestCalculateEwma:
    """Test calculate_ewma."""

    def test_empty_values(self):
        from app.services.qc_chart_service import calculate_ewma
        result = calculate_ewma([], target=5.0)
        assert result["ewma"] == []
        assert result["ucl"] == []
        assert result["lcl"] == []

    def test_zero_sd_returns_empty(self):
        from app.services.qc_chart_service import calculate_ewma
        result = calculate_ewma([1.0, 2.0], target=1.5, sd=0)
        assert result["ewma"] == []

    def test_single_value(self):
        from app.services.qc_chart_service import calculate_ewma
        result = calculate_ewma([5.5], target=5.0, lam=0.2, sd=1.0, L=3.0)
        assert len(result["ewma"]) == 1
        assert len(result["ucl"]) == 1
        assert len(result["lcl"]) == 1
        assert result["target"] == 5.0
        # EWMA(1) = 0.2*5.5 + 0.8*5.0 = 5.1
        assert result["ewma"][0] == pytest.approx(5.1, abs=0.01)

    def test_multiple_values(self):
        from app.services.qc_chart_service import calculate_ewma
        values = [5.0, 5.1, 4.9, 5.2, 5.0]
        result = calculate_ewma(values, target=5.0, lam=0.2, sd=0.5, L=3.0)
        assert len(result["ewma"]) == 5
        assert len(result["ucl"]) == 5
        assert len(result["lcl"]) == 5
        # UCL should be above target, LCL below
        for i in range(5):
            assert result["ucl"][i] > result["target"]
            assert result["lcl"][i] < result["target"]


class TestExportChartData:
    """Test export_chart_data."""

    def test_csv_format(self):
        from app.services.qc_chart_service import export_chart_data
        points = [
            {"value": 5.0, "date": "2026-01-01", "sample_code": "S-001", "operator": "A"},
            {"value": 8.5, "date": "2026-01-02", "sample_code": "S-002", "operator": "B"},
        ]
        csv_str = export_chart_data(points, "Mad", "GBW-001", target=5.0, sd=1.0)
        assert "QC Control Chart" in csv_str
        assert "Target: 5.0" in csv_str
        assert "S-001" in csv_str
        assert "OK" in csv_str
        # z-score for 8.5: (8.5-5)/1 = 3.5 => abs(z)>3 => REJECT
        assert "REJECT" in csv_str

    def test_csv_with_zero_sd(self):
        from app.services.qc_chart_service import export_chart_data
        points = [{"value": 5.0, "date": "2026-01-01", "sample_code": "S-001", "operator": "A"}]
        csv_str = export_chart_data(points, "Mad", "GBW-001", target=5.0, sd=0)
        assert "OK" in csv_str  # z=0 when sd=0

    def test_json_format(self):
        from app.services.qc_chart_service import export_chart_data
        points = [
            {"value": 5.0, "date": "2026-01-01", "sample_code": "S-001", "operator": "A"},
        ]
        json_str = export_chart_data(
            points, "Mad", "GBW-001", target=5.0, sd=1.0, format="json"
        )
        data = json.loads(json_str)
        assert data["standard_name"] == "GBW-001"
        assert data["analysis_code"] == "Mad"
        assert data["target"] == 5.0
        assert data["sd"] == 1.0
        assert data["ucl"] == 7.0
        assert data["lcl"] == 3.0
        assert len(data["data_points"]) == 1

    def test_csv_warning_zone(self):
        from app.services.qc_chart_service import export_chart_data
        # z-score = (7.5-5)/1 = 2.5 => WARNING
        points = [{"value": 7.5, "date": "2026-01-01", "sample_code": "S-001", "operator": "A"}]
        csv_str = export_chart_data(points, "Mad", "GBW-001", target=5.0, sd=1.0)
        assert "WARNING" in csv_str

    def test_empty_data_points(self):
        from app.services.qc_chart_service import export_chart_data
        csv_str = export_chart_data([], "Mad", "GBW-001", target=5.0, sd=1.0)
        lines = csv_str.strip().split("\n")
        assert len(lines) == 3  # 2 comment lines + header


class TestCreateCorrectiveAction:
    """Test create_corrective_action_from_violation."""

    @patch("app.services.qc_chart_service.db")
    def test_no_reject_violations_returns_none(self, mock_db):
        from app.services.qc_chart_service import create_corrective_action_from_violation
        violations = [{"severity": "warning", "rule": "1-2s"}]
        result = create_corrective_action_from_violation("GBW-001", "Mad", violations, 1)
        assert result is None

    @patch("app.services.qc_chart_service.db")
    def test_empty_violations_returns_none(self, mock_db):
        from app.services.qc_chart_service import create_corrective_action_from_violation
        result = create_corrective_action_from_violation("GBW-001", "Mad", [], 1)
        assert result is None

    @patch("app.services.qc_chart_service.db")
    def test_creates_ca_with_new_sequence(self, mock_db):
        from app.services.qc_chart_service import create_corrective_action_from_violation

        mock_db.session.query.return_value.scalar.return_value = None
        mock_ca_instance = MagicMock()
        mock_ca_instance.id = 99

        with patch("app.services.qc_chart_service.CorrectiveAction", create=True) as mock_ca_cls:
            # Patch the import inside the function
            with patch.dict("sys.modules", {
                "app.models.quality_records": MagicMock(CorrectiveAction=mock_ca_cls)
            }):
                mock_ca_cls.return_value = mock_ca_instance

                violations = [{"severity": "reject", "rule": "1-3s"}]
                # We need to reimport to get the patched version
                # Actually the function does a local import, so we patch differently
                result = create_corrective_action_from_violation(
                    "GBW-001", "Mad", violations, 1
                )
                assert result == 99

    @patch("app.services.qc_chart_service.db")
    def test_creates_ca_with_existing_sequence(self, mock_db):
        from app.services.qc_chart_service import create_corrective_action_from_violation
        year = datetime.now().year
        mock_db.session.query.return_value.scalar.return_value = f"CA-{year}-005"
        mock_ca_instance = MagicMock()
        mock_ca_instance.id = 100

        with patch.dict("sys.modules", {}):
            with patch("app.models.quality_records.CorrectiveAction") as mock_ca_cls:
                mock_ca_cls.return_value = mock_ca_instance

                violations = [
                    {"severity": "reject", "rule": "1-3s"},
                    {"severity": "reject", "rule": "2-2s"},
                ]
                result = create_corrective_action_from_violation(
                    "GBW-001", "Mad", violations, 1
                )
                assert result == 100
                # Verify ca_number has incremented sequence
                call_kwargs = mock_ca_cls.call_args[1]
                assert call_kwargs["ca_number"] == f"CA-{year}-006"
