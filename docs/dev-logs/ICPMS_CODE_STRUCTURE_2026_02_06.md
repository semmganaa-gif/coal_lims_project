# ICPMS Code Structure Analysis

**Огноо:** 2026-02-06
**Төсөл:** ICPMS (Integrated Coal Preparation Management System)
**Байршил:** D:\icpms

---

## 1. Төслийн тойм

| Үзүүлэлт | Утга |
|----------|------|
| **Нэр** | ICPMS - Нүүрс баяжуулах үйлдвэрийн удирдлагын систем |
| **Version** | 1.0.0 |
| **Backend** | FastAPI + SQLAlchemy (async) |
| **Frontend** | React 18 + TypeScript + Vite |
| **Database** | PostgreSQL + TimescaleDB |
| **Auth** | JWT (access + refresh tokens) |

---

## 2. Backend Бүтэц (D:\icpms\backend)

### 2.1 Үндсэн бүтэц

```
backend/
├── app/
│   ├── main.py                    # FastAPI entry point
│   ├── core/                      # Framework config
│   │   ├── config.py              # Settings (DB, JWT, CORS)
│   │   ├── database.py            # AsyncSession, engine
│   │   ├── security.py            # JWT, password hashing
│   │   ├── deps.py                # Dependency injection
│   │   ├── logging.py             # Structured logging
│   │   └── middleware.py          # Request logging
│   ├── models/                    # SQLAlchemy ORM
│   │   ├── user.py                # User, UserRole
│   │   ├── audit.py               # AuditLog
│   │   ├── chpp.py                # CHPPEquipment, ScadaTag
│   │   ├── washability.py         # WashabilityTest, Fractions
│   │   ├── module_process.py      # Module, SamplingPoint
│   │   └── optimization.py        # Seam, Stockpile, Scenario
│   ├── schemas/                   # Pydantic validation
│   │   ├── user.py                # UserCreate, Token
│   │   ├── washability.py         # WashabilityTest schemas
│   │   ├── module_process.py      # ProcessSample schemas
│   │   └── ...
│   ├── api/                       # FastAPI routes
│   │   ├── auth.py                # Login, register, users
│   │   ├── module_process.py      # Module yields
│   │   ├── washability/           # Float-sink analysis
│   │   │   ├── __init__.py
│   │   │   ├── analysis.py
│   │   │   ├── crud.py
│   │   │   ├── indices.py         # NGM calculations
│   │   │   ├── yield_estimation.py
│   │   │   └── excel_import.py
│   │   ├── optimization.py        # Blend optimization
│   │   ├── blending.py            # Coal blending
│   │   ├── pretreatment.py        # Drop shatter, sieve
│   │   ├── scada.py               # OPC UA integration
│   │   ├── daily_report.py        # Daily reports
│   │   ├── lims.py                # Coal LIMS integration
│   │   ├── yield_calc.py          # Yield calculations
│   │   ├── chpp.py                # Equipment, samples
│   │   └── process_flow.py        # Process diagrams
│   ├── services/                  # Business logic
│   │   ├── washability/           # Washability services
│   │   │   ├── indices.py         # NGM, NGMI
│   │   │   ├── cumulative.py      # Cumulative yield/ash
│   │   │   ├── m_curve.py         # M-curve (Mayer)
│   │   │   ├── partition.py       # Density partitioning
│   │   │   └── data_classes.py
│   │   ├── washability_constants.py  # Standards, NGM classification
│   │   ├── optimizer.py           # Optimization algorithms
│   │   ├── two_stage_optimizer.py # Two-stage optimization
│   │   ├── blending.py            # Blending logic
│   │   ├── pretreatment.py        # Pretreatment calcs
│   │   ├── opc_client.py          # OPC UA client
│   │   ├── lims_service.py        # LIMS API communication
│   │   ├── audit.py               # Audit logging
│   │   └── utils/
│   │       ├── db_helpers.py
│   │       └── fraction_utils.py
│   └── db/
│       └── seed_module_process.py # Initial data
├── alembic/                       # DB migrations
│   └── versions/
├── tests/
│   ├── conftest.py
│   ├── test_washability.py
│   └── test_module_process.py
├── venv/                          # Virtual environment
└── requirements.txt
```

