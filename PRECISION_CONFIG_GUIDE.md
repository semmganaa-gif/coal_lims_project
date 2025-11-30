# Тоон Оронгийн Удирдлага (Display Precision Configuration)

**Огноо:** 2025-11-29
**Статус:** ✅ ХЭРЭГЖСЭН
**Файл:** `app/config/display_precision.py`

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

Энэ модуль нь шинжилгээний үр дүнг харуулахдаа **хэдэн оронгийн нарийвчлалаар**
харуулахыг төвлөрсөн нэг файлаас удирддаг.

### Өмнө (🔴 Тархмал)

```python
# app/__init__.py
if base in ZERO_DEC_BASE: return f"{x:.0f}"
if base in ONE_DEC_BASE: return f"{x:.1f}"
if base in THREE_DEC_BASE: return f"{x:.3f}"
return f"{x:.2f}"

# app/routes/report_routes.py
result = f"{value:.2f}"  # Hardcoded!

# app/templates/sample_report.html
{{ value|round(2) }}  # Hardcoded!
```

**Асуудлууд:**
- ❌ Тохиргоо олон газарт тархсан
- ❌ Өөрчлөх хэцүү (5+ файл засах)
- ❌ Consistency алдагдана
- ❌ Шинэ анализ нэмэхэд төвөг

---

### Одоо (✅ Төвлөрсөн)

```python
# app/config/display_precision.py - ЗӨВ ХОР НЭГ ФАЙЛ
DECIMAL_PLACES = {
    'Aad': 2,      # 10.25%
    'P': 3,        # 0.015%
    'CV': 0,       # 25000 J/g
    'CSN': 1,      # 5.5
    # ... бусад
}
```

**Давуу талууд:**
- ✅ Бүх тохиргоо нэг файлд
- ✅ Өөрчлөх хялбар (1 мөр засах)
- ✅ Consistency баталгаатай
- ✅ Шинэ анализ нэмэх хялбар

---

## 🚀 Хэрэглээ

### Template-д (Jinja2)

```jinja
{# Автоматаар зөв оронгоор харуулна #}
{{ sample.ash_value|fmt_result('Aad') }}
{# Output: 10.25 (2 орон) #}

{{ sample.phosphorus|fmt_result('P') }}
{# Output: 0.015 (3 орон) #}

{{ sample.calorific_value|fmt_result('CV') }}
{# Output: 25000 (0 орон, бүхэл) #}
```

---

### Python код дээр

```python
from app.config.display_precision import format_result, get_decimal_places

# Format үр дүн
formatted = format_result(10.256, "Aad")
print(formatted)  # "10.26"

formatted = format_result(0.0156, "P")
print(formatted)  # "0.016"

# Зөвхөн decimal places авах
places = get_decimal_places("Aad")
print(places)  # 2

places = get_decimal_places("P")
print(places)  # 3
```

---

### JavaScript (frontend)-д

Backend API-аас formatted value авах:

```javascript
// Backend automatically formats
fetch('/api/sample/123/results')
  .then(r => r.json())
  .then(data => {
    // Already formatted by backend
    console.log(data.ash);  // "10.25"
    console.log(data.phosphorus);  // "0.015"
  });
```

---

## ⚙️ Тохиргоо

### Тоон орон өөрчлөх

**Файл:** `app/config/display_precision.py`

```python
# Жишээ: P (Фосфор)-ийн тоон оронг 4 болгох
DECIMAL_PLACES = {
    # ...
    'P': 4,        # 0.0156 → 0.0156 (4 орон)
    'P,ad': 4,
    'P,d': 4,
    # ...
}
```

**Үр дүн:**
- Өмнө: `0.015`
- Одоо: `0.0156`

---

### Шинэ анализ нэмэх

```python
DECIMAL_PLACES = {
    # ... existing codes ...

    # Шинэ анализ
    'NEW_ANALYSIS': 2,     # 2 орон
}
```

