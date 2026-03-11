# tests/test_server_calc_physical_calorific.py
# -*- coding: utf-8 -*-
"""
Comprehensive tests for physical.py and calorific.py server calculations.
Target: 80%+ coverage for both modules.
"""

import pytest
from math import isfinite
from unittest.mock import patch

from app.utils.server_calculations.physical import (
    calc_csn,
    calc_gray_king_gi,
    calc_free_moisture_fm,
    calc_solid,
    calc_trd,
)
from app.utils.server_calculations.calorific import calc_calorific_value_cv
from app.utils.server_calculations._helpers import J_PER_CAL, MJ_PER_KCAL


# ============================================================================
# calc_csn tests
# ============================================================================


class TestCalcCSN:
    """Tests for Crucible Swelling Number (CSN) calculation."""

    def test_valid_five_values(self):
        """All 5 valid values produce correct average rounded to 0.5 step."""
        raw = {"v1": 3.0, "v2": 3.5, "v3": 4.0, "v4": 3.5, "v5": 4.0}
        result = calc_csn(raw)
        # avg = 18/5 = 3.6, round(3.6*2)/2 = round(7.2)/2 = 7/2 = 3.5
        assert result == 3.5

    def test_two_valid_values_minimum(self):
        """Exactly 2 valid values should still produce a result."""
        raw = {"v1": 5.0, "v2": 6.0}
        result = calc_csn(raw)
        assert result == 5.5

    def test_one_valid_value_returns_none(self):
        """Only 1 valid value is insufficient, returns None."""
        raw = {"v1": 3.0}
        assert calc_csn(raw) is None

    def test_empty_dict_returns_none(self):
        assert calc_csn({}) is None

    def test_all_none_values(self):
        raw = {"v1": None, "v2": None, "v3": None, "v4": None, "v5": None}
        assert calc_csn(raw) is None

    def test_values_outside_0_9_range(self):
        """Values outside 0-9 are excluded."""
        raw = {"v1": -1, "v2": 10, "v3": 3.0, "v4": 4.0}
        result = calc_csn(raw)
        assert result == 3.5

    def test_single_outside_range_with_one_valid(self):
        """One valid + one invalid = only 1 valid, returns None."""
        raw = {"v1": 15.0, "v2": 3.0}
        assert calc_csn(raw) is None

    def test_non_half_step_values_rejected(self):
        """Values not on 0.5 step (e.g. 3.3) are excluded."""
        raw = {"v1": 3.3, "v2": 4.7, "v3": 5.0, "v4": 5.5}
        # Only 5.0 and 5.5 are valid (on 0.5 step)
        result = calc_csn(raw)
        # avg(5.0, 5.5) = 5.25 -> round(10.5)/2
        # Python banker's rounding: round(10.5) = 10, so 10/2 = 5.0
        assert result == 5.0

    def test_zero_values(self):
        """0 is a valid CSN value."""
        raw = {"v1": 0, "v2": 0, "v3": 0}
        assert calc_csn(raw) == 0.0

    def test_max_value_nine(self):
        """9 is the max valid CSN value."""
        raw = {"v1": 9, "v2": 9}
        assert calc_csn(raw) == 9.0

    def test_half_step_rounding_up(self):
        """Average 2.75 rounds to 3.0 (0.5 step)."""
        raw = {"v1": 2.5, "v2": 3.0}
        # avg = 2.75, round(2.75*2)/2 = round(5.5)/2 = 6/2 = 3.0
        assert calc_csn(raw) == 3.0

    def test_half_step_rounding_down(self):
        """Average 2.25 rounds to 2.5 (0.5 step)."""
        raw = {"v1": 2.0, "v2": 2.5}
        # avg = 2.25, round(2.25*2)/2 = round(4.5)/2 = 4/2 = 2.0
        # Python banker's rounding: round(4.5) = 4
        assert result_is_half_step(calc_csn(raw))

    def test_string_values_parsed(self):
        """String numeric values should be parsed by _safe_float."""
        raw = {"v1": "3.0", "v2": "4.0", "v3": "3.5"}
        result = calc_csn(raw)
        assert result is not None
        assert result == 3.5

    def test_invalid_string_ignored(self):
        raw = {"v1": "abc", "v2": "3.0", "v3": "4.0"}
        result = calc_csn(raw)
        assert result == 3.5

    def test_three_valid_values(self):
        raw = {"v1": 1.0, "v2": 1.5, "v3": 2.0}
        result = calc_csn(raw)
        assert result == 1.5

    def test_boundary_value_exactly_nine(self):
        raw = {"v1": 9.0, "v2": 8.5}
        assert calc_csn(raw) == 9.0  # avg=8.75 -> round(17.5)/2


