# tests/test_server_calc_proximate_ultimate.py
# -*- coding: utf-8 -*-
"""
Comprehensive tests for proximate.py and ultimate.py server calculations.
Target: 80%+ coverage on both files.
"""

import pytest
from unittest.mock import patch

from app.utils.server_calculations.proximate import (
    calc_moisture_mad,
    calc_ash_aad,
    calc_volatile_vad,
    calc_total_moisture_mt,
)
from app.utils.server_calculations.ultimate import (
    calc_sulfur_ts,
    calc_phosphorus_p,
    calc_fluorine_f,
    calc_chlorine_cl,
)


# ============================================================================
# calc_moisture_mad
# Formula: Mad% = ((m1 + m2) - m3) / m2 * 100
# ============================================================================

class TestCalcMoistureMad:
    """Tests for calc_moisture_mad."""

    def test_both_parallels(self):
        """Normal case with two parallels, result is average."""
        raw = {
            "p1": {"m1": 20.0, "m2": 1.0, "m3": 20.9},
            "p2": {"m1": 21.0, "m2": 1.0, "m3": 21.92},
        }
        # p1: (20+1-20.9)/1*100 = 10.0
        # p2: (21+1-21.92)/1*100 = 8.0
        # avg = 9.0
        result = calc_moisture_mad(raw)
        assert result == pytest.approx(9.0)

    def test_p1_only(self):
        """Only p1 provided."""
        raw = {"p1": {"m1": 20.0, "m2": 1.0, "m3": 20.95}}
        result = calc_moisture_mad(raw)
        assert result == pytest.approx(5.0)

    def test_p2_only(self):
        """Only p2 provided."""
        raw = {"p2": {"m1": 20.0, "m2": 2.0, "m3": 21.8}}
        # (20+2-21.8)/2*100 = 0.2/2*100 = 10.0
        result = calc_moisture_mad(raw)
        assert result == pytest.approx(10.0)

    def test_empty_dict(self):
        """Empty raw_data returns None."""
        assert calc_moisture_mad({}) is None

    def test_missing_m3(self):
        """Missing m3 in p1 skips that parallel."""
        raw = {"p1": {"m1": 20.0, "m2": 1.0}}
        assert calc_moisture_mad(raw) is None

    def test_m2_zero_divisor(self):
        """m2=0 should skip that parallel (division by zero guard)."""
        raw = {"p1": {"m1": 20.0, "m2": 0, "m3": 20.5}}
        assert calc_moisture_mad(raw) is None

    def test_m2_negative(self):
        """m2 negative should skip (m2 > 0 check)."""
        raw = {"p1": {"m1": 20.0, "m2": -1.0, "m3": 20.5}}
        assert calc_moisture_mad(raw) is None

    def test_negative_weight_loss(self):
        """wet_weight_loss < 0 means m3 > m1+m2, should skip."""
        raw = {"p1": {"m1": 20.0, "m2": 1.0, "m3": 22.0}}
        # (20+1-22)/1*100 = -100 => weight_loss=-1 < 0 => skip
        assert calc_moisture_mad(raw) is None

    def test_none_values_in_parallel(self):
        """None values in a parallel should skip it."""
        raw = {"p1": {"m1": None, "m2": 1.0, "m3": 20.5}}
        assert calc_moisture_mad(raw) is None

    def test_zero_weight_loss(self):
        """weight_loss == 0 is valid (>= 0), result is 0%."""
        raw = {"p1": {"m1": 20.0, "m2": 1.0, "m3": 21.0}}
        # (20+1-21)/1*100 = 0
        assert calc_moisture_mad(raw) == pytest.approx(0.0)

    def test_string_values_converted(self):
        """String numeric values are converted by _get_from_dict."""
        raw = {"p1": {"m1": "20.0", "m2": "1.0", "m3": "20.9"}}
        result = calc_moisture_mad(raw)
        assert result == pytest.approx(10.0)

    def test_one_parallel_valid_one_invalid(self):
        """One valid, one invalid parallel => returns only valid."""
        raw = {
            "p1": {"m1": 20.0, "m2": 1.0, "m3": 20.9},
            "p2": {"m1": None, "m2": 1.0, "m3": 20.9},
        }
        result = calc_moisture_mad(raw)
        assert result == pytest.approx(10.0)


# ============================================================================
# calc_ash_aad
# Formula: Aad% = (m3 - m1) / m2 * 100
# ============================================================================

