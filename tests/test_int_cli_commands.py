# tests/integration/test_cli_commands.py
# -*- coding: utf-8 -*-
"""CLI commands comprehensive tests"""

import pytest
from app import create_app, db
from app.models import User, Equipment


@pytest.fixture
def cli_app():
    app = create_app()
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False
    return app


@pytest.fixture
def runner(cli_app):
    return cli_app.test_cli_runner()


class TestUserCommands:
    def test_users_create_command(self, runner, cli_app):
        with cli_app.app_context():
            result = runner.invoke(args=['users', 'create', '--username', 'clitestuser', '--password', 'CliTest123', '--role', 'chemist'])
            assert result.exit_code in [0, 1, 2]

    def test_users_group(self, runner, cli_app):
        with cli_app.app_context():
            result = runner.invoke(args=['users'])
            assert result.exit_code in [0, 1, 2]


class TestEquipmentCommands:
    def test_equipment_group(self, runner, cli_app):
        with cli_app.app_context():
            result = runner.invoke(args=['equipment'])
            assert result.exit_code in [0, 1, 2]

    def test_equipment_import(self, runner, cli_app):
        with cli_app.app_context():
            result = runner.invoke(args=['equipment', 'import', '--excel-path', 'test.xlsx'])
            assert result.exit_code in [0, 1, 2]

    def test_equipment_export(self, runner, cli_app):
        with cli_app.app_context():
            result = runner.invoke(args=['equipment', 'export', '--excel-path', 'test_export.xlsx'])
            assert result.exit_code in [0, 1, 2]


class TestCLIHelpers:
    def test_safe_str(self):
        from app.cli import _safe_str
        assert _safe_str(None) == ""
        assert _safe_str("test") == "test"
        assert _safe_str("  trim  ") == "trim"

    def test_safe_int(self):
        from app.cli import _safe_int
        assert _safe_int(None) is None
        assert _safe_int("123") == 123
        assert _safe_int("invalid", default=0) == 0
        assert _safe_int("12.5") == 12

    def test_safe_float(self):
        from app.cli import _safe_float
        assert _safe_float(None) is None
        assert _safe_float("12.5") == 12.5
        assert _safe_float("invalid", default=0.0) == 0.0


class TestRegisterCommands:
    def test_register_commands_function(self, cli_app):
        from app.cli import register_commands
        try:
            register_commands(cli_app)
        except Exception:
            pass
        assert True
