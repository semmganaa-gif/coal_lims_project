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
- **Test:** pytest (~10 400 тест, README дээр 64%, сүүлийн ажилд **89%** coverage)

## Архитектурын давхарга — заавал баримтлах

```
Route → Service → Repository → Model
```

- **Routes** — зөвхөн service-ийн public API дуудна. `db.session.*` болон
  `Model.query.*`-ыг **route-д бичихгүй**.
- **Services** — business logic. Repository-гоор дамжина. `db.session.commit()`
  зөвхөн `@transactional` wrapper-аар.
- **Repositories** — DB I/O-ийн цорын ганц цэг.
- **Models** — SQLAlchemy ORM (~46 ширхэг).

> Энэ дүрэм одоогоор бүрэн биелээгүй (Sprint 4–5-аар цэвэрлэж байна). Шинэ код
> бичих үед энэ давхаргын дагуу бичиж, refactor-д routes/services-аас
> `db.session` / `.query` хасах чиглэлтэй.

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
├── bootstrap/      # Flask app factory + security headers
├── models/         # SQLAlchemy (core, analysis, equipment, chemicals, ...)
├── repositories/   # 14 repository файл
├── services/       # business logic (sample, analysis_workflow, chemical, ...)
├── labs/           # BaseLab + лаб бүрийн route/report/constants
├── routes/         # main, analysis, api, admin, equipment, chemicals, ...
├── security/       # decorators (@lab_required, @role_required), license, fingerprint
├── utils/          # server_calculations/, conversions, westgard, audit
├── templates/      # Jinja2 + analysis_forms/ (AG Grid форм 18+)
└── static/         # CSS, JS (aggrid_helpers, form_guards, xlsx)

config/             # dev/prod/test тохиргоо
migrations/         # Alembic
tests/              # pytest, 100+ файл
SOP/                # ISO 17025 SOP
docs/dev-logs/      # dev session log + architecture audit/plan/progress
docs_all/           # албан ёсны баримт (60+ файл, README.md = index)
```

## Ажиллуулах команд

```bash
# Dev сервер
python run.py

# Production (Linux)
gunicorn -w 4 -b 0.0.0.0:8000 "app:create_app()"

# Production (Windows) — waitress

# Тест
pytest
pytest --cov=app --cov-report=html
pytest tests/unit/
```

## Идэвхтэй ажил (2026-05-09 байдлаар)

**Architecture Sprint 1** (`docs/dev-logs/ARCHITECTURE_PROGRESS_2026_04_22.md`):

- ✅ S1.4 — `X-XSS-Protection` header хассан
- ✅ S1.1a — CSP nonce + `base-uri` / `form-action` hardening
- ✅ S1.3 — `config/database.py` dialect-ийн дагуу `connect_args`
- 🔜 **S1.1b** — 277 inline event handler → external JS (3 batch-аар).
  Эхний batch (`errors/`, `spare_parts/`, `settings/`) хэсэгчлэн эхэлсэн,
  шинэ `app/static/js/csp_handlers.js` үүсгэсэн, **commit-логдоогүй**
  ~38 modified template/JS байна.
- ⏳ S1.1c — 44+ inline style → class
- ⏳ S1.1d — Alpine CSP build руу шилжих
- ⏳ S1.1e — `'unsafe-inline'` + `'unsafe-eval'` хасах

**Дараагийн sprint-үүд (төлөвлөсөн):**

- Sprint 2 — Vite bundle (CDN-ыг local bundle руу)
- Sprint 3 — Dependency cleanup (sentry-sdk 1→2, pytz хасах, gevent vs waitress)
- Sprint 4 — Routes-аас `db.session.*` / `.query` хасах (196 call-site)
- Sprint 5 — Services → Repositories давхаргын цэвэрлэгээ

## Conventions

- **Commit message:** Монгол хэл, conventional prefix (`feat:`, `fix:`, `refactor:`, `chore:`)
  — жишээ: `commit f9e051a`, `e206e63`. Нэг мөр нийлбэр + bullet detail.
- **Co-author trailer:** Claude-ийн оролцоотой commit-д `Co-Authored-By: Claude ...` нэмдэг.
- **Dev log:** `docs/dev-logs/<TOPIC>_<YYYY_MM_DD>.md` форматтай.
- **Доc хэл:** `docs_all/` дотор Mongolian + English холимог. Архитектур audit-ууд бараг бүхэлдээ Монгол.

## Анхаарах зүйлс

- **Repo public** ([github.com/semmganaa-gif/coal_lims_project](https://github.com/semmganaa-gif/coal_lims_project)).
  Нууц өгөгдөл, client мэдээлэл commit-д орохгүй байх.
- **`instance/logs/security.log` болон `logs/audit.log`** бараг хоосон —
  production audit logging тохиргоо ажиллахгүй байх магадлалтай. Шалгах хэрэгтэй.
- **`docs_all/README.md` "39% coverage"** гэж бичсэн — хоцрогдсон. Бодит coverage 89%.
- **CRLF/LF warning:** `git diff`-д их хэмжээний LF→CRLF warning гарна (Windows).
  `.gitattributes` тохиргоог дараа цэгцлэх.

## Шинэ session-д юу уншихыг зөвлөнө

1. Энэ `CLAUDE.md`
2. `git log --oneline -10`, `git status`
3. `docs/dev-logs/ARCHITECTURE_PROGRESS_2026_04_22.md` — идэвхтэй sprint
4. `docs_all/README.md` — албан ёсны баримтын index
5. Зөвхөн хийх ажилд хамаатай файлуудыг (тэр үед нь)
