# LIMS — ROLE PERMISSIONS MATRIX (2026-05-16)

> **Зорилго:** Хэрэглэгчид role-уудын зөв эрхийн хүрээ тогтоох checklist үүсгэх.
> 5 role × 120+ үйлдлийн матриц — Excel-руу хуулж шинэ "Target" багана нэмж хариулах боломжтой.
>
> **Method:** `app/routes/`, `app/templates/`, `app/services/`, `app/utils/decorators.py`-ийн **бодит** кодоос грэп + read хийсэн.
>
> **Анхааруулга:** Сүүлийн audit doc `docs_all/LIMS_-_ROLE_PERMISSIONS_LOG.md` нь **2025-12-04 он** (5 сараас илүү хуучин). Кодтой хэр sync-тэй болохыг энэ матриц харуулна.

---

## Тэмдэглэгээ

- ✅ Зөвшөөрөгдсөн (decorator эсвэл inline check pass)
- ❌ Хориглосон (decorator deny)
- ⚠️ Inline conditional (зөвхөн нөхцлийн дагуу — өөрийнхөө бичсэн record, allowed_labs гэх мэт)
- (blank) — зөвхөн `@login_required`, role check байхгүй (бүх 5 role ✅)

## Категориуд

1. Authentication & User Management
2. Sample Registration & Lifecycle
3. Mass / Weight Entry
4. Analysis Workflow (chemist + senior)
5. Equipment Management
6. Chemical & Spare Parts
7. Quality Module
8. Standards (CM/GBW)
9. Reports & Exports
10. Monthly Plan
11. System Settings
12. Workflow Configuration
13. Audit & License
14. Chat / Communication
15. Lab Access (allowed_labs)
16. Navigation Menu (templates)

---

## 1. Authentication & User Management

| Action | File:Line | Method | prep | chemist | senior | manager | admin | Notes |
|--------|-----------|--------|------|---------|--------|---------|-------|-------|
| Login page | routes/main/auth.py:25 | public | ✅ | ✅ | ✅ | ✅ | ✅ | |
| Logout | routes/main/auth.py:52 | @login_required | ✅ | ✅ | ✅ | ✅ | ✅ | |
| Edit own profile | routes/main/auth.py:63 | @login_required | ✅ | ✅ | ✅ | ✅ | ✅ | Self-service |
| Manage users (list) | routes/admin/routes.py | @admin_required | ❌ | ❌ | ❌ | ❌ | ✅ | |
| Create user | routes/admin/routes.py | @admin_required | ❌ | ❌ | ❌ | ❌ | ✅ | |
| Edit user (role/labs) | routes/admin/routes.py | @admin_required | ❌ | ❌ | ❌ | ❌ | ✅ | |
| Delete user | routes/admin/routes.py:158 | @admin_required | ❌ | ❌ | ❌ | ❌ | ✅ | Cannot delete admins or self |

## 2. Sample Registration & Lifecycle

| Action | File:Line | Method | prep | chemist | senior | manager | admin | Notes |
|--------|-----------|--------|------|---------|--------|---------|-------|-------|
| View sample list | routes/main/index.py | @login_required | ✅ | ✅ | ✅ | ✅ | ✅ | |
| Register new sample | routes/main/index.py:122 | inline `["prep","admin"]` | ✅ | ❌ | ❌ | ❌ | ✅ | Hard-coded |
| Edit sample | routes/main/samples.py:41 | inline `[ADMIN,SENIOR]` + owner | ⚠️ | ⚠️ | ✅ | ❌ | ✅ | Bulk allow + owner exception |
| Bulk delete sample | api/mass_api.py:108 | inline `_can_delete_sample()` | ❌ | ❌ | ✅ | ❌ | ✅ | |
| Archive/unarchive sample | api/mass_api.py:27 | @login_required + workflow | ✅ | ✅ | ✅ | ✅ | ✅ | Workflow engine enforces |

## 3. Mass / Weight Entry

