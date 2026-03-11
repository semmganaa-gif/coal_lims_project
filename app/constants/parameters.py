"""Шинжилгээний параметрүүд — тодорхойлолт, алиас, mapping."""

PARAMETER_DEFINITIONS = {
    # --- Үндсэн чийгүүд (Түлхүүрүүд) ---
    'total_moisture': {
        'display_name': 'Нийт чийг',
        'lab_code': 'LAB.07.02',
        'standard_method': 'MNS ISO 589:2003',
        'aliases': ['Mt', 'MT', 'Total Moisture', 'Нийт чийг тодорхойлох', 'Mt,ar'],
        'type': 'measured',
        'is_basis_key': True
    },
    'inherent_moisture': {
        'display_name': 'Дотоод чийг',
        'lab_code': 'LAB.07.03',
        'standard_method': 'MNS GB/T 212:2015',
        'aliases': ['M,ad', 'Internal Moisture', 'Дотоод чийг тодорхойлох', 'Mad'],
        'type': 'measured',
        'is_basis_key': True
    },
    'free_moisture': {
        'display_name': 'Гадаргын чийг',
        'lab_code': 'LAB.07.02',
        'standard_method': 'MNS ISO 589:2003',
        'aliases': ['FM', 'Free Moisture', 'Гадаргын чийг'],
        'type': 'measured'
    },
    'solid': {
        'display_name': 'Хатуу үлдэгдэлийн агуулга',
        'lab_code': 'LAB.07.02',
        'standard_method': 'MNS ISO 589:2003',
        'aliases': ['solid', 'Solid', 'Хатуугийн агуулга'],
        'type': 'measured'
    },

    # --- Proximate Analysis (Түлшний шинжилгээ) ---
    'ash': {
        'display_name': 'Үнслэг (ad)',
        'lab_code': 'LAB.07.05',
        'standard_method': 'MNS GB/T 212:2015',
        'aliases': ['A,ad', 'Ad', 'Aad', 'Ash', 'Үнслэг тодорхойлох'],
        'type': 'measured',
        'conversion_bases': ['d', 'ar'],
        'is_basis_key': True
    },
    'volatile_matter': {
        'display_name': 'Дэгдэмхий бодис (ad)',
        'lab_code': 'LAB.07.04',
        'standard_method': 'MNS GB/T 212:2015',
        'aliases': ['V,ad', 'Vad', 'V', 'Volatile Matter', 'Дэгдэмхий бодисын гарц'],
        'type': 'measured',
        'conversion_bases': ['d', 'daf', 'ar']
    },

    # --- Ultimate Analysis (Элементийн шинжилгээ) ---
    'total_sulfur': {
        'display_name': 'Нийт хүхэр (ad)',
        'lab_code': 'LAB.07.08',
        'standard_method': 'MNS ISO 351:2001',
        'aliases': ['TS', 'St,ad', 'S', 'Total Sulfur', 'Нийт хүхэр тодорхойлох'],
        'type': 'measured',
        'conversion_bases': ['d', 'daf', 'ar']
    },
    'hydrogen': {
        'display_name': 'Устөрөгч (ad)',
        'lab_code': 'LAB.ULT.01',
        'standard_method': '...',
        'aliases': ['H', 'H,ad', 'Hydrogen'],
        'type': 'measured',
        'conversion_bases': ['d', 'daf', 'ar'],
        'is_basis_key': True
    },
    'phosphorus': {
        'display_name': 'Фосфор (ad)',
        'lab_code': 'LAB.07.09',
        'standard_method': 'MNS 7057-2024',
        'aliases': ['P', 'P,ad', 'Phosphorus', 'Фосфор тодорхойлох'],
        'type': 'measured',
        'conversion_bases': ['d', 'ar']
    },
    'total_chlorine': {
        'display_name': 'Нийт хлор (ad)',
        'lab_code': 'LAB.07.09',
        'standard_method': 'MNS 7057-2024',
        'aliases': ['Cl', 'Cl,ad', 'Chlorine', 'Нийт хлор тодорхойлох'],
        'type': 'measured',
        'conversion_bases': ['d', 'ar']
    },
    'total_fluorine': {
        'display_name': 'Нийт фтор (ad)',
        'lab_code': 'LAB.07.10',
        'standard_method': 'GB/T 4633-2014',
        'aliases': ['F', 'F,ad', 'Fluorine', 'Нийт фтор тодорхойлох'],
        'type': 'measured',
        'conversion_bases': ['d', 'ar']
    },

    # --- Бусад шинжилгээ (Хөрвөдөггүй) ---
    'free_swelling_index': {
        'display_name': 'Хөөлтийн зэрэг (CSN)',
        'lab_code': 'LAB.07.06',
        'standard_method': 'MNS ISO 501:2003',
        'aliases': ['CSN', 'Swelling Index', 'Хөөлтийн зэрэг тодорхойлох'],
        'type': 'measured'
    },
    'caking_power': {
        'display_name': 'Барьцалдах (бөсөх) чадвар (Gi)',
        'lab_code': 'LAB.07.07',
        'standard_method': 'MNS ISO 15585:2014',
        'aliases': ['Gi', 'Барьцалдах чадвар', 'Бөсөх чадвар'],
        'type': 'measured'
    },
    'relative_density': {
        'display_name': 'Харьцангуй нягт (TRD)',
        'lab_code': 'LAB.07.11',
        'standard_method': 'MNS GB/T 217:2015',
        'aliases': ['TRD', 'TRD,ad', 'Relative Density', 'Харьцангуй нягт тодорхойлох'],
        'type': 'measured'
    },
    'plastometer_x': {
        'display_name': 'Пластометр - Зузаан (X)',
        'lab_code': 'LAB.07.13',
        'standard_method': 'MNS GB/T 479:2015',
        'aliases': ['X', 'Plastometer X', 'Пластометр X', 'Пластометрийн үзүүлэлт X'],
        'type': 'measured'
    },
    'plastometer_y': {
        'display_name': 'Пластометр - Уян харимхай (Y)',
        'lab_code': 'LAB.07.13',
        'standard_method': 'MNS GB/T 479:2015',
        'aliases': ['Y', 'Plastometer Y', 'Пластометр Y', 'Пластометрийн үзүүлэлт Y'],
        'type': 'measured'
    },
    'coke_reactivity_index': {
        'display_name': 'Коксын идэвхжлийн индекс (CRI)',
        'lab_code': 'LAB.07.14',
        'standard_method': 'ISO 18894:2024',
        'aliases': ['CRI', 'Coke Reactivity Index', 'Коксын идэвхжил'],
        'type': 'measured'
    },
    'coke_strength_after_reaction': {
        'display_name': 'Коксын урвалын дараах бат бөх (CSR)',
        'lab_code': 'LAB.07.14',
        'standard_method': 'ISO 18894:2024',
        'aliases': ['CSR', 'Coke Strength', 'Коксын бат бөх'],
        'type': 'measured'
    },
    'mass': {
        'display_name': 'Дээжийн жин (Масс)',
        'lab_code': 'INPUT-M',
        'standard_method': 'N/A (As Weighed)',
        'aliases': ['m', 'mass', 'Масс', 'Жин', 'Sample Weight', 'As Received Mass'],
        'type': 'measured'
    },

    # --- Илчлэг (CV) ---
    'calorific_value': {
        'display_name': 'Илчлэгийн нийт утга (ad)',
        'lab_code': 'LAB.07.12',
        'standard_method': 'MNS ISO 1928:2009',
        'aliases': ['CV', 'Qgr,ad', 'Qgr', 'Calorific Value', 'Илчлэгийн нийт утга тодорхойлох'],
        'type': 'measured',
        'conversion_bases': ['d', 'daf', 'ar']
    },

    # --- ТООЦООЛЛЫН ПАРАМЕТРҮҮД (CALCULATED PARAMETERS) ---
    'fixed_carbon_ad': {
        'display_name': 'Тогтмол нүүрстөрөгч (ad)',
        'lab_code': 'CALC-FC',
        'standard_method': 'Calculated by difference',
        'aliases': ['FC', 'FC,ad', 'Fixed Carbon (ad)'],
        'type': 'calculated',
        'calculation_requires': ['ash', 'volatile_matter', 'inherent_moisture'],
        'conversion_bases': ['d', 'daf', 'ar']
    },
    'fixed_carbon_d': {'display_name': 'Тогтмол нүүрстөрөгч (d)', 'aliases': ['FC,d'], 'type': 'calculated'},
    'fixed_carbon_daf': {'display_name': 'Тогтмол нүүрстөрөгч (daf)', 'aliases': ['FC,daf'], 'type': 'calculated'},
    'fixed_carbon_ar': {'display_name': 'Тогтмол нүүрстөрөгч (ar)', 'aliases': ['FC,ar'], 'type': 'calculated'},

    'ash_d':   {'display_name': 'Үнслэг (d)',  'aliases': ['A,d', 'Ad (calc)'], 'type': 'calculated'},
    'ash_ar':  {'display_name': 'Үнслэг (ar)', 'aliases': ['A,ar'], 'type': 'calculated'},

    'volatile_matter_d':   {'display_name': 'Дэгдэмхий бодис (d)',   'aliases': ['V,d'],   'type': 'calculated'},
    'volatile_matter_daf': {'display_name': 'Дэгдэмхий бодис (daf)', 'aliases': ['V,daf'], 'type': 'calculated'},
    'volatile_matter_ar':  {'display_name': 'Дэгдэмхий бодис (ar)',  'aliases': ['V,ar'],  'type': 'calculated'},

    'calorific_value_d':   {'display_name': 'Илчлэг (d)',   'aliases': ['CV,d',   'Qgr,d'],   'type': 'calculated'},
    'calorific_value_daf': {'display_name': 'Илчлэг (daf)', 'aliases': ['CV,daf', 'Qgr,daf'], 'type': 'calculated'},
    'calorific_value_ar':  {'display_name': 'Илчлэг (ar)',  'aliases': ['CV,ar',  'Qgr,ar'],  'type': 'calculated'},
    'qnet_ar': {
        'display_name': 'Цэвэр илчлэг (ar)',
        'aliases': ['Qnet,ar'],
        'type': 'calculated',
        'calculation_requires': ['calorific_value_ar', 'hydrogen_ar', 'total_moisture']
    },

    'total_sulfur_d':   {'display_name': 'Нийт хүхэр (d)',   'aliases': ['S,d'],   'type': 'calculated'},
    'total_sulfur_daf': {'display_name': 'Нийт хүхэр (daf)', 'aliases': ['S,daf'], 'type': 'calculated'},
    'total_sulfur_ar':  {'display_name': 'Нийт хүхэр (ar)',  'aliases': ['S,ar'],  'type': 'calculated'},

    'hydrogen_d':   {'display_name': 'Устөрөгч (d)',   'aliases': ['H,d'],   'type': 'calculated'},
    'hydrogen_daf': {'display_name': 'Устөрөгч (daf)', 'aliases': ['H,daf'], 'type': 'calculated'},
    'hydrogen_ar':  {'display_name': 'Устөрөгч (ar)',  'aliases': ['H,ar'],  'type': 'calculated'},

    'phosphorus_d': {'display_name': 'Фосфор (d)', 'aliases': ['P,d'], 'type': 'calculated'},
    'phosphorus_ar':{'display_name': 'Фосфор (ar)', 'aliases': ['P,ar'], 'type': 'calculated'},

    'total_chlorine_d':  {'display_name': 'Нийт хлор (d)',  'aliases': ['Cl,d'],  'type': 'calculated'},
    'total_chlorine_ar': {'display_name': 'Нийт хлор (ar)', 'aliases': ['Cl,ar'], 'type': 'calculated'},

    'total_fluorine_d':  {'display_name': 'Нийт фтор (d)',  'aliases': ['F,d'],  'type': 'calculated'},
    'total_fluorine_ar': {'display_name': 'Нийт фтор (ar)', 'aliases': ['F,ar'], 'type': 'calculated'},

    'relative_density_d': {'display_name': 'Харьцангуй нягт (d)', 'aliases': ['TRD,d'], 'type': 'calculated'},
    'relative_density_ar':{'display_name': 'Харьцангуй нягт (ar)', 'aliases': ['TRD,ar'], 'type': 'calculated'},

    # --- WTL MG Analyses ---
    'mg_magnetic': {
        'display_name': 'MG Magnetic',
        'lab_code': 'LAB.MG.01',
        'standard_method': 'N/A',
        'aliases': ['MG', 'MG Magnetic', 'Magnetic Fraction'],
        'type': 'measured'
    },
}


