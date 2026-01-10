# -*- coding: utf-8 -*-
"""
Washability Calculation Engine

Нүүрсний баяжигдах чанарын шинжилгээ (Float-Sink Analysis) дээр суурилсан
Theoretical Yield тооцооллын систем.

Томъёонууд:
- Cumulative Float Yield = Σ(individual yield) нягт бага -> их рүү
- Cumulative Ash = Σ(yield × ash) / Σ(yield)
- Theoretical Yield = interpolation(target_ash, cumulative_ash, cumulative_yield)
- NGM (Near Gravity Material) = ±0.1 density дахь % (баяжуулахад хэцүү хэсэг)
"""

from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass


@dataclass
class FractionData:
    """Float-sink фракцийн дата"""
    density_sink: float  # Доод нягт
    density_float: float  # Дээд нягт (float to this density)
    mass_gram: float
    mass_percent: float
    ash_ad: float
    im_percent: Optional[float] = None
    vol_ad: Optional[float] = None
    sulphur_ad: Optional[float] = None
    csn: Optional[float] = None


@dataclass
class CumulativeData:
    """Cumulative (хуримтлагдсан) өгөгдөл"""
    density: float
    cumulative_yield: float  # %
    cumulative_ash: float  # %
    elementary_ash: float  # Individual fraction ash


@dataclass
class YieldResult:
    """Theoretical yield тооцооллын үр дүн"""
    target_ash: float
    theoretical_yield: float
    separation_density: float
    ngm_01: float  # ±0.1 density material %
    ngm_02: float  # ±0.2 density material %
    cumulative_data: List[CumulativeData]


def calculate_cumulative(fractions: List[FractionData]) -> List[CumulativeData]:
    """
    Cumulative float yield болон cumulative ash тооцоолох.

    Float-sink дата нь нягт багаас -> их рүү эрэмблэгдсэн байх ёстой.
    Cumulative yield = нягт бага фракцуудын нийлбэр
    Cumulative ash = weighted average

    Args:
        fractions: Float-sink фракцуудын жагсаалт

    Returns:
        Cumulative өгөгдлийн жагсаалт
    """
    if not fractions:
        return []

    # Нягтаар эрэмбэлэх (бага -> их)
    sorted_fractions = sorted(fractions, key=lambda x: x.density_float)

    cumulative_data = []
    cum_yield = 0.0
    cum_yield_ash_product = 0.0

    for frac in sorted_fractions:
        # Skip zero or invalid mass
        if frac.mass_percent is None or frac.mass_percent <= 0:
            continue
        if frac.ash_ad is None:
            continue

        cum_yield += frac.mass_percent
        cum_yield_ash_product += frac.mass_percent * frac.ash_ad

        # Cumulative ash = weighted average
        cum_ash = cum_yield_ash_product / cum_yield if cum_yield > 0 else 0

        cumulative_data.append(CumulativeData(
            density=frac.density_float,
            cumulative_yield=round(cum_yield * 100, 2),  # Convert to %
            cumulative_ash=round(cum_ash, 2),
            elementary_ash=frac.ash_ad
        ))

    return cumulative_data


def interpolate_yield(cumulative_data: List[CumulativeData],
                      target_ash: float) -> Tuple[float, float]:
    """
    Зорилтот үнслэгт хүрэх theoretical yield олох (linear interpolation).

    Args:
        cumulative_data: Cumulative өгөгдлийн жагсаалт
        target_ash: Зорилтот үнслэг (%)

    Returns:
        (theoretical_yield, separation_density)
    """
    if not cumulative_data:
        return 0.0, 0.0

    # Target ash-д хүрэх цэг олох
    prev = None
    for curr in cumulative_data:
        if curr.cumulative_ash >= target_ash:
            if prev is None:
                # Эхний фракц аль хэдийн target-аас их -> бүх нүүрс
                return curr.cumulative_yield, curr.density

            # Linear interpolation
            ash_diff = curr.cumulative_ash - prev.cumulative_ash
            if ash_diff == 0:
                return curr.cumulative_yield, curr.density

            ratio = (target_ash - prev.cumulative_ash) / ash_diff
            yield_interp = prev.cumulative_yield + ratio * (curr.cumulative_yield - prev.cumulative_yield)
            density_interp = prev.density + ratio * (curr.density - prev.density)

            return round(yield_interp, 2), round(density_interp, 3)

        prev = curr

    # Target ash-д хүрээгүй -> бүх нүүрсийг авах
    last = cumulative_data[-1]
    return last.cumulative_yield, last.density


