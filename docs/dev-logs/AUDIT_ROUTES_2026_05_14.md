# AUDIT — Routes давхарга (2026-05-14)

> **Хамрах хүрээ:** `app/routes/` — 63 файл, **14 572 мөр**.
> **Фокус:** Authentication/authorization decorators, давхарга алгасах
> (db.session/Model.query), input validation, XSS/CSRF, security pattern,
> i18n.
> **Шалгасан:** Opus 4.7. Хэмжээний улмаас 5 файлыг бүрэн уншсан
> (`admin/routes.py` partial, `chat/events.py`, `equipment/crud.py`,
> `api/analysis_save.py`, `main/index.py` partial), бусдыг grep + sample read-ээр.

---

## 1. Хураангуй

Routes давхарга нь:

- ✅ **151 `@login_required`** — нэвтрэх хамгаалалт өргөн ашиглагдсан.
- ✅ XSS escape (`markupsafe.escape`), path traversal check, file extension
  whitelist, `secure_filename()` — security awareness сайн.
- ✅ Repos болон Services-ийг **зарим routes ашигладаг** (Sample Service-аар
  амжилттай орлуулагдсан).

Гэвч:

- ⚠️ **CLAUDE.md-д заасан `app/security/` directory ОГТ БАЙХГҮЙ** — decorator-ууд
  `app/utils/decorators.py`-д шилжсэн ч documentation-д тэр хэвээр.
- ⚠️ **3 өөр `admin_required` definition** code-д давтан тодорхойлогдсон.
- ⚠️ **`app/utils/decorators.py`-ийн 3 decorator (admin_required, role_required,
  role_or_owner_required) бүгдээрээ DEAD CODE** — хэн ч import хийдэггүй.
- ⚠️ Routes-д **167 `db.session.*` call** + **106 `Model.query.*`** — layer
  алгасах олон газар.
- ⚠️ Inline `current_user.role not in [...]` шалгалт **45+ газар** — `@role_required`-ийг
  ашиглах боломжтой ч хэрэглээгүй.

| Severity | Тоо |
|----------|-----|
| 🟥 High | 2 |
| 🔴 Medium | 11 |
| 🟡 Low | 8 |
| ⚪ Nit | 6 |
| ℹ️ Info / acceptable | 5 |

---

## 2. 🟥 High severity

### H1 · `app/security/` directory **БАЙХГҮЙ** — CLAUDE.md худал зөвлөмж

**CLAUDE.md дотор:**
```
├── security/       # decorators (@lab_required, @role_required), license, fingerprint
```

**Бодит байдал:**
```bash
$ ls app/security/
ls: cannot access 'app/security/': No such file or directory
```

Decorator-ууд `app/utils/decorators.py`-д амьдрана. Лиценз дотор
`app/utils/license_protection.py`-д байж магадгүй (Bootstrap audit-аар).
"Fingerprint" нь `app/utils/fingerprint.py` эсвэл өөр газар.

**Үр дагавар:**
- Шинэ developer CLAUDE.md уншихад буруу зам хайна.
- "Where do I add a new decorator?" асуултанд буруу хариу.
- Memory-ийн `april_22_audit_session.md` тэмдэглэлд бас тэр хэвээр.

**Засвар:** CLAUDE.md-ийг шинэчлэх. Эсвэл `app/security/__init__.py` дотор
re-export pattern (`from app.utils.decorators import *`) хийж зөвлөмж зөв
болгох.

> **Engineering principle "perfect over fast" дагуу:** decorator-ууд logically
> security-ийн ажил тул `app/security/decorators.py`-руу шилжүүлэх нь зөв уг.

---

### H2 · **Гурван өөр `admin_required` decorator тодорхойлогдсон + 3 нь dead code**

**Definitions:**

1. `app/utils/decorators.py:56 admin_required` — `flash` + `redirect` өгдөг UX-той
2. `app/routes/admin/routes.py:50 admin_required` — `abort(403)` шууд буцаах (local)
3. `app/routes/api/audit_api.py:34 _audit_admin_required` — мөн локаль (local)

**Хэрэглээ:**
```bash
$ grep -rn "from app.utils.decorators import" app/routes/
# 'admin_required' import-ыг хэн ч хийдэггүй
# Зөвхөн `analysis_role_required` (3 газар) + `lab_required` (7 газар)
```

