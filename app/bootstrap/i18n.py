# app/bootstrap/i18n.py
"""Babel locale selector setup."""

from app.bootstrap.extensions import babel


def get_locale():
    """Select user's preferred language from session or profile."""
    from flask import session
    lang = session.get('language')
    if lang in ('en', 'mn'):
        return lang
    from flask_login import current_user
    if current_user.is_authenticated and getattr(current_user, 'language', None):
        return current_user.language
    return 'en'


def init_i18n(app):
    """Initialize Flask-Babel with locale selector."""
    babel.init_app(app, locale_selector=get_locale)
