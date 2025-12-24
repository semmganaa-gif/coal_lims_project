# tests/test_normalize_full.py
# -*- coding: utf-8 -*-
"""
Complete tests for app/utils/normalize.py
"""

import pytest
import json


class TestPick:
    """Tests for _pick helper function."""

    def test_picks_first_match(self, app):
        """Test picks first matching key."""
        with app.app_context():
            from app.utils.normalize import _pick
            d = {'a': 1, 'b': 2, 'c': 3}
            result = _pick(d, ['x', 'b', 'c'])
            assert result == 2

    def test_returns_none_when_no_match(self, app):
        """Test returns None when no key matches."""
        with app.app_context():
            from app.utils.normalize import _pick
            d = {'a': 1, 'b': 2}
            result = _pick(d, ['x', 'y', 'z'])
            assert result is None

    def test_skips_none_values(self, app):
        """Test skips None values."""
        with app.app_context():
            from app.utils.normalize import _pick
            d = {'a': None, 'b': 2}
            result = _pick(d, ['a', 'b'])
            assert result == 2

    def test_skips_empty_string(self, app):
        """Test skips empty string values."""
        with app.app_context():
            from app.utils.normalize import _pick
            d = {'a': '', 'b': 2}
            result = _pick(d, ['a', 'b'])
            assert result == 2

    def test_empty_dict(self, app):
        """Test with empty dict."""
        with app.app_context():
            from app.utils.normalize import _pick
            result = _pick({}, ['a', 'b'])
            assert result is None


class TestPickNumeric:
    """Tests for _pick_numeric helper function."""

    def test_converts_string_to_float(self, app):
        """Test converts string numeric to float."""
        with app.app_context():
            from app.utils.normalize import _pick_numeric
            d = {'a': '123.45'}
            result = _pick_numeric(d, ['a'])
            assert result == 123.45

    def test_returns_float_as_is(self, app):
        """Test returns float value as is."""
        with app.app_context():
            from app.utils.normalize import _pick_numeric
            d = {'a': 123.45}
            result = _pick_numeric(d, ['a'])
            assert result == 123.45

    def test_non_numeric_string_returned_as_is(self, app):
        """Test non-numeric string returned as is."""
        with app.app_context():
            from app.utils.normalize import _pick_numeric
            d = {'a': 'not_a_number'}
            result = _pick_numeric(d, ['a'])
            assert result == 'not_a_number'

    def test_returns_none_when_not_found(self, app):
        """Test returns None when key not found."""
        with app.app_context():
            from app.utils.normalize import _pick_numeric
            d = {'a': 1}
            result = _pick_numeric(d, ['b'])
            assert result is None


class TestNormParallel:
    """Tests for _norm_parallel helper function."""

    def test_non_dict_returns_empty(self, app):
        """Test non-dict input returns empty dict."""
        with app.app_context():
            from app.utils.normalize import _norm_parallel
            result = _norm_parallel("not a dict")
            assert result == {}

    def test_none_returns_empty(self, app):
        """Test None input returns empty dict."""
        with app.app_context():
            from app.utils.normalize import _norm_parallel
            result = _norm_parallel(None)
            assert result == {}

    def test_extracts_num_field(self, app):
        """Test extracts num field from aliases."""
        with app.app_context():
            from app.utils.normalize import _norm_parallel
            raw = {'box_no': 'B001'}
            result = _norm_parallel(raw)
            assert result.get('num') == 'B001'

    def test_extracts_m1_field(self, app):
        """Test extracts m1 field from aliases."""
        with app.app_context():
            from app.utils.normalize import _norm_parallel
            raw = {'m1_empty': 10.5}
            result = _norm_parallel(raw)
            assert result.get('m1') == 10.5

    def test_extracts_m2_field(self, app):
        """Test extracts m2 field from aliases."""
        with app.app_context():
            from app.utils.normalize import _norm_parallel
            raw = {'m2_sample': 25.3}
            result = _norm_parallel(raw)
            assert result.get('m2') == 25.3

    def test_extracts_m3_field(self, app):
        """Test extracts m3 field from aliases."""
        with app.app_context():
            from app.utils.normalize import _norm_parallel
            raw = {'m3_dried_box': 22.1}
            result = _norm_parallel(raw)
            assert result.get('m3') == 22.1

    def test_extracts_result_field(self, app):
        """Test extracts result field from aliases."""
        with app.app_context():
            from app.utils.normalize import _norm_parallel
            raw = {'value': 5.67}
            result = _norm_parallel(raw)
            assert result.get('result') == 5.67

    def test_converts_string_to_float(self, app):
        """Test converts string values to float."""
        with app.app_context():
            from app.utils.normalize import _norm_parallel
            raw = {'m1': '10.5', 'm2': '25.3'}
            result = _norm_parallel(raw)
            assert result.get('m1') == 10.5
            assert result.get('m2') == 25.3

    def test_adds_weight_alias(self, app):
        """Test adds weight alias for m1."""
        with app.app_context():
            from app.utils.normalize import _norm_parallel
            raw = {'m1': 10.5}
            result = _norm_parallel(raw)
            assert result.get('weight') == 10.5

    def test_empty_values_removed(self, app):
        """Test empty values are removed from result."""
        with app.app_context():
            from app.utils.normalize import _norm_parallel
            raw = {'m1': 10.5, 'm2': None, 'm3': ''}
            result = _norm_parallel(raw)
            assert 'm2' not in result
            assert 'm3' not in result


