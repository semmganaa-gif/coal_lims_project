# AUDIT — Models давхарга (2026-05-14)

> **Хамрах хүрээ:** `app/models/` — 20 файл, **3 572 мөр**.
> **Фокус:** Архитектур (давхарга, ISO 17025 audit trail, ondelete) + код чанар.
> **Шалгасан:** Opus 4.7. Memory-feedback: perfect over fast.

---

## 1. Хураангуй

Models давхарга нь логик ангиллаар хуваагдсан (analysis / equipment / chemicals /
quality / quality_records / planning / reports / etc) — сайн зохион байгуулалт.
**`HashableMixin` + SQLAlchemy `event.listen('before_update'/'before_delete')`**
pattern нь audit log-уудын ISO 17025 immutability-ийг хангаж байгаа нь маш сайн
шийдэл.

Гэвч:

- **1 реал encoding bug** олдсон (CheckConstraint дотор Latin+Cyrillic холимог).
- **ISO 17025 audit immutability нэг хэсэгт алга** — `MaintenanceLog`,
  `UsageLog`, `EnvironmentalLog`, `QCControlChart`, `ProficiencyTest` нь
  calibration/QC мэдээллийн audit trail боловч `event.listen`-гүй, hash-гүй.
- 35+ string column-д CheckConstraint байхгүй — free-form input гүйцэдгээ
  баталгаажуулдаггүй.
- ondelete behavior зарим FK-д тодорхой, заримд алга — өгөгдлийн integrity
  зөрчилтэй.

| Severity | Тоо |
|----------|-----|
| 🟥 High | 2 |
| 🔴 Medium | 8 |
| 🟡 Low | 9 |
| ⚪ Nit | 11 |
| ℹ️ Info / acceptable | 6 |

---

## 2. 🟥 High severity

### H1 · `app/models/core.py:261` — **CheckConstraint дотор кирилл/латин холимог тэмдэгт**

```python
__table_args__ = (
    CheckConstraint(
        "client_name IN ('CHPP','UHG-Geo','BN-Geo','QC','WTL','Proc','LAB',"
        "'uutsb','negdsen_office','tsagaan_khad','tsetsii',"
        "'naymant','naimdai','malchdyn_hudag',"
        "'hyanalт','tsf','uarp','shine_camp','busad',"     # ← 'hyanalт' bug
        "'dotood_air','dotood_swab',"
        "'naimdain','maiga','sum','uurhaichin','gallerey','sbutsb')",
        name="ck_sample_client_name",
    ),
    ...
)
```

`'hyanalт'`-ийн `т` нь **U+0442 (Cyrillic small letter Te)** — бусад тэмдэгт
бүгд Latin. Python source-ийн `\xd1\x82` UTF-8 байт.

**Үр дагавар:**

1. DB-д энэ CHECK constraint яг л `'hyanalт'` (mixed string) утгыг л
   зөвшөөрнө. Хэрэглэгч "хяналт" (бүх Cyrillic) эсвэл "hyanalt" (бүх Latin) шивэх
   нь **INSERT/UPDATE алдаа гарна**.
2. Шинээр гар утга шиввэл client_name нь Routes/Service-аас энэ exact
   mixed-encoding-аар л ирэх ёстой — бараг боломжгүй.
3. Үр дүнд: "хяналт" төрлийн дээж шивэх боломжгүй (бид routes/services-ийг
   шалгахдаа баталгаажуулна).
4. Илрэгдсэн магадлал: pre-existing CSV import, Alembic migration хийгдсэн ч
   худал зөв байсан гэж итгэх.

Мөн ойролцоо талд `'naimdai'` (line 262) болон `'naimdain'` (line 263) — нэг
үсгээр зөрсөн нь typo юм уу, эсвэл хоёр өөр газрын нэр (Наймдай vs Наймдайн)
эсэх тодорхойгүй.

**Засвар:** Зөв Latin transliteration `'hyanalt'` ашиглах, эсвэл бүх Mongolian-г
Cyrillic-р хадгалах. Alembic migration шаардлагатай (CHECK constraint солих).

