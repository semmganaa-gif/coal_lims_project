# tests/unit/test_repeatability_loader.py
# -*- coding: utf-8 -*-
"""
Repeatability loader tests
"""
import pytest
from unittest.mock import patch, Mock


class TestLoadLimitRules:
    """load_limit_rules() функцийн тестүүд"""

    def test_returns_dict(self, app):
        """Should return a dictionary"""
        with app.app_context():
            from app.utils.repeatability_loader import load_limit_rules
            result = load_limit_rules()
            assert isinstance(result, dict)

    def test_returns_file_fallback_when_no_db(self, app):
        """Should return file fallback when DB is empty"""
        with app.app_context():
            with patch('app.utils.repeatability_loader.SystemSetting') as mock:
                mock.query.filter_by.return_value.first.return_value = None
                from app.utils.repeatability_loader import load_limit_rules
                result = load_limit_rules()
                assert isinstance(result, dict)

    def test_returns_db_value_when_exists(self, app):
        """Should return DB value when exists"""
        with app.app_context():
            with patch('app.utils.repeatability_loader.SystemSetting') as mock:
                mock_setting = Mock()
                mock_setting.value = '{"MT": {"limit": 0.3}}'
                mock.query.filter_by.return_value.first.return_value = mock_setting
                from app.utils.repeatability_loader import load_limit_rules
                result = load_limit_rules()
                assert "MT" in result


class TestClearCache:
    """clear_cache() функцийн тестүүд"""

    def test_clear_cache_exists(self):
        """clear_cache function should exist"""
        from app.utils.repeatability_loader import clear_cache
        assert callable(clear_cache)
