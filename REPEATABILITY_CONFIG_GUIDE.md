# Repeatability Limits Удирдлага (T - Давтагдах Чадвар)

**Огноо:** 2025-11-29
**Статус:** ✅ ХЭРЭГЖСЭН - ТӨВЛӨРСӨН
**Файл:** `app/config/repeatability.py`

---

## 📋 Агуулга

1. [Тайлбар](#тайлбар)
2. [Хэрэглээ](#хэрэглээ)
3. [Тохиргоо](#тохиргоо)
4. [Удирдах скрипт](#удирдах-скрипт)
5. [Жишээнүүд](#жишээнүүд)
6. [API Reference](#api-reference)

---

## 🎯 Тайлбар

Энэ модуль нь шинжилгээний үр дүнгийн **repeatability (T) limits** буюу давтагдах чадварын
хязгаарыг төвлөрсөн нэг файлаас удирддаг.

### Өмнө (🔴 ДАВХАРДСАН)

```python
# app/config/repeatability.py - Python
LIMIT_RULES = {
    "Mad": {"bands": [{"upper": 10.0, "limit": 0.20, "mode": "abs"}]},
    # ...
}
```

```javascript
// app/static/js/repeatability.js - JavaScript HARDCODED!
const base = {
  'Mad': { bands: [{ upper:0.5, limit:0.20, mode:'abs' }, ...] },
  'Aad': { bands: [{ upper:15.0, limit:0.20, mode:'abs' }, ...] },
  // ... 30+ мөр давхардсан
};
```

**Асуудлууд:**
- ❌ Python + JavaScript 2 газарт тохиргоо
- ❌ Өөрчлөх хүнд (2 файл засах ёстой)
- ❌ Consistency эрсдэлтэй
- ❌ Maintenance төвөгтэй

---

### Одоо (✅ ТӨВЛӨРСӨН)

```python
# app/config/repeatability.py - ЗӨВХӨН НЭГ ЭХЛЭЛ
LIMIT_RULES = {
    "Mad": {"bands": [
        {"upper": 0.50, "limit": 0.20, "mode": "abs"},
        {"upper": 5.00, "limit": 0.20, "mode": "abs"},
        {"upper": 10.0, "limit": 0.30, "mode": "abs"},
        {"upper": inf,  "limit": 0.40, "mode": "abs"},
    ]},
    # ... 20 анализ
}
```

```javascript
// app/static/js/repeatability.js - ТӨВЛӨРСӨН
// Hardcoded config УСТГАСАН - серверээс бүгдийг авна
w.LIMS_LIMITS = w.LIMS_LIMIT_RULES || {};
```

**Давуу талууд:**
- ✅ Бүх тохиргоо нэг Python файлд
- ✅ JavaScript hardcoded устгасан
- ✅ Өөрчлөх хялбар (1 газар засах)
- ✅ Consistency баталгаатай
- ✅ Серверээс frontend-д автоматаар дамжина

---

## 🚀 Хэрэглээ

### Backend (Python)-д

```python
from app.utils.repeatability_loader import load_limit_rules

# Repeatability дүрмүүдийг авах
rules = load_limit_rules()

# Тодорхой анализын дүрэм авах
mad_rule = rules.get("Mad")
# {"bands": [{"upper": 0.5, "limit": 0.20, "mode": "abs"}, ...]}

# API-д ашиглах (app/routes/api/helpers.py-д орсон)
from app.routes.api.helpers import _effective_limit

limit, mode, band_label = _effective_limit("Mad", 3.5)
# (0.20, "abs", "0.5-5.0")
```

---

### Frontend (JavaScript)-д

```javascript
// Repeatability limit авах (avg-аар band сонгоно)
const limit = getRepeatabilityLimit('Mad', 3.5);
console.log(limit);  // 0.20 (3.5 нь 0.5-5.0 band-д багтана)

const limit2 = getRepeatabilityLimit('Mad', 8.0);
console.log(limit2);  // 0.30 (8.0 нь 5.0-10.0 band-д багтана)

// Single limit анализ
const csnLimit = getRepeatabilityLimit('CSN');
console.log(csnLimit);  // 0.5
```

**Автомат дамжуулалт:**
```html
<!-- app/templates/base.html -->
<script>
  // Серверээс автоматаар repeatability дүрмүүд ирнэ
  window.LIMS_LIMIT_RULES = {{ LIMS_LIMIT_RULES|tojson|safe }};
</script>
```

---

### Template-д (Jinja2)

```jinja
{# Context-д LIMS_LIMIT_RULES автоматаар inject хийгдсэн #}
{% if LIMS_LIMIT_RULES %}
  <script>
    const rules = {{ LIMS_LIMIT_RULES|tojson|safe }};
    console.log(rules['Mad']);
  </script>
{% endif %}
```

---

## ⚙️ Тохиргоо

### Limit өөрчлөх

**Файл:** `app/config/repeatability.py`

```python
# Жишээ: Mad-ийн эхний band limit-ийг 0.20 → 0.15 болгох
LIMIT_RULES = {
    "Mad": {"bands": [
        {"upper": 0.50, "limit": 0.15, "mode": "abs"},  # 0.20 → 0.15
        {"upper": 5.00, "limit": 0.20, "mode": "abs"},
        {"upper": 10.0, "limit": 0.30, "mode": "abs"},
        {"upper": inf,  "limit": 0.40, "mode": "abs"},
    ]},
    # ...
}
```

**Үр дүн:**
- Дундаж ≤ 0.5 үед: T = 0.15 (өмнө 0.20 байсан)
- Frontend автоматаар шинэ утгыг ашиглана

---

### Шинэ анализ нэмэх

```python
from math import inf

LIMIT_RULES = {
    # ... existing codes ...

    # Шинэ анализ - Single limit
    "NEW_CODE": {"single": {"limit": 0.25, "mode": "abs"}},

    # Шинэ анализ - Band limits
    "ANOTHER_CODE": {"bands": [
        {"upper": 10.0, "limit": 0.10, "mode": "abs"},
        {"upper": 20.0, "limit": 0.20, "mode": "abs"},
        {"upper": inf,  "limit": 0.30, "mode": "abs"},
    ]},
}
```

**Тэгээд л болсон!** JavaScript засах шаардлагагүй!

---

### Mode Types

| Mode | Тайлбар | Жишээ |
|------|---------|-------|
| `"abs"` | Absolute (үнэмлэхүй утга) | T = 0.20 |
| `"percent"` | Percent (хувиар) | T = 10% → дундаж 5.0 бол 0.5 |

**Жишээ:**
```python
# Absolute mode
{"limit": 0.20, "mode": "abs"}   # T = 0.20 (дундаж ямар ч байсан)

# Percent mode
{"limit": 0.50, "mode": "percent"}  # T = дундаж × 0.50%
# Дундаж = 10.0 → T = 10.0 × 0.50 / 100 = 0.05
```

---

## 🛠 Удирдах Скрипт

### Бүх тохиргоо харах

```bash
python scripts/manage_repeatability.py --show
```

**Гаралт:**
```
================================================================================
REPEATABILITY LIMITS ТОХИРГОО (T - Давтагдах Чадвар)
================================================================================

Нийт анализ: 20

📌 Single Limit Rules (7 анализ):
--------------------------------------------------------------------------------
  CRI        → T =   2.20 (abs)
  CSN        → T =   0.50 (abs)
  CSR        → T =   2.50 (abs)
  CV         → T = 120.00 (abs)
  F          → T =   0.01 (abs)
  F,ad       → T =   0.01 (abs)
  TRD        → T =   0.02 (abs)

📊 Band Rules (13 анализ):
--------------------------------------------------------------------------------

  Aad:
    ≤ 15                 → T =  0.200 (abs)
    15 < x ≤ 30          → T =  0.300 (abs)
    30 < x ≤ ∞           → T =  0.500 (abs)

  Mad:
    ≤ 0.5                → T =  0.200 (abs)
    0.5 < x ≤ 5          → T =  0.200 (abs)
    5 < x ≤ 10           → T =  0.300 (abs)
    10 < x ≤ ∞           → T =  0.400 (abs)

  ...
```

---

### Хураангуй харах

```bash
python scripts/manage_repeatability.py --summary
```

**Гаралт:**
```
================================================================================
ХУРААНГУЙ (Summary)
================================================================================

Нийт анализ: 20
  Single limits: 7 анализ
  Band limits: 13 анализ

Бүх анализ кодууд:
  Aad       , CRI       , CSN       , CSR       , CV        , Cl
  Cl,ad     , F         , F,ad      , Gi        , MT        , Mad
  P         , P,ad      , St,ad     , TRD       , TS        , Vad
  X         , Y
```

---

### Тест ажиллуулах

```bash
python scripts/manage_repeatability.py --test
```

**Гаралт:**
```
================================================================================
ТЕСТҮҮД (Automated Tests)
================================================================================

Test 1: Бүх анализ зөв бүтэцтэй эсэх
  ✅ 20/20 анализ зөв бүтэцтэй

Test 2: Single rules-үүд limit, mode-тэй эсэх
  ✅ 7 single rules бүгд зөв

Test 3: Band rules-үүд upper, limit, mode-тэй эсэх
  ✅ 30 bands бүгд зөв

Test 4: Mode утгууд зөв эсэх (abs эсвэл percent)
  ✅ 37 mode утга зөв

================================================================================
Үр дүн: 94 давсан, 0 амжилтгүй
✅ Бүх тест амжилттай!
```

---

### Тодорхой анализ тест

```bash
python scripts/manage_repeatability.py --code Mad
```

**Гаралт:**
```
================================================================================
ТЕСТ: Mad
================================================================================

Төрөл: Band limits (4 bands)

  Band 1: ≤ 0.5                → T = 0.2 (abs)
  Band 2: 0.5 < x ≤ 5          → T = 0.2 (abs)
  Band 3: 5 < x ≤ 10           → T = 0.3 (abs)
  Band 4: 10 < x ≤ ∞           → T = 0.4 (abs)

Жишээ утгууд:
  Дундаж =   0.40 → T =  0.200 (abs)
  Дундаж =   4.90 → T =  0.200 (abs)
  Дундаж =   9.90 → T =  0.300 (abs)
  Дундаж =  10.10 → T =  0.400 (abs)
```

---

## 📚 Жишээнүүд

### Single Limit Rules

| Анализ | Limit | Mode | Тайлбар |
|--------|-------|------|---------|
| CSN | 0.50 | abs | Crucible Swelling Number |
| CRI | 2.2 | abs | Coke Reactivity Index |
| CSR | 2.5 | abs | Coke Strength after Reaction |
| CV | 120.0 | abs | Calorific Value |
| F | 0.01 | abs | Fluorine |
| TRD | 0.02 | abs | Total Relative Dilatation |

**Жишээ:**
```python
# CSN: T = 0.50 (дундаж ямар ч байсан)
rule = {"single": {"limit": 0.50, "mode": "abs"}}

# Parallel 1: 5.2, Parallel 2: 5.6
# Diff = |5.2 - 5.6| = 0.4
# T limit = 0.50
# 0.4 ≤ 0.50 → ✅ PASS (Repeatability хангасан)
```

---

### Band Limit Rules

#### Чийг (Moisture) - Mad

| Дундаж Хүрээ | Limit | Mode |
|-------------|-------|------|
| ≤ 0.5 | 0.20 | abs |
| 0.5 < x ≤ 5.0 | 0.20 | abs |
| 5.0 < x ≤ 10.0 | 0.30 | abs |
| > 10.0 | 0.40 | abs |

**Жишээ:**
```python
# Дундаж = 3.5% (0.5-5.0 band)
# T limit = 0.20
# Parallel 1: 3.4%, Parallel 2: 3.6%
# Diff = |3.4 - 3.6| = 0.2
# 0.2 ≤ 0.20 → ✅ PASS

# Дундаж = 8.0% (5.0-10.0 band)
# T limit = 0.30
# Parallel 1: 7.8%, Parallel 2: 8.2%
# Diff = |7.8 - 8.2| = 0.4
# 0.4 ≤ 0.30 → ❌ FAIL (давтах шаардлагатай)
```

---

#### Үнс (Ash) - Aad

| Дундаж Хүрээ | Limit | Mode |
|-------------|-------|------|
| ≤ 15.0 | 0.20 | abs |
| 15.0 < x ≤ 30.0 | 0.30 | abs |
| > 30.0 | 0.50 | abs |

---

#### Хүхэр (Sulfur) - TS

| Дундаж Хүрээ | Limit | Mode |
|-------------|-------|------|
| ≤ 2.0 | 0.05 | abs |
| 2.0 < x ≤ 5.0 | 0.10 | abs |
| > 5.0 | 0.15 | abs |

---

#### Хлор (Chlorine) - Cl

| Дундаж Хүрээ | Limit | Mode |
|-------------|-------|------|
| ≤ 150 μg/g | 15.0 | abs |
| > 150 μg/g | 0.10 | **percent** |

**Жишээ (Percent mode):**
```python
# Дундаж = 200 μg/g (> 150, percent mode)
# T limit = 0.10% = 200 × 0.10 / 100 = 0.20
# Parallel 1: 199, Parallel 2: 201
# Diff = |199 - 201| = 2
# 2 ≤ 0.20 → ❌ FAIL

# Дундаж = 100 μg/g (≤ 150, abs mode)
# T limit = 15.0
# Parallel 1: 90, Parallel 2: 110
# Diff = |90 - 110| = 20
# 20 ≤ 15.0 → ❌ FAIL
```

---

## 🔧 API Reference

### Python API

#### `load_limit_rules() -> dict`

Repeatability дүрмүүдийг DB-с эсвэл файлаас уншина.

**Source:** `app/utils/repeatability_loader.py`

```python
from app.utils.repeatability_loader import load_limit_rules

rules = load_limit_rules()
# Returns: LIMIT_RULES dictionary
```

**Features:**
- ✅ DB-с уншина (SystemSetting.category="repeatability")
- ✅ DB-д байхгүй бол файлаас fallback
- ✅ LRU cache (@lru_cache) - Хурдан

---

#### `_effective_limit(analysis_code: str, avg: float | None) -> tuple`

Анализын кодоор effective limit олох (avg-аар band сонгоно).

**Source:** `app/routes/api/helpers.py`

```python
from app.routes.api.helpers import _effective_limit

# Band limit example
limit, mode, band_label = _effective_limit("Mad", 3.5)
# Returns: (0.20, "abs", "0.5-5.0")

# Single limit example
limit, mode, band_label = _effective_limit("CSN", None)
# Returns: (0.50, "abs", None)
```

**Parameters:**
- `analysis_code` (str): Анализын код (жнь: "Mad", "Aad", "P")
- `avg` (float | None): Дундаж утга (band сонгоход хэрэглэнэ)

**Returns:**
- `(limit, mode, band_label)` tuple
  - `limit` (float): Limit утга
  - `mode` (str): "abs" эсвэл "percent"
  - `band_label` (str | None): Band range (жнь: "0.5-5.0")

---

### JavaScript API

#### `getRepeatabilityLimit(code, avg)`

Анализын кодоор repeatability limit авах.

**Source:** `app/static/js/repeatability.js`

```javascript
// Band limit with avg
const limit1 = getRepeatabilityLimit('Mad', 3.5);
console.log(limit1);  // 0.20

// Band limit without avg (эхний band-ийн limit-ийг буцаана)
const limit2 = getRepeatabilityLimit('Mad');
console.log(limit2);  // 0.20 (эхний band)

// Single limit
const limit3 = getRepeatabilityLimit('CSN');
console.log(limit3);  // 0.5

// Олдохгүй код
const limit4 = getRepeatabilityLimit('UNKNOWN');
console.log(limit4);  // null
```

**Parameters:**
- `code` (string): Анализын код
- `avg` (number, optional): Дундаж утга (band сонгоход)

**Returns:**
- `number | null`: Limit утга эсвэл null (олдохгүй бол)

---

## ✅ Checklist

Repeatability тохиргоо өөрчлөх үед:

- [ ] `app/config/repeatability.py` засах
- [ ] `python scripts/manage_repeatability.py --test` ажиллуулах
- [ ] Бүх тест давсан эсэх шалгах
- [ ] Application дахин эхлүүлэх (серверийн cache цэвэрлэх)
- [ ] Browser refresh хийх
- [ ] Analysis form-д repeatability шалгалт зөв ажиллаж байгаа эсэх тест

---

## 🎯 Үр Дүнгийн Нэгтгэл

### Өмнө vs Одоо

| Үзүүлэлт | Өмнө (ДАВХАРДСАН) | Одоо (ТӨВЛӨРСӨН) |
|----------|-------------------|------------------|
| **Python config** | 1 файл | 1 файл |
| **JavaScript config** | 1 файл (30+ мөр hardcoded) | Байхгүй (серверээс) |
| **Нийт эх сурвалж** | 2 файл | 1 файл |
| **Өөрчлөх** | 2 файл засах | 1 файл засах |
| **Consistency** | ⚠️ Гараар синхрон | ✅ Автомат |
| **Maintenance** | ❌ Хүнд | ✅ Хялбар |
| **JavaScript file size** | 57 мөр | 26 мөр (-54%) |

---

### Precision-тэй Адилхан Шийдэл

| Feature | Precision | Repeatability |
|---------|-----------|---------------|
| **Төвлөрсөн Python config** | ✅ | ✅ |
| **JavaScript hardcoded устгасан** | ✅ | ✅ |
| **Серверээс дамжуулна** | ✅ | ✅ |
| **Management script** | ✅ | ✅ |
| **Auto tests** | ✅ | ✅ |
| **Documentation** | ✅ | ✅ |

---

## 📝 Санамж

1. **Тохиргоо өөрчилсний дараа:**
   - Application restart хийх
   - Browser cache цэвэрлэх
   - Тест ажиллуулах

2. **Шинэ анализ нэмэхдээ:**
   - Scientific standard баримтлах
   - GB/T стандарт лавлах
   - Тест нэмэх

3. **Production deployment:**
   - Өөрчлөлтийг staging-д эхлээд тест
   - Users-д мэдэгдэх
   - Rollback plan бэлэн байх

4. **DB-д тохиргоо хадгалах:**
   - SystemSetting model ашиглана
   - category="repeatability", key="limits"
   - JSON format-аар value-д хадгална

---

**Үүсгэсэн:** 2025-11-29
**Статус:** ✅ PRODUCTION READY - ТӨВЛӨРСӨН
**Анализын тоо:** 20 codes
**Тест:** 94/94 амжилттай (100%)
**File size reduction:** JavaScript 57 → 26 мөр (-54%)
