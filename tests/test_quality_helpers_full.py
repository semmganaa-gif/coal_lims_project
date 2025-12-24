# tests/test_quality_helpers_full.py
# -*- coding: utf-8 -*-
"""
Complete tests for app/utils/quality_helpers.py - targeting 100% coverage.
"""

import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime, date


class TestCanEditQuality:
    """Tests for can_edit_quality function."""

    def test_admin_can_edit(self, app):
        """Test admin can edit quality."""
        with app.app_context():
            from app.utils.quality_helpers import can_edit_quality
            with patch('app.utils.quality_helpers.current_user') as mock_user:
                mock_user.is_authenticated = True
                mock_user.role = 'admin'
                assert can_edit_quality() is True

    def test_senior_can_edit(self, app):
        """Test senior can edit quality."""
        with app.app_context():
            from app.utils.quality_helpers import can_edit_quality
            with patch('app.utils.quality_helpers.current_user') as mock_user:
                mock_user.is_authenticated = True
                mock_user.role = 'senior'
                assert can_edit_quality() is True

    def test_manager_can_edit(self, app):
        """Test manager can edit quality."""
        with app.app_context():
            from app.utils.quality_helpers import can_edit_quality
            with patch('app.utils.quality_helpers.current_user') as mock_user:
                mock_user.is_authenticated = True
                mock_user.role = 'manager'
                assert can_edit_quality() is True

    def test_chemist_cannot_edit(self, app):
        """Test chemist cannot edit quality."""
        with app.app_context():
            from app.utils.quality_helpers import can_edit_quality
            with patch('app.utils.quality_helpers.current_user') as mock_user:
                mock_user.is_authenticated = True
                mock_user.role = 'chemist'
                assert can_edit_quality() is False

    def test_technician_cannot_edit(self, app):
        """Test technician cannot edit quality."""
        with app.app_context():
            from app.utils.quality_helpers import can_edit_quality
            with patch('app.utils.quality_helpers.current_user') as mock_user:
                mock_user.is_authenticated = True
                mock_user.role = 'technician'
                assert can_edit_quality() is False

    def test_viewer_cannot_edit(self, app):
        """Test viewer cannot edit quality."""
        with app.app_context():
            from app.utils.quality_helpers import can_edit_quality
            with patch('app.utils.quality_helpers.current_user') as mock_user:
                mock_user.is_authenticated = True
                mock_user.role = 'viewer'
                assert can_edit_quality() is False

    def test_unauthenticated_cannot_edit(self, app):
        """Test unauthenticated user cannot edit quality."""
        with app.app_context():
            from app.utils.quality_helpers import can_edit_quality
            with patch('app.utils.quality_helpers.current_user') as mock_user:
                mock_user.is_authenticated = False
                mock_user.role = 'admin'
                assert can_edit_quality() is False


class TestRequireQualityEdit:
    """Tests for require_quality_edit decorator."""

    def test_decorator_allows_admin(self, app, client):
        """Test decorator allows admin."""
        with app.test_request_context('/'):
            from app.utils.quality_helpers import require_quality_edit

            @require_quality_edit()
            def test_view():
                return "Success"

            with patch('app.utils.quality_helpers.can_edit_quality', return_value=True):
                result = test_view()
                assert result == "Success"

    def test_decorator_redirects_non_admin(self, app, client):
        """Test decorator redirects non-admin."""
        with app.test_request_context('/'):
            from app.utils.quality_helpers import require_quality_edit

            @require_quality_edit('main.index')
            def test_view():
                return "Success"

            with patch('app.utils.quality_helpers.can_edit_quality', return_value=False):
                with patch('app.utils.quality_helpers.flash'):
                    result = test_view()
                    # Should be a redirect response
                    assert result.status_code == 302

    def test_decorator_custom_redirect(self, app, client):
        """Test decorator with custom redirect endpoint."""
        with app.test_request_context('/'):
            from app.utils.quality_helpers import require_quality_edit

            @require_quality_edit('quality.capa_list')
            def test_view():
                return "Success"

            # Just verify it's callable
            assert callable(test_view)


