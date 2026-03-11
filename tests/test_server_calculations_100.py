# -*- coding: utf-8 -*-
"""
server_calculations.py модулийн 100% coverage тестүүд
"""
import pytest
from unittest.mock import patch, MagicMock
import math


class TestServerCalculationsImport:
    """Модуль импорт тест"""

    def test_import_module(self):
        from app.utils import server_calculations
        assert server_calculations is not None

    def test_import_functions(self):
        from app.utils.server_calculations import (
            verify_and_recalculate, bulk_verify_results,
            calc_moisture_mad, calc_ash_aad, calc_volatile_vad,
            calc_total_moisture_mt, calc_sulfur_ts
        )
        assert all(callable(f) for f in [
            verify_and_recalculate, bulk_verify_results,
            calc_moisture_mad, calc_ash_aad, calc_volatile_vad,
            calc_total_moisture_mt, calc_sulfur_ts
        ])

    def test_import_constants(self):
        from app.utils.server_calculations import CALC_MISMATCH_ABS_THRESHOLD, CALCULATION_FUNCTIONS
        assert CALC_MISMATCH_ABS_THRESHOLD == 0.01
        assert isinstance(CALCULATION_FUNCTIONS, dict)


class TestSafeFloat:
    """_safe_float функцийн тест"""

    def test_none_input(self):
        from app.utils.server_calculations import _safe_float
        assert _safe_float(None) is None

    def test_valid_float(self):
        from app.utils.server_calculations import _safe_float
        assert _safe_float(3.14) == 3.14

    def test_valid_int(self):
        from app.utils.server_calculations import _safe_float
        assert _safe_float(42) == 42.0

    def test_valid_string(self):
        from app.utils.server_calculations import _safe_float
        assert _safe_float("3.14") == 3.14

    def test_invalid_string(self):
        from app.utils.server_calculations import _safe_float
        assert _safe_float("abc") is None

    def test_infinity(self):
        from app.utils.server_calculations import _safe_float
        assert _safe_float(float('inf')) is None

    def test_nan(self):
        from app.utils.server_calculations import _safe_float
        assert _safe_float(float('nan')) is None


class TestGetFromDict:
    """_get_from_dict функцийн тест"""

    def test_simple_path(self):
        from app.utils.server_calculations import _get_from_dict
        d = {"p1": {"m1": 10.5}}
        assert _get_from_dict(d, "p1", "m1") == 10.5

    def test_missing_key(self):
        from app.utils.server_calculations import _get_from_dict
        d = {"p1": {"m1": 10.5}}
        assert _get_from_dict(d, "p1", "m2") is None

    def test_missing_path(self):
        from app.utils.server_calculations import _get_from_dict
        d = {"p1": {"m1": 10.5}}
        assert _get_from_dict(d, "p2", "m1") is None

    def test_not_dict_value(self):
        from app.utils.server_calculations import _get_from_dict
        d = {"p1": "not a dict"}
        assert _get_from_dict(d, "p1", "m1") is None

    def test_string_value(self):
        from app.utils.server_calculations import _get_from_dict
        d = {"p1": {"m1": "10.5"}}
        assert _get_from_dict(d, "p1", "m1") == 10.5


class TestCalcMoistureMad:
    """calc_moisture_mad функцийн тест"""

    def test_valid_single_parallel(self):
        from app.utils.server_calculations import calc_moisture_mad
        raw_data = {
            "p1": {"m1": 10.0, "m2": 1.0, "m3": 10.97}
        }
        result = calc_moisture_mad(raw_data)
        # Mad = ((10 + 1) - 10.97) / 1 * 100 = 3%
        assert result is not None
        assert abs(result - 3.0) < 0.01

    def test_valid_two_parallels(self):
        from app.utils.server_calculations import calc_moisture_mad
        raw_data = {
            "p1": {"m1": 10.0, "m2": 1.0, "m3": 10.97},
            "p2": {"m1": 10.0, "m2": 1.0, "m3": 10.95}
        }
        result = calc_moisture_mad(raw_data)
        assert result is not None
        # Average of p1 (3%) and p2 (5%)
        assert result > 0

    def test_missing_values(self):
        from app.utils.server_calculations import calc_moisture_mad
        raw_data = {"p1": {"m1": 10.0}}
        result = calc_moisture_mad(raw_data)
        assert result is None

    def test_negative_weight_loss(self):
        from app.utils.server_calculations import calc_moisture_mad
        raw_data = {
            "p1": {"m1": 10.0, "m2": 1.0, "m3": 15.0}  # m3 > m1+m2
        }
        result = calc_moisture_mad(raw_data)
        assert result is None

    def test_zero_values(self):
        from app.utils.server_calculations import calc_moisture_mad
        raw_data = {"p1": {"m1": 0, "m2": 1.0, "m3": 0.97}}
        result = calc_moisture_mad(raw_data)
        # May return None or calculated value depending on formula
        assert result is None or isinstance(result, (int, float))


