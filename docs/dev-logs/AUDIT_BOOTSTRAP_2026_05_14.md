# AUDIT — Bootstrap + Config давхарга (2026-05-14)

> **Хамрах хүрээ:** `app/bootstrap/` (13 файл), `config/` (8 файл),
> `app/config/` (6 файл), `run.py` — нийт **28 файл, 1 994 мөр**.
> **Фокус:** Архитектур (давхарга зөрчил) + код чанар.
> **Шалгасан:** Opus 4.7 (auto-memory engineering principles — perfect over fast).

---

## 1. Хураангуй

Bootstrap давхарга нь сайн **бүрэлдэхүүн хэсгүүдэд** хуваагдсан (extensions / auth /
blueprints / errors / i18n / jinja / logging / middleware / security_headers /
websocket / cli_commands / celery_app). `bootstrap_app(app)` нь dependency
order-ийг тодорхой комментоор бичиж дагасан байгаа нь сайн.

`config/` нь домэйнээр хуваагдсан (base / database / security / mail /
integrations / runtime / i18n) — multiple inheritance-аар нэгтгэсэн `Config`
class цэвэр шийдэл.

Гэвч хэд хэдэн **давхарга/чанарын асуудал**, нэг **давхар бүртгэл** олдсон.

| Severity | Тоо |
|----------|-----|
| 🟥 High | 1 |
| 🔴 Medium | 4 |
| 🟡 Low | 8 |
| ⚪ Nit | 8 |
| ℹ️ Info / acceptable | 5 |

---

## 2. 🟥 High severity

### H1 · `audit.log` буруу зам руу бичигдэж байна — production audit logging тасарсан

**Файл:** `app/logging_config.py:22, 51`
`config/runtime.py:10–11` (related)

```python
# app/logging_config.py
def setup_logging(app):
    os.makedirs('logs', exist_ok=True)              # ← project cwd-д `logs/`!
    ...
    app_handler = RotatingFileHandler(
        app.config.get('APP_LOG_FILE', 'logs/app.log'),    # ← config-аас (INSTANCE_DIR/logs/app.log)
        ...
    )
    ...
    audit_handler = RotatingFileHandler(
        'logs/audit.log',                            # ← HARD-CODED! config-аас уншихгүй
        ...
    )
    ...
    security_handler = RotatingFileHandler(
        app.config.get('SECURITY_LOG_FILE', 'logs/security.log'),  # ← config-аас
        ...
    )
```

**Үр дагавар:**

| Лог | Очдог зам | Учир |
|-----|-----------|------|
| `app.log` | `instance/logs/app.log` | config-аас уншсан ✓ |
| `security.log` | `instance/logs/security.log` | config-аас уншсан ✓ |
| `audit.log` | `<cwd>/logs/audit.log` | **hard-coded** ✗ |

Hard-coded `'logs/audit.log'` нь Python процессийн **cwd**-аас relative. Гэвч:

1. `config/runtime.py:15` нь `INSTANCE_DIR/logs/`-г бүтээдэг — өөр санд.
2. `app/logging_config.py:22` `os.makedirs('logs', ...)` нь cwd-д өөр `logs/`-г үүсгэдэг.
3. Gunicorn/waitress/systemd үед cwd нь project root биш байх магадлалтай — лог огт хадгалагдахгүй эсвэл worker-ийн өөр өөр санд тарж магадгүй.
4. CLAUDE.md дотор тэмдэглэсэн "`logs/audit.log` бараг хоосон" нь яг энэ алдааны үр дүн.

**ISO/IEC 17025 audit trail-ийн дүрэм** — audit log нь алдагдалгүй, тогтсон газарт хадгалагдах ёстой. Энэ нь **compliance эрсдэл**.

**Засвар:**
```python
# config/runtime.py
class RuntimeConfig:
    SECURITY_LOG_FILE = os.path.join(INSTANCE_DIR, 'logs', 'security.log')
    APP_LOG_FILE = os.path.join(INSTANCE_DIR, 'logs', 'app.log')
    AUDIT_LOG_FILE = os.path.join(INSTANCE_DIR, 'logs', 'audit.log')  # ← НЭМЭХ
```

