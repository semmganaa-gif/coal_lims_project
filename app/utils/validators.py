# app/utils/validators.py
"""
Input validation utilities

Энэ модуль нь хэрэглэгчийн оруулж буй өгөгдлийг баталгаажуулдаг.
Аюулгүй байдлын хувьд маш чухал - SQL injection, XSS, буруу төрлийн
өгөгдөл зэргээс хамгаална.
"""

from typing import Any, Tuple, Optional, Dict
import re


# ============================================================================
# ШИНЖИЛГЭЭНИЙ ҮР ДҮНГИЙН VALIDATION
# ============================================================================

# Анализ тус бүрийн зөвшөөрөгдөх утгын мужууд
ANALYSIS_VALUE_RANGES: Dict[str, Tuple[float, float]] = {
    # Чийг (Moisture)
    'MT': (0.5, 40.0),          # Total moisture 0.5-40%
    'Mad': (0.2, 30.0),         # Inherent moisture 0.5-30%

    # Үнс (Ash)
    'Aad': (0.1, 99.0),         # Ash air-dried 0.1-99.0%
    'A': (0.1, 99.0),           # Ash 0.1-99.0%

    # Дэгдэмхий бодис (Volatile matter)
    'Vad': (0.1, 90.0),         # Volatile matter 0.1-90.0%
    'V': (0.1, 90.0),           # Volatile matter 0.1-90.0%
    'Vdaf': (0.1, 99.0),        # VM dry ash-free 0.1-99.0%

    # Хүхэр (Sulfur)
    'TS': (0.0, 40.0),          # Total sulfur 0-40%
    'St,ad': (0.0, 40.0),       # Sulfur air-dried 0-40%
    'St,d': (0.0, 40.0),        # Sulfur dry 0-40%

    # Дулааны үнэлгээ (Calorific value)
    'CV': (500, 40000),        # Calorific value 500-40000 J/g
    'Qgr,ad': (500, 40000),    # Gross calorific value
    'Qgr,d': (500, 40000),
    'Qgr,daf': (500, 40000),
    'Qnet,ar': (3000, 40000),   # Net calorific value

    # Бусад элементүүд
    'C': (0.0, 100.0),          # Carbon 0-100%
    'H': (0.0, 20.0),           # Hydrogen 0-20%
    'N': (0.0, 5.0),            # Nitrogen 0-5%
    'O': (0.0, 50.0),           # Oxygen 0-50%

    # Фосфор, Флюор, Хлор (trace elements) - ppm/µg/g нэгжтэй
    'P': (0.0, 1.0),            # Phosphorus 0-1%
    'F': (0.0, 500.0),          # Fluorine 100-500 ppm
    'Cl': (0.0, 600.0),         # Chlorine 120-600 ppm
    'P,ad': (0.0, 1.0),
    'P,d': (0.0, 1.0),
    'F,ad': (0.0, 500.0),       # Fluorine 100-500 ppm
    'F,d': (0.0, 500.0),
    'Cl,ad': (0.0, 600.0),      # Chlorine 120-600 ppm
    'Cl,d': (0.0, 600.0),

    # Caking indices
    'CSN': (0.0, 9.6),          # Crucible swelling number 0-9.6
    'Gi': (0, 110),             # Gray-King index 0-110
    'Y': (0, 50),               # Roga index Y
    'X': (0, 30),               # Roga index X
    'CRI': (0, 100),            # Coke Reactivity Index 0-100
    'CSR': (0, 100),            # Coke Strength after Reaction 0-100

    # Dilatation
    'TRD': (1, 4.00),            # Total relative dilatation 1-4.00%
    'TRD,ad': (1, 4.00),
    'TRD,d': (1, 4.00),

    # Solid residue
    'SOLID': (0, 100),          # Solid residue 0-100%

    # Free moisture
    'FM': (0, 100),          # Free moisture 0-100 
}

# Default муж (тодорхойгүй анализд)
DEFAULT_RANGE = (-10000.0, 100000.0)