class TestCalcAshAad:
    """Tests for calc_ash_aad."""

    def test_both_parallels(self):
        """Normal two-parallel case."""
        raw = {
            "p1": {"m1": 20.0, "m2": 1.0, "m3": 20.1},
            "p2": {"m1": 21.0, "m2": 1.0, "m3": 21.12},
        }
        # p1: (20.1-20)/1*100 = 10.0
        # p2: (21.12-21)/1*100 = 12.0
        # avg = 11.0
        result = calc_ash_aad(raw)
        assert result == pytest.approx(11.0)

    def test_p1_only(self):
        raw = {"p1": {"m1": 20.0, "m2": 1.0, "m3": 20.15}}
        # (20.15-20)/1*100 = 15.0
        assert calc_ash_aad(raw) == pytest.approx(15.0)

    def test_p2_only(self):
        raw = {"p2": {"m1": 10.0, "m2": 2.0, "m3": 10.4}}
        # (10.4-10)/2*100 = 20.0
        assert calc_ash_aad(raw) == pytest.approx(20.0)

    def test_empty_dict(self):
        assert calc_ash_aad({}) is None

    def test_negative_result_skipped(self):
        """m3 < m1 means ash% < 0, should skip."""
        raw = {"p1": {"m1": 20.0, "m2": 1.0, "m3": 19.5}}
        # (19.5-20)/1*100 = -50 => skip
        assert calc_ash_aad(raw) is None

    def test_zero_m2(self):
        """m2=0 fails the `all(x > 0)` check."""
        raw = {"p1": {"m1": 20.0, "m2": 0, "m3": 20.1}}
        assert calc_ash_aad(raw) is None

    def test_zero_m1(self):
        """m1=0 fails the `all(x > 0)` check."""
        raw = {"p1": {"m1": 0, "m2": 1.0, "m3": 0.1}}
        assert calc_ash_aad(raw) is None

    def test_none_value(self):
        raw = {"p1": {"m1": 20.0, "m2": None, "m3": 20.1}}
        assert calc_ash_aad(raw) is None

    def test_zero_ash(self):
        """m3 == m1 => 0% ash."""
        raw = {"p1": {"m1": 20.0, "m2": 1.0, "m3": 20.0}}
        assert calc_ash_aad(raw) == pytest.approx(0.0)


# ============================================================================
# calc_volatile_vad
# Formula: Vad% = ((m1 + m2 - m3) / m2) * 100 - mad_used
# ============================================================================