# ---------------------------------------------------------------------
# PARAMETER_MAP ҮҮСГЭХ (Доорх код нь PARAMETER_DEFINITIONS-д суурилна)
# ---------------------------------------------------------------------
PARAMETER_MAP = {}


def _alias_key(s: str) -> str:
    if s is None:
        return ''
    s = str(s).strip()
    s = s.replace('،', ',').replace('﹐', ',').replace('，', ',')
    s = ' '.join(s.split())
    return s


def _norm_param_key(s: str) -> str:
    return _alias_key(s).casefold()


# 1. ANALYSIS BASE CODE MAP (Canonical -> Base)
CANONICAL_TO_BASE_ANALYSIS = {
    'total_moisture': 'MT',
    'inherent_moisture': 'Mad',
    'ash': 'Aad',
    'volatile_matter': 'Vad',
    'total_sulfur': 'TS',
    'phosphorus': 'P',
    'total_chlorine': 'Cl',
    'total_fluorine': 'F',
    'calorific_value': 'CV',
    'free_swelling_index': 'CSN',
    'caking_power': 'Gi',
    'relative_density': 'TRD',
    'plastometer_x': 'X',
    'plastometer_y': 'Y',
    'coke_reactivity_index': 'CRI',
    'coke_strength_after_reaction': 'CSR',
    'mass': 'm',
    'free_moisture': 'FM',
    'solid': 'SOLID',
    'mg_magnetic': 'MG',
}

