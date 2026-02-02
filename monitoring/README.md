# LIMS - Monitoring Stack

Prometheus, Grafana, Loki, Alertmanager бүхий бүрэн monitoring stack.

## Quick Start

```bash
# Main app + Monitoring stack эхлүүлэх
docker-compose -f docker-compose.yml -f docker-compose.monitoring.yml up -d
```

## Components

| Service | Port | Description |
|---------|------|-------------|
| Prometheus | 9090 | Metrics collection |
| Grafana | 3000 | Visualization dashboards |
| Loki | 3100 | Log aggregation |
| Alertmanager | 9093 | Alert routing |

## Access URLs

- **Grafana**: http://localhost:3000 (admin/admin)
- **Prometheus**: http://localhost:9090
- **Alertmanager**: http://localhost:9093

## Prometheus Metrics

### Custom LIMS Metrics
- `lims_samples_total{client, sample_type}` - Sample registration count
- `lims_analysis_total{analysis_type, status}` - Analysis count
- `lims_active_users` - Current active users
- `lims_db_query_duration_seconds{query_type}` - DB query time
- `lims_qc_checks_total{check_type, result}` - QC check results

## Alert Rules

- `LIMSDown` - Application is unreachable (critical)
- `HighErrorRate` - Error rate > 10% (critical)
- `SlowResponseTime` - P95 > 2s (warning)
- `QCFailureSpike` - QC failures elevated (warning)

## Sentry Integration

```bash
export SENTRY_DSN=https://xxx@sentry.io/xxx
export SENTRY_ENVIRONMENT=production
```
