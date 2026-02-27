#!/bin/bash
# Coal LIMS - Automatic Database Backup
# Crontab: 0 2 * * * /opt/coal_lims/backup.sh >> /opt/coal_lims/logs/backup.log 2>&1

set -e

BACKUP_DIR="/opt/coal_lims/backups"
DATE=$(date +%Y%m%d_%H%M%S)
FILENAME="coal_lims_backup_${DATE}.sql.gz"

mkdir -p "${BACKUP_DIR}"

echo "[$(date)] Starting backup..."

# Backup хийх
docker compose -f /opt/coal_lims/docker-compose.yml exec -T db \
  pg_dump -U lims_user coal_lims | gzip > "${BACKUP_DIR}/${FILENAME}"

# Файлын хэмжээ шалгах
SIZE=$(du -h "${BACKUP_DIR}/${FILENAME}" | cut -f1)
echo "[$(date)] Backup done: ${FILENAME} (${SIZE})"

# 30 хоногоос хуучин backup устгах
DELETED=$(find ${BACKUP_DIR} -name "*.sql.gz" -mtime +30 -delete -print | wc -l)
if [ "$DELETED" -gt 0 ]; then
    echo "[$(date)] Deleted ${DELETED} old backup(s)"
fi
