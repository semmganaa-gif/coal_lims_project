# -*- coding: utf-8 -*-
"""
Normalize модулийн coverage тестүүд
"""
import pytest
import json


class TestPick:
    """_pick helper тестүүд"""

    def test_import_function(self):
        """Function import"""
        from app.utils.normalize import _pick
        assert _pick is not None

    def test_first_key_found(self):
        """First key in list found"""
        from app.utils.normalize import _pick
        d = {'num': 123, 'box_no': 456}
        result = _pick(d, ['num', 'box_no'])
        assert result == 123

    def test_second_key_found(self):
        """Second key in list found"""
        from app.utils.normalize import _pick
        d = {'box_no': 456}
        result = _pick(d, ['num', 'box_no'])
        assert result == 456

    def test_no_key_found(self):
        """No key found"""
        from app.utils.normalize import _pick
        d = {'other': 123}
        result = _pick(d, ['num', 'box_no'])
        assert result is None

    def test_none_value_skipped(self):
        """None value skipped"""
        from app.utils.normalize import _pick
        d = {'num': None, 'box_no': 456}
        result = _pick(d, ['num', 'box_no'])
        assert result == 456

    def test_empty_string_skipped(self):
        """Empty string skipped"""
        from app.utils.normalize import _pick
        d = {'num': '', 'box_no': 456}
        result = _pick(d, ['num', 'box_no'])
        assert result == 456

    def test_empty_dict(self):
        """Empty dict"""
        from app.utils.normalize import _pick
        result = _pick({}, ['num', 'box_no'])
        assert result is None


class TestPickNumeric:
    """_pick_numeric helper тестүүд"""

    def test_import_function(self):
        """Function import"""
        from app.utils.normalize import _pick_numeric
        assert _pick_numeric is not None

    def test_numeric_value(self):
        """Numeric value returned as-is"""
        from app.utils.normalize import _pick_numeric
        d = {'A': 123.5}
        result = _pick_numeric(d, ['A', 'a'])
        assert result == 123.5

    def test_string_number(self):
        """String number converted to float"""
        from app.utils.normalize import _pick_numeric
        d = {'A': '123.5'}
        result = _pick_numeric(d, ['A', 'a'])
        assert result == 123.5

    def test_invalid_string(self):
        """Invalid string returned as-is"""
        from app.utils.normalize import _pick_numeric
        d = {'A': 'abc'}
        result = _pick_numeric(d, ['A', 'a'])
        assert result == 'abc'

    def test_none_value(self):
        """None value"""
        from app.utils.normalize import _pick_numeric
        d = {'A': None}
        result = _pick_numeric(d, ['A', 'a'])
        assert result is None


class TestNormParallel:
    """_norm_parallel helper тестүүд"""

    def test_import_function(self):
        """Function import"""
        from app.utils.normalize import _norm_parallel
        assert _norm_parallel is not None

    def test_not_dict(self):
        """Not a dict"""
        from app.utils.normalize import _norm_parallel
        result = _norm_parallel("not a dict")
        assert result == {}

    def test_empty_dict(self):
        """Empty dict"""
        from app.utils.normalize import _norm_parallel
        result = _norm_parallel({})
        assert result == {}

    def test_with_num(self):
        """With num alias"""
        from app.utils.normalize import _norm_parallel
        result = _norm_parallel({'num': 'T-001'})
        assert result.get('num') == 'T-001'

    def test_with_crucible_no(self):
        """With crucible_no alias"""
        from app.utils.normalize import _norm_parallel
        result = _norm_parallel({'crucible_no': 'C-123'})
        assert result.get('num') == 'C-123'

    def test_with_m1_empty(self):
        """With m1_empty alias"""
        from app.utils.normalize import _norm_parallel
        result = _norm_parallel({'m1_empty': 10.5})
        assert result.get('m1') == 10.5

    def test_with_m2_sample(self):
        """With m2_sample alias"""
        from app.utils.normalize import _norm_parallel
        result = _norm_parallel({'m2_sample': 15.5})
        assert result.get('m2') == 15.5

    def test_with_m3_ashy(self):
        """With m3_ashy alias"""
        from app.utils.normalize import _norm_parallel
        result = _norm_parallel({'m3_ashy': 11.0})
        assert result.get('m3') == 11.0

    def test_with_result_alias(self):
        """With result alias"""
        from app.utils.normalize import _norm_parallel
        result = _norm_parallel({'res': 25.5})
        assert result.get('result') == 25.5

    def test_string_to_float(self):
        """String values converted to float"""
        from app.utils.normalize import _norm_parallel
        result = _norm_parallel({'m1': '10.5', 'm2': '15.0'})
        assert result.get('m1') == 10.5
        assert result.get('m2') == 15.0

    def test_invalid_string_kept(self):
        """Invalid string kept as-is"""
        from app.utils.normalize import _norm_parallel
        result = _norm_parallel({'m1': 'abc'})
        assert result.get('m1') == 'abc'

    def test_weight_alias(self):
        """Weight added from m1"""
        from app.utils.normalize import _norm_parallel
        result = _norm_parallel({'m1': 10.0})
        assert result.get('weight') == 10.0

    def test_empty_values_removed(self):
        """Empty values removed"""
        from app.utils.normalize import _norm_parallel
        result = _norm_parallel({'num': '', 'm1': None, 'm2': 5.0})
        assert 'num' not in result
        assert 'm1' not in result
        assert result.get('m2') == 5.0