### 2.2 API Endpoints

| Endpoint | Method | Зорилго |
|----------|--------|---------|
| `/api/auth/login` | POST | Нэвтрэлт |
| `/api/auth/register` | POST | Шинэ хэрэглэгч (admin) |
| `/api/auth/refresh` | POST | Token шинэчлэх |
| `/api/auth/me` | GET | Одоогийн хэрэглэгч |
| `/api/auth/setup` | POST | Анхны admin үүсгэх |
| `/api/auth/users` | GET | Хэрэглэгчийн жагсаалт |
| `/api/module-process/modules` | GET | 3 модуль (I, II, III) |
| `/api/module-process/modules/{id}/sampling-points` | GET | 19 sampling point |
| `/api/module-process/samples` | GET/POST | Process samples |
| `/api/module-process/yield` | POST | Yield тооцоолол |
| `/api/washability/tests` | GET/POST | Washability tests |
| `/api/washability/fractions/{test_id}` | GET | Float-sink fractions |
| `/api/washability/yield/estimate` | POST | Theoretical yield |
| `/api/washability/indices/ngm` | GET | NGM тооцоолол |
| `/api/washability/import/excel` | POST | Excel import |
| `/api/optimization/optimize` | POST | Blend optimization |
| `/api/optimization/scenarios` | GET/POST | Scenarios |
| `/api/blending/calculate` | POST | Blending calc |
| `/api/pretreatment/drop-shatter` | POST | Drop shatter test |
| `/api/pretreatment/sieve-analysis` | POST | Sieve analysis |
| `/api/scada/tags` | GET | SCADA tags |
| `/api/scada/readings` | GET/POST | SCADA data |
| `/api/chpp/equipment` | GET/POST | Equipment |
| `/api/chpp/samples` | GET/POST | CHPP samples |
| `/api/daily-report/generate` | POST | Daily report |
| `/api/lims/samples` | GET/POST | LIMS integration |
| `/api/yield/calculate` | POST | Ash balance yield |

---

## 3. Database Models

### 3.1 User & Auth

```python
class UserRole(str, enum.Enum):
    ADMIN = "ADMIN"       # Бүх эрх
    OPERATOR = "OPERATOR" # Read + Create + Update
    VIEWER = "VIEWER"     # Зөвхөн Read

class User(Base):
    __tablename__ = "users"
    id, username, email, hashed_password
    full_name, role (UserRole)
    is_active, is_superuser
    last_login, created_at, updated_at

class AuditLog(Base):
    __tablename__ = "audit_logs"
    id, user_id, username
    action, resource_type, resource_id
    description, old_values (JSON), new_values (JSON)
    ip_address, user_agent, created_at
```

### 3.2 Module Process

```python
class ModuleConfiguration(Base):
    __tablename__ = "module_configurations"
    id, module (enum: I, II, III)
    commissioned_year, design_capacity_mtpa, design_capacity_tph
    medium_particle_method (spiral vs TBS)
    hmc1_design_density, hmc2_design_density
    flotation_type, flotation_cells
    # Relationships: sampling_points, process_stages

class SamplingPoint(Base):
    __tablename__ = "sampling_points"
    id, module_config_id
    point_number (1-19), point_code, location_name
    process_stage, product_type, sampling_type
    particle_size, sample_state
    is_automatic, sampling_frequency_min
    # Relationships: process_samples

class ProcessSample(Base):
    __tablename__ = "process_samples"
    id, sampling_point_id, lims_sample_id
    module, sample_date, shift
    sample_weight_kg, solid_percent, liquid_percent
    # Proximate analysis:
    moisture_ad, ash_ad, volatile_ad, fixed_carbon_d
    # Ultimate analysis:
    sulfur_ad, calorific_ad
    # Coking properties:
    caking_index, free_swelling_index
    validation_status, notes

class ModuleYieldCalculation(Base):
    __tablename__ = "module_yield_calculations"
    id, module, calculation_date, shift
    raw_coal_ash, raw_coal_moisture, raw_coal_tonnage
    # Size fractions:
    large_particle_yield, medium_particle_yield, fine_particle_yield
    # Products:
    coking1_yield, coking2_yield, coking3_yield
    thermal_yield, reject1_yield, reject2_yield, reject3_yield
    ash_variance, yield_variance
```

