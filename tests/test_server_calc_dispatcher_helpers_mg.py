# tests/test_server_calc_dispatcher_helpers_mg.py
# -*- coding: utf-8 -*-
"""
Comprehensive tests for server_calculations: _helpers, mg_calcs, dispatcher.
Target: 80%+ coverage for all three modules.
"""

import math
import pytest
from unittest.mock import patch, MagicMock

from app.utils.server_calculations._helpers import (
    cv_cal_to_mj,
    cv_mj_to_cal,
    _safe_float,
    _get_from_dict,
    MJ_PER_KCAL,
    J_PER_CAL,
    CALC_MISMATCH_ABS_THRESHOLD,
)
from app.utils.server_calculations.mg_calcs import (
    calc_mg_mt,
    calc_mg_trd,
    calc_mg_tube,
    calc_mg_size,
)


# ============================================================================
# _helpers.py tests
# ============================================================================

class TestCvCalToMj:
    """Tests for cv_cal_to_mj."""

    def test_basic_conversion(self):
        assert cv_cal_to_mj(1000) == pytest.approx(4.1868)

    def test_zero(self):
        assert cv_cal_to_mj(0) == 0.0

    def test_negative(self):
        assert cv_cal_to_mj(-500) == pytest.approx(-500 * MJ_PER_KCAL)

    def test_small_value(self):
        assert cv_cal_to_mj(0.001) == pytest.approx(0.001 * MJ_PER_KCAL)

    def test_large_value(self):
        assert cv_cal_to_mj(8000) == pytest.approx(8000 * MJ_PER_KCAL)


class TestCvMjToCal:
    """Tests for cv_mj_to_cal."""

    def test_basic_conversion(self):
        assert cv_mj_to_cal(4.1868) == pytest.approx(1000)

    def test_zero(self):
        assert cv_mj_to_cal(0) == 0.0

    def test_negative(self):
        assert cv_mj_to_cal(-2.0) == pytest.approx(-2.0 / MJ_PER_KCAL)

    def test_roundtrip(self):
        """Convert cal->mj->cal should return original."""
        original = 6500.0
        assert cv_mj_to_cal(cv_cal_to_mj(original)) == pytest.approx(original)


class TestSafeFloat:
    """Tests for _safe_float."""

    def test_int(self):
        assert _safe_float(42) == 42.0

    def test_float(self):
        assert _safe_float(3.14) == 3.14

    def test_string_number(self):
        assert _safe_float("99.5") == 99.5

    def test_none_returns_none(self):
        assert _safe_float(None) is None

    def test_nan_returns_none(self):
        assert _safe_float(float("nan")) is None

    def test_inf_returns_none(self):
        assert _safe_float(float("inf")) is None

    def test_neg_inf_returns_none(self):
        assert _safe_float(float("-inf")) is None

    def test_invalid_string_returns_none(self):
        assert _safe_float("abc") is None

    def test_empty_string_returns_none(self):
        assert _safe_float("") is None

    def test_list_returns_none(self):
        assert _safe_float([1, 2]) is None

    def test_zero(self):
        assert _safe_float(0) == 0.0

    def test_negative(self):
        assert _safe_float(-10) == -10.0

    def test_bool_true(self):
        # bool is subclass of int, float(True) == 1.0
        assert _safe_float(True) == 1.0

    def test_dict_returns_none(self):
        assert _safe_float({"a": 1}) is None


class TestGetFromDict:
    """Tests for _get_from_dict."""

    def test_single_key(self):
        assert _get_from_dict({"x": 5.0}, "x") == 5.0

    def test_nested_keys(self):
        d = {"p1": {"m1": 10.5}}
        assert _get_from_dict(d, "p1", "m1") == 10.5

    def test_missing_key_returns_none(self):
        assert _get_from_dict({"a": 1}, "b") is None

    def test_missing_nested_key_returns_none(self):
        assert _get_from_dict({"p1": {"m1": 5}}, "p1", "m2") is None

    def test_none_value_returns_none(self):
        assert _get_from_dict({"x": None}, "x") is None

    def test_intermediate_not_dict(self):
        d = {"p1": "not_a_dict"}
        assert _get_from_dict(d, "p1", "m1") is None

    def test_string_value_converted(self):
        assert _get_from_dict({"x": "3.14"}, "x") == pytest.approx(3.14)

    def test_invalid_leaf_returns_none(self):
        assert _get_from_dict({"x": "abc"}, "x") is None

    def test_deeply_nested(self):
        d = {"a": {"b": {"c": 42}}}
        assert _get_from_dict(d, "a", "b", "c") == 42.0

    def test_empty_dict(self):
        assert _get_from_dict({}, "x") is None


