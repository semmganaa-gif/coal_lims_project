# app/constants.py
# -*- coding: utf-8 -*-
"""
Системийн тогтмолууд ба тохиргоонууд.

Шинжилгээний параметрүүд, дээжний төрөл, нэрийн алиасууд,
ээлжийн тохиргоо зэрэг бүх тогтмол утгуудыг энд тодорхойлно.
"""
import sys

# Windows console utf-8 fix
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except (AttributeError, OSError) as e:
        # ✅ Тодорхой exception барих, алдааг нуухгүй
        import logging
        logging.warning(f"UTF-8 encoding тохируулга амжилтгүй: {e}")


# =====================================================================
# ХЭСЭГ 1: ШИНЖИЛГЭЭНИЙ ПАРАМЕТРҮҮД (PARAMETER DEFINITIONS)
# =====================================================================

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
}


# =====================================================================
# ХЭСЭГ 2: ДЭЭЖ ҮҮСГЭХ ТОГТМОЛУУД (CONSTANTS FOR SAMPLE GENERATION)
# =====================================================================

# 1. КЛИЕНТ БОЛОН ДЭЭЖИЙН ТӨРЛҮҮД
SAMPLE_TYPE_CHOICES_MAP = {
    'CHPP':    ['2 hourly', '4 hourly', '12 hourly', 'com'],
    'UHG-Geo': ['Stock', 'TR', 'GRD', 'TE', 'PE', 'CQ'],
    'BN-Geo':  ['Stock', 'TR', 'GRD', 'TE', 'PE', 'CQ'],
    'QC':      ['HCC', 'SSCC', 'MASHCC', 'TC', 'Fine', 'Test'],
    'Proc':    ['CHP', 'HCC', 'SSCC', 'MASHCC', 'Test'],
    'WTL':     ['WTL', 'Size', 'FL', 'MG', 'Test'],
    'LAB':     ['CM', 'GBW', 'Test'],
}

# UHG/BN товчлол
UNIT_ABBREVIATIONS = {
    'UHG-Geo': 'UHG',
    'BN-Geo': 'BN'
}
CHPP_2H_SAMPLES_ORDER = [
    # 1. Үндсэн тэжээлүүд
    'PF211',
    'PF221',
    'PF231',

    # 2. CC (Clean Coal / Баяжмал) - Эхэлж харагдана
    'UHG MV_HCC',
    'UHG HV_HCC',
    'UHG MASHCC',
    'BN HV HCC',
    'BN SSCC',
    'CC', # Fallback

    # 3. TC (Thermal Coal / Мидлинг) - Дараа нь харагдана
    'UHG MASHCC_2',
    'UHG Midd',
    'BN MASHCC_2',
    'BN Midd',
    'TC'  # Fallback
]

