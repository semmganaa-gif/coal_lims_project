# -*- coding: utf-8 -*-
"""
Exports модулийн coverage тестүүд
"""
import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime
from io import BytesIO


class TestExportToExcel:
    """export_to_excel тестүүд"""

    def test_import_function(self):
        """Function import"""
        from app.utils.exports import export_to_excel
        assert export_to_excel is not None

    def test_empty_data(self):
        """Empty data returns valid BytesIO"""
        from app.utils.exports import export_to_excel
        columns = [{"key": "id", "label": "ID"}]
        result = export_to_excel([], columns)
        assert isinstance(result, BytesIO)
        assert result.getvalue()  # Not empty

    def test_single_row(self):
        """Single row data"""
        from app.utils.exports import export_to_excel
        data = [{"id": 1, "name": "Test"}]
        columns = [
            {"key": "id", "label": "ID"},
            {"key": "name", "label": "Name"}
        ]
        result = export_to_excel(data, columns)
        assert isinstance(result, BytesIO)

    def test_multiple_rows(self):
        """Multiple rows data"""
        from app.utils.exports import export_to_excel
        data = [
            {"id": 1, "name": "Test 1"},
            {"id": 2, "name": "Test 2"},
            {"id": 3, "name": "Test 3"}
        ]
        columns = [
            {"key": "id", "label": "ID"},
            {"key": "name", "label": "Name"}
        ]
        result = export_to_excel(data, columns)
        assert isinstance(result, BytesIO)

    def test_long_content(self):
        """Long content is handled"""
        from app.utils.exports import export_to_excel
        data = [{"content": "x" * 100}]
        columns = [{"key": "content", "label": "Content"}]
        result = export_to_excel(data, columns)
        assert isinstance(result, BytesIO)

    def test_missing_key(self):
        """Missing key returns empty string"""
        from app.utils.exports import export_to_excel
        data = [{"id": 1}]
        columns = [
            {"key": "id", "label": "ID"},
            {"key": "missing", "label": "Missing"}
        ]
        result = export_to_excel(data, columns)
        assert isinstance(result, BytesIO)

    def test_custom_sheet_name(self):
        """Custom sheet name"""
        from app.utils.exports import export_to_excel
        data = [{"id": 1}]
        columns = [{"key": "id", "label": "ID"}]
        result = export_to_excel(data, columns, sheet_name="Custom Sheet")
        assert isinstance(result, BytesIO)

    def test_special_characters(self):
        """Special characters in data"""
        from app.utils.exports import export_to_excel
        data = [{"text": "Монгол хэл тест"}]
        columns = [{"key": "text", "label": "Текст"}]
        result = export_to_excel(data, columns)
        assert isinstance(result, BytesIO)


class TestCreateSampleExport:
    """create_sample_export тестүүд"""

    def test_import_function(self):
        """Function import"""
        from app.utils.exports import create_sample_export
        assert create_sample_export is not None

    def test_empty_samples(self):
        """Empty samples list"""
        from app.utils.exports import create_sample_export
        result = create_sample_export([])
        assert isinstance(result, BytesIO)

    def test_with_sample(self):
        """With mock sample"""
        from app.utils.exports import create_sample_export

        sample = MagicMock()
        sample.id = 1
        sample.sample_code = "SAMPLE-001"
        sample.client_name = "Test Client"
        sample.sample_type = "Coal"
        sample.sample_date = datetime(2025, 1, 15)
        sample.received_date = datetime(2025, 1, 15, 10, 30)
        sample.status = "pending"
        sample.delivered_by = "John"

        result = create_sample_export([sample])
        assert isinstance(result, BytesIO)

    def test_sample_none_dates(self):
        """Sample with None dates"""
        from app.utils.exports import create_sample_export

        sample = MagicMock()
        sample.id = 2
        sample.sample_code = "SAMPLE-002"
        sample.client_name = "Client"
        sample.sample_type = "Coal"
        sample.sample_date = None
        sample.received_date = None
        sample.status = "pending"
        sample.delivered_by = None

        result = create_sample_export([sample])
        assert isinstance(result, BytesIO)

    def test_multiple_samples(self):
        """Multiple samples"""
        from app.utils.exports import create_sample_export

        samples = []
        for i in range(5):
            sample = MagicMock()
            sample.id = i + 1
            sample.sample_code = f"SAMPLE-{i:03d}"
            sample.client_name = f"Client {i}"
            sample.sample_type = "Coal"
            sample.sample_date = datetime(2025, 1, i + 1)
            sample.received_date = None
            sample.status = "pending"
            sample.delivered_by = None
            samples.append(sample)

        result = create_sample_export(samples)
        assert isinstance(result, BytesIO)