class TestNormalizeRawData:
    """Tests for normalize_raw_data function."""

    def test_empty_dict(self, app):
        """Test with empty dict."""
        with app.app_context():
            from app.utils.normalize import normalize_raw_data
            result = normalize_raw_data({})
            assert 'p1' in result
            assert 'p2' in result
            assert '_schema' in result

    def test_json_string_input(self, app):
        """Test with JSON string input."""
        with app.app_context():
            from app.utils.normalize import normalize_raw_data
            raw_str = json.dumps({'p1': {'m1': 10.5}})
            result = normalize_raw_data(raw_str)
            assert result['p1'].get('m1') == 10.5

    def test_dict_input(self, app):
        """Test with dict input."""
        with app.app_context():
            from app.utils.normalize import normalize_raw_data
            raw = {'p1': {'m1': 10.5}}
            result = normalize_raw_data(raw)
            assert result['p1'].get('m1') == 10.5

    def test_p1_p2_normalization(self, app):
        """Test p1 and p2 are normalized."""
        with app.app_context():
            from app.utils.normalize import normalize_raw_data
            raw = {
                'p1': {'m1': 10.5, 'm2': 25.3},
                'p2': {'m1': 10.6, 'm2': 25.4}
            }
            result = normalize_raw_data(raw)
            assert result['p1']['m1'] == 10.5
            assert result['p2']['m1'] == 10.6

    def test_parallels_array_created(self, app):
        """Test parallels array is created."""
        with app.app_context():
            from app.utils.normalize import normalize_raw_data
            raw = {
                'p1': {'m1': 10.5},
                'p2': {'m1': 10.6}
            }
            result = normalize_raw_data(raw)
            assert 'parallels' in result
            assert len(result['parallels']) == 2

    def test_csn_special_handling(self, app):
        """Test CSN analysis has special handling."""
        with app.app_context():
            from app.utils.normalize import normalize_raw_data
            raw = {'v1': 3, 'v2': 3, 'v3': 3.5, 'v4': 3.5, 'v5': 4}
            result = normalize_raw_data(raw, analysis_code='CSN')
            assert '_schema' in result
            assert 'parallels' in result

    def test_diff_preserved(self, app):
        """Test diff value is preserved."""
        with app.app_context():
            from app.utils.normalize import normalize_raw_data
            raw = {'p1': {'m1': 10.5}, 'diff': 0.05}
            result = normalize_raw_data(raw)
            assert result.get('diff') == 0.05

    def test_avg_preserved(self, app):
        """Test avg value is preserved."""
        with app.app_context():
            from app.utils.normalize import normalize_raw_data
            raw = {'p1': {'m1': 10.5}, 'avg': 10.55}
            result = normalize_raw_data(raw)
            assert result.get('avg') == 10.55

    def test_common_value_aliases(self, app):
        """Test common value aliases (A, B, C) are preserved."""
        with app.app_context():
            from app.utils.normalize import normalize_raw_data
            raw = {'A': 100.0, 'B': 50.0, 'C': 25.0}
            result = normalize_raw_data(raw)
            assert result.get('A') == 100.0
            assert result.get('B') == 50.0
            assert result.get('C') == 25.0

    def test_fm_fields_preserved(self, app):
        """Test FM analysis fields are preserved."""
        with app.app_context():
            from app.utils.normalize import normalize_raw_data
            raw = {
                'tray_g': 100.0,
                'before_g': 150.0,
                'after_g': 145.0,
                'loss_g': 5.0
            }
            result = normalize_raw_data(raw)
            assert result.get('tray_g') == 100.0
            assert result.get('before_g') == 150.0

    def test_cv_fields_preserved(self, app):
        """Test CV analysis fields are preserved."""
        with app.app_context():
            from app.utils.normalize import normalize_raw_data
            raw = {
                'p1': {'m': 0.5, 'delta_t': 2.5},
                'p2': {'m': 0.51, 'delta_t': 2.48}
            }
            result = normalize_raw_data(raw)
            assert result['p1'].get('m') == 0.5
            assert result['p1'].get('delta_t') == 2.5

    def test_trd_fields_preserved(self, app):
        """Test TRD analysis fields are preserved."""
        with app.app_context():
            from app.utils.normalize import normalize_raw_data
            raw = {
                'mad_used': 5.0,
                'temp_c': 23.0,
                'kt_used': 0.999
            }
            result = normalize_raw_data(raw)
            assert result.get('mad_used') == 5.0
            assert result.get('temp_c') == 23.0
            assert result.get('kt_used') == 0.999

    def test_schema_info(self, app):
        """Test _schema info is correct."""
        with app.app_context():
            from app.utils.normalize import normalize_raw_data
            raw = {'p1': {'m1': 10.5}, 'p2': {'m1': 10.6}}
            result = normalize_raw_data(raw)
            schema = result['_schema']
            assert schema['version'] == 1
            assert schema['parallels_count'] == 2
            assert schema['has_parallels'] is True

    def test_invalid_json_string(self, app):
        """Test invalid JSON string returns empty result."""
        with app.app_context():
            from app.utils.normalize import normalize_raw_data
            result = normalize_raw_data("not valid json {{{")
            assert '_schema' in result
            assert result['p1'] == {}

    def test_none_p1_p2_handled(self, app):
        """Test None p1/p2 values are handled."""
        with app.app_context():
            from app.utils.normalize import normalize_raw_data
            raw = {'p1': None, 'p2': None}
            result = normalize_raw_data(raw)
            assert result['p1'] == {}
            assert result['p2'] == {}