# 2. CHPP 12-HOURLY ДЭЭЖҮҮД
ALL_12H_SAMPLES = [
    {'name': 'SC401', 'mod': 'MOD I', 'condition': 'Чийгтэй'},
    {'name': 'SC402', 'mod': 'MOD I', 'condition': 'Чийгтэй'},
    {'name': 'SC403', 'mod': 'MOD I', 'condition': 'Чийгтэй'},
    {'name': 'SC405', 'mod': 'MOD I', 'condition': 'Чийгтэй'},
    {'name': 'SC406', 'mod': 'MOD I', 'condition': 'Чийгтэй'},
    {'name': 'SC501', 'mod': 'MOD I', 'condition': 'Чийгтэй'},
    {'name': 'SP502_F', 'mod': 'MOD I', 'condition': 'Шингэн'},
    {'name': 'SP502_Pro', 'mod': 'MOD I', 'condition': 'Шингэн'},
    {'name': 'SP502_Rej', 'mod': 'MOD I', 'condition': 'Шингэн'},
    {'name': 'DR601', 'mod': 'MOD I', 'condition': 'Шингэн'},
    {'name': 'FC601', 'mod': 'MOD I', 'condition': 'Шингэн'},
    {'name': 'FC602', 'mod': 'MOD I', 'condition': 'Шингэн'},
    {'name': 'FCU601', 'mod': 'MOD I', 'condition': 'Шингэн'},
    {'name': 'FCU602', 'mod': 'MOD I', 'condition': 'Шингэн'},
    {'name': 'SC421', 'mod': 'MOD II', 'condition': 'Чийгтэй'},
    {'name': 'SC422', 'mod': 'MOD II', 'condition': 'Чийгтэй'},
    {'name': 'SC423', 'mod': 'MOD II', 'condition': 'Чийгтэй'},
    {'name': 'SC425', 'mod': 'MOD II', 'condition': 'Чийгтэй'},
    {'name': 'SC426', 'mod': 'MOD II', 'condition': 'Чийгтэй'},
    {'name': 'SC521', 'mod': 'MOD II', 'condition': 'Чийгтэй'},
    {'name': 'DR621', 'mod': 'MOD II', 'condition': 'Шингэн'},
    {'name': 'TBS520_F', 'mod': 'MOD II', 'condition': 'Хуурай'},
    {'name': 'TBS521_Pro', 'mod': 'MOD II', 'condition': 'Хуурай'},
    {'name': 'TBS521_Rej', 'mod': 'MOD II', 'condition': 'Хуурай'},
    {'name': 'TBS522_Pro', 'mod': 'MOD II', 'condition': 'Хуурай'},
    {'name': 'TBS522_Rej', 'mod': 'MOD II', 'condition': 'Хуурай'},
    {'name': 'FC621', 'mod': 'MOD II', 'condition': 'Шингэн'},
    {'name': 'FC622', 'mod': 'MOD II', 'condition': 'Шингэн'},
    {'name': 'FCU621', 'mod': 'MOD II', 'condition': 'Шингэн'},
    {'name': 'FCU622', 'mod': 'MOD II', 'condition': 'Шингэн'},
    {'name': 'SC441', 'mod': 'MOD III', 'condition': 'Чийгтэй'},
    {'name': 'SC442', 'mod': 'MOD III', 'condition': 'Чийгтэй'},
    {'name': 'SC443', 'mod': 'MOD III', 'condition': 'Чийгтэй'},
    {'name': 'SC445', 'mod': 'MOD III', 'condition': 'Чийгтэй'},
    {'name': 'SC446', 'mod': 'MOD III', 'condition': 'Чийгтэй'},
    {'name': 'SC541', 'mod': 'MOD III', 'condition': 'Чийгтэй'},
    {'name': 'DR641', 'mod': 'MOD III', 'condition': 'Шингэн'},
    {'name': 'TBS540_F', 'mod': 'MOD III', 'condition': 'Хуурай'},
    {'name': 'TBS541_Pro', 'mod': 'MOD III', 'condition': 'Хуурай'},
    {'name': 'TBS541_Rej', 'mod': 'MOD III', 'condition': 'Хуурай'},
    {'name': 'TBS542_Pro', 'mod': 'MOD III', 'condition': 'Хуурай'},
    {'name': 'TBS542_Rej', 'mod': 'MOD III', 'condition': 'Хуурай'},
    {'name': 'TBS543_Pro', 'mod': 'MOD III', 'condition': 'Хуурай'},
    {'name': 'TBS543_Rej', 'mod': 'MOD III', 'condition': 'Хуурай'},
    {'name': 'FC641', 'mod': 'MOD III', 'condition': 'Шингэн'},
    {'name': 'FC642', 'mod': 'MOD III', 'condition': 'Шингэн'},
    {'name': 'FCU641', 'mod': 'MOD III', 'condition': 'Шингэн'},
    {'name': 'FCU642', 'mod': 'MOD III', 'condition': 'Шингэн'},
    {'name': 'TH701', 'mod': 'MOD I', 'condition': 'Шингэн'},
    {'name': 'TH721', 'mod': 'MOD II', 'condition': 'Шингэн'},
    {'name': 'TH741', 'mod': 'MOD III', 'condition': 'Шингэн'}
]

CONSTANT_12H_SAMPLES = [
    {'name': 'FiltP_A', 'condition': 'Чийгтэй'},
    {'name': 'FiltP_B', 'condition': 'Чийгтэй'},
    {'name': 'FiltP_C', 'condition': 'Чийгтэй'},
    {'name': 'FiltP_D', 'condition': 'Чийгтэй'},
    {'name': 'BeltP_dry', 'condition': 'Чийгтэй'},
    {'name': 'BeltP_solid', 'condition': 'Шингэн'}
]

