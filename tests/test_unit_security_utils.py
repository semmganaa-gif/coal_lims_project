# -*- coding: utf-8 -*-
"""
Security utils тестүүд
"""
import pytest


class TestEscapeLikePattern:
    """escape_like_pattern тестүүд"""

    def test_import_function(self):
        """Function import"""
        from app.utils.security import escape_like_pattern
        assert escape_like_pattern is not None

    def test_none_input(self):
        """None input returns None"""
        from app.utils.security import escape_like_pattern
        assert escape_like_pattern(None) is None

    def test_empty_string(self):
        """Empty string returns empty string"""
        from app.utils.security import escape_like_pattern
        assert escape_like_pattern("") == ""

    def test_normal_string(self):
        """Normal string without special chars"""
        from app.utils.security import escape_like_pattern
        assert escape_like_pattern("hello") == "hello"

    def test_percent_escape(self):
        """Percent sign is escaped"""
        from app.utils.security import escape_like_pattern
        result = escape_like_pattern("test%value")
        assert "\\%" in result

    def test_underscore_escape(self):
        """Underscore is escaped"""
        from app.utils.security import escape_like_pattern
        result = escape_like_pattern("user_name")
        assert "\\_" in result

    def test_backslash_escape(self):
        """Backslash is escaped"""
        from app.utils.security import escape_like_pattern
        result = escape_like_pattern("path\\file")
        assert "\\\\" in result

    def test_multiple_special_chars(self):
        """Multiple special chars are all escaped"""
        from app.utils.security import escape_like_pattern
        result = escape_like_pattern("test%user_name\\path")
        assert "\\%" in result
        assert "\\_" in result
        assert "\\\\" in result

    def test_sql_injection_attempt(self):
        """SQL injection attempt is escaped"""
        from app.utils.security import escape_like_pattern
        result = escape_like_pattern("'; DROP TABLE --")
        # Should not contain unescaped special chars
        assert "%" not in result or "\\%" in result


class TestIsSafeUrl:
    """is_safe_url тестүүд"""

    def test_import_function(self):
        """Function import"""
        from app.utils.security import is_safe_url
        assert is_safe_url is not None

    def test_relative_url_safe(self):
        """Relative URL is safe"""
        from app import create_app
        from app.utils.security import is_safe_url

        app = create_app()
        with app.test_request_context():
            assert is_safe_url("/dashboard") is True

    def test_relative_url_with_params(self):
        """Relative URL with query params is safe"""
        from app import create_app
        from app.utils.security import is_safe_url

        app = create_app()
        with app.test_request_context():
            assert is_safe_url("/search?q=test") is True

    def test_absolute_same_domain(self):
        """Absolute URL to same domain is safe"""
        from app import create_app
        from app.utils.security import is_safe_url

        app = create_app()
        with app.test_request_context(base_url='http://localhost'):
            assert is_safe_url("http://localhost/page") is True

    def test_external_url_unsafe(self):
        """External URL is unsafe"""
        from app import create_app
        from app.utils.security import is_safe_url

        app = create_app()
        with app.test_request_context(base_url='http://mysite.com'):
            assert is_safe_url("http://evil.com") is False

    def test_javascript_url_unsafe(self):
        """JavaScript URL is unsafe"""
        from app import create_app
        from app.utils.security import is_safe_url

        app = create_app()
        with app.test_request_context():
            result = is_safe_url("javascript:alert(1)")
            # Should be False as it's not http/https
            assert result is False

    def test_empty_url(self):
        """Empty URL handling"""
        from app import create_app
        from app.utils.security import is_safe_url

        app = create_app()
        with app.test_request_context():
            result = is_safe_url("")
            assert isinstance(result, bool)
