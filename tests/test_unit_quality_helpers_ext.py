# -*- coding: utf-8 -*-
"""
Quality helpers extended тестүүд
"""
import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime, date


class TestCanEditQuality:
    """can_edit_quality тестүүд"""

    def test_import_function(self):
        """Function import"""
        from app.utils.quality_helpers import can_edit_quality
        assert can_edit_quality is not None

    @patch('app.utils.quality_helpers.current_user')
    def test_admin_can_edit(self, mock_user):
        """Admin can edit"""
        from app.utils.quality_helpers import can_edit_quality
        mock_user.is_authenticated = True
        mock_user.role = 'admin'
        assert can_edit_quality() is True

    @patch('app.utils.quality_helpers.current_user')
    def test_manager_can_edit(self, mock_user):
        """Manager can edit"""
        from app.utils.quality_helpers import can_edit_quality
        mock_user.is_authenticated = True
        mock_user.role = 'manager'
        assert can_edit_quality() is True

    @patch('app.utils.quality_helpers.current_user')
    def test_senior_can_edit(self, mock_user):
        """Senior can edit"""
        from app.utils.quality_helpers import can_edit_quality
        mock_user.is_authenticated = True
        mock_user.role = 'senior'
        assert can_edit_quality() is True

    @patch('app.utils.quality_helpers.current_user')
    def test_chemist_cannot_edit(self, mock_user):
        """Chemist cannot edit"""
        from app.utils.quality_helpers import can_edit_quality
        mock_user.is_authenticated = True
        mock_user.role = 'chemist'
        assert can_edit_quality() is False

    @patch('app.utils.quality_helpers.current_user')
    def test_unauthenticated_cannot_edit(self, mock_user):
        """Unauthenticated cannot edit"""
        from app.utils.quality_helpers import can_edit_quality
        mock_user.is_authenticated = False
        assert can_edit_quality() is False


class TestRequireQualityEdit:
    """require_quality_edit decorator тестүүд"""

    def test_import_decorator(self):
        """Decorator import"""
        from app.utils.quality_helpers import require_quality_edit
        assert require_quality_edit is not None

    def test_decorator_returns_function(self):
        """Decorator returns function"""
        from app.utils.quality_helpers import require_quality_edit

        @require_quality_edit()
        def test_func():
            return "success"

        assert callable(test_func)


class TestCalculateStatusStats:
    """calculate_status_stats тестүүд"""

    def test_import_function(self):
        """Function import"""
        from app.utils.quality_helpers import calculate_status_stats
        assert calculate_status_stats is not None

    def test_empty_list(self):
        """Empty list returns total 0"""
        from app.utils.quality_helpers import calculate_status_stats
        result = calculate_status_stats([])
        assert result['total'] == 0

    def test_with_status_values(self):
        """Count specific status values"""
        from app.utils.quality_helpers import calculate_status_stats

        # Create mock items
        items = [
            MagicMock(status='open'),
            MagicMock(status='open'),
            MagicMock(status='closed'),
        ]

        result = calculate_status_stats(items, status_values=['open', 'closed'])
        assert result['total'] == 3
        assert result['open'] == 2
        assert result['closed'] == 1

    def test_auto_detect_statuses(self):
        """Auto-detect unique statuses"""
        from app.utils.quality_helpers import calculate_status_stats

        items = [
            MagicMock(status='active'),
            MagicMock(status='active'),
            MagicMock(status='inactive'),
        ]

        result = calculate_status_stats(items)
        assert result['total'] == 3
        assert result['active'] == 2
        assert result['inactive'] == 1

    def test_custom_status_field(self):
        """Custom status field"""
        from app.utils.quality_helpers import calculate_status_stats

        items = [
            MagicMock(state='pending'),
            MagicMock(state='approved'),
        ]

        result = calculate_status_stats(items, status_field='state', status_values=['pending', 'approved'])
        assert result['pending'] == 1
        assert result['approved'] == 1