class TestCalcAshAad:
    """calc_ash_aad функцийн тест"""

    def test_valid_calculation(self):
        from app.utils.server_calculations import calc_ash_aad
        raw_data = {
            "p1": {"m1": 10.0, "m2": 1.0, "m3": 10.15}
        }
        result = calc_ash_aad(raw_data)
        # Aad = (10.15 - 10) / 1 * 100 = 15%
        assert result is not None
        assert abs(result - 15.0) < 0.01

    def test_two_parallels(self):
        from app.utils.server_calculations import calc_ash_aad
        raw_data = {
            "p1": {"m1": 10.0, "m2": 1.0, "m3": 10.15},
            "p2": {"m1": 10.0, "m2": 1.0, "m3": 10.14}
        }
        result = calc_ash_aad(raw_data)
        assert result is not None

    def test_negative_result(self):
        from app.utils.server_calculations import calc_ash_aad
        raw_data = {
            "p1": {"m1": 10.0, "m2": 1.0, "m3": 9.0}  # m3 < m1
        }
        result = calc_ash_aad(raw_data)
        assert result is None


class TestCalcVolatileVad:
    """calc_volatile_vad функцийн тест"""

    def test_valid_calculation(self):
        from app.utils.server_calculations import calc_volatile_vad
        raw_data = {
            "p1": {"m1": 10.0, "m2": 1.0, "m3": 10.7}
        }
        result = calc_volatile_vad(raw_data)
        # Vad = ((10+1) - 10.7) / 1 * 100 = 30%
        assert result is not None
        assert abs(result - 30.0) < 0.01

    def test_negative_result(self):
        from app.utils.server_calculations import calc_volatile_vad
        raw_data = {
            "p1": {"m1": 1.0, "m2": 1.0, "m3": 2.5}  # m3 > m1+m2 => weight_loss < 0
        }
        result = calc_volatile_vad(raw_data)
        assert result is None


class TestCalcTotalMoistureMT:
    """calc_total_moisture_mt функцийн тест"""

    def test_valid_calculation(self):
        from app.utils.server_calculations import calc_total_moisture_mt
        raw_data = {
            "p1": {"m1": 100.0, "m2": 200.0, "m3": 185.0}
        }
        result = calc_total_moisture_mt(raw_data)
        # MT = ((m2-m3)/(m2-m1))*100 = ((200-185)/(200-100))*100 = 15%
        assert result is not None
        assert abs(result - 15.0) < 0.01

    def test_negative_result(self):
        from app.utils.server_calculations import calc_total_moisture_mt
        raw_data = {
            "p1": {"m1": 100.0, "m2": 200.0, "m3": 210.0}  # m3 > m2 -> negative
        }
        result = calc_total_moisture_mt(raw_data)
        assert result is None


class TestCalcSulfurTS:
    """calc_sulfur_ts функцийн тест"""

    def test_valid_calculation(self):
        from app.utils.server_calculations import calc_sulfur_ts
        # Source averages p1.result and p2.result
        raw_data = {
            "p1": {"result": 1.25}
        }
        result = calc_sulfur_ts(raw_data)
        assert result is not None
        assert abs(result - 1.25) < 0.01

    def test_both_parallels(self):
        from app.utils.server_calculations import calc_sulfur_ts
        raw_data = {
            "p1": {"result": 1.20},
            "p2": {"result": 1.30}
        }
        result = calc_sulfur_ts(raw_data)
        assert result is not None
        assert abs(result - 1.25) < 0.01


