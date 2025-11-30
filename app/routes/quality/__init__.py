# app/routes/quality/__init__.py
# -*- coding: utf-8 -*-
"""
ISO 17025 Quality Management routes
"""

from flask import Blueprint

bp = Blueprint('quality', __name__, url_prefix='/quality')

from .capa import register_routes as register_capa_routes
from .proficiency import register_routes as register_proficiency_routes
from .environmental import register_routes as register_environmental_routes
from .control_charts import register_routes as register_control_charts_routes
from .complaints import register_routes as register_complaints_routes

def register_routes_all():
    """Бүх quality routes бүртгэх"""
    register_capa_routes(bp)
    register_proficiency_routes(bp)
    register_environmental_routes(bp)
    register_control_charts_routes(bp)
    register_complaints_routes(bp)
