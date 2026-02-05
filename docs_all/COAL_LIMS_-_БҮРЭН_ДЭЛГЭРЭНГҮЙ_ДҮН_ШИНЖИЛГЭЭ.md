# COAL LIMS - БҮРЭН ДЭЛГЭРЭНГҮЙ ДҮН ШИНЖИЛГЭЭ

**Огноо:** 2026-01-10
**Үүсгэсэн:** Claude Code (Opus 4.5)
**Зорилго:** Өдөр бүр ажил эхлэхээс өмнө уншиж, сайжруулалт хийх
**Хуудас:** ~50+ хуудас тэнцэхүйц

---

# ХЭСЭГ 1: ТӨСЛИЙН ЕРӨНХИЙ МЭДЭЭЛЭЛ

## 1.1 Төслийн танилцуулга

**Coal LIMS** (Laboratory Information Management System) нь Energy Resources LLC компанийн нүүрсний лабораторид зориулсан цогц мэдээллийн удирдлагын систем юм.

### Үндсэн зорилго:
- Нүүрсний дээжний бүртгэл, хяналт
- Шинжилгээний үр дүнг бүртгэх, тооцоолох
- ISO 17025 стандартын дагуу чанарын хяналт
- Тайлан, сертификат үүсгэх
- Лабораторийн тоног төхөөрөмжийн удирдлага

### Хөгжүүлэлтийн түүх:
| Огноо | Үйл явдал |
|-------|-----------|
| 2024 | Төсөл эхэлсэн |
| 2025-11 | Аюулгүй байдлын том засвар |
| 2025-12 | AG Grid формууд шинэчлэгдсэн |
| 2025-12 | Chat систем нэмэгдсэн |
| 2025-12-27 | Coverage 37% хүрсэн |
| 2026-01-03 | Coverage 83% хүрсэн |
| 2026-01-09 | ICPMS интеграц |

---

## 1.2 Кодын статистик

### Нийт хэмжээ:
```
app/
├── __init__.py              185 мөр
├── models.py               2000+ мөр
├── cli.py                   270 мөр
├── routes/                 8000+ мөр (25 файл)
├── utils/                  2500+ мөр (20 файл)
├── templates/              15000+ мөр (100+ файл)
├── static/js/              5000+ мөр (30+ файл)
└── static/css/             2000+ мөр

tests/
├── test_*.py               20000+ мөр (50+ файл)

Нийт Python код:    ~15,000 мөр
Нийт Template:      ~15,000 мөр
Нийт JavaScript:    ~5,000 мөр
Нийт Тест:          ~20,000 мөр
```

### Файлын тоо:
| Төрөл | Тоо |
|-------|-----|
| Python файл (.py) | ~80 |
| HTML Template | ~100 |
| JavaScript файл | ~30 |
| CSS файл | ~10 |
| Test файл | ~50 |
| Markdown docs | ~25 |

---

## 1.3 Функциональ бүрэлдэхүүн

### 1.3.1 Дээж бүртгэл (Sample Management)
| Feature | Статус | Тайлбар |
|---------|--------|---------|
| Дээж үүсгэх | ✅ | Manual + Batch import |
| Дээж засах | ✅ | Бүх талбар |
| Дээж устгах | ✅ | Soft delete |
| Статус удирдлага | ✅ | new → in_progress → completed |
| Шинжилгээ сонгох | ✅ | Multi-select |
| Хайлт, шүүлт | ✅ | DataTables + server-side |
| Excel import | ✅ | Batch upload |
| Retention date | ✅ | Disposal workflow |

### 1.3.2 Шинжилгээний ажлын талбар (Analysis Workspace)
| Шинжилгээ | Код | Статус | Тооцоолол |
|-----------|-----|--------|-----------|
| Moisture (чийг) | Mad | ✅ | ((m1+m2)-m3)/m2 * 100 |
| Ash (үнс) | Aad | ✅ | (m3-m1)/m2 * 100 |
| Volatile (дэгдэмхий) | Vad | ✅ | ((m2-m3)/m1) * 100 |
| Total Moisture | Mt | ✅ | ((m1-m2)/m1) * 100 |
| Sulfur | TS | ✅ | K factor calculation |
| Calorific Value | CV | ✅ | Alpha + Sulfur correction |
| Gray King | Gi | ✅ | 5:1 / 3:3 mode |
| Free Moisture | FM | ✅ | Wet/dry basis |
| Solid Content | Solid | ✅ | A-B-C calculation |
| True Relative Density | TRD | ✅ | Kt coefficient |
| CRI/CSR | CRI/CSR | ✅ | Paired analysis |
| Plastometer | X/Y | ✅ | rowSpan structure |
| CSN | CSN | ✅ | v1-v5 fields |

### 1.3.3 Чанарын хяналт (QC)
| Feature | Статус | Тайлбар |
|---------|--------|---------|
| Repeatability limits | ✅ | ISO 17025 дагуу |
| Westgard rules | ✅ | 6 дүрэм (1:2s, 1:3s, 2:2s, R:4s, 4:1s, 10x) |
| Control charts | ✅ | Chart.js visualization |
| Bottle constants | ✅ | TRD-д ашиглах |
| KPI dashboard | ✅ | Performance metrics |

### 1.3.4 Тайлан & Сертификат
| Feature | Статус | Format |
|---------|--------|--------|
| Sample summary | ✅ | Excel |
| Certificate | ✅ | PDF/Excel |
| Batch reports | ✅ | Excel |
| Hourly report | ✅ | Email + Excel |
| Monthly plan | ✅ | Web + Excel |
| Audit export | ✅ | Excel |

### 1.3.5 Чат систем
| Feature | Статус | Тайлбар |
|---------|--------|---------|
| Real-time messaging | ✅ | WebSocket |
| File sharing | ✅ | PNG, JPG, PDF, DOC (10MB) |
| Emoji picker | ✅ | 40 emoji |
| Urgent messages | ✅ | Red border, sound |
| Sample linking | ✅ | Reference samples |
| Broadcast | ✅ | Admin/Senior → All |
| Online status | ✅ | Real-time |
| Typing indicator | ✅ | "бичиж байна..." |

### 1.3.6 Хэрэглэгчийн удирдлага
| Role | Эрх |
|------|-----|
| admin | Бүх эрх |
| ahlah (senior) | Батлах, тохиргоо |
| senior | Батлах |
| chemist | Шинжилгээ хийх |
| beltgegch (preparer) | Дээж бэлтгэх |

---

# ХЭСЭГ 2: ТЕХНОЛОГИЙН БҮРЭН ДҮН ШИНЖИЛГЭЭ

## 2.1 Backend Framework: Flask 3.1.2

### 2.1.1 Flask-ийн давуу талууд