> Comment-д шингэсэн зөвлөмж: client_name-г string-ээр биш, **lookup table**
> (`Client` model) болгож FK-р холбох нь long-term хариулт. Тэгвэл өөрчлөлт нь
> ердөө INSERT/UPDATE, schema migration огт хэрэггүй.

---

### H2 · `MaintenanceLog`, `UsageLog`, `EnvironmentalLog`, `QCControlChart`, `ProficiencyTest` — **ISO 17025 audit immutability дутуу**

**Файлууд:**
- `app/models/equipment.py:94` (MaintenanceLog), `app/models/equipment.py:122` (UsageLog)
- `app/models/quality_records.py:130` (EnvironmentalLog)
- `app/models/quality_records.py:172` (QCControlChart)
- `app/models/quality_records.py:83` (ProficiencyTest)

`AnalysisResultLog`, `AuditLog`, `ChemicalLog`, `SparePartLog` бүгд:
- `HashableMixin` (SHA-256 data_hash)
- `event.listen('before_update', _block_update)` — өөрчлөх боломжгүй
- `event.listen('before_delete', _block_delete)` — устгах боломжгүй

Гэвч **тоног төхөөрөмжийн calibration record**, **орчны нөхцлийн бүртгэл**,
**QC хяналтын график**, **PT (proficiency test)** — эдгээр нь ISO 17025
шаардлагын дагуу **storage-once, alter-never** ёстой:

- **ISO 17025 § 6.4.13** — Equipment calibration records.
- **ISO 17025 § 6.3.3** — Environmental monitoring.
- **ISO 17025 § 7.7.1** — QC measurements (control charts).
- **ISO 17025 § 7.7.2** — Proficiency testing records.

Одоо эдгээр model-уудад `db.session.commit()` явсаны дараа админ хүн ч UPDATE
хийх боломжтой. **Аудит хийгчид олдвол non-conformity record үүснэ.**

**Засвар:** Эдгээр 5 model-д `HashableMixin` + `event.listen` block идэвхжүүлэх.
Засварын logic-ийг "version-аар бичих" (versioning) аргаар шилжүүлэх:
calibration record-ийг update хийхгүй, шинэ row нэмж `effective_to`-г
тэмдэглэх. BottleConstant-ыг үлгэр болгох — `effective_from/effective_to` болон
`approved_at` талбартай — энэ pattern-ийг бусад model-д хэрэглэх.

---

## 3. 🔴 Medium severity

### M1 · `core.py:144` — `check_password` нь `password_hash=None` үед `TypeError` raise

```python
def check_password(self, password: str) -> bool:
    return check_password_hash(self.password_hash, password)
```

Шинэ User үүсгэхэд `password_hash` талбар default-гүй, nullable. Хэрэв login
flow-д ийм User тааралдвал `check_password_hash(None, ...)` → `TypeError`.
Login route 500 алдаа өгнө.

**Засвар:**
```python
def check_password(self, password: str) -> bool:
    if not self.password_hash:
        return False
    return check_password_hash(self.password_hash, password)
```
эсвэл column түвшинд `nullable=False`-аар хорих.

---

### M2 · FK-уудын **`ondelete` behavior зөрчилтэй**

