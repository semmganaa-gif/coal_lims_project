# config/base.py
"""Base paths, environment detection, timezone, secret key."""

import os
import secrets
from datetime import timezone, timedelta
from zoneinfo import ZoneInfo
from dotenv import load_dotenv

# Project root
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

# Load .env
load_dotenv(os.path.join(BASE_DIR, ".env"))

# Instance directory
INSTANCE_DIR = os.path.join(BASE_DIR, "instance")
os.makedirs(INSTANCE_DIR, exist_ok=True)


def _tz():
    """Return Asia/Ulaanbaatar timezone with UTC+8 fallback."""
    try:
        return ZoneInfo("Asia/Ulaanbaatar")
    except Exception as e:
        import logging
        logging.warning(f"ZoneInfo unavailable: {e}. Using UTC+8 fallback.")
        return timezone(timedelta(hours=8))


def _secret_key():
    """Load SECRET_KEY from env → instance file → random runtime token."""
    env_key = os.getenv("SECRET_KEY")
    if env_key:
        return env_key
    key_path = os.path.join(INSTANCE_DIR, "secret_key")
    if os.path.exists(key_path):
        with open(key_path, "r", encoding="utf-8") as f:
            return f.read().strip()
    return secrets.token_urlsafe(48)


class BaseConfig:
    """Environment, timezone, and secret key."""
    TIMEZONE = _tz()
    SECRET_KEY = _secret_key()
    ENV = os.getenv("FLASK_ENV", "production")
    DEBUG = ENV == "development"
