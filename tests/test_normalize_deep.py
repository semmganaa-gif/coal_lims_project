# tests/test_normalize_deep.py
# -*- coding: utf-8 -*-
"""
Deep coverage tests for app/utils/normalize.py
"""

import pytest
import json


class TestPick:
    """Tests for _pick helper function."""

    def test_pick_first_key(self, app):
        """Test _pick returns first matching key."""
        with app.app_context():
            from app.utils.normalize import _pick
            d = {'key1': 'value1', 'key2': 'value2'}
            result = _pick(d, ['key1', 'key2'])
            assert result == 'value1'

    def test_pick_second_key(self, app):
        """Test _pick returns second key when first is None."""
        with app.app_context():
            from app.utils.normalize import _pick
            d = {'key1': None, 'key2': 'value2'}
            result = _pick(d, ['key1', 'key2'])
            assert result == 'value2'

    def test_pick_no_match(self, app):
        """Test _pick returns None when no match."""
        with app.app_context():
            from app.utils.normalize import _pick
            d = {'other': 'value'}
            result = _pick(d, ['key1', 'key2'])
            assert result is None

    def test_pick_empty_dict(self, app):
        """Test _pick with empty dict."""
        with app.app_context():
            from app.utils.normalize import _pick
            result = _pick({}, ['key1'])
            assert result is None

    def test_pick_empty_string_skipped(self, app):
        """Test _pick skips empty string values."""
        with app.app_context():
            from app.utils.normalize import _pick
            d = {'key1': '', 'key2': 'value2'}
            result = _pick(d, ['key1', 'key2'])
            assert result == 'value2'


class TestNormParallel:
    """Tests for _norm_parallel function."""

    def test_norm_parallel_basic(self, app):
        """Test _norm_parallel with basic data."""
        with app.app_context():
            from app.utils.normalize import _norm_parallel
            data = {'m1': 10.0, 'm2': 1.0, 'm3': 10.5}
            result = _norm_parallel(data)
            assert result['m1'] == 10.0
            assert result['m2'] == 1.0
            assert result['m3'] == 10.5

    def test_norm_parallel_with_aliases(self, app):
        """Test _norm_parallel with alias names."""
        with app.app_context():
            from app.utils.normalize import _norm_parallel
            data = {'box_no': '123', 'tare': 10.0, 'm2_sample': 1.0}
            result = _norm_parallel(data)
            assert result['num'] == '123'
            assert result['m1'] == 10.0
            assert result['m2'] == 1.0

    def test_norm_parallel_non_dict(self, app):
        """Test _norm_parallel with non-dict input."""
        with app.app_context():
            from app.utils.normalize import _norm_parallel
            result = _norm_parallel("not a dict")
            assert result == {}

    def test_norm_parallel_string_numbers(self, app):
        """Test _norm_parallel converts string to float."""
        with app.app_context():
            from app.utils.normalize import _norm_parallel
            data = {'m1': '10.5', 'm2': '1.0'}
            result = _norm_parallel(data)
            assert result['m1'] == 10.5
            assert result['m2'] == 1.0

    def test_norm_parallel_with_result(self, app):
        """Test _norm_parallel with result alias."""
        with app.app_context():
            from app.utils.normalize import _norm_parallel
            data = {'result': 5.5}
            result = _norm_parallel(data)
            assert result['result'] == 5.5

    def test_norm_parallel_weight_copied(self, app):
        """Test _norm_parallel copies m1 to weight."""
        with app.app_context():
            from app.utils.normalize import _norm_parallel
            data = {'m1': 10.0}
            result = _norm_parallel(data)
            assert result.get('weight') == 10.0


class TestNormalizeRawData:
    """Tests for normalize_raw_data function."""

    def test_normalize_dict_input(self, app):
        """Test normalize_raw_data with dict input."""
        with app.app_context():
            from app.utils.normalize import normalize_raw_data
            data = {'p1': {'m1': 10.0, 'm2': 1.0, 'm3': 10.5}}
            result = normalize_raw_data(data)
            assert 'p1' in result

    def test_normalize_json_string(self, app):
        """Test normalize_raw_data with JSON string."""
        with app.app_context():
            from app.utils.normalize import normalize_raw_data
            data = json.dumps({'p1': {'m1': 10.0}})
            result = normalize_raw_data(data)
            assert isinstance(result, dict)

    def test_normalize_empty_dict(self, app):
        """Test normalize_raw_data with empty dict."""
        with app.app_context():
            from app.utils.normalize import normalize_raw_data
            result = normalize_raw_data({})
            assert isinstance(result, dict)

    def test_normalize_none_input(self, app):
        """Test normalize_raw_data with None."""
        with app.app_context():
            from app.utils.normalize import normalize_raw_data
            result = normalize_raw_data(None)
            assert isinstance(result, dict)

    def test_normalize_with_analysis_code(self, app):
        """Test normalize_raw_data with analysis code."""
        with app.app_context():
            from app.utils.normalize import normalize_raw_data
            data = {'p1': {'m1': 10.0}}
            result = normalize_raw_data(data, analysis_code='Mad')
            assert isinstance(result, dict)


class TestAliasConstants:
    """Tests for alias constants."""

    def test_num_aliases_exist(self, app):
        """Test NUM_ALIASES constant exists."""
        with app.app_context():
            from app.utils.normalize import NUM_ALIASES
            assert isinstance(NUM_ALIASES, list)
            assert 'num' in NUM_ALIASES
            assert 'box_no' in NUM_ALIASES

    def test_m1_aliases_exist(self, app):
        """Test M1_ALIASES constant exists."""
        with app.app_context():
            from app.utils.normalize import M1_ALIASES
            assert isinstance(M1_ALIASES, list)
            assert 'm1' in M1_ALIASES
            assert 'tare' in M1_ALIASES

    def test_m2_aliases_exist(self, app):
        """Test M2_ALIASES constant exists."""
        with app.app_context():
            from app.utils.normalize import M2_ALIASES
            assert isinstance(M2_ALIASES, list)
            assert 'm2' in M2_ALIASES

    def test_m3_aliases_exist(self, app):
        """Test M3_ALIASES constant exists."""
        with app.app_context():
            from app.utils.normalize import M3_ALIASES
            assert isinstance(M3_ALIASES, list)
            assert 'm3' in M3_ALIASES

    def test_result_aliases_exist(self, app):
        """Test RESULT_ALIASES constant exists."""
        with app.app_context():
            from app.utils.normalize import RESULT_ALIASES
            assert isinstance(RESULT_ALIASES, list)
            assert 'result' in RESULT_ALIASES

    def test_common_value_aliases_exist(self, app):
        """Test COMMON_VALUE_ALIASES constant exists."""
        with app.app_context():
            from app.utils.normalize import COMMON_VALUE_ALIASES
            assert isinstance(COMMON_VALUE_ALIASES, dict)
            assert 'A' in COMMON_VALUE_ALIASES
            assert 'B' in COMMON_VALUE_ALIASES
            assert 'C' in COMMON_VALUE_ALIASES