| Файл / Model | FK | ondelete | Үр дагавар |
|--------------|------|----------|-----------|
| `core.py:209` Sample.user_id | user.id | **байхгүй** | User устгахад orphan |
| `core.py:233` Sample.mass_ready_by_id | user.id | **байхгүй** | nullable боловч ondelete-гүй |
| `analysis.py:59` AnalysisResult.sample_id | sample.id | **байхгүй** | Sample-ийн `cascade="all, delete-orphan"` relationship side харгалзахгүй DB-түвшинд |
| `analysis.py:60` AnalysisResult.user_id | user.id | **байхгүй** | User устгахад orphan |
| `equipment.py:101` MaintenanceLog.equipment_id | equipment.id | **байхгүй** | Equipment устгахад orphan (cascade relationship-аар хамгаалагдсан, гэвч DB level гуй) |
| `chemicals.py:154` ChemicalUsage.chemical_id | chemical.id | **байхгүй** | nullable=False боловч ondelete-гүй |
| `chemicals.py:190` ChemicalLog.chemical_id | chemical.id | **байхгүй** | Хатуу хамаарал |
| `quality_records.py:265` CustomerComplaint.capa_id | corrective_action.id | **байхгүй** | CAPA устгахад FK violation |
| `worksheets.py:47` WaterWorksheet.primary_reagent_lot_id | chemical.id | **байхгүй** | nullable боловч ondelete-гүй |
| `worksheets.py:136` WorksheetRow.reagent_lot_id | chemical.id | **байхгүй** | Reagent устгасан → FK violation |

ondelete-тэй гэж үзэх жишээ:
- `analysis_audit.py:70` `sample_id` ondelete="SET NULL" ✓
- `analysis_audit.py:77` `analysis_result_id` ondelete="SET NULL" ✓
- `chat.py:33` sample_id ondelete="SET NULL" ✓

**Гол асуудал:** `relationship(... cascade="all, delete-orphan")` нь
**ORM-level** delete-ийг л зохицуулдаг. Хэрэв админ `DELETE FROM user WHERE
id=X` гэж SQL шууд явуулбал, эсвэл cascade trigger ажиллахгүй migration
тохиолдол байвал — orphan үүснэ.

**Засвар:** Бүх FK-д `ondelete="CASCADE"` (хатуу хамаарал) эсвэл `"SET NULL"`
(audit retention) тодорхой бичих.

---

### M3 · `core.py:88–123` — `validate_password` docstring **vs** код таарахгүй

```python
"""
Шаардлага:
    - Хамгийн багадаа 10 тэмдэгт      ← docstring
    ...
>>> User.validate_password('abc')
['хамгийн багадаа 8 тэмдэгт байх ёстой', ...]   ← Example нь 8 тэмдэгт
"""
errors = []
if len(password) < 10:                           ← Код нь 10
    errors.append("хамгийн багадаа 10 тэмдэгт байх ёстой")
```

Docstring "хамгийн багадаа 10 тэмдэгт" гэж зөв бичсэн, гэвч **Example блок**
"хамгийн багадаа 8 тэмдэгт" гэж хуучин утгыг үлдээсэн. Refactor-ийн дараа
documentation drift.

---

### M4 · `analysis_audit.py:180–216` — Domain constants model файлд

```python
# app/models/analysis_audit.py
AUDIT_ACTIONS = ('CREATED', 'UPDATED', ...)
DEFAULT_ERROR_REASONS = {
    'sample_prep': '1. Дээж бэлтгэлийн алдаа...',
    ...
}
```

Эдгээр нь **business domain constants** — model файлд биш, `app/constants.py`
эсвэл `app/config/audit.py`-д байх ёстой. `AnalysisResultLog`-ийн definition-ыг
тойруулсан газарт constants нийлсэн — separation of concerns зөрчилтэй.

Мөн line 182–189 нь stale comment block — `app/models/quality.py` нэр заасан,
гэвч файл нь `app/models/bottles.py` (refactor-ийн үлдэгдэл).

---

### M5 · `core.py:39, 53–58` — `User.role` нь **string + 'admin' literal**

```python
role = db.Column(db.String(64), index=True, default="prep")     # column
...
def has_lab_access(self, lab_key: str) -> bool:
    if self.role == 'admin':                                    # literal compare
        return True
```

- 5 role жагсаасан (prep, chemist, senior, manager, admin) — гэвч CheckConstraint
  байхгүй. DB-д ямар ч string зөвшөөрнө.
- `'admin'` нь hard-coded literal (bootstrap audit-аас давтан гарсан — middleware-д
  мөн адил). Constants/Enum-аар солих хэрэгтэй.

