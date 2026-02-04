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
    'TDS': {
        'name': 'Total dissolved solids',
        'name_mn': 'Хуурай үлдэгдэл',
        'unit': 'mg/L',
        'mns_limit': (None, 1000),
    },
    'NH4': {
        'name': 'Ammonium',
        'name_mn': 'Аммонийн ион',
        'unit': 'mg/L',
        'mns_limit': (None, 0.5),
    },
    'NO2': {
        'name': 'Nitrite',
        'name_mn': 'Нитритийн ион',
        'unit': 'mg/L',
        'mns_limit': (None, 3.0),
    },
    'DS': {
        'name': 'Dissolved salts',
        'name_mn': 'Ууссан давс',
        'unit': 'mg/L',
        'mns_limit': None,
    },
    'F_W': {
        'name': 'Fluoride',
        'name_mn': 'Фторид',
        'unit': 'mg/L',
        'mns_limit': (None, 1.5),
    },
    'CL_FREE': {
        'name': 'Free residual chlorine',
        'name_mn': 'Чөлөөт үлдэгдэл хлор',
        'unit': 'mg/L',
        'mns_limit': (0.3, 0.5),
    },
    'PO4': {
        'name': 'Phosphate',
        'name_mn': 'Фосфат ион',
        'unit': 'mg/L',
        'mns_limit': None,
    },
    'DUST': {
        'name': 'Dust',
        'name_mn': 'Тоос',
        'unit': 'mg/m³',
        'mns_limit': None,
    },
    'SLUDGE': {
        'name': 'Sludge',
        'name_mn': 'Лаг',
        'unit': 'mg/L',
        'mns_limit': None,
    },
    'SLUDGE_VOL': {
        'name': 'Sludge Volume',
        'name_mn': 'Лагийн эзлэхүүн',
        'unit': 'мл',
        'mns_limit': (70, 80),
    },
    'SLUDGE_DOSE': {
        'name': 'Sludge Dose',
        'name_mn': 'Лагийн тун',
        'unit': 'г/л',
        'mns_limit': (2, 4),
    },
    'SLUDGE_INDEX': {
        'name': 'Sludge Index',
        'name_mn': 'Лагийн индекс',
        'unit': 'мл/г',
        'mns_limit': (80, 150),
    },
}