def calculate_ngm(cumulative_data: List[CumulativeData],
                  separation_density: float,
                  delta: float = 0.1) -> float:
    """
    Near Gravity Material (NGM) тооцоолох.

    NGM = ялгаралтын нягт ± delta дахь материалын хэмжээ (%)
    Энэ утга өндөр байх тусам баяжуулахад хэцүү.

    Args:
        cumulative_data: Cumulative өгөгдөл
        separation_density: Ялгаралтын нягт
        delta: Хүрээ (default ±0.1)

    Returns:
        NGM хувь (%)
    """
    if not cumulative_data:
        return 0.0

    lower_density = separation_density - delta
    upper_density = separation_density + delta

    # Find yields at lower and upper density bounds
    lower_yield = 0.0
    upper_yield = 0.0

    for i, curr in enumerate(cumulative_data):
        if curr.density >= lower_density and lower_yield == 0:
            if i == 0:
                lower_yield = 0
            else:
                prev = cumulative_data[i - 1]
                # Interpolate
                if curr.density != prev.density:
                    ratio = (lower_density - prev.density) / (curr.density - prev.density)
                else:
                    ratio = 0
                lower_yield = prev.cumulative_yield + ratio * (curr.cumulative_yield - prev.cumulative_yield)

        if curr.density >= upper_density:
            if i == 0:
                upper_yield = curr.cumulative_yield
            else:
                prev = cumulative_data[i - 1]
                if curr.density != prev.density:
                    ratio = (upper_density - prev.density) / (curr.density - prev.density)
                else:
                    ratio = 0
                upper_yield = prev.cumulative_yield + ratio * (curr.cumulative_yield - prev.cumulative_yield)
            break

    # If upper density not reached, use last value
    if upper_yield == 0:
        upper_yield = cumulative_data[-1].cumulative_yield

    ngm = upper_yield - lower_yield
    return round(abs(ngm), 2)


def calculate_theoretical_yield(fractions: List[FractionData],
                                target_ash: float) -> YieldResult:
    """
    Theoretical yield бүрэн тооцоолол.

    Args:
        fractions: Float-sink фракцуудын жагсаалт
        target_ash: Зорилтот үнслэг (%)

    Returns:
        YieldResult объект
    """
    # 1. Cumulative values тооцоолох
    cumulative_data = calculate_cumulative(fractions)

    if not cumulative_data:
        return YieldResult(
            target_ash=target_ash,
            theoretical_yield=0,
            separation_density=0,
            ngm_01=0,
            ngm_02=0,
            cumulative_data=[]
        )

    # 2. Interpolate yield at target ash
    theoretical_yield, separation_density = interpolate_yield(cumulative_data, target_ash)

    # 3. Calculate NGM
    ngm_01 = calculate_ngm(cumulative_data, separation_density, delta=0.1)
    ngm_02 = calculate_ngm(cumulative_data, separation_density, delta=0.2)

    return YieldResult(
        target_ash=target_ash,
        theoretical_yield=theoretical_yield,
        separation_density=separation_density,
        ngm_01=ngm_01,
        ngm_02=ngm_02,
        cumulative_data=cumulative_data
    )


def calculate_recovery_efficiency(theoretical_yield: float,
                                  actual_yield: float) -> float:
    """
    Recovery efficiency тооцоолох.

    Args:
        theoretical_yield: Онолын гарц (%)
        actual_yield: Бодит үйлдвэрийн гарц (%)

    Returns:
        Recovery efficiency (%)
    """
    if theoretical_yield <= 0:
        return 0.0
    return round((actual_yield / theoretical_yield) * 100, 2)