class TestConstants:
    """Test module-level constants exist and have correct values."""

    def test_mj_per_kcal(self):
        assert MJ_PER_KCAL == 0.0041868

    def test_j_per_cal(self):
        assert J_PER_CAL == 4.1868

    def test_mismatch_threshold(self):
        assert CALC_MISMATCH_ABS_THRESHOLD == 0.01


# ============================================================================
# mg_calcs.py tests
# ============================================================================

class TestCalcMgMt:
    """Tests for calc_mg_mt."""

    def test_normal_calculation(self):
        # Result% = ((m1 + m2 - m3) / m2) * 100
        # ((10 + 5 - 14) / 5) * 100 = (1/5)*100 = 20.0
        result = calc_mg_mt({"m1": 10, "m2": 5, "m3": 14})
        assert result == pytest.approx(20.0)

    def test_zero_moisture(self):
        # m1 + m2 == m3 => 0%
        result = calc_mg_mt({"m1": 10, "m2": 5, "m3": 15})
        assert result == pytest.approx(0.0)

    def test_missing_m1(self):
        assert calc_mg_mt({"m2": 5, "m3": 14}) is None

    def test_missing_m2(self):
        assert calc_mg_mt({"m1": 10, "m3": 14}) is None

    def test_missing_m3(self):
        assert calc_mg_mt({"m1": 10, "m2": 5}) is None

    def test_m2_zero(self):
        assert calc_mg_mt({"m1": 10, "m2": 0, "m3": 9}) is None

    def test_m2_negative(self):
        assert calc_mg_mt({"m1": 10, "m2": -1, "m3": 9}) is None

    def test_negative_result_returns_none(self):
        # ((10 + 5 - 20) / 5) * 100 = -100 => negative => None
        assert calc_mg_mt({"m1": 10, "m2": 5, "m3": 20}) is None

    def test_none_values(self):
        assert calc_mg_mt({"m1": None, "m2": 5, "m3": 14}) is None

    def test_string_numbers(self):
        result = calc_mg_mt({"m1": "10", "m2": "5", "m3": "14"})
        assert result == pytest.approx(20.0)

    def test_invalid_string(self):
        assert calc_mg_mt({"m1": "abc", "m2": 5, "m3": 14}) is None

    def test_typical_coal_moisture(self):
        # Realistic: crucible=25g, sample=1g, dried=25.95g => 5%
        result = calc_mg_mt({"m1": 25.0, "m2": 1.0, "m3": 25.95})
        assert result == pytest.approx(5.0)