class TestAliasConstants:
    """Tests for alias constant arrays."""

    def test_num_aliases_list(self, app):
        """Test NUM_ALIASES is a list."""
        with app.app_context():
            from app.utils.normalize import NUM_ALIASES
            assert isinstance(NUM_ALIASES, list)
            assert len(NUM_ALIASES) > 0
            assert 'num' in NUM_ALIASES
            assert 'box_no' in NUM_ALIASES

    def test_m1_aliases_list(self, app):
        """Test M1_ALIASES is a list."""
        with app.app_context():
            from app.utils.normalize import M1_ALIASES
            assert isinstance(M1_ALIASES, list)
            assert 'm1' in M1_ALIASES

    def test_m2_aliases_list(self, app):
        """Test M2_ALIASES is a list."""
        with app.app_context():
            from app.utils.normalize import M2_ALIASES
            assert isinstance(M2_ALIASES, list)
            assert 'm2' in M2_ALIASES

    def test_m3_aliases_list(self, app):
        """Test M3_ALIASES is a list."""
        with app.app_context():
            from app.utils.normalize import M3_ALIASES
            assert isinstance(M3_ALIASES, list)
            assert 'm3' in M3_ALIASES

    def test_result_aliases_list(self, app):
        """Test RESULT_ALIASES is a list."""
        with app.app_context():
            from app.utils.normalize import RESULT_ALIASES
            assert isinstance(RESULT_ALIASES, list)
            assert 'result' in RESULT_ALIASES

    def test_common_value_aliases_dict(self, app):
        """Test COMMON_VALUE_ALIASES is a dict."""
        with app.app_context():
            from app.utils.normalize import COMMON_VALUE_ALIASES
            assert isinstance(COMMON_VALUE_ALIASES, dict)
            assert 'A' in COMMON_VALUE_ALIASES
            assert 'B' in COMMON_VALUE_ALIASES
            assert 'C' in COMMON_VALUE_ALIASES
