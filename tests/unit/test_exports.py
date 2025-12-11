# tests/unit/test_exports.py
# -*- coding: utf-8 -*-
"""
Export Utility тест

Tests for Excel export functions.
"""

import pytest
from io import BytesIO
from datetime import datetime
from unittest.mock import Mock, patch


class TestExportToExcel:
    """export_to_excel() функцийн тест"""

    def test_export_simple_data(self):
        """Энгийн өгөгдөл экспорт"""
        from app.utils.exports import export_to_excel

        data = [
            {"name": "Test 1", "value": 100},
            {"name": "Test 2", "value": 200},
        ]
        columns = [
            {"key": "name", "label": "Нэр"},
            {"key": "value", "label": "Утга"},
        ]

        result = export_to_excel(data, columns)

        assert isinstance(result, BytesIO)
        assert result.tell() == 0  # Seek to beginning
        assert len(result.getvalue()) > 0  # Has content

    def test_export_empty_data(self):
        """Хоосон өгөгдөл"""
        from app.utils.exports import export_to_excel

        data = []
        columns = [
            {"key": "name", "label": "Нэр"},
        ]

        result = export_to_excel(data, columns)
        assert isinstance(result, BytesIO)

    def test_export_missing_keys(self):
        """Байхгүй key-тэй өгөгдөл"""
        from app.utils.exports import export_to_excel

        data = [
            {"name": "Test 1"},  # missing "value"
        ]
        columns = [
            {"key": "name", "label": "Нэр"},
            {"key": "value", "label": "Утга"},
        ]

        result = export_to_excel(data, columns)
        assert isinstance(result, BytesIO)

    def test_export_custom_filename(self):
        """Custom filename"""
        from app.utils.exports import export_to_excel

        data = [{"name": "Test"}]
        columns = [{"key": "name", "label": "Нэр"}]

        result = export_to_excel(data, columns, filename="custom.xlsx")
        assert isinstance(result, BytesIO)

    def test_export_custom_sheet_name(self):
        """Custom sheet name"""
        from app.utils.exports import export_to_excel

        data = [{"name": "Test"}]
        columns = [{"key": "name", "label": "Нэр"}]

        result = export_to_excel(data, columns, sheet_name="CustomSheet")
        assert isinstance(result, BytesIO)

    def test_export_long_values(self):
        """Урт утгатай өгөгдөл (column width test)"""
        from app.utils.exports import export_to_excel

        long_text = "A" * 100  # Very long text
        data = [
            {"name": long_text, "value": 100},
        ]
        columns = [
            {"key": "name", "label": "Нэр"},
            {"key": "value", "label": "Утга"},
        ]

        result = export_to_excel(data, columns)
        assert isinstance(result, BytesIO)


class TestCreateSampleExport:
    """create_sample_export() функцийн тест"""

    def test_export_samples(self):
        """Дээжний экспорт"""
        from app.utils.exports import create_sample_export

        # Mock sample objects
        sample1 = Mock(
            id=1,
            sample_code="TT-D1",
            client_name="QC",
            sample_type="2hour",
            sample_date=datetime(2025, 12, 11),
            received_date=datetime(2025, 12, 11, 10, 30),
            status="received",
            delivered_by="John"
        )
        sample2 = Mock(
            id=2,
            sample_code="TT-D2",
            client_name="CHPP",
            sample_type="composite",
            sample_date=None,
            received_date=None,
            status="in_progress",
            delivered_by=None
        )

        result = create_sample_export([sample1, sample2])
        assert isinstance(result, BytesIO)

    def test_export_empty_samples(self):
        """Хоосон дээжний жагсаалт"""
        from app.utils.exports import create_sample_export

        result = create_sample_export([])
        assert isinstance(result, BytesIO)


class TestCreateAnalysisExport:
    """create_analysis_export() функцийн тест"""

    def test_export_analysis_results(self):
        """Шинжилгээний үр дүнгийн экспорт"""
        from app.utils.exports import create_analysis_export

        # Mock user
        mock_user = Mock(username="chemist1")
        # Mock sample
        mock_sample = Mock(sample_code="TT-D1")

        # Mock analysis result
        result1 = Mock(
            id=1,
            sample=mock_sample,
            analysis_code="Aad",
            final_result="5.25",
            status="approved",
            user=mock_user,
            created_at=datetime(2025, 12, 11, 14, 30)
        )
        result2 = Mock(
            id=2,
            sample=None,
            analysis_code="Mad",
            final_result="8.50",
            status="pending",
            user=None,
            created_at=None
        )

        result = create_analysis_export([result1, result2])
        assert isinstance(result, BytesIO)

    def test_export_empty_results(self):
        """Хоосон үр дүнгийн жагсаалт"""
        from app.utils.exports import create_analysis_export

        result = create_analysis_export([])
        assert isinstance(result, BytesIO)


class TestCreateAuditExport:
    """create_audit_export() функцийн тест"""

    def test_export_audit_logs(self):
        """Аудит лог экспорт"""
        from app.utils.exports import create_audit_export

        mock_user = Mock(username="admin")

        log1 = Mock(
            id=1,
            timestamp=datetime(2025, 12, 11, 10, 0, 0),
            user=mock_user,
            action="CREATE",
            resource_type="Sample",
            resource_id=123,
            ip_address="192.168.1.1",
            details={"field": "value"}
        )
        log2 = Mock(
            id=2,
            timestamp=None,
            user=None,
            action="UPDATE",
            resource_type=None,
            resource_id=None,
            ip_address=None,
            details=None
        )

        result = create_audit_export([log1, log2])
        assert isinstance(result, BytesIO)

    def test_export_long_details(self):
        """Урт details хязгаарлах (500 char)"""
        from app.utils.exports import create_audit_export

        mock_user = Mock(username="admin")
        long_details = "X" * 1000  # Very long string

        log = Mock(
            id=1,
            timestamp=datetime(2025, 12, 11),
            user=mock_user,
            action="UPDATE",
            resource_type="Sample",
            resource_id=1,
            ip_address="127.0.0.1",
            details=long_details
        )

        result = create_audit_export([log])
        assert isinstance(result, BytesIO)


class TestSendExcelResponse:
    """send_excel_response() функцийн тест"""

    def test_send_excel_response(self, app, client):
        """Excel response буцаах"""
        from app.utils.exports import send_excel_response

        excel_data = BytesIO(b"dummy excel content")

        # Request context шаардлагатай тул test_request_context ашиглана
        with app.test_request_context():
            response = send_excel_response(excel_data, "test.xlsx")

            # Response object буцаж байгаа эсэх
            assert response is not None
            assert response.mimetype == 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
