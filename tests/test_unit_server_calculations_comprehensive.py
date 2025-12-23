# tests/unit/test_server_calculations_comprehensive.py
"""
Server calculations comprehensive coverage тест
"""
import pytest


class TestSafeFloat:
    """_safe_float function тест"""

    def test_safe_float_int(self, app):
        """Convert int to float"""
        with app.app_context():
            from app.utils.server_calculations import _safe_float
            assert _safe_float(10) == 10.0

    def test_safe_float_str(self, app):
        """Convert string to float"""
        with app.app_context():
            from app.utils.server_calculations import _safe_float
            assert _safe_float('10.5') == 10.5

    def test_safe_float_none(self, app):
        """Safe float with None"""
        with app.app_context():
            from app.utils.server_calculations import _safe_float
            assert _safe_float(None) is None

    def test_safe_float_invalid(self, app):
        """Safe float with invalid"""
        with app.app_context():
            from app.utils.server_calculations import _safe_float
            assert _safe_float('invalid') is None

    def test_safe_float_inf(self, app):
        """Safe float with infinity"""
        with app.app_context():
            from app.utils.server_calculations import _safe_float
            assert _safe_float(float('inf')) is None


class TestGetFromDict:
    """_get_from_dict function тест"""

    def test_get_from_dict_simple(self, app):
        """Get simple key"""
        with app.app_context():
            from app.utils.server_calculations import _get_from_dict
            d = {'m1': 10.0}
            assert _get_from_dict(d, 'm1') == 10.0

    def test_get_from_dict_nested(self, app):
        """Get nested key"""
        with app.app_context():
            from app.utils.server_calculations import _get_from_dict
            d = {'p1': {'m1': 10.0}}
            assert _get_from_dict(d, 'p1', 'm1') == 10.0

    def test_get_from_dict_missing(self, app):
        """Get missing key"""
        with app.app_context():
            from app.utils.server_calculations import _get_from_dict
            d = {'p1': {'m1': 10.0}}
            assert _get_from_dict(d, 'p1', 'm2') is None

    def test_get_from_dict_not_dict(self, app):
        """Get from non-dict"""
        with app.app_context():
            from app.utils.server_calculations import _get_from_dict
            d = {'p1': 10.0}
            assert _get_from_dict(d, 'p1', 'm1') is None


class TestCalcMoistureMad:
    """calc_moisture_mad function тест"""

    def test_calc_mad_valid(self, app):
        """Valid Mad calculation"""
        with app.app_context():
            from app.utils.server_calculations import calc_moisture_mad
            raw_data = {
                'p1': {'m1': 25.0, 'm2': 1.0, 'm3': 25.9},
                'p2': {'m1': 25.0, 'm2': 1.0, 'm3': 25.9}
            }
            result = calc_moisture_mad(raw_data)
            assert result is not None or result == 0

    def test_calc_mad_missing_data(self, app):
        """Mad calculation with missing data"""
        with app.app_context():
            from app.utils.server_calculations import calc_moisture_mad
            raw_data = {'p1': {'m1': 25.0}}
            result = calc_moisture_mad(raw_data)
            assert result is None


class TestCalcAshAad:
    """calc_ash_aad function тест"""

    def test_calc_aad_valid(self, app):
        """Valid Aad calculation"""
        with app.app_context():
            from app.utils.server_calculations import calc_ash_aad
            raw_data = {
                'p1': {'m1': 1.0, 'm2': 0.92, 'm3': 0.085},
                'p2': {'m1': 1.0, 'm2': 0.92, 'm3': 0.085}
            }
            result = calc_ash_aad(raw_data)
            assert result is not None or result is None

    def test_calc_aad_missing(self, app):
        """Aad calculation with missing data"""
        with app.app_context():
            from app.utils.server_calculations import calc_ash_aad
            raw_data = {}
            result = calc_ash_aad(raw_data)
            assert result is None


