# app/utils/analysis_assignment.py
import re
import json
import logging
from sqlalchemy.exc import SQLAlchemyError
from app.models import AnalysisProfile, SystemSetting

# Default Gi shift config (fallback)
DEFAULT_GI_SHIFT_CONFIG = {
    'PF211': ['D1', 'D3', 'D5', 'N1', 'N3', 'N5'],
    'PF221': ['D2', 'D4', 'D6', 'N2', 'N4', 'N6'],
    'PF231': ['D1', 'D3', 'D5', 'N1', 'N3', 'N5'],
}


def get_gi_shift_config():
    """DB-ээс Gi ээлжийн тохиргоог унших, байхгүй бол default."""
    try:
        setting = SystemSetting.query.filter_by(
            category='gi_shift', key='config'
        ).first()
        if setting and setting.value:
            return json.loads(setting.value)
    except (json.JSONDecodeError, TypeError, OSError, SQLAlchemyError) as e:
        logging.warning(f"Gi shift config load error: {e}")
    return DEFAULT_GI_SHIFT_CONFIG


def assign_analyses_to_sample(sample=None, client_name=None, sample_type=None,
                               sample_code=None, sample_condition=None):
    """
    Дээж (Sample) объект ЭСВЭЛ тусдаа параметрүүд дамжуулж шинжилгээ оноох.

    ✅ САЙЖРУУЛСАН: Fake объект үүсгэх шаардлагагүй болсон!

    Args:
        sample: Sample объект (хэрэв байгаа бол)
        client_name: Үйлчлүүлэгчийн нэр (sample байхгүй үед)
        sample_type: Дээжний төрөл (sample байхгүй үед)
        sample_code: Дээжний код (sample байхгүй үед)
        sample_condition: Дээжний төлөв (sample байхгүй үед)

    Returns:
        list: Оногдсон шинжилгээний жагсаалт

    Жишээ:
        # Sample объекттой:
        assign_analyses_to_sample(sample)

        # Тусдаа параметрүүдтэй (preview-д):
        assign_analyses_to_sample(
            client_name="CHPP",
            sample_type="2H",
            sample_code="PF211_D1"
        )
    """

    # ✅ Параметрүүдийг тодорхойлох
    if sample:
        client_name = sample.client_name
        sample_type = sample.sample_type
        sample_code = sample.sample_code
        sample_condition = getattr(sample, 'sample_condition', None)

    assigned_analyses = set()

    # =========================================================
    # АЛХАМ 1: ЭНГИЙН МАТРИЦ ДҮРЭМ (Simple Profile)
    # =========================================================
    simple_profile = AnalysisProfile.query.filter(
        (AnalysisProfile.pattern.is_(None)) | (AnalysisProfile.pattern == ''),
        AnalysisProfile.client_name == client_name,
        AnalysisProfile.sample_type == sample_type
    ).first()

    if simple_profile:
        assigned_analyses.update(simple_profile.get_analyses())

    # =========================================================
    # АЛХАМ 2: ТУСГАЙ PATTERN ДҮРМҮҮД (Regex Profile)
    # =========================================================
    # ✅ ЗАСВАР: Зөвхөн тухайн client_name, sample_type-д хамаарах pattern профайлуудыг авах
    pattern_profiles = AnalysisProfile.query.filter(
        AnalysisProfile.pattern.isnot(None),
        AnalysisProfile.pattern != '',
        AnalysisProfile.client_name == client_name,
        AnalysisProfile.sample_type == sample_type
    ).order_by(AnalysisProfile.priority.asc()).all()

    # Дээжний нэр болон төлөвийг бэлдэх
    sample_code_str = str(sample_code or "").strip()
    sample_cond_str = str(sample_condition or "").strip()

    for profile in pattern_profiles:
        is_match = False
        pattern = profile.pattern.strip()

        try:
            # 1. Дээжний НЭРЭЭС хайх (PF211, PF221 гэх мэт)
            if re.search(pattern, sample_code_str, re.IGNORECASE):
                is_match = True

            # 2. ✅ ШИНЭ: Дээжний ТӨЛӨВӨӨС хайх (Шингэн, Чийгтэй)
            elif sample_cond_str and re.search(pattern, sample_cond_str, re.IGNORECASE):
                is_match = True

        except re.error:
            # Fallback: Энгийн текст хайлт
            if pattern.lower() in sample_code_str.lower():
                is_match = True
            elif pattern.lower() in sample_cond_str.lower():
                is_match = True

        if is_match:
            new_analyses = profile.get_analyses()
            rule = getattr(profile, 'match_rule', 'merge')

            if rule == 'replace':
                assigned_analyses = set(new_analyses)
            else:
                assigned_analyses.update(new_analyses)

    # =========================================================
    # АЛХАМ 3: Gi ЭЭЛЖИЙН ДҮРЭМ (PF211/PF221/PF231)
    # =========================================================
    # DB-ээс тохиргоог унших, байхгүй бол default:
    # PF211, PF231 → D1,D3,D5,N1,N3,N5 (сондгой)
    # PF221 → D2,D4,D6,N2,N4,N6 (тэгш)
    if sample_code_str and 'Gi' in assigned_analyses:
        sample_upper = sample_code_str.upper()

        # ✅ Ээлжийн кодыг дээжний нэрнээс олох (хаана ч байж болно)
        # Форматууд: _D1, _N2, D1, N2, _D1_, D1_ гэх мэт
        shift_match = re.search(r'[_]?([DN])(\d)[_]?', sample_upper)
        if shift_match:
            current_shift = shift_match.group(1) + shift_match.group(2)  # D1, N2 гэх мэт

            # ✅ DB-ээс Gi shift тохиргоог унших
            gi_config = get_gi_shift_config()

            # ✅ PF pattern шалгах
            matched_pf = None
            for pf_code in gi_config.keys():
                if pf_code.upper() in sample_upper:
                    matched_pf = pf_code
                    break

            if matched_pf:
                allowed_shifts = gi_config.get(matched_pf, [])
                allowed_upper = [s.upper() for s in allowed_shifts]

                if current_shift not in allowed_upper:
                    # ✅ Энэ ээлжинд Gi хийх ёсгүй - устгах
                    assigned_analyses.discard('Gi')
                    logging.info(f"Gi REMOVED from {sample_code_str}: shift {current_shift} not in {allowed_upper}")
                else:
                    logging.info(f"Gi KEPT for {sample_code_str}: shift {current_shift} in {allowed_upper}")

    # =========================================================
    # АЛХАМ 4: ҮР ДҮНГ ХАДГАЛАХ
    # =========================================================
    final_list = sorted(list(assigned_analyses))

    # ✅ Sample объект байвал хадгална, үгүй бол зөвхөн буцаана
    if sample:
        sample.analyses_to_perform = json.dumps(final_list)

    return final_list
