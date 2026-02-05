# Analysis Workspace Code Audit
**Огноо:** 2026-02-05
**Хамрах хүрээ:** Шинжилгээний ажлын талбар, API, үр дүн хадгалах логик

---

## 1. Бүтцийн тойм

### 1.1 Үндсэн файлууд
| Файл | Мөрийн тоо | Үүрэг |
|------|------------|-------|
| `app/routes/api/analysis_api.py` | 891 | Шинжилгээний үр дүн хадгалах API |
| `app/routes/analysis/workspace.py` | 337 | Ажлын хуудас routes |
| `app/routes/analysis/senior.py` | 499 | Ахлахын хяналт routes |
| `app/utils/analysis_rules.py` | 172 | Статус тодорхойлох дүрмүүд |
| `app/utils/server_calculations.py` | 994 | Серверт тооцоолол шалгах |

### 1.2 Template файлууд (17 ширхэг)
| Файл | Шинжилгээ |
|------|-----------|
| `mad_aggrid.html` | Аналитик чийг |
| `ash_form_aggrid.html` | Үнс |
| `vad_aggrid.html` | Дэгдэмхий |
| `mt_aggrid.html` | Нийт чийг |
| `sulfur_aggrid.html` | Хүхэр |
| `cv_aggrid.html` | Илчлэг |
| `csn_aggrid.html` | Кокс хийх чадвар |
| `Gi_aggrid.html` | Gray-King |
| `trd_aggrid.html` | TRD |
| `phosphorus_aggrid.html` | Фосфор |
| `fluorine_aggrid.html` | Фтор |
| `chlorine_aggrid.html` | Хлор |
| `xy_aggrid.html` | X, Y шинжилгээ |
| `cricsr_aggrid.html` | CRI/CSR |
| `solid_aggrid.html` | Хатуу үлдэгдэл |
| `free_moisture_aggrid.html` | Гадаргын чийг |
| `mass_aggrid.html` | Жин |

---

## 2. CRITICAL асуудлууд (2)

### 2.1 ⚠️ Audit Log Hash дутуу хадгалалт
**Байршил:** `app/routes/analysis/senior.py:181-194`
**Түвшин:** CRITICAL

```python
# senior.py - update_result_status()
audit = AnalysisResultLog(
    timestamp=now_local(),
    user_id=current_user.id,
    # ... fields ...
)
db.session.add(audit)  # ← data_hash тооцоолоогүй!
```

**Харьцуулалт:** `analysis_api.py:646-648` - Hash зөв хадгалсан:
```python
audit.data_hash = audit.compute_hash()
db.session.add(audit)
```

**Нөлөө:** ISO 17025 аудит бүрэн бүтэн байдал алдагдана.

---

### 2.2 ⚠️ Bulk update-д hash дутуу
**Байршил:** `app/routes/analysis/senior.py:271-284`
**Түвшин:** CRITICAL

```python
# bulk_update_status()
audit = AnalysisResultLog(
    # ... fields ...
)
db.session.add(audit)  # ← data_hash тооцоолоогүй!
```

---

## 3. MAJOR асуудлууд (4)

### 3.1 CSN тусгай хандлага дутуу
**Байршил:** `app/utils/analysis_rules.py:138-140`
**Түвшин:** MAJOR

```python
# CSN хэрэглэхгүй бол pending_review болгох ёстой, одоо шууд approved болж байна
if analysis_code == 'Gi':
    if raw_data.get("is_low_avg", False):
        return "rejected", "GI_RETEST_3_3"
# CSN дүрэм байхгүй!
```

**Шийдэл:** CSN-д тусгай дүрэм нэмэх (index 0-9 утгуудыг шалгах)

---

### 3.2 Tolerance Epsilon зөрүү
**Байршил:**
- `app/routes/api/analysis_api.py:346` - `EPSILON = 1e-6`
- `app/utils/server_calculations.py:33` - `EPSILON = 0.01`

