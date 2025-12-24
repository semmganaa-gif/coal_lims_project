# tests/test_analysis_rules_deep.py
# -*- coding: utf-8 -*-
"""
Deep coverage tests for app/utils/analysis_rules.py
"""

import pytest


class TestSoftLimitsConstants:
    """Tests for SOFT_LIMITS constant."""

    def test_soft_limits_exists(self, app):
        """Test SOFT_LIMITS constant exists."""
        with app.app_context():
            from app.utils.analysis_rules import SOFT_LIMITS
            assert isinstance(SOFT_LIMITS, dict)

    def test_soft_limits_has_moisture(self, app):
        """Test SOFT_LIMITS has moisture parameters."""
        with app.app_context():
            from app.utils.analysis_rules import SOFT_LIMITS
            assert 'MT' in SOFT_LIMITS
            assert 'Mad' in SOFT_LIMITS

    def test_soft_limits_has_ash(self, app):
        """Test SOFT_LIMITS has ash parameters."""
        with app.app_context():
            from app.utils.analysis_rules import SOFT_LIMITS
            assert 'Aad' in SOFT_LIMITS
            assert 'A' in SOFT_LIMITS

    def test_soft_limits_has_volatile(self, app):
        """Test SOFT_LIMITS has volatile parameters."""
        with app.app_context():
            from app.utils.analysis_rules import SOFT_LIMITS
            assert 'Vad' in SOFT_LIMITS
            assert 'V' in SOFT_LIMITS
            assert 'Vdaf' in SOFT_LIMITS

    def test_soft_limits_has_sulfur(self, app):
        """Test SOFT_LIMITS has sulfur parameters."""
        with app.app_context():
            from app.utils.analysis_rules import SOFT_LIMITS
            assert 'TS' in SOFT_LIMITS
            assert 'St,ad' in SOFT_LIMITS
            assert 'St,d' in SOFT_LIMITS

    def test_soft_limits_has_phosphorus(self, app):
        """Test SOFT_LIMITS has phosphorus parameters."""
        with app.app_context():
            from app.utils.analysis_rules import SOFT_LIMITS
            assert 'P' in SOFT_LIMITS
            assert 'P,ad' in SOFT_LIMITS
            assert 'P,d' in SOFT_LIMITS

    def test_soft_limits_has_chlorine(self, app):
        """Test SOFT_LIMITS has chlorine parameters."""
        with app.app_context():
            from app.utils.analysis_rules import SOFT_LIMITS
            assert 'Cl' in SOFT_LIMITS
            assert 'Cl,ad' in SOFT_LIMITS

    def test_soft_limits_has_fluorine(self, app):
        """Test SOFT_LIMITS has fluorine parameters."""
        with app.app_context():
            from app.utils.analysis_rules import SOFT_LIMITS
            assert 'F' in SOFT_LIMITS
            assert 'F,ad' in SOFT_LIMITS

    def test_soft_max_limits_copy(self, app):
        """Test SOFT_MAX_LIMITS is copy of SOFT_LIMITS."""
        with app.app_context():
            from app.utils.analysis_rules import SOFT_LIMITS, SOFT_MAX_LIMITS
            assert SOFT_LIMITS.keys() == SOFT_MAX_LIMITS.keys()


class TestSoftMinLimits:
    """Tests for SOFT_MIN_LIMITS constant."""

    def test_soft_min_limits_exists(self, app):
        """Test SOFT_MIN_LIMITS constant exists."""
        with app.app_context():
            from app.utils.analysis_rules import SOFT_MIN_LIMITS
            assert isinstance(SOFT_MIN_LIMITS, dict)

    def test_soft_min_limits_has_cv(self, app):
        """Test SOFT_MIN_LIMITS has CV parameters."""
        with app.app_context():
            from app.utils.analysis_rules import SOFT_MIN_LIMITS
            assert 'CV' in SOFT_MIN_LIMITS
            assert 'Qgr,ad' in SOFT_MIN_LIMITS
            assert 'Qnet,ar' in SOFT_MIN_LIMITS

    def test_soft_min_limits_has_csr(self, app):
        """Test SOFT_MIN_LIMITS has CSR parameter."""
        with app.app_context():
            from app.utils.analysis_rules import SOFT_MIN_LIMITS
            assert 'CSR' in SOFT_MIN_LIMITS

    def test_soft_min_limits_has_mad(self, app):
        """Test SOFT_MIN_LIMITS has Mad parameter."""
        with app.app_context():
            from app.utils.analysis_rules import SOFT_MIN_LIMITS
            assert 'Mad' in SOFT_MIN_LIMITS


