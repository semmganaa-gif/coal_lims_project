# tests/unit/test_server_calculations.py
# -*- coding: utf-8 -*-
"""
Server-Side Calculation тест

Tests for all coal analysis calculation functions.
"""

import pytest
from math import isnan
from unittest.mock import patch

from app.utils.server_calculations import (
    _safe_float,
    _get_from_dict,
    calc_moisture_mad,
    calc_ash_aad,
    calc_volatile_vad,
    calc_total_moisture_mt,
    calc_sulfur_ts,
    calc_phosphorus_p,
    calc_fluorine_f,
    calc_chlorine_cl,
    calc_calorific_value_cv,
    calc_gray_king_gi,
    calc_free_moisture_fm,
    calc_solid,
    calc_trd,
    verify_and_recalculate,
    bulk_verify_results,
    CALCULATION_FUNCTIONS,
)


class TestSafeFloat:
    """_safe_float() функцийн тест"""

    def test_valid_float(self):
        """Зөв float утга"""
        assert _safe_float(3.14) == 3.14

    def test_valid_int(self):
        """Integer -> float"""
        assert _safe_float(5) == 5.0

    def test_valid_string(self):
        """String -> float"""
        assert _safe_float("3.14") == 3.14

    def test_none_returns_none(self):
        """None -> None"""
        assert _safe_float(None) is None

    def test_invalid_string(self):
        """Буруу string -> None"""
        assert _safe_float("abc") is None

    def test_nan_returns_none(self):
        """NaN -> None"""
        assert _safe_float(float('nan')) is None

    def test_inf_returns_none(self):
        """Infinity -> None"""
        assert _safe_float(float('inf')) is None
        assert _safe_float(float('-inf')) is None


class TestGetFromDict:
    """_get_from_dict() функцийн тест"""

    def test_simple_key(self):
        """Энгийн key"""
        d = {"a": 1.5}
        assert _get_from_dict(d, "a") == 1.5

    def test_nested_keys(self):
        """Nested keys"""
        d = {"p1": {"m1": 10.5}}
        assert _get_from_dict(d, "p1", "m1") == 10.5

    def test_missing_key(self):
        """Байхгүй key"""
        d = {"a": 1.0}
        assert _get_from_dict(d, "b") is None

    def test_missing_nested_key(self):
        """Байхгүй nested key"""
        d = {"p1": {"m1": 10.0}}
        assert _get_from_dict(d, "p1", "m2") is None

    def test_non_dict_value(self):
        """Dict биш утга"""
        d = {"p1": "not a dict"}
        assert _get_from_dict(d, "p1", "m1") is None

    def test_converts_to_float(self):
        """String -> float"""
        d = {"a": "3.14"}
        assert _get_from_dict(d, "a") == 3.14


class TestCalcMoistureMad:
    """calc_moisture_mad() тест - Аналитик чийг"""

    def test_valid_calculation_p1_only(self):
        """P1 зөвхөн"""
        raw_data = {
            "p1": {"m1": 10.0, "m2": 1.0, "m3": 10.97}
        }
        # Mad = ((m1 + m2) - m3) / m2 * 100 = ((10+1) - 10.97) / 1 * 100 = 3%
        result = calc_moisture_mad(raw_data)
        assert result is not None
        assert abs(result - 3.0) < 0.01

    def test_valid_calculation_both_parallels(self):
        """P1 болон P2"""
        raw_data = {
            "p1": {"m1": 10.0, "m2": 1.0, "m3": 10.97},
            "p2": {"m1": 10.0, "m2": 1.0, "m3": 10.96}
        }
        # P1: 3%, P2: 4%, Average: 3.5%
        result = calc_moisture_mad(raw_data)
        assert result is not None
        assert abs(result - 3.5) < 0.01

    def test_empty_data(self):
        """Хоосон өгөгдөл"""
        assert calc_moisture_mad({}) is None

    def test_missing_values(self):
        """Дутуу утга"""
        raw_data = {"p1": {"m1": 10.0, "m2": 1.0}}  # m3 байхгүй
        assert calc_moisture_mad(raw_data) is None

    def test_zero_denominator(self):
        """m2=0 үед"""
        raw_data = {"p1": {"m1": 10.0, "m2": 0, "m3": 10.5}}
        assert calc_moisture_mad(raw_data) is None