# ==============================================================================
# 2a. CHPP ТОНОГ ТӨХӨӨРӨМЖИЙН ДЭЭЖ MAPPING (Screenshot 2026-01-05 дээр суурилсан)
# ==============================================================================
# Тоног төхөөрөмж -> Дээжний код mapping
# MOD I (4xx), MOD II (4xx+20), MOD III (4xx+40)
CHPP_EQUIPMENT_SAMPLES = {
    # ===================== DMC (Dense Medium Cyclone) - Хүнд орчны циклон =====================
    'primary_dmc_feed': {
        'name_mn': 'Анхдагч хүнд орчны циклоны тэжээл',
        'name_en': 'Primary DMC Feed',
        'samples': {
            'MOD I': ['SC401'],
            'MOD II': ['SC421'],
            'MOD III': ['SC441']
        },
        'condition': 'Чийгтэй',
        'stream_type': 'feed'
    },
    'primary_dmc_product': {
        'name_mn': 'Анхдагч хүнд орчны циклоны бүтээгдэхүүн',
        'name_en': 'Primary DMC Product (Clean Coal)',
        'samples': {
            'MOD I': ['SC402'],
            'MOD II': ['SC422'],
            'MOD III': ['SC442']
        },
        'condition': 'Чийгтэй',
        'stream_type': 'product'
    },
    'primary_dmc_reject': {
        'name_mn': 'Анхдагч хүнд орчны циклоны хаягдал',
        'name_en': 'Primary DMC Reject',
        'samples': {
            'MOD I': ['SC403'],
            'MOD II': ['SC423'],
            'MOD III': ['SC443']
        },
        'condition': 'Чийгтэй',
        'stream_type': 'reject'
    },
    'secondary_dmc_product': {
        'name_mn': 'Хоёрдогч хүнд орчны циклоны бүтээгдэхүүн',
        'name_en': 'Secondary DMC Product',
        'samples': {
            'MOD I': ['SC405'],
            'MOD II': ['SC425'],
            'MOD III': ['SC445']
        },
        'condition': 'Чийгтэй',
        'stream_type': 'product'
    },
    'secondary_dmc_reject': {
        'name_mn': 'Хоёрдогч хүнд орчны циклоны хаягдал',
        'name_en': 'Secondary DMC Reject',
        'samples': {
            'MOD I': ['SC406'],
            'MOD II': ['SC426'],
            'MOD III': ['SC446']
        },
        'condition': 'Чийгтэй',
        'stream_type': 'reject'
    },

    # ===================== Spiral Classifier - Мушгиа ангилуур =====================
    'spiral_reject': {
        'name_mn': 'Мушгиа ангилуурын хаягдал',
        'name_en': 'Spiral Classifier Reject',
        'samples': {
            'MOD I': ['SC501'],
            'MOD II': ['SC521'],
            'MOD III': ['SC541']
        },
        'condition': 'Чийгтэй',
        'stream_type': 'reject'
    },
    'spiral_product': {
        'name_mn': 'Мушгиа ангилуурын бүтээгдэхүүн',
        'name_en': 'Spiral Classifier Product',
        'samples': {
            'MOD I': ['CF501', 'CF502'],
            'MOD II': ['CF521', 'CF522'],
            'MOD III': ['CF541', 'CF542']
        },
        'condition': 'Шингэн',
        'stream_type': 'product'
    },
    'spiral_feed': {
        'name_mn': 'Мушгиа ангилуурын тэжээл',
        'name_en': 'Spiral Classifier Feed',
        'samples': {
            'MOD I': ['SP501', 'SP502_Feed', 'SP502_product', 'SP504_Feed', 'SP504_product'],
            'MOD II': ['SP521'],
            'MOD III': ['SP541']
        },
        'condition': 'Шингэн',
        'stream_type': 'feed'
    },

    # ===================== Flotation - Флотац =====================
    'flotation_feed': {
        'name_mn': 'Флотацын тэжээл',
        'name_en': 'Flotation Feed (Drain)',
        'samples': {
            'MOD I': ['DR601'],
            'MOD II': ['DR621'],
            'MOD III': ['DR641']
        },
        'condition': 'Шингэн',
        'stream_type': 'feed'
    },
    'flotation_product': {
        'name_mn': 'Флотацын бүтээгдэхүүн',
        'name_en': 'Flotation Concentrate',
        'samples': {
            'MOD I': ['FC601', 'FC602'],
            'MOD II': ['FC621', 'FC622'],
            'MOD III': ['FC641', 'FC642']
        },
        'condition': 'Шингэн',
        'stream_type': 'product'
    },
    'flotation_reject': {
        'name_mn': 'Флотацын хаягдал',
        'name_en': 'Flotation Tailings',
        'samples': {
            'MOD I': ['FCU601', 'FCU602'],
            'MOD II': ['FCU621', 'FCU622'],
            'MOD III': ['FCU641', 'FCU642']
        },
        'condition': 'Шингэн',
        'stream_type': 'reject'
    },

    # ===================== Centrifuge - Центрфуг =====================
    'centrifuge_product': {
        'name_mn': 'Центрфугийн бүтээгдэхүүн',
        'name_en': 'Centrifuge Product',
        'samples': {
            'MOD I': ['CF601', 'CF602'],
            'MOD II': ['CF621', 'CF622'],
            'MOD III': ['CF641', 'CF642']
        },
        'condition': 'Чийгтэй',
        'stream_type': 'product'
    },

    # ===================== TBS (Teeter Bed Separator) =====================
    'tbs': {
        'name_mn': 'TBS',
        'name_en': 'Teeter Bed Separator',
        'samples': {
            'MOD II': ['TBS521', 'TBS522'],
            'MOD III': ['TBS541', 'TBS542', 'TBS543']
        },
        'condition': 'Хуурай',
        'stream_type': 'separator'
    },

    # ===================== Thickener - Өтгөрүүлэгч =====================
    'thickener_underflow': {
        'name_mn': 'Өтгөрүүлэгчийн хаягдал',
        'name_en': 'Thickener Underflow',
        'samples': {
            'MOD I': ['TH701'],
            'MOD II': ['TH721'],
            'MOD III': ['TH741']
        },
        'condition': 'Шингэн',
        'stream_type': 'underflow'
    },

    # ===================== Dewatering - Усгүйжүүлэх =====================
    'dewatering': {
        'name_mn': 'Усгүйжүүлэх үйлдвэрийн дээж',
        'name_en': 'Dewatering (Belt Press / Filter Press)',
        'samples': {
            'ALL': ['Beltpress', 'Filterpress_A', 'Filterpress_B']
        },
        'condition': 'Чийгтэй',
        'stream_type': 'product'
    }
}

