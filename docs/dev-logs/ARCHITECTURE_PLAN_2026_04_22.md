# Архитектурыг сайжруулах төлөвлөгөө — 2026-04-22

**Эх сурвалж:** `docs/dev-logs/ARCHITECTURE_AUDIT_2026_04_22.md`
**Огноо:** 2026-04-22
**Хамрах хүрээ:** Богино (1-2 долоо хоног) + Урт (1-3 сар) төлөвлөгөө

---

## 🎯 Зорилго
1. README-д зарласан `Route → Service → Repository → Model` давхаргыг **бодитоор тогтоох**
2. Security-ийн КРИТИК цэгүүдийг хаах
3. Maintainability-ийг дээшлүүлэх (том файл, davхардсан давхарга)

---

## 📅 Богино хугацааны төлөвлөгөө (1-2 долоо хоног)

### Sprint 1 — Security & Config (2-3 өдөр)
| № | Ажил | Файл | ETA |
|---|---|---|---:|
| S1.1 | CSP header nonce хэрэглэж, `unsafe-inline/eval` хасах | `app/bootstrap/security_headers.py` + inline `<script>`-тай template-үүд | 1 өдөр |
| S1.2 | Inline JS → external files эсвэл `nonce="{{ csp_nonce }}"` | 10-20 template | 1 өдөр |
| S1.3 | `connect_args` dialect-оор нөхцөлтэй болгох (sqlite vs postgresql) | `config/database.py` | 0.5 өдөр |
| S1.4 | `X-XSS-Protection` header хасах (deprecated) | `security_headers.py` | 0.1 өдөр |

**Exit criteria:** CSP report-only → enforce. XSS test PR суулгаж, inline script блоклогдож байгааг баталгаажуулах.

### Sprint 2 — Supply Chain (2-3 өдөр)
| № | Ажил | Файл | ETA |
|---|---|---|---:|
| S2.1 | `vite.config.js` + entry point бэлдэх (htmx, alpine, bootstrap, aggrid) | `vite.config.js`, `app/static/src/` | 1 өдөр |
| S2.2 | `npm run build` → `app/static/dist/` output | build | 0.5 өдөр |
| S2.3 | `base.html` — CDN-ээр оруулсан linkages-ийг local bundle-аар солих | `app/templates/base.html` + 9 template | 1 өдөр |
| S2.4 | SRI hash үлдсэн гадаад CDN-д (жишээ нь Google Fonts) нэмэх | 3-4 template | 0.5 өдөр |

**Exit criteria:** Network offline дээр dashboard ачаалагдах. CDN 3-rd party байхгүй эсвэл SRI-тай.

### Sprint 3 — Dependency Cleanup (1-2 өдөр)
| № | Ажил | Файл | ETA |
|---|---|---|---:|
| S3.1 | `sentry-sdk 1.x → 2.x` шилжүүлэх + deprecation checker | `requirements.txt` + `app/sentry_integration.py` | 0.5 өдөр |
| S3.2 | `pytz` хасах — `zoneinfo` бүрэн ашиглах | `requirements.txt`, `config/base.py` + хэрэглэсэн газар | 0.5 өдөр |
| S3.3 | `xlrd` хэрэглээг шалгаад — .xls шаардлагагүй бол хасах | `requirements.txt` + `app/utils/excel_import.py` | 0.3 өдөр |
| S3.4 | `gevent*` vs `waitress` — Windows production-д `waitress`, Linux-д `gunicorn + gevent` сонгож нэгийг хасах | `requirements.txt` | 0.3 өдөр |
| S3.5 | Minor хувилбарын upgrade (`Flask-SocketIO`, `Flask-Limiter`, `pandas`) | `requirements.txt` | 0.5 өдөр |

**Exit criteria:** `pip install -r requirements.txt` + `pytest` ногоон. `pip-audit` ажиллуулж CVE-гүй байх.

---

## 📆 Дунд хугацааны төлөвлөгөө (3-6 долоо хоног)

### Sprint 4 — Davхаргын цэвэрлэгээ: Routes → Services (10-14 өдөр)
**Зорилго:** Routes-аас `db.session.*` ба `Model.query.*` call-уудыг бүрэн арилгах (196 call site).

| Алхам | Тайлбар |
|---|---|
| 4.1 | Архитектурын гэрээ (contract) бичих: "Routes нь service-ийн public API-г л дуудна" |
| 4.2 | Routes-г багцлаж, нэг package-ийг route-аар өгөөд services-рүү дамжуулах жишээ refactor (pilot: `routes/equipment/crud.py`) |
| 4.3 | Үлдсэн 23 route file-г багцаар refactor хийх (4-5 давхцалт батч) |
| 4.4 | `ruff` lint rule нэмэх: `routes/` дотор `db.session|\.query\.` эрэмбэ (grep-based pre-commit hook) |

**Exit criteria:**
- `grep -r "db\.session\." app/routes/` = 0 match
- `grep -r "\.query\." app/routes/` = 0 match (зөвхөн `sample_repository.query(...)` г.м. repo дуудлага хийгдэнэ)
- pre-commit hook идэвхжсэн

### Sprint 5 — Services → Repositories (10-14 өдөр)
**Зорилго:** Services нь `db.session.*` эсвэл `Model.query.*`-г бараг ашиглахгүй, зөвхөн repository-гаар дамжина.

| Алхам | Тайлбар |
|---|---|
| 5.1 | Repository public API цэгцлэх: `SampleRepository.get_by_id`, `.list_by_lab(...)` г.м. |
| 5.2 | Services-ийн `db.session` (145) + `.query` (80) call-уудыг дэс дараалан нүүлгэх |
| 5.3 | Test suite refactor: repo layer mock-лох боломжтой болгох |

