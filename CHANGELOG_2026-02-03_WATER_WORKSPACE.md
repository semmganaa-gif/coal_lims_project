# CHANGELOG — 2026-02-03 Усны химийн workspace шинэчлэл + Нэгдсэн нэгтгэл

## Хураангуй

Усны химийн лабораторийн 4 шинжилгээний ажлын хуудас (workspace)-г микробиологийн лабын загвараар бүрэн шинэчилсэн. Shared layout template үүсгэж, цаг хэмжигч нэмж, усны хими + микробиологи хоёрын нэгдсэн нэгтгэл хуудсыг AG Grid дээр хэрэгжүүлсэн.

---

## 1. Shared Layout Template (Шинэ)

**Файл:** `app/labs/water/templates/analysis_forms/water_ws_layout.html`

Микро workspace-ын бүтцийг дагасан нэгдсэн layout template:

- **Glassmorphism header** — шинжилгээний нэр, код, MNS стандарт, нэгж мэдээлэл
- **Action товчнууд** — Буцах, Стандарт лавлах toggle, Цаг хэмжигч toggle, Дээж сонгох modal, Хадгалах
- **Collapsible стандартын лавлах** (`#waterQuickRef`) — MNS limit, unit, стандартын нэр
- **AG Grid** (`#waterGrid`) — `LIMS_AGGRID` helper ашигласан, editable баганууд
- **Дээж сонгох modal** (`#waterSampleModal`) — микро лабтай адил загвар:
  - Захиалагчаар шүүх dropdown
  - Шүүлтүүр цэвэрлэх товч
  - Checkbox бүхий дээжний хүснэгт
  - "X / Y дээж" тоолуур
  - Бүгдийг сонгох — зөвхөн шүүлтэд таарсан мөрүүдийг сонгоно
- **Toast notification** — амжилттай/алдаа мэдэгдэл
- **LIMSDraftManager** — localStorage-д draft автомат хадгалах/сэргээх
- **Jinja2 block overrides** — form бүр зөвхөн өөрийн тусгай логикийг тодорхойлно:
  - `{% block method_badge %}` — арга зүйн badge
  - `{% block extra_ref %}` — нэмэлт стандарт мэдээлэл
  - `{% block column_defs %}` — AG Grid баганы тодорхойлолт
  - `{% block row_builder %}` — дээж → grid мөр хувиргах функц
  - `{% block save_collector %}` — grid-с хадгалах өгөгдөл цуглуулах функц

---

## 2. Цаг хэмжигч (Timer Panel)

**Файл:** `water_ws_layout.html` — `#waterTimerPanel` section

Микро лабын `micro_timer_panel.html`-тэй адил функционалтай:

- **4 preset цаг:**
  - BOD5 — 5 хоног (432000 секунд)
  - Хатаах — 2 цаг (7200 секунд)
  - Шатаах — 1 цаг (3600 секунд)
  - Титрлэлт — 30 минут (1800 секунд)
- **Custom цаг** оруулах боломжтой (цаг:минут:секунд)
- **Start / Pause / Reset** товчнууд
- **Дуут дохио** (beep) — цаг дуусахад
- Glassmorphism дизайн, gradient progress bar

---

## 3. 4 Form Template — Layout Extend

Өмнөх standalone template-уудыг `water_ws_layout.html`-с extend хийж дахин бичсэн. Form бүр зөвхөн өөрийн тусгай баганы тодорхойлолт, тооцоолол, хадгалах логикийг агуулна.

### 3.1 pH / EC Form

**Файл:** `app/labs/water/templates/analysis_forms/ph_ec_form.html`

- Layout-ын default баганууд хэрэглэнэ: m1, m2, m3, average
- Нэмэлт override шаардлагагүй — хамгийн товч template (3 мөр)

### 3.2 Spectrophotometric Form

**Файл:** `app/labs/water/templates/analysis_forms/spectro_form.html`

- **Баганууд:** dilution, abs1, abs2, r1, r2, average (× dilution factor), diff, control
- **Тооцоолол:**
  - `r1`, `r2` — калибрацийн муруйгаас тооцоолно (TODO: calibration curve)
  - `average` = (r1 + r2) / 2 × dilution
  - `diff` = |r1 - r2| / average × 100%
  - `control` — зөвшөөрөгдөх хэлбэлзэл шалгах
- **cellClassRules:** diff > 10% → улаан, diff ≤ 10% → ногоон

### 3.3 Titration Form

**Файл:** `app/labs/water/templates/analysis_forms/titration_form.html`

- **Баганууд:** v_sample, normality, dilution, blank (CL_W only), v1, v2, v_avg, result
- **Тооцооллын томъёо:**
  - `v_avg` = (v1 + v2) / 2
  - CL_W (Хлорид): `result = (v_avg - blank) × normality × 35.45 × 1000 / v_sample × dilution`
  - Бусад (ALK, HARD г.м.): `result = v_avg × normality × eq_factor × 1000 / v_sample × dilution`
- **CL_W тусгай:** blank багана зөвхөн CL_W шинжилгээнд харагдана

### 3.4 Gravimetric Form

**Файл:** `app/labs/water/templates/analysis_forms/gravimetric_form.html`

- **Баганууд:** volume, m1, m2, result
- **Томъёо:** `result = ((m2 - m1) × 1,000,000) / volume` (mg/L)
- TSS, TDS зэрэг жинлэх аргын шинжилгээнд ашиглана

---

## 4. Нэгдсэн нэгтгэл хуудас (Шинэ)

**Файлууд:**
- `app/labs/water/templates/water_summary.html` — AG Grid template
- `app/labs/water/routes.py` — `/summary` route + `/api/summary_data` API

