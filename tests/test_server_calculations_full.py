# tests/test_server_calculations_full.py
# -*- coding: utf-8 -*-
"""
Complete tests for app/utils/server_calculations.py
"""

import pytest
from unittest.mock import patch, MagicMock


class TestSafeFloat:
    """Tests for _safe_float helper function."""

    def test_none_returns_none(self, app):
        """Test None returns None."""
        with app.app_context():
            from app.utils.server_calculations import _safe_float
            result = _safe_float(None)
            assert result is None

    def test_int_returns_float(self, app):
        """Test int returns float."""
        with app.app_context():
            from app.utils.server_calculations import _safe_float
            result = _safe_float(10)
            assert result == 10.0

    def test_float_returns_float(self, app):
        """Test float returns float."""
        with app.app_context():
            from app.utils.server_calculations import _safe_float
            result = _safe_float(10.5)
            assert result == 10.5

    def test_string_number(self, app):
        """Test string number returns float."""
        with app.app_context():
            from app.utils.server_calculations import _safe_float
            result = _safe_float("10.5")
            assert result == 10.5

    def test_invalid_string_returns_none(self, app):
        """Test invalid string returns None."""
        with app.app_context():
            from app.utils.server_calculations import _safe_float
            result = _safe_float("not_a_number")
            assert result is None

    def test_inf_returns_none(self, app):
        """Test infinity returns None."""
        with app.app_context():
            from app.utils.server_calculations import _safe_float
            result = _safe_float(float('inf'))
            assert result is None


class TestGetFromDict:
    """Tests for _get_from_dict helper function."""

    def test_simple_key(self, app):
        """Test simple key access."""
        with app.app_context():
            from app.utils.server_calculations import _get_from_dict
            d = {'key': 10.5}
            result = _get_from_dict(d, 'key')
            assert result == 10.5

    def test_nested_key(self, app):
        """Test nested key access."""
        with app.app_context():
            from app.utils.server_calculations import _get_from_dict
            d = {'p1': {'m1': 10.5}}
            result = _get_from_dict(d, 'p1', 'm1')
            assert result == 10.5

    def test_missing_key_returns_none(self, app):
        """Test missing key returns None."""
        with app.app_context():
            from app.utils.server_calculations import _get_from_dict
            d = {'p1': {'m1': 10.5}}
            result = _get_from_dict(d, 'p1', 'm2')
            assert result is None

    def test_non_dict_intermediate_returns_none(self, app):
        """Test non-dict intermediate returns None."""
        with app.app_context():
            from app.utils.server_calculations import _get_from_dict
            d = {'p1': 'not a dict'}
            result = _get_from_dict(d, 'p1', 'm1')
            assert result is None


class TestCalcMoistureMad:
    """Tests for calc_moisture_mad function."""

    def test_valid_calculation(self, app):
        """Test valid Mad calculation."""
        with app.app_context():
            from app.utils.server_calculations import calc_moisture_mad
            raw_data = {
                'p1': {'m1': 20.0, 'm2': 1.0, 'm3': 20.95},
                'p2': {'m1': 20.0, 'm2': 1.0, 'm3': 20.94}
            }
            result = calc_moisture_mad(raw_data)
            assert result is not None
            assert abs(result - 5.0) < 0.5  # Expected ~5% moisture

    def test_missing_data_returns_none(self, app):
        """Test missing data returns None."""
        with app.app_context():
            from app.utils.server_calculations import calc_moisture_mad
            raw_data = {'p1': {'m1': 20.0}}  # Missing m2, m3
            result = calc_moisture_mad(raw_data)
            assert result is None

    def test_single_parallel(self, app):
        """Test with single parallel."""
        with app.app_context():
            from app.utils.server_calculations import calc_moisture_mad
            raw_data = {
                'p1': {'m1': 20.0, 'm2': 1.0, 'm3': 20.95}
            }
            result = calc_moisture_mad(raw_data)
            assert result is not None