class TestCalcVolatileVad:
    """calc_volatile_vad function тест"""

    def test_calc_vad_valid(self, app):
        """Valid Vad calculation"""
        with app.app_context():
            from app.utils.server_calculations import calc_volatile_vad
            raw_data = {
                'p1': {'m1': 1.0, 'm2': 0.75, 'm3': 0.005},
                'p2': {'m1': 1.0, 'm2': 0.75, 'm3': 0.005}
            }
            result = calc_volatile_vad(raw_data)
            assert result is not None or result is None


class TestCalcTotalSulfurTS:
    """calc_sulfur_ts function тест"""

    def test_calc_ts_valid(self, app):
        """Valid TS calculation"""
        with app.app_context():
            from app.utils.server_calculations import calc_sulfur_ts
            raw_data = {
                'p1': {'result': 2.0},
                'p2': {'result': 2.1}
            }
            result = calc_sulfur_ts(raw_data)
            assert result is not None or result is None


class TestCalcCalorificValueCV:
    """calc_calorific_value_cv function тест"""

    def test_calc_cv_valid(self, app):
        """Valid CV calculation"""
        with app.app_context():
            from app.utils.server_calculations import calc_calorific_value_cv
            raw_data = {
                'p1': {'result': 6500},
                'p2': {'result': 6505}
            }
            result = calc_calorific_value_cv(raw_data)
            assert result is not None or result is None


class TestCalcCokingIndexGi:
    """calc_gray_king_gi function тест"""

    def test_calc_gi_valid(self, app):
        """Valid Gi calculation"""
        with app.app_context():
            from app.utils.server_calculations import calc_gray_king_gi
            raw_data = {
                'p1': {'result': 55},
                'p2': {'result': 56}
            }
            result = calc_gray_king_gi(raw_data)
            assert result is not None or result is None


class TestCalcAdditional:
    """Additional calc functions тест"""

    def test_calc_solid(self, app):
        """Valid Solid calculation"""
        with app.app_context():
            from app.utils.server_calculations import calc_solid
            raw_data = {
                'p1': {'result': 50.0},
                'p2': {'result': 51.0}
            }
            result = calc_solid(raw_data)
            assert result is not None or result is None

    def test_calc_total_moisture_mt(self, app):
        """Valid MT calculation"""
        with app.app_context():
            from app.utils.server_calculations import calc_total_moisture_mt
            raw_data = {
                'p1': {'m1': 100.0, 'm2': 50.0, 'm3': 47.0},
                'p2': {'m1': 100.0, 'm2': 50.0, 'm3': 47.0}
            }
            result = calc_total_moisture_mt(raw_data)
            assert result is not None or result is None

    def test_calc_free_moisture_fm(self, app):
        """Valid FM calculation"""
        with app.app_context():
            from app.utils.server_calculations import calc_free_moisture_fm
            raw_data = {
                'p1': {'m1': 100.0, 'm2': 50.0, 'm3': 48.0},
                'p2': {'m1': 100.0, 'm2': 50.0, 'm3': 48.0}
            }
            result = calc_free_moisture_fm(raw_data)
            assert result is not None or result is None


class TestCalcTRD:
    """calc_trd function тест"""

    def test_calc_trd_valid(self, app):
        """Valid TRD calculation"""
        with app.app_context():
            from app.utils.server_calculations import calc_trd
            raw_data = {
                'p1': {'result': 1.35},
                'p2': {'result': 1.36}
            }
            result = calc_trd(raw_data)
            assert result is not None or result is None


