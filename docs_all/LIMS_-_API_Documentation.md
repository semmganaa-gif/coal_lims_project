# LIMS - API Documentation

## Base URL

```
Production: https://lims.example.com/api
Development: http://localhost:5000/api
```

## Authentication

All API endpoints require authentication via session cookie (Flask-Login).

```bash
# Login to get session
curl -X POST http://localhost:5000/login \
  -d "username=chemist&password=secret" \
  -c cookies.txt

# Use session for API calls
curl http://localhost:5000/api/samples \
  -b cookies.txt
```

---

## Samples API

### List Samples

```http
GET /api/samples
```

**Query Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| page | int | Page number (default: 1) |
| per_page | int | Items per page (default: 50) |
| search | string | Search by sample code |
| client | string | Filter by client |
| status | string | Filter by status |
| from_date | string | Start date (YYYY-MM-DD) |
| to_date | string | End date (YYYY-MM-DD) |

**Response:**

```json
{
  "samples": [
    {
      "id": 1,
      "sample_code": "QC-2026-001",
      "client_name": "QC",
      "sample_type": "Нүүрс",
      "status": "active",
      "assigned_analyses": ["Aad", "Mad", "Vad"],
      "created_at": "2026-01-11T10:30:00"
    }
  ],
  "total": 150,
  "page": 1,
  "per_page": 50,
  "pages": 3
}
```

### Get Sample

```http
GET /api/samples/{id}
```

**Response:**

```json
{
  "id": 1,
  "sample_code": "QC-2026-001",
  "client_name": "QC",
  "sample_type": "Нүүрс",
  "status": "active",
  "assigned_analyses": ["Aad", "Mad", "Vad"],
  "weight": 25.5,
  "description": "Control sample",
  "created_at": "2026-01-11T10:30:00",
  "results": [
    {
      "analysis_code": "Aad",
      "final_result": 12.5,
      "status": "approved"
    }
  ]
}
```

### Create Sample

```http
POST /api/samples
Content-Type: application/json
```

**Request Body:**

```json
{
  "sample_code": "LAB-2026-001",
  "client_name": "CHPP",
  "sample_type": "Нүүрс",
  "description": "Optional description",
  "assigned_analyses": ["Aad", "Mad", "Vad", "CV"]
}
```

**Response:**

```json
{
  "success": true,
  "sample_id": 123,
  "message": "Дээж амжилттай бүртгэгдлээ"
}
```

### Update Sample Status

```http
PATCH /api/samples/{id}/status
Content-Type: application/json
```

**Request Body:**

```json
{
  "status": "disposed",
  "reason": "Retention period expired"
}
```

---

## Analysis API

### Get Eligible Samples

```http
GET /api/analysis/eligible_samples
```

**Query Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| analysis_code | string | Filter by analysis type |

**Response:**

```json
{
  "samples": [
    {
      "id": 1,
      "sample_code": "QC-2026-001",
      "assigned_analyses": ["Aad", "Mad"],
      "completed_analyses": ["Mad"]
    }
  ]
}
```

### Save Results

```http
POST /api/analysis/save_results
Content-Type: application/json
```

**Request Body:**

```json
{
  "sample_id": 1,
  "data": [
    {
      "analysis_code": "Aad",
      "raw_data": {
        "A": "2.5432",
        "B": "2.2156",
        "C": "0.3276"
      },
      "final_result": 12.52
    },
    {
      "analysis_code": "Mad",
      "raw_data": {
        "W1": "10.0",
        "W2": "9.65"
      },
      "final_result": 3.5
    }
  ]
}
```

**Response:**

```json
{
  "success": true,
  "results": [
    {
      "analysis_code": "Aad",
      "status": "approved",
      "final_result": 12.52
    },
    {
      "analysis_code": "Mad",
      "status": "approved",
      "final_result": 3.5
    }
  ]
}
```

### Request Analysis

```http
POST /api/analysis/request
Content-Type: application/json
```

**Request Body:**

```json
{
  "sample_id": 1,
  "analyses": ["Aad", "Mad", "Vad"]
}
```

### Unassign Analysis

```http
POST /api/analysis/unassign
Content-Type: application/json
```

**Request Body:**

```json
{
  "sample_id": 1,
  "analyses": ["Vad"]
}
```

### Update Result Status

```http
POST /api/analysis/update_status
Content-Type: application/json
```

**Request Body:**

