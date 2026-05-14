# AUDIT — Repositories давхарга (2026-05-14)

> **Хамрах хүрээ:** `app/repositories/` — 15 файл, **1 917 мөр**.
> **Фокус:** Архитектур (давхарга, transaction boundary, API хэв маяг) +
> код чанар + runtime correctness.
> **Шалгасан:** Opus 4.7.

---

## 1. Хураангуй

Repositories давхарга нь модулийг (1 model class → 1 repository class)
сайн хуваасан. Static-method pattern нь stateless namespace-ийн зөв
хэрэглээ. Зарим CRUD API (save / delete / get_by_id / get_by_id_or_404) нь
тогтвортой.

Гэвч:

- **1 runtime crash bug** (`maintenance_repository.py`) — model-д байхгүй
  column нэрийг ашиглаж байна.
- **1 schema/code зөрчил** (`sample_repository.py`) — CheckConstraint-д
  байхгүй status утга ашигладаг.
- **Repository нь transaction commit хийж байна** — CLAUDE.md-д заасан
  "db.session.commit() зөвхөн @transactional wrapper-аар" дүрэм зөрчигдсөн.
- **Legacy `Model.query` API** хаа сайгүй — SQLAlchemy 2.0-д deprecated.
- **15+ model-д repository байхгүй** — энэ нь routes/services нь `Model.query`-г
  шууд дуудах гол шалтгаан.

| Severity | Тоо |
|----------|-----|
| 🟥 High | 2 |
| 🔴 Medium | 8 |
| 🟡 Low | 9 |
| ⚪ Nit | 7 |
| ℹ️ Info / acceptable | 4 |

---

## 2. 🟥 High severity

### H1 · `maintenance_repository.py:25` — **Runtime AttributeError** (column нэрийн зөрчил)

**Файл:** `app/repositories/maintenance_repository.py:21–27`

```python
@staticmethod
def get_by_equipment(equipment_id: int) -> list[MaintenanceLog]:
    return (
        MaintenanceLog.query
        .filter_by(equipment_id=equipment_id)
        .order_by(MaintenanceLog.maintenance_date.desc())   # ← AttributeError
        .all()
    )
```

`MaintenanceLog` model дотор `maintenance_date` талбар **байхгүй**:

```python
# app/models/equipment.py:104
action_date = db.Column(db.DateTime, default=now_mn, index=True)
```

`MaintenanceLog.maintenance_date` нь `AttributeError: type object
'MaintenanceLog' has no attribute 'maintenance_date'` raise хийнэ.

**Шалгасан:**
```bash
$ grep -rn "maintenance_date" app/
app/repositories/maintenance_repository.py:25   # ← цорын ганц reference
```

Бүх codebase-д энэ нэрийн өөр reference байхгүй — column-ыг хэзээ ч үүсгээгүй.
`MaintenanceLogRepository.get_by_equipment(...)` дуудсан route эсвэл service нь
500 алдаа гарна.

**Шалгах:** `equipment_repository.py`-аас `usages` / `logs` lazy='dynamic'
relationship-ыг ашиглаж байгаа газар олж, хэрэв `get_by_equipment` ашиглагдаагүй
бол dead code. Хэрвээ маршрутаар дуудагдаж байгаа бол өнөөдөр 500 алдаа.

**Засвар:**
```python
.order_by(MaintenanceLog.action_date.desc())
```

---

### H2 · `sample_repository.py` — `'disposed'` нь Sample.status CheckConstraint-д **байхгүй**

**Файлууд:** `app/repositories/sample_repository.py:118, 195–252`

```python
@staticmethod
def get_by_status(status: str) -> list[Sample]:
    """
    Args:
        status: "new", "archived", "disposed" гэх мэт      # ← 'disposed' гэж нэрлэсэн
    """
    ...

# Олон газар status != "disposed" filter:
def get_expired_retention(...):
    return Sample.query.filter(
        ...
        Sample.status != "disposed",     # ← бүгд "True" filter — disposed status байх боломжгүй
    ).all()
```

