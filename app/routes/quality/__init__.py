# app/routes/quality/__init__.py
# -*- coding: utf-8 -*-
"""
ISO 17025 Quality Management routes
"""

from flask import Blueprint

bp = Blueprint('quality', __name__, url_prefix='/quality')

# Route-үүд бүртгэгдсэн эсэхийг хянах
_routes_registered = False

from .proficiency import register_routes as register_proficiency_routes
from .environmental import register_routes as register_environmental_routes
from .control_charts import register_routes as register_control_charts_routes
from .complaints import register_routes as register_complaints_routes
from .improvement import register_routes as register_improvement_routes
from .nonconformity import register_routes as register_nonconformity_routes
from .capa import register_routes as register_capa_routes


def register_routes_all():
    """Бүх quality routes бүртгэх (зөвхөн нэг удаа)"""
    global _routes_registered
    if _routes_registered:
        return
    _routes_registered = True

    register_proficiency_routes(bp)
    register_environmental_routes(bp)
    register_control_charts_routes(bp)
    register_complaints_routes(bp)
    register_improvement_routes(bp)
    register_nonconformity_routes(bp)
    register_capa_routes(bp)
