# -*- coding: utf-8 -*-
"""
Tests for app/utils/normalize.py
Raw data normalization tests
"""
import pytest
import json


class TestPick:
    """_pick function tests"""

    def test_import(self):
        """Import function"""
        from app.utils.normalize import _pick
        assert callable(_pick)

    def test_first_key_found(self):
        """Returns value for first matching key"""
        from app.utils.normalize import _pick

        d = {"a": 1, "b": 2, "c": 3}
        result = _pick(d, ["a", "b", "c"])
        assert result == 1

    def test_second_key_found(self):
        """Returns value for second key when first missing"""
        from app.utils.normalize import _pick

        d = {"b": 2, "c": 3}
        result = _pick(d, ["a", "b", "c"])
        assert result == 2

    def test_no_key_found(self):
        """Returns None when no key found"""
        from app.utils.normalize import _pick

        d = {"x": 1}
        result = _pick(d, ["a", "b", "c"])
        assert result is None

    def test_none_value_skipped(self):
        """Skips None values"""
        from app.utils.normalize import _pick

        d = {"a": None, "b": 2}
        result = _pick(d, ["a", "b"])
        assert result == 2

    def test_empty_string_skipped(self):
        """Skips empty string values"""
        from app.utils.normalize import _pick

        d = {"a": "", "b": "value"}
        result = _pick(d, ["a", "b"])
        assert result == "value"

    def test_empty_dict(self):
        """Returns None for empty dict"""
        from app.utils.normalize import _pick

        result = _pick({}, ["a", "b"])
        assert result is None


class TestNormParallel:
    """_norm_parallel function tests"""

    def test_import(self):
        """Import function"""
        from app.utils.normalize import _norm_parallel
        assert callable(_norm_parallel)

    def test_empty_input(self):
        """Empty dict returns empty dict"""
        from app.utils.normalize import _norm_parallel

        result = _norm_parallel({})
        assert result == {}

    def test_non_dict_input(self):
        """Non-dict returns empty dict"""
        from app.utils.normalize import _norm_parallel

        result = _norm_parallel("not a dict")
        assert result == {}

    def test_num_alias(self):
        """Picks num from aliases"""
        from app.utils.normalize import _norm_parallel

        result = _norm_parallel({"box_no": "B123"})
        assert result.get("num") == "B123"

    def test_m1_alias(self):
        """Picks m1 from aliases"""
        from app.utils.normalize import _norm_parallel

        result = _norm_parallel({"m1_empty": 10.5})
        assert result.get("m1") == 10.5

    def test_m2_alias(self):
        """Picks m2 from aliases"""
        from app.utils.normalize import _norm_parallel

        result = _norm_parallel({"m2_sample": 15.5})
        assert result.get("m2") == 15.5

    def test_m3_alias(self):
        """Picks m3 from aliases"""
        from app.utils.normalize import _norm_parallel

        result = _norm_parallel({"m3_dried_box": 12.3})
        assert result.get("m3") == 12.3

    def test_result_alias(self):
        """Picks result from aliases"""
        from app.utils.normalize import _norm_parallel

        result = _norm_parallel({"res": 5.67})
        assert result.get("result") == 5.67

    def test_string_to_float_conversion(self):
        """Converts string to float"""
        from app.utils.normalize import _norm_parallel

        result = _norm_parallel({"m1": "10.5", "m2": "15.5"})
        assert result.get("m1") == 10.5
        assert result.get("m2") == 15.5

    def test_weight_fallback(self):
        """Adds weight field from m1"""
        from app.utils.normalize import _norm_parallel

        result = _norm_parallel({"m1": 10.5})
        assert result.get("weight") == 10.5

    def test_null_values_removed(self):
        """Removes None and empty values"""
        from app.utils.normalize import _norm_parallel

        result = _norm_parallel({"m1": 10.5, "m2": None, "m3": ""})
        assert "m2" not in result
        assert "m3" not in result


