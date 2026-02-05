# Role & Authentication Code Audit
**Огноо:** 2026-02-05
**Хамрах хүрээ:** User model, Login/Logout, Role-based access, Authorization decorators

---

## 1. Бүтцийн тойм

### 1.1 Үндсэн файлууд
| Файл | Мөрийн тоо | Үүрэг |
|------|------------|-------|
| `app/models.py` (User) | 25-154 | User model, password validation |
| `app/models.py` (AuditLog) | 1712-1743 | Audit logging model |
| `app/routes/main/auth.py` | 96 | Login/logout/profile routes |
| `app/utils/decorators.py` | 202 | 5 authorization decorators |
| `app/routes/admin_routes.py` | 800+ | User CRUD, config management |
| `app/utils/security.py` | 97 | Security utilities |
| `app/utils/audit.py` | 165 | Audit logging functions |
| `app/forms.py` | 51-96 | Login, UserManagement forms |

### 1.2 Roles (5 төрөл)
| Role | Монгол | Үндсэн эрх |
|------|--------|-----------|
| `prep` | Дээж бэлтгэгч | Дээж бүртгэх |
| `chemist` | Химич | Шинжилгээ хийх |
| `senior` | Ахлах химич | Үр дүн шалгах, баталгаажуулах |
| `manager` | Менежер | Лабораторийн удирдлага |
| `admin` | Админ | Бүх эрх + хэрэглэгч удирдлага |

### 1.3 Labs (4 төрөл)
| Lab Key | Монгол |
|---------|--------|
| `coal` | Нүүрсний лаб |
| `petrography` | Петрограф |
| `water` | Усны хими |
| `microbiology` | Микробиологи |

---

## 2. Сайн талууд ✅

### 2.1 Password Security
- ✅ Werkzeug password hashing (`generate_password_hash`, `check_password_hash`)
- ✅ Constant-time comparison (timing attack сэргийлэлт)
- ✅ Password policy validation (8+ chars, uppercase, lowercase, digit)
- ✅ Policy enforcement in `set_password()`

### 2.2 Authentication
- ✅ Flask-Login integration (`@login_required`)
- ✅ Rate limiting: 5 per minute on login (brute force protection)
- ✅ Open Redirect protection (`is_safe_url()`)
- ✅ Remember me функц

### 2.3 Authorization
- ✅ 5 reusable decorators:
  - `@role_required(*roles)`
  - `@admin_required`
  - `@role_or_owner_required(*roles, owner_check)`
  - `@lab_required(lab_key)`
  - `@analysis_role_required(roles)`
- ✅ Admin bypass for all labs
- ✅ Multi-lab access control (`allowed_labs` JSON field)

### 2.4 Audit Logging
- ✅ Login success/failure бүртгэдэг
- ✅ Logout бүртгэдэг
- ✅ Profile update бүртгэдэг
- ✅ IP address + User Agent хадгалдаг
- ✅ ISO 17025 compliance docstring

### 2.5 Admin Protections
- ✅ Шинэ admin үүсгэх хориотой (line 125-126)
- ✅ Admin өөрийгөө устгах хориотой (line 226-228)
- ✅ Admin role өөрчлөх хориотой (line 180-183)

### 2.6 Security Headers
- ✅ X-Frame-Options: SAMEORIGIN
- ✅ X-Content-Type-Options: nosniff
- ✅ X-XSS-Protection: 1; mode=block
- ✅ Content Security Policy
- ✅ CSRF protection (Flask-WTF)

---

## 3. Олдсон асуудлууд

### 3.1 MODERATE - AuditLog hash дутуу
**Байршил:** `app/models.py:1712-1743`
**Түвшин:** MODERATE (ISO 17025)

**Асуудал:** AuditLog model-д `data_hash` field байхгүй. SparePartLog, ChemicalLog дээр нэмсэн боловч AuditLog үлдсэн.

```python
# AuditLog-д нэмэх шаардлагатай:
data_hash = db.Column(db.String(64), nullable=True)

def compute_hash(self) -> str:
    """ISO 17025: Audit log integrity hash"""
    import hashlib
    data = (
        f"{self.user_id}|{self.action}|{self.resource_type}|"
        f"{self.resource_id}|{self.timestamp}|{self.details}"
    )
    return hashlib.sha256(data.encode('utf-8')).hexdigest()
```

---

### 3.2 LOW - Inline role checks давхардал
**Байршил:** 50+ газар
**Түвшин:** LOW (code quality)

**Асуудал:** Олон газарт inline role check ашигласан (`if current_user.role not in [...]`) - decorator ашиглах нь илүү найдвартай.

