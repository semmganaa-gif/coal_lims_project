# Code Review Session - 2026-03-08 (Delgerengui tailan)

## Hamrah huree

`app/routes/` dotor BUGD folder-uudiig systematik-aar shalgaj, kod chanariin zasvar hiisen.

**Niit 12 folder, ~40 file shalgagdsan. 27 file-d zasvar hiigdsen.**

---

## SESSION 1 (omno) - admin, analysis, api, chat

### 1. `app/routes/admin/routes.py` (825 mor)
**Zasvaruud:**
1. **SQLAlchemy BUG** (mor 283, 390): `AnalysisProfile.pattern is not None` -> `.isnot(None)` — Python `is not None` ni Column object deer **URGELJ True** butsaadag, CHPP profail shuultur ajillahgui baisan
2. **Race condition** — `activate_standard()`, `activate_gbw()`: `get_or_404` shalgaltiig bulk `update({is_active: False})`-iin **OMNO** shiljuulsen
3. **Helper extract** — `_auto_populate_profiles()` (~50 mor dedup), `_load_gi_shift_config()` (~15 mor dedup)
4. **Legacy** — 10x `.query.get_or_404()` -> `db.session.get()` + `abort(404)`
5. **Import** — PEP 8 daraallal, `json` negtgesen, aldagdsan `logger` nemsen

### 2. `app/routes/analysis/` (5 file -> 4 file)
- **`helpers.py` USTGASAN** (155 mor dead code) — QC constants, TIMER_PRESETS, analysis_role_required() bugdiig qc_config.py, decorators.py ruu shiljsen
- `kpi.py` — davhardsan import, emoji ustgasan
- `qc.py` — `import re` import daraallald shiljuulsen
- `senior.py` — **NoneType crash** (mor 202) zassan, 4 COUNT -> 1 query optimizatsid
- `workspace.py` — `type("V", ...)` hack, warning->debug, `if code in (...)` refactor

### 3. `app/routes/api/` (9 file)
- **`samples_api.py` — 2 NOTSTOI ALDAA:**
  1. `current_user` import dutuu — mg_summary POST "repeat" duudahad NameError crash
  2. `logging` import dutuu — except blok dotor NameError crash
- `analysis_api.py` — 5 zasvar (davhardsan import, .get_or_404, is_gbw init, audit log, commit try/except)
- `audit_api.py` — 7 zasvar (inline import tsegtselsen, int() try/except, N+1 query zasvar)
- `chat_api.py` — `== False` -> `.is_(False)` 6 gazar

### 4. `app/routes/chat/events.py`
- File path comment, import order zasvar

---

## SESSION 2 (unuudur) - chemicals, equipment, imports, license, main, quality, reports, settings, spare_parts

### 5. `app/routes/chemicals/` (3 file)

#### `crud.py` (591 mor)
- Import reorder (PEP 8: stdlib -> 3rd-party -> local), `abort` nemsen
- 5x `.query.get_or_404()` -> `db.session.get()` + `abort(404)` (mor 139, 276, 379, 431, 508)

#### `waste.py` (309 mor)
- Import reorder, `logger` buh import-iin daraa shiljuulsen, `abort` nemsen
- 2x `.query.get_or_404()` -> `db.session.get()` + `abort(404)` (mor 158, 204)

#### `api.py` (501 mor)
- 3x `int()` -> try/except (days, limit, chemical_id parameters)
- `datetime.strptime()` -> try/except + 400 error response
- 2x emoji comment ustgasan

### 6. `app/routes/equipment/` (4 file)

#### `crud.py` (574 mor)
- Import reorder + `abort` nemsen
- 6x `.query.get_or_404()` -> `db.session.get()` + `abort(404)` (Equipment: mor 78, 87, 209, 325, 428; MaintenanceLog: mor 553)
- `datetime.strptime()` -> try/except with fallback

#### `registers.py` (240 mor)
- Import reorder + `abort` nemsen
- 1x `.query.get_or_404()` -> `db.session.get()` + `abort(404)` (mor 172)

#### `api.py` (646 mor)
- 4x `datetime.strptime()` -> try/except + fallback (usage_summary, journal_detailed)
- `int()` -> try/except (monthly_stats year parameter)
- 1x emoji comment ustgasan

### 7. `app/routes/imports/routes.py` (582 mor)
- File path comment zassan: `# app/routes/import_routes.py` -> `# app/routes/imports/routes.py`
- `logger` import block-uudiin dundaas buh import-iin daraa shiljuulsen