class TestNormalizeRawData:
    """normalize_raw_data function tests"""

    def test_import(self):
        """Import function"""
        from app.utils.normalize import normalize_raw_data
        assert callable(normalize_raw_data)

    def test_empty_dict(self):
        """Empty dict returns structure"""
        from app.utils.normalize import normalize_raw_data

        result = normalize_raw_data({})
        assert "p1" in result
        assert "p2" in result
        assert "_schema" in result

    def test_json_string_input(self):
        """Parses JSON string"""
        from app.utils.normalize import normalize_raw_data

        json_str = '{"p1": {"m1": 10.5}}'
        result = normalize_raw_data(json_str)
        assert result["p1"].get("m1") == 10.5

    def test_dict_input(self):
        """Works with dict input"""
        from app.utils.normalize import normalize_raw_data

        data = {"p1": {"m1": 10.5}}
        result = normalize_raw_data(data)
        assert result["p1"].get("m1") == 10.5

    def test_invalid_json_string(self):
        """Invalid JSON returns empty structure"""
        from app.utils.normalize import normalize_raw_data

        result = normalize_raw_data("not json")
        assert result["p1"] == {}
        assert result["p2"] == {}

    def test_parallels_created(self):
        """Creates parallels list"""
        from app.utils.normalize import normalize_raw_data

        data = {"p1": {"m1": 10.5}, "p2": {"m1": 11.0}}
        result = normalize_raw_data(data)
        assert "parallels" in result
        assert len(result["parallels"]) == 2

    def test_diff_preserved(self):
        """Preserves diff field"""
        from app.utils.normalize import normalize_raw_data

        data = {"diff": 0.05}
        result = normalize_raw_data(data)
        assert result["diff"] == 0.05

    def test_avg_preserved(self):
        """Preserves avg field"""
        from app.utils.normalize import normalize_raw_data

        data = {"avg": 10.75}
        result = normalize_raw_data(data)
        assert result["avg"] == 10.75

    def test_schema_version(self):
        """Schema has version"""
        from app.utils.normalize import normalize_raw_data

        result = normalize_raw_data({})
        assert result["_schema"]["version"] == 1

    def test_schema_parallels_count(self):
        """Schema has parallels count"""
        from app.utils.normalize import normalize_raw_data

        data = {"p1": {"m1": 10.5}, "p2": {"m1": 11.0}}
        result = normalize_raw_data(data)
        assert result["_schema"]["parallels_count"] == 2

    def test_csn_analysis(self):
        """CSN analysis special handling"""
        from app.utils.normalize import normalize_raw_data

        data = {"v1": 1.0, "v2": 1.5, "v3": 2.0}
        result = normalize_raw_data(data, analysis_code="CSN")
        assert "parallels" in result
        # CSN values are stored in parallels[0]
        assert len(result["parallels"]) == 1
        assert result["parallels"][0].get("v1") == 1.0

    def test_fm_fields_preserved(self):
        """FM analysis fields preserved"""
        from app.utils.normalize import normalize_raw_data

        data = {
            "tray_g": 100.0,
            "before_g": 150.0,
            "after_g": 145.0,
            "loss_g": 5.0
        }
        result = normalize_raw_data(data)
        assert result["tray_g"] == 100.0
        assert result["before_g"] == 150.0

    def test_cv_fields_preserved(self):
        """CV analysis fields preserved"""
        from app.utils.normalize import normalize_raw_data

        data = {
            "batch": "B001",
            "s_used": 0.5,
            "E": 1500.0
        }
        result = normalize_raw_data(data)
        assert result["batch"] == "B001"
        assert result["s_used"] == 0.5

    def test_repeatability_fields(self):
        """Repeatability fields preserved"""
        from app.utils.normalize import normalize_raw_data

        data = {
            "repeatability": 0.02,
            "t_exceeded": False,
            "limit_used": 0.5
        }
        result = normalize_raw_data(data)
        assert result["repeatability"] == 0.02

    def test_trd_fields(self):
        """TRD fields preserved"""
        from app.utils.normalize import normalize_raw_data

        data = {
            "mad_used": 5.0,
            "temp_c": 25.0,
            "kt_used": 0.98
        }
        result = normalize_raw_data(data)
        assert result["mad_used"] == 5.0
        assert result["temp_c"] == 25.0

    def test_p1_delta_t_preserved(self):
        """CV p1 delta_t preserved"""
        from app.utils.normalize import normalize_raw_data

        data = {"p1": {"m": 1.0, "delta_t": 2.5}}
        result = normalize_raw_data(data)
        assert result["p1"].get("delta_t") == 2.5

    def test_common_value_aliases(self):
        """Common value aliases (A, B, C) preserved"""
        from app.utils.normalize import normalize_raw_data

        data = {"A": 100.0, "B": 50.0, "C": 30.0}
        result = normalize_raw_data(data)
        assert result.get("A") == 100.0
        assert result.get("B") == 50.0