| Action | File:Line | Method | prep | chemist | senior | manager | admin | Notes |
|--------|-----------|--------|------|---------|--------|---------|-------|-------|
| View eligible samples | api/mass_api.py:49 | @login_required | ✅ | ✅ | ✅ | ✅ | ✅ | |
| Save mass measurements | api/mass_api.py:59 | @login_required | ✅ | ✅ | ✅ | ✅ | ✅ | |
| Update sample weight | api/mass_api.py:74 | @login_required | ✅ | ✅ | ✅ | ✅ | ✅ | |
| Unready samples (revert) | api/mass_api.py:92 | @login_required | ✅ | ✅ | ✅ | ✅ | ✅ | |

## 4. Analysis Workflow

| Action | File:Line | Method | prep | chemist | senior | manager | admin | Notes |
|--------|-----------|--------|------|---------|--------|---------|-------|-------|
| Analysis workspace | routes/analysis/workspace.py | @analysis_role_required(default) | ✅ | ✅ | ✅ | ✅ | ✅ | |
| Submit result | api/analysis_save.py | @login_required | ✅ | ✅ | ✅ | ✅ | ✅ | |
| Request analysis (assign) | api/analysis_api.py | @login_required | ✅ | ✅ | ✅ | ✅ | ✅ | |
| Ahlah review dashboard | analysis/senior.py:32 | @analysis_role_required(senior/admin) | ❌ | ❌ | ✅ | ❌ | ✅ | |
| Approve/reject result | analysis/senior.py:67 | @analysis_role_required(senior/admin) | ❌ | ❌ | ✅ | ❌ | ✅ | Just fixed (was inline) |
| Bulk approve/reject | analysis/senior.py:91 | @analysis_role_required(senior/admin) | ❌ | ❌ | ✅ | ❌ | ✅ | Just fixed |
| Select repeat result | analysis/senior.py:136 | @analysis_role_required(senior/admin) | ❌ | ❌ | ✅ | ❌ | ✅ | |
| Senior dashboard stats | analysis/senior.py:119 | @analysis_role_required(senior/admin) | ❌ | ❌ | ✅ | ❌ | ✅ | |
| QC Norm/Composite/Correlation | analysis/qc.py | @analysis_role_required(default) | ✅ | ✅ | ✅ | ✅ | ✅ | |

## 5. Equipment Management

| Action | File:Line | Method | prep | chemist | senior | manager | admin | Notes |
|--------|-----------|--------|------|---------|--------|---------|-------|-------|
| View equipment list | equipment/crud.py:174 | @login_required | ✅ | ✅ | ✅ | ✅ | ✅ | |
| Add equipment | equipment/crud.py | @role_required(senior/manager/admin) | ❌ | ❌ | ✅ | ✅ | ✅ | |
| Edit equipment | equipment/crud.py | @role_required(senior/manager/admin) | ❌ | ❌ | ✅ | ✅ | ✅ | |
| Delete/retire equipment | equipment/crud.py | @role_required(senior/manager/admin) | ❌ | ❌ | ✅ | ✅ | ✅ | |
| Calibration log | equipment/crud.py | @role_required(senior/manager/admin) | ❌ | ❌ | ✅ | ✅ | ✅ | |
| Maintenance log | equipment/crud.py | @role_required(senior/manager/admin) | ❌ | ❌ | ✅ | ✅ | ✅ | |
| View register journals | equipment/registers.py | @login_required | ✅ | ✅ | ✅ | ✅ | ✅ | |
| Add register entry | equipment/registers.py | @role_required(senior/manager/admin) | ❌ | ❌ | ✅ | ✅ | ✅ | |
| Bulk usage log | api/log_usage_bulk | @login_required | ✅ | ✅ | ✅ | ✅ | ✅ | |
| Out-of-service register | equipment/registers.py | @login_required | ✅ | ✅ | ✅ | ✅ | ✅ | |

## 6. Chemical & Spare Parts

