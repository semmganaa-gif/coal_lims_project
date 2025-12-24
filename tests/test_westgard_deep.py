# tests/test_westgard_deep.py
# -*- coding: utf-8 -*-
"""
Deep coverage tests for app/utils/westgard.py
"""

import pytest


class TestWestgardViolation:
    """Tests for WestgardViolation dataclass."""

    def test_violation_creation(self, app):
        """Test WestgardViolation can be created."""
        with app.app_context():
            from app.utils.westgard import WestgardViolation

            violation = WestgardViolation(
                rule="1:3s",
                description="Test violation",
                severity="reject",
                values=[10.5],
                indices=[0]
            )
            assert violation.rule == "1:3s"
            assert violation.severity == "reject"
            assert violation.values == [10.5]
            assert violation.indices == [0]


class TestCheckWestgardRulesEmpty:
    """Tests for check_westgard_rules with empty/invalid input."""

    def test_empty_values(self, app):
        """Test check_westgard_rules with empty values list."""
        with app.app_context():
            from app.utils.westgard import check_westgard_rules
            result = check_westgard_rules([], 10.0, 1.0)
            assert result == []

    def test_zero_sd(self, app):
        """Test check_westgard_rules with zero SD."""
        with app.app_context():
            from app.utils.westgard import check_westgard_rules
            result = check_westgard_rules([10.0, 11.0], 10.0, 0)
            assert result == []

    def test_negative_sd(self, app):
        """Test check_westgard_rules with negative SD."""
        with app.app_context():
            from app.utils.westgard import check_westgard_rules
            result = check_westgard_rules([10.0, 11.0], 10.0, -1.0)
            assert result == []


class TestCheckWestgardRules1to3s:
    """Tests for 1:3s rule (value beyond ±3SD)."""

    def test_1to3s_violation_above(self, app):
        """Test 1:3s rule triggers for value > 3SD above mean."""
        with app.app_context():
            from app.utils.westgard import check_westgard_rules
            # mean=10, sd=1, value=14 -> z=4 -> beyond 3SD
            result = check_westgard_rules([14.0], 10.0, 1.0)
            rules = [v.rule for v in result]
            assert "1:3s" in rules

    def test_1to3s_violation_below(self, app):
        """Test 1:3s rule triggers for value < 3SD below mean."""
        with app.app_context():
            from app.utils.westgard import check_westgard_rules
            # mean=10, sd=1, value=6 -> z=-4 -> beyond 3SD
            result = check_westgard_rules([6.0], 10.0, 1.0)
            rules = [v.rule for v in result]
            assert "1:3s" in rules

    def test_1to3s_no_violation(self, app):
        """Test 1:3s rule doesn't trigger for value within 3SD."""
        with app.app_context():
            from app.utils.westgard import check_westgard_rules
            # mean=10, sd=1, value=12.5 -> z=2.5 -> within 3SD
            result = check_westgard_rules([12.5], 10.0, 1.0)
            rules = [v.rule for v in result]
            assert "1:3s" not in rules


class TestCheckWestgardRules1to2s:
    """Tests for 1:2s rule (warning for value beyond ±2SD but within 3SD)."""

    def test_1to2s_warning(self, app):
        """Test 1:2s rule triggers warning for value between 2SD and 3SD."""
        with app.app_context():
            from app.utils.westgard import check_westgard_rules
            # mean=10, sd=1, value=12.5 -> z=2.5 -> beyond 2SD but within 3SD
            result = check_westgard_rules([12.5], 10.0, 1.0)
            violations = [v for v in result if v.rule == "1:2s"]
            assert len(violations) > 0
            assert violations[0].severity == "warning"

    def test_1to2s_no_warning_within_2sd(self, app):
        """Test 1:2s rule doesn't trigger for value within 2SD."""
        with app.app_context():
            from app.utils.westgard import check_westgard_rules
            # mean=10, sd=1, value=11.5 -> z=1.5 -> within 2SD
            result = check_westgard_rules([11.5], 10.0, 1.0)
            rules = [v.rule for v in result]
            assert "1:2s" not in rules