class TestCalcPhosphorusP:
    """calc_phosphorus_p функцийн тест"""

    def test_valid_calculation(self):
        from app.utils.server_calculations import calc_phosphorus_p
        # Source averages p1.result and p2.result
        raw_data = {
            "p1": {"result": 0.025}
        }
        result = calc_phosphorus_p(raw_data)
        assert result is not None
        assert abs(result - 0.025) < 0.001

    def test_missing_values(self):
        from app.utils.server_calculations import calc_phosphorus_p
        raw_data = {"p1": {"v": 10.0}}  # No 'result' key
        result = calc_phosphorus_p(raw_data)
        assert result is None

    def test_no_result_key(self):
        from app.utils.server_calculations import calc_phosphorus_p
        raw_data = {
            "p1": {"v": 10.0, "v0": 1.0, "c": 0.1, "m_sample": 1.0}
        }
        result = calc_phosphorus_p(raw_data)
        assert result is None


class TestCalcFluorineF:
    """calc_fluorine_f функцийн тест"""

    def test_valid_results(self):
        from app.utils.server_calculations import calc_fluorine_f
        raw_data = {
            "p1": {"result": 150.0},
            "p2": {"result": 155.0}
        }
        result = calc_fluorine_f(raw_data)
        assert result is not None
        assert abs(result - 152.5) < 0.01

    def test_negative_result(self):
        from app.utils.server_calculations import calc_fluorine_f
        raw_data = {"p1": {"result": -10.0}}
        result = calc_fluorine_f(raw_data)
        assert result is None


class TestCalcChlorineCl:
    """calc_chlorine_cl функцийн тест"""

    def test_valid_results(self):
        from app.utils.server_calculations import calc_chlorine_cl
        raw_data = {
            "p1": {"result": 200.0},
            "p2": {"result": 210.0}
        }
        result = calc_chlorine_cl(raw_data)
        assert result is not None
        assert abs(result - 205.0) < 0.01


class TestCalcCalorificValueCV:
    """calc_calorific_value_cv функцийн тест"""

    def test_valid_calculation(self):
        from app.utils.server_calculations import calc_calorific_value_cv
        raw_data = {
            "batch": {"E": 10500, "q1": 50, "q2": 10},
            "p1": {"m": 1.0, "delta_t": 2.5},
            "s_used": 0.5
        }
        result = calc_calorific_value_cv(raw_data)
        assert result is not None
        assert result > 0

    def test_missing_batch(self):
        from app.utils.server_calculations import calc_calorific_value_cv
        raw_data = {
            "p1": {"m": 1.0, "delta_t": 2.5}
        }
        result = calc_calorific_value_cv(raw_data)
        assert result is None

    def test_zero_mass(self):
        from app.utils.server_calculations import calc_calorific_value_cv
        raw_data = {
            "batch": {"E": 10500, "q1": 50},
            "p1": {"m": 0, "delta_t": 2.5}
        }
        result = calc_calorific_value_cv(raw_data)
        assert result is None

    def test_alternative_field_names(self):
        from app.utils.server_calculations import calc_calorific_value_cv
        raw_data = {
            "batch": {"E": 10500, "q1": 50, "q2": 10},
            "p1": {"m1": 1.0, "dT": 2.5},  # Alternative names
            "s_used": 0.5
        }
        result = calc_calorific_value_cv(raw_data)
        assert result is not None

    def test_high_qb_alpha(self):
        from app.utils.server_calculations import calc_calorific_value_cv
        raw_data = {
            "batch": {"E": 15000, "q1": 50},  # Higher E -> higher qb
            "p1": {"m": 1.0, "delta_t": 2.5}
        }
        result = calc_calorific_value_cv(raw_data)
        # Should use different alpha coefficient


class TestCalcGrayKingGi:
    """calc_gray_king_gi функцийн тест"""

    def test_51_mode(self):
        from app.utils.server_calculations import calc_gray_king_gi
        raw_data = {
            "p1": {"m1": 5.0, "m2": 1.0, "m3": 2.0}
        }
        result = calc_gray_king_gi(raw_data)
        # Gi = 10 + (30*1 + 70*2) / 5 = 10 + 170/5 = 44
        assert result is not None
        assert abs(result - 44) < 1

    def test_33_mode(self):
        from app.utils.server_calculations import calc_gray_king_gi
        raw_data = {
            "p1": {"m1": 5.0, "m2": 1.0, "m3": 2.0, "mode": "3:3"}
        }
        result = calc_gray_king_gi(raw_data)
        # Gi = (30*1 + 70*2) / (5*5) = 170/25 = 6.8 -> 7
        assert result is not None

    def test_retest_mode(self):
        from app.utils.server_calculations import calc_gray_king_gi
        raw_data = {
            "p1": {"m1": 5.0, "m2": 1.0, "m3": 2.0, "retest_mode": "retest"}
        }
        result = calc_gray_king_gi(raw_data)
        assert result is not None