def validate_analysis_result(
    value: Any,
    analysis_code: str,
    allow_none: bool = True
) -> Tuple[Optional[float], Optional[str]]:
    """
    Шинжилгээний үр дүнгийн утгыг баталгаажуулах

    Args:
        value: Шалгах утга (float, int, str, эсвэл None)
        analysis_code: Анализын код (жнь: "MT", "Aad", "TS")
        allow_none: None утгыг зөвшөөрөх эсэх

    Returns:
        Tuple[Optional[float], Optional[str]]:
            (validated_value, error_message)
            - validated_value: None эсвэл float утга
            - error_message: None эсвэл алдааны тайлбар

    Example:
        >>> validate_analysis_result(5.2, "Mad")
        (5.2, None)  # ОК

        >>> validate_analysis_result(50.0, "Mad")
        (None, "Inherent moisture 0-20% хооронд байх ёстой")  # Range error

        >>> validate_analysis_result("abc", "Mad")
        (None, "Үр дүн тоон утга байх ёстой")  # Type error
    """
    # None утгыг шалгах
    if value is None or value == '':
        if allow_none:
            return None, None
        else:
            return None, "Үр дүн шаардлагатай"

    # Float руу хөрвүүлэх оролдлого
    try:
        if isinstance(value, (int, float)):
            float_value = float(value)
        elif isinstance(value, str):
            # Comma-г decimal point болгох
            cleaned = value.strip().replace(',', '.')
            float_value = float(cleaned)
        else:
            return None, f"Үр дүн буруу төрөл: {type(value).__name__}"
    except (ValueError, TypeError):
        return None, "Үр дүн тоон утга байх ёстой"

    # NaN, Infinity шалгах
    if not (-1e308 < float_value < 1e308):
        return None, "Үр дүн хэт том эсвэл буруу утга"

    # Range validation
    min_val, max_val = ANALYSIS_VALUE_RANGES.get(
        analysis_code,
        DEFAULT_RANGE
    )

    if not (min_val <= float_value <= max_val):
        return None, (
            f"Үр дүн {min_val}-{max_val} хооронд байх ёстой "
            f"(одоо: {float_value})"
        )

    return float_value, None


# ============================================================================
# SAMPLE_ID VALIDATION
# ============================================================================

def validate_sample_id(value: Any) -> Tuple[Optional[int], Optional[str]]:
    """
    Sample ID-г баталгаажуулах

    Args:
        value: Шалгах утга

    Returns:
        Tuple[Optional[int], Optional[str]]: (sample_id, error_message)

    Example:
        >>> validate_sample_id("123")
        (123, None)

        >>> validate_sample_id("-5")
        (None, "Sample ID эерэг тоо байх ёстой")
    """
    if value is None:
        return None, "Sample ID шаардлагатай"

    try:
        sample_id = int(value)
    except (ValueError, TypeError):
        return None, f"Sample ID тоо байх ёстой (одоо: {value})"

    if sample_id <= 0:
        return None, "Sample ID эерэг тоо байх ёстой"

    if sample_id > 2147483647:  # INT max value
        return None, "Sample ID хэт том утга"

    return sample_id, None


# ============================================================================
# ANALYSIS CODE VALIDATION
# ============================================================================

def validate_analysis_code(value: Any) -> Tuple[Optional[str], Optional[str]]:
    """
    Analysis code-ыг баталгаажуулах

    Args:
        value: Шалгах утга

    Returns:
        Tuple[Optional[str], Optional[str]]: (code, error_message)

    Example:
        >>> validate_analysis_code("MT")
        ("MT", None)

        >>> validate_analysis_code("INVALID_CODE_123")
        (None, "Analysis code хэт урт байна")
    """
    if not value:
        return None, "Analysis code шаардлагатай"

    if not isinstance(value, str):
        return None, "Analysis code текст байх ёстой"

    code = value.strip()

    # Length check
    if len(code) > 20:
        return None, "Analysis code хэт урт байна (max: 20 тэмдэгт)"

    if len(code) < 1:
        return None, "Analysis code хоосон байж болохгүй"

    # Valid characters check (letters, numbers, comma, space)
    if not re.match(r'^[A-Za-z0-9,\s]+$', code):
        return None, "Analysis code зөвхөн үсэг, тоо, таслал агуулна"

    return code, None