class TestCalcAshAad:
    """calc_ash_aad() тест - Үнс"""

    def test_valid_calculation(self):
        """Зөв тооцоолол"""
        raw_data = {
            "p1": {"m1": 20.0, "m2": 1.0, "m3": 20.1}
        }
        # Aad = (m3 - m1) / m2 * 100 = (20.1 - 20) / 1 * 100 = 10%
        result = calc_ash_aad(raw_data)
        assert result is not None
        assert abs(result - 10.0) < 0.01

    def test_two_parallels(self):
        """Хоёр parallel"""
        raw_data = {
            "p1": {"m1": 20.0, "m2": 1.0, "m3": 20.1},
            "p2": {"m1": 20.0, "m2": 1.0, "m3": 20.12}
        }
        result = calc_ash_aad(raw_data)
        assert result is not None
        assert abs(result - 11.0) < 0.01  # Average of 10 and 12

    def test_empty_data(self):
        """Хоосон өгөгдөл"""
        assert calc_ash_aad({}) is None


class TestCalcVolatileVad:
    """calc_volatile_vad() тест - Дэгдэмхий бодис"""

    def test_valid_calculation(self):
        """Зөв тооцоолол"""
        raw_data = {
            "p1": {"m1": 1.0, "m2": 1.3, "m3": 1.0}
        }
        # Vad = ((m2 - m3) / m1) * 100 = ((1.3 - 1.0) / 1.0) * 100 = 30%
        result = calc_volatile_vad(raw_data)
        assert result is not None
        assert abs(result - 30.0) < 0.01

    def test_empty_data(self):
        """Хоосон өгөгдөл"""
        assert calc_volatile_vad({}) is None


class TestCalcTotalMoistureMt:
    """calc_total_moisture_mt() тест - Нийт чийг"""

    def test_valid_calculation(self):
        """Зөв тооцоолол"""
        raw_data = {
            "p1": {"m1": 100.0, "m2": 90.0}
        }
        # MT = ((m1 - m2) / m1) * 100 = ((100 - 90) / 100) * 100 = 10%
        result = calc_total_moisture_mt(raw_data)
        assert result is not None
        assert abs(result - 10.0) < 0.01

    def test_empty_data(self):
        """Хоосон өгөгдөл"""
        assert calc_total_moisture_mt({}) is None


class TestCalcSulfurTs:
    """calc_sulfur_ts() тест - Хүхэр"""

    def test_valid_calculation(self):
        """Зөв тооцоолол"""
        raw_data = {
            "p1": {"m1": 1.0, "m2": 1.1, "m_sample": 1.0, "k": 0.34296}
        }
        # S = ((m2 - m1) / m_sample) * k * 100
        result = calc_sulfur_ts(raw_data)
        assert result is not None
        assert result > 0

    def test_default_k(self):
        """k байхгүй үед default"""
        raw_data = {
            "p1": {"m1": 1.0, "m2": 1.1, "m_sample": 1.0}
        }
        result = calc_sulfur_ts(raw_data)
        assert result is not None

    def test_empty_data(self):
        """Хоосон өгөгдөл"""
        assert calc_sulfur_ts({}) is None


class TestCalcPhosphorusP:
    """calc_phosphorus_p() тест - Фосфор"""

    def test_valid_calculation(self):
        """Зөв тооцоолол"""
        raw_data = {
            "p1": {"v": 10.0, "v0": 0.5, "c": 0.1, "m_sample": 0.5}
        }
        result = calc_phosphorus_p(raw_data)
        assert result is not None
        assert result >= 0

    def test_empty_data(self):
        """Хоосон өгөгдөл"""
        assert calc_phosphorus_p({}) is None


class TestCalcFluorineF:
    """calc_fluorine_f() тест - Фтор"""

    def test_single_result(self):
        """Нэг үр дүн"""
        raw_data = {"p1": {"result": 0.05}}
        result = calc_fluorine_f(raw_data)
        assert result == 0.05

    def test_two_results(self):
        """Хоёр үр дүн"""
        raw_data = {
            "p1": {"result": 0.04},
            "p2": {"result": 0.06}
        }
        result = calc_fluorine_f(raw_data)
        assert result == 0.05  # Average

    def test_negative_result_ignored(self):
        """Сөрөг утга орохгүй"""
        raw_data = {
            "p1": {"result": -0.05},
            "p2": {"result": 0.06}
        }
        result = calc_fluorine_f(raw_data)
        assert result == 0.06

    def test_empty_data(self):
        """Хоосон өгөгдөл"""
        assert calc_fluorine_f({}) is None


class TestCalcChlorineCl:
    """calc_chlorine_cl() тест - Хлор"""

    def test_valid_calculation(self):
        """Зөв тооцоолол"""
        raw_data = {"p1": {"result": 0.1}}
        result = calc_chlorine_cl(raw_data)
        assert result == 0.1

    def test_empty_data(self):
        """Хоосон өгөгдөл"""
        assert calc_chlorine_cl({}) is None