| # | Давуу тал | Тайлбар |
|---|-----------|---------|
| 1 | Хялбар | Сурахад амархан, код цөөн |
| 2 | Уян хатан | Extension олон, customize хялбар |
| 3 | Тогтвортой | 10+ жил хөгжүүлэгдсэн |
| 4 | Community | Том, documentation сайн |
| 5 | Sync | LIMS workload-д тохиромжтой |

### 2.1.2 Flask-ийн сул талууд

| # | Сул тал | Нөлөө |
|---|---------|-------|
| 1 | Async биш | High concurrency-д удаан |
| 2 | Type hints сул | Runtime error олон |
| 3 | Auto docs байхгүй | Swagger гараар хийх |
| 4 | Validation сул | WTForms эсвэл гараар |

### 2.1.3 Орчин үеийн хувилбаруудтай харьцуулалт

#### FastAPI (Хамгийн түгээмэл alternative)

```python
# FastAPI жишээ
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

class Sample(BaseModel):
    code: str
    weight: float

@app.post("/samples/")
async def create_sample(sample: Sample):
    return {"code": sample.code}
```

| Шалгуур | Flask | FastAPI | Ялгаа |
|---------|-------|---------|-------|
| Performance | 1x | 3-5x | FastAPI async |
| Type safety | Байхгүй | Pydantic | FastAPI сайн |
| Auto docs | Гараар | Автомат | FastAPI сайн |
| Learning curve | Хялбар | Дунд | Flask хялбар |
| Extensions | Олон | Цөөн | Flask олон |
| Maturity | 10+ жил | 5 жил | Flask туршлагатай |

**Flask → FastAPI шилжих шаардлага:**
- ❌ Одоо байгаа код бүгд дахин бичих
- ❌ Flask extensions (Login, WTF, Limiter) орлуулах
- ❌ Template rendering өөрчлөх
- ❌ 3-6 сарын хөгжүүлэлт

**Дүгнэлт:** Flask-ээс FastAPI руу шилжих нь **шаардлагагүй**. LIMS систем нь:
- I/O bound биш, CPU bound биш
- High concurrency шаардлагагүй
- Одоо ажиллаж байна

#### Django (Full-featured alternative)

| Шалгуур | Flask | Django | Тайлбар |
|---------|-------|--------|---------|
| Admin panel | Байхгүй | Автомат | Django давуу |
| ORM | SQLAlchemy | Django ORM | SQLAlchemy илүү уян |
| Size | Жижиг | Том | Flask хөнгөн |
| Flexibility | Өндөр | Дунд | Flask уян |
| "Batteries included" | Үгүй | Тийм | Django бүрэн |

**Django руу шилжих шаардлага:**
- ❌ SQLAlchemy models → Django models
- ❌ Бүх код дахин бичих
- ❌ Over-engineering болох

**Дүгнэлт:** Django **хэт том** энэ төсөлд.

#### Litestar (Хамгийн хурдан)

| Шалгуур | Flask | Litestar |
|---------|-------|----------|
| Performance | 1x | 5-10x |
| Community | Том | Жижиг |
| Documentation | Сайн | Дунд |
| Production ready | Тийм | Эргэлзээтэй |

**Дүгнэлт:** Litestar **эрсдэлтэй** - community жижиг.

### 2.1.4 Flask-ийн эцсийн үнэлгээ

```
┌─────────────────────────────────────────────────────────────┐
│  FLASK 3.1.2 ҮНЭЛГЭЭ                                       │
├─────────────────────────────────────────────────────────────┤
│  LIMS-д тохиромжтой байдал:     ██████████  10/10          │
│  Performance:                    ██████░░░░  6/10           │
│  Modern features:                █████░░░░░  5/10           │
│  Ecosystem:                      █████████░  9/10           │
│  Learning curve:                 ██████████  10/10          │
│                                                             │
│  НИЙТ:                          ████████░░  8/10            │
│                                                             │
│  ШИЙДВЭР: ҮЛДЭХ - Шилжих шаардлагагүй                      │
└─────────────────────────────────────────────────────────────┘
```

---

## 2.2 ORM: SQLAlchemy 2.0.44

### 2.2.1 SQLAlchemy давуу талууд

| # | Давуу тал | Тайлбар |
|---|-----------|---------|
| 1 | Бүрэн ORM | Complex queries, relationships |
| 2 | Raw SQL боломж | Performance optimization |
| 3 | Migration | Alembic интеграц |
| 4 | Multi-database | SQLite, PostgreSQL, MySQL |
| 5 | Session management | Transaction control |

### 2.2.2 Одоогийн хэрэглээ

```python
# app/models.py - Жишээ
class Sample(db.Model):
    __tablename__ = 'sample'

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(100), unique=True, nullable=False)
    client_name = db.Column(db.String(100))
    sample_type = db.Column(db.String(100))
    weight = db.Column(db.Float)
    status = db.Column(db.String(20), default='new')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    results = db.relationship('AnalysisResult', backref='sample')
```

### 2.2.3 Асуудлууд

#### N+1 Query асуудал
```python
# МУУХАЙ - N+1 query
samples = Sample.query.all()
for sample in samples:
    print(sample.results)  # Дээж бүрд нэг query

# ЗӨӨВ - Eager loading
samples = Sample.query.options(
    joinedload(Sample.results)
).all()
```

**Илэрсэн газрууд:**
- `app/routes/analysis/workspace.py`
- `app/routes/api/audit_api.py`

#### Index дутуу
```python
# Байх ёстой index-үүд
# migrations/versions/add_database_constraints.py

ix_sample_client_name          # ✅ Нэмсэн
ix_sample_sample_type          # ✅ Нэмсэн
ix_sample_client_type_status   # ✅ Нэмсэн
ix_sample_analyses_to_perform  # ✅ Нэмсэн

# Дутуу index-үүд
ix_analysis_result_sample_id_code  # ❌ Байхгүй
ix_audit_log_created_at            # ❌ Байхгүй
```

### 2.2.4 Alternative ORMs

| ORM | Давуу тал | Сул тал | Coal LIMS-д |
|-----|-----------|---------|-------------|
| SQLAlchemy (одоо) | Бүрэн, уян | Нарийн | ✅ Тохиромжтой |
| Django ORM | Хялбар | Зөвхөн Django | ❌ |
| Peewee | Хөнгөн | Feature цөөн | ❌ |
| Tortoise ORM | Async | Шинэ | ❌ |
| SQLModel | Type hints | SQLAlchemy дээр суурилсан | ⚠️ Боломжтой |

**Дүгнэлт:** SQLAlchemy **хамгийн зөв** сонголт.

---

## 2.3 Database: PostgreSQL

### 2.3.1 PostgreSQL давуу талууд LIMS-д

| # | Feature | LIMS-д яагаад чухал |
|---|---------|---------------------|
| 1 | ACID | Шинжилгээний үр дүн алдагдахгүй |
| 2 | JSON/JSONB | raw_data хадгалах |
| 3 | Full-text search | Дээж хайх |
| 4 | Window functions | Тайлан үүсгэх |
| 5 | CTEs | Complex queries |
| 6 | Triggers | Audit log автомат |
| 7 | Constraints | Data integrity |

