# -*- coding: utf-8 -*-
"""
Tests for app/utils/westgard.py
Westgard QC rules tests
"""
import pytest


# ============================================================================
# WestgardViolation DATACLASS TESTS
# ============================================================================

class TestWestgardViolation:
    """WestgardViolation dataclass tests"""

    def test_import(self):
        """Import dataclass"""
        from app.utils.westgard import WestgardViolation
        assert WestgardViolation is not None

    def test_create_violation(self):
        """Create violation instance"""
        from app.utils.westgard import WestgardViolation

        v = WestgardViolation(
            rule="1:3s",
            description="Test violation",
            severity="reject",
            values=[10.0],
            indices=[0]
        )
        assert v.rule == "1:3s"
        assert v.description == "Test violation"
        assert v.severity == "reject"
        assert v.values == [10.0]
        assert v.indices == [0]

    def test_violation_with_multiple_values(self):
        """Violation with multiple values"""
        from app.utils.westgard import WestgardViolation

        v = WestgardViolation(
            rule="2:2s",
            description="Two values exceeded",
            severity="reject",
            values=[10.0, 11.0],
            indices=[0, 1]
        )
        assert len(v.values) == 2
        assert len(v.indices) == 2


# ============================================================================
# check_westgard_rules TESTS
# ============================================================================

class TestCheckWestgardRules:
    """check_westgard_rules function tests"""

    def test_import(self):
        """Import function"""
        from app.utils.westgard import check_westgard_rules
        assert callable(check_westgard_rules)

    def test_empty_values_returns_empty(self):
        """Empty values returns empty list"""
        from app.utils.westgard import check_westgard_rules

        result = check_westgard_rules([], mean=10.0, sd=1.0)
        assert result == []

    def test_zero_sd_returns_empty(self):
        """Zero SD returns empty list"""
        from app.utils.westgard import check_westgard_rules

        result = check_westgard_rules([10.0, 11.0], mean=10.0, sd=0)
        assert result == []

    def test_negative_sd_returns_empty(self):
        """Negative SD returns empty list"""
        from app.utils.westgard import check_westgard_rules

        result = check_westgard_rules([10.0, 11.0], mean=10.0, sd=-1.0)
        assert result == []

    def test_all_normal_no_violations(self):
        """All normal values - no violations"""
        from app.utils.westgard import check_westgard_rules

        # Values within 1 SD
        values = [10.0, 10.5, 9.5, 10.2, 9.8]
        result = check_westgard_rules(values, mean=10.0, sd=1.0)
        assert len(result) == 0


class TestRule13s:
    """1:3s rule tests (single value > 3SD)"""

    def test_value_exceeds_plus_3sd(self):
        """Value exceeds +3SD"""
        from app.utils.westgard import check_westgard_rules

        # 13.5 is 3.5 SD above mean of 10
        values = [13.5]
        result = check_westgard_rules(values, mean=10.0, sd=1.0)

        assert len(result) >= 1
        assert any(v.rule == "1:3s" for v in result)
        assert any(v.severity == "reject" for v in result)

    def test_value_exceeds_minus_3sd(self):
        """Value exceeds -3SD"""
        from app.utils.westgard import check_westgard_rules

        # 6.5 is 3.5 SD below mean of 10
        values = [6.5]
        result = check_westgard_rules(values, mean=10.0, sd=1.0)

        assert len(result) >= 1
        assert any(v.rule == "1:3s" for v in result)

    def test_value_exactly_3sd_no_violation(self):
        """Value exactly at 3SD - no violation"""
        from app.utils.westgard import check_westgard_rules

        # 13.0 is exactly 3 SD above mean
        values = [13.0]
        result = check_westgard_rules(values, mean=10.0, sd=1.0)

        # Should only be 1:2s warning, not 1:3s reject
        assert not any(v.rule == "1:3s" for v in result)

    def test_violation_contains_value(self):
        """Violation contains the violating value"""
        from app.utils.westgard import check_westgard_rules

        values = [15.0]  # 5 SD above
        result = check_westgard_rules(values, mean=10.0, sd=1.0)

        violation = next(v for v in result if v.rule == "1:3s")
        assert 15.0 in violation.values
        assert 0 in violation.indices


