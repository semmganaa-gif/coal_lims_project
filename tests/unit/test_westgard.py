# tests/unit/test_westgard.py
# -*- coding: utf-8 -*-
"""
Westgard QC rules тест

Tests for:
- WestgardViolation dataclass
- check_westgard_rules() - All 6 Westgard rules
- get_qc_status() - Status determination
- check_single_value() - Single value check
"""

import pytest
from app.utils.westgard import (
    WestgardViolation,
    check_westgard_rules,
    get_qc_status,
    check_single_value
)


class TestWestgardViolation:
    """WestgardViolation dataclass тест"""

    def test_violation_creation(self):
        """Violation объект үүсгэх"""
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

    def test_violation_multiple_values(self):
        """Олон утгатай violation"""
        violation = WestgardViolation(
            rule="2:2s",
            description="Two consecutive",
            severity="reject",
            values=[10.5, 11.2],
            indices=[0, 1]
        )
        assert len(violation.values) == 2
        assert len(violation.indices) == 2


class TestCheckWestgardRules:
    """check_westgard_rules() функцийн тест"""

    def test_empty_values(self):
        """Хоосон утга"""
        result = check_westgard_rules([], mean=10.0, sd=1.0)
        assert result == []

    def test_zero_sd(self):
        """SD=0 үед"""
        result = check_westgard_rules([10.0, 11.0], mean=10.0, sd=0)
        assert result == []

    def test_negative_sd(self):
        """Сөрөг SD үед"""
        result = check_westgard_rules([10.0], mean=10.0, sd=-1.0)
        assert result == []

    def test_no_violations(self):
        """Зөрчилгүй - бүх утга хэвийн"""
        # mean=100, sd=2, values within ±2SD
        values = [100.0, 101.0, 99.0, 100.5, 99.5]
        result = check_westgard_rules(values, mean=100.0, sd=2.0)
        # No violations expected
        assert all(v.rule not in ["1:3s", "2:2s", "R:4s", "4:1s", "10x"]
                   for v in result if v.severity == "reject")

    # ================================================================
    # 1:3s Rule Tests
    # ================================================================
    def test_rule_1_3s_positive(self):
        """1:3s - Утга +3SD-ээс хэтэрсэн"""
        # mean=100, sd=2, value > 106 triggers 1:3s
        values = [107.0]  # z = (107-100)/2 = 3.5 > 3
        result = check_westgard_rules(values, mean=100.0, sd=2.0)

        rule_1_3s = [v for v in result if v.rule == "1:3s"]
        assert len(rule_1_3s) == 1
        assert rule_1_3s[0].severity == "reject"
        assert 107.0 in rule_1_3s[0].values

    def test_rule_1_3s_negative(self):
        """1:3s - Утга -3SD-ээс хэтэрсэн"""
        # mean=100, sd=2, value < 94 triggers 1:3s
        values = [93.0]  # z = (93-100)/2 = -3.5 < -3
        result = check_westgard_rules(values, mean=100.0, sd=2.0)

        rule_1_3s = [v for v in result if v.rule == "1:3s"]
        assert len(rule_1_3s) == 1
        assert rule_1_3s[0].severity == "reject"

    def test_rule_1_3s_boundary(self):
        """1:3s - Яг 3SD дээр (зөрчилгүй)"""
        # mean=100, sd=2, value=106 is exactly 3SD
        values = [106.0]  # z = 3.0, not > 3
        result = check_westgard_rules(values, mean=100.0, sd=2.0)

        rule_1_3s = [v for v in result if v.rule == "1:3s"]
        assert len(rule_1_3s) == 0

    # ================================================================
    # 1:2s Rule Tests
    # ================================================================
    def test_rule_1_2s_warning(self):
        """1:2s - Утга 2SD-3SD хооронд (анхааруулга)"""
        # mean=100, sd=2, value between 104-106
        values = [105.0]  # z = 2.5, between 2 and 3
        result = check_westgard_rules(values, mean=100.0, sd=2.0)

        rule_1_2s = [v for v in result if v.rule == "1:2s"]
        assert len(rule_1_2s) == 1
        assert rule_1_2s[0].severity == "warning"

    def test_rule_1_2s_negative_side(self):
        """1:2s - Сөрөг талд 2SD-3SD хооронд"""
        values = [95.0]  # z = -2.5
        result = check_westgard_rules(values, mean=100.0, sd=2.0)

        rule_1_2s = [v for v in result if v.rule == "1:2s"]
        assert len(rule_1_2s) == 1
        assert rule_1_2s[0].severity == "warning"

    def test_rule_1_2s_not_triggered_within_2sd(self):
        """1:2s - 2SD дотор (зөрчилгүй)"""
        values = [103.0]  # z = 1.5
        result = check_westgard_rules(values, mean=100.0, sd=2.0)

        rule_1_2s = [v for v in result if v.rule == "1:2s"]
        assert len(rule_1_2s) == 0

    # ================================================================
    # 2:2s Rule Tests
    # ================================================================
    def test_rule_2_2s_positive(self):
        """2:2s - 2 дараалсан утга +2SD-ээс хэтэрсэн"""
        # Both values > mean + 2*sd = 104
        values = [105.0, 106.0]  # Both z > 2
        result = check_westgard_rules(values, mean=100.0, sd=2.0)

        rule_2_2s = [v for v in result if v.rule == "2:2s"]
        assert len(rule_2_2s) == 1
        assert rule_2_2s[0].severity == "reject"

    def test_rule_2_2s_negative(self):
        """2:2s - 2 дараалсан утга -2SD-ээс хэтэрсэн"""
        values = [95.0, 94.0]  # Both z < -2
        result = check_westgard_rules(values, mean=100.0, sd=2.0)

        rule_2_2s = [v for v in result if v.rule == "2:2s"]
        assert len(rule_2_2s) == 1

    def test_rule_2_2s_opposite_sides(self):
        """2:2s - 2 утга өөр талд (зөрчилгүй)"""
        values = [105.0, 95.0]  # One positive, one negative
        result = check_westgard_rules(values, mean=100.0, sd=2.0)

        rule_2_2s = [v for v in result if v.rule == "2:2s"]
        assert len(rule_2_2s) == 0

    def test_rule_2_2s_not_consecutive(self):
        """2:2s - Дараалаагүй (зөрчилгүй)"""
        values = [105.0, 100.0, 106.0]  # Not consecutive
        result = check_westgard_rules(values, mean=100.0, sd=2.0)

        rule_2_2s = [v for v in result if v.rule == "2:2s"]
        assert len(rule_2_2s) == 0

    # ================================================================
    # R:4s Rule Tests
    # ================================================================
    def test_rule_r4s(self):
        """R:4s - 2 утгын зөрүү 4SD-ээс их"""
        # |z1 - z2| > 4, need range > 4*sd = 8
        values = [110.0, 98.0]  # z1=5, z2=-1, diff=6 > 4
        result = check_westgard_rules(values, mean=100.0, sd=2.0)

        rule_r4s = [v for v in result if v.rule == "R:4s"]
        assert len(rule_r4s) == 1
        assert rule_r4s[0].severity == "reject"

    def test_rule_r4s_boundary(self):
        """R:4s - Яг 4SD зөрүү (зөрчилгүй)"""
        # |z1 - z2| = 4
        values = [104.0, 96.0]  # z1=2, z2=-2, diff=4, not > 4
        result = check_westgard_rules(values, mean=100.0, sd=2.0)

        rule_r4s = [v for v in result if v.rule == "R:4s"]
        assert len(rule_r4s) == 0

    # ================================================================
    # 4:1s Rule Tests
    # ================================================================
    def test_rule_4_1s_positive(self):
        """4:1s - 4 дараалсан утга +1SD-ээс хэтэрсэн"""
        # All 4 values > mean + sd = 102
        values = [103.0, 104.0, 103.5, 102.5]  # All z > 1
        result = check_westgard_rules(values, mean=100.0, sd=2.0)

        rule_4_1s = [v for v in result if v.rule == "4:1s"]
        assert len(rule_4_1s) == 1
        assert rule_4_1s[0].severity == "reject"

    def test_rule_4_1s_negative(self):
        """4:1s - 4 дараалсан утга -1SD-ээс хэтэрсэн"""
        values = [97.0, 96.0, 97.5, 96.5]  # All z < -1
        result = check_westgard_rules(values, mean=100.0, sd=2.0)

        rule_4_1s = [v for v in result if v.rule == "4:1s"]
        assert len(rule_4_1s) == 1

    def test_rule_4_1s_mixed(self):
        """4:1s - 4 утга холимог (зөрчилгүй)"""
        values = [103.0, 97.0, 104.0, 96.0]  # Mixed sides
        result = check_westgard_rules(values, mean=100.0, sd=2.0)

        rule_4_1s = [v for v in result if v.rule == "4:1s"]
        assert len(rule_4_1s) == 0

    def test_rule_4_1s_only_3_values(self):
        """4:1s - Зөвхөн 3 утга (хангалтгүй)"""
        values = [103.0, 104.0, 103.5]  # Only 3 values
        result = check_westgard_rules(values, mean=100.0, sd=2.0)

        rule_4_1s = [v for v in result if v.rule == "4:1s"]
        assert len(rule_4_1s) == 0

    # ================================================================
    # 10x Rule Tests
    # ================================================================
    def test_rule_10x_positive(self):
        """10x - 10 дараалсан утга дунджаас их"""
        # All 10 values > mean
        values = [101.0 + i * 0.1 for i in range(10)]  # All above mean
        result = check_westgard_rules(values, mean=100.0, sd=2.0)

        rule_10x = [v for v in result if v.rule == "10x"]
        assert len(rule_10x) == 1
        assert rule_10x[0].severity == "reject"

    def test_rule_10x_negative(self):
        """10x - 10 дараалсан утга дунджаас бага"""
        values = [99.0 - i * 0.1 for i in range(10)]  # All below mean
        result = check_westgard_rules(values, mean=100.0, sd=2.0)

        rule_10x = [v for v in result if v.rule == "10x"]
        assert len(rule_10x) == 1

    def test_rule_10x_mixed(self):
        """10x - 10 утга холимог (зөрчилгүй)"""
        values = [101.0, 99.0, 101.0, 99.0, 101.0, 99.0, 101.0, 99.0, 101.0, 99.0]
        result = check_westgard_rules(values, mean=100.0, sd=2.0)

        rule_10x = [v for v in result if v.rule == "10x"]
        assert len(rule_10x) == 0

    def test_rule_10x_not_enough_values(self):
        """10x - 10-аас бага утга"""
        values = [101.0] * 9  # Only 9 values
        result = check_westgard_rules(values, mean=100.0, sd=2.0)

        rule_10x = [v for v in result if v.rule == "10x"]
        assert len(rule_10x) == 0

    # ================================================================
    # Multiple Rules Tests
    # ================================================================
    def test_multiple_violations(self):
        """Олон дүрэм нэгэн зэрэг зөрчигдөх"""
        # Value that triggers both 1:3s
        values = [110.0]  # z = 5 > 3
        result = check_westgard_rules(values, mean=100.0, sd=2.0)

        assert len(result) >= 1
        rules = [v.rule for v in result]
        assert "1:3s" in rules


