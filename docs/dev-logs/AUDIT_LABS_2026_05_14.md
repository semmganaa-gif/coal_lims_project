# AUDIT — Labs давхарга (2026-05-14)

> **Хамрах хүрээ:** `app/labs/` — 18 файл, **5 478 мөр**.
> **Фокус:** BaseLab pattern, лаб-аар тусгаарласан хариуцлага, давхарга
> зөрчил, dead code.
> **Шалгасан:** Opus 4.7.

---

## 1. Хураангуй

`BaseLab` ABC pattern нь олон лабийг нэгтгэх сайн загвар. CoalLab,
PetrographyLab, ChemistryLab, MicrobiologyLab бүгд бүртгэгдсэн. Гэвч:

- 🔥 **`WaterLaboratory` парент классь, `water_lab_bp` blueprint бүртгэгдээгүй**
  тул `app/labs/water_lab/routes.py` бүхэлдээ **DEAD CODE** — invoke хийвэл
  `AttributeError: 'NoneType' object has no attribute 'sample_stats'`.
- 🔥 **`petrography/routes.py` `'prepared'` status filter dead** — Sample
  CheckConstraint-д тэр value байхгүй.
- `chemistry/routes.py` нь 47 `db.session/Model.query` call — Routes audit M1
  pattern давтан.
- `chemistry/constants.py:1` нь stale path comment: `# app/labs/water/constants.py`
  ("water" → "water_chemistry" refactor-аас үлдсэн).
- Inline role check 10+ газар — `@role_required` decorator dead code (Routes
  audit M3, M4 давтан).

| Severity | Тоо |
|----------|-----|
| 🟥 High | 2 |
| 🔴 Medium | 9 |
| 🟡 Low | 6 |
| ⚪ Nit | 4 |
| ℹ️ Info / acceptable | 4 |

---

## 2. 🟥 High severity

### H1 · `app/labs/water_lab/routes.py` + `WaterLaboratory` class — **DEAD CODE that CRASHES**

**Файлууд:**
- `app/labs/water_lab/__init__.py` (WaterLaboratory class)
- `app/labs/water_lab/routes.py` (water_lab_bp + main_hub route)

**Бөртгэл шалгалт:**

```python
# app/bootstrap/blueprints.py:13–19
from app.labs.coal import CoalLab
from app.labs.petrography import PetrographyLab
from app.labs.water_lab.chemistry import ChemistryLab
from app.labs.water_lab.microbiology import MicrobiologyLab

register_lab(CoalLab())
register_lab(PetrographyLab())
register_lab(ChemistryLab())
register_lab(MicrobiologyLab())
# ← WaterLaboratory() БҮРТГЭГДЭЭГҮЙ
```

Mөн `app/bootstrap/blueprints.py:36–37`:
```python
from app.labs.water_lab.chemistry.routes import water_bp
from app.labs.water_lab.microbiology.routes import micro_bp
# ← water_lab_bp БҮРТГЭГДЭЭГҮЙ
```

**Crash path** — `app/labs/water_lab/routes.py:15–38`:

```python
@water_lab_bp.route('/')
@login_required
@lab_required('water')               # ← 'water' нь User.allowed_labs values-д байхгүй
def main_hub():
    from app.labs import get_lab
    stats = get_lab('water_lab').sample_stats()    # ← get_lab('water_lab') нь None!
    #                                                      None.sample_stats() → AttributeError
```

**Аппликейшн ачаалахад асуудал гарахгүй** (blueprint бүртгэгдсэнгүй тул route
зарлагдахгүй). Гэвч хэн нэг developer:
1. Bootstrap-д `_safe_register(water_lab_bp)` нэмбэл → route активт.
2. `lab_required('water')` — User.allowed_labs дотор 'water' хэрэглэгчгүй тул
   бүх хэрэглэгчийг blocking. Зөвхөн admin байж магадгүй.
3. Admin route хүртэл явахад → `None.sample_stats()` AttributeError.

