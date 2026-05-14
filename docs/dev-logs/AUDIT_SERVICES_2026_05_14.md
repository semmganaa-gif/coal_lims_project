# AUDIT — Services давхарга (2026-05-14)

> **Хамрах хүрээ:** `app/services/` — 20 файл, **10 217 мөр**.
> **Фокус:** Архитектур (transaction boundary, layer зөрчил, давхарга алгасах) +
> бизнес логик зөв байдал + код чанар.
> **Шалгасан:** Opus 4.7. Хэмжээний улмаас 8 файлыг бүрэн уншсан
> (analysis_audit, mg_service, instrument_service, mass_service, sla_service,
> datatable_service, qc_chart_service, dashboard_service, sample_service),
> бусдыг pattern-аар (grep + sample read) шалгасан.

---

## 1. Хураангуй

Services давхарга нь route-аас бизнес логик гаргах зорилтыг **хагас биелүүлсэн**.
`ServiceResult`/`*Result` dataclass pattern сайн, `log_analysis_action`-ийн
"caller commits" convention зөв. Гэвч:

- **CLAUDE.md-д заасан `@transactional` decorator кодын аль ч хэсэгт байхгүй** —
  convention хэзээ ч implement хийгдээгүй.
- Services + Repositories **хоёулаа** `db.session.commit()` хийдэг — transaction
  boundary тодорхойгүй.
- 80+ direct `Model.query` / `db.session.query` call — Repository давхарга
  ихэвчлэн алгасагдсан.
- **Workflow engine role нэрс User.role-той тохирохгүй** — chemist user-ийн
  workflow зөрчил.
- 2 service нь route-аас импорт хийсэн — урвуу давхарга зөрчил.
- `datetime.now()` болон `now_local()` хольсон — timezone drift.

| Severity | Тоо |
|----------|-----|
| 🟥 High | 2 |
| 🔴 Medium | 11 |
| 🟡 Low | 7 |
| ⚪ Nit | 6 |
| ℹ️ Info / acceptable | 4 |

---

## 2. 🟥 High severity

### H1 · `workflow_engine.py` — **role нэрс User.role-той тохирохгүй**

**Файл:** `app/services/workflow_engine.py`

`workflow_engine.py` дотор `roles` талбарт **5 өөр утга** ашигласан:

```bash
$ grep -oE '"(analyst|senior_analyst|chemist|prep|senior|manager|admin)"' workflow_engine.py | sort -u
"admin"
"analyst"        # ← User.role-д БАЙХГҮЙ
"manager"
"senior"
"senior_analyst" # ← User.role-д БАЙХГҮЙ
```

`User.role` (core.py:27)-д жагсаасан утга:
- `prep`, `chemist`, `senior`, `manager`, `admin`

**Tomahjээний зөрчил:**

| Transition | Шаардлагатай role | User.role-тэй таарах хэрэглэгч |
|------------|-------------------|-------------------------------|
| pending_review → rejected | `senior`, `senior_analyst`, `admin`, `manager` | senior, admin, manager |
| rejected → pending_review (Resubmit) | `analyst`, `senior`, `senior_analyst`, `admin`, `manager` | senior, admin, manager — **chemist, prep BLOCK** |
| reanalysis → pending_review (Submit) | `analyst`, `senior`, `senior_analyst`, `admin`, `manager` | senior, admin, manager — **chemist, prep BLOCK** |
| new → in_progress (Start sample) | `analyst`, `senior_analyst`, `admin`, `manager` | admin, manager — **chemist, prep, senior BLOCK** |
| in_progress → analysis | `analyst`, `senior_analyst`, `admin`, `manager` | admin, manager — **бусад BLOCK** |
| analysis → completed | `senior_analyst`, `admin`, `manager` | admin, manager — **senior ч block!** |

`analysis_workflow.py:381–401` дотор `engine.can_transition()` дуудаж байна:

```python
try:
    engine = WorkflowEngine("analysis_result")
    user_role = _cu.role if hasattr(_cu, 'role') else "admin"
    check = engine.can_transition(res.status, new_status, user_role, ctx)
    if not check.allowed:
        return None, check.reason, 403          # ← Шууд 403 буцаана
except Exception:
    pass  # ← Зөвхөн Python алдаа барих
```