class TestRule12s:
    """1:2s rule tests (single value > 2SD, warning)"""

    def test_value_exceeds_plus_2sd_warning(self):
        """Value exceeds +2SD gives warning"""
        from app.utils.westgard import check_westgard_rules

        # 12.5 is 2.5 SD above mean of 10
        values = [12.5]
        result = check_westgard_rules(values, mean=10.0, sd=1.0)

        assert len(result) >= 1
        assert any(v.rule == "1:2s" for v in result)
        warning = next(v for v in result if v.rule == "1:2s")
        assert warning.severity == "warning"

    def test_value_exceeds_minus_2sd_warning(self):
        """Value exceeds -2SD gives warning"""
        from app.utils.westgard import check_westgard_rules

        # 7.5 is 2.5 SD below mean
        values = [7.5]
        result = check_westgard_rules(values, mean=10.0, sd=1.0)

        assert any(v.rule == "1:2s" for v in result)

    def test_value_exactly_2sd_no_warning(self):
        """Value exactly at 2SD - no warning"""
        from app.utils.westgard import check_westgard_rules

        # 12.0 is exactly 2 SD above
        values = [12.0]
        result = check_westgard_rules(values, mean=10.0, sd=1.0)

        # Exactly 2SD should not trigger warning
        assert not any(v.rule == "1:2s" for v in result)

    def test_value_above_3sd_not_12s(self):
        """Value > 3SD should not be 1:2s"""
        from app.utils.westgard import check_westgard_rules

        # 14.0 is 4 SD above - should be 1:3s, not 1:2s
        values = [14.0]
        result = check_westgard_rules(values, mean=10.0, sd=1.0)

        # Should have 1:3s but not 1:2s for this value
        assert any(v.rule == "1:3s" for v in result)
        # 1:2s check is abs(z) > 2 AND abs(z) <= 3
        assert not any(v.rule == "1:2s" for v in result)


class TestRule22s:
    """2:2s rule tests (two consecutive values > 2SD same side)"""

    def test_two_values_plus_2sd(self):
        """Two consecutive values > +2SD"""
        from app.utils.westgard import check_westgard_rules

        # Both > 2 SD above mean
        values = [12.5, 13.0]
        result = check_westgard_rules(values, mean=10.0, sd=1.0)

        assert any(v.rule == "2:2s" for v in result)
        violation = next(v for v in result if v.rule == "2:2s")
        assert violation.severity == "reject"

    def test_two_values_minus_2sd(self):
        """Two consecutive values < -2SD"""
        from app.utils.westgard import check_westgard_rules

        # Both > 2 SD below mean
        values = [7.5, 7.0]
        result = check_westgard_rules(values, mean=10.0, sd=1.0)

        assert any(v.rule == "2:2s" for v in result)

    def test_two_values_opposite_sides_no_violation(self):
        """Two values on opposite sides - no violation"""
        from app.utils.westgard import check_westgard_rules

        # One above, one below
        values = [12.5, 7.5]
        result = check_westgard_rules(values, mean=10.0, sd=1.0)

        # Should have 1:2s warnings but no 2:2s
        assert not any(v.rule == "2:2s" for v in result)

    def test_22s_only_reported_once(self):
        """2:2s only reported once even with multiple violations"""
        from app.utils.westgard import check_westgard_rules

        # Multiple consecutive values above 2SD
        values = [12.5, 12.8, 12.6]
        result = check_westgard_rules(values, mean=10.0, sd=1.0)

        # Should only have one 2:2s violation (break after first)
        count_22s = sum(1 for v in result if v.rule == "2:2s")
        assert count_22s == 1


class TestRuleR4s:
    """R:4s rule tests (range between two consecutive > 4SD)"""

    def test_range_exceeds_4sd(self):
        """Range between consecutive values > 4SD"""
        from app.utils.westgard import check_westgard_rules

        # 15.0 (z=5) and 5.0 (z=-5), range = 10 SD
        values = [15.0, 5.0]
        result = check_westgard_rules(values, mean=10.0, sd=1.0)

        assert any(v.rule == "R:4s" for v in result)
        violation = next(v for v in result if v.rule == "R:4s")
        assert violation.severity == "reject"

    def test_range_exactly_4sd_no_violation(self):
        """Range exactly 4SD - no violation"""
        from app.utils.westgard import check_westgard_rules

        # 12.0 (z=2) and 8.0 (z=-2), range = 4 SD
        values = [12.0, 8.0]
        result = check_westgard_rules(values, mean=10.0, sd=1.0)

        # Exactly 4SD should not trigger
        assert not any(v.rule == "R:4s" for v in result)

    def test_r4s_only_reported_once(self):
        """R:4s only reported once"""
        from app.utils.westgard import check_westgard_rules

        values = [15.0, 5.0, 15.0]
        result = check_westgard_rules(values, mean=10.0, sd=1.0)

        count_r4s = sum(1 for v in result if v.rule == "R:4s")
        assert count_r4s == 1


