# tests/unit/test_quality_helpers.py
# -*- coding: utf-8 -*-
"""
Quality Helpers тест

Tests for utility functions in app/utils/quality_helpers.py
"""

import pytest
from datetime import datetime, date
from unittest.mock import Mock, MagicMock, patch

from app.utils.quality_helpers import (
    calculate_status_stats,
    parse_date,
    parse_datetime,
)


class TestCalculateStatusStats:
    """calculate_status_stats() функцийн тест"""

    def test_empty_items(self):
        """Хоосон жагсаалт"""
        result = calculate_status_stats([])
        assert result == {'total': 0}

    def test_with_status_values(self):
        """Тодорхой status утгуудаар"""
        # Mock objects
        item1 = Mock(status='open')
        item2 = Mock(status='open')
        item3 = Mock(status='closed')
        items = [item1, item2, item3]

        result = calculate_status_stats(
            items,
            status_values=['open', 'closed', 'in_progress']
        )

        assert result['total'] == 3
        assert result['open'] == 2
        assert result['closed'] == 1
        assert result['in_progress'] == 0

    def test_auto_detect_statuses(self):
        """Status утгуудыг автоматаар олох"""
        item1 = Mock(status='new')
        item2 = Mock(status='new')
        item3 = Mock(status='resolved')
        items = [item1, item2, item3]

        result = calculate_status_stats(items)

        assert result['total'] == 3
        assert result['new'] == 2
        assert result['resolved'] == 1

    def test_custom_status_field(self):
        """Өөр талбарын нэр ашиглах"""
        item1 = Mock(state='active')
        item2 = Mock(state='inactive')
        items = [item1, item2]

        result = calculate_status_stats(
            items,
            status_field='state',
            status_values=['active', 'inactive']
        )

        assert result['active'] == 1
        assert result['inactive'] == 1

    def test_missing_status_attribute(self):
        """Status талбар байхгүй үед"""
        item1 = Mock(spec=[])  # No attributes
        items = [item1]

        result = calculate_status_stats(
            items,
            status_values=['open', 'closed']
        )

        assert result['total'] == 1
        assert result['open'] == 0
        assert result['closed'] == 0

    def test_none_status_values(self):
        """None status утгуудыг auto-detect хийхгүй"""
        item1 = Mock(status=None)
        item2 = Mock(status='active')
        items = [item1, item2]

        result = calculate_status_stats(items)

        assert result['total'] == 2
        assert result.get('active') == 1
        assert None not in result  # None should not be a key


class TestParseDate:
    """parse_date() функцийн тест"""

    def test_valid_date(self):
        """Зөв форматтай огноо"""
        result = parse_date('2025-12-11')
        assert result == date(2025, 12, 11)

    def test_empty_string(self):
        """Хоосон string"""
        result = parse_date('')
        assert result is None

    def test_none_input(self):
        """None утга"""
        result = parse_date(None)
        assert result is None

    def test_invalid_format(self):
        """Буруу формат"""
        result = parse_date('12-11-2025')  # DD-MM-YYYY
        assert result is None

    def test_invalid_date(self):
        """Байхгүй огноо"""
        result = parse_date('2025-13-45')  # Invalid month/day
        assert result is None

    def test_default_value(self):
        """Default утга буцаах"""
        default = date(2000, 1, 1)
        result = parse_date('invalid', default=default)
        assert result == default

    def test_none_default(self):
        """Default=None"""
        result = parse_date('invalid', default=None)
        assert result is None


class TestParseDatetime:
    """parse_datetime() функцийн тест"""

    def test_full_datetime(self):
        """Бүтэн datetime (YYYY-MM-DD HH:MM:SS)"""
        result = parse_datetime('2025-12-11 14:30:45')
        assert result == datetime(2025, 12, 11, 14, 30, 45)

    def test_datetime_without_seconds(self):
        """Секундгүй (YYYY-MM-DD HH:MM)"""
        result = parse_datetime('2025-12-11 14:30')
        assert result == datetime(2025, 12, 11, 14, 30)

    def test_iso_format_with_t(self):
        """ISO format with T separator"""
        result = parse_datetime('2025-12-11T14:30:45')
        assert result == datetime(2025, 12, 11, 14, 30, 45)

    def test_iso_format_without_seconds(self):
        """ISO format without seconds"""
        result = parse_datetime('2025-12-11T14:30')
        assert result == datetime(2025, 12, 11, 14, 30)

    def test_date_only(self):
        """Зөвхөн огноо (YYYY-MM-DD)"""
        result = parse_datetime('2025-12-11')
        assert result == datetime(2025, 12, 11, 0, 0, 0)

    def test_empty_string(self):
        """Хоосон string"""
        result = parse_datetime('')
        assert result is None

    def test_none_input(self):
        """None утга"""
        result = parse_datetime(None)
        assert result is None

    def test_invalid_format(self):
        """Буруу формат"""
        result = parse_datetime('11/12/2025 2:30 PM')
        assert result is None

    def test_default_value(self):
        """Default утга буцаах"""
        default = datetime(2000, 1, 1, 0, 0, 0)
        result = parse_datetime('invalid', default=default)
        assert result == default


class TestCanEditQualityAndDecorator:
    """can_edit_quality() болон require_quality_edit() тестүүд"""

    def test_can_edit_quality_admin(self, app):
        """Admin эрхтэй хэрэглэгч"""
        with app.app_context():
            from app.utils.quality_helpers import can_edit_quality
            with patch('app.utils.quality_helpers.current_user') as mock_user:
                mock_user.is_authenticated = True
                mock_user.role = 'admin'
                assert can_edit_quality() is True

    def test_can_edit_quality_senior(self, app):
        """Senior эрхтэй хэрэглэгч"""
        with app.app_context():
            from app.utils.quality_helpers import can_edit_quality
            with patch('app.utils.quality_helpers.current_user') as mock_user:
                mock_user.is_authenticated = True
                mock_user.role = 'senior'
                assert can_edit_quality() is True

    def test_can_edit_quality_manager(self, app):
        """Manager эрхтэй хэрэглэгч"""
        with app.app_context():
            from app.utils.quality_helpers import can_edit_quality
            with patch('app.utils.quality_helpers.current_user') as mock_user:
                mock_user.is_authenticated = True
                mock_user.role = 'manager'
                assert can_edit_quality() is True

    def test_can_edit_quality_chemist_denied(self, app):
        """Chemist эрхгүй"""
        with app.app_context():
            from app.utils.quality_helpers import can_edit_quality
            with patch('app.utils.quality_helpers.current_user') as mock_user:
                mock_user.is_authenticated = True
                mock_user.role = 'chemist'
                assert can_edit_quality() is False

    def test_can_edit_quality_not_authenticated(self, app):
        """Нэвтрээгүй хэрэглэгч"""
        with app.app_context():
            from app.utils.quality_helpers import can_edit_quality
            with patch('app.utils.quality_helpers.current_user') as mock_user:
                mock_user.is_authenticated = False
                mock_user.role = 'admin'
                assert can_edit_quality() is False
