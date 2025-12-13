# Coal LIMS - Код чанарын шалгалт

**Огноо:** 2025-12-13
**Шалгагч:** Claude Code

---

## 1. mypy - Type Checking

| Статус | Тайлбар |
|--------|---------|
| **122 алдаа** | 18 файлд type annotation алдаа |

**Гол асуудлууд:**
- None handling буруу (Unsupported operand types)
- Optional type зарлаагүй (PEP 484 implicit Optional)
- Index assignment errors

**Их асуудалтай файлууд:**

| Файл | Алдааны тоо |
|------|-------------|
| utils/server_calculations.py | 40+ |
| utils/conversions.py | 6 |
| utils/normalize.py | 6 |
| config/display_precision.py | 4 |

---

## 2. radon - Complexity Analysis

| Статус | Тайлбар |
|--------|---------|
| **A (4.98)** | Дундаж complexity маш сайн |

**Complexity үнэлгээ:**
- A (1-5): Хялбар, засвартай
- B (6-10): Бага зэрэг нарийн
- C (11-20): Нарийн
- F (21+): Маш нарийн

**B rating-тай функцүүд:**

| Функц | Файл | Rating |
|-------|------|--------|
| User.validate_password | models.py:76 | B (8) |
| SampleCalculations._calculate_conversion | models.py:827 | B (8) |
| ChatMessage.to_dict | models.py:1730 | B (8) |
| _safe_int | cli.py:28 | B (8) |
| _safe_float | cli.py:46 | B (8) |

---

## 3. interrogate - Docstring Coverage

| Статус | Тайлбар |
|--------|---------|
| **65.3%** | Docstring coverage (80% хүрэхгүй) |

**Дутуу docstring-тэй файлууд:**

| Файл | Coverage |
|------|----------|
| forms.py | 0% |
| utils/__init__.py | 0% |
| config/__init__.py | 0% |
| config/repeatability.py | 0% |

---

## 4. ruff - Fast Linter

| Статус | Тайлбар |
|--------|---------|
| **141 алдаа** | 37 автоматаар засагдах боломжтой |

**Алдааны төрлүүд:**

| Код | Тоо | Тайлбар |
|-----|-----|---------|
| E701 | 40 | Multiple statements on one line (colon) |
| F401 | 31 | Unused import |
| E402 | 25 | Module import not at top of file |
| E711 | 14 | None comparison |
| E712 | 9 | True/False comparison |
| F841 | 8 | Unused variable |
| E702 | 7 | Multiple statements on one line (semicolon) |

**Автомат засах команд:**
```bash
ruff check app --fix
```

---

## 5. Нийт дүгнэлт

| Хэрэгсэл | Үр дүн | Статус |
|----------|--------|--------|
| mypy | 122 алдаа | Засах хэрэгтэй |
| radon | A (4.98) | Маш сайн |
| interrogate | 65.3% | Docstring нэмэх |
| ruff | 141 алдаа | Засах хэрэгтэй |
| flake8 | 598+ | Style issues |
| bandit | 0 | Аюулгүй |
| vulture | 39 | Dead code |
| pip-audit | Fixed | Шинэчлэгдсэн |

---

## 6. Хэрэгсэл суулгах команд

```bash
pip install mypy radon interrogate ruff
```

## 7. Шалгах командууд

```bash
# Type checking
mypy app --ignore-missing-imports

# Complexity
radon cc app -a -s

# Docstring coverage
interrogate app -v

# Fast linter
ruff check app --statistics

# Auto-fix
ruff check app --fix
```