**Асуудал:** 2 газарт өөр утга ашиглаж байна. 0.01% (server) нь хэт өргөн.

---

### 3.3 Template давхардал (~13,000+ мөр)
**Байршил:** `app/templates/analysis_forms/*.html`
**Түвшин:** MAJOR (засвар хэцүү)

17 template файл ихэнх хэсэг ижил (AG-Grid тохиргоо, toolbar, modal):
- AG-Grid setup: ~200 мөр x 17 = 3,400 мөр
- Toolbar buttons: ~100 мөр x 17 = 1,700 мөр
- Modal dialogs: ~150 мөр x 17 = 2,550 мөр
- Save/Submit logic: ~300 мөр x 17 = 5,100 мөр

**Санал:** `_analysis_base.html` macro/include үүсгэх

---

### 3.4 CV нэгж тодорхойгүй
**Байршил:** `app/utils/server_calculations.py`
**Түвшин:** MAJOR

```python
# CV тооцоолол байхгүй - calc_cv() функц дутуу
# Калориметрийн тооцоолол GBW болон CM-д өөр нэгжтэй:
# - CM: kcal/kg
# - GBW: MJ/kg
```

---

## 4. MODERATE асуудлууд (6)

### 4.1 rejection_comment XSS риск
**Байршил:** `app/routes/api/analysis_api.py:520, 713`
**Түвшин:** MODERATE

```python
reason = status_reason if status_reason else (item.get("rejection_comment") or "Химич хадгалсан")
# rejection_comment escape хийгээгүй
```

**Засах:** `from markupsafe import escape` ашиглах

---

### 4.2 Equipment validation дутуу
**Байршил:** `app/routes/api/analysis_api.py:316-317`
**Түвшин:** MODERATE

```python
equipment_id_raw = item.get("equipment_id")
equipment_id, _ = validate_equipment_id(equipment_id_raw, allow_none=True)
# equipment_id байгаа эсэхийг шалгахгүй (exists check missing)
```

---

### 4.3 sample_state defensive check үлдсэн
**Байршил:** `app/routes/analysis/workspace.py` - Засагдсан
**Статус:** ✅ Шийдэгдсэн (samples_api.py дээр)

---

### 4.4 Error handling хэт ерөнхий
**Байршил:** `app/routes/analysis/senior.py:287-289`
**Түвшин:** MODERATE

```python
except (ValueError, Exception):  # ← Exception нь ValueError-г агуулна
    failed_ids.append(rid)
    continue  # Log байхгүй
```

---

### 4.5 Async await дутуу
**Байршил:** `app/routes/api/analysis_api.py` (бүх async route)
**Түвшин:** MODERATE (Ирээдүйд засах)

```python
async def eligible_samples(analysis_code):
    # ... await asyncio.to_thread() зөв ашигласан
```

**Статус:** ✅ Зөв хэрэгжүүлсэн (asyncio.to_thread ашигласан)

---

### 4.6 N+1 query potential
**Байршил:** `app/routes/analysis/workspace.py:92-101`
**Статус:** ✅ Шийдэгдсэн (joinedload ашигласан)

```python
existing_results = (
    AnalysisResult.query
    .options(joinedload(AnalysisResult.sample))  # ✅ Зөв!
    # ...
)
```

---

## 5. LOW түвшний асуудлууд (8)

| # | Асуудал | Байршил |
|---|---------|---------|
| 1 | Template нэр inconsistent (`Gi_aggrid` vs `chlorine_aggrid`) | templates/analysis_forms/ |
| 2 | Magic numbers (2SD, 1SD limits) | analysis_rules.py:121-127 |
| 3 | Шаардлагагүй import json давхардал | workspace.py:9, senior.py:15 |
| 4 | hasattr checks шаардлагагүй | senior.py:162-174 |
| 5 | Timer config hardcoded | workspace.py:284-289 |
| 6 | form_map dict бүртгэл дутуу | workspace.py:266-277 |
| 7 | Log level буруу (warning instead of info) | workspace.py:77-83 |
| 8 | original_user_id/timestamp олох логик давхардал | analysis_api.py:611-625 |

