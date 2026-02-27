# Coal LIMS - Production Server Байршуулах Заавар

**Хэнд зориулсан:** IT мэдлэггүй хүн шууд дагаж хийх боломжтой.
**Хугацаа:** ~1-2 цаг (серверийн бэлдэлтээс хамаарна)

---

## 0-р алхам: Юу хэрэгтэй вэ?

Эхлэхийн өмнө дараах зүйлс бэлэн байх ёстой:

| Зүйл | Тайлбар |
|-------|---------|
| **Сервер** | Ubuntu 22.04 (эсвэл Windows Server). RAM 4GB+, HDD 50GB+ |
| **Домэйн** (заавал биш) | Жишээ: `lims.mmc.mn` — HTTPS ашиглахад хэрэгтэй |
| **SSH нэвтрэх** | Серверт терминалаар холбогдох боломж (PuTTY эсвэл Terminal) |
| **Имэйл нууц үг** | `gantulga.u@mmc.mn` Office365 App Password |

---

## 1-р алхам: Серверт холбогдох

### Windows-оос PuTTY ашиглах:
1. PuTTY програм татах: https://www.putty.org/
2. Нээгээд `Host Name` хэсэгт серверийн IP хаяг бичнэ (жишээ: `192.168.1.100`)
3. `Open` дарна
4. Нэвтрэх нэр, нууц үг оруулна

### Mac/Linux-оос:
```bash
ssh username@192.168.1.100
```

---

## 2-р алхам: Docker суулгах

Docker бол програмуудыг "хайрцаг" дотор ажиллуулдаг программ хангамж. Манай LIMS систем Docker ашиглан ажиллана.

Доорх командуудыг **нэг нэгээр нь** хуулж серверт paste хийнэ:

```bash
# 1. Системийг шинэчлэх
sudo apt update && sudo apt upgrade -y

# 2. Docker суулгах
sudo apt install -y docker.io docker-compose-plugin

# 3. Docker-г автоматаар асдаг болгох
sudo systemctl enable docker
sudo systemctl start docker

# 4. Өөрийн хэрэглэгчийг Docker бүлэгт нэмэх (sudo шаардлагагүй болно)
sudo usermod -aG docker $USER

# 5. Гарч дахин нэвтрэх (бүлгийн өөрчлөлт хүчин төгөлдөр болно)
exit
```

Дахин SSH-ээр нэвтрэнэ. Дараа нь:
```bash
# Docker ажиллаж байгаа эсэхийг шалгах
docker --version
docker compose version
```

Хоёулангаас хувилбарын дугаар гарч ирвэл зөв.

---

## 3-р алхам: Кодыг серверт авчрах

```bash
# 1. Хавтас үүсгэх
sudo mkdir -p /opt/coal_lims
sudo chown $USER:$USER /opt/coal_lims
cd /opt/coal_lims

# 2. GitHub-аас кодыг татах
git clone https://github.com/semmganaa-gif/coal_lims_project.git .
```

Хэрэв `git` суулгаагүй бол:
```bash
sudo apt install -y git
```

---

## 4-р алхам: .env файл тохируулах (ХАМГИЙН ЧУХАЛ!)

`.env` файл бол системийн бүх нууц тохиргоог агуулсан файл. Энэ файлыг **ЗААВАЛ** зөв тохируулах ёстой.

### 4.1. Нууц түлхүүр (SECRET_KEY) үүсгэх

Энэ команд нууц түлхүүр үүсгэнэ. Гарч ирсэн урт текстийг хуулж авна:

```bash
python3 -c "import secrets; print(secrets.token_urlsafe(48))"
```

Жишээ гаралт: `Abc123xYz456...` (маш урт текст гарна, тэр бүгдийг хуулна)

### 4.2. DB нууц үг бэлдэх

```bash
python3 -c "import secrets; print(secrets.token_urlsafe(24))"
```

Гарч ирсэн текстийг бас хуулж авна.

### 4.3. .env файл үүсгэх

```bash
nano /opt/coal_lims/.env
```

`nano` нээгдэнэ. Доорх текстийг **бүхэлд нь** хуулж paste хийнэ.
**ХААЛТТАЙ ХЭСГҮҮДИЙГ ӨӨРИЙНХӨӨРӨӨ СОЛИНО:**