class TestCalculateStatusStats:
    """Tests for calculate_status_stats function."""

    def test_empty_list(self, app):
        """Test with empty list."""
        with app.app_context():
            from app.utils.quality_helpers import calculate_status_stats
            result = calculate_status_stats([])
            assert result['total'] == 0

    def test_with_status_values(self, app):
        """Test with specified status values."""
        with app.app_context():
            from app.utils.quality_helpers import calculate_status_stats

            class MockItem:
                def __init__(self, status):
                    self.status = status

            items = [
                MockItem('open'),
                MockItem('open'),
                MockItem('closed'),
                MockItem('in_progress')
            ]
            result = calculate_status_stats(items, status_values=['open', 'closed', 'in_progress'])
            assert result['total'] == 4
            assert result['open'] == 2
            assert result['closed'] == 1
            assert result['in_progress'] == 1

    def test_auto_detect_statuses(self, app):
        """Test auto-detecting statuses when status_values not provided."""
        with app.app_context():
            from app.utils.quality_helpers import calculate_status_stats

            class MockItem:
                def __init__(self, status):
                    self.status = status

            items = [
                MockItem('pending'),
                MockItem('approved'),
                MockItem('pending')
            ]
            result = calculate_status_stats(items)
            assert result['total'] == 3
            assert result['pending'] == 2
            assert result['approved'] == 1

    def test_custom_status_field(self, app):
        """Test with custom status field name."""
        with app.app_context():
            from app.utils.quality_helpers import calculate_status_stats

            class MockItem:
                def __init__(self, state):
                    self.state = state

            items = [MockItem('active'), MockItem('inactive')]
            result = calculate_status_stats(items, status_field='state', status_values=['active', 'inactive'])
            assert result['active'] == 1
            assert result['inactive'] == 1

    def test_none_status(self, app):
        """Test items with None status."""
        with app.app_context():
            from app.utils.quality_helpers import calculate_status_stats

            class MockItem:
                def __init__(self, status):
                    self.status = status

            items = [MockItem(None), MockItem('open')]
            result = calculate_status_stats(items)
            assert result['total'] == 2
            # None should not be counted as a status key


class TestGenerateSequentialCode:
    """Tests for generate_sequential_code function."""

    def test_first_code(self, app, db):
        """Test generating first code when no existing codes."""
        with app.app_context():
            from app.utils.quality_helpers import generate_sequential_code
            from app.models import CorrectiveAction

            with patch.object(CorrectiveAction.query, 'filter') as mock_filter:
                mock_filter.return_value.order_by.return_value.first.return_value = None
                code = generate_sequential_code(CorrectiveAction, 'ca_number', 'CA', year=2025)
                assert code == 'CA-2025-0001'

    def test_next_code(self, app, db):
        """Test generating next code after existing ones."""
        with app.app_context():
            from app.utils.quality_helpers import generate_sequential_code
            from app.models import CorrectiveAction
            from datetime import date

            # Create an actual record in the database
            ca = CorrectiveAction(
                ca_number='CA-2025-0005',
                issue_date=date.today(),
                issue_description='Test CA',
                status='open'
            )
            db.session.add(ca)
            db.session.commit()

            code = generate_sequential_code(CorrectiveAction, 'ca_number', 'CA', year=2025)
            assert code == 'CA-2025-0006'

            # Cleanup
            db.session.delete(ca)
            db.session.commit()

    def test_custom_padding(self, app, db):
        """Test with custom padding."""
        with app.app_context():
            from app.utils.quality_helpers import generate_sequential_code
            from app.models import CorrectiveAction

            with patch.object(CorrectiveAction.query, 'filter') as mock_filter:
                mock_filter.return_value.order_by.return_value.first.return_value = None
                code = generate_sequential_code(CorrectiveAction, 'ca_number', 'CA', year=2025, padding=6)
                assert code == 'CA-2025-000001'

    def test_invalid_last_code(self, app, db):
        """Test with invalid last code format."""
        with app.app_context():
            from app.utils.quality_helpers import generate_sequential_code
            from app.models import CorrectiveAction

            mock_record = MagicMock()
            mock_record.ca_number = 'CA-2025-invalid'

            with patch.object(CorrectiveAction.query, 'filter') as mock_filter:
                mock_filter.return_value.order_by.return_value.first.return_value = mock_record
                code = generate_sequential_code(CorrectiveAction, 'ca_number', 'CA', year=2025)
                assert code == 'CA-2025-0001'

    def test_default_year(self, app, db):
        """Test with default year (current year)."""
        with app.app_context():
            from app.utils.quality_helpers import generate_sequential_code
            from app.models import CorrectiveAction

            with patch.object(CorrectiveAction.query, 'filter') as mock_filter:
                mock_filter.return_value.order_by.return_value.first.return_value = None
                code = generate_sequential_code(CorrectiveAction, 'ca_number', 'CA')
                assert 'CA-' in code