`Sample.status` CheckConstraint (core.py:267):
```python
CheckConstraint(
    "status IN ('new','in_progress','analysis','completed','archived')",
    name="ck_sample_status",
)
```

**'disposed' энэ жагсаалтад байхгүй.** Үр дагавар:

1. `sample.status = 'disposed'` гэж тохируулбал INSERT/UPDATE CHECK constraint
   алдаа гарна.
2. `Sample.status != "disposed"` filter нь **бүх удаа True** — dead filter.
3. `get_disposed()` (line 233–236) нь **бүх үед хоосон жагсаалт буцаана**.

**Хоёр боломжит уг:**

(a) **Logic bug** — sample disposal нь `disposal_date IS NOT NULL` (core.py:252)
    талбараар хэрэгжсэн боловч код status-аар л шалгаж байгаа. Эдгээр filter-уудыг
    `Sample.disposal_date.is_(None)`-руу засах.

(b) **Schema gap** — 'disposed' нь зорилтот status, гэвч CheckConstraint-д
    нэмэх дутуу. Alembic migration:
    ```sql
    ALTER TABLE sample DROP CONSTRAINT ck_sample_status;
    ALTER TABLE sample ADD CONSTRAINT ck_sample_status
      CHECK (status IN ('new','in_progress','analysis','completed','archived','disposed'));
    ```

Аль нь зөв вэ — service давхаргад `Sample.status = 'disposed'` гэж сэт хийгдэх
эсэхээс хамаарна. Дараагийн audit (services)-д тогтоох.

---

## 3. 🔴 Medium severity

### M1 · Repository нь **transaction commit хийж байна** — convention зөрчил

**CLAUDE.md:**
> `db.session.commit()` зөвхөн `@transactional` wrapper-аар.

**Бодит байдал:** 15 repository файл бүгд:

```python
@staticmethod
def save(sample: Sample, commit: bool = True) -> Sample:    # ← default True
    db.session.add(sample)
    if commit:
        db.session.commit()                                  # ← Repository commits!
    return sample

@staticmethod
def delete(sample: Sample, commit: bool = True) -> bool:
    db.session.delete(sample)
    if commit:
        db.session.commit()
    return True

@staticmethod
def update_status(sample_ids: list[int], new_status: str, commit: bool = True) -> int:
    ...
    if commit:
        db.session.commit()
    return count
```

**Repository pattern-ийн зөв загвар:**

- Repository: DB I/O-ийг encapsulate хийх (query, add, delete, flush). **Commit
  хийхгүй.**
- Service: Business logic + transaction boundary (`@transactional`). Олон
  repository call-ыг **нэг transaction** дотор багтаах.
- Route: Service-ийг дуудах. Transaction-ийг огт хариуцахгүй.

Одоогийн дизайнаар service нь олон repository call-ийг хийвэл — нэг
`save(commit=False)` мартсан тохиолдолд **хэсэгчилсэн commit** үүсэх эрсдэлтэй
(нэг repository commit-сэн, нөгөө нь үлдсэн — atomicity алдсан).

**Засвар:**

1. Бүх repository-аас `commit` параметрийг устгах.
2. Бүх commit-ийг service layer-руу шилжүүлэх.
3. `@transactional` decorator-ийг үнэндээ хэрэглээний хэлбэр (зорилтот sprint).
4. Эсвэл — Repository нь зөвхөн `add/delete/flush`-ыг хийдэг (`db.session.flush()`),
   commit нь Flask `teardown_request` эсвэл service layer.

Энэ нь project-ийн **Sprint 4–5 (Services → Repositories)**-ийн гол зорилго —
аль хэдийн төлөвлөсөн ажил.

---

### M2 · Legacy `Model.query` API — SQLAlchemy 2.0-д **deprecated**

**Бараг бүх repository:**
```python
User.query.filter_by(username=username).first()
AnalysisResult.query.filter(AnalysisResult.sample_id.in_(sample_ids)).all()
Sample.query.filter(Sample.status == status).all()
```

Flask-SQLAlchemy 3.x-д `Model.query` API нь "Legacy API" гэж тэмдэглэгдсэн.
SQLAlchemy 2.0 native API:

