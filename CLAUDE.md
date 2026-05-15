# CLAUDE.md — Coal LIMS төслийн Claude-д зориулсан гарын авлага

> Энэ файл Claude Code өөр session-аас сэргэн орох үед төслийн контекстийг
> хурдан дуудах зорилготой. Урт танилцуулга биш — зөвхөн шууд хэрэгтэй зүйлс.

---

## Төсөл — нэг өгүүлбэр

**Coal LIMS** — нүүрс / ус хими / микробиологи / петрограф 4 лабын **ISO/IEC 17025:2017**-д
нийцсэн Flask-based Laboratory Information Management System. Олон лаб модуль
`BaseLab` pattern-аар нэгтгэгдэнэ. Хэл — Монгол (UI, commit message, dev лог).

## Stack

- **Backend:** Python 3.11+, Flask 3.x, SQLAlchemy 2.0
- **Frontend:** Alpine.js, htmx, AG Grid v32, Bootstrap 5, Chart.js
- **DB:** PostgreSQL 15 (prod) / SQLite (dev)
- **Real-time:** Flask-SocketIO (chat)
- **Cache:** Redis / SimpleCache
- **Test:** pytest (657+ critical test pass, **0 fail**, 89% coverage)
- **Build (frontend):** Vite 6 + Tailwind v4 (`npm install && npm run build`)

## Архитектурын давхарга — заавал баримтлах

```
Route → @transactional Service → Repository → Model
                ↓                       ↓
            commit/rollback         add/delete (no commit)
```

- **Routes** — Service-ийн public API дуудна. `db.session.commit()`-ыг
  `safe_commit()` helper-ээр centralize эсвэл @transactional service-р дамжуулна.
- **Services** — Business logic. `@transactional()` декоратораар transaction
  boundary тогтооно. `db.session.commit()` гар хийхгүй.
- **Repositories** — DB I/O-ийн цорын ганц цэг. Default `commit=False`,
  caller-ийн @transactional эсвэл explicit commit хариуцна.
- **Models** — SQLAlchemy ORM (~46 ширхэг).

**Pattern: public + atomic core (`_xxx_atomic` + `xxx`):**
```python
@transactional()
def _xxx_atomic(args) -> Result:
    # DB read + write + audit log
    return Result(...)

def xxx(args) -> Result:
    # Validation (no DB)
    try:
        return _xxx_atomic(args)
    except SQLAlchemyError as e:
        return _db_error_to_result(e)
```

Жишээ: `mass_service._save_mass_measurements_atomic`, `admin_service._delete_
standard_atomic`. Зорилго — StaleDataError/IntegrityError-ийг public translator-
оор тогтсон HTTP status code болгож буцаах.

## Лабын модулиуд

| Лаб | Зам | Шинжилгээ |
|-----|-----|-----------|
| Нүүрс | `app/labs/coal/` | 18 код (MT, Mad, Aad, Vdaf, TS, CV, CSN, Gi, TRD, P, F, Cl, XY...) — basis conversion (ad/d/daf/ar) |
| Ус хими | `app/labs/water_lab/chemistry/` | 32 параметр (PH, EC, NH4, NO2, TDS, COLOR…) — MNS/WHO лимит |
| Микробиологи | `app/labs/water_lab/microbiology/` | 8 код (CFU, ECOLI, SALM, AIR, SWAB…) — Ус/Агаар/Арчдас 3 ангилал |
| Петрограф | `app/labs/petrography/` | 7 код (MAC, VR, MM, TS_PETRO…) |

⚠️ **Нэр солилт:** `'water'` → `'water_chemistry'` бүрэн refactor хийгдсэн
(commit `e206e63`). Шинэ кодод `'water_chemistry'`-г ашиглана.

## Үндсэн фолдерууд

