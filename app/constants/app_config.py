# app/constants/app_config.py
"""Програмын тохиргоо — хязгаарлалт, толеранс, HTTP кодууд, лаб төрлүүд."""

# Бортого (пикнометр) тогтмол - Хоосон тодорхойлолтын тохирц (грамм)
BOTTLE_TOLERANCE = 0.0015  # MNS GB/T 217: 3 хэмжилтийн max зөрүү ≤ 0.0015g

# Query хязгаарлалтууд
MAX_ANALYSIS_RESULTS = 200
MAX_SAMPLE_QUERY_LIMIT = 5000
MAX_IMPORT_BATCH_SIZE = 1000

# Дээжний жингийн хязгаарлалт (грамм)
MIN_SAMPLE_WEIGHT = 0.001
MAX_SAMPLE_WEIGHT = 10000

# Огноо/жил хязгаарлалт
MIN_VALID_YEAR = 2000
MAX_VALID_YEAR = 2100

# JSON/Audit хязгаарлалт
MAX_JSON_PAYLOAD_BYTES = 200_000
DEFAULT_AUDIT_LOG_LIMIT = 100

# Тайлбар урт хязгаарлалт
MAX_DESCRIPTION_LENGTH = 1000

# Мульти-лаборатори тогтмолууд
LAB_TYPES = {
    'coal': {'name': 'Нүүрсний лаборатори', 'icon': 'bi-fire', 'color': '#dc3545'},
    'petrography': {'name': 'Петрограф лаборатори', 'icon': 'bi-gem', 'color': '#6f42c1'},
    'water_chemistry': {'name': 'Усны хими лаборатори', 'icon': 'bi-droplet-half', 'color': '#0dcaf0'},
    'microbiology': {'name': 'Микробиологийн лаборатори', 'icon': 'bi-bug', 'color': '#20c997'},
}

# HTTP Status codes
HTTP_OK = 200
HTTP_MULTI_STATUS = 207
HTTP_BAD_REQUEST = 400
HTTP_UNAUTHORIZED = 401
HTTP_FORBIDDEN = 403
HTTP_NOT_FOUND = 404
HTTP_SERVER_ERROR = 500
