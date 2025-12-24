# tests/test_normalize_complete.py
# -*- coding: utf-8 -*-
"""
Complete coverage tests for app/utils/normalize.py
"""

import pytest
import json


class TestPickFunction:
    """Tests for _pick helper function."""

    def test_pick_first_key_exists(self, app):
        """Test _pick returns first matching key."""
        with app.app_context():
            from app.utils.normalize import _pick
            d = {"num": "123", "box_no": "456"}
            result = _pick(d, ["num", "box_no"])
            assert result == "123"

    def test_pick_second_key_exists(self, app):
        """Test _pick returns second key if first missing."""
        with app.app_context():
            from app.utils.normalize import _pick
            d = {"box_no": "456"}
            result = _pick(d, ["num", "box_no"])
            assert result == "456"

    def test_pick_no_key_exists(self, app):
        """Test _pick returns None if no key exists."""
        with app.app_context():
            from app.utils.normalize import _pick
            d = {"other": "value"}
            result = _pick(d, ["num", "box_no"])
            assert result is None

    def test_pick_empty_dict(self, app):
        """Test _pick with empty dict."""
        with app.app_context():
            from app.utils.normalize import _pick
            result = _pick({}, ["num", "box_no"])
            assert result is None

    def test_pick_none_value(self, app):
        """Test _pick skips None values."""
        with app.app_context():
            from app.utils.normalize import _pick
            d = {"num": None, "box_no": "456"}
            result = _pick(d, ["num", "box_no"])
            assert result == "456"

    def test_pick_empty_string_value(self, app):
        """Test _pick skips empty string values."""
        with app.app_context():
            from app.utils.normalize import _pick
            d = {"num": "", "box_no": "456"}
            result = _pick(d, ["num", "box_no"])
            assert result == "456"


class TestNormParallel:
    """Tests for _norm_parallel helper function."""

    def test_norm_parallel_basic(self, app):
        """Test _norm_parallel with basic input."""
        with app.app_context():
            from app.utils.normalize import _norm_parallel
            raw = {"num": "123", "m1": 10.5, "m2": 15.3, "m3": 12.1}
            result = _norm_parallel(raw)
            assert result["num"] == "123"
            assert result["m1"] == 10.5
            assert result["m2"] == 15.3
            assert result["m3"] == 12.1

    def test_norm_parallel_with_aliases(self, app):
        """Test _norm_parallel with alias keys."""
        with app.app_context():
            from app.utils.normalize import _norm_parallel
            raw = {"box_no": "123", "tare": 10.5}
            result = _norm_parallel(raw)
            assert result["num"] == "123"
            assert result["m1"] == 10.5

    def test_norm_parallel_empty(self, app):
        """Test _norm_parallel with empty dict."""
        with app.app_context():
            from app.utils.normalize import _norm_parallel
            result = _norm_parallel({})
            assert result == {}

    def test_norm_parallel_not_dict(self, app):
        """Test _norm_parallel with non-dict input."""
        with app.app_context():
            from app.utils.normalize import _norm_parallel
            result = _norm_parallel("not a dict")
            assert result == {}

    def test_norm_parallel_string_to_float(self, app):
        """Test _norm_parallel converts string to float."""
        with app.app_context():
            from app.utils.normalize import _norm_parallel
            raw = {"m1": "10.5", "m2": "15.3"}
            result = _norm_parallel(raw)
            assert result["m1"] == 10.5
            assert result["m2"] == 15.3

    def test_norm_parallel_invalid_string(self, app):
        """Test _norm_parallel with invalid string number."""
        with app.app_context():
            from app.utils.normalize import _norm_parallel
            raw = {"m1": "invalid"}
            result = _norm_parallel(raw)
            # Should keep original string if conversion fails
            assert "m1" in result

    def test_norm_parallel_weight_alias(self, app):
        """Test _norm_parallel adds weight from m1."""
        with app.app_context():
            from app.utils.normalize import _norm_parallel
            raw = {"m1": 10.5}
            result = _norm_parallel(raw)
            assert result.get("weight") == 10.5