**Засвар:** Хэрэв WaterLaboratory нэгдсэн dashboard зорилготой бол:
1. `register_lab(WaterLaboratory())` нэмэх.
2. `_safe_register(water_lab_bp)` нэмэх.
3. `@lab_required('water_chemistry')` эсвэл shared `'water'` key-г User.allowed_labs-д
   тохиргоо хийх.

Эсвэл — энэ feature track хийгээгүй бол **бүх файлыг устгах**.

---

### H2 · `petrography/routes.py` — **`'prepared'` status нь Sample CheckConstraint-д байхгүй (filter dead)**

**Файл:** `app/labs/petrography/routes.py:46, 49, 106, 173`

```python
all_statuses = ['new', 'in_progress', 'analysis', 'prepared', 'completed']
pending_pe = _pe_samples(['new', 'in_progress', 'analysis']).count()
total_petro = _pe_samples(all_statuses).count()
in_progress = _pe_samples(['in_progress', 'analysis', 'prepared']).count()  # ← 'prepared' нэмсэн
completed = _pe_samples(['completed']).count()
```

`Sample.status` CheckConstraint (`core.py:267`):
```sql
CHECK (status IN ('new','in_progress','analysis','completed','archived'))
```

**'prepared' жагсаалтад байхгүй.** Тиймээс:

- `_pe_samples([..., 'prepared']).count()` — `WHERE status='prepared'` буюу
  **бүх үед 0**.
- `in_progress = _pe_samples(['in_progress', 'analysis', 'prepared']).count()`
  бодит дүн нь `'in_progress'` + `'analysis'`-ийн тоо.
- "prepared" нэр дээр UI label-аар хэрэглэсэн boл шинэ хэрэглэгч төөрөгдөнө.

Энэ нь Repos audit H2 (`'disposed'`), Services audit M10 (`'New'` capital)-ийн
**гурав дахь жишээ** — status enum-ийг тогтворгүй ашиглах урт хугацааны bug
pattern.

**Засвар:** Хоёр сонголтой:
- (а) Logic bug — 'prepared'-ыг устгах filter-аас. PE дээж бэлтгэлийн status
  нь өөр (`mass_ready=True` Boolean?) байж магадгүй.
- (b) Schema gap — 'prepared'-ыг CheckConstraint-д нэмэх (Alembic migration).
  Гэвч workflow_engine.DEFAULT_WORKFLOWS-д 'prepared' state байхгүй тул consistent
  байх ёстой.

---

## 3. 🔴 Medium severity

### M1 · `chemistry/routes.py` болон бусад — **130+ `db.session.*`/Model.query** layer skip

```bash
$ grep -c "db\.session\.\|.*\.query\." app/labs/water_lab/
chemistry/routes.py: 47
solutions.py: 27
microbiology/routes.py: 25
microbiology/micro_reports.py: 15
water_reports.py: 8
chemistry/utils.py: 10
chemistry/__init__.py: 2
microbiology/__init__.py: 2
```

**Repository ашиглалт:**

```bash
$ grep -c "Repository\." app/labs/water_lab/
chemistry/solutions.py: 4
microbiology/routes.py: 1
```

Зөвхөн 5 Repository call vs **130+ direct** — labs нь Repositories давхаргыг
бараг бүхлээр алгассан.

Routes audit M1, M2-той ижил pattern. Sprint 4-ээр шилжүүлэх.

---

### M2 · `water_lab/routes.py:17` — `@lab_required('water')` нь registered key биш

```python
@lab_required('water')
def main_hub():
    ...
```

Registered lab keys:
- `'coal'`
- `'petrography'`
- `'water_chemistry'`
- `'microbiology'`

`'water'` key нь:
- `INSTALLED_LABS`-д байхгүй (H1).
- `User.allowed_labs` доторх default `['coal']`-аас өөр valid values тодорхой бус.
- CLAUDE.md заасан `'water'` key-г refactor-аар `'water_chemistry'`-руу шилжүүлсэн
  ч `@lab_required('water')` хэвээр.

