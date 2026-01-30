# -*- coding: utf-8 -*-
"""
Westgard модулийн coverage тестүүд
"""
import pytest


class TestWestgardViolation:
    """WestgardViolation dataclass тестүүд"""

    def test_import_class(self):
        """Class import"""
        from app.utils.westgard import WestgardViolation
        assert WestgardViolation is not None

    def test_create_violation(self):
        """Create violation instance"""
        from app.utils.westgard import WestgardViolation
        v = WestgardViolation(
            rule="1:3s",
            description="Test violation",
            severity="reject",
            values=[10.5],
            indices=[0]
        )
        assert v.rule == "1:3s"
        assert v.severity == "reject"


class TestCheckWestgardRules:
    """check_westgard_rules тестүүд"""

    def test_import_function(self):
        """Function import"""
        from app.utils.westgard import check_westgard_rules
        assert check_westgard_rules is not None

    def test_empty_values(self):
        """Empty values list"""
        from app.utils.westgard import check_westgard_rules
        result = check_westgard_rules([], 10.0, 1.0)
        assert result == []

    def test_zero_sd(self):
        """Zero SD"""
        from app.utils.westgard import check_westgard_rules
        result = check_westgard_rules([10.0, 11.0], 10.0, 0)
        assert result == []

    def test_negative_sd(self):
        """Negative SD"""
        from app.utils.westgard import check_westgard_rules
        result = check_westgard_rules([10.0, 11.0], 10.0, -1.0)
        assert result == []

    def test_no_violations(self):
        """No violations (values within 1SD)"""
        from app.utils.westgard import check_westgard_rules
        # Values very close to mean
        result = check_westgard_rules([10.0, 10.1, 9.9], 10.0, 1.0)
        assert len(result) == 0

    def test_1_3s_violation(self):
        """1:3s rule violation"""
        from app.utils.westgard import check_westgard_rules
        # Value at mean + 3.5SD
        result = check_westgard_rules([13.5], 10.0, 1.0)
        violations = [v for v in result if v.rule == "1:3s"]
        assert len(violations) == 1
        assert violations[0].severity == "reject"

    def test_1_2s_violation(self):
        """1:2s rule violation (warning)"""
        from app.utils.westgard import check_westgard_rules
        # Value at mean + 2.5SD (warning only)
        result = check_westgard_rules([12.5], 10.0, 1.0)
        violations = [v for v in result if v.rule == "1:2s"]
        assert len(violations) == 1
        assert violations[0].severity == "warning"

    def test_2_2s_violation_positive(self):
        """2:2s rule violation (both positive)"""
        from app.utils.westgard import check_westgard_rules
        # Two consecutive values > 2SD above mean
        result = check_westgard_rules([12.5, 12.8], 10.0, 1.0)
        violations = [v for v in result if v.rule == "2:2s"]
        assert len(violations) == 1
        assert violations[0].severity == "reject"

    def test_2_2s_violation_negative(self):
        """2:2s rule violation (both negative)"""
        from app.utils.westgard import check_westgard_rules
        # Two consecutive values > 2SD below mean
        result = check_westgard_rules([7.5, 7.2], 10.0, 1.0)
        violations = [v for v in result if v.rule == "2:2s"]
        assert len(violations) == 1

    def test_2_2s_no_violation_opposite(self):
        """2:2s no violation (opposite sides)"""
        from app.utils.westgard import check_westgard_rules
        # Two values on opposite sides of mean
        result = check_westgard_rules([12.5, 7.5], 10.0, 1.0)
        violations = [v for v in result if v.rule == "2:2s"]
        assert len(violations) == 0

    def test_r_4s_violation(self):
        """R:4s rule violation"""
        from app.utils.westgard import check_westgard_rules
        # Range > 4SD between consecutive values
        result = check_westgard_rules([7.0, 12.0], 10.0, 1.0)
        violations = [v for v in result if v.rule == "R:4s"]
        assert len(violations) >= 1
        assert violations[0].severity == "reject"

    def test_4_1s_violation_positive(self):
        """4:1s rule violation (all positive)"""
        from app.utils.westgard import check_westgard_rules
        # 4 consecutive values > 1SD above mean
        result = check_westgard_rules([11.2, 11.3, 11.1, 11.4], 10.0, 1.0)
        violations = [v for v in result if v.rule == "4:1s"]
        assert len(violations) == 1
        assert violations[0].severity == "reject"

    def test_4_1s_violation_negative(self):
        """4:1s rule violation (all negative)"""
        from app.utils.westgard import check_westgard_rules
        # 4 consecutive values > 1SD below mean
        result = check_westgard_rules([8.8, 8.7, 8.9, 8.6], 10.0, 1.0)
        violations = [v for v in result if v.rule == "4:1s"]
        assert len(violations) == 1

    def test_4_1s_no_violation_mixed(self):
        """4:1s no violation (mixed sides)"""
        from app.utils.westgard import check_westgard_rules
        # 4 values but not all on same side
        result = check_westgard_rules([11.2, 11.3, 8.9, 11.4], 10.0, 1.0)
        violations = [v for v in result if v.rule == "4:1s"]
        assert len(violations) == 0

    def test_10x_violation_positive(self):
        """10x rule violation (all positive)"""
        from app.utils.westgard import check_westgard_rules
        # 10 consecutive values above mean
        values = [10.1, 10.2, 10.3, 10.1, 10.2, 10.3, 10.1, 10.2, 10.3, 10.1]
        result = check_westgard_rules(values, 10.0, 1.0)
        violations = [v for v in result if v.rule == "10x"]
        assert len(violations) == 1

    def test_10x_violation_negative(self):
        """10x rule violation (all negative)"""
        from app.utils.westgard import check_westgard_rules
        # 10 consecutive values below mean
        values = [9.9, 9.8, 9.7, 9.9, 9.8, 9.7, 9.9, 9.8, 9.7, 9.9]
        result = check_westgard_rules(values, 10.0, 1.0)
        violations = [v for v in result if v.rule == "10x"]
        assert len(violations) == 1

    def test_10x_no_violation_mixed(self):
        """10x no violation (mixed)"""
        from app.utils.westgard import check_westgard_rules
        # 10 values but crossing mean
        values = [10.1, 10.2, 9.8, 10.1, 9.9, 10.3, 9.7, 10.2, 10.3, 9.9]
        result = check_westgard_rules(values, 10.0, 1.0)
        violations = [v for v in result if v.rule == "10x"]
        assert len(violations) == 0

    def test_fewer_than_10_values(self):
        """10x rule not checked with fewer values"""
        from app.utils.westgard import check_westgard_rules
        values = [10.1, 10.2, 10.3, 10.1, 10.2, 10.3, 10.1, 10.2, 10.3]  # Only 9
        result = check_westgard_rules(values, 10.0, 1.0)
        violations = [v for v in result if v.rule == "10x"]
        assert len(violations) == 0


