# Coal LIMS - Developer Onboarding Guide

## Тавтай морилно уу!

Энэхүү гарын авлага нь Coal LIMS төсөлд шинээр нэгдэж буй хөгжүүлэгчдэд зориулагдсан.

---

## 1. Орчин бэлтгэх

### 1.1 Шаардлагатай хэрэгслүүд

```bash
# Python 3.11+
python --version  # Python 3.11.x

# Node.js 18+
node --version  # v18.x or higher

# Docker & Docker Compose
docker --version
docker-compose --version

# Git
git --version

# PostgreSQL client (optional)
psql --version
```

### 1.2 IDE тохиргоо

**VS Code extensions:**
- Python (Microsoft)
- Pylance
- Flask Snippets
- GitLens
- Docker
- PostgreSQL

**PyCharm:**
- Flask support идэвхжүүлэх
- Python interpreter тохируулах

### 1.3 Код татаж авах

```bash
# Clone repo
git clone https://github.com/your-org/coal-lims.git
cd coal-lims

# Create virtual environment
python -m venv venv

# Activate (Windows)
venv\Scripts\activate

# Activate (Linux/Mac)
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Install dev dependencies
pip install -r requirements-dev.txt
```

### 1.4 Environment тохиргоо

```bash
# Copy example env
cp .env.example .env

# Edit .env file
SECRET_KEY=your-dev-secret-key
DATABASE_URL=postgresql://lims_user:password@localhost:5432/coal_lims
REDIS_URL=redis://localhost:6379/0
FLASK_ENV=development
FLASK_DEBUG=1
```

### 1.5 Database эхлүүлэх

```bash
# Docker ашиглах
docker-compose up -d db redis

# Migrations ажиллуулах
flask db upgrade

# Test users үүсгэх
flask users create admin Admin123! admin
flask users create chemist Chemist123! chemist
```

### 1.6 Application эхлүүлэх

```bash
# Development server
flask run --debug

# Or with hot reload
flask run --reload

# Open browser
# http://localhost:5000
```

---

## 2. Төслийн бүтэц

```
coal_lims_project/
├── app/                    # Flask application
│   ├── __init__.py        # App factory
│   ├── models.py          # Database models
│   ├── constants.py       # Analysis aliases
│   ├── routes/            # Blueprints
│   │   ├── main/          # Main pages
│   │   ├── analysis/      # Analysis workspace
│   │   ├── api/           # REST API
│   │   └── ...
│   ├── services/          # Business logic
│   ├── repositories/      # Data access layer
│   ├── utils/             # Utility functions
│   ├── templates/         # Jinja2 templates
│   └── static/            # CSS, JS, images
├── migrations/            # Alembic migrations
├── tests/                 # pytest tests
├── e2e/                   # Playwright E2E tests
├── docs/                  # Documentation
├── monitoring/            # Prometheus, Grafana
└── performance/           # k6, locust tests
```

---

## 3. Код стандарт

### 3.1 Python Style

```python
# Type hints ашиглах
def get_sample(sample_id: int) -> Sample | None:
    return Sample.query.get(sample_id)

# Docstrings
def calculate_result(raw_data: dict) -> float:
    """
    Түүхий өгөгдлөөс эцсийн үр дүн тооцоолох.

    Args:
        raw_data: Түүхий хэмжилтийн өгөгдөл

    Returns:
        Эцсийн тооцоолсон үр дүн

    Raises:
        ValueError: Өгөгдөл буруу бол
    """
    pass
```

### 3.2 Linting & Formatting

```bash
# Run ruff (linting)
ruff check app/

# Auto-fix
ruff check app/ --fix

# Type checking
mypy app/

# Run all checks
make lint
```

### 3.3 Git Workflow

```bash
# Feature branch
git checkout -b feature/add-new-analysis

# Commit convention
git commit -m "feat: Add phosphorus analysis calculation"
git commit -m "fix: Correct repeatability check for CV"
git commit -m "test: Add tests for QC validation"
git commit -m "docs: Update API documentation"

# Push and create PR
git push -u origin feature/add-new-analysis
```

**Commit prefixes:**
- `feat:` - Шинэ feature
- `fix:` - Bug засах
- `test:` - Тест нэмэх
- `docs:` - Documentation
- `refactor:` - Код сайжруулах
- `chore:` - Бусад (dependencies, config)

---

## 4. Тест бичих

### 4.1 Unit Test

```python
# tests/test_normalize.py
import pytest
from app.utils.normalize import normalize_analysis_code

class TestNormalizeCode:
    def test_lowercase_conversion(self):
        assert normalize_analysis_code("AAD") == "aad"

    def test_alias_mapping(self):
        assert normalize_analysis_code("üns") == "aad"

    def test_empty_string(self):
        assert normalize_analysis_code("") == ""
```

