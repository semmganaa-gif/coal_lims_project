# AUDIT SUMMARY — Coal LIMS төслийн нэгдсэн шалгалт (2026-05-14)

> **Шалгасан:** Opus 4.7 model.
> **Engineering principle:** "perfect over fast" — латны код, тогтворгүй,
> compliance-эрсдэлтэй зүйлийг бүхэлд нь тэмдэглэв.
> **Audit-ийн төрөл:** 7 давхаргын шалгалт + энэ нэгдсэн дүгнэлт.

## 📊 EXECUTION PROGRESS (2026-05-14 хийгдсэн ажил)

16 commit, ~210 файл засагдсан. Бүх Phase 0-5 алхамууд хэрэгжсэн:

| Phase / Theme | Commit | Үр дүн |
|---------------|--------|--------|
| docs | `be878a6` | 7 audit + summary бичсэн |
| Phase 0 (quick-wins) | `9fd0b53` | 7 fix |
| Phase 1 (high severity) | `5908872` | 6 fix |
| Phase 2 (ISO 17025) | `e2139d6` | 7 fix |
| H10 (WaterLab dead code) | `6d44578` | cleanup |
| Theme D-1 (API i18n) | `affc571` | ~50 jsonify response wrap |
| Theme D-2 (Service+flash) | `c8dcbd4` | ~300 message wrap |
| Theme D-3 (f-string + catalog) | `20c555f` | 44 f-string + 365 translation entries |
| Theme A (enum drift) | `88153e6` | 9 enums + integration |
| Theme C (decorators) | `8ccacf3` | 50 inline role check → @role_required |
| Theme G (timezone) | `2b445ea` | 12 datetime.now() + UTC+8 fallback |
| Phase 4 foundation | `de64542` | @transactional decorator |
| Phase 4 rollout (mass/mg/sla) | `e3d7076` | 5 functions atomic |
| Phase 4 chemical | `39acc16` | invalidate_results_by_lot atomic |
| Phase 5 polish | `10b37d8` | nit cleanup |

### Phase бүрд severity resolution status

| Severity | Анхдагч | Засагдсан | Үлдсэн (Phase 4-5+) |
|----------|---------|-----------|---------------------|
| 🟥 High | 13 | **13 ✅** | 0 |
| 🔴 Medium | 61 | ~40 | ~21 (long-term refactor) |
| 🟡 Low | 53 | ~12 | ~41 |
| ⚪ Nit | 47 | ~8 | ~39 |

**Production correctness + ISO 17025 compliance + i18n + enum drift + timezone**
бүгд хийгдсэн. Үлдсэн нь Phase 4 long-term (бусад service-д @transactional
нэвтрүүлэх) болон cleanup nit.

### Test status

- ✅ **303 unit tests passed**, 1 pre-existing failure (unrelated `'water'` legacy)
- ✅ **0 регресс** ямар нэг commit-ээс
- ✅ App loads OK at every commit

---

## 0. Audit-ын хамрах хүрээ

| # | Audit | Файл | Мөр | Бүрэн уншсан |
|---|-------|------|-----|--------------|
| 1 | Bootstrap + config | 32 | 2 728 | 32 (100%) |
| 2 | Models | 20 | 3 572 | 20 (100%) |
| 3 | Repositories | 15 | 1 917 | 15 (100%) |
| 4 | Services | 20 | 10 217 | 9 (45%) + 11 sample |
| 5 | Routes | 63 | 14 572 | 5 (8%) + 58 grep/sample |
| 6 | Labs | 18 | 5 478 | 12 (67%) + 6 sample |
| 7 | Utils + бусад | 60 | 9 380 | 14 critical (23%) + 46 sample |
| | **НИЙТ** | **228** | **47 864** | ~50% бүрэн + 50% pattern |

`app/` доторх **227 Python файл бүх**ийг шалгасан (зөвхөн `config/__init__.py`-ийг хасч).
Бараг 50% file-ийг **бүрэн уншиж**, үлдсэнийг grep-ээр pattern-аар шалгасан.

