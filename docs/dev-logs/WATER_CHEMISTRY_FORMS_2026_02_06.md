# Усны химийн шинжилгээний form-ууд - 2026-02-06

## Хураангуй
Усны химийн лабораторийн шинжилгээний ажлын хуудсуудыг шинэчилж, conversion factor тооцоо нэмсэн.

---

## Шинээр үүсгэсэн form-ууд

### 1. CL_W (Хлорид ион) - `cl_w_form.html`
**Стандарт:** MNS 4424:2005

**Бүтэц:**
| Засварын коэффициент |||| N | V, мл | V0 | Сорьц титрлэлт ||| Шинг. | Cl⁻ мг/л |
|-----|-----|-----|--------|-----|-------|-----|-----|-----|-----|-------|----------|
| Vt1 | Vt2 | Vtd | K | | | | V1 | V2 | Vd | | |

**Томьёо:**
```
Cl⁻ (мг/л) = (Vd - V0) × K × N × 35.453 × 1000 / V × Шингэрүүлэлт
```

---

### 2. NH4 (Аммонийн ион) - `nh4_form.html`
**Стандарт:** MNS 1097:2023

**Conversion factor:** × 0.777 (14.007 / 18.038)
- Багажны уншилт: NH4+ ион хэлбэрээр
- Эцсийн үр дүн: NH4-N азот хэлбэрээр (багасна)

**Томьёо:**
```
NH4-N (мг/л) = Дундаж × Шингэрүүлэлт × 0.777
```

---

### 3. NO2 (Нитрит ион) - `no2_form.html`
**Стандарт:** MNS 4431:2005

**Conversion factor:** × 3.286 (46.005 / 14.007)
- Багажны уншилт: NO2-N азот хэлбэрээр
- Эцсийн үр дүн: NO2⁻ ион хэлбэрээр (ихэснэ)

**Томьёо:**
```
NO2⁻ (мг/л) = Дундаж × Шингэрүүлэлт × 3.286
```

---

### 4. PO4 (Фосфат ион) - `po4_form.html`
**Conversion factor:** × 3.06 (94.97 / 30.97)
- Багажны уншилт: PO4-P фосфор хэлбэрээр
- Эцсийн үр дүн: PO4³⁻ ион хэлбэрээр (ихэснэ)

**Томьёо:**
```
PO4³⁻ (мг/л) = Дундаж × Шингэрүүлэлт × 3.06
```

---

### 5. TDS (Хуурай үлдэгдэл) - `tds_form.html`
**Арга:** Жингийн арга (Параллель A/B)

**Бүтэц:**
| V_a мл | m1_a г | m2_a г | A мг/л | V_b мл | m1_b г | m2_b г | B мг/л | Үр дүн | A-B зөрүү |

**Томьёо:**
```
A/B үр дүн (мг/л) = (m2 - m1) × 10⁶ / V
Эцсийн үр дүн = (A + B) / 2
```

---

### 6. COLOR (Өнгө) - `color_form.html`
**Стандарт:** MNS 1097:2023

**Бүтэц:**
| Сорьцын V | Шингэр. | Abs 1 | Abs 2 | Үр дүн 1 | Үр дүн 2 | Дундаж | Үр дүн | Зөрүү |

**Томьёо:**
```
Үр дүн = Дундаж × Шингэрүүлэлт
```

---

## Бусад засварууд

### eligible_samples API
- `lab_type.in_(['water', 'water & micro'])` болгосон
- `microbiology` хасагдсан (усны хими биш)

### aggrid_macros.html
- `sample.sample_code` эхлээд шалгах болгосон (өмнө `sample.code`)
- Sample model-д `sample_code` attribute байгаа

### constants.py
- CL_W categories: `['wastewater']` → `['drinking', 'wastewater']`

### routes.py form_templates
```python
'NH4': 'labs/water/chemistry/analysis_forms/nh4_form.html',
'NO2': 'labs/water/chemistry/analysis_forms/no2_form.html',
'PO4': 'labs/water/chemistry/analysis_forms/po4_form.html',
'TDS': 'labs/water/chemistry/analysis_forms/tds_form.html',
'COLOR': 'labs/water/chemistry/analysis_forms/color_form.html',
'CL_W': 'labs/water/chemistry/analysis_forms/cl_w_form.html',
```

---

## Conversion Factor Хураангуй

| Шинжилгээ | Итгэлцүүр | Шилжүүлэг | Өөрчлөлт |
|-----------|-----------|-----------|----------|
| NH4 | 0.777 | NH4+ → NH4-N | Багасна |
| NO2 | 3.286 | NO2-N → NO2⁻ | Ихэснэ |
| PO4 | 3.06 | PO4-P → PO4³⁻ | Ихэснэ |

---

## Git Commit
```
78f5812 feat: усны химийн шинжилгээний form-ууд + conversion factor тооцоо
```

## Файлууд (20 файл, +1110/-121 мөр)
- 6 шинэ form үүсгэсэн
- 14 файл засагдсан
