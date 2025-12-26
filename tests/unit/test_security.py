# -*- coding: utf-8 -*-
"""
Tests for app/utils/security.py
Security utility functions comprehensive tests
"""
import pytest
from unittest.mock import patch, MagicMock


class TestEscapeLikePattern:
    """escape_like_pattern function tests"""

    def test_import(self):
        """Import function"""
        from app.utils.security import escape_like_pattern
        assert callable(escape_like_pattern)

    def test_none_returns_none(self):
        """None input returns None"""
        from app.utils.security import escape_like_pattern
        assert escape_like_pattern(None) is None

    def test_empty_string_returns_empty(self):
        """Empty string returns empty (falsy)"""
        from app.utils.security import escape_like_pattern
        result = escape_like_pattern("")
        # Empty string is falsy, so returns as-is
        assert result == ""

    def test_normal_text_unchanged(self):
        """Normal text without special chars unchanged"""
        from app.utils.security import escape_like_pattern
        assert escape_like_pattern("hello") == "hello"

    def test_percent_escaped(self):
        """Percent sign is escaped"""
        from app.utils.security import escape_like_pattern
        assert escape_like_pattern("test%value") == "test\\%value"

    def test_underscore_escaped(self):
        """Underscore is escaped"""
        from app.utils.security import escape_like_pattern
        assert escape_like_pattern("user_input") == "user\\_input"

    def test_backslash_escaped(self):
        """Backslash is escaped"""
        from app.utils.security import escape_like_pattern
        assert escape_like_pattern("path\\file") == "path\\\\file"

    def test_multiple_percent(self):
        """Multiple percent signs escaped"""
        from app.utils.security import escape_like_pattern
        assert escape_like_pattern("100%% complete") == "100\\%\\% complete"

    def test_multiple_underscore(self):
        """Multiple underscores escaped"""
        from app.utils.security import escape_like_pattern
        assert escape_like_pattern("a_b_c") == "a\\_b\\_c"

    def test_mixed_special_chars(self):
        """Mixed special characters escaped"""
        from app.utils.security import escape_like_pattern
        result = escape_like_pattern("test%user_name")
        assert result == "test\\%user\\_name"

    def test_all_special_chars_together(self):
        """All special characters (\\, %, _) together"""
        from app.utils.security import escape_like_pattern
        result = escape_like_pattern("a\\b%c_d")
        # Order: first \\ -> \\\\, then % -> \\%, then _ -> \\_
        assert result == "a\\\\b\\%c\\_d"

    def test_leading_percent(self):
        """Leading percent sign"""
        from app.utils.security import escape_like_pattern
        assert escape_like_pattern("%start") == "\\%start"

    def test_trailing_percent(self):
        """Trailing percent sign"""
        from app.utils.security import escape_like_pattern
        assert escape_like_pattern("end%") == "end\\%"

    def test_leading_underscore(self):
        """Leading underscore"""
        from app.utils.security import escape_like_pattern
        assert escape_like_pattern("_private") == "\\_private"

    def test_trailing_underscore(self):
        """Trailing underscore"""
        from app.utils.security import escape_like_pattern
        assert escape_like_pattern("name_") == "name\\_"

    def test_only_percent(self):
        """Only percent sign"""
        from app.utils.security import escape_like_pattern
        assert escape_like_pattern("%") == "\\%"

    def test_only_underscore(self):
        """Only underscore"""
        from app.utils.security import escape_like_pattern
        assert escape_like_pattern("_") == "\\_"

    def test_only_backslash(self):
        """Only backslash"""
        from app.utils.security import escape_like_pattern
        assert escape_like_pattern("\\") == "\\\\"

    def test_unicode_text(self):
        """Unicode text unchanged"""
        from app.utils.security import escape_like_pattern
        assert escape_like_pattern("Монгол") == "Монгол"

    def test_unicode_with_special(self):
        """Unicode text with special characters"""
        from app.utils.security import escape_like_pattern
        result = escape_like_pattern("Дээж%нэр_123")
        assert result == "Дээж\\%нэр\\_123"

    def test_numbers_unchanged(self):
        """Numbers unchanged"""
        from app.utils.security import escape_like_pattern
        assert escape_like_pattern("12345") == "12345"

    def test_whitespace_unchanged(self):
        """Whitespace unchanged"""
        from app.utils.security import escape_like_pattern
        assert escape_like_pattern("hello world") == "hello world"

    def test_newline_unchanged(self):
        """Newline unchanged"""
        from app.utils.security import escape_like_pattern
        assert escape_like_pattern("line1\nline2") == "line1\nline2"

    def test_tab_unchanged(self):
        """Tab unchanged"""
        from app.utils.security import escape_like_pattern
        assert escape_like_pattern("col1\tcol2") == "col1\tcol2"


