# tests/unit/test_normalize_coverage.py
"""
Normalize module comprehensive coverage тест
"""
import pytest


class TestNormalizePick:
    """_pick function тест"""

    def test_pick_first_key(self, app):
        """Pick first matching key"""
        with app.app_context():
            from app.utils.normalize import _pick
            d = {'m1': 10.0, 'm2': 20.0}
            result = _pick(d, ['m1', 'm2'])
            assert result == 10.0

    def test_pick_second_key(self, app):
        """Pick second key when first is None"""
        with app.app_context():
            from app.utils.normalize import _pick
            d = {'m1': None, 'm2': 20.0}
            result = _pick(d, ['m1', 'm2'])
            assert result == 20.0

    def test_pick_empty_string(self, app):
        """Pick skips empty string"""
        with app.app_context():
            from app.utils.normalize import _pick
            d = {'m1': '', 'm2': 20.0}
            result = _pick(d, ['m1', 'm2'])
            assert result == 20.0

    def test_pick_no_match(self, app):
        """Pick returns None when no match"""
        with app.app_context():
            from app.utils.normalize import _pick
            d = {'x': 10.0}
            result = _pick(d, ['m1', 'm2'])
            assert result is None


class TestNormParallel:
    """_norm_parallel function тест"""

    def test_norm_parallel_basic(self, app):
        """Basic norm parallel"""
        with app.app_context():
            from app.utils.normalize import _norm_parallel
            raw = {'num': '1', 'm1': 10.0, 'm2': 20.0, 'm3': 30.0, 'result': 5.0}
            result = _norm_parallel(raw)
            assert result['m1'] == 10.0
            assert result['result'] == 5.0

    def test_norm_parallel_aliases(self, app):
        """Norm parallel with aliases"""
        with app.app_context():
            from app.utils.normalize import _norm_parallel
            raw = {'box_no': '1', 'm1_empty': 10.0, 'm2_sample': 20.0, 'm3_dry': 30.0}
            result = _norm_parallel(raw)
            assert result['num'] == '1'
            assert result['m1'] == 10.0

    def test_norm_parallel_string_values(self, app):
        """Norm parallel with string values"""
        with app.app_context():
            from app.utils.normalize import _norm_parallel
            raw = {'m1': '10.5', 'm2': '20.5'}
            result = _norm_parallel(raw)
            assert result['m1'] == 10.5

    def test_norm_parallel_invalid_string(self, app):
        """Norm parallel with invalid string"""
        with app.app_context():
            from app.utils.normalize import _norm_parallel
            raw = {'m1': 'invalid', 'm2': 20.0}
            result = _norm_parallel(raw)
            assert result['m1'] == 'invalid'

    def test_norm_parallel_empty(self, app):
        """Norm parallel with empty dict"""
        with app.app_context():
            from app.utils.normalize import _norm_parallel
            result = _norm_parallel({})
            assert isinstance(result, dict)

    def test_norm_parallel_none(self, app):
        """Norm parallel with None"""
        with app.app_context():
            from app.utils.normalize import _norm_parallel
            result = _norm_parallel(None)
            assert result == {}