**Засвар:** `@lab_required('water_chemistry')` болгох. Эсвэл shared 'water' key-г
дэмжих lab_required logic нэмэх.

---

### M3 · `BaseLab.sample_query` / `sample_stats` — Repository алгасасан, "completed" filter dead

**Файл:** `app/labs/base.py:47–64`

```python
def sample_query(self, statuses=None):
    from app.models import Sample
    q = Sample.query.filter(Sample.lab_type == self.key)     # ← SampleRepository алгасасан
    ...

def sample_stats(self):
    from app.models import Sample
    base = Sample.query.filter(Sample.lab_type == self.key)
    return {
        ...
        'completed': base.filter(Sample.status == 'completed').count(),  # ← always 0
    }
```

**Хоёр асуудал:**

1. **`Sample.query` direct** — `SampleRepository.get_by_status()` эсвэл тусгайлсан
   helper байхгүй ч ашиглах боломжтой.

2. **`completed` count бүх үед 0**:
   - Services audit M11, Routes audit M11-аас баталгаажсан: `Sample.status =
     'completed'` нь зөвхөн `workflow_engine._hook_check_sample_complete`
     hook-аар set хийгддэг.
   - workflow_engine role mismatch (Services audit H1)-аас болж chemist-ийн
     workflow blocked → hook fire хийгдэхгүй.
   - Үр дүнд: бүх labs-ийн dashboard `completed: 0` гэж harvuugaa.

---

### M4 · `chemistry/constants.py:1` — Stale path comment

```python
# app/labs/water/constants.py        # ← Хуучин зам (refactor-ийн өмнө)
"""Усны лабораторийн шинжилгээний параметрүүд."""
```

Файлын бодит зам: `app/labs/water_lab/chemistry/constants.py`. Refactor
`'water'` → `'water_chemistry'` (commit `e206e63`)-ийн дараа file header
комментоо update хийгээгүй. Documentation drift.

---

### M5 · `chemistry/routes.py:1158` — **Bulk DELETE without audit log per result**

```python
# Холбогдох AnalysisResult-уудыг эхлээд устгах (orphan сэргийлэлт)
AnalysisResult.query.filter_by(sample_id=sample.id).delete()

log_audit(
    action='sample_deleted',
    resource_type='Sample',
    resource_id=sample.id,
    details={'sample_code': sample.sample_code, 'client_name': sample.client_name},
)
db.session.delete(sample)
```

**3 асуудал:**

1. **AnalysisResult-ыг устгахаас өмнө `log_analysis_action(action='DELETED', ...)`-ийг
   дуудаагүй**. Sample-ийн `log_audit` бий, гэвч тус result-уудын аудит лог
   үлдээгүй (mass_service.delete_sample-д үлгэр).

2. **Bulk DELETE bypasses ORM event listeners.** Сайн уг: `AnalysisResultLog`
   нь `analysis_result_id` FK-аар `ondelete="SET NULL"` тул log survives.
   Гэвч `AnalysisResult.version_id` (optimistic locking) шалгагдахгүй.

3. **`cascade="all, delete-orphan"` (Sample.results, core.py:280) аль хэдийн
   бий тул `.delete()` redundant**. `db.session.delete(sample)` нь auto-cascade
   хийнэ.

`microbiology/routes.py:161` нь яг ижил pattern (cascade-ыг ашигладаг, гэхдээ
audit log per result-гүй).

---

### M6 · Inline `current_user.role` check **10+ газар** (Routes audit M3 давтан)

```bash
$ grep -rn "current_user\.role" app/labs/
chemistry/routes.py:1070,1133,1145,1153,1314,1337,1364
solutions.py:279,735
microbiology/routes.py:77,140,152
micro_reports.py:504
```

`@role_required(...)` decorator (`app/utils/decorators.py:14`) аль хэдийн бий —
гэхдээ Routes audit M4-аас баталгаажсан **dead code**. Хэн ч импорт хийдэггүй.

---

### M7 · **Chemist дээж устгах эрхтэй** (хэт зөвшөөрөл)