class TestCheckWestgardRules2to2s:
    """Tests for 2:2s rule (2 consecutive values on same side beyond 2SD)."""

    def test_2to2s_violation_both_above(self, app):
        """Test 2:2s rule triggers for 2 consecutive values above 2SD."""
        with app.app_context():
            from app.utils.westgard import check_westgard_rules
            # Both values > 2SD above mean
            result = check_westgard_rules([12.5, 12.8], 10.0, 1.0)
            rules = [v.rule for v in result]
            assert "2:2s" in rules

    def test_2to2s_violation_both_below(self, app):
        """Test 2:2s rule triggers for 2 consecutive values below -2SD."""
        with app.app_context():
            from app.utils.westgard import check_westgard_rules
            # Both values < -2SD
            result = check_westgard_rules([7.5, 7.2], 10.0, 1.0)
            rules = [v.rule for v in result]
            assert "2:2s" in rules

    def test_2to2s_no_violation_opposite_sides(self, app):
        """Test 2:2s rule doesn't trigger for values on opposite sides."""
        with app.app_context():
            from app.utils.westgard import check_westgard_rules
            # One above, one below
            result = check_westgard_rules([12.5, 7.5], 10.0, 1.0)
            rules = [v.rule for v in result]
            assert "2:2s" not in rules


class TestCheckWestgardRulesR4s:
    """Tests for R:4s rule (range between 2 consecutive values > 4SD)."""

    def test_r4s_violation(self, app):
        """Test R:4s rule triggers for large range."""
        with app.app_context():
            from app.utils.westgard import check_westgard_rules
            # Range = |14 - 6| = 8, which is > 4SD (4)
            result = check_westgard_rules([14.0, 6.0], 10.0, 1.0)
            rules = [v.rule for v in result]
            assert "R:4s" in rules

    def test_r4s_no_violation(self, app):
        """Test R:4s rule doesn't trigger for small range."""
        with app.app_context():
            from app.utils.westgard import check_westgard_rules
            # Range = |11 - 9| = 2, which is < 4SD
            result = check_westgard_rules([11.0, 9.0], 10.0, 1.0)
            rules = [v.rule for v in result]
            assert "R:4s" not in rules


class TestCheckWestgardRules4to1s:
    """Tests for 4:1s rule (4 consecutive values on same side beyond 1SD)."""

    def test_4to1s_violation_above(self, app):
        """Test 4:1s rule triggers for 4 values above 1SD."""
        with app.app_context():
            from app.utils.westgard import check_westgard_rules
            # All 4 values > 1SD above mean
            result = check_westgard_rules([11.5, 11.3, 11.8, 11.2], 10.0, 1.0)
            rules = [v.rule for v in result]
            assert "4:1s" in rules

    def test_4to1s_violation_below(self, app):
        """Test 4:1s rule triggers for 4 values below -1SD."""
        with app.app_context():
            from app.utils.westgard import check_westgard_rules
            # All 4 values < -1SD
            result = check_westgard_rules([8.5, 8.3, 8.8, 8.2], 10.0, 1.0)
            rules = [v.rule for v in result]
            assert "4:1s" in rules

    def test_4to1s_no_violation_mixed(self, app):
        """Test 4:1s rule doesn't trigger for mixed values."""
        with app.app_context():
            from app.utils.westgard import check_westgard_rules
            # Mixed values
            result = check_westgard_rules([11.5, 9.5, 11.3, 10.5], 10.0, 1.0)
            rules = [v.rule for v in result]
            assert "4:1s" not in rules


class TestCheckWestgardRules10x:
    """Tests for 10x rule (10 consecutive values on same side of mean)."""

    def test_10x_violation_above(self, app):
        """Test 10x rule triggers for 10 values above mean."""
        with app.app_context():
            from app.utils.westgard import check_westgard_rules
            # All 10 values > mean
            values = [10.1] * 10
            result = check_westgard_rules(values, 10.0, 1.0)
            rules = [v.rule for v in result]
            assert "10x" in rules

    def test_10x_violation_below(self, app):
        """Test 10x rule triggers for 10 values below mean."""
        with app.app_context():
            from app.utils.westgard import check_westgard_rules
            # All 10 values < mean
            values = [9.9] * 10
            result = check_westgard_rules(values, 10.0, 1.0)
            rules = [v.rule for v in result]
            assert "10x" in rules

    def test_10x_no_violation_mixed(self, app):
        """Test 10x rule doesn't trigger for mixed values."""
        with app.app_context():
            from app.utils.westgard import check_westgard_rules
            # Mixed values
            values = [10.1, 9.9, 10.1, 9.9, 10.1, 9.9, 10.1, 9.9, 10.1, 9.9]
            result = check_westgard_rules(values, 10.0, 1.0)
            rules = [v.rule for v in result]
            assert "10x" not in rules

    def test_10x_not_enough_values(self, app):
        """Test 10x rule doesn't trigger with fewer than 10 values."""
        with app.app_context():
            from app.utils.westgard import check_westgard_rules
            values = [10.1] * 9  # Only 9 values
            result = check_westgard_rules(values, 10.0, 1.0)
            rules = [v.rule for v in result]
            assert "10x" not in rules


