# Production-д гаргах ажлын жагсаалт

## Шинэ компьютер дээр хийсэн ажлууд (2025-12-13)

### Тест Coverage
- [x] Unit тестүүд: 1313+ passed
- [x] utils модулиуд 90-100% coverage
  - decorators.py: 100%
  - database.py: 100%
  - security.py: 100%
  - westgard.py: 100%
  - converters.py: 100%
  - analysis_aliases.py: 100%
  - analysis_rules.py: 100%
  - shifts.py: 99%
  - analysis_assignment.py: 97%
  - validators.py: 95%
  - audit.py: 95%
  - server_calculations.py: 93%

### Код засварууд
- [x] pandas import устгасан (app/routes/main/index.py)
- [x] test_decorators_audit_db.py нэмсэн
- [x] test_schemas_comprehensive.py нэмсэн

---

## Хуучин компьютер дээр хийх ажлууд

### 1. Git pull хийх
```bash
cd D:/coal_lims_project
git pull origin main
```

### 2. PostgreSQL сервер асаах
```bash
# PostgreSQL service эхлүүлэх
net start postgresql-x64-18
# эсвэл
pg_ctl -D "C:\Program Files\PostgreSQL\18\data" start
```

### 3. Full тест ажиллуулах
```bash
# Virtual environment идэвхжүүлэх
D:\coal_lims_project\venv\Scripts\activate

# Бүх тест ажиллуулах
python -m pytest tests/ -q --cov=app --cov-report=term-missing --cov-report=html

# Coverage report харах
start htmlcov/index.html
```

### 4. Coverage 80% хүргэх
Хэрэв coverage < 80% бол:
- Integration тестүүдийг нэмэх
- Routes тестүүдийг нэмэх

### 5. Production server ажиллуулах
```bash
# Waitress production server
python run_production.py

# эсвэл
start_server.bat
```

---

## Одоогийн Coverage тайлан (PostgreSQL-гүй)

| Модуль | Coverage |
|--------|----------|
| utils/decorators.py | 100% |
| utils/database.py | 100% |
| utils/security.py | 100% |
| utils/westgard.py | 100% |
| utils/converters.py | 100% |
| utils/analysis_aliases.py | 100% |
| utils/analysis_rules.py | 100% |
| utils/shifts.py | 99% |
| utils/analysis_assignment.py | 97% |
| utils/validators.py | 95% |
| utils/audit.py | 95% |
| utils/server_calculations.py | 93% |
| schemas/analysis_schema.py | 96% |
| schemas/user_schema.py | 94% |
| schemas/sample_schema.py | 91% |
| **TOTAL** | **42%** (PostgreSQL-гүй) |

**Тайлбар:** Routes coverage бага байгаа нь PostgreSQL холболт шаардлагатай тестүүд ажиллаагүйтэй холбоотой.

---

## Production Checklist

- [ ] PostgreSQL сервер ажиллаж байна
- [ ] Full тест suite passed
- [ ] Coverage >= 80%
- [ ] Security тестүүд passed
- [ ] Performance тестүүд passed
- [ ] Backup тохиргоо хийгдсэн
- [ ] Monitoring (Prometheus) идэвхжсэн
- [ ] SSL/HTTPS тохируулсан (production орчинд)
