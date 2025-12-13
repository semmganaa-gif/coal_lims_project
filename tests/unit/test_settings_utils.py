# -*- coding: utf-8 -*-
"""
Settings utils тестүүд
"""
import pytest


class TestSettingsModule:
    """Settings module тестүүд"""

    def test_import_module(self):
        """Module import"""
        from app.utils import settings
        assert settings is not None


class TestGetSettingValue:
    """get_setting_value тестүүд"""

    def test_import_function(self):
        """Function import"""
        from app.utils.settings import get_setting_value
        assert get_setting_value is not None

    def test_get_nonexistent(self):
        """Get nonexistent setting"""
        from app import create_app
        from app.utils.settings import get_setting_value

        app = create_app()
        with app.app_context():
            result = get_setting_value('nonexistent_category', 'nonexistent_key')
            assert result is None

    def test_get_with_default(self):
        """Get with default value"""
        from app import create_app
        from app.utils.settings import get_setting_value

        app = create_app()
        with app.app_context():
            result = get_setting_value('nonexistent', 'key', default='default_value')
            assert result == 'default_value'


class TestGetSettingByCategory:
    """get_setting_by_category тестүүд"""

    def test_import_function(self):
        """Function import"""
        from app.utils.settings import get_setting_by_category
        assert get_setting_by_category is not None

    def test_get_category(self):
        """Get settings by category"""
        from app import create_app
        from app.utils.settings import get_setting_by_category

        app = create_app()
        with app.app_context():
            result = get_setting_by_category('general')
            assert isinstance(result, (dict, list, type(None)))


class TestUpdateSetting:
    """update_setting тестүүд"""

    def test_import_function(self):
        """Function import"""
        from app.utils.settings import update_setting
        assert update_setting is not None


class TestGetSampleTypeChoices:
    """get_sample_type_choices_map тестүүд"""

    def test_import_function(self):
        """Function import"""
        from app.utils.settings import get_sample_type_choices_map
        assert get_sample_type_choices_map is not None


class TestGetUnitAbbreviations:
    """get_unit_abbreviations тестүүд"""

    def test_import_function(self):
        """Function import"""
        from app.utils.settings import get_unit_abbreviations
        assert get_unit_abbreviations is not None


class TestGetErrorReasonLabels:
    """get_error_reason_labels тестүүд"""

    def test_import_function(self):
        """Function import"""
        from app.utils.settings import get_error_reason_labels
        assert get_error_reason_labels is not None
