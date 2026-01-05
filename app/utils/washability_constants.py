# -*- coding: utf-8 -*-
"""
Washability Testing Constants and Reference Data

Based on international standards and research:
- ASTM D4371 - Standard Test Method for Determining the Washability Characteristics of Coal
- Bird (1931) - NGM Classification
- Sarkar & Das (1974), Majumder & Barnwal (2004) - Washability Indices

Sources:
- Kentucky Geological Survey (https://www.uky.edu/KGS/coal/coal-analyses-float-sink.php)
- SGS Float-Sink Testing (https://www.sgs.com/en/services/float-sink-and-washability-testing)
- ResearchGate publications on coal washability
"""

# ==============================================================================
# DENSITY RANGES FOR FLOAT-SINK ANALYSIS
# ==============================================================================

# Standard density fractions (g/cm³) - ASTM D4371
STANDARD_DENSITY_FRACTIONS = [
    1.30, 1.325, 1.35, 1.375, 1.40,
    1.425, 1.45, 1.50, 1.60, 1.70,
    1.80, 2.00, 2.20
]

# Extended density fractions for detailed analysis
EXTENDED_DENSITY_FRACTIONS = [
    1.25, 1.30, 1.325, 1.35, 1.375, 1.40,
    1.425, 1.45, 1.475, 1.50, 1.55, 1.60,
    1.70, 1.80, 1.90, 2.00, 2.20, 2.80
]

# Typical specific gravities
SPECIFIC_GRAVITY = {
    'coal': (1.2, 1.5),          # Clean coal
    'shale': (2.4, 2.8),         # Shale/mudstone
    'pyrite': (4.9, 5.2),        # Pyrite (FeS2)
    'calcite': (2.7, 2.7),       # Calcite
    'siderite': (3.8, 3.9),      # Siderite
}


# ==============================================================================
# NGM CLASSIFICATION (Bird, 1931)
# Near Gravity Material at ±0.1 RD
# ==============================================================================

NGM_CLASSIFICATION = {
    'simple': (0, 7),              # Хялбар баяжуулах
    'moderate': (7, 10),           # Дунд зэрэг
    'difficult': (10, 15),         # Хүнд
    'very_difficult': (15, 20),    # Маш хүнд
    'exceedingly_difficult': (20, 25),  # Туйлын хүнд
    'formidable': (25, 100),       # Боломжгүй
}

NGM_LABELS = {
    'simple': 'Simple (Хялбар)',
    'moderate': 'Moderate (Дунд)',
    'difficult': 'Difficult (Хүнд)',
    'very_difficult': 'Very Difficult (Маш хүнд)',
    'exceedingly_difficult': 'Exceedingly Difficult (Туйлын хүнд)',
    'formidable': 'Formidable (Боломжгүй)',
}


def classify_ngm(ngm_value: float) -> str:
    """
    NGM утгаар баяжигдах чанарыг ангилах.

    Args:
        ngm_value: NGM ±0.1 утга (%)

    Returns:
        Ангиллын нэр
    """
    for name, (low, high) in NGM_CLASSIFICATION.items():
        if low <= ngm_value < high:
            return NGM_LABELS[name]
    return NGM_LABELS['formidable']


# ==============================================================================
# WASHABILITY INDEX RANGES
# ==============================================================================

# Washability Number (W) - 0 to 100
# Higher W = easier to wash
WASHABILITY_NUMBER_INTERPRETATION = {
    'very_easy': (80, 100),
    'easy': (60, 80),
    'moderate': (40, 60),
    'difficult': (20, 40),
    'very_difficult': (0, 20),
}

# NGMI (Near Gravity Material Index) - 0 to 1
# Lower NGMI = easier to wash
NGMI_INTERPRETATION = {
    'easy': (0.0, 0.2),
    'moderate': (0.2, 0.4),
    'difficult': (0.4, 0.6),
    'very_difficult': (0.6, 0.8),
    'formidable': (0.8, 1.0),
}


# ==============================================================================
# ORGANIC EFFICIENCY BENCHMARKS
# ==============================================================================

# Organic Efficiency = (Actual Yield / Theoretical Yield) × 100
ORGANIC_EFFICIENCY_BENCHMARKS = {
    'excellent': (95, 100),      # Маш сайн
    'good': (90, 95),            # Сайн
    'acceptable': (85, 90),      # Хүлээн зөвшөөрөгдөхүйц
    'poor': (80, 85),            # Муу
    'very_poor': (0, 80),        # Маш муу
}


