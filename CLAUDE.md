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

## Архитектурын төлөв (2026-05-14 байдлаар)

### ✅ ДУУССАН — Sprint 1, 2, 3, 4, 5 + test cleanup

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

### 🔜 Үлдсэн ажил

- **`api/analysis_save.py`** — StaleDataError 409 vs SQLAlchemyError 500
  тусгай error handling-той тул `safe_commit`-аар орлоогүй, route-д
  үлдсэн.
- **`equipment/crud.py:_commit_with_audit`** — IntegrityError vs SQLAlchemy
  Error ялгаатай flash өгөх тусгай helper, route-домэйн транзакц hooks-той
  тул `safe_commit`-аар орлоогүй.
- **`import_service`** — Зориудаар batch-р commit хийдэг (large CSV
  memory + partial-failure tolerance), `@transactional` applicable биш.
- **Major dep upgrades** — celery 5.4→5.6 (minor), redis 5→7 (major),
  gunicorn 24→26 (major). Тус тусын session-д careful upgrade.

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
- **`instance/logs/security.log` болон `logs/audit.log`** бараг хоосон —
  production audit logging тохиргоо ажиллахгүй байх магадлалтай. Шалгах
  хэрэгтэй.
- **`docs_all/README.md` "39% coverage"** гэж бичсэн — хоцрогдсон. Бодит
  coverage 89%.
- **CRLF/LF warning:** `git diff`-д их хэмжээний LF→CRLF warning гарна
  (Windows). `.gitattributes` тохиргоог дараа цэгцлэх.

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
