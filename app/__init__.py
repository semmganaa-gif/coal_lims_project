# app/__init__.py (Circular Import-ийг зассан)

from flask import Flask
from config import Config
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
import json

# Утилитиудыг дээд талд импортлох
from app.utils.codes import norm_code
from app.constants import ALIAS_TO_BASE_ANALYSIS
from app.utils.datetime import now_local
# (!!!) from app import models-г эндээс УСТГАСАН

# ---- Глобал extension-үүд
db = SQLAlchemy()
migrate = Migrate()
login = LoginManager()
login.login_view = 'main.login'
login.login_message = "Энэ хуудсанд хандахын тулд нэвтэрнэ үү."


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # ---- Extensions-г app-тай холбох
    db.init_app(app)
    migrate.init_app(app, db)
    login.init_app(app)

    # (!!! ШИНЭ) Моделийг энд, init_app-ийн дараа импортлоно
    from app import models 

    # ---- Blueprints
    from app.routes.main_routes import main_bp
    from app.routes.analysis_routes import analysis_bp
    from app.routes.admin_routes import admin_bp
    from app.routes.api_routes import api_bp
    from app.routes.settings_routes import settings_bp
    # app/__init__.py
    from app.routes.report_routes import reports_bp
    from app.routes.import_routes import import_bp





    app.register_blueprint(main_bp)
    app.register_blueprint(analysis_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(api_bp)
    app.register_blueprint(settings_bp)
    app.register_blueprint(reports_bp)
    app.register_blueprint(import_bp)
    
    
    # ======================================================
    # Jinja2 filters
    # ======================================================

    # 1) loads (JSON string -> dict/list)
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

    # 2) fmt_result (тоон үр дүнгийн формат: оронгийн нарийвчлал)
    def _to_float(v):
        try:
            if v is None: return None
            if isinstance(v, (int, float)): return float(v)
            s = str(v).strip().replace(",", ".")
            return float(s) if s else None
        except Exception: return None

    def format_result(value, analysis_code=None, metric=None) -> str:
        x = _to_float(value)
        if x is None: return "-"
        base = norm_code(analysis_code or "")
        ZERO_DEC_BASE   = {"CV"}
        ONE_DEC_BASE    = {"MT", "CSN"}
        INT_ONLY_BASE   = {"Gi", "X", "Y"}
        THREE_DEC_BASE  = {"P", "F", "Cl", "TRD"}
        if base in ZERO_DEC_BASE: return f"{x:.0f}"
        if base in ONE_DEC_BASE: return f"{x:.1f}"
        if base in INT_ONLY_BASE: return f"{int(round(x))}"
        if base in THREE_DEC_BASE: return f"{x:.3f}"
        return f"{x:.2f}"
    app.add_template_filter(
        lambda v, analysis_code=None, metric=None: format_result(v, analysis_code, metric),
        name="fmt_result"
    )

    # 3) fmt_code (base → харагдах alias)
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
        return dict(now_local=now_local)

    # (!!! ШИНЭ) user_loader-г энд, 'models' импортлогдсоны ДАРАА тодорхойлно
    @login.user_loader
    def load_user(id):
        return db.session.get(models.User, int(id))

    return app