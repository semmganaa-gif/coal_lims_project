# app/bootstrap/logging_setup.py
"""Structured logging, monitoring, and Sentry initialization."""


def init_logging(app):
    """Setup structured logging, monitoring, and Sentry."""
    from app.logging_config import setup_logging
    setup_logging(app)

    from app.monitoring import setup_monitoring
    setup_monitoring(app)

    from app.sentry_integration import init_sentry
    init_sentry(app)
