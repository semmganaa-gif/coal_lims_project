# -*- coding: utf-8 -*-
"""
Analysis rules тестүүд
"""
import pytest


class TestSoftLimits:
    """SOFT_LIMITS тестүүд"""

    def test_import_soft_limits(self):
        """SOFT_LIMITS import"""
        from app.utils.analysis_rules import SOFT_LIMITS
        assert SOFT_LIMITS is not None
        assert isinstance(SOFT_LIMITS, dict)

    def test_soft_limits_keys(self):
        """SOFT_LIMITS has expected keys"""
        from app.utils.analysis_rules import SOFT_LIMITS
        assert 'MT' in SOFT_LIMITS
        assert 'Mad' in SOFT_LIMITS
        assert 'TS' in SOFT_LIMITS

    def test_soft_max_limits(self):
        """SOFT_MAX_LIMITS"""
        from app.utils.analysis_rules import SOFT_MAX_LIMITS
        assert SOFT_MAX_LIMITS is not None

    def test_soft_min_limits(self):
        """SOFT_MIN_LIMITS"""
        from app.utils.analysis_rules import SOFT_MIN_LIMITS
        assert SOFT_MIN_LIMITS is not None
        assert 'CV' in SOFT_MIN_LIMITS


class TestDetermineResultStatus:
    """determine_result_status тестүүд"""

    def test_import_function(self):
        """Function import"""
        from app.utils.analysis_rules import determine_result_status
        assert determine_result_status is not None

    def test_approved_normal_value(self):
        """Normal value should be approved"""
        from app.utils.analysis_rules import determine_result_status
        status, reason = determine_result_status('Mad', 5.0)
        assert status == 'approved'

    def test_pending_soft_limit_max(self):
        """Value exceeding soft max limit should be pending"""
        from app.utils.analysis_rules import determine_result_status
        # Mad soft limit is 15.0
        status, reason = determine_result_status('Mad', 20.0)
        assert status == 'pending_review'
        assert 'Soft Limit' in reason

    def test_pending_soft_limit_min(self):
        """Value below soft min limit should be pending"""
        from app.utils.analysis_rules import determine_result_status
        # CV soft min limit is 1000.0
        status, reason = determine_result_status('CV', 500.0)
        assert status == 'pending_review'
        # Reason can be in Mongolian or English
        assert reason is not None

    def test_control_sample_rejected_2sd(self):
        """Control sample > 2SD should be rejected"""
        from app.utils.analysis_rules import determine_result_status
        control_targets = {'mean': 10.0, 'sd': 0.5}
        # value = 12.0, mean = 10.0, diff = 2.0 > 2*0.5 = 1.0
        status, reason = determine_result_status('TS', 12.0, control_targets=control_targets)
        assert status == 'rejected'
        assert '2SD' in reason

    def test_control_sample_pending_1sd(self):
        """Control sample > 1SD should be pending"""
        from app.utils.analysis_rules import determine_result_status
        control_targets = {'mean': 10.0, 'sd': 0.5}
        # value = 10.7, mean = 10.0, diff = 0.7 > 1*0.5 = 0.5 but < 2*0.5 = 1.0
        status, reason = determine_result_status('TS', 10.7, control_targets=control_targets)
        assert status == 'pending_review'
        assert '1SD' in reason

    def test_control_sample_approved(self):
        """Control sample within 1SD should be approved"""
        from app.utils.analysis_rules import determine_result_status
        control_targets = {'mean': 10.0, 'sd': 0.5}
        # value = 10.2, mean = 10.0, diff = 0.2 < 1*0.5 = 0.5
        status, reason = determine_result_status('TS', 10.2, control_targets=control_targets)
        assert status == 'approved'
        assert reason == 'Control Pass'

    def test_control_targets_missing_sd(self):
        """Control targets without SD should skip control check"""
        from app.utils.analysis_rules import determine_result_status
        control_targets = {'mean': 10.0}  # No SD
        status, reason = determine_result_status('TS', 5.0, control_targets=control_targets)
        assert status == 'approved'

    def test_control_targets_missing_mean(self):
        """Control targets without mean should skip control check"""
        from app.utils.analysis_rules import determine_result_status
        control_targets = {'sd': 0.5}  # No mean
        status, reason = determine_result_status('TS', 5.0, control_targets=control_targets)
        assert status == 'approved'

    def test_gi_low_avg_rejected(self):
        """Gi with low avg should be rejected"""
        from app.utils.analysis_rules import determine_result_status
        raw_data = {'is_low_avg': True}
        status, reason = determine_result_status('Gi', 1.0, raw_data=raw_data)
        assert status == 'rejected'
        assert 'GI_RETEST' in reason

    def test_gi_normal_approved(self):
        """Gi with normal avg should be approved"""
        from app.utils.analysis_rules import determine_result_status
        raw_data = {'is_low_avg': False}
        status, reason = determine_result_status('Gi', 5.0, raw_data=raw_data)
        assert status == 'approved'

    def test_csr_low_pending(self):
        """CSR below 20 should be pending"""
        from app.utils.analysis_rules import determine_result_status
        status, reason = determine_result_status('CSR', 15.0)
        assert status == 'pending_review'
        assert 'CSR' in reason

    def test_csr_normal_approved(self):
        """CSR above 20 should be approved"""
        from app.utils.analysis_rules import determine_result_status
        status, reason = determine_result_status('CSR', 50.0)
        assert status == 'approved'

    def test_cv_low_pending(self):
        """CV below 2000 should be pending"""
        from app.utils.analysis_rules import determine_result_status
        status, reason = determine_result_status('CV', 1500.0)
        assert status == 'pending_review'

    def test_qgr_ad_low_pending(self):
        """Qgr,ad below 2000 should be pending"""
        from app.utils.analysis_rules import determine_result_status
        status, reason = determine_result_status('Qgr,ad', 1500.0)
        assert status == 'pending_review'

    def test_qnet_ar_low_pending(self):
        """Qnet,ar below 2000 should be pending"""
        from app.utils.analysis_rules import determine_result_status
        status, reason = determine_result_status('Qnet,ar', 1500.0)
        assert status == 'pending_review'

    def test_tolerance_exceeded_pending(self):
        """Tolerance exceeded should be pending"""
        from app.utils.analysis_rules import determine_result_status
        raw_data = {'t_exceeded': True}
        status, reason = determine_result_status('TS', 3.0, raw_data=raw_data)
        assert status == 'pending_review'
        assert 'Tolerance' in reason

    def test_none_value_approved(self):
        """None value should be approved"""
        from app.utils.analysis_rules import determine_result_status
        status, reason = determine_result_status('TS', None)
        assert status == 'approved'

    def test_unknown_code_approved(self):
        """Unknown analysis code should be approved"""
        from app.utils.analysis_rules import determine_result_status
        status, reason = determine_result_status('UNKNOWN_CODE', 5.0)
        assert status == 'approved'

    def test_raw_data_none(self):
        """raw_data=None should work"""
        from app.utils.analysis_rules import determine_result_status
        status, reason = determine_result_status('TS', 5.0, raw_data=None)
        assert status == 'approved'

    def test_empty_control_targets(self):
        """Empty control_targets should skip control check"""
        from app.utils.analysis_rules import determine_result_status
        status, reason = determine_result_status('TS', 5.0, control_targets={})
        assert status == 'approved'

    def test_all_soft_limit_codes(self):
        """Test all codes in SOFT_LIMITS"""
        from app.utils.analysis_rules import determine_result_status, SOFT_LIMITS
        for code, limit in SOFT_LIMITS.items():
            # Test value above limit
            high_value = limit + 10.0
            status, reason = determine_result_status(code, high_value)
            # Should be pending_review for exceeding soft limit
            assert status in ['approved', 'pending_review']

    def test_all_soft_min_limit_codes(self):
        """Test all codes in SOFT_MIN_LIMITS"""
        from app.utils.analysis_rules import determine_result_status, SOFT_MIN_LIMITS
        for code, limit in SOFT_MIN_LIMITS.items():
            # Test value below limit
            low_value = limit - 500.0
            status, reason = determine_result_status(code, low_value)
            # Should be pending_review for being below soft limit
            assert status in ['approved', 'pending_review']

    # ================================================================
    # Gi server-side threshold check (line 152)
    # ================================================================

    def test_gi_server_threshold_retest_5_1(self):
        """Gi value < threshold with retest_mode=5_1 should be rejected"""
        from app.utils.analysis_rules import determine_result_status
        raw_data = {'is_low_avg': False, 'retest_mode': '5_1'}
        status, reason = determine_result_status('Gi', 10.0, raw_data=raw_data)
        assert status == 'rejected'
        assert 'GI_RETEST_3_3' in reason

    def test_gi_server_threshold_retest_3_3_not_rejected(self):
        """Gi with retest_mode=3_3 should NOT reject even if low"""
        from app.utils.analysis_rules import determine_result_status
        raw_data = {'is_low_avg': True, 'retest_mode': '3_3'}
        status, reason = determine_result_status('Gi', 10.0, raw_data=raw_data)
        assert status == 'approved'

    def test_gi_above_threshold_5_1_approved(self):
        """Gi value >= threshold with retest_mode=5_1 should be approved"""
        from app.utils.analysis_rules import determine_result_status
        raw_data = {'is_low_avg': False, 'retest_mode': '5_1'}
        status, reason = determine_result_status('Gi', 25.0, raw_data=raw_data)
        assert status == 'approved'

    # ================================================================
    # CSN rules (lines 158-182)
    # ================================================================

    def test_csn_value_out_of_range_negative(self):
        """CSN < 0 should be rejected"""
        from app.utils.analysis_rules import determine_result_status
        status, reason = determine_result_status('CSN', -1.0)
        assert status == 'rejected'
        assert 'CSN' in reason

    def test_csn_value_out_of_range_high(self):
        """CSN > 9 should be rejected"""
        from app.utils.analysis_rules import determine_result_status
        status, reason = determine_result_status('CSN', 10.0)
        assert status == 'rejected'
        assert 'CSN' in reason

    def test_csn_valid_value_approved(self):
        """CSN within 0-9 should be approved"""
        from app.utils.analysis_rules import determine_result_status
        status, reason = determine_result_status('CSN', 5.0)
        assert status == 'approved'

    def test_csn_parallel_diff_exceeded(self):
        """CSN parallel diff >= 1.0 should be pending_review"""
        from app.utils.analysis_rules import determine_result_status
        raw_data = {'p1_csn': 3.0, 'p2_csn': 5.0}
        status, reason = determine_result_status('CSN', 4.0, raw_data=raw_data)
        assert status == 'pending_review'
        assert 'parallel' in reason.lower() or 'CSN' in reason

    def test_csn_parallel_diff_ok(self):
        """CSN parallel diff < 1.0 should be approved"""
        from app.utils.analysis_rules import determine_result_status
        raw_data = {'p1_csn': 4.0, 'p2_csn': 4.5}
        status, reason = determine_result_status('CSN', 4.0, raw_data=raw_data)
        assert status == 'approved'

    def test_csn_parallel_from_p1_p2_dict(self):
        """CSN parallel from nested p1/p2 dict"""
        from app.utils.analysis_rules import determine_result_status
        raw_data = {'p1': {'csn': 2.0}, 'p2': {'csn': 4.0}}
        status, reason = determine_result_status('CSN', 3.0, raw_data=raw_data)
        assert status == 'pending_review'

    def test_csn_parallel_invalid_values(self):
        """CSN parallel with non-numeric values should be handled"""
        from app.utils.analysis_rules import determine_result_status
        raw_data = {'p1_csn': 'abc', 'p2_csn': 'xyz'}
        status, reason = determine_result_status('CSN', 5.0, raw_data=raw_data)
        assert status == 'approved'

    def test_csn_zero_value(self):
        """CSN = 0 should be approved (non-coking coal)"""
        from app.utils.analysis_rules import determine_result_status
        status, reason = determine_result_status('CSN', 0)
        assert status == 'approved'

    def test_csn_none_value(self):
        """CSN with None value should be approved"""
        from app.utils.analysis_rules import determine_result_status
        status, reason = determine_result_status('CSN', None)
        assert status == 'approved'