### 2.3.2 Одоогийн тохиргоо

```python
# config.py
# Development
DATABASE_URL = "sqlite:///instance/coal_lims.db"

# Production
DATABASE_URL = "postgresql://lims_user:password@localhost:5432/coal_lims"
```

### 2.3.3 Асуудлууд

#### Development vs Production mismatch
```
DEV:  SQLite  (file-based, limited features)
PROD: PostgreSQL (full features)
```

**Эрсдэл:**
- SQLite-д ажилласан код PostgreSQL-д ажиллахгүй байж болно
- Data type ялгаа (DateTime, JSON)
- Constraint behavior ялгаа

**Шийдэл:**
```yaml
# docker-compose.yml - Dev environment-д PostgreSQL ашиглах
services:
  db:
    image: postgres:14
    environment:
      POSTGRES_DB: coal_lims_dev
      POSTGRES_USER: dev
      POSTGRES_PASSWORD: dev
    ports:
      - "5432:5432"
```

### 2.3.4 Alternative Databases

| Database | Use case | Coal LIMS-д |
|----------|----------|-------------|
| PostgreSQL (одоо) | General purpose, ACID | ✅ Хамгийн зөв |
| MySQL/MariaDB | Web apps | ⚠️ Боломжтой |
| SQLite | Embedded, dev | ✅ Dev-д OK |
| MongoDB | Document store | ❌ LIMS-д тохиромжгүй |
| TimescaleDB | Time-series | ⚠️ Хэрэв time-series их бол |

**Дүгнэлт:** PostgreSQL **100% зөв** сонголт.

---

## 2.4 Frontend: Bootstrap 5 + AG-Grid + Chart.js

### 2.4.1 Bootstrap 5

#### Давуу талууд:
| # | Давуу тал |
|---|-----------|
| 1 | Түгээмэл, documentation сайн |
| 2 | Responsive grid system |
| 3 | Ready-made components |
| 4 | Cross-browser compatible |

#### Сул талууд:
| # | Сул тал | Нөлөө |
|---|---------|-------|
| 1 | Bundle size том (~150KB) | Page load удаан |
| 2 | Utility classes хязгаартай | Custom CSS их |
| 3 | Design хуучирсан загвартай | Modern UI хэцүү |

#### Tailwind CSS-тай харьцуулалт:

```html
<!-- Bootstrap -->
<div class="container">
  <div class="row">
    <div class="col-md-6">
      <button class="btn btn-primary btn-lg">Click me</button>
    </div>
  </div>
</div>

<!-- Tailwind -->
<div class="max-w-7xl mx-auto px-4">
  <div class="flex flex-wrap">
    <div class="w-full md:w-1/2">
      <button class="bg-blue-500 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded">
        Click me
      </button>
    </div>
  </div>
</div>
```

| Шалгуур | Bootstrap 5 | Tailwind CSS |
|---------|-------------|--------------|
| Bundle size | ~150KB | ~10KB (purged) |
| Customization | Дунд | Өндөр |
| Learning curve | Хялбар | Дунд |
| Design flexibility | Дунд | Өндөр |
| Component library | Олон | Build yourself |

**Шилжих хүчин чармайлт:** ДУНД (100+ template файл)

### 2.4.2 AG-Grid

#### Яагаад AG-Grid хамгийн зөв:

| # | Feature | LIMS-д яагаад чухал |
|---|---------|---------------------|
| 1 | Excel-like editing | Химичид танил |
| 2 | Keyboard navigation | Хурдан оруулалт |
| 3 | Copy/paste | Excel-ээс хуулах |
| 4 | Column filtering | Өгөгдөл шүүх |
| 5 | Row grouping | Дээжээр бүлэглэх |
| 6 | Cell validation | Input шалгах |
| 7 | Export | Excel, CSV |

#### Alternatives:

| Grid | License | Features | Coal LIMS-д |
|------|---------|----------|-------------|
| AG-Grid (одоо) | Free/Enterprise | Бүрэн | ✅ Хамгийн зөв |
| Handsontable | Commercial | Excel-like | ⚠️ Лиценз үнэтэй |
| SlickGrid | MIT | Performance | ❌ Хуучирсан |
| DataTables | MIT | Simple | ❌ Grid биш |
| TanStack Table | MIT | Headless | ⚠️ Build хэрэгтэй |

**Дүгнэлт:** AG-Grid **солих шаардлагагүй**.

### 2.4.3 Chart.js

#### Давуу талууд:
- Хөнгөн (~60KB)
- Responsive
- 8 chart type
- Хялбар API

#### Сул талууд:
- Interactivity хязгаартай
- Large dataset удаан
- Tooltip customization хэцүү

#### Apache ECharts-тай харьцуулалт:

| Шалгуур | Chart.js | Apache ECharts |
|---------|----------|----------------|
| Size | 60KB | 400KB+ |
| Chart types | 8 | 20+ |
| Interactivity | Дунд | Өндөр |
| Large data | Муу | Сайн |
| 3D charts | Байхгүй | Байгаа |
| Map charts | Байхгүй | Байгаа |

**Шилжих хүчин чармайлт:** БАГА (API төстэй)

### 2.4.4 Vanilla JavaScript

#### Одоогийн байдал:
```
app/static/js/
├── aggrid_helpers.js      # 500+ мөр, AG-Grid utilities
├── calendar-module.js     # Shared calendar
├── chat.js                # 600+ мөр, WebSocket chat
├── serial_balance.js      # Web Serial API
├── logger.js              # Console logging
├── safe-storage.js        # localStorage wrapper
└── ... 25+ бусад файл
```

#### Асуудлууд:

| # | Асуудал | Нөлөө |
|---|---------|-------|
| 1 | Build system байхгүй | No minification, tree-shaking |
| 2 | TypeScript байхгүй | Runtime errors |
| 3 | Module system сул | Global pollution |
| 4 | Тест байхгүй | Bugs олон |
| 5 | Duplicate code | Maintenance хэцүү |

#### Жишээ асуудал:

```javascript
// aggrid_helpers.js - Global functions
window.LIMS_AGGRID = {
    createGrid: function(el, options) { ... },
    navHandlerFactory: function(fields) { ... },
    // 20+ functions
};

// Асуудал: Type checking байхгүй
// `fields` юу байх ёстой вэ? Array? Object? String?
```

#### Modern alternatives:

| Approach | Давуу тал | Хүчин чармайлт |
|----------|-----------|----------------|
| Vanilla JS (одоо) | Шууд ажиллана | - |
| Alpine.js | Reactive, жижиг | БАГА |
| htmx | No JS, server-driven | БАГА |
| Vite + TypeScript | Full modern stack | ТОМ |
| React/Vue/Svelte | SPA | МААГҮЙ ТОМ |

