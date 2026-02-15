# Testing Guide - Coal LIMS

**Last Updated:** 2026-02-15

---

## Table of Contents

1. [Test Strategy Overview](#1-test-strategy-overview)
2. [Test Structure](#2-test-structure)
3. [Running Tests](#3-running-tests)
4. [Test Categories](#4-test-categories)
5. [Writing New Tests](#5-writing-new-tests)
6. [Fixtures Reference](#6-fixtures-reference)
7. [Coverage Targets](#7-coverage-targets)
8. [CI/CD Integration](#8-cicd-integration)
9. [Best Practices](#9-best-practices)

---

## 1. Test Strategy Overview

The Coal LIMS project employs a multi-layered testing strategy designed to ensure reliability and security for a laboratory information management system handling four laboratories (Coal, Water Chemistry, Microbiology, Petrography).

| Metric                | Value           |
|-----------------------|-----------------|
| **Total test files**  | 402             |
| **Total lines of test code** | ~118,000 |
| **Overall line coverage** | 39.3%       |
| **Minimum coverage gate** | 25% (pytest.ini) / 80% (CI) |
| **Test framework**    | pytest 7.4+     |
| **Test database**     | SQLite in-memory |
| **CI/CD**             | GitHub Actions   |

The testing strategy covers:

- **Unit tests** for utility functions, calculations, validators, and model methods
- **Integration tests** for Flask routes, API endpoints, and database workflows
- **Security tests** for SQL injection, XSS, CSRF, and authentication bypass
- **Load tests** (Locust) for performance validation under concurrent access

---

## 2. Test Structure

### 2.1 Folder Layout

```
tests/
├── __init__.py
├── conftest.py                          # Shared fixtures (app, client, auth, db, factories)
├── test_smoke.py                        # Smoke tests (basic health checks)
│
├── unit/                                # Well-organized unit tests (24 files)
│   ├── test_analysis_assignment.py
│   ├── test_analysis_audit.py
│   ├── test_analysis_rules.py
│   ├── test_api_docs.py
│   ├── test_audit.py
│   ├── test_cli.py
│   ├── test_conversions.py
│   ├── test_converters.py
│   ├── test_database_utils.py
│   ├── test_datetime.py
│   ├── test_decorators.py
│   ├── test_exports.py
│   ├── test_hardware_fingerprint.py
│   ├── test_logging_config.py
│   ├── test_normalize.py
│   ├── test_parameters.py
│   ├── test_qc_utils.py
│   ├── test_schemas.py
│   ├── test_security.py
│   ├── test_server_calculations.py
│   ├── test_shifts.py
│   ├── test_sorting.py
│   ├── test_validators.py
│   └── test_westgard.py
│
├── test_unit_*.py                       # Unit tests at root level (~97 files)
│   ├── test_unit_analysis_rules.py
│   ├── test_unit_server_calculations.py
│   ├── test_unit_validators.py
│   ├── test_unit_decorators.py
│   ├── test_unit_models.py
│   ├── test_unit_exports.py
│   └── ... (more unit test files)
│
├── test_int_*.py                        # Integration tests (~114 files)
│   ├── test_int_admin_routes.py
│   ├── test_int_analysis_api.py
│   ├── test_int_equipment_routes.py
│   ├── test_int_index_routes.py
│   ├── test_int_quality_routes.py
│   ├── test_int_report_routes.py
│   ├── test_int_samples_api.py
│   ├── test_int_senior_routes.py
│   └── ... (more integration test files)
│
├── test_*_coverage*.py                  # Coverage-focused tests
├── test_*_boost*.py                     # Coverage boost tests
├── test_*_deep*.py                      # Deep/thorough test suites
├── test_*_100*.py                       # Full-coverage target tests
│
├── test_license_protection*.py          # License protection tests
├── test_security_*.py                   # Security-focused tests
└── test_integration_api.py              # Cross-module API integration tests
```

### 2.2 Naming Conventions

| Pattern                  | Purpose                                    |
|--------------------------|--------------------------------------------|
| `test_unit_*.py`         | Unit tests (root level, ~97 files)         |
| `unit/test_*.py`         | Unit tests (organized subdirectory, 24 files) |
| `test_int_*.py`          | Integration tests (~114 files)             |
| `test_*_coverage*.py`    | Tests targeting specific coverage gaps     |
| `test_*_boost*.py`       | Additional coverage boost tests            |
| `test_*_deep*.py`        | Thorough/deep test scenarios               |
| `test_*_100*.py`         | Tests aiming for 100% coverage of a module |
| `test_*_push*.py`        | Tests added to push coverage higher        |
| `test_*_full*.py`        | Comprehensive full-coverage tests          |
| `test_smoke.py`          | Smoke tests for basic health checks        |

---

## 3. Running Tests

### 3.1 All Tests

```bash
# Run all tests (uses settings from pytest.ini)
pytest

# Run all tests with verbose output
pytest -v

# Run all tests, stop on first failure
pytest -x

# Run all tests, show first N failures
pytest --maxfail=3
```

### 3.2 Specific Module or File

```bash
# Run a specific test file
pytest tests/test_smoke.py

# Run all unit tests in the unit/ subdirectory
pytest tests/unit/

# Run all integration tests (test_int_ prefix)
pytest tests/ -k "test_int_"

# Run a specific test class
pytest tests/test_smoke.py::TestInfrastructure

# Run a specific test function
pytest tests/test_smoke.py::TestInfrastructure::test_app_exists

# Run tests matching a keyword expression
pytest -k "server_calculations"

# Run tests for a specific module area
pytest -k "validators or conversions"
```

### 3.3 With Coverage

```bash
# Run with HTML coverage report (output to htmlcov/)
pytest --cov=app --cov-report=html

# Run with terminal coverage report showing missing lines
pytest --cov=app --cov-report=term-missing

# Run with XML coverage report (for CI/CD)
pytest --cov=app --cov-report=xml

# Run with all report types and a minimum coverage threshold
pytest --cov=app --cov-report=html --cov-report=term-missing --cov-report=xml --cov-fail-under=25

# Generate coverage for a specific module only
pytest --cov=app.utils --cov-report=term-missing tests/unit/
```

> **Note:** The default `pytest.ini` configuration already includes `--cov=app`, `--cov-report=html`, `--cov-report=term-missing`, `--cov-report=xml`, and `--cov-fail-under=25`. Running `pytest` without arguments will produce all coverage reports automatically.

### 3.4 Verbose and Debug Modes

```bash
# Verbose output (default via pytest.ini)
pytest -v

# Extra verbose with local variables in tracebacks (default via pytest.ini)
pytest -v --showlocals

# Short traceback format
pytest --tb=short

# Full traceback format
pytest --tb=long

# Run with print output visible
pytest -s

# Run with detailed output and print statements
pytest -v -s
```

### 3.5 Using Markers

```bash
# Run only smoke tests
pytest -m smoke

# Run only unit tests
pytest -m unit

# Run only integration tests
pytest -m integration

# Run only security tests
pytest -m security

# Run only API tests
pytest -m api

# Skip slow tests
pytest -m "not slow"

# Combine markers
pytest -m "unit and not slow"
```

### 3.6 Load Tests

Load testing uses [Locust](https://locust.io/). The locustfile was originally in `tests/load/locustfile.py` (referenced in historical docs). To run:

```bash
# Start the application first
python run.py

# Run Locust with web UI (http://localhost:8089)
locust -f tests/load/locustfile.py --host=http://localhost:5000

# Run Locust headless (no web UI)
locust -f tests/load/locustfile.py --host=http://localhost:5000 \
    --users 100 --spawn-rate 10 --run-time 2m --headless
```

---

## 4. Test Categories

### 4.1 Unit Tests

Unit tests validate individual functions, calculations, and utility modules in isolation. They form the largest category with ~97 root-level files and 24 files in `tests/unit/`.

**Key areas covered:**

| Module                  | Test File(s)                                        | Coverage |
|-------------------------|-----------------------------------------------------|----------|
| `utils/server_calculations.py` | `unit/test_server_calculations.py`, `test_server_calculations_*.py` | Comprehensive |
| `utils/validators.py`   | `unit/test_validators.py`, `test_validators_*.py`  | Comprehensive |
| `utils/analysis_rules.py` | `unit/test_analysis_rules.py`, `test_analysis_rules_*.py` | Comprehensive |
| `utils/westgard.py`     | `unit/test_westgard.py`, `test_westgard_*.py`      | 100%     |
| `utils/shifts.py`       | `unit/test_shifts.py`, `test_shifts_*.py`           | 100%     |
| `utils/exports.py`      | `unit/test_exports.py`, `test_exports_*.py`         | 100%     |
| `utils/converters.py`   | `unit/test_converters.py`, `test_converters_*.py`   | 100%     |
| `utils/normalize.py`    | `unit/test_normalize.py`, `test_normalize_*.py`     | Comprehensive |
| `utils/security.py`     | `unit/test_security.py`, `test_unit_security_utils.py` | 100%  |
| `utils/database.py`     | `unit/test_database_utils.py`, `test_database_*.py` | 100%     |
| `utils/datetime.py`     | `unit/test_datetime.py`                              | 100%     |
| `utils/decorators.py`   | `unit/test_decorators.py`, `test_decorators_*.py`   | Comprehensive |
| `schemas/`              | `unit/test_schemas.py`, `test_schemas_*.py`          | 93.8%    |
| `models/`               | `test_unit_models*.py`                               | 83.0%    |

**Example unit test:**

```python
import pytest

def test_moisture_calculation_correct():
    """Test that Mad (moisture) calculation returns expected result."""
    raw_data = {"p1": {"m1": 10.0, "m2": 1.0, "m3": 10.97}}
    result = calc_moisture_mad(raw_data)
    assert result == pytest.approx(3.0, rel=0.01)

def test_csn_value_within_range():
    """Test that CSN value stays in 0-9 range."""
    assert validate_csn_range(5) is True
    assert validate_csn_range(10) is False
    assert validate_csn_range(-1) is False
```

### 4.2 Integration Tests

Integration tests verify Flask routes, API endpoints, and end-to-end workflows involving the database. There are ~114 files prefixed with `test_int_`.

**Key areas covered:**

| Area                    | Test File(s)                                       |
|-------------------------|---------------------------------------------------|
| Admin routes            | `test_int_admin_routes*.py` (5 files)             |
| Analysis API            | `test_int_analysis_api*.py` (4 files)             |
| Analysis QC             | `test_int_analysis_qc*.py` (2 files)              |
| Equipment routes        | `test_int_equipment_routes*.py` (3 files)         |
| Import/CSV routes       | `test_int_import_routes*.py` (6 files)            |
| Index/Dashboard         | `test_int_index_*.py` (8 files)                   |
| KPI routes              | `test_int_kpi_*.py` (5 files)                     |
| Quality management      | `test_int_quality_*.py` (5 files)                 |
| Report routes           | `test_int_report_*.py` (5 files)                  |
| Sample API/workflow     | `test_int_samples_*.py` (5 files)                 |
| Senior workspace        | `test_int_senior_*.py` (4 files)                  |
| Settings routes         | `test_int_settings_*.py` (4 files)                |
| Authentication          | `test_int_auth_routes.py`, `test_int_main_routes*.py` |
| CSRF protection         | `test_int_csrf_protection.py`                      |

**Example integration test:**

```python
def test_api_requires_authentication(client):
    """Test that API endpoints require login."""
    response = client.post('/api/save_results', json={})
    assert response.status_code in (401, 302)  # Unauthorized or redirect to login

def test_sample_registration_workflow(auth_user, db):
    """Test complete sample registration workflow."""
    response = auth_user.post('/api/samples', json={
        'sample_code': 'TEST-001',
        'client_name': 'QC',
        'sample_type': 'Coal'
    })
    assert response.status_code == 200
    data = response.get_json()
    assert data['success'] is True
```

### 4.3 Security Tests

Security tests verify protection against common web vulnerabilities. These are critical for a LIMS system handling laboratory data with ISO 17025 compliance requirements.

| Test Area              | Test File(s)                                        |
|------------------------|-----------------------------------------------------|
| SQL injection          | `test_security_deep.py`, `unit/test_security.py`   |
| XSS prevention         | `test_unit_security_utils.py`                       |
| CSRF protection        | `test_int_csrf_protection.py`                       |
| Authentication bypass  | `test_int_auth_routes.py`                           |
| License protection     | `test_license_protection.py`, `test_license_protection_deep.py`, `test_license_protection_full.py` |
| Security settings      | `test_security_settings_full.py`                    |

**Example security test:**

```python
def test_sql_injection_prevented(client, auth):
    """Test that SQL injection is blocked in sample search."""
    auth.login()
    response = client.get("/api/samples?q='; DROP TABLE sample; --")
    assert response.status_code == 200
    # The table must still exist and the response must be valid JSON
    data = response.get_json()
    assert 'success' in data
```

### 4.4 API Tests

API tests verify JSON endpoints under `app/routes/api/`. They are a subset of integration tests but focused specifically on request/response validation.

| Endpoint Area          | Test File(s)                                        |
|------------------------|-----------------------------------------------------|
| Analysis API           | `test_analysis_api_*.py`, `test_int_analysis_api*.py` |
| Samples API            | `test_samples_api_*.py`, `test_int_samples_api*.py` |
| Quality API            | `test_int_quality_api_routes.py`                    |
| Report API             | `test_int_report_api_routes.py`                     |
| KPI API                | `test_int_kpi_api_routes.py`                        |
| Audit API              | `test_int_api_comprehensive.py`                     |
| Chat API               | `test_int_chat_api_comprehensive.py`                |

---

## 5. Writing New Tests

### 5.1 File Naming

All test files must follow the `test_*.py` naming pattern (configured in `pytest.ini`).

Recommended naming conventions:

- **Unit tests:** Place in `tests/unit/test_<module_name>.py` or `tests/test_unit_<module_name>.py`
- **Integration tests:** Place in `tests/test_int_<route_or_feature>.py`
- **Security tests:** Include `security` in the filename
- **Coverage-targeted:** Append `_coverage`, `_boost`, or `_100` to the base name

### 5.2 Using Fixtures from conftest.py

The `tests/conftest.py` file provides several fixtures. Import them by name in your test function signatures:

```python
def test_with_app(app):
    """Access the Flask application instance."""
    assert app.config['TESTING'] is True

def test_with_client(client):
    """Use the Flask test client for HTTP requests."""
    response = client.get('/')
    assert response.status_code in (200, 302)

def test_with_database(db):
    """Access the SQLAlchemy database session."""
    from app.models import User
    users = User.query.all()
    assert len(users) >= 3  # admin, chemist, senior

def test_with_authenticated_user(auth_user):
    """Make requests as an authenticated chemist user."""
    response = auth_user.get('/coal')
    assert response.status_code == 200

def test_with_authenticated_admin(auth_admin):
    """Make requests as an authenticated admin user."""
    response = auth_admin.get('/admin/users')
    assert response.status_code == 200

def test_with_auth_actions(client, auth):
    """Use the AuthActions helper for login/logout control."""
    auth.login(username='chemist', password='TestPass123')
    response = client.get('/coal')
    assert response.status_code == 200
    auth.logout()

def test_with_auth_client(auth_client):
    """Use AuthClient for integration tests with follow_redirects."""
    auth_client.login()            # Login as chemist
    auth_client.login_as_admin()   # Login as admin
    auth_client.logout()

def test_with_sample(test_sample):
    """Use a pre-created test sample."""
    assert test_sample.sample_code.startswith('TEST-')
    assert test_sample.client_name == 'QC'

def test_with_sample_factory(sample_factory):
    """Use the factory to create multiple samples with custom attributes."""
    sample1 = sample_factory.create(client_name='Client A')
    sample2 = sample_factory.create(client_name='Client B', sample_type='Water')
    assert sample1.client_name == 'Client A'
    assert sample2.sample_type == 'Water'

def test_with_init_database(init_database):
    """Use pre-initialized database with 3 test samples."""
    assert len(init_database) == 3
```

### 5.3 Testing Flask Routes

```python
def test_index_page_requires_login(client):
    """Test that the index page redirects unauthenticated users."""
    response = client.get('/')
    assert response.status_code == 302
    assert '/login' in response.headers['Location']

def test_coal_hub_renders(auth_user):
    """Test that the coal hub page renders successfully."""
    response = auth_user.get('/coal')
    assert response.status_code == 200
    assert b'coal' in response.data.lower() or response.status_code == 200

def test_post_route_with_form_data(auth_admin):
    """Test a POST route that accepts form data."""
    response = auth_admin.post('/admin/users/create', data={
        'username': 'newuser',
        'password': 'NewPass123',
        'role': 'chemist'
    }, follow_redirects=True)
    assert response.status_code == 200
```

### 5.4 Testing API Endpoints

```python
import json

def test_api_returns_json(auth_user):
    """Test that API endpoints return valid JSON."""
    response = auth_user.get('/api/samples/list')
    assert response.content_type == 'application/json'
    data = response.get_json()
    assert 'success' in data or 'data' in data

def test_api_save_results(auth_user, test_sample):
    """Test saving analysis results via API."""
    response = auth_user.post('/api/save_results', json={
        'sample_id': test_sample.id,
        'analysis_code': 'Mad',
        'raw_data': {'p1': {'m1': 10.0, 'm2': 1.0, 'm3': 10.97}}
    })
    assert response.status_code == 200
    data = response.get_json()
    assert data.get('success') is True

def test_api_error_handling(auth_user):
    """Test that API returns proper error responses."""
    response = auth_user.post('/api/save_results', json={})
    data = response.get_json()
    assert data.get('success') is False or response.status_code >= 400
```

### 5.5 Testing Calculations

```python
import pytest

def test_calorific_value_conversion():
    """Test CV conversion between cal/g and MJ/kg."""
    from app.utils.server_calculations import cv_cal_to_mj, cv_mj_to_cal

    assert cv_cal_to_mj(6000) == pytest.approx(25.12, abs=0.01)
    assert cv_mj_to_cal(25.12) == pytest.approx(6000, abs=1)

def test_moisture_parallel_difference():
    """Test that parallel difference is within repeatability limit."""
    from app.utils.analysis_rules import check_repeatability

    result = check_repeatability('Mad', 3.0, 3.1)
    assert result['within_limit'] is True

def test_float_tolerance():
    """Test floating point comparison with tolerance."""
    from app.constants import FLOAT_TOLERANCE

    a = 0.1 + 0.2
    b = 0.3
    assert abs(a - b) < FLOAT_TOLERANCE
```

### 5.6 Mocking Database

```python
from unittest.mock import patch, MagicMock

def test_with_mocked_query(app):
    """Test route behavior when database query fails."""
    with app.test_client() as client:
        with app.app_context():
            with patch('app.models.Sample.query') as mock_query:
                mock_query.filter_by.return_value.first.return_value = None
                # Test behavior when sample is not found

def test_with_mocked_db_session(app, auth):
    """Test transaction rollback on database error."""
    with app.test_client() as client:
        auth_actions = type(auth)(client)
        auth_actions.login()
        with patch('app.db.session.commit', side_effect=Exception('DB Error')):
            response = client.post('/api/save_results', json={
                'sample_id': 1,
                'analysis_code': 'Mad',
                'raw_data': {}
            })
            # Should handle the error gracefully
            assert response.status_code in (200, 400, 500)
```

---

## 6. Fixtures Reference

All fixtures are defined in `tests/conftest.py`.

### 6.1 Core Fixtures

| Fixture           | Scope     | Description                                          |
|-------------------|-----------|------------------------------------------------------|
| `app`             | session   | Flask application with `TestConfig`, in-memory SQLite, creates 3 test users (admin, chemist, senior) with password `TestPass123` |
| `client`          | function  | Flask test client for making HTTP requests           |
| `db`              | function  | SQLAlchemy database session within app context       |

### 6.2 Authentication Fixtures

| Fixture           | Scope     | Description                                          |
|-------------------|-----------|------------------------------------------------------|
| `auth_user`       | function  | Pre-authenticated test client logged in as `chemist` (role: chemist) |
| `auth_admin`      | function  | Pre-authenticated test client logged in as `admin` (role: admin) |
| `auth`            | function  | `AuthActions` helper with `.login()` and `.logout()` methods |
| `auth_client`     | function  | `AuthClient` helper with `.login()`, `.login_as_admin()`, `.logout()` (follows redirects) |

### 6.3 Data Fixtures

| Fixture           | Scope     | Description                                          |
|-------------------|-----------|------------------------------------------------------|
| `test_user`       | function  | Returns the `chemist` User object from the database  |
| `test_sample`     | function  | Creates a single test Sample with unique code `TEST-{uuid}`, cleans up after test |
| `init_database`   | function  | Creates 3 test samples with codes `INIT-{uuid}`, cleans up after test |
| `sample_factory`  | function  | `SampleFactory` instance with `.create(**kwargs)` for custom samples, auto-cleanup |

### 6.4 Test Configuration

The `TestConfig` class (defined in `conftest.py`) sets:

| Setting                       | Value                   |
|-------------------------------|-------------------------|
| `TESTING`                     | `True`                  |
| `WTF_CSRF_ENABLED`           | `False`                 |
| `SQLALCHEMY_DATABASE_URI`    | `sqlite:///:memory:`    |
| `SECRET_KEY`                 | `test-secret-key`       |
| `SQLALCHEMY_ENGINE_OPTIONS`  | `{}` (no pool for SQLite) |
| `RATELIMIT_ENABLED`         | `False`                 |
| `RATELIMIT_DEFAULT`         | `10000 per minute`      |
| `MAIL_SUPPRESS_SEND`        | `True`                  |

---

## 7. Coverage Targets

### 7.1 Current Coverage (as of 2026-02-15)

**Overall: 39.3%** (5,749 / 14,616 lines)

| Package                     | Coverage | Lines Covered / Total |
|-----------------------------|----------|-----------------------|
| `app/` (root)              | 71.1%    | 678 / 953             |
| `app/config/`              | 69.2%    | 63 / 91               |
| `app/models/`              | 83.0%    | 901 / 1,085           |
| `app/schemas/`             | 93.8%    | 135 / 144             |
| `app/utils/`               | 71.3%    | 1,746 / 2,449         |
| `app/services/`            | 31.6%    | 111 / 351             |
| `app/repositories/`        | 51.0%    | 78 / 153              |
| `app/routes/api/`          | 26.7%    | 385 / 1,440           |
| `app/routes/main/`         | 19.0%    | 124 / 652             |
| `app/routes/analysis/`     | 16.3%    | 132 / 812             |
| `app/routes/quality/`      | 27.8%    | 122 / 439             |
| `app/routes/reports/`      | 13.2%    | 135 / 1,021           |
| `app/routes/equipment/`    | 21.3%    | 153 / 719             |
| `app/routes/chemicals/`    | 18.0%    | 103 / 571             |
| `app/routes/admin/`        | 19.7%    | 92 / 466              |
| `app/routes/settings/`     | 17.7%    | 56 / 317              |
| `app/routes/spare_parts/`  | 21.4%    | 90 / 420              |
| `app/routes/imports/`      | 23.7%    | 63 / 266              |
| `app/routes/chat/`         | 66.3%    | 122 / 184             |
| `app/routes/license/`      | 55.8%    | 24 / 43               |
| `app/routes/yield_calc/`   | 26.4%    | 42 / 159              |
| `app/labs/`                 | 68.4%    | 26 / 38               |
| `app/labs/coal/`           | 76.5%    | 13 / 17               |
| `app/labs/petrography/`    | 47.1%    | 48 / 102              |
| `app/labs/water_lab/`      | 50.0%    | 23 / 46               |
| `app/labs/water_lab/chemistry/` | 14.7% | 157 / 1,065         |
| `app/labs/water_lab/microbiology/` | 20.7% | 127 / 613        |

### 7.2 Modules at 100% Coverage

These modules have full test coverage:

- `utils/westgard.py` - Westgard QC rules
- `utils/shifts.py` - Shift management
- `utils/security.py` - Security utilities
- `utils/exports.py` - Data export functions
- `utils/datetime.py` - Date/time helpers
- `utils/database.py` - Database utilities
- `utils/converters.py` - Unit converters
- `utils/analysis_aliases.py` - Analysis code aliases

### 7.3 Coverage Targets

| Tier               | Target   | Current Status |
|--------------------|----------|----------------|
| **Utils/Core**     | 80%+     | 71.3% (on track) |
| **Models**         | 80%+     | 83.0% (met) |
| **Schemas**        | 90%+     | 93.8% (met) |
| **Routes**         | 50%+     | 13-27% (needs improvement) |
| **Labs**           | 50%+     | 14-76% (mixed) |
| **Overall**        | 80%+     | 39.3% (CI target: 80%) |

### 7.4 Priority Areas for Coverage Improvement

The following modules have the lowest coverage and handle critical functionality:

1. `routes/reports/routes.py` - 8.7% (report generation)
2. `routes/api/analysis_api.py` - 9.9% (analysis data API)
3. `routes/equipment/api.py` - 10.3% (equipment API)
4. `routes/main/index.py` - 10.7% (main dashboard)
5. `routes/analysis/kpi.py` - 11.7% (KPI calculations)
6. `routes/analysis/qc.py` - 12.0% (quality control)
7. `labs/water_lab/chemistry/routes.py` - 14.7% (water chemistry lab)
8. `routes/main/samples.py` - 14.2% (sample management)

---

## 8. CI/CD Integration

### 8.1 GitHub Actions Pipeline

The project uses GitHub Actions (`.github/workflows/ci.yml`) with a four-stage pipeline:

```
lint --> test --> security --> build --> deploy
```

#### Stage 1: Code Quality Check (`lint`)

- Runs on `ubuntu-latest`
- Uses `ruff` for linting
- Checks code formatting (dry run)

#### Stage 2: Test Suite (`test`)

- Depends on `lint` passing
- Runs on Python 3.9, 3.10, 3.11, and 3.12 (matrix strategy)
- Uses PostgreSQL 15 service container for database tests
- Caches pip dependencies for faster builds
- Runs `pytest --cov=app --cov-report=xml --cov-report=term-missing --cov-fail-under=80`
- Uploads coverage to Codecov (Python 3.11 only)

#### Stage 3: Security Scan (`security`)

- Runs `bandit` for static security analysis
- Runs `pip-audit` for dependency vulnerability scanning
- Uploads security reports as artifacts

#### Stage 4: Build & Validate (`build`)

- Depends on both `test` and `security` passing
- Builds Docker image
- Validates the image by importing the app module

#### Stage 5: Deploy (`deploy`)

- Only runs on `main` branch push events
- Placeholder for production deployment commands

### 8.2 Trigger Events

| Event         | Branches          |
|---------------|-------------------|
| `push`        | `main`, `develop` |
| `pull_request`| `main`, `develop` |

### 8.3 Running CI Locally

To simulate the CI pipeline locally:

```bash
# Install dev dependencies
pip install -r requirements-dev.txt

# Lint check
ruff check app

# Run tests with CI-equivalent settings
pytest --cov=app --cov-report=xml --cov-report=term-missing --cov-fail-under=80

# Security scan
bandit -r app -ll
pip-audit
```

---

## 9. Best Practices

### 9.1 Test Design

1. **One assertion per concept.** Each test should verify one specific behavior. Multiple related assertions in one test are fine, but avoid testing unrelated behaviors.

2. **Use descriptive test names.** Test names should describe what is being tested and what the expected outcome is:
   ```python
   # Good
   def test_moisture_calculation_returns_zero_when_no_weight_loss():

   # Avoid
   def test_moisture_1():
   ```

3. **Use `pytest.approx` for floating-point comparisons.** The LIMS system performs many scientific calculations:
   ```python
   assert result == pytest.approx(3.14, abs=0.01)
   ```

4. **Test edge cases.** Include tests for None inputs, empty strings, zero values, negative numbers, and boundary conditions.

5. **Test error paths.** Verify that functions handle invalid inputs gracefully:
   ```python
   def test_calculation_with_none_input():
       result = calc_moisture_mad(None)
       assert result is None  # or raises ValueError
   ```

### 9.2 Fixture Usage

1. **Use the narrowest scope possible.** Prefer function-scoped fixtures (default) over session-scoped ones to avoid test interdependence.

2. **Use `sample_factory` for multiple samples** instead of creating them manually:
   ```python
   def test_bulk_operations(sample_factory):
       samples = [sample_factory.create() for _ in range(5)]
       # Test bulk operations
   ```

3. **Use `auth_user` or `auth_admin`** for tests that need authentication rather than manually logging in.

4. **Clean up test data.** Fixtures with `yield` handle cleanup automatically. If you create data outside fixtures, ensure it is cleaned up.

### 9.3 Database Testing

1. **Use in-memory SQLite for speed.** The test configuration uses `sqlite:///:memory:` which is much faster than a real PostgreSQL instance.

2. **Be aware of SQLite limitations.** Some PostgreSQL-specific features (JSON operators, array types, `FOR UPDATE`) may not work in SQLite tests. Use `pytest.mark.skipif` for those:
   ```python
   @pytest.mark.skipif(
       'sqlite' in str(db.engine.url),
       reason="PostgreSQL-specific feature"
   )
   def test_json_query(db):
       pass
   ```

3. **Test transaction rollback behavior.** Ensure that database errors trigger proper rollback:
   ```python
   def test_rollback_on_error(db):
       try:
           # Intentionally cause an error
           db.session.execute(text("INVALID SQL"))
           db.session.commit()
       except Exception:
           db.session.rollback()
       # Session should still be usable
       assert db.session.is_active
   ```

### 9.4 Security Testing

1. **Always test authentication requirements.** Every protected endpoint should be tested without authentication:
   ```python
   def test_endpoint_requires_login(client):
       response = client.get('/protected-route')
       assert response.status_code in (302, 401)
   ```

2. **Test role-based access.** Verify that role restrictions are enforced:
   ```python
   def test_admin_route_forbidden_for_chemist(auth_user):
       response = auth_user.get('/admin/users')
       assert response.status_code in (302, 403)
   ```

3. **Test input sanitization.** Include SQL injection and XSS payloads in tests.

### 9.5 Code Organization

1. **Group related tests in classes:**
   ```python
   class TestMoistureCalculation:
       def test_normal_case(self):
           pass
       def test_edge_case_zero(self):
           pass
       def test_invalid_input(self):
           pass
   ```

2. **Use markers for categorization:**
   ```python
   @pytest.mark.unit
   def test_utility_function():
       pass

   @pytest.mark.integration
   @pytest.mark.database
   def test_database_workflow(db):
       pass

   @pytest.mark.security
   def test_xss_prevention(auth_user):
       pass
   ```

3. **Keep tests independent.** Tests should not depend on the execution order or state from other tests.

### 9.6 Performance

1. **Use session-scoped `app` fixture.** The application and test users are created once per test session, not per test.

2. **Use `pytest -x` during development** to stop on the first failure and save time.

3. **Run specific test files** during development rather than the entire suite:
   ```bash
   pytest tests/unit/test_validators.py -v
   ```

4. **Use `pytest -k` for keyword filtering** to run a subset of tests:
   ```bash
   pytest -k "moisture or calorific"
   ```

### 9.7 Dependencies

Install all test dependencies via:

```bash
pip install -r requirements-dev.txt
```

Key testing packages:

| Package           | Version  | Purpose                          |
|-------------------|----------|----------------------------------|
| `pytest`          | 7.4.3    | Test framework                   |
| `pytest-flask`    | 1.3.0    | Flask test integration           |
| `pytest-cov`      | 4.1.0    | Coverage reporting               |
| `pytest-mock`     | 3.12.0   | Mocking support                  |
| `coverage[toml]`  | 7.3.2    | Coverage engine                  |
| `factory-boy`     | 3.3.0    | Test data factories              |
| `Faker`           | 20.1.0   | Fake data generation             |
| `locust`          | 2.17.0   | Load testing                     |
| `bandit`          | 1.7.5    | Security scanning                |
| `requests-mock`   | 1.11.0   | HTTP request mocking             |

---

**End of Testing Guide**