class TestGetQcStatus:
    """get_qc_status тестүүд"""

    def test_import_function(self):
        """Function import"""
        from app.utils.westgard import get_qc_status
        assert get_qc_status is not None

    def test_no_violations(self):
        """No violations returns pass"""
        from app.utils.westgard import get_qc_status
        result = get_qc_status([])
        assert result["status"] == "pass"
        assert len(result["rules_violated"]) == 0

    def test_warning_violations(self):
        """Warning violations only"""
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

    def test_reject_violations(self):
        """Reject violations"""
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

    def test_mixed_violations(self):
        """Mixed warning and reject"""
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
                rule="2:2s",
                description="Reject",
                severity="reject",
                values=[12.5, 12.8],
                indices=[0, 1]
            )
        ]
        result = get_qc_status(violations)
        # Reject takes precedence
        assert result["status"] == "reject"

    def test_multiple_same_rule(self):
        """Multiple violations of same rule"""
        from app.utils.westgard import get_qc_status, WestgardViolation
        violations = [
            WestgardViolation(
                rule="1:2s",
                description="Warning 1",
                severity="warning",
                values=[12.5],
                indices=[0]
            ),
            WestgardViolation(
                rule="1:2s",
                description="Warning 2",
                severity="warning",
                values=[12.6],
                indices=[1]
            )
        ]
        result = get_qc_status(violations)
        # Rules should be deduplicated
        assert result["rules_violated"].count("1:2s") == 1


class TestCheckSingleValue:
    """check_single_value тестүүд"""

    def test_import_function(self):
        """Function import"""
        from app.utils.westgard import check_single_value
        assert check_single_value is not None

    def test_zero_sd(self):
        """Zero SD returns error"""
        from app.utils.westgard import check_single_value
        result = check_single_value(10.0, 10.0, 0)
        assert "error" in result

    def test_negative_sd(self):
        """Negative SD returns error"""
        from app.utils.westgard import check_single_value
        result = check_single_value(10.0, 10.0, -1.0)
        assert "error" in result

    def test_value_at_mean(self):
        """Value at mean"""
        from app.utils.westgard import check_single_value
        result = check_single_value(10.0, 10.0, 1.0)
        assert result["z_score"] == 0.0
        assert result["status"] == "ok"
        assert result["in_1sd"] is True
        assert result["in_2sd"] is True
        assert result["in_3sd"] is True

    def test_value_within_1sd(self):
        """Value within 1SD"""
        from app.utils.westgard import check_single_value
        result = check_single_value(10.5, 10.0, 1.0)
        assert abs(result["z_score"]) <= 1
        assert result["status"] == "ok"
        assert result["in_1sd"] is True

    def test_value_between_1sd_2sd(self):
        """Value between 1SD and 2SD"""
        from app.utils.westgard import check_single_value
        result = check_single_value(11.5, 10.0, 1.0)
        assert 1 < abs(result["z_score"]) <= 2
        assert result["status"] == "ok"
        assert result["in_1sd"] is False
        assert result["in_2sd"] is True

    def test_value_between_2sd_3sd(self):
        """Value between 2SD and 3SD"""
        from app.utils.westgard import check_single_value
        result = check_single_value(12.5, 10.0, 1.0)
        assert 2 < abs(result["z_score"]) <= 3
        assert result["status"] == "warning"
        assert result["in_2sd"] is False
        assert result["in_3sd"] is True

    def test_value_beyond_3sd(self):
        """Value beyond 3SD"""
        from app.utils.westgard import check_single_value
        result = check_single_value(14.0, 10.0, 1.0)
        assert abs(result["z_score"]) > 3
        assert result["status"] == "reject"
        assert result["in_3sd"] is False

    def test_negative_deviation(self):
        """Negative deviation"""
        from app.utils.westgard import check_single_value
        result = check_single_value(7.0, 10.0, 1.0)
        assert result["z_score"] < 0
        assert result["deviation"] < 0

    def test_result_has_all_fields(self):
        """Result has all expected fields"""
        from app.utils.westgard import check_single_value
        result = check_single_value(10.5, 10.0, 1.0)
        assert "value" in result
        assert "z_score" in result
        assert "deviation" in result
        assert "in_1sd" in result
        assert "in_2sd" in result
        assert "in_3sd" in result
        assert "status" in result
