# tests/test_security_settings_full.py
# -*- coding: utf-8 -*-
"""
Complete tests for app/utils/security.py and app/utils/settings.py
"""

import pytest
from unittest.mock import patch, MagicMock


# ============================================================================
# SECURITY.PY TESTS
# ============================================================================

class TestEscapeLikePattern:
    """Tests for escape_like_pattern function."""

    def test_escape_percent(self, app):
        """Test escaping percent sign."""
        with app.app_context():
            from app.utils.security import escape_like_pattern
            result = escape_like_pattern("test%value")
            assert result == "test\\%value"

    def test_escape_underscore(self, app):
        """Test escaping underscore."""
        with app.app_context():
            from app.utils.security import escape_like_pattern
            result = escape_like_pattern("user_input")
            assert result == "user\\_input"

    def test_escape_backslash(self, app):
        """Test escaping backslash."""
        with app.app_context():
            from app.utils.security import escape_like_pattern
            result = escape_like_pattern("path\\file")
            assert result == "path\\\\file"

    def test_escape_all(self, app):
        """Test escaping all special chars."""
        with app.app_context():
            from app.utils.security import escape_like_pattern
            result = escape_like_pattern("%_\\")
            assert result == "\\%\\_\\\\"

    def test_none_input(self, app):
        """Test with None input."""
        with app.app_context():
            from app.utils.security import escape_like_pattern
            result = escape_like_pattern(None)
            assert result is None

    def test_empty_string(self, app):
        """Test with empty string."""
        with app.app_context():
            from app.utils.security import escape_like_pattern
            result = escape_like_pattern("")
            assert result == ""

    def test_no_special_chars(self, app):
        """Test with no special chars."""
        with app.app_context():
            from app.utils.security import escape_like_pattern
            result = escape_like_pattern("normal text")
            assert result == "normal text"


class TestIsSafeUrl:
    """Tests for is_safe_url function."""

    def test_relative_url(self, app):
        """Test relative URL is safe."""
        with app.test_request_context('/'):
            from app.utils.security import is_safe_url
            result = is_safe_url("/dashboard")
            assert result is True

    def test_same_host(self, app):
        """Test same host URL is safe."""
        with app.test_request_context('/'):
            from app.utils.security import is_safe_url
            from flask import request
            result = is_safe_url(request.host_url + "profile")
            assert result is True

    def test_different_host(self, app):
        """Test different host URL is not safe."""
        with app.test_request_context('/'):
            from app.utils.security import is_safe_url
            result = is_safe_url("http://evil.com")
            assert result is False

    def test_empty_path(self, app):
        """Test empty path."""
        with app.test_request_context('/'):
            from app.utils.security import is_safe_url
            result = is_safe_url("")
            assert result is True

    def test_javascript_scheme(self, app):
        """Test javascript scheme is not safe."""
        with app.test_request_context('/'):
            from app.utils.security import is_safe_url
            result = is_safe_url("javascript:alert(1)")
            assert result is False


# ============================================================================
# SETTINGS.PY TESTS
# ============================================================================

class TestGetErrorReasonLabels:
    """Tests for get_error_reason_labels function."""

    def test_returns_dict(self, app, db):
        """Test returns a dictionary."""
        with app.app_context():
            from app.utils.settings import get_error_reason_labels
            result = get_error_reason_labels()
            assert isinstance(result, dict)

    def test_with_settings(self, app, db):
        """Test with actual settings in DB."""
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
            assert 'test_error' in result
            assert result['test_error'] == 'Test Error Label'

            # Cleanup
            db.session.delete(setting)
            db.session.commit()