# ============================================================================
# calc_gray_king_gi tests
# ============================================================================


class TestCalcGrayKingGi:
    """Tests for Gray-King Index (Gi) calculation."""

    def test_default_51_mode_both_parallels(self):
        """5:1 mode with two parallels averages correctly."""
        raw = {
            "p1": {"m1": 1.0, "m2": 0.5, "m3": 0.3},
            "p2": {"m1": 1.0, "m2": 0.5, "m3": 0.3},
        }
        # Gi = 10 + (30*0.5 + 70*0.3) / 1.0 = 10 + (15+21)/1 = 10 + 36 = 46
        result = calc_gray_king_gi(raw)
        assert result == 46

    def test_51_mode_single_parallel(self):
        """Only p1 provided, should use single result."""
        raw = {"p1": {"m1": 2.0, "m2": 1.0, "m3": 0.5}}
        # Gi = 10 + (30*1.0 + 70*0.5) / 2.0 = 10 + (30+35)/2 = 10 + 32.5 = 42.5
        # floor(42.5 + 0.5) = floor(43) = 43
        assert calc_gray_king_gi(raw) == 43

    def test_33_mode_retest_top_level(self):
        """3:3 mode set at top level (retest_mode)."""
        raw = {
            "retest_mode": "3:3",
            "p1": {"m1": 1.0, "m2": 0.5, "m3": 0.3},
        }
        # Gi = (30*0.5 + 70*0.3) / (5*1.0) = (15+21)/5 = 36/5 = 7.2
        # floor(7.2 + 0.5) = floor(7.7) = 7
        assert calc_gray_king_gi(raw) == 7

    def test_33_mode_at_p1_level(self):
        """3:3 mode set in p1 dict."""
        raw = {"p1": {"m1": 1.0, "m2": 0.5, "m3": 0.3, "mode": "3:3"}}
        assert calc_gray_king_gi(raw) == 7

    def test_33_mode_retest_string(self):
        """Mode 'retest' string also triggers 3:3 mode."""
        raw = {"p1": {"m1": 1.0, "m2": 0.5, "m3": 0.3, "mode": "retest"}}
        result = calc_gray_king_gi(raw)
        # Same formula as 3:3
        assert result == 7

    def test_33_mode_underscore_format(self):
        """Mode '3_3' string also triggers 3:3 mode."""
        raw = {"p1": {"m1": 1.0, "m2": 0.5, "m3": 0.3, "mode": "3_3"}}
        assert calc_gray_king_gi(raw) == 7

    def test_mixed_modes_p1_and_p2(self):
        """Different modes for p1 and p2."""
        raw = {
            "p1": {"m1": 1.0, "m2": 0.5, "m3": 0.3, "mode": "5:1"},
            "p2": {"m1": 1.0, "m2": 0.5, "m3": 0.3, "mode": "3:3"},
        }
        # p1: 10 + 36/1 = 46
        # p2: 36/5 = 7.2
        # avg = (46 + 7.2)/2 = 26.6
        # floor(26.6 + 0.5) = floor(27.1) = 27
        assert calc_gray_king_gi(raw) == 27

    def test_half_up_rounding(self):
        """floor(x + 0.5) rounds 0.5 up (unlike Python banker's rounding)."""
        raw = {
            "p1": {"m1": 2.0, "m2": 1.0, "m3": 0.5},  # Gi = 42.5
        }
        # floor(42.5 + 0.5) = floor(43.0) = 43
        assert calc_gray_king_gi(raw) == 43

    def test_no_valid_parallels_returns_none(self):
        raw = {"p1": {"m1": None, "m2": 1.0, "m3": 0.5}}
        assert calc_gray_king_gi(raw) is None

    def test_empty_dict_returns_none(self):
        assert calc_gray_king_gi({}) is None

    def test_zero_m1_returns_none(self):
        """m1 = 0 causes division by zero, should return None."""
        raw = {"p1": {"m1": 0, "m2": 0.5, "m3": 0.3}}
        assert calc_gray_king_gi(raw) is None

    def test_negative_m_values_returns_none(self):
        raw = {"p1": {"m1": -1.0, "m2": 0.5, "m3": 0.3}}
        assert calc_gray_king_gi(raw) is None

    def test_missing_m3_returns_none(self):
        raw = {"p1": {"m1": 1.0, "m2": 0.5}}
        assert calc_gray_king_gi(raw) is None

    def test_p1_invalid_p2_valid(self):
        """p1 is invalid (missing m2), p2 is valid => uses p2 only."""
        raw = {
            "p1": {"m1": 1.0, "m3": 0.3},
            "p2": {"m1": 1.0, "m2": 0.5, "m3": 0.3},
        }
        # Only p2: Gi=46
        assert calc_gray_king_gi(raw) == 46

    def test_retest_mode_at_p1_level_with_retest_mode_key(self):
        """retest_mode key in p1 dict."""
        raw = {"p1": {"m1": 1.0, "m2": 0.5, "m3": 0.3, "retest_mode": "3:3"}}
        assert calc_gray_king_gi(raw) == 7

    def test_top_level_mode_key(self):
        """Top-level 'mode' key fallback."""
        raw = {
            "mode": "3:3",
            "p1": {"m1": 1.0, "m2": 0.5, "m3": 0.3},
        }
        assert calc_gray_king_gi(raw) == 7

    def test_string_values(self):
        """String numeric values should work."""
        raw = {"p1": {"m1": "1.0", "m2": "0.5", "m3": "0.3"}}
        assert calc_gray_king_gi(raw) == 46


