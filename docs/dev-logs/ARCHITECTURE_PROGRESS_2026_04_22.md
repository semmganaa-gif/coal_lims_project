# Архитектурын сайжруулалт — Ахиц дэвшлийн лог 2026-04-22

**Эх сурвалж:** `ARCHITECTURE_PLAN_2026_04_22.md` Sprint 1
**Статус:** Хэсэгчлэн дуусав (Day 1 үйл ажиллагаа)

---

## ✅ Дууссан алхмууд

### S1.4 — `X-XSS-Protection` header хасах (БҮТЭН)
**Файл:** `app/bootstrap/security_headers.py:26-28`
- Deprecated header (Chrome 78+, Edge 17+-д үл хамаарна)
- MDN-ийн зөвлөмж: огт тавихгүй байх
- Comment-аар шалтгааныг бүртгэсэн

### S1.1a — CSP-д `nonce-{nonce}` нэмэх (БҮТЭН)
**Файл:** `app/bootstrap/security_headers.py:30-52`
- `script-src`-д `'nonce-{nonce}'` нэмсэн
- `style-src`-д `'nonce-{nonce}'` нэмсэн
- Template-үүд аль хэдийн `nonce="{{ csp_nonce }}"` бүхий тул нэн даруй идэвхжинэ
- Шинээр `base-uri 'self'` болон `form-action 'self'` нэмсэн (CSP3 hardening)
- `'unsafe-inline'` + `'unsafe-eval'` хэвээр үлдсэн — доорх блокуудад дэлгэрэнгүй

**Smoke test үр дүн:**
```
Status: 200
CSP present: True
X-XSS removed: True
Nonce in script-src: True
base-uri present: True
form-action present: True
```

### S1.3 — `connect_args` dialect-оор нөхцөлт болгох (БҮТЭН)
**Файл:** `config/database.py`
- `_build_engine_options(db_uri)` helper үүсгэсэн
- PostgreSQL: `statement_timeout`, pool-ийн тохиргоо + connect_args
- SQLite: `check_same_thread=False` л тавина, PG-тусгай `options`-ыг оруулахгүй
- `postgresql://`, `postgresql+psycopg2://`, `postgres://` гурван variant-ыг хүлээн авна
- Assertion-тэй baseline тест ногоон

---

## 🔍 Sprint 1.1-ийн бодит хэмжүүр (шинэ олдвор)

**Анхны төлөвлөгөөнд:** "Sprint 1.1: CSP + remove unsafe-inline/eval" → 1 өдөр, 10-20 template
**Бодит цар хүрээ:**

| Хэмжүүр | Тоо | Хязгаарлалт |
|---|---:|---|
| Inline `<script>` блок | 232 (121 template) | Nonce-аар шийдэж болно — аль хэдийн цөөнх хэсэгт зэрэг хийгдсэн |
| Inline event handler (`onclick=""` гм) | **277** (76 template) | `script-src 'unsafe-inline'` шаардлагатай |
| Inline `style=""` attribute | **44+** (эхний 5 файлаас л) | `style-src 'unsafe-inline'` шаардлагатай |
| `eval()` / `new Function()` өөрийн кодод | 0 | — |
| Alpine.js CDN build `new Function()` | 1 (Alpine цөм) | `'unsafe-eval'` заавал |

**Үр дүн:** `'unsafe-inline'` болон `'unsafe-eval'`-г нэн даруй устгах **боломжгүй**. Устгахын өмнө дараах refactor шаардлагатай:

1. **277 inline event handler** → external JS + `addEventListener`
2. **44+ inline style** → class/utility CSS
3. **Alpine.js** → CSP-compatible build руу шилжиж, x-data expression-уудыг object-руу шилжүүлэх

---

## 📝 Шинэчилсэн төлөвлөгөө (Sprint 1.1 үргэлжлэл)

| Дэд алхам | Агуулга | Хэмжээ | Статус |
|---|---|---|---|
| S1.1a | CSP nonce + header hardening | 0.5 өдөр | ✅ ДУУССАН |
| S1.1b | 277 inline handler → external JS (template-ийн бүлгээр) | 1-2 долоо хоног | 🔜 дараагийн |
| S1.1c | 44+ inline style → class | 2-3 өдөр | — |
| S1.1d | Alpine CSP build + x-data object-based migration | 3-4 өдөр | — |
| S1.1e | CSP-аас `'unsafe-inline'` + `'unsafe-eval'` хасах | 0.5 өдөр | — |