class TestGetQcStatus:
    """get_qc_status() функцийн тест"""

    def test_pass_status(self):
        """Зөрчилгүй - pass"""
        result = get_qc_status([])
        assert result["status"] == "pass"
        assert result["rules_violated"] == []
        assert "хэвийн" in result["message"]

    def test_warning_status(self):
        """Анхааруулга - warning"""
        violations = [
            WestgardViolation(
                rule="1:2s",
                description="Test",
                severity="warning",
                values=[105.0],
                indices=[0]
            )
        ]
        result = get_qc_status(violations)
        assert result["status"] == "warning"
        assert "1:2s" in result["rules_violated"]

    def test_reject_status(self):
        """Татгалзах - reject"""
        violations = [
            WestgardViolation(
                rule="1:3s",
                description="Test",
                severity="reject",
                values=[110.0],
                indices=[0]
            )
        ]
        result = get_qc_status(violations)
        assert result["status"] == "reject"
        assert "1:3s" in result["rules_violated"]
        assert "REJECT" in result["message"]

    def test_reject_takes_precedence(self):
        """Reject нь warning-ээс давуу"""
        violations = [
            WestgardViolation(
                rule="1:2s",
                description="Warning",
                severity="warning",
                values=[105.0],
                indices=[0]
            ),
            WestgardViolation(
                rule="1:3s",
                description="Reject",
                severity="reject",
                values=[110.0],
                indices=[1]
            )
        ]
        result = get_qc_status(violations)
        assert result["status"] == "reject"

    def test_unique_rules(self):
        """Давхардсан дүрмүүд нэг удаа"""
        violations = [
            WestgardViolation(rule="1:3s", description="", severity="reject", values=[110], indices=[0]),
            WestgardViolation(rule="1:3s", description="", severity="reject", values=[111], indices=[1]),
        ]
        result = get_qc_status(violations)
        # rules_violated should have unique values
        assert result["rules_violated"].count("1:3s") == 1