# Helper function: Get all sample codes for an equipment


def get_equipment_samples(equipment_key, mod=None):
    """
    Тоног төхөөрөмжийн дээжний кодуудыг авах.

    Args:
        equipment_key: CHPP_EQUIPMENT_SAMPLES-н түлхүүр
        mod: 'MOD I', 'MOD II', 'MOD III' эсвэл None (бүгд)

    Returns:
        Дээжний кодуудын жагсаалт
    """
    if equipment_key not in CHPP_EQUIPMENT_SAMPLES:
        return []

    samples = CHPP_EQUIPMENT_SAMPLES[equipment_key]['samples']
    if mod and mod in samples:
        return samples[mod]
    elif mod is None:
        all_samples = []
        for mod_samples in samples.values():
            all_samples.extend(mod_samples)
        return all_samples
    return []


# 2b. CHPP ШИНЖИЛГЭЭНИЙ ТОХИРГООНЫ БҮЛГҮҮД
# Энэ нь шинжилгээний тохиргоо хуудсанд CHPP дээжүүдийг бүлэглэхэд хэрэглэгдэнэ
CHPP_CONFIG_GROUPS = {
    '2 hourly': {
        'display': 'CHPP - 2 цаг',
        'samples': [
            # PF (Primary Feed)
            {'name': 'PF211', 'group': 'PF'},
            {'name': 'PF221', 'group': 'PF'},
            {'name': 'PF231', 'group': 'PF'},
            # CC (Clean Coal)
            {'name': 'UHG MV_HCC', 'group': 'CC'},
            {'name': 'UHG HV_HCC', 'group': 'CC'},
            {'name': 'UHG MASHCC', 'group': 'CC'},
            {'name': 'BN HV HCC', 'group': 'CC'},
            {'name': 'BN SSCC', 'group': 'CC'},
            # TC (Thermal Coal / Middlings)
            {'name': 'UHG MASHCC_2', 'group': 'TC'},
            {'name': 'UHG Midd', 'group': 'TC'},
            {'name': 'BN MASHCC_2', 'group': 'TC'},
            {'name': 'BN Midd', 'group': 'TC'},
        ]
    },
    '4 hourly': {
        'display': 'CHPP - 4 цаг',
        'samples': [
            {'name': 'CF501', 'group': 'MOD I'},
            {'name': 'CF502', 'group': 'MOD I'},
            {'name': 'CF601', 'group': 'MOD I'},
            {'name': 'CF602', 'group': 'MOD I'},
            {'name': 'CF521', 'group': 'MOD II'},
            {'name': 'CF522', 'group': 'MOD II'},
            {'name': 'CF621', 'group': 'MOD II'},
            {'name': 'CF622', 'group': 'MOD II'},
            {'name': 'CF541', 'group': 'MOD III'},
            {'name': 'CF542', 'group': 'MOD III'},
            {'name': 'CF641', 'group': 'MOD III'},
            {'name': 'CF642', 'group': 'MOD III'},
        ]
    },
    '12 hourly': {
        'display': 'CHPP - 12 цаг',
        'samples': [
            # SC (Screen) - Чийгтэй
            {'name': 'SC401', 'group': 'SC'},
            {'name': 'SC402', 'group': 'SC'},
            {'name': 'SC403', 'group': 'SC'},
            {'name': 'SC405', 'group': 'SC'},
            {'name': 'SC406', 'group': 'SC'},
            {'name': 'SC421', 'group': 'SC'},
            {'name': 'SC422', 'group': 'SC'},
            {'name': 'SC423', 'group': 'SC'},
            {'name': 'SC425', 'group': 'SC'},
            {'name': 'SC426', 'group': 'SC'},
            {'name': 'SC441', 'group': 'SC'},
            {'name': 'SC442', 'group': 'SC'},
            {'name': 'SC443', 'group': 'SC'},
            {'name': 'SC445', 'group': 'SC'},
            {'name': 'SC446', 'group': 'SC'},
            {'name': 'SC501', 'group': 'SC'},
            {'name': 'SC521', 'group': 'SC'},
            {'name': 'SC541', 'group': 'SC'},
            # SP (Spiral)
            {'name': 'SP502_F', 'group': 'SP'},
            {'name': 'SP502_Pro', 'group': 'SP'},
            {'name': 'SP502_Rej', 'group': 'SP'},
            # DR (Drain)
            {'name': 'DR601', 'group': 'DR'},
            {'name': 'DR621', 'group': 'DR'},
            {'name': 'DR641', 'group': 'DR'},
            # FC (Flotation Cell)
            {'name': 'FC601', 'group': 'FC'},
            {'name': 'FC602', 'group': 'FC'},
            {'name': 'FC621', 'group': 'FC'},
            {'name': 'FC622', 'group': 'FC'},
            {'name': 'FC641', 'group': 'FC'},
            {'name': 'FC642', 'group': 'FC'},
            # FCU (Flotation Cell Unit)
            {'name': 'FCU601', 'group': 'FCU'},
            {'name': 'FCU602', 'group': 'FCU'},
            {'name': 'FCU621', 'group': 'FCU'},
            {'name': 'FCU622', 'group': 'FCU'},
            {'name': 'FCU641', 'group': 'FCU'},
            {'name': 'FCU642', 'group': 'FCU'},
            # TBS
            {'name': 'TBS520_F', 'group': 'TBS'},
            {'name': 'TBS521_Pro', 'group': 'TBS'},
            {'name': 'TBS521_Rej', 'group': 'TBS'},
            {'name': 'TBS522_Pro', 'group': 'TBS'},
            {'name': 'TBS522_Rej', 'group': 'TBS'},
            {'name': 'TBS540_F', 'group': 'TBS'},
            {'name': 'TBS541_Pro', 'group': 'TBS'},
            {'name': 'TBS541_Rej', 'group': 'TBS'},
            {'name': 'TBS542_Pro', 'group': 'TBS'},
            {'name': 'TBS542_Rej', 'group': 'TBS'},
            {'name': 'TBS543_Pro', 'group': 'TBS'},
            {'name': 'TBS543_Rej', 'group': 'TBS'},
            # TH (Thickener)
            {'name': 'TH701', 'group': 'TH'},
            {'name': 'TH721', 'group': 'TH'},
            {'name': 'TH741', 'group': 'TH'},
            # FiltP (Filter Press)
            {'name': 'FiltP_A', 'group': 'FiltP'},
            {'name': 'FiltP_B', 'group': 'FiltP'},
            {'name': 'FiltP_C', 'group': 'FiltP'},
            {'name': 'FiltP_D', 'group': 'FiltP'},
            # BeltP (Belt Press)
            {'name': 'BeltP_dry', 'group': 'BeltP'},
            {'name': 'BeltP_solid', 'group': 'BeltP'},
        ]
    },
    'com': {
        'display': 'CHPP - COM (Нэгтгэл)',
        'samples': [
            # PF (Primary Feed) - composite
            {'name': 'PF211', 'group': 'PF'},
            {'name': 'PF221', 'group': 'PF'},
            {'name': 'PF231', 'group': 'PF'},
            # CC (Clean Coal) - composite
            {'name': 'UHG MV_HCC', 'group': 'CC'},
            {'name': 'UHG HV_HCC', 'group': 'CC'},
            {'name': 'UHG MASHCC', 'group': 'CC'},
            {'name': 'BN HV HCC', 'group': 'CC'},
            {'name': 'BN SSCC', 'group': 'CC'},
            # TC (Thermal Coal) - composite
            {'name': 'UHG MASHCC_2', 'group': 'TC'},
            {'name': 'UHG Midd', 'group': 'TC'},
            {'name': 'BN MASHCC_2', 'group': 'TC'},
            {'name': 'BN Midd', 'group': 'TC'},
        ]
    },
}