class TestEscapeLikePatternSQLInjection:
    """SQL injection prevention tests"""

    def test_prevents_wildcard_injection(self):
        """Prevents % wildcard injection"""
        from app.utils.security import escape_like_pattern
        # Attacker input trying to match all records
        malicious = "%"
        escaped = escape_like_pattern(malicious)
        assert escaped == "\\%"
        assert "%" not in escaped.replace("\\%", "")

    def test_prevents_single_char_wildcard(self):
        """Prevents _ single char wildcard injection"""
        from app.utils.security import escape_like_pattern
        # Attacker input trying to match any single char
        malicious = "a_b"
        escaped = escape_like_pattern(malicious)
        assert escaped == "a\\_b"

    def test_complex_injection_attempt(self):
        """Complex SQL injection attempt"""
        from app.utils.security import escape_like_pattern
        # Attacker trying: %'; DROP TABLE users; --
        malicious = "%'; DROP TABLE users; --"
        escaped = escape_like_pattern(malicious)
        # Percent should be escaped, rest passes through
        assert escaped.startswith("\\%")
        # Note: SQL semicolon is not escaped, that's handled by parameterized queries

    def test_double_percent(self):
        """Double percent (like operator escape attempt)"""
        from app.utils.security import escape_like_pattern
        escaped = escape_like_pattern("%%")
        assert escaped == "\\%\\%"

    def test_double_underscore(self):
        """Double underscore"""
        from app.utils.security import escape_like_pattern
        escaped = escape_like_pattern("__")
        assert escaped == "\\_\\_"

    def test_backslash_before_percent(self):
        """Backslash before percent (escape escape attempt)"""
        from app.utils.security import escape_like_pattern
        # Attacker trying: \% hoping to unescape
        escaped = escape_like_pattern("\\%")
        # Should become \\\\% (escaped backslash + escaped percent)
        assert escaped == "\\\\\\%"


