# Performance & Optimization Guide

**Coal LIMS - Laboratory Information Management System**

Last updated: 2026-02-15

---

## Table of Contents

1. [Database Optimization](#1-database-optimization)
2. [Application Performance](#2-application-performance)
3. [Monitoring](#3-monitoring)
4. [Load Testing](#4-load-testing)
5. [Caching Strategy](#5-caching-strategy)
6. [Scaling](#6-scaling)
7. [Troubleshooting Performance Issues](#7-troubleshooting-performance-issues)

---

## 1. Database Optimization

### 1.1 Connection Pooling

The application uses SQLAlchemy with a connection pool configured in `config.py`. These settings are tuned for a production PostgreSQL deployment.

**Current settings** (`config.py` &rarr; `Config.SQLALCHEMY_ENGINE_OPTIONS`):

```python
SQLALCHEMY_ENGINE_OPTIONS = {
    "pool_size": 10,          # Base number of persistent connections
    "max_overflow": 20,       # Extra connections under burst load (up to 30 total)
    "pool_recycle": 300,      # Recycle idle connections every 5 minutes
    "pool_pre_ping": True,    # Verify connection is alive before each query
    "pool_timeout": 10,       # Max seconds to wait for a free connection
}
```

| Parameter | Value | Explanation |
|-----------|-------|-------------|
| `pool_size` | 10 | Permanent connections kept open in the pool |
| `max_overflow` | 20 | Temporary connections created when all 10 base connections are busy (max total = 30) |
| `pool_recycle` | 300 | Connections older than 5 minutes are transparently replaced (prevents stale connections) |
| `pool_pre_ping` | True | Sends a lightweight `SELECT 1` before each checkout to detect broken connections |
| `pool_timeout` | 10 | If no connection is available within 10 seconds, raise `TimeoutError` |

**Tuning guidelines:**

- For **small deployments** (1-5 concurrent users): `pool_size=5`, `max_overflow=10`
- For **medium deployments** (5-20 concurrent users): current settings are appropriate
- For **large deployments** (20-50+ concurrent users): `pool_size=20`, `max_overflow=30`
- Never set `pool_size + max_overflow` higher than PostgreSQL's `max_connections` (default 100) minus overhead for monitoring, backups, etc.

Check active connections in PostgreSQL:

```sql
SELECT count(*) FROM pg_stat_activity WHERE datname = 'coal_lims';
```

### 1.2 Query Optimization

#### Use `joinedload` to Prevent N+1 Queries

The N+1 query problem occurs when fetching a list of objects and then issuing individual queries for each related object. The codebase uses `joinedload` in critical paths.

**Example from `app/routes/analysis/workspace.py`:**

```python
from sqlalchemy.orm import joinedload

results = AnalysisResult.query \
    .options(joinedload(AnalysisResult.sample)) \
    .filter(...) \
    .all()
```

**Example from `app/routes/api/samples_api.py`:**

```python
results = AnalysisResult.query \
    .options(joinedload(AnalysisResult.user)) \
    .filter(...) \
    .all()
```

**When to use each loading strategy:**

| Strategy | Use When | Example |
|----------|----------|---------|
| `joinedload` | Always need the related object; small result sets | Sample + AnalysisResults on detail page |
| `subqueryload` | One-to-many with large collections | Sample + all its AnalysisResults in batch |
| `selectinload` | Many-to-many; collections with many items | Users + Roles |
| `lazy='dynamic'` | Need to further filter the relationship | Sample.analysis_results with status filter |

#### Enforce Pagination Limits

All list queries in the application use `.limit()` to prevent unbounded result sets. The codebase consistently applies these limits:

| Context | Limit | File |
|---------|-------|------|
| Sample list pages | 500 | `samples_api.py`, `chemistry/routes.py` |
| Analysis results | 200-300 | `microbiology/routes.py`, `chemistry/routes.py` |
| KPI / QC queries | 5000 | `analysis/kpi.py`, `analysis/qc.py` |
| API endpoints | 50-500 | Various API routes |
| Chat messages | 50 | `chat_api.py` |
| Reports | 100 | `reports/crud.py` |

**Rule:** Never call `.all()` on a query without a preceding `.limit()` unless the table is guaranteed to be small (e.g., SystemSetting, User).

#### Use `.count()` Instead of `len(.all())`

For cases where only the count is needed (e.g., archive totals), use the SQL `COUNT` aggregate rather than loading all rows into Python:

```python
# Bad - loads all rows into memory
total = len(Sample.query.filter_by(status='archived').all())

# Good - single COUNT query
total = Sample.query.filter_by(status='archived').count()
```

This optimization was applied in `app/labs/water_lab/chemistry/routes.py` for archive data.

### 1.3 N+1 Query Prevention Checklist

When writing new routes or modifying existing ones, check for N+1 patterns:

1. **Template loops accessing relationships:** If a Jinja2 template iterates over `samples` and accesses `sample.analysis_results` or `sample.user`, add `joinedload` to the query.
2. **API serialization:** If serializing objects to JSON and including related data, load it eagerly.
3. **Batch operations:** When processing multiple records, load all needed relationships in the initial query rather than querying inside a loop.

**Detection:** Enable SQLAlchemy query logging in development:

```python
# In config.py for development only
SQLALCHEMY_ECHO = True
```

Look for repeated similar queries in the log output. If you see the same `SELECT` statement appearing N times in sequence, you have an N+1 problem.

### 1.4 Index Strategy

PostgreSQL indexes that should exist for optimal performance:

```sql
-- Primary lookup patterns
CREATE INDEX IF NOT EXISTS idx_sample_code ON sample (sample_code);
CREATE INDEX IF NOT EXISTS idx_sample_lab_type ON sample (lab_type);
CREATE INDEX IF NOT EXISTS idx_sample_status ON sample (status);
CREATE INDEX IF NOT EXISTS idx_sample_received_date ON sample (received_date DESC);
CREATE INDEX IF NOT EXISTS idx_sample_client ON sample (client_name);

-- Analysis results (most queried table)
CREATE INDEX IF NOT EXISTS idx_analysis_sample_id ON analysis_result (sample_id);
CREATE INDEX IF NOT EXISTS idx_analysis_code ON analysis_result (analysis_code);
CREATE INDEX IF NOT EXISTS idx_analysis_status ON analysis_result (status);
CREATE INDEX IF NOT EXISTS idx_analysis_created ON analysis_result (created_at DESC);

-- Composite indexes for common filters
CREATE INDEX IF NOT EXISTS idx_sample_lab_status ON sample (lab_type, status);
CREATE INDEX IF NOT EXISTS idx_analysis_sample_code ON analysis_result (sample_id, analysis_code);

-- Audit log (grows continuously)
CREATE INDEX IF NOT EXISTS idx_audit_timestamp ON audit_log (timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_audit_user ON audit_log (user_id);
CREATE INDEX IF NOT EXISTS idx_audit_action ON audit_log (action);

-- Equipment
CREATE INDEX IF NOT EXISTS idx_equipment_type ON equipment (equipment_type);
CREATE INDEX IF NOT EXISTS idx_equipment_status ON equipment (status);
```

**Check for missing indexes:**

```sql
-- Find slow queries that may need indexes
SELECT query, calls, mean_exec_time, total_exec_time
FROM pg_stat_statements
ORDER BY mean_exec_time DESC
LIMIT 20;
```

Enable `pg_stat_statements` extension in `postgresql.conf`:

```
shared_preload_libraries = 'pg_stat_statements'
pg_stat_statements.track = all
```

### 1.5 VACUUM and ANALYZE Schedule

PostgreSQL requires regular maintenance to reclaim dead tuples and update query planner statistics.

**Recommended cron schedule** (add to PostgreSQL server's crontab):

```bash
# Daily ANALYZE to update statistics (lightweight, safe to run frequently)
0 2 * * * psql -U lims_user -d coal_lims -c "ANALYZE;"

# Weekly VACUUM to reclaim space (run during low-traffic hours)
0 3 * * 0 psql -U lims_user -d coal_lims -c "VACUUM ANALYZE;"

# Monthly VACUUM FULL on high-churn tables (locks table, schedule during maintenance window)
0 4 1 * * psql -U lims_user -d coal_lims -c "VACUUM FULL analysis_result; VACUUM FULL audit_log;"
```

**Autovacuum tuning** (in `postgresql.conf`):

```ini
autovacuum = on
autovacuum_vacuum_scale_factor = 0.1     # VACUUM when 10% of rows are dead (default 20%)
autovacuum_analyze_scale_factor = 0.05   # ANALYZE when 5% of rows change (default 10%)
autovacuum_vacuum_cost_delay = 10ms      # Reduce I/O impact
```

**Monitor autovacuum activity:**

```sql
SELECT relname, last_vacuum, last_autovacuum, last_analyze, last_autoanalyze,
       n_dead_tup, n_live_tup
FROM pg_stat_user_tables
ORDER BY n_dead_tup DESC;
```

---

## 2. Application Performance

### 2.1 Gunicorn Worker Configuration

The application uses Gunicorn as the WSGI server in production. Configuration is in `gunicorn_config.py`.

**Current settings:**

```python
# Server socket
bind = os.getenv("GUNICORN_BIND", "127.0.0.1:8000")
backlog = 2048

# Worker processes
workers = int(os.getenv("GUNICORN_WORKERS", multiprocessing.cpu_count() * 2 + 1))
worker_class = "sync"
worker_connections = 1000
threads = 2
max_requests = 1000          # Restart worker after 1000 requests (prevents memory leaks)
max_requests_jitter = 50     # Randomize restart to avoid all workers restarting at once

# Timeout
timeout = 120                # Kill worker if request takes > 120s
graceful_timeout = 30        # Wait 30s for in-flight requests during shutdown
keepalive = 5                # Keep-alive for upstream connections
```

**Docker override** (from `Dockerfile`):

```dockerfile
CMD ["gunicorn",
    "--worker-class", "gthread",  # Threaded workers (better for I/O-bound apps)
    "--workers", "4",
    "--threads", "2",
    "--bind", "0.0.0.0:5000",
    "--timeout", "120",
    "--keep-alive", "5",
    "--max-requests", "1000",
    "--max-requests-jitter", "50",
    "--access-logfile", "-",
    "--error-logfile", "-",
    "run:app"]
```

**Worker calculation guidelines:**

| Server CPU Cores | Recommended Workers | Threads | Total Concurrency |
|------------------|--------------------:|--------:|------------------:|
| 1 | 2 | 2 | 4 |
| 2 | 5 | 2 | 10 |
| 4 | 9 | 2 | 18 |
| 8 | 17 | 2 | 34 |

Formula: `workers = (CPU cores * 2) + 1`, `threads = 2`

**Key considerations:**

- Use `gthread` (threaded) worker class for this application because it is I/O-bound (database queries, file I/O).
- `max_requests = 1000` forces worker recycling, which prevents gradual memory leaks from accumulating.
- `timeout = 120` is generous; most requests should complete in under 5 seconds. If a request takes > 120s, it likely indicates a bug (infinite loop, deadlock).

### 2.2 Static File Serving with Nginx

In production, Nginx serves static files directly, bypassing Gunicorn/Flask entirely. This dramatically reduces load on the application server.

**Docker Compose** (`docker-compose.yml`) includes an Nginx service:

```yaml
nginx:
  image: nginx:alpine
  ports:
    - "80:80"
    - "443:443"
  volumes:
    - ./nginx.conf:/etc/nginx/nginx.conf:ro
    - ./app/static:/usr/share/nginx/html/static:ro
    - ./ssl:/etc/nginx/ssl:ro
  depends_on:
    - web
  profiles:
    - production
```

**Recommended `nginx.conf` for static file serving:**

```nginx
upstream lims_app {
    server web:5000;
}

server {
    listen 80;
    server_name your-domain.com;

    # Static files served directly by Nginx
    location /static/ {
        alias /usr/share/nginx/html/static/;
        expires 7d;
        add_header Cache-Control "public, immutable";
        access_log off;

        # Gzip compression
        gzip on;
        gzip_types text/css application/javascript application/json image/svg+xml;
        gzip_min_length 1000;
    }

    # Proxy all other requests to Gunicorn
    location / {
        proxy_pass http://lims_app;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        proxy_connect_timeout 10s;
        proxy_read_timeout 120s;
        proxy_send_timeout 120s;
    }

    # Health check passthrough
    location /health {
        proxy_pass http://lims_app/health;
        access_log off;
    }
}
```

### 2.3 Template Caching

Flask/Jinja2 automatically caches compiled templates in production (when `FLASK_ENV=production`). No additional configuration is needed.

**Key points:**

- In production, Jinja2 compiles templates once and caches the bytecode in memory. Subsequent renders skip the parsing step.
- In development (`FLASK_ENV=development`), templates are reloaded on every request to support live editing.
- Do not set `TEMPLATES_AUTO_RELOAD = True` in production.

**Template performance tips:**

- Avoid complex logic in templates; move calculations to the route or model layer.
- Use `{% include %}` and `{% macro %}` for reusable components (already implemented in `aggrid_macros.html`).
- Minimize the number of database calls triggered inside templates (e.g., calling `sample.analysis_results` in a loop without eager loading).

### 2.4 Session Management

Sessions are configured for security and performance in `config.py`:

```python
SESSION_COOKIE_SAMESITE = "Lax"
SESSION_COOKIE_SECURE = ENV != "development"  # HTTPS in production
SESSION_COOKIE_HTTPONLY = True                  # No JavaScript access
```

**Current state:** Sessions use Flask's default signed-cookie storage (server-side via `itsdangerous`). This means session data is stored in the client's cookie, signed with `SECRET_KEY`.

**Performance implications:**

- Cookie-based sessions require no server-side storage lookups. This is fast.
- Session data should be kept minimal (user ID, role, lab). Do not store large objects in the session.
- The `SECRET_KEY` is generated once and persisted in `instance/secret_key` for consistency across restarts.

**Future improvement:** For server-side sessions (e.g., with Redis), see [Section 5.3 Redis Integration](#53-redis-integration-future).

---

## 3. Monitoring

### 3.1 Current Monitoring Setup

The application has a comprehensive monitoring system implemented in `app/monitoring.py`.

**Request timing:**

- Every request's duration is measured via `g.start_time` in `before_request` / `after_request` hooks.
- Response time is included in the `X-Response-Time` header.
- Requests taking > 1 second are logged at `WARNING` level.
- Requests taking > 5 seconds are logged at `ERROR` level with an "Investigate immediately" flag.

**Prometheus metrics** (when `prometheus-flask-exporter` is installed):

| Metric | Type | Labels | Description |
|--------|------|--------|-------------|
| `lims_analysis_total` | Counter | `analysis_type`, `status` | Analyses performed |
| `lims_samples_total` | Counter | `client`, `sample_type` | Samples registered |
| `lims_active_users` | Gauge | - | Currently active users |
| `lims_db_query_duration_seconds` | Histogram | `query_type` | DB query latency distribution |
| `lims_qc_checks_total` | Counter | `check_type`, `result` | QC check outcomes (pass/fail/warning) |
| `lims_app_info` | Info | - | Application version and environment |

**Helper functions** for tracking metrics in application code:

```python
from app.monitoring import track_analysis, track_sample, track_db_query, QueryTimer

# Track a completed analysis
track_analysis('Mad', 'completed')

# Track a new sample
track_sample('QC', 'coal')

# Measure database query duration
with QueryTimer('select'):
    results = db.session.query(Sample).filter_by(status='active').all()
```

**Prometheus is disabled** in development and testing modes to avoid secure-cookie issues.

### 3.2 Log Files

Three structured log files are configured in `app/logging_config.py`:

| Log File | Purpose | Level | Max Size | Backups |
|----------|---------|-------|----------|---------|
| `logs/app.log` | General application events, request timing | INFO | 10 MB | 5 |
| `logs/audit.log` | User actions, data changes (ISO 17025 compliance) | INFO | 10 MB | 10 |
| `logs/security.log` | Failed logins, tampering attempts, security events | WARNING | 10 MB | 10 |

**Log format examples:**

```
# app.log
[2026-02-15 09:30:15] INFO in monitoring: GET /api/samples 200 0.1234s
[2026-02-15 09:30:20] WARNING in monitoring: Slow request: GET /reports/dashboard took 2.15s from 192.168.1.10

# audit.log
[2026-02-15 09:31:00] AUDIT INFO: User admin created sample S-2026-0150 (coal)
[2026-02-15 09:32:00] AUDIT INFO: User chemist1 approved analysis Mad for S-2026-0150

# security.log
2026-02-15 09:33:00 [SECURITY] WARNING: Failed login attempt for user 'unknown' from 192.168.1.50
2026-02-15 09:34:00 [SECURITY] WARNING: Server calculation mismatch detected for analysis Aad
```

**Accessing loggers in application code:**

```python
from app.logging_config import get_audit_logger, get_security_logger

audit = get_audit_logger()
audit.info(f"User {current_user.username} approved analysis {code}")

security = get_security_logger()
security.warning(f"Tamper attempt detected from {request.remote_addr}")
```

### 3.3 Health Check Endpoint

The `/health` endpoint is defined in `app/monitoring.py` and verifies both application and database connectivity.

**Response (healthy):**

```json
{
  "status": "healthy",
  "database": "connected"
}
```

**Response (unhealthy):**

```json
{
  "status": "unhealthy",
  "error": "connection refused"
}
```

**Used by:**

- Docker `HEALTHCHECK` (every 30 seconds, 3 retries)
- Docker Compose health condition for service dependencies
- Load balancers for backend health detection
- Monitoring tools (Prometheus blackbox exporter, uptime checks)

### 3.4 Monitoring Stack (Docker)

The full monitoring stack is defined in `docker-compose.monitoring.yml`:

```bash
# Start with monitoring
docker-compose -f docker-compose.yml -f docker-compose.monitoring.yml up -d
```

| Service | Port | Description |
|---------|------|-------------|
| Prometheus | 9090 | Metrics collection and storage (30-day retention) |
| Grafana | 3000 | Dashboard visualization (admin/admin) |
| Loki | 3100 | Log aggregation |
| Promtail | - | Log collector (ships logs to Loki) |
| Alertmanager | 9093 | Alert routing and notification |

**Pre-configured alert rules** (`monitoring/prometheus/alerts/lims_alerts.yml`):

| Alert | Condition | Severity | For |
|-------|-----------|----------|-----|
| `LIMSDown` | Application unreachable | Critical | 1 min |
| `HighErrorRate` | 5xx rate > 10% | Critical | 5 min |
| `SlowResponseTime` | p95 > 2s | Warning | 5 min |
| `HighMemoryUsage` | RSS > 500 MB | Warning | 10 min |
| `QCFailureSpike` | QC fail rate elevated | Warning | 15 min |
| `SlowDatabaseQueries` | p95 DB query > 1s | Warning | 5 min |
| `HighSampleRate` | > 100 samples/hour | Info | 30 min |
| `AnalysisBacklog` | > 500 pending analyses | Warning | 1 hour |

### 3.5 Key Metrics to Watch

**Application health:**

- `flask_http_request_total` -- Total request count by status code
- `flask_http_request_duration_seconds` -- Request latency histogram
- `lims_active_users` -- Concurrent users

**Database health:**

- `lims_db_query_duration_seconds` -- Query latency by type (select, insert, update, delete)
- PostgreSQL connection count (`pg_stat_activity`)
- Dead tuples count (`pg_stat_user_tables`)

**Business metrics:**

- `lims_samples_total` -- Sample registration rate (throughput indicator)
- `lims_analysis_total` -- Analysis completion rate
- `lims_qc_checks_total{result="fail"}` -- QC failure rate (quality indicator)

---

## 4. Load Testing

The project includes pre-built load testing scripts in the `performance/` directory using both k6 and Locust.

### 4.1 k6 Setup (Recommended)

**Installation:**

```bash
# Windows
winget install k6

# macOS
brew install k6

# Docker
docker pull grafana/k6
```

**Running tests:**

```bash
# Smoke test - quick validation (1 user, 30 seconds)
k6 run performance/smoke_test.js

# Load test - normal traffic simulation (10-20 users, 4 minutes)
k6 run performance/load_test.js

# Stress test - find system limits (50-200 users, 11 minutes)
k6 run performance/stress_test.js

# Against a specific environment
k6 run -e BASE_URL=http://production-server:5000 performance/load_test.js
```

**Test scripts overview:**

| Script | File | Duration | Users | Purpose |
|--------|------|----------|-------|---------|
| Smoke | `performance/smoke_test.js` | 30s | 1 | Verify system is working; health check + login page |
| Load | `performance/load_test.js` | ~4 min | 10-20 | Simulate typical usage: login, dashboard, samples, API, reports, logout |
| Stress | `performance/stress_test.js` | ~11 min | 50-200 | Find breaking point; ramp up until errors appear |

**Custom metrics tracked in load test:**

- `login_duration` -- Time to complete login flow
- `samples_page_duration` -- Time to load the samples list page
- `api_duration` -- Time for API calls
- `errors` -- Custom error rate

Results are saved to `performance/results.json` after each k6 run.

### 4.2 Locust Setup (Python Alternative)

**Installation:**

```bash
pip install locust
```

**Running tests:**

```bash
# Web UI mode (interactive)
locust -f performance/locustfile.py --host=http://localhost:5000
# Open http://localhost:8089 to configure and start

# Headless mode (CI/CD)
locust -f performance/locustfile.py --host=http://localhost:5000 \
    --headless -u 10 -r 2 -t 1m
```

**Pre-configured user types:**

| User Class | Weight | Tasks | Description |
|------------|--------|-------|-------------|
| `LIMSUser` | Default | Dashboard, Samples, Workspace, Reports, API | Typical lab user |
| `AdminUser` | 1 | Admin panel, Users, Settings | Administrator |
| `HealthCheckUser` | 1 | Health endpoint only | Monitoring simulation |

Locust automatically handles CSRF tokens by extracting them from the login page before posting credentials.

### 4.3 Baseline Performance Targets

| Metric | Target | Stress Threshold |
|--------|--------|------------------|
| Response time (p95) | < 2,000 ms | < 5,000 ms |
| Response time (p99) | < 3,000 ms | N/A |
| Login flow (p95) | < 3,000 ms | N/A |
| API calls (p95) | < 1,000 ms | N/A |
| Error rate | < 1% | < 10% (under normal load) |
| Health check | < 200 ms | < 1,000 ms |
| Throughput | > 50 req/s (20 users) | Degrades gracefully |

**When to re-test:**

- After adding new database queries or heavy computations
- Before major releases
- After infrastructure changes (server upgrade, database migration)
- When users report slow performance

---

## 5. Caching Strategy

### 5.1 What to Cache

**Currently cached in the application:**

| Data | Mechanism | Location | Invalidation |
|------|-----------|----------|--------------|
| Repeatability rules | `lru_cache` (function-level) | `app/utils/repeatability_loader.py` | `clear_cache()` CLI command or settings save |
| License info | In-memory cache with TTL | `app/utils/license_protection.py` | `clear_cache()` method; auto-expires |
| Sample calculations | Instance-level cache | `app/models/models.py` (`_calculations_cache`) | Per-request (object lifecycle) |
| Jinja2 templates | Bytecode cache (built-in) | Flask/Jinja2 internals | Automatic in production |

**Good candidates for additional caching:**

| Data | Why | TTL Suggestion |
|------|-----|----------------|
| Analysis rules (`analysis_rules.py`) | Rarely changes; read on every analysis | 1 hour |
| Constants / dropdown options | Static or near-static data | 24 hours |
| User permissions / allowed labs | Checked on every request | 5 minutes |
| Dashboard aggregates | Expensive queries; data changes slowly | 1-5 minutes |
| Equipment list for dropdowns | Rarely changes | 10 minutes |

### 5.2 Session Caching

Current sessions use signed cookies (no server-side storage). This is sufficient for the current user base.

**When to switch to server-side sessions:**

- Session data exceeds 4 KB (cookie size limit)
- Need to invalidate sessions server-side (e.g., force logout)
- Concurrent user count exceeds 100

**Implementation with Flask-Session + Redis:**

```python
# config.py addition (future)
SESSION_TYPE = 'redis'
SESSION_REDIS = redis.from_url(os.getenv('REDIS_URL', 'redis://localhost:6379/0'))
SESSION_PERMANENT = True
PERMANENT_SESSION_LIFETIME = timedelta(hours=8)  # Shift-length session
```

### 5.3 Redis Integration (Future)

The Docker Compose stack already includes a Redis container:

```yaml
redis:
  image: redis:7-alpine
  command: redis-server --appendonly yes --maxmemory 256mb --maxmemory-policy allkeys-lru
```

**Integration plan:**

1. **Phase 1 -- Session storage:** Move sessions from cookies to Redis (Flask-Session).
2. **Phase 2 -- Application caching:** Use Flask-Caching with Redis backend for analysis rules, dashboard data, and dropdown options.
3. **Phase 3 -- Rate limiting:** Move rate limiting state to Redis (shared across Gunicorn workers).

**Flask-Caching configuration (Phase 2):**

```python
# config.py addition (future)
CACHE_TYPE = 'RedisCache'
CACHE_REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
CACHE_DEFAULT_TIMEOUT = 300  # 5 minutes default

# Usage in routes:
from flask_caching import Cache
cache = Cache()

@cache.cached(timeout=3600, key_prefix='analysis_rules')
def get_analysis_rules():
    return load_rules_from_db()
```

---

## 6. Scaling

### 6.1 Horizontal Scaling with Load Balancer

The application is stateless (cookie-based sessions), making horizontal scaling straightforward.

**Architecture:**

```
                    ┌──────────────┐
                    │   Nginx LB   │
                    │  (port 80)   │
                    └──────┬───────┘
                           │
              ┌────────────┼────────────┐
              │            │            │
        ┌─────┴─────┐ ┌───┴──────┐ ┌──┴───────┐
        │  Web #1   │ │  Web #2  │ │  Web #3  │
        │ Gunicorn  │ │ Gunicorn │ │ Gunicorn │
        │  :5001    │ │  :5002   │ │  :5003   │
        └─────┬─────┘ └────┬─────┘ └────┬─────┘
              │            │            │
              └────────────┼────────────┘
                           │
                    ┌──────┴───────┐
                    │  PostgreSQL  │
                    │   (shared)   │
                    └──────────────┘
```

**Docker Compose scaling:**

```bash
# Scale web service to 3 instances
docker-compose up -d --scale web=3
```

**Nginx upstream configuration for multiple backends:**

```nginx
upstream lims_app {
    least_conn;  # Route to backend with fewest connections
    server web_1:5000;
    server web_2:5000;
    server web_3:5000;
}
```

**Prerequisites for horizontal scaling:**

- Move session storage to Redis (shared across instances)
- Ensure file uploads go to shared storage (NFS, S3, or Docker volume)
- Use database connection pooling (PgBouncer) if connection count becomes an issue

### 6.2 Database Read Replicas

For read-heavy workloads, PostgreSQL streaming replication can offload read queries to replica servers.

**When to consider:**

- Database CPU consistently above 70%
- Read-to-write ratio is high (typical for LIMS: many views per data entry)
- Report generation queries are impacting interactive users

**Implementation approach:**

```python
# config.py (future)
SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL')           # Primary (read-write)
SQLALCHEMY_BINDS = {
    'readonly': os.getenv('DATABASE_READONLY_URL')             # Replica (read-only)
}

# In routes, bind read-only queries to replica:
samples = db.session.query(Sample).execution_options(bind_key='readonly').all()
```

### 6.3 Background Tasks (Future)

Long-running operations should be moved to background workers to keep the web interface responsive.

**Candidates for background processing:**

| Task | Current Duration | Priority |
|------|-----------------|----------|
| PDF report generation | 2-10 seconds | High |
| Bulk sample import | 5-30 seconds | High |
| Email notifications | 1-5 seconds | Medium |
| Dashboard data aggregation | 2-5 seconds | Medium |
| Data export (CSV/Excel) | 5-20 seconds | Medium |
| Database backups | Minutes | Low |

**Celery integration plan:**

```python
# celery_config.py (future)
from celery import Celery

celery = Celery('coal_lims')
celery.config_from_object({
    'broker_url': os.getenv('REDIS_URL', 'redis://localhost:6379/1'),
    'result_backend': os.getenv('REDIS_URL', 'redis://localhost:6379/2'),
    'task_serializer': 'json',
    'result_serializer': 'json',
    'accept_content': ['json'],
    'timezone': 'Asia/Ulaanbaatar',
    'task_soft_time_limit': 300,  # 5 minute soft limit
    'task_time_limit': 600,       # 10 minute hard limit
})
```

---

## 7. Troubleshooting Performance Issues

### 7.1 Slow Query Identification

**Step 1: Check application logs for slow requests**

```bash
# Find requests taking > 1 second
grep "Slow request" logs/app.log | tail -20

# Find very slow requests (> 5 seconds)
grep "VERY SLOW REQUEST" logs/app.log
```

**Step 2: Enable PostgreSQL slow query logging**

Add to `postgresql.conf`:

```ini
log_min_duration_statement = 500   # Log queries taking > 500ms
log_statement = 'none'             # Don't log all queries (too noisy)
log_line_prefix = '%t [%p] %u@%d '
```

**Step 3: Analyze with `pg_stat_statements`**

```sql
-- Top 10 slowest queries (by average time)
SELECT query,
       calls,
       round(mean_exec_time::numeric, 2) AS avg_ms,
       round(total_exec_time::numeric, 2) AS total_ms,
       rows
FROM pg_stat_statements
ORDER BY mean_exec_time DESC
LIMIT 10;

-- Top 10 most time-consuming queries (by total time)
SELECT query,
       calls,
       round(total_exec_time::numeric, 2) AS total_ms,
       round(mean_exec_time::numeric, 2) AS avg_ms
FROM pg_stat_statements
ORDER BY total_exec_time DESC
LIMIT 10;
```

**Step 4: Use `EXPLAIN ANALYZE` on slow queries**

```sql
EXPLAIN (ANALYZE, BUFFERS, FORMAT TEXT)
SELECT s.*, ar.*
FROM sample s
JOIN analysis_result ar ON ar.sample_id = s.id
WHERE s.lab_type = 'coal' AND ar.status = 'completed'
ORDER BY s.received_date DESC
LIMIT 100;
```

Look for:
- `Seq Scan` on large tables (add an index)
- `Nested Loop` with large row counts (consider a different join strategy)
- High `actual rows` vs `planned rows` (run `ANALYZE` to update statistics)

### 7.2 Memory Usage Monitoring

**Application memory:**

```bash
# Check Gunicorn worker memory usage
ps aux | grep gunicorn | awk '{print $6/1024 " MB", $0}' | sort -rn | head

# Monitor over time
watch -n 5 'ps aux | grep gunicorn | awk "{sum += \$6} END {print sum/1024 \" MB total\"}"'
```

**PostgreSQL memory:**

```sql
-- Check shared buffer usage
SELECT pg_size_pretty(pg_database_size('coal_lims')) AS db_size;

-- Cache hit ratio (should be > 99%)
SELECT
    round(100.0 * sum(blks_hit) / sum(blks_hit + blks_read), 2) AS cache_hit_ratio
FROM pg_stat_database
WHERE datname = 'coal_lims';
```

**Warning signs:**

- Worker memory growing continuously (memory leak) -- `max_requests = 1000` in Gunicorn mitigates this
- Cache hit ratio below 95% -- increase `shared_buffers` in PostgreSQL
- Swap usage increasing -- add RAM or reduce worker count

### 7.3 CPU Bottlenecks

**Identify CPU-heavy operations:**

```bash
# Check CPU usage by process
top -p $(pgrep -d, gunicorn)

# Profile a specific endpoint (development only)
# Add to route temporarily:
import cProfile
profiler = cProfile.Profile()
profiler.enable()
# ... route logic ...
profiler.disable()
profiler.dump_stats('profile_output.prof')

# Analyze with snakeviz:
pip install snakeviz
snakeviz profile_output.prof
```

**Common CPU bottlenecks in LIMS:**

| Bottleneck | Symptom | Solution |
|------------|---------|----------|
| Template rendering with large datasets | High CPU on page loads | Paginate data; use AG-Grid server-side |
| JSON serialization of large result sets | High CPU on API calls | Limit returned fields; paginate |
| Repeated calculations in loops | CPU spike during batch operations | Cache intermediate results; vectorize |
| CSRF token generation | Minor overhead per request | Already optimized (no action needed) |

### 7.4 Quick Diagnostic Checklist

When users report "the system is slow", work through this checklist:

1. **Check health endpoint:** `curl http://localhost:5000/health` -- Is the database connected?
2. **Check application logs:** `tail -50 logs/app.log` -- Any slow request warnings?
3. **Check database connections:** `SELECT count(*) FROM pg_stat_activity;` -- Pool exhaustion?
4. **Check disk space:** `df -h` -- Log files filling up?
5. **Check CPU/Memory:** `top` or `htop` -- Any runaway process?
6. **Check PostgreSQL locks:** `SELECT * FROM pg_locks WHERE NOT granted;` -- Deadlocks?
7. **Check recent changes:** `git log --oneline -10` -- Was new code deployed?
8. **Check Prometheus metrics:** `http://localhost:9090` -- Any spike in error rate or latency?

---

## Appendix: Configuration Reference

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | SQLite (dev) | PostgreSQL connection string |
| `FLASK_ENV` | `production` | `development` or `production` |
| `SECRET_KEY` | Auto-generated | Session signing key |
| `REDIS_URL` | `redis://redis:6379/0` | Redis connection (Docker) |
| `GUNICORN_WORKERS` | `CPU * 2 + 1` | Number of Gunicorn workers |
| `GUNICORN_BIND` | `127.0.0.1:8000` | Gunicorn bind address |
| `GUNICORN_LOG_LEVEL` | `info` | Gunicorn log verbosity |
| `SENTRY_DSN` | (none) | Sentry error tracking DSN |
| `SENTRY_ENVIRONMENT` | (none) | Sentry environment tag |

### Key File Locations

| File | Purpose |
|------|---------|
| `config.py` | Application configuration (DB pool, sessions, security) |
| `gunicorn_config.py` | Gunicorn WSGI server configuration |
| `app/monitoring.py` | Request timing, Prometheus metrics, health check |
| `app/logging_config.py` | Structured logging (app, audit, security) |
| `docker-compose.yml` | Main Docker stack (app, PostgreSQL, Redis, Nginx) |
| `docker-compose.monitoring.yml` | Monitoring stack (Prometheus, Grafana, Loki, Alertmanager) |
| `monitoring/prometheus/prometheus.yml` | Prometheus scrape configuration |
| `monitoring/prometheus/alerts/lims_alerts.yml` | Alert rules |
| `monitoring/alertmanager/alertmanager.yml` | Alert routing configuration |
| `performance/load_test.js` | k6 load test script |
| `performance/locustfile.py` | Locust load test script |
