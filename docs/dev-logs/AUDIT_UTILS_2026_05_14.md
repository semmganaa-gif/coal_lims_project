# AUDIT — Utils + Forms + Schemas + Constants + Tasks давхарга (2026-05-14)

> **Хамрах хүрээ:** `app/utils/` (30 файл, 6 353 мөр) + `app/constants/`
> (8 файл, 1 110 мөр) + `app/forms/` (6 файл, 442 мөр) + `app/schemas/`
> (4 файл, 570 мөр) + `app/tasks/` (6 файл, 408 мөр) + `app/instrument_parsers/`
> (6 файл, 497 мөр) = **60 файл, 9 380 мөр**.
> **Фокус:** Security helpers, audit utility, decorator, license/fingerprint,
> conversion engine, schema validation, constants organization.
> **Шалгасан:** Opus 4.7. Security-critical файлууд (security, audit, database,
> datetime, license_protection, hardware_fingerprint, notifications, user_schema)
> бүрэн уншсан; үлдсэнийг pattern/sample-аар.

---

## 1. Хураангуй

`app/utils/` нь codebase-ийн "shared toolbox" — олон давхараг ашигладаг helpers:
- ✅ `security.py` — `escape_like_pattern`, `is_safe_url` (зөв шийдэгдсэн).
- ✅ `audit.py:log_audit` — ISO 17025 audit log helper, hash чанартай.
- ✅ `database.py:safe_commit/safe_add/safe_delete` — transaction helpers.
- ✅ `notifications.py` — Jinja2 `autoescape=True` (XSS protection).
- ✅ `server_calculations/` — Coal LIMS-ийн "хөдөлгүүр" (5 submodule, well-organized).

Гэвч:

- 🔥 **`user_schema.py:24` `ALLOWED_LABS = ["coal", "petrography", "water"]`** —
  Registered lab keys-той тохиргоогүй! Validation bug.
- 🔥 **`hardware_fingerprint.py`** Windows-only — Linux production-д weak ID,
  `wmic` Windows 11-д deprecated.
- License protection-д ephemeral key fallback (signing key restart-аар алдагдах).
- `audit.py`-аар commit failure silently swallowed.
- `database.py:safe_add` IntegrityError log хийдэггүй.

| Severity | Тоо |
|----------|-----|
| 🟥 High | 2 |
| 🔴 Medium | 10 |
| 🟡 Low | 6 |
| ⚪ Nit | 5 |
| ℹ️ Info / acceptable | 6 |

---

## 2. 🟥 High severity

### H1 · `user_schema.py:24` — `ALLOWED_LABS` нь **registered lab keys-той тохирохгүй**

**Файл:** `app/schemas/user_schema.py:24`

```python
ALLOWED_LABS = ["coal", "petrography", "water"]
```

**Registered lab keys** (bootstrap/blueprints.py:13–19, models/core.py docstring):
- `'coal'`
- `'petrography'`
- `'water_chemistry'`   ← Schema-д **байхгүй**
- `'microbiology'`      ← Schema-д **байхгүй**

`'water'` нь **registered lab огт биш** — Labs audit M2-той ижил алдаа.

**Validation bug:**

1. `User.allowed_labs = ['water_chemistry']` гэж тохируулахад
   `UserSchema().validate(data)` нь:
   ```
   {'allowed_labs': {0: ['Must be one of: coal, petrography, water.']}}
   ```
   → Validation **fails**, хэрэглэгчийг устгайхад водан лаб эрх хадгалагдахгүй.

2. `User.allowed_labs = ['water']` гэж buruu utgaar тохируулсан хэрэглэгч —
   schema OK гэвч `has_lab_access('water_chemistry')` шалгалт fails.

3. `User.allowed_labs` field-ийг JSON column-аар хадгалдаг (core.py:42) — DB
   level constraint байхгүй тул schema-аас өнгөрөөгүй buruu utga DB-д орох
   боломжтой.

**Засвар:**
```python
ALLOWED_LABS = ["coal", "petrography", "water_chemistry", "microbiology"]
```

> **Том дүр зураг:** Models audit M5 (User.role CheckConstraint), Labs audit M2
> (`@lab_required('water')`), Schema H1 — **enum drift-ийн дөрөв дэх жишээ**.
> Status/role/lab enum-уудыг `app/constants/`-руу нэгтгэж бүх давхараг
> ажиглах нь shared source of truth-ийг хангана.