`except Exception: pass` нь зөвхөн `ImportError`, `AttributeError` зэрэг
**Python exception**-ийг барина. `return None, ..., 403` нь exception биш — шууд
буцаана. Тиймээс **chemist Resubmit оролдох үед 403 алдаа гарна**.

**Эрсдэлийн бодит түвшин:** Energy practical-аар одоо ажиллах magic нь хоёрын
аль нэг гэж сэжиглэж байна:
- (а) `WorkflowEngine`-г route бүрд unique-аар дуудаагүй (зөвхөн `update_result_status`,
      `mass_service.update_sample_status`-д). Бусад workflow transitions нь
      engine алгасаж байна.
- (b) Production-д зөвхөн senior/admin/manager workflow-той зүйл хийдэг тул
      bug илрээгүй.

Гэхдээ комплексын **тогтворгүй байдал** болон тэлэлтийн эрсдэл өндөр.

**Засвар:**
1. `workflow_engine.py` доторх "analyst" → "chemist", "senior_analyst" → "senior".
2. Эсвэл `User.role` constants-ыг `app/constants.py` дотор Enum болгож,
   workflow_engine үүнийг import хийдэг болгох.
3. CheckConstraint-аар `User.role` хязгаарлах (Models audit M5 хамт).

---

### H2 · Sample disposal нь `disposal_date`-аар хянагдсан — Repos audit H2 **БАТАЛГААЖСАН**

**Файл:** `app/services/sample_service.py:835–865` (`get_retention_context`)

```python
expired_samples = Sample.query.filter(
    Sample.lab_type == lab_type,
    Sample.retention_date < today,
    Sample.disposal_date.is_(None),               # ← disposal_date IS NULL
).order_by(Sample.retention_date.asc()).limit(200).all()

disposed_samples = Sample.query.filter(
    Sample.lab_type == lab_type,
    Sample.disposal_date >= today - timedelta(days=90),  # ← disposal_date filter
).order_by(Sample.disposal_date.desc()).limit(100).all()
```

`sample_service.py` нь дээж устгасан эсэхийг **`Sample.disposal_date IS NOT NULL`**-ээр шалгадаг
(`status="disposed"` биш). Sample model-ийн `disposal_date` талбар (core.py:252)
энэ зорилгод оруулсан.

**Үр дүн:** Repositories audit-ын H2-д тэмдэглэсэн `sample_repository.py` дотор
`Sample.status != "disposed"` filter-ууд бүгд **dead code** — disposed status хэзээ
ч тохиолддоггүй.

**Засвар (Repos audit H2-той хамт):**
- `sample_repository.get_expired_retention`, `get_disposed`, `get_no_retention`,
  `get_return_samples`, `get_upcoming_expiry` — бүх `status != "disposed"`-ийг
  `disposal_date.is_(None)`-руу засах.

---

## 3. 🔴 Medium severity

### M1 · `@transactional` decorator **нэг ч кодын газарт байхгүй**

```bash
$ grep -rn "@transactional\|def transactional" app/
(no output)
```

CLAUDE.md-д заасан convention:
> "`db.session.commit()` зөвхөн `@transactional` wrapper-аар."

Гэвч decorator хэзээ ч implement хийгдээгүй. Үр дүнд:

- **Repositories** `commit=True` default-той `save`/`delete` хийдэг (Repos audit M1)
- **Services** Хувийн `db.session.commit()` дуудалт **olon olon** хийдэг:

```bash
$ grep -c "db.session.commit\(\)" app/services/*.py | sort -t: -k2 -rn | head
admin_service.py:42
import_service.py:13
mass_service.py:11
analysis_workflow.py:11
spare_parts_service.py:9
equipment_service.py:7
chemical_service.py:7
report_service.py:6
sla_service.py:5
instrument_service.py:4
```

**Үр дагавар:**
- Бизнес flow дунд нь commit хийгдэх боломжтой → хэсэгчилсэн транзакц
  (atomicity алдсан).
- Service нэг функц дотор олон жижиг commit → row-level locking, slow.
- Test-аас mock хийхэд хүндрэлтэй.

**Засвар:** `app/utils/transaction.py` дотор `@transactional` decorator үүсгэж
бүх service entry function-уудад ашиглах (нэг decorator → нэг commit/rollback).

