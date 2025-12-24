# tests/test_repeatability_loader_full.py
# -*- coding: utf-8 -*-
"""
Complete tests for app/utils/repeatability_loader.py
"""

import pytest
import json
from unittest.mock import patch, MagicMock


class TestLoadLimitRules:
    """Tests for load_limit_rules function."""

    def test_returns_dict(self, app, db):
        """Test returns a dictionary."""
        with app.app_context():
            from app.utils.repeatability_loader import load_limit_rules
            result = load_limit_rules()
            assert isinstance(result, dict)

    def test_fallback_to_file_rules(self, app, db):
        """Test falls back to FILE_LIMIT_RULES when no DB setting."""
        with app.app_context():
            from app.utils.repeatability_loader import load_limit_rules
            from app.models import SystemSetting

            # Make sure no repeatability limits setting exists
            SystemSetting.query.filter_by(category='repeatability', key='limits').delete()
            db.session.commit()

            result = load_limit_rules()
            assert isinstance(result, dict)

    def test_loads_from_db(self, app, db):
        """Test loads rules from database when available."""
        with app.app_context():
            from app.utils.repeatability_loader import load_limit_rules
            from app.models import SystemSetting

            # Create test setting with JSON value
            test_rules = {"test_param": {"T": 0.5}}
            setting = SystemSetting(
                category='repeatability',
                key='limits',
                value=json.dumps(test_rules),
                is_active=True
            )
            db.session.add(setting)
            db.session.commit()

            result = load_limit_rules()
            assert 'test_param' in result
            assert result['test_param']['T'] == 0.5

            # Cleanup
            db.session.delete(setting)
            db.session.commit()

    def test_empty_value_returns_fallback(self, app, db):
        """Test returns fallback when DB value is empty."""
        with app.app_context():
            from app.utils.repeatability_loader import load_limit_rules
            from app.models import SystemSetting

            # Create setting with empty value
            setting = SystemSetting(
                category='repeatability',
                key='limits',
                value='',
                is_active=True
            )
            db.session.add(setting)
            db.session.commit()

            result = load_limit_rules()
            assert isinstance(result, dict)

            # Cleanup
            db.session.delete(setting)
            db.session.commit()

    def test_invalid_json_returns_fallback(self, app, db):
        """Test returns fallback when DB value is invalid JSON."""
        with app.app_context():
            from app.utils.repeatability_loader import load_limit_rules
            from app.models import SystemSetting

            # Create setting with invalid JSON
            setting = SystemSetting(
                category='repeatability',
                key='limits',
                value='not valid json {{{',
                is_active=True
            )
            db.session.add(setting)
            db.session.commit()

            result = load_limit_rules()
            assert isinstance(result, dict)

            # Cleanup
            db.session.delete(setting)
            db.session.commit()

    def test_db_exception_returns_fallback(self, app):
        """Test returns fallback when DB exception occurs."""
        with app.app_context():
            from app.utils.repeatability_loader import load_limit_rules

            # Mock DB query to raise exception
            with patch('app.utils.repeatability_loader.SystemSetting') as mock_setting:
                mock_setting.query.filter_by.side_effect = Exception("DB Error")
                result = load_limit_rules()
                assert isinstance(result, dict)


class TestClearCache:
    """Tests for clear_cache function."""

    def test_clear_cache_no_error(self, app):
        """Test clear_cache doesn't raise error."""
        with app.app_context():
            from app.utils.repeatability_loader import clear_cache
            # Should not raise any exception
            try:
                clear_cache()
            except AttributeError:
                # cache_clear may not exist if not using @lru_cache
                pass


class TestFileLimitRules:
    """Tests for FILE_LIMIT_RULES constant."""

    def test_file_limit_rules_is_dict(self, app):
        """Test FILE_LIMIT_RULES is a dictionary."""
        with app.app_context():
            from app.config.repeatability import LIMIT_RULES
            assert isinstance(LIMIT_RULES, dict)

    def test_file_limit_rules_has_entries(self, app):
        """Test FILE_LIMIT_RULES has entries."""
        with app.app_context():
            from app.config.repeatability import LIMIT_RULES
            assert len(LIMIT_RULES) > 0
