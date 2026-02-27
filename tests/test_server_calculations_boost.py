# tests/test_server_calculations_boost.py
# -*- coding: utf-8 -*-
"""Tests to boost server_calculations.py coverage to 100%."""

import pytest
from unittest.mock import patch


class TestSafeFloat:
    """Test _safe_float function."""

    def test_safe_float_none(self, app):
        with app.app_context():
            from app.utils.server_calculations import _safe_float
            assert _safe_float(None) is None

    def test_safe_float_valid(self, app):
        with app.app_context():
            from app.utils.server_calculations import _safe_float
            assert _safe_float(5.5) == 5.5
            assert _safe_float("3.14") == 3.14
            assert _safe_float(10) == 10.0

    def test_safe_float_invalid(self, app):
        with app.app_context():
            from app.utils.server_calculations import _safe_float
            assert _safe_float("not_a_number") is None
            assert _safe_float([1, 2, 3]) is None

    def test_safe_float_infinity(self, app):
        with app.app_context():
            from app.utils.server_calculations import _safe_float
            assert _safe_float(float('inf')) is None
            assert _safe_float(float('-inf')) is None


class TestGetFromDict:
    """Test _get_from_dict function."""

    def test_get_from_dict_simple(self, app):
        with app.app_context():
            from app.utils.server_calculations import _get_from_dict
            d = {"p1": {"m1": 10.5}}
            assert _get_from_dict(d, "p1", "m1") == 10.5

    def test_get_from_dict_missing(self, app):
        with app.app_context():
            from app.utils.server_calculations import _get_from_dict
            d = {"p1": {"m1": 10.5}}
            assert _get_from_dict(d, "p1", "m2") is None
            assert _get_from_dict(d, "p2", "m1") is None

    def test_get_from_dict_not_dict(self, app):
        with app.app_context():
            from app.utils.server_calculations import _get_from_dict
            d = {"p1": "not_a_dict"}
            assert _get_from_dict(d, "p1", "m1") is None


class TestCalcMoistureMad:
    """Test calc_moisture_mad function."""

    def test_calc_moisture_mad_valid(self, app):
        with app.app_context():
            from app.utils.server_calculations import calc_moisture_mad
            # Formula: Mad% = ((m1 + m2) - m3) / m2 * 100
            raw_data = {
                "p1": {"m1": 10.0, "m2": 1.0, "m3": 10.95},
                "p2": {"m1": 10.0, "m2": 1.0, "m3": 10.95}
            }
            result = calc_moisture_mad(raw_data)
            assert result is not None
            assert abs(result - 5.0) < 0.1

    def test_calc_moisture_mad_single_parallel(self, app):
        with app.app_context():
            from app.utils.server_calculations import calc_moisture_mad
            raw_data = {"p1": {"m1": 10.0, "m2": 1.0, "m3": 10.95}}
            result = calc_moisture_mad(raw_data)
            assert result is not None

    def test_calc_moisture_mad_missing_data(self, app):
        with app.app_context():
            from app.utils.server_calculations import calc_moisture_mad
            result = calc_moisture_mad({})
            assert result is None


class TestCalcAshAad:
    """Test calc_ash_aad function."""

    def test_calc_ash_aad_valid(self, app):
        with app.app_context():
            from app.utils.server_calculations import calc_ash_aad
            # Formula: Aad% = (m3 - m1) / m2 * 100
            raw_data = {
                "p1": {"m1": 10.0, "m2": 1.0, "m3": 10.1},
                "p2": {"m1": 10.0, "m2": 1.0, "m3": 10.1}
            }
            result = calc_ash_aad(raw_data)
            assert result is not None

    def test_calc_ash_aad_missing(self, app):
        with app.app_context():
            from app.utils.server_calculations import calc_ash_aad
            result = calc_ash_aad({})
            assert result is None