---

### M2 · 80+ газар `Model.query` / `db.session.query` — **Repository алгасасан**

```bash
$ grep -c "\.query\." app/services/*.py | sort -t: -k2 -rn | head
spare_parts_service.py:11
report_service.py:10
sla_service.py:9
chemical_service.py:7
analytics_service.py:7
workflow_engine.py:5
sample_service.py:5
analysis_workflow.py:5
admin_service.py:5
report_builder.py:4
instrument_service.py:4
mg_service.py:3
mass_service.py:3
dashboard_service.py:3
datatable_service.py:1
```

Service олонх нь Repository-г дуудалгүй model-руу шууд query хийдэг.

**Жишээ:**

```python
# sla_service.py:45 — SystemSettingRepository байхад шууд .query
settings = SystemSetting.query.filter_by(category=SLA_CONFIG_CATEGORY, ...)

# chemical_service.py:171–173 — ChemicalRepository байхад шууд .query
'total': Chemical.query.filter(Chemical.status != 'disposed').count(),
'low_stock': Chemical.query.filter(Chemical.status == 'low_stock').count(),
```

**Үр дагавар:** Repository дизайн pattern алдагдсан. ORM шилжих эсвэл DB engine
сольж байх үед олон газар өөрчлөх шаардлагатай.

**Засвар:** Services-ийг рефактор хийж Repos-руу call route хийх. Repos audit
M5-д заасан 18+ model-д шинэ Repository нэмэх.

---

### M3 · 2 service нь **routes-аас import** — урвуу давхарга зөрчил

**Файлууд:**
```python
# app/services/datatable_service.py:155
from app.routes.api.helpers import _aggregate_sample_status

# app/services/sample_service.py:687
from app.routes.main.helpers import get_12h_shift_code
```

Architecture rule: **Routes → Service → Repository → Model**.

Service нь route-аас function/helper-ийг импортлох нь reverse layer
dependency. Энэ нь:

1. Тест хийхэд route module ачаалах шаардлагатай.
2. Helper-ийг шилжүүлэх эсвэл устгахад service эвдэрнэ.
3. Routes-аас side effect (Blueprint бүртгэх г.м.) санамсаргүй import-аас явдаг.

**Засвар:** `_aggregate_sample_status`, `get_12h_shift_code` функцуудыг
`app/utils/`-руу шилжүүлэх. Route нь утилийн дамжуулагч болох.

---

### M4 · 5 service `from app.bootstrap.extensions` import — inconsistent

**Файлууд:**
```python
# analytics_service.py, instrument_service.py, qc_chart_service.py,
# report_builder.py, workflow_engine.py
from app.bootstrap.extensions import db
```

Бусад 15 service нь `from app import db` (re-export pattern) ашиглана.
Конвенцийн зөрчил — нэг л style сонгох.

`from app import db` нь app-ийн public API-аар уншиж байгаа учраас тогтвортой.
`bootstrap.extensions` нь implementation detail.

---

### M5 · `instrument_service.py`, `qc_chart_service.py`, `report_builder.py` — `datetime.now()` ашигладаг (`now_local()` биш)

```bash
$ grep -c "datetime\.now(" app/services/*.py
instrument_service.py:2
qc_chart_service.py:2
report_builder.py:1
```

**Жишээнүүд:**
```python
# instrument_service.py:102
reading.reviewed_at = datetime.now(timezone.utc)   # UTC!

# qc_chart_service.py:232, 252
year = datetime.now().year
ca = CorrectiveAction(..., issue_date=datetime.now().date(), ...)
```

Бусад codebase `now_local()` (`Asia/Ulaanbaatar` tz) ашигладаг. Эдгээр service-д
**UTC** эсвэл **system local** timestamps бичигдэх — DB-ийн `Mongolian local time`
багана дотор холимог. Хэрэглэгчид буруу цаг харагдах эрсдэлтэй.

**Засвар:** `from app.utils.datetime import now_local`-ээр солих. `instrument_service`
дотор `timezone.utc` ашигласан нь зориуд (server timestamps?), гэхдээ DB
column-аар naive datetime ашигладаг тул conversion drift гарах магадлал бий.

---

