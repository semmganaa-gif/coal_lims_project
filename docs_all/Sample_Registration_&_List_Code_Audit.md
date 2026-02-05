# Sample Registration & List Code Audit
**Огноо:** 2026-02-05
**Хамрах хүрээ:** Дээж бүртгэл, жагсаалт, API

---

## 1. Бүтцийн тойм

### 1.1 Нүүрсний лаб (Coal)
| Файл | Үүрэг |
|------|-------|
| `app/routes/main/index.py` | Дээж бүртгэл (CHPP, WTL, LAB, QC) |
| `app/routes/main/samples.py` | Дээж удирдлага (disposal, retention) |
| `app/routes/api/samples_api.py` | AG-Grid API, summary, history |
| `app/templates/add_sample.html` | Бүртгэлийн form |
| `app/templates/sample_hub.html` | Жагсаалт (AG-Grid) |

### 1.2 Усны лаб (Water)
| Файл | Үүрэг |
|------|-------|
| `app/labs/water_lab/chemistry/routes.py` | Усны дээж бүртгэл |
| `app/labs/water_lab/microbiology/routes.py` | Микробиологийн дээж |
| `app/labs/water_lab/templates/water_sample_form.html` | Бүртгэлийн form |

### 1.3 Хуваалцсан (Shared)
| Файл | Үүрэг |
|------|-------|
| `app/models.py` | Sample model (lines 159-283) |
| `app/forms.py` | SampleForm (lines 126-250) |
| `app/schemas/sample_schema.py` | Validation schema |
| `app/repositories/sample_repository.py` | DB operations |

---

## 2. CRITICAL асуудлууд (3)

### 2.1 dispose_samples() логик алдаа
**Байршил:** `app/routes/main/samples.py:224`
**Түвшин:** CRITICAL

```python
# БУРУУ КОД
for sid in sample_ids:
    sample = Sample.query.get(int(sid))
    if sample and Sample.disposal_date is None:  # ← Class attribute!
        sample.disposal_date = today

# ЗӨВ КОД
    if sample and sample.disposal_date is None:  # ← Instance attribute
```

**Асуудал:** `Sample.disposal_date` (class) vs `sample.disposal_date` (instance)
- Class attribute шалгаж байгаа тул ҮРГЭЛЖ True болно
- Устгасан дээжийг дахин устгах боломжтой

**Нөлөө:** Өгөгдлийн бүрэн бүтэн байдал алдагдана

---

### 2.2 Field нэрлэлт зөрөө
**Байршил:**
- `app/models.py:221` - `sample_condition`
- `app/routes/api/samples_api.py:107-114` - `sample_condition` ба `sample_state` шалгадаг

```python
# models.py
sample_condition = db.Column(db.String(100))

# samples_api.py - Шаардлагагүй defensive check
if hasattr(Sample, "sample_condition"):
    cond_col = Sample.sample_condition
elif hasattr(Sample, "sample_state"):  # ← Байхгүй field!
    cond_col = Sample.sample_state
else:
    cond_col = Sample.status  # ← Утга зөрнө
```

**Асуудал:** Дутуу migration/refactoring, `sample_state` хэзээ ч байгаагүй

---

### 2.3 Form утга ба Template зөрөө
**Байршил:**
- `app/forms.py:148-156`
- `app/templates/add_sample.html:897`

```python
# forms.py - Монгол утга хадгална
choices=[
    ("Хуурай", "Хуурай"),
    ("Чийгтэй", "Чийгтэй"),
    ("Шингэн", "Шингэн"),
]

# add_sample.html - Англи утга шалгаж байна
{% if subfield.data == 'wet' %}
    <i class="bi bi-droplet"></i>
{% else %}
    <i class="bi bi-sun"></i>
{% endif %}
```

**Асуудал:** 'wet' хэзээ ч 'Чийгтэй'-тай таарахгүй → Icon буруу харагдана

---

## 3. MODERATE асуудлууд (9)

### 3.1 N+1 Query Pattern
**Байршил:** `app/routes/api/samples_api.py:300-320`

```python
results = AnalysisResult.query.filter_by(sample_id=sample_id).all()
# Template дотор results[i].sample хандвал N query үүснэ
```

**Засах:** `options(joinedload(AnalysisResult.sample))` нэмэх

---

### 3.2 lab_type Filter дутуу
**Байршил:** `app/routes/main/samples.py:312-315`

```python
# БУРУУ - lab_type filter байхгүй
samples = Sample.query.filter(
    Sample.retention_date is None,
    Sample.disposal_date is None
).all()

# ЗӨВ - lab_type нэмэх
samples = Sample.query.filter(
    Sample.lab_type == 'coal',
    Sample.retention_date.is_(None),
    Sample.disposal_date.is_(None)
).all()
```

**Асуудал:** Усны лабын дээжийг санамсаргүй өөрчлөх боломжтой

---

### 3.3 Error Handling хэт өргөн
**Байршил:** `app/routes/main/samples.py:238`

```python
except (ValueError, Exception):  # ← Exception нь ValueError-г агуулна
    continue  # ← Log бичихгүй, хэрэглэгчид мэдэгдэхгүй
```