**Санал:** Alpine.js + htmx эхлээд нэмэх (БАГА хүчин чармайлт)

---

## 2.5 Security Stack

### 2.5.1 Одоогийн хэрэгжүүлэлт

#### CSRF Protection
```python
# app/__init__.py
from flask_wtf.csrf import CSRFProtect
csrf = CSRFProtect()
csrf.init_app(app)

# config.py
WTF_CSRF_ENABLED = True
WTF_CSRF_TIME_LIMIT = 3600  # 1 цаг
```
**Статус:** ✅ OK

#### Rate Limiting
```python
# app/__init__.py
from flask_limiter import Limiter
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"]
)

# app/routes/main/auth.py
@limiter.limit("5 per minute")
def login():
    ...
```
**Статус:** ✅ OK (гэхдээ Redis storage байхгүй)

#### Session Security
```python
# config.py
SESSION_COOKIE_SECURE = True      # Production-д
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = "Lax"
```
**Статус:** ✅ OK

#### Password Policy
```python
# app/models.py
def validate_password(password):
    if len(password) < 8:
        return False, "8-аас дээш тэмдэгт"
    if not re.search(r'[A-Z]', password):
        return False, "Том үсэг агуулах"
    if not re.search(r'[a-z]', password):
        return False, "Жижиг үсэг агуулах"
    if not re.search(r'\d', password):
        return False, "Тоо агуулах"
    return True, None
```
**Статус:** ✅ OK

#### Security Headers
```python
# app/__init__.py
@app.after_request
def add_security_headers(response):
    response.headers['X-Frame-Options'] = 'SAMEORIGIN'
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Strict-Transport-Security'] = 'max-age=31536000'
    return response
```
**Статус:** ✅ OK

### 2.5.2 Дутуу хэсгүүд

| # | Feature | Статус | Эрсдэл | Шийдэл |
|---|---------|--------|--------|--------|
| 1 | 2FA / MFA | ❌ | Account takeover | pyotp + QR code |
| 2 | JWT Auth | ❌ | API-only clients | Flask-JWT-Extended |
| 3 | Password reset | ⚠️ | Email interception | Token + time limit |
| 4 | Account lockout | ❌ | Brute force | N failed → lock |
| 5 | API rate limit | ⚠️ | DDoS | Per-endpoint limits |
| 6 | Input sanitization | ⚠️ | XSS, injection | Comprehensive validation |

### 2.5.3 Security тестийн хамрах хүрээ

```
tests/security/
├── test_csrf.py           # 5 тест ✅
├── test_sql_injection.py  # 4 тест ⚠️ (бага)
├── test_xss.py            # 5 тест ✅
└── test_auth.py           # ? тест

Нийт: ~15 security тест
Хэрэгтэй: 50+ тест
```

**Байхгүй тестүүд:**
- Rate limit bypass
- Session fixation
- IDOR (Insecure Direct Object Reference)
- File upload vulnerabilities
- Path traversal

---

## 2.6 DevOps & Infrastructure

### 2.6.1 Одоогийн байдал

```
┌─────────────────────────────────────────────────────────────┐
│  DEVOPS MATURITY: 2/10 - МААЖИЙ МУУ                        │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  CI/CD:              ❌ Байхгүй                             │
│  Containerization:   ⚠️ docker-compose.yml байгаа          │
│  Orchestration:      ❌ Kubernetes байхгүй                  │
│  Monitoring:         ❌ Prometheus/Grafana байхгүй          │
│  Logging:            ⚠️ File-based (ELK байхгүй)           │
│  Alerting:           ❌ PagerDuty/Slack байхгүй             │
│  Secrets management: ⚠️ .env файл                          │
│  Infrastructure as Code: ❌ Terraform байхгүй              │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 2.6.2 Deployment процесс

**Одоо:**
```bash
# Гар ажиллагаа, downtime-тай
ssh server
cd /var/www/coal_lims
git pull origin main
source venv/bin/activate
pip install -r requirements.txt
flask db upgrade
sudo systemctl restart coal_lims
# Алдаа гарвал → rollback хэцүү
```

**Байх ёстой:**
```yaml
# .github/workflows/deploy.yml
name: Deploy
on:
  push:
    branches: [main]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: pip install -r requirements.txt
      - run: pytest --cov=app

  deploy:
    needs: test
    runs-on: ubuntu-latest
    steps:
      - run: docker build -t coal-lims .
      - run: docker push registry/coal-lims
      - run: kubectl rollout restart deployment/coal-lims
```

### 2.6.3 Monitoring хэрэгтэй

| Tool | Зорилго | Статус |
|------|---------|--------|
| Prometheus | Metrics collection | ❌ |
| Grafana | Visualization | ❌ |
| Loki | Log aggregation | ❌ |
| Alertmanager | Alerting | ❌ |
| Sentry | Error tracking | ❌ |
| Uptime Robot | Health check | ⚠️ Script байгаа |

### 2.6.4 Шийдэл - Эхлэх алхмууд

**Step 1: GitHub Actions CI**
```yaml
# .github/workflows/ci.yml
name: CI
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:14
        env:
          POSTGRES_DB: test
          POSTGRES_USER: test
          POSTGRES_PASSWORD: test
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - run: pip install -r requirements.txt
      - run: pytest --cov=app --cov-fail-under=80
```

**Step 2: Docker production**
```dockerfile
# Dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .

CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:8000", "app:create_app()"]
```

---

# ХЭСЭГ 3: ХАТУУ ШҮҮМЖЛЭЛ - 15 АСУУДАЛ

## 3.1 CRITICAL - Шууд засах

### Асуудал #1: Bus Factor = 1

```
╔═══════════════════════════════════════════════════════════════╗
║  ХАМГИЙН ТОМ ЭРСДЭЛ                                          ║
║                                                               ║
║  Төсөл = 1 хөгжүүлэгч (Gantulga)                             ║
║  Knowledge transfer = 0                                       ║
║  Code review = 0                                              ║
║  Pair programming = 0                                         ║
║                                                               ║
║  ХЭРЭВ ТЭР ХҮН ЯВБАЛ → ТӨСӨЛ ЗОГСОНО                        ║
╚═══════════════════════════════════════════════════════════════╝
```

**Яагаад чухал:**
- Бүх мэдлэг 1 хүний толгойд
- Documentation бүрэн биш
- Хэн ч code review хийдэггүй
- Bugs олох хүн цөөн

**Шийдэл:**
1. 2-р хөгжүүлэгч авах эсвэл сургах
2. Бүрэн documentation бичих
3. Video tutorial бичих
4. Architecture diagram үүсгэх

---

### Асуудал #2: Service Layer байхгүй

**Одоогийн бүтэц:**
```
routes/api/samples_api.py (426 мөр)
├── get_data()           # 100+ мөр - DB query + business logic + response
├── sample_summary()     # 80+ мөр - бүгд холилдсон
├── export_samples()     # 60+ мөр
└── ... 15+ functions
```

**Асуудал:**
- Business logic route дотор
- Тест бичихэд хэцүү
- Refactor хэцүү
- Duplicate code

**Байх ёстой бүтэц:**
```
app/
├── routes/
│   └── api/
│       └── samples_api.py      # Request/Response ONLY
├── services/
│   └── sample_service.py       # Business logic
├── repositories/
│   └── sample_repository.py    # Database access
└── models/
    └── sample.py               # Data models
