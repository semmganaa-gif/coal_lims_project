# app/utils/conversions.py
# Энэ бол бүх 'ar', 'd', 'daf' ба FC зэрэг хувиргалтын тооцооллыг хийдэг “хөдөлгүүр”.

from app.utils.parameters import calculate_value as calculate_parameter_value


def calculate_all_conversions(raw_canonical_results, param_definitions):
    """
    Нэг дээжийн “түүхий” (ихэвчлэн ad) үр дүнг аваад,
    боломжит бүх төлөв (ar, d, daf) болон FC (fixed carbon)-ийг тооцоолно.
    - Оролт: raw_canonical_results нь каноник түлхүүрүүдтэй dict
      (утга нь тоо эсвэл {'value': x, ...} хэлбэртэй байж болно)
    - Гаралт: түүхий + тооцоолсон бүх утгуудыг агуулсан dict
    """
    final_results = raw_canonical_results.copy()

    def get_float_from_raw(key):
        """raw_canonical_results-оос утгыг аюулгүй авч, float болгоно."""
        data = raw_canonical_results.get(key)
        if isinstance(data, dict):
            val = data.get('value')
        else:
            val = data
        if val is None or val == 'null':
            return None
        try:
            return float(str(val).replace(',', '').strip())
        except (ValueError, TypeError):
            return None

    def get_float_from_any(key):
        """final_results эсвэл raw-аас (аль нь тоо/dict байна түүнийгээ) унших дэмжлэг."""
        v = final_results.get(key)
        if v is None:
            v = raw_canonical_results.get(key)
        if isinstance(v, dict):
            v = v.get('value')
        if v is None or v == 'null':
            return None
        try:
            return float(str(v).replace(',', '').strip())
        except (ValueError, TypeError):
            return None

    # 1) Үндсэн түлхүүрүүд
    M_ad = get_float_from_raw('inherent_moisture')   # Mad (ad)
    A_ad = get_float_from_raw('ash')                 # Aad (ad)
    M_t  = get_float_from_raw('total_moisture')      # Mt,ar
    H_ad = get_float_from_raw('hydrogen')            # H (ad)
    V_ad = get_float_from_raw('volatile_matter')     # Vad (ad)  # noqa: F841

    # 2) FC,ad (parameters.py: fixed_carbon_ad)
    simple_raw_values = {k: get_float_from_raw(k) for k in raw_canonical_results}
    fc_ad_value = calculate_parameter_value('fixed_carbon_ad', simple_raw_values)
    if fc_ad_value is not None:
        final_results['fixed_carbon_ad'] = fc_ad_value

    # (!!! ШИНЭ)
    # 3) ⚠️ TRD (Нягт) тусгай тохиолдол:
    # JS тооцоологч нь "TRD,d" (хуурай)-г тооцоолоод "relative_density" гэсэн
    # үндсэн (ad) түлхүүр дээр хадгалж байна.
    # Бид үүнийг засаж, "relative_density" (ad)-г тооцоолж,
    # "relative_density_d" (d) рүү хуучин утгыг нь зөөнө.
    TRD_d_val = get_float_from_raw('relative_density') # Энэ нь үнэндээ TRD,d
    if TRD_d_val is not None:
        # Эхлээд хуурай утгыг зөв түлхүүрт нь хийнэ
        final_results['relative_density_d'] = TRD_d_val
        
        # Одоо 'ad' (ажлын) утгыг тооцоолно
        if M_ad is not None:
            denom_ad = 100.0 - M_ad
            if denom_ad > 0: # 0-д хуваах, <0 байх алдаанаас хамгаална
                # TRD,ad = TRD,d * (100 - Mad) / 100
                TRD_ad_val = TRD_d_val * denom_ad / 100.0
                final_results['relative_density'] = TRD_ad_val # Үндсэн түлхүүрийг 'ad' утгаар дарж бичнэ
            else:
                # M_ad >= 100% бол 'ad' утга 0 байна
                final_results['relative_density'] = 0.0
        else:
            # M_ad байхгүй бол 'ad' утгыг тооцоолох боломжгүй.
            # 'relative_density' (ad) түлхүүрийг устгана, зөвхөн 'relative_density_d' үлдэнэ.
            if 'relative_density' in final_results:
                 del final_results['relative_density']
    
    # 4) Хувиргалтын коэффициентууд (өмнө нь 3 байсан)
    factor_d = None   # -> _d
    factor_daf = None # -> _daf
    factor_ar = None  # -> _ar

    if M_ad is not None:
        denom_d = 100.0 - M_ad
        if denom_d != 0:
            factor_d = 100.0 / denom_d
            if A_ad is not None:
                denom_daf = 100.0 - M_ad - A_ad
                if denom_daf != 0:
                    factor_daf = 100.0 / denom_daf

    if M_t is not None and M_ad is not None:
        denom_ad = 100.0 - M_ad
        if denom_ad != 0:
            factor_ar = (100.0 - M_t) / denom_ad

    # 5) PARAMETER_DEFINITIONS-ыг давтаж, _d/_daf/_ar хувиргалтууд (өмнө нь 4 байсан)
    for param_name, _data in list(final_results.copy().items()):
        details = param_definitions.get(param_name)
        if not details:
            continue
        bases = details.get('conversion_bases', [])
        if not bases:
            continue
        
        # (!!! ШИНЭЧЛЭЛ) TRD-г энд давхар хувиргахгүй (relative_density_d-г дахин ad болгох г.м)
        if param_name in ('relative_density', 'relative_density_d'):
            continue
            
        val_ad = get_float_from_any(param_name)  # зөвхөн value-г float болгож уншина
        if val_ad is None:
            continue

        if 'd' in bases and factor_d is not None:
            new_key = f"{param_name}_d"
            if param_definitions.get(new_key) is not None:
                final_results[new_key] = val_ad * factor_d

        if 'daf' in bases and factor_daf is not None:
            new_key = f"{param_name}_daf"
            if param_definitions.get(new_key) is not None:
                final_results[new_key] = val_ad * factor_daf

        if 'ar' in bases and factor_ar is not None:
            new_key = f"{param_name}_ar"
            if param_definitions.get(new_key) is not None:
                final_results[new_key] = val_ad * factor_ar

    # 6) Qnet,ar — ТАНЫ ӨГСӨН ТОМЪЁОГООР (cal/g суурь гэж үзэв) (өмнө нь 5 байсан)
    #
    # Qnet,ar = ((Qgr,ad*4.1868 - 206*(100 - Aad - Mad)*(0.059*Vdaf + 3.173)/100)
    #           * (100 - Mt,ar)/(100 - Mad) - 23*Mt,ar) / 4.1868
    #
    # Шаардлагатай оролтууд:
    #  - Qgr,ad  = calorific_value          (cal/g)
    #  - Aad     = ash                      (ad, %)
    #  - Mad     = inherent_moisture        (ad, %)
    #  - Vdaf    = volatile_matter_daf      (%, daf)  ← дээрх хувиргалтаар үүснэ
    #  - Mt,ar   = total_moisture           (ar, %)
    Qgr_ad = get_float_from_any('calorific_value')       # cal/g
    Aad    = get_float_from_any('ash')                   # %
    Mad    = get_float_from_any('inherent_moisture')     # %
    Mt_ar  = get_float_from_any('total_moisture')        # %
    Vdaf   = get_float_from_any('volatile_matter_daf')   # %

    qnet_ar_value = None
    try:
        if None not in (Qgr_ad, Aad, Mad, Mt_ar, Vdaf):
            denom = (100.0 - Mad)
            if denom != 0:
                term1 = Qgr_ad * 4.1868
                term2 = 206.0 * (100.0 - Aad - Mad) * (0.059 * Vdaf + 3.173) / 100.0
                term3 = (100.0 - Mt_ar) / denom
                qnet_ar_value = ((term1 - term2) * term3 - 23.0 * Mt_ar) / 4.1868
                final_results['qnet_ar'] = qnet_ar_value
    except Exception:
        # Аливаа тооцооны алдаа гарвал доорх fallback руу шилжинэ.
        qnet_ar_value = None

    # 6b) Fallback – хэрэв дээрх томъёонд шаардлагатай оролтууд дутвал хуучин томъёогоор
    #     (MNS ISO 1928:2009, J/g) тооцоод 'qnet_ar' тавина.
    if 'qnet_ar' not in final_results:
        Qgr_ar = get_float_from_any('calorific_value_ar')  # J/g байх магадлалтай гэж өмнө нь төсөөлж байсан
        H_ar   = get_float_from_any('hydrogen_ar')
        if Qgr_ar is not None and H_ar is not None and M_t is not None:
            # Qnet,ar = Qgr,ar − 21.22·H_ar − 2.45·M_t  (J/g, %, %)
            final_results['qnet_ar'] = Qgr_ar - (21.22 * H_ar) - (2.45 * M_t)

        # 🔎 Qnet,ar-д шаардлагатай орцын шалгалт (доголдол)
    dbg_inputs = {
        'Qgr_ad(calorific_value)': get_float_from_any('calorific_value'),
        'Aad(ash)':                get_float_from_any('ash'),
        'Mad(inherent_moisture)':  get_float_from_any('inherent_moisture'),
        'Mt,ar(total_moisture)':   get_float_from_any('total_moisture'),
        'Vdaf':                    get_float_from_any('volatile_matter_daf'),
    }

    have_any = any(v is not None for v in dbg_inputs.values())
    have_all = all(v is not None for v in dbg_inputs.values())

    # Зөвхөн “хэсэгчилсэн” үед (орцын зарим нь байна, гэхдээ бүгд нь биш) бөгөөд
    # qnet_ar хараахан үүсээгүй бол л хэвлэе:
    if have_any and not have_all and 'qnet_ar' not in final_results:
        missing = {k: v for k, v in dbg_inputs.items() if v is None}
        print('[QNET DEBUG] Missing inputs:', missing)


    return final_results