```
app/
├── bootstrap/      # Flask app factory + i18n + security headers
├── models/         # SQLAlchemy (core, analysis, equipment, chemicals, ...)
├── repositories/   # 45 repository class (бүх model хамрагдсан)
├── services/       # business logic, @transactional pattern (30+ функц)
├── labs/           # BaseLab + лаб бүрийн route/report/constants
├── routes/         # main, analysis, api, admin, equipment, chemicals, ...
├── utils/          # transaction.py (@transactional), database.py (safe_commit),
│                   # server_calculations/, conversions, audit, security helpers,
│                   # decorators, license_protection, hardware_fingerprint
├── templates/      # Jinja2 + analysis_forms/ (AG Grid форм 18+)
└── static/         # CSS, JS (aggrid_helpers, form_guards, xlsx)

config/             # dev/prod/test тохиргоо
migrations/         # Alembic
tests/              # pytest, 100+ файл, 657+ critical pass
SOP/                # ISO 17025 SOP
docs/dev-logs/      # dev session log + architecture audit/plan/progress
docs_all/           # албан ёсны баримт (60+ файл, README.md = index)
```

## Ажиллуулах команд

```bash
# Dev сервер (0.0.0.0:5000)
python run.py

# Production (Linux)
gunicorn -w 4 -b 0.0.0.0:8000 "app:create_app()"

# Production (Windows) — waitress

# Frontend bundle (Vite)
npm install                # Эхний удаа эсвэл package.json өөрчилсний дараа
npm run build              # Production bundle → app/static/dist/
npm run dev                # Dev mode (HMR, port 5173)

# Тест
pytest
pytest --cov=app --cov-report=html
pytest tests/test_services_admin.py tests/test_services_analysis_workflow.py  # critical

# Лиценз (CLI)
flask license info                           # Одоогийн лицензийн төлөв
flask license hwid                           # Энэ компьютерийн hardware ID
flask license allow-hardware <hwid>          # Нэг лицензээр хэд хэдэн компьютер
flask license clear-tamper                   # tampering flag арилгах
flask license generate --company X --expiry YYYY-MM-DD
```

## Архитектурын төлөв (2026-05-15 эцсийн байдлаар)

### ✅ ДУУССАН — Sprint 1-5 + Phase 0-4 audit + Phase 5 polish + Theme A/C/G

**Sprint 1 (Security/CSP):** S1.1a-e, S1.3, S1.4 (өмнө хийсэн)

**Sprint 4 — Service @transactional + commit устгал:**
- 30+ service функц @transactional pattern-д шилжсэн (mass, sample,
  analysis_workflow, admin × 15, equipment, instrument, report, sla,
  qc_chart, workflow_engine, report_builder)
- 13 repository default `commit=True` → `commit=False`
- Route layer-аас 30+ direct `db.session.commit()` устгасан
- `app/utils/transaction.py` — `@transactional` декоратор (ContextVar-аар
  nested support, SAVEPOINT биш гадна transaction-ыг ашиглана)
- `app/utils/database.py` — `safe_commit()`/`safe_delete()`/`safe_add()`
  route layer-ийн helper

**Sprint 5 — Repository pattern:**
- 14 → **45 repository** (21 шинэ model хамрагдсан)
- Service direct `Model.query` → repository method (68 газар)
- Шинэ repository файлууд:
  - `analysis_profile_repository.py`
  - `instrument_repository.py`
  - `planning_repository.py` (MonthlyPlan + StaffSettings)
  - `spare_parts_repository.py` (4 class)
  - `chemical_usage_repository.py` (Usage + Log + Waste × 2)
  - `solutions_repository.py` (Recipe + Preparation + Ingredient)
  - `worksheets_repository.py` (WaterWorksheet + Row)
  - `qc_chart_repository.py`
  - `license_repository.py`
  - `analysis_audit_repository.py`

**Sprint 2 — Vite bundle (CDN → local bundle):**
- 10 Vite entry: `main.js` (Bootstrap + jQuery + Alpine + collapse + htmx),
  `styles.css`, `aggrid.{js,css}`, `chart.js`, `datatables.{js,css}`,
  `tabulator.{js,css}`, `socketio.js`
- ~30 template-ийн CDN ref устгасан (29 уникальн CDN URL → 1 үлдсэн)
- Үлдсэн: DataTables i18n JSON data URL (runtime fetch хийдэг data, script биш)
- Build командууд: `npm install && npm run build` → `app/static/dist/` гарна
  (gitignored)
- Vite manifest helper: `app/utils/vite_assets.py` (vite_asset / vite_css_tag
  / vite_js_tag — base.html-аас autoload Jinja context-д)

