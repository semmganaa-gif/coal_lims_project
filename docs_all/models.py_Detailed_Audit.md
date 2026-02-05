# models.py Detailed Audit
**Огноо:** 2026-02-05
**Файл:** `app/models.py` (3,174 мөр, 45 класс)

---

## 1. Бүтцийн тойм

### 1.1 Classes (45 ширхэг)
| Бүлэг | Классууд |
|-------|----------|
| User/Auth | User, AuditLog |
| Sample | Sample, AnalysisResult, AnalysisType, AnalysisProfile, AnalysisResultLog |
| Equipment | Equipment, MaintenanceLog, UsageLog |
| Spare Parts | SparePartCategory, SparePart, SparePartUsage, SparePartLog |
| Chemicals | Chemical, ChemicalUsage, ChemicalLog, ChemicalWaste, ChemicalWasteRecord |
| QC | ControlStandard, GbwStandard, QCControlChart, ProficiencyTest, EnvironmentalLog |
| Reports | LabReport, ReportSignature |
| Solutions | SolutionPreparation, SolutionRecipe, SolutionRecipeIngredient |
| Yield | WashabilityTest, WashabilityFraction, TheoreticalYield, PlantYield |
| System | SystemSetting, SystemLicense, LicenseLog, StaffSettings, MonthlyPlan |
| Other | Bottle, BottleConstant, CorrectiveAction, CustomerComplaint, ChatMessage, UserOnlineStatus |
| Helper | SampleCalculations (plain class, not db model) |

### 1.2 Импорт статистик
| Импорт | Ашиглалт |
|--------|----------|
| `db` | ✅ Бүх model-д |
| `datetime` | ✅ |
| `Optional, Dict, Any, List` | ✅ Type hints |
| `generate_password_hash, check_password_hash` | ✅ User model |
| `UserMixin` | ✅ User model |
| `Date, Text` | ✅ |
| `CheckConstraint` | ✅ Sample model |
| `validates` | ✅ Sample.validate_sample_code |
| `re` | ✅ Sample.validate_sample_code |
| `json` | ✅ JSON талбарууд |
| `now_mn` | ✅ Timestamp defaults |
| `FLOAT_EPSILON` | ✅ SampleCalculations |

**Үр дүн:** Ашиглаагүй импорт байхгүй ✅

---

## 2. Давхардсан код

### 2.1 `compute_hash()` / `verify_hash()` - 4 удаа
**Түвшин:** MODERATE (refactoring боломж)

| Model | Мөр | Талбарууд |
|-------|-----|-----------|
| SparePartLog | 1084-1102 | spare_part_id, action, quantity_*, user_id, timestamp, details |
| AnalysisResultLog | 1420-1437 | sample_id, analysis_code, action, raw_data_*, final_result_*, timestamp |
| AuditLog | 1745-1762 | user_id, action, resource_type, resource_id, timestamp, details, ip_address |
| ChemicalLog | 2711-2729 | chemical_id, action, quantity_*, user_id, timestamp, details |

**Санал:** `HashableMixin` класс үүсгэж давхардлыг арилгах

```python
# app/models/mixins.py
class HashableMixin:
    """ISO 17025 audit log integrity mixin."""
    data_hash = db.Column(db.String(64), nullable=True)

    @property
    def _hash_fields(self) -> tuple:
        """Override in subclass."""
        raise NotImplementedError

    def compute_hash(self) -> str:
        import hashlib
        data = '|'.join(str(getattr(self, f, '')) for f in self._hash_fields)
        return hashlib.sha256(data.encode('utf-8')).hexdigest()

    def verify_hash(self) -> bool:
        if not self.data_hash:
            return True
        return self.data_hash == self.compute_hash()
```

**Статус:** ⏸️ Хойшлуулсан (код ажиллаж байгаа)

---

## 3. Ашиглаагүй/Potential dead code

### 3.1 Ашиглаагүй method-ууд

| Класс | Method | Шалтгаан | Статус |
|-------|--------|----------|--------|
| AnalysisProfile | `set_analyses()` | Зөвхөн docstring-д | ⚠️ Шалгах |
| AnalysisProfile | `get_tokens_as_dict()` | UI-д ашиглах гэсэн боловч ашиглаагүй | 🗑️ Устгаж болно |
| Sample | `is_mass_ready` property | `mass_ready` column шууд ашиглагддаг | 🗑️ Устгаж болно |

### 3.2 verify_hash() ашиглалт
`verify_hash()` нь `app/routes/api/audit_api.py:169` дээр ашиглагддаг тул устгах ёсгүй.

---

## 4. Сайн талууд ✅

### 4.1 ISO 17025 Compliance
- ✅ AuditLog - бүх үйлдлийн түүх
- ✅ AnalysisResultLog - шинжилгээний өөрчлөлтийн түүх
- ✅ data_hash - бүртгэлийн бүрэн бүтэн байдал

### 4.2 Relationships
- ✅ Cascade delete (`cascade="all, delete-orphan"`)
- ✅ Foreign key constraints with names
- ✅ Composite indexes for common queries

### 4.3 Validations
- ✅ `@validates('sample_code')` - Кирилл/Latin шалгах
- ✅ Password policy enforcement
- ✅ CheckConstraint for client_name

### 4.4 Docstrings
- ✅ Бүх класс docstring-тэй
- ✅ ISO 17025 холбогдох тайлбарууд

---

## 5. Засах зөвлөмж

### 5.1 Шууд засах (LOW effort)

1. **`get_tokens_as_dict()` устгах** (line 605-627)
   - Ашиглагдаагүй
   - ~23 мөр хэмнэнэ

2. **`is_mass_ready` property устгах** (line 275-283)
   - `sample.mass_ready` шууд ашиглаж болно
   - ~9 мөр хэмнэнэ

### 5.2 Хойшлуулах (MEDIUM effort)

1. **HashableMixin үүсгэх**
   - 4 model-д давхардсан код (~80 мөр) → 1 mixin (~20 мөр)
   - Ашиг: ~60 мөр хэмнэнэ, засвар нэг газарт

2. **SampleCalculations-г тусад нь файл руу зөөх**
   - Одоо: `models.py` дотор (line 1113-1340)
   - Санал: `app/utils/sample_calculations.py`
   - Ашиг: models.py-г ~227 мөрөөр богиносгоно

---

## 6. Хураангуй статистик

| Хэмжүүр | Утга |
|---------|------|
| Нийт мөр | 3,174 |
| Классын тоо | 45 |
| Давхардсан pattern | 1 (compute_hash x4) |
| Ашиглаагүй import | 0 |
| Ашиглаагүй method | 2-3 |
| Зөвлөмж тоо | 4 |

---

## 7. Төлөв

| # | Асуудал | Түвшин | Статус |
|---|---------|--------|--------|
| 1 | `get_tokens_as_dict()` | LOW | 🔧 Устгах |
| 2 | `is_mass_ready` property | LOW | 🔧 Устгах |
| 3 | HashableMixin refactor | MEDIUM | ⏸️ Хойшлуулах |
| 4 | SampleCalculations зөөх | MEDIUM | ⏸️ Хойшлуулах |

---

*Шинжилгээг хийсэн: Claude Code*
*Огноо: 2026-02-05*
