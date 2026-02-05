# Session Log: Coverage Analysis
**Date:** 2025-12-25

## Coverage Report - Files Below 60%

Total files with coverage < 60%: **47 files**

| Coverage | File |
|----------|------|
| 0% | app/api_docs.py |
| 0% | app/schemas/__init__.py |
| 0% | app/schemas/analysis_schema.py |
| 0% | app/schemas/sample_schema.py |
| 0% | app/schemas/user_schema.py |
| 0% | app/services/analysis_audit.py |
| 9% | app/routes/main/index.py |
| 9% | app/utils/validators.py |
| 9% | app/routes/api/samples_api.py |
| 10% | app/routes/analysis/qc.py |
| 10% | app/routes/report_routes.py |
| 10% | app/routes/api/analysis_api.py |
| 10% | app/routes/import_routes.py |
| 10% | app/routes/quality/control_charts.py |
| 11% | app/cli.py |
| 11% | app/utils/qc.py |
| 11% | app/routes/analysis/kpi.py |
| 13% | app/routes/analysis/workspace.py |
| 14% | app/routes/main/samples.py |
| 16% | app/routes/equipment_routes.py |
| 16% | app/routes/chat_events.py |
| 16% | app/routes/api/audit_api.py |
| 17% | app/routes/analysis/senior.py |
| 17% | app/routes/settings_routes.py |
| 19% | app/utils/sorting.py |
| 19% | app/routes/api/mass_api.py |
| 20% | app/routes/admin_routes.py |
| 24% | app/routes/api/helpers.py |
| 25% | app/utils/decorators.py |
| 26% | app/config/analysis_schema.py |
| 27% | app/utils/security.py |
| 27% | app/utils/settings.py |
| 27% | app/routes/main/helpers.py |
| 29% | app/utils/quality_helpers.py |
| 30% | app/routes/main/auth.py |
| 31% | app/routes/api/chat_api.py |
| 34% | app/routes/quality/capa.py |
| 35% | app/utils/shifts.py |
| 36% | app/routes/quality/proficiency.py |
| 40% | app/config/display_precision.py |
| 43% | app/routes/license_routes.py |
| 43% | app/monitoring.py |
| 44% | app/routes/quality/complaints.py |
| 47% | app/utils/license_protection.py |
| 48% | app/routes/quality/environmental.py |
| 50% | app/utils/parameters.py |
| 57% | app/__init__.py |

## Summary by Category

### 0% Coverage (6 files)
- app/api_docs.py
- app/schemas/__init__.py
- app/schemas/analysis_schema.py
- app/schemas/sample_schema.py
- app/schemas/user_schema.py
- app/services/analysis_audit.py

### Utils (10 files)
| Coverage | File |
|----------|------|
| 9% | app/utils/validators.py |
| 11% | app/utils/qc.py |
| 19% | app/utils/sorting.py |
| 25% | app/utils/decorators.py |
| 27% | app/utils/security.py |
| 27% | app/utils/settings.py |
| 29% | app/utils/quality_helpers.py |
| 35% | app/utils/shifts.py |
| 47% | app/utils/license_protection.py |
| 50% | app/utils/parameters.py |

### Routes (22 files)
| Coverage | File |
|----------|------|
| 9% | app/routes/main/index.py |
| 9% | app/routes/api/samples_api.py |
| 10% | app/routes/analysis/qc.py |
| 10% | app/routes/report_routes.py |
| 10% | app/routes/api/analysis_api.py |
| 10% | app/routes/import_routes.py |
| 10% | app/routes/quality/control_charts.py |
| 11% | app/routes/analysis/kpi.py |
| 13% | app/routes/analysis/workspace.py |
| 14% | app/routes/main/samples.py |
| 16% | app/routes/equipment_routes.py |
| 16% | app/routes/chat_events.py |
| 16% | app/routes/api/audit_api.py |
| 17% | app/routes/analysis/senior.py |
| 17% | app/routes/settings_routes.py |
| 19% | app/routes/api/mass_api.py |
| 20% | app/routes/admin_routes.py |
| 24% | app/routes/api/helpers.py |
| 27% | app/routes/main/helpers.py |
| 30% | app/routes/main/auth.py |
| 31% | app/routes/api/chat_api.py |
| 34% | app/routes/quality/capa.py |
| 36% | app/routes/quality/proficiency.py |
| 43% | app/routes/license_routes.py |
| 44% | app/routes/quality/complaints.py |
| 48% | app/routes/quality/environmental.py |

### Config (2 files)
| Coverage | File |
|----------|------|
| 26% | app/config/analysis_schema.py |
| 40% | app/config/display_precision.py |

### Other (3 files)
| Coverage | File |
|----------|------|
| 11% | app/cli.py |
| 43% | app/monitoring.py |
| 57% | app/__init__.py |

## Current Total Coverage: 33.13%

## Session Work Completed

### Tests Fixed
1. `test_soft_min_limit_exceeded` - CV business logic check order
2. `test_calculation_exception_returns_client` - MagicMock import + dictionary patch
3. `test_gi_removed_for_wrong_shift` - AnalysisProfile.set_analyses() method
4. `test_gi_kept_for_correct_shift` - AnalysisProfile.set_analyses() method
5. `test_pattern_profile_match` - AnalysisProfile.set_analyses() method

### Test Results
- **382 tests passed**
- **0 failures**
- Coverage: 33.13%
