# File Structure Refactoring Log

**Огноо:** 2026-02-05
**Зорилго:** Төслийн файлын бүтцийг цэгцлэх

---

## ҮЕ ШАТ 1: Root Directory цэвэрлэх ✅

### 1.1 Устгасан файлууд

#### Screenshots (26 файл):
- Capture.PNG0112.PNG
- Capture.JPG0130.JPG - Capture.JPG02042.JPG (20 файл)
- Screenshot 2025-12-20/21 (6 файл)

#### Temp/Malformed файлууд:
- `{`, `nul`, `D:icpmsbackendsamples_temp.json`, `coal_lims_backup_20251222.dump`

#### Хоосон folder:
- `approutesapi/`

### 1.2 Зөөсөн файлууд → scripts/seeds/
| seed_*.py (7 файл) → scripts/seeds/ |

**Commit:** `2af2697`

---

## ҮЕ ШАТ 2: Templates нэгтгэх ✅

### Зөөсөн templates:
- `app/labs/petrography/templates/` → `app/templates/labs/petrography/` (5 файл)
- `app/labs/water_lab/chemistry/templates/` → `app/templates/labs/water/chemistry/` (19 файл)
- `app/labs/water_lab/microbiology/templates/` → `app/templates/labs/water/microbiology/` (9 файл)

### Blueprint засварууд:
- `template_folder` устгасан
- `render_template()` зам шинэчилсэн (34 газар)

**Commit:** `8dbc4a0`

---

## ҮЕ ШАТ 3: Routes зохион байгуулах ✅

### Зөөсөн routes:
| Хуучин | Шинэ |
|--------|------|
| admin_routes.py | routes/admin/routes.py |
| settings_routes.py | routes/settings/routes.py |
| report_routes.py | routes/reports/routes.py |
| import_routes.py | routes/imports/routes.py |
| yield_routes.py | routes/yield_calc/routes.py |
| license_routes.py | routes/license/routes.py |
| chat_events.py | routes/chat/events.py |

### app/__init__.py засварууд:
- Бүх import зам шинэчилсэн

**Commit:** `c1c36f6`

---

## ҮЕ ШАТ 4: Models.py package болгох ✅

### Өөрчлөлт:
- `app/models.py` → `app/models/models.py` зөөсөн
- `app/models/__init__.py` үүсгэж бүх models re-export
- Backward compatibility хадгалагдсан

**Commit:** `88b8704`

---

## Явц

| Үе шат | Статус | Commit |
|--------|--------|--------|
| 1. Root cleanup | ✅ Done | 2af2697 |
| 2. Templates | ✅ Done | 8dbc4a0 |
| 3. Routes | ✅ Done | c1c36f6 |
| 4. Models | ✅ Done | 88b8704 |

---

## Эцсийн бүтэц

```
app/
├── models/              # Models package
│   ├── __init__.py      # Re-export бүх models
│   └── models.py        # Бүх models (3126 мөр)
│
├── templates/
│   ├── [үндсэн 130]
│   └── labs/
│       ├── petrography/ (5)
│       └── water/
│           ├── chemistry/ (19)
│           └── microbiology/ (9)
│
├── routes/
│   ├── admin/routes.py
│   ├── settings/routes.py
│   ├── imports/routes.py
│   ├── yield_calc/routes.py
│   ├── license/routes.py
│   ├── chat/events.py
│   ├── reports/routes.py
│   └── [main/, api/, analysis/, equipment/, chemicals/, spare_parts/, quality/]
│
└── labs/                # Blueprints (templates хасагдсан)
    ├── petrography/
    └── water_lab/
        ├── chemistry/
        └── microbiology/

scripts/
└── seeds/               # Seed scripts (7 файл)
```
