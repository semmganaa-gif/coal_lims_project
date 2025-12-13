# Coal LIMS - Code Fixes

**Огноо:** 2025-12-11

Энэ файлд бүх засварлах кодуудыг жагсаав. Гараар хуулж тавина уу.

---

## 1. chat_api.py - LIKE Query Escape (Security Fix)

### 1.1 Import нэмэх (Line 14 дараа)
```python
from app.utils.security import escape_like_pattern
```

### 1.2 Line 146-147 засах
```python
# ХУУЧИН:
if search:
    query = query.filter(ChatMessage.message.ilike(f'%{search}%'))

# ШИНЭ:
if search:
    safe_search = escape_like_pattern(search)
    query = query.filter(ChatMessage.message.ilike(f'%{safe_search}%'))
```

### 1.3 Line 183-184 засах
```python
# ХУУЧИН:
q = ChatMessage.query.filter(
    ChatMessage.message.ilike(f'%{query_text}%'),

# ШИНЭ:
safe_query_text = escape_like_pattern(query_text)
q = ChatMessage.query.filter(
    ChatMessage.message.ilike(f'%{safe_query_text}%'),
```

### 1.4 Line 274-283 засах
```python
# ХУУЧИН:
query = request.args.get('q', '').strip()
if not query or len(query) < 2:
    return jsonify({'samples': []})

samples = Sample.query.filter(
    or_(
        Sample.sample_code.ilike(f'%{query}%'),
        Sample.client_name.ilike(f'%{query}%'),
        Sample.sample_type.ilike(f'%{query}%')
    )
).order_by(Sample.id.desc()).limit(20).all()

# ШИНЭ:
query = request.args.get('q', '').strip()
if not query or len(query) < 2:
    return jsonify({'samples': []})

safe_query = escape_like_pattern(query)
samples = Sample.query.filter(
    or_(
        Sample.sample_code.ilike(f'%{safe_query}%'),
        Sample.client_name.ilike(f'%{safe_query}%'),
        Sample.sample_type.ilike(f'%{safe_query}%')
    )
).order_by(Sample.id.desc()).limit(20).all()
```

---

## 2. datetime.now() → now_local() засах

### 2.1 equipment_routes.py

```python
# Файлын эхэнд import нэмэх:
from app.utils.datetime import now_local

# Line 27 засах:
# ХУУЧИН: today = datetime.now().date()
# ШИНЭ:
today = now_local().date()

# Line 256 засах:
# ХУУЧИН: action_date = datetime.strptime(...) if action_date_str else datetime.now()
# ШИНЭ:
action_date = datetime.strptime(action_date_str, "%Y-%m-%d") if action_date_str else now_local()

# Line 283 засах:
# ХУУЧИН: unique_filename = f"{int(datetime.now().timestamp())}_{filename}"
# ШИНЭ:
unique_filename = f"{int(now_local().timestamp())}_{filename}"

# Line 360 засах:
# ХУУЧИН: today_date = datetime.now()
# ШИНЭ:
today_date = now_local()

# Line 465-466 засах:
# ХУУЧИН:
# start_dt = ... if start_str else datetime.now() - timedelta(days=30)
# end_dt = ... if end_str else datetime.now()
# ШИНЭ:
start_dt = datetime.strptime(start_str, "%Y-%m-%d") if start_str else now_local() - timedelta(days=30)
end_dt = datetime.strptime(end_str, "%Y-%m-%d") if end_str else now_local()

# Line 500 засах:
# ХУУЧИН: year = int(request.args.get("year", datetime.now().year))
# ШИНЭ:
year = int(request.args.get("year", now_local().year))

# Line 570 засах:
# ХУУЧИН: today = datetime.now().date()
# ШИНЭ:
today = now_local().date()
```

### 2.2 report_routes.py

```python
# Файлын эхэнд import нэмэх:
from app.utils.datetime import now_local

# Line 48 засах:
# ХУУЧИН: y = int(request.args.get("year", datetime.now().year))
# ШИНЭ:
y = int(request.args.get("year", now_local().year))
```

### 2.3 samples_api.py

```python
# Файлын эхэнд import нэмэх:
from app.utils.datetime import now_local

# Line 809 засах:
# ХУУЧИН: filename = f"samples_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx"
# ШИНЭ:
filename = f"samples_{now_local().strftime('%Y%m%d_%H%M')}.xlsx"

# Line 846 засах:
# ХУУЧИН: filename = f"analysis_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx"
# ШИНЭ:
filename = f"analysis_{now_local().strftime('%Y%m%d_%H%M')}.xlsx"
```

### 2.4 audit_api.py

```python
# Файлын эхэнд import нэмэх:
from app.utils.datetime import now_local

# Line 337 засах:
# ХУУЧИН: filename = f"audit_log_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx"
# ШИНЭ:
filename = f"audit_log_{now_local().strftime('%Y%m%d_%H%M')}.xlsx"
```

### 2.5 shifts.py

