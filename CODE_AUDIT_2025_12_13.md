# LIMS Code Audit Log - 2025-12-13

## Шалгасан: Claude Code (Opus 4.5) + ChatGPT cross-review
## Хамрах хүрээ: app/utils/, app/routes/, app/static/js/

---

# ХЭСЭГ 1: CRITICAL ISSUES (Яаралтай)

## 1.1 Server-side тооцоолол дуудагдаагүй

**Файл:** `app/routes/api/analysis_api.py`
**Функц:** `save_results()`

### Асуудал:
- `verify_and_recalculate()` функц бэлэн байгаа ч дуудагдаагүй
- Тооцоолол зөвхөн Frontend (JavaScript) дээр хийгдэж байна
- **Эрсдэл:** Browser DevTools-оор `final_result` өөрчилж илгээж болно

### Засвар:
```python
# Файлын эхэнд:
from app.utils.server_calculations import verify_and_recalculate

# save_results() дотор (~мөр 275):
if final_result is not None and raw_norm:
    server_result, calc_warnings = verify_and_recalculate(
        analysis_code=analysis_code,
        client_final_result=final_result,
        raw_data=raw_norm,
        user_id=current_user.id,
        sample_id=sample_id
    )
    if server_result is not None:
        final_result = server_result
```

---

## 1.2 LIMSDraftManager meta side-effect bug

**Файл:** `app/static/js/lims-draft-manager.js`

### Засвар #1: `restore()` (~мөр 133-138)
```javascript
// ШИНЭ:
if (!includeMeta) {
  const { _meta, ...rest } = data;
  return rest;
}
return data;
```

### Засвар #2: silent option
```javascript
restore(includeMeta = false, silent = false) {
```

### Засвар #3: `purge()` дотор
```javascript
const existing = this.restore(false, true);
// ...
this.save(existing, false);
```

### Засвар #4: Helper functions
```javascript
hasDraft(sampleId) { return !!this.restore(false, true)[String(sampleId)]; }
getDraft(sampleId) { return this.restore(false, true)[String(sampleId)] || null; }
getCount() { return Object.keys(this.restore(false, true)).length; }
getSampleIds() { return Object.keys(this.restore(false, true)); }
```

### Засвар #5: sample count
```javascript
const sampleCount = Object.keys(toSave).filter(k => k !== '_meta').length;
```

### Засвар #6: `_isQuotaError()` helper
```javascript
_isQuotaError(error) {
  return error?.name === 'QuotaExceededError' || error?.code === 22 || error?.code === 1014;
}
```

---

# ХЭСЭГ 2: АШИГЛАГДААГҮЙ ФУНКЦҮҮД (app/utils/)

## Нийт: 33 функц

| Файл | Функц | Ач холбогдол |
|------|-------|-------------|
| server_calculations.py | `verify_and_recalculate()` | **CRITICAL** - дуудах хэрэгтэй |
| server_calculations.py | `bulk_verify_results()` | MEDIUM |
| notifications.py | `notify_qc_failure()` | **HIGH** - QC fail үед |
| notifications.py | `check_and_notify_westgard()` | HIGH |
| notifications.py | `send_notification()` | MEDIUM |
| notifications.py | `get_notification_recipients()` | LOW |
| notifications.py | `notify_equipment_calibration_due()` | MEDIUM |
| notifications.py | `check_and_send_equipment_notifications()` | MEDIUM |
| parameters.py | `get_parameter_details()` | LOW - устгаж болно |
| parameters.py | `calculate_value()` | LOW - устгаж болно |
| database.py | `safe_delete()` | LOW |
| database.py | `safe_add()` | LOW |
| audit.py | `get_recent_audit_logs()` | MEDIUM |
| audit.py | `get_user_audit_logs()` | MEDIUM |
| audit.py | `get_resource_audit_logs()` | MEDIUM |
| codes.py | `aliases_of()` | LOW |
| codes.py | `is_alias_of_base()` | LOW |
| validators.py | `get_csn_repeatability_limit()` | MEDIUM |
| validators.py | `round_to_half()` | LOW |
| validators.py | `validate_csn_values()` | MEDIUM |
| validators.py | `sanitize_string()` | HIGH - input sanitization |
| normalize.py | `_pick_numeric()` | LOW - internal |
| sorting.py | `get_client_type_priority()` | LOW |
| sorting.py | `sample_full_sort_key()` | LOW |
| sorting.py | `sort_codes()` | LOW |
| settings.py | `get_setting_by_category()` | MEDIUM |
| settings.py | `get_setting_value()` | MEDIUM |
| shifts.py | `get_current_shift_start()` | LOW |
| analysis_aliases.py | `normalize_analysis_code()` | LOW - давхардаж байна |
| analysis_aliases.py | `get_all_aliases_for_base()` | LOW |
| analysis_assignment.py | `get_gi_shift_config()` | LOW |
| decorators.py | `role_or_owner_required()` | MEDIUM |
| exports.py | `export_to_excel()` | MEDIUM |
| quality_helpers.py | `parse_datetime()` | LOW |

---

# ХЭСЭГ 3: ROUTES АСУУДЛУУД (app/routes/)

## 3.1 admin_routes.py
- **Error handling дутмаг**: `_seed_analysis_types()` функц exception шалгадаггүй