```python
# app/logging_config.py
def setup_logging(app):
    # cwd-д `logs/`-г үүсгэхээ болих — INSTANCE_DIR/logs/ нь config/runtime.py-д үүссэн
    ...
    audit_handler = RotatingFileHandler(
        app.config.get('AUDIT_LOG_FILE', os.path.join(INSTANCE_DIR, 'logs', 'audit.log')),
        ...
    )
```

> Сошиал нэгэн санаа: одоогийн hard-coded `logs/audit.log`-ийн утга ALWAYS-fail байх ёстой биш — Werkzeug dev server-ыг `python run.py`-р асаах үед cwd нь project root тул `./logs/audit.log` бичигдэх боломжтой. Гэхдээ энэ нь `instance/logs/`-ийн дүрэмтэй санамсаргүй давхцал — үндсэн зорилго биш.

---

## 3. 🔴 Medium severity

### M1 · `run.py` + bootstrap дотор CLI команд **давхар бүртгэгдэж байна**

**Файл:** `run.py:6,9` ба `app/bootstrap/cli_commands.py:9`
`app/bootstrap/__init__.py:59`

```python
# run.py
from app.cli import register_commands
app = create_app()            # bootstrap_app(app) → init_cli(app) → register_commands(app)
register_commands(app)        # ← ДАВТАН дуудаж байна
```

`create_app()` → `bootstrap_app(app)` → `init_cli(app)` дотроос
`app_cli.register_commands(app)`-г аль хэдийн дуудсан. Дараа нь `run.py:9` мөн л
дуудаж байна.

Click `@app.cli.group()` болон `@<group>.command()` декораторууд ижил нэртэй
команд хоёр дахь удаа бүртгэхэд хадгалагдсан handler-аа overwrite хийнэ (Click
≥8). Үр дүнд нь:

- `python run.py` (Werkzeug dev server) — бүртгэл хоёр удаа явна.
- `flask run` / `flask shell` — мөн адил (top-level `register_commands(app)`
  Python import-д ажилладаг).
- `gunicorn "app:create_app()"` — `run.py`-г import хийдэггүй тул асуудалгүй.

**Засвар:** `run.py:6,9`-аас CLI бүртгэлийг устгана. Bootstrap path
(`init_cli`) нь `create_app()` бүрд автоматаар явдаг тул хангалттай.

```python
# run.py
import os
from app import create_app, db, socketio
from app.models import User, Sample

app = create_app()
```

---

### M2 · `celery_app.py` — модулийн түвшинд `make_celery()` дуудаж байна (import-time side effect)

**Файл:** `app/bootstrap/celery_app.py:106`

```python
# Module-level Celery instance (lazy — worker эхлэхэд Flask app үүснэ)
celery_app = make_celery()
```

`make_celery(app=None)` дотор `app is None` тохиолдолд `create_app()` дууддаг.
Энэ нь `from app.bootstrap.celery_app import ...` гэсэн **аль ч импорт** Flask
аппликейшнийг **бүхэлд нь bootstrap хийхэд хүргэнэ** — extensions, DB,
blueprints, jinja, security headers бүгд.

**Эрсдэл:**

- Test/CLI үед санамсаргүй импорт хийгдвэл бүтэн app үүснэ.
- `make_celery()` import-ийн дунд `create_app()` дууддаг — circular import-ын
  магадлал (`create_app()` нь `bootstrap_app()`-г дууддаг, тэр нь celery-г
  импортлоосон код руу хүрвэл lock үүсэх).
- Comment-д "lazy" гэж бичсэн боловч **lazy биш** — import дээр шууд явдаг.

**Засвар санал 1 (proper lazy):**
```python
celery_app = None  # populated by worker entry point

def get_celery():
    global celery_app
    if celery_app is None:
        celery_app = make_celery()
    return celery_app
```

**Засвар санал 2 (entrypoint pattern, Flask docs-ын зөвлөмж):**
```python
# celery_worker.py
from app import create_app
from app.bootstrap.celery_app import make_celery

flask_app = create_app()
celery_app = make_celery(flask_app)
```
Модуль импорт-д огт side effect үлдээхгүй.

---

### M3 · `config/security.py` — `_IS_PROD` нь **testing орчинд secure cookies-ийг асаана**

**Файл:** `config/security.py:7–22`

