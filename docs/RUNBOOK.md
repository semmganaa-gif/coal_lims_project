# LIMS - Operations Runbook

> **Тэмдэглэл:** Энэ runbook дахь `coal_lims` нэрс (container, database) нь production infra нэрс бөгөөд хэвээр ашиглагдана. Систем нь 4 лаб (Coal, Water, Microbiology, Petrography) дэмжинэ.

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