| Action | File:Line | Method | prep | chemist | senior | manager | admin | Notes |
|--------|-----------|--------|------|---------|--------|---------|-------|-------|
| View chemical list | chemicals/crud.py | @login_required | ✅ | ✅ | ✅ | ✅ | ✅ | |
| Add chemical | chemicals/crud.py | @role_required(chemist+) | ❌ | ✅ | ✅ | ✅ | ✅ | |
| Edit chemical | chemicals/crud.py | @role_required(chemist+) | ❌ | ✅ | ✅ | ✅ | ✅ | |
| Consume chemical (usage log) | chemicals/crud.py | @role_required(chemist+) | ❌ | ✅ | ✅ | ✅ | ✅ | |
| Dispose chemical | chemicals/crud.py | @role_required(senior/manager/admin) | ❌ | ❌ | ✅ | ✅ | ✅ | |
| Waste chemical list | chemicals/waste.py | @login_required | ✅ | ✅ | ✅ | ✅ | ✅ | |
| Add waste entry | chemicals/waste.py | @role_required(chemist+) | ❌ | ✅ | ✅ | ✅ | ✅ | |
| Approve waste disposal | chemicals/waste.py | @role_required(senior/manager/admin) | ❌ | ❌ | ✅ | ✅ | ✅ | |
| View solutions list | water_lab/chemistry/solutions.py | @login_required | ✅ | ✅ | ✅ | ✅ | ✅ | |
| Add solution recipe | water_lab/chemistry/solutions.py | @role_required(senior/admin) | ❌ | ❌ | ✅ | ❌ | ✅ | |
| View spare parts | spare_parts/crud.py | @role_required(manager/admin) | ❌ | ❌ | ❌ | ✅ | ✅ | View also restricted |
| Add spare part | spare_parts/crud.py | @role_required(manager/admin) | ❌ | ❌ | ❌ | ✅ | ✅ | |
| Use spare part (usage) | spare_parts/crud.py | @role_required(chemist+) | ❌ | ✅ | ✅ | ✅ | ✅ | |
| Spare parts categories | spare_parts/crud.py | @role_required(admin) | ❌ | ❌ | ❌ | ❌ | ✅ | |

## 7. Quality Module

| Action | File:Line | Method | prep | chemist | senior | manager | admin | Notes |
|--------|-----------|--------|------|---------|--------|---------|-------|-------|
| CAPA list | quality/capa.py | @login_required | ✅ | ✅ | ✅ | ✅ | ✅ | |
| Create CAPA | quality/capa.py | inline `[senior,manager,admin]` | ❌ | ❌ | ✅ | ✅ | ✅ | |
| Edit CAPA | quality/capa.py | inline | ❌ | ❌ | ✅ | ✅ | ✅ | |
| Complaints list | quality/complaints.py | @login_required | ✅ | ✅ | ✅ | ✅ | ✅ | |
| Create complaint | quality/complaints.py | @login_required | ✅ | ✅ | ✅ | ✅ | ✅ | All can file |
| Sign complaint | quality/complaints.py | @role_required(senior/admin) | ❌ | ❌ | ✅ | ❌ | ✅ | |
| PT (Proficiency Test) list | quality/proficiency.py | @login_required | ✅ | ✅ | ✅ | ✅ | ✅ | |
| Create PT record | quality/proficiency.py | inline `[senior,manager,admin]` | ❌ | ❌ | ✅ | ✅ | ✅ | |
| Environmental log | quality/environmental.py | @login_required | ✅ | ✅ | ✅ | ✅ | ✅ | |
| Control charts | quality/control_charts.py | @login_required | ✅ | ✅ | ✅ | ✅ | ✅ | |
| Improvement records | quality/improvement.py | @login_required | ✅ | ✅ | ✅ | ✅ | ✅ | |
| Nonconformity records | quality/nonconformity.py | @login_required | ✅ | ✅ | ✅ | ✅ | ✅ | |

## 8. Standards (CM/GBW)

