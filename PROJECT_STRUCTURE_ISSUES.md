# ТӨСЛИЙН БҮТЦИЙН АСУУДЛУУД / PROJECT STRUCTURE ISSUES

**Огноо / Date:** 2025-11-30
**Статус / Status:** Шинжилгээ хийгдэж байна / Analysis in Progress

---

## 1. АСУУДЛЫН НЭГДСЭН ЖАГСААЛТ / SUMMARY OF ISSUES

### 🔴 Ноцтой асуудлууд / Critical Issues

1. **Helpers файлууд 3 газар тархсан** - Нэг төрлийн функцүүд өөр өөр газар
2. **Audit систем хоёр** - Хоёр өөр audit систем давхцаж байна
3. **Файлын нэр агуулгатай нь тохирохгүй** - helpers.py гэсэн ч QC config байна

### 🟡 Дунд зэргийн асуудлууд / Medium Issues

4. **Config файлууд олон газар** - app/config болон app/utils-д
5. **BOM character** - app/routes/api/helpers.py файлд UTF-8 BOM байна
6. **Shift кодууд 2 газар** - main/helpers.py болон utils/shift_helper.py

### 🟢 Бага асуудлууд / Minor Issues

7. **Decorators тархсан** - analysis/helpers.py болон utils/decorators.py
8. **Database утилитиуд** - app/utils/database.py бие даасан

---

## 2. ДЭЛГЭРЭНГҮЙ ШИНЖИЛГЭЭ / DETAILED ANALYSIS

### A. HELPERS ФАЙЛУУД

#### 📁 app/routes/analysis/helpers.py (233 мөр, 8835 bytes)

**Агуулга:**
- QC Dashboard тогтмолууд (`QC_PARAM_CODES`, `QC_TOLERANCE`, `QC_SPEC_DEFAULT`)
- Composite QC тохиргоо (`COMPOSITE_QC_CODES`, `COMPOSITE_QC_LIMITS`)
- QC утилити функцүүд:
  - `_qc_to_date(dt)` - Огноо боловсруулалт
  - `_qc_split_family(sample_code)` - Дээжийн кодыг задлах
  - `_qc_is_composite(sample, slot)` - Composite эсэхийг шалгах
  - `_qc_check_spec(value, spec_tuple)` - Specification шалгалт
  - `_parse_numeric(val)` - Тоон утга задлах
  - `_eval_qc_status(param_code, diff, diff_pct)` - QC статус үнэлэлт
- Stream утилити:
  - `_split_stream_key(sample)` - Stream task-уудыг задлах
- Decorator:
  - `analysis_role_required(allowed_roles)` - Эрх шалгалт
- Sulfur mapping:
  - `_sulfur_map_for(sample_ids)` - Хүхрийн утгын map

**Асуудал:**
- Файлын нэр "helpers" гэсэн ч агуулга нь QC-ийн configuration!
- QC тогтмолууд `app/config/` фолдерт байх ёстой
- Утилити функцүүд `app/utils/qc.py` гэх мэтээр байх ёстой

#### 📁 app/routes/api/helpers.py (159 мөр, 6173 bytes)

**Агуулга:**
- Mass gate шалгалт:
  - `_requires_mass_gate(code)` - M task шаардлагатай эсэх
  - `_has_m_task_sql()` - SQL query generator
- Эрх шалгалт:
  - `_can_delete_sample()` - Устгах эрх
- Sample status:
  - `_aggregate_sample_status(sample_status, result_statuses)` - Төлөв нэгтгэх
- Repeatability шалгалт:
  - `_to_float_or_none(x)` - Float хөрвүүлэлт
  - `_coalesce_diff(raw_norm)` - Зөрүү тооцоолох
  - `_pick_rule(analysis_code)` - Repeatability rule сонгох
  - `_effective_limit(analysis_code, avg)` - Limit тооцоолох
  - `should_require_review(analysis_code, raw_norm)` - Review шаардлагатай эсэх

**Асуудал:**
- ⚠️ **UTF-8 BOM character** байна (U+FEFF)
- Repeatability логик `app/utils/repeatability.py`-д байх ёстой
- Permission check функцүүд `app/utils/permissions.py` эсвэл `security.py`-д байх ёстой

#### 📁 app/routes/main/helpers.py (36 мөр, 920 bytes)

**Агуулга:**
- Shift кодууд:
  - `get_12h_shift_code(dt)` - 12 цагийн ээлж (_D/_N)
  - `get_quarter_code(dt)` - Улирлын код (_Q1-_Q4)
- URL шалгалт:
  - `is_safe_url(target)` - Open redirect халдлагаас хамгаалах

**Асуудал:**
- Shift функцүүд `app/utils/shift_helper.py`-д ч байна (ДАВХАРДАЛ!)
- URL security `app/utils/security.py`-д байх ёстой

---

### B. AUDIT СИСТЕМ ХОЁР

#### 📁 app/routes/audit_log_service.py (102 мөр, 4184 bytes)

**Зориулалт:** AnalysisResultLog - Шинжилгээний үр дүнгийн audit trail

**Функцүүд:**
- `_to_jsonable(data)` - Dataclass → JSON
- `_safe_json_dumps(payload, limit_bytes)` - Safe JSON serialization (200KB limit)
- `log_analysis_action(...)` - Analysis үр дүнгийн өөрчлөлт бичих