---

## 6. Засах дараалал

### Яаралтай (CRITICAL) - ДУУССАН ✅
1. ✅ `senior.py:update_result_status()` - `audit.data_hash = audit.compute_hash()` нэмсэн
2. ✅ `senior.py:bulk_update_status()` - `audit.data_hash = audit.compute_hash()` нэмсэн

### Дунд хугацаа (MAJOR) - ДУУССАН ✅
3. ✅ CSN дүрэм нэмэх - `analysis_rules.py` (0-9 range, parallel diff check)
4. ✅ EPSILON нэр тодруулалт - `FLOAT_TOLERANCE`, `CALC_MISMATCH_ABS_THRESHOLD`
5. ✅ Template macro сайжруулалт - `aggrid_macros.html` (col_*, draft_manager_init, sample_id_persistence)
6. ✅ CV нэгж тодорхойлох - `server_calculations.py` (cv_cal_to_mj, cv_mj_to_cal, unit parameter)

### Бусад (MODERATE) - ДУУССАН ✅
7. ✅ rejection_comment XSS escape - `analysis_api.py`, `senior.py`
8. ✅ Equipment exists check нэмэх - `analysis_api.py`
9. ✅ Error handling сайжруулах + logging - `senior.py:bulk_update_status()`

---

## 7. Архитектурын сайжруулалт (Ирээдүйд)

### 7.1 Template Base Class
```html
<!-- app/templates/analysis_forms/_base_aggrid.html -->
{% macro analysis_grid(analysis_code, columns, options={}) %}
<div id="ag-grid-container" class="ag-theme-alpine"></div>
<script>
const gridOptions = {
    columnDefs: {{ columns | tojson }},
    // ... common settings
};
</script>
{% endmacro %}
```

### 7.2 Analysis Rules Engine
```python
# app/utils/analysis_rules.py - Шинэ бүтэц
class AnalysisRuleEngine:
    def __init__(self, analysis_code: str):
        self.code = analysis_code
        self.rules = self._load_rules()

    def evaluate(self, value, raw_data, control_targets=None) -> Tuple[str, str]:
        for rule in self.rules:
            status, reason = rule.check(value, raw_data, control_targets)
            if status != "continue":
                return status, reason
        return "approved", None
```

### 7.3 Unified Audit Logger
```python
# app/utils/audit.py - Шинэ функц
def log_analysis_audit(
    result: AnalysisResult,
    action: str,
    user_id: int,
    reason: str = None,
    extra: dict = None
) -> AnalysisResultLog:
    """
    Unified audit log creator with automatic hash computation.
    """
    audit = AnalysisResultLog(
        timestamp=now_local(),
        user_id=user_id,
        sample_id=result.sample_id,
        analysis_result_id=result.id,
        analysis_code=result.analysis_code,
        action=action,
        raw_data_snapshot=result.raw_data,
        final_result_snapshot=result.final_result,
        reason=reason,
        **(extra or {})
    )
    audit.data_hash = audit.compute_hash()
    return audit
```

---

## 8. Тест хийх хэсгүүд

### 8.1 Unit Tests шаардлагатай
- [ ] `analysis_rules.py` - determine_result_status()
- [ ] `server_calculations.py` - calc_moisture_mad(), calc_ash_aad() гэх мэт
- [ ] `analysis_api.py` - tolerance calculation

### 8.2 Integration Tests
- [ ] Save results → Status determination flow
- [ ] Control sample (CM/GBW) → Dry basis conversion
- [ ] Bulk approve/reject → Audit log integrity

---

*Шинжилгээг хийсэн: Claude Code*
*Огноо: 2026-02-05*
