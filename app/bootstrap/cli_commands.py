# app/bootstrap/cli_commands.py
"""CLI command registration."""


def init_cli(app):
    """Register Flask CLI commands."""
    try:
        from app import cli as app_cli
        app_cli.register_commands(app)
    except (ImportError, AttributeError) as e:
        app.logger.warning(f"CLI commands registration failed: {e}")
