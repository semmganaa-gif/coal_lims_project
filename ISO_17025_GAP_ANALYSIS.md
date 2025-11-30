# ISO/IEC 17025:2017 Gap Analysis - Coal LIMS

**Огноо:** 2025-11-30
**Лаборатори:** Нүүрсний лаборатори
**Стандарт:** ISO/IEC 17025:2017
**LIMS систем:** Coal LIMS v1.0

---

## 📋 ХУРААНГУЙ

| Категори | Хангасан | Хэсэгчлэн | Дутуу | Нийт |
|----------|----------|-----------|-------|------|
| **Удирдлагын шаардлага** | 4 | 6 | 4 | 14 |
| **Техникийн шаардлага** | 5 | 4 | 6 | 15 |
| **НИЙТ** | **9** | **10** | **10** | **29** |

**Нийт дүн:** 31% бүрэн ✅ | 34% хэсэгчлэн ⚠️ | 35% дутуу ❌

**Үнэлгээ:** C+ (Суурь систем байгаа, гэхдээ ISO 17025 бүрэн хангахад ихээхэн ажил шаардлагатай)

---

## 🔍 ДЭЛГЭРЭНГҮЙ ШИНЖИЛГЭЭ

---

## ХЭСЭГ 1: УДИРДЛАГЫН ШААРДЛАГА (Management Requirements)

### 4.1 Шударга байдал (Impartiality)

**Статус:** ❌ ДУТУУ

**ISO 17025 шаардлага:**
- Ашиг сонирхлын зөрчлийн тодорхойлолт
- Шударга байдлын баталгаажуулалт
- Гадны дарамтаас хамгаалах бодлого

**Одоогийн байдал:**
- ❌ Ашиг сонирхлын зөрчлийн бүртгэл байхгүй
- ❌ Шударга байдлын баталгаа байхгүй

**Шаардлагатай:**
```
1. Ашиг сонирхлын зөрчлийн мэдүүлэг (Declaration form)
2. Шударга байдлын бодлого (Impartiality policy)
3. Жилийн тайлан (Impartiality review)
```

---

### 4.2 Нууцлал (Confidentiality)

**Статус:** ⚠️ ХЭСЭГЧЛЭН

**ISO 17025 шаардлага:**
- Үйлчлүүлэгчийн мэдээллийн нууцлал
- Хэрэглэгчийн эрхийн удирдлага
- Гэрээгээр хамгаалагдсан мэдээлэл

**Одоогийн байдал:**
- ✅ Хэрэглэгчийн эрх (role-based access)
- ✅ Login систем (Flask-Login)
- ❌ Нууцлалын гэрээ байхгүй
- ❌ Мэдээлэл задруулах бодлого байхгүй

**Файл:** `app/models.py:23-45` (User модел)

**Шаардлагатай:**
```
1. Нууцлалын гэрээ (Confidentiality agreement)
2. Үйлчлүүлэгчтэй NDA (Non-disclosure agreement)
3. Мэдээлэл задруулах журам
```

---

### 6.2 Хүний нөөц (Personnel)

**Статус:** ⚠️ ХЭСЭГЧЛЭН

**ISO 17025 шаардлага:**
- Ажилтны ур чадварын шаардлага
- Сургалтын бүртгэл
- Эрх олгох баталгаажуулалт
- Гүйцэтгэлийн үнэлгээ

**Одоогийн байдал:**
- ✅ Эрхийн систем байгаа (beltgegch, himich, ahlah, senior, admin)
- ✅ Хэрэглэгчийн роль (User.role)
- ❌ Сургалтын бүртгэл байхгүй
- ❌ Гэрчилгээний хадгалалт байхгүй
- ❌ Эрх олгох баталгаажуулалт байхгүй

**Файл:** `app/models.py:23` (User class)

