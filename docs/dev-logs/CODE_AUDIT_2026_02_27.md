# Code Audit — 2026-02-27 (Өргөтгөсөн)

## Хамрах хүрээ
- 02-25 аудитын дараах бүх өөрчлөлт + шинэ файлууд
- 57 route файл (43 routes/ + 14 labs/)
- Templates (6 modified + 4 new)
- Models, Utils, JS

---

## CRITICAL засварууд (Бүгд хийгдсэн ✅)

| # | Асуудал | Файл | Засвар |
|---|---------|------|--------|
| C-1 | ✅ | `models/analysis.py` | `import json` нэмсэн |
| C-2 | ✅ | `routes/license/routes.py` | `@login_required` + admin check нэмсэн (5 endpoint) |
| C-3 | ✅ | `routes/reports/crud.py` | Extension whitelist + magic bytes + UUID filename + 5MB limit |
| C-4 | ✅ | `routes/imports/routes.py` | `admin` role check + batch_size bound |
| C-5 | ✅ | `auth.py`, `routes.py` | `is_safe_url()` referrer validation (4 газар) |
| C-6 | ✅ | `samples_api.py` | `escape()` нэмсэн (htmx search) |
| C-7 | ✅ | `license_protection.py` | `hmac.new()` HMAC signing болгосон |

## HIGH засварууд (Бүгд хийгдсэн ✅)

| # | Асуудал | Файл | Засвар |
|---|---------|------|--------|
| H-1 | ✅ | `water_ws_layout.html:738` | innerHTML escape `_e()` нэмсэн |
| H-2 | ✅ | `license.py`, `quality.py`, `license_protection.py` | `utcnow()` → `now_mn()` |
| H-3 | ✅ | `license_protection.py` | 5 мин кэш + 1 цаг тутамд DB write |
| H-4 | ✅ | `analysis_api.py`, `spare_parts/api.py`, `waste.py`, `samples_api.py` | `str(e)` → generic error + logger |
| H-5 | ✅ | `admin/routes.py`, `index.py`, `samples.py` | Flash `str(e)` → generic msg |
| H-6 | ✅ | `__init__.py` | petro_bp CSRF exempt устгасан |
| H-7 | ✅ | `quality/capa.py` | `@require_quality_edit` нэмсэн |
| H-8 | ✅ | `water routes.py:159` | `or` → `if is not None` (cfu_avg, ecoli, salmonella, staph) |
| H-9 | ✅ | `samples_api.py`, `audit_api.py` | `joinedload(sample, user)` нэмсэн |
| H-10 | ✅ | `water_ws_layout.html:1091` | `X-CSRF-TOKEN` → `X-CSRFToken` |

## Нэмэлт засварууд
- `reports/crud.py` — PDF path traversal `realpath` + `startswith`
- `imports/routes.py` — batch_size upper bound (5000)
- `license_protection.py` — middleware skip list шинэчлэгдсэн

---

## MEDIUM засварууд (Бүгд хийгдсэн ✅)

| # | Асуудал | Файл | Засвар |
|---|---------|------|--------|
| M-1 | ✅ | `water_utils.js:37-44` | `.replace(/'/g, '&#39;')` нэмсэн |
| M-2 | ✅ | `sfm_form.html:123` | default dilution 10→1 |
| M-3 | — | `routes.py` | Code duplication — refactor хойшлуулсан |
| M-4 | ✅ | `routes.py:2360-2368` | `func.count`/`func.max` batch query |
| M-5 | ✅ | `microbiology/routes.py` | try-except аль хэдийн байгаа |
| M-6 | ✅ | `reports/crud.py` | C-3 засварт хамрагдсан |
| M-7 | ✅ | `chat/events.py` | `markupsafe.escape()` бүх message-д |
| M-8 | ✅ | `chat/events.py` | `file_url` regex whitelist `/static/uploads/` |
| M-9 | ✅ | `routes.py`, `constants.py` | `VALID_WATER_ANALYSIS_CODES` frozenset |
| M-10 | ✅ | `water_ws_layout.html` | `r.ok` check нэмсэн |
| M-11 | ✅ | All child forms | Аль хэдийн null check хийгддэг |
| M-12 | ✅ | 4 model файл | `lazy="dynamic"` → `lazy="select"` |

## LOW засварууд (Бүгд хийгдсэн ✅)