# ============================================================================
# EQUIPMENT ID VALIDATION
# ============================================================================

def validate_equipment_id(
    value: Any,
    allow_none: bool = True
) -> Tuple[Optional[int], Optional[str]]:
    """
    Equipment ID-г баталгаажуулах

    Args:
        value: Шалгах утга
        allow_none: None зөвшөөрөх эсэх

    Returns:
        Tuple[Optional[int], Optional[str]]: (equipment_id, error_message)
    """
    if value is None or value == '':
        if allow_none:
            return None, None
        else:
            return None, "Equipment ID шаардлагатай"

    try:
        eq_id = int(value)
    except (ValueError, TypeError):
        return None, f"Equipment ID тоо байх ёстой"

    if eq_id <= 0:
        return None, "Equipment ID эерэг тоо байх ёстой"

    return eq_id, None


# ============================================================================
# BATCH VALIDATION
# ============================================================================

def validate_save_results_batch(
    items: list
) -> Tuple[bool, list, list]:
    """
    /api/save_results endpoint-ийн batch input-ыг баталгаажуулах

    Args:
        items: List of dictionaries with analysis results

    Returns:
        Tuple[bool, list, list]:
            - is_valid: Бүх item зөв эсэх
            - validated_items: Validated болон cleaned items
            - errors: Алдаануудын жагсаалт

    Example:
        >>> items = [
        ...     {"sample_id": "1", "analysis_code": "MT", "final_result": "5.2"},
        ...     {"sample_id": "2", "analysis_code": "BAD", "final_result": "abc"}
        ... ]
        >>> is_valid, validated, errors = validate_save_results_batch(items)
        >>> is_valid
        False
        >>> len(errors)
        1
    """
    if not isinstance(items, list):
        return False, [], ["Input бай batch array байх ёстой"]

    validated_items = []
    errors = []

    for idx, item in enumerate(items):
        if not isinstance(item, dict):
            errors.append(f"Item {idx}: Dictionary байх ёстой")
            continue

        # Validate sample_id
        sample_id, err = validate_sample_id(item.get('sample_id'))
        if err:
            errors.append(f"Item {idx}: {err}")
            continue

        # Validate analysis_code
        analysis_code, err = validate_analysis_code(item.get('analysis_code'))
        if err:
            errors.append(f"Item {idx}: {err}")
            continue

        # Validate final_result
        final_result, err = validate_analysis_result(
            item.get('final_result'),
            analysis_code,
            allow_none=True
        )
        if err:
            errors.append(f"Item {idx} ({analysis_code}): {err}")
            # Энэ нь critical биш, цааш үргэлжлүүлнэ

        # Validate equipment_id
        equipment_id, err = validate_equipment_id(
            item.get('equipment_id'),
            allow_none=True
        )
        if err:
            errors.append(f"Item {idx}: {err}")
            # Warning level - цааш үргэлжлүүлнэ

        # Validated item үүсгэх
        validated_item = {
            'sample_id': sample_id,
            'analysis_code': analysis_code,
            'final_result': final_result,
            'equipment_id': equipment_id,
            # Бусад талбарууд (status, notes, гэх мэт)
            'status': item.get('status', 'draft'),
            'notes': item.get('notes', ''),
            'raw_data': item.get('raw_data'),  # JSON field
        }

        validated_items.append(validated_item)

    is_valid = len(errors) == 0
    return is_valid, validated_items, errors


# ============================================================================
# CSN VALIDATION
# ============================================================================

def get_csn_repeatability_limit() -> float:
    """
    CSN тохирцын хязгаарыг config-оос авах
    """
    try:
        from app.config.repeatability import LIMIT_RULES
        csn_rule = LIMIT_RULES.get('CSN', {})
        if 'single' in csn_rule:
            return csn_rule['single'].get('limit', 0.50)
    except ImportError:
        pass
    # Fallback
    return 0.50


