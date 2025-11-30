# app/monitoring.py
# -*- coding: utf-8 -*-
"""
Performance monitoring тохиргоо

Request хурд, алдаа, metrics бүртгэнэ
"""

from flask import request, g
import time
import logging


def setup_monitoring(app):
    """
    Performance monitoring тохируулах

    - Request хугацаа хэмжих
    - Удаан request log-д бичих
    - Response header-д хугацаа нэмэх
    """

    @app.before_request
    def before_request():
        """Request эхлэхийн өмнө хугацааг тэмдэглэх"""
        g.start_time = time.time()
        g.request_path = request.path
        g.request_method = request.method

    @app.after_request
    def after_request(response):
        """Request дууссаны дараа metrics бүртгэх"""
        if hasattr(g, 'start_time'):
            # Гүйцэтгэх хугацаа тооцоолох
            elapsed = time.time() - g.start_time

            # Response header-д хугацааг нэмэх
            response.headers['X-Response-Time'] = f"{elapsed:.4f}s"

            # Удаан request-үүдийг log-д бичих
            if elapsed > 1.0:  # 1 секундээс урт
                app.logger.warning(
                    f"Slow request: {g.request_method} {g.request_path} "
                    f"took {elapsed:.2f}s "
                    f"from {request.remote_addr}"
                )

            # Info level log (бүх request)
            app.logger.info(
                f"{g.request_method} {g.request_path} "
                f"{response.status_code} {elapsed:.4f}s"
            )

            # Маш удаан request-үүдийг тусгай анхааруулах
            if elapsed > 5.0:  # 5 секундээс урт
                app.logger.error(
                    f"VERY SLOW REQUEST: {g.request_method} {g.request_path} "
                    f"took {elapsed:.2f}s - Investigate immediately!"
                )

        return response

    @app.teardown_request
    def teardown_request(exception=None):
        """Request дууссаны дараа цэвэрлэх"""
        if exception:
            # Exception гарсан тохиолдолд log-д бичих
            app.logger.error(
                f"Request error: {g.request_method if hasattr(g, 'request_method') else 'UNKNOWN'} "
                f"{g.request_path if hasattr(g, 'request_path') else 'UNKNOWN'} - "
                f"{str(exception)}",
                exc_info=True
            )

    # Health check endpoint
    @app.route('/health')
    def health_check():
        """
        Health check endpoint

        Docker, load balancer-т зориулсан
        """
        from flask import jsonify

        try:
            # Database холболт шалгах
            from app import db
            db.session.execute(db.text('SELECT 1'))

            return jsonify({
                'status': 'healthy',
                'database': 'connected'
            }), 200

        except Exception as e:
            app.logger.error(f"Health check failed: {e}")
            return jsonify({
                'status': 'unhealthy',
                'error': str(e)
            }), 500

    app.logger.info("Performance monitoring initialized")

    return app


def get_performance_stats():
    """
    Performance statistics авах

    Logs-оос удаан request-үүдийг задлан авч,
    статистик гаргана.
    """
    # TODO: Logs файлаас мэдээлэл унших,
    # эсвэл бусад monitoring tool ашиглах
    pass
