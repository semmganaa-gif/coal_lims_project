# -*- coding: utf-8 -*-
"""
Tests for app/utils/server_calculations.py
Server-side calculation and verification tests
"""
import pytest
from unittest.mock import patch, MagicMock


class TestSafeFloat:
    """_safe_float function tests"""

    def test_safe_float_none(self):
        """None returns None"""
        from app.utils.server_calculations import _safe_float
        assert _safe_float(None) is None

    def test_safe_float_int(self):
        """Int to float"""
        from app.utils.server_calculations import _safe_float
        assert _safe_float(5) == 5.0

    def test_safe_float_float(self):
        """Float passthrough"""
        from app.utils.server_calculations import _safe_float
        assert _safe_float(5.5) == 5.5

    def test_safe_float_string(self):
        """String to float"""
        from app.utils.server_calculations import _safe_float
        assert _safe_float("5.5") == 5.5

    def test_safe_float_invalid(self):
        """Invalid string returns None"""
        from app.utils.server_calculations import _safe_float
        assert _safe_float("abc") is None

    def test_safe_float_inf(self):
        """Infinity returns None"""
        from app.utils.server_calculations import _safe_float
        assert _safe_float(float('inf')) is None

    def test_safe_float_nan(self):
        """NaN returns None"""
        from app.utils.server_calculations import _safe_float
        assert _safe_float(float('nan')) is None


class TestGetFromDict:
    """_get_from_dict function tests"""

    def test_get_from_dict_simple(self):
        """Simple key access"""
        from app.utils.server_calculations import _get_from_dict
        d = {"a": 5.0}
        assert _get_from_dict(d, "a") == 5.0

    def test_get_from_dict_nested(self):
        """Nested key access"""
        from app.utils.server_calculations import _get_from_dict
        d = {"p1": {"m1": 10.0}}
        assert _get_from_dict(d, "p1", "m1") == 10.0

    def test_get_from_dict_missing(self):
        """Missing key returns None"""
        from app.utils.server_calculations import _get_from_dict
        d = {"a": 5.0}
        assert _get_from_dict(d, "b") is None

    def test_get_from_dict_not_dict(self):
        """Non-dict in path returns None"""
        from app.utils.server_calculations import _get_from_dict
        d = {"a": 5.0}
        assert _get_from_dict(d, "a", "b") is None


class TestCalcMoistureMad:
    """calc_moisture_mad function tests"""

    def test_calc_mad_valid(self):
        """Valid Mad calculation"""
        from app.utils.server_calculations import calc_moisture_mad

        raw_data = {
            "p1": {"m1": 10.0, "m2": 1.0, "m3": 10.95},
            "p2": {"m1": 10.0, "m2": 1.0, "m3": 10.95}
        }
        result = calc_moisture_mad(raw_data)
        # Mad = ((10+1) - 10.95) / 1 * 100 = 5%
        assert result is not None
        assert abs(result - 5.0) < 0.1

    def test_calc_mad_single_parallel(self):
        """Single parallel"""
        from app.utils.server_calculations import calc_moisture_mad

        raw_data = {
            "p1": {"m1": 10.0, "m2": 1.0, "m3": 10.95}
        }
        result = calc_moisture_mad(raw_data)
        assert result is not None

    def test_calc_mad_missing_data(self):
        """Missing data returns None"""
        from app.utils.server_calculations import calc_moisture_mad

        raw_data = {"p1": {"m1": 10.0}}
        result = calc_moisture_mad(raw_data)
        assert result is None

    def test_calc_mad_empty(self):
        """Empty data returns None"""
        from app.utils.server_calculations import calc_moisture_mad
        assert calc_moisture_mad({}) is None


class TestCalcAshAad:
    """calc_ash_aad function tests"""

    def test_calc_aad_valid(self):
        """Valid Aad calculation"""
        from app.utils.server_calculations import calc_ash_aad

        raw_data = {
            "p1": {"m1": 10.0, "m2": 1.0, "m3": 10.1},
            "p2": {"m1": 10.0, "m2": 1.0, "m3": 10.1}
        }
        result = calc_ash_aad(raw_data)
        # Aad = (10.1 - 10) / 1 * 100 = 10%
        assert result is not None
        assert abs(result - 10.0) < 0.1

    def test_calc_aad_missing_data(self):
        """Missing data returns None"""
        from app.utils.server_calculations import calc_ash_aad
        assert calc_ash_aad({}) is None