Усны хими + микробиологи хоёрын шинжилгээний үр дүнг **нэг хүснэгтэнд** нэгтгэсэн хуудас.

### 4.1 Backend API (`/api/summary_data`)

- `Sample` + `AnalysisResult` хүснэгтүүдээс join query
- **Химийн үр дүн:** analysis_code бүрээр (PH, EC, FE_W, ...) raw_data.value татна
- **Микробиологийн үр дүн:** `MICRO_WATER` analysis_code → raw_data-с cfu_22, cfu_37, ecoli, salmonella татна
- **Date filter:** `date_from`, `date_to` query parameter
- **Limit:** 300 дээж хүртэл
- **Response format:**
  ```json
  {
    "rows": [...],
    "chem_params": [{"code": "PH", "name": "pH", "unit": "", "limit": [6.5, 8.5]}, ...],
    "micro_fields": [{"field": "cfu_22", "name": "CFU 22°C", "limit": [null, 100]}, ...]
  }
  ```

### 4.2 AG Grid Frontend

Нүүрсний лабын `sample_summary.js` загвараар хэрэгжүүлсэн:

- **Динамик баганууд:** API-с ирсэн `chem_params` + `micro_fields`-р автомат үүсгэнэ
- **Fixed баганууд:** №, Дээж (pinned left, floatingFilter), Огноо, Нэгж
- **headerClass:** `chem-header` (цэнхэр), `micro-header` (ногоон) — ялгаатай өнгөтэй
- **cellClassRules:** MNS limit-с хэтэрсэн утга улаанаар (`cell-over-limit`), норм доторх ногооноор (`cell-within-limit`) тодорно
- **Микро тусгай:** `cell-detect-fail` (илэрсэн), `cell-detect-pass` (илрээгүй)
- **Column state persistence:** `localStorage`-д баганы өргөн, байрлал, эрэмбэ хадгалагдана
- **CSV export:** AG Grid `exportDataAsCsv()` ашигласан — нүүрсний лабтай адил
- **Clipboard copy:** Сонгосон мөрүүдийг clipboard-д хуулна
- **Date filter:** Огноо сонгож шүүх боломжтой
- **Row count badge:** Нийт мөрийн тоо header-д харагдана

---

## 5. Hub линкүүд шинэчлэл

### 5.1 Микробиологийн Hub

**Файл:** `app/labs/microbiology/templates/micro_hub.html`

- "Нэгтгэл" карт → `url_for('water.water_summary')` руу заасан (хуучин `microbiology.summary` биш)
- Тайлбар: "Усны хими + микробиологи — нэгдсэн үр дүнгийн нэгтгэл"

### 5.2 Усны шинжилгээний Hub

**Файл:** `app/labs/water/templates/water_analysis_hub.html`

- Header actions-д "Нэгтгэл" товч нэмсэн → `url_for('water.water_summary')`

### 5.3 Усны Hub

**Файл:** `app/labs/water/templates/water_hub.html`

- Нэгтгэл nav card нэмсэн

---

## 6. aggrid_macros.html цэвэрлэгээ

**Файл:** `app/templates/analysis/partials/aggrid_macros.html`

- `water_sample_selector_ui()` macro устгасан — layout-д шилжсэн
- `water_sample_selector_js()` macro устгасан — layout-д шилжсэн

---

## 7. Бусад өөрчлөлтүүд

| Файл | Тайлбар |
|------|---------|
| `app/labs/water/constants.py` | Params бүтэц шинэчлэл — categories, standard нэмсэн |
| `app/labs/water/utils.py` | Туслах функц нэмэлт |
| `app/labs/water/templates/water_register.html` | UI сайжруулалт |
| `app/utils/license_protection.py` | Бага засвар |

---

## Өөрчлөгдсөн файлуудын бүрэн жагсаалт

| # | Файл | Төрөл | Тайлбар |
|---|------|-------|---------|
| 1 | `app/labs/water/templates/analysis_forms/water_ws_layout.html` | **Шинэ** | Shared layout — header, grid, modal, timer, draft |
| 2 | `app/labs/water/templates/analysis_forms/ph_ec_form.html` | Дахин бичсэн | Layout extend — default баганууд |
| 3 | `app/labs/water/templates/analysis_forms/spectro_form.html` | **Шинэ** | Layout extend — dilution, abs, control |
| 4 | `app/labs/water/templates/analysis_forms/titration_form.html` | **Шинэ** | Layout extend — titration тооцоолол |
| 5 | `app/labs/water/templates/analysis_forms/gravimetric_form.html` | **Шинэ** | Layout extend — жинлэх арга |
| 6 | `app/labs/water/templates/water_summary.html` | **Шинэ** | Нэгдсэн нэгтгэл — AG Grid |
| 7 | `app/labs/water/routes.py` | Засвар | `/summary` route + `/api/summary_data` API |
| 8 | `app/labs/water/templates/water_analysis_hub.html` | Засвар | Нэгтгэл товч нэмсэн |
| 9 | `app/labs/water/templates/water_hub.html` | Засвар | Нэгтгэл nav card |
| 10 | `app/labs/water/templates/water_register.html` | Засвар | UI шинэчлэл |
| 11 | `app/labs/water/constants.py` | Засвар | Params бүтэц, categories |
| 12 | `app/labs/water/utils.py` | Засвар | Туслах функцууд |
| 13 | `app/labs/microbiology/templates/micro_hub.html` | Засвар | Нэгтгэл линк шинэчлэл |
| 14 | `app/utils/license_protection.py` | Засвар | Бага засвар |