class TestCalcVolatileVad:
    """Tests for calc_volatile_vad."""

    def test_both_parallels_with_mad(self):
        raw = {
            "p1": {"m1": 20.0, "m2": 1.0, "m3": 20.6},
            "p2": {"m1": 21.0, "m2": 1.0, "m3": 21.58},
            "mad_used": 5.0,
        }
        # p1: (20+1-20.6)/1*100 = 40 - 5 = 35
        # p2: (21+1-21.58)/1*100 = 42 - 5 = 37
        # avg = 36.0
        result = calc_volatile_vad(raw)
        assert result == pytest.approx(36.0)

    def test_without_mad_used(self):
        """No mad_used => no subtraction."""
        raw = {"p1": {"m1": 20.0, "m2": 1.0, "m3": 20.6}}
        # (20+1-20.6)/1*100 = 40.0
        result = calc_volatile_vad(raw)
        assert result == pytest.approx(40.0)

    def test_mad_used_none(self):
        """mad_used=None => no subtraction."""
        raw = {"p1": {"m1": 20.0, "m2": 1.0, "m3": 20.6}, "mad_used": None}
        result = calc_volatile_vad(raw)
        assert result == pytest.approx(40.0)

    def test_p1_only(self):
        raw = {
            "p1": {"m1": 20.0, "m2": 1.0, "m3": 20.7},
            "mad_used": 3.0,
        }
        # (20+1-20.7)/1*100 = 30 - 3 = 27
        assert calc_volatile_vad(raw) == pytest.approx(27.0)

    def test_p2_only(self):
        raw = {
            "p2": {"m1": 20.0, "m2": 2.0, "m3": 21.4},
            "mad_used": 2.0,
        }
        # (20+2-21.4)/2*100 = 0.6/2*100 = 30 - 2 = 28
        assert calc_volatile_vad(raw) == pytest.approx(28.0)

    def test_empty_dict(self):
        assert calc_volatile_vad({}) is None

    def test_m2_zero(self):
        raw = {"p1": {"m1": 20.0, "m2": 0, "m3": 20.5}, "mad_used": 1.0}
        assert calc_volatile_vad(raw) is None

    def test_negative_weight_loss_skipped(self):
        """m3 > m1+m2 => weight_loss < 0 => skip."""
        raw = {"p1": {"m1": 20.0, "m2": 1.0, "m3": 22.0}, "mad_used": 1.0}
        assert calc_volatile_vad(raw) is None

    def test_result_clamped_to_zero(self):
        """If result after subtracting mad goes negative, clamp to 0."""
        raw = {
            "p1": {"m1": 20.0, "m2": 1.0, "m3": 20.98},
            "mad_used": 10.0,
        }
        # (20+1-20.98)/1*100 = 2.0 - 10.0 = -8 => clamped to 0
        result = calc_volatile_vad(raw)
        assert result == pytest.approx(0.0)

    def test_none_m1(self):
        raw = {"p1": {"m1": None, "m2": 1.0, "m3": 20.5}}
        assert calc_volatile_vad(raw) is None

    def test_mad_used_string(self):
        """mad_used as string should be converted by _safe_float."""
        raw = {
            "p1": {"m1": 20.0, "m2": 1.0, "m3": 20.6},
            "mad_used": "5.0",
        }
        result = calc_volatile_vad(raw)
        assert result == pytest.approx(35.0)

    def test_both_parallels_no_mad(self):
        """Two parallels, no mad_used key at all."""
        raw = {
            "p1": {"m1": 20.0, "m2": 1.0, "m3": 20.6},
            "p2": {"m1": 21.0, "m2": 1.0, "m3": 21.58},
        }
        # p1: 40.0, p2: 42.0 => avg 41.0
        result = calc_volatile_vad(raw)
        assert result == pytest.approx(41.0)

    def test_p2_result_clamped_to_zero(self):
        """Ensure p2 result is also clamped to 0 when negative after mad subtraction."""
        raw = {
            "p1": {"m1": 20.0, "m2": 1.0, "m3": 20.6},  # 40 - 50 = -10 => 0
            "p2": {"m1": 21.0, "m2": 1.0, "m3": 21.98},  # 2 - 50 = -48 => 0
            "mad_used": 50.0,
        }
        result = calc_volatile_vad(raw)
        assert result == pytest.approx(0.0)


# ============================================================================
# calc_total_moisture_mt
# Formula: MT% = ((m2 - m3) / (m2 - m1)) * 100
# Also supports MG flat format delegation
# ============================================================================

class TestCalcTotalMoistureMt:
    """Tests for calc_total_moisture_mt."""

    def test_both_parallels(self):
        raw = {
            "p1": {"m1": 100.0, "m2": 200.0, "m3": 190.0},
            "p2": {"m1": 100.0, "m2": 200.0, "m3": 188.0},
        }
        # p1: (200-190)/(200-100)*100 = 10/100*100 = 10.0
        # p2: (200-188)/(200-100)*100 = 12/100*100 = 12.0
        # avg = 11.0
        result = calc_total_moisture_mt(raw)
        assert result == pytest.approx(11.0)

    def test_p1_only(self):
        raw = {"p1": {"m1": 100.0, "m2": 200.0, "m3": 180.0}}
        # (200-180)/(200-100)*100 = 20.0
        assert calc_total_moisture_mt(raw) == pytest.approx(20.0)

    def test_p2_only(self):
        raw = {"p2": {"m1": 50.0, "m2": 150.0, "m3": 140.0}}
        # (150-140)/(150-50)*100 = 10.0
        assert calc_total_moisture_mt(raw) == pytest.approx(10.0)

    def test_empty_dict(self):
        assert calc_total_moisture_mt({}) is None

    def test_zero_sample_mass(self):
        """m2 == m1 => sample_mass=0 => skip."""
        raw = {"p1": {"m1": 100.0, "m2": 100.0, "m3": 99.0}}
        assert calc_total_moisture_mt(raw) is None

    def test_negative_result_skipped(self):
        """m3 > m2 => result < 0 => skip."""
        raw = {"p1": {"m1": 100.0, "m2": 200.0, "m3": 210.0}}
        assert calc_total_moisture_mt(raw) is None

    def test_zero_m1(self):
        """m1=0 fails `all(x > 0)` check."""
        raw = {"p1": {"m1": 0, "m2": 200.0, "m3": 190.0}}
        assert calc_total_moisture_mt(raw) is None

    def test_none_value(self):
        raw = {"p1": {"m1": 100.0, "m2": None, "m3": 190.0}}
        assert calc_total_moisture_mt(raw) is None

    def test_mg_flat_format(self):
        """Flat m1/m2/m3 without p1 => delegates to calc_mg_mt."""
        raw = {"m1": 20.0, "m2": 1.0, "m3": 20.95}
        # calc_mg_mt: (20+1-20.95)/1*100 = 5.0
        result = calc_total_moisture_mt(raw)
        assert result == pytest.approx(5.0)

    def test_mg_flat_format_invalid(self):
        """Flat format with m2=0 => calc_mg_mt returns None."""
        raw = {"m1": 20.0, "m2": 0, "m3": 20.5}
        assert calc_total_moisture_mt(raw) is None

    def test_not_flat_when_p1_present(self):
        """Has m1/m2/m3 AND p1 => NOT flat format, uses standard path."""
        raw = {
            "m1": 99, "m2": 99, "m3": 99,
            "p1": {"m1": 100.0, "m2": 200.0, "m3": 190.0},
        }
        result = calc_total_moisture_mt(raw)
        assert result == pytest.approx(10.0)

    def test_one_valid_one_invalid_parallel(self):
        raw = {
            "p1": {"m1": 100.0, "m2": 200.0, "m3": 190.0},
            "p2": {"m1": 100.0, "m2": 100.0, "m3": 99.0},  # sample_mass=0
        }
        assert calc_total_moisture_mt(raw) == pytest.approx(10.0)

    def test_mg_flat_negative_result(self):
        """Flat format where m3 > m1+m2 => calc_mg_mt returns None."""
        raw = {"m1": 20.0, "m2": 1.0, "m3": 22.0}
        assert calc_total_moisture_mt(raw) is None