### 8. `app/routes/license/routes.py` (98 mor)
- Tsever, zasvar shaardlagagui

### 9. `app/routes/settings/routes.py` (764 mor)
- File path comment zassan: `# app/routes/settings_routes.py` -> `# app/routes/settings/routes.py`
- Import reorder: stdlib -> 3rd-party -> local, `jsonify` ba `current_app` module level-d nemsen
- Emoji comment ustgasan: `# ✅ Монгол цагийн функц`
- 2x `.query.get_or_404()` -> `db.session.get()` + `abort(404)` (Bottle: mor 291, 331)
- 3x inline import ustgasan: `from flask import jsonify` (mor 203), `from flask import current_app` (mor 698, 737)
- `from app.constants import BOTTLE_TOLERANCE` module level-d shiljuulsen (mor 341-ees)

### 10. `app/routes/spare_parts/` (3 file)

#### `crud.py` (629 mor)
- Import reorder: `from datetime import datetime, date` stdlib ruu, `abort` nemsen
- **8x `.query.get_or_404()`** -> `db.session.get()` + `abort(404)`:
  - SparePartCategory: mor 154, 183
  - SparePart: mor 278, 388, 485, 524, 588, 623

#### `api.py` (303 mor)
- `logger` import block-iin dundaas buh import-iin daraa shiljuulsen
- Emoji comment ustgasan: `# ✅ SQL Injection хамгаалалт`

### 11. `app/routes/main/` (5 file)

#### `samples.py` (364 mor) — **BUG ZASSAN!**
- **NOTSTOI: `current_app` import dutuu** — `current_app.logger.error()` duudahad NameError crash garch baisan (mor 76, 249). `current_app`, `abort` import-d nemsen.
- 1x `.query.get_or_404()` -> `db.session.get()` + `abort(404)` (mor 29)
- Import reorder: stdlib -> 3rd-party -> local

#### `__init__.py`, `auth.py`, `helpers.py`, `index.py` — Tsever

### 12. `app/routes/quality/` (8 file)

#### `capa.py` (141 mor)
- Import reorder (stdlib -> 3rd-party -> local), `abort` nemsen
- 3x `.query.get_or_404()` -> `db.session.get()` + `abort(404)` (CorrectiveAction: mor 89, 101, 124)

#### `improvement.py` (140 mor)
- Import reorder, `abort` nemsen
- 3x `.query.get_or_404()` -> `db.session.get()` + `abort(404)` (ImprovementRecord: mor 90, 101, 125)

#### `nonconformity.py` (142 mor)
- Import reorder, `abort` nemsen
- 3x `.query.get_or_404()` -> `db.session.get()` + `abort(404)` (NonConformityRecord: mor 89, 101, 128)

#### `complaints.py` (379 mor)
- Import reorder (stdlib -> 3rd-party -> local), `abort` nemsen
- 3x `.query.get_or_404()` -> `db.session.get()` + `abort(404)` (CustomerComplaint: mor 258, 323, 345)

#### `control_charts.py` (463 mor)
- Import reorder: `import json`, `import logging`, `import statistics`, `from datetime import datetime` stdlib ruu
- Inline `import json` (mor 145) ustgasan — module level-d shiljuulsen
- 6x emoji comment ustgasan

#### `environmental.py` (51 mor)
- 6x `float(request.form[...])` -> try/except + flash + redirect
  - `temperature`, `humidity`, `temp_min`, `temp_max`, `humidity_min`, `humidity_max`
  - Buruu toon utga oruulahad ValueError crash-aas hamgaalsan

#### `proficiency.py` (93 mor)
- Import reorder (stdlib -> 3rd-party -> local)

#### `__init__.py` (37 mor) — Tsever

### 13. `app/routes/reports/` (5 file)

#### `crud.py` (396 mor)
- Import reorder: stdlib -> 3rd-party -> local, `abort` nemsen
- Constants (ALLOWED_IMAGE_EXTENSIONS, IMAGE_MAGIC_BYTES, MAX_SIGNATURE_FILE_SIZE) import-uudiin daraa shiljuulsen
- 5x `.query.get_or_404()` -> `db.session.get()` + `abort(404)`:
  - ReportSignature: mor 175
  - LabReport: mor 188, 224, 259, 293
- `datetime.strptime()` -> try/except + 400 JSON error response (API endpoint, mor 354, 356)