**Засвар:**
```python
class UserRole(str, Enum):
    PREP = 'prep'
    CHEMIST = 'chemist'
    SENIOR = 'senior'
    MANAGER = 'manager'
    ADMIN = 'admin'

role = db.Column(db.String(20), default=UserRole.PREP.value)
__table_args__ = (
    CheckConstraint(f"role IN ({','.join(repr(r.value) for r in UserRole)})",
                    name='ck_user_role'),
)
```

---

### M6 · `core.py:218` — `Sample.analyses_to_perform` нь зайгаар тусгаарлагдсан string

```python
analyses_to_perform = db.Column(db.String(500))     # "Mad Aad Vad CV..."
```

**1NF зөрчил.** Олон утга нэг талбарт. Query хийхэд `LIKE '%Mad%'`, нэмэхэд
string concat. Junction table эсвэл JSON column ашиглах хэрэгтэй.

Гэвч legacy code-аар дамжсан байх магадлалтай, refactor-д careful.

---

### M7 · 35+ string column-д **CheckConstraint байхгүй**

| Model | Column | Жагсаасан утга | Constraint |
|-------|--------|----------------|----------|
| `User.role` | string | prep/chemist/senior/manager/admin | ❌ |
| `Sample.priority` | string | normal/urgent/rush | ❌ |
| `AnalysisResult.rejection_category` | string | "ISO буцаалт ангилал" | ❌ |
| `AnalysisResult.error_reason` | string | KPI алдааны шалтгаан | ❌ |
| `Equipment.category` | string | "other" default | ❌ |
| `Equipment.register_type` | string | "main" default | ❌ |
| `MaintenanceLog.action_type` | string | Calibration/Repair/Maintenance/Daily Check | ❌ |
| `MaintenanceLog.result` | string | Pass/Fail/Warning | ❌ |
| `Chemical.lab_type` | string | coal/water/microbiology/petrography/all | ❌ |
| `Chemical.category` | string | acid/base/solvent/indicator/standard/media/other | ❌ |
| `ChemicalLog.action` | string | бүх үйлдэл | ❌ |
| `InstrumentReading.status` | string | pending/approved/rejected | ❌ |
| `InstrumentReading.instrument_type` | string | tga/bomb_cal/elemental/karl_fischer | ❌ |
| `ChatMessage.message_type` | string | text/image/file/sample/urgent | ❌ |
| `CustomerComplaint.status` | string | draft/received/resolved/closed | ❌ |
| `ImprovementRecord.status` | string | pending/in_progress/reviewed/closed | ❌ |
| `NonConformityRecord.status` | string | pending/investigating/reviewed/closed | ❌ |
| `LabReport.status` | string | draft/pending_approval/approved/sent | ❌ |
| `LabReport.report_type` | string | analysis/summary/certificate | ❌ |
| `WaterWorksheet.status` | string | open/submitted/approved/rejected | ❌ |
| `WorksheetRow.row_type` | string | unknown/blank/control/duplicate/spike/msd | ❌ |
| `WorksheetRow.qc_status` | string | pending/pass/warn/fail | ❌ |
| ... | ... | ... | ❌ |

Зөв жишээ нь `Sample.status` (`'new','in_progress','analysis','completed','archived'`)
дээр `ck_sample_status` constraint бий. `AnalysisResult.status`-д бас бий.
Гэвч бусад нь "documentation only".

DB level constraint байхгүй бол migration, batch import, эсвэл typo-ийн үед
буруу утга өгөгдөл рүү орох эрсдэлтэй.

---

### M8 · `analysis.py:459–460` — `qnet_ar` stub method (бүх үед None буцаах)

```python
@property
def qnet_ar(self):
    return None
```

Comment байхгүй, doc-гүй. "Хийгдэх дутуу" эсвэл `qnet_ar`-ийг зориуд аль өөр
газар тооцоолох гэж байгаа эсэх тодорхойгүй. Dead code эсвэл late binding-ийн
магадлалтай.

