# -*- coding: utf-8 -*-
"""
Шинжилгээний кодуудын alias (товчлол) -> base код хөрвүүлэх map

Энэ файл нь CSV импортлохдоо alias кодуудыг стандарт кодууд руу хөрвүүлэхэд ашиглагдана.

Жишээ:
    "ts" -> "TS"  (Total Sulfur)
    "cv" -> "CV"  (Calorific Value)
    "mad" -> "Mad" (Moisture as Determined)
"""

# Alias -> Base код mapping
# Key нь жижиг үсгээр, value нь стандарт код
ALIAS_TO_BASE = {
    # Total Sulfur (TS)
    "ts": "TS",
    "st,ad": "TS",
    "st.ad": "TS",
    "s": "TS",
    "s,t,ad": "TS",
    "total sulfur": "TS",
    "sulfur": "TS",
    "хүхэр": "TS",

    # Calorific Value (CV)
    "cv": "CV",
    "qgr,ad": "CV",
    "qgr.ad": "CV",
    "qnet,ar": "CV",
    "qnet.ar": "CV",
    "gross cv": "CV",
    "net cv": "CV",
    "дулаан багтаамж": "CV",
    "илчлэг": "CV",

    # Moisture as Determined (Mad)
    "mad": "Mad",
    "m,ad": "Mad",
    "m.ad": "Mad",
    "air dried moisture": "Mad",

    # Total Moisture (MT)
    "mt": "MT",
    "mt,ar": "MT",
    "mt.ar": "MT",
    "total moisture": "MT",
    "нийт чийг": "MT",

    # Free Moisture (FM)
    "fm": "FM",
    "free moisture": "FM",
    "гадаргын чийг": "FM",

    # Ash (Aad)
    "aad": "Aad",
    "a,ad": "Aad",
    "a.ad": "Aad",
    "ash": "Aad",
    "үнс": "Aad",

    # Volatile Matter (Vad)
    "vad": "Vad",
    "v,ad": "Vad",
    "v.ad": "Vad",
    "vm": "Vad",
    "volatile": "Vad",
    "дэгдэмхий": "Vad",

    # True Relative Density (TRD)
    "trd": "TRD",
    "true rd": "TRD",
    "жинхэнэ нягт": "TRD",

    # Crucible Swelling Number (CSN)
    "csn": "CSN",
    "fsi": "CSN",
    "swelling": "CSN",

    # Gray-King Index (Gi)
    "gi": "Gi",
    "gk": "Gi",
    "gray king": "Gi",

    # Phosphorus (P)
    "p": "P",
    "phosphorus": "P",
    "фосфор": "P",

    # Fluorine (F)
    "f": "F",
    "fluorine": "F",
    "фтор": "F",

    # Chlorine (Cl)
    "cl": "Cl",
    "chlorine": "Cl",
    "хлор": "Cl",

    # Coke Reactivity Index (CRI)
    "cri": "CRI",
    "reactivity": "CRI",

    # Coke Strength after Reaction (CSR)
    "csr": "CSR",
    "strength": "CSR",

    # Solid (Yield)
    "solid": "Solid",
    "yield": "Solid",

    # Fixed Carbon (FC)
    "fc": "FC",
    "fcad": "FC",
    "fc,ad": "FC",
    "fixed carbon": "FC",
    "тогтмол нүүрстөрөгч": "FC",

    # Hardgrove Grindability Index (HGI)
    "hgi": "HGI",
    "hardgrove": "HGI",

    # Size Distribution
    "+50mm": "Size_50",
    "+25mm": "Size_25",
    "-6mm": "Size_6",
    "-3mm": "Size_3",
    "-1mm": "Size_1",
    "-0.5mm": "Size_05",

    # Carbon (C)
    "c": "C",
    "carbon": "C",
    "нүүрстөрөгч": "C",

    # Hydrogen (H)
    "h": "H",
    "hydrogen": "H",
    "устөрөгч": "H",

    # Nitrogen (N)
    "n": "N",
    "nitrogen": "N",
    "азот": "N",

    # Oxygen (O)
    "o": "O",
    "oxygen": "O",
    "хүчилтөрөгч": "O",

    # Iron (Fe)
    "fe": "Fe",
    "iron": "Fe",
    "төмөр": "Fe",

    # Silicon (Si)
    "si": "Si",
    "sio2": "SiO2",
    "silicon": "Si",
    "цахиур": "Si",

    # Aluminum (Al)
    "al": "Al",
    "al2o3": "Al2O3",
    "aluminum": "Al",
    "хөнгөн цагаан": "Al",

    # Calcium (Ca)
    "ca": "Ca",
    "cao": "CaO",
    "calcium": "Ca",
    "кальци": "Ca",

    # Magnesium (Mg)
    "mg": "Mg",
    "mgo": "MgO",
    "magnesium": "Mg",

    # Sodium (Na)
    "na": "Na",
    "na2o": "Na2O",
    "sodium": "Na",

    # Potassium (K)
    "k": "K",
    "k2o": "K2O",
    "potassium": "K",

    # Titanium (Ti)
    "ti": "Ti",
    "tio2": "TiO2",
    "titanium": "Ti",

    # Manganese (Mn)
    "mn": "Mn",
    "mno": "MnO",
    "manganese": "Mn",

    # Ash Fusion Temperature
    "idt": "IDT",
    "st": "ST",
    "ht": "HT",
    "ft": "FT",
    "initial deformation": "IDT",
    "softening": "ST",
    "hemispherical": "HT",
    "fluid": "FT",

    # Specific Energy
    "se": "SE",
    "specific energy": "SE",

    # Additional common aliases
    "arsenic": "As",
    "as": "As",
    "lead": "Pb",
    "pb": "Pb",
    "mercury": "Hg",
    "hg": "Hg",
    "selenium": "Se",
}


def normalize_analysis_code(code: str) -> str:
    """
    Шинжилгээний кодыг стандартчлах

    Args:
        code: Оруулсан код (alias эсвэл base)

    Returns:
        Стандарт base код

    Example:
        >>> normalize_analysis_code("ts")
        'TS'
        >>> normalize_analysis_code("Total Sulfur")
        'TS'
        >>> normalize_analysis_code("unknown")
        'unknown'
    """
    if not code:
        return code

    normalized = code.strip().lower()
    return ALIAS_TO_BASE.get(normalized, code)


def get_all_aliases_for_base(base_code: str) -> list:
    """
    Base код-д харгалзах бүх alias-уудыг буцаах

    Args:
        base_code: Стандарт base код (жнь: "TS")

    Returns:
        Тухайн base код-д харгалзах alias-уудын жагсаалт
    """
    return [alias for alias, base in ALIAS_TO_BASE.items() if base == base_code]
