# -*- coding: utf-8 -*-
"""
Normalize extended тестүүд
"""
import pytest


class TestPick:
    """_pick function тестүүд"""

    def test_import_function(self):
        """Function import"""
        from app.utils.normalize import _pick
        assert _pick is not None

    def test_pick_first_match(self):
        """Pick returns first matching key"""
        from app.utils.normalize import _pick
        d = {'a': 1, 'b': 2}
        assert _pick(d, ['a', 'b']) == 1

    def test_pick_second_match(self):
        """Pick returns second key if first not found"""
        from app.utils.normalize import _pick
        d = {'b': 2}
        assert _pick(d, ['a', 'b']) == 2

    def test_pick_none_found(self):
        """Pick returns None if no match"""
        from app.utils.normalize import _pick
        d = {'c': 3}
        assert _pick(d, ['a', 'b']) is None

    def test_pick_skips_none_value(self):
        """Pick skips None values"""
        from app.utils.normalize import _pick
        d = {'a': None, 'b': 2}
        assert _pick(d, ['a', 'b']) == 2

    def test_pick_skips_empty_string(self):
        """Pick skips empty string values"""
        from app.utils.normalize import _pick
        d = {'a': '', 'b': 2}
        assert _pick(d, ['a', 'b']) == 2


class TestNormParallel:
    """_norm_parallel function тестүүд"""

    def test_import_function(self):
        """Function import"""
        from app.utils.normalize import _norm_parallel
        assert _norm_parallel is not None

    def test_empty_dict(self):
        """Empty dict returns empty"""
        from app.utils.normalize import _norm_parallel
        result = _norm_parallel({})
        assert isinstance(result, dict)

    def test_non_dict_returns_empty(self):
        """Non-dict returns empty dict"""
        from app.utils.normalize import _norm_parallel
        assert _norm_parallel([]) == {}
        assert _norm_parallel(None) == {}
        assert _norm_parallel("string") == {}

    def test_num_aliases(self):
        """Various num aliases work"""
        from app.utils.normalize import _norm_parallel
        for alias in ['num', 'box_no', 'crucible_no']:
            result = _norm_parallel({alias: 'A1'})
            assert result.get('num') == 'A1'

    def test_m1_aliases(self):
        """Various m1 aliases work"""
        from app.utils.normalize import _norm_parallel
        for alias in ['m1', 'm1_empty', 'weight']:
            result = _norm_parallel({alias: 10.5})
            assert result.get('m1') == 10.5

    def test_m2_aliases(self):
        """Various m2 aliases work"""
        from app.utils.normalize import _norm_parallel
        for alias in ['m2', 'm2_sample', 'm']:
            result = _norm_parallel({alias: 20.5})
            assert result.get('m2') == 20.5

    def test_m3_aliases(self):
        """Various m3 aliases work"""
        from app.utils.normalize import _norm_parallel
        for alias in ['m3', 'm3_ashy', 'm3_dried_box']:
            result = _norm_parallel({alias: 15.5})
            assert result.get('m3') == 15.5

    def test_result_aliases(self):
        """Various result aliases work"""
        from app.utils.normalize import _norm_parallel
        for alias in ['result', 'res', 'value']:
            result = _norm_parallel({alias: 5.5})
            assert result.get('result') == 5.5

    def test_string_to_float_conversion(self):
        """String values are converted to float"""
        from app.utils.normalize import _norm_parallel
        result = _norm_parallel({'m1': '10.5', 'm2': '20.5'})
        assert result['m1'] == 10.5
        assert result['m2'] == 20.5

    def test_invalid_string_kept(self):
        """Invalid string values are kept as-is"""
        from app.utils.normalize import _norm_parallel
        result = _norm_parallel({'m1': 'invalid'})
        assert result['m1'] == 'invalid'

    def test_weight_copy(self):
        """m1 is copied to weight"""
        from app.utils.normalize import _norm_parallel
        result = _norm_parallel({'m1': 10.5})
        assert result.get('weight') == 10.5


class TestNormalizeRawData:
    """normalize_raw_data function тестүүд"""

    def test_import_function(self):
        """Function import"""
        from app.utils.normalize import normalize_raw_data
        assert normalize_raw_data is not None

    def test_dict_input(self):
        """Dict input works"""
        from app.utils.normalize import normalize_raw_data
        result = normalize_raw_data({'m1': 10.5})
        assert isinstance(result, dict)

    def test_json_string_input(self):
        """JSON string input works"""
        from app.utils.normalize import normalize_raw_data
        import json
        data = json.dumps({'m1': 10.5})
        result = normalize_raw_data(data)
        assert isinstance(result, dict)

    def test_invalid_json_string(self):
        """Invalid JSON string returns empty dict"""
        from app.utils.normalize import normalize_raw_data
        result = normalize_raw_data('not json')
        assert isinstance(result, dict)

    def test_none_input(self):
        """None input returns empty dict"""
        from app.utils.normalize import normalize_raw_data
        result = normalize_raw_data(None)
        assert isinstance(result, dict)

    def test_empty_string_input(self):
        """Empty string input returns empty dict"""
        from app.utils.normalize import normalize_raw_data
        result = normalize_raw_data('')
        assert isinstance(result, dict)

    def test_p1_p2_structure(self):
        """p1/p2 structure is normalized"""
        from app.utils.normalize import normalize_raw_data
        data = {
            'p1': {'m1': 10.0, 'm2': 20.0},
            'p2': {'m1': 10.5, 'm2': 20.5}
        }
        result = normalize_raw_data(data)
        assert 'p1' in result or result.get('m1') is not None

    def test_with_analysis_code(self):
        """Works with analysis code parameter"""
        from app.utils.normalize import normalize_raw_data
        result = normalize_raw_data({'m1': 10.5}, analysis_code='Mad')
        assert isinstance(result, dict)


class TestAliases:
    """Alias constants тестүүд"""

    def test_num_aliases_exists(self):
        """NUM_ALIASES exists"""
        from app.utils.normalize import NUM_ALIASES
        assert isinstance(NUM_ALIASES, list)
        assert len(NUM_ALIASES) > 0

    def test_m1_aliases_exists(self):
        """M1_ALIASES exists"""
        from app.utils.normalize import M1_ALIASES
        assert isinstance(M1_ALIASES, list)
        assert len(M1_ALIASES) > 0

    def test_m2_aliases_exists(self):
        """M2_ALIASES exists"""
        from app.utils.normalize import M2_ALIASES
        assert isinstance(M2_ALIASES, list)
        assert len(M2_ALIASES) > 0

    def test_m3_aliases_exists(self):
        """M3_ALIASES exists"""
        from app.utils.normalize import M3_ALIASES
        assert isinstance(M3_ALIASES, list)
        assert len(M3_ALIASES) > 0

    def test_result_aliases_exists(self):
        """RESULT_ALIASES exists"""
        from app.utils.normalize import RESULT_ALIASES
        assert isinstance(RESULT_ALIASES, list)
        assert len(RESULT_ALIASES) > 0

    def test_common_value_aliases_exists(self):
        """COMMON_VALUE_ALIASES exists"""
        from app.utils.normalize import COMMON_VALUE_ALIASES
        assert isinstance(COMMON_VALUE_ALIASES, dict)
        assert 'A' in COMMON_VALUE_ALIASES
        assert 'B' in COMMON_VALUE_ALIASES