**`app/utils/decorators.py` доторх dead code:**
- `admin_required` (line 56) — import-гүй
- `role_required` (line 14) — import-гүй
- `role_or_owner_required` (line 87) — import-гүй

**Үр дагавар:**

1. Маргаан үүсэх:
   - `admin/routes.py:75` `@admin_required` — энэ local.
   - Хэн нэг `@admin_required` бичих гэвэл `from .routes import admin_required`
     гэх үү эсвэл `from app.utils.decorators import admin_required` гэх үү?

2. Bug-ийн ялгаа:
   - Local `admin_required` (admin/routes.py:54): `if not current_user.is_authenticated or current_user.role != 'admin': abort(403)`
   - utils `admin_required` (utils/decorators.py:79): мөн адил гэвч `flash(...)` + `redirect(...)` өгдөг (төстэй боловч UX ялгаатай)

3. Inline role check 45+ газар:
   ```python
   if current_user.role not in ["senior", "manager", "admin"]:
       flash("Эрх хүрэлцэхгүй байна.", "danger")
       return redirect(...)
   ```
   `@role_required('senior', 'manager', 'admin')`-ыг ашиглах боломжтой ч хэрэглээгүй.

**Засвар:**
1. Local `admin_required` (admin/routes.py + audit_api.py)-аас устгах.
2. Бүх route `from app.utils.decorators import admin_required`-аар импорт хийх.
3. Inline role check-ийг `@role_required(...)`-аар орлуулах.
4. Эсвэл `app/security/decorators.py`-руу нэгтгэх (H1-тэй хамт).

---

## 3. 🔴 Medium severity

### M1 · Routes-д **167 `db.session.*` call** — CLAUDE.md note баталгаажсан

```bash
$ grep -c "db\.session\." app/routes -r | awk -F: '{s+=$2} END {print s}'
167
```

CLAUDE.md-д "196 db.session call-site" гэж заасан. Бид 167 олсон (29 цөөн —
зарим нь Repository-руу шилжсэн байж магадгүй).

**Хамгийн их зөрчилтэй файлууд:**
| Файл | `db.session.*` |
|------|------|
| `chat/events.py` | 20 |
| `reports/pdf_generator.py` | 18 |
| `settings/routes.py` | 10 |
| `equipment/crud.py` | 10 |
| `main/samples.py` | 9 |
| `chemicals/waste.py` | 9 |
| `api/analysis_api.py` | 9 |
| `reports/dashboard.py` | 8 |
| `equipment/registers.py` | 8 |

**Конкрет жишээ — `chat/events.py:126`:**
```python
db.session.add(msg)
try:
    db.session.commit()
except SQLAlchemyError as e:
    db.session.rollback()
    ...
```

`ChatMessageRepository.save(msg)` аль хэдийн бий — хэрэглэгдэхгүй байгаа.

**Засвар:** Sprint 4 — Routes → Repos/Services шилжүүлэх (CLAUDE.md
roadmap-аас).

---

### M2 · Routes-д **106 `Model.query.*` call**

```bash
$ grep -c "\.query\." app/routes -r | awk -F: '{s+=$2} END {print s}'
106
```

**Хамгийн зөрчилтэй:**
| Файл | `.query.*` |
|------|------|
| `analysis/workspace.py` | 12 |
| `reports/pdf_generator.py` | 10 |
| `api/chat_api.py` | 10 |
| `admin/routes.py` | 7 |
| `reports/crud.py` | 6 |
| `analysis/qc.py` | 6 |
| `equipment/crud.py` | 5 |
| `chemicals/waste.py` | 5 |
| `api/morning_api.py` | 5 |
| `api/audit_api.py` | 5 |

`admin/routes.py:95, 100, 112` — `User.query.order_by(User.id).all()` — `UserRepository.get_all()` бий боловч ашиглагдаагүй.

---

### M3 · Inline `current_user.role not in [...]` — **45+ газар** (decorator байтал ашиглаагүй)