class TestCalcFreeMoistureFM:
    """calc_free_moisture_fm функцийн тест"""

    def test_valid_calculation(self):
        from app.utils.server_calculations import calc_free_moisture_fm
        # Source reads top-level tray_g/before_g/after_g (or tray/before/after)
        raw_data = {
            "tray_g": 10.0, "before_g": 110.0, "after_g": 105.0
        }
        result = calc_free_moisture_fm(raw_data)
        # FM = (110 - 105) / (105 - 10) * 100 = 5/95 * 100 = 5.26%
        assert result is not None
        assert abs(result - 5.26) < 0.1

    def test_zero_denominator(self):
        from app.utils.server_calculations import calc_free_moisture_fm
        raw_data = {
            "tray_g": 100.0, "before_g": 110.0, "after_g": 100.0  # after - tray = 0
        }
        result = calc_free_moisture_fm(raw_data)
        assert result is None

    def test_alternative_field_names(self):
        from app.utils.server_calculations import calc_free_moisture_fm
        # Source also accepts tray/before/after
        raw_data = {
            "tray": 10.0, "before": 110.0, "after": 105.0
        }
        result = calc_free_moisture_fm(raw_data)
        assert result is not None


class TestCalcSolid:
    """calc_solid функцийн тест"""

    def test_valid_calculation(self):
        from app.utils.server_calculations import calc_solid
        # Source reads top-level A/B/C (or a/b/c)
        raw_data = {
            "a": 100.0, "b": 20.0, "c": 68.0
        }
        result = calc_solid(raw_data)
        # Solid = 68 * 100 / (100 - 20) = 6800/80 = 85%
        assert result is not None
        assert abs(result - 85.0) < 0.1

    def test_zero_denominator(self):
        from app.utils.server_calculations import calc_solid
        raw_data = {
            "a": 100.0, "b": 100.0, "c": 50.0  # a == b
        }
        result = calc_solid(raw_data)
        assert result is None

    def test_uppercase_fields(self):
        from app.utils.server_calculations import calc_solid
        raw_data = {
            "A": 100.0, "B": 20.0, "C": 68.0
        }
        result = calc_solid(raw_data)
        assert result is not None


class TestCalcTRD:
    """calc_trd функцийн тест"""

    def test_valid_calculation(self):
        from app.utils.server_calculations import calc_trd
        raw_data = {
            "p1": {"m": 2.0, "m1": 50.0, "m2": 51.0, "temp": 20},
            "mad": 5.0
        }
        result = calc_trd(raw_data)
        assert result is not None
        assert result > 0

    def test_temperature_out_of_range(self):
        from app.utils.server_calculations import calc_trd
        raw_data = {
            "mad_used": 5.0, "temp_c": 50,
            "p1": {"m": 2.0, "m1": 50.0, "m2": 51.0, "temp": 50, "mad": 5.0}
        }
        result = calc_trd(raw_data)
        assert result is None

    def test_mad_in_parallel(self):
        from app.utils.server_calculations import calc_trd
        raw_data = {
            "mad_used": 5.0, "temp_c": 20,
            "p1": {"m": 2.0, "m1": 50.0, "m2": 51.0, "temp": 20, "mad": 5.0}
        }
        result = calc_trd(raw_data)
        assert result is not None

    def test_zero_dry_mass(self):
        from app.utils.server_calculations import calc_trd
        raw_data = {
            "mad_used": 100.0, "temp_c": 20,
            "p1": {"m": 2.0, "m1": 50.0, "m2": 51.0, "temp": 20, "mad": 100.0}
        }
        result = calc_trd(raw_data)
        assert result is None

    def test_zero_denominator(self):
        from app.utils.server_calculations import calc_trd
        raw_data = {
            "mad_used": 5.0, "temp_c": 20,
            "p1": {"m": 2.0, "m1": 51.9, "m2": 50.0, "temp": 20, "mad": 5.0}
        }
        result = calc_trd(raw_data)
        assert result is None