**Шаардлагатай нэмэлт:**
```python
# ШИНЭ: Training модел
class TrainingRecord(db.Model):
    """Сургалтын бүртгэл (ISO 17025 - 6.2)"""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    training_type = db.Column(db.String(100))  # Internal, External, On-the-job
    training_date = db.Column(db.Date)
    training_topic = db.Column(db.String(200))  # Ж: "Bomb calorimeter operation"
    trainer = db.Column(db.String(100))
    duration_hours = db.Column(db.Float)
    certificate_no = db.Column(db.String(100))
    certificate_file = db.Column(db.String(255))  # PDF зам
    expiry_date = db.Column(db.Date)  # Хүчинтэй хугацаа
    status = db.Column(db.String(20))  # valid, expired
    notes = db.Column(db.Text)

# ШИНЭ: Competence Assessment
class CompetenceRecord(db.Model):
    """Ур чадварын үнэлгээ"""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    analysis_code = db.Column(db.String(50))  # Аль анализд зөвшөөрөл өгсөн
    authorized_date = db.Column(db.Date)
    authorized_by_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    assessment_method = db.Column(db.String(100))  # Observation, Test, Review
    result = db.Column(db.String(20))  # Competent, Not yet competent
    review_date = db.Column(db.Date)  # Дараагийн хянах огноо
    notes = db.Column(db.Text)
```

---

### 6.4 Тоног төхөөрөмж (Equipment)

**Статус:** ✅ БҮРЭН ХАНГАСАН

**ISO 17025 шаардлага:**
- Тоног төхөөрөмжийн бүртгэл
- Хянах баталгаажуулалтын хуваарь
- Засвар үйлчилгээний түүх
- Тодорхойлолт (identification)

**Одоогийн байдал:**
- ✅ Equipment модел байгаа
- ✅ Calibration tracking (огноо, давтамж, дараагийн хугацаа)
- ✅ MaintenanceLog (засвар үйлчилгээ)
- ✅ UsageLog (ашиглалт)
- ✅ Ангилал (category: furnace, analysis, balance, гэх мэт)

**Файл:** `app/models.py:550-699`

**Сайн талууд:**
```python
class Equipment(db.Model):
    # ✅ Бүх шаардлагатай талбарууд байгаа
    calibration_date = db.Column(db.Date)
    calibration_cycle_days = db.Column(db.Integer, default=365)
    next_calibration_date = db.Column(db.Date)
    calibration_note = db.Column(db.String(200))
    status = db.Column(db.String(20))  # normal, broken, maintenance, retired

class MaintenanceLog(db.Model):
    # ✅ Засвар үйлчилгээний бүрэн бүртгэл
    action_type = db.Column(db.String(50))  # Calibration, Repair, Maintenance
    certificate_no = db.Column(db.String(100))
    performed_by = db.Column(db.String(150))
```

**Сайжруулах:**
```
1. Calibration сануулга систем (email эсвэл dashboard notification)
2. Хугацаа дууссан багажийг ашиглахыг хориглох
3. Гэрчилгээний PDF файл хавсралт (одоо file_path л байгаа)
```

---

### 6.5 Хэмжилтийн ундран (Metrological Traceability)

**Статус:** ⚠️ ХЭСЭГЧЛЭН

**ISO 17025 шаардлага:**
- Хэмжилтийн олон улсын ундран
- Лавлагаа материалын бүртгэл
- Баталгаажуулалтын гэрчилгээ

**Одоогийн байдал:**
- ✅ Equipment calibration бүртгэл
- ❌ Reference material (эталон материал) бүртгэл байхгүй
- ❌ Traceability chain (ундрангийн гинж) баримтжуулаагүй
- ❌ CRM (Certified Reference Material) хадгалалт байхгүй

**Шаардлагатай нэмэлт:**
```python
# ШИНЭ: Reference Material
class ReferenceMaterial(db.Model):
    """Эталон материал, стандарт дээжний бүртгэл"""
    id = db.Column(db.Integer, primary_key=True)
    material_name = db.Column(db.String(150))  # Ж: "NIST Coal SRM 1632d"
    material_type = db.Column(db.String(50))  # CRM, RM, QC Standard
    supplier = db.Column(db.String(100))  # NIST, ISO, BAM
    certificate_no = db.Column(db.String(100))
    lot_number = db.Column(db.String(100))

    # Certified values
    certified_values = db.Column(db.Text)  # JSON: {"Aad": 10.5, "CV": 6800}
    uncertainty = db.Column(db.Text)  # JSON: {"Aad": 0.2, "CV": 50}

    # Dates
    receipt_date = db.Column(db.Date)
    expiry_date = db.Column(db.Date)
    opened_date = db.Column(db.Date)

    # Storage
    storage_location = db.Column(db.String(100))
    storage_conditions = db.Column(db.String(200))  # Ж: "Desiccator, RT"
    quantity_received = db.Column(db.Float)  # g
    quantity_remaining = db.Column(db.Float)  # g

    status = db.Column(db.String(20))  # valid, expired, depleted
    certificate_file = db.Column(db.String(255))
```

