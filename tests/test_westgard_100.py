# -*- coding: utf-8 -*-
"""
westgard.py модулийн 100% coverage тестүүд

Westgard дүрмүүдийн бүх branch-уудыг тест хийнэ.
"""
import pytest
from typing import List


class TestWestgardImport:
    """Модуль импорт тест"""

    def test_import_module(self):
        from app.utils import westgard
        assert westgard is not None

    def test_import_violation_class(self):
        from app.utils.westgard import WestgardViolation
        assert WestgardViolation is not None

    def test_import_functions(self):
        from app.utils.westgard import (
            check_westgard_rules, get_qc_status, check_single_value
        )
        assert check_westgard_rules is not None
        assert get_qc_status is not None
        assert check_single_value is not None


class TestWestgardViolation:
    """WestgardViolation dataclass тест"""

    def test_create_violation(self):
        from app.utils.westgard import WestgardViolation
        v = WestgardViolation(
            rule="1:3s",
            description="Test violation",
            severity="reject",
            values=[10.5],
            indices=[0]
        )
        assert v.rule == "1:3s"
        assert v.description == "Test violation"
        assert v.severity == "reject"
        assert v.values == [10.5]
        assert v.indices == [0]


class TestCheckWestgardRules:
    """check_westgard_rules функцийн тест"""

    def test_empty_values(self):
        from app.utils.westgard import check_westgard_rules
        result = check_westgard_rules([], 10.0, 1.0)
        assert result == []

    def test_zero_sd(self):
        from app.utils.westgard import check_westgard_rules
        result = check_westgard_rules([10.0, 10.5], 10.0, 0)
        assert result == []

    def test_negative_sd(self):
        from app.utils.westgard import check_westgard_rules
        result = check_westgard_rules([10.0, 10.5], 10.0, -1)
        assert result == []

    def test_no_violations(self):
        """Зөрчилгүй утгууд"""
        from app.utils.westgard import check_westgard_rules
        values = [10.0, 10.1, 9.9, 10.05, 9.95]
        result = check_westgard_rules(values, 10.0, 0.5)
        # Бүх утга 1SD дотор
        assert len([v for v in result if v.severity == "reject"]) == 0


class TestRule13s:
    """1:3s дүрмийн тест"""

    def test_1_3s_violation_positive(self):
        """Утга +3SD-ээс хэтэрсэн"""
        from app.utils.westgard import check_westgard_rules
        # mean=10, sd=1, value=14 -> z=4 > 3
        values = [14.0, 10.0, 10.0]
        result = check_westgard_rules(values, 10.0, 1.0)
        rules = [v.rule for v in result]
        assert "1:3s" in rules

    def test_1_3s_violation_negative(self):
        """Утга -3SD-ээс хэтэрсэн"""
        from app.utils.westgard import check_westgard_rules
        values = [6.0, 10.0, 10.0]  # z=-4 < -3
        result = check_westgard_rules(values, 10.0, 1.0)
        rules = [v.rule for v in result]
        assert "1:3s" in rules

    def test_1_3s_severity_reject(self):
        from app.utils.westgard import check_westgard_rules
        values = [14.0]
        result = check_westgard_rules(values, 10.0, 1.0)
        assert any(v.severity == "reject" for v in result if v.rule == "1:3s")