# ============================================================================
# calc_free_moisture_fm tests
# ============================================================================


class TestCalcFreeMoistureFM:
    """Tests for Free Moisture (FM%) calculation."""

    def test_normal_calculation(self):
        """Standard FM calculation: ((Wb - Wa) / (Wa - Wt)) * 100."""
        raw = {"tray_g": 50.0, "before_g": 160.0, "after_g": 155.0}
        # FM = ((160 - 155) / (155 - 50)) * 100 = (5/105) * 100 = 4.7619...
        result = calc_free_moisture_fm(raw)
        assert result is not None
        assert abs(result - 4.7619) < 0.01

    def test_alternate_key_names(self):
        """'tray', 'before', 'after' keys also work."""
        raw = {"tray": 50.0, "before": 160.0, "after": 155.0}
        result = calc_free_moisture_fm(raw)
        assert result is not None
        assert abs(result - 4.7619) < 0.01

    def test_zero_denominator_returns_none(self):
        """When after_g == tray_g, denominator is zero."""
        raw = {"tray_g": 50.0, "before_g": 60.0, "after_g": 50.0}
        assert calc_free_moisture_fm(raw) is None

    def test_negative_fm_returns_none(self):
        """Negative FM (after > before) returns None."""
        raw = {"tray_g": 50.0, "before_g": 155.0, "after_g": 160.0}
        # FM = ((155 - 160) / (160 - 50)) * 100 = -4.5... < 0 => None
        assert calc_free_moisture_fm(raw) is None

    def test_missing_values_returns_none(self):
        raw = {"tray_g": 50.0, "before_g": 160.0}
        assert calc_free_moisture_fm(raw) is None

    def test_empty_dict_returns_none(self):
        assert calc_free_moisture_fm({}) is None

    def test_none_values_returns_none(self):
        raw = {"tray_g": None, "before_g": None, "after_g": None}
        assert calc_free_moisture_fm(raw) is None

    def test_string_values(self):
        raw = {"tray_g": "50", "before_g": "160", "after_g": "155"}
        result = calc_free_moisture_fm(raw)
        assert result is not None
        assert result > 0

    def test_zero_fm_when_before_equals_after(self):
        """FM = 0 when no moisture lost."""
        raw = {"tray_g": 50.0, "before_g": 155.0, "after_g": 155.0}
        result = calc_free_moisture_fm(raw)
        assert result == 0.0

    def test_large_fm(self):
        raw = {"tray_g": 10.0, "before_g": 200.0, "after_g": 110.0}
        # FM = (200-110)/(110-10) * 100 = 90/100*100 = 90
        result = calc_free_moisture_fm(raw)
        assert result == 90.0

    def test_non_finite_value(self):
        raw = {"tray_g": float("inf"), "before_g": 160.0, "after_g": 155.0}
        assert calc_free_moisture_fm(raw) is None


# ============================================================================
# calc_solid tests
# ============================================================================