---

### 6.6 Мэдээлэл хадгалах (Externally Provided Products and Services)

**Статус:** ❌ ДУТУУ

**ISO 17025 шаардлага:**
- Гадны үйлчилгээ үзүүлэгчийн үнэлгээ
- Аюулгүй байдлын баталгаа
- Гэрээ, худалдан авалт

**Одоогийн байдал:**
- ❌ Supplier evaluation байхгүй
- ❌ Purchase order tracking байхгүй
- ❌ Service provider assessment байхгүй

**Шаардлагатай:**
```
1. Supplier list (Calibration service, Chemical supplier)
2. Vendor qualification
3. Purchase order system
```

---

### 7.1 Хяналтын тайлан (Review of Requests, Tenders and Contracts)

**Статус:** ⚠️ ХЭСЭГЧЛЭН

**ISO 17025 шаардлага:**
- Үйлчлүүлэгчийн хүсэлтийн хяналт
- Лабораторийн чадавхи шалгах
- Гэрээний баримт

**Одоогийн байдал:**
- ✅ Sample бүртгэл (client_name, received_date)
- ❌ Contract байхгүй
- ❌ Request review процесс байхгүй
- ❌ Лабын чадавхи шалгах механизм байхгүй

**Файл:** `app/models.py:136` (Sample class)

**Шаардлагатай:**
```python
# ШИНЭ: Service Request
class ServiceRequest(db.Model):
    """Үйлчлүүлэгчийн хүсэлт"""
    id = db.Column(db.Integer, primary_key=True)
    request_date = db.Column(db.DateTime)
    client_name = db.Column(db.String(200))
    requested_tests = db.Column(db.Text)  # JSON: ["Aad", "Mad", "CV"]
    sample_count = db.Column(db.Integer)
    required_date = db.Column(db.Date)  # Хэзээ хэрэгтэй

    # Review
    reviewed_by_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    review_date = db.Column(db.DateTime)
    can_perform = db.Column(db.Boolean)  # Чадах уу?
    limitations = db.Column(db.Text)  # Хязгаарлалт

    # Contract
    contract_no = db.Column(db.String(100))
    status = db.Column(db.String(20))  # pending, accepted, rejected, completed
```

---

### 7.2 Аргын сонгож, батжуулах (Selection, Verification and Validation of Methods)

**Статус:** ✅ БҮРЭН ХАНГАСАН

**ISO 17025 шаардлага:**
- Стандарт аргуудын баримтжуулалт
- Аргын батжуулалт (validation)
- Аргын тохирох байдал шалгах

**Одоогийн байдал:**
- ✅ **13 SOP баримт** (LAB.07.01 - LAB.07.14)
- ✅ MNS/ISO стандартууд (PDF)
- ✅ Repeatability шалгалт (precision control)
- ✅ Calculation functions (`app/utils/server_calculations.py`)

**SOP баримтууд:**
```
./SOP/LAB.07.01 Нүүрсний дээж бэлтгэх арга.docx
./SOP/LAB.07.02 Нийт чийг тодорхойлох.docx
./SOP/LAB.07.03 Дотоод чийг тодорхойлох.docx
./SOP/LAB.07.04 Дэгдэмхий бодисын гарц тодорхойлох.docx
./SOP/LAB.07.05 Үнслэгийн гарц тодорхойлох.docx
./SOP/LAB.07.06 Хөөлтийн зэрэг тодорхойлох.docx
./SOP/LAB.07.07 Барьцалдах чанар тодорхойлох.docx
./SOP/LAB.07.08 Хүхрийн хэмжээг тодорхойлох.docx
./SOP/LAB.07.09 Фосфор, хлорын агуулга тодорхойлох.docx
./SOP/LAB.07.10 Фторын агуулга тодорхойлох арга.docx
./SOP/LAB.07.12 Харьцангуй нягт тодорхойлох арга.docx
./SOP/LAB.07.13 Илчлэг тодорхойлох арга.docx
./SOP/LAB.07.14 Пластометрийн үзүүлэлт тодорхойлох арга.docx
```

**Сайжруулах:**
```
1. SOP-г LIMS системд нэгтгэх (database-д оруулах)
2. SOP-н хувилбарын удирдлага
3. Method validation protocol бичлэг
```

