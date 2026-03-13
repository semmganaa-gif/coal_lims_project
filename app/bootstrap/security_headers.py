# app/bootstrap/security_headers.py
"""HTTP security headers with nonce-based CSP."""

import secrets

from flask import g, request


def init_security_headers(app):
    """Add security headers to all responses with per-request CSP nonce."""

    @app.before_request
    def generate_csp_nonce():
        """Generate a unique nonce for each request."""
        g.csp_nonce = secrets.token_urlsafe(32)

    @app.context_processor
    def inject_csp_nonce():
        """Make csp_nonce available in all templates."""
        return {"csp_nonce": getattr(g, "csp_nonce", "")}

    @app.after_request
    def add_security_headers(response):
        response.headers['X-Frame-Options'] = 'SAMEORIGIN'
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-XSS-Protection'] = '1; mode=block'
        response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'

        nonce = getattr(g, "csp_nonce", "")
        csp = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://cdn.jsdelivr.net https://unpkg.com; "
            "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://unpkg.com https://fonts.googleapis.com; "
            "font-src 'self' data: https://fonts.gstatic.com https://cdn.jsdelivr.net https://unpkg.com; "
            "img-src 'self' data: blob:; "
            "connect-src 'self' ws: wss: https://cdn.jsdelivr.net; "
            "frame-ancestors 'self';"
        )
        response.headers['Content-Security-Policy'] = csp

        response.headers['Permissions-Policy'] = 'microphone=(), camera=(), geolocation=()'
        response.headers['X-Permitted-Cross-Domain-Policies'] = 'none'

        if not app.debug:
            response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'

        return response
