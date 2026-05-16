"""Mine2NEMO sample routing mapping.

Зорилго: Шинэ системийн дээжний нэр (sample_code) → Mine2NEMO-ийн зөв
table-руу route хийх.

ZОБО хуучин системийн логиктэй ижил:
  - PF211/221/231 → QualityPlantFeed
  - Clean Coal (CC) → QualityPrimaryProduct
  - Thermal Coal (TC, Midlings) → QualitySecondaryProduct

Одоогоор зөвхөн CHPP/2 hourly дээжүүд Mine2NEMO-руу очино.
4 hourly, 12 hourly, com нэмэх нь дараагийн iteration-д.
"""

# Mine2NEMO target table нэр
TABLE_PLANT_FEED = "QualityPlantFeed"
TABLE_PRIMARY = "QualityPrimaryProduct"
TABLE_SECONDARY = "QualitySecondaryProduct"

# Date tracking tables (parent dates table)
TABLE_PLANT_FEED_DATE = "QualityPlantFeedDate"
TABLE_PRIMARY_DATE = "QualityPrimaryDate"
TABLE_SECONDARY_DATE = "QualitySecondaryDate"

# === CHPP 2-Hourly Sample Routing ===

# Plant Feed дээжүүд (үндсэн тэжээл) — startswith() шалгана
PF_PREFIXES = ("PF211", "PF221", "PF231")

# Plant Feed mapping: basename → (Group Name, QualityCategoryID UUID)
# QualityCategoryID Mine2NEMO.ProcessControl.QualityCategory-аас (одоо real prod-аас авсан)
PF_GROUP_INFO = {
    "PF211": ("Plant feed SA-211", "71d262a2-df27-4c71-82ac-e152e3587d7b"),
    "PF221": ("Plant feed SA-221", "c9c41600-f00e-489b-a4f4-0b65bf93963b"),
    "PF231": ("Plant feed SA-231", "601b7680-18b5-401a-978c-eb431f8b56c7"),
}

# Clean Coal (Primary) — UHG MV_HCC, UHG HV_HCC г.м. сонгох
# Mine2NEMO-руу очихдоо бүгд `CC_<date>_<shift>` нэр-аар rewrite болно
# (Mine2NEMO-н хуучин convention: бараа ялгаа байхгүй, нэг CC slot).
# Урт хугацаандаа Mine2NEMO dev team тус бүтээгдэхүүний нэрийг дэмжих болно.
CC_NAMES = frozenset({
    "UHG MV_HCC",
    "UHG HV_HCC",
    "UHG MASHCC",
    "BN HV HCC",
    "BN SSCC",
    "MV HCC",  # alt naming
    "HV HCC",
    "MASHCC",
    "SSCC",
})

# Thermal Coal / Midlings (Secondary)
TC_NAMES = frozenset({
    "UHG MASHCC_2",
    "UHG Midd",
    "BN MASHCC_2",
    "BN Midd",
    "MASHCC_2",
    "Midd",
})


# Shift code → SampleTime mapping (2-hourly format)
# Mine2NEMO хүлээгдэж буй формат: D1='08:00', D2='10:00' ... N6='06:00'
SHIFT_TIME_MAP = {
    "D1": "08:00",
    "D2": "10:00",
    "D3": "12:00",
    "D4": "14:00",
    "D5": "16:00",
    "D6": "18:00",
    "N1": "20:00",
    "N2": "22:00",
    "N3": "00:00",
    "N4": "02:00",
    "N5": "04:00",
    "N6": "06:00",
    # Composite shifts (Dcom/Ncom)
    "Dcom": "08:00-18:00",
    "Ncom": "20:00-06:00",
}


def _extract_date_shift(sample_code: str) -> tuple[str | None, str | None]:
    """Sample code-аас date + shift хэсгийг гаргах.

    `MV HCC_20260517_N3` → ('20260517', 'N3')
    Format mismatch үед (None, None) буцаана.
    """
    parts = sample_code.rsplit("_", 2)
    if len(parts) >= 3 and parts[1].isdigit() and len(parts[1]) >= 6:
        return parts[1], parts[2]
    return None, None


def _date_yymmdd(yyyymmdd: str) -> str:
    """8-digit YYYYMMDD-ийг Mine2NEMO 6-digit YYMMDD болгож хөрвүүлэх.

    `20260517` → `260517`. 6-digit аль хэдийн бол хэвээр.
    """
    if len(yyyymmdd) == 8:
        return yyyymmdd[2:]
    return yyyymmdd


