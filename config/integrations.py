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

    # CHPP Simulator
    SIMULATOR_URL = os.getenv('SIMULATOR_URL', 'http://localhost:8001')