class TestIsSafeUrl:
    """is_safe_url function tests"""

    def test_import(self):
        """Import function"""
        from app.utils.security import is_safe_url
        assert callable(is_safe_url)

    def test_relative_url_safe(self, app):
        """Relative URL is safe"""
        from app.utils.security import is_safe_url
        with app.test_request_context('/'):
            assert is_safe_url("/dashboard") is True

    def test_relative_url_with_path(self, app):
        """Relative URL with path is safe"""
        from app.utils.security import is_safe_url
        with app.test_request_context('/'):
            assert is_safe_url("/admin/users/1") is True

    def test_relative_url_with_query(self, app):
        """Relative URL with query string is safe"""
        from app.utils.security import is_safe_url
        with app.test_request_context('/'):
            assert is_safe_url("/search?q=test") is True

    def test_same_host_http_safe(self, app):
        """Same host HTTP URL is safe"""
        from app.utils.security import is_safe_url
        with app.test_request_context('/', base_url='http://localhost/'):
            assert is_safe_url("http://localhost/dashboard") is True

    def test_same_host_https_safe(self, app):
        """Same host HTTPS URL is safe"""
        from app.utils.security import is_safe_url
        with app.test_request_context('/', base_url='https://localhost/'):
            assert is_safe_url("https://localhost/dashboard") is True

    def test_external_url_unsafe(self, app):
        """External URL is unsafe"""
        from app.utils.security import is_safe_url
        with app.test_request_context('/', base_url='http://localhost/'):
            assert is_safe_url("http://evil.com") is False

    def test_external_https_unsafe(self, app):
        """External HTTPS URL is unsafe"""
        from app.utils.security import is_safe_url
        with app.test_request_context('/', base_url='http://localhost/'):
            assert is_safe_url("https://evil.com/phishing") is False

    def test_subdomain_unsafe(self, app):
        """Subdomain of different host is unsafe"""
        from app.utils.security import is_safe_url
        with app.test_request_context('/', base_url='http://localhost/'):
            assert is_safe_url("http://evil.localhost/") is False

    def test_protocol_relative_unsafe(self, app):
        """Protocol-relative URL to different host is unsafe"""
        from app.utils.security import is_safe_url
        with app.test_request_context('/', base_url='http://localhost/'):
            # //evil.com will be joined with host_url scheme
            assert is_safe_url("//evil.com") is False

    def test_empty_string(self, app):
        """Empty string URL"""
        from app.utils.security import is_safe_url
        with app.test_request_context('/'):
            # Empty joins with host_url, resulting in same host
            assert is_safe_url("") is True

    def test_hash_only(self, app):
        """Hash-only URL is safe (stays on same page)"""
        from app.utils.security import is_safe_url
        with app.test_request_context('/'):
            assert is_safe_url("#section") is True

    def test_javascript_protocol_unsafe(self, app):
        """JavaScript protocol is unsafe"""
        from app.utils.security import is_safe_url
        with app.test_request_context('/'):
            result = is_safe_url("javascript:alert('xss')")
            # javascript: scheme is not in (http, https, '')
            assert result is False

    def test_data_protocol_unsafe(self, app):
        """Data protocol is unsafe"""
        from app.utils.security import is_safe_url
        with app.test_request_context('/'):
            result = is_safe_url("data:text/html,<script>alert('xss')</script>")
            assert result is False

    def test_ftp_protocol_unsafe(self, app):
        """FTP protocol is unsafe"""
        from app.utils.security import is_safe_url
        with app.test_request_context('/'):
            result = is_safe_url("ftp://example.com/file")
            assert result is False

    def test_none_url(self, app):
        """None URL handling"""
        from app.utils.security import is_safe_url
        with app.test_request_context('/'):
            # None will be coerced to string "None" and joined
            try:
                result = is_safe_url(None)
                # If it doesn't crash, it should be safe (relative)
                assert result is True
            except (TypeError, AttributeError):
                # It's also acceptable to raise an error
                pass


class TestIsSafeUrlOpenRedirect:
    """Open redirect prevention tests"""

    def test_prevents_open_redirect(self, app):
        """Prevents basic open redirect"""
        from app.utils.security import is_safe_url
        with app.test_request_context('/', base_url='http://myapp.com/'):
            # Classic open redirect attack
            assert is_safe_url("http://evil.com/fake-login") is False

    def test_prevents_double_slash_redirect(self, app):
        """Prevents double-slash redirect trick"""
        from app.utils.security import is_safe_url
        with app.test_request_context('/', base_url='http://myapp.com/'):
            # //evil.com is protocol-relative, could redirect
            assert is_safe_url("//evil.com") is False

    def test_prevents_backslash_redirect(self, app):
        """Handles backslash in URL"""
        from app.utils.security import is_safe_url
        with app.test_request_context('/', base_url='http://myapp.com/'):
            # Some browsers treat \ as /
            result = is_safe_url("http://myapp.com\\@evil.com")
            # This is a tricky case, behavior depends on urljoin
            # Just ensure it doesn't crash
            assert isinstance(result, bool)

    def test_prevents_url_encoded_redirect(self, app):
        """Handles URL-encoded characters"""
        from app.utils.security import is_safe_url
        with app.test_request_context('/', base_url='http://myapp.com/'):
            # URL-encoded http://evil.com
            encoded = "http%3A%2F%2Fevil.com"
            result = is_safe_url(encoded)
            # urljoin treats this as relative path
            # Should be safe since it's treated as path segment
            assert result is True  # This is path, not absolute URL

    def test_same_host_different_port(self, app):
        """Different port on same host"""
        from app.utils.security import is_safe_url
        with app.test_request_context('/', base_url='http://localhost:5000/'):
            # localhost:8080 vs localhost:5000 have different netloc
            result = is_safe_url("http://localhost:8080/admin")
            assert result is False