`SampleCalculations`-ыг хэрэглэдэг газар (template/service) `calc.qnet_ar` гэж
дуудаж байгаа эсэхийг шалгаж, хэрэв ашигладаг бол бодит implement, ашиглахгүй
бол устгах.

---

## 4. 🟡 Low severity

### L1 · `core.py:11, 321` — Regex дотор fancy quotes ба `³` superscript

```python
import re
import json   # ← unused в core.py
...
if not re.match(r'^[\wЀ-ӿ\s/.,+\-\"""()³]+$', value):
```

`""` нь U+201C (left double quotation mark) болон U+201D (right double quotation
mark) — Word/docx-аас copy-paste-ын ул мөр. Smart quotes-ыг ердийн ASCII `"`-аар
солих, эсвэл нэмж зөвшөөрөгдсөн тэмдэгт жагсаалт зориуд бичих.

Мөн `³` (U+00B3, superscript three) — `m³` (cubic meter) нэгжид зориулагдсан
байж магадгүй. Хэрэглээ нь зөв байж болох ч comment-аар тайлбарлах хэрэгтэй.

`json` import line 11-д unused → устгах.

---

### L2 · `license.py:10–12` — `_safe_now` нь tzinfo-г хасч naive datetime буцаах

```python
def _safe_now():
    """Naive datetime буцаана (DB-д хадгалсан expiry_date-тэй зэрэгцүүлэхэд)."""
    return _now_mn_raw().replace(tzinfo=None)
```

DB column-ууд (`db.DateTime`) нь default-аар naive (no tz). Гэвч `now_local()`
нь tz-aware datetime буцаадаг тул `replace(tzinfo=None)` нь зориуд хийсэн
зөв уг.

**Эрсдэл:** `_safe_now() > self.expiry_date` (line 58) — энэ хоёулаа naive.
Хэрэв `expiry_date`-ийг өөр газраас tz-aware ачаалбал (timezone parse-тай ISO
string) `TypeError: can't compare offset-naive and offset-aware datetimes`.

Тогтвортой UTC timezone хадгалах нь long-term зөв шийдэл — `DateTime(timezone=True)`
ашиглах. Гэвч одоогийн дизайн codebase-д бүх talble naive байгаа тул consistent.

---

### L3 · `chat.py:61–62, 87–91` — `to_dict` нь lazy load N+1 risk

```python
def to_dict(self):
    result = {
        ...
        'sender_name': self.sender.username if self.sender else None,
        'receiver_name': self.receiver.username if self.receiver else None,
        ...
    }
    ...
    if self.sample_id and self.sample:
        result['sample'] = {'id': self.sample.id, 'code': self.sample.sample_code, ...}
```

Chat list endpoint олон message-ийг load хийгээд `to_dict` дуудах үед —
- `sender` lazy load (1 SELECT)
- `receiver` lazy load (1 SELECT)
- `sample` lazy load (1 SELECT)

100 message → 301 SELECT. `joinedload`-аар service давхарга-д optimize хийх.

---

### L4 · `equipment.py` — Equipment model нь **`serial_number`-д unique constraint, index байхгүй**

```python
serial_number = db.Column(db.String(100))    # ← no unique, no index
```

ISO asset бүртгэлд serial number нь өвөрмөц шаардлагатай (бараг). Тодорхой
давхардсан хайлт хийх үед index хэрэгтэй.

---

### L5 · `chemicals.py:96, 113`; `solutions.py:87`; `spare_parts.py:113` — Model дотор business logic

```python
class Chemical(db.Model):
    def update_status(self):
        """Нөөц болон хугацаанд үндэслэн төлөвийг автоматаар шинэчлэх."""
        from datetime import date, timedelta
        today = date.today()
        ...

    def days_until_expiry(self):
        ...
```

Convention-аар бол:
- `update_status` нь side-effect (status хувьсагч өөрчилнө) — service layer-д.
- `days_until_expiry`, `is_expiring_soon` — pure read computations, `@property`-аар үлдэх боломжтой.

