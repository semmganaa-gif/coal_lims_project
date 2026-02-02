# ТЕСТИЙН БАРИМТ БИЧИГ
# LIMS System
# Огноо: 2025-12-04

---

## 1. ХУРААНГУЙ

| Категори | Тоо |
|----------|-----|
| **Smoke Tests** | 12 тест |
| **Unit Tests** | 12 тест |
| **Integration Tests** | 14 тест |
| **Load Test Scenarios** | 6 сценари |
| **Security Tests** | 8 тест |
| **Нийт** | 52+ тест |

**Тест код:** ~1,900 мөр

---

## 2. ТЕСТИЙН БҮТЭЦ

```
tests/
├── __init__.py
├── conftest.py              # Test fixtures
├── test_smoke.py            # Smoke tests (12)
├── unit/
│   ├── __init__.py
│   ├── test_error_handling.py
│   ├── test_validators.py
│   └── test_conversions.py
├── integration/
│   ├── __init__.py
│   ├── test_csrf_protection.py
│   ├── test_sample_workflow.py
│   └── test_analysis_workflow.py
├── security/
│   ├── __init__.py
│   ├── test_sql_injection.py
│   ├── test_xss.py
│   └── test_csrf.py
└── load/
    └── locustfile.py        # Load testing
```

---

## 3. ТЕСТ FIXTURES

### 3.1 conftest.py

```python
@pytest.fixture(scope="session")
def app():
    """Test app with in-memory SQLite"""
    # TESTING=True, WTF_CSRF_ENABLED=False
    # Creates test users: admin, himich, ahlah
    # Password: TestPass123

@pytest.fixture
def client(app):
    """Flask test client"""

@pytest.fixture
def db(app):
    """Database access"""

@pytest.fixture
def auth_user(client):
    """Authenticated regular user (himich)"""

@pytest.fixture
def auth_admin(client):
    """Authenticated admin user"""
```

---

## 4. ТЕСТ ТӨРЛҮҮД

### 4.1 Unit Tests

**Файл:** `tests/unit/test_error_handling.py`

| Тест | Зорилго |
|------|---------|
| `test_admin_priority_validation_handles_value_error` | ValueError handling |
| `test_equipment_edit_handles_integrity_error` | IntegrityError handling |
| `test_mass_api_handles_integrity_errors` | Mass API error handling |
| `test_sample_registration_rollback_on_error` | Transaction rollback |
| `test_file_upload_validates_size` | 5MB limit |
| `test_file_upload_validates_extension` | Allowed extensions |
| `test_mass_save_uses_bulk_query` | N+1 query fix |

### 4.2 Integration Tests

**Файл:** `tests/integration/test_csrf_protection.py`

| Тест | Зорилго |
|------|---------|
| `test_csrf_required_add_equipment` | CSRF on add |
| `test_csrf_required_edit_equipment` | CSRF on edit |
| `test_csrf_required_bulk_delete` | CSRF on delete |
| `test_csrf_token_in_forms` | Token presence |
| `test_valid_csrf_accepted` | Valid token |
| `test_invalid_csrf_rejected` | Invalid token |

### 4.3 Security Tests

**Файл:** `tests/security/`

| Тест | Зорилго |
|------|---------|
| `test_sql_injection_protection` | SQL injection prevention |
| `test_xss_protection` | XSS prevention |
| `test_csrf_protection` | CSRF bypass attempts |
| `test_authentication_bypass` | Access control |
| `test_file_upload_security` | Malicious file uploads |

### 4.4 Load Tests

**Файл:** `tests/load/locustfile.py`

| Сценари | Зорилго |
|---------|---------|
| `CoalLIMSUser` (legacy нэр) | Mixed usage patterns |
| `PaginationBenchmark` | Pagination performance |
| `IndexBenchmark` | Database index performance |
| `EquipmentListLoadTest` | Equipment list scenarios |
| `SampleListLoadTest` | Sample list scenarios |
| `ConcurrentWriteTest` | Race condition testing |

### 4.5 Multi-Lab Tests

Лаб бүрийн API endpoint тест: Water (`/labs/water/api/*`), Microbiology (`/labs/microbiology/api/*`), Petrography (`/labs/petrography/api/*`)

