# COAL LIMS - ROLE PERMISSIONS LOG
# Огноо: 2025-12-04
# ============================================================================

## 1. СИСТЕМИЙН ROLE-УУД (5 төрөл)

| Role | Код | Монгол нэр | Тайлбар |
|------|-----|-----------|---------|
| Sample Preparation | `prep` | Дээж бэлтгэгч | Дээж бүртгэх, бэлтгэлийн үе шат |
| Chemist | `chemist` | Химич | Шинжилгээ хийх, үр дүн оруулах |
| Senior Chemist | `senior` | Ахлах химич | Үр дүн шалгах, баталгаажуулах |
| Manager | `manager` | Менежер | Чанарын удирдлага, тайлан |
| Administrator | `admin` | Админ | Системийн бүх эрх |

---

## 2. ЭРХИЙН МАТРИЦ

### 2.1 Үндсэн функцууд

| Функц | prep | chemist | manager | senior | admin |
|-------|------|---------|---------|--------|-------|
| **Дээж бүртгэх** | ✅ | ❌ | ❌ | ❌ | ✅ |
| **Дээж засах** | Шинэ л | ❌ | ❌ | ✅ | ✅ |
| **Дээж устгах** | ❌ | ❌ | ❌ | ✅ | ✅ |
| **Шинжилгээ оруулах** | ❌ | ✅ | ❌ | ❌ | ❌ |
| **Үр дүн батлах** | ❌ | ❌ | ❌ | ✅ | ✅ |

### 2.2 Чанарын удирдлага (Quality)

| Функц | prep | chemist | manager | senior | admin |
|-------|------|---------|---------|--------|-------|
| **CAPA бүртгэх** | ❌ | ❌ | ✅ | ✅ | ✅ |
| **Гомдол бүртгэх** | ❌ | ❌ | ✅ | ✅ | ✅ |
| **PT Testing** | ❌ | ❌ | ✅ | ✅ | ✅ |
| **Орчны хяналт** | ❌ | ❌ | ✅ | ✅ | ✅ |
| **Control Charts** | ❌ | ❌ | ✅ | ✅ | ✅ |

### 2.3 Тоног төхөөрөмж

| Функц | prep | chemist | manager | senior | admin |
|-------|------|---------|---------|--------|-------|
| **Харах** | ✅ | ✅ | ✅ | ✅ | ✅ |
| **Нэмэх** | ❌ | ❌ | ✅ | ✅ | ✅ |
| **Засах** | ❌ | ❌ | ✅ | ✅ | ✅ |
| **Устгах** | ❌ | ❌ | ✅ | ✅ | ✅ |

### 2.4 Стандарт (CM/GBW)

| Функц | prep | chemist | manager | senior | admin |
|-------|------|---------|---------|--------|-------|
| **Харах** | ✅ | ✅ | ✅ | ✅ | ✅ |
| **Нэмэх** | ❌ | ❌ | ❌ | ✅ | ✅ |
| **Засах** | ❌ | ❌ | ❌ | ✅ | ✅ |
| **Устгах** | ❌ | ❌ | ❌ | ✅ | ✅ |

### 2.5 Системийн удирдлага

| Функц | prep | chemist | manager | senior | admin |
|-------|------|---------|---------|--------|-------|
| **Хэрэглэгч удирдлага** | ❌ | ❌ | ❌ | ❌ | ✅ |
| **Шинжилгээний тохиргоо** | ❌ | ❌ | ❌ | ✅ | ✅ |
| **Repeatability лимит** | ❌ | ❌ | ❌ | ✅ | ✅ |
| **Бортого тогтмол** | ❌ | ❌ | ❌ | ✅ | ✅ |
| **CSV импорт** | ❌ | ❌ | ❌ | ✅ | ✅ |

### 2.6 Тайлан ба Export

| Функц | prep | chemist | manager | senior | admin |
|-------|------|---------|---------|--------|-------|
| **Тайлан харах** | ✅ | ✅ | ✅ | ✅ | ✅ |
| **Excel Export** | ❌ | ❌ | ✅ | ✅ | ✅ |
| **Ээлжийн гүйцэтгэл** | ❌ | ❌ | ✅ | ✅ | ✅ |
| **Цагийн тайлан илгээх** | ❌ | ❌ | ❌ | ✅ | ✅ |

---

## 3. NAVIGATION MENU ЭРХҮҮД

### 3.1 Бүгдэд харагдана
- Нүүр
- Шинжилгээ
- Тоног төхөөрөмж
- Чанар (бүх submenu)
- Стандарт (CM, GBW)
- Тайлан (Consumption, Monthly Plan, Статистик, Дээж хадгалалт)

### 3.2 Senior, Manager, Admin
- Нэгтгэл
- Удирдлага (бүх submenu)

### 3.3 Senior, Admin
- Ахлахын хяналт
- Цагийн тайлан илгээх товч

### 3.4 Admin only
- Хэрэглэгч удирдлага

---

## 4. НЭГТГЭЛ (SAMPLE SUMMARY) ХУУДАСНЫ ТОВЧНУУД