Гэвч энэ нь "model-rich" pattern (DDD-ын entity дотор encapsulation). Project
convention-ы хатуу хэрэглээ: Routes → Service → Repository → Model. Иймд
`update_status()`-ийг service layer-д шилжүүлэх.

---

### L6 · `equipment.py:82, 89` болон бусад — `lazy='dynamic'` нь SQLAlchemy 2.0-д **deprecated**

```python
logs = db.relationship('MaintenanceLog', backref='equipment', lazy='dynamic', ...)
usages = db.relationship('UsageLog', backref='equipment', lazy='dynamic', ...)
```

`lazy='dynamic'` нь Query API буцаадаг (Query.filter() гэж дуудах боломжтой).
SQLAlchemy 2.0 + Flask-SQLAlchemy 3.x-д энэ нь deprecated, ирээдүйд устах.
**`lazy='select'` + service-д filter logic** эсвэл `with_loader_criteria`
ашиглах нь 2.0-н шилжилт.

Бусад файлд олон: `chemicals.py:90,92`; `spare_parts.py:110,111`;
`reports.py` (тийм биш); `solutions.py:137,139` гэх мэт.

---

### L7 · `reports.py:148–155` — Hard-coded Mongolian status labels in model

```python
def get_status_display(self):
    status_map = {
        'draft': 'Ноорог',
        'pending_approval': 'Хүлээгдэж буй',
        ...
    }
    return status_map.get(self.status, self.status)
```

Mongolian-only label. i18n-ийг харгалзахгүй (`flask_babel` гадуур). Шилжүүлэх
газар: `app/constants.py` эсвэл template filter, эсвэл `lazy_gettext()`
ашиглан translation catalog-руу.

---

### L8 · `quality_records.py:393` — Нэг файлд **7 model + ~400 мөр**

`CorrectiveAction`, `ProficiencyTest`, `EnvironmentalLog`, `QCControlChart`,
`CustomerComplaint`, `ImprovementRecord`, `NonConformityRecord` — нийт 7 model.
Бүгд "Quality" ангилалд багтах боловч navigation/maintenance-д хүндрэлтэй.

Файлыг 2-3 хэсэгт хуваах: `quality_records_capa.py`, `quality_records_pt.py`,
`quality_records_complaints.py`. Эсвэл `quality_records/` package болгох.

---

### L9 · `solutions.py:87–92` — `calculate_v_avg` нь mutation өгдөг

```python
def calculate_v_avg(self):
    """Дундаж V тооцоолох."""
    values = [v for v in [self.v1, self.v2, self.v3] if v is not None]
    if values:
        self.v_avg = sum(values) / len(values)
    return self.v_avg
```

"calculate" гэсэн нэр нь pure function-ыг таамаглуулдаг. Гэвч `self.v_avg = ...`
side-effect өгдөг. Зөв нэр нь `compute_and_store_v_avg` эсвэл event listener-аар
auto-compute хийх (before_insert/before_update).

---

## 5. ⚪ Nit / стилийн зөрчил

### N1 · `core.py:11` — `import json` ашиглагдаагүй

```python
import re
import json   # ← unused
```

Dead import.

---

### N2 · `core.py:230`, `equipment.py:14`, бусад — Emoji-уудтай comment-ууд

```python
# 🛑 Mass gate талбарууд
# 🛑 ТОНОГ ТӨХӨӨРӨМЖИЙН УДИРДЛАГА (ISO 17025 - 6.4)
# 🛑 KPI Алдааны шалтгаан
# 🆕 ISO 17025: Chain of Custody & Sample Retention
# ✅ CHECK CONSTRAINT
```

Comment-д emoji зориуд хэрэглэх нь сэдэв тэмдэглэх боломжтой, гэвч production
кодоор audit-аас гарсан "перфект" коэффициент-ийн зөрчилтэй. Хатуу
зөвлөмжгүй — стиль.

---

### N3 · `analysis_audit.py:156, 175–176`; `audit.py:70, 89–90` — Import at file bottom