### M6 · `admin_service.py:230, 312` — Password error message "8+" гэж бичсэн, бодит хязгаар 10

```python
# admin_service.py:230
return False, 'Нууц үг шаардлагыг хангахгүй байна (8+ тэмдэгт, том/жижиг үсэг, тоо).', None
```

`User.validate_password` (core.py:115):
```python
if len(password) < 10:
    errors.append("хамгийн багадаа 10 тэмдэгт байх ёстой")
```

Хэрэглэгч 9 тэмдэгт нууц үг бичсэн үед `set_password()` нь `ValueError`-ийг
("хамгийн багадаа 10 тэмдэгт...") raise хийнэ. admin_service нь try/except-р
барьж "8+ тэмдэгт" гэсэн **буруу** мессеж буцаана. Хэрэглэгч 9 тэмдэгт нууц үг
бичээд "8+ шаардлагатай" гэсэн мессеж аваад **9 нь хангалттай гэж итгэх**
тогтворгүй UX.

(Models audit M3-аас уламжилсан.)

**Засвар:** "8+" → "10+ тэмдэгт"-руу засах.

---

### M7 · `admin_service.py:216, 295, 297, 358` — Hard-coded `'admin'` string

```python
if role == 'admin':
if user_to_edit.role != 'admin':
if user_to_delete.role == 'admin':
```

Bootstrap audit + Models audit-аас давтан. `UserRole.ADMIN` constants/Enum
санал болгосон.

---

### M8 · `except Exception` broad catches — 9 occurrences

```bash
analysis_workflow.py: 4
mass_service.py: 2
chemical_service.py: 2
workflow_engine.py: 1
```

Бүгд `pass` эсвэл `logger.exception(...)`-той. Гэвч `Exception`-ийг хамгийн
үндсэн catch хийх нь:
- Code типийн bug (NameError, AttributeError) -ийг silently барих.
- Test үед бодит алдаа дарагдах.

**Зөв pattern** — нарийн exception type ашиглах:
```python
except (SQLAlchemyError, ValueError) as exc:
    logger.exception(...)
```

`analysis_workflow.py:399` дотор `except Exception: pass` нь workflow engine
fallback зорилготой. Гэхдээ `except (ImportError, KeyError)`-аар бичсэн нь
зөв уг.

---

### M9 · God-functions — 100+ мөртэй

| Function | Файл | Мөрийн тоо |
|----------|------|-----------|
| `save_single_result` | analysis_workflow.py:918 | **308** |
| `build_calibration_description` | equipment_service.py:34 | **222** |
| `bulk_update_result_status` | analysis_workflow.py:474 | 152 |
| `build_dashboard_stats` | analysis_workflow.py:192 | 148 |
| `invalidate_results_by_lot` | chemical_service.py:793 | 132 |
| `update_result_status` | analysis_workflow.py:361 | 113 |
| `get_archive_tree` | dashboard_service.py:161 | 108 |
| `update_result_status_api` | analysis_workflow.py:709 | 107 |
| `generate_insights` | analytics_service.py:428 | 106 |
| `_process_control_gbw` | analysis_workflow.py:816 | 102 |

**308 мөртэй `save_single_result`** — Single Responsibility принципийн ноцтой
зөрчил. Сорилт хэцүү, refactor-д risk их.

**Засвар:** Жижиг функцэд хуваах. Эхлээд `save_single_result` (analysis_workflow)
+ `build_calibration_description` (equipment_service).

---

### M10 · `mass_service.py:127` — `Sample.status.in_(["new", "New"])` — case duplication

```python
base_filters = [
    Sample.status.in_(["new", "New"]),    # ← "New" нь CheckConstraint-д байхгүй
    _has_m_task_sql(),
]
```

`Sample.status` CheckConstraint (core.py:267): `'new','in_progress','analysis','completed','archived'` — зөвхөн lowercase.

`"New"` (capital N) нь хэзээ ч тохиолдохгүй — defensive filter эсвэл сүүлд
batch import нь capital case бичсэн legacy data-аас илрэсэн.

**Засвар:** `"New"`-ийг устгах, эсвэл migration script-аар capitalized values-ийг
lowercase-руу нормализаци хийх.

---