### 3.3 Washability

```python
class WashabilityTest(Base):
    __tablename__ = "washability_tests"
    id, lab_number (unique), sample_name, sample_date
    client_name, seam_id
    # Raw coal analysis:
    tm, im, ash, vol, fc, sulfur, csn, g_index, trd, ard
    # Relationships: fractions, theoretical_yields, plant_yields

class WashabilityFraction(Base):
    __tablename__ = "washability_fractions"
    id, test_id, size_fraction (e.g., "-50+16mm")
    density_sink, density_float
    mass_gram, yield_percent
    ash_ad, vm_ad, fc_ad, csn, g_index
    cumulative_yield, cumulative_ash, cumulative_combustible

class TheoreticalYield(Base):
    __tablename__ = "theoretical_yields"
    id, test_id, target_ash
    theoretical_yield, separation_density
    ngm_plus_01, ngm_minus_01  # Near Gravity Material
    washability_index  # Classification

class PlantYield(Base):
    __tablename__ = "plant_yields"
    id, test_id, production_date, shift, product_type
    feed_tonnes, product_tonnes
    actual_yield, theoretical_yield, recovery_efficiency
    feed_ash, product_ash

class CompositeProduct(Base):
    __tablename__ = "composite_products"
    id, test_id, product_type (HCC, SSCC, Middlings, Reject)
    initial_mass, inherent_moisture
    ash_ad, vol_ad, fc_ad, sulfur_ad, phosphorus
    csn, g_index, trd, ard, cv
    yield_percent, recovery_percent
```

### 3.4 Optimization

```python
class MasterSeam(Base):
    __tablename__ = "master_seams"
    id, seam_code (0AL, 0AU, 0BL, 0CL, etc.)
    description
    # Typical quality:
    typical_ash, typical_moisture, typical_volatile
    typical_sulfur, typical_csn, typical_yield
    mining_cost_per_ton
    status (ACTIVE, DEPLETED, RESERVED, MAINTENANCE)

class MineStockpile(Base):
    __tablename__ = "mine_stockpiles"
    id, seam_id, available_tonnage
    min_tonnage, max_tonnage
    current_ash, current_moisture, current_sulfur
    stockpile_name, location
    last_updated, updated_by

class OptimizationScenario(Base):
    __tablename__ = "optimization_scenarios"
    id, name, description, creation_date
    target_ash, target_yield
    feed_blend (JSON)  # Seam proportions
    calculated_quality, cost_per_ton

class FeedBlend(Base):
    __tablename__ = "feed_blends"
    id, scenario_id, seam_id, proportion_percent
```

### 3.5 CHPP & SCADA

```python
class CHPPEquipment(Base):
    __tablename__ = "chpp_equipment"
    id, tag (SC401, SC404, etc.)
    equipment_type, module, name, description
    is_active

class ScadaTag(Base):
    __tablename__ = "scada_tags"
    id, tag_name, tag_description
    module, equipment_tag
    data_type, unit
    min_value, max_value  # Alarm thresholds
    is_active

class ScadaReading(Base):
    __tablename__ = "scada_readings"  # TimescaleDB hypertable
    id, scada_tag_id, reading_value
    reading_timestamp, quality_status
    source (OPC_UA, MANUAL)
```

---