```

**Жишээ refactor:**

```python
# ОДОО - routes/api/samples_api.py
@bp.route('/data')
def get_data():
    # 100 мөр: request parsing + db query + filtering + response
    draw = request.args.get('draw', 1, type=int)
    start = request.args.get('start', 0, type=int)
    length = min(request.args.get('length', 25, type=int), 1000)

    query = Sample.query
    # ... 50 мөр filtering logic
    # ... 30 мөр response building
    return jsonify(result)

# БАЙХ ЁСТОЙ - routes/api/samples_api.py
@bp.route('/data')
def get_data():
    params = DataTableParams.from_request(request)
    result = sample_service.get_samples_datatable(params)
    return jsonify(result)

# services/sample_service.py
class SampleService:
    def __init__(self, repository: SampleRepository):
        self.repository = repository

    def get_samples_datatable(self, params: DataTableParams) -> dict:
        samples = self.repository.find_all(params.filters)
        return self._format_datatable_response(samples, params)

# repositories/sample_repository.py
class SampleRepository:
    def find_all(self, filters: dict) -> List[Sample]:
        query = Sample.query
        # Apply filters
        return query.all()
```

---

### Асуудал #3: CI/CD байхгүй

**Одоогийн deployment:**
```bash
# Гар ажиллагаа
git pull && pip install && flask db upgrade && systemctl restart
```

**Эрсдэл:**
- Тест ажиллуулахгүйгээр deploy
- Downtime
- Rollback хэцүү
- Staging environment байхгүй

**Шийдэл - GitHub Actions:**

```yaml
# .github/workflows/ci.yml
name: CI/CD

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest

    services:
      postgres:
        image: postgres:14
        env:
          POSTGRES_DB: coal_lims_test
          POSTGRES_USER: test
          POSTGRES_PASSWORD: test
        ports:
          - 5432:5432
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5

    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Cache pip
        uses: actions/cache@v3
        with:
          path: ~/.cache/pip
          key: ${{ runner.os }}-pip-${{ hashFiles('requirements.txt') }}

      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install -r requirements-dev.txt

      - name: Run linting
        run: |
          ruff check app/
          mypy app/ --ignore-missing-imports

      - name: Run tests
        env:
          DATABASE_URL: postgresql://test:test@localhost:5432/coal_lims_test
        run: |
          pytest --cov=app --cov-report=xml --cov-fail-under=80

      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          files: ./coverage.xml

  deploy:
    needs: test
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'

    steps:
      - name: Deploy to production
        run: |
          # SSH deploy эсвэл Docker push
          echo "Deploying..."
```

---

## 3.2 HIGH - Энэ сард засах

### Асуудал #4: Frontend тест 0%

**Одоогийн байдал:**
```
tests/
├── test_*.py           # Python тест: 10,250
└── (frontend тест)     # 0
```

**JavaScript файлууд тестлэгдээгүй:**
- `aggrid_helpers.js` - 500+ мөр
- `chat.js` - 600+ мөр
- `serial_balance.js` - 400+ мөр
- Нийт: 5,000+ мөр JavaScript = 0% тест

**Шийдэл - Vitest нэмэх:**

```javascript
// vitest.config.js
import { defineConfig } from 'vitest/config'

export default defineConfig({
  test: {
    environment: 'jsdom',
    globals: true,
  },
})

// tests/js/aggrid_helpers.test.js
import { describe, it, expect } from 'vitest'
import { LIMS_AGGRID } from '../../app/static/js/aggrid_helpers.js'

describe('LIMS_AGGRID', () => {
  describe('navHandlerFactory', () => {
    it('should create navigation handler', () => {
      const handler = LIMS_AGGRID.navHandlerFactory(['m1', 'm2'])
      expect(handler).toBeDefined()
      expect(typeof handler).toBe('function')
    })
  })
})
```

---

### Асуудал #5: TypeScript байхгүй

**Одоогийн JavaScript:**
```javascript
// aggrid_helpers.js
window.LIMS_AGGRID = {
    createGrid: function(el, options) {
        // el юу вэ? HTMLElement? String?
        // options юу агуулах ёстой вэ?
        // Return type юу вэ?
    }
};
```

**TypeScript-тай:**
```typescript
// aggrid_helpers.ts
interface GridOptions {
    columnDefs: ColumnDef[];
    rowData: any[];
    onCellValueChanged?: (params: CellValueChangedEvent) => void;
}

interface LimsAggrid {
    createGrid(el: HTMLElement, options: GridOptions): GridApi;
    navHandlerFactory(fields: string[]): NavigationHandler;
}

declare global {
    interface Window {
        LIMS_AGGRID: LimsAggrid;
    }
}

export const LIMS_AGGRID: LimsAggrid = {
    createGrid(el: HTMLElement, options: GridOptions): GridApi {
        // Type-safe implementation
    }
};
```

**Давуу тал:**
- IDE autocomplete
- Compile-time error
- Refactor хялбар
- Documentation built-in

---

### Асуудал #6: Coverage 83% худлаа

**Headline:** 83% coverage

**Бодит байдал:**

| Файл | Coverage | Чухал эсэх |
|------|----------|------------|
| index.py | **54%** | Үндсэн хуудас! |
| equipment_routes.py | **56%** | CRUD! |
| analysis_api.py | **61%** | Гол API! |
| audit_api.py | **62%** | Audit! |
| cli.py | **64%** | DB commands! |
| control_charts.py | **66%** | QC charts! |

**Чухал файлуудын дундаж:** ~60%

**Байхгүй тест төрлүүд:**
| Төрөл | Тоо | Хэрэгтэй |
|-------|-----|----------|
| Unit тест | 10,250 | ✅ |
| Integration тест | ~0 | 100+ |
| E2E тест | 0 | 50+ |
| Performance тест | 0 | 20+ |
| Security тест | ~15 | 50+ |
| Frontend тест | 0 | 100+ |

---

### Асуудал #7: Code Quality алдаа олон

```
┌─────────────────────────────────────────────────────────────┐
│  CODE QUALITY REPORT                                        │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  mypy type errors:     122  ████████████░░░░░░  BAD        │
│  ruff linting:         141  █████████████░░░░░  BAD        │
│  flake8 style:         598  ██████████████████  VERY BAD   │
│  vulture dead code:    39   ████░░░░░░░░░░░░░░  OK         │
│  docstring coverage:   65%  █████████████░░░░░  BAD        │
│                                                             │
│  TOTAL ISSUES:         ~900                                 │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

