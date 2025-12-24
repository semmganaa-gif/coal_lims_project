# tests/test_westgard_full.py
# -*- coding: utf-8 -*-
"""
Complete tests for app/utils/westgard.py
"""

import pytest


class TestCheckWestgardRules:
    """Tests for check_westgard_rules function."""

    def test_empty_values(self, app):
        """Test with empty values returns empty list."""
        with app.app_context():
            from app.utils.westgard import check_westgard_rules
            result = check_westgard_rules([], 10.0, 1.0)
            assert result == []

    def test_zero_sd(self, app):
        """Test with zero SD returns empty list."""
        with app.app_context():
            from app.utils.westgard import check_westgard_rules
            result = check_westgard_rules([10.0, 11.0], 10.0, 0)
            assert result == []

    def test_negative_sd(self, app):
        """Test with negative SD returns empty list."""
        with app.app_context():
            from app.utils.westgard import check_westgard_rules
            result = check_westgard_rules([10.0, 11.0], 10.0, -1.0)
            assert result == []

    def test_normal_values_no_violations(self, app):
        """Test normal values have no violations."""
        with app.app_context():
            from app.utils.westgard import check_westgard_rules
            values = [10.0, 10.1, 9.9, 10.2, 9.8]
            result = check_westgard_rules(values, 10.0, 1.0)
            # All values within 1SD, no violations expected
            assert len([v for v in result if v.severity == 'reject']) == 0

    def test_1_3s_rule_violation(self, app):
        """Test 1:3s rule violation (value > 3SD)."""
        with app.app_context():
            from app.utils.westgard import check_westgard_rules
            values = [14.0, 10.0, 10.0]  # 14.0 is 4SD above mean
            result = check_westgard_rules(values, 10.0, 1.0)
            violations = [v for v in result if v.rule == "1:3s"]
            assert len(violations) > 0
            assert violations[0].severity == "reject"

    def test_1_3s_rule_negative(self, app):
        """Test 1:3s rule with negative deviation."""
        with app.app_context():
            from app.utils.westgard import check_westgard_rules
            values = [6.0, 10.0, 10.0]  # 6.0 is 4SD below mean
            result = check_westgard_rules(values, 10.0, 1.0)
            violations = [v for v in result if v.rule == "1:3s"]
            assert len(violations) > 0

    def test_1_2s_rule_warning(self, app):
        """Test 1:2s rule warning (value between 2SD and 3SD)."""
        with app.app_context():
            from app.utils.westgard import check_westgard_rules
            values = [12.5, 10.0, 10.0]  # 12.5 is 2.5SD above mean
            result = check_westgard_rules(values, 10.0, 1.0)
            violations = [v for v in result if v.rule == "1:2s"]
            assert len(violations) > 0
            assert violations[0].severity == "warning"

    def test_2_2s_rule_violation(self, app):
        """Test 2:2s rule violation (2 consecutive values > 2SD same side)."""
        with app.app_context():
            from app.utils.westgard import check_westgard_rules
            values = [12.5, 12.3, 10.0]  # Both > 2SD above mean
            result = check_westgard_rules(values, 10.0, 1.0)
            violations = [v for v in result if v.rule == "2:2s"]
            assert len(violations) > 0
            assert violations[0].severity == "reject"

    def test_2_2s_rule_negative(self, app):
        """Test 2:2s rule with negative deviation."""
        with app.app_context():
            from app.utils.westgard import check_westgard_rules
            values = [7.5, 7.3, 10.0]  # Both < -2SD
            result = check_westgard_rules(values, 10.0, 1.0)
            violations = [v for v in result if v.rule == "2:2s"]
            assert len(violations) > 0

    def test_r_4s_rule_violation(self, app):
        """Test R:4s rule violation (range > 4SD)."""
        with app.app_context():
            from app.utils.westgard import check_westgard_rules
            values = [13.0, 7.0, 10.0]  # Range = 6, which is 6SD
            result = check_westgard_rules(values, 10.0, 1.0)
            violations = [v for v in result if v.rule == "R:4s"]
            assert len(violations) > 0
            assert violations[0].severity == "reject"

    def test_4_1s_rule_violation(self, app):
        """Test 4:1s rule violation (4 consecutive > 1SD same side)."""
        with app.app_context():
            from app.utils.westgard import check_westgard_rules
            values = [11.5, 11.3, 11.4, 11.2, 10.0]  # All > 1SD
            result = check_westgard_rules(values, 10.0, 1.0)
            violations = [v for v in result if v.rule == "4:1s"]
            assert len(violations) > 0
            assert violations[0].severity == "reject"

    def test_4_1s_rule_negative(self, app):
        """Test 4:1s rule with negative deviation."""
        with app.app_context():
            from app.utils.westgard import check_westgard_rules
            values = [8.5, 8.3, 8.4, 8.2, 10.0]  # All < -1SD
            result = check_westgard_rules(values, 10.0, 1.0)
            violations = [v for v in result if v.rule == "4:1s"]
            assert len(violations) > 0

    def test_10x_rule_violation(self, app):
        """Test 10x rule violation (10 consecutive on same side)."""
        with app.app_context():
            from app.utils.westgard import check_westgard_rules
            # 10 values all above mean
            values = [10.1, 10.2, 10.3, 10.1, 10.2, 10.3, 10.1, 10.2, 10.3, 10.1, 10.0]
            result = check_westgard_rules(values, 10.0, 1.0)
            violations = [v for v in result if v.rule == "10x"]
            assert len(violations) > 0
            assert violations[0].severity == "reject"

    def test_10x_rule_negative(self, app):
        """Test 10x rule with all values below mean."""
        with app.app_context():
            from app.utils.westgard import check_westgard_rules
            # 10 values all below mean
            values = [9.9, 9.8, 9.7, 9.9, 9.8, 9.7, 9.9, 9.8, 9.7, 9.9, 10.0]
            result = check_westgard_rules(values, 10.0, 1.0)
            violations = [v for v in result if v.rule == "10x"]
            assert len(violations) > 0

    def test_less_than_10_values_no_10x(self, app):
        """Test fewer than 10 values doesn't trigger 10x."""
        with app.app_context():
            from app.utils.westgard import check_westgard_rules
            values = [10.1, 10.2, 10.3, 10.1, 10.2]  # Only 5 values
            result = check_westgard_rules(values, 10.0, 1.0)
            violations = [v for v in result if v.rule == "10x"]
            assert len(violations) == 0