class TestRule12s:
    """1:2s дүрмийн тест"""

    def test_1_2s_violation_positive(self):
        """Утга +2SD - +3SD хооронд"""
        from app.utils.westgard import check_westgard_rules
        # mean=10, sd=1, value=12.5 -> z=2.5
        values = [12.5, 10.0]
        result = check_westgard_rules(values, 10.0, 1.0)
        rules = [v.rule for v in result]
        assert "1:2s" in rules

    def test_1_2s_violation_negative(self):
        """Утга -2SD - -3SD хооронд"""
        from app.utils.westgard import check_westgard_rules
        values = [7.5, 10.0]  # z=-2.5
        result = check_westgard_rules(values, 10.0, 1.0)
        rules = [v.rule for v in result]
        assert "1:2s" in rules

    def test_1_2s_severity_warning(self):
        from app.utils.westgard import check_westgard_rules
        values = [12.5]
        result = check_westgard_rules(values, 10.0, 1.0)
        assert any(v.severity == "warning" for v in result if v.rule == "1:2s")

    def test_1_2s_not_triggered_at_exactly_2(self):
        """z=2 яг бол 1:2s trigger хийхгүй (2-оос их байх ёстой)"""
        from app.utils.westgard import check_westgard_rules
        values = [12.0]  # z=2 exactly
        result = check_westgard_rules(values, 10.0, 1.0)
        rules = [v.rule for v in result]
        assert "1:2s" not in rules


class TestRule22s:
    """2:2s дүрмийн тест"""

    def test_2_2s_violation_positive(self):
        """2 дараалсан утга +2SD-ээс хэтэрсэн"""
        from app.utils.westgard import check_westgard_rules
        # Both z > 2
        values = [12.5, 12.3, 10.0]
        result = check_westgard_rules(values, 10.0, 1.0)
        rules = [v.rule for v in result]
        assert "2:2s" in rules

    def test_2_2s_violation_negative(self):
        """2 дараалсан утга -2SD-ээс хэтэрсэн"""
        from app.utils.westgard import check_westgard_rules
        values = [7.5, 7.3, 10.0]  # Both z < -2
        result = check_westgard_rules(values, 10.0, 1.0)
        rules = [v.rule for v in result]
        assert "2:2s" in rules

    def test_2_2s_not_same_side(self):
        """2 утга өөр талд (зөрчилгүй)"""
        from app.utils.westgard import check_westgard_rules
        values = [12.5, 7.5, 10.0]  # One positive, one negative
        result = check_westgard_rules(values, 10.0, 1.0)
        rules = [v.rule for v in result]
        assert "2:2s" not in rules

    def test_2_2s_severity_reject(self):
        from app.utils.westgard import check_westgard_rules
        values = [12.5, 12.3]
        result = check_westgard_rules(values, 10.0, 1.0)
        assert any(v.severity == "reject" for v in result if v.rule == "2:2s")


class TestRuleR4s:
    """R:4s дүрмийн тест"""

    def test_r4s_violation(self):
        """2 дараалсан утгын зөрүү 4SD-ээс их"""
        from app.utils.westgard import check_westgard_rules
        # z1=2.5, z2=-2.5, range=5 > 4
        values = [12.5, 7.5, 10.0]
        result = check_westgard_rules(values, 10.0, 1.0)
        rules = [v.rule for v in result]
        assert "R:4s" in rules

    def test_r4s_no_violation(self):
        """Зөрүү 4SD-ээс бага"""
        from app.utils.westgard import check_westgard_rules
        values = [11.5, 8.5, 10.0]  # z range = 3 < 4
        result = check_westgard_rules(values, 10.0, 1.0)
        rules = [v.rule for v in result]
        assert "R:4s" not in rules

    def test_r4s_severity_reject(self):
        from app.utils.westgard import check_westgard_rules
        values = [12.5, 7.5]
        result = check_westgard_rules(values, 10.0, 1.0)
        assert any(v.severity == "reject" for v in result if v.rule == "R:4s")


