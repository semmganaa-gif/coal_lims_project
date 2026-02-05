================================================================================
COAL LIMS - COVERAGE REPORT
Generated: 2025-12-24 21:20:31
Session: 2025-12-24 Night Session
================================================================================

TOTAL COVERAGE: 77.94%
Lines Covered: 7050 / 9045
Tests: 4719 passed, 82 skipped

================================================================================
DETAILED COVERAGE BY FILE
================================================================================

### CRITICAL (0-25% coverage) ###
--------------------------------------------------------------------------------

### LOW (25-50% coverage) ###
--------------------------------------------------------------------------------
  45.5% |  157/ 345 lines | routes/main/index.py

### MEDIUM (50-75% coverage) ###
--------------------------------------------------------------------------------
  56.0% |  202/ 361 lines | routes/equipment_routes.py
  56.5% |  100/ 177 lines | utils/license_protection.py
  56.8% |   25/  44 lines | routes/license_routes.py
  58.1% |  219/ 377 lines | routes/api/analysis_api.py
  61.4% |  178/ 290 lines | routes/quality/control_charts.py
  62.5% |  100/ 160 lines | routes/api/audit_api.py
  63.2% |  285/ 451 lines | routes/admin_routes.py
  63.6% |   14/  22 lines | routes/analysis/helpers.py
  63.7% |  172/ 270 lines | cli.py
  66.3% |  122/ 184 lines | routes/chat_events.py
  67.2% |   45/  67 lines | utils/hardware_fingerprint.py
  69.2% |  295/ 426 lines | routes/api/samples_api.py
  73.3% |  126/ 172 lines | routes/api/mass_api.py
  74.0% |  196/ 265 lines | routes/import_routes.py
  74.6% |  138/ 185 lines | __init__.py

### GOOD (75-90% coverage) ###
--------------------------------------------------------------------------------
  76.1% |  121/ 159 lines | routes/analysis/workspace.py
  76.1% |  166/ 218 lines | routes/analysis/qc.py
  78.4% |   98/ 125 lines | routes/api/helpers.py
  80.8% |   42/  52 lines | routes/quality/complaints.py
  81.5% |  529/ 649 lines | models.py
  81.6% |  111/ 136 lines | monitoring.py
  82.2% |   88/ 107 lines | utils/notifications.py
  82.9% |   34/  41 lines | utils/audit.py
  83.3% |   15/  18 lines | routes/main/helpers.py
  83.5% |   66/  79 lines | routes/quality/capa.py
  83.6% |   46/  55 lines | config/display_precision.py
  83.9% |   47/  56 lines | routes/main/auth.py
  85.4% |   35/  41 lines | services/analysis_audit.py
  85.7% |   12/  14 lines | utils/repeatability_loader.py
  86.7% |  170/ 196 lines | routes/main/samples.py
  88.0% |  279/ 317 lines | routes/settings_routes.py
  88.4% |  411/ 465 lines | routes/report_routes.py
  88.5% |   77/  87 lines | forms.py
  89.5% |   68/  76 lines | constants.py

### EXCELLENT (90-100% coverage) ###
--------------------------------------------------------------------------------
  91.1% |   41/  45 lines | schemas/sample_schema.py
  91.5% |  184/ 201 lines | routes/analysis/senior.py
  91.7% |   22/  24 lines | utils/codes.py
  93.4% |   99/ 106 lines | utils/normalize.py
  93.4% |   57/  61 lines | utils/sorting.py
  93.6% |  367/ 392 lines | utils/server_calculations.py
  93.9% |   46/  49 lines | schemas/user_schema.py
  93.9% |   31/  33 lines | utils/settings.py
  94.1% |   32/  34 lines | logging_config.py
  94.1% |   32/  34 lines | utils/parameters.py
  94.3% |   99/ 105 lines | utils/conversions.py
  95.5% |  171/ 179 lines | routes/analysis/kpi.py
  95.7% |   44/  46 lines | schemas/analysis_schema.py
  96.7% |   59/  61 lines | utils/quality_helpers.py
  96.8% |  121/ 125 lines | routes/api/chat_api.py
  97.0% |   65/  67 lines | utils/analysis_assignment.py
  97.1% |  134/ 138 lines | utils/validators.py
  99.0% |  103/ 104 lines | utils/qc.py
 100.0% |    8/   8 lines | api_docs.py
 100.0% |    0/   0 lines | config/__init__.py
 100.0% |   26/  26 lines | config/analysis_schema.py
 100.0% |    8/   8 lines | config/qc_config.py
 100.0% |    2/   2 lines | config/repeatability.py
 100.0% |   10/  10 lines | routes/analysis/__init__.py
 100.0% |   12/  12 lines | routes/api/__init__.py
 100.0% |    8/   8 lines | routes/main/__init__.py
 100.0% |   17/  17 lines | routes/quality/__init__.py
 100.0% |   27/  27 lines | routes/quality/environmental.py
 100.0% |   41/  41 lines | routes/quality/proficiency.py
 100.0% |    4/   4 lines | schemas/__init__.py
 100.0% |    0/   0 lines | services/__init__.py
 100.0% |    0/   0 lines | utils/__init__.py
 100.0% |    8/   8 lines | utils/analysis_aliases.py
 100.0% |   36/  36 lines | utils/analysis_rules.py
 100.0% |   15/  15 lines | utils/converters.py
 100.0% |   46/  46 lines | utils/database.py
 100.0% |   11/  11 lines | utils/datetime.py
 100.0% |   56/  56 lines | utils/decorators.py
 100.0% |   66/  66 lines | utils/exports.py
 100.0% |   11/  11 lines | utils/security.py
 100.0% |   78/  78 lines | utils/shifts.py
 100.0% |   64/  64 lines | utils/westgard.py

================================================================================
SUMMARY
================================================================================
Critical (0-25%):      0 files
Low (25-50%):          1 files
Medium (50-75%):      15 files
Good (75-90%):        19 files
Excellent (90-100%):  42 files
TOTAL:                77 files

================================================================================
NEW TESTS ADDED THIS SESSION
================================================================================
1. tests/test_license_protection.py - 27 tests
2. tests/test_api_docs.py - 12 tests
3. tests/test_index_extended.py - 30 tests

IMPROVEMENTS:
- license_protection.py: 22.6% -> 56.5%
- api_docs.py: 37.5% -> 100%
- Overall: 75.91% -> 77.94%