`chemistry/routes.py:1133, microbiology/routes.py:140`:
```python
if current_user.role not in ('admin', 'senior', 'chemist'):
    flash('You do not have permission to delete samples.', 'danger')
    return redirect(...)
```

Хязгаарласан зүйл (line 1145):
```python
if current_user.role in ('senior', 'chemist') and sample.status != 'new':
    failed.append(f'{sample.sample_code} (Боловсруулалтад орсон)')
    continue
```

**Үр дүн:**
- Chemist + Senior: `status='new'` дээж устгах боломжтой (approved result-гүй бол).
- Admin: ямар ч дээж устгах боломжтой.

**Asuudal:** ISO 17025-д дээж устгах нь serial process — chemist-д хязгаарлахгүй
байх нь permissive. Defensive control нь зөв уг гэхдээ:
- Audit-аас илрэх боломжтой control gap.
- "Дээжийг засах" эсвэл "цуцлах" (status='cancelled') гэж soft pattern илүү
  тогтвортой.

---

### M8 · `microbiology/routes.py:120` — Микробиологийн route нь **chemistry template** rendering хийдэг

```python
return render_template(
    'labs/water/chemistry/water_edit_sample.html',    # ← chemistry template
    title='Дээж засах',
    sample=sample,
    ...
)
```

Micro/chem labs хоорондын coupling. UI-ийн төстэй байдалд OK, гэвч:
- Chemistry template-ийг өөрчилбөл micro UI санамсаргүйгээр өөрчлөгдөнө.
- Test/mock isolation хүндрэлтэй.

**Засвар:** Хоёр өөр template, эсвэл `labs/water/shared/edit_sample.html` shared
template.

---

### M9 · `chemistry/utils.py:_generate_micro_lab_id` — N+1 query

```python
def _generate_micro_lab_id(sample_date, next_batch=False):
    ...
    rows = db.session.query(Sample.micro_lab_id).filter(...).all()   # ① All micros
    ...
    today_count = Sample.query.filter(...).count()                   # ② Today's count
    ...
    if next_batch and today_count > 0:
        existing_today = db.session.query(...).all()                 # ③ Today's micros
    elif today_count > 0:
        existing = db.session.query(...).first()                     # ④ First today
    ...
    total_samples = Sample.query.filter(micro_filter).count()        # ⑤ Total count
```

Нэг ID үүсгэхэд 3–5 query. `create_water_micro_samples`-аар sample 50-аад үүсгэх
үед — 200+ query.

Sequence/counter table эсвэл cached counter ашиглах нь хурдан. (Жижиг
оптимизаци, гэхдээ batch-аар нэмэгдэнэ.)

---

## 4. 🟡 Low severity

### L1 · `BaseLab.sample_query`/`sample_stats` нь `@abstractmethod` биш

```python
class BaseLab(ABC):
    @property
    @abstractmethod
    def key(self) -> str: ...

    def sample_query(self, statuses=None):   # ← @abstractmethod БИШ
        ...

    def sample_stats(self):                  # ← @abstractmethod БИШ
        ...
```

Subclass нь `sample_query`-ийг override хийхгүй бол default `Sample.lab_type ==
self.key` filter ажиллана. Жишээ:

- `WaterLaboratory.key='water_lab'` (line 18) → default sample_query нь `lab_type
  == 'water_lab'` — ОГТ ТОХИРОХГҮЙ (real values: 'water_chemistry',
  'microbiology'). Тиймээс override хийсэн (line 41).
- Гэхдээ override forgотовч бол silent zero results.

`@abstractmethod`-аар enforce хийх нь зөв уг.

---

### L2 · `chemistry/routes.py:7` — Underscore aliases for builtins

```python
import json as _json
from datetime import datetime as _dt, timedelta as _td
```

Underscore alias нь "private" гэсэн convention. Гэвч `json`, `datetime`,
`timedelta` нь стандарт нэр. Aliasing наc стандарт нэрийг "private"-аар
тэмдэглэх нь буруу сэдэлт.

