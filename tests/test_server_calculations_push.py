# -*- coding: utf-8 -*-
"""
Server Calculations модулийн coverage тестүүд
"""
import pytest
from unittest.mock import patch, MagicMock
import math


class TestSafeFloat:
    """_safe_float тестүүд"""

    def test_import_function(self):
        """Function import"""
        from app.utils.server_calculations import _safe_float
        assert _safe_float is not None

    def test_none(self):
        """None returns None"""
        from app.utils.server_calculations import _safe_float
        assert _safe_float(None) is None

    def test_int(self):
        """Int converts to float"""
        from app.utils.server_calculations import _safe_float
        assert _safe_float(10) == 10.0

    def test_float(self):
        """Float returns float"""
        from app.utils.server_calculations import _safe_float
        assert _safe_float(10.5) == 10.5

    def test_string_number(self):
        """String number converts"""
        from app.utils.server_calculations import _safe_float
        assert _safe_float("10.5") == 10.5

    def test_invalid_string(self):
        """Invalid string returns None"""
        from app.utils.server_calculations import _safe_float
        assert _safe_float("abc") is None

    def test_infinity(self):
        """Infinity returns None"""
        from app.utils.server_calculations import _safe_float
        assert _safe_float(float('inf')) is None

    def test_nan(self):
        """NaN returns None"""
        from app.utils.server_calculations import _safe_float
        assert _safe_float(float('nan')) is None


class TestGetFromDict:
    """_get_from_dict тестүүд"""

    def test_import_function(self):
        """Function import"""
        from app.utils.server_calculations import _get_from_dict
        assert _get_from_dict is not None

    def test_simple_key(self):
        """Simple key access"""
        from app.utils.server_calculations import _get_from_dict
        d = {"a": 10.0}
        assert _get_from_dict(d, "a") == 10.0

    def test_nested_keys(self):
        """Nested key access"""
        from app.utils.server_calculations import _get_from_dict
        d = {"p1": {"m1": 10.0}}
        assert _get_from_dict(d, "p1", "m1") == 10.0

    def test_missing_key(self):
        """Missing key returns None"""
        from app.utils.server_calculations import _get_from_dict
        d = {"a": 10.0}
        assert _get_from_dict(d, "b") is None

    def test_not_dict(self):
        """Non-dict in path returns None"""
        from app.utils.server_calculations import _get_from_dict
        d = {"a": "string"}
        assert _get_from_dict(d, "a", "b") is None

    def test_deep_nested(self):
        """Deep nested access"""
        from app.utils.server_calculations import _get_from_dict
        d = {"a": {"b": {"c": 5.0}}}
        assert _get_from_dict(d, "a", "b", "c") == 5.0


class TestCalcMoistureMad:
    """calc_moisture_mad тестүүд"""

    def test_import_function(self):
        """Function import"""
        from app.utils.server_calculations import calc_moisture_mad
        assert calc_moisture_mad is not None

    def test_valid_single_parallel(self):
        """Valid p1 only"""
        from app.utils.server_calculations import calc_moisture_mad
        raw = {
            "p1": {"m1": 10.0, "m2": 1.0, "m3": 10.95}
        }
        result = calc_moisture_mad(raw)
        # ((10+1) - 10.95) / 1 * 100 = 5%
        assert result is not None
        assert abs(result - 5.0) < 0.01

    def test_valid_both_parallels(self):
        """Valid p1 and p2"""
        from app.utils.server_calculations import calc_moisture_mad
        raw = {
            "p1": {"m1": 10.0, "m2": 1.0, "m3": 10.95},
            "p2": {"m1": 10.0, "m2": 1.0, "m3": 10.93}
        }
        result = calc_moisture_mad(raw)
        # Average of 5% and 7%
        assert result is not None

    def test_empty_raw_data(self):
        """Empty raw data returns None"""
        from app.utils.server_calculations import calc_moisture_mad
        assert calc_moisture_mad({}) is None

    def test_missing_m1(self):
        """Missing m1 returns None"""
        from app.utils.server_calculations import calc_moisture_mad
        raw = {"p1": {"m2": 1.0, "m3": 10.95}}
        assert calc_moisture_mad(raw) is None

    def test_zero_m2(self):
        """Zero m2 returns None (division by zero protection)"""
        from app.utils.server_calculations import calc_moisture_mad
        raw = {"p1": {"m1": 10.0, "m2": 0, "m3": 10.95}}
        assert calc_moisture_mad(raw) is None

    def test_negative_weight_loss(self):
        """Negative weight loss skipped"""
        from app.utils.server_calculations import calc_moisture_mad
        raw = {"p1": {"m1": 10.0, "m2": 1.0, "m3": 12.0}}  # m3 > m1+m2
        assert calc_moisture_mad(raw) is None


