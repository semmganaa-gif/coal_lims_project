# Анализын Код/Нэрийн Төвлөрсөн Удирдлага

**Огноо:** 2025-11-30
**Статус:** ✅ АЖИЛЛАЖ БАЙНА
**Төвлөрсөн файл:** `app/constants.py`

---

## 🎯 Зорилго

Анализын код/нэршлийг **нэг газраас** удирдаж, бүх системд consistency (тууштай байдал) хангах:

- ✅ Тайлан дээр **нэг хэлбэр** харагдана
- ✅ Код өөрчлөхөд **нэг газар** засна
- ✅ Alias-ууд автомат шийдэгдэнэ
- ✅ Template-үүд `fmt_code` filter ашиглана

---

## 📁 Системийн Бүтэц

### 1. Canonical Definitions (app/constants.py)

**PARAMETER_DEFINITIONS** - Үндсэн тодорхойлолт:

```python
PARAMETER_DEFINITIONS = {
    'total_moisture': {
        'display_name': 'Нийт чийг',
        'lab_code': 'LAB.07.02',
        'standard_method': 'MNS ISO 589:2003',
        'aliases': ['Mt', 'MT', 'Total Moisture', 'Нийт чийг тодорхойлох', 'Mt,ar'],
        'type': 'measured',
        'is_basis_key': True
    },
    'calorific_value': {
        'display_name': 'Илчлэгийн нийт утга (ad)',
        'lab_code': 'LAB.07.12',
        'standard_method': 'MNS ISO 1928:2009',
        'aliases': ['CV', 'Qgr,ad', 'Qgr', 'Calorific Value', 'Илчлэгийн нийт утга тодорхойлох'],
        'type': 'measured',
        'conversion_bases': ['d', 'daf', 'ar']
    },
    # ... бусад анализууд
}
```

**3 давхарга бүтэц:**
1. **Canonical name** - Системийн үндсэн нэр (`total_moisture`, `calorific_value`)
2. **Base code** - Үндсэн код (`MT`, `CV`)
3. **Display alias** - Харуулах хэлбэр (`Mt,ar`, `Qgr,ad`)

---

### 2. Mapping Tables

**CANONICAL_TO_BASE_ANALYSIS** - Canonical → Base:
```python
CANONICAL_TO_BASE_ANALYSIS = {
    'total_moisture': 'MT',
    'calorific_value': 'CV',
    'total_sulfur': 'TS',
    # ...
}
```

**ALIAS_TO_BASE_ANALYSIS** - Alias → Base (автоматаар үүснэ):
```python
ALIAS_TO_BASE_ANALYSIS = {
    'mt': 'MT',
    'mt,ar': 'MT',
    'total_moisture': 'MT',
    'cv': 'CV',
    'qgr,ad': 'CV',
    'qgr': 'CV',
    'calorific_value': 'CV',
    # ... PARAMETER_DEFINITIONS-аас автоматаар үүснэ
}
```

---

### 3. Display Preference Order

**`app/__init__.py` - _PREF_ORDER:**

```python
_PREF_ORDER = [
    "st,ad",    # TS → St,ad
    "qgr,ad",   # CV → Qgr,ad
    "mt,ar",    # MT → Mt,ar
    "trd,d",    # TRD → TRD,d (хэрэв байвал)
    "p,ad",     # P → P,ad
    "f,ad",     # F → F,ad
    "cl,ad"     # Cl → Cl,ad
]
```

**Логик:**
- Хэрэв base code-ын alias-д `_PREF_ORDER` дотор байгаа код байвал → тэрийг харуулна
- Үгүй бол base code-г харуулна

---

## 🔧 fmt_code Filter - Хэрэглээ

### Template-д хэрхэн ашиглах:

```django
{# Хатуу бичихийн оронд: #}
<th>MT</th>           ❌ ХУУЧИН арга

{# fmt_code ашиглах: #}
<th>{{ 'MT'|fmt_code }}</th>   ✅ ШИНЭ арга → "Mt,ar"
<th>{{ 'CV'|fmt_code }}</th>   ✅ → "Qgr,ad"
<th>{{ 'TS'|fmt_code }}</th>   ✅ → "St,ad"
<th>{{ 'P'|fmt_code }}</th>    ✅ → "P,ad"
```

### Юу болж байна:

**Жишээ 1: MT (Total Moisture)**
```python
'MT'|fmt_code
↓
base = 'MT'
↓
_pick_display_alias('MT')
↓
# MT-ийн aliases-ээс 'mt,ar' олох (_PREF_ORDER дотор)
↓
Format: 'mt,ar' → 'Mt,ar'
↓
Output: "Mt,ar"
```

**Жишээ 2: CV (Calorific Value)**
```python
'CV'|fmt_code
↓
base = 'CV'
↓
_pick_display_alias('CV')
↓
# CV-ийн aliases-ээс 'qgr,ad' олох (_PREF_ORDER дотор)
↓
Format: 'qgr,ad' → 'Qgr,ad'
↓
Output: "Qgr,ad"
```

**Жишээ 3: Qgr,ar (аль хэдийн comma байгаа)**
```python
'Qgr,ar'|fmt_code
↓
if "," in code: return code  # Аль хэдийн comma байвал буцаах
↓
Output: "Qgr,ar"
```

---

## 📊 Анализын Код Хөрвүүлэлт

### Одоогийн Тайлан Header Хөрвүүлэлт:

