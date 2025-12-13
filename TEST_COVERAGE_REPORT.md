# Coal LIMS Test Coverage Report
Огноо: 2025-12-11

## Тестийн үр дүн

| Metric | Value |
|--------|-------|
| Нийт тест | 1355 |
| Passed | 1354 |
| Failed | 1 |
| Coverage | 57.33% |

## Coverage by Module

### Utils (80-100% coverage)
- westgard.py: 100%
- shifts.py: 100%
- security.py: 100%
- exports.py: 100%
- decorators.py: 100%
- database.py: 100%
- analysis_rules.py: 100%
- analysis_assignment.py: 97%
- parameters.py: 94%
- conversions.py: 94%
- quality_helpers.py: 93%
- server_calculations.py: 92%
- codes.py: 92%
- analysis_aliases.py: 88%
- sorting.py: 85%
- qc.py: 85%
- notifications.py: 82%

### Routes (Low coverage - needs improvement)
- index.py: 15%
- settings_routes.py: 18%
- qc.py: 10%
- chat_events.py: 17%
- kpi.py: 25%
- samples.py: 30%
- import_routes.py: 30%

### Models
- models.py: 81%

## Нэмсэн тест файлууд

### Unit Tests
- test_validators_comprehensive.py
- test_models_comprehensive.py
- test_datetime_utils.py
- test_audit_extended.py
- test_analysis_rules.py
- test_security_utils.py
- test_settings_utils.py
- test_audit_utils.py
- test_conversions_extended.py
- test_codes_extended.py
- test_sorting_extended.py
- test_notifications_extended.py
- test_validators_full.py

### Integration Tests
- test_main_routes_comprehensive.py
- test_settings_routes.py
- test_qc_routes.py
- test_workspace_routes.py
- test_import_routes.py
- test_senior_routes.py
- test_kpi_routes.py
- test_api_extended.py
- test_report_routes_extended.py
- test_chat_routes.py
- test_quality_routes_extended.py

## 80% хүрэхэд хийх зүйлс

1. Routes файлуудын coverage нэмэх
   - index.py: 271 мөр дутуу
   - settings_routes.py: 236 мөр дутуу
   - report_routes.py: 247 мөр дутуу

2. Database-тэй integration тестүүд
   - Fixture-үүд сайжруулах
   - Test database тохируулах

3. Mock-based тестүүд
   - External API calls mock хийх
   - Email notifications mock хийх

## Тайлбар

80% coverage хүрэхэд routes файлууд хамгийн их саад болж байна.
Routes-ийн тест бичихэд:
- Database state шаардлагатай
- Form submissions хийх хэрэгтэй
- Session state удирдах хэрэгтэй

Utils модулууд бараг бүгд 80%+ coverage-тэй болсон.