class TestCalcVolatileVad:
    """calc_volatile_vad function tests"""

    def test_calc_vad_valid(self):
        """Valid Vad calculation"""
        from app.utils.server_calculations import calc_volatile_vad

        raw_data = {
            "p1": {"m1": 1.0, "m2": 1.3, "m3": 1.0},
        }
        result = calc_volatile_vad(raw_data)
        # Vad = ((1.3 - 1.0) / 1.0) * 100 = 30%
        assert result is not None
        assert abs(result - 30.0) < 0.1

    def test_calc_vad_missing_data(self):
        """Missing data returns None"""
        from app.utils.server_calculations import calc_volatile_vad
        assert calc_volatile_vad({}) is None


class TestCalcTotalMoistureMt:
    """calc_total_moisture_mt function tests"""

    def test_calc_mt_valid(self):
        """Valid MT calculation"""
        from app.utils.server_calculations import calc_total_moisture_mt

        raw_data = {
            "p1": {"m1": 100.0, "m2": 200.0, "m3": 185.0},
        }
        result = calc_total_moisture_mt(raw_data)
        # MT = ((m2 - m3) / (m2 - m1)) * 100 = ((200-185)/(200-100))*100 = 15%
        assert result is not None
        assert abs(result - 15.0) < 0.1

    def test_calc_mt_missing_data(self):
        """Missing data returns None"""
        from app.utils.server_calculations import calc_total_moisture_mt
        assert calc_total_moisture_mt({}) is None


class TestCalcSulfurTs:
    """calc_sulfur_ts function tests"""

    def test_calc_ts_valid(self):
        """Valid TS calculation"""
        from app.utils.server_calculations import calc_sulfur_ts

        raw_data = {
            "p1": {"m1": 0.1, "m2": 0.2, "m_sample": 1.0, "k": 0.34296},
        }
        result = calc_sulfur_ts(raw_data)
        assert result is not None

    def test_calc_ts_default_k(self):
        """Default k value"""
        from app.utils.server_calculations import calc_sulfur_ts

        raw_data = {
            "p1": {"m1": 0.1, "m2": 0.2, "m_sample": 1.0},
        }
        result = calc_sulfur_ts(raw_data)
        assert result is not None

    def test_calc_ts_missing_data(self):
        """Missing data returns None"""
        from app.utils.server_calculations import calc_sulfur_ts
        assert calc_sulfur_ts({}) is None


class TestCalcPhosphorusP:
    """calc_phosphorus_p function tests"""

    def test_calc_p_valid(self):
        """Valid P calculation"""
        from app.utils.server_calculations import calc_phosphorus_p

        raw_data = {
            "p1": {"v": 10.0, "v0": 1.0, "c": 0.1, "m_sample": 1.0},
        }
        result = calc_phosphorus_p(raw_data)
        assert result is not None

    def test_calc_p_missing_data(self):
        """Missing data returns None"""
        from app.utils.server_calculations import calc_phosphorus_p
        assert calc_phosphorus_p({}) is None


class TestCalcFluorineF:
    """calc_fluorine_f function tests"""

    def test_calc_f_valid(self):
        """Valid F calculation"""
        from app.utils.server_calculations import calc_fluorine_f

        raw_data = {
            "p1": {"result": 100.0},
            "p2": {"result": 110.0}
        }
        result = calc_fluorine_f(raw_data)
        assert result == 105.0

    def test_calc_f_single(self):
        """Single parallel"""
        from app.utils.server_calculations import calc_fluorine_f

        raw_data = {"p1": {"result": 100.0}}
        result = calc_fluorine_f(raw_data)
        assert result == 100.0

    def test_calc_f_missing_data(self):
        """Missing data returns None"""
        from app.utils.server_calculations import calc_fluorine_f
        assert calc_fluorine_f({}) is None


class TestCalcChlorineCl:
    """calc_chlorine_cl function tests"""

    def test_calc_cl_valid(self):
        """Valid Cl calculation"""
        from app.utils.server_calculations import calc_chlorine_cl

        raw_data = {
            "p1": {"result": 200.0},
            "p2": {"result": 220.0}
        }
        result = calc_chlorine_cl(raw_data)
        assert result == 210.0

    def test_calc_cl_missing_data(self):
        """Missing data returns None"""
        from app.utils.server_calculations import calc_chlorine_cl
        assert calc_chlorine_cl({}) is None


class TestCalcCalorificValueCv:
    """calc_calorific_value_cv function tests"""

    def test_calc_cv_valid(self):
        """Valid CV calculation"""
        from app.utils.server_calculations import calc_calorific_value_cv

        raw_data = {
            "batch": {"E": 10000.0, "q1": 100.0, "q2": 50.0},
            "p1": {"m": 1.0, "delta_t": 3.0, "s": 1.0},
            "s_used": 1.0
        }
        result = calc_calorific_value_cv(raw_data)
        assert result is not None

    def test_calc_cv_missing_batch(self):
        """Missing batch data"""
        from app.utils.server_calculations import calc_calorific_value_cv

        raw_data = {
            "p1": {"m": 1.0, "delta_t": 3.0}
        }
        result = calc_calorific_value_cv(raw_data)
        assert result is None

    def test_calc_cv_missing_data(self):
        """Missing data returns None"""
        from app.utils.server_calculations import calc_calorific_value_cv
        assert calc_calorific_value_cv({}) is None