**Модел:** `AnalysisResultLog`

#### 📁 app/utils/audit.py (162 мөр, 5583 bytes)

**Зориулалт:** AuditLog - Ерөнхий системийн audit trail (ISO 17025)

**Функцүүд:**
- `log_audit(action, resource_type, resource_id, details)` - Ерөнхий audit бичих
- `get_recent_audit_logs(limit, action)` - Сүүлийн логууд
- `get_user_audit_logs(user_id, limit)` - Хэрэглэгчийн логууд
- `get_resource_audit_logs(resource_type, resource_id, limit)` - Нөөцийн логууд

**Модел:** `AuditLog`

**Асуудал:**
- ✅ Хоёр өөр зорилготой тул **зөв**
- Гэхдээ `app/routes/audit_log_service.py` → `app/services/` эсвэл `app/utils/` руу зөөх ёстой
- Routes фолдерт service код байх нь буруу архитектур

---

### C. CONFIG ФАЙЛУУД

```
app/config/
├── __init__.py
├── analysis_schema.py       # Analysis validation schemas
├── display_precision.py     # Display formatting
└── repeatability.py         # Repeatability limits

app/utils/
├── analysis_assignment.py   # Analysis assignment logic (config?)
├── analysis_rules.py        # Analysis validation rules (config?)
├── parameters.py            # Parameter definitions (config?)
└── settings.py              # Settings utilities
```

**Асуудал:**
- `analysis_rules.py`, `parameters.py` app/config/-д байх ёстой
- `analysis_assignment.py` логик юм, config биш - `app/utils/` зөв

---

### D. ДАВХАРДАЛ / DUPLICATES

#### Shift кодууд:

**app/routes/main/helpers.py:**
```python
def get_12h_shift_code(dt):
    hour = dt.hour
    return "_D" if 7 <= hour < 19 else "_N"
```

**app/utils/shift_helper.py:**
```python
# Адилхан функц байна уу шалгах хэрэгтэй
```

---

## 3. САНАЛ БОЛГОЖ БУЙ ШИЙДЭЛ / PROPOSED SOLUTION

### Алхам 1: Config файлуудыг цэгцлэх

**Зөөх:**
- `app/utils/analysis_rules.py` → `app/config/analysis_rules.py`
- `app/utils/parameters.py` → `app/config/parameters.py`

**QC config-ийг салгах:**
- `app/routes/analysis/helpers.py`-аас QC тогтмолуудыг → `app/config/qc_config.py`

### Алхам 2: Helpers файлуудыг merge + rename

**Шинэ бүтэц:**
```
app/utils/
├── qc.py                    # QC утилити функцүүд (analysis/helpers.py-аас)
├── permissions.py           # Эрхийн шалгалтууд
├── repeatability_check.py   # Repeatability логик (api/helpers.py-аас)
├── shifts.py                # Shift кодууд (main/helpers.py + shift_helper.py merge)
├── security.py              # URL validation + бусад security (өөрчлөлтгүй)
```

**Устгах:**
- `app/routes/analysis/helpers.py` → хуваагдана
- `app/routes/api/helpers.py` → хуваагдана
- `app/routes/main/helpers.py` → хуваагдана

### Алхам 3: Services фолдер үүсгэх

```
app/services/
├── __init__.py
├── analysis_audit.py        # audit_log_service.py-ийг зөөх
└── sample_service.py        # Цаашид нэмэх
```

### Алхам 4: BOM character засах

```bash
# app/routes/api/helpers.py файлаас BOM устгах
sed -i '1s/^\xEF\xBB\xBF//' app/routes/api/helpers.py
```

---

## 4. ХЭРЭГЖҮҮЛЭХ ДАРААЛАЛ / IMPLEMENTATION ORDER

1. ✅ **Шинжилгээ** - Энэ баримт
2. ⏳ **Config цэгцлэх** - QC config салгах
3. ⏳ **Helpers merge** - 3 файлыг 4-5 утилити болгох
4. ⏳ **Services фолдер** - audit_log_service зөөх
5. ⏳ **BOM засах** - UTF-8 цэвэрлэх
6. ⏳ **Import засах** - Бүх файлын import statements
7. ⏳ **Test** - Систем ажиллаж байгааг батална
8. ⏳ **Commit** - Git-д хадгална

---

## 5. ЭРСДЭЛ / RISKS

- ⚠️ **Import breaking changes** - Олон файлд import засах шаардлагатай
- ⚠️ **Тестгүй код** - Unit test байхгүй тул manual тест шаардлагатай
- ⚠️ **Regression** - Функцүүд зөөхөд алдаа гарч болно

---

## 6. ДАРААГИЙН АЛХАМ / NEXT STEPS

1. Хэрэглэгчтэй зөвшөөрч батална
2. Config файлуудаас эхлэх (хамгийн аюулгүй)
3. Нэг нэгээр хэрэгжүүлж, тест хийх
4. Import засах
5. Git commit (feature branch)

---

**Баталгаажуулалт хэрэгтэй:**
- [ ] QC config салгах үү?
- [ ] Helpers merge хийх үү?
- [ ] Services фолдер үүсгэх үү?
- [ ] Shift давхардлыг засах уу?
