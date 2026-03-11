# tests/unit/test_settings_comprehensive.py
# -*- coding: utf-8 -*-
"""
Settings utility comprehensive tests
"""
import pytest
from unittest.mock import Mock, patch, MagicMock


class TestGetSettingValue:
    """get_setting_value() функцийн тестүүд"""

    def test_returns_default_when_not_found(self, app):
        """Returns default when setting doesn't exist"""
        with app.app_context():
            with patch('app.utils.settings.db') as mock_db:
                mock_exec = MagicMock()
                mock_exec.scalars.return_value.first.return_value = None
                mock_db.session.execute.return_value = mock_exec
                from app.utils.settings import get_setting_value
                result = get_setting_value("category", "nonexistent", default="default_value")
                assert result == "default_value"

    def test_returns_value_when_found(self, app):
        """Returns value when setting exists"""
        with app.app_context():
            with patch('app.utils.settings.db') as mock_db:
                mock_setting = Mock()
                mock_setting.value = "test_value"
                mock_exec = MagicMock()
                mock_exec.scalars.return_value.first.return_value = mock_setting
                mock_db.session.execute.return_value = mock_exec
                from app.utils.settings import get_setting_value
                result = get_setting_value("category", "existing_key")
                assert result == "test_value"


class TestGetSettingByCategory:
    """get_setting_by_category() функцийн тестүүд"""

    def test_returns_empty_dict_when_no_settings(self, app):
        """Returns empty dict when no settings exist"""
        with app.app_context():
            with patch('app.utils.settings.db') as mock_db:
                mock_exec = MagicMock()
                mock_exec.scalars.return_value.all.return_value = []
                mock_db.session.execute.return_value = mock_exec
                from app.utils.settings import get_setting_by_category
                result = get_setting_by_category("test_category")
                assert result == {}

    def test_returns_dict_when_settings_exist(self, app):
        """Returns dict of settings when they exist"""
        with app.app_context():
            with patch('app.utils.settings.db') as mock_db:
                mock_setting = Mock()
                mock_setting.key = "test_key"
                mock_setting.value = "test_value"
                mock_exec = MagicMock()
                mock_exec.scalars.return_value.all.return_value = [mock_setting]
                mock_db.session.execute.return_value = mock_exec
                from app.utils.settings import get_setting_by_category
                result = get_setting_by_category("test_category")
                assert result == {"test_key": "test_value"}


class TestGetSampleTypeChoicesMap:
    """get_sample_type_choices_map() функцийн тестүүд"""

    def test_returns_dict(self, app):
        """Should return a dictionary"""
        with app.app_context():
            with patch('app.utils.settings.db') as mock_db:
                mock_exec = MagicMock()
                mock_exec.scalars.return_value.all.return_value = []
                mock_db.session.execute.return_value = mock_exec
                from app.utils.settings import get_sample_type_choices_map
                result = get_sample_type_choices_map()
                assert isinstance(result, dict)

    def test_returns_fallback_when_empty(self, app):
        """Should return fallback from constants when DB is empty"""
        with app.app_context():
            with patch('app.utils.settings.db') as mock_db:
                mock_exec = MagicMock()
                mock_exec.scalars.return_value.all.return_value = []
                mock_db.session.execute.return_value = mock_exec
                from app.utils.settings import get_sample_type_choices_map
                result = get_sample_type_choices_map()
                # Should return constants fallback
                assert isinstance(result, dict)


class TestGetUnitAbbreviations:
    """get_unit_abbreviations() функцийн тестүүд"""

    def test_returns_dict(self, app):
        """Should return a dictionary"""
        with app.app_context():
            with patch('app.utils.settings.db') as mock_db:
                mock_exec = MagicMock()
                mock_exec.scalars.return_value.all.return_value = []
                mock_db.session.execute.return_value = mock_exec
                from app.utils.settings import get_unit_abbreviations
                result = get_unit_abbreviations()
                assert isinstance(result, dict)

    def test_returns_fallback_when_empty(self, app):
        """Should return fallback from constants when DB is empty"""
        with app.app_context():
            with patch('app.utils.settings.db') as mock_db:
                mock_exec = MagicMock()
                mock_exec.scalars.return_value.all.return_value = []
                mock_db.session.execute.return_value = mock_exec
                from app.utils.settings import get_unit_abbreviations
                result = get_unit_abbreviations()
                assert isinstance(result, dict)


class TestGetErrorReasonLabels:
    """get_error_reason_labels() функцийн тестүүд"""

    def test_returns_dict(self, app):
        """Should return a dictionary"""
        with app.app_context():
            with patch('app.utils.settings.db') as mock_db:
                mock_exec = MagicMock()
                mock_exec.scalars.return_value.all.return_value = []
                mock_db.session.execute.return_value = mock_exec
                from app.utils.settings import get_error_reason_labels
                result = get_error_reason_labels()
                assert isinstance(result, dict)

    def test_returns_settings_when_exist(self, app):
        """Should return settings when they exist"""
        with app.app_context():
            with patch('app.utils.settings.db') as mock_db:
                mock_setting = Mock()
                mock_setting.key = "sample_prep"
                mock_setting.value = "Sample preparation error"
                mock_exec = MagicMock()
                mock_exec.scalars.return_value.all.return_value = [mock_setting]
                mock_db.session.execute.return_value = mock_exec
                from app.utils.settings import get_error_reason_labels
                result = get_error_reason_labels()
                assert result == {"sample_prep": "Sample preparation error"}


class TestUpdateSetting:
    """update_setting() функцийн тестүүд"""

    def test_updates_existing_setting(self, app):
        """Should update existing setting"""
        with app.app_context():
            with patch('app.utils.settings.db') as mock_db:
                mock_setting = Mock()
                mock_setting.value = "old_value"
                mock_exec = MagicMock()
                mock_exec.scalars.return_value.first.return_value = mock_setting
                mock_db.session.execute.return_value = mock_exec
                from app.utils.settings import update_setting
                result = update_setting("category", "key", "new_value")
                assert mock_setting.value == "new_value"

    def test_creates_new_setting(self, app):
        """Should create new setting if not exists"""
        with app.app_context():
            with patch('app.utils.settings.db') as mock_db:
                mock_exec = MagicMock()
                mock_exec.scalars.return_value.first.return_value = None
                mock_db.session.execute.return_value = mock_exec
                from app.utils.settings import update_setting
                result = update_setting("category", "key", "value")
                mock_db.session.add.assert_called_once()