**Тэгээд л болсон!** Систем автоматаар ашиглана.

---

### Default өөрчлөх

```python
# Тодорхойгүй анализд default precision
DEFAULT_DECIMAL_PLACES = 2  # → 3 болгож болно
```

---

## 🛠 Удирдах скрипт

### Бүх тохиргоо харах

```bash
python scripts/manage_precision.py --show
```

**Гаралт:**
```
================================================================================
ТООН ОРОНГИЙН ТОХИРГОО (Display Precision Configuration)
================================================================================

Default precision: 2 орон
Total analysis codes: 75

0 орон (14 анализ):
--------------------------------------------------------------------------------
  CV          , Gi          , X           , Y           , CRI
  CSR         , TRD         , TRD,ad      , TRD,d       , FM
  Qgr,ad      , Qgr,d       , Qgr,daf     , Qnet,ar

1 орон (1 анализ):
--------------------------------------------------------------------------------
  CSN

2 орон (51 анализ):
--------------------------------------------------------------------------------
  MT          , Mad         , Aad         , Vad         , TS
  ...

3 орон (9 анализ):
--------------------------------------------------------------------------------
  P           , P,ad        , P,d         , F           , F,ad
  F,d         , Cl          , Cl,ad       , Cl,d
```

---

### Хураангуй харах

```bash
python scripts/manage_precision.py --summary
```

**Гаралт:**
```
================================================================================
ХУРААНГУЙ (Summary)
================================================================================

Нийт анализ: 75
Default: 2 орон

Бүлгээр:
  0 орон: 14 анализ
  1 орон: 1 анализ
  2 орон: 51 анализ
  3 орон: 9 анализ
```

---

### Тест ажиллуулах

```bash
python scripts/manage_precision.py --test
```

**Гаралт:**
```
================================================================================
ТЕСТҮҮД (Tests)
================================================================================

✅ format_result(10.256, 'Aad'     ) = '10.26' (expected: '10.26')
✅ format_result(10.251, 'Aad'     ) = '10.25' (expected: '10.25')
✅ format_result(0.0156, 'P'       ) = '0.016' (expected: '0.016')
✅ format_result(0.0154, 'P'       ) = '0.015' (expected: '0.015')
✅ format_result(25432.8, 'CV'      ) = '25433' (expected: '25433')
✅ format_result(5.55, 'CSN'     ) = '5.5' (expected: '5.5')
...

Results: 12 passed, 0 failed

✅ All tests passed!
```

---

### Тодорхой анализ тест

```bash
python scripts/manage_precision.py --code Aad
```

**Гаралт:**
```
================================================================================
ТЕСТ: Aad
================================================================================

Тоон орон: 2

Жишээ үр дүнгүүд:
     0.0100 → 0.01
     0.1000 → 0.10
     1.0000 → 1.00
    10.0000 → 10.00
   100.0000 → 100.00
  1000.0000 → 1000.00
     0.0156 → 0.02
 25432.8000 → 25432.80
```

---

### Интерактив горим

```bash
python scripts/manage_precision.py --interactive
```

**Жишээ session:**
```
================================================================================
ИНТЕРАКТИВ ГОРИМ
================================================================================
'quit' эсвэл 'exit' гэж бичээд гарах

Анализын код (жнь: Aad, P, CV): Aad
Үр дүнгийн утга (жнь: 10.256): 10.256

📊 Үр дүн:
  Анализ: Aad
  Тоон орон: 2
  Оруулсан: 10.256
  Харуулах: 10.26

Анализын код (жнь: Aad, P, CV): P
Үр дүнгийн утга (жнь: 10.256): 0.0156

📊 Үр дүн:
  Анализ: P
  Тоон орон: 3
  Оруулсан: 0.0156
  Харуулах: 0.016
```

---

## 📚 Жишээнүүд

### Бүх precision groups