class TestCheckSingleValue:
    """check_single_value() функцийн тест"""

    def test_value_within_1sd(self):
        """1SD дотор"""
        result = check_single_value(100.5, mean=100.0, sd=2.0)
        assert result["status"] == "ok"
        assert result["in_1sd"] is True
        assert result["in_2sd"] is True
        assert result["in_3sd"] is True

    def test_value_between_1sd_2sd(self):
        """1SD-2SD хооронд"""
        result = check_single_value(103.5, mean=100.0, sd=2.0)  # z = 1.75
        assert result["status"] == "ok"
        assert result["in_1sd"] is False
        assert result["in_2sd"] is True
        assert result["in_3sd"] is True

    def test_value_between_2sd_3sd(self):
        """2SD-3SD хооронд - warning"""
        result = check_single_value(105.0, mean=100.0, sd=2.0)  # z = 2.5
        assert result["status"] == "warning"
        assert result["in_1sd"] is False
        assert result["in_2sd"] is False
        assert result["in_3sd"] is True

    def test_value_beyond_3sd(self):
        """3SD-ээс хол - reject"""
        result = check_single_value(107.0, mean=100.0, sd=2.0)  # z = 3.5
        assert result["status"] == "reject"
        assert result["in_1sd"] is False
        assert result["in_2sd"] is False
        assert result["in_3sd"] is False

    def test_negative_deviation(self):
        """Сөрөг хазайлт"""
        result = check_single_value(95.0, mean=100.0, sd=2.0)  # z = -2.5
        assert result["status"] == "warning"
        assert result["z_score"] < 0

    def test_zero_sd_error(self):
        """SD=0 үед алдаа"""
        result = check_single_value(100.0, mean=100.0, sd=0)
        assert "error" in result

    def test_negative_sd_error(self):
        """Сөрөг SD үед алдаа"""
        result = check_single_value(100.0, mean=100.0, sd=-1.0)
        assert "error" in result

    def test_z_score_calculation(self):
        """Z-score тооцоолол"""
        result = check_single_value(104.0, mean=100.0, sd=2.0)
        assert result["z_score"] == 2.0

    def test_deviation_calculation(self):
        """Deviation тооцоолол"""
        result = check_single_value(104.0, mean=100.0, sd=2.0)
        assert result["deviation"] == 4.0

    def test_value_included_in_result(self):
        """Утга буцаагдсан эсэх"""
        result = check_single_value(104.0, mean=100.0, sd=2.0)
        assert result["value"] == 104.0