```env
# ============================================================================
# COAL LIMS - PRODUCTION CONFIGURATION
# ============================================================================

# -------------------- APPLICATION --------------------
FLASK_ENV=production
DEBUG=False
FLASK_DEBUG=0

# ЭНД 4.1-д ҮҮСГЭСЭН УРТТАЙ ТЕКСТИЙГ ТАВИНА:
SECRET_KEY=ЭНД_4.1_АЛХАМЫН_ТЕКСТИЙГ_БУУЛГАНА

# -------------------- DATABASE --------------------
# ЭНД 4.2-д ҮҮСГЭСЭН НУУЦ ҮГИЙГ lims_password ГЭСНИЙ ОРОНД ТАВИНА:
DB_PASSWORD=ЭНД_4.2_АЛХАМЫН_ТЕКСТИЙГ_БУУЛГАНА

# Docker дотоод холболт (өөрчлөх шаардлагагүй)
DATABASE_URL=postgresql://lims_user:${DB_PASSWORD}@db:5432/coal_lims

# -------------------- EMAIL (Office 365) --------------------
MAIL_SERVER=smtp.office365.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=gantulga.u@mmc.mn
MAIL_PASSWORD=ЭНД_ИМЭЙЛИЙН_APP_PASSWORD_ТАВИНА
MAIL_DEFAULT_SENDER=gantulga.u@mmc.mn

# -------------------- SESSION --------------------
SESSION_COOKIE_HTTPONLY=True
SESSION_COOKIE_SAMESITE=Lax

# -------------------- ICPMS --------------------
ICPMS_API_URL=http://localhost:8000
ICPMS_USERNAME=lims_service
ICPMS_PASSWORD=
ICPMS_TIMEOUT=30

# ============================================================================
```

### 4.4. Файлыг хадгалах

1. `Ctrl + O` дарна (хадгалах)
2. `Enter` дарна (файлын нэр батлах)
3. `Ctrl + X` дарна (гарах)

### 4.5. Файлын эрхийг хязгаарлах (чухал!)

```bash
chmod 600 /opt/coal_lims/.env
```

Энэ команд нь `.env` файлыг зөвхөн та өөрөө уншиж чадна, бусад хүн харах боломжгүй болгоно.

---

## 5-р алхам: Nginx тохиргооны файл үүсгэх

Nginx бол "хаалганы жижүүр" — гаднаас ирсэн хүсэлтийг LIMS рүү дамжуулна.

```bash
nano /opt/coal_lims/nginx.conf
```

Доорх текстийг бүхэлд нь paste хийнэ:

```nginx
worker_processes auto;
events {
    worker_connections 1024;
}

http {
    include       /etc/nginx/mime.types;
    default_type  application/octet-stream;
    sendfile      on;
    keepalive_timeout 65;

    # Хэт том request хориглох (16MB хүртэл зөвшөөрнө — файл upload-д)
    client_max_body_size 16M;

    # Gzip шахалт (хуудас хурдан ачаалагдана)
    gzip on;
    gzip_types text/plain text/css application/json application/javascript text/xml;
    gzip_min_length 1000;

    # Аюулгүй байдлын толгой
    add_header X-Frame-Options SAMEORIGIN always;
    add_header X-Content-Type-Options nosniff always;
    add_header X-XSS-Protection "1; mode=block" always;

    # Rate limit (DDoS хамгаалалт)
    limit_req_zone $binary_remote_addr zone=general:10m rate=30r/s;
    limit_req_zone $binary_remote_addr zone=login:10m rate=5r/m;

    upstream lims_app {
        server web:5000;
    }

    server {
        listen 80;
        server_name _;

        # Static файлууд (CSS, JS, зураг) — Nginx шууд өгнө (хурдан)
        location /static/ {
            alias /usr/share/nginx/html/static/;
            expires 7d;
            add_header Cache-Control "public, immutable";
            access_log off;
        }

        # Login хуудас — хатуу rate limit
        location /login {
            limit_req zone=login burst=3 nodelay;
            proxy_pass http://lims_app;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }

        # WebSocket (чат, real-time шинэчлэл)
        location /socket.io/ {
            proxy_pass http://lims_app;
            proxy_http_version 1.1;
            proxy_set_header Upgrade $http_upgrade;
            proxy_set_header Connection "upgrade";
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_read_timeout 86400;
        }

        # Бусад бүх хүсэлт
        location / {
            limit_req zone=general burst=50 nodelay;
            proxy_pass http://lims_app;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            proxy_read_timeout 120;
        }
    }
}
```

Хадгалах: `Ctrl + O` → `Enter` → `Ctrl + X`

---

## 6-р алхам: SSL хавтас үүсгэх

```bash
mkdir -p /opt/coal_lims/ssl
```

Хэрэв HTTPS (домэйн) ашиглахгүй бол хоосон хавтас хангалттай.

---

## 7-р алхам: Шаардлагатай хавтсууд үүсгэх

```bash
cd /opt/coal_lims
mkdir -p instance logs backups
```

---