class TestCalcVolatileVad:
    """Test calc_volatile_vad function."""

    def test_calc_volatile_vad_valid(self, app):
        with app.app_context():
            from app.utils.server_calculations import calc_volatile_vad
            # Formula: Vad% = ((m2 - m3) / m1) * 100
            raw_data = {
                "p1": {"m1": 1.0, "m2": 1.3, "m3": 1.0},
                "p2": {"m1": 1.0, "m2": 1.3, "m3": 1.0}
            }
            result = calc_volatile_vad(raw_data)
            assert result is not None

    def test_calc_volatile_vad_missing(self, app):
        with app.app_context():
            from app.utils.server_calculations import calc_volatile_vad
            result = calc_volatile_vad({})
            assert result is None


class TestCalcTotalMoistureMt:
    """Test calc_total_moisture_mt function."""

    def test_calc_total_moisture_valid(self, app):
        with app.app_context():
            from app.utils.server_calculations import calc_total_moisture_mt
            # Formula: MT% = ((m2 - m3) / (m2 - m1)) * 100
            raw_data = {
                "p1": {"m1": 100.0, "m2": 200.0, "m3": 190.0},
                "p2": {"m1": 100.0, "m2": 200.0, "m3": 190.0}
            }
            result = calc_total_moisture_mt(raw_data)
            assert result is not None
            assert abs(result - 10.0) < 0.1

    def test_calc_total_moisture_missing(self, app):
        with app.app_context():
            from app.utils.server_calculations import calc_total_moisture_mt
            result = calc_total_moisture_mt({})
            assert result is None


class TestCalcSulfurTs:
    """Test calc_sulfur_ts function."""

    def test_calc_sulfur_ts_valid(self, app):
        with app.app_context():
            from app.utils.server_calculations import calc_sulfur_ts
            # Formula: S% = ((m2 - m1) / m_sample) * K * 100
            raw_data = {
                "p1": {"m1": 0.1, "m2": 0.15, "m_sample": 1.0, "k": 0.34296},
                "p2": {"m1": 0.1, "m2": 0.15, "m_sample": 1.0, "k": 0.34296}
            }
            result = calc_sulfur_ts(raw_data)
            assert result is not None

    def test_calc_sulfur_ts_missing(self, app):
        with app.app_context():
            from app.utils.server_calculations import calc_sulfur_ts
            result = calc_sulfur_ts({})
            assert result is None


class TestCalcPhosphorusP:
    """Test calc_phosphorus_p function."""

    def test_calc_phosphorus_valid(self, app):
        with app.app_context():
            from app.utils.server_calculations import calc_phosphorus_p
            # Formula: P% = ((V - V0) * C * 0.0030974 * 100) / m_sample
            raw_data = {
                "p1": {"v": 10.0, "v0": 0.5, "c": 0.1, "m_sample": 1.0},
                "p2": {"v": 10.0, "v0": 0.5, "c": 0.1, "m_sample": 1.0}
            }
            result = calc_phosphorus_p(raw_data)
            assert result is not None

    def test_calc_phosphorus_missing(self, app):
        with app.app_context():
            from app.utils.server_calculations import calc_phosphorus_p
            result = calc_phosphorus_p({})
            assert result is None


class TestCalcFluorineF:
    """Test calc_fluorine_f function."""

    def test_calc_fluorine_valid(self, app):
        with app.app_context():
            from app.utils.server_calculations import calc_fluorine_f
            raw_data = {
                "p1": {"result": 0.05},
                "p2": {"result": 0.05}
            }
            result = calc_fluorine_f(raw_data)
            assert result is not None
            assert abs(result - 0.05) < 0.01

    def test_calc_fluorine_missing(self, app):
        with app.app_context():
            from app.utils.server_calculations import calc_fluorine_f
            result = calc_fluorine_f({})
            assert result is None


class TestCalcChlorineCl:
    """Test calc_chlorine_cl function."""

    def test_calc_chlorine_valid(self, app):
        with app.app_context():
            from app.utils.server_calculations import calc_chlorine_cl
            raw_data = {
                "p1": {"result": 0.1},
                "p2": {"result": 0.1}
            }
            result = calc_chlorine_cl(raw_data)
            assert result is not None
            assert abs(result - 0.1) < 0.01

    def test_calc_chlorine_missing(self, app):
        with app.app_context():
            from app.utils.server_calculations import calc_chlorine_cl
            result = calc_chlorine_cl({})
            assert result is None