### M11 · `sla_service.py` — `Sample.status.notin_(["archived", "completed"])` ашигладаг ч "completed" status хэзээ тохиолдох вэ тодорхойгүй

```python
active = Sample.query.filter(
    Sample.lab_type == lab_type,
    Sample.status.notin_(["archived", "completed"]),
)
```

`mark_completed(sample)` функц нь `sample.completed_at = now_local()` гэж
тэмдэглэдэг, гэвч `sample.status = "completed"` гэж **тохируулдаггүй**.

Workflow engine-ийн `Sample` workflow-д `analysis → completed` transition байгаа
(workflow_engine.py:219). Гэвч энэ transition-ийг **кодын аль ч хэсэгт ашигладаг
эсэхийг тодорхойлох шаардлагатай**.

Хэрэв "completed" status хэзээ ч set хийгддэггүй бол:
- `sla_service.notin_([..., "completed"])` filter dead — "completed" эзэлдэг
  огт байдаггүй.
- Workflow engine-ийн transition тодорхойлогдсон ч хэрэглээ алга.

**Шалгах:** Routes audit-ын үед `sample.status = "completed"` set хийдэг газар хайх.

---

## 4. 🟡 Low severity

### L1 · Гурван өөр commit pattern зэрэгцэн оршдог

```python
# Pattern A — Direct (most common)
db.session.commit()
except SQLAlchemyError:
    db.session.rollback()

# Pattern B — mass_service._safe_commit() helper
def _safe_commit() -> ServiceResult | None:
    try:
        db.session.commit()
    except StaleDataError:
        ...

# Pattern C — sample_service uses external util
from app.utils.database import safe_commit
if not safe_commit("...", "..."):
    ...
```

Гурван pattern зэрэгцэн оршдог нь:
- Inconsistent error handling
- Test-эд mock хийхэд хүндрэлтэй
- Convention тодорхойгүй

**Засвар:** Нэг standard pattern сонгох (M1 — @transactional decorator).

---

### L2 · Cache key strings hard-coded олон газар

```python
# analysis_workflow.py:437–438, workflow_engine.py:465–466
cache.delete('kpi_summary_ahlah')
cache.delete('ahlah_stats')
```

Олон газарт хатуу string. `app/constants/cache_keys.py` дотор:
```python
class CacheKey:
    KPI_SUMMARY_AHLAH = 'kpi_summary_ahlah'
    AHLAH_STATS = 'ahlah_stats'
```

---

### L3 · Mongolian-only error messages — i18n зөрчил

```bash
$ grep -c "буцаагдсан\|алдаа гарлаа\|сонгоогүй" app/services/*.py
analysis_workflow.py: 4
sample_service.py: 3
mass_service.py: 2
mg_service.py: 2
equipment_service.py: 1
```

`flask_babel` ашиглаж `lazy_gettext()`-аар орчуулах. Учир нь:
- User.language-ийн `en` value бий (core.py:45).
- i18n config-д `'en': 'English', 'mn': 'Монгол'` хоёр хэл байна.
- Гэвч service-ийн error message бүгд Mongolian-аар буцдаг → English UI ажиллахгүй.

---

### L4 · `mg_service.py:121` — Hard-coded role tuple

```python
if user_role not in ("senior", "admin"):
    return RepeatResult(success=False, message="Зөвхөн ахлах/админ")
```

`{UserRole.SENIOR, UserRole.ADMIN}` set ашиглах нь зөв (M7-той хамт).

---

### L5 · `analysis_audit.py:165` — Audit failure silently swallowed

```python
except (SQLAlchemyError, TypeError, ValueError) as e:
    # Аудит алдаанаас болж үндсэн transaction нурахгүй байх ёстой.
    # rollback хийхгүй — дуудагч тал шийднэ.
    logger.error("CRITICAL ERROR in log_analysis_action: %s", e)
```

Audit log алдаа бичигдэхгүй боловч caller нь "OK" гэж үздэг. **ISO 17025 эрсдэл** —
audit trail дутуу.

**Засвар:** Audit алдаа нь `app.logger.critical(...)` + Sentry-руу шууд илгээх,
эсвэл fallback (нэг secondary table / file) бичих.

---

### L6 · `mass_service.py:261–276` — Audit log handler `log_analysis_action`-аар биш, шууд `AnalysisResultLog(...)` үүсгэдэг