**Шинэ нийт:** Sprint 1.1 = 1 өдрөөс → ~3 долоо хоног.

### Sprint 1.1b батч стратеги (277 handler):
1. **Batch 1 (~30 handler):** `errors/` + `spare_parts/` + `settings/` — бага эрсдэлтэй
2. **Batch 2 (~60 handler):** `equipment/` + `chemicals/` — мэдэгдэж буй workflow
3. **Batch 3 (~60 handler):** `analysis_page.html` + `analysis_config*.html` — cross-cutting
4. **Batch 4 (~70 handler):** `labs/water/*` — хамгийн том cluster
5. **Batch 5 (~60 handler):** `quality/` + `reports/` + үлдсэн

Batch бүрийн дараа тест + CSP report-only хяналт → enforce.

---

## 📊 KPI шинэчилсэн

| Үзүүлэлт | Эхлэл (өглөө) | Одоо (үд дунд) | Зорилго (Sprint 1 төгсгөл) |
|---|---:|---:|---:|
| CSP `unsafe-inline` (script) | Тийм | Тийм | ✗ (Sprint 1.1e-д) |
| CSP `unsafe-eval` (script) | Тийм | Тийм | ✗ (Sprint 1.1d-д) |
| CSP `nonce-` | Үгүй | **Тийм** | Тийм |
| `X-XSS-Protection` (deprecated) | Тавиастай | **Хасагдсан** | Хасагдсан |
| CSP `base-uri`, `form-action` | Үгүй | **Тавьсан** | Тавьсан |
| SQLite dev engine үүсэх | Эргэлзэлтэй | **Баталгаажсан** | Баталгаажсан |
| `connect_args` dialect-branched | Үгүй | **Тийм** | Тийм |

---

## 🗂 Өнөөдрийн коммит санал (хэрэв OK гэвэл)
**Коммит 1:** `fix(security): CSP nonce идэвхжүүлж, deprecated X-XSS-Protection хасах`
- `app/bootstrap/security_headers.py`

**Коммит 2:** `fix(config): DB connect_args-ыг dialect-оор нөхцөлт болгох`
- `config/database.py`

**Коммит 3:** `docs: 2026-04-22 архитектур аудит + төлөвлөгөө + ахиц дэвшил`
- `docs/dev-logs/ARCHITECTURE_AUDIT_2026_04_22.md`
- `docs/dev-logs/ARCHITECTURE_PLAN_2026_04_22.md`
- `docs/dev-logs/ARCHITECTURE_PROGRESS_2026_04_22.md`

---

## ⏭ Дараагийн алхам (Day 2)
**S1.1b Batch 1 эхлүүлэх:** `errors/` + `spare_parts/` + `settings/` template-үүдэд байгаа ~30 inline handler-ыг external JS + `addEventListener`-руу шилжүүлэх.

---

## 📝 Day 1 үргэлжлэл — Batch 1 & 2

### Batch 1 (errors/ + spare_parts/ + settings/) — БҮТЭН
- **9 handler хасагдсан** (бодитоор 30 биш)
- 8 template бүрэн цэвэр
- Шинэ файл: `app/static/js/csp_handlers.js` (4 төрлийн delegated listener)
- `base.html`-д `csp_handlers.js` холбогдсон

### Batch 2 (equipment/ + chemicals/) — БҮТЭН
- **25 handler хасагдсан**
- 13 template бүрэн цэвэр (equipment: 9, chemicals: 4)
- `csp_handlers.js`-д `data-action="print"` нэмэгдсэн
- `equipment_register.js`-д auto-bind click handler нэмэгдсэн (6 template хуваалцдаг)

### Өссөн үзүүлэлт
| Үе шат | Handler | Template |
|---|---:|---:|
| Эхлэл (өглөө) | 277 | 76 |
| Batch 1 | ~268 | 73 |
| Batch 2 | **243** | **55** |
| **Бууралт** | **−34 (12.3%)** | **−21** |

### Дараагийн алхам (Day 3)
**Batch 3:** `analysis_page.html` (31) + `analysis_config*.html` (17+6) + `workflow_admin.html` (8) + `archive_hub.html` (4) — ~66 handler. Энэ бол хамгийн cross-cutting бүлэг.