```python
_ENV = os.getenv("FLASK_ENV", "production")
_IS_PROD = _ENV != "development"

class SecurityConfig:
    SESSION_COOKIE_SECURE = _IS_PROD   # ← testing үед True
    REMEMBER_COOKIE_SECURE = _IS_PROD  # ← testing үед True
    WTF_CSRF_SSL_STRICT = _IS_PROD     # ← testing үед True
```

Логик: `FLASK_ENV != "development"` бол prod. **Гэвч "testing" нь `development`
биш** — тиймээс `SESSION_COOKIE_SECURE=True`. Werkzeug-ийн test client нь
secure flag-ийг шаардахгүй ажиллаж магадгүй ч, энэ нь:

1. `TestConfig` тестийн орчныг production cookie тохиргоотой ажиллуулна.
2. `FLASK_ENV=staging` зэрэг өөр env-ийн утга oc-аар production гэж хүлээн авна.
3. `WTF_CSRF_SSL_STRICT=True` нь HTTPS дээр Referer-ийг хатуу шалгана —
   testing-д энэ хатуу шалгалт идэвхтэй.

**Засвар:** Тестийн `TESTING=True` config-ийг тусгайлж шалгах:
```python
_IS_PROD = _ENV == "production"  # strict whitelist
# эсвэл TestConfig дотор тус тус override
```
эсвэл `TestConfig`-д `SESSION_COOKIE_SECURE = False` нэмж нэмэх.

---

### M4 · `app/monitoring.py:213–236` — `/health` route нь `app/routes/`-ийн **гадна** бүртгэгдэж байна

**Файл:** `app/monitoring.py:213–236`

```python
def setup_monitoring(app):
    ...
    @app.route('/health')
    def health_check():
        ...
        db.session.execute(db.text('SELECT 1'))   # ← Route доторх шууд DB call
```

**3 зөрчил:**

1. **Архитектур:** `monitoring` нь observability давхарга (logging/metrics).
   Route бүртгэх нь `app/routes/`-ийн ажил. `health_check` endpoint-ийг
   `app/routes/main/` эсвэл `app/routes/api/`-д шилжүүлэх.

2. **Route → Service → Repository давхарга зөрчил:** Health check шууд
   `db.session.execute()` дууддаг. Энгийн `SELECT 1` тул маш бага зөрчил, гэхдээ
   convention-той тулгана.

3. **Endpoint name `health_check`** нь `app/bootstrap/middleware.py:14`-ийн
   `LICENSE_EXEMPT_ENDPOINTS`-д жагсаасан. Blueprint-гүй route тул endpoint name
   нь зүгээр л function name (`health_check`). Хэрэв irgendwannи blueprint руу
   шилжүүлбэл endpoint name өөрчлөгдөж, license check дотор нь зогсоох болно.
   Coupling-ийг кодлог комментоор тэмдэглэхгүй хийсэн.

**Засвар:** `health_check` route-ийг `app/routes/main/routes.py` (эсвэл шинэ
`app/routes/api/health.py`) руу шилжүүлэх; `monitoring.py` зөвхөн `metrics`,
`before/after_request` hook-уудтай үлдээх; middleware-ийн exempt list-ийг
шинэчлэх.

---

## 4. 🟡 Low severity

### L1 · `app/bootstrap/auth.py:14` — `db.session.get` шууд дуудаж байна

```python
return db.session.get(models.User, int(id))
```

Flask-Login-ийн user_loader тул Repository давхарга үсэрч bootstrap-аас шууд DB
дуудах нь техникийн хувьд **зөвшөөрөгдсөн** (decorator бүртгэх цэг). Гэвч
project convention-ы дагуу `UserRepository.get(id)` ашиглавал давхарга бүрэн
цэвэр болно.

---

### L2 · `app/bootstrap/errors.py:18` — `db.session.rollback()` 500 handler дотор

```python
@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    ...
```

Бизнес логик биш — last-resort rollback. **Acceptable**. Гэвч хэрэв
service-үүд `@transactional` wrapper-аар session-аа удирдаж байгаа бол энэ
rollback шаардлагагүй (давхар явах). Sprint 4–5-д шалгах.

---