class TestCalcCalorificValueCv:
    """calc_calorific_value_cv() тест - Илчлэг"""

    def test_valid_calculation(self):
        """Зөв тооцоолол"""
        raw_data = {
            "batch": {"E": 10000, "q1": 50, "q2": 10},
            "p1": {"m": 1.0, "delta_t": 2.5, "s": 0.5}
        }
        result = calc_calorific_value_cv(raw_data)
        assert result is not None
        assert result > 0

    def test_two_parallels(self):
        """Хоёр parallel"""
        raw_data = {
            "batch": {"E": 10000, "q1": 50, "q2": 10},
            "p1": {"m": 1.0, "delta_t": 2.5, "s": 0.5},
            "p2": {"m": 1.0, "delta_t": 2.6, "s": 0.5}
        }
        result = calc_calorific_value_cv(raw_data)
        assert result is not None

    def test_empty_data(self):
        """Хоосон өгөгдөл"""
        assert calc_calorific_value_cv({}) is None

    def test_missing_mass(self):
        """m байхгүй"""
        raw_data = {
            "batch": {"E": 10000, "q1": 50},
            "p1": {"delta_t": 2.5}
        }
        assert calc_calorific_value_cv(raw_data) is None

    def test_zero_mass(self):
        """m=0"""
        raw_data = {
            "batch": {"E": 10000, "q1": 50},
            "p1": {"m": 0, "delta_t": 2.5}
        }
        assert calc_calorific_value_cv(raw_data) is None


class TestCalcGrayKingGi:
    """calc_gray_king_gi() тест - Gray-King Index"""

    def test_normal_mode_5_1(self):
        """5:1 mode (default)"""
        raw_data = {
            "p1": {"m1": 1.0, "m2": 0.1, "m3": 0.2}
        }
        # Gi = 10 + (30*m2 + 70*m3) / m1 = 10 + (30*0.1 + 70*0.2) / 1 = 10 + 17 = 27
        result = calc_gray_king_gi(raw_data)
        assert result is not None
        assert abs(result - 27) < 1

    def test_retest_mode_3_3(self):
        """3:3 mode (retest)"""
        raw_data = {
            "p1": {"m1": 1.0, "m2": 0.1, "m3": 0.2, "mode": "3:3"}
        }
        # Gi = (30*m2 + 70*m3) / (5*m1) = (30*0.1 + 70*0.2) / (5*1) = 17/5 = 3.4
        result = calc_gray_king_gi(raw_data)
        assert result is not None

    def test_empty_data(self):
        """Хоосон өгөгдөл"""
        assert calc_gray_king_gi({}) is None


class TestCalcFreeMoistureFm:
    """calc_free_moisture_fm() тест - Чөлөөт чийг"""

    def test_valid_calculation(self):
        """Зөв тооцоолол"""
        raw_data = {
            "p1": {"wt": 50.0, "wb": 160.0, "wa": 150.0}
        }
        # FM = ((wb - wa) / (wa - wt)) * 100 = ((160-150) / (150-50)) * 100 = 10%
        result = calc_free_moisture_fm(raw_data)
        assert result is not None
        assert abs(result - 10.0) < 0.01

    def test_zero_denominator(self):
        """wa == wt үед"""
        raw_data = {
            "p1": {"wt": 50.0, "wb": 60.0, "wa": 50.0}
        }
        assert calc_free_moisture_fm(raw_data) is None

    def test_empty_data(self):
        """Хоосон өгөгдөл"""
        assert calc_free_moisture_fm({}) is None


class TestCalcSolid:
    """calc_solid() тест - Хатуу бодис"""

    def test_valid_calculation(self):
        """Зөв тооцоолол"""
        raw_data = {
            "p1": {"a": 110.0, "b": 100.0, "c": 5.0}
        }
        # Solid = (c * 100) / (a - b) = (5 * 100) / (110 - 100) = 50%
        result = calc_solid(raw_data)
        assert result is not None
        assert abs(result - 50.0) < 0.01

    def test_zero_denominator(self):
        """a == b үед"""
        raw_data = {"p1": {"a": 100.0, "b": 100.0, "c": 5.0}}
        assert calc_solid(raw_data) is None

    def test_empty_data(self):
        """Хоосон өгөгдөл"""
        assert calc_solid({}) is None