# Бүх усны шинжилгээний төрлүүд
WATER_ANALYSIS_TYPES = [
    # ─── Унд ахуйн (12) + Бохир ус (12) — олон категорид хамаарч болно ───
    {'code': 'HARD', 'name': 'Ерөнхий хатуулаг', 'order': 1, 'role': 'chemist', 'categories': ['drinking', 'wastewater']},
    {'code': 'TDS', 'name': 'Хуурай үлдэгдэл (Умбуур)', 'order': 2, 'role': 'chemist', 'categories': ['drinking', 'wastewater']},
    {'code': 'NH4', 'name': 'Аммонийн ион (NH₄⁺)', 'order': 3, 'role': 'chemist', 'categories': ['drinking', 'wastewater']},
    {'code': 'NO2', 'name': 'Нитритийн ион (NO₂⁻)', 'order': 4, 'role': 'chemist', 'categories': ['drinking', 'wastewater']},
    {'code': 'NO3', 'name': 'Нитратын ион (NO₃⁻)', 'order': 5, 'role': 'chemist', 'categories': ['drinking', 'wastewater']},
    {'code': 'FE_W', 'name': 'Төмрийн ион (Fe)', 'order': 6, 'role': 'chemist', 'categories': ['drinking', 'wastewater']},
    {'code': 'COLOR', 'name': 'Өнгө', 'order': 7, 'role': 'chemist', 'categories': ['drinking']},
    {'code': 'EC', 'name': 'ЦДЧ (EC)', 'order': 8, 'role': 'chemist', 'categories': ['drinking', 'wastewater']},
    {'code': 'DS', 'name': 'Ууссан давс', 'order': 9, 'role': 'chemist', 'categories': ['drinking', 'wastewater']},
    {'code': 'F_W', 'name': 'Фторид (F⁻)', 'order': 10, 'role': 'chemist', 'categories': ['drinking']},
    {'code': 'CL_FREE', 'name': 'Чөлөөт үлдэгдэл хлор', 'order': 11, 'role': 'chemist', 'categories': ['drinking', 'wastewater']},
    {'code': 'PH', 'name': 'Усны орчин (pH)', 'order': 12, 'role': 'chemist', 'categories': ['drinking', 'wastewater']},
    {'code': 'CL_W', 'name': 'Хлорид (Cl⁻)', 'order': 13, 'role': 'chemist', 'categories': ['wastewater']},
    {'code': 'PO4', 'name': 'Фосфат ион (PO₄³⁻)', 'order': 14, 'role': 'chemist', 'categories': ['wastewater']},
    {'code': 'BOD', 'name': 'БХХ5 (BOD5)', 'order': 15, 'role': 'chemist', 'categories': ['wastewater']},
    # ─── Лагийн шинжилгээ ───
    {'code': 'SLUDGE_VOL', 'name': 'Лагийн эзлэхүүн (SV)', 'order': 16, 'role': 'chemist', 'categories': ['wastewater']},
    {'code': 'SLUDGE_DOSE', 'name': 'Лагийн тун (SD)', 'order': 17, 'role': 'chemist', 'categories': ['wastewater']},
    {'code': 'SLUDGE_INDEX', 'name': 'Лагийн индекс (SI)', 'order': 18, 'role': 'chemist', 'categories': ['wastewater']},
    # ─── Бусад ───
    {'code': 'DUST', 'name': 'Тоос', 'order': 20, 'role': 'chemist', 'categories': ['other']},
    {'code': 'SLUDGE', 'name': 'Лаг', 'order': 21, 'role': 'chemist', 'categories': ['archive']},
    # ─── Архив (түр хадгалсан, ашиглахгүй байгаа) ───
    {'code': 'COD', 'name': 'ХХХ (COD)', 'order': 90, 'role': 'chemist', 'categories': ['archive']},
    {'code': 'DO_W', 'name': 'Ууссан хүчилтөрөгч (DO)', 'order': 91, 'role': 'chemist', 'categories': ['archive']},
    {'code': 'TSS', 'name': 'Нийт хатуу бодис (TSS)', 'order': 92, 'role': 'chemist', 'categories': ['archive']},
    {'code': 'TURB', 'name': 'Булингар (Turbidity)', 'order': 93, 'role': 'chemist', 'categories': ['archive']},
    {'code': 'TEMP', 'name': 'Температур', 'order': 94, 'role': 'chemist', 'categories': ['archive']},
    {'code': 'CA', 'name': 'Кальци (Ca)', 'order': 95, 'role': 'chemist', 'categories': ['archive']},
    {'code': 'MG', 'name': 'Магни (Mg)', 'order': 96, 'role': 'chemist', 'categories': ['archive']},
    {'code': 'ALK', 'name': 'Шүлтлэг (Alkalinity)', 'order': 97, 'role': 'chemist', 'categories': ['archive']},
    {'code': 'SO4', 'name': 'Сульфат (SO₄²⁻)', 'order': 98, 'role': 'chemist', 'categories': ['archive']},
    {'code': 'MN_W', 'name': 'Манган (Mn)', 'order': 99, 'role': 'chemist', 'categories': ['archive']},
    {'code': 'CU_W', 'name': 'Зэс (Cu)', 'order': 100, 'role': 'chemist', 'categories': ['archive']},
    {'code': 'ZN_W', 'name': 'Цайр (Zn)', 'order': 101, 'role': 'chemist', 'categories': ['archive']},
    {'code': 'PB_W', 'name': 'Хар тугалга (Pb)', 'order': 102, 'role': 'chemist', 'categories': ['archive']},
    {'code': 'AS_W', 'name': 'Хүнцэл (As)', 'order': 103, 'role': 'chemist', 'categories': ['archive']},
    {'code': 'CD_W', 'name': 'Кадми (Cd)', 'order': 104, 'role': 'chemist', 'categories': ['archive']},
    {'code': 'CR_W', 'name': 'Хром (Cr)', 'order': 105, 'role': 'chemist', 'categories': ['archive']},
    {'code': 'HG_W', 'name': 'Мөнгөн ус (Hg)', 'order': 106, 'role': 'chemist', 'categories': ['archive']},
    {'code': 'CN_W', 'name': 'Цианид (CN)', 'order': 107, 'role': 'chemist', 'categories': ['archive']},
]