### L3 · `app/bootstrap/celery_app.py:32–43` — `FlaskTask` дотор `_app` lexical scope

```python
class FlaskTask(Task):
    def __call__(self, *args, **kwargs):
        with _app.app_context():    # ← _app хараахан тодорхойлогдоогүй
            return self.run(*args, **kwargs)

if app is None:
    from app import create_app
    app = create_app()
_app = app
```

Class-г `_app`-аас өмнө тодорхойлж байгаа боловч `__call__` нь дуудагдах үед
`_app` бэлэн болсон тул ажилладаг. Гэвч уншихад нэлээд төөрөгдөл үүсгэдэг.
Class-ийг `make_celery` дотор шилжүүлэх эсвэл `_app`-ийг class attribute-аар
inject хийх нь тодорхой болно.

---

### L4 · `app/bootstrap/middleware.py:55` — `'admin'` string literal

```python
if current_user.role == 'admin':
```

Хатуу string. `UserRole.ADMIN` constant/enum ашиглах нь зөв. `app.constants`
эсвэл `app.security.constants` дотор тодорхойлох.

---

### L6 · `app/monitoring.py:25–30` — Prometheus client-ийн **private API** ашиглаж байна

```python
def _get_existing(name):
    try:
        return REGISTRY._names_to_collectors.get(name + '_total', REGISTRY._names_to_collectors.get(name))
    except AttributeError:
        return None
```

`REGISTRY._names_to_collectors` нь **private attribute** (`_`-аар эхэлсэн).
prometheus_client minor version-д өөрчлөгдөж устаж магадгүй. Public API
ашиглах: `REGISTRY.collect()` дотроос нэрээр нь хайх.

---

### L7 · `app/monitoring.py:185–189` — Бүх request-ийг INFO log-д бичих → лог spam

```python
# Info level log (бүх request)
app.logger.info(
    f"{g.request_method} {g.request_path} "
    f"{response.status_code} {elapsed:.4f}s"
)
```

`app.log` файл бүх request-д (static file, /metrics, /health г.м.) бичигдэнэ.
Production-д 10 MB rotate-той ч маш хурдан дүүрнэ. Зөвлөмж:

- INFO log-ийг устгах эсвэл `app.logger.debug(...)`-руу шилжүүлэх.
- Slow request (>1s) `warning`, very slow (>5s) `error` — аль хэдийн зөв.
- Эсвэл `logging.Filter` ашиглан `/static/*`, `/metrics`, `/health` excluder
  бичих.

---

### L8 · `app/sentry_integration.py:50` — Default environment `'development'` — config-той зөрчилтэй

```python
environment = os.environ.get('SENTRY_ENVIRONMENT') or app.config.get('ENV', 'development')
```

`config/base.py:47`-д `ENV = os.getenv("FLASK_ENV", "production")` — энэ нь
**production** default. Гэвч Sentry эндээс уншихдаа `'development'` default
хэрэглэж байна. Эхний default нь null хувьсагч өгвөл (`ENV=''` нөхцөлд)
production орчинд буруу шошготой алдаа Sentry руу илгээгдэнэ.

**Засвар:**
```python
environment = os.environ.get('SENTRY_ENVIRONMENT') or app.config.get('ENV') or 'production'
```

---

### L5 · `app/bootstrap/middleware.py:30–32` — Hard-coded test license dict

```python
if app.config.get('TESTING'):
    g.license_valid = True
    g.license_info = {'company': 'Test', 'expires_at': '2099-12-31'}
    return None
```

Magic value `'2099-12-31'`. `TEST_LICENSE_INFO` constant эсвэл fixture-аар
гаргавал тест handler-уудтай нэг газраас удирдагдана.

---

## 4. ⚪ Nit / стилийн зөрчил

### N1 · `app/bootstrap/extensions.py:34–35` — PEP 8 хоосон мөр дутуу

```python
csrf = CSRFProtect()
def _rate_limit_key():       # ← module-level def-ийн өмнө 2 хоосон мөр шаардлагатай
```

---

### N2 · `app/bootstrap/jinja.py:30–33` — Lambda template filter

```python
app.add_template_filter(
    lambda v, analysis_code=None: format_result_centralized(v, analysis_code),
    name="fmt_result"
)
```

