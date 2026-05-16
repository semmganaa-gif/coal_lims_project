# LIMS - ROLE PERMISSIONS LOG
# Сүүлд шинэчилсэн: 2026-05-16
# ============================================================================

> Энэхүү баримт нь Coal LIMS төслийн **role-based access control (RBAC)**
> policy-ийн нэгдсэн эх сурвалж. Шинэ route нэмэх эсвэл эрхийн дүрэм засах
> үед энэ файлыг тулгуур болгоно.
>
> **Cross-reference:** `docs/dev-logs/ROLE_PERMISSIONS_MATRIX_2026_05_16.md`
> — кодоос шууд scan хийсэн 120+ үйлдлийн нарийвчилсан матриц.

---

## 1. Системийн ROLE-УУД (5 төрөл)

| Role | Код | Монгол нэр | Тайлбар |
|------|-----|-----------|---------|
| Sample Preparation | `prep` | Дээж бэлтгэгч | Дээж бүртгэх, бэлтгэх (status='new' үед засна) |
| Chemist | `chemist` | Химич | Шинжилгээ хийх, өөрийн pending үр дүн submit |
| Senior Chemist | `senior` | Ахлах химич | Үр дүн approve/reject, оперaциональ удирдлага |
| Manager | `manager` | Менежер | **VIEW ONLY** — observer/auditor |
| Administrator | `admin` | Админ | Системийн бүх эрх |

**Source of truth:** `app/constants/enums.py:UserRole`

```python
class UserRole(_StrEnum):
    PREP = "prep"
    CHEMIST = "chemist"
    SENIOR = "senior"
    MANAGER = "manager"
    ADMIN = "admin"
```

---

## 2. POLICY (2026-05-16 хэрэглэгч баталсан)

### admin
**Бүх эрхтэй.** Хязгаар үгүй.

### senior
- Operational бүх үйлдэл (sample, analysis review, equipment, chemical, quality, standards, reports, settings) ✅
- **Системийн тохиргоо, хэрэглэгч удирдлага, workflow config, лиценз** ❌ (admin only)
- **Аудит лог:** view + export ✅; устгах/purge ❌ (append-only enforced)

### manager (VIEW-ONLY)
- Бүх модулийг **харах боломжтой** ✅
- **Ямар ч бичих/засах/устгах үйлдэл** ❌
- 2026-05-16-ны дараа quality_helpers + equipment + chemicals + reports + spare_parts + control_charts + sla_api + tools + instrument + report_builder декораторуудаас хасагдсан.

### chemist
- View ✅
- **Өөрийн шинжилгээний үр дүн submit/edit** ✅ (pending_review status үед)
- Sample register ❌
- Sample edit ❌
- Бусдын record устгах/засах ❌

### prep
- View ✅
- Sample register ✅
- Sample edit ✅ — **ЗӨВХӨН `status='new'`** үед (шинжилгээ эхэлсэн бол засах боломжгүй)
- Sample delete ❌

---

## 3. DECORATORS

`app/utils/decorators.py`:

| Decorator | Хамрах роль | API response | Тэмдэглэл |
|-----------|------------|--------------|----------|
| `@admin_required` | admin | JSON 403 / UI flash+redirect | |
| `@senior_or_admin_required` | senior, admin | JSON 403 / UI flash+redirect | |
| `@role_required(*roles)` | varargs | JSON 403 / UI flash+redirect | UserRole.X.value заавал |
| `@analysis_role_required(roles=None)` | default: бүх 5 role | JSON 403 / UI flash+redirect | `UserRole.values()` default |
| `@lab_required(lab_key)` | allowed_labs JSON | Flash+redirect | Admin bypass |

`app/utils/quality_helpers.py`:

| Function | Allow | Hard-coded? |
|----------|-------|-------------|
| `can_edit_quality()` | senior, admin | ✅ UserRole enum (manager хасагдсан 2026-05-16) |
| `@require_quality_edit(endpoint)` | senior, admin | (uses can_edit_quality) |

`app/routes/settings/routes.py`:

| Helper | Allow | Type |
|--------|-------|------|
| `_is_admin()` | admin | UserRole.ADMIN.value |
| `_is_senior_or_admin()` | senior, admin | UserRole enum |

---

