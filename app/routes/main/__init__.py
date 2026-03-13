# app/routes/main/__init__.py
# -*- coding: utf-8 -*-
"""
Main модулиудыг нэгтгэсэн blueprint.

Бүтэц:
  - helpers.py: Туслах функцүүд (get_12h_shift_code, get_quarter_code, is_safe_url)
  - auth.py: Нэвтрэх/Гарах (2 routes)
  - index.py: Нүүр хуудас + live preview (2 routes)
  - samples.py: Дээж засах/устгах (2 routes)

Өмнөх main_routes.py (522 мөр) → 4 модуляр файл
"""

from flask import Blueprint

# Үндсэн "main" blueprint үүсгэх
main_bp = Blueprint("main", __name__)

# Бүх модулиудыг импортлоод route-уудыг main_bp дээр бүртгэх
from . import auth
from . import index
from . import samples
from . import hourly_report  # noqa: F401 — registers @main_bp.route
from . import tools

# Route-уудыг бүртгэх
auth.register_routes(main_bp)
index.register_routes(main_bp)
samples.register_routes(main_bp)
tools.register_routes(main_bp)