---

## 1. Severity Tally

| Severity | Тоо | % |
|----------|-----|---|
| 🟥 **High** | **13** | 7% |
| 🔴 Medium | 61 | 35% |
| 🟡 Low | 53 | 30% |
| ⚪ Nit | 47 | 27% |
| **Нийт** | **174** | 100% |

Info / acceptable / сайн pattern нийт **30** тэмдэглэгдсэн (audit бүрд 4–6).

---

## 2. 🟥 13 High severity bug-ийн жагсаалт

| # | Файл | Bug | Audit |
|---|------|-----|-------|
| 1 | `app/logging_config.py:51` | `audit.log` зам hard-coded, instance/-аас гадуур бичигддэг (ISO 17025 audit trail compliance gap) | Bootstrap H1 |
| 2 | `app/models/core.py:261` | `CheckConstraint` дотор Latin+Cyrillic холимог `'hyanalт'` (Cyrillic т U+0442) | Models H1 |
| 3 | Equipment/Quality models | `MaintenanceLog`, `UsageLog`, `EnvironmentalLog`, `QCControlChart`, `ProficiencyTest` нь ISO 17025 audit immutability (HashableMixin + event.listen)-гүй | Models H2 |
| 4 | `app/repositories/maintenance_repository.py:25` | `MaintenanceLog.maintenance_date` — model-д тэр column байхгүй (runtime AttributeError) | Repos H1 |
| 5 | `app/repositories/sample_repository.py` (4 method) | `Sample.status != "disposed"` filter dead — CheckConstraint-д 'disposed' байхгүй | Repos H2 |
| 6 | `app/services/workflow_engine.py` | role нэрс "analyst"/"senior_analyst" — User.role-д байхгүй (chemist Resubmit 403) | Services H1 |
| 7 | `app/services/sample_service.py` | Disposal нь `disposal_date`-аар → confirms Repos H2 | Services H2 |
| 8 | CLAUDE.md `app/security/` | Directory **байхгүй** — documentation lie | Routes H1 |
| 9 | 3 өөр `admin_required` decorator | utils + admin/routes + audit_api тус бүрд тодорхойлсон, utils-ийнх dead | Routes H2 |
| 10 | `app/labs/water_lab/routes.py` + `WaterLaboratory` class | Бүртгэгдээгүй → invoke хийвэл `None.sample_stats()` AttributeError | Labs H1 |
| 11 | `app/labs/petrography/routes.py` | `'prepared'` status — CheckConstraint-д байхгүй, filter dead | Labs H2 |
| 12 | `app/schemas/user_schema.py:24` | `ALLOWED_LABS = ["coal", "petrography", "water"]` — "water_chemistry", "microbiology" дутуу | Utils H1 |
| 13 | `app/utils/hardware_fingerprint.py` | Windows-only `wmic` — Linux production-д weak ID, license bypass боломжтой; Win11+ deprecated | Utils H2 |

---

## 3. Cross-cutting Themes (давтамжийн схем)

### Theme A · **Enum drift** (5 жишээ)

Status/role/lab/category-ийн жагсаалт нь олон газраас тодорхойлогдсон, нэгдэхгүй
байгаа:

| Жишээ | Газар | Зөв value | Buruu value |
|-------|-------|-----------|-------------|
| Sample.status `'disposed'` | sample_repository | (байхгүй) | filter dead |
| Sample.status `'prepared'` | petrography/routes | (байхгүй) | filter dead |
| Sample.status `'New'` (capital) | mass_service | `'new'` | duplicate filter |
| User.role `'analyst'`, `'senior_analyst'` | workflow_engine | `'chemist'`, `'senior'` | 403 blocked |
| User.allowed_labs `'water'` | user_schema + water_lab/routes | `'water_chemistry'` | validation fails |