**Жишээ mypy алдаа:**
```python
# server_calculations.py
def calc_something(m1, m2, m3):
    # m1, m2, m3 may be None
    result = m1 - m2  # Error: Unsupported operand types for - ("float" and "None")
```

**Засах:**
```python
def calc_something(m1: float | None, m2: float | None, m3: float | None) -> float | None:
    if m1 is None or m2 is None:
        return None
    result = m1 - m2
    return result
```

---

### Асуудал #8: 2FA байхгүй

**Одоогийн auth:**
```python
# Username + Password only
@bp.route('/login', methods=['POST'])
def login():
    user = User.query.filter_by(username=username).first()
    if user and user.check_password(password):
        login_user(user)
        return redirect(url_for('main.index'))
```

**Эрсдэл:**
- Password leak → бүрэн access
- Phishing → account takeover
- Shared passwords → audit хэцүү

**Шийдэл - pyotp:**

```python
# pip install pyotp qrcode

# models.py
class User(db.Model):
    # ... existing fields
    totp_secret = db.Column(db.String(32), nullable=True)
    totp_enabled = db.Column(db.Boolean, default=False)

    def get_totp_uri(self):
        return pyotp.totp.TOTP(self.totp_secret).provisioning_uri(
            name=self.username,
            issuer_name="Coal LIMS"
        )

    def verify_totp(self, token):
        totp = pyotp.TOTP(self.totp_secret)
        return totp.verify(token)

# routes/auth.py
@bp.route('/login', methods=['POST'])
def login():
    user = User.query.filter_by(username=username).first()
    if user and user.check_password(password):
        if user.totp_enabled:
            session['pending_user_id'] = user.id
            return redirect(url_for('auth.verify_2fa'))
        login_user(user)
        return redirect(url_for('main.index'))

@bp.route('/verify-2fa', methods=['GET', 'POST'])
def verify_2fa():
    if request.method == 'POST':
        user = User.query.get(session['pending_user_id'])
        if user.verify_totp(request.form['token']):
            login_user(user)
            return redirect(url_for('main.index'))
    return render_template('auth/verify_2fa.html')
```

---

## 3.3 MEDIUM - Энэ улиралд засах

### Асуудал #9: Redis Cache байхгүй

**Одоогийн байдал:**
- Бүх query шууд database руу
- Rate limiter memory-д
- Session file-based

**Асуудал:**
- Ижил query давтагдана
- Multi-process rate limit ажиллахгүй
- Session share хийгдэхгүй

**Шийдэл:**

```python
# pip install redis flask-caching

# config.py
CACHE_TYPE = "RedisCache"
CACHE_REDIS_URL = "redis://localhost:6379/0"

# app/__init__.py
from flask_caching import Cache
cache = Cache()
cache.init_app(app)

# routes/api/samples_api.py
@bp.route('/dashboard_stats')
@cache.cached(timeout=60, key_prefix='dashboard_stats')
def dashboard_stats():
    # Энэ query 60 секунд cache-лэгдэнэ
    ...

# Cache invalidation
@bp.route('/samples', methods=['POST'])
def create_sample():
    # ... create sample
    cache.delete('dashboard_stats')
    return jsonify(sample)
```

---

### Асуудал #10: N+1 Query

**Илэрсэн газрууд:**

```python
# workspace.py - N+1 асуудал
samples = Sample.query.filter(...).all()
for sample in samples:
    results = sample.results  # Дээж бүрд 1 query = N query
    for result in results:
        print(result.analysis_code)

# audit_api.py - N+1 асуудал
logs = AuditLog.query.all()
for log in logs:
    print(log.user.username)  # Log бүрд 1 query
```

**Шийдэл:**

```python
# Eager loading ашиглах
from sqlalchemy.orm import joinedload, selectinload

# One-to-Many
samples = Sample.query.options(
    selectinload(Sample.results)
).all()

# Many-to-One
logs = AuditLog.query.options(
    joinedload(AuditLog.user)
).all()
```

---

### Асуудал #11: Broad Exception Catching

**Муухай код:**
```python
# 10+ газар илэрсэн
try:
    result = do_something()
except Exception:
    pass  # Бүх алдааг нуух

try:
    value = calculate()
except:  # Bare except - PEP 8 зөрчил
    return None
```

**Зөв код:**
```python
try:
    result = do_something()
except ValueError as e:
    logger.warning(f"Invalid value: {e}")
    return None
except IOError as e:
    logger.error(f"IO error: {e}")
    raise
except Exception as e:
    logger.exception(f"Unexpected error: {e}")
    raise
```

---

### Асуудал #12: Magic Numbers

**Илэрсэн жишээ:**
```python
# Код дотор шууд тоо
if len(password) < 8:  # Яагаад 8?
    ...

if weight > 10000:  # 10000 гэж юу?
    ...

results = query.limit(200)  # 200 хаанаас?
```

**Зөв арга:**
```python
# app/constants.py
MIN_PASSWORD_LENGTH = 8
MAX_SAMPLE_WEIGHT_GRAMS = 10000
MAX_ANALYSIS_RESULTS_PER_PAGE = 200
BOTTLE_TOLERANCE = 0.0015
MAX_IMPORT_BATCH_SIZE = 1000

# Ашиглах
from app.constants import MIN_PASSWORD_LENGTH
if len(password) < MIN_PASSWORD_LENGTH:
    ...
```

---

### Асуудал #13: Documentation Inconsistent

**Асуудлууд:**
1. Монгол + Англи холимог
2. Architecture diagram байхгүй
3. API docs бүрэн биш
4. Docstring 65%

**Жишээ:**
```python
# Docstring байхгүй
def calculate_cv(m, dt, e, q1, q2, sulfur):
    alpha = get_alpha(Qb_Jg)
    # ... 50 мөр код
    return result

# Байх ёстой
def calculate_cv(
    m: float,
    dt: float,
    e: float,
    q1: float,
    q2: float,
    sulfur: float
) -> dict | None:
    """
    Calculate Calorific Value (CV) using bomb calorimeter data.

    Args:
        m: Sample mass in grams
        dt: Temperature rise in Kelvin
        e: Energy equivalent of calorimeter (J/K)
        q1: Fuse wire correction (J)
        q2: Acid correction (J)
        sulfur: Sulfur content (%)

    Returns:
        dict with keys:
            - Qgr_ad_Jg: Gross CV at air-dried basis (J/g)
            - Qgr_ad_calg: Gross CV (cal/g)
            - alpha: Acid correction factor
        None if calculation fails

    Example:
        >>> calculate_cv(1.0, 2.5, 10000, 50, 30, 0.5)
        {'Qgr_ad_Jg': 25000.0, 'Qgr_ad_calg': 5972.0, 'alpha': 0.0012}
    """
```

---

### Асуудал #14: E2E тест байхгүй

