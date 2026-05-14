# config/database.py
"""Database and connection pool configuration."""

import os
from config.base import INSTANCE_DIR


def _build_engine_options(db_uri: str) -> dict:
    """Dialect-д тохирох SQLAlchemy engine options үүсгэх.

    PostgreSQL (psycopg2) `connect_args={"options": "-c ..."}` хүлээж авдаг.
    SQLite энэ синтаксыг хүлээн авдаггүй тул алдаа өгнө.
    """
    opts: dict = {
        "pool_pre_ping": True,
    }

    is_postgres = db_uri.startswith(("postgresql://", "postgresql+", "postgres://"))
    is_sqlite = db_uri.startswith("sqlite:")

    if is_postgres:
        # Connection pool нь зөвхөн PostgreSQL production-д утга бүхий.
        # (SQLite нь single-file, pool-гүй драйвертэй.)
        opts.update({
            "pool_size": int(os.getenv("DB_POOL_SIZE", 25)),
            "max_overflow": int(os.getenv("DB_MAX_OVERFLOW", 25)),
            "pool_recycle": int(os.getenv("DB_POOL_RECYCLE", 300)),
            "pool_timeout": int(os.getenv("DB_POOL_TIMEOUT", 15)),
            "connect_args": {
                "options": f"-c statement_timeout={int(os.getenv('DB_STATEMENT_TIMEOUT_MS', 30000))}"
            },
        })
    elif is_sqlite:
        # SQLite-д multi-thread хэрэглээ (Flask + background job)
        opts["connect_args"] = {"check_same_thread": False}

    return opts


class DatabaseConfig:
    """SQLAlchemy database settings."""
    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABASE_URL",
        f"sqlite:///{os.path.join(INSTANCE_DIR, 'lims.db')}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    SQLALCHEMY_ENGINE_OPTIONS = _build_engine_options(SQLALCHEMY_DATABASE_URI)
