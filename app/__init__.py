# app/__init__.py
"""
Coal LIMS Application Factory.

Thin orchestration shell — all bootstrap logic lives in app/bootstrap/.
Extension instances are re-exported here for backward compatibility
(e.g. `from app import db, cache, socketio`).
"""

from flask import Flask
from config import Config

# Re-export extension instances so existing code keeps working:
#   from app import db, migrate, login, mail, babel, cache, socketio, csrf, limiter
from app.bootstrap.extensions import (  # noqa: F401
    db,
    migrate,
    login,
    mail,
    babel,
    cache,
    socketio,
    csrf,
    limiter,
)


def create_app(config_class=Config):
    """Flask application factory."""
    app = Flask(__name__)
    app.config.from_object(config_class)
    app.config['TEMPLATES_AUTO_RELOAD'] = True
    app.config['JSON_AS_ASCII'] = False

    from app.bootstrap import bootstrap_app
    bootstrap_app(app)

    return app