class TestCalcAshAad:
    """Tests for calc_ash_aad function."""

    def test_valid_calculation(self, app):
        """Test valid Aad calculation."""
        with app.app_context():
            from app.utils.server_calculations import calc_ash_aad
            raw_data = {
                'p1': {'m1': 20.0, 'm2': 1.0, 'm3': 20.10},
                'p2': {'m1': 20.0, 'm2': 1.0, 'm3': 20.11}
            }
            result = calc_ash_aad(raw_data)
            assert result is not None

    def test_missing_data_returns_none(self, app):
        """Test missing data returns None."""
        with app.app_context():
            from app.utils.server_calculations import calc_ash_aad
            raw_data = {}
            result = calc_ash_aad(raw_data)
            assert result is None


class TestCalcVolatileVad:
    """Tests for calc_volatile_vad function."""

    def test_valid_calculation(self, app):
        """Test valid Vad calculation."""
        with app.app_context():
            from app.utils.server_calculations import calc_volatile_vad
            raw_data = {
                'p1': {'m1': 1.0, 'm2': 21.0, 'm3': 20.7},
                'p2': {'m1': 1.0, 'm2': 21.0, 'm3': 20.65}
            }
            result = calc_volatile_vad(raw_data)
            assert result is not None

    def test_missing_data_returns_none(self, app):
        """Test missing data returns None."""
        with app.app_context():
            from app.utils.server_calculations import calc_volatile_vad
            raw_data = {}
            result = calc_volatile_vad(raw_data)
            assert result is None


class TestCalcTotalMoistureMt:
    """Tests for calc_total_moisture_mt function."""

    def test_valid_calculation(self, app):
        """Test valid MT calculation."""
        with app.app_context():
            from app.utils.server_calculations import calc_total_moisture_mt
            raw_data = {
                'p1': {'m1': 100.0, 'm2': 85.0},
                'p2': {'m1': 100.0, 'm2': 86.0}
            }
            result = calc_total_moisture_mt(raw_data)
            assert result is not None
            assert abs(result - 14.5) < 0.5  # Expected ~14.5% moisture

    def test_missing_data_returns_none(self, app):
        """Test missing data returns None."""
        with app.app_context():
            from app.utils.server_calculations import calc_total_moisture_mt
            raw_data = {}
            result = calc_total_moisture_mt(raw_data)
            assert result is None


class TestCalcFluorine:
    """Tests for calc_fluorine_f function."""

    def test_valid_calculation(self, app):
        """Test valid F calculation."""
        with app.app_context():
            from app.utils.server_calculations import calc_fluorine_f
            raw_data = {
                'p1': {'result': 150.0},
                'p2': {'result': 155.0}
            }
            result = calc_fluorine_f(raw_data)
            assert result is not None
            assert abs(result - 152.5) < 0.1

    def test_missing_data_returns_none(self, app):
        """Test missing data returns None."""
        with app.app_context():
            from app.utils.server_calculations import calc_fluorine_f
            raw_data = {}
            result = calc_fluorine_f(raw_data)
            assert result is None


class TestCalcChlorine:
    """Tests for calc_chlorine_cl function."""

    def test_valid_calculation(self, app):
        """Test valid Cl calculation."""
        with app.app_context():
            from app.utils.server_calculations import calc_chlorine_cl
            raw_data = {
                'p1': {'result': 200.0},
                'p2': {'result': 205.0}
            }
            result = calc_chlorine_cl(raw_data)
            assert result is not None

    def test_missing_data_returns_none(self, app):
        """Test missing data returns None."""
        with app.app_context():
            from app.utils.server_calculations import calc_chlorine_cl
            raw_data = {}
            result = calc_chlorine_cl(raw_data)
            assert result is None