#### `email_sender.py` (141 mor)
- Import reorder: stdlib -> 3rd-party -> local, `abort` nemsen
- 1x `.query.get_or_404()` -> `db.session.get()` + `abort(404)` (LabReport: mor 108)

#### `pdf_generator.py` (344 mor)
- Import reorder: stdlib -> 3rd-party -> local

#### `routes.py` (~1441 mor)
- File path comment zassan: `# app/routes/report_routes.py` -> `# app/routes/reports/routes.py`
- Emoji comment ustgasan: `# ✅ ШИНЭ: Төвлөрсөн ээлжийн логикийг импортлох`

#### `__init__.py` (30 mor) — Tsever

---

## Niit statistik (2 session-iin niilber)

| Uzuulelt | Too |
|----------|-----|
| Shalgasan folder | 12 |
| Shalgasan file | ~40 |
| Zasvarlasen file | 27 |
| Ustgasan file | 1 (analysis/helpers.py dead code) |
| **NOTSTOI aldaa olson** | **5** |
| - NameError crash (import dutuu) | 3 (samples_api: current_user + logging, main/samples: current_app) |
| - SQLAlchemy filter bug | 1 (admin: `.isnot(None)`) |
| - Race condition | 1 (admin: activate_standard) |
| Legacy .query.get_or_404() zasvar | **53+ gazar** |
| int()/float() try/except nemsen | 10+ gazar |
| datetime.strptime() try/except | 8+ gazar |
| Import tsegtselsen (PEP 8) | 20+ file |
| Emoji comment ustgasan | 15+ gazar |
| N+1 query zasvar | 2 |
| Inline import module level-d | 8+ gazar |
| logger bayrshil zassan | 4 file |
| File path comment zassan | 3 file |

---

## Zasvariin turluur

### 1. `.query.get_or_404()` -> `db.session.get()` + `abort(404)` (53+ gazar)
SQLAlchemy 2.0-d `Query.get()` deprecated. Shineer:
```python
# BEFORE:
item = Model.query.get_or_404(id)
# AFTER:
item = db.session.get(Model, id)
if not item:
    abort(404)
```

### 2. int()/float()/strptime() web input validation (18+ gazar)
Web request-ees irsen parameter-uudiig parse hiihded:
```python
# BEFORE:
days = int(request.args.get("days", 30))  # ValueError crash!
# AFTER:
try:
    days = int(request.args.get("days", 30))
except (ValueError, TypeError):
    days = 30
```

### 3. Import daraallal (PEP 8) (20+ file)
```python
# Zugeer:
import stdlib_modules      # 1. stdlib
from flask import ...      # 2. 3rd-party
from app import ...        # 3. local
logger = logging.getLogger(__name__)  # import-iin daraa
```

### 4. Emoji comment ustgasan (15+ gazar)
`# ✅ ...` -> `# ...` buyu bugd ustgasan

### 5. `== False` -> `.is_(False)` (SQLAlchemy boolean)
SQLAlchemy boolean haritsuulaltad `==` biish `.is_()` ashiglah

---

## Bug-iin notstoi zereg

| Zereg | Tailbar | File | Mor |
|-------|---------|------|-----|
| **CRITICAL** | `current_user` import dutuu -> NameError | samples_api.py | POST handler |
| **CRITICAL** | `logging` import dutuu -> NameError | samples_api.py | except block |
| **CRITICAL** | `current_app` import dutuu -> NameError | main/samples.py | 76, 249 |
| **HIGH** | `.isnot(None)` SQL bug -> shuultur ajillahgui | admin/routes.py | 283, 390 |
| **HIGH** | Race condition -> standard idvehijuuleh ued | admin/routes.py | activate_standard |
| **MEDIUM** | `.query.get_or_404()` deprecated | 53+ gazar | buh routes |
| **MEDIUM** | float/int/strptime try/except dutuu | 18+ gazar | web input |
| **LOW** | Import daraallal, emoji, logger bayrshil | 20+ file | buh folder |

---

## Syntax shalgalt

Buh 27 zasvarlasen file `py_compile.compile()` damjsan. **0 syntax error.**

---

## Uldsen ajil

- `app/routes/` dotorh BUH folder shalgagdaj duussan
- Test ajilluulah (pytest) — shineer nemsen abort(404) logic zuv ajillaj baigaag batagaljuulah
- `main/index.py` — ih file (900 mor), logic zuv baigaa ch code refactor hiij bolno (hoishluulah)
