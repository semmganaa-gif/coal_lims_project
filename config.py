# config.py
import os, secrets
from datetime import timezone, timedelta
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
INSTANCE_DIR = os.path.join(BASE_DIR, "instance")
os.makedirs(INSTANCE_DIR, exist_ok=True)

def _tz():
    try:
        return ZoneInfo("Asia/Ulaanbaatar")
    except Exception:
        try:
            import tzdata  # noqa: F401
            return ZoneInfo("Asia/Ulaanbaatar")
        except Exception:
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
    SECRET_KEY = _secret_key()  # ← ҮҮНИЙГ НЭМНЭ

    # DB
    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABASE_URL",
        f"sqlite:///{os.path.join(INSTANCE_DIR, 'lims.db')}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # (сонголттой) cookie-гийн аюулгүй тохиргоо
    SESSION_COOKIE_SAMESITE = "Lax"
    SESSION_COOKIE_SECURE = False  # HTTPS орчинд True болгоорой