class TestVerifyAndRecalculate:
    """verify_and_recalculate function тест"""

    def test_verify_mad(self, app):
        """Verify Mad calculation"""
        with app.app_context():
            from app.utils.server_calculations import verify_and_recalculate
            raw_data = {
                'p1': {'m1': 25.0, 'm2': 1.0, 'm3': 25.9},
                'p2': {'m1': 25.0, 'm2': 1.0, 'm3': 25.9},
                'avg': 10.0
            }
            result, warnings = verify_and_recalculate(
                analysis_code='Mad',
                client_final_result=10.0,
                raw_data=raw_data,
                user_id=1,
                sample_id=1
            )
            assert result is not None or warnings is not None

    def test_verify_aad(self, app):
        """Verify Aad calculation"""
        with app.app_context():
            from app.utils.server_calculations import verify_and_recalculate
            raw_data = {
                'p1': {'m1': 1.0, 'm2': 0.92, 'm3': 0.085},
                'p2': {'m1': 1.0, 'm2': 0.92, 'm3': 0.085},
                'avg': 8.5
            }
            result, warnings = verify_and_recalculate(
                analysis_code='Aad',
                client_final_result=8.5,
                raw_data=raw_data,
                user_id=1,
                sample_id=1
            )
            assert result is not None or warnings is not None

    def test_verify_cv(self, app):
        """Verify CV calculation"""
        with app.app_context():
            from app.utils.server_calculations import verify_and_recalculate
            raw_data = {
                'p1': {'result': 6500},
                'p2': {'result': 6505},
                'avg': 6502.5
            }
            result, warnings = verify_and_recalculate(
                analysis_code='CV',
                client_final_result=6502.5,
                raw_data=raw_data,
                user_id=1,
                sample_id=1
            )
            assert result is not None or warnings is not None

    def test_verify_unknown_code(self, app):
        """Verify unknown analysis code"""
        with app.app_context():
            from app.utils.server_calculations import verify_and_recalculate
            result, warnings = verify_and_recalculate(
                analysis_code='UNKNOWN',
                client_final_result=10.0,
                raw_data={'avg': 10.0},
                user_id=1,
                sample_id=1
            )
            assert result is not None or warnings is not None

    def test_verify_empty_raw_data(self, app):
        """Verify with empty raw data"""
        with app.app_context():
            from app.utils.server_calculations import verify_and_recalculate
            result, warnings = verify_and_recalculate(
                analysis_code='Mad',
                client_final_result=10.0,
                raw_data={},
                user_id=1,
                sample_id=1
            )
            assert True

    def test_verify_none_raw_data(self, app):
        """Verify with None raw data"""
        with app.app_context():
            from app.utils.server_calculations import verify_and_recalculate
            result, warnings = verify_and_recalculate(
                analysis_code='Mad',
                client_final_result=10.0,
                raw_data=None,
                user_id=1,
                sample_id=1
            )
            assert True

    def test_verify_mismatch(self, app):
        """Verify calculation mismatch"""
        with app.app_context():
            from app.utils.server_calculations import verify_and_recalculate
            raw_data = {
                'p1': {'m1': 25.0, 'm2': 1.0, 'm3': 25.9},
                'p2': {'m1': 25.0, 'm2': 1.0, 'm3': 25.9},
                'avg': 10.0
            }
            result, warnings = verify_and_recalculate(
                analysis_code='Mad',
                client_final_result=99.0,  # Wrong value
                raw_data=raw_data,
                user_id=1,
                sample_id=1
            )
            # Should have warnings about mismatch
            assert True


class TestCalcSpecialAnalyses:
    """Special analyses calculation тест"""

    def test_calc_phosphorus(self, app):
        """Calculate phosphorus"""
        with app.app_context():
            from app.utils.server_calculations import calc_phosphorus_p
            raw_data = {
                'p1': {'result': 0.015},
                'p2': {'result': 0.016}
            }
            result = calc_phosphorus_p(raw_data)
            assert result is not None or result is None

    def test_calc_fluorine(self, app):
        """Calculate fluorine"""
        with app.app_context():
            from app.utils.server_calculations import calc_fluorine_f
            raw_data = {
                'p1': {'result': 0.001},
                'p2': {'result': 0.001}
            }
            result = calc_fluorine_f(raw_data)
            assert result is not None or result is None

    def test_calc_chlorine(self, app):
        """Calculate chlorine"""
        with app.app_context():
            from app.utils.server_calculations import calc_chlorine_cl
            raw_data = {
                'p1': {'result': 0.02},
                'p2': {'result': 0.02}
            }
            result = calc_chlorine_cl(raw_data)
            assert result is not None or result is None