## 8-р алхам: Систем ажиллуулах!

```bash
cd /opt/coal_lims

# Бүх зүйлийг эхлүүлэх (DB + Redis + Web + Nginx)
docker compose --profile production up -d --build
```

**Юу болж байна:**
1. Docker нь PostgreSQL мэдээллийн сан үүсгэнэ
2. Redis кэш сервер эхэлнэ
3. LIMS код бүтээгдэж (build) ажиллана
4. Nginx "хаалганы жижүүр" эхэлнэ

**Энэ 5-15 минут үргэлжилж болно** (анх удаа код бүтээх учраас). Хүлээнэ.

### Амжилттай эсэхийг шалгах:

```bash
# Бүх 4 service "Up" гэж харагдах ёстой
docker compose --profile production ps
```

Жишээ гаралт:
```
NAME                STATUS          PORTS
coal_lims_web       Up (healthy)    0.0.0.0:5000->5000/tcp
coal_lims_db        Up (healthy)    5432/tcp
coal_lims_redis     Up (healthy)    6379/tcp
coal_lims_nginx     Up              0.0.0.0:80->80/tcp
```

4-үүлээ **Up** гэж харагдвал амжилттай!

---

## 9-р алхам: Мэдээллийн сангийн бүтэц үүсгэх (migration)

```bash
# Docker container дотор migration ажиллуулах
docker compose exec web flask db upgrade
```

Энэ команд нь бүх хүснэгт, индекс, constraint-уудыг мэдээллийн санд үүсгэнэ.

**"ERROR" гэж гарвал:** migration-ний алдаа байна, намайг дуудна уу.

---

## 10-р алхам: Анхны admin хэрэглэгч үүсгэх

```bash
docker compose exec web flask shell
```

Python shell нээгдэнэ (>>> тэмдэг гарна). Доорх кодыг бүхэлд нь paste хийнэ:

```python
from app.models import User
from app import db

admin = User(username='admin', role='admin')
admin.set_password('Admin12345!')
db.session.add(admin)
db.session.commit()
print("Admin хэрэглэгч үүслээ!")
exit()
```

---

## 11-р алхам: Браузераар шалгах!

Компьютерийн браузерт:
```
http://СЕРВЕРИЙН_IP_ХАЯГ
```

Жишээ: `http://192.168.1.100`

**Нэвтрэх:**
- Нэр: `admin`
- Нууц үг: `Admin12345!`

Нэвтэрч чадвал **АМЖИЛТТАЙ!**

---

## 12-р алхам: Автомат нөөцлөлт (Backup) тохируулах

### 12.1. Backup script үүсгэх

```bash
nano /opt/coal_lims/backup.sh
```

Paste хийнэ:

```bash
#!/bin/bash
# Coal LIMS - Automatic Database Backup
BACKUP_DIR="/opt/coal_lims/backups"
DATE=$(date +%Y%m%d_%H%M%S)
FILENAME="coal_lims_backup_${DATE}.sql.gz"

# Backup хийх
docker compose exec -T db pg_dump -U lims_user coal_lims | gzip > "${BACKUP_DIR}/${FILENAME}"

# 30 хоногоос хуучин backup устгах
find ${BACKUP_DIR} -name "*.sql.gz" -mtime +30 -delete

echo "Backup done: ${FILENAME}"
```

Хадгалах: `Ctrl + O` → `Enter` → `Ctrl + X`

```bash
# Script-г ажиллуулах боломжтой болгох
chmod +x /opt/coal_lims/backup.sh
```

### 12.2. Өдөр бүр шөнийн 2 цагт автомат backup

```bash
crontab -e
```

Нээгдсэн файлын **хамгийн доод мөрөнд** нэмнэ:

```
0 2 * * * /opt/coal_lims/backup.sh >> /opt/coal_lims/logs/backup.log 2>&1
```

Хадгалах: `Ctrl + O` → `Enter` → `Ctrl + X`

---

## 13-р алхам: Хуучин мэдээллийн сангийн өгөгдөл шилжүүлэх

Хэрэв одоо development дээр ашиглаж байгаа мэдээлэл (дээж, шинжилгээний үр дүн гэх мэт) байгаа бол шилжүүлнэ.

### 13.1. Development компьютераас export хийх

Development компьютер дээрээ (Windows):

```bash
cd D:\coal_lims_project
pg_dump -U postgres -h localhost coal_lims > coal_lims_data.sql
```

### 13.2. Файлыг серверт хуулах

WinSCP програм ашиглан `coal_lims_data.sql` файлыг серверийн `/opt/coal_lims/backups/` руу хуулна.

Эсвэл SCP ашиглаж болно:
```bash
scp coal_lims_data.sql username@SERVER_IP:/opt/coal_lims/backups/
```