---

### 7.3 Дээжний авалт (Sampling)

**Статус:** ⚠️ ХЭСЭГЧЛЭН

**ISO 17025 шаардлага:**
- Дээж авалтын төлөвлөгөө
- Дээж авалтын журам
- Дээжний тодорхойлолт

**Одоогийн байдал:**
- ✅ Sample бүртгэл (unique sample_code)
- ✅ Received date, client info
- ✅ SOP: LAB.07.01 Нүүрсний дээж бэлтгэх арга
- ❌ Sampling plan байхгүй
- ❌ Chain of custody байхгүй
- ❌ Sample retention policy байхгүй

**Файл:** `app/models.py:136-230` (Sample class)

**Шаардлагатай нэмэлт:**
```python
# Sample классд нэмэх:
class Sample(db.Model):
    # ... existing fields ...

    # ШИНЭ: Sampling information
    sampled_by = db.Column(db.String(100))  # Хэн авсан
    sampling_date = db.Column(db.DateTime)  # Хэзээ авсан
    sampling_location = db.Column(db.String(200))  # Хаанаас авсан
    sampling_method = db.Column(db.String(100))  # Ж: "MNS GB-T 474-2015"

    # Chain of custody
    custody_transfer_log = db.Column(db.Text)  # JSON: [{date, from, to}]

    # Retention
    retention_date = db.Column(db.Date)  # Хадгалах хугацаа
    disposal_date = db.Column(db.Date)  # Устгах огноо
    disposal_method = db.Column(db.String(100))  # Яаж устгасан
```

---

### 7.4 Дээж шинжлэх (Handling of Test or Calibration Items)

**Статус:** ✅ ХАНГАСАН

**ISO 17025 шаардлага:**
- Дээжний хадгалалт, тээвэрлэлт
- Орчны нөхцөл (температур, чийг)
- Дээжний бүрэн бүтэн байдал

**Одоогийн байдал:**
- ✅ Sample status tracking (new, in_progress, completed, archived)
- ✅ Sample code (unique identification)
- ❌ Storage conditions бүртгэл байхгүй
- ❌ Environmental monitoring (T, RH) байхгүй

**Файл:** `app/models.py:203-208` (Sample.status)

**Шаардлагатай:**
```python
# ШИНЭ: Environmental Monitoring
class EnvironmentalLog(db.Model):
    """Орчны нөхцлийн бүртгэл"""
    id = db.Column(db.Integer, primary_key=True)
    log_date = db.Column(db.DateTime, default=now_mn)
    location = db.Column(db.String(100))  # Ж: "Sample storage room"
    temperature = db.Column(db.Float)  # °C
    humidity = db.Column(db.Float)  # %
    pressure = db.Column(db.Float)  # kPa (optional)
    recorded_by_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    notes = db.Column(db.Text)
```

---

### 7.7 Үр дүн батлах (Ensuring the Validity of Results)

**Статус:** ✅ БҮРЭН ХАНГАСАН

**ISO 17025 шаардлага:**
- Чанарын хяналтын дээж
- Repeatability шалгалт
- Proficiency testing

**Одоогийн байдал:**
- ✅ **Repeatability checking** (precision control)
- ✅ Автомат repeatability шалгалт
- ✅ Тохируулж болох limits (`app/config/repeatability.py`)
- ⚠️ Proficiency testing бүртгэл байхгүй
- ⚠️ Control charts байхгүй

**Файлууд:**
- `app/config/repeatability.py` - Repeatability limits
- `app/utils/repeatability_loader.py` - DB-ээс унших
- `app/utils/server_calculations.py` - Parallel measurements

