# app/bootstrap/errors.py
"""HTTP error handlers."""

from app.bootstrap.extensions import db


def init_error_handlers(app):
    """Register error handlers for 404, 500, 403, 429."""

    @app.errorhandler(404)
    def not_found_error(error):
        from flask import render_template
        return render_template('errors/404.html'), 404

    @app.errorhandler(500)
    def internal_error(error):
        from flask import render_template
        db.session.rollback()
        app.logger.error(f'Server Error: {error}', exc_info=True)
        return render_template('errors/500.html'), 500

    @app.errorhandler(403)
    def forbidden_error(error):
        from flask import render_template
        return render_template('errors/403.html'), 403

    @app.errorhandler(429)
    def ratelimit_handler(error):
        from flask import render_template, jsonify, request
        if request.path.startswith('/api/'):
            return jsonify({
                'error': 'Too many requests. Please wait and try again.',
                'status': 429
            }), 429
        return render_template('errors/429.html'), 429
