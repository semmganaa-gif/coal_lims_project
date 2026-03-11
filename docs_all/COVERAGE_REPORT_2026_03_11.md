# Coverage Test Report — 2026-03-11 (Updated)

## Summary

| Metric | Value |
|--------|-------|
| **Total Coverage** | **89.71%** |
| **Previous Coverage** | 81.46% (2026-03-11 initial) |
| **Improvement** | +8.25% |
| **Total Tests** | 13,233 collected |
| **Passed** | 13,051 |
| **Failed** | 1 (flaky — passes in isolation) |
| **Skipped** | 181 |
| **Duration** | 61 min 16 sec |

## File Stats

| Category | Count |
|----------|-------|
| Total source files | 194 |
| Files at 100% | 85 |
| Files at 80%+ | 155 |
| Files under 80% | 39 |
| Files under 50% | 5 |

## Changes from Previous Run

1. **158 → 1 failed test** — fixed mock paths for repository pattern migration
2. **Deleted 25 dead code files** (app/domain/ + app/security/) — 0% coverage mirrors removed
3. **Coverage 81.46% → 89.71%** (+8.25%)

## Low Coverage Files

### Under 50%

| Coverage | File | Miss |
|----------|------|------|
| 24% | labs/water_lab/microbiology/routes.py | 206 |
| 39% | labs/petrography/routes.py | 50 |
| 42% | repositories/chat_repository.py | 40 |
| 48% | labs/water_lab/__init__.py | 16 |
| 49% | repositories/analysis_result_repository.py | 42 |

### 50-79%

| Coverage | File | Miss |
|----------|------|------|
| 50% | repositories/equipment_repository.py | 28 |
| 51% | repositories/audit_repository.py | 19 |
| 51% | repositories/report_repository.py | 34 |
| 53% | labs/water_lab/routes.py | 7 |
| 54% | labs/water_lab/microbiology/__init__.py | 13 |
| 54% | bootstrap/jinja.py | 24 |
| 56% | routes/analysis/workspace.py | 108 |
| 60% | repositories/maintenance_repository.py | 17 |
| 60% | repositories/sample_repository.py | 33 |
| 60% | repositories/bottle_repository.py | 22 |
| 60% | sentry_integration.py | 33 |
| 61% | constants/samples.py | 11 |
| 61% | repositories/system_setting_repository.py | 21 |
| 62% | repositories/chemical_repository.py | 17 |
| 62% | repositories/user_repository.py | 17 |
| 64% | bootstrap/errors.py | 8 |
| 64% | labs/water_lab/chemistry/__init__.py | 10 |
| 64% | models/mixins.py | 5 |
| 65% | forms/analysis_config.py | 7 |
| 66% | labs/base.py | 10 |
| 67% | bootstrap/cli_commands.py | 2 |
| 68% | models/analysis.py | 57 |
| 70% | repositories/standard_repository.py | 26 |
| 70% | forms/common.py | 3 |
| 70% | repositories/quality_repository.py | 53 |
| 70% | routes/chat/events.py | 67 |
| 72% | labs/petrography/__init__.py | 5 |
| 74% | cli.py | 93 |
| 74% | routes/main/auth.py | 17 |
| 76% | routes/main/hourly_report.py | 49 |
| 76% | bootstrap/middleware.py | 9 |
| 76% | labs/coal/__init__.py | 4 |
| 78% | bootstrap/auth.py | 2 |
| 79% | constants/__init__.py | 3 |

## 1 Flaky Test

| Test | Root Cause |
|------|------------|
| test_routes_remaining_batch.py::TestWestgardDetail::test_no_qc_samples | Test ordering issue — passes in isolation |

## Coverage History

| Date | Coverage | Tests | Notes |
|------|----------|-------|-------|
| 2026-02-28 | 59.50% | ~10,000 | Baseline |
| 2026-03-08 | 64.31% | 10,462 | Test fix sprint |
| 2026-03-10 | 64% | 10,460 | Code review + service layer |
| 2026-03-11 (initial) | 81.46% | 12,894 | Architecture refactor + 2,800 new tests |
| **2026-03-11 (final)** | **89.71%** | **13,051** | Fix 158 tests + remove dead code |

## Action Items

1. **Water lab routes** — microbiology (24%), petrography (39%) need more tests
2. **New repository files** — 12 repositories at 50-70%, write more tests
3. **routes/analysis/workspace.py** (56%) — large file, needs coverage improvement
