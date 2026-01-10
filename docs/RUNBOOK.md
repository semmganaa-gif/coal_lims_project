# Coal LIMS - Operations Runbook

## Quick Reference

| Service | Port | Health Check | Logs |
|---------|------|--------------|------|
| Flask App | 5000 | /health | /app/logs/ |
| PostgreSQL | 5432 | pg_isready | docker logs |
| Redis | 6379 | redis-cli ping | docker logs |
| Nginx | 80/443 | curl localhost | /var/log/nginx/ |

---

## 1. Application Issues

### 1.1 Application Not Responding

**Symptoms:**
- 502/504 Gateway errors
- Health check failing
- No response from /health

**Diagnosis:**
```bash
# Check container status
docker ps -a | grep coal_lims

# Check application logs
docker logs coal_lims_web --tail 100

# Check health endpoint
curl -v http://localhost:5000/health

# Check resource usage
docker stats coal_lims_web
```

**Resolution:**
```bash
# Restart application
docker-compose restart web

# If container keeps crashing, rebuild
docker-compose up -d --build web

# Check for port conflicts
netstat -tlnp | grep 5000
```

### 1.2 High Response Time

**Symptoms:**
- P95 response time > 2s
- Slow page loads
- Timeout errors

**Diagnosis:**
```bash
# Check slow query log
docker exec coal_lims_db psql -U lims_user -d coal_lims -c \
  "SELECT query, calls, mean_time FROM pg_stat_statements ORDER BY mean_time DESC LIMIT 10;"

# Check application performance
curl -w "@curl-format.txt" http://localhost:5000/samples

# Check Redis latency
docker exec coal_lims_redis redis-cli --latency

# Check system resources
docker stats
```

**Resolution:**
```bash
# Clear Redis cache
docker exec coal_lims_redis redis-cli FLUSHDB

# Analyze slow queries
docker exec coal_lims_db psql -U lims_user -d coal_lims -c "ANALYZE;"

# Increase workers (temporary)
docker-compose exec web pkill -HUP gunicorn
```

### 1.3 Memory Issues

**Symptoms:**
- OOM kills
- Container restarts
- Memory usage > 500MB

**Diagnosis:**
```bash
# Check memory usage
docker stats --no-stream coal_lims_web

# Check for memory leaks
docker exec coal_lims_web python -c "import tracemalloc; tracemalloc.start()"

# Check gunicorn workers
docker exec coal_lims_web ps aux | grep gunicorn
```

**Resolution:**
```bash
# Restart workers
docker-compose exec web pkill -HUP gunicorn

# Reduce workers
# Edit docker-compose.yml: --workers 2

# Add memory limit
# Edit docker-compose.yml: mem_limit: 512m
```

---

## 2. Database Issues

### 2.1 Database Connection Failed

**Symptoms:**
- "Connection refused" errors
- Application startup failure
- Health check shows "database: disconnected"

**Diagnosis:**
```bash
# Check PostgreSQL status
docker exec coal_lims_db pg_isready

# Check connections
docker exec coal_lims_db psql -U lims_user -d coal_lims -c \
  "SELECT count(*) FROM pg_stat_activity;"

# Check logs
docker logs coal_lims_db --tail 50
```

**Resolution:**
```bash
# Restart PostgreSQL
docker-compose restart db

# Check max connections
docker exec coal_lims_db psql -U lims_user -d coal_lims -c "SHOW max_connections;"

# Kill idle connections
docker exec coal_lims_db psql -U lims_user -d coal_lims -c \
  "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE state = 'idle' AND query_start < now() - interval '1 hour';"
```

### 2.2 Database Slow Queries

**Symptoms:**
- Queries taking > 1s
- High CPU on database container
- Lock wait timeouts

