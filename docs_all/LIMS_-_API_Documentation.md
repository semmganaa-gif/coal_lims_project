# Coal LIMS - API Documentation

**Last Updated:** 2026-02-15
**Version:** 2.0

---

## Table of Contents

1. [Base URL](#base-url)
2. [Authentication](#authentication)
3. [Standard Response Format](#standard-response-format)
4. [Rate Limits](#rate-limits)
5. [Samples API](#samples-api)
6. [Analysis API](#analysis-api)
7. [Mass Workspace API](#mass-workspace-api)
8. [Senior Review API](#senior-review-api)
9. [Audit API](#audit-api)
10. [Equipment API](#equipment-api)
11. [Spare Parts API](#spare-parts-api)
12. [Chemicals API](#chemicals-api)
13. [Quality Management API](#quality-management-api)
14. [Chat API](#chat-api)
15. [Morning Dashboard API](#morning-dashboard-api)
16. [Simulator API](#simulator-api)
17. [Export API](#export-api)
18. [HTMX Endpoints](#htmx-endpoints)
19. [Error Codes](#error-codes)

---

## Base URL

```
Production: https://lims.example.com
Development: http://localhost:5000
```

All API endpoints are prefixed with their respective blueprint URL prefix (e.g., `/api`, `/equipment`, `/chemicals`, `/quality`, `/analysis`).

---

## Authentication

All API endpoints require authentication via Flask-Login session cookie. There is no token-based authentication.

```bash
# Login to get session
curl -X POST http://localhost:5000/login \
  -d "username=chemist&password=secret" \
  -c cookies.txt

# Use session for API calls
curl http://localhost:5000/api/data \
  -b cookies.txt
```

### Roles

| Role | Description |
|------|-------------|
| `admin` | Full access to all endpoints |
| `senior` | Senior analyst - can approve/reject results, manage analyses |
| `chemist` | Lab chemist - can save analysis results |
| `prep` | Sample preparation - can manage mass workspace |

### Login Rate Limit

Login is rate-limited to **5 requests per minute** to prevent brute-force attacks.

---

## Standard Response Format

All new API endpoints use the standardized response format:

**Success:**

```json
{
  "success": true,
  "data": { ... },
  "message": "Operation completed successfully"
}
```

**Error:**

```json
{
  "success": false,
  "error": "Error description",
  "code": "VALIDATION_ERROR",
  "details": { ... }
}
```

Helper functions: `api_success(data, message)` and `api_error(message, code, status_code, details)` defined in `app/routes/api/helpers.py`.

> **Note:** Some legacy endpoints still use `{"message": ...}` or flat JSON responses. These are being migrated to the standard format.

---

## Rate Limits

| Endpoint Group | Limit |
|----------------|-------|
| `/api/data` (DataTables) | 100/minute |
| `/api/save_results` | 100/minute |
| `/api/eligible_samples/*` | 100/minute |
| `/api/sample_summary` | 100/minute |
| `/api/mass/*` | 100/minute |
| `/login` | 5/minute |
| Default (unspecified) | No explicit limit |

Rate limiting is enforced via `flask-limiter`. Exceeding the limit returns HTTP 429.

---

## Samples API

Blueprint: `api` | URL Prefix: `/api`

### GET /api/data

DataTables server-side data provider for the coal sample listing page.

**Auth:** `login_required`

**Query Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| draw | int | DataTables draw counter |
| start | int | Offset (default: 0) |
| length | int | Rows per page (default: 25, max: 1000) |
| dateFilterStart | string | Start date filter (ISO format) |
| dateFilterEnd | string | End date filter (ISO format) |
| columns[N][search][value] | string | Per-column search (N = column index) |

**Column Index Mapping:**

| Index | Field |
|-------|-------|
| 1 | id (exact match) |
| 2 | sample_code (LIKE) |
| 3 | client_name (LIKE) |
| 4 | sample_type (LIKE) |
| 5 | sample_condition (LIKE) |
| 6 | delivered_by (LIKE) |
| 7 | prepared_by (LIKE) |
| 9 | notes (LIKE) |
| 11 | weight (exact match) |
| 13 | analyses_to_perform (LIKE) |

**Response:**

```json
{
  "draw": 1,
  "recordsTotal": 150,
  "recordsFiltered": 150,
  "data": [
    [
      "<input type='checkbox' ...>",
      1,
      "QC-2026-001",
      "CHPP",
      "2 hourly",
      "Dry",
      "John",
      "Jane",
      "2026-01-15",
      "notes...",
      "2026-01-15 10:30",
      25.5,
      "approved",
      "[\"Aad\",\"Mad\",\"Vad\"]",
      "<span class='badge ...'>30 days</span>",
      "<a href='...' class='btn ...'>Edit</a>"
    ]
  ]
}
```

---

### GET /api/sample_summary

Renders the sample summary page with analysis results. Also supports archive/unarchive via POST.

**Auth:** `login_required`

**POST Parameters (form):**

| Parameter | Type | Description |
|-----------|------|-------------|
| action | string | `archive` or `unarchive` |
| sample_ids | string | Comma-separated sample IDs |

**Response:** Renders HTML template `sample_summary.html`

---

### GET /api/sample_report/{sample_id}

Generates a sample report page.

**Auth:** `login_required`

**URL Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| sample_id | int | Sample ID |

**Response:** Renders HTML template `report.html`

---

### GET /api/sample_history/{sample_id}

Shows the full history (analysis results + audit logs) for a sample.

**Auth:** `login_required`

**URL Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| sample_id | int | Sample ID |

**Response:** Renders HTML template `sample_history.html`

---

### GET /api/archive_hub

Archive hub page with tree structure (Client -> Type -> Year -> Month).

**Auth:** `login_required`

**Query Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| client | string | Filter by client name |
| type | string | Filter by sample type |
| year | int | Filter by year |
| month | int | Filter by month |

**POST:** Supports `unarchive` action for restoring samples from the archive.

**Response:** Renders HTML template `archive_hub.html`

---

### GET /api/dashboard_stats

Dashboard statistics for Chart.js visualizations (coal lab only).

**Auth:** `login_required`

**Response:**

```json
{
  "samples_by_day": [
    { "date": "02/09", "day_name": "Mon", "count": 12 }
  ],
  "samples_by_client": [
    { "client": "CHPP", "count": 45 }
  ],
  "analysis_by_status": [
    { "status": "approved", "count": 120 }
  ],
  "approval_stats": {
    "approved": 450,
    "rejected": 12,
    "pending": 35
  },
  "today": {
    "samples": 8,
    "analyses": 42,
    "pending_review": 5
  }
}
```

---

### GET /api/sample_analysis_results/{sample_id}

Returns all analysis results for a sample as JSON (used in complaints).

**Auth:** `login_required`

**Response:**

```json
{
  "success": true,
  "data": [
    {
      "id": 1,
      "analysis_code": "Aad",
      "final_result": 12.5,
      "status": "approved",
      "user": "chemist1",
      "created_at": "2026-01-15 10:30"
    }
  ]
}
```

---

### GET /api/search_samples_json

JSON search for samples (autocomplete for complaints, registrations).

**Auth:** `login_required`

**Query Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| q | string | Search query (min 2 chars) |

**Response:**

```json
[
  {
    "id": 1,
    "sample_code": "QC-2026-001",
    "client_name": "CHPP",
    "lab_type": "coal",
    "status": "new"
  }
]
```

---

## Analysis API

Blueprint: `api` | URL Prefix: `/api`

### GET /api/eligible_samples/{analysis_code}

Returns samples eligible for a specific analysis, plus rejected samples awaiting re-analysis.

**Auth:** `login_required`

**URL Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| analysis_code | string | Analysis code (e.g., `Aad`, `Mad`, `CV`) |

**Response:**

```json
{
  "samples": [
    {
      "id": 1,
      "sample_code": "QC-2026-001",
      "name": "",
      "client_name": "CHPP",
      "sample_type": "2 hourly",
      "received_date": "2026-01-15 10:30"
    }
  ],
  "rejected": [
    {
      "id": 1,
      "result_id": 42,
      "sample_code": "QC-2026-001",
      "client_name": "CHPP",
      "sample_type": "2 hourly",
      "error_reason": "Tolerance exceeded",
      "updated_at": "2026-01-15 11:00"
    }
  ],
  "rejected_count": 1
}
```

**Notes:**
- Coal lab samples only (`lab_type == 'coal'`)
- Filters by sample status `new`/`New`
- Excludes samples that already have results for the specified analysis code
- Mass gate applies (requires `mass_ready == True` for most analyses, except X, Y, CRI, CSR)
- Chemists see only their own rejected samples; seniors/admins see all

---

### POST /api/save_results

Saves analysis results with server-side verification, tolerance checking, and QC standard validation (CM/GBW).

**Auth:** `login_required`

**Request Body (JSON array or single object):**

```json
[
  {
    "sample_id": 1,
    "analysis_code": "Aad",
    "final_result": 12.52,
    "raw_data": {
      "p1": { "A": "2.5432", "B": "2.2156", "result": "12.48" },
      "p2": { "A": "2.5433", "B": "2.2157", "result": "12.56" },
      "avg": "12.52",
      "diff": "0.08"
    },
    "equipment_id": 5,
    "rejection_comment": "Optional comment"
  }
]
```

**Response (HTTP 200 or 207 for partial success):**

```json
{
  "message": "2 rows saved successfully, 0 errors.",
  "results": [
    {
      "sample_id": 1,
      "analysis_code": "Aad",
      "status": "approved",
      "raw_data": { ... },
      "success": true,
      "reason": "Auto-approved (within tolerance)"
    }
  ],
  "errors": []
}
```

**Status Determination Logic:**
- `approved` - Result within tolerance, passes QC checks
- `pending_review` - Tolerance exceeded or Mad unavailable for CM/GBW dry basis conversion
- `rejected` - QC control failure (CM/GBW standard check failed)

**Server-Side Features:**
- Server-side recalculation verification
- Tolerance limit checking (band-based or single limit)
- CM/GBW dry basis conversion and standard validation
- Equipment existence check
- XSS protection on rejection_comment
- Audit trail with hash integrity (ISO 17025)
- Prometheus metrics tracking

---

### POST /api/unassign_sample

Removes an analysis assignment from a sample.

**Auth:** `login_required` | **Role:** `senior`, `admin`

**Request Body:**

```json
{
  "sample_id": 1,
  "analysis_code": "Aad"
}
```

**Response:**

```json
{
  "success": true,
  "message": "Unassigned Aad analysis from sample QC-2026-001",
  "remaining_analyses": ["Mad", "Vad"]
}
```

---

### POST /api/update_result_status/{result_id}/{new_status}

Approve, reject, or return results for review (senior/admin only).

**Auth:** `login_required` | **Role:** `senior`, `admin`

**URL Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| result_id | int | AnalysisResult ID |
| new_status | string | `approved`, `rejected`, or `pending_review` |

**Request Body (JSON or form):**

```json
{
  "rejection_comment": "Value looks incorrect",
  "rejection_category": "tolerance",
  "rejection_subcategory": "diff_exceeded",
  "error_reason": "tolerance",
  "action_type": "manual_review"
}
```

**Response:**

```json
{
  "message": "OK",
  "status": "approved"
}
```

---

### POST /api/request_analysis

Order a new analysis for a sample from the summary view (senior/admin only).

**Auth:** `login_required` | **Role:** `senior`, `admin`

**Request Body:**

```json
{
  "sample_id": 1,
  "analysis_code": "CV"
}
```

**Response:**

```json
{
  "message": "'CV' analysis ordered successfully",
  "sample_id": 1,
  "analysis_code": "CV"
}
```

---

### GET /api/check_ready_samples

Checks for CHPP samples that have completed required analyses and are ready for reporting.

**Auth:** `login_required`

**Response:**

```json
{
  "ready_count": 3,
  "samples": [
    {
      "sample_code": "CHPP-2H-001",
      "time": "10:30",
      "product": "ROM"
    }
  ],
  "timestamp": "14:30:00"
}
```

---

## Mass Workspace API

Blueprint: `api` | URL Prefix: `/api`

### POST /api/mass/update_sample_status

Archive or unarchive samples.

**Auth:** `login_required`

**Form Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| action | string | `archive` or `unarchive` |
| sample_ids | list | List of sample IDs |

**Response:**

```json
{
  "message": "5 sample status updated."
}
```

---

### GET /api/mass/eligible

Returns samples eligible for mass measurement.

**Auth:** `login_required`

**Query Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| include_ready | string | `0` (default) or `1` - include already-ready samples |
| q | string | Search by sample_code |

**Response:**

```json
{
  "samples": [
    {
      "id": 1,
      "sample_code": "QC-2026-001",
      "client_name": "CHPP",
      "sample_type": "2 hourly",
      "weight": null,
      "received_date": "2026-01-15 10:30",
      "mass_ready": false
    }
  ]
}
```

---

### POST /api/mass/save

Save mass measurements (weight) and optionally mark samples as mass_ready.

**Auth:** `login_required`

**Request Body:**

```json
{
  "items": [
    { "sample_id": 1, "weight": 2500.0 },
    { "sample_id": 2, "weight": 1800.0 }
  ],
  "mark_ready": true
}
```

**Notes:** Weight is provided in grams and automatically converted to kilograms (divided by 1000).

**Response:**

```json
{
  "success": true,
  "data": { "updated_ids": [1, 2] },
  "message": "2 samples updated."
}
```

---

### POST /api/mass/update_weight

Update weight for a single sample (even if already mass_ready).

**Auth:** `login_required`

**Request Body:**

```json
{
  "sample_id": 1,
  "weight": 1800
}
```

**Response:**

```json
{
  "success": true,
  "data": { "sample_id": 1 },
  "message": "Weight updated."
}
```

---

### POST /api/mass/unready

Reset mass_ready status for selected samples.

**Auth:** `login_required`

**Request Body:**

```json
{
  "sample_ids": [1, 2, 3]
}
```

**Response:**

```json
{
  "success": true,
  "message": "3 samples set to Unready."
}
```

---

### POST /api/mass/delete

Permanently delete a sample (cascade). Restricted to admin/senior roles.

**Auth:** `login_required` | **Role:** `admin`, `senior`

**Request Body:**

```json
{
  "sample_id": 123
}
```

**Response:**

```json
{
  "success": true,
  "data": { "deleted_id": 123 },
  "message": "Sample deleted."
}
```

---

## Senior Review API

Blueprint: `analysis` | URL Prefix: `/analysis`

### GET /analysis/api/ahlah_data

Returns pending and rejected analysis results for the senior review dashboard.

**Auth:** `login_required` | **Role:** `senior`, `admin`

**Query Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| start_date | string | Start date (YYYY-MM-DD) |
| end_date | string | End date (YYYY-MM-DD) |
| sample_name | string | Search by sample code |

**Response:**

```json
[
  {
    "result_id": 42,
    "sample_code": "QC-2026-001",
    "analysis_name": "Ash Content",
    "analysis_code": "Aad",
    "status": "pending_review",
    "error_reason": null,
    "raw_data": { "p1": {}, "p2": {}, "avg": 12.52, "diff": 0.08 },
    "t_value": 0.08,
    "final_value": 12.52,
    "user_name": "chemist1",
    "updated_at": "2026-01-15 10:30"
  }
]
```

---

### POST /analysis/update_result_status/{result_id}/{new_status}

Approve or reject analysis results from the senior dashboard.

**Auth:** `login_required` | **Role:** `senior`, `admin`

**URL Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| result_id | int | AnalysisResult ID |
| new_status | string | `approved`, `rejected`, or `pending_review` |

**Request Body:**

```json
{
  "rejection_comment": "Re-analyze required",
  "rejection_category": "tolerance"
}
```

**Response:**

```json
{
  "message": "OK",
  "status": "approved"
}
```

---

### POST /analysis/bulk_update_status

Bulk approve or reject multiple results.

**Auth:** `login_required` | **Role:** `senior`, `admin`

**Request Body:**

```json
{
  "result_ids": [42, 43, 44],
  "status": "approved",
  "rejection_comment": "Optional",
  "rejection_category": "tolerance"
}
```

**Response:**

```json
{
  "message": "3 result(s) successfully set to approved.",
  "success_count": 3,
  "failed_count": 0,
  "failed_ids": []
}
```

**Notes:**
- When `status` is `rejected`, `rejection_category` is required.
- Only results with `pending_review` or `rejected` status can be modified.
- Triggers email notification for status changes.

---

### GET /analysis/api/ahlah_stats

Statistics for the senior dashboard (shift-aware).

**Auth:** `login_required` | **Role:** `senior`, `admin`

**Response:**

```json
{
  "chemists": [
    {
      "username": "chemist1",
      "user_id": 5,
      "total": 25,
      "approved": 20,
      "pending": 3,
      "rejected": 2
    }
  ],
  "analysis_types": [
    {
      "code": "Aad",
      "name": "Ash Content",
      "total": 15,
      "approved": 12,
      "pending": 2,
      "rejected": 1
    }
  ],
  "samples_today": 42,
  "samples_by_unit": [
    { "name": "CHPP", "count": 30 }
  ],
  "samples_by_type": [
    { "name": "2 hourly", "count": 20 }
  ],
  "summary": {
    "total": 150,
    "approved": 120,
    "pending": 20,
    "rejected": 10
  }
}
```

---

## Audit API

Blueprint: `api` | URL Prefix: `/api`

### GET /api/audit_hub

Renders the audit hub page.

**Auth:** `login_required`

**Response:** Renders HTML template `audit_hub.html`

---

### GET /api/audit_log/{analysis_code}

Audit trail page for a specific analysis code, grouped by sample.

**Auth:** `login_required`

**URL Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| analysis_code | string | Analysis code (e.g., `Aad`) |

**Query Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| start_date | string | Start date (YYYY-MM-DD) |
| end_date | string | End date (YYYY-MM-DD) |
| sample_name | string | Filter by sample code |
| user_name | string | Filter by chemist username |
| error_type | string | Filter by error type (or `all`) |
| shift | string | `day`, `night`, or `all` |

**Response:** Renders HTML template `audit_log_page.html`

---

### GET /api/audit_search

Search audit logs across all analysis types.

**Auth:** `login_required`

**Query Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| q | string | Search text (sample code, username, analysis code) |
| start_date | string | Start date (YYYY-MM-DD) |
| end_date | string | End date (YYYY-MM-DD) |
| analysis_code | string | Filter by analysis code |
| action | string | Filter by action type (APPROVED, REJECTED, etc.) |
| limit | int | Max results (default: 100, max: 500) |

**Response:**

```json
{
  "count": 25,
  "results": [
    {
      "id": 1,
      "timestamp": "2026-01-15 10:30:00",
      "sample_code": "QC-2026-001",
      "analysis_code": "Aad",
      "action": "CREATED_AUTO_APPROVED",
      "user": "chemist1",
      "final_result": 12.52,
      "reason": "Auto-approved",
      "error_reason": null
    }
  ]
}
```

---

## Equipment API

Blueprint: `equipment` | URL Prefix: `/equipment`

### POST /equipment/api/log_usage_bulk

Log usage, calibration checks, and repairs for multiple equipment items at once.

**Auth:** `login_required`

**Request Body:**

```json
{
  "items": [
    {
      "eq_id": 1,
      "minutes": 60,
      "note": "Routine analysis",
      "is_checked": true,
      "calibration": {
        "type": "temperature",
        "set_temp": 815,
        "actual_temp": 814.5
      }
    },
    {
      "eq_id": 2,
      "minutes": 30,
      "repair": true,
      "repair_date": "2026-01-15",
      "note": "Replaced heating element",
      "spare_parts": [
        { "spare_id": 5, "qty": 1, "used_by": "technician1" }
      ]
    }
  ]
}
```

**Calibration Types:**
- `temperature` - Furnace temperature check (set_temp, actual_temp)
- `weight` - Balance check (weights: [{standard, measured}])
- `sulfur` - Sulfur analyzer calibration (standards: [{name, certified, measured}])
- `calorimeter` - Calorimeter check (standard_name, certified_value, measurements: [])
- `analysis` - General analysis check (standard_name, certified_value, measured_value)

**Response:**

```json
{
  "success": true,
  "data": { "count": 3 },
  "message": "3 records saved"
}
```

---

### GET /equipment/api/equipment/usage_summary

Equipment usage summary with aggregated statistics.

**Auth:** `login_required`

**Query Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| start_date | string | Start date (YYYY-MM-DD, default: 30 days ago) |
| end_date | string | End date (YYYY-MM-DD, default: today) |
| category | string | Equipment category filter (default: `all`) |

**Response:**

```json
{
  "rows": [
    {
      "equipment_id": 1,
      "lab_code": "F-001",
      "name": "Muffle Furnace",
      "location": "Coal Lab",
      "room": "101",
      "status": "normal",
      "total_usage_hours": 120.5,
      "maintenance_count": 3,
      "last_usage_end": "2026-01-15T14:00:00",
      "last_maintenance": "2026-01-10T09:00:00",
      "next_calibration_date": "2026-03-15",
      "is_calibration_expired": false
    }
  ],
  "start_date": "2025-12-15",
  "end_date": "2026-01-15"
}
```

---

### GET /equipment/api/equipment/journal_detailed

Detailed maintenance and usage journal.

**Auth:** `login_required`

**Query Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| start_date | string | Start date (YYYY-MM-DD) |
| end_date | string | End date (YYYY-MM-DD) |
| category | string | Equipment category filter |

**Response:**

```json
{
  "rows": [
    {
      "date": "2026-01-15 10:30",
      "timestamp": 1737000600.0,
      "lab_code": "F-001",
      "equipment": "Muffle Furnace",
      "category": "Maintenance",
      "type": "Temperature Check",
      "user": "chemist1",
      "description": "Set: 815C, Actual: 814.5C",
      "result": "Pass"
    }
  ]
}
```

---

### GET /equipment/api/equipment/monthly_stats

Monthly usage and maintenance statistics.

**Auth:** `login_required`

**Query Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| year | int | Year (default: current year) |
| category | string | Equipment category filter |

**Response:**

```json
{
  "rows": [
    {
      "lab_code": "F-001",
      "name": "Muffle Furnace",
      "usage_1": 1200, "maint_1": 5,
      "usage_2": 1100, "maint_2": 3
    }
  ],
  "year": 2026
}
```

---

### GET /equipment/api/equipment_list_json

Equipment list as JSON (for AG Grid).

**Auth:** `login_required`

**Query Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| include_retired | string | `true` to include retired equipment (default: `false`) |

**Response:**

```json
[
  {
    "id": 1,
    "name": "Muffle Furnace",
    "manufacturer": "Nabertherm",
    "model": "L9/11",
    "serial_number": "SN12345",
    "lab_code": "F-001",
    "quantity": 1,
    "location": "Coal Lab",
    "calibration_date": "2025-09-15",
    "next_calibration_date": "2026-03-15",
    "status": "normal",
    "category": "furnace",
    "is_expired": false
  }
]
```

**Notes:** Limited to 1000 equipment records.

---

## Spare Parts API

Blueprint: `spare_parts` | URL Prefix: `/spare_parts`

### GET /spare_parts/api/list

List all spare parts.

**Auth:** `login_required`

**Response:**

```json
[
  {
    "id": 1,
    "name": "Heating Element",
    "name_en": "Heating Element",
    "part_number": "HE-001",
    "quantity": 5,
    "unit": "pcs",
    "reorder_level": 2,
    "status": "active",
    "category": "furnace",
    "storage_location": "Cabinet A",
    "equipment_name": "Muffle Furnace"
  }
]
```

---

### GET /spare_parts/api/low_stock

List spare parts with low or zero stock.

**Auth:** `login_required`

**Response:**

```json
[
  {
    "id": 1,
    "name": "Heating Element",
    "quantity": 1,
    "unit": "pcs",
    "reorder_level": 2,
    "status": "low_stock"
  }
]
```

---

### GET /spare_parts/api/stats

Spare parts statistics.

**Auth:** `login_required`

**Response:**

```json
{
  "total": 50,
  "active": 45,
  "low_stock": 3,
  "out_of_stock": 2,
  "total_value": 125000.0
}
```

---

### POST /spare_parts/api/consume

Consume a spare part (deduct from stock).

**Auth:** `login_required`

**Request Body:**

```json
{
  "spare_part_id": 1,
  "quantity": 1,
  "equipment_id": 5,
  "maintenance_log_id": 10,
  "purpose": "Scheduled replacement"
}
```

**Response:**

```json
{
  "success": true,
  "message": "1 pcs consumed",
  "remaining": 4,
  "status": "active"
}
```

---

### POST /spare_parts/api/consume_bulk

Consume multiple spare parts at once.

**Auth:** `login_required`

**Request Body:**

```json
{
  "items": [
    { "spare_part_id": 1, "quantity": 1 },
    { "spare_part_id": 2, "quantity": 2 }
  ],
  "equipment_id": 5,
  "maintenance_log_id": 10,
  "purpose": "Scheduled maintenance"
}
```

**Response:**

```json
{
  "success": true,
  "results": [
    { "spare_part_id": 1, "name": "Heating Element", "consumed": 1, "remaining": 4 }
  ],
  "errors": []
}
```

---

### GET /spare_parts/api/search

Search spare parts (autocomplete).

**Auth:** `login_required`

**Query Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| q | string | Search query (min 2 chars) |

**Response:**

```json
[
  {
    "id": 1,
    "name": "Heating Element",
    "name_en": "Heating Element",
    "part_number": "HE-001",
    "quantity": 5,
    "unit": "pcs",
    "status": "active"
  }
]
```

---

### GET /spare_parts/api/usage_history/{id}

Usage history for a specific spare part.

**Auth:** `login_required`

**URL Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| id | int | Spare part ID |

**Response:**

```json
[
  {
    "id": 1,
    "quantity_used": 1,
    "unit": "pcs",
    "purpose": "Scheduled replacement",
    "used_by": "technician1",
    "used_at": "2026-01-15 10:30",
    "equipment_name": "Muffle Furnace",
    "quantity_before": 5,
    "quantity_after": 4
  }
]
```

**Notes:** Limited to 100 most recent records.

---

## Chemicals API

Blueprint: `chemicals` | URL Prefix: `/chemicals`

### GET /chemicals/api/list

List all chemicals with filtering.

**Auth:** `login_required`

**Query Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| lab | string | Lab filter (`coal`, `water`, `all`) |
| category | string | Category filter |
| status | string | Status filter (`active`, `low_stock`, `expired`) |
| include_disposed | string | `true` to include disposed (default: `false`) |

**Response:**

```json
[
  {
    "id": 1,
    "name": "Hydrochloric Acid",
    "formula": "HCl",
    "cas_number": "7647-01-0",
    "manufacturer": "Merck",
    "lot_number": "LOT-001",
    "grade": "ACS",
    "quantity": 2.5,
    "unit": "L",
    "reorder_level": 1,
    "expiry_date": "2026-06-15",
    "storage_location": "Cabinet B",
    "lab_type": "coal",
    "category": "acid",
    "status": "active",
    "is_low_stock": false,
    "is_expiring": false,
    "is_expired": false
  }
]
```

**Notes:** Limited to 2000 records.

---

### GET /chemicals/api/low_stock

List chemicals with low stock levels.

**Auth:** `login_required`

**Query Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| lab | string | Lab filter (default: `all`) |

**Response:**

```json
{
  "count": 3,
  "items": [
    {
      "id": 1,
      "name": "HCl",
      "quantity": 0.5,
      "unit": "L",
      "reorder_level": 1,
      "lab_type": "coal"
    }
  ]
}
```

---

### GET /chemicals/api/expiring

List chemicals expiring within a specified period.

**Auth:** `login_required`

**Query Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| lab | string | Lab filter (default: `all`) |
| days | int | Days ahead to check (default: 30) |

**Response:**

```json
{
  "count": 2,
  "items": [
    {
      "id": 1,
      "name": "Silver Nitrate",
      "expiry_date": "2026-02-28",
      "days_left": 13,
      "quantity": 100,
      "unit": "g",
      "lab_type": "water"
    }
  ]
}
```

---

### POST /chemicals/api/consume

Record chemical consumption.

**Auth:** `login_required`

**Request Body:**

```json
{
  "chemical_id": 1,
  "quantity_used": 0.1,
  "purpose": "Titration",
  "analysis_code": "CL_W",
  "sample_id": 42
}
```

**Response:**

```json
{
  "success": true,
  "data": {
    "new_quantity": 2.4,
    "chemical_status": "active"
  },
  "message": "Consumed 0.1 L"
}
```

---

### POST /chemicals/api/consume_bulk

Record consumption for multiple chemicals at once.

**Auth:** `login_required`

**Request Body:**

```json
{
  "items": [
    { "chemical_id": 1, "quantity_used": 0.1 },
    { "chemical_id": 2, "quantity_used": 5.0 }
  ],
  "purpose": "Daily analysis",
  "analysis_code": "PH",
  "sample_id": 42
}
```

**Response:**

```json
{
  "success": true,
  "data": {
    "count": 2,
    "errors": []
  },
  "message": "2 chemicals consumed."
}
```

---

### GET /chemicals/api/search

Search chemicals (autocomplete).

**Auth:** `login_required`

**Query Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| q | string | Search query (min 2 chars, searches name/formula/CAS) |
| lab | string | Lab filter (default: `all`) |
| limit | int | Max results (default: 20) |

**Response:**

```json
[
  {
    "id": 1,
    "name": "Hydrochloric Acid",
    "formula": "HCl",
    "quantity": 2.5,
    "unit": "L",
    "status": "active",
    "label": "Hydrochloric Acid (HCl)"
  }
]
```

---

### GET /chemicals/api/stats

Chemical inventory statistics.

**Auth:** `login_required`

**Query Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| lab | string | Lab filter (default: `all`) |

**Response:**

```json
{
  "total": 85,
  "low_stock": 5,
  "expired": 2,
  "expiring": 8,
  "by_category": {
    "acid": 15,
    "base": 10,
    "indicator": 8,
    "standard": 12
  }
}
```

---

### GET /chemicals/api/usage_history

Chemical usage history with filtering.

**Auth:** `login_required`

**Query Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| chemical_id | int | Filter by specific chemical |
| lab | string | Lab filter (default: `all`) |
| start_date | string | Start date (YYYY-MM-DD) |
| end_date | string | End date (YYYY-MM-DD) |
| limit | int | Max results (default: 100) |

**Response:**

```json
{
  "items": [
    {
      "id": 1,
      "chemical_id": 1,
      "chemical_name": "Hydrochloric Acid",
      "quantity_used": 0.1,
      "unit": "L",
      "purpose": "Titration",
      "analysis_code": "CL_W",
      "used_at": "2026-01-15 10:30",
      "used_by": "chemist1"
    }
  ],
  "count": 25
}
```

---

## Quality Management API

Blueprint: `quality` | URL Prefix: `/quality`

All quality management routes follow ISO 17025 requirements. These are primarily HTML-rendered pages with form-based interactions, not REST APIs.

### QC Control Charts

#### GET /quality/control_charts

QC Control Charts page displaying CM/GBW analysis results.

**Auth:** `login_required`

**Response:** Renders HTML template `quality/control_charts.html`

---

#### GET /quality/api/westgard_summary

Westgard rule summary for all QC standard/analysis combinations.

**Auth:** `login_required`

**Response:**

```json
{
  "qc_samples": [
    {
      "standard_name": "GBW11135a",
      "qc_type": "GBW",
      "analysis_code": "Aad",
      "status": "pass",
      "rules_violated": [],
      "count": 15,
      "target": 12.5,
      "sd": 0.15,
      "latest_value": 12.48
    }
  ]
}
```

**Status Values:** `pass`, `warning`, `fail`, `insufficient_data`

---

#### GET /quality/api/westgard_detail/{qc_type}/{analysis_code}

Detailed Westgard analysis for a specific QC type and analysis code.

**Auth:** `login_required`

**URL Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| qc_type | string | `CM` or `GBW` |
| analysis_code | string | Analysis code (e.g., `Aad`) |

**Response:**

```json
{
  "qc_type": "GBW",
  "analysis_code": "Aad",
  "count": 15,
  "target": 12.5,
  "ucl": 12.8,
  "lcl": 12.2,
  "sd": 0.15,
  "qc_status": {
    "status": "pass",
    "rules_violated": []
  },
  "latest_value": {
    "value": 12.48,
    "check": { "status": "ok", "zone": "1s" }
  },
  "violations": [],
  "data_points": [
    {
      "value": 12.48,
      "date": "2026-01-15T10:30:00",
      "sample_code": "GBW11135a_20260115A",
      "operator": "chemist1"
    }
  ]
}
```

---

### Customer Complaints (ISO 17025 Clause 7.9)

#### GET /quality/complaints

List all customer complaints.

**Auth:** `login_required`

**Response:** Renders HTML template `quality/complaints_list.html`

---

#### GET /quality/complaints/dashboard

Complaints dashboard with yearly statistics (by month, analysis type, department, senior).

**Auth:** `login_required`

**Query Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| year | int | Year (default: current year) |

**Response:** Renders HTML template `quality/complaints_dashboard.html`

---

#### POST /quality/complaints/new

Create a new customer complaint. Supports automatic rejection of related analysis results for re-analysis.

**Auth:** `login_required` | **Role:** quality edit permission required

**Form Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| complainant_name | string | Name of complainant (required) |
| complaint_content | string | Complaint description (required) |
| complaint_date | string | Date (default: today) |
| complainant_department | string | Department |
| related_sample_id | int | Related sample ID |
| reanalysis_codes | JSON string | Analysis codes for re-analysis |
| original_results_snapshot | JSON string | Original results snapshot |

---

#### POST /quality/complaints/{id}/receive

Record complaint reception by senior analyst.

**Auth:** `login_required` | **Role:** quality edit permission required

---

#### POST /quality/complaints/{id}/control

Quality manager review of complaint.

**Auth:** `login_required` | **Role:** quality edit permission required

---

### Corrective Actions - CAPA (ISO 17025 Clause 8.7)

#### GET /quality/capa

List all corrective actions.

**Auth:** `login_required`

---

#### POST /quality/capa/new

Create a new corrective action.

**Auth:** `login_required` | **Role:** quality edit permission required

---

#### POST /quality/capa/{id}/fill

Fill in corrective action details (implementer).

**Auth:** `login_required`

---

#### POST /quality/capa/{id}/review

Technical manager review.

**Auth:** `login_required` | **Role:** quality edit permission required

---

### Improvement Records (ISO 17025 Clause 8.6)

#### GET /quality/improvement

List all improvement records.

**Auth:** `login_required`

---

#### POST /quality/improvement/new

Create a new improvement record.

**Auth:** `login_required` | **Role:** quality edit permission required

---

#### POST /quality/improvement/{id}/fill

Fill in improvement details.

**Auth:** `login_required`

---

#### POST /quality/improvement/{id}/review

Technical manager review.

**Auth:** `login_required` | **Role:** quality edit permission required

---

### Nonconformity Records (ISO 17025 Clause 7.10)

#### GET /quality/nonconformity

List all nonconformity records.

**Auth:** `login_required`

---

#### POST /quality/nonconformity/new

Create a new nonconformity record.

**Auth:** `login_required` | **Role:** quality edit permission required

---

#### POST /quality/nonconformity/{id}/investigate

Investigation by responsible unit.

**Auth:** `login_required` | **Role:** quality edit permission required

---

#### POST /quality/nonconformity/{id}/review

Manager review.

**Auth:** `login_required` | **Role:** quality edit permission required

---

### Proficiency Testing (ISO 17025 Clause 7.7.2)

#### GET /quality/proficiency

List all proficiency test records.

**Auth:** `login_required`

---

#### POST /quality/proficiency/new

Register a new proficiency test result. Automatically calculates Z-score and performance rating.

**Auth:** `login_required` | **Role:** quality edit permission required

**Performance Rating:**
- |Z-score| <= 2: `satisfactory`
- |Z-score| <= 3: `questionable`
- |Z-score| > 3: `unsatisfactory`

---

### Environmental Monitoring (ISO 17025 Clause 6.3.3)

#### GET /quality/environmental

List environmental monitoring records.

**Auth:** `login_required`

---

#### POST /quality/environmental/add

Add an environmental measurement.

**Auth:** `login_required` | **Role:** quality edit permission required

**Form Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| location | string | Measurement location |
| temperature | float | Temperature reading |
| humidity | float | Humidity reading |
| temp_min | float | Min acceptable temp (default: 15) |
| temp_max | float | Max acceptable temp (default: 30) |
| humidity_min | float | Min acceptable humidity (default: 20) |
| humidity_max | float | Max acceptable humidity (default: 70) |
| notes | string | Additional notes |

---

## Chat API

Blueprint: `api` | URL Prefix: `/api`

### GET /api/chat/contacts

List chat contacts with unread message counts and online status.

**Auth:** `login_required`

**Response:**

```json
{
  "contacts": [
    {
      "id": 5,
      "username": "senior1",
      "role": "senior",
      "is_online": true,
      "unread_count": 3,
      "last_message": "Results are ready",
      "last_message_time": "2026-01-15T10:30:00",
      "last_message_urgent": false
    }
  ]
}
```

**Notes:** Chemists/prep users only see senior/admin contacts. Seniors/admins see all users.

---

### GET /api/chat/history/{user_id}

Message history between the current user and specified user. Automatically marks messages as read.

**Auth:** `login_required`

**Query Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| page | int | Page number (default: 1) |
| per_page | int | Messages per page (default: 50) |
| search | string | Search within messages |

**Response:**

```json
{
  "messages": [ ... ],
  "page": 1,
  "pages": 3,
  "total": 150,
  "has_more": true
}
```

---

### GET /api/chat/search

Search messages across conversations.

**Auth:** `login_required`

**Query Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| q | string | Search query (min 2 chars) |
| user_id | int | Optional: limit to specific conversation |

**Response:**

```json
{
  "messages": [ ... ],
  "query": "search text"
}
```

---

### GET /api/chat/unread_count

Get total unread message count for the current user.

**Auth:** `login_required`

**Response:**

```json
{
  "unread_count": 5
}
```

---

### POST /api/chat/upload

Upload a file attachment for chat.

**Auth:** `login_required`

**Request:** Multipart form with `file` field.

**Allowed Extensions:** png, jpg, jpeg, gif, webp, pdf, doc, docx, xls, xlsx

**Max File Size:** 10 MB

**Response:**

```json
{
  "success": true,
  "file_url": "/static/uploads/chat/abc123.png",
  "file_name": "original_name.png",
  "file_size": 524288
}
```

**Security:** Validates file extension, magic bytes, generates UUID filename.

---

### GET /api/chat/samples/search

Search samples for linking in chat messages.

**Auth:** `login_required`

**Query Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| q | string | Search query (min 2 chars) |

**Response:**

```json
{
  "samples": [
    {
      "id": 1,
      "code": "QC-2026-001",
      "name": "2 hourly - CHPP",
      "type": "2 hourly",
      "client": "CHPP"
    }
  ]
}
```

---

### GET /api/chat/templates

Get predefined message templates.

**Auth:** `login_required`

**Response:**

```json
{
  "templates": [
    { "id": 1, "text": "Sample is ready", "icon": "..." },
    { "id": 2, "text": "Analysis started", "icon": "..." }
  ]
}
```

---

### GET /api/chat/broadcasts

Get broadcast announcements.

**Auth:** `login_required`

**Response:**

```json
{
  "broadcasts": [ ... ]
}
```

---

## Morning Dashboard API

Blueprint: `api` | URL Prefix: `/api`

### GET /api/morning_dashboard

Morning start dashboard data including equipment calibration status, broken equipment, and sample counts.

**Auth:** `login_required`

**Query Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| lab | string | Lab type: `coal`, `water`, `micro`, `petro` (default: `coal`) |

**Response:**

```json
{
  "calibration_due": [
    {
      "id": 1,
      "lab_code": "F-001",
      "name": "Muffle Furnace",
      "next_calibration": "2026-01-20",
      "days_left": 5
    }
  ],
  "calibration_overdue": [
    {
      "id": 2,
      "lab_code": "B-003",
      "name": "Analytical Balance",
      "next_calibration": "2026-01-10",
      "days_overdue": 5
    }
  ],
  "broken_equipment": [
    {
      "id": 3,
      "lab_code": "A-002",
      "name": "TGA Analyzer",
      "status": "maintenance"
    }
  ],
  "samples": {
    "new": 12,
    "in_progress": 8,
    "today_received": 15
  }
}
```

---

## Simulator API

Blueprint: `api` | URL Prefix: `/api`

### POST /api/send_to_simulator/chpp/{sample_id}

Send approved CHPP sample analysis results to the external Simulator system.

**Auth:** `login_required`

**URL Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| sample_id | int | Sample ID (must be CHPP client) |

**Response:**

```json
{
  "success": true,
  "message": "Sent to Simulator successfully (8 analyses)",
  "simulator_response": { ... }
}
```

**Error Responses:**
- 404: Sample not found
- 400: Not a CHPP sample or no approved results
- 502: Simulator connection failed
- 504: Simulator timeout

---

### POST /api/send_to_simulator/wtl/{lab_number}

Send WTL washability data to the Simulator.

**Auth:** `login_required`

**URL Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| lab_number | string | WTL lab number |

**Response:**

```json
{
  "success": true,
  "message": "Sent to Simulator successfully (70 fractions)",
  "simulator_response": { ... }
}
```

---

## Export API

Blueprint: `api` | URL Prefix: `/api`

### GET /api/export/samples

Export sample data to Excel (.xlsx).

**Auth:** `login_required`

**Query Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| client | string | Filter by client name |
| type | string | Filter by sample type |
| start_date | string | Start date (YYYY-MM-DD) |
| end_date | string | End date (YYYY-MM-DD) |
| limit | int | Max rows (default: 1000, max: 5000) |

**Response:** Binary Excel file download

---

### GET /api/export/analysis

Export analysis results to Excel (.xlsx).

**Auth:** `login_required`

**Query Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| status | string | Filter by status |
| start_date | string | Start date (YYYY-MM-DD) |
| end_date | string | End date (YYYY-MM-DD) |
| limit | int | Max rows (default: 1000, max: 5000) |

**Response:** Binary Excel file download

---

### GET /api/export/audit

Export audit log to Excel (.xlsx).

**Auth:** `login_required`

**Query Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| start_date | string | Start date (YYYY-MM-DD) |
| end_date | string | End date (YYYY-MM-DD) |
| action | string | Filter by action type |
| limit | int | Max rows (default: 1000, max: 5000) |

**Response:** Binary Excel file download

---

## HTMX Endpoints

These endpoints return HTML fragments for use with HTMX.

Blueprint: `api` | URL Prefix: `/api`

### GET /api/sample_count

Returns total coal sample count as an HTML fragment.

**Auth:** `login_required`

**Response:** `<strong class="text-primary">150</strong> samples`

---

### GET /api/search_samples

Search samples and return HTML partial results.

**Auth:** `login_required`

**Query Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| q | string | Search query (min 2 chars) |

**Response:** HTML list-group fragment with matching samples (max 10).

---

## Error Codes

### HTTP Status Codes

| HTTP Status | Description |
|-------------|-------------|
| 200 | Success |
| 207 | Multi-Status (partial success in batch operations) |
| 400 | Bad Request / Validation Error |
| 403 | Forbidden (insufficient permissions) |
| 404 | Resource Not Found |
| 409 | Conflict (data integrity error, e.g., cascade delete blocked) |
| 429 | Rate Limited |
| 500 | Internal Server Error |
| 502 | Bad Gateway (external service connection failure) |
| 504 | Gateway Timeout (external service timeout) |

### API Error Codes

| Code | Description |
|------|-------------|
| `VALIDATION_ERROR` | Invalid input data |
| `NOT_FOUND` | Resource not found |
| `UNAUTHORIZED` | Not logged in |
| `FORBIDDEN` | Insufficient permissions |
| `DUPLICATE` | Duplicate entry |
| `DATABASE_ERROR` | Database operation failed |
| `INTERNAL_ERROR` | Internal server error |

### Analysis Status Values

| Status | Description |
|--------|-------------|
| `approved` | Automatically approved (within tolerance) |
| `pending_review` | Requires senior review (tolerance exceeded or manual review needed) |
| `rejected` | Rejected by senior or QC failure |

### Sample Status Values

| Status | Description |
|--------|-------------|
| `new` / `New` | Newly registered sample |
| `in_progress` | Analysis in progress |
| `completed` | All analyses complete |
| `reported` | Report generated |
| `archived` | Archived sample |
| `disposed` | Sample disposed |

---

## Security Features

- **SQL Injection Protection:** All LIKE queries use `escape_like_pattern()` from `app.utils.security`
- **XSS Protection:** User-supplied text (rejection_comment, etc.) is escaped via `markupsafe.escape()`
- **CSRF Protection:** Flask-WTF CSRF tokens on all POST forms
- **Rate Limiting:** `flask-limiter` on all critical endpoints
- **Audit Integrity:** Hash-based integrity verification on audit logs (ISO 17025 compliance)
- **File Upload Security:** Extension validation, magic bytes verification, UUID filename generation
- **Open Redirect Protection:** `is_safe_url()` check on login redirects
