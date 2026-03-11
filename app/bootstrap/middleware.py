# app/bootstrap/middleware.py
"""Request lifecycle hooks: license check, dev cookie override."""

from flask import redirect, url_for, flash, request, g
from flask_login import current_user


# Endpoints exempt from license validation
LICENSE_EXEMPT_ENDPOINTS = {
    'license.activate', 'license.info', 'license.expired', 'license.error',
    'license.check', 'license.hardware_id',
    'main.login', 'main.logout', 'main.register',
    'static', 'health_check',
}


def init_middleware(app):
    """Register before_request hooks."""

    # Development mode: disable secure cookies for HTTP
    if app.config.get('ENV') == 'development' or app.debug:
        app.config['SESSION_COOKIE_SECURE'] = False

    @app.before_request
    def check_license():
        """Validate system license on every authenticated request."""
        # Skip in test environment
        if app.config.get('TESTING'):
            g.license_valid = True
            g.license_warning = None
            g.license_info = {'company': 'Test', 'expires_at': '2099-12-31'}
            return None

        # Skip for exempt endpoints and static files
        if request.endpoint in LICENSE_EXEMPT_ENDPOINTS:
            return None
        if request.endpoint and request.endpoint.startswith('static'):
            return None

        # Unauthenticated users pass through
        if not current_user.is_authenticated:
            return None

        # Validate license
        from app.utils.license_protection import license_manager
        result = license_manager.validate_license()

        g.license_valid = result.get('valid', False)
        g.license_warning = result.get('warning')
        g.license_info = result.get('license')

        if not result['valid']:
            error = result.get('error', 'UNKNOWN_ERROR')

            if current_user.role == 'admin':
                if error == 'LICENSE_NOT_FOUND':
                    flash('License not found. Please activate.', 'warning')
                    return redirect(url_for('license.activate'))
                elif error == 'LICENSE_EXPIRED':
                    flash('License has expired.', 'error')
                    return redirect(url_for('license.expired'))
                else:
                    flash(f'License error: {error}', 'error')
                    return redirect(url_for('license.error'))
            else:
                flash('System license issue. Please contact administrator.', 'error')
                return redirect(url_for('license.error'))

        return None