def build_mine2nemo_code(prefix: str, sample_code: str) -> tuple[str, str | None]:
    """`MV HCC_20260517_N3` + prefix='CC' → ('CC_260517_N3', '00:00').

    Returns:
        (mine2nemo_sample_code, sample_time) tuple
    """
    date_str, shift = _extract_date_shift(sample_code)
    if date_str is None or shift is None:
        return f"{prefix}_{sample_code}", None
    yymmdd = _date_yymmdd(date_str)
    sample_time = SHIFT_TIME_MAP.get(shift)
    return f"{prefix}_{yymmdd}_{shift}", sample_time

# Primary/Secondary categories (CC/TC implementation-д хэрэглэгдэнэ)
PRIMARY_CATEGORY_ID = "bfcdaacb-feea-438c-a5a2-15adb5893f24"   # Primary Product /CC/
SECONDARY_CATEGORY_ID = "3e50f369-f755-4a52-86bf-866d9f8261f9"  # Secondary Product /TC/


def _extract_basename(sample_code: str) -> str:
    """`PF211_20260312_D6` → `PF211`.

    Sample code-ийн формат: <basename>_<YYYYMMDD>_<shift_code>
    Suffix-ыг хасан basename-ыг буцаана.
    """
    # Сүүлийн 2 underscore-ын өмнөх хэсэг = basename
    parts = sample_code.rsplit("_", 2)
    if len(parts) >= 3 and parts[1].isdigit() and len(parts[1]) >= 6:
        return parts[0]
    return sample_code  # Suffix байхгүй эсвэл format taarakhgui


def route_to_mine2nemo(client_name: str, sample_type: str, sample_code: str) -> dict | None:
    """Дээжийг Mine2NEMO-ийн зөв table-руу route хийх.

    Sample code format: <basename>_<YYYYMMDD>_<shift>
        PF211_20260312_D6     → basename "PF211"
        UHG MASHCC_2_20260312_D6 → basename "UHG MASHCC_2"

    Returns:
        Routing info dict {"table": ..., "date_table": ..., "group_name": ...}
        Эсвэл None — Mine2NEMO-руу очих ёсгүй дээж бол.
    """
    # Одоогоор зөвхөн CHPP/2 hourly дээж
    if client_name != "CHPP" or sample_type != "2 hourly":
        return None

    if not sample_code:
        return None

    basename = _extract_basename(sample_code)

    # Plant Feed (PF211/221/231) — sample_code хэвээр (PF211_<date>_<shift>)
    if basename in PF_GROUP_INFO:
        group_name, category_id = PF_GROUP_INFO[basename]
        date_str, shift = _extract_date_shift(sample_code)
        # PF-д ч SampleCode rewrite — Mine2NEMO 6-digit date convention
        if date_str and shift:
            yymmdd = _date_yymmdd(date_str)
            mine2nemo_code = f"{basename}_{yymmdd}_{shift}"
            sample_time = SHIFT_TIME_MAP.get(shift)
        else:
            mine2nemo_code = sample_code
            sample_time = None
        return {
            "table": TABLE_PLANT_FEED,
            "date_table": TABLE_PLANT_FEED_DATE,
            "group_name": group_name,
            "category_id": category_id,
            "mine2nemo_code": mine2nemo_code,
            "sample_time": sample_time,
        }

    # Clean Coal (Primary) — бүх CC бүтээгдэхүүн нэг "CC_<date>_<shift>" нэр-руу
    if basename in CC_NAMES:
        mine2nemo_code, sample_time = build_mine2nemo_code("CC", sample_code)
        return {
            "table": TABLE_PRIMARY,
            "date_table": TABLE_PRIMARY_DATE,
            "group_name": None,
            "category_id": PRIMARY_CATEGORY_ID,
            "mine2nemo_code": mine2nemo_code,
            "sample_time": sample_time,
        }

    # Thermal Coal (Secondary) — бүх TC бүтээгдэхүүн "TC_<date>_<shift>" нэр-руу
    if basename in TC_NAMES:
        mine2nemo_code, sample_time = build_mine2nemo_code("TC", sample_code)
        return {
            "table": TABLE_SECONDARY,
            "date_table": TABLE_SECONDARY_DATE,
            "group_name": None,
            "category_id": SECONDARY_CATEGORY_ID,
            "mine2nemo_code": mine2nemo_code,
            "sample_time": sample_time,
        }

    return None  # Mapping олдсонгүй — дээж Mine2NEMO-д ороогүй
