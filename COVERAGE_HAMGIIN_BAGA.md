# Coverage Report - Хамгийн Бага

**Огноо:** 2025-01-03
**Нийт тест:** 10,250 passed (113 skipped)
**Нийт coverage:** 83%

## Хамгийн бага coverage файлууд (80% доош)

| # | Файл | Stmts | Miss | Cover |
|---|------|-------|------|-------|
| 1 | app/routes/main/index.py | 345 | 157 | **54%** |
| 2 | app/routes/equipment_routes.py | 361 | 159 | **56%** |
| 3 | app/routes/api/analysis_api.py | 377 | 148 | **61%** |
| 4 | app/routes/api/audit_api.py | 160 | 60 | **62%** |
| 5 | app/routes/analysis/helpers.py | 22 | 8 | **64%** |
| 6 | app/cli.py | 270 | 96 | **64%** |
| 7 | app/routes/quality/control_charts.py | 290 | 99 | **66%** |
| 8 | app/routes/chat_events.py | 184 | 62 | **66%** |
| 9 | app/routes/api/mass_api.py | 172 | 46 | **73%** |
| 10 | app/__init__.py | 185 | 47 | **75%** |
| 11 | app/routes/import_routes.py | 265 | 67 | **75%** |
| 12 | app/routes/analysis/qc.py | 218 | 52 | **76%** |
| 13 | app/routes/api/helpers.py | 125 | 27 | **78%** |
| 14 | app/routes/analysis/workspace.py | 159 | 34 | **79%** |

## 100% Coverage файлууд (28 файл)

- app/utils/normalize.py
- app/utils/qc.py
- app/utils/westgard.py
- app/utils/sorting.py
- app/utils/shifts.py
- app/utils/decorators.py
- app/utils/database.py
- app/utils/exports.py
- app/utils/converters.py
- app/utils/analysis_rules.py
- app/utils/audit.py
- app/utils/quality_helpers.py
- app/utils/settings.py
- app/utils/security.py
- app/utils/repeatability_loader.py
- app/utils/datetime.py
- app/utils/analysis_aliases.py
- app/services/analysis_audit.py
- app/routes/quality/proficiency.py
- app/routes/quality/environmental.py
- app/logging_config.py
- app/config/analysis_schema.py
- app/config/qc_config.py
- app/config/repeatability.py
- app/api_docs.py

## 99% Coverage файлууд (5 файл)

| Файл | Stmts | Miss | Cover |
|------|-------|------|-------|
| app/utils/server_calculations.py | 392 | 1 | 99% |
| app/utils/license_protection.py | 177 | 1 | 99% |
| app/utils/validators.py | 138 | 2 | 99% |
| app/monitoring.py | 136 | 2 | 99% |
| app/utils/analysis_assignment.py | 67 | 1 | 99% |

## Тодорхойлолт

### Яагаад зарим файлын coverage бага байна?

1. **index.py (54%)** - Олон route, form validation, hourly report Excel үүсгэх
2. **equipment_routes.py (56%)** - Тоног төхөөрөмжийн CRUD, calibration
3. **analysis_api.py (61%)** - API endpoints, олон exception handling
4. **audit_api.py (62%)** - Audit log API
5. **cli.py (64%)** - Command line commands, database operations

### Дараагийн алхмууд

1. equipment_routes.py (56%) - Тест нэмэх
2. analysis_api.py (61%) - API тест нэмэх
3. audit_api.py (62%) - Audit тест нэмэх
4. cli.py (64%) - CLI команд тест нэмэх

## Статистик

- **Нийт statements:** 9,045
- **Covered:** 7,509
- **Missing:** 1,536
- **Coverage:** 83%
