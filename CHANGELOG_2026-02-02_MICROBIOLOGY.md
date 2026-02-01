# CHANGELOG — 2026-02-02 Микробиологийн лаб сайжруулалт

## Хураангуй

Микробиологийн лабораторийн нэгтгэл хуудас, ажлын хуудас (workspace), дээж бүртгэлийн бүрэн сайжруулалт хийгдсэн. Нүүрсний лабын загвар дээр суурилж дээж сонгох модал, draft менежмент, category-аар шүүлт зэрэг функцуудыг нэгдсэн стандартаар хэрэгжүүлсэн.

---

## 1. Нэгтгэл хуудас (Шинэ)

**Файл:** `app/labs/microbiology/templates/micro_summary.html`
**Route:** `app/labs/microbiology/routes.py` → `/summary`

- 3 tab бүхий нэгтгэл хуудас: **Ус**, **Агаар**, **Арчдас**
- Tab бүрт MNS стандартын дугаар, зөвшөөрөгдөх хэмжээ бүхий олон мөрт толгой (multi-row header)
- Зөвшөөрөгдөх хэмжээнээс хэтэрсэн утгууд **улаан өнгөөр** тодорно
- Усны tab: CFU дундаж = (22°С + 37°С) / 2 автомат тооцоолол
- `/api/load_batch?category=XXX` API-аар өгөгдөл татна
- Navbar болон micro_hub дээр нэгтгэл линк нэмэгдсэн

### Толгой формат (жишээ — Ус):
```
| Д/д | Сорьцын дугаар | Эхэлсэн | Дууссан | Сорьцын нэр | CFU 22°C | CFU 37°C | Дундаж | E.coli | Salmonella |
|     |                |         |         |             | /MNS ISO 6222:1998/              |        |            |
|     |                |         |         |             | Зөвшөөрөгдөх: 1мл-т 100         | 100мл  | 25мл       |
```

---

## 2. Ажлын хуудас (Workspace) засвар

**Файлууд:**
- `app/labs/microbiology/templates/analysis_forms/micro_workspace.html` (Ус)
- `app/labs/microbiology/templates/analysis_forms/micro_air_workspace.html` (Агаар)
- `app/labs/microbiology/templates/analysis_forms/micro_swab_workspace.html` (Арчдас)

### 2.1 Draft буг засвар (CRITICAL)
- **Асуудал:** `draftMgr.clear()` гэж дуудаж байсан — `LIMSDraftManager`-д `clear()` метод байхгүй
- **Шийдэл:** `draftMgr.purge()` болгосон — хадгалсны дараа localStorage-аас draft бүрэн устна
- **Үр дүн:** Хадгалсны дараа grid мөрүүд буцаж гарахгүй болсон

### 2.2 Дээж сонгох модал шинэчлэл (нүүрсний лабын загвар)
- **Захиалагчаар шүүх** dropdown (`filterClient`) нэмсэн
- **Шүүлтүүр цэвэрлэх** товч (`clearFilters`) нэмсэн
- **Тоолуур**: "X / Y дээж" формат — шүүлтэд таарсан / нийт
- **Бүгдийг сонгох**: Зөвхөн харагдаж байгаа (шүүлтэд таарсан) мөрүүдийг сонгоно
- **DOM шүүлт**: Re-render хийхгүй, `tr.style.display` ашиглан шүүнэ — хурдан
- **`data-code`, `data-client`** attribute-ууд мөр бүрт нэмсэн

### 2.3 Category-аар дээж шүүлт
- **Backend:** `api_samples?category=MICRO_WATER` → `analyses_to_perform` JSON талбараас exact match (`"CFU"`) хийж шүүнэ
- **Хадгалсан дээж хасагдана:** `AnalysisResult` дээр тухайн category-д бичлэг байвал жагсаалтаас хасна
- Workspace бүр зөвхөн өөрт хамааралтай дээжийг л харуулна:
  - MICRO_WATER → `"CFU"`, `"ECOLI"`, `"SALM"` агуулсан дээж
  - MICRO_AIR → `"AIR_CFU"`, `"AIR_STAPH"` агуулсан дээж
  - MICRO_SWAB → `"SWAB_CFU"`, `"SWAB_ECOLI"`, `"SWAB_SALM"` агуулсан дээж

### 2.4 Бусад засвар
- **DateCellEditor**: HTML5 `<input type="date">` ашигласан (AG Grid community-д `agDateStringCellEditor` байхгүй)
- **Баганы нэр:** "Сорьцын дугаар" → "Сорьцын нэр / Sample Name"
- **Буцах товч:** `micro_hub` → `analysis_hub` руу зөв чиглүүлсэн

---

## 3. Дээж бүртгэл сайжруулалт

### 3.1 Дотоод хяналт бүлэг салгалт

**Файл:** `app/labs/water/constants.py`

Өмнө нь 1 бүлэг (`dotood_khyanalt`, 9 дээж) байсныг 2 бүлэг болгож салгасан:

| Бүлэг | Нэр | Дээжийн тоо | Автомат шинжилгээ |
|-------|------|------------|-------------------|
| `dotood_air` | Дотоод хяналт (Агаар) | 4 | AIR_CFU, AIR_STAPH |
| `dotood_swab` | Дотоод хяналт (Арчдас) | 5 | SWAB_CFU, SWAB_ECOLI, SWAB_SALM |

**Агаарын дээж:** Ламинар бокс /ариутгалын өмнө/, Шинжилгээний өрөө /ариутгалын өмнө/, Ламинар бокс /ариутгалын дараа/, Шинжилгээний өрөө /ариутгалын дараа/