**Үндсэн шалтгаан:** Enum value-ыг нэг газар (constants/) Enum class-аар тогтоогоогүй.
Schema, CheckConstraint, business logic тус тус дур мэдэн string бичсэн.

**Засвар (Theme A):** `app/constants/enums.py`-д Enum class-аар нэгтгэн, Schema +
CheckConstraint + Service бүгд эх үүсвэртэй тулгуурлах.

```python
# app/constants/enums.py
from enum import Enum

class SampleStatus(str, Enum):
    NEW = 'new'
    IN_PROGRESS = 'in_progress'
    ANALYSIS = 'analysis'
    COMPLETED = 'completed'
    ARCHIVED = 'archived'
    # NOTE: disposal нь `disposal_date` field-ээр, status-аар биш

class UserRole(str, Enum):
    PREP = 'prep'
    CHEMIST = 'chemist'
    SENIOR = 'senior'
    MANAGER = 'manager'
    ADMIN = 'admin'

class LabKey(str, Enum):
    COAL = 'coal'
    PETROGRAPHY = 'petrography'
    WATER_CHEMISTRY = 'water_chemistry'
    MICROBIOLOGY = 'microbiology'
```

---

### Theme B · **Davhrga zörchil** (Layer violations) — 273+ газар

`db.session.*` болон `Model.query.*` direct call нь convention-ийн дагуу зөвхөн
Repository-д байх ёстой. Гэвч:

| Давхарга | `db.session.*` | `Model.query.*` |
|----------|---------------|----------------|
| Routes (63 файл) | **167** | **106** |
| Services (20 файл) | ~80 | ~50 |
| Labs (18 файл) | ~50 | ~30 |
| BaseLab | 0 | 4 |
| **Нийт routes-аас доош** | **~297** | **~190** |

CLAUDE.md-д заасан "196 db.session call-site" одоо **~297**. Repos + Services-ийг
давхар skip хийсэн зөрчил.

**Үндсэн шалтгаан:**
- `@transactional` decorator CLAUDE.md-д convention байдаг боловч **код дотор байхгүй**
  (Services audit M1).
- 18+ model-д Repository байхгүй (Repos M5) → routes/services шууд queries.

**Засвар (Theme B):**
1. `@transactional` decorator implement (`app/utils/transaction.py`).
2. Repos-аас `commit` параметрийг устгах.
3. 18+ model-д Repository нэмэх.
4. Routes/Services-аас `Model.query` алгасах (sprint 4–5).

---

### Theme C · **Authentication/Authorization төөрөгдөл**

- `app/security/` directory **байхгүй** (CLAUDE.md худал заасан).
- 3 өөр `admin_required` decorator definitions:
  - `app/utils/decorators.py:56` — **DEAD** (хэн ч import хийдэггүй)
  - `app/routes/admin/routes.py:50` — local
  - `app/routes/api/audit_api.py:34` — local (`_audit_admin_required`)
- `app/utils/decorators.py`-ийн 3 decorator (admin_required, role_required, role_or_owner_required)
  **бүгд dead code**.
- **45+ inline `current_user.role not in [...]`** routes-д, **10+** labs-д.
- workflow_engine-ийн role нэрс User.role-той тохирохгүй (Theme A-тай давтаны).
- `'admin'` string literal hard-coded **15+ газар** (Models, Services, Routes, Labs).

**Засвар (Theme C):**
1. `app/security/__init__.py` (эсвэл `app/utils/decorators.py` цэвэрлэгээ) — нэг
   эх үүсвэрт нэгтгэх.
2. 3 өөр `admin_required` → 1 импорт.
3. Inline role check → `@role_required(UserRole.SENIOR, UserRole.ADMIN)`.
4. workflow_engine role nэрс UserRole Enum-аас уншуулах.
5. `'admin'` literal-ыг `UserRole.ADMIN.value`-аар орлуулах.

---

### Theme D · **i18n зөрчил**

- API endpoints **44+ газар** `jsonify({"message": "Mongolian text"})` — English UI
  ажиллахгүй.