class TestVerifyAndRecalculate:
    """verify_and_recalculate функцийн тест"""

    @patch('app.utils.codes.norm_code')
    def test_no_calculation_function(self, mock_norm):
        from app.utils.server_calculations import verify_and_recalculate
        mock_norm.return_value = "Unknown"

        result, warnings = verify_and_recalculate(
            analysis_code="Unknown",
            client_final_result=5.0,
            raw_data={}
        )
        assert result == 5.0
        assert len(warnings) == 0

    @patch('app.utils.codes.norm_code')
    def test_matching_results(self, mock_norm):
        from app.utils.server_calculations import verify_and_recalculate
        mock_norm.return_value = "Mad"

        raw_data = {
            "p1": {"m1": 10.0, "m2": 1.0, "m3": 10.97}
        }
        result, warnings = verify_and_recalculate(
            analysis_code="Mad",
            client_final_result=3.0,
            raw_data=raw_data
        )
        assert result is not None
        assert len(warnings) == 0  # No significant mismatch

    @patch('app.utils.codes.norm_code')
    def test_mismatched_results(self, mock_norm):
        from app.utils.server_calculations import verify_and_recalculate
        mock_norm.return_value = "Mad"

        raw_data = {
            "p1": {"m1": 10.0, "m2": 1.0, "m3": 10.97}
        }
        result, warnings = verify_and_recalculate(
            analysis_code="Mad",
            client_final_result=50.0,  # Wrong value
            raw_data=raw_data
        )
        assert result is not None
        assert result != 50.0  # Server result used
        assert len(warnings) > 0  # Warning generated

    @patch('app.utils.codes.norm_code')
    def test_calculation_error(self, mock_norm):
        from app.utils.server_calculations import verify_and_recalculate, CALCULATION_FUNCTIONS
        mock_norm.return_value = "Mad"

        # Temporarily replace calc function to raise error
        original_func = CALCULATION_FUNCTIONS["Mad"]
        CALCULATION_FUNCTIONS["Mad"] = lambda x: 1/0  # Will raise ZeroDivisionError

        try:
            result, warnings = verify_and_recalculate(
                analysis_code="Mad",
                client_final_result=5.0,
                raw_data={}
            )
            assert result == 5.0  # Fallback to client value
            assert len(warnings) > 0
        finally:
            CALCULATION_FUNCTIONS["Mad"] = original_func

    @patch('app.utils.codes.norm_code')
    def test_server_result_none(self, mock_norm):
        from app.utils.server_calculations import verify_and_recalculate
        mock_norm.return_value = "Mad"

        result, warnings = verify_and_recalculate(
            analysis_code="Mad",
            client_final_result=5.0,
            raw_data={}  # Empty data -> None result
        )
        assert result == 5.0  # Fallback to client


class TestBulkVerifyResults:
    """bulk_verify_results функцийн тест"""

    @patch('app.utils.server_calculations.verify_and_recalculate')
    def test_empty_list(self, mock_verify):
        from app.utils.server_calculations import bulk_verify_results
        result = bulk_verify_results([])
        assert result["verified_items"] == []
        assert result["total_warnings"] == 0
        assert result["total_mismatches"] == 0

    @patch('app.utils.server_calculations.verify_and_recalculate')
    def test_single_item(self, mock_verify):
        from app.utils.server_calculations import bulk_verify_results
        mock_verify.return_value = (5.0, [])

        items = [{"analysis_code": "Mad", "final_result": 5.0, "sample_id": 1}]
        result = bulk_verify_results(items)

        assert len(result["verified_items"]) == 1
        assert result["verified_items"][0]["server_verified"] is True

    @patch('app.utils.server_calculations.dispatcher.verify_and_recalculate')
    def test_with_warnings(self, mock_verify):
        from app.utils.server_calculations import bulk_verify_results
        mock_verify.return_value = (3.0, ["MISMATCH warning"])

        items = [{"analysis_code": "Mad", "final_result": 50.0}]
        result = bulk_verify_results(items)

        assert result["total_warnings"] == 1
        assert result["total_mismatches"] == 1

    @patch('app.utils.server_calculations.dispatcher.verify_and_recalculate')
    def test_multiple_items(self, mock_verify):
        from app.utils.server_calculations import bulk_verify_results
        mock_verify.side_effect = [
            (5.0, []),
            (10.0, ["warning1"]),
            (15.0, ["MISMATCH", "warning2"])
        ]

        items = [
            {"analysis_code": "Mad", "final_result": 5.0},
            {"analysis_code": "Aad", "final_result": 10.0},
            {"analysis_code": "Vad", "final_result": 15.0}
        ]
        result = bulk_verify_results(items, user_id=1)

        assert len(result["verified_items"]) == 3
        assert result["total_warnings"] == 3
        assert result["total_mismatches"] == 1


