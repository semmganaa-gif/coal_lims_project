# PRECISION & REPEATABILITY БАРИМТ БИЧИГ
# LIMS System
# Огноо: 2025-12-04

---

## 1. ХУРААНГУЙ

| Систем | Файл | Статус |
|--------|------|--------|
| Display Precision | `app/config/precision.py` | ✅ Production Ready |
| Repeatability (T) | `app/config/repeatability.py` | ✅ Production Ready |

**Давуу талууд:**
- ✅ Бүх тохиргоо нэг Python файлд төвлөрсөн
- ✅ JavaScript hardcoded устгасан
- ✅ Серверээс frontend-д автоматаар дамжина
- ✅ Management scripts бэлэн

---

## 2. DISPLAY PRECISION (Тоон орон)

### 2.1 Тохиргооны файл
**Файл:** `app/config/precision.py`

```python
DECIMAL_PLACES = {
    'Aad': 2,      # 10.25%
    'P': 3,        # 0.015%
    'CV': 0,       # 25000 J/g
    'CSN': 1,      # 5.5
    # ... бусад
}
DEFAULT_DECIMAL_PLACES = 2
```

### 2.2 Хэрэглээ

**Template-д (Jinja2):**
```jinja
{{ sample.ash_value|fmt_result('Aad') }}  {# 10.25 (2 орон) #}
{{ sample.phosphorus|fmt_result('P') }}   {# 0.015 (3 орон) #}
```

**Python код дээр:**
```python
from app.config.precision import format_result, get_decimal_places

formatted = format_result(10.256, "Aad")  # "10.26"
places = get_decimal_places("P")          # 3
```

### 2.3 Precision Groups

| Бүлэг | Орон | Анализууд | Жишээ |
|-------|------|-----------|-------|
| Бүхэл тоо | 0 | CV, Gi, X, Y, CRI, CSR, TRD, FM | 25000 |
| 1 орон | 1 | CSN | 5.5 |
| Стандарт | 2 | MT, Mad, Aad, Vad, TS, C, H, N, O | 10.25 |
| Ховор элементүүд | 3 | P, F, Cl | 0.015 |

### 2.4 Удирдах скрипт

```bash
python scripts/manage_precision.py list      # Бүх тохиргоо харах
python scripts/manage_precision.py --test    # Тест ажиллуулах
python scripts/manage_precision.py --code Aad # Тодорхой анализ тест
```

---

## 3. REPEATABILITY LIMITS (T)

### 3.1 Тохиргооны файл
**Файл:** `app/config/repeatability.py`

```python
from math import inf

LIMIT_RULES = {
    "Mad": {"bands": [
        {"upper": 0.50, "limit": 0.20, "mode": "abs"},
        {"upper": 5.00, "limit": 0.20, "mode": "abs"},
        {"upper": 10.0, "limit": 0.30, "mode": "abs"},
        {"upper": inf,  "limit": 0.40, "mode": "abs"},
    ]},
    "CSN": {"single": {"limit": 0.50, "mode": "abs"}},
    # ... 20 анализ
}
```

### 3.2 Хэрэглээ

**Backend (Python):**
```python
from app.utils.repeatability_loader import load_limit_rules
from app.routes.api.helpers import _effective_limit

rules = load_limit_rules()
limit, mode, band_label = _effective_limit("Mad", 3.5)
# (0.20, "abs", "0.5-5.0")
```

**Frontend (JavaScript):**
```javascript
const limit = getRepeatabilityLimit('Mad', 3.5);  // 0.20
```

### 3.3 Mode Types

| Mode | Тайлбар | Жишээ |
|------|---------|-------|
| `"abs"` | Absolute (үнэмлэхүй утга) | T = 0.20 |
| `"percent"` | Percent (хувиар) | T = дундаж × 0.50% |

### 3.4 Band Rules Жишээ

**Чийг (Mad):**
| Дундаж Хүрээ | Limit | Mode |
|-------------|-------|------|
| ≤ 0.5 | 0.20 | abs |
| 0.5 < x ≤ 5.0 | 0.20 | abs |
| 5.0 < x ≤ 10.0 | 0.30 | abs |
| > 10.0 | 0.40 | abs |

**Үнс (Aad):**
| Дундаж Хүрээ | Limit | Mode |
|-------------|-------|------|
| ≤ 15.0 | 0.20 | abs |
| 15.0 < x ≤ 30.0 | 0.30 | abs |
| > 30.0 | 0.50 | abs |

### 3.5 Удирдах скрипт

```bash
python scripts/manage_repeatability.py list      # Бүх тохиргоо
python scripts/manage_repeatability.py --test    # Тест
python scripts/manage_repeatability.py --code Mad # Тодорхой анализ
```

---

## 4. ШИНЭ ТОХИРГОО НЭМЭХ

### 4.1 Шинэ Precision нэмэх

```python
# app/config/precision.py
DECIMAL_PLACES = {
    # ... existing codes ...
    'NEW_ANALYSIS': 2,  # Шинэ анализ
}
```

### 4.2 Шинэ Repeatability нэмэх

```python
# app/config/repeatability.py
LIMIT_RULES = {
    # Single limit
    "NEW_CODE": {"single": {"limit": 0.25, "mode": "abs"}},

    # Band limits
    "ANOTHER_CODE": {"bands": [
        {"upper": 10.0, "limit": 0.10, "mode": "abs"},
        {"upper": inf,  "limit": 0.20, "mode": "abs"},
    ]},
}
```

---

## 5. API ENDPOINTS

| Endpoint | Тайлбар |
|----------|---------|
| `GET /api/precision_config` | Precision тохиргоо авах |
| `GET /api/repeatability_config` | Repeatability тохиргоо авах |

---

## 6. CHECKLIST

Тохиргоо өөрчлөх үед:

- [ ] Config файл засах (precision.py эсвэл repeatability.py)
- [ ] Management script-ээр тест ажиллуулах
- [ ] Application restart хийх
- [ ] Browser cache цэвэрлэх
- [ ] Шинжилгээний form дээр шалгах

---

## 7. СТАТИСТИК

### Precision
- **Нийт анализ:** 75+ codes
- **Default:** 2 орон
- **Тест:** 12/12 амжилттай (100%)

### Repeatability
- **Нийт анализ:** 20 codes
- **Single limits:** 7 анализ
- **Band limits:** 13 анализ
- **Тест:** 94/94 амжилттай (100%)

---

**Сүүлд шинэчилсэн:** 2025-12-04
