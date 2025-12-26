# -*- coding: utf-8 -*-
"""
Tests for app/utils/analysis_rules.py
Analysis business rules tests
"""
import pytest


class TestSoftLimits:
    """SOFT_LIMITS tests"""

    def test_soft_limits_exists(self):
        """SOFT_LIMITS dict exists"""
        from app.utils.analysis_rules import SOFT_LIMITS
        assert isinstance(SOFT_LIMITS, dict)
        assert len(SOFT_LIMITS) > 0

    def test_soft_limits_mt(self):
        """MT (moisture) limit"""
        from app.utils.analysis_rules import SOFT_LIMITS
        assert 'MT' in SOFT_LIMITS
        assert SOFT_LIMITS['MT'] == 35.0

    def test_soft_limits_mad(self):
        """Mad limit"""
        from app.utils.analysis_rules import SOFT_LIMITS
        assert 'Mad' in SOFT_LIMITS
        assert SOFT_LIMITS['Mad'] == 15.0

    def test_soft_limits_aad(self):
        """Aad (ash) limit"""
        from app.utils.analysis_rules import SOFT_LIMITS
        assert 'Aad' in SOFT_LIMITS
        assert SOFT_LIMITS['Aad'] == 90.0

    def test_soft_limits_ts(self):
        """TS (sulfur) limit"""
        from app.utils.analysis_rules import SOFT_LIMITS
        assert 'TS' in SOFT_LIMITS
        assert SOFT_LIMITS['TS'] == 20.0

    def test_soft_limits_chlorine(self):
        """Cl limit"""
        from app.utils.analysis_rules import SOFT_LIMITS
        assert 'Cl' in SOFT_LIMITS
        assert SOFT_LIMITS['Cl'] == 600.0

    def test_soft_limits_fluorine(self):
        """F limit"""
        from app.utils.analysis_rules import SOFT_LIMITS
        assert 'F' in SOFT_LIMITS
        assert SOFT_LIMITS['F'] == 500.0


class TestSoftMaxLimits:
    """SOFT_MAX_LIMITS tests"""

    def test_soft_max_limits_exists(self):
        """SOFT_MAX_LIMITS exists"""
        from app.utils.analysis_rules import SOFT_MAX_LIMITS
        assert isinstance(SOFT_MAX_LIMITS, dict)

    def test_soft_max_limits_equals_soft_limits(self):
        """SOFT_MAX_LIMITS is copy of SOFT_LIMITS"""
        from app.utils.analysis_rules import SOFT_LIMITS, SOFT_MAX_LIMITS
        assert SOFT_MAX_LIMITS == SOFT_LIMITS


class TestSoftMinLimits:
    """SOFT_MIN_LIMITS tests"""

    def test_soft_min_limits_exists(self):
        """SOFT_MIN_LIMITS exists"""
        from app.utils.analysis_rules import SOFT_MIN_LIMITS
        assert isinstance(SOFT_MIN_LIMITS, dict)

    def test_soft_min_limits_cv(self):
        """CV min limit"""
        from app.utils.analysis_rules import SOFT_MIN_LIMITS
        assert 'CV' in SOFT_MIN_LIMITS
        assert SOFT_MIN_LIMITS['CV'] == 1000.0

    def test_soft_min_limits_csr(self):
        """CSR min limit"""
        from app.utils.analysis_rules import SOFT_MIN_LIMITS
        assert 'CSR' in SOFT_MIN_LIMITS
        assert SOFT_MIN_LIMITS['CSR'] == 20.0

    def test_soft_min_limits_mad(self):
        """Mad min limit"""
        from app.utils.analysis_rules import SOFT_MIN_LIMITS
        assert 'Mad' in SOFT_MIN_LIMITS
        assert SOFT_MIN_LIMITS['Mad'] == 0.40


