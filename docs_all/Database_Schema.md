# Coal LIMS - Database Schema Documentation

**Last Updated:** 2026-02-15
**Database Engine:** PostgreSQL (via SQLAlchemy ORM)
**Total Tables:** 46 (44 database tables + 1 mixin + 1 non-DB calculation class)
**Source File:** `app/models/models.py`

---

## Table of Contents

1. [Overview](#overview)
2. [Core Domain](#1-core-domain)
3. [Quality Management (ISO 17025)](#2-quality-management-iso-17025)
4. [Equipment Management](#3-equipment-management)
5. [Chemicals & Reagents](#4-chemicals--reagents)
6. [Spare Parts Inventory](#5-spare-parts-inventory)
7. [Audit & Logging](#6-audit--logging)
8. [Washability & Yield](#7-washability--yield)
9. [Reports](#8-reports)
10. [Solutions (Water Chemistry Lab)](#9-solutions-water-chemistry-lab)
11. [Planning & Staff](#10-planning--staff)
12. [Chat & Communication](#11-chat--communication)
13. [Settings & Configuration](#12-settings--configuration)
14. [License Management](#13-license-management)
15. [Entity Relationship Summary](#entity-relationship-summary)
16. [Mermaid ER Diagram](#mermaid-er-diagram)

---

## Overview

The Coal LIMS database supports a multi-laboratory system (Coal, Water Chemistry, Microbiology, Petrography) compliant with ISO 17025. All models are defined in a single file `app/models/models.py` and re-exported through `app/models/__init__.py`.

**Key Design Principles:**
- SHA-256 hash integrity via `HashableMixin` on audit-critical tables
- Mongolian local timestamps (`now_mn`) instead of UTC for all user-facing dates
- Soft references with `SET NULL` on delete for audit preservation
- JSON columns for flexible semi-structured data (raw_data, targets, extra_data)
- Composite indexes on frequently queried column combinations

**Shared Mixin:**

### HashableMixin (not a table)

ISO 17025 audit log integrity mixin. Provides SHA-256 hash computation and verification for tamper detection.

| Method | Description |
|--------|-------------|
| `_get_hash_data()` | Override: returns pipe-separated string of fields to hash |
| `compute_hash()` | Computes SHA-256 hash of record data |
| `verify_hash()` | Returns True if hash is valid or not set |

**Used by:** `AuditLog`, `AnalysisResultLog`, `SparePartLog`, `ChemicalLog`

---

## 1. Core Domain

### 1.1 User

**Table name:** `user`
**Purpose:** System users with role-based access control and multi-laboratory permissions.

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| `id` | Integer | No | Auto | Primary key |
| `username` | String(64) | No | - | Login username (unique, indexed) |
| `password_hash` | String(256) | Yes | - | Werkzeug hashed password |
| `role` | String(64) | Yes | `'prep'` | User role (indexed). Values: `prep`, `chemist`, `senior`, `manager`, `admin` |
| `allowed_labs` | JSON | Yes | `['coal']` | List of lab keys user can access: `coal`, `petrography`, `water`, `microbiology` |
| `full_name` | String(100) | Yes | - | Full name (for email signatures) |
| `email` | String(120) | Yes | - | Work email address |
| `phone` | String(20) | Yes | - | Phone number |
| `position` | String(100) | Yes | - | Job title / position |

**Indexes:** `username` (unique), `role`
**Relationships:**
- `analysis_results` -> AnalysisResult (backref, one-to-many)
- `logs` -> AnalysisResultLog (backref via dynamic, one-to-many)
- `audit_logs` -> AuditLog (backref, one-to-many)
- `sent_messages` -> ChatMessage (backref, one-to-many)
- `received_messages` -> ChatMessage (backref, one-to-many)
- `online_status` -> UserOnlineStatus (backref, one-to-one)
- `monthly_plans` -> MonthlyPlan (backref, one-to-many)
- `pt_tests` -> ProficiencyTest (backref, one-to-many)
- `env_logs` -> EnvironmentalLog (backref, one-to-many)
- `qc_measurements` -> QCControlChart (backref, one-to-many)
- `assigned_capas` -> CorrectiveAction (backref, one-to-many)
- `verified_capas` -> CorrectiveAction (backref, one-to-many)
- `reviewed_capas` -> CorrectiveAction (backref, one-to-many)
- `filed_complaints` -> CustomerComplaint (backref, one-to-many)
- `received_complaints` -> CustomerComplaint (backref, one-to-many)
- `signed_complaints` -> CustomerComplaint (backref, one-to-many)
- `improvement_records` -> ImprovementRecord (backref, one-to-many)
- `detected_nonconformities` -> NonConformityRecord (backref, one-to-many)
- `responsible_nonconformities` -> NonConformityRecord (backref, one-to-many)
- `reviewed_nonconformities` -> NonConformityRecord (backref, one-to-many)

---

### 1.2 Sample

**Table name:** `sample`
**Purpose:** Laboratory sample registration with chain of custody tracking and multi-lab support.

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| `id` | Integer | No | Auto | Primary key |
| `sample_code` | String(100) | Yes | - | Unique sample code (e.g., "CHPP-250101-001") |
| `received_date` | DateTime | Yes | `now_mn` | Date/time received (Mongolian time) |
| `user_id` | Integer | Yes | - | FK -> User (who registered) |
| `status` | String(64) | Yes | `'new'` | Sample status: `new`, `prepared`, `analysis`, `completed` |
| `lab_type` | String(20) | Yes | `'coal'` | Lab type: `coal`, `petrography`, `water`, `microbiology` |
| `sample_date` | Date | Yes | `now_mn().date()` | Sampling date |
| `sample_condition` | String(100) | Yes | - | Sample condition description |
| `client_name` | String(200) | Yes | - | Client/consignor name (CHECK constraint) |
| `sample_type` | String(100) | Yes | - | Sample type (e.g., "2 hourly", "Daily") |
| `analyses_to_perform` | String(500) | Yes | - | Space-separated analysis codes to perform |
| `notes` | Text | Yes | - | Notes / remarks |
| `weight` | Float | Yes | - | Weight in grams |
| `return_sample` | Boolean | Yes | `False` | Whether sample should be returned |
| `delivered_by` | String(200) | Yes | - | Person who delivered the sample |
| `prepared_by` | String(200) | Yes | - | Person who prepared the sample |
| `prepared_date` | Date | Yes | - | Preparation date |
| `location` | String(100) | Yes | - | Location |
| `hourly_system` | String(50) | Yes | - | Hourly system identifier |
| `shift_time` | String(50) | Yes | - | Shift time |
| `product` | String(100) | Yes | - | Product name |
| `mass_ready` | Boolean | No | `False` | Whether mass gate is ready |
| `mass_ready_at` | DateTime | Yes | - | When mass gate became ready |
| `mass_ready_by_id` | Integer | Yes | - | User who marked mass gate ready |
| `chem_lab_id` | String(20) | Yes | - | Water chemistry lab ID (e.g., "1_05") |
| `micro_lab_id` | String(20) | Yes | - | Microbiology lab ID (e.g., "01_05") |
| `sampled_by` | String(100) | Yes | - | ISO 17025: Who collected the sample |
| `sampling_date` | DateTime | Yes | - | ISO 17025: When sample was collected |
| `sampling_location` | String(200) | Yes | - | ISO 17025: Where sample was collected |
| `sampling_method` | String(100) | Yes | - | ISO 17025: SOP reference |
| `custody_log` | Text | Yes | - | ISO 17025: JSON chain of custody history |
| `retention_date` | Date | Yes | - | ISO 17025: Retention expiry date |
| `disposal_date` | Date | Yes | - | Disposal date |
| `disposal_method` | String(100) | Yes | - | Disposal method |

**Indexes:** `sample_code` (unique), `received_date`, `status`, `lab_type`, `mass_ready`, `chem_lab_id`, `micro_lab_id`, `user_id`
**Constraints:**
- CHECK `ck_sample_client_name`: Restricts `client_name` to predefined values (CHPP, UHG-Geo, BN-Geo, QC, WTL, Proc, LAB, uutsb, negdsen_office, etc.)

**Relationships:**
- `results` -> AnalysisResult (one-to-many, cascade delete-orphan, dynamic)
- `complaints` -> CustomerComplaint (backref, one-to-many)
- `washability_tests` -> WashabilityTest (backref, one-to-many)
- `chat_messages` -> ChatMessage (backref, one-to-many)

---

### 1.3 AnalysisResult

**Table name:** `analysis_result`
**Purpose:** Individual analysis result for a sample, with raw data and approval workflow.

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| `id` | Integer | No | Auto | Primary key |
| `sample_id` | Integer | No | - | FK -> Sample |
| `user_id` | Integer | Yes | - | FK -> User (analyst) |
| `analysis_code` | String(50) | No | - | Analysis code (e.g., "Mad", "Aad", "CV") |
| `final_result` | Float | Yes | - | Final numeric result |
| `raw_data` | Text | Yes | - | Raw data as JSON string |
| `reason` | Text | Yes | - | Explanation / reason |
| `status` | String(50) | No | `'pending_review'` | Status: `pending_review`, `approved`, `rejected`, `reanalysis` |
| `rejection_category` | String(100) | Yes | - | ISO rejection category |
| `rejection_subcategory` | String(100) | Yes | - | ISO rejection subcategory |
| `rejection_comment` | String(255) | Yes | - | Rejection comment |
| `error_reason` | String(50) | Yes | - | KPI error reason |
| `created_at` | DateTime | Yes | `now_mn` | Created timestamp |
| `updated_at` | DateTime | Yes | `now_mn` | Last updated timestamp (auto-update) |

**Indexes:** `sample_id`, `user_id`, `analysis_code`, `status`, `created_at`
**Composite Indexes:**
- `ix_analysis_result_sample_code` (sample_id, analysis_code)
- `ix_analysis_result_sample_status` (sample_id, status)
- `ix_analysis_result_code_status` (analysis_code, status)
- `ix_analysis_result_user_code` (user_id, analysis_code)

**Relationships:**
- `sample` -> Sample (many-to-one, via backref)
- `user` -> User (many-to-one)
- `logs` -> AnalysisResultLog (one-to-many, cascade delete-orphan, dynamic, ordered by desc timestamp)

---

### 1.4 AnalysisType

**Table name:** `analysis_type`
**Purpose:** Registry of available analysis types with ordering and role requirements.

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| `id` | Integer | No | Auto | Primary key |
| `code` | String(50) | No | - | Unique analysis code (e.g., "Mad", "Aad") |
| `name` | String(100) | No | - | Analysis name (e.g., "Moisture air-dried") |
| `order_num` | Integer | Yes | `100` | Display order |
| `required_role` | String(64) | No | `'chemist'` | Minimum role required |
| `lab_type` | String(20) | Yes | `'coal'` | Lab type: `coal`, `petrography`, `water` |

**Indexes:** `code` (unique), `required_role`, `lab_type`

---

### 1.5 AnalysisProfile

**Table name:** `analysis_profiles`
**Purpose:** Auto-selection profiles mapping client/sample type to analysis sets via simple or regex pattern matching.

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| `id` | Integer | No | Auto | Primary key |
| `profile_type` | String(50) | No | `'simple'` | Profile type: `simple` or `pattern` |
| `client_name` | String(200) | Yes | - | Client name (for simple profiles) |
| `sample_type` | String(100) | Yes | - | Sample type (for simple profiles) |
| `pattern` | String(255) | Yes | - | Regex pattern (for pattern profiles) |
| `analyses_json` | Text | Yes | `'[]'` | JSON array of analysis codes |
| `priority` | Integer | Yes | `50` | Matching priority (higher = more important) |
| `match_rule` | String(50) | Yes | `'merge'` | `merge` (add to existing) or `replace` |

**Indexes:** `profile_type`, `client_name`, `sample_type`, `pattern`

---

### 1.6 SampleCalculations (non-DB class)

**Not a database table.** This is a Python helper class that computes derived coal analysis values (dry basis, as-received, dry ash-free) from a Sample's AnalysisResult records. Instantiated via `sample.get_calculations()`.

---

## 2. Quality Management (ISO 17025)

### 2.1 CorrectiveAction

**Table name:** `corrective_action`
**Purpose:** CAPA (Corrective and Preventive Actions) records per ISO 17025 Clause 8.7.

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| `id` | Integer | No | Auto | Primary key |
| `ca_number` | String(50) | No | - | CAPA number (e.g., "CA-2025-001", unique) |
| `issue_date` | Date | No | `now_mn` | Date issue was identified |
| `issue_source` | String(100) | Yes | - | Source: Internal audit, Customer complaint, PT, Equipment |
| `issue_description` | Text | No | - | Description of the issue |
| `severity` | String(20) | Yes | `'Minor'` | Severity: `Critical`, `Major`, `Minor` |
| `root_cause` | Text | Yes | - | Root cause analysis result |
| `root_cause_method` | String(100) | Yes | - | Method: 5 Whys, Fishbone, Pareto |
| `corrective_action` | Text | Yes | - | Corrective action taken |
| `preventive_action` | Text | Yes | - | Preventive action planned |
| `responsible_person_id` | Integer | Yes | - | FK -> User (responsible person) |
| `target_date` | Date | Yes | - | Target completion date |
| `completion_date` | Date | Yes | - | Actual completion date |
| `verification_method` | Text | Yes | - | Verification method (legacy) |
| `verification_date` | Date | Yes | - | Verification date (legacy) |
| `verified_by_id` | Integer | Yes | - | FK -> User (verifier, legacy) |
| `effectiveness` | String(20) | Yes | - | Effectiveness rating (legacy) |
| `completed_on_time` | Boolean | Yes | - | Completed on time? (technical manager section) |
| `fully_resolved` | Boolean | Yes | - | Fully resolved? |
| `residual_risk_exists` | Boolean | Yes | - | Residual risk exists? |
| `management_change_needed` | Boolean | Yes | - | Management system change needed? |
| `control_notes` | Text | Yes | - | Control section notes |
| `control_date` | Date | Yes | - | Control review date |
| `technical_manager_id` | Integer | Yes | - | FK -> User (technical manager) |
| `status` | String(20) | Yes | `'open'` | Status: `open`, `in_progress`, `reviewed`, `closed` |
| `notes` | Text | Yes | - | General notes |

**Indexes:** `ca_number` (unique), `status`
**Relationships:**
- `responsible_person` -> User (many-to-one)
- `verified_by` -> User (many-to-one)
- `technical_manager` -> User (many-to-one)
- `source_complaints` -> CustomerComplaint (backref, one-to-many)

---

### 2.2 ProficiencyTest

**Table name:** `proficiency_test`
**Purpose:** Proficiency testing records per ISO 17025 Clause 7.7.2 for lab capability verification.

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| `id` | Integer | No | Auto | Primary key |
| `pt_provider` | String(150) | Yes | - | PT provider (ASTM, ISO LEAP, NIST) |
| `pt_program` | String(100) | Yes | - | PT program name |
| `round_number` | String(50) | Yes | - | Round number |
| `sample_code` | String(100) | Yes | - | PT sample code |
| `analysis_code` | String(50) | Yes | - | Analysis code tested |
| `our_result` | Float | Yes | - | Lab's result |
| `assigned_value` | Float | Yes | - | Assigned (correct) value |
| `uncertainty` | Float | Yes | - | Measurement uncertainty |
| `z_score` | Float | Yes | - | Z-score performance indicator |
| `performance` | String(30) | Yes | - | `satisfactory`, `questionable`, `unsatisfactory` |
| `received_date` | Date | Yes | - | Date PT sample received |
| `test_date` | Date | Yes | - | Date test performed |
| `report_date` | Date | Yes | - | Date results reported |
| `certificate_file` | String(255) | Yes | - | Certificate file path |
| `notes` | Text | Yes | - | Notes |
| `tested_by_id` | Integer | Yes | - | FK -> User |

**Indexes:** `analysis_code`, `test_date`
**Relationships:**
- `tested_by` -> User (many-to-one)

---

### 2.3 CustomerComplaint

**Table name:** `customer_complaint`
**Purpose:** Customer complaint tracking per ISO 17025 Clause 7.9 (LAB.02.00.01 form).

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| `id` | Integer | No | Auto | Primary key |
| `complaint_no` | String(50) | Yes | - | Complaint number (e.g., "COMP-2025-001", unique) |
| `complaint_date` | Date | No | `now_mn` | Date of complaint |
| `complainant_name` | String(200) | Yes | - | Complainant name, title |
| `complainant_department` | String(200) | Yes | - | Complainant department |
| `complaint_content` | Text | Yes | - | Complaint details and evidence |
| `complainant_user_id` | Integer | Yes | - | FK -> User (complainant signature) |
| `receiver_name` | String(200) | Yes | - | Receiver name, title |
| `action_taken` | Text | Yes | - | Actions taken by receiver |
| `receiver_documentation` | Text | Yes | - | Documentation materials |
| `is_justified` | Boolean | Yes | - | Whether complaint is justified |
| `response_detail` | Text | Yes | - | Response detail |
| `receiver_user_id` | Integer | Yes | - | FK -> User (receiver signature) |
| `action_corrective` | Boolean | Yes | `False` | Corrective action checkbox |
| `action_improvement` | Boolean | Yes | `False` | Improvement action checkbox |
| `action_partial_audit` | Boolean | Yes | `False` | Partial audit checkbox |
| `quality_manager_id` | Integer | Yes | - | FK -> User (quality manager) |
| `reanalysis_codes` | Text | Yes | - | JSON list of reanalysis codes |
| `original_results_snapshot` | Text | Yes | - | JSON snapshot of original results |
| `client_name` | String(200) | Yes | - | Client name (legacy) |
| `contact_person` | String(100) | Yes | - | Contact person (legacy) |
| `contact_email` | String(100) | Yes | - | Contact email (legacy) |
| `contact_phone` | String(50) | Yes | - | Contact phone (legacy) |
| `complaint_type` | String(100) | Yes | - | Complaint type (legacy) |
| `description` | Text | Yes | - | Description (legacy) |
| `related_sample_id` | Integer | Yes | - | FK -> Sample (SET NULL on delete) |
| `investigated_by_id` | Integer | Yes | - | FK -> User (legacy) |
| `investigation_findings` | Text | Yes | - | Investigation findings (legacy) |
| `resolution` | Text | Yes | - | Resolution (legacy) |
| `resolution_date` | Date | Yes | - | Resolution date (legacy) |
| `customer_notified` | Boolean | Yes | `False` | Customer notified (legacy) |
| `customer_satisfied` | Boolean | Yes | - | Customer satisfied (legacy) |
| `capa_created` | Boolean | Yes | `False` | CAPA created (legacy) |
| `capa_id` | Integer | Yes | - | FK -> CorrectiveAction (legacy) |
| `status` | String(20) | Yes | `'draft'` | Status: `draft`, `received`, `resolved`, `closed` |

**Indexes:** `complaint_no` (unique), `status`
**Relationships:**
- `complainant_user` -> User
- `receiver_user` -> User
- `quality_manager` -> User
- `investigated_by` -> User
- `related_sample` -> Sample
- `related_capa` -> CorrectiveAction
- `improvement_records` -> ImprovementRecord (backref, one-to-many)

---

### 2.4 ImprovementRecord

**Table name:** `improvement_record`
**Purpose:** Continuous improvement records per ISO 17025 Clause 8.6 (LAB.02.00.03 form).

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| `id` | Integer | No | Auto | Primary key |
| `record_no` | String(50) | No | - | Record number (e.g., "IMP-2026-0001", unique) |
| `record_date` | Date | No | `now_mn` | Record date |
| `activity_description` | Text | Yes | - | Activity requiring improvement |
| `improvement_plan` | Text | Yes | - | Improvement plan |
| `deadline` | Date | Yes | - | Deadline |
| `responsible_person` | String(200) | Yes | - | Responsible person name |
| `documentation` | Text | Yes | - | Documentation and notes |
| `created_by_id` | Integer | Yes | - | FK -> User |
| `source_complaint_id` | Integer | Yes | - | FK -> CustomerComplaint (auto-created from complaint) |
| `completed_on_time` | Boolean | Yes | - | Completed on time? |
| `fully_implemented` | Boolean | Yes | - | Fully implemented? |
| `control_notes` | Text | Yes | - | Control notes |
| `control_date` | Date | Yes | - | Control date |
| `technical_manager_id` | Integer | Yes | - | FK -> User (technical manager) |
| `status` | String(20) | Yes | `'pending'` | Status: `pending`, `in_progress`, `reviewed`, `closed` |

**Indexes:** `record_no` (unique), `status`
**Relationships:**
- `created_by` -> User
- `technical_manager` -> User
- `source_complaint` -> CustomerComplaint

---

### 2.5 NonConformityRecord

**Table name:** `nonconformity_record`
**Purpose:** Non-conforming work management per ISO 17025 Clause 7.10 (LAB.10.00.01 form).

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| `id` | Integer | No | Auto | Primary key |
| `record_no` | String(50) | No | - | Record number (e.g., "NC-2026-0001", unique) |
| `record_date` | Date | No | `now_mn` | Record date |
| `detector_name` | String(200) | Yes | - | Name of person who detected |
| `detector_department` | String(200) | Yes | - | Detector's department |
| `nc_description` | Text | Yes | - | Description and evidence |
| `proposed_action` | Text | Yes | - | Proposed action |
| `detector_user_id` | Integer | Yes | - | FK -> User (detector) |
| `responsible_unit` | String(200) | Yes | - | Responsible unit |
| `responsible_person` | String(200) | Yes | - | Responsible person |
| `direct_cause` | Text | Yes | - | Direct cause |
| `corrective_action` | Text | Yes | - | Corrective action |
| `corrective_deadline` | Date | Yes | - | Corrective action deadline |
| `root_cause` | Text | Yes | - | Root cause |
| `corrective_plan` | Text | Yes | - | Corrective plan and documentation |
| `responsible_user_id` | Integer | Yes | - | FK -> User (responsible) |
| `completed_on_time` | Boolean | Yes | - | Completed on time? |
| `fully_implemented` | Boolean | Yes | - | Fully implemented? |
| `control_notes` | Text | Yes | - | Control notes |
| `manager_id` | Integer | Yes | - | FK -> User (manager) |
| `status` | String(20) | Yes | `'pending'` | Status: `pending`, `investigating`, `reviewed`, `closed` |

**Indexes:** `record_no` (unique), `status`
**Relationships:**
- `detector_user` -> User
- `responsible_user` -> User
- `manager` -> User

---

### 2.6 ControlStandard

**Table name:** `control_standards`
**Purpose:** QC control standards with target mean and standard deviation values for each analysis parameter.

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| `id` | Integer | No | Auto | Primary key |
| `name` | String(100) | No | - | Standard name (e.g., "CM-2025-Q4") |
| `created_at` | DateTime | Yes | `now_mn` | Created timestamp |
| `is_active` | Boolean | Yes | `False` | Currently in use? |
| `targets` | JSON | Yes | `{}` | Target values: `{"Aad": {"mean": 24.22, "sd": 0.22}, ...}` |

---

### 2.7 GbwStandard

**Table name:** `gbw_standards`
**Purpose:** GBW (National Standard Reference Material) certified values for analysis verification.

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| `id` | Integer | No | Auto | Primary key |
| `name` | String(50) | No | - | GBW batch number |
| `targets` | JSON | No | - | Target values: `{"Mad": {"mean": 1.2, "sd": 0.1}, ...}` |
| `is_active` | Boolean | Yes | `False` | Currently active? |
| `created_at` | DateTime | Yes | `datetime.utcnow` | Created timestamp |

---

### 2.8 EnvironmentalLog

**Table name:** `environmental_log`
**Purpose:** Laboratory environmental condition monitoring per ISO 17025 Clause 6.3.3.

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| `id` | Integer | No | Auto | Primary key |
| `log_date` | DateTime | Yes | `now_mn` | Log date/time |
| `location` | String(100) | Yes | - | Location: Sample storage, Analysis room, Furnace room |
| `temperature` | Float | Yes | - | Temperature in Celsius |
| `humidity` | Float | Yes | - | Relative humidity in % |
| `pressure` | Float | Yes | - | Atmospheric pressure in kPa (optional) |
| `temp_min` | Float | Yes | - | Minimum acceptable temperature |
| `temp_max` | Float | Yes | - | Maximum acceptable temperature |
| `humidity_min` | Float | Yes | - | Minimum acceptable humidity |
| `humidity_max` | Float | Yes | - | Maximum acceptable humidity |
| `within_limits` | Boolean | Yes | `True` | Within acceptable limits? |
| `recorded_by_id` | Integer | Yes | - | FK -> User |
| `notes` | Text | Yes | - | Notes |

**Indexes:** `log_date`
**Relationships:**
- `recorded_by` -> User

---

### 2.9 QCControlChart

**Table name:** `qc_control_chart`
**Purpose:** QC control chart data points per ISO 17025 Clause 7.7.1 for statistical process control.

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| `id` | Integer | No | Auto | Primary key |
| `analysis_code` | String(50) | Yes | - | Analysis code |
| `qc_sample_name` | String(100) | Yes | - | QC sample name |
| `target_value` | Float | Yes | - | Target (center line) value |
| `ucl` | Float | Yes | - | Upper control limit (target + 2*SD) |
| `lcl` | Float | Yes | - | Lower control limit (target - 2*SD) |
| `usl` | Float | Yes | - | Upper spec limit (optional) |
| `lsl` | Float | Yes | - | Lower spec limit (optional) |
| `measurement_date` | Date | Yes | - | Measurement date |
| `measured_value` | Float | Yes | - | Measured value |
| `in_control` | Boolean | Yes | `True` | Within UCL/LCL? |
| `operator_id` | Integer | Yes | - | FK -> User |
| `notes` | Text | Yes | - | Notes |

**Indexes:** `analysis_code`, `measurement_date`
**Relationships:**
- `operator` -> User

---

### 2.10 Bottle

**Table name:** `bottle`
**Purpose:** Pycnometer (bottle) registration for true relative density determination.

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| `id` | Integer | No | Auto | Primary key |
| `serial_no` | String(64) | No | - | Serial number (unique) |
| `label` | String(64) | Yes | - | Label / display name |
| `is_active` | Boolean | No | `True` | Active status |
| `created_by_id` | Integer | Yes | - | FK -> User |
| `created_at` | DateTime | No | `now_mn` | Created timestamp |

**Indexes:** `serial_no` (unique), `created_by_id`
**Relationships:**
- `constants` -> BottleConstant (one-to-many, cascade delete-orphan, dynamic)

---

### 2.11 BottleConstant

**Table name:** `bottle_constant`
**Purpose:** Pycnometer constant values (3-trial average) with approval workflow per MNS 656:2019.

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| `id` | Integer | No | Auto | Primary key |
| `bottle_id` | Integer | No | - | FK -> Bottle |
| `trial_1` | Float | No | - | First trial measurement |
| `trial_2` | Float | No | - | Second trial measurement |
| `trial_3` | Float | Yes | - | Third trial measurement (optional) |
| `avg_value` | Float | No | - | Average value (the constant) |
| `temperature_c` | Float | No | `20` | Temperature in Celsius |
| `effective_from` | DateTime | No | `now_mn` | Effective start date |
| `effective_to` | DateTime | Yes | - | Effective end date (optional) |
| `remarks` | String(255) | Yes | - | Remarks |
| `approved_by_id` | Integer | Yes | - | FK -> User (approver) |
| `approved_at` | DateTime | Yes | - | Approval timestamp |
| `created_by_id` | Integer | Yes | - | FK -> User (creator) |
| `created_at` | DateTime | No | `now_mn` | Created timestamp |

**Indexes:** `bottle_id`, `avg_value`, `approved_by_id`, `created_by_id`

---

## 3. Equipment Management

### 3.1 Equipment

**Table name:** `equipment`
**Purpose:** Laboratory equipment registry per ISO 17025 Section 6.4, with calibration tracking and categorization.

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| `id` | Integer | No | Auto | Primary key |
| `name` | String(150) | No | - | Equipment name |
| `manufacturer` | String(100) | Yes | - | Manufacturer |
| `model` | String(100) | Yes | - | Model designation |
| `serial_number` | String(100) | Yes | - | Official serial number |
| `lab_code` | String(50) | Yes | - | Internal lab code |
| `quantity` | Integer | Yes | `1` | Quantity |
| `location` | String(50) | Yes | - | Lab location |
| `room_number` | String(50) | Yes | - | Room number |
| `related_analysis` | String(200) | Yes | - | Related analysis codes (comma-separated) |
| `status` | String(20) | Yes | `'normal'` | Status: `normal`, `broken`, `needs_spare`, `maintenance`, `retired` |
| `calibration_date` | Date | Yes | - | Last calibration date |
| `calibration_cycle_days` | Integer | Yes | `365` | Calibration cycle in days |
| `next_calibration_date` | Date | Yes | - | Next calibration due date |
| `calibration_note` | String(200) | Yes | - | Calibration notes |
| `category` | String(50) | Yes | `'other'` | Category: `furnace`, `prep`, `analysis`, `balance`, `water`, `micro`, `wtl`, `other` |
| `manufactured_info` | String(20) | Yes | - | Manufacturing date (text) |
| `commissioned_info` | String(20) | Yes | - | Commissioning date (text) |
| `initial_price` | Float | Yes | - | Initial purchase price |
| `residual_price` | Float | Yes | - | Residual value |
| `remark` | String(255) | Yes | - | Remarks |
| `register_type` | String(30) | Yes | `'main'` | Register type: `main`, `measurement`, `glassware`, `internal_check`, `new_equipment`, `out_of_service`, `spares`, `balances` |
| `extra_data` | JSON | Yes | - | Register-specific extra fields |
| `created_at` | DateTime | Yes | `now_mn` | Created timestamp |
| `updated_at` | DateTime | Yes | `now_mn` | Last updated timestamp |
| `created_by_id` | Integer | Yes | - | FK -> User |

**Indexes:** `status`, `category`, `register_type`
**Relationships:**
- `created_by` -> User (many-to-one)
- `logs` -> MaintenanceLog (one-to-many, cascade delete-orphan, ordered by desc action_date)
- `usages` -> UsageLog (one-to-many, cascade delete-orphan)

---

### 3.2 MaintenanceLog

**Table name:** `maintenance_logs`
**Purpose:** Equipment maintenance, calibration, and daily check history records.

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| `id` | Integer | No | Auto | Primary key |
| `equipment_id` | Integer | Yes | - | FK -> Equipment |
| `action_date` | DateTime | Yes | `now_mn` | Action date/time |
| `action_type` | String(50) | Yes | - | Type: `Calibration`, `Repair`, `Maintenance`, `Daily Check` |
| `description` | Text | Yes | - | Description of action taken |
| `performed_by` | String(50) | Yes | - | Performer name (external) |
| `performed_by_id` | Integer | Yes | - | FK -> User (internal user) |
| `certificate_no` | String(50) | Yes | - | Certificate number |
| `result` | String(20) | Yes | - | Result: `Pass`, `Fail`, `Warning` |
| `file_path` | String(256) | Yes | - | Attached certificate file path |
| `created_at` | DateTime | Yes | `now_mn` | Created timestamp |

**Indexes:** `equipment_id`, `action_date`, `performed_by_id`
**Relationships:**
- `equipment` -> Equipment (many-to-one, via backref)
- `performed_by_user` -> User (many-to-one)

---

### 3.3 UsageLog

**Table name:** `usage_logs`
**Purpose:** Equipment usage duration tracking for utilization statistics.

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| `id` | Integer | No | Auto | Primary key |
| `equipment_id` | Integer | Yes | - | FK -> Equipment |
| `sample_id` | Integer | Yes | - | FK -> Sample (SET NULL on delete) |
| `start_time` | DateTime | Yes | - | Usage start time |
| `end_time` | DateTime | Yes | - | Usage end time |
| `duration_minutes` | Integer | Yes | - | Total minutes used |
| `used_by` | String(100) | Yes | - | User name (legacy, backward compat) |
| `used_by_id` | Integer | Yes | - | FK -> User (internal user) |
| `purpose` | String(255) | Yes | - | Purpose of usage |
| `created_at` | DateTime | Yes | `now_mn` | Created timestamp |

**Indexes:** `equipment_id`, `sample_id`, `used_by_id`
**Relationships:**
- `equipment` -> Equipment (many-to-one, via backref)
- `used_by_user` -> User (many-to-one)

---

## 4. Chemicals & Reagents

### 4.1 Chemical

**Table name:** `chemical`
**Purpose:** Chemical reagent inventory with hazard tracking, expiry management, and multi-lab categorization.

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| `id` | Integer | No | Auto | Primary key |
| `name` | String(200) | No | - | Chemical name |
| `cas_number` | String(50) | Yes | - | CAS registry number |
| `formula` | String(100) | Yes | - | Chemical formula |
| `manufacturer` | String(150) | Yes | - | Manufacturer |
| `supplier` | String(150) | Yes | - | Supplier |
| `catalog_number` | String(100) | Yes | - | Catalog number |
| `lot_number` | String(100) | Yes | - | Lot/batch number |
| `grade` | String(50) | Yes | - | Grade: AR, CP, HPLC, ACS |
| `quantity` | Float | Yes | `0` | Current quantity |
| `unit` | String(20) | Yes | `'mL'` | Unit: mL, g, L, kg, pcs |
| `reorder_level` | Float | Yes | - | Reorder threshold |
| `received_date` | Date | Yes | - | Date received |
| `expiry_date` | Date | Yes | - | Expiry date |
| `opened_date` | Date | Yes | - | Date opened |
| `storage_location` | String(100) | Yes | - | Storage location |
| `storage_conditions` | String(200) | Yes | - | Storage conditions |
| `hazard_class` | String(100) | Yes | - | Hazard classification |
| `sds_file_path` | String(255) | Yes | - | Safety Data Sheet file path |
| `lab_type` | String(30) | Yes | `'all'` | Lab type: `coal`, `water`, `microbiology`, `petrography`, `all` |
| `category` | String(30) | Yes | `'other'` | Category: `acid`, `base`, `solvent`, `indicator`, `standard`, `media`, `buffer`, `salt`, `other` |
| `status` | String(20) | Yes | `'active'` | Status: `active`, `low_stock`, `expired`, `empty`, `disposed` |
| `notes` | Text | Yes | - | Notes |
| `created_at` | DateTime | Yes | `now_mn` | Created timestamp |
| `updated_at` | DateTime | Yes | `now_mn` | Last updated timestamp |
| `created_by_id` | Integer | Yes | - | FK -> User |

**Indexes:** `name`, `expiry_date`, `lab_type`, `category`, `status`, `created_by_id`
**Relationships:**
- `usages` -> ChemicalUsage (one-to-many, cascade delete-orphan, dynamic)
- `logs` -> ChemicalLog (one-to-many, cascade delete-orphan, dynamic)
- `created_by` -> User

---

### 4.2 ChemicalUsage

**Table name:** `chemical_usage`
**Purpose:** Chemical consumption records linked to specific samples and analyses.

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| `id` | Integer | No | Auto | Primary key |
| `chemical_id` | Integer | No | - | FK -> Chemical |
| `quantity_used` | Float | No | - | Quantity consumed |
| `unit` | String(20) | Yes | - | Unit |
| `sample_id` | Integer | Yes | - | FK -> Sample (SET NULL on delete) |
| `analysis_code` | String(50) | Yes | - | Analysis code |
| `purpose` | String(255) | Yes | - | Purpose of usage |
| `used_by_id` | Integer | Yes | - | FK -> User |
| `used_at` | DateTime | Yes | `now_mn` | Usage timestamp |
| `quantity_before` | Float | Yes | - | Quantity before usage |
| `quantity_after` | Float | Yes | - | Quantity after usage |

**Indexes:** `chemical_id`, `used_by_id`, `used_at`
**Relationships:**
- `chemical` -> Chemical (via backref)
- `used_by` -> User
- `sample` -> Sample

---

### 4.3 ChemicalLog

**Table name:** `chemical_log`
**Purpose:** Chemical audit trail with SHA-256 hash integrity (HashableMixin).

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| `id` | Integer | No | Auto | Primary key |
| `chemical_id` | Integer | No | - | FK -> Chemical |
| `timestamp` | DateTime | Yes | `now_mn` | Action timestamp |
| `user_id` | Integer | Yes | - | FK -> User |
| `action` | String(30) | No | - | Action: `created`, `updated`, `received`, `consumed`, `disposed`, `adjusted` |
| `quantity_change` | Float | Yes | - | Quantity change (+/-) |
| `quantity_before` | Float | Yes | - | Quantity before |
| `quantity_after` | Float | Yes | - | Quantity after |
| `details` | Text | Yes | - | Details (JSON or text) |
| `data_hash` | String(64) | Yes | - | SHA-256 integrity hash |

**Indexes:** `chemical_id`, `timestamp`, `user_id`, `action`
**Composite Indexes:**
- `ix_chemical_log_chemical_timestamp` (chemical_id, timestamp)

**Relationships:**
- `chemical` -> Chemical (via backref)
- `user` -> User

---

### 4.4 ChemicalWaste

**Table name:** `chemical_waste`
**Purpose:** Chemical and hazardous waste type registry with disposal method tracking.

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| `id` | Integer | No | Auto | Primary key |
| `name_mn` | String(255) | No | - | Waste name (Mongolian) |
| `name_en` | String(255) | Yes | - | Waste name (English) |
| `monthly_amount` | Float | Yes | - | Average monthly amount |
| `unit` | String(20) | Yes | `'l'` | Unit (l, kg, pcs, ml) |
| `disposal_method` | String(50) | Yes | - | Method: `sewer`, `evaporate`, `special`, `incinerate` |
| `disposal_location` | String(255) | Yes | - | Disposal location |
| `is_hazardous` | Boolean | Yes | `True` | Is hazardous waste? |
| `hazard_type` | String(100) | Yes | - | Hazard type: corrosive, toxic, flammable, etc. |
| `lab_type` | String(30) | Yes | `'all'` | Lab type |
| `is_active` | Boolean | Yes | `True` | Active status |
| `notes` | Text | Yes | - | Notes |
| `created_at` | DateTime | Yes | `now_mn` | Created timestamp |
| `created_by_id` | Integer | Yes | - | FK -> User |

**Relationships:**
- `created_by` -> User
- `records` -> ChemicalWasteRecord (one-to-many, dynamic)

---

### 4.5 ChemicalWasteRecord

**Table name:** `chemical_waste_record`
**Purpose:** Monthly waste quantity records with starting and ending balance tracking.

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| `id` | Integer | No | Auto | Primary key |
| `waste_id` | Integer | No | - | FK -> ChemicalWaste |
| `year` | Integer | No | - | Year |
| `month` | Integer | No | - | Month (1-12) |
| `quantity` | Float | Yes | `0` | Quantity disposed this month |
| `starting_balance` | Float | Yes | `0` | Starting balance |
| `ending_balance` | Float | Yes | `0` | Ending balance |
| `notes` | Text | Yes | - | Notes |
| `recorded_at` | DateTime | Yes | `now_mn` | Recorded timestamp |
| `recorded_by_id` | Integer | Yes | - | FK -> User |

**Indexes:** `waste_id`, `year`, `month`
**Composite Indexes:**
- `ix_waste_record_year_month` (year, month)

**Constraints:**
- UNIQUE `uq_waste_year_month` (waste_id, year, month)

**Relationships:**
- `waste` -> ChemicalWaste (many-to-one)
- `recorded_by` -> User

---

## 5. Spare Parts Inventory

### 5.1 SparePartCategory

**Table name:** `spare_part_category`
**Purpose:** Spare part categories organized by equipment type.

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| `id` | Integer | No | Auto | Primary key |
| `code` | String(50) | No | - | Category code (unique) |
| `name` | String(150) | No | - | Category name |
| `name_en` | String(150) | Yes | - | English name |
| `description` | Text | Yes | - | Description |
| `sort_order` | Integer | Yes | `0` | Display sort order |
| `is_active` | Boolean | Yes | `True` | Active status |
| `created_at` | DateTime | Yes | `now_mn` | Created timestamp |
| `equipment_id` | Integer | Yes | - | FK -> Equipment (SET NULL on delete) |

**Indexes:** `code` (unique)
**Relationships:**
- `equipment` -> Equipment

---

### 5.2 SparePart

**Table name:** `spare_part`
**Purpose:** Spare part inventory with stock management and low-stock alerts.

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| `id` | Integer | No | Auto | Primary key |
| `name` | String(200) | No | - | Spare part name |
| `name_en` | String(200) | Yes | - | English name |
| `part_number` | String(100) | Yes | - | Part/catalog number |
| `description` | Text | Yes | - | Description |
| `manufacturer` | String(150) | Yes | - | Manufacturer |
| `supplier` | String(150) | Yes | - | Supplier |
| `quantity` | Float | Yes | `0` | Current stock quantity |
| `unit` | String(20) | Yes | `'pcs'` | Unit: pcs, set, box, roll, m, pack |
| `reorder_level` | Float | Yes | `1` | Reorder threshold |
| `unit_price` | Float | Yes | - | Unit price |
| `storage_location` | String(150) | Yes | - | Storage location |
| `image_path` | String(255) | Yes | - | Image file path |
| `compatible_equipment` | Text | Yes | - | Compatible equipment (text) |
| `equipment_id` | Integer | Yes | - | FK -> Equipment (SET NULL on delete) |
| `usage_life_months` | Integer | Yes | - | Expected usage life in months |
| `received_date` | Date | Yes | - | Last received date |
| `last_used_date` | Date | Yes | - | Last used date |
| `category` | String(50) | Yes | `'general'` | Category: `general`, `filter`, `belt`, `lamp`, `fuse`, `bearing`, `seal`, `tube`, `sensor`, `other` |
| `status` | String(20) | Yes | `'active'` | Status: `active`, `low_stock`, `out_of_stock` |
| `created_at` | DateTime | Yes | `now_mn` | Created timestamp |
| `created_by_id` | Integer | Yes | - | FK -> User |

**Indexes:** `name`, `part_number`, `equipment_id`, `category`, `status`
**Relationships:**
- `created_by` -> User
- `equipment` -> Equipment
- `usages` -> SparePartUsage (one-to-many, dynamic)
- `logs` -> SparePartLog (one-to-many, dynamic)

---

### 5.3 SparePartUsage

**Table name:** `spare_part_usage`
**Purpose:** Spare part consumption records linked to equipment and maintenance logs.

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| `id` | Integer | No | Auto | Primary key |
| `spare_part_id` | Integer | No | - | FK -> SparePart (CASCADE delete) |
| `equipment_id` | Integer | Yes | - | FK -> Equipment (SET NULL on delete) |
| `maintenance_log_id` | Integer | Yes | - | FK -> MaintenanceLog (SET NULL on delete) |
| `quantity_used` | Float | No | - | Quantity used |
| `unit` | String(20) | Yes | - | Unit |
| `purpose` | String(255) | Yes | - | Purpose |
| `used_by_id` | Integer | Yes | - | FK -> User |
| `used_at` | DateTime | Yes | `now_mn` | Usage timestamp |
| `quantity_before` | Float | Yes | - | Quantity before |
| `quantity_after` | Float | Yes | - | Quantity after |
| `notes` | Text | Yes | - | Notes |

**Indexes:** `spare_part_id`, `equipment_id`, `used_by_id`
**Relationships:**
- `spare_part` -> SparePart (via backref)
- `used_by` -> User
- `equipment` -> Equipment
- `maintenance_log` -> MaintenanceLog

---

### 5.4 SparePartLog

**Table name:** `spare_part_log`
**Purpose:** Spare part audit trail with SHA-256 hash integrity (HashableMixin).

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| `id` | Integer | No | Auto | Primary key |
| `spare_part_id` | Integer | No | - | FK -> SparePart (CASCADE delete) |
| `action` | String(30) | No | - | Action: `created`, `updated`, `received`, `consumed`, `adjusted`, `disposed` |
| `quantity_change` | Float | Yes | - | Quantity change (+/-) |
| `quantity_before` | Float | Yes | - | Quantity before |
| `quantity_after` | Float | Yes | - | Quantity after |
| `user_id` | Integer | Yes | - | FK -> User |
| `timestamp` | DateTime | Yes | `now_mn` | Action timestamp |
| `details` | Text | Yes | - | Details |
| `data_hash` | String(64) | Yes | - | SHA-256 integrity hash |

**Indexes:** `spare_part_id`, `action`, `user_id`, `timestamp`
**Relationships:**
- `spare_part` -> SparePart (via backref)
- `user` -> User

---

## 6. Audit & Logging

### 6.1 AuditLog

**Table name:** `audit_log`
**Purpose:** System-wide audit log for all critical operations with SHA-256 hash integrity (HashableMixin).

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| `id` | Integer | No | Auto | Primary key |
| `timestamp` | DateTime | No | `now_mn` | Action timestamp |
| `user_id` | Integer | Yes | - | FK -> User |
| `action` | String(50) | No | - | Action type: `login`, `logout`, `delete_sample`, `create_user`, `delete_user`, `update_settings`, `approve_result`, `reject_result` |
| `resource_type` | String(50) | Yes | - | Resource: `Sample`, `User`, `Equipment`, `AnalysisResult` |
| `resource_id` | Integer | Yes | - | ID of affected resource |
| `details` | Text | Yes | - | Details as JSON |
| `ip_address` | String(50) | Yes | - | Client IP address |
| `user_agent` | String(200) | Yes | - | Client user agent |
| `data_hash` | String(64) | Yes | - | SHA-256 integrity hash |

**Indexes:** `timestamp`, `user_id`, `action`, `resource_type`
**Relationships:**
- `user` -> User (many-to-one)

---

### 6.2 AnalysisResultLog

**Table name:** `analysis_result_log`
**Purpose:** Analysis result change history / audit trail with SHA-256 hash integrity (HashableMixin) per ISO 17025.

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| `id` | Integer | No | Auto | Primary key |
| `timestamp` | DateTime | No | `now_mn` | Action timestamp |
| `user_id` | Integer | No | - | FK -> User (who performed action) |
| `sample_id` | Integer | Yes | - | FK -> Sample (SET NULL on delete) |
| `analysis_result_id` | Integer | Yes | - | FK -> AnalysisResult (SET NULL on delete) |
| `analysis_code` | String(50) | No | - | Analysis code |
| `original_user_id` | Integer | Yes | - | FK -> User (original analyst, immutable) |
| `original_timestamp` | DateTime | Yes | - | Original creation timestamp (immutable) |
| `sample_code_snapshot` | String(100) | Yes | - | Sample code snapshot (preserved if sample deleted) |
| `data_hash` | String(64) | Yes | - | SHA-256 integrity hash |
| `action` | String(50) | No | - | Action: `created`, `updated`, `approved`, `rejected`, `reanalysis` |
| `raw_data_snapshot` | Text | Yes | - | Raw data snapshot as JSON |
| `final_result_snapshot` | Float | Yes | - | Final result snapshot |
| `rejection_category` | String(100) | Yes | - | Rejection category |
| `rejection_subcategory` | String(100) | Yes | - | Rejection subcategory |
| `reason` | String(255) | Yes | - | Reason / comment |
| `error_reason` | String(50) | Yes | - | KPI error reason |

**Indexes:** `timestamp`, `user_id`, `sample_id`, `analysis_result_id`, `analysis_code`, `action`
**Composite Indexes:**
- `ix_result_log_code_timestamp` (analysis_code, timestamp)
- `ix_result_log_sample_timestamp` (sample_id, timestamp)
- `ix_result_log_user_timestamp` (user_id, timestamp)

**Relationships:**
- `user` -> User (many-to-one)
- `original_user` -> User (many-to-one)
- `result` -> AnalysisResult (many-to-one, back_populates)

---

## 7. Washability & Yield

### 7.1 WashabilityTest

**Table name:** `washability_test`
**Purpose:** Float-sink washability analysis test records for coal beneficiation.

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| `id` | Integer | No | Auto | Primary key |
| `lab_number` | String(50) | Yes | - | Lab number (e.g., "#25_45") |
| `sample_name` | String(100) | Yes | - | Sample name |
| `sample_date` | Date | Yes | - | Sample date |
| `report_date` | Date | Yes | - | Report date |
| `consignor` | String(100) | Yes | - | Consignor name |
| `initial_mass_kg` | Float | Yes | - | Initial mass in kg |
| `raw_tm` | Float | Yes | - | Raw coal total moisture % |
| `raw_im` | Float | Yes | - | Raw coal inherent moisture % |
| `raw_ash` | Float | Yes | - | Raw coal ash (ad) % |
| `raw_vol` | Float | Yes | - | Raw coal volatiles (ad) % |
| `raw_sulphur` | Float | Yes | - | Raw coal sulphur (ad) % |
| `raw_csn` | Float | Yes | - | Raw coal CSN |
| `raw_gi` | Float | Yes | - | Raw coal G index |
| `raw_trd` | Float | Yes | - | Raw coal TRD |
| `sample_id` | Integer | Yes | - | FK -> Sample (SET NULL on delete) |
| `source` | String(50) | Yes | `'excel'` | Data source: `excel` or `lims` |
| `excel_filename` | String(255) | Yes | - | Source Excel filename |
| `created_at` | DateTime | Yes | `now_mn` | Created timestamp |
| `created_by_id` | Integer | Yes | - | FK -> User |

**Indexes:** `lab_number`, `sample_name`, `sample_date`
**Relationships:**
- `sample` -> Sample (many-to-one)
- `created_by` -> User
- `fractions` -> WashabilityFraction (one-to-many, cascade delete-orphan, dynamic)
- `yields` -> TheoreticalYield (one-to-many, cascade delete-orphan, dynamic)
- `plant_yields` -> PlantYield (backref, one-to-many)

---

### 7.2 WashabilityFraction

**Table name:** `washability_fraction`
**Purpose:** Individual size/density fraction data points within a washability test.

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| `id` | Integer | No | Auto | Primary key |
| `test_id` | Integer | No | - | FK -> WashabilityTest (CASCADE delete) |
| `size_fraction` | String(20) | Yes | - | Size fraction label (e.g., "-50+16") |
| `size_upper` | Float | Yes | - | Upper size bound (mm) |
| `size_lower` | Float | Yes | - | Lower size bound (mm) |
| `size_mass_kg` | Float | Yes | - | Total mass of this size fraction (kg) |
| `density_sink` | Float | Yes | - | Sink density |
| `density_float` | Float | Yes | - | Float density |
| `mass_gram` | Float | Yes | - | Fraction mass (g) |
| `mass_percent` | Float | Yes | - | Mass percentage within size fraction |
| `im_percent` | Float | Yes | - | Inherent moisture % |
| `ash_ad` | Float | Yes | - | Ash (ad) % |
| `vol_ad` | Float | Yes | - | Volatiles (ad) % |
| `sulphur_ad` | Float | Yes | - | Sulphur (ad) % |
| `csn` | Float | Yes | - | CSN |
| `cumulative_yield` | Float | Yes | - | Cumulative yield % |
| `cumulative_ash` | Float | Yes | - | Cumulative ash % |

**Indexes:** `test_id`
**Relationships:**
- `test` -> WashabilityTest (many-to-one, back_populates)

---

### 7.3 TheoreticalYield

**Table name:** `theoretical_yield`
**Purpose:** Theoretical yield calculation results at target ash levels from washability curve interpolation.

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| `id` | Integer | No | Auto | Primary key |
| `test_id` | Integer | No | - | FK -> WashabilityTest (CASCADE delete) |
| `target_ash` | Float | No | - | Target ash percentage |
| `size_fraction` | String(20) | Yes | - | Size fraction (or `'all'`) |
| `theoretical_yield` | Float | Yes | - | Theoretical yield % |
| `actual_yield` | Float | Yes | - | Actual plant yield (if available) |
| `recovery_efficiency` | Float | Yes | - | actual / theoretical * 100 |
| `ngm_plus_01` | Float | Yes | - | Near gravity material at +/-0.1 density |
| `ngm_plus_02` | Float | Yes | - | Near gravity material at +/-0.2 density |
| `separation_density` | Float | Yes | - | Separation density to achieve target ash |
| `calculated_at` | DateTime | Yes | `now_mn` | Calculation timestamp |
| `notes` | Text | Yes | - | Notes |

**Indexes:** `test_id`
**Relationships:**
- `test` -> WashabilityTest (many-to-one, back_populates)

---

### 7.4 PlantYield

**Table name:** `plant_yield`
**Purpose:** Actual plant production yield data for comparison with theoretical calculations.

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| `id` | Integer | No | Auto | Primary key |
| `production_date` | Date | No | - | Production date |
| `shift` | String(20) | Yes | - | Shift: Day, Night, etc. |
| `coal_source` | String(100) | Yes | - | Coal source (pit, seam) |
| `product_type` | String(50) | Yes | - | Product type: HCC, SSCC, MASHCC |
| `feed_tonnes` | Float | Yes | - | Feed tonnage |
| `product_tonnes` | Float | Yes | - | Product tonnage |
| `actual_yield` | Float | Yes | - | Actual yield % (product/feed*100) |
| `feed_ash` | Float | Yes | - | Feed ash % |
| `product_ash` | Float | Yes | - | Product ash % |
| `washability_test_id` | Integer | Yes | - | FK -> WashabilityTest (SET NULL on delete) |
| `theoretical_yield` | Float | Yes | - | Theoretical yield (from washability) |
| `recovery_efficiency` | Float | Yes | - | Recovery efficiency % |
| `created_at` | DateTime | Yes | `now_mn` | Created timestamp |
| `notes` | Text | Yes | - | Notes |

**Indexes:** `production_date`
**Relationships:**
- `washability_test` -> WashabilityTest (many-to-one)

---

## 8. Reports

### 8.1 ReportSignature

**Table name:** `report_signature`
**Purpose:** Signature and stamp image registry for lab report generation.

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| `id` | Integer | No | Auto | Primary key |
| `name` | String(100) | No | - | Name and title |
| `signature_type` | String(20) | No | - | Type: `signature` or `stamp` |
| `image_path` | String(255) | Yes | - | Image file path |
| `user_id` | Integer | Yes | - | FK -> User |
| `lab_type` | String(30) | Yes | `'all'` | Lab type |
| `is_active` | Boolean | Yes | `True` | Active status |
| `position` | String(100) | Yes | - | Job title / position |
| `created_at` | DateTime | Yes | `now_mn` | Created timestamp |

**Relationships:**
- `user` -> User

---

### 8.2 LabReport

**Table name:** `lab_report`
**Purpose:** Lab report records with PDF generation, approval workflow, and email dispatch.

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| `id` | Integer | No | Auto | Primary key |
| `report_number` | String(50) | No | - | Report number (unique, e.g., "2026_15") |
| `lab_type` | String(30) | No | - | Lab type |
| `report_type` | String(30) | Yes | `'analysis'` | Type: `analysis`, `summary`, `certificate` |
| `title` | String(255) | Yes | - | Report title |
| `status` | String(20) | Yes | `'draft'` | Status: `draft`, `pending_approval`, `approved`, `sent` |
| `sample_ids` | JSON | Yes | - | JSON array of related sample IDs |
| `date_from` | Date | Yes | - | Report period start |
| `date_to` | Date | Yes | - | Report period end |
| `report_data` | JSON | Yes | - | Report content data |
| `pdf_path` | String(255) | Yes | - | Generated PDF file path |
| `analyst_signature_id` | Integer | Yes | - | FK -> ReportSignature (analyst) |
| `manager_signature_id` | Integer | Yes | - | FK -> ReportSignature (manager) |
| `stamp_id` | Integer | Yes | - | FK -> ReportSignature (stamp) |
| `approved_by_id` | Integer | Yes | - | FK -> User (approver) |
| `approved_at` | DateTime | Yes | - | Approval timestamp |
| `email_sent` | Boolean | Yes | `False` | Email sent? |
| `email_sent_at` | DateTime | Yes | - | Email sent timestamp |
| `email_recipients` | Text | Yes | - | Comma-separated recipients |
| `notes` | Text | Yes | - | Notes |
| `created_by_id` | Integer | Yes | - | FK -> User |
| `created_at` | DateTime | Yes | `now_mn` | Created timestamp |
| `updated_at` | DateTime | Yes | `now_mn` | Last updated timestamp |

**Indexes:** `lab_type`, `status`
**Composite Indexes:**
- `ix_lab_report_lab_status` (lab_type, status)

**Constraints:**
- UNIQUE: `report_number`

**Relationships:**
- `analyst_signature` -> ReportSignature
- `manager_signature` -> ReportSignature
- `stamp` -> ReportSignature
- `approved_by` -> User
- `created_by` -> User

---

## 9. Solutions (Water Chemistry Lab)

### 9.1 SolutionPreparation

**Table name:** `solution_preparation`
**Purpose:** Solution preparation journal for water chemistry lab, including titer determination.

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| `id` | Integer | No | Auto | Primary key |
| `solution_name` | String(200) | No | - | Solution name (e.g., "HCl 0.1N") |
| `concentration` | Float | Yes | - | Concentration value |
| `concentration_unit` | String(20) | Yes | `'mg/L'` | Unit: `mg/L`, `mol/L`, `N`, `%` |
| `volume_ml` | Float | Yes | - | Volume prepared (mL) |
| `chemical_used_mg` | Float | Yes | - | Chemical used (mg) |
| `chemical_id` | Integer | Yes | - | FK -> Chemical (SET NULL on delete) |
| `recipe_id` | Integer | Yes | - | FK -> SolutionRecipe (SET NULL on delete) |
| `prepared_date` | Date | No | - | Preparation date |
| `expiry_date` | Date | Yes | - | Expiry date |
| `v1` | Float | Yes | - | Titer V1 measurement |
| `v2` | Float | Yes | - | Titer V2 measurement |
| `v3` | Float | Yes | - | Titer V3 measurement (optional) |
| `v_avg` | Float | Yes | - | Average titer volume |
| `titer_coefficient` | Float | Yes | - | Titer coefficient (K) |
| `preparation_notes` | Text | Yes | - | Preparation instructions / notes |
| `status` | String(20) | Yes | `'active'` | Status: `active`, `expired`, `empty` |
| `prepared_by_id` | Integer | Yes | - | FK -> User |
| `created_at` | DateTime | Yes | `now_mn` | Created timestamp |

**Indexes:** `solution_name`, `prepared_date`, `status`, `prepared_by_id`, `recipe_id`
**Relationships:**
- `prepared_by` -> User
- `chemical` -> Chemical
- `recipe` -> SolutionRecipe (via backref)

---

### 9.2 SolutionRecipe

**Table name:** `solution_recipe`
**Purpose:** Predefined solution preparation recipes with ingredient lists.

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| `id` | Integer | No | Auto | Primary key |
| `name` | String(200) | No | - | Recipe name (e.g., "Trilon B 0.05N") |
| `concentration` | Float | Yes | - | Target concentration |
| `concentration_unit` | String(20) | Yes | `'N'` | Unit: `N`, `M`, `%`, `mg/L` |
| `standard_volume_ml` | Float | Yes | `1000` | Standard volume (mL) |
| `preparation_notes` | Text | Yes | - | Detailed preparation instructions |
| `lab_type` | String(20) | Yes | `'water'` | Lab type |
| `category` | String(50) | Yes | - | Category: `titrant`, `buffer`, `indicator`, `standard`, `reagent` |
| `is_active` | Boolean | Yes | `True` | Active status |
| `created_at` | DateTime | Yes | `now_mn` | Created timestamp |
| `created_by_id` | Integer | Yes | - | FK -> User |

**Indexes:** `name`, `lab_type`
**Relationships:**
- `created_by` -> User
- `ingredients` -> SolutionRecipeIngredient (one-to-many, cascade delete-orphan, dynamic)
- `preparations` -> SolutionPreparation (one-to-many, dynamic)

---

### 9.3 SolutionRecipeIngredient

**Table name:** `solution_recipe_ingredient`
**Purpose:** Individual ingredient entries within a solution recipe.

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| `id` | Integer | No | Auto | Primary key |
| `recipe_id` | Integer | No | - | FK -> SolutionRecipe (CASCADE delete) |
| `chemical_id` | Integer | Yes | - | FK -> Chemical (SET NULL on delete) |
| `amount` | Float | No | - | Amount for standard volume |
| `unit` | String(20) | Yes | `'g'` | Unit: `g`, `mg`, `mL` |

**Relationships:**
- `recipe` -> SolutionRecipe (via backref)
- `chemical` -> Chemical

---

## 10. Planning & Staff

### 10.1 MonthlyPlan

**Table name:** `monthly_plan`
**Purpose:** Weekly sample planning by client and sample type for laboratory workload management.

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| `id` | Integer | No | Auto | Primary key |
| `year` | Integer | No | - | Year |
| `month` | Integer | No | - | Month (1-12) |
| `week` | Integer | No | - | Week number (1-5) |
| `client_name` | String(50) | No | - | Client/consignor |
| `sample_type` | String(100) | No | - | Sample type |
| `planned_count` | Integer | Yes | `0` | Planned sample count |
| `created_by_id` | Integer | Yes | - | FK -> User |
| `created_at` | DateTime | Yes | `now_mn` | Created timestamp |
| `updated_at` | DateTime | Yes | `now_mn` | Last updated timestamp |

**Indexes:** `year`, `month`, `client_name`
**Constraints:**
- UNIQUE `uq_monthly_plan_entry` (year, month, week, client_name, sample_type)

**Relationships:**
- `created_by` -> User

---

### 10.2 StaffSettings

**Table name:** `staff_settings`
**Purpose:** Monthly staff count configuration for workload calculations.

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| `id` | Integer | No | Auto | Primary key |
| `year` | Integer | No | - | Year |
| `month` | Integer | No | - | Month |
| `preparers` | Integer | Yes | `6` | Number of sample preparers |
| `chemists` | Integer | Yes | `10` | Number of chemists |
| `updated_at` | DateTime | Yes | `now_mn` | Last updated timestamp |

**Constraints:**
- UNIQUE `uq_staff_settings_month` (year, month)

---

## 11. Chat & Communication

### 11.1 ChatMessage

**Table name:** `chat_messages`
**Purpose:** Real-time chat messages between chemists and senior staff with file attachment support.

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| `id` | Integer | No | Auto | Primary key |
| `sender_id` | Integer | No | - | FK -> User (sender) |
| `receiver_id` | Integer | Yes | - | FK -> User (receiver, null = broadcast) |
| `message` | Text | No | - | Message content |
| `sent_at` | DateTime | Yes | `now_mn` | Sent timestamp |
| `read_at` | DateTime | Yes | - | Read timestamp |
| `message_type` | String(20) | Yes | `'text'` | Type: `text`, `image`, `file`, `sample`, `urgent` |
| `file_url` | String(500) | Yes | - | Attached file URL |
| `file_name` | String(255) | Yes | - | Attached file name |
| `file_size` | Integer | Yes | - | File size in bytes |
| `is_urgent` | Boolean | Yes | `False` | Urgent message flag |
| `sample_id` | Integer | Yes | - | FK -> Sample (SET NULL on delete) |
| `is_deleted` | Boolean | Yes | `False` | Soft delete flag |
| `deleted_at` | DateTime | Yes | - | Deletion timestamp |
| `is_broadcast` | Boolean | Yes | `False` | Broadcast message flag |

**Indexes:** `sender_id`, `receiver_id`, `sent_at`
**Relationships:**
- `sender` -> User
- `receiver` -> User
- `sample` -> Sample

---

### 11.2 UserOnlineStatus

**Table name:** `user_online_status`
**Purpose:** User online presence tracking for WebSocket-based real-time communication.

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| `user_id` | Integer | No | - | PK + FK -> User |
| `is_online` | Boolean | Yes | `False` | Currently online? |
| `last_seen` | DateTime | Yes | `now_mn` | Last activity timestamp |
| `socket_id` | String(100) | Yes | - | Current WebSocket session ID |

**Relationships:**
- `user` -> User (one-to-one via backref)

---

## 12. Settings & Configuration

### 12.1 SystemSetting

**Table name:** `system_setting`
**Purpose:** Flexible key-value configuration store with category-based organization.

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| `id` | Integer | No | Auto | Primary key |
| `category` | String(64) | No | - | Category: `error_reason`, `unit_abbr`, `sample_type`, `rejection_category`, etc. |
| `key` | String(128) | No | - | Setting key |
| `value` | Text | No | - | Setting value (may be JSON string) |
| `description` | String(256) | Yes | - | Description |
| `is_active` | Boolean | No | `True` | Active status |
| `sort_order` | Integer | Yes | `0` | Display order |
| `created_at` | DateTime | No | `now_mn` | Created timestamp |
| `updated_at` | DateTime | Yes | `now_mn` | Last updated timestamp |
| `updated_by_id` | Integer | Yes | - | FK -> User |

**Indexes:** `category`
**Constraints:**
- UNIQUE `uq_system_setting_category_key` (category, key)

---

## 13. License Management

### 13.1 SystemLicense

**Table name:** `system_license`
**Purpose:** Software license management with hardware binding and tamper detection.

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| `id` | Integer | No | Auto | Primary key |
| `license_key` | String(128) | No | - | License key (unique) |
| `company_name` | String(200) | No | - | Company name |
| `company_code` | String(50) | Yes | - | Company code |
| `issued_date` | DateTime | Yes | `datetime.utcnow` | Issue date |
| `expiry_date` | DateTime | No | - | Expiry date |
| `max_users` | Integer | Yes | `10` | Maximum concurrent users |
| `max_samples_per_month` | Integer | Yes | `10000` | Maximum samples per month |
| `hardware_id` | String(128) | Yes | - | Bound hardware ID |
| `allowed_hardware_ids` | Text | Yes | - | JSON array of allowed hardware IDs |
| `is_active` | Boolean | Yes | `True` | License active? |
| `is_trial` | Boolean | Yes | `False` | Trial license? |
| `last_check` | DateTime | Yes | - | Last validation check |
| `check_count` | Integer | Yes | `0` | Number of validation checks |
| `tampering_detected` | Boolean | Yes | `False` | Tampering detected? |
| `tampering_details` | Text | Yes | - | Tampering details |
| `created_at` | DateTime | Yes | `datetime.utcnow` | Created timestamp |
| `updated_at` | DateTime | Yes | `datetime.utcnow` | Last updated timestamp |

**Constraints:**
- UNIQUE: `license_key`

**Relationships:**
- `logs` -> LicenseLog (backref, one-to-many)

---

### 13.2 LicenseLog

**Table name:** `license_log`
**Purpose:** License event log for tracking all license-related operations.

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| `id` | Integer | No | Auto | Primary key |
| `license_id` | Integer | Yes | - | FK -> SystemLicense |
| `event_type` | String(50) | Yes | - | Event type |
| `event_details` | Text | Yes | - | Event details |
| `hardware_id` | String(128) | Yes | - | Hardware ID at time of event |
| `ip_address` | String(50) | Yes | - | IP address |
| `created_at` | DateTime | Yes | `datetime.utcnow` | Created timestamp |

**Relationships:**
- `license` -> SystemLicense (many-to-one)

---

## Entity Relationship Summary

### Primary Entity Relationships

| Parent Table | Child Table | Relationship | FK Column | On Delete |
|-------------|-------------|-------------|-----------|-----------|
| User | Sample | one-to-many | `sample.user_id` | - |
| Sample | AnalysisResult | one-to-many | `analysis_result.sample_id` | CASCADE (via ORM) |
| User | AnalysisResult | one-to-many | `analysis_result.user_id` | - |
| AnalysisResult | AnalysisResultLog | one-to-many | `analysis_result_log.analysis_result_id` | SET NULL |
| Sample | AnalysisResultLog | one-to-many | `analysis_result_log.sample_id` | SET NULL |
| User | AnalysisResultLog | one-to-many | `analysis_result_log.user_id` | - |
| Equipment | MaintenanceLog | one-to-many | `maintenance_logs.equipment_id` | CASCADE (via ORM) |
| Equipment | UsageLog | one-to-many | `usage_logs.equipment_id` | CASCADE (via ORM) |
| SparePart | SparePartUsage | one-to-many | `spare_part_usage.spare_part_id` | CASCADE |
| SparePart | SparePartLog | one-to-many | `spare_part_log.spare_part_id` | CASCADE |
| Chemical | ChemicalUsage | one-to-many | `chemical_usage.chemical_id` | CASCADE (via ORM) |
| Chemical | ChemicalLog | one-to-many | `chemical_log.chemical_id` | CASCADE (via ORM) |
| ChemicalWaste | ChemicalWasteRecord | one-to-many | `chemical_waste_record.waste_id` | - |
| Bottle | BottleConstant | one-to-many | `bottle_constant.bottle_id` | CASCADE (via ORM) |
| WashabilityTest | WashabilityFraction | one-to-many | `washability_fraction.test_id` | CASCADE |
| WashabilityTest | TheoreticalYield | one-to-many | `theoretical_yield.test_id` | CASCADE |
| WashabilityTest | PlantYield | one-to-many | `plant_yield.washability_test_id` | SET NULL |
| Sample | WashabilityTest | one-to-many | `washability_test.sample_id` | SET NULL |
| SolutionRecipe | SolutionRecipeIngredient | one-to-many | `solution_recipe_ingredient.recipe_id` | CASCADE |
| SolutionRecipe | SolutionPreparation | one-to-many | `solution_preparation.recipe_id` | SET NULL |
| SystemLicense | LicenseLog | one-to-many | `license_log.license_id` | - |
| User | AuditLog | one-to-many | `audit_log.user_id` | - |
| User | ChatMessage (sender) | one-to-many | `chat_messages.sender_id` | - |
| User | ChatMessage (receiver) | one-to-many | `chat_messages.receiver_id` | - |
| Sample | ChatMessage | one-to-many | `chat_messages.sample_id` | SET NULL |
| User | UserOnlineStatus | one-to-one | `user_online_status.user_id` | - |
| CustomerComplaint | ImprovementRecord | one-to-many | `improvement_record.source_complaint_id` | - |
| CorrectiveAction | CustomerComplaint | one-to-many | `customer_complaint.capa_id` | - |
| Sample | CustomerComplaint | one-to-many | `customer_complaint.related_sample_id` | SET NULL |

### Cross-Domain References

| From | To | Via Column | Purpose |
|------|----|-----------|---------|
| SparePartCategory | Equipment | `equipment_id` | Category linked to equipment |
| SparePart | Equipment | `equipment_id` | Part compatible with equipment |
| SparePartUsage | Equipment | `equipment_id` | Which equipment used the part |
| SparePartUsage | MaintenanceLog | `maintenance_log_id` | Which maintenance event |
| ChemicalUsage | Sample | `sample_id` | Chemical used on which sample |
| UsageLog | Sample | `sample_id` | Equipment used on which sample |
| SolutionPreparation | Chemical | `chemical_id` | Chemical used in solution |
| SolutionRecipeIngredient | Chemical | `chemical_id` | Chemical in recipe |
| ReportSignature | User | `user_id` | Signature belongs to user |
| LabReport | ReportSignature | `analyst_signature_id`, `manager_signature_id`, `stamp_id` | Report signatures |

---

## Mermaid ER Diagram

```mermaid
erDiagram
    %% ==================== CORE ====================
    User {
        int id PK
        string username UK
        string password_hash
        string role
        json allowed_labs
        string full_name
        string email
        string phone
        string position
    }

    Sample {
        int id PK
        string sample_code UK
        datetime received_date
        int user_id FK
        string status
        string lab_type
        date sample_date
        string client_name
        string sample_type
        string analyses_to_perform
        text notes
        float weight
        boolean return_sample
        boolean mass_ready
        string chem_lab_id
        string micro_lab_id
        date disposal_date
        date retention_date
    }

    AnalysisResult {
        int id PK
        int sample_id FK
        int user_id FK
        string analysis_code
        float final_result
        text raw_data
        string status
        string rejection_category
        string error_reason
        datetime created_at
        datetime updated_at
    }

    AnalysisType {
        int id PK
        string code UK
        string name
        int order_num
        string required_role
        string lab_type
    }

    AnalysisProfile {
        int id PK
        string profile_type
        string client_name
        string sample_type
        string pattern
        text analyses_json
        int priority
        string match_rule
    }

    %% ==================== AUDIT ====================
    AuditLog {
        int id PK
        datetime timestamp
        int user_id FK
        string action
        string resource_type
        int resource_id
        text details
        string ip_address
        string data_hash
    }

    AnalysisResultLog {
        int id PK
        datetime timestamp
        int user_id FK
        int sample_id FK
        int analysis_result_id FK
        string analysis_code
        string action
        text raw_data_snapshot
        float final_result_snapshot
        string data_hash
    }

    %% ==================== EQUIPMENT ====================
    Equipment {
        int id PK
        string name
        string manufacturer
        string model
        string serial_number
        string lab_code
        string status
        string category
        date calibration_date
        date next_calibration_date
        string register_type
        json extra_data
        int created_by_id FK
    }

    MaintenanceLog {
        int id PK
        int equipment_id FK
        datetime action_date
        string action_type
        text description
        string performed_by
        int performed_by_id FK
        string result
    }

    UsageLog {
        int id PK
        int equipment_id FK
        int sample_id FK
        datetime start_time
        datetime end_time
        int duration_minutes
        int used_by_id FK
    }

    %% ==================== SPARE PARTS ====================
    SparePartCategory {
        int id PK
        string code UK
        string name
        int equipment_id FK
        boolean is_active
    }

    SparePart {
        int id PK
        string name
        string part_number
        float quantity
        string unit
        float reorder_level
        string status
        string category
        int equipment_id FK
        int created_by_id FK
    }

    SparePartUsage {
        int id PK
        int spare_part_id FK
        int equipment_id FK
        int maintenance_log_id FK
        float quantity_used
        int used_by_id FK
    }

    SparePartLog {
        int id PK
        int spare_part_id FK
        string action
        float quantity_change
        int user_id FK
        datetime timestamp
        string data_hash
    }

    %% ==================== CHEMICALS ====================
    Chemical {
        int id PK
        string name
        string cas_number
        string formula
        float quantity
        string unit
        date expiry_date
        string lab_type
        string category
        string status
        int created_by_id FK
    }

    ChemicalUsage {
        int id PK
        int chemical_id FK
        float quantity_used
        int sample_id FK
        string analysis_code
        int used_by_id FK
    }

    ChemicalLog {
        int id PK
        int chemical_id FK
        string action
        float quantity_change
        int user_id FK
        datetime timestamp
        string data_hash
    }

    ChemicalWaste {
        int id PK
        string name_mn
        string name_en
        float monthly_amount
        string disposal_method
        boolean is_hazardous
        string lab_type
    }

    ChemicalWasteRecord {
        int id PK
        int waste_id FK
        int year
        int month
        float quantity
        float starting_balance
        float ending_balance
    }

    %% ==================== QUALITY ====================
    CorrectiveAction {
        int id PK
        string ca_number UK
        date issue_date
        string issue_source
        text issue_description
        string severity
        text root_cause
        string status
        int responsible_person_id FK
        int technical_manager_id FK
    }

    ProficiencyTest {
        int id PK
        string pt_provider
        string pt_program
        string analysis_code
        float our_result
        float assigned_value
        float z_score
        string performance
        int tested_by_id FK
    }

    CustomerComplaint {
        int id PK
        string complaint_no UK
        date complaint_date
        text complaint_content
        string status
        int complainant_user_id FK
        int receiver_user_id FK
        int quality_manager_id FK
        int related_sample_id FK
        int capa_id FK
    }

    ImprovementRecord {
        int id PK
        string record_no UK
        date record_date
        text activity_description
        string status
        int created_by_id FK
        int source_complaint_id FK
        int technical_manager_id FK
    }

    NonConformityRecord {
        int id PK
        string record_no UK
        date record_date
        text nc_description
        string status
        int detector_user_id FK
        int responsible_user_id FK
        int manager_id FK
    }

    ControlStandard {
        int id PK
        string name
        boolean is_active
        json targets
    }

    GbwStandard {
        int id PK
        string name
        json targets
        boolean is_active
    }

    EnvironmentalLog {
        int id PK
        datetime log_date
        string location
        float temperature
        float humidity
        boolean within_limits
        int recorded_by_id FK
    }

    QCControlChart {
        int id PK
        string analysis_code
        string qc_sample_name
        float target_value
        float measured_value
        boolean in_control
        int operator_id FK
    }

    Bottle {
        int id PK
        string serial_no UK
        string label
        boolean is_active
        int created_by_id FK
    }

    BottleConstant {
        int id PK
        int bottle_id FK
        float trial_1
        float trial_2
        float trial_3
        float avg_value
        float temperature_c
        int approved_by_id FK
        int created_by_id FK
    }

    %% ==================== WASHABILITY ====================
    WashabilityTest {
        int id PK
        string lab_number
        string sample_name
        date sample_date
        int sample_id FK
        string source
        int created_by_id FK
    }

    WashabilityFraction {
        int id PK
        int test_id FK
        string size_fraction
        float density_sink
        float density_float
        float mass_percent
        float ash_ad
        float cumulative_yield
    }

    TheoreticalYield {
        int id PK
        int test_id FK
        float target_ash
        float theoretical_yield
        float actual_yield
        float recovery_efficiency
    }

    PlantYield {
        int id PK
        date production_date
        string product_type
        float feed_tonnes
        float product_tonnes
        float actual_yield
        int washability_test_id FK
    }

    %% ==================== REPORTS ====================
    ReportSignature {
        int id PK
        string name
        string signature_type
        string image_path
        int user_id FK
        boolean is_active
    }

    LabReport {
        int id PK
        string report_number UK
        string lab_type
        string report_type
        string status
        json sample_ids
        string pdf_path
        int analyst_signature_id FK
        int manager_signature_id FK
        int stamp_id FK
        int approved_by_id FK
        int created_by_id FK
    }

    %% ==================== SOLUTIONS ====================
    SolutionRecipe {
        int id PK
        string name
        float concentration
        string concentration_unit
        float standard_volume_ml
        string lab_type
        boolean is_active
        int created_by_id FK
    }

    SolutionRecipeIngredient {
        int id PK
        int recipe_id FK
        int chemical_id FK
        float amount
        string unit
    }

    SolutionPreparation {
        int id PK
        string solution_name
        float concentration
        float volume_ml
        date prepared_date
        float titer_coefficient
        string status
        int prepared_by_id FK
        int chemical_id FK
        int recipe_id FK
    }

    %% ==================== PLANNING & CHAT ====================
    MonthlyPlan {
        int id PK
        int year
        int month
        int week
        string client_name
        string sample_type
        int planned_count
        int created_by_id FK
    }

    StaffSettings {
        int id PK
        int year
        int month
        int preparers
        int chemists
    }

    ChatMessage {
        int id PK
        int sender_id FK
        int receiver_id FK
        text message
        datetime sent_at
        datetime read_at
        string message_type
        int sample_id FK
        boolean is_broadcast
    }

    UserOnlineStatus {
        int user_id PK_FK
        boolean is_online
        datetime last_seen
        string socket_id
    }

    %% ==================== SETTINGS & LICENSE ====================
    SystemSetting {
        int id PK
        string category
        string key
        text value
        boolean is_active
        int updated_by_id FK
    }

    SystemLicense {
        int id PK
        string license_key UK
        string company_name
        datetime expiry_date
        int max_users
        boolean is_active
        boolean tampering_detected
    }

    LicenseLog {
        int id PK
        int license_id FK
        string event_type
        text event_details
        string hardware_id
    }

    %% ==================== RELATIONSHIPS ====================
    User ||--o{ Sample : "registers"
    User ||--o{ AnalysisResult : "performs"
    User ||--o{ AuditLog : "creates"
    User ||--o| UserOnlineStatus : "has"

    Sample ||--o{ AnalysisResult : "has results"
    Sample ||--o{ ChatMessage : "referenced in"
    Sample ||--o{ CustomerComplaint : "related to"
    Sample ||--o{ WashabilityTest : "linked to"

    AnalysisResult ||--o{ AnalysisResultLog : "has history"

    Equipment ||--o{ MaintenanceLog : "has logs"
    Equipment ||--o{ UsageLog : "has usage"

    SparePart ||--o{ SparePartUsage : "consumed"
    SparePart ||--o{ SparePartLog : "has audit"
    SparePartUsage }o--o| Equipment : "used on"
    SparePartUsage }o--o| MaintenanceLog : "during"

    Chemical ||--o{ ChemicalUsage : "consumed"
    Chemical ||--o{ ChemicalLog : "has audit"
    ChemicalUsage }o--o| Sample : "for"

    ChemicalWaste ||--o{ ChemicalWasteRecord : "has records"

    Bottle ||--o{ BottleConstant : "has constants"

    WashabilityTest ||--o{ WashabilityFraction : "has fractions"
    WashabilityTest ||--o{ TheoreticalYield : "has yields"
    WashabilityTest ||--o{ PlantYield : "compared with"

    CorrectiveAction ||--o{ CustomerComplaint : "source of"
    CustomerComplaint ||--o{ ImprovementRecord : "generates"

    SolutionRecipe ||--o{ SolutionRecipeIngredient : "has ingredients"
    SolutionRecipe ||--o{ SolutionPreparation : "used by"
    SolutionRecipeIngredient }o--o| Chemical : "uses"

    LabReport }o--o| ReportSignature : "analyst sig"
    LabReport }o--o| ReportSignature : "manager sig"
    LabReport }o--o| ReportSignature : "stamp"

    SystemLicense ||--o{ LicenseLog : "has logs"

    User ||--o{ ChatMessage : "sends"
    User ||--o{ MonthlyPlan : "creates"
    User ||--o{ CorrectiveAction : "assigned to"
    User ||--o{ ProficiencyTest : "tests"
    User ||--o{ EnvironmentalLog : "records"
    User ||--o{ QCControlChart : "measures"
    User ||--o{ NonConformityRecord : "detects"
    User ||--o{ ImprovementRecord : "creates"
```

---

*Generated from `app/models/models.py` -- 46 model classes (44 DB tables + HashableMixin + SampleCalculations)*