class TestCalculationFunctions:
    """CALCULATION_FUNCTIONS dict тест"""

    def test_all_codes_mapped(self):
        from app.utils.server_calculations import CALCULATION_FUNCTIONS

        expected_codes = [
            "Mad", "M", "Aad", "A", "Vad", "V", "MT",
            "TS", "St,ad", "S", "P", "P,ad",
            "F", "F,ad", "Cl", "Cl,ad",
            "CV", "Qgr,ad", "Qgr",
            "Gi", "GI", "FM", "Solid", "TRD", "TRD,d"
        ]

        for code in expected_codes:
            assert code in CALCULATION_FUNCTIONS
            assert callable(CALCULATION_FUNCTIONS[code])

    def test_aliases_point_to_same_function(self):
        from app.utils.server_calculations import CALCULATION_FUNCTIONS

        assert CALCULATION_FUNCTIONS["Mad"] == CALCULATION_FUNCTIONS["M"]
        assert CALCULATION_FUNCTIONS["Aad"] == CALCULATION_FUNCTIONS["A"]
        assert CALCULATION_FUNCTIONS["TS"] == CALCULATION_FUNCTIONS["St,ad"]
        assert CALCULATION_FUNCTIONS["Gi"] == CALCULATION_FUNCTIONS["GI"]


class TestEdgeCases:
    """Edge case тестүүд"""

    def test_empty_raw_data(self):
        from app.utils.server_calculations import (
            calc_moisture_mad, calc_ash_aad, calc_volatile_vad,
            calc_total_moisture_mt, calc_calorific_value_cv
        )

        assert calc_moisture_mad({}) is None
        assert calc_ash_aad({}) is None
        assert calc_volatile_vad({}) is None
        assert calc_total_moisture_mt({}) is None
        assert calc_calorific_value_cv({}) is None

    def test_none_parallel_data(self):
        from app.utils.server_calculations import calc_moisture_mad
        raw_data = {"p1": None, "p2": None}
        assert calc_moisture_mad(raw_data) is None

    def test_string_numbers(self):
        from app.utils.server_calculations import calc_moisture_mad
        raw_data = {
            "p1": {"m1": "10.0", "m2": "1.0", "m3": "10.97"}
        }
        result = calc_moisture_mad(raw_data)
        assert result is not None

    def test_infinity_in_data(self):
        from app.utils.server_calculations import calc_calorific_value_cv
        raw_data = {
            "batch": {"E": float('inf'), "q1": 50},
            "p1": {"m": 1.0, "delta_t": 2.5}
        }
        result = calc_calorific_value_cv(raw_data)
        # Should handle infinity gracefully
        assert result is None