# ============================================================================
# calc_sulfur_ts
# Formula: avg of p1.result, p2.result
# ============================================================================

class TestCalcSulfurTs:
    """Tests for calc_sulfur_ts."""

    def test_both_parallels(self):
        raw = {"p1": {"result": 0.5}, "p2": {"result": 0.6}}
        assert calc_sulfur_ts(raw) == pytest.approx(0.55)

    def test_p1_only(self):
        raw = {"p1": {"result": 0.5}}
        assert calc_sulfur_ts(raw) == pytest.approx(0.5)

    def test_p2_only(self):
        raw = {"p2": {"result": 0.7}}
        assert calc_sulfur_ts(raw) == pytest.approx(0.7)

    def test_empty(self):
        assert calc_sulfur_ts({}) is None

    def test_none_results(self):
        raw = {"p1": {"result": None}, "p2": {"result": None}}
        assert calc_sulfur_ts(raw) is None

    def test_one_none_one_valid(self):
        raw = {"p1": {"result": None}, "p2": {"result": 1.2}}
        assert calc_sulfur_ts(raw) == pytest.approx(1.2)

    def test_zero_values(self):
        raw = {"p1": {"result": 0.0}, "p2": {"result": 0.0}}
        assert calc_sulfur_ts(raw) == pytest.approx(0.0)

    def test_string_result(self):
        raw = {"p1": {"result": "0.45"}, "p2": {"result": "0.55"}}
        assert calc_sulfur_ts(raw) == pytest.approx(0.5)

    def test_negative_values_included(self):
        """Sulfur has no >= 0 guard, negatives are included."""
        raw = {"p1": {"result": -0.1}, "p2": {"result": 0.5}}
        assert calc_sulfur_ts(raw) == pytest.approx(0.2)


# ============================================================================
# calc_phosphorus_p
# Formula: avg of p1.result, p2.result
# ============================================================================

class TestCalcPhosphorusP:
    """Tests for calc_phosphorus_p."""

    def test_both_parallels(self):
        raw = {"p1": {"result": 0.02}, "p2": {"result": 0.04}}
        assert calc_phosphorus_p(raw) == pytest.approx(0.03)

    def test_p1_only(self):
        raw = {"p1": {"result": 0.05}}
        assert calc_phosphorus_p(raw) == pytest.approx(0.05)

    def test_p2_only(self):
        raw = {"p2": {"result": 0.03}}
        assert calc_phosphorus_p(raw) == pytest.approx(0.03)

    def test_empty(self):
        assert calc_phosphorus_p({}) is None

    def test_none_results(self):
        raw = {"p1": {"result": None}, "p2": {"result": None}}
        assert calc_phosphorus_p(raw) is None

    def test_one_none(self):
        raw = {"p1": {"result": 0.01}, "p2": {"result": None}}
        assert calc_phosphorus_p(raw) == pytest.approx(0.01)

    def test_zero_values(self):
        raw = {"p1": {"result": 0}, "p2": {"result": 0}}
        assert calc_phosphorus_p(raw) == pytest.approx(0.0)