| Өмнө (хатуу бичсэн) | Одоо (fmt_code) | Харагдах |
|---------------------|-----------------|----------|
| `<th>MT</th>` | `<th>{{ 'MT'\|fmt_code }}</th>` | **Mt,ar** |
| `<th>Mad</th>` | `<th>{{ 'Mad'\|fmt_code }}</th>` | **Mad** |
| `<th>Aad</th>` | `<th>{{ 'Aad'\|fmt_code }}</th>` | **Aad** |
| `<th>CV</th>` | `<th>{{ 'CV'\|fmt_code }}</th>` | **Qgr,ad** |
| `<th>TS</th>` | `<th>{{ 'TS'\|fmt_code }}</th>` | **St,ad** |
| `<th>P</th>` | `<th>{{ 'P'\|fmt_code }}</th>` | **P,ad** |
| `<th>Qgr,ar</th>` | `<th>{{ 'Qgr,ar'\|fmt_code }}</th>` | **Qgr,ar** |

---

## 🔄 Хэрхэн Шинэ Анализ Нэмэх

### 1. constants.py-д тодорхойлох:

```python
PARAMETER_DEFINITIONS = {
    'new_analysis': {
        'display_name': 'Шинэ анализ',
        'lab_code': 'LAB.XX.YY',
        'standard_method': 'MNS ...',
        'aliases': ['NA', 'NA,ad', 'New Analysis'],
        'type': 'measured'
    }
}
```

### 2. CANONICAL_TO_BASE_ANALYSIS нэмэх:

```python
CANONICAL_TO_BASE_ANALYSIS = {
    # ...
    'new_analysis': 'NA',
}
```

### 3. Display preference (хэрэв шаардлагатай):

```python
# app/__init__.py
_PREF_ORDER = [
    "st,ad", "qgr,ad", "mt,ar", "trd,d", "p,ad", "f,ad", "cl,ad",
    "na,ad"  # ✅ ШИНЭ нэмэх
]
```

### 4. Template-д ашиглах:

```django
<th>{{ 'NA'|fmt_code }}</th>  <!-- Автоматаар "Na,ad" харуулна -->
```

✅ **Тэгээд л болно!** Alias автомат үүснэ, fmt_code автомат ажиллана.

---

## 🎯 Давуу тал

### Өмнө (Хатуу бичигдсэн):

```django
{# 50 template файл #}
<th>MT</th>  <!-- Засах: 50 газар -->
<th>Mad</th>
<th>CV</th>
```

❌ Код өөрчлөхөд 50 файл засах
❌ Consistency алдагдах
❌ Alias солихгүй

### Одоо (Төвлөрсөн):

```django
{# constants.py - 1 файл #}
_PREF_ORDER = ["...", "mt,ar", ...]  <!-- Засах: 1 газар -->

{# template - автомат #}
<th>{{ 'MT'|fmt_code }}</th>  <!-- Автомат "Mt,ar" гарна -->
```

✅ Код өөрчлөхөд 1 газар засна
✅ Consistency автомат
✅ Alias солих хялбар

---

## 📋 Засварласан Файлууд

**Өнөөдөр (2025-11-30):**

1. ✅ `app/templates/report.html` - Lines 200-218
   - 19 header-ийг `fmt_code` filter ашиглуулсан
   - Хатуу бичсэн код устгасан

**Системд аль хэдийн байгаа:**

1. ✅ `app/constants.py` - Canonical definitions
2. ✅ `app/__init__.py` - fmt_code filter + _PREF_ORDER
3. ✅ `app/utils/codes.py` - norm_code() функц

---

## 🧪 Тест

### Хэрхэн шалгах:

1. **Python shell:**
```python
from app import create_app
app = create_app()

with app.app_context():
    from app import fmt_code

    print(fmt_code('MT'))     # Output: "Mt,ar"
    print(fmt_code('CV'))     # Output: "Qgr,ad"
    print(fmt_code('TS'))     # Output: "St,ad"
    print(fmt_code('Qgr,ar')) # Output: "Qgr,ar"
```

2. **Тайлан харах:**
   - Дээж үүсгэж, тайлан гаргах
   - Header-үүд зөв харагдаж байгаа эсэхийг шалгах

---

## 📝 Checklist - Шинэ Анализ Нэмэхэд

- [ ] `constants.py` → PARAMETER_DEFINITIONS нэмсэн
- [ ] `constants.py` → CANONICAL_TO_BASE_ANALYSIS нэмсэн
- [ ] `app/__init__.py` → _PREF_ORDER шинэчилсэн (хэрэв шаардлагатай)
- [ ] Template-д `{{ 'CODE'|fmt_code }}` ашигласан (хатуу бичихгүй)
- [ ] Тест хийсэн
- [ ] Documentation шинэчилсэн

---

## 🎉 Дүгнэлт

✅ **Анализын код/нэр нэг газраас удирдагдаж байна!**

- **1 газар тодорхойлох:** `constants.py`
- **1 газар харуулах дүрэм:** `app/__init__.py` - _PREF_ORDER
- **Бүх template:** `fmt_code` filter ашиглана
- **Автомат consistency:** Alias-ууд автомат шийдэгдэнэ

**Хэрэглэгчийн асуулт:**
- "TM гэж ярьдаг, MT,ar гэж тайланд гарч байна" ✅ Засагдсан
- "CV гэж бичдэг, Qgr,ad гэж тайланд гарч байна" ✅ Зохицуулагдсан

**Одоо:**
- `_PREF_ORDER`-д "mt,ar" байгаа → MT → Mt,ar
- `_PREF_ORDER`-д "qgr,ad" байгаа → CV → Qgr,ad

Хэрэв **CV** харуулахыг хүсвэл:
```python
# app/__init__.py
_PREF_ORDER = [
    "st,ad",
    # "qgr,ad",  ← Энийг устгах эсвэл коммент хийх
    "mt,ar",
    ...
]
```

Тэгвэл `{{ 'CV'|fmt_code }}` → "CV" харуулна!
