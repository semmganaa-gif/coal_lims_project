# LIMS - System Architecture

## Overview

LIMS нь лабораторийн мэдээллийн удирдлагын систем бөгөөд 4 лабораторийн модулийг (Coal, Water, Microbiology, Petrography) дэмжих ISO 17025 стандартын дагуу хөгжүүлэгдсэн.

## Multi-Lab Architecture

```mermaid
graph TB
    subgraph "Lab Modules"
        Coal[Coal Lab<br/>18 analyses<br/>bi-fire]
        Water[Water Lab<br/>32 parameters<br/>bi-droplet]
        Micro[Microbiology Lab<br/>8 codes<br/>bi-bug]
        Petro[Petrography Lab<br/>7 codes<br/>bi-gem]
    end

    subgraph "Core Framework"
        BaseLab[BaseLab Abstract Class]
        Registry[Lab Registry]
        Auth[allowed_labs Access Control]
    end

    subgraph "Shared Infrastructure"
        Models[SQLAlchemy Models]
        QC[QC Engine / Westgard]
        Reports[Report Generator]
    end

    Coal --> BaseLab
    Water --> BaseLab
    Micro --> BaseLab
    Petro --> BaseLab
    BaseLab --> Registry
    Registry --> Auth
    Auth --> Models
    Auth --> QC
    Auth --> Reports
```

### BaseLab Pattern

Бүх лабораторийн модулиуд `BaseLab` абстракт класс-аас удамшина. Энэ нь дараах гол атрибут, методуудыг тодорхойлно:

- **key** — лабын дотоод нэр (жнь: `"coal"`, `"water"`)
- **name** — хэрэглэгчид харагдах нэр
- **icon** — Bootstrap icon class
- **color** — UI өнгө
- **analysis_codes** — тухайн лабын шинжилгээний кодуудын жагсаалт
- **get_blueprint()** — Flask Blueprint буцаана
- **sample_query()** — тухайн лабын дээжийн query буцаана
- **sample_stats()** — тухайн лабын статистик мэдээлэл буцаана

### allowed_labs Access Control

Хэрэглэгч бүрийн `allowed_labs` талбар нь тухайн хэрэглэгчийн хандах боломжтой лабуудыг тодорхойлно. Админ хэрэглэгч бүрт лабын эрхийг тусад нь тохируулж өгнө. Зөвшөөрөгдөөгүй лабын route, API-д хандахыг хориглоно.

## High-Level Architecture

```mermaid
graph TB
    subgraph "Client Layer"
        Browser[Web Browser]
        Mobile[Mobile Device]
    end

    subgraph "Load Balancer"
        Nginx[Nginx Reverse Proxy]
    end

    subgraph "Application Layer"
        Flask1[Flask App 1]
        Flask2[Flask App 2]
        Flask3[Flask App N]
        SocketIO[WebSocket Server]
    end

    subgraph "Cache Layer"
        Redis[(Redis Cache)]
    end

    subgraph "Data Layer"
        PostgreSQL[(PostgreSQL DB)]
    end

    subgraph "Monitoring"
        Prometheus[Prometheus]
        Grafana[Grafana]
        Loki[Loki Logs]
        Sentry[Sentry]
    end

    Browser --> Nginx
    Mobile --> Nginx
    Nginx --> Flask1
    Nginx --> Flask2
    Nginx --> Flask3
    Nginx --> SocketIO
    Flask1 --> Redis
    Flask2 --> Redis
    Flask3 --> Redis
    Flask1 --> PostgreSQL
    Flask2 --> PostgreSQL
    Flask3 --> PostgreSQL
    Flask1 --> Prometheus
    Flask1 --> Sentry
    Prometheus --> Grafana
    Flask1 --> Loki
```

## Component Architecture

```mermaid
graph LR
    subgraph "Flask Application"
        subgraph "Routes Layer"
            Main[Main Routes]
            Analysis[Analysis Routes]
            API[API Routes]
            Admin[Admin Routes]
            Reports[Report Routes]
            Quality[Quality Routes]
        end

        subgraph "Service Layer"
            SampleSvc[Sample Service]
            AnalysisSvc[Analysis Service]
            QCSvc[QC Service]
        end

        subgraph "Repository Layer"
            SampleRepo[Sample Repository]
            ResultRepo[Result Repository]
        end

        subgraph "Utils"
            Validators[Validators]
            Conversions[Conversions]
            Normalize[Normalize]
            Westgard[Westgard Rules]
        end
    end

    Main --> SampleSvc
    Analysis --> AnalysisSvc
    Quality --> QCSvc
    SampleSvc --> SampleRepo
    AnalysisSvc --> ResultRepo
    AnalysisSvc --> Validators
    AnalysisSvc --> Conversions
    QCSvc --> Westgard
```

## Data Flow

```mermaid
sequenceDiagram
    participant U as User
    participant F as Flask App
    participant R as Redis
    participant DB as PostgreSQL
    participant Q as QC Engine

    U->>F: Submit Analysis Result
    F->>DB: Get Sample Info
    DB-->>F: Sample Data
    F->>F: Normalize & Validate
    F->>Q: Check QC Rules
    Q-->>F: QC Status
    F->>DB: Save Result
    DB-->>F: Saved
    F->>R: Invalidate Cache
    F-->>U: Success Response
```

## Database Schema (Core Tables)