# ============================================================================
# calc_fluorine_f
# Formula: avg of p1.result (>=0), p2.result (>=0)
# ============================================================================

class TestCalcFluorineF:
    """Tests for calc_fluorine_f."""

    def test_both_parallels(self):
        raw = {"p1": {"result": 0.01}, "p2": {"result": 0.03}}
        assert calc_fluorine_f(raw) == pytest.approx(0.02)

    def test_p1_only(self):
        raw = {"p1": {"result": 0.05}}
        assert calc_fluorine_f(raw) == pytest.approx(0.05)

    def test_p2_only(self):
        raw = {"p2": {"result": 0.02}}
        assert calc_fluorine_f(raw) == pytest.approx(0.02)

    def test_empty(self):
        assert calc_fluorine_f({}) is None

    def test_none_results(self):
        raw = {"p1": {"result": None}, "p2": {"result": None}}
        assert calc_fluorine_f(raw) is None

    def test_negative_p1_excluded(self):
        """Negative result in p1 should be excluded."""
        raw = {"p1": {"result": -0.5}, "p2": {"result": 0.03}}
        assert calc_fluorine_f(raw) == pytest.approx(0.03)

    def test_negative_p2_excluded(self):
        """Negative result in p2 should be excluded."""
        raw = {"p1": {"result": 0.04}, "p2": {"result": -1.0}}
        assert calc_fluorine_f(raw) == pytest.approx(0.04)

    def test_both_negative(self):
        """Both negative => None."""
        raw = {"p1": {"result": -0.1}, "p2": {"result": -0.2}}
        assert calc_fluorine_f(raw) is None

    def test_zero_is_valid(self):
        """result == 0 should be included (>= 0)."""
        raw = {"p1": {"result": 0.0}, "p2": {"result": 0.04}}
        assert calc_fluorine_f(raw) == pytest.approx(0.02)

    def test_one_none_one_negative(self):
        raw = {"p1": {"result": None}, "p2": {"result": -0.5}}
        assert calc_fluorine_f(raw) is None


# ============================================================================
# calc_chlorine_cl
# Formula: avg of p1.result (>=0), p2.result (>=0)
# ============================================================================

class TestCalcChlorineCl:
    """Tests for calc_chlorine_cl."""

    def test_both_parallels(self):
        raw = {"p1": {"result": 0.01}, "p2": {"result": 0.03}}
        assert calc_chlorine_cl(raw) == pytest.approx(0.02)

    def test_p1_only(self):
        raw = {"p1": {"result": 0.05}}
        assert calc_chlorine_cl(raw) == pytest.approx(0.05)

    def test_p2_only(self):
        raw = {"p2": {"result": 0.02}}
        assert calc_chlorine_cl(raw) == pytest.approx(0.02)

    def test_empty(self):
        assert calc_chlorine_cl({}) is None

    def test_none_results(self):
        raw = {"p1": {"result": None}, "p2": {"result": None}}
        assert calc_chlorine_cl(raw) is None

    def test_negative_p1_excluded(self):
        raw = {"p1": {"result": -0.5}, "p2": {"result": 0.03}}
        assert calc_chlorine_cl(raw) == pytest.approx(0.03)

    def test_negative_p2_excluded(self):
        raw = {"p1": {"result": 0.04}, "p2": {"result": -1.0}}
        assert calc_chlorine_cl(raw) == pytest.approx(0.04)

    def test_both_negative(self):
        raw = {"p1": {"result": -0.1}, "p2": {"result": -0.2}}
        assert calc_chlorine_cl(raw) is None

    def test_zero_is_valid(self):
        raw = {"p1": {"result": 0.0}, "p2": {"result": 0.0}}
        assert calc_chlorine_cl(raw) == pytest.approx(0.0)

    def test_one_none_one_negative(self):
        raw = {"p1": {"result": None}, "p2": {"result": -0.3}}
        assert calc_chlorine_cl(raw) is None

    def test_string_values(self):
        raw = {"p1": {"result": "0.02"}, "p2": {"result": "0.04"}}
        assert calc_chlorine_cl(raw) == pytest.approx(0.03)