class TestRule41s:
    """4:1s дүрмийн тест"""

    def test_4_1s_violation_positive(self):
        """4 дараалсан утга +1SD-ээс хэтэрсэн"""
        from app.utils.westgard import check_westgard_rules
        # All z > 1
        values = [11.5, 11.3, 11.4, 11.2, 10.0]
        result = check_westgard_rules(values, 10.0, 1.0)
        rules = [v.rule for v in result]
        assert "4:1s" in rules

    def test_4_1s_violation_negative(self):
        """4 дараалсан утга -1SD-ээс хэтэрсэн"""
        from app.utils.westgard import check_westgard_rules
        values = [8.5, 8.7, 8.6, 8.8, 10.0]  # All z < -1
        result = check_westgard_rules(values, 10.0, 1.0)
        rules = [v.rule for v in result]
        assert "4:1s" in rules

    def test_4_1s_not_all_same_side(self):
        """4 утга нэг талд биш"""
        from app.utils.westgard import check_westgard_rules
        values = [11.5, 8.5, 11.3, 11.2]  # Mixed sides
        result = check_westgard_rules(values, 10.0, 1.0)
        rules = [v.rule for v in result]
        assert "4:1s" not in rules

    def test_4_1s_only_3_values(self):
        """3 утга - дүрэм ажиллахгүй"""
        from app.utils.westgard import check_westgard_rules
        values = [11.5, 11.3, 11.4]
        result = check_westgard_rules(values, 10.0, 1.0)
        rules = [v.rule for v in result]
        assert "4:1s" not in rules

    def test_4_1s_severity_reject(self):
        from app.utils.westgard import check_westgard_rules
        values = [11.5, 11.3, 11.4, 11.2]
        result = check_westgard_rules(values, 10.0, 1.0)
        assert any(v.severity == "reject" for v in result if v.rule == "4:1s")


class TestRule10x:
    """10x дүрмийн тест"""

    def test_10x_violation_positive(self):
        """10 дараалсан утга дунджийн дээд талд"""
        from app.utils.westgard import check_westgard_rules
        values = [10.1] * 10 + [9.5]  # All positive z for first 10
        result = check_westgard_rules(values, 10.0, 1.0)
        rules = [v.rule for v in result]
        assert "10x" in rules

    def test_10x_violation_negative(self):
        """10 дараалсан утга дунджийн доод талд"""
        from app.utils.westgard import check_westgard_rules
        values = [9.9] * 10 + [10.5]  # All negative z for first 10
        result = check_westgard_rules(values, 10.0, 1.0)
        rules = [v.rule for v in result]
        assert "10x" in rules

    def test_10x_not_all_same_side(self):
        """10 утга нэг талд биш"""
        from app.utils.westgard import check_westgard_rules
        values = [10.1, 9.9] * 5  # Alternating
        result = check_westgard_rules(values, 10.0, 1.0)
        rules = [v.rule for v in result]
        assert "10x" not in rules

    def test_10x_only_9_values(self):
        """9 утга - дүрэм ажиллахгүй"""
        from app.utils.westgard import check_westgard_rules
        values = [10.1] * 9
        result = check_westgard_rules(values, 10.0, 1.0)
        rules = [v.rule for v in result]
        assert "10x" not in rules

    def test_10x_severity_reject(self):
        from app.utils.westgard import check_westgard_rules
        values = [10.1] * 10
        result = check_westgard_rules(values, 10.0, 1.0)
        assert any(v.severity == "reject" for v in result if v.rule == "10x")


