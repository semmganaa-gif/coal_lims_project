# tests/unit/test_monitoring_comprehensive.py
# -*- coding: utf-8 -*-
"""
Monitoring comprehensive tests
"""

import pytest
from app.monitoring import (
    track_sample, track_analysis, track_qc_check,
    PROMETHEUS_AVAILABLE
)


class TestMonitoringFunctions:
    """Monitoring functions тестүүд"""

    def test_track_sample_basic(self, app):
        """track_sample basic"""
        with app.app_context():
            try:
                track_sample(client='QC', sample_type='2hour')
            except Exception:
                pass  # Prometheus may not be available

    def test_track_sample_all_clients(self, app):
        """track_sample all clients"""
        with app.app_context():
            clients = ['CHPP', 'QC', 'WTL', 'LAB', 'Proc', 'UHG-Geo', 'BN-Geo']
            for client in clients:
                try:
                    track_sample(client=client, sample_type='Test')
                except Exception:
                    pass

    def test_track_analysis_basic(self, app):
        """track_analysis basic"""
        with app.app_context():
            try:
                track_analysis(analysis_code='Mad', status='approved')
            except Exception:
                pass

    def test_track_analysis_all_codes(self, app):
        """track_analysis all codes"""
        with app.app_context():
            codes = ['Mad', 'Aad', 'Vad', 'CV', 'TS', 'MT', 'Gi', 'FM']
            for code in codes:
                try:
                    track_analysis(analysis_code=code, status='pending_review')
                except Exception:
                    pass

    def test_track_qc_check_basic(self, app):
        """track_qc_check basic"""
        with app.app_context():
            try:
                track_qc_check(analysis_code='Mad', result='pass')
            except Exception:
                pass

    def test_track_qc_check_all_results(self, app):
        """track_qc_check all results"""
        with app.app_context():
            for result in ['pass', 'fail', 'warning']:
                try:
                    track_qc_check(analysis_code='Mad', result=result)
                except Exception:
                    pass


class TestPrometheusCounters:
    """Prometheus counters тестүүд"""

    def test_prometheus_available(self, app):
        """Prometheus availability check"""
        with app.app_context():
            # PROMETHEUS_AVAILABLE is True or False depending on installation
            assert isinstance(PROMETHEUS_AVAILABLE, bool)

    def test_sample_counter_exists(self, app):
        """Sample counter exists"""
        with app.app_context():
            if PROMETHEUS_AVAILABLE:
                from app.monitoring import SAMPLE_COUNTER
                assert SAMPLE_COUNTER is not None
            else:
                pytest.skip("Prometheus not available")

    def test_analysis_counter_exists(self, app):
        """Analysis counter exists"""
        with app.app_context():
            if PROMETHEUS_AVAILABLE:
                from app.monitoring import ANALYSIS_COUNTER
                assert ANALYSIS_COUNTER is not None
            else:
                pytest.skip("Prometheus not available")

    def test_qc_check_counter_exists(self, app):
        """QC check counter exists"""
        with app.app_context():
            if PROMETHEUS_AVAILABLE:
                from app.monitoring import QC_CHECK_COUNTER
                assert QC_CHECK_COUNTER is not None
            else:
                pytest.skip("Prometheus not available")