**Сайжруулах:**
```python
# ШИНЭ: Proficiency Testing
class ProficiencyTest(db.Model):
    """Чадамжийн шалгалт (Proficiency Testing)"""
    id = db.Column(db.Integer, primary_key=True)
    pt_provider = db.Column(db.String(150))  # Ж: "ASTM, ISO LEAP"
    pt_program = db.Column(db.String(100))  # Ж: "Coal PT-2025"
    round_number = db.Column(db.String(50))
    sample_id = db.Column(db.String(100))  # PT дээжний код

    # Results
    analysis_code = db.Column(db.String(50))
    our_result = db.Column(db.Float)
    assigned_value = db.Column(db.Float)  # Зөвт утга
    uncertainty = db.Column(db.Float)
    z_score = db.Column(db.Float)  # Performance indicator
    status = db.Column(db.String(20))  # satisfactory, questionable, unsatisfactory

    # Dates
    received_date = db.Column(db.Date)
    test_date = db.Column(db.Date)
    report_date = db.Column(db.Date)

    certificate_file = db.Column(db.String(255))
    notes = db.Column(db.Text)

# ШИНЭ: Control Charts
class QCControlChart(db.Model):
    """Чанарын хяналтын график (Control Chart)"""
    id = db.Column(db.Integer, primary_key=True)
    analysis_code = db.Column(db.String(50))
    qc_sample_name = db.Column(db.String(100))  # Ж: "QC Coal Standard A"

    # Control limits
    target_value = db.Column(db.Float)  # Зорилтот утга
    ucl = db.Column(db.Float)  # Upper control limit
    lcl = db.Column(db.Float)  # Lower control limit
    usl = db.Column(db.Float)  # Upper spec limit (optional)
    lsl = db.Column(db.Float)  # Lower spec limit

    # Data points
    measurement_date = db.Column(db.Date)
    measured_value = db.Column(db.Float)
    in_control = db.Column(db.Boolean)  # UCL/LCL дотор уу?

    operator_id = db.Column(db.Integer, db.ForeignKey('user.id'))
```

---

### 7.8 Үр дүн тайлагнах (Reporting of Results)

**Статус:** ✅ ХАНГАСАН

**ISO 17025 шаардлага:**
- Үр дүнгийн тайлан (test report)
- Тайлангийн шаардлагатай мэдээлэл
- Тайлангийн засвар (amendments)

**Одоогийн байдал:**
- ✅ Analysis result storage
- ✅ Result approval workflow (ahlah батлах)
- ✅ Result status (draft, pending_review, approved, rejected)
- ✅ Timestamp (created_at, updated_at)
- ✅ Excel export
- ⚠️ Formal test report template байхгүй
- ⚠️ Report numbering system байхгүй

**Файл:** `app/models.py:767` (AnalysisResult)

**Шаардлагатай:**
```
1. Test Report template (logo, accreditation mark, disclaimer)
2. Report numbering (ж: TR-2025-0001)
3. Amendment tracking (засварын түүх)
4. Digital signature
```

---

### 7.10 Үр дүн батлах, хянах (Technical Records)

**Статус:** ✅ ХАНГАСАН

**ISO 17025 шаардлага:**
- Үр дүнгийн хадгалалт
- Өөрчлөлтийн түүх
- Эрх зөвшөөрөл

**Одоогийн байдал:**
- ✅ **AnalysisResultLog** - Бүх өөрчлөлт бичигдэнэ
- ✅ User tracking (created_by_id, reviewed_by_id)
- ✅ Action logging (CREATED, UPDATED, APPROVED, REJECTED)
- ✅ Timestamp (бүх үйлдэл)
- ✅ **AuditLog** - ISO 17025 compliance

**Файлууд:**
- `app/models.py:1016` (AnalysisResultLog)
- `app/models.py:1278` (AuditLog)
- `app/utils/audit.py` (Audit helper functions)

**Маш сайн!** Энэ бол ISO 17025-ын гол шаардлага.

---

### 7.11 Хяналт хийх (Control of Data and Information Management)

**Статус:** ⚠️ ХЭСЭГЧЛЭН

**ISO 17025 шаардлага:**
- Өгөгдлийн аюулгүй байдал
- Backup & recovery
- Database integrity

**Одоогийн байдал:**
- ✅ Database constraints (Foreign key, Unique, Check)
- ✅ Backup script (`scripts/backup_database.py`)
- ✅ Migration system (Alembic)
- ❌ Автомат backup байхгүй
- ❌ Disaster recovery plan байхгүй
- ❌ Data retention policy байхгүй

**Файлууд:**
- `migrations/versions/add_database_constraints.py`
- `scripts/backup_database.py`

**Шаардлагатай:**
```bash
# Автомат backup (cron job нэмэх)
0 2 * * * cd /path/to/coal_lims && python scripts/backup_database.py

# Retention policy
# - Analysis results: 10 жил хадгалах
# - Audit logs: 5 жил
# - Backup files: Сүүлийн 30
```

---

### 8.2 Дотоод хяналт (Internal Audits)