### 4.2 Integration Test

```python
# tests/test_analysis_api.py
class TestSaveResults:
    def test_save_valid_result(self, client, auth_admin, test_sample):
        response = client.post('/api/analysis/save_results', json={
            'sample_id': test_sample.id,
            'data': [{
                'analysis_code': 'Aad',
                'raw_data': {'value': '12.5'},
                'final_result': 12.5
            }]
        })
        assert response.status_code == 200
```

### 4.3 Тест ажиллуулах

```bash
# All tests
pytest

# Specific file
pytest tests/test_normalize.py

# With coverage
pytest --cov=app --cov-report=html

# Watch mode
pytest-watch

# E2E tests
npm run e2e
```

---

## 5. Шинэ Feature нэмэх

### 5.1 Жишээ: Шинэ шинжилгээ нэмэх

**1. Constant нэмэх:**
```python
# app/constants.py
ALIAS_TO_BASE_ANALYSIS = {
    ...
    "new_analysis": "NewAn",
    "na": "NewAn",
}
```

**2. Тооцооллын логик:**
```python
# app/utils/server_calculations.py
def calculate_new_analysis(raw_data: dict) -> float:
    """NewAnalysis тооцоолох."""
    a = float(raw_data.get('A', 0))
    b = float(raw_data.get('B', 0))
    return round((a - b) / a * 100, 2)
```

**3. Validator нэмэх:**
```python
# app/utils/validators.py
def validate_new_analysis(value: float) -> tuple[bool, str]:
    if value < 0 or value > 100:
        return False, "Утга 0-100 хооронд байх ёстой"
    return True, ""
```

**4. Template засах:**
```html
<!-- app/templates/analysis/workspace.html -->
<option value="NewAn">New Analysis</option>
```

**5. Тест бичих:**
```python
# tests/test_new_analysis.py
def test_calculate_new_analysis():
    result = calculate_new_analysis({'A': 10, 'B': 2})
    assert result == 80.0
```

---

## 6. Debugging

### 6.1 Flask Debug

```python
# Add breakpoint
import pdb; pdb.set_trace()

# Or use debugpy for VS Code
import debugpy
debugpy.listen(5678)
debugpy.wait_for_client()
```

### 6.2 SQL Queries

```python
# Enable SQL echo
app.config['SQLALCHEMY_ECHO'] = True

# Or in shell
from app import db
db.session.execute(text("EXPLAIN ANALYZE SELECT ..."))
```

### 6.3 Log level

```bash
# In .env
LOG_LEVEL=DEBUG
```

---

## 7. Чухал файлууд

| Файл | Тайлбар |
|------|---------|
| `app/__init__.py` | App factory, extensions |
| `app/models.py` | All database models |
| `app/constants.py` | Analysis codes mapping |
| `app/utils/normalize.py` | Data normalization |
| `app/utils/westgard.py` | QC rules |
| `config.py` | Application configuration |
| `migrations/` | Database migrations |

---

## 8. Түгээмэл асуултууд

### Q: Шинэ model хэрхэн нэмэх вэ?

```python
# 1. app/models.py дээр class нэмэх
class NewModel(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))

# 2. Migration үүсгэх
flask db migrate -m "Add NewModel"

# 3. Migration ажиллуулах
flask db upgrade
```

### Q: API endpoint хэрхэн нэмэх вэ?

```python
# app/routes/api/new_api.py
from flask import Blueprint, jsonify

bp = Blueprint('new_api', __name__, url_prefix='/api/new')

@bp.route('/items', methods=['GET'])
def get_items():
    return jsonify({'items': []})

# app/routes/api/__init__.py дээр бүртгэх
from app.routes.api.new_api import bp as new_bp
api_bp.register_blueprint(new_bp)
```

### Q: Background task хэрхэн ажиллуулах вэ?

Одоогоор Celery тохируулаагүй. Энгийн thread ашиглах:

```python
from threading import Thread

def long_task():
    # Heavy processing
    pass

thread = Thread(target=long_task)
thread.start()
```

---

## 9. Холбогдох материалууд

- [Architecture](./ARCHITECTURE.md)
- [API Documentation](./API.md)
- [Runbook](./RUNBOOK.md)
- [Flask Documentation](https://flask.palletsprojects.com/)
- [SQLAlchemy Documentation](https://docs.sqlalchemy.org/)

---

## 10. Тусламж авах

- **Slack**: #lims-dev channel
- **Email**: dev-team@example.com
- **Wiki**: https://wiki.example.com/lims

Асуулт байвал чөлөөтэй асуугаарай!
