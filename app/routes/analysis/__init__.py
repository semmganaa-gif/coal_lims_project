# app/routes/analysis/__init__.py
# -*- coding: utf-8 -*-
"""
Analysis модулиудыг нэгтгэсэн blueprint.

Бүтэц:
  - helpers.py: Хамтын хэрэгсэл, тогтмол, декоратор
  - workspace.py: Химичийн ажлын талбар (2 routes)
  - senior.py: Ахлахын хяналт (3 routes)
  - kpi.py: KPI / Ээлжийн гүйцэтгэл (1 route)
  - qc.py: QC хэрэгслүүд (3 routes)

Өмнөх analysis_routes.py (1139 мөр) → 5 модуляр файл
АНХААР: Давхардсан 5 route-ыг устгасан (api модульд байгаа)
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
