# Coal LIMS - Code Fixes

**Огноо:** 2025-12-13 (Шинэчлэгдсэн)
**Статус:** ✅ БҮГД ХИЙГДСЭН

---

## Засварын жагсаалт

| # | Засвар | Статус | Огноо |
|---|--------|--------|-------|
| 1 | chat_api.py - LIKE Query Escape | ✅ Хийгдсэн | 2025-12-11 |
| 2 | datetime.now() → now_local() (16 газар) | ✅ Хийгдсэн | 2025-12-13 |
| 3 | import_routes.py fallback устгах | ✅ Хийгдсэн | 2025-12-11 |
| 4 | _to_float() нэгтгэх | ✅ Хийгдсэн | 2025-12-13 |
| 5 | Unused imports устгах | ✅ Хийгдсэн | 2025-12-12 |
| 6 | requirements.txt security update | ✅ Хийгдсэн | 2025-12-13 |

---

## Дэлгэрэнгүй

### 1. chat_api.py - LIKE Query Escape (Security Fix)
- `escape_like_pattern()` нэмэгдсэн
- SQL injection эрсдэл арилсан

### 2. datetime.now() → now_local()
Бүх файлууд засагдсан:
- equipment_routes.py ✅
- report_routes.py ✅
- samples_api.py ✅
- audit_api.py ✅
- shifts.py ✅
- quality_helpers.py ✅
- notifications.py ✅
- index.py ✅

### 3. import_routes.py fallback
- Давхардсан ALIAS_TO_BASE fallback устгагдсан
- `analysis_aliases.py`-ээс import хийж байна

### 4. _to_float() нэгтгэх
- `app/utils/converters.py` үүсгэгдсэн
- import_routes.py дахь давхардал устгагдсан

### 5. Unused imports
- 40+ unused import устгагдсан
- flake8 F401/F841 алдаанууд засагдсан

### 6. requirements.txt Security Update
- Werkzeug 3.1.3 → 3.1.4 (CVE-2025-66221)
- python-socketio 5.10.0 → 5.15.0 (CVE-2025-61765)
- python-engineio 4.8.1 → 4.12.3

---

**Дууссан:** 2025-12-13