class TestCalcAshAad:
    """calc_ash_aad тестүүд"""

    def test_import_function(self):
        """Function import"""
        from app.utils.server_calculations import calc_ash_aad
        assert calc_ash_aad is not None

    def test_valid_single_parallel(self):
        """Valid p1 only"""
        from app.utils.server_calculations import calc_ash_aad
        raw = {
            "p1": {"m1": 10.0, "m2": 1.0, "m3": 10.15}
        }
        result = calc_ash_aad(raw)
        # (10.15 - 10) / 1 * 100 = 15%
        assert result is not None
        assert abs(result - 15.0) < 0.01

    def test_valid_both_parallels(self):
        """Valid p1 and p2"""
        from app.utils.server_calculations import calc_ash_aad
        raw = {
            "p1": {"m1": 10.0, "m2": 1.0, "m3": 10.15},
            "p2": {"m1": 10.0, "m2": 1.0, "m3": 10.14}
        }
        result = calc_ash_aad(raw)
        assert result is not None

    def test_empty_raw_data(self):
        """Empty raw data returns None"""
        from app.utils.server_calculations import calc_ash_aad
        assert calc_ash_aad({}) is None

    def test_negative_result(self):
        """Negative result skipped"""
        from app.utils.server_calculations import calc_ash_aad
        raw = {"p1": {"m1": 10.0, "m2": 1.0, "m3": 9.0}}  # m3 < m1
        assert calc_ash_aad(raw) is None


class TestCalcVolatileVad:
    """calc_volatile_vad тестүүд"""

    def test_import_function(self):
        """Function import"""
        from app.utils.server_calculations import calc_volatile_vad
        assert calc_volatile_vad is not None

    def test_valid_single_parallel(self):
        """Valid p1 only"""
        from app.utils.server_calculations import calc_volatile_vad
        raw = {
            "p1": {"m1": 1.0, "m2": 1.0, "m3": 0.65}
        }
        result = calc_volatile_vad(raw)
        # (1.0 - 0.65) / 1.0 * 100 = 35%
        assert result is not None
        assert abs(result - 35.0) < 0.01

    def test_valid_both_parallels(self):
        """Valid p1 and p2"""
        from app.utils.server_calculations import calc_volatile_vad
        raw = {
            "p1": {"m1": 1.0, "m2": 1.0, "m3": 0.65},
            "p2": {"m1": 1.0, "m2": 1.0, "m3": 0.64}
        }
        result = calc_volatile_vad(raw)
        assert result is not None

    def test_empty_raw_data(self):
        """Empty raw data returns None"""
        from app.utils.server_calculations import calc_volatile_vad
        assert calc_volatile_vad({}) is None


class TestCalcTotalMoistureMt:
    """calc_total_moisture_mt тестүүд"""

    def test_import_function(self):
        """Function import"""
        from app.utils.server_calculations import calc_total_moisture_mt
        assert calc_total_moisture_mt is not None

    def test_valid_single_parallel(self):
        """Valid p1 only"""
        from app.utils.server_calculations import calc_total_moisture_mt
        raw = {
            "p1": {"m1": 100.0, "m2": 90.0}
        }
        result = calc_total_moisture_mt(raw)
        # (100 - 90) / 100 * 100 = 10%
        assert result is not None
        assert abs(result - 10.0) < 0.01

    def test_valid_both_parallels(self):
        """Valid p1 and p2"""
        from app.utils.server_calculations import calc_total_moisture_mt
        raw = {
            "p1": {"m1": 100.0, "m2": 90.0},
            "p2": {"m1": 100.0, "m2": 89.0}
        }
        result = calc_total_moisture_mt(raw)
        assert result is not None

    def test_empty_raw_data(self):
        """Empty raw data returns None"""
        from app.utils.server_calculations import calc_total_moisture_mt
        assert calc_total_moisture_mt({}) is None