class TestPickNumeric:
    """_pick_numeric function tests"""

    def test_import(self):
        """Import function"""
        from app.utils.normalize import _pick_numeric
        assert callable(_pick_numeric)

    def test_returns_float(self):
        """Returns float value"""
        from app.utils.normalize import _pick_numeric

        result = _pick_numeric({"a": 10.5}, ["a"])
        assert result == 10.5

    def test_string_to_float(self):
        """Converts string to float"""
        from app.utils.normalize import _pick_numeric

        result = _pick_numeric({"a": "10.5"}, ["a"])
        assert result == 10.5

    def test_invalid_string(self):
        """Invalid string returns as-is"""
        from app.utils.normalize import _pick_numeric

        result = _pick_numeric({"a": "not a number"}, ["a"])
        assert result == "not a number"

    def test_none_returns_none(self):
        """None returns None"""
        from app.utils.normalize import _pick_numeric

        result = _pick_numeric({}, ["a"])
        assert result is None


class TestAliases:
    """Alias constants tests"""

    def test_num_aliases_exist(self):
        """NUM_ALIASES exists"""
        from app.utils.normalize import NUM_ALIASES
        assert isinstance(NUM_ALIASES, list)
        assert "num" in NUM_ALIASES
        assert "box_no" in NUM_ALIASES

    def test_m1_aliases_exist(self):
        """M1_ALIASES exists"""
        from app.utils.normalize import M1_ALIASES
        assert isinstance(M1_ALIASES, list)
        assert "m1" in M1_ALIASES
        assert "tare" in M1_ALIASES

    def test_m2_aliases_exist(self):
        """M2_ALIASES exists"""
        from app.utils.normalize import M2_ALIASES
        assert isinstance(M2_ALIASES, list)
        assert "m2" in M2_ALIASES

    def test_m3_aliases_exist(self):
        """M3_ALIASES exists"""
        from app.utils.normalize import M3_ALIASES
        assert isinstance(M3_ALIASES, list)
        assert "m3" in M3_ALIASES

    def test_result_aliases_exist(self):
        """RESULT_ALIASES exists"""
        from app.utils.normalize import RESULT_ALIASES
        assert isinstance(RESULT_ALIASES, list)
        assert "result" in RESULT_ALIASES

    def test_common_value_aliases_exist(self):
        """COMMON_VALUE_ALIASES exists"""
        from app.utils.normalize import COMMON_VALUE_ALIASES
        assert isinstance(COMMON_VALUE_ALIASES, dict)
        assert "A" in COMMON_VALUE_ALIASES


