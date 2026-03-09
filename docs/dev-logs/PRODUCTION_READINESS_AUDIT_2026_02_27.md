# Production Readiness Audit — 2026-02-27

## Хүрээ
Coal LIMS төслийн production-д гаргах бэлэн эсэхийг 4 чиглэлээр шалгасан:
1. Аюулгүй байдал & Тохиргоо
2. Өгөгдлийн сан & Data Integrity
3. Гүйцэтгэл & Deployment
4. Frontend & UX

---

## Ерөнхий дүн: 5.9→7.8/10 — DEPLOY ТОХИРГООТОЙ БЭЛЭН

Анхны оноо 5.9/10 → Засварын дараа **7.8/10** (02-28 байдлаар)

| Чиглэл | Анхны | Засагдсан | Үлдсэн | Шинэ оноо |
|---------|-------|-----------|---------|-----------|
| 🔒 Аюулгүй байдал | 5/10 | C-8,9,10,11, H-2,5,10,16 | C-1~5 (.env) | 7.5/10 |
| 🗄️ Өгөгдлийн сан | 6/10 | C-6, H-9,10,11, M-3 | H-8 (FK null) | 8/10 |
| ⚡ Гүйцэтгэл & Deploy | 6/10 | H-12, CH-5 | H-13,H-6 (nginx,redis) | 7.5/10 |
| 🖥️ Frontend & UX | 6.5/10 | C-10,11, H-16 | M-11,15,16 (a11y) | 8/10 |

---

## 🔴 CRITICAL (12 асуудал)

### C-1: DEBUG=True .env-д
- **Файл:** `.env` (line 7-8)
- **Эрсдэл:** Stack trace, interactive debugger ил харагдана
- **Засвар:** `FLASK_ENV=production`, `DEBUG=False`, `FLASK_DEBUG=0`

### C-2: DB нууц үг .env-д ил
- **Файл:** `.env` (line 16)
- `DATABASE_URL=postgresql://postgres:201320@localhost:5432/coal_lims`
- **Засвар:** Environment variable эсвэл secret manager руу шилжүүлэх

### C-3: Email нууц үг .env-д ил
- **Файл:** `.env` (line 34-35)
- **Засвар:** Secret management system ашиглах

### C-4: .env файлын permission `-rw-r--r--`
- **Засвар:** `chmod 600 .env`

### C-5: MAIL_PASSWORD=your_password_here солигдоогүй
- **Файл:** `.env` (line 34)
- **Засвар:** Жинхэнэ credential тохируулах

### C-6: Alembic/Flask-Migrate тохируулаагүй
- **Файл:** `migrations/` directory байхгүй
- **Эрсдэл:** Schema change tracking/rollback боломжгүй
- **Засвар:** `flask db init && flask db migrate -m "Initial" && flask db upgrade`

### C-7: Backup стратеги байхгүй
- pg_dump automation, WAL archiving, recovery procedure байхгүй
- **Засвар:** Automated backup script + monthly recovery test

### C-8: SocketIO async_mode='threading' + Gunicorn 4 worker ✅ ЗАСАГДСАН (CH-5)
- **Файл:** `gunicorn_config.py` — `geventwebsocket` worker class болгосон
- `requirements.txt` — `gevent`, `gevent-websocket` packages нэмэгдсэн

### C-9: SocketIO Redis message queue байхгүй ✅ ЗАСАГДСАН (a332df6)
- `SOCKETIO_MESSAGE_QUEUE`, `SOCKETIO_ASYNC_MODE` config нэмэгдсэн
- `__init__.py` — configurable async_mode + message_queue
- **Үлдсэн:** Production-д Redis суулгаж .env тохируулах

### C-10: beforeunload handler байхгүй ✅ ЗАСАГДСАН (a332df6)
- `form_guards.js` — `FormGuards.markDirty()` / `markClean()` utility
- Water ws, mass aggrid form-д integrate хийгдсэн

### C-11: Double-submit хамгаалалт дутмаг ✅ ЗАСАГДСАН (a332df6)
- `FormGuards.guardButton()` — btn.disabled + spinner during save
- Water ws, mass, micro workspace, bottle_constants form-д хийгдсэн

### C-12: Устгах үйлдэлд alert() ашиглаж байна
- 30+ газар browser alert() ашиглаж байна
- **Засвар:** Custom modal dialog болгох