class TestCalcSulfurTs:
    """calc_sulfur_ts тестүүд"""

    def test_import_function(self):
        """Function import"""
        from app.utils.server_calculations import calc_sulfur_ts
        assert calc_sulfur_ts is not None

    def test_valid_single_parallel(self):
        """Valid p1 only"""
        from app.utils.server_calculations import calc_sulfur_ts
        raw = {
            "p1": {"m1": 0.01, "m2": 0.02, "m_sample": 1.0, "k": 0.34296}
        }
        result = calc_sulfur_ts(raw)
        assert result is not None

    def test_default_k_value(self):
        """Default k value used"""
        from app.utils.server_calculations import calc_sulfur_ts
        raw = {
            "p1": {"m1": 0.01, "m2": 0.02, "m_sample": 1.0}  # no k
        }
        result = calc_sulfur_ts(raw)
        assert result is not None

    def test_empty_raw_data(self):
        """Empty raw data returns None"""
        from app.utils.server_calculations import calc_sulfur_ts
        assert calc_sulfur_ts({}) is None


class TestCalcPhosphorusP:
    """calc_phosphorus_p тестүүд"""

    def test_import_function(self):
        """Function import"""
        from app.utils.server_calculations import calc_phosphorus_p
        assert calc_phosphorus_p is not None

    def test_valid_single_parallel(self):
        """Valid p1 only"""
        from app.utils.server_calculations import calc_phosphorus_p
        raw = {
            "p1": {"v": 10.0, "v0": 0.5, "c": 0.01, "m_sample": 1.0}
        }
        result = calc_phosphorus_p(raw)
        assert result is not None

    def test_empty_raw_data(self):
        """Empty raw data returns None"""
        from app.utils.server_calculations import calc_phosphorus_p
        assert calc_phosphorus_p({}) is None

    def test_zero_m_sample(self):
        """Zero m_sample returns None"""
        from app.utils.server_calculations import calc_phosphorus_p
        raw = {
            "p1": {"v": 10.0, "v0": 0.5, "c": 0.01, "m_sample": 0}
        }
        assert calc_phosphorus_p(raw) is None


class TestCalcFluorineF:
    """calc_fluorine_f тестүүд"""

    def test_import_function(self):
        """Function import"""
        from app.utils.server_calculations import calc_fluorine_f
        assert calc_fluorine_f is not None

    def test_valid_single_parallel(self):
        """Valid p1 only"""
        from app.utils.server_calculations import calc_fluorine_f
        raw = {"p1": {"result": 150.0}}
        result = calc_fluorine_f(raw)
        assert result == 150.0

    def test_valid_both_parallels(self):
        """Valid p1 and p2"""
        from app.utils.server_calculations import calc_fluorine_f
        raw = {
            "p1": {"result": 150.0},
            "p2": {"result": 160.0}
        }
        result = calc_fluorine_f(raw)
        assert result == 155.0

    def test_empty_raw_data(self):
        """Empty raw data returns None"""
        from app.utils.server_calculations import calc_fluorine_f
        assert calc_fluorine_f({}) is None

    def test_negative_result_skipped(self):
        """Negative result skipped"""
        from app.utils.server_calculations import calc_fluorine_f
        raw = {"p1": {"result": -10.0}}
        assert calc_fluorine_f(raw) is None


