# app/labs/microbiology/constants.py
"""Микробиологийн лабораторийн шинжилгээний параметрүүд."""

# =====================================================================
# 1. УСНЫ МИКРОБИОЛОГИ (MNS 0900:2018)
# =====================================================================
WATER_MICRO_PARAMS = {
    'BBET': {
        'name': 'ББЕТ',
        'name_mn': 'Бүлэг бичил ерөнхий тоо',
        'unit': 'КОЕ/мл',
        'mns_limit': (None, 100),
        'standard': 'MNS 5668:2006',
        'mns_ref': 'MNS 0900:2018',
        'method': 'Pour plate',
        'formula': 'N=Σ/(n1+0.1*n2)*d',
        'sub_params': {
            'S1': {'name': 'Сорьц 1', 'name_mn': 'Сорьц 1'},
            'S2': {'name': 'Сорьц 2', 'name_mn': 'Сорьц 2'},
            'AVG': {'name': 'Дундаж', 'name_mn': 'Дундаж'},
        },
    },
    'ECOLI_W': {
        'name': 'E. coli',
        'name_mn': 'E. coli',
        'unit': 'КОЕ/100мл',
        'mns_limit': 'Илрэхгүй',
        'standard': 'MNS 5668:2006',
        'mns_ref': 'MNS 0900:2018',
        'method': 'Membrane filtration',
    },
    'GBET': {
        'name': 'ГБЭТ',
        'name_mn': 'Гэдэсний бүлэг эсийн тоо',
        'unit': 'КОЕ/100мл',
        'mns_limit': 'Илрэхгүй',
        'standard': 'MNS 5668:2006',
        'mns_ref': 'MNS 0900:2018',
        'method': 'Membrane filtration',
    },
    'GBET_THERMO': {
        'name': 'Халуунд тэсвэртэй ГБЭТ',
        'name_mn': 'Халуунд тэсвэртэй ГБЭТ',
        'unit': 'КОЕ/100мл',
        'mns_limit': 'Илрэхгүй',
        'standard': 'MNS 5668:2006',
        'mns_ref': 'MNS 0900:2018',
        'method': 'Membrane filtration',
    },
}

# Усны микробиологийн ажлын хуудасны баганууд
WATER_MICRO_COLUMNS = [
    'BBET',        # Сорьц1, Сорьц2, Дундаж
    'ECOLI_W',     # E.coli
    'GBET',        # ГБЭТ
    'GBET_THERMO', # Халуунд тэсвэртэй ГБЭТ
]

WATER_MICRO_SAMPLES = []  # Усны дээж бүртгэлээс ирнэ

# =====================================================================
# 2. АГААРЫН МИКРОБИОЛОГИ (MNS 5484:2005)
# =====================================================================
AIR_MICRO_PARAMS = {
    'CFU_A': {
        'name': 'Colony Forming Units (Air)',
        'name_mn': 'CFU (Агаар)',
        'unit': 'CFU/1м³',
        'mns_limit': (None, 50),
        'standard': 'MNS 5484:2005',
        'mns_ref': 'MNS 5484:2005',
        'method': 'Settle plate',
    },
    'STAPH_A': {
        'name': 'Staphylococcus spp. (Air)',
        'name_mn': 'Стафилококк (Агаар)',
        'unit': '',
        'mns_limit': 'Илрэхгүй',
        'standard': 'MNS 5484:2005',
        'mns_ref': 'MNS 5484:2005',
        'method': 'Settle plate',
        'result_type': 'presence',
    },
}

AIR_SAMPLE_NAMES = [
    'Ламинар бокс / ариутгалын өмнө /',
    'Шинжилгээний өрөө / ариутгалын өмнө /',
    'Ламинар бокс / ариутгалын дараа /',
    'Шинжилгээний өрөө / ариутгалын дараа /',
]

# =====================================================================
# 3. ГАДАРГУУГИЙН МИКРОБИОЛОГИ (MNS 6410:2018)
# =====================================================================
SURFACE_MICRO_PARAMS = {
    'CFU_S': {
        'name': 'Colony Forming Units (Surface)',
        'name_mn': 'CFU (Гадаргуу)',
        'unit': 'CFU/50см²',
        'mns_limit': (None, 100),
        'standard': 'MNS 6410:2018',
        'mns_ref': 'MNS 6410:2018',
        'method': 'Swab / Contact plate',
    },
    'ECOLI_S': {
        'name': 'E. coli (Surface)',
        'name_mn': 'E. coli (Гадаргуу)',
        'unit': '',
        'mns_limit': 'Илрэхгүй',
        'standard': 'MNS 6410:2018',
        'mns_ref': 'MNS 6410:2018',
        'method': 'Swab',
        'result_type': 'presence',
    },
    'SALM_S': {
        'name': 'Salmonella spp. (Surface)',
        'name_mn': 'Салмонелла (Гадаргуу)',
        'unit': '',
        'mns_limit': 'Илрэхгүй',
        'standard': 'MNS 6410:2018',
        'mns_ref': 'MNS 6410:2018',
        'method': 'Enrichment',
        'result_type': 'presence',
    },
}

SURFACE_SAMPLE_NAMES = [
    'Ламинар бокс / ариутгалын өмнө /',
    'Ламинар бокс / ариутгалын дараа /',
    'Зейтца - 1',
    'Зейтца - 2',
    'Зейтца - 3',
]

# =====================================================================
# НЭГТГЭЛ
# =====================================================================
ALL_MICRO_PARAMS = {**WATER_MICRO_PARAMS, **AIR_MICRO_PARAMS, **SURFACE_MICRO_PARAMS}

MICRO_ANALYSIS_TYPES = [
    # Усны микробиологи
    {'code': 'BBET', 'name': 'ББЕТ (Сорьц1/Сорьц2/Дундаж)', 'order': 1, 'role': 'chemist', 'category': 'water'},
    {'code': 'ECOLI_W', 'name': 'E. coli', 'order': 2, 'role': 'chemist', 'category': 'water'},
    {'code': 'GBET', 'name': 'ГБЭТ', 'order': 3, 'role': 'chemist', 'category': 'water'},
    {'code': 'GBET_THERMO', 'name': 'Халуунд тэсвэртэй ГБЭТ', 'order': 4, 'role': 'chemist', 'category': 'water'},
    # Агаарын микробиологи
    {'code': 'CFU_A', 'name': 'Агаарын CFU', 'order': 10, 'role': 'chemist', 'category': 'air'},
    {'code': 'STAPH_A', 'name': 'Staphylococcus spp.', 'order': 11, 'role': 'chemist', 'category': 'air'},
    # Гадаргуугийн микробиологи
    {'code': 'CFU_S', 'name': 'Гадаргуугийн CFU', 'order': 20, 'role': 'chemist', 'category': 'surface'},
    {'code': 'ECOLI_S', 'name': 'E. coli (Гадаргуу)', 'order': 21, 'role': 'chemist', 'category': 'surface'},
    {'code': 'SALM_S', 'name': 'Salmonella spp. (Гадаргуу)', 'order': 22, 'role': 'chemist', 'category': 'surface'},
]