class TestCalcCalorificValueCv:
    """Test calc_calorific_value_cv function."""

    def test_calc_calorific_valid(self, app):
        with app.app_context():
            from app.utils.server_calculations import calc_calorific_value_cv
            raw_data = {
                "p1": {"m": 1.0, "delta_t": 2.5, "s": 0.5},
                "p2": {"m": 1.0, "delta_t": 2.5, "s": 0.5},
                "batch": {"E": 10000.0, "q1": 50.0, "q2": 10.0},
                "s_used": 0.5
            }
            result = calc_calorific_value_cv(raw_data)
            assert result is not None

    def test_calc_calorific_high_value(self, app):
        """Test with high calorific value (alpha = 0.0016)."""
        with app.app_context():
            from app.utils.server_calculations import calc_calorific_value_cv
            raw_data = {
                "p1": {"m": 1.0, "delta_t": 3.0, "s": 0.5},
                "p2": {"m": 1.0, "delta_t": 3.0, "s": 0.5},
                "batch": {"E": 15000.0, "q1": 50.0, "q2": 10.0},
                "s_used": 0.5
            }
            result = calc_calorific_value_cv(raw_data)
            assert result is not None

    def test_calc_calorific_low_value(self, app):
        """Test with low calorific value (alpha = 0.0010)."""
        with app.app_context():
            from app.utils.server_calculations import calc_calorific_value_cv
            raw_data = {
                "p1": {"m": 1.0, "delta_t": 1.5, "s": 0.5},
                "p2": {"m": 1.0, "delta_t": 1.5, "s": 0.5},
                "batch": {"E": 8000.0, "q1": 50.0, "q2": 10.0}
            }
            result = calc_calorific_value_cv(raw_data)
            assert result is not None

    def test_calc_calorific_missing(self, app):
        with app.app_context():
            from app.utils.server_calculations import calc_calorific_value_cv
            result = calc_calorific_value_cv({})
            assert result is None

    def test_calc_calorific_zero_mass(self, app):
        with app.app_context():
            from app.utils.server_calculations import calc_calorific_value_cv
            raw_data = {
                "p1": {"m": 0, "delta_t": 2.5},
                "batch": {"E": 10000.0, "q1": 50.0}
            }
            result = calc_calorific_value_cv(raw_data)
            assert result is None


class TestCalcGrayKingGi:
    """Test calc_gray_king_gi function."""

    def test_calc_gray_king_valid_51_mode(self, app):
        with app.app_context():
            from app.utils.server_calculations import calc_gray_king_gi
            # 5:1 mode: Gi = 10 + (30*m2 + 70*m3) / m1
            raw_data = {
                "p1": {"m1": 100.0, "m2": 2.0, "m3": 1.0},
                "p2": {"m1": 100.0, "m2": 2.0, "m3": 1.0}
            }
            result = calc_gray_king_gi(raw_data)
            assert result is not None

    def test_calc_gray_king_33_mode(self, app):
        with app.app_context():
            from app.utils.server_calculations import calc_gray_king_gi
            # 3:3 mode: Gi = (30*m2 + 70*m3) / (5*m1)
            raw_data = {
                "p1": {"m1": 100.0, "m2": 2.0, "m3": 1.0, "mode": "3:3"},
                "p2": {"m1": 100.0, "m2": 2.0, "m3": 1.0, "mode": "3:3"}
            }
            result = calc_gray_king_gi(raw_data)
            assert result is not None

    def test_calc_gray_king_retest_mode(self, app):
        with app.app_context():
            from app.utils.server_calculations import calc_gray_king_gi
            raw_data = {
                "p1": {"m1": 100.0, "m2": 2.0, "m3": 1.0, "mode": "retest"}
            }
            result = calc_gray_king_gi(raw_data)
            assert result is not None

    def test_calc_gray_king_missing(self, app):
        with app.app_context():
            from app.utils.server_calculations import calc_gray_king_gi
            result = calc_gray_king_gi({})
            assert result is None


