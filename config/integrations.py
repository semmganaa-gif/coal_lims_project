# config/integrations.py
"""WebSocket, rate limiting, caching, and external service configuration."""

import os

_ENV = os.getenv("FLASK_ENV", "production")


class IntegrationsConfig:
    """SocketIO, rate limiter, cache, and simulator settings."""
    # WebSocket
    SOCKETIO_CORS_ORIGINS = os.getenv(
        'SOCKETIO_CORS_ORIGINS',
        '*' if _ENV == 'development' else None
    )
    SOCKETIO_MESSAGE_QUEUE = os.getenv('SOCKETIO_MESSAGE_QUEUE', None)
    SOCKETIO_ASYNC_MODE = os.getenv(
        'SOCKETIO_ASYNC_MODE',
        'gevent' if _ENV != 'development' else 'threading'
    )

    # Rate limiting
    RATELIMIT_STORAGE_URI = os.getenv('RATELIMIT_STORAGE_URI', 'memory://')

    # Caching
    CACHE_TYPE = os.getenv('CACHE_TYPE', 'SimpleCache')
    CACHE_DEFAULT_TIMEOUT = int(os.getenv('CACHE_DEFAULT_TIMEOUT', 300))

    # Celery (background tasks)
    CELERY_BROKER_URL = os.getenv('CELERY_BROKER_URL', 'redis://localhost:6379/1')
    CELERY_RESULT_BACKEND = os.getenv('CELERY_RESULT_BACKEND', 'redis://localhost:6379/2')
    CELERY_TIMEZONE = 'Asia/Ulaanbaatar'

    # Instrument file import
    INSTRUMENT_BASE_PATH = os.getenv('INSTRUMENT_BASE_PATH', 'instrument_data')
    INSTRUMENT_WATCH_DIRS = {
        'tga': 'tga',
        'bomb_cal': 'bomb_cal',
        'elemental': 'elemental',
        'generic_csv': 'generic_csv',
    }
    INSTRUMENT_PROCESSED_DIR = os.getenv('INSTRUMENT_PROCESSED_DIR', 'instrument_data/_processed')

    # CHPP Simulator
    SIMULATOR_URL = os.getenv('SIMULATOR_URL', 'http://localhost:8001')

    # Mine2NEMO ProcessControl SQL Server
    # CHPP 2-hourly дээжүүдийг шууд бичих (Zobo legacy compat)
    # Хоосон бол feature идэвхгүй
    MINE2NEMO_DATABASE_URL = os.getenv('MINE2NEMO_DATABASE_URL', '')