# Бүх параметр нэгтгэл
ALL_WATER_PARAMS = {**PHYSICAL_PARAMS, **CHEMICAL_PARAMS}


# =====================================================================
# УСНЫ ДЭЭЖНИЙ НЭГЖ & ДЭЭЖНИЙ НЭРС (11 нэгж, 32 дээж)
# =====================================================================
WATER_UNITS = {
    'uutsb': {
        'name': 'УУЦБ',
        'short_name': 'УУЦБ',
        'icon': 'bi-gear-wide-connected',
        'color': '#06b6d4',
        'samples': [
            'УУЦБ-ийн боловсруулагдах ус',
            'УУЦБ-ийн 6м3/ц гаралтын ус',
            'УУЦБ-ийн 26м3/ц гаралтын ус',
            'УУЦБ-ийн нөөцийн савны ус',
        ],
    },
    'negdsen_office': {
        'name': 'Нэгдсэн оффис',
        'short_name': 'Нэгдсэн оффис',
        'icon': 'bi-building',
        'color': '#8b5cf6',
        'samples': [
            'Нэгдсэн оффис боловсруулагдах ус',
            'Нэгдсэн оффис цэвэршүүлсэн ус',
        ],
    },
    'tsagaan_khad': {
        'name': 'Цагаан хад',
        'short_name': 'TKH',
        'icon': 'bi-building',
        'color': '#6366f1',
        'samples': [
            'Цагаан хад боловсруулагдах ус',
            'Цагаан хад цэвэршүүлсэн ус',
        ],
    },
    'tsetsii': {
        'name': 'Цэций хороолол',
        'short_name': 'Цэций хороолол',
        'icon': 'bi-thermometer-half',
        'color': '#ef4444',
        'samples': [
            'Цэций хороолол хүйтэн ус',
        ],
    },
    'naymant': {
        'name': '"Наймант" гүний худаг',
        'short_name': 'Наймант',
        'icon': 'bi-arrow-down-circle',
        'color': '#0dcaf0',
        'samples': [
            '"Наймант" 1-р гүний худаг',
            '"Наймант" 2-р гүний худаг',
            '"Наймант" 3-р гүний худаг',
            '"Наймант" 4-р гүний худаг',
            '"Наймант" 5-р гүний худаг',
            '"Наймант" 6-р гүний худаг',
            '"Наймант" 7-р гүний худаг',
            '"Наймант" 9-р гүний худаг',
            '"Наймант" 11-р гүний худаг',
            '"Наймант" 13-р гүний худаг',
        ],
    },
    'naimdai': {
        'name': '"Наймдайн хөндий" гүний худаг',
        'short_name': 'Наймдай',
        'icon': 'bi-arrow-down-circle',
        'color': '#3b82f6',
        'samples': [
            '"Наймдайн хөндий" 4-р гүний худаг',
            '"Наймдайн хөндий" 5-р гүний худаг',
            '"Наймдайн хөндий" 7-р гүний худаг',
            '"Наймдайн хөндий" 9-р гүний худаг',
            '"Наймдайн хөндий" 10-р гүний худаг',
            '"Наймдайн хөндий" 11-р гүний худаг',
            '"Наймдайн хөндий" 12-р гүний худаг',
            '"Наймдайн хөндий" 13-р гүний худаг',
            '"Наймдайн хөндий" 14-р гүний худаг',
            '"Наймдайн хөндий" 15-р гүний худаг',
        ],
    },
    'malchdyn_hudag': {
        'name': 'Малчдын худаг',
        'short_name': 'Малчдын худаг',
        'icon': 'bi-droplet-half',
        'color': '#f59e0b',
        'samples': [
            'Малчдын худаг- Бунхан',
            'Малчдын худаг- Шангай',
            'Малчдын худаг- Баруун сайр',
            'Малчдын худаг- Хулгар',
            'Малчдын худаг- Зүүн сайр',
            'Малчдын худаг- Зүүн хирс',
            'Малчдын худаг- Баруун хирс',
            'Малчдын худаг- Цагаан эрэг',
            'Малчдын худаг- Шинэ ус',
            'Малчдын худаг- Шугам',
            'Малчдын худаг- Сүүжийн худаг',
            'Малчдын худаг- Таван толгой',
            'Малчдын худаг- Сондуул',
            'Малчдын худаг- Наймдайн худаг',
            'Малчдын худаг- Хулсан',
            'Малчдын худаг- Долоодой',
            'Малчдын худаг- Маахууз',
            'Малчдын худаг- Гучийн ус',
            'Малчдын худаг- Улаан худаг',
            'Малчдын худаг- Батчулуун',
            'Малчдын худаг- Хажуу ус',
            'Малчдын худаг- Хоолойн гучин',
            'Малчдын худаг- Адгийн ус',
        ],
    },
    'hyanalт': {
        'name': 'Хяналтын цооног',
        'short_name': 'Хяналтын цооног',
        'icon': 'bi-eyeglasses',
        'color': '#14b8a6',
        'samples': [
            'Хяналтын цооног-2',
            'Хяналтын цооног-3',
            'Хяналтын цооног-4',
            'Хяналтын цооног-5',
            'Хяналтын цооног-6',
        ],
    },
    'tsf': {
        'name': 'TSF',
        'short_name': 'TSF',
        'icon': 'bi-water',
        'color': '#ec4899',
        'samples': [
            'TSF-2',
            'TSF-3',
            'TSF-4',
            'TSF-5',
        ],
    },
    'uarp': {
        'name': 'UARP',
        'short_name': 'UARP',
        'icon': 'bi-house-gear',
        'color': '#10b981',
        'samples': [
            'UARP ундны усны гаралт',
            'UARP амрах байрны усны гаралт',
            'UARP худгийн усны гаралт',
            'UARP худаг гаралт',
            'UARP гал тогоо гаралт',
        ],
    },
    'shine_camp': {
        'name': 'Шинэ кэмп',
        'short_name': 'Шинэ кэмп',
        'icon': 'bi-house',
        'color': '#f97316',
        'samples': [
            'Шинэ кэмп, Түүхий ус',
            'Шинэ кэмп, Ундны усны гаралт',
        ],
    },
    'busad': {
        'name': 'Бусад',
        'short_name': 'Бусад',
        'icon': 'bi-three-dots',
        'color': '#64748b',
        'samples': [
            'Баруун наран гал тогооны ус',
            'НБҮ галын ус',
            'Дулааны цахилгаан станц',
            'Шатахуун түгээх станц',
            'Нүүрс баяжуулах үйлдвэр',
            'ХХУ-К-2',
            'Тэжээлийн ус К-2',
            'ХЦУБ',
            'Богвойн шанд',
            'Их бууц',
            'Эрдэнэ толгойн худаг',
            'Угтуул катеринг ХХХ-Кемпын амны ус',
            'Юу Эй Ар Пи ХХК-Уурхайн шинэ шоп худаг',
        ],
    },
    'dotood_air': {
        'name': 'Дотоод хяналт (Агаар)',
        'short_name': 'CM (Агаар)',
        'icon': 'bi-wind',
        'color': '#6366f1',
        'samples': [
            'Ламинар бокс / ариутгалын өмнө /',
            'Шинжилгээний өрөө / ариутгалын өмнө /',
            'Ламинар бокс / ариутгалын дараа /',
            'Шинжилгээний өрөө / ариутгалын дараа /',
            'Зейтца - 1',
            'Зейтца - 2',
            'Зейтца - 3',
        ],
        'auto_analyses': ['AIR_CFU', 'AIR_STAPH'],
    },
    'dotood_swab': {
        'name': 'Дотоод хяналт (Арчдас)',
        'short_name': 'CM (Арчдас)',
        'icon': 'bi-hand-index',
        'color': '#8b5cf6',
        'samples': [
            'Сорьцын шил',
            'Пипетканы хошуу',
            'Нэрмэл ус',
            'Петрийн аяга',
        ],
        'auto_analyses': ['SWAB_CFU', 'SWAB_ECOLI', 'SWAB_SALM'],
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