```python
log_entry = AnalysisResultLog(
    user_id=user_id,
    sample_id=sample_id,
    ...
    action="DELETED",
    ...
)
db.session.add(log_entry)
```

Helper-ийг алгасаж, hash computation болон IP capture (analysis_audit.py:107–118)
хийдэггүй. Audit trail integrity дутуу.

**Засвар:** `log_analysis_action(action="DELETED", ...)` руу шилжүүлэх.

---

### L7 · `instrument_service.bulk_approve/bulk_reject` — ValueError silently барина

```python
def bulk_approve(reading_ids, user_id):
    count = 0
    for rid in reading_ids:
        try:
            approve_reading(rid, user_id)
            count += 1
        except ValueError:
            continue        # ← Аль reading алдаа гарсан log байхгүй
    return count
```

Caller-д ямар reading алдаа гарсан мэдээ байхгүй. `failed_ids: list[int]` буцаах
нь зөв уг (analysis_workflow.bulk_update_result_status pattern шиг).

---

## 5. ⚪ Nit / стилийн зөрчил

### N1 · `__init__.py` — зөвхөн 7 export, гэвч 20 service файл

```python
# app/services/__init__.py
from app.services.analysis_audit import log_analysis_action
from app.services.sample_service import (...)
__all__ = [...]
```

Бусад 18 service file-ийн API нь `app.services.X`-аар л дуудаж болно — гэвч
__all__-д жагсаагүй нь incomplete public API. Хэрэв barrel pattern хэрэглэхгүй
бол нэг service-ийн export-ыг бас хасах нь cleaner.

---

### N2 · Deferred imports method дотор

```python
# sample_service.py:687
def register_lab_sample(...):
    ...
    from app.routes.main.helpers import get_12h_shift_code   # method дотор
```

```python
# mass_service.py:57
def _has_m_task_sql():
    from sqlalchemy import func   # method дотор
    return func.lower(...)
```

PEP 8 — top-level import-ыг top-of-file-д байрлуулах. Лгvi circular import-ыг
зайлсхийх зорилгоор byvol Зарим зөв уг. Циркл exists-эс баталгаажуулах.

---

### N3 · Magic numbers — `with_for_update`, hardcoded limits

```python
# datatable_service.py:70
length = min(length, 1000)                # ← magic 1000

# analysis_workflow.py:148
results_to_review = q.order_by(...).limit(500).all()    # ← magic 500

# analysis_workflow.py:492
if len(result_ids) > 200:
    return None, "Нэг удаад 200-аас их үр дүн шинэчлэх боломжгүй", 400
```

Constants module-руу шилжүүлэх.

---

### N4 · `mass_service.py:107` — `except Exception: pass` workflow engine fallback

```python
try:
    from app.services.workflow_engine import WorkflowEngine
    engine = WorkflowEngine("sample")
    user_role = getattr(current_user, 'role', 'admin')
    first_sample = db.session.get(Sample, sample_ids[0])
    if first_sample:
        check = engine.can_transition(first_sample.status, new_status, user_role)
        if not check.allowed:
            return ServiceResult(False, check.reason, status_code=403)
except Exception:
    pass  # Fallback: allow if workflow unavailable
```

`getattr(current_user, 'role', 'admin')` — нэвтрээгүй хэрэглэгчид 'admin' оноох
**security risk**. (Гэхдээ login_required-аар guard хийгдсэн route байж магадгүй).

Workflow engine import fails-аас (M8) илрэх Python error-ыг silently swallow
хийдэг. Тэгш зөв уг — but logger.warning нэмж тэмдэглэх.

---

### N5 · `datatable_service.py:165` — `getattr(s, "sample_condition", None) or getattr(s, "sample_state", None)`

```python
sample_condition_val = (
    getattr(s, "sample_condition", None) or
    getattr(s, "sample_state", None) or ""
)
```

`sample_state` нь Sample model-д **байхгүй** column (core.py-д `sample_condition`
бий). Defensive code эсвэл legacy refactor-ийн үлдэгдэл. Тодорхойлох эсвэл устгах.

---

### N6 · `sample_service.py:184` — `from app.monitoring import track_sample` deferred import inside batch loop