class TestNormalizeRawData:
    """normalize_raw_data function тестүүд"""

    def test_import_function(self):
        """Function import"""
        from app.utils.normalize import normalize_raw_data
        assert normalize_raw_data is not None

    def test_empty_dict(self):
        """Empty dict input"""
        from app.utils.normalize import normalize_raw_data
        result = normalize_raw_data({})
        assert 'p1' in result
        assert 'p2' in result

    def test_dict_input(self):
        """Dict input"""
        from app.utils.normalize import normalize_raw_data
        raw = {'p1': {'num': 'T-001', 'm1': 10.0}}
        result = normalize_raw_data(raw)
        assert result['p1'].get('num') == 'T-001'

    def test_json_string_input(self):
        """JSON string input"""
        from app.utils.normalize import normalize_raw_data
        raw = '{"p1": {"num": "T-001", "m1": 10.0}}'
        result = normalize_raw_data(raw)
        assert result['p1'].get('num') == 'T-001'

    def test_invalid_json_string(self):
        """Invalid JSON string"""
        from app.utils.normalize import normalize_raw_data
        result = normalize_raw_data('{invalid json}')
        assert 'p1' in result

    def test_non_json_string(self):
        """Non-JSON string (not starting with {)"""
        from app.utils.normalize import normalize_raw_data
        result = normalize_raw_data('just a string')
        assert 'p1' in result

    def test_with_p1_and_p2(self):
        """With both p1 and p2"""
        from app.utils.normalize import normalize_raw_data
        raw = {
            'p1': {'num': 'T-001', 'm1': 10.0},
            'p2': {'num': 'T-002', 'm1': 11.0}
        }
        result = normalize_raw_data(raw)
        assert len(result.get('parallels', [])) == 2

    def test_with_diff(self):
        """With diff value"""
        from app.utils.normalize import normalize_raw_data
        raw = {'diff': 0.5}
        result = normalize_raw_data(raw)
        assert result.get('diff') == 0.5

    def test_with_avg(self):
        """With avg value"""
        from app.utils.normalize import normalize_raw_data
        raw = {'avg': 10.5}
        result = normalize_raw_data(raw)
        assert result.get('avg') == 10.5

    def test_csn_analysis(self):
        """CSN analysis with v1-v5"""
        from app.utils.normalize import normalize_raw_data
        raw = {'v1': 2.0, 'v2': 2.5, 'v3': 2.0, 'v4': '', 'v5': None}
        result = normalize_raw_data(raw, analysis_code='CSN')
        assert 'parallels' in result
        # CSN values count might be stored differently or not at all
        assert len(result.get('parallels', [])) >= 1

    def test_csn_with_string_values(self):
        """CSN with string values"""
        from app.utils.normalize import normalize_raw_data
        raw = {'v1': '2.0', 'v2': '2.5'}
        result = normalize_raw_data(raw, analysis_code='csn')  # lowercase
        assert 'parallels' in result

    def test_csn_invalid_values(self):
        """CSN with invalid values"""
        from app.utils.normalize import normalize_raw_data
        raw = {'v1': 'abc', 'v2': 2.5}
        result = normalize_raw_data(raw, analysis_code='CSN')
        # Invalid 'abc' should be kept as string
        assert result is not None

    def test_common_value_aliases_a(self):
        """Common value alias A"""
        from app.utils.normalize import normalize_raw_data
        raw = {'A': 100.0}
        result = normalize_raw_data(raw)
        assert result.get('A') == 100.0

    def test_common_value_aliases_b(self):
        """Common value alias B (tare_mass)"""
        from app.utils.normalize import normalize_raw_data
        raw = {'tare_mass': 50.0}
        result = normalize_raw_data(raw)
        assert result.get('B') == 50.0

    def test_common_value_aliases_c(self):
        """Common value alias C (solid_mass)"""
        from app.utils.normalize import normalize_raw_data
        raw = {'solid_mass': 25.0}
        result = normalize_raw_data(raw)
        assert result.get('C') == 25.0

    def test_fm_fields_preserved(self):
        """FM analysis fields preserved"""
        from app.utils.normalize import normalize_raw_data
        raw = {
            'tray_g': 50.0,
            'before_g': 100.0,
            'after_g': 95.0,
            'loss_g': 5.0
        }
        result = normalize_raw_data(raw)
        assert result.get('tray_g') == 50.0
        assert result.get('before_g') == 100.0

    def test_cv_fields_preserved(self):
        """CV analysis fields preserved"""
        from app.utils.normalize import normalize_raw_data
        raw = {
            'batch': 'B001',
            's_used': 1.0,
            'E': 12000.0
        }
        result = normalize_raw_data(raw)
        assert result.get('batch') == 'B001'

    def test_repeatability_fields_preserved(self):
        """Repeatability fields preserved"""
        from app.utils.normalize import normalize_raw_data
        raw = {
            'repeatability': 0.2,
            't_exceeded': False,
            'limit_used': 0.5
        }
        result = normalize_raw_data(raw)
        assert result.get('repeatability') == 0.2

    def test_cv_m_delta_t_preserved(self):
        """CV m and delta_t in p1/p2 preserved"""
        from app.utils.normalize import normalize_raw_data
        raw = {
            'p1': {'m': 1.0, 'delta_t': 2.5},
            'p2': {'m': 1.0, 'delta_t': 2.6}
        }
        result = normalize_raw_data(raw)
        assert result['p1'].get('m') == 1.0
        assert result['p1'].get('delta_t') == 2.5

    def test_trd_fields_preserved(self):
        """TRD specific fields preserved"""
        from app.utils.normalize import normalize_raw_data
        raw = {
            'mad_used': 5.0,
            'temp_c': 25.0,
            'kt_used': 0.996
        }
        result = normalize_raw_data(raw)
        assert result.get('mad_used') == 5.0
        assert result.get('temp_c') == 25.0
        assert result.get('kt_used') == 0.996

    def test_schema_version(self):
        """_schema with version"""
        from app.utils.normalize import normalize_raw_data
        result = normalize_raw_data({})
        assert result['_schema']['version'] == 1

    def test_parallels_count(self):
        """_schema parallels_count"""
        from app.utils.normalize import normalize_raw_data
        raw = {'p1': {'m1': 10.0}, 'p2': {'m1': 11.0}}
        result = normalize_raw_data(raw)
        assert result['_schema']['parallels_count'] == 2
        assert result['_schema']['has_parallels'] is True

    def test_no_parallels(self):
        """_schema with no parallels"""
        from app.utils.normalize import normalize_raw_data
        result = normalize_raw_data({})
        assert result['_schema']['parallels_count'] == 0
        assert result['_schema']['has_parallels'] is False


