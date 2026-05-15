# app/bootstrap/security_headers.py
"""HTTP security headers with nonce-based CSP."""

import secrets

from flask import g


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
        # X-XSS-Protection нь deprecated (Chrome 78+, Edge 17+). Modern browser-д
        # CSP-ээр орлуулагдсан. MDN: огт тавихгүй байх нь зөв. 2026-04-22 хасав.
        response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'

        nonce = getattr(g, "csp_nonce", "")
        # CSP3 split-architecture:
        #   style-src-elem  → <style nonce> + external stylesheets (strict, nonce-only)
        #   style-src-attr  → runtime element.style mutations (htmx, AG Grid, Bootstrap
        #                     modal positioning, Tabulator). Inline зөвшөөрсөн.
        # Sprint 1.1c-аар template-ээс бүх inline `style=""` устгасан; 3rd party
        # libs runtime DOM-д style тохируулах нь хэвийн ажиллагаа.
        #
        # TODO (Sprint 1.1b): 277 inline event handler (`onclick=""`) → external JS.
        # TODO (Sprint 1.1d): Alpine.js CDN build `new Function()` ашигладаг тул
        # 'unsafe-eval' шаардлагатай. Alpine CSP build-руу шилжих.
        csp = (
            "default-src 'self'; "
            # Scripts:
            #   script-src      — eval / new Function() execution (Alpine.js CDN)
            #   script-src-elem — <script> блок (strict, nonce-той)
            #   script-src-attr — inline event handler (HTML attr) — 'none' (бүгд external)
            # 'unsafe-eval'-ийг Sprint 1.1d-аар Alpine CSP build руу шилжвэл устгана.
            f"script-src 'self' 'nonce-{nonce}' 'unsafe-eval' "
            "https://cdn.jsdelivr.net https://unpkg.com; "
            f"script-src-elem 'self' 'nonce-{nonce}' "
            "https://cdn.jsdelivr.net https://unpkg.com; "
            "script-src-attr 'none'; "
            # Stylesheets: зөвхөн nonce-той <style> + same-origin/CDN external
            f"style-src-elem 'self' 'nonce-{nonce}' "
            "https://cdn.jsdelivr.net https://unpkg.com https://fonts.googleapis.com; "
            # Runtime style mutations (JS-set element.style) — 3rd party libs хэрэгтэй
            "style-src-attr 'unsafe-inline'; "
            "font-src 'self' data: https://fonts.gstatic.com https://cdn.jsdelivr.net https://unpkg.com; "
            "img-src 'self' data: blob:; "
            "connect-src 'self' ws: wss: https://cdn.jsdelivr.net; "
            "frame-ancestors 'self'; "
            "base-uri 'self'; "
            "form-action 'self';"
        )
        response.headers['Content-Security-Policy'] = csp

        response.headers['Permissions-Policy'] = 'microphone=(), camera=(), geolocation=()'
        response.headers['X-Permitted-Cross-Domain-Policies'] = 'none'

        if not app.debug:
            response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'

        return response
