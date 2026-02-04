# app/labs/microbiology/constants.py
"""Микробиологийн лабораторийн шинжилгээний параметрүүд.

3 ажлын хуудас:
  1. WATER — Усны микробиологи (CFU, E.coli, Salmonella)
  2. AIR   — Агаарын микробиологи (CFU, Staphylococcus, Mold/Fungi)
  3. SURFACE — Гадаргуугийн микробиологи
"""

# =====================================================================
# МИКРОБИОЛОГИЙН ШИНЖИЛГЭЭНИЙ ПАРАМЕТРҮҮД
# =====================================================================
MICRO_PARAMS = {
    'CFU': {
        'name': 'CFU',
        'name_mn': 'Colony Forming Units',
        'unit': 'КОЕ/мл',
        'standard': 'MNS ISO 6222:1998',
        'method': 'Pour plate / Spread plate',
    },
    'ECOLI': {
        'name': 'E. coli',
        'name_mn': 'E. coli',
        'unit': 'КОЕ/100мл',
        'standard': 'MNS ISO 9308-1:1998',
        'method': 'Membrane filtration',
    },
    'SALM': {
        'name': 'Salmonella spp.',
        'name_mn': 'Салмонелла',
        'unit': '',
        'standard': 'MNS ISO 19250:2017',
        'method': 'Enrichment',
        'result_type': 'presence',
    },
}

# =====================================================================
# АЖЛЫН ХУУДАС БҮРИЙН FIELD ТОДОРХОЙЛОЛТ
# =====================================================================
MICRO_WATER_FIELDS = [
    'cfu_22', 'cfu_37', 'cfu_avg',
    'ecoli', 'salmonella',
    'start_date', 'end_date',
]

MICRO_AIR_FIELDS = [
    'cfu_air', 'staphylococcus', 'mold_fungi',
    'start_date', 'end_date',
]

MICRO_SWAB_FIELDS = [
    'cfu_swab', 'salmonella_swab', 'ecoli_swab', 'staphylococcus_swab',
    'start_date', 'end_date',
]

# =====================================================================
# ШИНЖИЛГЭЭНИЙ ТӨРЛҮҮД (micro_hub дээр харагдана)
# =====================================================================
MICRO_ANALYSIS_TYPES = [
    # Усны микробиологи
    {'code': 'CFU', 'name': 'CFU (Colony Forming Units)', 'order': 1, 'role': 'chemist'},
    {'code': 'ECOLI', 'name': 'E. coli', 'order': 2, 'role': 'chemist'},
    {'code': 'SALM', 'name': 'Salmonella spp.', 'order': 3, 'role': 'chemist'},
    # Агаарын микробиологи
    {'code': 'AIR_CFU', 'name': 'Агаарын CFU', 'order': 4, 'role': 'chemist'},
    {'code': 'AIR_STAPH', 'name': 'Staphylococcus (агаар)', 'order': 5, 'role': 'chemist'},
    # Арчдасны микробиологи
    {'code': 'SWAB_CFU', 'name': 'Арчдасны CFU', 'order': 6, 'role': 'chemist'},
    {'code': 'SWAB_ECOLI', 'name': 'E. coli (арчдас)', 'order': 7, 'role': 'chemist'},
    {'code': 'SWAB_SALM', 'name': 'Salmonella (арчдас)', 'order': 8, 'role': 'chemist'},
]

# Category → analyses_to_perform кодын mapping
CATEGORY_ANALYSIS_CODES = {
    'MICRO_WATER': ['CFU', 'ECOLI', 'SALM'],
    'MICRO_AIR': ['AIR_CFU', 'AIR_STAPH'],
    'MICRO_SWAB': ['SWAB_CFU', 'SWAB_ECOLI', 'SWAB_SALM'],
}

# =====================================================================
# Backward compatibility aliases
# =====================================================================
ALL_MICRO_PARAMS = MICRO_PARAMS

# Legacy exports
WATER_MICRO_PARAMS = MICRO_PARAMS
AIR_MICRO_PARAMS = {}
SURFACE_MICRO_PARAMS = {}
AIR_SAMPLE_NAMES = []
SURFACE_SAMPLE_NAMES = []