class TestRule41s:
    """4:1s rule tests (four consecutive > 1SD same side)"""

    def test_four_values_plus_1sd(self):
        """Four consecutive values > +1SD"""
        from app.utils.westgard import check_westgard_rules

        # All > 1 SD above mean
        values = [11.5, 11.2, 11.8, 11.3]
        result = check_westgard_rules(values, mean=10.0, sd=1.0)

        assert any(v.rule == "4:1s" for v in result)
        violation = next(v for v in result if v.rule == "4:1s")
        assert violation.severity == "reject"
        assert len(violation.values) == 4

    def test_four_values_minus_1sd(self):
        """Four consecutive values < -1SD"""
        from app.utils.westgard import check_westgard_rules

        # All > 1 SD below mean
        values = [8.5, 8.2, 8.8, 8.3]
        result = check_westgard_rules(values, mean=10.0, sd=1.0)

        assert any(v.rule == "4:1s" for v in result)

    def test_three_values_no_violation(self):
        """Three values not enough for 4:1s"""
        from app.utils.westgard import check_westgard_rules

        values = [11.5, 11.2, 11.8]
        result = check_westgard_rules(values, mean=10.0, sd=1.0)

        assert not any(v.rule == "4:1s" for v in result)

    def test_four_values_mixed_sides_no_violation(self):
        """Four values on mixed sides - no violation"""
        from app.utils.westgard import check_westgard_rules

        values = [11.5, 8.5, 11.2, 8.2]
        result = check_westgard_rules(values, mean=10.0, sd=1.0)

        assert not any(v.rule == "4:1s" for v in result)


class TestRule10x:
    """10x rule tests (ten consecutive on same side of mean)"""

    def test_ten_values_above_mean(self):
        """Ten consecutive values above mean"""
        from app.utils.westgard import check_westgard_rules

        # All positive (above mean)
        values = [10.1, 10.2, 10.3, 10.1, 10.2, 10.3, 10.1, 10.2, 10.3, 10.1]
        result = check_westgard_rules(values, mean=10.0, sd=1.0)

        assert any(v.rule == "10x" for v in result)
        violation = next(v for v in result if v.rule == "10x")
        assert violation.severity == "reject"
        assert len(violation.values) == 10

    def test_ten_values_below_mean(self):
        """Ten consecutive values below mean"""
        from app.utils.westgard import check_westgard_rules

        # All negative (below mean)
        values = [9.9, 9.8, 9.7, 9.9, 9.8, 9.7, 9.9, 9.8, 9.7, 9.9]
        result = check_westgard_rules(values, mean=10.0, sd=1.0)

        assert any(v.rule == "10x" for v in result)

    def test_nine_values_no_violation(self):
        """Nine values not enough for 10x"""
        from app.utils.westgard import check_westgard_rules

        values = [10.1, 10.2, 10.3, 10.1, 10.2, 10.3, 10.1, 10.2, 10.3]
        result = check_westgard_rules(values, mean=10.0, sd=1.0)

        assert not any(v.rule == "10x" for v in result)

    def test_ten_values_mixed_sides_no_violation(self):
        """Ten values crossing mean - no violation"""
        from app.utils.westgard import check_westgard_rules

        values = [10.1, 9.9, 10.1, 9.9, 10.1, 9.9, 10.1, 9.9, 10.1, 9.9]
        result = check_westgard_rules(values, mean=10.0, sd=1.0)

        assert not any(v.rule == "10x" for v in result)


# ============================================================================
# get_qc_status TESTS
# ============================================================================