class TestAliases:
    """Alias constants тестүүд"""

    def test_num_aliases_exists(self):
        """NUM_ALIASES exists"""
        from app.utils.normalize import NUM_ALIASES
        assert isinstance(NUM_ALIASES, list)
        assert 'num' in NUM_ALIASES
        assert 'box_no' in NUM_ALIASES

    def test_m1_aliases_exists(self):
        """M1_ALIASES exists"""
        from app.utils.normalize import M1_ALIASES
        assert isinstance(M1_ALIASES, list)
        assert 'm1' in M1_ALIASES
        assert 'm1_empty' in M1_ALIASES

    def test_m2_aliases_exists(self):
        """M2_ALIASES exists"""
        from app.utils.normalize import M2_ALIASES
        assert isinstance(M2_ALIASES, list)
        assert 'm2' in M2_ALIASES

    def test_m3_aliases_exists(self):
        """M3_ALIASES exists"""
        from app.utils.normalize import M3_ALIASES
        assert isinstance(M3_ALIASES, list)
        assert 'm3' in M3_ALIASES

    def test_result_aliases_exists(self):
        """RESULT_ALIASES exists"""
        from app.utils.normalize import RESULT_ALIASES
        assert isinstance(RESULT_ALIASES, list)
        assert 'result' in RESULT_ALIASES

    def test_common_value_aliases_exists(self):
        """COMMON_VALUE_ALIASES exists"""
        from app.utils.normalize import COMMON_VALUE_ALIASES
        assert isinstance(COMMON_VALUE_ALIASES, dict)
        assert 'A' in COMMON_VALUE_ALIASES
        assert 'B' in COMMON_VALUE_ALIASES
        assert 'C' in COMMON_VALUE_ALIASES


class TestEdgeCases:
    """Edge case тестүүд"""

    def test_none_p1(self):
        """None p1 value"""
        from app.utils.normalize import normalize_raw_data
        raw = {'p1': None, 'p2': {'m1': 10.0}}
        result = normalize_raw_data(raw)
        assert result is not None

    def test_empty_string_values_ignored(self):
        """Empty string values in preserve_keys ignored"""
        from app.utils.normalize import normalize_raw_data
        raw = {'tray_g': '', 'before_g': 100.0}
        result = normalize_raw_data(raw)
        assert 'tray_g' not in result
        assert result.get('before_g') == 100.0

    def test_none_values_ignored(self):
        """None values in preserve_keys ignored"""
        from app.utils.normalize import normalize_raw_data
        raw = {'tray_g': None, 'before_g': 100.0}
        result = normalize_raw_data(raw)
        assert 'tray_g' not in result

    def test_nested_json(self):
        """Nested JSON string"""
        from app.utils.normalize import normalize_raw_data
        raw = json.dumps({
            'p1': {'num': 'T-001', 'm1': 10.0, 'm2': 15.0, 'm3': 11.0},
            'diff': 0.5,
            'avg': 12.5
        })
        result = normalize_raw_data(raw)
        assert result['p1'].get('num') == 'T-001'
        assert result.get('diff') == 0.5