def generate_washability_curve_data(cumulative_data: List[CumulativeData]) -> Dict:
    """
    Washability curve график-д зориулсан дата үүсгэх.

    Returns:
        {
            'yield': [list of cumulative yields],
            'ash': [list of cumulative ash],
            'density': [list of densities],
            'elementary_ash': [list of individual ash values]
        }
    """
    return {
        'yield': [d.cumulative_yield for d in cumulative_data],
        'ash': [d.cumulative_ash for d in cumulative_data],
        'density': [d.density for d in cumulative_data],
        'elementary_ash': [d.elementary_ash for d in cumulative_data]
    }


def analyze_washability_quality(ngm_01: float) -> str:
    """
    Баяжигдах чанарын үнэлгээ (NGM дээр суурилсан).

    NGM ±0.1 утгаар үнэлгээ:
    - < 7%: Хялбар (Easy)
    - 7-10%: Дунд зэрэг (Moderate)
    - 10-15%: Хүнд (Difficult)
    - 15-20%: Маш хүнд (Very Difficult)
    - > 20%: Боломжгүй (Impractical)

    Args:
        ngm_01: NGM ±0.1 утга

    Returns:
        Үнэлгээний тэмдэгт мөр
    """
    if ngm_01 < 7:
        return "Easy (Хялбар)"
    elif ngm_01 < 10:
        return "Moderate (Дунд)"
    elif ngm_01 < 15:
        return "Difficult (Хүнд)"
    elif ngm_01 < 20:
        return "Very Difficult (Маш хүнд)"
    else:
        return "Impractical (Боломжгүй)"


# ==============================================================================
# SIZE FRACTION CALCULATIONS
# ==============================================================================

def calculate_composite_yield(size_fractions: Dict[str, List[FractionData]],
                              size_weights: Dict[str, float],
                              target_ash: float) -> YieldResult:
    """
    Олон size fraction-ийг нэгтгэсэн composite theoretical yield.

    Args:
        size_fractions: {size_name: [fractions]} dictionary
        size_weights: {size_name: weight_percent} dictionary
        target_ash: Зорилтот үнслэг

    Returns:
        Composite YieldResult
    """
    total_weight = sum(size_weights.values())
    if total_weight == 0:
        return YieldResult(target_ash, 0, 0, 0, 0, [])

    weighted_yield = 0
    weighted_density = 0
    weighted_ngm_01 = 0
    weighted_ngm_02 = 0

    for size_name, fractions in size_fractions.items():
        weight = size_weights.get(size_name, 0)
        if weight == 0:
            continue

        result = calculate_theoretical_yield(fractions, target_ash)
        weight_ratio = weight / total_weight

        weighted_yield += result.theoretical_yield * weight_ratio
        weighted_density += result.separation_density * weight_ratio
        weighted_ngm_01 += result.ngm_01 * weight_ratio
        weighted_ngm_02 += result.ngm_02 * weight_ratio

    return YieldResult(
        target_ash=target_ash,
        theoretical_yield=round(weighted_yield, 2),
        separation_density=round(weighted_density, 3),
        ngm_01=round(weighted_ngm_01, 2),
        ngm_02=round(weighted_ngm_02, 2),
        cumulative_data=[]  # Composite-д individual data байхгүй
    )


def calculate_yield_table(fractions: List[FractionData],
                          ash_range: Tuple[float, float] = (8.0, 12.0),
                          step: float = 0.5) -> List[Dict]:
    """
    Олон зорилтот үнслэгт хүрэх yield хүснэгт үүсгэх.

    Args:
        fractions: Float-sink фракцуудын жагсаалт
        ash_range: (min_ash, max_ash) хүрээ
        step: Алхам

    Returns:
        [{target_ash, theoretical_yield, separation_density, ngm_01}, ...]
    """
    results = []
    ash = ash_range[0]

    while ash <= ash_range[1]:
        result = calculate_theoretical_yield(fractions, ash)
        results.append({
            'target_ash': ash,
            'theoretical_yield': result.theoretical_yield,
            'separation_density': result.separation_density,
            'ngm_01': result.ngm_01,
            'quality': analyze_washability_quality(result.ngm_01)
        })
        ash += step

    return results


