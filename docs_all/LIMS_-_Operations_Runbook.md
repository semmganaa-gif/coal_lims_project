# LIMS - Operations Runbook

**Last Updated:** 2026-02-15
**System:** Coal LIMS - Laboratory Information Management System (4 labs: Coal, Water, Microbiology, Petrography)
**Stack:** Flask + PostgreSQL + Redis + Nginx (Docker / Bare Metal / Windows Server)

> **Note:** Container and database names use the `coal_lims` prefix throughout. This is the production infrastructure naming convention and applies to all 4 laboratory modules.

---

## Table of Contents

1. [Quick Reference](#1-quick-reference)
2. [Daily Operations](#2-daily-operations)
3. [Startup and Shutdown Procedures](#3-startup-and-shutdown-procedures)
4. [Backup and Restore](#4-backup-and-restore)
5. [Monitoring and Alerts](#5-monitoring-and-alerts)
6. [Troubleshooting Guide](#6-troubleshooting-guide)
7. [Rollback Procedures](#7-rollback-procedures)
8. [User Management](#8-user-management)
9. [Database Maintenance](#9-database-maintenance)
10. [SSL Certificate Renewal](#10-ssl-certificate-renewal)
11. [Emergency Contacts and Escalation](#11-emergency-contacts-and-escalation)

---

## 1. Quick Reference

### Service Map

| Service | Port | Container Name | Health Check | Logs |
|---------|------|----------------|--------------|------|
| Flask App | 5000 | `coal_lims_web` | `curl http://localhost:5000/health` | `logs/app.log`, `logs/audit.log` |
| PostgreSQL | 5432 | `coal_lims_db` | `pg_isready -U lims_user -d coal_lims` | `docker logs coal_lims_db` |
| Redis | 6379 | `coal_lims_redis` | `redis-cli ping` | `docker logs coal_lims_redis` |
| Nginx | 80/443 | `coal_lims_nginx` | `curl -s -o /dev/null -w "%{http_code}" http://localhost` | `/var/log/nginx/coal_lims_*.log` |

### Monitoring Stack (Optional)

| Service | Port | Container Name | Purpose |
|---------|------|----------------|---------|
| Prometheus | 9090 | `coal_lims_prometheus` | Metrics collection |
| Grafana | 3000 | `coal_lims_grafana` | Dashboard visualization |
| Loki | 3100 | `coal_lims_loki` | Log aggregation |
| Alertmanager | 9093 | `coal_lims_alertmanager` | Alert routing |

### Staging Environment

| Service | Port | Container Name |
|---------|------|----------------|
| Flask App (staging) | 5001 | `coal_lims_staging_web` |
| PostgreSQL (staging) | 5433 | `coal_lims_staging_db` |
| Redis (staging) | 6380 | `coal_lims_staging_redis` |
| Adminer (staging) | 8080 | `coal_lims_staging_adminer` |

### Key File Locations

| Purpose | Path (Linux) | Path (Windows) |
|---------|-------------|----------------|
| Application root | `/var/www/coal_lims_project` | `D:\coal_lims_project` |
| Environment config | `.env` (project root) | `.env` (project root) |
| Application config | `config.py` (project root) | `config.py` (project root) |
| Application logs | `logs/app.log` | `logs\app.log` |
| Audit logs | `logs/audit.log` | `logs\audit.log` |
| Security logs | `instance/logs/security.log` | `instance\logs\security.log` |
| Backup directory | `backups/` | `backups\` |
| Database migrations | `migrations/` | `migrations\` |
| Uploads | `app/static/uploads/certificates/` | `app\static\uploads\certificates\` |

---

## 2. Daily Operations

### 2.1 Morning Health Check Checklist

Perform these checks at the start of each working day (recommended before 09:00).

**Application Health:**

```bash
# Docker environment
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" | grep coal_lims

# Direct health check
curl -s http://localhost:5000/health
# Expected: HTTP 200 with JSON response

# Check application uptime and resource usage
docker stats --no-stream coal_lims_web coal_lims_db coal_lims_redis
```

**Windows Server:**

```powershell
# Check NSSM service status
nssm status CoalLIMS

# Check if Waitress is responding
Invoke-WebRequest -Uri http://localhost:8000/health -UseBasicParsing | Select-Object StatusCode
```

**Database Health:**

```bash
# Check PostgreSQL connections
docker exec coal_lims_db psql -U lims_user -d coal_lims -c "SELECT count(*) FROM pg_stat_activity WHERE datname='coal_lims';"

# Check database size
docker exec coal_lims_db psql -U lims_user -d coal_lims -c "SELECT pg_size_pretty(pg_database_size('coal_lims'));"
```

**Redis Health:**

```bash
docker exec coal_lims_redis redis-cli info memory | grep used_memory_human
docker exec coal_lims_redis redis-cli dbsize
```

### 2.2 Log Review

Review logs for errors or unusual patterns that occurred overnight.

```bash
# Application errors from the last 24 hours
docker logs coal_lims_web --since 24h 2>&1 | grep -i "error\|exception\|critical"

# Security events (failed logins, tampering attempts)
tail -100 logs/security.log

# Audit log (user actions, data changes)
tail -100 logs/audit.log

# Nginx access patterns (top 10 IPs with most requests)
awk '{print $1}' /var/log/nginx/coal_lims_access.log | sort | uniq -c | sort -rn | head -10
```

### 2.3 Backup Verification

Verify that the nightly backup completed successfully.

```bash
# Linux: Check that today's backup file exists and has reasonable size
ls -lh backups/ | head -5

# Verify the latest backup is not empty (should be at least several KB)
LATEST=$(ls -t backups/lims_backup_*.sql* 2>/dev/null | head -1)
if [ -n "$LATEST" ]; then
    echo "Latest backup: $LATEST ($(stat --printf='%s' "$LATEST") bytes)"
else
    echo "WARNING: No backup files found!"
fi
```

**Windows:**

```powershell
# Check backup directory
Get-ChildItem D:\coal_lims_project\backups -Filter *.sql | Sort-Object LastWriteTime -Descending | Select-Object -First 5

# Check backup log
Get-Content D:\coal_lims_project\logs\backup.log -Tail 10
```

### 2.4 Disk Space Check

```bash
# Check disk usage
df -h / /var/lib/docker

# Docker volume sizes
docker system df -v

# Database-specific disk usage
docker exec coal_lims_db psql -U lims_user -d coal_lims -c \
  "SELECT schemaname, tablename, pg_size_pretty(pg_total_relation_size(schemaname || '.' || tablename)) AS size
   FROM pg_tables WHERE schemaname = 'public' ORDER BY pg_total_relation_size(schemaname || '.' || tablename) DESC LIMIT 10;"
```

---

## 3. Startup and Shutdown Procedures

### 3.1 Development Environment

**Starting (Linux/macOS):**

```bash
cd /path/to/coal_lims_project
source venv/bin/activate
export FLASK_ENV=development
flask run --host=0.0.0.0 --port=5000 --debug
```

**Starting (Windows):**

```powershell
cd D:\coal_lims_project
.\venv\Scripts\activate
set FLASK_ENV=development
flask run --host=0.0.0.0 --port=5000 --debug
```

**Stopping:** Press `Ctrl+C` in the terminal.

### 3.2 Production - Docker Compose

**Full Stack Startup:**

```bash
cd /var/www/coal_lims_project

# Start all services (web, db, redis)
docker-compose up -d

# Start with Nginx (production profile)
docker-compose --profile production up -d

# Verify all containers are healthy
docker-compose ps
```

**Start with Monitoring Stack:**

```bash
docker-compose -f docker-compose.yml -f docker-compose.monitoring.yml up -d
```

**Start Staging Environment:**

```bash
docker-compose -f docker-compose.staging.yml up -d
```

**Graceful Shutdown:**

```bash
# Graceful stop (waits for in-flight requests to complete)
docker-compose stop

# Full shutdown and remove containers (data persists in volumes)
docker-compose down

# Full shutdown including monitoring
docker-compose -f docker-compose.yml -f docker-compose.monitoring.yml down
```

**Order of operations for shutdown:**
1. Stop Nginx first (stops accepting new connections)
2. Stop web application (completes in-flight requests)
3. Stop Redis
4. Stop PostgreSQL last

```bash
docker stop coal_lims_nginx
sleep 5
docker stop coal_lims_web
docker stop coal_lims_redis
docker stop coal_lims_db
```

### 3.3 Production - Systemd (Bare Metal Linux)

```bash
# Start the application
sudo systemctl start coal_lims

# Stop the application
sudo systemctl stop coal_lims

# Restart (graceful reload of Gunicorn workers)
sudo systemctl restart coal_lims

# Check status
sudo systemctl status coal_lims

# View live logs
sudo journalctl -u coal_lims -f

# Start/stop Nginx
sudo systemctl start nginx
sudo systemctl stop nginx
```

### 3.4 Production - Windows Server (NSSM + Waitress)

**Start:**

```powershell
nssm start CoalLIMS
```

**Stop:**

```powershell
nssm stop CoalLIMS
```

**Restart:**

```powershell
nssm restart CoalLIMS
```

**Check Status:**

```powershell
nssm status CoalLIMS
```

**Manual Start (without NSSM):**

```powershell
cd D:\coal_lims_project
.\venv\Scripts\activate
python run_production.py
```

### 3.5 Post-Startup Verification

After any startup, verify the system is fully operational:

```bash
# 1. Health endpoint
curl -f http://localhost:5000/health

# 2. Login page loads
curl -s -o /dev/null -w "%{http_code}" http://localhost:5000/login
# Expected: 200

# 3. Database connectivity (check via application logs)
docker logs coal_lims_web --tail 20 | grep -i "database\|connection"

# 4. Redis connectivity
docker exec coal_lims_redis redis-cli ping
# Expected: PONG
```

---

## 4. Backup and Restore

### 4.1 Database Backup

#### Manual Backup (Docker)

```bash
# Full database dump (compressed)
docker exec coal_lims_db pg_dump -U lims_user -d coal_lims | gzip > backups/lims_backup_$(date +%Y%m%d_%H%M%S).sql.gz

# Schema only
docker exec coal_lims_db pg_dump -U lims_user -d coal_lims --schema-only > backups/lims_schema_$(date +%Y%m%d).sql

# Data only
docker exec coal_lims_db pg_dump -U lims_user -d coal_lims --data-only | gzip > backups/lims_data_$(date +%Y%m%d).sql.gz

# Specific tables
docker exec coal_lims_db pg_dump -U lims_user -d coal_lims -t sample -t analysis_result | gzip > backups/lims_samples_$(date +%Y%m%d).sql.gz
```

#### Manual Backup (Bare Metal Linux)

```bash
pg_dump -U lims_user -h localhost coal_lims | gzip > /var/backups/coal_lims/lims_backup_$(date +%Y%m%d_%H%M%S).sql.gz
```

#### Manual Backup (Windows)

```powershell
& "C:\Program Files\PostgreSQL\18\bin\pg_dump.exe" -U postgres -d coal_lims > D:\coal_lims_project\backups\lims_%date:~0,4%%date:~5,2%%date:~8,2%.sql
```

### 4.2 Automated Backup Schedule

#### Linux (Cron)

Add to crontab (`sudo crontab -e`):

```cron
# Daily database backup at 02:00
0 2 * * * /opt/scripts/backup_lims.sh >> /var/log/backup_lims.log 2>&1

# Weekly full backup (files + database) on Sunday at 03:00
0 3 * * 0 /opt/scripts/full_backup_lims.sh >> /var/log/backup_lims.log 2>&1

# Monthly cleanup of old backups on the 1st at 04:00
0 4 1 * * find /var/backups/coal_lims -name "lims_backup_*.sql.gz" -mtime +90 -delete
```

**Backup Script (`/opt/scripts/backup_lims.sh`):**

```bash
#!/bin/bash
set -e

BACKUP_DIR="/var/backups/coal_lims"
DATE=$(date +%Y%m%d_%H%M%S)
FILENAME="lims_backup_${DATE}.sql.gz"
RETENTION_DAYS=30

mkdir -p "$BACKUP_DIR"

# Database backup
pg_dump -U lims_user coal_lims | gzip > "$BACKUP_DIR/$FILENAME"

# Verify backup is not empty
if [ ! -s "$BACKUP_DIR/$FILENAME" ]; then
    echo "$(date): ERROR - Backup file is empty!" >&2
    exit 1
fi

# Remove old backups
find "$BACKUP_DIR" -name "lims_backup_*.sql.gz" -mtime +$RETENTION_DAYS -delete

echo "$(date): Backup successful - $FILENAME ($(du -h "$BACKUP_DIR/$FILENAME" | cut -f1))"
```

#### Windows (Task Scheduler)

The scheduled backup is configured via `D:\coal_lims_project\scripts\scheduled_backup.bat`:

1. Open Task Scheduler: `Win + R` then `taskschd.msc`
2. Create Basic Task named "LIMS Daily Backup"
3. Trigger: Daily at 02:00 AM
4. Action: Start a program: `D:\coal_lims_project\scripts\scheduled_backup.bat`
5. Start in: `D:\coal_lims_project`
6. Properties: "Run whether user is logged on or not", "Run with highest privileges"
7. Settings: "Run task as soon as possible after a scheduled start is missed"

Or via PowerShell (Administrator):

```powershell
$action = New-ScheduledTaskAction -Execute "D:\coal_lims_project\scripts\scheduled_backup.bat" -WorkingDirectory "D:\coal_lims_project"
$trigger = New-ScheduledTaskTrigger -Daily -At 2:00AM
$settings = New-ScheduledTaskSettingsSet -RunOnlyIfNetworkAvailable -WakeToRun -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries
$principal = New-ScheduledTaskPrincipal -UserId "SYSTEM" -LogonType ServiceAccount -RunLevel Highest
Register-ScheduledTask -TaskName "LIMS Daily Backup" -Action $action -Trigger $trigger -Settings $settings -Principal $principal -Description "PostgreSQL database backup every day at 2:00 AM"
```

Backup files are stored in `D:\coal_lims_project\backups\` with 30-day retention.

### 4.3 File Backup

```bash
# Application code (excluding virtualenv, caches, and local data)
tar -czf /var/backups/coal_lims_app_$(date +%Y%m%d).tar.gz \
    /var/www/coal_lims_project \
    --exclude='venv' \
    --exclude='*.pyc' \
    --exclude='__pycache__' \
    --exclude='instance' \
    --exclude='backups' \
    --exclude='logs'

# Instance directory (uploads, local secrets)
tar -czf /var/backups/coal_lims_instance_$(date +%Y%m%d).tar.gz \
    /var/www/coal_lims_project/instance

# Uploads only
tar -czf /var/backups/coal_lims_uploads_$(date +%Y%m%d).tar.gz \
    /var/www/coal_lims_project/app/static/uploads
```

### 4.4 Database Restore

**IMPORTANT:** Always test restore on a staging environment first. Never restore directly to production without verification.

#### Restore to Docker

```bash
# Stop the web application first
docker stop coal_lims_web

# Restore from compressed backup
gunzip -c backups/lims_backup_20260215_020000.sql.gz | docker exec -i coal_lims_db psql -U lims_user -d coal_lims

# Or for uncompressed SQL
docker exec -i coal_lims_db psql -U lims_user -d coal_lims < backups/lims_20260215.sql

# Restart web application
docker start coal_lims_web
```

#### Restore to Bare Metal

```bash
# Stop the application
sudo systemctl stop coal_lims

# Drop and recreate database (DESTRUCTIVE - use with caution)
sudo -u postgres psql -c "DROP DATABASE IF EXISTS coal_lims;"
sudo -u postgres psql -c "CREATE DATABASE coal_lims OWNER lims_user;"

# Restore
gunzip -c /var/backups/coal_lims/lims_backup_20260215_020000.sql.gz | psql -U lims_user -h localhost -d coal_lims

# Start the application
sudo systemctl start coal_lims
```

#### Restore on Windows

```powershell
# Stop the service
nssm stop CoalLIMS

# Restore using psql
& "C:\Program Files\PostgreSQL\18\bin\psql.exe" -U postgres -d coal_lims -f D:\coal_lims_project\backups\lims_20260215.sql

# Start the service
nssm start CoalLIMS
```

#### Restore to Staging for Verification

```bash
# Restore production backup to staging database
docker-compose -f docker-compose.staging.yml up -d db
gunzip -c backups/lims_backup_20260215_020000.sql.gz | docker exec -i coal_lims_staging_db psql -U lims_user -d coal_lims_staging

# Start staging web to verify
docker-compose -f docker-compose.staging.yml up -d web

# Verify at http://localhost:5001
curl -s http://localhost:5001/health
```

---

## 5. Monitoring and Alerts

### 5.1 What to Monitor

| Metric | Warning Threshold | Critical Threshold | Check Frequency |
|--------|-------------------|-------------------|-----------------|
| Application health (`/health`) | N/A | Not responding for 1 min | Every 30 seconds |
| HTTP error rate (5xx) | > 5% over 5 min | > 10% over 5 min | Every 15 seconds |
| Response time (p95) | > 2 seconds | > 5 seconds | Every 15 seconds |
| Memory usage | > 500 MB | > 1 GB | Every 30 seconds |
| Database connections | > 20 active | > 40 active | Every 15 seconds |
| Database query time (p95) | > 1 second | > 3 seconds | Every 15 seconds |
| Disk usage | > 80% | > 90% | Every 5 minutes |
| Backup completion | Missed 1 backup | Missed 2+ consecutive | Daily |
| SSL certificate expiry | < 30 days | < 7 days | Daily |
| QC failure rate | Elevated rate 15 min | N/A | Every 15 seconds |
| Analysis backlog | > 500 pending | > 1000 pending | Every 5 minutes |

### 5.2 Monitoring Stack Setup

The project includes a full monitoring stack via Docker Compose:

```bash
# Start monitoring alongside the main application
docker-compose -f docker-compose.yml -f docker-compose.monitoring.yml up -d

# Access dashboards
# Prometheus: http://localhost:9090
# Grafana:    http://localhost:3000 (default: admin/admin)
# Loki:       http://localhost:3100
```

**Prometheus** scrapes the Flask application at `/metrics` every 15 seconds.

**Grafana** provides visualization dashboards with provisioned datasources for both Prometheus (metrics) and Loki (logs).

**Alertmanager** routes alerts by severity:
- **Critical** (e.g., LIMSDown, HighErrorRate): immediate notification, 1-hour repeat
- **Warning** (e.g., SlowResponseTime, HighMemoryUsage): 1-minute group wait, 4-hour repeat
- **Info** (e.g., HighSampleRate): 10-minute group wait, 24-hour repeat

### 5.3 Configured Alert Rules

These alerts are defined in `monitoring/prometheus/alerts/lims_alerts.yml`:

| Alert | Condition | Severity |
|-------|-----------|----------|
| `LIMSDown` | Application unreachable for 1 minute | Critical |
| `HighErrorRate` | 5xx error rate > 10% for 5 minutes | Critical |
| `SlowResponseTime` | p95 response time > 2 seconds for 5 minutes | Warning |
| `HighMemoryUsage` | Process memory > 500 MB for 10 minutes | Warning |
| `SlowDatabaseQueries` | p95 DB query time > 1 second for 5 minutes | Warning |
| `QCFailureSpike` | QC check failure rate elevated for 15 minutes | Warning |
| `HighSampleRate` | Sample registration > 100/hour for 30 minutes | Info |
| `AnalysisBacklog` | > 500 pending analyses for 1 hour | Warning |

### 5.4 Log Locations

| Log | Location | Contents |
|-----|----------|----------|
| Application log | `logs/app.log` | General application events, errors |
| Audit log | `logs/audit.log` | User actions, data modifications, ISO 17025 audit trail |
| Security log | `instance/logs/security.log` | Failed logins, tampering attempts, calculation mismatches |
| Backup log | `logs/backup.log` | Backup job results (Windows Task Scheduler) |
| Gunicorn access | `/var/log/coal_lims/access.log` | HTTP request access log (Linux) |
| Gunicorn error | `/var/log/coal_lims/error.log` | WSGI server errors (Linux) |
| Nginx access | `/var/log/nginx/coal_lims_access.log` | Reverse proxy access log |
| Nginx error | `/var/log/nginx/coal_lims_error.log` | Reverse proxy errors |

### 5.5 Log Rotation

**Linux (logrotate)** -- `/etc/logrotate.d/coal_lims`:

```
/var/log/coal_lims/*.log {
    daily
    rotate 14
    compress
    delaycompress
    notifempty
    create 0640 www-data www-data
    sharedscripts
    postrotate
        systemctl reload coal_lims > /dev/null 2>&1 || true
    endscript
}
```

**Application-level rotation** is configured via `.env`:

```
LOG_MAX_BYTES=10485760   # 10 MB per log file
LOG_BACKUP_COUNT=10      # Keep 10 rotated files
```

### 5.6 Simple Health Check Script (No Monitoring Stack)

If you are not using the Prometheus/Grafana stack, use this script for basic health monitoring:

```bash
#!/bin/bash
# /opt/scripts/health_check.sh
# Add to cron: */5 * * * * /opt/scripts/health_check.sh

URL="https://lims.energyresources.mn/login"
STATUS=$(curl -s -o /dev/null -w "%{http_code}" --max-time 10 "$URL")

if [ "$STATUS" -eq 200 ]; then
    echo "$(date): LIMS is UP (HTTP $STATUS)"
    exit 0
else
    echo "$(date): LIMS is DOWN (HTTP $STATUS)"
    # Send alert email (configure SMTP settings)
    echo "LIMS application is down! HTTP status: $STATUS at $(date)" | \
        mail -s "ALERT: Coal LIMS Down" admin@energyresources.mn
    exit 1
fi
```

---

## 6. Troubleshooting Guide

### 6.1 Application Not Responding (502/504 Gateway Errors)

**Symptoms:** Browser shows 502 Bad Gateway or 504 Gateway Timeout. The `/health` endpoint does not respond.

**Diagnosis and Resolution:**

```bash
# 1. Check if the container/process is running
docker ps -a | grep coal_lims_web
# If status is "Exited", the container crashed

# 2. Check application logs for the cause
docker logs coal_lims_web --tail 100

# 3. Check resource exhaustion
docker stats --no-stream coal_lims_web
# Look for high CPU (>90%) or memory approaching the limit

# 4. Check Gunicorn worker status
docker exec coal_lims_web ps aux | grep gunicorn
# Should show 4 workers + 1 master process

# 5. Check if the port is being listened on
docker exec coal_lims_web ss -tlnp | grep 5000

# 6. Restart the application
docker restart coal_lims_web

# 7. If repeated crashes, check for memory leaks
docker logs coal_lims_web 2>&1 | grep -i "killed\|oom\|memory"
```

**Windows (Waitress):**

```powershell
# Check if the process is running
Get-Process -Name python -ErrorAction SilentlyContinue

# Check the service
nssm status CoalLIMS

# Check port binding
netstat -ano | findstr ":8000"

# Restart the service
nssm restart CoalLIMS
```

### 6.2 Database Connection Issues

**Symptoms:** Application logs show `OperationalError`, `psycopg2.OperationalError`, connection refused, or "too many connections".

**Diagnosis and Resolution:**

```bash
# 1. Verify PostgreSQL is running
docker exec coal_lims_db pg_isready -U lims_user -d coal_lims
# Expected: accepting connections

# 2. Check current connections
docker exec coal_lims_db psql -U lims_user -d coal_lims -c \
  "SELECT count(*), state FROM pg_stat_activity WHERE datname='coal_lims' GROUP BY state;"

# 3. Check max connections setting
docker exec coal_lims_db psql -U lims_user -d coal_lims -c "SHOW max_connections;"

# 4. If "too many connections", kill idle connections
docker exec coal_lims_db psql -U lims_user -d coal_lims -c \
  "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname='coal_lims' AND state='idle' AND state_change < NOW() - INTERVAL '10 minutes';"

# 5. Verify DATABASE_URL is correct in .env
docker exec coal_lims_web env | grep DATABASE_URL

# 6. Test connectivity from the web container
docker exec coal_lims_web python -c "
from sqlalchemy import create_engine, text
import os
engine = create_engine(os.getenv('DATABASE_URL'))
with engine.connect() as conn:
    result = conn.execute(text('SELECT 1'))
    print('Database connection successful:', result.fetchone())
"

# 7. Check PostgreSQL logs
docker logs coal_lims_db --tail 50
```

**Connection pool settings** (in `config.py`):

| Setting | Value | Description |
|---------|-------|-------------|
| `pool_size` | 10 | Base number of connections |
| `max_overflow` | 20 | Additional connections when pool is exhausted |
| `pool_recycle` | 300 | Recycle connections every 5 minutes |
| `pool_pre_ping` | True | Verify connection is alive before use |
| `pool_timeout` | 10 | Seconds to wait for a connection from pool |

If the application consistently runs out of connections, increase `pool_size` and `max_overflow` in `config.py`, and also increase `max_connections` in PostgreSQL configuration.

### 6.3 Migration Failures

**Symptoms:** `flask db upgrade` fails with errors. Application fails to start after a code update.

**Diagnosis and Resolution:**

```bash
# 1. Check current migration version
flask db current

# 2. View migration history
flask db history --verbose

# 3. If migration fails due to an existing table or column
# Check what the migration is trying to do
flask db show <revision_id>

# 4. Roll back the failed migration
flask db downgrade -1

# 5. Retry the upgrade
flask db upgrade

# 6. If migration state is inconsistent, check alembic_version table
docker exec coal_lims_db psql -U lims_user -d coal_lims -c "SELECT * FROM alembic_version;"

# 7. If the alembic_version table is out of sync, manually set it
# WARNING: Only do this if you are certain of the correct version
docker exec coal_lims_db psql -U lims_user -d coal_lims -c "UPDATE alembic_version SET version_num='<correct_revision>';"

# 8. For merge conflicts in migration files
flask db merge heads -m "merge heads"
flask db upgrade
```

**Common Migration Errors:**

| Error | Cause | Solution |
|-------|-------|----------|
| `relation already exists` | Table/column already created manually | Add `if_not_exists=True` or skip |
| `column does not exist` | Migration order wrong | Check `depends_on` in migration |
| `multiple head revisions` | Branch divergence | Run `flask db merge heads` |
| `Target database is not up to date` | Pending migrations | Run `flask db upgrade` |
| `Can't locate revision` | Missing migration file | Restore from git or set version manually |

### 6.4 Permission Errors

**Symptoms:** `PermissionError`, "Permission denied" in logs, file upload failures.

**Diagnosis and Resolution:**

```bash
# Linux: Check file ownership
ls -la /var/www/coal_lims_project/
ls -la /var/www/coal_lims_project/instance/
ls -la /var/www/coal_lims_project/logs/
ls -la /var/www/coal_lims_project/app/static/uploads/

# Fix ownership (Linux - bare metal with Gunicorn)
sudo chown -R www-data:www-data /var/www/coal_lims_project/instance
sudo chown -R www-data:www-data /var/www/coal_lims_project/logs
sudo chown -R www-data:www-data /var/www/coal_lims_project/app/static/uploads

# Fix permissions
sudo chmod -R 755 /var/www/coal_lims_project/instance
sudo chmod -R 755 /var/www/coal_lims_project/logs
sudo chmod 600 /var/www/coal_lims_project/.env  # Restrict .env access

# Docker: Check container user
docker exec coal_lims_web whoami
# Should be: lims (non-root user as per Dockerfile)

# Docker: Fix volume permissions
docker exec -u root coal_lims_web chown -R lims:lims /app/instance /app/logs /app/backups
```

**Windows:**

```powershell
# Check permissions
icacls D:\coal_lims_project\instance
icacls D:\coal_lims_project\logs
icacls D:\coal_lims_project\backups

# Grant permissions to SYSTEM (for Task Scheduler backups)
icacls D:\coal_lims_project\backups /grant "SYSTEM:(OI)(CI)F"
```

### 6.5 Performance Degradation

**Symptoms:** Slow page loads, timeouts, high CPU or memory usage.

**Diagnosis and Resolution:**

```bash
# 1. Check system resources
docker stats --no-stream

# 2. Check for slow database queries
docker exec coal_lims_db psql -U lims_user -d coal_lims -c \
  "SELECT pid, now() - pg_stat_activity.query_start AS duration, query, state
   FROM pg_stat_activity
   WHERE datname='coal_lims' AND state != 'idle'
   ORDER BY duration DESC LIMIT 10;"

# 3. Check for table bloat (requires VACUUM)
docker exec coal_lims_db psql -U lims_user -d coal_lims -c \
  "SELECT relname, n_dead_tup, n_live_tup, last_vacuum, last_autovacuum
   FROM pg_stat_user_tables
   ORDER BY n_dead_tup DESC LIMIT 10;"

# 4. Check for missing indexes
docker exec coal_lims_db psql -U lims_user -d coal_lims -c \
  "SELECT relname, seq_scan, idx_scan, seq_scan - idx_scan AS too_many_seq_scans
   FROM pg_stat_user_tables
   WHERE seq_scan > idx_scan AND seq_scan > 1000
   ORDER BY too_many_seq_scans DESC LIMIT 10;"

# 5. Check Redis memory usage
docker exec coal_lims_redis redis-cli info memory

# 6. Check Gunicorn workers (are they all busy?)
docker exec coal_lims_web ps aux | grep gunicorn

# 7. Check Nginx connection queue
sudo ss -tlnp | grep ":80\|:443"

# 8. If needed, increase Gunicorn workers (currently 4 workers, 2 threads each)
# Edit Dockerfile CMD or gunicorn_config.py:
# workers = (2 * CPU_CORES) + 1
```

**Quick Performance Fixes:**

| Issue | Solution |
|-------|----------|
| Slow queries | Run `VACUUM ANALYZE` (see Section 9) |
| High memory | Restart application to clear leaked memory |
| Many concurrent users | Increase Gunicorn workers/threads |
| Large table scans | Add missing indexes |
| Static file slowness | Ensure Nginx serves static files directly |
| Redis full | Check `maxmemory-policy` (currently `allkeys-lru`) |

### 6.6 CSRF Token Errors

**Symptoms:** "CSRF token missing" or "CSRF token expired" errors on form submissions.

**Resolution:**

```bash
# 1. Verify CSRF is enabled in config
grep -i csrf config.py

# 2. Check token lifetime (default: 3600 seconds / 1 hour)
# If users leave forms open for long periods, increase WTF_CSRF_TIME_LIMIT in .env

# 3. Verify SECRET_KEY hasn't changed (changing it invalidates all sessions and tokens)
# If SECRET_KEY was regenerated, all active sessions become invalid
# Users must log in again

# 4. Check if instance/secret_key file exists and matches
cat instance/secret_key
```

### 6.7 Email Delivery Failures

**Symptoms:** Report emails not sending, "SMTP AUTH" errors, timeout errors.

**Resolution:**

```bash
# 1. Test SMTP connectivity
python -c "
import smtplib
server = smtplib.SMTP('smtp.office365.com', 587)
server.starttls()
server.login('your@email.com', 'app-password')
print('SMTP connection successful')
server.quit()
"

# 2. Verify .env settings
grep MAIL .env

# 3. Common issues:
# - SMTP AUTH not enabled in Exchange Admin for the mailbox
# - App Password required when MFA is enabled
# - Firewall blocking port 587
# - Incorrect MAIL_DEFAULT_SENDER (must match MAIL_USERNAME for Office 365)
```

### 6.8 Docker-Specific Issues

**Container Keeps Restarting:**

```bash
# Check exit code and logs
docker inspect coal_lims_web --format='{{.State.ExitCode}}'
docker logs coal_lims_web --tail 50

# Common exit codes:
# 0 = Normal shutdown
# 1 = Application error
# 137 = OOM killed (out of memory)
# 139 = Segfault
```

**Volume Permission Issues:**

```bash
# Check volume mounts
docker inspect coal_lims_web --format='{{range .Mounts}}{{.Source}} -> {{.Destination}}{{"\n"}}{{end}}'

# Fix permissions inside container
docker exec -u root coal_lims_web chown -R lims:lims /app/instance /app/logs
```

**Network Issues Between Containers:**

```bash
# Verify network exists
docker network ls | grep lims

# Check container connectivity
docker exec coal_lims_web ping -c 3 db
docker exec coal_lims_web ping -c 3 redis

# Recreate network if needed
docker-compose down
docker-compose up -d
```

---

## 7. Rollback Procedures

### 7.1 Application Code Rollback

```bash
# 1. Identify the commit to roll back to
cd /var/www/coal_lims_project
git log --oneline -10

# 2. Check out the previous stable version
git checkout <commit_hash>

# 3. Reinstall dependencies (in case requirements changed)
source venv/bin/activate
pip install -r requirements.txt

# 4. Restart the application
sudo systemctl restart coal_lims
# or
docker-compose restart web
```

**Docker image rollback:**

```bash
# If using tagged images
docker-compose down
# Edit docker-compose.yml to point to the previous image tag
docker-compose up -d
```

### 7.2 Database Migration Rollback

```bash
# Roll back the last migration
flask db downgrade -1

# Roll back to a specific revision
flask db downgrade <revision_id>

# Verify current revision
flask db current
```

**IMPORTANT:** Some migrations are irreversible (e.g., data deletions). Always check the `downgrade()` function in the migration file before rolling back.

### 7.3 Full System Rollback

In case of catastrophic failure, restore from the last known good backup:

```bash
# 1. Stop the application
docker-compose down

# 2. Restore code from git
git checkout <last_known_good_commit>

# 3. Restore database from backup
docker-compose up -d db
sleep 10  # Wait for PostgreSQL to start
gunzip -c backups/lims_backup_YYYYMMDD_HHMMSS.sql.gz | docker exec -i coal_lims_db psql -U lims_user -d coal_lims

# 4. Reinstall dependencies
docker-compose build web

# 5. Start all services
docker-compose up -d

# 6. Verify
curl -f http://localhost:5000/health
```

### 7.4 Rollback Checklist

Before performing any rollback, verify:

- [ ] Current state is documented (git hash, migration version, error description)
- [ ] Backup of current database exists
- [ ] Rollback target version identified and confirmed working
- [ ] Users notified of planned downtime
- [ ] Post-rollback verification plan ready

---

## 8. User Management

### 8.1 Create a New User

**Via Flask CLI:**

```bash
# Activate virtual environment
source venv/bin/activate  # Linux
# .\venv\Scripts\activate  # Windows

# Create admin user
flask users create <username> <password> admin

# Create regular user (analyst)
flask users create <username> <password> analyst

# Create senior analyst
flask users create <username> <password> senior
```

**Via Database (direct):**

```bash
docker exec coal_lims_db psql -U lims_user -d coal_lims -c \
  "INSERT INTO \"user\" (username, password_hash, role, is_active, allowed_labs)
   VALUES ('newuser', '<werkzeug_hash>', 'analyst', true, '{\"coal\",\"water\"}');"
```

Note: Generating the password hash requires Werkzeug:

```python
from werkzeug.security import generate_password_hash
print(generate_password_hash('the-password'))
```

### 8.2 Disable a User

```bash
# Via database
docker exec coal_lims_db psql -U lims_user -d coal_lims -c \
  "UPDATE \"user\" SET is_active = false WHERE username = 'username_here';"
```

Disabled users cannot log in but their historical audit trail and analysis records are preserved.

### 8.3 Reset a User's Password

**Via Flask CLI:**

```bash
flask users reset-password <username> <new_password>
```

**Via Python shell:**

```bash
flask shell
```

```python
from app.models import User
from app import db
from werkzeug.security import generate_password_hash

user = User.query.filter_by(username='target_user').first()
user.password_hash = generate_password_hash('new_secure_password')
db.session.commit()
print(f"Password reset for {user.username}")
```

### 8.4 View Users and Roles

```bash
docker exec coal_lims_db psql -U lims_user -d coal_lims -c \
  "SELECT id, username, role, is_active, allowed_labs, last_login FROM \"user\" ORDER BY id;"
```

### 8.5 Manage Laboratory Access

Users are granted access to specific labs via the `allowed_labs` field:

```bash
# Grant access to coal and water labs
docker exec coal_lims_db psql -U lims_user -d coal_lims -c \
  "UPDATE \"user\" SET allowed_labs = '{\"coal\",\"water\"}' WHERE username = 'analyst1';"

# Grant access to all labs
docker exec coal_lims_db psql -U lims_user -d coal_lims -c \
  "UPDATE \"user\" SET allowed_labs = '{\"coal\",\"water\",\"microbiology\",\"petrography\"}' WHERE username = 'senior1';"
```

### 8.6 Available Roles

| Role | Description | Typical Permissions |
|------|-------------|---------------------|
| `admin` | System administrator | Full access, user management, settings |
| `senior` | Senior analyst | Approve/reject results, view all labs |
| `analyst` | Laboratory analyst | Enter results, view own lab |
| `viewer` | Read-only user | View reports and dashboards |

---

## 9. Database Maintenance

### 9.1 VACUUM and ANALYZE

PostgreSQL requires periodic `VACUUM` to reclaim storage from deleted/updated rows, and `ANALYZE` to update query planner statistics.

**Autovacuum** is enabled by default in PostgreSQL, but manual runs are recommended after bulk operations:

```bash
# Run VACUUM ANALYZE on all tables
docker exec coal_lims_db psql -U lims_user -d coal_lims -c "VACUUM ANALYZE;"

# VACUUM a specific table
docker exec coal_lims_db psql -U lims_user -d coal_lims -c "VACUUM ANALYZE sample;"
docker exec coal_lims_db psql -U lims_user -d coal_lims -c "VACUUM ANALYZE analysis_result;"

# VACUUM FULL (rewrites table, requires exclusive lock - schedule during off-hours)
docker exec coal_lims_db psql -U lims_user -d coal_lims -c "VACUUM FULL ANALYZE;"

# Check autovacuum status
docker exec coal_lims_db psql -U lims_user -d coal_lims -c \
  "SELECT relname, last_vacuum, last_autovacuum, last_analyze, last_autoanalyze, n_dead_tup
   FROM pg_stat_user_tables ORDER BY n_dead_tup DESC;"
```

### 9.2 REINDEX

Rebuild indexes if they become bloated or corrupted:

```bash
# Reindex an entire database (may take time on large databases)
docker exec coal_lims_db psql -U lims_user -d coal_lims -c "REINDEX DATABASE coal_lims;"

# Reindex a specific table
docker exec coal_lims_db psql -U lims_user -d coal_lims -c "REINDEX TABLE sample;"

# Check index sizes
docker exec coal_lims_db psql -U lims_user -d coal_lims -c \
  "SELECT indexrelname, pg_size_pretty(pg_relation_size(indexrelid)) AS index_size, idx_scan
   FROM pg_stat_user_indexes ORDER BY pg_relation_size(indexrelid) DESC LIMIT 15;"
```

### 9.3 Database Migration

```bash
# Check current migration state
flask db current

# Apply all pending migrations
flask db upgrade

# View migration history
flask db history --verbose

# Create a new migration after model changes
flask db migrate -m "description of changes"

# Roll back the last migration
flask db downgrade -1
```

### 9.4 Database Size Management

```bash
# Overall database size
docker exec coal_lims_db psql -U lims_user -d coal_lims -c \
  "SELECT pg_size_pretty(pg_database_size('coal_lims')) AS db_size;"

# Table sizes
docker exec coal_lims_db psql -U lims_user -d coal_lims -c \
  "SELECT relname AS table, pg_size_pretty(pg_total_relation_size(relid)) AS total_size,
          pg_size_pretty(pg_relation_size(relid)) AS data_size,
          pg_size_pretty(pg_total_relation_size(relid) - pg_relation_size(relid)) AS index_size
   FROM pg_catalog.pg_statio_user_tables ORDER BY pg_total_relation_size(relid) DESC LIMIT 15;"

# Row counts for key tables
docker exec coal_lims_db psql -U lims_user -d coal_lims -c \
  "SELECT 'sample' AS tbl, count(*) FROM sample UNION ALL
   SELECT 'analysis_result', count(*) FROM analysis_result UNION ALL
   SELECT 'audit_log', count(*) FROM audit_log UNION ALL
   SELECT 'user', count(*) FROM \"user\";"
```

### 9.5 Archiving Old Data

For very old data that is no longer needed for daily operations but must be retained for compliance:

```bash
# Export old analysis results to CSV (e.g., older than 2 years)
docker exec coal_lims_db psql -U lims_user -d coal_lims -c \
  "\COPY (SELECT * FROM analysis_result WHERE created_at < NOW() - INTERVAL '2 years') TO '/backups/archive_analysis_results.csv' WITH CSV HEADER;"

# Export old audit logs
docker exec coal_lims_db psql -U lims_user -d coal_lims -c \
  "\COPY (SELECT * FROM audit_log WHERE created_at < NOW() - INTERVAL '2 years') TO '/backups/archive_audit_log.csv' WITH CSV HEADER;"
```

**IMPORTANT:** Do not delete records that are required for ISO 17025 compliance without proper authorization and archival.

### 9.6 Recommended Maintenance Schedule

| Task | Frequency | When | Downtime Required |
|------|-----------|------|-------------------|
| `VACUUM ANALYZE` | Weekly | Sunday 03:00 | No |
| `VACUUM FULL` | Monthly | 1st Sunday 03:00 | Yes (brief) |
| `REINDEX` | Monthly | 1st Sunday 04:00 | Yes (brief) |
| Database backup | Daily | 02:00 | No |
| Migration check | After each deployment | N/A | No |
| Connection pool review | Monthly | N/A | No |
| Archive old data | Annually | End of year | No |

---

## 10. SSL Certificate Renewal

### 10.1 Let's Encrypt (Automatic)

If using Certbot with Nginx:

```bash
# Check certificate expiry
sudo certbot certificates

# Test renewal (dry run)
sudo certbot renew --dry-run

# Force renewal
sudo certbot renew

# Reload Nginx after renewal
sudo systemctl reload nginx
```

**Automatic renewal** is typically configured by Certbot via a systemd timer or cron job:

```bash
# Check if the timer exists
sudo systemctl list-timers | grep certbot

# Or verify cron entry
sudo crontab -l | grep certbot
# Expected: 0 12 * * * /usr/bin/certbot renew --quiet
```

### 10.2 Commercial SSL Certificate

```bash
# 1. Generate a new CSR (Certificate Signing Request)
sudo openssl req -new -newkey rsa:2048 -nodes \
    -keyout /etc/ssl/private/lims.key \
    -out /etc/ssl/certs/lims.csr \
    -subj "/C=MN/ST=Ulaanbaatar/O=Energy Resources/CN=lims.energyresources.mn"

# 2. Submit CSR to certificate authority and receive the signed certificate

# 3. Install the new certificate
sudo cp new-certificate.crt /etc/ssl/certs/lims.crt
sudo cp new-certificate.key /etc/ssl/private/lims.key
sudo chmod 600 /etc/ssl/private/lims.key

# 4. Test Nginx configuration
sudo nginx -t

# 5. Reload Nginx
sudo systemctl reload nginx

# 6. Verify the new certificate
echo | openssl s_client -connect lims.energyresources.mn:443 2>/dev/null | openssl x509 -noout -dates
```

### 10.3 Docker SSL Certificate

For the Docker Nginx container, SSL certificates are mounted from `./ssl/`:

```bash
# Place certificate files
cp new-certificate.crt ssl/lims.crt
cp new-certificate.key ssl/lims.key

# Restart Nginx container to pick up new certificates
docker restart coal_lims_nginx
```

### 10.4 Certificate Expiry Monitoring

Add this check to your daily monitoring:

```bash
#!/bin/bash
# /opt/scripts/check_ssl.sh
DOMAIN="lims.energyresources.mn"
DAYS_WARNING=30

EXPIRY=$(echo | openssl s_client -connect "$DOMAIN:443" -servername "$DOMAIN" 2>/dev/null | openssl x509 -noout -enddate | cut -d= -f2)
EXPIRY_EPOCH=$(date -d "$EXPIRY" +%s)
NOW_EPOCH=$(date +%s)
DAYS_LEFT=$(( (EXPIRY_EPOCH - NOW_EPOCH) / 86400 ))

if [ "$DAYS_LEFT" -lt "$DAYS_WARNING" ]; then
    echo "WARNING: SSL certificate expires in $DAYS_LEFT days ($EXPIRY)"
    # Send alert
else
    echo "OK: SSL certificate valid for $DAYS_LEFT more days"
fi
```

---

## 11. Emergency Contacts and Escalation

### 11.1 Escalation Matrix

| Level | Trigger | Who to Contact | Response Time |
|-------|---------|---------------|---------------|
| **L1** | Application slow or minor errors | On-duty analyst / IT support | Within 30 minutes |
| **L2** | Application down, data integrity issues | System administrator / DevOps | Within 15 minutes |
| **L3** | Database corruption, security breach, data loss | Lead developer + IT manager | Immediate |

### 11.2 Contact List

| Role | Name | Contact | Responsibilities |
|------|------|---------|------------------|
| System Administrator | _(fill in)_ | _(phone / email)_ | Server, Docker, Nginx, backups |
| Database Administrator | _(fill in)_ | _(phone / email)_ | PostgreSQL, migrations, data recovery |
| Lead Developer | _(fill in)_ | _(phone / email)_ | Application code, bug fixes, deployments |
| IT Infrastructure | _(fill in)_ | _(phone / email)_ | Network, DNS, SSL, firewall, email (SMTP) |
| Lab Manager | _(fill in)_ | _(phone / email)_ | Business decisions, user access approval |
| Quality Manager | _(fill in)_ | _(phone / email)_ | ISO 17025 compliance, audit trail queries |

### 11.3 Emergency Procedures

**System Completely Down:**

1. Check server/VM health (is the machine itself up?)
2. Check Docker daemon: `systemctl status docker`
3. Start all services: `docker-compose up -d`
4. If Docker is unresponsive, restart Docker: `sudo systemctl restart docker`
5. If the server is unresponsive, contact IT Infrastructure for a hard restart
6. After recovery, verify database integrity and check for data loss

**Suspected Security Breach:**

1. Immediately block the compromised account: `UPDATE "user" SET is_active = false WHERE username = 'compromised_user';`
2. Review `logs/security.log` and `logs/audit.log` for unauthorized actions
3. Change the `SECRET_KEY` in `.env` (this will invalidate all active sessions)
4. Restart the application
5. Review and rotate all passwords (database, email, API keys)
6. Contact IT Infrastructure to review firewall and network logs
7. Document the incident for ISO 17025 compliance

**Database Corruption:**

1. Stop the application immediately to prevent further damage
2. Do NOT run `VACUUM FULL` or `REINDEX` on a corrupted database
3. Take a filesystem-level backup of the PostgreSQL data directory
4. Attempt recovery: `docker exec coal_lims_db pg_resetwal /var/lib/postgresql/data/pgdata` (last resort)
5. If recovery fails, restore from the latest backup (see Section 4.4)
6. After restore, verify data integrity by spot-checking recent samples and analysis results

### 11.4 Incident Report Template

After resolving any L2 or L3 incident, document the following:

```
Incident Report
================
Date/Time:
Duration:
Severity: L1 / L2 / L3
Affected Services:
Root Cause:
Actions Taken:
Data Impact:
Users Affected:
Preventive Measures:
Reported By:
Resolved By:
```

---

## Appendix A: Environment Variable Reference

All configuration is managed via the `.env` file in the project root. See `.env.example` for the full template.

### Required Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `FLASK_ENV` | Environment mode | `production` |
| `SECRET_KEY` | Session encryption key (32+ chars) | `python -c "import secrets; print(secrets.token_urlsafe(48))"` |
| `DATABASE_URL` | Database connection string | `postgresql://lims_user:pass@localhost:5432/coal_lims` |

### Email (Office 365)

| Variable | Description | Example |
|----------|-------------|---------|
| `MAIL_SERVER` | SMTP server | `smtp.office365.com` |
| `MAIL_PORT` | SMTP port | `587` |
| `MAIL_USE_TLS` | Enable TLS | `True` |
| `MAIL_USERNAME` | Email address | `laboratory@mmc.mn` |
| `MAIL_PASSWORD` | App Password (not the regular password) | `xxxx-xxxx-xxxx-xxxx` |
| `MAIL_DEFAULT_SENDER` | From address | `laboratory@mmc.mn` |

### Security

| Variable | Default | Description |
|----------|---------|-------------|
| `SESSION_COOKIE_SECURE` | `True` (production) | Require HTTPS for cookies |
| `SESSION_COOKIE_HTTPONLY` | `True` | Block JavaScript cookie access |
| `SESSION_COOKIE_SAMESITE` | `Lax` | CSRF protection for cookies |
| `WTF_CSRF_TIME_LIMIT` | `3600` | CSRF token lifetime (seconds) |
| `LOGIN_RATE_LIMIT` | `5 per minute` | Login attempt rate limit |
| `API_RATE_LIMIT` | `30 per minute` | API request rate limit |

### Logging

| Variable | Default | Description |
|----------|---------|-------------|
| `LOG_LEVEL` | `INFO` | Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL) |
| `LOG_FILE` | `logs/app.log` | Application log path |
| `AUDIT_LOG_FILE` | `logs/audit.log` | Audit trail log path |
| `SECURITY_LOG_FILE` | `logs/security.log` | Security events log path |
| `LOG_MAX_BYTES` | `10485760` (10 MB) | Max size before rotation |
| `LOG_BACKUP_COUNT` | `10` | Number of rotated log files to keep |

### Backup

| Variable | Default | Description |
|----------|---------|-------------|
| `BACKUP_DIR` | `backups` | Backup storage directory |
| `BACKUP_RETENTION_DAYS` | `30` | Days to keep backup files |
| `BACKUP_SCHEDULE` | `0 2 * * *` | Cron schedule (daily at 02:00) |

---

## Appendix B: Docker Compose Command Reference

```bash
# Start all services
docker-compose up -d

# Start with production Nginx
docker-compose --profile production up -d

# Start with monitoring stack
docker-compose -f docker-compose.yml -f docker-compose.monitoring.yml up -d

# Start staging environment
docker-compose -f docker-compose.staging.yml up -d

# View running containers
docker-compose ps

# View logs (follow mode)
docker-compose logs -f web
docker-compose logs -f db

# Restart a single service
docker-compose restart web

# Rebuild after code changes
docker-compose build web
docker-compose up -d web

# Stop all services
docker-compose stop

# Stop and remove containers (preserves volumes)
docker-compose down

# Stop and remove everything including volumes (DESTRUCTIVE)
docker-compose down -v

# Run a one-off command in the web container
docker-compose exec web flask db upgrade
docker-compose exec web flask shell

# Scale web workers (if not using container_name)
docker-compose up -d --scale web=3
```

---

## Appendix C: Useful Database Queries

```sql
-- Recent samples registered today
SELECT id, sample_code, lab_type, created_at
FROM sample WHERE DATE(created_at) = CURRENT_DATE ORDER BY id DESC;

-- Analysis results pending approval
SELECT ar.id, ar.analysis_code, s.sample_code, ar.status, ar.created_at
FROM analysis_result ar JOIN sample s ON ar.sample_id = s.id
WHERE ar.status = 'pending' ORDER BY ar.created_at;

-- Active users who logged in today
SELECT username, role, last_login FROM "user"
WHERE DATE(last_login) = CURRENT_DATE AND is_active = true;

-- Failed login attempts (from audit log)
SELECT * FROM audit_log
WHERE action LIKE '%login_failed%' AND DATE(created_at) = CURRENT_DATE
ORDER BY created_at DESC;

-- Database connection count by state
SELECT state, count(*) FROM pg_stat_activity
WHERE datname = 'coal_lims' GROUP BY state;

-- Table row counts
SELECT schemaname, relname, n_live_tup AS row_count
FROM pg_stat_user_tables ORDER BY n_live_tup DESC;

-- Index usage statistics
SELECT relname, indexrelname, idx_scan, idx_tup_read, idx_tup_fetch
FROM pg_stat_user_indexes ORDER BY idx_scan DESC LIMIT 20;
```