# 2. ALIAS_TO_BASE_ANALYSIS (Alias -> Base)
ALIAS_TO_BASE_ANALYSIS = {}
for canonical, details in PARAMETER_DEFINITIONS.items():
    base = CANONICAL_TO_BASE_ANALYSIS.get(canonical)
    if not base:
        continue
    ALIAS_TO_BASE_ANALYSIS[canonical.lower()] = base
    for a in details.get('aliases', []):
        k = _alias_key(a)
        if not k:
            continue
        key_lc = k.lower()
        if key_lc in ALIAS_TO_BASE_ANALYSIS and ALIAS_TO_BASE_ANALYSIS[key_lc] != base:
            continue
        ALIAS_TO_BASE_ANALYSIS[key_lc] = base

_manual_pairs = {
    'mt,ar': 'MT', 'mad': 'Mad', 'aad': 'Aad', 'vad': 'Vad', 'st,ad': 'TS',
    'qgr,ad': 'CV', 'cv': 'CV', 'ts': 'TS', 'csn': 'CSN', 'gi': 'Gi',
    'trd': 'TRD', 'y': 'Y', 'x': 'X', 'fm': 'FM', 'solid': 'SOLID',
    'mg': 'MG', 'mg_size': 'MG_SIZE',
}
for k, v in _manual_pairs.items():
    ALIAS_TO_BASE_ANALYSIS[k] = v

for b in set(CANONICAL_TO_BASE_ANALYSIS.values()):
    ALIAS_TO_BASE_ANALYSIS[b.lower()] = b


# 3. PARAMETER_MAP (UI Alias -> Canonical)
for canonical_name, details in PARAMETER_DEFINITIONS.items():
    PARAMETER_MAP[_norm_param_key(canonical_name)] = canonical_name
    for alias in details.get('aliases', []):
        if not alias:
            continue
        key = _norm_param_key(alias)
        PARAMETER_MAP[key] = canonical_name


def param_key(name_or_alias: str) -> str | None:
    """UI-гаас ирсэн параметрийн нэрийг каноник түлхүүр болгон буцаана."""
    if not name_or_alias:
        return None
    return PARAMETER_MAP.get(_norm_param_key(name_or_alias))