class TestGetQcStatus:
    """get_qc_status функцийн тест"""

    def test_no_violations(self):
        from app.utils.westgard import get_qc_status
        result = get_qc_status([])
        assert result["status"] == "pass"
        assert result["rules_violated"] == []
        assert "хэвийн" in result["message"]

    def test_warning_only(self):
        from app.utils.westgard import get_qc_status, WestgardViolation
        violations = [
            WestgardViolation(
                rule="1:2s",
                description="Test",
                severity="warning",
                values=[12.5],
                indices=[0]
            )
        ]
        result = get_qc_status(violations)
        assert result["status"] == "warning"
        assert "1:2s" in result["rules_violated"]
        assert "Анхааруулга" in result["message"]

    def test_reject(self):
        from app.utils.westgard import get_qc_status, WestgardViolation
        violations = [
            WestgardViolation(
                rule="1:3s",
                description="Test",
                severity="reject",
                values=[14.0],
                indices=[0]
            )
        ]
        result = get_qc_status(violations)
        assert result["status"] == "reject"
        assert "1:3s" in result["rules_violated"]
        assert "REJECT" in result["message"]

    def test_mixed_violations(self):
        """Warning + Reject = Reject"""
        from app.utils.westgard import get_qc_status, WestgardViolation
        violations = [
            WestgardViolation(
                rule="1:2s",
                description="Test",
                severity="warning",
                values=[12.5],
                indices=[0]
            ),
            WestgardViolation(
                rule="1:3s",
                description="Test",
                severity="reject",
                values=[14.0],
                indices=[1]
            )
        ]
        result = get_qc_status(violations)
        assert result["status"] == "reject"
        assert "1:2s" in result["rules_violated"]
        assert "1:3s" in result["rules_violated"]

    def test_duplicate_rules(self):
        """Давхардсан дүрмүүд"""
        from app.utils.westgard import get_qc_status, WestgardViolation
        violations = [
            WestgardViolation("1:3s", "Test1", "reject", [14], [0]),
            WestgardViolation("1:3s", "Test2", "reject", [15], [1])
        ]
        result = get_qc_status(violations)
        # Давхардсан дүрмүүд нэг л удаа жагсаалтад байна
        assert result["rules_violated"].count("1:3s") == 1


class TestCheckSingleValue:
    """check_single_value функцийн тест"""

    def test_zero_sd(self):
        from app.utils.westgard import check_single_value
        result = check_single_value(10.0, 10.0, 0)
        assert "error" in result

    def test_negative_sd(self):
        from app.utils.westgard import check_single_value
        result = check_single_value(10.0, 10.0, -1)
        assert "error" in result

    def test_ok_status(self):
        from app.utils.westgard import check_single_value
        result = check_single_value(10.5, 10.0, 1.0)
        assert result["status"] == "ok"
        assert result["in_1sd"] is True
        assert result["in_2sd"] is True
        assert result["in_3sd"] is True

    def test_warning_status(self):
        from app.utils.westgard import check_single_value
        result = check_single_value(12.5, 10.0, 1.0)  # z=2.5
        assert result["status"] == "warning"
        assert result["in_1sd"] is False
        assert result["in_2sd"] is False
        assert result["in_3sd"] is True

    def test_reject_status(self):
        from app.utils.westgard import check_single_value
        result = check_single_value(14.0, 10.0, 1.0)  # z=4
        assert result["status"] == "reject"
        assert result["in_1sd"] is False
        assert result["in_2sd"] is False
        assert result["in_3sd"] is False

    def test_z_score_calculation(self):
        from app.utils.westgard import check_single_value
        result = check_single_value(12.0, 10.0, 1.0)
        assert result["z_score"] == 2.0

    def test_deviation_calculation(self):
        from app.utils.westgard import check_single_value
        result = check_single_value(12.0, 10.0, 1.0)
        assert result["deviation"] == 2.0

    def test_value_returned(self):
        from app.utils.westgard import check_single_value
        result = check_single_value(12.5, 10.0, 1.0)
        assert result["value"] == 12.5

    def test_negative_z_score(self):
        from app.utils.westgard import check_single_value
        result = check_single_value(8.0, 10.0, 1.0)  # z=-2
        assert result["z_score"] == -2.0
        assert result["status"] == "ok"  # |z|=2, not > 2

    def test_exactly_at_boundaries(self):
        from app.utils.westgard import check_single_value
        # z = 1 exactly
        result = check_single_value(11.0, 10.0, 1.0)
        assert result["in_1sd"] is True

        # z = 2 exactly
        result = check_single_value(12.0, 10.0, 1.0)
        assert result["in_2sd"] is True
        assert result["status"] == "ok"

        # z = 3 exactly
        result = check_single_value(13.0, 10.0, 1.0)
        assert result["in_3sd"] is True
        assert result["status"] == "warning"