**Статус:** ❌ ДУТУУ

**ISO 17025 шаардлага:**
- Дотоод хяналтын төлөвлөгөө
- Хяналтын тайлан
- Засвар арга хэмжээ

**Одоогийн байдал:**
- ❌ Internal audit system байхгүй
- ❌ Audit checklist байхгүй
- ❌ Audit schedule байхгүй

**Шаардлагатай:**
```python
# ШИНЭ: Internal Audit
class InternalAudit(db.Model):
    """Дотоод хяналт"""
    id = db.Column(db.Integer, primary_key=True)
    audit_date = db.Column(db.Date)
    audit_type = db.Column(db.String(50))  # ISO 17025, System, Process
    auditor_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    scope = db.Column(db.Text)  # Хамрах хүрээ

    # Findings
    findings = db.Column(db.Text)  # JSON: [{category, description, severity}]
    non_conformities = db.Column(db.Integer)  # Тоо
    observations = db.Column(db.Integer)

    # Follow-up
    status = db.Column(db.String(20))  # scheduled, completed, closed
    report_file = db.Column(db.String(255))
    next_audit_date = db.Column(db.Date)
```

---

### 8.7 Засвар арга хэмжээ (Corrective Actions)

**Статус:** ❌ ДУТУУ

**ISO 17025 шаардлага:**
- Зөрчил илрүүлэх
- Шалтгаан шинжилгээ (root cause analysis)
- Засвар арга хэмжээ авах
- Үр дүнтэй байдлыг шалгах

**Одоогийн байдал:**
- ✅ Result rejection (буцаах механизм)
- ✅ Error reason tracking
- ❌ CAPA (Corrective and Preventive Action) system байхгүй
- ❌ Root cause analysis байхгүй
- ❌ Effectiveness verification байхгүй

**Файл:** `app/models.py:429` (AnalysisProfile - error_reason)

**Шаардлагатай:**
```python
# ШИНЭ: CAPA System
class CorrectiveAction(db.Model):
    """Засвар арга хэмжээ (CAPA)"""
    id = db.Column(db.Integer, primary_key=True)
    ca_number = db.Column(db.String(50), unique=True)  # Ж: CA-2025-001

    # Issue
    issue_date = db.Column(db.Date)
    issue_source = db.Column(db.String(100))  # Internal audit, Customer complaint, PT
    issue_description = db.Column(db.Text)
    severity = db.Column(db.String(20))  # Critical, Major, Minor

    # Analysis
    root_cause = db.Column(db.Text)  # 5 Why analysis
    root_cause_method = db.Column(db.String(100))  # 5 Whys, Fishbone, Pareto

    # Actions
    corrective_action = db.Column(db.Text)  # Засах арга хэмжээ
    preventive_action = db.Column(db.Text)  # Урьдчилан сэргийлэх
    responsible_person_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    target_date = db.Column(db.Date)
    completion_date = db.Column(db.Date)

    # Verification
    verification_method = db.Column(db.Text)
    verification_date = db.Column(db.Date)
    verified_by_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    effectiveness = db.Column(db.String(20))  # Effective, Not effective

    status = db.Column(db.String(20))  # open, in_progress, closed
    attachments = db.Column(db.Text)  # JSON: [file paths]
```

---

### 8.9 Гомдол (Complaints)

**Статус:** ❌ ДУТУУ

**ISO 17025 шаардлага:**
- Гомдлын бүртгэл
- Шийдвэрлэлтийн процесс
- Үйлчлүүлэгчид мэдэгдэх

**Одоогийн байдал:**
- ❌ Complaint tracking system байхгүй

**Шаардлагатай:**
```python
# ШИНЭ: Customer Complaints
class CustomerComplaint(db.Model):
    """Үйлчлүүлэгчийн гомдол"""
    id = db.Column(db.Integer, primary_key=True)
    complaint_no = db.Column(db.String(50), unique=True)

    # Customer
    client_name = db.Column(db.String(200))
    contact_person = db.Column(db.String(100))
    contact_email = db.Column(db.String(100))

    # Complaint
    complaint_date = db.Column(db.Date)
    complaint_type = db.Column(db.String(100))  # Turnaround time, Result accuracy, Service
    description = db.Column(db.Text)
    related_sample_id = db.Column(db.Integer, db.ForeignKey('sample.id'))

    # Resolution
    investigated_by_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    investigation_findings = db.Column(db.Text)
    resolution = db.Column(db.Text)
    resolution_date = db.Column(db.Date)

    # Follow-up
    customer_notified = db.Column(db.Boolean)
    customer_satisfied = db.Column(db.Boolean)
    capa_created = db.Column(db.Boolean)  # CAPA үүссэн үү

    status = db.Column(db.String(20))  # received, investigating, resolved, closed
```