# Gi шинжилгээний ээлжийн тохиргоо
# PF211, PF231 → Сондгой ээлж (D1,D3,D5,N1,N3,N5)
# PF221 → Тэгш ээлж (D2,D4,D6,N2,N4,N6)
GI_SHIFT_CONFIG = {
    'odd_shifts': ['D1', 'D3', 'D5', 'N1', 'N3', 'N5'],  # Сондгой
    'even_shifts': ['D2', 'D4', 'D6', 'N2', 'N4', 'N6'],  # Тэгш
    'sample_mapping': {
        'PF211': 'odd_shifts',
        'PF231': 'odd_shifts',
        'PF221': 'even_shifts',
    }
}

# 3. COM (Composite) бүтээгдэхүүний Map
COM_PRIMARY_PRODUCTS = [
    'UHG MV_HCC',
    'UHG HV_HCC',
    'UHG MASHCC',
    'BN HV HCC',
    'BN SSCC'
]

COM_SECONDARY_MAP = {
    'UHG MV_HCC': ['UHG MASHCC_2', 'UHG Midd'],
    'UHG HV_HCC': ['none'],
    'UHG MASHCC': ['none'],
    'BN HV HCC':  ['BN MASHCC_2', 'BN Midd'],
    'BN SSCC':    ['BN MASHCC_2', 'BN Midd']
}

# 4. WTL ЖАГСААЛТУУД
WTL_SAMPLE_NAMES_19 = [
    'Dry_/+31.5', 'Dry_/+16.0', 'Dry_/+8.0', 'Dry_/+4.75', 'Dry_/+2.0', 'Dry_/+1.0', 'Dry_/-1.0',
    'Wet_/+31.5', 'Wet_/+16.0', 'Wet_/+8.0', 'Wet_/+4.75', 'Wet_/+2.0', 'Wet_/+1.0',
    'Wet_/+0.5', 'Wet_/+0.25', 'Wet_/+0.15', 'Wet_/+0.074', 'Wet_/+0.038', 'Wet_/-0.038',
]