**Sprint 3 — Dependency cleanup:**
- `sentry-sdk` 1.39.1 → 2.60.0 (major upgrade, `push_scope()` → `new_scope()`)
- Flask 3.1.2 → 3.1.3, SQLAlchemy 2.0.44 → 2.0.49, Flask-SocketIO 5.6.0 → 5.6.1
- `pytz` хадгалсан (Flask-Babel transitive dep)
- `gevent` (Linux gunicorn worker) + `waitress` (Windows server) хоёулаа
  хадгалсан — платформ тус бүрд хэрэгцээтэй

**Test cleanup:**
- 37 pre-existing test failure-ийг 0 болгосон
- Root cause: `get_locale` request context, LazyString → DB binding, legacy
  'water' lab_type, workflow mismatch, test fixture issues

### ✅ Sprint 4 closeout (2026-05-15)

- **`api/analysis_save.py`** — `db.session.commit()` ба StaleDataError/
  SQLAlchemyError translation-ийг `analysis_workflow._save_results_batch_
  atomic` (@transactional) + public `save_results_batch` translator-руу
  шилжүүлсэн (commit `789d73d`).
- **`equipment/crud.py:_commit_with_audit`** — мөн `equipment_service.
  _save_equipment_with_audit_atomic` (@transactional) + public
  `save_equipment_with_audit` translator-аар орлуулсан. Route helper нь
  одоо service дуудаад зөвхөн status-аар flash шиднэ.

### ✅ Phase 4 — SQLAlchemy 2.0 native API миграц (2026-05-15)

Legacy `Model.query.filter(...)` → modern `db.session.execute(select(Model).
where(...))` бүхэлд нь шилжсэн. Зорилго: SA 2.0 deprecation warning арилгах,
explicit session API-аар concurrent-safe + thread-pool friendly код.

**Хамрах хүрээ — 86 файл, ~370 occurrence:**
- Repository layer — 22 файл (`791a3fe`)
- Service layer — 12 файл (`97121c4`)
- Routes (4 batch) — 49 файл, ~165 occurrence (`556d900`, `49e1efc`,
  `a35b31f`, `46c1765`)
- Forms / Tasks / Utils — 4 файл (`46ab809`)

**Pattern:**
```python
# Legacy (Flask-SQLAlchemy implicit query)
items = Model.query.filter(Model.col == x).all()
count = Model.query.filter_by(...).count()
obj = Model.query.get(id)

# Modern (SA 2.0 native)
items = list(db.session.execute(select(Model).where(Model.col == x)).scalars().all())
count = db.session.execute(select(func.count(Model.id)).where(...)).scalar_one()
obj = db.session.get(Model, id)
```

**Lab base helper-уудын төрөл өөрчилсөн:**
- `app/labs/base.py:sample_query()` → `Query` биш `Select` буцаана
- `app/labs/petrography/routes.py:_pe_samples()` адил `Select`
- Caller-ууд `db.session.execute(stmt.order_by(...).limit(...)).scalars().all()`
- Count-д `stmt.with_only_columns(func.count(Sample.id)).order_by(None)`

**⚠️ Зориудаар үлдсэн (5 occurrence):**
- `app/services/analysis_workflow.py` дахь `AnalysisResult.query.filter_by(
  ...).with_for_update().first()` + `Sample.query.filter(...)` —
  `tests/test_services_analysis_workflow.py` module-level mock-той гүнзгий
  холбоотой (26 unit test rewrite). Дараа integration test болгож шилжүүлбэл
  засна.
- `app/services/import_service.py` — Batch commit pattern зориудаар үлдсэн.

### ✅ Phase 5 — Polish (2026-05-15 AM)

- **Theme A — Enum drift:** ~100 газар (5 commit). UserRole, SampleStatus,
  AnalysisResultStatus enum-аар бүх hard-coded role/status literal-ыг сольсон.
- **Constants wildcard → explicit:** 7 sub-module-ын `import *` → 52 explicit
  нэр (`app/constants/__init__.py`).
