# tests/test_security_deep.py
# -*- coding: utf-8 -*-
"""
Deep coverage tests for app/utils/security.py
"""

import pytest
from unittest.mock import patch, MagicMock


class TestEscapeLikePattern:
    """Tests for escape_like_pattern function."""

    def test_escape_none(self, app):
        """Test escape_like_pattern with None."""
        with app.app_context():
            from app.utils.security import escape_like_pattern
            result = escape_like_pattern(None)
            assert result is None

    def test_escape_empty_string(self, app):
        """Test escape_like_pattern with empty string."""
        with app.app_context():
            from app.utils.security import escape_like_pattern
            result = escape_like_pattern('')
            assert result == ''

    def test_escape_normal_string(self, app):
        """Test escape_like_pattern with normal string."""
        with app.app_context():
            from app.utils.security import escape_like_pattern
            result = escape_like_pattern('hello world')
            assert result == 'hello world'

    def test_escape_percent(self, app):
        """Test escape_like_pattern escapes percent."""
        with app.app_context():
            from app.utils.security import escape_like_pattern
            result = escape_like_pattern('test%value')
            assert result == 'test\\%value'

    def test_escape_underscore(self, app):
        """Test escape_like_pattern escapes underscore."""
        with app.app_context():
            from app.utils.security import escape_like_pattern
            result = escape_like_pattern('user_input')
            assert result == 'user\\_input'

    def test_escape_backslash(self, app):
        """Test escape_like_pattern escapes backslash."""
        with app.app_context():
            from app.utils.security import escape_like_pattern
            result = escape_like_pattern('path\\file')
            assert result == 'path\\\\file'

    def test_escape_multiple_special_chars(self, app):
        """Test escape_like_pattern with multiple special chars."""
        with app.app_context():
            from app.utils.security import escape_like_pattern
            result = escape_like_pattern('100%_complete')
            assert result == '100\\%\\_complete'

    def test_escape_only_special_chars(self, app):
        """Test escape_like_pattern with only special chars."""
        with app.app_context():
            from app.utils.security import escape_like_pattern
            result = escape_like_pattern('%_%')
            assert result == '\\%\\_\\%'

    def test_escape_mixed_content(self, app):
        """Test escape_like_pattern with mixed content."""
        with app.app_context():
            from app.utils.security import escape_like_pattern
            result = escape_like_pattern('file_name%25.txt')
            assert '\\%' in result
            assert '\\_' in result

    def test_escape_unicode_string(self, app):
        """Test escape_like_pattern with unicode."""
        with app.app_context():
            from app.utils.security import escape_like_pattern
            result = escape_like_pattern('тест%юникод')
            assert result == 'тест\\%юникод'

    def test_escape_sql_injection_attempt(self, app):
        """Test escape_like_pattern handles SQL injection patterns."""
        with app.app_context():
            from app.utils.security import escape_like_pattern
            # Common SQL injection patterns with LIKE wildcards
            result = escape_like_pattern("'; DROP TABLE users;--")
            # Should not modify non-LIKE special chars
            assert "'" in result
            assert "DROP" in result

    def test_escape_preserves_other_special_chars(self, app):
        """Test escape_like_pattern preserves non-LIKE special chars."""
        with app.app_context():
            from app.utils.security import escape_like_pattern
            result = escape_like_pattern("test@email.com")
            assert result == "test@email.com"

    def test_escape_numbers_and_symbols(self, app):
        """Test escape_like_pattern with numbers and symbols."""
        with app.app_context():
            from app.utils.security import escape_like_pattern
            result = escape_like_pattern("item#123_test%50")
            assert '\\%' in result
            assert '\\_' in result
            assert '#123' in result


class TestIsSafeUrl:
    """Tests for is_safe_url function."""

    def test_safe_url_relative_path(self, client, app):
        """Test is_safe_url with relative path."""
        with client:
            with app.app_context():
                from app.utils.security import is_safe_url
                # Need request context
                with app.test_request_context('/'):
                    result = is_safe_url('/dashboard')
                    assert result is True

    def test_safe_url_home(self, client, app):
        """Test is_safe_url with home path."""
        with client:
            with app.app_context():
                from app.utils.security import is_safe_url
                with app.test_request_context('/'):
                    result = is_safe_url('/')
                    assert result is True

    def test_safe_url_absolute_same_host(self, client, app):
        """Test is_safe_url with absolute URL same host."""
        with client:
            with app.app_context():
                from app.utils.security import is_safe_url
                with app.test_request_context('/', base_url='http://localhost/'):
                    result = is_safe_url('http://localhost/profile')
                    assert result is True

    def test_unsafe_url_different_host(self, client, app):
        """Test is_safe_url with different host."""
        with client:
            with app.app_context():
                from app.utils.security import is_safe_url
                with app.test_request_context('/', base_url='http://localhost/'):
                    result = is_safe_url('http://evil.com')
                    assert result is False

    def test_unsafe_url_https_different_host(self, client, app):
        """Test is_safe_url with https different host."""
        with client:
            with app.app_context():
                from app.utils.security import is_safe_url
                with app.test_request_context('/', base_url='http://localhost/'):
                    result = is_safe_url('https://attacker.com/steal')
                    assert result is False

    def test_safe_url_with_query_params(self, client, app):
        """Test is_safe_url with query parameters."""
        with client:
            with app.app_context():
                from app.utils.security import is_safe_url
                with app.test_request_context('/'):
                    result = is_safe_url('/search?q=test')
                    assert result is True

    def test_safe_url_with_fragment(self, client, app):
        """Test is_safe_url with fragment."""
        with client:
            with app.app_context():
                from app.utils.security import is_safe_url
                with app.test_request_context('/'):
                    result = is_safe_url('/page#section')
                    assert result is True

    def test_safe_url_nested_path(self, client, app):
        """Test is_safe_url with nested path."""
        with client:
            with app.app_context():
                from app.utils.security import is_safe_url
                with app.test_request_context('/'):
                    result = is_safe_url('/admin/settings/users')
                    assert result is True

    def test_unsafe_url_protocol_relative(self, client, app):
        """Test is_safe_url with protocol-relative URL."""
        with client:
            with app.app_context():
                from app.utils.security import is_safe_url
                with app.test_request_context('/', base_url='http://localhost/'):
                    result = is_safe_url('//evil.com/path')
                    assert result is False

    def test_safe_url_empty_path(self, client, app):
        """Test is_safe_url with empty path."""
        with client:
            with app.app_context():
                from app.utils.security import is_safe_url
                with app.test_request_context('/'):
                    result = is_safe_url('')
                    assert result is True


class TestSecurityModuleIntegrity:
    """Tests for security module integrity."""

    def test_module_imports(self, app):
        """Test security module can be imported."""
        with app.app_context():
            import app.utils.security as security
            assert hasattr(security, 'escape_like_pattern')
            assert hasattr(security, 'is_safe_url')

    def test_functions_are_callable(self, app):
        """Test security functions are callable."""
        with app.app_context():
            from app.utils.security import escape_like_pattern, is_safe_url
            assert callable(escape_like_pattern)
            assert callable(is_safe_url)