```python
# (file content)
...

from sqlalchemy import event       # ← bottom of file

event.listen(AnalysisResultLog, "before_update", _block_audit_update)
event.listen(AnalysisResultLog, "before_delete", _block_audit_delete)
```

PEP 8: бүх import top-of-file. Listener бүртгэлийг module init-д орхих хэвээр
зөв, гэвч import нь дээрээ үлдэх ёстой.

---

### N4 · `quality_standards.py:25`, `equipment.py:61`, `chemicals.py:58` — `default=lambda: {}` vs `default=dict`

```python
targets = db.Column(db.JSON, default=lambda: {})
```

`default=dict` нь хоёр тэмдэгт богино, мөн functools зөв. Lambda-аар `{}` ийм
"mutable default" дамжуулах нь шаардлагагүй.

---

### N5 · `analysis.py` болон бусад — `__tablename__` зөрчилтэй convention

| Model | Tablename |
|-------|-----------|
| User | "user" (auto-derived) |
| Sample | "sample" (auto-derived) |
| AnalysisResult | "analysis_result" (explicit) |
| AnalysisType | автомат |
| Equipment | "equipment" (explicit but same as auto) |
| MaintenanceLog | "maintenance_logs" (irregular plural) |
| UsageLog | "usage_logs" (irregular plural) |
| Chemical | "chemical" (explicit) |
| ... | ... |

Зарим model-д `__tablename__` тодорхой бичсэн, заримд хийгээгүй. Plural vs
singular conventions зөрчилтэй (`maintenance_logs` plural, гэвч `equipment`
singular).

Convention сонгож, бүх model-д даган мөрдөх.

---

### N6 · `worksheets.py:62, 144, 146` — `relationship(...)` doc-гүй

```python
sample = db.relationship('Sample')              # type-hint-гүй
analysis_result = db.relationship('AnalysisResult')
reagent_lot = db.relationship('Chemical')
```

Эдгээр нь back_populates биш — нэг талын. Backref дамжуулах эсвэл
`back_populates` тодорхой бичих нь bidirectional model-уудтай тогтвортой.

---

### N7 · `chat.py:18` — `receiver_id` nullable=True (broadcast хэрэглэнэ)

```python
receiver_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True, index=True)
# null = broadcast
```

Comment дотор "null = broadcast". Зөв логик, гэвч `is_broadcast` Boolean column
(line 40) аль хэдийн байна. Хоёр давхар state — `receiver_id IS NULL` болон
`is_broadcast=True` хоёрын аль нь канон вэ? Нэгийг сонгох эсвэл assertion хийх.

---

### N8 · `planning.py:34` — `week` column-д CheckConstraint байхгүй

```python
week = db.Column(db.Integer, nullable=False)  # 1-5
```

`1-5` гэж бичсэн боловч 0 ба 99 шивэх боломжтой.

---

### N9 · `instrument.py` — Equipment-аас `instrument_readings` backref, гэвч `analysis_result_id`-аас reverse-relationship алга

```python
analysis_result_id = db.Column(db.Integer, db.ForeignKey("analysis_result.id", ondelete="SET NULL"), nullable=True)
# ← No relationship('AnalysisResult', backref='instrument_readings')
```

`AnalysisResult.instrument_readings` гэж navigate хийх боломжгүй.

---

### N10 · `bottles.py:5–7` — `from datetime import datetime` нь зөвхөн type hint-д

```python
from datetime import datetime
from typing import Optional
...
def is_active_now(self, ref: Optional[datetime] = None) -> bool:
```

Use TYPE_CHECKING-аар conditional import боломжтой, гэвч жижиг файлд хэт
осторожный болно. Acceptable.

---

### N11 · `core.py:148`, `analysis.py:149, 187`, бусад — `__repr__` нь debug мэдээллийн форматтай

```python
def __repr__(self) -> str:
    return f"<Sample {self.sample_code}>"
```