- **Magic numbers:** `MAX_SAMPLE_QUERY_LIMIT`, `DASHBOARD_RECENT_LIMIT = 500`,
  `CHEMICAL_LIST_LIMIT = 2000` константууд нэмж 8 газрын magic утгыг
  орлуулсан.
- **Equipment pagination:** `per_page=500 → 50`.
- **Pyflakes F401/F841/F541:** ~150 газрын ашиглаагүй import/variable/
  empty f-string цэвэрлэсэн.
- **Stale TODO + module header:** Sprint 1.1b stale TODO арилгасан,
  microbiology/constants.py header засагдсан.
- **2 NameError bug олж зассан:** `add_solution` дотор `Chemical` хэрэглэгддэг
  ч import-д байгаагүй; `petrography/routes.py` дотор `SQLAlchemyError`
  handler-д import дутуу.
- **pytest 0 warning:** datetime.utcnow() deprecation цэгцэлсэн +
  pytest-asyncio config-ыг засаж warning-ыг арилгасан.

### ✅ Phase 0-2 — Audit critical/mid-severity fixes (2026-05-15 PM)

Audit `AUDIT_SUMMARY_2026_05_14.md`-ийн бүх 13 H-severity bug verify
хийсэн (бүгд өмнөх sessions-д засагдсан байсан):

| Bug | Status |
|-----|--------|
| H1 audit.log path config | ✅ |
| H2 'hyanalt' Latin Cyrillic mix | ✅ |
| H3 HashableMixin × 5 model | ✅ |
| H4 MaintenanceLog.action_date | ✅ |
| H5 sample_repository disposal_date | ✅ |
| H6 workflow_engine role names | ✅ |
| H8/H9 admin_required dedup | ✅ |
| H10 WaterLaboratory dead class | ✅ |
| H11 petrography 'prepared' status | ✅ |
| H12 ALLOWED_LABS Enum | ✅ |
| H13 hardware_fingerprint cross-platform | ✅ |

**Phase 2 — ISO 17025 mid-severity:**
- **39 FK ondelete=SET NULL** (2 Alembic migration applied):
  - Audit FK-ууд: AuditLog.user_id, AnalysisResultLog.user_id + original_user_id
    (migration `2df88ac7f1d1`)
  - Operational user FK 36 ширхэг: chemicals, equipment, instrument, planning,
    quality_records, reports, solutions, spare_parts, bottles
    (migration `69695d8ac4e9`)

### ✅ Phase 3 Theme C — Decorator cleanup (2026-05-15 PM)

12 inline role check → `@role_required(...)` decorator. 27 → 13 газар
(52% reduction). Үлдсэн 13 нь contextual cases (in-loop ownership,
SocketIO event, template variable, query filter).

### ✅ Phase 3 Theme G — Timezone (substantial)

- Production-ын `datetime.now()`-уудыг `now_local()`-ээр сольсон (өмнөх).
- Test файлуудын 23 `datetime.utcnow()` (Python 3.12 deprecated) →
  `datetime.now()` (5 файл).
- ZoneInfo unavailable үед UTC+8 fallback тогтоосон (`app/utils/datetime.py`).

### 🔜 Үлдсэн ажил

- **`analysis_workflow.py`-ийн 5 legacy query** — Test mock decoupling шаардлагатай.
- **`import_service`** — Зориудаар batch-р commit хийдэг (large CSV
  memory + partial-failure tolerance), `@transactional` applicable биш.
- **Chat/UserOnlineStatus FK ondelete** — Phase 2 Models M2-ийн үлдсэн FK
  (CASCADE for message records, CASCADE for presence PK).
- **`db.DateTime(timezone=True)` migration** — Theme G full closure. Schema-
  level migration with backfill. Production-ын `license_protection.py:27-29`-н
  `now_mn() = now_local().replace(tzinfo=None)` strip pattern-ыг устгахад
  хэрэгтэй.
- **Phase 3 Theme D — i18n** — Service/Routes-аас Mongolian text-уудыг
  `lazy_gettext` (`_l()`)-ээр wrap + Babel translation catalog шинэчлэх.
- **Browser regression testing** — Phase 5 enum + Theme C refactor-ийн дараа
  real-world UI workflow шалгах.

## Conventions