```json
{
  "result_id": 123,
  "status": "approved",
  "comment": "Manual approval after review"
}
```

---

## Reports API

### Generate Report

```http
GET /api/reports/generate
```

**Query Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| sample_ids | string | Comma-separated sample IDs |
| format | string | pdf, excel, html |
| template | string | Report template name |

**Response:** Binary file download

### Export Data

```http
GET /api/reports/export
```

**Query Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| from_date | string | Start date |
| to_date | string | End date |
| format | string | excel, csv |
| analyses | string | Analysis codes to include |

---

## QC API

### Get Control Chart Data

```http
GET /api/qc/control_chart
```

**Query Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| analysis_code | string | Analysis type |
| material | string | CM, GBW |
| days | int | Number of days (default: 30) |

**Response:**

```json
{
  "analysis_code": "Aad",
  "material": "CM",
  "target": 12.5,
  "std_dev": 0.15,
  "data": [
    {
      "date": "2026-01-10",
      "value": 12.48,
      "status": "pass"
    }
  ],
  "limits": {
    "ucl": 12.95,
    "lcl": 12.05,
    "uwl": 12.80,
    "lwl": 12.20
  }
}
```

### Westgard Check

```http
POST /api/qc/westgard_check
Content-Type: application/json
```

**Request Body:**

```json
{
  "analysis_code": "Aad",
  "values": [12.5, 12.3, 12.7, 12.4, 12.6]
}
```

**Response:**

```json
{
  "passed": true,
  "rules_checked": ["1_2s", "1_3s", "2_2s", "R_4s", "4_1s", "10x"],
  "violations": []
}
```

---

## Admin API

### List Users

```http
GET /api/admin/users
```

**Response:**

```json
{
  "users": [
    {
      "id": 1,
      "username": "admin",
      "role": "admin",
      "last_login": "2026-01-11T09:00:00",
      "is_active": true
    }
  ]
}
```

### Create User

```http
POST /api/admin/users
Content-Type: application/json
```

**Request Body:**

```json
{
  "username": "newchemist",
  "password": "SecurePass123!",
  "role": "chemist"
}
```

### Audit Log

```http
GET /api/admin/audit_log
```

**Query Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| user_id | int | Filter by user |
| action | string | Filter by action type |
| from_date | string | Start date |
| to_date | string | End date |

---

## Equipment API

### List Equipment

```http
GET /api/equipment
```

### Get Equipment

```http
GET /api/equipment/{id}
```

### Create Equipment

```http
POST /api/equipment
Content-Type: application/json
```

### Update Calibration

```http
POST /api/equipment/{id}/calibration
Content-Type: application/json
```

---

## Water Lab API

Water quality analysis endpoints. URL prefix: `/labs/water`

### Water Samples List

```http
GET /labs/water/api/data
```

**Response:**

```json
{
  "samples": [
    {
      "id": 1,
      "sample_code": "WTR-2026-001",
      "source": "Intake",
      "status": "active",
      "created_at": "2026-01-15T08:00:00"
    }
  ],
  "total": 42
}
```

### Eligible Samples for Analysis

```http
GET /labs/water/api/eligible/{code}
```

**Response:**

```json
{
  "samples": [
    {
      "id": 1,
      "sample_code": "WTR-2026-001",
      "assigned_analyses": ["pH", "TDS", "Hardness"]
    }
  ]
}
```

### Save Water Analysis Results

```http
POST /labs/water/api/save_results
Content-Type: application/json
```

**Request Body:**

```json
{
  "sample_id": 1,
  "data": [
    {
      "analysis_code": "pH",
      "final_result": 7.2
    },
    {
      "analysis_code": "TDS",
      "final_result": 320.5
    }
  ]
}
```

**Response:**

```json
{
  "success": true,
  "message": "Үр дүн хадгалагдлаа"
}
```

### MNS/WHO Standards

```http
GET /labs/water/api/standards
```

**Response:**

```json
{
  "standards": [
    {
      "parameter": "pH",
      "mns_min": 6.5,
      "mns_max": 8.5,
      "who_min": 6.5,
      "who_max": 8.5
    },
    {
      "parameter": "TDS",
      "mns_max": 1000,
      "who_max": 600
    }
  ]
}
```

---

## Microbiology Lab API

Microbiology analysis endpoints for water, air, and swab samples. URL prefix: `/labs/microbiology`

### Samples by Category