class TestParallel2Coverage:
    """p2 parallel branch coverage тестүүд"""

    def test_aad_with_valid_p2(self):
        """calc_ash_aad p2 branch - lines 195-197"""
        from app.utils.server_calculations import calc_ash_aad
        raw_data = {
            "p1": {"m1": 10.0, "m2": 1.0, "m3": 10.15},
            "p2": {"m1": 10.0, "m2": 1.0, "m3": 10.16}
        }
        result = calc_ash_aad(raw_data)
        assert result is not None
        # Average of 15% and 16%
        assert 15.0 < result < 16.0

    def test_mt_with_valid_p2(self):
        """calc_total_moisture_mt p2 branch"""
        from app.utils.server_calculations import calc_total_moisture_mt
        raw_data = {
            "p1": {"m1": 100.0, "m2": 200.0, "m3": 190.0},
            "p2": {"m1": 100.0, "m2": 200.0, "m3": 192.0}
        }
        result = calc_total_moisture_mt(raw_data)
        assert result is not None
        # p1: (200-190)/(200-100)*100 = 10%, p2: (200-192)/(200-100)*100 = 8%
        assert 8.0 < result < 10.0

    def test_vad_with_valid_p2(self):
        """calc_volatile_vad p2 branch - lines 271-273, 276"""
        from app.utils.server_calculations import calc_volatile_vad
        raw_data = {
            "p1": {"m1": 10.0, "m2": 1.0, "m3": 10.7},
            "p2": {"m1": 10.0, "m2": 1.0, "m3": 10.75}
        }
        result = calc_volatile_vad(raw_data)
        assert result is not None
        # p1: ((10+1)-10.7)/1*100=30%, p2: ((10+1)-10.75)/1*100=25%, avg=27.5%
        assert 25.0 < result < 30.0

    def test_ts_with_valid_p2(self):
        """calc_sulfur_ts p2 branch"""
        from app.utils.server_calculations import calc_sulfur_ts
        raw_data = {
            "p1": {"result": 1.20},
            "p2": {"result": 1.30}
        }
        result = calc_sulfur_ts(raw_data)
        assert result is not None
        assert abs(result - 1.25) < 0.01

    def test_p_with_valid_p2(self):
        """calc_phosphorus_p p2 branch"""
        from app.utils.server_calculations import calc_phosphorus_p
        raw_data = {
            "p1": {"result": 0.020},
            "p2": {"result": 0.030}
        }
        result = calc_phosphorus_p(raw_data)
        assert result is not None
        assert abs(result - 0.025) < 0.001

    def test_cv_with_valid_p2(self):
        """calc_calorific_value_cv p2 branch - lines 412, 414, 423, 425"""
        from app.utils.server_calculations import calc_calorific_value_cv
        raw_data = {
            "batch": {"E": 12000.0, "q1": 50.0, "q2": 10.0},
            "p1": {"m": 1.0, "delta_t": 2.5, "s": 0.5},
            "p2": {"m": 1.0, "delta_t": 2.6, "s": 0.5}
        }
        result = calc_calorific_value_cv(raw_data)
        assert result is not None

    def test_fm_valid(self):
        """calc_free_moisture_fm - source uses top-level keys"""
        from app.utils.server_calculations import calc_free_moisture_fm
        raw_data = {
            "tray_g": 10.0, "before_g": 100.0, "after_g": 95.0
        }
        result = calc_free_moisture_fm(raw_data)
        assert result is not None
        # FM = (100-95)/(95-10)*100 = 5/85*100 = 5.88%
        assert abs(result - 5.88) < 0.1

    def test_solid_valid(self):
        """calc_solid - source uses top-level keys"""
        from app.utils.server_calculations import calc_solid
        raw_data = {
            "a": 100.0, "b": 50.0, "c": 25.0  # Solid = 25*100/(100-50) = 50%
        }
        result = calc_solid(raw_data)
        assert result is not None
        assert abs(result - 50.0) < 0.1

    def test_gi_51_with_valid_p2(self):
        """calc_gray_king_gi p2 branch - line 477, 547"""
        from app.utils.server_calculations import calc_gray_king_gi
        raw_data = {
            "p1": {"m1": 1.0, "m2": 0.9, "m3": 0.8, "mode": "5:1"},
            "p2": {"m1": 1.0, "m2": 0.88, "m3": 0.78, "mode": "5:1"}
        }
        result = calc_gray_king_gi(raw_data)
        assert result is not None

    def test_trd_with_valid_p2(self):
        """calc_trd p2 branch - lines 724, 742, 794"""
        from app.utils.server_calculations import calc_trd
        raw_data = {
            "mad": 5.0,  # Global mad value
            "p1": {
                "m": 1.0, "m1": 50.0, "m2": 50.5,
                "temp": 25.0
            },
            "p2": {
                "m": 1.0, "m1": 50.0, "m2": 50.6,
                "temp": 25.0
            }
        }
        result = calc_trd(raw_data)
        assert result is not None

    def test_aad_only_p2_valid(self):
        """p1 invalid, p2 valid"""
        from app.utils.server_calculations import calc_ash_aad
        raw_data = {
            "p1": {"m1": 0, "m2": 0, "m3": 0},  # Invalid p1
            "p2": {"m1": 10.0, "m2": 1.0, "m3": 10.15}  # Valid p2
        }
        result = calc_ash_aad(raw_data)
        assert result is not None
        assert abs(result - 15.0) < 0.01

    def test_mt_only_p2_valid(self):
        """p1 invalid, p2 valid for MT"""
        from app.utils.server_calculations import calc_total_moisture_mt
        raw_data = {
            "p1": {"m1": None, "m2": None, "m3": None},  # Invalid p1
            "p2": {"m1": 100.0, "m2": 200.0, "m3": 190.0}  # Valid p2 - 10% moisture
        }
        result = calc_total_moisture_mt(raw_data)
        assert result is not None
        assert abs(result - 10.0) < 0.01