## 4. Frontend Бүтэц (D:\icpms\frontend)

### 4.1 Файлын бүтэц

```
frontend/
├── public/
├── src/
│   ├── main.tsx              # Entry point
│   ├── App.tsx               # Routes
│   ├── index.css             # TailwindCSS
│   ├── pages/                # Route components
│   │   ├── Login.tsx
│   │   ├── Dashboard.tsx
│   │   ├── ModuleProcess.tsx
│   │   ├── ModuleStructure.tsx
│   │   ├── Washability.tsx
│   │   ├── WashabilityYield.tsx
│   │   ├── BlendOptimizer.tsx
│   │   ├── CoalBlending.tsx
│   │   ├── PretreatmentAnalysis.tsx
│   │   ├── SeamManagement.tsx
│   │   ├── CHPPSamples.tsx
│   │   ├── ScadaMonitor.tsx
│   │   ├── Equipment.tsx
│   │   ├── Downtime.tsx
│   │   ├── YieldCalculator.tsx
│   │   ├── DailyReport.tsx
│   │   └── Users.tsx
│   ├── components/
│   │   ├── Layout.tsx        # Sidebar + nav
│   │   ├── ProtectedRoute.tsx
│   │   ├── NGMWidget.tsx
│   │   ├── ProcessFlowDiagram.tsx
│   │   └── washability/
│   │       ├── TestList.tsx
│   │       ├── AnalysisTab.tsx
│   │       ├── YieldTab.tsx
│   │       └── ImportModal.tsx
│   ├── contexts/
│   │   └── AuthContext.tsx   # Global auth state
│   └── services/
│       └── api.ts            # Axios + API methods
├── package.json
├── vite.config.ts
├── tailwind.config.js
└── tsconfig.json
```

### 4.2 Route Map

```
/ (Protected)
├── /                    → Dashboard
├── /modules             → ModuleProcess
├── /module-structure    → ModuleStructure
├── /yield               → YieldCalculator
├── /washability         → Washability
├── /optimizer           → BlendOptimizer
├── /blending            → CoalBlending
├── /pretreatment        → PretreatmentAnalysis
├── /seams               → SeamManagement
├── /samples             → CHPPSamples
├── /scada               → ScadaMonitor
├── /equipment           → Equipment
├── /downtime            → Downtime
├── /daily-report        → DailyReport
└── /users               → Users (admin only)

Public
└── /login               → Login
```

### 4.3 Tech Stack

| Package | Version | Зорилго |
|---------|---------|---------|
| react | 18.3.1 | UI framework |
| typescript | 5.4 | Type safety |
| vite | 5.4 | Build tool |
| react-router-dom | 6.28 | Routing |
| axios | 1.7 | HTTP client |
| tailwindcss | 3.4 | Styling |
| recharts | 3.6 | Charts |
| highcharts | 11.4 | Advanced charts |
| lucide-react | 0.400 | Icons |
| date-fns | 3.6 | Date utilities |

---

## 5. Тохиргоо

### 5.1 Backend Config (app/core/config.py)

```python
class Settings(BaseSettings):
    APP_NAME: str = "ICPMS"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://..."

    # JWT
    SECRET_KEY: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # CORS
    CORS_ORIGINS: List[str] = ["http://localhost:5173"]

    # LIMS Integration
    LIMS_API_URL: str = "http://localhost:5000/api"
    LIMS_API_KEY: str

    # OPC UA
    OPC_UA_URL: str = "opc.tcp://localhost:4840"
```

### 5.2 Frontend Config (vite.config.ts)

```typescript
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:8001',  // Backend
        changeOrigin: true,
      },
    },
  },
})
```

---

## 6. Business Logic

### 6.1 Washability Testing Workflow

```
WashabilityTest
├── WashabilityFraction[] (density ranges)
│   ├── Calculate cumulative yield/ash
│   └── Determine separation density
├── TheoreticalYield (at target ash)
│   ├── NGM (Near Gravity Material %)
│   ├── NGMI index
│   └── Washability classification
└── PlantYield (actual production)
    └── Organic Efficiency = Actual / Theoretical × 100%
```