class TestCalcTrd:
    """calc_trd() тест - Үнэн харьцангуй нягт"""

    def test_valid_calculation(self):
        """Зөв тооцоолол"""
        raw_data = {
            "p1": {
                "m": 1.0,
                "m1": 50.0,
                "m2": 50.5,
                "temp": 20,
                "mad": 5.0
            }
        }
        result = calc_trd(raw_data)
        assert result is not None
        assert result > 0

    def test_global_mad(self):
        """Global mad утга"""
        raw_data = {
            "mad": 5.0,
            "p1": {
                "m": 1.0,
                "m1": 50.0,
                "m2": 50.5,
                "temp": 20
            }
        }
        result = calc_trd(raw_data)
        assert result is not None

    def test_temperature_out_of_range(self):
        """Температур хязгаараас гарсан"""
        raw_data = {
            "p1": {
                "m": 1.0,
                "m1": 50.0,
                "m2": 50.5,
                "temp": 40,  # Out of range (6-35)
                "mad": 5.0
            }
        }
        assert calc_trd(raw_data) is None

    def test_empty_data(self):
        """Хоосон өгөгдөл"""
        assert calc_trd({}) is None


class TestVerifyAndRecalculate:
    """verify_and_recalculate() функцийн тест"""

    def test_known_analysis_code(self):
        """Танигдсан analysis code"""
        raw_data = {
            "p1": {"m1": 10.0, "m2": 1.0, "m3": 10.97}
        }
        result, warnings = verify_and_recalculate(
            analysis_code="Mad",
            client_final_result=3.0,
            raw_data=raw_data
        )
        assert result is not None
        assert abs(result - 3.0) < 0.1

    def test_unknown_analysis_code(self):
        """Танигдаагүй analysis code"""
        result, warnings = verify_and_recalculate(
            analysis_code="UnknownCode",
            client_final_result=5.0,
            raw_data={}
        )
        # Should return client value
        assert result == 5.0

    def test_mismatch_warning(self):
        """Client/Server зөрүү"""
        raw_data = {
            "p1": {"m1": 10.0, "m2": 1.0, "m3": 10.97}
        }
        # Correct result is ~3.0, but client sends 10.0
        result, warnings = verify_and_recalculate(
            analysis_code="Mad",
            client_final_result=10.0,
            raw_data=raw_data
        )
        assert result is not None
        assert len(warnings) > 0
        assert "MISMATCH" in warnings[0]

    def test_calculation_error(self):
        """Тооцооллын алдаа"""
        # Pass invalid raw_data that might cause error
        result, warnings = verify_and_recalculate(
            analysis_code="Mad",
            client_final_result=5.0,
            raw_data={"p1": {"m1": "invalid"}}
        )
        # Should handle gracefully
        assert result is not None or len(warnings) > 0


class TestBulkVerifyResults:
    """bulk_verify_results() функцийн тест"""

    def test_multiple_items(self):
        """Олон item шалгах"""
        items = [
            {
                "analysis_code": "Mad",
                "final_result": 3.0,
                "raw_data": {"p1": {"m1": 10.0, "m2": 1.0, "m3": 10.97}},
                "sample_id": 1
            },
            {
                "analysis_code": "Aad",
                "final_result": 10.0,
                "raw_data": {"p1": {"m1": 20.0, "m2": 1.0, "m3": 20.1}},
                "sample_id": 2
            }
        ]

        result = bulk_verify_results(items)

        assert "verified_items" in result
        assert len(result["verified_items"]) == 2
        assert result["total_warnings"] >= 0
        assert result["total_mismatches"] >= 0

    def test_empty_items(self):
        """Хоосон жагсаалт"""
        result = bulk_verify_results([])
        assert result["verified_items"] == []
        assert result["total_warnings"] == 0
        assert result["total_mismatches"] == 0

    def test_items_have_server_verified_flag(self):
        """server_verified flag"""
        items = [
            {
                "analysis_code": "F",
                "final_result": 0.05,
                "raw_data": {"p1": {"result": 0.05}},
                "sample_id": 1
            }
        ]

        result = bulk_verify_results(items)
        assert result["verified_items"][0]["server_verified"] is True


class TestCalculationFunctionsMapping:
    """CALCULATION_FUNCTIONS mapping тест"""

    def test_mad_aliases(self):
        """Mad aliases"""
        assert CALCULATION_FUNCTIONS.get("Mad") is not None
        assert CALCULATION_FUNCTIONS.get("M") is not None

    def test_aad_aliases(self):
        """Aad aliases"""
        assert CALCULATION_FUNCTIONS.get("Aad") is not None
        assert CALCULATION_FUNCTIONS.get("A") is not None

    def test_cv_aliases(self):
        """CV aliases"""
        assert CALCULATION_FUNCTIONS.get("CV") is not None
        assert CALCULATION_FUNCTIONS.get("Qgr,ad") is not None
        assert CALCULATION_FUNCTIONS.get("Qgr") is not None

    def test_sulfur_aliases(self):
        """Sulfur aliases"""
        assert CALCULATION_FUNCTIONS.get("TS") is not None
        assert CALCULATION_FUNCTIONS.get("St,ad") is not None
        assert CALCULATION_FUNCTIONS.get("S") is not None