---

### H2 · `hardware_fingerprint.py` — **Windows-only fingerprint** + `wmic` deprecated

**Файл:** `app/utils/hardware_fingerprint.py:25–58`

```python
def get_cpu_id():
    try:
        if platform.system() == 'Windows':
            result = subprocess.run(
                ['wmic', 'cpu', 'get', 'processorid'],   # ← Windows-only command
                ...
            )
            ...
    except ...:
        ...
    return platform.processor() or "unknown"           # ← Linux/Mac fallback

def get_disk_serial():
    ...if platform.system() == 'Windows': wmic ...
    return "unknown"                                    # ← Linux/Mac

def get_motherboard_serial():
    ...if platform.system() == 'Windows': wmic ...
    return "unknown"
```

**Хоёр чухал асуудал:**

1. **Linux/Mac хост дээр fingerprint weak** — production gunicorn deploy:
   - cpu_id = `platform.processor()` (Intel(R) Core(TM) i5..., ердийн утга)
   - disk_serial = "unknown"
   - motherboard_serial = "unknown"
   - Үлдэгдэл components: hostname + MAC + OS + machine
   - Hardware ID нь хост машин нь ижил MAC-тай үед хуулагдах боломжтой.

2. **`wmic` deprecated Windows 11+**:
   - Microsoft нь Windows 11 22H2-аас `wmic.exe`-ийг устгаж байна.
   - Windows Server 2022 PowerShell-руу шилжсэн.
   - Лиценз шалгах process fails on Win11 → all hardware_id components return
     "unknown" → fingerprint = MAC + hostname + system info → лиценз break.

**Засвар (cross-platform):**
- `psutil` ашиглах: `psutil.disk_partitions()` + disk-аар lsblk/diskutil
- Linux: `/sys/class/dmi/id/board_serial` (root шаардлагатай) эсвэл
  `dmidecode`
- Windows: PowerShell `Get-CimInstance -ClassName Win32_Processor`
- Cross-platform library: `py-machineid` packagе

> **Бизнесийн эрсдэл:** Linux server-т deploy хийсэн client нь fingerprint
> алдаатай тул лицензийг ондорхой машинд copy хийх боломжтой — лицензийн
> хамгаалалт effectively bypass хийгдсэн.

---

## 3. 🔴 Medium severity

### M1 · `database.py:safe_commit / safe_add` — IntegrityError **log хийдэггүй**

**Файл:** `app/utils/database.py:56–60, 134–138`

```python
except IntegrityError:
    db.session.rollback()
    if notify:
        _flash_msg(error_msg, "danger")
    return False                              # ← Log алга
except SQLAlchemyError as e:
    ...
    logger.error(f"{error_msg}: {e}")          # ← Энэ нь log хийнэ
```

`IntegrityError` нь хатуу constraint violation (FK, UNIQUE, CHECK). Дебагт
**яг ямар constraint** нурсныг мэдэх зайлшгүй хэрэгтэй. Гэвч одоо silent —
хэрэглэгчид `error_msg` flash харагдана, developer лог хайхад мэдээгүй.

**Засвар:**
```python
except IntegrityError as e:
    db.session.rollback()
    logger.warning(f"IntegrityError ({error_msg}): {e}")
    if notify:
        _flash_msg(error_msg, "danger")
    return False
```

---

### M2 · `license_protection.py:49` — **Ephemeral key fallback** (restart-аар лиценз бүгд invalidate)

**Файл:** `app/utils/license_protection.py:39–51`

```python
def _load_or_generate_key(env_var: str, filename: str, length: int = 48) -> str:
    val = os.getenv(env_var)
    if val:
        return val
    key_path = os.path.join(_INSTANCE_DIR, filename)
    if os.path.exists(key_path):
        ...
    # Файл байхгүй үед import дээр бичихгүй — runtime-д түр түлхүүр ашиглана
    key = secrets.token_urlsafe(length)
    logger.warning(f"{env_var} not found; using ephemeral key (not persisted).")
    return key
```

**Үр дагавар:**
- `LICENSE_SECRET_KEY` env-д тохируулаагүй + `instance/license_secret_key` файл байхгүй үед:
  - Process нь random key үүсгэж модулийн level-д цээжлэх.
  - Restart-аар шинэ key, өмнө validate хийсэн licenses бүгд алдаатай гэж тооцоологдоно.
