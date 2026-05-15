# app/routes/spare_parts/__init__.py
"""Сэлбэг хэрэгслийн routes - нөөцийн удирдлага."""

from flask import Blueprint
from app import limiter

spare_parts_bp = Blueprint(
    "spare_parts",
    __name__,
    url_prefix="/spare_parts",
    template_folder="../../templates/spare_parts"
)

# A-H2: Blueprint-level rate limit (бүх endpoint-д хамаарна)
limiter.limit("200 per minute")(spare_parts_bp)

# Constants - Тоног төхөөрөмжөөр категори
CATEGORIES = [
    ('sulfur_s144dr', 'Хүхэр багаж S-144DR'),
    ('sulfur_5e_irs', 'Хүхэр багаж 5E-IRS II'),
    ('muffle_5e_mf6000', 'Шатаах зуух 5E-MF6000'),
    ('muffle_aaf', 'Шатаах зуух AAF'),
    ('calorimeter_c2000', 'Илчлэг багаж C2000'),
    ('calorimeter_c5000', 'Илчлэг багаж C5000'),
    ('calorimeter_bomb', 'Илчлэгийн бомб'),
    ('csi_crucible', 'Хөөлтийн зэрэг багаж'),
    ('mill', 'Тээрэм'),
    ('dryer_prieser', 'Хатаах шүүгээ Prieser'),
    ('magnetite', 'Магнетитийн багаж'),
    ('drum', 'Барьцалдах чадвар барабан'),
    ('mixer', 'Автомат холигч'),
    ('general', 'Бусад хэрэгсэл'),
]

UNITS = ['pcs', 'set', 'box', 'roll', 'm', 'pack', 'pair', 'kg', 'L']

STATUS_TYPES = [
    ('active', 'Идэвхтэй'),
    ('low_stock', 'Нөөц бага'),
    ('out_of_stock', 'Дууссан'),
    ('disposed', 'Устгагдсан'),
]

# Route registration side-effects (декоратор-аар blueprint-д бүртгэгдэнэ)
from app.routes.spare_parts import crud  # noqa: F401
from app.routes.spare_parts import api   # noqa: F401