`format_result_centralized` нэр аль хэдийн байгаа — шууд `add_template_filter(
format_result_centralized, name="fmt_result")` боломжтой (хоёр аргументтай).

---

### N3 · `config/security.py:31–34` — `UPLOAD_FOLDER` нь `BASE_DIR`-ийг дахин тооцоолж байна

```python
UPLOAD_FOLDER = os.path.join(
    os.path.abspath(os.path.join(os.path.dirname(__file__), '..')),
    'app', 'static', 'uploads', 'certificates'
)
```

`config/base.py:11`-д `BASE_DIR` тодорхойлсон. DRY:
```python
from config.base import BASE_DIR
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'app', 'static', 'uploads', 'certificates')
```

---

### N4 · `run.py:5,12` — Shell context зөвхөн 2 model expose хийдэг

```python
return {'db': db, 'User': User, 'Sample': Sample}
```

46 model байгаагаас ердөө 2-ыг харуулсан. Дадал — ихэвчлэн хамгийн их хэрэглэдэг
бүгдийг (Equipment, AnalysisResult гэх мэт) нэмэх. `tests/conftest.py`-д аль
хэдийн илүү жагсаалт байгаа — тэндээс шилжүүлэх.

---

### N5 · `app/bootstrap/middleware.py:48,52` — `result.get('valid')` vs `result['valid']` зөрчил

```python
g.license_valid = result.get('valid', False)
...
if not result['valid']:        # ← g.license_valid-ийг ашиглах нь тогтвортой
```

`if not g.license_valid:` гэвэл defensive `.get(..., False)`-той зохицно.

---

### N7 · `app/monitoring.py:300–348` — None-safety байхгүй

```python
ANALYSIS_COUNTER = _get_or_create_counter(...)  # → Counter | None
...
def track_analysis(analysis_type: str, status: str = 'completed'):
    if PROMETHEUS_AVAILABLE:
        ANALYSIS_COUNTER.labels(...)  # ← ANALYSIS_COUNTER нь None байж магадгүй
```

`_get_existing()` нь `None` буцаах боломжтой (registry-д байхгүй үед). Гэвч
helper-ийн callsite-ууд `if PROMETHEUS_AVAILABLE`-ыг л шалгадаг, `ANALYSIS_COUNTER`
байгаа эсэхийг шалгадаггүй. Edge case-д `AttributeError: 'NoneType' object has
no attribute 'labels'`.

**Засвар:** `if PROMETHEUS_AVAILABLE and ANALYSIS_COUNTER:` эсвэл
`_get_or_create_counter`-ийг ValueError үед raise хийдэг болгох.

---

### N8 · `app/monitoring.py:71, 110, 136–144` — `APP_INFO` module-level None overwrite

```python
APP_INFO = None  # line 71
if PROMETHEUS_AVAILABLE:
    ...
    APP_INFO = _get_or_create_info('lims_app', 'LIMS application information')  # line 110

def setup_monitoring(app):
    if APP_INFO:
        try:
            APP_INFO.info({...})        # line 138
        except ValueError:
            pass
    metrics.info('lims_app_info', ...)  # line 148 — өөр нэртэй давхар info
```

`lims_app` болон `lims_app_info` хоёр өөр Prometheus info бий. `setup_monitoring`
дотор хоёр дахь `metrics.info('lims_app_info', ...)` нь яах вэ — `APP_INFO` нь
аль хэдийн `lims_app` нэртэй info бүртгэсэн. Давхар бичлэг, comment-д
"davhardakhыг zailskheekh" гэж бичсэн ч давхар бий.

---

### N6 · `app/bootstrap/__init__.py:24` — `'X-XSS-Protection'` хасах тухай комментоо алга

`security_headers.py:26–27` дотор X-XSS-Protection-ийг хассан тухай комментоо
бичсэн нь сайн. Bootstrap orchestrator-ийн "12. Security headers" комментод
ямар header-үүд орсныг нэрлэвэл уншихад тус болно.

---

## 5. ℹ️ Acceptable / тэмдэглэх

- **I1 · Import-time side effects:** `config/base.py:14` `load_dotenv()`,
  `config/runtime.py:15` `os.makedirs()`, `config/base.py:18`
  `os.makedirs(INSTANCE_DIR)` — config-import-ийн нэг удаагийн side effect,
  Flask app factory pattern-д **acceptable**.
