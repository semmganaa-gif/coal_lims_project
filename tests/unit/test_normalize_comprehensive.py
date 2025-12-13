# tests/unit/test_normalize_comprehensive.py
# -*- coding: utf-8 -*-
"""
Normalize utility comprehensive tests
"""
import pytest
from app.utils.normalize import (
    normalize_raw_data,
    _pick,
    _norm_parallel,
    _pick_numeric,
    NUM_ALIASES,
    M1_ALIASES,
    M2_ALIASES,
    M3_ALIASES,
    RESULT_ALIASES,
)


class TestPick:
    """_pick() функцийн тестүүд"""

    def test_picks_first_matching_key(self):
        """Should pick first matching key"""
        d = {"box_no": "123", "num": "456"}
        result = _pick(d, ["num", "box_no"])
        assert result == "456"

    def test_picks_from_aliases(self):
        """Should pick from alias list"""
        d = {"box_num": "ABC123"}
        result = _pick(d, NUM_ALIASES)
        assert result == "ABC123"

    def test_returns_none_if_not_found(self):
        """Should return None if no key found"""
        d = {"other_key": "value"}
        result = _pick(d, ["num", "box_no"])
        assert result is None

    def test_skips_none_values(self):
        """Should skip None values"""
        d = {"num": None, "box_no": "123"}
        result = _pick(d, ["num", "box_no"])
        assert result == "123"

    def test_skips_empty_string(self):
        """Should skip empty string values"""
        d = {"num": "", "box_no": "123"}
        result = _pick(d, ["num", "box_no"])
        assert result == "123"


class TestNormParallel:
    """_norm_parallel() функцийн тестүүд"""

    def test_extracts_num(self):
        """Should extract num field"""
        raw = {"box_no": "T123"}
        result = _norm_parallel(raw)
        assert result.get("num") == "T123"

    def test_extracts_m1(self):
        """Should extract m1 field"""
        raw = {"m1_empty": 10.5}
        result = _norm_parallel(raw)
        assert result.get("m1") == 10.5

    def test_extracts_m2(self):
        """Should extract m2 field"""
        raw = {"m2_sample": 15.3}
        result = _norm_parallel(raw)
        assert result.get("m2") == 15.3

    def test_extracts_m3(self):
        """Should extract m3 field"""
        raw = {"m3_dried_box": 11.2}
        result = _norm_parallel(raw)
        assert result.get("m3") == 11.2

    def test_extracts_result(self):
        """Should extract result field"""
        raw = {"result": 8.5}
        result = _norm_parallel(raw)
        assert result.get("result") == 8.5

    def test_converts_string_numbers(self):
        """Should convert string numbers to float"""
        raw = {"m1": "10.5", "m2": "15.3"}
        result = _norm_parallel(raw)
        assert result.get("m1") == 10.5
        assert result.get("m2") == 15.3

    def test_handles_non_dict_input(self):
        """Should handle non-dict input"""
        result = _norm_parallel("not a dict")
        assert result == {}

    def test_removes_empty_values(self):
        """Should remove empty values"""
        raw = {"num": "T123", "m1": None, "m2": ""}
        result = _norm_parallel(raw)
        assert "num" in result
        assert "m1" not in result
        assert "m2" not in result


class TestPickNumeric:
    """_pick_numeric() функцийн тестүүд"""

    def test_picks_float(self):
        """Should pick float value"""
        d = {"A": 10.5}
        result = _pick_numeric(d, ["A"])
        assert result == 10.5

    def test_converts_string_to_float(self):
        """Should convert string to float"""
        d = {"A": "10.5"}
        result = _pick_numeric(d, ["A"])
        assert result == 10.5

    def test_returns_string_if_cant_convert(self):
        """Should return string if can't convert to float"""
        d = {"A": "not a number"}
        result = _pick_numeric(d, ["A"])
        assert result == "not a number"

    def test_returns_none_if_not_found(self):
        """Should return None if not found"""
        d = {"B": 10.5}
        result = _pick_numeric(d, ["A"])
        assert result is None


class TestNormalizeRawData:
    """normalize_raw_data() функцийн тестүүд"""

    def test_handles_dict_input(self):
        """Should handle dict input"""
        raw = {"p1": {"m1": 10.5}, "p2": {"m1": 10.6}}
        result = normalize_raw_data(raw)
        assert "p1" in result
        assert "p2" in result

    def test_handles_json_string_input(self):
        """Should handle JSON string input"""
        raw = '{"p1": {"m1": 10.5}, "p2": {"m1": 10.6}}'
        result = normalize_raw_data(raw)
        assert "p1" in result
        assert "p2" in result

    def test_handles_invalid_json(self):
        """Should handle invalid JSON"""
        raw = "not valid json"
        result = normalize_raw_data(raw)
        assert "_schema" in result

    def test_preserves_diff_and_avg(self):
        """Should preserve diff and avg values"""
        raw = {"diff": 0.1, "avg": 10.55}
        result = normalize_raw_data(raw)
        assert result.get("diff") == 0.1
        assert result.get("avg") == 10.55

    def test_adds_schema_info(self):
        """Should add schema info"""
        raw = {"p1": {"m1": 10.5}}
        result = normalize_raw_data(raw)
        assert "_schema" in result
        assert result["_schema"]["version"] == 1

    def test_handles_csn_analysis(self):
        """Should handle CSN analysis with v1-v5"""
        raw = {"v1": 2.0, "v2": 2.5, "v3": 2.5, "v4": None, "v5": None}
        result = normalize_raw_data(raw, analysis_code="CSN")
        assert "parallels" in result
        assert "v1" in result["parallels"][0]

    def test_preserves_fm_fields(self):
        """Should preserve FM analysis fields"""
        raw = {"tray_g": 100, "before_g": 150, "after_g": 145}
        result = normalize_raw_data(raw)
        assert result.get("tray_g") == 100
        assert result.get("before_g") == 150
        assert result.get("after_g") == 145

    def test_preserves_cv_fields(self):
        """Should preserve CV analysis fields"""
        raw = {
            "p1": {"m": 1.0, "delta_t": 2.5},
            "p2": {"m": 1.0, "delta_t": 2.6}
        }
        result = normalize_raw_data(raw)
        assert result["p1"].get("m") == 1.0
        assert result["p1"].get("delta_t") == 2.5

    def test_creates_parallels_list(self):
        """Should create parallels list"""
        raw = {
            "p1": {"num": "T1", "m1": 10.5},
            "p2": {"num": "T2", "m1": 10.6}
        }
        result = normalize_raw_data(raw)
        assert "parallels" in result
        assert len(result["parallels"]) == 2


class TestAliases:
    """Alias constants tests"""

    def test_num_aliases_not_empty(self):
        """NUM_ALIASES should not be empty"""
        assert len(NUM_ALIASES) > 0
        assert "num" in NUM_ALIASES
        assert "box_no" in NUM_ALIASES

    def test_m1_aliases_not_empty(self):
        """M1_ALIASES should not be empty"""
        assert len(M1_ALIASES) > 0
        assert "m1" in M1_ALIASES

    def test_m2_aliases_not_empty(self):
        """M2_ALIASES should not be empty"""
        assert len(M2_ALIASES) > 0
        assert "m2" in M2_ALIASES

    def test_m3_aliases_not_empty(self):
        """M3_ALIASES should not be empty"""
        assert len(M3_ALIASES) > 0
        assert "m3" in M3_ALIASES

    def test_result_aliases_not_empty(self):
        """RESULT_ALIASES should not be empty"""
        assert len(RESULT_ALIASES) > 0
        assert "result" in RESULT_ALIASES