class TestCalcGrayKingGi:
    """calc_gray_king_gi function tests"""

    def test_calc_gi_51_mode(self):
        """5:1 mode (default)"""
        from app.utils.server_calculations import calc_gray_king_gi

        raw_data = {
            "p1": {"m1": 1.0, "m2": 0.5, "m3": 0.3}
        }
        result = calc_gray_king_gi(raw_data)
        # Gi = 10 + (30*0.5 + 70*0.3) / 1 = 10 + 36 = 46
        assert result is not None

    def test_calc_gi_33_mode(self):
        """3:3 mode (retest)"""
        from app.utils.server_calculations import calc_gray_king_gi

        raw_data = {
            "p1": {"m1": 1.0, "m2": 0.5, "m3": 0.3, "mode": "3:3"}
        }
        result = calc_gray_king_gi(raw_data)
        # Gi = (30*0.5 + 70*0.3) / (5*1) = 36/5 = 7.2 -> 7
        assert result is not None

    def test_calc_gi_missing_data(self):
        """Missing data returns None"""
        from app.utils.server_calculations import calc_gray_king_gi
        assert calc_gray_king_gi({}) is None


class TestCalcFreeMoistureFm:
    """calc_free_moisture_fm function tests"""

    def test_calc_fm_valid(self):
        """Valid FM calculation"""
        from app.utils.server_calculations import calc_free_moisture_fm

        raw_data = {
            "p1": {"wt": 50.0, "wb": 150.0, "wa": 140.0}
        }
        result = calc_free_moisture_fm(raw_data)
        # FM = ((150 - 140) / (140 - 50)) * 100 = (10/90)*100 = 11.11%
        assert result is not None
        assert abs(result - 11.11) < 0.1

    def test_calc_fm_zero_denominator(self):
        """Zero denominator"""
        from app.utils.server_calculations import calc_free_moisture_fm

        raw_data = {
            "p1": {"wt": 100.0, "wb": 150.0, "wa": 100.0}
        }
        result = calc_free_moisture_fm(raw_data)
        assert result is None

    def test_calc_fm_missing_data(self):
        """Missing data returns None"""
        from app.utils.server_calculations import calc_free_moisture_fm
        assert calc_free_moisture_fm({}) is None


class TestCalcSolid:
    """calc_solid function tests"""

    def test_calc_solid_valid(self):
        """Valid Solid calculation"""
        from app.utils.server_calculations import calc_solid

        raw_data = {
            "p1": {"a": 100.0, "b": 90.0, "c": 5.0}
        }
        result = calc_solid(raw_data)
        # Solid = (5 * 100) / (100 - 90) = 500/10 = 50%
        assert result is not None
        assert abs(result - 50.0) < 0.1

    def test_calc_solid_zero_denominator(self):
        """Zero denominator"""
        from app.utils.server_calculations import calc_solid

        raw_data = {
            "p1": {"a": 100.0, "b": 100.0, "c": 5.0}
        }
        result = calc_solid(raw_data)
        assert result is None

    def test_calc_solid_missing_data(self):
        """Missing data returns None"""
        from app.utils.server_calculations import calc_solid
        assert calc_solid({}) is None


class TestCalcTrd:
    """calc_trd function tests"""

    def test_calc_trd_valid(self):
        """Valid TRD calculation"""
        from app.utils.server_calculations import calc_trd

        raw_data = {
            "p1": {"m": 1.0, "m1": 100.0, "m2": 100.5, "temp": 20, "mad": 5.0}
        }
        result = calc_trd(raw_data)
        assert result is not None

    def test_calc_trd_global_mad(self):
        """Global mad"""
        from app.utils.server_calculations import calc_trd

        raw_data = {
            "p1": {"m": 1.0, "m1": 100.0, "m2": 100.5, "temp": 20},
            "mad": 5.0
        }
        result = calc_trd(raw_data)
        assert result is not None

    def test_calc_trd_out_of_temp_range(self):
        """Temperature out of range returns None (coal TRD with mad_used/temp_c)"""
        from app.utils.server_calculations import calc_trd

        raw_data = {
            "mad_used": 5.0, "temp_c": 50,
            "p1": {"m": 1.0, "m1": 100.0, "m2": 100.5, "temp": 50, "mad": 5.0}
        }
        result = calc_trd(raw_data)
        assert result is None

    def test_calc_trd_missing_data(self):
        """Missing data returns None"""
        from app.utils.server_calculations import calc_trd
        assert calc_trd({}) is None