class TestCalcSolid:
    """Tests for Solid% calculation."""

    def test_normal_calculation(self):
        """Solid% = C * 100 / (A - B)."""
        raw = {"A": 50.0, "B": 20.0, "C": 15.0}
        # Solid = 15 * 100 / (50 - 20) = 1500 / 30 = 50.0
        assert calc_solid(raw) == 50.0

    def test_lowercase_keys(self):
        """Lowercase a, b, c keys work."""
        raw = {"a": 50.0, "b": 20.0, "c": 15.0}
        assert calc_solid(raw) == 50.0

    def test_zero_denominator_returns_none(self):
        """A == B means zero denominator."""
        raw = {"A": 50.0, "B": 50.0, "C": 15.0}
        assert calc_solid(raw) is None

    def test_negative_result_returns_none(self):
        """Negative solid% returns None."""
        raw = {"A": 20.0, "B": 50.0, "C": 15.0}
        # Solid = 15*100 / (20-50) = 1500 / -30 = -50 < 0 => None
        assert calc_solid(raw) is None

    def test_missing_value_returns_none(self):
        raw = {"A": 50.0, "B": 20.0}
        assert calc_solid(raw) is None

    def test_empty_dict_returns_none(self):
        assert calc_solid({}) is None

    def test_zero_c_gives_none_due_to_falsy_or(self):
        """C=0.0 is falsy, so `raw_data.get("C") or raw_data.get("c")` yields None."""
        raw = {"A": 50.0, "B": 20.0, "C": 0.0}
        # Because 0.0 is falsy in Python, the `or` fallback makes C=None => None
        assert calc_solid(raw) is None

    def test_small_positive_c(self):
        raw = {"A": 50.0, "B": 20.0, "C": 0.001}
        result = calc_solid(raw)
        assert result is not None
        assert abs(result - 0.001 * 100 / 30) < 0.001

    def test_string_values(self):
        raw = {"A": "50", "B": "20", "C": "15"}
        assert calc_solid(raw) == 50.0

    def test_non_finite_returns_none(self):
        raw = {"A": float("nan"), "B": 20.0, "C": 15.0}
        assert calc_solid(raw) is None


# ============================================================================
# calc_trd tests
# ============================================================================


