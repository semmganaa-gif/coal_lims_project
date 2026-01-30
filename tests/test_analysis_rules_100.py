# -*- coding: utf-8 -*-
"""
analysis_rules.py модулийн 100% coverage тестүүд
"""
import pytest


class TestAnalysisRulesImport:
    """Модуль импорт тест"""

    def test_import_module(self):
        from app.utils import analysis_rules
        assert analysis_rules is not None

    def test_import_constants(self):
        from app.utils.analysis_rules import SOFT_LIMITS, SOFT_MAX_LIMITS, SOFT_MIN_LIMITS
        assert isinstance(SOFT_LIMITS, dict)
        assert isinstance(SOFT_MAX_LIMITS, dict)
        assert isinstance(SOFT_MIN_LIMITS, dict)

    def test_import_function(self):
        from app.utils.analysis_rules import determine_result_status
        assert determine_result_status is not None
        assert callable(determine_result_status)


class TestSoftLimits:
    """SOFT_LIMITS тогтмолуудын тест"""

    def test_moisture_limits(self):
        from app.utils.analysis_rules import SOFT_LIMITS
        assert 'MT' in SOFT_LIMITS
        assert 'Mad' in SOFT_LIMITS
        assert SOFT_LIMITS['MT'] == 35.0

    def test_ash_limits(self):
        from app.utils.analysis_rules import SOFT_LIMITS
        assert 'Aad' in SOFT_LIMITS
        assert 'A' in SOFT_LIMITS

    def test_volatile_limits(self):
        from app.utils.analysis_rules import SOFT_LIMITS
        assert 'Vad' in SOFT_LIMITS
        assert 'Vdaf' in SOFT_LIMITS

    def test_sulfur_limits(self):
        from app.utils.analysis_rules import SOFT_LIMITS
        assert 'TS' in SOFT_LIMITS
        assert 'St,ad' in SOFT_LIMITS

    def test_min_limits(self):
        from app.utils.analysis_rules import SOFT_MIN_LIMITS
        assert 'CV' in SOFT_MIN_LIMITS
        assert 'CSR' in SOFT_MIN_LIMITS
        assert 'Mad' in SOFT_MIN_LIMITS


class TestDetermineResultStatus:
    """determine_result_status функцийн тест"""

    def test_approved_default(self):
        from app.utils.analysis_rules import determine_result_status
        status, comment = determine_result_status('Mad', 5.0)
        assert status == "approved"
        assert comment is None

    def test_tolerance_exceeded(self):
        from app.utils.analysis_rules import determine_result_status
        raw_data = {"t_exceeded": True}
        status, comment = determine_result_status('Mad', 5.0, raw_data=raw_data)
        assert status == "pending_review"
        assert "Tolerance" in comment

    def test_tolerance_not_exceeded(self):
        from app.utils.analysis_rules import determine_result_status
        raw_data = {"t_exceeded": False}
        status, comment = determine_result_status('Mad', 5.0, raw_data=raw_data)
        assert status == "approved"


class TestControlSampleCheck:
    """Control sample шалгалтын тест"""

    def test_control_2sd_rejection(self):
        """2SD-ээс их -> rejected"""
        from app.utils.analysis_rules import determine_result_status
        control_targets = {"mean": 10.0, "sd": 1.0}
        # value = 13 -> diff = 3 > 2*1 = 2
        status, comment = determine_result_status('Mad', 13.0, control_targets=control_targets)
        assert status == "rejected"
        assert "2SD" in comment

    def test_control_1sd_warning(self):
        """1SD < diff < 2SD -> pending_review"""
        from app.utils.analysis_rules import determine_result_status
        control_targets = {"mean": 10.0, "sd": 1.0}
        # value = 11.5 -> diff = 1.5, 1 < 1.5 < 2
        status, comment = determine_result_status('Mad', 11.5, control_targets=control_targets)
        assert status == "pending_review"
        assert "1SD" in comment

    def test_control_pass(self):
        """diff < 1SD -> approved"""
        from app.utils.analysis_rules import determine_result_status
        control_targets = {"mean": 10.0, "sd": 1.0}
        # value = 10.5 -> diff = 0.5 < 1
        status, comment = determine_result_status('Mad', 10.5, control_targets=control_targets)
        assert status == "approved"
        assert "Pass" in comment

    def test_control_no_mean(self):
        """Mean байхгүй -> default logic"""
        from app.utils.analysis_rules import determine_result_status
        control_targets = {"sd": 1.0}
        status, comment = determine_result_status('Mad', 5.0, control_targets=control_targets)
        assert status == "approved"

    def test_control_no_sd(self):
        """SD байхгүй -> default logic"""
        from app.utils.analysis_rules import determine_result_status
        control_targets = {"mean": 10.0}
        status, comment = determine_result_status('Mad', 5.0, control_targets=control_targets)
        assert status == "approved"