```bash
$ grep -c "current_user\.role not in\|current_user\.role ==" app/routes -r
spare_parts/crud.py: 7
reports/crud.py: 5
main/samples.py: 5
api/instrument_api.py: 5
equipment/crud.py: 4
chemicals/crud.py: 4
equipment/registers.py: 3
chemicals/waste.py: 3
... (total 45+)
```

**Жишээ — `equipment/crud.py:238`:**
```python
@equipment_bp.route("/add_equipment", methods=["POST"])
@login_required
def add_equipment():
    if current_user.role not in ["senior", "manager", "admin"]:
        flash("Эрх хүрэлцэхгүй байна.", "danger")
        return redirect(url_for("equipment.equipment_list"))
    ...
```

`@role_required('senior', 'manager', 'admin')` (`app/utils/decorators.py:14`) аль хэдийн бий — гэхдээ
H2-ын тулгуурт dead code.

**Засвар:**
```python
@equipment_bp.route("/add_equipment", methods=["POST"])
@login_required
@role_required('senior', 'manager', 'admin')
def add_equipment():
    ...
```

---

### M4 · `app/utils/decorators.py:56–129` — **3 decorator dead code**

```bash
$ grep -rn "from app.utils.decorators import" app/
# admin_required, role_required, role_or_owner_required — НЭГ Ч ИМПОРТ БАЙХГҮЙ
```

| Decorator | Тодорхойлсон | Импорт хийсэн |
|-----------|--------------|---------------|
| `role_required` | utils/decorators.py:14 | 0 газар |
| `admin_required` | utils/decorators.py:56 | 0 газар |
| `role_or_owner_required` | utils/decorators.py:87 | 0 газар |
| `lab_required` | utils/decorators.py:132 | 7 газар (labs/) |
| `analysis_role_required` | utils/decorators.py:162 | 3 газар (routes/analysis/) |

50%+ decorator dead code. Test coverage ч мөн биш магадтай.

---

### M5 · `api/analysis_save.py:42` — **`async def` route handler-тэй sync DB call**

```python
@bp.route("/save_results", methods=["POST"])
@login_required
@limiter.limit("100 per minute")
async def save_results():        # ← async
    ...
    with db.session.begin_nested():    # ← sync DB
        result_info, err = save_single_result(...)
    ...
    db.session.commit()                # ← sync DB
```

Flask `async def` route нь `asgiref`-ээр sync wrapper болж ажилладаг.
`db.session.commit()` нь блок-олох call. Async benefit:

- Concurrent I/O (HTTP-ийн зэргэлдээ хүсэлт нэг threaded loop дотор) — Flask
  sync-аар л явдаг тул **ашиггүй**.
- Database operation idle хийгээгүй — async буюу sync үр ажиллагаа адил.

`async def` олох цорын хоёр route нь `analysis_save.py:42, 135`.

**Засвар:** `async`-ийг устгах (sync def). Хэрэв concurrent network call (HTTP
client, Celery dispatch) хийдэг бол flask `await`-аар утга бий. Одоо DB-аас өөр
async I/O байхгүй.

---

### M6 · `audit_api.py:34` — Локаль `_audit_admin_required` decorator (третий)

H2-ын үргэлжлэл. `audit_api.py` дотор:

```python
def _audit_admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        ...
```

Гурван өөр газар `admin_required` тодорхойлогдсон. DRY зөрчил.

---

### M7 · API endpoints **Mongolian-only response**

```bash
$ grep -c "jsonify.*['\"][А-Яа-яӨөҮү]" app/routes/api/
analysis_api.py: 6
chat_api.py: 6
instrument_api.py: 6
analysis_save.py: 4
simulator_api.py: 4
sla_api.py: 7
workflow_api.py: 10
```

Жишээ:
```python
return jsonify({"message": "Шинжилгээний үр дүн хадгалах эрхгүй"}), 403
```

User.language column-д 'en' бий. Mongolian-only API response → English UI
ажиллахгүй.

`flask_babel.lazy_gettext()` ашиглах:
```python
return jsonify({"message": _l("You do not have permission to save analysis results")}), 403
```

---

### M8 · Inline role check `getattr(current_user, "role", None)` — **fail-open**

```python
# analysis_save.py:42, 136
if getattr(current_user, "role", None) not in ("chemist", "senior", "admin"):
    return jsonify({...}), 403
```

