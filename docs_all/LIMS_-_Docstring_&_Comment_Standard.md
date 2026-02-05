# LIMS - Docstring & Comment Standard

## 1. Файлын толгой (Module Docstring)

Бүх `.py` файл дараах форматтай байна:

```python
# app/module_name.py
# -*- coding: utf-8 -*-
"""
Модулийн нэр - Товч тайлбар

Дэлгэрэнгүй тайлбар:
  - Юу хийдэг вэ
  - Ямар endpoints/functions агуулдаг вэ
  - Ямар бусад модультай холбогддог вэ

Жишээ:
  >>> from app.module_name import function
  >>> function()

Author: Таны нэр
Created: 2025-01-01
Modified: 2025-12-13
"""
```

---

## 2. Функцийн Docstring

Google стиль ашиглана:

```python
def calculate_moisture(weight_before: float, weight_after: float) -> float:
    """
    Чийгийн хувийг тооцоолох.

    Дээжийн хатаахын өмнөх болон дараах жингээс
    чийгийн хувийг тооцоолно.

    Args:
        weight_before: Хатаахын өмнөх жин (грамм)
        weight_after: Хатаасны дараах жин (грамм)

    Returns:
        Чийгийн хувь (0-100 хооронд)

    Raises:
        ValueError: Жин сөрөг тоо байвал
        ZeroDivisionError: weight_before = 0 байвал

    Example:
        >>> calculate_moisture(10.5, 9.8)
        6.67

    Note:
        ISO 17025 стандартын дагуу тооцоолно.
    """
    pass
```

---

## 3. Class Docstring

```python
class Sample(db.Model):
    """
    Дээжийн модел.

    Лабораторид ирсэн дээжийн бүх мэдээллийг хадгална.
    ISO 17025 стандартын дагуу бүртгэл хөтөлнө.

    Attributes:
        id (int): Primary key
        sample_code (str): Дээжийн код (өвөрмөц)
        client_name (str): Захиалагчийн нэр
        sample_type (str): Дээжийн төрөл
        status (str): Төлөв ('new', 'in_progress', 'completed')

    Relationships:
        - user: Бүртгэсэн хэрэглэгч (User)
        - analysis_results: Шинжилгээний үр дүнгүүд (AnalysisResult)

    Example:
        >>> sample = Sample(sample_code='S-2025-001', client_name='ЭРДЭНЭС')
        >>> db.session.add(sample)
    """
    pass
```

---

## 4. Route/Endpoint Docstring

```python
@bp.route('/samples', methods=['GET'])
@login_required
def list_samples():
    """
    Дээжийн жагсаалт.

    GET /samples

    Query Parameters:
        page (int): Хуудасны дугаар (default: 1)
        per_page (int): Хуудас бүрт (default: 20)
        status (str): Төлөвөөр шүүх (optional)

    Returns:
        JSON: {
            'data': [...],
            'total': 100,
            'page': 1
        }

    Permissions:
        - chemist, senior, admin

    Example:
        GET /samples?page=1&status=new
    """
    pass
```

---

## 5. Inline Comments

### Сайн жишээ:
```python
# Чийгийн хувийг тооцоолох (ISO 17025 formula)
moisture = (weight_before - weight_after) / weight_before * 100

# WESTGARD дүрмээр шалгах (1-2s, 1-3s, 2-2s, R-4s)
qc_status = check_westgard_rules(values, mean, sd)
```

### Муу жишээ (ХЭРЭГЛЭХГҮЙ):
```python
# x = 5  # энэ утгыг хадгална (тодорхойгүй)
moisture = x  # moisture тооцоолсон (илүүдэл)
```

---

## 6. Section Comments

Том функц/файлд хэсэг тусгаарлах:

```python
# ============================================================================
# ШИНЖИЛГЭЭНИЙ ҮР ДҮНГИЙН VALIDATION
# ============================================================================

def validate_moisture(value):
    pass

def validate_ash(value):
    pass

# ============================================================================
# ТООЦООЛОЛ
# ============================================================================

def calculate_dry_basis(value, moisture):
    pass
```

---

## 7. TODO Comments

```python
# TODO: Энэ функцыг refactor хийх (2025-01 хүртэл)
# FIXME: Edge case - weight = 0 үед алдаа гардаг
# NOTE: ISO 17025:2017 шинэчлэлтийн дагуу өөрчлөгдсөн
# HACK: Түр шийдэл - database migration дараа засна
```

---

## 8. Type Hints

Бүх функцэд type hints ашиглах:

```python
from typing import Optional, List, Dict, Tuple

def get_samples(
    status: Optional[str] = None,
    limit: int = 100
) -> List[Dict[str, Any]]:
    """Дээжүүдийг авах."""
    pass
```

---

## 9. Шалгах команд

```bash
# Docstring шалгах
pydocstyle app --convention=google

# Type hints шалгах
mypy app --ignore-missing-imports
```

---

## 10. Файл бүрийн бүтэц

```python
# app/example.py
# -*- coding: utf-8 -*-
"""
Модулийн нэр - Товч тайлбар

Дэлгэрэнгүй...
"""

# 1. Standard Library Imports
import os
from datetime import datetime

# 2. Third-Party Imports
from flask import Blueprint, request
from sqlalchemy import or_

# 3. Local Application Imports
from app import db
from app.models import Sample

# 4. Constants
MAX_RESULTS = 100
DEFAULT_STATUS = 'new'

# 5. Module-level code
bp = Blueprint('example', __name__)

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def helper_function():
    """Helper функцийн docstring."""
    pass

# ============================================================================
# ROUTES / MAIN FUNCTIONS
# ============================================================================

@bp.route('/')
def index():
    """Route docstring."""
    pass
```