class TestEdgeCases:
    """Edge case tests"""

    def test_none_p1_p2(self):
        """Handles None p1/p2"""
        from app.utils.normalize import normalize_raw_data

        data = {"p1": None, "p2": None}
        result = normalize_raw_data(data)
        assert result["p1"] == {}
        assert result["p2"] == {}

    def test_empty_string_json(self):
        """Empty string JSON"""
        from app.utils.normalize import normalize_raw_data

        result = normalize_raw_data("")
        assert "_schema" in result

    def test_whitespace_string(self):
        """Whitespace string"""
        from app.utils.normalize import normalize_raw_data

        result = normalize_raw_data("   ")
        assert "_schema" in result

    def test_nested_none_values(self):
        """Nested None values"""
        from app.utils.normalize import normalize_raw_data

        data = {
            "p1": {"m1": None, "m2": 10.5},
            "diff": None
        }
        result = normalize_raw_data(data)
        assert "m1" not in result["p1"]
        assert "diff" not in result

    def test_csn_with_empty_values(self):
        """CSN with empty values"""
        from app.utils.normalize import normalize_raw_data

        data = {"v1": 1.0, "v2": "", "v3": None}
        result = normalize_raw_data(data, analysis_code="csn")  # lowercase
        assert "parallels" in result

    def test_json_with_extra_whitespace(self):
        """JSON with extra whitespace"""
        from app.utils.normalize import normalize_raw_data

        json_str = '  {"p1": {"m1": 10.5}}  '
        result = normalize_raw_data(json_str)
        assert result["p1"].get("m1") == 10.5

    def test_does_not_modify_original(self):
        """Does not modify original dict"""
        from app.utils.normalize import normalize_raw_data

        original = {"p1": {"m1": 10.5}}
        normalize_raw_data(original)
        assert original == {"p1": {"m1": 10.5}}

    def test_solid_fields_preserved(self):
        """Solid analysis fields preserved"""
        from app.utils.normalize import normalize_raw_data

        data = {
            "solid_pct": 95.5,
            "wet_mass": 100.0,
            "formula": "solid formula"
        }
        result = normalize_raw_data(data)
        assert result["solid_pct"] == 95.5


class TestNormParallelEdgeCases:
    """_norm_parallel edge case tests"""

    def test_all_num_aliases(self):
        """All NUM_ALIASES work"""
        from app.utils.normalize import _norm_parallel, NUM_ALIASES
        for alias in NUM_ALIASES:
            result = _norm_parallel({alias: "TEST"})
            assert result.get("num") == "TEST", f"{alias} should map to num"

    def test_all_m1_aliases(self):
        """All M1_ALIASES work"""
        from app.utils.normalize import _norm_parallel, M1_ALIASES
        for alias in M1_ALIASES:
            result = _norm_parallel({alias: 10.5})
            assert result.get("m1") == 10.5, f"{alias} should map to m1"

    def test_all_m2_aliases(self):
        """All M2_ALIASES work"""
        from app.utils.normalize import _norm_parallel, M2_ALIASES
        for alias in M2_ALIASES:
            result = _norm_parallel({alias: 15.5})
            assert result.get("m2") == 15.5, f"{alias} should map to m2"

    def test_all_m3_aliases(self):
        """All M3_ALIASES work"""
        from app.utils.normalize import _norm_parallel, M3_ALIASES
        for alias in M3_ALIASES:
            result = _norm_parallel({alias: 12.3})
            assert result.get("m3") == 12.3, f"{alias} should map to m3"

    def test_all_result_aliases(self):
        """All RESULT_ALIASES work"""
        from app.utils.normalize import _norm_parallel, RESULT_ALIASES
        for alias in RESULT_ALIASES:
            result = _norm_parallel({alias: 5.67})
            assert result.get("result") == 5.67, f"{alias} should map to result"

    def test_priority_order(self):
        """First alias in list takes priority"""
        from app.utils.normalize import _norm_parallel
        # num is first in NUM_ALIASES
        result = _norm_parallel({"num": "A", "box_no": "B"})
        assert result.get("num") == "A"

    def test_invalid_float_string(self):
        """Invalid float string kept as-is"""
        from app.utils.normalize import _norm_parallel
        result = _norm_parallel({"m1": "not_a_number"})
        assert result.get("m1") == "not_a_number"

    def test_list_input(self):
        """List input returns empty dict"""
        from app.utils.normalize import _norm_parallel
        result = _norm_parallel([1, 2, 3])
        assert result == {}

    def test_none_input(self):
        """None input returns empty dict"""
        from app.utils.normalize import _norm_parallel
        result = _norm_parallel(None)
        assert result == {}

    def test_zero_values_preserved(self):
        """Zero values preserved (not treated as empty)"""
        from app.utils.normalize import _norm_parallel
        result = _norm_parallel({"m1": 0, "m2": 0.0})
        assert result.get("m1") == 0
        assert result.get("m2") == 0.0


