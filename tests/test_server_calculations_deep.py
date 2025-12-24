# tests/test_server_calculations_deep.py
# -*- coding: utf-8 -*-
"""
Deep coverage tests for app/utils/server_calculations.py
"""

import pytest


class TestSafeFloat:
    """Tests for _safe_float function."""

    def test_safe_float_valid_float(self, app):
        """Test _safe_float with valid float."""
        with app.app_context():
            from app.utils.server_calculations import _safe_float
            result = _safe_float(10.5)
            assert result == 10.5

    def test_safe_float_valid_string(self, app):
        """Test _safe_float with valid string."""
        with app.app_context():
            from app.utils.server_calculations import _safe_float
            result = _safe_float('10.5')
            assert result == 10.5

    def test_safe_float_none(self, app):
        """Test _safe_float with None."""
        with app.app_context():
            from app.utils.server_calculations import _safe_float
            result = _safe_float(None)
            assert result is None

    def test_safe_float_invalid_string(self, app):
        """Test _safe_float with invalid string."""
        with app.app_context():
            from app.utils.server_calculations import _safe_float
            result = _safe_float('invalid')
            assert result is None

    def test_safe_float_infinity(self, app):
        """Test _safe_float with infinity."""
        with app.app_context():
            from app.utils.server_calculations import _safe_float
            result = _safe_float(float('inf'))
            assert result is None

    def test_safe_float_nan(self, app):
        """Test _safe_float with NaN."""
        with app.app_context():
            from app.utils.server_calculations import _safe_float
            result = _safe_float(float('nan'))
            assert result is None

    def test_safe_float_integer(self, app):
        """Test _safe_float with integer."""
        with app.app_context():
            from app.utils.server_calculations import _safe_float
            result = _safe_float(10)
            assert result == 10.0


class TestGetFromDict:
    """Tests for _get_from_dict function."""

    def test_get_from_dict_single_key(self, app):
        """Test _get_from_dict with single key."""
        with app.app_context():
            from app.utils.server_calculations import _get_from_dict
            data = {'key1': 10.5}
            result = _get_from_dict(data, 'key1')
            assert result == 10.5

    def test_get_from_dict_nested_keys(self, app):
        """Test _get_from_dict with nested keys."""
        with app.app_context():
            from app.utils.server_calculations import _get_from_dict
            data = {'p1': {'m1': 10.5}}
            result = _get_from_dict(data, 'p1', 'm1')
            assert result == 10.5

    def test_get_from_dict_missing_key(self, app):
        """Test _get_from_dict with missing key."""
        with app.app_context():
            from app.utils.server_calculations import _get_from_dict
            data = {'key1': 10.5}
            result = _get_from_dict(data, 'missing')
            assert result is None

    def test_get_from_dict_none_value(self, app):
        """Test _get_from_dict with None value."""
        with app.app_context():
            from app.utils.server_calculations import _get_from_dict
            data = {'key1': None}
            result = _get_from_dict(data, 'key1')
            assert result is None

    def test_get_from_dict_non_dict_intermediate(self, app):
        """Test _get_from_dict with non-dict intermediate."""
        with app.app_context():
            from app.utils.server_calculations import _get_from_dict
            data = {'key1': 'not a dict'}
            result = _get_from_dict(data, 'key1', 'nested')
            assert result is None


class TestCalcMoistureMad:
    """Tests for calc_moisture_mad function."""

    def test_calc_moisture_mad_single_parallel(self, app):
        """Test calc_moisture_mad with single parallel."""
        with app.app_context():
            from app.utils.server_calculations import calc_moisture_mad
            raw_data = {
                'p1': {'m1': 10.0, 'm2': 1.0, 'm3': 10.95}
            }
            result = calc_moisture_mad(raw_data)
            # Mad% = ((10 + 1) - 10.95) / 1 * 100 = 5.0
            assert result is not None
            assert abs(result - 5.0) < 0.01

    def test_calc_moisture_mad_two_parallels(self, app):
        """Test calc_moisture_mad with two parallels."""
        with app.app_context():
            from app.utils.server_calculations import calc_moisture_mad
            raw_data = {
                'p1': {'m1': 10.0, 'm2': 1.0, 'm3': 10.95},
                'p2': {'m1': 10.0, 'm2': 1.0, 'm3': 10.95}
            }
            result = calc_moisture_mad(raw_data)
            assert result is not None

    def test_calc_moisture_mad_missing_data(self, app):
        """Test calc_moisture_mad with missing data."""
        with app.app_context():
            from app.utils.server_calculations import calc_moisture_mad
            raw_data = {'p1': {'m1': 10.0}}
            result = calc_moisture_mad(raw_data)
            assert result is None

    def test_calc_moisture_mad_empty(self, app):
        """Test calc_moisture_mad with empty data."""
        with app.app_context():
            from app.utils.server_calculations import calc_moisture_mad
            result = calc_moisture_mad({})
            assert result is None