`import json` шууд бичих нь зөв (chemistry/utils.py-д шиг).

---

### L3 · `petrography/routes.py:32–38` — `or_` logic — sample_type='PE' fallback

```python
return Sample.query.filter(
    Sample.status.in_(statuses),
    or_(
        Sample.lab_type == 'petrography',
        Sample.sample_type == 'PE',
        Sample.analyses_to_perform.contains('"PE"'),
    )
)
```

3 өөр газраас петрограф дээж тогтоох — legacy data-аас sample_type='PE',
ирээдүйд analyses_to_perform JSON, эсвэл lab_type='petrography'. Гурван эх
үүсвэр нэгэн дороор query — query optimizer-ийн ажил хүнд.

`lab_type='petrography'`-руу migrate хийсэн дараа `or_` бүрэлдхэх ёстой.

---

### L4 · `chemistry/utils.py:271` — `from app.services.sla_service import assign_sla` deferred import in loop

```python
for sample_name in sample_names:
    ...
    for suffix in suffixes:
        ...
        sample = Sample(...)
        from app.services.sla_service import assign_sla   # ← Loop дотор
        assign_sla(sample)
```

Loop бүрд import statement ажиллана (Python cache хийдэг боловч). Top-level
import илүү цэвэр.

---

### L5 · `solutions.py:691` — Bulk DELETE on `SolutionRecipeIngredient`

```python
SolutionRecipeIngredient.query.filter_by(recipe_id=recipe.id).delete()
```

`SolutionRecipe.ingredients` relationship-д `cascade='all, delete-orphan'`
(solutions.py:137 in models) аль хэдийн бий. Bulk DELETE redundant.

---

### L6 · All labs hardcoded "completed" in sample_stats

`base.py:63`, `chemistry/__init__.py:47`, `microbiology/__init__.py:47`,
`water_lab/__init__.py:57`:

```python
'completed': base.filter(Sample.status == 'completed').count(),
```

Workflow audit M11 (Routes audit)-ийн нэгэн адил — `completed` нь зөвхөн
workflow hook-аар set хийгддэг. Practical-аар бүгд 0.

---

## 5. ⚪ Nit / стилийн зөрчил

### N1 · Lab keys inconsistent

```
'water_lab'         — WaterLaboratory (parent, unregistered)
'water_chemistry'   — ChemistryLab (child)
'microbiology'      — MicrobiologyLab (child)
```

Parent-child naming зөрчилтэй. `water` parent, `water_chemistry`/`water_micro`
child нь илүү тогтвортой.

---

### N2 · `BaseLab.color` — hex string format баталгаа байхгүй

```python
@property
@abstractmethod
def color(self) -> str:
    """Лабын өнгө (hex)."""
    ...
```

Type hint `str` ч hex format-ыг enforce хийдэггүй. `'#dc3545'` ажиллана, `'red'`
ажиллана — UI-д CSS-аар render-д аль аль нь зөв. OK.

---

### N3 · `chemistry/utils.py:148` — Function name `create_water_micro_samples` зөрчилтэй

Function нь хоёр lab_type-ийг (water_chemistry эсвэл microbiology) тогтооно
(line 168–171), нэг утга буцаахгүй. Нэр "water_micro" хоёр өгөгдөл нэг аппликейшнд
гэж буруу таамаглуулна.

---

### N4 · `petrography/routes.py:78–82` — `form_templates` dict дотор `'TS_PETRO'` key

```python
form_templates = {
    'MAC': '...maceral_form.html',
    'VR': '...vitrinite_form.html',
    'MM': '...mineral_form.html',
    'TS_PETRO': '...thin_section_form.html',   # ← Underscore
    'MOD': '...mineral_form.html',
    'TEX': '...thin_section_form.html',
    'GS': '...mineral_form.html',
}
```

