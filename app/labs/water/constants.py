# app/labs/water/constants.py
"""Усны лабораторийн шинжилгээний параметрүүд."""

# Физик шинжилгээ
PHYSICAL_PARAMS = {
    'PH': {
        'name': 'pH',
        'name_mn': 'pH',
        'unit': '-',
        'mns_limit': (6.5, 8.5),
        'standard': 'MNS 4586:2007',
    },
    'EC': {
        'name': 'Electrical conductivity',
        'name_mn': 'Цахилгаан дамжуулалт',
        'unit': 'μS/cm',
        'mns_limit': (None, 1500),
        'standard': 'MNS 4586:2007',
    },
    'TURB': {
        'name': 'Turbidity',
        'name_mn': 'Булингар',
        'unit': 'NTU',
        'mns_limit': (None, 5),
        'standard': 'MNS 4586:2007',
    },
    'TSS': {
        'name': 'Total suspended solids',
        'name_mn': 'Нийт хатуу бодис',
        'unit': 'mg/L',
        'mns_limit': (None, 500),
        'standard': 'MNS 4586:2007',
    },
    'COLOR': {
        'name': 'Color',
        'name_mn': 'Өнгө',
        'unit': 'Pt-Co',
        'mns_limit': (None, 15),
        'standard': 'MNS 4586:2007',
    },
    'TEMP': {
        'name': 'Temperature',
        'name_mn': 'Температур',
        'unit': '°C',
        'mns_limit': None,
        'standard': '',
    },
}

# Хими шинжилгээ
CHEMICAL_PARAMS = {
    'CA': {
        'name': 'Calcium',
        'name_mn': 'Кальци',
        'unit': 'mg/L',
        'mns_limit': (None, 100),
    },
    'MG': {
        'name': 'Magnesium',
        'name_mn': 'Магни',
        'unit': 'mg/L',
        'mns_limit': (None, 30),
    },
    'HARD': {
        'name': 'Hardness',
        'name_mn': 'Хатуулаг',
        'unit': 'mg/L CaCO3',
        'mns_limit': (None, 300),
    },
    'ALK': {
        'name': 'Alkalinity',
        'name_mn': 'Шүлтлэг',
        'unit': 'mg/L',
        'mns_limit': None,
    },
    'CL_W': {
        'name': 'Chloride',
        'name_mn': 'Хлорид',
        'unit': 'mg/L',
        'mns_limit': (None, 350),
    },
    'SO4': {
        'name': 'Sulfate',
        'name_mn': 'Сульфат',
        'unit': 'mg/L',
        'mns_limit': (None, 500),
    },
    'NO3': {
        'name': 'Nitrate',
        'name_mn': 'Нитрат',
        'unit': 'mg/L',
        'mns_limit': (None, 50),
    },
    'FE_W': {
        'name': 'Iron',
        'name_mn': 'Төмөр',
        'unit': 'mg/L',
        'mns_limit': (None, 0.3),
    },
    'MN_W': {
        'name': 'Manganese',
        'name_mn': 'Манган',
        'unit': 'mg/L',
        'mns_limit': (None, 0.1),
    },
    'CU_W': {
        'name': 'Copper',
        'name_mn': 'Зэс',
        'unit': 'mg/L',
        'mns_limit': (None, 1.0),
    },
    'ZN_W': {
        'name': 'Zinc',
        'name_mn': 'Цайр',
        'unit': 'mg/L',
        'mns_limit': (None, 5.0),
    },
    'PB_W': {
        'name': 'Lead',
        'name_mn': 'Хар тугалга',
        'unit': 'mg/L',
        'mns_limit': (None, 0.01),
    },
    'AS_W': {
        'name': 'Arsenic',
        'name_mn': 'Хүнцэл',
        'unit': 'mg/L',
        'mns_limit': (None, 0.01),
    },
    'CD_W': {
        'name': 'Cadmium',
        'name_mn': 'Кадми',
        'unit': 'mg/L',
        'mns_limit': (None, 0.003),
    },
    'CR_W': {
        'name': 'Chromium',
        'name_mn': 'Хром',
        'unit': 'mg/L',
        'mns_limit': (None, 0.05),
    },
    'HG_W': {
        'name': 'Mercury',
        'name_mn': 'Мөнгөн ус',
        'unit': 'μg/L',
        'mns_limit': (None, 1.0),
    },
    'CN_W': {
        'name': 'Cyanide',
        'name_mn': 'Цианид',
        'unit': 'mg/L',
        'mns_limit': (None, 0.07),
    },
    'BOD': {
        'name': 'BOD5',
        'name_mn': 'БХХ5',
        'unit': 'mg/L',
        'mns_limit': None,
    },
    'COD': {
        'name': 'COD',
        'name_mn': 'ХХХ',
        'unit': 'mg/L',
        'mns_limit': None,
    },
    'DO_W': {
        'name': 'Dissolved oxygen',
        'name_mn': 'Ууссан хүчилтөрөгч',
        'unit': 'mg/L',
        'mns_limit': None,
    },
}