WTL_SAMPLE_NAMES_70 = [
    '/+16.0/_F1.300', '/+16.0/_F1.325', '/+16.0/_F1.350', '/+16.0/_F1.375', '/+16.0/_F1.400',
    '/+16.0/_F1.425', '/+16.0/_F1.450', '/+16.0/_F1.50', '/+16.0/_F1.60', '/+16.0/_F1.70',
    '/+16.0/_F1.80', '/+16.0/_F2.0', '/+16.0/_F2.2', '/+16.0/_S2.2',
    '/+8.0/_F1.300', '/+8.0/_F1.325', '/+8.0/_F1.350', '/+8.0/_F1.375', '/+8.0/_F1.400',
    '/+8.0/_F1.425', '/+8.0/_F1.450', '/+8.0/_F1.50', '/+8.0/_F1.60', '/+8.0/_F1.70',
    '/+8.0/_F1.80', '/+8.0/_F2.0', '/+8.0/_F2.2', '/+8.0/_S2.2',
    '/+2.0/_F1.300', '/+2.0/_F1.325', '/+2.0/_F1.350', '/+2.0/_F1.375', '/+2.0/_F1.400',
    '/+2.0/_F1.425', '/+2.0/_F1.450', '/+2.0/_F1.50', '/+2.0/_F1.60', '/+2.0/_F1.70',
    '/+2.0/_F1.80', '/+2.0/_F2.0', '/+2.0/_F2.2', '/+2.0/_S2.2',
    '/+0.5/_F1.300', '/+0.5/_F1.325', '/+0.5/_F1.350', '/+0.5/_F1.375', '/+0.5/_F1.400',
    '/+0.5/_F1.425', '/+0.5/_F1.450', '/+0.5/_F1.50', '/+0.5/_F1.60', '/+0.5/_F1.70',
    '/+0.5/_F1.80', '/+0.5/_F2.0', '/+0.5/_F2.2', '/+0.5/_S2.2',
    '/+0.25/_F1.300', '/+0.25/_F1.325', '/+0.25/_F1.350', '/+0.25/_F1.375', '/+0.25/_F1.400',
    '/+0.25/_F1.425', '/+0.25/_F1.450', '/+0.25/_F1.50', '/+0.25/_F1.60', '/+0.25/_F1.70',
    '/+0.25/_F1.80', '/+0.25/_F2.0', '/+0.25/_F2.2', '/+0.25/_S2.2'
]

WTL_SAMPLE_NAMES_6 = ['C1', 'C2', 'C3', 'C4', 'T1', 'T2']
WTL_SAMPLE_NAMES_2 = ['Initial', 'Comp']

WTL_SIZE_NAMES = [
    '/+31.5', '/+16.0', '/+8.0', '/+4.75', '/+2.0', '/+1.0',
    '/+0.5', '/+0.25', '/+0.15', '/+0.074', '/+0.038', '/-0.038', 'Initial'
]

WTL_FL_NAMES = ['C1', 'C2', 'C3', 'C4', 'T1', 'T2', 'Initial']


# =====================================================================
# 5. СИСТЕМИЙН ҮНДСЭН ШИНЖИЛГЭЭНҮҮД (Admin Seed)
# =====================================================================
MASTER_ANALYSIS_TYPES_LIST = [
    {'code': 'MT',    'name': 'Нийт чийг (MT)',               'order': 1,  'role': 'chemist'},
    {'code': 'Mad',   'name': 'Дотоод чийг (Mad)',            'order': 2,  'role': 'chemist'},
    {'code': 'Aad',   'name': 'Үнс (Aad)',                    'order': 3,  'role': 'chemist'},
    {'code': 'Vad',   'name': 'Дэгдэмхий бодис (Vad)',        'order': 4,  'role': 'chemist'},
    {'code': 'TS',    'name': 'Нийт хүхэр (TS)',              'order': 5,  'role': 'chemist'},
    {'code': 'CV',    'name': 'Илчлэг (CV)',                  'order': 6,  'role': 'chemist'},
    {'code': 'CSN',   'name': 'Хөөлтийн зэрэг (CSN)',         'order': 7,  'role': 'chemist'},
    {'code': 'Gi',    'name': 'Барьцалдах чадвар (Gi)',       'order': 8,  'role': 'chemist'},
    {'code': 'TRD',   'name': 'Харьцангуй нягт (TRD)',        'order': 9,  'role': 'chemist'},
    {'code': 'P',     'name': 'Фосфор (P)',                   'order': 10, 'role': 'chemist'},
    {'code': 'F',     'name': 'Фтор (F)',                     'order': 11, 'role': 'chemist'},
    {'code': 'Cl',    'name': 'Хлор (Cl)',                    'order': 12, 'role': 'chemist'},
    {'code': 'X',     'name': 'Пластометр (X)',               'order': 13, 'role': 'chemist'},
    {'code': 'Y',     'name': 'Пластометр (Y)',               'order': 14, 'role': 'chemist'},
    {'code': 'CRI',   'name': 'Коксын урвалын идэвх (CRI)',   'order': 15, 'role': 'chemist'},
    {'code': 'CSR',   'name': 'Урвалын дараах бат бэх (CSR)', 'order': 16, 'role': 'chemist'},
    {'code': 'FM',    'name': 'Чөлөөт чийг (FM)',             'order': 17, 'role': 'prep'},
    {'code': 'Solid', 'name': 'Хатуу бодисын үлдэгдэл (Solid)', 'order': 18, 'role': 'prep'},
    {'code': 'm',     'name': 'Масс (m)',                     'order': 19, 'role': 'chemist'},
    {'code': 'PE',    'name': 'Петрограф (PE)',               'order': 20, 'role': 'chemist'},
]