- **Commit message:** Монгол хэл, conventional prefix (`feat:`, `fix:`,
  `refactor:`, `chore:`, `docs:`) — жишээ `5a980e2`, `e206e63`. Нэг мөр
  нийлбэр + bullet detail.
- **Co-author trailer:** Claude-ийн оролцоотой commit-д
  `Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>` нэмнэ.
- **Public + atomic split:** Service layer-ийн write функц нь
  `_xxx_atomic` (@transactional, business logic) + `xxx` (public, error
  translation) хосоор бичнэ.
- **Dev log:** `docs/dev-logs/<TOPIC>_<YYYY_MM_DD>.md` форматтай.
- **Доc хэл:** `docs_all/` дотор Mongolian + English холимог. Архитектур
  audit-ууд бараг бүхэлдээ Монгол.

## Анхаарах зүйлс

- **Repo public** ([github.com/semmganaa-gif/coal_lims_project](https://github.com/semmganaa-gif/coal_lims_project)).
  Нууц өгөгдөл, client мэдээлэл commit-д орохгүй байх.
- **License hardware-bound:** Нэг лицензээр хэд хэдэн компьютер ашиглах
  бол `flask license allow-hardware <hwid>` команд ажиллуулна. Hardware
  ID нь LicenseLog хүснэгтэд `event_type='hardware_mismatch'`-аас олно.
- **LazyString → DB column:** `_l(...)`-ийг шууд model field-д бичих бол
  `str(_l(...))`-ээр eager evaluate хийх (SQLAlchemy bind error-аас
  сэргийлэх).
- **`get_locale` request context-аас гадуур:** `has_request_context()`
  шалгалттай тул CLI/тест/background task-д default 'en'-ийг буцаана.
- **Vite build шаардлагатай:** Deploy эсвэл шинэ clone хийсэний дараа
  `npm install && npm run build` → `app/static/dist/` дотор хэшлэгдсэн
  JS/CSS гаргадаг. Энэ folder `.gitignore`-д орсон тул git-аас татагдахгүй.
  CSS/JS өөрчилсний дараа дахин `npm run build` хийх (dev mode-д
  `npm run dev` HMR-той ажиллана).
- **sentry-sdk v2 API:** `push_scope()` deprecated → `new_scope()`-ээр
  context manager бичнэ. `set_user`, `set_extra`, `add_breadcrumb`
  хэвээр ажиллана.
- **File-based audit/security log:** `instance/logs/audit.log` болон
  `security.log` нь `app/utils/audit.py:_write_file_log` ба
  `app/utils/license_protection.py:_log_event`-ээс бичигдэнэ (commit `b94d34c`).
  Integration тест: `tests/unit/test_audit.py::TestFileLoggers`. `logs/`
  фолдер хуучин — `instance/logs/` бол active path.
- **SA 2.0 query API:** Шинэ кодод `Model.query.filter(...)` бичих
  ХОРИОТОЙ. `db.session.execute(select(Model).where(...)).scalars().all()`
  pattern-аар бичнэ. `.first()` → `.scalars().first()` эсвэл
  `.scalar_one_or_none()`, `.get(id)` → `db.session.get(Model, id)`,
  `.count()` → `select(func.count(Model.id))` + `.scalar_one()`. Exception:
  `analysis_workflow.py`-ийн 5 газар + `import_service.py` (mocking болон
  batch commit-ийн улмаас).

## Шинэ session-д юу уншихыг зөвлөнө

1. Энэ `CLAUDE.md`
2. `git log --oneline -20`, `git status`
3. Шинэ Repository ашиглахаас өмнө `app/repositories/__init__.py` —
   бүх 45 repository-ийн экспорт нэгдсэн index
4. `app/utils/transaction.py` — @transactional pattern reference
5. Frontend ажил хийх бол:
   - `vite.config.js` — 10 Vite entry-ийн жагсаалт
   - `src/main.js` — vendor bundle (Bootstrap, jQuery, Alpine, htmx)
   - `app/utils/vite_assets.py` — Jinja helper (vite_css_tag, vite_js_tag)
6. `docs_all/README.md` — албан ёсны баримтын index
7. Зөвхөн хийх ажилд хамаатай файлуудыг (тэр үед нь)