- Production-д хэн нэг dev-урт `instance/license_secret_key` файлыг устгавал → бүх лицензийг invalidate.

Warning лог хэдийгээр бий — гэвч deployer мэдэхгүй "Energy Resources LIMS-ийн лицензүүд яагаад
бүгд гэнэт expired болсон бэ" гэж асуух магадлалтай.

**Засвар:**
```python
key = secrets.token_urlsafe(length)
# Файлд хадгалах — restart-аар тогтвортой
try:
    os.makedirs(_INSTANCE_DIR, exist_ok=True)
    with open(key_path, 'w', encoding='utf-8') as f:
        f.write(key)
    logger.info(f"{env_var} not found; auto-generated and persisted to {key_path}")
except OSError as e:
    logger.critical(f"Cannot persist {env_var}: {e}")
return key
```

Эсвэл `RuntimeError` raise хийж explicit setup алхам шаардах.

---

### M3 · `license_protection.py:391` — `check_license_middleware` нь bootstrap middleware-тэй **давтан**

**Файлууд:**
- `app/utils/license_protection.py:391–437` — `check_license_middleware()` function
- `app/bootstrap/middleware.py:24–69` — `@app.before_request def check_license()` (inline)

Хоёр өөр implementation. Bootstrap-ийн one is actually wired up. `utils/license_protection.py`-ийнх
dead. (Bootstrap audit-аар хараагүй — энэ нь Routes M4 dead decorator-той ижил
pattern.)

**Засвар:** `utils/license_protection.py:391–437`-ийг устгах (dead code). Bootstrap-ийнхийг
эх үүсвэр болгох.

---

### M4 · `audit.py:106–113` — **Audit commit failure silently logged, not raised**

```python
if commit:
    try:
        db.session.commit()
    except SQLAlchemyError as e:
        db.session.rollback()
        import logging
        logger = logging.getLogger('security')
        logger.error(f"Failed to write audit log: {e}")
    # commit=False: дуудагч тал commit хийнэ (transaction consistency)
```

**Same issue as Services audit L5:** Caller мэдээгүй audit log алдсан. ISO 17025:
audit trail must be complete; silent failure is non-compliant.

**Засвар:** Raise хийх (caller-аар catch хийж шийдэх):
```python
except SQLAlchemyError as e:
    db.session.rollback()
    logger.critical(f"Failed to write audit log: {e}")
    raise   # ← Бизнес flow тасрах нь better-than-silent-fail
```

Эсвэл — fallback file/Sentry-руу шууд бичих.

---

### M5 · `license_protection.py:215` — `except Exception` broad catch

```python
try:
    db.session.commit()
except Exception:  # rollback fallback — keep broad
    db.session.rollback()
```

Code сэтгэгдэлд "keep broad" гэж тэмдэглэсэн. Гэвч `Exception`-аар барих нь
NameError/AttributeError зэрэг developer bugs-ыг hide хийдэг. `(SQLAlchemyError,
OSError)` нарийн барих нь зөв уг.

---

### M6 · `datetime.py:18–19` — Fallback `datetime.now()` (naive, server-time)

```python
def now_local(tz_name: str = _DEFAULT_TZ) -> datetime:
    try:
        return datetime.now(ZoneInfo(tz_name))
    except (KeyError, ValueError):
        return datetime.now()                  # ← Naive system time
```

ZoneInfo нь tzdata package шаардлагатай. Container/server-д tzdata байхгүй бол:
- `datetime.now()` нь naive local time (server TZ-аар).
- Server TZ = UTC → DB дотор UTC хадгалагдана.
- Server TZ = Asia/Ulaanbaatar → OK.
- Хэрэв container `TZ=America/New_York` бол → 13 цагаар backward drift.

**Засвар:**
```python
except (KeyError, ValueError) as e:
    logger.critical(f"ZoneInfo({tz_name!r}) failed: {e}. Install tzdata.")
    # UTC+8 fallback (Mongolian time is UTC+8 year-round)
    from datetime import timezone, timedelta
    return datetime.now(timezone(timedelta(hours=8)))
```

config/base.py-д ижил pattern зөв implement хийсэн (_tz function) — энэ дугаарт consistent
байх ёстой.

---