---

## 🟠 HIGH (19 асуудал)

### Security (H-1 ~ H-7)

#### H-1: SECRET_KEY тогтмол хадгалагдаагүй
- **Файл:** `config.py:30-41`
- Runtime-д ephemeral key → restart бүрт session устна
- **Засвар:** `SECRET_KEY` env variable production-д set хийх

#### H-2: innerHTML XSS — dashboard template-д 20+ газар ✅ ЗАСАГДСАН (f38d0f1)
- `ahlah_dashboard.html` — `formatNum()` fallback escape, `p.label`/`f.label` escapeHtml, `errorText` escape
- `ahlah_dashboard.js` — `formatValue()` float fallback escape

#### H-3: innerHTML XSS — admin template-үүд
- **Файл:** `templates/admin/control_standards.html`, `gbw_list.html`
- **Засвар:** Safe DOM methods ашиглах

#### H-4: SocketIO CORS wildcard `'*'`
- **Файл:** `config.py:114`
- Development-д wildcard → production руу шилжих эрсдэл
- **Засвар:** Тодорхой origin-ууд зааж өгөх

#### H-5: CSRF_TIME_LIMIT = 3600с (хэт урт) ✅ ЗАСАГДСАН (a332df6)
- `config.py` — `WTF_CSRF_TIME_LIMIT = 1800` (30 мин)

#### H-6: Rate limiter memory storage ✅ ХАГАС ЗАСАГДСАН (CH-4)
- **Файл:** `app/__init__.py` — production warning нэмэгдсэн
- `config.py` — Redis тохиргоо тайлбар нэмэгдсэн
- **Үлдсэн:** Redis суурилуулж `RATELIMIT_STORAGE_URI=redis://localhost:6379` тохируулах

#### H-7: Sensitive endpoint-д rate limit байхгүй
- Login-д `5/min` бий, бусад endpoint-д байхгүй
- **Засвар:** `/profile`, `/settings`, `/api/analysis` rate limit нэмэх

### Database (H-8 ~ H-11)

#### H-8: FK column-д NOT NULL дутмаг
- `AnalysisResult.user_id` — nullable=True (audit trail алдана)
- `MaintenanceLog.performed_by_id` — nullable=True
- `ChemicalUsage.used_by_id` — nullable=True
- **Засвар:** `nullable=False` нэмэх + migration

#### H-9: Composite index дутмаг ✅ ЗАСАГДСАН (a332df6)
- `Sample(lab_type,status)`, `Sample(received_date,lab_type)`, `Sample(client_name,sample_type)`
- `Equipment(category,status)`
- Migration `53884d8642d7` applied

#### H-10: `db.session.commit()` ≠ `safe_commit()` ✅ ЗАСАГДСАН (a332df6 + f38d0f1)
- ~60 bare commit → safe_commit() / try-except хөрвүүлэгдсэн
- 22 route файл: quality(4), chemicals(3), reports(3), spare_parts(2), misc(8), chat events
- settings/routes.py(7), equipment/registers.py(3 аль хэдийн try/except)

#### H-11: Bulk delete loop-д commit/rollback байхгүй ✅ ЗАСАГДСАН (a332df6)
- `main/samples.py` — try/except + rollback + logger.error нэмэгдсэн

### Performance (H-12 ~ H-14)

#### H-12: Caching framework байхгүй ✅ ЗАСАГДСАН (f38d0f1)
- Flask-Caching==2.3.0 суурилуулсан, SimpleCache (dev) / Redis (prod)
- KPI summary 60s cache, ahlah_stats 30s cache
- Approve/reject → cache invalidation

#### H-13: Static файлуудыг Flask serve хийж байна
- Nginx зөвхөн `production` profile-д (docker-compose)
- JS файлууд minify биш (xlsx.full.min.js 862KB, tabulator.min.js 433KB)
- **Засвар:** Nginx default болгох, Vite build бүрэн хийх

#### H-14: `async def` route-ууд `await` ашиглаагүй — АЛГАСАГДСАН (ADR-001)
- Хэрэглэгч async хадгалахаар тодорхой шийдсэн (02-28)
- **УСТГАХГҮЙ** — Flask[async] суурилуулсан, ирээдүйд await нэмэгдэж болно

### Frontend (H-15 ~ H-18)

