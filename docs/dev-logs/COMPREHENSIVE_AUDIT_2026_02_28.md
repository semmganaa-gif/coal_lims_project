# Иж бүрэн Code Audit — 2026-02-28

## Хамрах хүрээ
4 чиглэлийн аудит зэрэг хийгдсэн:
1. Performance & N+1 Query
2. Business Logic Correctness
3. API Design & Consistency
4. DB Schema & Model

---

## НЭГТГЭЛ (Summary Scorecard)

| Аудитын төрөл | 🔴 CRITICAL | 🟠 HIGH | 🟡 MEDIUM | 🔵 LOW | Нийт |
|---------------|------------|---------|-----------|--------|------|
| Performance | 3 | 6 | 5 | 0 | 14 |
| Business Logic | 6 | 5 | 4 | 2 | 17 |
| API Design | 1 | 4 | 2 | 1 | 8 |
| DB Schema | 8 | 19 | 11 | 4 | 42 |
| **НИЙТ** | **18** | **34** | **22** | **7** | **81** |

---

## 1. PERFORMANCE & N+1 QUERY АУДИТ

### CRITICAL (3)

| # | Асуудал | Файл:Мөр | Нөлөө |
|---|---------|----------|--------|
| P-C1 | N+1: bulk_update_status дотор Sample.query.get() loop | senior.py:263-307 | 100 result → 100 query |
| P-C2 | Pagination байхгүй: ahlah_data `.all()` limit-гүй | senior.py:101 | 10,000+ row санах ойд |
| P-C3 | LIKE '%X%' full table scan DataTables column filter | samples_api.py:99-127 | Index ашиглагдахгүй |

### HIGH (6)

| # | Асуудал | Файл:Мөр |
|---|---------|----------|
| P-H1 | N+1: audit_api.py User.query.get() loop | audit_api.py:151 |
| P-H2 | User.query.all() admin manage_users limit-гүй | admin/routes.py:101 |
| P-H3 | Олон COUNT(*) нэг хүсэлтэд (spare_parts 3×, chemicals 4×) | spare_parts/crud.py:185, chemicals/api.py:309 |
| P-H4 | Water lab: 500 sample × бүх result → 5000+ объект | water routes.py:67-70 |
| P-H5 | get_analysis_schema() N+1 loop | senior.py:44-46 |
| P-H6 | QC module `.all()` limit-гүй | qc.py:50,84 |

### MEDIUM (5)

| # | Асуудал | Файл |
|---|---------|------|
| P-M1 | AnalysisType.query.all() form __init__-д | forms.py:337 |
| P-M2 | Dashboard 4× count query | index.py:105-117 |
| P-M3 | Admin routes `.all()` (AnalysisType, Profile, GBW) | admin/routes.py |
| P-M4 | Missing composite index (received_date, lab_type, status) | models/core.py |
| P-M5 | status_map 25 sample × N result | samples_api.py:140-150 |

---

## 2. BUSINESS LOGIC АУДИТ

### CRITICAL (6)

| # | Асуудал | Файл:Мөр | ISO 17025 |
|---|---------|----------|-----------|
| B-C1 | Rejected → Approved шууд шилжих (retest шаардахгүй) | analysis_api.py:612-651 | 7.7.2 зөрчил |
| B-C2 | Химич өөрийн үр дүнг auto-approve хийх боломжтой | analysis_api.py:289-400, 586-604 | Бие даасан хяналт зөрчил |
| B-C3 | Sample code race condition → 500 error (409 биш) | models/core.py:204 | — |
| B-C4 | final_result=NULL + status='approved' зөвшөөрөгддөг | analysis.py:62, analysis_api.py:335 | Шинжилгээний бүрэн бүтэн байдал |
| B-C5 | Malformed JSON raw_data batch save-г бүхэлд нь сүйтгэнэ | analysis_api.py:359-375 | — |
| B-C6 | Буруу lab_type дээр analysis үүсгэх боломжтой | analysis_api.py:354, water routes.py:891 | — |

### HIGH (5)

| # | Асуудал | Файл:Мөр |
|---|---------|----------|
| B-H1 | TRD temp коэффициент range-ээс гадуур → silent None | server_calculations.py:806-842 |
| B-H2 | CV тооцоо сөрөг утга гаргах боломжтой (S>3%) | server_calculations.py:500-507 |
| B-H3 | CSR дээд хязгаар байхгүй (150% зөвшөөрөгдөнө) | analysis_rules.py:184-187 |
| B-H4 | analyses_to_perform-д байхгүй code-оор result үүсгэх | analysis_api.py:132-247 |
| B-H5 | Lab type validation analysis endpoint-д байхгүй | = B-C6 |

### MEDIUM (4)

| # | Асуудал | Файл |
|---|---------|------|
| B-M1 | Percent diff epsilon=0.0001 бага утгад false alarm | server_calculations.py:1119 |
| B-M2 | No-op status update дээр audit log үүсдэг | analysis_api.py:651, 714 |
| B-M3 | Tolerance exceeded flag parallel тус бүрд биш глобал | analysis_api.py:382-400 |
| B-M4 | Archived sample дээр шинэ analysis зөвшөөрөгдөнө | water routes.py:891 |

---

## 3. API DESIGN & CONSISTENCY АУДИТ

### CRITICAL (1)

| # | Асуудал | Файл:Мөр |
|---|---------|----------|
| A-C1 | str(e) error leak client руу | chemicals/api.py:243, 484 |