Бүхэлдээ зөв. Гэвч `AnalysisResult.__repr__` нь зөвхөн id-ийг харуулдаг
(`<AnalysisResult {self.id}>`) — өгөгдөл бага. Debug-д
`analysis_code=...` эсвэл `final_result=...` нэмж буцаах нь тус.

---

## 6. ℹ️ Info / acceptable / сайн pattern

- **I1 · `HashableMixin` + `event.listen`** (`mixins.py`, `analysis_audit.py`,
  `audit.py`, `chemicals.py`, `spare_parts.py`) — ISO 17025-ын audit
  immutability цэвэрхэн шийдсэн. **Сайн pattern.**
- **I2 · `version_id_col` for optimistic locking** (`analysis.py:101–103`) —
  Concurrent edit detection. **Сайн.**
- **I3 · Composite indexes (`H-9`)** — Олон газар сайн ашигласан (Sample,
  AnalysisResult, AnalysisResultLog).
- **I4 · `__table_args__ = (UniqueConstraint, CheckConstraint, ...)`** — Where
  used, well-applied.
- **I5 · `BottleConstant.is_active_now()`** — Effective-date pattern, audit
  trail-ийн оронд immutability. **Хуулбарлах боломжтой үлгэр.**
- **I6 · `app/models/__init__.py` re-exports** — Backward-compat хадгалсан,
  cleanly organized.

---

## 7. Дараагийн алхам

| № | Үйлдэл | Файл | Severity | Тэрчлэн |
|---|--------|------|----------|--------|
| 1 | **H1** — `'hyanalт'` (mixed encoding)-ыг засах + Alembic migration | `core.py:261` | 🟥 High | 1 commit + migration |
| 2 | **H2** — MaintenanceLog/UsageLog/Env/QC/PT-д HashableMixin + event.listen нэмэх | `equipment.py`, `quality_records.py` | 🟥 High | 1 commit |
| 3 | M1 — `check_password` None-guard | `core.py:144` | 🔴 Medium | 1 commit |
| 4 | M2 — FK-уудад ondelete behavior нэмэх | олон файл | 🔴 Medium | 1 commit + migration |
| 5 | M3 — `validate_password` docstring засах | `core.py:107` | 🔴 Medium | 1 commit |
| 6 | M4 — `AUDIT_ACTIONS`, `DEFAULT_ERROR_REASONS`-ыг `app/constants.py`-руу шилжүүлэх | `analysis_audit.py` | 🔴 Medium | 1 commit |
| 7 | M5 — `User.role`-д CheckConstraint + Enum | `core.py:39` | 🔴 Medium | 1 commit + migration |
| 8 | M6 — `analyses_to_perform` JSON column-руу шилжүүлэх (долгийн refactor) | `core.py:218` | 🔴 Medium | Тусгай sprint |
| 9 | M7 — 35+ string column-д CheckConstraint нэмэх | олон файл | 🔴 Medium | 2–3 commit |
| 10 | M8 — `qnet_ar` бодит implement эсвэл устгах | `analysis.py:459` | 🔴 Medium | 1 commit |
| 11 | L1–L9 — Code quality fixes (json import, lazy='dynamic', model-rich logic) | олон файл | 🟡 Low | 2 commit |
| 12 | N1–N11 — Стилийн nit | олон файл | ⚪ Nit | 1 commit |

**Зөвлөмж:** H1 → H2 → M1 → M5 → M4 → M2 (хатуу үе) → бусад.

---

## 8. Энэ audit-ын хамрах хүрээний дүгнэлт

✅ **Бүрэн шалгасан** — 20 model файл бүгд (3 572 мөр).

📊 **Нэмэгдсэн олдвор:** Bootstrap audit-аас илрээгүй real encoding bug
(`'hyanalт'`) **DB CHECK constraint түвшинд** олдсон. Энэ нь "цаашид routes
шалгахад дээжний шинэ client_name шивэх боломжгүй" эсвэл "тестүүд яагаад зөв
ажилладаг" гэх нөхцлийн шалтгаан байж магадгүй.

🔍 **Дараагийн алхам** — Repositories давхарга. 14 файл.
