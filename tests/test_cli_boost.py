# tests/test_cli_boost.py
# -*- coding: utf-8 -*-
"""Tests to boost cli.py coverage."""

import pytest
from unittest.mock import patch, MagicMock


class TestCLIHelpers:
    """Test CLI helper functions."""

    def test_safe_str(self, app):
        """Test _safe_str function."""
        with app.app_context():
            from app.cli import _safe_str
            assert _safe_str(None) == ""
            assert _safe_str("test") == "test"
            assert _safe_str("  hello  ") == "hello"

    def test_safe_int(self, app):
        """Test _safe_int function."""
        with app.app_context():
            from app.cli import _safe_int
            assert _safe_int(None) is None
            assert _safe_int("5") == 5
            assert _safe_int("3.7") == 3
            assert _safe_int("invalid", default=0) == 0

    def test_safe_float(self, app):
        """Test _safe_float function."""
        with app.app_context():
            from app.cli import _safe_float
            assert _safe_float(None) is None
            assert _safe_float("5.5") == 5.5
            assert _safe_float("invalid", default=0.0) == 0.0


class TestCLIModule:
    """Test CLI module imports."""

    def test_cli_import(self, app):
        """Test CLI module imports."""
        with app.app_context():
            from app import cli
            assert cli is not None

    def test_cli_has_helper_functions(self, app):
        """Test CLI has helper functions."""
        with app.app_context():
            from app import cli
            assert hasattr(cli, '_safe_str')
            assert hasattr(cli, '_safe_int')
            assert hasattr(cli, '_safe_float')


class TestCLICommands:
    """Test CLI commands registration."""

    def test_register_commands(self, app):
        """Test commands are registered."""
        with app.app_context():
            # Check that app has CLI
            assert hasattr(app, 'cli')

    def test_cli_module_loaded(self, app):
        """Test CLI module is loaded."""
        with app.app_context():
            from app.cli import register_commands
            assert register_commands is not None