| Бүлэг | Орон | Анализууд | Жишээ |
|-------|------|-----------|-------|
| Бүхэл тоо | 0 | CV, Gi, X, Y, CRI, CSR, TRD, FM | 25000 |
| 1 орон | 1 | CSN | 5.5 |
| Стандарт | 2 | MT, Mad, Aad, Vad, TS, C, H, N, O | 10.25 |
| Ховор элементүүд | 3 | P, F, Cl | 0.015 |

---

### Conversion үр дүн

```python
# ad → d → daf conversions бүгд зөв precision-тэй
format_result(10.00, "Aad")   # "10.00"  (2 орон)
format_result(10.53, "Ad")    # "10.53"  (2 орон)
format_result(11.76, "Adaf")  # "11.76"  (2 орон) - technically should be 0

# Ховор элементүүд
format_result(0.015, "P,ad")  # "0.015"  (3 орон)
format_result(0.016, "P,d")   # "0.016"  (3 орон)

# Дулааны үнэлгээ
format_result(25432.8, "Qgr,ad")   # "25433"  (0 орон, бүхэл)
format_result(26315.2, "Qgr,d")    # "26315"  (0 орон)
```

---

## 🔧 API Reference

### `get_decimal_places(analysis_code: str) -> int`

Анализын кодоор тоон орон авах.

**Parameters:**
- `analysis_code` (str): Анализын код

**Returns:**
- `int`: Тоон орон (0, 1, 2, 3, ...)

**Examples:**
```python
>>> get_decimal_places("Aad")
2
>>> get_decimal_places("P")
3
>>> get_decimal_places("CV")
0
```

---

### `format_result(value: float, analysis_code: str) -> str`

Үр дүнг formatting хийх.

**Parameters:**
- `value` (float): Үр дүнгийн утга
- `analysis_code` (str): Анализын код

**Returns:**
- `str`: Formatted string

**Examples:**
```python
>>> format_result(10.256, "Aad")
'10.26'
>>> format_result(0.0156, "P")
'0.016'
>>> format_result(None, "Aad")
'-'
```

---

### `get_precision_summary() -> dict`

Тохиргооны хураангуй мэдээлэл.

**Returns:**
- `dict`: Summary info

**Example:**
```python
>>> summary = get_precision_summary()
>>> summary['total_codes']
75
>>> summary['by_precision'][2]
['MT', 'Mad', 'Aad', ...]
```

---

## ✅ Checklist

Precision тохиргоо өөрчлөх үед:

- [ ] `app/config/display_precision.py` засах
- [ ] `python scripts/manage_precision.py --test` ажиллуулах
- [ ] Бүх тест давсан эсэх шалгах
- [ ] Application дахин эхлүүлэх
- [ ] Browser refresh хийх (template cache)
- [ ] Sample тайлан шалгах

---

## 🎯 Үр дүнгийн нэгтгэл

### Өмнө vs Одоо

| Үзүүлэлт | Өмнө | Одоо |
|----------|------|------|
| Тохиргооны байршил | 5+ файл | 1 файл |
| Precision codes | ~20 | 75+ |
| Өөрчлөх | 5+ файл засах | 1 мөр засах |
| Тест | Байхгүй | Бүрэн |
| Удирдах tool | Байхгүй | CLI script |
| Consistency | ⚠️ Зарим | ✅ Баталгаатай |

---

## 📝 Санамж

1. **Precision өөрчилсний дараа:**
   - Application restart хийх
   - Browser cache цэвэрлэх
   - Тест ажиллуулах

2. **Шинэ анализ нэмэхдээ:**
   - Scientific precision стандарт баримтлах
   - Тест нэмэх
   - Documentation шинэчлэх

3. **Production deployment:**
   - Өөрчлөлтийг staging-д эхлээд тест
   - Users-д мэдэгдэх
   - Rollback plan бэлэн байх

---

**Үүсгэсэн:** 2025-11-29
**Статус:** ✅ PRODUCTION READY
**Анализын тоо:** 75+ codes