**Одоо:**
- Unit тест: 10,250 ✅
- E2E тест: 0 ❌

**Хэрэгтэй E2E тестүүд:**

```python
# tests/e2e/test_sample_workflow.py
from playwright.sync_api import Page, expect

def test_create_sample_workflow(page: Page, logged_in_user):
    """Дээж үүсгэх бүрэн flow тест"""

    # 1. Нүүр хуудас руу орох
    page.goto("/")
    expect(page).to_have_title("Coal LIMS")

    # 2. Дээж үүсгэх таб сонгох
    page.click("text=Дээж бүртгэх")

    # 3. Форм бөглөх
    page.fill("#sample_code", "TEST-001")
    page.fill("#weight", "100.5")
    page.select_option("#client_name", "UHG-Geo")
    page.select_option("#sample_type", "Tailings")

    # 4. Шинжилгээ сонгох
    page.check("#analysis_Mad")
    page.check("#analysis_Aad")

    # 5. Хадгалах
    page.click("text=Хадгалах")

    # 6. Амжилттай үүссэн эсэх
    expect(page.locator(".alert-success")).to_be_visible()
    expect(page.locator("text=TEST-001")).to_be_visible()

def test_analysis_workflow(page: Page, sample_with_analyses):
    """Шинжилгээ хийх бүрэн flow тест"""

    # 1. Workspace руу орох
    page.goto(f"/analysis/workspace/Mad?sample_ids={sample_with_analyses.id}")

    # 2. Утга оруулах
    page.fill("[data-field='m1']", "1.0000")
    page.fill("[data-field='m2']", "1.0500")
    page.fill("[data-field='m3']", "1.0450")

    # 3. Тооцоолол шалгах
    result = page.locator("[data-field='result']").text_content()
    assert float(result) == pytest.approx(4.76, rel=0.01)

    # 4. Хадгалах
    page.click("text=Хадгалах")
    expect(page.locator(".alert-success")).to_be_visible()
```

---

### Асуудал #15: Scalability Plan байхгүй

**Одоогийн архитектур:**
```
[Users] ──→ [1x Flask Server] ──→ [PostgreSQL]
                   │
                   └── [File Storage]
```

**100+ user = Асуудал:**
- Single server bottleneck
- No caching
- No load balancing
- No horizontal scaling

**Шийдэл - Target архитектур:**

```
                        ┌─────────────────┐
                        │   Load Balancer │
                        │    (Nginx/HAProxy)
                        └────────┬────────┘
                                 │
              ┌──────────────────┼──────────────────┐
              │                  │                  │
              ▼                  ▼                  ▼
        ┌──────────┐      ┌──────────┐      ┌──────────┐
        │  Flask   │      │  Flask   │      │  Flask   │
        │ Server 1 │      │ Server 2 │      │ Server 3 │
        └────┬─────┘      └────┬─────┘      └────┬─────┘
             │                 │                 │
             └────────────┬────┴────┬────────────┘
                          │         │
                          ▼         ▼
                    ┌──────────┐  ┌──────────┐
                    │  Redis   │  │PostgreSQL│
                    │ (Cache)  │  │ (Primary)│
                    └──────────┘  └────┬─────┘
                                       │
                                       ▼
                                ┌──────────┐
                                │PostgreSQL│
                                │ (Replica)│
                                └──────────┘
```

---

# ХЭСЭГ 4: ЗАСВАРЫН ТӨЛӨВЛӨГӨӨ

## 4.1 Энэ долоо хоног (Week 1)

| # | Ажил | Файл | Хугацаа | Priority |
|---|------|------|---------|----------|
| 1 | ruff --fix | Бүх файл | 30 мин | P0 |
| 2 | Dead code устгах | vulture report | 1 цаг | P0 |
| 3 | index.py coverage 80%+ | tests/test_index_boost.py | 3 цаг | P1 |
| 4 | equipment_routes.py coverage 80%+ | tests/test_equipment_boost.py | 3 цаг | P1 |
| 5 | GitHub Actions CI | .github/workflows/ci.yml | 2 цаг | P1 |

### Өдөр бүрийн task:

**Даваа:**
- `ruff check app/ --fix` ажиллуулах
- `vulture app/` ажиллуулаад dead code устгах

**Мягмар:**
- index.py-д тест нэмж эхлэх
- Target: 54% → 70%

**Лхагва:**
- index.py тест үргэлжлүүлэх
- Target: 70% → 80%

**Пүрэв:**
- equipment_routes.py тест эхлэх
- Target: 56% → 70%

**Баасан:**
- equipment_routes.py тест дуусгах
- GitHub Actions CI үүсгэх

---

## 4.2 Энэ сар (Month 1)

| # | Ажил | Тайлбар | Хугацаа |
|---|------|---------|---------|
| 1 | Service layer эхлүүлэх | samples_api.py refactor | 1 долоо хоног |
| 2 | Redis cache нэмэх | Dashboard queries | 3 өдөр |
| 3 | Alpine.js туршилт | 1 хуудсанд | 2 өдөр |
| 4 | 2FA нэмэх | pyotp integration | 3 өдөр |
| 5 | mypy errors засах | 122 → 50 | 1 долоо хоног |

---

## 4.3 Энэ улирал (Quarter 1)

| # | Ажил | Тайлбар |
|---|------|---------|
| 1 | Vite + TypeScript | Frontend modernization |
| 2 | Playwright E2E | Critical paths |
| 3 | Docker production | Full containerization |
| 4 | Monitoring | Prometheus + Grafana |
| 5 | 2-р хөгжүүлэгч | Training эсвэл hire |

---

## 4.4 Энэ жил (Year 1)

| # | Ажил | Тайлбар |
|---|------|---------|
| 1 | Full service layer | Бүх route refactor |
| 2 | Kubernetes deploy | Scaling готов |
| 3 | 100% test coverage | Unit + E2E + Performance |
| 4 | Mobile app | React Native эсвэл Flutter |
| 5 | Multi-tenant | Олон лаборатори |

---

# ХЭСЭГ 5: ӨДӨР БҮРИЙН CHECKLIST

## 5.1 Ажил эхлэхээс өмнө (5 минут)

```
□ Энэ log уншсан
□ git status шалгасан
□ pytest -x ажиллуулсан (хурдан fail)
□ Өнөөдрийн task тодорхойлсон
□ JIRA/Todo шинэчилсэн
```

## 5.2 Код бичихдээ (байнга)

```
□ Type hints нэмсэн
□ Docstring бичсэн
□ Тест бичсэн
□ ruff check ажиллуулсан
□ mypy шалгасан
```

## 5.3 Commit хийхээс өмнө (2 минут)

```
□ pytest бүрэн ажиллуулсан
□ Coverage буураагүй эсэх
□ ruff check passed
□ Commit message тодорхой
```

## 5.4 Ажил дуусахад (5 минут)