```python
def register_batch_samples(...):
    ...
    from app.monitoring import track_sample
    ...
    for _ in range(count):
        track_sample(client=client_name, sample_type=sample_type)
```

Top-level import-руу шилжүүлэх. Batch loop дотор function pointer-ийг үргэлжлүүлэн
ашигладаг тул optimization биш.

---

## 6. ℹ️ Info / acceptable / сайн pattern

- **I1 · `ServiceResult` / `RegistrationResult` / `ArchiveResult` dataclass pattern** —
  service-аас route-руу буцаах tuple биш structured object. **Сайн.**
- **I2 · `log_analysis_action` "caller commits" convention** (analysis_audit.py:88) —
  Тодорхой бичсэн, single source of truth-той. **Сайн.**
- **I3 · `with_for_update()` row-locking** — Concurrent edit-аас сэргийлэх. **Сайн.**
- **I4 · Optimistic locking-тэй version_id-аар** (analysis_workflow.py-д `StaleDataError`
  барих) — Models audit-аас уламжилсан analytical level. **Сайн.**
- **I5 · Cross-service import (sample_service → sla_service.assign_sla,
  mass_service → workflow_engine)** — нэг layer дотор зөв.

---

## 7. Дараагийн алхам

| № | Үйлдэл | Severity | Тэрчлэн |
|---|--------|----------|--------|
| 1 | **H1** — workflow_engine.py role нэрс User.role-той тааруулах | 🟥 High | 1 commit |
| 2 | **H2** — sample_repository.py `disposal_date.is_(None)`-руу засах (Repos audit H2-той хамт) | 🟥 High | 1 commit |
| 3 | M1 — `@transactional` decorator implement | 🔴 Medium | Том sprint |
| 4 | M2 — Services рефактор → Repos руу шилжүүлэх | 🔴 Medium | Том sprint (S4-5) |
| 5 | M3 — `_aggregate_sample_status`, `get_12h_shift_code`-ыг `app/utils/`-руу шилжүүлэх | 🔴 Medium | 1 commit |
| 6 | M4 — 5 service-ийн import-ыг `from app import db`-руу нэгтгэх | 🔴 Medium | 1 commit |
| 7 | M5 — `datetime.now()` → `now_local()` (3 файл) | 🔴 Medium | 1 commit |
| 8 | M6 — "8+ тэмдэгт" → "10+ тэмдэгт" (Models M3-той хамт) | 🔴 Medium | 1 commit |
| 9 | M7 — `'admin'` literal → Enum/constant | 🔴 Medium | 1 commit |
| 10 | M8 — `except Exception` → нарийн exception types | 🔴 Medium | 2 commit |
| 11 | M9 — God-function split (хамгийн жижиг 3-аас эхлэх) | 🔴 Medium | 2–3 commit |
| 12 | M10 — `Sample.status.in_(["new", "New"])` → `["new"]` + migration | 🔴 Medium | 1 commit |
| 13 | M11 — "completed" status set хийгддэг эсэхийг тодорхойлох | 🔴 Medium | Шалгаах (Routes audit) |
| 14 | L1–L7 — Style/correctness fixes | 🟡 Low | 2 commit |
| 15 | N1–N6 — Nit | ⚪ Nit | 1 commit |

**Зөвлөмж:** H1 → H2 → M3 → M5/M6/M7/M10 (хамт) → M1/M2/M9 (том sprint).

---

## 8. Энэ audit-ын хамрах хүрээний дүгнэлт

✅ **Бүрэн уншсан:** 9 file (analysis_audit, mg_service, instrument_service,
   mass_service, sla_service, datatable_service, qc_chart_service, dashboard_service,
   sample_service, admin_service partial — ~3 500 мөр).

📊 **Pattern-аар шалгасан:** 11 file (analysis_workflow толбоор, chemical_service,
   equipment_service, analytics_service, import_service, report_service, report_builder,
   spare_parts_service, workflow_engine).

⚠️ **Хамгийн чухал олдвор:** H1 (workflow_engine role mismatch) — production-д
chemist хэрэглэгч rejected analysis-ийг resubmit хийх боломжгүй. Routes audit-аар
энэ үнэхээр илэрсэн эсэхийг шалгах.

🔍 **Дараагийн алхам** — Routes давхарга (~40 файл).
