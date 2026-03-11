# app/constants/analysis_types.py
"""Системийн үндсэн шинжилгээнүүд (Admin Seed)."""

MASTER_ANALYSIS_TYPES_LIST = [
    {'code': 'MT',    'name': 'Total Moisture',               'order': 1,  'role': 'chemist'},
    {'code': 'Mad',   'name': 'Moisture (air-dried)',         'order': 2,  'role': 'chemist'},
    {'code': 'Aad',   'name': 'Ash (air-dried)',              'order': 3,  'role': 'chemist'},
    {'code': 'Vad',   'name': 'Volatile Matter (air-dried)',  'order': 4,  'role': 'chemist'},
    {'code': 'TS',    'name': 'Total Sulfur',                 'order': 5,  'role': 'chemist'},
    {'code': 'CV',    'name': 'Calorific Value (gross)',       'order': 6,  'role': 'chemist'},
    {'code': 'CSN',   'name': 'Crucible Swelling Number',     'order': 7,  'role': 'chemist'},
    {'code': 'Gi',    'name': 'Caking Index',                 'order': 8,  'role': 'chemist'},
    {'code': 'TRD',   'name': 'True Relative Density',        'order': 9,  'role': 'chemist'},
    {'code': 'P',     'name': 'Phosphorus (air-dried)',       'order': 10, 'role': 'chemist'},
    {'code': 'F',     'name': 'Fluorine (air-dried)',         'order': 11, 'role': 'chemist'},
    {'code': 'Cl',    'name': 'Chlorine (air-dried)',         'order': 12, 'role': 'chemist'},
    {'code': 'X',     'name': 'Plastometric Shrinkage (X)',   'order': 13, 'role': 'chemist'},
    {'code': 'Y',     'name': 'Plastometric Thickness (Y)',   'order': 14, 'role': 'chemist'},
    {'code': 'CRI',   'name': 'Coke Reactivity Index',        'order': 15, 'role': 'chemist'},
    {'code': 'CSR',   'name': 'Coke Strength after Reaction', 'order': 16, 'role': 'chemist'},
    {'code': 'FM',    'name': 'Free Moisture',                'order': 17, 'role': 'prep'},
    {'code': 'Solid', 'name': 'Solid Residue',                'order': 18, 'role': 'prep'},
    {'code': 'm',     'name': 'Mass',                         'order': 19, 'role': 'chemist'},
    {'code': 'PE',    'name': 'Petrography',                  'order': 20, 'role': 'chemist'},
    {'code': 'MG',      'name': 'MG Magnetic',         'order': 200, 'role': 'chemist'},
    {'code': 'MG_SIZE', 'name': 'MG Size Distribution','order': 201, 'role': 'chemist'},
]