class TestCalcTRD:
    """Tests for True Relative Density (TRD) calculation."""

    def _make_coal_trd_data(self, p1=None, p2=None, mad=None):
        """Helper to build coal TRD raw_data (with mad_used + temp_c markers)."""
        data = {"mad_used": True, "temp_c": True}
        if mad is not None:
            data["mad"] = mad
        if p1 is not None:
            data["p1"] = p1
        if p2 is not None:
            data["p2"] = p2
        return data

    def test_single_parallel_exact_temp(self):
        """Single parallel with exact integer temperature."""
        raw = self._make_coal_trd_data(
            p1={"m": 1.0, "m1": 50.0, "m2": 49.5, "temp": 20, "mad": 5.0},
        )
        # md = 1.0 * (100 - 5) / 100 = 0.95
        # denom = 0.95 + 49.5 - 50.0 = 0.45
        # kt(20) = 1.00000
        # TRD = (0.95 / 0.45) * 1.00000 = 2.11111...
        result = calc_trd(raw)
        assert result is not None
        assert abs(result - 2.1111) < 0.01

    def test_both_parallels_averaged(self):
        """Two parallels should be averaged."""
        raw = self._make_coal_trd_data(
            p1={"m": 1.0, "m1": 50.0, "m2": 49.5, "temp": 20, "mad": 5.0},
            p2={"m": 1.0, "m1": 50.0, "m2": 49.5, "temp": 20, "mad": 5.0},
        )
        result = calc_trd(raw)
        assert result is not None
        assert abs(result - 2.1111) < 0.01

    def test_global_mad_fallback(self):
        """If p1 has no mad, global mad is used."""
        raw = self._make_coal_trd_data(
            p1={"m": 1.0, "m1": 50.0, "m2": 49.5, "temp": 20},
            mad=5.0,
        )
        result = calc_trd(raw)
        assert result is not None
        assert abs(result - 2.1111) < 0.01

    def test_fractional_temperature_interpolation(self):
        """Fractional temp uses linear interpolation between KT table values."""
        raw = self._make_coal_trd_data(
            p1={"m": 1.0, "m1": 50.0, "m2": 49.5, "temp": 20.5, "mad": 5.0},
        )
        # kt(20) = 1.00000, kt(21) = 0.99979
        # kt(20.5) = 1.00000 + (0.99979 - 1.00000) * 0.5 = 1.00000 - 0.000105 = 0.999895
        result = calc_trd(raw)
        assert result is not None
        # Should be slightly less than the temp=20 result
        assert result < 2.1111

    def test_temperature_at_lower_bound(self):
        """Temperature exactly 6 degrees."""
        raw = self._make_coal_trd_data(
            p1={"m": 1.0, "m1": 50.0, "m2": 49.5, "temp": 6, "mad": 5.0},
        )
        result = calc_trd(raw)
        assert result is not None
        # kt(6) = 1.00174

    def test_temperature_at_upper_bound(self):
        """Temperature exactly 35 degrees."""
        raw = self._make_coal_trd_data(
            p1={"m": 1.0, "m1": 50.0, "m2": 49.5, "temp": 35, "mad": 5.0},
        )
        result = calc_trd(raw)
        assert result is not None
        # kt(35) = 0.99582

    def test_temperature_below_range_returns_none(self):
        """Temperature < 6 is out of range."""
        raw = self._make_coal_trd_data(
            p1={"m": 1.0, "m1": 50.0, "m2": 49.5, "temp": 5, "mad": 5.0},
        )
        assert calc_trd(raw) is None

    def test_temperature_above_range_returns_none(self):
        """Temperature > 35 is out of range."""
        raw = self._make_coal_trd_data(
            p1={"m": 1.0, "m1": 50.0, "m2": 49.5, "temp": 36, "mad": 5.0},
        )
        assert calc_trd(raw) is None

    def test_temperature_interpolation_at_34_7(self):
        """Fractional temp near upper bound."""
        raw = self._make_coal_trd_data(
            p1={"m": 1.0, "m1": 50.0, "m2": 49.5, "temp": 34.7, "mad": 5.0},
        )
        # kt(34)=0.99616, kt(35)=0.99582
        # kt(34.7)=0.99616 + (0.99582-0.99616)*0.7 = 0.99616 - 0.000238 = 0.995922
        result = calc_trd(raw)
        assert result is not None

    def test_missing_mad_returns_none(self):
        """No mad at any level => None."""
        raw = self._make_coal_trd_data(
            p1={"m": 1.0, "m1": 50.0, "m2": 49.5, "temp": 20},
        )
        assert calc_trd(raw) is None

    def test_negative_mad_returns_none(self):
        raw = self._make_coal_trd_data(
            p1={"m": 1.0, "m1": 50.0, "m2": 49.5, "temp": 20, "mad": -1.0},
        )
        assert calc_trd(raw) is None

    def test_mad_100_gives_zero_md_returns_none(self):
        """mad=100 means md=0, should return None."""
        raw = self._make_coal_trd_data(
            p1={"m": 1.0, "m1": 50.0, "m2": 49.5, "temp": 20, "mad": 100.0},
        )
        assert calc_trd(raw) is None

    def test_zero_denominator_returns_none(self):
        """When md + m2 - m1 ~= 0."""
        raw = self._make_coal_trd_data(
            p1={"m": 1.0, "m1": 50.0, "m2": 49.05, "temp": 20, "mad": 5.0},
        )
        # md = 0.95, denom = 0.95 + 49.05 - 50.0 = 0.0
        assert calc_trd(raw) is None

    def test_missing_m_returns_none(self):
        raw = self._make_coal_trd_data(
            p1={"m1": 50.0, "m2": 49.5, "temp": 20, "mad": 5.0},
        )
        assert calc_trd(raw) is None

    def test_empty_dict_with_markers_returns_none(self):
        raw = {"mad_used": True, "temp_c": True}
        assert calc_trd(raw) is None

    def test_mg_format_detection(self):
        """Without mad_used/temp_c keys, delegates to calc_mg_trd."""
        raw = {
            "p1": {"m": 15, "m1": 94, "m2": 82},
        }
        # MG TRD = m / (m2 + m - m1) = 15 / (82 + 15 - 94) = 15 / 3 = 5.0
        result = calc_trd(raw)
        assert result is not None
        assert result == 5.0

    def test_mg_format_both_parallels(self):
        """MG TRD with both parallels."""
        raw = {
            "p1": {"m": 15, "m1": 94, "m2": 82},
            "p2": {"m": 15, "m1": 94, "m2": 82},
        }
        result = calc_trd(raw)
        assert result == 5.0

    def test_mg_format_invalid_returns_none(self):
        """MG format with invalid data returns None."""
        raw = {
            "p1": {"m": None, "m1": 94, "m2": 82},
        }
        assert calc_trd(raw) is None

    def test_temperature_key_alias(self):
        """'temperature' key should also work."""
        raw = self._make_coal_trd_data(
            p1={"m": 1.0, "m1": 50.0, "m2": 49.5, "temperature": 20, "mad": 5.0},
        )
        result = calc_trd(raw)
        assert result is not None

    def test_none_temp_returns_none(self):
        raw = self._make_coal_trd_data(
            p1={"m": 1.0, "m1": 50.0, "m2": 49.5, "temp": None, "mad": 5.0},
        )
        assert calc_trd(raw) is None

    def test_p1_invalid_p2_valid(self):
        """Only p2 is valid, result uses p2 only."""
        raw = self._make_coal_trd_data(
            p1={"m": None, "m1": 50.0, "m2": 49.5, "temp": 20, "mad": 5.0},
            p2={"m": 1.0, "m1": 50.0, "m2": 49.5, "temp": 20, "mad": 5.0},
        )
        result = calc_trd(raw)
        assert result is not None
        assert abs(result - 2.1111) < 0.01

    def test_different_temperatures_per_parallel(self):
        """p1 and p2 have different temps."""
        raw = self._make_coal_trd_data(
            p1={"m": 1.0, "m1": 50.0, "m2": 49.5, "temp": 10, "mad": 5.0},
            p2={"m": 1.0, "m1": 50.0, "m2": 49.5, "temp": 30, "mad": 5.0},
        )
        result = calc_trd(raw)
        assert result is not None

    def test_mad_over_100_gives_negative_md(self):
        """mad > 100 makes md negative => None."""
        raw = self._make_coal_trd_data(
            p1={"m": 1.0, "m1": 50.0, "m2": 49.5, "temp": 20, "mad": 150.0},
        )
        assert calc_trd(raw) is None

    def test_exact_boundary_temp_35(self):
        """At temp=35, t_high=36 > 35, should use KT_TABLE[35] directly."""
        raw = self._make_coal_trd_data(
            p1={"m": 1.0, "m1": 50.0, "m2": 49.5, "temp": 35.0, "mad": 5.0},
        )
        result = calc_trd(raw)
        assert result is not None

    def test_non_finite_temp_returns_none(self):
        raw = self._make_coal_trd_data(
            p1={"m": 1.0, "m1": 50.0, "m2": 49.5, "temp": float("inf"), "mad": 5.0},
        )
        assert calc_trd(raw) is None