**Diagnosis:**
```bash
# Find slow queries
docker exec coal_lims_db psql -U lims_user -d coal_lims -c \
  "SELECT pid, now() - pg_stat_activity.query_start AS duration, query
   FROM pg_stat_activity
   WHERE state = 'active' AND now() - pg_stat_activity.query_start > interval '5 seconds';"

# Check locks
docker exec coal_lims_db psql -U lims_user -d coal_lims -c \
  "SELECT blocked_locks.pid AS blocked_pid, blocking_locks.pid AS blocking_pid
   FROM pg_locks blocked_locks
   JOIN pg_locks blocking_locks ON blocking_locks.locktype = blocked_locks.locktype;"

# Check table bloat
docker exec coal_lims_db psql -U lims_user -d coal_lims -c \
  "SELECT relname, n_dead_tup FROM pg_stat_user_tables ORDER BY n_dead_tup DESC LIMIT 10;"
```

**Resolution:**
```bash
# Kill long-running query
docker exec coal_lims_db psql -U lims_user -d coal_lims -c \
  "SELECT pg_cancel_backend(PID);"

# Vacuum tables
docker exec coal_lims_db psql -U lims_user -d coal_lims -c "VACUUM ANALYZE;"

# Reindex
docker exec coal_lims_db psql -U lims_user -d coal_lims -c \
  "REINDEX DATABASE coal_lims;"
```

### 2.3 Database Disk Full

**Symptoms:**
- Write errors
- "No space left on device"
- Database crash

**Diagnosis:**
```bash
# Check disk usage
docker exec coal_lims_db df -h

# Check database size
docker exec coal_lims_db psql -U lims_user -d coal_lims -c \
  "SELECT pg_size_pretty(pg_database_size('coal_lims'));"

# Check table sizes
docker exec coal_lims_db psql -U lims_user -d coal_lims -c \
  "SELECT relname, pg_size_pretty(pg_total_relation_size(relid))
   FROM pg_catalog.pg_statio_user_tables ORDER BY pg_total_relation_size(relid) DESC LIMIT 10;"
```

**Resolution:**
```bash
# Remove old WAL files
docker exec coal_lims_db pg_archivecleanup /var/lib/postgresql/data/pg_wal 0000000100000000000000XX

# Vacuum full (requires downtime)
docker exec coal_lims_db psql -U lims_user -d coal_lims -c "VACUUM FULL;"

# Truncate audit logs (if safe)
docker exec coal_lims_db psql -U lims_user -d coal_lims -c \
  "DELETE FROM analysis_result_log WHERE timestamp < now() - interval '1 year';"
```

---

## 3. Redis Issues

### 3.1 Redis Connection Failed

**Symptoms:**
- Rate limiting errors
- Session issues
- Cache miss rate high

**Diagnosis:**
```bash
# Check Redis status
docker exec coal_lims_redis redis-cli ping

# Check memory
docker exec coal_lims_redis redis-cli info memory

# Check connections
docker exec coal_lims_redis redis-cli client list
```

**Resolution:**
```bash
# Restart Redis
docker-compose restart redis

# Flush if corrupted
docker exec coal_lims_redis redis-cli FLUSHALL

# Check maxmemory policy
docker exec coal_lims_redis redis-cli config get maxmemory-policy
```

---

## 4. Authentication Issues

### 4.1 User Cannot Login

**Symptoms:**
- "Invalid credentials" message
- Session not created
- Redirect loop

**Diagnosis:**
```bash
# Check user exists
docker exec coal_lims_db psql -U lims_user -d coal_lims -c \
  "SELECT id, username, role, is_active FROM \"user\" WHERE username = 'USERNAME';"

# Check failed login attempts
docker logs coal_lims_web | grep "Failed login"

# Check rate limiting
docker exec coal_lims_redis redis-cli keys "LIMITER:*"
```

**Resolution:**
```bash
# Reset password via CLI
docker exec coal_lims_web flask users create USERNAME NewPass123! ROLE

# Clear rate limit
docker exec coal_lims_redis redis-cli del "LIMITER:USERNAME"

# Unlock account
docker exec coal_lims_db psql -U lims_user -d coal_lims -c \
  "UPDATE \"user\" SET is_active = true WHERE username = 'USERNAME';"
```

