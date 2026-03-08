# app/routes/analysis/__init__.py
# -*- coding: utf-8 -*-
"""
Analysis модулиудыг нэгтгэсэн blueprint.

Бүтэц:
  - workspace.py: Химичийн ажлын талбар (analysis_hub, analysis_page)
  - senior.py: Ахлахын хяналт (dashboard, approve/reject, bulk, repeat)
  - kpi.py: KPI / Ээлжийн гүйцэтгэл (shift_daily, kpi_summary)
  - qc.py: QC хэрэгслүүд (composite_check, norm_limit, correlation)
"""

from flask import Blueprint

# Үндсэн "analysis" blueprint үүсгэх
analysis_bp = Blueprint("analysis", __name__)

# Бүх модулиудыг импортлоод route-уудыг analysis_bp дээр бүртгэх
from . import workspace
from . import senior
from . import kpi
from . import qc

# Route-уудыг бүртгэх
workspace.register_routes(analysis_bp)
senior.register_routes(analysis_bp)
kpi.register_routes(analysis_bp)
qc.register_routes(analysis_bp)
