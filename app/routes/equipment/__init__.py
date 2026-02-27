# app/routes/equipment/__init__.py
# -*- coding: utf-8 -*-
"""
Тоног төхөөрөмжийн удирдлагын модуль (ISO 17025).

Энэ модуль нь лабораторийн тоног төхөөрөмжийн бүртгэл, засвар үйлчилгээ,
калибрацийн хяналт болон ашиглалтын журналыг удирдана.
"""

from flask import Blueprint
from app import limiter

equipment_bp = Blueprint("equipment", __name__)

# A-H2: Blueprint-level rate limit (бүх endpoint-д хамаарна)
limiter.limit("200 per minute")(equipment_bp)

# Файл байршуулахын хязгаарлалт
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB
ALLOWED_EXTENSIONS = {'pdf', 'xlsx', 'xls', 'doc', 'docx', 'jpg', 'jpeg', 'png', 'txt'}

# Route модулиудыг бүртгэх (Blueprint-д route-уудыг холбох)
from app.routes.equipment import crud, api, registers  # noqa: E402, F401
