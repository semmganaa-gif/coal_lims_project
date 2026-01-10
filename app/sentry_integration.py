# -*- coding: utf-8 -*-
"""
Sentry Error Tracking Integration
Coal LIMS - Exception monitoring and performance tracking
"""
import os
import logging

logger = logging.getLogger(__name__)

# Sentry SDK availability check
try:
    import sentry_sdk
    from sentry_sdk.integrations.flask import FlaskIntegration
    from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration
    from sentry_sdk.integrations.logging import LoggingIntegration
    SENTRY_AVAILABLE = True
except ImportError:
    SENTRY_AVAILABLE = False
    sentry_sdk = None


def init_sentry(app):
    """
    Initialize Sentry error tracking.

    Environment variables:
        SENTRY_DSN: Sentry project DSN (required to enable)
        SENTRY_ENVIRONMENT: Environment name (production, staging, development)
        SENTRY_TRACES_SAMPLE_RATE: Performance monitoring sample rate (0.0 - 1.0)

    Args:
        app: Flask application instance
    """
    if not SENTRY_AVAILABLE:
        logger.info("Sentry SDK not installed. Skipping initialization.")
        return False

    dsn = os.environ.get('SENTRY_DSN') or app.config.get('SENTRY_DSN')

    if not dsn:
        logger.info("SENTRY_DSN not configured. Sentry disabled.")
        return False

    # Skip in testing mode
    if app.config.get('TESTING'):
        logger.info("Testing mode - Sentry disabled.")
        return False

    environment = os.environ.get('SENTRY_ENVIRONMENT') or app.config.get('ENV', 'development')
    traces_sample_rate = float(
        os.environ.get('SENTRY_TRACES_SAMPLE_RATE') or
        app.config.get('SENTRY_TRACES_SAMPLE_RATE', 0.1)
    )

    # Configure Sentry logging integration
    sentry_logging = LoggingIntegration(
        level=logging.INFO,        # Capture info and above as breadcrumbs
        event_level=logging.ERROR  # Send errors as events
    )

    try:
        sentry_sdk.init(
            dsn=dsn,
            environment=environment,
            integrations=[
                FlaskIntegration(),
                SqlalchemyIntegration(),
                sentry_logging,
            ],
            # Performance monitoring
            traces_sample_rate=traces_sample_rate,

            # Send PII data (careful in production)
            send_default_pii=False,

            # Release version (from app config or env)
            release=app.config.get('VERSION', os.environ.get('APP_VERSION', '1.0.0')),

            # Before send hook for filtering
            before_send=before_send_filter,

            # Before breadcrumb hook
            before_breadcrumb=before_breadcrumb_filter,
        )

        logger.info(f"Sentry initialized for environment: {environment}")
        return True

    except Exception as e:
        logger.error(f"Failed to initialize Sentry: {e}")
        return False


def before_send_filter(event, hint):
    """
    Filter events before sending to Sentry.

    Use this to:
    - Scrub sensitive data
    - Filter out specific errors
    - Add custom context

    Args:
        event: Sentry event dict
        hint: Additional context

    Returns:
        event dict or None to drop the event
    """
    # Get the original exception if available
    if 'exc_info' in hint:
        exc_type, exc_value, tb = hint['exc_info']

        # Filter out common non-errors
        ignored_exceptions = (
            # Rate limit errors (expected behavior)
            'RateLimitExceeded',
            # Client disconnects
            'ConnectionResetError',
            'BrokenPipeError',
            # 404s are usually not errors
            'NotFound',
        )

        if exc_type and exc_type.__name__ in ignored_exceptions:
            return None

    # Scrub sensitive headers
    if 'request' in event:
        headers = event['request'].get('headers', {})
        sensitive_headers = ['Authorization', 'Cookie', 'X-CSRF-Token']
        for header in sensitive_headers:
            if header in headers:
                headers[header] = '[Filtered]'

    # Add custom tags
    event.setdefault('tags', {})
    event['tags']['app'] = 'coal-lims'

    return event


def before_breadcrumb_filter(crumb, hint):
    """
    Filter breadcrumbs before adding to event.

    Args:
        crumb: Breadcrumb dict
        hint: Additional context

    Returns:
        breadcrumb dict or None to drop
    """
    # Filter out noisy SQL queries
    if crumb.get('category') == 'query':
        # Skip SELECT 1 health checks
        if 'SELECT 1' in crumb.get('message', ''):
            return None

    # Filter out static file requests
    if crumb.get('category') == 'http':
        url = crumb.get('data', {}).get('url', '')
        if '/static/' in url or '.css' in url or '.js' in url:
            return None

    return crumb


def capture_exception(error, **extra):
    """
    Capture an exception with additional context.

    Args:
        error: Exception to capture
        **extra: Additional context to attach
    """
    if not SENTRY_AVAILABLE or not sentry_sdk:
        logger.error(f"Exception (Sentry unavailable): {error}")
        return

    with sentry_sdk.push_scope() as scope:
        for key, value in extra.items():
            scope.set_extra(key, value)
        sentry_sdk.capture_exception(error)


def capture_message(message, level='info', **extra):
    """
    Capture a message with additional context.

    Args:
        message: Message to capture
        level: Message level (info, warning, error)
        **extra: Additional context to attach
    """
    if not SENTRY_AVAILABLE or not sentry_sdk:
        logger.log(getattr(logging, level.upper(), logging.INFO), message)
        return

    with sentry_sdk.push_scope() as scope:
        for key, value in extra.items():
            scope.set_extra(key, value)
        sentry_sdk.capture_message(message, level=level)


def set_user_context(user):
    """
    Set user context for error tracking.

    Call this after user login to associate errors with users.

    Args:
        user: User object with id, username, and role attributes
    """
    if not SENTRY_AVAILABLE or not sentry_sdk:
        return

    if user and hasattr(user, 'id'):
        sentry_sdk.set_user({
            "id": str(user.id),
            "username": getattr(user, 'username', None),
            "role": getattr(user, 'role', None),
        })
    else:
        sentry_sdk.set_user(None)


def add_breadcrumb(message, category='custom', level='info', **data):
    """
    Add a custom breadcrumb for debugging.

    Args:
        message: Breadcrumb message
        category: Category (e.g., 'analysis', 'sample', 'qc')
        level: Level (debug, info, warning, error)
        **data: Additional data to attach
    """
    if not SENTRY_AVAILABLE or not sentry_sdk:
        return

    sentry_sdk.add_breadcrumb(
        message=message,
        category=category,
        level=level,
        data=data,
    )