### M7 · `hardware_fingerprint.py:132–144` — `verify_hardware_id` `tolerance` parameter **unused**

```python
def verify_hardware_id(stored_id, tolerance=1):
    """
    Hardware ID шалгах
    tolerance - хэдэн component өөрчлөгдөж болох (VM-д шилжих үед)
    """
    current_id = generate_hardware_id()

    if stored_id == current_id:
        return True

    # Хэрвээ яг таарахгүй бол, зөвхөн хатуу шалгалт хийх
    # VM эсвэл hardware солигдсон үед
    return False
```

Docstring "tolerance — хэдэн component өөрчлөгдөж болох" — гэвч код яг adain
match-аар тогтоодог. `tolerance` параметр **огт ашиглагдаагүй**. Caller нь
үнэхээр tolerance дамжуулахад → silently ignored.

**Засвар:** Эсвэл implement хийх (component-аар хэсэглэн compare), эсвэл
parameter-ыг устгах + docstring шинэчлэх.

---

### M8 · `constants/__init__.py:22–28` — **Wildcard re-exports**

```python
from .nomenclature import *      # noqa: F401,F403
from .parameters import *        # noqa: F401,F403
from .samples import *           # noqa: F401,F403
from .analysis_types import *    # noqa: F401,F403
from .error_reasons import *     # noqa: F401,F403
from .qc_specs import *          # noqa: F401,F403
from .app_config import *        # noqa: F401,F403
```

**Үр дагавар:**

1. **Name collisions** — хоёр submodule ижил нэртэй constant зарласан үед сүүлдээ
   import-сэн нь override хийнэ.
2. **`__all__` тодорхой биш** — `from app.constants import X` гэж бичих үед X
   аль submodule-аас ирсэн нь IDE/linter-д ялгахгүй.
3. **Refactor risky** — constant-ыг submodule-ээс устгахад caller-уудыг hand-аар хайх.

**Засвар:** Тус submodule-аас explicit re-export, эсвэл `__all__`-аар жагсаах.

---

### M9 · `is_safe_url` — Port mismatch шалгахгүй

```python
return (
    test_url.scheme in ("http", "https")
) and test_url.hostname == host_url.hostname
```

`hostname == hostname` нь port дугаар хайхгүй. Same hostname + different port:
- App run `http://localhost:5000`
- Redirect `http://localhost:8080/evil` → `hostname='localhost'` → **зөв гэж тооцоолно**.

Multi-tenant эсвэл local dev environment-д marginal risk.

**Засвар:**
```python
return (
    test_url.scheme in ("http", "https")
    and test_url.hostname == host_url.hostname
    and (test_url.port or _default_port(test_url.scheme))
        == (host_url.port or _default_port(host_url.scheme))
)
```

---

### M10 · `constants/__init__.py:13–19` — `sys.stdout.reconfigure` **import-time side effect**

```python
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except (AttributeError, OSError) as e:
        import logging
        logging.warning(f"UTF-8 encoding тохируулга амжилтгүй: {e}")
```

Module import-аар system stdout-ийг encoding солих:
- **Side effect at import** — мэдээлэхгүй yan гэж онцлог.
- Production-д stdout = pipe (gunicorn worker → master) — `reconfigure` нь
  pipe-д нөлөөгүй байж магадгүй.
- Test-аар capture хийсэн stdout-ийг хэн нэг библиотек reconfigure хийх нь
  unexpected behaviour.

**Засвар:** Module init-аас гарах, эсвэл explicit setup function-аар хийх.
`run.py`-аас нэг удаа дуудах.

---

## 4. 🟡 Low severity

### L1 · `notifications.py:19–26` — Jinja2 `autoescape=True` Environment (security awareness)

```python
_email_env = Environment(autoescape=True)

def _render_email(template_str: str, **kwargs) -> str:
    tmpl = _email_env.from_string(template_str)
    return tmpl.render(**kwargs)
```

**Сайн pattern.** `flask.render_template_string` нь default `autoescape=False`,
энэ нь email-д XSS оруулах эрсдэлтэй. Тусгай env-аар autoescape=True
тогтоосон нь зөв.

(Информаци: I-class-аар тэмдэглэх ёстой, гэвч feature-ийг highlight хийе.)

---

### L2 · `hardware_fingerprint.py:29–37` — Subprocess timeout 10 секунд