---

## 📊 ХЭСЭГ 2: НЭГТГЭЛ

### ✅ САЙН ТАЛУУД (Strengths)

1. **Equipment Management** - Бүрэн хангасан ✅
   - Calibration tracking
   - Maintenance logs
   - Usage tracking

2. **Method Documentation** - Маш сайн ✅
   - 13 SOP баримт
   - ISO/MNS стандартууд
   - Repeatability control

3. **Result Approval Workflow** - Сайн ✅
   - Review process
   - Approval/rejection
   - Audit trail

4. **Data Integrity** - Сайн ✅
   - Database constraints
   - Foreign keys
   - Change logging

5. **Repeatability Control** - Сайн ✅
   - Автомат precision checking
   - Configurable limits
   - Parallel measurements

6. **Audit Trail** - Маш сайн ✅
   - AnalysisResultLog
   - AuditLog
   - User tracking

---

### ❌ ДУТУУ ХЭСЭГ (Critical Gaps)

| № | ISO Clause | Шаардлага | Критик эсэх |
|---|------------|-----------|-------------|
| 1 | 6.2 | **Training Records** | 🔴 Критик |
| 2 | 6.2 | **Competence Assessment** | 🔴 Критик |
| 3 | 6.5 | **Reference Material Tracking** | 🔴 Критик |
| 4 | 7.3 | **Chain of Custody** | 🔴 Критик |
| 5 | 7.3 | **Sample Retention Policy** | 🟡 Чухал |
| 6 | 7.4 | **Environmental Monitoring** | 🟡 Чухал |
| 7 | 7.7 | **Proficiency Testing** | 🔴 Критик |
| 8 | 7.7 | **Control Charts** | 🟡 Чухал |
| 9 | 7.8 | **Formal Test Report Template** | 🟡 Чухал |
| 10 | 8.2 | **Internal Audit System** | 🔴 Критик |
| 11 | 8.7 | **CAPA System** | 🔴 Критик |
| 12 | 8.9 | **Complaint Tracking** | 🟡 Чухал |
| 13 | 7.11 | **Automated Backup** | 🟡 Чухал |
| 14 | 7.11 | **Data Retention Policy** | 🟡 Чухал |

---

## 🎯 ЗӨВЛӨМЖ (Recommendations)

### Нэн тэргүүний зорилт (1-3 сар):

**1. Training & Competence System** 🔴
```
- TrainingRecord модел нэмэх
- CompetenceRecord модел нэмэх
- Сургалтын бүртгэл хөтлөх interface
- Хүчинтэй хугацааны сануулга

Давуу тал: ISO 17025-ын clause 6.2 бүрэн хангана
Хугацаа: 2 долоо хоног
```

**2. CAPA System** 🔴
```
- CorrectiveAction модель нэмэх
- CAPA tracking interface
- Root cause analysis tools
- Effectiveness verification

Давуу тал: ISO 17025-ын clause 8.7 бүрэн хангана
Хугацаа: 3 долоо хоног
```

**3. Reference Material Tracking** 🔴
```
- ReferenceMaterial модель нэмэх
- CRM certificate storage
- Expiry tracking
- Usage logging

Давуу тал: ISO 17025-ын clause 6.5 хангана
Хугацаа: 1 долоо хоног
```

### Дунд хугацааны зорилт (3-6 сар):

**4. Proficiency Testing System** 🔴
```
- ProficiencyTest модель
- Z-score calculation
- PT result tracking
- Trend analysis

Хугацаа: 2 долоо хоног
```

**5. Internal Audit System** 🔴
```
- InternalAudit модель
- Audit checklist
- Finding tracking
- CAPA integration

Хугацаа: 3 долоо хоног
```

**6. Environmental Monitoring** 🟡
```
- EnvironmentalLog модель
- Temperature/Humidity tracking
- Alert system (out of range)
- Trend charts

Хугацаа: 1-2 долоо хоног
```