```python
# Line 243 засах:
# ХУУЧИН: dt = datetime.now()
# ШИНЭ:
from app.utils.datetime import now_local
dt = now_local()
```

### 2.6 quality_helpers.py

```python
# Файлын эхэнд import нэмэх:
from app.utils.datetime import now_local

# Line 99 засах:
# ХУУЧИН: year = year or datetime.now().year
# ШИНЭ:
year = year or now_local().year
```

### 2.7 notifications.py

```python
# Файлын эхэнд import нэмэх:
from app.utils.datetime import now_local

# Line 301 засах:
# ХУУЧИН: today = datetime.now().date()
# ШИНЭ:
today = now_local().date()
```

---

## 3. Давхардсан код устгах

### 3.1 import_routes.py - Fallback устгах (Line 38-66)

```python
# ХУУЧИН (Line 38-66):
try:
    from app.utils.analysis_aliases import ALIAS_TO_BASE as _ALIAS_TO_BASE
    ALIAS_TO_BASE: Dict[str, str] = {k.lower(): v for k, v in _ALIAS_TO_BASE.items()}
except Exception as e:
    logger.warning(f"analysis_aliases модуль ачаалагдсангүй, fallback ашиглаж байна: {e}")
    ALIAS_TO_BASE = {
        "ts": "TS",
        ... # олон мөр
    }

# ШИНЭ (энгийнээр):
from app.utils.analysis_aliases import ALIAS_TO_BASE as _ALIAS_TO_BASE
ALIAS_TO_BASE: Dict[str, str] = {k.lower(): v for k, v in _ALIAS_TO_BASE.items()}
```

### 3.2 parameters.py - get_canonical_name() устгах

`parameters.py` дахь `get_canonical_name()` функцийг устгаж, `constants.py` дахийг ашиглах:

```python
# parameters.py дээр:
# ХУУЧИН:
def get_canonical_name(input_name):
    ...

# ШИНЭ:
from app.constants import get_canonical_name  # Шууд import хийх
```

---

## 4. _to_float() нэгтгэх

`app/utils/converters.py` файл үүсгэх:

```python
# app/utils/converters.py
# -*- coding: utf-8 -*-
"""
Төрөл хөрвүүлэх туслах функцүүд
"""
from typing import Any, Optional


def to_float(v: Any) -> Optional[float]:
    """
    Утгыг float болгох. Буруу утгад None буцаана.

    Args:
        v: Хөрвүүлэх утга (string, int, float)

    Returns:
        Optional[float]: Хөрвүүлсэн тоо эсвэл None

    Note:
        - "null", "none", "na" утгуудыг None гэж үзнэ
        - Таслалыг (,) цэг (.) болгож хөрвүүлнэ
    """
    if v is None:
        return None
    if isinstance(v, (int, float)):
        return float(v)
    if isinstance(v, str):
        s = v.strip().lower()
        if not s or s in ("null", "none", "na", "n/a", "-", ""):
            return None
        try:
            return float(s.replace(",", "."))
        except ValueError:
            return None
    return None
```

Дараа нь `import_routes.py` болон `helpers.py` дахь функцуудыг import-оор солих.

---

## 5. Dead Code / Unused Imports устгах

### 5.1 Unused Imports устгах

| Файл | Мөр | Устгах import |
|------|-----|---------------|
| `analysis_api.py` | 19 | `import traceback` |
| `index.py` | 18 | `from ... import Color` |
| `index.py` | 31 | `from ... import get_current_shift_start` |
| `index.py` | 738 | `import traceback` |
| `exports.py` | 39 | `from ... import dataframe_to_rows` |
| `repeatability_loader.py` | 4 | `from functools import lru_cache` |

### 5.2 Unused Variables устгах/засах

| Файл | Мөр | Хувьсагч | Засах арга |
|------|-----|----------|------------|
| `api_docs.py` | 31 | `tag` | `_tag` болгох эсвэл устгах |
| `exports.py` | 99 | `include_results` | `_` болгох эсвэл устгах |
| `monitoring.py` | 301 | `exc_type, exc_val, exc_tb` | `_` болгох |

### 5.3 monitoring.py засах (Line 301)

```python
# ХУУЧИН:
def __exit__(self, exc_type, exc_val, exc_tb):

# ШИНЭ:
def __exit__(self, _exc_type, _exc_val, _exc_tb):
```

### 5.4 api_docs.py засах (Line 31)

```python
# ХУУЧИН:
tag = ...

# ШИНЭ:
_tag = ...  # Unused variable marker
```

### 5.5 exports.py засах (Line 99)

```python
# ХУУЧИН:
include_results = ...

# ШИНЭ:
_ = ...  # Эсвэл устгах
```

---

## 6. Нэмэлт шалгалт - Функц дуудагдаагүй эсэх

Дараах функцууд дуудагдаагүй байж болзошгүй (шалгах хэрэгтэй):

```bash
# Vulture-ээр дэлгэрэнгүй шалгах:
vulture app/ --min-confidence 60
```

---

**Дууссан:** 2025-12-11