- **I2 · `from app import models  # noqa: F401`** (`__init__.py:50`) —
  SQLAlchemy mapper-уудыг бүртгэх стандарт pattern. **OK.**
- **I3 · CSP string concatenation** (`security_headers.py:41–64`) — урт string
  боловч nonce-той хувьсагч цөөн. Тестлэхэд struct-аас илүү уншихад тохиромжтой.
  **OK.**
- **I4 · Lab `_safe_register`** (`blueprints.py:40–42`) — test environment-д
  давтан bootstrap хийгдэх үед `BlueprintAlreadyRegistered` гарахаас сэргийлсэн.
  **Сайн pattern.**
- **I5 · `app/config/__init__.py` хоосон** — `app/config/*.py`-ыг өөр газраас
  шууд импортлодог тул хоосон __init__ нь зөв. **OK.**

---

## 6. Шалгасан нэмэлт файлууд (Хувилбар 2)

**1-р хувилбарт "deferred" гэсэн файлуудыг бүрэн уншилаа:**

| Файл | Мөр | Дүгнэлт |
|------|-----|---------|
| `app/logging_config.py` | 97 | **H1** — audit.log hard-coded path |
| `app/monitoring.py` | 372 | **M4, L6, L7, N7, N8** |
| `app/sentry_integration.py` | 247 | **L8** + үндсэндээ цэвэр |
| `app/routes/quality/__init__.py` | 37 | `register_routes_all()` — параметргүй ✓ зөв |
| `app/config/analysis_schema.py` | 330 | Static schema dict + `get_analysis_schema()` — цэвэр |
| `app/config/qc_config.py` | 197 | QC tolerance + timer presets dict — цэвэр |
| `app/config/sop_standards.py` | 131 | SOP/MNS mapping dict — цэвэр |
| `app/config/display_precision.py` | 315 | Precision + format helpers — цэвэр, import-time validate сайн pattern |
| `app/config/repeatability.py` | 55 | LIMIT_RULES static dict — цэвэр |

> **Тайлбар:** `app/config/` дотрох 5 файл нь зөвхөн static dict + simple
> helper-уудтай. Архитектурын зөрчил байхгүй, layer-аар тооцоологдохгүй —
> "constants" давхарга.

---

## 7. Дараагийн алхам

| № | Үйлдэл | Файл | Severity | Тэрчлэн |
|---|--------|------|----------|--------|
| 1 | **H1** — `audit.log` path-ийг config-аас уншуулах | `logging_config.py`, `runtime.py` | 🟥 High | 1 commit |
| 2 | M1 — CLI давхар бүртгэлийг устгах | `run.py:6,9` | 🔴 Medium | 1 commit |
| 3 | M2 — Celery import-time side effect-ийг lazy болгох | `celery_app.py:106`, `celery_worker.py` | 🔴 Medium | 1 commit |
| 4 | M3 — `TestConfig`-д secure cookie override нэмэх | `tests/conftest.py` | 🔴 Medium | 1 commit |
| 5 | M4 — `/health` route-ийг `app/routes/`-руу шилжүүлэх | `monitoring.py` → `routes/main/` | 🔴 Medium | 1 commit |
| 6 | L1–L8 — Convention align (UserRepository, role enum, private API, log spam, sentry default) | олон файл | 🟡 Low | 1–2 commit |
| 7 | N1–N8 — Style/DRY/clarity nit-үүд | олон файл | ⚪ Nit | 1 commit |

**Зөвлөмж:** H1 → M1–M4 → L1–L8 → N1–N8 дарааллаар буюу risk-аас эхлэх.

---

## 8. Энэ audit-ын хамрах хүрээний дүгнэлт

✅ **Бүрэн шалгасан** — bootstrap + config давхарга (28 файл) + logging
   call-target 3 файл + quality blueprint registration (1 файл).

📊 **Нийт уншсан:** 32 файл, ~2,728 мөр.

> **Дараагийн алхам** — хэрэглэгчтэй тохирсон ёсоор: Models →
> Repositories → Services → Routes давхарга бүрээр audit үргэлжилнэ.
