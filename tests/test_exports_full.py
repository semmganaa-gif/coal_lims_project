# tests/test_exports_full.py
# -*- coding: utf-8 -*-
"""
Complete tests for app/utils/exports.py
"""

import pytest
from unittest.mock import MagicMock, patch
from io import BytesIO
from datetime import datetime, date


class TestExportToExcel:
    """Tests for export_to_excel function."""

    def test_export_basic(self, app):
        """Test basic export with simple data."""
        with app.app_context():
            from app.utils.exports import export_to_excel

            data = [
                {"name": "Test1", "value": 10},
                {"name": "Test2", "value": 20}
            ]
            columns = [
                {"key": "name", "label": "Name"},
                {"key": "value", "label": "Value"}
            ]

            result = export_to_excel(data, columns)
            assert isinstance(result, BytesIO)
            content = result.read()
            assert content[:2] == b'PK'

    def test_export_empty_data(self, app):
        """Test export with empty data."""
        with app.app_context():
            from app.utils.exports import export_to_excel

            data = []
            columns = [{"key": "name", "label": "Name"}]
            result = export_to_excel(data, columns)
            assert isinstance(result, BytesIO)

    def test_export_missing_keys(self, app):
        """Test export when data doesn't have all keys."""
        with app.app_context():
            from app.utils.exports import export_to_excel

            data = [{"name": "Test1"}]
            columns = [
                {"key": "name", "label": "Name"},
                {"key": "value", "label": "Value"}
            ]
            result = export_to_excel(data, columns)
            assert isinstance(result, BytesIO)

    def test_export_long_values(self, app):
        """Test export with long values."""
        with app.app_context():
            from app.utils.exports import export_to_excel

            data = [{"name": "A" * 100, "value": "B" * 60}]
            columns = [
                {"key": "name", "label": "Name"},
                {"key": "value", "label": "Value"}
            ]
            result = export_to_excel(data, columns)
            assert isinstance(result, BytesIO)

    def test_export_custom_sheet_name(self, app):
        """Test export with custom sheet name."""
        with app.app_context():
            from app.utils.exports import export_to_excel

            data = [{"col1": "val1"}]
            columns = [{"key": "col1", "label": "Column1"}]
            result = export_to_excel(data, columns, filename="custom.xlsx", sheet_name="CustomSheet")
            assert isinstance(result, BytesIO)


class TestCreateSampleExport:
    """Tests for create_sample_export function."""

    def test_sample_export_empty(self, app):
        """Test sample export with empty list."""
        with app.app_context():
            from app.utils.exports import create_sample_export
            result = create_sample_export([])
            assert isinstance(result, BytesIO)

    def test_sample_export_with_samples(self, app, db):
        """Test sample export with actual samples."""
        with app.app_context():
            from app.utils.exports import create_sample_export
            from app.models import Sample, User

            user = User.query.first()
            if user:
                sample = Sample(
                    sample_code='EXPORT_TEST_001',
                    client_name='CHPP',
                    sample_type='2 hourly',
                    user_id=user.id,
                    sample_date=date.today(),
                    status='new',
                    delivered_by='Test Person'
                )
                db.session.add(sample)
                db.session.commit()
                result = create_sample_export([sample])
                assert isinstance(result, BytesIO)

    def test_sample_export_none_dates(self, app, db):
        """Test sample export with None dates."""
        with app.app_context():
            from app.utils.exports import create_sample_export
            from app.models import Sample, User

            user = User.query.first()
            if user:
                sample = Sample(
                    sample_code='EXPORT_TEST_002',
                    client_name='CHPP',
                    sample_type='2 hourly',
                    user_id=user.id,
                    sample_date=None,
                    received_date=None,
                    status='new'
                )
                db.session.add(sample)
                db.session.commit()
                result = create_sample_export([sample])
                assert isinstance(result, BytesIO)


class TestCreateAnalysisExport:
    """Tests for create_analysis_export function."""

    def test_analysis_export_empty(self, app):
        """Test analysis export with empty list."""
        with app.app_context():
            from app.utils.exports import create_analysis_export
            result = create_analysis_export([])
            assert isinstance(result, BytesIO)

    def test_analysis_export_none_values(self, app):
        """Test analysis export with None values."""
        with app.app_context():
            from app.utils.exports import create_analysis_export

            mock_result = MagicMock()
            mock_result.id = 1
            mock_result.sample = None
            mock_result.analysis_code = 'Mad'
            mock_result.final_result = None
            mock_result.status = 'pending'
            mock_result.user = None
            mock_result.created_at = None

            result = create_analysis_export([mock_result])
            assert isinstance(result, BytesIO)


class TestCreateAuditExport:
    """Tests for create_audit_export function."""

    def test_audit_export_empty(self, app):
        """Test audit export with empty list."""
        with app.app_context():
            from app.utils.exports import create_audit_export
            result = create_audit_export([])
            assert isinstance(result, BytesIO)

    def test_audit_export_none_values(self, app):
        """Test audit export with None values."""
        with app.app_context():
            from app.utils.exports import create_audit_export

            mock_log = MagicMock()
            mock_log.id = 1
            mock_log.timestamp = None
            mock_log.user = None
            mock_log.action = 'test'
            mock_log.resource_type = None
            mock_log.resource_id = None
            mock_log.ip_address = None
            mock_log.details = None

            result = create_audit_export([mock_log])
            assert isinstance(result, BytesIO)

    def test_audit_export_long_details(self, app):
        """Test audit export with long details."""
        with app.app_context():
            from app.utils.exports import create_audit_export

            mock_log = MagicMock()
            mock_log.id = 1
            mock_log.timestamp = datetime.now()
            mock_log.user = MagicMock()
            mock_log.user.username = 'admin'
            mock_log.action = 'test'
            mock_log.resource_type = 'Sample'
            mock_log.resource_id = 1
            mock_log.ip_address = '127.0.0.1'
            mock_log.details = {'data': 'x' * 1000}

            result = create_audit_export([mock_log])
            assert isinstance(result, BytesIO)