| Action | File:Line | Method | prep | chemist | senior | manager | admin | Notes |
|--------|-----------|--------|------|---------|--------|---------|-------|-------|
| List control standards | admin/routes.py | @senior_or_admin_required | ❌ | ❌ | ✅ | ❌ | ✅ | |
| Add control standard | admin/routes.py | @senior_or_admin_required | ❌ | ❌ | ✅ | ❌ | ✅ | |
| Edit control standard | admin/routes.py | @senior_or_admin_required | ❌ | ❌ | ✅ | ❌ | ✅ | |
| Activate/delete CM | admin/routes.py | @senior_or_admin_required | ❌ | ❌ | ✅ | ❌ | ✅ | |
| List GBW | admin/routes.py | @senior_or_admin_required | ❌ | ❌ | ✅ | ❌ | ✅ | |
| Add/edit GBW | admin/routes.py | @senior_or_admin_required | ❌ | ❌ | ✅ | ❌ | ✅ | |

## 9. Reports & Exports

| Action | File:Line | Method | prep | chemist | senior | manager | admin | Notes |
|--------|-----------|--------|------|---------|--------|---------|-------|-------|
| Report list | reports/crud.py | @login_required | ✅ | ✅ | ✅ | ✅ | ✅ | |
| Generate PDF | reports/pdf_generator.py | @login_required | ✅ | ✅ | ✅ | ✅ | ✅ | |
| Send email report | reports/email_sender.py | @role_required(senior/admin) | ❌ | ❌ | ✅ | ❌ | ✅ | |
| Approve report | reports/crud.py | inline `[senior,manager,admin]` | ❌ | ❌ | ✅ | ✅ | ✅ | |
| Consumption report | reports/consumption.py | @login_required | ✅ | ✅ | ✅ | ✅ | ✅ | |
| Custom report builder | api/report_builder_api.py | @login_required | ✅ | ✅ | ✅ | ✅ | ✅ | |
| Save report template | api/report_builder_api.py | @role_required(admin/manager) | ❌ | ❌ | ❌ | ✅ | ✅ | |
| Excel export (sample summary) | api/samples_api.py | @login_required | ✅ | ✅ | ✅ | ✅ | ✅ | |
| Audit log export | api/audit_api.py | @admin_required | ❌ | ❌ | ❌ | ❌ | ✅ | |

## 10. Monthly Plan & Planning

| Action | File:Line | Method | prep | chemist | senior | manager | admin | Notes |
|--------|-----------|--------|------|---------|--------|---------|-------|-------|
| View monthly plan | reports/monthly_plan.py | @login_required | ✅ | ✅ | ✅ | ✅ | ✅ | |
| Edit monthly plan | reports/monthly_plan.py | @role_required(senior/admin) | ❌ | ❌ | ✅ | ❌ | ✅ | Just fixed (Theme C) |
| Set staff numbers | reports/monthly_plan.py | @role_required(senior/admin) | ❌ | ❌ | ✅ | ❌ | ✅ | |
| KPI dashboard | analysis/kpi.py | @login_required | ✅ | ✅ | ✅ | ✅ | ✅ | |
| SLA dashboard | analysis/sla.py | @login_required | ✅ | ✅ | ✅ | ✅ | ✅ | |

## 11. System Settings

| Action | File:Line | Method | prep | chemist | senior | manager | admin | Notes |
|--------|-----------|--------|------|---------|--------|---------|-------|-------|
| View settings page | settings/routes.py | @login_required | ✅ | ✅ | ✅ | ✅ | ✅ | |
| Edit bottle constants | settings/routes.py | inline `_is_senior_or_admin()` | ❌ | ❌ | ✅ | ❌ | ✅ | |
| Bottle CRUD | settings/routes.py | inline `_is_senior_or_admin()` | ❌ | ❌ | ✅ | ❌ | ✅ | |
| Repeatability limits | settings/routes.py | inline `_is_senior_or_admin()` | ❌ | ❌ | ✅ | ❌ | ✅ | |
| Error reason settings | settings/routes.py | inline `_is_admin()` | ❌ | ❌ | ❌ | ❌ | ✅ | |
| Email recipient | settings/routes.py | @login_required | ✅ | ✅ | ✅ | ✅ | ✅ | |
| Hourly schedule | settings/routes.py | inline `_is_senior_or_admin()` | ❌ | ❌ | ✅ | ❌ | ✅ | |
| Analysis config (types) | admin/routes.py | @senior_or_admin_required | ❌ | ❌ | ✅ | ❌ | ✅ | |
| CSV import (historical) | imports/routes.py | @role_required(admin) | ❌ | ❌ | ❌ | ❌ | ✅ | |

