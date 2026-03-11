# config/security.py
"""Session cookies, CSRF, and Remember Me configuration."""

import os
from datetime import timedelta

_ENV = os.getenv("FLASK_ENV", "production")
_IS_PROD = _ENV != "development"


class SecurityConfig:
    """Cookie and CSRF security settings."""
    # Session cookies
    SESSION_COOKIE_SAMESITE = "Lax"
    SESSION_COOKIE_SECURE = _IS_PROD
    SESSION_COOKIE_HTTPONLY = True
    PERMANENT_SESSION_LIFETIME = timedelta(hours=8)

    # Remember Me
    REMEMBER_COOKIE_HTTPONLY = True
    REMEMBER_COOKIE_SAMESITE = "Lax"
    REMEMBER_COOKIE_SECURE = _IS_PROD
    REMEMBER_COOKIE_DURATION = timedelta(days=7)

    # CSRF
    WTF_CSRF_ENABLED = True
    WTF_CSRF_TIME_LIMIT = 1800  # 30 minutes
    WTF_CSRF_SSL_STRICT = _IS_PROD

    # File uploads
    UPLOAD_FOLDER = os.path.join(
        os.path.abspath(os.path.join(os.path.dirname(__file__), '..')),
        'app', 'static', 'uploads', 'certificates'
    )