class TestCalcMgTrd:
    """Tests for calc_mg_trd."""

    def test_single_parallel(self):
        # TRD = m / (m2 + m - m1) = 15 / (82 + 15 - 94) = 15/3 = 5.0
        raw = {"p1": {"m": 15, "m2": 82, "m1": 94}}
        result = calc_mg_trd(raw)
        assert result == pytest.approx(5.0)

    def test_two_parallels_averaged(self):
        raw = {
            "p1": {"m": 15, "m2": 82, "m1": 94},   # 15/3 = 5.0
            "p2": {"m": 10, "m2": 50, "m1": 55},    # 10/5 = 2.0
        }
        result = calc_mg_trd(raw)
        assert result == pytest.approx(3.5)  # (5+2)/2

    def test_missing_p1_uses_p2(self):
        raw = {"p2": {"m": 10, "m2": 50, "m1": 55}}
        result = calc_mg_trd(raw)
        assert result == pytest.approx(2.0)

    def test_no_parallels_returns_none(self):
        assert calc_mg_trd({}) is None

    def test_missing_field_in_parallel(self):
        raw = {"p1": {"m": 15, "m2": 82}}  # missing m1
        assert calc_mg_trd(raw) is None

    def test_zero_denominator(self):
        # m2 + m - m1 = 0 => skip
        raw = {"p1": {"m": 10, "m2": 50, "m1": 60}}  # 50+10-60=0
        assert calc_mg_trd(raw) is None

    def test_negative_denominator(self):
        raw = {"p1": {"m": 5, "m2": 30, "m1": 40}}  # 30+5-40=-5
        assert calc_mg_trd(raw) is None

    def test_none_parallel_dict(self):
        raw = {"p1": None, "p2": None}
        assert calc_mg_trd(raw) is None

    def test_one_valid_one_invalid(self):
        raw = {
            "p1": {"m": 15, "m2": 82, "m1": 94},  # valid => 5.0
            "p2": {"m": None, "m2": 50, "m1": 55},  # invalid
        }
        result = calc_mg_trd(raw)
        assert result == pytest.approx(5.0)

    def test_string_values(self):
        raw = {"p1": {"m": "15", "m2": "82", "m1": "94"}}
        assert calc_mg_trd(raw) == pytest.approx(5.0)


class TestCalcMgTube:
    """Tests for calc_mg_tube."""

    def test_normal_calculation(self):
        # MG% = 100 * (dried - empty) / sample = 100 * (12 - 10) / 5 = 40
        raw = {"empty_crucible": 10, "sample_mass": 5, "dried_weight": 12}
        assert calc_mg_tube(raw) == pytest.approx(40.0)

    def test_zero_mg(self):
        raw = {"empty_crucible": 10, "sample_mass": 5, "dried_weight": 10}
        assert calc_mg_tube(raw) == pytest.approx(0.0)

    def test_missing_field(self):
        assert calc_mg_tube({"empty_crucible": 10, "sample_mass": 5}) is None

    def test_sample_mass_zero(self):
        raw = {"empty_crucible": 10, "sample_mass": 0, "dried_weight": 12}
        assert calc_mg_tube(raw) is None

    def test_sample_mass_negative(self):
        raw = {"empty_crucible": 10, "sample_mass": -1, "dried_weight": 12}
        assert calc_mg_tube(raw) is None

    def test_negative_result_returns_none(self):
        # dried < empty => negative result => None
        raw = {"empty_crucible": 10, "sample_mass": 5, "dried_weight": 8}
        assert calc_mg_tube(raw) is None

    def test_none_values(self):
        raw = {"empty_crucible": None, "sample_mass": 5, "dried_weight": 12}
        assert calc_mg_tube(raw) is None

    def test_string_values(self):
        raw = {"empty_crucible": "10", "sample_mass": "5", "dried_weight": "12"}
        assert calc_mg_tube(raw) == pytest.approx(40.0)

    def test_realistic_values(self):
        # empty=25.1234, sample=1.0000, dried=25.4567 => 33.33%
        raw = {"empty_crucible": 25.1234, "sample_mass": 1.0, "dried_weight": 25.4567}
        expected = 100 * (25.4567 - 25.1234) / 1.0
        assert calc_mg_tube(raw) == pytest.approx(expected)


class TestCalcMgSize:
    """Tests for calc_mg_size."""

    def test_always_returns_none(self):
        assert calc_mg_size({}) is None

    def test_with_data_still_none(self):
        assert calc_mg_size({"fractions": [1, 2, 3]}) is None

    def test_with_empty_dict(self):
        assert calc_mg_size({}) is None


# ============================================================================
# dispatcher.py tests
# ============================================================================