class TestGetQcStatus:
    """get_qc_status function tests"""

    def test_import(self):
        """Import function"""
        from app.utils.westgard import get_qc_status
        assert callable(get_qc_status)

    def test_no_violations_pass(self):
        """No violations returns pass"""
        from app.utils.westgard import get_qc_status

        result = get_qc_status([])
        assert result["status"] == "pass"
        assert result["rules_violated"] == []
        assert "хэвийн" in result["message"]

    def test_warning_only(self):
        """Warning-only violations returns warning"""
        from app.utils.westgard import get_qc_status, WestgardViolation

        violations = [WestgardViolation(
            rule="1:2s",
            description="Test",
            severity="warning",
            values=[12.5],
            indices=[0]
        )]
        result = get_qc_status(violations)
        assert result["status"] == "warning"
        assert "1:2s" in result["rules_violated"]
        assert "Анхааруулга" in result["message"]

    def test_reject_violations(self):
        """Reject violations returns reject"""
        from app.utils.westgard import get_qc_status, WestgardViolation

        violations = [WestgardViolation(
            rule="1:3s",
            description="Test",
            severity="reject",
            values=[15.0],
            indices=[0]
        )]
        result = get_qc_status(violations)
        assert result["status"] == "reject"
        assert "1:3s" in result["rules_violated"]
        assert "REJECT" in result["message"]

    def test_mixed_severity_returns_reject(self):
        """Mixed severity returns reject (higher)"""
        from app.utils.westgard import get_qc_status, WestgardViolation

        violations = [
            WestgardViolation(rule="1:2s", description="", severity="warning", values=[], indices=[]),
            WestgardViolation(rule="1:3s", description="", severity="reject", values=[], indices=[])
        ]
        result = get_qc_status(violations)
        assert result["status"] == "reject"
        assert "1:2s" in result["rules_violated"]
        assert "1:3s" in result["rules_violated"]

    def test_multiple_same_rule_unique(self):
        """Multiple same rule violations show once"""
        from app.utils.westgard import get_qc_status, WestgardViolation

        violations = [
            WestgardViolation(rule="1:2s", description="", severity="warning", values=[], indices=[]),
            WestgardViolation(rule="1:2s", description="", severity="warning", values=[], indices=[])
        ]
        result = get_qc_status(violations)
        # Should only have one "1:2s" in the list
        assert result["rules_violated"].count("1:2s") == 1


# ============================================================================
# check_single_value TESTS
# ============================================================================

class TestCheckSingleValue:
    """check_single_value function tests"""

    def test_import(self):
        """Import function"""
        from app.utils.westgard import check_single_value
        assert callable(check_single_value)

    def test_zero_sd_returns_error(self):
        """Zero SD returns error"""
        from app.utils.westgard import check_single_value

        result = check_single_value(10.0, mean=10.0, sd=0)
        assert "error" in result

    def test_negative_sd_returns_error(self):
        """Negative SD returns error"""
        from app.utils.westgard import check_single_value

        result = check_single_value(10.0, mean=10.0, sd=-1.0)
        assert "error" in result

    def test_value_at_mean(self):
        """Value at mean is ok"""
        from app.utils.westgard import check_single_value

        result = check_single_value(10.0, mean=10.0, sd=1.0)
        assert result["status"] == "ok"
        assert result["z_score"] == 0.0
        assert result["in_1sd"] is True
        assert result["in_2sd"] is True
        assert result["in_3sd"] is True

    def test_value_within_1sd(self):
        """Value within 1SD is ok"""
        from app.utils.westgard import check_single_value

        result = check_single_value(10.5, mean=10.0, sd=1.0)
        assert result["status"] == "ok"
        assert result["in_1sd"] is True

    def test_value_between_1sd_and_2sd(self):
        """Value between 1SD and 2SD is ok"""
        from app.utils.westgard import check_single_value

        result = check_single_value(11.5, mean=10.0, sd=1.0)
        assert result["status"] == "ok"
        assert result["in_1sd"] is False
        assert result["in_2sd"] is True

    def test_value_between_2sd_and_3sd(self):
        """Value between 2SD and 3SD is warning"""
        from app.utils.westgard import check_single_value

        result = check_single_value(12.5, mean=10.0, sd=1.0)
        assert result["status"] == "warning"
        assert result["in_2sd"] is False
        assert result["in_3sd"] is True

    def test_value_beyond_3sd(self):
        """Value beyond 3SD is reject"""
        from app.utils.westgard import check_single_value

        result = check_single_value(14.0, mean=10.0, sd=1.0)
        assert result["status"] == "reject"
        assert result["in_3sd"] is False

    def test_negative_z_score(self):
        """Negative z-score calculated correctly"""
        from app.utils.westgard import check_single_value

        result = check_single_value(8.0, mean=10.0, sd=1.0)
        assert result["z_score"] == -2.0
        assert result["in_2sd"] is True

    def test_deviation_calculated(self):
        """Deviation is calculated"""
        from app.utils.westgard import check_single_value

        result = check_single_value(12.0, mean=10.0, sd=1.0)
        assert result["deviation"] == 2.0
        assert result["value"] == 12.0

    def test_z_score_rounded(self):
        """Z-score is rounded to 3 decimals"""
        from app.utils.westgard import check_single_value

        result = check_single_value(10.3333, mean=10.0, sd=1.0)
        assert isinstance(result["z_score"], float)
        # Should be rounded
        assert len(str(result["z_score"]).split('.')[-1]) <= 3


