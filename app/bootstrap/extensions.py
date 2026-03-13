# app/bootstrap/extensions.py
"""
Flask extension instances and initialization.

All extension objects are created here at module level (before app context).
init_extensions(app) binds them to the Flask app.
"""

from decimal import Decimal
from flask.json.provider import DefaultJSONProvider
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_login import current_user as _limiter_current_user
from flask_wtf.csrf import CSRFProtect
from flask_mail import Mail
from flask_socketio import SocketIO
from flask_babel import Babel, lazy_gettext as _l
from flask_caching import Cache


# ---- Global extension instances ----
db = SQLAlchemy()
migrate = Migrate()
login = LoginManager()
login.login_view = 'main.login'
login.login_message = _l("Please log in to access this page.")
mail = Mail()
babel = Babel()
cache = Cache()
socketio = SocketIO()
csrf = CSRFProtect()
def _rate_limit_key():
    """Authenticated хэрэглэгчийг user ID-аар, бусдыг IP-аар тодорхойлох."""
    try:
        if getattr(_limiter_current_user, 'is_authenticated', False):
            return f"user:{_limiter_current_user.id}"
    except RuntimeError:
        pass  # app context-гүй үед (test, CLI)
    return get_remote_address()


limiter = Limiter(
    key_func=_rate_limit_key,
    default_limits=["10000 per day", "500 per hour"],
    storage_uri=None
)


class _LIMSJSONProvider(DefaultJSONProvider):
    """Extend Flask's JSON provider to handle Decimal (Numeric columns)."""

    @staticmethod
    def default(o):
        if isinstance(o, Decimal):
            return float(o)
        return DefaultJSONProvider.default(o)


def init_extensions(app):
    """Bind all extensions to the Flask app."""
    # JSON provider
    app.json_provider_class = _LIMSJSONProvider
    app.json = _LIMSJSONProvider(app)

    # Core extensions
    db.init_app(app)
    migrate.init_app(app, db)
    login.init_app(app)
    csrf.init_app(app)
    mail.init_app(app)
    cache.init_app(app)

    # Rate limiter
    app.config.setdefault("RATELIMIT_STORAGE_URI", "memory://")
    limiter.storage_uri = app.config["RATELIMIT_STORAGE_URI"]
    limiter.init_app(app)
    if app.config["RATELIMIT_STORAGE_URI"] == "memory://" and not app.debug:
        app.logger.warning(
            "Rate limiter: memory:// storage — multi-worker орчинд Redis ашиглана уу. "
            "RATELIMIT_STORAGE_URI=redis://localhost:6379"
        )