`getattr(current_user, "role", None)` нь хэрэв `current_user.role` байхгүй
бол `None`-ийг буцаана. `None not in (...)` нь **True** тул 403 явна — fail-closed,
зөв.

Гэвч `current_user.is_anonymous` (нэвтрэлгүй) үед AnonymousUserMixin нь
`role` атрибутгүй — `getattr(..., None)` нь None. 403 buцаана — зөв уг.

`@login_required` decorator already идэвхтэй тул хоёр давхар хамгаалалт. **OK**
гэхдээ оптимизаци хэрэгтэй (`@role_required`-аар нэг газраас удирдах).

---

### M9 · `chat/events.py` — `ChatMessageRepository`, `UserRepository` хэсэгчлэн ашиглагдсан

```python
# Line 104, 112: Repository ашигласан
receiver = UserRepository.get_by_id(receiver_id)
sample = SampleRepository.get_by_id(sample_id)

# Line 126, 304-312: Repository байхгүй гэдэг шиг direct query
db.session.add(msg)
db.session.commit()

unread = ChatMessage.query.filter(...).all()
```

`ChatMessageRepository.save(msg)`, `mark_as_read(message_ids)`, `soft_delete(msg)`
бүгд бий. Зарим method ашигласан, заримд алгассан. Inconsistent.

---

### M10 · `equipment/crud.py:289` — `MaintenanceLog.query.filter_by` (Repos audit H1-той холбоотой)

```python
has_history = (
    MaintenanceLog.query.filter_by(equipment_id=eq.id).first()
    or UsageLog.query.filter_by(equipment_id=eq.id).first()
)
```

`MaintenanceLogRepository.has_records(equipment_id)` бий — гэхдээ ашиглахгүй,
шууд query хийсэн. Тэгээд `MaintenanceLogRepository.get_by_equipment(...)` руу
очдоггүй (`maintenance_date` typo bug тойруулсан байж магадгүй?).

---

### M11 · `main/index.py:76` — `Sample.status == 'completed'` filter (Services M11-тэй холбоотой)

```python
# main/index.py:76
.filter(Sample.lab_type == 'coal', Sample.status == 'completed')
```

Services audit M11 баталгаажсан:
- `workflow_engine.py:510` дотор `sample.status = 'completed'` set хийгддэг (via `_hook_check_sample_complete` hook).
- Hook нь `on_enter_approved` event-аар л дуудагдана (workflow_engine.py:152).
- Үр дүнд: AnalysisResult-аар бүх result approved үед → check_sample_complete fires → sample.status = 'completed'.
- `main/index.py:76` filter ажиллах ёстой.

**Учир:** Services audit M11 одоо resolved — completed status хэдийгээр **workflow_engine
дамжуулан** set хийгддэг. Гэхдээ workflow_engine role mismatch (Services H1)-ийн
улмаас chemist user-ийн approval flow эвдрэхэд hook firing эвдэрнэ.

---

## 4. 🟡 Low severity

### L1 · `chat/events.py:229` — `msg.message = "Мессеж устгагдсан"` — destructive update

```python
@socketio.on('delete_message')
def handle_delete_message(data):
    ...
    msg.is_deleted = True
    msg.deleted_at = now_mn()
    msg.message = "Мессеж устгагдсан"   # ← Original устгагдсан!
```

Soft delete-ийн логик `is_deleted` flag-ээр л байх ёстой. Original `message`
тексыг хадгалах нь:
- Audit/forensics-д шаардлагатай (хэн юу хэлсэн)
- Хэрэглэгчийн өөрийн undo боломжтой

**Засвар:** `msg.message`-ийг хэвээр үлдээх. UI/template-д `is_deleted=True` бол
"Мессеж устгагдсан" гэж харуулах.

---

### L2 · `equipment/crud.py:188` — `paginate(per_page=500, ...)` нь маш том page size

```python
pagination = query.order_by(Equipment.name.asc()).paginate(
    page=page, per_page=500, error_out=False
)
```

500 row нэг хуудсанд буцаах нь:
- Memory load 50K Equipment бэлжсэн үед.
- AG Grid/DataTables client-side render slow.

**Зөвлөмж:** `per_page=50` болгож, infinite scroll эсвэл server-side
DataTables ашиглах.

---

