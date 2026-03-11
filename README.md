# LIMS - Laboratory Information Management System

**Лабораторийн мэдээллийн удирдлагын систем**

[![Python](https://img.shields.io/badge/Python-3.11%2B-blue.svg)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-3.1-green.svg)](https://flask.palletsprojects.com/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15-336791.svg)](https://www.postgresql.org/)
[![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-2.0-red.svg)](https://www.sqlalchemy.org/)
[![ISO 17025](https://img.shields.io/badge/ISO-17025-orange.svg)]()
[![License](https://img.shields.io/badge/License-Proprietary-red.svg)]()

---

## Төслийн тухай

LIMS нь олон лабораторид зориулсан цогц мэдээллийн удирдлагын систем юм. 4 лабораторийн модулийг нэгтгэн удирддаг бөгөөд **ISO/IEC 17025:2017** стандартын шаардлагыг хангахаар бүтээгдсэн.

### Лабораторийн модулиуд

| Лаб | Шинжилгээ | Тайлбар |
|-----|-----------|---------|
| **Нүүрс** (Coal) | 18 код (MT, Mad, Aad, Vdaf, TS, CV, CSN, Gi, TRD, P, F, Cl, XY...) | Basis conversion (ad/d/daf/ar), ISO 17025 QC |
| **Ус хими** (Water Chemistry) | 32 параметр (PH, EC, NH4, NO2, TDS, COLOR...) | MNS/WHO стандарт харьцуулалт |
| **Микробиологи** (Microbiology) | 8 код (CFU, ECOLI, SALM, AIR, SWAB...) | 3 ангилал: Ус, Агаар, Арчдас |
| **Петрограф** (Petrography) | 7 код (MAC, VR, MM, TS_PETRO...) | Мicroскопын шинжилгээ |

---

## Технологийн стек

| Layer | Technology |
|-------|------------|
| **Backend** | Python 3.11+, Flask 3.x, SQLAlchemy 2.0 |
| **Frontend** | Alpine.js, htmx, AG Grid v32, Bootstrap 5, Chart.js |
| **Database** | PostgreSQL 15 (prod), SQLite (dev) |
| **Real-time** | Flask-SocketIO (Chat) |
| **Cache** | Redis / SimpleCache |
| **Deployment** | Docker, Gunicorn + Nginx, Waitress (Windows) |
| **Monitoring** | Prometheus, Grafana, Sentry |
| **Testing** | pytest (10,400+ tests, 64% coverage) |

---

## Төслийн бүтэц

```
coal_lims_project/
├── app/                          # Flask application
│   ├── __init__.py               # App factory (create_app)
│   │
│   ├── bootstrap/                # App initialization modules
│   │   ├── auth.py               # Flask-Login setup
│   │   ├── blueprints.py         # Blueprint registration
│   │   ├── extensions.py         # Flask extensions (db, migrate, cache...)
│   │   ├── security_headers.py   # CSP, HSTS, X-Frame-Options
│   │   ├── websocket.py          # SocketIO setup
│   │   ├── errors.py             # Error handlers (404, 500)
│   │   ├── jinja.py              # Jinja2 filters, globals
│   │   └── middleware.py         # Request/response middleware
│   │
│   ├── models/                   # SQLAlchemy models (30+ tables)
│   │   ├── core.py               # User, Sample
│   │   ├── analysis.py           # AnalysisResult, AnalysisType
│   │   ├── equipment.py          # Equipment, Calibration
│   │   ├── chemicals.py          # Chemical, ChemicalUsage
│   │   ├── quality_records.py    # Complaint, CAPA, NonConformity
│   │   ├── reports.py            # LabReport, ReportSignature
│   │   └── ...                   # chat, bottles, license, spare_parts
│   │
│   ├── repositories/             # Data access layer (Repository pattern)
│   │   ├── sample_repository.py
│   │   ├── analysis_result_repository.py
│   │   ├── user_repository.py
│   │   ├── equipment_repository.py
│   │   ├── chemical_repository.py
│   │   ├── quality_repository.py # Complaint, CAPA, NC, PT repos
│   │   └── ...                   # 14 repository files total
│   │
│   ├── services/                 # Business logic layer
│   │   ├── sample_service.py     # Sample registration (batch, auto-name)
│   │   ├── analysis_workflow.py  # Analysis save/approve/reject
│   │   ├── analysis_audit.py     # Server-side recalculation & audit
│   │   ├── report_service.py     # Report generation
│   │   ├── equipment_service.py  # Equipment CRUD + calibration
│   │   ├── chemical_service.py   # Chemical inventory management
│   │   ├── admin_service.py      # User/system administration
│   │   ├── import_service.py     # Excel import processing
│   │   └── spare_parts_service.py
│   │
│   ├── constants/                # Application constants package
│   │   ├── analysis_types.py     # Analysis type definitions
│   │   ├── parameters.py         # Analysis parameters & aliases
│   │   ├── samples.py            # Sample type constants
│   │   └── qc_specs.py           # QC specifications
│   │
│   ├── config/                   # Configuration package
│   │   ├── analysis_schema.py    # Analysis form schemas
│   │   ├── repeatability.py      # Repeatability limits (ISO)
│   │   ├── qc_config.py          # QC rules configuration
│   │   └── display_precision.py  # Result display precision
│   │
│   ├── labs/                     # Multi-lab modules (BaseLab pattern)
│   │   ├── base.py               # BaseLab abstract class
│   │   ├── coal/                 # Coal lab (18 analyses)
│   │   ├── water_lab/
│   │   │   ├── chemistry/        # Water chemistry routes + reports
│   │   │   └── microbiology/     # Microbiology routes + reports
│   │   └── petrography/          # Petrography lab (7 codes)
│   │
│   ├── routes/                   # HTTP route handlers
│   │   ├── main/                 # Index, auth, samples, hourly report
│   │   ├── analysis/             # Analysis workspace, senior approval
│   │   ├── api/                  # REST API endpoints
│   │   ├── admin/                # User & system administration
│   │   ├── equipment/            # Equipment management
│   │   ├── chemicals/            # Chemical inventory
│   │   ├── spare_parts/          # Spare parts inventory
│   │   ├── reports/              # Reports, PDF, email
│   │   ├── quality/              # CAPA, complaints, PT, environmental
│   │   ├── chat/                 # Real-time chat (SocketIO)
│   │   ├── imports/              # Excel data import
│   │   ├── settings/             # System settings
│   │   └── license/              # License management
│   │
│   ├── security/                 # Security modules
│   │   ├── decorators.py         # @lab_required, @role_required
│   │   ├── security.py           # SQL injection prevention
│   │   ├── license_protection.py # License validation (HMAC)
│   │   └── hardware_fingerprint.py
│   │
│   ├── utils/                    # Utility modules
│   │   ├── server_calculations/  # Analysis formulas (18+ calculations)
│   │   ├── conversions.py        # Basis conversion (ad/d/daf/ar)
│   │   ├── westgard.py           # Westgard QC rules
│   │   ├── exports.py            # Excel export helpers
│   │   ├── audit.py              # Audit logging
│   │   └── ...                   # notifications, validators, etc.
│   │
│   ├── templates/                # Jinja2 templates
│   │   ├── base.html             # Base layout
│   │   ├── macros/               # Reusable macros
│   │   ├── analysis/partials/    # AG Grid macros
│   │   └── analysis_forms/       # AG Grid analysis forms (18+)
│   │
│   └── static/                   # CSS, JS, images
│       ├── js/aggrid_helpers.js   # AG Grid navigation, XSS escape
│       ├── js/form_guards.js      # Double-submit prevention
│       └── js/xlsx.full.min.js    # SheetJS (local, Excel export)
│
├── config/                       # App configuration (dev/prod/test)
├── migrations/                   # Alembic DB migrations
├── tests/                        # pytest tests (100+ files)
├── SOP/                          # ISO 17025 Standard Operating Procedures
├── docs/                         # Architecture decision records
├── docs_all/                     # Full documentation (60+ files)
├── scripts/                      # Utility scripts
├── monitoring/                   # Prometheus + Grafana configs
│
├── Dockerfile                    # Docker build
├── docker-compose.yml            # Production compose
├── gunicorn_config.py            # Gunicorn settings
├── nginx.conf                    # Nginx reverse proxy
├── requirements.txt              # Python dependencies
├── pytest.ini                    # Test configuration
└── run.py                        # Development server entry point
```

---

## Архитектура

```
Route (HTTP) → Service (Business Logic) → Repository (Data Access) → Model (ORM)
```

- **Routes** — HTTP request handling, input validation, response formatting
- **Services** — Business logic, complex workflows, cross-cutting concerns
- **Repositories** — Database queries, CRUD operations (static methods)
- **Models** — SQLAlchemy ORM, table definitions, relationships

### Server-side Calculations (Tampering Prevention)

```
Client JS (feedback) → Server verification → Correct value → DB
```

Шинжилгээний үр дүн серверт дахин тооцоологдоно. Client vs Server утга зөрвөл `security.log`-д бичигдэнэ.

---

## Суулгах заавар

### 1. Clone & Virtual Environment

```bash
git clone https://github.com/semmganaa-gif/coal_lims_project.git
cd coal_lims_project

# Windows
python -m venv venv
venv\Scripts\activate

# Linux/Mac
python3 -m venv venv
source venv/bin/activate
```

### 2. Dependencies суулгах

```bash
pip install -r requirements.txt
```

### 3. Environment тохируулах

```bash
cp .env.example .env
# .env файлд DATABASE_URL, SECRET_KEY, MAIL_* тохируулах
```

### 4. Database

```bash
flask db upgrade
flask seed-analysis-types
flask seed-sample-types
flask seed-error-reasons
flask create-admin
```

### 5. Ажиллуулах

```bash
# Development
python run.py

# Production (Linux)
gunicorn -w 4 -b 0.0.0.0:8000 "app:create_app()"

# Production (Windows)
waitress-serve --host=0.0.0.0 --port=8000 --call app:create_app
```

---

## Тест ажиллуулах

```bash
# Бүх тест
pytest

# Coverage-тай
pytest --cov=app --cov-report=html

# Unit tests
pytest tests/unit/
```

**Одоогийн байдал:** 10,400+ тест, 64% coverage

---

## Deployment

### Docker

```bash
docker-compose up -d
```

### Production Checklist

- `FLASK_ENV=production`, `DEBUG=False`
- `SECRET_KEY` random (32+ chars)
- PostgreSQL + backup configured
- HTTPS + `SESSION_COOKIE_SECURE=True`
- Redis for caching & rate limiting
- Log rotation configured

Дэлгэрэнгүй: [DEPLOY_GUIDE.md](DEPLOY_GUIDE.md)

---

## Аюулгүй байдал

| Хамгаалалт | Статус |
|------------|--------|
| SQL Injection | SQLAlchemy ORM + `escape_like_pattern()` |
| CSRF | Flask-WTF CSRF tokens |
| XSS | Jinja2 auto-escaping + `_escHtml()` |
| Rate Limiting | Login: 5/min, Global: 500/hour |
| Session | HttpOnly, Secure, SameSite=Lax |
| CSP | Content Security Policy headers |
| Audit | AuditLog + data_hash (ISO 17025) |
| Password | 8+ chars, uppercase, lowercase, digits |
| Access Control | Role-based + `allowed_labs` per user |

---

## API Endpoints

| Prefix | Тайлбар |
|--------|---------|
| `/api/samples` | Дээж CRUD |
| `/api/analysis/*` | Шинжилгээний үр дүн |
| `/api/qc/*` | Control charts, Westgard |
| `/labs/water/api/*` | Усны хими API |
| `/labs/microbiology/api/*` | Микробиологи API |
| `/labs/petrography/api/*` | Петрограф API |

Бүрэн API docs: [docs_all/LIMS_-_API_Documentation.md](docs_all/LIMS_-_API_Documentation.md)

---

## Баримт бичиг

| Баримт | Тайлбар |
|--------|---------|
| [System Architecture](docs_all/LIMS_-_System_Architecture.md) | Системийн бүтэц, BaseLab pattern |
| [API Documentation](docs_all/LIMS_-_API_Documentation.md) | REST API endpoints |
| [Developer Onboarding](docs_all/LIMS_-_Developer_Onboarding_Guide.md) | Хөгжүүлэгчдэд заавар |
| [DEPLOY_GUIDE.md](DEPLOY_GUIDE.md) | Production deployment |
| [Operations Runbook](docs_all/LIMS_-_Operations_Runbook.md) | Ашиглалтын заавар |

---

## Лиценз

Proprietary - LIMS by Gantulga

&copy; 2024-2026 LIMS. Developed by Gantulga U. (semmganaa@gmail.com)

---

**Version:** 2.0.0
**Last Updated:** 2026-03-11