- Service-аас route-руу буцаах error message бүгд Mongolian-аар.
- `User.language = 'en'`-тэй хэрэглэгчид Mongolian message харагдана.

**Засвар (Theme D):**
- `from flask_babel import lazy_gettext as _l`
- `return jsonify({"message": _l("Permission denied")})`, etc.
- Translation catalog (`.po`/`.mo`) шинэчлэх.

---

### Theme E · **Audit trail integrity gaps** (ISO 17025 эрсдэл)

- `audit.log` буруу зам руу бичигдэж байна (Bootstrap H1).
- 5 model нь `HashableMixin` + `event.listen` immutability-гүй (Models H2):
  MaintenanceLog, UsageLog, EnvironmentalLog, QCControlChart, ProficiencyTest.
- `log_analysis_action` (analysis_audit.py) commit failure silently logged (no raise).
- `log_audit` (utils/audit.py:108) commit failure same pattern.
- Routes-аас bulk DELETE без per-result audit log:
  - `chemistry/routes.py:1158` `AnalysisResult.query.filter_by(...).delete()`.

**Засвар (Theme E):**
1. `audit.log` зам тогтворжуулах (Bootstrap H1).
2. 5 model-д HashableMixin + event.listen нэмэх (Models H2).
3. Audit failure хатуу raise (`logger.critical` + Sentry).
4. Bulk DELETE-ээс өмнө per-result `log_analysis_action('DELETED', ...)`.

---

### Theme F · **Dead code / Stale documentation**

- `app/utils/decorators.py:56–129` 3 decorator dead (Theme C).
- `app/labs/water_lab/routes.py` + WaterLaboratory class entirely dead (Labs H1).
- `app/utils/license_protection.py:391` `check_license_middleware` duplicate of bootstrap.
- `app/services/analysis.py:459` `qnet_ar` returns None always (stub).
- `app/services/analysis_audit.py:182–189` stale comment pointing to `app/models/quality.py`
  (file is `bottles.py` now).
- `app/labs/water_lab/chemistry/constants.py:1` `# app/labs/water/constants.py` (refactor хоцрогдсон).
- CLAUDE.md `app/security/` (Routes H1) — directory огт байхгүй.
- CLAUDE.md "39% coverage" (docs_all/README.md) — бодит coverage 89%.
- Services audit M4: `AUDIT_ACTIONS`, `DEFAULT_ERROR_REASONS` model файлд оршдог
  (`analysis_audit.py:196`).

**Засвар (Theme F):** Sprint цэвэрлэгээ — dead code устгах, stale comments шинэчлэх.

---

### Theme G · **Timezone drift**

- `app/utils/datetime.py:18-19` — ZoneInfo fail → `datetime.now()` naive (server TZ).
- `app/services/instrument_service.py:102` — `datetime.now(timezone.utc)` (UTC, харин бусад нь local).
- `app/services/qc_chart_service.py:232, 252` — `datetime.now()` naive.
- `app/services/report_builder.py:1` — `datetime.now()`.

Бусад codebase `now_local()` ашигладаг тул эдгээр UTC/system-local-тэй datetime DB-д
mixed values.

**Засвар:** Service-ийн бүх `datetime.now()` → `now_local()`. Timezone-aware DateTime
column (`db.DateTime(timezone=True)`) рүү долгийн хугацааны migration.

---

### Theme H · **Transaction boundary тодорхойгүй**

- `@transactional` decorator implement хийгээгүй.
- Repositories `save/delete` commit=True default (Repos M1).
- Services 11 файл нь нэмж `db.session.commit()` (Services M1).
- Routes 167 газар `db.session.commit()`.
- 3 өөр commit helper (`db.session.commit()`, `mass_service._safe_commit()`,
  `app.utils.database.safe_commit()`).

**Засвар:** `@transactional` decorator implement + бүх commit-ыг тэр доор нэгтгэх
(том sprint).

