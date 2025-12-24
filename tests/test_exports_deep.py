# tests/test_exports_deep.py
# -*- coding: utf-8 -*-
"""
Deep coverage tests for app/utils/exports.py
"""

import pytest
from unittest.mock import MagicMock, patch
from io import BytesIO
from datetime import datetime


class TestExportToExcel:
    """Tests for export_to_excel function."""

    def test_export_empty_data(self, app):
        """Test export_to_excel with empty data."""
        with app.app_context():
            from app.utils.exports import export_to_excel

            data = []
            columns = [{"key": "name", "label": "Name"}]
            result = export_to_excel(data, columns)

            assert isinstance(result, BytesIO)
            assert result.getvalue()  # Has content

    def test_export_basic_data(self, app):
        """Test export_to_excel with basic data."""
        with app.app_context():
            from app.utils.exports import export_to_excel

            data = [
                {"name": "Test1", "value": 100},
                {"name": "Test2", "value": 200}
            ]
            columns = [
                {"key": "name", "label": "Name"},
                {"key": "value", "label": "Value"}
            ]
            result = export_to_excel(data, columns)

            assert isinstance(result, BytesIO)

    def test_export_with_custom_filename(self, app):
        """Test export_to_excel with custom filename."""
        with app.app_context():
            from app.utils.exports import export_to_excel

            data = [{"col": "value"}]
            columns = [{"key": "col", "label": "Column"}]
            result = export_to_excel(data, columns, filename="custom.xlsx")

            assert isinstance(result, BytesIO)

    def test_export_with_custom_sheet(self, app):
        """Test export_to_excel with custom sheet name."""
        with app.app_context():
            from app.utils.exports import export_to_excel

            data = [{"col": "value"}]
            columns = [{"key": "col", "label": "Column"}]
            result = export_to_excel(data, columns, sheet_name="Custom Sheet")

            assert isinstance(result, BytesIO)

    def test_export_missing_key(self, app):
        """Test export_to_excel with missing key in data."""
        with app.app_context():
            from app.utils.exports import export_to_excel

            data = [{"name": "Test"}]
            columns = [
                {"key": "name", "label": "Name"},
                {"key": "missing", "label": "Missing"}
            ]
            result = export_to_excel(data, columns)

            assert isinstance(result, BytesIO)

    def test_export_long_cell_values(self, app):
        """Test export_to_excel with long cell values."""
        with app.app_context():
            from app.utils.exports import export_to_excel

            data = [{"text": "A" * 100}]  # Long text
            columns = [{"key": "text", "label": "Text"}]
            result = export_to_excel(data, columns)

            assert isinstance(result, BytesIO)

    def test_export_multiple_columns(self, app):
        """Test export_to_excel with multiple columns."""
        with app.app_context():
            from app.utils.exports import export_to_excel

            data = [
                {"a": 1, "b": 2, "c": 3, "d": 4, "e": 5}
            ]
            columns = [
                {"key": "a", "label": "Col A"},
                {"key": "b", "label": "Col B"},
                {"key": "c", "label": "Col C"},
                {"key": "d", "label": "Col D"},
                {"key": "e", "label": "Col E"},
            ]
            result = export_to_excel(data, columns)

            assert isinstance(result, BytesIO)


class TestCreateSampleExport:
    """Tests for create_sample_export function."""

    def test_create_sample_export_empty(self, app):
        """Test create_sample_export with empty list."""
        with app.app_context():
            from app.utils.exports import create_sample_export

            result = create_sample_export([])
            assert isinstance(result, BytesIO)

    def test_create_sample_export_basic(self, app, db):
        """Test create_sample_export with samples."""
        with app.app_context():
            from app.utils.exports import create_sample_export
            from app.models import Sample

            # Create mock samples
            sample = MagicMock(spec=Sample)
            sample.id = 1
            sample.sample_code = "TEST001"
            sample.client_name = "CHPP"
            sample.sample_type = "2H"
            sample.sample_date = datetime(2025, 12, 25)
            sample.received_date = datetime(2025, 12, 25, 10, 30)
            sample.status = "pending"
            sample.delivered_by = "Operator"

            result = create_sample_export([sample])
            assert isinstance(result, BytesIO)

    def test_create_sample_export_none_dates(self, app):
        """Test create_sample_export with None dates."""
        with app.app_context():
            from app.utils.exports import create_sample_export

            sample = MagicMock()
            sample.id = 1
            sample.sample_code = "TEST002"
            sample.client_name = "CHPP"
            sample.sample_type = "2H"
            sample.sample_date = None
            sample.received_date = None
            sample.status = "pending"
            sample.delivered_by = None

            result = create_sample_export([sample])
            assert isinstance(result, BytesIO)

    def test_create_sample_export_multiple(self, app):
        """Test create_sample_export with multiple samples."""
        with app.app_context():
            from app.utils.exports import create_sample_export

            samples = []
            for i in range(5):
                sample = MagicMock()
                sample.id = i
                sample.sample_code = f"TEST{i:03d}"
                sample.client_name = "CHPP"
                sample.sample_type = "2H"
                sample.sample_date = datetime(2025, 12, 25)
                sample.received_date = datetime(2025, 12, 25, 10, 30)
                sample.status = "pending"
                sample.delivered_by = "Operator"
                samples.append(sample)

            result = create_sample_export(samples)
            assert isinstance(result, BytesIO)