class TestCalcChlorineCl:
    """calc_chlorine_cl тестүүд"""

    def test_import_function(self):
        """Function import"""
        from app.utils.server_calculations import calc_chlorine_cl
        assert calc_chlorine_cl is not None

    def test_valid_single_parallel(self):
        """Valid p1 only"""
        from app.utils.server_calculations import calc_chlorine_cl
        raw = {"p1": {"result": 200.0}}
        result = calc_chlorine_cl(raw)
        assert result == 200.0

    def test_valid_both_parallels(self):
        """Valid p1 and p2"""
        from app.utils.server_calculations import calc_chlorine_cl
        raw = {
            "p1": {"result": 200.0},
            "p2": {"result": 210.0}
        }
        result = calc_chlorine_cl(raw)
        assert result == 205.0

    def test_empty_raw_data(self):
        """Empty raw data returns None"""
        from app.utils.server_calculations import calc_chlorine_cl
        assert calc_chlorine_cl({}) is None


class TestCalcCalorificValueCv:
    """calc_calorific_value_cv тестүүд"""

    def test_import_function(self):
        """Function import"""
        from app.utils.server_calculations import calc_calorific_value_cv
        assert calc_calorific_value_cv is not None

    def test_valid_single_parallel(self):
        """Valid p1 only"""
        from app.utils.server_calculations import calc_calorific_value_cv
        raw = {
            "batch": {"E": 10000.0, "q1": 50.0, "q2": 30.0},
            "p1": {"m": 1.0, "delta_t": 2.5},
            "s_used": 0.5
        }
        result = calc_calorific_value_cv(raw)
        assert result is not None

    def test_valid_both_parallels(self):
        """Valid p1 and p2"""
        from app.utils.server_calculations import calc_calorific_value_cv
        raw = {
            "batch": {"E": 10000.0, "q1": 50.0, "q2": 30.0},
            "p1": {"m": 1.0, "delta_t": 2.5},
            "p2": {"m": 1.0, "delta_t": 2.6},
            "s_used": 0.5
        }
        result = calc_calorific_value_cv(raw)
        assert result is not None

    def test_empty_raw_data(self):
        """Empty raw data returns None"""
        from app.utils.server_calculations import calc_calorific_value_cv
        assert calc_calorific_value_cv({}) is None

    def test_zero_mass(self):
        """Zero mass returns None"""
        from app.utils.server_calculations import calc_calorific_value_cv
        raw = {
            "batch": {"E": 10000.0, "q1": 50.0},
            "p1": {"m": 0, "delta_t": 2.5}
        }
        assert calc_calorific_value_cv(raw) is None

    def test_alternative_field_names(self):
        """Alternative field names (dT, temp)"""
        from app.utils.server_calculations import calc_calorific_value_cv
        raw = {
            "batch": {"E": 10000.0, "q1": 50.0},
            "p1": {"m1": 1.0, "dT": 2.5}
        }
        result = calc_calorific_value_cv(raw)
        assert result is not None

    def test_no_q2(self):
        """No q2 uses 0"""
        from app.utils.server_calculations import calc_calorific_value_cv
        raw = {
            "batch": {"E": 10000.0, "q1": 50.0},  # no q2
            "p1": {"m": 1.0, "delta_t": 2.5}
        }
        result = calc_calorific_value_cv(raw)
        assert result is not None


class TestCalcGrayKingGi:
    """calc_gray_king_gi тестүүд"""

    def test_import_function(self):
        """Function import"""
        from app.utils.server_calculations import calc_gray_king_gi
        assert calc_gray_king_gi is not None

    def test_valid_51_mode(self):
        """Valid 5:1 mode"""
        from app.utils.server_calculations import calc_gray_king_gi
        raw = {
            "p1": {"m1": 5.0, "m2": 1.0, "m3": 2.0}
        }
        result = calc_gray_king_gi(raw)
        # Gi = 10 + (30*1 + 70*2) / 5 = 10 + 34 = 44
        assert result is not None

    def test_valid_33_mode(self):
        """Valid 3:3 mode (retest)"""
        from app.utils.server_calculations import calc_gray_king_gi
        raw = {
            "p1": {"m1": 3.0, "m2": 1.0, "m3": 2.0, "mode": "3:3"}
        }
        result = calc_gray_king_gi(raw)
        assert result is not None

    def test_retest_mode(self):
        """Retest mode detection"""
        from app.utils.server_calculations import calc_gray_king_gi
        raw = {
            "p1": {"m1": 3.0, "m2": 1.0, "m3": 2.0, "retest_mode": "retest"}
        }
        result = calc_gray_king_gi(raw)
        assert result is not None

    def test_both_parallels(self):
        """Both parallels"""
        from app.utils.server_calculations import calc_gray_king_gi
        raw = {
            "p1": {"m1": 5.0, "m2": 1.0, "m3": 2.0},
            "p2": {"m1": 5.0, "m2": 1.0, "m3": 2.1}
        }
        result = calc_gray_king_gi(raw)
        assert result is not None

    def test_empty_raw_data(self):
        """Empty raw data returns None"""
        from app.utils.server_calculations import calc_gray_king_gi
        assert calc_gray_king_gi({}) is None