### 13.3. Серверт import хийх

```bash
cd /opt/coal_lims

# Хуучин DB-г устгаад дахин үүсгэх
docker compose exec db psql -U lims_user -d postgres -c "DROP DATABASE IF EXISTS coal_lims;"
docker compose exec db psql -U lims_user -d postgres -c "CREATE DATABASE coal_lims;"

# Өгөгдөл оруулах
cat backups/coal_lims_data.sql | docker compose exec -T db psql -U lims_user -d coal_lims

# Migration шинэчлэх
docker compose exec web flask db upgrade
```

---

## Хэрэгтэй командууд (хадгалж авна уу!)

Серверт SSH-ээр нэвтрэн, `/opt/coal_lims` хавтас руу очоод ажиллуулна:

```bash
cd /opt/coal_lims
```

| Юу хийх | Команд |
|---------|--------|
| **Систем эхлүүлэх** | `docker compose --profile production up -d` |
| **Систем зогсоох** | `docker compose --profile production down` |
| **Систем дахин ачаалах** | `docker compose --profile production restart` |
| **Төлөв шалгах** | `docker compose --profile production ps` |
| **Web log харах** | `docker compose logs -f web` |
| **DB log харах** | `docker compose logs -f db` |
| **Бүх log харах** | `docker compose logs -f` |
| **Гараар backup хийх** | `./backup.sh` |
| **Код шинэчлэх** | Доорх "Шинэчлэх" хэсгийг хар |
| **DB руу нэвтрэх** | `docker compose exec db psql -U lims_user -d coal_lims` |
| **Flask shell** | `docker compose exec web flask shell` |

---

## Код шинэчлэх (Update хийх)

GitHub-д шинэ код push хийсний дараа серверт шинэчлэхдээ:

```bash
cd /opt/coal_lims

# 1. Шинэ код татах
git pull origin main

# 2. Дахин бүтээж ачаалах
docker compose --profile production up -d --build

# 3. Migration (хэрэв шинэ migration нэмэгдсэн бол)
docker compose exec web flask db upgrade
```

---

## Алдаа засах (Troubleshooting)

### "Нээгдэхгүй байна"

```bash
# 1. Service ажиллаж байгаа эсэх шалгах
docker compose --profile production ps

# 2. Web log-оос алдаа харах
docker compose logs --tail=50 web

# 3. Firewall шалгах (80 порт нээлттэй байх ёстой)
sudo ufw allow 80
sudo ufw allow 443
```

### "Database error"

```bash
# DB ажиллаж байгаа эсэх
docker compose logs --tail=20 db

# DB холболт шалгах
docker compose exec web python -c "from app import create_app, db; app=create_app();
with app.app_context(): db.session.execute(db.text('SELECT 1')); print('DB OK')"
```

### "Бүх зүйл эвдэрчихлээ"

```bash
cd /opt/coal_lims

# Бүгдийг зогсоож дахин эхлүүлэх
docker compose --profile production down
docker compose --profile production up -d --build

# Log харах
docker compose logs -f
```

### Backup-аас сэргээх

```bash
# Хамгийн сүүлийн backup олох
ls -la backups/

# Сэргээх (ФАЙЛЫН_НЭРИЙГ солино)
gunzip -c backups/coal_lims_backup_20260228_020000.sql.gz | \
  docker compose exec -T db psql -U lims_user -d coal_lims
```

---

## Аюулгүй байдлын шалгах хуудас

Бүгд дуусмагц доорх зүйлсийг шалгана:

- [ ] `.env` файлд `DEBUG=False` байна уу?
- [ ] `.env` файлд `SECRET_KEY` урт random текст байна уу?
- [ ] `.env` файлын эрх `chmod 600` хийсэн үү?
- [ ] `DB_PASSWORD` нь "lims_password" биш өөр нууц үг байна уу?
- [ ] `MAIL_PASSWORD` жинхэнэ нууц үг байна уу?
- [ ] Серверийн firewall зөвхөн 80, 443, 22 порт нээлттэй юу?
- [ ] Backup автомат ажиллаж байна уу? (`./backup.sh` гараар туршина)
- [ ] Браузераар нэвтэрч чадаж байна уу?
- [ ] Admin нууц үгээ `Admin12345!`-аас **СОЛИСОН** уу?

---

## Тусламж хэрэгтэй бол

Алдаа гарвал дараах мэдээллийг хадгалж өгнө үү:

```bash
# Энэ командыг ажиллуулаад гаралтыг хуулна
docker compose --profile production ps
docker compose logs --tail=100 web
docker compose logs --tail=50 db
```