class TestCreateAnalysisExport:
    """create_analysis_export тестүүд"""

    def test_import_function(self):
        """Function import"""
        from app.utils.exports import create_analysis_export
        assert create_analysis_export is not None

    def test_empty_results(self):
        """Empty results list"""
        from app.utils.exports import create_analysis_export
        result = create_analysis_export([])
        assert isinstance(result, BytesIO)

    def test_with_result(self):
        """With mock analysis result"""
        from app.utils.exports import create_analysis_export

        sample = MagicMock()
        sample.sample_code = "SAMPLE-001"

        user = MagicMock()
        user.username = "chemist1"

        analysis = MagicMock()
        analysis.id = 1
        analysis.sample = sample
        analysis.analysis_code = "CV"
        analysis.final_result = 15.5
        analysis.status = "completed"
        analysis.user = user
        analysis.created_at = datetime(2025, 1, 15, 14, 30)

        result = create_analysis_export([analysis])
        assert isinstance(result, BytesIO)

    def test_result_none_values(self):
        """Result with None values"""
        from app.utils.exports import create_analysis_export

        analysis = MagicMock()
        analysis.id = 2
        analysis.sample = None
        analysis.analysis_code = "Aad"
        analysis.final_result = None
        analysis.status = "pending"
        analysis.user = None
        analysis.created_at = None

        result = create_analysis_export([analysis])
        assert isinstance(result, BytesIO)

    def test_multiple_results(self):
        """Multiple results"""
        from app.utils.exports import create_analysis_export

        results = []
        for i in range(3):
            analysis = MagicMock()
            analysis.id = i + 1
            analysis.sample = MagicMock()
            analysis.sample.sample_code = f"SAMPLE-{i:03d}"
            analysis.analysis_code = "CV"
            analysis.final_result = 10.0 + i
            analysis.status = "completed"
            analysis.user = MagicMock()
            analysis.user.username = f"user{i}"
            analysis.created_at = datetime(2025, 1, 15)
            results.append(analysis)

        result = create_analysis_export(results)
        assert isinstance(result, BytesIO)


class TestCreateAuditExport:
    """create_audit_export тестүүд"""

    def test_import_function(self):
        """Function import"""
        from app.utils.exports import create_audit_export
        assert create_audit_export is not None

    def test_empty_logs(self):
        """Empty logs list"""
        from app.utils.exports import create_audit_export
        result = create_audit_export([])
        assert isinstance(result, BytesIO)

    def test_with_log(self):
        """With mock audit log"""
        from app.utils.exports import create_audit_export

        user = MagicMock()
        user.username = "admin"

        log = MagicMock()
        log.id = 1
        log.timestamp = datetime(2025, 1, 15, 10, 30, 45)
        log.user = user
        log.action = "CREATE"
        log.resource_type = "sample"
        log.resource_id = "123"
        log.ip_address = "192.168.1.1"
        log.details = {"key": "value"}

        result = create_audit_export([log])
        assert isinstance(result, BytesIO)

    def test_log_none_values(self):
        """Log with None values"""
        from app.utils.exports import create_audit_export

        log = MagicMock()
        log.id = 2
        log.timestamp = None
        log.user = None
        log.action = "DELETE"
        log.resource_type = None
        log.resource_id = None
        log.ip_address = None
        log.details = None

        result = create_audit_export([log])
        assert isinstance(result, BytesIO)

    def test_long_details(self):
        """Log with long details"""
        from app.utils.exports import create_audit_export

        log = MagicMock()
        log.id = 3
        log.timestamp = datetime(2025, 1, 15)
        log.user = MagicMock()
        log.user.username = "admin"
        log.action = "UPDATE"
        log.resource_type = "sample"
        log.resource_id = "456"
        log.ip_address = "10.0.0.1"
        log.details = "x" * 1000  # Very long details

        result = create_audit_export([log])
        assert isinstance(result, BytesIO)

    def test_multiple_logs(self):
        """Multiple logs"""
        from app.utils.exports import create_audit_export

        logs = []
        for i in range(5):
            log = MagicMock()
            log.id = i + 1
            log.timestamp = datetime(2025, 1, 15, i, 0, 0)
            log.user = MagicMock()
            log.user.username = f"user{i}"
            log.action = "ACTION"
            log.resource_type = "sample"
            log.resource_id = str(i)
            log.ip_address = f"192.168.1.{i}"
            log.details = {"index": i}
            logs.append(log)

        result = create_audit_export(logs)
        assert isinstance(result, BytesIO)


class TestSendExcelResponse:
    """send_excel_response тестүүд"""

    def test_import_function(self):
        """Function import"""
        from app.utils.exports import send_excel_response
        assert send_excel_response is not None

    @patch('app.utils.exports.send_file')
    def test_sends_file(self, mock_send_file):
        """Calls send_file with correct params"""
        from app.utils.exports import send_excel_response

        excel_data = BytesIO(b"test")
        mock_send_file.return_value = "response"

        result = send_excel_response(excel_data, "test.xlsx")

        mock_send_file.assert_called_once()
        args, kwargs = mock_send_file.call_args
        assert kwargs['mimetype'] == 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        assert kwargs['as_attachment'] is True
        assert kwargs['download_name'] == "test.xlsx"