# Бүх усны шинжилгээний төрлүүд
WATER_ANALYSIS_TYPES = [
    {'code': 'PH', 'name': 'pH', 'order': 1, 'role': 'chemist'},
    {'code': 'EC', 'name': 'Цахилгаан дамжуулалт (EC)', 'order': 2, 'role': 'chemist'},
    {'code': 'TURB', 'name': 'Булингар (Turbidity)', 'order': 3, 'role': 'chemist'},
    {'code': 'TSS', 'name': 'Нийт хатуу бодис (TSS)', 'order': 4, 'role': 'chemist'},
    {'code': 'COLOR', 'name': 'Өнгө (Color)', 'order': 5, 'role': 'chemist'},
    {'code': 'TEMP', 'name': 'Температур', 'order': 6, 'role': 'chemist'},
    {'code': 'CA', 'name': 'Кальци (Ca)', 'order': 10, 'role': 'chemist'},
    {'code': 'MG', 'name': 'Магни (Mg)', 'order': 11, 'role': 'chemist'},
    {'code': 'HARD', 'name': 'Хатуулаг (Hardness)', 'order': 12, 'role': 'chemist'},
    {'code': 'ALK', 'name': 'Шүлтлэг (Alkalinity)', 'order': 13, 'role': 'chemist'},
    {'code': 'CL_W', 'name': 'Хлорид (Cl-)', 'order': 14, 'role': 'chemist'},
    {'code': 'SO4', 'name': 'Сульфат (SO4)', 'order': 15, 'role': 'chemist'},
    {'code': 'NO3', 'name': 'Нитрат (NO3)', 'order': 16, 'role': 'chemist'},
    {'code': 'FE_W', 'name': 'Төмөр (Fe)', 'order': 20, 'role': 'chemist'},
    {'code': 'MN_W', 'name': 'Манган (Mn)', 'order': 21, 'role': 'chemist'},
    {'code': 'CU_W', 'name': 'Зэс (Cu)', 'order': 22, 'role': 'chemist'},
    {'code': 'ZN_W', 'name': 'Цайр (Zn)', 'order': 23, 'role': 'chemist'},
    {'code': 'PB_W', 'name': 'Хар тугалга (Pb)', 'order': 24, 'role': 'chemist'},
    {'code': 'AS_W', 'name': 'Хүнцэл (As)', 'order': 25, 'role': 'chemist'},
    {'code': 'CD_W', 'name': 'Кадми (Cd)', 'order': 26, 'role': 'chemist'},
    {'code': 'CR_W', 'name': 'Хром (Cr)', 'order': 27, 'role': 'chemist'},
    {'code': 'HG_W', 'name': 'Мөнгөн ус (Hg)', 'order': 28, 'role': 'chemist'},
    {'code': 'CN_W', 'name': 'Цианид (CN)', 'order': 29, 'role': 'chemist'},
    {'code': 'BOD', 'name': 'БХХ5 (BOD5)', 'order': 30, 'role': 'chemist'},
    {'code': 'COD', 'name': 'ХХХ (COD)', 'order': 31, 'role': 'chemist'},
    {'code': 'DO_W', 'name': 'Ууссан хүчилтөрөгч (DO)', 'order': 32, 'role': 'chemist'},
]

# Бүх параметр нэгтгэл
ALL_WATER_PARAMS = {**PHYSICAL_PARAMS, **CHEMICAL_PARAMS}


