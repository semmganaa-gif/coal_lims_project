# Code Duplication & Unused Code Audit
**Огноо:** 2026-02-05
**Хамрах хүрээ:** Давхардсан код, ашиглаагүй импорт, refactoring боломж

---

## 1. Шалгасан файлууд (Хамгийн том)

| # | Файл | Мөрийн тоо |
|---|------|------------|
| 1 | `app/models.py` | 3,174 |
| 2 | `app/labs/water_lab/chemistry/routes.py` | 1,898 |
| 3 | `app/routes/report_routes.py` | 1,576 |
| 4 | `app/constants.py` | 1,070 |
| 5 | `app/utils/server_calculations.py` | 1,048 |

---

## 2. Давхардсан код

### 2.1 `compute_hash()` / `verify_hash()` - 4 удаа давхардсан
**Түвшин:** MODERATE (refactoring opportunity)

**Байршлууд:**
| Model | Мөр |
|-------|-----|
| SparePartLog | 1084-1102 |
| AnalysisResultLog | 1420-1437 |
| AuditLog | 1745-1762 |
| ChemicalLog | 2711-2729 |

**Асуудал:** Ижил pattern бүхий код 4 удаа давтагдсан:
```python
def compute_hash(self) -> str:
    import hashlib
    data = f"{self.field1}|{self.field2}|..."
    return hashlib.sha256(data.encode('utf-8')).hexdigest()

def verify_hash(self) -> bool:
    if not self.data_hash:
        return True
    return self.data_hash == self.compute_hash()
```

**Санал:** Mixin class үүсгэх:
```python
class HashableMixin:
    data_hash = db.Column(db.String(64), nullable=True)

    def _get_hash_fields(self) -> list:
        raise NotImplementedError

    def compute_hash(self) -> str:
        import hashlib
        data = '|'.join(str(getattr(self, f, '')) for f in self._get_hash_fields())
        return hashlib.sha256(data.encode('utf-8')).hexdigest()

    def verify_hash(self) -> bool:
        if not self.data_hash:
            return True
        return self.data_hash == self.compute_hash()
```

**Статус:** ⏸️ Хойшлуулсан (код ажиллаж байгаа)

---

### 2.2 `parse_float()` - 8 удаа давхардсан
**Түвшин:** MODERATE

**Байршлууд:**
| Файл | Мөр |
|------|-----|
| `spare_parts/crud.py` | 303, 393 |
| `utils/excel_import.py` | 41 (global, pandas-тэй) |
| `water_lab/chemistry/routes.py` | 1258, 1394, 1609, 1761, 1828 |

**Асуудал:** Ижил функц олон газар inline тодорхойлогдсон.

**Шийдэл:** `app/utils/converters.py` дотор `to_float()` функц аль хэдийн байна!

```python
# app/utils/converters.py - EXISTING
def to_float(v: Any) -> Optional[float]:
    """Утгыг float болгох. Буруу утгад None буцаана."""
    # ... илүү олон edge case handle хийдэг
```

**Санал:** Inline `parse_float()` функцүүдийг `from app.utils.converters import to_float` болгож солих.

**Статус:** ⏸️ Хойшлуулсан (олон файл өөрчлөх шаардлагатай)

---

### 2.3 Inline role check + flash - 20+ удаа давхардсан
**Түвшин:** LOW

**Pattern:**
```python
if current_user.role not in ["senior", "manager", "admin"]:
    flash("Эрх хүрэхгүй.", "danger")
    return redirect(url_for(...))
```

**Байршлууд:** 20+ газар:
- `reports/crud.py` (5 удаа)
- `chemicals/crud.py` (4 удаа)
- `chemicals/waste.py` (3 удаа)
- `equipment/crud.py` (4 удаа)
- `equipment/registers.py` (3 удаа)
- `spare_parts/crud.py` (9 удаа)

**Санал:** Decorator ашиглах эсвэл helper function:
```python
# utils/auth_helpers.py
def require_role(*roles, redirect_to=None):
    if current_user.role not in roles:
        flash("Эрх хүрэхгүй.", "danger")
        return redirect(url_for(redirect_to or 'main.index'))
    return None
```

**Статус:** ⏸️ Хойшлуулсан (ажиллагаанд нөлөөлөхгүй)

---

## 3. Ашиглаагүй импорт

### 3.1 water_lab/chemistry/routes.py
**Мөр 8:** `AnalysisType` import хийгдсэн боловч ашиглаагүй

```python
from app.models import Sample, AnalysisResult, AnalysisType, Equipment
#                                             ^^^^^^^^^^^^ unused
```

**Статус:** 🔧 Устгах

---

## 4. Код чанарын асуудлууд

### 4.1 Урт функцүүд (100+ мөр)

| Файл | Функц | Мөр |
|------|-------|-----|
| `water_lab/chemistry/routes.py` | `add_solution()` | ~150 |
| `water_lab/chemistry/routes.py` | `edit_solution()` | ~180 |
| `report_routes.py` | `dashboard()` | ~200 |
| `report_routes.py` | `monthly_plan()` | ~150 |

**Санал:** Service layer-д задлах

---

### 4.2 Import inside function (Local imports)

**Байршлууд:** 30+ газар
- `report_routes.py` - олон газар
- `water_lab/chemistry/routes.py` - олон газар

**Жишээ:**
```python
def add_solution():
    from app.models import SolutionPreparation, Chemical  # Inside function
```

**Статус:** ⏸️ Хойшлуулсан (circular import сэргийлж байгаа)

---

## 5. Засах дараалал

| # | Асуудал | Түвшин | Нөлөө | Хугацаа |
|---|---------|--------|-------|---------|
| 1 | `parse_float()` давхардал | MODERATE | 8 файл | 🔧 Засах |
| 2 | Unused import (AnalysisType) | LOW | 1 файл | 🔧 Засах |
| 3 | `compute_hash` mixin | MODERATE | 4 model | ⏸️ Хойшлуулах |
| 4 | Inline role checks | LOW | 20+ газар | ⏸️ Хойшлуулах |
| 5 | Урт функцүүд задлах | LOW | Code quality | ⏸️ Хойшлуулах |

---

## 6. Хураангуй

### Олдсон асуудлууд
| Төрөл | Тоо |
|-------|-----|
| Давхардсан функц | 3 pattern |
| Ашиглаагүй импорт | 1 |
| Урт функц (100+) | 4+ |
| Inline role check | 20+ |

### Шууд засах
1. ✅ `parse_float()` - utils/helpers.py руу зөөх
2. ✅ `AnalysisType` unused import устгах

### Хойшлуулах (Refactoring)
1. HashableMixin class үүсгэх
2. Role check decorator нэгтгэх
3. Урт функцүүдыг service layer-д задлах

---

## 7. Код давхардлын статистик

```
models.py:           compute_hash x4 (4 model)
parse_float:         8 definitions
flash("Эрх хүрэхгүй"): 20+ occurrences
@login_required + role check: 50+ routes
```

---

*Шинжилгээг хийсэн: Claude Code*
*Огноо: 2026-02-05*
