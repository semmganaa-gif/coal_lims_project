# app/bootstrap/blueprints.py
"""Blueprint and lab registration."""

from app.bootstrap.extensions import csrf


def init_blueprints(app):
    """Import and register all blueprints and labs."""
    # ---- Lab instances ----
    from app.labs import register_lab
    from app.labs.coal import CoalLab
    from app.labs.petrography import PetrographyLab
    from app.labs.water_lab import WaterLaboratory
    from app.labs.water_lab.chemistry import ChemistryLab
    from app.labs.water_lab.microbiology import MicrobiologyLab

    register_lab(CoalLab())
    register_lab(PetrographyLab())
    register_lab(WaterLaboratory())
    register_lab(ChemistryLab())
    register_lab(MicrobiologyLab())

    # ---- Blueprint imports ----
    from app.routes.main import main_bp
    from app.routes.analysis import analysis_bp
    from app.routes.admin.routes import admin_bp
    from app.routes.api import api_bp, APIVersionMiddleware
    from app.routes.settings.routes import settings_bp
    from app.routes.reports.routes import reports_bp
    from app.routes.imports.routes import import_bp
    from app.routes.equipment import equipment_bp
    from app.routes.chemicals import chemicals_bp
    from app.routes.reports import pdf_reports_bp
    from app.routes.spare_parts import spare_parts_bp
    from app.routes.license.routes import license_bp
    from app.routes.quality import bp as quality_bp, register_routes_all as register_quality_routes
    from app.labs.petrography.routes import petro_bp
    from app.labs.water_lab.routes import water_lab_bp
    from app.labs.water_lab.chemistry.routes import water_bp
    from app.labs.water_lab.microbiology.routes import micro_bp

    # ---- Safe registration (prevents duplicate in test env) ----
    def _safe_register(blueprint):
        if blueprint.name not in app.blueprints:
            app.register_blueprint(blueprint)

    _safe_register(main_bp)
    _safe_register(analysis_bp)
    _safe_register(admin_bp)
    _safe_register(api_bp)
    _safe_register(settings_bp)
    _safe_register(reports_bp)
    _safe_register(import_bp)
    _safe_register(equipment_bp)
    _safe_register(chemicals_bp)
    _safe_register(pdf_reports_bp)
    _safe_register(spare_parts_bp)
    _safe_register(license_bp)
    _safe_register(petro_bp)
    _safe_register(water_lab_bp)
    _safe_register(water_bp)
    _safe_register(micro_bp)

    # Quality management routes
    if quality_bp.name not in app.blueprints:
        register_quality_routes()
        app.register_blueprint(quality_bp)

    # CSRF exempt: JSON API only
    csrf.exempt(api_bp)

    # WSGI middleware: /api/* → /api/v1/* backward-compat rewrite
    app.wsgi_app = APIVersionMiddleware(app.wsgi_app, app)
