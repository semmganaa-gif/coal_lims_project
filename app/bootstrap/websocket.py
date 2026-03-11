# app/bootstrap/websocket.py
"""SocketIO initialization and chat event registration."""

from app.bootstrap.extensions import socketio


def init_websocket(app):
    """Initialize SocketIO with app config and register chat events."""
    _mq = app.config.get('SOCKETIO_MESSAGE_QUEUE')
    _async_mode = app.config.get('SOCKETIO_ASYNC_MODE', 'threading')
    socketio.init_app(
        app,
        cors_allowed_origins=app.config.get('SOCKETIO_CORS_ORIGINS', None),
        async_mode=_async_mode,
        message_queue=_mq,
    )
    if not _mq and not app.debug:
        app.logger.warning(
            "SocketIO: message_queue тохируулаагүй — multi-worker WebSocket sync ажиллахгүй. "
            "SOCKETIO_MESSAGE_QUEUE=redis://localhost:6379 тохируулна уу."
        )

    # Register chat SocketIO events
    with app.app_context():
        from app.routes.chat import events as _chat_events  # noqa: F401