class TestDetermineResultStatus:
    """determine_result_status function tests"""

    def test_determine_result_status_import(self):
        """Import function"""
        from app.utils.analysis_rules import determine_result_status
        assert callable(determine_result_status)

    def test_determine_result_status_approved_normal(self):
        """Normal value approved"""
        from app.utils.analysis_rules import determine_result_status

        status, comment = determine_result_status('Mad', 8.5)
        assert status == 'approved'
        assert comment is None

    def test_determine_result_status_soft_limit_exceeded(self):
        """Soft limit exceeded - pending_review"""
        from app.utils.analysis_rules import determine_result_status

        # MT > 35.0
        status, comment = determine_result_status('MT', 40.0)
        assert status == 'pending_review'
        assert 'Soft Limit Exceeded' in comment

    def test_determine_result_status_min_limit_exceeded(self):
        """Min limit exceeded - pending_review"""
        from app.utils.analysis_rules import determine_result_status

        # CV < 1000 - triggers CV special rule first
        status, comment = determine_result_status('CV', 500.0)
        assert status == 'pending_review'
        assert 'Илчлэг' in comment or '500.0' in comment

    def test_determine_result_status_tolerance_exceeded(self):
        """Tolerance exceeded - pending_review"""
        from app.utils.analysis_rules import determine_result_status

        raw_data = {'t_exceeded': True}
        status, comment = determine_result_status('Mad', 8.5, raw_data=raw_data)
        assert status == 'pending_review'
        assert 'Tolerance Exceeded' in comment

    def test_determine_result_status_control_sample_pass(self):
        """Control sample pass"""
        from app.utils.analysis_rules import determine_result_status

        control = {'mean': 10.0, 'sd': 0.5}
        # Value within 1SD: 10.0 +/- 0.5
        status, comment = determine_result_status('Mad', 10.2, control_targets=control)
        assert status == 'approved'
        assert comment == 'Control Pass'

    def test_determine_result_status_control_sample_warning(self):
        """Control sample warning (>1SD)"""
        from app.utils.analysis_rules import determine_result_status

        control = {'mean': 10.0, 'sd': 0.5}
        # Value > 1SD but < 2SD: 10.7 (diff = 0.7)
        status, comment = determine_result_status('Mad', 10.7, control_targets=control)
        assert status == 'pending_review'
        assert 'Control Warning' in comment
        assert '> 1SD' in comment

    def test_determine_result_status_control_sample_fail(self):
        """Control sample fail (>2SD)"""
        from app.utils.analysis_rules import determine_result_status

        control = {'mean': 10.0, 'sd': 0.5}
        # Value > 2SD: 11.5 (diff = 1.5 > 1.0)
        status, comment = determine_result_status('Mad', 11.5, control_targets=control)
        assert status == 'rejected'
        assert 'Control Failure' in comment
        assert '> 2SD' in comment

    def test_determine_result_status_gi_retest(self):
        """Gi retest required"""
        from app.utils.analysis_rules import determine_result_status

        raw_data = {'is_low_avg': True}
        status, comment = determine_result_status('Gi', 5.0, raw_data=raw_data)
        assert status == 'rejected'
        assert comment == 'GI_RETEST_3_3'

    def test_determine_result_status_csr_low(self):
        """CSR too low"""
        from app.utils.analysis_rules import determine_result_status

        status, comment = determine_result_status('CSR', 15.0)
        assert status == 'pending_review'
        assert 'CSR' in comment

    def test_determine_result_status_cv_low(self):
        """CV too low"""
        from app.utils.analysis_rules import determine_result_status

        status, comment = determine_result_status('CV', 1500.0)
        assert status == 'pending_review'
        assert 'Илчлэг' in comment

    def test_determine_result_status_qgr_low(self):
        """Qgr,ad too low"""
        from app.utils.analysis_rules import determine_result_status

        status, comment = determine_result_status('Qgr,ad', 1800.0)
        assert status == 'pending_review'

    def test_determine_result_status_none_value(self):
        """None value"""
        from app.utils.analysis_rules import determine_result_status

        status, comment = determine_result_status('Mad', None)
        assert status == 'approved'

    def test_determine_result_status_unknown_code(self):
        """Unknown analysis code"""
        from app.utils.analysis_rules import determine_result_status

        status, comment = determine_result_status('UNKNOWN', 50.0)
        assert status == 'approved'
        assert comment is None

    def test_determine_result_status_none_raw_data(self):
        """None raw_data defaults to empty dict"""
        from app.utils.analysis_rules import determine_result_status

        status, comment = determine_result_status('Mad', 8.5, raw_data=None)
        assert status == 'approved'

    def test_determine_result_status_control_none_mean(self):
        """Control with None mean"""
        from app.utils.analysis_rules import determine_result_status

        control = {'mean': None, 'sd': 0.5}
        status, comment = determine_result_status('Mad', 8.5, control_targets=control)
        # Falls through to normal checks
        assert status == 'approved'

    def test_determine_result_status_control_none_sd(self):
        """Control with None sd"""
        from app.utils.analysis_rules import determine_result_status

        control = {'mean': 10.0, 'sd': None}
        status, comment = determine_result_status('Mad', 8.5, control_targets=control)
        # Falls through to normal checks
        assert status == 'approved'

    def test_determine_result_status_aad_high(self):
        """Aad high"""
        from app.utils.analysis_rules import determine_result_status

        status, comment = determine_result_status('Aad', 95.0)
        assert status == 'pending_review'
        assert 'Soft Limit Exceeded' in comment

    def test_determine_result_status_vad_high(self):
        """Vad high"""
        from app.utils.analysis_rules import determine_result_status

        status, comment = determine_result_status('Vad', 95.0)
        assert status == 'pending_review'

    def test_determine_result_status_nitrogen_high(self):
        """N (nitrogen) high"""
        from app.utils.analysis_rules import determine_result_status

        status, comment = determine_result_status('N', 5.0)
        assert status == 'pending_review'

    def test_determine_result_status_phosphorus_high(self):
        """P (phosphorus) high"""
        from app.utils.analysis_rules import determine_result_status

        status, comment = determine_result_status('P', 0.5)
        assert status == 'pending_review'

    def test_determine_result_status_trd_high(self):
        """TRD high"""
        from app.utils.analysis_rules import determine_result_status

        status, comment = determine_result_status('TRD', 4.0)
        assert status == 'pending_review'

    def test_determine_result_status_qnet_ar_low(self):
        """Qnet,ar low"""
        from app.utils.analysis_rules import determine_result_status

        status, comment = determine_result_status('Qnet,ar', 1500.0)
        assert status == 'pending_review'

    def test_determine_result_status_returns_tuple(self):
        """Returns tuple of (status, comment)"""
        from app.utils.analysis_rules import determine_result_status

        result = determine_result_status('Mad', 8.5)
        assert isinstance(result, tuple)
        assert len(result) == 2


