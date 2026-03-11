"""Дээж үүсгэх тогтмолууд — CHPP тоног төхөөрөмж, WTL, ээлжийн тохиргоо."""

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