class TestCalcGrayKingGi:
    """Tests for calc_gray_king_gi function."""

    def test_5_1_mode(self, app):
        """Test Gi 5:1 mode calculation."""
        with app.app_context():
            from app.utils.server_calculations import calc_gray_king_gi
            raw_data = {
                'p1': {'m1': 1.0, 'm2': 0.5, 'm3': 0.5},
                'p2': {'m1': 1.0, 'm2': 0.5, 'm3': 0.5}
            }
            result = calc_gray_king_gi(raw_data)
            assert result is not None

    def test_3_3_mode(self, app):
        """Test Gi 3:3 mode calculation."""
        with app.app_context():
            from app.utils.server_calculations import calc_gray_king_gi
            raw_data = {
                'p1': {'m1': 1.0, 'm2': 0.5, 'm3': 0.5, 'mode': '3:3'}
            }
            result = calc_gray_king_gi(raw_data)
            assert result is not None

    def test_missing_data_returns_none(self, app):
        """Test missing data returns None."""
        with app.app_context():
            from app.utils.server_calculations import calc_gray_king_gi
            raw_data = {}
            result = calc_gray_king_gi(raw_data)
            assert result is None


class TestCalcFreeMoistureFm:
    """Tests for calc_free_moisture_fm function."""

    def test_valid_calculation(self, app):
        """Test valid FM calculation."""
        with app.app_context():
            from app.utils.server_calculations import calc_free_moisture_fm
            raw_data = {
                'p1': {'wt': 100.0, 'wb': 200.0, 'wa': 180.0},
                'p2': {'wt': 100.0, 'wb': 200.0, 'wa': 182.0}
            }
            result = calc_free_moisture_fm(raw_data)
            assert result is not None

    def test_zero_denominator_returns_none(self, app):
        """Test zero denominator returns None."""
        with app.app_context():
            from app.utils.server_calculations import calc_free_moisture_fm
            raw_data = {
                'p1': {'wt': 100.0, 'wb': 150.0, 'wa': 100.0}  # wa - wt = 0
            }
            result = calc_free_moisture_fm(raw_data)
            assert result is None


class TestCalcSolid:
    """Tests for calc_solid function."""

    def test_valid_calculation(self, app):
        """Test valid Solid calculation."""
        with app.app_context():
            from app.utils.server_calculations import calc_solid
            raw_data = {
                'p1': {'A': 100.0, 'B': 50.0, 'C': 25.0}
            }
            result = calc_solid(raw_data)
            assert result is not None
            assert abs(result - 50.0) < 0.1  # 25 * 100 / (100 - 50) = 50

    def test_zero_denominator_returns_none(self, app):
        """Test zero denominator returns None."""
        with app.app_context():
            from app.utils.server_calculations import calc_solid
            raw_data = {
                'p1': {'A': 50.0, 'B': 50.0, 'C': 25.0}  # A - B = 0
            }
            result = calc_solid(raw_data)
            assert result is None


class TestCalcTrd:
    """Tests for calc_trd function."""

    def test_valid_calculation(self, app):
        """Test valid TRD calculation."""
        with app.app_context():
            from app.utils.server_calculations import calc_trd
            raw_data = {
                'p1': {'m': 1.0, 'm1': 50.0, 'm2': 50.3, 'temp': 20.0},
                'mad': 5.0
            }
            result = calc_trd(raw_data)
            assert result is not None

    def test_invalid_temperature_returns_none(self, app):
        """Test invalid temperature returns None."""
        with app.app_context():
            from app.utils.server_calculations import calc_trd
            raw_data = {
                'p1': {'m': 1.0, 'm1': 50.0, 'm2': 50.3, 'temp': 50.0},  # temp > 35
                'mad': 5.0
            }
            result = calc_trd(raw_data)
            assert result is None