### 4.2 License Issues

**Symptoms:**
- "License expired" message
- Redirect to license activation
- Feature restrictions

**Diagnosis:**
```bash
# Check license status
curl http://localhost:5000/license/info

# Check license file
docker exec coal_lims_web cat /app/instance/license.json

# Check hardware fingerprint
docker exec coal_lims_web python -c "from app.utils.hardware_fingerprint import get_fingerprint; print(get_fingerprint())"
```

**Resolution:**
- Contact license administrator for new license key
- Verify hardware fingerprint matches license

---

## 5. Backup & Recovery

### 5.1 Create Backup

```bash
# Database backup
docker exec coal_lims_db pg_dump -U lims_user coal_lims > backup_$(date +%Y%m%d).sql

# Compressed backup
docker exec coal_lims_db pg_dump -U lims_user -Fc coal_lims > backup_$(date +%Y%m%d).dump

# Full backup with uploads
tar -czvf lims_full_backup_$(date +%Y%m%d).tar.gz \
  backup_$(date +%Y%m%d).sql \
  ./instance/ \
  ./app/static/uploads/
```

### 5.2 Restore Backup

```bash
# Stop application
docker-compose stop web

# Restore database
docker exec -i coal_lims_db psql -U lims_user -d coal_lims < backup.sql

# Or from compressed
docker exec -i coal_lims_db pg_restore -U lims_user -d coal_lims backup.dump

# Restart
docker-compose up -d web
```

---

## 6. Monitoring Alerts

### 6.1 Alert Response Matrix

| Alert | Severity | Response Time | Action |
|-------|----------|---------------|--------|
| LIMSDown | Critical | 5 min | Restart app, check logs |
| HighErrorRate | Critical | 15 min | Check logs, rollback if deploy |
| SlowResponseTime | Warning | 30 min | Check DB, clear cache |
| HighMemoryUsage | Warning | 30 min | Restart workers |
| QCFailureSpike | Warning | 1 hour | Notify lab manager |
| DatabaseDiskFull | Critical | 10 min | Clean logs, expand disk |

### 6.2 Escalation Path

1. **L1 (On-call)**: Basic restarts, cache clear
2. **L2 (DevOps)**: Database issues, deployment
3. **L3 (Developer)**: Code bugs, complex issues
4. **Management**: Business decisions, extended downtime

---

## 7. Deployment

### 7.1 Production Deploy

```bash
# Pull latest code
git pull origin main

# Build new image
docker-compose build web

# Run migrations
docker-compose exec web flask db upgrade

# Deploy with zero downtime
docker-compose up -d --no-deps web

# Verify health
curl http://localhost:5000/health

# Check logs
docker logs coal_lims_web --tail 50
```

### 7.2 Rollback

```bash
# Find previous image
docker images | grep coal_lims

# Rollback to previous
docker tag coal_lims_web:previous coal_lims_web:latest
docker-compose up -d --no-deps web

# Or git rollback
git revert HEAD
docker-compose up -d --build web
```

---

## 8. Emergency Contacts

| Role | Name | Phone | Email |
|------|------|-------|-------|
| On-call DevOps | TBD | +976-XXX | devops@example.com |
| Lead Developer | TBD | +976-XXX | dev@example.com |
| Lab Manager | TBD | +976-XXX | lab@example.com |
| IT Manager | TBD | +976-XXX | it@example.com |

---

## 9. Useful Commands Cheatsheet

```bash
# Logs
docker logs coal_lims_web --tail 100 -f
docker logs coal_lims_db --tail 100 -f

# Shell access
docker exec -it coal_lims_web /bin/bash
docker exec -it coal_lims_db psql -U lims_user coal_lims

# Resource check
docker stats --no-stream

# Restart all
docker-compose restart

# Full rebuild
docker-compose down && docker-compose up -d --build

# Check config
docker-compose config
```
