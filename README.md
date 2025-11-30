# Coal LIMS - Laboratory Information Management System

**Нүүрсний лабораторийн мэдээллийн удирдлагын систем**

[![Python](https://img.shields.io/badge/Python-3.8%2B-blue.svg)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-3.1.2-green.svg)](https://flask.palletsprojects.com/)
[![License](https://img.shields.io/badge/License-Proprietary-red.svg)]()

---

## 📋 Агуулга

1. [Төслийн тухай](#төслийн-тухай)
2. [Үндсэн функционалууд](#үндсэн-функционалууд)
3. [Технологийн стек](#технологийн-стек)
4. [Суулгах заавар](#суулгах-заавар)
5. [Тохиргоо](#тохиргоо)
6. [Хөгжүүлэлтийн орчин](#хөгжүүлэлтийн-орчин)
7. [Тест ажиллуулах](#тест-ажиллуулах)
8. [Deployment](#deployment)
9. [API Documentation](#api-documentation)
10. [Аюулгүй байдал](#аюулгүй-байдал)
11. [Contributing](#contributing)
12. [Лиценз](#лиценз)

---

## 🎯 Төслийн тухай

Coal LIMS нь **Energy Resources LLC** компанийн нүүрсний лабораторид зориулсан цогц лабораторийн мэдээллийн удирдлагын систем юм. Систем нь **ISO 17025** стандартын шаардлагыг хангахаар бүтээгдсэн.

### Зорилго

- 🔬 Нүүрсний дээжний бүртгэл, удирдлага
- 📊 Шинжилгээний үр дүнгий бүртгэл, тооцоолол
- 📈 Чанарын хяналтын удирдлага (QC)
- 📝 Тайлан, сертификат үүсгэх
- 🔧 Лабораторийн хэрэгслийн удирдлага
- 👥 Хэрэглэгчийн эрх, эрхийн удирдлага
- 📋 ISO 17025 дагуу мөрдөх баримт бичгийн удирдлага

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
- ✅ Role-based access control (admin, ahlah, senior, beltgegch, himich)
- ✅ Нууц үгний бодлого
- ✅ Login rate limiting
- ✅ Audit logging

---

## 🛠 Технологийн стек

### Backend
- **Framework:** Flask 3.1.2
- **Database ORM:** SQLAlchemy 2.0.44
- **Migration:** Alembic 1.17.1
- **Authentication:** Flask-Login 0.6.3
- **Forms:** Flask-WTF 1.2.1
- **Security:** Flask-Limiter, CSRF Protection
- **Database:** SQLite (development), PostgreSQL (production ready)

### Frontend
- **HTML Templates:** Jinja2
- **CSS Framework:** Bootstrap 5
- **JavaScript:** Vanilla JS + DataTables
- **Charts:** Chart.js
- **Excel Export:** openpyxl

### Python Libraries
- **Data Processing:** pandas, numpy
- **Math:** statistics, scipy
- **Date/Time:** python-dateutil, pytz
- **Email:** Flask-Mail

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
Description=Coal LIMS
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

## 📚 API Documentation

API баримт бичиг: http://localhost:5000/api/docs (Swagger UI)

### Үндсэн endpoints

#### Samples
- `GET /api/samples/data` - Get samples list (DataTables)
- `GET /api/sample_summary` - Sample summary with results
- `GET /api/check_ready_samples` - Check samples ready for analysis

#### Analysis
- `GET /api/eligible_samples/<code>` - Get eligible samples for analysis
- `POST /api/analysis/save_results` - Save analysis results
- `PUT /api/update_result_status/<id>/<status>` - Approve/reject results

#### Equipment
- `GET /api/equipment` - List equipment
- `POST /api/equipment` - Create equipment
- `PUT /api/equipment/<id>` - Update equipment

Бүрэн API docs: [API.md](docs/API.md) файл үзнэ үү.

---

## 🔐 Аюулгүй байдал

### Хэрэгжүүлсэн хамгаалалтууд

- ✅ **SQL Injection Protection** - SQLAlchemy ORM + parameterized queries
- ✅ **CSRF Protection** - Flask-WTF CSRF tokens on all forms
- ✅ **XSS Prevention** - Jinja2 auto-escaping
- ✅ **Password Policy** - Minimum 8 chars, uppercase, lowercase, digits
- ✅ **Rate Limiting** - Login: 5/min, API: 30/min
- ✅ **Session Security** - HttpOnly, Secure, SameSite cookies
- ✅ **Input Validation** - Comprehensive validation on all endpoints
- ✅ **Audit Logging** - All critical actions logged

### Security Checklist

Дэлгэрэнгүй: [SECURITY_CHECKLIST.md](SECURITY_CHECKLIST.md)

### Reported Vulnerabilities

Аюулгүй байдлын асуудал илрүүлбэл:
- Email: security@example.com
- Эсвэл GitHub Issues (private)

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

Proprietary - Energy Resources LLC

© 2024-2025 Energy Resources LLC. All rights reserved.

---

## 👥 Team

- **Project Lead:** Gantulga U.
- **Development:** Energy Resources IT Team
- **Testing:** Quality Assurance Team

---

## 📞 Support

- **Email:** support@energyresources.mn
- **Phone:** +976-xxxx-xxxx
- **Issues:** GitHub Issues

---

## 📝 Changelog

Өөрчлөлтийн түүх: [CHANGELOG.md](CHANGELOG.md)

---

## 🙏 Acknowledgments

- Flask framework болон бусад open-source libraries
- MongoDB Mongolian User Group community
- Energy Resources LLC management

---

**Last Updated:** 2025-11-29
**Version:** 1.0.0