## 12. Workflow Configuration

| Action | File:Line | Method | prep | chemist | senior | manager | admin | Notes |
|--------|-----------|--------|------|---------|--------|---------|-------|-------|
| View workflows | api/workflow_api.py | @login_required | ✅ | ✅ | ✅ | ✅ | ✅ | |
| Get workflow config | api/workflow_api.py | @login_required | ✅ | ✅ | ✅ | ✅ | ✅ | |
| Get available transitions | api/workflow_api.py | @login_required (workflow eng. check) | ⚠️ | ⚠️ | ⚠️ | ⚠️ | ⚠️ | Depends on workflow rules |
| Save workflow config | api/workflow_api.py | @role_required(admin) | ❌ | ❌ | ❌ | ❌ | ✅ | |
| Reset workflow | api/workflow_api.py | @role_required(admin) | ❌ | ❌ | ❌ | ❌ | ✅ | |

## 13. Audit & License

| Action | File:Line | Method | prep | chemist | senior | manager | admin | Notes |
|--------|-----------|--------|------|---------|--------|---------|-------|-------|
| View audit log | api/audit_api.py | @admin_required | ❌ | ❌ | ❌ | ❌ | ✅ | |
| Filter audit log | api/audit_api.py | @admin_required | ❌ | ❌ | ❌ | ❌ | ✅ | |
| Audit hub | api/audit_api.py | @login_required + role | ❌ | ❌ | ✅ | ❌ | ✅ | |
| View analysis result log | sample_history | @login_required | ✅ | ✅ | ✅ | ✅ | ✅ | Per-sample history |
| License info | license/routes.py | @role_required(admin) | ❌ | ❌ | ❌ | ❌ | ✅ | |
| License hwid view | license/routes.py | @role_required(admin) | ❌ | ❌ | ❌ | ❌ | ✅ | |
| Clear tamper flag | flask CLI (terminal) | CLI only | ❌ | ❌ | ❌ | ❌ | ✅ | Server admin |

## 14. Chat / Communication

| Action | File:Line | Method | prep | chemist | senior | manager | admin | Notes |
|--------|-----------|--------|------|---------|--------|---------|-------|-------|
| View chat | api/chat_api.py | @login_required | ✅ | ✅ | ✅ | ✅ | ✅ | |
| Send message | api/chat_api.py:85 | @login_required + inline | ⚠️ | ⚠️ | ⚠️ | ⚠️ | ⚠️ | Chemist/Prep scope-limited |
| Delete own message | api/chat_api.py | @login_required (owner) | ⚠️ | ⚠️ | ⚠️ | ⚠️ | ⚠️ | Owner only |
| Delete any message | api/chat_api.py | @role_required(senior/admin) | ❌ | ❌ | ✅ | ❌ | ✅ | |
| SocketIO connect | chat/events.py | @authenticated_only | ✅ | ✅ | ✅ | ✅ | ✅ | |
| Broadcast event | chat/events.py:255 | inline `[senior,admin]` | ❌ | ❌ | ✅ | ❌ | ✅ | |

## 15. Lab Access (allowed_labs)

| Lab | File:Line | Method | prep | chemist | senior | manager | admin | Notes |
|-----|-----------|--------|------|---------|--------|---------|-------|-------|
| Coal lab | utils/decorators.py:lab_required('coal') | per-user `allowed_labs` JSON | ⚠️ | ⚠️ | ⚠️ | ⚠️ | ✅ | Admin bypass |
| Petrography | utils/decorators.py:lab_required('petrography') | per-user `allowed_labs` | ⚠️ | ⚠️ | ⚠️ | ⚠️ | ✅ | |
| Water chemistry | utils/decorators.py:lab_required('water_chemistry') | per-user `allowed_labs` | ⚠️ | ⚠️ | ⚠️ | ⚠️ | ✅ | |
| Microbiology | utils/decorators.py:lab_required('microbiology') | per-user `allowed_labs` | ⚠️ | ⚠️ | ⚠️ | ⚠️ | ✅ | |