```python
db.session.execute(
    select(User).where(User.username == username)
).scalar_one_or_none()
```

**Үргэлжлүүлэн ашиглах эрсдэл:**
- Flask-SQLAlchemy 4.x-д устгагдах магадлалтай.
- `Model.query` нь `scoped_session`-аас уламжлагдсан thread-local — async context-д
  зөрчилтэй.
- Type hint-үүд тэлэгдэхгүй (returns Query, not typed result).

**Бараг бүх 1 917 мөр-ийг refactor хийх шаардлагатай — том sprint.**

---

### M3 · `analysis_result_repository.py:165` — Docstring **«pending»** утга буруу

```python
@staticmethod
def get_by_status(status: str) -> list[AnalysisResult]:
    """
    Args:
        status: "pending", "approved", "rejected" гэх мэт   # ← "pending" буруу
    """
```

`AnalysisResult.status` CheckConstraint (analysis.py:92–94):
```python
CheckConstraint(
    "status IN ('pending_review','approved','rejected','reanalysis')",
    ...
)
```

**'pending' гэдэг утга байхгүй** — `pending_review` зөв нэр. Docstring
documentation drift.

---

### M4 · `analysis_result_repository.py:278–292` — `samples_with_approved_results` нэр **буруу**

```python
@staticmethod
def samples_with_approved_results() -> list[int]:
    """Батлагдсан үр дүнтэй дээжний ID-ууд."""    # ← docstring "approved"
    rows = (
        db.session.query(AnalysisResult.sample_id)
        .filter(AnalysisResult.status.in_(["approved", "pending_review"]))  # ← хоёулаа
        .distinct()
        .all()
    )
```

Метод нэр болон docstring "approved" гэж хэлсэн, гэвч **pending_review-ийг
бас оруулдаг**. Caller-ыг төөрөгдүүлнэ.

Зөв нэр: `samples_with_reviewable_results` эсвэл filter-ийг засах.

---

### M5 · Repository **байхгүй 15+ model** — давхарга бүрэн биш

**Repository-той model-ууд (14):** User, Sample, AnalysisResult, AnalysisType,
GbwStandard, ControlStandard, Equipment, Chemical, SystemSetting, Bottle,
BottleConstant, ChatMessage, UserOnlineStatus, AuditLog, Complaint, CAPA,
NonConformity, Improvement, ProficiencyTest, EnvironmentalLog, LabReport,
ReportSignature, MaintenanceLog, UsageLog (24).

**Repository-гүй model-ууд:**

| Model | Шалтгаан |
|-------|---------|
| `AnalysisProfile` | DB-аас query шаардсан, repository алга |
| `AnalysisResultLog` | Audit trail — append-only, гэвч query API алга |
| `SparePart`, `SparePartCategory`, `SparePartUsage`, `SparePartLog` | Нийт 4 |
| `ChemicalUsage`, `ChemicalLog`, `ChemicalWaste`, `ChemicalWasteRecord` | 4 |
| `InstrumentReading` | Багаж интеграц — query шаардлагатай |
| `WaterWorksheet`, `WorksheetRow` | Усны лабын хуудас |
| `SolutionPreparation`, `SolutionRecipe`, `SolutionRecipeIngredient` | Уусмал |
| `MonthlyPlan`, `StaffSettings` | Планинг |
| `QCControlChart` | QC хяналт |
| `SystemLicense`, `LicenseLog` | Лиценз |

Нийт **~18 model нь Repository-гүй.** Routes/services тэдгээрийг `Model.query`
шууд дууддаг. Энэ нь CLAUDE.md-д заасан **196 db.session call-site-ийн ихэнх**
эх үүсвэр.

---

### M6 · `EnvironmentalLogRepository`-д `delete()` **алга**

**Файл:** `app/repositories/quality_repository.py:230–256`

`ComplaintRepository`, `CAPARepository`, `NonConformityRepository`,
`ImprovementRepository`, `ProficiencyTestRepository` бүгд `delete()`-тэй. Гэвч
**EnvironmentalLogRepository нь `delete()` дутуу**.