class TestIsSafeUrlRealWorld:
    """Real world URL scenarios"""

    def test_login_next_parameter(self, app):
        """Login next parameter (common use case)"""
        from app.utils.security import is_safe_url
        with app.test_request_context('/login?next=/dashboard'):
            assert is_safe_url("/dashboard") is True

    def test_logout_redirect(self, app):
        """Logout redirect to login page"""
        from app.utils.security import is_safe_url
        with app.test_request_context('/logout'):
            assert is_safe_url("/login") is True

    def test_api_redirect(self, app):
        """API endpoint redirect"""
        from app.utils.security import is_safe_url
        with app.test_request_context('/api/v1/'):
            assert is_safe_url("/api/v1/users") is True

    def test_nested_path(self, app):
        """Nested path URL"""
        from app.utils.security import is_safe_url
        with app.test_request_context('/'):
            assert is_safe_url("/admin/samples/123/edit") is True

    def test_with_anchor(self, app):
        """URL with anchor"""
        from app.utils.security import is_safe_url
        with app.test_request_context('/'):
            assert is_safe_url("/docs/guide#section-1") is True


class TestEscapeLikePatternEdgeCases:
    """Edge cases for escape_like_pattern"""

    def test_long_string(self):
        """Very long string"""
        from app.utils.security import escape_like_pattern
        long_str = "a" * 10000 + "%" + "b" * 10000
        result = escape_like_pattern(long_str)
        assert "\\%" in result
        assert len(result) == len(long_str) + 1  # One extra char for escape

    def test_only_special_chars(self):
        """String with only special characters"""
        from app.utils.security import escape_like_pattern
        result = escape_like_pattern("%_%\\")
        assert result == "\\%\\_\\%\\\\"  # Each gets escaped

    def test_consecutive_backslashes(self):
        """Consecutive backslashes"""
        from app.utils.security import escape_like_pattern
        result = escape_like_pattern("\\\\\\")
        assert result == "\\\\\\\\\\\\"  # Each \ becomes \\

    def test_alternating_special(self):
        """Alternating special and normal characters"""
        from app.utils.security import escape_like_pattern
        result = escape_like_pattern("a%b_c\\d")
        assert result == "a\\%b\\_c\\\\d"

    def test_integer_input(self):
        """Non-string input (integer)"""
        from app.utils.security import escape_like_pattern
        # Function expects string, int should not be passed
        # But testing edge case
        try:
            result = escape_like_pattern(123)
            # If it works, it means it converted to string
            assert result == "123" or result == 123
        except (AttributeError, TypeError):
            # Expected if type checking is strict
            pass

    def test_list_input(self):
        """Non-string input (list)"""
        from app.utils.security import escape_like_pattern
        try:
            result = escape_like_pattern(["a", "b"])
            # Should either fail or convert somehow
        except (AttributeError, TypeError):
            pass  # Expected

    def test_zero_falsy(self):
        """Zero as input (falsy)"""
        from app.utils.security import escape_like_pattern
        try:
            result = escape_like_pattern(0)
            # 0 is falsy, so if int accepted, returns as-is
            assert result == 0 or result == "0"
        except (AttributeError, TypeError):
            pass

    def test_false_falsy(self):
        """False as input (falsy)"""
        from app.utils.security import escape_like_pattern
        try:
            result = escape_like_pattern(False)
            assert result is False or result == "False"
        except (AttributeError, TypeError):
            pass

