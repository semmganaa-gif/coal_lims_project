# Equipment Code Audit
**Огноо:** 2026-02-05
**Хамрах хүрээ:** Тоног төхөөрөмж, сэлбэг хэрэгсэл, засвар үйлчилгээ

---

## 1. Бүтцийн тойм

### 1.1 Models (app/models.py)
| Model | Мөр | Үүрэг |
|-------|-----|-------|
| Equipment | 640-767 | Төхөөрөмжийн бүртгэл |
| MaintenanceLog | 769-818 | Засвар/калибровкийн бүртгэл |
| UsageLog | 820-865 | Ашиглалтын бүртгэл |
| SparePartCategory | 872-895 | Сэлбэгийн ангилал |
| SparePart | 897-986 | Сэлбэг хэрэгсэл |
| SparePartUsage | 988-1039 | Сэлбэгийн зарцуулалт |
| SparePartLog | 1041-1083 | Сэлбэгийн аудит лог |

### 1.2 Routes
| Файл | Мөр | Үүрэг |
|------|-----|-------|
| `equipment/crud.py` | 523 | CRUD + файл upload |
| `equipment/api.py` | 478 | Usage/maintenance API |
| `equipment/registers.py` | 239 | 7 төрлийн бүртгэл |
| `spare_parts/crud.py` | 634 | Сэлбэг CRUD |
| `spare_parts/api.py` | 273 | Сэлбэг API |

### 1.3 Templates
| Файл | Мөр | Үүрэг |
|------|-----|-------|
| `equipment_list.html` | 655 | Жагсаалт |
| `equipment_detail.html` | 1035 | Дэлгэрэнгүй + засвар бүртгэл |
| `equipment_hub.html` | 312 | Журналын төв |
| `equipment_journal.html` | 671 | Нэгдсэн журнал |
| 6+ register templates | ~1,100 | Тусгай бүртгэлүүд |

---

## 2. Олдсон асуудлууд

### 2.1 MODERATE - SQL Injection риск
**Байршил:** `app/routes/spare_parts/api.py:234-238`
**Түвшин:** MODERATE

```python
# БУРУУ - escape хийгээгүй
spare_parts = SparePart.query.filter(
    (SparePart.name.ilike(f'%{q}%')) |
    (SparePart.name_en.ilike(f'%{q}%')) |
    (SparePart.part_number.ilike(f'%{q}%'))
).limit(20).all()
```

**Засах:** `escape_like_pattern()` ашиглах

---

### 2.2 MODERATE - Image upload path traversal
**Байршил:** `app/routes/spare_parts/crud.py:26-43`
**Түвшин:** MODERATE

```python
def save_image(file):
    # filename нь UUID тул аюулгүй
    # Гэхдээ realpath шалгалт нэмэх нь зүйтэй
    filename = f"{uuid.uuid4().hex}.{ext}"
```

**Статус:** ✅ UUID ашигласан тул аюулгүй, гэхдээ realpath шалгалт нэмвэл сайн.

---

### 2.3 LOW - API response format зөрүү
**Байршил:** Олон API endpoint

```python
# equipment/api.py - {"status": "success", "count": ...}
return jsonify({"status": "success", "count": count})

# spare_parts/api.py - {"success": True, "message": ...}
return jsonify({'success': True, 'message': ...})
```

**Санал:** Нэг стандарт ашиглах (`api_success`, `api_error`)

---

### 2.4 LOW - Pagination дутуу
**Байршил:** `equipment/api.py:447-476` - `api_equipment_list_json()`

```python
equipments = Equipment.query.order_by(Equipment.name.asc()).all()
# Pagination байхгүй - бүх equipment ачаална
```

---

### 2.5 LOW - Retired filter дутуу
**Байршил:** `equipment/api.py:447-476`

```python
# Retired төхөөрөмж бас буцаагдаж байна
equipments = Equipment.query.order_by(Equipment.name.asc()).all()
# .filter(Equipment.status != 'retired') нэмэх
```

---

### 2.6 LOW - Import inside function
**Байршил:** `equipment/api.py:183`, `spare_parts/api.py:103,179`

```python
# Function дотор import - байж болно гэхдээ дээрээс нь байвал илүү
from app.models import SparePart, SparePartUsage, SparePartLog
```

---

### 2.7 INFO - Аудит логд hash дутуу
**Байршил:** `spare_parts/crud.py:54-66`

```python
def log_spare_part_action(...):
    log = SparePartLog(...)
    db.session.add(log)
    # data_hash тооцоолоогүй
```

**Санал:** SparePartLog модел дээр hash field нэмэх (ISO 17025)

---

## 3. Сайн талууд ✅

### 3.1 Аюулгүй байдал
- ✅ File upload - secure_filename + size check + extension check
- ✅ Path traversal check (`add_maintenance_log`, `download_certificate`)
- ✅ Role-based access control бүх route дээр
- ✅ Cascade delete Equipment → MaintenanceLog
- ✅ Audit logging (`log_audit()`) бараг бүх CRUD үйлдэлд

### 3.2 Бизнес логик
- ✅ Calibration tracking - автомат next_calibration_date
- ✅ Status transitions (calibration → normal, repair → maintenance)
- ✅ Spare parts integration - засвар бүртгэлтэй холбосон
- ✅ Inventory auto-update - `update_status()` method

### 3.3 Код чанар
- ✅ Error handling + rollback
- ✅ Flash messages хэрэглэгчид
- ✅ Logging (`current_app.logger.error`)
- ✅ Shift date handling (`get_shift_date()`)

---

## 4. Засах дараалал

### Яаралтай - ДУУССАН ✅
1. ✅ SQL Injection fix - `api_search()` escape (`spare_parts/api.py`)

### Дунд хугацаа - ДУУССАН ✅
2. ✅ API response format нэгтгэх - `equipment/api.py` (`api_success`, `api_error`)
3. ✅ `api_equipment_list_json()` retired filter + limit нэмсэн (`equipment/api.py`)
4. ⏸️ Image save path validation (UUID ашиглаж байгаа тул аюулгүй)

### ISO 17025 - ДУУССАН ✅
5. ✅ SparePartLog hash field - `models.py` (`data_hash`, `compute_hash()`, `verify_hash()`)
6. ✅ Imports дээрээс нь болгох - `equipment/api.py`, `spare_parts/api.py`

---

## 5. Статистик

| Хэмжүүр | Утга |
|---------|------|
| Нийт файл | 10+ |
| Нийт мөр | ~4,000+ |
| Model | 7 |
| Route функц | 30+ |
| Template | 15+ |
| Test файл | 7 (2,491 мөр) |

---

## 6. Equipment категориуд (8)

| Код | Монгол нэр |
|-----|-----------|
| furnace | Шатаах зуух |
| prep | Дээж бэлтгэл |
| analysis | Шинжилгээний багаж |
| balance | Жин |
| water | Усны лаб |
| micro | Микроскоп |
| wtl | WTL лаб |
| other | Бусад |

---

## 7. Equipment статус (5)

| Код | Монгол нэр | Тайлбар |
|-----|-----------|---------|
| normal | Хэвийн | Ажиллаж байгаа |
| broken | Эвдэрсэн | Ажиллахгүй |
| needs_spare | Сэлбэг хэрэгтэй | Сэлбэг солих |
| maintenance | Засварт | Засварлаж байгаа |
| retired | Ашиглалтаас гарсан | Хуучирсан |

---

*Шинжилгээг хийсэн: Claude Code*
*Огноо: 2026-02-05*