class TestDetermineResultStatusApproved:
    """Tests for determine_result_status - approved cases."""

    def test_normal_value_approved(self, app):
        """Test normal value returns approved."""
        with app.app_context():
            from app.utils.analysis_rules import determine_result_status
            status, comment = determine_result_status('MT', 10.0)
            assert status == 'approved'

    def test_unknown_code_approved(self, app):
        """Test unknown analysis code returns approved."""
        with app.app_context():
            from app.utils.analysis_rules import determine_result_status
            status, comment = determine_result_status('UNKNOWN', 50.0)
            assert status == 'approved'

    def test_none_value_approved(self, app):
        """Test None value returns approved."""
        with app.app_context():
            from app.utils.analysis_rules import determine_result_status
            status, comment = determine_result_status('MT', None)
            assert status == 'approved'

    def test_zero_value(self, app):
        """Test zero value handling."""
        with app.app_context():
            from app.utils.analysis_rules import determine_result_status
            status, comment = determine_result_status('MT', 0.0)
            assert status == 'approved'


class TestDetermineResultStatusPending:
    """Tests for determine_result_status - pending cases."""

    def test_high_moisture_pending(self, app):
        """Test high moisture triggers pending_review."""
        with app.app_context():
            from app.utils.analysis_rules import determine_result_status
            # MT soft limit is 35.0
            status, comment = determine_result_status('MT', 40.0)
            assert status == 'pending_review'
            assert 'Soft Limit' in comment

    def test_high_ash_pending(self, app):
        """Test high ash triggers pending_review."""
        with app.app_context():
            from app.utils.analysis_rules import determine_result_status
            # Aad soft limit is 90.0
            status, comment = determine_result_status('Aad', 95.0)
            assert status == 'pending_review'

    def test_low_cv_pending(self, app):
        """Test low CV triggers pending_review."""
        with app.app_context():
            from app.utils.analysis_rules import determine_result_status
            # CV soft min limit is 1000, but CV<2000 also triggers warning
            status, comment = determine_result_status('CV', 500.0)
            assert status == 'pending_review'

    def test_low_csr_pending(self, app):
        """Test low CSR triggers pending_review."""
        with app.app_context():
            from app.utils.analysis_rules import determine_result_status
            # CSR < 20.0 triggers pending
            status, comment = determine_result_status('CSR', 15.0)
            assert status == 'pending_review'
            assert 'CSR' in comment

    def test_high_sulfur_pending(self, app):
        """Test high sulfur triggers pending_review."""
        with app.app_context():
            from app.utils.analysis_rules import determine_result_status
            # TS soft limit is 20.0
            status, comment = determine_result_status('TS', 25.0)
            assert status == 'pending_review'

    def test_tolerance_exceeded_pending(self, app):
        """Test t_exceeded in raw_data triggers pending_review."""
        with app.app_context():
            from app.utils.analysis_rules import determine_result_status
            raw_data = {"t_exceeded": True}
            status, comment = determine_result_status('MT', 10.0, raw_data=raw_data)
            assert status == 'pending_review'
            assert 'Tolerance' in comment


class TestDetermineResultStatusControl:
    """Tests for determine_result_status - control sample cases."""

    def test_control_within_1sd_approved(self, app):
        """Test control within 1SD returns approved."""
        with app.app_context():
            from app.utils.analysis_rules import determine_result_status
            control_targets = {"mean": 10.0, "sd": 1.0}
            # Value 10.5 is within 1SD of mean 10.0
            status, comment = determine_result_status('MT', 10.5, control_targets=control_targets)
            assert status == 'approved'
            assert 'Control Pass' in comment

    def test_control_between_1sd_2sd_pending(self, app):
        """Test control between 1SD and 2SD returns pending_review."""
        with app.app_context():
            from app.utils.analysis_rules import determine_result_status
            control_targets = {"mean": 10.0, "sd": 1.0}
            # Value 11.5 is between 1SD (11.0) and 2SD (12.0)
            status, comment = determine_result_status('MT', 11.5, control_targets=control_targets)
            assert status == 'pending_review'
            assert '1SD' in comment

    def test_control_beyond_2sd_rejected(self, app):
        """Test control beyond 2SD returns rejected."""
        with app.app_context():
            from app.utils.analysis_rules import determine_result_status
            control_targets = {"mean": 10.0, "sd": 1.0}
            # Value 12.5 is beyond 2SD (12.0)
            status, comment = determine_result_status('MT', 12.5, control_targets=control_targets)
            assert status == 'rejected'
            assert '2SD' in comment

    def test_control_none_mean(self, app):
        """Test control with None mean falls through."""
        with app.app_context():
            from app.utils.analysis_rules import determine_result_status
            control_targets = {"mean": None, "sd": 1.0}
            status, comment = determine_result_status('MT', 10.0, control_targets=control_targets)
            assert status == 'approved'

    def test_control_none_sd(self, app):
        """Test control with None sd falls through."""
        with app.app_context():
            from app.utils.analysis_rules import determine_result_status
            control_targets = {"mean": 10.0, "sd": None}
            status, comment = determine_result_status('MT', 10.0, control_targets=control_targets)
            assert status == 'approved'

    def test_control_empty_dict(self, app):
        """Test control with empty dict falls through."""
        with app.app_context():
            from app.utils.analysis_rules import determine_result_status
            status, comment = determine_result_status('MT', 10.0, control_targets={})
            assert status == 'approved'


