# Хуучин компьютер дээр хийх ажлууд

## 1. Git pull хийх
```bash
cd D:/coal_lims_project
git pull origin main
```

---

## 2. PostgreSQL сервер асаах
```bash
net start postgresql-x64-18
```

---

## 3. Код засварууд (40 асуудал)

### A. Хэрэглэгдээгүй импортууд устгах (12)

#### app/routes/main/samples.py
```python
# ӨМНӨ:
from flask import render_template, flash, redirect, url_for, request, jsonify
from datetime import datetime

# ДАРАА:
from flask import render_template, flash, redirect, url_for, request
# datetime устгах (хэрэглэгдээгүй)
```

#### app/routes/quality/capa.py
```python
# ӨМНӨ:
from app.utils.quality_helpers import can_edit_quality

# ДАРАА:
# Энэ мөрийг устгах (хэрэглэгдээгүй)
```

#### app/routes/quality/control_charts.py
```python
# ӨМНӨ:
from app import db

# ДАРАА:
# Энэ мөрийг устгах (хэрэглэгдээгүй)
```

#### app/schemas/sample_schema.py
```python
# ӨМНӨ:
from datetime import datetime

# ДАРАА:
# datetime устгах (хэрэглэгдээгүй)
```

#### app/utils/decorators.py
```python
# ӨМНӨ:
from typing import Callable, List

# ДАРАА:
from typing import Callable
```

#### app/utils/exports.py
```python
# ӨМНӨ:
from datetime import datetime
from typing import List, Dict, Any, Optional

# ДАРАА:
from typing import List, Dict, Any
```

#### app/utils/notifications.py
```python
# Мөр 11:
# ӨМНӨ:
from flask import current_app, url_for

# ДАРАА:
from flask import url_for

# Мөр 299 орчим - функц дотор datetime import байвал устгах
```

#### app/utils/quality_helpers.py
```python
# ӨМНӨ:
from datetime import datetime, date, timedelta

# ДАРАА:
from datetime import datetime, timedelta
```

#### app/utils/server_calculations.py
```python
# ӨМНӨ:
from math import isnan, isinf

# ДАРАА:
from math import isinf
```

#### app/utils/westgard.py
```python
# ӨМНӨ:
from typing import List, Dict, Any, Optional, Tuple

# ДАРАА:
from typing import List, Dict, Any, Tuple
```

---

### B. Хэрэглэгдээгүй хувьсагчид засах (7)

#### app/routes/main/index.py:484
```python
# ӨМНӨ:
file_date_str = some_value  # хэрэглэгдээгүй

# ДАРАА:
# Хэрэв хэрэггүй бол устгах
# Хэрэв debug-д хэрэгтэй бол _ болгох:
_ = some_value
```

#### app/routes/main/index.py:602
```python
# ӨМНӨ:
found_suffix = some_value  # хэрэглэгдээгүй

# ДАРАА:
# Устгах эсвэл _ болгох
```

#### app/utils/conversions.py:53
```python
# ӨМНӨ:
H_ad = calculated_value  # хэрэглэгдээгүй

# ДАРАА:
# Хэрэв тооцоололд хэрэггүй бол устгах
# Хэрэв debug-д хэрэгтэй бол:
_ = calculated_value  # H_ad - debug
```

#### app/utils/database.py:37,106
```python
# ӨМНӨ:
except Exception as e:
    db.session.rollback()

# ДАРАА (2 газар):
except Exception:
    db.session.rollback()
# эсвэл logging хийх бол:
except Exception as e:
    logger.error(f"Database error: {e}")
    db.session.rollback()
```

#### app/utils/exports.py:48
```python
# ӨМНӨ:
df = some_dataframe  # хэрэглэгдээгүй

# ДАРАА:
# Устгах эсвэл ашиглах
```

---

### C. Dead code устгах (2)

#### app/api_docs.py:31
```python
# ӨМНӨ:
tag = some_value  # unused

# ДАРАА:
# Энэ мөрийг устгах
```

#### app/utils/exports.py:98
```python
# ӨМНӨ:
include_results = True  # unused parameter

# ДАРАА:
# Хэрэв функцын параметр бол:
# 1. Ашиглах
# 2. Эсвэл функцын signature-аас хасах
```

---

## 4. Тест ажиллуулах

```bash
# Virtual environment
D:\coal_lims_project\venv\Scripts\activate

# Бүх тест
python -m pytest tests/ -q --cov=app --cov-report=term-missing --cov-report=html

# Coverage report
start htmlcov/index.html
```

---

## 5. Coverage 80% хүргэх

Одоогийн coverage: 42% (PostgreSQL-гүй)
Зорилт: 80%

Routes coverage нэмэхэд анхаарах:
- `app/routes/main/index.py` - 12%
- `app/routes/report_routes.py` - 10%
- `app/routes/settings_routes.py` - 18%

---

## 6. Бэлэн байгаа зүйлс (шалгагдсан)

| Бүрэлдэхүүн | Төлөв | Файл |
|------------|-------|------|
| API Docs | ✅ | app/api_docs.py |
| Migrations | ✅ | migrations/versions/*.py |
| Security config | ✅ | config.py |
| Prometheus monitoring | ✅ | app/monitoring.py |
| .env файл | ✅ | .env, .env.example |
| Backup script | ✅ | scripts/backup_database.py |
| Migration script | ✅ | scripts/migrate_sqlite_to_postgres.py |
| Production server | ✅ | run_production.py, start_server.bat |
| pip-audit | ✅ | Эмзэг байдал олдсонгүй |

---

## 7. Production server тест

```bash
# Waitress server ажиллуулах
python run_production.py

# эсвэл
start_server.bat

# Браузер дээр шалгах
# http://localhost:8080
```

---

## 8. Backup тест

```bash
# Backup хийх
python scripts/backup_database.py

# Backup файл шалгах
dir backups/
```

---

## 9. Production checklist

- [ ] PostgreSQL ажиллаж байна
- [ ] Код засварууд хийгдсэн (40 асуудал)
- [ ] Full тест suite passed
- [ ] Coverage >= 80%
- [ ] flake8 алдаагүй
- [ ] vulture алдаагүй
- [ ] Production server (Waitress) ажиллаж байна
- [ ] Backup script ажиллаж байна
- [ ] Prometheus /metrics endpoint ажиллаж байна

---

## Хурдан засах команд

```bash
# flake8 шалгах
python -m flake8 app --select=F401,F841 --count

# vulture шалгах
vulture app --min-confidence 80

# Бүх тест
python -m pytest tests/ -v --tb=short
```

---

## Засварын дараа

```bash
# Өөрчлөлтүүдийг commit хийх
git add -A
git commit -m "refactor: Unused imports and variables removed"
git push origin main
```