class TestGenerateSequentialCode:
    """generate_sequential_code тестүүд"""

    def test_import_function(self):
        """Function import"""
        from app.utils.quality_helpers import generate_sequential_code
        assert generate_sequential_code is not None

    @patch('app.utils.quality_helpers.now_local')
    def test_first_code_of_year(self, mock_now_local):
        """First code of year"""
        from app.utils.quality_helpers import generate_sequential_code
        mock_now_local.return_value.year = 2025

        mock_model = MagicMock()
        mock_model.query.filter.return_value.order_by.return_value.first.return_value = None

        result = generate_sequential_code(mock_model, 'ca_number', 'CA')
        assert result == 'CA-2025-0001'

    @patch('app.utils.quality_helpers.now_local')
    def test_increment_existing_code(self, mock_now_local):
        """Increment existing code"""
        from app.utils.quality_helpers import generate_sequential_code
        mock_now_local.return_value.year = 2025

        mock_last = MagicMock()
        mock_last.ca_number = 'CA-2025-0005'

        mock_model = MagicMock()
        mock_model.query.filter.return_value.order_by.return_value.first.return_value = mock_last

        result = generate_sequential_code(mock_model, 'ca_number', 'CA')
        assert result == 'CA-2025-0006'

    @patch('app.utils.quality_helpers.now_local')
    def test_custom_padding(self, mock_now_local):
        """Custom padding"""
        from app.utils.quality_helpers import generate_sequential_code
        mock_now_local.return_value.year = 2025

        mock_model = MagicMock()
        mock_model.query.filter.return_value.order_by.return_value.first.return_value = None

        result = generate_sequential_code(mock_model, 'code', 'TEST', padding=6)
        assert result == 'TEST-2025-000001'


class TestParseDate:
    """parse_date тестүүд"""

    def test_import_function(self):
        """Function import"""
        from app.utils.quality_helpers import parse_date
        assert parse_date is not None

    def test_valid_date(self):
        """Valid date string"""
        from app.utils.quality_helpers import parse_date
        result = parse_date('2025-01-15')
        assert result == date(2025, 1, 15)

    def test_none_input(self):
        """None input returns default"""
        from app.utils.quality_helpers import parse_date
        result = parse_date(None, default='today')
        assert result == 'today'

    def test_empty_input(self):
        """Empty input returns default"""
        from app.utils.quality_helpers import parse_date
        result = parse_date('', default=None)
        assert result is None

    def test_invalid_format(self):
        """Invalid format returns default"""
        from app.utils.quality_helpers import parse_date
        result = parse_date('15-01-2025', default=None)
        assert result is None


class TestParseDatetime:
    """parse_datetime тестүүд"""

    def test_import_function(self):
        """Function import"""
        from app.utils.quality_helpers import parse_datetime
        assert parse_datetime is not None

    def test_full_datetime(self):
        """Full datetime format"""
        from app.utils.quality_helpers import parse_datetime
        result = parse_datetime('2025-01-15 10:30:00')
        assert result == datetime(2025, 1, 15, 10, 30, 0)

    def test_datetime_no_seconds(self):
        """Datetime without seconds"""
        from app.utils.quality_helpers import parse_datetime
        result = parse_datetime('2025-01-15 10:30')
        assert result == datetime(2025, 1, 15, 10, 30)

    def test_iso_format(self):
        """ISO format"""
        from app.utils.quality_helpers import parse_datetime
        result = parse_datetime('2025-01-15T10:30:00')
        assert result == datetime(2025, 1, 15, 10, 30, 0)

    def test_date_only(self):
        """Date only format"""
        from app.utils.quality_helpers import parse_datetime
        result = parse_datetime('2025-01-15')
        assert result == datetime(2025, 1, 15, 0, 0, 0)

    def test_none_input(self):
        """None input returns default"""
        from app.utils.quality_helpers import parse_datetime
        result = parse_datetime(None, default='now')
        assert result == 'now'

    def test_invalid_format(self):
        """Invalid format returns default"""
        from app.utils.quality_helpers import parse_datetime
        result = parse_datetime('invalid-date', default=None)
        assert result is None