class TestNormalizeRawDataExtended:
    """Extended normalize_raw_data tests"""

    def test_json_braces_only(self):
        """JSON with only braces"""
        from app.utils.normalize import normalize_raw_data
        result = normalize_raw_data("{}")
        assert "_schema" in result

    def test_deeply_nested_json(self):
        """Deeply nested JSON structure"""
        from app.utils.normalize import normalize_raw_data
        data = {
            "p1": {
                "m1": 10.5,
                "nested": {"deep": "value"}
            }
        }
        result = normalize_raw_data(data)
        assert result["p1"].get("m1") == 10.5

    def test_csn_all_five_values(self):
        """CSN with all 5 values - check parallels contains all values"""
        from app.utils.normalize import normalize_raw_data
        data = {"v1": 1.0, "v2": 1.5, "v3": 2.0, "v4": 2.5, "v5": 3.0}
        result = normalize_raw_data(data, analysis_code="CSN")
        # CSN values are stored in parallels
        assert "parallels" in result
        assert len(result["parallels"]) == 1
        csn_row = result["parallels"][0]
        assert csn_row["v1"] == 1.0
        assert csn_row["v2"] == 1.5
        assert csn_row["v3"] == 2.0
        assert csn_row["v4"] == 2.5
        assert csn_row["v5"] == 3.0

    def test_csn_partial_values(self):
        """CSN with partial values - only v1 and v3"""
        from app.utils.normalize import normalize_raw_data
        data = {"v1": 1.0, "v3": 2.0}
        result = normalize_raw_data(data, analysis_code="CSN")
        # CSN values are stored in parallels
        assert "parallels" in result
        csn_row = result["parallels"][0]
        assert csn_row["v1"] == 1.0
        assert csn_row["v3"] == 2.0
        assert "v2" not in csn_row  # v2 not provided

    def test_csn_string_values(self):
        """CSN with string values"""
        from app.utils.normalize import normalize_raw_data
        data = {"v1": "1.5", "v2": "2.5"}
        result = normalize_raw_data(data, analysis_code="CSN")
        assert result["parallels"][0]["v1"] == 1.5

    def test_both_parallels_empty(self):
        """Both p1 and p2 empty"""
        from app.utils.normalize import normalize_raw_data
        result = normalize_raw_data({"p1": {}, "p2": {}})
        assert "parallels" not in result or len(result.get("parallels", [])) == 0

    def test_only_p1(self):
        """Only p1 has data"""
        from app.utils.normalize import normalize_raw_data
        data = {"p1": {"m1": 10.5}}
        result = normalize_raw_data(data)
        assert len(result["parallels"]) == 1

    def test_only_p2(self):
        """Only p2 has data"""
        from app.utils.normalize import normalize_raw_data
        data = {"p2": {"m1": 11.0}}
        result = normalize_raw_data(data)
        assert len(result["parallels"]) == 1

    def test_p1_m_field_preserved(self):
        """CV p1 m field preserved"""
        from app.utils.normalize import normalize_raw_data
        data = {"p1": {"m": 1.234}}
        result = normalize_raw_data(data)
        assert result["p1"].get("m") == 1.234

    def test_p2_m_delta_t_preserved(self):
        """CV p2 m and delta_t preserved"""
        from app.utils.normalize import normalize_raw_data
        data = {"p2": {"m": 1.5, "delta_t": 3.2}}
        result = normalize_raw_data(data)
        assert result["p2"].get("m") == 1.5
        assert result["p2"].get("delta_t") == 3.2

    def test_is_low_avg_preserved(self):
        """is_low_avg field preserved"""
        from app.utils.normalize import normalize_raw_data
        data = {"is_low_avg": True}
        result = normalize_raw_data(data)
        assert result["is_low_avg"] is True

    def test_retest_mode_preserved(self):
        """retest_mode field preserved"""
        from app.utils.normalize import normalize_raw_data
        data = {"retest_mode": "average"}
        result = normalize_raw_data(data)
        assert result["retest_mode"] == "average"


