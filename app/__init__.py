# app/__init__.py
"""
Coal LIMS Application Factory.

Flask application үүсгэх factory pattern. Extensions, blueprints,
error handlers болон middleware-үүдийг тохируулна.
"""

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
from flask_babel import Babel, lazy_gettext as _l
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
login.login_message = _l("Please log in to access this page.")
mail = Mail()
babel = Babel()

# WebSocket - Real-time чат
socketio = SocketIO()

# CSRF хамгаалалт
csrf = CSRFProtect()

# ✅ Rate limiter - Brute force халдлагаас хамгаалах
# create_app дотор init_app хийгдэнэ
# 10+ химич, 1200+ шинжилгээ/өдөр тооцсон
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["10000 per day", "500 per hour"],  # LIMS production хязгаар
    storage_uri=None
)


def create_app(config_class=Config):
    """Flask application үүсгэх factory function."""
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Template auto-reload (dev mode)
    app.config['TEMPLATES_AUTO_RELOAD'] = True

    # ✅ JSON UTF-8 encoding - Монгол текст зөв харагдахын тулд
    app.config['JSON_AS_ASCII'] = False

    # ✅ Development mode дээр Secure cookie унтраах (HTTP дээр ажиллуулахад)
    if app.config.get('ENV') == 'development' or app.debug:
        app.config['SESSION_COOKIE_SECURE'] = False

    # ---- Extensions-г app-тай холбох
    db.init_app(app)
    migrate.init_app(app, db)
    login.init_app(app)
    csrf.init_app(app)
    # Limiter storage (Redis гэх мэт). Default: memory://
    app.config.setdefault("RATELIMIT_STORAGE_URI", "memory://")
    limiter.storage_uri = app.config["RATELIMIT_STORAGE_URI"]
    limiter.init_app(app)
    mail.init_app(app)

    # Flask-Babel (i18n) - locale_selector
    def get_locale():
        from flask import session
        lang = session.get('language')
        if lang in ('en', 'mn'):
            return lang
        from flask_login import current_user
        if current_user.is_authenticated and getattr(current_user, 'language', None):
            return current_user.language
        return 'en'

    babel.init_app(app, locale_selector=get_locale)

    # ✅ WebSocket initialization - CORS тохиргоотой
    socketio.init_app(
        app,
        cors_allowed_origins=app.config.get('SOCKETIO_CORS_ORIGINS', None),
        async_mode='threading'
    )

    # Register SocketIO events
    with app.app_context():
        from app.routes.chat import events as chat_events  # noqa: F401

    # ---- Setup Structured Logging
    from app.logging_config import setup_logging
    setup_logging(app)

    # ---- Setup Performance Monitoring
    from app.monitoring import setup_monitoring
    setup_monitoring(app)

    # ---- Setup Sentry Error Tracking
    from app.sentry_integration import init_sentry
    init_sentry(app)

    # (!!!) Моделийг энд, init_app-ийн дараа импортлоно
    from app import models

    # ---- Blueprints (Route-уудыг бүртгэх)
    from app.routes.main import main_bp
    from app.routes.analysis import analysis_bp
    from app.routes.admin.routes import admin_bp
    from app.routes.api import api_bp
    from app.routes.settings.routes import settings_bp
    from app.routes.reports.routes import reports_bp
    from app.routes.imports.routes import import_bp

    # Тоног төхөөрөмжийн модуль (ISO 17025)
    from app.routes.equipment import equipment_bp

    # Химийн бодисын модуль
    from app.routes.chemicals import chemicals_bp

    # PDF тайлангийн модуль
    from app.routes.reports import pdf_reports_bp

    # Сэлбэг хэрэгслийн модуль
    from app.routes.spare_parts import spare_parts_bp

    # Лиценз хамгаалалт
    from app.routes.license.routes import license_bp

    # Чанарын удирдлага (ISO 17025 - Quality Management Systems)
    from app.routes.quality import bp as quality_bp, register_routes_all as register_quality_routes

    # Мульти-лаборатори (Петрограф, Усны лаб)
    from app.labs import register_lab
    from app.labs.coal import CoalLab
    from app.labs.petrography import PetrographyLab
    from app.labs.petrography.routes import petro_bp

    # Усны лаборатори (Water Lab = Chemistry + Microbiology)
    from app.labs.water_lab import WaterLaboratory
    from app.labs.water_lab.chemistry import ChemistryLab
    from app.labs.water_lab.microbiology import MicrobiologyLab
    from app.labs.water_lab.routes import water_lab_bp
    from app.labs.water_lab.chemistry.routes import water_bp
    from app.labs.water_lab.microbiology.routes import micro_bp

    # Лаб instance-уудыг бүртгэх
    register_lab(CoalLab())
    register_lab(PetrographyLab())
    register_lab(WaterLaboratory())  # Parent lab
    register_lab(ChemistryLab())     # water key for backward compatibility
    register_lab(MicrobiologyLab())

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
    safe_register_blueprint(chemicals_bp)
    safe_register_blueprint(pdf_reports_bp)
    safe_register_blueprint(spare_parts_bp)
    safe_register_blueprint(license_bp)
    safe_register_blueprint(petro_bp)
    safe_register_blueprint(water_lab_bp)  # Parent: /labs/water-lab
    safe_register_blueprint(water_bp)      # Chemistry: /labs/water-lab/chemistry
    safe_register_blueprint(micro_bp)      # Microbiology: /labs/water-lab/microbiology

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

    # CSRF exempt: зөвхөн JSON API blueprint-үүд
    # HTML form-тэй blueprint-үүдийг exempt хийхгүй (CSRF хамгаалалттай)
    csrf.exempt(api_bp)       # Pure JSON API - CSRF exempt зөв
    # petro_bp CSRF exempt устгасан — template-ууд X-CSRFToken илгээдэг

    # ======================================================
    # Лиценз хамгаалалт - before_request hook
    # ======================================================
    from flask import redirect, url_for, flash, request, g
    from flask_login import current_user

    # Лиценз шалгахгүй endpoint-үүд
    LICENSE_EXEMPT_ENDPOINTS = {
        'license.activate', 'license.info', 'license.expired', 'license.error',
        'license.check', 'license.hardware_id',
        'main.login', 'main.logout', 'main.register',
        'static', 'health_check'  # Health check for Docker/K8s
    }

    @app.before_request
    def check_license():
        """Бүх хүсэлт дээр лиценз шалгах"""
        # Тест орчинд лиценз шалгахгүй
        if app.config.get('TESTING'):
            g.license_valid = True
            g.license_warning = None
            g.license_info = {'company': 'Test', 'expires_at': '2099-12-31'}
            return None

        # Static файлууд болон лицензийн хуудсуудыг алгасах
        if request.endpoint in LICENSE_EXEMPT_ENDPOINTS:
            return None
        if request.endpoint and request.endpoint.startswith('static'):
            return None

        # Нэвтрээгүй хэрэглэгч - login хуудас руу
        if not current_user.is_authenticated:
            return None

        # Лиценз шалгах
        from app.utils.license_protection import license_manager
        result = license_manager.validate_license()

        # Лицензийн статусыг template-д дамжуулах
        g.license_valid = result.get('valid', False)
        g.license_warning = result.get('warning')
        g.license_info = result.get('license')

        if not result['valid']:
            error = result.get('error', 'UNKNOWN_ERROR')

            # Admin хэрэглэгч бол лиценз идэвхжүүлэх хуудас руу
            if current_user.role == 'admin':
                if error == 'LICENSE_NOT_FOUND':
                    flash('License not found. Please activate.', 'warning')
                    return redirect(url_for('license.activate'))
                elif error == 'LICENSE_EXPIRED':
                    flash('License has expired.', 'error')
                    return redirect(url_for('license.expired'))
                else:
                    flash(f'License error: {error}', 'error')
                    return redirect(url_for('license.error'))
            else:
                # Энгийн хэрэглэгч - алдааны мэдээлэл
                flash('System license issue. Please contact administrator.', 'error')
                return redirect(url_for('license.error'))

        return None

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

    # 3) fmt_code — subscript-тэй шинжилгээний код (HTML output)
    #    Жишээ: 'Mad' → 'M<sub>ad</sub>', 'St,d' → 'S<sub>t,d</sub>'
    from markupsafe import Markup
    from app.constants import ANALYSIS_CODE_SUBSCRIPTS

    def fmt_code(code: str | None) -> Markup:
        if not code:
            return Markup("")
        c = str(code).strip()
        lookup = c.lower().replace(" ", "")
        sub = ANALYSIS_CODE_SUBSCRIPTS.get(lookup)
        if sub:
            prefix, subscript = sub
            if subscript:
                return Markup(f'{prefix}<sub>{subscript}</sub>')
            return Markup(prefix)
        # Fallback: comma байвал subscript болгох (Ж: "St,d" → S<sub>t,d</sub>)
        if "," in c:
            parts = c.split(",", 1)
            prefix_part = parts[0]
            sub_part = parts[1]
            # prefix-ийн сүүлийн жижиг үсгүүдийг subscript-д нэмэх
            i = len(prefix_part)
            for j in range(len(prefix_part) - 1, 0, -1):
                if prefix_part[j].islower():
                    i = j
                else:
                    break
            if i < len(prefix_part):
                real_prefix = prefix_part[:i]
                sub_start = prefix_part[i:]
                return Markup(f'{real_prefix}<sub>{sub_start},{sub_part}</sub>')
            return Markup(f'{prefix_part}<sub>{sub_part}</sub>')
        return Markup(c)

    app.add_template_filter(fmt_code, name="fmt_code")

    # (!!!) 'now_local'-г template-д таниулах
    @app.context_processor
    def inject_utility_functions():
        from app.utils.repeatability_loader import load_limit_rules
        from app.labs import LAB_TYPES
        return dict(
            now_local=now_local,
            LIMS_LIMIT_RULES=load_limit_rules(),
            LAB_TYPES=LAB_TYPES,
            get_locale=get_locale,
        )

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
                'error': 'Too many requests. Please wait and try again.',
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
            "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://unpkg.com; "
            "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://unpkg.com https://fonts.googleapis.com; "
            "font-src 'self' https://fonts.gstatic.com https://cdn.jsdelivr.net; "
            "img-src 'self' data: blob:; "
            "connect-src 'self' ws: wss:; "
            "frame-ancestors 'self';"
        )
        response.headers['Content-Security-Policy'] = csp

        # Permissions-Policy: камер, микрофон, GPS зэрэг API хязгаарлах
        response.headers['Permissions-Policy'] = 'microphone=(), camera=(), geolocation=()'
        response.headers['X-Permitted-Cross-Domain-Policies'] = 'none'

        # ✅ ШИНЭ: HTTPS-д шилжүүлэх (Production-д)
        if not app.debug:
            response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'

        return response

    return app