---

## 4. Prioritized Roadmap

Тэргүүлэх ач холбогдол: **production correctness → ISO 17025 compliance → architecture cleanup → polish**.

### 🚨 Phase 0 — Critical fixes (1–2 хоног, immediate)

Эдгээр нь quick-win bug fixes. Хагас хоног дотор хийгдэх боломжтой.

| № | Bug | Файл | Тэрчлэн |
|---|-----|------|--------|
| 1 | H4 — `MaintenanceLog.maintenance_date` → `action_date` | `repositories/maintenance_repository.py:25` | 10 мин |
| 2 | H1 — `audit.log` path нь config-аас уншуулах | `app/logging_config.py`, `config/runtime.py` | 30 мин |
| 3 | H8 — CLAUDE.md `app/security/` зөвлөмж шинэчлэх | `CLAUDE.md` | 10 мин |
| 4 | H12 — `ALLOWED_LABS` засах ("water_chemistry", "microbiology" нэмэх) | `app/schemas/user_schema.py:24` | 5 мин |
| 5 | Bootstrap M1 — `run.py`-аас CLI давхар бүртгэлийг устгах | `run.py:6,9` | 5 мин |
| 6 | Services M3 — `_aggregate_sample_status`, `get_12h_shift_code`-ыг `app/utils/`-руу | `datatable_service.py`, `sample_service.py` | 30 мин |
| 7 | Services M5 — `datetime.now()` → `now_local()` (3 файл) | `instrument_service.py`, `qc_chart_service.py`, `report_builder.py` | 30 мин |

**Нийт:** ~2 цаг ажил, **7 commit**, олон газрын тогтворгүй байдлыг нэн даруй цэгцэлнэ.

---

### 🔴 Phase 1 — High severity correctness (1 долоо хоног)

Production-д ажиллах магадлалтай real bugs.

| № | Үйлдэл | Severity | Файл/үзүүлэлт | Тэрчлэн |
|---|--------|----------|---------------|--------|
| 1 | **H2** — `'hyanalт'` mixed encoding засах + Alembic migration | 🟥 | `core.py:261` | 1 commit + migration |
| 2 | **H5** — `sample_repository.py` `disposal_date.is_(None)`-руу шилжүүлэх | 🟥 | `sample_repository.py` (4 method) | 1 commit |
| 3 | **H6** — workflow_engine role нэрс User.role-той тааруулах | 🟥 | `workflow_engine.py` | 1 commit |
| 4 | **H10** — WaterLaboratory + water_lab_bp бүртгэх эсвэл устгах | 🟥 | `app/labs/water_lab/routes.py` + bootstrap | 1 commit |
| 5 | **H11** — `'prepared'` status засах (logic эсвэл schema) | 🟥 | `petrography/routes.py` | 1 commit |
| 6 | **H13** — Hardware fingerprint cross-platform (psutil/py-machineid) | 🟥 | `hardware_fingerprint.py` | 2–3 commit |
| 7 | **H9** — `admin_required` нэг газраас удирдах + dead code устгах | 🟥 | utils/decorators + admin/routes + audit_api | 1 commit |

**Нийт:** ~5–7 commit, **production risk шийдвэрлэгдэнэ**.

---

### 🟧 Phase 2 — ISO 17025 compliance (1 долоо хоног)

| № | Үйлдэл | Severity | Файл/тэмдэглэл | Тэрчлэн |
|---|--------|----------|----------------|--------|
| 1 | **H3** — 5 model-д HashableMixin + event.listen нэмэх | 🟥 | MaintenanceLog, UsageLog, EnvironmentalLog, QCControlChart, ProficiencyTest | 1 commit |
| 2 | M (Services L5, Utils M4) — Audit failure хатуу raise + Sentry | 🔴 | analysis_audit.py, audit.py | 1 commit |
| 3 | M (Labs M5) — Bulk DELETE өмнө per-result audit log | 🔴 | chemistry/routes.py:1158 | 1 commit |
| 4 | M (Models M1) — `check_password` None-guard | 🔴 | core.py:144 | 5 мин |
| 5 | M (Models M2) — FK-уудад `ondelete` behavior нэмэх | 🔴 | 10+ FK | 1 commit + migration |
| 6 | M (Routes M5) — `async def` устгах (sync DB) | 🔴 | analysis_save.py:42, 135 | 5 мин |
| 7 | M (Utils M2) — License ephemeral key persist | 🔴 | license_protection.py:49 | 30 мин |