class TestGetQcStatus:
    """Tests for get_qc_status function."""

    def test_qc_status_pass(self, app):
        """Test get_qc_status returns pass for no violations."""
        with app.app_context():
            from app.utils.westgard import get_qc_status
            result = get_qc_status([])
            assert result["status"] == "pass"
            assert result["rules_violated"] == []

    def test_qc_status_warning(self, app):
        """Test get_qc_status returns warning for warning violations."""
        with app.app_context():
            from app.utils.westgard import get_qc_status, WestgardViolation
            violations = [
                WestgardViolation(
                    rule="1:2s",
                    description="Warning",
                    severity="warning",
                    values=[12.5],
                    indices=[0]
                )
            ]
            result = get_qc_status(violations)
            assert result["status"] == "warning"
            assert "1:2s" in result["rules_violated"]

    def test_qc_status_reject(self, app):
        """Test get_qc_status returns reject for reject violations."""
        with app.app_context():
            from app.utils.westgard import get_qc_status, WestgardViolation
            violations = [
                WestgardViolation(
                    rule="1:3s",
                    description="Reject",
                    severity="reject",
                    values=[14.0],
                    indices=[0]
                )
            ]
            result = get_qc_status(violations)
            assert result["status"] == "reject"
            assert "1:3s" in result["rules_violated"]

    def test_qc_status_mixed_violations(self, app):
        """Test get_qc_status with mixed severity violations."""
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
            # Should be reject if any reject violation exists
            assert result["status"] == "reject"


class TestCheckSingleValue:
    """Tests for check_single_value function."""

    def test_single_value_ok(self, app):
        """Test check_single_value returns ok for value within 1SD."""
        with app.app_context():
            from app.utils.westgard import check_single_value
            result = check_single_value(10.5, 10.0, 1.0)
            assert result["status"] == "ok"
            assert result["in_1sd"] is True
            assert result["in_2sd"] is True
            assert result["in_3sd"] is True

    def test_single_value_warning(self, app):
        """Test check_single_value returns warning for value between 2SD and 3SD."""
        with app.app_context():
            from app.utils.westgard import check_single_value
            result = check_single_value(12.5, 10.0, 1.0)
            assert result["status"] == "warning"
            assert result["in_1sd"] is False
            assert result["in_2sd"] is False
            assert result["in_3sd"] is True

    def test_single_value_reject(self, app):
        """Test check_single_value returns reject for value beyond 3SD."""
        with app.app_context():
            from app.utils.westgard import check_single_value
            result = check_single_value(14.0, 10.0, 1.0)
            assert result["status"] == "reject"
            assert result["in_1sd"] is False
            assert result["in_2sd"] is False
            assert result["in_3sd"] is False

    def test_single_value_zero_sd(self, app):
        """Test check_single_value with zero SD returns error."""
        with app.app_context():
            from app.utils.westgard import check_single_value
            result = check_single_value(10.0, 10.0, 0)
            assert "error" in result

    def test_single_value_negative_sd(self, app):
        """Test check_single_value with negative SD returns error."""
        with app.app_context():
            from app.utils.westgard import check_single_value
            result = check_single_value(10.0, 10.0, -1.0)
            assert "error" in result

    def test_single_value_z_score(self, app):
        """Test check_single_value calculates correct z-score."""
        with app.app_context():
            from app.utils.westgard import check_single_value
            result = check_single_value(12.0, 10.0, 1.0)
            assert result["z_score"] == 2.0

    def test_single_value_deviation(self, app):
        """Test check_single_value calculates correct deviation."""
        with app.app_context():
            from app.utils.westgard import check_single_value
            result = check_single_value(12.0, 10.0, 1.0)
            assert result["deviation"] == 2.0
