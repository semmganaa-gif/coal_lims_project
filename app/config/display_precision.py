# app/config/display_precision.py
"""
Шинжилгээний үр дүнгийн харуулах тоон орон (Display Precision)

Энэ файл нь шинжилгээ тус бүрийн үр дүнг хэдэн оронгийн нарийвчлалаар
харуулахыг тодорхойлно.

Жишээ:
    Aad (Үнс): 10.25% → 2 орон (0.01)
    P (Фосфор): 0.015% → 3 орон (0.001)
    CV (Дулаан): 25000 → 0 орон (бүхэл тоо)
"""

from typing import Dict, Optional
import logging

logger = logging.getLogger(__name__)


# ============================================================================
# ТООН ОРОНГИЙН ТОХИРГОО
# ============================================================================

DECIMAL_PLACES: Dict[str, int] = {
    # ========================================================================
    # НИЙТ ЧИЙГ (Total Moisture) - 1 орон
    # ========================================================================
    'MT': 1,            # Total moisture - 5.2%


    # ========================================================================
    # ЧИЙГ (Moisture) - 1 орон
    # ========================================================================
    'Mad': 2,           # Inherent moisture - 3.15%
    'M': 2,             # Moisture

    # ========================================================================
    # ҮНС (Ash) - 2 орон
    # ========================================================================
    'Aad': 2,           # Ash air-dried - 10.25%
    'A': 2,             # Ash - 10.25%
    'Ad': 2,            # Ash dry - 10.53%
    'Adaf': 2,          # Ash dry ash-free (should be 0)

    # ========================================================================
    # ДЭГДЭМХИЙ БОДИС (Volatile Matter) - 2 орон
    # ========================================================================
    'Vad': 2,           # Volatile matter air-dried - 30.25%
    'V': 2,             # Volatile matter - 30.25%
    'Vd': 2,            # Volatile matter dry - 31.58%
    'Vdaf': 2,          # Volatile matter dry ash-free - 35.29%

    # ========================================================================
    # ТОГТСОН НҮҮРСТӨРӨГЧ (Fixed Carbon) - 2 орон
    # ========================================================================
    'FC': 2,            # Fixed carbon - 55.00%
    'FC,ad': 2,         # Fixed carbon air-dried
    'FC,d': 2,          # Fixed carbon dry
    'FC,daf': 2,        # Fixed carbon dry ash-free

    # ========================================================================
    # ХҮХЭР (Sulfur) - 2 орон
    # ========================================================================
    'TS': 2,            # Total sulfur - 0.85%
    'St,ad': 2,         # Sulfur air-dried - 0.85%
    'St,d': 2,          # Sulfur dry - 0.89%
    'St,daf': 2,        # Sulfur dry ash-free - 1.05%
    'S': 2,             # Sulfur - 0.85%

    # ========================================================================
    # ЭЛЕМЕНТҮҮД (C, H, N, O) - 2 орон
    # ========================================================================
    'C': 2,             # Carbon - 75.50%
    'Cd': 2,            # Carbon dry
    'Cdaf': 2,          # Carbon dry ash-free

    'H': 2,             # Hydrogen - 5.25%
    'Hd': 2,            # Hydrogen dry
    'Hdaf': 2,          # Hydrogen dry ash-free

    'N': 2,             # Nitrogen - 1.50%
    'Nd': 2,            # Nitrogen dry
    'Ndaf': 2,          # Nitrogen dry ash-free

    'O': 2,             # Oxygen - 10.25%
    'Od': 2,            # Oxygen dry
    'Odaf': 2,          # Oxygen dry ash-free

    # ========================================================================
    # ХОРТОЙ ЭЛЕМЕНТҮҮД (Trace Elements) - 3 орон
    # ========================================================================
    'P': 3,             # Phosphorus - 0.015% → 3 орон
    'P,ad': 3,          # Phosphorus air-dried - 0.015%
    'P,d': 3,           # Phosphorus dry - 0.016%

    'F': 3,             # Fluorine - 0.025% → 3 орон
    'F,ad': 3,          # Fluorine air-dried - 0.025%
    'F,d': 3,           # Fluorine dry - 0.026%

    'Cl': 3,            # Chlorine - 0.035% → 3 орон
    'Cl,ad': 3,         # Chlorine air-dried - 0.035%
    'Cl,d': 3,          # Chlorine dry - 0.037%

    # ========================================================================
    # ИЛЧЛЭГ (Calorific Value) - 0 орон (бүхэл тоо)
    # ========================================================================
    'CV': 0,            # Calorific value - 25000 J/g (бүхэл)
    'Qgr,ad': 0,        # Gross calorific value air-dried - 25000
    'Qgr,d': 0,         # Gross calorific value dry - 26000
    'Qgr,daf': 0,       # Gross calorific value daf - 30000
    'Qgr,ar': 0,        # Gross calorific value as-received - 24500
    'Qnet,ar': 0,       # Net calorific value as-received - 24000

    # ========================================================================
    # КОКСЖИХ ИНДЕКСҮҮД (Caking Indices)
    # ========================================================================
    'CSN': 1,           # Crucible swelling number - 5.5 → 1 орон
    'Gi': 0,            # Gray-King index - 5 (бүхэл тоо)
    'Y': 0,             # Roga Y - 25 (бүхэл тоо)
    'X': 0,             # Roga X - 15 (бүхэл тоо)
    'CRI': 0,           # Coke Reactivity Index - 25 (бүхэл)
    'CSR': 0,           # Coke Strength after Reaction - 65 (бүхэл)

    # ========================================================================
    # ХАРЬЦАНГУЙ НЯГТ (True Relative Density) - 2 орон
    # ========================================================================
    'TRD': 2,           # Relative density - 1.45
    'TRD,ad': 2,        # TRD air-dried - 1.42
    'TRD,d': 2,         # TRD dry - 1.45

    # ========================================================================
    # ЧӨЛӨӨТ ЧИЙГ (Free Moisture) - 1 орон
    # ========================================================================
    'FM': 1,            # Free moisture - 8.5%

    # ========================================================================
    # ХАТУУГИЙН АГУУЛГА (Solid) - 1 орон
    # ========================================================================
    'Solid': 1,         # Solid residue - 85.5%

    }