### L3 · Auth check inconsistency — flash+redirect vs abort(403)

```python
# admin/routes.py:54 (local admin_required)
abort(403)

# equipment/crud.py:238 (inline)
flash("Эрх хүрэлцэхгүй байна.", "danger")
return redirect(url_for("equipment.equipment_list"))
```

UX-ийн ялгаа:
- `abort(403)` — `errors/403.html` template харуулна.
- `flash + redirect` — toast notification + redirect.

Convention сонгох. SPA flow-той бол `abort(403)` дээр template нэмэх илүү
консистенц.

---

### L4 · Path traversal check тогтмол давтан pattern

`equipment/crud.py:476–481, 506–511` — хоёр газар ижил pattern:

```python
real_path = os.path.realpath(full_path)
real_upload = os.path.realpath(upload_folder)
if not real_path.startswith(real_upload):
    current_app.logger.warning(f"Path traversal attempt: ...")
    flash(...)
    return ...
```

`app/utils/security.py`-руу `validate_upload_path(filename, upload_dir)` helper-аар нэгтгэх.

---

### L5 · API success messages-д hard-coded Mongolian

```python
# analysis_save.py:123
"message": f"{saved_count} мөр амжилттай хадгалагдлаа, {failed_count} алдаа."
```

I18n зөрчил (M7-той хамт).

---

### L6 · `chat/events.py:148` — `receiver.username if receiver else 'self'`

```python
logger.info(f"Message sent: {current_user.username} -> {receiver.username if receiver else 'self'}")
```

`if receiver else 'self'` нь буруу нэр — receiver=None үед broadcast үед эсвэл
тодорхой бус. 'broadcast' эсвэл 'unknown' гэж нэрлэх нь зөв.

---

### L7 · `analysis_save.py:53–57` — Magic number `MAX_BATCH_SIZE = 500`

```python
MAX_BATCH_SIZE = 500
...
if len(data) > MAX_BATCH_SIZE:
    return jsonify({
        "message": f"Нэг удаад {MAX_BATCH_SIZE}-аас их мөр хадгалах боломжгүй."
    }), 400
```

`app/constants.py`-руу шилжүүлэх. Тестэд config-аар override хийх боломжтой
байх.

---

### L8 · `chat/events.py:27` — Process-level state `online_users` dict

```python
online_users = {}  # {user_id: socket_id}
_online_lock = Lock()
```

Multi-worker (gunicorn-тэй) орчинд **тус бүр процесст ondhik dict**. Worker A-д
холбогдсон user-ийг Worker B мэдэхгүй.

`UserOnlineStatus` DB table-аас уншсан нь ажиллах ёстой (line 367), гэвч
`online_users` dict-д давхар хадгалсан нь зорилгогүй duplication.

**Засвар:** `online_users` dict устгаж зөвхөн DB-аас уншуулах. Эсвэл Redis
shared state ашиглах.

---

## 5. ⚪ Nit / стилийн зөрчил

### N1 · `chat/events.py:138, 145` — `if receiver_id:` нь 0-ыг falsy гэж үздэг

`receiver_id=0` нь хэвийн user_id биш ч, type-safety алга. Convention `if
receiver_id is not None and receiver_id > 0:` илүү тодорхой.

---

### N2 · Path-аар хийсэн `os.makedirs(upload_folder, mode=0o755)` (line 474) — directory permission зориуд set

OK, гэхдээ Windows-д mode flag нөлөөгүй. Cross-platform-д документлэх.

---

### N3 · `analysis_save.py:127` — Response status code `207` (Multi-Status)

```python
status_code = 200 if failed_count == 0 else 207
return jsonify(response_data), status_code
```

HTTP 207 нь WebDAV multi-status. REST API-д нийтлэг ашиглагдсан, OK гэхдээ
тэмдэглэлд бичих.

---

### N4 · `equipment/crud.py:467` — Allowed extensions string concat

```python
flash(f"Файлын төрөл зөвшөөрөгдөөгүй (.{ext}). Зөвшөөрөгдөх: {', '.join(ALLOWED_EXTENSIONS)}", "danger")
```

`ALLOWED_EXTENSIONS` нь `set` эсвэл `frozenset` байх магадлалтай — `', '.join`
зөвлөмжтэй ч ordering nondeterministic. UI-д дараалал хэлбэртэй харагдах
нь зөв уг.