---

### 3.4 Form Regex Spaces зөвшөөрөхгүй
**Байршил:** `app/forms.py:177-186`

```python
Regexp("^[A-Za-z0-9_.]*$", ...)  # ← Space байхгүй!
# "Болд Батаа" гэж оруулж болохгүй
```

---

### 3.5 Race Condition Report Counter
**Байршил:** `app/routes/main/index.py:625-642`

```python
current_count = int(setting_count.value)
current_count += 1
setting_count.value = str(current_count)
db.session.commit()  # ← Atomic биш!
```

**Асуудал:** 07:00-д олон request ирвэл давхардаж increment болно

---

### 3.6 Schema Validation Registration-д байхгүй
**Байршил:** `app/routes/main/index.py:130-426`

**Асуудал:** SampleSchema зөвхөн API-д ашиглагдаж байна, registration form-д байхгүй

---

### 3.7 Weight Validation зөрөө
| Байршил | Range |
|---------|-------|
| `forms.py` | Validation байхгүй |
| `index.py:216-225` | MIN_SAMPLE_WEIGHT - MAX_SAMPLE_WEIGHT |
| `sample_schema.py:54` | 0.001 - 10000 |

---

### 3.8 Pagination дутуу
**Байршил:** `app/routes/main/samples.py:147-175`

```python
expired_samples = Sample.query.filter(...).all()  # ← limit байхгүй
upcoming_samples = Sample.query.filter(...).all()  # ← limit байхгүй
# Мянга мянган бичлэг ачаалж болно
```

---

### 3.9 Duplicate Registration Code
**Байршил:** `app/routes/main/index.py:184-458`

4 газарт ижил Sample үүсгэх логик давтагдаж байна:
- CHPP/multi_gen (lines 184-308)
- WTL auto (lines 311-375)
- LAB auto (lines 378-426)
- WTL manual (lines 429-458)

**Санал:** `_create_sample()` helper function үүсгэх

---

## 4. LOW түвшний асуудлууд (8)

| # | Асуудал | Байршил |
|---|---------|---------|
| 1 | Шаардлагагүй `async` decorators | `samples_api.py:51+` |
| 2 | Magic strings/numbers | Бүх файл |
| 3 | Archive hub input validation дутуу | `samples_api.py:348` |
| 4 | Unused `return_sample` field | `forms.py:163` |
| 5 | Index дутуу (status, received_date) | `models.py` |
| 6 | Cascading delete дутуу (logs) | `models.py` |
| 7 | SQL Injection risk (minor) | `samples_api.py:125` |
| 8 | `sample_condition` is/== зөрөө | `samples.py` |

---

## 5. Засах дараалал

### Яаралтай (CRITICAL) - ДУУССАН ✅
1. ✅ `dispose_samples()` логик засах (`samples.py:224`)
   - `Sample.disposal_date` → `sample.disposal_date`
   - Error logging нэмсэн
2. ✅ `sample_condition` vs `sample_state` цэгцлэх (`samples_api.py:106-114`)
   - Шаардлагагүй hasattr checks устгасан
   - Шууд `Sample.sample_condition` ашиглах болгосон
3. ✅ Form утга ба template icon засах (`add_sample.html:897`)
   - `'wet'` → `['Чийгтэй', 'Шингэн']` болгосон

### Дунд хугацаа (MODERATE) - ДУУССАН ✅
4. ✅ N+1 query засах - `samples_api.py` joinedload нэмсэн
5. ✅ lab_type filter нэмэх - `samples.py:312` `lab_type='coal'` нэмсэн
6. ✅ Error handling сайжруулах - dispose_samples-д logging нэмсэн
7. ✅ Form regex spaces нэмэх - `forms.py` `\s` нэмсэн
8. ⏸️ Race condition засах - Ирээдүйд (db locking шаардлагатай)
9. ⏸️ Schema validation нэмэх - Ирээдүйд (бүтцийн өөрчлөлт)
10. ⏸️ Weight validation нэгтгэх - Ирээдүйд (schema унификаци)
11. ✅ Pagination нэмэх - `samples.py` бүх query-д limit нэмсэн
12. ⏸️ Duplicate code helper болгох - Ирээдүйд (refactoring)

---

## 6. Усны лаб дээж бүртгэл

### 6.1 Онцлог
- `chem_lab_id`, `micro_lab_id` - тусдаа дугаар
- `lab_type`: 'water', 'microbiology', 'water & micro'
- Шинжилгээ: PH, EC, TDS, NH4, MICRO_WATER гэх мэт

### 6.2 Routes
| Route | Файл |
|-------|------|
| `/water/samples/register` | `water_lab/chemistry/routes.py` |
| `/water/samples/list` | `water_lab/chemistry/routes.py` |
| `/micro/samples/register` | `water_lab/microbiology/routes.py` |

### 6.3 Нэмэлт шалгах
- ⬜ Усны лабын бүртгэл дээр ижил асуудал байгаа эсэх
- ⬜ chem_lab_id, micro_lab_id давхардал шалгах
- ⬜ Water sample validation

---

*Шинжилгээг хийсэн: Claude Code*
*Огноо: 2026-02-05*
