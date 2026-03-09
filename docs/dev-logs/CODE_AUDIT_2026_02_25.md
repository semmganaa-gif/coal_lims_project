# Code Audit — 2026-02-25

## Хамрах хүрээ
- Models (47 model, 3275 мөр)
- Routes (36 файл, 12 directory)
- Utils/Services/Repositories (27 файл)
- Config/Templates/Static JS (15+ файл)

---

## CRITICAL (Нэн даруй)

### C-1. CSP `unsafe-eval` устгах
- **Файл:** `app/__init__.py:405-416`
- **Асуудал:** `script-src` дотор `unsafe-eval` + `unsafe-inline` → XSS хамгаалалт сулруулна
- **Засвар:** `unsafe-eval` устгах

### C-2. JS innerHTML XSS
- **Файлууд:** `ahlah_dashboard.js:340`, `add_sample.js:78,95,129`, `sample_summary.js:754`, `water_summary.js:496`
- **Асуудал:** `innerHTML`-д error message шууд оруулж байна
- **Засвар:** `textContent` эсвэл global `escapeHtml()` ашиглах (`chat.js:984-988` дээр зөв жишээ байна)

### C-3. Gi rounding алдаа
- **Файл:** `app/utils/server_calculations.py:555-626`
- **Асуудал:** Parallel бүрийг тусдаа round хийгээд дундажилж байна. ASTM стандарт: дундажилсаны дараа round хийх
- **Засвар:** `return round(sum(results)/len(results))` болгох

---

## HIGH (Чухал)

### H-1. FK Index дутуу (35+ багана)
- **Файл:** `app/models/models.py`
- `AnalysisResult.user_id:419`, `Equipment.created_by_id:753`, `MaintenanceLog.equipment_id:802`, `MaintenanceLog.performed_by_id:809`, `UsageLog.equipment_id:849`, `UsageLog.used_by_id:860`, `SparePart.created_by_id:970`, `SparePartUsage.used_by_id:1025`, `SparePartLog.user_id:1075`, `AnalysisResultLog.original_user_id:1375`, `BottleConstant.approved_by_id:1532`, `BottleConstant.created_by_id:1539`, `BottleConstant.updated_by_id:1640`, `AuditLog.user_id:1710` + Quality module FK-ууд

### H-2. N+1 Query: lazy=True → lazy='dynamic'
- `Equipment.logs:756`, `Equipment.usages:764`, `Equipment.created_by:756`
- `MaintenanceLog`, `UsageLog`, `SparePart` relationships (10+)

### H-3. MT/MG format detection сул
- **Файл:** `server_calculations.py:263-265`
- `m3` + `p1` хоёулаа байвал буруу томьёо сонгоно
- Stricter check хэрэгтэй

### H-4. CSN discrete value validation
- **Файл:** `validators.py:62-64`
- 0, 0.5, 1.0, ..., 9.0 (0.5 increment) шалгахгүй байна
- Одоо 0.0-9.6 хүртэл дурын float зөвшөөрнө

### H-5. License salt hardcoded
- **Файл:** `license_protection.py:49`
- `LICENSE_SALT = "COAL_LIMS_2024_LICENSE_SALT_V1"` → env var болгох

### H-6. AnalysisResult.logs cascade буруу
- **Файл:** `models.py:456`
- `cascade="all, delete-orphan"` → result устгахад audit log бас устна (ISO 17025 зөрчил)
- `ondelete="SET NULL"` болгох

### H-7. Hardware fingerprint bare exception
- **Файл:** `hardware_fingerprint.py:17-80`
- Бүх функц `except Exception: return "unknown"` — log хийхгүй

### H-8. Calculation error silent fallback
- **Файл:** `sample_service.py:261-268`
- Тооцоо fail → raw data-руу чимээгүй fallback

---

## MEDIUM (Засах зүйтэй)

| # | Асуудал | Файл:мөр |
|---|---------|----------|
| M-1 | Error response `str(e)` leak | `analysis_api.py:752` |
| M-2 | API response format зөрүүтэй (6 endpoint) | `analysis_api.py`, `reports/routes.py` |
| M-3 | CSRF exempt blueprint form check | `__init__.py:196-199` |
| M-4 | FLOAT_TOLERANCE hardcoded | `analysis_api.py:379` |
| M-5 | Year/month bounds validation | `reports/routes.py:239,419` |
| M-6 | CV alpha interpolation дутуу | `server_calculations.py:470-478` |
| M-7 | `db.session.rollback()` exception guard | `database.py:44` |
| M-8 | `to_float()` NaN/Infinity check | `converters.py:9-36` |
| M-9 | `datetime.utcnow()` vs `now_mn()` | `models.py:2307` |
| M-10 | Rate limiter хэт өргөн, in-memory | `__init__.py:45-49` |

---

## LOW

| # | Асуудал | Файл |
|---|---------|------|
| L-1 | `Permissions-Policy` header дутуу | `__init__.py` |
| L-2 | localStorage draft size hard limit | `lims-draft-manager.js:68` |
| L-3 | Password policy 8→12 char | `models.py:158` |
| L-4 | Schema blacklist → whitelist | `analysis_schema.py:83` |
| L-5 | Test code in production | `hardware_fingerprint.py:142` |

---

## Сайн хэрэгжүүлсэн
- ✅ SQLAlchemy ORM (SQL injection-гүй)
- ✅ Flask-Login @login_required бүх route
- ✅ markupsafe.escape() backend XSS
- ✅ Werkzeug password hashing
- ✅ Audit trail + SHA-256 HashableMixin
- ✅ Rate limiting @limiter.limit()
- ✅ begin_nested() + rollback transaction
- ✅ escape_like_pattern() LIKE injection
- ✅ RBAC (admin, senior, analyst)

---

## Засварын явц

| # | Статус | Тайлбар |
|---|--------|---------|
| C-1 | ✅ | CSP unsafe-eval устгасан |
| C-2 | ✅ | innerHTML → textContent (4 файл) |
| C-3 | ✅ | Gi: round ДАРАА дундажлах |
| H-1 | ✅ | FK index нэмсэн (42 багана) |
| H-2 | ✅ | Equipment lazy=True → lazy='dynamic' |
| H-3 | ✅ | MT/MG: stricter is_flat detection |
| H-4 | ✅ | CSN 0.5 increment validation |
| H-5 | ⬜ | License salt (хойшлуулсан) |
| H-6 | ✅ | cascade → save-update,merge + passive_deletes |
| H-7 | ✅ | HW fingerprint: specific exception + logging |
| H-8 | ✅ | Calc error: _calc_error flag + exc_info logging |
| M-1 | ✅ | Error response: str(e) устгасан |
| M-6 | ✅ | CV alpha: linear interpolation нэмсэн |
| M-7 | ✅ | db rollback guard (3 газар) |
| M-8 | ✅ | to_float: NaN/Infinity шалгалт |
| M-9 | ✅ | utcnow → now_mn (License models) |
| L-1 | ✅ | Permissions-Policy + X-Permitted-Cross-Domain-Policies |
| L-2~5 | ⬜ | Хойшлуулсан (draft limit, password, schema, test code) |
