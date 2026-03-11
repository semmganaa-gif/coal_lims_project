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
            from app.utils.repeatability_loader import load_limit_rules, clear_cache
            clear_cache()
            result = load_limit_rules()
            assert isinstance(result, dict)
            clear_cache()

    def test_returns_file_fallback_when_no_db(self, app):
        """Should return file fallback when DB is empty"""
        with app.app_context():
            from app.utils.repeatability_loader import load_limit_rules, clear_cache
            from app import db
            clear_cache()

            mock_scalars = Mock()
            mock_scalars.first.return_value = None
            mock_execute_result = Mock()
            mock_execute_result.scalars.return_value = mock_scalars

            with patch.object(db.session, 'execute', return_value=mock_execute_result):
                result = load_limit_rules()
                assert isinstance(result, dict)
            clear_cache()

    def test_returns_db_value_when_exists(self, app):
        """Should return DB value when exists"""
        with app.app_context():
            from app.utils.repeatability_loader import load_limit_rules, clear_cache
            from app import db
            clear_cache()

            mock_setting = Mock()
            mock_setting.value = '{"MT": {"limit": 0.3}}'
            mock_scalars = Mock()
            mock_scalars.first.return_value = mock_setting
            mock_execute_result = Mock()
            mock_execute_result.scalars.return_value = mock_scalars

            with patch.object(db.session, 'execute', return_value=mock_execute_result):
                result = load_limit_rules()
                assert "MT" in result
            clear_cache()


class TestClearCache:
    """clear_cache() функцийн тестүүд"""

    def test_clear_cache_exists(self):
        """clear_cache function should exist"""
        from app.utils.repeatability_loader import clear_cache
        assert callable(clear_cache)