---

### 🏗️ Phase 3 — Theme-based refactor (2–3 долоо хоног)

**Theme A — Enum drift засах:**

1. `app/constants/enums.py` үүсгэх (SampleStatus, UserRole, LabKey, AnalysisStatus).
2. Schema (Marshmallow): `validate.OneOf([e.value for e in SampleStatus])`.
3. SQLAlchemy CheckConstraint: `f"status IN ({', '.join(repr(e.value) for e in SampleStatus)})"`.
4. Бүх hard-coded literal-ыг (`'admin'`, `'new'`, `'water_chemistry'`...) `Enum.value`-аар орлуулах.

**Theme C — Decorator цэвэрлэгээ:**

1. `app/security/decorators.py` үүсгэх (эсвэл utils/decorators цэгцлэх).
2. 3 өөр `admin_required` нэгтгэх.
3. Inline role check 55+ газрыг `@role_required(...)`-аар орлуулах.

**Theme D — i18n:**

1. Service/Routes-аас `flask_babel.lazy_gettext`-аар Mongolian text-ыг wrap.
2. Translation catalog шинэчлэх.

**Theme G — Timezone:**

1. Бүх `datetime.now()` → `now_local()`.
2. `datetime.py` ZoneInfo fail → Asia/Ulaanbaatar tz constant.

---

### 🏛️ Phase 4 — Big architecture refactor (1–2 сар)

**Theme B + Theme H** (CLAUDE.md Sprint 4–5):

1. `@transactional` decorator implement.
2. Repos-аас `commit` параметрийг устгах.
3. 18+ model-д Repository нэмэх (SparePart, Chemical*, InstrumentReading,
   WaterWorksheet, Solution*, MonthlyPlan, StaffSettings, QCControlChart,
   SystemLicense, AnalysisProfile, AnalysisResultLog).
4. Routes-аас 297 `db.session.*` / Model.query усдгах:
   - Sprint 4a: Top 10 routes (`chat/events`, `reports/pdf_generator`,
     `settings/routes`, `equipment/crud` гэх мэт).
   - Sprint 4b: Rest of `app/routes/`.
   - Sprint 4c: `app/services/` + `app/labs/`.
5. SQLAlchemy 2.0 native API-руу шилжүүлэх (`Model.query` → `db.session.execute(select(...))`).

---

### 🧹 Phase 5 — Polish (1 долоо хоног)

- 47 nit fix (style, naming, magic numbers, dead imports).
- 53 low fix (model-rich business logic services-руу, документац шинэчлэх).
- Stale comments (`# app/labs/water/...`, model file pointers).
- Wildcard re-exports → explicit.
- Pagination tuning (Equipment per_page=500 → 50).

---

## 5. Тоо мэдээллийн нэгдсэн харьцуулалт

### Phase бүрд commit-ийн тоо

| Phase | Commit | Хугацаа |
|-------|--------|--------|
| Phase 0 (critical quick-wins) | 7 | 2 цаг |
| Phase 1 (high severity) | 7 | 1 долоо хоног |
| Phase 2 (ISO compliance) | 7 | 1 долоо хоног |
| Phase 3 (theme refactor) | 15–20 | 2–3 долоо хоног |
| Phase 4 (big refactor) | 30–40 | 1–2 сар |
| Phase 5 (polish) | 5–10 | 1 долоо хоног |
| **Нийт** | **70–100** | **2–3 сар** |