## 4. RECENT CHANGES (2026-05-15 → 2026-05-16)

### `ef2d63c` — Ahlah dashboard audit
- senior.py inline `("senior","admin")` → `@analysis_role_required(_SENIOR_ROLES)`
- `_apply_status_fields`: error_reason (KPI tag) approve/pending үед хадгална
- Workflow engine `except Exception: pass` → specific exceptions + logger.warning
- `"preparer"` typo → `UserRole.PREP.value`

### `57db49d` — Manager view-only + audit log senior view (2026-05-16 policy)
- 15 файл, 30+ декоратораас `MANAGER` хасах
- audit_api: `@admin_required` → `@senior_or_admin_required` (5 route)
- spare_parts category_list → @login_required (view бүгд)
- routes/main/index.py:122 — `["prep","admin"]` literal → UserRole enum
- Quality module manager хориглож (can_edit_quality) senior+admin

### Дараах commit (2026-05-16 эцэст)
- workflow_api.py: ghost roles "senior_analyst", "analyst" устгасан
- mass_service.py: `'admin'` fallback → `'' (хоосон)`; bare `except Exception` → specific
- decorators.py: `analysis_role_required` default `UserRole.values()`
- settings/routes.py: `_is_admin()`/`_is_senior_or_admin()` UserRole enum

---

## 5. ЭРХИЙН МАТРИЦ (cheat sheet)

> Бүрэн матриц: `docs/dev-logs/ROLE_PERMISSIONS_MATRIX_2026_05_16.md` (120+ үйлдэл)

### 5.1 Үндсэн функцууд

| Функц | prep | chemist | senior | manager | admin |
|-------|------|---------|--------|---------|-------|
| Дээж бүртгэх | ✅ | ❌ | ❌ | ❌ | ✅ |
| Дээж засах (status=new) | ✅ | ❌ | ✅ | ❌ | ✅ |
| Дээж засах (бусад status) | ❌ | ❌ | ✅ | ❌ | ✅ |
| Дээж устгах | ❌ | ❌ | ✅ | ❌ | ✅ |
| Шинжилгээний үр дүн submit | ❌ | ✅ | ✅ | ❌ | ✅ |
| Approve/Reject result | ❌ | ❌ | ✅ | ❌ | ✅ |

### 5.2 Чанарын удирдлага (Quality)

| Функц | prep | chemist | senior | manager | admin |
|-------|------|---------|--------|---------|-------|
| View (CAPA, complaints, PT, environmental, control charts) | ✅ | ✅ | ✅ | ✅ | ✅ |
| Create/Edit | ❌ | ❌ | ✅ | ❌ | ✅ |
| Approve | ❌ | ❌ | ✅ | ❌ | ✅ |

### 5.3 Тоног төхөөрөмж

| Функц | prep | chemist | senior | manager | admin |
|-------|------|---------|--------|---------|-------|
| View | ✅ | ✅ | ✅ | ✅ | ✅ |
| Add/Edit/Calibrate/Maintenance | ❌ | ❌ | ✅ | ❌ | ✅ |
| Retire/Delete | ❌ | ❌ | ✅ | ❌ | ✅ |

### 5.4 Урвалж/Хими

| Функц | prep | chemist | senior | manager | admin |
|-------|------|---------|--------|---------|-------|
| View | ✅ | ✅ | ✅ | ✅ | ✅ |
| Add/Edit/Consume | ❌ | ✅ | ✅ | ❌ | ✅ |
| Dispose/Waste approve | ❌ | ❌ | ✅ | ❌ | ✅ |

### 5.5 Сэлбэг (Spare Parts)

| Функц | prep | chemist | senior | manager | admin |
|-------|------|---------|--------|---------|-------|
| Categories view | ✅ | ✅ | ✅ | ✅ | ✅ |
| Categories add/edit | ❌ | ❌ | ✅ | ❌ | ✅ |
| Categories delete | ❌ | ❌ | ❌ | ❌ | ✅ |
| Parts add/edit/receive | ❌ | ✅ | ✅ | ❌ | ✅ |
| Parts dispose | ❌ | ❌ | ✅ | ❌ | ✅ |

### 5.6 Стандарт (CM/GBW)

