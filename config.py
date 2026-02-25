# config.py
import os, secrets
from datetime import timezone, timedelta
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError
from dotenv import load_dotenv

# Төслийн үндсэн зам (root folder)
BASE_DIR = os.path.abspath(os.path.dirname(__file__))

# .env файлаас environment variables ачаалах
load_dotenv(os.path.join(BASE_DIR, ".env"))
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
        with open(key_path, "r", encoding="utf-8") as f:
            return f.read().strip()
    # 3) Файл байхгүй бол runtime-д л ашиглах түр түлхүүр буцаана (import үед бичихгүй)
    return secrets.token_urlsafe(48)

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

    # DB connection pool тохиргоо (PostgreSQL production-д)
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_size": 10,          # Үндсэн холболтын тоо
        "max_overflow": 20,       # Нэмэлт холболт (завгүй үед)
        "pool_recycle": 300,      # 5 мин-д нэг холболт шинэчлэх (idle timeout)
        "pool_pre_ping": True,    # Query-н өмнө холболт амьд эсэх шалгах
        "pool_timeout": 10,       # Холболт хүлээх хугацаа (секунд)
    }

    # ✅ САЙЖРУУЛСАН: Cookie аюулгүй байдал
    SESSION_COOKIE_SAMESITE = "Lax"
    # Production-д HTTPS ашиглах тул True, development-д False
    SESSION_COOKIE_SECURE = ENV != "development"
    SESSION_COOKIE_HTTPONLY = True  # JavaScript-ээс хандахгүй байх

    # ✅ CSRF хамгаалалт - ИДЭВХЖҮҮЛСЭН
    WTF_CSRF_ENABLED = True  # Production-д заавал идэвхтэй байх
    WTF_CSRF_TIME_LIMIT = 3600  # Токен 1 цагийн дараа дуусна (секундээр)
    WTF_CSRF_SSL_STRICT = ENV != "development"  # Production-д HTTPS шаардах

    # Session тохиргоо (SECRET_KEY дээр тодорхойлогдсон)

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

    # ✅ ЗАСВАРЛАСАН: Имэйл тохиргоо - зөвхөн .env файлаас авна
    # .env файлд: MAIL_USERNAME=your@email.com, MAIL_PASSWORD=your_password
    MAIL_USERNAME = os.getenv('MAIL_USERNAME', '')
    MAIL_PASSWORD = os.getenv('MAIL_PASSWORD', '')  # ⚠️ Hardcoded нууц үг УСТГАСАН
    MAIL_DEFAULT_SENDER = os.getenv('MAIL_DEFAULT_SENDER', '')

    # ========================================================
    # 🔒 WEBSOCKET CORS CONFIGURATION
    # ========================================================
    # Production-д зөвхөн өөрийн домэйнээс холболт зөвшөөрнө
    # Development-д бүх origin-ээс зөвшөөрнө (ngrok, localhost гэх мэт)
    SOCKETIO_CORS_ORIGINS = os.getenv('SOCKETIO_CORS_ORIGINS', '*' if ENV == 'development' else None)

    # ========================================================
    # 🔒 RATE LIMIT STORAGE (Redis гэх мэт)
    # ========================================================
    RATELIMIT_STORAGE_URI = os.getenv('RATELIMIT_STORAGE_URI', 'memory://')

    # ========================================================
    # 🔒 SECURITY LOGGING CONFIGURATION
    # ========================================================
    # Серверийн тооцоололын зөрүү, тамперинг оролдлого, security events
    SECURITY_LOG_FILE = os.path.join(INSTANCE_DIR, 'logs', 'security.log')
    APP_LOG_FILE = os.path.join(INSTANCE_DIR, 'logs', 'app.log')

    # Logs директори үүсгэх
    os.makedirs(os.path.join(INSTANCE_DIR, 'logs'), exist_ok=True)

    # ========================================================
    # CHPP SIMULATOR INTEGRATION
    # ========================================================
    SIMULATOR_URL = os.getenv('SIMULATOR_URL', 'http://localhost:8001')

    # ========================================================
    # FLASK-BABEL (i18n) CONFIGURATION
    # ========================================================
    BABEL_DEFAULT_LOCALE = 'en'
    BABEL_DEFAULT_TIMEZONE = 'Asia/Ulaanbaatar'
    LANGUAGES = {'en': 'English', 'mn': 'Монгол'}
