# tests/test_settings_deep.py
# -*- coding: utf-8 -*-
"""
Deep coverage tests for app/utils/settings.py
"""

import pytest
from unittest.mock import patch, MagicMock


class TestGetErrorReasonLabels:
    """Tests for get_error_reason_labels function."""

    def test_get_error_reason_labels_empty(self, app, db):
        """Test get_error_reason_labels with no settings."""
        with app.app_context():
            from app.utils.settings import get_error_reason_labels
            result = get_error_reason_labels()
            assert isinstance(result, dict)

    def test_get_error_reason_labels_with_data(self, app, db):
        """Test get_error_reason_labels with settings data."""
        with app.app_context():
            from app.utils.settings import get_error_reason_labels
            from app.models import SystemSetting

            # Create test setting
            setting = SystemSetting(
                category='error_reason',
                key='test_error',
                value='Test Error Label',
                is_active=True,
                sort_order=1
            )
            db.session.add(setting)
            db.session.commit()

            result = get_error_reason_labels()
            assert isinstance(result, dict)
            assert 'test_error' in result
            assert result['test_error'] == 'Test Error Label'


class TestGetSettingByCategory:
    """Tests for get_setting_by_category function."""

    def test_get_setting_by_category_empty(self, app, db):
        """Test get_setting_by_category with empty category."""
        with app.app_context():
            from app.utils.settings import get_setting_by_category
            result = get_setting_by_category('nonexistent_category')
            assert isinstance(result, dict)
            assert len(result) == 0

    def test_get_setting_by_category_with_data(self, app, db):
        """Test get_setting_by_category with data."""
        with app.app_context():
            from app.utils.settings import get_setting_by_category
            from app.models import SystemSetting

            # Create test settings
            setting1 = SystemSetting(
                category='test_category',
                key='key1',
                value='value1',
                is_active=True,
                sort_order=1
            )
            setting2 = SystemSetting(
                category='test_category',
                key='key2',
                value='value2',
                is_active=True,
                sort_order=2
            )
            db.session.add_all([setting1, setting2])
            db.session.commit()

            result = get_setting_by_category('test_category')
            assert 'key1' in result
            assert 'key2' in result

    def test_get_setting_by_category_inactive_excluded(self, app, db):
        """Test get_setting_by_category excludes inactive."""
        with app.app_context():
            from app.utils.settings import get_setting_by_category
            from app.models import SystemSetting

            # Create inactive setting
            setting = SystemSetting(
                category='inactive_cat',
                key='inactive_key',
                value='value',
                is_active=False,
                sort_order=1
            )
            db.session.add(setting)
            db.session.commit()

            result = get_setting_by_category('inactive_cat')
            assert 'inactive_key' not in result


class TestGetSettingValue:
    """Tests for get_setting_value function."""

    def test_get_setting_value_not_found(self, app, db):
        """Test get_setting_value with not found key."""
        with app.app_context():
            from app.utils.settings import get_setting_value
            result = get_setting_value('cat', 'notfound')
            assert result is None

    def test_get_setting_value_with_default(self, app, db):
        """Test get_setting_value with default value."""
        with app.app_context():
            from app.utils.settings import get_setting_value
            result = get_setting_value('cat', 'notfound', default='default_val')
            assert result == 'default_val'

    def test_get_setting_value_found(self, app, db):
        """Test get_setting_value with existing key."""
        with app.app_context():
            from app.utils.settings import get_setting_value
            from app.models import SystemSetting

            setting = SystemSetting(
                category='my_cat',
                key='my_key',
                value='my_value',
                is_active=True,
                sort_order=1
            )
            db.session.add(setting)
            db.session.commit()

            result = get_setting_value('my_cat', 'my_key')
            assert result == 'my_value'

    def test_get_setting_value_inactive_not_found(self, app, db):
        """Test get_setting_value returns None for inactive."""
        with app.app_context():
            from app.utils.settings import get_setting_value
            from app.models import SystemSetting

            setting = SystemSetting(
                category='cat_inactive',
                key='key_inactive',
                value='value',
                is_active=False,
                sort_order=1
            )
            db.session.add(setting)
            db.session.commit()

            result = get_setting_value('cat_inactive', 'key_inactive', default='fallback')
            assert result == 'fallback'