### HIGH (4)

| # | Асуудал | Тоо |
|---|---------|-----|
| A-H1 | Response format зөрүүтэй (success field дутмаг) | 67 endpoint |
| A-H2 | Rate limiting дутмаг | 21+ endpoint (chemicals, equipment, spare_parts) |
| A-H3 | Input validation дутмаг (type, bounds, required) | 12 газар |
| A-H4 | Unbounded array хүлээн авдаг (bulk endpoints) | 3 endpoint |

### MEDIUM (2)

| # | Асуудал |
|---|---------|
| A-M1 | POST → DELETE/PUT method зөрүү |
| A-M2 | Content-Type validation дутмаг |

---

## 4. DB SCHEMA & MODEL АУДИТ

### CRITICAL (8)

| # | Асуудал | Файл:Мөр |
|---|---------|----------|
| D-C1 | Sample.sample_code nullable (unique байсан ч NULL орно) | core.py:204 |
| D-C2 | Sample.user_id nullable (бүртгэлгүй дээж) | core.py:209 |
| D-C3 | AnalysisResult.final_result Float → Numeric(10,4) шаардлагатай | analysis.py:62 |
| D-C4 | Sample.weight Float → Numeric(12,4) шаардлагатай | core.py:220 |
| D-C5 | AnalysisResult.status CHECK constraint байхгүй | analysis.py:66-71 |
| D-C6 | Sample.status CHECK constraint байхгүй | core.py:211 |
| D-C7 | Sample → AnalysisResult cascade delete-orphan (audit trail устана) | core.py:266-271 |
| D-C8 | AnalysisResult.user_id nullable | analysis.py:61 |

### HIGH (19)

| Бүлэг | Тоо | Тодорхойлолт |
|--------|-----|-------------|
| NOT NULL constraints | 3 | client_name, analyses_to_perform, BottleConstant |
| CHECK constraints | 6 | Equipment.status, Chemical.status, CA.severity, CA.status |
| FK constraints | 3 | mass_ready_by_id, SystemSetting.updated_by_id |
| Float → Numeric | 4 | BottleConstant.trial*, WashabilityTest, SolutionPreparation |
| Cascade delete | 3 | Bottle→Constant, Equipment→Logs, Chemical→Usage |

### MEDIUM (11) — Index gaps, soft-delete, lazy loading

---

## ДАВХАРДСАН / ХОЛБОГДОХ АСУУДЛУУД

| Аудит A | Аудит B | Тайлбар |
|---------|---------|---------|
| B-C2 (auto-approve) | D-C5 (status CHECK) | Status constraint + role check хоёулаа шаардлагатай |
| P-C2 (no pagination) | A-H4 (unbounded) | Бүх endpoint-д limit/pagination нэмэх |
| B-C4 (NULL final_result) | D-C3 (Float) | Data type + constraint хоёулаа засах |
| P-H3 (олон COUNT) | A-H1 (response format) | API refactor үед хоёулаа засагдана |

---

## ЭН ТЭРГҮҮНД ЗАСАХ (Top 10 Priority)

| # | Асуудал | Эрсдэл | Хүчин чармайлт |
|---|---------|--------|---------------|
| 1 | **B-C2**: Химич auto-approve хориглох | 🔴 ISO | 10 мин |
| 2 | **B-C1**: Rejected → retest шаардах | 🔴 ISO | 30 мин |
| 3 | **A-C1**: str(e) error leak устгах | 🔴 Security | 5 мин |
| 4 | **B-C6**: Lab type validation нэмэх | 🔴 Data | 15 мин |
| 5 | **P-C1**: senior.py bulk_update N+1 засах | 🔴 Perf | 10 мин |
| 6 | **P-C2**: ahlah_data pagination нэмэх | 🔴 Perf | 15 мин |
| 7 | **A-H2**: Rate limiting chemicals/equipment/spare | 🟠 Security | 15 мин |
| 8 | **A-H4**: Bulk array size cap (100 max) | 🟠 DoS | 10 мин |
| 9 | **B-M4**: Archived sample дээр analysis хориглох | 🟡 Logic | 5 мин |
| 10 | **P-H3**: COUNT → GROUP BY нэгтгэл | 🟠 Perf | 20 мин |

### DB Schema (тусдаа migration шаардана)
| # | Засвар | Хугацаа |
|---|--------|---------|
| D-C3 | Float → Numeric(10,4) final_result | 2 цаг + тест |
| D-C7 | Cascade delete → SET NULL | 1 цаг |
| D-C5,6 | CHECK constraints (status enum) | 30 мин |
| Soft delete | Sample, Equipment, Chemical | 3 цаг |

---

## САЙН ТЭМДЭГЛЭЛ (Positive Findings)

✅ with_for_update() pessimistic locking — coal, water, mass, senior
✅ version_id_col optimistic locking — AnalysisResult
✅ markupsafe.escape() XSS хамгаалалт
✅ safe_commit() pattern тархалт
✅ AnalysisResultLog ISO 17025 audit trail
✅ compute_hash() data integrity
✅ VALID_WATER_ANALYSIS_CODES whitelist
✅ escape_like_pattern() SQL injection хамгаалалт
✅ FormGuards double-submit/beforeunload
✅ Composite indexes dashboard query-д
✅ Statement timeout 30s
✅ Pool sizing 25+25=50
