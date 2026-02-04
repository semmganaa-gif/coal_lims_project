# app/routes/chemicals/__init__.py
# -*- coding: utf-8 -*-
"""
Химийн бодисын удирдлагын модуль.

Энэ модуль нь лабораторийн химийн бодис, урвалж, индикатор,
стандартуудын бүртгэл, хэрэглээ, нөөцийн хяналтыг удирдана.
"""

from flask import Blueprint

chemicals_bp = Blueprint("chemicals", __name__, url_prefix="/chemicals")

# Файл байршуулахын хязгаарлалт
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB
ALLOWED_EXTENSIONS = {'pdf', 'xlsx', 'xls', 'doc', 'docx', 'jpg', 'jpeg', 'png'}

# Lab types
LAB_TYPES = ['coal', 'water', 'microbiology', 'petrography', 'all']

# Chemical categories
CATEGORIES = [
    ('acid', 'Хүчил'),
    ('base', 'Суурь'),
    ('solvent', 'Уусгагч'),
    ('indicator', 'Индикатор'),
    ('standard', 'Стандарт'),
    ('media', 'Орчин'),
    ('buffer', 'Буфер'),
    ('salt', 'Давс'),
    ('other', 'Бусад'),
]

# Units
UNITS = ['mL', 'L', 'g', 'kg', 'pcs', 'bottle', 'pack']

# Status types
STATUS_TYPES = [
    ('active', 'Идэвхтэй'),
    ('low_stock', 'Бага нөөцтэй'),
    ('expired', 'Хугацаа дууссан'),
    ('empty', 'Дууссан'),
    ('disposed', 'Устгагдсан'),
]

# Route модулиудыг бүртгэх
from app.routes.chemicals import crud, api, waste  # noqa: E402, F401