`PETRO_ANALYSIS_TYPES` (constants.py:66) дотор `'TS_PETRO'` гэж бичсэн —
матчилж байгаа. Гэвч AnalysisResult-ийг хадгалахад `analysis_code='TS_PETRO'`
гэсэн уг (line 151 `analysis_code.upper()`). Coal lab-д `'TS'` (Total Sulfur)
аль хэдийн бий — өөр код, conflict зайлсхийх зорилгоор '_PETRO' suffix. OK уг
гэвч naming convention тогтвортой бус.

---

## 6. ℹ️ Info / acceptable / сайн pattern

- **I1 · `BaseLab` ABC** — Abstract base class нь shared behavior + abstract
  contract зөв.
- **I2 · `INSTALLED_LABS` registry pattern** (`labs/__init__.py:13`) — Plugin-аар
  лаб бүртгэх боломж. **Сайн.**
- **I3 · `lab_required` decorator** — Лабын эрхийн шалгалт зөв нэгтгэгдсэн.
- **I4 · `@water_bp.route` import-аар нэгтгэх pattern** (solutions.py:16) —
  Нэг blueprint олон файлд route-ыг бүртгэх — modular.

---

## 7. Дараагийн алхам

| № | Үйлдэл | Severity | Тэрчлэн |
|---|--------|----------|--------|
| 1 | **H1** — `WaterLaboratory`-г бүртгэх эсвэл устгах (dead code дилемма) | 🟥 High | 1 commit |
| 2 | **H2** — `'prepared'` status засах (filter эсвэл schema) | 🟥 High | 1 commit |
| 3 | M1 — Labs-аас `db.session.*` устгаж Repos-руу шилжүүлэх (Sprint 4) | 🔴 Medium | Том sprint |
| 4 | M2 — `@lab_required('water')` → `@lab_required('water_chemistry')` | 🔴 Medium | 1 commit (H1-тэй хамт) |
| 5 | M3 — `BaseLab.sample_stats` нь `completed` filter-ыг review хийх | 🔴 Medium | Routes M11-тэй хамт |
| 6 | M4 — `chemistry/constants.py:1` stale path comment засах | 🔴 Medium | 1 commit (nit-тэй хамт) |
| 7 | M5 — `delete_samples` бүрд audit log per result нэмэх | 🔴 Medium | 1 commit |
| 8 | M6 — Inline role check → `@role_required` (Routes M3-той хамт) | 🔴 Medium | 1 commit |
| 9 | M7 — Chemist delete permission бодлогийг review | 🔴 Medium | Discussion |
| 10 | M8 — `microbiology` route өөрийн template хэрэглэх | 🔴 Medium | 1 commit |
| 11 | M9 — `_generate_micro_lab_id` queries-ийг каш/sequence-аар оптимиз | 🔴 Medium | 1 commit |
| 12 | L1–L6 — Style/correctness fixes | 🟡 Low | 2 commit |
| 13 | N1–N4 — Nit | ⚪ Nit | 1 commit |

---

## 8. Энэ audit-ын хамрах хүрээний дүгнэлт

✅ **Бүрэн уншсан:** `base.py`, `__init__.py`-ууд (бүх 7), `petrography/routes.py`,
   `water_lab/routes.py`, `chemistry/utils.py` бүрэн; `chemistry/routes.py`
   эхэлж + хэсэгчилсэн (1 200/1 460 мөр); `microbiology/routes.py` 200 мөр.

📊 **Pattern-аар шалгасан:** chemistry/constants.py, solutions.py,
   water_reports.py, microbiology/micro_reports.py, microbiology/constants.py.

⚠️ **Хамгийн чухал олдвор:**
- **H1** — WaterLaboratory dead code, invoke хийвэл AttributeError. Бүртгэх
  эсвэл устгах гэсэн yes-or-no шийдвэр шаардлагатай.
- **H2** — `'prepared'` status — Repos H2 (`'disposed'`), Services M10 (`'New'`)
  нэгдэн "status enum drift" төрлийн **3 дахь жишээ**. Status enum-ийг Enum
  class-аар хатуу хязгаарлах нь long-term зөв уг (Models M5).

🔍 **Дараагийн алхам — Utils + Forms + Schemas + Constants + Templates** —
сүүлийн хэсэг.