class TestVerifyAndRecalculate:
    """Tests for verify_and_recalculate."""

    def _call(self, analysis_code, client_result, raw_data, user_id=1, sample_id=100):
        """Helper that patches norm_code for every call."""
        with patch(
            'app.utils.codes.norm_code',
            side_effect=lambda x: x,
        ):
            from app.utils.server_calculations.dispatcher import verify_and_recalculate
            return verify_and_recalculate(
                analysis_code, client_result, raw_data, user_id, sample_id
            )

    def test_no_calc_func_returns_client_value(self):
        """Unknown code => returns client value, no warnings."""
        result, warnings = self._call("UNKNOWN_CODE", 42.0, {})
        assert result == 42.0
        assert warnings == []

    def test_no_calc_func_none_client(self):
        """Unknown code with None client => returns None."""
        result, warnings = self._call("UNKNOWN_CODE", None, {})
        assert result is None
        assert warnings == []

    def test_known_code_server_calculates(self):
        """MG_SIZE always returns None => fallback to client."""
        result, warnings = self._call("MG_SIZE", 5.0, {})
        assert result == 5.0
        assert warnings == []

    def test_known_code_server_result_used(self):
        """MG code triggers calc_mg_tube, server result used."""
        raw = {"empty_crucible": 10, "sample_mass": 5, "dried_weight": 12}
        # Server calculates 40.0
        result, warnings = self._call("MG", 40.0, raw)
        assert result == pytest.approx(40.0)
        assert warnings == []

    def test_mismatch_detected(self):
        """Server and client differ significantly => warning."""
        raw = {"empty_crucible": 10, "sample_mass": 5, "dried_weight": 12}
        # Server = 40.0, client = 50.0 => 10.0 diff, 25% => mismatch
        result, warnings = self._call("MG", 50.0, raw)
        assert result == pytest.approx(40.0)  # server result used
        assert len(warnings) == 1
        assert "MISMATCH" in warnings[0]

    def test_small_difference_no_warning(self):
        """Tiny rounding difference => no warning."""
        raw = {"empty_crucible": 10, "sample_mass": 5, "dried_weight": 12}
        # Server = 40.0, client = 40.005 => diff=0.005 < 0.01 threshold
        result, warnings = self._call("MG", 40.005, raw)
        assert result == pytest.approx(40.0)
        assert warnings == []

    def test_calc_error_returns_client_with_warning(self):
        """If calc function raises, fallback to client with warning."""
        with patch(
            'app.utils.codes.norm_code',
            side_effect=lambda x: x,
        ), patch(
            'app.utils.server_calculations.dispatcher.CALCULATION_FUNCTIONS',
            {"BOOM": MagicMock(side_effect=ValueError("bad data"))},
        ):
            from app.utils.server_calculations.dispatcher import verify_and_recalculate
            result, warnings = verify_and_recalculate("BOOM", 99.0, {}, 1, 100)
            assert result == 99.0
            assert len(warnings) == 1
            assert "error" in warnings[0].lower()

    def test_calc_error_type_error(self):
        """TypeError in calc => fallback to client."""
        with patch(
            'app.utils.codes.norm_code',
            side_effect=lambda x: x,
        ), patch(
            'app.utils.server_calculations.dispatcher.CALCULATION_FUNCTIONS',
            {"ERR": MagicMock(side_effect=TypeError("oops"))},
        ):
            from app.utils.server_calculations.dispatcher import verify_and_recalculate
            result, warnings = verify_and_recalculate("ERR", 10.0, {}, 1, 1)
            assert result == 10.0
            assert len(warnings) == 1

    def test_calc_error_zero_division(self):
        """ZeroDivisionError in calc => fallback to client."""
        with patch(
            'app.utils.codes.norm_code',
            side_effect=lambda x: x,
        ), patch(
            'app.utils.server_calculations.dispatcher.CALCULATION_FUNCTIONS',
            {"DIV0": MagicMock(side_effect=ZeroDivisionError("div0"))},
        ):
            from app.utils.server_calculations.dispatcher import verify_and_recalculate
            result, warnings = verify_and_recalculate("DIV0", 7.0, {})
            assert result == 7.0
            assert len(warnings) == 1

    def test_server_none_client_none(self):
        """Both None => returns None."""
        result, warnings = self._call("MG_SIZE", None, {})
        assert result is None
        assert warnings == []

    def test_server_result_none_fallback_to_client(self):
        """Server returns None => use client value."""
        result, warnings = self._call("MG_SIZE", 12.5, {})
        assert result == 12.5

    def test_server_result_not_none_client_none(self):
        """Client None, server has value => use server."""
        raw = {"empty_crucible": 10, "sample_mass": 5, "dried_weight": 12}
        result, warnings = self._call("MG", None, raw)
        assert result == pytest.approx(40.0)
        assert warnings == []

    def test_percent_diff_exactly_at_boundary(self):
        """Diff > 0.01 abs but <= 1% relative => no warning."""
        # We need server and client to differ by >0.01 but <=1%
        # Server = 40.0, client = 40.0 + 0.02 = 40.02
        # diff = 0.02, percent = 0.02/40 * 100 = 0.05% < 1% => no warning
        raw = {"empty_crucible": 10, "sample_mass": 5, "dried_weight": 12}
        result, warnings = self._call("MG", 40.02, raw)
        assert result == pytest.approx(40.0)
        assert warnings == []