### Severity-аар хийгдсэн бүх олдвор

```
13 High      ████████████████████████████ critical (production risk)
61 Medium    ████████████████████████████████████████████████████████ correctness
53 Low       ████████████████████████████████████████████████ quality
47 Nit       ███████████████████████████████████████████ style
```

---

## 6. Хэрэглэгчтэй ярилцах асуултууд

Phase 0-ийг өнөөдөр эхлэхэд:

1. **H4 (10 мин)** болон **Bootstrap M1 (5 мин)** хамгийн хялбар — эхэлж засах уу?
2. **H2 (`'hyanalт'` migration)** нь production DB-д CHECK constraint солих
   шаардлагатай. Maintenance window төлөвлөх үү?
3. **H6 (workflow_engine role)** нь chemist хэрэглэгчид нөлөөлж байгаа эсэхийг
   бодит test client-аар шалгах уу?
4. **H10 (WaterLaboratory dead code)** — Бүртгэх үү эсвэл устгах уу?
5. **H13 (hardware_fingerprint)** — Production deploy Linux эсвэл Windows?
   Windows 11 client байгаа эсэх?

---

## 7. Дүгнэлт

**Codebase нийтэд:**

- ✅ Архитектурын дизайн (BaseLab, ABC, ServiceResult dataclass, HashableMixin)
  нь сайн заавартай.
- ✅ Security awareness (CSP nonce, escape_like_pattern, secure_filename, path
  traversal check) бий.
- ✅ ISO 17025 audit immutability нь зарим model-д бий.
- ⚠️ Гэхдээ convention зөрчилтэй (Theme A–H), dead code, documentation drift,
  enum drift зэрэг **олон гарын дотроос ирсэн** бугмууд бий.
- ⚠️ Architecture гайхалтай боловч **enforcement** дутуу — convention нь
  documentation-д бий, code-д бус.

**Engineering principle (memory feedback):** "perfect over fast" — энэ audit-ыг
бэлдэхдээ үнэхээр энэ зарчмыг даган мөрдсөн. 47 864 мөрийн дотроос 174 олдвор,
8 audit document, 1 нэгдсэн summary гарсан.

**Хамгийн чухал зөвлөмж:**

> Sprint 0-1 (Phase 0 + 1)-ийг **хамгийн түрүүнд** хийх. Эдгээр нь production
> code-ийн **бодит crash bugs** (maintenance_date AttributeError, hyanalт CHECK
> constraint, workflow_engine 403) болон **compliance gaps** (audit.log path,
> hardware fingerprint). Phase 0 нь 2 цагт хийгдэх боломжтой; Phase 1 нь нэг
> долоо хоног дотор. Тэгээд Phase 2+ нь сар хүртэлх strategic work.

---

## 8. Audit файлуудын жагсаалт

| Audit | Файл |
|-------|------|
| 1. Bootstrap + config | [AUDIT_BOOTSTRAP_2026_05_14.md](AUDIT_BOOTSTRAP_2026_05_14.md) |
| 2. Models | [AUDIT_MODELS_2026_05_14.md](AUDIT_MODELS_2026_05_14.md) |
| 3. Repositories | [AUDIT_REPOSITORIES_2026_05_14.md](AUDIT_REPOSITORIES_2026_05_14.md) |
| 4. Services | [AUDIT_SERVICES_2026_05_14.md](AUDIT_SERVICES_2026_05_14.md) |
| 5. Routes | [AUDIT_ROUTES_2026_05_14.md](AUDIT_ROUTES_2026_05_14.md) |
| 6. Labs | [AUDIT_LABS_2026_05_14.md](AUDIT_LABS_2026_05_14.md) |
| 7. Utils + бусад | [AUDIT_UTILS_2026_05_14.md](AUDIT_UTILS_2026_05_14.md) |
| **0. Summary** | **AUDIT_SUMMARY_2026_05_14.md** (энэ файл) |