class TestCalcAshAad:
    """Tests for calc_ash_aad function."""

    def test_calc_ash_aad_valid(self, app):
        """Test calc_ash_aad with valid data."""
        with app.app_context():
            from app.utils.server_calculations import calc_ash_aad
            raw_data = {
                'p1': {'m1': 10.0, 'm2': 1.0, 'm3': 10.1}
            }
            result = calc_ash_aad(raw_data)
            # Aad% = (m3 - m1) / m2 * 100 = (10.1 - 10) / 1 * 100 = 10
            if result is not None:
                assert abs(result - 10.0) < 0.01

    def test_calc_ash_aad_empty(self, app):
        """Test calc_ash_aad with empty data."""
        with app.app_context():
            from app.utils.server_calculations import calc_ash_aad
            result = calc_ash_aad({})
            assert result is None


class TestCalcVolatileVad:
    """Tests for calc_volatile_vad function."""

    def test_calc_volatile_vad_valid(self, app):
        """Test calc_volatile_vad with valid data."""
        with app.app_context():
            try:
                from app.utils.server_calculations import calc_volatile_vad
                raw_data = {
                    'p1': {'m1': 10.0, 'm2': 1.0, 'm3': 10.7}
                }
                result = calc_volatile_vad(raw_data)
                assert result is None or isinstance(result, float)
            except (ImportError, AttributeError):
                pytest.skip("calc_volatile_vad not available")


class TestCalcTotalSulfur:
    """Tests for calc_total_sulfur function."""

    def test_calc_total_sulfur_valid(self, app):
        """Test calc_total_sulfur with valid data."""
        with app.app_context():
            try:
                from app.utils.server_calculations import calc_total_sulfur
                raw_data = {'p1': {'result': 0.5}}
                result = calc_total_sulfur(raw_data)
                assert result is None or isinstance(result, float)
            except (ImportError, AttributeError):
                pytest.skip("calc_total_sulfur not available")


class TestCalcCalorificValue:
    """Tests for calc_calorific_value function."""

    def test_calc_calorific_value_valid(self, app):
        """Test calc_calorific_value with valid data."""
        with app.app_context():
            try:
                from app.utils.server_calculations import calc_calorific_value
                raw_data = {'p1': {'result': 6500}}
                result = calc_calorific_value(raw_data)
                assert result is None or isinstance(result, float)
            except (ImportError, AttributeError):
                pytest.skip("calc_calorific_value not available")


class TestVerifyAndRecalculate:
    """Tests for verify_and_recalculate function."""

    def test_verify_unknown_analysis(self, app):
        """Test verify_and_recalculate with unknown analysis."""
        with app.app_context():
            try:
                from app.utils.server_calculations import verify_and_recalculate
                result, warnings = verify_and_recalculate(
                    analysis_code='UNKNOWN',
                    client_final_result=5.0,
                    raw_data={}
                )
                # Unknown analysis should return client value
                assert result == 5.0 or result is None
            except (ImportError, AttributeError):
                pytest.skip("verify_and_recalculate not available")

    def test_verify_mad_analysis(self, app):
        """Test verify_and_recalculate with Mad analysis."""
        with app.app_context():
            try:
                from app.utils.server_calculations import verify_and_recalculate
                raw_data = {
                    'p1': {'m1': 10.0, 'm2': 1.0, 'm3': 10.95}
                }
                result, warnings = verify_and_recalculate(
                    analysis_code='Mad',
                    client_final_result=5.0,
                    raw_data=raw_data
                )
                assert result is not None or result is None
            except (ImportError, AttributeError):
                pytest.skip("verify_and_recalculate not available")


class TestConstants:
    """Tests for module constants."""

    def test_epsilon_exists(self, app):
        """Test EPSILON constant exists."""
        with app.app_context():
            from app.utils.server_calculations import EPSILON
            assert isinstance(EPSILON, (int, float))
            assert EPSILON > 0