---

## 5. ТЕСТ АЖИЛЛУУЛАХ

### 5.1 Үндсэн командууд

```bash
# Бүх тест
pytest tests/ -v

# Smoke tests
pytest tests/test_smoke.py -v

# Unit tests
pytest tests/unit/ -v

# Integration tests
pytest tests/integration/ -v

# Security tests
pytest tests/security/ -v

# Coverage report
pytest --cov=app --cov-report=html:htmlcov
```

### 5.2 Test Runner

```bash
# Бүх тестүүд
python run_tests.py

# Тодорхой suite
python run_tests.py --unit
python run_tests.py --integration
python run_tests.py --security

# Coverage-тай
python run_tests.py --coverage
```

### 5.3 Load Tests

```bash
# App эхлүүлэх
python run.py

# Load test ажиллуулах
locust -f tests/load/locustfile.py --host=http://localhost:5000

# Headless mode
locust -f tests/load/locustfile.py --host=http://localhost:5000 \
    --users 100 --spawn-rate 10 --run-time 2m --headless
```

---

## 6. ТЕСТИЙН ҮР ДҮН

### 6.1 Smoke Tests

```
============================= test session starts =============================
collected 12 items

tests/test_smoke.py::TestInfrastructure::test_app_exists PASSED
tests/test_smoke.py::TestInfrastructure::test_database_connection PASSED
tests/test_smoke.py::TestInfrastructure::test_test_users_created PASSED
tests/test_smoke.py::TestInfrastructure::test_password_validation PASSED
tests/test_smoke.py::TestFixtures::test_client_fixture PASSED
...

========================== 9 passed, 3 expected failures ======================
```

### 6.2 Coverage

| Module | Coverage |
|--------|----------|
| app/routes/ | ~40% |
| app/utils/ | ~60% |
| app/models.py | ~50% |
| **Total** | ~45% |

---

## 7. HIGH-PRIORITY FIXES ТЕСТЛЭСЭН

| Fix | Тест |
|-----|------|
| Bare exception handlers | ✅ `test_admin_priority_validation_handles_value_error` |
| Database commit errors | ✅ `test_mass_api_handles_integrity_errors` |
| Transaction atomicity | ✅ `test_sample_registration_rollback_on_error` |
| File upload validation | ✅ `test_file_upload_validates_size` |
| N+1 queries | ✅ `test_mass_save_uses_bulk_query` |
| CSRF protection | ✅ `test_csrf_required_*` |
| Pagination | ✅ Load tests |
| Database indexes | ✅ `IndexBenchmark` |

---

## 8. DEPENDENCIES

```
pytest==9.0.1
pytest-flask==1.3.0
pytest-cov==7.0.0
pytest-mock==3.15.1
coverage==7.8.0
faker==38.2.0
locust==2.17.0
```

**Суулгах:**
```bash
pip install pytest pytest-flask pytest-cov pytest-mock coverage faker locust
```

---

## 9. ТЕСТ БИЧИХ ЗААВАР

### 9.1 Unit Test

```python
def test_calculation_correct():
    """Test that calculation returns expected result"""
    raw_data = {"p1": {"m1": 10.0, "m2": 1.0, "m3": 10.97}}
    result = calc_moisture_mad(raw_data)
    assert result == pytest.approx(3.0, rel=0.01)
```

### 9.2 Integration Test

```python
def test_api_requires_authentication(client):
    """Test that API requires login"""
    response = client.post('/api/save_results', json={})
    assert response.status_code == 401
```

### 9.3 Security Test

```python
def test_sql_injection_prevented(client, auth):
    """Test SQL injection is blocked"""
    auth.login()
    response = client.get('/api/samples?q=\'; DROP TABLE sample; --')
    assert response.status_code == 200
    # Table should still exist
```

---

## 10. ДАРААГИЙН АЛХАМУУД

1. [ ] Coverage 80%+ болгох
2. [ ] Бүх API endpoint-уудад тест нэмэх
3. [ ] E2E тест нэмэх (Playwright/Selenium)
4. [ ] CI/CD pipeline тохируулах
5. [ ] Автомат regression тест

---

**Сүүлд шинэчилсэн:** 2025-12-04