```http
GET /labs/microbiology/api/samples?category=MICRO_WATER|MICRO_AIR|MICRO_SWAB
```

**Query Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| category | string | MICRO_WATER, MICRO_AIR, or MICRO_SWAB |

**Response:**

```json
{
  "samples": [
    {
      "id": 1,
      "sample_code": "MIC-2026-001",
      "category": "MICRO_WATER",
      "status": "active"
    }
  ]
}
```

### Micro Samples List

```http
GET /labs/microbiology/api/data
```

**Response:**

```json
{
  "samples": [
    {
      "id": 1,
      "sample_code": "MIC-2026-001",
      "category": "MICRO_WATER",
      "status": "active",
      "created_at": "2026-01-20T09:00:00"
    }
  ],
  "total": 28
}
```

### Save Single Result

```http
POST /labs/microbiology/api/save_results
Content-Type: application/json
```

**Request Body:**

```json
{
  "sample_id": 1,
  "data": {
    "analysis_code": "coliform",
    "final_result": 0,
    "unit": "CFU/mL"
  }
}
```

**Response:**

```json
{
  "success": true,
  "message": "Үр дүн хадгалагдлаа"
}
```

### Save Batch Results

```http
POST /labs/microbiology/api/save_batch
Content-Type: application/json
```

**Request Body:**

```json
{
  "results": [
    {
      "sample_id": 1,
      "analysis_code": "coliform",
      "final_result": 0
    },
    {
      "sample_id": 2,
      "analysis_code": "coliform",
      "final_result": 2
    }
  ]
}
```

**Response:**

```json
{
  "success": true,
  "saved_count": 2
}
```

### Load Saved Batch

```http
GET /labs/microbiology/api/load_batch
```

**Response:**

```json
{
  "batch": [
    {
      "sample_id": 1,
      "sample_code": "MIC-2026-001",
      "analysis_code": "coliform",
      "final_result": 0,
      "saved_at": "2026-01-20T10:30:00"
    }
  ]
}
```

---

## Petrography Lab API

Petrographic (PE) analysis endpoints. URL prefix: `/labs/petrography`

### PE Samples List

```http
GET /labs/petrography/api/data
```

**Response:**

```json
{
  "samples": [
    {
      "id": 1,
      "sample_code": "PE-2026-001",
      "status": "active",
      "created_at": "2026-01-18T11:00:00"
    }
  ],
  "total": 15
}
```

### Eligible PE Samples

```http
GET /labs/petrography/api/eligible/{code}
```

**Response:**

```json
{
  "samples": [
    {
      "id": 1,
      "sample_code": "PE-2026-001",
      "assigned_analyses": ["vitrinite", "maceral"]
    }
  ]
}
```

### Save PE Results

```http
POST /labs/petrography/api/save_results
Content-Type: application/json
```

**Request Body:**

```json
{
  "sample_id": 1,
  "data": [
    {
      "analysis_code": "vitrinite",
      "final_result": 0.85
    },
    {
      "analysis_code": "maceral",
      "raw_data": {
        "vitrinite_pct": 65.2,
        "inertinite_pct": 28.1,
        "liptinite_pct": 6.7
      },
      "final_result": null
    }
  ]
}
```

**Response:**

```json
{
  "success": true,
  "message": "Үр дүн хадгалагдлаа"
}
```

---

## Error Responses

All errors follow this format:

```json
{
  "error": true,
  "code": "VALIDATION_ERROR",
  "message": "Утга буруу байна",
  "details": {
    "field": "sample_code",
    "reason": "Давхардсан код"
  }
}
```

### Error Codes

| Code | HTTP Status | Description |
|------|-------------|-------------|
| VALIDATION_ERROR | 400 | Invalid input data |
| UNAUTHORIZED | 401 | Not logged in |
| FORBIDDEN | 403 | Insufficient permissions |
| NOT_FOUND | 404 | Resource not found |
| RATE_LIMITED | 429 | Too many requests |
| SERVER_ERROR | 500 | Internal server error |

---

## Rate Limits

| Endpoint | Limit |
|----------|-------|
| Default | 500/hour |
| /api/analysis/save_results | 1000/hour |
| /api/reports/generate | 100/hour |

---

## Webhooks (Future)

```http
POST /api/webhooks/register
Content-Type: application/json
```

```json
{
  "url": "https://your-server.com/webhook",
  "events": ["sample.created", "result.approved", "qc.failed"]
}
```