```mermaid
erDiagram
    USER ||--o{ SAMPLE : creates
    USER ||--o{ ANALYSIS_RESULT : performs
    SAMPLE ||--o{ ANALYSIS_RESULT : has
    SAMPLE }o--|| CLIENT : belongs_to
    ANALYSIS_RESULT ||--o{ ANALYSIS_RESULT_LOG : logs

    USER {
        int id PK
        string username
        string password_hash
        string role
        datetime created_at
    }

    SAMPLE {
        int id PK
        string sample_code UK
        int user_id FK
        string client_name
        string sample_type
        json assigned_analyses
        string status
        datetime created_at
    }

    ANALYSIS_RESULT {
        int id PK
        int sample_id FK
        int user_id FK
        string analysis_code
        json raw_data
        float final_result
        string status
        datetime created_at
    }

    ANALYSIS_RESULT_LOG {
        int id PK
        int sample_id FK
        string analysis_code
        json raw_data
        float final_result
        string action
        datetime timestamp
    }
```

## Module Structure

```
app/
├── __init__.py              # Application factory
├── models.py                # SQLAlchemy models
├── constants.py             # Analysis aliases, constants
├── monitoring.py            # Prometheus metrics
├── sentry_integration.py    # Error tracking
│
├── labs/                    # Multi-lab modules
│   ├── __init__.py          # Lab registry, LAB_TYPES
│   ├── base.py              # BaseLab abstract class
│   ├── coal/                # Coal lab (18 analyses)
│   ├── water/               # Water lab (32 parameters)
│   ├── microbiology/        # Microbiology lab (8 codes)
│   └── petrography/         # Petrography lab (7 codes)
│
├── routes/                  # Core + Coal routes
│   ├── main/               # Main pages (index, login)
│   ├── analysis/           # Analysis workspace
│   ├── api/                # REST API endpoints
│   ├── admin_routes.py     # Admin panel
│   ├── report_routes.py    # Report generation
│   ├── quality/            # QC management
│   └── equipment_routes.py # Equipment tracking
│
├── services/               # Business logic
│   ├── sample_service.py
│   └── analysis_audit.py
│
├── repositories/           # Data access
│   ├── sample_repository.py
│   └── analysis_result_repository.py
│
├── utils/                  # Utilities
│   ├── validators.py       # Input validation
│   ├── conversions.py      # Unit conversions
│   ├── normalize.py        # Data normalization
│   ├── westgard.py         # Westgard QC rules
│   ├── qc.py              # QC checks
│   └── server_calculations.py  # Analysis formulas
│
├── templates/              # Jinja2 templates
│   ├── base.html
│   ├── index.html
│   └── ...
│
└── static/                 # Static assets
    ├── css/
    ├── js/
    └── images/
```

## Technology Stack

| Layer | Technology |
|-------|------------|
| Frontend | HTML5, CSS3, JavaScript, Alpine.js, htmx, AG Grid |
| Backend | Python 3.11, Flask 3.x |
| Database | PostgreSQL 15 |
| Cache | Redis 7 |
| Web Server | Gunicorn + Nginx |
| Containerization | Docker, Docker Compose |
| Monitoring | Prometheus, Grafana, Loki, Sentry |
| Testing | pytest, Playwright, k6 |

## Security Architecture

```mermaid
graph TB
    subgraph "Security Layers"
        HTTPS[HTTPS/TLS]
        CSRF[CSRF Protection]
        RateLimit[Rate Limiting]
        Auth[Flask-Login Auth]
        RBAC[Role-Based Access]
        License[License Protection]
    end

    Request[Incoming Request]
    Request --> HTTPS
    HTTPS --> RateLimit
    RateLimit --> CSRF
    CSRF --> Auth
    Auth --> RBAC
    RBAC --> License
    License --> App[Application]
```

## Deployment Architecture

```mermaid
graph TB
    subgraph "Production"
        LB[Load Balancer]

        subgraph "App Servers"
            App1[Web Server 1]
            App2[Web Server 2]
        end

        subgraph "Data"
            DB[(PostgreSQL Primary)]
            DBR[(PostgreSQL Replica)]
            Redis[(Redis)]
        end

        subgraph "Monitoring"
            Mon[Prometheus + Grafana]
        end
    end

    Internet[Internet] --> LB
    LB --> App1
    LB --> App2
    App1 --> DB
    App2 --> DB
    DB --> DBR
    App1 --> Redis
    App2 --> Redis
    App1 --> Mon
    App2 --> Mon
```

## Analysis Workflow

```mermaid
stateDiagram-v2
    [*] --> Registered: Sample Created
    Registered --> Assigned: Analyses Assigned
    Assigned --> InProgress: Chemist Starts
    InProgress --> Pending: Result Entered
    Pending --> Approved: Auto/Manual Approve
    Pending --> Rejected: QC Failed
    Rejected --> InProgress: Re-analyze
    Approved --> Reported: Generate Report
    Reported --> [*]
```

## QC Decision Flow

```mermaid
flowchart TD
    A[Result Entered] --> B{Repeatability Check}
    B -->|Pass| C{Control Material?}
    B -->|Fail| R[Rejected]
    C -->|Yes| D{Within Limits?}
    C -->|No| E[Auto Approved]
    D -->|Yes| E
    D -->|No| F{Westgard Rules}
    F -->|Pass| G[Pending Review]
    F -->|Fail| R
    G --> H{Senior Review}
    H -->|Approve| E
    H -->|Reject| R
```