class TestNormalizeRawData:
    """normalize_raw_data function тест"""

    def test_normalize_mad_full(self, app):
        """Normalize Mad with full data"""
        with app.app_context():
            from app.utils.normalize import normalize_raw_data
            raw = {
                'p1': {'num': '1', 'm1': 10.0, 'm2': 11.0, 'm3': 10.5, 'result': 4.5},
                'p2': {'num': '2', 'm1': 10.0, 'm2': 11.0, 'm3': 10.5, 'result': 4.6},
                'avg': 4.55,
                'diff': 0.1
            }
            result = normalize_raw_data(raw, 'Mad')
            assert 'p1' in result or 'avg' in result

    def test_normalize_aad_full(self, app):
        """Normalize Aad with full data"""
        with app.app_context():
            from app.utils.normalize import normalize_raw_data
            raw = {
                'p1': {'num': '1', 'm1': 1.0, 'm2': 0.92, 'm3': 0.005, 'result': 8.5},
                'p2': {'num': '2', 'm1': 1.0, 'm2': 0.92, 'm3': 0.005, 'result': 8.6},
                'avg': 8.55
            }
            result = normalize_raw_data(raw, 'Aad')
            assert isinstance(result, dict)

    def test_normalize_cv_full(self, app):
        """Normalize CV with full data"""
        with app.app_context():
            from app.utils.normalize import normalize_raw_data
            raw = {
                'gross_cv': 6500,
                'net_cv': 6200,
                'r1': 6495,
                'r2': 6505
            }
            result = normalize_raw_data(raw, 'CV')
            assert isinstance(result, dict)

    def test_normalize_ts_full(self, app):
        """Normalize TS with full data"""
        with app.app_context():
            from app.utils.normalize import normalize_raw_data
            raw = {
                'm_crucible': 10.0,
                'm_sample_crucible': 11.0,
                'm_after': 10.2,
                'result': 2.0
            }
            result = normalize_raw_data(raw, 'TS')
            assert isinstance(result, dict)

    def test_normalize_gi_full(self, app):
        """Normalize Gi with full data"""
        with app.app_context():
            from app.utils.normalize import normalize_raw_data
            raw = {
                'gi_value': 55,
                'gi_index': 55
            }
            result = normalize_raw_data(raw, 'Gi')
            assert isinstance(result, dict)

    def test_normalize_trd_full(self, app):
        """Normalize TRD with full data"""
        with app.app_context():
            from app.utils.normalize import normalize_raw_data
            raw = {
                'bottle_num': '1',
                'm': 1.0,
                'result': 1.35
            }
            result = normalize_raw_data(raw, 'TRD')
            assert isinstance(result, dict)

    def test_normalize_unknown_code(self, app):
        """Normalize unknown code"""
        with app.app_context():
            from app.utils.normalize import normalize_raw_data
            raw = {'value': 10.0}
            result = normalize_raw_data(raw, 'UNKNOWN')
            assert isinstance(result, dict)

    def test_normalize_json_string(self, app):
        """Normalize JSON string input"""
        with app.app_context():
            import json
            from app.utils.normalize import normalize_raw_data
            raw = json.dumps({'m1': 10.0, 'm2': 20.0})
            result = normalize_raw_data(raw, 'Mad')
            assert isinstance(result, dict)

    def test_normalize_list_of_dicts(self, app):
        """Normalize list of dicts"""
        with app.app_context():
            from app.utils.normalize import normalize_raw_data
            raw = [
                {'num': '1', 'm1': 10.0, 'm2': 11.0, 'm3': 10.5, 'result': 4.5},
                {'num': '2', 'm1': 10.0, 'm2': 11.0, 'm3': 10.5, 'result': 4.6}
            ]
            result = normalize_raw_data(raw, 'Mad')
            assert isinstance(result, dict)


class TestNormalizeSpecialCases:
    """Special case тестүүд"""

    def test_normalize_with_common_aliases(self, app):
        """Normalize with A, B, C aliases"""
        with app.app_context():
            from app.utils.normalize import normalize_raw_data
            raw = {
                'A': 100.0,
                'B': 50.0,
                'C': 45.0
            }
            result = normalize_raw_data(raw, 'Solid')
            assert isinstance(result, dict)

    def test_normalize_cv_arb_adb(self, app):
        """Normalize CV with ARB/ADB"""
        with app.app_context():
            from app.utils.normalize import normalize_raw_data
            raw = {
                'cv_arb': 6000,
                'cv_adb': 6500
            }
            result = normalize_raw_data(raw, 'CV')
            assert isinstance(result, dict)

    def test_normalize_p_with_percentages(self, app):
        """Normalize P (Phosphorus) data"""
        with app.app_context():
            from app.utils.normalize import normalize_raw_data
            raw = {
                'weight': 0.5,
                'result': 0.015
            }
            result = normalize_raw_data(raw, 'P')
            assert isinstance(result, dict)

    def test_normalize_cl_with_percentages(self, app):
        """Normalize Cl (Chlorine) data"""
        with app.app_context():
            from app.utils.normalize import normalize_raw_data
            raw = {
                'weight': 0.5,
                'result': 0.02
            }
            result = normalize_raw_data(raw, 'Cl')
            assert isinstance(result, dict)

    def test_normalize_f_with_percentages(self, app):
        """Normalize F (Fluorine) data"""
        with app.app_context():
            from app.utils.normalize import normalize_raw_data
            raw = {
                'weight': 0.5,
                'result': 0.001
            }
            result = normalize_raw_data(raw, 'F')
            assert isinstance(result, dict)
