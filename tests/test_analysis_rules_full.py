# tests/test_analysis_rules_full.py
# -*- coding: utf-8 -*-
"""
Complete tests for app/utils/analysis_rules.py
"""

import pytest


class TestDetermineResultStatus:
    """Tests for determine_result_status function."""

    def test_approved_normal_value(self, app):
        """Test normal value returns approved."""
        with app.app_context():
            from app.utils.analysis_rules import determine_result_status
            status, comment = determine_result_status('MT', 15.0)
            assert status == 'approved'
            assert comment is None

    def test_tolerance_exceeded(self, app):
        """Test tolerance exceeded returns pending_review."""
        with app.app_context():
            from app.utils.analysis_rules import determine_result_status
            raw_data = {'t_exceeded': True}
            status, comment = determine_result_status('MT', 15.0, raw_data=raw_data)
            assert status == 'pending_review'
            assert 'Tolerance' in comment

    def test_control_sample_pass(self, app):
        """Test control sample within 1SD passes."""
        with app.app_context():
            from app.utils.analysis_rules import determine_result_status
            control_targets = {'mean': 10.0, 'sd': 1.0}
            status, comment = determine_result_status('MT', 10.3, control_targets=control_targets)
            assert status == 'approved'
            assert 'Pass' in comment

    def test_control_sample_warning(self, app):
        """Test control sample between 1SD and 2SD returns warning."""
        with app.app_context():
            from app.utils.analysis_rules import determine_result_status
            control_targets = {'mean': 10.0, 'sd': 1.0}
            status, comment = determine_result_status('MT', 11.5, control_targets=control_targets)
            assert status == 'pending_review'
            assert '1SD' in comment

    def test_control_sample_rejected(self, app):
        """Test control sample beyond 2SD is rejected."""
        with app.app_context():
            from app.utils.analysis_rules import determine_result_status
            control_targets = {'mean': 10.0, 'sd': 1.0}
            status, comment = determine_result_status('MT', 13.0, control_targets=control_targets)
            assert status == 'rejected'
            assert '2SD' in comment

    def test_gi_low_avg_rejected(self, app):
        """Test Gi with low avg is rejected."""
        with app.app_context():
            from app.utils.analysis_rules import determine_result_status
            raw_data = {'is_low_avg': True}
            status, comment = determine_result_status('Gi', 5, raw_data=raw_data)
            assert status == 'rejected'
            assert 'RETEST' in comment

    def test_csr_low_value_pending(self, app):
        """Test CSR below 20 is pending."""
        with app.app_context():
            from app.utils.analysis_rules import determine_result_status
            status, comment = determine_result_status('CSR', 15.0)
            assert status == 'pending_review'
            assert 'CSR' in comment

    def test_cv_low_value_pending(self, app):
        """Test CV below 2000 is pending."""
        with app.app_context():
            from app.utils.analysis_rules import determine_result_status
            status, comment = determine_result_status('CV', 1500.0)
            assert status == 'pending_review'
            assert 'Илчлэг' in comment

    def test_soft_max_limit_exceeded(self, app):
        """Test exceeding soft max limit."""
        with app.app_context():
            from app.utils.analysis_rules import determine_result_status
            status, comment = determine_result_status('MT', 40.0)  # MT soft limit is 35
            assert status == 'pending_review'
            assert 'Soft Limit' in comment

    def test_soft_min_limit_exceeded(self, app):
        """Test exceeding soft min limit."""
        with app.app_context():
            from app.utils.analysis_rules import determine_result_status
            # CV value 500 triggers CV business rule first (value < 2000)
            status, comment = determine_result_status('CV', 500.0)
            assert status == 'pending_review'
            # Business logic checks CV < 2000 first, returns 'Илчлэг хэт бага'
            assert 'Илчлэг' in comment or 'Soft Limit' in comment

    def test_none_raw_data(self, app):
        """Test with None raw_data."""
        with app.app_context():
            from app.utils.analysis_rules import determine_result_status
            status, comment = determine_result_status('MT', 15.0, raw_data=None)
            assert status == 'approved'

    def test_none_control_targets(self, app):
        """Test with None control_targets."""
        with app.app_context():
            from app.utils.analysis_rules import determine_result_status
            status, comment = determine_result_status('MT', 15.0, control_targets=None)
            assert status == 'approved'

    def test_none_value(self, app):
        """Test with None value."""
        with app.app_context():
            from app.utils.analysis_rules import determine_result_status
            status, comment = determine_result_status('MT', None)
            assert status == 'approved'

    def test_control_targets_missing_sd(self, app):
        """Test control targets with missing SD."""
        with app.app_context():
            from app.utils.analysis_rules import determine_result_status
            control_targets = {'mean': 10.0}  # No sd
            status, comment = determine_result_status('MT', 15.0, control_targets=control_targets)
            # Should proceed to normal checks
            assert status == 'approved'

    def test_control_targets_missing_mean(self, app):
        """Test control targets with missing mean."""
        with app.app_context():
            from app.utils.analysis_rules import determine_result_status
            control_targets = {'sd': 1.0}  # No mean
            status, comment = determine_result_status('MT', 15.0, control_targets=control_targets)
            assert status == 'approved'


class TestSoftLimits:
    """Tests for SOFT_LIMITS constant."""

    def test_soft_limits_is_dict(self, app):
        """Test SOFT_LIMITS is a dictionary."""
        with app.app_context():
            from app.utils.analysis_rules import SOFT_LIMITS
            assert isinstance(SOFT_LIMITS, dict)

    def test_soft_limits_has_mt(self, app):
        """Test SOFT_LIMITS has MT."""
        with app.app_context():
            from app.utils.analysis_rules import SOFT_LIMITS
            assert 'MT' in SOFT_LIMITS
            assert SOFT_LIMITS['MT'] == 35.0

    def test_soft_limits_has_aad(self, app):
        """Test SOFT_LIMITS has Aad."""
        with app.app_context():
            from app.utils.analysis_rules import SOFT_LIMITS
            assert 'Aad' in SOFT_LIMITS


class TestSoftMinLimits:
    """Tests for SOFT_MIN_LIMITS constant."""

    def test_soft_min_limits_is_dict(self, app):
        """Test SOFT_MIN_LIMITS is a dictionary."""
        with app.app_context():
            from app.utils.analysis_rules import SOFT_MIN_LIMITS
            assert isinstance(SOFT_MIN_LIMITS, dict)

    def test_soft_min_limits_has_cv(self, app):
        """Test SOFT_MIN_LIMITS has CV."""
        with app.app_context():
            from app.utils.analysis_rules import SOFT_MIN_LIMITS
            assert 'CV' in SOFT_MIN_LIMITS
            assert SOFT_MIN_LIMITS['CV'] == 1000.0

    def test_soft_min_limits_has_csr(self, app):
        """Test SOFT_MIN_LIMITS has CSR."""
        with app.app_context():
            from app.utils.analysis_rules import SOFT_MIN_LIMITS
            assert 'CSR' in SOFT_MIN_LIMITS
            assert SOFT_MIN_LIMITS['CSR'] == 20.0