class TestDetermineResultStatusGi:
    """Tests for determine_result_status - Gi specific cases."""

    def test_gi_low_avg_rejected(self, app):
        """Test Gi with low average is rejected."""
        with app.app_context():
            from app.utils.analysis_rules import determine_result_status
            raw_data = {"is_low_avg": True}
            status, comment = determine_result_status('Gi', 3.0, raw_data=raw_data)
            assert status == 'rejected'
            assert 'GI_RETEST' in comment

    def test_gi_normal_approved(self, app):
        """Test Gi normal value is approved."""
        with app.app_context():
            from app.utils.analysis_rules import determine_result_status
            status, comment = determine_result_status('Gi', 5.0)
            assert status == 'approved'


class TestDetermineResultStatusCV:
    """Tests for determine_result_status - CV specific cases."""

    def test_cv_low_value_pending(self, app):
        """Test CV low value triggers pending."""
        with app.app_context():
            from app.utils.analysis_rules import determine_result_status
            status, comment = determine_result_status('CV', 1500.0)
            assert status == 'pending_review'

    def test_qgr_ad_low_value_pending(self, app):
        """Test Qgr,ad low value triggers pending."""
        with app.app_context():
            from app.utils.analysis_rules import determine_result_status
            status, comment = determine_result_status('Qgr,ad', 1800.0)
            assert status == 'pending_review'

    def test_qnet_ar_low_value_pending(self, app):
        """Test Qnet,ar low value triggers pending."""
        with app.app_context():
            from app.utils.analysis_rules import determine_result_status
            status, comment = determine_result_status('Qnet,ar', 1999.0)
            assert status == 'pending_review'

    def test_cv_normal_value_approved(self, app):
        """Test CV normal value is approved."""
        with app.app_context():
            from app.utils.analysis_rules import determine_result_status
            status, comment = determine_result_status('CV', 5000.0)
            assert status == 'approved'


class TestDetermineResultStatusMinLimits:
    """Tests for determine_result_status - min limit checks."""

    def test_low_mad_pending(self, app):
        """Test low Mad triggers pending_review."""
        with app.app_context():
            from app.utils.analysis_rules import determine_result_status
            # Mad min limit is 0.40
            status, comment = determine_result_status('Mad', 0.3)
            assert status == 'pending_review'
            assert 'Soft Limit' in comment

    def test_mad_above_min_approved(self, app):
        """Test Mad above min limit is approved."""
        with app.app_context():
            from app.utils.analysis_rules import determine_result_status
            status, comment = determine_result_status('Mad', 5.0)
            assert status == 'approved'


class TestDetermineResultStatusEdgeCases:
    """Edge case tests for determine_result_status."""

    def test_boundary_max_value(self, app):
        """Test value exactly at max limit."""
        with app.app_context():
            from app.utils.analysis_rules import determine_result_status
            # MT soft limit is 35.0
            status, comment = determine_result_status('MT', 35.0)
            assert status == 'approved'  # Exactly at limit should pass

    def test_boundary_min_value(self, app):
        """Test value exactly at min limit."""
        with app.app_context():
            from app.utils.analysis_rules import determine_result_status
            # Mad min limit is 0.40
            status, comment = determine_result_status('Mad', 0.40)
            assert status == 'approved'  # Exactly at limit should pass

    def test_negative_value(self, app):
        """Test negative value handling."""
        with app.app_context():
            from app.utils.analysis_rules import determine_result_status
            status, comment = determine_result_status('MT', -5.0)
            # Negative values should still work (pass to approved if no min limit)
            assert status in ['approved', 'pending_review']

    def test_very_large_value(self, app):
        """Test very large value."""
        with app.app_context():
            from app.utils.analysis_rules import determine_result_status
            status, comment = determine_result_status('MT', 99999.0)
            assert status == 'pending_review'

    def test_empty_raw_data(self, app):
        """Test with empty raw_data dict."""
        with app.app_context():
            from app.utils.analysis_rules import determine_result_status
            status, comment = determine_result_status('MT', 10.0, raw_data={})
            assert status == 'approved'

    def test_raw_data_with_other_keys(self, app):
        """Test raw_data with irrelevant keys."""
        with app.app_context():
            from app.utils.analysis_rules import determine_result_status
            raw_data = {"other_key": "value", "another": 123}
            status, comment = determine_result_status('MT', 10.0, raw_data=raw_data)
            assert status == 'approved'
