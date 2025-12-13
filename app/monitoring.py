# app/monitoring.py
# -*- coding: utf-8 -*-
"""
Performance monitoring тохиргоо

Request хурд, алдаа, metrics бүртгэнэ.
Prometheus/Grafana интеграцтай.
"""

from flask import request, g
import time
import logging

# Prometheus metrics
try:
    from prometheus_flask_exporter import PrometheusMetrics
    from prometheus_client import Counter, Histogram, Gauge, Info
    PROMETHEUS_AVAILABLE = True
except ImportError:
    PROMETHEUS_AVAILABLE = False

# Custom metrics (Prometheus байвал)
if PROMETHEUS_AVAILABLE:
    # Шинжилгээний тоолуур
    ANALYSIS_COUNTER = Counter(
        'lims_analysis_total',
        'Total number of analyses performed',
        ['analysis_type', 'status']
    )

    # Дээжийн тоолуур
    SAMPLE_COUNTER = Counter(
        'lims_samples_total',
        'Total number of samples registered',
        ['client', 'sample_type']
    )

    # Хэрэглэгчийн идэвхи
    ACTIVE_USERS = Gauge(
        'lims_active_users',
        'Number of currently active users'
    )

    # Database query хугацаа
    DB_QUERY_DURATION = Histogram(
        'lims_db_query_duration_seconds',
        'Database query duration in seconds',
        ['query_type'],
        buckets=[0.01, 0.05, 0.1, 0.5, 1.0, 2.0, 5.0]
    )

    # QC check үр дүн
    QC_CHECK_COUNTER = Counter(
        'lims_qc_checks_total',
        'Total QC checks performed',
        ['check_type', 'result']  # result: pass, fail, warning
    )

    # App мэдээлэл
    APP_INFO = Info('lims_app', 'LIMS application information')


def setup_monitoring(app):
    """
    Performance monitoring тохируулах

    - Request хугацаа хэмжих
    - Удаан request log-д бичих
    - Response header-д хугацаа нэмэх
    - Prometheus metrics (/metrics endpoint)
    """

    # Prometheus metrics тохируулах
    metrics = None
    if PROMETHEUS_AVAILABLE:
        metrics = PrometheusMetrics(app, path='/metrics')

        # App мэдээлэл тохируулах
        APP_INFO.info({
            'version': app.config.get('VERSION', '1.0.0'),
            'environment': app.config.get('ENV', 'production'),
            'name': 'Coal LIMS'
        })

        # Default metrics-ийг бүртгэх
        metrics.info('lims_app_info', 'Application info', version='1.0.0')

        app.logger.info("Prometheus metrics enabled at /metrics")

    # metrics объектыг app-д хадгалах
    app.prometheus_metrics = metrics

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

    Prometheus metrics-ээс статистик гаргана.

    Returns:
        dict: Performance statistics
    """
    if not PROMETHEUS_AVAILABLE:
        return {
            "status": "prometheus_unavailable",
            "message": "Install prometheus-flask-exporter for metrics",
            "slow_requests": [],
            "avg_response_time": None,
            "total_requests": None
        }

    try:
        from prometheus_client import REGISTRY

        # Prometheus registry-ээс metrics авах
        metrics_data = {}
        for metric in REGISTRY.collect():
            for sample in metric.samples:
                if sample.name.startswith('lims_'):
                    metrics_data[sample.name] = sample.value

        return {
            "status": "ok",
            "prometheus_enabled": True,
            "metrics_endpoint": "/metrics",
            "custom_metrics": metrics_data,
            "message": "Use /metrics endpoint for Prometheus scraping"
        }

    except Exception as e:
        return {
            "status": "error",
            "message": str(e),
            "prometheus_enabled": PROMETHEUS_AVAILABLE
        }


# =============================================================================
# METRICS HELPER FUNCTIONS
# =============================================================================

def track_analysis(analysis_type: str, status: str = 'completed'):
    """
    Шинжилгээ хийгдсэнийг бүртгэх

    Args:
        analysis_type: Шинжилгээний төрөл (Aad, Mad, Vad, ...)
        status: Статус (completed, failed, pending)
    """
    if PROMETHEUS_AVAILABLE:
        ANALYSIS_COUNTER.labels(analysis_type=analysis_type, status=status).inc()


def track_sample(client: str, sample_type: str):
    """
    Шинэ дээж бүртгэгдсэнийг тэмдэглэх

    Args:
        client: Захиалагч (QC, CHPP, LAB, ...)
        sample_type: Дээжийн төрөл
    """
    if PROMETHEUS_AVAILABLE:
        SAMPLE_COUNTER.labels(client=client or 'unknown', sample_type=sample_type or 'unknown').inc()


def track_active_users(count: int):
    """
    Идэвхтэй хэрэглэгчийн тоог тохируулах

    Args:
        count: Хэрэглэгчийн тоо
    """
    if PROMETHEUS_AVAILABLE:
        ACTIVE_USERS.set(count)


def track_db_query(query_type: str, duration: float):
    """
    Database query хугацааг бүртгэх

    Args:
        query_type: Query төрөл (select, insert, update, delete)
        duration: Хугацаа (секундээр)
    """
    if PROMETHEUS_AVAILABLE:
        DB_QUERY_DURATION.labels(query_type=query_type).observe(duration)


def track_qc_check(check_type: str, result: str):
    """
    QC шалгалтын үр дүнг бүртгэх

    Args:
        check_type: Шалгалтын төрөл (repeatability, westgard, ...)
        result: Үр дүн (pass, fail, warning)
    """
    if PROMETHEUS_AVAILABLE:
        QC_CHECK_COUNTER.labels(check_type=check_type, result=result).inc()


class QueryTimer:
    """
    Database query хугацааг хэмжих context manager

    Usage:
        with QueryTimer('select'):
            results = db.session.query(...).all()
    """

    def __init__(self, query_type: str):
        self.query_type = query_type
        self.start_time = None

    def __enter__(self):
        self.start_time = time.time()
        return self

    def __exit__(self, _exc_type, _exc_val, _exc_tb):
        if self.start_time:
            duration = time.time() - self.start_time
            track_db_query(self.query_type, duration)
        return False