| Товч | manager | senior | admin |
|------|---------|--------|-------|
| QC: Tol | ❌ | ✅ | ✅ |
| QC: Spec | ❌ | ✅ | ✅ |
| Correlation | ❌ | ✅ | ✅ |
| CSV | ❌ | ✅ | ✅ |
| Хуулах | ❌ | ✅ | ✅ |
| Аудит | ❌ | ✅ | ✅ |
| **Архив** | ✅ | ✅ | ✅ |
| Архивлах | ❌ | ✅ | ✅ |
| Шинэчлэх | ✅ | ✅ | ✅ |

---

## 5. ROUTE ФАЙЛУУД ДАХ ЭРХ ШАЛГАЛТУУД

### 5.1 admin_routes.py
```python
# Админ л
@admin_required  # manage_users, edit_user, delete_user

# Ахлах/Админ
@senior_or_admin_required  # analysis_config, control_standards, gbw_standards
```

### 5.2 equipment_routes.py
```python
if current_user.role not in ["senior", "manager", "admin"]:
    # add_equipment, edit_equipment, delete_equipment, calibration_update
```

### 5.3 quality/*.py (capa, complaints, proficiency, environmental, control_charts)
```python
def _can_edit():
    return current_user.role in ['senior', 'manager', 'admin']
```

### 5.4 analysis/senior.py
```python
@analysis_role_required(["senior", "admin"])
# ahlah_dashboard, api_ahlah_data, api_ahlah_stats
```

### 5.5 settings_routes.py
```python
def _is_senior_or_admin():
    return current_user.role in ("senior", "admin")
# bottles, repeatability_limits
```

### 5.6 report_routes.py
```python
if current_user.role not in ["senior", "admin"]:
    # monthly_plan save
```

---

## 6. TEMPLATE ФАЙЛУУД ДАХ ЭРХ ШАЛГАЛТУУД

### 6.1 base.html (Navigation)
- Line 200: Ахлахын хяналт `['senior', 'admin']`
- Line 209: Нэгтгэл `['senior', 'manager', 'admin']`
- Line 240: Удирдлага `['senior', 'manager', 'admin']`
- Line 246: Хэрэглэгч `admin`
- Line 275: Цагийн тайлан `['senior', 'admin']`

### 6.2 sample_summary.html
- Line 15-54: Товчнуудын эрх шалгалт

### 6.3 index.html
- Line 201: Excel товч `['senior', 'manager', 'admin']`

### 6.4 equipment_list.html
- Line 20: Шинэ төхөөрөмж товч `['senior', 'manager', 'admin']`
- Line 411: Устгах товч `['senior', 'manager', 'admin']`

### 6.5 admin/control_standards.html
- Line 10: Шинэ стандарт товч `['senior', 'admin']`
- Line 53-84: Үйлдлийн товчнууд `['senior', 'admin']`

### 6.6 admin/gbw_list.html
- Line 10: Шинэ GBW товч `['senior', 'admin']`
- Line 54-96: Үйлдлийн товчнууд `['senior', 'admin']`

### 6.7 analytics_dashboard.html
- Line 8-26: Excel Export `['senior', 'manager', 'admin']`

### 6.8 audit_hub.html
- Line 215: Excel Export `['senior', 'manager', 'admin']`

---

## 7. DATABASE MIGRATION-УУД

### 7.1 Role нэрийн өөрчлөлтүүд
- `b3ed3b177364`: ahlah → senior
- `c3bc04cf9877`: himich → chemist, beltgegch → prep

---

## 8. FORMS ДАХ ROLE СОНГОЛТУУД

### app/forms.py - UserManagementForm
```python
role = SelectField(
    "Эрхийн түвшин",
    choices=[
        ("prep", "Дээж бэлтгэгч (Sample Preparation)"),
        ("chemist", "Химич (Chemist)"),
        ("senior", "Ахлах химич (Senior Chemist)"),
        ("manager", "Менежер (Manager)"),
        ("admin", "Админ"),
    ],
)
```

---

## 9. MODELS ДАХ ROLE

### app/models.py - User
```python
role = db.Column(db.String(64), index=True, default="prep")
# Боломжит утгууд: prep, chemist, senior, manager, admin
```

### app/models.py - AnalysisType
```python
required_role = db.Column(db.String(64), default="chemist")
# FM, Solid → prep
# Бусад → chemist
```

---

## 10. DECORATORS

### app/utils/decorators.py
```python
allowed_roles = ["chemist", "senior", "manager", "admin", "prep"]
```

### app/routes/admin_routes.py
```python
def admin_required(f):
    # role == 'admin'

def senior_or_admin_required(f):
    # role in ['senior', 'admin']
```

---

## ТҮҮХ

| Огноо | Өөрчлөлт |
|-------|----------|
| 2025-12-04 | ahlah → senior нэр солисон |
| 2025-12-04 | himich → chemist нэр солисон |
| 2025-12-04 | beltgegch → prep нэр солисон |
| 2025-12-04 | manager role нэмэгдсэн |
| 2025-12-04 | Чанар, Тоног төхөөрөмжийн эрх manager-т нэмэгдсэн |
| 2025-12-04 | Excel export эрх manager-т нэмэгдсэн |
| 2025-12-04 | Нэгтгэл хуудасны товчнуудын эрх тохируулсан |

---

**Файл үүсгэсэн:** Claude Code
**Сүүлд шинэчилсэн:** 2025-12-04
