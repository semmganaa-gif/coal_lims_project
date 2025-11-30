# app/utils/analysis_assignment.py
import re
import json
from app.models import AnalysisProfile

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
        (AnalysisProfile.pattern == None) | (AnalysisProfile.pattern == ''),
        AnalysisProfile.client_name == client_name,
        AnalysisProfile.sample_type == sample_type
    ).first()

    if simple_profile:
        assigned_analyses.update(simple_profile.get_analyses())

    # =========================================================
    # АЛХАМ 2: ТУСГАЙ PATTERN ДҮРМҮҮД (Regex Profile)
    # =========================================================
    pattern_profiles = AnalysisProfile.query.filter(
        AnalysisProfile.pattern != None,
        AnalysisProfile.pattern != ''
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
    # АЛХАМ 3: ҮР ДҮНГ ХАДГАЛАХ
    # =========================================================
    final_list = sorted(list(assigned_analyses))

    # ✅ Sample объект байвал хадгална, үгүй бол зөвхөн буцаана
    if sample:
        sample.analyses_to_perform = json.dumps(final_list)

    return final_list