## 16. Navigation Menu (Templates)

| Menu | Template:Line | Check | prep | chemist | senior | manager | admin | Notes |
|------|---------------|-------|------|---------|--------|---------|-------|-------|
| Хяналт (Senior dashboard) | base.html | `[senior,admin]` | ❌ | ❌ | ✅ | ❌ | ✅ | |
| Нэгтгэл (Sample Summary) | base.html | `[senior,manager,admin]` | ❌ | ❌ | ✅ | ✅ | ✅ | |
| Удирдлага (Admin menu) | base.html | `[senior,manager,admin]` | ❌ | ❌ | ✅ | ✅ | ✅ | |
| Хэрэглэгч (User mgmt) | base.html | `admin` | ❌ | ❌ | ❌ | ❌ | ✅ | |
| Цагийн тайлан | base.html | `[senior,admin]` | ❌ | ❌ | ✅ | ❌ | ✅ | |
| Audit menu | base.html | `[senior,admin]` | ❌ | ❌ | ✅ | ❌ | ✅ | |

---

## 🚩 Anomaly / Bug сэжиг (HIGH priority)

| # | Хаана | Асуудал |
|---|-------|---------|
| 1 | `routes/api/workflow_api.py:23, 352` | "senior_analyst", "analyst" enum-д байхгүй ghost role-ууд. Workflow config UI-аас allow хийсэн нь bug. |
| 2 | `routes/api/helpers.py:177` | `_can_delete_sample()` literal `{"admin","senior"}`. Decorator биш inline helper — pattern inconsistent. |
| 3 | `services/mass_service.py:116` | `getattr(current_user, 'role', 'admin')` fallback нь role атрибут байхгүй edge case-д admin эрх олгож байна (security). |
| 4 | `utils/decorators.py:170` | `analysis_role_required` default literal list — UserRole enum биш. |
| 5 | `routes/main/index.py:122` | `if current_user.role not in ["prep", "admin"]` literal — UserRole enum биш. |
| 6 | `routes/settings/routes.py:48-53` | `_is_admin()`, `_is_senior_or_admin()` helper literal — UserRole enum биш. |
| 7 | `routes/spare_parts/crud.py` | Senior CHANNot view spare parts. Manager/admin only. Senior зориудаар хасагдсан уу? |
| 8 | `models/analysis.py` | `AnalysisType.required_role` баган — `chemist`, `prep` literals seed-д hardcoded. |
| 9 | Templates × 14+ | `{% if current_user.role == 'admin' %}` hard-coded literal. Context_processor pattern байхгүй. |
| 10 | `routes/analysis/senior.py:34` (засагдсан) | Inline check → @analysis_role_required солисон (today commit ef2d63c) |

---

## CSV Excel-руу хуулах формат

Эхний хүснэгтийн толгойг **`Action | File:Line | Method | prep | chemist | senior | manager | admin | Current | Target | Notes`** болгоод, Target багана хоосон үлдээж checklist хийнэ үү.

CSV format жишээ (нэг мөр):
```
Register new sample,routes/main/index.py:122,inline,✅,❌,❌,❌,✅,prep+admin only,?,Hard-coded ["prep","admin"]
```

---

## ТҮҮХ

| Огноо | Шинэчилсэн |
|-------|-----------|
| 2025-12-04 | Анхны audit (`LIMS_-_ROLE_PERMISSIONS_LOG.md`) |
| 2026-05-16 | Энэ матриц — кодоос шууд scan, anomalies нэмж 5+ HIGH bug олж тэмдэглэв |

---

**Файл үүсгэсэн:** Claude Opus 4.7 — code-direct audit
**Зорилго:** Хэрэглэгч Excel-руу хуулж target эрхийн хүрээ тогтоох
