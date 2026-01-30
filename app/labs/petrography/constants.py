# app/labs/petrography/constants.py
"""Петрограф лабораторийн шинжилгээний параметрүүд."""

# Нүүрсний петрограф
COAL_PETRO_PARAMS = {
    'MAC': {
        'name': 'Maceral analysis',
        'name_mn': 'Мацерал шинжилгээ (Vitrinite, Inertinite, Liptinite %)',
        'standard': 'ISO 7404-3',
        'unit': '%',
        'fields': ['vitrinite', 'inertinite', 'liptinite', 'mineral_matter'],
    },
    'VR': {
        'name': 'Vitrinite reflectance',
        'name_mn': 'Витринитийн ойлт (Ro%)',
        'standard': 'ISO 7404-5',
        'unit': '%',
        'fields': ['ro_mean', 'ro_min', 'ro_max', 'std_dev', 'count'],
    },
    'MM': {
        'name': 'Mineral matter',
        'name_mn': 'Эрдэс бодис (%)',
        'standard': 'Manual count',
        'unit': '%',
        'fields': ['mineral_matter_pct'],
    },
}

# Чулуулгийн петрограф
ROCK_PETRO_PARAMS = {
    'TS': {
        'name': 'Thin section',
        'name_mn': 'Нимгэн зүсэлт — Эрдэс тодорхойлолт',
        'standard': 'Optical microscopy',
        'unit': '',
        'fields': ['minerals_identified', 'description', 'image_path'],
    },
    'MOD': {
        'name': 'Modal analysis',
        'name_mn': 'Модал шинжилгээ (%)',
        'standard': 'Point count',
        'unit': '%',
        'fields': ['mineral_name', 'percentage'],
    },
    'TEX': {
        'name': 'Texture description',
        'name_mn': 'Бүтцийн тодорхойлолт',
        'standard': 'Visual',
        'unit': '',
        'fields': ['texture_type', 'grain_shape', 'description'],
    },
    'GS': {
        'name': 'Grain size distribution',
        'name_mn': 'Ширхэгийн хэмжээний тархалт',
        'standard': 'Micrometer',
        'unit': 'mm',
        'fields': ['size_fraction', 'percentage'],
    },
}

# Бүх петрограф шинжилгээний төрлүүд (AnalysisType seed-д ашиглана)
PETRO_ANALYSIS_TYPES = [
    {'code': 'MAC', 'name': 'Мацерал шинжилгээ (MAC)', 'order': 1, 'role': 'chemist'},
    {'code': 'VR', 'name': 'Витринитийн ойлт (VR)', 'order': 2, 'role': 'chemist'},
    {'code': 'MM', 'name': 'Эрдэс бодис (MM)', 'order': 3, 'role': 'chemist'},
    {'code': 'TS_PETRO', 'name': 'Нимгэн зүсэлт (TS)', 'order': 4, 'role': 'chemist'},
    {'code': 'MOD', 'name': 'Модал шинжилгээ (MOD)', 'order': 5, 'role': 'chemist'},
    {'code': 'TEX', 'name': 'Бүтцийн тодорхойлолт (TEX)', 'order': 6, 'role': 'chemist'},
    {'code': 'GS', 'name': 'Ширхэгийн хэмжээ (GS)', 'order': 7, 'role': 'chemist'},
]

# Бүх параметр нэгтгэл
ALL_PETRO_PARAMS = {**COAL_PETRO_PARAMS, **ROCK_PETRO_PARAMS}