| # | Асуудал | Файл | Засвар |
|---|---------|------|--------|
| L-1 | ✅ | `__init__.py` | 02-25 аудитад хийгдсэн (Permissions-Policy) |
| L-2 | ✅ | `lims-draft-manager.js` | Hard limit 2MB нэмсэн, хэтэрвэл save блоклоно |
| L-3 | ✅ | `core.py` | Password policy 8→10 char |
| L-4 | ✅ | `analysis_schema.py` | SQL blacklist → `^[A-Za-z0-9_]+$` whitelist regex |
| L-5 | ✅ | `hardware_fingerprint.py` | `if __name__` test block устгасан |
| L-6 | ✅ | `config.py` | Session 8h lifetime, Remember cookie HTTPOnly+SameSite+Secure |
| L-7 | ✅ | `lims-draft-manager.js` | `console.log` → `_log()` (localhost only debug mode) |

## Concurrency Audit (40 химич, 21 worksheet)

### CRITICAL (Бүгд хийгдсэн ✅)

| # | Асуудал | Файл | Засвар |
|---|---------|------|--------|
| CC-1 | ✅ | `config.py` | Pool 25+25=50 (40 user-д) |
| CC-2 | ✅ | `analysis_api.py:348` | Sample `with_for_update()` TOCTOU fix |
| CC-3 | ✅ | `water routes.py:891` | Sample `with_for_update()` TOCTOU fix |
| CC-4 | ✅ | `micro routes.py` | Sample + AR `with_for_update()` |
| CC-5 | ✅ | `chat/events.py` | `threading.Lock` online_users dict |

### HIGH (Бүгд хийгдсэн ✅)

| # | Асуудал | Файл | Засвар |
|---|---------|------|--------|
| CH-1 | ✅ | `models/analysis.py` | `UniqueConstraint('sample_id','analysis_code')` |
| CH-2 | ✅ | `water_ws_layout.html` | Partial save: `savedIds` only draft purge |
| CH-3 | ✅ | `models/analysis.py`, `database.py`, `analysis_api.py` | `version_id_col` optimistic lock + `StaleDataError` handler |
| CH-4 | ✅ | `__init__.py`, `config.py` | `memory://` production warning, Redis comment |
| CH-5 | ✅ | `gunicorn_config.py`, `requirements.txt` | `geventwebsocket` worker + packages |

### MEDIUM (Бүгд шалгагдсан ✅)

| # | Асуудал | Төлөв |
|---|---------|-------|
| CM-1 | Sample creation race | `sample_code unique=True` аль хэдийн байгаа |
| CM-2 | N+1 workspace load | `joinedload` аль хэдийн ашиглагдаж байгаа |
| CM-3 | SOLID deadlock | CC-2 Sample row lock дотор — deadlock байхгүй |

## 02-28 Production Readiness Fixes (commits: a332df6, f38d0f1)

### safe_commit тархалт — ~60 bare commit засагдсан
| Бүлэг | Файлууд | Тоо |
|-------|---------|-----|
| quality | capa, complaints, nonconformity, improvement | 12 |
| chemicals | crud, waste, api | 11 |
| reports | crud, routes, pdf_generator | 10 |
| spare_parts | crud, api | 11 |
| misc routes | auth, index, samples, analysis_api, chat_api, mass_api, equipment/api, imports | 12 |
| prev session | settings/routes, environmental, proficiency, email_sender, chat/events | 17 |

### Бусад засварууд
| # | Засвар | Commit |
|---|--------|--------|
| H-2 | innerHTML XSS — formatNum/formatValue escape, label/errorText | f38d0f1 |
| H-5 | CSRF 3600→1800s | a332df6 |
| H-9 | Composite indexes (4) + migration 53884d8642d7 | a332df6 |
| H-11 | Bulk delete try/except rollback | a332df6 |
| H-12 | Flask-Caching (SimpleCache/Redis) + KPI cache | f38d0f1 |
| H-16 | $.getJSON .fail() analysis_page.js | f38d0f1 |
| C-9 | SocketIO async_mode + message_queue configurable | a332df6 |
| C-10 | FormGuards.markDirty() — beforeunload (water ws, mass) | a332df6 |
| C-11 | FormGuards.guardButton() — double-submit (4 forms) | a332df6 |
| M-3 | statement_timeout=30000ms | a332df6 |

## Хойшлуулсан

| # | Асуудал | Шалтгаан |
|---|---------|----------|
| M-3 (audit) | Workspace route duplication | Refactoring scope том |
| H-5 (02-25) | License salt env var | Deployment хамааралтай |
| H-8 | FK NOT NULL (user_id) | 158 null rows data migration хэрэгтэй |
| H-14 | async def → def | Хэрэглэгч хадгалсан (ADR-001) |