| Функц | prep | chemist | senior | manager | admin |
|-------|------|---------|--------|---------|-------|
| View | ❌ | ❌ | ✅ | ❌ | ✅ |
| Add/Edit/Activate/Delete | ❌ | ❌ | ✅ | ❌ | ✅ |

> **Note:** Стандарт нэмэх/засах нь chemist/manager/prep-д ил үзэгдэхгүй (admin/senior only). View ч admin/senior only.

### 5.7 Системийн удирдлага

| Функц | prep | chemist | senior | manager | admin |
|-------|------|---------|--------|---------|-------|
| Хэрэглэгч CRUD | ❌ | ❌ | ❌ | ❌ | ✅ |
| Workflow config | ❌ | ❌ | ❌ | ❌ | ✅ |
| CSV historical import | ❌ | ❌ | ❌ | ❌ | ✅ |
| Лиценз info/hwid | ❌ | ❌ | ❌ | ❌ | ✅ |
| Audit log purge | ❌ | ❌ | ❌ | ❌ | ✅ |
| Bottle constants (settings) | ❌ | ❌ | ✅ | ❌ | ✅ |
| Repeatability limits | ❌ | ❌ | ✅ | ❌ | ✅ |
| Error reason taxonomy | ❌ | ❌ | ❌ | ❌ | ✅ |
| Analysis types config | ❌ | ❌ | ✅ | ❌ | ✅ |

### 5.8 Тайлан ба Export

| Функц | prep | chemist | senior | manager | admin |
|-------|------|---------|--------|---------|-------|
| View PDF report | ✅ | ✅ | ✅ | ✅ | ✅ |
| Excel/CSV export | ✅ | ✅ | ✅ | ✅ | ✅ |
| Send email report | ❌ | ❌ | ✅ | ❌ | ✅ |
| Approve report | ❌ | ❌ | ✅ | ❌ | ✅ |
| Report template save | ❌ | ❌ | ❌ | ❌ | ✅ |
| SLA config save | ❌ | ❌ | ✅ | ❌ | ✅ |

### 5.9 Audit log

| Функц | prep | chemist | senior | manager | admin |
|-------|------|---------|--------|---------|-------|
| View audit hub | ❌ | ❌ | ✅ | ❌ | ✅ |
| Search audit log | ❌ | ❌ | ✅ | ❌ | ✅ |
| Export audit (CSV) | ❌ | ❌ | ✅ | ❌ | ✅ |
| Modify/Delete | ❌ | ❌ | ❌ | ❌ | ❌ (event listener block) |

### 5.10 Лабораторийн хандалт (allowed_labs)

| Эрх | prep | chemist | senior | manager | admin |
|-----|------|---------|--------|---------|-------|
| Өөрийн лабын дээж | ✅ | ✅ | ✅ | ✅ | ✅ |
| Бусад лабын дээж | ❌ | ❌ | ❌ | ❌ | ✅ |
| `allowed_labs` тохируулах | ❌ | ❌ | ❌ | ❌ | ✅ |

**Decorator:** `@lab_required('lab_key')` — route бүрт лаб эрх шалгана.
**Admin bypass:** Admin бүх лабд автоматаар хандах эрхтэй.

**Lab keys:** `coal`, `petrography`, `water_chemistry`, `microbiology`

---

## 6. NAVIGATION MENU ЭРХҮҮД (templates)

> **Анхаар:** Template-аас одоо `current_user.role` literal-аар шалгалт хийдэг (14+ газар). Manager view-only refactor-ийн дараа эдгээр template-аас manager-ыг write-action товчнуудаас хорих засвар шаардлагатай.
> **Үлдсэн ажил:** User model-д `is_admin`, `is_senior`, `can_edit_quality` гэх мэт boolean property нэмж template-уудыг refactor хийх.

### 6.1 Бүгдэд харагдана
- Нүүр
- Шинжилгээ
- Тоног төхөөрөмж
- Чанар (бүх submenu)
- Стандарт (admin/senior only — view ч хязгаарлагдсан)
- Тайлан (Consumption, Monthly Plan, Статистик, Дээж хадгалалт)

### 6.2 Senior, Manager, Admin
- Нэгтгэл (sample summary)
- Удирдлага (admin menu)

### 6.3 Senior, Admin
- Ахлахын хяналт (`ahlah_dashboard`)
- Цагийн тайлан илгээх товч
- Audit menu

