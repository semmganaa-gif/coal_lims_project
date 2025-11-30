# config.py
import os, secrets
from datetime import timezone, timedelta
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

# Төслийн үндсэн зам (root folder)
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
INSTANCE_DIR = os.path.join(BASE_DIR, "instance")
os.makedirs(INSTANCE_DIR, exist_ok=True)

def _tz():
    """
    Монгол цагийн бүсийг буцаана.

    ✅ САЙЖРУУЛСАН: tzdata requirements.txt-д байгаа тул
    олон давхар fallback хэрэггүй болсон.
    """
    try:
        return ZoneInfo("Asia/Ulaanbaatar")
    except Exception as e:
        # Хэрэв ZoneInfo алдаа гарвал fallback ашиглана
        import logging
        logging.warning(f"ZoneInfo татаж чадсангүй: {e}. UTC+8 ашиглана.")
        return timezone(timedelta(hours=8))

def _secret_key():
    # 1) ENV-ээс уншина (prod-д ингэж өг)
    env_key = os.getenv("SECRET_KEY")
    if env_key:
        return env_key
    # 2) instance/secret_key файлд хадгалж тогтмол болгоно
    key_path = os.path.join(INSTANCE_DIR, "secret_key")
    if os.path.exists(key_path):
        return open(key_path, "r", encoding="utf-8").read().strip()
    key = secrets.token_urlsafe(48)
    with open(key_path, "w", encoding="utf-8") as f:
        f.write(key)
    return key

class Config:
    TIMEZONE = _tz()
    SECRET_KEY = _secret_key()

    # Environment тодорхойлох (production эсвэл development)
    ENV = os.getenv("FLASK_ENV", "production")
    DEBUG = ENV == "development"

    # DB
    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABASE_URL",
        f"sqlite:///{os.path.join(INSTANCE_DIR, 'lims.db')}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # ✅ САЙЖРУУЛСАН: Cookie аюулгүй байдал (Production-д автоматаар идэвхжинэ)
    SESSION_COOKIE_SAMESITE = "Lax"
    SESSION_COOKIE_SECURE = ENV == "production"  # Production-д HTTPS шаардлагатай
    SESSION_COOKIE_HTTPONLY = True  # JavaScript-ээс хандахгүй байх

    # CSRF хамгаалалт
    WTF_CSRF_ENABLED = True
    WTF_CSRF_TIME_LIMIT = None  # Токен хугацаа хязгааргүй

    # ✅ ШИНЭ: Файл хадгалах зам (Гэрчилгээ хавсаргахад)
    # BASE_DIR ашиглан замыг бүтэн зааж өгнө.
    UPLOAD_FOLDER = os.path.join(BASE_DIR, 'app', 'static', 'uploads', 'certificates')

    # ========================================================
    # ✅ ШИНЭ: EMAIL CONFIGURATION (MMC / Office 365)
    # ========================================================
    # Доорх утгуудыг IT-аас авсан мэдээллээрээ сольж болно.
    # Одоохондоо та туршихдаа шууд энд бичиж болно, эсвэл .env файл ашиглаж болно.
    
    MAIL_SERVER = os.getenv('MAIL_SERVER', 'smtp.office365.com')
    MAIL_PORT = int(os.getenv('MAIL_PORT', 587))
    MAIL_USE_TLS = os.getenv('MAIL_USE_TLS', 'True') == 'True'
    
    # Таны ажлын имэйл
    MAIL_USERNAME = os.getenv('MAIL_USERNAME', 'gantulga.u@mmc.mn')
    
    # Энд нууц үгээ бичнэ (Эсвэл IT-аас авсан App Password)
    MAIL_PASSWORD = os.getenv('MAIL_PASSWORD', 'mfrdlxfzvsfskvgb') 
    
    MAIL_DEFAULT_SENDER = os.getenv('MAIL_DEFAULT_SENDER', 'gantulga.u@mmc.mn')

    # ========================================================
    # 🔒 SECURITY LOGGING CONFIGURATION
    # ========================================================
    # Серверийн тооцоололын зөрүү, тамперинг оролдлого, security events
    SECURITY_LOG_FILE = os.path.join(INSTANCE_DIR, 'logs', 'security.log')
    APP_LOG_FILE = os.path.join(INSTANCE_DIR, 'logs', 'app.log')

    # Logs директори үүсгэх
    os.makedirs(os.path.join(INSTANCE_DIR, 'logs'), exist_ok=True)