class TestControlSampleDetailedChecks:
    """Control sample detailed check tests"""

    def test_control_exactly_at_mean(self):
        """Value exactly at mean is approved"""
        from app.utils.analysis_rules import determine_result_status
        control = {'mean': 10.0, 'sd': 1.0}
        status, comment = determine_result_status('MT', 10.0, control_targets=control)
        assert status == 'approved'
        assert 'Control Pass' in comment

    def test_control_below_mean_within_1sd(self):
        """Value below mean but within 1SD"""
        from app.utils.analysis_rules import determine_result_status
        control = {'mean': 10.0, 'sd': 1.0}
        status, comment = determine_result_status('MT', 9.5, control_targets=control)
        assert status == 'approved'

    def test_control_below_mean_between_1sd_2sd(self):
        """Value below mean between 1SD and 2SD"""
        from app.utils.analysis_rules import determine_result_status
        control = {'mean': 10.0, 'sd': 1.0}
        # 8.5 is 1.5 below mean, > 1SD but < 2SD
        status, comment = determine_result_status('MT', 8.5, control_targets=control)
        assert status == 'pending_review'
        assert '> 1SD' in comment

    def test_control_below_mean_beyond_2sd(self):
        """Value below mean beyond 2SD"""
        from app.utils.analysis_rules import determine_result_status
        control = {'mean': 10.0, 'sd': 1.0}
        # 7.5 is 2.5 below mean, > 2SD
        status, comment = determine_result_status('MT', 7.5, control_targets=control)
        assert status == 'rejected'
        assert '> 2SD' in comment

    def test_control_missing_mean_key(self):
        """Control dict missing mean key"""
        from app.utils.analysis_rules import determine_result_status
        control = {'sd': 1.0}
        status, comment = determine_result_status('MT', 10.0, control_targets=control)
        assert status == 'approved'
        assert comment is None

    def test_control_missing_sd_key(self):
        """Control dict missing sd key"""
        from app.utils.analysis_rules import determine_result_status
        control = {'mean': 10.0}
        status, comment = determine_result_status('MT', 10.0, control_targets=control)
        assert status == 'approved'

    def test_control_empty_dict(self):
        """Empty control dict"""
        from app.utils.analysis_rules import determine_result_status
        status, comment = determine_result_status('MT', 10.0, control_targets={})
        assert status == 'approved'

    def test_control_comment_includes_diff(self):
        """Control failure comment includes calculated difference"""
        from app.utils.analysis_rules import determine_result_status
        control = {'mean': 10.0, 'sd': 1.0}
        status, comment = determine_result_status('MT', 13.0, control_targets=control)
        assert 'Diff:' in comment
        assert '3.0' in comment