class TestCalculationFunctions:
    """CALCULATION_FUNCTIONS dict tests"""

    def test_calculation_functions_exists(self):
        """Dict exists"""
        from app.utils.server_calculations import CALCULATION_FUNCTIONS
        assert isinstance(CALCULATION_FUNCTIONS, dict)
        assert len(CALCULATION_FUNCTIONS) > 0

    def test_calculation_functions_mad(self):
        """Mad function mapped"""
        from app.utils.server_calculations import CALCULATION_FUNCTIONS, calc_moisture_mad
        assert CALCULATION_FUNCTIONS.get("Mad") == calc_moisture_mad

    def test_calculation_functions_aad(self):
        """Aad function mapped"""
        from app.utils.server_calculations import CALCULATION_FUNCTIONS, calc_ash_aad
        assert CALCULATION_FUNCTIONS.get("Aad") == calc_ash_aad


class TestVerifyAndRecalculate:
    """verify_and_recalculate function tests"""

    def test_verify_matching_result(self):
        """Matching client and server result"""
        from app.utils.server_calculations import verify_and_recalculate

        raw_data = {
            "p1": {"m1": 10.0, "m2": 1.0, "m3": 10.95}
        }
        result, warnings = verify_and_recalculate(
            analysis_code="Mad",
            client_final_result=5.0,
            raw_data=raw_data
        )
        assert result is not None

    def test_verify_unknown_code(self):
        """Unknown analysis code uses client value"""
        from app.utils.server_calculations import verify_and_recalculate

        result, warnings = verify_and_recalculate(
            analysis_code="UNKNOWN",
            client_final_result=10.0,
            raw_data={}
        )
        assert result == 10.0

    def test_verify_mismatch_warning(self):
        """Mismatch generates warning"""
        from app.utils.server_calculations import verify_and_recalculate

        raw_data = {
            "p1": {"m1": 10.0, "m2": 1.0, "m3": 10.95}
        }
        result, warnings = verify_and_recalculate(
            analysis_code="Mad",
            client_final_result=100.0,  # Wrong value
            raw_data=raw_data
        )
        # Server should calculate correct value
        assert result is not None
        assert abs(result - 5.0) < 0.1
        # Should have mismatch warning
        assert len(warnings) > 0

    def test_verify_none_client_result(self):
        """None client result"""
        from app.utils.server_calculations import verify_and_recalculate

        raw_data = {
            "p1": {"m1": 10.0, "m2": 1.0, "m3": 10.95}
        }
        result, warnings = verify_and_recalculate(
            analysis_code="Mad",
            client_final_result=None,
            raw_data=raw_data
        )
        # Should still calculate server result
        assert result is not None


class TestBulkVerifyResults:
    """bulk_verify_results function tests"""

    def test_bulk_verify_empty(self):
        """Empty list"""
        from app.utils.server_calculations import bulk_verify_results

        result = bulk_verify_results([])
        assert result["verified_items"] == []
        assert result["total_warnings"] == 0
        assert result["total_mismatches"] == 0

    def test_bulk_verify_single(self):
        """Single item"""
        from app.utils.server_calculations import bulk_verify_results

        items = [{
            "analysis_code": "Mad",
            "final_result": 5.0,
            "raw_data": {"p1": {"m1": 10.0, "m2": 1.0, "m3": 10.95}},
            "sample_id": 1
        }]
        result = bulk_verify_results(items)

        assert len(result["verified_items"]) == 1
        assert result["verified_items"][0]["server_verified"] is True

    def test_bulk_verify_multiple(self):
        """Multiple items"""
        from app.utils.server_calculations import bulk_verify_results

        items = [
            {
                "analysis_code": "Mad",
                "final_result": 5.0,
                "raw_data": {"p1": {"m1": 10.0, "m2": 1.0, "m3": 10.95}},
                "sample_id": 1
            },
            {
                "analysis_code": "Aad",
                "final_result": 10.0,
                "raw_data": {"p1": {"m1": 10.0, "m2": 1.0, "m3": 10.1}},
                "sample_id": 1
            }
        ]
        result = bulk_verify_results(items)

        assert len(result["verified_items"]) == 2


class TestConstants:
    """Constants tests"""

    def test_calc_mismatch_abs_threshold(self):
        """CALC_MISMATCH_ABS_THRESHOLD constant"""
        from app.utils.server_calculations import CALC_MISMATCH_ABS_THRESHOLD
        assert CALC_MISMATCH_ABS_THRESHOLD == 0.01
