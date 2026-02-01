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

Өмнөх api_routes.py (1405 мөр) → 4 бие даасан модуль болон shared helpers
"""

from flask import Blueprint

# Үндсэн "api" blueprint үүсгэх
api_bp = Blueprint("api", __name__, url_prefix="/api")

# Бүх модулиудыг импортлоод route-уудыг api_bp дээр бүртгэх
# Энэ нь endpoint нэр өөрчлөгдөхөөс сергийлнэ (api.data хэвээр үлдэнэ)
from . import samples_api
from . import analysis_api
from . import audit_api
from . import mass_api
from . import chat_api
from . import icpms_api
from . import morning_api

# Route-уудыг бүртгэх
samples_api.register_routes(api_bp)
analysis_api.register_routes(api_bp)
audit_api.register_routes(api_bp)
mass_api.register_routes(api_bp)
chat_api.register_routes(api_bp)
icpms_api.register_routes(api_bp)
morning_api.register_routes(api_bp)