### 6.4 Admin only
- Хэрэглэгч удирдлага
- Workflow config
- Settings → Error reason
- License management

---

## 7. WORKFLOW ENGINE

`app/services/workflow_engine.py:DEFAULT_WORKFLOWS` — sample, analysis_result workflow-уудын transition-уудад role check:
- `["senior", "admin", "manager"]` — гэхдээ manager view-only policy-ын дараа transition хэрэгжүүлэхгүй (allow рулийн effective хэрэглээг senior+admin ширхэглэх төлөв)
- Admin custom workflow config үед `UserRole.values()` (5 role) дотроос л сонгох — workflow_api.py:VALID_ROLES enforce хийнэ.

---

## 8. DATABASE / MIGRATIONS

### Role нэрсийн өөрчлөлтийн түүх
- `b3ed3b177364`: ahlah → senior
- `c3bc04cf9877`: himich → chemist, beltgegch → prep

### User устгах FK behavior
- Audit FK-ууд: `ondelete='SET NULL'` (audit_log, analysis_result_log) + ORM `passive_deletes=True`
- Operational FK-ууд: ondelete=SET NULL (chemicals, equipment, etc.) — `768ae2c`, `1161f61`
- Chat/worksheets/settings: CASCADE / SET NULL — `957db5e` (2026-05-16)

---

## 9. ҮЛДСЭН АЖИЛ (code quality)

| # | Asуудал | Файл |
|---|---------|------|
| 5 | Template `current_user.role == 'admin'` literals (14+ газар) — User model-д `is_admin` property нэмж refactor хийх | `base.html`, `equipment/list.html`, `sample_summary.html`, `workflow_admin.html`, etc. |

Бусад code-quality items 2026-05-16-нд хаагдсан:
- ✅ #1 Ghost roles `workflow_api.py`
- ✅ #2 mass_service.py:116 security fallback
- ✅ #3 decorators.py default literal
- ✅ #4 settings/routes.py helper literals

---

## 10. FORMS

`app/forms.py` — UserManagementForm role choices:

```python
role = SelectField(
    "Эрхийн түвшин",
    choices=[
        ("prep", "Дээж бэлтгэгч (Sample Preparation)"),
        ("chemist", "Химич (Chemist)"),
        ("senior", "Ахлах химич (Senior Chemist)"),
        ("manager", "Менежер (Manager — view only)"),
        ("admin", "Админ"),
    ],
)
```

---

## 11. MODELS

`app/models/core.py` — User:

```python
role = db.Column(db.String(64), index=True, default="prep")
# Боломжит утгууд: UserRole.values() = ['prep', 'chemist', 'senior', 'manager', 'admin']
```

`app/models/analysis.py` — AnalysisType:

```python
required_role = db.Column(db.String(64), default="chemist")
# FM, Solid → prep
# Бусад → chemist
```

---

## ТҮҮХ

| Огноо | Өөрчлөлт |
|-------|----------|
| 2025-12-04 | Анхны audit — ahlah/himich/beltgegch → senior/chemist/prep rename |
| 2025-12-04 | manager role нэмэгдсэн, allowed_labs JSON анх анх |
| 2026-02-03 | allowed_labs 4 лаб дэмжих (coal/petro/water/micro) |
| 2026-05-15 | Theme C decorator cleanup — inline role check → @role_required (12 газар) |
| 2026-05-16 AM | ahlah dashboard audit — preparer typo, error_reason KPI loss, role pattern unify |
| **2026-05-16 PM** | **Manager view-only policy баталсан + 30+ декоратор хасагдсан + audit log senior view нээгдсэн** |
| 2026-05-16 PM | Code-quality cleanup #1-4: ghost roles, security fallback, default literals |
| 2026-05-16 | role policy matrix doc үүсгэсэн (`docs/dev-logs/ROLE_PERMISSIONS_MATRIX_2026_05_16.md`) |

---

**Файл үүсгэсэн:** Claude Code
**Сүүлд шинэчилсэн:** 2026-05-16 (Manager view-only policy + code quality cleanup)
**Холбоотой:** `docs/dev-logs/ROLE_PERMISSIONS_MATRIX_2026_05_16.md` (120+ үйлдлийн дэлгэрэнгүй матриц)