**Exit criteria:**
- Services-д `db.session.commit()` зөвхөн `@transactional` wrapper-аар дамжина
- Repositories нь DB I/O-ийн цорын ганц цэг

### Sprint 6 — God object salalt (7-10 өдөр)
**Зорилго:** 700+ мөртэй service файлуудыг доменоор хуваах.

| Зорилтот файл | Санал болгож буй хуваалт |
|---|---|
| `analysis_workflow.py` (1225) | `analysis_save.py`, `analysis_approval.py`, `analysis_rejection.py`, `analysis_bulk.py` |
| `chemical_service.py` (942) | `chemical_inventory.py`, `chemical_usage.py`, `chemical_ghs.py` |
| `sample_service.py` (875) | `sample_registration.py`, `sample_naming.py`, `sample_batch.py`, `sample_query.py` |
| `report_service.py` (857) | `report_build.py`, `report_render.py`, `report_email.py` |
| `water_chemistry/routes.py` (1460) | `crud.py`, `worksheet.py`, `reports.py`, `import.py`, `solutions.py` |

**Exit criteria:** Нэг ч service файл > 500 мөр биш.

---

## 🗓️ Урт хугацааны төлөвлөгөө (2-3 сар)

### Sprint 7 — Transaction boundary & data integrity (5-7 өдөр)
- `@transactional` декоратор service edge-ээр нэвтрүүлэх
- Routes, repositories, labs-аас `session.commit()` устгах
- Rollback-ийг audit log нэгэн зэрэг хийх тест нэмэх

### Sprint 8 — BaseLab полисморфизмыг бүрэн ашиглах (5-7 өдөр)
- Coal lab-ийн route-уудыг `app/labs/coal/routes.py`-руу нэгтгэх
- `sample_stats()` → нэг `GROUP BY status` query болгох
- `BaseLab.get_blueprint()` заавал implement болгох

### Sprint 9 — N+1 & Performance (5 өдөр)
- Dashboard, senior review, reports дээр `EXPLAIN ANALYZE` авч эрэмбэлэх
- `joinedload/selectinload` стратегиар хэрэглэх
- Query count assertion-тай тест нэмэх (`pytest-sqlalchemy-mock` эсвэл `SQLALCHEMY_ECHO` хяналт)

### Sprint 10 — Type safety (үргэлжлэх)
- `mypy` override-уудыг аажмаар хасах
- Шинэ код — strict type, хуучин — шатлан шилжих
- Pydantic эсвэл marshmallow schema route boundary-д

### Sprint 11 — Config & deployment (3-5 өдөр)
- `config/` → `DevelopmentConfig`, `ProductionConfig`, `TestingConfig` салгах
- Rate limiter `redis://` production-д албадлагын default
- Docker compose secrets management (`.env.production.vault` г.м.)

### Sprint 12 — API security (3-5 өдөр)
- `csrf.exempt(api_bp)` → token-based ба `SameSite=Strict` cookie guard
- API key эсвэл JWT middleware
- OpenAPI spec (`docs/openapi.yaml`) endpoint бүрийг хамарсан болгох

---

## 📊 Хэмжүүрүүд (KPI)

| Үзүүлэлт | Эхлэл (2026-04-22) | Богино (2 долоо хоног) | Дунд (6 долоо хоног) | Урт (3 сар) |
|---|---:|---:|---:|---:|
| Routes-д `db.session` хандалт | 96 | 96 | 0 | 0 |
| Routes-д `.query` шууд | 100 | 100 | 0 | 0 |
| Services-д `db.session` | 145 | 145 | 30 | 0 |
| 500+ мөртэй service файл | 9 | 9 | 4 | 0 |
| CSP `unsafe-inline` | ✓ байгаа | ✗ устгасан | ✗ | ✗ |
| CDN хамаарал (template-д) | 30+ | < 5 | 0 | 0 |
| `pip-audit` CVE | ? | 0 | 0 | 0 |
| `mypy` override тоо | 15+ | 15+ | 10 | < 5 |

---

## 🚦 Эхлэх дараалал (өнөөдөр эхлэх)

**Өнөөдөр:** `S1.1` — CSP nonce асуудлыг засах. Хамгийн бага эрсдэлтэй, хамгийн том security нөлөө.

**Маргааш:** `S1.3` — `connect_args` dialect-ээр ялгах.

**Энэ долоо хоногт:** Sprint 1 бүрэн дуусгах.

---

## Эрсдэл ба анхаарах

1. **Том refactor (Sprint 4-6)** нь feature нэмэхгүй, гэхдээ тогтворгүй байдал үүсгэж болно. Хяналт:
   - Үе бүрт ногоон CI
   - Feature flag шаардлагагүй (refactor л хийж байна)
   - PR-ууд бага, бие даасан
2. **CSP nonce** нэвтрүүлэхэд inline JS (template дотор `<script>` шууд бичсэн) олдвол тусгай migration хийх ёстой.
3. **Dependency upgrade** — `sentry-sdk 2.x` API-ийн breaking change харах.

---

## Нэмэлт
- Энэхүү төлөвлөгөөг хэрэгжүүлэх тусам `docs/dev-logs/` дотор ахиц дэвшлийн лог үүсгэнэ (жишээ нь `ARCHITECTURE_PROGRESS_2026_04_29.md`).
- Бүрэн дуустал ойролцоогоор 8-10 долоо хоног.
