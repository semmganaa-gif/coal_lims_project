# LIMS - Laboratory Information Management System

**Лабораторийн мэдээллийн удирдлагын систем**

[![Python](https://img.shields.io/badge/Python-3.11%2B-blue.svg)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-3.1.2-green.svg)](https://flask.palletsprojects.com/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15-336791.svg)](https://www.postgresql.org/)
[![ISO 17025](https://img.shields.io/badge/ISO-17025-orange.svg)]()
[![License](https://img.shields.io/badge/License-Proprietary-red.svg)]()

---

## 📋 Агуулга

1. [Төслийн тухай](#төслийн-тухай)
2. [Үндсэн функционалууд](#үндсэн-функционалууд)
3. [Технологийн стек](#технологийн-стек)
4. [Төслийн бүтэц](#төслийн-бүтэц)
5. [Суулгах заавар](#суулгах-заавар)
6. [Тохиргоо](#тохиргоо)
7. [Хөгжүүлэлтийн орчин](#хөгжүүлэлтийн-орчин)
8. [Тест ажиллуулах](#тест-ажиллуулах)
9. [Deployment](#deployment)
10. [Баримт бичиг](#баримт-бичиг-documentation)
11. [API Documentation](#api-documentation)
12. [Аюулгүй байдал](#аюулгүй-байдал)
13. [Contributing](#contributing)
14. [Лиценз](#лиценз)

---

## 🎯 Төслийн тухай

LIMS нь **Energy Resources LLC** компанийн олон лабораторид зориулсан цогц мэдээллийн удирдлагын систем юм. Систем нь 4 лабораторийн модулийг (Нүүрс, Ус, Микробиологи, Петрограф) нэгтгэн удирддаг бөгөөд **ISO 17025** стандартын шаардлагыг хангахаар бүтээгдсэн.

---

## Лабораторийн модулиуд

### Нүүрсний лаб (Coal Lab)
- 18 шинжилгээний код: MT, Mad, Aad, Vad, TS, CV, CSN, Gi, TRD, P, SiO2, Al2O3, Fe2O3, CaO, MgO, Na2O, K2O, TiO2
- Basis conversion (ad, d, daf, ar)
- ISO 17025 QC (repeatability, reproducibility)

### Усны лаб (Water Lab)
- 32 параметр: PH, EC, металлууд, анионууд гэх мэт
- MNS/WHO стандартын харьцуулалт

### Микробиологийн лаб (Microbiology Lab)
- 8 код, 3 ангилал:
  - Ус: CFU, ECOLI, SALM
  - Агаар: AIR_CFU, AIR_STAPH
  - Арчдас: SWAB_CFU, SWAB_ECOLI, SWAB_SALM

### Петрограф лаб (Petrography Lab)
- 7 код: MAC, VR, MM, TS_PETRO, MOD, TEX, GS

### Зорилго

- Дээжний бүртгэл, удирдлага
- Шинжилгээний үр дүнгий бүртгэл, тооцоолол
- Чанарын хяналтын удирдлага (QC + Westgard rules)
- Тайлан, сертификат үүсгэх
- Лабораторийн хэрэгслийн удирдлага (ISO 17025 Section 6.4)
- Хэрэглэгчийн эрх, эрхийн удирдлага
- ISO 17025 дагуу мөрдөх баримт бичгийн удирдлага
- Олон лабораторийн дэмжлэг (BaseLab pattern)
- Лаб тусгай эрхийн удирдлага (allowed_labs)

### Multi-Lab Architecture (BaseLab Pattern)

Бүх лабораторийн модулиуд `BaseLab` абстракт класс-аас удамшина:

```python
class BaseLab:
    key: str          # "coal", "water", "microbiology", "petrography"
    name: str         # UI-д харагдах нэр
    icon: str         # Bootstrap icon
    analysis_codes: list  # Тухайн лабын шинжилгээний кодууд

    def get_blueprint() -> Blueprint
    def sample_query() -> Query
    def sample_stats() -> dict
```

Дэлгэрэнгүй: [System Architecture](docs_all/LIMS_-_System_Architecture.md)

---

## ⚡ Үндсэн функционалууд

### 1. Дээжний удирдлага
- ✅ Дээж бүртгэх (batch import болон manual)
- ✅ Дээжний мэдээлэл засах, устгах
- ✅ Дээжний төлөв удирдах (new → in_progress → completed)
- ✅ Шинжилгээний төрөл сонгох
- ✅ Дээжний хайлт, шүүлт (DataTables)

### 2. Шинжилгээний ажлын талбар
- ✅ Анализ тус бүрийн тусгай workspace
- ✅ Параллель хэмжилтүүдийн бүртгэл
- ✅ Автомат тооцоолол (mean, std, RSD, repeatability check)
- ✅ Basis conversion (ad ↔ d ↔ daf ↔ ar)
- ✅ Real-time validation
- ✅ Senior approval workflow

### 3. Чанарын хяналт (QC)
- ✅ Давталтын хязгаар шалгах (Repeatability limits)
- ✅ Бортого (Bottle constants) удирдлага
- ✅ KPI dashboard
- ✅ Quality control charts

### 4. Тайлан & Сертификат
- ✅ Sample summary (Excel export)
- ✅ Certificate генерация
- ✅ Multi-sample batch reports
- ✅ Customizable templates

### 5. Хэрэгслийн удирдлага
- ✅ Хэрэгслийн бүртгэл
- ✅ Тохируулга, calibration tracking
- ✅ Maintenance schedule
- ✅ Certificate upload

### 6. Хэрэглэгчийн удирдлага
- ✅ Role-based access control (admin, ahlah, senior, beltgegch, himich) + allowed_labs эрх
- ✅ Нууц үгний бодлого
- ✅ Login rate limiting
- ✅ Audit logging

---

## 🛠 Технологийн стек

| Layer | Technology |
|-------|------------|
| Frontend | HTML5, CSS3, JavaScript, Alpine.js, htmx, AG Grid |
| Backend | Python 3.11+, Flask 3.x |
| Database | PostgreSQL 15 (production), SQLite (development) |
| Cache | Redis 7 (optional) |
| Web Server | Gunicorn + Nginx (Linux), Waitress (Windows) |
| Containerization | Docker, Docker Compose |
| Monitoring | Prometheus, Grafana, Loki, Sentry |
| Testing | pytest, Playwright, k6, Locust |

### Backend Details
- **Framework:** Flask 3.1.2
- **Database ORM:** SQLAlchemy 2.0.44
- **Migration:** Alembic 1.17.1
- **Authentication:** Flask-Login 0.6.3
- **Forms:** Flask-WTF 1.2.1
- **Security:** Flask-Limiter, CSRF Protection, Content Security Policy
- **Real-time:** Flask-SocketIO (Chat system)

### Frontend Details
- **HTML Templates:** Jinja2 (macro-based reusable components)
- **CSS Framework:** Bootstrap 5 + Glassmorphism design
- **Data Grid:** AG Grid Community (floating filters, export)
- **Charts:** Chart.js (Control charts, KPI dashboards)
- **Excel Export:** openpyxl

### Python Libraries
- **Data Processing:** pandas, numpy
- **Math:** statistics, scipy
- **Date/Time:** python-dateutil, pytz
- **Email:** Flask-Mail
- **PDF Reports:** WeasyPrint (in progress)

---

## 📁 Төслийн бүтэц

```
coal_lims_project/
├── app/                    # Flask application
│   ├── __init__.py        # App factory, extensions
│   ├── models.py          # SQLAlchemy models (30+ tables)
│   ├── constants.py       # Analysis aliases, constants
│   ├── monitoring.py      # Prometheus metrics
│   │
│   ├── labs/              # Multi-lab modules (BaseLab pattern)
│   │   ├── base.py        # BaseLab abstract class
│   │   ├── coal/          # Coal lab (18 analyses)
│   │   ├── water_lab/     # Water lab (32 parameters)
│   │   │   ├── chemistry/ # Chemistry routes
│   │   │   └── microbiology/ # Microbiology routes
│   │   └── petrography/   # Petrography lab (7 codes)
│   │
│   ├── routes/            # Core routes
│   │   ├── main/          # Index, auth, samples
│   │   ├── analysis/      # Analysis workspace, senior, QC
│   │   ├── api/           # REST API endpoints
│   │   ├── equipment/     # Equipment management
│   │   ├── spare_parts/   # Spare parts inventory
│   │   ├── chemicals/     # Chemical inventory
│   │   └── quality/       # CAPA, PT, Environmental
│   │
│   ├── utils/             # Utilities
│   │   ├── server_calculations.py  # Analysis formulas
│   │   ├── westgard.py    # Westgard QC rules
│   │   ├── security.py    # SQL injection prevention
│   │   └── decorators.py  # @lab_required, @analysis_role_required
│   │
│   ├── templates/         # Jinja2 templates
│   │   ├── macros/        # Reusable macros (aggrid, form helpers)
│   │   └── analysis_forms/ # AG Grid analysis forms
│   │
│   └── static/            # CSS, JS, images
│       └── js/            # AG Grid helpers, calculators
│
├── migrations/            # Alembic migrations (33+ versions)
├── tests/                 # pytest tests (100+ files)
├── docs_all/              # All documentation (64 files)
└── logs/                  # Application logs
```

---

## 📥 Суулгах заавар

### Шаардлага
- Python 3.8 эсвэл түүнээс дээш
- pip (Python package manager)
- Git

### 1. Repository татах

```bash
git clone https://github.com/your-org/coal-lims.git
cd coal-lims
```

### 2. Virtual Environment үүсгэх

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/Mac
python3 -m venv venv
source venv/bin/activate
```

### 3. Dependencies суулгах

```bash
pip install -r requirements.txt
```

### 4. Environment тохируулах

```bash
# .env файл үүсгэх (.env.example файлаас хуулах)
cp .env.example .env

# .env файлд шаардлагатай утгуудыг оруулах
# Дэлгэрэнгүй: Тохиргоо хэсэг үз
```

### 5. Database migration

```bash
# Database үүсгэх
flask db upgrade

# Анхдагч өгөгдөл оруулах
flask seed-analysis-types
flask seed-sample-types
flask seed-error-reasons
```

### 6. Админ хэрэглэгч үүсгэх

```bash
flask create-admin
# Эсвэл интерактив горимд:
flask create-user
```

### 7. Ажиллуулах

```bash
# Development mode
python run.py

# Flask development server
flask run

# Эсвэл debug горимд
flask run --debug
```

Аппликейшн http://127.0.0.1:5000 дээр ажиллана.

---

## ⚙️ Тохиргоо

### Environment Variables

`.env` файл үүсгээд дараах утгуудыг тохируулна:

```bash
# Application
FLASK_ENV=development                # production эсвэл development
SECRET_KEY=your-secret-key-here      # 32+ тэмдэгт random string
DEBUG=False                          # Production-д ЗААВАЛ False

# Database
DATABASE_URL=sqlite:///instance/coal_lims.db  # SQLite
# DATABASE_URL=postgresql://user:pass@localhost/coal_lims  # PostgreSQL

# Email Configuration
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=your-email@example.com
MAIL_PASSWORD=your-app-password      # Gmail: App Password ашиглах

# Session Security
SESSION_COOKIE_SECURE=True           # Production-д HTTPS шаардлагатай
SESSION_COOKIE_HTTPONLY=True
SESSION_COOKIE_SAMESITE=Lax

# File Upload
MAX_CONTENT_LENGTH=16777216          # 16MB
UPLOAD_FOLDER=instance/uploads/certificates
```

### Secret Key генерация

```python
python -c "import secrets; print(secrets.token_urlsafe(48))"
```

### Database сонголт

**Development:** SQLite (default)
```bash
DATABASE_URL=sqlite:///instance/coal_lims.db
```

**Production:** PostgreSQL (зөвлөмж)
```bash
DATABASE_URL=postgresql://username:password@localhost:5432/coal_lims
```

---

## 💻 Хөгжүүлэлтийн орчин

### Code Quality Tools суулгах

```bash
pip install -r requirements-dev.txt
```

### Code Formatting

```bash
# Black formatter
black app/ tests/

# Flake8 linting
flake8 app/ tests/

# Type checking
mypy app/
```

### Pre-commit hooks

```bash
# Pre-commit суулгах
pip install pre-commit
pre-commit install

# Гар аргаар ажиллуулах
pre-commit run --all-files
```

---

## 🧪 Тест ажиллуулах

### Бүх тест ажиллуулах

```bash
pytest
```

### Coverage-тай ажиллуулах

```bash
pytest --cov=app --cov-report=html
```

Coverage тайланг `htmlcov/index.html` файлд үзнэ.

### Тодорхой тест ажиллуулах

```bash
# Unit tests
pytest tests/unit/

# Integration tests
pytest tests/integration/

# Security tests
pytest tests/security/

# Smoke tests
pytest -m smoke
```

---

## 🚀 Deployment

### Production Checklist

- [ ] `FLASK_ENV=production` тохируулсан
- [ ] `DEBUG=False` тохируулсан
- [ ] `SECRET_KEY` random утга өгсөн (32+ chars)
- [ ] Database backup тохируулсан
- [ ] HTTPS идэвхжүүлсэн
- [ ] `SESSION_COOKIE_SECURE=True`
- [ ] Email credentials environment-д орсон
- [ ] Firewall тохируулсан
- [ ] Log rotation тохируулсан
- [ ] Monitoring идэвхжүүлсэн

### Gunicorn ашиглах

```bash
# Суулгах
pip install gunicorn

# Ажиллуулах
gunicorn -w 4 -b 0.0.0.0:8000 "app:create_app()"
```

### Nginx тохиргоо

```nginx
server {
    listen 80;
    server_name lims.example.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /static {
        alias /path/to/coal-lims/app/static;
        expires 30d;
    }
}
```

### Systemd Service

```ini
[Unit]
Description=LIMS
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/path/to/coal-lims
Environment="PATH=/path/to/coal-lims/venv/bin"
ExecStart=/path/to/coal-lims/venv/bin/gunicorn -w 4 -b 127.0.0.1:8000 "app:create_app()"

[Install]
WantedBy=multi-user.target
```

### Docker (Дэлгэрэнгүй: docker-compose.yml)

```bash
docker-compose up -d
```

---

## 📚 Баримт бичиг (Documentation)

Бүх баримт бичгүүд `docs_all/` хавтаст нэгтгэгдсэн.

### Системийн баримт бичиг
| Файл | Тайлбар |
|------|---------|
| [System Architecture](docs_all/LIMS_-_System_Architecture.md) | Системийн бүтэц, BaseLab pattern, Data flow |
| [API Documentation](docs_all/LIMS_-_API_Documentation.md) | REST API endpoints, Water/Micro/Petro lab APIs |
| [Developer Onboarding](docs_all/LIMS_-_Developer_Onboarding_Guide.md) | Хөгжүүлэгчдэд зориулсан заавар |
| [Production Readiness](docs_all/LIMS_Production_Readiness_Report.md) | Production шалгалтын тайлан (95% бэлэн) |

### Аюулгүй байдал & ISO 17025
| Файл | Тайлбар |
|------|---------|
| [Security Documentation](docs_all/АЮУЛГҮЙ_БАЙДЛЫН_БАРИМТ_БИЧИГ.md) | SQL Injection, CSRF, Rate Limiting, Server Calculations |
| [ISO 17025 Compliance](docs_all/ISO_17025_БАРИМТ_БИЧИГ.md) | ISO/IEC 17025:2017 нийцэл (31% бүрэн, 34% хэсэгчлэн) |
| [Precision & Repeatability](docs_all/PRECISION_&_REPEATABILITY_БАРИМТ_БИЧИГ.md) | QC дүрмүүд, Westgard rules |

### Код шалгалтын тайлангууд
| Файл | Тайлбар |
|------|---------|
| [Sample Code Audit](docs_all/Sample_Registration_&_List_Code_Audit.md) | Дээж бүртгэл, жагсаалт |
| [Analysis Workspace Audit](docs_all/Analysis_Workspace_Code_Audit.md) | Шинжилгээний ажлын талбар |
| [Equipment Audit](docs_all/Equipment_Code_Audit.md) | Тоног төхөөрөмж |
| [Chemicals Audit](docs_all/Chemicals_Code_Audit.md) | Химийн бодис |
| [Role & Auth Audit](docs_all/Role_&_Authentication_Code_Audit.md) | Эрх, нэвтрэлт |

### Өөрчлөлтийн түүх
| Файл | Тайлбар |
|------|---------|
| [CHANGELOG](docs_all/CHANGELOG_-_LIMS_Сайжруулалтууд.md) | Бүх өөрчлөлтийн дэлгэрэнгүй түүх |
| [2026-02-05 Work Log](docs_all/WORK_LOG_—_2026-02-05_(Лхагва).md) | Сүүлийн өдрийн ажлын лог |

### Бусад
| Файл | Тайлбар |
|------|---------|
| [Operations Runbook](docs_all/LIMS_-_Operations_Runbook.md) | Системийн ашиглалтын заавар |
| [Monitoring Stack](docs_all/LIMS_-_Monitoring_Stack.md) | Prometheus, Grafana тохиргоо |
| [Template Macros](docs_all/Template_Macros_-_Хэрэглэх_заавар.md) | Jinja2 macro заавар |

---

## 📡 API Documentation

### Base URL
```
Production: https://lims.example.com/api
Development: http://localhost:5000/api
```

### Samples API
| Endpoint | Method | Тайлбар |
|----------|--------|---------|
| `/api/samples` | GET | Дээжний жагсаалт (pagination) |
| `/api/samples/{id}` | GET | Дээжний дэлгэрэнгүй |
| `/api/samples` | POST | Шинэ дээж бүртгэх |
| `/api/samples/{id}/status` | PATCH | Статус өөрчлөх |

### Analysis API
| Endpoint | Method | Тайлбар |
|----------|--------|---------|
| `/api/analysis/eligible_samples` | GET | Боломжит дээжүүд |
| `/api/analysis/save_results` | POST | Үр дүн хадгалах |
| `/api/analysis/update_status` | POST | Статус шинэчлэх |

### Lab-specific APIs
| Lab | Prefix | Endpoints |
|-----|--------|-----------|
| Water | `/labs/water/api/` | `data`, `eligible/{code}`, `save_results`, `standards` |
| Microbiology | `/labs/microbiology/api/` | `samples`, `data`, `save_results`, `save_batch` |
| Petrography | `/labs/petrography/api/` | `data`, `eligible/{code}`, `save_results` |

### QC API
| Endpoint | Method | Тайлбар |
|----------|--------|---------|
| `/api/qc/control_chart` | GET | Control chart data |
| `/api/qc/westgard_check` | POST | Westgard rules check |

Бүрэн API docs: [API Documentation](docs_all/LIMS_-_API_Documentation.md)

---

## 🔐 Аюулгүй байдал

### Security Score: 88/100

| Хамгаалалт | Статус | Тайлбар |
|------------|--------|---------|
| SQL Injection | ✅ | `escape_like_pattern()` + SQLAlchemy ORM |
| CSRF Protection | ✅ | Flask-WTF CSRF tokens |
| XSS Prevention | ✅ | Jinja2 auto-escaping + `html_escape()` |
| Password Policy | ✅ | 8+ chars, uppercase, lowercase, digits |
| Rate Limiting | ✅ | Login: 5/min, Global: 500/hour |
| Session Security | ✅ | HttpOnly, Secure, SameSite=Lax |
| Security Headers | ✅ | CSP, HSTS, X-Frame-Options |
| Audit Logging | ✅ | AuditLog + data_hash (ISO 17025) |
| 2FA | ❌ | Дараагийн хувилбарт |

### Server-side Calculations (CRITICAL)

Шинжилгээний үр дүн **серверт дахин тооцоологдоно** (tampering prevention):

```
JavaScript (feedback) → Server verification → Зөв утга → DB
```

- Client vs Server утга харьцуулна
- Зөрүү байвал `security.log`-д бичигдэнэ
- **СЕРВЕРИЙН утгыг хадгална**

### allowed_labs Access Control

Хэрэглэгч бүрийн `allowed_labs` талбар нь хандах боломжтой лабуудыг тодорхойлно:
- Зөвшөөрөгдөөгүй лабын route/API → 403 Forbidden
- `@lab_required('coal')` decorator ашиглана

### Дэлгэрэнгүй баримт бичиг

- [Security Documentation](docs_all/АЮУЛГҮЙ_БАЙДЛЫН_БАРИМТ_БИЧИГ.md)
- [Role & Auth Audit](docs_all/Role_&_Authentication_Code_Audit.md)

---

## 🤝 Contributing

### Хөгжүүлэлтийн workflow

1. Feature branch үүсгэх: `git checkout -b feature/your-feature`
2. Өөрчлөлт хийх
3. Тест бичих
4. Commit: `git commit -m "Add feature: your feature"`
5. Push: `git push origin feature/your-feature`
6. Pull Request үүсгэх

### Coding Standards

- Python: PEP 8 стандарт дагах
- Docstrings: Google-style docstrings
- Type hints: Бүх функцд type annotation
- Comments: Монгол хэл дээр
- Git commits: Англи хэл дээр

### Code Review Process

- [ ] Бүх тест давж байна
- [ ] Code coverage 80%+ байна
- [ ] Linting алдаагүй
- [ ] Documentation шинэчлэгдсэн
- [ ] Security checklist шалгагдсан

---

## 📄 Лиценз

Proprietary - LIMS by Gantulga

© 2024-2025 LIMS. Developed by Gantulga (semmganaa@gmail.com)

---

## 👥 Team

- **Project Lead:** Gantulga U.
- **Development:** LIMS Development
- **Testing:** Quality Assurance Team

---

## 📞 Support

- **Email:** support@energyresources.mn
- **Phone:** +976-xxxx-xxxx
- **Issues:** GitHub Issues

---

## 📝 Changelog

### Сүүлийн томоохон өөрчлөлтүүд

| Огноо | Өөрчлөлт |
|-------|----------|
| 2026-02-05 | Code audit дууссан: XSS fix, N+1 query, HashableMixin |
| 2026-02-04 | Equipment calibration + Spare parts integration |
| 2026-02-03 | Water lab workspace шинэчлэл + Нэгдсэн нэгтгэл |
| 2026-02-02 | Microbiology lab: Summary, Air/Swab categories |
| 2025-12-06 | Production security audit + Chat system |

Бүрэн түүх: [CHANGELOG](docs_all/CHANGELOG_-_LIMS_Сайжруулалтууд.md)

---

## 🙏 Acknowledgments

- Flask framework болон бусад open-source libraries
- AG Grid Community Edition
- Chart.js for data visualization
- LIMS customers

---

**Last Updated:** 2026-02-05
**Version:** 1.1.0
**Production Readiness:** 95% (Grade A)