```python
# Жишээ - spare_parts/crud.py:91
if current_user.role not in ['manager', 'admin']:
    flash("Эрх хүрэхгүй.", "danger")
    return redirect(...)

# Илүү сайн:
@login_required
@role_required('manager', 'admin')
def some_route():
    ...
```

**Статус:** ⏸️ Хойшлуулсан (ажиллагаанд нөлөөлөхгүй)

---

### 3.3 LOW - Admin user устгах шалгалт дутуу
**Байршил:** `app/routes/admin_routes.py:224-239`
**Түвшин:** LOW

**Асуудал:** Admin хэрэглэгч өөр админ хэрэглэгчийг устгах боломжтой.

```python
# Одоогийн код:
if current_user.id == user_id:
    flash("Админ хэрэглэгч өөрийгөө устгах боломжгүй.", 'danger')
    return redirect(...)

# Нэмэх шаардлагатай:
user_to_delete = User.query.get_or_404(user_id)
if user_to_delete.role == 'admin':
    flash("Админ хэрэглэгчийг устгах боломжгүй.", 'danger')
    return redirect(...)
```

---

### 3.4 LOW - User audit logging дутуу
**Байршил:** `app/routes/admin_routes.py`
**Түвшин:** LOW

**Асуудал:** User create, edit, delete үйлдлүүдэд audit log бичдэггүй.

```python
# Нэмэх шаардлагатай:
log_audit(
    action='create_user',
    resource_type='User',
    resource_id=user.id,
    details={'username': user.username, 'role': user.role}
)
```

---

### 3.5 INFO - Session timeout тохиргоо дутуу
**Байршил:** `app/__init__.py`
**Түвшин:** INFO

**Санал:** Flask-Login session timeout тохируулах:
```python
app.config['REMEMBER_COOKIE_DURATION'] = timedelta(days=7)
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=8)  # Ажлын өдөр
```

---

## 4. Засах дараалал

| # | Асуудал | Түвшин | Статус |
|---|---------|--------|--------|
| 1 | AuditLog hash field | MODERATE | ✅ Засагдсан |
| 2 | Inline role checks | LOW | ⏸️ Хойшлуулах |
| 3 | Admin user delete | LOW | ✅ Засагдсан |
| 4 | User audit logging | LOW | ✅ Засагдсан |
| 5 | Session timeout | INFO | ⏸️ Хойшлуулах |

### 4.1 Засагдсан засварууд

**AuditLog hash (models.py:1738-1755):**
```python
data_hash = db.Column(db.String(64), nullable=True)

def compute_hash(self) -> str:
    data = f"{self.user_id}|{self.action}|{self.resource_type}|..."
    return hashlib.sha256(data.encode('utf-8')).hexdigest()
```

**Admin user delete protection (admin_routes.py:243-246):**
```python
if user_to_delete.role == 'admin':
    flash("Админ хэрэглэгчийг устгах боломжгүй.", 'danger')
    return redirect(...)
```

**User audit logging (admin_routes.py):**
- `create_user` - line 153-161
- `edit_user` - line 223-231
- `delete_user` - line 254-260

---

## 5. Decorator ашиглалтын статистик

| Decorator | Ашиглалтын тоо |
|-----------|---------------|
| `@login_required` | 267 |
| `@role_required` | Бага (decorator.py-д) |
| `@admin_required` | admin_routes.py-д |
| Inline role check | 50+ |

---

## 6. Role Permission Matrix

| Үйлдэл | prep | chemist | senior | manager | admin |
|--------|------|---------|--------|---------|-------|
| Дээж бүртгэх | ✓ | ✓ | ✓ | ✓ | ✓ |
| Шинжилгээ хийх | ✗ | ✓ | ✓ | ✓ | ✓ |
| Үр дүн шалгах | ✗ | ✗ | ✓ | ✓ | ✓ |
| Equipment CRUD | ✗ | ✗ | ✓ | ✓ | ✓ |
| Chemical CRUD | ✗ | ✓ | ✓ | ✓ | ✓ |
| Spare Parts | ✗ | ✓ | ✓ | ✓ | ✓ |
| User CRUD | ✗ | ✗ | ✗ | ✗ | ✓ |
| Config/Standards | ✗ | ✗ | ✓ | ✗ | ✓ |
| All labs access | ✗ | ✗ | ✗ | ✗ | ✓ |

---

## 7. Статистик

| Хэмжүүр | Утга |
|---------|------|
| Нийт файл | 8 core |
| User model мөр | 130 |
| Decorator | 5 төрөл |
| `@login_required` | 267 газар |
| CRITICAL асуудал | 0 |
| MODERATE асуудал | 1 |
| LOW асуудал | 3 |
| INFO | 1 |

---

*Шинжилгээг хийсэн: Claude Code*
*Огноо: 2026-02-05*