class TestGetQcStatus:
    """Tests for get_qc_status function."""

    def test_empty_violations_returns_pass(self, app):
        """Test empty violations returns pass."""
        with app.app_context():
            from app.utils.westgard import get_qc_status
            result = get_qc_status([])
            assert result['status'] == 'pass'
            assert result['rules_violated'] == []

    def test_warning_violation(self, app):
        """Test warning violation returns warning status."""
        with app.app_context():
            from app.utils.westgard import get_qc_status, WestgardViolation
            violations = [WestgardViolation(
                rule="1:2s",
                description="Test",
                severity="warning",
                values=[12.5],
                indices=[0]
            )]
            result = get_qc_status(violations)
            assert result['status'] == 'warning'
            assert '1:2s' in result['rules_violated']

    def test_reject_violation(self, app):
        """Test reject violation returns reject status."""
        with app.app_context():
            from app.utils.westgard import get_qc_status, WestgardViolation
            violations = [WestgardViolation(
                rule="1:3s",
                description="Test",
                severity="reject",
                values=[14.0],
                indices=[0]
            )]
            result = get_qc_status(violations)
            assert result['status'] == 'reject'
            assert '1:3s' in result['rules_violated']

    def test_mixed_violations_returns_reject(self, app):
        """Test mixed violations returns reject (worst case)."""
        with app.app_context():
            from app.utils.westgard import get_qc_status, WestgardViolation
            violations = [
                WestgardViolation(
                    rule="1:2s",
                    description="Warning",
                    severity="warning",
                    values=[12.5],
                    indices=[0]
                ),
                WestgardViolation(
                    rule="1:3s",
                    description="Reject",
                    severity="reject",
                    values=[14.0],
                    indices=[1]
                )
            ]
            result = get_qc_status(violations)
            assert result['status'] == 'reject'

    def test_result_has_message(self, app):
        """Test result contains message."""
        with app.app_context():
            from app.utils.westgard import get_qc_status
            result = get_qc_status([])
            assert 'message' in result
            assert isinstance(result['message'], str)