class TestSoftLimitsAllCodes:
    """Test all analysis codes in SOFT_LIMITS"""

    def test_volatile_v_limit(self):
        """V limit exceeded"""
        from app.utils.analysis_rules import determine_result_status
        status, comment = determine_result_status('V', 95.0)
        assert status == 'pending_review'

    def test_volatile_vdaf_limit(self):
        """Vdaf limit exceeded"""
        from app.utils.analysis_rules import determine_result_status
        status, comment = determine_result_status('Vdaf', 96.0)
        assert status == 'pending_review'

    def test_sulfur_st_ad_limit(self):
        """St,ad limit exceeded"""
        from app.utils.analysis_rules import determine_result_status
        status, comment = determine_result_status('St,ad', 25.0)
        assert status == 'pending_review'

    def test_sulfur_st_d_limit(self):
        """St,d limit exceeded"""
        from app.utils.analysis_rules import determine_result_status
        status, comment = determine_result_status('St,d', 25.0)
        assert status == 'pending_review'

    def test_oxygen_limit(self):
        """O (oxygen) limit exceeded"""
        from app.utils.analysis_rules import determine_result_status
        status, comment = determine_result_status('O', 30.0)
        assert status == 'pending_review'

    def test_phosphorus_ad_limit(self):
        """P,ad limit exceeded"""
        from app.utils.analysis_rules import determine_result_status
        status, comment = determine_result_status('P,ad', 0.30)
        assert status == 'pending_review'

    def test_phosphorus_d_limit(self):
        """P,d limit exceeded"""
        from app.utils.analysis_rules import determine_result_status
        status, comment = determine_result_status('P,d', 0.30)
        assert status == 'pending_review'

    def test_chlorine_ad_limit(self):
        """Cl,ad limit exceeded"""
        from app.utils.analysis_rules import determine_result_status
        status, comment = determine_result_status('Cl,ad', 700.0)
        assert status == 'pending_review'

    def test_chlorine_d_limit(self):
        """Cl,d limit exceeded"""
        from app.utils.analysis_rules import determine_result_status
        status, comment = determine_result_status('Cl,d', 700.0)
        assert status == 'pending_review'

    def test_fluorine_ad_limit(self):
        """F,ad limit exceeded"""
        from app.utils.analysis_rules import determine_result_status
        status, comment = determine_result_status('F,ad', 550.0)
        assert status == 'pending_review'

    def test_fluorine_d_limit(self):
        """F,d limit exceeded"""
        from app.utils.analysis_rules import determine_result_status
        status, comment = determine_result_status('F,d', 550.0)
        assert status == 'pending_review'

    def test_cri_limit(self):
        """CRI limit exceeded"""
        from app.utils.analysis_rules import determine_result_status
        status, comment = determine_result_status('CRI', 65.0)
        assert status == 'pending_review'

    def test_solid_limit(self):
        """SOLID limit exceeded"""
        from app.utils.analysis_rules import determine_result_status
        status, comment = determine_result_status('SOLID', 85.0)
        assert status == 'pending_review'

    def test_fm_limit(self):
        """FM limit exceeded"""
        from app.utils.analysis_rules import determine_result_status
        status, comment = determine_result_status('FM', 65.0)
        assert status == 'pending_review'

    def test_a_limit(self):
        """A (ash alternate) limit exceeded"""
        from app.utils.analysis_rules import determine_result_status
        status, comment = determine_result_status('A', 95.0)
        assert status == 'pending_review'