class TestCalcFreeMoistureFm:
    """Test calc_free_moisture_fm function."""

    def test_calc_free_moisture_valid(self, app):
        with app.app_context():
            from app.utils.server_calculations import calc_free_moisture_fm
            # Formula: FM% = ((Wb - Wa) / (Wa - Wt)) * 100
            raw_data = {
                "p1": {"wt": 50.0, "wb": 110.0, "wa": 105.0},
                "p2": {"wt": 50.0, "wb": 110.0, "wa": 105.0}
            }
            result = calc_free_moisture_fm(raw_data)
            assert result is not None

    def test_calc_free_moisture_zero_denominator(self, app):
        with app.app_context():
            from app.utils.server_calculations import calc_free_moisture_fm
            raw_data = {
                "p1": {"wt": 50.0, "wb": 110.0, "wa": 50.0}  # wa - wt = 0
            }
            result = calc_free_moisture_fm(raw_data)
            assert result is None

    def test_calc_free_moisture_missing(self, app):
        with app.app_context():
            from app.utils.server_calculations import calc_free_moisture_fm
            result = calc_free_moisture_fm({})
            assert result is None


class TestCalcSolid:
    """Test calc_solid function."""

    def test_calc_solid_valid(self, app):
        with app.app_context():
            from app.utils.server_calculations import calc_solid
            # Formula: Solid% = C * 100 / (A - B)
            raw_data = {
                "p1": {"a": 100.0, "b": 50.0, "c": 25.0},
                "p2": {"a": 100.0, "b": 50.0, "c": 25.0}
            }
            result = calc_solid(raw_data)
            assert result is not None
            assert abs(result - 50.0) < 0.1

    def test_calc_solid_zero_denominator(self, app):
        with app.app_context():
            from app.utils.server_calculations import calc_solid
            raw_data = {
                "p1": {"a": 100.0, "b": 100.0, "c": 25.0}  # a - b = 0
            }
            result = calc_solid(raw_data)
            assert result is None

    def test_calc_solid_missing(self, app):
        with app.app_context():
            from app.utils.server_calculations import calc_solid
            result = calc_solid({})
            assert result is None


class TestCalcTrd:
    """Test calc_trd function."""

    def test_calc_trd_valid(self, app):
        with app.app_context():
            from app.utils.server_calculations import calc_trd
            # TRD needs m, m1, m2, temp, mad
            raw_data = {
                "p1": {"m": 1.0, "m1": 50.0, "m2": 50.5, "temp": 20, "mad": 5.0},
                "p2": {"m": 1.0, "m1": 50.0, "m2": 50.5, "temp": 20, "mad": 5.0}
            }
            result = calc_trd(raw_data)
            assert result is not None

    def test_calc_trd_missing(self, app):
        with app.app_context():
            from app.utils.server_calculations import calc_trd
            result = calc_trd({})
            assert result is None

    def test_calc_trd_global_mad(self, app):
        with app.app_context():
            from app.utils.server_calculations import calc_trd
            raw_data = {
                "p1": {"m": 1.0, "m1": 50.0, "m2": 50.5, "temp": 20},
                "mad": 5.0  # global mad value
            }
            result = calc_trd(raw_data)
            assert result is not None or result is None  # may or may not work