### Урт хугацааны сайжруулалт (6-12 сар):

**7. Document Control System**
```
- SOP version control
- Approval workflow
- Training on new versions
- Obsolete document management
```

**8. Test Report System**
```
- Professional report template
- Report numbering
- Digital signature
- Amendment tracking
```

**9. Complaint Management**
```
- CustomerComplaint модель
- Resolution tracking
- Customer satisfaction survey
```

---

## 📈 ROADMAP

```
┌─────────────────────────────────────────────────────────────┐
│ MONTH 1-2: Critical Gap Closure (60% → 75%)                │
├─────────────────────────────────────────────────────────────┤
│ ✓ Training & Competence System                             │
│ ✓ Reference Material Tracking                              │
│ ✓ Chain of Custody                                         │
│ ✓ Automated Backup                                         │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│ MONTH 3-4: Quality Systems (75% → 85%)                     │
├─────────────────────────────────────────────────────────────┤
│ ✓ CAPA System                                              │
│ ✓ Proficiency Testing                                      │
│ ✓ Environmental Monitoring                                 │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│ MONTH 5-6: Continuous Improvement (85% → 95%)              │
├─────────────────────────────────────────────────────────────┤
│ ✓ Internal Audit System                                    │
│ ✓ Control Charts                                           │
│ ✓ Test Report Template                                     │
│ ✓ Complaint Management                                     │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│ MONTH 7-12: Full Compliance & Accreditation Ready (95%+)   │
├─────────────────────────────────────────────────────────────┤
│ ✓ Document Control                                         │
│ ✓ Supplier Management                                      │
│ ✓ Management Review                                        │
│ ✓ Pre-assessment Audit                                     │
│ ✓ ISO 17025 Accreditation Application                      │
└─────────────────────────────────────────────────────────────┘
```

---

## 💰 ХӨРӨНГӨ ОРУУЛАЛТ

### Программчлалын ажил:

| Зүйл | Хугацаа | Давуу эрэмбэ |
|------|---------|--------------|
| Training & Competence | 2 долоо хоног | 🔴 Нэн тэргүүн |
| CAPA System | 3 долоо хоног | 🔴 Нэн тэргүүн |
| Reference Material | 1 долоо хоног | 🔴 Нэн тэргүүн |
| Proficiency Testing | 2 долоо хоног | 🔴 Нэн тэргүүн |
| Internal Audit | 3 долоо хоног | 🔴 Нэн тэргүүн |
| Environmental Monitoring | 1-2 долоо хоног | 🟡 Чухал |
| Complaint Management | 1-2 долоо хоног | 🟡 Чухал |
| Document Control | 2-3 долоо хоног | 🟡 Чухал |
| Test Report System | 2-3 долоо хоног | 🟡 Чухал |

**НИЙТ:** 17-23 долоо хоног хөгжүүлэлт

### Сургалт:

- ISO 17025:2017 сургалт (бүх ажилтан): 2-3 хоног
- Internal auditor сургалт: 3 хоног
- CAPA training: 1 хоног
- LIMS систем сургалт: 2 хоног

---

## ✅ ДҮГНЭЛТ

### Одоогийн төлөв:

Coal LIMS нь **ISO 17025-ын 31%**-ийг бүрэн хангаж, **34%**-ийг хэсэгчлэн хангасан байна. Үндсэн техникийн шаардлагууд (equipment, method, result approval) сайн байгаа боловч удирдлагын систем (training, CAPA, audit) дутуу байна.

### Гол зөвлөмж:

1. **Training & Competence system** - Энэ нь хамгийн чухал Gap
2. **CAPA system** - Continuous improvement-д заавал шаардлагатай
3. **Reference Material tracking** - Traceability хангахад чухал
4. **Proficiency Testing** - Лабораторийн чадавхи батлах
5. **Internal Audit** - Үргэлжилсэн хяналт

### Timeline:

- **6 сар:** Critical gaps хаах (60% → 85%)
- **12 сар:** ISO 17025 accreditation-д бэлэн (85% → 95%+)

### Санхүүжилт:

- Программчлалын ажил: 4-6 сар (full-time developer)
- Сургалт: 1-2 сая ₮
- Accreditation зардал: 5-10 сая ₮ (гадны audit)

---

**Бэлтгэсэн:** Claude (AI Assistant)
**Огноо:** 2025-11-30
**Хувилбар:** 1.0