Бизнес логик хэлбэрээр environmental log устгах боломжгүй (ISO 17025 audit
trail тул логик зөв) — гэвч **CRUD API consistency** алдсан. `delete()`
байхгүй гэдгийг тэмдэглэх docstring эсвэл `NotImplementedError`-той stub.

> Models audit (H2)-аар санал болгож байсан: EnvironmentalLog-д
> HashableMixin + event.listen нэмэх. Тэгвэл delete() бүрэн тогтоох
> ёстой — DB level-ээр append-only.

---

### M7 · `standard_repository.py:43, 97` — `deactivate_all` default `commit=False`

```python
# GbwStandardRepository:
@staticmethod
def deactivate_all(commit: bool = False) -> int:      # ← default False!
    count = GbwStandard.query.update({GbwStandard.is_active: False})
    if commit:
        db.session.commit()
    return count
```

Бусад бүх repository метод default `commit=True`. **Зөвхөн `deactivate_all`-д
default False.** Caller бүртгэхгүй мартвал — `is_active=False` UPDATE pending,
гэвч commit байхгүй → session rollback / next commit-аар орох/орохгүй.

**M1-ийн засвартай хамт**: бүх commit параметрийг устгаж, service-руу шилжүүлэх
үед энэ зөрчил арилна.

---

### M8 · `chat_repository.py:89–95` — `soft_delete` хэн устгасныг бүртгэхгүй

```python
@staticmethod
def soft_delete(message: ChatMessage, commit: bool = True) -> bool:
    from app.utils.datetime import now_local as now_mn
    message.is_deleted = True
    message.deleted_at = now_mn()        # ← only timestamp
    if commit:
        db.session.commit()
    return True
```

`ChatMessage.is_deleted = True` + `deleted_at = now_mn()` гэж тэмдэглэдэг.
Гэвч `deleted_by_id` талбар байхгүй (ChatMessage model дотор) тул хэн
устгасныг хадгалах боломжгүй.

ISO 17025-д мессеж audit trail чухал биш гэж үзвэл OK, гэвч admin багт
"гомдол хайх" зэрэгт хэн устгасныг мэдэх шаардлагатай.

---

## 4. 🟡 Low severity

### L1 · `from flask import abort` — олон газар duplicate import

`UserRepository.get_by_id_or_404`, `SampleRepository.get_by_id_or_404`,
`AnalysisResultRepository.get_by_id_or_404`, `LabReportRepository.get_by_id_or_404`,
`AnalysisTypeRepository.get_by_code_or_404`, `BottleRepository.get_by_id_or_404`,
`ComplaintRepository.get_by_id_or_404`, ... бүгд:

```python
@staticmethod
def get_by_id_or_404(...) -> ...:
    obj = db.session.get(Model, id)
    if obj is None:
        from flask import abort           # ← олон газарт хийсэн
        abort(404)
    return obj
```

Top-of-file import-руу нэгтгэх, эсвэл BaseRepository-д shared helper болгох.

---

### L2 · `equipment_repository.py` — `or_(Equipment.status.is_(None), Equipment.status != 'retired')` **4 газар** давтан

```python
# get_all_active, get_by_category, get_by_categories, get_by_related_analysis
or_(Equipment.status.is_(None), Equipment.status != 'retired')
```

Жижиг helper-аар цэгцлэх:
```python
@staticmethod
def _not_retired_filter():
    return or_(Equipment.status.is_(None), Equipment.status != 'retired')
```

---

### L3 · `chat_repository.py` — `from app.utils.datetime import now_local as now_mn` method **дотор** олон удаа

```python
@staticmethod
def mark_as_read(...):
    from app.utils.datetime import now_local as now_mn       # ← line 68
    ...

@staticmethod
def soft_delete(...):
    from app.utils.datetime import now_local as now_mn       # ← line 90
    ...

@staticmethod
def set_online(...):
    ...
    from app.utils.datetime import now_local as now_mn       # ← line 117
    ...

@staticmethod
def set_offline(...):
    ...
    from app.utils.datetime import now_local as now_mn       # ← line 128
    ...
```