**Арчдасны дээж:** Ламинар бокс /ариутгалын өмнө/, Ламинар бокс /ариутгалын дараа/, Зейтца-1, Зейтца-2, Зейтца-3

### 3.2 Автомат шинжилгээ сонголт (`auto_analyses`)

**Файл:** `app/labs/water/templates/water_register.html`

Нэгж (unit) сонгоход `auto_analyses` массив байвал тухайн шинжилгээний checkbox-ууд автоматаар чеклэгдэнэ. Жишээ нь "Дотоод хяналт (Агаар)" сонговол AIR_CFU, AIR_STAPH автомат идэвхжинэ.

### 3.3 Шинжилгээний 3 бүлэг

Дээж бүртгэлийн хуудас дээр микробиологийн шинжилгээг 3 бүлэгт хуваасан:
- **Микробиологи (Ус):** CFU, E.coli, Salmonella
- **Микробиологи (Агаар):** Агаарын CFU, Staphylococcus
- **Микробиологи (Арчдас):** Арчдасны CFU, E.coli, Salmonella

### 3.4 Шинэ шинжилгээний кодууд

**Файл:** `app/labs/microbiology/constants.py`

| Код | Нэр | Бүлэг |
|-----|------|-------|
| CFU | CFU (Colony Forming Units) | Ус |
| ECOLI | E. coli | Ус |
| SALM | Salmonella spp. | Ус |
| AIR_CFU | Агаарын CFU | Агаар |
| AIR_STAPH | Staphylococcus (агаар) | Агаар |
| SWAB_CFU | Арчдасны CFU | Арчдас |
| SWAB_ECOLI | E. coli (арчдас) | Арчдас |
| SWAB_SALM | Salmonella (арчдас) | Арчдас |

`CATEGORY_ANALYSIS_CODES` mapping нэмэгдсэн — workspace бүр ямар кодтой дээжийг харуулахыг тодорхойлно.

### 3.5 Redirect засвар
- Амжилттай бүртгэсний дараа **дээжний жагсаалт** (`register_sample`) руу буцна
- Өмнө нь нүүр хуудас (`water_hub`, `micro_hub`) руу redirect хийдэг байсан

---

## 4. Лаб дугаар (Lab ID) систем

**Файл:** `app/labs/water/utils.py`

- Формат: **XX_YY** (XX = өдрийн дэс дугаар, YY = нийт дээжийн дэс дугаар)
- `microbiology` болон `water & micro` төрлийн дээжид автомат үүсгэнэ
- `sample_code` формат: `{lab_id}_{sample_name}_{date}` → жишээ: `01_07_Ламинар бокс_2026-02-01`

---

## 5. Lab type шинэчлэл

- `water & micro` хослол төрөл нэмэгдсэн
- Ус + микро шинжилгээ хоёуланг нь сонговол → `lab_type = "water & micro"`
- Зөвхөн микро → `lab_type = "microbiology"`
- Зөвхөн ус → `lab_type = "water"`
- Бүх query-д `['water', 'microbiology', 'water & micro']` шүүлт

---

## 6. Устгах / Засах функц

- **Устгах:** admin, senior, chemist эрхтэй хэрэглэгч дээж устгах боломжтой
- **Засах:** Дээжийн нэр, огноо, шинжилгээ засварлах боломжтой
- Нүүрсний лабын загвараар хэрэгжүүлсэн

---

## 7. DB өөрчлөлт

- `ck_sample_client_name` CHECK constraint шинэчлэгдсэн:
  - `dotood_khyanalt` хасагдсан
  - `dotood_air`, `dotood_swab` нэмэгдсэн

---

## Өөрчлөгдсөн файлуудын бүрэн жагсаалт

| # | Файл | Төрөл | Тайлбар |
|---|------|-------|---------|
| 1 | `app/labs/microbiology/routes.py` | Засвар | summary route, api_samples category шүүлт, edit/delete |
| 2 | `app/labs/microbiology/constants.py` | Засвар | AIR/SWAB кодууд, CATEGORY_ANALYSIS_CODES |
| 3 | `app/labs/microbiology/templates/micro_summary.html` | Шинэ | Нэгтгэл хуудас |
| 4 | `app/labs/microbiology/templates/micro_hub.html` | Засвар | Нэгтгэл линк |
| 5 | `app/labs/microbiology/templates/analysis_forms/micro_workspace.html` | Засвар | Модал, draft fix, DateCellEditor |
| 6 | `app/labs/microbiology/templates/analysis_forms/micro_air_workspace.html` | Засвар | Модал, draft fix |
| 7 | `app/labs/microbiology/templates/analysis_forms/micro_swab_workspace.html` | Засвар | Модал, draft fix |
| 8 | `app/labs/water/constants.py` | Засвар | dotood_air, dotood_swab (auto_analyses) |
| 9 | `app/labs/water/utils.py` | Засвар | lab_id үүсгэх, water & micro логик |
| 10 | `app/labs/water/routes.py` | Засвар | edit, delete, redirect засвар |
| 11 | `app/labs/water/templates/water_register.html` | Засвар | 3 бүлэг микро шинжилгээ, auto_analyses JS |
| 12 | `app/templates/base.html` | Засвар | Navbar нэгтгэл линк |
| 13 | `app/models.py` | Засвар | ck_sample_client_name constraint |
| 14 | `CHANGELOG.md` | Засвар | Өнөөдрийн бичлэг нэмсэн |
