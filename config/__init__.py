# config/__init__.py
"""
Configuration package — split by domain for maintainability.

Usage (backward compatible):
    from config import Config
"""

from config.base import BASE_DIR, INSTANCE_DIR
from config.base import BaseConfig
from config.database import DatabaseConfig
from config.security import SecurityConfig
from config.mail import MailConfig
from config.integrations import IntegrationsConfig
from config.runtime import RuntimeConfig
from config.i18n import I18nConfig


class Config(
    BaseConfig,
    DatabaseConfig,
    SecurityConfig,
    MailConfig,
    IntegrationsConfig,
    RuntimeConfig,
    I18nConfig,
):
    """Merged configuration — drop-in replacement for the old monolithic Config."""
    pass
