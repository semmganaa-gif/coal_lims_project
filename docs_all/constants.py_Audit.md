# constants.py Audit
**Огноо:** 2026-02-05
**Файл:** `app/constants.py` (1,070 мөр, 46 constant)

---

## 1. Бүтцийн тойм

### 1.1 Хэсгүүд
| # | Хэсэг | Мөр | Тоо |
|---|-------|-----|-----|
| 1 | PARAMETER_DEFINITIONS | 25-238 | 35+ param |
| 2 | SAMPLE_TYPE_CHOICES | 246-260 | 7 client |
| 3 | CHPP CONFIG | 261-620 | 5 config |
| 4 | WTL CONFIG | 620-760 | 5 config |
| 5 | MASTER_ANALYSIS_TYPES_LIST | 760-780 | 20 type |
| 6 | ERROR REASONS | 786-808 | 8 reason |
| 7 | NAME_CLASS_SPECS | 900-987 | 9 spec |
| 8 | SUMMARY_VIEW_COLUMNS | 993-1023 | 24 column |
| 9 | APP CONFIG | 1030-1070 | 15 config |

### 1.2 Нийт тогтмолууд: 46

---

## 2. Ашиглаагүй тогтмолууд

### 2.1 HTTP Status Constants - АШИГЛААГҮЙ
**Мөр:** 1063-1070

```python
HTTP_OK = 200              # 0 references
HTTP_MULTI_STATUS = 207    # 0 references
HTTP_BAD_REQUEST = 400     # 0 references
HTTP_UNAUTHORIZED = 401    # 0 references
HTTP_FORBIDDEN = 403       # 0 references
HTTP_NOT_FOUND = 404       # 0 references
HTTP_SERVER_ERROR = 500    # 0 references
```

**Санал:** Устгах эсвэл ашиглаж эхлэх (hard-coded 200, 400, 403 гэх мэт-ийг солих)

---

### 2.2 MASTER_ANALYSIS_TYPES_LIST - АШИГЛААГҮЙ + ДАВХАРДСАН
**Мөр:** 760-780

```python
MASTER_ANALYSIS_TYPES_LIST = [
    {'code': 'MT', 'name': 'Нийт чийг (MT)', 'order': 1, 'role': 'chemist'},
    # ... 20 entry
]
```

**Асуудал:** `admin_routes.py:53-74` дээр яг ижил өгөгдөл `required_analyses` нэрээр давхардсан!

**Санал:** `admin_routes.py`-г constants-оос import хийх болгох:
```python
# admin_routes.py
from app.constants import MASTER_ANALYSIS_TYPES_LIST as required_analyses
```

---

### 2.3 Бусад ашиглаагүй
| Constant | References | Санал |
|----------|-----------|-------|
| `MAX_DESCRIPTION_LENGTH` | 0 | Validation-д ашиглах |
| `MAX_IMPORT_BATCH_SIZE` | 0 | Excel import-д ашиглах |
| `MAX_SAMPLE_QUERY_LIMIT` | 0 | Query-д ашиглах |
| `MAX_ANALYSIS_RESULTS` | 1 (define only) | Ашиглах эсвэл устгах |
| `GI_SHIFT_CONFIG` | 1 (define only) | DB-д аль хэдийн байгаа |

---

## 3. Давхардсан өгөгдөл

### 3.1 Analysis Types - 2 газар
| Байршил | Нэр | Элемент |
|---------|-----|---------|
| `constants.py:760` | `MASTER_ANALYSIS_TYPES_LIST` | 20 шинжилгээ |
| `admin_routes.py:53` | `required_analyses` | 20 шинжилгээ (+ PE) |

**Ялгаа:**
- `constants.py`: FM=12, Solid=11 дараалал
- `admin_routes.py`: FM=17, Solid=18 дараалал + PE=20 нэмсэн

**Статус:** ⚠️ Нэгтгэх шаардлагатай

---

## 4. Сайн талууд ✅

### 4.1 Бүтцийн зохион байгуулалт
- ✅ Хэсэг бүр тусдаа comment-тэй
- ✅ Related constants хамт байрлуулсан
- ✅ ISO стандарт code-ууд тодорхой

### 4.2 Тохиргооны тогтмолууд
- ✅ BOTTLE_TOLERANCE - MNS стандарт
- ✅ PARAMETER_DEFINITIONS - lab_code, standard_method тодорхой
- ✅ LAB_TYPES - icon, color тодорхой

### 4.3 Windows UTF-8 fix
- ✅ Line 11-18: Console encoding fix with proper error handling

---

## 5. Засах дараалал

| # | Асуудал | Түвшин | Статус |
|---|---------|--------|--------|
| 1 | HTTP_* constants ашиглаагүй | LOW | ⏸️ Хойшлуулах |
| 2 | MASTER_ANALYSIS_TYPES_LIST давхардал | MODERATE | 🔧 Нэгтгэх |
| 3 | MAX_* constants ашиглаагүй | LOW | ⏸️ Хойшлуулах |
| 4 | GI_SHIFT_CONFIG deprecated | LOW | ⏸️ DB-д шилжсэн |

---

## 6. Хураангуй

| Хэмжүүр | Утга |
|---------|------|
| Нийт мөр | 1,070 |
| Нийт constant | 46 |
| Ашиглаагүй | 9 |
| Давхардсан | 1 (analysis types) |
| Устгаж болох | ~30 мөр (HTTP_*) |

---

## 7. Зөвлөмж

### Шууд засах
1. ~~HTTP_* constants устгах~~ → Хойшлуулсан (ирээдүйд ашиглаж болно)

### Refactor
1. `MASTER_ANALYSIS_TYPES_LIST` → `admin_routes.py`-д import хийх
2. Ашиглаагүй MAX_* constants → Validation-д ашиглаж эхлэх эсвэл устгах

---

*Шинжилгээг хийсэн: Claude Code*
*Огноо: 2026-02-05*
