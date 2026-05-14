# Архитектур / Технологийн аудит — 2026-04-22

**Огноо:** 2026-04-22
**Хамрах хүрээ:** `Технологийн стек` ба `Архитектур` хэсгийн бодит байдал
**Арга:** Код-баримт тулгалт (grep + structural inspection)
**Үндсэн эх сурвалж:** `README.md` дээр зарласан `Route → Service → Repository → Model` pattern-ийн хэрэгжилт

---

## Executive Summary

README дээр зарласан давхарга хуваарь **бодитоор хадгалагдаагүй**. Технологийн сонголт ерөнхийдөө зөв боловч **CSP аюулгүй байдал, dev/prod config зөрчил, supply chain, давхаргын цэвэр байдал** зэрэг 15 тодорхой цэгт сайжруулалт шаардлагатай.

---

## 🔴 КРИТИК (даруй)

### 1. CSP nonce — хэрэгжээгүй
**Байршил:** `app/bootstrap/security_headers.py:30-38`
- `csp_nonce` үүсгэж template-д inject хийдэг
- Гэвч CSP header дотор `'unsafe-inline' 'unsafe-eval'` hard-coded → nonce утгагүй
- XSS-ээс хамгаалах CSP-ийн үндсэн зорилго устсан
- `X-XSS-Protection` header deprecated, орчин үеийн browser-ууд ашиглахгүй

### 2. `connect_args` SQLite-тай нийцэхгүй
**Байршил:** `config/database.py:17-24`
- `connect_args={"options": "-c statement_timeout=30000"}` нь PostgreSQL/psycopg2-тусгай
- SQLite dev-д engine үүсгэх үед унах магадлалтай
- Тестэд `:memory:` override хэрэглэж байгаагаар нуугдаж байна

### 3. CDN хараат байдал (supply chain)
- `base.html` + 10 template: `cdn.jsdelivr.net`, `unpkg.com` → 30+ ашиглалт
- SRI (Subresource Integrity) hash байхгүй
- `node_modules/`, `vite.config.js` байгаа атал local bundle хийдэггүй

---

## 🟠 ӨНДӨР (архитектурын үндсэн)

### 4. Давхаргын зөрчил — бодит тоо баримт

| Давхарга | Файлын тоо | Шууд `db.session.*` | Шууд `Model.query.*` | `from app.repositories` |
|---|---:|---:|---:|---:|
| Routes | 38 | 96 | 100 | 23 |
| Services | 18 | 145 | 80 | 8 (зөвхөн 6 service) |
| Labs | 7 | 63 | — | 0 |

**Дүгнэлт:** Repository layer байгаа боловч **бараг ашиглагддаггүй**. Services өөрсдөө DB руу шууд ордог. Routes нь service-гүйгээр шууд DB ашигладаг.

### 5. Service "God object"-ууд
| Файл | Мөр |
|---|---:|
| `analysis_workflow.py` | 1225 |
| `chemical_service.py` | 942 |
| `sample_service.py` | 875 |
| `report_service.py` | 857 |
| `analytics_service.py` | 755 |
| `spare_parts_service.py` | 732 |

Нэг service файлд 3-5 домэйн холилдсон.

### 6. `water_chemistry/routes.py` — 1460 мөр
- CRUD + worksheet + reports + import + solutions нэг файлд
- Харьцуулбал `petrography/routes.py` = 188, `microbiology/routes.py` = 696
- Хэт тэгш бус

### 7. BaseLab хийсвэрлэлт бүрэн биш
**Байршил:** `app/labs/base.py:47-64`
- Coal lab-д өөрийн `routes/` байхгүй, ерөнхий `routes/main|analysis`-т тархсан
- `sample_stats()` = 4 тусдаа `COUNT(*)` query. Dashboard × 4 lab = **16 count query** бүр ачаалалд
- Нэг `GROUP BY status` хангалттай

---

## 🟡 ДУНД (технологийн сонголт)

### 8. Хуучирсан / нэмэлт сангууд
| Сан | Одоогийн | Асуудал |
|---|---|---|
| `sentry-sdk` | 1.39.1 | 1.x EOL, 2.x шилжих ёстой |
| `Flask-SocketIO` | 5.3.6 | Minor security fix-тэй 5.4+ |
| `Flask-Limiter` | 3.5.0 | Minor fix-тэй 3.8+ |
| `pandas` | 2.1.4 | 2.2.x |
| `pytz` | 2024.1 | `zoneinfo` байгаа тул хасах боломжтой |
| `xlrd` | 2.0.1 | .xls legacy, хэрэггүй бол хасах |
| `gevent` + `waitress` + `gunicorn` | — | Production сервер 2 давхар суулгасан — нэгийг сонгох |

### 9. `config/` — dev/prod салбарлалтгүй
- Нэг `Config` класс бүх орчинд
- Тестэд зөвхөн `TestConfig(Config)` override
- `FLASK_ENV=production|development|testing`-ээр салбарлах ёстой

### 10. `mypy` бараг унтраалттай
`pyproject.toml:1-74` — 15+ модуль `disable_error_code` бүхий override. Type-checking бодитоор ажиллахгүй. `strict_optional=false`, `disallow_untyped_defs=false`.

### 11. Rate limiter `memory://` default
`bootstrap/extensions.py:77-84` — production multi-worker орчинд Redis шаардлагатай (warning-ийг log хийдэг боловч анхдагчаар unsafe).

---

## 🟢 БАГА / анхаарах

### 12. N+1 эрсдэл
- `joinedload/selectinload` 13 файлд 25 удаа
- 196+ route-level `.query.filter` relationship preload-гүй
- `sample_stats()` × 4 lab = 16 COUNT dashboard бүрт

### 13. Transaction boundary тодорхойгүй
- `session.commit()` — 50 файлд 151 удаа
- Нэг request-д 3-5 commit элбэг
- Шийдэл: service edge дээр single `@transactional` decorator, routes/repositories-т commit байхгүй

### 14. Vite pipeline ашиглагддаггүй
- `vite.config.js`, `tsconfig.json`, `package.json` бэлэн
- Гэхдээ production-д CDN хэрэглэдэг
- `npm run build` output хаашаа нь орохгүй

### 15. API CSRF exempt бүхэлдээ
`bootstrap/blueprints.py:66` — `csrf.exempt(api_bp)` бүх `api_bp` endpoint-д. `POST/PUT/DELETE` endpoint-ууд Origin/Referer эсвэл token шалгадаггүй тохиолдолд CSRF хамгаалалтгүй.

---

## ✅ Зөв сонголтууд (өөрчлөх шаардлагагүй)

- Flask 3.1 + SQLAlchemy 2.0 + Alembic — modern, production-ready
- Alpine.js + htmx + SSR approach — Jinja-тай сайн зохицдог
- AG Grid v32 — lab table-д зөв сонголт
- BaseLab pattern-ийн үзэл санаа — scalable
- Repository layer **байгаа** — дагаж мөрдөх л дутуу
- Prometheus + Sentry + Grafana observability холбогдсон
- PostgreSQL prod + SQLite dev — тестэд хөнгөн

---

## Хамаарах эх сурвалжууд
- `README.md` — "Архитектура" хэсэг
- `app/bootstrap/security_headers.py`
- `config/database.py`
- `app/labs/base.py`
- `app/labs/water_lab/chemistry/routes.py` (1460 мөр)
- `requirements.txt`
- `pyproject.toml`
- Grep: routes/services давхаргаас шууд DB хандалт