def round_to_half(value: float) -> float:
    """
    CSN дундажийг 0.5 алхамаар дугуйлах (0.5, 1.0, 1.5, 2.0, ...)

    Args:
        value: Дугуйлах утга

    Returns:
        float: 0.5 алхамаар дугуйлсан утга

    Example:
        >>> round_to_half(2.3)
        2.5
        >>> round_to_half(2.7)
        2.5
        >>> round_to_half(2.8)
        3.0
    """
    return round(value * 2) / 2


def validate_csn_values(
    values: list
) -> Tuple[bool, Optional[dict], list]:
    """
    CSN утгуудыг баталгаажуулах

    Args:
        values: v1-v5 утгуудын жагсаалт [v1, v2, v3, v4, v5]

    Returns:
        Tuple[bool, Optional[dict], list]:
            - is_valid: Validation амжилттай эсэх
            - result: Тооцоолсон үр дүн (avg, range, exceeded)
            - errors: Алдаануудын жагсаалт

    Example:
        >>> validate_csn_values([2, 4, 4, None, None])
        (False, {...}, ["Тохирцын зөрүү давсан: 2.0 > 1.0"])
    """
    errors = []

    # None болон хоосон утгуудыг хасах
    valid_values = []
    for i, v in enumerate(values):
        if v is not None and v != '':
            try:
                num = float(v)
                valid_values.append(num)
            except (ValueError, TypeError):
                errors.append(f"v{i+1} буруу утга: {v}")

    # Хамгийн багадаа 2 утга шаардлага
    if len(valid_values) < 2:
        errors.append(f"Хамгийн багадаа 2 утга оруулах шаардлагатай (одоо: {len(valid_values)})")
        return False, None, errors

    # Тохирц тооцоолох (max - min)
    range_val = max(valid_values) - min(valid_values)

    # Дундаж тооцоолох
    raw_avg = sum(valid_values) / len(valid_values)

    # 0.5 алхамаар дугуйлах
    avg = round_to_half(raw_avg)

    # Тохирцын хязгаарыг config-оос авна
    repeatability_limit = get_csn_repeatability_limit()

    # Тохирцын шалгалт
    exceeded = range_val > repeatability_limit
    if exceeded:
        errors.append(f"Тохирцын зөрүү давсан: {range_val:.2f} > {repeatability_limit}")

    result = {
        'avg': avg,
        'raw_avg': raw_avg,
        'range': range_val,
        'limit': repeatability_limit,
        'exceeded': exceeded,
        'values_count': len(valid_values)
    }

    # exceeded байсан ч is_valid = True (анхааруулга харуулах боловч хадгалах боломжтой)
    # Гэхдээ < 2 утга байвал is_valid = False
    is_valid = len(valid_values) >= 2

    return is_valid, result, errors


# ============================================================================
# STRING VALIDATION (XSS PREVENTION)
# ============================================================================

def sanitize_string(
    value: Any,
    max_length: int = 1000,
    allow_none: bool = True
) -> Tuple[Optional[str], Optional[str]]:
    """
    String утгыг цэвэрлэх (XSS сэргийлэх)

    Args:
        value: Шалгах утга
        max_length: Хамгийн их урт
        allow_none: None зөвшөөрөх эсэх

    Returns:
        Tuple[Optional[str], Optional[str]]: (cleaned_string, error_message)
    """
    if value is None or value == '':
        if allow_none:
            return None, None
        else:
            return None, "Утга шаардлагатай"

    if not isinstance(value, str):
        value = str(value)

    # Strip whitespace
    cleaned = value.strip()

    # Length check
    if len(cleaned) > max_length:
        return None, f"Хэт урт байна (max: {max_length} тэмдэгт)"

    # Dangerous patterns check (simple XSS prevention)
    dangerous_patterns = [
        r'<script',
        r'javascript:',
        r'onerror=',
        r'onload=',
        r'onclick=',
    ]

    for pattern in dangerous_patterns:
        if re.search(pattern, cleaned, re.IGNORECASE):
            return None, "Хориотой тэмдэгт агуулсан байна"

    return cleaned, None
