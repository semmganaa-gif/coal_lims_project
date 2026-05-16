# app/routes/api/__init__.py
# -*- coding: utf-8 -*-
"""
API модулиудыг нэгтгэсэн blueprint.

Бүтэц:
  - samples_api.py: Дээжтэй холбоотой endpoints (4)
  - analysis_api.py: Шинжилгээтэй холбоотой endpoints (3)
  - audit_api.py: Аудиттай холбоотой endpoints (2)
  - mass_api.py: Массын ажлын талбартай холбоотой endpoints (6)
  - helpers.py: Хамтын хэрэгсэл, дүрэм, шалгалтууд

API Versioning:
  - /api/v1/... — одоогийн version (v1)
  - /api/...   — backward-compat redirect → /api/v1/...
  - url_for('api.data') → /api/v1/data (автоматаар)
"""

from flask import Blueprint

# ---- v1 API blueprint (үндсэн) ----
api_bp = Blueprint("api", __name__, url_prefix="/api/v1")

# Бүх модулиудыг импортлоод route-уудыг api_bp дээр бүртгэх
from . import samples_api
from . import analysis_api
from . import audit_api
from . import mass_api
from . import chat_api
from . import morning_api
from . import simulator_api
from . import sla_api
from . import instrument_api  # noqa: F401 — routes registered via decorators
from . import workflow_api  # noqa: F401 — routes registered via decorators
from . import report_builder_api  # noqa: F401 — routes registered via decorators
from . import analytics_api
from . import mine2nemo_api

samples_api.register_routes(api_bp)
analysis_api.register_routes(api_bp)
audit_api.register_routes(api_bp)
mass_api.register_routes(api_bp)
chat_api.register_routes(api_bp)
morning_api.register_routes(api_bp)
simulator_api.register_routes(api_bp)
sla_api.register_routes(api_bp)
analytics_api.register_routes(api_bp)
mine2nemo_api.register_routes(api_bp)


class APIVersionMiddleware:
    """
    WSGI middleware: /api/* → /api/v1/* transparent rewrite.

    Хуучин /api/xxx хүсэлтүүдийг /api/v1/xxx руу дотооддоо чиглүүлнэ.
    Redirect биш — client-д ил харагдахгүй, test-үүд эвдрэхгүй.

    Зөвхөн Flask URL map-д original path олдохгүй бол rewrite хийнэ.
    Бусад blueprint-ийн /api/* route-уудыг эвдэхгүй.
    """

    def __init__(self, wsgi_app, flask_app):
        self.wsgi_app = wsgi_app
        self.flask_app = flask_app
        self._adapter = None

    def _get_adapter(self):
        if self._adapter is None:
            self._adapter = self.flask_app.url_map.bind("")
        return self._adapter

    def __call__(self, environ, start_response):
        path = environ.get("PATH_INFO", "")

        if path.startswith("/api/") and not path.startswith(("/api/v1/", "/api/docs/")):
            # Original path-ыг Flask URL map-аас шалгах
            try:
                self._get_adapter().match(path, method=environ.get("REQUEST_METHOD", "GET"))
                # Original path олдсон → rewrite хийхгүй
            except Exception:
                # Original path олдохгүй → /api/v1/... руу rewrite
                environ["PATH_INFO"] = "/api/v1" + path[4:]
        elif path == "/api":
            environ["PATH_INFO"] = "/api/v1"

        return self.wsgi_app(environ, start_response)