# =====================================================================
# 6. KPI / ERROR REASONS
# =====================================================================
ERROR_REASON_KEYS = [
    "sample_prep",
    "measurement",
    "qc_fail",
    "equipment",
    "data_entry",
    "method",
    "sample_mixup",
    "customer_complaint",
]

ERROR_REASON_LABELS = {
    "sample_prep":          "1. Дээж бэлтгэлийн алдаа (Бутлалт/Хуваалт)",
    "measurement":          "2. Шинжилгээний гүйцэтгэлийн алдаа",
    "qc_fail":              "3. QC / Стандарт дээжийн зөрүү",
    "equipment":            "4. Тоног төхөөрөмж / Орчны нөхцөл",
    "data_entry":           "5. Өгөгдөл шивэлт / Тооцооллын алдаа",
    "method":               "6. Арга аргачлал зөрчсөн (SOP)",
    "sample_mixup":         "7. Дээж солигдсон / Буруу дээж",
    "customer_complaint":   "8. Санал гомдол / Хяналтын шинжилгээ",
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

# =============================================================================
# Name/Class QC Master Specs
# =============================================================================


# 🛑 ШИНЭ: Name/Class QC-ийн "мастер" spec хүснэгт.
# Мөр бүрийг нэг түлхүүрээр хадгална (чи хүсвэл нэрийг өөрчилж болно).
NAME_CLASS_MASTER_SPECS = {
    "UHG MV_HCC": {
        "Mad": 0.80,
        "Aad": 10.70,
        "Vdaf": 27.00,
        "Qnet,ar": None,
        "CSN": None,
        "Gi": 80.0,
    },
    "UHG HV_HCC": {
        "Mad": 1.00,
        "Aad": 11.00,
        "Vdaf": 30.00,
        "Qnet,ar": None,
        "CSN": None,
        "Gi": 87.0,
    },
    "UHG MASHCC": {
        "Mad": 0.50,
        "Aad": 25.00,
        "Vdaf": 15.00,
        "Qnet,ar": None,
        "CSN": None,
        "Gi": 22.0,
    },
    "BN HV HCC": {
        "Mad": 1.20,
        "Aad": 12.00,
        "Vdaf": 32.00,
        "Qnet,ar": None,
        "CSN": None,
        "Gi": 90.0,
    },
    "BN SSCC": {
        "Mad": 1.50,
        "Aad": 9.00,
        "Vdaf": 27.00,
        "Qnet,ar": None,
        "CSN": None,
        "Gi": 88.0,
    },
    "UHG MASHCC_2": {
        "Mad": 0.60,
        "Aad": 25.00,
        "Vdaf": 35.00,
        "Qnet,ar": None,
        "CSN": None,
        "Gi": 18.0,
    },
    "UHG Midd": {
        "Mad": 0.50,
        "Aad": 30.00,
        "Vdaf": 22.00,
        "Qnet,ar": None,
        "CSN": None,
        "Gi": 10.0,
    },
    "BN MASHCC_2": {
        "Mad": 0.70,
        "Aad": 25.00,
        "Vdaf": 30.00,
        "Qnet,ar": None,
        "CSN": None,
        "Gi": 25.0,
    },
    "BN Midd": {
        "Mad": 0.50,
        "Aad": 30.00,
        "Vdaf": 22.00,
        "Qnet,ar": None,
        "CSN": None,
        "Gi": 10.0,
    },
}

# 🛑 ШИНЭ: эдгээр "зорилтот" утган дээр хэдэн хангалтын зурвас (± band) авах вэ.
# Жишээ болгож тавьлаа – лабораторийн бодит шаардлагаараа өөрчилж болно.
# QC_PARAM_CODES = ["Mad", "Aad", "Vdaf", "Qnet,ar", "CSN", "Gi"] -тай тохирсон
NAME_CLASS_SPEC_BANDS = {
    "Mad": 0.2,        # ±0.2
    "Aad": 2.0,        # ±2.0
    "Vdaf": 3.0,       # ±3.0
    "Qnet,ar": 200.0,  # ±200 кЖ/кг
    "CSN": 1.0,        # ±1.0
    "Gi": 5.0,         # ±5
}

# =====================================================================
# ХЭСЭГ 10: SUMMARY VIEW COLUMNS (Хураангуй харуулах баганууд)
# =====================================================================
# ✅ Давхардлыг арилгасан - analysis_routes.py ба api_routes.py-аас энд шилжүүлсэн
SUMMARY_VIEW_COLUMNS = [
    {"code": "MT", "canonical_base": "total_moisture"},
    {"code": "Mad", "canonical_base": "inherent_moisture"},
    {"code": "Aad", "canonical_base": "ash"},
    {"code": "Ad", "canonical_base": "ash"},
    {"code": "Vad", "canonical_base": "volatile_matter"},
    {"code": "Vdaf", "canonical_base": "volatile_matter"},
    {"code": "FC,ad", "canonical_base": "fixed_carbon_ad"},
    {"code": "St,ad", "canonical_base": "total_sulfur"},
    {"code": "St,d", "canonical_base": "total_sulfur"},
    {"code": "Qgr,ad", "canonical_base": "calorific_value"},
    {"code": "Qgr,ar", "canonical_base": "calorific_value"},
    {"code": "Qnet,ar", "canonical_base": "calorific_value"},
    {"code": "CSN", "canonical_base": "free_swelling_index"},
    {"code": "Gi", "canonical_base": "caking_power"},
    {"code": "TRD,ad", "canonical_base": "relative_density"},
    {"code": "TRD,d", "canonical_base": "relative_density"},
    {"code": "P,ad", "canonical_base": "phosphorus"},
    {"code": "P,d", "canonical_base": "phosphorus"},
    {"code": "Solid", "canonical_base": "solid"},
    {"code": "FM", "canonical_base": "free_moisture"},
    {"code": "F,ad", "canonical_base": "total_fluorine"},
    {"code": "F,d", "canonical_base": "total_fluorine"},
    {"code": "Cl,ad", "canonical_base": "total_chlorine"},
    {"code": "Cl,d", "canonical_base": "total_chlorine"},
    {"code": "X", "canonical_base": "plastometer_x"},
    {"code": "Y", "canonical_base": "plastometer_y"},
    {"code": "CRI", "canonical_base": "coke_reactivity_index"},
    {"code": "CSR", "canonical_base": "coke_strength_after_reaction"},
    {"code": "m", "canonical_base": "mass"},
]


# =====================================================================
# ХЭСЭГ: ПРОГРАМЫН ТОХИРГОО (APPLICATION CONFIGURATION)
# =====================================================================

# Хуруу бөмбөлгийн тогтмол - Хоосон жингийн тохирц (грамм)
BOTTLE_TOLERANCE = 0.0015  # MNS стандарт: max зөрүү ≤ 0.0015g

# Query хязгаарлалтууд
MAX_ANALYSIS_RESULTS = 200  # Шинжилгээний үр дүнгийн хамгийн их тоо
MAX_SAMPLE_QUERY_LIMIT = 5000  # Дээжний query-н хамгийн их тоо
MAX_IMPORT_BATCH_SIZE = 1000  # Import хийх дээжний хамгийн их тоо

# Дээжний жингийн хязгаарлалт (грамм)
MIN_SAMPLE_WEIGHT = 0.001  # Хамгийн бага жин
MAX_SAMPLE_WEIGHT = 10000  # Хамгийн их жин (10кг)

# Огноо/жил хязгаарлалт
MIN_VALID_YEAR = 2000  # Хамгийн бага жил
MAX_VALID_YEAR = 2100  # Хамгийн их жил

# JSON/Audit хязгаарлалт
MAX_JSON_PAYLOAD_BYTES = 200_000  # JSON payload-н хамгийн их хэмжээ
DEFAULT_AUDIT_LOG_LIMIT = 100  # Audit log-н default limit

# Тайлбар урт хязгаарлалт
MAX_DESCRIPTION_LENGTH = 1000  # Тайлбар/comment-н хамгийн их урт

# =====================================================================
# МУЛЬТИ-ЛАБОРАТОРИ ТОГТМОЛУУД
# =====================================================================
LAB_TYPES = {
    'coal': {'name': 'Нүүрсний лаборатори', 'icon': 'bi-fire', 'color': '#dc3545'},
    'petrography': {'name': 'Петрограф лаборатори', 'icon': 'bi-gem', 'color': '#6f42c1'},
    'water': {'name': 'Усны лаборатори', 'icon': 'bi-droplet', 'color': '#0dcaf0'},
    'microbiology': {'name': 'Микробиологийн лаборатори', 'icon': 'bi-bug', 'color': '#20c997'},
}

# HTTP Status codes
HTTP_OK = 200
HTTP_MULTI_STATUS = 207  # Partial success
HTTP_BAD_REQUEST = 400
HTTP_UNAUTHORIZED = 401
HTTP_FORBIDDEN = 403
HTTP_NOT_FOUND = 404
HTTP_SERVER_ERROR = 500
