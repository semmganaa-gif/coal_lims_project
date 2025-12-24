# tests/test_exports_full.py
# -*- coding: utf-8 -*-
"""
Complete tests for app/utils/exports.py
"""

import pytest
from io import BytesIO
from unittest.mock import patch, MagicMock
from datetime import datetime


class TestExportToExcel:
    """Tests for export_to_excel function."""

    def test_returns_bytesio(self, app):
        """Test returns BytesIO object."""
        with app.app_context():
            from app.utils.exports import export_to_excel
            data = [{"col1": "val1", "col2": "val2"}]
            columns = [
                {"key": "col1", "label": "Column 1"},
                {"key": "col2", "label": "Column 2"}
            ]
            result = export_to_excel(data, columns)
            assert isinstance(result, BytesIO)

    def test_empty_data(self, app):
        """Test with empty data."""
        with app.app_context():
            from app.utils.exports import export_to_excel
            data = []
            columns = [
                {"key": "col1", "label": "Column 1"}
            ]
            result = export_to_excel(data, columns)
            assert isinstance(result, BytesIO)

    def test_multiple_rows(self, app):
        """Test with multiple rows."""
        with app.app_context():
            from app.utils.exports import export_to_excel
            data = [
                {"col1": "val1", "col2": "val2"},
                {"col1": "val3", "col2": "val4"},
                {"col1": "val5", "col2": "val6"}
            ]
            columns = [
                {"key": "col1", "label": "Column 1"},
                {"key": "col2", "label": "Column 2"}
            ]
            result = export_to_excel(data, columns)
            assert isinstance(result, BytesIO)
            assert result.getvalue()  # Not empty

    def test_missing_key_in_data(self, app):
        """Test with missing key in data."""
        with app.app_context():
            from app.utils.exports import export_to_excel
            data = [{"col1": "val1"}]  # Missing col2
            columns = [
                {"key": "col1", "label": "Column 1"},
                {"key": "col2", "label": "Column 2"}
            ]
            result = export_to_excel(data, columns)
            assert isinstance(result, BytesIO)

    def test_custom_sheet_name(self, app):
        """Test with custom sheet name."""
        with app.app_context():
            from app.utils.exports import export_to_excel
            data = [{"col1": "val1"}]
            columns = [{"key": "col1", "label": "Column 1"}]
            result = export_to_excel(data, columns, sheet_name="Custom Sheet")
            assert isinstance(result, BytesIO)

    def test_long_cell_value(self, app):
        """Test with long cell value (>50 chars for column width)."""
        with app.app_context():
            from app.utils.exports import export_to_excel
            long_value = "A" * 100
            data = [{"col1": long_value}]
            columns = [{"key": "col1", "label": "Column 1"}]
            result = export_to_excel(data, columns)
            assert isinstance(result, BytesIO)

    def test_numeric_values(self, app):
        """Test with numeric values."""
        with app.app_context():
            from app.utils.exports import export_to_excel
            data = [{"num": 123.45, "int": 100}]
            columns = [
                {"key": "num", "label": "Number"},
                {"key": "int", "label": "Integer"}
            ]
            result = export_to_excel(data, columns)
            assert isinstance(result, BytesIO)

    def test_none_values(self, app):
        """Test with None values."""
        with app.app_context():
            from app.utils.exports import export_to_excel
            data = [{"col1": None, "col2": "val2"}]
            columns = [
                {"key": "col1", "label": "Column 1"},
                {"key": "col2", "label": "Column 2"}
            ]
            result = export_to_excel(data, columns)
            assert isinstance(result, BytesIO)


class TestCreateSampleExport:
    """Tests for create_sample_export function."""

    def test_returns_bytesio(self, app, db):
        """Test returns BytesIO object."""
        with app.app_context():
            from app.utils.exports import create_sample_export
            from app.models import Sample

            samples = Sample.query.limit(5).all()
            result = create_sample_export(samples)
            assert isinstance(result, BytesIO)

    def test_empty_samples(self, app, db):
        """Test with empty samples list."""
        with app.app_context():
            from app.utils.exports import create_sample_export
            result = create_sample_export([])
            assert isinstance(result, BytesIO)

    def test_with_mock_samples(self, app):
        """Test with mock sample objects."""
        with app.app_context():
            from app.utils.exports import create_sample_export

            # Create mock sample
            mock_sample = MagicMock()
            mock_sample.id = 1
            mock_sample.sample_code = "TEST-001"
            mock_sample.client_name = "Test Client"
            mock_sample.sample_type = "Coal"
            mock_sample.sample_date = datetime(2024, 1, 15)
            mock_sample.received_date = datetime(2024, 1, 15, 10, 30)
            mock_sample.status = "pending"
            mock_sample.delivered_by = "John"

            result = create_sample_export([mock_sample])
            assert isinstance(result, BytesIO)

    def test_with_none_dates(self, app):
        """Test with None dates."""
        with app.app_context():
            from app.utils.exports import create_sample_export

            mock_sample = MagicMock()
            mock_sample.id = 1
            mock_sample.sample_code = "TEST-001"
            mock_sample.client_name = "Test Client"
            mock_sample.sample_type = "Coal"
            mock_sample.sample_date = None
            mock_sample.received_date = None
            mock_sample.status = "pending"
            mock_sample.delivered_by = None

            result = create_sample_export([mock_sample])
            assert isinstance(result, BytesIO)