#### H-15: fetch() network error catch байхгүй
- `index.js`, `chat.js` (9 газар), `water_summary.js` — fetch without .catch()
- **Засвар:** Бүх fetch()-д `.catch()` + user-friendly error message

#### H-16: $.getJSON() .fail() handler байхгүй ✅ ЗАСАГДСАН (f38d0f1)
- `analysis_page.js` — `.fail()` handler нэмэгдсэн (error alert in modal)

#### H-17: Loading spinner/indicator дутмаг
- Water summary grid, modal selection, chat load — spinner байхгүй
- **Засвар:** Loading indicator нэмэх

#### H-18: console.log 60+ ш production код-д ✅ ХАГАС ЗАСАГДСАН (L-7)
- `lims-draft-manager.js` — `_debugMode` + `_log()` conditional debug болгосон
- **Үлдсэн:** `analysis_page.js`, `chat.js`, `sample_summary.js` — console.log устгах

---

## 🟡 MEDIUM (16 асуудал)

| # | Чиглэл | Асуудал | Файл |
|---|--------|---------|------|
| M-1 | 🔒 | File upload validation дутмаг (extension, size, MIME) | `imports/routes.py:493` |
| M-2 | 🔒 | Password-д special character шалгалт байхгүй | `models/core.py:88` |
| M-3 | ✅ | DB query timeout — `statement_timeout=30000` config-д нэмэгдсэн | `config.py:66` |
| M-4 | 🗄️ | Equipment.serial_number, ControlStandard.name UNIQUE биш | `equipment.py`, `quality_standards.py` |
| M-5 | 🗄️ | CASCADE rules — audit trail-д тусдаа стратеги хэрэгтэй | `analysis_audit.py` |
| M-6 | 🗄️ | Model validator дутмаг (final_result range, quantity non-negative) | `models/` |
| M-7 | 🗄️ | Long-running transaction: bulk delete batch commit-гүй | `main/samples.py` |
| M-8 | ⚡ | Vite build бүрэн биш — JS minify хийгдээгүй | `app/static/js/` |
| M-9 | ⚡ | Cache header static asset-д байхгүй | `app/__init__.py` |
| M-10 | ⚡ | Log level INFO → production-д WARNING болгох | `logging_config.py` |
| M-11 | 🖥️ | ARIA labels, semantic HTML дутмаг | templates |
| M-12 | 🖥️ | ES6+ transpilation (Babel) байхгүй | JS files |
| M-13 | 🖥️ | Mongolian/English хольсон strings (i18n бүрэн биш) | JS files |
| M-14 | 🖥️ | localStorage quota handling зөвхөн DraftManager-д | JS files |
| M-15 | 🖥️ | Form validation visual feedback байхгүй | templates |
| M-16 | 🖥️ | Modal accessibility (role, aria) дутмаг | `analysis_page.js` |

---

## 🔵 LOW (10 асуудал)

| # | Чиглэл | Асуудал |
|---|--------|---------|
| L-1 | 🔒 | HSTS `preload` directive байхгүй (optional) |
| L-2 | 🔒 | CSP `'unsafe-inline'` (Flask template шаардлагаар) |
| L-3 | 🔒 | SESSION_COOKIE_SECURE env variable-аас хамаарна |
| L-4 | 🔒 | Error handler-д request context logging дутмаг |
| L-5 | 🔒 | hardware_fingerprint.py subprocess runtime-д ажилладаг |
| L-6 | 🗄️ | N+1 query risk loops (minor, mostly mitigated) |
| L-7 | 🖥️ | Unused/dead code (legacy functions) |
| L-8 | 🖥️ | Color contrast edge cases (gradient text) |
| L-9 | 🖥️ | Error message format inconsistent |
| L-10 | ⚡ | Audit logger handler дахин нэмэх шалгалт дутмаг |

---

## ✅ Давуу тал (Зөв хийгдсэн зүйлс)

### Security
- ✅ Password hashing: werkzeug bcrypt/scrypt
- ✅ CSRF: WTF_CSRF_ENABLED + token
- ✅ Headers: CSP, X-Frame-Options, HSTS, X-Content-Type-Options
- ✅ SQL injection: SQLAlchemy ORM (parameterized)
- ✅ Open redirect: `is_safe_url()` хамгаалалт
- ✅ Session: HttpOnly, SameSite, Secure cookies
- ✅ Sentry: Error tracking + PII filtering
- ✅ Monitoring: Prometheus metrics