def evaluate_organic_efficiency(efficiency: float) -> str:
    """
    Organic efficiency үнэлгээ.

    Args:
        efficiency: Organic efficiency (%)

    Returns:
        Үнэлгээний тэмдэгт мөр
    """
    for name, (low, high) in ORGANIC_EFFICIENCY_BENCHMARKS.items():
        if low <= efficiency <= high:
            return name
    return 'very_poor'


# ==============================================================================
# STANDARD SIZE FRACTIONS (mm)
# ==============================================================================

SIZE_FRACTIONS_COARSE = [
    (50, 31.5),
    (31.5, 16),
    (16, 8),
    (8, 4.75),
    (4.75, 2),
]

SIZE_FRACTIONS_FINE = [
    (2, 1),
    (1, 0.5),
    (0.5, 0.25),
    (0.25, 0.15),
    (0.15, 0.074),
    (0.074, 0.038),
    (0.038, 0),  # -0.038mm (slimes)
]


# ==============================================================================
# TARGET ASH LEVELS (Typical product specifications)
# ==============================================================================

TARGET_ASH_HCC = {
    'premium': (8.0, 9.0),       # Premium HCC
    'standard': (9.0, 10.5),     # Standard HCC
    'secondary': (10.5, 12.0),   # Secondary HCC
}

TARGET_ASH_SSCC = {
    'low_ash': (10.0, 11.0),
    'medium_ash': (11.0, 13.0),
    'high_ash': (13.0, 15.0),
}

TARGET_ASH_THERMAL = {
    'export': (12.0, 15.0),
    'domestic': (15.0, 20.0),
}


# ==============================================================================
# WASHABILITY CURVE FORMULAS (Reference)
# ==============================================================================

"""
WASHABILITY CURVE EQUATIONS:

1. Cumulative Float Curve:
   Y = Σ(yi) for all fractions where density ≤ separation density
   where yi = individual fraction yield (%)

2. Cumulative Ash (Weighted Average):
   A_cum = Σ(yi × ai) / Σ(yi)
   where ai = ash content of fraction i (%)

3. Theoretical Yield at Target Ash (Linear Interpolation):
   Y_target = Y1 + (A_target - A1) × (Y2 - Y1) / (A2 - A1)
   where:
   - (Y1, A1) = cumulative yield and ash just below target
   - (Y2, A2) = cumulative yield and ash just above target

4. Near Gravity Material (NGM):
   NGM = Y(ρ + 0.1) - Y(ρ - 0.1)
   where:
   - ρ = separation density
   - Y(ρ) = cumulative yield at density ρ

5. Organic Efficiency:
   OE = (Actual Yield / Theoretical Yield) × 100%

6. Recovery Efficiency:
   RE = (Actual Yield × Feed Mass) / (Theoretical Yield × Feed Mass) × 100%

7. Separation Density (from washability curve):
   Find ρ where cumulative ash = target ash

8. M-Curve (Mayer Curve):
   Plot: Cumulative Mass (Y-axis) vs Ash Mass (X-axis)
   Ash Mass = Σ(yi × ai)
   Slope at any point = instantaneous ash content

9. Washability Number (W):
   W = 100 × (1 - NGM/100) × F
   where F = correction factor based on ash distribution

10. NGMI (Near Gravity Material Index):
    NGMI = Σ(NGMi × Wi) / Σ(Wi)
    where NGMi = NGM at density i, Wi = weight factor
"""


# ==============================================================================
# HELPER FUNCTIONS
# ==============================================================================

def get_target_ash_range(product_type: str) -> tuple:
    """
    Бүтээгдэхүүний төрлөөр зорилтот үнслэгийн хүрээ авах.

    Args:
        product_type: 'HCC', 'SSCC', 'thermal' гэх мэт

    Returns:
        (min_ash, max_ash) tuple
    """
    product_type = product_type.upper()

    if 'HCC' in product_type:
        return (8.0, 12.0)
    elif 'SSCC' in product_type:
        return (10.0, 15.0)
    elif 'THERMAL' in product_type or 'STEAM' in product_type:
        return (12.0, 20.0)
    else:
        return (8.0, 15.0)  # Default range


def calculate_density_midpoint(sink: float, flt: float) -> float:
    """
    Нягтын фракцийн дундаж нягт тооцоолох.

    Args:
        sink: Доод нягт (sink to)
        flt: Дээд нягт (float at)

    Returns:
        Дундаж нягт
    """
    return (sink + flt) / 2


def density_to_fraction_name(sink: float, flt: float) -> str:
    """
    Нягтын утгаас фракцийн нэр үүсгэх.

    Args:
        sink: Доод нягт
        flt: Дээд нягт

    Returns:
        "F1.30-1.35" гэх мэт нэр
    """
    return f"F{sink:.2f}-{flt:.2f}"
