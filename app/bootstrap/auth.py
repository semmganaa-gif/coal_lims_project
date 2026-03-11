# app/bootstrap/auth.py
"""Flask-Login user loader setup."""

from app.bootstrap.extensions import db, login


def init_auth(app):
    """Register user loader callback."""

    @login.user_loader
    def load_user(id):
        from app import models
        try:
            return db.session.get(models.User, int(id))
        except (ValueError, TypeError):
            return None
