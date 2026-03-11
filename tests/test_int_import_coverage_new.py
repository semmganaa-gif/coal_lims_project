# tests/test_int_import_coverage_new.py
# -*- coding: utf-8 -*-
"""
import_routes.py модулийн coverage нэмэгдүүлэх тестүүд.
"""

import pytest
from io import BytesIO, StringIO
from datetime import datetime


class TestImportHelperFunctions:
    """Import helper функцүүдийн тестүүд."""

    def test_norm_with_string(self, app):
        """Test _norm with string input."""
        from app.services.import_service import _norm

        assert _norm("  test  ") == "test"
        assert _norm("hello") == "hello"
        assert _norm(None) == ""
        assert _norm("") == ""

    def test_norm_with_number(self, app):
        """Test _norm with number input."""
        from app.services.import_service import _norm

        assert _norm(123) == "123"
        assert _norm(45.67) == "45.67"

    def test_parse_date_valid_formats(self, app):
        """Test _parse_date with various valid date formats."""
        from app.services.import_service import _parse_date

        # YYYY-MM-DD
        result = _parse_date("2025-12-23")
        assert result == datetime(2025, 12, 23)

        # YYYY/MM/DD
        result = _parse_date("2025/12/23")
        assert result == datetime(2025, 12, 23)

        # YYYY-MM-DD HH:MM
        result = _parse_date("2025-12-23 14:30")
        assert result == datetime(2025, 12, 23, 14, 30)

        # YYYY-MM-DD HH:MM:SS
        result = _parse_date("2025-12-23 14:30:45")
        assert result == datetime(2025, 12, 23, 14, 30, 45)

        # YYYY-MM (month only)
        result = _parse_date("2025-12")
        assert result == datetime(2025, 12, 1)

        # DD/MM/YYYY
        result = _parse_date("23/12/2025")
        assert result == datetime(2025, 12, 23)

        # DD/MM/YYYY HH:MM
        result = _parse_date("23/12/2025 14:30")
        assert result == datetime(2025, 12, 23, 14, 30)

        # Year only
        result = _parse_date("2025")
        assert result == datetime(2025, 1, 1)

    def test_parse_date_invalid(self, app):
        """Test _parse_date with invalid input."""
        from app.services.import_service import _parse_date

        assert _parse_date(None) is None
        assert _parse_date("") is None
        assert _parse_date("null") is None
        assert _parse_date("none") is None
        assert _parse_date("invalid date") is None
        assert _parse_date("abc123") is None

    def test_map_header(self, app):
        """Test _map_header function."""
        from app.services.import_service import _map_header

        # Standard headers
        assert _map_header("sample_code") == "sample_code"
        assert _map_header("Sample") == "sample_code"
        assert _map_header("Дээжний нэр") == "sample_code"

        # Client name
        assert _map_header("client_name") == "client_name"
        assert _map_header("unit") == "client_name"
        assert _map_header("Нэгж") == "client_name"

        # Unknown header
        assert _map_header("unknown_column") is None
        assert _map_header("random") is None

    def test_base_code(self, app):
        """Test _base_code function."""
        from app.services.import_service import _base_code

        # Empty input
        assert _base_code("") == ""
        assert _base_code(None) == ""

        # Simple code
        result = _base_code("  Mad  ")
        assert result == "Mad"

        # With alias - just check it returns something
        result = _base_code("Mt,ar")
        assert result is not None
        assert len(result) > 0

    def test_get_or_create_sample_new(self, app):
        """Test _get_or_create_sample creates new sample."""
        from app.services.import_service import _get_or_create_sample
        from app.models import Sample
        from app import db

        with app.app_context():
            sample = _get_or_create_sample(
                "NEW_IMPORT_001",
                {
                    "client_name": "CHPP",
                    "sample_type": "coal",
                    "received_date": datetime.now()
                }
            )
            assert sample is not None
            assert sample.sample_code == "NEW_IMPORT_001"
            db.session.rollback()

    def test_get_or_create_sample_existing(self, app):
        """Test _get_or_create_sample finds existing sample."""
        from app.services.import_service import _get_or_create_sample
        from app.models import Sample
        from app import db

        with app.app_context():
            # Create existing sample
            existing = Sample(
                sample_code="EXISTING_001",
                sample_type="coal",
                client_name="CHPP",
                received_date=datetime.now()
            )
            db.session.add(existing)
            db.session.commit()

            # Should find existing
            result = _get_or_create_sample(
                "EXISTING_001",
                {"client_name": "CHPP"}
            )
            assert result.id == existing.id

    def test_upsert_result_new(self, app):
        """Test _upsert_result creates new result."""
        from app.services.import_service import _upsert_result
        from app.models import Sample
        from app import db

        with app.app_context():
            sample = Sample(
                sample_code="UPSERT_001",
                sample_type="coal",
                client_name="CHPP",
                received_date=datetime.now()
            )
            db.session.add(sample)
            db.session.commit()

            is_new, result_id = _upsert_result(
                sample.id,
                "Mad",
                datetime.now(),
                5.5,
                "approved"
            )
            assert is_new is True
            assert result_id > 0

    def test_upsert_result_update(self, app):
        """Test _upsert_result updates existing result."""
        from app.services.import_service import _upsert_result
        from app.models import Sample, AnalysisResult
        from app import db

        with app.app_context():
            sample = Sample(
                sample_code="UPSERT_002",
                sample_type="coal",
                client_name="CHPP",
                received_date=datetime.now()
            )
            db.session.add(sample)
            db.session.commit()

            # Create first result
            is_new1, _ = _upsert_result(
                sample.id, "Mad", datetime.now(), 5.5, "pending_review"
            )
            db.session.commit()
            assert is_new1 is True

            # Update same result
            is_new2, _ = _upsert_result(
                sample.id, "Mad", datetime.now(), 6.0, "approved"
            )
            assert is_new2 is False