# ============================================================================
# DEFAULT PRECISION
# ============================================================================
DEFAULT_DECIMAL_PLACES = 2


def get_decimal_places(analysis_code: str) -> int:
    """
    Анализын кодоор тоон оронг авах

    Args:
        analysis_code: Анализын код (жнь: "Aad", "P,ad", "CV")

    Returns:
        int: Тоон орон (0, 1, 2, 3, ...)

    Examples:
        >>> get_decimal_places("Aad")
        2
        >>> get_decimal_places("P")
        3
        >>> get_decimal_places("CV")
        0
        >>> get_decimal_places("UNKNOWN")
        2  # default
    """
    if not analysis_code:
        return DEFAULT_DECIMAL_PLACES

    # Exact match хайх
    code = analysis_code.strip()
    if code in DECIMAL_PLACES:
        return DECIMAL_PLACES[code]

    # Case-insensitive хайлт
    code_upper = code.upper()
    for key, value in DECIMAL_PLACES.items():
        if key.upper() == code_upper:
            return value

    # Base code-оор хайх (St,ad → St гэх мэт)
    if ',' in code:
        base_code = code.split(',')[0]
        if base_code in DECIMAL_PLACES:
            return DECIMAL_PLACES[base_code]

    # Default
    return DEFAULT_DECIMAL_PLACES


def format_result(value: float, analysis_code: Optional[str] = None) -> str:
    """
    Үр дүнг зөв тоон оронгоор харуулах

    Args:
        value: Үр дүнгийн утга
        analysis_code: Анализын код

    Returns:
        str: Formatted string

    Examples:
        >>> format_result(10.256, "Aad")
        '10.26'
        >>> format_result(0.0156, "P")
        '0.016'
        >>> format_result(25432.8, "CV")
        '25433'
        >>> format_result(5.5, "CSN")
        '5.5'
    """
    if value is None:
        return "-"

    try:
        decimal_places = get_decimal_places(analysis_code) if analysis_code else DEFAULT_DECIMAL_PLACES
        return f"{value:.{decimal_places}f}"
    except (ValueError, TypeError):
        return str(value)


# ============================================================================
# PRECISION GROUPS (хялбар удирдахад)
# ============================================================================

PRECISION_GROUPS = {
    '0_decimals': {
        'name': 'Бүхэл тоо (0 орон)',
        'codes': ['CV', 'Qgr,ad', 'Qgr,d', 'Qgr,daf', 'Qnet,ar',
                  'Gi', 'Y', 'X', 'CRI', 'CSR', 'TRD', 'TRD,ad', 'TRD,d'],
        'example': '25000',
    },
    '1_decimal': {
        'name': '1 орон',
        'codes': ['MT', 'CSN', 'FM', 'Solid'],
        'example': '5.5',
    },
    '2_decimals': {
        'name': '2 орон (стандарт)',
        'codes': ['Mad', 'Aad', 'Vad', 'TS', 'C', 'H', 'N', 'O', 'FC'],
        'example': '10.25',
    },
    '3_decimals': {
        'name': '3 орон (хортой элементүүд)',
        'codes': ['P', 'P,ad', 'P,d', 'F', 'F,ad', 'F,d', 'Cl', 'Cl,ad', 'Cl,d'],
        'example': '0.015',
    },
}


def get_precision_summary() -> dict:
    """
    Тоон оронгийн тохиргооны хураангуй

    Returns:
        dict: Summary information
    """
    summary = {
        'total_codes': len(DECIMAL_PLACES),
        'default_precision': DEFAULT_DECIMAL_PLACES,
        'groups': PRECISION_GROUPS,
        'by_precision': {},
    }

    # Group by precision
    for code, places in DECIMAL_PLACES.items():
        if places not in summary['by_precision']:
            summary['by_precision'][places] = []
        summary['by_precision'][places].append(code)

    return summary


# ============================================================================
# VALIDATION
# ============================================================================

def validate_precision_config():
    """
    Тохиргооны зөв байдлыг шалгах

    Raises:
        ValueError: Алдаа байвал
    """
    errors = []

    # Check for duplicates
    seen = set()
    for code in DECIMAL_PLACES.keys():
        code_upper = code.upper()
        if code_upper in seen:
            errors.append(f"Duplicate code: {code}")
        seen.add(code_upper)

    # Check valid decimal places (0-10)
    for code, places in DECIMAL_PLACES.items():
        if not isinstance(places, int):
            errors.append(f"{code}: decimal places must be integer")
        if places < 0 or places > 10:
            errors.append(f"{code}: decimal places must be 0-10")

    if errors:
        raise ValueError(f"Precision config errors: {'; '.join(errors)}")


# ============================================================================
# INITIALIZATION
# ============================================================================

# Validate configuration on import
try:
    validate_precision_config()
except ValueError as e:
    logger.warning(f"Precision configuration validation: {e}")
