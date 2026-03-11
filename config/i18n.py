# config/i18n.py
"""Internationalization (Flask-Babel) configuration."""


class I18nConfig:
    """Babel locale and language settings."""
    BABEL_DEFAULT_LOCALE = 'en'
    BABEL_DEFAULT_TIMEZONE = 'Asia/Ulaanbaatar'
    LANGUAGES = {'en': 'English', 'mn': 'Монгол'}