class TestPickEdgeCases:
    """_pick edge case tests"""

    def test_zero_value_not_skipped(self):
        """Zero values are not skipped"""
        from app.utils.normalize import _pick
        result = _pick({"a": 0}, ["a"])
        assert result == 0

    def test_false_value_not_skipped(self):
        """False values are not skipped"""
        from app.utils.normalize import _pick
        result = _pick({"a": False}, ["a"])
        assert result is False

    def test_empty_list_value_not_skipped(self):
        """Empty list is not skipped"""
        from app.utils.normalize import _pick
        result = _pick({"a": []}, ["a"])
        assert result == []


class TestRealWorldAnalysis:
    """Real world analysis data tests"""

    def test_typical_mt_data(self):
        """Typical MT (moisture) analysis data"""
        from app.utils.normalize import normalize_raw_data
        data = {
            "p1": {
                "num": "B001",
                "m1_empty": 10.123,
                "m2_sample": 15.456,
                "m3_dried_box": 14.789,
                "result": 4.32
            },
            "p2": {
                "num": "B002",
                "m1_empty": 10.234,
                "m2_sample": 15.567,
                "m3_dried_box": 14.890,
                "result": 4.29
            },
            "diff": 0.03,
            "avg": 4.305
        }
        result = normalize_raw_data(data)
        assert result["p1"]["num"] == "B001"
        assert result["p1"]["m1"] == 10.123
        assert result["diff"] == 0.03
        assert result["avg"] == 4.305

    def test_typical_cv_data(self):
        """Typical CV (calorific value) analysis data"""
        from app.utils.normalize import normalize_raw_data
        data = {
            "p1": {"m": 1.001, "delta_t": 2.534},
            "p2": {"m": 1.002, "delta_t": 2.541},
            "batch": "CV001",
            "s_used": 0.45,
            "E": 15000.0
        }
        result = normalize_raw_data(data)
        assert result["p1"]["m"] == 1.001
        assert result["p1"]["delta_t"] == 2.534
        assert result["batch"] == "CV001"

    def test_typical_trd_data(self):
        """Typical TRD (relative density) analysis data"""
        from app.utils.normalize import normalize_raw_data
        data = {
            "p1": {"bottle_num": "B01", "m": 0.789},
            "p2": {"bottle_num": "B02", "m": 0.792},
            "mad_used": 3.5,
            "temp_c": 25.0,
            "kt_used": 0.997
        }
        result = normalize_raw_data(data)
        assert result["mad_used"] == 3.5
        assert result["temp_c"] == 25.0
        assert result["kt_used"] == 0.997

    def test_typical_fm_data(self):
        """Typical FM (free moisture) analysis data"""
        from app.utils.normalize import normalize_raw_data
        data = {
            "tray_g": 500.0,
            "before_g": 2500.0,
            "after_g": 2380.0,
            "loss_g": 120.0,
            "fm_pct": 6.0
        }
        result = normalize_raw_data(data)
        assert result["tray_g"] == 500.0
        assert result["before_g"] == 2500.0
        assert result["loss_g"] == 120.0