class TestSoftMinLimitsAllCodes:
    """Test all analysis codes in SOFT_MIN_LIMITS"""

    def test_qgr_ad_min_limit(self):
        """Qgr,ad min limit violated"""
        from app.utils.analysis_rules import determine_result_status
        status, comment = determine_result_status('Qgr,ad', 800.0)
        assert status == 'pending_review'

    def test_qnet_ar_min_limit(self):
        """Qnet,ar min limit violated"""
        from app.utils.analysis_rules import determine_result_status
        status, comment = determine_result_status('Qnet,ar', 900.0)
        assert status == 'pending_review'


class TestGiSpecialCases:
    """Gi (Gray-King) special case tests"""

    def test_gi_normal_value_approved(self):
        """Gi normal value approved"""
        from app.utils.analysis_rules import determine_result_status
        status, comment = determine_result_status('Gi', 5.0)
        assert status == 'approved'

    def test_gi_with_empty_raw_data(self):
        """Gi with empty raw_data"""
        from app.utils.analysis_rules import determine_result_status
        status, comment = determine_result_status('Gi', 5.0, raw_data={})
        assert status == 'approved'

    def test_gi_is_low_avg_false(self):
        """Gi with is_low_avg=False"""
        from app.utils.analysis_rules import determine_result_status
        raw_data = {'is_low_avg': False}
        status, comment = determine_result_status('Gi', 5.0, raw_data=raw_data)
        assert status == 'approved'


class TestCSRSpecialCases:
    """CSR special case tests"""

    def test_csr_exactly_20_approved(self):
        """CSR exactly 20 is approved"""
        from app.utils.analysis_rules import determine_result_status
        status, comment = determine_result_status('CSR', 20.0)
        assert status == 'approved'

    def test_csr_above_20_approved(self):
        """CSR above 20 is approved"""
        from app.utils.analysis_rules import determine_result_status
        status, comment = determine_result_status('CSR', 50.0)
        assert status == 'approved'

    def test_csr_slightly_below_20(self):
        """CSR slightly below 20"""
        from app.utils.analysis_rules import determine_result_status
        status, comment = determine_result_status('CSR', 19.9)
        assert status == 'pending_review'


class TestCVSpecialCases:
    """CV special case tests"""

    def test_cv_exactly_2000_approved(self):
        """CV exactly 2000 is approved"""
        from app.utils.analysis_rules import determine_result_status
        status, comment = determine_result_status('CV', 2000.0)
        assert status == 'approved'

    def test_cv_high_value_approved(self):
        """CV high value is approved"""
        from app.utils.analysis_rules import determine_result_status
        status, comment = determine_result_status('CV', 7000.0)
        assert status == 'approved'


class TestPriorityOrder:
    """Test check priority order"""

    def test_tolerance_before_control(self):
        """Tolerance check runs before control check"""
        from app.utils.analysis_rules import determine_result_status
        raw_data = {'t_exceeded': True}
        control = {'mean': 10.0, 'sd': 1.0}
        status, comment = determine_result_status('MT', 10.0,
                                                   raw_data=raw_data,
                                                   control_targets=control)
        assert 'Tolerance Exceeded' in comment

    def test_control_before_gi_rule(self):
        """Control check runs before Gi special rule"""
        from app.utils.analysis_rules import determine_result_status
        raw_data = {'is_low_avg': True}
        control = {'mean': 5.0, 'sd': 0.1}
        # Value 10.0 is way above control limits
        status, comment = determine_result_status('Gi', 10.0,
                                                   raw_data=raw_data,
                                                   control_targets=control)
        assert 'Control Failure' in comment

    def test_control_pass_then_gi_rule(self):
        """If control passes, Gi rule still applies"""
        from app.utils.analysis_rules import determine_result_status
        raw_data = {'is_low_avg': True}
        # No control targets, so Gi rule applies
        status, comment = determine_result_status('Gi', 5.0, raw_data=raw_data)
        assert status == 'rejected'
        assert 'GI_RETEST_3_3' in comment