class TestVerifyAndRecalculate:
    """Tests for verify_and_recalculate function."""

    def test_no_calc_function_returns_client_value(self, app):
        """Test returns client value when no calc function."""
        with app.app_context():
            from app.utils.server_calculations import verify_and_recalculate
            result, warnings = verify_and_recalculate(
                'UnknownAnalysis',
                10.5,
                {}
            )
            assert result == 10.5
            assert len(warnings) == 0

    def test_returns_server_calculated_value(self, app):
        """Test returns server calculated value."""
        with app.app_context():
            from app.utils.server_calculations import verify_and_recalculate
            raw_data = {
                'p1': {'result': 150.0},
                'p2': {'result': 155.0}
            }
            result, warnings = verify_and_recalculate('F', 152.5, raw_data)
            assert result is not None

    def test_mismatch_warning(self, app):
        """Test mismatch generates warning."""
        with app.app_context():
            from app.utils.server_calculations import verify_and_recalculate
            raw_data = {
                'p1': {'result': 150.0},
                'p2': {'result': 155.0}
            }
            result, warnings = verify_and_recalculate('F', 200.0, raw_data)  # Client value is wrong
            # Server calculates 152.5, client says 200.0
            assert any('MISMATCH' in w for w in warnings)

    def test_calculation_exception_returns_client(self, app):
        """Test calculation exception returns client value."""
        with app.app_context():
            from app.utils.server_calculations import verify_and_recalculate, CALCULATION_FUNCTIONS
            # Need to patch the dictionary entry since it holds a reference to the function
            original_func = CALCULATION_FUNCTIONS.get('F')
            try:
                CALCULATION_FUNCTIONS['F'] = MagicMock(side_effect=Exception("Calc error"))
                result, warnings = verify_and_recalculate('F', 150.0, {})
                assert result == 150.0
                assert len(warnings) > 0
            finally:
                if original_func:
                    CALCULATION_FUNCTIONS['F'] = original_func


class TestBulkVerifyResults:
    """Tests for bulk_verify_results function."""

    def test_empty_items(self, app):
        """Test with empty items list."""
        with app.app_context():
            from app.utils.server_calculations import bulk_verify_results
            result = bulk_verify_results([])
            assert result['verified_items'] == []
            assert result['total_warnings'] == 0
            assert result['total_mismatches'] == 0

    def test_single_item(self, app):
        """Test with single item."""
        with app.app_context():
            from app.utils.server_calculations import bulk_verify_results
            items = [{
                'analysis_code': 'F',
                'final_result': 150.0,
                'raw_data': {'p1': {'result': 150.0}}
            }]
            result = bulk_verify_results(items)
            assert len(result['verified_items']) == 1
            assert result['verified_items'][0]['server_verified'] is True

    def test_multiple_items(self, app):
        """Test with multiple items."""
        with app.app_context():
            from app.utils.server_calculations import bulk_verify_results
            items = [
                {'analysis_code': 'F', 'final_result': 150.0, 'raw_data': {}},
                {'analysis_code': 'Cl', 'final_result': 200.0, 'raw_data': {}}
            ]
            result = bulk_verify_results(items)
            assert len(result['verified_items']) == 2


class TestCalculationFunctions:
    """Tests for CALCULATION_FUNCTIONS mapping."""

    def test_has_mad(self, app):
        """Test has Mad."""
        with app.app_context():
            from app.utils.server_calculations import CALCULATION_FUNCTIONS
            assert 'Mad' in CALCULATION_FUNCTIONS

    def test_has_aad(self, app):
        """Test has Aad."""
        with app.app_context():
            from app.utils.server_calculations import CALCULATION_FUNCTIONS
            assert 'Aad' in CALCULATION_FUNCTIONS

    def test_has_vad(self, app):
        """Test has Vad."""
        with app.app_context():
            from app.utils.server_calculations import CALCULATION_FUNCTIONS
            assert 'Vad' in CALCULATION_FUNCTIONS

    def test_has_cv(self, app):
        """Test has CV."""
        with app.app_context():
            from app.utils.server_calculations import CALCULATION_FUNCTIONS
            assert 'CV' in CALCULATION_FUNCTIONS

    def test_has_gi(self, app):
        """Test has Gi."""
        with app.app_context():
            from app.utils.server_calculations import CALCULATION_FUNCTIONS
            assert 'Gi' in CALCULATION_FUNCTIONS
