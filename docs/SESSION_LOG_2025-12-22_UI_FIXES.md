# Session Log: UI Засварууд ба Rate Limiting
**Огноо:** 2025-12-22

## 1. Шинжилгээний Хуудасны Засварууд

### 1.1 Үйлдэл баганы өргөн (80 → 90px)
**15 файл засагдсан:**
- xy_aggrid.html, Gi_aggrid.html, vad_aggrid.html, csn_aggrid.html
- free_moisture_aggrid.html, phosphorus_aggrid.html, trd_aggrid.html
- fluorine_aggrid.html, solid_aggrid.html, mt_aggrid.html
- cricsr_aggrid.html, mad_aggrid.html, cv_aggrid.html
- chlorine_aggrid.html, ash_form_aggrid.html
- sulfur_aggrid.html (90 хэвээр), mass_aggrid.html (220 хэвээр)

### 1.2 CV шинжилгээний хуудас
**Label өөрчлөлт:**
| Хуучин | Шинэ |
|--------|------|
| Системийн дулаан багтаамж (E) | Бомб дулаан багтаамж (E) |
| Гал хамгаалагчийн засвар (q1) | Гал өдөөх утасны дулаан (q1) |
| Хүчиллэгийн засвар (q2) | Нэмэлт дулаан (q2) |

**Input өөрчлөлт:**
- E, q1: `value` → `placeholder` болгосон
- Хадгалах үед validation нэмсэн (хоосон бол alert)

**Багана өөрчлөлт:**
- m (жин): 3 орон → 4 орон (`numFmt4`)
- dT: 3 орон → хязгааргүй (багажнаас ирсэн шигээ)

### 1.3 Gi шинжилгээний хуудас
**Багана толгой хялбарчилсан:**
| Хуучин | Шинэ |
|--------|------|
| m1 (г) | m1 |
| m2 (>6.3мм) | m2 |
| m3 (<3мм) | m3 |

### 1.4 Client name устгасан (8 файл)
Дээжийн нэрний доор харагдаж байсан нэгжийн нэр устгасан:
- sulfur, solid, cricsr, xy, free_moisture
- phosphorus, chlorine, fluorine

### 1.5 Тохирц баганы нэр стандартчилсан
`(T)` хассан - бүгд `Тохирц` болсон:
- phosphorus, chlorine, sulfur, fluorine
- xy: X тохирц, Y тохирц
- cricsr: CRI тохирц, CSR тохирц

---

## 2. Rate Limiting Шинэчлэл

### 2.1 Асуудал
10+ химич, 1200+ шинжилгээ/өдөр хийхэд хуучин хязгаар хэт бага байсан.

### 2.2 Шийдэл
**`app/__init__.py`:**
```python
# Хуучин
default_limits=["200 per day", "50 per hour"]

# Шинэ
default_limits=["10000 per day", "500 per hour"]
```

**API endpoints (analysis_api.py, samples_api.py, mass_api.py):**
```python
# Хуучин
@limiter.limit("20-30 per minute")

# Шинэ
@limiter.limit("100 per minute")
```

### 2.3 Шинэ хязгаарууд
| Хэсэг | Хуучин | Шинэ |
|-------|--------|------|
| Ерөнхий/өдөр | 200 | 10,000 |
| Ерөнхий/цаг | 50 | 500 |
| API/минут | 20-30 | 100 |
| Login/минут | 5 | 5 (хэвээр) |

---

## 3. Шинэчилсэн Баримтжуулалт
- `docs/SECURITY_DOCUMENTATION.md` - Rate limiting хэсэг шинэчлэгдсэн

---

## 4. Өөрчилсөн Файлууд
### UI Templates (17 файл)
- `app/templates/analysis_forms/*.html`

### Backend (4 файл)
- `app/__init__.py`
- `app/routes/api/analysis_api.py`
- `app/routes/api/samples_api.py`
- `app/routes/api/mass_api.py`

### Documentation (1 файл)
- `docs/SECURITY_DOCUMENTATION.md`

---

## 5. Нэмэлт UI Засварууд (Session 2)

### 5.1 TRD шинжилгээний хуудас
**Багана толгой хялбарчилсан:**
- m (Жин, г) → m
- m1 (Хатаасны дараа) → m1
- m2 (Шатаасны дараа) → m2

### 5.2 Free Moisture хуудас
- Free moisture % (wet) → Free moisture %

### 5.3 Solid шинжилгээний хуудас
- (A) bucket + sample → bucket + sample
- (B) bucket tare → bucket tare
- (C) dry residue → dry residue

### 5.4 Mass хуудас
- Заавар хэсэг устгасан

---

## 6. Quality хуудсууд AG Grid болгосон (4 файл)
- capa_list.html (200px)
- complaints_list.html (200px)
- proficiency_list.html (200px)
- environmental_list.html (200px)

### ISO заалтууд монгол болгосон:
- CAPA: 8.7 заалт: Залруулах ба Урьдчилан Сэргийлэх Арга Хэмжээ
- Complaints: 8.9 заалт: Үйлчлүүлэгчийн гомдлын менежмент
- Proficiency: 7.7.2 заалт: Лабораторийн чадамжийн шалгалт
- Environmental: 6.3.3 заалт: Температур, Чийгийн бүртгэл

---

## 7. Ахлахын хяналт (Ahlah Dashboard) засвар

### 7.1 Асуудал
Шөнийн ээлжийн үед (19:00-07:00) "Химичийн шинжилгээ" хэсэгт "Өнөөдөр шинжилгээ хийгээгүй" гэж харагдаж байсан, гэтэл шинжилгээ хийгдсэн байсан.

### 7.2 Шалтгаан
`get_shift_date()` функц нь зөвхөн огноо буцаадаг (00:00-23:59), харин шөнийн ээлж 2 өдрийг хамардаг (өчигдөр 19:01 - өнөөдөр 07:00).

### 7.3 Шийдэл
**`app/routes/analysis/senior.py`:**
```python
# Хуучин
today = get_shift_date()
today_start = datetime.combine(today, datetime.min.time())
today_end = datetime.combine(today, datetime.max.time())

# Шинэ
shift_info = get_shift_info(now_local())
today_start = shift_info.shift_start
today_end = shift_info.shift_end
```

### 7.4 Preparer role нэмсэн
Дээж бэлтгэгч (preparer) FM, Solid шинжилгээ хийдэг тул chemist stats-д нэмсэн:
```python
# Хуучин
.filter(User.role.in_(["chemist", "senior"]))

# Шинэ
.filter(User.role.in_(["chemist", "senior", "preparer"]))
```