class TestVerifyAndRecalculate:
    """verify_and_recalculate тестүүд"""

    def test_import_function(self):
        """Function import"""
        from app.utils.server_calculations import verify_and_recalculate
        assert verify_and_recalculate is not None

    def test_unknown_analysis(self):
        """Unknown analysis uses client value"""
        from app.utils.server_calculations import verify_and_recalculate
        result, warnings = verify_and_recalculate(
            analysis_code="UNKNOWN",
            client_final_result=10.0,
            raw_data={}
        )
        assert result == 10.0

    def test_mad_calculation(self):
        """Mad calculation"""
        from app.utils.server_calculations import verify_and_recalculate
        raw = {
            "p1": {"m1": 10.0, "m2": 1.0, "m3": 10.95}
        }
        result, warnings = verify_and_recalculate(
            analysis_code="Mad",
            client_final_result=5.0,
            raw_data=raw
        )
        assert result is not None

    def test_aad_calculation(self):
        """Aad calculation"""
        from app.utils.server_calculations import verify_and_recalculate
        raw = {
            "p1": {"m1": 10.0, "m2": 1.0, "m3": 10.15}
        }
        result, warnings = verify_and_recalculate(
            analysis_code="Aad",
            client_final_result=15.0,
            raw_data=raw
        )
        assert result is not None

    def test_cv_calculation(self):
        """CV calculation"""
        from app.utils.server_calculations import verify_and_recalculate
        raw = {
            "batch": {"E": 10000.0, "q1": 50.0},
            "p1": {"m": 1.0, "delta_t": 2.5}
        }
        result, warnings = verify_and_recalculate(
            analysis_code="CV",
            client_final_result=6000.0,
            raw_data=raw
        )
        assert result is not None

    def test_empty_raw_data(self):
        """Empty raw data falls back to client"""
        from app.utils.server_calculations import verify_and_recalculate
        result, warnings = verify_and_recalculate(
            analysis_code="Mad",
            client_final_result=5.0,
            raw_data={}
        )
        # Falls back to client value when calculation fails
        assert result is not None

    def test_none_client_result(self):
        """None client result"""
        from app.utils.server_calculations import verify_and_recalculate
        result, warnings = verify_and_recalculate(
            analysis_code="UNKNOWN",
            client_final_result=None,
            raw_data={}
        )
        assert result is None


class TestCalculationFunctions:
    """CALCULATION_FUNCTIONS dict тестүүд"""

    def test_import_dict(self):
        """Dict import"""
        from app.utils.server_calculations import CALCULATION_FUNCTIONS
        assert CALCULATION_FUNCTIONS is not None
        assert isinstance(CALCULATION_FUNCTIONS, dict)

    def test_has_mad(self):
        """Has Mad"""
        from app.utils.server_calculations import CALCULATION_FUNCTIONS
        assert "Mad" in CALCULATION_FUNCTIONS

    def test_has_aad(self):
        """Has Aad"""
        from app.utils.server_calculations import CALCULATION_FUNCTIONS
        assert "Aad" in CALCULATION_FUNCTIONS

    def test_has_cv(self):
        """Has CV"""
        from app.utils.server_calculations import CALCULATION_FUNCTIONS
        assert "CV" in CALCULATION_FUNCTIONS


class TestConstants:
    """Constants тестүүд"""

    def test_epsilon(self):
        """EPSILON exists"""
        from app.utils.server_calculations import EPSILON
        assert EPSILON > 0
        assert EPSILON <= 1.0