# ==============================================================================
# ADVANCED WASHABILITY INDICES
# Based on: Sarkar & Das (1974), Majumder & Barnwal (2004), Bird (1931)
# ==============================================================================

def calculate_ngmi(fractions: List[FractionData],
                   density_points: List[float] = None) -> float:
    """
    Near Gravity Material Index (NGMI) тооцоолох.

    NGMI = Σ(NGMi × Wi) / Σ(Wi)
    NGMI: 0 = хялбар баяжуулах, 1 = боломжгүй

    Reference: Majumder & Barnwal (2004)

    Args:
        fractions: Float-sink фракцуудын жагсаалт
        density_points: NGM тооцоолох нягтын цэгүүд

    Returns:
        NGMI утга (0-1)
    """
    if density_points is None:
        density_points = [1.4, 1.5, 1.6, 1.7, 1.8]

    cumulative_data = calculate_cumulative(fractions)
    if not cumulative_data:
        return 0.0

    total_ngm_weighted = 0.0
    total_weight = 0.0

    for density in density_points:
        ngm = calculate_ngm(cumulative_data, density, delta=0.1)
        # Weight by yield at that density
        _, yield_at_density = interpolate_yield(cumulative_data, density)
        weight = yield_at_density if yield_at_density > 0 else 1.0

        total_ngm_weighted += ngm * weight
        total_weight += weight

    if total_weight == 0:
        return 0.0

    # Normalize to 0-1 range (assuming max NGM = 100)
    ngmi = (total_ngm_weighted / total_weight) / 100
    return round(min(max(ngmi, 0), 1), 3)


def calculate_washability_number(fractions: List[FractionData],
                                 target_ash: float) -> float:
    """
    Washability Number (W) тооцоолох.

    W = 0-100, өндөр утга = хялбар баяжуулах

    Reference: Sarkar et al. (1977)

    Args:
        fractions: Float-sink фракцуудын жагсаалт
        target_ash: Зорилтот үнслэг

    Returns:
        Washability Number (0-100)
    """
    result = calculate_theoretical_yield(fractions, target_ash)

    if result.theoretical_yield <= 0:
        return 0.0

    # W is inversely related to NGM
    # W = 100 × (1 - NGM/max_possible_ngm)
    # Assuming max NGM for formidable coal is ~30%
    ngm_factor = min(result.ngm_01 / 30, 1.0)
    washability_number = 100 * (1 - ngm_factor)

    # Adjust for yield (higher yield = easier washing)
    yield_factor = result.theoretical_yield / 100
    washability_number *= (0.5 + 0.5 * yield_factor)

    return round(max(min(washability_number, 100), 0), 1)


def calculate_m_curve_data(fractions: List[FractionData]) -> Dict:
    """
    M-Curve (Mayer Curve) дата үүсгэх.

    M-Curve: Cumulative Mass vs Ash Mass
    Slope = instantaneous ash content

    Args:
        fractions: Float-sink фракцуудын жагсаалт

    Returns:
        {
            'cumulative_mass': [...],
            'ash_mass': [...],
            'slope': [...]  # instantaneous ash
        }
    """
    sorted_fractions = sorted(fractions, key=lambda x: x.density_float)

    cumulative_mass = []
    ash_mass = []
    slopes = []

    cum_mass = 0.0
    cum_ash_mass = 0.0

    for i, frac in enumerate(sorted_fractions):
        if frac.mass_percent is None or frac.mass_percent <= 0:
            continue
        if frac.ash_ad is None:
            continue

        cum_mass += frac.mass_percent * 100  # Convert to %
        cum_ash_mass += frac.mass_percent * frac.ash_ad

        cumulative_mass.append(round(cum_mass, 2))
        ash_mass.append(round(cum_ash_mass, 2))

        # Calculate slope (instantaneous ash)
        if i > 0 and len(cumulative_mass) > 1:
            delta_mass = cumulative_mass[-1] - cumulative_mass[-2]
            delta_ash = ash_mass[-1] - ash_mass[-2]
            slope = delta_ash / delta_mass if delta_mass > 0 else 0
            slopes.append(round(slope, 2))
        else:
            slopes.append(frac.ash_ad)

    return {
        'cumulative_mass': cumulative_mass,
        'ash_mass': ash_mass,
        'slope': slopes
    }


