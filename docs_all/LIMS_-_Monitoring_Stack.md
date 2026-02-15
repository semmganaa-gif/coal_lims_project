# LIMS - Monitoring Stack

This document has been consolidated into the comprehensive performance guide.

See **[Performance & Optimization Guide](Performance_Optimization_Guide.md)** -- specifically:

- **Section 3: Monitoring** -- current monitoring setup, log files, health check, Prometheus metrics
- **Section 3.4: Monitoring Stack (Docker)** -- Prometheus, Grafana, Loki, Alertmanager configuration
- **Section 3.5: Key Metrics to Watch** -- application, database, and business metrics

**Quick start** (unchanged):

```bash
# Start main app + monitoring stack
docker-compose -f docker-compose.yml -f docker-compose.monitoring.yml up -d
```

| Service | Port | URL |
|---------|------|-----|
| Grafana | 3000 | http://localhost:3000 (admin/admin) |
| Prometheus | 9090 | http://localhost:9090 |
| Alertmanager | 9093 | http://localhost:9093 |
| Loki | 3100 | http://localhost:3100 |