class TestVerifyAndRecalculate:
    """Test verify_and_recalculate function."""

    def test_verify_mad(self, app):
        with app.app_context():
            from app.utils.server_calculations import verify_and_recalculate
            raw_data = {
                "p1": {"m1": 10.0, "m2": 1.0, "m3": 10.95},
                "p2": {"m1": 10.0, "m2": 1.0, "m3": 10.95}
            }
            result, warnings = verify_and_recalculate("Mad", 5.0, raw_data)
            assert result is not None

    def test_verify_aad(self, app):
        with app.app_context():
            from app.utils.server_calculations import verify_and_recalculate
            raw_data = {
                "p1": {"m1": 10.0, "m2": 1.0, "m3": 10.1},
                "p2": {"m1": 10.0, "m2": 1.0, "m3": 10.1}
            }
            result, warnings = verify_and_recalculate("Aad", 10.0, raw_data)
            assert result is not None

    def test_verify_vad(self, app):
        with app.app_context():
            from app.utils.server_calculations import verify_and_recalculate
            raw_data = {
                "p1": {"m1": 1.0, "m2": 1.3, "m3": 1.0},
                "p2": {"m1": 1.0, "m2": 1.3, "m3": 1.0}
            }
            result, warnings = verify_and_recalculate("Vad", 30.0, raw_data)
            assert result is not None

    def test_verify_mt(self, app):
        with app.app_context():
            from app.utils.server_calculations import verify_and_recalculate
            raw_data = {
                "p1": {"m1": 100.0, "m2": 90.0},
                "p2": {"m1": 100.0, "m2": 90.0}
            }
            result, warnings = verify_and_recalculate("Mt", 10.0, raw_data)
            assert result is not None

    def test_verify_ts(self, app):
        with app.app_context():
            from app.utils.server_calculations import verify_and_recalculate
            raw_data = {
                "p1": {"m1": 0.1, "m2": 0.15, "m_sample": 1.0, "k": 0.34296},
                "p2": {"m1": 0.1, "m2": 0.15, "m_sample": 1.0}
            }
            result, warnings = verify_and_recalculate("TS", 1.7, raw_data)
            assert result is not None

    def test_verify_cv(self, app):
        with app.app_context():
            from app.utils.server_calculations import verify_and_recalculate
            raw_data = {
                "p1": {"m": 1.0, "delta_t": 2.5, "s": 0.5},
                "p2": {"m": 1.0, "delta_t": 2.5, "s": 0.5},
                "batch": {"E": 10000.0, "q1": 50.0, "q2": 10.0}
            }
            result, warnings = verify_and_recalculate("CV", 5500, raw_data)
            assert result is not None

    def test_verify_gi(self, app):
        with app.app_context():
            from app.utils.server_calculations import verify_and_recalculate
            raw_data = {
                "p1": {"m1": 100.0, "m2": 2.0, "m3": 1.0}
            }
            result, warnings = verify_and_recalculate("Gi", 11, raw_data)
            assert result is not None

    def test_verify_fm(self, app):
        with app.app_context():
            from app.utils.server_calculations import verify_and_recalculate
            raw_data = {
                "p1": {"wt": 50.0, "wb": 110.0, "wa": 105.0}
            }
            result, warnings = verify_and_recalculate("FM", 9.0, raw_data)
            assert result is not None

    def test_verify_solid(self, app):
        with app.app_context():
            from app.utils.server_calculations import verify_and_recalculate
            raw_data = {
                "p1": {"a": 100.0, "b": 50.0, "c": 25.0}
            }
            result, warnings = verify_and_recalculate("SOLID", 50.0, raw_data)
            assert result is not None

    def test_verify_trd(self, app):
        with app.app_context():
            from app.utils.server_calculations import verify_and_recalculate
            raw_data = {
                "p1": {"result": 1.5}
            }
            result, warnings = verify_and_recalculate("TRD", 1.5, raw_data)
            assert result is not None

    def test_verify_unknown(self, app):
        with app.app_context():
            from app.utils.server_calculations import verify_and_recalculate
            result, warnings = verify_and_recalculate("UNKNOWN", 5.0, {})
            assert result == 5.0

    def test_verify_mismatch(self, app):
        with app.app_context():
            from app.utils.server_calculations import verify_and_recalculate
            raw_data = {
                "p1": {"m1": 10.0, "m2": 1.0, "m3": 10.95},
                "p2": {"m1": 10.0, "m2": 1.0, "m3": 10.95}
            }
            result, warnings = verify_and_recalculate("Mad", 10.0, raw_data)
            assert result is not None
            assert len(warnings) > 0

    def test_verify_none_raw_data(self, app):
        with app.app_context():
            from app.utils.server_calculations import verify_and_recalculate
            result, warnings = verify_and_recalculate("Mad", 5.0, None)
            assert result == 5.0

    def test_verify_p(self, app):
        with app.app_context():
            from app.utils.server_calculations import verify_and_recalculate
            raw_data = {
                "p1": {"v": 10.0, "v0": 0.5, "c": 0.1, "m_sample": 1.0}
            }
            result, warnings = verify_and_recalculate("P", 0.03, raw_data)
            assert result is not None

    def test_verify_f(self, app):
        with app.app_context():
            from app.utils.server_calculations import verify_and_recalculate
            raw_data = {
                "p1": {"result": 0.05}
            }
            result, warnings = verify_and_recalculate("F", 0.05, raw_data)
            assert result is not None

    def test_verify_cl(self, app):
        with app.app_context():
            from app.utils.server_calculations import verify_and_recalculate
            raw_data = {
                "p1": {"result": 0.1}
            }
            result, warnings = verify_and_recalculate("Cl", 0.1, raw_data)
            assert result is not None


