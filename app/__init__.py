# app/__init__.py

from flask import Flask
from config import Config
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_wtf.csrf import CSRFProtect
from flask_mail import Mail
from flask_socketio import SocketIO
import json

# Утилитиудыг дээд талд импортлох
from app.utils.codes import norm_code
from app.constants import ALIAS_TO_BASE_ANALYSIS
from app.utils.datetime import now_local

# ---- Глобал extension-үүд
db = SQLAlchemy()
migrate = Migrate()
login = LoginManager()
login.login_view = 'main.login'
login.login_message = "Энэ хуудсанд хандахын тулд нэвтэрнэ үү."
mail = Mail()

# WebSocket - Real-time чат
socketio = SocketIO()

# CSRF хамгаалалт
csrf = CSRFProtect()

# ✅ Rate limiter - Brute force халдлагаас хамгаалах (ИДЭВХЖҮҮЛСЭН)
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"],  # Ерөнхий хязгаар
    storage_uri="memory://"
)

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Template auto-reload (dev mode)
    app.config['TEMPLATES_AUTO_RELOAD'] = True

    # ---- Extensions-г app-тай холбох
    db.init_app(app)
    migrate.init_app(app, db)
    login.init_app(app)
    csrf.init_app(app)
    limiter.init_app(app)
    mail.init_app(app)

    # ✅ WebSocket initialization - CORS тохиргоотой
    socketio.init_app(
        app,
        cors_allowed_origins=app.config.get('SOCKETIO_CORS_ORIGINS', None),
        async_mode='threading'
    )

    # Register SocketIO events
    with app.app_context():
        from app.routes import chat_events  # noqa: F401

    # ---- Setup Structured Logging
    from app.logging_config import setup_logging
    setup_logging(app)

    # ---- Setup Performance Monitoring
    from app.monitoring import setup_monitoring
    setup_monitoring(app)

    # (!!!) Моделийг энд, init_app-ийн дараа импортлоно
    from app import models

    # ---- Blueprints (Route-уудыг бүртгэх)
    from app.routes.main import main_bp
    from app.routes.analysis import analysis_bp
    from app.routes.admin_routes import admin_bp
    from app.routes.api import api_bp
    from app.routes.settings_routes import settings_bp
    from app.routes.report_routes import reports_bp
    from app.routes.import_routes import import_bp

    # Тоног төхөөрөмжийн модуль (ISO 17025)
    from app.routes.equipment_routes import equipment_bp

    # Чанарын удирдлага (ISO 17025 - Quality Management Systems)
    from app.routes.quality import bp as quality_bp, register_routes_all as register_quality_routes

    # Blueprint давхар бүртгэгдэхээс хамгаалах (тест орчинд чухал)
    def safe_register_blueprint(blueprint):
        if blueprint.name not in app.blueprints:
            app.register_blueprint(blueprint)

    safe_register_blueprint(main_bp)
    safe_register_blueprint(analysis_bp)
    safe_register_blueprint(admin_bp)
    safe_register_blueprint(api_bp)
    safe_register_blueprint(settings_bp)
    safe_register_blueprint(reports_bp)
    safe_register_blueprint(import_bp)
    safe_register_blueprint(equipment_bp)

    # Чанарын удирдлагын route-уудыг бүртгэх
    if quality_bp.name not in app.blueprints:
        register_quality_routes()
        app.register_blueprint(quality_bp)

    # CLI commands
    try:
        from app import cli as app_cli
        app_cli.register_commands(app)
    except Exception:
        pass

    # API blueprint-g CSRF-ees cholooloh
    csrf.exempt(api_bp)

    # ======================================================
    # Jinja2 filters
    # ======================================================

    # 1) loads
    def jinja_loads_filter(value):
        if isinstance(value, (dict, list)):
            return value
        if isinstance(value, str):
            s = value.strip()
            if (s.startswith("{") and s.endswith("}")) or (s.startswith("[") and s.endswith("]")):
                try:
                    return json.loads(s)
                except Exception:
                    return {} if s.startswith("{") else []
        return {}
    app.jinja_env.filters["loads"] = jinja_loads_filter

    # 2) fmt_result - ШИНЭЧИЛСЭН: Centralized precision config ашиглана
    from app.config.display_precision import format_result as format_result_centralized

    app.add_template_filter(
        lambda v, analysis_code=None, metric=None: format_result_centralized(v, analysis_code),
        name="fmt_result"
    )

    # 3) fmt_code
    _REV: dict[str, set[str]] = {}
    for alias_lc, base in ALIAS_TO_BASE_ANALYSIS.items():
        if not base: continue
        _REV.setdefault(base, set()).add(alias_lc)

    _PREF_ORDER = ["st,ad", "qgr,ad", "mt,ar", "trd,d", "p,ad", "f,ad", "cl,ad"]

    def _pick_display_alias(base: str) -> str:
        aliases = _REV.get(base, set())
        for pref in _PREF_ORDER:
            if pref in aliases: return pref
        return base

    def fmt_code(code: str | None) -> str:
        if not code: return ""
        c = str(code).strip()
        if "," in c: return c
        base = norm_code(c)
        alias = _pick_display_alias(base)
        if alias and "," in alias:
            left, right = alias.split(",", 1)
            if left: left_norm = left[0].upper() + left[1:].lower()
            else: left_norm = left
            return f"{left_norm},{right.lower()}"
        return alias or c

    app.add_template_filter(fmt_code, name="fmt_code")

    # (!!!) 'now_local'-г template-д таниулах
    @app.context_processor
    def inject_utility_functions():
        from app.utils.repeatability_loader import load_limit_rules
        return dict(now_local=now_local, LIMS_LIMIT_RULES=load_limit_rules())

    @login.user_loader
    def load_user(id):
        return db.session.get(models.User, int(id))

    # ======================================================
    # API Documentation (Swagger)
    # ======================================================
    # Uncomment to enable Swagger API docs at /api/docs/
    # from app.api_docs import setup_api_docs
    # setup_api_docs(app)

    # ======================================================
    # Error Handlers
    # ======================================================

    @app.errorhandler(404)
    def not_found_error(error):
        """404 - Хуудас олдсонгүй"""
        from flask import render_template
        return render_template('errors/404.html'), 404

    @app.errorhandler(500)
    def internal_error(error):
        """500 - Серверийн алдаа"""
        from flask import render_template
        # Database rollback хийх (transaction-ий алдаа байвал)
        db.session.rollback()
        # Алдааг log-д бичих
        app.logger.error(f'Server Error: {error}', exc_info=True)
        return render_template('errors/500.html'), 500

    @app.errorhandler(403)
    def forbidden_error(error):
        """403 - Нэвтрэх эрхгүй"""
        from flask import render_template
        return render_template('errors/403.html'), 403

    @app.errorhandler(429)
    def ratelimit_handler(error):
        """429 - Rate limit хязгаарлалт"""
        from flask import render_template, jsonify, request
        # API request бол JSON буцаах
        if request.path.startswith('/api/'):
            return jsonify({
                'error': 'Хэт олон хүсэлт илгээсэн байна. Түр хүлээгээд дахин оролдоно уу.',
                'status': 429
            }), 429
        # Бусад тохиолдолд HTML template
        return render_template('errors/429.html'), 429

    # ======================================================
    # Security Headers
    # ======================================================
    @app.after_request
    def add_security_headers(response):
        """Аюулгүй байдлын HTTP headers нэмэх"""
        # Clickjacking хамгаалалт
        response.headers['X-Frame-Options'] = 'SAMEORIGIN'
        # MIME sniffing хамгаалалт
        response.headers['X-Content-Type-Options'] = 'nosniff'
        # XSS хамгаалалт (хуучин browser-үүдэд)
        response.headers['X-XSS-Protection'] = '1; mode=block'
        # Referrer мэдээлэл хязгаарлах
        response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'

        # ✅ ШИНЭ: Content Security Policy (XSS хамгаалалт)
        # Note: 'unsafe-inline' шаардлагатай - Flask templates inline script/style ашигладаг
        csp = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://cdn.jsdelivr.net https://unpkg.com; "
            "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://fonts.googleapis.com; "
            "font-src 'self' https://fonts.gstatic.com https://cdn.jsdelivr.net; "
            "img-src 'self' data: blob:; "
            "connect-src 'self' ws: wss:; "
            "frame-ancestors 'self';"
        )
        response.headers['Content-Security-Policy'] = csp

        # ✅ ШИНЭ: HTTPS-д шилжүүлэх (Production-д)
        if not app.debug:
            response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'

        return response

    return app
