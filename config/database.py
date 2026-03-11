# config/database.py
"""Database and connection pool configuration."""

import os
from config.base import INSTANCE_DIR


class DatabaseConfig:
    """SQLAlchemy database settings."""
    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABASE_URL",
        f"sqlite:///{os.path.join(INSTANCE_DIR, 'lims.db')}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Connection pool (PostgreSQL production)
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_size": int(os.getenv("DB_POOL_SIZE", 25)),
        "max_overflow": int(os.getenv("DB_MAX_OVERFLOW", 25)),
        "pool_recycle": int(os.getenv("DB_POOL_RECYCLE", 300)),
        "pool_pre_ping": True,
        "pool_timeout": int(os.getenv("DB_POOL_TIMEOUT", 15)),
        "connect_args": {"options": "-c statement_timeout=30000"},
    }
