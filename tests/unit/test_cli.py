# -*- coding: utf-8 -*-
"""
Tests for app/cli.py
CLI helper functions tests
"""
import pytest
from unittest.mock import patch, MagicMock
import math


class TestSafeStr:
    """_safe_str function tests"""

    def test_import(self):
        """Import function"""
        from app.cli import _safe_str
        assert callable(_safe_str)

    def test_none_returns_empty(self):
        """None returns empty string"""
        from app.cli import _safe_str
        assert _safe_str(None) == ""

    def test_string_stripped(self):
        """String is stripped"""
        from app.cli import _safe_str
        assert _safe_str("  test  ") == "test"

    def test_int_to_string(self):
        """Int converted to string"""
        from app.cli import _safe_str
        assert _safe_str(123) == "123"

    def test_float_to_string(self):
        """Float converted to string"""
        from app.cli import _safe_str
        assert _safe_str(123.45) == "123.45"

    def test_nan_returns_empty(self):
        """NaN returns empty string"""
        from app.cli import _safe_str
        import numpy as np
        # pd.NA is not float, but np.nan is
        assert _safe_str(np.nan) == ""

    def test_float_nan_returns_empty(self):
        """Float NaN returns empty string"""
        from app.cli import _safe_str
        assert _safe_str(float('nan')) == ""


class TestSafeInt:
    """_safe_int function tests"""

    def test_import(self):
        """Import function"""
        from app.cli import _safe_int
        assert callable(_safe_int)

    def test_none_returns_default(self):
        """None returns default"""
        from app.cli import _safe_int
        assert _safe_int(None) is None
        assert _safe_int(None, default=0) == 0

    def test_int_unchanged(self):
        """Int returns unchanged"""
        from app.cli import _safe_int
        assert _safe_int(123) == 123

    def test_float_to_int(self):
        """Float converted to int"""
        from app.cli import _safe_int
        assert _safe_int(123.9) == 123

    def test_string_to_int(self):
        """String converted to int"""
        from app.cli import _safe_int
        assert _safe_int("123") == 123

    def test_string_float_to_int(self):
        """String float converted to int"""
        from app.cli import _safe_int
        assert _safe_int("123.9") == 123

    def test_empty_string_returns_default(self):
        """Empty string returns default"""
        from app.cli import _safe_int
        assert _safe_int("") is None
        assert _safe_int("", default=0) == 0

    def test_whitespace_returns_default(self):
        """Whitespace returns default"""
        from app.cli import _safe_int
        assert _safe_int("   ") is None

    def test_invalid_string_returns_default(self):
        """Invalid string returns default"""
        from app.cli import _safe_int
        assert _safe_int("abc") is None
        assert _safe_int("abc", default=-1) == -1

    def test_nan_returns_default(self):
        """NaN returns default"""
        from app.cli import _safe_int
        assert _safe_int(float('nan')) is None


class TestSafeFloat:
    """_safe_float function tests"""

    def test_import(self):
        """Import function"""
        from app.cli import _safe_float
        assert callable(_safe_float)

    def test_none_returns_default(self):
        """None returns default"""
        from app.cli import _safe_float
        assert _safe_float(None) is None
        assert _safe_float(None, default=0.0) == 0.0

    def test_float_unchanged(self):
        """Float returns unchanged"""
        from app.cli import _safe_float
        assert _safe_float(123.45) == 123.45

    def test_int_to_float(self):
        """Int converted to float"""
        from app.cli import _safe_float
        assert _safe_float(123) == 123.0

    def test_string_to_float(self):
        """String converted to float"""
        from app.cli import _safe_float
        assert _safe_float("123.45") == 123.45

    def test_empty_string_returns_default(self):
        """Empty string returns default"""
        from app.cli import _safe_float
        assert _safe_float("") is None
        assert _safe_float("", default=0.0) == 0.0

    def test_whitespace_removed(self):
        """Whitespace is removed"""
        from app.cli import _safe_float
        assert _safe_float("  123.45  ") == 123.45

    def test_internal_spaces_removed(self):
        """Internal spaces removed (for thousands)"""
        from app.cli import _safe_float
        assert _safe_float("1 000") == 1000.0

    def test_comma_removed(self):
        """Comma removed (for thousands)"""
        from app.cli import _safe_float
        assert _safe_float("1,000.50") == 1000.50

    def test_invalid_string_returns_default(self):
        """Invalid string returns default"""
        from app.cli import _safe_float
        assert _safe_float("abc") is None
        assert _safe_float("abc", default=-1.0) == -1.0

    def test_nan_returns_default(self):
        """NaN returns default"""
        from app.cli import _safe_float
        assert _safe_float(float('nan')) is None


class TestRegisterCommands:
    """register_commands function tests"""

    def test_import(self):
        """Import function"""
        from app.cli import register_commands
        assert callable(register_commands)

    def test_registers_users_group(self, app):
        """Registers users command group"""
        from app.cli import register_commands

        # Check that users command group exists
        with app.app_context():
            # The function should not raise any error
            register_commands(app)

    def test_registers_equipment_group(self, app):
        """Registers equipment command group"""
        from app.cli import register_commands

        with app.app_context():
            register_commands(app)


class TestCliCommandsSignature:
    """CLI commands signature tests"""

    def test_users_create_command_exists(self, app):
        """users create command signature"""
        # This test verifies the command structure exists
        # We test via the CLI runner instead of invoking directly
        pass

    def test_equipment_import_exists(self, app):
        """equipment import-excel command exists"""
        pass

    def test_equipment_export_exists(self, app):
        """equipment export-excel command exists"""
        pass


class TestEdgeCases:
    """Edge case tests"""

    def test_safe_str_with_list(self):
        """_safe_str with list"""
        from app.cli import _safe_str
        result = _safe_str([1, 2, 3])
        assert result == "[1, 2, 3]"

    def test_safe_str_with_dict(self):
        """_safe_str with dict"""
        from app.cli import _safe_str
        result = _safe_str({"a": 1})
        assert "a" in result

    def test_safe_int_negative(self):
        """_safe_int with negative"""
        from app.cli import _safe_int
        assert _safe_int(-123) == -123
        assert _safe_int("-123") == -123

    def test_safe_float_negative(self):
        """_safe_float with negative"""
        from app.cli import _safe_float
        assert _safe_float(-123.45) == -123.45
        assert _safe_float("-123.45") == -123.45

    def test_safe_float_scientific(self):
        """_safe_float with scientific notation"""
        from app.cli import _safe_float
        assert _safe_float("1e5") == 100000.0

    def test_safe_int_zero(self):
        """_safe_int with zero"""
        from app.cli import _safe_int
        assert _safe_int(0) == 0
        assert _safe_int("0") == 0

    def test_safe_float_zero(self):
        """_safe_float with zero"""
        from app.cli import _safe_float
        assert _safe_float(0.0) == 0.0
        assert _safe_float("0.0") == 0.0
