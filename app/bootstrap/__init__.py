# app/bootstrap/__init__.py
"""
Bootstrap orchestrator — initializes all app components in dependency order.
"""

from app.bootstrap.extensions import init_extensions
from app.bootstrap.i18n import init_i18n
from app.bootstrap.logging_setup import init_logging
from app.bootstrap.websocket import init_websocket
from app.bootstrap.auth import init_auth
from app.bootstrap.blueprints import init_blueprints
from app.bootstrap.cli_commands import init_cli
from app.bootstrap.middleware import init_middleware
from app.bootstrap.jinja import init_jinja
from app.bootstrap.errors import init_error_handlers
from app.bootstrap.security_headers import init_security_headers


def bootstrap_app(app):
    """
    Initialize all app components in correct dependency order.

    Order matters:
    1. Extensions (db, login, csrf, etc.) — everything depends on these
    2. i18n (babel) — needs app config
    3. Logging/monitoring/sentry — early for error capture
    4. WebSocket — needs app + socketio
    5. Models import — needs db.init_app done first
    6. Auth (user_loader) — needs models
    7. Blueprints + labs — needs models + extensions
    8. CLI commands
    9. Middleware (license check) — needs blueprints registered
    10. Jinja filters + context — needs constants, labs
    11. Error handlers
    12. Security headers
    """
    # 1. Extensions
    init_extensions(app)

    # 2. i18n
    init_i18n(app)

    # 3. Logging, monitoring, Sentry
    init_logging(app)

    # 4. WebSocket
    init_websocket(app)

    # 5. Models (must be after db.init_app)
    from app import models  # noqa: F401

    # 6. Auth
    init_auth(app)

    # 7. Blueprints + labs
    init_blueprints(app)

    # 8. CLI
    init_cli(app)

    # 9. Middleware (license check)
    init_middleware(app)

    # 10. Jinja filters + context processor
    init_jinja(app)

    # 11. Error handlers
    init_error_handlers(app)

    # 12. Security headers
    init_security_headers(app)