class TestCheckSingleValue:
    """Tests for check_single_value function."""

    def test_zero_sd_returns_error(self, app):
        """Test zero SD returns error."""
        with app.app_context():
            from app.utils.westgard import check_single_value
            result = check_single_value(10.0, 10.0, 0)
            assert 'error' in result

    def test_negative_sd_returns_error(self, app):
        """Test negative SD returns error."""
        with app.app_context():
            from app.utils.westgard import check_single_value
            result = check_single_value(10.0, 10.0, -1.0)
            assert 'error' in result

    def test_value_at_mean(self, app):
        """Test value at mean."""
        with app.app_context():
            from app.utils.westgard import check_single_value
            result = check_single_value(10.0, 10.0, 1.0)
            assert result['z_score'] == 0.0
            assert result['status'] == 'ok'
            assert result['in_1sd'] is True
            assert result['in_2sd'] is True
            assert result['in_3sd'] is True

    def test_value_within_1sd(self, app):
        """Test value within 1SD."""
        with app.app_context():
            from app.utils.westgard import check_single_value
            result = check_single_value(10.5, 10.0, 1.0)
            assert result['status'] == 'ok'
            assert result['in_1sd'] is True

    def test_value_between_1sd_and_2sd(self, app):
        """Test value between 1SD and 2SD."""
        with app.app_context():
            from app.utils.westgard import check_single_value
            result = check_single_value(11.5, 10.0, 1.0)
            assert result['status'] == 'ok'
            assert result['in_1sd'] is False
            assert result['in_2sd'] is True

    def test_value_between_2sd_and_3sd(self, app):
        """Test value between 2SD and 3SD."""
        with app.app_context():
            from app.utils.westgard import check_single_value
            result = check_single_value(12.5, 10.0, 1.0)
            assert result['status'] == 'warning'
            assert result['in_2sd'] is False
            assert result['in_3sd'] is True

    def test_value_beyond_3sd(self, app):
        """Test value beyond 3SD."""
        with app.app_context():
            from app.utils.westgard import check_single_value
            result = check_single_value(14.0, 10.0, 1.0)
            assert result['status'] == 'reject'
            assert result['in_3sd'] is False

    def test_negative_deviation(self, app):
        """Test negative deviation."""
        with app.app_context():
            from app.utils.westgard import check_single_value
            result = check_single_value(6.0, 10.0, 1.0)
            assert result['z_score'] == -4.0
            assert result['status'] == 'reject'

    def test_result_has_deviation(self, app):
        """Test result contains deviation."""
        with app.app_context():
            from app.utils.westgard import check_single_value
            result = check_single_value(11.0, 10.0, 1.0)
            assert 'deviation' in result
            assert result['deviation'] == 1.0

    def test_result_has_value(self, app):
        """Test result contains original value."""
        with app.app_context():
            from app.utils.westgard import check_single_value
            result = check_single_value(11.0, 10.0, 1.0)
            assert 'value' in result
            assert result['value'] == 11.0


class TestWestgardViolation:
    """Tests for WestgardViolation dataclass."""

    def test_create_violation(self, app):
        """Test creating a violation."""
        with app.app_context():
            from app.utils.westgard import WestgardViolation
            v = WestgardViolation(
                rule="1:3s",
                description="Test violation",
                severity="reject",
                values=[14.0],
                indices=[0]
            )
            assert v.rule == "1:3s"
            assert v.description == "Test violation"
            assert v.severity == "reject"
            assert v.values == [14.0]
            assert v.indices == [0]

    def test_violation_with_multiple_values(self, app):
        """Test violation with multiple values."""
        with app.app_context():
            from app.utils.westgard import WestgardViolation
            v = WestgardViolation(
                rule="2:2s",
                description="Two consecutive violations",
                severity="reject",
                values=[12.5, 12.3],
                indices=[0, 1]
            )
            assert len(v.values) == 2
            assert len(v.indices) == 2
