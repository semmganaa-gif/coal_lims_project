# 🚀 LIMS - Production Deployment Guide

LIMS - Laboratory Information Management System

> **Тэмдэглэл:** Deployment тохиргоонд `coal_lims` нэрс (database, Docker container, service) хэвээр ашиглагдана. Энэ нь production infra-тай нийцтэй байх зорилготой. Систем нь 4 лабораторийн модулийг (Coal, Water, Microbiology, Petrography) дэмжинэ.

---

## 📋 Агуулга

1. [Систем шаардлага](#систем-шаардлага)
2. [Өгөгдлийн сангийн тохиргоо](#өгөгдлийн-сангийн-тохиргоо)
3. [Application суулгах](#application-суулгах)
4. [Environment Variables](#environment-variables)
5. [HTTPS тохиргоо](#https-тохиргоо)
6. [Gunicorn тохиргоо](#gunicorn-тохиргоо) (Linux)
7. [Nginx тохиргоо](#nginx-тохиргоо) (Linux)
8. [Systemd service](#systemd-service) (Linux)
9. [Windows Server тохиргоо](#windows-server-тохиргоо) ⭐
10. [Backup стратеги](#backup-стратеги)
11. [Monitoring](#monitoring)
12. [Troubleshooting](#troubleshooting)

---

## 🖥️ Систем шаардлага

### Hardware
- **CPU:** 2+ cores
- **RAM:** 4GB+ (8GB recommended)
- **Storage:** 50GB+ SSD
- **Network:** 100Mbps+

### Software
- **OS:** Ubuntu 20.04+ / CentOS 8+ / Windows Server 2019+
- **Python:** 3.11+
- **Database:** PostgreSQL 14+ (Production) / SQLite (Development)
- **Web Server:** Nginx 1.18+
- **WSGI:** Gunicorn (Linux) / Waitress (Windows)

---

## 🗄️ Өгөгдлийн сангийн тохиргоо

### PostgreSQL (Production - Recommended)

#### 1. PostgreSQL суулгах

**Ubuntu/Debian:**
```bash
sudo apt update
sudo apt install postgresql postgresql-contrib
sudo systemctl start postgresql
sudo systemctl enable postgresql
```

**CentOS/RHEL:**
```bash
sudo dnf install postgresql-server postgresql-contrib
sudo postgresql-setup --initdb
sudo systemctl start postgresql
sudo systemctl enable postgresql
```

#### 2. Database үүсгэх

```bash
sudo -u postgres psql

# PostgreSQL shell дотор:
CREATE DATABASE coal_lims;
CREATE USER lims_user WITH PASSWORD 'your-strong-password';
GRANT ALL PRIVILEGES ON DATABASE coal_lims TO lims_user;
ALTER DATABASE coal_lims OWNER TO lims_user;
\q
```

#### 3. PostgreSQL тохиргоо

`/etc/postgresql/14/main/pg_hba.conf`:
```conf
# IPv4 local connections:
host    coal_lims    lims_user    127.0.0.1/32    md5
```

```bash
sudo systemctl restart postgresql
```

### SQLite (Development only)

SQLite автоматаар `instance/lims.db` үүсгэнэ. Production-д бүү ашигла!

---

## 📦 Application суулгах

### 1. Code татах

```bash
cd /var/www
git clone https://github.com/your-org/coal_lims_project.git
cd coal_lims_project
```

### 2. Virtual environment үүсгэх

```bash
python3.11 -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate   # Windows
```

### 3. Dependencies суулгах

```bash
pip install --upgrade pip
pip install -r requirements.txt
pip install gunicorn psycopg2-binary  # Production dependencies
```

### 4. Environment файл үүсгэх

`.env` файл үүсгэх:
```bash
# Production Configuration
FLASK_ENV=production
SECRET_KEY=your-very-long-random-secret-key-here-use-secrets.token-urlsafe-48

# Database
DATABASE_URL=postgresql://lims_user:your-strong-password@localhost:5432/coal_lims

# Security
SESSION_COOKIE_SECURE=True
WTF_CSRF_ENABLED=True

# Timezone
TZ=Asia/Ulaanbaatar
```

**⚠️ ЧУХАЛ:** `.env` файлыг git-д оруулахгүй! `.gitignore`-д нэмэх:
```bash
echo ".env" >> .gitignore
```

### 5. Database migration

```bash
flask db upgrade
```

### 6. Анхны админ үүсгэх

```bash
flask users create admin your-password admin
```

---

## 🔐 Environment Variables

### Шаардлагатай

| Variable | Тайлбар | Жишээ |
|----------|---------|-------|
| `FLASK_ENV` | Орчин | `production` |
| `SECRET_KEY` | Session шифрлэх түлхүүр | `secrets.token_urlsafe(48)` |
| `DATABASE_URL` | DB холболт | `postgresql://user:pass@host/db` |

### Email тохиргоо (Office 365)

| Variable | Тайлбар | Жишээ |
|----------|---------|-------|
| `MAIL_SERVER` | SMTP сервер | `smtp.office365.com` |
| `MAIL_PORT` | Port | `587` |
| `MAIL_USE_TLS` | TLS ашиглах | `True` |
| `MAIL_USERNAME` | Имэйл хаяг | `laboratory@mmc.mn` |
| `MAIL_PASSWORD` | App Password | `xxxx-xxxx-xxxx-xxxx` |
| `MAIL_DEFAULT_SENDER` | Илгээгч | `laboratory@mmc.mn` |

**⚠️ App Password авах:**
1. https://mysignins.microsoft.com/security-info
2. "Add sign-in method" → "App password"
3. Үүссэн нууц үгийг `MAIL_PASSWORD`-д ашиглах

**IT-д хэлэх:** SMTP AUTH идэвхжүүлсэн эсэхийг шалгах (Exchange Admin → Mailboxes → Authenticated SMTP ✓)

### Сонголттой

| Variable | Тайлбар | Default |
|----------|---------|---------|
| `TZ` | Цагийн бүс | `Asia/Ulaanbaatar` |
| `SESSION_COOKIE_SECURE` | HTTPS шаардлага | `True` (production) |

### SECRET_KEY үүсгэх

```bash
python3 -c "import secrets; print(secrets.token_urlsafe(48))"
```

---

## 🔒 HTTPS тохиргоо

### SSL Certificate авах

#### Option 1: Let's Encrypt (Үнэгүй)

```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d lims.energyresources.mn
```

#### Option 2: Commercial SSL

```bash
# Certificate файлуудыг хуулах
sudo cp your-cert.crt /etc/ssl/certs/lims.crt
sudo cp your-key.key /etc/ssl/private/lims.key
sudo chmod 600 /etc/ssl/private/lims.key
```

---

## 🦄 Gunicorn тохиргоо

### gunicorn_config.py үүсгэх

```python
# gunicorn_config.py
import multiprocessing

bind = "127.0.0.1:8000"
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = "sync"
worker_connections = 1000
timeout = 120
keepalive = 5

# Logging
accesslog = "/var/log/coal_lims/access.log"
errorlog = "/var/log/coal_lims/error.log"
loglevel = "info"

# Process naming
proc_name = "coal_lims"

# Server mechanics
daemon = False
pidfile = "/var/run/coal_lims.pid"
```

### Log folder үүсгэх

```bash
sudo mkdir -p /var/log/coal_lims
sudo chown www-data:www-data /var/log/coal_lims
```

### Gunicorn ажиллуулах

```bash
source venv/bin/activate
gunicorn -c gunicorn_config.py "app:create_app()"
```

---

## 🌐 Nginx тохиргоо

### /etc/nginx/sites-available/coal_lims

```nginx
upstream coal_lims {
    server 127.0.0.1:8000 fail_timeout=0;
}

server {
    listen 80;
    server_name lims.energyresources.mn;

    # Redirect HTTP to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name lims.energyresources.mn;

    # SSL Configuration
    ssl_certificate /etc/ssl/certs/lims.crt;
    ssl_certificate_key /etc/ssl/private/lims.key;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;

    # Security Headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;

    # Root directory
    root /var/www/coal_lims_project;

    # Max upload size
    client_max_body_size 20M;

    # Gzip compression
    gzip on;
    gzip_types text/plain text/css application/json application/javascript text/xml application/xml;

    # Static files
    location /static {
        alias /var/www/coal_lims_project/app/static;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    # Proxy to Gunicorn
    location / {
        proxy_pass http://coal_lims;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_redirect off;

        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    # Access & Error logs
    access_log /var/log/nginx/coal_lims_access.log;
    error_log /var/log/nginx/coal_lims_error.log;
}
```

### Nginx идэвхжүүлэх

```bash
sudo ln -s /etc/nginx/sites-available/coal_lims /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

---

## ⚙️ Systemd Service

### /etc/systemd/system/coal_lims.service

```ini
[Unit]
Description=LIMS Gunicorn Service
After=network.target postgresql.service

[Service]
Type=notify
User=www-data
Group=www-data
WorkingDirectory=/var/www/coal_lims_project
Environment="PATH=/var/www/coal_lims_project/venv/bin"
EnvironmentFile=/var/www/coal_lims_project/.env
ExecStart=/var/www/coal_lims_project/venv/bin/gunicorn -c gunicorn_config.py "app:create_app()"
ExecReload=/bin/kill -s HUP $MAINPID
KillMode=mixed
TimeoutStopSec=5
PrivateTmp=true
Restart=on-failure
RestartSec=5s

[Install]
WantedBy=multi-user.target
```

### Service идэвхжүүлэх

```bash
sudo systemctl daemon-reload
sudo systemctl start coal_lims
sudo systemctl enable coal_lims
sudo systemctl status coal_lims
```

### Service командууд

```bash
# Эхлүүлэх
sudo systemctl start coal_lims

# Зогсоох
sudo systemctl stop coal_lims

# Дахин эхлүүлэх
sudo systemctl restart coal_lims

# Статус шалгах
sudo systemctl status coal_lims

# Logs харах
sudo journalctl -u coal_lims -f
```

---

## 🪟 Windows Server тохиргоо

### 1. Python суулгах

1. https://python.org/downloads/ - Python 3.11+ татах
2. "Add Python to PATH" сонгох
3. Суулгах

### 2. PostgreSQL суулгах

1. https://postgresql.org/download/windows/
2. Суулгах, `postgres` нууц үг тохируулах
3. pgAdmin-ээр `coal_lims` database үүсгэх

### 3. Application суулгах

```powershell
# Folder үүсгэх
mkdir C:\Apps\coal_lims
cd C:\Apps\coal_lims

# Code хуулах (git эсвэл zip)
git clone https://github.com/your-org/coal_lims_project.git .

# Virtual environment
python -m venv venv
.\venv\Scripts\activate

# Dependencies
pip install -r requirements.txt
pip install waitress  # Windows WSGI server
```

### 4. .env файл үүсгэх

```powershell
# C:\Apps\coal_lims\.env
FLASK_ENV=production
SECRET_KEY=your-secret-key-here
DATABASE_URL=postgresql://postgres:your_password@localhost:5432/coal_lims

# Email (Office 365)
MAIL_SERVER=smtp.office365.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=laboratory@mmc.mn
MAIL_PASSWORD=your-app-password
MAIL_DEFAULT_SENDER=laboratory@mmc.mn
```

### 5. Database migration

```powershell
.\venv\Scripts\activate
flask db upgrade
flask users create admin your-password admin
```

### 6. Waitress ашиглан ажиллуулах

**run_production.py:**
```python
from waitress import serve
from app import create_app

app = create_app()

if __name__ == '__main__':
    print("Starting LIMS on http://0.0.0.0:8000")
    serve(app, host='0.0.0.0', port=8000, threads=4)
```

**Ажиллуулах:**
```powershell
.\venv\Scripts\python.exe run_production.py
```

### 7. Windows Service болгох (NSSM)

1. https://nssm.cc/download - NSSM татах
2. `nssm.exe` файлыг `C:\Windows\System32` руу хуулах

```powershell
# Service үүсгэх
nssm install CoalLIMS "C:\Apps\coal_lims\venv\Scripts\python.exe" "C:\Apps\coal_lims\run_production.py"

# Startup directory тохируулах
nssm set CoalLIMS AppDirectory "C:\Apps\coal_lims"

# Auto start тохируулах
nssm set CoalLIMS Start SERVICE_AUTO_START

# Service эхлүүлэх
nssm start CoalLIMS
```

### 8. Windows Firewall

```powershell
# Port 8000 нээх (хэрэв Nginx ашиглахгүй бол)
netsh advfirewall firewall add rule name="LIMS" dir=in action=allow protocol=TCP localport=8000

# Эсвэл 80, 443 (Nginx ашиглавал)
netsh advfirewall firewall add rule name="HTTP" dir=in action=allow protocol=TCP localport=80
netsh advfirewall firewall add rule name="HTTPS" dir=in action=allow protocol=TCP localport=443
```

### 9. IIS Reverse Proxy (Сонголттой)

IIS-ийг reverse proxy болгон ашиглаж болно:
1. URL Rewrite Module суулгах
2. Application Request Routing (ARR) суулгах
3. `web.config` файл үүсгэх

```xml
<?xml version="1.0" encoding="UTF-8"?>
<configuration>
    <system.webServer>
        <rewrite>
            <rules>
                <rule name="ReverseProxy" stopProcessing="true">
                    <match url="(.*)" />
                    <action type="Rewrite" url="http://localhost:8000/{R:1}" />
                </rule>
            </rules>
        </rewrite>
    </system.webServer>
</configuration>
```

### 10. Windows Task Scheduler (Backup)

1. Task Scheduler нээх
2. "Create Basic Task" → "Daily" → 02:00
3. Action: `C:\Apps\coal_lims\scripts\backup.bat`

**backup.bat:**
```batch
@echo off
set BACKUP_DIR=C:\Backups\coal_lims
set DATE=%date:~0,4%%date:~5,2%%date:~8,2%

mkdir %BACKUP_DIR% 2>nul

"C:\Program Files\PostgreSQL\14\bin\pg_dump.exe" -U postgres -d coal_lims > %BACKUP_DIR%\lims_%DATE%.sql

:: 30 хоногоос хуучин файлууд устгах
forfiles /p %BACKUP_DIR% /s /m *.sql /d -30 /c "cmd /c del @path"
```

---

## 💾 Backup стратеги

### Database Backup

```bash
#!/bin/bash
# /opt/scripts/backup_lims.sh

BACKUP_DIR="/var/backups/coal_lims"
DATE=$(date +%Y%m%d_%H%M%S)
FILENAME="lims_backup_${DATE}.sql.gz"

# Folder үүсгэх
mkdir -p $BACKUP_DIR

# Backup хийх
pg_dump -U lims_user coal_lims | gzip > $BACKUP_DIR/$FILENAME

# 30 хоногоос хуучин файлууд устгах
find $BACKUP_DIR -name "lims_backup_*.sql.gz" -mtime +30 -delete

echo "Backup амжилттай: $FILENAME"
```

### Cron job нэмэх

```bash
sudo crontab -e

# Өдөр бүр 2:00 цагт
0 2 * * * /opt/scripts/backup_lims.sh >> /var/log/backup_lims.log 2>&1
```

### Файлын backup

```bash
# Application код
tar -czf /var/backups/coal_lims_app_$(date +%Y%m%d).tar.gz \
    /var/www/coal_lims_project \
    --exclude='venv' \
    --exclude='*.pyc' \
    --exclude='__pycache__'

# Instance folder (SQLite, uploads)
tar -czf /var/backups/coal_lims_instance_$(date +%Y%m%d).tar.gz \
    /var/www/coal_lims_project/instance
```

---

## 📊 Monitoring

### Log rotation

`/etc/logrotate.d/coal_lims`:
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

### Health check script

```bash
#!/bin/bash
# /opt/scripts/health_check.sh

URL="https://lims.energyresources.mn/login"
STATUS=$(curl -s -o /dev/null -w "%{http_code}" $URL)

if [ $STATUS -eq 200 ]; then
    echo "✅ LIMS is UP"
    exit 0
else
    echo "❌ LIMS is DOWN (HTTP $STATUS)"
    # Send alert email
    echo "LIMS down!" | mail -s "ALERT: LIMS Down" admin@energyresources.mn
    exit 1
fi
```

Cron:
```bash
*/5 * * * * /opt/scripts/health_check.sh
```

---

## 🔧 Troubleshooting

### Application ажиллахгүй байна

```bash
# Logs шалгах
sudo journalctl -u coal_lims -n 100 --no-pager

# Permission шалгах
ls -la /var/www/coal_lims_project
sudo chown -R www-data:www-data /var/www/coal_lims_project

# Database холболт шалгах
psql -U lims_user -h localhost -d coal_lims

# Port ашиглагдаж байгаа эсэх
sudo netstat -tlnp | grep 8000
```

### Database migration алдаа

```bash
# Current version шалгах
flask db current

# History харах
flask db history

# Rollback хийх
flask db downgrade -1

# Upgrade дахин оролдох
flask db upgrade
```

### Performance асуудал

```bash
# Database queries шалгах
tail -f /var/log/coal_lims/error.log | grep "SELECT"

# Gunicorn workers шалгах
ps aux | grep gunicorn

# Memory ашиглалт
free -h
top -p $(pgrep -d',' gunicorn)
```

### HTTPS алдаа

```bash
# Certificate шалгах
sudo certbot certificates

# SSL renew
sudo certbot renew --dry-run

# Nginx тохиргоо шалгах
sudo nginx -t
```

---

## 📝 Maintenance

### Code шинэчлэх

```bash
cd /var/www/coal_lims_project
git pull origin main
source venv/bin/activate
pip install -r requirements.txt
flask db upgrade
sudo systemctl restart coal_lims
```

### Dependencies шинэчлэх

```bash
pip list --outdated
pip install --upgrade package-name
pip freeze > requirements.txt
```

---

## ✅ Production Checklist

### Үндсэн тохиргоо
- [ ] PostgreSQL суулгасан, бүрэн тохируулсан
- [ ] SECRET_KEY үүсгэсэн, аюулгүй хадгалсан
- [ ] `FLASK_ENV=production` тохируулсан
- [ ] `.env` файл үүсгэсэн (git-д оруулаагүй)
- [ ] `flask db upgrade` амжилттай
- [ ] Админ хэрэглэгч үүсгэсэн

### Email тохиргоо (Office 365)
- [ ] MAIL_SERVER, MAIL_PORT тохируулсан
- [ ] App Password авсан (MFA идэвхтэй бол)
- [ ] SMTP AUTH идэвхжүүлсэн (IT-тай шалгасан)
- [ ] Тест имэйл илгээж туршсан
- [ ] TO/CC хаягууд тохируулсан (Тохиргоо → Тайлангийн имэйл)

### Linux Server
- [ ] SSL certificate суулгасан
- [ ] Nginx тохируулсан, идэвхжүүлсэн
- [ ] Gunicorn тохируулсан
- [ ] Systemd service үүсгэсэн
- [ ] Firewall тохируулсан (80, 443 port)
- [ ] Cron backup job нэмсэн
- [ ] Log rotation тохируулсан

### Windows Server
- [ ] Python 3.11+ суулгасан (PATH-д нэмсэн)
- [ ] PostgreSQL суулгасан
- [ ] Waitress суулгасан
- [ ] NSSM service үүсгэсэн (auto-start)
- [ ] Windows Firewall port нээсэн
- [ ] Task Scheduler backup тохируулсан
- [ ] IIS reverse proxy (сонголттой)

### Эцсийн шалгалт
- [ ] Health check endpoint ажиллаж байна (`/health`)
- [ ] Системийг бүрэн турших
- [ ] Documentation бэлтгэсэн
- [ ] Backup restore турших

---

**Амжилт хүсье! 🚀**