Top-of-file import нэг удаа хангалттай.

---

### L4 · `get_by_id_or_404` нь **хагас репозиторт** бий

Хувьсагч CRUD pattern:

| Repository | get_by_id | get_by_id_or_404 |
|------------|-----------|---------------------|
| User | ✓ | ✓ |
| Sample | ✓ | ✓ |
| AnalysisResult | ✓ | ✓ |
| LabReport | ✓ | ✓ |
| Bottle | ✓ | ✓ |
| Complaint/CAPA/NC/Improvement/PT | ✓ | ✓ |
| AnalysisType | ✓ | (get_by_code_or_404 only) |
| Equipment | ✓ | ❌ |
| Chemical | ✓ | ❌ |
| AuditLog | ✓ | ❌ |
| MaintenanceLog | ✓ | ❌ |
| UsageLog | ✓ | ❌ |
| GbwStandard / ControlStandard | ✓ | ❌ |
| ChatMessage / OnlineStatus | ✓ | ❌ |
| ReportSignature | ✓ | ❌ |
| EnvironmentalLog | ✓ | ❌ |

Route нь Equipment-ийг 404 шалгах үед — `Repository.get_by_id(eid) or
abort(404)` гэж бичих эсвэл шууд `db.session.get` дуудах хэрэгтэй.
Inconsistent.

**BaseRepository pattern** ашиглавал энэ бүгдийг нэг газраас өвлүүлж болно:

```python
class BaseRepository(Generic[ModelT]):
    model: type[ModelT]

    @classmethod
    def get_by_id(cls, id_: int) -> Optional[ModelT]:
        return db.session.get(cls.model, id_)

    @classmethod
    def get_by_id_or_404(cls, id_: int) -> ModelT:
        obj = cls.get_by_id(id_)
        if obj is None:
            abort(404)
        return obj
```

---

### L5 · `get_active` метод нь **тус бүрд янз бүрийн утга буцаах**

| Repository | get_active(...) | Return type |
|------------|-----------------|-------------|
| `ChemicalRepository.get_active(lab_type)` | list[Chemical] | list |
| `BottleRepository.get_active()` | list[Bottle] | list |
| `GbwStandardRepository.get_active()` | Optional[GbwStandard] | **single** |
| `ControlStandardRepository.get_active()` | Optional[ControlStandard] | **single** |
| `ReportSignatureRepository.get_active(...)` | list[ReportSignature] | list |

Нэг нэрлэх "get_active" гэвч заримд **list**, заримд **single instance**.
Зөв нэр: `get_active_one()` vs `get_all_active()`.

---

### L6 · `standard_repository.py:87–94` — Гурван fallback алхамтай логик зөрчилтэй

```python
@staticmethod
def get_active_or_by_name(name: str) -> Optional[ControlStandard]:
    std = ControlStandard.query.filter_by(name=name, is_active=True).first()
    if not std:
        std = ControlStandard.query.filter_by(name=name).first()
    if not std:
        std = ControlStandard.query.filter_by(is_active=True).first()   # ← name огт хайхгүй
    return std
```

3 дахь fallback — `is_active=True` нэртэйг үл хамаарч буцаах. Caller "X нэртэй
standard" гэж асууж байсан тул нэр огт өөр standard ирэх нь bug магадлалтай.

`GbwStandardRepository` (line 35–40)-д **энэ 3 дахь fallback байхгүй** —
inconsistent.

---

### L7 · `system_setting_repository.py:58–69` — Hard-coded category/key string-үүд

```python
@staticmethod
def get_email_recipients() -> tuple[str, str]:
    to_setting = SystemSetting.query.filter_by(
        category='email', key='report_recipients_to'
    ).first()
    ...
```

`'email'`, `'report_recipients_to'`, `'report_recipients_cc'` — magic
strings. `app/constants/system_settings.py` дотор нэгтгэх:

```python
class SettingCategory:
    EMAIL = 'email'

class SettingKey:
    REPORT_RECIPIENTS_TO = 'report_recipients_to'
    ...
```