class TestUpdateSetting:
    """Tests for update_setting function."""

    def test_update_setting_create_new(self, app, db):
        """Test update_setting creates new setting."""
        with app.app_context():
            from app.utils.settings import update_setting
            from app.models import SystemSetting

            result = update_setting('new_cat', 'new_key', 'new_value')
            assert result is not None
            assert result.category == 'new_cat'
            assert result.key == 'new_key'
            assert result.value == 'new_value'

    def test_update_setting_update_existing(self, app, db):
        """Test update_setting updates existing setting."""
        with app.app_context():
            from app.utils.settings import update_setting
            from app.models import SystemSetting

            # Create initial setting
            setting = SystemSetting(
                category='upd_cat',
                key='upd_key',
                value='old_value',
                is_active=True,
                sort_order=1
            )
            db.session.add(setting)
            db.session.commit()

            # Update it
            result = update_setting('upd_cat', 'upd_key', 'new_value')
            assert result.value == 'new_value'

    def test_update_setting_with_user_id(self, app, db):
        """Test update_setting with updated_by_id."""
        with app.app_context():
            from app.utils.settings import update_setting

            result = update_setting('cat_user', 'key_user', 'value', updated_by_id=1)
            assert result is not None
            assert result.updated_by_id == 1


class TestGetSampleTypeChoicesMap:
    """Tests for get_sample_type_choices_map function."""

    def test_get_sample_type_choices_map_fallback(self, app, db):
        """Test get_sample_type_choices_map returns fallback."""
        with app.app_context():
            from app.utils.settings import get_sample_type_choices_map
            result = get_sample_type_choices_map()
            assert isinstance(result, dict)

    def test_get_sample_type_choices_map_from_db(self, app, db):
        """Test get_sample_type_choices_map from DB."""
        with app.app_context():
            from app.utils.settings import get_sample_type_choices_map
            from app.models import SystemSetting
            import json

            # Create sample type setting
            setting = SystemSetting(
                category='sample_type',
                key='CHPP',
                value=json.dumps(['2H', '12H', 'Dcom']),
                is_active=True,
                sort_order=1
            )
            db.session.add(setting)
            db.session.commit()

            result = get_sample_type_choices_map()
            assert 'CHPP' in result
            assert '2H' in result['CHPP']


class TestGetUnitAbbreviations:
    """Tests for get_unit_abbreviations function."""

    def test_get_unit_abbreviations_fallback(self, app, db):
        """Test get_unit_abbreviations returns fallback."""
        with app.app_context():
            from app.utils.settings import get_unit_abbreviations
            result = get_unit_abbreviations()
            assert isinstance(result, dict)

    def test_get_unit_abbreviations_from_db(self, app, db):
        """Test get_unit_abbreviations from DB."""
        with app.app_context():
            from app.utils.settings import get_unit_abbreviations
            from app.models import SystemSetting

            # Create unit abbreviation setting
            setting = SystemSetting(
                category='unit_abbr',
                key='CHPP',
                value='ХБЗ',
                is_active=True,
                sort_order=1
            )
            db.session.add(setting)
            db.session.commit()

            result = get_unit_abbreviations()
            assert 'CHPP' in result


class TestSettingsModuleIntegrity:
    """Tests for settings module integrity."""

    def test_module_imports(self, app):
        """Test settings module can be imported."""
        with app.app_context():
            import app.utils.settings as settings
            assert hasattr(settings, 'get_error_reason_labels')
            assert hasattr(settings, 'get_setting_by_category')
            assert hasattr(settings, 'get_setting_value')
            assert hasattr(settings, 'update_setting')
            assert hasattr(settings, 'get_sample_type_choices_map')
            assert hasattr(settings, 'get_unit_abbreviations')

    def test_all_functions_callable(self, app):
        """Test all settings functions are callable."""
        with app.app_context():
            from app.utils.settings import (
                get_error_reason_labels,
                get_setting_by_category,
                get_setting_value,
                update_setting,
                get_sample_type_choices_map,
                get_unit_abbreviations
            )
            assert callable(get_error_reason_labels)
            assert callable(get_setting_by_category)
            assert callable(get_setting_value)
            assert callable(update_setting)
            assert callable(get_sample_type_choices_map)
            assert callable(get_unit_abbreviations)