class TestBulkVerifyResults:
    """Tests for bulk_verify_results."""

    def _call(self, items, user_id=1):
        with patch(
            'app.utils.codes.norm_code',
            side_effect=lambda x: x,
        ):
            from app.utils.server_calculations.dispatcher import bulk_verify_results
            return bulk_verify_results(items, user_id)

    def test_empty_list(self):
        result = self._call([])
        assert result["verified_items"] == []
        assert result["total_warnings"] == 0
        assert result["total_mismatches"] == 0

    def test_single_item_no_calc(self):
        items = [{"analysis_code": "UNKNOWN", "final_result": 5.0, "raw_data": {}}]
        result = self._call(items)
        assert len(result["verified_items"]) == 1
        vi = result["verified_items"][0]
        assert vi["final_result"] == 5.0
        assert vi["server_verified"] is True
        assert vi["verification_warnings"] == []
        assert result["total_warnings"] == 0
        assert result["total_mismatches"] == 0

    def test_single_item_with_mismatch(self):
        raw = {"empty_crucible": 10, "sample_mass": 5, "dried_weight": 12}
        items = [{
            "analysis_code": "MG",
            "final_result": 99.0,  # Server=40 => big mismatch
            "raw_data": raw,
            "sample_id": 1,
        }]
        result = self._call(items)
        assert result["total_warnings"] == 1
        assert result["total_mismatches"] == 1
        vi = result["verified_items"][0]
        assert vi["final_result"] == pytest.approx(40.0)

    def test_multiple_items_mixed(self):
        items = [
            {"analysis_code": "UNKNOWN", "final_result": 10.0, "raw_data": {}},
            {
                "analysis_code": "MG",
                "final_result": 40.0,
                "raw_data": {"empty_crucible": 10, "sample_mass": 5, "dried_weight": 12},
                "sample_id": 2,
            },
            {"analysis_code": "MG_SIZE", "final_result": 3.0, "raw_data": {}},
        ]
        result = self._call(items)
        assert len(result["verified_items"]) == 3
        assert result["total_mismatches"] == 0

    def test_item_without_raw_data(self):
        """raw_data missing => defaults to {}."""
        items = [{"analysis_code": "MG_SIZE", "final_result": 1.0}]
        result = self._call(items)
        assert len(result["verified_items"]) == 1

    def test_preserves_original_fields(self):
        items = [{"analysis_code": "UNKNOWN", "final_result": 5.0, "raw_data": {}, "extra": "kept"}]
        result = self._call(items)
        assert result["verified_items"][0]["extra"] == "kept"

    def test_warnings_counted_correctly(self):
        """Multiple warnings from multiple items are summed."""
        with patch(
            'app.utils.codes.norm_code',
            side_effect=lambda x: x,
        ), patch(
            'app.utils.server_calculations.dispatcher.CALCULATION_FUNCTIONS',
            {"ERR": MagicMock(side_effect=ValueError("err"))},
        ):
            from app.utils.server_calculations.dispatcher import bulk_verify_results
            items = [
                {"analysis_code": "ERR", "final_result": 1.0, "raw_data": {}},
                {"analysis_code": "ERR", "final_result": 2.0, "raw_data": {}},
            ]
            result = bulk_verify_results(items, user_id=1)
            assert result["total_warnings"] == 2
            # These are "error" warnings, not "MISMATCH"
            assert result["total_mismatches"] == 0
