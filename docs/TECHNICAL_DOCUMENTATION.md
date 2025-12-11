# ТЕХНИКИЙН БАРИМТ БИЧИГ
# Coal LIMS System
# Огноо: 2025-12-04

---

## 1. PRECISION & REPEATABILITY

### 1.1 Тохиргооны файлууд
- `app/config/precision.py` - Precision limits
- `app/config/repeatability.py` - Repeatability (T) limits

### 1.2 Удирдах скриптүүд
```bash
python scripts/manage_precision.py list
python scripts/manage_repeatability.py list
```

### 1.3 API
- `GET /api/precision_config` - Precision тохиргоо авах
- `GET /api/repeatability_config` - Repeatability тохиргоо авах

---

## 2. СЕРВЕРИЙН ТООЦОО

### 2.1 Файл
`app/utils/server_calculations.py`

### 2.2 Тооцооны функцууд
- `calculate_mt()` - Нийт чийг
- `calculate_mad()` - Дотоод чийг
- `calculate_aad()` - Үнс
- `calculate_vad()` - Дэгдэмхий
- `calculate_cv()` - Илчлэг
- `calculate_ts()` - Хүхэр

### 2.3 Аюулгүй байдал
- SQL injection хамгаалалт
- XSS хамгаалалт
- CSRF token шалгалт
- Input validation

---

## 3. ШИНЖИЛГЭЭНИЙ КОД

| Код | Нэр | Нэгж |
|-----|-----|------|
| MT | Нийт чийг | % |
| Mad | Дотоод чийг | % |
| Aad | Үнс | % |
| Vad | Дэгдэмхий | % |
| CV | Илчлэг | cal/g |
| TS | Хүхэр | % |
| CSN | Хөөлтийн зэрэг | - |
| Gi | Барьцалдах чадвар | - |
| TRD | Харьцангуй нягт | g/cm³ |

---

## 4. ТЕСТИЙН БҮТЭЦ

### 4.1 Тест файлууд
- `tests/unit/` - Unit tests
- `tests/integration/` - Integration tests
- `tests/security/` - Security tests

### 4.2 Ажиллуулах
```bash
pytest tests/ -v
pytest tests/security/ -v
```

---

## 5. АЮУЛГҮЙ БАЙДАЛ

### 5.1 Шалгалтууд
- ✅ CSRF protection
- ✅ SQL injection prevention
- ✅ XSS prevention
- ✅ Rate limiting (login)
- ✅ Password hashing (bcrypt)

### 5.2 Role-based access
- prep, chemist, manager, senior, admin

---

**Сүүлд шинэчилсэн:** 2025-12-04