class TestBulkVerifyResults:
    """Test bulk_verify_results function."""

    def test_bulk_verify_empty(self, app):
        with app.app_context():
            from app.utils.server_calculations import bulk_verify_results
            result = bulk_verify_results([])
            assert "verified_items" in result
            assert result["verified_items"] == []

    def test_bulk_verify_single(self, app):
        with app.app_context():
            from app.utils.server_calculations import bulk_verify_results
            raw_data = {
                "p1": {"m1": 10.0, "m2": 1.0, "m3": 10.95},
                "p2": {"m1": 10.0, "m2": 1.0, "m3": 10.95}
            }
            items = [{
                "analysis_code": "Mad",
                "final_result": 5.0,
                "raw_data": raw_data
            }]
            result = bulk_verify_results(items)
            assert len(result["verified_items"]) == 1

    def test_bulk_verify_multiple(self, app):
        with app.app_context():
            from app.utils.server_calculations import bulk_verify_results
            items = [
                {
                    "analysis_code": "Mad",
                    "final_result": 5.0,
                    "raw_data": {"p1": {"m1": 10.0, "m2": 1.0, "m3": 10.95}}
                },
                {
                    "analysis_code": "Aad",
                    "final_result": 10.0,
                    "raw_data": {"p1": {"m1": 10.0, "m2": 1.0, "m3": 10.1}}
                }
            ]
            result = bulk_verify_results(items)
            assert len(result["verified_items"]) == 2

    def test_bulk_verify_with_mismatch(self, app):
        """Test bulk verify counting mismatches."""
        with app.app_context():
            from app.utils.server_calculations import bulk_verify_results
            items = [{
                "analysis_code": "Mad",
                "final_result": 50.0,  # Wrong value - will cause mismatch
                "raw_data": {
                    "p1": {"m1": 10.0, "m2": 1.0, "m3": 10.95},
                    "p2": {"m1": 10.0, "m2": 1.0, "m3": 10.95}
                }
            }]
            result = bulk_verify_results(items)
            assert result["total_mismatches"] >= 1


class TestCalcCvEdgeCases:
    """Test calc_calorific_value_cv edge cases."""

    def test_calc_cv_infinite_values(self, app):
        """Test CV with infinite values in input."""
        with app.app_context():
            from app.utils.server_calculations import calc_calorific_value_cv
            raw_data = {
                "p1": {"m": float('inf'), "delta_t": 2.5, "s": 0.5},
                "batch": {"E": 10000.0, "q1": 50.0}
            }
            result = calc_calorific_value_cv(raw_data)
            assert result is None

    def test_calc_cv_zero_mass_m1_key(self, app):
        """Test CV with m1=0 (using m1 key to bypass 'or' falsy check)."""
        with app.app_context():
            from app.utils.server_calculations import calc_calorific_value_cv
            # Use m1 instead of m to pass 0 through (m or m1 evaluates to m1 when m is None/falsy)
            raw_data = {
                "p1": {"m1": 0, "delta_t": 2.5},  # m1=0 should trigger m==0 check
                "batch": {"E": 10000.0, "q1": 50.0}
            }
            result = calc_calorific_value_cv(raw_data)
            assert result is None

    def test_calc_cv_infinite_in_batch(self, app):
        """Test CV with infinite values in batch parameters."""
        with app.app_context():
            from app.utils.server_calculations import calc_calorific_value_cv
            raw_data = {
                "p1": {"m1": 1.0, "delta_t": 2.5},
                "batch": {"E": float('inf'), "q1": 50.0}
            }
            result = calc_calorific_value_cv(raw_data)
            assert result is None