class TestParseDate:
    """Tests for parse_date function."""

    def test_valid_date(self, app):
        """Test with valid date string."""
        with app.app_context():
            from app.utils.quality_helpers import parse_date
            result = parse_date('2025-12-25')
            assert result == date(2025, 12, 25)

    def test_empty_string(self, app):
        """Test with empty string."""
        with app.app_context():
            from app.utils.quality_helpers import parse_date
            result = parse_date('')
            assert result is None

    def test_none_input(self, app):
        """Test with None input."""
        with app.app_context():
            from app.utils.quality_helpers import parse_date
            result = parse_date(None)
            assert result is None

    def test_default_value(self, app):
        """Test with default value."""
        with app.app_context():
            from app.utils.quality_helpers import parse_date
            default = date(2020, 1, 1)
            result = parse_date('', default=default)
            assert result == default

    def test_invalid_format(self, app):
        """Test with invalid date format."""
        with app.app_context():
            from app.utils.quality_helpers import parse_date
            result = parse_date('25/12/2025')
            assert result is None

    def test_invalid_date(self, app):
        """Test with invalid date value."""
        with app.app_context():
            from app.utils.quality_helpers import parse_date
            result = parse_date('2025-13-45')
            assert result is None


class TestParseDatetime:
    """Tests for parse_datetime function."""

    def test_full_datetime(self, app):
        """Test with full datetime string."""
        with app.app_context():
            from app.utils.quality_helpers import parse_datetime
            result = parse_datetime('2025-12-25 14:30:45')
            assert result == datetime(2025, 12, 25, 14, 30, 45)

    def test_datetime_no_seconds(self, app):
        """Test with datetime without seconds."""
        with app.app_context():
            from app.utils.quality_helpers import parse_datetime
            result = parse_datetime('2025-12-25 14:30')
            assert result == datetime(2025, 12, 25, 14, 30)

    def test_iso_format(self, app):
        """Test with ISO format (T separator)."""
        with app.app_context():
            from app.utils.quality_helpers import parse_datetime
            result = parse_datetime('2025-12-25T14:30:45')
            assert result == datetime(2025, 12, 25, 14, 30, 45)

    def test_iso_format_no_seconds(self, app):
        """Test with ISO format without seconds."""
        with app.app_context():
            from app.utils.quality_helpers import parse_datetime
            result = parse_datetime('2025-12-25T14:30')
            assert result == datetime(2025, 12, 25, 14, 30)

    def test_date_only(self, app):
        """Test with date only string."""
        with app.app_context():
            from app.utils.quality_helpers import parse_datetime
            result = parse_datetime('2025-12-25')
            assert result == datetime(2025, 12, 25, 0, 0, 0)

    def test_empty_string(self, app):
        """Test with empty string."""
        with app.app_context():
            from app.utils.quality_helpers import parse_datetime
            result = parse_datetime('')
            assert result is None

    def test_none_input(self, app):
        """Test with None input."""
        with app.app_context():
            from app.utils.quality_helpers import parse_datetime
            result = parse_datetime(None)
            assert result is None

    def test_invalid_format(self, app):
        """Test with invalid format."""
        with app.app_context():
            from app.utils.quality_helpers import parse_datetime
            result = parse_datetime('25/12/2025 14:30')
            assert result is None

    def test_default_value(self, app):
        """Test with default value on invalid input."""
        with app.app_context():
            from app.utils.quality_helpers import parse_datetime
            default = datetime(2020, 1, 1)
            result = parse_datetime('invalid', default=default)
            assert result == default