`get_gi_shift_config`, `get_repeatability_limits`-д мөн адил magic string.

---

### L8 · `equipment_repository.py:93` — `pattern: str` нь caller-аас `%X%` хэлбэрлэгдэх

```python
@staticmethod
def get_by_related_analysis(pattern: str, category: Optional[str] = None) -> list[Equipment]:
    """Related analysis талбараар ILIKE хайлт хийх."""
    q = Equipment.query.filter(
        ...
    )
    if category:
        q = q.filter(
            or_(Equipment.related_analysis.ilike(pattern), ...)   # ← raw pattern
        )
```

Caller-аас pattern `%Mad%` гэж өгөх ёстой. Abstraction leak — Repository нь
SQL ILIKE-ийн дүрэм мэддэг гэж онцолно. Зөв:

```python
def search_by_related_analysis(term: str, ...) -> list[Equipment]:
    pattern = f"%{term}%"
    ...
```

---

### L9 · Repository-д logger байхгүй

Repository бүгд `db.session.commit()` хийдэг боловч exception тохиолдолд **log
бичдэггүй**. SQLAlchemy `IntegrityError`, `OperationalError` ороход — caller
(service) дамжуулна гэж үзвэл OK. Гэвч хатуу зөвлөмж нь silent fallback
хийхгүй байх + log бичих.

Одоогийн дизайн — repository нь raw exception-ийг raise хийнэ, service catch
хийгээд бизнес-friendly алдаа болгоно. Acceptable.

---

## 5. ⚪ Nit / стилийн зөрчил

### N1 · `SystemSettingRepository.get` vs `get_value` — нэр төөрөгдмөл

```python
@staticmethod
def get(category: str, key: str) -> Optional[SystemSetting]:  # ← SystemSetting object
    ...

@staticmethod
def get_value(category: str, key: str, default: Any = None) -> Any:  # ← string value
    ...
```

`get(...)` нь дандаа `get_by_id()` гэхтэй адил object буцаах ёстой
convention-той. Энд `get` нь composite key (category, key)-ээр хайдаг.
`get_by_keys(category, key)` бичих нь илүү тогтвортой.

---

### N2 · `from typing import Optional, Any` олон файлд — `__future__` `annotations`-ыг бараг бүх файлд import хийсэн

```python
from __future__ import annotations
from typing import Optional
```

PEP 604 (Python 3.10+) `int | None` хэлбэр аль хэдийн `__future__ annotations`-той
ашиглах боломжтой. `Optional`-ыг устгах боломжтой:

```python
from __future__ import annotations
# typing import шаардлагагүй

def get_by_id(self, id_: int) -> User | None:
    ...
```

Гэхдээ codebase Python 3.11+-аар тогтсон бол шууд `int | None` бичих хэрэгтэй
(PEP 585). __future__-гүйгээр.

---

### N3 · `report_repository.py:74` — `from sqlalchemy import or_` метод **дотор**

```python
@staticmethod
def get_active(...) -> list[ReportSignature]:
    ...
    if lab_type:
        from sqlalchemy import or_       # ← method scope
        query = query.filter(or_(...))
    return query.all()
```

Other files (chat_repository, equipment_repository) `or_`-ыг top-аас import
хийсэн. Inconsistent.

---

### N4 · Module docstring урт-сэр зөрчилтэй

| Файл | Docstring |
|------|-----------|
| user_repository | 1 line |
| sample_repository | 5 lines |
| analysis_result_repository | 4 lines |
| equipment_repository | 1 line |
| chemical_repository | 1 line |
| ... | ... |

Convention — 1 line summary эсвэл 1 line + blank + extended description.

---

### N5 · `chat_repository.py:29, 33` — `db.and_` хэрэглээ

```python
or_(
    db.and_(ChatMessage.sender_id == user1_id, ...),
    db.and_(...),
),
```

SQLAlchemy `and_` нь `from sqlalchemy import and_, or_` гэж шууд import хийх
боломжтой. `db.and_` нь Flask-SQLAlchemy proxy — sqlalchemy import-той
тогтвортой бус.

---

