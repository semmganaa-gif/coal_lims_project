# Coal LIMS - User and Administrator Guide

**Last Updated:** 2026-02-15
**Version:** 1.0
**System:** CORELINK LIMS (Laboratory Information Management System)

---

## Table of Contents

1. [System Overview](#1-system-overview)
2. [User Roles and Permissions](#2-user-roles-and-permissions)
3. [Getting Started](#3-getting-started)
4. [For Chemists (Sample Preparation & Analysis)](#4-for-chemists)
5. [For Senior Chemists (Review & QC)](#5-for-senior-chemists)
6. [For Managers (Oversight & Reporting)](#6-for-managers)
7. [For Administrators (System Management)](#7-for-administrators)
8. [FAQ and Common Issues](#8-faq-and-common-issues)

---

## 1. System Overview

CORELINK LIMS is a web-based Laboratory Information Management System developed for **Energy Resources LLC**. It manages the complete lifecycle of laboratory samples, from registration through analysis to final reporting, across four specialized laboratories.

### 1.1 Supported Laboratories

| Laboratory | Code | Purpose | Key Analysis Types |
|---|---|---|---|
| **Coal Lab** | `coal` | Coal quality testing | MT, Mad, Aad, Vad, CV, TS, CSN, Gi, TRD, CRI/CSR, and more (18 codes) |
| **Water Lab (Chemistry)** | `water` | Water chemistry analysis | PH, EC, COLOR, HARD, TDS, NH4, NO2, NO3, FE_W, F_W, CL_FREE, and more (32 parameters) |
| **Microbiology Lab** | `microbiology` | Microbiological testing | CFU (22C/37C), E. coli, Salmonella, Air/Swab tests (8 codes) |
| **Petrography Lab** | `petrography` | Petrographic analysis | Maceral (MAC), Vitrinite Reflectance (VR), Mineral Matter (MM), and more (7 codes) |

### 1.2 Core Capabilities

- **Sample Management:** Registration, tracking, editing, disposal, and retention management
- **Analysis Workspace:** Dedicated workspace per analysis type with parallel measurements, auto-calculation, and real-time validation
- **Quality Control:** Repeatability checks, control charts, Westgard rules, CAPA, and proficiency testing (ISO 17025 compliant)
- **Senior Review Workflow:** Approval/rejection of analysis results with full audit trail
- **Reporting:** Sample summary, Excel/CSV export, PDF certificates, and shift-based performance reports
- **Equipment Management:** Equipment registration, calibration tracking, maintenance schedules, and certificate storage
- **Audit Trail:** Every critical action is logged with hash-based integrity verification for ISO 17025 compliance

### 1.3 Technology

The system runs on Flask (Python) with a PostgreSQL database. The user interface uses Bootstrap 5 with responsive design (works on desktop, tablet, and mobile). Data grids use AG-Grid for interactive table features, and charts are rendered with Chart.js.

---

## 2. User Roles and Permissions

LIMS uses a role-based access control (RBAC) system with five roles. Each user is assigned exactly one role and may also be granted access to specific laboratories via the `allowed_labs` setting.

### 2.1 Role Definitions

| Role | Code | Description |
|---|---|---|
| **Sample Preparation** | `prep` | Registers new samples, prepares them for analysis |
| **Chemist** | `chemist` | Performs analyses, enters measurement data |
| **Senior Chemist** | `senior` | Reviews and approves/rejects results, manages QC |
| **Manager** | `manager` | Oversees quality management, views reports and dashboards |
| **Administrator** | `admin` | Full system access, user management, system configuration |

### 2.2 Permissions Matrix

#### Core Functions

| Function | Prep | Chemist | Senior | Manager | Admin |
|---|:---:|:---:|:---:|:---:|:---:|
| Register samples | Yes | -- | -- | -- | Yes |
| Edit samples | New only | -- | Yes | -- | Yes |
| Delete samples | -- | -- | Yes (new only) | -- | Yes |
| Enter analysis data | -- | Yes | -- | -- | -- |
| Approve/reject results | -- | -- | Yes | -- | Yes |
| View reports | Yes | Yes | Yes | Yes | Yes |
| Export (Excel/CSV) | -- | -- | Yes | Yes | Yes |

#### Quality Management

| Function | Prep | Chemist | Senior | Manager | Admin |
|---|:---:|:---:|:---:|:---:|:---:|
| CAPA records | -- | -- | Yes | Yes | Yes |
| Complaints | -- | -- | Yes | Yes | Yes |
| Proficiency testing | -- | -- | Yes | Yes | Yes |
| Environmental monitoring | -- | -- | Yes | Yes | Yes |
| Control charts | -- | -- | Yes | Yes | Yes |

#### Equipment

| Function | Prep | Chemist | Senior | Manager | Admin |
|---|:---:|:---:|:---:|:---:|:---:|
| View equipment | Yes | Yes | Yes | Yes | Yes |
| Add/Edit equipment | -- | -- | Yes | Yes | Yes |
| Delete equipment | -- | -- | Yes | Yes | Yes |

#### System Administration

| Function | Prep | Chemist | Senior | Manager | Admin |
|---|:---:|:---:|:---:|:---:|:---:|
| User management | -- | -- | -- | -- | Yes |
| Analysis type configuration | -- | -- | Yes | -- | Yes |
| Repeatability limits | -- | -- | Yes | -- | Yes |
| Bottle constants | -- | -- | Yes | -- | Yes |
| Control/GBW standards | -- | -- | Yes | -- | Yes |
| CSV import | -- | -- | Yes | -- | Yes |

### 2.3 Laboratory Access (allowed_labs)

Each user is assigned one or more laboratories they can access. This is configured via the `allowed_labs` field during user creation or editing. Admin users automatically have access to all laboratories. A user can only see samples and perform analyses within their allowed labs.

Available lab keys: `coal`, `water`, `microbiology`, `petrography`

---

## 3. Getting Started

### 3.1 Logging In

1. Open the LIMS URL in your web browser (typically `http://<server-address>:5000`).
2. Enter your **username** and **password** on the login page.
3. Optionally check **Remember me** to stay logged in across browser sessions.
4. Click **Sign In**.

**Security notes:**
- Login attempts are rate-limited to 5 per minute to prevent brute-force attacks.
- After successful login, you will be redirected to the Lab Selector page.
- Passwords must meet minimum security requirements: at least 8 characters, including uppercase, lowercase, and digits.

### 3.2 Lab Selector

After login, the **Lab Selector** page is displayed. This page shows the laboratories you are authorized to access (based on your `allowed_labs` setting). Each lab is shown as a card with its name and icon.

- **Coal Lab** -- Coal quality analyses
- **Water Lab** -- Water chemistry and microbiology
- **Microbiology Lab** -- Microbiological testing
- **Petrography Lab** -- Petrographic analysis

Click on a laboratory card to enter that lab's workspace. The system will remember your selection and filter all relevant data (samples, analyses, equipment) to that lab context.

### 3.3 Navigation

The main navigation bar at the top of the screen provides access to all features. Navigation items are filtered by your role:

**All users see:**
- **Home** -- Main dashboard with sample list
- **Analysis** -- Analysis hub and workspace
- **Equipment** -- Equipment list and details
- **Quality** -- Quality management modules (CAPA, Complaints, PT, Environmental, Control Charts)
- **Standards** -- Control standards (CM) and GBW standards
- **Reports** -- Consumption reports, monthly plans, statistics, sample retention

**Senior, Manager, Admin additionally see:**
- **Summary** -- Sample summary with aggregated results
- **Management** -- Settings and configuration submenus

**Senior, Admin additionally see:**
- **Senior Review** -- Senior chemist review dashboard
- **Send Shift Report** button

**Admin only:**
- **User Management** -- Create, edit, and delete users

### 3.4 Profile Settings

All users can update their own profile information (full name, email, phone, position) by navigating to the Profile page. This information is used in email signatures and report generation.

To access your profile:
1. Click on your username in the top-right corner of the navigation bar.
2. Select **Profile** from the dropdown menu.
3. Update your information and click **Save**.

### 3.5 Logging Out

Click on your username in the navigation bar and select **Logout**. You will be returned to the login page. All logout actions are recorded in the audit log.

---

## 4. For Chemists

This section covers the daily workflows for **Sample Preparation (prep)** and **Chemist** roles.

### 4.1 Sample Registration (Prep Role)

Sample registration is performed by users with the `prep` or `admin` role. The process follows a two-phase workflow:

#### Phase 1: Select Unit

1. Navigate to the **Home** page and click the **Add Sample** tab.
2. The **Unit Hub** is displayed with cards for each operational unit:
   - **CHPP** -- Coal Handling and Preparation Plant
   - **UHG-Geo** -- UHG Geology
   - **BN-Geo** -- BN Geology
   - **QC** -- Quality Control
   - **Proc** -- Process
   - **WTL** -- Water Lab
   - **LAB** -- Laboratory
3. Click on the appropriate unit card to proceed to the configuration workspace.

#### Phase 2: Configure and Generate Samples

After selecting a unit, the workspace is displayed with two panels side by side:

**Left Panel -- Configuration:**
- **Sample Type:** Select the type of sample (varies by unit). Types are loaded dynamically based on the selected unit.
- **Condition:** Choose the sample condition -- either dry or wet/liquid.
- **Dates:** Set the sample date and preparation date. Today's date is pre-filled by default.
- **Submitted By / Prepared By:** Enter the names of personnel who submitted and prepared the samples.
- **Retention Period:** Select how long the sample should be retained (7 days, 14 days, 1 month, 2 years, or 5 years). This sets the retention date for disposal tracking.
- **Notes:** Optional free-text notes for the sample.

**Unit-specific options:**
- **CHPP:** Additional configuration for 2-hourly, 4-hourly, 12-hourly, and composite samples. Select modules (MOD I, II, III), primary/secondary products, shifts, and timeslots.
- **UHG/BN/QC/Proc:** Enter location, product (optional), and sample count.
- **WTL:** Enter lab number or custom sample code for water samples.
- **LAB:** Sample names are generated automatically.

After configuring, click the **Generate Samples** button. The system will auto-generate sample codes following the naming convention for that unit.

**Right Panel -- Sample List:**
- Displays generated samples in a table with columns: number, sample code, analysis types, and weight fields.
- Sample codes can be edited inline.
- Analysis types are shown as colored badges.
- Weight fields are available for entering initial mass values.

Click the **Register** button at the top of the right panel to submit all samples to the database.

#### Editing Samples

Prep users can edit samples that are still in "new" status:
1. From the main sample list, click on the sample you wish to edit.
2. Modify the sample code or analysis types as needed.
3. Click **Save**.

**Note:** Once a sample moves to "in_progress" status (after analysis begins), only senior and admin users can edit it.

### 4.2 Mass Measurement (Mass Gate)

For coal analyses, many analysis types require an initial mass measurement before data entry is allowed. This is called the **mass gate**.

1. Navigate to **Analysis Hub** and select the **MT** (Total Moisture) or equivalent mass analysis type.
2. Click **+ Sample** to open the sample selection modal.
3. Select the samples you wish to weigh.
4. Enter the mass values in the designated fields.
5. The mass measurement is saved automatically.

Once mass is recorded for a sample, it becomes eligible for subsequent analyses (e.g., Mad, Aad, Vad, CV).

### 4.3 Analysis Workspace

The Analysis Hub is the central page for performing analyses. It is organized into three categories based on ISO nomenclature:

- **Technical Analysis** -- MT, Mad, Aad, Vad, FCd, FM, CV, Solid
- **Elemental & Trace Analysis** -- TS, C, H, N, O, P, F, Cl
- **Physical & Coking** -- TRD, CSN, Gi, X, Y, XY, CRI, CSR, CRICSR, PE

#### Navigating the Analysis Hub

1. Go to **Analysis** in the navigation bar.
2. The Analysis Hub displays cards for each analysis type, organized into tabbed categories.
3. Use the **search bar** to quickly find an analysis by name or code.
4. Click on an analysis card to open the analysis workspace for that type.

#### Entering Analysis Data

1. From the analysis workspace, click **+ Sample** to add samples to the workspace.
2. A modal dialog shows eligible samples (samples that have the required analysis type in their profile and have passed the mass gate if applicable).
3. Select samples and click **Add**.
4. The workspace table shows one row per sample with input fields for measurements.

**For most analyses, you will enter:**
- **Parallel measurements:** Two or more measurements (A and B) for the same sample.
- **Equipment selection:** Select the equipment used for the analysis (e.g., furnace, balance, calorimeter).
- **Measurement values:** Enter raw measurement data in the appropriate fields.

The system performs **auto-calculation** in real-time:
- **Mean:** Average of parallel measurements.
- **Difference (diff):** Absolute difference between parallel values.
- **Repeatability check:** The diff is compared against the repeatability limit defined in ISO standards or lab-specific configuration.
- **Status determination:** If the difference exceeds the repeatability limit, the result is flagged.

5. After entering all values, click **Save**.
6. The system will:
   - Validate all inputs
   - Perform server-side recalculation to verify client-side calculations
   - Apply analysis-specific rules (from `analysis_rules.py`)
   - Check against control standard values if the sample is a QC standard
   - Set the result status to `pending_review`

#### Understanding Parallel Measurements

Most analyses require two parallel measurements to ensure precision. The system:
- Calculates the mean of the two values
- Computes the difference (absolute difference)
- Compares the difference against the **repeatability limit** (r-value) defined for that analysis
- If diff <= limit: Result passes and goes to `pending_review`
- If diff > limit: Result is flagged and may need attention

#### Result Statuses

| Status | Meaning |
|---|---|
| `draft` | Data entered but not yet submitted |
| `pending_review` | Submitted and awaiting senior review |
| `approved` | Approved by senior chemist |
| `rejected` | Rejected by senior chemist (with reason) |

### 4.4 Basis Conversion (Coal Lab)

Coal analysis results can be expressed on different bases:
- **ad** (air-dried basis) -- as received in the lab
- **d** (dry basis) -- moisture-free
- **daf** (dry, ash-free basis) -- moisture and ash-free
- **ar** (as-received basis) -- original moisture content

The system automatically performs basis conversions when the required moisture and ash data are available. Converted values are displayed alongside the original measurement.

---

## 5. For Senior Chemists

Senior chemists are responsible for reviewing, approving or rejecting analysis results, managing quality control, and overseeing daily lab operations.

### 5.1 Senior Review Dashboard

The **Senior Review Dashboard** (also called "Ahlah Dashboard") is the primary tool for reviewing pending results.

**Accessing the dashboard:**
1. Navigate to **Senior Review** in the navigation bar (visible only to senior and admin users).

**Dashboard features:**
- **Date range filter:** Filter results by date range.
- **Sample search:** Search for specific samples by code.
- **Results grid:** An AG-Grid table showing all results with status `pending_review` or `rejected`.

**Columns displayed:**
- Sample code
- Analysis name and code
- Raw data values
- Tolerance value (diff for most analyses, or specific values for CSN)
- Final value (calculated result)
- Chemist name
- Last updated timestamp
- Current status

### 5.2 Approving Results

To approve a result:
1. Review the raw data, tolerance value, and final value in the dashboard grid.
2. Click the **Approve** button (green checkmark) for the result row.
3. The system will:
   - Set the result status to `approved`
   - Clear any previous rejection comments
   - Create an audit log entry with hash integrity verification
   - Log the action for ISO 17025 compliance

**Bulk approval:**
1. Select multiple results using the checkboxes in the grid.
2. Click the **Bulk Approve** button.
3. All selected results will be approved in a single operation.
4. A summary shows how many were successfully approved.

### 5.3 Rejecting Results

To reject a result:
1. Click the **Reject** button (red X) for the result row.
2. A dialog appears asking for:
   - **Rejection category:** Select a predefined reason from the dropdown (e.g., "Repeatability exceeded", "Equipment issue", "Sample contamination").
   - **Rejection comment:** Enter a free-text explanation.
3. Click **Confirm Rejection**.
4. The system will:
   - Set the result status to `rejected`
   - Store the rejection category and comment
   - Create an audit log entry
   - Notify relevant personnel (if email notifications are configured)

**Bulk rejection:**
1. Select multiple results using the checkboxes.
2. Click the **Bulk Reject** button.
3. Select a rejection category (required for bulk rejection).
4. Optionally enter a comment.
5. Confirm the bulk rejection.

When a result is rejected, the chemist is expected to re-perform the analysis. The rejected result remains visible in the dashboard for tracking purposes.

### 5.4 Dashboard Statistics

The senior dashboard provides real-time statistics for the current shift:

- **Per-chemist performance:** Total analyses, approved count, pending count, rejected count for each chemist working today.
- **Samples today:** Total samples registered today, broken down by unit (client) and sample type.
- **Analysis type breakdown:** Count of analyses by type (e.g., how many Mad, Aad, CV tests were performed today).
- **Summary totals:** Overall totals for approved, pending, and rejected results.

The shift timing is automatically calculated based on the current time, correctly handling day and night shifts.

### 5.5 QC Dashboard and Control Charts

Navigate to **Quality > Control Charts** to access quality control monitoring.

**Control charts** are generated for active control standards (CM and GBW):
- Each chart shows measurement values plotted over time.
- **Mean line** -- target value from the standard.
- **Warning limits** (2 sigma) -- yellow zones.
- **Control limits** (3 sigma) -- red zones.
- **Westgard rules** are applied to detect systematic errors:
  - 1-2s warning
  - 1-3s violation
  - 2-2s violation
  - R-4s range violation
  - 4-1s trend
  - 10x shift

Click on a chart card to expand it and see the full detailed chart with data points, limits, and rule violations.

### 5.6 Sample Summary and Export

The **Sample Summary** page provides a comprehensive view of all samples with their analysis results in a single AG-Grid table.

**Accessing:**
1. Navigate to **Summary** in the navigation bar.

**Features available to senior/admin users:**

| Button | Function |
|---|---|
| **Composite** | Compare composite sample results against hourly averages |
| **Norm Limit** | Check results against specification/norm limits |
| **Correlation** | Perform correlation analysis between parameters |
| **CSV** | Export the current data as a CSV file |
| **Copy** | Copy selected rows to clipboard |
| **Audit** | Navigate to the audit log hub |
| **Archive** | Navigate to the archive center |
| **Report** | Generate PDF report for selected samples |
| **Archive (action)** | Move selected samples to the archive |
| **Simulator** | Send selected samples to the CHPP simulator |
| **Refresh** | Reload the summary data |

**Manager role** sees only the Archive and Refresh buttons.

### 5.7 Sample Editing and Deletion

Senior chemists can:
- **Edit any sample** regardless of status (admin and senior only).
- **Delete samples** that are in "new" status. Samples already in processing cannot be deleted by senior users (only admin can force-delete).

### 5.8 Sample Retention and Disposal

Navigate to **Reports > Sample Retention** to manage sample storage:
- View **expired samples** (retention date has passed).
- View **upcoming expirations** (within 30 days).
- View **recently disposed** samples.
- Set retention dates for samples without one.
- **Dispose samples:** Select samples and enter a disposal method. Only senior and admin users can perform disposal.
- **Bulk retention:** Set retention dates for all samples without a date in one operation.

---

## 6. For Managers

Managers have access to oversight, reporting, and quality management features.

### 6.1 Dashboard Overview

The main dashboard provides:
- **Sample counts:** Total samples by status (new, in progress, completed).
- **Today's activity:** Samples registered today, analyses performed today.
- **Quick navigation:** Links to frequently used features.

### 6.2 Reports and Statistics

**Analytics Dashboard:**
Navigate to **Reports > Statistics** for an analytics overview:
- Analysis counts by type and date range
- Performance metrics
- Trend analysis

**Chemist Report:**
View per-chemist performance including total analyses, approval rates, and rejection rates.

**Consumption Report:**
Track chemical and reagent consumption over time.

**Monthly Plan:**
View and compare planned vs. actual analysis volumes.

### 6.3 Quality Management

Managers have full access to quality management modules:

- **CAPA (Corrective Action):** Record and track corrective actions per ISO 17025 Clause 8.7. Track status: Open, In Progress, Reviewed, Closed.
- **Complaints:** Record customer complaints, track investigation and resolution.
- **Proficiency Testing (PT):** Record and manage interlaboratory comparison results.
- **Environmental Monitoring:** Track environmental conditions in the laboratory.
- **Nonconformity:** Record nonconformities and track corrective measures.
- **Improvement:** Track continual improvement initiatives.

### 6.4 Archive Access

Navigate to **Summary > Archive** to access archived sample data. Archived samples are read-only and serve as historical records. Managers can view archives but cannot modify archived data.

### 6.5 Excel Export

Managers can export data to Excel from:
- The main sample list (Home page)
- The analytics dashboard
- The audit hub

Look for the Excel/CSV export button (green spreadsheet icon) in the page header.

---

## 7. For Administrators

Administrators have full access to all system features plus exclusive access to system configuration and user management.

### 7.1 User Management

Navigate to **Admin > User Management** to manage system users.

#### Creating a New User

1. Go to **User Management**.
2. Fill in the user creation form:
   - **Username:** Unique identifier for the user (required).
   - **Password:** Must meet security requirements -- minimum 8 characters, uppercase, lowercase, and digits (required).
   - **Role:** Select from prep, chemist, senior, manager. Note: creating additional admin users is not permitted through this form for security reasons.
   - **Allowed Labs:** Select one or more laboratories the user can access (coal, water, microbiology, petrography).
   - **Full Name, Email, Phone, Position:** Optional profile information.
3. Click **Create User**.
4. The action is recorded in the audit log.

#### Editing a User

1. From the user list, click the **Edit** button for the user you wish to modify.
2. Update the desired fields.
3. To change the password, enter a new password in the password field. Leave it blank to keep the current password.
4. Click **Save Changes**.

**Important restrictions:**
- The admin role cannot be changed to a different role (protection against accidental lockout).
- If you change a user's role, their permissions take effect immediately on their next page load.

#### Deleting a User

1. Click the **Delete** button for the user.
2. Confirm the deletion.

**Important restrictions:**
- Admin users cannot be deleted.
- An admin cannot delete their own account.
- All user deletions are logged in the audit trail.

### 7.2 Analysis Type Configuration

Navigate to **Admin > Analysis Configuration** to manage analysis types and profiles.

**Analysis Types:**
The system maintains a master list of analysis types (defined in `constants.py`). When you visit the configuration page, the system automatically seeds/updates analysis types from this master list. Each type has:
- **Code:** Unique identifier (e.g., Mad, Aad, CV)
- **Name:** Display name
- **Order:** Display order in lists
- **Required Role:** Minimum role needed to perform this analysis (usually `chemist` or `prep`)

**Analysis Profiles:**
Profiles define which analyses are automatically assigned to samples based on their unit and sample type. There are two categories:

1. **Simple Profiles** (non-CHPP units): Define analysis sets for each combination of unit and sample type (e.g., UHG-Geo + ROM = [Mad, Aad, Vad, CV, TS]).
2. **CHPP Profiles** (pattern-based): Define analysis sets for specific CHPP sample patterns (e.g., 2-hourly, 4-hourly, 12-hourly, composite samples).

To configure:
1. Navigate to the Analysis Configuration page.
2. For each profile, check or uncheck the analysis types that should be included.
3. Click **Save** to persist changes.

**Gi Shift Configuration:**
A special section allows configuring which shifts run the Gi (swelling) analysis for each PF module (PF211, PF221, PF231).

### 7.3 Control Standards (CM) and GBW Standards

Navigate to **Admin > Standards** to manage control and reference standards.

#### Control Standards (CM)

1. Click **New Standard** to create a new control standard.
2. Enter the standard name and target values for each analysis parameter.
3. Click **Save**.
4. To activate a standard, click the **Activate** button. Only one CM standard can be active at a time.
5. Active standards are used in QC checks when chemists analyze QC samples.

#### GBW Standards

1. Click **New GBW** to register a new GBW reference material.
2. Enter the GBW number and certified target values.
3. Click **Save**.
4. Activate/deactivate as needed. Only one GBW standard can be active at a time.

**Notes:**
- Active standards cannot be deleted. Deactivate first, then delete.
- Standard target values use different units for CM vs GBW (e.g., CV uses kcal/kg for CM but MJ/kg for GBW).

### 7.4 Equipment Management

Navigate to **Equipment** to manage laboratory equipment.

**Equipment List:**
- View all registered equipment with details (name, model, serial number, location, calibration status).
- Filter by status, type, or search by name.

**Adding Equipment:**
1. Click **New Equipment**.
2. Fill in equipment details: name, model, serial number, manufacturer, location, category.
3. Upload calibration certificates if available.
4. Click **Save**.

**Equipment Details Page:**
- View full equipment history including calibration records, maintenance logs, and usage history.
- Upload calibration certificates (PDF, images).
- Record calibration events with date, result, and next due date.
- Track equipment status: Active, Under Maintenance, Out of Service, Retired.

**Internal Checks:**
- Record internal verification checks for balances, thermometers, and other measuring instruments.
- Track glassware journals with cleaning and verification records.

### 7.5 Settings

#### Bottle Constants

Navigate to **Admin > Bottle Constants** to manage bottle/crucible tare weights used in gravimetric analyses:
- Add new bottles with their constant (tare) weight.
- Edit existing bottle weights.
- Bulk import bottle constants.
- Bottles are referenced during analysis data entry.

#### Repeatability Limits

Navigate to the Analysis Configuration page to view and modify repeatability limits for each analysis type. These limits define the maximum acceptable difference between parallel measurements.

### 7.6 System Settings

The system stores various configuration values in the `SystemSetting` table, organized by category. These include:
- Gi shift configuration
- Error reason labels for rejection categories
- Notification settings
- Report templates

### 7.7 Audit Log Review

Navigate to **Summary > Audit** to access the audit log hub.

The audit log records all significant system events:
- User login/logout
- Sample creation, editing, deletion, disposal
- Analysis result saves, approvals, rejections
- User creation, editing, deletion
- Equipment changes
- Standard activations/deactivations
- Configuration changes

**Audit log features:**
- Search by date range, action type, user, or resource.
- Export audit data to Excel.
- Each log entry includes a **data hash** for integrity verification (ISO 17025 requirement).

**Hash Verification:**
Critical audit records (AnalysisResultLog, AuditLog, SparePartLog, ChemicalLog) contain a `data_hash` field computed from the record's data. This hash can be verified to ensure that audit records have not been tampered with after creation.

### 7.8 Backup Procedures

**Database Backup:**

For PostgreSQL (production):
```bash
# Full database dump
pg_dump -U username -h localhost coal_lims > backup_$(date +%Y%m%d_%H%M%S).sql

# Compressed backup
pg_dump -U username -h localhost coal_lims | gzip > backup_$(date +%Y%m%d_%H%M%S).sql.gz
```

For SQLite (development):
```bash
# Copy the database file
cp instance/coal_lims.db instance/coal_lims_backup_$(date +%Y%m%d).db
```

**Recommended backup schedule:**
- **Daily:** Full database backup (automated via cron job or Windows Task Scheduler)
- **Weekly:** Backup with verification (restore to a test environment to confirm integrity)
- **Before updates:** Always take a backup before applying system updates or migrations

**File Backup:**
In addition to the database, back up the following directories:
- `instance/uploads/` -- Uploaded certificates and documents
- `.env` -- Environment configuration (store securely, do not commit to version control)
- `logs/` -- Application and audit logs

**Restore Procedure:**

For PostgreSQL:
```bash
# Restore from backup
psql -U username -h localhost coal_lims < backup_file.sql
```

For SQLite:
```bash
# Stop the application first, then replace the database file
cp instance/coal_lims_backup.db instance/coal_lims.db
```

---

## 8. FAQ and Common Issues

### Q: I cannot log in. What should I do?

**A:** Check the following:
1. Verify your username and password are correct (passwords are case-sensitive).
2. If you have tried too many times, wait 1 minute (rate limiting: 5 attempts per minute).
3. Contact your administrator to verify your account exists and is active.
4. Clear your browser cache and cookies, then try again.

### Q: I cannot see certain menu items or pages.

**A:** Menu visibility is controlled by your user role. For example:
- Only `senior` and `admin` roles see the Senior Review dashboard.
- Only `admin` sees User Management.
- Only `senior`, `manager`, and `admin` see the Summary page.

If you believe you should have access, contact your administrator to verify your role assignment.

### Q: I cannot see samples from another laboratory.

**A:** Each user is restricted to the laboratories listed in their `allowed_labs` setting. Contact your administrator to request access to additional laboratories. Admin users have automatic access to all labs.

### Q: My analysis data was rejected. What should I do?

**A:** When a senior chemist rejects your result:
1. Check the **rejection category** and **comment** in the senior dashboard or your notification.
2. Common reasons include: repeatability limit exceeded, equipment calibration issue, sample contamination.
3. Re-perform the analysis addressing the noted issue.
4. Submit the new result. It will appear again in the senior review queue.

### Q: The repeatability check failed. What does this mean?

**A:** The repeatability check compares the difference between your parallel measurements against the ISO-defined repeatability limit (r-value) for that analysis. If the difference exceeds the limit:
- The result is flagged but still submitted for review.
- The senior chemist may approve it with justification or reject it for re-analysis.
- Common causes: insufficient sample homogeneity, equipment drift, procedural errors.

### Q: How do I know which samples are ready for analysis?

**A:** In the Analysis Workspace:
1. Click **+ Sample** to open the sample selection dialog.
2. Only **eligible** samples are shown -- these are samples that:
   - Have the relevant analysis type in their profile
   - Have passed the mass gate (if required for that analysis)
   - Have not already been analyzed for that type (or were rejected and need re-analysis)

### Q: How do I export data to Excel or CSV?

**A:** Depending on your role:
- **Sample Summary page:** Click the **CSV** button to export all visible data.
- **Main sample list:** Click the **Excel** button (visible to senior, manager, admin).
- **Analytics dashboard:** Use the **Excel Export** button.
- **Audit hub:** Use the **Excel Export** button.

### Q: A sample was registered with the wrong code. How do I fix it?

**A:**
- **Prep users** can edit samples that are still in "new" status.
- **Senior and admin users** can edit any sample regardless of status.
- Navigate to the sample in the sample list, click **Edit**, change the code, and save.
- The system checks for duplicate codes (case-insensitive) before saving.

### Q: How do I dispose of samples?

**A:** Navigate to **Reports > Sample Retention**:
1. Find the samples to dispose (check the "Expired" tab).
2. Select the samples using checkboxes.
3. Enter the disposal method (e.g., "Discarded", "Returned to client").
4. Click **Dispose Selected**.
5. Only `senior` and `admin` users can perform disposal.

### Q: The system shows "Insufficient permissions" (403 error).

**A:** This means your role does not have permission for the requested action. Common scenarios:
- Trying to access admin pages without admin role.
- Trying to approve results without senior/admin role.
- Trying to edit equipment without senior/manager/admin role.

Contact your administrator if you need elevated permissions.

### Q: How does the audit trail work?

**A:** Every critical action in the system is automatically logged:
- **Who** performed the action (user ID and username)
- **What** action was performed (create, edit, delete, approve, reject, etc.)
- **When** the action occurred (timestamp)
- **What resource** was affected (sample ID, result ID, user ID, etc.)
- **Details** of the change (stored as JSON)
- **Data hash** for integrity verification

Audit logs cannot be modified or deleted by any user, including administrators. This ensures compliance with ISO 17025 requirements for record integrity.

### Q: Can I use the system on a mobile device?

**A:** Yes. The system is designed with responsive layouts that work on tablets and smartphones. The analysis workspace includes a mobile drawer for sidebar navigation, and most features are accessible on smaller screens. However, for data-intensive tasks (analysis entry, summary review), a desktop or laptop with a larger screen is recommended for the best experience.

---

*This guide covers the primary features and workflows of CORELINK LIMS. For technical documentation, API references, and development guides, refer to the separate technical documentation in the `docs_all/` directory.*

*For support, contact your system administrator or email support@energyresources.mn.*