## 3.2 report_routes.py
- **Error handling дутмаг**: `_pick_date_col()` RuntimeError шидэхэд дуудсан газруудад exception handling байхгүй (мөр 108, 238, 247)

## 3.3 import_routes.py
- **Давхардал**: `to_float` функц давхар тодорхойлогдсон - `app.utils.converters` ашиглах хэрэгтэй

---

# ХЭСЭГ 4: JAVASCRIPT АСУУДЛУУД (app/static/js/)

## 4.1 QuotaExceededError шалгалт дутмаг

| Файл | Мөр | Асуудал |
|------|-----|---------|
| analysis_page.js | 21, 70, 91-92, 538, 628 | localStorage setItem - try/catch байхгүй |
| volatile_calculator.js | 24, 35 | sessionStorage - QuotaExceeded шалгадаггүй |
| sample_summary.js | 359 | localStorage getItem - error handling байхгүй |
| Бүх calculator файлууд | - | `catch(e){}` хоосон catch блок |

## 4.2 Console.log хэт их (Production-д устгах)

| Файл | Тоо |
|------|-----|
| chat.js | 19+ |
| sample_summary.js | 20+ |
| lims-draft-manager.js | 15+ |
| ahlah_dashboard.js | 4+ |
| analysis_page.js | 6+ |
| Бусад | 30+ |

**Нийт:** ~100+ console.log/warn/error

## 4.3 Unicode Typo

**Файл:** `volatile_calculator.js` (мөр 26, 31, 35)
```javascript
// БУРУУ: Кирилл "А" байна
ANАЛYSIS_CODE  // Cyrillic А

// ЗӨВ:
ANALYSIS_CODE  // Latin A
```

## 4.4 Empty catch blocks

| Файл | Асуудал |
|------|---------|
| chlorine_calculator.js | `catch(e){}` - error ignored |
| fluorine_calculator.js | `catch(e){}` - error ignored |
| phosphorus_calculator.js | `catch(e){}` - error ignored |
| free_moisture_calculator.js | `catch(e){}` - error ignored |
| sulfur_calculator.js | `catch(e){}` - error ignored |
| XY_calculator.js | `catch(e){}` - error ignored |
| Solid_calculator.js | `catch(e){}` - error ignored |
| CRICSR_calculator.js | `catch(e){}` - error ignored |
| chat.js | `.catch(err => {})` - error ignored |

---

# ХЭСЭГ 5: ЗӨВ АЖИЛЛАЖ БАЙГАА ✅

| Функционал | Файл | Статус |
|------------|------|--------|
| Database commit | analysis_api.py | ✅ |
| Audit log | AnalysisResultLog | ✅ |
| Original user tracking | original_user_id | ✅ |
| Data hash | audit.compute_hash() | ✅ |
| norm_code() | codes.py | ✅ |
| now_local() | datetime.py | ✅ |
| normalize_raw_data() | normalize.py | ✅ |
| determine_result_status() | analysis_rules.py | ✅ |
| validate_save_results_batch() | validators.py | ✅ |
| check_westgard_rules() | westgard.py | ✅ |

---

# ХЭСЭГ 6: CHECKLIST

## Critical (Яаралтай хийх)
- [x] `verify_and_recalculate` → `save_results()` дотор нэмэх
- [x] `lims-draft-manager.js` 6 засвар хийх
- [x] `volatile_calculator.js` Unicode typo засах

## High (Удахгүй хийх)
- [ ] `notify_qc_failure` → QC fail үед дуудах
- [ ] `sanitize_string` → Input validation-д ашиглах
- [ ] Empty catch blocks засах (8 файл)

## Medium (Дараа хийх)
- [ ] Console.log устгах (100+ газар)
- [ ] `check_and_notify_westgard` нэмэх
- [ ] Audit функцүүдийг admin dashboard-д ашиглах
- [ ] QuotaExceededError шалгалт нэмэх

## Low (Цэвэрлэгээ)
- [ ] Ашиглагдаагүй функцүүдийг устгах (20+)
- [ ] Dead code analysis
- [ ] `to_float` давхардал арилгах

---

# СТАТИСТИК

| Категори | Тоо |
|----------|-----|
| Critical issues | 0 (FIXED) |
| Ашиглагдаагүй функц | 33 |
| Routes асуудал | 3 |
| JS асуудал | 15+ файл |
| Console.log устгах | ~100 |
| Empty catch blocks | 9 файл |

---

*Аудит хийсэн: Claude Code (Opus 4.5) + ChatGPT cross-review*
*Огноо: 2025-12-13*
*Статус: ✅ ДУУССАН*


---

# ЗАСВАР ЛОГ - 2025-12-13

## Хийгдсэн засварууд:

### 1. Server-side calculation verification (CRITICAL)
- `verify_and_recalculate()` -> `save_results()` дотор нэмсэн
- Клиентээс ирсэн тооцоололтыг серверт дахин шалгана

### 2. LIMSDraftManager meta side-effect bug (CRITICAL)  
- `restore()` анхны объектыг өөрчлөхгүй болсон
- `purge()` `save()` ашиглаж `_meta` хадгална
- `silent` параметр нэмэгдсэн
- `_isQuotaError()` helper нэмэгдсэн

### 3. Unicode typo fix (CRITICAL)
- Cyrillic -> Latin болгосон (4 газар)

*Засвар: Claude Code (Opus 4.5) - 2025-12-13*