### N6 · `analysis_result_repository.py:160` — `get_by_status(status: str)` нь validation хийдэггүй

```python
@staticmethod
def get_by_status(status: str) -> list[AnalysisResult]:
    return AnalysisResult.query.filter(AnalysisResult.status == status).all()
```

Caller буруу status дамжуулбал — хоосон жагсаалт буцаана. CHECK constraint-той
тулгаж validate хийх, эсвэл Enum-аар type-safe болгох.

---

### N7 · `EnvironmentalLogRepository` нэр зөрчил

```python
EnvironmentalLogRepository.get_by_id(log_id)      # → EnvironmentalLog
```

Singular vs plural — `*LogRepository` нь log нэг буцаах боломжтой. Бусад үед
"Logs" plural. Convention сонгох.

---

## 6. ℹ️ Info / acceptable

- **I1 · Static method pattern** — Repository класс нь stateless. OK.
- **I2 · `db.session.get(Model, id)`** — SQLAlchemy 2.0 native. Бараг бүх
  repository-д ашигласан — сайн.
- **I3 · `synchronize_session=False`** — Bulk update efficient. Acceptable
  гэхдээ caller event-аас ангид болохыг мэдэх ёстой.
- **I4 · `__init__.py` re-exports + `__all__`** — Сайн pattern, namespace
  цэвэр.

---

## 7. Дараагийн алхам

| № | Үйлдэл | Файл | Severity | Тэрчлэн |
|---|--------|------|----------|--------|
| 1 | **H1** — `maintenance_date` → `action_date` | `maintenance_repository.py:25` | 🟥 High | 1 commit (10 мин) |
| 2 | **H2** — `'disposed'` логик/schema-ийг нэг рүү шийдвэрлэх | `sample_repository.py` + `core.py` (магадгүй migration) | 🟥 High | 1–2 commit |
| 3 | M1 — Repositories-аас commit устгах + service @transactional | бүх 15 файл | 🔴 Medium | Том sprint (S5) |
| 4 | M2 — `Model.query` → `db.session.execute(select(...))` | бүх 15 файл | 🔴 Medium | Том sprint |
| 5 | M3 — `get_by_status` docstring "pending" → "pending_review" | `analysis_result_repository.py:165` | 🔴 Medium | 1 commit |
| 6 | M4 — `samples_with_approved_results` нэр зас | `analysis_result_repository.py:279` | 🔴 Medium | 1 commit |
| 7 | M5 — 18 model-д Repository нэмэх | олон шинэ файл | 🔴 Medium | Том sprint |
| 8 | M6 — `EnvironmentalLogRepository.delete()` нэмэх (эсвэл explicit reject) | `quality_repository.py` | 🔴 Medium | 1 commit |
| 9 | M7 — `deactivate_all` default commit=True болгох | `standard_repository.py` | 🔴 Medium | 1 commit (M1-тэй хамт устгана) |
| 10 | M8 — ChatMessage-д `deleted_by_id` нэмэх + log | `models/chat.py`, `chat_repository.py` | 🔴 Medium | 1 commit + migration |
| 11 | L1–L9 — Code quality (BaseRepository, helper-үүд, magic constants) | олон файл | 🟡 Low | 2 commit |
| 12 | N1–N7 — Style/naming nit | олон файл | ⚪ Nit | 1 commit |

**Зөвлөмж:** H1 (10 мин fix) → H2 (services-ийн audit-аас дараа шийдвэрлэх)
→ M3,M4,M6,M7 (нэг commit) → M1,M2,M5 (хамт том sprint).

---

## 8. Энэ audit-ын хамрах хүрээний дүгнэлт

✅ **Бүрэн шалгасан** — 15 repository файл (1 917 мөр).

⚠️ **Хамгийн өгөрхөл олдвор:** H1 (runtime AttributeError) — production-д
ажиллавал тэр route-аас 500 алдаа гарна, гэвч бүх route-аар дуудагдаагүй
байх магадлалтай тул хэн ч мэдээгүй болж магадгүй.

🔍 **Дараагийн алхам** — Services давхарга (~30 файл).