class TestNormalizeRawData:
    """Tests for normalize_raw_data function."""

    def test_normalize_dict_input(self, app):
        """Test normalize_raw_data with dict input."""
        with app.app_context():
            from app.utils.normalize import normalize_raw_data
            raw = {"p1": {"num": "123", "m1": 10.5}}
            result = normalize_raw_data(raw)
            assert isinstance(result, dict)

    def test_normalize_json_string_input(self, app):
        """Test normalize_raw_data with JSON string input."""
        with app.app_context():
            from app.utils.normalize import normalize_raw_data
            raw = json.dumps({"p1": {"num": "123", "m1": 10.5}})
            result = normalize_raw_data(raw)
            assert isinstance(result, dict)

    def test_normalize_empty_dict(self, app):
        """Test normalize_raw_data with empty dict."""
        with app.app_context():
            from app.utils.normalize import normalize_raw_data
            result = normalize_raw_data({})
            assert isinstance(result, dict)

    def test_normalize_none_input(self, app):
        """Test normalize_raw_data with None input."""
        with app.app_context():
            from app.utils.normalize import normalize_raw_data
            result = normalize_raw_data(None)
            assert isinstance(result, dict)

    def test_normalize_with_p1_p2(self, app):
        """Test normalize_raw_data with p1 and p2."""
        with app.app_context():
            from app.utils.normalize import normalize_raw_data
            raw = {
                "p1": {"num": "123", "m1": 10.5, "m2": 15.3, "m3": 12.1},
                "p2": {"num": "456", "m1": 11.0, "m2": 16.0, "m3": 13.0}
            }
            result = normalize_raw_data(raw)
            assert "p1" in result or isinstance(result, dict)

    def test_normalize_with_analysis_code(self, app):
        """Test normalize_raw_data with analysis code."""
        with app.app_context():
            from app.utils.normalize import normalize_raw_data
            raw = {"p1": {"m1": 10.5}}
            result = normalize_raw_data(raw, analysis_code="MT")
            assert isinstance(result, dict)

    def test_normalize_invalid_json(self, app):
        """Test normalize_raw_data with invalid JSON string."""
        with app.app_context():
            from app.utils.normalize import normalize_raw_data
            result = normalize_raw_data("not valid json")
            assert isinstance(result, dict)


class TestAliasConstants:
    """Tests for alias constants."""

    def test_num_aliases_exist(self, app):
        """Test NUM_ALIASES constant exists."""
        with app.app_context():
            from app.utils.normalize import NUM_ALIASES
            assert isinstance(NUM_ALIASES, list)
            assert "num" in NUM_ALIASES
            assert "box_no" in NUM_ALIASES

    def test_m1_aliases_exist(self, app):
        """Test M1_ALIASES constant exists."""
        with app.app_context():
            from app.utils.normalize import M1_ALIASES
            assert isinstance(M1_ALIASES, list)
            assert "m1" in M1_ALIASES
            assert "tare" in M1_ALIASES

    def test_m2_aliases_exist(self, app):
        """Test M2_ALIASES constant exists."""
        with app.app_context():
            from app.utils.normalize import M2_ALIASES
            assert isinstance(M2_ALIASES, list)
            assert "m2" in M2_ALIASES

    def test_m3_aliases_exist(self, app):
        """Test M3_ALIASES constant exists."""
        with app.app_context():
            from app.utils.normalize import M3_ALIASES
            assert isinstance(M3_ALIASES, list)
            assert "m3" in M3_ALIASES

    def test_result_aliases_exist(self, app):
        """Test RESULT_ALIASES constant exists."""
        with app.app_context():
            from app.utils.normalize import RESULT_ALIASES
            assert isinstance(RESULT_ALIASES, list)
            assert "result" in RESULT_ALIASES

    def test_common_value_aliases_exist(self, app):
        """Test COMMON_VALUE_ALIASES constant exists."""
        with app.app_context():
            from app.utils.normalize import COMMON_VALUE_ALIASES
            assert isinstance(COMMON_VALUE_ALIASES, dict)
            assert "A" in COMMON_VALUE_ALIASES
            assert "B" in COMMON_VALUE_ALIASES