# ============================================================================
# INTEGRATION TESTS
# ============================================================================

class TestIntegration:
    """Integration tests combining multiple rules"""

    def test_multiple_violations_detected(self):
        """Multiple violations are detected"""
        from app.utils.westgard import check_westgard_rules

        # First value > 3SD (1:3s), second and third > 2SD same side (2:2s)
        values = [14.0, 12.5, 12.8]
        result = check_westgard_rules(values, mean=10.0, sd=1.0)

        assert any(v.rule == "1:3s" for v in result)
        assert any(v.rule == "2:2s" for v in result)

    def test_realistic_qc_data(self):
        """Realistic QC control chart data"""
        from app.utils.westgard import check_westgard_rules, get_qc_status

        # Typical QC values with slight drift
        values = [10.2, 10.1, 10.3, 10.0, 9.9, 10.1, 10.2, 9.8, 10.0, 10.1]
        violations = check_westgard_rules(values, mean=10.0, sd=0.5)
        status = get_qc_status(violations)

        # Should pass with normal variation
        assert status["status"] == "pass"

    def test_qc_out_of_control(self):
        """QC out of control scenario"""
        from app.utils.westgard import check_westgard_rules, get_qc_status

        # Values showing systematic bias
        values = [10.8, 10.9, 11.0, 11.1, 10.7, 10.8, 10.9, 11.0, 10.8, 10.9]
        violations = check_westgard_rules(values, mean=10.0, sd=0.3)
        status = get_qc_status(violations)

        # Should detect issues
        assert status["status"] in ["warning", "reject"]

    def test_full_workflow(self):
        """Full QC workflow"""
        from app.utils.westgard import check_westgard_rules, get_qc_status, check_single_value

        mean = 10.0
        sd = 1.0

        # Check single incoming value
        single = check_single_value(12.5, mean=mean, sd=sd)
        assert single["status"] == "warning"

        # Check historical values
        values = [12.5, 10.0, 10.2]
        violations = check_westgard_rules(values, mean=mean, sd=sd)

        # Get overall status
        status = get_qc_status(violations)
        assert status is not None


class TestEdgeCases:
    """Edge case tests"""

    def test_single_value_list(self):
        """Single value in list"""
        from app.utils.westgard import check_westgard_rules

        values = [14.0]  # > 3SD
        result = check_westgard_rules(values, mean=10.0, sd=1.0)

        # Should detect 1:3s
        assert any(v.rule == "1:3s" for v in result)

    def test_very_small_sd(self):
        """Very small SD"""
        from app.utils.westgard import check_westgard_rules

        values = [10.001]
        result = check_westgard_rules(values, mean=10.0, sd=0.0001)

        # Value is 10 SD away
        assert any(v.rule == "1:3s" for v in result)

    def test_large_values(self):
        """Large values"""
        from app.utils.westgard import check_westgard_rules

        values = [1000000.0, 1000050.0]
        result = check_westgard_rules(values, mean=1000000.0, sd=10.0)

        # 1000050 is 5 SD above
        assert any(v.rule == "1:3s" for v in result)

    def test_negative_values(self):
        """Negative values"""
        from app.utils.westgard import check_westgard_rules

        values = [-10.0, -12.5]
        result = check_westgard_rules(values, mean=-10.0, sd=1.0)

        # -12.5 is 2.5 SD below mean of -10
        assert any(v.rule == "1:2s" for v in result)

    def test_value_equals_mean_exactly(self):
        """Value equals mean exactly"""
        from app.utils.westgard import check_westgard_rules

        values = [10.0, 10.0, 10.0]
        result = check_westgard_rules(values, mean=10.0, sd=1.0)

        # All at mean - no violations
        assert len(result) == 0
