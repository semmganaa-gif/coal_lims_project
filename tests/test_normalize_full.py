# tests/test_normalize_full.py
# -*- coding: utf-8 -*-
"""Complete tests for app/utils/normalize.py"""

import pytest
import json


class TestPick:

    def test_pick_found(self, app):
        with app.app_context():
            from app.utils.normalize import _pick
            d = {'m1': 10.5, 'm2': 20.0}
            result = _pick(d, ['m1', 'm2'])
            assert result == 10.5

    def test_pick_not_found(self, app):
        with app.app_context():
            from app.utils.normalize import _pick
            d = {'other': 10.5}
            result = _pick(d, ['m1', 'm2'])
            assert result is None

    def test_pick_empty_value(self, app):
        with app.app_context():
            from app.utils.normalize import _pick
            d = {'m1': '', 'm2': 20.0}
            result = _pick(d, ['m1', 'm2'])
            assert result == 20.0

    def test_pick_none_value(self, app):
        with app.app_context():
            from app.utils.normalize import _pick
            d = {'m1': None, 'm2': 20.0}
            result = _pick(d, ['m1', 'm2'])
            assert result == 20.0


class TestNormParallel:

    def test_norm_parallel_basic(self, app):
        with app.app_context():
            from app.utils.normalize import _norm_parallel
            raw = {'m1': 10.0, 'm2': 20.0, 'm3': 8.0, 'result': 5.5}
            result = _norm_parallel(raw)
            assert result['m1'] == 10.0
            assert result['result'] == 5.5

    def test_norm_parallel_with_aliases(self, app):
        with app.app_context():
            from app.utils.normalize import _norm_parallel
            raw = {'box_no': 'A1', 'tare': 5.0, 'm2_sample': 15.0}
            result = _norm_parallel(raw)
            assert result['num'] == 'A1'
            assert result['m1'] == 5.0
            assert result['m2'] == 15.0

    def test_norm_parallel_string_to_float(self, app):
        with app.app_context():
            from app.utils.normalize import _norm_parallel
            raw = {'m1': '10.5', 'm2': '20.0'}
            result = _norm_parallel(raw)
            assert result['m1'] == 10.5
            assert result['m2'] == 20.0

    def test_norm_parallel_non_dict(self, app):
        with app.app_context():
            from app.utils.normalize import _norm_parallel
            result = _norm_parallel('not a dict')
            assert result == {}

    def test_norm_parallel_empty(self, app):
        with app.app_context():
            from app.utils.normalize import _norm_parallel
            result = _norm_parallel({})
            assert result == {}


class TestNormalizeRawData:

    def test_normalize_dict(self, app):
        with app.app_context():
            from app.utils.normalize import normalize_raw_data
            raw = {'m1': 10.0, 'm2': 20.0}
            result = normalize_raw_data(raw)
            assert isinstance(result, dict)

    def test_normalize_json_string(self, app):
        with app.app_context():
            from app.utils.normalize import normalize_raw_data
            raw = json.dumps({'m1': 10.0, 'm2': 20.0})
            result = normalize_raw_data(raw)
            assert isinstance(result, dict)

    def test_normalize_with_p1_p2(self, app):
        with app.app_context():
            from app.utils.normalize import normalize_raw_data
            raw = {
                'p1': {'m1': 10.0, 'm2': 20.0, 'm3': 8.0},
                'p2': {'m1': 10.5, 'm2': 20.5, 'm3': 8.5}
            }
            result = normalize_raw_data(raw)
            assert isinstance(result, dict)

    def test_normalize_with_analysis_code(self, app):
        with app.app_context():
            from app.utils.normalize import normalize_raw_data
            raw = {'m1': 10.0, 'm2': 20.0}
            result = normalize_raw_data(raw, analysis_code='Mad')
            assert isinstance(result, dict)

    def test_normalize_none_input(self, app):
        with app.app_context():
            from app.utils.normalize import normalize_raw_data
            result = normalize_raw_data(None)
            assert isinstance(result, dict)


class TestAliases:

    def test_num_aliases(self, app):
        with app.app_context():
            from app.utils.normalize import NUM_ALIASES
            assert 'num' in NUM_ALIASES
            assert 'box_no' in NUM_ALIASES
            assert 'crucible_no' in NUM_ALIASES

    def test_m1_aliases(self, app):
        with app.app_context():
            from app.utils.normalize import M1_ALIASES
            assert 'm1' in M1_ALIASES
            assert 'tare' in M1_ALIASES

    def test_m2_aliases(self, app):
        with app.app_context():
            from app.utils.normalize import M2_ALIASES
            assert 'm2' in M2_ALIASES

    def test_m3_aliases(self, app):
        with app.app_context():
            from app.utils.normalize import M3_ALIASES
            assert 'm3' in M3_ALIASES