def calculate_organic_efficiency(theoretical_yield: float,
                                 actual_yield: float) -> Dict:
    """
    Organic Efficiency тооцоолж, үнэлгээ өгөх.

    OE = (Actual Yield / Theoretical Yield) × 100%

    Args:
        theoretical_yield: Онолын гарц (%)
        actual_yield: Бодит гарц (%)

    Returns:
        {
            'efficiency': float,
            'rating': str,
            'description': str
        }
    """
    if theoretical_yield <= 0:
        return {
            'efficiency': 0,
            'rating': 'N/A',
            'description': 'Онолын гарц тооцоологдоогүй'
        }

    efficiency = (actual_yield / theoretical_yield) * 100

    if efficiency >= 95:
        rating = 'excellent'
        description = 'Маш сайн - үйлдвэрийн гүйцэтгэл онолын утгад маш ойр'
    elif efficiency >= 90:
        rating = 'good'
        description = 'Сайн - хэвийн үйл ажиллагаа'
    elif efficiency >= 85:
        rating = 'acceptable'
        description = 'Хүлээн зөвшөөрөгдөхүйц - сайжруулах боломжтой'
    elif efficiency >= 80:
        rating = 'poor'
        description = 'Муу - тоног төхөөрөмж/процессийг шалгах шаардлагатай'
    else:
        rating = 'very_poor'
        description = 'Маш муу - яаралтай засвар шаардлагатай'

    return {
        'efficiency': round(efficiency, 2),
        'rating': rating,
        'description': description
    }


def generate_full_washability_report(fractions: List[FractionData],
                                     target_ashes: List[float] = None) -> Dict:
    """
    Бүрэн washability тайлан үүсгэх.

    Args:
        fractions: Float-sink фракцуудын жагсаалт
        target_ashes: Зорилтот үнслэгүүдийн жагсаалт

    Returns:
        Бүрэн тайлангийн dictionary
    """
    if target_ashes is None:
        target_ashes = [8.0, 9.0, 10.0, 10.5, 11.0, 12.0]

    # Calculate cumulative data
    cumulative_data = calculate_cumulative(fractions)

    # Calculate yields for each target ash
    yield_results = []
    for ash in target_ashes:
        result = calculate_theoretical_yield(fractions, ash)
        yield_results.append({
            'target_ash': ash,
            'theoretical_yield': result.theoretical_yield,
            'separation_density': result.separation_density,
            'ngm_01': result.ngm_01,
            'ngm_02': result.ngm_02,
            'quality': analyze_washability_quality(result.ngm_01)
        })

    # Calculate indices
    ngmi = calculate_ngmi(fractions)
    washability_number = calculate_washability_number(fractions, 10.0)  # At 10% ash

    # M-curve data
    m_curve = calculate_m_curve_data(fractions)

    # Washability curve data
    curve_data = generate_washability_curve_data(cumulative_data)

    return {
        'summary': {
            'total_fractions': len(fractions),
            'ngmi': ngmi,
            'washability_number': washability_number,
            'overall_quality': 'Easy' if ngmi < 0.3 else 'Moderate' if ngmi < 0.5 else 'Difficult'
        },
        'yield_results': yield_results,
        'cumulative_data': [
            {
                'density': d.density,
                'cumulative_yield': d.cumulative_yield,
                'cumulative_ash': d.cumulative_ash,
                'elementary_ash': d.elementary_ash
            }
            for d in cumulative_data
        ],
        'curves': {
            'washability': curve_data,
            'm_curve': m_curve
        }
    }