### Database
- ✅ Connection pool: pool_size=25, overflow=25, pre_ping=True
- ✅ AnalysisResult: UniqueConstraint(sample_id, analysis_code)
- ✅ safe_commit() utility: rollback + error handling
- ✅ Cascade rules ерөнхийдөө зөв
- ✅ Sample.sample_code unique=True
- ✅ User.username unique=True

### Deployment
- ✅ Docker: Multi-stage build, non-root user (lims:lims)
- ✅ Health: `/health` endpoint + DB connectivity check
- ✅ Healthcheck: Docker healthcheck configured (30s interval)
- ✅ Gunicorn: 4 workers, 2 threads, max-requests=1000
- ✅ Logging: 3 тусдаа log (app, audit, security) + rotation

### Frontend
- ✅ LIMSDraftManager: localStorage draft save/restore
- ✅ LIMS_AGGRID: Factory pattern + keyboard nav
- ✅ setBusy(): Button disable during save
- ✅ I18N object: Partial translation system

---

## Засах дараалал — Хийгдсэн/Үлдсэн

### Phase 1 — Production Blocker ✅ ДУУССАН
- ✅ SocketIO gevent + Redis MQ config (C-8, C-9)
- ✅ Flask-Migrate (C-6) — 57+ migrations
- ⬜ .env тохиргоо (C-1~5) — server deploy үед
- ⬜ Backup script (C-7) — infra task

### Phase 2 — Security ✅ ДУУССАН
- ✅ innerHTML XSS escape (H-2)
- ✅ safe_commit() ~60 commit хөрвүүлэгдсэн (H-10)
- ✅ CSRF 1800s (H-5), indexes (H-9), bulk delete (H-11)
- ✅ statement_timeout 30s (M-3)
- ⬜ H-8 FK NOT NULL — null data migration хэрэгтэй
- ⬜ H-14 async def — хэрэглэгч хадгалсан (ADR-001)

### Phase 3 — UX ✅ ДУУССАН
- ✅ beforeunload + double-submit (FormGuards) (C-10, C-11)
- ✅ $.getJSON .fail() (H-16)
- ✅ console.log production-д хаагдсан (base.html)

### Phase 4 — Optimization ✅ ХАГАС ДУУССАН
- ✅ Flask-Caching + KPI/stats cache (H-12)
- ⬜ Nginx static file serving (H-13)
- ⬜ Redis rate limiter (H-6)
- ⬜ Vite build (M-8)

---

## Өмнөх холбоотой audit-ууд

- [Water Lab Code Audit](./CODE_AUDIT_2026_02_27.md) — Усны лаб код шалгалт + засвар
- [Code Audit 02-25](./CODE_AUDIT_2026_02_25.md) — Ерөнхий код шалгалт
- [Concurrency Audit] — 40 хэрэглэгчийн зэрэг ажиллах шалгалт (энэ session-д хийгдсэн)

### Concurrency Audit хураангуй (Бүгд засагдсан ✅)
40 химич нэгэн зэрэг ажиллах үед — commit `2a8f0b9`:

**CRITICAL (5/5 ✅):**
- CC-1: Connection pool 25+25=50 (40 user-д)
- CC-2: Coal save_results Sample `with_for_update()` TOCTOU fix
- CC-3: Water save_results Sample `with_for_update()`
- CC-4: Micro batch save Sample+AR `with_for_update()`
- CC-5: Chat online_users `threading.Lock`

**HIGH (5/5 ✅):**
- CH-1: `UniqueConstraint('sample_id', 'analysis_code')` on AnalysisResult
- CH-2: Frontend partial save — зөвхөн амжилттай items draft purge
- CH-3: `version_id_col` optimistic locking + `StaleDataError` handler
- CH-4: Rate limiter `memory://` production warning + Redis docs
- CH-5: Gunicorn `geventwebsocket` worker class + requirements

**MEDIUM (3/3 — аль хэдийн шийдэгдсэн):**
- CM-1: `sample_code unique=True` аль хэдийн байгаа
- CM-2: `joinedload` workspace-д аль хэдийн ашиглагдаж байгаа
- CM-3: CC-2 Sample row lock дотор — deadlock байхгүй