class TestGiRules:
    """Gi (Gray-King) дүрмийн тест"""

    def test_gi_low_avg_rejection(self):
        from app.utils.analysis_rules import determine_result_status
        raw_data = {"is_low_avg": True}
        status, comment = determine_result_status('Gi', 50, raw_data=raw_data)
        assert status == "rejected"
        assert "GI_RETEST" in comment

    def test_gi_normal(self):
        from app.utils.analysis_rules import determine_result_status
        raw_data = {"is_low_avg": False}
        status, comment = determine_result_status('Gi', 50, raw_data=raw_data)
        assert status == "approved"


class TestCsrRules:
    """CSR дүрмийн тест"""

    def test_csr_too_low(self):
        from app.utils.analysis_rules import determine_result_status
        status, comment = determine_result_status('CSR', 15.0)
        assert status == "pending_review"
        assert "CSR" in comment

    def test_csr_normal(self):
        from app.utils.analysis_rules import determine_result_status
        status, comment = determine_result_status('CSR', 50.0)
        assert status == "approved"


class TestCvRules:
    """CV дүрмийн тест"""

    def test_cv_too_low(self):
        from app.utils.analysis_rules import determine_result_status
        status, comment = determine_result_status('CV', 1500)
        assert status == "pending_review"
        assert "Илчлэг" in comment

    def test_qgr_ad_too_low(self):
        from app.utils.analysis_rules import determine_result_status
        status, comment = determine_result_status('Qgr,ad', 1000)
        assert status == "pending_review"

    def test_qnet_ar_too_low(self):
        from app.utils.analysis_rules import determine_result_status
        status, comment = determine_result_status('Qnet,ar', 1800)
        assert status == "pending_review"

    def test_cv_normal(self):
        from app.utils.analysis_rules import determine_result_status
        status, comment = determine_result_status('CV', 6000)
        assert status == "approved"


class TestSoftMaxLimits:
    """Soft max limit тест"""

    def test_mt_exceeded(self):
        from app.utils.analysis_rules import determine_result_status
        status, comment = determine_result_status('MT', 40.0)  # > 35
        assert status == "pending_review"
        assert "Soft Limit" in comment

    def test_mad_exceeded(self):
        from app.utils.analysis_rules import determine_result_status
        status, comment = determine_result_status('Mad', 20.0)  # > 15
        assert status == "pending_review"

    def test_aad_exceeded(self):
        from app.utils.analysis_rules import determine_result_status
        status, comment = determine_result_status('Aad', 95.0)  # > 90
        assert status == "pending_review"

    def test_vdaf_exceeded(self):
        from app.utils.analysis_rules import determine_result_status
        status, comment = determine_result_status('Vdaf', 98.0)  # > 95
        assert status == "pending_review"

    def test_ts_exceeded(self):
        from app.utils.analysis_rules import determine_result_status
        status, comment = determine_result_status('TS', 25.0)  # > 20
        assert status == "pending_review"


class TestSoftMinLimits:
    """Soft min limit тест"""

    def test_cv_below_min(self):
        from app.utils.analysis_rules import determine_result_status, SOFT_MIN_LIMITS
        # CV min limit-ээс бага бол
        if 'CV' in SOFT_MIN_LIMITS:
            min_limit = SOFT_MIN_LIMITS['CV']
            status, comment = determine_result_status('CV', min_limit - 100)
            assert status == "pending_review"

    def test_csr_below_min(self):
        from app.utils.analysis_rules import determine_result_status
        # CSR < 20 (min limit)
        status, comment = determine_result_status('CSR', 15.0)
        assert status == "pending_review"

    def test_mad_below_min(self):
        from app.utils.analysis_rules import determine_result_status, SOFT_MIN_LIMITS
        if 'Mad' in SOFT_MIN_LIMITS:
            min_limit = SOFT_MIN_LIMITS['Mad']
            status, comment = determine_result_status('Mad', min_limit - 0.1)
            assert status == "pending_review"


class TestNoneValues:
    """None утгуудын тест"""

    def test_none_value(self):
        from app.utils.analysis_rules import determine_result_status
        status, comment = determine_result_status('MT', None)
        assert status == "approved"

    def test_none_raw_data(self):
        from app.utils.analysis_rules import determine_result_status
        status, comment = determine_result_status('MT', 10.0, raw_data=None)
        assert status == "approved"

    def test_none_control_targets(self):
        from app.utils.analysis_rules import determine_result_status
        status, comment = determine_result_status('MT', 10.0, control_targets=None)
        assert status == "approved"