class TestGetSettingByCategory:
    """Tests for get_setting_by_category function."""

    def test_returns_dict(self, app, db):
        """Test returns a dictionary."""
        with app.app_context():
            from app.utils.settings import get_setting_by_category
            result = get_setting_by_category('nonexistent_category')
            assert isinstance(result, dict)

    def test_with_settings(self, app, db):
        """Test with actual settings in DB."""
        with app.app_context():
            from app.utils.settings import get_setting_by_category
            from app.models import SystemSetting

            # Create test setting
            setting = SystemSetting(
                category='test_cat',
                key='test_key',
                value='test_value',
                is_active=True,
                sort_order=1
            )
            db.session.add(setting)
            db.session.commit()

            result = get_setting_by_category('test_cat')
            assert 'test_key' in result
            assert result['test_key'] == 'test_value'

            # Cleanup
            db.session.delete(setting)
            db.session.commit()


class TestGetSettingValue:
    """Tests for get_setting_value function."""

    def test_not_found_returns_default(self, app, db):
        """Test returns default when not found."""
        with app.app_context():
            from app.utils.settings import get_setting_value
            result = get_setting_value('nonexistent', 'key', default='default_val')
            assert result == 'default_val'

    def test_found_returns_value(self, app, db):
        """Test returns value when found."""
        with app.app_context():
            from app.utils.settings import get_setting_value
            from app.models import SystemSetting

            # Create test setting
            setting = SystemSetting(
                category='test_cat',
                key='test_key',
                value='actual_value',
                is_active=True
            )
            db.session.add(setting)
            db.session.commit()

            result = get_setting_value('test_cat', 'test_key')
            assert result == 'actual_value'

            # Cleanup
            db.session.delete(setting)
            db.session.commit()


class TestUpdateSetting:
    """Tests for update_setting function."""

    def test_create_new(self, app, db):
        """Test creating new setting."""
        with app.app_context():
            from app.utils.settings import update_setting
            from app.models import SystemSetting

            result = update_setting('new_cat', 'new_key', 'new_value')
            assert result is not None
            assert result.category == 'new_cat'
            assert result.key == 'new_key'
            assert result.value == 'new_value'

            # Cleanup
            db.session.delete(result)
            db.session.commit()

    def test_update_existing(self, app, db):
        """Test updating existing setting."""
        with app.app_context():
            from app.utils.settings import update_setting
            from app.models import SystemSetting

            # Create initial setting
            setting = SystemSetting(
                category='upd_cat',
                key='upd_key',
                value='old_value'
            )
            db.session.add(setting)
            db.session.commit()

            # Update it
            result = update_setting('upd_cat', 'upd_key', 'new_value', updated_by_id=1)
            assert result.value == 'new_value'

            # Cleanup
            db.session.delete(result)
            db.session.commit()


class TestGetSampleTypeChoicesMap:
    """Tests for get_sample_type_choices_map function."""

    def test_returns_dict(self, app, db):
        """Test returns a dictionary."""
        with app.app_context():
            from app.utils.settings import get_sample_type_choices_map
            result = get_sample_type_choices_map()
            assert isinstance(result, dict)

    def test_fallback_to_constants(self, app, db):
        """Test falls back to constants when no DB settings."""
        with app.app_context():
            from app.utils.settings import get_sample_type_choices_map
            from app.models import SystemSetting

            # Make sure no sample_type settings exist
            SystemSetting.query.filter_by(category='sample_type').delete()
            db.session.commit()

            result = get_sample_type_choices_map()
            assert isinstance(result, dict)


class TestGetUnitAbbreviations:
    """Tests for get_unit_abbreviations function."""

    def test_returns_dict(self, app, db):
        """Test returns a dictionary."""
        with app.app_context():
            from app.utils.settings import get_unit_abbreviations
            result = get_unit_abbreviations()
            assert isinstance(result, dict)

    def test_fallback_to_constants(self, app, db):
        """Test falls back to constants when no DB settings."""
        with app.app_context():
            from app.utils.settings import get_unit_abbreviations
            from app.models import SystemSetting

            # Make sure no unit_abbr settings exist
            SystemSetting.query.filter_by(category='unit_abbr').delete()
            db.session.commit()

            result = get_unit_abbreviations()
            assert isinstance(result, dict)