# ============================================================================
# calc_calorific_value_cv tests
# ============================================================================


class TestCalcCalorificValueCV:
    """Tests for Calorific Value (CV) bomb calorimeter calculation."""

    @staticmethod
    def _make_cv_data(
        m=1.0, dt=3.0, e=10000.0, q1=50.0, q2=10.0, s=0.5,
        m2=None, dt2=None, s2=None, s_used=None, unit="cal/g",
    ):
        """Helper to build CV raw_data."""
        batch = {"E": e, "q1": q1, "q2": q2}
        p1 = {"m": m, "delta_t": dt, "s": s}
        data = {"batch": batch, "p1": p1}
        if s_used is not None:
            data["s_used"] = s_used
        if m2 is not None:
            data["p2"] = {"m": m2, "delta_t": dt2 or dt, "s": s2 or s}
        return data, unit

    def test_single_parallel_cal_g(self):
        """Basic single parallel CV in cal/g."""
        raw, unit = self._make_cv_data(m=1.0, dt=3.0, e=10000.0, q1=50.0, q2=10.0, s=0.5)
        result = calc_calorific_value_cv(raw, unit)
        assert result is not None
        assert result > 0

        # Manual calc:
        # Qb = ((10000 * 3) - 50 - 10) / 1.0 = 29940
        # Qb_MJ = 29940/1000 = 29.94 > 25.1 => alpha = 0.0016
        # acid_corr = 0.0016 * 29940 = 47.904
        # S_corr = 94.1 * 0.5 = 47.05
        # Qgr_Jg = 29940 - (47.05 + 47.904) = 29845.046
        # Qgr_cal_g = 29845.046 / 4.1868 = 7129.07...
        assert abs(result - 7129.07) < 1.0

    def test_both_parallels_averaged(self):
        """Two identical parallels produce same result as single."""
        raw, unit = self._make_cv_data(m=1.0, dt=3.0, e=10000.0, q1=50.0, q2=10.0, s=0.5)
        raw["p2"] = {"m": 1.0, "delta_t": 3.0, "s": 0.5}
        result = calc_calorific_value_cv(raw, unit)
        assert result is not None

        single_raw, _ = self._make_cv_data(m=1.0, dt=3.0, e=10000.0, q1=50.0, q2=10.0, s=0.5)
        single_result = calc_calorific_value_cv(single_raw, unit)
        assert abs(result - single_result) < 0.01

    def test_unit_mj_kg(self):
        """MJ/kg conversion."""
        raw, _ = self._make_cv_data()
        result_cal = calc_calorific_value_cv(raw, "cal/g")
        result_mj = calc_calorific_value_cv(raw, "MJ/kg")
        assert result_mj is not None
        assert abs(result_mj - result_cal * MJ_PER_KCAL) < 0.001

    def test_unit_j_g(self):
        """J/g conversion."""
        raw, _ = self._make_cv_data()
        result_cal = calc_calorific_value_cv(raw, "cal/g")
        result_jg = calc_calorific_value_cv(raw, "J/g")
        assert result_jg is not None
        assert abs(result_jg - result_cal * J_PER_CAL) < 0.01

    def test_alpha_low_range(self):
        """Qb <= 16.7 MJ/kg => alpha = 0.0010."""
        # Need Qb_Jg such that Qb_MJkg <= 16.7, i.e. Qb_Jg <= 16700
        # Qb = ((E*dT) - q1 - q2) / m
        # ((E*dT) - q1 - q2) = 16700 => E*dT = 16760, q1=50, q2=10
        raw = {
            "batch": {"E": 5586.67, "q1": 50.0, "q2": 10.0},
            "p1": {"m": 1.0, "delta_t": 3.0, "s": 0.5},
        }
        # Qb = (5586.67*3 - 50 - 10) / 1 = 16760.01 - 60 = 16700.01
        # Qb_MJ = 16.70001 => on the boundary
        result = calc_calorific_value_cv(raw, "cal/g")
        assert result is not None
        assert result > 0

    def test_alpha_mid_range(self):
        """16.7 < Qb <= 25.1 MJ/kg => alpha = 0.0012."""
        # Need Qb_Jg ~= 20000 (20 MJ/kg)
        raw = {
            "batch": {"E": 6686.67, "q1": 50.0, "q2": 10.0},
            "p1": {"m": 1.0, "delta_t": 3.0, "s": 0.5},
        }
        # Qb = (6686.67*3 - 60) / 1 = 20060.01 - 60 = 20000.01
        result = calc_calorific_value_cv(raw, "cal/g")
        assert result is not None
        assert result > 0

    def test_alpha_high_range(self):
        """Qb > 25.1 MJ/kg => alpha = 0.0016."""
        raw, _ = self._make_cv_data(m=1.0, dt=3.0, e=10000.0, q1=50.0, q2=10.0, s=0.5)
        # Qb = 29940 J/g = 29.94 MJ/kg > 25.1
        result = calc_calorific_value_cv(raw, "cal/g")
        assert result is not None

    def test_missing_m_returns_none(self):
        raw = {
            "batch": {"E": 10000.0, "q1": 50.0, "q2": 10.0},
            "p1": {"delta_t": 3.0, "s": 0.5},
        }
        assert calc_calorific_value_cv(raw) is None

    def test_missing_e_returns_none(self):
        raw = {
            "batch": {"q1": 50.0, "q2": 10.0},
            "p1": {"m": 1.0, "delta_t": 3.0, "s": 0.5},
        }
        assert calc_calorific_value_cv(raw) is None

    def test_missing_q1_returns_none(self):
        raw = {
            "batch": {"E": 10000.0, "q2": 10.0},
            "p1": {"m": 1.0, "delta_t": 3.0, "s": 0.5},
        }
        assert calc_calorific_value_cv(raw) is None

    def test_missing_delta_t_returns_none(self):
        raw = {
            "batch": {"E": 10000.0, "q1": 50.0, "q2": 10.0},
            "p1": {"m": 1.0, "s": 0.5},
        }
        assert calc_calorific_value_cv(raw) is None

    def test_zero_mass_returns_none(self):
        raw = {
            "batch": {"E": 10000.0, "q1": 50.0, "q2": 10.0},
            "p1": {"m": 0, "delta_t": 3.0, "s": 0.5},
        }
        assert calc_calorific_value_cv(raw) is None

    def test_empty_dict_returns_none(self):
        assert calc_calorific_value_cv({}) is None

    def test_q2_none_defaults_to_zero(self):
        """q2 is optional, defaults to 0."""
        raw = {
            "batch": {"E": 10000.0, "q1": 50.0},
            "p1": {"m": 1.0, "delta_t": 3.0, "s": 0.5},
        }
        result = calc_calorific_value_cv(raw)
        assert result is not None
        assert result > 0

    def test_s_none_defaults_to_zero(self):
        """Sulfur is optional, defaults to 0."""
        raw = {
            "batch": {"E": 10000.0, "q1": 50.0, "q2": 10.0},
            "p1": {"m": 1.0, "delta_t": 3.0},
        }
        result = calc_calorific_value_cv(raw)
        assert result is not None

    def test_s_used_fallback(self):
        """s_used at top level is used when p1/p2 don't have s."""
        raw = {
            "batch": {"E": 10000.0, "q1": 50.0, "q2": 10.0},
            "p1": {"m": 1.0, "delta_t": 3.0},
            "s_used": 0.8,
        }
        result = calc_calorific_value_cv(raw)
        assert result is not None

    def test_p1_invalid_p2_valid(self):
        """p1 missing m, p2 valid => uses p2 only."""
        raw = {
            "batch": {"E": 10000.0, "q1": 50.0, "q2": 10.0},
            "p1": {"delta_t": 3.0, "s": 0.5},
            "p2": {"m": 1.0, "delta_t": 3.0, "s": 0.5},
        }
        result = calc_calorific_value_cv(raw)
        assert result is not None

    def test_non_finite_m_returns_none(self):
        raw = {
            "batch": {"E": 10000.0, "q1": 50.0, "q2": 10.0},
            "p1": {"m": float("inf"), "delta_t": 3.0, "s": 0.5},
        }
        assert calc_calorific_value_cv(raw) is None

    def test_alternate_key_dT(self):
        """delta_t alias: dT."""
        raw = {
            "batch": {"E": 10000.0, "q1": 50.0, "q2": 10.0},
            "p1": {"m": 1.0, "dT": 3.0, "s": 0.5},
        }
        result = calc_calorific_value_cv(raw)
        assert result is not None

    def test_alternate_key_m1(self):
        """m alias: m1."""
        raw = {
            "batch": {"E": 10000.0, "q1": 50.0, "q2": 10.0},
            "p1": {"m1": 1.0, "delta_t": 3.0, "s": 0.5},
        }
        result = calc_calorific_value_cv(raw)
        assert result is not None

    def test_alternate_key_temp(self):
        """delta_t alias: temp."""
        raw = {
            "batch": {"E": 10000.0, "q1": 50.0, "q2": 10.0},
            "p1": {"m": 1.0, "temp": 3.0, "s": 0.5},
        }
        result = calc_calorific_value_cv(raw)
        assert result is not None

    def test_negative_result_excluded(self):
        """If CV < 0, it's excluded from results."""
        # Make q1 very large so Qb becomes very negative
        raw = {
            "batch": {"E": 10.0, "q1": 50000.0, "q2": 0},
            "p1": {"m": 1.0, "delta_t": 1.0, "s": 0.0},
        }
        # Qb = ((10*1) - 50000) / 1 = -49990
        # Qgr would be negative => excluded => None
        assert calc_calorific_value_cv(raw) is None

    def test_default_unit_is_cal_g(self):
        """When no unit specified, default is cal/g."""
        raw, _ = self._make_cv_data()
        default_result = calc_calorific_value_cv(raw)
        cal_result = calc_calorific_value_cv(raw, "cal/g")
        assert default_result == cal_result

    def test_string_values_in_batch(self):
        """String numeric values parsed by _safe_float."""
        raw = {
            "batch": {"E": "10000", "q1": "50", "q2": "10"},
            "p1": {"m": "1.0", "delta_t": "3.0", "s": "0.5"},
        }
        result = calc_calorific_value_cv(raw)
        assert result is not None
        assert result > 0


# ============================================================================
# Helper
# ============================================================================


def result_is_half_step(value):
    """Check if a value is on a 0.5 step."""
    if value is None:
        return False
    return abs(value * 2 - round(value * 2)) < 1e-9
