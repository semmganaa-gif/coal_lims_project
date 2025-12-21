# Session Log: QC Control Charts Засварууд
**Огноо:** 2025-12-22

## Гол Асуудлууд ба Шийдэл

### 1. QC Validation Ажиллахгүй Байсан
**Асуудал:** CM дээжний CV=6980 үр дүн QC шалгалт давж consolidation руу орж байсан (target: 7696 ± 52)

**Шалтгаан:** DB код (`CV`) ≠ Target код (`CV,d`)

**Засвар:** `app/routes/api/analysis_api.py`
```python
DB_TO_STANDARD_CODE = {
    'Aad': 'Ad',
    'Vad': 'Vd',
    'CV': 'CV,d',
    'TS': 'St,d',
    ...
}
standard_code = DB_TO_STANDARD_CODE.get(analysis_code, analysis_code)
```

### 2. Tolerance Check Алгасагдаж Байсан
**Асуудал:** `t_exceeded` шалгалт control_targets check-ийн дараа байсан тул хэзээ ч хүрэхгүй байсан

**Засвар:** `app/utils/analysis_rules.py` - `t_exceeded` шалгалтыг функцийн эхэнд зөөсөн

### 3. MJ Хөрвүүлэлт Буруу Байсан
**Асуудал:** CM дээжинд CV-г MJ руу хөрвүүлж байсан (зөвхөн GBW дээр хөрвүүлэх ёстой)

**Засвар:** `app/routes/api/analysis_api.py`
```python
if is_gbw and analysis_code in ["CV", "Qgr,ad"]:
    # Зөвхөн GBW дээр MJ хөрвүүлэх
```

### 4. График 1 Цэгтэй Үед Харагдахгүй
**Асуудал:** `< 2` шалгалт байсан тул 1 цэгтэй үед график харагдахгүй

**Засвар:** `app/routes/quality/control_charts.py` болон `control_charts.html`
- `if len(data_points) < 2:` → `< 1`

### 5. "Өнөөдөр" Фильтер Ажиллахгүй
**Асуудал:** `toISOString()` UTC огноо буцаадаг, сервер Local time (UTC+8) хадгалдаг

**Засвар:** `app/templates/quality/control_charts.html`
```javascript
// Хуучин (буруу):
const today = now.toISOString().split('T')[0];

// Шинэ (зөв):
const year = now.getFullYear();
const month = String(now.getMonth() + 1).padStart(2, '0');
const day = String(now.getDate()).padStart(2, '0');
const today = `${year}-${month}-${day}`;
```

### 6. Westgard Зөрчил Дэлгэрэнгүй Харуулаагүй
**Асуудал:** Modal дээр зөвхөн дүрмийн нэр харагдаж, тайлбар харагдахгүй байсан

**Засвар:** `loadModalChart()` функцэд detail API-аас зөрчлийн дэлгэрэнгүй мэдээлэл авч харуулах код нэмсэн
```javascript
if (data.violations && data.violations.length > 0) {
  violationsList.innerHTML = data.violations.map(v => {
    const badge = v.severity === 'reject' ? 'bg-danger' : 'bg-warning';
    return `<span class="badge ${badge}">${v.rule}</span> ${v.description}`;
  }).join('');
}
```

## Өөрчилсөн Файлууд
1. `app/routes/api/analysis_api.py` - DB_TO_STANDARD_CODE mapping, MJ хөрвүүлэлт
2. `app/utils/analysis_rules.py` - t_exceeded check байршил
3. `app/routes/quality/control_charts.py` - Data point minimum check
4. `app/templates/quality/control_charts.html` - Timezone fix, Westgard violations display

## Westgard Дүрмүүд (Лавлагаа)
| Дүрэм | Тайлбар | Үр дүн |
|-------|---------|--------|
| 1:2s | 1 утга ±2SD-ээс гадна | Анхааруулга |
| 1:3s | 1 утга ±3SD-ээс гадна | REJECT |
| 2:2s | 2 дараалсан утга нэг талд 2SD-ээс гадна | REJECT |
| R:4s | 2 утгын зөрүү > 4SD | REJECT |
| 4:1s | 4 дараалсан утга нэг талд 1SD-ээс гадна | REJECT |
| 10x | 10 дараалсан утга дунджийн нэг талд | REJECT |

## Тест Үр Дүн
- QC validation ажиллаж байна
- Tolerance check ажиллаж байна
- "Өнөөдөр" фильтер ажиллаж байна
- Westgard зөрчил дэлгэрэнгүй харагдаж байна