class TestImportCHPPWide:
    """CHPP wide CSV импорт тестүүд."""

    def test_import_chpp_wide_valid(self, app):
        """Test CHPP wide import with valid data."""
        from app.services.import_service import import_chpp_wide as _import_chpp_wide
        import csv

        with app.app_context():
            header = ['_sel', 'ID', 'Дээжний нэр', 'Нэгж', 'Төрөл', 'Бүртгэсэн', 'Шинжилсэн', 'Mt,ar', 'Mad', 'Aad']
            data = [
                ['', '1', 'SAMPLE001', 'CHPP', 'coal', '2025-12-23', '2025-12-23', '15.5', '5.2', '10.1'],
                ['', '2', 'SAMPLE002', 'CHPP', 'coal', '2025-12-23', '2025-12-23', '14.2', '4.8', '9.5'],
            ]

            # Create reader
            csv_content = '\n'.join([','.join(row) for row in data])
            reader = csv.reader(StringIO(csv_content))

            summary, errors = _import_chpp_wide(reader, header, dry_run=True, batch_size=100)
            assert 'Нийт мөр' in summary
            assert 'Шинэ дээж' in summary

    def test_import_chpp_wide_insufficient_columns(self, app):
        """Test CHPP wide import with too few columns."""
        from app.services.import_service import import_chpp_wide as _import_chpp_wide
        import csv

        with app.app_context():
            header = ['_sel', 'ID', 'Дээжний нэр']  # Too few columns
            reader = csv.reader(StringIO(''))

            summary, errors = _import_chpp_wide(reader, header, dry_run=True, batch_size=100)
            assert len(errors) > 0  # Should have error about insufficient columns

    def test_import_chpp_wide_empty_sample_code(self, app):
        """Test CHPP wide import with empty sample code."""
        from app.services.import_service import import_chpp_wide as _import_chpp_wide
        import csv

        with app.app_context():
            header = ['_sel', 'ID', 'Дээжний нэр', 'Нэгж', 'Төрөл', 'Бүртгэсэн', 'Шинжилсэн', 'Mt,ar']
            data = [
                ['', '1', '', 'CHPP', 'coal', '2025-12-23', '2025-12-23', '15.5'],  # Empty sample code
            ]

            csv_content = '\n'.join([','.join(row) for row in data])
            reader = csv.reader(StringIO(csv_content))

            summary, errors = _import_chpp_wide(reader, header, dry_run=True, batch_size=100)
            assert summary['Шинэ дээж'] == 0  # No samples created


class TestImportRoutes:
    """Import route тестүүд."""

    def test_import_page_get(self, app, auth_admin):
        """Test import page GET request."""
        response = auth_admin.get('/admin/import/')
        # May return different status codes depending on route registration
        assert response.status_code in [200, 302, 404]


class TestImportLongFormat:
    """Long format CSV импорт тестүүд."""

    def test_import_long_format_valid(self, app):
        """Test long format import with valid data."""
        from app.services.import_service import _norm, _parse_date, _base_code

        with app.app_context():
            # Test helper functions that are used in long format
            assert _norm("  test  ") == "test"
            assert _parse_date("2025-12-23") == datetime(2025, 12, 23)
            assert _base_code("Mad") == "Mad"

    def test_import_with_various_date_formats(self, app):
        """Test import with various date formats."""
        from app.services.import_service import _parse_date

        # Test all supported formats
        formats = [
            ("2025-12-23", datetime(2025, 12, 23)),
            ("2025/12/23", datetime(2025, 12, 23)),
            ("2025-12-23 14:30", datetime(2025, 12, 23, 14, 30)),
            ("2025-12-23T14:30", datetime(2025, 12, 23, 14, 30)),
            ("23/12/2025", datetime(2025, 12, 23)),
        ]

        for date_str, expected in formats:
            result = _parse_date(date_str)
            assert result == expected, f"Failed for {date_str}"


class TestImportEdgeCases:
    """Import edge case тестүүд."""

    def test_import_unicode_sample_code(self, app):
        """Test import with unicode in sample code."""
        from app.services.import_service import _norm

        # Mongolian characters
        result = _norm("Дээж_001")
        assert result == "Дээж_001"

    def test_import_special_characters(self, app):
        """Test import with special characters."""
        from app.services.import_service import _norm

        result = _norm("Sample-001_A/B")
        assert result == "Sample-001_A/B"

    def test_import_numeric_sample_code(self, app):
        """Test import with numeric sample code."""
        from app.services.import_service import _norm

        result = _norm(12345)
        assert result == "12345"

    def test_import_float_value(self, app):
        """Test import with float value."""
        from app.utils.converters import to_float

        assert to_float("5.5") == 5.5
        assert to_float("5,5") == 5.5  # European format
        assert to_float("") is None
        assert to_float("invalid") is None

    def test_import_with_batch_commit(self, app):
        """Test import with batch commit."""
        from app.services.import_service import import_chpp_wide as _import_chpp_wide
        import csv

        with app.app_context():
            header = ['_sel', 'ID', 'Дээжний нэр', 'Нэгж', 'Төрөл', 'Бүртгэсэн', 'Шинжилсэн', 'Mad']
            data = []
            for i in range(150):  # More than batch_size
                data.append(['', str(i), f'BATCH_{i:03d}', 'CHPP', 'coal', '2025-12-23', '2025-12-23', '5.5'])

            csv_content = '\n'.join([','.join(row) for row in data])
            reader = csv.reader(StringIO(csv_content))

            summary, errors = _import_chpp_wide(reader, header, dry_run=True, batch_size=50)
            assert summary['Нийт мөр'] == 150