```
□ git push хийсэн
□ PR үүсгэсэн (хэрэв branch)
□ Маргааш юу хийх тэмдэглэсэн
□ Энэ log шинэчилсэн (хэрэв шаардлагатай)
```

---

# ХЭСЭГ 6: QUICK REFERENCE

## 6.1 Commands

```bash
# Activate
cd D:\coal_lims_project
.\venv\Scripts\activate

# Test
pytest                              # Бүх тест
pytest -x                           # Эхний fail-д зогсох
pytest -v                           # Verbose
pytest --cov=app                    # Coverage
pytest --cov=app --cov-report=html  # HTML report
pytest tests/test_specific.py       # Тодорхой файл

# Code quality
ruff check app/                     # Lint
ruff check app/ --fix               # Auto fix
mypy app/ --ignore-missing-imports  # Type check
vulture app/                        # Dead code
black app/                          # Format

# Database
flask db upgrade                    # Migration apply
flask db downgrade                  # Rollback
flask db current                    # Current version

# Server
python run.py                       # Development
python run_https.py                 # HTTPS (Web Serial)
gunicorn -w 4 "app:create_app()"    # Production
```

## 6.2 File Locations

```
D:\coal_lims_project\
├── app\                    # Application code
│   ├── routes\             # URL handlers
│   ├── utils\              # Utilities
│   ├── templates\          # Jinja2 templates
│   └── static\             # CSS, JS, images
├── tests\                  # Test files
├── logs\                   # Log files (энэ файл энд)
├── docs\                   # Documentation
├── migrations\             # Database migrations
├── htmlcov\                # Coverage HTML report
├── .env                    # Environment variables
├── requirements.txt        # Python dependencies
└── README.md               # Project readme
```

## 6.3 Key Files to Watch

| Файл | Coverage | Яагаад чухал |
|------|----------|--------------|
| routes/main/index.py | 54% | Үндсэн хуудас |
| routes/equipment_routes.py | 56% | Equipment CRUD |
| routes/api/analysis_api.py | 61% | Analysis API |
| utils/server_calculations.py | 99% | Тооцоолол |
| models.py | ~80% | Database models |

---

# ХЭСЭГ 7: TECHNICAL DEBT TRACKER

## 7.1 Current Score

```
┌─────────────────────────────────────────────────────────────┐
│  TECHNICAL DEBT SCORECARD - 2026-01-10                     │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ARCHITECTURE                                               │
│  ├─ Service layer:     ░░░░░░░░░░  0%   (байхгүй)         │
│  ├─ Repository pattern: ░░░░░░░░░░  0%   (байхгүй)        │
│  └─ Dependency injection: ░░░░░░░░░░  0%                  │
│                                                             │
│  CODE QUALITY                                               │
│  ├─ Type coverage:     ████░░░░░░  40%  (mypy 122 error)  │
│  ├─ Linting:           ██████░░░░  60%  (ruff 141 error)  │
│  ├─ Docstrings:        ██████░░░░  65%                    │
│  └─ Dead code:         ████████░░  80%  (39 items)        │
│                                                             │
│  TESTING                                                    │
│  ├─ Unit tests:        ████████░░  83%                    │
│  ├─ Integration:       ░░░░░░░░░░  0%                     │
│  ├─ E2E:               ░░░░░░░░░░  0%                     │
│  ├─ Performance:       ░░░░░░░░░░  0%                     │
│  └─ Frontend:          ░░░░░░░░░░  0%                     │
│                                                             │
│  SECURITY                                                   │
│  ├─ Auth:              ████████░░  80%  (2FA байхгүй)     │
│  ├─ Input validation:  ███████░░░  70%                    │
│  └─ Security tests:    ███░░░░░░░  30%                    │
│                                                             │
│  DEVOPS                                                     │
│  ├─ CI/CD:             ░░░░░░░░░░  0%                     │
│  ├─ Containerization:  ██░░░░░░░░  20%                    │
│  ├─ Monitoring:        ░░░░░░░░░░  0%                     │
│  └─ Logging:           ████░░░░░░  40%                    │
│                                                             │
│  DOCUMENTATION                                              │
│  ├─ Code docs:         ██████░░░░  65%                    │
│  ├─ API docs:          █████░░░░░  50%                    │
│  └─ Architecture:      ██░░░░░░░░  20%                    │
│                                                             │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  OVERALL SCORE:        █████░░░░░  45/100                  │
│                                                             │
│  TARGET (3 months):    ███████░░░  70/100                  │
│  TARGET (6 months):    ████████░░  80/100                  │
│  TARGET (1 year):      █████████░  90/100                  │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

## 7.2 Progress Tracker

| Огноо | Score | Өөрчлөлт | Тэмдэглэл |
|-------|-------|----------|-----------|
| 2026-01-10 | 45/100 | - | Baseline |
| 2026-01-17 | - | - | Week 1 дүн |
| 2026-01-24 | - | - | Week 2 дүн |
| 2026-01-31 | - | - | Month 1 дүн |

---

# ХЭСЭГ 8: ХОЛБООСУУД

## 8.1 Төслийн файлууд

| Файл | Байршил |
|------|---------|
| README | [README.md](../README.md) |
| CHANGELOG | [CHANGELOG.md](../CHANGELOG.md) |
| DEPLOYMENT | [DEPLOYMENT.md](../DEPLOYMENT.md) |
| Coverage Report | [htmlcov/index.html](../htmlcov/index.html) |

## 8.2 Logs

| Файл | Агуулга |
|------|---------|
| Энэ файл | COMPREHENSIVE_REVIEW_2026-01-10.md |
| Өмнөх ажлын лог | [WORK_LOG_2025_12_27.md](./WORK_LOG_2025_12_27.md) |
| Production audit | [../PRODUCTION_AUDIT_LOG.md](../PRODUCTION_AUDIT_LOG.md) |

## 8.3 Гадаад холбоосууд

| Resource | URL |
|----------|-----|
| Flask docs | https://flask.palletsprojects.com/ |
| SQLAlchemy docs | https://docs.sqlalchemy.org/ |
| AG-Grid docs | https://www.ag-grid.com/documentation/ |
| pytest docs | https://docs.pytest.org/ |

---

# ДҮГНЭЛТ

Энэ лог нь Coal LIMS төслийн бүрэн дүн шинжилгээ юм. Өдөр бүр энэ файлыг уншиж:

1. **Одоогийн байдлыг** ойлгох
2. **Асуудлуудыг** санах
3. **Энэ өдрийн task** тодорхойлох
4. **Progress** хянах

---

**Дараагийн шинэчлэл:** 2026-01-11 эсвэл томоохон өөрчлөлт хийсний дараа

---

*"The best time to fix technical debt was yesterday. The second best time is today."*

---

**Файлын хэмжээ:** ~1500 мөр
**Үүсгэсэн:** Claude Code (Opus 4.5)
**Огноо:** 2026-01-10