```python
result = subprocess.run(
    ['wmic', 'cpu', 'get', 'processorid'],
    capture_output=True,
    text=True,
    timeout=10                                  # ← 10s wait
)
```

Хэрэв `wmic` (Windows) нь slow эсвэл hang болж байвал — request-уудад 10
секундын delay. Хувийн pop-ийг license validation flow дотор:
- request → check_license_middleware → validate_license → generate_hardware_id →
  4× subprocess.run × 10s timeout = **40 секунд**

Эхний request slow magut.

**Засвар:** Hardware ID-ийг cache хийх (сэргэлтэд нэг удаа тооцоолох), timeout
2 секундэд хязгаарлах.

---

### L3 · `audit.py:60` — `user_agent[:200]` truncation

```python
user_agent = request.headers.get('User-Agent', '')[:200]
```

Truncation OK (DB column max 200), гэхдээ User-Agent string-ийг "AuditLog.user_agent"
column нь `db.String(200)` (models/audit.py:39). Coupling — Schema-аар
тогтоохгүй truncate.

`if len(ua) > 200: ua = ua[:197] + '...'` гэвэл truncation илрэл байх.

---

### L4 · `license_protection.py:36–37` — `_INSTANCE_DIR` os.path.join `..` traversal

```python
_INSTANCE_DIR = os.path.join(os.path.abspath(os.path.dirname(__file__)), '..', '..', 'instance')
```

File нь `app/utils/license_protection.py`. `..` × 2 → `app/../../instance` → `instance/`.
Зөв уг гэвч fragile to file moves.

Bootstrap audit-аас баталгаажсан `config/base.py:17` `INSTANCE_DIR`-ыг import
хийх нь зөв.

---

### L5 · `database.py:_flash_msg` нь request context outside-д silent

```python
def _flash_msg(msg: str, category: str) -> None:
    try:
        from flask import flash
        flash(msg, category)
    except RuntimeError:
        pass
```

CLI/background task-аас дуудсан үед `flash()` RuntimeError-аар таагдаагүй
silently. Acceptable, гэхдээ logger-д тэмдэглэх нь хэрэгтэй.

---

### L6 · `tasks/sla_tasks.py` — `for lab_type in ("coal", "water_chemistry", "microbiology")`

```python
for lab_type in ("coal", "water_chemistry", "microbiology"):
    summary = get_sla_summary(lab_type)
```

Hard-coded lab list. Petrography үлдэгдсэн. Хэрэв petrography-д SLA шаардахгүй
бол OK гэвч `app.labs.INSTALLED_LABS` registry-аас динамикаар авах нь зөв.

---

## 5. ⚪ Nit / стилийн зөрчил

### N1 · `audit.py:46` — `from app import db` метод дотор

```python
def log_audit(...):
    from app import db
    from app.models import AuditLog
    ...
```

Top-level import circular import causes байж магадгүй. Deferred import зөв уг,
гэхдээ модулийн level-д document хийх.

---

### N2 · `hardware_fingerprint.py:18` — `uuid.getnode()` нь virtual MAC ашиглах

```python
def get_mac_address():
    try:
        mac = uuid.getnode()
        ...
```

`uuid.getnode()` нь MAC байхгүй үед random number үүсгэдэг. Документац уг:
"Note: If no networking interface address can be found, then this function returns
a random 48-bit number with the eighth bit set to 1." → Hardware ID-д random
утга орох магадлал.

---

### N3 · `notifications.py:32–61` — HTML template module-level string

Email template нь Python string-ээр multi-line бичсэн. `app/templates/emails/` дотор
file-ээр хадгалах нь:
- Designer-ийн засвар хялбар.
- IDE syntax highlighting.
- Version control diff цэвэр.

---

### N4 · `user_schema.py:101–108` — `strip_username` pre_load

```python
@pre_load
def strip_username(self, data, **kwargs):
    if isinstance(data, dict) and "username" in data:
        val = data["username"]
        if isinstance(val, str):
            data["username"] = val.strip()
    return data
```

`marshmallow.fields.Str(strip=True)` гэх pattern-аар тогтох боломжтой — гэвч
Marshmallow нь built-in `strip` арг байхгүй. Кода зүгээр.

---

### N5 · `instrument_parsers/`, `tasks/` — Бүрэн уншаагүй, гэвч `wc -l` нь reasonable хэмжээ