---

### N5 · `admin/routes.py:50–67` — `wraps` import inside function-ээс гадуур

```python
import logging
from functools import wraps
```

OK, гэвч decorator definition нь module-level. Хэрэв utils/decorators-аар
импорт хийвэл `wraps`-г огт хэрэглэхгүй.

---

### N6 · `chat/events.py:174` — `message_text = str(_esc(data.get('message', file_name or 'File')))`

`file_name or 'File'` хоосон нэр default 'File'. Localization-д "File" мөн
зөвлөмж.

---

## 6. ℹ️ Info / acceptable / сайн pattern

- **I1 · Path traversal check** (equipment/crud.py:476, 506) — security awareness сайн.
- **I2 · `secure_filename()` + extension whitelist** (equipment/crud.py:461) — нэгэн
  стандарт upload pattern.
- **I3 · `markupsafe.escape` input-д хэрэглэсэн** (chat/events.py:92, 173) — XSS
  хамгаалалт.
- **I4 · `csp_nonce` template-д ашиглагдсан** (CSP audit-аас уламжилсан).
- **I5 · 151 `@login_required`** — нэвтрэх хамгаалалт хүчтэй.

---

## 7. Дараагийн алхам

| № | Үйлдэл | Severity | Тэрчлэн |
|---|--------|----------|--------|
| 1 | **H1** — `app/security/` directory үүсгэх эсвэл CLAUDE.md шинэчлэх | 🟥 High | 1 commit |
| 2 | **H2** — `admin_required` нэг газраас удирдах (utils/decorators) + dead code устгах | 🟥 High | 1 commit |
| 3 | M1, M2 — Routes-аас `db.session.*` / `Model.query` устгаж Repos/Services-руу шилжүүлэх (Sprint 4) | 🔴 Medium | Том sprint |
| 4 | M3 — Inline role check 45+ газрыг `@role_required(...)`-аар орлуулах | 🔴 Medium | 2–3 commit |
| 5 | M4 — `role_required`, `role_or_owner_required` dead code эзэмшил тогтоох | 🔴 Medium | M3-той хамт |
| 6 | M5 — `async def` устгах (`analysis_save.py`) | 🔴 Medium | 1 commit |
| 7 | M6 — `_audit_admin_required` устгаж utils ашиглах | 🔴 Medium | H2-той хамт |
| 8 | M7 — API jsonify response-уудыг `lazy_gettext()`-ээр орчуулах | 🔴 Medium | Том sprint |
| 9 | M9, M10 — Repository ашиглалт routes-д бүрэн нэвтрүүлэх | 🔴 Medium | M1-тэй хамт |
| 10 | M11 — Services audit M11 хариулагдсан — `'completed'` нь workflow_engine-аар set хийгддэг | ✅ Done (info) | — |
| 11 | L1–L8 — Soft delete fix, pagination, path helper, etc. | 🟡 Low | 2 commit |
| 12 | N1–N6 — Style fixes | ⚪ Nit | 1 commit |

**Зөвлөмж:** H1 → H2 → M3+M4+M6 (decorator цэвэрлэгээ) → M5 → бусад. Том sprint
4–5 нь сэргээх ажил.

---

## 8. Энэ audit-ын хамрах хүрээний дүгнэлт

✅ **Бүрэн уншсан:** 5 файл (~1 800 мөр).

📊 **Pattern-аар шалгасан:** 58 файл (~12 700 мөр).

⚠️ **Хамгийн чухал олдвор:**
- **H2** — Гурван өөр `admin_required` definition байгаа нь үнэхээр төөрөгдмөл
  байдал үүсгэдэг. CLAUDE.md-д "@lab_required, @role_required" гэж заасан
  decorators-ийн **role_required нь dead code**.
- **M11 = Services H1+M11 resolved** — `'completed'` status workflow_engine
  hook-аар set хийгддэг. Гэхдээ workflow role mismatch (Services H1)-ийг
  засахгүй бол hook firing chemist user-аас эвдэрнэ.

🔍 **Дараагийн алхам** — Labs давхарга (4 лаб: coal, water_chemistry,
microbiology, petrography).