# =====================================================================
# УСНЫ ДЭЭЖНИЙ НЭГЖ & ДЭЭЖНИЙ НЭРС (11 нэгж, 32 дээж)
# =====================================================================
WATER_UNITS = {
    'naimdain': {
        'name': 'Наймдайн',
        'icon': 'bi-arrow-down-circle',
        'color': '#0dcaf0',
        'samples': [
            'Наймдайн хөндийн малчдын гар худаг',
            'Наймантын хөндийн малчдын гар худаг',
            '"Наймант" гүний худаг',
            '"Наймдайн хөндий" гүний худаг',
        ],
    },
    'maiga': {
        'name': 'Майга',
        'icon': 'bi-water',
        'color': '#3b82f6',
        'samples': [
            '"Майга" уулын 500м3 усан сан',
            '"Майга" уулын 28000м3 усан сан',
        ],
    },
    'tsagaan_khad': {
        'name': 'Цагаан хад',
        'icon': 'bi-building',
        'color': '#6366f1',
        'samples': [
            'Цагаан хад /Боловсруулагдах ус/',
            'Цагаан хад /Цэвэршүүлсэн ус/',
            'Цагаан хад /Гал тогоо/',
            'Цагаан хад /Цооногийн ус/',
        ],
    },
    'sum': {
        'name': 'Сум',
        'icon': 'bi-house',
        'color': '#f59e0b',
        'samples': [
            'Сумын баруун худаг',
            'Сумын зүүн худаг',
        ],
    },
    'uurhaichin': {
        'name': 'Уурхайчин',
        'icon': 'bi-people',
        'color': '#10b981',
        'samples': [
            'Уурхайчин хотхон худаг -1',
            'Уурхайчин хотхон худаг -2',
            'Уурхайчин хотхон худаг -3',
        ],
    },
    'tsetsii': {
        'name': 'Цэций хороолол',
        'icon': 'bi-thermometer-half',
        'color': '#ef4444',
        'samples': [
            'Цэций хороолол халуун ус',
            'Цэций хороолол хүйтэн ус',
        ],
    },
    'gallerey': {
        'name': 'Галлерей',
        'icon': 'bi-cup-straw',
        'color': '#ec4899',
        'samples': [
            '"Галлерей" кемп хэрэглээний халуун ус',
            '"Галлерей" кемп хэрэглээний хүйтэн ус',
        ],
    },
    'negdsen_office': {
        'name': 'Нэгдсэн оффис',
        'icon': 'bi-building',
        'color': '#8b5cf6',
        'samples': [
            'Нэгдсэн оффис боловсруулагдах ус',
            'Нэгдсэн оффис цэвэршүүлсэн ус',
            'Нэгдсэн оффис 1-р тогоо',
            'Нэгдсэн оффис 2-р тогоо',
        ],
    },
    'uutsb': {
        'name': 'УУЦБ',
        'icon': 'bi-gear-wide-connected',
        'color': '#06b6d4',
        'samples': [
            'УУЦБ- боловсруулагдах ус',
            'УУЦБ- 6м3/ц т/т гаралтын ус',
            'УУЦБ- 26м3/ц т/т гаралтын ус',
            'УУЦБ нөөцийн сав',
        ],
    },
    'sbutsb': {
        'name': 'СБУЦБ',
        'icon': 'bi-recycle',
        'color': '#14b8a6',
        'samples': [
            'СБУЦБ оролт',
            'СБУЦБ гаралт',
            'СБУЦБ лаг',
        ],
    },
    'busad': {
        'name': 'Бусад',
        'icon': 'bi-three-dots',
        'color': '#64748b',
        'samples': [
            'Шинэ хаягдлын далангийн цооног',
            '2-р өргөлтийн насос станц',
        ],
    },
    'dotood_khyanalt': {
        'name': 'Дотоод хяналт',
        'icon': 'bi-shield-check',
        'color': '#20c997',
        'samples': [
            'Ламинар бокс / ариутгалын өмнө /',
            'Шинжилгээний өрөө / ариутгалын өмнө /',
            'Ламинар бокс / ариутгалын дараа /',
            'Шинжилгээний өрөө / ариутгалын дараа /',
            'Ламинар бокс / ариутгалын өмнө / (арчдас)',
            'Ламинар бокс / ариутгалын дараа / (арчдас)',
            'Зейтца - 1',
            'Зейтца - 2',
            'Зейтца - 3',
        ],
    },
}

# Бүх дээжний нэрсийн жагсаалт (flat)
ALL_WATER_SAMPLE_NAMES = []
for unit_data in WATER_UNITS.values():
    ALL_WATER_SAMPLE_NAMES.extend(unit_data['samples'])


def get_mns_standards() -> dict:
    """MNS/WHO стандартын хязгаарууд буцаах."""
    standards = {}
    for code, params in ALL_WATER_PARAMS.items():
        if params.get('mns_limit'):
            standards[code] = {
                'name': params['name_mn'],
                'unit': params['unit'],
                'limit': params['mns_limit'],
            }
    return standards