### 6.2 NGM Classification

| NGM % | Ангилал |
|-------|---------|
| 0-7% | Simple |
| 7-10% | Moderate |
| 10-15% | Difficult |
| 15-20% | Very Difficult |
| 20-25% | Exceedingly Difficult |
| 25%+ | Formidable |

### 6.3 Module Yield Calculation

```
Module (I/II/III)
├── 19 Sampling Points
│   └── ProcessSample (proximate, ultimate, coking)
└── ModuleYieldCalculation
    ├── Large fraction: HMC → Coking1/Thermal/Reject1
    ├── Medium fraction: Spiral/TBS → Coking2/Reject2
    └── Fine fraction: Flotation → Coking3/Reject3
```

### 6.4 Blend Optimization

```
Input:
- MasterSeam[] (0AL, 0AU, 0BL...)
- MineStockpile[] (inventory, quality)
- Target (ash %, yield %)

Algorithm:
1. Load washability data per seam
2. Linear blending quality estimation
3. Constraint satisfaction
4. Cost minimization OR yield maximization

Output:
- OptimizationScenario with FeedBlend[]
```

---

## 7. Засагдсан асуудлууд (2026-02-06)

### 7.1 Login Internal Server Error

**Шалтгаан:** `datetime.now(timezone.utc)` (offset-aware) vs PostgreSQL `TIMESTAMP WITHOUT TIME ZONE` (offset-naive)

**Засвар:** `auth.py` файлд `datetime.utcnow()` болгож солисон

```python
# ХУУЧИН (алдаатай):
user.last_login = datetime.now(timezone.utc)

# ШИНЭ (засагдсан):
user.last_login = datetime.utcnow()
```

### 7.2 Rate Limiter давхардал

**Шалтгаан:** `auth.py` дээр тусдаа `Limiter` instance үүсгэсэн нь `main.py`-ын limiter-тэй зөрчилдсөн

**Засвар:** `auth.py` дээрх limiter decorator устгасан

---

## 8. Ашигтай файлын замууд

| Зорилго | Зам |
|---------|-----|
| FastAPI App | `D:\icpms\backend\app\main.py` |
| Database Config | `D:\icpms\backend\app\core\database.py` |
| Settings | `D:\icpms\backend\app\core\config.py` |
| Security | `D:\icpms\backend\app\core\security.py` |
| User Model | `D:\icpms\backend\app\models\user.py` |
| Auth Routes | `D:\icpms\backend\app\api\auth.py` |
| Module Process | `D:\icpms\backend\app\api\module_process.py` |
| Washability API | `D:\icpms\backend\app\api\washability\__init__.py` |
| Washability Services | `D:\icpms\backend\app\services\washability\` |
| LIMS Service | `D:\icpms\backend\app\services\lims_service.py` |
| Frontend App | `D:\icpms\frontend\src\App.tsx` |
| API Service | `D:\icpms\frontend\src\services\api.ts` |
| Auth Context | `D:\icpms\frontend\src\contexts\AuthContext.tsx` |
| Vite Config | `D:\icpms\frontend\vite.config.ts` |

---

## 9. Coal LIMS-тэй харьцуулалт

| Онцлог | Coal LIMS | ICPMS |
|--------|-----------|-------|
| Framework | Flask | FastAPI |
| DB Session | Sync SQLAlchemy | Async SQLAlchemy |
| Frontend | Jinja2 + AG-Grid | React + TypeScript |
| Auth | Flask-Login + Session | JWT tokens |
| API Format | `api_success/api_error` | Pydantic response_model |
| Зорилго | Лабораторийн удирдлага | Үйлдвэрийн удирдлага |

---

**Үүсгэсэн:** 2026-02-06
**Шинэчилсэн:** 2026-02-06