class TestCreateAnalysisExport:
    """Tests for create_analysis_export function."""

    def test_create_analysis_export_empty(self, app):
        """Test create_analysis_export with empty list."""
        with app.app_context():
            from app.utils.exports import create_analysis_export

            result = create_analysis_export([])
            assert isinstance(result, BytesIO)

    def test_create_analysis_export_basic(self, app):
        """Test create_analysis_export with results."""
        with app.app_context():
            from app.utils.exports import create_analysis_export

            mock_sample = MagicMock()
            mock_sample.sample_code = "TEST001"

            mock_user = MagicMock()
            mock_user.username = "chemist1"

            result_obj = MagicMock()
            result_obj.id = 1
            result_obj.sample = mock_sample
            result_obj.analysis_code = "MT"
            result_obj.final_result = 10.5
            result_obj.status = "approved"
            result_obj.user = mock_user
            result_obj.created_at = datetime(2025, 12, 25, 10, 30)

            result = create_analysis_export([result_obj])
            assert isinstance(result, BytesIO)

    def test_create_analysis_export_none_relations(self, app):
        """Test create_analysis_export with None sample/user."""
        with app.app_context():
            from app.utils.exports import create_analysis_export

            result_obj = MagicMock()
            result_obj.id = 1
            result_obj.sample = None
            result_obj.analysis_code = "MT"
            result_obj.final_result = 10.5
            result_obj.status = "approved"
            result_obj.user = None
            result_obj.created_at = None

            result = create_analysis_export([result_obj])
            assert isinstance(result, BytesIO)


class TestCreateAuditExport:
    """Tests for create_audit_export function."""

    def test_create_audit_export_empty(self, app):
        """Test create_audit_export with empty list."""
        with app.app_context():
            from app.utils.exports import create_audit_export

            result = create_audit_export([])
            assert isinstance(result, BytesIO)

    def test_create_audit_export_basic(self, app):
        """Test create_audit_export with logs."""
        with app.app_context():
            from app.utils.exports import create_audit_export

            mock_user = MagicMock()
            mock_user.username = "admin"

            log = MagicMock()
            log.id = 1
            log.timestamp = datetime(2025, 12, 25, 10, 30, 45)
            log.user = mock_user
            log.action = "login"
            log.resource_type = "User"
            log.resource_id = 1
            log.ip_address = "127.0.0.1"
            log.details = '{"browser": "Chrome"}'

            result = create_audit_export([log])
            assert isinstance(result, BytesIO)

    def test_create_audit_export_none_values(self, app):
        """Test create_audit_export with None values."""
        with app.app_context():
            from app.utils.exports import create_audit_export

            log = MagicMock()
            log.id = 1
            log.timestamp = None
            log.user = None
            log.action = "anonymous_action"
            log.resource_type = None
            log.resource_id = None
            log.ip_address = None
            log.details = None

            result = create_audit_export([log])
            assert isinstance(result, BytesIO)

    def test_create_audit_export_long_details(self, app):
        """Test create_audit_export with long details."""
        with app.app_context():
            from app.utils.exports import create_audit_export

            log = MagicMock()
            log.id = 1
            log.timestamp = datetime(2025, 12, 25)
            log.user = None
            log.action = "action"
            log.resource_type = "Type"
            log.resource_id = 1
            log.ip_address = "127.0.0.1"
            log.details = "A" * 1000  # Long details

            result = create_audit_export([log])
            assert isinstance(result, BytesIO)


class TestSendExcelResponse:
    """Tests for send_excel_response function."""

    def test_send_excel_response(self, client, app):
        """Test send_excel_response returns correct response."""
        with app.test_request_context('/'):
            from app.utils.exports import send_excel_response

            excel_data = BytesIO(b"test content")
            excel_data.seek(0)

            response = send_excel_response(excel_data, "test.xlsx")

            assert response.mimetype == 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'

    def test_send_excel_response_headers(self, client, app):
        """Test send_excel_response has correct headers."""
        with app.test_request_context('/'):
            from app.utils.exports import send_excel_response

            excel_data = BytesIO(b"test content")
            excel_data.seek(0)

            response = send_excel_response(excel_data, "my_file.xlsx")

            # Check content disposition header
            assert response.headers.get('Content-Disposition') is not None