Audit-аас зориуд орхив (~900 мөр). Pattern-аар бөгөөд эдгээр модулиуд нь
зориулалтаар тогтсон функцууд (Celery tasks, file parsers) — Service/Routes
давхаргын төстэй pattern-аар шалгах боломжтой.

---

## 6. ℹ️ Info / acceptable / сайн pattern

- **I1 · `escape_like_pattern`** — Backslash-first escape order зөв (SQL injection
  hard pattern, comment-аар тайлбарласан).
- **I2 · `is_safe_url`** — Open Redirect protection (хэдийгээр port issue M9).
- **I3 · `audit.py:data_hash`** — ISO 17025 audit hash integrity.
- **I4 · `Environment(autoescape=True)` (notifications)** — XSS protection on
  email templates.
- **I5 · `safe_commit/safe_add/safe_delete`** — Convention helper, тогтвортой
  error handling pattern.
- **I6 · `server_calculations/` split** — `_helpers`, `proximate`, `ultimate`,
  `calorific`, `physical`, `mg_calcs`, `dispatcher` — Coal LIMS математикийн
  цөм цэвэр зохион байгуулагдсан.

---

## 7. Дараагийн алхам

| № | Үйлдэл | Severity | Тэрчлэн |
|---|--------|----------|--------|
| 1 | **H1** — `ALLOWED_LABS` засах ("water_chemistry", "microbiology" нэмэх) | 🟥 High | 1 commit |
| 2 | **H2** — Hardware fingerprint cross-platform (psutil/py-machineid) + `wmic` deprecate plan | 🟥 High | 1 commit + migration |
| 3 | M1 — `safe_commit/safe_add` IntegrityError log нэмэх | 🔴 Medium | 1 commit |
| 4 | M2 — License ephemeral key persist | 🔴 Medium | 1 commit |
| 5 | M3 — `check_license_middleware` dead code устгах | 🔴 Medium | 1 commit |
| 6 | M4 — `audit.py` commit failure raise (эсвэл fallback file) | 🔴 Medium | 1 commit |
| 7 | M5 — License `except Exception` нарийн болгох | 🔴 Medium | 1 commit |
| 8 | M6 — `datetime.py` fallback Asia/Ulaanbaatar tz constant | 🔴 Medium | 1 commit |
| 9 | M7 — `verify_hardware_id` tolerance implement эсвэл устгах | 🔴 Medium | 1 commit |
| 10 | M8 — `constants/__init__.py` wildcard → explicit | 🔴 Medium | 1 commit |
| 11 | M9 — `is_safe_url` port check | 🔴 Medium | 1 commit |
| 12 | M10 — `constants/__init__.py` stdout reconfigure устгах | 🔴 Medium | 1 commit |
| 13 | L1–L6 — Code quality fixes | 🟡 Low | 2 commit |
| 14 | N1–N5 — Style/nit | ⚪ Nit | 1 commit |

---

## 8. Энэ audit-ын хамрах хүрээний дүгнэлт

✅ **Бүрэн уншсан:**
- `app/utils/security.py` (96 мөр)
- `app/utils/audit.py` (194)
- `app/utils/database.py` (147)
- `app/utils/datetime.py` (26)
- `app/utils/license_protection.py` (437)
- `app/utils/hardware_fingerprint.py` (144)
- `app/utils/notifications.py` (sample: 100/494)
- `app/schemas/user_schema.py` (159)
- `app/schemas/__init__.py` (17)
- `app/forms/__init__.py` (13)
- `app/constants/__init__.py` (28)
- `app/tasks/sla_tasks.py` (sample)
- `app/utils/conversions.py` (sample)
- `app/utils/server_calculations/__init__.py` + `dispatcher.py` (sample)

📊 **Бараг уншсан:** ~2 000 мөр (security-critical файлууд бүрэн, бусдыг
sample/grep).

⚠️ **Хамгийн чухал олдвор:**
- **H1 (ALLOWED_LABS)** — Schema bug нь нэгэн жижиг const-аар л үүсэх — гэвч
  User registration flow-д лаб тохиргоо буруу хадгалагдах боломжтой.
- **H2 (hardware_fingerprint)** — License protection-ийн bedrock үнэхээр weak.
  Сар хүртэл fixed хийх ёстой prod risk.

🔍 **Сүүлчийн audit-ын тоймхой бичих** — overall summary + cross-cutting findings.