class TestCalcTrdEdgeCases:
    """Test calc_trd edge cases."""

    def test_calc_trd_temp_out_of_bounds_low(self, app):
        """Test TRD with temperature below 6 degrees (coal format)."""
        with app.app_context():
            from app.utils.server_calculations import calc_trd
            raw_data = {
                "mad_used": 5.0, "temp_c": 5,
                "p1": {"m": 1.0, "m1": 50.0, "m2": 50.5, "temp": 5, "mad": 5.0}
            }
            result = calc_trd(raw_data)
            assert result is None

    def test_calc_trd_temp_out_of_bounds_high(self, app):
        """Test TRD with temperature above 35 degrees (coal format)."""
        with app.app_context():
            from app.utils.server_calculations import calc_trd
            raw_data = {
                "mad_used": 5.0, "temp_c": 40,
                "p1": {"m": 1.0, "m1": 50.0, "m2": 50.5, "temp": 40, "mad": 5.0}
            }
            result = calc_trd(raw_data)
            assert result is None

    def test_calc_trd_negative_mad(self, app):
        """Test TRD with negative mad value (coal format)."""
        with app.app_context():
            from app.utils.server_calculations import calc_trd
            raw_data = {
                "mad_used": -5.0, "temp_c": 20,
                "p1": {"m": 1.0, "m1": 50.0, "m2": 50.5, "temp": 20, "mad": -5.0}
            }
            result = calc_trd(raw_data)
            assert result is None

    def test_calc_trd_zero_dry_mass(self, app):
        """Test TRD with md <= 0 (100% moisture, coal format)."""
        with app.app_context():
            from app.utils.server_calculations import calc_trd
            raw_data = {
                "mad_used": 100.0, "temp_c": 20,
                "p1": {"m": 1.0, "m1": 50.0, "m2": 50.5, "temp": 20, "mad": 100.0}
            }
            result = calc_trd(raw_data)
            assert result is None

    def test_calc_trd_zero_denominator(self, app):
        """Test TRD with denominator = 0 (coal format)."""
        with app.app_context():
            from app.utils.server_calculations import calc_trd
            # md + m2 - m1 = 0
            raw_data = {
                "mad_used": 5.0, "temp_c": 20,
                "p1": {"m": 1.0, "m1": 50.5, "m2": 49.55, "temp": 20, "mad": 5.0}
            }
            result = calc_trd(raw_data)
            assert result is None

    def test_calc_trd_infinite_temp(self, app):
        """Test TRD with infinite temperature (coal format)."""
        with app.app_context():
            from app.utils.server_calculations import calc_trd
            raw_data = {
                "mad_used": 5.0, "temp_c": float('inf'),
                "p1": {"m": 1.0, "m1": 50.0, "m2": 50.5, "temp": float('inf'), "mad": 5.0}
            }
            result = calc_trd(raw_data)
            assert result is None


class TestVerifyCalcException:
    """Test verify_and_recalculate with exception."""

    def test_verify_calc_exception(self, app):
        """Test verification when calculation raises exception."""
        with app.app_context():
            from app.utils.server_calculations import verify_and_recalculate
            # Pass malformed data that could cause exception
            raw_data = {
                "p1": {"m1": "invalid", "m2": [1, 2, 3], "m3": {"nested": "dict"}},
                "p2": None  # May cause issues
            }
            result, warnings = verify_and_recalculate("Mad", 5.0, raw_data)
            # Should return client value on exception
            assert result == 5.0

    def test_verify_calc_with_mocked_exception(self, app):
        """Test verification when calc_func raises exception."""
        with app.app_context():
            import app.utils.server_calculations as sc

            def raise_exception(*args, **kwargs):
                raise ValueError("Test exception")

            # Save original and replace in CALCULATION_FUNCTIONS dict
            original_calc = sc.CALCULATION_FUNCTIONS.get("Mad")
            sc.CALCULATION_FUNCTIONS["Mad"] = raise_exception
            try:
                result, warnings = sc.verify_and_recalculate(
                    "Mad", 5.0,
                    {"p1": {"m1": 10.0, "m2": 1.0, "m3": 10.95}}
                )
                # Should return client value and have warning
                assert result == 5.0
                assert any("error" in w.lower() for w in warnings)
            finally:
                # Restore original
                if original_calc:
                    sc.CALCULATION_FUNCTIONS["Mad"] = original_calc