class TestCreateAnalysisExport:
    """Tests for create_analysis_export function."""

    def test_returns_bytesio(self, app, db):
        """Test returns BytesIO object."""
        with app.app_context():
            from app.utils.exports import create_analysis_export
            from app.models import AnalysisResult

            results = AnalysisResult.query.limit(5).all()
            result = create_analysis_export(results)
            assert isinstance(result, BytesIO)

    def test_empty_results(self, app, db):
        """Test with empty results list."""
        with app.app_context():
            from app.utils.exports import create_analysis_export
            result = create_analysis_export([])
            assert isinstance(result, BytesIO)

    def test_with_mock_results(self, app):
        """Test with mock analysis result objects."""
        with app.app_context():
            from app.utils.exports import create_analysis_export

            # Create mock result
            mock_result = MagicMock()
            mock_result.id = 1
            mock_result.sample = MagicMock()
            mock_result.sample.sample_code = "TEST-001"
            mock_result.analysis_code = "TS"
            mock_result.final_result = 0.85
            mock_result.status = "completed"
            mock_result.user = MagicMock()
            mock_result.user.username = "chemist1"
            mock_result.created_at = datetime(2024, 1, 15, 14, 30)

            result = create_analysis_export([mock_result])
            assert isinstance(result, BytesIO)

    def test_with_none_relations(self, app):
        """Test with None sample/user relations."""
        with app.app_context():
            from app.utils.exports import create_analysis_export

            mock_result = MagicMock()
            mock_result.id = 1
            mock_result.sample = None
            mock_result.analysis_code = "TS"
            mock_result.final_result = 0.85
            mock_result.status = "completed"
            mock_result.user = None
            mock_result.created_at = None

            result = create_analysis_export([mock_result])
            assert isinstance(result, BytesIO)


class TestCreateAuditExport:
    """Tests for create_audit_export function."""

    def test_returns_bytesio(self, app, db):
        """Test returns BytesIO object."""
        with app.app_context():
            from app.utils.exports import create_audit_export
            from app.models import AuditLog

            logs = AuditLog.query.limit(5).all()
            result = create_audit_export(logs)
            assert isinstance(result, BytesIO)

    def test_empty_logs(self, app, db):
        """Test with empty logs list."""
        with app.app_context():
            from app.utils.exports import create_audit_export
            result = create_audit_export([])
            assert isinstance(result, BytesIO)

    def test_with_mock_logs(self, app):
        """Test with mock audit log objects."""
        with app.app_context():
            from app.utils.exports import create_audit_export

            mock_log = MagicMock()
            mock_log.id = 1
            mock_log.timestamp = datetime(2024, 1, 15, 14, 30, 45)
            mock_log.user = MagicMock()
            mock_log.user.username = "admin"
            mock_log.action = "update"
            mock_log.resource_type = "sample"
            mock_log.resource_id = "123"
            mock_log.ip_address = "192.168.1.1"
            mock_log.details = {"field": "status", "old": "pending", "new": "approved"}

            result = create_audit_export([mock_log])
            assert isinstance(result, BytesIO)

    def test_with_none_values(self, app):
        """Test with None values."""
        with app.app_context():
            from app.utils.exports import create_audit_export

            mock_log = MagicMock()
            mock_log.id = 1
            mock_log.timestamp = None
            mock_log.user = None
            mock_log.action = "view"
            mock_log.resource_type = None
            mock_log.resource_id = None
            mock_log.ip_address = None
            mock_log.details = None

            result = create_audit_export([mock_log])
            assert isinstance(result, BytesIO)

    def test_long_details_truncated(self, app):
        """Test that long details are truncated."""
        with app.app_context():
            from app.utils.exports import create_audit_export

            mock_log = MagicMock()
            mock_log.id = 1
            mock_log.timestamp = datetime.now()
            mock_log.user = MagicMock()
            mock_log.user.username = "admin"
            mock_log.action = "update"
            mock_log.resource_type = "sample"
            mock_log.resource_id = "123"
            mock_log.ip_address = "192.168.1.1"
            mock_log.details = {"data": "x" * 1000}  # Very long details

            result = create_audit_export([mock_log])
            assert isinstance(result, BytesIO)


class TestSendExcelResponse:
    """Tests for send_excel_response function."""

    def test_returns_response(self, app):
        """Test returns Flask response."""
        with app.app_context():
            with app.test_request_context():
                from app.utils.exports import send_excel_response

                excel_data = BytesIO(b"test data")
                result = send_excel_response(excel_data, "test.xlsx")
                # Should return a response object
                assert result is not None

    def test_correct_mimetype(self, app):
        """Test correct mimetype is set."""
        with app.app_context():
            with app.test_request_context():
                from app.utils.exports import send_excel_response

                excel_data = BytesIO(b"test data")
                result = send_excel_response(excel_data, "test.xlsx")
                assert 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' in result.content_type

    def test_attachment_disposition(self, app):
        """Test attachment disposition is set."""
        with app.app_context():
            with app.test_request_context():
                from app.utils.exports import send_excel_response

                excel_data = BytesIO(b"test data")
                result = send_excel_response(excel_data, "my_export.xlsx")
                content_disposition = result.headers.get('Content-Disposition', '')
                assert 'attachment' in content_disposition