class TestEdgeCasesExtended:
    """Extended edge case tests"""

    def test_zero_value_for_cv(self):
        """Zero CV triggers pending"""
        from app.utils.analysis_rules import determine_result_status
        status, comment = determine_result_status('CV', 0.0)
        assert status == 'pending_review'

    def test_negative_value_handled(self):
        """Negative value doesn't crash"""
        from app.utils.analysis_rules import determine_result_status
        status, comment = determine_result_status('MT', -5.0)
        assert status == 'approved'

    def test_very_large_value(self):
        """Very large value triggers soft limit"""
        from app.utils.analysis_rules import determine_result_status
        status, comment = determine_result_status('MT', 1000000.0)
        assert status == 'pending_review'

    def test_at_exact_max_limit_approved(self):
        """Value exactly at max limit is approved"""
        from app.utils.analysis_rules import determine_result_status
        # MT limit is 35.0
        status, comment = determine_result_status('MT', 35.0)
        assert status == 'approved'

    def test_just_above_max_limit(self):
        """Value just above max limit is pending"""
        from app.utils.analysis_rules import determine_result_status
        status, comment = determine_result_status('MT', 35.0001)
        assert status == 'pending_review'

    def test_at_exact_min_limit_approved(self):
        """Value exactly at min limit is approved"""
        from app.utils.analysis_rules import determine_result_status
        # Mad min limit is 0.40
        status, comment = determine_result_status('Mad', 0.40)
        assert status == 'approved'

    def test_just_below_min_limit(self):
        """Value just below min limit is pending"""
        from app.utils.analysis_rules import determine_result_status
        status, comment = determine_result_status('Mad', 0.39)
        assert status == 'pending_review'

    def test_control_zero_sd(self):
        """Control with zero SD - value at mean passes"""
        from app.utils.analysis_rules import determine_result_status
        control = {'mean': 10.0, 'sd': 0.0}
        status, comment = determine_result_status('MT', 10.0, control_targets=control)
        assert status == 'approved'

    def test_mad_has_both_limits(self):
        """Mad has both min (0.40) and max (15.0) limits"""
        from app.utils.analysis_rules import determine_result_status
        # Below min
        status1, _ = determine_result_status('Mad', 0.30)
        assert status1 == 'pending_review'

        # Above max
        status2, _ = determine_result_status('Mad', 16.0)
        assert status2 == 'pending_review'

        # Within range
        status3, _ = determine_result_status('Mad', 5.0)
        assert status3 == 'approved'


class TestRealWorldCoalSamples:
    """Real world coal sample scenario tests"""

    def test_typical_thermal_coal(self):
        """Typical thermal coal values"""
        from app.utils.analysis_rules import determine_result_status
        samples = {
            'MT': 8.5,
            'Mad': 3.2,
            'Aad': 22.5,
            'Vad': 29.8,
            'CV': 5800.0,
            'TS': 0.65,
        }
        for code, value in samples.items():
            status, _ = determine_result_status(code, value)
            assert status == 'approved', f'{code}={value} should be approved'

    def test_high_ash_coal(self):
        """High ash coal triggers warning"""
        from app.utils.analysis_rules import determine_result_status
        status, comment = determine_result_status('Aad', 92.0)
        assert status == 'pending_review'

    def test_high_sulfur_coal(self):
        """High sulfur coal triggers warning"""
        from app.utils.analysis_rules import determine_result_status
        status, comment = determine_result_status('TS', 22.0)
        assert status == 'pending_review'

    def test_qc_sample_in_control(self):
        """QC sample in statistical control"""
        from app.utils.analysis_rules import determine_result_status
        control = {'mean': 25.0, 'sd': 0.3}
        status, comment = determine_result_status('Aad', 25.2, control_targets=control)
        assert status == 'approved'
        assert 'Control Pass' in comment

    def test_qc_sample_drifting(self):
        """QC sample drifting from target"""
        from app.utils.analysis_rules import determine_result_status
        control = {'mean': 25.0, 'sd': 0.3}
        # 25.5 is 0.5 away, > 1SD (0.3) but < 2SD (0.6)
        status, comment = determine_result_status('Aad', 25.5, control_targets=control)
        assert status == 'pending_review'
        assert 'Warning' in comment
